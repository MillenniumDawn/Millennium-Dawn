#!/usr/bin/env python3
"""Regenerate vanilla_defines.txt from a local HOI4 install.

validate_defines.py cross-references MD_defines.lua against that manifest
when no live install is present (CI). Run this after a HOI4 version bump:

    python3 tools/validation/gen_vanilla_defines_manifest.py

Requires the game installed (auto-detected, or set $HOI4_PATH).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_defines import find_vanilla_defines, parse_vanilla_defines

_MANIFEST = os.path.join(os.path.dirname(__file__), "vanilla_defines.txt")
_HEADER = [
    "# Vanilla Hearts of Iron IV define names (NAMESPACE.NAME, from",
    "# common/defines/00_defines.lua). Used by validate_defines.py when no",
    "# live install is present (CI) to catch dead or renamed defines.",
    "#",
    "# Regenerate after a HOI4 version bump (game installed), from the mod root:",
    "#   python3 tools/validation/gen_vanilla_defines_manifest.py",
    "",
]


def main() -> int:
    path = find_vanilla_defines()
    if not path:
        print("No HOI4 install found (set $HOI4_PATH).", file=sys.stderr)
        return 1
    namespaces = parse_vanilla_defines(path)
    lines = sorted(f"{ns}.{name}" for ns, names in namespaces.items() for name in names)
    with open(_MANIFEST, "w", encoding="utf-8") as f:
        f.write("\n".join(_HEADER) + "\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} vanilla defines to {_MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
