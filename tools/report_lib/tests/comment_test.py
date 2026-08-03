"""Tests for `report_lib.comment.find_existing_comment` and delete_comment."""

from report_lib import comment as C
from report_lib.comment import REPORT_MARKER, delete_comment, find_existing_comment


class _Resp:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


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


def test_delete_comment_noop_without_existing(monkeypatch):
    monkeypatch.setattr(C, "_get", lambda *a, **k: [])
    success, message = delete_comment("owner", "repo", "7", "token")
    assert success
    assert "no report comment" in message


def test_delete_comment_removes_marker_comment(monkeypatch):
    comments = [_comment(f"{REPORT_MARKER}\n# Validation Report\nstuff", cid=42)]
    monkeypatch.setattr(C, "_get", lambda *a, **k: comments)
    deleted = []

    def fake_urlopen(req):
        deleted.append(req.full_url)
        assert req.method == "DELETE"
        return _Resp()

    monkeypatch.setattr(C.urllib.request, "urlopen", fake_urlopen)
    success, message = delete_comment("owner", "repo", "7", "token")
    assert success
    assert "deleted comment #42" in message
    assert deleted == ["https://api.github.com/repos/owner/repo/issues/comments/42"]


def test_delete_comment_falls_back_to_legacy_title(monkeypatch):
    comments = [_comment("# Validation Report\nlegacy, no marker", cid=9)]
    monkeypatch.setattr(C, "_get", lambda *a, **k: comments)
    deleted = []

    def fake_urlopen(req):
        deleted.append(req.full_url)
        return _Resp()

    monkeypatch.setattr(C.urllib.request, "urlopen", fake_urlopen)
    success, message = delete_comment("owner", "repo", "7", "token")
    assert success
    assert "deleted comment #9" in message
