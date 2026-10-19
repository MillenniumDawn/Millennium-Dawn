"""Tests for validate_gfx_references.py."""

import argparse
import os
import sys

import pytest
import validate_gfx_references as vg
from shared.suite import run_validator, write_under
from shared_utils import extract_block_from_text
from validate_gfx_references import Validator as GfxReferenceValidator
from validator_common import Severity

# Captured before the autouse stubs replace them, so the discovery tests can
# still exercise the real glob logic against a fake install.
_REAL_VANILLA_GFX_FILES = vg._vanilla_gfx_files
_REAL_VANILLA_GUI_FILES = vg._vanilla_gui_files
_REAL_VANILLA_GUI_REF_INDEX = vg._vanilla_gui_ref_index
_REAL_SPRITE_MANIFEST = vg._load_vanilla_sprite_manifest
_REAL_FONT_MANIFEST = vg._load_vanilla_font_manifest


@pytest.fixture(autouse=True)
def _no_vanilla_install(no_vanilla_gfx, monkeypatch):
    monkeypatch.setattr(vg, "_vanilla_gui_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_font_manifest", lambda: frozenset())


def _write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return str(path)


def _directory(path):
    """A directory whose name matches a scanned glob; reads as unreadable."""
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _broken_symlink(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(str(path.parent / "no_such_target"), str(path))
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")
    return str(path)


def _validator(tmp_path, **kwargs):
    return GfxReferenceValidator(str(tmp_path), use_colors=False, **kwargs)


def _categories(validator, category):
    return [i for i in validator._issues if i.category == category]


def _sprite(name, texture):
    return (
        f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{texture}"\n\t}}\n'
    )


def _write_gfx(tmp_path, filename, *blocks):
    return _write(
        tmp_path / "interface" / filename, "spriteTypes = {\n" + "".join(blocks) + "}\n"
    )


def _iface(tmp_path, basename):
    return os.path.join(str(tmp_path), "interface", basename)


# --- vanilla discovery ------------------------------------------------------


def _fake_install(tmp_path):
    root = tmp_path / "hoi4"
    _write(root / "interface" / "core.gfx", "spriteTypes = {\n}\n")
    _write(root / "interface" / "core.gui", "guiTypes = {\n}\n")
    _write(root / "dlc" / "dlc01" / "interface" / "toa.gfx", "spriteTypes = {\n}\n")
    _write(root / "dlc" / "dlc01" / "interface" / "toa.gui", "guiTypes = {\n}\n")
    _write(
        root / "integrated_dlc" / "gd" / "interface" / "gd.gfx", "spriteTypes = {\n}\n"
    )
    _write(root / "integrated_dlc" / "gd" / "interface" / "gd.gui", "guiTypes = {\n}\n")
    return str(root)


def test_vanilla_gfx_and_gui_scans_include_dlc_interfaces(tmp_path, monkeypatch):
    install = _fake_install(tmp_path)
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: install)

    gfx = [os.path.basename(f) for f in _REAL_VANILLA_GFX_FILES()]
    gui = [os.path.basename(f) for f in _REAL_VANILLA_GUI_FILES()]

    assert sorted(gfx) == ["core.gfx", "gd.gfx", "toa.gfx"]
    assert sorted(gui) == ["core.gui", "gd.gui", "toa.gui"]


def test_vanilla_interface_dir_is_found_inside_an_install(tmp_path, monkeypatch):
    install = _fake_install(tmp_path)
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: install)
    assert vg._find_vanilla_interface_dir() == os.path.join(install, "interface")


def test_vanilla_scans_are_empty_without_an_install(monkeypatch):
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: None)
    assert _REAL_VANILLA_GFX_FILES() == []
    assert _REAL_VANILLA_GUI_FILES() == []
    assert vg._find_vanilla_interface_dir() is None


def test_install_without_an_interface_dir_has_no_vanilla_interface(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: str(tmp_path))
    assert vg._find_vanilla_interface_dir() is None


@pytest.mark.parametrize(
    "loader, filename, attribute",
    [
        (_REAL_SPRITE_MANIFEST, "vanilla_sprites.txt", "_VANILLA_SPRITES_MANIFEST"),
        (_REAL_FONT_MANIFEST, "vanilla_fonts.txt", "_VANILLA_FONTS_MANIFEST"),
    ],
    ids=["sprites", "fonts"],
)
def test_committed_manifests_skip_comments_and_blank_lines(
    tmp_path, monkeypatch, loader, filename, attribute
):
    manifest = tmp_path / filename
    manifest.write_text("# generated\n\nENTRY_ONE\nENTRY_TWO\n", encoding="utf-8")
    monkeypatch.setattr(vg, attribute, str(manifest))
    assert loader() == frozenset({"ENTRY_ONE", "ENTRY_TWO"})


@pytest.mark.parametrize(
    "loader, attribute",
    [
        (_REAL_SPRITE_MANIFEST, "_VANILLA_SPRITES_MANIFEST"),
        (_REAL_FONT_MANIFEST, "_VANILLA_FONTS_MANIFEST"),
        (vg._load_vanilla_gui_basenames, "_VANILLA_GUI_MANIFEST"),
    ],
    ids=["sprites", "fonts", "gui files"],
)
def test_corrupt_manifest_reads_as_empty(tmp_path, monkeypatch, loader, attribute):
    manifest = tmp_path / "manifest.txt"
    manifest.write_bytes(b"ENTRY_ONE\n\xff\xfe not utf-8 \x80\n")
    monkeypatch.setattr(vg, attribute, str(manifest))
    assert loader() == frozenset()


def test_vanilla_gui_ref_index_keys_refs_by_basename(tmp_path, monkeypatch):
    unreadable = _directory(tmp_path / "broken.gui")
    real = _write(
        tmp_path / "topbar.gui",
        'guiTypes = {\n\tspriteType = "GFX_topbar_pp"\n'
        '\tbackground = "GFX_stray]token"\n}\n',
    )
    monkeypatch.setattr(vg, "_vanilla_gui_files", lambda: [unreadable, real])

    index = _REAL_VANILLA_GUI_REF_INDEX()

    assert index["topbar.gui"] == {"GFX_topbar_pp"}
    assert "broken.gui" not in index


# --- declaration harvesting -------------------------------------------------


def test_empty_declaration_blocks_declare_no_names():
    assert vg._entry_names_from_text("equipments = {}\n", vg._EQUIPMENTS_BLOCK_RE) == []
    assert vg._unit_category_names_from_text("sub_unit_categories = {}\n") == []


def test_txt_walk_ignores_other_extensions(tmp_path):
    _write(tmp_path / "a.txt", "")
    _write(tmp_path / "nested" / "b.txt", "")
    _write(tmp_path / "nested" / "c.gfx", "")
    assert sorted(os.path.basename(f) for f in vg._iter_txt_files(str(tmp_path))) == [
        "a.txt",
        "b.txt",
    ]


def test_missing_directory_yields_no_files(tmp_path):
    assert vg._iter_txt_files(str(tmp_path / "absent"), recursive=False) == []
    assert vg._iter_txt_files(str(tmp_path / "absent")) == []


# case: (directory, unreadable entry, readable file content, loader, names)
_UNREADABLE_DECLARATION_CASES = {
    "focus search filters": (
        "common/national_focus",
        _broken_symlink,
        "focus = {\n\tsearch_filters = { FOCUS_FILTER_UKR }\n}\n",
        vg._load_search_filter_names,
        frozenset({"FOCUS_FILTER_UKR"}),
    ),
    "equipment archetypes": (
        "common/units/equipment",
        _broken_symlink,
        "equipments = {\n\tutil_vehicle_1 = {\n\t}\n}\n",
        lambda mod: vg._load_equipment_tree(mod)[0],
        frozenset({"util_vehicle_1"}),
    ),
    "country tags": (
        "common/country_tags",
        _directory,
        'CHI = "countries/China.txt"\n',
        vg._load_ace_pool_names,
        frozenset({"CHI"}),
    ),
}


@pytest.mark.parametrize(
    "rel, unreadable, content, loader, names",
    _UNREADABLE_DECLARATION_CASES.values(),
    ids=_UNREADABLE_DECLARATION_CASES,
)
def test_unreadable_declaration_file_is_skipped(
    tmp_path, rel, unreadable, content, loader, names
):
    unreadable(tmp_path / rel / "broken.txt")
    _write(tmp_path / rel / "00_real.txt", content)
    assert loader(str(tmp_path)) == names


EQUIPMENT_FIXTURE = (
    "equipments = {\n"
    "\tutil_vehicle_1 = {\n"
    "\t\tyear = 1936\n"
    "\t\tmodule_slots = {\n"
    "\t\t\tvalues = { module_a module_b }\n"
    "\t\t}\n"
    "\t}\n"
    "\tinfantry_equipment_0 = {\n"
    "\t\tyear = 1936\n"
    "\t}\n"
    "\tAPC_1 = {\n"
    "\t\tyear = 1936\n"
    "\t}\n"
    "}\n"
)

TECHNOLOGY_FIXTURE = (
    "technologies = {\n"
    "\t@1945 = -4\n"
    "\tMBT_1 = {\n"
    "\t\tenable_equipments = {\n"
    "\t\t\tmedium_tank_chassis\n"
    "\t\t}\n"
    "\t}\n"
    "\tSAM0 = {\n"
    "\t\tyear = 1945\n"
    "\t}\n"
    "}\n"
)

_EQUIPMENT_FILE = "common/units/equipment/test_equipment.txt"
_TECH_FILE = "common/technologies/test_tech.txt"


def test_equipments_block_and_entry_regex_parse_one_tab_entries():
    block = vg._EQUIPMENTS_BLOCK_RE.search(EQUIPMENT_FIXTURE)
    assert block is not None
    body, end = extract_block_from_text(EQUIPMENT_FIXTURE, block.start())
    assert end != -1
    entries = set(vg._EQUIPMENT_ENTRY_RE.findall(body))
    # nested `values` two tabs deep must not be picked up as an entry
    assert entries == {"util_vehicle_1", "infantry_equipment_0", "APC_1"}


@pytest.mark.parametrize(
    "rel, content, loader, names",
    [
        (
            _EQUIPMENT_FILE,
            EQUIPMENT_FIXTURE,
            vg._load_equipment_names,
            {"util_vehicle_1", "infantry_equipment_0", "APC_1"},
        ),
        (None, None, vg._load_equipment_names, set()),
        (_TECH_FILE, TECHNOLOGY_FIXTURE, vg._load_technology_names, {"MBT_1", "SAM0"}),
        (None, None, vg._load_technology_names, set()),
    ],
    ids=["equipment", "no equipment dir", "technologies", "no technologies dir"],
)
def test_declaration_loaders_read_top_level_entries(
    tmp_path, rel, content, loader, names
):
    if rel:
        _write(tmp_path / rel, content)
    assert loader(str(tmp_path)) == frozenset(names)


def test_load_technology_names_refresh_after_edit(tmp_path, monkeypatch):
    # Names are content-cached per file; an edited file must not serve stale ids.
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write(tmp_path / _TECH_FILE, TECHNOLOGY_FIXTURE)
    assert vg._load_technology_names(str(tmp_path)) == frozenset({"MBT_1", "SAM0"})
    _write(
        tmp_path / _TECH_FILE,
        "technologies = {\n\tMBT_2 = {\n\t\tyear = 1950\n\t}\n}\n",
    )
    assert vg._load_technology_names(str(tmp_path)) == frozenset({"MBT_2"})


def test_search_filter_names_are_read_from_focus_trees(tmp_path):
    _write(
        tmp_path / "common" / "national_focus" / "test.txt",
        "focus = {\n\tsearch_filters = { FOCUS_FILTER_POLITICAL FOCUS_FILTER_UKR_STABILITY }\n}\n",
    )
    assert vg._load_search_filter_names(str(tmp_path)) == frozenset(
        {"FOCUS_FILTER_POLITICAL", "FOCUS_FILTER_UKR_STABILITY"}
    )


_MODULES_FILE = "common/units/equipment/modules/test.txt"
_UNITS_FILE = "common/units/test.txt"
_UNIT_TAGS_FILE = "common/unit_tags/00_categories.txt"
_AA_COMPANY = "sub_units = {\n\tAA_company = {\n\t\tsprite = infantry\n\t}\n}\n"


def test_module_names_cover_modules_and_their_categories(tmp_path):
    _write(
        tmp_path / _MODULES_FILE,
        "equipment_modules = {\n\ttank_diesel_engine_gen1 = {\n"
        "\t\tcategory = tank_engine_type\n\t}\n}\n",
    )
    assert vg._load_module_icon_names(str(tmp_path)) == frozenset(
        {"tank_diesel_engine_gen1", "tank_engine_type"}
    )


def test_chassis_slot_categories_are_read_too(tmp_path):
    # A category is never declared on its own. Harvesting only `category =` misses
    # one a chassis slot allows but no surviving module claims, and deleting its
    # icon blanks the slot in the designer.
    _write(
        tmp_path / "common" / "units" / "equipment" / "chassis.txt",
        "equipments = {\n\ttank_chassis = {\n\t\tmodule_slots = {\n"
        "\t\t\tengine_type_slot = {\n\t\t\t\tallowed_module_categories = {\n"
        "\t\t\t\t\tafv_gasoline_engine_type\n\t\t\t\t\ttank_diesel_engine_type\n"
        "\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n",
    )
    names = vg._load_module_icon_names(str(tmp_path))
    assert {"afv_gasoline_engine_type", "tank_diesel_engine_type"} <= names


def test_unit_icon_names_cover_subunits_and_categories(tmp_path):
    _write(tmp_path / _UNITS_FILE, _AA_COMPANY)
    _write(
        tmp_path / _UNIT_TAGS_FILE, "sub_unit_categories = {\n\tcategory_fighter\n}\n"
    )
    assert vg._load_unit_icon_names(str(tmp_path)) == frozenset(
        {"AA_company", "category_fighter"}
    )


def test_unit_icon_names_ignore_equipment_and_namelist_dirs(tmp_path):
    _write(tmp_path / _UNITS_FILE, _AA_COMPANY)
    for rel, name in (
        ("equipment/fake.txt", "fake_from_equipment"),
        ("names/00_names.txt", "fake_from_names"),
    ):
        _write(
            tmp_path / "common" / "units" / rel,
            f"sub_units = {{\n\t{name} = {{\n\t\tsprite = infantry\n\t}}\n}}\n",
        )
    assert vg._load_unit_icon_names(str(tmp_path)) == frozenset({"AA_company"})


def test_equipment_tree_serves_archetypes_and_modules(tmp_path):
    _write(
        tmp_path / "common" / "units" / "equipment" / "both.txt",
        "equipments = {\n\tutil_vehicle_1 = {\n\t\tyear = 1936\n\t}\n}\n"
        "equipment_modules = {\n\tCZE_engine_1 = {\n\t\tyear = 2000\n\t}\n}\n",
    )
    archetypes, modules = vg._load_equipment_tree(str(tmp_path))
    assert archetypes == frozenset({"util_vehicle_1"})
    assert modules == frozenset({"CZE_engine_1"})
    assert vg._load_equipment_names(str(tmp_path)) == archetypes
    assert vg._load_module_icon_names(str(tmp_path)) == modules


def test_declaration_engine_refs_reuse_the_aggregate_cache(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write(tmp_path / _UNITS_FILE, _AA_COMPANY)
    first, _notices = vg._declaration_engine_refs(str(tmp_path))
    assert "GFX_unit_AA_company_icon_medium" in first

    def _boom(_mod_path):
        raise AssertionError("declaration cache missed")

    monkeypatch.setattr(
        vg,
        "_ENGINE_DECLARATION_FAMILIES",
        ((_boom, "", ("GFX_unit_{name}_icon_medium",)),),
    )
    second, _notices = vg._declaration_engine_refs(str(tmp_path))
    assert second == first


# --- engine-resolved references ---------------------------------------------
#
# These are resolved into the reference set, not filtered out of the report, so
# a sprite whose backing declaration is gone still reports as unused and one
# spelled with the wrong case still reports as miscased.

_FOCUS_FILE = "common/national_focus/test.txt"
_TOKENS_FILE = "common/synchronized_dynamic_tokens/MD_tokens.txt"
_CZE_ENGINE = "equipment_modules = {\n\tCZE_engine_1 = {\n\t\tyear = 2000\n\t}\n}\n"
_UNIT_SUFFIXES = (
    "medium",
    "small",
    "medium_white",
    "small_white",
    "medium_black",
)

# case: (files, candidate sprites, resolved, unresolved)
_ENGINE_REF_CASES = {
    "focus filter icon in use": (
        {
            _FOCUS_FILE: "focus = {\n\tsearch_filters = { FOCUS_FILTER_UKR_STABILITY }\n}\n"
        },
        set(),
        {"GFX_FOCUS_FILTER_UKR_STABILITY"},
        set(),
    ),
    "focus filter icon no focus uses": (
        {_FOCUS_FILE: "focus = {\n\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n}\n"},
        {"GFX_FOCUS_FILTER_RETIRED"},
        set(),
        {"GFX_FOCUS_FILTER_RETIRED"},
    ),
    "commented-out search filter": (
        {_FOCUS_FILE: "focus = {\n#\tsearch_filters = { FOCUS_FILTER_DEAD }\n}\n"},
        {"GFX_FOCUS_FILTER_DEAD"},
        set(),
        {"GFX_FOCUS_FILTER_DEAD"},
    ),
    "module category icon": (
        {
            _MODULES_FILE: "equipment_modules = {\n\tafv_petrol_1 = {\n"
            "\t\tcategory = afv_gasoline_engine_type\n\t}\n}\n"
        },
        set(),
        {"GFX_EMI_afv_gasoline_engine_type", "GFX_SMI_afv_gasoline_engine_type"},
        set(),
    ),
    "module icon": (
        {_MODULES_FILE: _CZE_ENGINE},
        set(),
        {"GFX_EMI_CZE_engine_1", "GFX_SMI_CZE_engine_1"},
        set(),
    ),
    # Real MD art for an AFV module set that no longer exists.
    "icon of a deleted module": (
        {_MODULES_FILE: _CZE_ENGINE},
        {"GFX_EMI_afv_battlestation_1", "GFX_SMI_afv_battlestation_1"},
        set(),
        {"GFX_EMI_afv_battlestation_1", "GFX_SMI_afv_battlestation_1"},
    ),
    "unit icons for a real subunit": (
        {
            _UNITS_FILE: "sub_units = {\n\tALN_bellatoris = {\n"
            "\t\tsprite = CHIMERA_bellatoris\n\t}\n}\n"
        },
        set(),
        {f"GFX_unit_ALN_bellatoris_icon_{suffix}" for suffix in _UNIT_SUFFIXES},
        set(),
    ),
    "unit category icon": (
        {_UNIT_TAGS_FILE: "sub_unit_categories = {\n\tcategory_all_airborne\n}\n"},
        set(),
        {"GFX_unit_category_all_airborne_icon_small"},
        set(),
    ),
    "icon of a deleted unit": (
        {_UNITS_FILE: _AA_COMPANY},
        {"GFX_unit_AFG_donkey_logistics_icon_medium"},
        set(),
        {"GFX_unit_AFG_donkey_logistics_icon_medium"},
    ),
    # The engine's own last-resort ace pool has no key to check; an ace for a
    # tag the mod does not declare is dead art.
    "ace portraits": (
        {
            "common/country_tags/00_countries.txt": 'CHI = "countries/China.txt"\n',
            "common/countries/Test.txt": (
                "graphical_culture = asian_gfx\ngraphical_culture_2d = asian_2d\n"
            ),
        },
        {"GFX_CHI_ace_m_0", "GFX_asian_2d_ace_f_1", "GFX_ace_m_2", "GFX_XYZ_ace_m_0"},
        {"GFX_CHI_ace_m_0", "GFX_asian_2d_ace_f_1", "GFX_ace_m_2"},
        {"GFX_XYZ_ace_m_0"},
    ),
    # Same GFX_missile_ prefix, but the template's _ID_/_icon literals don't fit.
    "scripted loc template": (
        {
            "common/scripted_localisation/test.txt": "defined_text = {\n"
            "\tname = missile_icon\n\ttext = {\n"
            '\t\tlocalization_key = "GFX_missile_[THIS.GetTag]_ID_[?var_x]_icon"\n'
            "\t}\n}\n"
        },
        {"GFX_missile_CHI_ID_101_icon", "GFX_missile_submarine_offensive_medium"},
        {"GFX_missile_CHI_ID_101_icon"},
        {"GFX_missile_submarine_offensive_medium"},
    ),
    "token template": (
        {
            "common/scripted_guis/topbar.txt": 'image = "GFX_[?topbar.GetTokenKey]"\n',
            _TOKENS_FILE: "topbar_oil_total\n",
        },
        {"GFX_topbar_oil_total", "GFX_topbar_oil"},
        {"GFX_topbar_oil_total"},
        {"GFX_topbar_oil"},
    ),
    "tokens without a token template": (
        {_TOKENS_FILE: "topbar_oil_total\n"},
        {"GFX_topbar_oil_total"},
        set(),
        {"GFX_topbar_oil_total"},
    ),
}


@pytest.mark.parametrize(
    "files, candidates, resolved, unresolved",
    _ENGINE_REF_CASES.values(),
    ids=_ENGINE_REF_CASES,
)
def test_resolve_engine_refs(tmp_path, files, candidates, resolved, unresolved):
    for rel, body in files.items():
        _write(tmp_path / rel, body)

    found = _validator(tmp_path)._resolve_engine_refs(candidates)

    assert resolved <= found
    assert not unresolved & found


def test_only_a_placeholder_template_resolves_nothing(tmp_path):
    # GFX_[?topbar.GetTokenKey] would otherwise resolve every sprite in the mod.
    assert vg._template_pattern("GFX_[?topbar.GetTokenKey]") is None
    assert vg._template_pattern("GFX_missile_[THIS.GetTag]_ID_[?v]_icon") is not None
    _write(
        tmp_path / "common" / "scripted_localisation" / "test.txt",
        "defined_text = {\n\tname = alert\n\ttext = {\n"
        '\t\tlocalization_key = "GFX_[?md_alerts^alert_idx.GetTokenKey]"\n'
        "\t}\n}\n",
    )
    assert _validator(tmp_path)._resolve_engine_refs({"GFX_anything_at_all"}) == set()


@pytest.mark.parametrize(
    "check, notices",
    [
        (
            lambda validator: validator._resolve_engine_refs(set()),
            ("search_filters", "equipment modules", "unit icons", "graphical cultures"),
        ),
        (
            lambda validator: validator._check_unused_sprites(
                defined=set(), all_refs=set()
            ),
            ("equipment", "technologies"),
        ),
    ],
    ids=["engine refs", "unused sprites"],
)
def test_missing_data_dirs_are_logged(tmp_path, gfx_notices, check, notices):
    logged = gfx_notices(tmp_path, check)
    for expected in notices:
        assert any(expected in msg for msg in logged)


# --- per-file parsers -------------------------------------------------------


@pytest.mark.parametrize(
    "parser",
    [
        vg._parse_gfx_file,
        vg._parse_gui_file,
        vg._parse_gui_fonts,
        vg._parse_gfx_fonts,
        vg._parse_sgui_file,
        vg._parse_script_refs,
        vg._parse_loc_refs,
        vg._parse_sprite_templates,
        vg._parse_sloc_file,
        vg._parse_raw_variant_icons,
        vg._parse_raw_graphic_db_icons,
    ],
)
def test_every_parser_tolerates_an_unreadable_file(tmp_path, parser):
    unreadable = _directory(tmp_path / "unreadable")
    assert parser((unreadable, str(tmp_path))) == []


@pytest.mark.parametrize(
    "raw, defs",
    [
        (
            'spriteType = { name = "GFX_unbalanced" texturefile = "gfx/a.dds"\n',
            [("GFX_unbalanced", "gfx/a.dds", 1)],
        ),
        (
            'spriteType = { name = "GFX_a" texturefile = gfx/a.dds }\n',
            [("GFX_a", "gfx/a.dds", 1)],
        ),
        (
            'spriteType = {\n\ttexturefile = "gfx/a.dds"\n}\n'
            'spriteType = {\n\tname = "GFX_real"\n}\n',
            [("GFX_real", "", 4)],
        ),
    ],
    ids=["unbalanced block", "unquoted texturefile", "nameless block"],
)
def test_sprite_defs_from_gfx_text(raw, defs):
    assert vg.sprite_defs_from_gfx_text(raw) == defs
    assert vg.sprite_names_from_gfx_text(raw) == {name for name, _t, _l in defs}


def test_gfx_parse_carries_the_texturefile(tmp_path):
    path = _write_gfx(tmp_path, "test.gfx", _sprite("GFX_a", "gfx/a.dds"))
    assert vg._parse_gfx_file((path, str(tmp_path))) == [
        ("GFX_a", path, "gfx/a.dds", 2)
    ]


_CORE_FONTS = (
    "bitmapfonts = {\n"
    "\tbitmapfont = {\n"
    '\t\tname = "hoi_16mbs"\n'
    '\t\tfontfiles = { "gfx/fonts/hoi_16mbs.fnt" }\n'
    "\t}\n"
    "\tbitmapfont = {\n"
    '\t\tname = "hoi_18b"\n'
    "\t}\n"
    "}\n"
)


@pytest.mark.parametrize(
    "raw, names",
    [
        (_CORE_FONTS, {"hoi_16mbs", "hoi_18b"}),
        ('bitmapfonts = {\n#\tbitmapfont = {\n#\t\tname = "ub_16bs"\n#\t}\n}\n', set()),
        ('bitmapfont = {\n\tfontfiles = { "gfx/fonts/x.fnt" }\n}\n', set()),
        # A .gfx missing its closing brace must not turn every font into a
        # false undefined-font error.
        ('bitmapfont = {\n\tname = "hoi_16"\n', {"hoi_16"}),
    ],
    ids=["named fonts", "commented font", "nameless font", "unbalanced font"],
)
def test_font_names_from_gfx_text(raw, names):
    assert vg.font_names_from_gfx_text(raw) == names


# case: (.gui text, collected (sprite name, line))
_GUI_REF_CASES = {
    "lowercase quadtexturesprite and spritetype": (
        'quadtexturesprite = "GFX_Bundeswehr_bar"\n'
        'spritetype = "GFX_PER_propaganda_progress_frame"\n',
        [("GFX_Bundeswehr_bar", 1), ("GFX_PER_propaganda_progress_frame", 2)],
    ),
    "PascalCase SpriteType": (
        'SpriteType = "GFX_resources_bg"\n',
        [("GFX_resources_bg", 1)],
    ),
    "unquoted names": (
        "spriteType = GFX_button_94x31\n"
        "quadTextureSprite = GFX_faction_theater_background\n",
        [("GFX_button_94x31", 1), ("GFX_faction_theater_background", 2)],
    ),
    "camelCase quoted names": (
        'spriteType = "GFX_closebutton"\n'
        'quadTextureSprite = "GFX_button_123x34"\n'
        'background = "GFX_tiled_plain_bg"\n',
        [("GFX_closebutton", 1), ("GFX_button_123x34", 2), ("GFX_tiled_plain_bg", 3)],
    ),
    "lowercase gfx_ prefix": ('quadTextureSprite = "gfx_transparency_white"\n', []),
    "dynamic quoted name": ('spriteType = "GFX_missile_[THIS.GetTag]_icon"\n', []),
    # A bracket anywhere in the name means the engine assembles it at runtime.
    "runtime-built name": (
        'guiTypes = {\n\tspriteType = "GFX_static"\n'
        '\tbackground = "GFX_stray]token"\n}\n',
        [("GFX_static", 2)],
    ),
    # Lines count in the comment-stripped text, which keeps every newline.
    "comments above the ref": (
        "# View for the topbar widget.\n# Adapted from Black Ice.\n"
        'spriteType = "GFX_NV_btn_add"\n',
        [("GFX_NV_btn_add", 3)],
    ),
}


@pytest.mark.parametrize("text, refs", _GUI_REF_CASES.values(), ids=_GUI_REF_CASES)
def test_parse_gui_file(tmp_path, text, refs):
    path = _write(tmp_path / "interface" / "view.gui", text)
    assert [
        (name, line) for name, _f, line in vg._parse_gui_file((path, str(tmp_path)))
    ] == refs


def test_scripted_gui_and_scripted_loc_refs_carry_their_line(tmp_path):
    sgui = _write(
        tmp_path / "common" / "scripted_guis" / "panel.txt",
        '# comment\nimage = "GFX_panel_icon"\nimage = "GFX_[?v]_dynamic"\n'
        'image = "GFX_stray]token"\n',
    )
    sloc = _write(
        tmp_path / "common" / "scripted_localisation" / "text.txt",
        'defined_text = {\n\tlocalization_key = "GFX_sloc_icon"\n'
        "#\tlocalization_key = GFX_commented_out\n"
        "\tlocalization_key = GFX_bare_icon # trailing note\n}\n",
    )

    assert vg._parse_sgui_file((sgui, str(tmp_path))) == [("GFX_panel_icon", sgui, 2)]
    assert vg._parse_sloc_file((sloc, str(tmp_path))) == [
        ("GFX_sloc_icon", sloc, 2),
        ("GFX_bare_icon", sloc, 4),
    ]


@pytest.mark.parametrize(
    "rel, text, refs",
    [
        (
            "common/ideas/00_ideas.txt",
            "ideas = {\n\ttest_idea = {\n\t\tpicture = generic_bank\n\t}\n}\n",
            ["GFX_idea_generic_bank"],
        ),
        (
            "common/decisions/test.txt",
            "picture = generic_bank\nicon = GFX_decision_icon\n",
            ["GFX_decision_icon"],
        ),
        (
            "common/decisions/test.txt",
            "icon = arabic\nicon = {\n\tkey = sinaloa_high\n}\n",
            [
                "GFX_decision_arabic",
                "GFX_decision_category_arabic",
                "GFX_decision_category_sinaloa_high",
                "GFX_decision_sinaloa_high",
            ],
        ),
    ],
    ids=["idea picture", "picture outside ideas", "bare decision icon"],
)
def test_parse_script_refs(tmp_path, rel, text, refs):
    path = _write(tmp_path / rel, text)
    assert vg._parse_script_refs((path, str(tmp_path))) == refs


@pytest.mark.parametrize(
    "text, refs",
    [
        (
            'l_english:\n A:0 "£command_power. and £."\n B:0 "£command_power again"\n',
            [("GFX_command_power", 2)],
        ),
        ('l_english:\n A:0 "£GFX_money_icon"\n', [("GFX_money_icon", 2)]),
        (
            'l_english:\n A:0 "£trigger_no£Not £mission_icons|1£Intel"\n',
            [("GFX_trigger_no", 2), ("GFX_mission_icons", 2)],
        ),
    ],
    ids=["punctuation and repeats", "prefix already present", "closing pound sign"],
)
def test_parse_loc_refs(tmp_path, text, refs):
    path = _write(tmp_path / "localisation" / "english" / "a_l_english.yml", text)
    assert vg._parse_loc_refs((path, str(tmp_path))) == [
        (name, path, line) for name, line in refs
    ]


def test_sprite_templates_are_collected_from_scripted_files(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_localisation" / "t.txt",
        'localization_key = "GFX_missile_[THIS.GetTag]_icon"\n'
        'localization_key = "GFX_plain_icon"\n',
    )
    assert vg._parse_sprite_templates((path, str(tmp_path))) == [
        "GFX_missile_[THIS.GetTag]_icon"
    ]


# --- definition set assembly ------------------------------------------------


def test_vanilla_manifest_is_folded_in_when_no_install_is_present(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        vg, "_load_vanilla_sprite_manifest", lambda: frozenset({"GFX_vanilla_only"})
    )
    _write(tmp_path / "interface" / "a.gfx", 'spriteType = { name = "GFX_mod" }\n')

    validator = _validator(tmp_path)
    defined, mod_defined = validator._build_gfx_definitions()

    assert defined == {"GFX_mod", "GFX_vanilla_only"}
    assert mod_defined == {"GFX_mod"}
    assert validator._vanilla_defs_loaded is True


def test_live_vanilla_gfx_files_take_priority_over_the_manifest(tmp_path, monkeypatch):
    vanilla = _write(
        tmp_path / "vanilla" / "interface" / "core.gfx",
        'spriteType = { name = "GFX_from_install" }\n',
    )
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [vanilla])
    monkeypatch.setattr(
        vg,
        "_load_vanilla_sprite_manifest",
        lambda: pytest.fail("manifest read with a live install"),
    )
    _write(tmp_path / "interface" / "a.gfx", 'spriteType = { name = "GFX_mod" }\n')

    validator = _validator(tmp_path)
    defined, _mod_defined = validator._build_gfx_definitions()

    assert defined == {"GFX_mod", "GFX_from_install"}
    assert validator._vanilla_defined == {"GFX_from_install"}


# --- undefined sprites ------------------------------------------------------

# Real vanilla designer GUIs (present in vanilla_gui_files.txt); the `_isr`
# variant basename is MD-authored (absent from the manifest).
VANILLA_BASE = "tank_chassis_super_heavy_tank.gui"
MD_VARIANT = "tank_chassis_super_heavy_tank_isr.gui"
_DEAD = "GFX_dead_vanilla_ref"


@pytest.mark.parametrize(
    "path, parent",
    [
        ("a/b/" + MD_VARIANT, VANILLA_BASE),
        ("a/b/MD_unique_feature.gui", None),
        ("a/b/nounderscore.gui", None),
    ],
)
def test_vanilla_parent_basename(path, parent):
    assert vg._vanilla_parent_basename(path) == parent


# case: (refs as (sprite, .gui basename, line), live vanilla .gui index,
#        vanilla names loaded, (basename, line, severity) per finding)
_UNDEFINED_GUI_CASES = {
    "each site once": (
        [("GFX_absent", "md_panel.gui", 7), ("GFX_absent", "md_panel.gui", 7)],
        {},
        True,
        [("md_panel.gui", 7, Severity.ERROR)],
    ),
    "flag and vanilla-shaped names before vanilla loads": (
        [
            ("GFX_flag_USA", "md_panel.gui", 1),
            ("GFX_USA_shield", "md_panel.gui", 2),
            ("GFX_topbar_pp", "md_panel.gui", 3),
        ],
        {},
        False,
        [],
    ),
    "vanilla-shaped name after vanilla loads": (
        [("GFX_topbar_pp", "md_panel.gui", 3)],
        {},
        True,
        [("md_panel.gui", 3, Severity.ERROR)],
    ),
    "ref inherited from the vanilla parent": (
        [(_DEAD, VANILLA_BASE, 10), (_DEAD, MD_VARIANT, 20)],
        {},
        True,
        [(VANILLA_BASE, 10, Severity.WARNING), (MD_VARIANT, 20, Severity.WARNING)],
    ),
    # The old repo-wide downgrade wrongly silenced the unrelated MD file.
    "same ref in an unrelated MD file": (
        [(_DEAD, VANILLA_BASE, 10), (_DEAD, "MD_unique_feature.gui", 20)],
        {},
        True,
        [
            (VANILLA_BASE, 10, Severity.WARNING),
            ("MD_unique_feature.gui", 20, Severity.ERROR),
        ],
    ),
    "variant ref the parent does not carry": (
        [("GFX_only_in_variant", MD_VARIANT, 20)],
        {},
        True,
        [(MD_VARIANT, 20, Severity.ERROR)],
    ),
    "variant ref carried by the live vanilla parent": (
        [(_DEAD, MD_VARIANT, 20)],
        {VANILLA_BASE: {_DEAD}},
        True,
        [(MD_VARIANT, 20, Severity.WARNING)],
    ),
}


@pytest.mark.parametrize(
    "refs, vanilla_index, loaded, expected",
    _UNDEFINED_GUI_CASES.values(),
    ids=_UNDEFINED_GUI_CASES,
)
def test_undefined_gui_refs(
    tmp_path, monkeypatch, refs, vanilla_index, loaded, expected
):
    monkeypatch.setattr(vg, "_vanilla_gui_ref_index", lambda: vanilla_index)
    validator = _validator(tmp_path)
    validator._vanilla_defs_loaded = loaded

    validator._check_undefined_refs(
        [(name, _iface(tmp_path, base), line) for name, base, line in refs],
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )

    assert sorted(
        (os.path.basename(i.file), i.line, i.severity) for i in validator._issues
    ) == sorted(expected)


def test_case_mismatched_ref_gets_the_linux_diagnostic(tmp_path):
    validator = _validator(tmp_path)
    validator._vanilla_defs_loaded = True
    path = os.path.join(str(tmp_path), "common", "scripted_guis", "panel.txt")
    validator._check_undefined_refs(
        [("GFX_Ukr_Energy", path, 4)],
        {"GFX_ukr_energy"},
        source_label="scripted_guis",
        category="undefined-sprite",
        mod_defined_ci=vg.casefold_index({"GFX_ukr_energy"}),
    )
    message = validator._issues[0].message
    assert "case-mismatch" in message
    assert "defined as 'GFX_ukr_energy'" in message
    assert validator._issues[0].severity == vg.Severity.ERROR


def test_staged_mode_reports_only_staged_files(tmp_path):
    validator = _validator(tmp_path)
    validator._vanilla_defs_loaded = True
    validator.staged_only = True
    staged = _iface(tmp_path, "md_staged.gui")
    validator.staged_files = [staged]
    validator._check_undefined_refs(
        [
            ("GFX_absent", staged, 1),
            ("GFX_absent", _iface(tmp_path, "md_other.gui"), 2),
        ],
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    assert [os.path.basename(i.file) for i in validator._issues] == ["md_staged.gui"]


def test_scripted_gui_and_scripted_loc_refs_reach_the_report(tmp_path):
    _write(tmp_path / "interface" / "a.gfx", "spriteTypes = {\n}\n")
    _write(
        tmp_path / "common" / "scripted_guis" / "panel.txt",
        'image = "GFX_missing_sgui"\n',
    )
    _write(
        tmp_path / "common" / "scripted_localisation" / "text.txt",
        'localization_key = "GFX_missing_sloc"\n',
    )

    validator = _validator(tmp_path)
    validator.run_validations()

    messages = " ".join(i.message for i in validator._issues)
    assert "GFX_missing_sgui" in messages
    assert "GFX_missing_sloc" in messages


# --- undefined fonts --------------------------------------------------------


@pytest.mark.parametrize(
    "gui, findings",
    [
        (
            '# Status bar text.\ninstantTextBoxType = {\n\tfont = "hoi_16"\n}\n',
            [('font = "hoi_16"', 3)],
        ),
        ('instantTextBoxType = {\n\tfont = "hoi_16mbs"\n}\n', []),
        ('instantTextBoxType = {\n\tfont = "vic_18"\n}\n', []),
        ('#\tfont = "hoi_16"\n', []),
    ],
    ids=["undefined font", "mod font", "vanilla manifest font", "commented reference"],
)
def test_undefined_fonts(tmp_path, monkeypatch, gui, findings):
    monkeypatch.setattr(
        vg, "_load_vanilla_font_manifest", lambda: frozenset({"vic_18"})
    )
    _write(tmp_path / "interface" / "core.gfx", _CORE_FONTS)
    _write(tmp_path / "interface" / "view.gui", gui)
    validator = _validator(tmp_path)
    validator.run_validations()

    issues = _categories(validator, "undefined-font")
    assert [(i.message.split(" is ")[0], i.line) for i in issues] == findings


def test_live_vanilla_fonts_satisfy_a_gui_reference(tmp_path, monkeypatch):
    vanilla = _write(
        tmp_path / "vanilla" / "interface" / "fonts.gfx",
        'bitmapfonts = {\n\tbitmapfont = {\n\t\tname = "vic_18"\n\t}\n}\n',
    )
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [vanilla])
    _write(tmp_path / "interface" / "core.gfx", "bitmapfonts = {\n}\n")
    _write(
        tmp_path / "interface" / "view.gui",
        'instantTextBoxType = {\n\tfont = "vic_18"\n\tfont = "absent_18"\n}\n',
    )

    validator = _validator(tmp_path)
    validator._check_undefined_fonts()

    assert len(validator._issues) == 1
    assert 'font = "absent_18"' in validator._issues[0].message


def test_font_check_is_skipped_without_an_install_or_manifest(tmp_path):
    _write(tmp_path / "interface" / "core.gfx", "bitmapfonts = {\n}\n")
    _write(
        tmp_path / "interface" / "view.gui", 'instantTextBoxType = {\n\tfont = "x"\n}\n'
    )

    validator = _validator(tmp_path)
    validator._check_undefined_fonts()

    assert validator._issues == []


def test_staged_font_check_reports_only_staged_gui_files(tmp_path, monkeypatch):
    monkeypatch.setattr(vg, "_load_vanilla_font_manifest", lambda: frozenset({"x"}))
    _write(tmp_path / "interface" / "core.gfx", _CORE_FONTS)
    gui = 'instantTextBoxType = {\n\tfont = "absent_18"\n}\n'
    staged = _write(tmp_path / "interface" / "staged.gui", gui)
    _write(tmp_path / "interface" / "other.gui", gui)
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator.staged_files = [staged]

    validator._check_undefined_fonts()

    assert [os.path.basename(i.file) for i in validator._issues] == ["staged.gui"]


# --- £refs ------------------------------------------------------------------

# case: (sprite definition, loc language, loc ref, finding categories)
_LOC_REF_CASES = {
    "miscased ref": (
        "GFX_VTB_autocracy",
        "english",
        "£VTB_Autocracy",
        ["sprite-ref-case"],
    ),
    "matching ref": ("GFX_VTB_Autocracy", "english", "£VTB_Autocracy", []),
    "ref with no case match": (
        "GFX_real",
        "english",
        "£totally_absent",
        ["undefined-loc-sprite"],
    ),
    # Non-English loc is out of scope, and `£Réseau` truncates at the accent.
    "non-English ref": ("GFX_VTB_autocracy", "french", "£VTB_Autocracy", []),
    "pound sign": ("GFX_real", "english", "£5 billion", []),
}


@pytest.mark.parametrize(
    "sprite, language, ref, categories",
    _LOC_REF_CASES.values(),
    ids=_LOC_REF_CASES,
)
def test_loc_refs_run_by_default(tmp_path, sprite, language, ref, categories):
    _write_gfx(tmp_path, "test.gfx", _sprite(sprite, "gfx/vtb.dds"))
    _write(
        tmp_path / "localisation" / language / f"a_l_{language}.yml", f' a: "{ref}"\n'
    )
    validator = _validator(tmp_path)
    validator.run_validations()

    issues = [
        i
        for i in validator._issues
        if i.category in {"sprite-ref-case", "undefined-loc-sprite"}
    ]
    assert [
        (i.category, ref in i.message, i.file.endswith("a_l_english.yml"), i.severity)
        for i in issues
    ] == [(category, True, True, Severity.ERROR) for category in categories]


def test_loc_ref_case_check_is_scoped_to_staged_files(tmp_path):
    defined = {"GFX_ukr_energy"}
    loc = os.path.join(str(tmp_path), "localisation", "english")
    staged = os.path.join(loc, "staged_l_english.yml")
    other = os.path.join(loc, "other_l_english.yml")
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator.staged_files = [staged]
    validator._check_loc_refs(
        [("GFX_UKR_energy", other, 3)], defined, vg.casefold_index(defined)
    )
    assert validator._issues == []

    validator._check_loc_refs(
        [("GFX_UKR_energy", staged, 3)], defined, vg.casefold_index(defined)
    )
    assert len(validator._issues) == 1


# --- duplicate definitions --------------------------------------------------

# case: (sprites as (name, texture), (category, message fragment) per finding)
_DUPLICATE_CASES = {
    "name defined twice on two textures": (
        [("GFX_dup", "gfx/one.dds"), ("GFX_dup", "gfx/two.dds")],
        [
            ("duplicate-sprite", "defined 2 times"),
            ("duplicate-sprite", "different textures"),
        ],
    ),
    "name defined twice on one texture": (
        [("GFX_dup", "gfx/same.dds"), ("GFX_dup", "gfx/same.dds")],
        [("duplicate-sprite", "redundant")],
    ),
    "unique names": ([("GFX_a", "gfx/a.dds"), ("GFX_b", "gfx/b.dds")], []),
    "case variants on one texture": (
        [("GFX_idea_Nexter", "gfx/Nexter.dds"), ("GFX_idea_nexter", "gfx/Nexter.dds")],
        [("case-variant-sprite", "collapse them onto one name")],
    ),
    "case variants on separate textures": (
        [
            ("GFX_idea_IRGC", "gfx/iran/IRGC.dds"),
            ("GFX_idea_irgc", "gfx/factions/irgc.dds"),
        ],
        [("case-variant-sprite", "distinct textures")],
    ),
}


@pytest.mark.parametrize(
    "sprites, fragments", _DUPLICATE_CASES.values(), ids=_DUPLICATE_CASES
)
def test_duplicate_definitions(tmp_path, sprites, fragments):
    _write_gfx(tmp_path, "test.gfx", *(_sprite(n, t) for n, t in sprites))
    validator = _validator(tmp_path)
    validator._build_gfx_definitions()
    validator._check_duplicate_definitions()

    issues = [
        i
        for i in validator._issues
        if i.category in {"duplicate-sprite", "case-variant-sprite"}
    ]
    assert len(issues) == len({category for category, _ in fragments})
    assert all(i.severity == Severity.ERROR for i in issues)
    for category, fragment in fragments:
        assert any(i.category == category and fragment in i.message for i in issues)


# case: (.gfx files as {basename: sprite names}, check, category, reported names)
_STAGED_REPORT_CASES = {
    "duplicate name": (
        {"a.gfx": ["GFX_dup"], "b.gfx": ["GFX_dup", "GFX_old"], "c.gfx": ["GFX_old"]},
        "duplicate-sprite",
        ["GFX_dup"],
    ),
    "case variant": (
        {"a.gfx": ["GFX_Case"], "b.gfx": ["GFX_case", "GFX_Old"], "c.gfx": ["GFX_old"]},
        "case-variant-sprite",
        ["GFX_Case"],
    ),
}


@pytest.mark.parametrize(
    "gfx, category, reported", _STAGED_REPORT_CASES.values(), ids=_STAGED_REPORT_CASES
)
def test_staged_duplicates_need_a_staged_definition(tmp_path, gfx, category, reported):
    for basename, names in gfx.items():
        _write_gfx(tmp_path, basename, *(_sprite(n, "gfx/x.dds") for n in names))
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator.staged_files = [_iface(tmp_path, "a.gfx")]
    validator._build_gfx_definitions()
    validator._check_duplicate_definitions()

    issues = _categories(validator, category)
    assert [n for n in reported if any(n in i.message for i in issues)] == reported
    assert len(issues) == len(reported)


# --- unused sprites ---------------------------------------------------------

# case: (defined sprites, references, vanilla names, (category, sprite) per finding)
_UNUSED_CASES = {
    "sprite referenced only with other case": (
        {"GFX_ukr_energy"},
        {"GFX_UKR_energy"},
        set(),
        [("unused-sprite-case", "GFX_UKR_energy")],
    ),
    # GFX_idea_irgc and GFX_idea_IRGC are separate sprites on separate art.
    "defined case variant stays an orphan": (
        {"GFX_idea_irgc", "GFX_idea_IRGC"},
        {"GFX_idea_IRGC"},
        set(),
        [("unused-sprite", "GFX_idea_irgc")],
    ),
    "vanilla name override": (
        {"GFX_MODIFIER_ATTRITION"},
        set(),
        {"GFX_MODIFIER_ATTRITION"},
        [],
    ),
    "mod-only name with vanilla names loaded": (
        {"GFX_MD_only"},
        set(),
        {"GFX_MODIFIER_ATTRITION"},
        [("unused-sprite", "GFX_MD_only")],
    ),
    "vanilla-shaped mod-only name with vanilla names loaded": (
        {"GFX_topbar_md_only"},
        set(),
        {"GFX_MODIFIER_ATTRITION"},
        [("unused-sprite", "GFX_topbar_md_only")],
    ),
    "vanilla-shaped name without vanilla names": (
        {"GFX_topbar_md_only"},
        set(),
        set(),
        [],
    ),
    # The flag pattern covers engine-built names, which are never defined.
    "defined flag-shaped sprite": (
        {"GFX_british_flag"},
        set(),
        set(),
        [("unused-sprite", "GFX_british_flag")],
    ),
    # Focus icons are not GFX_-prefixed; the equipment exemption must not
    # swallow them.
    "unprefixed sprite": (
        {"focus_icon_orphan"},
        set(),
        set(),
        [("unused-sprite", "focus_icon_orphan")],
    ),
    "equipment icon": ({"GFX_util_vehicle_1_medium"}, set(), set(), []),
    # APC_1 looks like <TAG>_<name>; stripping the tag first left "1".
    "archetype with a three-letter prefix": ({"GFX_APC_1_medium"}, set(), set(), []),
    "tagged technology icon": ({"GFX_BEL_SAM0_medium"}, set(), set(), []),
    "untagged technology icon": ({"GFX_SAM0_medium"}, set(), set(), []),
    # Tank-designer profile sprites carry no size suffix.
    "designer profile icon": ({"GFX_BRA_MBT_1"}, set(), set(), []),
    # Tags may carry digits after the first letter: C01 = Custom_01.
    "tag with digits": ({"GFX_C01_util_vehicle_1_medium"}, set(), set(), []),
    # interface/MD_parties_icons.gfx: the shape matches, the archetype does not.
    "shape match without an archetype": (
        {"GFX_ALG_Autocracy_small"},
        set(),
        set(),
        [("unused-sprite", "GFX_ALG_Autocracy_small")],
    ),
    # Party logos share the GFX_<TAG>_<name> shape.
    "suffixless name that is not a technology": (
        {"GFX_BRA_NOVO"},
        set(),
        set(),
        [("unused-sprite", "GFX_BRA_NOVO")],
    ),
    "suffixless untagged technology": (
        {"GFX_SAM0"},
        set(),
        set(),
        [("unused-sprite", "GFX_SAM0")],
    ),
    "unknown stem with a size suffix": (
        {"GFX_BEL_nsb_SP_Anti_Air_0_medium"},
        set(),
        set(),
        [("unused-sprite", "GFX_BEL_nsb_SP_Anti_Air_0_medium")],
    ),
}


@pytest.mark.parametrize(
    "defined, refs, vanilla, expected", _UNUSED_CASES.values(), ids=_UNUSED_CASES
)
def test_unused_sprites(tmp_path, defined, refs, vanilla, expected):
    _write(tmp_path / _EQUIPMENT_FILE, EQUIPMENT_FIXTURE)
    _write(tmp_path / _TECH_FILE, TECHNOLOGY_FIXTURE)
    validator = _validator(tmp_path)
    validator._vanilla_defined = vanilla
    validator._vanilla_defs_loaded = bool(vanilla)

    validator._check_unused_sprites(defined=defined, all_refs=refs)

    assert len(validator._issues) == len(expected)
    for category, sprite in expected:
        assert any(
            i.category == category and sprite in i.message for i in validator._issues
        )


def test_unused_finding_names_the_sprite_and_its_definition(tmp_path):
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_orphan", "gfx/a.dds"))
    validator = _validator(tmp_path)
    validator._build_gfx_definitions()
    validator._check_unused_sprites(defined={"GFX_orphan"}, all_refs=set())
    assert [(i.message, i.file, i.line) for i in validator._issues] == [
        (
            "Unused GFX sprite 'GFX_orphan' (defined but never referenced)",
            "interface/test.gfx",
            2,
        )
    ]


def test_unused_check_is_skipped_in_staged_mode(tmp_path):
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator._check_unused_sprites(defined={"GFX_orphan"}, all_refs=set())
    assert validator._issues == []


def test_script_refs_include_equipment_designer_graphic_db(tmp_path):
    _write(
        tmp_path / "gfx" / "interface" / "equipmentdesigner" / "graphic_db" / "x.txt",
        "icons = {\n\t\tGFX_BRA_MBT_1\n}\n",
    )
    assert "GFX_BRA_MBT_1" in _validator(tmp_path)._collect_script_refs()


def test_lowercase_quadtexturesprite_is_not_unused(tmp_path):
    _write(
        tmp_path / "interface" / "bars.gfx",
        "progressbartype = {\n"
        '\tname = "GFX_Bundeswehr_bar"\n'
        '\ttexturefile1 = "gfx/interface/ger_bundeswehr_recovery.dds"\n'
        "}\n",
    )
    _write(
        tmp_path / "interface" / "german_bundeswehr_reform.gui",
        'quadtexturesprite = "GFX_Bundeswehr_bar"\n',
    )
    validator = _validator(tmp_path, report_unused=True)
    validator.run_validations()
    assert not [i for i in validator._issues if "GFX_Bundeswehr_bar" in i.message]


_NEVER_REFERENCED = (
    "spriteType = {\n"
    '\tname = "GFX_never_referenced"\n'
    '\ttexturefile = "gfx//interface/never_referenced.dds"\n'
    "}\n"
)


# The unused report is ~6.7k findings on a full repo, so a default run and CI
# skip it, including the script ref collection that feeds only it.
@pytest.mark.parametrize(
    "report_unused, hide, reported",
    [(False, None, False), (True, None, True), (True, "1", False), (True, "0", True)],
    ids=["default run", "report unused", "hide env set", "hide env off"],
)
def test_unused_report_gate(tmp_path, monkeypatch, report_unused, hide, reported):
    _write(tmp_path / "interface" / "test.gfx", _NEVER_REFERENCED)
    if hide is not None:
        monkeypatch.setenv("MD_GFX_HIDE_UNUSED", hide)
    kwargs = {"report_unused": True} if report_unused else {}
    validator = _validator(tmp_path, **kwargs)
    assert validator.report_unused is report_unused
    if not report_unused:
        monkeypatch.setattr(
            validator,
            "_collect_script_refs",
            lambda: pytest.fail("script refs collected"),
        )

    validator.run_validations()

    unused = [
        i
        for i in _categories(validator, "unused-sprite")
        if "GFX_never_referenced" in i.message
    ]
    assert bool(unused) is reported


def test_staged_report_unused_run_skips_the_full_repo_passes(tmp_path, monkeypatch):
    _write(tmp_path / "interface" / "a.gfx", 'spriteType = { name = "GFX_orphan" }\n')
    validator = _validator(tmp_path, report_unused=True)
    validator.staged_only = True
    validator.staged_files = []
    monkeypatch.setattr(
        validator, "_collect_script_refs", lambda: pytest.fail("script refs collected")
    )
    validator.run_validations()

    assert not _categories(validator, "unused-sprite")


# --- raw icon paths ---------------------------------------------------------

HISTORY = "history/countries/SOV.txt"
GRAPHIC_DB = "gfx/interface/equipmentdesigner/graphic_db/00.txt"
RAW_POOL = (
    "pool = {\n"
    "\ticons = {\n"
    "\t\tGFX_OK\n"
    '\t\t"GFX_OK_QUOTED"\n'
    '\t\t"gfx/interface/technologies/gwtank.dds"\n'
    "\t\tgfx/interface/technologies/Su-57.dds\n"
    "\t}\n"
    "\tmodels = {\n"
    '\t\t"gfx/should_not_flag.dds"\n'
    "\t}\n"
    "}\n"
)


def _variant(icon, name="Su-57"):
    return f'create_equipment_variant = {{\n\tname = "{name}"\n\ticon = {icon}\n}}\n'


def _raw_icon_issues(validator):
    return _categories(validator, "raw-icon-path")


@pytest.mark.parametrize(
    "icon",
    [
        '"gfx/interface/technologies/SOV/AIR/foo.dds"',
        "gfx/interface/technologies/SOV/AIR/bar.dds",
        '"gfx\\interface\\technologies\\SOV\\AIR\\baz.dds"',
        "gfx\\interface\\technologies\\SOV\\AIR\\qux.dds",
        "lone.dds",
    ],
)
def test_raw_variant_icon_is_flagged_on_its_line(icon):
    assert vg.raw_variant_icon_paths(_variant(icon)) == [(icon.strip('"'), 3)]


@pytest.mark.parametrize(
    "text",
    [
        _variant('"GFX_SOV_AIR_ok"'),
        _variant("GFX_SOV_AIR_ok_bare"),
        "focus = {\n\ticon = gfx/interface/goals/bad.dds\n}\n",
        'create_equipment_variant = {\n\t#icon = "gfx/commented.dds"\n}\n',
    ],
)
def test_sprite_focus_and_commented_icons_are_ignored(text):
    assert vg.raw_variant_icon_paths(text) == []


def test_hash_inside_a_quoted_name_does_not_hide_the_icon():
    text = _variant("gfx/a.dds", name="Batch #1") + _variant("gfx/b.dds")
    assert vg.raw_variant_icon_paths(text) == [("gfx/a.dds", 3), ("gfx/b.dds", 7)]


def test_graphic_db_icons_flag_paths_and_ignore_models():
    assert vg.raw_graphic_db_icon_paths(RAW_POOL) == [
        ("gfx/interface/technologies/gwtank.dds", 5),
        ("gfx/interface/technologies/Su-57.dds", 6),
    ]


@pytest.mark.parametrize(
    "relative_path, body, line",
    [
        (HISTORY, _variant("gfx/interface/technologies/SOV/AIR/Su-57.dds"), 3),
        (
            GRAPHIC_DB,
            RAW_POOL.replace('\t\t"gfx/interface/technologies/gwtank.dds"\n', ""),
            5,
        ),
    ],
)
def test_run_reports_a_raw_icon_path_as_an_error(tmp_path, relative_path, body, line):
    write_under(tmp_path, relative_path, body)

    (issue,) = _raw_icon_issues(run_validator(GfxReferenceValidator, tmp_path))

    assert issue.severity == Severity.ERROR
    assert "Su-57.dds" in issue.message
    assert (issue.file.replace("\\", "/"), issue.line) == (relative_path, line)


def test_run_accepts_sprite_icons(tmp_path):
    write_under(tmp_path, HISTORY, _variant('"GFX_SOV_AIR_Su_57"'))
    write_under(
        tmp_path, GRAPHIC_DB, "pool = {\n\ticons = {\n\t\tGFX_SOV_AIR_Su_57\n\t}\n}\n"
    )
    assert _raw_icon_issues(run_validator(GfxReferenceValidator, tmp_path)) == []


def test_staged_run_checks_only_staged_graphic_db_files(tmp_path):
    staged = write_under(tmp_path, GRAPHIC_DB, RAW_POOL)
    write_under(tmp_path, GRAPHIC_DB.replace("00.txt", "01.txt"), RAW_POOL)
    validator = GfxReferenceValidator(
        str(tmp_path), use_colors=False, workers=1, no_cache=True
    )
    validator.staged_only = True
    validator.staged_files = [str(staged)]

    validator.run_validations()

    assert {i.file.replace("\\", "/") for i in _raw_icon_issues(validator)} == {
        GRAPHIC_DB
    }


# --- command line -----------------------------------------------------------


def test_report_unused_flag_is_registered():
    parser = argparse.ArgumentParser()
    vg._add_extra_args(parser)
    assert parser.parse_args(["--report-unused"]).report_unused is True
    assert parser.parse_args([]).report_unused is False


def test_main_exits_zero_on_a_clean_mod(tmp_path, monkeypatch):
    _write(tmp_path / "interface" / "a.gfx", "spriteTypes = {\n}\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_gfx_references.py", "--path", str(tmp_path), "--workers", "1"],
    )
    with pytest.raises(SystemExit) as exit_info:
        vg.main()
    assert exit_info.value.code == 0
