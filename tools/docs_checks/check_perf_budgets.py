#!/usr/bin/env python3
"""Check what a browser downloads for each page of the built docs site.

Page budgets count bytes on the wire. The host gzips text, so a long Markdown
page stays cheap. Images are sent as they are, so they decide page weight.
"""

from __future__ import annotations

import argparse
import gzip
from html.parser import HTMLParser
from pathlib import Path

try:
    from check_site_links import iter_html_files, normalize_target
except ImportError:  # when imported as a package module
    from .check_site_links import iter_html_files, normalize_target

# Shared bundles, on disk. Every page parses them.
BUDGETS_BYTES = {
    ".css": 120_000,
    ".js": 80_000,
}

# HTML, CSS, JS and the images that load before the reader scrolls.
INITIAL_BUDGET = 300_000
# The initial load plus every lazy image on the page.
PAGE_BUDGET = 1_000_000

TEXT_SUFFIXES = {".html", ".css", ".js"}


class ResourceCollector(HTMLParser):
    """Collect the URLs a browser fetches to render one page.

    Each entry lists the candidate URLs for one resource. A srcset has several
    and the browser picks one.
    """

    def __init__(self) -> None:
        super().__init__()
        self.initial: list[list[str]] = []
        self.lazy: list[list[str]] = []
        self._picture_srcset: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs if v}

        if tag == "source":
            # Browsers take the first <source> of a <picture> that they support.
            self._picture_srcset = self._picture_srcset or attr_map.get("srcset")
        elif tag == "img":
            srcset = self._picture_srcset or attr_map.get("srcset")
            self._picture_srcset = None
            if srcset:
                candidates = [c.split()[0] for c in srcset.split(",") if c.strip()]
            else:
                candidates = [attr_map.get("src", "")]
            lazy = attr_map.get("loading") == "lazy"
            (self.lazy if lazy else self.initial).append(candidates)
        elif tag == "script" and "src" in attr_map:
            self.initial.append([attr_map["src"]])
        elif tag == "link" and attr_map.get("rel") in {"stylesheet", "modulepreload"}:
            self.initial.append([attr_map.get("href", "")])


def transfer_size(path: Path, cache: dict[Path, int]) -> int:
    """Return the bytes sent for a file: gzipped for text, as stored otherwise."""
    if path not in cache:
        if path.suffix.lower() in TEXT_SUFFIXES:
            cache[path] = len(gzip.compress(path.read_bytes(), compresslevel=6))
        else:
            cache[path] = path.stat().st_size
    return cache[path]


def weigh_page(
    html_file: Path, site_dir: Path, baseurl: str, cache: dict[Path, int]
) -> tuple[int, int, Path]:
    """Return (initial bytes, total bytes, heaviest file) for one built page."""
    parser = ResourceCollector()
    parser.feed(html_file.read_text(encoding="utf-8"))

    def fetched(resources: list[list[str]]) -> set[Path]:
        files: set[Path] = set()
        for candidates in resources:
            targets = [
                normalize_target(url, html_file, site_dir, baseurl)
                for url in candidates
            ]
            local = [site_dir / target.lstrip("/") for target in targets if target]
            local = [path for path in local if path.is_file()]
            if local:
                # Budget for the heaviest candidate the browser might pick.
                files.add(max(local, key=lambda path: transfer_size(path, cache)))
        return files

    initial = fetched(parser.initial) | {html_file}
    lazy = fetched(parser.lazy) - initial
    initial_bytes = sum(transfer_size(path, cache) for path in initial)
    lazy_bytes = sum(transfer_size(path, cache) for path in lazy)
    heaviest = max(initial | lazy, key=lambda path: transfer_size(path, cache))
    return initial_bytes, initial_bytes + lazy_bytes, heaviest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-dir", required=True, help="Path to generated site directory"
    )
    parser.add_argument(
        "--baseurl", default="", help="Site base path (e.g. /Millennium-Dawn)"
    )
    return parser.parse_args()


def run(site_dir: Path, baseurl: str = "") -> tuple[bool, str]:
    """Check built assets against perf budgets; return (passed, report)."""
    site_dir = site_dir.resolve()
    baseurl = baseurl.rstrip("/")
    if not site_dir.exists():
        return False, f"ERROR: site directory does not exist: {site_dir}"

    failures: list[str] = []

    for file_path in site_dir.rglob("*"):
        ext = file_path.suffix.lower()
        if ext not in BUDGETS_BYTES or not file_path.is_file():
            continue

        size = file_path.stat().st_size
        if size > BUDGETS_BYTES[ext]:
            failures.append(
                f"- {file_path}: {size} bytes exceeds {ext} budget of {BUDGETS_BYTES[ext]} bytes"
            )

    cache: dict[Path, int] = {}
    for html_file in iter_html_files(site_dir):
        initial, total, heaviest = weigh_page(html_file, site_dir, baseurl, cache)
        if initial > INITIAL_BUDGET:
            over = f"{initial} bytes exceeds initial load budget of {INITIAL_BUDGET}"
        elif total > PAGE_BUDGET:
            over = f"{total} bytes exceeds page budget of {PAGE_BUDGET}"
        else:
            continue

        failures.append(
            f"- {html_file}: {over} bytes "
            f"(heaviest: {heaviest.relative_to(site_dir).as_posix()}, {cache[heaviest]} bytes)"
        )

    if failures:
        return False, "Performance budget checks failed:\n" + "\n".join(failures)

    return True, f"Performance budget checks passed for {site_dir}"


def main() -> int:
    args = parse_args()
    passed, report = run(Path(args.site_dir), args.baseurl)
    print(report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
