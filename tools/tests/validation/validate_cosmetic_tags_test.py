"""Tests for validate_cosmetic_tags (missing, unused, and unused-colour checks)."""

import validate_cosmetic_tags as V


def _run(tmp_path, **kwargs):
    validator = V.Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, no_cache=True, **kwargs
    )
    validator.run_validations()
    return validator


def _categories(validator):
    return sorted(issue.category for issue in validator._issues)


def test_loc_worker_skips_ignored_paths(tmp_path, write_path):
    skipped = write_path(tmp_path, ".git/x.yml", 'x:0 "TAG_A:"\n')

    assert (
        V.process_file_for_cosmetic_tag_in_loc((str(skipped), frozenset({"TAG_A"})))
        == {}
    )


def test_loc_worker_needs_a_key_shaped_reference(tmp_path, write_path):
    """A bare mention in prose is not a localisation entry for the tag."""
    loc = write_path(
        tmp_path, "localisation/english/x.yml", 'x:0 "see TAG_A for details"\n'
    )

    assert (
        V.process_file_for_cosmetic_tag_in_loc((str(loc), frozenset({"TAG_A"}))) == {}
    )


def test_a_tag_named_in_two_files_is_reported_once(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/national_focus/a.txt",
        "has_cosmetic_tag = TAG_MISSING\nset_cosmetic_tag = TAG_SET_UNUSED\n",
    )
    write_path(
        tmp_path,
        "common/national_focus/b.txt",
        "has_cosmetic_tag = TAG_MISSING\nset_cosmetic_tag = TAG_SET_UNUSED\n",
    )

    validator = _run(tmp_path)
    by_category = {}
    for issue in validator._issues:
        by_category.setdefault(issue.category, []).append(issue)

    assert sorted(by_category) == ["missing-cosmetic-tag", "unused-cosmetic-tag"]
    assert len(by_category["missing-cosmetic-tag"]) == 1
    assert len(by_category["unused-cosmetic-tag"]) == 1
    assert by_category["missing-cosmetic-tag"][0].file in ("a.txt", "b.txt")


def test_a_flag_named_exactly_after_the_tag_counts_as_used(tmp_path, write_path):
    write_path(
        tmp_path, "common/national_focus/tags.txt", "set_cosmetic_tag = TAG_EXACT\n"
    )
    write_path(tmp_path, "gfx/flags/TAG_EXACT.tga", "")

    assert _categories(_run(tmp_path)) == []


def test_a_tag_referenced_only_in_script_needs_no_flag(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/national_focus/tags.txt",
        "set_cosmetic_tag = TAG_ONLY_TXT\nhas_cosmetic_tag = TAG_ONLY_TXT\n",
    )

    assert _categories(_run(tmp_path)) == []


def test_a_tag_referenced_only_in_localisation_counts_as_used(tmp_path, write_path):
    write_path(
        tmp_path, "common/national_focus/tags.txt", "set_cosmetic_tag = TAG_ONLY_LOC\n"
    )
    write_path(
        tmp_path,
        "localisation/english/tags_l_english.yml",
        'l_english:\nTAG_ONLY_LOC:0 "Loc Name"\n',
    )

    assert _categories(_run(tmp_path)) == []


def test_a_cosmetic_file_with_no_colour_definitions_is_a_clean_pass(
    tmp_path, write_path
):
    write_path(tmp_path, "common/countries/cosmetic.txt", "# no definitions yet\n")
    write_path(
        tmp_path,
        "common/national_focus/tags.txt",
        "set_cosmetic_tag = TAG_ONLY_TXT\nhas_cosmetic_tag = TAG_ONLY_TXT\n",
    )

    assert _categories(_run(tmp_path)) == []


def test_colour_definitions_on_the_false_positive_list_are_not_reported(
    tmp_path, write_path
):
    write_path(tmp_path, "common/countries/cosmetic.txt", "PER_REB = {\n}\n")

    assert _categories(_run(tmp_path)) == []


def test_staged_run_with_nothing_staged_skips(tmp_path, write_path, monkeypatch):
    write_path(
        tmp_path, "common/national_focus/tags.txt", "has_cosmetic_tag = TAG_MISSING\n"
    )
    monkeypatch.setenv("MD_STAGED_FILES", "")

    validator = _run(tmp_path, staged_only=True)

    assert validator._issues == []
    assert any("skipping cosmetic tags" in line for line in validator.output_lines)
