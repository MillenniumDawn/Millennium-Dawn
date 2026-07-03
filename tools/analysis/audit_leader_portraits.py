#!/usr/bin/env python3
"""
audit_leader_portraits.py — Classify gfx/leaders/ portrait files as zero-reference
(safe to move out of gfx/) or broken-reference (referenced, but only via a
case-typo'd path — a Linux-breaking content bug, not a dead asset).

Reuses validate_unused_textures.py's exhaustive reference scan (every .gfx
texturefile, every portrait=/picture=/bare "gfx/...ext" literal in common/,
history/, events/, portraits/, plus the basename-only fallback HOI4 itself
uses for bare filenames) to find candidates, then adds a case-insensitive pass
over the same reference set to split "nobody references this" from "someone
references this with the wrong case".

Usage:
    python3 tools/analysis/audit_leader_portraits.py
    python3 tools/analysis/audit_leader_portraits.py --json
"""

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "validation"))

from shared_utils import FileOpener  # noqa: E402
from validate_unused_textures import Validator  # noqa: E402

LEADERS_PREFIX = "gfx/leaders/"

# Same four texturefile patterns process_gfx_file() matches in .gfx files;
# reproduced here (rather than imported) because that function only returns
# resolved matches, not the raw ref string + line needed to name the typo.
_GFX_FILE_REF_PATTERNS = [
    re.compile(r'texturefile\s*=\s*"([^"]+)"', re.IGNORECASE),
    re.compile(r'texture_diffuse\s*=\s*"([^"]+)"', re.IGNORECASE),
    re.compile(r'texture_normal\s*=\s*"([^"]+)"', re.IGNORECASE),
    re.compile(r'texture_specular\s*=\s*"([^"]+)"', re.IGNORECASE),
]

_GAME_FILE_REF_PATTERNS = [
    re.compile(r'portrait\s*=\s*"([^"]+\.(?:dds|tga|png))"', re.IGNORECASE),
    re.compile(r'picture\s*=\s*"([^"]+\.(?:dds|tga|png))"', re.IGNORECASE),
    re.compile(r'"(gfx/[^"]+\.(?:dds|tga|png))"', re.IGNORECASE),
]


def _normalize(ref: str) -> str:
    ref = ref.replace("\\", "/").lstrip("/")
    while "//" in ref:
        ref = ref.replace("//", "/")
    return ref


def _scan_raw_refs(
    filepath: str, patterns: List[re.Pattern]
) -> List[Tuple[str, str, int]]:
    try:
        content = FileOpener.open_text_file(
            filepath, lowercase=False, strip_comments_flag=True
        )
    except Exception:
        return []
    rel = os.path.relpath(filepath, REPO_ROOT)
    found = []
    for lineno, line in enumerate(content.split("\n"), 1):
        for pattern in patterns:
            for m in pattern.finditer(line):
                found.append((_normalize(m.group(1)), rel, lineno))
    return found


def collect_raw_refs() -> List[Tuple[str, str, int]]:
    """Every raw texture-path literal in the mod, before matching against disk."""
    refs: List[Tuple[str, str, int]] = []

    for d in ("gfx", "interface"):
        base = REPO_ROOT / d
        if base.is_dir():
            for filepath in glob.iglob(str(base / "**" / "*.gfx"), recursive=True):
                refs.extend(_scan_raw_refs(filepath, _GFX_FILE_REF_PATTERNS))

    for d in ("common", "history", "events", "portraits"):
        base = REPO_ROOT / d
        if base.is_dir():
            for filepath in glob.iglob(str(base / "**" / "*.txt"), recursive=True):
                refs.extend(_scan_raw_refs(filepath, _GAME_FILE_REF_PATTERNS))

    return refs


def run_audit():
    """Run the scan and return (zero_reference, broken_reference, validator).

    zero_reference is a sorted list of gfx/leaders/... paths with no reference
    anywhere (exact or case-typo'd). broken_reference is a list of
    (leader_path, [(wrong_ref, source_file, line), ...]) for files that are
    only reachable through a case-mismatched reference.
    """
    validator = Validator(str(REPO_ROOT), use_colors=False)
    validator.validate_unused_textures()

    all_leaders = {
        t
        for t in validator.texture_files
        if t.replace(os.sep, "/").startswith(LEADERS_PREFIX)
    }
    referenced = validator.referenced_textures | validator.game_file_textures
    unused_leaders = sorted(all_leaders - referenced)

    raw_refs = collect_raw_refs()
    # A ref that already resolves exactly (full path or exact-case basename) to
    # *some* real texture is spoken for — it can't also be a typo pointing at an
    # unrelated file that happens to share a basename case-insensitively.
    exact_basenames = set(validator.texture_filename_lookup.keys())
    exact_paths = validator.texture_files

    # Basename-only matching mirrors HOI4's own bare-filename resolution (relative
    # to gfx/leaders/<TAG>/), so it only applies to refs with no directory part.
    # A fully-qualified "gfx/..." ref that happens to share a basename with an
    # unrelated file elsewhere is not a typo of that file.
    basename_hits: dict = {}
    for ref, src, line in raw_refs:
        if "/" not in ref and ref not in exact_basenames:
            basename_hits.setdefault(ref.lower(), []).append((ref, src, line))
    full_hits: dict = {}
    for ref, src, line in raw_refs:
        if ref not in exact_paths:
            full_hits.setdefault(ref.lower(), []).append((ref, src, line))

    zero_reference = []
    broken_reference = []
    for path in unused_leaders:
        base_lower = os.path.basename(path).lower()
        hits = full_hits.get(path.lower(), []) + basename_hits.get(base_lower, [])
        if hits:
            seen = set()
            deduped = []
            for h in hits:
                if h not in seen:
                    seen.add(h)
                    deduped.append(h)
            broken_reference.append((path, deduped))
        else:
            zero_reference.append(path)

    return zero_reference, broken_reference, validator


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON"
    )
    args = parser.parse_args()

    zero_reference, broken_reference, _ = run_audit()

    if args.json:
        print(
            json.dumps(
                {
                    "zero_reference": zero_reference,
                    "broken_reference": [
                        {
                            "file": path,
                            "wrong_refs": [
                                {"ref": ref, "source": src, "line": line}
                                for ref, src, line in hits
                            ],
                        }
                        for path, hits in broken_reference
                    ],
                },
                indent=2,
            )
        )
        return

    print(f"Zero-reference leader portraits (safe to move): {len(zero_reference)}")
    for path in zero_reference:
        print(f"  {path}")

    print(
        f"\nBroken-reference leader portraits (typo'd path, needs a content fix): {len(broken_reference)}"
    )
    for path, hits in broken_reference:
        print(f"  {path}")
        for ref, src, line in hits:
            print(f"      referenced as '{ref}' at {src}:{line}")

    print("\nSummary")
    print(f"  Zero-reference:   {len(zero_reference)}")
    print(f"  Broken-reference: {len(broken_reference)}")


if __name__ == "__main__":
    main()
