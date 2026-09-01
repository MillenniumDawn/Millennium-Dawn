"""Parser- and branch-level tests for validate_gfx_references.

The validator's verdict is assembled from a dozen tiny per-file parsers plus the
vanilla-discovery helpers. Each is driven directly here so an unreadable file,
a runtime-built sprite name or a missing HOI4 install produces the documented
fallback instead of a crash or a false finding.
"""

import argparse
import os
import sys

import pytest
import validate_gfx_references as vg
from validate_gfx_references import Validator as GfxReferenceValidator

# Captured before the autouse stubs replace them, so the discovery tests can
# still exercise the real glob logic against a fake install.
_REAL_VANILLA_GFX_FILES = vg._vanilla_gfx_files
_REAL_VANILLA_GUI_FILES = vg._vanilla_gui_files
_REAL_VANILLA_GUI_REF_INDEX = vg._vanilla_gui_ref_index
_REAL_SPRITE_MANIFEST = vg._load_vanilla_sprite_manifest
_REAL_FONT_MANIFEST = vg._load_vanilla_font_manifest


@pytest.fixture(autouse=True)
def _no_vanilla_install(no_vanilla_gfx, monkeypatch):
    monkeypatch.setattr(vg, "_vanilla_gui_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_font_manifest", lambda: frozenset())


def _write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return str(path)


def _directory(path):
    """A directory whose name matches a scanned glob — reads as unreadable."""
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _broken_symlink(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(str(path.parent / "no_such_target"), str(path))
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")
    return str(path)


# --- vanilla discovery ------------------------------------------------------


def _fake_install(tmp_path):
    root = tmp_path / "hoi4"
    _write(root / "interface" / "core.gfx", "spriteTypes = {\n}\n")
    _write(root / "interface" / "core.gui", "guiTypes = {\n}\n")
    _write(root / "dlc" / "dlc01" / "interface" / "toa.gfx", "spriteTypes = {\n}\n")
    _write(root / "dlc" / "dlc01" / "interface" / "toa.gui", "guiTypes = {\n}\n")
    _write(
        root / "integrated_dlc" / "gd" / "interface" / "gd.gfx", "spriteTypes = {\n}\n"
    )
    _write(root / "integrated_dlc" / "gd" / "interface" / "gd.gui", "guiTypes = {\n}\n")
    return str(root)


def test_vanilla_gfx_and_gui_scans_include_dlc_interfaces(tmp_path, monkeypatch):
    install = _fake_install(tmp_path)
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: install)

    gfx = [os.path.basename(f) for f in _REAL_VANILLA_GFX_FILES()]
    gui = [os.path.basename(f) for f in _REAL_VANILLA_GUI_FILES()]

    assert sorted(gfx) == ["core.gfx", "gd.gfx", "toa.gfx"]
    assert sorted(gui) == ["core.gui", "gd.gui", "toa.gui"]


def test_vanilla_scans_are_empty_without_an_install(monkeypatch):
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: None)
    assert _REAL_VANILLA_GFX_FILES() == []
    assert _REAL_VANILLA_GUI_FILES() == []
    assert vg._find_vanilla_interface_dir() is None


def test_vanilla_interface_dir_is_found_inside_an_install(tmp_path, monkeypatch):
    install = _fake_install(tmp_path)
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: install)
    assert vg._find_vanilla_interface_dir() == os.path.join(install, "interface")


def test_install_without_an_interface_dir_has_no_vanilla_interface(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(vg, "find_hoi4_install", lambda: str(tmp_path))
    assert vg._find_vanilla_interface_dir() is None


@pytest.mark.parametrize(
    "loader, filename, attribute",
    [
        (_REAL_SPRITE_MANIFEST, "vanilla_sprites.txt", "_VANILLA_SPRITES_MANIFEST"),
        (_REAL_FONT_MANIFEST, "vanilla_fonts.txt", "_VANILLA_FONTS_MANIFEST"),
    ],
)
def test_committed_manifests_skip_comments_and_blank_lines(
    tmp_path, monkeypatch, loader, filename, attribute
):
    manifest = tmp_path / filename
    manifest.write_text("# generated\n\nENTRY_ONE\nENTRY_TWO\n", encoding="utf-8")
    monkeypatch.setattr(vg, attribute, str(manifest))
    assert loader() == frozenset({"ENTRY_ONE", "ENTRY_TWO"})


@pytest.mark.parametrize(
    "loader, attribute",
    [
        (_REAL_SPRITE_MANIFEST, "_VANILLA_SPRITES_MANIFEST"),
        (_REAL_FONT_MANIFEST, "_VANILLA_FONTS_MANIFEST"),
    ],
)
def test_corrupt_manifest_reads_as_empty(tmp_path, monkeypatch, loader, attribute):
    manifest = tmp_path / "manifest.txt"
    manifest.write_bytes(b"ENTRY_ONE\n\xff\xfe not utf-8 \x80\n")
    monkeypatch.setattr(vg, attribute, str(manifest))
    assert loader() == frozenset()


def test_vanilla_gui_ref_index_keys_refs_by_basename(tmp_path, monkeypatch):
    unreadable = _directory(tmp_path / "broken.gui")
    real = _write(
        tmp_path / "topbar.gui",
        'guiTypes = {\n\tspriteType = "GFX_topbar_pp"\n'
        '\tbackground = "GFX_stray]token"\n}\n',
    )
    monkeypatch.setattr(vg, "_vanilla_gui_files", lambda: [unreadable, real])

    index = _REAL_VANILLA_GUI_REF_INDEX()

    assert index["topbar.gui"] == {"GFX_topbar_pp"}
    assert "broken.gui" not in index


# --- declaration harvesting -------------------------------------------------


def test_empty_declaration_blocks_declare_no_names():
    assert vg._entry_names_from_text("equipments = {}\n", vg._EQUIPMENTS_BLOCK_RE) == []
    assert vg._unit_category_names_from_text("sub_unit_categories = {}\n") == []


def test_txt_walk_ignores_other_extensions(tmp_path):
    _write(tmp_path / "a.txt", "")
    _write(tmp_path / "nested" / "b.txt", "")
    _write(tmp_path / "nested" / "c.gfx", "")
    assert sorted(os.path.basename(f) for f in vg._iter_txt_files(str(tmp_path))) == [
        "a.txt",
        "b.txt",
    ]


def test_missing_directory_yields_no_files(tmp_path):
    assert vg._iter_txt_files(str(tmp_path / "absent"), recursive=False) == []
    assert vg._iter_txt_files(str(tmp_path / "absent")) == []


def test_unreadable_declaration_file_is_skipped(tmp_path):
    focus_dir = tmp_path / "common" / "national_focus"
    _broken_symlink(focus_dir / "broken.txt")
    _write(
        focus_dir / "real.txt",
        "focus = {\n\tsearch_filters = { FOCUS_FILTER_UKR }\n}\n",
    )
    assert vg._load_search_filter_names(str(tmp_path)) == frozenset(
        {"FOCUS_FILTER_UKR"}
    )


def test_unreadable_equipment_file_is_skipped(tmp_path):
    equipment = tmp_path / "common" / "units" / "equipment"
    _broken_symlink(equipment / "broken.txt")
    _write(equipment / "real.txt", "equipments = {\n\tutil_vehicle_1 = {\n\t}\n}\n")
    archetypes, _modules = vg._load_equipment_tree(str(tmp_path))
    assert archetypes == frozenset({"util_vehicle_1"})


def test_unreadable_country_tag_file_is_skipped(tmp_path):
    tags = tmp_path / "common" / "country_tags"
    _directory(tags / "broken.txt")
    _write(tags / "00_countries.txt", 'CHI = "countries/China.txt"\n')
    assert vg._load_ace_pool_names(str(tmp_path)) == frozenset({"CHI"})


# --- per-file parsers -------------------------------------------------------


@pytest.mark.parametrize(
    "parser",
    [
        vg._parse_gfx_file,
        vg._parse_gui_file,
        vg._parse_gui_fonts,
        vg._parse_gfx_fonts,
        vg._parse_sgui_file,
        vg._parse_script_refs,
        vg._parse_loc_refs,
        vg._parse_sprite_templates,
        vg._parse_sloc_file,
    ],
)
def test_every_parser_tolerates_an_unreadable_file(tmp_path, parser):
    unreadable = _directory(tmp_path / "unreadable")
    assert parser((unreadable, str(tmp_path))) == []


def test_unbalanced_sprite_block_falls_back_to_the_opening_line():
    raw = 'spriteType = { name = "GFX_unbalanced" texturefile = "gfx/a.dds"\n'
    assert vg.sprite_defs_from_gfx_text(raw) == [("GFX_unbalanced", "gfx/a.dds", 1)]


def test_nameless_sprite_block_defines_nothing():
    raw = (
        'spriteType = {\n\ttexturefile = "gfx/a.dds"\n}\n'
        'spriteType = {\n\tname = "GFX_real"\n}\n'
    )
    assert vg.sprite_defs_from_gfx_text(raw) == [("GFX_real", "", 4)]
    assert vg.sprite_names_from_gfx_text(raw) == {"GFX_real"}


def test_font_block_without_a_name_defines_nothing():
    raw = 'bitmapfont = {\n\tfontfiles = { "gfx/fonts/x.fnt" }\n}\n'
    assert vg.font_names_from_gfx_text(raw) == set()


def test_unbalanced_font_block_still_declares_its_name():
    # The scan runs to end of text rather than dropping the block, so a .gfx
    # missing its closing brace does not turn every `font = "hoi_16"` into a
    # false undefined-font error.
    assert vg.font_names_from_gfx_text('bitmapfont = {\n\tname = "hoi_16"\n') == {
        "hoi_16"
    }


def test_gui_parser_drops_runtime_built_sprite_names(tmp_path):
    # A bracket anywhere in the name means the engine assembles it at runtime,
    # so the literal token can never be checked against a definition.
    path = _write(
        tmp_path / "interface" / "view.gui",
        'guiTypes = {\n\tspriteType = "GFX_static"\n'
        '\tbackground = "GFX_stray]token"\n}\n',
    )
    assert [name for name, _f, _l in vg._parse_gui_file((path, str(tmp_path)))] == [
        "GFX_static"
    ]


def test_scripted_gui_parser_drops_runtime_built_sprite_names(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_guis" / "panel.txt",
        'image = "GFX_static"\nimage = "GFX_stray]token"\n',
    )
    assert [name for name, _f, _l in vg._parse_sgui_file((path, str(tmp_path)))] == [
        "GFX_static"
    ]


def test_scripted_gui_and_scripted_loc_refs_carry_their_line(tmp_path):
    sgui = _write(
        tmp_path / "common" / "scripted_guis" / "panel.txt",
        '# comment\nimage = "GFX_panel_icon"\nimage = "GFX_[?v]_dynamic"\n',
    )
    sloc = _write(
        tmp_path / "common" / "scripted_localisation" / "text.txt",
        'defined_text = {\n\tlocalization_key = "GFX_sloc_icon"\n}\n',
    )

    assert vg._parse_sgui_file((sgui, str(tmp_path))) == [("GFX_panel_icon", sgui, 2)]
    assert vg._parse_sloc_file((sloc, str(tmp_path))) == [("GFX_sloc_icon", sloc, 2)]


def test_idea_picture_resolves_to_the_idea_sprite(tmp_path):
    path = _write(
        tmp_path / "common" / "ideas" / "00_ideas.txt",
        "ideas = {\n\ttest_idea = {\n\t\tpicture = generic_bank\n\t}\n}\n",
    )
    assert vg._parse_script_refs((path, str(tmp_path))) == ["GFX_idea_generic_bank"]


def test_script_refs_outside_ideas_ignore_picture_values(tmp_path):
    path = _write(
        tmp_path / "common" / "decisions" / "test.txt",
        "picture = generic_bank\nicon = GFX_decision_icon\n",
    )
    assert vg._parse_script_refs((path, str(tmp_path))) == ["GFX_decision_icon"]


def test_loc_refs_drop_punctuation_and_report_each_name_once(tmp_path):
    path = _write(
        tmp_path / "localisation" / "english" / "a_l_english.yml",
        'l_english:\n A:0 "£command_power. and £."\n B:0 "£command_power again"\n',
    )
    assert vg._parse_loc_refs((path, str(tmp_path))) == [("GFX_command_power", path, 2)]


def test_loc_ref_already_carrying_the_prefix_is_not_double_prefixed(tmp_path):
    path = _write(
        tmp_path / "localisation" / "english" / "b_l_english.yml",
        'l_english:\n A:0 "£GFX_money_icon"\n',
    )
    assert [name for name, _f, _l in vg._parse_loc_refs((path, str(tmp_path)))] == [
        "GFX_money_icon"
    ]


def test_sprite_templates_are_collected_from_scripted_files(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_localisation" / "t.txt",
        'localization_key = "GFX_missile_[THIS.GetTag]_icon"\n'
        'localization_key = "GFX_plain_icon"\n',
    )
    assert vg._parse_sprite_templates((path, str(tmp_path))) == [
        "GFX_missile_[THIS.GetTag]_icon"
    ]


# --- definition set assembly ------------------------------------------------


def test_vanilla_manifest_is_folded_in_when_no_install_is_present(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        vg, "_load_vanilla_sprite_manifest", lambda: frozenset({"GFX_vanilla_only"})
    )
    _write(tmp_path / "interface" / "a.gfx", 'spriteType = { name = "GFX_mod" }\n')

    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    defined, mod_defined = validator._build_gfx_definitions()

    assert defined == {"GFX_mod", "GFX_vanilla_only"}
    assert mod_defined == {"GFX_mod"}
    assert validator._vanilla_defs_loaded is True


def test_live_vanilla_gfx_files_take_priority_over_the_manifest(tmp_path, monkeypatch):
    vanilla = _write(
        tmp_path / "vanilla" / "interface" / "core.gfx",
        'spriteType = { name = "GFX_from_install" }\n',
    )
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [vanilla])
    monkeypatch.setattr(
        vg,
        "_load_vanilla_sprite_manifest",
        lambda: pytest.fail("manifest read with a live install"),
    )
    _write(tmp_path / "interface" / "a.gfx", 'spriteType = { name = "GFX_mod" }\n')

    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    defined, mod_defined = validator._build_gfx_definitions()

    assert defined == {"GFX_mod", "GFX_from_install"}
    assert validator._vanilla_defined == {"GFX_from_install"}


def test_live_vanilla_fonts_satisfy_a_gui_reference(tmp_path, monkeypatch):
    vanilla = _write(
        tmp_path / "vanilla" / "interface" / "fonts.gfx",
        'bitmapfonts = {\n\tbitmapfont = {\n\t\tname = "vic_18"\n\t}\n}\n',
    )
    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [vanilla])
    _write(tmp_path / "interface" / "core.gfx", "bitmapfonts = {\n}\n")
    _write(
        tmp_path / "interface" / "view.gui",
        'instantTextBoxType = {\n\tfont = "vic_18"\n\tfont = "absent_18"\n}\n',
    )

    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator._check_undefined_fonts()

    assert len(validator._issues) == 1
    assert 'font = "absent_18"' in validator._issues[0].message


# --- undefined-reference reporting ------------------------------------------


def _iface(tmp_path, basename):
    return os.path.join(str(tmp_path), "interface", basename)


def test_undefined_ref_reports_each_site_once(tmp_path):
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator._vanilla_defs_loaded = True
    path = _iface(tmp_path, "md_panel.gui")
    validator._check_undefined_refs(
        [("GFX_absent", path, 7), ("GFX_absent", path, 7)],
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    assert len(validator._issues) == 1
    assert validator._issues[0].line == 7


def test_flag_and_vanilla_shaped_names_are_not_reported(tmp_path):
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    path = _iface(tmp_path, "md_panel.gui")
    validator._check_undefined_refs(
        [
            ("GFX_flag_USA", path, 1),
            ("GFX_USA_shield", path, 2),
            ("GFX_topbar_pp", path, 3),
        ],
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    assert validator._issues == []


def test_vanilla_prefix_heuristic_stops_once_vanilla_names_are_loaded(tmp_path):
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator._vanilla_defs_loaded = True
    path = _iface(tmp_path, "md_panel.gui")
    validator._check_undefined_refs(
        [("GFX_topbar_pp", path, 3)],
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    assert len(validator._issues) == 1


def test_case_mismatched_ref_gets_the_linux_diagnostic(tmp_path):
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator._vanilla_defs_loaded = True
    path = os.path.join(str(tmp_path), "common", "scripted_guis", "panel.txt")
    validator._check_undefined_refs(
        [("GFX_Ukr_Energy", path, 4)],
        {"GFX_ukr_energy"},
        source_label="scripted_guis",
        category="undefined-sprite",
        mod_defined_ci=vg.casefold_index({"GFX_ukr_energy"}),
    )
    message = validator._issues[0].message
    assert "case-mismatch" in message
    assert "defined as 'GFX_ukr_energy'" in message
    assert validator._issues[0].severity == vg.Severity.ERROR


def test_staged_mode_reports_only_staged_files(tmp_path):
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator._vanilla_defs_loaded = True
    validator.staged_only = True
    staged = _iface(tmp_path, "md_staged.gui")
    validator.staged_files = [staged]
    validator._check_undefined_refs(
        [
            ("GFX_absent", staged, 1),
            ("GFX_absent", _iface(tmp_path, "md_other.gui"), 2),
        ],
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    assert [os.path.basename(i.file) for i in validator._issues] == ["md_staged.gui"]


# --- font check -------------------------------------------------------------


def test_font_check_is_skipped_without_an_install_or_manifest(tmp_path):
    _write(tmp_path / "interface" / "core.gfx", "bitmapfonts = {\n}\n")
    _write(
        tmp_path / "interface" / "view.gui", 'instantTextBoxType = {\n\tfont = "x"\n}\n'
    )

    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator._check_undefined_fonts()

    assert validator._issues == []


# --- unused-sprite check ----------------------------------------------------


def test_unused_check_is_skipped_in_staged_mode(tmp_path):
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator.staged_only = True
    validator._check_unused_sprites(defined={"GFX_orphan"}, all_refs=set())
    assert validator._issues == []


def test_unprefixed_sprite_name_is_still_reportable(tmp_path):
    # Focus icons are not GFX_-prefixed, so the equipment-icon exemption must
    # not swallow them.
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator._check_unused_sprites(defined={"focus_icon_orphan"}, all_refs=set())
    assert [i.message for i in validator._issues] == [
        "Unused GFX sprite 'focus_icon_orphan' (defined but never referenced)"
    ]


def test_loc_ref_case_check_is_scoped_to_staged_files(tmp_path):
    defined = {"GFX_ukr_energy"}
    staged = os.path.join(
        str(tmp_path), "localisation", "english", "staged_l_english.yml"
    )
    other = os.path.join(
        str(tmp_path), "localisation", "english", "other_l_english.yml"
    )
    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator.staged_only = True
    validator.staged_files = [staged]
    validator._check_loc_ref_case(
        [("GFX_UKR_energy", other, 3)], defined, vg.casefold_index(defined)
    )
    assert validator._issues == []

    validator._check_loc_ref_case(
        [("GFX_UKR_energy", staged, 3)], defined, vg.casefold_index(defined)
    )
    assert len(validator._issues) == 1


# --- full runs --------------------------------------------------------------


def test_staged_report_unused_run_skips_the_full_repo_passes(tmp_path, monkeypatch):
    _write(tmp_path / "interface" / "a.gfx", 'spriteType = { name = "GFX_orphan" }\n')
    validator = GfxReferenceValidator(
        str(tmp_path), use_colors=False, report_unused=True
    )
    validator.staged_only = True
    validator.staged_files = []
    monkeypatch.setattr(
        validator, "_collect_script_refs", lambda: pytest.fail("script refs collected")
    )
    validator.run_validations()

    assert not [i for i in validator._issues if i.category == "unused-sprite"]


def test_scripted_gui_and_scripted_loc_refs_reach_the_report(tmp_path):
    _write(tmp_path / "interface" / "a.gfx", "spriteTypes = {\n}\n")
    _write(
        tmp_path / "common" / "scripted_guis" / "panel.txt",
        'image = "GFX_missing_sgui"\n',
    )
    _write(
        tmp_path / "common" / "scripted_localisation" / "text.txt",
        'localization_key = "GFX_missing_sloc"\n',
    )

    validator = GfxReferenceValidator(str(tmp_path), use_colors=False)
    validator.run_validations()

    messages = " ".join(i.message for i in validator._issues)
    assert "GFX_missing_sgui" in messages
    assert "GFX_missing_sloc" in messages


def test_report_unused_flag_is_registered():
    parser = argparse.ArgumentParser()
    vg._add_extra_args(parser)
    assert parser.parse_args(["--report-unused"]).report_unused is True
    assert parser.parse_args([]).report_unused is False


def test_main_exits_zero_on_a_clean_mod(tmp_path, monkeypatch):
    _write(tmp_path / "interface" / "a.gfx", "spriteTypes = {\n}\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_gfx_references.py", "--path", str(tmp_path), "--workers", "1"],
    )
    with pytest.raises(SystemExit) as exit_info:
        vg.main()
    assert exit_info.value.code == 0
