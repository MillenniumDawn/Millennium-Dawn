"""Tests for the typo-watchlist check in validate_localisation.py.

Flags known recurring misspellings (.claude/docs/typo-watchlist.md) inside loc
VALUES only -- keys are never scanned. Context-dependent entries ("it's",
"civilisation") are excluded from the watchlist.
"""

import re
from pathlib import Path

from validate_localisation import _TYPO_WATCHLIST, process_yml_for_typos


def _write_yml(tmp_path, name, value_line):
    p = tmp_path / name
    p.write_text(f"l_english:\n {value_line}\n", encoding="utf-8-sig")
    return str(p)


def test_flags_typo_in_value_case_insensitively(tmp_path):
    path = _write_yml(tmp_path, "a_l_english.yml", 'key:0 "The Airforce arrived."')
    results = process_yml_for_typos((path,))
    assert len(results) == 1
    assert "Airforce" in results[0]
    assert "Air Force" in results[0]


def test_does_not_flag_typo_inside_loc_key(tmp_path):
    path = _write_yml(
        tmp_path, "b_l_english.yml", 'TAG_airforce_idea:0 "Some correct value"'
    )
    assert process_yml_for_typos((path,)) == []


def test_does_not_flag_correct_spellings(tmp_path):
    path = _write_yml(
        tmp_path, "c_l_english.yml", 'key:0 "The Air Force will separate the units."'
    )
    assert process_yml_for_typos((path,)) == []


def test_excluded_words_never_flagged(tmp_path):
    path = _write_yml(
        tmp_path, "d_l_english.yml", 'key:0 "It\'s a matter of civilisation."'
    )
    assert process_yml_for_typos((path,)) == []


def test_typo_watchlist_covers_every_doc_token():
    # "it's" is possessive-rule context-dependent; "civilisation" is a
    # legitimate British spelling -- both are excluded from the watchlist.
    excluded = {"it's", "civilisation"}
    doc = Path(__file__).resolve().parents[3] / ".claude" / "docs" / "typo-watchlist.md"
    text = doc.read_text(encoding="utf-8")
    tokens = set()
    for line in text.splitlines():
        columns = line.split("|")
        if len(columns) < 2:
            continue
        tokens.update(m.lower() for m in re.findall(r"`([^`]+)`", columns[1]))
    tokens -= excluded
    missing = tokens - set(_TYPO_WATCHLIST)
    assert not missing, (
        f"typo-watchlist.md tokens missing from _TYPO_WATCHLIST: {missing}"
    )
