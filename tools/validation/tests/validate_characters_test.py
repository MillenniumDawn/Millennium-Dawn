"""Behavior tests for unit leader trait role checks."""

from validate_characters import Validator, collect_trait_uses, parse_trait_types

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


ADVISOR_TRAITS = """leader_traits = {
\tarmy_chief_defensive_2 = {
\t\tsprite = 7
\t}
}
"""


def _write_fixture(tmp_path, characters: str):
    trait_dir = tmp_path / "common" / "unit_leader"
    advisor_dir = tmp_path / "common" / "country_leader"
    char_dir = tmp_path / "common" / "characters"
    trait_dir.mkdir(parents=True)
    advisor_dir.mkdir(parents=True)
    char_dir.mkdir(parents=True)
    (trait_dir / "01_army_leader_traits.txt").write_text(TRAITS, encoding="utf-8")
    (advisor_dir / "02_army_chief_traits.txt").write_text(
        ADVISOR_TRAITS, encoding="utf-8"
    )
    (char_dir / "TAG.txt").write_text(characters, encoding="utf-8")


def test_parse_trait_types_reads_single_list_and_universal_types(tmp_path):
    _write_fixture(tmp_path, "characters = {\n}\n")

    assert parse_trait_types(str(tmp_path)) == {
        "infantry_officer": {"land"},
        "bold": {"navy"},
        "defensive_doctrine": {"field_marshal"},
        "politically_connected": {"land", "navy"},
        "old_guard": {"all"},
    }


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
    issues = {(issue.category, issue.message) for issue in validator._issues}

    assert issues == {
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
