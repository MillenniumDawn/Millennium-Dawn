#!/usr/bin/env python3
"""
Test staged validators against REAL mod files that have known issues.

Stages actual codebase files with temporary deliberate issues, runs each
validator with --staged, and verifies they find the expected issues.

Usage:
    MD_RUN_STAGED_INTEGRATION=1 python -m pytest tools/tests/staged_validators_real_test.py
"""

import os
import sys
from unittest import SkipTest

from _staged_integration_gate import require_staged_integration_enabled
from shared.paths import REPO_ROOT
from shared.staged_harness import StagedHarness, restore_all
from shared.suite import run_git

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


def stage_file_as_modified(path, suffix, staged_files):
    """Append a temporary issue and stage the file for a real validator run."""
    if ".." in path or os.path.isabs(path) or path not in _TOUCHED_FILES:
        raise ValueError(f"unsafe real path: {path}")
    # Recorded before the write, so a failed stage still gets restored.
    staged_files.append(path)
    # pi-lens-ignore: python-path-traversal
    with open(path, "a", encoding="utf-8-sig") as f:
        f.write(suffix)
    # pi-lens-ignore: python-path-traversal
    run_git(REPO_ROOT, "add", path)


def unstage_file(path):
    """Unstage a file and restore its working tree state."""
    run_git(REPO_ROOT, "reset", "HEAD", path)
    run_git(REPO_ROOT, "checkout", "--", path)


def main():
    harness = StagedHarness()
    run_validator = harness.run_validator

    os.chdir(REPO_ROOT)
    staged_files = []

    def stage(path, suffix="\n"):
        stage_file_as_modified(path, suffix, staged_files)

    def cleanup():
        restore_all(staged_files, unstage_file)
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
            expected_path="Event Horizon.txt",
            expected_category="missing-triggered-only",
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
            expected_path="MD_focus_ALG_l_english.yml",
            expected_category="Unpaired brackets found in localisation",
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
            expected_path="Event Horizon.txt",
            expected_category="missing-triggered-only",
        )
        run_validator(
            "validate_localisation.py",
            "localisation: multiple files staged (only loc checked)",
            expect_issues=True,
            expected_path="MD_focus_ALG_l_english.yml",
            expected_category="Unpaired brackets found in localisation",
        )
        cleanup()

    except Exception as exc:
        print(f"\nERROR: {exc}")
        harness.failed += 1
    finally:
        cleanup()

    return harness.summary()


# ── pytest entry points ─────────────────────────────────────────────────────
# Without a `test_*` function pytest collects this `*_test.py` module but finds
# zero tests. These wrap the script logic so `pytest` actually exercises it.

_TOUCHED_FILES = (
    "events/Event Horizon.txt",
    "localisation/english/MD_focus_ALG_l_english.yml",
    "common/national_focus/05_algeria.txt",
)


def _touched_files_clean() -> bool:
    status = run_git(REPO_ROOT, "status", "--porcelain", "--", *_TOUCHED_FILES)
    return not status.stdout.strip()


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
        rel_path = os.path.join(REPO_ROOT, rel)
        if not os.path.exists(rel_path):
            raise AssertionError(f"missing touched file: {rel_path}")


def test_staged_validators_real():
    """Integration run; stages/restores real files, so they must be clean first.

    Opt-in (MD_RUN_STAGED_INTEGRATION=1): it mutates the working repo and runs
    the full validator set, so it stays out of the default `pytest` sweep."""
    require_staged_integration_enabled()
    if not _touched_files_clean():
        raise SkipTest("target files have local changes; skipping to avoid clobbering")
    if main() != 0:
        raise AssertionError("staged validator real integration failed")


if __name__ == "__main__":
    sys.exit(main())
