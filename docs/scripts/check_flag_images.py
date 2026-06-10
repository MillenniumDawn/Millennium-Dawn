#!/usr/bin/env python3
"""Fail when a country `flag_image` frontmatter path has no file under src/assets/images."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_DIR = ROOT / "src" / "content" / "countries"
ASSETS_ROOT = ROOT / "src" / "assets" / "images"
FLAG_IMAGE_RE = re.compile(r"^flag_image:\s*[\"']?(/assets/images/[^\s\"']+)[\"']?\s*$", re.MULTILINE)


def main() -> int:
    errors: list[str] = []

    for country_file in sorted(COUNTRIES_DIR.glob("*.md")):
        text = country_file.read_text(encoding="utf-8")
        for match in FLAG_IMAGE_RE.finditer(text):
            asset_path = match.group(1)
            relative = asset_path.removeprefix("/assets/images/")
            disk_path = ASSETS_ROOT / relative
            if not disk_path.is_file():
                errors.append(
                    f"{country_file.name}: flag_image {asset_path} missing at src/assets/images/{relative}",
                )

    if errors:
        print("Flag image validation failed:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
