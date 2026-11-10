"""Regression tests for `BaseValidator._report`."""

import pytest
from validator_common import BaseValidator, Issue, Severity


class _DummyValidator(BaseValidator):
    TITLE = "DUMMY"

    def run_validations(self):
        pass


@pytest.fixture
def dummy_validator(tmp_path):
    """Validator backed by a real on-disk temp directory that survives the test."""
    return _DummyValidator(mod_path=str(tmp_path), use_colors=False)


# ---------------------------------------------------------------------------
# _report with Issue instances that have category but no severity override
# (smoke test that the mixed-inputs fix didn't regress other paths)
# ---------------------------------------------------------------------------


def test_report_issue_with_category_and_severity(dummy_validator):
    """Pre-built Issue with both category and severity must be stored unchanged."""
    v = dummy_validator
    pre_built = Issue(
        severity=Severity.WARNING,
        category="custom",
        message="prebuilt warning",
        file="a.txt",
        line=3,
    )
    v._report(
        [pre_built],
        ok_msg="OK",
        fail_msg="Found issues:",
        severity=Severity.ERROR,  # should NOT override pre-built severity
        category="custom",
    )
    assert len(v._issues) == 1
    assert v._issues[0].severity == Severity.WARNING  # pre-built preserved
    assert v._issues[0].category == "custom"
    # Counter must reflect the Issue's own severity, not the call's severity arg.
    assert v.warnings_found == 1
    assert v.errors_found == 0


def test_report_normalizes_windows_file_separators(dummy_validator):
    dummy_validator._report(
        [("finding", r"common\national_focus\foo.txt", 3)],
        ok_msg="OK",
        fail_msg="Findings:",
    )

    assert dummy_validator._issues[0].file == "common/national_focus/foo.txt"


def test_report_does_not_mutate_prebuilt_issue(dummy_validator):
    source = Issue(
        severity=Severity.WARNING,
        category="",
        message="finding",
        file=r"common\decisions\foo.txt",
        line=3,
    )

    dummy_validator._report([source], ok_msg="OK", fail_msg="Findings:")

    assert source.category == ""
    assert source.file == r"common\decisions\foo.txt"
    assert dummy_validator._issues[0].category == "Findings"
    assert dummy_validator._issues[0].file == "common/decisions/foo.txt"


def test_report_counts_mixed_severities_correctly(dummy_validator):
    """When _report receives a mix of pre-built Issues and tuples, each entry
    must increment the counter matching its own severity."""
    v = dummy_validator
    inputs = [
        Issue(
            severity=Severity.WARNING,
            category="c",
            message="prebuilt warning",
            file="a.txt",
            line=1,
        ),
        Issue(
            severity=Severity.ERROR,
            category="c",
            message="prebuilt error",
            file="b.txt",
            line=2,
        ),
        ("tuple-form result", "c.txt", 3),  # inherits the call's severity
    ]
    v._report(
        inputs,
        ok_msg="OK",
        fail_msg="Found issues:",
        severity=Severity.ERROR,
        category="c",
    )
    assert v.errors_found == 2  # one pre-built ERROR + one tuple
    assert v.warnings_found == 1  # the pre-built WARNING
