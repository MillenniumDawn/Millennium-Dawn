#!/usr/bin/env python3
"""
publish_workshop.py - Publish Millennium Dawn to Steam Workshop.

Usage:
  publish_workshop.py release --full --version 1.12.3
  publish_workshop.py beta --base-ref v1.12.3b --version 1.12.3b
  publish_workshop.py release --full --username OtherUser
  STEAM_USERNAME=MyUser publish_workshop.py beta --full

Username is read from --username or the STEAM_USERNAME env var.
--version rewrites version= in descriptor.mod for this upload only; omit
to ship whatever version is currently committed in the repo.
"""

import argparse
import fnmatch
import os
import shlex
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

# Dev/CI artifacts excluded only at the repo root. Names here collide with
# legitimate game content deeper in the tree (e.g. common/resources is game
# data; docs/ has its own tools/ and resources/ subdirs).
ROOT_ONLY_EXCLUDES = {
    ".pre-commit-config.yaml",
    ".gitignore",
    ".gitattributes",
    ".secrets.baseline",
    "CODEOWNERS",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "README.md",
    "Millennium_Dawn.mod",
    "bun.lock",
    "package.json",
    "docs",
    "tools",
    "resources",
    "specs",
}

# Dev artifacts excluded wherever they appear in the tree.
ANYWHERE_EXCLUDES = {
    ".git",
    ".github",
    ".claude",
    ".vscode",
    ".vs",
    ".idea",
    ".continue",
    ".DS_Store",
    "CLAUDE.md",
    "node_modules",
    "vscode-userdata:",
    "pythontools.log",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.psd",
    "repomix-*.xml",
}

DEFAULT_EXCLUDES = ROOT_ONLY_EXCLUDES | ANYWHERE_EXCLUDES


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

    def __exit__(self, exc_type: object, *_: object) -> None:
        self._stop.set()
        self._thread.join()
        dt = elapsed_str(self._start)
        status = "+" if exc_type is None else "x"
        label = self._label if exc_type is None else f"{self._label} failed"
        sys.stdout.write(f"\r  {status} {label} [{dt}]\n")
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


def git_diff_name_only(base_ref: str, diff_filter: str) -> set[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                f"--diff-filter={diff_filter}",
                "--find-renames",
                f"{base_ref}...HEAD",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        sys.exit(f"ERROR: Failed to diff against '{base_ref}': {detail}")

    files = {l for l in result.stdout.splitlines() if l}
    return files


def get_changed_files(base_ref: str) -> set[str]:
    files = git_diff_name_only(base_ref, "ACMR")
    if not files:
        sys.exit(f"No files changed since '{base_ref}'. Nothing to publish.")
    return files


def get_deleted_files(base_ref: str) -> set[str]:
    return git_diff_name_only(base_ref, "D")


def get_publishable_changed_files(mod_dir: Path, changed: set[str]) -> set[str]:
    """Return changed files that survived the copy/exclude step."""
    return {
        path.relative_to(mod_dir).as_posix()
        for path in mod_dir.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path.relative_to(mod_dir).as_posix() in changed
    }


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

    # Anything in excludes that is also in ROOT_ONLY_EXCLUDES is applied only
    # at the repo root. Everything else matches at every depth.
    # Note: we treat any exclusion matching ROOT_ONLY_EXCLUDES as root-only,
    # even if added via --exclude.
    root_only = {e for e in excludes if e in ROOT_ONLY_EXCLUDES}
    anywhere = excludes - root_only

    def _ignore(dir_path: str, names: list[str]) -> set[str]:
        patterns = anywhere
        # dir_path is relative to REPO_ROOT during copy, so join them
        abs_dir = (REPO_ROOT / dir_path).resolve()
        if abs_dir == REPO_ROOT:
            patterns = patterns | root_only
        return {
            n
            for n in names
            if n in patterns or any(fnmatch.fnmatch(n, p) for p in patterns)
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


def escape_vdf(value: str | Path) -> str:
    """Escape a string for inclusion in a quoted VDF value."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def validate_mod_files(mod_dir: Path) -> None:
    """Check that required mod files exist."""
    required = {
        "descriptor.mod": mod_dir / "descriptor.mod",
        "thumbnail.png": mod_dir / "thumbnail.png",
    }
    missing = []
    for name, path in required.items():
        if not path.exists():
            missing.append(name)

    if missing:
        sys.exit(f"ERROR: Missing required mod files: {', '.join(missing)}")


def prune_unchanged(mod_dir: Path, changed: set[str], verbose: bool = False) -> None:
    removed, kept = 0, []
    for path in list(mod_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(mod_dir).as_posix()
        if rel in changed or rel in ALWAYS_KEEP:
            kept.append((rel, path.stat().st_size))
        else:
            try:
                path.unlink()
                removed += 1
            except (OSError, PermissionError) as e:
                print(f"  WARNING: Failed to remove {rel}: {e}")

    # Clean empty directories.
    for path in sorted(mod_dir.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass

    kept.sort(key=lambda x: x[1], reverse=True)
    total = sum(s for _, s in kept)
    if verbose:
        print(f"\n  {'File':<70}  {'Size':>10}")
        print(f"  {'-'*70}  {'-'*10}")
        for rel, size in kept:
            print(f"  {rel:<70}  {format_size(size):>10}")
        print(f"  {'-'*70}  {'-'*10}")
        print(f"  {'TOTAL':<70}  {format_size(total):>10}")
    print(
        f"\n  Removed {removed}, kept {len(kept)} files "
        f"({format_size(total)}; pass --verbose for listing)."
        if not verbose
        else f"\n  Removed {removed}, kept {len(kept)} files."
    )


def write_vdf(mod_dir: Path, mod_id: str, changenote: str) -> Path:
    vdf_path = mod_dir.parent / "workshop_upload.vdf"
    vdf_path.write_text(
        f'"workshopitem"\n'
        f"{{\n"
        f'    "appid"           "{HOI4_APP_ID}"\n'
        f'    "publishedfileid" "{escape_vdf(mod_id)}"\n'
        f'    "contentfolder"   "{escape_vdf(mod_dir)}"\n'
        f'    "previewfile"     "{escape_vdf(mod_dir / "thumbnail.png")}"\n'
        f'    "changenote"      "{escape_vdf(changenote)}"\n'
        f"}}\n",
        encoding="utf-8",
    )
    return vdf_path


def patch_descriptor(
    mod_dir: Path, target_name: str, mod_id: str, version: str | None
) -> None:
    """Rewrite name, remote_file_id, and (optionally) version in descriptor.mod.

    The repo's descriptor.mod hardcodes the release mod ID and a stale version.
    Each publish target needs its own name + ID so the launcher binds the
    uploaded content to the correct Workshop item.
    """
    descriptor = mod_dir / "descriptor.mod"
    if not descriptor.exists():
        print("  WARNING: descriptor.mod not found in content folder; skipping patch")
        return

    updates = {
        "name=": f'name="{target_name}"\n',
        "remote_file_id=": f'remote_file_id="{mod_id}"\n',
    }
    if version:
        updates["version="] = f'version="{version}"\n'

    lines = descriptor.read_text(encoding="utf-8").splitlines(keepends=True)
    patched: set[str] = set()
    for i, line in enumerate(lines):
        for prefix, replacement in updates.items():
            if prefix in patched:
                continue
            if line.startswith(prefix):
                lines[i] = replacement
                patched.add(prefix)
                break

    # Any field missing from the descriptor is appended so the upload is
    # self-consistent rather than silently omitting it.
    for prefix in updates.keys() - patched:
        print(
            f"  WARNING: descriptor.mod had no '{prefix.rstrip('=')}' line; appending"
        )
        lines.append(updates[prefix])

    descriptor.write_text("".join(lines), encoding="utf-8")

    print(f"  Mod name:       {target_name}")
    print(f"  remote_file_id: {mod_id}")
    if version:
        print(f"  version:        {version}")
    else:
        print("  version:        (unchanged — using repo descriptor.mod value)")


def steam_login(steamcmd: Path, username: str) -> None:
    """Log in to Steam interactively to cache credentials before uploading."""
    print(f"  Logging in to Steam as '{username}'...")
    print("  (Enter password / Steam Guard code if prompted)\n")
    ret = subprocess.call([str(steamcmd), "+login", username, "+quit"])
    if ret != 0:
        sys.exit(f"ERROR: Steam login failed (exit code {ret})")
    print("\n  Login successful — credentials cached.\n")


def publish(
    mod_dir: Path, username: str, mod_id: str, changenote: str, verbose: bool = False
) -> None:
    steamcmd = find_steamcmd()

    # Pre-login interactively so credentials are cached for the upload.
    steam_login(steamcmd, username)

    vdf_path = write_vdf(mod_dir, mod_id, changenote)

    # Persistent log outside the temp content folder so it survives cleanup.
    log_path = Path(tempfile.gettempdir()) / f"md_publish_{int(time.time())}.log"

    count, total = dir_stats(mod_dir)

    # Phases are ordered: only move forward, never backwards, to avoid flapping.
    PHASES = [
        ("Connecting", ()),
        ("Logging in", ("logging in", "logged in")),
        ("Waiting for Steam Guard", ("waiting for confirmation",)),
        ("Preparing upload", ("preparing",)),
        ("Uploading content", ("uploading content",)),
        ("Uploading preview", ("uploading preview",)),
        ("Committing update", ("committing",)),
    ]

    # +set_spew_level N N raises steamcmd's console/log verbosity (0=silent, 4=debug).
    # +@ShutdownOnFailedCommand 0 prints failures instead of bailing silently.
    cmd = [
        str(steamcmd),
        "+@ShutdownOnFailedCommand",
        "0",
        "+@NoPromptForPassword",
        "1",
        "+set_spew_level",
        "4",
        "4",
        "+login",
        username,
        "+workshop_build_item",
        str(vdf_path),
        "+quit",
    ]

    preamble = [
        f"  Mod ID:       {mod_id}",
        f"  Content dir:  {mod_dir}",
        f"  Files:        {count:,}",
        f"  Total size:   {format_size(total)}",
        f"  VDF:          {vdf_path}",
        f"  steamcmd:     {steamcmd}",
        f"  Log file:     {log_path}",
        "",
        "  --- workshop_upload.vdf ---",
        *(f"    {l}" for l in vdf_path.read_text(encoding="utf-8").splitlines()),
        "  ---------------------------",
        "",
        f"  Command: {shlex.join(cmd)}",
        "",
    ]

    # Short summary always prints; full preamble (VDF contents + command line)
    # only at --verbose. The full version is still written to the log file
    # regardless, so post-mortem debugging isn't affected.
    if verbose:
        for pline in preamble:
            print(pline)
    else:
        for pline in preamble[:7]:
            print(pline)
        print(
            "  (pass --verbose to echo workshop_upload.vdf and the steamcmd command)\n"
        )

    # Preserve preamble context in the log file for post-mortem; each
    # attempt appends its own section below.
    with log_path.open("w", encoding="utf-8") as log_f:
        for pline in preamble:
            log_f.write(pline + "\n")

    # steamcmd's first workshop upload frequently fails with transient CM /
    # session errors; a second attempt almost always succeeds. Auth failures
    # short-circuit since they don't fix themselves.
    MAX_ATTEMPTS = 3
    RETRY_BACKOFF_SECS = 15
    AUTH_ERROR_MARKERS = (
        "failed login",
        "invalid password",
        "two-factor code mismatch",
        "account logon denied",
        "rate limit exceeded",
    )

    overall_start = time.time()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt > 1:
            print(
                f"\n  Retrying in {RETRY_BACKOFF_SECS}s "
                f"(attempt {attempt}/{MAX_ATTEMPTS})...\n"
            )
            time.sleep(RETRY_BACKOFF_SECS)

        start = time.time()
        phase_start = start
        phase_idx = 0
        phase_timings: list[tuple[str, float]] = []
        auth_failed = False

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        with log_path.open("a", encoding="utf-8") as log_f:
            log_f.write(f"\n=== Attempt {attempt}/{MAX_ATTEMPTS} ===\n")
            log_f.flush()

            for line in proc.stdout:
                line = line.rstrip()
                if not line:
                    continue

                log_f.write(line + "\n")
                log_f.flush()

                low = line.lower()
                if any(m in low for m in AUTH_ERROR_MARKERS):
                    auth_failed = True

                # Detect monotonic phase transitions from steamcmd output.
                for i in range(phase_idx + 1, len(PHASES)):
                    name, keywords = PHASES[i]
                    if any(k in low for k in keywords):
                        dt = time.time() - phase_start
                        phase_timings.append((PHASES[phase_idx][0], dt))
                        print(
                            f"  [{elapsed_str(start)}] + {PHASES[phase_idx][0]} done ({int(dt)}s)"
                        )
                        phase_idx = i
                        phase_start = time.time()
                        break

                # Per-line steamcmd echo is huge (hundreds of lines per upload);
                # the full stream is still captured in the log file. At default
                # verbosity we only surface lines that look like errors/warnings
                # so the user isn't blind if steamcmd is unhappy.
                if verbose:
                    print(f"  [{elapsed_str(start)}] {PHASES[phase_idx][0]}: {line}")
                elif any(
                    m in low
                    for m in (
                        "error",
                        "warning",
                        "failed",
                        "fail ",
                        "denied",
                        "timeout",
                    )
                ):
                    print(f"  [{elapsed_str(start)}] {PHASES[phase_idx][0]}: {line}")

        proc.wait()
        phase_timings.append((PHASES[phase_idx][0], time.time() - phase_start))

        print(f"\n  --- Phase timings (attempt {attempt}) ---")
        for name, dt in phase_timings:
            print(f"    {name:<28}  {int(dt)}s")
        print(f"    {'TOTAL':<28}  {elapsed_str(start)}\n")

        if proc.returncode == 0:
            print(
                f"  Upload completed in {elapsed_str(overall_start)} "
                f"across {attempt} attempt(s)"
            )
            print(f"  Full steamcmd log preserved at: {log_path}")
            return

        if auth_failed:
            print(f"  Full steamcmd output: {log_path}")
            sys.exit(
                f"ERROR: steamcmd auth failure (exit code {proc.returncode}) — not retrying"
            )

        print(f"  Attempt {attempt} failed with exit code {proc.returncode}.")

    print(f"  Full steamcmd output: {log_path}")
    sys.exit(
        f"ERROR: steamcmd exited with code {proc.returncode} "
        f"after {MAX_ATTEMPTS} attempts"
    )


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
        "--version",
        help='Override version= in descriptor.mod (e.g. "1.12.3"). '
        "Leave unset to ship the value already committed in the repo.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Extra exclude patterns (repeatable)",
    )
    parser.add_argument(
        "--no-default-excludes", action="store_true", help="Skip built-in exclude list"
    )
    parser.add_argument(
        "--changenote",
        default="Update",
        help="Change description for workshop (default: Update)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Echo the full file listing, VDF contents, steamcmd command, "
        "and per-line steamcmd output (default: summary only; full stream "
        "is always written to the log file).",
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

    print(
        f"\n  Repo:   {REPO_ROOT}\n"
        f"  Target: {args.target} (mod {mod_id})\n"
        f"  Mode:   {'diff from ' + args.base_ref if args.base_ref else 'full'}\n"
    )

    tmp = Path(tempfile.mkdtemp(prefix="md_publish_"))
    try:
        if args.base_ref:
            deleted = get_deleted_files(args.base_ref)
            if deleted:
                sys.exit(
                    "ERROR: Diff publish cannot safely express deleted files. "
                    "Use --full when the range removes content."
                )

            changed = get_changed_files(args.base_ref)
            print(f"  {len(changed)} file(s) changed since {args.base_ref}")
            mod_dir = copy_repo(tmp, excludes)
            publishable_changed = get_publishable_changed_files(mod_dir, changed)
            skipped = sorted(changed - publishable_changed)
            if skipped:
                print(
                    "  "
                    f"{len(skipped)} changed file(s) are excluded from publishing and will be ignored"
                )
            if not publishable_changed - ALWAYS_KEEP:
                sys.exit(
                    "ERROR: No publishable mod files changed after excludes. "
                    "Use --full or adjust --exclude / --no-default-excludes."
                )
            prune_unchanged(mod_dir, publishable_changed, verbose=args.verbose)
        else:
            mod_dir = copy_repo(tmp, excludes)

        # Rewrite descriptor.mod so the shipped copy matches this target.
        patch_descriptor(mod_dir, MOD_NAMES[args.target], mod_id, args.version)

        # Validate required files exist
        validate_mod_files(mod_dir)

        print()
        publish(mod_dir, username, mod_id, args.changenote, verbose=args.verbose)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n  Total time: {elapsed_str(total_start)}\n")


if __name__ == "__main__":
    main()
