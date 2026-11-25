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
        "set_global_flag = GLOBAL_md_benchmark_logging",
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


def _put(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _run_in(mod: Path, monkeypatch, args) -> int:
    (mod / "common" / "on_actions").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sys, "argv", ["headless_run.py", "--path", str(mod), *args])
    return headless_run.main()


# case: (file present before, arguments, exit code, fragments in order, fragments absent)
# fragments None means the file must be absent afterwards
_PROBE_CASES = {
    "add logs stats monthly": (
        False,
        ["probe", "add", "ABC"],
        0,
        ["on_monthly_ABC = {", "FAKE_STATS"],
        ["FAKE_INFRA", "probe_months"],
    ),
    "add takes several kinds in order": (
        False,
        ["probe", "add", "ABC", "--kind", "stats", "infrastructure"],
        0,
        ["FAKE_STATS", "FAKE_INFRA"],
        ["probe_months"],
    ),
    "add yearly wraps the body in the month gate": (
        False,
        ["probe", "add", "ABC", "--every", "year"],
        0,
        [
            "\n\t\t\tadd_to_variable = { probe_months = 1 }\n",
            "\n\t\t\tif = {\n",
            "\n\t\t\t\tlimit = { check_variable = { probe_months > 11 } }\n",
            '\n\t\t\t\tlog = "FAKE_STATS"\n',
            "\n\t\t\t}\n\t\t}\n",
        ],
        ["FAKE_INFRA", '\n\t\t\tlog = "FAKE_STATS"'],
    ),
    "add rejects a bad tag": (False, ["probe", "add", "abc"], 1, None, None),
    "add needs a tag": (False, ["probe", "add"], 1, None, None),
    "remove": (True, ["probe", "remove"], 0, None, None),
}


@pytest.mark.parametrize(
    "existing, args, code, present, absent", _PROBE_CASES.values(), ids=_PROBE_CASES
)
def test_probe(tmp_path, monkeypatch, existing, args, code, present, absent):
    probes = tmp_path / "probes"
    _put(probes / "country_stats.txt", 'log = "FAKE_STATS"\n')
    _put(probes / "state_infrastructure.txt", 'log = "FAKE_INFRA"\n')
    monkeypatch.setattr(headless_run, "PROBE_DIR", str(probes))
    mod = tmp_path / "mod"
    if existing:
        _put(mod / headless_run.PROBE_FILE, "on_actions = {\n}\n")
    assert _run_in(mod, monkeypatch, args) == code
    path = mod / headless_run.PROBE_FILE
    if present is None:
        assert not path.exists()
        return
    text = path.read_text(encoding="utf-8")
    assert text.startswith("on_actions = {\n\ton_monthly_ABC = {")
    assert text.count("{") == text.count("}")
    position = 0
    for fragment in present:
        position = text.find(fragment, position)
        assert position >= 0, fragment
    for fragment in absent:
        assert fragment not in text


@pytest.mark.parametrize("every", ["month", "year"])
def test_probe_real_files(tmp_path, monkeypatch, every):
    args = [
        "probe",
        "add",
        "ABC",
        "--every",
        every,
        "--kind",
        *headless_run.PROBE_KINDS,
    ]
    assert _run_in(tmp_path, monkeypatch, args) == 0
    text = (tmp_path / headless_run.PROBE_FILE).read_text(encoding="utf-8")
    assert text.count("{") == text.count("}")
    body = text.splitlines()[3:-3]  # inside `effect = { ... }`
    if every == "year":
        assert body[:2] == [
            "\t\t\tadd_to_variable = { probe_months = 1 }",
            "\t\t\tif = {",
        ]
        assert body[-1] == "\t\t\t}"
        body = body[2:-1]
        assert all(line.startswith("\t\t\t\t") for line in body)
    assert sum('log = "PROBE_' in line for line in body) == len(
        headless_run.PROBE_KINDS
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
