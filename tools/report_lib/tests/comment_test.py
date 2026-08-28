"""Tests for `report_lib.comment` discovery and posting."""

from report_lib import comment as C
from report_lib.comment import (
    REPORT_MARKER,
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
    assert calls == [
        ("GET", C._REQUEST_TIMEOUT),
        ("POST", C._REQUEST_TIMEOUT),
        ("PATCH", C._REQUEST_TIMEOUT),
    ]


def test_creates_a_comment_when_the_pr_has_none(monkeypatch):
    # A clean run still opens a comment: silence is indistinguishable from a
    # pipeline that never reached the PR.
    monkeypatch.setattr(C, "_get", lambda *a, **k: [])
    posted = []
    monkeypatch.setattr(
        C,
        "_post",
        lambda url, payload, headers: posted.append((url, payload)) or {"id": 7},
    )
    success, message = post_comment("owner", "repo", "7", "clean body", "token")
    assert success
    assert "created comment #7" in message
    assert posted == [
        (
            "https://api.github.com/repos/owner/repo/issues/7/comments",
            {"body": "clean body"},
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
