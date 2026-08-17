"""Tests for the opt-in gate on the unused-sprite check.

The unused-sprite report is ~10k findings on a full repo, so a default run (and
CI) must skip it entirely — including the script/localisation ref collection
that feeds only it. `--report-unused` turns it back on.
"""

import pytest
import validate_gfx_references as vg
from validate_gfx_references import Validator as GfxReferenceValidator

GFX_FIXTURE = (
    "spriteType = {\n"
    '\tname = "GFX_never_referenced"\n'
    '\ttexturefile = "gfx//interface/never_referenced.dds"\n'
    "}\n"
)


@pytest.fixture(autouse=True)
def _no_vanilla_install(monkeypatch):
    # Keep the run inside tmp_path: no vanilla .gfx/.gui scan, no manifest.
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_sprite_manifest", lambda: frozenset())
    monkeypatch.setattr(vg, "_vanilla_gui_ref_index", lambda: {})


def _mod_path(tmp_path):
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "test.gfx").write_text(GFX_FIXTURE, encoding="utf-8")
    return str(tmp_path)


def _unused(validator):
    return [i for i in validator._issues if i.category == "unused-sprite"]


def test_report_unused_defaults_to_false(tmp_path):
    v = GfxReferenceValidator(_mod_path(tmp_path), use_colors=False)
    assert v.report_unused is False


def test_default_run_skips_unused_check(tmp_path, monkeypatch):
    v = GfxReferenceValidator(_mod_path(tmp_path), use_colors=False)
    monkeypatch.setattr(
        v, "_collect_script_refs", lambda: pytest.fail("script refs collected")
    )
    monkeypatch.setattr(
        v, "_collect_loc_refs", lambda: pytest.fail("loc refs collected")
    )
    v.run_validations()
    assert not _unused(v)


def test_report_unused_run_reports_unused_sprite(tmp_path):
    v = GfxReferenceValidator(_mod_path(tmp_path), use_colors=False, report_unused=True)
    v.run_validations()
    assert [i for i in _unused(v) if "GFX_never_referenced" in i.message]
