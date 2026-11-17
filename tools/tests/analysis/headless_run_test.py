"""Behavioral tests for tools/analysis/headless_run.py."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.analysis import headless_run  # noqa: E402

_WAR_LINE = "CHI = { declare_war_on = { target = RAJ type = annex_everything } }"

# case: (file present before, arguments, exit code, file checked, text it must hold or None for absent)
_SETUP_CASES = {
    "bench on": (
        None,
        ["bench", "on"],
        0,
        headless_run.BENCH_FILE,
        "set_global_flag = md_benchmark_logging",
    ),
    "bench off": (
        headless_run.BENCH_FILE,
        ["bench", "off"],
        0,
        headless_run.BENCH_FILE,
        None,
    ),
    "war add": (None, ["war", "add", "CHI:RAJ"], 0, headless_run.WAR_FILE, _WAR_LINE),
    "war add rejects a bad pair": (
        None,
        ["war", "add", "CHI-RAJ"],
        1,
        headless_run.WAR_FILE,
        None,
    ),
    "war add needs a pair": (None, ["war", "add"], 1, headless_run.WAR_FILE, None),
    "war remove": (
        headless_run.WAR_FILE,
        ["war", "remove"],
        0,
        headless_run.WAR_FILE,
        None,
    ),
}


@pytest.mark.parametrize(
    "existing, args, code, checked, text", _SETUP_CASES.values(), ids=_SETUP_CASES
)
def test_setup(tmp_path, monkeypatch, existing, args, code, checked, text):
    (tmp_path / "common" / "on_actions").mkdir(parents=True)
    if existing:
        with open(tmp_path / existing, "w", encoding="utf-8", newline="") as handle:
            handle.write("on_actions = {\n}\n")
    monkeypatch.setattr(
        sys, "argv", ["headless_run.py", "--path", str(tmp_path), *args]
    )
    assert headless_run.main() == code
    path = tmp_path / checked
    if text is None:
        assert not path.exists()
    else:
        assert text in path.read_text(encoding="utf-8")
        assert path.read_text(encoding="utf-8").startswith(
            "on_actions = {\n\ton_startup = {"
        )


# case: (files in the HOI4 user folder, exit code, files the run folder must hold)
_SAVE_CASES = {
    "copies logs and the newest save": (
        [
            "logs/game.log",
            "logs/error.log",
            "save games/old.hoi4",
            "save games/new.hoi4",
        ],
        0,
        ["game.log", "error.log", "new.hoi4"],
    ),
    "missing log": (["logs/game.log", "save games/new.hoi4"], 1, []),
}


@pytest.mark.parametrize("present, code, copied", _SAVE_CASES.values(), ids=_SAVE_CASES)
def test_save(tmp_path, monkeypatch, present, code, copied):
    user = tmp_path / "user"
    for age, name in enumerate(reversed(present)):
        path = user / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(name)
        os.utime(path, (1_000_000 - age, 1_000_000 - age))
    run = tmp_path / "run"
    argv = ["headless_run.py", "save", str(run), "--user-dir", str(user)]
    monkeypatch.setattr(sys, "argv", argv)
    assert headless_run.main() == code
    held = sorted(os.listdir(run)) if run.exists() else []
    assert held == sorted(copied)
