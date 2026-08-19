"""Tests for `validate_mios.py` (MIO organization definitions)."""

import validate_mios as V


def _validator(tmp_path):
    return V.Validator(str(tmp_path))


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
    assert by_cat["trait-x-bounds"].severity == "warning"
    assert by_cat["initial-trait-name"].severity == "warning"
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
    v._check_org_equipment_bonus(org_id, body, "f.txt", 0, _equipment_index(tmp_path))
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
    assert "AA_Equipment" in v._issues[0].message
    assert "cnc_equipment_type" in v._issues[0].message


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
    v._check_org_equipment_bonus(
        "TST_org", body, "f.txt", 0, _equipment_index(tmp_path)
    )
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
    v._check_org_equipment_bonus(
        "TST_org", body, "f.txt", 0, _equipment_index(tmp_path)
    )
    assert not v._issues


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
