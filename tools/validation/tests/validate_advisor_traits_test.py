"""Behavior tests for advisor trait slot checks."""

import pytest
from validate_advisor_traits import (
    Validator,
    collect_advisor_uses,
    parse_advisor_trait_slots,
)

ADVISOR_TRAITS = """leader_traits = {

\t### Military Minister Traits
\tstray_preamble_trait = {
\t\tsprite = 1
\t}

\t### Military High Command Traits ###
\tarmy_armored_2 = {
\t\tsprite = 8
\t}
\tair_naval_strike_1 = {
\t\tsprite = 1
\t}

### Army Chief Traits ###
\tarmy_chief_defensive_1 = {
\t\tsprite = 7
\t}

\t### Navy Chief Traits ###
\tnavy_chief_reform_2 = {
\t\tsprite = 3
\t}

\t### Air Chief Traits ###
\tair_chief_ground_support_1 = {
\t\tsprite = 2
\t}
\tair_air_superiority_1 = {
\t\tsprite = 1
\t}

\t### Intelligence Agency Advisor Traits ###
\thead_of_intelligence = {
\t\tsprite = 15
\t}
}
"""

COUNTRY_TRAITS = """leader_traits = {
\tENG_royalty_advisor_trait = {
\t\tsprite = 5
\t}
}
"""

UNIT_LEADER_TRAITS = """leader_traits = {
\tENG_royalty_trait = {
\t\ttype = land
\t}
}
"""


@pytest.fixture(autouse=True)
def _no_classification_floor(monkeypatch):
    monkeypatch.setattr("validate_advisor_traits._MIN_CLASSIFIED", 0)


def _write_fixture(tmp_path, characters: str):
    leader_dir = tmp_path / "common" / "country_leader"
    unit_dir = tmp_path / "common" / "unit_leader"
    char_dir = tmp_path / "common" / "characters"
    leader_dir.mkdir(parents=True)
    unit_dir.mkdir(parents=True)
    char_dir.mkdir(parents=True)
    (leader_dir / "01_military_advisor_traits.txt").write_text(
        ADVISOR_TRAITS, encoding="utf-8"
    )
    (leader_dir / "ENG_traits.txt").write_text(COUNTRY_TRAITS, encoding="utf-8")
    (unit_dir / "ENG_traits.txt").write_text(UNIT_LEADER_TRAITS, encoding="utf-8")
    (char_dir / "TAG.txt").write_text(characters, encoding="utf-8")


def _categories(validator):
    return {(issue.category, issue.message) for issue in validator._issues}


def test_parse_advisor_trait_slots_reads_section_headers():
    assert parse_advisor_trait_slots(ADVISOR_TRAITS) == {
        "army_armored_2": "high_command",
        "air_naval_strike_1": "high_command",
        "army_chief_defensive_1": "army_chief",
        "navy_chief_reform_2": "navy_chief",
        "air_chief_ground_support_1": "air_chief",
        "air_air_superiority_1": "air_chief",
    }


def test_parse_advisor_trait_slots_ignores_traits_outside_a_mapped_section():
    slots = parse_advisor_trait_slots(ADVISOR_TRAITS)

    # Before any header, and under a header with no trailing ###.
    assert "stray_preamble_trait" not in slots
    # Under a header that maps to no advisor slot.
    assert "head_of_intelligence" not in slots


def test_parse_advisor_trait_slots_handles_a_crlf_working_tree():
    assert parse_advisor_trait_slots(
        ADVISOR_TRAITS.replace("\n", "\r\n")
    ) == parse_advisor_trait_slots(ADVISOR_TRAITS)


def test_collect_advisor_uses_covers_both_trait_list_forms():
    content = (
        "advisor = {\n"
        "\tslot = army_chief\n"
        "\ttraits = { army_chief_defensive_1 army_armored_2 }\n"
        "}\n"
        "advisor = {\n"
        "\tslot = high_command\n"
        "\ttraits = {\n"
        "\t\tarmy_armored_2\n"
        "\t}\n"
        "}\n"
    )

    assert collect_advisor_uses(content) == [
        ("army_chief", "army_chief_defensive_1", 3),
        ("army_chief", "army_armored_2", 3),
        ("high_command", "army_armored_2", 7),
    ]


def test_collect_advisor_uses_covers_add_advisor_role():
    content = (
        "add_advisor_role = {\n"
        "\tadvisor = {\n"
        "\t\tslot = army_chief\n"
        "\t\ttraits = { army_chief_defensive_1 }\n"
        "\t}\n"
        "}\n"
    )

    assert collect_advisor_uses(content) == [
        ("army_chief", "army_chief_defensive_1", 4)
    ]


def test_validator_reports_slot_mismatch_in_both_directions(tmp_path):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_chief = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = army_chief\n"
        "\t\t\ttraits = { army_armored_2 }\n"
        "\t\t}\n"
        "\t}\n"
        "\tTAG_high_command = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = high_command\n"
        "\t\t\ttraits = { army_chief_defensive_1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    issues = _categories(validator)

    assert all(category == "advisor-trait-slot-mismatch" for category, _ in issues)
    assert any("army_armored_2" in message for _, message in issues)
    assert any("army_chief_defensive_1" in message for _, message in issues)


def test_validator_accepts_correct_pairings_including_the_air_families(tmp_path):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_air_chief = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = air_chief\n"
        "\t\t\ttraits = { air_air_superiority_1 }\n"
        "\t\t}\n"
        "\t}\n"
        "\tTAG_navy_chief = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = navy_chief\n"
        "\t\t\ttraits = { navy_chief_reform_2 }\n"
        "\t\t}\n"
        "\t}\n"
        "\tTAG_high_command = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = high_command\n"
        "\t\t\ttraits = { air_naval_strike_1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []


def test_validator_exempts_country_traits_and_unchecked_slots(tmp_path):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_bespoke = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = high_command\n"
        "\t\t\ttraits = { ENG_royalty_advisor_trait }\n"
        "\t\t}\n"
        "\t}\n"
        "\tTAG_political = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = political_advisor\n"
        "\t\t\ttraits = { army_chief_defensive_1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []


def test_validator_reports_undefined_and_unit_leader_traits(tmp_path):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_typo = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = air_chief\n"
        "\t\t\ttraits = { air_superiority_1 }\n"
        "\t\t}\n"
        "\t}\n"
        "\tTAG_general_trait = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = high_command\n"
        "\t\t\ttraits = { ENG_royalty_trait }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    issues = _categories(validator)

    assert (
        "undefined-advisor-trait",
        "slot air_chief uses trait 'air_superiority_1', which is not defined in "
        "common/country_leader/",
    ) in issues
    assert (
        "unit-leader-trait-on-advisor",
        "slot high_command uses 'ENG_royalty_trait', a common/unit_leader/ trait "
        "that does nothing on an advisor",
    ) in issues


def test_validator_skips_when_the_trait_pool_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("validate_advisor_traits._MIN_CLASSIFIED", 50)
    char_dir = tmp_path / "common" / "characters"
    char_dir.mkdir(parents=True)
    (char_dir / "TAG.txt").write_text(
        "advisor = {\n\tslot = army_chief\n\ttraits = { made_up }\n}\n",
        encoding="utf-8",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []


def test_validator_scans_all_uses_when_a_trait_definition_is_staged(
    tmp_path, monkeypatch
):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_chief = {\n"
        "\t\tadvisor = {\n"
        "\t\t\tslot = army_chief\n"
        "\t\t\ttraits = { army_armored_2 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/country_leader/01_military_advisor_traits.txt"
    )
    validator = Validator(str(tmp_path), use_colors=False, staged_only=True, workers=1)

    validator.run_validations()

    assert any(
        issue.category == "advisor-trait-slot-mismatch" for issue in validator._issues
    )
