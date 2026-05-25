"""Emit GitHub Checks API annotations for validator issues.

One Check Run per validator. The GitHub Checks API caps each request at 50
annotations, but a Check Run can hold an unlimited total — additional
batches are attached via PATCH after the initial POST. We default to 100
annotations per Check Run (configurable via MAX_ANNOTATIONS_PER_CHECK),
which keeps the slowest GitHub Files-Changed render time reasonable while
giving reviewers double the inline coverage. Issues are sorted errors-first,
then by file/line, so the most important entries always survive any cap.

Only issues with both `file` and `line > 0` are eligible for annotations.
Issues without a concrete location appear in the PR comment but not on the
Files Changed tab.
"""

import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from .models import Issue, Severity, ValidatorRun

# GitHub caps any single POST/PATCH at 50 annotations. We can break through
# that by PATCHing additional batches, so the visible cap below is the only
# project-level knob — bump it to surface more issues per Check Run.
ANNOTATIONS_PER_REQUEST = 50  # GitHub API hard limit per POST/PATCH
MAX_ANNOTATIONS_PER_CHECK = 100  # total kept; multiple of ANNOTATIONS_PER_REQUEST
MAX_MESSAGE_CHARS = 64_000  # API cap on output.text


def post_checks(
    repo_owner: str,
    repo_name: str,
    head_sha: str,
    runs: List[ValidatorRun],
    github_token: str,
) -> List[Tuple[str, bool, str]]:
    """Create one Check Run per validator. Returns [(title, success, msg), ...]."""
    api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}/check-runs"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    results: List[Tuple[str, bool, str]] = []
    for run in runs:
        annotations = _pick_annotations(run)
        # First batch goes in the initial POST; remaining batches go in PATCHes.
        first_batch = annotations[:ANNOTATIONS_PER_REQUEST]
        remaining = annotations[ANNOTATIONS_PER_REQUEST:]

        payload = _build_check_payload(run, head_sha, first_batch)
        success, msg, check_id = _post_one(api_base, payload, headers)
        if not success or not remaining:
            results.append((run.title, success, msg))
            continue

        # Attach the extra batches. Each PATCH replaces output.title/summary
        # too, so we re-send the same metadata each round (cheap and safe).
        patch_url = f"{api_base}/{check_id}"
        for start in range(0, len(remaining), ANNOTATIONS_PER_REQUEST):
            batch = remaining[start : start + ANNOTATIONS_PER_REQUEST]
            patch_payload = _build_patch_payload(run, batch)
            patch_ok, patch_msg = _patch_one(patch_url, patch_payload, headers)
            if not patch_ok:
                msg += f"; PATCH at offset {start + ANNOTATIONS_PER_REQUEST} failed: {patch_msg}"
                success = False
                break
        results.append((run.title, success, msg))
    return results


def _build_check_payload(
    run: ValidatorRun, head_sha: str, annotations: List[Dict]
) -> dict:
    return {
        "name": run.title or run.name,
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


def _build_patch_payload(run: ValidatorRun, annotations: List[Dict]) -> dict:
    return {
        "output": {
            "title": f"{run.title}: {run.errors} error(s), {run.warnings} warning(s)",
            "summary": _summary_line(run),
            "annotations": annotations,
        },
    }


def _conclusion_for(run: ValidatorRun) -> str:
    if run.errors > 0:
        return "failure"
    if run.warnings > 0:
        return "neutral"
    if run.status == "no_output":
        return "skipped"
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
