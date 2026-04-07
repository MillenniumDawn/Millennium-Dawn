#!/usr/bin/env python3
"""
Test staged validators against REAL mod files that have known issues.

Stages actual codebase files (without modifying them), runs each validator
with --staged, and verifies they find the expected issues.

Usage:
    python3 tools/test_staged_validators_real.py
"""

import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)

MAX_TIME = 10.0
passed = 0
failed = 0
errors = []


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def stage_file_as_modified(path):
    """Stage an existing file by touching it (add to index without changing content).

    We use `git add` which works even if the file hasn't changed — it just
    refreshes the index entry so --staged sees it.
    """
    # Create a harmless change, stage it, then restore the original
    # This is needed because `git add` on an unchanged file won't mark it staged
    with open(path, "r", encoding="utf-8-sig") as f:
        original = f.read()
    # Append a blank line
    with open(path, "a", encoding="utf-8-sig") as f:
        f.write("\n")
    run(["git", "add", path])
    # Restore the working copy but keep it staged
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(original)


def unstage_file(path):
    """Unstage a file and restore its working tree state."""
    run(["git", "reset", "HEAD", path])
    run(["git", "checkout", "--", path])


def run_validator(script, label, expect_issues=True, min_issues=0):
    global passed, failed, errors

    cmd = [
        "python3",
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

    # Extract issue count from output
    issue_count = 0
    import re as _re

    for line in (result.stderr or "").split("\n") + (result.stdout or "").split("\n"):
        m = _re.search(r"(\d+)\s+TOTAL ISSUES FOUND", line)
        if m:
            issue_count = int(m.group(1))

    ok = True
    status_parts = []

    if elapsed > MAX_TIME:
        ok = False
        status_parts.append(f"TOO SLOW ({elapsed:.1f}s)")
    else:
        status_parts.append(f"{elapsed:.1f}s")

    if expect_issues and result.returncode == 0:
        ok = False
        status_parts.append("expected issues but validator passed")
    elif not expect_issues and result.returncode != 0:
        ok = False
        status_parts.append(f"expected pass but got exit {result.returncode}")

    if expect_issues and min_issues > 0 and issue_count < min_issues:
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

    staged_files = []

    def stage(path):
        stage_file_as_modified(path)
        staged_files.append(path)

    def cleanup():
        for path in staged_files:
            unstage_file(path)
        staged_files.clear()

    try:
        # ── Test 1: Event file with known issues ───────────────────────────
        print("Test 1: Stage a real event file with known issues")
        print("-" * 60)
        # Event Horizon.txt has 11 missing is_triggered_only
        stage("events/Event Horizon.txt")

        run_validator(
            "validate_events.py",
            "events: Event Horizon.txt (11 missing is_triggered_only)",
            expect_issues=True,
            min_issues=10,
        )
        cleanup()

        # ── Test 2: Loc file with known issues ─────────────────────────────
        print("\nTest 2: Stage a real localisation file with known issues")
        print("-" * 60)
        # MD_focus_ALG has color syntax issues
        stage("localisation/english/MD_focus_ALG_l_english.yml")

        run_validator(
            "validate_localisation.py",
            "localisation: ALG loc file (color syntax issues)",
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
        stage("events/Event Horizon.txt")
        stage("localisation/english/MD_focus_ALG_l_english.yml")
        stage("common/national_focus/05_algeria.txt")

        run_validator(
            "validate_events.py",
            "events: multiple files staged (only events checked)",
            expect_issues=True,
            min_issues=10,
        )
        run_validator(
            "validate_localisation.py",
            "localisation: multiple files staged (only loc checked)",
            expect_issues=True,
            min_issues=1,
        )
        cleanup()

    except Exception as e:
        print(f"\nERROR: {e}")
        failed += 1
    finally:
        cleanup()

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(e)
    print("=" * 60)

    return 1 if failed else 0


# Override run_validator to handle expect_issues=None (don't care about result)
_orig_run_validator = run_validator


def run_validator(script, label, expect_issues=True, min_issues=0):
    global passed, failed, errors

    cmd = [
        "python3",
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

    issue_count = 0
    import re as _re

    for line in (result.stderr or "").split("\n") + (result.stdout or "").split("\n"):
        m = _re.search(r"(\d+)\s+TOTAL ISSUES FOUND", line)
        if m:
            issue_count = int(m.group(1))

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
        output = (result.stderr or "") + (result.stdout or "")
        for line in output.strip().split("\n")[-5:]:
            print(f"        {line}")


if __name__ == "__main__":
    sys.exit(main())
