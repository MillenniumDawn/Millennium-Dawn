"""Raw texture paths in unit-icon sites must fail closed.

create_equipment_variant `icon =` and graphic_db `icons = { }` entries have to
be GFX_ sprites. A raw .dds path on a plane icon crashes the macOS air battle
window. Quoted, unquoted, and backslash forms all count; comments and
focus-tree `icon =` values do not.
"""

from pathlib import Path

import pytest
import validate_gfx_references as vg
from validate_gfx_references import Validator as GfxReferenceValidator
from validator_common import Severity


@pytest.fixture(autouse=True)
def _no_vanilla_install(no_vanilla_gfx):
    return no_vanilla_gfx


def _categories(validator, category):
    return [i for i in validator._issues if i.category == category]


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _run(tmp_path):
    _write(tmp_path / "interface" / "empty.gfx", "spriteTypes = {\n}\n")
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return validator


def test_quoted_and_plain_variant_icon_paths_are_flagged():
    text = (
        "create_equipment_variant = {\n"
        '\ticon = "gfx/interface/technologies/SOV/AIR/foo.dds"\n'
        "}\n"
        "create_equipment_variant = {\n"
        "\ticon = gfx/interface/technologies/SOV/AIR/bar.dds\n"
        "}\n"
        "create_equipment_variant = {\n"
        '\ticon = "gfx\\interface\\technologies\\SOV\\AIR\\baz.dds"\n'
        "}\n"
        "create_equipment_variant = {\n"
        "\ticon = gfx\\interface\\technologies\\SOV\\AIR\\qux.dds\n"
        "}\n"
        "create_equipment_variant = {\n"
        "\ticon = lone.dds\n"
        "}\n"
        "create_equipment_variant = {\n"
        '\ticon = "GFX_SOV_AIR_ok"\n'
        "}\n"
        "create_equipment_variant = {\n"
        "\ticon = GFX_SOV_AIR_ok_bare\n"
        "}\n"
        "focus = {\n"
        "\ticon = gfx/interface/goals/bad.dds\n"
        "}\n"
        "#icon = gfx/interface/technologies/SOV/AIR/commented.dds\n"
    )
    values = [value for value, _line in vg.raw_variant_icon_paths(text)]
    assert "gfx/interface/technologies/SOV/AIR/foo.dds" in values
    assert "gfx/interface/technologies/SOV/AIR/bar.dds" in values
    assert r"gfx\interface\technologies\SOV\AIR\baz.dds" in values
    assert r"gfx\interface\technologies\SOV\AIR\qux.dds" in values
    assert "lone.dds" in values
    assert "GFX_SOV_AIR_ok" not in values
    assert "GFX_SOV_AIR_ok_bare" not in values
    assert "gfx/interface/goals/bad.dds" not in values
    assert not any("commented.dds" in value for value in values)


def test_graphic_db_icons_flag_paths_and_ignore_models():
    text = (
        "pool = {\n"
        "\ticons = {\n"
        "\t\tGFX_OK\n"
        '\t\t"GFX_OK_QUOTED"\n'
        '\t\t"gfx/interface/technologies/gwtank.dds"\n'
        "\t\tgfx/interface/technologies/plain.dds\n"
        "\t}\n"
        "\tmodels = {\n"
        '\t\t"gfx/should_not_flag.dds"\n'
        "\t}\n"
        "}\n"
    )
    values = [value for value, _line in vg.raw_graphic_db_icon_paths(text)]
    assert "gfx/interface/technologies/gwtank.dds" in values
    assert "gfx/interface/technologies/plain.dds" in values
    assert "GFX_OK" not in values
    assert "GFX_OK_QUOTED" not in values
    assert "gfx/should_not_flag.dds" not in values


def test_run_validations_flags_plain_variant_icon(tmp_path):
    _write(
        tmp_path / "history" / "countries" / "SOV.txt",
        "create_equipment_variant = {\n"
        '\tname = "Su-57"\n'
        "\ticon = gfx/interface/technologies/SOV/AIR/Su-57.dds\n"
        "}\n",
    )
    issues = _categories(_run(tmp_path), "raw-icon-path")
    assert len(issues) == 1
    assert issues[0].severity == Severity.ERROR
    assert "Su-57.dds" in issues[0].message
    assert issues[0].file.replace("\\", "/").endswith("history/countries/SOV.txt")


def test_run_validations_flags_graphic_db_plain_path(tmp_path):
    _write(
        tmp_path / "gfx" / "interface" / "equipmentdesigner" / "graphic_db" / "00.txt",
        "pool = {\n"
        "\ticons = {\n"
        "\t\tGFX_OK\n"
        "\t\tgfx/interface/technologies/plain.dds\n"
        "\t}\n"
        "}\n",
    )
    issues = _categories(_run(tmp_path), "raw-icon-path")
    assert len(issues) == 1
    assert "plain.dds" in issues[0].message
    assert "graphic_db" in issues[0].file.replace("\\", "/")


def test_run_validations_accepts_sprite_icons(tmp_path):
    _write(
        tmp_path / "history" / "countries" / "SOV.txt",
        "create_equipment_variant = {\n"
        '\tname = "Su-57"\n'
        '\ticon = "GFX_SOV_AIR_Su_57"\n'
        "}\n",
    )
    _write(
        tmp_path / "gfx" / "interface" / "equipmentdesigner" / "graphic_db" / "00.txt",
        "pool = {\n\ticons = {\n\t\tGFX_SOV_AIR_Su_57\n\t}\n}\n",
    )
    assert _categories(_run(tmp_path), "raw-icon-path") == []
