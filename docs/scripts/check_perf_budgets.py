#!/usr/bin/env python3
"""Check generated docs assets against lightweight performance budgets."""

from __future__ import annotations

import argparse
from pathlib import Path


BUDGETS_BYTES = {
    ".html": 300_000,
    ".css": 120_000,
    ".js": 80_000,
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}
MAX_IMAGE_BYTES = 3_000_000
INDEX_HTML_BUDGET = 60_000


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

    for file_path in site_dir.rglob("*"):
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        size = file_path.stat().st_size

        if ext in BUDGETS_BYTES and size > BUDGETS_BYTES[ext]:
            failures.append(
                f"- {file_path}: {size} bytes exceeds {ext} budget of {BUDGETS_BYTES[ext]} bytes"
            )

        if ext in IMAGE_EXTENSIONS and size > MAX_IMAGE_BYTES:
            failures.append(
                f"- {file_path}: {size} bytes exceeds image budget of {MAX_IMAGE_BYTES} bytes"
            )

    index_html = site_dir / "index.html"
    if index_html.exists():
        index_size = index_html.stat().st_size
        if index_size > INDEX_HTML_BUDGET:
            failures.append(
                f"- {index_html}: {index_size} bytes exceeds index budget of {INDEX_HTML_BUDGET} bytes"
            )

    if failures:
        print("Performance budget checks failed:")
        print("\n".join(failures))
        return 1

    print(f"Performance budget checks passed for {site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
