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
