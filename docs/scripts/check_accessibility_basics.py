#!/usr/bin/env python3
"""Basic accessibility checks for generated HTML pages."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List


class A11yParser(HTMLParser):
    """Collect small accessibility signals from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.main_count = 0
        self.heading_count = 0
        self.html_lang_seen = False
        self.images_missing_alt: List[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs}

        if tag == "html":
            lang = (attr_map.get("lang") or "").strip()
            if lang:
                self.html_lang_seen = True

        if tag == "main":
            self.main_count += 1

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_count += 1

        if tag == "img" and "alt" not in attr_map:
            self.images_missing_alt.append(self.getpos()[0])


def iter_html_files(site_dir: Path) -> Iterable[Path]:
    for file_path in site_dir.rglob("*.html"):
        if file_path.is_file():
            yield file_path


def check_file(path: Path) -> list[str]:
    parser = A11yParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))

    issues: list[str] = []
    if not parser.html_lang_seen:
        issues.append("missing <html lang=\"...\">")
    if parser.main_count != 1:
        issues.append(f"expected exactly one <main>, found {parser.main_count}")
    if parser.heading_count == 0:
        issues.append("page has no heading elements (<h1>-<h6>)")
    if parser.images_missing_alt:
        lines = ", ".join(str(line) for line in parser.images_missing_alt[:10])
        issues.append(f"<img> without alt attribute at line(s): {lines}")

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", required=True, help="Path to generated site directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    site_dir = Path(args.site_dir).resolve()
    if not site_dir.exists():
        print(f"ERROR: site directory does not exist: {site_dir}")
        return 2

    failures: list[str] = []
    for html_file in iter_html_files(site_dir):
        issues = check_file(html_file)
        if issues:
            for issue in issues:
                failures.append(f"- {html_file}: {issue}")

    if failures:
        print("Accessibility baseline checks failed:")
        print("\n".join(failures))
        return 1

    print(f"Accessibility baseline checks passed for {site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
