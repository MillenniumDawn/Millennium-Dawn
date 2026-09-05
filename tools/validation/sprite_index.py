#!/usr/bin/env python3
"""Shared sprite-name index for validators that cross-reference GFX sprites.

A sprite reference (event `picture`, focus `icon`, idea `picture`) resolves to
a spriteType whose `name = "..."` matches the value verbatim. This module reads
every interface/*.gfx in the mod plus the vanilla install (when discoverable)
and returns the set of defined sprite names so a validator can flag references
that point at nothing.
"""

import glob
import os
import re
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(__file__))

import disk_cache
from shared_utils import extract_block_from_text
from validate_gfx_references import (
    _GFX_SPRITE_TYPES,
    _strip_comments,
    _vanilla_gfx_files,
    sprite_defs_from_gfx_text,
)

_NAME_IN_BLOCK = re.compile(r'\bname\s*=\s*(?:"([^"]+)"|([^\s}]+))')


def _parse_names(raw: str) -> List[str]:
    """Return every spriteType name in one .gfx file's text (block-scoped)."""
    text = _strip_comments(raw)
    names: List[str] = []
    for m in _GFX_SPRITE_TYPES.finditer(text):
        block, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            line_end = text.find("\n", m.start())
            block = text[m.end() : line_end if line_end != -1 else m.end() + 200]
        nm = _NAME_IN_BLOCK.search(block)
        if nm:
            names.append(nm.group(1) or nm.group(2))
    return names


def _names_in_file(filepath: str, mod_path: Optional[str] = None) -> List[str]:
    """Return every spriteType name defined in one .gfx file.

    When *mod_path* is given the parse is content-cached on disk, so a warm run
    only re-parses .gfx files whose bytes changed (e.g. a newly added one).
    """
    try:
        with open(filepath, encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    if mod_path is None:
        return _parse_names(raw)
    return disk_cache.per_file_cached_by_content(
        mod_path, "sprite_index.names", filepath, raw, lambda: _parse_names(raw)
    )


def _names_in_file_pair(args) -> List[str]:
    """Pool-worker wrapper: unpack ``(filepath, mod_path)`` for pool.map."""
    filepath, mod_path = args
    return _names_in_file(filepath, mod_path)


def build_sprite_index(
    mod_path: str, gfx_only: bool = False, pool_map=None, include_vanilla: bool = True
) -> frozenset:
    """Return every sprite name defined in interface/*.gfx.

    Args:
        mod_path: mod root; its `interface/` is scanned.
        gfx_only: when True, keep only `GFX_`-prefixed names (event/idea
            pictures are always prefixed; focus icons are not).
        pool_map: optional BaseValidator._pool_map for parallel reads; falls
            back to a sequential scan when None.
        include_vanilla: when True, also scan the vanilla HOI4 install (if
            discoverable). Event pictures must be MD-defined, so the event check
            passes False — that keeps it accurate in CI, where vanilla is absent.
            Focus/idea/decision icons may legitimately reuse vanilla sprites, so
            those keep the default.
    """
    gfx_files: List[str] = glob.glob(
        os.path.join(mod_path, "interface", "**", "*.gfx"), recursive=True
    )
    if include_vanilla:
        gfx_files.extend(_vanilla_gfx_files())

    names = set()
    if pool_map is not None:
        for sub in pool_map(_names_in_file_pair, [(f, mod_path) for f in gfx_files]):
            names.update(sub)
    else:
        for f in gfx_files:
            names.update(_names_in_file(f, mod_path))

    if gfx_only:
        names = {n for n in names if n.startswith("GFX_")}
    return frozenset(names)


def _gfx_root(filepath: str) -> str:
    """Return the root a .gfx file's `texturefile` paths are relative to.

    That is the directory holding `interface/`: the mod root, the vanilla
    install, or an individual `dlc/<name>/` — DLC art ships beside its own .gfx.
    """
    normalized = filepath.replace("\\", "/")
    root, sep, _rest = normalized.partition("/interface/")
    return root if sep else os.path.dirname(normalized)


def _textures_in_file(args) -> List[List[str]]:
    """Pool-worker: return ``[sprite_name, absolute texture path]`` pairs."""
    filepath, mod_path = args
    root = _gfx_root(filepath)
    try:
        with open(filepath, encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except OSError:
        return []

    def _compute() -> List[List[str]]:
        pairs = []
        for name, texture, _line in sprite_defs_from_gfx_text(raw):
            if not texture:
                continue
            rel = texture.replace("\\", "/").lstrip("/")
            pairs.append([name, os.path.normpath(os.path.join(root, rel))])
        return pairs

    return disk_cache.per_file_cached_by_content(
        mod_path, "sprite_index.textures", filepath, raw, _compute
    )


def build_sprite_texture_index(
    mod_path: str, pool_map=None, include_vanilla: bool = True
) -> Dict[str, str]:
    """Return sprite name -> absolute path of the texture it renders.

    Mod definitions are applied last so a mod sprite overriding a vanilla name
    wins, matching load order. Sprites with no `texturefile` (frame strips built
    from other sprites, `textfile` entries) are absent rather than empty.
    """
    jobs: List = []
    if include_vanilla:
        jobs.extend((f, mod_path) for f in _vanilla_gfx_files())
    jobs.extend(
        (f, mod_path)
        for f in glob.glob(
            os.path.join(mod_path, "interface", "**", "*.gfx"), recursive=True
        )
    )

    mapper = pool_map if pool_map is not None else lambda fn, it: map(fn, it)
    index: Dict[str, str] = {}
    for pairs in mapper(_textures_in_file, jobs):
        for name, path in pairs:
            index[name] = path
    return index
