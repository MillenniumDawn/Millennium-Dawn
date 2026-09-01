"""Tests for the auto-parser and structured ``_report`` paths in BaseValidator.

These tests verify the improvements shipped in Layer C3:
  * ``_parse_result_location`` extracts ``file`` and ``line`` from the common
    result string formats emitted across the 13 validators.
  * ``_report`` accepts legacy strings, (message, file, line) tuples, and
    ``Issue`` instances, populating ``self._issues`` consistently.
"""

import tempfile

from validator_common import BaseValidator, Issue, Severity


class _DummyValidator(BaseValidator):
    """Minimal subclass so we can instantiate BaseValidator in tests."""

    TITLE = "DUMMY"

    def run_validations(self):
        pass


def _make_validator() -> _DummyValidator:
    with tempfile.TemporaryDirectory() as td:
        v = _DummyValidator(mod_path=td, use_colors=False)
    return v


# ---------------------------------------------------------------------------
# _parse_result_location
# ---------------------------------------------------------------------------


def test_parse_colon_form():
    msg, file, line = BaseValidator._parse_result_location(
        "events/foo.txt:42 - something broken"
    )
    assert file == "events/foo.txt"
    assert line == 42
    assert msg == "something broken"


def test_parse_colon_colon_form():
    msg, file, line = BaseValidator._parse_result_location(
        "common/decisions/bar.txt:7: another issue"
    )
    assert file == "common/decisions/bar.txt"
    assert line == 7
    assert msg == "another issue"


def test_parse_dash_line_form():
    msg, file, line = BaseValidator._parse_result_location(
        "bar.txt - line 12 - unpaired bracket"
    )
    assert file == "bar.txt"
    assert line == 12
    assert msg == "unpaired bracket"


def test_parse_comma_line_form():
    msg, file, line = BaseValidator._parse_result_location(
        "baz.txt, line 99, colors - odd number of § symbols"
    )
    assert file == "baz.txt"
    assert line == 99
    assert "colors" in msg


def test_parse_id_file_desc_form():
    msg, file, line = BaseValidator._parse_result_location(
        "some_event.1 - Turkey.txt - invalid desc"
    )
    assert file == "Turkey.txt"
    assert line == 0
    assert "some_event.1" in msg
    assert "invalid desc" in msg


def test_parse_unknown_format_returns_as_message():
    msg, file, line = BaseValidator._parse_result_location(
        "free-form message with no path"
    )
    assert file == ""
    assert line == 0
    assert msg == "free-form message with no path"


# ---------------------------------------------------------------------------
# _report input shapes
# ---------------------------------------------------------------------------


def test_report_accepts_legacy_strings_and_parses_location():
    v = _make_validator()
    v._report(
        ["events/foo.txt:42 - something"],
        ok_msg="OK",
        fail_msg="Found issues:",
        severity=Severity.ERROR,
        category="events",
    )
    assert v.errors_found == 1
    assert len(v._issues) == 1
    issue = v._issues[0]
    assert issue.file == "events/foo.txt"
    assert issue.line == 42
    assert issue.message == "something"
    assert issue.category == "events"
    assert issue.severity == Severity.ERROR


def test_report_accepts_tuples():
    v = _make_validator()
    v._report(
        [("flag_not_set", "common/file.txt", 15)],
        ok_msg="OK",
        fail_msg="Found issues:",
        severity=Severity.WARNING,
        category="variables",
    )
    assert v.warnings_found == 1
    issue = v._issues[0]
    assert issue.file == "common/file.txt"
    assert issue.line == 15
    assert issue.message == "flag_not_set"
    assert issue.severity == Severity.WARNING


def test_report_accepts_issue_instances():
    v = _make_validator()
    pre_built = Issue(
        severity=Severity.ERROR,
        category="custom",
        message="prebuilt message",
        file="a.txt",
        line=3,
    )
    v._report(
        [pre_built],
        ok_msg="OK",
        fail_msg="Found issues:",
        severity=Severity.ERROR,
        category="custom",
    )
    assert len(v._issues) == 1
    assert v._issues[0] is pre_built


def test_report_empty_list_records_nothing():
    v = _make_validator()
    v._report(
        [],
        ok_msg="All clear",
        fail_msg="Found issues:",
        severity=Severity.ERROR,
        category="events",
    )
    assert v.errors_found == 0
    assert v.warnings_found == 0
    assert v._issues == []


def test_report_mixed_input_shapes():
    v = _make_validator()
    results = [
        "events/a.txt:1 - A",
        ("B", "events/b.txt", 2),
        Issue(
            severity=Severity.ERROR,
            category="x",
            message="C",
            file="events/c.txt",
            line=3,
        ),
    ]
    v._report(
        results,
        ok_msg="OK",
        fail_msg="Found issues:",
        severity=Severity.ERROR,
        category="mixed",
    )
    assert v.errors_found == 3
    assert len(v._issues) == 3
    # All three preserved their file/line
    for issue, expected in zip(
        v._issues, [("events/a.txt", 1), ("events/b.txt", 2), ("events/c.txt", 3)]
    ):
        assert issue.file == expected[0]
        assert issue.line == expected[1]


def test_report_persists_issues_without_category():
    """Every finding is stored, and a missing category falls back to the
    (cleaned) fail_msg so the grouped end-of-run report has a sensible label.

    Issues must reach the JSON sidecar (and the CI report built from it) even
    when the caller omits a category — otherwise a _report call would fail the
    build (errors_found increments) while contributing nothing to the report.
    """
    v = _make_validator()
    v._report(
        ["some.txt:1 - issue"],
        ok_msg="OK",
        fail_msg="Found issues:",
        severity=Severity.ERROR,
    )
    assert v.errors_found == 1
    assert len(v._issues) == 1
    # No explicit category → grouped under the cleaned fail_msg label.
    assert v._issues[0].category == "Found issues"


def test_render_issues_caps_per_category():
    """The console render caps each category and notes the overflow; the
    full list stays in ``_issues`` for the JSON sidecar."""
    v = _make_validator()
    cap = v.MAX_RENDERED_PER_CATEGORY
    for i in range(cap + 7):
        v.add_warning("big-category", f"finding {i}", file="a.txt", line=i + 1)
    v._render_issues()
    rendered = [ln for ln in v.output_lines if " - finding " in ln]
    assert len(rendered) == cap
    assert any("and 7 more" in ln for ln in v.output_lines)
    assert len(v._issues) == cap + 7


def test_render_issues_emits_parseable_lines():
    """Rendered lines keep the two-space ``file:line - message`` shape that
    report_lib's text-fallback parser (loader._LOG_ISSUE_RE) matches."""
    v = _make_validator()
    v.add_error("cat", "broken thing", file="events/x.txt", line=12)
    v._render_issues()
    assert "  events/x.txt:12 - broken thing" in v.output_lines
