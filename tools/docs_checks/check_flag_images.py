#!/usr/bin/env python3
"""Fail when a country `flag_image` frontmatter path has no file under src/assets/images."""

from __future__ import annotations

import re
import sys

try:
    from common import DOCS_ROOT
except ImportError:  # when imported as a package module
    from .common import DOCS_ROOT

COUNTRIES_DIR = DOCS_ROOT / "src" / "content" / "countries"
ASSETS_ROOT = DOCS_ROOT / "src" / "assets" / "images"
FLAG_IMAGE_RE = re.compile(
    r"^flag_image:\s*[\"']?(/assets/images/[^\s\"']+)[\"']?\s*$", re.MULTILINE
)


def run() -> tuple[bool, str]:
    """Validate country flag_image references; return (passed, report)."""
    errors: list[str] = []

    for country_file in sorted(COUNTRIES_DIR.glob("*.md")):
        text = country_file.read_text(encoding="utf-8", errors="replace")
        for match in FLAG_IMAGE_RE.finditer(text):
            asset_path = match.group(1)
            relative = asset_path.removeprefix("/assets/images/")
            disk_path = ASSETS_ROOT / relative
            if not disk_path.is_file():
                errors.append(
                    f"{country_file.name}: flag_image {asset_path} missing at src/assets/images/{relative}",
                )

    if errors:
        return False, "Flag image validation failed:\n" + "\n".join(errors)

    return True, "Flag image references OK."


def main() -> int:
    passed, report = run()
    print(report, file=sys.stdout if passed else sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
