#!/usr/bin/env python3
"""Archive diverging files from stale branches into resources/archived-branches/.

Uses 3-dot diff (main...branch) so we only see changes made on the branch
relative to its merge base with main, not the full diverged history.

For each branch:
1. `git diff --name-only main...branch` -> the diverging file list
2. `git archive | tar` -> extract branch tree to temp dir
3. For each diff path: copy if branch's blob != main's blob

The temp dir lives inside the repo (.tmp-archive/) because /tmp is usually
tmpfs with a tight size cap and the yemen branch alone is a 5 GB extract.

The BRANCHES list at the top of the file is the single source of truth. Edit
it and re-run to refresh the archive. By default it points at the branches
we archived in the initial chore commit.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

BRANCHES = [
    "origin/yemen-development",
    "origin/Taiwan-dev",
    "origin/ASEAN_shared_tree",
    "origin/religion-breakdown-chart",
    "origin/panama-focuses",
    "origin/danubia",
    "origin/iraqi-gui",
    "origin/military-strength",
    "origin/3D-tank-models-to-check",
    "origin/md-railway-guns",
    "origin/didi",
    "origin/Irish-Development",
]

# Files we never want to archive regardless of diff (unrelated noise)
SKIP_FILES = {".gitignore"}


def find_repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(out)


def run(cmd, repo: Path, **kw):
    return subprocess.run(cmd, cwd=repo, capture_output=True, check=True, **kw).stdout


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def diff_paths(branch: str, repo: Path) -> list[str]:
    output = run(["git", "diff", "--name-only", "-z", f"main...{branch}"], repo)
    paths = []
    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue
        path = os.fsdecode(raw_path)
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"Unsafe path from git diff: {path}")
        paths.append(path)
    return paths


def archive_ref(ref: str, dest: Path, repo: Path):
    """Extract ref's tree to dest using git archive | tar."""
    p1 = subprocess.Popen(["git", "archive", ref], cwd=repo, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(
        ["tar", "-x", "-C", str(dest)],
        stdin=p1.stdout,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    assert p1.stdout is not None
    p1.stdout.close()
    _out, err = p2.communicate()
    rc1 = p1.wait()
    if p2.returncode != 0 or rc1 != 0:
        raise RuntimeError(
            f"git archive {ref} failed: rc={rc1}/{p2.returncode} err={err[:200]!r}"
        )


def _reject_symlinks(root: Path) -> None:
    """Reject links before archive output can dereference one."""
    if root.is_symlink():
        raise ValueError(f"Refusing symlink in archive output: {root}")
    if not root.exists():
        return
    for current, directories, files in os.walk(root, followlinks=False):
        for name in (*directories, *files):
            path = Path(current) / name
            if path.is_symlink():
                raise ValueError(f"Refusing symlink in archive output: {path}")


def _mkdir_owned(path: Path, root: Path) -> None:
    """Create *path* without traversing a pre-existing symlink directory."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"Refusing symlink in archive output: {current}")
        current.mkdir(exist_ok=True)
        if not current.is_dir():
            raise ValueError(f"Archive output path is not a directory: {current}")


def remove_stale_files(target: Path, desired_files: set[str]) -> int:
    _reject_symlinks(target)
    removed = 0
    for existing in target.rglob("*"):
        if not existing.is_file():
            continue
        rel = existing.relative_to(target).as_posix()
        if rel not in desired_files:
            existing.unlink()
            removed += 1
    for directory in sorted(target.rglob("*"), reverse=True):
        if directory.is_dir():
            try:
                directory.rmdir()
            except OSError:
                pass
    return removed


def branch_exists(ref: str, repo: Path) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", ref], cwd=repo, capture_output=True
        ).returncode
        == 0
    )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else ""
    )
    parser.add_argument(
        "--branches",
        nargs="*",
        default=BRANCHES,
        help=f"Branches to archive (default: the {len(BRANCHES)} in BRANCHES)",
    )
    args = parser.parse_args()

    repo = find_repo_root()
    archive_root = repo / "resources" / "archived-branches"
    temp_root = repo / ".tmp-archive"
    _mkdir_owned(archive_root, repo)
    _mkdir_owned(temp_root, repo)
    _reject_symlinks(archive_root)

    summary = {}
    missing_refs = []

    with tempfile.TemporaryDirectory(dir=temp_root) as main_tmp:
        main_tmp_path = Path(main_tmp)
        print("Extracting main tree...", flush=True)
        archive_ref("main", main_tmp_path, repo)

        for branch in args.branches:
            if not branch_exists(branch, repo):
                print(f"  {branch}: SKIP (ref not found)", flush=True)
                missing_refs.append(branch)
                continue

            name = branch.removeprefix("origin/")
            name_path = PurePosixPath(name)
            if name_path.is_absolute() or ".." in name_path.parts:
                raise ValueError(f"Unsafe branch archive name: {name}")
            target = archive_root.joinpath(*name_path.parts)
            diff_files = diff_paths(branch, repo)

            with tempfile.TemporaryDirectory(dir=temp_root) as branch_tmp:
                branch_tmp_path = Path(branch_tmp)
                print(f"  archiving {branch} ({len(diff_files)} files)...", flush=True)
                archive_ref(branch, branch_tmp_path, repo)

                _mkdir_owned(target, archive_root)
                _reject_symlinks(target)
                copied = 0
                skipped_identical = 0
                skipped_missing = 0
                skipped_excluded = 0
                desired_files = set()

                for f in diff_files:
                    if f in SKIP_FILES:
                        skipped_excluded += 1
                        continue
                    src = branch_tmp_path / f
                    if not src.exists():
                        skipped_missing += 1
                        continue
                    if src.is_symlink():
                        skipped_excluded += 1
                        continue

                    branch_bytes = src.read_bytes()
                    main_src = main_tmp_path / f
                    if main_src.exists():
                        main_bytes = main_src.read_bytes()
                        if sha256_bytes(main_bytes) == sha256_bytes(branch_bytes):
                            skipped_identical += 1
                            continue

                    dest = target / f
                    if dest.is_symlink():
                        raise ValueError(f"Refusing symlink in archive output: {dest}")
                    _mkdir_owned(dest.parent, target)
                    shutil.copy2(src, dest)
                    desired_files.add(f)
                    copied += 1

                removed_stale = remove_stale_files(target, desired_files)

            summary[branch] = {
                "target": str(target.relative_to(repo)),
                "copied": copied,
                "skipped_identical": skipped_identical,
                "skipped_missing": skipped_missing,
                "skipped_excluded": skipped_excluded,
                "removed_stale": removed_stale,
            }
            print(
                f"  {branch}: copied={copied} | identical={skipped_identical} | "
                f"missing={skipped_missing} | excluded={skipped_excluded} | stale={removed_stale}",
                flush=True,
            )

    print()
    print("=== Archive summary ===")
    for b, s in summary.items():
        print(f"{b}")
        print(f"  -> {s['target']}/")
        print(
            f"     copied={s['copied']} | identical={s['skipped_identical']} | "
            f"missing={s['skipped_missing']} | excluded={s['skipped_excluded']} | "
            f"stale={s['removed_stale']}"
        )
    if missing_refs:
        print()
        print(
            f"Skipped {len(missing_refs)} branch(es) with missing refs: {missing_refs}"
        )

    return 0 if not missing_refs else 1


if __name__ == "__main__":
    sys.exit(main())
