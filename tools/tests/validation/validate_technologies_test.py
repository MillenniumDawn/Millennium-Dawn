"""Tests for `validate_technologies.py` (tech category consistency)."""

import validate_technologies as V

FIXTURE = """technologies = {
\tfoo_1 = {
\t\tcategories = {
\t\t\tCAT_a
\t\t\tCAT_b
\t\t}
\t\tpath = {
\t\t\tleads_to_tech = foo_2
\t\t\tresearch_cost_coeff = 1
\t\t}
\t}
\tfoo_2 = {
\t\tcategories = {
\t\t\tCAT_a
\t\t}
\t}
\tbar_1 = {
\t\tcategories = {
\t\t\tCAT_x
\t\t}
\t\tpath = {
\t\t\tleads_to_tech = baz_1
\t\t\tresearch_cost_coeff = 1
\t\t}
\t}
\tbaz_1 = {
\t\tcategories = {
\t\t\tCAT_y
\t\t}
\t}
}
"""


def _write_fixture(tmp_path):
    tech_dir = tmp_path / "common" / "technologies"
    tech_dir.mkdir(parents=True)
    (tech_dir / "test.txt").write_text(FIXTURE, encoding="utf-8")


def test_same_family_missing_category_flagged(tmp_path):
    _write_fixture(tmp_path)
    v = V.Validator(str(tmp_path))
    v.run_validations()
    assert len(v._issues) == 1
    issue = v._issues[0]
    assert issue.category == "category-missing"
    assert "foo_2" in issue.message
    assert "CAT_b" in issue.message
    assert issue.file.endswith("test.txt")


def test_different_family_branch_not_flagged(tmp_path):
    _write_fixture(tmp_path)
    v = V.Validator(str(tmp_path))
    v.run_validations()
    assert not any("baz_1" in i.message for i in v._issues)


def test_stem():
    assert V.stem("gen_4_large") == V.stem("gen_3_large")
    assert V.stem("nsb_engine_tech_6") == V.stem("nsb_engine_tech_5")
    assert V.stem("AA_upgrade_1") != V.stem("Anti_Air_0")
    assert V.stem("countermeasures_1") != V.stem("air_weapons_1")


def test_no_tech_dir_is_a_clean_pass(tmp_path):
    v = V.Validator(str(tmp_path))
    v.run_validations()
    assert v._issues == []


def test_unreadable_tech_file_is_skipped(tmp_path):
    _write_fixture(tmp_path)
    (tmp_path / "common" / "technologies" / "broken.txt").mkdir()

    v = V.Validator(str(tmp_path))
    v.run_validations()

    assert [i.message for i in v._issues if "CAT_b" in i.message]


def test_staged_mode_reports_only_staged_files(tmp_path, monkeypatch):
    _write_fixture(tmp_path)
    other = tmp_path / "common" / "technologies" / "other.txt"
    other.write_text("technologies = {\n\tqux_1 = {\n\t}\n}\n", encoding="utf-8")
    monkeypatch.setenv("MD_STAGED_FILES", "common/technologies/other.txt")

    v = V.Validator(str(tmp_path), staged_only=True)
    v.run_validations()

    assert v._issues == []


def test_staged_mode_still_reports_the_staged_file(tmp_path, monkeypatch):
    _write_fixture(tmp_path)
    monkeypatch.setenv("MD_STAGED_FILES", "common/technologies/test.txt")

    v = V.Validator(str(tmp_path), staged_only=True)
    v.run_validations()

    assert [i.category for i in v._issues] == ["category-missing"]


def test_path_for_scans_every_file_and_falls_back_to_empty():
    file_techs = {"a.txt": ["one"], "b.txt": ["two"]}
    assert V._path_for("two", file_techs) == "b.txt"
    assert V._path_for("missing", file_techs) == ""
