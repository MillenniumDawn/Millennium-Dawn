"""Tests for the HOI4 run reporter.

The behaviour that matters most is the partial-read guard: error.log is written
progressively during load, so a report taken while the game is still running can
look clean minutes before the errors arrive.
"""

import json
import sys
from pathlib import Path

# Make tools/analysis importable for `import hoi4_run_report`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import hoi4_run_report as rr

LOG = (
    "[22:10:49][no_game_date][dlc.cpp:218]: Invalid supported_version in  "
    "file: mod/ugc_2243912940.mod line: 10\n"
    "[22:10:59][no_game_date][pdx_audio.cpp:1294]: Music with name 'X' already added\n"
    "[22:11:45][no_game_date][parser.cpp:1111]: Error: unexpected token in "
    'file: "common/scripted_effects/85_top.txt" near line: 136 ( } )\n'
    "[22:11:45][no_game_date][parser.cpp:1111]: Error: unexpected token in "
    'file: "common/scripted_effects/85_top.txt" near line: 143 ( } )\n'
    "[22:12:00][no_game_date][trigger.cpp:700]: Invalid trigger 'TARGET' in "
    "common/scripted_triggers/80_top.txt line : 110\n"
    '[22:12:30][2001.10.25.17][icon_entry.cpp:38]: Icon definition "" is bad\n'
)


def _write(tmp_path, text=LOG):
    path = tmp_path / "error.log"
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return str(path)


def test_third_party_noise_is_separated_from_mod_errors(tmp_path):
    report = rr.parse(_write(tmp_path))

    # the ugc line is evidenced third-party; the audio line is unattributed
    assert report["third_party"] == 1
    assert report["audio"] == 1
    assert report["mod_errors"] == 4
    assert report["span"] == ("22:10:49", "22:12:30")


def test_a_dated_line_counts_as_a_runtime_error(tmp_path):
    """`no_game_date` is load time; anything else happened in play."""
    report = rr.parse(_write(tmp_path))

    assert report["runtime_errors"] == 1


def test_errors_group_by_originating_file(tmp_path):
    report = rr.parse(_write(tmp_path))

    assert report["by_file"]["common/scripted_effects/85_top.txt"] == 2
    assert report["by_file"]["common/scripted_triggers/80_top.txt"] == 1


def test_repeats_collapse_to_one_shape(tmp_path):
    """Two identical errors differing only by line number are one shape."""
    report = rr.parse(_write(tmp_path))
    shapes = report["by_shape"]

    parser_shapes = [k for k in shapes if "parser.cpp:1111" in k]
    assert len(parser_shapes) == 1
    assert shapes[parser_shapes[0]] == 2


def test_a_running_game_makes_the_report_partial(tmp_path, monkeypatch, capsys):
    """This is the guard: a partial log can look clean. Exit 2, never 0."""
    monkeypatch.setattr(rr, "hoi4_is_running", lambda: True)
    path = _write(tmp_path, "")

    code = rr.main(["--log", path])

    assert code == 2
    assert "still being written" in capsys.readouterr().err


def test_a_clean_log_from_a_finished_run_exits_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(rr, "hoi4_is_running", lambda: False)
    path = _write(tmp_path, "")

    assert rr.main(["--log", path]) == 0


def test_mod_errors_from_a_finished_run_exit_one(tmp_path, monkeypatch):
    monkeypatch.setattr(rr, "hoi4_is_running", lambda: False)

    assert rr.main(["--log", _write(tmp_path)]) == 1


def test_baseline_round_trip_reports_the_delta(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rr, "hoi4_is_running", lambda: False)
    baseline = tmp_path / "base.json"
    rr.main(["--log", _write(tmp_path), "--save-baseline", str(baseline)])
    capsys.readouterr()

    # a second run with one file's errors gone
    shorter = LOG.replace(
        "[22:11:45][no_game_date][parser.cpp:1111]: Error: unexpected token in "
        'file: "common/scripted_effects/85_top.txt" near line: 143 ( } )\n',
        "",
    )
    rr.main(["--log", _write(tmp_path, shorter), "--baseline", str(baseline)])

    out = capsys.readouterr().out
    assert "vs baseline" in out
    assert "-1" in out and "85_top.txt" in out


def test_wait_returns_immediately_when_nothing_is_running(monkeypatch):
    monkeypatch.setattr(rr, "hoi4_is_running", lambda: False)

    exited, note = rr.wait_for_exit(timeout=1.0)

    assert exited is True
    assert "not running" in note


def test_saved_baseline_is_valid_json(tmp_path, monkeypatch):
    monkeypatch.setattr(rr, "hoi4_is_running", lambda: False)
    out = tmp_path / "b.json"
    rr.main(["--log", _write(tmp_path), "--save-baseline", str(out)])

    with open(out, encoding="utf-8") as handle:
        assert json.load(handle)["mod_errors"] == 4


def test_an_audio_error_without_third_party_evidence_is_not_dropped(tmp_path):
    """Matching the audio subsystem alone would hide a mod-owned audio error."""
    log = (
        "[10:00:00][no_game_date][pdx_audio.cpp:1294]: Music with name "
        "'MD_theme' already added\n"
    )
    report = rr.parse(_write(tmp_path, log))

    assert report["third_party"] == 0
    assert report["audio"] == 1


def test_a_run_with_only_audio_errors_does_not_read_as_clean(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(rr, "hoi4_is_running", lambda: False)
    log = (
        "[10:00:00][no_game_date][pdx_audio.cpp:1294]: Music with name "
        "'MD_theme' already added\n"
    )
    rr.main(["--log", _write(tmp_path, log)])

    out = capsys.readouterr().out
    assert "could not be attributed" in out
    assert "No mod errors." not in out


def test_a_ugc_line_is_still_dropped_as_third_party(tmp_path):
    log = (
        "[10:00:00][no_game_date][dlc.cpp:218]: Invalid supported_version in  "
        "file: mod/ugc_2243912940.mod line: 10\n"
    )
    report = rr.parse(_write(tmp_path, log))

    assert report["third_party"] == 1
    assert report["audio"] == 0
    assert report["mod_errors"] == 0
