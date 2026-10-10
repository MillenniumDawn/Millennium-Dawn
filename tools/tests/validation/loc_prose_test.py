"""Tests for the prose-convention check in validate_localisation.py.

Flags em dashes (U+2014), spaced en dashes (U+2013) used in their place,
backtick-as-apostrophe, and an odd count of \\" quotes inside loc VALUES only --
keys and comments are never scanned.
"""

from shared.suite import yml_scan


def _hits(tmp_path, body):
    path = tmp_path / "a_l_english.yml"
    path.write_text(body, encoding="utf-8-sig")
    return yml_scan(path, "prose")


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


def test_hyphen_and_unspaced_en_dash_not_flagged(tmp_path):
    body = (
        'l_english:\n key:0 "pro-Western government, ASML–USA pact, 70–80mm rockets."\n'
    )
    assert _hits(tmp_path, body) == []


def test_flags_spaced_en_dash_in_value(tmp_path):
    body = 'l_english:\n key:0 "Accept the proposal – deepen our alliance"\n'
    results = _hits(tmp_path, body)
    assert [(r.category, r.severity, r.line) for r in results] == [
        ("loc-spaced-en-dash", "warning", 2)
    ]


def test_spaced_en_dash_between_numbers_is_a_range(tmp_path):
    body = 'l_english:\n key:0 "Born 9 October 1959 – 27 February 2015."\n'
    assert _hits(tmp_path, body) == []


def test_spaced_en_dash_in_comment_not_flagged(tmp_path):
    body = 'l_english:\n # Section – notes\n key:0 "A clean value."\n'
    assert _hits(tmp_path, body) == []


def test_spaced_en_dash_exemptions(tmp_path, monkeypatch):
    import validate_localisation as VL

    monkeypatch.setattr(VL, "_SPACED_EN_DASH_EXEMPTIONS", frozenset({"name_key"}))
    monkeypatch.setattr(
        VL, "_SPACED_EN_DASH_EXEMPT_FILES", frozenset({"parties_l_english.yml"})
    )
    assert (
        _hits(tmp_path, 'l_english:\n name_key:0 "Land Systems – Mowag GmbH"\n') == []
    )
    path = tmp_path / "parties_l_english.yml"
    path.write_text('l_english:\n p:0 "NEOS – The New Austria"\n', encoding="utf-8-sig")
    assert yml_scan(path, "prose") == []


def test_both_violations_in_one_file(tmp_path):
    body = (
        "l_english:\n"
        ' key1:0 "Their economy answers to us\u2014intact."\n'
        ' key2:0 "we`ll see."\n'
    )
    results = _hits(tmp_path, body)
    categories = sorted(r.category for r in results)
    assert categories == ["loc-backtick-apostrophe", "loc-em-dash"]


def test_flags_odd_count_of_escaped_quotes(tmp_path):
    results = _hits(tmp_path, 'l_english:\n key:0 "He said: \\"go now."\n')
    assert [(r.category, r.severity, r.line) for r in results] == [
        ("loc-unbalanced-quote", "error", 2)
    ]


def test_balanced_escaped_quotes_not_flagged(tmp_path):
    results = _hits(
        tmp_path, 'l_english:\n key:0 "He said: \\"go\\" and \\"stay\\"."\n'
    )
    assert results == []
