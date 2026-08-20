#!/usr/bin/env python3
"""
Test that validators work correctly in --staged mode.

Creates temporary files with deliberate errors, stages them via git,
runs each validator with --staged, and checks that:
  1. Validators complete within the integration time budget
  2. Validators that should find issues DO find issues (non-zero exit)
  3. Validators that should skip (no relevant files) exit cleanly (zero exit)

Usage:
    python3 tools/test_staged_validators.py

All temporary files and git state are cleaned up automatically.
"""

import os
import shutil
import subprocess
import sys
import time
from unittest import SkipTest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Maximum seconds a staged validator should take in CI
MAX_TIME = 15.0
# This validator intentionally scans the full repository in staged mode.
TIME_BUDGETS = {"validate_scripted_localisation.py": 30.0}

passed = 0
failed = 0
errors: list[str] = []


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def _assert_safe_path(path):
    if ".." in path or os.path.isabs(path) or path not in TEST_FILES:
        raise ValueError(f"unsafe test path: {path}")


def git_stage(path):
    _assert_safe_path(path)
    run(["git", "add", path])


def git_unstage(path):
    run(["git", "reset", "HEAD", path], cwd=REPO_ROOT)


def git_restore(path):
    """Remove a file from the index and working tree if it was newly created."""
    _assert_safe_path(path)
    run(["git", "reset", "HEAD", path], cwd=REPO_ROOT)
    if os.path.exists(path):
        # pi-lens-ignore: python-path-traversal
        os.remove(path)


def run_validator(
    script, label, expect_issues=True, expected_path=None, expected_category=None
):
    """Run a validator with --staged and check the result."""
    global passed, failed, errors

    cmd = [
        sys.executable,
        f"tools/validation/{script}",
        "--staged",
        "--strict",
        "--no-color",
        "--workers",
        "4",
    ]

    start = time.time()
    result = run(cmd)
    elapsed = time.time() - start

    ok = True
    status_parts = []
    time_budget = TIME_BUDGETS.get(script, MAX_TIME)

    if elapsed > time_budget:
        ok = False
        status_parts.append(f"TOO SLOW ({elapsed:.1f}s > {time_budget}s)")
    else:
        status_parts.append(f"{elapsed:.2f}s")

    output = (result.stdout or "") + (result.stderr or "")
    if expect_issues and result.returncode != 1:
        ok = False
        status_parts.append(
            f"expected findings exit code 1 but got {result.returncode}"
        )
    elif expect_issues and expected_path and expected_path not in output:
        ok = False
        status_parts.append(f"missing expected path {expected_path}")
    elif expect_issues and expected_category and expected_category not in output:
        ok = False
        status_parts.append(f"missing expected category {expected_category}")
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
        _assert_safe_path(path)
        # pi-lens-ignore: python-path-traversal
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # pi-lens-ignore: python-path-traversal
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        git_stage(path)


def cleanup_test_files():
    for path in TEST_FILES:
        git_restore(path)


def main():
    global passed, failed

    os.chdir(REPO_ROOT)
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
            expected_path=TEST_EVENT_FILE,
            expected_category="missing-triggered-only",
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
            expected_path=os.path.basename(TEST_LOC_FILE),
            expected_category="Unpaired brackets found in localisation",
        )

        # history_techs should find issues with non-existent tech
        run_validator(
            "validate_history.py",
            "history techs validator finds bad tech dependency",
            expect_issues=True,
            expected_path=os.path.basename(TEST_HISTORY_FILE),
            expected_category="missing technology prerequisites",
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


# ── pytest entry points ─────────────────────────────────────────────────────
# Without a `test_*` function pytest collects this `*_test.py` module but finds
# zero tests. These wrap the script logic so `pytest` actually exercises it.


def _index_is_clean() -> bool:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0 and not r.stdout.strip()


def test_validator_scripts_exist():
    """Always-collectible smoke check needing no git staging area."""
    for script in (
        "validate_events.py",
        "validate_decisions.py",
        "validate_localisation.py",
        "validate_history.py",
    ):
        script_path = os.path.join(REPO_ROOT, "tools", "validation", script)
        if not os.path.exists(script_path):
            raise AssertionError(f"missing validator script: {script_path}")


def test_staged_validators():
    """Integration run; needs a clean git index (it stages/unstages files).

    Opt-in (MD_RUN_STAGED_INTEGRATION=1): it mutates the working repo and runs
    the full validator set, so it stays out of the default `pytest` sweep."""
    if not os.environ.get("MD_RUN_STAGED_INTEGRATION"):
        raise SkipTest(
            "set MD_RUN_STAGED_INTEGRATION=1 to run staged-validator integration"
        )
    if shutil.which("git") is None:
        raise SkipTest("git not available")
    if not _index_is_clean():
        raise SkipTest("git index has staged changes; skipping to avoid clobbering")
    if main() != 0:
        raise AssertionError("staged validator integration failed")


if __name__ == "__main__":
    sys.exit(main())
