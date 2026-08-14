"""Tests for `report_lib.baseline`."""

import json

from report_lib import (
    Issue,
    Severity,
    classify,
    load_baseline,
    load_issues,
    write_baseline,
)
from report_lib.baseline import META_FILENAME, issue_key


def _issue(**overrides):
    fields = {
        "severity": Severity.ERROR,
        "category": "missing_key",
        "message": "key FOO not found",
        "file": "events/MD_x.txt",
        "line": 212,
        "validator": "events",
    }
    fields.update(overrides)
    return Issue(**fields)


def _write_sidecar(base, slug, issues):
    (base / f"{slug}.json").write_text(json.dumps(issues), encoding="utf-8")


def _issue_dict(severity, file="a.txt", line=1, message="m", category="missing_key"):
    return {
        "severity": severity,
        "category": category,
        "message": message,
        "file": file,
        "line": line,
    }


def test_load_baseline_returns_none_without_meta(tmp_path):
    _write_sidecar(tmp_path, "events", [_issue_dict("error")])
    assert load_baseline(str(tmp_path)) is None


def test_load_baseline_returns_none_on_toolshash_mismatch(tmp_path):
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"toolshash": "old-hash"}), encoding="utf-8"
    )
    assert load_baseline(str(tmp_path), "new-hash") is None


def test_load_baseline_loads_and_dedupes_sidecars(tmp_path):
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"toolshash": "h"}), encoding="utf-8"
    )
    dup = _issue_dict("error")
    _write_sidecar(tmp_path, "events", [dup])
    _write_sidecar(tmp_path, "localisation", [dup])
    baseline = load_baseline(str(tmp_path), "h")
    assert baseline is not None
    # Cross-validator duplicates collapse before keys are built.
    assert len(baseline.keys) == 1
    assert baseline.meta["toolshash"] == "h"


def test_issue_key_requires_location():
    assert issue_key(_issue()) is not None
    assert issue_key(_issue(file="", line=0)) is None


def test_classify_tags_new_and_existing(tmp_path):
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"toolshash": "h"}), encoding="utf-8"
    )
    _write_sidecar(
        tmp_path,
        "events",
        [
            _issue_dict("error", file="old.txt", line=1, message="old finding"),
            _issue_dict("warning", file="warn.txt", line=3, message="known warning"),
        ],
    )
    baseline = load_baseline(str(tmp_path), "h")

    issues = [
        _issue(file="old.txt", line=1, message="old finding"),
        _issue(file="new.txt", line=1, message="new finding"),
        _issue(
            severity=Severity.WARNING,
            file="new.txt",
            line=2,
            message="new warning",
        ),
        _issue(
            severity=Severity.WARNING,
            file="warn.txt",
            line=3,
            message="known warning",
        ),
    ]
    stats = classify(issues, baseline)

    assert [i.baseline_status for i in issues] == [
        "existing",
        "new",
        "new",
        "existing",
    ]
    assert stats.new_errors == 1
    assert stats.new_warnings == 1
    assert stats.existing_errors == 1
    assert stats.existing_warnings == 1
    assert stats.unclassified == 0
    assert stats.new_issues == issues[1:3]


def test_classify_escalated_severity_counts_as_new(tmp_path):
    # Severity is part of the key: a warning on main that a PR escalates to
    # an error must alarm as a new error, not read as existing.
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"toolshash": "h"}), encoding="utf-8"
    )
    _write_sidecar(
        tmp_path,
        "events",
        [_issue_dict("warning", file="a.txt", line=1, message="escalated")],
    )
    baseline = load_baseline(str(tmp_path), "h")

    stats = classify([_issue(file="a.txt", line=1, message="escalated")], baseline)
    assert stats.new_errors == 1
    assert stats.existing_errors == 0


def test_classify_leaves_unkeyable_issues_untagged(tmp_path):
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"toolshash": "h"}), encoding="utf-8"
    )
    baseline = load_baseline(str(tmp_path), "h")
    assert baseline is not None

    unkeyable = _issue(file="", line=0, message="no location")
    stats = classify([unkeyable], baseline)

    assert unkeyable.baseline_status is None
    assert stats.unclassified == 1


def test_load_issues_ignores_non_list_json(tmp_path):
    (tmp_path / "notes.json").write_text('{"not": "a list"}', encoding="utf-8")
    assert load_issues(str(tmp_path)) == []


def test_load_issues_skips_unparseable_sidecars(tmp_path):
    (tmp_path / "broken.json").write_text("not json", encoding="utf-8")
    (tmp_path / "events.json").write_text(
        json.dumps([_issue_dict("error")]), encoding="utf-8"
    )
    issues = load_issues(str(tmp_path))
    # The broken sidecar is skipped, not fatal: one validator with a
    # truncated upload must not crash the PR report or the nightly diff.
    assert len(issues) == 1


def test_load_baseline_returns_none_when_meta_not_a_dict(tmp_path):
    (tmp_path / META_FILENAME).write_text("[1, 2, 3]", encoding="utf-8")
    assert load_baseline(str(tmp_path), "h") is None


def test_load_baseline_returns_none_on_unreadable_meta(tmp_path):
    (tmp_path / META_FILENAME).write_text("{broken", encoding="utf-8")
    assert load_baseline(str(tmp_path), "h") is None


def test_classify_with_empty_baseline_marks_everything_new(tmp_path):
    # An all-clean main run stores only meta (no sidecars): any PR finding
    # is new by definition.
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"toolshash": "h"}), encoding="utf-8"
    )
    baseline = load_baseline(str(tmp_path), "h")
    assert baseline is not None

    stats = classify(
        [
            _issue(file="a.txt", line=1, message="first"),
            _issue(
                severity=Severity.WARNING,
                file="b.txt",
                line=2,
                message="second",
            ),
        ],
        baseline,
    )

    assert stats.new_errors == 1
    assert stats.new_warnings == 1
    assert stats.existing_errors == 0
    assert stats.unclassified == 0


def test_classify_counts_mixed_unclassified_and_new(tmp_path):
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"toolshash": "h"}), encoding="utf-8"
    )
    baseline = load_baseline(str(tmp_path), "h")
    assert baseline is not None

    stats = classify(
        [
            _issue(file="a.txt", line=1, message="keyed"),
            _issue(file="", line=0, message="no location"),
        ],
        baseline,
    )

    assert stats.new_errors == 1
    assert stats.unclassified == 1
    assert len(stats.new_issues) == 1


def test_write_baseline_copies_sidecars_writes_meta_and_prunes(tmp_path):
    current = tmp_path / "current"
    current.mkdir()
    _write_sidecar(current, "events", [_issue_dict("error")])

    output = tmp_path / "baseline"
    output.mkdir()
    # A stale sidecar from a validator that no longer runs.
    _write_sidecar(output, "removed-validator", [_issue_dict("error")])

    write_baseline(str(current), str(output), {"toolshash": "h"})

    assert (output / "events.json").is_file()
    assert not (output / "removed-validator.json").exists()
    meta = json.loads((output / META_FILENAME).read_text(encoding="utf-8"))
    assert meta["toolshash"] == "h"


def test_write_baseline_over_empty_sidecar_dir_prunes_all(tmp_path):
    current = tmp_path / "current"
    current.mkdir()
    output = tmp_path / "baseline"
    output.mkdir()
    _write_sidecar(output, "events", [_issue_dict("error")])

    # All-clean run: no sidecars at all, so the baseline collapses to the
    # meta file only — the empty findings set.
    write_baseline(str(current), str(output), {"toolshash": "h"})

    assert not (output / "events.json").exists()
    assert (output / META_FILENAME).is_file()
    baseline = load_baseline(str(output), "h")
    assert baseline is not None
    assert baseline.keys == set()


def test_build_report_annotates_new_vs_existing(tmp_path):
    # End-to-end wiring: the report generator classifies against a restored
    # baseline and both bodies carry the NEW/EXISTING signal.
    import generate_validation_report

    from report_lib import ReportContext

    results = tmp_path / "validation-results" / "validation-events-results"
    results.mkdir(parents=True)
    (results / "validation-events.log").write_text(
        "VALIDATION COMPLETE", encoding="utf-8"
    )
    (results / "validation-events.json").write_text(
        json.dumps(
            [
                _issue_dict("error", file="old.txt", message="old finding"),
                _issue_dict("error", file="new.txt", message="new finding"),
            ]
        ),
        encoding="utf-8",
    )

    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    (baseline_dir / META_FILENAME).write_text(
        json.dumps({"toolshash": "h"}), encoding="utf-8"
    )
    _write_sidecar(
        baseline_dir,
        "events",
        [_issue_dict("error", file="old.txt", message="old finding")],
    )
    baseline = load_baseline(str(baseline_dir), "h")
    assert baseline is not None

    ctx = ReportContext(
        pr_number="42",
        commit_sha="abc1234deadbeef",  # pragma: allowlist secret
        repo="MillenniumDawn/Millennium-Dawn",
    )
    body, step_body, _runs, deduped, _trunc, stats = (
        generate_validation_report.build_report(
            str(tmp_path / "validation-results"), ctx, baseline
        )
    )

    assert stats is not None
    assert stats.new_errors == 1
    assert stats.existing_errors == 1
    assert "1 new against the main baseline." in body
    assert "## New findings vs main baseline" in step_body
    assert len(deduped) == 2
