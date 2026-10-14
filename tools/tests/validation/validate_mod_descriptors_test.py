"""Tests for validate_mod_descriptors: descriptor.mod and Millennium_Dawn.mod must
list the same replace_path entries, once each."""

import sys

import pytest
import validate_mod_descriptors as V
from shared.suite import build_validator, issue_categories, write_tree
from shared_utils import run_validator_main


def test_parser_skips_comments_and_keeps_line_numbers():
    text = '# replace_path = "commented"\nreplace_path = "common/a"\n'
    assert V.parse_replace_paths(text) == [("common/a", 2)]


# case: ({file: content}, categories reported)
_DESCRIPTOR_CASES = {
    "in sync": (
        {
            "descriptor.mod": 'replace_path = "common/a"\n',
            "Millennium_Dawn.mod": 'replace_path = "common/a"\n',
        },
        [],
    ),
    "duplicate and out of sync": (
        {
            "descriptor.mod": 'replace_path = "common/a"\nreplace_path = "common/a"\n',
            "Millennium_Dawn.mod": 'replace_path = "common/b"\n',
        },
        ["duplicate-replace-path", "replace-path-sync"],
    ),
    "missing mod file": ({"descriptor.mod": ""}, ["missing-mod-file"]),
}


@pytest.mark.parametrize(
    ("files", "expected"), _DESCRIPTOR_CASES.values(), ids=_DESCRIPTOR_CASES
)
def test_descriptors(tmp_path, files, expected):
    write_tree(tmp_path, files)
    validator = build_validator(V.Validator, tmp_path)
    validator.run_validations()
    assert sorted(set(issue_categories(validator))) == expected


def test_staged_run_with_nothing_staged_reports_nothing(tmp_path, monkeypatch):
    write_tree(tmp_path, _DESCRIPTOR_CASES["duplicate and out of sync"][0])
    monkeypatch.setenv("MD_STAGED_FILES", "")
    validator = build_validator(V.Validator, tmp_path, staged_only=True)
    validator.run_validations()
    assert validator._issues == []


def test_strict_cli_exits_nonzero_for_findings(tmp_path, monkeypatch):
    write_tree(
        tmp_path,
        {
            "descriptor.mod": 'replace_path = "a"\n',
            "Millennium_Dawn.mod": 'replace_path = "b"\n',
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_mod_descriptors.py", "--path", str(tmp_path), "--strict"],
    )
    with pytest.raises(SystemExit) as result:
        run_validator_main(V.Validator, "descriptors")
    assert result.value.code == 1
