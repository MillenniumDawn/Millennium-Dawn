"""Tests for the case-sensitivity and duplicate-definition checks.

Case mismatches are split across two parts of the validator because they are two
different bugs. `_check_loc_ref_case` catches a `£ref` whose spelling matches no
sprite (the icon is simply gone on Linux); `_check_unused_sprites` tags a sprite
whose only reference is miscased, so an archive sweep does not delete live art.

`_check_duplicate_definitions` covers the third shape: one name defined twice
(engine load order decides), or two names differing only in case, which is how a
Windows author ends up with the split in the first place.
"""

import os

import pytest
import validate_gfx_references as vg
from validate_gfx_references import Validator as GfxReferenceValidator


@pytest.fixture(autouse=True)
def _no_vanilla_install(monkeypatch):
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_sprite_manifest", lambda: frozenset())
    monkeypatch.setattr(vg, "_vanilla_gui_ref_index", lambda: {})


def _sprite(name, texture):
    return (
        f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{texture}"\n\t}}\n'
    )


def _write_gfx(tmp_path, filename, *blocks):
    interface = tmp_path / "interface"
    interface.mkdir(exist_ok=True)
    (interface / filename).write_text(
        "spriteTypes = {\n" + "".join(blocks) + "}\n", encoding="utf-8"
    )


def _write_loc(tmp_path, language, filename, body):
    loc = tmp_path / "localisation" / language
    loc.mkdir(parents=True, exist_ok=True)
    (loc / filename).write_text(body, encoding="utf-8")


def _categories(validator, category):
    return [i for i in validator._issues if i.category == category]


# --- £ref case (reference side) --------------------------------------------


def test_miscased_loc_ref_is_reported(tmp_path):
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_VTB_autocracy", "gfx/vtb.dds"))
    _write_loc(tmp_path, "english", "a_l_english.yml", ' a: "£VTB_Autocracy"\n')
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v.run_validations()
    issues = _categories(v, "sprite-ref-case")
    assert len(issues) == 1
    assert "GFX_VTB_autocracy" in issues[0].message
    assert issues[0].file.endswith("a_l_english.yml")


def test_exactly_matching_loc_ref_is_not_reported(tmp_path):
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_VTB_Autocracy", "gfx/vtb.dds"))
    _write_loc(tmp_path, "english", "a_l_english.yml", ' a: "£VTB_Autocracy"\n')
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v.run_validations()
    assert not _categories(v, "sprite-ref-case")


def test_undefined_loc_ref_without_a_case_match_is_not_reported(tmp_path):
    # Only case mismatches are in scope — a ref naming nothing at all is a
    # separate (and much larger) question this check deliberately stays out of.
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_real", "gfx/real.dds"))
    _write_loc(tmp_path, "english", "a_l_english.yml", ' a: "£totally_absent"\n')
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v.run_validations()
    assert not _categories(v, "sprite-ref-case")


def test_non_english_loc_ref_case_is_not_reported(tmp_path):
    # Non-English loc is out of scope until the translation project (AGENTS.md),
    # and `£Réseau` truncates at the accent to `£R`, colliding with short names.
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_VTB_autocracy", "gfx/vtb.dds"))
    _write_loc(tmp_path, "french", "a_l_french.yml", ' a: "£VTB_Autocracy"\n')
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v.run_validations()
    assert not _categories(v, "sprite-ref-case")


def test_loc_ref_case_runs_without_report_unused(tmp_path):
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_VTB_autocracy", "gfx/vtb.dds"))
    _write_loc(tmp_path, "english", "a_l_english.yml", ' a: "£VTB_Autocracy"\n')
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert v.report_unused is False
    v.run_validations()
    assert _categories(v, "sprite-ref-case")


# --- unused-sprite case split (definition side) -----------------------------


def test_sprite_referenced_only_with_other_case_is_split_out(tmp_path):
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_ukr_energy"}, all_refs={"GFX_UKR_energy"})
    assert not _categories(v, "unused-sprite")
    miscased = _categories(v, "unused-sprite-case")
    assert len(miscased) == 1
    assert "GFX_UKR_energy" in miscased[0].message


def test_case_variant_that_is_itself_defined_stays_an_orphan(tmp_path):
    # GFX_idea_irgc and GFX_idea_IRGC are separate sprites on separate art; the
    # referenced one resolves fine, so the other is an ordinary dead definition.
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(
        defined={"GFX_idea_irgc", "GFX_idea_IRGC"}, all_refs={"GFX_idea_IRGC"}
    )
    assert not _categories(v, "unused-sprite-case")
    assert [i for i in _categories(v, "unused-sprite") if "GFX_idea_irgc" in i.message]


# --- duplicate definitions --------------------------------------------------


def test_name_defined_twice_is_reported(tmp_path):
    _write_gfx(
        tmp_path,
        "test.gfx",
        _sprite("GFX_dup", "gfx/one.dds"),
        _sprite("GFX_dup", "gfx/two.dds"),
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._build_gfx_definitions()
    v._check_duplicate_definitions()
    issues = _categories(v, "duplicate-sprite")
    assert len(issues) == 1
    assert "defined 2 times" in issues[0].message
    assert "different textures" in issues[0].message


def test_duplicate_on_one_texture_is_called_redundant(tmp_path):
    _write_gfx(
        tmp_path,
        "test.gfx",
        _sprite("GFX_dup", "gfx/same.dds"),
        _sprite("GFX_dup", "gfx/same.dds"),
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._build_gfx_definitions()
    v._check_duplicate_definitions()
    assert "redundant" in _categories(v, "duplicate-sprite")[0].message


def test_unique_names_report_no_duplicate(tmp_path):
    _write_gfx(
        tmp_path,
        "test.gfx",
        _sprite("GFX_a", "gfx/a.dds"),
        _sprite("GFX_b", "gfx/b.dds"),
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._build_gfx_definitions()
    v._check_duplicate_definitions()
    assert not _categories(v, "duplicate-sprite")
    assert not _categories(v, "case-variant-sprite")


def test_case_variants_on_one_texture_say_collapse(tmp_path):
    _write_gfx(
        tmp_path,
        "test.gfx",
        _sprite("GFX_idea_Nexter", "gfx/Nexter.dds"),
        _sprite("GFX_idea_nexter", "gfx/Nexter.dds"),
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._build_gfx_definitions()
    v._check_duplicate_definitions()
    issues = _categories(v, "case-variant-sprite")
    assert len(issues) == 1
    assert "collapse them onto one name" in issues[0].message


def test_case_variants_on_separate_textures_are_marked_distinct(tmp_path):
    _write_gfx(
        tmp_path,
        "test.gfx",
        _sprite("GFX_idea_IRGC", "gfx/iran/IRGC.dds"),
        _sprite("GFX_idea_irgc", "gfx/factions/irgc.dds"),
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._build_gfx_definitions()
    v._check_duplicate_definitions()
    assert "distinct textures" in _categories(v, "case-variant-sprite")[0].message


# --- engine-resolved exemptions ---------------------------------------------


def test_vanilla_name_override_is_exempt_from_the_unused_report(tmp_path):
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._vanilla_defined = {"GFX_MODIFIER_ATTRITION"}
    v._check_unused_sprites(defined={"GFX_MODIFIER_ATTRITION"}, all_refs=set())
    assert not v._issues


def test_mod_only_name_is_still_reported_when_vanilla_names_are_loaded(tmp_path):
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._vanilla_defined = {"GFX_MODIFIER_ATTRITION"}
    v._check_unused_sprites(defined={"GFX_MD_only"}, all_refs=set())
    assert [i for i in v._issues if "GFX_MD_only" in i.message]


def _write_focus(tmp_path, body):
    focus_dir = tmp_path / "common" / "national_focus"
    focus_dir.mkdir(parents=True, exist_ok=True)
    (focus_dir / "test.txt").write_text(body, encoding="utf-8")


def test_search_filter_names_are_read_from_focus_trees(tmp_path):
    _write_focus(
        tmp_path,
        "focus = {\n\tsearch_filters = { FOCUS_FILTER_POLITICAL FOCUS_FILTER_UKR_STABILITY }\n}\n",
    )
    assert vg._load_search_filter_names(str(tmp_path)) == frozenset(
        {"FOCUS_FILTER_POLITICAL", "FOCUS_FILTER_UKR_STABILITY"}
    )


def test_focus_filter_icon_in_use_is_exempt_from_the_unused_report(tmp_path):
    _write_focus(
        tmp_path, "focus = {\n\tsearch_filters = { FOCUS_FILTER_UKR_STABILITY }\n}\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_FOCUS_FILTER_UKR_STABILITY"}, all_refs=set())
    assert not v._issues


def test_focus_filter_icon_no_focus_uses_stays_reported(tmp_path):
    _write_focus(
        tmp_path, "focus = {\n\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n}\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_FOCUS_FILTER_RETIRED"}, all_refs=set())
    assert [i for i in v._issues if "GFX_FOCUS_FILTER_RETIRED" in i.message]


def test_commented_out_search_filter_does_not_exempt(tmp_path):
    _write_focus(tmp_path, "focus = {\n#\tsearch_filters = { FOCUS_FILTER_DEAD }\n}\n")
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._check_unused_sprites(defined={"GFX_FOCUS_FILTER_DEAD"}, all_refs=set())
    assert [i for i in v._issues if "GFX_FOCUS_FILTER_DEAD" in i.message]


def test_unused_check_logs_notice_when_no_search_filters_exist(tmp_path, monkeypatch):
    logged = []
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    monkeypatch.setattr(v, "log", lambda msg, *a, **k: logged.append(msg))
    v._check_unused_sprites(defined=set(), all_refs=set())
    assert any("search_filters" in msg for msg in logged)


def test_gfx_parse_carries_the_texturefile(tmp_path):
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_a", "gfx/a.dds"))
    path = os.path.join(str(tmp_path), "interface", "test.gfx")
    assert vg._parse_gfx_file((path, str(tmp_path))) == [
        ("GFX_a", path, "gfx/a.dds", 2)
    ]
