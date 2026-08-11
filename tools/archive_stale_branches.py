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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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
    archive_root.mkdir(parents=True, exist_ok=True)
    temp_root.mkdir(parents=True, exist_ok=True)

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
            target = archive_root / name

            # 3-dot diff: only changes in branch not in main
            diff_out = run(
                ["git", "diff", "--name-only", f"main...{branch}"], repo, text=True
            )
            diff_files = [f for f in diff_out.splitlines() if f.strip()]

            with tempfile.TemporaryDirectory(dir=temp_root) as branch_tmp:
                branch_tmp_path = Path(branch_tmp)
                print(f"  archiving {branch} ({len(diff_files)} files)...", flush=True)
                archive_ref(branch, branch_tmp_path, repo)

                target.mkdir(parents=True, exist_ok=True)
                copied = 0
                skipped_identical = 0
                skipped_missing = 0
                skipped_excluded = 0

                for f in diff_files:
                    if f in SKIP_FILES:
                        skipped_excluded += 1
                        continue
                    # git diff --name-only quotes paths with non-ASCII bytes
                    if not f or f.startswith('"'):
                        continue

                    src = branch_tmp_path / f
                    if not src.exists():
                        skipped_missing += 1
                        continue

                    branch_bytes = src.read_bytes()
                    main_src = main_tmp_path / f
                    if main_src.exists():
                        main_bytes = main_src.read_bytes()
                        if sha256_bytes(main_bytes) == sha256_bytes(branch_bytes):
                            skipped_identical += 1
                            continue

                    dest = target / f
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    copied += 1

            summary[branch] = {
                "target": str(target.relative_to(repo)),
                "copied": copied,
                "skipped_identical": skipped_identical,
                "skipped_missing": skipped_missing,
                "skipped_excluded": skipped_excluded,
            }
            print(
                f"  {branch}: copied={copied} | identical={skipped_identical} | "
                f"missing={skipped_missing} | excluded={skipped_excluded}",
                flush=True,
            )

    print()
    print("=== Archive summary ===")
    for b, s in summary.items():
        print(f"{b}")
        print(f"  -> {s['target']}/")
        print(
            f"     copied={s['copied']} | identical={s['skipped_identical']} | "
            f"missing={s['skipped_missing']} | excluded={s['skipped_excluded']}"
        )
    if missing_refs:
        print()
        print(
            f"Skipped {len(missing_refs)} branch(es) with missing refs: {missing_refs}"
        )

    return 0 if not missing_refs else 1


if __name__ == "__main__":
    sys.exit(main())
