#!/usr/bin/env python3
##########################
# GFX Sprite Reference Validation Script
#
# Validates that sprite names referenced in .gui files, scripted GUIs, and
# scripted localisation are defined in interface/*.gfx files.
#
# Checks:
#   1. Build GFX definition set from all interface/*.gfx files
#   2. Validate spriteType / quadTextureSprite / background references in .gui files
#   3. Validate image = "GFX_xxx" references in common/scripted_guis/*.txt
#   4. Validate localization_key = "GFX_xxx" in common/scripted_localisation/*.txt
#   5. Unused GFX definitions (warning; skipped in staged mode; capped at 50)
#
# Note: validate_scripted_gui.py already checks spriteType/quadTextureSprite in
# .gui files at WARNING level. This validator promotes those to ERROR, adds
# background= and scripted-GUI image= coverage, and adds unused-sprite reporting.
#
# Usage:
#   python3 tools/validation/validate_gfx_references.py [OPTIONS]
#
# Options:
#   --path PATH         Path to mod root (default: auto-detected)
#   --strict            Exit 1 if any errors found
#   --no-color          Disable colour output
#   --staged            Only validate staged .gui/.gfx/.txt files
#   --workers N         Worker processes (default: CPU count / 2)
##########################
import glob
import os
import re
import sys
from typing import List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import compute_line_offsets, line_for_offset
from validator_common import BaseValidator, Colors, Severity, run_validator_main

# ---------------------------------------------------------------------------
# MD-authored file detection
# ---------------------------------------------------------------------------
# .gui files in MD fall into two categories:
#   1. MD-authored: files the mod team wrote from scratch (scripted GUIs,
#      country-specific GUIs, feature GUIs). Missing sprites here are real bugs.
#   2. Vanilla overrides: copies of vanilla .gui files with small patches. These
#      reference thousands of vanilla sprites the mod doesn't redefine. Missing
#      sprites here are almost always vanilla refs — flag as WARNING only.
#
# Heuristic: a .gui file is MD-authored if its basename (without extension) starts
# with a known MD or country prefix. Everything else is treated as a vanilla override.

_MD_GUI_PREFIXES = (
    "MD_",
    "EH_",
    "ENG_",
    "GER_",
    "LBA_",
    "Iran_",
    "Iraq_",
    "bos_",
    "cze_",
    "Counter_",
    "agriculture_",
    "SIN_",
    "HKG_",
    "HOL_",
    "NKO_",
    "GRE_",
    "CYP_",
    "SCO_",
    "RAJ_",
    "SUB_",
    "PER_",
    "ALG_",
    "artsakh_",
    "israel_",
    "singapore_",
    "divisions_summary",
    "!MD_",
)


def _is_md_gui_file(filepath: str) -> bool:
    """Return True if this .gui file is MD-authored (not a vanilla override)."""
    basename = os.path.basename(filepath)
    return any(basename.startswith(p) for p in _MD_GUI_PREFIXES)


# ---------------------------------------------------------------------------
# Helpers — HOI4/Clausewitz comment stripping for .gfx and .gui files
# These use C-style // and /* */ comments, NOT the # used by .txt scripts.
# strip_comments() from shared_utils strips # comments; do NOT use it here.
# ---------------------------------------------------------------------------

_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"//.*")


def _strip_cstyle_comments(text: str) -> str:
    """Remove // line comments and /* block comments from Clausewitz GUI/GFX text."""
    text = _BLOCK_COMMENT_RE.sub("", text)
    text = _LINE_COMMENT_RE.sub("", text)
    return text


# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------

# All sprite type block openers in .gfx files; all use `name = "GFX_xxx"`.
# We collect any `name = "GFX_xxx"` inside any of these blocks.
_GFX_SPRITE_TYPES = re.compile(
    r"\b(?:spriteType|frameAnimatedSpriteType|corneredTileSpriteType|"
    r"maskedShieldType|progressbartype|textSpriteType)\s*=\s*\{",
    re.IGNORECASE,
)

# name = "GFX_xxx" inside a block
_GFX_NAME = re.compile(r'\bname\s*=\s*"(GFX_[A-Za-z0-9_]+)"')

# GUI references — spriteType / quadTextureSprite / background
_GUI_REF = re.compile(
    r'\b(spriteType|quadTextureSprite|background)\s*=\s*"(GFX_[^"\[]+)"'
)

# Scripted GUI properties: image = "GFX_xxx"
_SGUI_IMAGE_REF = re.compile(r'\bimage\s*=\s*"(GFX_[^"\[]+)"')

# Scripted localisation: localization_key = "GFX_xxx"
_SLOC_KEY_REF = re.compile(r'\blocalization_key\s*=\s*"(GFX_[^"\[]+)"')

# Auto-generated flag sprites — never defined in .gfx, built by the engine.
# Matches GFX_flag_TAG, GFX_TAG_flag, GFX_shield_TAG etc.
_FLAG_SPRITE_RE = re.compile(
    r"^GFX_(?:flag_|.*_flag$|.*_coat_of_arms$|.*_shield$)", re.IGNORECASE
)

# Sprites defined purely in vanilla (game install) that we can't track when
# the vanilla install isn't present. We accept all vanilla-looking names
# rather than false-positiving on them. The heuristic: if the name has no
# MD-identifying prefix and a short common suffix, it's probably vanilla.
# We limit false-positive suppression to a small explicit allowlist of
# patterns, not a broad sweep.
#
# When the vanilla HOI4 install IS detected (Steam path), the validator
# instead reads its interface/*.gfx files directly and adds them to the
# defined-sprites set — much more accurate than the prefix heuristic.
_VANILLA_PREFIXES = (
    "GFX_zoom_",
    "GFX_topbar_",
    "GFX_icon_",
    "GFX_console_",
    "GFX_tutorial_",
    "GFX_empty_",
    "GFX_war_support_",
    "GFX_stability_",
    "GFX_pp_",
    "GFX_politics_",
)

# Common Steam install locations for vanilla HOI4 — used to detect vanilla
# interface/*.gfx for sprite resolution. Mirrors validate_defines.py.
_VANILLA_HOI4_PATHS = [
    os.path.expanduser("~/.local/share/Steam/steamapps/common/Hearts of Iron IV"),
    os.path.expanduser("~/.steam/steam/steamapps/common/Hearts of Iron IV"),
    "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV",
    "C:/Program Files/Steam/steamapps/common/Hearts of Iron IV",
    os.path.expanduser(
        "~/Library/Application Support/Steam/steamapps/common/Hearts of Iron IV"
    ),
]


def _find_vanilla_interface_dir() -> Optional[str]:
    """Return the vanilla HOI4 interface/ directory if discoverable."""
    env_path = os.environ.get("HOI4_PATH")
    if env_path:
        interface = os.path.join(env_path, "interface")
        if os.path.isdir(interface):
            return interface
    for base in _VANILLA_HOI4_PATHS:
        interface = os.path.join(base, "interface")
        if os.path.isdir(interface):
            return interface
    return None


# Max unused sprites to list before summarising remainder
_UNUSED_SPRITE_LIMIT = 50


def _is_dynamic(name: str) -> bool:
    """Return True if name contains template substitution markers."""
    return "[" in name or "]" in name


def _is_flag_sprite(name: str) -> bool:
    """Return True for engine-generated flag/shield sprites."""
    return bool(_FLAG_SPRITE_RE.match(name))


def _is_likely_vanilla(name: str) -> bool:
    """Return True for names that are almost certainly vanilla sprites."""
    return any(name.startswith(p) for p in _VANILLA_PREFIXES)


def _balance_braces(text: str, start: int) -> Optional[int]:
    """Return position of the closing '}' matching the '{' at text[start-1].

    ``start`` is the index *after* the opening brace. Returns None if the
    text is unbalanced.
    """
    depth = 1
    i = start
    n = len(text)
    in_str = False
    while i < n:
        c = text[i]
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            in_str = not in_str
        elif not in_str:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return None


# ---------------------------------------------------------------------------
# Per-file worker functions (top-level so they're picklable)
# ---------------------------------------------------------------------------


def _parse_gfx_file(filepath: str) -> Set[str]:
    """Return the set of GFX sprite names defined in a .gfx file."""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except Exception:
        return set()

    text = _strip_cstyle_comments(raw)
    names: Set[str] = set()

    # Walk sprite-type block openers and extract the name inside each block.
    for m in _GFX_SPRITE_TYPES.finditer(text):
        block_start = m.end()
        block_end = _balance_braces(text, block_start)
        if block_end is None:
            # Fallback: scan remainder of line for name
            line_end = text.find("\n", m.start())
            snippet = text[
                block_start : line_end if line_end != -1 else block_start + 200
            ]
        else:
            snippet = text[block_start:block_end]
        nm = _GFX_NAME.search(snippet)
        if nm:
            names.add(nm.group(1))

    return names


def _parse_gui_file(
    filepath: str,
) -> List[Tuple[str, str, int]]:
    """Return list of (sprite_name, rel_filepath, line_number) from a .gui file."""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except Exception:
        return []

    text = _strip_cstyle_comments(raw)
    offsets = compute_line_offsets(raw)
    results = []
    for m in _GUI_REF.finditer(text):
        sprite = m.group(2)
        if _is_dynamic(sprite):
            continue
        line = line_for_offset(offsets, m.start())
        results.append((sprite, filepath, line))
    return results


def _parse_sgui_file(
    filepath: str,
) -> List[Tuple[str, str, int]]:
    """Return list of (sprite_name, rel_filepath, line_number) from a scripted_gui .txt file."""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except Exception:
        return []

    # scripted_gui .txt files use # comments (Clausewitz script style)
    # but the image = "GFX_xxx" attribute pattern is the same.
    # We don't strip # comments here to avoid stripping scripted loc keys
    # that start with # — just use raw text.
    offsets = compute_line_offsets(raw)
    results = []
    for m in _SGUI_IMAGE_REF.finditer(raw):
        sprite = m.group(1)
        if _is_dynamic(sprite):
            continue
        line = line_for_offset(offsets, m.start())
        results.append((sprite, filepath, line))
    return results


def _parse_sloc_file(
    filepath: str,
) -> List[Tuple[str, str, int]]:
    """Return list of (sprite_name, rel_filepath, line_number) from a scripted_localisation .txt file."""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except Exception:
        return []

    offsets = compute_line_offsets(raw)
    results = []
    for m in _SLOC_KEY_REF.finditer(raw):
        sprite = m.group(1)
        if _is_dynamic(sprite):
            continue
        line = line_for_offset(offsets, m.start())
        results.append((sprite, filepath, line))
    return results


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class GfxReferenceValidator(BaseValidator):
    TITLE = "GFX SPRITE REFERENCE VALIDATION"
    STAGED_EXTENSIONS = [".gui", ".gfx", ".txt"]

    def __init__(self, mod_path: str, **kwargs):
        super().__init__(mod_path, **kwargs)

    # ------------------------------------------------------------------
    # Build phases
    # ------------------------------------------------------------------

    def _build_gfx_definitions(self) -> Tuple[Set[str], Set[str]]:
        """Scan all interface/*.gfx files and return (all_defined, mod_defined).

        `all_defined` includes vanilla HOI4 sprites when a Steam install is
        detected (or HOI4_PATH env var is set) — without that, the validator
        would flag any MD .gui referencing vanilla sprites like GFX_divider
        or GFX_ideology_democratic_group.

        `mod_defined` is just the mod's own sprites — used for the unused-
        sprite check so vanilla never appears in that report.
        """
        self._log_section("Building GFX sprite definition set")
        # Always scan the full repo — definitions must come from anywhere.
        gfx_files = self._collect_files(["interface/*.gfx"], ignore_staged=True)
        results = self._pool_map(_parse_gfx_file, gfx_files)
        mod_defined: Set[str] = set()
        for s in results:
            mod_defined.update(s)
        self.log(
            f"  Found {len(mod_defined)} GFX sprite names across {len(gfx_files)} .gfx files (mod)"
        )

        defined = set(mod_defined)
        vanilla_dir = _find_vanilla_interface_dir()
        if vanilla_dir:
            vanilla_gfx = glob.glob(os.path.join(vanilla_dir, "*.gfx"))
            vanilla_results = self._pool_map(_parse_gfx_file, vanilla_gfx)
            vanilla_defined: Set[str] = set()
            for s in vanilla_results:
                vanilla_defined.update(s)
            new = vanilla_defined - defined
            defined.update(vanilla_defined)
            self.log(
                f"  Found {len(vanilla_defined)} GFX sprite names in vanilla "
                f"({len(new)} new) at {vanilla_dir}"
            )
        else:
            self.log(
                "  Vanilla HOI4 interface/ not detected — set HOI4_PATH to "
                "enable vanilla sprite cross-reference (CI runs without it)"
            )
        return defined, mod_defined

    def _collect_gui_refs(self, defined: Set[str]) -> List[Tuple[str, str, int]]:
        """Return undefined GUI sprite references from interface/*.gui files."""
        self._log_section("Collecting GFX references from interface/*.gui files")
        gui_files = self._collect_files(["interface/*.gui"])
        all_refs: List[Tuple[str, str, int]] = []
        for batch in self._pool_map(_parse_gui_file, gui_files):
            all_refs.extend(batch)
        self.log(
            f"  Scanned {len(gui_files)} .gui files; found {len(all_refs)} GFX references"
        )
        return all_refs

    def _collect_sgui_refs(self, defined: Set[str]) -> List[Tuple[str, str, int]]:
        """Return undefined image= references from common/scripted_guis/*.txt."""
        self._log_section("Collecting GFX image= references from scripted_guis/*.txt")
        sgui_files = self._collect_files(["common/scripted_guis/*.txt"])
        all_refs: List[Tuple[str, str, int]] = []
        for batch in self._pool_map(_parse_sgui_file, sgui_files):
            all_refs.extend(batch)
        self.log(
            f"  Scanned {len(sgui_files)} scripted_gui files; found {len(all_refs)} GFX image= references"
        )
        return all_refs

    def _collect_sloc_refs(self, defined: Set[str]) -> List[Tuple[str, str, int]]:
        """Return GFX references from common/scripted_localisation/*.txt."""
        self._log_section(
            "Collecting GFX localization_key= references from scripted_localisation/*.txt"
        )
        sloc_files = self._collect_files(["common/scripted_localisation/*.txt"])
        all_refs: List[Tuple[str, str, int]] = []
        for batch in self._pool_map(_parse_sloc_file, sloc_files):
            all_refs.extend(batch)
        self.log(
            f"  Scanned {len(sloc_files)} scripted_localisation files; found {len(all_refs)} GFX references"
        )
        return all_refs

    # ------------------------------------------------------------------
    # Check phases
    # ------------------------------------------------------------------

    def _check_undefined_refs(
        self,
        refs: List[Tuple[str, str, int]],
        defined: Set[str],
        source_label: str,
        category: str,
        gui_mode: bool = False,
    ) -> None:
        """Report any sprite names in refs that are not in defined.

        When gui_mode is True, .gui files that are vanilla overrides (not
        MD-authored) are reported as WARNINGs rather than ERRORs, because
        those files legitimately reference vanilla sprites the mod doesn't
        redefine. MD-authored .gui files and all scripted_gui/.txt files
        get ERROR severity.
        """
        errors: List[Tuple[str, str, int]] = []
        warnings: List[Tuple[str, str, int]] = []
        seen: Set[Tuple[str, str, int]] = set()

        for sprite, filepath, line in refs:
            if sprite in defined:
                continue
            if _is_flag_sprite(sprite):
                continue
            if _is_likely_vanilla(sprite):
                continue
            rel = os.path.relpath(filepath, self.mod_path)
            key = (sprite, rel, line)
            if key in seen:
                continue
            seen.add(key)
            entry = (f"Undefined sprite '{sprite}'", rel, line)
            if gui_mode and not _is_md_gui_file(filepath):
                warnings.append(entry)
            else:
                errors.append(entry)

        self._report(
            errors,
            ok_msg=f"All MD-authored {source_label} GFX sprite references are defined.",
            fail_msg=f"Undefined GFX sprite references in MD-authored {source_label}:",
            severity=Severity.ERROR,
            category=category,
        )
        if warnings:
            self._report(
                warnings,
                ok_msg=f"All vanilla-override {source_label} GFX sprite references are defined.",
                fail_msg=(
                    f"Undefined GFX sprite references in vanilla-override {source_label} "
                    f"(likely vanilla sprites not redefined in MD — expected):"
                ),
                severity=Severity.WARNING,
                category=category + "-vanilla",
            )

    def _check_unused_sprites(
        self,
        defined: Set[str],
        all_refs: Set[str],
    ) -> None:
        """Report GFX sprites that are defined but never referenced (warning only).

        Skipped entirely in staged mode to avoid noise — this check needs a
        full-repo scan to be meaningful, but in staged mode we only see a
        subset of files.
        """
        self._log_section("Checking for unused GFX sprite definitions")
        if self.staged_only:
            self.log("  Skipping unused-sprite check in staged mode.")
            return

        unused = sorted(
            s
            for s in defined
            if s not in all_refs
            and not _is_flag_sprite(s)
            and not _is_likely_vanilla(s)
        )

        if not unused:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}  All defined GFX sprites are referenced.{Colors.ENDC if self.use_colors else ''}"
            )
            return

        display = unused[:_UNUSED_SPRITE_LIMIT]
        remainder = len(unused) - len(display)

        issues = [
            (f"Unused GFX sprite '{s}' (defined but never referenced)", "", 0)
            for s in display
        ]
        if remainder > 0:
            issues.append(
                (
                    f"... and {remainder} more unused sprites (run without --staged to see all)",
                    "",
                    0,
                )
            )

        self._report(
            issues,
            ok_msg="All defined GFX sprites are referenced.",
            fail_msg=f"Unused GFX sprite definitions ({len(unused)} total; first {_UNUSED_SPRITE_LIMIT} shown):",
            severity=Severity.WARNING,
            category="unused-sprite",
        )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run_validations(self) -> None:
        # Phase 1: build the complete definition set (always full-repo scan)
        defined, mod_defined = self._build_gfx_definitions()

        # Phase 2: collect all references from the (possibly staged) files
        gui_refs = self._collect_gui_refs(defined)
        sgui_refs = self._collect_sgui_refs(defined)
        sloc_refs = self._collect_sloc_refs(defined)

        # Phase 3: cross-reference checks
        self._log_section("Checking undefined GFX sprite references in .gui files")
        self._check_undefined_refs(
            gui_refs,
            defined,
            source_label=".gui files",
            category="undefined-sprite",
            gui_mode=True,
        )

        self._log_section("Checking undefined GFX sprite references in scripted_guis")
        self._check_undefined_refs(
            sgui_refs,
            defined,
            source_label="scripted_guis",
            category="undefined-sprite",
        )

        self._log_section(
            "Checking undefined GFX sprite references in scripted_localisation"
        )
        self._check_undefined_refs(
            sloc_refs,
            defined,
            source_label="scripted_localisation",
            category="undefined-sprite",
        )

        # Phase 4: unused sprites — only against mod-defined; vanilla sprites the
        # mod doesn't redefine aren't ours to flag as unused.
        all_referenced: Set[str] = {r[0] for r in gui_refs + sgui_refs + sloc_refs}
        self._check_unused_sprites(mod_defined, all_referenced)


def main() -> int:
    return run_validator_main(
        GfxReferenceValidator,
        description="Validate GFX sprite references in Millennium Dawn mod.",
    )


if __name__ == "__main__":
    sys.exit(main())
