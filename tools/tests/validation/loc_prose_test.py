"""Tests for the prose-convention check in validate_localisation.py.

Flags em dashes (U+2014) and backtick-as-apostrophe inside loc VALUES only --
keys and comments are never scanned.
"""

from validate_localisation import process_yml_for_prose


def _hits(tmp_path, body):
    path = tmp_path / "a_l_english.yml"
    path.write_text(body, encoding="utf-8-sig")
    return process_yml_for_prose((str(path),))


def test_flags_em_dash_in_value(tmp_path):
    body = 'l_english:\n key:0 "Their economy answers to us\u2014intact."\n'
    results = _hits(tmp_path, body)
    assert len(results) == 1
    assert results[0].category == "loc-em-dash"
    assert results[0].line == 2


def test_flags_backtick_in_value(tmp_path):
    results = _hits(tmp_path, 'l_english:\n key:0 "we`ll see."\n')
    assert len(results) == 1
    assert results[0].category == "loc-backtick-apostrophe"
    assert results[0].line == 2


def test_clean_value_not_flagged(tmp_path):
    results = _hits(
        tmp_path,
        'l_english:\n key:0 "Their economy answers to us. Their borders remain intact."\n',
    )
    assert results == []


def test_em_dash_in_comment_not_flagged(tmp_path):
    body = 'l_english:\n # a comment with an em dash \u2014 here\n key:0 "A clean value."\n'
    assert _hits(tmp_path, body) == []


def test_hyphen_and_en_dash_not_flagged(tmp_path):
    body = 'l_english:\n key:0 "pro-Western government – still fine."\n'
    assert _hits(tmp_path, body) == []


def test_both_violations_in_one_file(tmp_path):
    body = (
        "l_english:\n"
        ' key1:0 "Their economy answers to us\u2014intact."\n'
        ' key2:0 "we`ll see."\n'
    )
    results = _hits(tmp_path, body)
    categories = sorted(r.category for r in results)
    assert categories == ["loc-backtick-apostrophe", "loc-em-dash"]
