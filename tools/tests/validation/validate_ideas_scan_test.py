"""Tests for the idea scanners: reference extraction, parsing, and gfx probing.

These are the pure functions the pool workers call, so they are exercised
directly with the text and files the validator would hand them.
"""

import os

from validate_ideas import (
    _META_PREFIX_SENTINEL,
    _check_file_for_refs,
    _extract_idea_refs_from_blocks,
    _extract_swap_idea_refs,
    _idea_categories_frame_count,
    _load_dynamic_token_names,
    _on_add_is_log_only,
    _parse_ideas_from_file,
    _parse_ideas_from_text,
    _scan_idea_refs_for_unused,
)
from validator_common import casefold_index

NO_CATEGORIES: frozenset = frozenset()


def _write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return path


def test_swap_block_refs_are_collected():
    text = """focus = {
\tcompletion_reward = {
\t\tswap_ideas = {
\t\t\tremove_idea = OLD_spirit
\t\t\tadd_idea = NEW_spirit
\t\t}
\t}
}
"""

    assert _extract_swap_idea_refs(text) == ["OLD_spirit", "NEW_spirit"]


def test_unclosed_add_ideas_block_yields_no_refs():
    assert _extract_idea_refs_from_blocks("add_ideas = {\n\tSPIRIT_one\n") == []


def test_quoted_and_nested_entries_do_not_swallow_sibling_names():
    text = """add_ideas = {
\t"QUOTED_spirit"
\tif = {
\t\tlimit = { has_country_flag = "brace } inside" }
\t\t# a skipped comment
\t}
\tPLAIN_spirit
}
"""

    assert _extract_idea_refs_from_blocks(text) == ["QUOTED_spirit", "PLAIN_spirit"]


def test_on_add_log_only_detection():
    assert _on_add_is_log_only('idea = {\n\ton_add = {\n\t\tlog = "x"\n\t}\n}')
    assert _on_add_is_log_only(
        'idea = {\n\ton_add = {\n\n\t\t# note\n\t\tlog = "x"\n\t}\n}'
    )
    assert not _on_add_is_log_only(
        'idea = {\n\ton_add = {\n\t\tlog = "x"\n\t\tadd_stability = 0.05\n\t}\n}'
    )
    assert not _on_add_is_log_only("idea = {\n\tpicture = x\n}")


def test_second_on_add_with_real_effects_clears_the_flag():
    text = (
        "idea = {\n"
        '\ton_add = {\n\t\tlog = "x"\n\t}\n'
        "\ton_add = {\n\t\tadd_stability = 0.05\n\t}\n"
        "}"
    )

    assert not _on_add_is_log_only(text)


def test_empty_ideas_file_parses_to_nothing(tmp_path):
    path = _write(tmp_path, "common/ideas/empty.txt", "")

    assert _parse_ideas_from_file(str(path), str(tmp_path), NO_CATEGORIES) == ({}, [])


def test_schema_key_at_idea_level_is_not_an_idea():
    text = """ideas = {
\tcountry = {
\t\tmodifier = { stability_factor = 0.1 }
\t\tREAL_idea = {
\t\t\tpicture = x
\t\t}
\t}
}
"""

    defined, issues = _parse_ideas_from_text(text, NO_CATEGORIES)

    assert defined == {"REAL_idea": ("country", None, "x")}
    assert issues == []


def test_cancel_always_no_and_log_only_on_add_are_recorded():
    text = """ideas = {
\tcountry = {
\t\tCANCEL_idea = {
\t\t\tcancel = { always = no }
\t\t\tpicture = x
\t\t}
\t\tLOG_idea = {
\t\t\ton_add = {
\t\t\t\tlog = "[GetDateText]: traced"
\t\t\t}
\t\t\tpicture = x
\t\t}
\t}
}
"""

    _defined, issues = _parse_ideas_from_text(text, NO_CATEGORIES)

    assert [(i.idea_name, i.issue_type, i.line) for i in issues] == [
        ("CANCEL_idea", "cancel-always-no", 3),
        ("LOG_idea", "on-add-log-only", 7),
    ]


def test_dynamic_token_names_are_loaded(tmp_path):
    _write(
        tmp_path,
        "common/synchronized_dynamic_tokens/MD_tokens.txt",
        "TOKEN_one\nTOKEN_two\n\nnot a token line\n",
    )

    assert _load_dynamic_token_names(str(tmp_path)) == {"TOKEN_one", "TOKEN_two"}


def test_dynamic_token_names_from_an_empty_registry(tmp_path):
    _write(tmp_path, "common/synchronized_dynamic_tokens/MD_tokens.txt", "")

    assert _load_dynamic_token_names(str(tmp_path)) == set()


def test_unused_scan_captures_literal_and_meta_references(tmp_path):
    path = _write(
        tmp_path,
        "common/scripted_effects/grants.txt",
        "grant = {\n"
        "\tadd_ideas = SPIRIT_one\n"
        "\tadd_ideas = { SPIRIT_two SPIRIT_three }\n"
        "\tadd_timed_idea = { idea = tribute_idea_[ROOTTAG] days = 30 }\n"
        "}\n",
    )

    refs = _scan_idea_refs_for_unused((str(path), str(tmp_path)))

    assert {"SPIRIT_one", "SPIRIT_two", "SPIRIT_three"} <= set(refs)
    assert _META_PREFIX_SENTINEL + "tribute_idea_" in refs


def test_unused_scan_ignores_skipped_and_empty_files(tmp_path):
    ignored = _write(tmp_path, "gfx/notes.txt", "add_ideas = SPIRIT_one\n")
    empty = _write(tmp_path, "common/empty.txt", "")

    assert _scan_idea_refs_for_unused((str(ignored), str(tmp_path))) == []
    assert _scan_idea_refs_for_unused((str(empty), str(tmp_path))) == []


def _ref_check(path, defined, tmp_path):
    return _check_file_for_refs(
        (str(path), frozenset(defined), casefold_index(defined), str(tmp_path))
    )


def test_undefined_and_case_mismatched_refs_are_separated(tmp_path):
    path = _write(
        tmp_path,
        "events/MD_test.txt",
        "option = {\n"
        "\thas_idea = KNOWN_idea\n"
        "\thas_idea = known_idea\n"
        "\tadd_ideas = missing_idea\n"
        "\tadd_ideas = generic_spirit\n"
        "\tadd_ideas = var:dynamic_token\n"
        "\tadd_ideas = tribute_[ROOTTAG]\n"
        "\tadd_ideas = 42\n"
        "\tadd_ideas = ab\n"
        "}\n",
    )

    assert _ref_check(path, {"KNOWN_idea"}, tmp_path) == [
        "MD_test.txt: case-mismatch idea reference 'known_idea' — defined as "
        "'KNOWN_idea' (works on Windows, fails on Linux)",
        "MD_test.txt: undefined idea reference 'missing_idea'",
    ]


def test_ref_check_skips_ignored_empty_and_keywordless_files(tmp_path):
    ignored = _write(tmp_path, "gfx/notes.txt", "has_idea = missing_idea\n")
    empty = _write(tmp_path, "events/empty.txt", "")
    unrelated = _write(tmp_path, "events/other.txt", "add_stability = 0.05\n")

    assert _ref_check(ignored, set(), tmp_path) == []
    assert _ref_check(empty, set(), tmp_path) == []
    assert _ref_check(unrelated, set(), tmp_path) == []


def test_frame_count_ignores_an_unlistable_directory(tmp_path, monkeypatch):
    real_listdir = os.listdir

    def failing_listdir(path):
        if str(path) == str(tmp_path):
            raise PermissionError("denied")
        return real_listdir(path)

    monkeypatch.setattr(os, "listdir", failing_listdir)

    assert _idea_categories_frame_count([str(tmp_path)]) is None


def test_frame_count_skips_a_gfx_entry_it_cannot_read(tmp_path):
    (tmp_path / "a_unreadable.gfx").mkdir()
    _write(
        tmp_path,
        "b_ideas.gfx",
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 4 }\n',
    )

    assert _idea_categories_frame_count([str(tmp_path)]) == 4
