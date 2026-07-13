"""Tests for the unknown-modifier-name check in validate_modifiers.py.

Invalid modifier names compile silently and do nothing in-game, so this check
is the only guard against typo'd modifiers in ideas/focuses/decisions.
"""

from validate_modifiers import (
    Validator,
    _check_file_for_unknown_modifiers,
    _is_parametric_modifier,
)


def _write_idea_file(tmp_path, modifier_body):
    ideas_dir = tmp_path / "common" / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    path = ideas_dir / "test_ideas.txt"
    path.write_text(
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\ttest_idea = {\n"
        "\t\t\tpicture = generic_foreign_capital\n"
        "\t\t\tmodifier = {\n"
        f"{modifier_body}"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    return path


def test_unknown_modifier_in_idea_flagged(tmp_path):
    path = _write_idea_file(
        tmp_path,
        "\t\t\t\tstability_factor = 0.05\n"
        "\t\t\t\tcompletely_fake_modifier_field = 0.1\n",
    )
    results = _check_file_for_unknown_modifiers(
        (str(path), frozenset({"stability_factor"}), str(tmp_path))
    )
    assert len(results) == 1
    name, rel, lineno = results[0]
    assert name == "completely_fake_modifier_field"
    assert rel.endswith("test_ideas.txt")
    assert lineno > 0


def test_known_modifier_not_flagged(tmp_path):
    path = _write_idea_file(tmp_path, "\t\t\t\tstability_factor = 0.05\n")
    results = _check_file_for_unknown_modifiers(
        (str(path), frozenset({"stability_factor"}), str(tmp_path))
    )
    assert results == []


def test_ai_weight_modifier_block_skipped(tmp_path):
    """A modifier = {} carrying factor/base/add is an AI weight block, not a
    game modifier block — its trigger keys must not be checked as modifiers."""
    ideas_dir = tmp_path / "common" / "ideas"
    ideas_dir.mkdir(parents=True)
    path = ideas_dir / "weights.txt"
    path.write_text(
        "random_list = {\n"
        "\t50 = {\n"
        "\t\tmodifier = {\n"
        "\t\t\tfactor = 2\n"
        "\t\t\tis_major = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    results = _check_file_for_unknown_modifiers((str(path), frozenset(), str(tmp_path)))
    assert results == []


def test_parametric_modifier_families_exempt():
    assert _is_parametric_modifier("production_speed_arms_factory_factor")
    assert _is_parametric_modifier("democratic_drift")
    assert not _is_parametric_modifier("completely_fake_modifier_field")


def test_repeated_unknown_modifier_is_not_known_or_reported_repeatedly(tmp_path):
    for index in range(3):
        path = _write_idea_file(
            tmp_path,
            "\t\t\t\trepeated_fake_modifier = 0.1\n",
        )
        path.rename(path.with_name(f"test_ideas_{index}.txt"))

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    assert "repeated_fake_modifier" not in known_good

    validator.validate_modifier_names(known_good)
    assert validator.warnings_found == 1
    assert len(validator._issues) == 1
    assert "repeated_fake_modifier" in validator._issues[0].message


def test_dynamic_modifier_nested_typo_is_not_self_whitelisted(tmp_path):
    definition_dir = tmp_path / "common" / "modifier_definitions"
    definition_dir.mkdir(parents=True)
    (definition_dir / "test.txt").write_text(
        "known_dynamic_modifier_key = { value_type = number }\n",
        encoding="utf-8",
    )
    dynamic_dir = tmp_path / "common" / "dynamic_modifiers"
    dynamic_dir.mkdir(parents=True)
    (dynamic_dir / "test.txt").write_text(
        "test_dynamic_modifier = {\n"
        "\tenable = { always = yes }\n"
        "\tknown_dynamic_modifier_key = 0.1\n"
        "\tnested_dynamic_modifier_typo = 0.2\n"
        "}\n",
        encoding="utf-8",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    assert "known_dynamic_modifier_key" in known_good
    assert "nested_dynamic_modifier_typo" not in known_good

    validator.validate_modifier_names(known_good)
    assert validator.warnings_found == 1
    assert len(validator._issues) == 1
    assert "nested_dynamic_modifier_typo" in validator._issues[0].message


def test_full_run_flags_only_undefined_modifier(tmp_path):
    """A name defined in common/modifier_definitions/ enters the known-good
    set regardless of usage frequency; a made-up name in the same block warns."""
    def_dir = tmp_path / "common" / "modifier_definitions"
    def_dir.mkdir(parents=True)
    (def_dir / "00_test_modifiers.txt").write_text(
        "my_custom_defined_modifier = {\n"
        "\tcolor_type = good\n"
        "\tvalue_type = number\n"
        "}\n",
        encoding="utf-8",
    )
    _write_idea_file(
        tmp_path,
        "\t\t\t\tmy_custom_defined_modifier = 0.05\n"
        "\t\t\t\tcompletely_fake_modifier_field = 0.1\n",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    validator.validate_modifier_names(known_good)

    assert validator.warnings_found == 1
    issue = validator._issues[0]
    assert issue.category == "unknown-modifier"
    assert "completely_fake_modifier_field" in issue.message
    assert "my_custom_defined_modifier" not in issue.message


def test_md_prefixed_modifiers_always_valid(tmp_path):
    path = _write_idea_file(tmp_path, "\t\t\t\tMD_custom_thing = 0.1\n")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_modifier_names(frozenset())
    assert validator.warnings_found == 0
    assert path.exists()
