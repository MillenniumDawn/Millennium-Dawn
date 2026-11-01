"""Exercise Greek, Turkish, and historical USA AI equipment regressions."""

import pytest
from ai_equipment_buildability import check_ammunition_compatibility, parse_designs
from equipment_module_slots import (
    _iter_blocks,
    blank_comments,
    build_equipment_index,
    check_target_variants,
)
from shared.paths import REPO_ROOT
from shared.suite import assert_findings, build_validator, write_tree
from validate_ai_equipment import Validator
from validator_common import Severity


@pytest.fixture(scope="module")
def live_equipment_index():
    return build_equipment_index(str(REPO_ROOT / "common/units/equipment"))


@pytest.mark.parametrize(
    "historical", (True, False), ids=("before-aaa631c76f", "corrected-USA-APC")
)
def test_usa_apc_ammunition_regression(live_equipment_index, historical):
    path = "common/ai_equipment/USA_tank.txt"
    text = (REPO_ROOT / path).read_text(encoding="utf-8-sig")
    group = next(
        text[header : hi + 1]
        for name, _, hi, header in _iter_blocks(blank_comments(text), 0, len(text))
        if name == "USA_APC_design"
    )
    weapon = "main_armament_slot = small_autocannon_3"
    ammunition = "ammunition_load_slot = anti_infantry_autocannon_ammo_3"
    assert group.count(weapon) == group.count(ammunition) == 1
    if historical:
        group = group.replace(
            weapon,
            "main_armament_slot = { any_of = { small_autocannon_3 afv_machine_gun_3 } }",
        ).replace(ammunition, "ammunition_load_slot = machine_gun_ammo")
    analysis = check_ammunition_compatibility(
        parse_designs(group, path), live_equipment_index
    )
    findings = analysis.findings
    assert [(record["design"], record["status"]) for record in analysis.records] == [
        ("modern_APC_default", "incompatible" if historical else "checked"),
        ("new_APC_default", "checked"),
    ]
    assert_findings(
        [f"{issue.category}: {issue.message}" for issue in findings],
        (
            [
                (
                    "ai-equipment-incompatible-ammo",
                    "USA_APC_design/modern_APC_default",
                    "small_autocannon_3",
                    "machine_gun_ammo",
                )
            ]
            if historical
            else []
        ),
    )
    assert all(
        issue.severity == Severity.WARNING and issue.file == path for issue in findings
    )
    assert not any(
        finding.kind == "category_mismatch"
        and "ammunition_load_slot" in finding.message
        for finding in check_target_variants(group, live_equipment_index)
    )


@pytest.fixture(scope="module")
def live_naval_sources():
    countries = {
        "ALG": "Algeria",
        "ARG": "Argentina",
        "AST": "Australia",
        "GRE": "Greece",
        "TUR": "Turkey",
    }
    paths = [
        REPO_ROOT / path
        for tag, name in countries.items()
        for path in (
            f"common/ai_equipment/{tag}_naval.txt",
            f"history/countries/{tag} - {name}.txt",
        )
    ]
    for directory in (
        "common/bookmarks",
        "common/technologies",
        "common/technology_tags",
        "common/scripted_effects",
        "common/special_projects",
        "common/units/equipment",
    ):
        paths.extend((REPO_ROOT / directory).rglob("*.txt"))
    return {
        path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8-sig")
        for path in paths
    }


def test_naval_regression_sources(tmp_path, live_naval_sources):
    sources = live_naval_sources
    write_tree(tmp_path, sources)
    for country in ("GRE", "TUR"):
        path = f"common/ai_equipment/{country}_naval.txt"
        designs = parse_designs(sources[path], path)
        assert designs and all(design.users == {country} for design in designs)
        assert any(design.hull == "frigate_hull_2" for design in designs)
    validator = build_validator(Validator, tmp_path, check_buildability=True)
    validator._validate_buildability()
    assert validator.errors_found == 0
    assert not any(
        "DLC configuration limit" in issue.message for issue in validator._issues
    )
    assert all(issue.severity == Severity.WARNING for issue in validator._issues)
    assert all(
        issue.file.startswith("common/ai_equipment/")
        and issue.message.startswith(("ALG:", "ARG:", "AST:", "GRE:", "TUR:"))
        for issue in validator._issues
    )
    assert validator.analysis_records


@pytest.mark.parametrize(
    ("country", "group", "design", "module", "technology"),
    (
        (
            "ALG - Algeria",
            "ALG_corvettes",
            "ALG_Corvette_1970s",
            "module_torpedoes_2",
            "tech_torpedoes_2",
        ),
        (
            "ARG - Argentina",
            "ARG_attack_submarines",
            "ARG_attack_sub_1960s",
            "module_sub_esm_1",
            "tech_combat_radar_2",
        ),
        (
            "AST - Australia",
            "AST_unique_frigates",
            "AST_adelaide_class_2",
            "module_light_surface_diesel_power_1",
            "tech_diesel_power_systems_1",
        ),
    ),
)
@pytest.mark.parametrize("researched", (False, True))
def test_live_module_claim_tracks_its_enabling_technology(
    tmp_path, live_naval_sources, country, group, design, module, technology, researched
):
    sources = dict(live_naval_sources)
    history = f"history/countries/{country}.txt"
    sources[
        history
    ] += (
        f"\n2000.1.1.12 = {{ set_technology = {{ {technology} = {int(researched)} }} }}"
    )
    write_tree(tmp_path, sources)
    validator = build_validator(Validator, tmp_path, check_buildability=True)
    validator._validate_buildability()
    records = [
        record
        for record in validator.analysis_records
        if record.get("country") == country[:3]
        and record["group"] == group
        and record["design"] == design
    ]
    assert records
    claim = f"{module} requires {technology}"
    assert any(claim in record["reason"] for record in records) is not researched
