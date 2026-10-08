"""Tests for how validate_localisation treats the section sign (§).

`§§` is the engine's escape for a literal section sign: "15 U.S.C. §§ 1"
renders "15 U.S.C. § 1". A single § always starts a color code, even before a
space. Checked in game (1.19.3, #5097): "15 U.S.C. § 1" renders
"15 U.S.C. 1", drops the space, and logs "Could not find coloring for
character ' '" every frame, so a bare § before whitespace must be flagged.
"""

from shared.suite import write_yml as _write_yml
from shared.suite import yml_syntax
from validate_localisation import _LITERAL_SECTION_SIGN_RE

S = "§"


def test_regex_strips_escaped_section_sign():
    assert S not in _LITERAL_SECTION_SIGN_RE.sub("", f"15 U.S.C. {S}{S} 1")


def test_regex_keeps_single_section_sign():
    for line in [f"15 U.S.C. {S} 1", f"ends here {S}", f'ends {S}"', f"a {S} word"]:
        assert S in _LITERAL_SECTION_SIGN_RE.sub("", line)


def test_regex_keeps_color_codes():
    assert _LITERAL_SECTION_SIGN_RE.sub("", f"{S}Yhello{S}!") == f"{S}Yhello{S}!"


def _syntax(path):
    return yml_syntax(path, ["Y", "R", "G"])


def test_syntax_check_accepts_escaped_legal_citation(tmp_path):
    path = _write_yml(tmp_path, "a_l_english.yml", f'key:0 "(15 U.S.C. {S}{S} 1)."')
    assert _syntax(path) == []


def test_syntax_check_accepts_escaped_sign_next_to_color_codes(tmp_path):
    line = f'key:0 "{S}YSection{S}! {S}{S} 1 applies."'
    path = _write_yml(tmp_path, "b_l_english.yml", line)
    assert _syntax(path) == []


def test_syntax_check_flags_bare_section_sign_before_a_number(tmp_path):
    path = _write_yml(tmp_path, "c_l_english.yml", f'key:0 "(15 U.S.C. {S} 1)."')
    results = _syntax(path)
    assert len(results) == 1
    assert "read as a color code" in results[0]


def test_syntax_check_flags_dangling_section_sign(tmp_path):
    path = _write_yml(tmp_path, "d_l_english.yml", f'key:0 "broken color {S}"')
    results = _syntax(path)
    assert any("odd number" in r for r in results)
