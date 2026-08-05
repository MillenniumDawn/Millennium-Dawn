"""Scope gating for the validation report's PR-comment behaviour.

Deleting the report comment claims the PR is clean, so only a full run may do
it. A per-PR run gates each validator on the file groups the diff touches, and
a validator that did not run this time can still have live findings from an
earlier push.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from generate_validation_report import should_delete_comment  # noqa: E402
from report_lib import Issue, Severity, ValidatorRun  # noqa: E402


def _passed():
    return [ValidatorRun(name="events", title="Events", status="passed")]


def test_full_clean_run_deletes():
    assert should_delete_comment(_passed(), [], "full")


def test_partial_clean_run_never_deletes():
    assert not should_delete_comment(_passed(), [], "partial")


def test_findings_keep_the_comment():
    issue = Issue(
        severity=Severity.WARNING,
        category="missing-decision-log",
        message="no log line",
        file="common/decisions/x.txt",
        line=12,
        validator="decisions",
    )
    assert not should_delete_comment(_passed(), [issue], "full")


def test_warning_only_validator_keeps_the_comment():
    runs = [ValidatorRun(name="events", title="Events", status="warnings")]
    assert not should_delete_comment(runs, [], "full")


def test_no_validator_output_keeps_the_comment():
    assert not should_delete_comment([], [], "full")
