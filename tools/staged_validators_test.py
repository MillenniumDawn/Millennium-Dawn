#!/usr/bin/env python3
"""
Test that validators work correctly in --staged mode.

Creates temporary files with deliberate errors, stages them via git,
runs each validator with --staged, and checks that:
  1. Validators exit quickly (under 5 seconds each)
  2. Validators that should find issues DO find issues (non-zero exit)
  3. Validators that should skip (no relevant files) exit cleanly (zero exit)

Usage:
    python3 tools/test_staged_validators.py

All temporary files and git state are cleaned up automatically.
"""

import os
import subprocess
import sys
import tempfile
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)

# Maximum seconds a staged validator should take
MAX_TIME = 5.0

# Track results
passed = 0
failed = 0
errors = []


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def git_stage(path):
    run(["git", "add", path])


def git_unstage(path):
    run(["git", "reset", "HEAD", path], cwd=REPO_ROOT)


def git_restore(path):
    """Remove a file from the index and working tree if it was newly created."""
    run(["git", "reset", "HEAD", path], cwd=REPO_ROOT)
    if os.path.exists(path):
        os.remove(path)


def run_validator(script, label, expect_issues=True):
    """Run a validator with --staged and check the result."""
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

    ok = True
    status_parts = []

    # Check timing
    if elapsed > MAX_TIME:
        ok = False
        status_parts.append(f"TOO SLOW ({elapsed:.1f}s > {MAX_TIME}s)")
    else:
        status_parts.append(f"{elapsed:.2f}s")

    # Check exit code
    if expect_issues and result.returncode == 0:
        ok = False
        status_parts.append("expected issues but validator passed")
    elif not expect_issues and result.returncode != 0:
        ok = False
        status_parts.append(
            f"expected clean pass but got exit code {result.returncode}"
        )

    if ok:
        passed += 1
        print(f"  PASS  {label} [{', '.join(status_parts)}]")
    else:
        failed += 1
        msg = f"  FAIL  {label} [{', '.join(status_parts)}]"
        errors.append(msg)
        print(msg)
        if result.stderr:
            for line in result.stderr.strip().split("\n")[-5:]:
                print(f"        {line}")


# ── Test files with deliberate errors ──────────────────────────────────────

TEST_EVENT_FILE = "events/_test_staged_validator.txt"
TEST_EVENT_CONTENT = """\
add_namespace = _test_staged

# Missing is_triggered_only
country_event = {
\tid = _test_staged.1
\ttitle = _test_staged.1.t
\tdesc = _test_staged.1.d

\toption = {
\t\tname = _test_staged.1.a
\t}
}
"""

TEST_DECISION_FILE = "common/decisions/_test_staged_validator.txt"
TEST_DECISION_CONTENT = """\
test_decision_category = {
\t_test_staged_decision = {
\t\ticon = GFX_decision_generic
\t\tavailable = {
\t\t\talways = yes
\t\t}
\t\tcomplete_effect = {
\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision _test_staged_decision"
\t\t}
\t}
}
"""

TEST_LOC_FILE = "localisation/english/_test_staged_validator_l_english.yml"
TEST_LOC_CONTENT = '\ufeffl_english:\n _test_staged_key: "value [unclosed bracket"\n'

TEST_HISTORY_FILE = "history/countries/_test_staged_validator - Testland.txt"
# SAM_non_got requires air_defense_non_got — omitting the prerequisite triggers an error
TEST_HISTORY_CONTENT = """\
capital = 1

set_technology = {
\tSAM_non_got = 1
}
"""

TEST_FILES = [
    TEST_EVENT_FILE,
    TEST_DECISION_FILE,
    TEST_LOC_FILE,
    TEST_HISTORY_FILE,
]


def create_test_files():
    for path, content in [
        (TEST_EVENT_FILE, TEST_EVENT_CONTENT),
        (TEST_DECISION_FILE, TEST_DECISION_CONTENT),
        (TEST_LOC_FILE, TEST_LOC_CONTENT),
        (TEST_HISTORY_FILE, TEST_HISTORY_CONTENT),
    ]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        git_stage(path)


def cleanup_test_files():
    for path in TEST_FILES:
        git_restore(path)


def main():
    global passed, failed

    print("Creating test files and staging them...\n")
    create_test_files()

    try:
        # ── Test 1: validators find issues in their relevant staged files ──

        print("Test: validators detect issues in staged files")
        print("-" * 60)

        run_validator(
            "validate_events.py",
            "events validator finds missing is_triggered_only",
            expect_issues=True,
        )

        run_validator(
            "validate_decisions.py",
            "decisions validator skips in staged mode (needs full scan)",
            expect_issues=False,
        )

        run_validator(
            "validate_localisation.py",
            "localisation validator finds unpaired bracket",
            expect_issues=True,
        )

        # history_techs should find issues with non-existent tech
        run_validator(
            "validate_history_techs.py",
            "history techs validator finds bad tech dependency",
            expect_issues=True,
        )

        print()

        # ── Test 2: validators that skip in staged mode ──

        print("Test: validators skip cross-reference checks in staged mode")
        print("-" * 60)

        run_validator(
            "validate_unused_scripted.py",
            "unused scripted skips entirely in staged mode",
            expect_issues=False,
        )

        print()

        # ── Test 3: validators with no relevant staged files ──

        print("Test: validators exit fast when no relevant files staged")
        print("-" * 60)

        # Unstage everything, stage only the loc file
        for path in TEST_FILES:
            run(["git", "reset", "HEAD", path])
        git_stage(TEST_LOC_FILE)

        run_validator(
            "validate_events.py",
            "events validator skips (no event files staged)",
            expect_issues=False,
        )

        run_validator(
            "validate_decisions.py",
            "decisions validator skips (no decision files staged)",
            expect_issues=False,
        )

        run_validator(
            "validate_variables.py",
            "variables validator skips (no .txt files staged)",
            expect_issues=False,
        )

        run_validator(
            "validate_cosmetic_tags.py",
            "cosmetic tags validator skips (no .txt files staged)",
            expect_issues=False,
        )

        run_validator(
            "validate_scripted_localisation.py",
            "scripted loc validator skips (no scripted_loc files staged)",
            expect_issues=False,
        )

        # Re-stage everything for cleanup
        for path in TEST_FILES:
            if os.path.exists(path):
                git_stage(path)

    finally:
        print("\nCleaning up test files...")
        cleanup_test_files()

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(e)
    print("=" * 60)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
