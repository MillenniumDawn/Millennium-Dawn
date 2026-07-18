"""Tests for the localisation standardizer.

Regression guard for the bug where user comment lines were discarded on rewrite.
Genuine `#` comments must survive (attached to the key below them), quoted values
must stay byte-exact, no keys may be lost, and re-standardizing must be stable
(the tool's own generated section headers are regenerated, not accumulated).
"""

from standardize_localisation import (
    SECTION_ORDER,
    LocalisationStandardizer,
    _format_output,
    _parse_loc_file,
)


def _empty_index():
    return {cat: set() for cat in SECTION_ORDER}


def _round(content, index):
    header, entries = _parse_loc_file(content)
    return _format_output(header, entries, index)


def test_user_comment_and_quoted_value_preserved():
    content = 'l_english:\n # user comment\n my_key: "A   B   C"\n'
    out = _round(content, _empty_index())
    assert " # user comment" in out
    assert ' my_key: "A   B   C"' in out


def test_no_keys_lost():
    content = 'l_english:\n alpha_key: "one"\n beta_key: "two"\n gamma_key: "three"\n'
    out = _round(content, _empty_index())
    for key in ("alpha_key", "beta_key", "gamma_key"):
        assert f" {key}:" in out


def test_round_trip_idempotent():
    content = (
        'l_english:\n # leading comment\n my_key: "A   B   C"\n another_key: "x"\n'
    )
    index = _empty_index()
    once = _round(content, index)
    twice = _round(once, index)
    assert once == twice


def test_bom_preserved_and_file_idempotent(tmp_path):
    mod_root = tmp_path / "mod"
    (mod_root / "common").mkdir(parents=True)
    (mod_root / "events").mkdir()
    loc_dir = mod_root / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    loc_file = loc_dir / "MD_test_l_english.yml"
    loc_file.write_text(
        'l_english:\n # user comment\n my_key: "A   B   C"\n',
        encoding="utf-8-sig",
    )

    std = LocalisationStandardizer(mod_root)
    assert std.standardize_file(loc_file, loc_file)

    assert loc_file.read_bytes().startswith(b"\xef\xbb\xbf")
    first = loc_file.read_text(encoding="utf-8-sig")
    assert "# user comment" in first
    assert '"A   B   C"' in first

    assert std.standardize_file(loc_file, loc_file)
    second = loc_file.read_text(encoding="utf-8-sig")
    assert first == second
