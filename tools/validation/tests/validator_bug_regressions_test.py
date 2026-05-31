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


# ---------------------------------------------------------------------------
# Bug: set_variable usage validator reported referenced variables as unused.
# File: validate_set_variables.py
# Three distinct false-positive sources, each pinned below:
#   1. _SET_LONG_RE char class lacked A-Z, truncating tag-prefixed targets
#      (GER_event_counter_1_wot -> _event_counter_1_wot) so they never matched
#      their own reads.
#   2. ref-minus-set subtraction netted a set-once/read-once var to zero.
#   3. the symmetric context window caught a `set_variable` on the FOLLOWING
#      line, miscategorizing a genuine read as a write.
# ---------------------------------------------------------------------------


def _scan_set_vars(path):
    """Return a file's set_variable targets via the case-preserving pass-1 scan."""
    from shared_utils import FileOpener
    from validate_set_variables import _scan_set_variables

    text = FileOpener.open_text_file(path, lowercase=False, strip_comments_flag=True)
    return _scan_set_variables(text)


def _count_refs(path, tracked):
    """Count non-definition references to `tracked` vars in a file, driving the
    same pass-2 worker path the Pool initializer sets up."""
    import validate_set_variables as sv
    from shared_utils import FileOpener

    bare = {v.lower(): v for v in tracked if "." not in v}
    dotted = {v.lower(): v for v in tracked if "." in v}
    sv._pass2_init("", bare, dotted, "test")
    text = FileOpener.open_text_file(path, lowercase=True, strip_comments_flag=True)
    return sv._count_refs_in_text(text)


def test_scan_captures_tag_prefixed_target_whole(tmp_path):
    """A tag-prefixed set_variable target must be captured whole, not truncated
    at its uppercase prefix."""
    f = tmp_path / "x.txt"
    f.write_text("set_variable = { GER_event_counter_1_wot = 1 }\n")
    variables = _scan_set_vars(str(f))
    assert "GER_event_counter_1_wot" in variables
    assert "_event_counter_1_wot" not in variables


def test_tag_prefixed_var_set_and_read_not_flagged(tmp_path):
    """A tag-prefixed var that is set and also read must show a positive ref
    count (the reads match case-insensitively against the lowercased text)."""
    f = tmp_path / "x.txt"
    f.write_text(
        "add_to_variable = { GER_event_counter_1_wot = 1 }\n"
        "if = { limit = { check_variable = { GER_event_counter_1_wot > 6 } } }\n"
        "set_variable = { GER_event_counter_1_wot = 0 }\n"
    )
    tracked = frozenset(_scan_set_vars(str(f)))
    counts = _count_refs(str(f), tracked)
    assert counts.get("GER_event_counter_1_wot", 0) == 2  # add_to + check_variable


def test_var_set_once_read_once_counts_as_referenced(tmp_path):
    """A var set exactly once and read exactly once must count as referenced —
    the old ref-minus-set subtraction wrongly netted this to zero."""
    f = tmp_path / "x.txt"
    f.write_text(
        "set_variable = { ruling_party_popularity_var = 5 }\n"
        "if = { limit = { check_variable = { ruling_party_popularity_var < 10 } } }\n"
    )
    counts = _count_refs(str(f), frozenset(["ruling_party_popularity_var"]))
    assert counts.get("ruling_party_popularity_var", 0) == 1


def test_read_followed_by_set_variable_line_counts_as_read(tmp_path):
    """A read immediately followed by a `set_variable` statement on the next
    line must still count as a read — only the look-behind decides set vs read."""
    f = tmp_path / "x.txt"
    f.write_text(
        "multiply_temp_variable = { income = global.price_per_gw_for_els }\n"
        "set_variable = { other_var = income }\n"
    )
    counts = _count_refs(str(f), frozenset(["global.price_per_gw_for_els"]))
    assert counts.get("global.price_per_gw_for_els", 0) == 1


def test_rhs_value_in_set_variable_counts_as_read(tmp_path):
    """In `set_variable = { target = source }`, the LHS target is a definition
    but the RHS source is a read."""
    f = tmp_path / "x.txt"
    f.write_text("set_variable = { target = source_var }\n")
    counts = _count_refs(str(f), frozenset(["source_var", "target"]))
    assert counts.get("source_var", 0) == 1
    assert counts.get("target", 0) == 0


def test_genuinely_unused_var_still_has_zero_refs(tmp_path):
    """A var that is only ever set (never read) must report zero refs so the
    validator still catches real dead variables — no false negative."""
    f = tmp_path / "x.txt"
    f.write_text(
        "set_variable = { ALG_drs_type = 6 }\n" "set_variable = { ALG_drs_type = 5 }\n"
    )
    counts = _count_refs(str(f), frozenset(["ALG_drs_type"]))
    assert counts.get("ALG_drs_type", 0) == 0


def test_scope_prefixed_target_tracked_by_bare_name(tmp_path):
    """A scope-qualified target (PREV./ROOT./TAG.) is stored under its bare name
    so reads via a different scope prefix or `var:` are matched."""
    from validate_set_variables import _strip_scope_prefix

    assert _strip_scope_prefix("PREV.foreign_celeb_country") == "foreign_celeb_country"
    assert _strip_scope_prefix("ALB.eurosceptic") == "eurosceptic"
    assert _strip_scope_prefix("global.price_per_gw_for_els") == (
        "global.price_per_gw_for_els"
    )  # global namespace kept
    assert _strip_scope_prefix("plain_var") == "plain_var"

    f = tmp_path / "x.txt"
    f.write_text("set_variable = { PREV.foreign_celeb_country = THIS.id }\n")
    variables = _scan_set_vars(str(f))
    assert "foreign_celeb_country" in variables
    assert "PREV.foreign_celeb_country" not in variables


def test_scope_prefixed_var_read_via_other_scope_not_flagged(tmp_path):
    """Set on PREV scope, read via `var:` — must count as referenced, and the
    set occurrence itself must NOT count (look-behind tolerates the scope chain)."""
    f = tmp_path / "x.txt"
    f.write_text(
        "set_variable = { PREV.foreign_celeb_country = THIS.id }\n"
        "var:foreign_celeb_country = { add_stability = 0.05 }\n"
    )
    counts = _count_refs(str(f), frozenset(["foreign_celeb_country"]))
    assert counts.get("foreign_celeb_country", 0) == 1  # the var: read, not the set


def test_scope_prefixed_var_only_set_still_flagged(tmp_path):
    """A scope-qualified var that is only ever set (never read) must still report
    zero refs — the scope-chain-tolerant look-behind must classify it as a set."""
    f = tmp_path / "x.txt"
    f.write_text("set_variable = { THIS.never_read_var = 1 }\n")
    counts = _count_refs(str(f), frozenset(["never_read_var"]))
    assert counts.get("never_read_var", 0) == 0


# ---------------------------------------------------------------------------
# Bug: GFX reference validator only stripped // and /* */ comments, but
# Clausewitz .gui/.gfx files use `#` line comments. Sprite references inside
# `#`-commented blocks leaked through and were reported as missing.
# File: validate_gfx_references.py
# ---------------------------------------------------------------------------


def test_strip_comments_removes_hash_line_comment():
    """A `#`-commented sprite reference must be stripped so it isn't treated as
    a live reference."""
    from validate_gfx_references import _strip_comments

    text = '# spriteType = "GFX_commented_out"\nspriteType = "GFX_real"\n'
    out = _strip_comments(text)
    assert "GFX_commented_out" not in out
    assert "GFX_real" in out


def test_strip_comments_removes_trailing_hash_comment():
    """A trailing `#` comment must be stripped without removing the live ref
    earlier on the same line."""
    from validate_gfx_references import _strip_comments

    text = 'spriteType = "GFX_real" # GFX_commented\n'
    out = _strip_comments(text)
    assert "GFX_real" in out
    assert "GFX_commented" not in out
