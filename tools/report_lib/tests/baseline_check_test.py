"""Tests for the nightly `baseline_check` CLI."""

import json

import baseline_check

from report_lib import load_baseline
from report_lib.baseline import META_FILENAME


def _issue_dict(severity, file="a.txt", line=1, message="m", category="c"):
    return {
        "severity": severity,
        "category": category,
        "message": message,
        "file": file,
        "line": line,
    }


def _write_sidecar(base, slug, issues):
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{slug}.json").write_text(json.dumps(issues), encoding="utf-8")


def _write_meta(base, toolshash="h"):
    base.mkdir(parents=True, exist_ok=True)
    (base / META_FILENAME).write_text(
        json.dumps({"toolshash": toolshash}), encoding="utf-8"
    )


def _run(tmp_path, previous, current, toolshash="h", monkeypatch=None):
    if monkeypatch is not None:
        monkeypatch.setattr(baseline_check, "_write_step_summary", lambda lines: None)
        monkeypatch.setattr(
            baseline_check, "_build_meta", lambda args: {"toolshash": args.toolshash}
        )
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


def test_new_errors_fail_and_keep_old_baseline(tmp_path, monkeypatch, capsys):
    previous = tmp_path / "prev"
    _write_meta(previous)
    _write_sidecar(previous, "events", [_issue_dict("error", message="old")])
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
    previous = tmp_path / "prev"
    _write_meta(previous)
    _write_sidecar(previous, "events", [_issue_dict("error", message="old")])
    current = tmp_path / "current"
    _write_sidecar(current, "events", [_issue_dict("error", message="old")])

    code = _run(tmp_path, previous, current, monkeypatch=monkeypatch)

    assert code == 0
    assert (tmp_path / "baseline" / META_FILENAME).is_file()
    assert "baseline updated" in capsys.readouterr().out


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
    assert "fixed" in capsys.readouterr().out
    assert (tmp_path / "baseline" / META_FILENAME).is_file()


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
