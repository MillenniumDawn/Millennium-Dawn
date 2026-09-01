"""Tests for the opt-in gate on the unused-sprite check.

The unused-sprite report is ~6.7k findings on a full repo, so a default run (and
CI) must skip it entirely — including the script ref collection that feeds only
it. `--report-unused` turns it back on, and `MD_GFX_HIDE_UNUSED` suppresses just
the orphan list so the case and duplicate findings shipped alongside it are
readable. The localisation scan is NOT gated: it also feeds the £ref case check,
which reports real Linux breakage on every run.
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
    v.run_validations()
    assert not _unused(v)


def test_report_unused_run_reports_unused_sprite(tmp_path):
    v = GfxReferenceValidator(_mod_path(tmp_path), use_colors=False, report_unused=True)
    v.run_validations()
    assert [i for i in _unused(v) if "GFX_never_referenced" in i.message]


def test_hide_unused_env_suppresses_the_orphan_list(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_GFX_HIDE_UNUSED", "1")
    v = GfxReferenceValidator(_mod_path(tmp_path), use_colors=False, report_unused=True)
    v.run_validations()
    assert not _unused(v)


def test_hide_unused_env_off_value_keeps_the_orphan_list(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_GFX_HIDE_UNUSED", "0")
    v = GfxReferenceValidator(_mod_path(tmp_path), use_colors=False, report_unused=True)
    v.run_validations()
    assert [i for i in _unused(v) if "GFX_never_referenced" in i.message]
