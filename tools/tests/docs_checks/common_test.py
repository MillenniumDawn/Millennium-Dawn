"""Shared docs check helpers: running a command and listing Markdown files."""

import subprocess
from pathlib import Path

import pytest
from shared.suite import write_text

import common


def _completed(returncode, stdout, stderr):
    return lambda cmd, **_kwargs: subprocess.CompletedProcess(
        cmd, returncode, stdout, stderr
    )


def _raises(error):
    def run(*_args, **_kwargs):
        raise error

    return run


@pytest.mark.parametrize(
    ("run", "passed", "output"),
    [
        pytest.param(_completed(0, "ok\n", ""), True, "ok", id="exit 0"),
        pytest.param(
            _completed(3, "out\n", "err\n"), False, "out\nerr", id="nonzero exit"
        ),
        pytest.param(
            _raises(FileNotFoundError()), False, "command not found: tool", id="no tool"
        ),
        pytest.param(
            _raises(subprocess.TimeoutExpired(["tool"], 2.5)),
            False,
            "timed out after 2s",
            id="timeout",
        ),
    ],
)
def test_run_cmd_turns_the_outcome_into_a_result(monkeypatch, run, passed, output):
    monkeypatch.setattr(common.subprocess, "run", run)

    result = common.run_cmd("check", ["tool"], timeout=2.5)

    assert (result.name, result.passed, result.output) == ("check", passed, output)


def test_run_cmd_runs_the_command_in_the_given_directory(monkeypatch):
    calls = []
    monkeypatch.setattr(
        common.subprocess,
        "run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or _completed(0, "", "")(cmd),
    )

    common.run_cmd("check", ["tool", "--flag"], Path("work"), 2.5)

    assert calls == [
        (
            ["tool", "--flag"],
            {"capture_output": True, "text": True, "cwd": Path("work"), "timeout": 2.5},
        )
    ]


def test_iter_markdown_lists_each_file_once_in_a_stable_order(tmp_path, monkeypatch):
    late, early, other = (
        write_text(tmp_path / name, "") for name in ("z.md", "a.md", "b.mdx")
    )
    # The second pattern matches the .md files again.
    monkeypatch.setattr(common, "MARKDOWN_GLOBS", ("**/*.md", "**/*.md*"))

    assert list(common.iter_markdown(tmp_path)) == [early, late, other]
