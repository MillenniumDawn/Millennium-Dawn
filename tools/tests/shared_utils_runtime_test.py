"""Unit tests for the runtime plumbing in shared_utils: the worker budget,
logging, timing, the argument parsers, file collection by mode, the process
pool and run_validator_main."""

import argparse
import multiprocessing
import os
import sys
from types import SimpleNamespace

import pytest
import shared_utils as U
from shared.suite import write_text as _write

# ---- worker budget -----------------------------------------------------------


# case: (MD_MAX_WORKERS, CI, budget)
_BUDGET_CASES = {
    "explicit override": ("4", None, 4),
    "local run keeps two cores free": ("0", None, 6),
    "CI uses every core": ("0", "true", 8),
    "unparsable override is ignored": ("not-a-number", "true", 8),
}


@pytest.mark.parametrize(
    ("workers", "ci", "expected"), _BUDGET_CASES.values(), ids=_BUDGET_CASES
)
def test_cpu_budget(monkeypatch, workers, ci, expected):
    monkeypatch.setenv("MD_MAX_WORKERS", workers)
    monkeypatch.setattr(U.os, "cpu_count", lambda: 8)
    if ci is None:
        monkeypatch.delenv("CI", raising=False)
    else:
        monkeypatch.setenv("CI", ci)
    assert U.cpu_budget() == expected


@pytest.mark.parametrize("share, expected", [(3, (3, 2)), (0, (1, 6))])
def test_split_cpu_budget(monkeypatch, share, expected):
    monkeypatch.setenv("MD_MAX_WORKERS", "0")
    monkeypatch.setattr(U.os, "cpu_count", lambda: 8)
    monkeypatch.delenv("CI", raising=False)
    assert U.split_cpu_budget(share) == expected


# ---- logging and timing ------------------------------------------------------


def test_debug_messages_are_hidden(capsys):
    U.log_message("DEBUG", "hidden")
    assert capsys.readouterr().err == ""


def test_no_color_env_drops_colour_codes(monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "1")
    U.log_message("INFO", "visible")
    U.log_message("NOTICE", "unknown", use_colors=False)
    captured = capsys.readouterr().err
    assert "INFO: visible" in captured
    assert "NOTICE: unknown" in captured
    assert "\033[" not in captured


def test_timing_disabled_prints_nothing(monkeypatch, capsys):
    monkeypatch.setenv("MD_TIMING", "0")
    assert not U.timing_enabled()
    assert U.Timer("disabled").enabled is False
    assert U.Timer("manual", enabled=False).stop() == 0.0
    U.print_timing_summary([])
    U.print_timing_summary([("step", 1.0)])
    assert capsys.readouterr().err == ""


def test_timing_summary_prints_when_enabled(capsys):
    with U.Timer("context", enabled=True):
        pass
    U.print_timing_summary([("first", 0.0), ("second", 1.0)])
    assert "Timing summary" in capsys.readouterr().err


# ---- argument parsers --------------------------------------------------------


def test_standard_file_arguments():
    parser = argparse.ArgumentParser()
    U.add_standard_file_arguments(parser, input_help="Custom input")
    assert "Custom input" in parser.format_help()
    parsed = parser.parse_args(["source.txt", "-o", "dest.txt", "-b", "-v"])
    assert (parsed.input_file, parsed.output, parsed.backup, parsed.verbose) == (
        "source.txt",
        "dest.txt",
        True,
        True,
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["source.txt", "--no-color"])


def test_validation_parser():
    parsed = U.create_validation_parser("validation").parse_args(
        ["--path", "/mod", "--strict", "--staged", "--no-cache", "--workers", "2"]
    )
    assert (parsed.path, parsed.strict, parsed.staged, parsed.no_cache) == (
        "/mod",
        True,
        True,
        True,
    )
    assert parsed.workers == 2


def test_linting_parser_takes_extra_arguments_and_can_drop_diff_mode():
    def add_extra(parser):
        parser.add_argument("--extra", action="store_true")

    lint = U.create_linting_parser("lint", include_diff=False, extra_args_fn=add_extra)
    parsed = lint.parse_args(["--mode", "staged", "--files", "x.txt", "--extra"])
    assert (parsed.mode, parsed.files, parsed.extra) == ("staged", ["x.txt"], True)
    with pytest.raises(SystemExit):
        lint.parse_args(["--mode", "diff"])


# ---- file collection by mode -------------------------------------------------


def test_named_files_that_are_missing_are_warned_about(tmp_path, capsys):
    existing = _write(tmp_path / "one.txt", "x")
    args = SimpleNamespace(
        filenames=[str(existing), str(tmp_path / "gone.txt")], files=None, mode="all"
    )
    assert U.collect_files_by_mode(args, str(tmp_path)) == [str(existing)]
    assert "not found" in capsys.readouterr().out


# case: (mode, --files given, include_interface, git diff call expected)
_MODE_CASES = {
    "explicit files skip git": ("all", True, False, None),
    "diff mode": (
        "diff",
        False,
        False,
        {"base_branch": "release", "include_interface": False},
    ),
    "staged mode": (
        "staged",
        False,
        True,
        {"staged_only": True, "include_interface": True},
    ),
}


@pytest.mark.parametrize(
    ("mode", "files", "include_interface", "call"),
    _MODE_CASES.values(),
    ids=_MODE_CASES,
)
def test_collect_files_by_mode(
    tmp_path, monkeypatch, mode, files, include_interface, call
):
    existing = str(_write(tmp_path / "one.txt", "x"))
    calls = []
    monkeypatch.setattr(
        U, "get_git_diff_files", lambda **kwargs: calls.append(kwargs) or [existing]
    )
    args = SimpleNamespace(
        filenames=[],
        files=[existing] if files else None,
        mode=mode,
        base_branch="release",
    )
    assert U.collect_files_by_mode(
        args, str(tmp_path), include_interface=include_interface
    ) == [existing]
    assert calls == ([] if call is None else [call])


def test_all_mode_walks_the_tree(tmp_path, monkeypatch):
    existing = str(_write(tmp_path / "one.txt", "x"))
    monkeypatch.setattr(U, "get_all_txt_files", lambda root, **kwargs: [existing])
    args = SimpleNamespace(filenames=[], files=None, mode="all")
    assert U.collect_files_by_mode(args, str(tmp_path)) == [existing]


# ---- process pool ------------------------------------------------------------


@pytest.mark.parametrize(
    "items, workers", [(["a", "b"], 1), ([], 4)], ids=["one worker", "no items"]
)
def test_run_with_pool_runs_in_process(items, workers):
    assert U.run_with_pool(str.upper, items, workers=workers) == [
        item.upper() for item in items
    ]


class _FakePool:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def map(self, func, items, **kwargs):
        self.map_kwargs = kwargs
        return [func(item) for item in items]


@pytest.mark.parametrize("chunksize", [3, None], ids=["given", "computed"])
def test_run_with_pool_maps_over_a_pool(monkeypatch, chunksize):
    monkeypatch.setattr(multiprocessing, "Pool", _FakePool)
    kwargs = {} if chunksize is None else {"chunksize": chunksize}
    assert U.run_with_pool(str.upper, list("abcdefghij"), workers=2, **kwargs) == list(
        "ABCDEFGHIJ"
    )


# ---- run_validator_main ------------------------------------------------------


class _FailingValidator:
    created = {}

    def __init__(self, mod_path, **kwargs):
        _FailingValidator.created = {"path": mod_path, "kwargs": kwargs}

    def run_all_validations(self):
        return 1


class _CleanValidator:
    def __init__(self, *_args, **_kwargs):
        pass

    def run_all_validations(self):
        return 0


def test_strict_run_with_findings_exits_one_and_passes_the_arguments(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)

    def extra(parser):
        parser.add_argument("--flavor", default="plain")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validator",
            "--path",
            str(tmp_path),
            "--strict",
            "--no-cache",
            "--flavor",
            "fast",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(_FailingValidator, extra_args_fn=extra)
    assert exc.value.code == 1
    created = _FailingValidator.created
    assert created["path"] == str(tmp_path.resolve())
    assert (created["kwargs"]["flavor"], created["kwargs"]["no_cache"]) == (
        "fast",
        True,
    )
    assert os.environ["MD_NO_CACHE"] == "1"


# case: (path under tmp_path, validator, exit code)
_MAIN_PATH_CASES = {
    "a file, not a directory": ("not-a-dir", _CleanValidator, 1),
    "a missing path": ("gone", _CleanValidator, 1),
    "a clean run": (".", _CleanValidator, 0),
}


@pytest.mark.parametrize(
    ("path", "validator", "code"), _MAIN_PATH_CASES.values(), ids=_MAIN_PATH_CASES
)
def test_run_validator_main_exit_codes(tmp_path, monkeypatch, path, validator, code):
    _write(tmp_path / "not-a-dir", "x")
    monkeypatch.setattr(sys, "argv", ["validator", "--path", str(tmp_path / path)])
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(validator)
    assert exc.value.code == code
