"""Tests for the equipment-icon exemption in the unused-sprite check.

Equipment icons (GFX_util_vehicle_1_medium, GFX_AFG_util_vehicle_1_medium) are
resolved by the engine from the equipment archetype name and never appear
literally in script, so `_check_unused_sprites` must not flag them as unused.
The exemption is membership-based, not shape-based: a sprite that merely
matches the GFX_<TAG_>name_(small|medium|large) shape but whose captured name
is not a real equipment archetype must still be reported.
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
    "}\n"
)


def _write_equipment(mod_path, text=EQUIPMENT_FIXTURE):
    eq_dir = os.path.join(mod_path, "common", "units", "equipment")
    os.makedirs(eq_dir, exist_ok=True)
    with open(os.path.join(eq_dir, "test_equipment.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)


def test_equipments_block_and_entry_regex_parse_one_tab_entries():
    block = vg._EQUIPMENTS_BLOCK_RE.search(EQUIPMENT_FIXTURE)
    assert block is not None
    body, end = extract_block_from_text(EQUIPMENT_FIXTURE, block.start())
    assert end != -1
    entries = set(vg._EQUIPMENT_ENTRY_RE.findall(body))
    # nested `values` two tabs deep must not be picked up as an entry
    assert entries == {"util_vehicle_1", "infantry_equipment_0"}


def test_load_equipment_names_reads_top_level_entries(tmp_path):
    _write_equipment(str(tmp_path))
    assert vg._load_equipment_names(str(tmp_path)) == frozenset(
        {"util_vehicle_1", "infantry_equipment_0"}
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
