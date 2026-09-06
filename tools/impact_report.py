"""Report PR-code validator impact results from the trusted workflow bridge."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from report_lib import (
    MANIFEST_NAME as REPORT_MANIFEST_NAME,
)
from report_lib import (
    artifact_members,
    clear_comment,
    load_all,
    load_manifest,
    post_checks,
    post_comment,
    render,
    validate_manifest,
)
from report_lib.models import Issue, ReportContext, Severity, ValidatorRun

IMPACT_WORKFLOW_NAME = "Validator impact"
IMPACT_WORKFLOW_PATH = ".github/workflows/validator-impact.yml"
IMPACT_ARTIFACT_NAME = "validator-impact-results"
IMPACT_MARKER = "<!-- md-validator-impact-report:v1 -->"
IMPACT_REPORT_TITLE = "Validator Impact Report"
IMPACT_CHECK_PREFIX = "Impact / "
MANIFEST_NAME = REPORT_MANIFEST_NAME

_MEMBER_RE = re.compile(
    r"^(?:validation-[a-z0-9]+(?:-[a-z0-9]+)*\.(?:log|json)|"
    r"validation-[a-z0-9]+(?:-[a-z0-9]+)*\.stderr\.log|batch-manifest\.json)$"
)
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
_API_TIMEOUT = 60


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(
            req.full_url, code, "redirect rejected", headers, fp
        )


def _open_api(request: urllib.request.Request):
    if not request.full_url.startswith("https://api.github.com/"):
        raise ValueError("refusing non-GitHub API URL")
    opener = urllib.request.build_opener(_NoRedirect())
    return opener.open(request, timeout=_API_TIMEOUT)


def _api_request(url: str, token: str, accept: str = "application/vnd.github+json"):
    request = urllib.request.Request(url, headers=_headers(token, accept))
    with _open_api(request) as response:
        return response.read()


def _headers(token: str, accept: str = "application/vnd.github+json") -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _api_json(url: str, token: str):
    return json.loads(_api_request(url, token).decode("utf-8"))


def _api_pages(url: str, token: str, key: Optional[str] = None) -> List[Dict[str, Any]]:
    separator = "&" if "?" in url else "?"
    page = 1
    items: List[Dict[str, Any]] = []
    while True:
        payload = _api_json(f"{url}{separator}per_page=100&page={page}", token)
        batch = payload
        if key is not None:
            if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
                raise ValueError(f"GitHub API pagination has no {key} list")
            batch = payload[key]
        if not isinstance(batch, list) or not all(
            isinstance(item, dict) for item in batch
        ):
            raise ValueError("GitHub API pagination returned invalid items")
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def _api_json_pages(url: str, token: str) -> List[Dict[str, Any]]:
    return _api_pages(url, token)


def _api_dict_pages(url: str, key: str, token: str) -> List[Dict[str, Any]]:
    return _api_pages(url, token, key)


def load_workflow_run_event(path: str) -> Dict[str, Any]:
    """Read workflow_run from the trusted GitHub event payload."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("workflow event payload is unreadable") from exc
    event = payload.get("workflow_run") if isinstance(payload, dict) else None
    if not isinstance(event, dict):
        raise ValueError("workflow event payload has no workflow_run object")
    return event


def verify_workflow_run(event: Dict[str, Any], repo: str) -> Optional[str]:
    """Return a failure reason, or None when the workflow_run is ours."""
    if event.get("name") != IMPACT_WORKFLOW_NAME:
        return f"workflow name mismatch: {event.get('name')!r}"
    if event.get("path") not in (None, IMPACT_WORKFLOW_PATH):
        return f"workflow path mismatch: {event.get('path')!r}"
    if event.get("event") != "pull_request":
        return f"workflow was not triggered by a pull_request: {event.get('event')!r}"
    repository = event.get("repository")
    if not isinstance(repository, dict) or repository.get("full_name") != repo:
        return "workflow repository mismatch"
    if type(event.get("workflow_id")) is not int:
        return "workflow run workflow_id missing"
    if type(event.get("id")) is not int or type(event.get("run_attempt")) is not int:
        return "workflow run id/attempt missing"
    if not isinstance(event.get("head_branch"), str) or not event["head_branch"]:
        return "workflow run head branch missing"
    head_repository_data = event.get("head_repository")
    head_repository = (
        head_repository_data.get("full_name")
        if isinstance(head_repository_data, dict)
        else None
    )
    if not isinstance(head_repository, str) or not head_repository:
        return "workflow run head repository missing"
    head_sha = event.get("head_sha") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        return f"workflow run head_sha is not a commit: {head_sha!r}"
    return None


def verify_api_run(
    event: Dict[str, Any], api_run: Dict[str, Any], repo: str
) -> Optional[str]:
    """Verify the workflow-run event against the authoritative API record."""
    if not isinstance(api_run, dict):
        return "workflow run API record is not an object"
    if type(api_run.get("id")) is not int or api_run.get("id") != event.get("id"):
        return "workflow run id does not match the API record"
    for key in ("name", "event", "head_sha", "run_attempt"):
        if api_run.get(key) != event.get(key):
            return f"workflow run {key} does not match the API record"
    if "path" in api_run and api_run.get("path") != event.get("path"):
        return "workflow run path does not match the API record"
    repository = api_run.get("repository")
    if not isinstance(repository, dict) or repository.get("full_name") != repo:
        return "workflow run repository does not match the reporting repository"
    if type(api_run.get("workflow_id")) is not int:
        return "workflow run workflow_id is missing"
    if event.get("workflow_id") != api_run["workflow_id"]:
        return "workflow run workflow_id does not match the event"
    head_repository_data = api_run.get("head_repository")
    head_repository = (
        head_repository_data.get("full_name")
        if isinstance(head_repository_data, dict)
        else None
    )
    head_branch = api_run.get("head_branch")
    if not isinstance(head_repository, str) or not head_repository:
        return "workflow run head repository is missing"
    if not isinstance(head_branch, str) or not head_branch:
        return "workflow run head branch is missing"
    event_head_repository_data = event.get("head_repository")
    event_head_repository = (
        event_head_repository_data.get("full_name")
        if isinstance(event_head_repository_data, dict)
        else None
    )
    if head_repository != event_head_repository:
        return "workflow run head repository does not match the event"
    if head_branch != event.get("head_branch"):
        return "workflow run head branch does not match the event"
    return None


def verify_workflow_definition(
    event: Dict[str, Any], workflow: Dict[str, Any], repo: str
) -> Optional[str]:
    """Verify the workflow id and path from the repository API."""
    if not isinstance(workflow, dict):
        return "workflow definition API record is not an object"
    if type(workflow.get("id")) is not int or workflow.get("id") != event.get(
        "workflow_id"
    ):
        return "workflow definition id does not match the run"
    if workflow.get("path") != IMPACT_WORKFLOW_PATH:
        return "workflow definition path mismatch"
    if workflow.get("name") != IMPACT_WORKFLOW_NAME:
        return "workflow definition name mismatch"
    workflow_repository = workflow.get("repository")
    if isinstance(workflow_repository, dict) and workflow_repository.get(
        "full_name"
    ) not in (None, repo):
        return "workflow definition repository mismatch"
    return None


def newer_run_reason(
    source: Dict[str, Any], candidates: List[Dict[str, Any]]
) -> Optional[str]:
    """Reject a completed run superseded by another run for the same head."""
    source_id = source.get("id")
    source_attempt = source.get("run_attempt")
    if type(source_attempt) is not int:
        return "could not verify workflow run attempts"
    source_number = source.get("run_number")
    source_created = source.get("created_at")
    for candidate in candidates:
        if type(candidate.get("id")) is not int:
            return "could not verify workflow run ids"
        if candidate.get("event") != "pull_request":
            continue
        if candidate.get("head_sha") != source.get("head_sha"):
            continue
        if candidate.get("workflow_id") != source.get("workflow_id"):
            continue
        candidate_repository = candidate.get("repository")
        source_repository = source.get("repository")
        if not isinstance(candidate_repository, dict) or not isinstance(
            source_repository, dict
        ):
            return "could not verify workflow run repositories"
        if candidate_repository.get("full_name") != source_repository.get("full_name"):
            continue
        candidate_head_repository = candidate.get("head_repository")
        source_head_repository = source.get("head_repository")
        if not isinstance(candidate_head_repository, dict) or not isinstance(
            source_head_repository, dict
        ):
            return "could not verify workflow run head repositories"
        if candidate_head_repository.get("full_name") != source_head_repository.get(
            "full_name"
        ):
            continue
        if candidate.get("head_branch") != source.get("head_branch"):
            continue
        if candidate.get("id") == source_id:
            candidate_attempt = candidate.get("run_attempt")
            if type(candidate_attempt) is not int:
                return "could not verify workflow run attempts"
            if candidate_attempt > source_attempt:
                return "a newer attempt superseded this workflow run"
            continue
        newer = False
        comparable_number = (
            type(candidate.get("run_number")) is int and type(source_number) is int
        )
        comparable_created = isinstance(
            candidate.get("created_at"), str
        ) and isinstance(source_created, str)
        if comparable_number and candidate["run_number"] > source_number:
            newer = True
        elif comparable_created and candidate["created_at"] > source_created:
            newer = True
        elif not (comparable_number or comparable_created):
            return "could not establish workflow run ordering"
        if newer:
            return f"workflow run {candidate.get('id')} superseded this run"
    return None


def select_pull_request(
    pulls: List[Dict[str, Any]], event: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Pick the one open PR matching the run's SHA, repo, and branch."""
    head_sha = event.get("head_sha")
    run_head_repository_data = event.get("head_repository")
    run_head_repo = (
        run_head_repository_data.get("full_name")
        if isinstance(run_head_repository_data, dict)
        else None
    )
    run_head_branch = event.get("head_branch")
    if not isinstance(run_head_repo, str) or not isinstance(run_head_branch, str):
        return None, "workflow run lacks a verifiable head repository or branch"
    matching = []
    for pr in pulls:
        head = pr.get("head")
        head_repo = head.get("repo") if isinstance(head, dict) else None
        if (
            pr.get("state") == "open"
            and isinstance(head, dict)
            and head.get("sha") == head_sha
            and head.get("ref") == run_head_branch
            and isinstance(head_repo, dict)
            and head_repo.get("full_name") == run_head_repo
        ):
            matching.append(pr)
    if len(matching) != 1:
        return None, (
            f"expected exactly one open PR with head {head_sha}, repo "
            f"{run_head_repo!r}, branch {run_head_branch!r}; found {len(matching)}"
        )
    if type(matching[0].get("number")) is not int:
        return None, "matching PR has no valid number"
    return matching[0], None


def staleness_reason(
    event: Dict[str, Any], current_pr: Dict[str, Any]
) -> Optional[str]:
    """Return a reason when the run no longer reflects the current PR."""
    if not isinstance(current_pr, dict):
        return "current PR API record is not an object"
    head = current_pr.get("head")
    if not isinstance(head, dict):
        return "current PR head metadata is missing"
    current_sha = head.get("sha")
    if current_sha != event.get("head_sha"):
        return (
            f"the PR head has moved since this run "
            f"({event.get('head_sha', '')[:7]} -> {str(current_sha)[:7]})"
        )
    current_repo = head.get("repo")
    event_repo = event.get("head_repository")
    if not isinstance(current_repo, dict) or not isinstance(event_repo, dict):
        return "the PR head repository metadata is missing"
    if current_repo.get("full_name") != event_repo.get("full_name"):
        return "the PR head repository no longer matches this run"
    if head.get("ref") != event.get("head_branch"):
        return "the PR head branch no longer matches this run"
    if current_pr.get("state") != "open":
        return f"the PR is no longer open (state {current_pr.get('state')!r})"
    return None


def cross_check(
    runs: List[ValidatorRun],
    manifest: Dict[str, Any],
    members: Optional[Dict[str, List[Tuple[str, Path]]]] = None,
) -> List[str]:
    """Reconcile selected validators, execution metadata, and artifact files."""
    try:
        validate_manifest(manifest)
    except ValueError as exc:
        return [str(exc)]

    problems: List[str] = []
    selected = set(manifest["selected"])
    result_names = {entry["name"] for entry in manifest["results"]}
    run_names = {run.name for run in runs}
    for name in sorted(selected - result_names):
        problems.append(f"validator {name} is selected but missing from results")
    for name in sorted(result_names - selected):
        problems.append(f"result {name} is not in the manifest selection")
    for name in sorted(selected - run_names):
        problems.append(f"validator {name} was selected but produced no result files")
    for name in sorted(run_names - selected):
        problems.append(f"result files for {name} were not in the manifest selection")

    if members is not None:
        member_names = set(members)
        for name in sorted(selected - member_names):
            problems.append(f"validator {name} is missing from the artifact")
        for name in sorted(member_names - selected):
            problems.append(f"artifact contains unselected validator {name}")
        for name in sorted(selected & member_names):
            kinds = [kind for kind, _path in members[name]]
            if sorted(kinds) != ["json", "log"]:
                problems.append(
                    f"validator {name} must have exactly one log and JSON sidecar"
                )

    by_name = {run.name: run for run in runs}
    for entry in manifest["results"]:
        name = entry["name"]
        run = by_name.get(name)
        if run is None:
            continue
        failed = entry["status"] in {"crash", "missing"} or entry["returncode"] != 0
        if failed and run.status != "failed":
            problems.append(
                f"validator {name} reported no trustworthy verdict: "
                f"exit {entry['returncode']} ({entry['status']})"
            )
    return problems


def apply_execution_metadata(
    runs: List[ValidatorRun], manifest: Dict[str, Any]
) -> List[ValidatorRun]:
    """Apply manifest execution outcomes to loaded runs."""
    by_name = {run.name: run for run in runs}
    for entry in manifest["results"]:
        run = by_name.get(entry["name"])
        if run is None:
            continue
        run.strict = entry["strict"]
        failed = entry["status"] in {"crash", "missing"} or entry["returncode"] != 0
        if failed:
            run.execution_complete = False
            if run.status == "passed":
                run.status = "failed"
                run.errors += 1
                run.issues.append(
                    Issue(
                        severity=Severity.ERROR,
                        category="impact-run-incomplete",
                        message=(
                            f"validator exited {entry['returncode']} "
                            f"({entry['status']}); no trustworthy verdict"
                        ),
                        validator=run.name,
                    )
                )
    return runs


def safe_extract(zip_path: Path, dest: Path) -> List[str]:
    """Unpack only expected flat result files into dest."""
    extracted: List[str] = []
    dest.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(zip_path) as archive:
        members = [member for member in archive.infolist() if not member.is_dir()]
        seen = set()
        for member in members:
            normalized = member.filename.replace("\\", "/")
            name = Path(normalized).name
            if normalized != name or not _MEMBER_RE.fullmatch(name):
                raise ValueError(f"unexpected artifact member: {member.filename!r}")
            if name in seen:
                raise ValueError(f"duplicate artifact member: {name!r}")
            seen.add(name)
            total += member.file_size
            if member.file_size > MAX_MEMBER_BYTES or total > MAX_ARTIFACT_BYTES:
                raise ValueError(f"artifact member too large: {member.filename!r}")
        if not members:
            raise ValueError("artifact held no result files")
        dest.mkdir(parents=True, exist_ok=True)
        for member in members:
            name = Path(member.filename).name
            target = dest / name
            with archive.open(member) as source, open(target, "wb") as output:
                output.write(source.read(MAX_MEMBER_BYTES + 1))
                if output.tell() > MAX_MEMBER_BYTES:
                    raise ValueError(f"artifact member too large: {member.filename!r}")
            extracted.append(name)
    return extracted


def find_artifact(
    artifacts: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    candidates = [
        artifact
        for artifact in artifacts
        if artifact.get("name") == IMPACT_ARTIFACT_NAME and not artifact.get("expired")
    ]
    if len(candidates) != 1 or type(candidates[0].get("id")) is not int:
        return None, (
            f"expected exactly one valid {IMPACT_ARTIFACT_NAME} artifact on this run, "
            f"found {len(candidates)}"
        )
    return candidates[0], None


def build_report_body(
    runs: List[ValidatorRun],
    ctx: ReportContext,
) -> Tuple[str, str]:
    issues = [issue for run in runs for issue in run.issues]
    comment_body = render(
        runs,
        issues,
        ctx,
        include_raw_logs=False,
        include_validator_sections=False,
    )
    step_body = render(runs, issues, ctx)
    return comment_body, step_body


def report_is_clean(runs: List[ValidatorRun], problems: List[str]) -> bool:
    """True when a complete run has no findings, including an empty run."""
    return not problems and all(
        run.execution_complete and run.status == "passed" for run in runs
    )


def report_should_fail(runs: List[ValidatorRun], problems: List[str]) -> bool:
    """Return whether incomplete results or strict findings fail the job."""
    if problems:
        return True
    return any(
        not run.execution_complete
        or (
            run.status in {"failed", "unknown", "no_output"} and run.strict is not False
        )
        for run in runs
    )


def _open_artifact_redirect(location: str):
    parsed = urllib.parse.urlparse(location)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith(
        ".blob.core.windows.net"
    ):
        raise ValueError("refusing an unexpected artifact redirect")
    request = urllib.request.Request(
        location, headers={"Accept": "application/octet-stream"}
    )
    opener = urllib.request.build_opener(_NoRedirect())
    return opener.open(request, timeout=_API_TIMEOUT)


def _download_to_file(url: str, token: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers=_headers(token))
    try:
        response = _open_api(request)
    except urllib.error.HTTPError as exc:
        if exc.code not in {301, 302, 303, 307, 308}:
            raise
        location = exc.headers.get("Location")
        if not location:
            raise ValueError("artifact redirect has no location") from exc
        response = _open_artifact_redirect(location)
    with response:
        with open(dest, "wb") as output:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_ARTIFACT_BYTES:
                    raise ValueError("downloaded artifact is too large")
                output.write(chunk)


def _load_results(results_dir: Path) -> Tuple[List[ValidatorRun], List[str]]:
    """Load runs plus verification problems from the unpacked artifact."""
    problems: List[str] = []
    runs = load_all(str(results_dir))
    manifest_path = results_dir / MANIFEST_NAME
    if manifest_path.is_file():
        try:
            manifest = load_manifest(manifest_path)
            problems.extend(
                cross_check(runs, manifest, artifact_members(str(results_dir)))
            )
            apply_execution_metadata(runs, manifest)
        except ValueError as exc:
            problems.append(str(exc))
    else:
        problems.append(f"artifact held no {MANIFEST_NAME}")
    # Treat incomplete or stray runs as unverifiable.
    for run in runs:
        if run.status in {"unknown", "no_output"}:
            problems.append(f"validator {run.name} produced no complete result")
    return runs, problems


def _verification_run(problems: List[str]) -> ValidatorRun:
    return ValidatorRun(
        name="impact-verification",
        title="Impact report verification",
        issues=[
            Issue(
                severity=Severity.ERROR,
                category="impact-report-incomplete",
                message=problem,
                validator="impact-verification",
            )
            for problem in problems
        ],
        status="failed",
        errors=len(problems),
    )


def _report_ctx(
    event: Dict[str, Any], run_url: str, pr_number: Optional[str], repo: str
) -> ReportContext:
    return ReportContext(
        pr_number=pr_number,
        commit_sha=event.get("head_sha"),
        workflow_run_url=run_url,
        artifact_url="",
        date_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        repo=repo,
        validation_scope="preview",
        report_marker=IMPACT_MARKER,
        report_title=IMPACT_REPORT_TITLE,
    )


def _run_url(event: Dict[str, Any], repo: str) -> str:
    return f"https://github.com/{repo}/actions/runs/{event.get('id', 0)}"


def _write_outputs(output: str, step_body: str, comment_body: str) -> None:
    with open(output, "w", encoding="utf-8", newline="") as handle:
        handle.write(comment_body)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "w", encoding="utf-8", newline="") as handle:
            handle.write(step_body)


def _post_report(
    runs: List[ValidatorRun],
    body: str,
    clean: bool,
    head_sha: str,
    repo_owner: str,
    repo_name: str,
    pr_number: str,
    token: str,
) -> int:
    exit_code = 0
    if clean:
        success, message = clear_comment(
            repo_owner, repo_name, pr_number, token, marker=IMPACT_MARKER
        )
    else:
        success, message = post_comment(
            repo_owner, repo_name, pr_number, body, token, marker=IMPACT_MARKER
        )
    (print if success else _err)(f"impact PR comment: {message}")
    if not success:
        # Never silently replace an older failure with a clean report.
        exit_code = 1

    for title, success, message in post_checks(
        repo_owner, repo_name, head_sha, runs, token, name_prefix=IMPACT_CHECK_PREFIX
    ):
        (print if success else _err)(f"Check Run '{title}': {message}")
        if not success:
            exit_code = 1
    return exit_code


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def current_association_reason(
    event: Dict[str, Any], api: str, token: str, pr_number: str
) -> Optional[str]:
    """Recheck the source run and PR immediately before publishing."""
    try:
        source = _api_json(f"{api}/actions/runs/{event['id']}", token)
        reason = verify_api_run(
            event, source, api.removeprefix("https://api.github.com/repos/")
        )
        if reason:
            return reason
        workflow = _api_json(f"{api}/actions/workflows/{event['workflow_id']}", token)
        reason = verify_workflow_definition(
            event, workflow, api.removeprefix("https://api.github.com/repos/")
        )
        if reason:
            return reason
        candidates = _api_dict_pages(
            f"{api}/actions/runs?head_sha={event['head_sha']}&event=pull_request",
            "workflow_runs",
            token,
        )
        reason = newer_run_reason(source, candidates)
        if reason:
            return reason
        current_pr = _api_json(f"{api}/pulls/{pr_number}", token)
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError) as exc:
        return f"could not recheck source association: {exc}"
    return staleness_reason(event, current_pr)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow-run-json",
        default=os.environ.get("GITHUB_EVENT_PATH"),
    )
    parser.add_argument("--results-dir", default="impact-results")
    parser.add_argument("--download-dir", default="impact-download")
    parser.add_argument("--output", default="impact-report.md")
    parser.add_argument(
        "--github-repository", default=os.environ.get("GITHUB_REPOSITORY")
    )
    parser.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"))
    args = parser.parse_args(argv)

    if (
        not args.github_repository
        or not args.github_token
        or not args.workflow_run_json
    ):
        print(
            "GITHUB_EVENT_PATH, GITHUB_REPOSITORY, and GITHUB_TOKEN are required",
            file=sys.stderr,
        )
        return 1
    repo_parts = args.github_repository.split("/")
    if len(repo_parts) != 2 or not all(repo_parts):
        print("--github-repository must be owner/repo", file=sys.stderr)
        return 1
    repo_owner, repo_name = repo_parts
    api = f"https://api.github.com/repos/{args.github_repository}"
    token = args.github_token

    event_error: Optional[str]
    try:
        event = load_workflow_run_event(args.workflow_run_json)
    except ValueError as exc:
        event = {}
        event_error = str(exc)
    else:
        event_error = verify_workflow_run(event, args.github_repository)

    pr_holder: Dict[str, Optional[str]] = {"number": None}
    run_url = _run_url(event, args.github_repository)

    def emit_incomplete(reason: str, publish: bool = False) -> int:
        runs = [_verification_run([reason])]
        body, step_body = build_report_body(
            runs,
            _report_ctx(event, run_url, pr_holder["number"], args.github_repository),
        )
        _write_outputs(args.output, step_body, body)
        if publish and pr_holder["number"]:
            publish_reason = current_association_reason(
                event, api, token, pr_holder["number"]
            )
            if publish_reason is None:
                _post_report(
                    runs,
                    body,
                    clean=False,
                    head_sha=event.get("head_sha", ""),
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    pr_number=pr_holder["number"],
                    token=token,
                )
            else:
                _err(f"incomplete report not posted: {publish_reason}")
        else:
            _err("no verified current PR; posting skipped")
        _err(f"Incomplete impact report: {reason}")
        return 1

    if event_error:
        return emit_incomplete(event_error)

    try:
        source = _api_json(f"{api}/actions/runs/{event['id']}", token)
        reason = verify_api_run(event, source, args.github_repository)
        if reason:
            return emit_incomplete(reason)
        workflow = _api_json(f"{api}/actions/workflows/{event['workflow_id']}", token)
        reason = verify_workflow_definition(event, workflow, args.github_repository)
        if reason:
            return emit_incomplete(reason)
        newer = newer_run_reason(
            source,
            _api_dict_pages(
                f"{api}/actions/runs?head_sha={event['head_sha']}&event=pull_request",
                "workflow_runs",
                token,
            ),
        )
        if newer:
            return emit_incomplete(newer)
        pulls = _api_json_pages(f"{api}/commits/{event['head_sha']}/pulls", token)
        pr, reason = select_pull_request(pulls, event)
        if pr is None:
            return emit_incomplete(reason or "no matching pull request")
        pr_number = str(pr["number"])
        pr_holder["number"] = pr_number
        current_pr = _api_json(f"{api}/pulls/{pr_number}", token)
        stale = staleness_reason(event, current_pr)
        if stale:
            return emit_incomplete(f"stale run: {stale}")
        artifacts = _api_dict_pages(
            f"{api}/actions/runs/{event['id']}/artifacts", "artifacts", token
        )
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError) as exc:
        return emit_incomplete(f"could not verify impact source: {exc}", publish=True)

    artifact, reason = find_artifact(artifacts)
    if artifact is None:
        return emit_incomplete(reason or "artifact not found", publish=True)
    artifact_run = artifact.get("workflow_run")
    if (
        not isinstance(artifact_run, dict)
        or type(artifact_run.get("id")) is not int
        or artifact_run["id"] != event["id"]
    ):
        return emit_incomplete(
            "artifact does not belong to the triggering run", publish=True
        )

    download_dir = Path(args.download_dir)
    results_dir = Path(args.results_dir)
    zip_path = download_dir / f"{IMPACT_ARTIFACT_NAME}.zip"
    try:
        download_dir.mkdir(parents=True, exist_ok=True)
        _download_to_file(
            f"{api}/actions/artifacts/{artifact['id']}/zip", token, zip_path
        )
        extracted = safe_extract(zip_path, results_dir)
        print(f"Unpacked {len(extracted)} result file(s) into {results_dir}.")
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as exc:
        return emit_incomplete(f"artifact unpack failed: {exc}", publish=True)

    runs, problems = _load_results(results_dir)
    if event.get("conclusion") not in (None, "success"):
        problems.append(f"impact workflow concluded {event.get('conclusion')!r}")

    final_reason = current_association_reason(event, api, token, pr_number)
    if final_reason:
        problems.append(f"report not published: {final_reason}")
        can_publish = False
    else:
        can_publish = True
    if problems:
        runs = list(runs) + [_verification_run(problems)]

    clean = report_is_clean(runs, problems)
    body, step_body = build_report_body(
        runs, _report_ctx(event, run_url, pr_number, args.github_repository)
    )
    _write_outputs(args.output, step_body, body)
    if not can_publish:
        _err("Impact report is stale or unverifiable; posting and cleanup skipped.")
        return 1
    exit_code = _post_report(
        runs,
        body,
        clean=clean,
        head_sha=event["head_sha"],
        repo_owner=repo_owner,
        repo_name=repo_name,
        pr_number=pr_number,
        token=token,
    )
    if exit_code:
        return exit_code
    if report_should_fail(runs, problems):
        _err("Impact validation failed; see the posted report.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
