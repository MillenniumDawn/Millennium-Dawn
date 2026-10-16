from __future__ import annotations

import json
from pathlib import Path

import pytest
from validation_timing_report import (
    TimingReportError,
    load_exports,
    parse_export,
    render_report,
)

_BASE_METADATA = {
    "workload": "tools-tests",
    "runner": "ubuntu-24.04",
    "tool": "6bf489e",
    "python": "3.14.0",
    "dependencies": {"pytest": "9.1.0"},
    "cache": "cold",
    "worker_budget": 4,
    "baseSha": "base-sha",
}


def _export(
    run_id="1",
    head="head-sha",
    *,
    attempt=1,
    status="completed",
    conclusion: str | None = "success",
):
    return {
        "databaseId": int(run_id),
        "attempt": attempt,
        "headSha": head,
        "displayTitle": "Tools tests",
        "status": status,
        "conclusion": conclusion,
        "createdAt": "2026-01-01T00:00:00Z",
        "startedAt": "2026-01-01T00:00:10Z",
        "updatedAt": "2026-01-01T00:00:50Z",
        "metadata": dict(_BASE_METADATA),
        "jobs": [
            {
                "databaseId": 10,
                "name": "Linux",
                "status": "completed",
                "conclusion": "success",
                "startedAt": "2026-01-01T00:00:10Z",
                "completedAt": "2026-01-01T00:00:30Z",
                "steps": [
                    {
                        "name": "worktree",
                        "status": "completed",
                        "conclusion": "success",
                        "startedAt": "2026-01-01T00:00:10Z",
                        "completedAt": "2026-01-01T00:00:20Z",
                    },
                    {
                        "name": "skipped",
                        "status": "completed",
                        "conclusion": "skipped",
                        "startedAt": "2026-01-01T00:00:20Z",
                        "completedAt": "2026-01-01T00:00:25Z",
                    },
                    {
                        "name": "zero",
                        "status": "completed",
                        "conclusion": "success",
                        "startedAt": "2026-01-01T00:00:25Z",
                        "completedAt": "2026-01-01T00:00:25Z",
                    },
                ],
            },
            {"name": "Linux", "status": "completed", "conclusion": "success"},
        ],
    }


def _write_export(path: Path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_report_lists_real_jobs_steps_and_distinguishes_spans():
    sample = parse_export(_export(), Path("run.json"))

    report = render_report([sample], 0)

    assert "Run 1 attempt 1:" in report
    assert "compatibility: supplied metadata; cache=cold" in report
    assert "overall run span: 40.000s" in report
    assert "summed job time: 20.000s" in report
    assert "job Linux: 20.000s" in report
    assert "step worktree: 10.000s [success]" in report
    assert "step skipped: not-run/unknown [skipped]" in report
    assert "step zero: 0.000s [success]" in report
    assert (
        report.splitlines().count(
            "  job Linux: 20.000s status=completed conclusion=success"
        )
        == 1
    )


def test_duplicate_runs_do_not_inflate_summary_and_same_revision_is_summarized(
    tmp_path,
):
    first = _export("1")
    second = _export("1", attempt=2)
    second["updatedAt"] = "2026-01-01T00:01:00Z"
    duplicate = _export("1")
    first_path = tmp_path / "one.json"
    second_path = tmp_path / "two.json"
    duplicate_path = tmp_path / "duplicate.json"
    _write_export(first_path, first)
    _write_export(second_path, second)
    _write_export(duplicate_path, duplicate)

    samples, duplicates = load_exports([first_path, second_path, duplicate_path])
    report = render_report(samples, duplicates)

    assert len(samples) == 2
    assert duplicates == 1
    assert "Samples: 2 unique run attempts (1 duplicates ignored)" in report
    assert "head=head-sha base=base-sha cache=cold: n=2" in report
    assert "median=45.000s range=40.000-50.000s" in report


def test_reruns_with_distinct_attempts_are_retained():
    first = parse_export(_export("8", attempt=1), Path("first.json"))
    second = parse_export(_export("8", attempt=2), Path("second.json"))

    assert first.database_id == second.database_id == "8"
    assert [first.attempt, second.attempt] == [1, 2]


def test_incomplete_cancelled_and_unverified_samples_have_no_summary():
    incomplete = _export("3", status="in_progress", conclusion=None)
    incomplete["startedAt"] = None
    incomplete["updatedAt"] = None
    cancelled = _export("4", status="completed", conclusion="cancelled")
    unverified = _export("5")
    del unverified["metadata"]

    samples = [
        parse_export(payload, Path(f"{index}.json"))
        for index, payload in enumerate((incomplete, cancelled, unverified))
    ]
    report = render_report(samples, 0)

    assert "conclusion=none" in report
    assert "head=head-sha base=unknown" in report
    assert "compatibility: unverified" in report
    assert "No compatible completed-success samples" in report
    assert "Compatible summaries" not in report


def test_cross_revision_samples_are_not_aggregated():
    first = parse_export(_export("6", head="head-a"), Path("a.json"))
    second = parse_export(_export("7", head="head-b"), Path("b.json"))

    report = render_report([first, second], 0)

    assert "head=head-a base=base-sha cache=cold: n=1" in report
    assert "head=head-b base=base-sha cache=cold: n=1" in report
    assert "range=40.000-40.000s" in report


def test_missing_executed_step_timestamps_have_no_summary():
    payload = _export("9")
    payload["jobs"][0]["steps"][0]["completedAt"] = None

    sample = parse_export(payload, Path("incomplete-step.json"))

    assert sample.eligible_for_summary is False
    assert "No compatible completed-success samples" in render_report([sample], 0)
    assert "step worktree: — [success]" in render_report([sample], 0)


def test_skipped_and_executed_workloads_are_separate_groups():
    first = _export("10")
    second = _export("11")
    second["jobs"][0]["steps"][1]["conclusion"] = "success"
    second["jobs"][0]["steps"][1]["status"] = "completed"

    samples = [
        parse_export(first, Path("skipped.json")),
        parse_export(second, Path("executed.json")),
    ]
    report = render_report(samples, 0)

    assert report.count("cache=cold: n=1") == 2


def test_duplicate_actual_jobs_do_not_inflate_job_summary():
    payload = _export("12")
    payload["jobs"].append(dict(payload["jobs"][0]))

    sample = parse_export(payload, Path("duplicate-job.json"))
    report = render_report([sample], 0)

    assert len(sample.jobs) == 1
    assert "job Linux: n=1" in report


def test_job_response_order_does_not_change_compatibility_key():
    first = _export("19")
    windows = {
        "databaseId": 11,
        "name": "Windows",
        "status": "completed",
        "conclusion": "success",
        "startedAt": "2026-01-01T00:00:10Z",
        "completedAt": "2026-01-01T00:00:30Z",
        "steps": [
            {
                "name": "worktree",
                "status": "completed",
                "conclusion": "success",
                "startedAt": "2026-01-01T00:00:10Z",
                "completedAt": "2026-01-01T00:00:20Z",
            }
        ],
    }
    first["jobs"].insert(1, windows)
    second = _export("20")
    second["jobs"] = [windows, second["jobs"][0], second["jobs"][1]]

    first_sample = parse_export(first, Path("first-order.json"))
    second_sample = parse_export(second, Path("reverse-order.json"))

    assert first_sample.compatibility_key == second_sample.compatibility_key
    assert "cache=cold: n=2" in render_report([first_sample, second_sample], 0)

    second["jobs"][1]["steps"][1]["conclusion"] = "success"
    second["jobs"][1]["steps"][1]["status"] = "completed"
    changed_sample = parse_export(second, Path("changed-step-selection.json"))

    assert changed_sample.compatibility_key != first_sample.compatibility_key
    assert (
        render_report([first_sample, changed_sample], 0).count("cache=cold: n=1") == 2
    )


@pytest.mark.parametrize("cache", [[], {}, False, None])
def test_non_scalar_cache_metadata_is_unverified(cache):
    payload = _export("21")
    payload["metadata"]["cache"] = cache

    sample = parse_export(payload, Path("bad-cache.json"))
    report = render_report([sample], 0)

    assert sample.metadata_error is not None
    assert "compatibility: unverified" in report
    assert "No compatible completed-success samples" in report


def test_non_list_steps_are_a_clear_error():
    payload = _export("13")
    payload["jobs"][0]["steps"] = {}

    with pytest.raises(TimingReportError, match=r"jobs\[0\]\.steps must be an array"):
        parse_export(payload, Path("bad-steps.json"))


def test_unusable_metadata_is_reported_without_a_summary():
    payload = _export("14")
    payload["metadata"].update(
        {
            "workload": {},
            "runner": [],
            "tool": False,
            "python": 0,
            "dependencies": [],
            "cache": "anything",
            "worker_budget": 0,
            "baseSha": "unknown",
        }
    )

    sample = parse_export(payload, Path("bad-metadata.json"))
    report = render_report([sample], 0)

    assert sample.metadata_error is not None
    assert "compatibility: unverified" in report
    assert "No compatible completed-success samples" in report


def test_optional_metadata_does_not_split_compatible_groups():
    first = _export("15")
    second = _export("16")
    first["metadata"]["memory_mb"] = 100
    second["metadata"]["memory_mb"] = 200

    samples = [
        parse_export(first, Path("memory-a.json")),
        parse_export(second, Path("memory-b.json")),
    ]

    assert "cache=cold: n=2" in render_report(samples, 0)


@pytest.mark.parametrize("attempt", [0, -1, True, "1"])
def test_attempt_must_be_positive_integer(attempt):
    payload = _export("17", attempt=attempt)

    with pytest.raises(TimingReportError, match="attempt.*positive integer"):
        parse_export(payload, Path("bad-attempt.json"))


def test_malformed_metadata_structure_has_explicit_error():
    payload = _export("18")
    payload["metadata"] = []

    with pytest.raises(TimingReportError, match="metadata.*object"):
        parse_export(payload, Path("bad-metadata-structure.json"))


def test_malformed_export_has_explicit_error():
    payload = _export()
    del payload["jobs"]

    with pytest.raises(TimingReportError, match="missing required field.*jobs"):
        parse_export(payload, Path("bad.json"))
