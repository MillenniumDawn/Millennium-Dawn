#!/usr/bin/env python3
"""Validate GFX sprite references in interface/*.gui, scripted_guis, and scripted_localisation.

Checks sprites referenced in .gui files (spriteType/quadTextureSprite/background),
scripted_gui image= properties, and scripted_localisation localization_key= against
the set defined in interface/*.gfx. Promotes .gui errors from WARNING to ERROR for
MD-authored files; vanilla-override files stay at WARNING, as do MD-authored nation
variants for refs inherited from the specific vanilla file they copy.
"""

import glob
import os
import re
import sys
from typing import FrozenSet, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import (
    compute_line_offsets,
    extract_block_from_text,
    find_hoi4_install,
    line_for_offset,
    strip_inline_comment,
)
from validator_common import (
    BaseValidator,
    Colors,
    Severity,
    case_mismatch,
    casefold_index,
    run_validator_main,
)

# .gui files in MD fall into two categories:
#   1. MD-authored: files the mod team wrote from scratch (scripted GUIs,
#      country-specific GUIs, feature GUIs). Missing sprites here are real bugs.
#   2. Vanilla overrides: copies of vanilla .gui files with small patches. These
#      reference thousands of vanilla sprites the mod doesn't redefine. Missing
#      sprites here are almost always vanilla refs — flag as WARNING only.
#
# A file is a vanilla override iff its basename matches a vanilla interface/*.gui
# filename, listed in vanilla_gui_files.txt. Everything else is MD-authored. This
# means new MD content of any naming convention is classified correctly with no
# edits here; the manifest only needs regenerating on a HOI4 version bump (see
# refresh_vanilla_data.py).
#
# One carve-out: an MD-authored nation variant (`<vanilla_stem>_<tag>.gui`) that
# inherits a dead ref from the specific vanilla file it copies stays WARNING too —
# that ref is vanilla's bug, not the mod's (see _check_undefined_refs).

_VANILLA_GUI_MANIFEST = os.path.join(os.path.dirname(__file__), "vanilla_gui_files.txt")

# The orphan backlog is ~6.7k warnings and buries the case-mismatch and duplicate
# findings shipped alongside it. Set this to run the full --report-unused pass for
# those findings alone, without the backlog scrolling them off the screen.
_HIDE_UNUSED_ENV = "MD_GFX_HIDE_UNUSED"


def _hide_unused_backlog() -> bool:
    return os.environ.get(_HIDE_UNUSED_ENV, "").strip().lower() not in (
        "",
        "0",
        "false",
    )


def _load_vanilla_gui_basenames() -> frozenset:
    # UnicodeDecodeError too: a corrupt manifest must degrade to "no manifest"
    # rather than crash the validator at module-import time.
    try:
        with open(_VANILLA_GUI_MANIFEST, encoding="utf-8") as fh:
            return frozenset(
                line.strip() for line in fh if line.strip() and not line.startswith("#")
            )
    except (OSError, UnicodeDecodeError):
        # No/unreadable manifest: treat every .gui as MD-authored (fail loud as
        # ERRORs rather than silently downgrading real missing-sprite bugs).
        return frozenset()


_VANILLA_GUI_BASENAMES = _load_vanilla_gui_basenames()


def _is_md_gui_file(filepath: str) -> bool:
    """Return True if this .gui file is MD-authored (not a vanilla override)."""
    return os.path.basename(filepath) not in _VANILLA_GUI_BASENAMES


def _vanilla_parent_basename(filepath: str) -> Optional[str]:
    """Vanilla .gui a nation-variant file copies, or None.

    Country/variant designer GUIs are named ``<vanilla_stem>_<tag>.gui`` (e.g.
    ``tank_chassis_super_heavy_tank_isr.gui`` copies vanilla
    ``tank_chassis_super_heavy_tank.gui``). Strip the trailing ``_<tag>`` segment
    and return it only when the result is a real vanilla basename — used to tie a
    downgraded sprite ref back to the specific vanilla file it was inherited from.
    """
    stem, ext = os.path.splitext(os.path.basename(filepath))
    if "_" not in stem:
        return None
    parent = stem.rsplit("_", 1)[0] + ext
    return parent if parent in _VANILLA_GUI_BASENAMES else None


_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_HASH_COMMENT_RE = re.compile(r"#.*")


def _strip_comments(text: str) -> str:
    """Remove comments from Clausewitz GUI/GFX text.

    `#` is the Clausewitz line-comment marker. `//` is NOT stripped: it never
    appears as a comment in interface/, but does appear inside texture paths
    (`"gfx//interface/..."`), and cutting there leaves an unterminated quote that
    desyncs the quote-aware block scanner and silently drops the sprite.
    """
    text = _BLOCK_COMMENT_RE.sub("", text)
    text = _HASH_COMMENT_RE.sub("", text)
    return text


# Renderable GFX block openers in .gfx files. Names may be quoted or bare.
_GFX_SPRITE_TYPES = re.compile(
    r"\b(?:spriteType|frameAnimatedSpriteType|corneredTileSpriteType|"
    r"maskedShieldType|progressbartype|textSpriteType|pieChartType|"
    r"lineChartType|circularProgressBarType)\s*=\s*\{",
    re.IGNORECASE,
)

# name = GFX_xxx or name = "GFX_xxx" inside a block. `@` appears in engine
# frame-variant names (e.g. GFX_x@highlight); `.` and `-` occur in mod sprites.
_GFX_NAME = re.compile(
    r'\bname\s*=\s*(?:"(GFX_[A-Za-z0-9_.@-]+)"|(GFX_[A-Za-z0-9_.@-]+))'
)

# textureFile / texturefile inside a sprite block — the art a definition points at.
_GFX_TEXTUREFILE = re.compile(r'\btexture[fF]ile\s*=\s*"([^"]+)"', re.IGNORECASE)

# Property names are case-insensitive; quotes are optional. GFX_ stays exact.
_GUI_REF = re.compile(
    r"\b(?i:spriteType|quadTextureSprite|background)\s*=\s*"
    r'(?:"(GFX_[^"\[]+)"|(GFX_[A-Za-z0-9_.@-]+))'
)

# Scripted GUI properties: image = "GFX_xxx"
_SGUI_IMAGE_REF = re.compile(r'\bimage\s*=\s*"(GFX_[^"\[]+)"')

# Scripted localisation: localization_key = "GFX_xxx"
_SLOC_KEY_REF = re.compile(r'\blocalization_key\s*=\s*"(GFX_[^"\[]+)"')

# The same two attributes, but keeping the `[` those exclude — a bracket is what
# marks a name the engine builds at runtime (GFX_missile_[THIS.GetTag]_ID_[?v]_icon).
_SPRITE_TEMPLATE_REF = re.compile(
    r'\b(?:localization_key|image)\s*=\s*"(GFX_[^"]*\[[^"]*)"'
)

# Any literal GFX_ sprite token in game script (event `picture = GFX_x`, focus
# `icon = GFX_x`, decision icons, MIO/agency logos, portraits, etc.). Names can
# carry `.` frame suffixes and `-`. Used only to mark sprites as referenced for
# the unused-sprite check, so over-matching (e.g. a token in a string) is safe.
_GFX_TOKEN_REF = re.compile(r"GFX_[A-Za-z0-9_.\-]+")
_HASH_COMMENT = re.compile(r"#[^\n]*")

# Localisation sprite reference: `£name` renders the sprite `GFX_name` (an
# optional `|frame` suffix may follow). Party, idea and money icons are often
# referenced this way and nowhere else, so skipping .yml mis-reports them as
# unused. `£GFX_name` also occurs, hence both spellings are recorded. Names can
# carry `.` frame suffixes and `-`, same as _GFX_TOKEN_REF.
_LOC_SPRITE_REF = re.compile(r"£([A-Za-z0-9_.\-]+)")
# Idea `picture = X` resolves to the sprite `GFX_idea_X` (X is not GFX_-prefixed).
_IDEA_PICTURE_REF = re.compile(r"^\s*picture\s*=\s*([A-Za-z0-9_.\-]+)", re.MULTILINE)

# Auto-generated flag sprites — never defined in .gfx, built by the engine.
# Matches GFX_flag_TAG, GFX_TAG_flag, GFX_shield_TAG etc.
_FLAG_SPRITE_RE = re.compile(
    r"^GFX_(?:flag_|.*_flag$|.*_coat_of_arms$|.*_shield$)", re.IGNORECASE
)

# Vanilla sprite names come from three sources, best first:
#   1. A live HOI4 install (Steam path or $HOI4_PATH): interface/*.gfx read
#      directly and folded into the defined-sprites set.
#   2. The committed vanilla_sprites.txt manifest (generated from a local
#      install by refresh_vanilla_data.py) — what CI uses.
#   3. The _VANILLA_PREFIXES heuristic below, only when neither exists:
#      accept vanilla-looking names rather than false-positive on them.
_VANILLA_SPRITES_MANIFEST = os.path.join(
    os.path.dirname(__file__), "vanilla_sprites.txt"
)


def _load_vanilla_sprite_manifest() -> FrozenSet[str]:
    # UnicodeDecodeError too: decoding happens lazily during iteration, and a
    # corrupt manifest should degrade to the heuristic, not crash the run.
    try:
        with open(_VANILLA_SPRITES_MANIFEST, encoding="utf-8") as fh:
            return frozenset(
                line.strip() for line in fh if line.strip() and not line.startswith("#")
            )
    except (OSError, UnicodeDecodeError):
        return frozenset()


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


def _find_vanilla_interface_dir() -> Optional[str]:
    """Return the vanilla HOI4 interface/ directory if discoverable."""
    base = find_hoi4_install()
    if base:
        interface = os.path.join(base, "interface")
        if os.path.isdir(interface):
            return interface
    return None


def _vanilla_gfx_files() -> List[str]:
    """Return every vanilla .gfx path, including DLC interface dirs.

    DLC sprites (dlc/*/interface, integrated_dlc/*/interface) are referenced by
    vanilla-override .gui files, so omitting them false-positives those refs.
    """
    base = find_hoi4_install()
    if not base:
        return []
    files = glob.glob(os.path.join(base, "interface", "**", "*.gfx"), recursive=True)
    for sub in ("dlc", "integrated_dlc"):
        files.extend(
            glob.glob(
                os.path.join(base, sub, "*", "interface", "**", "*.gfx"),
                recursive=True,
            )
        )
    return sorted(files)


def _vanilla_gui_files() -> List[str]:
    """Return every vanilla .gui path, including DLC interface dirs."""
    base = find_hoi4_install()
    if not base:
        return []
    files = glob.glob(os.path.join(base, "interface", "**", "*.gui"), recursive=True)
    for sub in ("dlc", "integrated_dlc"):
        files.extend(
            glob.glob(
                os.path.join(base, sub, "*", "interface", "**", "*.gui"),
                recursive=True,
            )
        )
    return sorted(files)


def _vanilla_gui_ref_index() -> dict:
    """Map each vanilla .gui basename to the GFX sprite names it references.

    Lets a nation-variant file (``<stem>_<tag>.gui``) be forgiven a dead ref its
    real vanilla parent carries even when the mod ships no full-name override of
    that parent — without a live install the mod's own override map is the only
    signal, and a variant added alone would false-positive to ERROR. Empty when
    no vanilla install is discoverable (CI), so callers keep current behaviour.
    """
    index: dict = {}
    for path in _vanilla_gui_files():
        raw = _read_raw(path)
        if raw is None:
            continue
        text = _strip_comments(raw)
        refs = index.setdefault(os.path.basename(path), set())
        for m in _GUI_REF.finditer(text):
            sprite = m.group(1) or m.group(2)
            if not _is_dynamic(sprite):
                refs.add(sprite)
    return index


def _is_dynamic(name: str) -> bool:
    """Return True if name contains template substitution markers."""
    return "[" in name or "]" in name


def _is_flag_sprite(name: str) -> bool:
    """Return True for engine-generated flag/shield sprites."""
    return bool(_FLAG_SPRITE_RE.match(name))


def _is_likely_vanilla(name: str) -> bool:
    """Return True for names that are almost certainly vanilla sprites."""
    return any(name.startswith(p) for p in _VANILLA_PREFIXES)


# Three sprite families are resolved by the engine from an equipment archetype or
# a technology id and are never named literally in script, so the unused check
# needs both lists to tell a real orphan from an engine-resolved icon:
#   equipment icons         GFX_util_vehicle_1_medium, GFX_AFG_util_vehicle_1_medium
#   country tech-tree icons GFX_BEL_SAM0_medium
#   designer profile icons  GFX_BRA_MBT_1 (no size suffix, country tag required)
_EQUIPMENT_ICON_RE = re.compile(r"^GFX_(.+?)_(?:small|medium|large)$")
# Stripped as a second attempt only. Folding the optional tag into the pattern
# above swallows the archetype's own prefix (APC_1 → "1"), because the match
# succeeds either way and never backtracks. Tags are a letter plus two
# alphanumerics (BRA, C01).
_EQUIPMENT_ICON_TAG_RE = re.compile(r"^[A-Z][A-Z0-9]{2}_(.+)$")
# Only entries directly inside `equipments = { }` / `technologies = { }` count.
# Matching any one-tab key would also pick up container keys such as `values` in
# tank_filters.txt, which could mask a genuinely dead sprite.
_EQUIPMENTS_BLOCK_RE = re.compile(r"^equipments\s*=\s*\{", re.MULTILINE)
_TECHNOLOGIES_BLOCK_RE = re.compile(r"^technologies\s*=\s*\{", re.MULTILINE)
_MODULES_BLOCK_RE = re.compile(r"^equipment_modules\s*=\s*\{", re.MULTILINE)
_SUB_UNITS_BLOCK_RE = re.compile(r"^sub_units\s*=\s*\{", re.MULTILINE)
_SUB_UNIT_CATEGORIES_BLOCK_RE = re.compile(
    r"^sub_unit_categories\s*=\s*\{", re.MULTILINE
)
_EQUIPMENT_ENTRY_RE = re.compile(r"^\t([A-Za-z][A-Za-z0-9_]*)\s*=\s*\{", re.MULTILINE)
_UNIT_ICON_SUFFIXES = (
    "_icon_small",
    "_icon_medium",
    "_icon_small_white",
    "_icon_medium_white",
    "_icon_medium_black",
)

# The equipment designer draws GFX_EMI_<name> for both halves of the module
# system: the module itself, and the category its slot accepts. A category is
# never declared on its own — it exists because a module claims it and a chassis
# slot allows it, so both spellings have to be harvested or live category icons
# (GFX_EMI_afv_gasoline_engine_type) read as orphans.
_MODULE_CATEGORY_RE = re.compile(
    r"^\s*(?:module_)?category\s*=\s*([A-Za-z][A-Za-z0-9_]*)", re.MULTILINE
)
_ALLOWED_CATEGORIES_RE = re.compile(r"\ballowed_module_categories\s*=\s*\{([^}]*)\}")

# Focus search-filter icons: a focus tags itself `search_filters = { FOCUS_FILTER_X }`
# and the engine swaps GFX_FOCUS_FILTER_X into the filter button at runtime — vanilla's
# nationalfocusview.gui only carries GFX_FOCUS_FILTER_POLITICAL as the template
# placeholder, so no other filter icon is ever named literally.
_SEARCH_FILTERS_RE = re.compile(r"\bsearch_filters\s*=\s*\{([^}]*)\}")

# Ace portraits. The engine picks GFX_<TAG>_ace_<m|f>_<n>, falling back to the
# country's graphical culture (GFX_african_2d_ace_f_0) and then the generic pool
# (GFX_ace_m_2). The pool name is the only variable part, so resolving one means
# checking it against the tags and cultures the mod actually declares.
_ACE_PORTRAIT_RE = re.compile(r"^GFX_(?:(?P<pool>.+)_)?ace_[mf]_\d+$")
_COUNTRY_TAG_RE = re.compile(r'^\s*([A-Z0-9_]{3})\s*=\s*"', re.MULTILINE)
_GRAPHICAL_CULTURE_RE = re.compile(
    r"^\s*graphical_culture(?:_2d)?\s*=\s*([A-Za-z0-9_]+)", re.MULTILINE
)

# A `[...]` placeholder inside a sprite name is filled at runtime, so the literal
# template never matches a definition. Turning it into a pattern resolves the
# concrete sprites it can produce — but only when enough literal text survives to
# identify them: `GFX_[?topbar.GetTokenKey]` would otherwise match every sprite.
_TEMPLATE_PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]")
_TEMPLATE_MIN_LITERAL = 4


def _entry_names_from_text(raw: str, block_re: "re.Pattern[str]") -> List[str]:
    """Return the one-tab entry names declared inside every `block_re` block."""
    text = _HASH_COMMENT.sub("", raw)
    names: Set[str] = set()
    for block in block_re.finditer(text):
        body, _end = extract_block_from_text(text, block.start())
        if body:
            names.update(_EQUIPMENT_ENTRY_RE.findall(body))
    return sorted(names)


def _search_filter_names_from_text(raw: str) -> List[str]:
    """Return every token listed inside a `search_filters = { }` block."""
    text = _HASH_COMMENT.sub("", raw)
    names: Set[str] = set()
    for block in _SEARCH_FILTERS_RE.finditer(text):
        names.update(block.group(1).split())
    return sorted(names)


def _iter_txt_files(root: str, *, recursive: bool = True) -> List[str]:
    """Return `.txt` paths under `root`. Missing dirs yield an empty list."""
    if not recursive:
        try:
            return [
                os.path.join(root, fn)
                for fn in os.listdir(root)
                if fn.endswith(".txt") and os.path.isfile(os.path.join(root, fn))
            ]
        except OSError:
            return []
    files: List[str] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".txt"):
                files.append(os.path.join(dirpath, fn))
    return files


def _load_names_from_dir(
    mod_path: str, root: str, parse, namespace: str, *, recursive: bool = True
) -> FrozenSet[str]:
    """Return every name `parse` finds under `root`, content-cached per file."""
    names: Set[str] = set()
    for filepath in _iter_txt_files(root, recursive=recursive):
        try:
            with open(filepath, encoding="utf-8-sig", errors="replace") as fh:
                raw = fh.read()
        except OSError:
            continue
        names.update(
            disk_cache.per_file_cached_by_content(
                mod_path, namespace, filepath, raw, lambda: parse(raw)
            )
        )
    return frozenset(names)


def _load_entry_names(
    mod_path: str, root: str, block_re: "re.Pattern[str]", namespace: str
) -> FrozenSet[str]:
    """Return every entry name declared under `root`, content-cached per file."""
    return _load_names_from_dir(
        mod_path, root, lambda raw: _entry_names_from_text(raw, block_re), namespace
    )


def _equipment_tree_from_text(raw: str) -> Tuple[List[str], List[str]]:
    """Return (equipment entries, module/category names) from one equipment file."""
    return (
        _entry_names_from_text(raw, _EQUIPMENTS_BLOCK_RE),
        _module_icon_names_from_text(raw),
    )


def _load_equipment_tree(mod_path: str) -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """Return cached (equipment names, module/category names) for the equipment tree."""
    root = os.path.join(mod_path, "common", "units", "equipment")
    tracked = _iter_txt_files(root)

    def _build() -> Tuple[FrozenSet[str], FrozenSet[str]]:
        equipment: Set[str] = set()
        modules: Set[str] = set()
        for filepath in tracked:
            try:
                with open(filepath, encoding="utf-8-sig", errors="replace") as fh:
                    raw = fh.read()
            except OSError:
                continue
            eq_names, module_names = disk_cache.per_file_cached_by_content(
                mod_path,
                "gfx_ref.equipment_tree",
                filepath,
                raw,
                lambda: _equipment_tree_from_text(raw),
            )
            equipment.update(eq_names)
            modules.update(module_names)
        return frozenset(equipment), frozenset(modules)

    return disk_cache.aggregate_cached(
        mod_path,
        "gfx_ref.equipment_tree.aggregate",
        tracked,
        _build,
        namespace="gfx_ref",
    )


def _load_equipment_names(mod_path: str) -> FrozenSet[str]:
    """Return every equipment archetype/variant declared in common/units/equipment."""
    return _load_equipment_tree(mod_path)[0]


def _load_technology_names(mod_path: str) -> FrozenSet[str]:
    """Return every technology id declared in common/technologies."""
    return _load_entry_names(
        mod_path,
        os.path.join(mod_path, "common", "technologies"),
        _TECHNOLOGIES_BLOCK_RE,
        "gfx_ref.tech_names",
    )


def _load_search_filter_names(mod_path: str) -> FrozenSet[str]:
    """Return every search_filters token used in common/national_focus."""
    return _load_names_from_dir(
        mod_path,
        os.path.join(mod_path, "common", "national_focus"),
        _search_filter_names_from_text,
        "gfx_ref.search_filters",
    )


def _module_icon_names_from_text(raw: str) -> List[str]:
    """Return every module and module category an equipment file declares."""
    text = _HASH_COMMENT.sub("", raw)
    names: Set[str] = set(_entry_names_from_text(text, _MODULES_BLOCK_RE))
    names.update(_MODULE_CATEGORY_RE.findall(text))
    for block in _ALLOWED_CATEGORIES_RE.finditer(text):
        names.update(block.group(1).split())
    return sorted(names)


def _load_module_icon_names(mod_path: str) -> FrozenSet[str]:
    """Return every module and category the designer can draw an icon for."""
    return _load_equipment_tree(mod_path)[1]


def _unit_category_names_from_text(raw: str) -> List[str]:
    """Return every token listed inside a `sub_unit_categories = { }` block."""
    text = _HASH_COMMENT.sub("", raw)
    names: Set[str] = set()
    for block in _SUB_UNIT_CATEGORIES_BLOCK_RE.finditer(text):
        body, _end = extract_block_from_text(text, block.start())
        if body:
            names.update(body.split())
    return sorted(names)


def _load_unit_icon_names(mod_path: str) -> FrozenSet[str]:
    """Return every subunit and unit category the engine can draw a counter for."""
    names = set(
        _load_names_from_dir(
            mod_path,
            os.path.join(mod_path, "common", "units"),
            lambda raw: _entry_names_from_text(raw, _SUB_UNITS_BLOCK_RE),
            "gfx_ref.unit_names",
            recursive=False,
        )
    )
    names.update(
        _load_names_from_dir(
            mod_path,
            os.path.join(mod_path, "common", "unit_tags"),
            _unit_category_names_from_text,
            "gfx_ref.unit_categories",
        )
    )
    return frozenset(names)


_ENGINE_DECLARATION_FAMILIES = (
    (
        _load_search_filter_names,
        "  No search_filters found under common/national_focus"
        " — focus-filter icons unresolved",
        ("GFX_{name}",),
    ),
    (
        _load_module_icon_names,
        "  No equipment modules found under common/units/equipment"
        " — module icons unresolved",
        ("GFX_EMI_{name}", "GFX_SMI_{name}"),
    ),
    (
        _load_unit_icon_names,
        "  No sub-units or unit categories found — unit icons unresolved",
        tuple("GFX_unit_{name}" + suffix for suffix in _UNIT_ICON_SUFFIXES),
    ),
)


def _declaration_engine_source_files(mod_path: str) -> List[str]:
    """Return the files that feed declaration-derived engine sprites."""
    return (
        _iter_txt_files(os.path.join(mod_path, "common", "national_focus"))
        + _iter_txt_files(os.path.join(mod_path, "common", "units", "equipment"))
        + _iter_txt_files(os.path.join(mod_path, "common", "units"), recursive=False)
        + _iter_txt_files(os.path.join(mod_path, "common", "unit_tags"))
    )


def _declaration_engine_refs(
    mod_path: str,
) -> Tuple[FrozenSet[str], Tuple[str, ...]]:
    """Return cached declaration-derived engine sprites plus empty-source notices."""

    def _build() -> Tuple[FrozenSet[str], Tuple[str, ...]]:
        refs: Set[str] = set()
        notices: List[str] = []
        for load, notice, templates in _ENGINE_DECLARATION_FAMILIES:
            names = load(mod_path)
            if not names:
                notices.append(notice)
            refs.update(t.format(name=n) for t in templates for n in names)
        return frozenset(refs), tuple(notices)

    return disk_cache.aggregate_cached(
        mod_path,
        "gfx_ref.declaration_engine_refs",
        _declaration_engine_source_files(mod_path),
        _build,
        namespace="gfx_ref",
    )


def _load_ace_pool_names(mod_path: str) -> FrozenSet[str]:
    """Return every country tag and graphical culture an ace portrait can key off."""
    names: Set[str] = set()
    for pattern, name_re in (
        (os.path.join("common", "country_tags", "*.txt"), _COUNTRY_TAG_RE),
        (os.path.join("common", "countries", "*.txt"), _GRAPHICAL_CULTURE_RE),
    ):
        for filepath in glob.glob(os.path.join(mod_path, pattern)):
            raw = _read_raw(filepath)
            if raw is None:
                continue

            def _ace_names(text: str = raw) -> list[str]:
                return sorted(set(name_re.findall(_HASH_COMMENT.sub("", text))))

            names.update(
                disk_cache.per_file_cached_by_content(
                    mod_path, "gfx_ref.ace_pools", filepath, raw, _ace_names
                )
            )
    return frozenset(names)


def _template_pattern(template: str) -> Optional["re.Pattern[str]"]:
    """Compile a `GFX_x_[placeholder]_y` sprite template into a matcher.

    Returns None when the literal text outside the placeholders is too short to
    identify anything — `GFX_[?topbar.GetTokenKey]` names every sprite in the mod,
    so treating it as a reference would mark the whole repo as used.
    """
    stripped = _TEMPLATE_PLACEHOLDER_RE.sub("", template)
    literal = stripped[len("GFX_") :] if stripped.startswith("GFX_") else stripped
    if len(literal.replace("_", "")) < _TEMPLATE_MIN_LITERAL:
        return None
    pattern = "".join(
        r"[A-Za-z0-9_.\-]+" if part.startswith("[") else re.escape(part)
        for part in re.split(r"(\[[^\]]*\])", template)
        if part
    )
    try:
        return re.compile(f"^{pattern}$")
    except re.error as _e:
        return None


# Per-file parsers take (filepath, mod_path) and disk-cache their result keyed
# on file content, so a warm run only re-parses changed files. .gfx/.gui scans
# cover all of interface/, so the cache is the bulk of the speedup.


def _read_raw(filepath: str) -> Optional[str]:
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            return fh.read()
    except Exception:
        return None


def sprite_defs_from_gfx_text(raw: str) -> List[Tuple[str, str, int]]:
    """Return (sprite_name, texturefile, line) for every definition in .gfx content.

    One entry per spriteType block, duplicates included — the duplicate-name check
    needs to see a name defined twice, which a set would silently collapse. The
    texturefile tells a harmless repeat of the same art from a silent override of
    two different textures under one name.
    """
    text = _strip_comments(raw)
    offsets = compute_line_offsets(text)
    defs: List[Tuple[str, str, int]] = []
    for m in _GFX_SPRITE_TYPES.finditer(text):
        block_start = m.end()
        snippet, end = extract_block_from_text(text, block_start - 1)
        if end == -1:
            # Unbalanced braces: fall back to scanning the rest of the line.
            line_end = text.find("\n", m.start())
            snippet = text[
                block_start : line_end if line_end != -1 else block_start + 200
            ]
        nm = _GFX_NAME.search(snippet)
        if nm:
            tx = _GFX_TEXTUREFILE.search(snippet)
            defs.append(
                (
                    nm.group(1) or nm.group(2),
                    tx.group(1) if tx else "",
                    line_for_offset(offsets, m.start()),
                )
            )
    return defs


def sprite_names_from_gfx_text(raw: str) -> Set[str]:
    """Return the set of GFX sprite names defined in raw .gfx file content.

    Shared with refresh_vanilla_data.py so the committed manifest is
    built with exactly the parse the validator applies to mod files.
    """
    return {name for name, _tx, _line in sprite_defs_from_gfx_text(raw)}


def _parse_gfx_file(args: Tuple[str, str]) -> List[Tuple[str, str, str, int]]:
    """Return (sprite_name, filepath, texturefile, line) for each def in a .gfx file."""
    filepath, mod_path = args
    raw = _read_raw(filepath)
    if raw is None:
        return []

    def _compute() -> List[Tuple[str, str, str, int]]:
        return [
            (name, filepath, texture, line)
            for name, texture, line in sprite_defs_from_gfx_text(raw)
        ]

    return disk_cache.per_file_cached_by_content(
        mod_path, "gfx_ref.gfx", filepath, raw, _compute
    )


def _parse_gui_file(args: Tuple[str, str]) -> List[Tuple[str, str, int]]:
    """Return list of (sprite_name, rel_filepath, line_number) from a .gui file."""
    filepath, mod_path = args
    raw = _read_raw(filepath)
    if raw is None:
        return []

    def _compute():
        text = _strip_comments(raw)
        offsets = compute_line_offsets(raw)
        results = []
        for m in _GUI_REF.finditer(text):
            sprite = m.group(1) or m.group(2)
            if _is_dynamic(sprite):
                continue
            line = line_for_offset(offsets, m.start())
            results.append((sprite, filepath, line))
        return results

    return disk_cache.per_file_cached_by_content(
        mod_path, "gfx_ref.gui", filepath, raw, _compute
    )


def _parse_sgui_file(args: Tuple[str, str]) -> List[Tuple[str, str, int]]:
    """Return list of (sprite_name, rel_filepath, line_number) from a scripted_gui .txt file."""
    filepath, mod_path = args
    raw = _read_raw(filepath)
    if raw is None:
        return []

    def _compute():
        # scripted_gui .txt files use # comments (Clausewitz script style) but the
        # image = "GFX_xxx" attribute pattern is the same. We don't strip # comments
        # here to avoid stripping scripted loc keys that start with # — use raw text.
        offsets = compute_line_offsets(raw)
        results = []
        for m in _SGUI_IMAGE_REF.finditer(raw):
            sprite = m.group(1)
            if _is_dynamic(sprite):
                continue
            line = line_for_offset(offsets, m.start())
            results.append((sprite, filepath, line))
        return results

    return disk_cache.per_file_cached_by_content(
        mod_path, "gfx_ref.sgui", filepath, raw, _compute
    )


def _parse_script_refs(args: Tuple[str, str]) -> List[str]:
    """Return every GFX sprite a game-script .txt file references.

    Picks up literal `GFX_xxx` tokens (event pictures, focus/decision icons,
    MIO and agency logos, portraits, etc.) plus idea `picture = X` entries,
    which resolve to `GFX_idea_X`. Comment lines are stripped first so a
    commented-out reference does not mask a genuinely unused sprite. Content-
    cached, so a warm run only re-scans changed files.
    """
    filepath, mod_path = args
    raw = _read_raw(filepath)
    if raw is None:
        return []

    def _compute() -> List[str]:
        text = _HASH_COMMENT.sub("", raw)
        refs = set(_GFX_TOKEN_REF.findall(text))
        if os.sep + "ideas" + os.sep in filepath:
            for m in _IDEA_PICTURE_REF.finditer(text):
                refs.add("GFX_idea_" + m.group(1))
        return sorted(refs)

    return disk_cache.per_file_cached_by_content(
        mod_path, "gfx_ref.script", filepath, raw, _compute
    )


def _parse_loc_refs(args: Tuple[str, str]) -> List[Tuple[str, str, int]]:
    """Return (sprite_name, filepath, line) for every `£name` in a localisation .yml."""
    filepath, mod_path = args
    raw = _read_raw(filepath)
    if raw is None:
        return []

    def _compute() -> List[Tuple[str, str, int]]:
        text = "\n".join(strip_inline_comment(line) for line in raw.splitlines())
        offsets = compute_line_offsets(text)
        seen: Set[str] = set()
        results: List[Tuple[str, str, int]] = []
        for m in _LOC_SPRITE_REF.finditer(text):
            # Sentence-final punctuation (`£command_power.`) is not part of the name.
            name = m.group(1).rstrip(".-")
            if not name:
                continue
            if not name.startswith("GFX_"):
                name = "GFX_" + name
            if name in seen:
                continue
            seen.add(name)
            results.append((name, filepath, line_for_offset(offsets, m.start())))
        return results

    return disk_cache.per_file_cached_by_content(
        mod_path, "gfx_ref.loc", filepath, raw, _compute
    )


def _parse_sprite_templates(args: Tuple[str, str]) -> List[str]:
    """Return every runtime-built `GFX_...[...]...` sprite name in a scripted file.

    Comments are left in place for the same reason `_parse_sloc_file` leaves them:
    a scripted loc key may legitimately start with `#`.
    """
    filepath, mod_path = args
    raw = _read_raw(filepath)
    if raw is None:
        return []

    return disk_cache.per_file_cached_by_content(
        mod_path,
        "gfx_ref.templates",
        filepath,
        raw,
        lambda: sorted(set(_SPRITE_TEMPLATE_REF.findall(raw))),
    )


def _parse_sloc_file(args: Tuple[str, str]) -> List[Tuple[str, str, int]]:
    """Return list of (sprite_name, rel_filepath, line_number) from a scripted_localisation .txt file."""
    filepath, mod_path = args
    raw = _read_raw(filepath)
    if raw is None:
        return []

    def _compute():
        offsets = compute_line_offsets(raw)
        results = []
        for m in _SLOC_KEY_REF.finditer(raw):
            sprite = m.group(1)
            if _is_dynamic(sprite):
                continue
            line = line_for_offset(offsets, m.start())
            results.append((sprite, filepath, line))
        return results

    return disk_cache.per_file_cached_by_content(
        mod_path, "gfx_ref.sloc", filepath, raw, _compute
    )


class Validator(BaseValidator):
    TITLE = "GFX SPRITE REFERENCE VALIDATION"
    STAGED_EXTENSIONS = [".gui", ".gfx", ".txt"]

    def __init__(self, mod_path: str, report_unused: bool = False, **kwargs):
        super().__init__(mod_path, **kwargs)
        self.report_unused = report_unused
        # True once vanilla sprite names (live install or manifest) were folded
        # into the defined set — disables the _is_likely_vanilla heuristic.
        self._vanilla_defs_loaded = False
        # The vanilla names themselves, for the unused check's override exemption.
        self._vanilla_defined: Set[str] = set()
        # Every mod definition site (name, file, texturefile, line) for the
        # duplicate-name check.
        self._mod_defs: List[Tuple[str, str, str, int]] = []

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
        gfx_files = self._collect_files(["interface/**/*.gfx"], ignore_staged=True)
        results = self._pool_map(
            _parse_gfx_file, [(f, self.mod_path) for f in gfx_files]
        )
        for batch in results:
            self._mod_defs.extend(batch)
        mod_defined: Set[str] = {name for name, _f, _tx, _l in self._mod_defs}
        self.log(
            f"  Found {len(mod_defined)} GFX sprite names across {len(gfx_files)} .gfx files (mod)"
        )

        defined = set(mod_defined)
        vanilla_gfx = _vanilla_gfx_files()
        if vanilla_gfx:
            vanilla_results = self._pool_map(
                _parse_gfx_file, [(f, self.mod_path) for f in vanilla_gfx]
            )
            vanilla_defined: Set[str] = {
                name for batch in vanilla_results for name, _f, _tx, _l in batch
            }
            new = vanilla_defined - defined
            defined.update(vanilla_defined)
            self._vanilla_defs_loaded = True
            self._vanilla_defined = vanilla_defined
            self.log(
                f"  Found {len(vanilla_defined)} GFX sprite names in vanilla "
                f"({len(new)} new) across {len(vanilla_gfx)} .gfx files"
            )
        else:
            manifest = _load_vanilla_sprite_manifest()
            if manifest:
                new = set(manifest) - defined
                defined.update(manifest)
                self._vanilla_defs_loaded = True
                self._vanilla_defined = set(manifest)
                self.log(
                    f"  Loaded {len(manifest)} vanilla GFX sprite names from "
                    f"vanilla_sprites.txt ({len(new)} new)"
                )
            else:
                self.log(
                    "  No vanilla HOI4 install detected and no vanilla_sprites.txt"
                    " manifest — set HOI4_PATH or run"
                    " refresh_vanilla_data.py (prefix heuristic active)"
                )
        return defined, mod_defined

    def _collect_gui_refs(self, defined: Set[str]) -> List[Tuple[str, str, int]]:
        """Return undefined GUI sprite references from interface/*.gui files."""
        self._log_section("Collecting GFX references from interface/*.gui files")
        # Full-repo scan even under --staged: a variant file's inherited refs are
        # only downgradable when their vanilla parent/override is in view, so the
        # ref universe must not be staged-limited (would escalate WARNING->ERROR).
        gui_files = self._collect_files(["interface/**/*.gui"], ignore_staged=True)
        all_refs: List[Tuple[str, str, int]] = []
        for batch in self._pool_map(
            _parse_gui_file, [(f, self.mod_path) for f in gui_files]
        ):
            all_refs.extend(batch)
        self.log(
            f"  Scanned {len(gui_files)} .gui files; found {len(all_refs)} GFX references"
        )
        return all_refs

    def _collect_script_refs(self) -> Set[str]:
        """Return every GFX sprite referenced from game script (events, common, history, gfx).

        Feeds the unused-sprite check so sprites used as event pictures, focus or
        decision icons, MIO/agency logos, portraits, etc. are not mis-reported as
        unused just because they are not referenced from interface/.
        """
        self._log_section(
            "Collecting GFX references from game script (events/common/history/gfx)"
        )
        files = self._collect_files(
            ["events/**/*.txt", "common/**/*.txt", "history/**/*.txt"],
            ignore_staged=True,
        )
        # should_skip_file ignores gfx/ wholesale, so _collect_files can't reach
        # the equipment-designer graphic_db there — and it names sprites literally.
        files.extend(
            glob.iglob(
                os.path.join(self.mod_path, "gfx", "**", "*.txt"), recursive=True
            )
        )
        refs: Set[str] = set()
        for batch in self._pool_map(
            _parse_script_refs, [(f, self.mod_path) for f in files]
        ):
            refs.update(batch)
        self.log(
            f"  Scanned {len(files)} script files; found {len(refs)} distinct GFX references"
        )
        return refs

    def _collect_loc_refs(self) -> List[Tuple[str, str, int]]:
        """Return every GFX sprite referenced from localisation via `£name`.

        Every language is scanned, not just English: a `£` reference is a real
        sprite use whichever file it sits in.
        """
        self._log_section("Collecting GFX £sprite references from localisation/*.yml")
        files = self._collect_files(["localisation/**/*.yml"], ignore_staged=True)
        all_refs: List[Tuple[str, str, int]] = []
        for batch in self._pool_map(
            _parse_loc_refs, [(f, self.mod_path) for f in files]
        ):
            all_refs.extend(batch)
        self.log(
            f"  Scanned {len(files)} localisation files;"
            f" found {len({r[0] for r in all_refs})} distinct GFX references"
        )
        return all_refs

    def _resolve_engine_refs(self, defined: Set[str]) -> Set[str]:
        """Return the sprites the engine resolves from mod data rather than script.

        These are real references, not exemptions: each one is derived from a
        declaration the mod ships, so a sprite whose module, tag or filter has
        since been deleted still reports as unused, and a sprite spelled with the
        wrong case still reports as miscased instead of quietly passing.

            GFX_<FOCUS_FILTER_X>          every search_filters token in a focus tree
            GFX_EMI_<module|category>     equipment modules and the slot categories
                                          they claim / a chassis slot allows
            GFX_SMI_<module|category>     the same names, ship-designer prefix
            GFX_unit_<subunit|category>_icon_{small,medium}[_white|_black]
                                          battalion counters from sub_units and
                                          unit_tags
            GFX_<TAG|culture>_ace_<m|f>_N ace portraits, keyed by tag or 2d culture
            GFX_missile_<TAG>_ID_<N>_icon and anything else a `[...]` scripted-loc
                                          or scripted-GUI template can build
        """
        self._log_section("Resolving engine-built GFX references from mod data")
        declared, notices = _declaration_engine_refs(self.mod_path)
        refs: Set[str] = set(declared)
        for notice in notices:
            self.log(notice)

        pools = _load_ace_pool_names(self.mod_path)
        if not pools:
            self.log(
                "  No country tags or graphical cultures found"
                " — ace portraits unresolved"
            )
        for name in defined:
            ace = _ACE_PORTRAIT_RE.match(name)
            # A pool-less GFX_ace_m_0 is the engine's own last-resort fallback.
            if ace and (ace.group("pool") is None or ace.group("pool") in pools):
                refs.add(name)

        template_files = self._collect_files(
            ["common/scripted_localisation/*.txt", "common/scripted_guis/*.txt"],
            ignore_staged=True,
        )
        templates: Set[str] = set()
        for batch in self._pool_map(
            _parse_sprite_templates, [(f, self.mod_path) for f in template_files]
        ):
            templates.update(batch)
        patterns = [p for p in map(_template_pattern, sorted(templates)) if p]
        skipped = len(templates) - len(patterns)
        if skipped:
            self.log(
                f"  {skipped} sprite template(s) too generic to resolve"
                " (nothing but a placeholder after GFX_)"
            )
        for name in defined:
            if any(p.match(name) for p in patterns):
                refs.add(name)

        self.log(
            f"  Resolved {len(refs)} engine-built GFX references"
            f" from {len(patterns)} template(s) plus mod declarations"
        )
        return refs

    def _collect_sgui_refs(self, defined: Set[str]) -> List[Tuple[str, str, int]]:
        """Return undefined image= references from common/scripted_guis/*.txt."""
        self._log_section("Collecting GFX image= references from scripted_guis/*.txt")
        sgui_files = self._collect_files(["common/scripted_guis/*.txt"])
        all_refs: List[Tuple[str, str, int]] = []
        for batch in self._pool_map(
            _parse_sgui_file, [(f, self.mod_path) for f in sgui_files]
        ):
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
        for batch in self._pool_map(
            _parse_sloc_file, [(f, self.mod_path) for f in sloc_files]
        ):
            all_refs.extend(batch)
        self.log(
            f"  Scanned {len(sloc_files)} scripted_localisation files; found {len(all_refs)} GFX references"
        )
        return all_refs

    def _check_undefined_refs(
        self,
        refs: List[Tuple[str, str, int]],
        defined: Set[str],
        source_label: str,
        category: str,
        gui_mode: bool = False,
        mod_defined_ci: Optional[dict] = None,
    ) -> None:
        """Report any sprite names in refs that are not in defined.

        When gui_mode is True, .gui files that are vanilla overrides (not
        MD-authored) are reported as WARNINGs rather than ERRORs, because
        those files legitimately reference vanilla sprites the mod doesn't
        redefine. An MD-authored nation variant is likewise WARNING'd for a
        ref inherited from the specific vanilla file it copies — from the
        mod's own full-name override of that file, or (when a live vanilla
        install is present) from real vanilla .gui data. Every other
        MD-authored .gui ref and all scripted_gui/.txt refs get ERROR.

        *mod_defined_ci* is the casefold index of mod-only sprites (not
        vanilla). When a ref misses case-sensitively but hits here, the
        message is upgraded to a Linux case-mismatch diagnostic.
        """
        errors: List[Tuple[str, str, int]] = []
        warnings: List[Tuple[str, str, int]] = []
        seen: Set[Tuple[str, str, int]] = set()
        ci = mod_defined_ci or {}
        # .gui refs are gathered full-repo (ignore_staged) to build the override
        # index below, so under --staged the reported entries must be re-scoped to
        # the staged files or the whole repo's ~50 .gui errors would surface.
        staged_rel = (
            {os.path.relpath(f, self.mod_path) for f in (self.staged_files or [])}
            if self.staged_only
            else None
        )
        # Vanilla .gui files ship dead sprite refs of their own; an MD-authored
        # nation variant (`<vanilla_stem>_<tag>.gui`) inheriting the same ref is
        # vanilla's bug, not the mod's — downgrade to WARNING. Keyed per vanilla
        # file (basename -> its sprite refs) so a variant is only forgiven a ref
        # its own parent carries, not any dead ref that happens to share a name
        # somewhere else in the repo.
        override_refs_by_file: dict = {}
        vanilla_ref_index: dict = {}
        if gui_mode:
            for s, f, _ in refs:
                if not _is_md_gui_file(f):
                    override_refs_by_file.setdefault(os.path.basename(f), set()).add(s)
            # Real vanilla .gui refs (keyed by basename), so a variant added
            # without a full-name mod override is still forgiven refs its actual
            # vanilla parent carries. Empty without a live install (CI).
            vanilla_ref_index = _vanilla_gui_ref_index()

        for sprite, filepath, line in refs:
            if sprite in defined:
                continue
            if _is_flag_sprite(sprite):
                continue
            # Prefix heuristic only when no vanilla names were loaded — with a
            # live install or manifest the defined set already covers vanilla.
            if not self._vanilla_defs_loaded and _is_likely_vanilla(sprite):
                continue
            rel = os.path.relpath(filepath, self.mod_path)
            if staged_rel is not None and rel not in staged_rel:
                continue
            key = (sprite, rel, line)
            if key in seen:
                continue
            seen.add(key)
            canonical = case_mismatch(sprite, ci)
            if canonical:
                msg = (
                    f"Undefined sprite '{sprite}': case-mismatch reference '{sprite}'"
                    f" — defined as '{canonical}' (works on Windows, fails on Linux)"
                )
            else:
                msg = f"Undefined sprite '{sprite}'"
            entry = (msg, rel, line)
            downgrade = False
            if gui_mode:
                if not _is_md_gui_file(filepath):
                    downgrade = True
                else:
                    parent = _vanilla_parent_basename(filepath)
                    downgrade = parent is not None and (
                        sprite in override_refs_by_file.get(parent, ())
                        or sprite in vanilla_ref_index.get(parent, ())
                    )
            if downgrade:
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

    def _check_duplicate_definitions(self) -> None:
        """Report sprite names the mod defines more than once.

        Exact repeats are an engine coin-flip: whichever block loads last wins, so
        the two textures silently compete. Names differing only in case are separate
        sprites to the engine but the same file to a Windows author, which is how a
        `£ref` ends up pointing at whichever variant happens to be miscased.

        WARNING, not ERROR: the mod carries a ~477-entry backlog of exact repeats,
        and `--strict` gates on errors, so erroring here would fail every CI run
        until that backlog is cleared.
        """
        self._log_section("Checking for duplicate GFX sprite definitions")
        by_name: dict = {}
        for name, filepath, texture, line in self._mod_defs:
            by_name.setdefault(name, []).append(
                (os.path.relpath(filepath, self.mod_path), texture, line)
            )

        exact = []
        for name in sorted(by_name):
            sites = by_name[name]
            if len(sites) < 2:
                continue
            elsewhere = ", ".join(f"{f}:{ln}" for f, _tx, ln in sites[1:])
            same_art = len({tx for _f, tx, _ln in sites}) == 1
            verdict = (
                "same texture, so the extra blocks are redundant"
                if same_art
                else "different textures — the last block loaded wins"
            )
            exact.append(
                (
                    f"Duplicate GFX sprite '{name}' defined {len(sites)} times"
                    f" (also at {elsewhere}) — {verdict}",
                    sites[0][0],
                    sites[0][2],
                )
            )
        self._report(
            exact,
            ok_msg="No GFX sprite name is defined twice.",
            fail_msg=f"Duplicate GFX sprite definitions ({len(exact)} total):",
            severity=Severity.WARNING,
            category="duplicate-sprite",
        )

        by_lower: dict = {}
        for name in by_name:
            by_lower.setdefault(name.lower(), []).append(name)
        variants = []
        for lower in sorted(by_lower):
            names = sorted(by_lower[lower])
            if len(names) < 2:
                continue
            first = by_name[names[0]][0]
            # Same art under two spellings is one sprite split in half by a Windows
            # author; distinct art is two real sprites that merely collide in case.
            same_art = len({by_name[n][0][1] for n in names}) == 1
            verdict = (
                " on the same texture — collapse them onto one name"
                if same_art
                else " (distinct textures)"
            )
            variants.append(
                (
                    f"Case-variant GFX sprites {', '.join(repr(n) for n in names)}"
                    f" differ only in case{verdict}",
                    first[0],
                    first[2],
                )
            )
        if variants:
            self._report(
                variants,
                ok_msg="No case-variant GFX sprite definitions.",
                fail_msg="Case-variant GFX sprite definitions:",
                severity=Severity.WARNING,
                category="case-variant-sprite",
            )

    def _check_loc_ref_case(
        self,
        refs: List[Tuple[str, str, int]],
        defined: Set[str],
        defined_ci: dict,
    ) -> None:
        """Report `£sprite` localisation refs that only match a sprite case-insensitively.

        Nothing else validates localisation sprite refs — script `GFX_` tokens are
        covered by the focus/event/decision/idea validators' sprite index, and .gui
        refs by `_check_undefined_refs`. A miscased `£ref` renders no icon on Linux.

        English only: non-English loc is out of scope until the translation project
        (AGENTS.md), and a stray `£` before an accented word truncates at the accent
        (`£Réseau` -> `£R`), which then collides with short vanilla sprite names.

        One entry per distinct misspelling, not per occurrence — the same `£token` is
        copied verbatim into every file that carries the key.
        """
        self._log_section("Checking GFX £sprite reference case in localisation")
        staged_rel = (
            {os.path.relpath(f, self.mod_path) for f in (self.staged_files or [])}
            if self.staged_only
            else None
        )
        sites: dict = {}
        for sprite, filepath, line in refs:
            if sprite in defined or sprite in sites:
                continue
            rel = os.path.relpath(filepath, self.mod_path)
            if os.sep + "english" + os.sep not in rel:
                continue
            canonical = case_mismatch(sprite, defined_ci)
            if not canonical:
                continue
            if staged_rel is not None and rel not in staged_rel:
                continue
            sites[sprite] = (canonical, rel, line)

        issues = [
            (
                f"Sprite reference '£{sprite[len('GFX_') :]}' matches no sprite —"
                f" defined as '{canonical}' (works on Windows, fails on Linux)",
                rel,
                line,
            )
            for sprite, (canonical, rel, line) in sorted(sites.items())
        ]
        self._report(
            issues,
            ok_msg="All localisation £sprite references match a defined sprite's case.",
            fail_msg="Case-mismatched £sprite references in localisation:",
            severity=Severity.ERROR,
            category="sprite-ref-case",
        )

    def _check_unused_sprites(
        self,
        defined: Set[str],
        all_refs: Set[str],
    ) -> None:
        """Report GFX sprites that are defined but never referenced (warning only).

        Only reached when --report-unused is passed. Skipped entirely in staged
        mode to avoid noise — this check needs a full-repo scan to be
        meaningful, but in staged mode we only see a subset of files.

        A sprite whose only reference spells it with different case is reported
        separately: it is a live icon broken on Linux, not an orphan to archive.
        """
        self._log_section("Checking for unused GFX sprite definitions")
        if self.staged_only:
            self.log("  Skipping unused-sprite check in staged mode.")
            return

        equipment = _load_equipment_names(self.mod_path)
        if not equipment:
            self.log(
                "  No equipment archetypes found under common/units/equipment"
                " — equipment-icon exemption disabled"
            )
        technologies = _load_technology_names(self.mod_path)
        if not technologies:
            self.log(
                "  No technologies found under common/technologies"
                " — tech-icon exemption disabled"
            )
        implicit = equipment | technologies

        # A mod sprite carrying a vanilla name overrides vanilla's definition, so
        # vanilla's own UI and engine lookups still resolve it — the mod is under
        # no obligation to reference it. Removing it either blanks a vanilla icon
        # (same-path .gfx overrides replace the file outright) or silently reverts
        # MD art, so it is never an orphan to archive.
        if not self._vanilla_defined:
            self.log(
                "  No vanilla sprite names loaded — vanilla-override exemption disabled"
            )

        def _is_engine_resolved_icon(name: str) -> bool:
            if not name.startswith("GFX_"):
                return False
            sized = _EQUIPMENT_ICON_RE.match(name)
            stem = sized.group(1) if sized else name[len("GFX_") :]
            if sized and stem in implicit:
                return True
            # Without a size suffix only a tagged name is engine-resolved; an
            # untagged bare name is an ordinary sprite and stays reportable.
            tagged = _EQUIPMENT_ICON_TAG_RE.match(stem)
            return tagged is not None and tagged.group(1) in implicit

        unused = sorted(
            s
            for s in defined
            if s not in all_refs
            and s not in self._vanilla_defined
            and not _is_flag_sprite(s)
            and not _is_likely_vanilla(s)
            and not _is_engine_resolved_icon(s)
        )

        refs_ci = casefold_index(all_refs)
        orphans: List[str] = []
        miscased: List[Tuple[str, str]] = []
        for s in unused:
            referenced_as = case_mismatch(s, refs_ci)
            # A miscased reference that is itself a defined sprite resolves fine;
            # `s` is then a redundant case-variant alias, not a broken icon.
            if referenced_as and referenced_as not in defined:
                miscased.append((s, referenced_as))
            else:
                orphans.append(s)

        if miscased:
            self._report(
                [
                    (
                        f"Unused GFX sprite '{s}': referenced only as"
                        f" '{ref}' (works on Windows, fails on Linux)",
                        "",
                        0,
                    )
                    for s, ref in miscased
                ],
                ok_msg="No case-mismatched GFX sprite definitions.",
                fail_msg=(
                    f"Case-mismatched GFX sprite definitions ({len(miscased)} total)"
                    " — live icons, fix the case rather than archiving them:"
                ),
                severity=Severity.WARNING,
                category="unused-sprite-case",
            )

        if _hide_unused_backlog():
            self.log(
                f"  Suppressing {len(orphans)} unused-sprite warnings"
                f" ({_HIDE_UNUSED_ENV} is set); case and duplicate findings still report."
            )
            return

        if not orphans:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}  All defined GFX sprites are referenced.{Colors.ENDC if self.use_colors else ''}"
            )
            return

        issues = [
            (f"Unused GFX sprite '{s}' (defined but never referenced)", "", 0)
            for s in orphans
        ]

        self._report(
            issues,
            ok_msg="All defined GFX sprites are referenced.",
            fail_msg=f"Unused GFX sprite definitions ({len(orphans)} total):",
            severity=Severity.WARNING,
            category="unused-sprite",
        )

    def run_validations(self) -> None:
        defined, mod_defined = self._build_gfx_definitions()
        # Case-insensitive index of mod-only sprites — never suggest a
        # vanilla-only sprite as the canonical name for a case-mismatch.
        mod_defined_ci = casefold_index(mod_defined)

        self._check_duplicate_definitions()

        gui_refs = self._collect_gui_refs(defined)
        sgui_refs = self._collect_sgui_refs(defined)
        sloc_refs = self._collect_sloc_refs(defined)

        self._log_section("Checking undefined GFX sprite references in .gui files")
        self._check_undefined_refs(
            gui_refs,
            defined,
            source_label=".gui files",
            category="undefined-sprite",
            gui_mode=True,
            mod_defined_ci=mod_defined_ci,
        )

        self._log_section("Checking undefined GFX sprite references in scripted_guis")
        self._check_undefined_refs(
            sgui_refs,
            defined,
            source_label="scripted_guis",
            category="undefined-sprite",
            mod_defined_ci=mod_defined_ci,
        )

        self._log_section(
            "Checking undefined GFX sprite references in scripted_localisation"
        )
        self._check_undefined_refs(
            sloc_refs,
            defined,
            source_label="scripted_localisation",
            category="undefined-sprite",
            mod_defined_ci=mod_defined_ci,
        )

        # Localisation £refs are checked for case whether or not --report-unused is
        # passed: a miscased ref is a broken icon, not backlog. The full defined set
        # (mod + vanilla) is the index — £refs legitimately name vanilla sprites.
        loc_refs = self._collect_loc_refs()
        self._check_loc_ref_case(loc_refs, defined, casefold_index(defined))

        if not self.report_unused:
            self._log_section(
                "Skipping unused-sprite check (pass --report-unused to enable)"
            )
            return

        # Unused-sprite check is mod-only; vanilla sprites the mod doesn't redefine aren't ours to flag.
        # A sprite is "used" if referenced anywhere — interface/ or game script.
        all_referenced: Set[str] = {r[0] for r in gui_refs + sgui_refs + sloc_refs}
        if not self.staged_only:
            all_referenced |= self._collect_script_refs()
            all_referenced |= {r[0] for r in loc_refs}
            all_referenced |= self._resolve_engine_refs(mod_defined)
        self._check_unused_sprites(mod_defined, all_referenced)


def _add_extra_args(parser):
    parser.add_argument(
        "--report-unused",
        action="store_true",
        dest="report_unused",
        help="Report GFX sprites that are defined but never referenced",
    )


def main() -> int:
    return run_validator_main(
        Validator,
        description="Validate GFX sprite references in Millennium Dawn mod.",
        extra_args_fn=_add_extra_args,
    )


if __name__ == "__main__":
    sys.exit(main())
