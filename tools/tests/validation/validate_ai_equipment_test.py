"""Tests for validate_ai_equipment.py — blocked-nation role coverage and
duplicate template names across common/ai_equipment/ files.

A nation blocked from a generic role template with no custom/shared coverage
never produces designs for that role; duplicate template names mean the
last-loaded file silently wins.
"""

from validate_ai_equipment import Validator, parse_equipment_file


def _write_equipment(tmp_path, filename, body):
    equip_dir = tmp_path / "common" / "ai_equipment"
    equip_dir.mkdir(parents=True, exist_ok=True)
    path = equip_dir / filename
    path.write_text(body, encoding="utf-8")
    return path


def _template(name, role, extra=""):
    return (
        f"{name} = {{\n"
        "\tcategory = naval\n"
        f"\troles = {{ {role} }}\n"
        "\tpriority = 100\n"
        f"{extra}"
        "}\n"
    )


def _run(tmp_path):
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return validator


def test_parse_equipment_file_extracts_template_fields(tmp_path):
    path = _write_equipment(
        tmp_path,
        "generic_naval.txt",
        _template(
            "generic_destroyer", "naval_destroyer", "\tblocked_for = { USA ENG }\n"
        ),
    )
    templates = parse_equipment_file(str(path))
    assert len(templates) == 1
    t = templates[0]
    assert t["name"] == "generic_destroyer"
    assert t["category"] == "naval"
    assert t["roles"] == {"naval_destroyer"}
    assert t["blocked_for"] == {"USA", "ENG"}
    assert t["available_for"] == set()


def test_blocked_nation_without_coverage_flagged(tmp_path):
    _write_equipment(
        tmp_path,
        "generic_naval.txt",
        _template("generic_destroyer", "naval_destroyer", "\tblocked_for = { USA }\n"),
    )
    validator = _run(tmp_path)
    assert validator.errors_found == 1
    message = validator._issues[0].message
    assert "USA" in message
    assert "naval_destroyer" in message


def test_available_for_coverage_clears(tmp_path):
    _write_equipment(
        tmp_path,
        "generic_naval.txt",
        _template("generic_destroyer", "naval_destroyer", "\tblocked_for = { USA }\n"),
    )
    _write_equipment(
        tmp_path,
        "shared_western_naval.txt",
        _template(
            "western_destroyer", "naval_destroyer", "\tavailable_for = { USA }\n"
        ),
    )
    validator = _run(tmp_path)
    assert validator.errors_found == 0
    assert validator._issues == []


def test_nation_specific_filename_infers_coverage(tmp_path):
    """A custom file with no available_for covers the tag named by its
    filename prefix (usa_naval.txt -> USA)."""
    _write_equipment(
        tmp_path,
        "generic_naval.txt",
        _template("generic_destroyer", "naval_destroyer", "\tblocked_for = { USA }\n"),
    )
    _write_equipment(
        tmp_path,
        "usa_naval.txt",
        _template("usa_destroyer", "naval_destroyer"),
    )
    validator = _run(tmp_path)
    assert validator.errors_found == 0


def test_duplicate_template_names_flagged(tmp_path):
    _write_equipment(
        tmp_path, "generic_naval.txt", _template("destroyer_role", "naval_destroyer")
    )
    _write_equipment(
        tmp_path, "usa_naval.txt", _template("destroyer_role", "naval_destroyer")
    )
    validator = _run(tmp_path)
    assert validator.errors_found == 1
    message = validator._issues[0].message
    assert "destroyer_role" in message
    assert "generic_naval.txt" in message
    assert "usa_naval.txt" in message


def test_templates_without_a_category_or_roles_are_skipped(tmp_path):
    path = _write_equipment(
        tmp_path,
        "generic_naval.txt",
        "default_priority = 50\n"
        "roles_only = {\n\troles = { naval_destroyer }\n}\n"
        "category_only = {\n\tcategory = naval\n}\n"
        + _template("real_template", "naval_destroyer"),
    )

    assert [t["name"] for t in parse_equipment_file(str(path))] == ["real_template"]


def test_unreadable_equipment_file_yields_no_templates(tmp_path):
    assert parse_equipment_file(str(tmp_path / "gone.txt")) == []


def test_custom_file_without_a_three_letter_prefix_covers_nothing(tmp_path):
    _write_equipment(
        tmp_path,
        "generic_naval.txt",
        _template("generic_destroyer", "naval_destroyer", "\tblocked_for = { USA }\n"),
    )
    _write_equipment(
        tmp_path,
        "shared_western_naval.txt",
        _template("western_destroyer", "naval_destroyer"),
    )

    validator = _run(tmp_path)

    assert [i.message for i in validator._issues] == [
        "USA: blocked from generic 'naval_destroyer' but has no custom coverage"
    ]


def test_unreadable_design_file_is_reported_and_skipped(tmp_path, caplog):
    import logging

    _write_equipment(
        tmp_path, "usa_naval.txt", _template("usa_destroyer", "naval_destroyer")
    )
    (tmp_path / "common" / "ai_equipment" / "broken.txt").mkdir()

    with caplog.at_level(logging.WARNING):
        validator = _run(tmp_path)

    assert "broken.txt" in caplog.text
    assert validator._issues == []


_HISTORY_GROUP = """TST_navy = {
\tcategory = naval
\troles = { naval_destroyer }
\tTST_marked = {
\t\thistory = yes
\t\ttarget_variant = {
\t\t\ttype = no_such_hull
\t\t\tmodules = {
\t\t\t\tfixed_ship_battery_slot = module_test_gun
\t\t\t}
\t\t}
\t}
\tTST_unmarked = {
\t\ttarget_variant = {
\t\t\ttype = no_such_hull
\t\t\tmodules = {
\t\t\t\tfixed_ship_battery_slot = module_test_gun
\t\t\t}
\t\t}
\t}
}
"""


def _staged_repo(tmp_path, write_path):
    write_path(tmp_path, "common/units/equipment/MD_hulls.txt", "equipments = { }\n")
    _write_equipment(tmp_path, "tst_naval.txt", _HISTORY_GROUP)
    _write_equipment(
        tmp_path, "usa_naval.txt", _template("usa_destroyer", "naval_destroyer")
    )


def test_staged_run_without_ai_equipment_files_skips_every_check(
    tmp_path, write_path, monkeypatch
):
    _staged_repo(tmp_path, write_path)
    write_path(tmp_path, "common/ideas/unrelated.txt", "ideas = { }\n")
    monkeypatch.setenv("MD_STAGED_FILES", "common/ideas/unrelated.txt")

    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, staged_only=True, workers=1
    )
    validator.run_validations()

    assert validator._issues == []


def test_staged_run_checks_only_the_staged_equipment_file(
    tmp_path, write_path, monkeypatch
):
    _staged_repo(tmp_path, write_path)
    monkeypatch.setenv("MD_STAGED_FILES", "common/ai_equipment/usa_naval.txt")

    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, staged_only=True, workers=1
    )
    validator.run_validations()

    assert validator._issues == []


def test_partial_history_and_unknown_hull_are_reported_in_a_full_run(
    tmp_path, write_path
):
    _staged_repo(tmp_path, write_path)

    validator = _run(tmp_path)
    categories = sorted(i.category for i in validator._issues)

    assert categories == [
        "AI EQUIPMENT: partial history = yes",
        "EQUIPMENT VARIANT: unknown hull type",
        "EQUIPMENT VARIANT: unknown hull type",
    ]
