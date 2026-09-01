"""Tests for validate_ai_roles.py — role_ratio/build_army references in
common/ai_strategy/ against the roles defined in common/ai_templates/ and
declared on common/ai_equipment/ variants.

A reference to an undefined role silently produces no units for that slot, so
every typo has to be reported with the file, the line, and the closest match.
"""

import validate_ai_roles as V


def _write(tmp_path, relative, body):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return str(path)


def _validator(tmp_path):
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def test_collect_roles_from_file_ignores_commented_definitions(tmp_path):
    path = _write(
        tmp_path,
        "common/ai_templates/land.txt",
        "generic_infantry = {\n"
        "\trole = infantry\n"
        "\t# role = retired_infantry\n"
        "}\n"
        "generic_armor = {\n"
        "\trole = armor\n"
        "}\n",
    )
    assert V.collect_roles_from_file(path) == {"infantry", "armor"}


def test_collect_roles_from_file_missing_file_is_empty(tmp_path):
    assert V.collect_roles_from_file(str(tmp_path / "gone.txt")) == set()


def test_collect_variant_roles_from_file_reads_role_lists(tmp_path):
    path = _write(
        tmp_path,
        "common/ai_equipment/naval.txt",
        "generic_frigate = {\n"
        "\tcategory = naval\n"
        "\troles = { naval_frigate naval_escort }\n"
        "}\n"
        "# generic_ghost = {\n"
        "# \troles = { naval_ghost }\n"
        "# }\n",
    )
    assert V.collect_variant_roles_from_file(path) == {"naval_frigate", "naval_escort"}


def test_collect_variant_roles_from_file_missing_file_is_empty(tmp_path):
    assert V.collect_variant_roles_from_file(str(tmp_path / "gone.txt")) == set()


def test_collect_references_records_line_numbers_and_skips_comments(tmp_path):
    path = _write(
        tmp_path,
        "common/ai_strategy/USA.txt",
        "USA_army = {\n"
        "\trole_ratio = {\n"
        "\t\tid = infantry\n"
        "\t\tratio = 0.5\n"
        "\t}\n"
        "\tbuild_army id = armor\n"
        "\t# build_army id = ghost\n"
        "}\n",
    )
    assert V.collect_references_from_file(path) == [("armor", "USA.txt", 6)]


def test_collect_references_missing_file_is_empty(tmp_path):
    assert V.collect_references_from_file(str(tmp_path / "gone.txt")) == []


def test_validate_strategy_file_suggests_closest_role(tmp_path):
    path = _write(
        tmp_path,
        "common/ai_strategy/USA.txt",
        "USA_army = {\n\tbuild_army id = naval_frigat\n}\n",
    )
    results = V.validate_strategy_file((path, {"naval_frigate", "infantry"}))
    assert results == [
        "USA.txt:2: unknown role 'naval_frigat' (did you mean 'naval_frigate'?)"
    ]


def test_validate_strategy_file_without_close_match_omits_suggestion(tmp_path):
    path = _write(
        tmp_path,
        "common/ai_strategy/USA.txt",
        "USA_army = {\n\tbuild_army id = zzzzzzz\n}\n",
    )
    results = V.validate_strategy_file((path, {"infantry"}))
    assert results == ["USA.txt:2: unknown role 'zzzzzzz'"]


def test_validate_strategy_file_clean_for_known_role(tmp_path):
    path = _write(
        tmp_path,
        "common/ai_strategy/USA.txt",
        "USA_army = {\n\tbuild_army id = infantry\n}\n",
    )
    assert V.validate_strategy_file((path, {"infantry"})) == []


def test_collect_valid_roles_unions_templates_equipment_and_vanilla(tmp_path):
    _write(
        tmp_path,
        "common/ai_templates/land.txt",
        "generic_infantry = {\n\trole = infantry\n}\n",
    )
    _write(
        tmp_path,
        "common/ai_equipment/naval.txt",
        "generic_frigate = {\n\troles = { naval_frigate }\n}\n",
    )
    validator = _validator(tmp_path)
    validator._collect_valid_roles()
    assert {"infantry", "naval_frigate"} <= validator.valid_roles
    assert V.VANILLA_ROLES <= validator.valid_roles


def test_validator_flags_unknown_role_with_file_and_line(tmp_path):
    _write(
        tmp_path,
        "common/ai_templates/land.txt",
        "generic_infantry = {\n\trole = infantry\n}\n",
    )
    _write(
        tmp_path,
        "common/ai_strategy/USA.txt",
        "USA_army = {\n"
        "\trole_ratio id = infantry\n"
        "\trole_ratio id = infantery\n"
        "}\n",
    )
    validator = _validator(tmp_path)
    validator.run_validations()

    assert validator.errors_found == 1
    issue = validator._issues[0]
    assert issue.file == "USA.txt"
    assert issue.line == 3
    assert issue.message == "unknown role 'infantery' (did you mean 'infantry'?)"


def test_validator_clean_when_every_reference_resolves(tmp_path):
    _write(
        tmp_path,
        "common/ai_templates/land.txt",
        "generic_infantry = {\n\trole = infantry\n}\n",
    )
    _write(
        tmp_path,
        "common/ai_equipment/naval.txt",
        "generic_frigate = {\n\troles = { naval_frigate }\n}\n",
    )
    _write(
        tmp_path,
        "common/ai_strategy/USA.txt",
        "USA_army = {\n"
        "\trole_ratio id = infantry\n"
        "\tbuild_army id = naval_frigate\n"
        "\tbuild_army id = nuclear_missile\n"
        "}\n",
    )
    validator = _validator(tmp_path)
    validator.run_validations()

    assert validator.errors_found == 0
    assert validator._issues == []
