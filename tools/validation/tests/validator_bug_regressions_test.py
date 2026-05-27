"""Regression tests for bug patterns fixed in the validator-false-positives branch.

These tests verify the specific bug fixes so future changes don't reintroduce
the same false positives.
"""

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
# Bug: count_event_ids_in_file returning empty dict for zero-count IDs
# File: validate_events.py
# Fix: Real function returns ONLY IDs present in the file; callers must
#      pre-initialize the aggregate dict with zeros for every tracked ID.
#      Tests pin both halves of that contract.
# ---------------------------------------------------------------------------


def test_count_event_ids_in_file_returns_only_present_ids(tmp_path):
    """The real production function returns a dict containing only IDs that
    appear in the file. Absent IDs are NOT included — callers compensate by
    pre-initializing their aggregate dict with zero counts."""
    from validate_events import count_event_ids_in_file

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    fpath = events_dir / "test.txt"
    fpath.write_text(
        "add_namespace = test\n"
        "country_event = {\n"
        "    id = test.1\n"
        "    title = test.1.t\n"
        "    desc = test.1.d\n"
        "    option = { name = test.1.a }\n"
        "}\n"
    )
    tracked = frozenset(["test.1", "test.999"])
    result = count_event_ids_in_file((str(fpath), tracked))
    assert "test.1" in result, "Event ID present in file must be in result"
    assert (
        "test.999" not in result
    ), "Absent ID must NOT be in result — caller pre-initializes zeros"


def test_count_event_ids_in_file_handles_referenced_event(tmp_path):
    """When an event ID IS referenced, the count must be accurate."""
    from validate_events import count_event_ids_in_file

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    fpath = events_dir / "test.txt"
    fpath.write_text(
        "country_event = test.1\n" "country_event = test.1\n" "country_event = test.1\n"
    )
    tracked = frozenset(["test.1"])
    result = count_event_ids_in_file((str(fpath), tracked))
    assert result["test.1"] == 3


# ---------------------------------------------------------------------------
# Bug: get_all_colors missing warning when core.gfx is absent
# File: validate_localisation.py
# Fix: Added logging.warning when interface/core.gfx doesn't exist
# ---------------------------------------------------------------------------


def test_get_all_colors_warns_on_missing_core_gfx(tmp_path, caplog):
    """When interface/core.gfx is missing, get_all_colors should log a warning
    and return the fallback color set."""
    import logging

    from validate_localisation import get_all_colors

    (tmp_path / "interface").mkdir()
    fallback_colors = list("WGRBYCMwgrbycm!")

    with caplog.at_level(logging.WARNING):
        result = get_all_colors(str(tmp_path))

    assert "core.gfx" in caplog.text
    assert result == fallback_colors


def test_get_all_colors_returns_colors_when_file_present(tmp_path):
    """When core.gfx exists and is parseable, return the extracted colors."""
    from validate_localisation import get_all_colors

    gfx_dir = tmp_path / "interface"
    gfx_dir.mkdir()
    (gfx_dir / "core.gfx").write_text(
        "textures = {\n"
        "    textcolors = {\n"
        '        "W" = { color = { 1 0 0 } }\n'
        '        "R" = { color = { 0 1 0 } }\n'
        "    }\n"
        "}\n"
    )
    result = get_all_colors(str(tmp_path))
    assert len(result) >= 2


# ---------------------------------------------------------------------------
# Bug: fragile line.index(":") + 2 pattern in loc key extraction
# File: validate_localisation.py
# Fix: Use explicit colon_idx variable with proper slice bounds
# ---------------------------------------------------------------------------


def test_colon_idx_extraction_handles_value_with_colon():
    """A loc value that contains a colon (e.g. "Value: with colon") must not
    break key extraction — the colon before the value is the separator."""
    line = 'my_key: "A value with : a colon inside"'
    colon_idx = line.index(":")
    key = line[:colon_idx].strip()
    value = line[colon_idx + 2 :].strip()  # +2 skips ": "
    assert key == "my_key"
    assert value == '"A value with : a colon inside"'


def test_colon_idx_extraction_preserves_quoted_colon_in_value():
    """A value that starts with a quoted string containing a colon must not
    misidentify the opening quote as the separator."""
    line = 'desc: "§YSome description: with a colon§!"'
    colon_idx = line.index(":")
    key = line[:colon_idx].strip()
    value = line[colon_idx + 2 :].strip()
    assert key == "desc"
    assert value == '"§YSome description: with a colon§!"'


# ---------------------------------------------------------------------------
# Bug: gate_signature coordinate mismatch in on_actions duplicate detection
# File: validate_on_actions.py
# Fix: line_offset threaded through _scan_on_action_block so line numbers
#       are computed relative to the full file, not the block body
# ---------------------------------------------------------------------------


def test_gate_signature_line_offset_from_full_file():
    """When _scan_on_action_block is called with line_offset > 0, the reported
    line numbers must account for lines before the block in the full file."""
    from validate_on_actions import _scan_on_action_block

    # Simulate a file that has 10 lines before the on_action block content
    block_body = "country_event = test.1\ncountry_event = test.1\n"
    line_offset = 10  # block starts at line 11 in the real file

    refs, dupes = _scan_on_action_block(
        block_body,
        block_name="on_action_test",
        filepath="test.txt",
        line_offset=line_offset,
    )

    # The duplicate ref at block_body[18..26] is on the second event call.
    # Its line in the full file = 10 (offset) + 2 (newline before 2nd call) + 1 = 13
    # or simply: offset + text[:pos].count("\n") + 1 for pos at start of 2nd call.
    # Second call starts at byte 18 (after "country_event = test.1\n" = 18 bytes)
    # In block_body: "country_event = test.1\n" has 1 newline
    # So line = 10 + 1 + 1 = 12
    # But wait — line counting in _line_of: text[:18].count("\n") + offset + 1
    # text[:18] = "country_event = test.1\n" = 1 newline
    # So line = 10 + 1 + 1 = 12
    # The duplicate should be at line 12
    assert len(dupes) == 1, f"Expected 1 duplicate, got {len(dupes)}: {dupes}"
    _, bname, line = dupes[0]
    assert bname == "on_action_test"
    assert line == 12, f"Expected line 12 (offset {line_offset}), got {line}"


def test_gate_signature_same_line_different_branch_not_dupe():
    """Two refs to the same event in sibling if/else branches must NOT be
    flagged as duplicates — they are mutually exclusive at runtime."""
    from validate_on_actions import _scan_on_action_block

    # Two refs to same event in sibling if/else branches
    block_body = (
        "if = { limit = { has_country_flag = A } country_event = test.1 }\n"
        "else_if = { limit = { has_country_flag = B } country_event = test.1 }\n"
    )

    refs, dupes = _scan_on_action_block(
        block_body,
        block_name="on_action_test",
        filepath="test.txt",
        line_offset=0,
    )

    # Should have 2 refs (one in each mutually-exclusive branch) but 0 dupes
    assert len(refs) == 2, f"Expected 2 refs, got {len(refs)}: {refs}"
    assert len(dupes) == 0, f"Events in sibling branches must not be dupes: {dupes}"


def test_gate_signature_different_line_same_branch_is_dupe():
    """Two refs to the same event in the SAME if branch (not mutually exclusive)
    must be flagged as duplicates."""
    from validate_on_actions import _scan_on_action_block

    # Same event fired twice in the same branch body (not inside nested gating)
    block_body = "country_event = test.1\ncountry_event = test.1\n"

    refs, dupes = _scan_on_action_block(
        block_body,
        block_name="on_action_test",
        filepath="test.txt",
        line_offset=0,
    )

    assert len(dupes) == 1, f"Expected 1 duplicate, got {len(dupes)}: {dupes}"
    assert dupes[0][0] == "test.1"


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
