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


def _round_stem(content, index, stem, references=None):
    header, entries = _parse_loc_file(content)
    return _format_output(header, entries, index, stem, references)


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


def test_focus_tree_anchor_preserved_and_idempotent():
    # Matching `MD_focus_<TAG>_l_english` stem so the `<TAG>_focus_tree` anchor
    # path fires. The anchor key is not indexed as a focus, so it categorises as
    # Unreferenced — the case the old NF-only anchor search corrupted on re-run.
    index = _empty_index()
    index["National Focus"].add("ISR_test_focus")
    stem = "MD_focus_ISR_l_english.yml"
    content = (
        "l_english:\n"
        ' ISR_focus_tree: "Israeli Focus Tree"\n'
        ' ISR_test_focus: "Test Focus"\n'
    )

    once = _round_stem(content, index, stem, references=set())
    assert ' ISR_focus_tree: "Israeli Focus Tree"' in once
    assert ' ISR_focus_tree: ""' not in once
    assert once.count("ISR_focus_tree:") == 1

    twice = _round_stem(once, index, stem, references=set())
    assert once == twice


def test_duplicate_focus_tree_anchor_keeps_last_non_blank():
    # HOI4 loc is last-wins, so a later duplicate of the focus-tree anchor must
    # win. The old dedup kept the FIRST non-blank, silently flipping the shown
    # name back after standardization.
    index = _empty_index()
    stem = "MD_focus_ISR_l_english.yml"
    content = 'l_english:\n ISR_focus_tree: "Old Name"\n ISR_focus_tree: "New Name"\n'
    out = _round_stem(content, index, stem, references=set())
    assert ' ISR_focus_tree: "New Name"' in out
    assert ' ISR_focus_tree: "Old Name"' not in out
    assert out.count("ISR_focus_tree:") == 1


def test_duplicate_focus_tree_later_blank_does_not_clobber():
    # A later blank duplicate must not wipe an earlier real value.
    index = _empty_index()
    stem = "MD_focus_ISR_l_english.yml"
    content = 'l_english:\n ISR_focus_tree: "Real Name"\n ISR_focus_tree: ""\n'
    out = _round_stem(content, index, stem, references=set())
    assert ' ISR_focus_tree: "Real Name"' in out
    assert out.count("ISR_focus_tree:") == 1


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
