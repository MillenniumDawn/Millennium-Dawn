"""Tests for the nightly `baseline_check` CLI."""

import builtins
import json

import baseline_check
from report_lib import load_baseline
from report_lib.baseline import META_FILENAME
from shared.suite import issue_dict as _issue_dict
from shared.suite import write_slug_json as _write_sidecar


def _write_meta(base, toolshash="h"):
    base.mkdir(parents=True, exist_ok=True)
    (base / META_FILENAME).write_text(
        json.dumps({"toolshash": toolshash}), encoding="utf-8"
    )


def _previous_with_one_old_error(tmp_path):
    previous = tmp_path / "prev"
    _write_meta(previous)
    _write_sidecar(previous, "events", [_issue_dict("error", message="old")])
    return previous


def _identical_previous_and_current(tmp_path):
    previous = _previous_with_one_old_error(tmp_path)
    current = tmp_path / "current"
    _write_sidecar(current, "events", [_issue_dict("error", message="old")])
    return previous, current


def _run(
    tmp_path, previous, current, toolshash="h", monkeypatch=None, summary_path=None
):
    if monkeypatch is not None:
        if summary_path is None:
            # No summary requested: exercise the real no-op path rather
            # than mocking the writer away.
            monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        else:
            # Keep the real writer: the step summary is the nightly alarm's
            # only human-readable output, so tests assert its content.
            monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    argv = [
        "--previous",
        str(previous),
        "--current",
        str(current),
        "--output",
        str(tmp_path / "baseline"),
        "--toolshash",
        toolshash,
        "--commit-sha",
        "abc1234deadbeef",  # pragma: allowlist secret
    ]
    return baseline_check.main(argv)


def test_empty_candidate_establishes_clean_baseline(tmp_path, monkeypatch, capsys):
    current = tmp_path / "current"
    current.mkdir()

    code = _run(
        tmp_path, tmp_path / "no-such-baseline", current, monkeypatch=monkeypatch
    )

    assert code == 0
    assert (tmp_path / "baseline" / META_FILENAME).is_file()
    assert "0 issue(s)" in capsys.readouterr().out


def test_missing_candidate_directory_fails(tmp_path, monkeypatch, capsys):
    code = _run(
        tmp_path,
        tmp_path / "no-such-baseline",
        tmp_path / "missing",
        monkeypatch=monkeypatch,
    )

    assert code == 1
    assert "--current directory does not exist" in capsys.readouterr().err


def test_establishing_baseline_when_previous_missing(tmp_path, monkeypatch, capsys):
    current = tmp_path / "current"
    _write_sidecar(current, "events", [_issue_dict("error")])

    code = _run(
        tmp_path, tmp_path / "no-such-baseline", current, monkeypatch=monkeypatch
    )

    assert code == 0
    assert "established" in capsys.readouterr().out
    assert (tmp_path / "baseline" / META_FILENAME).is_file()
    assert (tmp_path / "baseline" / "events.json").is_file()
    # The real _build_meta ran: the persisted meta carries the hash the
    # PR-side load_baseline will later verify against.
    meta = json.loads(
        (tmp_path / "baseline" / META_FILENAME).read_text(encoding="utf-8")
    )
    assert meta["toolshash"] == "h"


def test_new_errors_fail_and_keep_old_baseline(tmp_path, monkeypatch, capsys):
    previous = _previous_with_one_old_error(tmp_path)
    current = tmp_path / "current"
    _write_sidecar(
        current,
        "events",
        [
            _issue_dict("error", message="old"),
            _issue_dict("error", message="brand new", file="b.txt", line=2),
        ],
    )

    code = _run(tmp_path, previous, current, monkeypatch=monkeypatch)

    assert code == 1
    assert "1 new error(s)" in capsys.readouterr().err
    # Red night: the old baseline stays; nothing is written to --output.
    assert not (tmp_path / "baseline" / META_FILENAME).exists()


def test_clean_diff_promotes_baseline(tmp_path, monkeypatch, capsys):
    previous, current = _identical_previous_and_current(tmp_path)

    code = _run(tmp_path, previous, current, monkeypatch=monkeypatch)

    assert code == 0
    assert (tmp_path / "baseline" / META_FILENAME).is_file()
    assert "baseline updated" in capsys.readouterr().out


def test_all_clean_night_promotes_empty_baseline(tmp_path, monkeypatch, capsys):
    # A fully clean suite writes no sidecars at all. That is the empty
    # findings set, not a crash: the previous baseline (with findings)
    # collapses to meta-only and the fixed counts are reported.
    previous = tmp_path / "prev"
    _write_meta(previous)
    _write_sidecar(previous, "events", [_issue_dict("error", message="old")])
    current = tmp_path / "current"
    current.mkdir()

    code = _run(tmp_path, previous, current, monkeypatch=monkeypatch)

    assert code == 0
    assert (tmp_path / "baseline" / META_FILENAME).is_file()
    assert not (tmp_path / "baseline" / "events.json").exists()
    assert "1 error(s), 0 warning(s) fixed" in capsys.readouterr().out


def test_fixed_errors_still_promote(tmp_path, monkeypatch, capsys):
    previous = tmp_path / "prev"
    _write_meta(previous)
    _write_sidecar(
        previous,
        "events",
        [_issue_dict("error", message="old"), _issue_dict("error", message="fixed")],
    )
    current = tmp_path / "current"
    _write_sidecar(current, "events", [_issue_dict("error", message="old")])

    code = _run(tmp_path, previous, current, monkeypatch=monkeypatch)

    assert code == 0
    assert "1 error(s), 0 warning(s) fixed" in capsys.readouterr().out
    assert (tmp_path / "baseline" / META_FILENAME).is_file()


def test_red_night_step_summary_reports_new_errors(tmp_path, monkeypatch):
    previous = tmp_path / "prev"
    _write_meta(previous)
    current = tmp_path / "current"
    _write_sidecar(
        current,
        "events",
        [_issue_dict("error", file="b.txt", line=2, message="brand new")],
    )
    summary_path = tmp_path / "summary.md"

    code = _run(
        tmp_path,
        previous,
        current,
        monkeypatch=monkeypatch,
        summary_path=summary_path,
    )

    assert code == 1
    summary = summary_path.read_text(encoding="utf-8")
    assert "New errors on main — baseline not updated." in summary
    assert "`b.txt:2` — brand new" in summary


def test_clean_night_step_summary_confirms_update(tmp_path, monkeypatch):
    previous, current = _identical_previous_and_current(tmp_path)
    summary_path = tmp_path / "summary.md"

    code = _run(
        tmp_path,
        previous,
        current,
        monkeypatch=monkeypatch,
        summary_path=summary_path,
    )

    assert code == 0
    summary = summary_path.read_text(encoding="utf-8")
    assert "✅ No new errors — baseline updated to tonight's results." in summary


def test_step_summary_caps_new_findings_lists(tmp_path, monkeypatch):
    previous = tmp_path / "prev"
    _write_meta(previous)
    current = tmp_path / "current"
    issues = [
        _issue_dict("warning", file="w.txt", line=n, message=f"warning {n}")
        for n in range(1, baseline_check.MAX_LISTED + 2)
    ]
    _write_sidecar(current, "events", issues)
    summary_path = tmp_path / "summary.md"

    code = _run(
        tmp_path,
        previous,
        current,
        monkeypatch=monkeypatch,
        summary_path=summary_path,
    )

    assert code == 0
    summary = summary_path.read_text(encoding="utf-8")
    assert "_…and 1 more._" in summary
    assert summary.count("- ⚠️ `w.txt:") == baseline_check.MAX_LISTED


def test_issue_line_renders_fallback_locations():
    no_line = baseline_check.Issue.from_dict(
        {"severity": "error", "category": "c", "message": "m", "file": "f.txt"}
    )
    assert baseline_check._issue_line(no_line) == "- ❌ `f.txt` — m"

    no_file = baseline_check.Issue.from_dict(
        {"severity": "warning", "category": "c", "message": "m"}
    )
    assert baseline_check._issue_line(no_file) == "- ⚠️ _(no location)_ — m"


def test_new_warnings_do_not_fail(tmp_path, monkeypatch, capsys):
    previous = tmp_path / "prev"
    _write_meta(previous)
    current = tmp_path / "current"
    _write_sidecar(current, "events", [_issue_dict("warning", message="new warn")])

    code = _run(tmp_path, previous, current, monkeypatch=monkeypatch)

    assert code == 0
    assert "1 new warning(s)" in capsys.readouterr().out
    assert (tmp_path / "baseline" / META_FILENAME).is_file()


def test_toolshash_mismatch_reestablishes(tmp_path, monkeypatch, capsys):
    previous = tmp_path / "prev"
    _write_meta(previous, toolshash="old-generation")
    current = tmp_path / "current"
    _write_sidecar(current, "events", [_issue_dict("error", message="old")])

    code = _run(
        tmp_path, previous, current, toolshash="new-gen", monkeypatch=monkeypatch
    )

    assert code == 0
    assert "established" in capsys.readouterr().out


def test_missing_current_dir_fails(tmp_path, monkeypatch, capsys):
    code = _run(tmp_path, tmp_path / "prev", tmp_path / "no-such-dir")
    assert code == 1
    assert "does not exist" in capsys.readouterr().err


def test_split_new_findings(tmp_path):
    previous = tmp_path / "prev"
    _write_meta(previous)
    _write_sidecar(previous, "events", [_issue_dict("error", message="old")])
    baseline = load_baseline(str(previous), "h")
    assert baseline is not None

    current = [
        baseline_check.Issue.from_dict(_issue_dict("error", message="old")),
        baseline_check.Issue.from_dict(_issue_dict("error", message="new")),
        baseline_check.Issue.from_dict(_issue_dict("warning", message="new warning")),
    ]
    new_errors, new_warnings = baseline_check._split_new_findings(current, baseline)
    assert [i.message for i in new_errors] == ["new"]
    assert [i.message for i in new_warnings] == ["new warning"]


def test_unkeyable_findings_count_as_new(tmp_path):
    previous = tmp_path / "prev"
    _write_meta(previous)
    baseline = load_baseline(str(previous), "h")
    assert baseline is not None

    current = [
        baseline_check.Issue.from_dict(
            {"severity": "error", "category": "c", "message": "no location"}
        )
    ]
    new_errors, new_warnings = baseline_check._split_new_findings(current, baseline)
    assert len(new_errors) == 1
    assert new_warnings == []

    # The fixed-counts side also skips unkeyable findings instead of
    # treating them as keyed matches.
    fixed_errors, fixed_warnings = baseline_check._fixed_counts(current, baseline)
    assert fixed_errors == 0
    assert fixed_warnings == 0


def test_step_summary_write_failure_is_non_fatal(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))

    def broken_open(_path, _mode, **_kwargs):
        raise OSError("read-only filesystem")

    monkeypatch.setattr(builtins, "open", broken_open)

    baseline_check._write_step_summary(["line"])

    assert "could not write step summary" in capsys.readouterr().err
