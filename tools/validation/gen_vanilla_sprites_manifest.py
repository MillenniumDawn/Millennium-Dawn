#!/usr/bin/env python3
"""Regenerate vanilla_sprites.txt from a local HOI4 install.

validate_gfx_references.py folds that manifest into the defined-sprites set
when no live install is present (CI), replacing the imprecise
_VANILLA_PREFIXES heuristic. Run this after a HOI4 version bump:

    python3 tools/validation/gen_vanilla_sprites_manifest.py

Requires the game installed (auto-detected, or set $HOI4_PATH).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_gfx_references import (
    _read_raw,
    _vanilla_gfx_files,
    sprite_names_from_gfx_text,
)

_MANIFEST = os.path.join(os.path.dirname(__file__), "vanilla_sprites.txt")
_HEADER = [
    "# Vanilla Hearts of Iron IV GFX sprite names (base + DLC interface .gfx).",
    "# Used by validate_gfx_references.py when no live install is present",
    "# (CI) so references to vanilla sprites are not flagged as undefined.",
    "#",
    "# Regenerate after a HOI4 version bump (game installed), from the mod root:",
    "#   python3 tools/validation/gen_vanilla_sprites_manifest.py",
    "",
]


def main() -> int:
    # Same file list the validator uses against a live install, so the
    # manifest and the live-install path stay interchangeable.
    gfx_files = _vanilla_gfx_files()
    if not gfx_files:
        print("No HOI4 install found (set $HOI4_PATH).", file=sys.stderr)
        return 1
    names = set()
    for gfx in gfx_files:
        raw = _read_raw(gfx)
        if raw is not None:
            names.update(sprite_names_from_gfx_text(raw))
    with open(_MANIFEST, "w", encoding="utf-8") as f:
        f.write("\n".join(_HEADER) + "\n".join(sorted(names)) + "\n")
    print(f"Wrote {len(names)} vanilla sprite names to {_MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
