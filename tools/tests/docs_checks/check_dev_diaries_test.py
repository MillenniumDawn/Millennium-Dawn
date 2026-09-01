"""Unit tests for dev-diary docs checks."""

import check_dev_diaries as dev_diaries
import pytest


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "/dev-diaries/53-the-military-of-japan/",
            "/dev-diaries/53-the-military-of-japan",
        ),
        (
            "/dev-diaries/53-the-military-of-japan",
            "/dev-diaries/53-the-military-of-japan",
        ),
        (
            "https://www.reddit.com/r/MillenniumDawn/comments/abc/",
            "https://www.reddit.com/r/millenniumdawn/comments/abc",
        ),
    ],
)
def test_normalize_compare_url(url, expected):
    assert dev_diaries.normalize_compare_url(url) == expected


@pytest.mark.parametrize(
    "tag, is_version_like",
    [
        ("v2.0", True),
        ("v2", True),
        ("dev diary", False),
    ],
)
def test_is_version_like_tag(tag, is_version_like):
    assert dev_diaries.is_version_like_tag(tag) is is_version_like


def test_self_test_passes():
    assert dev_diaries.self_test() == 0
