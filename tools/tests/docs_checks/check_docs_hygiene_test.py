"""Docs hygiene: tracked files that should not be, and unused assets."""

from pathlib import Path

import check_docs_hygiene as hygiene
import pytest
from shared.suite import write_text, write_tree

_IMAGE = "docs/public/assets/images/a.png"


@pytest.mark.parametrize(
    ("pathspec", "command"),
    [
        (None, ["git", "-C", "repo", "ls-files"]),
        ("docs/", ["git", "-C", "repo", "ls-files", "--", "docs/"]),
    ],
)
def test_git_ls_files_lists_tracked_paths(monkeypatch, pathspec, command):
    calls = []
    monkeypatch.setattr(
        hygiene.subprocess,
        "check_output",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or "docs/a.md\n\n b.md \n",
    )

    assert hygiene.git_ls_files(Path("repo"), pathspec) == ["docs/a.md", "b.md"]
    assert calls == [(command, {"text": True, "encoding": "utf-8", "timeout": 60})]


@pytest.mark.parametrize(
    ("source", "text", "asset", "unused"),
    [
        pytest.param("docs/src/page.md", "nothing", _IMAGE, True, id="no reference"),
        pytest.param(
            "docs/src/page.md", "assets/images/a.png", _IMAGE, False, id="referenced"
        ),
        pytest.param(
            "docs/src/page.md",
            "assets/images/a.png",
            "docs/src/assets/images/a.png",
            False,
            id="a source image is served from the same path",
        ),
        pytest.param(
            "docs/src/page.md",
            "/assets/downloads/f.zip",
            "docs/public/assets/downloads/f.zip",
            False,
            id="a download by its site path",
        ),
        pytest.param(
            "docs/src/page.md",
            "assets/downloads/f.zip",
            "docs/public/assets/downloads/f.zip",
            True,
            id="a download needs the leading slash",
        ),
        pytest.param(
            "docs/src/page.bin", "assets/images/a.png", _IMAGE, True, id="binary source"
        ),
        pytest.param(
            "docs/public/assets/images/notes.md",
            "assets/images/a.png",
            _IMAGE,
            True,
            id="a file in an asset folder is not a source",
        ),
        pytest.param(
            "other/page.md", "assets/images/a.png", _IMAGE, True, id="outside docs"
        ),
        pytest.param(
            "docs/src/page.md",
            None,
            _IMAGE,
            True,
            id="a tracked source deleted on disk",
        ),
        pytest.param(
            "docs/src/page.md",
            "nothing",
            "docs/src/other/a.png",
            False,
            id="not in an asset folder",
        ),
    ],
)
def test_unused_assets(tmp_path, source, text, asset, unused):
    if text is not None:
        write_text(tmp_path / source, text)

    issues = hygiene.find_unused_assets(tmp_path, Path("docs"), [source, asset])

    assert (f"Unused docs asset tracked: {asset}" in issues) is unused


def test_an_allowed_asset_may_be_unused(tmp_path, monkeypatch):
    monkeypatch.setattr(hygiene, "ALLOW_UNUSED_ASSETS", {"/assets/images/a.png"})

    assert hygiene.find_unused_assets(tmp_path, Path("docs"), [_IMAGE]) == []


def _run(monkeypatch, repo, docs_dir, tracked):
    pathspecs = []
    monkeypatch.setattr(
        hygiene,
        "git_ls_files",
        lambda _root, pathspec: pathspecs.append(pathspec) or tracked,
    )
    return hygiene.run(repo, docs_dir), pathspecs


def test_run_reports_tracked_files_that_should_not_be(tmp_path, monkeypatch):
    kept = "docs/public/assets/images/photo-temp.png"
    deleted = "docs/public/assets/images/gone-temp.png"
    write_tree(
        tmp_path,
        {"docs/.bundle/config": "", kept: "", "docs/src/page-temp.md": ""},
    )
    tracked = [
        "outside-temp.png",
        "docs/.bundle/config",
        kept,
        deleted,
        "docs/src/page-temp.md",
    ]

    # An absolute docs dir is made relative, as git lists paths.
    result, pathspecs = _run(monkeypatch, tmp_path, tmp_path / "docs", tracked)

    assert pathspecs == ["docs/"]
    assert result == (
        False,
        "Docs hygiene checks failed:\n"
        "- Bundler local config must not be tracked: docs/.bundle/config\n"
        f"- Temp-named docs asset is tracked: {kept}\n"
        f"- Unused docs asset tracked: {kept}\n"
        # A file deleted in the working tree is only checked for use.
        f"- Unused docs asset tracked: {deleted}",
    )


def test_run_passes_a_clean_tree(tmp_path, monkeypatch):
    write_tree(tmp_path, {"docs/src/page.md": "/assets/images/a.png", _IMAGE: ""})

    result, _ = _run(monkeypatch, tmp_path, Path("docs"), ["docs/src/page.md", _IMAGE])

    assert result == (True, "Docs hygiene checks passed")


def test_run_rejects_a_docs_dir_outside_the_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()

    (passed, report), pathspecs = _run(monkeypatch, repo, tmp_path / "docs", [])

    assert not passed and "is not inside repo-root" in report
    assert pathspecs == []
