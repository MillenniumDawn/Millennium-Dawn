#!/usr/bin/env python3
"""Regenerate vanilla_gui_files.txt from a local HOI4 install.

validate_gfx_references.py uses that manifest to tell MD-authored .gui files
from vanilla overrides. Run this after a HOI4 version bump:

    python3 tools/validation/gen_vanilla_gui_manifest.py

Requires the game installed (auto-detected, or set $HOI4_PATH).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import find_hoi4_install

_MANIFEST = os.path.join(os.path.dirname(__file__), "vanilla_gui_files.txt")
_HEADER = [
    "# Vanilla Hearts of Iron IV interface/*.gui basenames.",
    "# Used by validate_gfx_references.py to tell MD-authored .gui files (a",
    "# missing sprite is a real bug -> ERROR) from vanilla overrides (which",
    "# reference thousands of vanilla sprites MD doesn't redefine -> WARNING).",
    "# MD-authored = a basename NOT in this list, so new content of any naming",
    "# convention is classified correctly with no edits here.",
    "#",
    "# Regenerate after a HOI4 version bump (game installed), from the mod root:",
    "#   python3 tools/validation/gen_vanilla_gui_manifest.py",
    "",
]


def main() -> int:
    base = find_hoi4_install()
    if not base:
        print("No HOI4 install found (set $HOI4_PATH).", file=sys.stderr)
        return 1
    vdir = os.path.join(base, "interface")
    names = sorted(f for f in os.listdir(vdir) if f.endswith(".gui"))
    with open(_MANIFEST, "w", encoding="utf-8") as f:
        f.write("\n".join(_HEADER) + "\n".join(names) + "\n")
    print(f"Wrote {len(names)} vanilla .gui basenames to {_MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
