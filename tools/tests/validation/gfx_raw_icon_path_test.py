"""Raw texture paths in unit-icon sites must fail closed.

create_equipment_variant `icon =` and graphic_db `icons = { }` entries have to
be GFX_ sprites. A raw .dds path on a plane icon crashes the macOS air battle
window. Quoted, unquoted, and backslash forms all count; comments and
focus-tree `icon =` values do not.
"""

import pytest
import validate_gfx_references as vg
from shared.suite import run_validator, write_under
from validate_gfx_references import Validator as GfxReferenceValidator
from validator_common import Severity

HISTORY = "history/countries/SOV.txt"
GRAPHIC_DB = "gfx/interface/equipmentdesigner/graphic_db/00.txt"
RAW_POOL = (
    "pool = {\n"
    "\ticons = {\n"
    "\t\tGFX_OK\n"
    '\t\t"GFX_OK_QUOTED"\n'
    '\t\t"gfx/interface/technologies/gwtank.dds"\n'
    "\t\tgfx/interface/technologies/Su-57.dds\n"
    "\t}\n"
    "\tmodels = {\n"
    '\t\t"gfx/should_not_flag.dds"\n'
    "\t}\n"
    "}\n"
)


@pytest.fixture(autouse=True)
def _no_vanilla_install(no_vanilla_gfx):
    return no_vanilla_gfx


def _variant(icon, name="Su-57"):
    return f'create_equipment_variant = {{\n\tname = "{name}"\n\ticon = {icon}\n}}\n'


def _raw_icon_issues(validator):
    return [i for i in validator._issues if i.category == "raw-icon-path"]


@pytest.mark.parametrize(
    "icon",
    [
        '"gfx/interface/technologies/SOV/AIR/foo.dds"',
        "gfx/interface/technologies/SOV/AIR/bar.dds",
        '"gfx\\interface\\technologies\\SOV\\AIR\\baz.dds"',
        "gfx\\interface\\technologies\\SOV\\AIR\\qux.dds",
        "lone.dds",
    ],
)
def test_raw_variant_icon_is_flagged_on_its_line(icon):
    assert vg.raw_variant_icon_paths(_variant(icon)) == [(icon.strip('"'), 3)]


@pytest.mark.parametrize(
    "text",
    [
        _variant('"GFX_SOV_AIR_ok"'),
        _variant("GFX_SOV_AIR_ok_bare"),
        "focus = {\n\ticon = gfx/interface/goals/bad.dds\n}\n",
        'create_equipment_variant = {\n\t#icon = "gfx/commented.dds"\n}\n',
    ],
)
def test_sprite_focus_and_commented_icons_are_ignored(text):
    assert vg.raw_variant_icon_paths(text) == []


def test_hash_inside_a_quoted_name_does_not_hide_the_icon():
    text = _variant("gfx/a.dds", name="Batch #1") + _variant("gfx/b.dds")
    assert vg.raw_variant_icon_paths(text) == [("gfx/a.dds", 3), ("gfx/b.dds", 7)]


def test_graphic_db_icons_flag_paths_and_ignore_models():
    assert vg.raw_graphic_db_icon_paths(RAW_POOL) == [
        ("gfx/interface/technologies/gwtank.dds", 5),
        ("gfx/interface/technologies/Su-57.dds", 6),
    ]


@pytest.mark.parametrize(
    "relative_path, body, line",
    [
        (HISTORY, _variant("gfx/interface/technologies/SOV/AIR/Su-57.dds"), 3),
        (
            GRAPHIC_DB,
            RAW_POOL.replace('\t\t"gfx/interface/technologies/gwtank.dds"\n', ""),
            5,
        ),
    ],
)
def test_run_reports_a_raw_icon_path_as_an_error(tmp_path, relative_path, body, line):
    write_under(tmp_path, relative_path, body)

    (issue,) = _raw_icon_issues(run_validator(GfxReferenceValidator, tmp_path))

    assert issue.severity == Severity.ERROR
    assert "Su-57.dds" in issue.message
    assert (issue.file.replace("\\", "/"), issue.line) == (relative_path, line)


def test_run_accepts_sprite_icons(tmp_path):
    write_under(tmp_path, HISTORY, _variant('"GFX_SOV_AIR_Su_57"'))
    write_under(
        tmp_path, GRAPHIC_DB, "pool = {\n\ticons = {\n\t\tGFX_SOV_AIR_Su_57\n\t}\n}\n"
    )
    assert _raw_icon_issues(run_validator(GfxReferenceValidator, tmp_path)) == []


def test_staged_run_checks_only_staged_graphic_db_files(tmp_path):
    staged = write_under(tmp_path, GRAPHIC_DB, RAW_POOL)
    write_under(tmp_path, GRAPHIC_DB.replace("00.txt", "01.txt"), RAW_POOL)
    validator = GfxReferenceValidator(
        str(tmp_path), use_colors=False, workers=1, no_cache=True
    )
    validator.staged_only = True
    validator.staged_files = [str(staged)]

    validator.run_validations()

    assert {i.file.replace("\\", "/") for i in _raw_icon_issues(validator)} == {
        GRAPHIC_DB
    }
