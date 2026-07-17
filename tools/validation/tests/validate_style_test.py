import json

import pytest
import validate_style
from validate_style import Validator, _changed_lines_from_diff, _scan_file
from validator_common import Severity


def _errors(text, path="common/scripted_effects/test.txt"):
    return [
        finding
        for finding in _scan_file(text, path)
        if finding.severity == Severity.ERROR
    ]


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("root = {\nvalue = yes\n}\n", 2),
        ("root = {\n\tchild = {\n\t\tvalue = yes\n\t\t}\n}\n", 4),
    ],
)
def test_layout_rejects_indentation_inconsistent_with_brace_depth(text, line):
    findings = _errors(text)

    assert any(
        finding.category == "layout-indentation" and finding.line == line
        for finding in findings
    )


def test_layout_rejects_tab_after_indentation():
    findings = _errors("root = {\n\tvalue =\tyes\n}\n")

    assert any(finding.category == "layout-tabs" for finding in findings)


def test_four_space_indentation_is_changed_line_gated():
    findings = _errors("root = {\n    value = yes\n}\n")

    assert any(finding.category == "layout-indentation" for finding in findings)
    assert not any(finding.category == "indent-brackets" for finding in findings)


def test_layout_rejects_doubled_token_spacing():
    findings = _errors(
        "root = {\n\tprerequisite = { focus = AAA_one  focus = AAA_two }\n}\n"
    )

    assert any(finding.category == "layout-spacing" for finding in findings)


def test_layout_rejects_child_content_on_multiline_opener():
    text = (
        "root = {\n"
        "\tavailable = { hidden_trigger = { always = yes }\n"
        "\t\talways = yes\n"
        "\t}\n"
        "}\n"
    )

    findings = _errors(text)

    assert any(
        finding.category == "layout-blocks"
        and "opener" in finding.message
        and finding.line == 2
        for finding in findings
    )


def test_layout_rejects_executable_content_closing_parent_block():
    findings = _errors("root = {\n\tTAG = { value = yes } }\n")

    assert any(
        finding.category == "layout-blocks" and "Executable content" in finding.message
        for finding in findings
    )


def test_layout_rejects_multiple_parent_closes():
    findings = _errors("root = {\n\tchild = {\n} }\n")

    assert any(
        finding.category == "layout-blocks" and "Multiple parent" in finding.message
        for finding in findings
    )


def test_layout_ignores_strings_and_comments():
    text = (
        "root = {\n"
        '\tvalue = "# { }\t two  spaces"\n'
        "\tvalue = yes # } }\t two  spaces\n"
        "\t# { }\t two  spaces\n"
        "}\n"
    )

    assert not _errors(text)


def test_layout_allows_balanced_inline_blocks():
    text = "root = {\n\tavailable = { hidden_trigger = { always = yes } }\n}\n"

    assert not _errors(text)


def test_layout_allows_multiline_raw_token_arrays():
    text = "names = { Alice  Bob\n\tCharlie  Delta }\n"

    assert not _errors(text)


def test_layout_allows_raw_token_array_opened_on_previous_line():
    text = "names = {\n\tAlice  Bob\n\tCharlie Delta\n}\n"

    assert not _errors(text)


def test_layout_allows_else_transitions():
    text = (
        "root = {\n"
        "\tif = {\n"
        "\t\tlimit = { always = yes }\n"
        "\t} else_if = {\n"
        "\t\tlimit = { always = no }\n"
        "\t} else = {\n"
        "\t\tvalue = yes\n"
        "\t}\n"
        "}\n"
    )

    assert not _errors(text)


def _focus_block(focus_id):
    return (
        "\tfocus = {\n"
        f"\t\tid = {focus_id}\n"
        "\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
        "\t}\n"
    )


@pytest.mark.parametrize(
    "next_section",
    [
        _focus_block("AAA_second"),
        "\t# Next section\n",
    ],
)
def test_national_focus_requires_separator_after_focus(next_section):
    text = "focus_tree = {\n" + _focus_block("AAA_first") + next_section + "}\n"

    findings = _errors(text, "common/national_focus/test.txt")

    assert any(finding.category == "focus-layout" for finding in findings)


def test_national_focus_requires_separator_between_shared_focuses():
    block = (
        "shared_focus = {\n"
        "\tid = AAA_shared\n"
        "\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
        "}\n"
    )

    findings = _errors(block + block, "common/national_focus/test.txt")

    assert any(finding.category == "focus-layout" for finding in findings)


def test_national_focus_allows_separator_between_focuses():
    text = (
        "focus_tree = {\n"
        + _focus_block("AAA_first")
        + "\n"
        + _focus_block("AAA_second")
        + "}\n"
    )

    assert not _errors(text, "common/national_focus/test.txt")


def test_national_focus_does_not_require_separator_before_tree_close():
    text = "focus_tree = {\n" + _focus_block("AAA_first") + "}\n"

    assert not _errors(text, "common/national_focus/test.txt")


def test_changed_lines_from_diff_includes_added_lines_and_deletion_boundary():
    diff = "@@ -10,2 +10,3 @@\n@@ -30 +31,0 @@\n@@ -40 +41 @@\n"

    assert _changed_lines_from_diff(diff) == {10, 11, 12, 31, 41}


def test_full_scan_suppresses_legacy_layout_debt_by_default(tmp_path):
    content_dir = tmp_path / "common" / "scripted_effects"
    content_dir.mkdir(parents=True)
    (content_dir / "test.txt").write_text("root = {\nvalue = yes\n}\n")
    validator = Validator(str(tmp_path), use_colors=False, no_cache=True)

    validator.run_all_validations()

    assert validator.errors_found == 0


def test_all_layout_reports_legacy_layout_debt(tmp_path):
    content_dir = tmp_path / "common" / "scripted_effects"
    content_dir.mkdir(parents=True)
    (content_dir / "test.txt").write_text("root = {\nvalue = yes\n}\n")
    validator = Validator(
        str(tmp_path), use_colors=False, no_cache=True, all_layout=True
    )

    validator.run_all_validations()

    assert validator.errors_found == 1


@pytest.mark.parametrize(("changed_lines", "expected_errors"), [({2}, 1), ({3}, 0)])
def test_staged_scan_reports_layout_only_on_changed_lines(
    tmp_path, monkeypatch, changed_lines, expected_errors
):
    content_dir = tmp_path / "common" / "scripted_effects"
    content_dir.mkdir(parents=True)
    path = content_dir / "test.txt"
    path.write_text("root = {\nvalue = yes\n}\n")
    validator = Validator(
        str(tmp_path), use_colors=False, no_cache=True, staged_only=True
    )
    validator.staged_files = [str(path)]
    monkeypatch.setattr(
        validate_style,
        "_staged_changed_lines",
        lambda _mod_path, _rel_path: changed_lines,
    )

    validator.run_all_validations()

    assert validator.errors_found == expected_errors


def test_staged_changed_lines_reads_ci_sidecar(tmp_path, monkeypatch):
    sidecar = tmp_path / ".style-changed-lines.json"
    sidecar.write_text(
        json.dumps({"common/scripted_effects/test.txt": [2, 4]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("MD_STAGED_CHANGED_LINES_FILE", sidecar.name)

    assert validate_style._staged_changed_lines(
        str(tmp_path), "common/scripted_effects/test.txt"
    ) == {2, 4}


def test_staged_changed_lines_rejects_missing_ci_metadata(tmp_path, monkeypatch):
    sidecar = tmp_path / ".style-changed-lines.json"
    sidecar.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("MD_STAGED_CHANGED_LINES_FILE", sidecar.name)

    with pytest.raises(RuntimeError, match="Unable to load changed lines"):
        validate_style._staged_changed_lines(
            str(tmp_path), "common/scripted_effects/test.txt"
        )
