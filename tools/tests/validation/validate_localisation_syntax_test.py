"""Localisation file syntax: unpaired brackets, colour codes and the section
sign, formatter-mangled lines, the l_english header, the YAML lint, and how
the shared scan picks and reads English files."""

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
from shared.suite import (
    assert_findings,
    build_validator,
    write_under_str,
    write_yml,
    yml_scan,
    yml_syntax,
)
from validator_common import Severity


def _syntax(tmp_path, line):
    path = write_yml(tmp_path, "a_l_english.yml", line)
    return [
        f"{f.category}: {f.message}" if isinstance(f, VL.Issue) else f
        for f in yml_syntax(path, ["Y", "R", "G"])
    ]


# ---- brackets ----------------------------------------------------------------


@pytest.mark.parametrize(
    "line, expected",
    [
        ('KEY:0 "[ROOT.GetName] ready"', []),
        ('KEY:0 "[broken"', ["a_l_english.yml - line 2 - unpaired bracket"]),
    ],
    ids=["paired", "unpaired"],
)
def test_brackets(tmp_path, line, expected):
    assert yml_scan(write_yml(tmp_path, "a_l_english.yml", line), "brackets") == (
        expected
    )


# ---- colour codes, the section sign and mangled lines -------------------------

_MANGLED = "mangled-loc-line: Loc "

# A single § always starts a colour code, even before a space: in game "§ 1"
# drops the space and logs a missing colour every frame. `§§` is a literal §.
# case: (loc line, fragments of each finding)
_SYNTAX_CASES = {
    "closed colour codes": ('KEY:0 "§Ya§! §Yb§!"', []),
    "colour code never closed": ('KEY:0 "§Ya §Yb"', [("expected 1 §! but got 0",)]),
    "odd number of section signs": (
        'KEY:0 "broken color §"',
        [("odd number of § symbols (1)",)],
    ),
    "unsupported colour": ('KEY:0 "§Zbad§!"', [("unsupported color 'Z'",)]),
    "colour from a getter or substitution": ('KEY:0 "§[GetC]a§! §$c$b§!"', []),
    "section sign before a space": (
        'KEY:0 "(15 U.S.C. § 1)."',
        [("line 2", "§ before whitespace is read as a color code")],
    ),
    "escaped section sign": ('KEY:0 "(15 U.S.C. §§ 1)."', []),
    "single-quoted value": (
        "KEY:0 'Some Value'",
        [(_MANGLED, "single quotes")],
    ),
    "key with no value": ("KEY:0", [(_MANGLED, "no value")]),
}


@pytest.mark.parametrize(
    ("line", "expected"), _SYNTAX_CASES.values(), ids=_SYNTAX_CASES
)
def test_syntax(tmp_path, line, expected):
    assert_findings(_syntax(tmp_path, line), expected)


# A key used as $KEY$ elsewhere may hold half a colour pair.
@pytest.mark.parametrize(
    "other, expected",
    [
        ('other:0 "$sub_a$ text"', []),
        ('other:0 "plain"', ["colors - odd number of § symbols (1)"]),
    ],
    ids=["substituted", "not substituted"],
)
def test_substituted_keys_are_exempt_from_colour_checks(tmp_path, other, expected):
    write_under_str(
        tmp_path, "localisation/english/a_l_english.yml", 'l_english:\n sub_a:0 "§Y"\n'
    )
    write_under_str(
        tmp_path, "localisation/english/b_l_english.yml", f"l_english:\n {other}\n"
    )
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_syntax()
    assert [issue.message for issue in validator._issues] == expected


# ---- l_english header ---------------------------------------------------------


@pytest.mark.parametrize(
    "body, expected",
    [
        ("", []),
        (' KEY:0 "value"\n', ["headless_l_english.yml - l_english: line is absent"]),
    ],
    ids=["empty file", "no header"],
)
def test_mandatory_header(tmp_path, body, expected):
    path = write_under_str(tmp_path, "headless_l_english.yml", body)
    assert yml_scan(path, "mandatory") == expected


# ---- YAML lint ----------------------------------------------------------------


# The content checks strip comments; the YAML checks see them raw.
@pytest.mark.parametrize(
    "line", [' KEY: "“curly”"', " # a ‘curly’ comment"], ids=["value", "comment"]
)
def test_yaml_findings_reuse_the_fixer_finding_with_its_location(line):
    issues = VL._scan_yaml_text(f"l_english:\n{line}\n", "fixture.yml")
    assert [(i.severity, i.category, i.message, i.file, i.line) for i in issues] == [
        (
            Severity.ERROR,
            f"loc-yaml-{kind.replace('_', '-')}",
            description,
            "fixture.yml",
            2,
        )
        for _, kind, description in check_line(line, 2)
    ]
    assert issues


def test_valid_quotes_and_dynamic_text_are_unchanged():
    text = 'l_english:\n KEY: "[ROOT.GetName] §Y$value$§! \\n he said \\"hi\\""\n'
    assert VL._scan_yaml_text(text, "fixture.yml") == []
    assert "\n".join(fix_line(line) for line in text.split("\n")) == text


# The YAML lint covers files exempt from the content checks; one read serves both.
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
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_yaml_syntax()
    validator.validate_syntax()
    assert sorted(calls) == sorted([normal, exempt])
    assert sorted((i.category, i.file, i.line) for i in validator._issues) == [
        (
            "loc-yaml-smart-quote",
            "localisation/english/MD_dm_modifiers_l_english.yml",
            2,
        ),
        ("loc-yaml-smart-quote", "localisation/english/nested/a.yml", 2),
    ]
    assert validator.errors_found == 2


def test_staged_run_reports_only_the_selected_english_files(tmp_path, monkeypatch):
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
