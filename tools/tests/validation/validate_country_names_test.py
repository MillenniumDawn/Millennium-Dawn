"""Tests for `validate_country_names.py` (every tag has a names block)."""

import validate_country_names as V

DEFAULT_TAGS = 'AAA = "countries/A.txt"\nBBB = "countries/B.txt"\n'
NAME_BLOCK = "{name} = {{\n\tmale = {{\n\t\tnames = {{ X }}\n\t}}\n}}\n"
NAMES_AAA_ONLY = "default = {\n}\n" + NAME_BLOCK.format(name="AAA")
NAMES_BOTH = NAMES_AAA_ONLY + NAME_BLOCK.format(name="BBB")


def _write(tmp_path, write_path, tags=DEFAULT_TAGS, names=NAMES_BOTH):
    write_path(tmp_path, "common/country_tags/00_countries.txt", tags)
    write_path(tmp_path, "common/names/00_names.txt", names)


def test_reports_tag_without_names_block(tmp_path, write_path):
    _write(tmp_path, write_path, names=NAMES_AAA_ONLY)

    v = V.Validator(str(tmp_path))
    v.run_validations()

    assert len(v._issues) == 1
    issue = v._issues[0]
    assert issue.category == "country-names-missing"
    assert issue.file == "common/country_tags/00_countries.txt"
    assert issue.line == 2
    assert "'BBB'" in issue.message


def test_every_tag_named_is_clean(tmp_path, write_path):
    _write(tmp_path, write_path)

    v = V.Validator(str(tmp_path))
    v.run_validations()

    assert v._issues == []


def test_dynamic_tags_are_exempt(tmp_path, write_path):
    _write(tmp_path, write_path)
    write_path(
        tmp_path,
        "common/country_tags/zz_dynamic_countries.txt",
        'dynamic_tags = yes # any tags after this\nD01 = "countries/D01.txt"\n',
    )

    v = V.Validator(str(tmp_path))
    v.run_validations()

    assert v._issues == []


def test_commented_tag_is_ignored(tmp_path, write_path):
    tags = '#CCC = "countries/C.txt"\nAAA = "countries/A.txt"\n'
    _write(tmp_path, write_path, tags=tags, names=NAMES_AAA_ONLY)

    v = V.Validator(str(tmp_path))
    v.run_validations()

    assert v._issues == []


def test_empty_tree_is_clean(tmp_path):
    v = V.Validator(str(tmp_path))
    v.run_validations()

    assert v._issues == []


def test_staged_mode_skips_when_scope_untouched(tmp_path, write_path, monkeypatch):
    _write(tmp_path, write_path, names=NAMES_AAA_ONLY)
    write_path(tmp_path, "common/technologies/x.txt", "")
    monkeypatch.setenv("MD_STAGED_FILES", "common/technologies/x.txt")

    v = V.Validator(str(tmp_path), staged_only=True)
    v.run_validations()

    assert v._issues == []


def test_staged_mode_runs_when_names_file_staged(tmp_path, write_path, monkeypatch):
    _write(tmp_path, write_path, names=NAMES_AAA_ONLY)
    monkeypatch.setenv("MD_STAGED_FILES", "common/names/00_names.txt")

    v = V.Validator(str(tmp_path), staged_only=True)
    v.run_validations()

    assert len(v._issues) == 1


def test_names_tags_parser():
    assert V._names_tags("default = {\n}\nABC = {\n}\n\tXYZ = {\n}\n") == {"ABC"}
