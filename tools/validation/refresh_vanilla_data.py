#!/usr/bin/env python3
"""Refresh every vanilla-derived file the validators read, from a local HOI4 install.

CI has no game installed, so validate_defines, validate_file_paths,
validate_gfx_references and validate_modifiers fall back to committed copies of
vanilla data. A game update leaves those stale: a modifier Paradox added after
the last refresh reads as a typo. Run this after a HOI4 version bump, from the
mod root:

    python3 tools/validation/refresh_vanilla_data.py
    python3 tools/validation/refresh_vanilla_data.py --only docs sprites

Requires the game installed (auto-detected, or set $HOI4_PATH).
"""

import argparse
import glob
import os
import shutil
import sys
from typing import Callable, Dict, Iterable, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import find_hoi4_install
from validate_defines import find_vanilla_defines, parse_vanilla_defines
from validate_file_paths import collect_vanilla_paths
from validate_gfx_references import (
    _read_raw,
    _vanilla_gfx_files,
    _vanilla_gui_files,
    sprite_names_from_gfx_text,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
_DOC_DIR = os.path.normpath(
    os.path.join(_HERE, "..", "..", "resources", "documentation")
)


class RefreshError(Exception):
    """A target could not be refreshed: its source data is missing."""


def _install() -> str:
    base = find_hoi4_install()
    if not base:
        raise RefreshError("no HOI4 install found")
    return base


def _write_manifest(
    filename: str, description: List[str], entries: Iterable[str]
) -> str:
    header = description + [
        "#",
        "# Regenerate after a HOI4 version bump (game installed), from the mod root:",
        "#   python3 tools/validation/refresh_vanilla_data.py",
        "",
    ]
    lines = sorted(entries)
    with open(os.path.join(_HERE, filename), "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(header) + "\n".join(lines) + "\n")
    return f"{filename}: {len(lines)} entries"


def _refresh_defines() -> str:
    path = find_vanilla_defines()
    if not path:
        raise RefreshError("common/defines/00_defines.lua not found")
    namespaces = parse_vanilla_defines(path)
    return _write_manifest(
        "vanilla_defines.txt",
        [
            "# Vanilla Hearts of Iron IV define names (NAMESPACE.NAME, from",
            "# common/defines/00_defines.lua). Used by validate_defines.py when no",
            "# live install is present (CI) to catch dead or renamed defines.",
        ],
        (f"{ns}.{name}" for ns, names in namespaces.items() for name in names),
    )


def _refresh_docs() -> str:
    source = os.path.join(_install(), "documentation")
    docs = glob.glob(os.path.join(source, "*.md"))
    if not docs:
        raise RefreshError(f"no .md files under {source}")
    added = 0
    for doc in docs:
        target = os.path.join(_DOC_DIR, os.path.basename(doc))
        if not os.path.exists(target):
            added += 1
        shutil.copyfile(doc, target)
    return f"resources/documentation: {len(docs)} files ({added} new)"


def _refresh_gui() -> str:
    files = _vanilla_gui_files()
    if not files:
        raise RefreshError("no interface .gui files found")
    return _write_manifest(
        "vanilla_gui_files.txt",
        [
            "# Vanilla Hearts of Iron IV interface .gui basenames (base + DLC, recursive).",
            "# Used by validate_gfx_references.py to tell MD-authored .gui files (a",
            "# missing sprite is a real bug -> ERROR) from vanilla overrides (which",
            "# reference thousands of vanilla sprites MD doesn't redefine -> WARNING).",
            "# MD-authored = a basename NOT in this list, so new content of any naming",
            "# convention is classified correctly with no edits here.",
        ],
        {os.path.basename(f) for f in files},
    )


def _refresh_paths() -> str:
    install = _install()
    paths = collect_vanilla_paths(install)
    if not paths:
        raise RefreshError(f"no checksummed paths found under {install}")
    return _write_manifest(
        "vanilla_paths.txt",
        [
            "# Vanilla Hearts of Iron IV paths covered by the multiplayer checksum",
            "# (base game + DLC), taken from the directory/extension rules in the",
            "# game's own checksum_manifest.txt.",
            "#",
            "# Used by validate_file_paths.py when no live install is present (CI).",
        ],
        paths,
    )


def _refresh_sprites() -> str:
    # Same file list the validator uses against a live install, so the
    # manifest and the live-install path stay interchangeable.
    gfx_files = _vanilla_gfx_files()
    if not gfx_files:
        raise RefreshError("no interface .gfx files found")
    names = set()
    for gfx in gfx_files:
        raw = _read_raw(gfx)
        if raw is not None:
            names.update(sprite_names_from_gfx_text(raw))
    return _write_manifest(
        "vanilla_sprites.txt",
        [
            "# Vanilla Hearts of Iron IV GFX sprite names (base + DLC interface .gfx).",
            "# Used by validate_gfx_references.py when no live install is present",
            "# (CI) so references to vanilla sprites are not flagged as undefined.",
        ],
        names,
    )


_TARGETS: Dict[str, Callable[[], str]] = {
    "defines": _refresh_defines,
    "docs": _refresh_docs,
    "gui": _refresh_gui,
    "paths": _refresh_paths,
    "sprites": _refresh_sprites,
}


def main() -> int:
    targets = sorted(_TARGETS)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only",
        nargs="+",
        choices=targets,
        metavar="TARGET",
        default=targets,
        help=f"refresh a subset ({', '.join(targets)})",
    )
    args = parser.parse_args()

    install = find_hoi4_install()
    if not install:
        print("No HOI4 install found (set $HOI4_PATH).", file=sys.stderr)
        return 1
    print(f"Refreshing from {install}")

    failed = False
    for name in args.only:
        try:
            print(f"  {_TARGETS[name]()}")
        except RefreshError as exc:
            print(f"  {name}: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
