#!/usr/bin/env python3
"""
Test that validators work correctly in --staged mode.

Creates temporary files with deliberate errors, stages them via git,
runs each validator with --staged, and checks that:
  1. Validators complete within the integration time budget
  2. Validators that should find issues DO find issues (non-zero exit)
  3. Validators that should skip (no relevant files) exit cleanly (zero exit)

Usage:
    MD_RUN_STAGED_INTEGRATION=1 python -m pytest tools/tests/staged_validators_test.py

All temporary files and git state are cleaned up automatically.
"""

import os
import sys
from unittest import SkipTest

from _staged_integration_gate import require_staged_integration_enabled
from shared.paths import REPO_ROOT
from shared.staged_harness import StagedHarness, restore_all
from shared.suite import run_git


def _assert_safe_path(path):
    if ".." in path or os.path.isabs(path) or path not in TEST_FILES:
        raise ValueError(f"unsafe test path: {path}")


def git_stage(path):
    _assert_safe_path(path)
    run_git(REPO_ROOT, "add", path)


def git_unstage(path):
    run_git(REPO_ROOT, "reset", "HEAD", path)


def git_restore(path):
    """Remove a file from the index and working tree if it was newly created."""
    _assert_safe_path(path)
    git_unstage(path)
    if os.path.exists(path):
        # pi-lens-ignore: python-path-traversal
        os.remove(path)


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
    restore_all(TEST_FILES, git_restore)


def main():
    harness = StagedHarness()
    run_validator = harness.run_validator

    os.chdir(REPO_ROOT)
    print("Creating test files and staging them...\n")

    try:
        create_test_files()

        # ── Test 1: validators find issues in their relevant staged files ──

        print("Test: validators detect issues in staged files")
        print("-" * 60)

        run_validator(
            "validate_events.py",
            "events validator finds missing is_triggered_only",
            expect_issues=True,
            expected_path=os.path.basename(TEST_EVENT_FILE),
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
            expected_category="History files with missing technology prerequisites",
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
            git_unstage(path)
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

    return harness.summary()


# ── pytest entry points ─────────────────────────────────────────────────────
# Without a `test_*` function pytest collects this `*_test.py` module but finds
# zero tests. These wrap the script logic so `pytest` actually exercises it.


def _index_is_clean() -> bool:
    return not run_git(REPO_ROOT, "diff", "--cached", "--name-only").stdout.strip()


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
    require_staged_integration_enabled()
    if not _index_is_clean():
        raise SkipTest("git index has staged changes; skipping to avoid clobbering")
    if main() != 0:
        raise AssertionError("staged validator integration failed")


if __name__ == "__main__":
    sys.exit(main())
