"""Token-level and CLI behaviour of cleanup_or.py.

The token helpers are imported by check_common_mistakes.py, so their handling of
malformed script (stray braces, unterminated blocks) has to stay predictable.
"""

import runpy
import sys

import cleanup_or as C
import pytest


def _conditions(text):
    return C._count_top_level_conditions(C._tokenize_inner(text))


def test_condition_count_of_a_flat_block():
    assert _conditions("has_country_flag = a\nhas_country_flag = b\n") == 2


def test_anonymous_nested_block_counts_nothing():
    assert _conditions("{ has_country_flag = a }") == 0


def test_stray_closing_brace_is_absorbed():
    assert _conditions("has_country_flag = a }") == 1


def test_unterminated_block_value_counts_once():
    assert _conditions("NOT = { has_country_flag = a") == 1


def test_nested_block_value_counts_once():
    assert _conditions("NOT = { AND = { a = b c = d } }") == 1


def test_key_without_a_value_counts_once():
    assert _conditions("has_country_flag =") == 1


def test_extract_inner_text_of_an_empty_block():
    assert C._extract_inner_text([]) == ""


def test_comment_only_condition_yields_no_replacement():
    assert C._extract_single_condition_lines("\n\t\t# only a comment\n", "\t") == []


def test_ragged_condition_indentation_is_preserved():
    inner = "\t\t\tNOT = {\n\t\thas_country_flag = a\n\t\t\t}"

    assert C._extract_single_condition_lines(inner, "\t") == [
        "\tNOT = {\n",
        "\t\thas_country_flag = a\n",
        "\t}\n",
    ]


def test_blank_and_block_yields_no_lines():
    assert C._extract_all_inner_lines("\n\n", "\t") == []


def test_ragged_and_body_indentation_is_preserved():
    assert C._extract_all_inner_lines("\t\ta = b\n\tc = d", "\t") == [
        "\ta = b\n",
        "\tc = d\n",
    ]


def test_or_context_stack_never_pops_its_root():
    stack = [False]
    C._push_pop_or_context(stack, False, 0, 2)
    assert stack == [False]


def test_inline_or_with_two_conditions_is_not_reported():
    lines = ["\tavailable = { OR = { has_country_flag = a has_country_flag = b } }\n"]
    assert C.find_single_condition_or_blocks(lines) == []


def test_inline_or_with_one_condition_is_reported():
    lines = ["\tavailable = { OR = { has_country_flag = a } }\n"]
    assert [line for line, _message in C.find_single_condition_or_blocks(lines)] == [1]


def test_main_reports_nothing_when_no_file_changes(tmp_path, capsys):
    (tmp_path / "clean.txt").write_text("foo = {\n\tbar = yes\n}\n", encoding="utf-8")

    C.main([str(tmp_path)])

    assert "No single-condition OR blocks found." in capsys.readouterr().out


def _run_cli(argv):
    saved = sys.argv
    sys.argv = argv
    try:
        runpy.run_path(C.__file__, run_name="__main__")
    finally:
        sys.argv = saved


def test_cli_simplifies_the_files_it_is_given(tmp_path, capsys):
    target = tmp_path / "focus.txt"
    target.write_text(
        "foo = {\n\tavailable = {\n\t\tOR = {\n\t\t\thas_country_flag = bar\n\t\t}\n\t}\n}\n",
        encoding="utf-8",
    )

    _run_cli(["cleanup_or.py", str(target)])

    assert target.read_text(encoding="utf-8") == (
        "foo = {\n\tavailable = {\n\t\thas_country_flag = bar\n\t}\n}\n"
    )
    assert "Simplified OR blocks in:" in capsys.readouterr().out


def test_cli_without_arguments_prints_usage_and_fails(capsys):
    with pytest.raises(SystemExit) as exc:
        _run_cli(["cleanup_or.py"])

    assert exc.value.code == 1
    assert "usage: cleanup_or.py" in capsys.readouterr().err
