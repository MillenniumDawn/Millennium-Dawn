"""Unit tests for fix_loc_yaml.py."""

import codecs
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fix_loc_yaml import check_line, fix_line, process_file


def _missing_close_quote(line):
    return [p for p in check_line(line, 1) if p[1] == "missing_close_quote"]


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
