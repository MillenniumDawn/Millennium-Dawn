"""Tests for validate_unused_scripted (scripted effect/trigger call detection)."""

import validate_unused_scripted as V


def _validator(tmp_path, **kwargs):
    return V.Validator(str(tmp_path), use_colors=False, workers=1, **kwargs)


def test_allowlisted_names_are_never_reported():
    assert V._is_false_positive("has_md_alert", "00_alert_triggers.txt")
    assert V._is_false_positive("USA_election_house", "USA_congress.txt")
    assert not V._is_false_positive("has_md_alerts", "00_alert_triggers.txt")


def test_a_repo_with_no_scripted_definitions_is_a_clean_pass(tmp_path):
    validator = _validator(tmp_path)
    validator.run_validations()
    assert validator._issues == []


def test_extract_definitions_ignores_top_level_assignments(tmp_path, write_path):
    source = write_path(
        tmp_path,
        "common/scripted_effects/effects.txt",
        "some_setting = yes\neffect_one = { }\n",
    )

    names = [
        name
        for name, _rel, _line in V.extract_definitions((str(source), str(tmp_path)))
    ]

    assert names == ["effect_one"]


def test_collect_definitions_narrows_to_the_staged_files(
    tmp_path, write_path, monkeypatch
):
    write_path(tmp_path, "common/scripted_effects/staged.txt", "staged_effect = { }\n")
    write_path(
        tmp_path, "common/scripted_effects/untouched.txt", "other_effect = { }\n"
    )
    monkeypatch.setenv("MD_STAGED_FILES", "common/scripted_effects/staged.txt")

    validator = _validator(tmp_path, staged_only=True)
    names = [
        name for name, _rel, _line in validator._collect_definitions("scripted_effects")
    ]

    assert names == ["staged_effect"]


def test_a_false_positive_name_is_not_reported_as_unused(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_triggers/years.txt",
        "trigger_year_2020 = { }\nordinary_trigger = { }\n",
    )

    validator = _validator(tmp_path)
    validator.run_validations()

    messages = [issue.message for issue in validator._issues]
    assert any("ordinary_trigger" in message for message in messages)
    assert not any("trigger_year_2020" in message for message in messages)


def test_a_name_defined_twice_is_reported_at_both_sites(tmp_path, write_path):
    write_path(tmp_path, "common/scripted_effects/a.txt", "twin_effect = { }\n")
    write_path(tmp_path, "common/scripted_effects/b.txt", "twin_effect = { }\n")

    validator = _validator(tmp_path)
    validator.run_validations()

    files = sorted(issue.file for issue in validator._issues)
    assert files == [
        "common/scripted_effects/a.txt",
        "common/scripted_effects/b.txt",
    ]


def test_an_unreadable_definition_file_does_not_hide_the_rest(tmp_path, write_path):
    write_path(tmp_path, "common/scripted_effects/effects.txt", "lonely_effect = { }\n")
    (tmp_path / "common" / "scripted_effects" / "broken.txt").mkdir()

    validator = _validator(tmp_path)
    validator.run_validations()

    assert [(issue.file, issue.line, issue.message) for issue in validator._issues] == [
        ("common/scripted_effects/effects.txt", 1, "lonely_effect")
    ]


def test_parameterised_cross_call_between_definition_files_counts_as_use(
    tmp_path, write_path
):
    """`NAME = { ARG = 1 }` from another scripted file is a use.

    The cross-call pass matched only `NAME = yes`, so an effect called solely
    with parameters, and solely from other definition files, was reported
    unused. Targeted Operations tripped this repeatedly.
    """
    write_path(
        tmp_path,
        "common/scripted_effects/00_caller.txt",
        "caller_effect = {\n\tcallee_effect = { TARGET = 7 }\n}\n",
    )
    write_path(
        tmp_path,
        "common/scripted_effects/01_callee.txt",
        "callee_effect = {\n\tset_temp_variable = { x = $TARGET$ }\n}\n",
    )
    write_path(tmp_path, "events/use.txt", "caller_effect = yes\n")

    validator = _validator(tmp_path)
    validator.run_validations()

    reported = [str(issue) for issue in validator._issues]
    assert not any("callee_effect" in r for r in reported), reported


def test_a_definition_does_not_count_as_its_own_use(tmp_path, write_path):
    """Definitions sit at column 0; only an indented call is a call."""
    write_path(
        tmp_path,
        "common/scripted_effects/00_lonely.txt",
        "lonely_effect = {\n\tadd_political_power = 1\n}\n",
    )

    validator = _validator(tmp_path)
    validator.run_validations()

    assert any("lonely_effect" in str(issue) for issue in validator._issues)
