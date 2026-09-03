import os
import sys
from pathlib import Path
from types import SimpleNamespace

import archive_stale_branches as A
import pytest
from shared.suite import read_text as read
from shared.suite import symlinks_available
from shared.suite import write_text as write

SYMLINK = object()

requires_symlinks = pytest.mark.skipif(
    not symlinks_available(),
    reason="creating a symlink needs Developer Mode or admin on Windows",
)


def stub_repo(monkeypatch, tmp_path, trees, diffs, missing=()):
    """Stand in for git: canned trees per ref, canned diff lists per branch."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    repo = repo.resolve()

    def fake_archive_ref(ref, dest, _repo):
        for rel, content in trees.get(ref, {}).items():
            path = Path(dest) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if content is SYMLINK:
                path.symlink_to(Path(dest))
            else:
                write(path, content)

    monkeypatch.setattr(A, "find_repo_root", lambda: repo)
    monkeypatch.setattr(A, "branch_exists", lambda ref, _repo: ref not in missing)
    monkeypatch.setattr(A, "diff_paths", lambda branch, _repo: list(diffs[branch]))
    monkeypatch.setattr(A, "archive_ref", fake_archive_ref)
    return repo


def invoke(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["archive_stale_branches.py", *argv])
    return A.main()


def test_diff_paths_accepts_nul_delimited_unicode(monkeypatch, tmp_path):
    monkeypatch.setattr(
        A,
        "run",
        lambda *_args, **_kwargs: "café.txt\0renamed file.txt\0".encode(),
    )
    assert A.diff_paths("branch", tmp_path) == ["café.txt", "renamed file.txt"]


def test_diff_paths_rejects_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr(A, "run", lambda *_args, **_kwargs: b"../escape.txt\0")
    with pytest.raises(ValueError, match="Unsafe path"):
        A.diff_paths("branch", tmp_path)


def test_diff_paths_uses_a_three_dot_range_against_main(monkeypatch, tmp_path):
    recorded = {}

    def fake_run(cmd, repo, **_kwargs):
        recorded["cmd"] = cmd
        recorded["repo"] = repo
        return b""

    monkeypatch.setattr(A, "run", fake_run)

    assert A.diff_paths("origin/topic", tmp_path) == []
    assert recorded["cmd"] == [
        "git",
        "diff",
        "--name-only",
        "-z",
        "main...origin/topic",
    ]
    assert recorded["repo"] == tmp_path


def test_remove_stale_files_keeps_only_current_divergences(tmp_path):
    target = tmp_path / "archive"
    (target / "nested").mkdir(parents=True)
    keep = target / "nested" / "keep.txt"
    stale = target / "stale.txt"
    keep.write_text("keep", encoding="utf-8")
    stale.write_text("stale", encoding="utf-8")

    removed = A.remove_stale_files(target, {"nested/keep.txt"})

    assert removed == 1
    assert keep.exists()
    assert not stale.exists()


def test_remove_stale_files_prunes_directories_left_empty(tmp_path):
    target = tmp_path / "archive"
    write(target / "gone" / "deep" / "file.txt", "x")

    assert A.remove_stale_files(target, set()) == 1
    assert not (target / "gone").exists()


def test_diff_paths_decodes_filesystem_bytes(monkeypatch, tmp_path):
    raw = os.fsencode("naïve.txt") + b"\0"
    monkeypatch.setattr(A, "run", lambda *_args, **_kwargs: raw)
    assert A.diff_paths("branch", tmp_path) == ["naïve.txt"]


def test_find_repo_root_returns_the_git_toplevel(monkeypatch):
    monkeypatch.setattr(
        A.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout="/srv/repo\n")
    )
    assert A.find_repo_root() == Path("/srv/repo")


def test_run_executes_in_the_repo_and_raises_on_failure(monkeypatch, tmp_path):
    recorded = {}

    def fake_run(cmd, **kwargs):
        recorded.update(kwargs)
        recorded["cmd"] = cmd
        return SimpleNamespace(stdout=b"out")

    monkeypatch.setattr(A.subprocess, "run", fake_run)

    assert A.run(["git", "status"], tmp_path) == b"out"
    assert recorded["cwd"] == tmp_path
    assert recorded["check"] is True
    assert recorded["capture_output"] is True


def test_sha256_bytes_separates_differing_content():
    assert A.sha256_bytes(b"abc") == A.sha256_bytes(b"abc")
    assert A.sha256_bytes(b"abc") != A.sha256_bytes(b"abd")


def test_branch_exists_reflects_the_rev_parse_exit_code(monkeypatch, tmp_path):
    codes = iter([0, 1])
    monkeypatch.setattr(
        A.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=next(codes))
    )

    assert A.branch_exists("origin/here", tmp_path) is True
    assert A.branch_exists("origin/gone", tmp_path) is False


class FakePipeline:
    """Two-process git-archive|tar stand-in with scripted return codes."""

    def __init__(self, archive_rc=0, tar_rc=0, tar_err=b""):
        self.archive_rc = archive_rc
        self.tar_rc = tar_rc
        self.tar_err = tar_err
        self.commands = []

    def __call__(self, cmd, **kwargs):
        self.commands.append(cmd)
        if cmd[0] == "git":
            return SimpleNamespace(
                stdout=SimpleNamespace(close=lambda: None),
                wait=lambda: self.archive_rc,
            )
        return SimpleNamespace(
            communicate=lambda: (None, self.tar_err),
            returncode=self.tar_rc,
        )


def test_archive_ref_pipes_git_archive_into_tar(monkeypatch, tmp_path):
    pipeline = FakePipeline()
    monkeypatch.setattr(A.subprocess, "Popen", pipeline)

    A.archive_ref("main", tmp_path, tmp_path)

    assert pipeline.commands == [
        ["git", "archive", "main"],
        ["tar", "-x", "-C", str(tmp_path)],
    ]


@pytest.mark.parametrize(
    ("archive_rc", "tar_rc"),
    [(128, 0), (0, 2)],
)
def test_archive_ref_raises_when_either_side_fails(
    archive_rc, tar_rc, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        A.subprocess,
        "Popen",
        FakePipeline(archive_rc=archive_rc, tar_rc=tar_rc, tar_err=b"boom"),
    )

    with pytest.raises(RuntimeError, match="git archive main failed"):
        A.archive_ref("main", tmp_path, tmp_path)


def test_reject_symlinks_ignores_an_absent_directory(tmp_path):
    A._reject_symlinks(tmp_path / "not-created-yet")


@requires_symlinks
def test_reject_symlinks_refuses_a_symlinked_root(tmp_path):
    (tmp_path / "real").mkdir()
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real")

    with pytest.raises(ValueError, match="Refusing symlink"):
        A._reject_symlinks(link)


@requires_symlinks
def test_reject_symlinks_refuses_a_nested_symlink(tmp_path):
    write(tmp_path / "nested" / "real.txt", "x")
    (tmp_path / "nested" / "link.txt").symlink_to(tmp_path / "nested" / "real.txt")

    with pytest.raises(ValueError, match="link.txt"):
        A._reject_symlinks(tmp_path)


def test_mkdir_owned_creates_the_whole_chain(tmp_path):
    A._mkdir_owned(tmp_path / "a" / "b" / "c", tmp_path)

    assert (tmp_path / "a" / "b" / "c").is_dir()


@requires_symlinks
def test_mkdir_owned_refuses_to_descend_through_a_symlink(tmp_path):
    (tmp_path / "real").mkdir()
    (tmp_path / "a").symlink_to(tmp_path / "real")

    with pytest.raises(ValueError, match="Refusing symlink"):
        A._mkdir_owned(tmp_path / "a" / "b", tmp_path)

    assert not (tmp_path / "real" / "b").exists()


def test_main_archives_only_files_that_differ_from_main(monkeypatch, tmp_path, capsys):
    repo = stub_repo(
        monkeypatch,
        tmp_path,
        trees={
            "main": {"shared.txt": "same", "changed.txt": "old"},
            "origin/topic": {
                "shared.txt": "same",
                "changed.txt": "new",
                "added.txt": "added",
            },
        },
        diffs={"origin/topic": ["shared.txt", "changed.txt", "added.txt"]},
    )
    out = repo / "archive"

    assert invoke(monkeypatch, "--branches", "origin/topic", "--output", str(out)) == 0

    target = out / "topic"
    assert read(target / "changed.txt") == "new"
    assert read(target / "added.txt") == "added"
    assert not (target / "shared.txt").exists()
    stdout = capsys.readouterr().out
    assert "copied=2 | identical=1" in stdout
    assert "=== Archive summary ===" in stdout


@requires_symlinks
def test_main_reports_excluded_missing_and_symlinked_paths(
    monkeypatch, tmp_path, capsys
):
    repo = stub_repo(
        monkeypatch,
        tmp_path,
        trees={
            "main": {},
            "origin/topic": {"real.txt": "kept", "link.txt": SYMLINK},
        },
        diffs={"origin/topic": [".gitignore", "gone.txt", "link.txt", "real.txt"]},
    )
    out = repo / "archive"

    assert invoke(monkeypatch, "--branches", "origin/topic", "--output", str(out)) == 0

    assert "copied=1 | identical=0 | missing=1 | excluded=2" in capsys.readouterr().out
    assert not (out / "topic" / "link.txt").exists()


def test_main_prunes_files_that_no_longer_diverge(monkeypatch, tmp_path, capsys):
    repo = stub_repo(
        monkeypatch,
        tmp_path,
        trees={"main": {}, "origin/topic": {"kept.txt": "new"}},
        diffs={"origin/topic": ["kept.txt"]},
    )
    out = repo / "archive"
    write(out / "topic" / "obsolete.txt", "from a previous run")

    assert invoke(monkeypatch, "--branches", "origin/topic", "--output", str(out)) == 0

    assert not (out / "topic" / "obsolete.txt").exists()
    assert "stale=1" in capsys.readouterr().out


def test_main_flags_missing_refs_and_exits_nonzero(monkeypatch, tmp_path, capsys):
    repo = stub_repo(
        monkeypatch,
        tmp_path,
        trees={"main": {}, "origin/here": {"a.txt": "new"}},
        diffs={"origin/here": ["a.txt"]},
        missing=("origin/gone",),
    )
    out = repo / "archive"

    code = invoke(
        monkeypatch,
        "--branches",
        "origin/gone",
        "origin/here",
        "--output",
        str(out),
    )

    assert code == 1
    stdout = capsys.readouterr().out
    assert "origin/gone: SKIP (ref not found)" in stdout
    assert "Skipped 1 branch(es) with missing refs" in stdout
    assert (out / "here" / "a.txt").exists()


def test_main_resolves_a_relative_output_against_the_repo(monkeypatch, tmp_path):
    repo = stub_repo(
        monkeypatch,
        tmp_path,
        trees={"main": {}, "origin/topic": {"a.txt": "new"}},
        diffs={"origin/topic": ["a.txt"]},
    )

    assert (
        invoke(monkeypatch, "--branches", "origin/topic", "--output", "out/branches")
        == 0
    )

    assert read(repo / "out" / "branches" / "topic" / "a.txt") == "new"


def test_main_rejects_a_branch_name_that_escapes_the_archive(monkeypatch, tmp_path):
    repo = stub_repo(
        monkeypatch,
        tmp_path,
        trees={"main": {}, "origin/../evil": {}},
        diffs={"origin/../evil": []},
    )

    with pytest.raises(ValueError, match="Unsafe branch archive name"):
        invoke(
            monkeypatch,
            "--branches",
            "origin/../evil",
            "--output",
            str(repo / "archive"),
        )


@requires_symlinks
def test_main_refuses_a_symlinked_archive_root(monkeypatch, tmp_path):
    repo = stub_repo(
        monkeypatch,
        tmp_path,
        trees={"main": {}, "origin/topic": {}},
        diffs={"origin/topic": []},
    )
    (repo / "real").mkdir()
    link = repo / "archive"
    link.symlink_to(repo / "real")

    with pytest.raises(ValueError, match="Refusing symlink"):
        invoke(monkeypatch, "--branches", "origin/topic", "--output", str(link))


def test_default_branch_list_targets_the_resources_checkout():
    assert A.DEFAULT_OUTPUT == Path("../millennium-dawn-resources/archive/branches")
    assert all(branch.startswith("origin/") for branch in A.BRANCHES)
    assert ".gitignore" in A.SKIP_FILES
