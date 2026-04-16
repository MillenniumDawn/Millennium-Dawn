"""Emit GitHub Checks API annotations for validator issues.

One Check Run per validator. Each Check Run carries up to 50 annotations
(GitHub's API cap) selected by priority: errors before warnings, then by
file path and line. When the issue count exceeds the cap we truncate and
leave a synthetic 50th annotation that points reviewers to the PR comment
for the full list.

Only issues with both `file` and `line > 0` are eligible for annotations.
Issues without a concrete location (e.g. from validators that haven't
migrated to the structured `_report()` signature yet) appear in the PR
comment but not on the Files Changed tab.
"""

import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from .models import Issue, Severity, ValidatorRun

MAX_ANNOTATIONS_PER_CHECK = 50
MAX_MESSAGE_CHARS = 64_000  # API cap on output.text


def post_checks(
    repo_owner: str,
    repo_name: str,
    head_sha: str,
    runs: List[ValidatorRun],
    github_token: str,
) -> List[Tuple[str, bool, str]]:
    """Create one Check Run per validator. Returns [(title, success, msg), ...]."""
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/check-runs"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    results: List[Tuple[str, bool, str]] = []
    for run in runs:
        payload = _build_check_payload(run, head_sha)
        success, msg = _post_one(api_url, payload, headers)
        results.append((run.title, success, msg))
    return results


def _build_check_payload(run: ValidatorRun, head_sha: str) -> dict:
    annotations = _pick_annotations(run)
    conclusion = _conclusion_for(run)
    summary_line = _summary_line(run)
    output_text = _output_text(run)

    return {
        "name": run.title or run.name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {
            "title": f"{run.title}: {run.errors} error(s), {run.warnings} warning(s)",
            "summary": summary_line,
            "text": output_text,
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

    # Truncate and leave one synthetic annotation at the end
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


def _post_one(url: str, payload: dict, headers: dict) -> Tuple[bool, str]:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return True, f"check #{result.get('id', '?')}"
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = "<no body>"
        return False, f"HTTP {e.code}: {detail[:300]}"
    except Exception as e:
        return False, str(e)
