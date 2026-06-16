#!/usr/bin/env python3
"""Validate Open Graph and Twitter image metadata in built docs HTML."""

from __future__ import annotations

import argparse
import posixpath
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

try:
    from common import SITE_ORIGIN
except ImportError:  # when imported as a package module
    from .common import SITE_ORIGIN

SITE_HOST = urlsplit(SITE_ORIGIN).hostname

REQUIRED_OG_META = (
    "og:image",
    "og:image:width",
    "og:image:height",
    "og:image:alt",
)
REQUIRED_TWITTER_META = ("twitter:image",)
SEO_SIGNAL_META = (
    "og:title",
    "og:type",
    "twitter:card",
)


class MetaCollector(HTMLParser):
    """Collect meta name/property content pairs."""

    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return

        attr_map = {k.lower(): (v or "") for k, v in attrs}
        key = attr_map.get("property", "") or attr_map.get("name", "")
        content = attr_map.get("content", "")
        if key:
            self.meta[key.strip().lower()] = content.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-dir", required=True, help="Path to built site directory"
    )
    parser.add_argument(
        "--baseurl", default="", help="Site base path (e.g. /Millennium-Dawn)"
    )
    return parser.parse_args()


def iter_html_files(site_dir: Path) -> list[Path]:
    return sorted(path for path in site_dir.rglob("*.html") if path.is_file())


def has_seo_meta(meta: dict[str, str]) -> bool:
    return any(key in meta for key in SEO_SIGNAL_META)


def normalize_meta_image_to_path(raw_url: str, baseurl: str) -> str | None:
    if not raw_url:
        return None

    parsed = urlsplit(raw_url)
    # An absolute URL pointing at another host (e.g. a CDN) is not served from
    # the local build, so it isn't ours to validate.
    if parsed.hostname and parsed.hostname != SITE_HOST:
        return None
    path = parsed.path or raw_url
    if not path.startswith("/"):
        return None

    clean_baseurl = baseurl.rstrip("/")
    if clean_baseurl and path.startswith(clean_baseurl + "/"):
        path = path[len(clean_baseurl) :]
    elif clean_baseurl and path == clean_baseurl:
        path = "/"

    if not path.startswith("/"):
        path = "/" + path

    return posixpath.normpath(path)


def asset_exists(site_dir: Path, normalized_path: str) -> bool:
    if normalized_path == "/":
        return (site_dir / "index.html").exists()
    return (site_dir / normalized_path.lstrip("/")).exists()


def check_html_file(site_dir: Path, html_path: Path, baseurl: str) -> list[str]:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    parser = MetaCollector()
    parser.feed(text)
    meta = parser.meta

    if not has_seo_meta(meta):
        return []

    issues: list[str] = []

    for key in REQUIRED_OG_META:
        if not meta.get(key):
            issues.append(f"missing meta '{key}'")

    for key in REQUIRED_TWITTER_META:
        if not meta.get(key):
            issues.append(f"missing meta '{key}'")

    og_image = meta.get("og:image", "")
    tw_image = meta.get("twitter:image", "")

    if og_image:
        normalized = normalize_meta_image_to_path(og_image, baseurl=baseurl)
        if normalized is None:
            issues.append(f"og:image is not a site-local URL: {og_image}")
        elif not asset_exists(site_dir, normalized):
            issues.append(
                f"og:image target does not exist in site output: {normalized}"
            )

    if tw_image:
        normalized = normalize_meta_image_to_path(tw_image, baseurl=baseurl)
        if normalized is None:
            issues.append(f"twitter:image is not a site-local URL: {tw_image}")
        elif not asset_exists(site_dir, normalized):
            issues.append(
                f"twitter:image target does not exist in site output: {normalized}"
            )

    return issues


def run(site_dir: Path, baseurl: str = "") -> tuple[bool, str]:
    """Validate OG/Twitter image metadata; return (passed, report)."""
    site_dir = site_dir.resolve()
    if not site_dir.exists():
        return False, f"ERROR: site directory does not exist: {site_dir}"

    failures: list[str] = []
    for html_file in iter_html_files(site_dir):
        for issue in check_html_file(
            site_dir=site_dir, html_path=html_file, baseurl=baseurl
        ):
            failures.append(f"- {html_file}: {issue}")

    if failures:
        return False, "OG metadata checks failed:\n" + "\n".join(failures)

    return True, f"OG metadata checks passed for {site_dir}"


def main() -> int:
    args = parse_args()
    passed, report = run(Path(args.site_dir), args.baseurl)
    print(report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
