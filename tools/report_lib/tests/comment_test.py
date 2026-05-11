"""Tests for `report_lib.comment.find_existing_comment`."""

from report_lib.comment import REPORT_MARKER, find_existing_comment


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
