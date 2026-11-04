"""Tests for country graphical culture registration checks."""

import validate_graphical_cultures as V


def _write_inputs(tmp_path, write_path, country_text, registry_text):
    write_path(tmp_path, "common/countries/Testland.txt", country_text)
    write_path(tmp_path, "common/graphicalculturetype.txt", registry_text)


def test_registered_country_culture_is_clean(tmp_path, write_path):
    _write_inputs(
        tmp_path,
        write_path,
        "graphical_culture = test_gfx\n",
        "test_gfx\n",
    )

    validator = V.Validator(str(tmp_path))
    validator.run_validations()

    assert validator._issues == []


def test_unregistered_country_culture_warns_with_file_and_line(tmp_path, write_path):
    _write_inputs(
        tmp_path,
        write_path,
        "color = { 1 2 3 }\ngraphical_culture = missing_gfx\n",
        "test_gfx\n",
    )

    validator = V.Validator(str(tmp_path))
    validator.run_validations()

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.severity == "warning"
    assert issue.category == "graphical-culture-unregistered"
    assert issue.file == "common/countries/Testland.txt"
    assert issue.line == 2
    assert "missing_gfx" in issue.message


def test_country_parser_ignores_comments_strings_and_nested_assignments():
    country = """# graphical_culture = commented_gfx
name = "text says graphical_culture = quoted_gfx # still text"
metadata = { graphical_culture = nested_gfx }
graphical_culture = valid_gfx # comment after a real assignment
graphical_culture = "quoted_value"
"""

    assert V._country_cultures(country) == [("valid_gfx", 4)]


def test_staged_mode_checks_all_countries_when_registry_changes(
    tmp_path, write_path, monkeypatch
):
    write_path(
        tmp_path,
        "common/countries/Testland.txt",
        "graphical_culture = removed_gfx\n",
    )
    write_path(
        tmp_path,
        "common/countries/Otherland.txt",
        "graphical_culture = removed_gfx\n",
    )
    write_path(tmp_path, "common/graphicalculturetype.txt", "other_gfx\n")
    monkeypatch.setenv("MD_STAGED_FILES", "common/graphicalculturetype.txt")

    validator = V.Validator(str(tmp_path), staged_only=True)
    validator.run_validations()

    assert {issue.file for issue in validator._issues} == {
        "common/countries/Testland.txt",
        "common/countries/Otherland.txt",
    }


def test_staged_mode_runs_for_country_changes_and_skips_unrelated_common(
    tmp_path, write_path, monkeypatch
):
    _write_inputs(
        tmp_path,
        write_path,
        "graphical_culture = missing_gfx\n",
        "test_gfx\n",
    )
    monkeypatch.setenv("MD_STAGED_FILES", "common/countries/Testland.txt")

    validator = V.Validator(str(tmp_path), staged_only=True)
    validator.run_validations()
    assert len(validator._issues) == 1

    monkeypatch.setenv("MD_STAGED_FILES", "common/technologies/example.txt")
    skipped = V.Validator(str(tmp_path), staged_only=True)
    skipped.run_validations()
    assert skipped._issues == []


def test_registered_cultures_are_bare_identifiers_and_ignore_comments():
    assert V._registered_cultures(
        '# ignored_gfx\nregistered_gfx\n"quoted_gfx"\ninvalid-name\n'
    ) == {"registered_gfx"}


def test_missing_registry_is_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/countries/Testland.txt",
        "graphical_culture = test_gfx\n",
    )

    validator = V.Validator(str(tmp_path))
    validator.run_validations()

    assert len(validator._issues) == 1
    assert validator._issues[0].category == "graphical-culture-registry-missing"


def test_staged_registry_deletion_is_reported(tmp_path, write_path, monkeypatch):
    write_path(
        tmp_path,
        "common/countries/Testland.txt",
        "graphical_culture = test_gfx\n",
    )
    monkeypatch.setenv("MD_STAGED_FILES", "common/graphicalculturetype.txt")

    validator = V.Validator(str(tmp_path), staged_only=True)
    validator.run_validations()

    assert len(validator._issues) == 1
    assert validator._issues[0].category == "graphical-culture-registry-missing"
    assert validator._issues[0].file == "common/graphicalculturetype.txt"
