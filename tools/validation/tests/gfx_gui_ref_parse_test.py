"""Tests for case-insensitive and unquoted .gui sprite refs.

HOI4 accepts spriteType / quadTextureSprite / background in any case, quoted or
bare. The unused-sprite check only sees what _GUI_REF collects, so a missed
casing (quadtexturesprite = "GFX_Bundeswehr_bar") false-positives a live sprite.
"""

import pytest
import validate_gfx_references as vg
from validate_gfx_references import Validator as GfxReferenceValidator
from validate_gfx_references import _parse_gui_file


@pytest.fixture(autouse=True)
def _no_vanilla_install(monkeypatch):
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_sprite_manifest", lambda: frozenset())
    monkeypatch.setattr(vg, "_vanilla_gui_ref_index", lambda: {})


def _names(gui, tmp_path):
    return [name for name, _file, _line in _parse_gui_file((str(gui), str(tmp_path)))]


def test_parse_gui_accepts_lowercase_quadtexturesprite(tmp_path):
    gui = tmp_path / "german_bundeswehr_reform.gui"
    gui.write_text(
        'quadtexturesprite = "GFX_Bundeswehr_bar"\n'
        'spritetype = "GFX_PER_propaganda_progress_frame"\n',
        encoding="utf-8",
    )
    assert _names(gui, tmp_path) == [
        "GFX_Bundeswehr_bar",
        "GFX_PER_propaganda_progress_frame",
    ]


def test_parse_gui_accepts_pascal_sprite_type(tmp_path):
    gui = tmp_path / "view.gui"
    gui.write_text('SpriteType = "GFX_resources_bg"\n', encoding="utf-8")
    assert _names(gui, tmp_path) == ["GFX_resources_bg"]


def test_parse_gui_accepts_unquoted_name(tmp_path):
    gui = tmp_path / "market.gui"
    gui.write_text(
        "spriteType = GFX_button_94x31\n"
        "quadTextureSprite = GFX_faction_theater_background\n",
        encoding="utf-8",
    )
    assert _names(gui, tmp_path) == [
        "GFX_button_94x31",
        "GFX_faction_theater_background",
    ]


def test_parse_gui_still_accepts_camel_quoted(tmp_path):
    gui = tmp_path / "ok.gui"
    gui.write_text(
        'spriteType = "GFX_closebutton"\n'
        'quadTextureSprite = "GFX_button_123x34"\n'
        'background = "GFX_tiled_plain_bg"\n',
        encoding="utf-8",
    )
    assert _names(gui, tmp_path) == [
        "GFX_closebutton",
        "GFX_button_123x34",
        "GFX_tiled_plain_bg",
    ]


def test_parse_gui_does_not_collect_lowercase_gfx_prefix(tmp_path):
    gui = tmp_path / "vanilla.gui"
    gui.write_text('quadTextureSprite = "gfx_transparency_white"\n', encoding="utf-8")
    assert _names(gui, tmp_path) == []


def test_parse_gui_skips_dynamic_quoted_name(tmp_path):
    gui = tmp_path / "dyn.gui"
    gui.write_text(
        'spriteType = "GFX_missile_[THIS.GetTag]_icon"\n',
        encoding="utf-8",
    )
    assert _names(gui, tmp_path) == []


def test_lowercase_quadtexturesprite_is_not_unused(tmp_path):
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "bars.gfx").write_text(
        "progressbartype = {\n"
        '\tname = "GFX_Bundeswehr_bar"\n'
        '\ttexturefile1 = "gfx/interface/ger_bundeswehr_recovery.dds"\n'
        "}\n",
        encoding="utf-8",
    )
    (interface / "german_bundeswehr_reform.gui").write_text(
        'quadtexturesprite = "GFX_Bundeswehr_bar"\n',
        encoding="utf-8",
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False, report_unused=True)
    v.run_validations()
    assert not [i for i in v._issues if "GFX_Bundeswehr_bar" in i.message]
