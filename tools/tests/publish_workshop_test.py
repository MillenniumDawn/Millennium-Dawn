import importlib.util
import os
import subprocess
from pathlib import PurePosixPath

import pytest
from shared.paths import TOOLS_DIR as TOOLS

SPEC = importlib.util.spec_from_file_location(
    "publish_workshop", TOOLS / "publishing" / "publish_workshop.py"
)
assert SPEC is not None and SPEC.loader is not None
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / "tracked.txt").write_text("HEAD\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "initial")
    return repo


def test_copy_repo_uses_tracked_head_only(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("secret\n", encoding="utf-8")
    monkeypatch.setattr(P, "REPO_ROOT", repo)

    copied = P.copy_repo(tmp_path / "publish", set())

    assert (copied / "tracked.txt").read_text(encoding="utf-8") == "HEAD\n"
    assert not (copied / "untracked.txt").exists()


def test_copy_repo_rejects_tracked_symlink(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    try:
        os.symlink("tracked.txt", repo / "tracked-link")
    except OSError:
        pytest.skip("symlinks unavailable")
    _git(repo, "add", "tracked-link")
    _git(repo, "commit", "-m", "symlink")
    monkeypatch.setattr(P, "REPO_ROOT", repo)

    with pytest.raises(RuntimeError, match="tracked symlink"):
        P.copy_repo(tmp_path / "publish", set())


def test_excludes_keep_root_only_scope():
    excludes = {"tools"}
    assert P._archive_path_excluded(PurePosixPath("tools"), excludes)
    assert not P._archive_path_excluded(
        PurePosixPath("common/tools/file.txt"), excludes
    )
