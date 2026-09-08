"""Tests for the localisation standardizer.

Regression guard for the bug where user comment lines were discarded on rewrite.
Genuine `#` comments must survive (attached to the key below them), quoted values
must stay byte-exact, no keys may be lost, and re-standardizing must be stable
(the tool's own generated section headers are regenerated, not accumulated).
"""

import sys

import pytest
import standardize_localisation
from standardize_localisation import (
    SECTION_ORDER,
    LocalisationStandardizer,
    _build_index,
    _build_reference_tokens,
    _detect_mod_root,
    _find_category,
    _format_output,
    _parse_loc_file,
)


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


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


def _mod_root(tmp_path):
    root = tmp_path / "mod"
    (root / "common").mkdir(parents=True)
    (root / "events").mkdir()
    return root


def test_directories_named_like_scripts_are_skipped(tmp_path):
    # `*.txt` globs match directories too; an unreadable entry must be skipped,
    # not abort the whole index build.
    root = _mod_root(tmp_path)
    focus = root / "common" / "national_focus"
    focus.mkdir()
    (focus / "not_a_file.txt").mkdir()

    assert _build_index(root, verbose=False)["National Focus"] == set()
    assert _build_reference_tokens(root, verbose=False) == set()


def test_dotted_key_without_an_event_namespace_falls_through_to_the_index():
    index = _empty_index()
    index["Ideas"].add("some.thing")
    assert _find_category("some.thing", index) == "Ideas"


def test_unparsable_line_is_kept_above_the_next_key():
    content = 'l_english:\n stray line without a colon\n my_key: "x"\n'
    out = _round(content, _empty_index()).splitlines()
    stray = out.index(" stray line without a colon")
    assert out[stray + 1] == ' my_key: "x"'


def test_missing_focus_tree_anchor_is_created():
    index = _empty_index()
    index["National Focus"].add("ISR_test_focus")
    out = _round_stem(
        'l_english:\n ISR_test_focus: "Test Focus"\n',
        index,
        "MD_focus_ISR_l_english.yml",
        references=set(),
    )
    assert ' ISR_focus_tree: ""' in out
    assert out.index("ISR_focus_tree") < out.index("ISR_test_focus")


def test_national_focus_section_omitted_when_a_tag_file_has_none():
    out = _round_stem(
        'l_english:\n other_key: "x"\n',
        _empty_index(),
        "MD_focus_ISR_l_english.yml",
        references={"other_key"},
    )
    assert "# National Focus" not in out
    assert ' other_key: "x"' in out


def test_detect_mod_root_walks_up_and_gives_up(tmp_path):
    root = _mod_root(tmp_path)
    loc_dir = root / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    loc_file = loc_dir / "MD_test_l_english.yml"
    _write(loc_file, "l_english:\n")

    assert _detect_mod_root(loc_file) == root
    assert _detect_mod_root(tmp_path / "not_a_mod") is None


def _loc_file(root):
    loc_dir = root / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    loc_file = loc_dir / "MD_test_l_english.yml"
    _write(loc_file, 'l_english:\n my_key: "x"\n')
    return loc_file


def test_main_detects_the_mod_root_and_overwrites_in_place(tmp_path, monkeypatch):
    root = _mod_root(tmp_path)
    loc_file = _loc_file(root)
    monkeypatch.setattr(
        sys, "argv", ["standardize_localisation.py", str(loc_file), "-v"]
    )

    standardize_localisation.main()

    assert loc_file.read_bytes().startswith(b"\xef\xbb\xbf")
    assert 'my_key: "x"' in loc_file.read_text(encoding="utf-8-sig")
    assert not list((root / "localisation" / "english").glob("*.backup.*"))


def test_main_exits_one_for_a_missing_input(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["standardize_localisation.py", str(tmp_path / "absent.yml")]
    )
    with pytest.raises(SystemExit) as exit_info:
        standardize_localisation.main()
    assert exit_info.value.code == 1


def test_main_exits_one_when_the_mod_root_cannot_be_detected(tmp_path, monkeypatch):
    loose = tmp_path / "MD_test_l_english.yml"
    _write(loose, 'l_english:\n my_key: "x"\n')
    monkeypatch.setattr(sys, "argv", ["standardize_localisation.py", str(loose)])
    with pytest.raises(SystemExit) as exit_info:
        standardize_localisation.main()
    assert exit_info.value.code == 1


def test_main_exits_one_when_the_backup_fails(tmp_path, monkeypatch):
    root = _mod_root(tmp_path)
    loc_file = _loc_file(root)
    monkeypatch.setattr(standardize_localisation, "create_backup", lambda _path: "")
    monkeypatch.setattr(
        sys, "argv", ["standardize_localisation.py", str(loc_file), "-b"]
    )
    with pytest.raises(SystemExit) as exit_info:
        standardize_localisation.main()
    assert exit_info.value.code == 1


def test_main_exits_one_when_the_file_has_no_language_header(tmp_path, monkeypatch):
    root = _mod_root(tmp_path)
    loc_dir = root / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    headerless = loc_dir / "MD_empty_l_english.yml"
    _write(headerless, "\n")
    monkeypatch.setattr(sys, "argv", ["standardize_localisation.py", str(headerless)])
    with pytest.raises(SystemExit) as exit_info:
        standardize_localisation.main()
    assert exit_info.value.code == 1
