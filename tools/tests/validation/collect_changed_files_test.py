"""Tests for the `git diff --name-status -z` parser behind CI change detection.

A misread record shifts every later field, so a changed file can drop out of
the impact selection and its validator never runs.
"""

import io
import os
from types import SimpleNamespace

import collect_changed_files
import pytest
from collect_changed_files import parse_name_status


@pytest.mark.parametrize(
    "data, expected",
    [
        pytest.param(b"", [], id="empty"),
        pytest.param(b"M\0common/a.txt\0", ["common/a.txt"], id="modified"),
        pytest.param(b"M\0common/a.txt", ["common/a.txt"], id="no-trailing-nul"),
        pytest.param(
            b"R100\0old.txt\0new.txt\0", ["old.txt", "new.txt"], id="rename-keeps-both"
        ),
        pytest.param(
            b"C075\0src.txt\0copy.txt\0", ["src.txt", "copy.txt"], id="copy-keeps-both"
        ),
        pytest.param(
            b"M\0a.txt\0R090\0b.txt\0c.txt\0A\0d.txt\0D\0e.txt\0",
            ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"],
            id="records-after-a-rename-stay-aligned",
        ),
        pytest.param(
            b"M\0README.md\0A\0Changelog.txt\0",
            ["README.md", "Changelog.txt"],
            id="path-starting-with-r-or-c-is-not-a-status",
        ),
        pytest.param(
            b"A\0events/caf\xc3\xa9 one.txt\0",
            ["events/café one.txt"],
            id="utf8-and-spaces",
        ),
        pytest.param(b"A\0bad\xff.txt\0", ["bad�.txt"], id="invalid-utf8"),
    ],
)
def test_name_status_records_become_paths(data, expected):
    assert parse_name_status(data) == expected


def test_main_writes_one_path_per_line_with_bare_newlines(tmp_path, monkeypatch):
    out = tmp_path / "changed-files.txt"
    with open(out, "wb") as sink, monkeypatch.context() as patch:
        patch.setattr(
            collect_changed_files.sys,
            "stdin",
            SimpleNamespace(buffer=io.BytesIO(b"R100\0old.txt\0new.txt\0")),
        )
        # main() closes the descriptor it writes to, so hand it a duplicate.
        patch.setattr(
            collect_changed_files.sys,
            "stdout",
            SimpleNamespace(fileno=lambda: os.dup(sink.fileno())),
        )
        assert collect_changed_files.main() == 0

    assert out.read_bytes() == b"old.txt\nnew.txt\n"
