"""Behavior tests for the MIO equipment group / equipment_type sprite check."""

import pytest
from validate_mio_icons import Validator, parse_groups, parse_org_equipment_types
from validator_common import Severity

GROUPS = (
    "mio_cat_all_armor = {\n"  # 1: has GFX_mio_cat_all_armor
    "\tequipment_type = {\n"
    "\t\tmedium_tank_chassis\n"
    "\t}\n"
    "}\n"
    "\n"
    "mio_cat_all_utils = { # This is the group the engine complains about\n"  # 7
    "\tequipment_type = {\n"
    "\t\tutil_vehicle_type\n"
    "\t}\n"
    "}\n"
)

ORGS = (
    "TST_ok_manufacturer = {\n"  # 1
    "\tallowed = { original_tag = TST }\n"
    "\tequipment_type = {\n"  # 3
    "\t\tmio_cat_all_armor\n"
    "\t\tartillery_equipment\n"
    "\t\tanti_air\n"
    "\t}\n"
    "\ttrait = {\n"
    "\t\ttoken = TST_trait\n"
    "\t\tlimit_to_equipment_type = { no_sprite_for_this }\n"
    "\t}\n"
    "}\n"
    "\n"
    "TST_broken_manufacturer = {\n"  # 14
    "\tequipment_type = {\n"  # 15
    "\t\tmio_cat_all_utils\n"
    "\t\theavy_frigate\n"
    "\t\t# medium_plane_airframe\n"
    "\t}\n"
    "}\n"
    "\n"
    "TST_thin_manufacturer = {\n"  # 22
    "\tinclude = generic_infantry_equipment_organization\n"
    "}\n"
)

GFX = (
    "spriteTypes = {\n"
    '\tspriteType = { name = "GFX_mio_cat_all_armor" texturefile = "a.dds" }\n'
    '\tspriteType = { name = "GFX_military_industrial_organization_artillery_equipment" texturefile = "b.dds" }\n'
    "}\n"
)

VANILLA = frozenset({"GFX_military_industrial_organization_anti_air"})


def _write_fixture(tmp_path, groups: str = GROUPS, orgs: str = ORGS, gfx: str = GFX):
    group_dir = tmp_path / "common" / "equipment_groups"
    org_dir = tmp_path / "common" / "military_industrial_organization" / "organizations"
    gfx_dir = tmp_path / "interface"
    for directory in (group_dir, org_dir, gfx_dir):
        directory.mkdir(parents=True)
    (group_dir / "mio_equipment_groups.txt").write_text(groups, encoding="utf-8")
    (org_dir / "MD_TST_organizations.txt").write_text(orgs, encoding="utf-8")
    (gfx_dir / "test.gfx").write_text(gfx, encoding="utf-8")


@pytest.fixture(autouse=True)
def _controlled_sprites(monkeypatch):
    # A fixture .gfx holds a handful of sprites, so the real floor would skip
    # every test; the vanilla manifest is pinned so `anti_air` resolves the
    # same way on a machine with and without a HOI4 install.
    monkeypatch.setattr("validate_mio_icons._MIN_SPRITE_INDEX", 0)
    monkeypatch.setattr("validate_mio_icons._vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(
        "validate_mio_icons._load_vanilla_sprite_manifest", lambda: VANILLA
    )
    monkeypatch.setattr(
        "validate_mio_icons.build_sprite_index",
        lambda mod_path, **_: _mod_sprites(mod_path),
    )


def _mod_sprites(mod_path):
    import re
    from pathlib import Path

    names = set()
    for path in Path(mod_path).glob("interface/**/*.gfx"):
        names.update(re.findall(r'name\s*=\s*"(GFX_[^"]+)"', path.read_text()))
    return names


def test_parse_groups_reads_top_level_tokens_with_lines():
    assert parse_groups(GROUPS) == [("mio_cat_all_armor", 1), ("mio_cat_all_utils", 7)]


def test_parse_org_equipment_types_skips_limits_and_include_only_orgs():
    tokens = parse_org_equipment_types(ORGS)
    assert tokens == [
        ("mio_cat_all_armor", 3),
        ("artillery_equipment", 3),
        ("anti_air", 3),
        ("mio_cat_all_utils", 15),
        ("heavy_frigate", 15),
        ("medium_plane_airframe", 15),
    ]


def test_missing_group_sprite_is_an_error_at_the_group_definition(
    tmp_path, issues_by_line
):
    _write_fixture(tmp_path)
    issues, _ = issues_by_line(Validator, tmp_path)
    issue = issues[("mio-equipment-group-icon", 7)]
    assert issue.severity == Severity.ERROR
    assert "GFX_mio_cat_all_utils" in issue.message
    assert "zMD_military_industrial_icons.gfx" in issue.message
    assert issue.file.replace("\\", "/").endswith("mio_equipment_groups.txt")


def test_group_token_in_an_org_is_not_reported_again(tmp_path, issues_by_line):
    _write_fixture(tmp_path)
    issues, _ = issues_by_line(Validator, tmp_path)
    assert not [
        key
        for key, issue in issues.items()
        if key[0] == "mio-equipment-type-icon" and "mio_cat_all_utils" in issue.message
    ]


def test_raw_token_without_sprite_is_an_error_on_the_equipment_type_line(
    tmp_path, issues_by_line
):
    _write_fixture(tmp_path)
    issues, _ = issues_by_line(Validator, tmp_path)
    issue = issues[("mio-equipment-type-icon", 15)]
    assert issue.severity == Severity.ERROR
    assert "GFX_military_industrial_organization_heavy_frigate" in issue.message


def test_commented_out_token_is_ignored(tmp_path, issues_by_line):
    _write_fixture(tmp_path)
    issues, _ = issues_by_line(Validator, tmp_path)
    assert not [
        issue for issue in issues.values() if "medium_plane_airframe" in issue.message
    ]


def test_mod_and_vanilla_sprites_both_resolve(tmp_path, issues_by_line):
    _write_fixture(tmp_path)
    issues, _ = issues_by_line(Validator, tmp_path)
    messages = [issue.message for issue in issues.values()]
    assert not [m for m in messages if "artillery_equipment" in m]
    assert not [m for m in messages if "anti_air" in m]
    assert not [m for m in messages if "mio_cat_all_armor" in m]


def test_clean_fixture_reports_nothing(tmp_path, issues_by_line):
    gfx = GFX[: GFX.rindex("}")] + (
        '\tspriteType = { name = "GFX_mio_cat_all_utils" texturefile = "c.dds" }\n'
        '\tspriteType = { name = "GFX_military_industrial_organization_heavy_frigate" texturefile = "d.dds" }\n'
        "}\n"
    )
    _write_fixture(tmp_path, gfx=gfx)
    issues, _ = issues_by_line(Validator, tmp_path)
    assert issues == {}


def test_small_sprite_index_skips_the_check(tmp_path, monkeypatch, issues_by_line):
    monkeypatch.setattr("validate_mio_icons._MIN_SPRITE_INDEX", 1000)
    _write_fixture(tmp_path)
    issues, _ = issues_by_line(Validator, tmp_path)
    assert issues == {}
