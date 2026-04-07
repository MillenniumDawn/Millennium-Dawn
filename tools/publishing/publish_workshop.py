#!/usr/bin/env python3
"""
publish_workshop.py - Publish Millennium Dawn to Steam Workshop.

Usage:
  publish_workshop.py release --full
  publish_workshop.py beta --base-ref v1.12.3b
  publish_workshop.py release --full --username OtherUser
  STEAM_USERNAME=MyUser publish_workshop.py beta --full

Username is read from --username or the STEAM_USERNAME env var.
"""

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOI4_APP_ID = "394360"
REPO_ROOT = Path(__file__).resolve().parent.parent

# Workshop mod IDs for each target.
MOD_IDS = {
    "release": "2777392649",
    "beta": "3374271790",
}

# Files that must always be included (even if unchanged in diff mode).
ALWAYS_KEEP = {"descriptor.mod", "thumbnail.png"}

# Dev/CI artifacts excluded from all uploads.
DEFAULT_EXCLUDES = {
    ".git",
    ".github",
    ".claude",
    ".vscode",
    ".vs",
    ".idea",
    ".continue",
    ".pre-commit-config.yaml",
    ".gitignore",
    ".gitattributes",
    "CLAUDE.md",
    "CODEOWNERS",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "README.md",
    "Changelog.txt",
    "Millennium_Dawn.mod",
    "docs",
    "tools",
    "resources",
    "scenario_tests",
    "node_modules",
    "vscode-userdata:",
    "pythontools.log",
    "__pycache__",
}


def find_steamcmd() -> Path:
    found = shutil.which("steamcmd")
    if found:
        return Path(found)
    for p in [
        Path("C:/Program Files/steamcmd/steamcmd.exe"),
        Path("C:/steamcmd/steamcmd.exe"),
        Path.home() / "steamcmd" / "steamcmd.sh",
        Path("/usr/bin/steamcmd"),
        Path("/usr/local/bin/steamcmd"),
    ]:
        if p.exists():
            return p
    sys.exit("ERROR: steamcmd not found. Install it or add it to PATH.")


def get_changed_files(base_ref: str) -> set[str]:
    result = subprocess.run(
        [
            "git",
            "log",
            "--name-only",
            "--diff-filter=ACM",
            "--pretty=format:",
            f"{base_ref}..HEAD",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    files = {l for l in result.stdout.splitlines() if l}
    if not files:
        sys.exit(f"No files changed since '{base_ref}'. Nothing to publish.")
    return files


def copy_repo(dest_parent: Path, excludes: set[str]) -> Path:
    dest = dest_parent / "mod"

    def _ignore(_dir: str, names: list[str]) -> set[str]:
        return {
            n
            for n in names
            if n in excludes or any(fnmatch.fnmatch(n, p) for p in excludes)
        }

    shutil.copytree(REPO_ROOT, dest, ignore=_ignore)
    return dest


def format_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def prune_unchanged(mod_dir: Path, changed: set[str]) -> None:
    removed, kept = 0, []
    for path in list(mod_dir.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(mod_dir).as_posix()
        if rel in changed or rel in ALWAYS_KEEP:
            kept.append((rel, path.stat().st_size))
        else:
            path.unlink()
            removed += 1

    # Clean empty directories.
    for path in sorted(mod_dir.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass

    kept.sort(key=lambda x: x[1], reverse=True)
    total = sum(s for _, s in kept)
    print(f"\n  {'File':<70}  {'Size':>10}")
    print(f"  {'-'*70}  {'-'*10}")
    for rel, size in kept:
        print(f"  {rel:<70}  {format_size(size):>10}")
    print(f"  {'-'*70}  {'-'*10}")
    print(f"  {'TOTAL':<70}  {format_size(total):>10}")
    print(f"\n  Removed {removed}, kept {len(kept)} files.")


def write_vdf(mod_dir: Path, mod_id: str) -> Path:
    vdf_path = mod_dir.parent / "workshop_upload.vdf"
    vdf_path.write_text(
        f'"workshopitem"\n'
        f"{{\n"
        f'    "appid"           "{HOI4_APP_ID}"\n'
        f'    "publishedfileid" "{mod_id}"\n'
        f'    "contentfolder"   "{mod_dir}"\n'
        f'    "previewfile"     "{mod_dir / "thumbnail.png"}"\n'
        f'    "changenote"      "Update"\n'
        f"}}\n",
        encoding="utf-8",
    )
    return vdf_path


def publish(mod_dir: Path, username: str, mod_id: str) -> None:
    steamcmd = find_steamcmd()
    vdf_path = write_vdf(mod_dir, mod_id)
    print(f"  Target: {mod_id}")
    print(f"  VDF: {vdf_path}")
    subprocess.run(
        [
            str(steamcmd),
            "+login",
            username,
            "+workshop_build_item",
            str(vdf_path),
            "+quit",
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish Millennium Dawn to Steam Workshop.",
    )
    parser.add_argument(
        "target",
        choices=list(MOD_IDS.keys()),
        help="Which Workshop item to publish to",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("STEAM_USERNAME"),
        help="Steam username (default: $STEAM_USERNAME)",
    )
    parser.add_argument("--mod-id", help="Override the Workshop mod ID")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Extra exclude patterns (repeatable)",
    )
    parser.add_argument(
        "--no-default-excludes", action="store_true", help="Skip built-in exclude list"
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--base-ref", help="Git ref to diff against (changed files only)")
    mode.add_argument("--full", action="store_true", help="Publish entire mod")

    args = parser.parse_args()

    username = args.username
    if not username:
        sys.exit("ERROR: No username. Pass --username or set STEAM_USERNAME.")

    mod_id = args.mod_id or MOD_IDS[args.target]
    excludes = set() if args.no_default_excludes else set(DEFAULT_EXCLUDES)
    excludes.update(args.exclude)

    print(f"Repo:   {REPO_ROOT}")
    print(f"Target: {args.target} (mod {mod_id})")

    tmp = Path(tempfile.mkdtemp(prefix="md_publish_"))
    try:
        if args.base_ref:
            changed = get_changed_files(args.base_ref)
            print(f"{len(changed)} file(s) changed since {args.base_ref}")
            mod_dir = copy_repo(tmp, excludes)
            prune_unchanged(mod_dir, changed)
        else:
            mod_dir = copy_repo(tmp, excludes)

        publish(mod_dir, username, mod_id)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("Done.")


if __name__ == "__main__":
    main()
