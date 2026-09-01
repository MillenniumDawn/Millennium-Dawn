"""Tests for fix_styling: the fix_line rules, the file-level fixers, and main().

fix_line owns leading spaces becoming tabs, ``===`` runs inside comments becoming
``---``, and a preserved trailing newline; normalize_spacing owns the rest. The
file-level cases cover what fix_file writes back and what it can only report.
"""

import runpy
import sys

import fix_styling
import pytest
from fix_styling import fix_file, fix_file_dry_run, fix_line


def _write(path, content):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def _run_main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", [fix_styling.__file__, *argv])
    return fix_styling.main()


def test_pads_inline_block():
    fixed, fixes = fix_line("\t\tNOT = {country_exists = ENG}\n")
    assert fixed == "\t\tNOT = { country_exists = ENG }\n"
    assert fixes == 1


def test_leading_spaces_become_tabs():
    fixed, _ = fix_line("    x = { y = 1 }")
    assert fixed == "\tx = { y = 1 }"


def test_equals_separator_in_comment():
    fixed, _ = fix_line("\t# ==== section ====\n")
    assert fixed == "\t# ---- section ----\n"


def test_inline_comment_preserved():
    fixed, _ = fix_line("\tfoo=bar  # note ==== here\n")
    assert fixed == "\tfoo = bar # note ---- here\n"


def test_quoted_string_not_rewritten():
    line = '\tlog = "a=b {c}"\n'
    assert fix_line(line) == (line, 0)


def test_comment_line_keeps_single_newline():
    line = "# plain {comment}\n"
    assert fix_line(line) == (line, 0)


def test_trailing_whitespace_stripped():
    fixed, _ = fix_line("\tcost = 10   \n")
    assert fixed == "\tcost = 10\n"


def test_clean_line_reports_no_fixes():
    line = "\tavailable = { has_country_flag = some_flag }\n"
    assert fix_line(line) == (line, 0)


def test_single_leading_space_is_left_alone():
    """One space is not a full tab, so the rewrite is a no-op and costs no fix."""
    fixed, fixes = fix_line(" x = { y = 1 }\n")
    assert fixed == " x = { y = 1 }\n"
    assert fixes == 0


def test_inline_comment_without_separator_is_untouched():
    fixed, _ = fix_line("\tfoo=bar # plain note\n")
    assert fixed == "\tfoo = bar # plain note\n"


def test_fix_file_rewrites_and_counts(tmp_path):
    path = tmp_path / "focus.txt"
    _write(path, "    cost=10   \nfoo = { bar = 1 }\n\n\n")

    _fp, fixes, unfixable = fix_file(str(path))

    with open(path, encoding="utf-8", newline="") as handle:
        assert handle.read() == "\tcost = 10\nfoo = { bar = 1 }\n"
    assert fixes == 2
    assert unfixable == []


def test_fix_file_leaves_a_clean_file_byte_identical(tmp_path):
    path = tmp_path / "clean.txt"
    original = "focus = {\n\tid = TAG_focus\n}\n"
    _write(path, original)

    _fp, fixes, unfixable = fix_file(str(path))

    assert path.read_bytes() == original.encode()
    assert (fixes, unfixable) == (0, [])


def test_fix_file_reports_an_odd_quote_it_cannot_fix(tmp_path):
    path = tmp_path / "quotes.txt"
    _write(path, 'focus = {\n\tlog = "unterminated\n}\n')

    _fp, _fixes, unfixable = fix_file(str(path))

    assert len(unfixable) == 1
    assert unfixable[0].endswith(":2: Possible missing quotation mark")


def test_fix_file_ignores_an_odd_quote_inside_a_comment(tmp_path):
    path = tmp_path / "commented.txt"
    _write(path, '\tcost = 10 # the " here is prose\n')

    _fp, _fixes, unfixable = fix_file(str(path))

    assert unfixable == []


def test_fix_file_reports_an_unreadable_path(tmp_path):
    filepath = str(tmp_path / "gone.txt")

    result_path, fixes, unfixable = fix_file(filepath)

    assert (result_path, fixes) == (filepath, 0)
    assert len(unfixable) == 1
    assert "Error processing" in unfixable[0]


def test_dry_run_counts_without_writing(tmp_path):
    path = tmp_path / "focus.txt"
    original = "    cost=10\n"
    _write(path, original)

    _fp, fixes, unfixable = fix_file_dry_run(str(path))

    assert path.read_bytes() == original.encode()
    assert fixes == 2
    assert unfixable == []


def test_dry_run_reports_an_unreadable_path(tmp_path):
    _fp, fixes, unfixable = fix_file_dry_run(str(tmp_path / "gone.txt"))

    assert fixes == 0
    assert "Error processing" in unfixable[0]


def test_dry_run_reports_only_the_odd_quote(tmp_path):
    path = tmp_path / "quotes.txt"
    _write(path, '\tlog = "balanced"\n\tlog = "unterminated\n')

    _fp, _fixes, unfixable = fix_file_dry_run(str(path))

    assert len(unfixable) == 1
    assert unfixable[0].endswith(":2: Possible missing quotation mark")


def test_main_fixes_the_files_it_is_given(tmp_path, monkeypatch, capsys):
    path = tmp_path / "focus.txt"
    _write(path, "    cost=10\n")

    assert _run_main(monkeypatch, str(path)) == 0

    assert path.read_bytes() == b"\tcost = 10\n"
    assert "Fixed 2 issues in 1 files" in capsys.readouterr().out


def test_main_dry_run_leaves_the_file_alone(tmp_path, monkeypatch, capsys):
    path = tmp_path / "focus.txt"
    original = "    cost=10\n"
    _write(path, original)

    assert _run_main(monkeypatch, "--dry-run", str(path)) == 0

    assert path.read_bytes() == original.encode()
    assert "Would fix 2 issues in 1 files" in capsys.readouterr().out


def test_main_reports_nothing_to_do(tmp_path, monkeypatch, capsys):
    assert _run_main(monkeypatch, str(tmp_path / "gone.txt")) == 0

    assert "No files to process" in capsys.readouterr().out


@pytest.mark.parametrize("count,truncated", [(3, False), (51, True)])
def test_main_truncates_only_a_long_unfixable_list(
    tmp_path, monkeypatch, capsys, count, truncated
):
    path = tmp_path / "quotes.txt"
    _write(path, '\tlog = "unterminated\n' * count)

    assert _run_main(monkeypatch, str(path)) == 0

    out = capsys.readouterr().out
    assert f"{count} issues need manual attention" in out
    assert ("... and 1 more" in out) is truncated


def test_script_entry_point_exits_zero(tmp_path, monkeypatch):
    path = tmp_path / "focus.txt"
    _write(path, "    cost=10\n")
    monkeypatch.setattr(sys, "argv", [fix_styling.__file__, str(path)])

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(fix_styling.__file__, run_name="__main__")

    assert excinfo.value.code == 0
