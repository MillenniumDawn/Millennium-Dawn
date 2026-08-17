"""Tests for the engine-resolved icon exemption in the unused-sprite check.

Equipment icons (GFX_util_vehicle_1_medium, GFX_AFG_util_vehicle_1_medium),
country tech-tree icons (GFX_BEL_SAM0_medium) and tank-designer profile icons
(GFX_BRA_MBT_1) are resolved by the engine from the equipment archetype or
technology id and never appear literally in script, so `_check_unused_sprites`
must not flag them as unused. The exemption is membership-based, not
shape-based: a sprite that merely matches the GFX_<TAG_>name_(small|medium|large)
shape but whose captured name is neither a real archetype nor a technology must
still be reported.
"""

import os

import validate_gfx_references as vg
from shared_utils import extract_block_from_text
from validate_gfx_references import Validator as GfxReferenceValidator

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


def _write_equipment(mod_path, text=EQUIPMENT_FIXTURE):
    eq_dir = os.path.join(mod_path, "common", "units", "equipment")
    os.makedirs(eq_dir, exist_ok=True)
    with open(os.path.join(eq_dir, "test_equipment.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)


def _write_technologies(mod_path, text=TECHNOLOGY_FIXTURE):
    tech_dir = os.path.join(mod_path, "common", "technologies")
    os.makedirs(tech_dir, exist_ok=True)
    with open(os.path.join(tech_dir, "test_tech.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)


def test_equipments_block_and_entry_regex_parse_one_tab_entries():
    block = vg._EQUIPMENTS_BLOCK_RE.search(EQUIPMENT_FIXTURE)
    assert block is not None
    body, end = extract_block_from_text(EQUIPMENT_FIXTURE, block.start())
    assert end != -1
    entries = set(vg._EQUIPMENT_ENTRY_RE.findall(body))
    # nested `values` two tabs deep must not be picked up as an entry
    assert entries == {"util_vehicle_1", "infantry_equipment_0", "APC_1"}


def test_load_equipment_names_reads_top_level_entries(tmp_path):
    _write_equipment(str(tmp_path))
    assert vg._load_equipment_names(str(tmp_path)) == frozenset(
        {"util_vehicle_1", "infantry_equipment_0", "APC_1"}
    )


def test_load_equipment_names_missing_dir_returns_empty(tmp_path):
    assert vg._load_equipment_names(str(tmp_path)) == frozenset()


def test_equipment_icon_exempted_from_unused_report(tmp_path):
    _write_equipment(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(
        defined={"GFX_util_vehicle_1_medium"},
        all_refs=set(),
    )
    assert not v._issues


def test_archetype_starting_with_three_letter_prefix_is_exempted(tmp_path):
    # APC_1, IFV_1, MBT_1 look like <TAG>_<name>: stripping the tag first leaves
    # "1", which is no archetype, so the sprite was reported as unused.
    _write_equipment(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(
        defined={"GFX_APC_1_medium"},
        all_refs=set(),
    )
    assert not v._issues


def test_shape_match_without_real_archetype_stays_reported(tmp_path):
    # Real MD sprite: interface/MD_parties_icons.gfx defines GFX_ALG_Autocracy_small,
    # which matches the GFX_<TAG>_name_small shape but "Autocracy" is not an
    # equipment archetype — membership must reject the shape-only match.
    _write_equipment(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(
        defined={"GFX_ALG_Autocracy_small"},
        all_refs=set(),
    )
    assert any("GFX_ALG_Autocracy_small" in i.message for i in v._issues)


def test_unused_check_logs_notice_when_equipment_dir_missing(tmp_path, monkeypatch):
    logged = []
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    monkeypatch.setattr(v, "log", lambda msg, *a, **k: logged.append(msg))
    v._check_unused_sprites(defined=set(), all_refs=set())
    assert any("equipment" in msg for msg in logged)


def test_load_technology_names_reads_top_level_entries(tmp_path):
    _write_technologies(str(tmp_path))
    assert vg._load_technology_names(str(tmp_path)) == frozenset({"MBT_1", "SAM0"})


def test_load_technology_names_missing_dir_returns_empty(tmp_path):
    assert vg._load_technology_names(str(tmp_path)) == frozenset()


def test_load_technology_names_refresh_after_edit(tmp_path, monkeypatch):
    # Names are content-cached per file; an edited file must not serve stale ids.
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write_technologies(str(tmp_path))
    assert vg._load_technology_names(str(tmp_path)) == frozenset({"MBT_1", "SAM0"})
    _write_technologies(
        str(tmp_path), "technologies = {\n\tMBT_2 = {\n\t\tyear = 1950\n\t}\n}\n"
    )
    assert vg._load_technology_names(str(tmp_path)) == frozenset({"MBT_2"})


def test_unused_check_logs_notice_when_technology_dir_missing(tmp_path, monkeypatch):
    logged = []
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    monkeypatch.setattr(v, "log", lambda msg, *a, **k: logged.append(msg))
    v._check_unused_sprites(defined=set(), all_refs=set())
    assert any("technologies" in msg for msg in logged)


def test_tagged_technology_icon_exempted_from_unused_report(tmp_path):
    _write_equipment(str(tmp_path))
    _write_technologies(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_BEL_SAM0_medium"}, all_refs=set())
    assert not v._issues


def test_untagged_technology_icon_exempted_from_unused_report(tmp_path):
    _write_equipment(str(tmp_path))
    _write_technologies(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_SAM0_medium"}, all_refs=set())
    assert not v._issues


def test_suffixless_designer_profile_icon_exempted_from_unused_report(tmp_path):
    # Tank-designer profile sprites carry no size suffix: GFX_<TAG>_<tech_id>.
    _write_equipment(str(tmp_path))
    _write_technologies(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_BRA_MBT_1"}, all_refs=set())
    assert not v._issues


def test_digit_bearing_tag_icon_exempted_from_unused_report(tmp_path):
    # Tags may carry digits after the first letter: C01 = Custom_01.
    _write_equipment(str(tmp_path))
    _write_technologies(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_C01_util_vehicle_1_medium"}, all_refs=set())
    assert not v._issues


def test_suffixless_non_technology_name_stays_reported(tmp_path):
    # Party logos share the GFX_<TAG>_<name> shape; only a real tech id is exempt.
    _write_equipment(str(tmp_path))
    _write_technologies(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_BRA_NOVO"}, all_refs=set())
    assert any("GFX_BRA_NOVO" in i.message for i in v._issues)


def test_suffixless_untagged_technology_name_stays_reported(tmp_path):
    _write_equipment(str(tmp_path))
    _write_technologies(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_SAM0"}, all_refs=set())
    assert any("GFX_SAM0" in i.message for i in v._issues)


def test_unknown_stem_with_size_suffix_stays_reported(tmp_path):
    _write_equipment(str(tmp_path))
    _write_technologies(str(tmp_path))
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(
        defined={"GFX_BEL_nsb_SP_Anti_Air_0_medium"}, all_refs=set()
    )
    assert any("GFX_BEL_nsb_SP_Anti_Air_0_medium" in i.message for i in v._issues)


def test_script_refs_include_equipment_designer_graphic_db(tmp_path):
    db_dir = os.path.join(
        str(tmp_path), "gfx", "interface", "equipmentdesigner", "graphic_db"
    )
    os.makedirs(db_dir, exist_ok=True)
    with open(os.path.join(db_dir, "x.txt"), "w", encoding="utf-8") as fh:
        fh.write("icons = {\n\t\tGFX_BRA_MBT_1\n}\n")
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert "GFX_BRA_MBT_1" in v._collect_script_refs()
