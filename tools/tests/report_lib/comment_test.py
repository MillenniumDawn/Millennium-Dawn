"""Tests for `report_lib.comment` discovery and posting."""

import pytest
from report_lib import comment as C
from report_lib.comment import (
    REPORT_MARKER,
    clear_comment,
    find_existing_comment,
    post_comment,
)


def _comment(body, bot=True, cid=1):
    return {
        "id": cid,
        "body": body,
        "user": {"type": "Bot" if bot else "User"},
    }


def test_matches_marker_first():
    comments = [
        _comment("Other bot comment", cid=1),
        _comment(f"{REPORT_MARKER}\n# Validation Report\nstuff", cid=2),
        _comment("# Validation Report (legacy)", cid=3),
    ]
    result = find_existing_comment(comments)
    assert result is not None
    assert result["id"] == 2


def test_falls_back_to_legacy_title():
    comments = [
        _comment("hello", cid=1),
        _comment("# Validation Report\nlegacy format with no marker", cid=2),
    ]
    result = find_existing_comment(comments)
    assert result is not None
    assert result["id"] == 2


def test_skips_human_comments_even_with_marker():
    comments = [
        _comment(f"{REPORT_MARKER}\nquote from bot", bot=False, cid=1),
    ]
    assert find_existing_comment(comments) is None


def test_returns_none_when_no_match():
    comments = [
        _comment("something unrelated", cid=1),
        _comment("another bot saying something", cid=2),
        _comment("Summary of the Validation Report", cid=3),
        _comment("# Validation Report for another tool", cid=4),
    ]
    assert find_existing_comment(comments) is None


def test_all_comment_requests_have_timeout(monkeypatch):
    calls = []

    class Response:
        def __init__(self, body):
            self.body = body

        def read(self):
            return self.body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    def fake_urlopen(req, timeout):
        method = req.get_method()
        calls.append((method, timeout))
        body = b"[]" if method == "GET" else b"{}"
        return Response(body)

    monkeypatch.setattr(C.urllib.request, "urlopen", fake_urlopen)
    C._get("https://example.invalid", {})
    C._post("https://example.invalid", {}, {})
    C._patch("https://example.invalid", {}, {})
    C._delete("https://example.invalid", {})
    assert calls == [
        ("GET", C._REQUEST_TIMEOUT),
        ("POST", C._REQUEST_TIMEOUT),
        ("PATCH", C._REQUEST_TIMEOUT),
        ("DELETE", C._REQUEST_TIMEOUT),
    ]


def test_creates_a_comment_when_the_pr_has_none(monkeypatch):
    monkeypatch.setattr(C, "_get", lambda *a, **k: [])
    posted = []
    monkeypatch.setattr(
        C,
        "_post",
        lambda url, payload, headers: posted.append((url, payload)) or {"id": 7},
    )
    success, message = post_comment("owner", "repo", "7", "finding body", "token")
    assert success
    assert "created comment #7" in message
    assert posted == [
        (
            "https://api.github.com/repos/owner/repo/issues/7/comments",
            {"body": "finding body"},
        )
    ]


def test_refreshes_an_existing_comment(monkeypatch):
    comments = [_comment(f"{REPORT_MARKER}\n# Validation Report\nold", cid=42)]
    monkeypatch.setattr(C, "_get", lambda *a, **k: comments)
    patched = []
    monkeypatch.setattr(
        C, "_patch", lambda url, payload, headers: patched.append((url, payload)) or {}
    )
    success, message = post_comment("owner", "repo", "7", "fresh body", "token")
    assert success
    assert "updated comment #42" in message
    assert patched == [
        (
            "https://api.github.com/repos/owner/repo/issues/comments/42",
            {"body": "fresh body"},
        )
    ]


def test_clears_an_existing_report_comment(monkeypatch):
    comments = [_comment(f"{REPORT_MARKER}\n# Validation Report\nold", cid=42)]
    monkeypatch.setattr(C, "_get", lambda *a, **k: comments)
    deleted = []
    monkeypatch.setattr(C, "_delete", lambda url, headers: deleted.append(url))

    success, message = clear_comment("owner", "repo", "7", "token")

    assert success
    assert message == "deleted comment #42"
    assert deleted == ["https://api.github.com/repos/owner/repo/issues/comments/42"]


def test_clear_reports_delete_failure(monkeypatch):
    comments = [_comment(f"{REPORT_MARKER}\n# Validation Report\nold", cid=42)]
    monkeypatch.setattr(C, "_get", lambda *a, **k: comments)

    def fail_delete(*_args):
        raise RuntimeError("boom")

    monkeypatch.setattr(C, "_delete", fail_delete)

    success, message = clear_comment("owner", "repo", "7", "token")

    assert not success
    assert message == "delete comment: boom"


@pytest.mark.parametrize(
    "comments",
    [
        pytest.param([], id="no-report"),
        pytest.param(
            [_comment(f"{REPORT_MARKER}\nquoted report", bot=False, cid=42)],
            id="human-report",
        ),
    ],
)
def test_clear_leaves_unowned_comments_untouched(monkeypatch, comments):
    monkeypatch.setattr(C, "_get", lambda *a, **k: comments)
    monkeypatch.setattr(
        C,
        "_delete",
        lambda *args: (_ for _ in ()).throw(AssertionError("must not delete")),
    )

    success, message = clear_comment("owner", "repo", "7", "token")

    assert success
    assert message == "no report comment to remove"
