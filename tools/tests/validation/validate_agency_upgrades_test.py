"""Tests for agency upgrade definitions, pictures, and script references."""

import pytest
import validate_agency_upgrades as agency
from shared.suite import build_validator, issue_categories
from shared.suite import write_under as _write


def _validator(root, **kwargs):
    return build_validator(agency.Validator, root, **kwargs)


def _messages(validator):
    return [issue.message for issue in validator._issues]


def test_read_of_a_missing_file_is_empty(tmp_path):
    assert agency._read(tmp_path / "missing.txt") == ""


def test_line_of_counts_from_one():
    assert agency.line_of("a\nb\n", 2) == 2


def test_call_scan_reads_icons_and_upgrades_and_skips_comments():
    text = (
        "# create_intelligence_agency = { icon = GFX_ignored }\n"
        "create_intelligence_agency = {\n"
        "\ticon = GFX_real\n"
        "}\n"
        "create_intelligence_agency = { }\n"
        "upgrade_intelligence_agency = upgrade_real\n"
        "upgrade_intelligence_agency = upgrade_other\n"
    )
    assert agency._scan_agency_calls(agency.strip_comments(text), "events/x.txt") == (
        [("events/x.txt", 2, "GFX_real")],
        [("events/x.txt", 6, "upgrade_real"), ("events/x.txt", 7, "upgrade_other")],
    )


def test_call_worker_on_a_missing_file_finds_nothing(tmp_path):
    assert agency.process_file_for_agency_calls(
        (str(tmp_path / "missing.txt"), str(tmp_path))
    ) == ([], [])


def test_full_run_reports_definition_picture_and_call_issues(tmp_path):
    _write(
        tmp_path,
        "common/intelligence_agency_upgrades/upgrades.txt",
        "\tupgrade_good = {\n\t\tpicture = GFX_good\n\t}\n"
        "\tupgrade_no_picture = {\n\t}\n"
        "\tupgrade_missing_picture = {\n\t\tpicture = GFX_missing\n\t}\n",
    )
    _write(
        tmp_path,
        "common/intelligence_agency_upgrades/duplicate.txt",
        "\tupgrade_good = {\n\t\tpicture = GFX_good\n\t}\n",
    )
    _write(tmp_path, "interface/agency.gfx", 'spriteType = { name = "GFX_good" }\n')
    _write(
        tmp_path,
        "events/calls.txt",
        "create_intelligence_agency = { icon = GFX_missing_logo }\n"
        "upgrade_intelligence_agency = upgrade_unknown\n",
    )

    validator = _validator(tmp_path)
    validator.run_all_validations()

    assert set(issue_categories(validator)) == {
        "agency-upgrades-duplicates",
        "agency-upgrades-pictures",
        "agency-upgrades-calls",
    }
    messages = _messages(validator)
    assert any(
        "upgrade_good" in message and "more than once" in message
        for message in messages
    )
    assert any("upgrade_no_picture" in message for message in messages)
    assert any("GFX_missing" in message for message in messages)
    assert any("GFX_missing_logo" in message for message in messages)
    assert any("upgrade_unknown" in message for message in messages)


def _clean_tree(tmp_path):
    _write(
        tmp_path,
        "common/intelligence_agency_upgrades/upgrades.txt",
        "\tupgrade_good = {\n\t\tpicture = GFX_good\n\t}\n",
    )
    _write(
        tmp_path,
        "interface/agency.gfx",
        'spriteType = { name = "GFX_good" }\nspriteType = { name = "GFX_logo" }\n',
    )
    _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        "create_intelligence_agency = { icon = GFX_logo }\n"
        "upgrade_intelligence_agency = upgrade_good\n",
    )


@pytest.mark.parametrize("staged_only", [False, True], ids=["full", "staged"])
def test_valid_definitions_and_references_are_clean(tmp_path, monkeypatch, staged_only):
    _clean_tree(tmp_path)
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/intelligence_agency_upgrades/upgrades.txt"
    )
    validator = _validator(tmp_path, staged_only=staged_only)
    assert validator.run_all_validations() == 0
    assert validator._issues == []
