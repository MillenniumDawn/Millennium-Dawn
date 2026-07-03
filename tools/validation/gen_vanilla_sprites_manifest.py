#!/usr/bin/env python3
"""Regenerate vanilla_sprites.txt from a local HOI4 install.

validate_gfx_references.py folds that manifest into the defined-sprites set
when no live install is present (CI), replacing the imprecise
_VANILLA_PREFIXES heuristic. Run this after a HOI4 version bump:

    python3 tools/validation/gen_vanilla_sprites_manifest.py

Requires the game installed (auto-detected, or set $HOI4_PATH).
"""

import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import find_hoi4_install
from validate_gfx_references import _read_raw, sprite_names_from_gfx_text

_MANIFEST = os.path.join(os.path.dirname(__file__), "vanilla_sprites.txt")
_HEADER = [
    "# Vanilla Hearts of Iron IV GFX sprite names (from interface/*.gfx).",
    "# Used by validate_gfx_references.py when no live install is present",
    "# (CI) so references to vanilla sprites are not flagged as undefined.",
    "#",
    "# Regenerate after a HOI4 version bump (game installed), from the mod root:",
    "#   python3 tools/validation/gen_vanilla_sprites_manifest.py",
    "",
]


def main() -> int:
    base = find_hoi4_install()
    if not base:
        print("No HOI4 install found (set $HOI4_PATH).", file=sys.stderr)
        return 1
    vdir = os.path.join(base, "interface")
    if not os.path.isdir(vdir):
        print(f"No interface/ directory under {base}.", file=sys.stderr)
        return 1
    names = set()
    # Same top-level glob the validator uses against a live install, so the
    # manifest and the live-install path stay interchangeable.
    for gfx in glob.glob(os.path.join(vdir, "*.gfx")):
        raw = _read_raw(gfx)
        if raw is not None:
            names.update(sprite_names_from_gfx_text(raw))
    with open(_MANIFEST, "w", encoding="utf-8") as f:
        f.write("\n".join(_HEADER) + "\n".join(sorted(names)) + "\n")
    print(f"Wrote {len(names)} vanilla sprite names to {_MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
