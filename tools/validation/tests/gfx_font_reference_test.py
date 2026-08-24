"""Tests for the undefined-font check in validate_gfx_references.

A .gui `font = "x"` that names no bitmapfont logs "No font with name x" and the
text box falls back to the engine default face, so the layout drifts silently.
"""

import pytest
import validate_gfx_references as vg
from validate_gfx_references import Validator as GfxReferenceValidator
from validate_gfx_references import font_names_from_gfx_text


@pytest.fixture(autouse=True)
def _no_vanilla_install(monkeypatch):
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_sprite_manifest", lambda: frozenset())
    monkeypatch.setattr(
        vg, "_load_vanilla_font_manifest", lambda: frozenset({"vic_18"})
    )
    monkeypatch.setattr(vg, "_vanilla_gui_ref_index", lambda: {})


_CORE_GFX = (
    "bitmapfonts = {\n"
    "\tbitmapfont = {\n"
    '\t\tname = "hoi_16mbs"\n'
    '\t\tfontfiles = { "gfx/fonts/hoi_16mbs.fnt" }\n'
    "\t}\n"
    "\tbitmapfont = {\n"
    '\t\tname = "hoi_18b"\n'
    "\t}\n"
    "}\n"
)


def test_font_names_parsed_from_gfx_text():
    assert font_names_from_gfx_text(_CORE_GFX) == {"hoi_16mbs", "hoi_18b"}


def test_commented_out_font_is_not_defined():
    raw = 'bitmapfonts = {\n#\tbitmapfont = {\n#\t\tname = "ub_16bs"\n#\t}\n}\n'
    assert font_names_from_gfx_text(raw) == set()


def _run(tmp_path, gui_text):
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "core.gfx").write_text(_CORE_GFX, encoding="utf-8")
    (interface / "view.gui").write_text(gui_text, encoding="utf-8")
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v.run_validations()
    return [i for i in v._issues if i.category == "undefined-font"]


def test_undefined_font_is_reported(tmp_path):
    issues = _run(tmp_path, 'instantTextBoxType = {\n\tfont = "hoi_16"\n}\n')
    assert len(issues) == 1
    assert 'font = "hoi_16"' in issues[0].message


def test_declared_font_is_not_reported(tmp_path):
    assert _run(tmp_path, 'instantTextBoxType = {\n\tfont = "hoi_16mbs"\n}\n') == []


def test_vanilla_font_from_manifest_is_not_reported(tmp_path):
    assert _run(tmp_path, 'instantTextBoxType = {\n\tfont = "vic_18"\n}\n') == []


def test_commented_out_reference_is_not_reported(tmp_path):
    assert _run(tmp_path, '#\tfont = "hoi_16"\n') == []
