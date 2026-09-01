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
def _no_vanilla_install(no_vanilla_gfx):
    return no_vanilla_gfx


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


# --- vanilla-override exemption ---------------------------------------------


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


# --- engine-resolved references ---------------------------------------------
#
# These are resolved into the reference set, not filtered out of the report, so
# a sprite whose backing declaration is gone still reports as unused and one
# spelled with the wrong case still reports as miscased.


def _write_focus(tmp_path, body):
    focus_dir = tmp_path / "common" / "national_focus"
    focus_dir.mkdir(parents=True, exist_ok=True)
    (focus_dir / "test.txt").write_text(body, encoding="utf-8")


def _write_modules(tmp_path, body):
    mod_dir = tmp_path / "common" / "units" / "equipment" / "modules"
    mod_dir.mkdir(parents=True, exist_ok=True)
    (mod_dir / "test.txt").write_text(body, encoding="utf-8")


def _write_tags(tmp_path, body):
    tag_dir = tmp_path / "common" / "country_tags"
    tag_dir.mkdir(parents=True, exist_ok=True)
    (tag_dir / "00_countries.txt").write_text(body, encoding="utf-8")


def _write_country(tmp_path, body):
    country_dir = tmp_path / "common" / "countries"
    country_dir.mkdir(parents=True, exist_ok=True)
    (country_dir / "Test.txt").write_text(body, encoding="utf-8")


def _write_sloc(tmp_path, body):
    sloc_dir = tmp_path / "common" / "scripted_localisation"
    sloc_dir.mkdir(parents=True, exist_ok=True)
    (sloc_dir / "test.txt").write_text(body, encoding="utf-8")


def _write_units(tmp_path, body):
    unit_dir = tmp_path / "common" / "units"
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / "test.txt").write_text(body, encoding="utf-8")


def _write_unit_tags(tmp_path, body):
    tag_dir = tmp_path / "common" / "unit_tags"
    tag_dir.mkdir(parents=True, exist_ok=True)
    (tag_dir / "00_categories.txt").write_text(body, encoding="utf-8")


def test_search_filter_names_are_read_from_focus_trees(tmp_path):
    _write_focus(
        tmp_path,
        "focus = {\n\tsearch_filters = { FOCUS_FILTER_POLITICAL FOCUS_FILTER_UKR_STABILITY }\n}\n",
    )
    assert vg._load_search_filter_names(str(tmp_path)) == frozenset(
        {"FOCUS_FILTER_POLITICAL", "FOCUS_FILTER_UKR_STABILITY"}
    )


def test_focus_filter_icon_in_use_resolves_as_a_reference(tmp_path):
    _write_focus(
        tmp_path, "focus = {\n\tsearch_filters = { FOCUS_FILTER_UKR_STABILITY }\n}\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert "GFX_FOCUS_FILTER_UKR_STABILITY" in v._resolve_engine_refs(set())


def test_focus_filter_icon_no_focus_uses_stays_unresolved(tmp_path):
    _write_focus(
        tmp_path, "focus = {\n\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n}\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert "GFX_FOCUS_FILTER_RETIRED" not in v._resolve_engine_refs(
        {"GFX_FOCUS_FILTER_RETIRED"}
    )


def test_commented_out_search_filter_does_not_resolve(tmp_path):
    _write_focus(tmp_path, "focus = {\n#\tsearch_filters = { FOCUS_FILTER_DEAD }\n}\n")
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert "GFX_FOCUS_FILTER_DEAD" not in v._resolve_engine_refs(
        {"GFX_FOCUS_FILTER_DEAD"}
    )


def test_module_names_cover_modules_and_their_categories(tmp_path):
    _write_modules(
        tmp_path,
        "equipment_modules = {\n\ttank_diesel_engine_gen1 = {\n"
        "\t\tcategory = tank_engine_type\n\t}\n}\n",
    )
    assert vg._load_module_icon_names(str(tmp_path)) == frozenset(
        {"tank_diesel_engine_gen1", "tank_engine_type"}
    )


def test_chassis_slot_categories_are_read_too(tmp_path):
    # A category is never declared on its own. Harvesting only `category =` misses
    # one a chassis slot allows but no surviving module claims, and deleting its
    # icon blanks the slot in the designer.
    equipment = tmp_path / "common" / "units" / "equipment"
    equipment.mkdir(parents=True, exist_ok=True)
    (equipment / "chassis.txt").write_text(
        "equipments = {\n\ttank_chassis = {\n\t\tmodule_slots = {\n"
        "\t\t\tengine_type_slot = {\n\t\t\t\tallowed_module_categories = {\n"
        "\t\t\t\t\tafv_gasoline_engine_type\n\t\t\t\t\ttank_diesel_engine_type\n"
        "\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n",
        encoding="utf-8",
    )
    names = vg._load_module_icon_names(str(tmp_path))
    assert "afv_gasoline_engine_type" in names
    assert "tank_diesel_engine_type" in names


def test_category_icon_resolves_as_a_reference(tmp_path):
    _write_modules(
        tmp_path,
        "equipment_modules = {\n\tafv_petrol_1 = {\n"
        "\t\tcategory = afv_gasoline_engine_type\n\t}\n}\n",
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    resolved = v._resolve_engine_refs(set())
    assert "GFX_EMI_afv_gasoline_engine_type" in resolved
    assert "GFX_SMI_afv_gasoline_engine_type" in resolved


def test_module_icon_resolves_as_a_reference(tmp_path):
    _write_modules(
        tmp_path, "equipment_modules = {\n\tCZE_engine_1 = {\n\t\tyear = 2000\n\t}\n}\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    resolved = v._resolve_engine_refs(set())
    assert "GFX_EMI_CZE_engine_1" in resolved
    assert "GFX_SMI_CZE_engine_1" in resolved


def test_module_icon_for_a_deleted_module_stays_unresolved(tmp_path):
    # GFX_EMI_afv_battlestation_1 is real MD art for an AFV module set that no
    # longer exists — membership must keep reporting it.
    _write_modules(
        tmp_path, "equipment_modules = {\n\tCZE_engine_1 = {\n\t\tyear = 2000\n\t}\n}\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    resolved = v._resolve_engine_refs(
        {"GFX_EMI_afv_battlestation_1", "GFX_SMI_afv_battlestation_1"}
    )
    assert "GFX_EMI_afv_battlestation_1" not in resolved
    assert "GFX_SMI_afv_battlestation_1" not in resolved


def test_unit_icon_names_cover_subunits_and_categories(tmp_path):
    _write_units(
        tmp_path, "sub_units = {\n\tAA_company = {\n\t\tsprite = infantry\n\t}\n}\n"
    )
    _write_unit_tags(tmp_path, "sub_unit_categories = {\n\tcategory_fighter\n}\n")
    assert vg._load_unit_icon_names(str(tmp_path)) == frozenset(
        {"AA_company", "category_fighter"}
    )


def test_unit_icon_names_ignore_equipment_and_namelist_dirs(tmp_path):
    _write_units(
        tmp_path, "sub_units = {\n\tAA_company = {\n\t\tsprite = infantry\n\t}\n}\n"
    )
    equipment = tmp_path / "common" / "units" / "equipment"
    equipment.mkdir(parents=True, exist_ok=True)
    (equipment / "fake.txt").write_text(
        "sub_units = {\n\tfake_from_equipment = {\n\t\tsprite = infantry\n\t}\n}\n",
        encoding="utf-8",
    )
    names_dir = tmp_path / "common" / "units" / "names"
    names_dir.mkdir(parents=True, exist_ok=True)
    (names_dir / "00_names.txt").write_text(
        "sub_units = {\n\tfake_from_names = {\n\t\tsprite = infantry\n\t}\n}\n",
        encoding="utf-8",
    )
    assert vg._load_unit_icon_names(str(tmp_path)) == frozenset({"AA_company"})


def test_equipment_tree_serves_archetypes_and_modules(tmp_path):
    equipment = tmp_path / "common" / "units" / "equipment"
    equipment.mkdir(parents=True, exist_ok=True)
    (equipment / "both.txt").write_text(
        "equipments = {\n\tutil_vehicle_1 = {\n\t\tyear = 1936\n\t}\n}\n"
        "equipment_modules = {\n\tCZE_engine_1 = {\n\t\tyear = 2000\n\t}\n}\n",
        encoding="utf-8",
    )
    archetypes, modules = vg._load_equipment_tree(str(tmp_path))
    assert archetypes == frozenset({"util_vehicle_1"})
    assert modules == frozenset({"CZE_engine_1"})
    assert vg._load_equipment_names(str(tmp_path)) == archetypes
    assert vg._load_module_icon_names(str(tmp_path)) == modules


def test_declaration_engine_refs_reuse_the_aggregate_cache(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write_units(
        tmp_path, "sub_units = {\n\tAA_company = {\n\t\tsprite = infantry\n\t}\n}\n"
    )
    first, _notices = vg._declaration_engine_refs(str(tmp_path))
    assert "GFX_unit_AA_company_icon_medium" in first

    def _boom(_mod_path):
        raise AssertionError("declaration cache missed")

    monkeypatch.setattr(
        vg,
        "_ENGINE_DECLARATION_FAMILIES",
        ((_boom, "", ("GFX_unit_{name}_icon_medium",)),),
    )
    second, _notices = vg._declaration_engine_refs(str(tmp_path))
    assert second == first


def test_unit_icon_resolves_for_a_real_subunit(tmp_path):
    _write_units(
        tmp_path,
        "sub_units = {\n\tALN_bellatoris = {\n\t\tsprite = CHIMERA_bellatoris\n\t}\n}\n",
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    resolved = v._resolve_engine_refs(set())
    assert "GFX_unit_ALN_bellatoris_icon_medium" in resolved
    assert "GFX_unit_ALN_bellatoris_icon_small" in resolved
    assert "GFX_unit_ALN_bellatoris_icon_medium_white" in resolved
    assert "GFX_unit_ALN_bellatoris_icon_small_white" in resolved
    assert "GFX_unit_ALN_bellatoris_icon_medium_black" in resolved


def test_unit_category_icon_resolves_as_a_reference(tmp_path):
    _write_unit_tags(tmp_path, "sub_unit_categories = {\n\tcategory_all_airborne\n}\n")
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert "GFX_unit_category_all_airborne_icon_small" in v._resolve_engine_refs(set())


def test_unit_icon_for_a_deleted_unit_stays_unresolved(tmp_path):
    _write_units(
        tmp_path, "sub_units = {\n\tAA_company = {\n\t\tsprite = infantry\n\t}\n}\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert "GFX_unit_AFG_donkey_logistics_icon_medium" not in v._resolve_engine_refs(
        {"GFX_unit_AFG_donkey_logistics_icon_medium"}
    )


def test_ace_portrait_resolves_for_a_real_tag_and_culture(tmp_path):
    _write_tags(tmp_path, 'CHI = "countries/China.txt"\n')
    _write_country(
        tmp_path, "graphical_culture = asian_gfx\ngraphical_culture_2d = asian_2d\n"
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    resolved = v._resolve_engine_refs(
        {"GFX_CHI_ace_m_0", "GFX_asian_2d_ace_f_1", "GFX_ace_m_2", "GFX_XYZ_ace_m_0"}
    )
    assert "GFX_CHI_ace_m_0" in resolved
    assert "GFX_asian_2d_ace_f_1" in resolved
    # The engine's own last-resort pool has no key to check.
    assert "GFX_ace_m_2" in resolved
    # An ace portrait for a tag the mod does not declare is dead art.
    assert "GFX_XYZ_ace_m_0" not in resolved


def test_scripted_loc_template_resolves_the_sprites_it_can_build(tmp_path):
    _write_sloc(
        tmp_path,
        "defined_text = {\n\tname = missile_icon\n\ttext = {\n"
        '\t\tlocalization_key = "GFX_missile_[THIS.GetTag]_ID_[?var_x]_icon"\n'
        "\t}\n}\n",
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    resolved = v._resolve_engine_refs(
        {"GFX_missile_CHI_ID_101_icon", "GFX_missile_submarine_offensive_medium"}
    )
    assert "GFX_missile_CHI_ID_101_icon" in resolved
    # Same GFX_missile_ prefix, but the template's _ID_/_icon literals don't fit.
    assert "GFX_missile_submarine_offensive_medium" not in resolved


def test_template_that_is_only_a_placeholder_is_rejected(tmp_path):
    # GFX_[?topbar.GetTokenKey] would otherwise resolve every sprite in the mod.
    assert vg._template_pattern("GFX_[?topbar.GetTokenKey]") is None
    assert vg._template_pattern("GFX_missile_[THIS.GetTag]_ID_[?v]_icon") is not None


def test_only_a_placeholder_template_resolves_nothing(tmp_path):
    _write_sloc(
        tmp_path,
        "defined_text = {\n\tname = alert\n\ttext = {\n"
        '\t\tlocalization_key = "GFX_[?md_alerts^alert_idx.GetTokenKey]"\n'
        "\t}\n}\n",
    )
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    assert v._resolve_engine_refs({"GFX_anything_at_all"}) == set()


def test_resolver_logs_notices_when_the_data_dirs_are_missing(tmp_path, gfx_notices):
    logged = gfx_notices(
        tmp_path, lambda validator: validator._resolve_engine_refs(set())
    )
    for expected in (
        "search_filters",
        "equipment modules",
        "unit icons",
        "graphical cultures",
    ):
        assert any(expected in msg for msg in logged)


def test_gfx_parse_carries_the_texturefile(tmp_path):
    _write_gfx(tmp_path, "test.gfx", _sprite("GFX_a", "gfx/a.dds"))
    path = os.path.join(str(tmp_path), "interface", "test.gfx")
    assert vg._parse_gfx_file((path, str(tmp_path))) == [
        ("GFX_a", path, "gfx/a.dds", 2)
    ]
