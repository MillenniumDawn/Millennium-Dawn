"""Shared runner for the opt-in staged-validator integration harnesses."""

import json
import os
import subprocess
import sys
import tempfile
import time

# Maximum seconds a staged validator should take in CI
MAX_TIME = 15.0
# This validator intentionally scans the full repository in staged mode.
TIME_BUDGETS = {"validate_scripted_localisation.py": 30.0}
# Hang guard only. It sits far above the budgets so a slow runner fails as TOO SLOW.
HANG_TIMEOUT = 300.0


def restore_all(paths, restore):
    """Restore every path before raising, so one failure cannot strand the rest."""
    failures = []
    for path in paths:
        try:
            restore(path)
        except (OSError, subprocess.SubprocessError) as exc:
            failures.append(f"{path}: {exc}")
    if failures:
        raise RuntimeError("cleanup failed:\n" + "\n".join(failures))


def read_result(returncode, json_path):
    """Return (issues, problem); problem is set when the run did not complete.

    Findings and a traceback both exit 1, so the result file decides which it was.
    """
    if returncode not in (0, 1):
        return [], f"unexpected exit code {returncode}"
    try:
        with open(json_path, encoding="utf-8") as handle:
            issues = json.load(handle)
    except (OSError, ValueError):
        return [], f"exit code {returncode} without a readable result file"
    has_errors = any(issue.get("severity") == "error" for issue in issues)
    if has_errors != (returncode == 1):
        return issues, f"exit code {returncode} disagrees with the result file"
    return issues, ""


def _matches(issue, category, path):
    if category and issue.get("category") != category:
        return False
    return not path or path in f"{issue.get('file')} {issue.get('message')}"


def check_validator(
    script, expect_issues=True, expected_path=None, expected_category=None
):
    """Run a validator with --staged; return (problems, status, output).

    expect_issues: True needs findings, False a clean pass, None accepts either.
    """
    with tempfile.TemporaryDirectory() as out_dir:
        cmd = [
            sys.executable,
            f"tools/validation/{script}",
            "--staged",
            "--strict",
            "--no-color",
            "--workers",
            "4",
            "--output",
            os.path.join(out_dir, "result.log"),
        ]
        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=HANG_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            return [f"TIMED OUT after {HANG_TIMEOUT:.0f}s"], "", ""
        elapsed = time.monotonic() - start
        issues, problem = read_result(
            result.returncode, os.path.join(out_dir, "result.json")
        )

    problems = []
    time_budget = TIME_BUDGETS.get(script, MAX_TIME)
    if elapsed > time_budget:
        problems.append(f"TOO SLOW ({elapsed:.1f}s > {time_budget}s)")
    if problem:
        problems.append(problem)
    elif expect_issues is True and result.returncode != 1:
        problems.append("expected findings but the run was clean")
    elif expect_issues is False and result.returncode != 0:
        problems.append(f"expected a clean pass but found {len(issues)} issue(s)")
    elif expect_issues and not any(
        _matches(issue, expected_category, expected_path) for issue in issues
    ):
        problems.append(
            f"no finding with category {expected_category!r} and path {expected_path!r}"
        )
    status = f"{elapsed:.2f}s, {len(issues)} issue(s)"
    return problems, status, (result.stdout or "") + (result.stderr or "")


class StagedHarness:
    """Runs staged validators and tallies the results for one harness."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_validator(self, script, label, **expectation):
        """Run a validator with --staged and check the result."""
        problems, status, output = check_validator(script, **expectation)
        if not problems:
            self.passed += 1
            print(f"  PASS  {label} [{status}]")
            return
        self.failed += 1
        msg = f"  FAIL  {label} [{', '.join(problems)}]"
        self.errors.append(msg)
        print(msg)
        for line in output.strip().split("\n")[-5:]:
            print(f"        {line}")

    def summary(self):
        """Print the tally and return the process exit code."""
        print()
        print("=" * 60)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        if self.errors:
            print("\nFailures:")
            for error in self.errors:
                print(error)
        print("=" * 60)
        return 1 if self.failed else 0
