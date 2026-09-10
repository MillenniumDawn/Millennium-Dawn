"""Summarize saved GitHub Actions validation-run timings."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

_REQUIRED_FIELDS = (
    "databaseId",
    "attempt",
    "headSha",
    "displayTitle",
    "status",
    "conclusion",
    "createdAt",
    "startedAt",
    "updatedAt",
    "jobs",
)
_REQUIRED_METADATA = (
    "workload",
    "runner",
    "tool",
    "python",
    "dependencies",
    "cache",
    "worker_budget",
    "baseSha",
)
_UNKNOWN_VALUES = {"unknown", "n/a", "na", "none", "null"}


class TimingReportError(ValueError):
    """Raised when an Actions export cannot be interpreted."""


@dataclass(frozen=True)
class StepTiming:
    name: str
    status: Optional[str]
    conclusion: Optional[str]
    duration_seconds: Optional[float]


@dataclass(frozen=True)
class JobTiming:
    database_id: Optional[str]
    name: str
    status: Optional[str]
    conclusion: Optional[str]
    duration_seconds: Optional[float]
    steps: Tuple[StepTiming, ...]


@dataclass(frozen=True)
class TimingSample:
    database_id: str
    attempt: int
    head_sha: str
    status: str
    conclusion: Optional[str]
    overall_seconds: Optional[float]
    jobs: Tuple[JobTiming, ...]
    metadata: Mapping[str, Any]
    metadata_error: Optional[str]

    @property
    def summed_job_seconds(self) -> Optional[float]:
        durations = [job.duration_seconds for job in self.jobs]
        if not durations or any(value is None for value in durations):
            return None
        return sum(value for value in durations if value is not None)

    @property
    def eligible_for_summary(self) -> bool:
        if (
            self.status.lower() != "completed"
            or self.conclusion != "success"
            or self.metadata_error is not None
            or self.overall_seconds is None
            or self.summed_job_seconds is None
        ):
            return False
        return all(_job_is_complete(job) for job in self.jobs)

    @property
    def compatibility_key(self) -> Optional[str]:
        if self.metadata_error is not None:
            return None
        metadata = {field: self.metadata[field] for field in _REQUIRED_METADATA}
        job_signatures = [_job_signature(job) for job in self.jobs]
        job_signatures.sort(
            key=lambda signature: json.dumps(
                signature, sort_keys=True, separators=(",", ":")
            )
        )
        workload = {
            "headSha": self.head_sha,
            "metadata": metadata,
            "jobs": job_signatures,
        }
        return json.dumps(workload, sort_keys=True, separators=(",", ":"))

    @property
    def cache_label(self) -> str:
        return str(self.metadata["cache"])


def _require_string(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value:
        raise TimingReportError(f"{path}: field '{field}' must be a non-empty string")
    return value


def _require_attempt(value: Any, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TimingReportError(f"{path}: field 'attempt' must be a positive integer")
    return value


def _parse_timestamp(value: Any, field: str, path: Path) -> Optional[datetime]:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise TimingReportError(
            f"{path}: field '{field}' must be an ISO timestamp or null"
        )
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TimingReportError(
            f"{path}: field '{field}' is not an ISO timestamp"
        ) from exc
    if timestamp.tzinfo is None:
        raise TimingReportError(f"{path}: field '{field}' must include a timezone")
    return timestamp


def _duration(
    start: Optional[datetime], end: Optional[datetime], label: str, path: Path
) -> Optional[float]:
    if start is None or end is None:
        return None
    seconds = (end - start).total_seconds()
    if seconds < 0:
        raise TimingReportError(f"{path}: {label} ends before it starts")
    return seconds


def _optional_status(value: Any, field: str, path: Path) -> Optional[str]:
    if value is None:
        return None
    return _require_string(value, field, path)


def _is_skipped(step: StepTiming) -> bool:
    return step.status == "skipped" or step.conclusion == "skipped"


def _parse_step(raw: Any, index: int, path: Path) -> StepTiming:
    if not isinstance(raw, dict):
        raise TimingReportError(f"{path}: job step {index} must be an object")
    name = _require_string(raw.get("name"), f"jobs[].steps[{index}].name", path)
    status = _optional_status(raw.get("status"), f"jobs[].steps[{index}].status", path)
    conclusion = _optional_status(
        raw.get("conclusion"), f"jobs[].steps[{index}].conclusion", path
    )
    started = _parse_timestamp(
        raw.get("startedAt"), f"jobs[].steps[{index}].startedAt", path
    )
    completed = _parse_timestamp(
        raw.get("completedAt"), f"jobs[].steps[{index}].completedAt", path
    )
    duration = (
        None
        if status == "skipped" or conclusion == "skipped"
        else _duration(started, completed, f"step '{name}'", path)
    )
    return StepTiming(name, status, conclusion, duration)


def _parse_job(raw: Any, index: int, path: Path) -> Optional[JobTiming]:
    if not isinstance(raw, dict):
        raise TimingReportError(f"{path}: jobs[{index}] must be an object")
    if "steps" not in raw or raw["steps"] == []:
        return None
    steps = raw["steps"]
    if not isinstance(steps, list):
        raise TimingReportError(f"{path}: jobs[{index}].steps must be an array")
    name = _require_string(raw.get("name"), f"jobs[{index}].name", path)
    database_id = raw.get("databaseId")
    if database_id is not None and isinstance(database_id, (dict, list, bool)):
        raise TimingReportError(
            f"{path}: jobs[{index}].databaseId must be scalar or null"
        )
    status = _optional_status(raw.get("status"), f"jobs[{index}].status", path)
    conclusion = _optional_status(
        raw.get("conclusion"), f"jobs[{index}].conclusion", path
    )
    started = _parse_timestamp(raw.get("startedAt"), f"jobs[{index}].startedAt", path)
    completed = _parse_timestamp(
        raw.get("completedAt"), f"jobs[{index}].completedAt", path
    )
    duration = _duration(started, completed, f"job '{name}'", path)
    parsed_steps = tuple(
        _parse_step(step, step_index, path) for step_index, step in enumerate(steps)
    )
    return JobTiming(
        None if database_id is None else str(database_id),
        name,
        status,
        conclusion,
        duration,
        parsed_steps,
    )


def _meaningful_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().lower() not in _UNKNOWN_VALUES
    )


def _nonempty_representation(value: Any) -> bool:
    if isinstance(value, str):
        return _meaningful_string(value)
    if isinstance(value, (dict, list)):
        return bool(value)
    return False


def _metadata(
    payload: Mapping[str, Any], path: Path
) -> Tuple[Mapping[str, Any], Optional[str]]:
    value = payload.get("metadata", {})
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise TimingReportError(f"{path}: field 'metadata' must be an object")
    metadata = dict(value)
    invalid = []
    for field in ("workload", "runner", "tool", "python", "baseSha"):
        if not _meaningful_string(metadata.get(field)):
            invalid.append(field)
    if not _nonempty_representation(metadata.get("dependencies")):
        invalid.append("dependencies")
    worker_budget = metadata.get("worker_budget")
    if (
        isinstance(worker_budget, bool)
        or not isinstance(worker_budget, int)
        or worker_budget <= 0
    ):
        invalid.append("worker_budget")
    if metadata.get("cache") not in ("cold", "warm"):
        invalid.append("cache")
    if invalid:
        return metadata, "unusable metadata: " + ", ".join(invalid)
    return metadata, None


def parse_export(payload: Any, path: Path) -> TimingSample:
    """Parse one ``gh run view --json`` export."""
    if not isinstance(payload, dict):
        raise TimingReportError(f"{path}: top-level JSON value must be an object")
    missing = [field for field in _REQUIRED_FIELDS if field not in payload]
    if missing:
        raise TimingReportError(
            f"{path}: missing required field(s): {', '.join(missing)}"
        )
    database_id = payload["databaseId"]
    if isinstance(database_id, (dict, list, bool)) or database_id in (None, ""):
        raise TimingReportError(
            f"{path}: field 'databaseId' must be a scalar identifier"
        )
    attempt = _require_attempt(payload["attempt"], path)
    head_sha = _require_string(payload["headSha"], "headSha", path)
    _require_string(payload["displayTitle"], "displayTitle", path)
    status = _require_string(payload["status"], "status", path)
    conclusion = _optional_status(payload["conclusion"], "conclusion", path)
    jobs = payload["jobs"]
    if not isinstance(jobs, list):
        raise TimingReportError(f"{path}: field 'jobs' must be an array")
    _parse_timestamp(payload["createdAt"], "createdAt", path)
    started = _parse_timestamp(payload["startedAt"], "startedAt", path)
    updated = _parse_timestamp(payload["updatedAt"], "updatedAt", path)
    overall = _duration(started, updated, "run", path)
    parsed_jobs = []
    seen_job_ids = set()
    for index, raw_job in enumerate(jobs):
        job = _parse_job(raw_job, index, path)
        if job is None:
            continue
        if job.database_id is not None and job.database_id in seen_job_ids:
            continue
        if job.database_id is not None:
            seen_job_ids.add(job.database_id)
        parsed_jobs.append(job)
    metadata, metadata_error = _metadata(payload, path)
    return TimingSample(
        str(database_id),
        attempt,
        head_sha,
        status,
        conclusion,
        overall,
        tuple(parsed_jobs),
        metadata,
        metadata_error,
    )


def load_exports(paths: Iterable[Path]) -> Tuple[List[TimingSample], int]:
    """Load exports, deduplicating samples by Actions run ID and attempt."""
    samples: List[TimingSample] = []
    seen = set()
    duplicates = 0
    for path in paths:
        try:
            with path.open(encoding="utf-8") as handle:
                payload = json.load(handle)
        except OSError as exc:
            raise TimingReportError(f"{path}: cannot read export: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise TimingReportError(f"{path}: invalid JSON: {exc.msg}") from exc
        sample = parse_export(payload, path)
        key = (sample.database_id, sample.attempt)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        samples.append(sample)
    return samples, duplicates


def _seconds(value: Optional[float]) -> str:
    return "—" if value is None else f"{value:.3f}s"


def _summary(values: Sequence[float]) -> str:
    return f"n={len(values)} median={statistics.median(values):.3f}s range={min(values):.3f}-{max(values):.3f}s"


def _step_result(step: StepTiming) -> str:
    return step.conclusion or step.status or "not-success"


def _job_is_complete(job: JobTiming) -> bool:
    if (
        job.status != "completed"
        or job.conclusion != "success"
        or job.duration_seconds is None
    ):
        return False
    return all(
        _is_skipped(step)
        or (
            step.status == "completed"
            and step.conclusion == "success"
            and step.duration_seconds is not None
        )
        for step in job.steps
    )


def _job_signature(job: JobTiming) -> Dict[str, Any]:
    return {
        "name": job.name,
        "status": job.status,
        "conclusion": job.conclusion,
        "steps": [
            {
                "name": step.name,
                "status": step.status,
                "conclusion": step.conclusion,
            }
            for step in job.steps
        ],
    }


def _sample_lines(sample: TimingSample) -> List[str]:
    base_sha = sample.metadata.get("baseSha")
    base_label = base_sha if _meaningful_string(base_sha) else "unknown"
    lines = [
        f"Run {sample.database_id} attempt {sample.attempt}: head={sample.head_sha} "
        f"base={base_label} status={sample.status} conclusion={sample.conclusion or 'none'}",
        f"  overall run span: {_seconds(sample.overall_seconds)}; "
        f"summed job time: {_seconds(sample.summed_job_seconds)}",
    ]
    if sample.metadata_error:
        lines.append(f"  compatibility: unverified ({sample.metadata_error})")
    else:
        lines.append(f"  compatibility: supplied metadata; cache={sample.cache_label}")
    if not sample.jobs:
        lines.append("  jobs: none with steps (synthetic Checks API jobs ignored)")
    for job in sample.jobs:
        lines.append(
            f"  job {job.name}: {_seconds(job.duration_seconds)} "
            f"status={job.status or 'none'} conclusion={job.conclusion or 'none'}"
        )
        for step in job.steps:
            lines.append(
                f"    step {step.name}: "
                f"{_seconds(step.duration_seconds) if not _is_skipped(step) else 'not-run/unknown'} "
                f"[{_step_result(step)}]"
            )
    return lines


def _summary_lines(samples: Sequence[TimingSample]) -> List[str]:
    groups: Dict[str, List[TimingSample]] = {}
    for sample in samples:
        if sample.eligible_for_summary and sample.compatibility_key is not None:
            groups.setdefault(sample.compatibility_key, []).append(sample)
    if not groups:
        return ["No compatible completed-success samples for median/range summaries."]
    lines = [
        "Compatible summaries (grouped by head/base revision, metadata, and workload):"
    ]
    for group in groups.values():
        first = group[0]
        base_sha = first.metadata["baseSha"]
        lines.append(
            f"  head={first.head_sha} base={base_sha} cache={first.cache_label}: "
            f"{_summary([sample.overall_seconds for sample in group if sample.overall_seconds is not None])} overall run span"
        )
        lines.append(
            "    summed job time: "
            f"{_summary([sample.summed_job_seconds for sample in group if sample.summed_job_seconds is not None])}"
        )
        names = sorted({job.name for sample in group for job in sample.jobs})
        for name in names:
            values = [
                job.duration_seconds
                for sample in group
                for job in sample.jobs
                if job.name == name and job.duration_seconds is not None
            ]
            if values:
                lines.append(f"    job {name}: {_summary(values)}")
    return lines


def render_report(samples: Sequence[TimingSample], duplicates: int) -> str:
    """Render a report for tests and callers that do not use stdout."""
    lines = ["Validation timing report"]
    duplicate_note = f" ({duplicates} duplicates ignored)" if duplicates else ""
    lines.append(f"Samples: {len(samples)} unique run attempts{duplicate_note}")
    for sample in samples:
        lines.extend(_sample_lines(sample))
    lines.extend(_summary_lines(samples))
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report GitHub Actions validation job and step timings from saved JSON exports.",
        epilog="Exports with incomplete timestamps or non-success conclusions are reported but excluded from summaries.",
    )
    parser.add_argument("exports", nargs="+", type=Path, metavar="EXPORT")
    args = parser.parse_args(argv)
    try:
        samples, duplicates = load_exports(args.exports)
        print(render_report(samples, duplicates))
    except TimingReportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
