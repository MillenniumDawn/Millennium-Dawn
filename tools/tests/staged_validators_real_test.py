#!/usr/bin/env python3
"""
Test staged validators against REAL mod files that have known issues.

Stages actual codebase files with temporary deliberate issues, runs each
validator with --staged, and verifies they find the expected issues.

Usage:
    python3 tools/test_staged_validators_real.py
"""

import os
import shutil
import subprocess
import sys
import time
from unittest import SkipTest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAX_TIME = 15.0
passed = 0
failed = 0
errors: list[str] = []

EVENT_INTEGRATION_SUFFIX = """
country_event = {
\tid = _staged_validator.1
\ttitle = _staged_validator.1.t
\tdesc = _staged_validator.1.d
\toption = {
\t\tname = _staged_validator.1.a
\t}
}
"""
LOC_INTEGRATION_SUFFIX = '\n _staged_validator_key: "broken ["\n'


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def stage_file_as_modified(path, suffix="\n"):
    """Append a temporary issue and stage the file for a real validator run."""
    with open(path, "a", encoding="utf-8-sig") as f:
        f.write(suffix)
    run(["git", "add", path])


def unstage_file(path):
    """Unstage a file and restore its working tree state."""
    run(["git", "reset", "HEAD", path])
    run(["git", "checkout", "--", path])


def run_validator(
    script: str,
    label: str,
    expect_issues: bool | None = True,
    min_issues: int = 0,
):
    global passed, failed, errors

    cmd = [
        sys.executable,
        f"tools/validation/{script}",
        "--staged",
        "--strict",
        "--no-color",
        "--workers",
        "2",
    ]

    start = time.time()
    result = run(cmd)
    elapsed = time.time() - start

    # Extract issue count from the validator summary.
    issue_count = 0
    import re as _re

    output = (result.stderr or "") + (result.stdout or "")
    total_match = _re.search(r"(\d+)\s+TOTAL ISSUES FOUND", output)
    if total_match:
        issue_count = int(total_match.group(1))
    else:
        summary_match = _re.search(
            r"(\d+)\s+ERROR\(S\)(?:\s*-\s*(\d+)\s+WARNING\(S\))?", output
        )
        if summary_match:
            issue_count = int(summary_match.group(1)) + int(summary_match.group(2) or 0)

    ok = True
    status_parts = []

    if elapsed > MAX_TIME:
        ok = False
        status_parts.append(f"TOO SLOW ({elapsed:.1f}s)")
    else:
        status_parts.append(f"{elapsed:.1f}s")

    if expect_issues is True and result.returncode == 0:
        ok = False
        status_parts.append("expected issues but validator passed")
    elif expect_issues is False and result.returncode != 0:
        ok = False
        status_parts.append(f"expected pass but got exit {result.returncode}")

    if expect_issues is True and min_issues > 0 and issue_count < min_issues:
        ok = False
        status_parts.append(f"expected >= {min_issues} issues but found {issue_count}")
    elif issue_count > 0:
        status_parts.append(f"{issue_count} issues")

    if ok:
        passed += 1
        print(f"  PASS  {label} [{', '.join(status_parts)}]")
    else:
        failed += 1
        msg = f"  FAIL  {label} [{', '.join(status_parts)}]"
        errors.append(msg)
        print(msg)
        # Print last few lines of stderr for context
        output = (result.stderr or "") + (result.stdout or "")
        for line in output.strip().split("\n")[-5:]:
            print(f"        {line}")


def main():
    global passed, failed

    os.chdir(REPO_ROOT)
    staged_files = []

    def stage(path, suffix="\n"):
        stage_file_as_modified(path, suffix)
        staged_files.append(path)

    def cleanup():
        for path in staged_files:
            unstage_file(path)
        staged_files.clear()

    try:
        # ── Test 1: Event file with known issues ───────────────────────────
        print("Test 1: Stage a real event file with known issues")
        print("-" * 60)
        # Add a deliberately incomplete event to Event Horizon.txt.
        stage("events/Event Horizon.txt", EVENT_INTEGRATION_SUFFIX)

        run_validator(
            "validate_events.py",
            "events: Event Horizon.txt (missing is_triggered_only)",
            expect_issues=True,
            min_issues=1,
        )
        cleanup()

        # ── Test 2: Loc file with known issues ─────────────────────────────
        print("\nTest 2: Stage a real localisation file with known issues")
        print("-" * 60)
        # Add an unclosed localization bracket to MD_focus_ALG.
        stage(
            "localisation/english/MD_focus_ALG_l_english.yml",
            LOC_INTEGRATION_SUFFIX,
        )

        run_validator(
            "validate_localisation.py",
            "localisation: ALG loc file (unclosed bracket)",
            expect_issues=True,
            min_issues=1,
        )
        cleanup()

        # ── Test 3: Variables validator skips in staged mode ──────────────
        print("\nTest 3: Variables validator skips in staged mode (needs cross-file)")
        print("-" * 60)
        stage("common/national_focus/05_algeria.txt")

        run_validator(
            "validate_variables.py",
            "variables: skips in staged mode (needs cross-file comparison)",
            expect_issues=False,
        )
        cleanup()

        # ── Test 4: Cosmetic tags with a real file ─────────────────────────
        print("\nTest 4: Stage a real file and verify cosmetic tags runs quickly")
        print("-" * 60)
        stage("common/national_focus/05_algeria.txt")

        run_validator(
            "validate_cosmetic_tags.py",
            "cosmetic tags: Algeria focus tree (missing tag check only)",
            expect_issues=None,
        )
        cleanup()

        # ── Test 5: Multiple files staged at once ──────────────────────────
        print("\nTest 5: Stage multiple files and verify validators handle them")
        print("-" * 60)
        stage("events/Event Horizon.txt", EVENT_INTEGRATION_SUFFIX)
        stage(
            "localisation/english/MD_focus_ALG_l_english.yml",
            LOC_INTEGRATION_SUFFIX,
        )
        stage("common/national_focus/05_algeria.txt")

        run_validator(
            "validate_events.py",
            "events: multiple files staged (only events checked)",
            expect_issues=True,
            min_issues=1,
        )
        run_validator(
            "validate_localisation.py",
            "localisation: multiple files staged (only loc checked)",
            expect_issues=True,
            min_issues=1,
        )
        cleanup()

    except Exception as exc:
        print(f"\nERROR: {exc}")
        failed += 1
    finally:
        cleanup()

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for error in errors:
            print(error)
    print("=" * 60)

    return 1 if failed else 0


# ── pytest entry points ─────────────────────────────────────────────────────
# Without a `test_*` function pytest collects this `*_test.py` module but finds
# zero tests. These wrap the script logic so `pytest` actually exercises it.

_TOUCHED_FILES = (
    "events/Event Horizon.txt",
    "localisation/english/MD_focus_ALG_l_english.yml",
    "common/national_focus/05_algeria.txt",
)


def _touched_files_clean() -> bool:
    r = subprocess.run(
        ["git", "status", "--porcelain", "--", *_TOUCHED_FILES],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0 and not r.stdout.strip()


def _game_content_checked_out() -> bool:
    """CI's report-lib-tests job sparse-checks out only tools/ — no game dirs."""
    return all(
        os.path.isdir(os.path.join(REPO_ROOT, d))
        for d in ("events", "common", "localisation")
    )


def test_real_files_present():
    """Always-collectible smoke check needing no git staging area.

    Skips under a sparse checkout (e.g. the CI report-lib-tests job, which only
    checks out tools/) since the game content this asserts on isn't present there.
    """
    if not _game_content_checked_out():
        raise SkipTest("game content not checked out (sparse checkout)")
    for rel in _TOUCHED_FILES:
        assert os.path.exists(os.path.join(REPO_ROOT, rel))


def test_staged_validators_real():
    """Integration run; stages/restores real files, so they must be clean first.

    Opt-in (MD_RUN_STAGED_INTEGRATION=1): it mutates the working repo and runs
    the full validator set, so it stays out of the default `pytest` sweep."""
    if not os.environ.get("MD_RUN_STAGED_INTEGRATION"):
        raise SkipTest(
            "set MD_RUN_STAGED_INTEGRATION=1 to run staged-validator integration"
        )
    if shutil.which("git") is None:
        raise SkipTest("git not available")
    if not _touched_files_clean():
        raise SkipTest("target files have local changes; skipping to avoid clobbering")
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
