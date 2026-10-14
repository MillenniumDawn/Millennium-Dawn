"""Localisation YAML findings belong to the validator's strict results."""

import json
import runpy
import sys

import pytest
import validate_localisation as VL
from fix_loc_yaml import check_line, fix_line
from report_lib.baseline import tag_changed_files
from report_lib.checks_api import _issue_to_annotation
from report_lib.markdown import _file_ref
from report_lib.models import Issue as ReportIssue
from report_lib.models import ReportContext
from shared.suite import issue_rows, write_under_str
from validator_common import Severity


@pytest.mark.parametrize(
    "line",
    [
        ' KEY:\t"value"',
        " # a\ttabbed comment",
        ' KEY: "“curly”"',
        " # a ‘curly’ comment",
        ' KEY:0 "value"',
        ' KEY:"value"',
        '   KEY: "value"',
        ' KEY: "unterminated',
        ' KEY: "say "hi" now"',
        ' KEY: "# don’t skip this"',
    ],
)
def test_yaml_checks_reuse_every_fixer_finding_with_locations(line):
    issues = VL._scan_yaml_text(f"l_english:\n{line}\n", "fixture.yml")
    assert [
        (issue.severity, issue.category, issue.message, issue.file, issue.line)
        for issue in issues
    ] == [
        (
            Severity.ERROR,
            f"loc-yaml-{kind.replace('_', '-')}",
            description,
            "fixture.yml",
            line_num,
        )
        for line_num, kind, description in check_line(line, 2)
    ]
    assert issues


def test_valid_quotes_and_dynamic_text_are_unchanged():
    text = 'l_english:\n KEY: "[ROOT.GetName] §Y$value$§! \\n he said \\"hi\\""\n'
    assert VL._scan_yaml_text(text, "fixture.yml") == []
    assert "\n".join(fix_line(line) for line in text.split("\n")) == text


def test_yaml_checks_include_content_exempt_files_and_share_reads(
    tmp_path, monkeypatch
):
    normal = write_under_str(
        tmp_path,
        "localisation/english/nested/a.yml",
        'l_english:\n KEY: "don’t"\n',
    )
    exempt = write_under_str(
        tmp_path,
        "localisation/english/MD_dm_modifiers_l_english.yml",
        'l_english:\n OTHER: "§Zdon’t§!"\n',
    )
    write_under_str(tmp_path, "localisation/french/a.yml", 'l_french:\n KEY: "don’t"\n')
    calls = []
    original_read = VL.read_text_strict

    def read(filename):
        calls.append(filename)
        return original_read(filename)

    monkeypatch.setattr(VL, "read_text_strict", read)
    validator = VL.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.validate_yaml_syntax()
    validator.validate_syntax()
    assert sorted(calls) == sorted([normal, exempt])
    assert sorted((i.category, i.file, i.line) for i in validator._issues) == sorted(
        [
            ("loc-yaml-smart-quote", path, 2)
            for path in (
                "localisation/english/nested/a.yml",
                "localisation/english/MD_dm_modifiers_l_english.yml",
            )
        ]
    )
    assert validator.errors_found == 2


def test_staged_yaml_checks_only_report_selected_english_files(tmp_path, monkeypatch):
    for name in ("selected", "untouched"):
        write_under_str(
            tmp_path,
            f"localisation/english/{name}.yml",
            f'l_english:\n {name}: "don’t"\n',
        )
    selected = "localisation/english/selected.yml"
    monkeypatch.setenv("MD_STAGED_FILES", selected)
    validator = VL.Validator(str(tmp_path), staged_only=True, workers=1)
    validator.run_all_validations()
    assert [(i.category, i.file, i.line) for i in validator._issues] == [
        ("loc-yaml-smart-quote", selected, 2)
    ]


@pytest.mark.parametrize("fixed", [False, True])
def test_strict_cli_gates_yaml_findings_and_writes_the_sidecar(
    tmp_path, monkeypatch, fixed
):
    line = ' KEY: "don’t"'
    relative = "localisation/english/a.yml"
    write_under_str(
        tmp_path,
        relative,
        f"l_english:\n{fix_line(line) if fixed else line}\n",
    )
    output = tmp_path / "localisation.log"
    monkeypatch.setenv("MD_STAGED_FILES", relative)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            VL.__file__,
            "--path",
            str(tmp_path),
            "--staged",
            "--strict",
            "--no-color",
            "--no-cache",
            "--workers",
            "1",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(VL.__file__, run_name="__main__")
    assert excinfo.value.code == (0 if fixed else 1)
    issues = json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
    assert [(i["category"], i["file"], i["line"]) for i in issues] == (
        [] if fixed else [("loc-yaml-smart-quote", relative, 2)]
    )
    if not fixed:
        issue = ReportIssue.from_dict(issues[0], validator="localisation")
        tag_changed_files([issue], {relative})
        assert issue.in_diff
        assert _issue_to_annotation(issue)["path"] == relative
        context = ReportContext(
            repo="MillenniumDawn/Millennium-Dawn", commit_sha="head"
        )
        assert _file_ref(issue, context) == (
            f"[`{relative}:2`](https://github.com/MillenniumDawn/Millennium-Dawn/blob/head/{relative}#L2)"
        )


def test_yaml_pool_matches_the_sequential_scan(tmp_path, monkeypatch, pool_sizes):
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    for index in range(12):
        write_under_str(
            tmp_path,
            f"localisation/english/f{index:02}.yml",
            'l_english:\n KEY: "don’t"\n',
        )

    def run(workers):
        validator = VL.Validator(str(tmp_path), use_colors=False, workers=workers)
        try:
            validator.validate_yaml_syntax()
            return issue_rows(validator)
        finally:
            validator._close_pool()

    pooled = run(2)
    assert pool_sizes and set(pool_sizes) == {2}
    assert pooled == run(1)
    assert len(pooled) == 12
    assert {row[2] for row in pooled} == {
        f"localisation/english/f{index:02}.yml" for index in range(12)
    }
