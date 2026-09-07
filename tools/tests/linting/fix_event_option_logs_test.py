"""Behavioral tests for tools/linting/fix_event_option_logs.py.

Deletes `log = "..."` lines from event options that run no effects. Tests use
real fixtures so the detector/writer pipeline is exercised, not mocked.
"""

import subprocess
import sys
from pathlib import Path

_CLI = Path(__file__).resolve().parents[2] / "linting" / "fix_event_option_logs.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")


def _events_tree(tmp_path: Path) -> Path:
    root = tmp_path / "mod"
    (root / "events").mkdir(parents=True)
    return root


def _event(option_body: str) -> str:
    return (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n" + option_body + "\t}\n"
        "}\n"
    )


_LOG = '\t\tlog = "[GetDateText]: [This.GetName]: foo.1.a executed"\n'


def test_is_event_file_accepts_only_events():
    from fix_event_option_logs import _is_event_file

    assert _is_event_file("events/Russia.txt")
    assert _is_event_file("events\\Russia.txt")
    assert not _is_event_file("common/decisions/x.txt")


def test_apply_removes_the_dead_log_line(tmp_path):
    from fix_event_option_logs import fix_file

    root = _events_tree(tmp_path)
    event = root / "events" / "Ev.txt"
    _write(event, _event("\t\tname = foo.1.a\n" + _LOG))

    path, count = fix_file(str(event))
    assert path == str(event)
    assert count == 1
    body = event.read_text(encoding="utf-8")
    assert "log =" not in body
    assert "name = foo.1.a" in body


def test_apply_leaves_options_with_effects_alone(tmp_path):
    from fix_event_option_logs import fix_file

    root = _events_tree(tmp_path)
    event = root / "events" / "Ev.txt"
    original = _event("\t\tname = foo.1.a\n" + _LOG + "\t\tadd_political_power = 10\n")
    _write(event, original)

    path, count = fix_file(str(event))
    assert count == 0
    assert event.read_text(encoding="utf-8") == original


def test_apply_removes_both_logs_of_a_two_log_option(tmp_path):
    from fix_event_option_logs import fix_file

    root = _events_tree(tmp_path)
    event = root / "events" / "Ev.txt"
    _write(event, _event("\t\tname = foo.1.a\n" + _LOG + _LOG))

    _path, count = fix_file(str(event))
    assert count == 2
    assert "log =" not in event.read_text(encoding="utf-8")


def test_apply_dry_run_does_not_write(tmp_path):
    from fix_event_option_logs import fix_file_dry_run

    root = _events_tree(tmp_path)
    event = root / "events" / "Ev.txt"
    original = _event("\t\tname = foo.1.a\n" + _LOG)
    _write(event, original)

    path, count = fix_file_dry_run(str(event))
    assert path == str(event)
    assert count == 1
    assert event.read_text(encoding="utf-8") == original


def test_non_event_path_is_skipped(tmp_path):
    from fix_event_option_logs import fix_file

    root = tmp_path / "mod" / "common" / "decisions"
    decision = root / "x.txt"
    _write(decision, _event("\t\tname = foo.1.a\n" + _LOG))

    _path, count = fix_file(str(decision))
    assert count == 0
    assert "log =" in decision.read_text(encoding="utf-8")


def test_cli_dry_run_reports_completion(tmp_path):
    # The CLI walks the whole mod tree (--root is derived from the script path),
    # so this only pins the entry point, not a per-fixture count.
    root = _events_tree(tmp_path)
    _write(root / "events" / "Ev.txt", _event("\t\tname = foo.1.a\n"))

    result = subprocess.run(
        [sys.executable, str(_CLI), "--mode", "all", "--dry-run", "--workers", "1"],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    assert "Fix Event Option Logs" in result.stdout
