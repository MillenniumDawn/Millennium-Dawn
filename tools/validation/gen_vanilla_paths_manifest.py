#!/usr/bin/env python3
"""Regenerate vanilla_paths.txt from a local HOI4 install.

validate_file_paths.py reads that manifest when no live install is present (CI)
to spot mod paths that differ from a vanilla one only in case. Run this after a
HOI4 version bump:

    python3 tools/validation/gen_vanilla_paths_manifest.py

Requires the game installed (auto-detected, or set $HOI4_PATH).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import find_hoi4_install
from validate_file_paths import collect_vanilla_paths

_MANIFEST = os.path.join(os.path.dirname(__file__), "vanilla_paths.txt")
_HEADER = [
    "# Vanilla Hearts of Iron IV paths covered by the multiplayer checksum",
    "# (base game + DLC), taken from the directory/extension rules in the",
    "# game's own checksum_manifest.txt.",
    "#",
    "# Used by validate_file_paths.py when no live install is present (CI).",
    "#",
    "# Regenerate after a HOI4 version bump (game installed), from the mod root:",
    "#   python3 tools/validation/gen_vanilla_paths_manifest.py",
    "",
]


def main() -> int:
    install = find_hoi4_install()
    if not install:
        print("No HOI4 install found (set $HOI4_PATH).", file=sys.stderr)
        return 1
    paths = collect_vanilla_paths(install)
    if not paths:
        print(f"No checksummed paths found under {install}.", file=sys.stderr)
        return 1
    with open(_MANIFEST, "w", encoding="utf-8") as f:
        f.write("\n".join(_HEADER) + "\n".join(sorted(paths)) + "\n")
    print(f"Wrote {len(paths)} vanilla paths to {_MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
