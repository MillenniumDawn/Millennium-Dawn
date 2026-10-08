"""Tests for validate_cosmetic_tags (missing, unused, and unused-colour checks)."""

import pytest
import validate_cosmetic_tags as V
from shared.suite import issue_categories as _categories
from shared.suite import run_validator


def _run(tmp_path, **kwargs):
    return run_validator(V.Validator, tmp_path, **kwargs)


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


def test_a_meta_effect_placeholder_is_not_a_cosmetic_tag(tmp_path, write_path):
    """`set_cosmetic_tag = [ROOTTAG]_AUTH` names a substitution, not a tag."""
    write_path(
        tmp_path,
        "common/decisions/flags.txt",
        "set_cosmetic_tag = [ROOTTAG]_AUTH\nset_cosmetic_tag = [ROOTTAG]\n",
    )

    assert _categories(_run(tmp_path)) == []


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


def _rows(validator):
    return [(i.category, i.message, i.file, i.line) for i in validator._issues]


def test_set_tag_counts_match_a_per_tag_count_on_every_site_shape(tmp_path, write_path):
    path = write_path(
        tmp_path,
        "common/national_focus/sites.txt",
        "set_cosmetic_tag = ABC_long\r\n"
        "# set_cosmetic_tag = ABC_commented\r\n"
        'log = "# { set_cosmetic_tag = ABC_quoted"\r\n'
        "set_cosmetic_tag = abcset_cosmetic_tag = abcset_cosmetic_tag = abc\r\n"
        "set_cosmetic_tag = ABC",
    )
    tags = ["A", "AB", "ABC", "ABC_long", "ABC_commented", "ABC_quoted", "abc"]
    tags += ["abcset_cos", "MISSING"]
    text = V.FileOpener.open_text_file(str(path), strip_comments_flag=True)

    counts = V.process_file_for_set_cosmetic_tag((str(path), False, tags))

    assert counts == {
        "A": 3,
        "AB": 3,
        "ABC": 3,
        "ABC_long": 1,
        "ABC_quoted": 1,
        "abc": 3,
        "abcset_cos": 1,
    }
    assert counts == {
        tag: text.count(f"set_cosmetic_tag = {tag}")
        for tag in tags
        if f"set_cosmetic_tag = {tag}" in text
    }


@pytest.mark.parametrize(
    ("body", "found"),
    [
        (' TAG_A.B_democratic:0 "x"\r\n', {"TAG_A.B": 1}),
        (' TAG_(X):0 "y"\r\n', {"TAG_(X)": 1}),
        (' TAG_LAST:0 "z"', {"TAG_LAST": 1}),
        ('# TAG_GONE:0 "c"\r\n TAG_AxB_:0 "d"\r\n', {}),
    ],
)
def test_loc_gate_lets_each_present_tag_through(tmp_path, write_path, body, found):
    loc = write_path(
        tmp_path, "localisation/english/tags_l_english.yml", "l_english:\r\n" + body
    )
    tags = frozenset({"TAG_A.B", "TAG_(X)", "TAG_LAST", "TAG_GONE"})

    assert V.process_file_for_cosmetic_tag_in_loc((str(loc), tags)) == found


def test_staged_missing_check_still_finds_setters_in_unstaged_files(
    tmp_path, write_path, monkeypatch
):
    write_path(
        tmp_path,
        "common/national_focus/staged.txt",
        "has_cosmetic_tag = TAG_SET_ELSEWHERE\nhas_cosmetic_tag = TAG_NEVER_SET\n",
    )
    write_path(
        tmp_path,
        "common/national_focus/other.txt",
        "set_cosmetic_tag = TAG_SET_ELSEWHERE\n",
    )
    monkeypatch.setenv("MD_STAGED_FILES", "common/national_focus/staged.txt")

    validator = _run(tmp_path, staged_only=True)

    assert _rows(validator) == [
        ("missing-cosmetic-tag", "TAG_NEVER_SET", "staged.txt", 0)
    ]


def _tag_tree(tmp_path, write_path, files=1):
    write_path(
        tmp_path,
        "common/countries/cosmetic.txt",
        "TAG_COLOUR_USED = {\n}\nTAG_COLOUR_IDLE = {\n}\n",
    )
    for index in range(files):
        write_path(
            tmp_path,
            f"common/national_focus/f{index:02}.txt",
            f"has_cosmetic_tag = TAG_HAS_{index:02}\n"
            "set_cosmetic_tag = TAG_COLOUR_USED\n",
        )


def test_a_full_run_walks_the_script_tree_once(tmp_path, write_path, monkeypatch):
    _tag_tree(tmp_path, write_path)
    patterns = []
    collect = V.Validator._collect_files

    def counting_collect(self, globs, *args, **kwargs):
        patterns.append(tuple(globs))
        return collect(self, globs, *args, **kwargs)

    monkeypatch.setattr(V.Validator, "_collect_files", counting_collect)

    validator = _run(tmp_path)

    assert patterns == [("**/*.txt",)]
    assert _rows(validator) == [
        ("missing-cosmetic-tag", "TAG_HAS_00", "f00.txt", 0),
        ("unused-cosmetic-color", "TAG_COLOUR_IDLE", "", 0),
    ]


def test_pooled_run_matches_the_in_process_run(
    tmp_path, write_path, monkeypatch, pool_sizes
):
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    _tag_tree(tmp_path, write_path, files=12)

    def run(workers):
        validator = V.Validator(
            mod_path=str(tmp_path), use_colors=False, workers=workers, no_cache=True
        )
        validator.run_all_validations()
        return _rows(validator)

    pooled = run(2)
    assert pool_sizes == [2]
    assert pooled == run(1)
    assert sorted(pooled) == [
        ("missing-cosmetic-tag", f"TAG_HAS_{index:02}", f"f{index:02}.txt", 0)
        for index in range(12)
    ] + [("unused-cosmetic-color", "TAG_COLOUR_IDLE", "", 0)]


def test_staged_run_with_nothing_staged_skips(tmp_path, write_path, monkeypatch):
    write_path(
        tmp_path, "common/national_focus/tags.txt", "has_cosmetic_tag = TAG_MISSING\n"
    )
    monkeypatch.setenv("MD_STAGED_FILES", "")

    validator = _run(tmp_path, staged_only=True)

    assert validator._issues == []
    assert any("skipping cosmetic tags" in line for line in validator.output_lines)
