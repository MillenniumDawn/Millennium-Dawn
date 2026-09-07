"""Behavior tests for unit leader trait role and advisor trait slot checks."""

import pytest
from validate_characters import (
    Validator,
    collect_advisor_uses,
    collect_trait_uses,
    missing_pool_files,
    parse_advisor_trait_slots,
    parse_trait_types,
)

TRAITS = """leader_traits = {
\tinfantry_officer = {
\t\ttype = land
\t\ttrait_type = personality_trait
\t}
\tbold = {
\t\ttype = navy
\t\ttrait_type = personality_trait
\t}
\tdefensive_doctrine = {
\t\ttype = field_marshal
\t}
\tpolitically_connected = {
\t\ttype = { land navy }
\t}
\told_guard = {
\t\ttype = all
\t}
}
"""

UNIT_LEADER_COUNTRY_TRAITS = """leader_traits = {
\tENG_royalty_trait = {
\t\ttype = land
\t}
}
"""

HIGH_COMMAND_TRAITS = """leader_traits = {
\tarmy_armored_2 = {
\t\tsprite = 8
\t}
\tair_naval_strike_1 = {
\t\tsprite = 1
\t}
\tTAG_bespoke_pool_trait = {
\t\tsprite = 4
\t}
}
"""

ARMY_CHIEF_TRAITS = """leader_traits = {
\tarmy_chief_defensive_1 = {
\t\tsprite = 7
\t}
\tarmy_chief_defensive_2 = {
\t\tsprite = 7
\t}
}
"""

NAVY_CHIEF_TRAITS = """leader_traits = {
\tnavy_chief_reform_2 = {
\t\tsprite = 3
\t}
}
"""

AIR_CHIEF_TRAITS = """leader_traits = {
\tair_chief_ground_support_1 = {
\t\tsprite = 2
\t}
\tair_air_superiority_1 = {
\t\tsprite = 1
\t}
}
"""

INTELLIGENCE_TRAITS = """leader_traits = {
\thead_of_intelligence = {
\t\tsprite = 15
\t}
}
"""

COUNTRY_TRAITS = """leader_traits = {
\tENG_royalty_advisor_trait = {
\t\tsprite = 5
\t}
\temerging_Communist-State = {
\t\trandom = no
\t}
}
"""

POOL_FILES = {
    "01_high_command_traits.txt": HIGH_COMMAND_TRAITS,
    "01_army_chief_traits.txt": ARMY_CHIEF_TRAITS,
    "01_navy_chief_traits.txt": NAVY_CHIEF_TRAITS,
    "01_air_chief_traits.txt": AIR_CHIEF_TRAITS,
}


def _write_fixture(tmp_path, characters: str, skip_pool_file: str = ""):
    trait_dir = tmp_path / "common" / "unit_leader"
    advisor_dir = tmp_path / "common" / "country_leader"
    char_dir = tmp_path / "common" / "characters"
    trait_dir.mkdir(parents=True)
    advisor_dir.mkdir(parents=True)
    char_dir.mkdir(parents=True)
    (trait_dir / "01_army_leader_traits.txt").write_text(TRAITS, encoding="utf-8")
    (trait_dir / "ENG_traits.txt").write_text(
        UNIT_LEADER_COUNTRY_TRAITS, encoding="utf-8"
    )
    for fname, content in POOL_FILES.items():
        if fname != skip_pool_file:
            (advisor_dir / fname).write_text(content, encoding="utf-8")
    (advisor_dir / "05_intelligence_agency_traits.txt").write_text(
        INTELLIGENCE_TRAITS, encoding="utf-8"
    )
    (advisor_dir / "ENG_traits.txt").write_text(COUNTRY_TRAITS, encoding="utf-8")
    (char_dir / "TAG.txt").write_text(characters, encoding="utf-8")


def _advisor(name: str, slot: str, traits: str) -> str:
    return (
        f"\t{name} = {{\n"
        "\t\tadvisor = {\n"
        f"\t\t\tslot = {slot}\n"
        f"\t\t\ttraits = {{ {traits} }}\n"
        "\t\t}\n"
        "\t}\n"
    )


def _characters(*blocks: str) -> str:
    return "characters = {\n" + "".join(blocks) + "}\n"


def _categories(validator):
    return {(issue.category, issue.message) for issue in validator._issues}


@pytest.fixture
def pool_dir(tmp_path):
    _write_fixture(tmp_path, _characters())
    return tmp_path


def test_parse_trait_types_reads_single_list_and_universal_types(tmp_path):
    _write_fixture(tmp_path, _characters())

    assert parse_trait_types(str(tmp_path)) == {
        "infantry_officer": {"land"},
        "bold": {"navy"},
        "defensive_doctrine": {"field_marshal"},
        "politically_connected": {"land", "navy"},
        "old_guard": {"all"},
        "ENG_royalty_trait": {"land"},
    }


def test_parse_advisor_trait_slots_maps_each_pool_file_to_its_slot(pool_dir):
    assert parse_advisor_trait_slots(str(pool_dir)) == {
        "army_armored_2": "high_command",
        "air_naval_strike_1": "high_command",
        "TAG_bespoke_pool_trait": "high_command",
        "army_chief_defensive_1": "army_chief",
        "army_chief_defensive_2": "army_chief",
        "navy_chief_reform_2": "navy_chief",
        "air_chief_ground_support_1": "air_chief",
        "air_air_superiority_1": "air_chief",
    }


def test_parse_advisor_trait_slots_ignores_files_outside_the_pool_map(pool_dir):
    slots = parse_advisor_trait_slots(str(pool_dir))

    assert "head_of_intelligence" not in slots
    assert "ENG_royalty_advisor_trait" not in slots


def test_missing_pool_files_lists_only_absent_files(tmp_path):
    _write_fixture(tmp_path, _characters(), skip_pool_file="01_navy_chief_traits.txt")

    assert missing_pool_files(str(tmp_path)) == ["01_navy_chief_traits.txt"]


def test_parse_advisor_trait_slots_skips_a_pool_file_that_is_absent(tmp_path):
    _write_fixture(tmp_path, _characters(), skip_pool_file="01_navy_chief_traits.txt")

    slots = parse_advisor_trait_slots(str(tmp_path))

    assert "navy_chief_reform_2" not in slots
    assert slots["army_chief_defensive_1"] == "army_chief"


def test_parse_trait_types_without_the_trait_dir(tmp_path):
    assert parse_trait_types(str(tmp_path)) == {}


def test_parse_trait_types_survives_an_unreadable_dir(tmp_path, monkeypatch):
    import validate_characters as VC

    (tmp_path / "common" / "unit_leader").mkdir(parents=True)
    monkeypatch.setattr(
        VC.os, "listdir", lambda path: (_ for _ in ()).throw(OSError("denied"))
    )

    assert parse_trait_types(str(tmp_path)) == {}


def test_parse_trait_types_reads_only_txt_and_typed_traits(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/unit_leader/01_traits.txt",
        "leader_traits = {\n"
        "\ttyped = {\n\t\ttype = navy\n\t}\n"
        "\tuntyped = {\n\t\ttrait_type = personality_trait\n\t}\n"
        "}\n",
    )
    write_path(
        tmp_path,
        "common/unit_leader/notes.md",
        "leader_traits = {\n\tignored = {\n\t\ttype = land\n\t}\n}\n",
    )

    assert parse_trait_types(str(tmp_path)) == {"typed": {"navy"}}


def test_collect_trait_uses_covers_roles_and_create_effects():
    content = (
        "corps_commander = {\n"
        "\ttraits = { bold }\n"
        "}\n"
        "create_navy_leader = {\n"
        "\ttraits = { infantry_officer old_guard }\n"
        "}\n"
        "create_operative_leader = {\n"
        "\ttraits = { bold }\n"
        "}\n"
    )

    assert collect_trait_uses(content) == [
        ("corps_commander", "bold", 2),
        ("navy_leader", "infantry_officer", 5),
        ("navy_leader", "old_guard", 5),
        ("operative", "bold", 8),
    ]


def test_collect_trait_uses_ignores_advisor_and_country_leader_traits():
    content = (
        "advisor = {\n"
        "\ttraits = { army_chief_defensive_2 }\n"
        "}\n"
        "country_leader = {\n"
        "\ttraits = { emerging_Conservative }\n"
        "}\n"
    )

    assert collect_trait_uses(content) == []


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


def test_collect_trait_uses_ignores_a_leader_block_without_traits():
    content = "corps_commander = {\n\tskill = 3\n}\n"

    assert collect_trait_uses(content) == []


def test_collect_advisor_uses_needs_both_a_slot_and_traits():
    content = (
        "advisor = {\n\ttraits = { army_chief_defensive_1 }\n}\n"
        "advisor = {\n\tslot = army_chief\n}\n"
    )

    assert collect_advisor_uses(content) == []


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


def test_validator_reports_branch_mismatch_and_undefined_trait(tmp_path):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_general = {\n"
        "\t\tcorps_commander = {\n"
        "\t\t\ttraits = { bold }\n"
        "\t\t}\n"
        "\t}\n"
        "\tTAG_admiral = {\n"
        "\t\tnavy_leader = {\n"
        "\t\t\ttraits = { made_up_trait }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    issues = {
        (issue.category, issue.severity, issue.message) for issue in validator._issues
    }

    assert any(
        category == "trait-role-mismatch" and "bold" in message
        for category, _, message in issues
    )
    assert any(
        category == "undefined-unit-leader-trait" and "made_up_trait" in message
        for category, _, message in issues
    )


def test_validator_reports_an_advisor_trait_on_a_unit_leader(tmp_path):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_general = {\n"
        "\t\tcorps_commander = {\n"
        "\t\t\ttraits = { army_chief_defensive_2 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert _categories(validator) == {
        (
            "advisor-trait-on-unit-leader",
            "corps_commander uses 'army_chief_defensive_2', a "
            "common/country_leader/ trait that does nothing on a unit leader",
        )
    }


def test_validator_scans_all_uses_when_a_trait_definition_is_staged(
    tmp_path, monkeypatch
):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_general = {\n"
        "\t\tcorps_commander = {\n"
        "\t\t\ttraits = { bold }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/unit_leader/01_army_leader_traits.txt"
    )
    validator = Validator(str(tmp_path), use_colors=False, staged_only=True, workers=1)

    validator.run_validations()

    assert any(issue.category == "trait-role-mismatch" for issue in validator._issues)


def test_validator_accepts_cross_role_land_traits_and_universal_types(tmp_path):
    _write_fixture(
        tmp_path,
        "characters = {\n"
        "\tTAG_marshal = {\n"
        "\t\tfield_marshal = {\n"
        "\t\t\ttraits = { infantry_officer old_guard politically_connected }\n"
        "\t\t}\n"
        "\t}\n"
        "\tTAG_general = {\n"
        "\t\tcorps_commander = {\n"
        "\t\t\ttraits = { defensive_doctrine }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []


def test_validator_reports_slot_mismatch_in_both_directions(tmp_path):
    _write_fixture(
        tmp_path,
        _characters(
            _advisor("TAG_chief", "army_chief", "army_armored_2"),
            _advisor("TAG_high_command", "high_command", "army_chief_defensive_1"),
        ),
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
        _characters(
            _advisor("TAG_air_chief", "air_chief", "air_air_superiority_1"),
            _advisor("TAG_navy_chief", "navy_chief", "navy_chief_reform_2"),
            _advisor("TAG_high_command", "high_command", "air_naval_strike_1"),
        ),
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []


def test_validator_exempts_country_traits_and_unchecked_slots(tmp_path):
    _write_fixture(
        tmp_path,
        _characters(
            _advisor("TAG_bespoke", "high_command", "ENG_royalty_advisor_trait"),
            _advisor("TAG_political", "political_advisor", "army_chief_defensive_1"),
            _advisor("TAG_hyphenated", "army_chief", "emerging_Communist-State"),
        ),
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []


def test_validator_exempts_tag_traits_sitting_in_a_pool_file(tmp_path):
    _write_fixture(
        tmp_path,
        _characters(_advisor("TAG_bespoke", "army_chief", "TAG_bespoke_pool_trait")),
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []


def test_validator_reports_undefined_and_unit_leader_traits_on_advisors(tmp_path):
    _write_fixture(
        tmp_path,
        _characters(
            _advisor("TAG_typo", "air_chief", "air_superiority_1"),
            _advisor("TAG_tag_typo", "army_chief", "ENG_made_up_trait"),
            _advisor("TAG_general_trait", "high_command", "ENG_royalty_trait"),
        ),
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    issues = _categories(validator)

    assert (
        "undefined-advisor-trait",
        "slot air_chief uses trait 'air_superiority_1', which is not defined in "
        "common/country_leader/",
    ) in issues
    # The TAG exemption covers the slot check only, never being defined at all.
    assert (
        "undefined-advisor-trait",
        "slot army_chief uses trait 'ENG_made_up_trait', which is not defined in "
        "common/country_leader/",
    ) in issues
    assert (
        "unit-leader-trait-on-advisor",
        "slot high_command uses 'ENG_royalty_trait', a common/unit_leader/ trait "
        "that does nothing on an advisor",
    ) in issues


def test_validator_reports_a_missing_pool_file_and_skips_the_slot_check(tmp_path):
    _write_fixture(
        tmp_path,
        _characters(
            _advisor("TAG_high_command", "high_command", "army_chief_defensive_1")
        ),
        skip_pool_file="01_navy_chief_traits.txt",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    categories = {category for category, _ in _categories(validator)}

    assert categories == {"advisor-pool-file-missing"}


def test_validator_skips_when_neither_trait_pool_parses(tmp_path):
    char_dir = tmp_path / "common" / "characters"
    char_dir.mkdir(parents=True)
    (char_dir / "TAG.txt").write_text(
        "advisor = {\n\tslot = army_chief\n\ttraits = { made_up }\n}\n",
        encoding="utf-8",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    categories = {category for category, _ in _categories(validator)}

    assert categories == {"advisor-pool-file-missing"}


def test_validator_runs_the_advisor_check_alone_when_no_unit_traits_exist(
    tmp_path, write_path
):
    advisor_dir = tmp_path / "common" / "country_leader"
    advisor_dir.mkdir(parents=True)
    for fname, content in POOL_FILES.items():
        (advisor_dir / fname).write_text(content, encoding="utf-8")
    write_path(
        tmp_path,
        "common/characters/TAG.txt",
        _characters(_advisor("TAG_chief", "army_chief", "army_armored_2")),
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert {category for category, _ in _categories(validator)} == {
        "advisor-trait-slot-mismatch"
    }


def test_validator_runs_the_role_check_alone_when_no_advisor_traits_exist(
    tmp_path, write_path
):
    write_path(tmp_path, "common/unit_leader/01_army_leader_traits.txt", TRAITS)
    write_path(
        tmp_path,
        "common/characters/TAG.txt",
        "characters = {\n"
        "\tTAG_general = {\n"
        "\t\tcorps_commander = {\n"
        "\t\t\ttraits = { bold }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    categories = {category for category, _ in _categories(validator)}

    assert "trait-role-mismatch" in categories
    assert "undefined-advisor-trait" not in categories


def test_validator_scans_all_uses_when_an_advisor_pool_file_is_staged(
    tmp_path, monkeypatch
):
    _write_fixture(
        tmp_path,
        _characters(_advisor("TAG_chief", "army_chief", "army_armored_2")),
    )
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/country_leader/01_high_command_traits.txt"
    )
    validator = Validator(str(tmp_path), use_colors=False, staged_only=True, workers=1)

    validator.run_validations()

    assert any(
        issue.category == "advisor-trait-slot-mismatch" for issue in validator._issues
    )
