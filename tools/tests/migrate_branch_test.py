"""Behavior tests for tools/migrate_branch.sh."""

import os
import subprocess
import sys

import pytest
from shared.paths import REPO_ROOT

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="the tests run tools/migrate_branch.sh in bash"
)

SCRIPT = REPO_ROOT / "tools" / "migrate_branch.sh"
ARCHIVE_URL = "https://github.com/MillenniumDawn/millennium-dawn-archive"
AUTHOR_DATE = "2026-11-20T10:00:00+00:00"
CUT_DATE = "2026-11-21T10:00:00+00:00"


def environment(**overrides):
    # A developer's global git config must not decide how these repos behave.
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_AUTHOR_NAME": "Author",
            "GIT_AUTHOR_EMAIL": "author@example.com",
            "GIT_AUTHOR_DATE": AUTHOR_DATE,
            "GIT_COMMITTER_NAME": "Committer",
            "GIT_COMMITTER_EMAIL": "committer@example.com",
            "GIT_COMMITTER_DATE": AUTHOR_DATE,
        }
    )
    env.update(overrides)
    return env


def run(repo, *args, author_date=AUTHOR_DATE, committer_date=AUTHOR_DATE):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=environment(GIT_AUTHOR_DATE=author_date, GIT_COMMITTER_DATE=committer_date),
        capture_output=True,
        text=True,
        timeout=60,
    )


def git(repo, *args, author_date=AUTHOR_DATE, committer_date=AUTHOR_DATE):
    result = run(repo, *args, author_date=author_date, committer_date=committer_date)
    assert result.returncode == 0, result.stderr
    return result


def commit(repo, name, text, message):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(repo, "add", "--", name)
    git(repo, "commit", "-m", message)
    return revision(repo, "HEAD")


def revision(repo, ref):
    return git(repo, "rev-parse", ref).stdout.strip()


def build_archive(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    git(archive, "init", "-b", "main")
    commit(archive, "file.txt", "one\n", "first")
    git(archive, "switch", "-c", "feature")
    commit(archive, "file.txt", "branch\n", "branch edit")
    git(archive, "switch", "main")
    commit(archive, "file.txt", "two\n", "second")
    git(archive, "switch", "feature")
    # The branch changed the same line main did, so its merge resolved a conflict.
    conflicting = run(archive, "merge", "main", "--no-commit")
    assert conflicting.returncode == 1
    (archive / "file.txt").write_text("two and branch\n", encoding="utf-8")
    git(archive, "add", "file.txt")
    git(archive, "commit", "-m", "merge main")
    merge = revision(archive, "HEAD")
    commit(archive, "feature.txt", "feature\n", "feature work")
    git(archive, "switch", "main")
    mirror_archive(archive)
    return archive, merge


def mirror_archive(archive):
    """Give the archive the origin/* refs a clone would have."""
    listing = git(archive, "for-each-ref", "refs/heads", "--format=%(refname)")
    for ref in listing.stdout.split():
        name = ref.removeprefix("refs/heads/")
        git(archive, "update-ref", f"refs/remotes/origin/{name}", ref)


def reroot(archive, target, keep):
    """Copy the named main commits into target with new commit ids.

    The cut kept each tree, author date and subject and rewrote the ancestry;
    this reproduces that by changing only the committer.
    """
    target.mkdir()
    git(target, "init", "-b", "main")
    # The archive's trees are needed to rebuild its commits.
    git(target, "fetch", "--quiet", "--no-tags", str(archive), "main")
    parent = None
    for sha in git(archive, "rev-list", "--reverse", "main").stdout.split():
        subject = git(archive, "log", "-1", "--format=%s", sha).stdout.strip()
        if subject not in keep:
            continue
        author_date = git(archive, "log", "-1", "--format=%aI", sha).stdout.strip()
        tree = revision(archive, f"{sha}^{{tree}}")
        args = ["commit-tree", tree, "-m", subject]
        if parent:
            args += ["-p", parent]
        parent = git(
            target,
            *args,
            author_date=author_date,
            committer_date=CUT_DATE,
        ).stdout.strip()
    git(target, "update-ref", "refs/heads/main", parent)
    git(target, "update-ref", "refs/remotes/origin/main", parent)
    return target


def migrate(repo, branch, archive, **overrides):
    env = environment(ARCHIVE=str(archive), SKIP_FETCH="1", **overrides)
    return subprocess.run(
        ["bash", str(SCRIPT), branch],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


def sha_of_subject(repo, subject):
    listing = git(repo, "log", "--format=%H%x09%s", "main").stdout
    for line in listing.splitlines():
        sha, _, text = line.partition("\t")
        if text == subject:
            return sha
    raise AssertionError(f"no commit with subject {subject!r}")


def assert_absent(repo, ref):
    assert run(repo, "rev-parse", "--verify", "-q", ref).returncode != 0


def assert_no_branch(repo, branch):
    assert_absent(repo, f"refs/heads/{branch}")
    assert_absent(repo, "refs/migrate/result")


def test_replays_a_merge_and_keeps_its_resolution(tmp_path):
    archive, archive_merge = build_archive(tmp_path)
    target = reroot(archive, tmp_path / "target", ["first", "second"])
    before = git(target, "symbolic-ref", "--short", "HEAD").stdout.strip()

    result = migrate(target, "feature", archive)

    assert result.returncode == 0, result.stderr
    assert git(target, "symbolic-ref", "--short", "HEAD").stdout.strip() == before
    own = git(target, "rev-list", "feature", "--not", "origin/main").stdout.split()
    assert len(own) == 3
    merges = git(target, "rev-list", "--merges", "feature", "--not", "origin/main")
    assert len(merges.stdout.split()) == 1
    parents = git(target, "log", "-1", "--format=%P", merges.stdout.strip())
    assert parents.stdout.split()[1] == sha_of_subject(target, "second")
    assert (
        git(target, "log", "-1", "--format=%s", merges.stdout.strip()).stdout.strip()
        == "merge main"
    )
    assert revision(target, "feature^{tree}") == revision(archive, "feature^{tree}")
    assert_absent(target, "refs/migrate/result")
    assert archive_merge not in git(target, "rev-list", "--all").stdout.split()


def test_maps_two_commits_with_one_tree_by_date_and_subject(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    git(archive, "init", "-b", "main")
    base = commit(archive, "file.txt", "same\n", "base")
    commit(archive, "file.txt", "different\n", "typo")
    revert = commit(archive, "file.txt", "same\n", "Revert typo")
    assert revision(archive, f"{base}^{{tree}}") == revision(
        archive, f"{revert}^{{tree}}"
    )
    git(archive, "switch", "-c", "feature", base)
    commit(archive, "feature.txt", "feature\n", "feature work")
    git(archive, "switch", "main")
    mirror_archive(archive)

    target = reroot(archive, tmp_path / "target", ["base", "typo", "Revert typo"])
    result = migrate(target, "feature", archive)

    assert result.returncode == 0, result.stderr
    assert revision(target, "feature^") == sha_of_subject(target, "base")


def test_stops_and_names_the_commit_when_no_parent_matches(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    git(archive, "init", "-b", "main")
    commit(archive, "file.txt", "one\n", "dropped")
    commit(archive, "file.txt", "two\n", "kept")
    git(archive, "switch", "-c", "feature", revision(archive, "HEAD~1"))
    commit(archive, "feature.txt", "feature\n", "feature work")
    git(archive, "switch", "main")
    mirror_archive(archive)

    target = reroot(archive, tmp_path / "target", ["kept"])
    result = migrate(target, "feature", archive)

    assert result.returncode == 1
    assert "no commit on the new main matches" in result.stderr
    assert "dropped" in result.stderr
    assert "MAP" in result.stderr
    assert_no_branch(target, "feature")


def test_stops_when_a_parent_matches_more_than_one_commit(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    git(archive, "init", "-b", "main")
    commit(archive, "file.txt", "one\n", "first")
    git(archive, "commit", "--allow-empty", "-m", "second")
    git(archive, "switch", "-c", "feature")
    commit(archive, "feature.txt", "feature\n", "feature work")
    git(archive, "switch", "main")
    mirror_archive(archive)

    target = reroot(archive, tmp_path / "target", ["first"])
    tree = revision(target, "main^{tree}")
    head = revision(target, "main")
    for _ in range(2):
        head = git(
            target, "commit-tree", tree, "-m", "second", "-p", head
        ).stdout.strip()
    git(target, "update-ref", "refs/heads/main", head)
    git(target, "update-ref", "refs/remotes/origin/main", head)

    result = migrate(target, "feature", archive)

    assert result.returncode == 1
    assert "matches 2 commits on the new main" in result.stderr
    assert "second" in result.stderr
    assert_no_branch(target, "feature")


def test_stops_when_the_cut_changed_a_mapped_parents_files(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    git(archive, "init", "-b", "main")
    (archive / "kept.txt").write_text("kept\n", encoding="utf-8")
    (archive / "removed.txt").write_text("removed\n", encoding="utf-8")
    git(archive, "add", ".")
    git(archive, "commit", "-m", "one")
    old = revision(archive, "HEAD")
    git(archive, "switch", "-c", "feature", old)
    commit(archive, "feature.txt", "feature\n", "feature work")
    git(archive, "switch", "main")
    mirror_archive(archive)

    target = tmp_path / "target"
    target.mkdir()
    git(target, "init", "-b", "main")
    # The cut removed removed.txt: same date and subject, different tree.
    new = commit(target, "kept.txt", "kept\n", "one")
    git(target, "update-ref", "refs/remotes/origin/main", "HEAD")
    commit_map = tmp_path / "commit-map"
    commit_map.write_text(f"{old} {new}\n", encoding="utf-8")

    result = migrate(target, "feature", archive, MAP=str(commit_map))

    assert result.returncode == 1
    assert "the cut changed the files at" in result.stderr
    assert "hand migration" in result.stderr
    assert_no_branch(target, "feature")


def test_help_states_that_signatures_are_lost():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        env=environment(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    assert "signatures" in result.stdout
    assert ARCHIVE_URL in result.stdout
