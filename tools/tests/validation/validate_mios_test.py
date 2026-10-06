"""Tests for `validate_mios.py` (MIO organization definitions)."""

import random
import re

import validate_mios as V


def _validator(tmp_path):
    return V.Validator(str(tmp_path))


def test_commented_org_blocks_are_not_parsed():
    text = (
        "# BAD_org = {\n"
        "#   allowed = { original_tag = BAD }\n"
        "# }\n"
        "GENERIC_live_org = { allowed = { always = yes } }\n"
    )
    clean = V.blank_comments(text)
    assert [org_id for _start, _end, org_id in V._block_spans(clean)] == [
        "GENERIC_live_org"
    ]


def test_shared_org_ids_are_exempt(tmp_path):
    v = _validator(tmp_path)
    v._check_id("generic_tank_equipment_organization", "f.txt", 0)
    v._check_id("GENERIC_marshall_tractor_works", "f.txt", 0)
    assert not v._issues


def test_non_tag_id_flagged(tmp_path):
    v = _validator(tmp_path)
    v._check_id("norinco_manufacturer", "f.txt", 3)
    assert v._issues[0].category == "org-id-format"
    assert v._issues[0].line == 4


def test_allowed_tag_mismatch_flagged(tmp_path):
    v = _validator(tmp_path)
    body = "\tallowed = { original_tag = GER }\n"
    v._check_allowed("FRA_naval_manufacturer", body, "f.txt", 0)
    assert v._issues[0].category == "org-allowed-tag"
    assert "original_tag = FRA" in v._issues[0].message


def test_allowed_tag_match_passes(tmp_path):
    v = _validator(tmp_path)
    body = "\tallowed = { original_tag = ISR }\n"
    v._check_allowed("ISR_rafael_materiel_manufacturer", body, "f.txt", 0)
    assert not v._issues


def test_initial_trait_naming(tmp_path):
    v = _validator(tmp_path)
    good = "initial_trait = {\n\tname = GER_Mercedes_trait\n}"
    v._check_initial_trait("GER_mercedes_manufacturer", good, "f.txt", 0)
    assert not v._issues
    bad = "initial_trait = {\n\tname = tank_facility_foundry\n}"
    v._check_initial_trait("NKO_second_economic_committee", bad, "f.txt", 0)
    assert v._issues[0].category == "initial-trait-name"


def test_generic_initial_trait_reference_is_exempt(tmp_path):
    v = _validator(tmp_path)
    body = (
        "initial_trait = {\n\tname = generic_mio_initial_trait_infantry_manufacturer\n}"
    )
    v._check_initial_trait("ARG_fabricaciones_militares_manufacturer", body, "f.txt", 0)
    assert not v._issues


def test_position_x_bounds(tmp_path):
    v = _validator(tmp_path)
    v._check_positions("TST_org", "\tposition = { x = -1 y = 0 }\n", "f.txt", 0)
    assert not v._issues
    v._check_positions("TST_org", "\tposition = { x = 12 y = 3 }\n", "f.txt", 0)
    assert v._issues[0].category == "trait-x-bounds"


def test_position_x_bounds_exempt_orgs(tmp_path):
    body = "\tposition = { x = 16 y = 0 }\n"
    v = _validator(tmp_path)
    v._check_positions("generic_naval_equipment_organization", body, "f.txt", 0)
    assert not v._issues

    v = _validator(tmp_path)
    v._check_positions("generic_some_new_org", body, "f.txt", 0)
    assert v._issues[0].category == "trait-x-bounds"


def test_percentage_org_modifier_whole_number_flagged(tmp_path):
    v = _validator(tmp_path)
    body = (
        "\tinitial_trait = {\n"
        "\t\torganization_modifier = {\n"
        "\t\t\tmilitary_industrial_organization_size_up_requirement = -3\n"
        "\t\t}\n"
        "\t}\n"
    )
    v._check_org_modifier_range(body, "f.txt", 0)
    assert len(v._issues) == 1
    assert v._issues[0].category == "org-modifier-out-of-range"
    assert v._issues[0].line == 3


def test_fractional_org_modifier_passes(tmp_path):
    v = _validator(tmp_path)
    body = (
        "\torganization_modifier = {\n"
        "\t\tmilitary_industrial_organization_size_up_requirement = -0.15\n"
        "\t\tmilitary_industrial_organization_research_bonus = 0.10\n"
        "\t}\n"
    )
    v._check_org_modifier_range(body, "f.txt", 0)
    assert not v._issues


def test_task_capacity_is_exempt_from_range_check(tmp_path):
    v = _validator(tmp_path)
    body = "\torganization_modifier = { military_industrial_organization_task_capacity = 3 }\n"
    v._check_org_modifier_range(body, "f.txt", 0)
    assert not v._issues


def test_empty_on_complete_flagged(tmp_path):
    v = _validator(tmp_path)
    v._check_on_complete("\ton_complete = {\n\t}\n", "f.txt", 0)
    assert v._issues[0].category == "on-complete-empty"
    v._check_on_complete(
        "\ton_complete = { expenditure_for_mio_upgrade = yes }\n", "f.txt", 0
    )
    assert len(v._issues) == 1


def test_header_literal_string_flagged(tmp_path):
    v = _validator(tmp_path)
    body = 'tree_header_text = {\n\ttext = "Lithgow Lineage"\n\tx = 1\n}'
    v._check_header_text("AST_nioa_australia_material", body, "f.txt", 0, set())
    assert v._issues[0].category == "header-text-not-tokenized"
    assert v._issues[0].severity == "error"
    assert "AST_nioa_australia_material_mio_header_<slug>" in v._issues[0].message


def test_header_token_with_loc_passes(tmp_path):
    v = _validator(tmp_path)
    body = "tree_header_text = {\n\ttext = NKO_mio_header_armor\n\tx = 1\n}"
    v._check_header_text(
        "NKO_1_bureau_materiel_manufacturer",
        body,
        "f.txt",
        0,
        {"NKO_mio_header_armor"},
    )
    assert not v._issues


def test_header_token_resolves_via_tag_prefix(tmp_path):
    v = _validator(tmp_path)
    body = "tree_header_text = {\n\ttext = mio_header_foo\n\tx = 1\n}"
    v._check_header_text(
        "ALG_khenchela_arms_manufacturer", body, "f.txt", 0, {"ALG_mio_header_foo"}
    )
    assert not v._issues


def test_header_token_without_loc_flagged(tmp_path):
    v = _validator(tmp_path)
    body = "tree_header_text = {\n\ttext = x\n\tx = 2\n}"
    v._check_header_text("ENG_supacat_utility_manufacturer", body, "f.txt", 4, set())
    assert v._issues[0].category == "header-text-loc-missing"
    assert v._issues[0].severity == "error"
    assert v._issues[0].line == 5


def test_shared_org_header_has_no_tag_fallback(tmp_path):
    v = _validator(tmp_path)
    body = "tree_header_text = {\n\ttext = kamov_header\n\tx = 2\n}"
    v._check_header_text(
        "GENERIC_mil_kamov_rotorworks", body, "f.txt", 0, {"GEN_kamov_header"}
    )
    assert v._issues[0].category == "header-text-loc-missing"


def test_trait_name_with_loc_passes(tmp_path):
    v = _validator(tmp_path)
    body = "trait = {\n\ttoken = ALG_khenchela_trait_desert_hardened\n\tname = ALG_khenchela_trait_desert_hardened\n}"
    v._check_trait_localisation(
        "ALG_khenchela_arms_manufacturer",
        body,
        "f.txt",
        0,
        {"ALG_khenchela_trait_desert_hardened"},
    )
    assert not v._issues


def test_trait_name_without_loc_flagged(tmp_path):
    v = _validator(tmp_path)
    body = "trait = {\n\ttoken = ROM_romarm_export_ammo\n\tname = ROM_romarm_trait_export_ammo\n}"
    v._check_trait_localisation(
        "ROM_romarm_material_manufacturer", body, "f.txt", 0, set()
    )
    assert v._issues[0].category == "trait-loc-missing"
    assert v._issues[0].severity == "error"
    assert "ROM_romarm_trait_export_ammo" in v._issues[0].message


def test_trait_without_name_uses_org_token_fallback(tmp_path):
    body = "trait = {\n\ttoken = FRA_arquus_griffon_vbmr\n}"
    v = _validator(tmp_path)
    v._check_trait_localisation(
        "FRA_arquus_manufacturer",
        body,
        "f.txt",
        0,
        {"FRA_arquus_manufacturer_FRA_arquus_griffon_vbmr"},
    )
    assert not v._issues

    v = _validator(tmp_path)
    v._check_trait_localisation("FRA_arquus_manufacturer", body, "f.txt", 0, set())
    assert v._issues[0].category == "trait-loc-missing"
    assert "name = FRA_arquus_griffon_vbmr" in v._issues[0].message


def test_initial_trait_name_without_loc_flagged(tmp_path):
    v = _validator(tmp_path)
    body = "initial_trait = {\n\tname = generic_infantry_equipment_organization\n}"
    v._check_trait_localisation("ARG_bersa_manufacturer", body, "f.txt", 0, set())
    assert [i.category for i in v._issues] == ["trait-loc-missing"]


def test_staged_english_localisation_scans_all_mios(tmp_path, monkeypatch):
    org_dir = tmp_path / V.ORG_DIR
    org_dir.mkdir(parents=True)
    (org_dir / "MD_TEST_organizations.txt").write_text(
        "TST_test_org = {\n"
        "\tallowed = { original_tag = TST }\n"
        "\ttrait = {\n"
        "\t\tname = TST_missing_trait\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    (loc_dir / "MD_mio_l_english.yml").write_text(
        'l_english:\n other:0 "Other"\n', encoding="utf-8-sig"
    )
    monkeypatch.setenv("MD_STAGED_FILES", "localisation/english/MD_mio_l_english.yml")

    v = V.Validator(str(tmp_path), staged_only=True)
    v.run_validations()

    assert [issue.category for issue in v._issues] == ["trait-loc-missing"]


def test_full_run_on_fixture_dir(tmp_path):
    org_dir = tmp_path / V.ORG_DIR
    org_dir.mkdir(parents=True)
    (org_dir / "MD_TEST_organizations.txt").write_text(
        "TST_bad_org = {\n"
        "\tallowed = { original_tag = GER }\n"
        "\tinitial_trait = {\n"
        "\t\tname = wrong_name\n"
        "\t}\n"
        "\tposition = { x = 12 y = 0 }\n"
        "\ton_complete = {\n"
        "\t}\n"
        "}\n"
        "\n"
        "generic_shared = {\n"
        "\tallowed = { always = no }\n"
        "}\n"
    )
    v = _validator(tmp_path)
    v.run_validations()
    assert sorted(i.category for i in v._issues) == [
        "initial-trait-name",
        "on-complete-empty",
        "org-allowed-tag",
        "trait-loc-missing",
        "trait-x-bounds",
    ]
    by_cat = {i.category: i for i in v._issues}
    assert "org-id-format" not in by_cat
    assert by_cat["org-allowed-tag"].severity == "error"
    assert by_cat["on-complete-empty"].severity == "error"
    assert by_cat["trait-x-bounds"].severity == "error"
    assert by_cat["initial-trait-name"].severity == "error"
    assert by_cat["trait-loc-missing"].severity == "error"


# ---- equipment_bonus dead-stat checks (issue #3044) ------------------------

_EQUIPMENT = """
equipments = {
\tAA_Equipment = {
\t\tis_archetype = yes
\t\treliability = 0.9
\t\tair_attack = 0.375
\t}
\tcnc_equipment_type = {
\t\tis_archetype = yes
\t\treliability = 0.9
\t\tmax_organisation = 0.2
\t}
\tcorvette = {
\t\tis_archetype = yes
\t\ttype = screen_ship
\t\treliability = 0.9
\t\tbuild_cost_ic = 900
\t}
}
"""


def _equipment_index(tmp_path):
    equipment_dir = tmp_path / "common" / "units" / "equipment"
    equipment_dir.mkdir(parents=True, exist_ok=True)
    (equipment_dir / "MD_test_equipment.txt").write_text(_EQUIPMENT, encoding="utf-8")
    return V.build_equipment_stat_index(str(tmp_path))


def _run_org_check(tmp_path, body, org_id="TST_org"):
    v = _validator(tmp_path)
    v._org_bodies = {org_id: body}
    v._check_org_trait_bonuses(org_id, body, "f.txt", 0, _equipment_index(tmp_path))
    return v


_MANPADS_ORG = (
    "\tequipment_type = {\n"
    "\t\tAA_Equipment\n"
    "\t}\n"
    "\ttrait = {\n"
    "\t\ttoken = TST_trait\n"
    "\t\tequipment_bonus = {\n"
    "\t\t\tmax_organisation = 0.10\n"
    "\t\t}\n"
    "\t}\n"
)


def test_bonus_on_stat_the_equipment_lacks_is_flagged(tmp_path):
    v = _run_org_check(tmp_path, _MANPADS_ORG)
    assert [i.category for i in v._issues] == ["mio-bonus-no-base-stat"]
    assert v._issues[0].severity == "warning"
    assert "max_organisation" in v._issues[0].message
    assert v._issues[0].line == 7


def test_bonus_on_declared_stat_passes(tmp_path):
    body = _MANPADS_ORG.replace("max_organisation = 0.10", "air_attack = 0.10")
    assert not _run_org_check(tmp_path, body)._issues


def test_limit_to_equipment_type_narrows_the_scope(tmp_path):
    # The org covers both, but the trait limits itself to the half that has no
    # max_organisation, so the bonus is fully dead rather than partial.
    body = (
        "\tequipment_type = {\n"
        "\t\tAA_Equipment\n"
        "\t\tcnc_equipment_type\n"
        "\t}\n"
        "\ttrait = {\n"
        "\t\tlimit_to_equipment_type = { AA_Equipment }\n"
        "\t\tequipment_bonus = { max_organisation = 0.10 }\n"
        "\t}\n"
    )
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-bonus-no-base-stat"]


def test_partial_coverage_is_its_own_category(tmp_path):
    body = (
        "\tequipment_type = {\n"
        "\t\tAA_Equipment\n"
        "\t\tcnc_equipment_type\n"
        "\t}\n"
        "\ttrait = {\n"
        "\t\tequipment_bonus = { max_organisation = 0.10 }\n"
        "\t}\n"
    )
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-bonus-partial-base-stat"]
    assert [i.severity for i in v._issues] == ["error"]
    assert "AA_Equipment" in v._issues[0].message
    assert "cnc_equipment_type" in v._issues[0].message


def test_initial_trait_partial_coverage_is_accepted(tmp_path):
    """An org has one initial_trait and cannot split it, and a limit narrowing
    it would restrict its production_bonus too, so a stat reaching only part of
    the roster is unfixable there and must not be reported."""
    body = (
        "\tequipment_type = {\n"
        "\t\tAA_Equipment\n"
        "\t\tcnc_equipment_type\n"
        "\t}\n"
        "\tinitial_trait = {\n"
        "\t\tequipment_bonus = { max_organisation = 0.10 }\n"
        "\t}\n"
    )
    assert _run_org_check(tmp_path, body)._issues == []


def test_initial_trait_still_reports_a_wholly_dead_bonus(tmp_path):
    """The exemption covers partial coverage only: a stat no equipment in the
    org declares is still a no-op the author can simply drop."""
    body = (
        "\tequipment_type = {\n"
        "\t\tAA_Equipment\n"
        "\t}\n"
        "\tinitial_trait = {\n"
        "\t\tequipment_bonus = { max_organisation = 0.10 }\n"
        "\t}\n"
    )
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-bonus-no-base-stat"]


def test_include_supplies_the_equipment_type(tmp_path):
    shared = "\tequipment_type = {\n\t\tAA_Equipment\n\t}\n"
    body = (
        "\tinclude = generic_shared\n"
        "\ttrait = {\n"
        "\t\tequipment_bonus = { max_organisation = 0.10 }\n"
        "\t}\n"
    )
    v = _validator(tmp_path)
    v._org_bodies = {"TST_org": body, "generic_shared": shared}
    v._check_org_trait_bonuses("TST_org", body, "f.txt", 0, _equipment_index(tmp_path))
    assert [i.category for i in v._issues] == ["mio-bonus-no-base-stat"]


def test_unresolvable_type_reports_itself_and_suppresses_the_bonus_check(tmp_path):
    body = (
        "\tequipment_type = {\n"
        "\t\thelicopter_equipment\n"
        "\t}\n"
        "\ttrait = {\n"
        "\t\tequipment_bonus = { max_organisation = 0.10 }\n"
        "\t}\n"
    )
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-equipment-type-unknown"]


def test_initial_trait_bonus_is_checked(tmp_path):
    body = (
        "\tequipment_type = { AA_Equipment }\n"
        "\tinitial_trait = {\n"
        "\t\tname = TST_org_trait\n"
        "\t\tequipment_bonus = { max_organisation = 0.05 }\n"
        "\t}\n"
    )
    assert [i.category for i in _run_org_check(tmp_path, body)._issues] == [
        "mio-bonus-no-base-stat"
    ]


def test_commented_out_bonus_is_ignored(tmp_path):
    body = (
        "\tequipment_type = { AA_Equipment }\n"
        "\ttrait = {\n"
        "\t\tequipment_bonus = {\n"
        "\t\t\t# max_organisation = 0.10\n"
        "\t\t\tair_attack = 0.05\n"
        "\t\t}\n"
        "\t}\n"
    )
    v = _validator(tmp_path)
    body = V.blank_comments(body)
    v._org_bodies = {"TST_org": body}
    v._check_org_trait_bonuses("TST_org", body, "f.txt", 0, _equipment_index(tmp_path))
    assert not v._issues


# ---- naval production_bonus checks (issue #3878) ---------------------------


def _production_org(equipment_type: str, bonus: str, limit: str = "") -> str:
    return (
        f"\tequipment_type = {{ {equipment_type} }}\n"
        "\ttrait = {\n"
        "\t\ttoken = TST_trait\n"
        f"{limit}"
        f"\t\tproduction_bonus = {{ {bonus} }}\n"
        "\t}\n"
    )


def test_efficiency_bonus_on_a_wholly_naval_scope_is_flagged(tmp_path):
    body = _production_org("corvette", "production_efficiency_gain_factor = 0.10")
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-production-bonus-naval"]
    assert v._issues[0].severity == "error"
    assert "corvette" in v._issues[0].message


def test_conversion_speed_on_a_wholly_naval_scope_is_flagged(tmp_path):
    body = _production_org("corvette", "production_conversion_speed_factor = 0.15")
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-production-bonus-naval"]


def test_type_category_token_counts_as_naval(tmp_path):
    """`equipment_type` accepts a type category, which owns no `types` entry of
    its own and so only resolves through the category set."""
    body = _production_org("screen_ship", "production_efficiency_cap_factor = 0.08")
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-production-bonus-naval"]


def test_efficiency_bonus_on_a_land_scope_passes(tmp_path):
    body = _production_org("AA_Equipment", "production_efficiency_gain_factor = 0.10")
    assert not _run_org_check(tmp_path, body)._issues


def test_live_production_keys_on_a_naval_scope_pass(tmp_path):
    body = _production_org(
        "corvette",
        "production_capacity_factor = 0.10 production_cost_factor = -0.05",
    )
    assert not _run_org_check(tmp_path, body)._issues


def test_mixed_naval_scope_is_its_own_category(tmp_path):
    body = _production_org(
        "AA_Equipment corvette", "production_efficiency_gain_factor = 0.10"
    )
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-production-bonus-partial-naval"]
    assert v._issues[0].severity == "warning"
    assert "corvette" in v._issues[0].message
    assert "AA_Equipment" in v._issues[0].message


def test_limit_to_equipment_type_narrows_a_mixed_org_onto_ships(tmp_path):
    body = _production_org(
        "AA_Equipment corvette",
        "production_efficiency_gain_factor = 0.10",
        limit="\t\tlimit_to_equipment_type = { corvette }\n",
    )
    v = _run_org_check(tmp_path, body)
    assert [i.category for i in v._issues] == ["mio-production-bonus-naval"]


def test_nested_policy_form_checks_each_archetype_separately(tmp_path):
    text = (
        "mio_policy_test = {\n"
        "\tequipment_bonus = {\n"
        "\t\tAA_Equipment = {\n"
        "\t\t\tmax_organisation = 0.03\n"
        "\t\t}\n"
        "\t\tcnc_equipment_type = {\n"
        "\t\t\tmax_organisation = 0.03\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v = _validator(tmp_path)
    v._check_nested_equipment_bonus(text, "p.txt", _equipment_index(tmp_path))
    assert [i.category for i in v._issues] == ["mio-bonus-no-base-stat"]
    assert "AA_Equipment" in v._issues[0].message


def test_type_and_child_sharing_a_stat_is_flagged(tmp_path):
    equipment_dir = tmp_path / "common" / "units" / "equipment"
    equipment_dir.mkdir(parents=True, exist_ok=True)
    (equipment_dir / "MD_ships.txt").write_text(
        "equipments = {\n"
        "\thelicopter_operator = {\n"
        "\t\tis_archetype = yes\n"
        "\t\ttype = carrier\n"
        "\t\tbuild_cost_ic = 28000\n"
        "\t}\n"
        "\tcarrier = {\n"
        "\t\tis_archetype = yes\n"
        "\t\ttype = carrier\n"
        "\t\tbuild_cost_ic = 40000\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    text = (
        "mio_policy_test = {\n"
        "\tequipment_bonus = {\n"
        "\t\tcarrier = {\n"
        "\t\t\tbuild_cost_ic = -0.25\n"
        "\t\t}\n"
        "\t\thelicopter_operator = {\n"
        "\t\t\tbuild_cost_ic = -0.25\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v = _validator(tmp_path)
    v._check_nested_equipment_bonus(
        text, "p.txt", V.build_equipment_stat_index(str(tmp_path))
    )
    assert [i.category for i in v._issues] == ["bonus-type-archetype-stack"]
    assert v._issues[0].severity == "error"
    assert "helicopter_operator" in v._issues[0].message
    assert "carrier" in v._issues[0].message


def test_production_keys_are_not_equipment_stats(tmp_path):
    text = (
        "mio_policy_test = {\n"
        "\tequipment_bonus = {\n"
        "\t\tAA_Equipment = {\n"
        "\t\t\tproduction_cost_factor = -0.1\n"
        "\t\t\tproduction_efficiency_cap_factor = 0.05\n"
        "\t\t\tinstant = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v = _validator(tmp_path)
    v._check_nested_equipment_bonus(text, "p.txt", _equipment_index(tmp_path))
    assert not v._issues


# ---- mio: reference reachability (issue #3049) -----------------------------

_REFERENCE_ORGS = """\
ENG_lockheed_martin_manufacturer = {
\tallowed = { original_tag = ENG }
}

GRE_eas_materiel_manufacturer = {
\tallowed = { original_tag = GRE }
}

CHI_norinco_manufacturer = {
\tallowed = { OR = { original_tag = CHI original_tag = HKG } }
}

SOV_uralvagonzavod_tank_manufacturer = {
\tallowed = { original_tag = SOV }
}

GENERIC_open_organization = {
\tallowed = { always = yes }
}

USA_boeing_aircraft_manufacturer = {
\tallowed = { is_usa_or_breakaway = yes }
}
"""

_REFERENCE_TAGS = (
    "ENG = { }\nGRE = { }\nCHI = { }\nHKG = { }\nSOV = { }\nNKO = { }\n"
    "USA = { }\nTEX = { }\n"
)

_REFERENCE_TRIGGERS = """\
is_usa_or_breakaway = {
\tOR = {
\t\toriginal_tag = USA
\t\toriginal_tag = TEX
\t}
}
"""


def _reference_validator(tmp_path):
    org_dir = tmp_path / V.ORG_DIR
    org_dir.mkdir(parents=True)
    (org_dir / "MD_TEST_organizations.txt").write_text(
        _REFERENCE_ORGS, encoding="utf-8"
    )
    tag_dir = tmp_path / V.COUNTRY_TAG_DIR
    tag_dir.mkdir(parents=True)
    (tag_dir / "00_countries.txt").write_text(_REFERENCE_TAGS, encoding="utf-8")
    trigger_dir = tmp_path / V.SCRIPTED_TRIGGER_DIR
    trigger_dir.mkdir(parents=True)
    (trigger_dir / "99_USA_scripted_triggers.txt").write_text(
        _REFERENCE_TRIGGERS, encoding="utf-8"
    )
    return _validator(tmp_path)


def _focus(focus_id: str, body: str, available: str = "") -> str:
    available = f"\t\tavailable = {{ {available} }}\n" if available else ""
    return (
        "focus_tree = {\n"
        "\tfocus = {\n"
        f"\t\tid = {focus_id}\n"
        f"{available}"
        "\t\tcompletion_reward = {\n"
        f"{body}"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def test_unknown_mio_reference_flagged(tmp_path):
    v = _reference_validator(tmp_path)
    text = _focus("GRE_test", "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturr\n")
    v._check_mio_references(text, "common/national_focus/05_greece.txt")
    assert [i.category for i in v._issues] == ["mio-reference-unknown"]
    assert v._issues[0].severity == "error"


def test_cross_tag_design_team_flagged(tmp_path):
    v = _reference_validator(tmp_path)
    text = _focus(
        "GRE_m270_mlrs", "\t\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n"
    )
    v._check_mio_references(text, "common/national_focus/05_greece.txt")
    assert [i.category for i in v._issues] == ["mio-reference-wrong-tag"]
    assert "GRE scope" in v._issues[0].message


def test_same_tag_design_team_passes(tmp_path):
    v = _reference_validator(tmp_path)
    text = _focus(
        "GRE_m270_mlrs", "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturer\n"
    )
    v._check_mio_references(text, "common/national_focus/05_greece.txt")
    assert not v._issues


def test_multi_tag_allowed_block_passes(tmp_path):
    """The `allowed = { OR = { ... } }` orgs need balanced-brace parsing."""
    v = _reference_validator(tmp_path)
    text = _focus("HKG_test", "\t\t\tdesign_team = mio:CHI_norinco_manufacturer\n")
    v._check_mio_references(text, "common/national_focus/05_china.txt")
    assert not v._issues


def test_scripted_trigger_allowed_block_resolves_its_tags(tmp_path):
    """`allowed = { is_usa_or_breakaway = yes }` reaches every tag the trigger names."""
    v = _reference_validator(tmp_path)
    text = "\tcreate_equipment_variant = {\n\t\tdesign_team = mio:USA_boeing_aircraft_manufacturer\n\t}\n"
    v._check_mio_references(text, "history/countries/TEX - Texas.txt")
    assert not v._issues
    v._check_mio_references(text, "history/countries/GRE - Greece.txt")
    assert [i.category for i in v._issues] == ["mio-reference-wrong-tag"]


def test_scripted_trigger_allowed_block_pins_the_tag(tmp_path):
    v = _reference_validator(tmp_path)
    body = "\tallowed = { is_usa_or_breakaway = yes }\n"
    v._check_allowed("USA_boeing_aircraft_manufacturer", body, "f.txt", 0)
    assert not v._issues
    v._check_allowed("GRE_eas_materiel_manufacturer", body, "f.txt", 0)
    assert [i.category for i in v._issues] == ["org-allowed-tag"]


def test_explicit_country_scope_wins_over_focus_owner(tmp_path):
    v = _reference_validator(tmp_path)
    text = _focus(
        "CHI_NKO_labor_export",
        "\t\t\tCHI = {\n"
        "\t\t\t\tmio:CHI_norinco_manufacturer = {\n"
        "\t\t\t\t\tunlock_mio_trait_tooltip = CHI_nko_juche_production\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n",
        available="original_tag = NKO",
    )
    v._check_mio_references(
        text, "common/national_focus/03_china_north_korea_joint.txt"
    )
    assert not v._issues


def test_joint_focus_member_scope_passes(tmp_path):
    """completion_reward_joint_member runs as the other participant, so every
    tag the focus block names counts as reachable."""
    v = _reference_validator(tmp_path)
    text = (
        "joint_focus = {\n"
        "\tid = CHI_SOV_defense_industrial\n"
        "\tjoint_trigger = {\n"
        "\t\tOR = {\n"
        "\t\t\toriginal_tag = CHI\n"
        "\t\t\toriginal_tag = SOV\n"
        "\t\t}\n"
        "\t}\n"
        "\tavailable = { original_tag = CHI }\n"
        "\tcompletion_reward_joint_member = {\n"
        "\t\tmio:SOV_uralvagonzavod_tank_manufacturer = {\n"
        "\t\t\tunlock_mio_trait_tooltip = SOV_chi_rare_earth_supply\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v._check_mio_references(text, "common/national_focus/03_china_russia_joint.txt")
    assert not v._issues


def test_history_filename_supplies_the_tag(tmp_path):
    v = _reference_validator(tmp_path)
    text = "\tset_variant_name = {\n\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n\t}\n"
    v._check_mio_references(text, "history/countries/GRE - Greece.txt")
    assert [i.category for i in v._issues] == ["mio-reference-wrong-tag"]


def test_event_option_scope_is_not_guessed(tmp_path):
    """An event's ROOT is whoever fired it, so only existence is checked."""
    v = _reference_validator(tmp_path)
    text = (
        "country_event = {\n"
        "\tid = iranian_focus.117\n"
        "\toption = {\n"
        "\t\tcreate_equipment_variant = {\n"
        "\t\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v._check_mio_references(text, "events/Iran.txt")
    assert not v._issues


def test_commented_out_reference_is_ignored(tmp_path):
    v = _reference_validator(tmp_path)
    raw = _focus(
        "GRE_test",
        "\t\t\t# design_team = mio:SWE_does_not_exist_manufacturer\n",
    )
    v._check_mio_references(
        V.blank_comments(raw), "common/national_focus/05_greece.txt"
    )
    assert not v._issues


def test_org_open_to_every_tag_is_reachable_anywhere(tmp_path):
    v = _reference_validator(tmp_path)
    text = _focus("GRE_test", "\t\t\tdesign_team = mio:GENERIC_open_organization\n")
    v._check_mio_references(text, "common/national_focus/05_greece.txt")
    assert not v._issues


def test_reference_outside_every_focus_block_is_not_scoped(tmp_path):
    v = _reference_validator(tmp_path)
    text = (
        "focus_tree = {\n"
        "\tid = greece\n"
        "\tmio:ENG_lockheed_martin_manufacturer = { }\n"
        "\tfocus = {\n"
        "\t\tid = GRE_other\n"
        "\t}\n"
        "}\n"
    )
    v._check_mio_references(text, "common/national_focus/05_greece.txt")
    assert not v._issues


def test_focus_without_an_id_falls_back_to_the_tags_it_names(tmp_path):
    v = _reference_validator(tmp_path)
    text = (
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tavailable = { original_tag = GRE }\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v._check_mio_references(text, "common/national_focus/05_greece.txt")
    assert [i.category for i in v._issues] == ["mio-reference-wrong-tag"]


def test_focus_id_prefix_that_is_not_a_tag_is_ignored(tmp_path):
    v = _reference_validator(tmp_path)
    text = _focus(
        "generic_industrial_base",
        "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturer\n",
        available="original_tag = GRE",
    )
    v._check_mio_references(text, "common/national_focus/05_greece.txt")
    assert not v._issues


def test_history_filename_without_a_known_tag_is_not_scoped(tmp_path):
    v = _reference_validator(tmp_path)
    text = "\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n"
    v._check_mio_references(text, "history/countries/ZZZ - Nowhere.txt")
    assert not v._issues


def test_org_index_is_built_once_and_survives_an_unreadable_file(tmp_path):
    v = _reference_validator(tmp_path)
    (tmp_path / V.ORG_DIR / "broken.txt").mkdir()

    first = v._org_allowed_tags()

    assert first["GRE_eas_materiel_manufacturer"] == frozenset({"GRE"})
    assert v._org_allowed_tags() is first


def test_country_tags_are_built_once_and_survive_an_unreadable_file(tmp_path):
    v = _reference_validator(tmp_path)
    (tmp_path / V.COUNTRY_TAG_DIR / "broken.txt").mkdir()

    first = v._country_tags()

    assert "GRE" in first
    assert v._country_tags() is first


# ---- parser and check edge cases -------------------------------------------


def test_named_sub_blocks_walks_nested_bodies_to_the_end():
    body = "AA_Equipment = { limit = { always = yes } max_organisation = 0.03 }"
    assert [name for name, _start, _inner in V._named_sub_blocks(body)] == [
        "AA_Equipment"
    ]


def test_allowed_check_skips_an_id_with_no_tag_prefix(tmp_path):
    v = _validator(tmp_path)
    v._check_allowed(
        "norinco_manufacturer", "\tallowed = { always = yes }\n", "f.txt", 0
    )
    assert not v._issues


def test_header_block_without_a_text_key_is_ignored(tmp_path):
    v = _validator(tmp_path)
    v._check_header_text(
        "GRE_org", "tree_header_text = {\n\tx = 1\n}", "f.txt", 0, set()
    )
    assert not v._issues


def test_trait_without_name_or_token_is_ignored(tmp_path):
    v = _validator(tmp_path)
    v._check_trait_localisation(
        "GRE_org", "trait = {\n\tposition = { x = 1 }\n}", "f.txt", 0, set()
    )
    assert not v._issues


def test_include_pointing_at_an_unknown_org_supplies_nothing(tmp_path):
    body = (
        "\tinclude = generic_missing\n"
        "\ttrait = {\n"
        "\t\tequipment_bonus = { max_organisation = 0.10 }\n"
        "\t}\n"
    )
    v = _validator(tmp_path)
    v._org_bodies = {"TST_org": body}
    v._check_org_trait_bonuses("TST_org", body, "f.txt", 0, _equipment_index(tmp_path))
    assert not v._issues


def test_nested_bonus_on_an_unknown_archetype_reports_only_the_type(tmp_path):
    text = (
        "mio_policy_test = {\n"
        "\tequipment_bonus = {\n"
        "\t\tnot_an_archetype = {\n"
        "\t\t\tmax_organisation = 0.03\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v = _validator(tmp_path)
    v._check_nested_equipment_bonus(text, "p.txt", _equipment_index(tmp_path))
    assert [i.category for i in v._issues] == ["mio-equipment-type-unknown"]


# ---- full-repo runs --------------------------------------------------------

_RUN_ORGS = """\
TST_test_org = {
\tallowed = { original_tag = TST }
\tequipment_type = {
\t\tAA_Equipment
\t}
\tinitial_trait = {
\t\tname = TST_test_org_trait
\t}
\ttrait = {
\t\tname = TST_test_org_dead_trait
\t\tequipment_bonus = { max_organisation = 0.10 }
\t}
}
"""

_RUN_POLICY = """\
mio_policy_test = {
\tequipment_bonus = {
\t\tAA_Equipment = {
\t\t\tmax_organisation = 0.03
\t\t}
\t}
}
"""

_RUN_COMPANY_TRAIT = """\
TST_company_trait = {
\tequipment_bonus = {
\t\tAA_Equipment = {
\t\t\treliability = 0.05
\t\t}
\t}
}
"""

_RUN_FOCUS = """\
focus_tree = {
\tfocus = {
\t\tid = TST_industry
\t\tcompletion_reward = {
\t\t\tdesign_team = mio:TST_missing_org
\t\t}
\t}
}
"""


def _run_repo(tmp_path, write_path):
    write_path(tmp_path, f"{V.ORG_DIR}/MD_TEST_organizations.txt", _RUN_ORGS)
    write_path(tmp_path, f"{V.POLICY_DIR}/MD_TEST_policies.txt", _RUN_POLICY)
    write_path(tmp_path, V.COMPANY_TRAIT_FILE, _RUN_COMPANY_TRAIT)
    write_path(tmp_path, f"{V.COUNTRY_TAG_DIR}/00_countries.txt", "TST = { }\n")
    write_path(tmp_path, "common/national_focus/05_test.txt", _RUN_FOCUS)
    write_path(
        tmp_path,
        "localisation/english/MD_mio_l_english.yml",
        'l_english:\n TST_test_org_trait:0 "Trait"\n'
        ' TST_test_org_dead_trait:0 "Dead"\n',
    )
    _equipment_index(tmp_path)
    return tmp_path


def test_full_run_covers_orgs_policies_and_references(tmp_path, write_path):
    _run_repo(tmp_path, write_path)
    v = _validator(tmp_path)

    v.run_validations()

    categories = sorted(i.category for i in v._issues)
    assert categories == [
        "mio-bonus-no-base-stat",
        "mio-bonus-no-base-stat",
        "mio-reference-unknown",
    ]
    assert {i.file for i in v._issues} == {
        f"{V.ORG_DIR}/MD_TEST_organizations.txt",
        f"{V.POLICY_DIR}/MD_TEST_policies.txt",
        "common/national_focus/05_test.txt",
    }


_COVERAGE_EQUIPMENT = """
equipments = {
\tsmall_plane_airframe = { is_archetype = yes }
\tsmall_plane_airframe_1 = { archetype = small_plane_airframe }
\tmedium_plane_airframe = {
\t\tis_archetype = yes
\t\ttype = { test_fighter }
\t}
\tmedium_plane_airframe_1 = { archetype = medium_plane_airframe }
}
duplicate_archetypes = {
\tsmall_plane_cas_airframe = { archetype = small_plane_airframe }
}
"""

_COVERAGE_GROUPS = """
mio_cat_test_medium = {
\tequipment_type = {
\t\tmedium_plane_airframe
\t}
}
"""

_COVERAGE_FILE = "history/countries/TST - Test.txt"


def _coverage_issues(tmp_path, write_path, org_types, variant):
    """Issues for one variant written against a TST_org listing *org_types*."""
    write_path(
        tmp_path,
        f"{V.ORG_DIR}/MD_TST_organizations.txt",
        f"TST_org = {{\n\tequipment_type = {{ {org_types} }}\n}}\n",
    )
    write_path(tmp_path, "common/units/equipment/MD_test.txt", _COVERAGE_EQUIPMENT)
    write_path(tmp_path, "common/equipment_groups/mio_test.txt", _COVERAGE_GROUPS)
    v = _validator(tmp_path)
    v._org_bodies = v._load_org_bodies()
    text = "create_equipment_variant = {\n" f"{variant}" "}\n"
    v._check_design_team_coverage(
        text, _COVERAGE_FILE, V.build_equipment_stat_index(str(tmp_path))
    )
    return v._issues


def _team(variant_type, team="\tdesign_team = mio:TST_org\n"):
    return f"\ttype = {variant_type}\n{team}"


def test_design_team_type_outside_equipment_type_is_flagged(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path, write_path, "small_plane_airframe", _team("medium_plane_airframe_1")
    )
    assert [(i.category, i.severity, i.line) for i in issues] == [
        ("mio-design-team-type-uncovered", "warning", 3)
    ]
    assert "medium_plane_airframe" in issues[0].message


def test_design_team_type_listed_directly_passes(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path, write_path, "medium_plane_airframe", _team("medium_plane_airframe")
    )
    assert not issues


def test_design_team_type_covered_through_mio_cat_group_passes(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path, write_path, "mio_cat_test_medium", _team("medium_plane_airframe_1")
    )
    assert not issues


def test_design_team_numbered_type_listed_directly_passes(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path,
        write_path,
        "medium_plane_airframe_1",
        _team("medium_plane_airframe_1"),
    )
    assert not issues


def test_design_team_type_covered_through_category_passes(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path, write_path, "test_fighter", _team("medium_plane_airframe_1")
    )
    assert not issues


def test_design_team_numbered_type_matches_its_archetype(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path, write_path, "small_plane_airframe", _team("small_plane_airframe_1")
    )
    assert not issues


def test_design_team_clone_is_its_own_archetype(tmp_path, write_path):
    org_types = "small_plane_airframe"
    issues = _coverage_issues(
        tmp_path, write_path, org_types, _team("small_plane_cas_airframe_1")
    )
    assert [i.category for i in issues] == ["mio-design-team-type-uncovered"]
    assert "small_plane_cas_airframe" in issues[0].message


def test_variant_without_design_team_is_not_flagged(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path,
        write_path,
        "small_plane_airframe",
        _team("medium_plane_airframe_1", ""),
    )
    assert not issues


def test_design_team_on_undefined_vanilla_type_is_skipped(tmp_path, write_path):
    issues = _coverage_issues(
        tmp_path, write_path, "small_plane_airframe", _team("fighter_equipment_1")
    )
    assert not issues


def test_unreadable_and_undecodable_files_do_not_stop_the_run(tmp_path, write_path):
    _run_repo(tmp_path, write_path)
    (tmp_path / V.ORG_DIR / "broken.txt").mkdir()
    (tmp_path / V.POLICY_DIR / "broken.txt").mkdir()
    (tmp_path / "common" / "decisions").mkdir(parents=True)
    (tmp_path / "common" / "decisions" / "broken.txt").mkdir()
    (tmp_path / "common" / "decisions" / "latin1.txt").write_bytes(
        b"design_team = mio:TST_test_org # caf\xe9\n"
    )
    v = _validator(tmp_path)

    v.run_validations()

    assert sorted(i.category for i in v._issues) == [
        "mio-bonus-no-base-stat",
        "mio-bonus-no-base-stat",
        "mio-reference-unknown",
    ]


def test_a_staged_equipment_edit_rescans_every_org(tmp_path, write_path, monkeypatch):
    _run_repo(tmp_path, write_path)
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/units/equipment/MD_test_equipment.txt"
    )
    v = V.Validator(str(tmp_path), staged_only=True)

    v.run_validations()

    assert sorted(i.category for i in v._issues) == [
        "mio-bonus-no-base-stat",
        "mio-bonus-no-base-stat",
    ]


def test_a_staged_scripted_trigger_rescans_orgs_and_references(
    tmp_path, write_path, monkeypatch
):
    orgs = _REFERENCE_ORGS.replace(
        "GRE_eas_materiel_manufacturer = {\n\tallowed = { original_tag = GRE }",
        "GRE_eas_materiel_manufacturer = {\n\tallowed = { is_usa_or_breakaway = yes }",
    )
    write_path(tmp_path, f"{V.ORG_DIR}/MD_TEST_organizations.txt", orgs)
    write_path(
        tmp_path,
        f"{V.COUNTRY_TAG_DIR}/00_countries.txt",
        _REFERENCE_TAGS,
    )
    write_path(
        tmp_path,
        f"{V.SCRIPTED_TRIGGER_DIR}/99_USA_scripted_triggers.txt",
        _REFERENCE_TRIGGERS,
    )
    write_path(
        tmp_path,
        "common/national_focus/05_greece.txt",
        _focus(
            "GRE_test",
            "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturer\n",
        ),
    )
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/scripted_triggers/99_USA_scripted_triggers.txt"
    )
    v = V.Validator(str(tmp_path), staged_only=True)

    v.run_validations()

    assert sorted(i.category for i in v._issues) == [
        "mio-reference-wrong-tag",
        "org-allowed-tag",
    ]


def test_staged_run_with_no_mio_input_skips(tmp_path, write_path, monkeypatch):
    _run_repo(tmp_path, write_path)
    write_path(tmp_path, "interface/unrelated.txt", "guiTypes = { }\n")
    monkeypatch.setenv("MD_STAGED_FILES", "interface/unrelated.txt")
    v = V.Validator(str(tmp_path), staged_only=True)

    v.run_validations()

    assert v._issues == []
    assert any("No staged MIO files" in line for line in v.output_lines)


def test_staged_interface_edit_rescans_all_mios(tmp_path, write_path, monkeypatch):
    _run_repo(tmp_path, write_path)
    sprite = tmp_path / "interface" / "mio.gfx"
    sprite.parent.mkdir(parents=True)
    sprite.write_text("spriteType = { name = GFX_test }\n", encoding="utf-8")
    monkeypatch.setenv("MD_STAGED_FILES", "interface/mio.gfx")

    v = V.Validator(str(tmp_path), staged_only=True)

    assert v._org_files()


def test_staged_sprite_deletion_rescans_all_mios(tmp_path, write_path):
    _run_repo(tmp_path, write_path)
    sprite = tmp_path / "interface" / "mio.gfx"
    sprite.parent.mkdir(parents=True)
    sprite.write_text("spriteType = { name = GFX_test }\n", encoding="utf-8")
    sprite.unlink()
    v = V.Validator(str(tmp_path))
    v.staged_only = True
    v.staged_files = [sprite]

    assert v._org_files()


def _sprite_set(*names):
    return frozenset(names) | {f"GFX_pad_{i}" for i in range(V._MIN_SPRITE_INDEX)}


def test_icon_that_is_not_a_gfx_name_is_flagged(tmp_path):
    v = _validator(tmp_path)
    v._sprites = _sprite_set()

    v._check_icons("\ticon = x # TODO: needs a company logo", "orgs.txt")

    assert [i.category for i in v._issues] == ["mio-icon-not-gfx"]
    assert v._issues[0].line == 1


def test_unresolved_gfx_icon_is_a_warning(tmp_path):
    v = _validator(tmp_path)
    v._sprites = _sprite_set("GFX_idea_other_org")

    v._check_icons("\ticon = GFX_idea_ALG_seriana\n", "orgs.txt")

    assert [i.category for i in v._issues] == ["mio-icon-unresolved"]
    assert v._issues[0].severity == "warning"


def test_resolved_gfx_icon_is_clean(tmp_path):
    v = _validator(tmp_path)
    v._sprites = _sprite_set(
        "GFX_idea_ALG_khenchela_arms", "GFX_generic_mio_trait_icon_reliability"
    )

    v._check_icons(
        "\ticon = GFX_idea_ALG_khenchela_arms\n"
        "\ttrait = {\n\t\ticon = GFX_generic_mio_trait_icon_reliability\n\t}\n",
        "orgs.txt",
    )

    assert not v._issues


def test_small_sprite_index_skips_resolution(tmp_path):
    v = _validator(tmp_path)
    v._sprites = frozenset({"GFX_something"})

    v._check_icons("\ticon = GFX_idea_missing\n", "orgs.txt")

    assert not v._issues


def test_quoted_icon_value_is_checked(tmp_path):
    v = _validator(tmp_path)
    v._sprites = _sprite_set()

    v._check_icons('\ticon = "bare_token"\n', "orgs.txt")

    assert [i.category for i in v._issues] == ["mio-icon-not-gfx"]


def test_icon_scanner_ignores_quoted_assignments_and_accepts_punctuation(tmp_path):
    v = _validator(tmp_path)
    v._sprites = _sprite_set("GFX_company-logo")

    v._check_icons(
        '\tdesc = "icon = not_a_reference"\n'
        "\ticon = GFX_company-logo # comment icon = fake\n",
        "orgs.txt",
    )

    assert not v._issues


def test_icon_scanner_reports_empty_values(tmp_path):
    v = _validator(tmp_path)
    v._sprites = _sprite_set()

    v._check_icons("\ticon = {}\n", "orgs.txt")

    assert [i.category for i in v._issues] == ["mio-icon-not-gfx"]


def _geometry_trait(
    token, x=None, y=None, rel=None, parents=None, any_parents=None, mutual=None
):
    text = "\ttrait = {\n\t\ttoken = " + token + "\n"
    if parents:
        text += "\t\tall_parents = { " + " ".join(parents) + " }\n"
    if any_parents:
        text += "\t\tany_parent = { " + " ".join(any_parents) + " }\n"
    if mutual:
        text += "\t\tmutually_exclusive = { " + " ".join(mutual) + " }\n"
    if rel:
        text += "\t\trelative_position_id = " + rel + "\n"
    if x is not None or y is not None:
        text += "\t\tposition = { x = " + str(x) + " y = " + str(y) + " }\n"
    text += "\t}\n"
    return text


def _index(*bodies):
    index = {}
    for body in bodies:
        for token, trait in V._parse_org_traits(body).items():
            index.setdefault(token, trait)
    return index


def _geometry_validator(tmp_path, index):
    v = _validator(tmp_path)
    v._traits = index
    v._reported_mutex_rows = set()
    return v


def test_real_mio_relative_position_is_trait_level():
    body = (
        "\ttrait = {\n"
        "\t\ttoken = AST_bae_trait_hull_reinforcement\n"
        "\t\tall_parents = { AST_bae_trait_combat_system_integration }\n"
        "\t\trelative_position_id = AST_bae_trait_combat_system_integration\n"
        "\t\tposition = { x = 0 y = 1 }\n"
        "\t}\n"
    )

    trait = V._parse_org_traits(body)["AST_bae_trait_hull_reinforcement"]

    assert trait.rel == "AST_bae_trait_combat_system_integration"
    assert (trait.x, trait.y) == (0, 1)


def test_nested_relative_position_is_not_a_trait_anchor():
    body = (
        "\ttrait = {\n"
        "\t\ttoken = TST_nested_relative\n"
        "\t\tposition = { x = 0 y = 1 relative_position_id = wrong }\n"
        "\t}\n"
    )

    trait = V._parse_org_traits(body)["TST_nested_relative"]

    assert trait.rel is None


def test_child_below_parent_is_clean(tmp_path):
    body = _geometry_trait("root", x=0, y=0) + _geometry_trait(
        "child", x=0, y=1, rel="root", parents=["root"]
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert not v._issues


def test_child_on_or_above_parent_row_is_flagged(tmp_path):
    body = _geometry_trait("root", x=0, y=0) + _geometry_trait(
        "child", x=0, y=0, rel="root", parents=["root"]
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert [(i.category, i.severity) for i in v._issues] == [
        ("trait-geometry-parent-row", "error")
    ]
    assert "`child`" in v._issues[0].message and "`root`" in v._issues[0].message

    v = _geometry_validator(tmp_path, _index(body))
    body_above = _geometry_trait("root", x=0, y=2) + _geometry_trait(
        "child", x=0, y=1, parents=["root"]
    )
    v._check_trait_geometry("TST_org", body_above, "orgs.txt", 0)
    assert [i.category for i in v._issues] == ["trait-geometry-parent-row"]


def test_relative_position_chain_resolves_across_orgs(tmp_path):
    other_org = _geometry_trait("cross_org_root", x=2, y=5)
    body = _geometry_trait("mid", x=0, y=1, rel="cross_org_root") + _geometry_trait(
        "leaf", x=0, y=1, rel="mid", parents=["mid"]
    )
    v = _geometry_validator(tmp_path, _index(body, other_org))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert not v._issues


def test_unresolvable_anchor_reports_nothing(tmp_path):
    body = _geometry_trait("orphan", x=0, y=1, rel="missing_anchor")
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert not v._issues


def test_position_anchor_cycle_reports_nothing(tmp_path):
    body = (
        _geometry_trait("a", x=0, y=1, rel="b")
        + _geometry_trait("b", x=0, y=1, rel="a")
        + _geometry_trait("child", x=0, y=1, rel="a", parents=["a"])
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert not v._issues


def test_mutually_exclusive_traits_on_different_rows_are_flagged(tmp_path):
    body = _geometry_trait("left", x=0, y=2, mutual=["right"]) + _geometry_trait(
        "right", x=1, y=3
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert [(i.category, i.severity) for i in v._issues] == [
        ("trait-geometry-mutex-row", "error")
    ]


def test_mutually_exclusive_traits_sharing_a_row_are_clean(tmp_path):
    body = _geometry_trait("left", x=0, y=2, mutual=["right"]) + _geometry_trait(
        "right", x=1, y=2
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert not v._issues


def test_all_parents_with_mutually_exclusive_parents_is_flagged(tmp_path):
    body = (
        _geometry_trait("left", x=0, y=0, mutual=["right"])
        + _geometry_trait("right", x=1, y=0)
        + _geometry_trait("child", x=0, y=1, parents=["left", "right"])
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert [(i.category, i.severity) for i in v._issues] == [
        ("trait-geometry-mutex-parents", "error")
    ]
    assert "any_parent" in v._issues[0].message


def test_any_parent_with_mutually_exclusive_parents_is_clean(tmp_path):
    body = (
        _geometry_trait("left", x=0, y=0, mutual=["right"])
        + _geometry_trait("right", x=1, y=0)
        + _geometry_trait("child", x=0, y=1, any_parents=["left", "right"])
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert not v._issues


def test_unknown_parent_or_mutex_tokens_report_nothing(tmp_path):
    body = _geometry_trait(
        "child",
        x=0,
        y=1,
        rel="no_such_anchor",
        parents=["ghost_parent"],
        mutual=["ghost_peer"],
    )
    v = _geometry_validator(tmp_path, _index(body))

    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)

    assert not v._issues


# ---- edge-case files through a full run ------------------------------------

_EDGE_TST = f"{V.ORG_DIR}/MD_TST_organizations.txt"
_EDGE_TSU = f"{V.ORG_DIR}/MD_TSU_organizations.txt"
_EDGE_FOCUS = "common/national_focus/05_edge.txt"

# Line 1 is an org, line 2 a comment full of check tokens, line 5 hides a brace
# and a `#` in a string, the trait nests three blocks deep, and the file ends
# without a newline on an org whose quoted `{` never closes.
_EDGE_TST_TEXT = (
    "TST_first = { allowed = { original_tag = TST } on_complete = { } }\n"
    "# TST_ghost = { trait = { token = TST_ghost_trait position = { x = 99 } }"
    " icon = bad mio:TST_ghost }\n"
    "TST_edge_org = {\n"
    "\tallowed = { original_tag = GER }\n"
    '\tdesc = "a {brace} and # hash"\n'
    "\ticon = edge_icon # icon = in_comment\n"
    "\ticon = GFX_missing_edge\n"
    "\ttrait = {\n"
    "\t\ttoken = TST_edge_trait\n"
    "\t\tposition = { x = 12 y = 0 }\n"
    "\t\ton_complete = {\n"
    "\t\t\tif = { limit = { always = yes } }\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
    'TST_last = { allowed = { original_tag = TST } desc = "{" trait = {'
    " token = TST_last_trait position = { x = 10 y = 0 } } }"
)

_EDGE_TSU_TEXT = (
    "TSU_crlf_org = {\r\n"
    "\tallowed = { original_tag = TSU }\r\n"
    "\ttrait = { token = TSU_crlf_trait position = { x = 11 y = 1 } }\r\n"
    "}\r\n"
)

# CRLF and read as bytes, so the `\r` stays in the scanned text.
_EDGE_FOCUS_TEXT = (
    "mio:TST_missing_first = { }\r\n"
    "focus_tree = {\r\n"
    "\tshared_focus = {\r\n"
    "\t\tid = TSU_shared # mio:TST_commented\r\n"
    '\t\tlog = "{ # mio:TST_in_string }"\r\n'
    "\t\tcompletion_reward = {\r\n"
    "\t\t\tdesign_team = mio:TST_edge_org\r\n"
    "\t\t\tTST = { if = { limit = { always = yes } mio:TSU_crlf_org = { } } }\r\n"
    "\t\t}\r\n"
    "\t}\r\n"
    "}\r\n"
    "mio:TST_missing_last = { }"
)


def _unknown_reference(org_id, line):
    return (
        "mio-reference-unknown",
        _EDGE_FOCUS,
        line,
        f"mio:{org_id} matches no MIO definition in {V.ORG_DIR}/ "
        "(ids are case-sensitive)",
    )


def _nameless_trait(path, line, org_id, token):
    return (
        "trait-loc-missing",
        path,
        line,
        f"trait '{token}' has no name and no '{org_id}_{token}' localisation key;"
        f" add name = {token} plus a loc entry",
    )


def _x_bounds(path, line, x):
    return (
        "trait-x-bounds",
        path,
        line,
        f"trait position x = {x} must stay inside 0..9",
    )


_EDGE_FINDINGS = [
    (
        "mio-icon-not-gfx",
        _EDGE_TST,
        6,
        "icon = edge_icon is not a GFX_ sprite name; the engine renders a blank icon",
    ),
    (
        "mio-icon-unresolved",
        _EDGE_TST,
        7,
        "icon = GFX_missing_edge matches no spriteType in any interface/*.gfx "
        "(mod or vanilla)",
    ),
    (
        "on-complete-empty",
        _EDGE_TST,
        1,
        "on_complete is empty; add expenditure_for_mio_upgrade = yes or custom effects",
    ),
    (
        "org-allowed-tag",
        _EDGE_TST,
        3,
        "MIO TST_edge_org must pin its tag with allowed = { original_tag = TST }",
    ),
    _x_bounds(_EDGE_TST, 10, 12),
    _nameless_trait(_EDGE_TST, 8, "TST_edge_org", "TST_edge_trait"),
    _x_bounds(_EDGE_TST, 16, 10),
    _nameless_trait(_EDGE_TST, 16, "TST_last", "TST_last_trait"),
    _x_bounds(_EDGE_TSU, 3, 11),
    _nameless_trait(_EDGE_TSU, 3, "TSU_crlf_org", "TSU_crlf_trait"),
    _unknown_reference("TST_missing_first", 1),
    _unknown_reference("TST_in_string", 5),
    (
        "mio-reference-wrong-tag",
        _EDGE_FOCUS,
        7,
        "mio:TST_edge_org is allowed only for GER, so it does not resolve in TSU scope",
    ),
    (
        "mio-reference-wrong-tag",
        _EDGE_FOCUS,
        8,
        "mio:TSU_crlf_org is allowed only for TSU, so it does not resolve in TST scope",
    ),
    _unknown_reference("TST_missing_last", 12),
]


def _write_edge_repo(tmp_path, write_path):
    write_path(tmp_path, _EDGE_TST, _EDGE_TST_TEXT)
    write_path(tmp_path, _EDGE_TSU, _EDGE_TSU_TEXT)
    write_path(tmp_path, _EDGE_FOCUS, _EDGE_FOCUS_TEXT)
    write_path(
        tmp_path,
        f"{V.COUNTRY_TAG_DIR}/00_countries.txt",
        "TST = { }\nTSU = { }\nGER = { }\n",
    )


def _edge_rows(tmp_path, *, workers, sprites=None):
    """Findings of one full run and whether it forked the worker pool."""
    v = V.Validator(str(tmp_path), workers=workers)
    if sprites is not None:
        v._sprites = sprites
    try:
        v.run_validations()
        pooled = v._pool is not None
    finally:
        if v._pool is not None:
            v._pool.terminate()
            v._pool.join()
    return [(i.category, i.file, i.line, i.message) for i in v._issues], pooled


def test_edge_case_files_report_exact_findings_in_order(tmp_path, write_path):
    """Quoted braces and `#`, a token-filled comment, first and last lines, a
    missing final newline, CRLF org and reference files, and a `shared_focus`
    owner all keep their findings, lines and order."""
    _write_edge_repo(tmp_path, write_path)

    rows, _pooled = _edge_rows(tmp_path, workers=1, sprites=_sprite_set())

    assert rows == _EDGE_FINDINGS


def test_pooled_run_matches_the_in_process_run_in_order(
    tmp_path, write_path, monkeypatch
):
    """Twelve .gfx files cross the pool threshold for the sprite index, which
    also holds enough sprites to resolve icons."""
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    monkeypatch.setenv("MD_NO_CACHE", "1")
    _write_edge_repo(tmp_path, write_path)
    for index in range(12):
        sprites = "".join(
            f"\tspriteType = {{ name = GFX_pad_{index}_{n} }}\n" for n in range(100)
        )
        write_path(
            tmp_path,
            f"interface/pad_{index:02}.gfx",
            f"spriteTypes = {{\n{sprites}}}\n",
        )

    in_process, forked = _edge_rows(tmp_path, workers=1)
    pooled, pool_used = _edge_rows(tmp_path, workers=2)

    assert (forked, pool_used) == (False, True)
    assert pooled == in_process == _EDGE_FINDINGS


# ---- equivalence with the character walks these scans replaced -------------


def _walk_block_end(text, open_brace_end):
    depth = 1
    i = open_brace_end
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return i


def _walk_left_open_braces(text, pos):
    """Every `{` a leftward walk from *pos* meets at depth zero, innermost first."""
    found = []
    depth = 0
    for i in range(pos - 1, -1, -1):
        if text[i] == "}":
            depth += 1
        elif text[i] == "{":
            if depth:
                depth -= 1
            else:
                found.append(i)
    return found


def _random_texts(pieces, seed, count=400, longest=30):
    rng = random.Random(seed)
    for _ in range(count):
        yield "".join(rng.choice(pieces) for _ in range(rng.randint(0, longest)))


def test_block_end_matches_the_character_walk():
    fixed = ["", "}", "{", " { } }", "a { b { c { d } } } e", "{ { {", '" { "}']
    for text in [*fixed, *_random_texts('{}"# a\n', seed=1)]:
        for start in range(len(text) + 1):
            assert V._block_end(text, start) == _walk_block_end(text, start), (
                text,
                start,
            )


def test_open_braces_match_the_leftward_walk():
    fixed = ["} a { a } } a", "{ a { { a } a", "a } } { a"]
    for text in [*fixed, *_random_texts("{}a\n", seed=2)]:
        positions = [i for i, char in enumerate(text) if char == "a"]
        for pos, stack in zip(positions, V._open_braces(text, positions)):
            assert list(reversed(stack)) == _walk_left_open_braces(text, pos), (
                text,
                pos,
            )


def test_focus_spans_match_the_line_anchored_regex():
    pieces = [
        "focus = {",
        "shared_focus = {",
        "joint_focus={",
        "has_completed_focus = {",
        "focus_tree = {",
        "focus\n=\n{",
        "\t",
        " ",
        "\n",
        "}",
        "x",
    ]
    for text in _random_texts(pieces, seed=3):
        expected = [
            (m.start(), _walk_block_end(text, m.end()))
            for m in V.FOCUS_BLOCK_RE.finditer(text)
        ]
        assert V._focus_spans(text) == expected, text


_LOOKBEHIND_FORMS = [
    (V.ORIGINAL_TAG_RE, r"\boriginal_tag\s*=\s*([A-Z][A-Z0-9_]{1,7})\b"),
    (V._POSITION_BLOCK_RE, r"(?<![A-Za-z0-9_])position\s*=\s*\{([^{}]*)\}"),
    (
        V._RELATIVE_POSITION_RE,
        r"(?<![A-Za-z0-9_])relative_position_id\s*=\s*([A-Za-z0-9_]+)",
    ),
    (
        V._PARENT_BLOCK_RE,
        r"(?<![A-Za-z0-9_])(all_parents|any_parent|parent)\s*=\s*\{([^{}]*)\}",
    ),
    (
        V._MUTUALLY_EXCLUSIVE_RE,
        r"(?<![A-Za-z0-9_])mutually_exclusive\s*=\s*\{([^{}]*)\}",
    ),
    (V.HEADER_TEXT_RE, r'(?<![A-Za-z0-9_])text\s*=\s*("[^"]*"|[^\s{}]+)'),
    (V.NAME_RE, r"(?<![A-Za-z0-9_])name\s*=\s*([A-Za-z0-9_]+)"),
    (V.TOKEN_RE, r"(?<![A-Za-z0-9_])token\s*=\s*([A-Za-z0-9_]+)"),
    (V.MIO_REFERENCE_RE, r"(?<![A-Za-z0-9_])mio:([A-Za-z0-9_]+)"),
    (V.BLOCK_TAG_RE, r"(?<![A-Za-z0-9_])(?:original_)?tag\s*=\s*([A-Z][A-Z0-9]{2})\b"),
    (V.INCLUDE_RE, r"(?<![A-Za-z0-9_])include\s*=\s*([A-Za-z0-9_]+)"),
]

_PATTERN_PIECES = [
    *(
        "original_tag tag position relative_position_id all_parents any_parent"
        " parent mutually_exclusive text name token mio: include trait"
        " initial_trait GER x _ 1 é = { }"
    ).split(),
    " ",
    '"',
    "\n",
]


def test_literal_first_patterns_match_the_lookbehind_forms():
    # `\b` counts a non-ASCII letter as a word character; the others do not.
    fixed = ["éoriginal_tag = GER", "étoken = a", "xmio:a mio:b", "original_tag=GER"]
    for text in [*fixed, *_random_texts(_PATTERN_PIECES, seed=4)]:
        for new, old in _LOOKBEHIND_FORMS:
            got = [(m.span(), m.groups()) for m in new.finditer(text)]
            want = [(m.span(), m.groups()) for m in re.finditer(old, text)]
            assert got == want, (old, text)
        for keyword in ("trait", "initial_trait"):
            opener = re.compile(r"(?<![A-Za-z0-9_])" + keyword + r"\s*=\s*\{")
            want_blocks = [
                (m.start(), text[m.end() : _walk_block_end(text, m.end()) - 1])
                for m in opener.finditer(text)
            ]
            assert V._sub_blocks(text, keyword) == want_blocks, (keyword, text)


def test_relative_position_scan_matches_the_depth_walk():
    old = re.compile(r"(?<![A-Za-z0-9_])relative_position_id\s*=\s*([A-Za-z0-9_]+)")
    pieces = ["relative_position_id = a", "relative_position_id = b", "{", "}", " "]
    for text in _random_texts(pieces + ["_"], seed=5):
        body = "trait = { token = t " + text + " }"
        inner = V._sub_blocks(body, "trait")[0][1]
        depth = 0
        expected = None
        for index, char in enumerate(inner):
            if char in "{}":
                depth += 1 if char == "{" else -1
            elif depth == 0 and old.match(inner, index):
                expected = old.match(inner, index).group(1)
                break
        assert V._parse_org_traits(body)["t"].rel == expected, text


def test_icon_lines_match_counting_from_the_top():
    pieces = ["icon = a", 'icon="b c"', "xicon = d", "# icon = e", '"', "#"]
    for text in _random_texts(pieces + ["\n", "\r\n", "\x0c", " ", "{"], seed=6):
        expected = []
        offset = 0
        for raw_line in text.splitlines():
            code, _comment = V.split_code_and_comment(raw_line)
            for match in V.ICON_ASSIGNMENT_RE.finditer(V.blank_quoted_strings(code)):
                expected.append(text.count("\n", 0, offset + match.start()) + 1)
            offset += len(raw_line) + 1
        assert [line for _name, line in V._iter_icon_values(text)] == expected, text
