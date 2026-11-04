"""Trust-boundary and CLI contracts for publishing validation artifacts."""

import io
import json
import urllib.error

import publish_validation_report as publisher
import pytest
from report_lib.comment import REPORT_MARKER
from shared.suite import run_tool_script, write_under_str

_HEAD = "a" * 40
_BASE = "b" * 40
_BODY = f"{REPORT_MARKER}\n# Test Suite Report\n\nFinding from @someone\n"


@pytest.fixture
def publishing(tmp_path, monkeypatch):
    run = {
        "id": 7,
        "run_attempt": 2,
        "repository": {"full_name": "owner/repo"},
        "head_repository": {"full_name": "author/fork"},
        "head_branch": "topic",
        "head_sha": _HEAD,
        "event": "pull_request",
        "path": ".github/workflows/test-suite.yml",
        "display_title": f"Validate PR #42 head={_HEAD} base={_BASE}",
        "status": "completed",
        "conclusion": "success",
    }
    pr = {
        "number": 42,
        "state": "open",
        "base": {"repo": {"full_name": "owner/repo"}, "ref": "main"},
        "head": {
            "sha": _HEAD,
            "ref": "topic",
            "repo": {"full_name": "author/fork"},
        },
    }
    event = {"action": "completed", "workflow_run": {"id": 7, "run_attempt": 2}}
    payload = {
        "pr_number": "42",
        "commit_sha": _HEAD,
        "run_id": "7",
        "run_attempt": "2",
        "should_post": True,
        "body": _BODY,
    }
    calls = []

    def get_json(url, token):
        assert token == "token"
        if url == "https://api.github.com/repos/owner/repo/actions/runs/7":
            return run
        assert url == "https://api.github.com/repos/owner/repo/pulls/42"
        return pr

    monkeypatch.setattr(publisher, "_get_json", get_json)
    for name in ("post_comment", "clear_comment"):
        monkeypatch.setattr(
            publisher,
            name,
            lambda *args, operation=name: calls.append((operation, args))
            or (True, "synchronized"),
        )
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    event_path = write_under_str(tmp_path, "event.json", json.dumps(event))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    return run, pr, payload, calls


# Object, field path, replacement, exit code, comment operation.
_PUBLISH_CASES = [
    pytest.param("payload", "should_post", True, 0, "post_comment", id="fork findings"),
    pytest.param("payload", "should_post", False, 0, "clear_comment", id="clean fork"),
    pytest.param("pr", "state", "closed", 0, None, id="closed PR"),
    pytest.param("pr", "head.sha", _BASE, 0, None, id="newer PR head"),
    pytest.param("run", "run_attempt", 3, 0, None, id="superseded attempt"),
    pytest.param("run", "status", "in_progress", 0, None, id="rerun active"),
    pytest.param("run", "conclusion", "cancelled", 0, None, id="cancelled run"),
    pytest.param("run", "id", 8, 1, None, id="wrong run"),
    pytest.param("run", "repository.full_name", "other/repo", 1, None, id="wrong repo"),
    pytest.param(
        "run", "path", ".github/workflows/other.yml", 1, None, id="wrong workflow"
    ),
    pytest.param("run", "event", "push", 1, None, id="wrong event"),
    pytest.param("run", "display_title", "custom run", 1, None, id="unpinned target"),
    pytest.param("run", "head_sha", _BASE, 1, None, id="forged validated commit"),
    pytest.param(
        "payload", "pr_number", "99", 1, None, id="artifact targets another PR"
    ),
    pytest.param(
        "payload", "commit_sha", _BASE, 1, None, id="artifact targets another commit"
    ),
    pytest.param("payload", "run_id", "8", 1, None, id="artifact from another run"),
    pytest.param("payload", "run_attempt", "1", 1, None, id="old attempt artifact"),
    pytest.param("payload", "should_post", "false", 1, None, id="nonboolean action"),
    pytest.param("payload", "body", None, 1, None, id="nontext body"),
    pytest.param("payload", "body", "unmarked text", 1, None, id="wrong report marker"),
    pytest.param(
        "payload", "body", _BODY + "x" * 65_536, 1, None, id="oversize comment"
    ),
    pytest.param("pr", "number", 99, 1, None, id="wrong API PR"),
    pytest.param("pr", "base.repo.full_name", "other/repo", 1, None, id="foreign base"),
    pytest.param("pr", "base.ref", "release", 1, None, id="wrong base branch"),
    pytest.param(
        "pr", "head.repo.full_name", "other/fork", 1, None, id="wrong head repo"
    ),
    pytest.param("pr", "head.ref", "other", 1, None, id="wrong head branch"),
]


@pytest.mark.parametrize("object_name,field,value,code,operation", _PUBLISH_CASES)
def test_main_binds_comment_writes_to_the_source_run(
    tmp_path, publishing, object_name, field, value, code, operation
):
    run, pr, payload, calls = publishing
    target = {"run": run, "pr": pr, "payload": payload}[object_name]
    *parents, leaf = field.split(".")
    for parent in parents:
        target = target[parent]
    target[leaf] = value
    path = write_under_str(tmp_path, "comment.json", json.dumps(payload))

    assert publisher.main(["--payload", str(path)]) == code

    if operation is None:
        assert not calls
    else:
        expected_args = ["owner", "repo", "42"]
        if operation == "post_comment":
            expected_args.append(_BODY.replace("@", "@\u200b"))
        expected_args.append("token")
        assert calls == [(operation, tuple(expected_args))]


@pytest.mark.parametrize(
    "head_repository,number,code,posts",
    [
        pytest.param("owner/repo", "42", 0, True, id="same-repo dispatch"),
        pytest.param("author/fork", "42", 1, False, id="fork dispatch rejected"),
        pytest.param("owner/repo", "current", 0, False, id="dispatch without a PR"),
    ],
)
def test_dispatch_uses_its_pinned_target_not_the_workflow_commit(
    tmp_path, publishing, head_repository, number, code, posts
):
    run, pr, payload, calls = publishing
    run.update(
        event="workflow_dispatch",
        head_sha=_BASE,
        display_title=f"Validate PR #{number} head={_HEAD} base={_BASE}",
    )
    pr["head"]["repo"]["full_name"] = head_repository
    path = write_under_str(tmp_path, "comment.json", json.dumps(payload))

    assert publisher.main(["--payload", str(path)]) == code
    assert bool(calls) is posts


@pytest.mark.parametrize("operation", ["post_comment", "clear_comment"])
def test_comment_failure_is_visible(tmp_path, monkeypatch, publishing, operation):
    _run, _pr, payload, _calls = publishing
    payload["should_post"] = operation == "post_comment"
    monkeypatch.setattr(publisher, operation, lambda *_args: (False, "HTTP 403"))
    path = write_under_str(tmp_path, "comment.json", json.dumps(payload))

    assert publisher.main(["--payload", str(path)]) == 1


def test_unreadable_pr_fails_closed(tmp_path, monkeypatch, publishing):
    run, _pr, payload, calls = publishing

    def get_json(url, _token):
        if "/actions/runs/" in url:
            return run
        raise urllib.error.URLError("unavailable")

    monkeypatch.setattr(publisher, "_get_json", get_json)
    path = write_under_str(tmp_path, "comment.json", json.dumps(payload))

    assert publisher.main(["--payload", str(path)]) == 1
    assert not calls


@pytest.mark.parametrize(
    "body",
    [
        pytest.param("{", id="malformed JSON"),
        pytest.param("[]", id="nonobject payload"),
        pytest.param("x" * 256_001, id="oversize payload"),
    ],
)
def test_invalid_artifact_never_writes(tmp_path, publishing, body):
    _run, _pr, _payload, calls = publishing
    path = write_under_str(tmp_path, "comment.json", body)

    assert publisher.main(["--payload", str(path)]) == 1
    assert not calls


def test_artifact_symlink_is_rejected(tmp_path, monkeypatch, publishing):
    _run, _pr, payload, calls = publishing
    path = write_under_str(tmp_path, "comment.json", json.dumps(payload))
    monkeypatch.setattr(publisher.Path, "is_symlink", lambda _self: True)

    assert publisher.main(["--payload", str(path)]) == 1
    assert not calls


@pytest.mark.parametrize("body,invalid", [(b'{"id": 7}', False), (b"{", True)])
def test_api_reads_are_authenticated_and_bounded(monkeypatch, body, invalid):
    seen = []

    def urlopen(request, timeout):
        seen.append((request.full_url, request.headers, timeout))
        return io.BytesIO(body)

    monkeypatch.setattr(publisher.urllib.request, "urlopen", urlopen)
    url = "https://api.github.com/repos/owner/repo/actions/runs/7"
    if invalid:
        with pytest.raises(ValueError, match="GitHub returned invalid JSON"):
            publisher._get_json(url, "token")
    else:
        assert publisher._get_json(url, "token") == {"id": 7}
    assert seen[0][0] == url
    assert seen[0][1]["Authorization"] == "Bearer token"
    assert seen[0][2] == 30


def test_script_requires_a_workflow_event(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    result = run_tool_script("publish_validation_report.py", "--payload", str(tmp_path))
    assert result.returncode == 1
    assert "Unable to publish validation report" in result.stderr
