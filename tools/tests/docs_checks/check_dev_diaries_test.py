"""Dev diary checks: frontmatter, version tags and duplicate links."""

import check_dev_diaries as dev_diaries
import pytest
from shared.suite import write_tree

_GOOD = "---\nversion: v1.0\npermalink: /same/\n---\n"
_TAGGED = "---\nversion: v1.0\ntags:\n  - v1.0\n  - diary\n---\n"
_TAG_WARNING = (
    "WARNING: content/devDiaries/tagged.mdx: tag 'v1.0' looks like a version; "
    "use version frontmatter instead"
)
_EXTERNAL = "content/devDiaryExternal/index.yml"


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
        ("HTTPS://EXAMPLE.COM/Path/?x=1", "https://example.com/path"),
    ],
)
def test_normalize_compare_url(url, expected):
    assert dev_diaries.normalize_compare_url(url) == expected


@pytest.mark.parametrize(
    "tag, is_version_like",
    [
        ("v2.0", True),
        ("v2", True),
        ("V2", True),
        ("dev diary", False),
    ],
)
def test_is_version_like_tag(tag, is_version_like):
    assert dev_diaries.is_version_like_tag(tag) is is_version_like


@pytest.mark.parametrize(
    ("text", "data"),
    [
        pytest.param("plain", None, id="no frontmatter"),
        pytest.param("---\ntitle: x\n---\n", {"tags": []}, id="none of the fields"),
        pytest.param(
            "---\nversion: v2.0\npermalink: '/a/'\ntags:\n  - 'v2.0'\n  - diary\n---\n",
            {"version": "v2.0", "permalink": "/a/", "tags": ["v2.0", "diary"]},
            id="quotes are dropped",
        ),
    ],
)
def test_parse_frontmatter(text, data):
    assert dev_diaries.parse_frontmatter(text) == data


def test_self_test_passes():
    assert dev_diaries.self_test() == 0


@pytest.mark.parametrize(
    ("files", "report"),
    [
        pytest.param({}, (True, "Dev diary checks passed"), id="no diaries"),
        pytest.param(
            {
                "content/devDiaries/good.mdx": _GOOD,
                # An entry with no url is skipped.
                _EXTERNAL: "- title: Group\n      url: /other/\n      url:\n",
            },
            (True, "Dev diary checks passed"),
            id="clean",
        ),
        pytest.param(
            {"content/devDiaries/tagged.mdx": _TAGGED},
            (True, f"Dev diary checks passed (1 warning(s))\n{_TAG_WARNING}"),
            id="a version as a tag is a warning",
        ),
        pytest.param(
            {"content/devDiaries/none.mdx": "no yaml"},
            (
                False,
                "Dev diary checks failed:\n"
                "ERROR: content/devDiaries/none.mdx: missing or invalid YAML "
                "frontmatter",
            ),
            id="no frontmatter",
        ),
        pytest.param(
            {
                "content/devDiaries/bad.mdx": "---\nversion: wrong\n---\n",
                "content/devDiaries/tagged.mdx": _TAGGED,
            },
            (
                False,
                f"Dev diary checks failed:\n{_TAG_WARNING}\n"
                "ERROR: content/devDiaries/bad.mdx: missing or invalid version "
                "(expected vMAJOR.MINOR, got None)",
            ),
            id="a bad version, after the warnings",
        ),
        pytest.param(
            {
                "content/devDiaries/good.mdx": _GOOD,
                _EXTERNAL: "- title: 'Group'\n      url: /same\n",
            },
            (
                False,
                "Dev diary checks failed:\n"
                "ERROR: devDiaryExternal (Group): url '/same' duplicates in-repo "
                "permalink",
            ),
            id="an external link to a diary in the repo",
        ),
    ],
)
def test_run(tmp_path, monkeypatch, files, report):
    content = tmp_path / "content"
    monkeypatch.setattr(dev_diaries, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(dev_diaries, "DEV_DIARIES_DIR", content / "devDiaries")
    monkeypatch.setattr(dev_diaries, "EXTERNAL_YML", tmp_path / _EXTERNAL)
    write_tree(tmp_path, files)

    assert dev_diaries.run() == report
