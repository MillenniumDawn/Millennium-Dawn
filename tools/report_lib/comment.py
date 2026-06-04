"""Post (or update) the validation report as a PR comment.

Comment discovery uses a hidden HTML marker emitted by `markdown.render()`
so renaming the title or restructuring the body never creates duplicate
comments. Falls back to the legacy "Validation Report" title-string match
to cleanly take over comments posted before the marker existed.
"""

import json
import urllib.error
import urllib.request
from typing import Optional, Tuple

REPORT_MARKER = "<!-- md-validation-report:v1 -->"


def find_existing_comment(comments: list) -> Optional[dict]:
    """Return the bot-authored validation report comment, or None.

    Prefers marker match; falls back to legacy title-string match.
    """
    marker_match = None
    legacy_match = None
    for comment in comments:
        if comment.get("user", {}).get("type") != "Bot":
            continue
        body = comment.get("body", "")
        if REPORT_MARKER in body and marker_match is None:
            marker_match = comment
        elif "Validation Report" in body and legacy_match is None:
            legacy_match = comment
    return marker_match or legacy_match


def post_comment(
    repo_owner: str,
    repo_name: str,
    pr_number: str,
    body: str,
    github_token: str,
) -> Tuple[bool, str]:
    """Create or update the validation report PR comment.

    Returns (success, message).
    """
    api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = _auth_headers(github_token)

    try:
        comments = _get(f"{api_base}/issues/{pr_number}/comments", headers)
    except urllib.error.HTTPError as e:
        return False, _fmt_http_error("list comments", e)
    except Exception as e:
        return False, f"list comments: {e}"

    existing = find_existing_comment(comments)
    try:
        if existing:
            comment_id = existing["id"]
            _patch(
                f"{api_base}/issues/comments/{comment_id}",
                {"body": body},
                headers,
            )
            return True, f"updated comment #{comment_id}"
        else:
            result = _post(
                f"{api_base}/issues/{pr_number}/comments",
                {"body": body},
                headers,
            )
            return True, f"created comment #{result.get('id', '?')}"
    except urllib.error.HTTPError as e:
        return False, _fmt_http_error("post comment", e)
    except Exception as e:
        return False, f"post comment: {e}"


def _auth_headers(github_token: str) -> dict:
    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def _get(url: str, headers: dict) -> list:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _patch(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fmt_http_error(label: str, e: urllib.error.HTTPError) -> str:
    try:
        detail = e.read().decode("utf-8")
    except Exception:
        detail = "<no body>"
    return f"{label}: HTTP {e.code} — {detail[:300]}"
