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
import threading
import time
from pathlib import Path

HOI4_APP_ID = "394360"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Workshop mod IDs for each target.
MOD_IDS = {
    "release": "2777392649",
    "beta": "3374271790",
    "test": "2777133449",
}

# Display names written into descriptor.mod per target.
MOD_NAMES = {
    "release": "Millennium Dawn: A Modern Day Mod",
    "beta": "Millennium Dawn: A Beta Test Mod",
    "test": "MD Test",
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
    "Millennium_Dawn.mod",
    "docs",
    "tools",
    "resources",
    "node_modules",
    "vscode-userdata:",
    "pythontools.log",
    "__pycache__",
}


def elapsed_str(start: float) -> str:
    s = int(time.time() - start)
    if s < 60:
        return f"{s}s"
    return f"{s // 60}m {s % 60:02d}s"


class Spinner:
    """Animated spinner that shows elapsed time on a single line."""

    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, label: str):
        self._label = label
        self._start = time.time()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        i = 0
        while not self._stop.is_set():
            frame = self.FRAMES[i % len(self.FRAMES)]
            sys.stdout.write(
                f"\r  {frame} {self._label} [{elapsed_str(self._start)}]   "
            )
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.1)

    def __enter__(self) -> "Spinner":
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join()
        dt = elapsed_str(self._start)
        sys.stdout.write(f"\r  + {self._label} [{dt}]\n")
        sys.stdout.flush()


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


def dir_stats(root: Path) -> tuple[int, int]:
    """Return (file_count, total_bytes) for a directory tree."""
    count, total = 0, 0
    for path in root.rglob("*"):
        if path.is_file():
            count += 1
            total += path.stat().st_size
    return count, total


def copy_repo(dest_parent: Path, excludes: set[str]) -> Path:
    dest = dest_parent / "mod"

    def _ignore(_dir: str, names: list[str]) -> set[str]:
        return {
            n
            for n in names
            if n in excludes or any(fnmatch.fnmatch(n, p) for p in excludes)
        }

    with Spinner("Copying mod files"):
        shutil.copytree(REPO_ROOT, dest, ignore=_ignore)

    count, total = dir_stats(dest)
    print(f"    {count:,} files, {format_size(total)}")
    return dest


def format_size(n: int | float) -> str:
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


def steam_login(steamcmd: Path, username: str) -> None:
    """Log in to Steam interactively to cache credentials before uploading."""
    print(f"  Logging in to Steam as '{username}'...")
    print("  (Enter password / Steam Guard code if prompted)\n")
    ret = subprocess.call([str(steamcmd), "+login", username, "+quit"])
    if ret != 0:
        sys.exit(f"ERROR: Steam login failed (exit code {ret})")
    print("\n  Login successful — credentials cached.\n")


def publish(mod_dir: Path, username: str, mod_id: str) -> None:
    steamcmd = find_steamcmd()

    # Pre-login interactively so credentials are cached for the upload.
    steam_login(steamcmd, username)

    vdf_path = write_vdf(mod_dir, mod_id)
    print(f"  Mod ID:   {mod_id}")
    print(f"  VDF:      {vdf_path}")
    print(f"  steamcmd: {steamcmd}")
    print()

    start = time.time()
    proc = subprocess.Popen(
        [
            str(steamcmd),
            "+login",
            username,
            "+workshop_build_item",
            str(vdf_path),
            "+quit",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    phase = "Connecting"
    for line in proc.stdout:
        line = line.rstrip()
        if not line:
            continue

        # Detect phase transitions from steamcmd output.
        low = line.lower()
        if "logging in" in low or "login" in low:
            phase = "Logging in"
        elif "waiting for confirmation" in low:
            phase = "Waiting for Steam Guard"
        elif "preparing" in low:
            phase = "Preparing upload"
        elif "uploading content" in low:
            phase = "Uploading content"
        elif "uploading preview" in low:
            phase = "Uploading preview"
        elif "committing" in low:
            phase = "Committing update"

        # Show steamcmd output with elapsed time.
        print(f"  [{elapsed_str(start)}] {phase}: {line}")

    proc.wait()
    if proc.returncode != 0:
        sys.exit(f"ERROR: steamcmd exited with code {proc.returncode}")

    print(f"\n  Upload completed in {elapsed_str(start)}")


def main() -> None:
    total_start = time.time()

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

    print()
    print(f"  Repo:   {REPO_ROOT}")
    print(f"  Target: {args.target} (mod {mod_id})")
    print(f"  Mode:   {'diff from ' + args.base_ref if args.base_ref else 'full'}")
    print()

    tmp = Path(tempfile.mkdtemp(prefix="md_publish_"))
    try:
        if args.base_ref:
            changed = get_changed_files(args.base_ref)
            print(f"  {len(changed)} file(s) changed since {args.base_ref}")
            mod_dir = copy_repo(tmp, excludes)
            prune_unchanged(mod_dir, changed)
        else:
            mod_dir = copy_repo(tmp, excludes)

        # Set the correct mod name in descriptor.mod for this target.
        descriptor = mod_dir / "descriptor.mod"
        target_name = MOD_NAMES[args.target]
        if descriptor.exists():
            text = descriptor.read_text(encoding="utf-8")
            lines = text.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if line.startswith("name="):
                    lines[i] = f'name="{target_name}"\n'
                    break
            descriptor.write_text("".join(lines), encoding="utf-8")
        print(f"  Mod name: {target_name}")

        print()
        publish(mod_dir, username, mod_id)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n  Total time: {elapsed_str(total_start)}")
    print()


if __name__ == "__main__":
    main()
