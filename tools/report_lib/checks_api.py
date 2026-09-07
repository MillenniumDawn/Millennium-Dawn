"""Emit GitHub Checks API annotations for validator issues, grouped by CI job.

One Check Run per job (the Actions job names, e.g. "Tools tests (Linux)" or
"Mod tests (core)"). Runs carry an explicit `job` when they come from a
suite-run sidecar or a batch manifest; validator sidecars fall back to a
name-based lookup through `validator_batches.BATCHES`. The GitHub Checks API
caps each request at 50 annotations, but a Check Run can hold an unlimited
total; additional batches are attached via PATCH after the initial write. We
default to 100 annotations per Check Run (configurable via
MAX_ANNOTATIONS_PER_CHECK), which keeps the slowest GitHub Files-Changed
render time reasonable while giving reviewers double the inline coverage.
Issues are sorted errors-first, then by file/line, so the most important
entries always survive any cap.

The workflow jobs already create Check Runs on the head SHA under their own
names, so an existing run with the job name is PATCHed in place; a POST is
only made when no matching Check Run exists.

Only issues with both `file` and `line > 0` are eligible for annotations.
Issues without a concrete location appear in the PR comment but not on the
Files Changed tab.
"""

import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from validation.validator_batches import BATCHES

from .models import Issue, Severity, ValidatorRun

ANNOTATIONS_PER_REQUEST = 50  # GitHub API hard limit per POST/PATCH
MAX_ANNOTATIONS_PER_CHECK = 100  # total kept; multiple of ANNOTATIONS_PER_REQUEST
MAX_MESSAGE_CHARS = 64_000  # API cap on output.text

_CORE_JOB = "Mod tests (core)"
_OS_JOB_NAMES = {"linux": "Linux", "macos": "macOS", "windows": "Windows"}


def _fallback_job(name: str) -> str:
    """Map a validator slug to its owning CI job when `job` is unset."""
    if name == "file-paths":
        return "File path validation"
    if name.startswith("tools-"):
        os_name = name.removeprefix("tools-")
        return f"Tools tests ({_OS_JOB_NAMES.get(os_name.lower(), os_name)})"
    for batch, specs in BATCHES.items():
        if any(spec.name == name for spec in specs):
            return f"Mod tests ({batch})"
    # Standalone checks (style, common-mistakes, encoding, descriptors) and
    # anything unmapped run inside the core batch job.
    return _CORE_JOB


def post_checks(
    repo_owner: str,
    repo_name: str,
    head_sha: str,
    runs: List[ValidatorRun],
    github_token: str,
    name_prefix: str = "",
) -> List[Tuple[str, bool, str]]:
    """Create one Check Run per job. Returns [(name, success, msg), ...]."""
    base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    api_base = f"{base}/check-runs"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    groups: Dict[str, List[ValidatorRun]] = {}
    for run in runs:
        groups.setdefault(run.job or _fallback_job(run.name), []).append(run)

    results: List[Tuple[str, bool, str]] = []
    existing = _existing_check_runs(base, head_sha, headers)
    for job, job_runs in groups.items():
        merged = _merge_runs(job, job_runs)
        annotations = _pick_annotations(merged)
        first_batch = annotations[:ANNOTATIONS_PER_REQUEST]
        remaining = annotations[ANNOTATIONS_PER_REQUEST:]

        name = name_prefix + (merged.title or merged.name)
        check_id = existing.get(name)
        success = False
        msg = ""
        if check_id is not None:
            patch_url = f"{api_base}/{check_id}"
            payload = _build_patch_payload(merged, first_batch, with_conclusion=True)
            success, msg = _patch_one(patch_url, payload, headers)
            if success:
                msg = f"check #{check_id}"
        if check_id is None or not success:
            # Job-owned Check Runs often reject PATCHes; POST a job-named run.
            payload = _build_check_payload(merged, head_sha, first_batch, name_prefix)
            success, msg, check_id = _post_one(api_base, payload, headers)
        if not success or not remaining:
            results.append((name, success, msg))
            continue

        # Attach the extra batches. Each PATCH replaces output.title/summary
        # too, so we re-send the same metadata each round (cheap and safe).
        patch_url = f"{api_base}/{check_id}"
        for start in range(0, len(remaining), ANNOTATIONS_PER_REQUEST):
            batch = remaining[start : start + ANNOTATIONS_PER_REQUEST]
            patch_payload = _build_patch_payload(merged, batch)
            patch_ok, patch_msg = _patch_one(patch_url, patch_payload, headers)
            if not patch_ok:
                msg += f"; PATCH at offset {start + ANNOTATIONS_PER_REQUEST} failed: {patch_msg}"
                success = False
                break
        results.append((name, success, msg))
    return results


def _merge_runs(job: str, runs: List[ValidatorRun]) -> ValidatorRun:
    """One synthetic run per job, carrying the merged verdict and issues."""
    status = "passed"
    if any(r.status in {"failed", "unknown"} for r in runs):
        status = "failed"
    elif any(r.status == "no_output" for r in runs):
        status = "no_output"
    elif any(r.status == "warnings" for r in runs):
        status = "warnings"
    return ValidatorRun(
        name=job,
        title=job,
        issues=[issue for run in runs for issue in run.issues],
        errors=sum(r.errors for r in runs),
        warnings=sum(r.warnings for r in runs),
        status=status,
        log_text="\n\n".join(r.log_text for r in runs if r.log_text),
        had_json=any(r.had_json for r in runs),
        execution_complete=all(r.execution_complete for r in runs),
        strict=all(r.strict is None or r.strict for r in runs),
    )


def _existing_check_runs(base: str, head_sha: str, headers: dict) -> Dict[str, int]:
    """Name -> id for the Check Runs already posted on the head SHA.

    An unreadable listing (network hiccup, rate limit) returns {} so the
    caller falls back to POSTing; the report comment stays the source of
    truth either way.
    """
    url = f"{base}/commits/{head_sha}/check-runs?per_page=100"
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}
    entries = data.get("check_runs") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return {}
    return {
        entry["name"]: entry["id"]
        for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("name"), str)
        and isinstance(entry.get("id"), int)
    }


def _build_check_payload(
    run: ValidatorRun, head_sha: str, annotations: List[Dict], name_prefix: str = ""
) -> dict:
    return {
        "name": name_prefix + (run.title or run.name),
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": _conclusion_for(run),
        "output": {
            "title": f"{run.title}: {run.errors} error(s), {run.warnings} warning(s)",
            "summary": _summary_line(run),
            "text": _output_text(run),
            "annotations": annotations,
        },
    }


def _build_patch_payload(
    run: ValidatorRun, annotations: List[Dict], with_conclusion: bool = False
) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "output": {
            "title": f"{run.title}: {run.errors} error(s), {run.warnings} warning(s)",
            "summary": _summary_line(run),
            "annotations": annotations,
        },
    }
    if with_conclusion:
        payload["status"] = "completed"
        payload["conclusion"] = _conclusion_for(run)
    return payload


def _conclusion_for(run: ValidatorRun) -> str:
    if not run.execution_complete:
        return "failure"
    if run.errors > 0 and (run.strict is None or run.strict):
        return "failure"
    if run.status in {"failed", "unknown"} and (run.strict is None or run.strict):
        return "failure"
    if run.errors > 0 or run.warnings > 0:
        return "neutral"
    if run.status == "no_output":
        return "skipped"
    if run.status != "passed":
        return "failure"
    return "success"


def _summary_line(run: ValidatorRun) -> str:
    if run.errors == 0 and run.warnings == 0:
        return "No issues found."
    bits = []
    if run.errors:
        bits.append(f"{run.errors} error(s)")
    if run.warnings:
        bits.append(f"{run.warnings} warning(s)")
    return ", ".join(bits) + "."


def _output_text(run: ValidatorRun) -> str:
    if not run.log_text:
        return ""
    text = "```\n" + run.log_text.rstrip() + "\n```"
    if len(text) > MAX_MESSAGE_CHARS:
        text = text[: MAX_MESSAGE_CHARS - 40] + "\n... (truncated)\n```"
    return text


def _pick_annotations(run: ValidatorRun) -> List[Dict]:
    eligible = [i for i in run.issues if i.has_location]
    if not eligible:
        return []

    eligible.sort(
        key=lambda i: (
            0 if i.severity == Severity.ERROR else 1,
            i.file,
            i.line,
        )
    )

    if len(eligible) <= MAX_ANNOTATIONS_PER_CHECK:
        return [_issue_to_annotation(i) for i in eligible]

    # Overflow: keep the highest-priority MAX-1 issues and append one
    # synthetic notice at the end so reviewers know the list was truncated.
    kept = eligible[: MAX_ANNOTATIONS_PER_CHECK - 1]
    overflow = len(eligible) - len(kept)
    top = eligible[0]
    overflow_annotation = {
        "path": top.file,
        "start_line": max(1, top.line),
        "end_line": max(1, top.line),
        "annotation_level": "notice",
        "title": f"{run.title}: {overflow} additional issue(s) truncated",
        "message": (
            f"Only the first {MAX_ANNOTATIONS_PER_CHECK - 1} issues are annotated "
            f"inline. See the PR comment for the full list."
        ),
    }
    return [_issue_to_annotation(i) for i in kept] + [overflow_annotation]


def _issue_to_annotation(issue: Issue) -> dict:
    level = "failure" if issue.severity == Severity.ERROR else "warning"
    title = (
        f"{issue.validator or issue.category or 'Validation'}: {issue.category}".rstrip(
            ": "
        )
    )
    return {
        "path": issue.file,
        "start_line": max(1, issue.line),
        "end_line": max(1, issue.line),
        "annotation_level": level,
        "title": title[:255],
        "message": issue.message[:MAX_MESSAGE_CHARS],
    }


def _post_one(
    url: str, payload: dict, headers: dict
) -> Tuple[bool, str, Optional[int]]:
    """POST returns (success, message, check_run_id)."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        check_id = result.get("id")
        return True, f"check #{check_id}", check_id
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = "<no body>"
        return False, f"HTTP {e.code}: {detail[:300]}", None
    except Exception as e:
        return False, str(e), None


def _patch_one(url: str, payload: dict, headers: dict) -> Tuple[bool, str]:
    """PATCH returns (success, message)."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        return True, "ok"
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = "<no body>"
        return False, f"HTTP {e.code}: {detail[:300]}"
    except Exception as e:
        return False, str(e)
