"""Publish an untrusted report artifact using only trusted workflow code."""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from report_lib.comment import REPORT_MARKER, clear_comment, post_comment

_RUN_TITLE = re.compile(
    r"Validate PR #(?P<pr>[1-9][0-9]*|current) "
    r"head=(?P<head>[0-9a-f]{40}) base=[0-9a-f]{40}"
)
_MAX_PAYLOAD_BYTES = 256_000


def _get_json(url, token):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except json.JSONDecodeError as exc:
        raise ValueError("GitHub returned invalid JSON") from exc


def _load_payload(path):
    if path.is_symlink():
        raise ValueError("Comment payload must not be a symbolic link")
    with path.open("rb") as handle:
        data = handle.read(_MAX_PAYLOAD_BYTES + 1)
    if len(data) > _MAX_PAYLOAD_BYTES:
        raise ValueError("Comment payload is too large")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("Malformed comment payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("Comment payload must be an object")
    body = payload.get("body")
    if (
        type(payload.get("should_post")) is not bool
        or not isinstance(body, str)
        or not body.startswith(f"{REPORT_MARKER}\n# Test Suite Report\n")
        or len(body.encode("utf-8")) > 65_536
    ):
        raise ValueError("Invalid comment payload")
    return payload


def publish_report(event, payload_path, repository, token):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid repository")
    source = event["workflow_run"]
    run_id = source["id"]
    if event["action"] != "completed" or type(run_id) is not int or run_id <= 0:
        raise ValueError("Expected a completed workflow_run event")
    api_base = f"https://api.github.com/repos/{repository}"
    run = _get_json(f"{api_base}/actions/runs/{run_id}", token)
    if (
        run["id"] != run_id
        or run["repository"]["full_name"] != repository
        or run["path"] != ".github/workflows/test-suite.yml"
        or run["event"] not in {"pull_request", "workflow_dispatch"}
    ):
        raise ValueError("Report did not come from this repository's Test Suite")
    if (
        run["status"] != "completed"
        or run["conclusion"] == "cancelled"
        or run["run_attempt"] != source["run_attempt"]
    ):
        return True, "Source run was cancelled or superseded; comment left as is"

    target = _RUN_TITLE.fullmatch(run["display_title"])
    if target is None:
        raise ValueError("Source run does not identify its PR and validated commit")
    pr_number, head_sha = target.group("pr", "head")
    if pr_number == "current" and run["event"] == "workflow_dispatch":
        return True, "Run has no PR; no comment to publish"
    if run["event"] == "pull_request" and run["head_sha"] != head_sha:
        raise ValueError("Validated commit does not match the source run")

    payload = _load_payload(payload_path)
    if (
        payload.get("pr_number") != pr_number
        or payload.get("commit_sha") != head_sha
        or payload.get("run_id") != str(run_id)
        or payload.get("run_attempt") != str(run["run_attempt"])
    ):
        raise ValueError(
            "Comment payload does not match the source run, PR, and commit"
        )
    pr = _get_json(f"{api_base}/pulls/{pr_number}", token)
    if str(pr["number"]) != pr_number or (
        pr["base"]["repo"]["full_name"] != repository or pr["base"]["ref"] != "main"
    ):
        raise ValueError("Report targets a different repository or base branch")
    if pr["state"] != "open" or pr["head"]["sha"] != head_sha:
        return True, "PR closed or head moved; comment left as is"
    if run["event"] == "pull_request":
        if (
            pr["head"]["repo"]["full_name"] != run["head_repository"]["full_name"]
            or pr["head"]["ref"] != run["head_branch"]
        ):
            raise ValueError(
                "PR does not belong to the source run's repository and branch"
            )
    elif pr["head"]["repo"]["full_name"] != repository:
        raise ValueError("Dispatched validation must target a same-repository PR")

    owner, name = repository.split("/")
    if payload["should_post"]:
        # Artifact text must not send notifications chosen by fork code.
        body = payload["body"].replace("@", "@\u200b")
        return post_comment(owner, name, pr_number, body, token)
    return clear_comment(owner, name, pr_number, token)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        repository = os.environ["GITHUB_REPOSITORY"]
        token = os.environ["GITHUB_TOKEN"]
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
            event = json.load(handle)
        success, message = publish_report(event, args.payload, repository, token)
    except (KeyError, TypeError, OSError, ValueError) as exc:
        print(f"Unable to publish validation report: {exc}", file=sys.stderr)
        return 1
    print(f"PR comment: {message}", file=sys.stderr)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
