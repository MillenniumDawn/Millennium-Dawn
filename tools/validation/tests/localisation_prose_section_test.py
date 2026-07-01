"""Tests for the prose section-sign (§) exemption in validate_localisation.

A § followed by whitespace and a digit is a legal citation ("15 U.S.C. § 1")
and must be exempt from colour-code balance checks; a dangling/broken § (before
a word, quote, or line end) must still be flagged.
"""

from validate_localisation import _PROSE_SECTION_SIGN_RE, process_yml_for_syntax

S = "§"


def test_regex_exempts_legal_section_number():
    assert S not in _PROSE_SECTION_SIGN_RE.sub("", f"15 U.S.C. {S} 1")


def test_regex_keeps_dangling_section_sign():
    for line in [f"ends here {S}", f'ends {S}"', f"a {S} word"]:
        assert S in _PROSE_SECTION_SIGN_RE.sub("", line)


def test_regex_keeps_color_codes():
    assert _PROSE_SECTION_SIGN_RE.sub("", f"{S}Yhello{S}!") == f"{S}Yhello{S}!"


def _write_yml(tmp_path, name, value_line):
    p = tmp_path / name
    p.write_text(f"l_english:\n {value_line}\n", encoding="utf-8-sig")
    return str(p)


def test_syntax_check_exempts_legal_citation(tmp_path):
    path = _write_yml(tmp_path, "a_l_english.yml", f'key:0 "(15 U.S.C. {S} 1)."')
    assert process_yml_for_syntax((path, ["Y", "R", "G"], frozenset())) == []


def test_syntax_check_flags_dangling_section_sign(tmp_path):
    path = _write_yml(tmp_path, "b_l_english.yml", f'key:0 "broken color {S} here"')
    results = process_yml_for_syntax((path, ["Y", "R", "G"], frozenset()))
    assert any("odd number" in r for r in results)
