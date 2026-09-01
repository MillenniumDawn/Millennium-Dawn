"""Unit tests for fix_loc_yaml.py."""

import codecs
import runpy
import sys

import fix_loc_yaml
import pytest
from fix_loc_yaml import check_line, fix_line, process_file


def _missing_close_quote(line):
    return [p for p in check_line(line, 1) if p[1] == "missing_close_quote"]


def _issue_types(line):
    return sorted(kind for _ln, kind, _desc in check_line(line, 1))


def _run_main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", [fix_loc_yaml.__file__, *argv])
    fix_loc_yaml.main()


def test_version_key_preserves_value():
    assert fix_line(' KEY:0 "value"') == ' KEY: "value"'


def test_version_key_multi_digit():
    assert fix_line(' KEY:10 "text here"') == ' KEY: "text here"'


def test_escaped_quotes_not_flagged():
    assert _missing_close_quote(r' KEY: "he said \"hi\""') == []


def test_escaped_backslash_not_flagged():
    assert _missing_close_quote(r' KEY: "path C:\\"') == []


def test_genuinely_unclosed_quote_flagged():
    assert _missing_close_quote(' KEY: "unclosed') != []


def test_bom_and_value_preserved(tmp_path):
    path = tmp_path / "test_l_english.yml"
    path.write_bytes(codecs.BOM_UTF8 + b' KEY:0 "value"\n')

    process_file(path, fix_mode=True)

    result = path.read_bytes()
    assert result.startswith(codecs.BOM_UTF8)
    assert result == codecs.BOM_UTF8 + b' KEY: "value"\n'


def test_malformed_encoding_skipped_not_corrupted(tmp_path):
    path = tmp_path / "bad_l_english.yml"
    # 0xFF is not valid UTF-8. --fix must leave the file byte-identical rather
    # than writing U+FFFD-substituted text back and corrupting it.
    original = codecs.BOM_UTF8 + b' KEY:0 "value \xff"\n'
    path.write_bytes(original)

    problems, fixed, decode_error = process_file(path, fix_mode=True)

    assert path.read_bytes() == original
    assert fixed == 0
    assert decode_error is True


def test_malformed_encoding_flagged_in_check_mode(tmp_path):
    path = tmp_path / "bad_l_english.yml"
    original = codecs.BOM_UTF8 + b' KEY:0 "value \xff"\n'
    path.write_bytes(original)

    problems, fixed, decode_error = process_file(path, fix_mode=False)

    assert path.read_bytes() == original
    assert decode_error is True


def test_fix_is_idempotent(tmp_path):
    path = tmp_path / "test_l_english.yml"
    path.write_bytes(codecs.BOM_UTF8 + b' KEY:0 "value"\n')

    process_file(path, fix_mode=True)
    first = path.read_bytes()
    process_file(path, fix_mode=True)
    second = path.read_bytes()

    assert first == second


@pytest.mark.parametrize(
    "line,expected",
    [
        (' KEY:\t"value"', ["tab"]),
        (" # a\ttabbed comment", ["tab"]),
        (' KEY: "“curly”"', ["smart_quote"]),
        (" # a ‘curly’ comment", ["smart_quote"]),
        (' KEY:"value"', ["colon_space"]),
        ('   KEY: "value"', ["indent"]),
        (' KEY:0 "value"', ["version_key"]),
        (" KEY: plain", []),
        (' KEY: "say "hi" now"', ["unescaped_quote"]),
        ("", []),
        (" # just a comment", []),
    ],
)
def test_check_line_classifies_each_issue(line, expected):
    assert _issue_types(line) == expected


def test_unterminated_value_reports_only_the_missing_quote():
    assert _issue_types(' KEY: "') == ["missing_close_quote"]


def test_escaped_quotes_survive_the_rewrite():
    assert fix_line(r' KEY: "he said \"hi\" ok"') == r' KEY: "he said \"hi\" ok"'


def test_unescaped_inner_quotes_get_escaped():
    assert fix_line(' KEY: "say "hi" now"') == r' KEY: "say \"hi\" now"'


def test_unterminated_value_is_left_alone():
    assert fix_line(' KEY: "unterminated') == ' KEY: "unterminated'


def test_fix_line_normalises_tabs_curly_quotes_and_indent():
    assert fix_line('   KEY:\t"“value”"') == ' KEY: "\\"value\\""'


def test_comment_lines_keep_their_indentation():
    assert fix_line("   # a comment") == "   # a comment"


def test_missing_space_after_colon_is_inserted():
    assert fix_line(' KEY:"value"') == ' KEY: "value"'


def test_unquoted_value_is_left_alone():
    assert fix_line(" KEY: plain") == " KEY: plain"


def test_process_file_reports_an_unreadable_path(tmp_path, capsys):
    directory = tmp_path / "dir_l_english.yml"
    directory.mkdir()

    assert process_file(directory, fix_mode=False) == (0, 0, False)

    assert "Error reading" in capsys.readouterr().err


def test_check_mode_lists_every_problem(tmp_path, capsys):
    path = tmp_path / "test_l_english.yml"
    path.write_bytes(b' KEY:0 "value"\n   OTHER:"x"\n')

    problems, fixed, decode_error = process_file(path, fix_mode=False)

    assert (problems, fixed, decode_error) == (3, 0, False)
    out = capsys.readouterr().out
    assert ":1: [version_key]" in out
    assert ":2: [colon_space]" in out
    assert ":2: [indent]" in out


def test_fix_mode_keeps_a_bomless_file_bomless(tmp_path, capsys):
    path = tmp_path / "test_l_english.yml"
    path.write_bytes(b' KEY:0 "value"\n')

    process_file(path, fix_mode=True)

    assert path.read_bytes() == b' KEY: "value"\n'
    assert "1 version_key" in capsys.readouterr().out


def test_clean_file_reports_nothing(tmp_path):
    path = tmp_path / "test_l_english.yml"
    original = codecs.BOM_UTF8 + b' KEY: "value"\n'
    path.write_bytes(original)

    assert process_file(path, fix_mode=True) == (0, 0, False)

    assert path.read_bytes() == original


def test_main_exits_nonzero_when_check_mode_finds_problems(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "test_l_english.yml"
    path.write_bytes(b' KEY:0 "value"\n')

    with pytest.raises(SystemExit) as excinfo:
        _run_main(monkeypatch, str(path))

    assert excinfo.value.code == 1
    assert "Run with --fix to auto-fix" in capsys.readouterr().out


def test_main_fix_mode_reports_the_repair_count(tmp_path, monkeypatch, capsys):
    path = tmp_path / "test_l_english.yml"
    path.write_bytes(b' KEY:0 "value"\n')

    _run_main(monkeypatch, "--fix", str(path))

    assert path.read_bytes() == b' KEY: "value"\n'
    assert "Fixed 1 issue(s)" in capsys.readouterr().out


def test_main_skips_paths_that_do_not_exist(tmp_path, monkeypatch, capsys):
    _run_main(monkeypatch, str(tmp_path / "gone_l_english.yml"))

    assert capsys.readouterr().out == ""


def test_main_defaults_to_the_english_localisation_directory(
    tmp_path, monkeypatch, capsys
):
    english = tmp_path / "localisation" / "english"
    english.mkdir(parents=True)
    (english / "MD_test_l_english.yml").write_bytes(b' KEY:0 "value"\n')
    monkeypatch.chdir(tmp_path)

    _run_main(monkeypatch, "--fix")

    assert (english / "MD_test_l_english.yml").read_bytes() == b' KEY: "value"\n'
    assert "Fixed 1 issue(s)" in capsys.readouterr().out


def test_main_exits_nonzero_on_an_undecodable_file(tmp_path, monkeypatch, capsys):
    path = tmp_path / "bad_l_english.yml"
    original = b' KEY: "value \xff"\n'
    path.write_bytes(original)

    with pytest.raises(SystemExit) as excinfo:
        _run_main(monkeypatch, "--fix", str(path))

    assert excinfo.value.code == 1
    assert path.read_bytes() == original
    assert "could not be decoded as UTF-8" in capsys.readouterr().err


def test_script_entry_point_exits_nonzero_on_problems(tmp_path, monkeypatch):
    path = tmp_path / "test_l_english.yml"
    path.write_bytes(b' KEY:0 "value"\n')
    monkeypatch.setattr(sys, "argv", [fix_loc_yaml.__file__, str(path)])

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(fix_loc_yaml.__file__, run_name="__main__")

    assert excinfo.value.code == 1
