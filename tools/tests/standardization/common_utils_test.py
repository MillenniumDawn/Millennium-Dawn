"""Tests for common_utils: the brace helpers, the block formatters, and the
read, write, backup and CLI plumbing every standardizer shares.

`strip_idea_allowed_gates.py` and `strip_dynmod_tag_gates.py` both slice around
a block by column and both track their nesting with the same stack, so a
regression here silently corrupts whichever file the next sweep touches.
"""

import argparse

import pytest
from common_utils import (
    BaseStandardizer,
    apply_brace_stack,
    block_has_log,
    code_of_line,
    collapse_blank_gap,
    collapse_blank_runs,
    compact_icon,
    compact_search_filters,
    emit_comments,
    find_block_span,
    inject_log_after_brace,
    join_groups,
    read_lines_for_standardization,
    resolve_output_file_and_backup,
    run_standardizer,
    write_standardized_output,
)
from shared.suite import read_text as _read
from shared.suite import write_text as _write


def test_span_stops_at_the_first_closer_on_a_shared_line():
    # `} }` is the whole reason this returns a column: a depth counter that
    # stops at "reached zero" cannot tell the two apart.
    lines = ["\tallowed = { original_tag = FOO } }"]
    assert find_block_span(lines, 0, 11) == (0, 32)


def test_span_crosses_lines():
    lines = ["\tallowed = {", "\t\tOR = { a = b }", "\t}", "\tpicture = x"]
    assert find_block_span(lines, 0, 11) == (2, 1)


def test_span_ignores_a_brace_in_a_comment():
    lines = ["\tallowed = { # }", "\t\ta = b", "\t}"]
    assert find_block_span(lines, 0, 11) == (2, 1)


def test_unbalanced_span_is_none():
    assert find_block_span(["\tallowed = {", "\t\ta = b"], 0, 11) is None


def test_stack_names_each_level():
    stack = []
    apply_brace_stack(code_of_line("ideas = {"), stack)
    assert stack == ["ideas"]
    apply_brace_stack(code_of_line("\tcountry = {"), stack)
    assert stack == ["ideas", "country"]
    apply_brace_stack(code_of_line("\t\tFOO = { OR = { a = b } }"), stack)
    assert stack == ["ideas", "country"]
    apply_brace_stack(code_of_line("\t}"), stack)
    assert stack == ["ideas"]


def test_stack_pushes_an_empty_name_for_a_bare_brace():
    stack = []
    apply_brace_stack("{", stack)
    assert stack == [""]


def test_stack_pop_on_an_empty_stack_is_survivable():
    stack = []
    apply_brace_stack("}", stack)
    assert stack == []


def test_code_of_line_blanks_quotes_and_comments_without_moving_columns():
    line = '\tname = "a } b" # }'
    code = code_of_line(line)
    assert "}" not in code
    assert code.index('"') == line.index('"')


def test_gap_collapses_a_doubled_blank():
    out = ["a", ""]
    lines = ["", "b"]
    assert collapse_blank_gap(out, lines, 0) == 1
    assert out == ["a", ""]


def test_gap_collapses_a_blank_under_the_parent_opener():
    out = ["FOO = {"]
    lines = ["", "\tb = c"]
    assert collapse_blank_gap(out, lines, 0) == 1


def test_gap_drops_a_blank_left_above_the_parent_closer():
    out = ["FOO = {", "\tb = c", ""]
    lines = ["}"]
    assert collapse_blank_gap(out, lines, 0) == 0
    assert out == ["FOO = {", "\tb = c"]


def test_gap_keeps_a_real_separator():
    out = ["FOO = {", "\tb = c"]
    lines = ["", "\td = e"]
    assert collapse_blank_gap(out, lines, 0) == 0
    assert out == ["FOO = {", "\tb = c"]


def test_span_of_a_block_closing_on_its_own_line():
    assert find_block_span(["x = {", "\ty = 1", "}", "}"], 0, 4) == (2, 0)


# ---- block formatters ----------------------------------------------------------


@pytest.mark.parametrize(
    "lines, expected",
    [
        ([], "search_filters = { }"),
        (
            ["\tsearch_filters = {", "\t\tnational_focus", "\t\tpolitics", "\t}"],
            "search_filters = { national_focus politics }",
        ),
    ],
    ids=["empty", "multi-line"],
)
def test_compact_search_filters(lines, expected):
    assert compact_search_filters(lines) == expected


@pytest.mark.parametrize(
    "lines, expected",
    [
        ([], "icon = GFX_goal_generic_support_the_left_wing"),
        ([" icon = GFX_a "], "icon = GFX_a"),
        (["icon = {", "\tfoo", "}"], "icon = {\n\tfoo\n}"),
        (["icon = {", "", "\tfoo", "}"], "icon = {\n\tfoo\n}"),
    ],
    ids=["default", "one line", "block", "block with a blank"],
)
def test_compact_icon(lines, expected):
    assert compact_icon(lines) == expected


def test_collapse_blank_runs_to_none():
    assert collapse_blank_runs(["a", "", "", "b"], max_blank=0) == ["a", "b"]


def test_join_groups_drops_empty_groups_and_edge_blanks():
    assert join_groups([["", "a", ""], [], ["b", ""]]) == ["a", "", "b"]


def test_emit_comments_skips_blanks_and_trims():
    out = []
    emit_comments(out, ["", " # note  "])
    assert out == [" # note"]


@pytest.mark.parametrize(
    "lines, expected",
    [(["x = {", "log = yes", "}"], True), ([], False)],
    ids=["logged", "empty"],
)
def test_block_has_log(lines, expected):
    assert block_has_log(lines) is expected


@pytest.mark.parametrize(
    "lines, expected",
    [(["plain"], ["plain"]), (["x = {", "}"], ["x = {", "\tlog", "}"])],
    ids=["no brace", "block"],
)
def test_inject_log_after_brace(lines, expected):
    assert inject_log_after_brace(lines, "\tlog") == expected


# ---- reading, writing and backups ----------------------------------------------


def test_read_reports_a_missing_or_unreadable_file(tmp_path):
    assert read_lines_for_standardization(str(tmp_path / "missing.txt")) is None
    unreadable = tmp_path / "as_a_directory.txt"
    unreadable.mkdir()
    assert read_lines_for_standardization(str(unreadable)) is None


def test_write_joins_lines_and_reports_a_failed_write(tmp_path, monkeypatch):
    output = tmp_path / "out.txt"
    assert write_standardized_output(
        str(output), ["foo = 1", "", "bar = 2"], start_time=0, processed_count=2
    )
    assert _read(output) == "foo = 1\n\nbar = 2\n"

    def fail_write(_path, _text):
        raise OSError("full")

    monkeypatch.setattr("common_utils.atomic_write_text", fail_write)
    assert not write_standardized_output(
        str(output), ["foo = 1"], start_time=0, processed_count=1
    )


def test_resolve_output_backs_up_the_input(tmp_path):
    source = _write(tmp_path / "source.txt", "value = yes\n")
    destination = tmp_path / "destination.txt"
    args = argparse.Namespace(
        input_file=str(source), output=str(destination), backup=True
    )
    assert resolve_output_file_and_backup(args) == str(destination)
    assert list(tmp_path.glob("source.txt.backup.*"))


def test_resolve_output_exits_for_a_missing_input(tmp_path):
    missing = argparse.Namespace(
        input_file=str(tmp_path / "no.txt"), output=None, backup=False
    )
    with pytest.raises(SystemExit):
        resolve_output_file_and_backup(missing)


def test_resolve_output_exits_when_the_backup_fails(tmp_path, monkeypatch):
    source = _write(tmp_path / "source.txt", "value = yes\n")
    monkeypatch.setattr("common_utils.create_backup", lambda _path: "")
    with pytest.raises(SystemExit):
        resolve_output_file_and_backup(
            argparse.Namespace(input_file=str(source), output=None, backup=True)
        )


# ---- BaseStandardizer and run_standardizer -------------------------------------


class _MiniStandardizer(BaseStandardizer):
    def get_block_pattern(self):
        return r"^thing\s*=\s*{"

    def extract_properties(self, block_lines):
        return {"id": block_lines[1].strip()}

    def format_block(self, props):
        return ["thing = {", f"\t{props['id']}", "}"]


def test_base_standardizer_formats_each_matching_block(tmp_path):
    source = _write(
        tmp_path / "mini.txt", "header = yes\nthing = {\n\tvalue = yes\n}\n"
    )
    output = tmp_path / "mini-out.txt"

    standardizer = _MiniStandardizer()
    assert standardizer.standardize_file(str(source), str(output))
    assert standardizer.processed_count == 1
    assert _read(output) == "header = yes\nthing = {\n\tvalue = yes\n}\n"


def test_base_standardizer_leaves_a_file_without_blocks_alone(tmp_path):
    untouched = _write(tmp_path / "untouched.txt", "header = yes\n")
    assert _MiniStandardizer().standardize_file(str(untouched), str(untouched))
    assert _read(untouched) == "header = yes\n"


def test_base_standardizer_fails_for_a_missing_input(tmp_path):
    absent = tmp_path / "absent.txt"
    assert not _MiniStandardizer().standardize_file(str(absent), str(tmp_path / "out"))
    assert not absent.exists()


def test_run_standardizer_writes_the_output(tmp_path, capsys):
    source = _write(tmp_path / "source.txt", "thing = {\nvalue = yes\n}\n")
    destination = tmp_path / "destination.txt"

    run_standardizer(
        _MiniStandardizer, "mini", argv=[str(source), "-o", str(destination), "-v"]
    )

    assert _read(destination) == "thing = {\n\tvalue = yes\n}\n"
    assert "Processing completed" in capsys.readouterr().err


def test_run_standardizer_exits_one_when_the_standardizer_fails(tmp_path):
    source = _write(tmp_path / "source.txt", "thing = {\nvalue = yes\n}\n")

    class _Failing(_MiniStandardizer):
        def standardize_file(self, *_args):
            return False

    with pytest.raises(SystemExit) as exit_info:
        run_standardizer(_Failing, "mini", argv=[str(source)])
    assert exit_info.value.code == 1
