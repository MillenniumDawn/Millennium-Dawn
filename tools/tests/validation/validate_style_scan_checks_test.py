"""Tests for `validate_style.py` brace, indent, spacing and quote checks.

Each check is a pure text scan returning `[(message, line)]`, so the fixtures
here are single-purpose snippets: one deliberate defect per case, plus the
comment/string-aware negatives that keep the scans from firing on valid script.
"""

import validate_style as V


def _braces(text):
    return V._check_brace_matching(text, "common/x.txt")


def _indent(text):
    return V._check_indent_and_brackets(text, "common/x.txt")


def _spacing(text):
    return V._check_spacing_and_quotes(text, "common/x.txt")


def _focus(text):
    return V._check_focus_standards(text, "common/national_focus/x.txt")


# ---------------------------------------------------------------------------
# Brace matching (ERROR)
# ---------------------------------------------------------------------------


def test_unclosed_opening_brace_reported_at_its_own_line():
    assert _braces("a = {\n\tb = 1\n") == [
        ("Opening brace '{' without matching closing brace", 1)
    ]


def test_closing_brace_without_opener_reported():
    assert _braces("a = 1\n}\n") == [
        ("Closing brace '}' without matching opening brace", 2)
    ]


def test_braces_inside_a_quoted_string_are_not_counted():
    assert _braces('log = "a { b } c"\na = { b = 1 }\n') == []


def test_braces_inside_a_comment_are_not_counted():
    assert _braces("# a = {\na = { b = 1 }\n") == []


def test_quote_inside_a_comment_does_not_open_a_string():
    """An unpaired `"` in a comment used to swallow the rest of the file."""
    assert _braces("# it's \"quoted\na = { b = 1 }\n") == []


# ---------------------------------------------------------------------------
# Indent and bracket balance (ERROR)
# ---------------------------------------------------------------------------


def test_four_space_indent_flagged():
    assert _indent("    a = 1\n") == [("4-space indent detected (use tab)", 1)]


def test_tab_indent_clean():
    assert _indent("\ta = 1\n") == []


def test_inline_alignment_spaces_are_not_an_indent():
    assert _indent("\ta = 1    }\n") == []


def test_unbalanced_square_brackets_reported():
    assert _indent("\ta = [GetName\n") == [
        ("Unbalanced square brackets: [ = 1, ] = 0", 0)
    ]


def test_unbalanced_round_brackets_reported():
    assert _indent("\ta = (1\n") == [("Unbalanced round brackets: ( = 1, ) = 0", 0)]


def test_balanced_brackets_clean():
    assert _indent("\ta = (1) [2]\n") == []


def test_brackets_in_a_comment_are_ignored():
    assert _indent("\t# a = ( [    x\n") == []


def test_brackets_and_indent_inside_a_string_are_ignored():
    assert _indent('\tlog = "(    ["\n') == []


# ---------------------------------------------------------------------------
# Spacing and quotes (WARNING)
# ---------------------------------------------------------------------------


def test_comment_line_is_skipped_entirely():
    assert _spacing('#a={ "\n') == []


def test_missing_space_after_open_brace_flagged():
    assert _spacing("\tfocus = {x = 1 }\n") == [
        ("Missing space before or after open brace", 1)
    ]


def test_missing_space_before_close_brace_flagged():
    assert _spacing("\tset_variable = { x = 1}\n") == [
        ("Missing space before or after close brace", 1)
    ]


def test_braces_in_a_trailing_comment_are_not_spacing_checked():
    assert _spacing("\ta = 1 # {x}\n") == []


def test_empty_brace_pair_is_idiomatic():
    assert _spacing("\ttopbar_empty = {}\n") == []


def test_odd_quote_count_flagged():
    assert _spacing('\tlog = "unterminated\n') == [("Odd number of quotation marks", 1)]


def test_balanced_quotes_not_flagged():
    assert _spacing('\tlog = "balanced"\n') == []


def test_odd_quote_inside_a_comment_not_flagged():
    assert _spacing('\ta = 1 # "note\n') == []


def test_double_space_around_equals_flagged():
    assert _spacing("\ta  = 1\n") == [
        ("Two spaces before or after '='", 1),
        ("Missing space before or after '='", 1),
    ]


def test_missing_space_around_equals_flagged():
    assert _spacing("\ta=1\n") == [("Missing space before or after '='", 1)]


def test_running_brace_depth_going_negative_flagged():
    assert _spacing("}\n") == [("Running brace depth went negative", 1)]


# ---------------------------------------------------------------------------
# Focus ID standards (WARNING)
# ---------------------------------------------------------------------------


FOCUS_TREE = """focus_tree = {
\tid = test_tree

\t# a comment line
\tfocus = {
\t\tset_variable = { grid_id = 4 }
\t\tid = FOCUS_ID
\t}
}
"""


def test_malformed_focus_id_flagged():
    """`grid_id =` on the line above contains `id =` but is not the ID line."""
    assert _focus(FOCUS_TREE.replace("FOCUS_ID", "badid")) == [
        ("Focus ID badid must be TAG_focus_name", 7)
    ]


def test_tag_prefixed_focus_id_clean():
    assert _focus(FOCUS_TREE.replace("FOCUS_ID", "GER_focus_a")) == []


def test_focus_block_without_an_id_line_is_clean():
    text = "focus_tree = {\n\tfocus = {\n\t\tx = 0\n\t}\n}\n"
    assert _focus(text) == []


# ---------------------------------------------------------------------------
# Event option logs (WARNING) — news events and quoted option names
# ---------------------------------------------------------------------------


NEWS_AND_COUNTRY = """news_event = {
\tid = news.1
\tmajor = yes

\toption = {
\t\tname = news.1.a
\t\tadd_political_power = 50
\t}
}

country_event = {
\tid = foo.1
\toption = {
\t\tname = foo.1.a
\t\tadd_political_power = 50
\t}
}
"""


def test_news_event_options_are_exempt_from_the_log_rule():
    findings = V._check_event_log_standards(NEWS_AND_COUNTRY, "events/Test.txt")
    assert findings == [("Event option foo.1.a has effects but no log", 13)]


def test_quoted_option_name_is_not_matched():
    text = 'option = {\n\tname = "foo.1.a"\n\tadd_political_power = 50\n}\n'
    assert V._check_event_log_standards(text, "events/Test.txt") == []


# ---------------------------------------------------------------------------
# Dispatch and severity wiring
# ---------------------------------------------------------------------------


def test_scan_file_runs_the_event_check_only_for_event_files():
    text = "option = {\n\tname = foo.1.a\n\tadd_political_power = 50\n}\n"
    assert V._scan_file(text, "/mod/events/Test.txt") == [
        ("Event option foo.1.a has effects but no log", 1)
    ]
    assert V._scan_file(text, "/mod/common/decisions/Test.txt") == []


def test_scan_file_runs_the_focus_check_only_for_focus_files():
    text = FOCUS_TREE.replace("FOCUS_ID", "badid")
    assert V._scan_file(text, "/mod/common/national_focus/x.txt") == [
        ("Focus ID badid must be TAG_focus_name", 7)
    ]
    assert V._scan_file(text, "/mod/common/decisions/x.txt") == []


def test_run_validations_splits_errors_from_warnings(tmp_path, write_path):
    write_path(
        tmp_path,
        "events/Test.txt",
        "option = {\n\tname = foo.1.a\n\tadd_political_power=50\n}\n",
    )
    write_path(tmp_path, "common/broken.txt", "a = {\n")

    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.run_validations()

    categories = {i.category for i in v._issues}
    assert "brace-matching" in categories
    assert "event-log" in categories
    assert "spacing" in categories
    assert v.errors_found == 1
    assert v.warnings_found == 2


def test_run_validations_scans_music_files(tmp_path, write_path):
    write_path(tmp_path, "music/broken.txt", "a = {\n")

    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.run_validations()

    categories = {i.category for i in v._issues}
    assert "brace-matching" in categories
    assert v.errors_found == 1
