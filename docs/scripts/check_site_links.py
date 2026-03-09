#!/usr/bin/env python3
"""Validate internal links and local assets in a built site."""

from __future__ import annotations

import argparse
import os
import posixpath
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List, Tuple


SKIP_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "javascript:",
    "data:",
)


class LinkCollector(HTMLParser):
    """Collect href/src attributes from HTML tags."""

    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs if v is not None}

        if tag == "a" and "href" in attr_map:
            self.links.append(attr_map["href"])
            return

        if tag in {"img", "script", "iframe", "source"} and "src" in attr_map:
            self.links.append(attr_map["src"])
            return

        if tag == "link" and "href" in attr_map:
            self.links.append(attr_map["href"])


def print_safe(line: str) -> None:
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "backslashreplace"))


def strip_query_and_hash(url: str) -> str:
    clean = url.split("#", 1)[0]
    clean = clean.split("?", 1)[0]
    return clean.strip()


def normalize_target(raw_url: str, current_html: Path, site_dir: Path, baseurl: str) -> str | None:
    url = strip_query_and_hash(raw_url)
    if not url or url == "#":
        return None

    lowered = url.lower()
    if lowered.startswith(SKIP_PREFIXES) or url.startswith("//"):
        return None

    if baseurl and url == baseurl:
        return "/"
    if baseurl and url.startswith(baseurl + "/"):
        url = url[len(baseurl) :]

    if url.startswith("/"):
        return posixpath.normpath(url)

    rel_from_site = current_html.relative_to(site_dir).parent.as_posix()
    candidate = posixpath.join("/", rel_from_site, url)
    return posixpath.normpath(candidate)


def path_exists_in_site(target_path: str, site_dir: Path) -> bool:
    normalized = target_path.lstrip("/")
    full_path = site_dir / normalized

    if target_path == "/":
        return (site_dir / "index.html").exists()

    suffix = Path(normalized).suffix
    if suffix:
        return full_path.exists()

    if full_path.exists():
        return True

    if (site_dir / (normalized + ".html")).exists():
        return True

    if (site_dir / normalized / "index.html").exists():
        return True

    return False


def iter_html_files(site_dir: Path) -> Iterable[Path]:
    for file_path in site_dir.rglob("*.html"):
        if file_path.is_file():
            yield file_path


def collect_broken_links(site_dir: Path, baseurl: str) -> List[Tuple[Path, str, str]]:
    errors: List[Tuple[Path, str, str]] = []

    for html_file in iter_html_files(site_dir):
        parser = LinkCollector()
        parser.feed(html_file.read_text(encoding="utf-8", errors="replace"))

        for raw_link in parser.links:
            normalized = normalize_target(raw_link, html_file, site_dir, baseurl)
            if normalized is None:
                continue

            if not path_exists_in_site(normalized, site_dir):
                errors.append((html_file, raw_link, normalized))

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", required=True, help="Path to generated site directory")
    parser.add_argument("--baseurl", default="", help="Site base path (e.g. /Millennium-Dawn)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    site_dir = Path(args.site_dir).resolve()
    baseurl = args.baseurl.rstrip("/")

    if not site_dir.exists():
        print_safe(f"ERROR: site directory does not exist: {site_dir}")
        return 2

    errors = collect_broken_links(site_dir, baseurl)

    if errors:
        print_safe("Broken internal links/assets found:")
        for html_file, raw_link, normalized in errors:
            print_safe(f"- {html_file}: {raw_link} -> {normalized}")
        return 1

    print_safe(f"Link check passed for {site_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
