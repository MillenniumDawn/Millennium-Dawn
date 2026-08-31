"""Branch-focused coverage for the smaller validation modules."""

import re
import sys
from pathlib import Path

import pytest
import validate_agency_upgrades as agency
import validate_cosmetic_tags as cosmetic
import validate_decisions as decisions
import validate_localisation as localisation
import validate_mod_descriptors as descriptors
import validate_scripted_gui as scripted_gui
import validate_unused_scripted as unused
from shared_utils import run_validator_main


def _write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return path


def _validator(cls, root: Path, staged_only: bool = False, **kwargs):
    return cls(
        mod_path=str(root),
        use_colors=False,
        staged_only=staged_only,
        workers=1,
        **kwargs,
    )


def _categories(validator):
    return {issue.category for issue in validator._issues}


def test_agency_helpers_cover_calls_and_unreadable_inputs(tmp_path):
    assert agency._read(tmp_path / "missing.txt") == ""
    assert agency._line_of("a\nb\n", 2) == 2
    assert agency.Validator._short_token("MD_auto_agency_12_upgrade_x") == "upgrade_x"
    assert (
        agency.Validator._short_token("MD_auto_agency_12_upgrade_x_name") == "upgrade_x"
    )
    assert agency.Validator._short_token("literal") == "literal"

    text = """# create_intelligence_agency = { icon = GFX_ignored }
create_intelligence_agency = {
\ticon = GFX_real
}
create_intelligence_agency = { }
upgrade_intelligence_agency = upgrade_real
upgrade_intelligence_agency = upgrade_other
"""
    assert agency._scan_agency_calls(agency.strip_comments(text), "events/x.txt") == (
        [("events/x.txt", 2, "GFX_real")],
        [("events/x.txt", 6, "upgrade_real"), ("events/x.txt", 7, "upgrade_other")],
    )
    missing = agency.process_file_for_agency_calls(
        (str(tmp_path / "missing.txt"), str(tmp_path))
    )
    assert missing == ([], [])


def test_agency_full_run_reports_every_integration_group(tmp_path):
    _write(
        tmp_path,
        "common/intelligence_agency_upgrades/upgrades.txt",
        """\tupgrade_good = {
\t\tlevel = { }
\t\tlevel = { }
\t}
\tupgrade_no_picture = {
\t\tlevel = { }
\t}
""",
    )
    _write(
        tmp_path,
        agency.ON_ACTIONS_FILE,
        """global.agency_upgrades^0 = token:MD_auto_agency_0_upgrade_good
global.agency_names^0 = token:MD_auto_agency_0_wrong_name
global.agency_gfx^0 = token:MD_auto_agency_0_wrong_gfx
global.agency_max_upgrades^0 = 1
global.agency_upgrades^1 = token:MD_auto_agency_1_upgrade_unknown
global.agency_gfx^1 = token:MD_auto_agency_1_upgrade_unknown_gfx
global.agency_names^2 = token:MD_auto_agency_2_upgrade_unknown_name
resize_array = { array = global.agency_upgrades value = 0 size = 3 }
""",
    )
    _write(
        tmp_path,
        agency.LOC_FILE,
        'MD_auto_agency_0_upgrade_good: "Good"\n'
        'MD_auto_agency_0_upgrade_good_gfx: "GFX_other"\n',
    )
    _write(
        tmp_path,
        "interface/agency.gfx",
        'spriteType = { name = "GFX_good" }\n',
    )
    _write(
        tmp_path,
        agency.SCRIPTED_GUI_FILE,
        """scripted_gui = {
\tcheck = {
\t\thas_done_agency_upgrade = upgrade_unknown
\t}
}
""",
    )
    _write(
        tmp_path,
        "events/calls.txt",
        """create_intelligence_agency = { icon = GFX_missing }
upgrade_intelligence_agency = upgrade_unknown
""",
    )

    validator = _validator(agency.Validator, tmp_path)
    validator.run_all_validations()
    assert _categories(validator) == {
        "agency-upgrades-registry",
        "agency-upgrades-max-levels",
        "agency-upgrades-loc-gfx",
        "agency-upgrades-array-size",
        "agency-upgrades-prereqs",
        "agency-upgrades-calls",
    }
    assert any("upgrade_no_picture" in issue.message for issue in validator._issues)
    assert any("index ^1 missing" in issue.message for issue in validator._issues)


def test_agency_success_and_staged_empty_boundaries(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "common/intelligence_agency_upgrades/upgrades.txt",
        "\tupgrade_good = {\n\t\tpicture = GFX_good\n\t\tlevel = { }\n\t}\n",
    )
    _write(
        tmp_path,
        agency.ON_ACTIONS_FILE,
        "global.agency_upgrades^0 = token:MD_auto_agency_0_upgrade_good\n"
        "global.agency_names^0 = token:MD_auto_agency_0_upgrade_good_name\n"
        "global.agency_gfx^0 = token:MD_auto_agency_0_upgrade_good_gfx\n"
        "resize_array = { array = global.agency_upgrades value = 0 size = 1 }\n",
    )
    _write(
        tmp_path,
        agency.LOC_FILE,
        'MD_auto_agency_0_upgrade_good: "Good"\n'
        'MD_auto_agency_0_upgrade_good_name: "Good name"\n'
        'MD_auto_agency_0_upgrade_good_gfx: "GFX_good"\n',
    )
    _write(tmp_path, "interface/agency.gfx", 'spriteType = { name = "GFX_good" }\n')
    _write(tmp_path, agency.SCRIPTED_GUI_FILE, "scripted_gui = { check = { } }\n")

    clean = _validator(agency.Validator, tmp_path)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    missing_gui = _validator(agency.Validator, tmp_path / "missing-gui")
    missing_gui._validate_scripted_gui_prereqs()
    assert missing_gui._issues == []

    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/intelligence_agency_upgrades/upgrades.txt"
    )
    staged = _validator(agency.Validator, tmp_path, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []


def test_cosmetic_workers_cover_comments_dynamic_and_missing_files(tmp_path):
    path = _write(
        tmp_path,
        "events/tags.txt",
        """# set_cosmetic_tag = ignored
set_cosmetic_tag = TAG_A
has_cosmetic_tag = TAG_B
has_cosmetic_tag = [ROOT.GetTag]
""",
    )
    assert cosmetic.process_file_for_set_cosmetic_tag(
        (str(path), False, ["TAG_A", "TAG_B", "TAG_NONE"])
    ) == {"TAG_A": 1}
    assert cosmetic._scan_both_cosmetic_tags(
        re.sub(r"#[^\n]*", "", path.read_text()), "tags.txt"
    )[0] == {"TAG_B": 0}
    assert cosmetic._scan_both_cosmetic_tags(
        re.sub(r"#[^\n]*", "", path.read_text()), "tags.txt"
    )[2] == {"TAG_A": 0}
    assert cosmetic.process_file_for_both_cosmetic_tags(
        (str(path), False, str(tmp_path))
    )[0] == {"TAG_B": 0}
    assert cosmetic.process_file_for_has_cosmetic_tag_lookup(
        (str(path), frozenset({"TAG_B", "TAG_NONE"}))
    ) == {"TAG_B"}
    assert cosmetic.process_file_for_cosmetic_tag_in_loc(
        (
            str(
                _write(
                    tmp_path,
                    "localisation/english/x.yml",
                    'x:0 "TAG_A: TAG_A_democratic:"\n',
                )
            ),
            frozenset({"TAG_A", "TAG_NONE"}),
        )
    ) == {"TAG_A": 2}
    assert (
        cosmetic.process_file_for_has_cosmetic_tag_lookup(
            (str(tmp_path / "missing.txt"), frozenset({"TAG_A"}))
        )
        == set()
    )
    assert (
        cosmetic.process_file_for_cosmetic_tag_in_loc(
            (str(tmp_path / "missing.yml"), frozenset({"TAG_A"}))
        )
        == {}
    )
    assert cosmetic._should_skip(".git/events.txt")
    assert cosmetic.process_file_for_both_cosmetic_tags(
        (
            str(_write(tmp_path, "events/empty.txt", "plain = yes\n")),
            False,
            str(tmp_path),
        )
    ) == ({}, {}, {}, {})
    skipped = _write(tmp_path, ".git/tags.txt", "has_cosmetic_tag = TAG_A\n")
    assert (
        cosmetic.process_file_for_has_cosmetic_tag_lookup(
            (str(skipped), frozenset({"TAG_A"}))
        )
        == set()
    )


def test_cosmetic_full_run_reports_missing_unused_and_color_categories(tmp_path):
    _write(
        tmp_path,
        "common/countries/cosmetic.txt",
        """TAG_COLOR_UNUSED = {
}
TAG_COLOR_USED = {
}
""",
    )
    _write(
        tmp_path,
        "common/national_focus/tags.txt",
        """set_cosmetic_tag = TAG_SET_UNUSED
set_cosmetic_tag = TAG_USED
set_cosmetic_tag = TAG_COLOR_USED
has_cosmetic_tag = TAG_MISSING
has_cosmetic_tag = TAG_USED
""",
    )
    _write(
        tmp_path,
        "localisation/english/tags_l_english.yml",
        'l_english:\nTAG_USED:0 "plain"\n',
    )
    validator = _validator(cosmetic.Validator, tmp_path)
    validator.run_all_validations()
    assert _categories(validator) == {
        "missing-cosmetic-tag",
        "unused-cosmetic-tag",
        "unused-cosmetic-color",
    }
    assert any("TAG_MISSING" in issue.message for issue in validator._issues)
    assert any("TAG_SET_UNUSED" in issue.message for issue in validator._issues)
    assert any("TAG_COLOR_UNUSED" in issue.message for issue in validator._issues)


def test_cosmetic_clean_and_staged_scope(tmp_path, monkeypatch):
    _write(tmp_path, "common/countries/cosmetic.txt", "TAG = { }\n")
    _write(tmp_path, "gfx/flags/TAG_FLAG_democratic.tga", "")
    staged_path = _write(
        tmp_path,
        "common/national_focus/staged.txt",
        "set_cosmetic_tag = TAG\nset_cosmetic_tag = TAG_FLAG\nhas_cosmetic_tag = TAG\n",
    )
    clean = _validator(cosmetic.Validator, tmp_path)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    monkeypatch.setenv("MD_STAGED_FILES", str(staged_path))
    staged = _validator(cosmetic.Validator, tmp_path, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []


def test_localisation_processors_cover_syntax_typo_prose_and_references(tmp_path):
    loc = _write(
        tmp_path,
        "localisation/english/test.yml",
        """l_english:
odd:0 "§R broken"
even_bad:0 "§Zbad§!"
sub_key:0 "§Y"
quoted:0 'bad'
novalue:0
bracket:0 "[broken"
typo:0 "seperate [ROOT.GetName] $VALUE$"
prose:0 "bad — `"
clean:0 "§Yok§!"
""",
    )
    assert localisation.process_yml_for_brackets((str(loc),))
    syntax = localisation.process_yml_for_syntax(
        (str(loc), ["R", "Y", "!"], frozenset({"sub_key"}))
    )
    assert {
        item.category for item in syntax if isinstance(item, localisation.Issue)
    } == {"mangled-loc-line"}
    assert any("odd number" in str(item) for item in syntax)
    assert any("unsupported color" in str(item) for item in syntax)
    assert localisation.process_yml_for_mandatory((str(loc),)) == []
    bad_mandatory = _write(tmp_path, "localisation/english/no_header.yml", 'x:0 "x"\n')
    assert localisation.process_yml_for_mandatory((str(bad_mandatory),))
    typo_results = localisation.process_yml_for_typos((str(loc),))
    assert any("seperate" in item for item in typo_results)
    prose_results = localisation.process_yml_for_prose((str(loc),))
    assert {item.category for item in prose_results} == {
        "loc-em-dash",
        "loc-backtick-apostrophe",
    }
    _write(
        tmp_path,
        "interface/core.gfx",
        "\ttextcolors = {\n\t\tQ = { }\n\t}\n",
    )
    assert localisation.get_all_colors(str(tmp_path)) == ["Q"]
    assert localisation._parse_loc_keys_from_text("# comment\nl_english:\n") == []

    script = _write(
        tmp_path,
        "events/refs.txt",
        """localization_key = valid
localization_key = missing
localization_key = [dynamic]
localization_key = GFX_skip
localization_key = EFFECT_skip
custom_effect_tooltip = missing_tt
custom_trigger_tooltip = { tooltip = trigger_missing }
NOT = { tooltip = base_tt }
""",
    )
    localisation._txt_refs_init(frozenset({"valid"}), frozenset({"scripted"}))
    refs = localisation.process_txt_for_loc_key_refs(str(script))
    assert refs == ["missing"]
    tooltip_refs = localisation.process_txt_for_custom_tt_refs(str(script))
    assert "missing_tt - refs.txt" in tooltip_refs
    assert "trigger_missing - refs.txt" in tooltip_refs
    _write(
        tmp_path,
        "events/extra_refs.txt",
        """custom_effect_tooltip = valid
custom_effect_tooltip = GFX_skip
custom_effect_tooltip = [dynamic]
custom_effect_tooltip = cannot_go_higher_than_x
custom_trigger_tooltip = { tooltip = valid }
""",
    )
    assert (
        localisation.process_txt_for_custom_tt_refs(
            str(tmp_path / "events/extra_refs.txt")
        )
        == []
    )
    skipped_txt = _write(tmp_path, ".git/refs.txt", "localization_key = missing\n")
    assert localisation.process_txt_for_loc_key_refs(str(skipped_txt)) == []
    orphan = localisation.process_file_for_orphan_tt_refs(
        (str(script), [r"tooltip\s*=\s*(\S+)"])
    )
    assert "base_tt" in orphan[2]
    assert localisation._extract_not_blocks("NOT = { tooltip = x }") == [
        " tooltip = x "
    ]


def test_localisation_full_run_reports_all_reference_and_style_groups(tmp_path):
    _write(
        tmp_path,
        "interface/core.gfx",
        "malformed core gfx\n",
    )
    _write(
        tmp_path,
        "localisation/english/main_l_english.yml",
        """l_english:
dup:0 "one"
dup:0 "two"
odd:0 "§R broken"
bad_color:0 "§Zbad§!"
quote:0 'bad'
novalue:0
bracket:0 "[broken"
typo:0 "seperate"
prose:0 "bad — `"
sub_a:0 "§Y"
orphan_tt:0 "never used"
used_tt:0 "used"
base_tt:0 "base"
base_tt_NOT:0 "negated"
dynamic_TAG_tt:0 "dynamic"
resistance_bad:0 "bad value"
""",
    )
    _write(
        tmp_path,
        "localisation/english/no_header_l_english.yml",
        'missing_header:0 "value"\n',
    )
    _write(
        tmp_path,
        "localisation/english/00_operations_l_english.yml",
        'skipped_tt:0 "intentionally skipped"\n',
    )
    _write(
        tmp_path,
        "common/scripted_localisation/keys.txt",
        """defined_text = {
\tname = scripted_key
}
""",
    )
    _write(
        tmp_path,
        "events/loc_refs.txt",
        """localization_key = missing_key
localization_key = scripted_key
custom_effect_tooltip = missing_tooltip
custom_trigger_tooltip = { tooltip = missing_trigger }
tooltip = used_tt
NOT = { tooltip = base_tt }
tooltip = dynamic_[TAG]_tt
\tadd_resistance_target = {
\t\ttooltip = resistance_bad
\t}
\tadd_resistance_target = {
\t}
\tadd_resistance_target = {
\t\ttooltip = OTT_vanilla
\t}
""",
    )
    _write(
        tmp_path,
        "common/ideas/other.txt",
        "add_resistance_target = { tooltip = absent_resistance }\n",
    )
    validator = _validator(localisation.Validator, tmp_path)
    validator.run_all_validations()
    categories = _categories(validator)
    assert "loc-typo-watchlist" in categories
    assert "loc-em-dash" in categories
    assert "loc-backtick-apostrophe" in categories
    assert any("missing_key" in issue.message for issue in validator._issues)
    assert any("orphan_tt" in issue.message for issue in validator._issues)
    assert any("resistance_bad" in issue.message for issue in validator._issues)


def test_localisation_clean_and_staged_scope(tmp_path, monkeypatch):
    loc = _write(
        tmp_path,
        "localisation/english/staged_l_english.yml",
        'l_english:\nvalid:0 "plain"\n',
    )
    clean = _validator(localisation.Validator, tmp_path)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    monkeypatch.setenv("MD_STAGED_FILES", str(loc))
    staged = _validator(localisation.Validator, tmp_path, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []


def test_descriptor_parser_and_full_scope(tmp_path, monkeypatch):
    text = '# replace_path = "commented"\nreplace_path = "common/a"\n'
    assert descriptors.parse_replace_paths(text) == [("common/a", 2)]
    _write(tmp_path, "descriptor.mod", text + 'replace_path = "common/a"\n')
    _write(tmp_path, "Millennium_Dawn.mod", 'replace_path = "common/b"\n')
    validator = _validator(descriptors.Validator, tmp_path)
    validator.run_all_validations()
    assert _categories(validator) == {"duplicate-replace-path", "replace-path-sync"}

    clean_root = tmp_path / "clean"
    _write(clean_root, "descriptor.mod", 'replace_path = "common/a"\n')
    _write(clean_root, "Millennium_Dawn.mod", 'replace_path = "common/a"\n')
    clean = _validator(descriptors.Validator, clean_root)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    missing_root = tmp_path / "missing"
    _write(missing_root, "descriptor.mod", "")
    missing = _validator(descriptors.Validator, missing_root)
    missing.run_all_validations()
    assert "missing-mod-file" in _categories(missing)

    monkeypatch.setenv("MD_STAGED_FILES", "")
    staged = _validator(descriptors.Validator, clean_root, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []


def test_scripted_gui_parsers_cover_templates_and_malformed_blocks(tmp_path):
    assert scripted_gui._looks_like_template("name_")
    assert scripted_gui._looks_like_template("x_TAG_y")
    assert not scripted_gui._looks_like_template("ordinary")
    assert scripted_gui._normalise_path(r"./common\\x.txt") == "common//x.txt"
    assert scripted_gui._parse_gui_text("buttonType = {", "interface/broken.gui") == {
        "elements": {},
        "element_files": {},
        "containers": [],
    }
    parsed = scripted_gui._parse_gui_text(
        'containerWindowType = { name = "window" }\n'
        "buttonType = { name = button }\n"
        "buttonType = { visible = yes }\n",
        "interface/test.gui",
    )
    assert set(parsed["elements"]) == {"window", "button"}
    assert parsed["containers"] == ["window"]
    blocks, triggers = scripted_gui._parse_scripted_gui_text(
        "scripted_gui = {\n\tname = {\n"
        "\t\tcontext_type = player_context\n"
        "\t\twindow_name = window\n"
        "\t\tparent_window_name = parent\n"
        "\t\tparent_window_token = token\n"
        "\t\tdirty = global.x\n"
        "\t\tai_test_scopes = test_self_country\n"
        "\t\tentry_container = foo_TAG_bar\n"
        "\t\tbutton_alt_control_click_enabled = { }\n"
        "\t}\n}\n",
        "common/scripted_guis/x.txt",
    )
    assert blocks[0]["parent_window_token"] == "token"
    assert "button_alt_control_click_enabled" in triggers
    assert scripted_gui._parse_scripted_gui_text(
        "scripted_gui = { bad = {", "x.txt"
    ) == ([], set())
    assert scripted_gui._parse_var_writes_text(
        "set_global_variable = { global.written = 1 }\n"
        "set_variable = { var = ROOT.local }\n"
        "global.read = yes\n"
        "dirty = global.only_dirty\n"
    ) == ({"written", "local"}, {"written", "read"})


def test_scripted_gui_full_run_reports_cross_references(tmp_path):
    _write(
        tmp_path,
        "interface/windows.gui",
        """containerWindowType = {
\tname = good_window
\tbuttonType = { name = good_button }
}
""",
    )
    _write(
        tmp_path,
        "common/scripted_guis/test.txt",
        """scripted_gui = {
\tgood = {
\t\tcontext_type = selected_country_context
\t\twindow_name = good_window
\t\tdirty = global.written
\t\tai_test_scopes = test_self_country
\t\tgood_button_click = { }
\t}
\tbad = {
\t\tcontext_type = invalid_context
\t\twindow_name = missing_window
\t\tparent_window_name = missing_parent
\t\tdirty = local_var
\t\tai_test_scopes = invalid_scope
\t\tmissing_button_visible = { }
\t\tentry_container = missing_container
\t\tentry_container = foo_TAG_bar
\t}
\tplayer_scopes = {
\t\tcontext_type = player_context
\t\tai_test_scopes = test_self_country
\t}
\tselected_bad = {
\t\tcontext_type = selected_country_context
\t\tai_test_scopes = invalid_scope
\t}
\tvanilla = {
\t\tcontext_type = player_context
\t\twindow_name = top_bar
\t\tparent_window_name = top_bar_instance
\t}
\tno_context = { dirty = yes }
\tglobal_none = { dirty = global.never_written }
}
""",
    )
    _write(
        tmp_path,
        "events/writes.txt",
        """set_global_variable = { global.written = 1 }
global.local_var = yes
""",
    )
    _write(
        tmp_path,
        "localisation/english/gui_l_english.yml",
        'l_english:\nkey:0 "[!good_button_click] [!never_click]"\n',
    )
    validator = _validator(scripted_gui.Validator, tmp_path)
    validator.run_all_validations()
    assert _categories(validator) == {
        "DEAD_HANDLER",
        "DEAD_BANG_REF",
        "MISSING_WINDOW",
        "MISSING_PARENT_WINDOW",
        "MISSING_ENTRY_CONTAINER",
        "INVALID_CONTEXT_TYPE",
        "DIRTY_SCOPE_MISMATCH",
        "DIRTY_VAR_UNDEFINED",
        "INVALID_AI_TEST_SCOPE",
        "AI_TEST_SCOPES_NOT_APPLICABLE",
    }
    assert any("global.never_written" in issue.message for issue in validator._issues)


def test_scripted_gui_clean_staged_and_cli_boundaries(tmp_path, monkeypatch):
    gui = _write(
        tmp_path,
        "interface/good.gui",
        "containerWindowType = { name = good_window }\n",
    )
    sgui = _write(
        tmp_path,
        "common/scripted_guis/good.txt",
        "scripted_gui = { good = { context_type = player_context } }\n",
    )
    _write(tmp_path, "localisation/english/good.yml", 'l_english:\nkey:0 "ok"\n')
    clean = _validator(scripted_gui.Validator, tmp_path)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    monkeypatch.setenv("MD_STAGED_FILES", str(gui))
    staged = _validator(scripted_gui.Validator, tmp_path, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []

    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_scripted_gui.py", "--path", str(tmp_path), "--workers", "1"],
    )
    with pytest.raises(SystemExit) as result:
        scripted_gui.main()
    assert result.value.code == 0

    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_scripted_gui.py", "--path", str(tmp_path / "missing")],
    )
    with pytest.raises(SystemExit) as result:
        scripted_gui.main()
    assert result.value.code == 1
    assert sgui.exists()


def test_unused_helpers_and_worker_error_paths(tmp_path):
    assert unused._is_false_positive("trigger_year_2020", "x.txt")
    assert unused._is_false_positive("anything", "00_game_rule_triggers.txt")
    assert not unused._is_false_positive("ordinary", "x.txt")
    assert (
        unused.extract_definitions((str(tmp_path / "missing.txt"), str(tmp_path))) == []
    )
    assert (
        unused.scan_file_for_usages(
            (str(tmp_path / "missing.txt"), {"x"}, str(tmp_path))
        )
        == set()
    )
    source = _write(
        tmp_path,
        "common/scripted_effects/effects.txt",
        """if = { ignored = { } }
effect_one = { }
effect_two = { nested = { } }
""",
    )
    # extract_definitions reports os.path.relpath output — native separators.
    relative = str(Path("common/scripted_effects/effects.txt"))
    assert unused.extract_definitions((str(source), str(tmp_path))) == [
        ("effect_one", relative, 2),
        ("effect_two", relative, 3),
    ]
    assert unused.scan_file_for_usages(
        (str(source), {"effect_one", "missing"}, str(tmp_path))
    ) == {"effect_one"}


def test_unused_full_run_reports_effect_and_trigger_findings(tmp_path):
    _write(
        tmp_path,
        "common/scripted_effects/effects.txt",
        """effect_used = { }
effect_unused = { }
effect_parent = {
\teffect_child = yes
}
effect_child = { }
""",
    )
    _write(
        tmp_path,
        "common/scripted_triggers/triggers.txt",
        """trigger_used = { }
trigger_unused = { }
trigger_meta_red = { }
""",
    )
    _write(
        tmp_path,
        "events/calls.txt",
        """effect_used = yes
custom_effect_tooltip = trigger_used
meta_effect = {
\tset_leader_[IDEOLOGY] = yes
\ttrigger_meta_[COLOR] = yes
}
""",
    )
    validator = _validator(unused.Validator, tmp_path)
    validator.run_all_validations()
    assert {issue.category for issue in validator._issues} == {
        "unused-scripted-effect",
        "unused-scripted-trigger",
    }
    assert any("effect_unused" in issue.message for issue in validator._issues)
    assert any("trigger_unused" in issue.message for issue in validator._issues)
    assert not any("effect_child" in issue.message for issue in validator._issues)
    assert not any("trigger_meta_red" in issue.message for issue in validator._issues)


def test_unused_clean_and_staged_scope(tmp_path, monkeypatch):
    _write(tmp_path, "common/scripted_effects/effects.txt", "effect = { }\n")
    _write(tmp_path, "events/call.txt", "effect = yes\n")
    clean = _validator(unused.Validator, tmp_path)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    monkeypatch.setenv("MD_STAGED_FILES", "common/scripted_effects/effects.txt")
    staged = _validator(unused.Validator, tmp_path, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []


def _decision(token: str, body: str = "") -> str:
    return f"\t{token} = {{\n{body}\n\t}}\n"


def _field(name: str, body: str) -> str:
    return f"\t\t{name} = {{\n{body}\n\t\t}}\n"


def test_decision_parsers_and_low_level_branches(tmp_path):
    assert decisions._owner_spans("x = { y = { } }", 0)
    assert decisions._sprite_candidates("category_picture", "x") == ["x"]
    assert decisions._sprite_candidates("category_icon", "x") == [
        "x",
        "GFX_decision_category_x",
    ]
    assert (
        decisions._missing_sprite_message("decision", "x", "[dynamic]", frozenset())
        is None
    )
    assert decisions._slot_for_size(32, 31) == "decision"
    assert decisions._slot_for_size(52, 40) == "category_icon"
    assert decisions._slot_for_size(114, 101) == "category_picture"
    assert decisions._slot_for_size(40, 40) is None
    assert (
        decisions._resolved_sprite("decision", "plain", {"GFX_decision_plain": "x"})
        == "GFX_decision_plain"
    )
    assert decisions._icon_type_message("decision", "x", "none", {}) is None
    assert decisions._extract_from_blocks("FROM = { x = yes }") == [" x = yes "]
    assert decisions._extract_from_blocks("FROM = {") == []
    assert decisions._flat_tag_pins("{ tag = GER NOT = { tag = ITA } }") == {"GER"}
    assert decisions._flat_tag_pins_with_kind("{ original_tag = GER }") == {
        ("original_tag", "GER")
    }
    assert list(decisions._scan_top_level("{ tag = GER GER = { x = yes } }")) == [
        ("tag", "GER"),
        ("scope", "GER"),
    ]
    assert decisions._is_sole_flat_pin("{ tag = GER }", "GER")
    assert not decisions._is_sole_flat_pin("{ tag = GER x = yes }", "GER")
    assert (
        decisions._top_level_field_value('{ name = custom desc = "literal" }', "name")
        == "custom"
    )
    assert decisions._top_level_field_value('{ name = "literal" }', "name") is None
    assert decisions._top_level_neg_pp("{ add_political_power = -12 }") == 12
    assert decisions._top_level_neg_pp("{ if = { add_political_power = -12 } }") is None
    validator = _validator(decisions.Validator, tmp_path)
    assert (
        validator._normalize_block("{ a = yes # comment\n b = no }") == "a = yes b = no"
    )
    assert decisions._unactivated({"a", "b"}, {"a"}) == ["b"]
    assert (
        decisions._unactivated(
            {"cyber_op_slot_1_gps_tracking"}, {"cyber_op_slot_[SLOT]_[TYPE]"}
        )
        == []
    )

    categories = _write(
        tmp_path, "common/decisions/categories/cats.txt", "cat = {\n}\n"
    )
    decision_file = _write(
        tmp_path,
        "common/decisions/decisions.txt",
        "cat = {\n" + _decision("decision_a", "\t\ticon = icon\n") + "}\n",
    )
    assert decisions.parse_all_decisions(str(tmp_path))[0]
    assert (
        decisions.parse_all_decision_factories(str(tmp_path))[0].token == "decision_a"
    )
    assert decisions.parse_all_decision_names(str(tmp_path))[0] == ["decision_a"]
    assert decisions.parse_decision_categories(str(tmp_path)) == {"cat": "cat = {\n}"}
    _write(
        tmp_path,
        "common/decisions/categories/hidden.txt",
        "hidden = {\n\tvisible_when_empty = yes\n}\n",
    )
    assert "hidden" not in decisions.parse_decision_categories(
        str(tmp_path), visible_when_empty=False
    )
    assert (
        decisions._remove_available_block_for_token(
            "\tdecision_a = {\n\t\tavailable = { always = yes }\n\t}\n", "decision_a"
        )
        is not None
    )
    assert (
        decisions._remove_available_block_for_token("decision_a = { }", "missing")
        is None
    )
    assert decisions.parse_categories_with_decisions(str(tmp_path)) == {
        "cat": ["decision_a"]
    }
    assert decisions._is_category_file(str(categories))
    assert decisions._find_decision_file(str(tmp_path), "decisions.txt") == str(
        decision_file
    )
    assert decisions._find_decision_file(str(tmp_path), "missing.txt") is None
    assert decisions._int_literal("12") == 12
    with pytest.raises(ValueError):
        decisions._int_literal("bad")


def test_decisions_full_run_exercises_finding_categories(tmp_path):
    category_text = """cat_allowed = {
\tallowed = { original_tag = GER }
}
cat_unchecked = {
}
cat_empty = {
}
cat_orphan = {
}
cat_ai_disabled = {
	allowed = { always = no }
}
"""
    _write(tmp_path, "common/decisions/categories/categories.txt", category_text)
    common = "\t\ticon = icon\n"
    decisions_text = "cat_allowed = {\n"
    decisions_text += _decision(
        "decision_dup",
        common
        + _field("allowed", "\t\t\toriginal_tag = GER")
        + _field("visible", "\t\t\ttag = GER\n\t\t\tGER = { has_war = yes }")
        + "\t\tdays_remove = 2\n"
        + _field("remove_effect", "\t\t\tadd_stability = 1")
        + "\t\tcreate_wargoal = yes\n",
    )
    decisions_text += _decision(
        "category_recheck_allowed",
        common + _field("visible", "\t\t\toriginal_tag = GER"),
    )
    decisions_text += "}\ncat_unchecked = {\n"
    decisions_text += _decision("decision_dup", common)
    decisions_text += _decision("no_allowed", common)
    decisions_text += "}\ncat_empty = { }\n"
    decisions_text += _decision(
        "manual_unused",
        common + _field("allowed", "\t\t\talways = no"),
    )
    decisions_text += _decision(
        "manual_used",
        common + _field("allowed", "\t\t\talways = no"),
    )
    decisions_text += _decision(
        "missing_ai",
        common,
    )
    decisions_text += _decision(
        "selectable_mission",
        common + "\t\tdays_mission_timeout = 3\n\t\tselectable_mission = yes\n",
    )
    decisions_text += _decision(
        "nonselect_mission",
        common + "\t\tdays_mission_timeout = 3\n\t\tai_will_do = { base = 1 }\n",
    )
    decisions_text += _decision(
        "custom_cost",
        common + _field("custom_cost_trigger", "\t\t\t has_political_power > 10"),
    )
    decisions_text += _decision(
        "target_no_set",
        common + _field("target_trigger", "\t\t\thas_war = yes"),
    )
    decisions_text += _decision(
        "from_no_trigger",
        common
        + _field("targets", "\t\t\tGER = { }\n")
        + _field("visible", "\t\t\tFROM = { has_war = yes }"),
    )
    decisions_text += _decision(
        "root_visible",
        common
        + _field("targets", "\t\t\tGER = { }\n")
        + _field("visible", "\t\t\thas_war = yes"),
    )
    decisions_text += _decision(
        "from_duplicate",
        common
        + _field("targets", "\t\t\tGER = { }\n")
        + _field("target_trigger", "\t\t\tFROM = { has_war = yes }")
        + _field("visible", "\t\t\tFROM = { has_war = yes }"),
    )
    decisions_text += _decision(
        "from_move",
        common
        + _field("targets", "\t\t\tGER = { }\n")
        + _field(
            "target_trigger",
            "\t\t\tFROM = { has_war = yes }",
        )
        + _field(
            "visible",
            "\t\t\tFROM = { has_war = yes }\n\t\t\tFROM = { has_stability = yes }",
        ),
    )
    decisions_text += _decision(
        "from_unscoped",
        common + _field("visible", "\t\t\tFROM = { has_war = yes }"),
    )
    decisions_text += _decision(
        "random_decision",
        common + _field("complete_effect", "\t\t\trandom = { chance = 50 }"),
    )
    decisions_text += _decision(
        "tag_checks",
        common
        + _field("allowed", "\t\t\ttag = GER\n\t\t\toriginal_tag = GER")
        + _field("visible", "\t\t\ttag = GER"),
    )
    decisions_text += _decision(
        "category_recheck",
        common + _field("visible", "\t\t\toriginal_tag = GER"),
    )
    decisions_text += _decision(
        "pp_hidden",
        common + _field("complete_effect", "\t\t\tadd_political_power = -5"),
    )
    decisions_text += _decision(
        "pp_double",
        common
        + "\t\tcost = 5\n"
        + _field("complete_effect", "\t\t\tadd_political_power = -3"),
    )
    decisions_text += _decision(
        "same_visible_available",
        common
        + _field("visible", "\t\t\thas_war = yes")
        + _field("available", "\t\t\thas_war = yes"),
    )
    decisions_text += _decision(
        "bare_trigger",
        common + _field("available", "\t\t\tpolitical_power < 5"),
    )
    decisions_text += _decision(
        "missing_loc",
        common
        + "\t\tname = missing_name\n\t\tdesc = missing_desc\n\t\tcustom_cost_text = missing_cost\n",
    )
    decisions_text += _decision(
        "missing_log",
        common + _field("complete_effect", "\t\t\tadd_stability = 1"),
    )
    decisions_text += _decision(
        "late_log",
        common
        + _field("complete_effect", '\t\t\tadd_stability = 1\n\t\t\tlog = "late"'),
    )
    decisions_text += _decision(
        "mission_visible",
        common
        + "\t\tdays_mission_timeout = 3\n"
        + _field("visible", "\t\t\thas_war = yes"),
    )
    decisions_text += _decision(
        "mission_script",
        common
        + "\t\tdays_mission_timeout = 3\n\t\tactivation = { always = no }\n"
        + _field("visible", "\t\t\thas_war = yes"),
    )
    decisions_text += _decision(
        "war_target",
        common + "\t\ttargets = { GER }\n\t\twar_with_on_complete = FROM\n",
    )
    decisions_text += _decision(
        "war_all",
        common + "\t\twar_with_on_remove = FROM\n\t\twar_with_on_timeout = FROM\n",
    )
    decisions_text += _decision(
        "war_no_hint",
        common + _field("complete_effect", "\t\t\tcreate_wargoal = yes"),
    )
    decisions_text += _decision(
        "cancel_missing_visible",
        common + "\t\tcancel_if_not_visible = yes\n",
    )
    decisions_text += _decision(
        "custom_pp_hint",
        common + _field("custom_cost_trigger", "\t\t\thas_political_power > 10"),
    )
    decisions_text += _decision(
        "state_bad",
        common
        + "\t\tstate_target = any_owned_state\n"
        + _field("targets", "\t\t\tGER = { }"),
    )
    decisions_text += _decision(
        "mission_only",
        common
        + "\t\ttimeout_effect = { }\n\t\tactivation = { always = no }\n"
        + "\t\tis_good = yes\n\t\tselectable_mission = yes\n\t\twar_with_on_timeout = GER\n"
        + "\t\twar_with_target_on_timeout = yes\n",
    )
    decisions_text += _decision(
        "orphan_remove",
        common + _field("remove_effect", "\t\t\tadd_stability = 1"),
    )
    decisions_text += _decision(
        "orphan_modifiers",
        common + "\t\ttargets_dynamic = yes\n\t\ttarget_non_existing = yes\n",
    )
    decisions_text += _decision(
        "skip_ai_available",
        common + _field("available", "\t\t\t is_ai = no"),
    )
    decisions_text += _decision(
        "skip_ai_visible",
        common + _field("visible", "\t\t\t always = no"),
    )
    decisions_text += "}\ncat_ai_disabled = {\n"
    decisions_text += _decision("category_ai_skip", common)
    decisions_text += "}\n"
    _write(tmp_path, "common/decisions/decisions.txt", decisions_text)
    _write(
        tmp_path,
        "events/activations.txt",
        "activate_targeted_decision = { decision = manual_used }\n",
    )
    _write(
        tmp_path,
        "common/bop/bop.txt",
        "decision_category = cat_empty\n",
    )
    _write(
        tmp_path,
        "localisation/english/decisions_l_english.yml",
        'l_english:\nmissing_ai:0 "Missing AI"\n',
    )
    # validate_missing_icons skips itself below 1000 indexed sprites. Without a
    # mod-side index the check only ran where a vanilla install is discoverable,
    # so it passed locally and reported nothing on CI.
    _write(
        tmp_path,
        "interface/filler.gfx",
        "spriteTypes = {\n"
        + "".join(
            f'\tspriteType = {{ name = "GFX_filler_{i}" }}\n' for i in range(1000)
        )
        + "}\n",
    )

    validator = _validator(decisions.Validator, tmp_path)
    validator.run_all_validations()
    missing_icons = _validator(decisions.Validator, tmp_path, missing_icons=True)
    missing_icons.validate_missing_icons()
    assert "missing-decision-icon" in _categories(missing_icons)
    categories = _categories(validator)
    expected = {
        "missing-decision-localisation",
        "missing-decision-log",
        "decision-log-not-first",
        "bare-trigger-name",
    }
    assert expected <= categories
    for marker in (
        "Decision AI factor issues",
        "Decisions in categories without allowed",
        "Decisions that declare war",
        "Decisions with custom_cost_trigger",
        "Decisions with redundant tag checks",
        "Missions with visible block",
        "Regular decisions using mission-only",
        "Targeted decisions using war_with_on_",
        "Decisions charging political power",
        "Decisions double-charging PP",
        "Decisions using FROM without",
        "Decisions with FROM checks in visible/available",
        "Decisions with `allowed` redundant",
        "Decisions with cancel_if_not_visible",
        "Decisions with identical visible and available",
        "Decisions with tag/original_tag",
        "Decisions with target_root_trigger",
        "Decisions with targets_dynamic",
        "Duplicated decisions found",
        "Repeatable decisions",
        "State-targeted decisions",
        "Targeted decisions with FROM checks",
        "Unused decision categories",
        "Unused decisions",
        "Decisions spending political power",
        "Decisions with remove_effect",
    ):
        assert any(marker in category for category in categories), marker
    assert any(
        issue.category == "missing-decision-localisation" for issue in validator._issues
    )
    assert any("manual_unused" in issue.message for issue in validator._issues)
    assert any("pp_hidden" in issue.message for issue in validator._issues)
    assert any("orphan_modifiers" in issue.message for issue in validator._issues)
    assert any(
        "from_move" in issue.message and "move the FROM" in issue.message
        for issue in validator._issues
    )


def test_decisions_clean_staged_and_cli_strict_boundaries(tmp_path, monkeypatch):
    _write(tmp_path, "common/decisions/categories/cat.txt", "cat = { }\n")
    _write(
        tmp_path,
        "common/decisions/clean.txt",
        "cat = {\n"
        + _decision("clean_decision", "\t\tai_will_do = { base = 0 }\n")
        + "}\n",
    )
    _write(
        tmp_path,
        "localisation/english/clean.yml",
        'l_english:\nclean_decision:0 "Clean"\n',
    )
    clean = _validator(decisions.Validator, tmp_path)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    monkeypatch.setenv("MD_STAGED_FILES", "common/decisions/clean.txt")
    staged = _validator(decisions.Validator, tmp_path, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_decisions.py",
            "--path",
            str(tmp_path),
            "--strict",
            "--workers",
            "1",
        ],
    )
    with pytest.raises(SystemExit) as result:
        run_validator_main(
            decisions.Validator,
            "decisions",
            extra_args_fn=decisions._add_extra_args,
        )
    assert result.value.code == 0

    file_path = _write(tmp_path, "not-a-mod.txt", "content\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_decisions.py", "--path", str(file_path)],
    )
    with pytest.raises(SystemExit) as result:
        run_validator_main(decisions.Validator, "decisions")
    assert result.value.code == 1


def test_decision_fix_paths_rewrite_only_synthetic_files(tmp_path):
    decision_file = _write(
        tmp_path,
        "common/decisions/fix.txt",
        "cat = {\n"
        + _decision("missing_ai", "\t\tvisible = { has_war = yes }\n")
        + _decision(
            "same_blocks",
            _field("visible", "\t\t\thas_war = yes")
            + _field("available", "\t\t\thas_war = yes"),
        )
        + "}\n",
    )
    fixer = _validator(decisions.Validator, tmp_path, fix=True)
    fixer.validate_ai_factors()
    assert "ai_will_do = {" in decision_file.read_text()
    fixer.validate_visible_equals_available()
    assert "same_blocks = {\n\t\tvisible" in decision_file.read_text()
    assert "\n\t\tavailable =" not in decision_file.read_text()


def test_cli_strict_exits_nonzero_for_descriptor_findings(tmp_path, monkeypatch):
    _write(tmp_path, "descriptor.mod", 'replace_path = "a"\n')
    _write(tmp_path, "Millennium_Dawn.mod", 'replace_path = "b"\n')
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_mod_descriptors.py", "--path", str(tmp_path), "--strict"],
    )
    with pytest.raises(SystemExit) as result:
        run_validator_main(descriptors.Validator, "descriptors")
    assert result.value.code == 1


def test_formable_commitment_helper_covers_drift_rows():
    update = decisions.DecisionFactory(
        "\tAAA_update_flag = {\n\t\tavailable = {\n\t\t\t1 = { }\n\t\t}\n\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    integrate = decisions.DecisionFactory(
        "\tAAA_integrate_start = {\n"
        "\t\tformable_committed_size = 1\n"
        "\t\tset_variable = { formable_committed_id = 1 }\n"
        "\t\tset_variable = { formable_committed_size = 1 }\n"
        "\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    conflict = decisions.DecisionFactory(
        "\tZZZ_integrate_start = {\n"
        "\t\tformable_committed_size = 9\n"
        "\t\tvar = formable_committed_size value = 8\n"
        "\t\tset_variable = { formable_committed_id = 1 }\n"
        "\t\tset_variable = { formable_committed_size = 9 }\n"
        "\t\tset_variable = { formable_committed_id = 2 }\n"
        "\t\tset_variable = { formable_committed_size = 9 }\n"
        "\t\tNOT = { check_variable = { formable_committed_id = 9 } }\n"
        "\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    zzz_update = decisions.DecisionFactory(
        "\tZZZ_update_flag = {\n"
        "\t\tavailable = {\n\t\t\t1 = { }\n\t\t\t2 = { }\n\t\t}\n"
        "\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    bbb_update = decisions.DecisionFactory(
        "\tBBB_update_flag = {\n\t\tavailable = {\n\t\t\t1 = { }\n\t\t}\n\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    no_gate = decisions.DecisionFactory(
        "\tBBB_integrate_start = {\n\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    bbb_commit = decisions.DecisionFactory(
        "\tBBB_buy_core_state = {\n"
        "\t\tformable_committed_size = 1\n"
        "\t\tset_variable = { formable_committed_id = 1 }\n"
        "\t\tset_variable = { formable_committed_size = 1 }\n"
        "\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    no_update = decisions.DecisionFactory(
        "\tCCC_integrate_start = {\n\t}\n",
        source_basename="formable_nation_decisions.txt",
    )
    not_formable = decisions.DecisionFactory(
        "\tordinary = {\n\t}\n", source_basename="formable_nation_decisions.txt"
    )
    assert decisions._FORMABLE_TAG_RE.match(conflict.token)
    assert decisions._COMMIT_PAIR_RE.findall(conflict.raw) == [("1", "9"), ("2", "9")]
    rows = decisions._find_formable_commitment_rows(
        [
            update,
            integrate,
            conflict,
            zzz_update,
            bbb_update,
            no_gate,
            bbb_commit,
            no_update,
            not_formable,
        ],
        {
            "focus.txt": (
                "set_variable = { formable_committed_id = 99 }\n"
                "set_variable = { formable_committed_size = 2 }\n"
                "set_variable = { formable_committed_id = 1 }\n"
                "set_variable = { formable_committed_size = 2 }\n"
                "var = formable_committed_size value = 8"
            )
        },
    )
    assert any("conflicting commit ids" in row for row in rows)
    assert any("size literal 9" in row for row in rows)
    assert any("commit id 1 collides" in row for row in rows)
    assert any("unknown formable id 9" in row for row in rows)
    assert any("focus commit references unknown" in row for row in rows)
    assert any("focus commit size 2" in row for row in rows)
    assert any("focus guard size 8" in row for row in rows)
    assert any("no update_flag" in row for row in rows)
    assert any("not a formable decision shape" in row for row in rows)
