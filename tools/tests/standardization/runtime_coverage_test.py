"""Branch-oriented coverage for the small HOI4 standardization tools."""

import argparse
import sys
from pathlib import Path

import cleanup_effect_tooltip as effect_tooltip
import cleanup_or
import pytest
import standardize_focus_tree as focus_tree
import standardize_history as history
import standardize_localisation as localisation
import standardize_mio as mio
import standardize_staged
import strip_idea_allowed_gates as idea_gates
from common_utils import (
    BaseStandardizer,
    apply_brace_stack,
    block_has_log,
    code_of_line,
    collapse_blank_runs,
    compact_icon,
    compact_search_filters,
    emit_comments,
    find_block_span,
    inject_log_after_brace,
    join_groups,
    read_lines_for_standardization,
    resolve_output_file_and_backup,
    write_standardized_output,
)


def _write(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    with open(path, "w", encoding=encoding, newline="") as handle:
        handle.write(text)


def _read(path: Path, *, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding, newline="") as handle:
        return handle.read()


def test_effect_tooltip_check_inline_and_idempotence(tmp_path, capsys):
    source = tmp_path / "effects.txt"
    original = """root = {
\teffect_tooltip = { custom_effect_tooltip = one custom_effect_tooltip = two }
\tnested = { effect_tooltip = { custom_effect_tooltip = embedded } } # keep
\teffect_tooltip = {
\t\tcustom_effect_tooltip = three
\t}
\teffect_tooltip = { add_stability = 0.1 }
}
"""
    _write(source, original)

    issues = effect_tooltip.find_redundant_effect_tooltip_wrappers(
        original.splitlines(keepends=True)
    )
    assert [line for line, _message in issues] == [2, 3, 4]

    effect_tooltip.main([str(source)], check_only=True)
    assert _read(source) == original
    assert "Would collapse 3" in capsys.readouterr().out

    assert effect_tooltip.main([str(source)]) == 3
    output = _read(source)
    assert output.count("custom_effect_tooltip = one") == 1
    assert output.count("custom_effect_tooltip = two") == 1
    assert "nested = { custom_effect_tooltip = embedded } # keep" in output
    assert "custom_effect_tooltip = three" in output
    assert "add_stability" in output
    assert effect_tooltip.process_file(str(source)) == 0
    assert _read(source) == output


def test_effect_tooltip_malformed_and_decode_errors(tmp_path, capsys):
    assert effect_tooltip._custom_tooltip_keys("") is None
    assert effect_tooltip._custom_tooltip_keys("custom_effect_tooltip = { x }") is None
    assert effect_tooltip._custom_tooltip_keys("# custom_effect_tooltip = x") is None
    assert effect_tooltip._custom_tooltip_keys("custom_effect_tooltip = x") == ["x"]

    line = 'x = { effect_tooltip = { custom_effect_tooltip = x } } # "# not code"\n'
    fixed, count = effect_tooltip._fix_inline_line(line)
    assert count == 1
    assert fixed.endswith('# "# not code"\n')

    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"effect_tooltip = { custom_effect_tooltip = x }\n\xff")
    assert effect_tooltip.process_file(str(invalid)) == 0
    assert "undecodable UTF-8" in capsys.readouterr().err


def test_cleanup_or_nested_context_detection_and_idempotence(tmp_path):
    source = tmp_path / "conditions.txt"
    original = """root = {
\tOR = {
\t\tNOT = {
\t\t\thas_country_flag = FLAG_one
\t\t}
\t}
\tavailable = { OR = { has_government = democratic } }
\tAND = {
\t\thas_war = no
\t\thas_stability > 0.5
\t}
\tOR = { has_war = no has_stability > 0.5 }
\tNOT = { AND = { has_war = no has_stability > 0.5 } }
}
"""
    _write(source, original)

    assert cleanup_or.find_single_condition_or_blocks(
        original.splitlines(keepends=True)
    ) == [
        (
            2,
            "redundant OR = { } wrapper around single condition"
            " -- run tools/cleanup_or.py to fix",
        ),
        (
            7,
            "redundant OR = { } wrapper around single condition"
            " -- run tools/cleanup_or.py to fix",
        ),
    ]
    and_issues = cleanup_or.find_redundant_and_blocks(
        original.splitlines(keepends=True)
    )
    assert [line for line, _message in and_issues] == [8]

    assert cleanup_or.process_file(str(source)) is True
    once = _read(source)
    assert cleanup_or.process_file(str(source)) is False
    assert _read(source) == once
    assert "available = { has_government = democratic }" in once
    assert "\thas_war = no\n\thas_stability > 0.5" in once
    assert "NOT = { AND = { has_war = no has_stability > 0.5 } }" in once
    assert "OR = { has_war = no has_stability > 0.5 }" in once


def test_cleanup_or_inline_comment_and_malformed_input(tmp_path, capsys):
    lines = [
        "trigger = { OR = { has_country_flag = x } } # braces }\n",
        "trigger = { OR = { has_country_flag = x has_war = no } }\n",
        "OR = {\n",
        "\thas_war = no\n",
        "\thas_stability > 0.5\n",
        "",  # no closer: the malformed tail must not be rewritten
    ]
    simplified = cleanup_or.simplify_or_block(lines)
    assert "trigger = { has_country_flag = x } # braces }\n" in simplified
    assert "trigger = { OR = { has_country_flag = x has_war = no } }\n" in simplified
    assert simplified[-4:] == lines[-4:]
    assert cleanup_or.simplify_and_block(simplified) == simplified

    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"OR = { has_war = no }\n\xff")
    assert cleanup_or.process_file(str(invalid)) is False
    assert "undecodable UTF-8" in capsys.readouterr().err


def test_cleanup_or_directory_walk_prunes_resources(tmp_path, capsys):
    normal = tmp_path / "normal.txt"
    excluded = tmp_path / "resources" / "reference.txt"
    excluded.parent.mkdir()
    _write(normal, "x = { OR = { has_war = no } }\n")
    _write(excluded, "x = { OR = { has_war = no } }\n")

    cleanup_or.main([str(tmp_path)])
    assert _read(normal) == "x = { has_war = no }\n"
    assert _read(excluded) == "x = { OR = { has_war = no } }\n"
    assert "Simplified OR blocks" in capsys.readouterr().out


def test_common_utils_boundaries_and_base_standardizer(tmp_path, monkeypatch):
    assert code_of_line('\tname = "a } b" # }') == '\tname = "     " '
    assert find_block_span(["x = {", "\ty = 1", "}", "}"], 0, 4) == (2, 0)
    assert find_block_span(["x = {"], 0, 4) is None

    assert compact_search_filters([]) == "search_filters = { }"
    assert (
        compact_search_filters(
            ["\tsearch_filters = {", "\t\tnational_focus", "\t\tpolitics", "\t}"]
        )
        == "search_filters = { national_focus politics }"
    )
    assert compact_icon([]) == "icon = GFX_goal_generic_support_the_left_wing"
    assert compact_icon([" icon = GFX_a "]) == "icon = GFX_a"
    assert compact_icon(["icon = {", "\tfoo", "}"]) == "icon = {\n\tfoo\n}"
    assert collapse_blank_runs(["a", "", "", "b"], max_blank=0) == ["a", "b"]
    assert join_groups([["", "a", ""], [], ["b", ""]]) == ["a", "", "b"]

    out = []
    emit_comments(out, ["", " # note  "])
    assert out == [" # note"]
    assert block_has_log(["x = {", "log = yes", "}"])
    assert not block_has_log([])
    assert inject_log_after_brace(["plain"], "log") == ["plain"]
    assert inject_log_after_brace(["x = {", "}"], "\tlog") == ["x = {", "\tlog", "}"]
    stack = []
    apply_brace_stack("x = { y = { z = 1 } }", stack)
    assert stack == []

    missing = tmp_path / "missing.txt"
    assert read_lines_for_standardization(str(missing)) is None
    output = tmp_path / "out.txt"
    assert write_standardized_output(
        str(output), ["foo = 1", "", "bar = 2"], start_time=0, processed_count=2
    )
    assert _read(output) == "foo = 1\n\nbar = 2\n"

    def fail_write(_path, _text):
        raise OSError("full")

    monkeypatch.setattr("common_utils.atomic_write_text", fail_write)
    assert not write_standardized_output(
        str(output), ["foo = 1"], start_time=0, processed_count=1
    )


class _MiniStandardizer(BaseStandardizer):
    def get_block_pattern(self):
        return r"^thing\s*=\s*{"

    def extract_properties(self, block_lines):
        return {"id": block_lines[1].strip()}

    def format_block(self, props):
        return ["thing = {", f"\t{props['id']}", "}"]


def test_base_standardizer_matching_and_no_match(tmp_path):
    source = tmp_path / "mini.txt"
    output = tmp_path / "mini-out.txt"
    _write(source, "header = yes\nthing = {\n\tvalue = yes\n}\n")

    standardizer = _MiniStandardizer()
    assert standardizer.standardize_file(str(source), str(output))
    assert standardizer.processed_count == 1
    assert _read(output) == "header = yes\nthing = {\n\tvalue = yes\n}\n"

    untouched = tmp_path / "untouched.txt"
    _write(untouched, "header = yes\n")
    assert _MiniStandardizer().standardize_file(str(untouched), str(untouched))
    assert _read(untouched) == "header = yes\n"


def test_common_utils_output_and_backup_edges(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination.txt"
    _write(source, "value = yes\n")
    args = argparse.Namespace(
        input_file=str(source), output=str(destination), backup=True
    )
    assert resolve_output_file_and_backup(args) == str(destination)
    assert list(tmp_path.glob("source.txt.backup.*"))

    missing = argparse.Namespace(
        input_file=str(tmp_path / "no.txt"), output=None, backup=False
    )
    with pytest.raises(SystemExit):
        resolve_output_file_and_backup(missing)

    monkeypatch.setattr("common_utils.create_backup", lambda _path: "")
    with pytest.raises(SystemExit):
        resolve_output_file_and_backup(
            argparse.Namespace(input_file=str(source), output=None, backup=True)
        )


_FOCUS_FIXTURE = """focus_tree = {
\tcontinuous_focus_position = { x = 5700 y = 2000 }
\tinitial_show_position = { x = 2 y = 0 }
\toffset = {
\t\tx = 1
\t\ty = 2
\t\ttrigger = { has_country_flag = TST_ready }
\t}
\tshortcut = {
\t\tname = TST_shortcut
\t\ttarget = TST_focus
\t\tscroll_wheel_factor = 1
\t\ttrigger = { has_country_flag = TST_ready }
\t\tpriority = 2
\t}
\tinlay_window = {
\t\tid = TST_window
\t\tposition = { x = 1 y = 2 }
\t\toverride_position = { x = 3 y = 4 }
\t\tvisible = yes
\t}
\tfocus = {
\t\tid = TST_focus # comment
\t\ticon = GFX_goal_generic_political_pressure
\t\ttext_icon = TST_text
\t\toverlay = GFX_overlay
\t\tx = 0
\t\ty = 1
\t\trelative_position_id = TST_parent
\t\toffset = {
\t\t\tx = 2
\t\t\ty = 3
\t\t\ttrigger = { has_war = no }
\t\t}
\t\tallow_branch = { has_country_flag = TST_ready }
\t\tprerequisite = { focus = TST_parent }
\t\tmutually_exclusive = { focus = TST_other }
\t\twill_lead_to_war_with = TST_enemy
\t\tsearch_filters = {
\t\t\tpolitics
\t\t\tnational_focus
\t\t}
\t\tavailable = { has_war = no }
\t\tbypass = { has_country_flag = TST_done }
\t\tcancel = { has_war = yes }
\t\tselect_effect = { add_political_power = 1 }
\t\tcompletion_reward = {
\t\t\tadd_stability = 0.1
\t\t}
\t\tcompletion_reward_joint_originator = { add_political_power = 2 }
\t\tcompletion_reward_joint_member = { add_political_power = 3 }
\t\tbypass_effect = { add_political_power = 4 }
\t\tunknown_property = yes
\t\tai_will_do = { factor = 0.5 }
\t}
}
shared_focus = {
\tid = TST_shared
\tcompletion_reward = { add_political_power = 1 }
}
joint_focus = {
\tid = TST_joint
\tai_will_do = { factor = 0.2 }
}
"""


def test_focus_simple_handlers_realistic_fixture_and_idempotence(tmp_path):
    source = tmp_path / "focus.txt"
    _write(source, _FOCUS_FIXTURE)
    assert focus_tree.standardize_focus_tree(str(source), str(source), verbose=True)
    once = _read(source)
    assert "continuous_focus_position = { x = 5700 y = 2000 }" in once
    assert "initial_show_position = { x = 2 y = 0 }" in once
    assert "\tshortcut = {" in once
    assert "\tinlay_window = {" in once
    assert 'Focus TST_focus"' in once
    assert 'Focus TST_shared"' in once
    assert "base = 0.5" in once
    assert "# shortcut" not in once
    assert focus_tree.standardize_focus_tree(str(source), str(source))
    assert _read(source) == once


def test_focus_helper_malformed_and_boundary_shapes():
    assert focus_tree.is_empty_block([])
    assert focus_tree.is_empty_block(["available = { }"])
    assert not focus_tree.is_empty_block(["available = { has_war = no }"])
    assert focus_tree._split_block(["x = { bad"]) is None
    assert focus_tree._split_block(["x = { value } # note"]) is None
    split = focus_tree._split_block(
        ["x = { value } # note"], allow_trailing_comment=True
    )
    assert split == ("x = {", ["\tvalue"], "} # note")
    assert focus_tree._merge_duplicate_blocks(
        ["x = { value } # note"], ["x = { y }"]
    ) == [
        "x = { value } # note",
        "x = { y }",
    ]
    assert focus_tree.effect_block_with_log([], "TST_empty") == []
    assert focus_tree.format_continuous_focus_position_block(
        ["continuous_focus_position = { x = 1 }"]
    ) == ["continuous_focus_position = { x = 1 }"]
    assert focus_tree.format_initial_show_position_block(
        ["initial_show_position = { focus = TST_focus }"]
    ) == ["\tinitial_show_position = { focus = TST_focus }"]
    assert focus_tree.format_shortcut_block(["shortcut = { }"]) == ["\tshortcut = { }"]
    assert focus_tree.format_inlay_window_block(["inlay_window = { }"]) == [
        "\tinlay_window = { }"
    ]


def _history_mod_fixture(root: Path) -> Path:
    ideas = root / "common" / "ideas"
    dynamic = root / "common" / "dynamic_modifiers"
    history_dir = root / "history" / "countries"
    ideas.mkdir(parents=True)
    dynamic.mkdir(parents=True)
    history_dir.mkdir(parents=True)
    _write(
        ideas / "AA_law_test.txt",
        """ideas = {
\tlaw_category = {
\t\tlaw = yes
\t\tlaw_income = {
\t\t\tname = law_income
\t\t}
\t}
}
""",
    )
    _write(
        ideas / "factions.txt",
        """ideas = {
\tinternal_factions = {
\t\tfaction_support = {
\t\t\tname = faction_support
\t\t}
\t}
\tmd_category = {
\t\tmd_example = {
\t\t\tname = md_example
\t\t}
\t}
}
""",
    )
    _write(
        dynamic / "modifiers.txt",
        """TST_modifier = {
\ticon = x
\tvalue = TST_modifier_value
\tnested = {
\t\tfield = TST_nested_value
\t}
}
""",
    )
    history_file = history_dir / "TST.txt"
    _write(
        history_file,
        """capital = 652
2000.1.1 = {
\t# Set Ideas
\tadd_ideas = {
\t\tlaw_income
\t\tmd_example
\t\tfaction_support
\t\tTST_country
\t\tmd_example
\t}
\tadd_dynamic_modifier = { modifier = TST_modifier }
\tset_variable = { var = TST_modifier_value value = 1 }
\tset_variable = { var = global_unclaimed value = 2 }
\tset_variable = { var = TST_country_value value = 3 }
\tadd_to_array = { array = global_array value = TST_country }
\tcomplete_special_project = sp:sp_space_program
\tset_technology = { infantry_weapons = 1 }
\tif = { limit = { has_dlc = yes } set_technology = { armor = 1 } }
\tcreate_equipment_variant = { type = infantry_equipment_0 }
\tcreate_equipment_variant = { type = airframe }
\tcreate_equipment_variant = { type = destroyer_hull }
\tset_oob = TST_army
\tset_air_oob = TST_air
\tset_naval_oob = TST_navy
\tstart_politics_input = { }
\tstartup_politics = { }
\tcreate_country_leader = { name = TST_leader }
\tset_popularities = { democratic = 0.5 }
\tset_politics = { ruling_party = democratic }
\tadd_opinion_modifier = { target = USA modifier = good }
\treverse_add_opinion_modifier = { target = USA modifier = bad }
\tset_power_balance = { id = TST_balance }
\t652 = { buildings = { infrastructure = 1 } }
\tset_country_flag = TST_started
\tclr_country_flag = TST_old
\tother_statement = yes
}
""",
    )
    return history_file


def test_history_loaders_and_all_statement_groups(tmp_path):
    history._IDEA_CACHE.clear()
    history._MODIFIER_CACHE.clear()
    root = tmp_path / "mod"
    history_file = _history_mod_fixture(root)
    assert history._detect_mod_root(str(history_file)) == str(root)
    assert history._iter_file_lines(str(root / "missing.txt")) is None
    law, factions = history._load_idea_classification(str(root))
    assert "law_income" in law
    assert "faction_support" in factions
    modifier_vars = history._load_modifier_variables(str(root))
    assert modifier_vars["TST_modifier"] >= {"TST_modifier_value", "TST_nested_value"}

    standardizer = history.HistoryStandardizer(mod_root=str(root))
    block = history.extract_block(_read(history_file).splitlines(keepends=True), 1)[0]
    assert standardizer.extract_properties(block)["ideas"]
    standardizer._ensure_classification(str(history_file))
    props = standardizer.extract_properties(block)
    assert props["ideas"]
    assert standardizer._classify_idea("law_income") == "law"
    assert any("# Laws" in line for line in standardizer.format_block(props))
    assert standardizer.standardize_file(str(history_file), str(history_file))
    output = _read(history_file)
    assert "# Laws" in output
    assert "# Internal Factions" in output
    assert "# Country Content" in output
    assert "# Dynamic Modifiers" in output
    assert "# Air Force Equipment" in output
    assert "# Naval Equipment" in output
    assert output.count("set_country_flag = TST_started") == 1
    assert output.count("clr_country_flag = TST_old") == 1
    assert "other_statement = yes" in output
    assert standardizer.standardize_file(str(history_file), str(history_file))
    assert _read(history_file) == output


def test_history_without_mod_root_degrades_cleanly(tmp_path):
    source = tmp_path / "history.txt"
    _write(source, "2000.1.1 = {\n\tset_country_flag = TST_flag\n}\n")
    standardizer = history.HistoryStandardizer()
    assert standardizer.standardize_file(str(source), str(source))
    assert standardizer._law == set()
    assert standardizer._faction == set()
    assert standardizer._modvars == {}
    assert history._detect_mod_root(str(tmp_path)) is None


def _localisation_mod_fixture(root: Path) -> Path:
    files = {
        "common/national_focus/focus.txt": "focus = {\n\tid = TST_focus\n}\n",
        "common/ideas/ideas.txt": "ideas = {\n\t\tTST_idea = {\n\t\t}\n}\n",
        "common/dynamic_modifiers/modifiers.txt": "TST_modifier = {\n}\n",
        "common/opinion_modifiers/opinions.txt": "\tTST_opinion = {\n\t}\n",
        "common/decisions/categories/sub.txt": "TST_category = {\n\tTST_decision = {\n\t}\n}\n",
        "events/events.txt": "add_namespace = tst_events\n",
        "common/characters/characters.txt": "\tTST_character = {\n\t}\n",
        "common/military_industrial_organization/organizations/mio.txt": "TST_org = {\n\tname = TST_mio\n}\n",
        "common/unit_leader/traits.txt": "\tTST_trait = {\n\t}\n",
        "common/scripted_effects/effects.txt": "set_variable = { TST_variable = 1 }\n",
        "interface/window.gui": "TST_gui = {\n}\n",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        _write(path, content)
    reference = root / "common" / "scripted_effects" / "references.txt"
    _write(reference, "pdx_tooltip = TST_live\n")
    loc = root / "localisation" / "english" / "MD_focus_TST_l_english.yml"
    loc.parent.mkdir(parents=True, exist_ok=True)
    _write(
        loc,
        """l_english:
 # user note
 # National Focus
 TST_focus_tree: "TST Tree"
 TST_focus: "Focus"
 TST_focus_desc: "Description"
 TST_idea: "Idea"
 TST_modifier: "Modifier"
 TST_opinion: "Opinion"
 TST_category: "Category"
 TST_decision: "Decision"
 tst_events.1: "Event"
 TST_character: "Character"
 TST_org: "Organization"
 TST_mio: "MIO"
 TST_trait: "Trait"
 TST_variable: "Variable"
 TST_gui: "GUI"
 unknown_tt: "Tooltip"
 TST_live: "Live"
 dead_key: "Dead"
 # trailing note
""",
    )
    return loc


def test_localisation_index_categories_references_and_idempotence(tmp_path):
    root = tmp_path / "mod"
    loc_file = _localisation_mod_fixture(root)
    index = localisation._build_index(root, verbose=True)
    references = localisation._build_reference_tokens(root, verbose=True)
    assert localisation._scan_dir(root / "missing", recursive=False) == []
    assert "TST_focus" in index["National Focus"]
    assert "TST_decision" in index["Decisions"]
    assert "tst_events" in index["Events"]
    assert "TST_gui" in references
    assert localisation._find_category("tst_events.1", index, references) == "Events"
    assert (
        localisation._find_category("TST_focus_desc", index, references)
        == "National Focus"
    )
    assert localisation._find_category("unknown_tt", index, references) == "Tooltips"
    assert localisation._find_category("TST_live", index, references) == "Other"
    assert localisation._find_category("dead_key", index, references) == "Unreferenced"
    assert localisation._referenced("dead_key_desc", references) is False

    standardizer = localisation.LocalisationStandardizer(root, verbose=True)
    assert standardizer.standardize_file(loc_file, loc_file)
    once = _read(loc_file, encoding="utf-8-sig")
    assert once.startswith("l_english:")
    assert " # user note" in once
    assert " # trailing note" in once
    assert once.index("# National Focus") < once.index("# Ideas")
    assert ' TST_focus_tree: "TST Tree"' in once
    assert standardizer.standardize_file(loc_file, loc_file)
    assert _read(loc_file, encoding="utf-8-sig") == once


def test_localisation_bad_header_and_write_errors(tmp_path, monkeypatch):
    root = tmp_path / "mod"
    root.mkdir()
    bad = root / "bad.yml"
    _write(bad, "\n")
    standardizer = localisation.LocalisationStandardizer(root)
    assert not standardizer.standardize_file(bad, bad)
    assert not standardizer.standardize_file(root / "missing.yml", bad)

    good = root / "good.yml"
    _write(good, 'l_english:\n key: "value"\n')

    def fail_write(*_args, **_kwargs):
        raise OSError("disk")

    monkeypatch.setattr(localisation, "atomic_write_text", fail_write)
    assert not standardizer.standardize_file(good, good)


def test_localisation_cli_main_explicit_root_and_backup(tmp_path, monkeypatch):
    root = tmp_path / "mod"
    loc_file = _localisation_mod_fixture(root)
    output = tmp_path / "out.yml"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "standardize_localisation.py",
            str(loc_file),
            "--mod-root",
            str(root),
            "--output",
            str(output),
            "--backup",
        ],
    )
    localisation.main()
    assert output.read_bytes().startswith(b"\xef\xbb\xbf")
    assert list(
        (root / "localisation" / "english").glob("MD_focus_TST_l_english.yml.backup.*")
    )


_MIO_FIXTURE = """TST_manufacturer = {
\tallowed = { original_tag = TST }
\tname = TST_manufacturer
\ticon = {
\t\ticon = GFX_mio
\t}
\tinclude = TST_base
\ttask_capacity = 3
\tavailable = { has_country_flag = TST_ready }
\tvisible = { has_war = no }
\ton_design_team_assigned_to_tech = { log = yes }
\tai_will_do = { base = 1 }
\tequipment_type = {
\t\tinfantry_weapons
\t\tartillery
\t}
\tresearch_categories = { armor }
\ttree_header_text = { text = TST_header }
\tinitial_trait = {
\t\ttoken = TST_initial
\t\tname = TST_initial
\t}
\ttrait = {
\t\ttoken = TST_trait
\t\tname = TST_trait
\t\ticon = GFX_trait
\t\tavailable = { has_country_flag = TST_ready }
\t\tvisible = { has_war = no }
\t\tparent = { traits = { TST_parent_one TST_parent_two } }
\t\tall_parents = { TST_parent }
\t\tposition = { x = 0 y = 0 }
\t\trelative_position_id = TST_previous
\t\tmutually_exclusive = { TST_other_one TST_other_two }
\t\tlimit_to_equipment_type = { infantry_weapons }
\t\tequipment_bonus = { reliability = 0.1 }
\t\tequipment_bonus = { reliability = 0.2 }
\t\tproduction_bonus = {
\t\t\t# preserve
\t\t\tproduction_speed = 0.1
\t\t}
\t\torganization_modifier = { organization = 0.1 }
\t\ton_complete = {
\t\t\tadd_political_power = 1
\t\t\tfree_trait_picks = 1
\t\t}
\t\tai_will_do = { base = 1 }
\t\tunknown = yes
\t}
}
"""


def test_mio_full_fixture_and_normalization_edges(tmp_path):
    source = tmp_path / "mio.txt"
    _write(source, _MIO_FIXTURE)
    standardizer = mio.MIOStandardizer()
    assert standardizer.standardize_file(str(source), str(source))
    once = _read(source)
    assert "allowed = { original_tag = TST }" in once
    assert "on_design_team_assigned_to_tech" in once
    assert "equipment_type = {" in once
    assert "TST_parent_one" in once
    assert "reliability = 0.2" in once
    assert "expenditure_for_mio_upgrade = yes" in once
    assert standardizer.standardize_file(str(source), str(source))
    assert _read(source) == once

    assert standardizer.normalize_on_complete(
        ["on_complete = { free_trait_picks = 1 }"]
    ) == ["on_complete = { expenditure_for_mio_upgrade = yes }"]
    assert standardizer._normalize_token_list(
        ["parent = {", "\t# note", "\tTST_parent", "}"], "parent", "\t\t"
    ) == ["parent = {", "\t# note", "\tTST_parent", "}"]
    assert standardizer._normalize_modifier_block(
        ["equipment_bonus = {", "\treliability = 0.1", "}"],
        "equipment_bonus",
        "\t",
    ) == ["\tequipment_bonus = { reliability = 0.1 }"]
    assert (
        standardizer._normalize_modifier_block(
            ["equipment_bonus = {", "\treliability = 0.1", "\tarmor = 0.2", "}"],
            "equipment_bonus",
            "\t",
        )[1]
        == "\t\treliability = 0.1"
    )
    assert standardizer._merge_and_normalize_modifier_blocks(
        [
            ["equipment_bonus = {", "\treliability = 0.1", "}"],
            ["equipment_bonus = {", "\tarmor = 0.2", "}"],
        ],
        "equipment_bonus",
        "\t",
    )[1:3] == ["\t\treliability = 0.1", "\t\tarmor = 0.2"]
    assert (
        standardizer._merge_and_normalize_modifier_blocks([], "equipment_bonus", "\t")
        == []
    )


def test_mio_fallbacks_and_strip_gate_cli(tmp_path, monkeypatch):
    standardizer = mio.MIOStandardizer()
    malformed = ["equipment_bonus = {", "\treliability =", "}"]
    assert (
        standardizer._normalize_modifier_block(malformed, "equipment_bonus", "\t")
        == malformed
    )
    assert standardizer.format_nested_block([], "\t") == []

    root = tmp_path / "mod"
    tags = root / "common" / "idea_tags"
    tags.mkdir(parents=True)
    _write(
        tags / "tags.txt",
        "idea_categories = {\n\tcountry = { }\n\thidden_ideas = { hidden = yes }\n}\n",
    )
    idea = root / "common" / "ideas" / "ideas.txt"
    idea.parent.mkdir(parents=True)
    _write(
        idea,
        "ideas = {\n\tcountry = {\n\t\tTST_idea = {\n\t\t\tallowed = { original_tag = TST }\n\t\t}\n\t}\n}\n",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["strip_idea_allowed_gates.py", "--root", str(root), "--dry-run", str(idea)],
    )
    assert idea_gates.main() == 0
    assert "allowed" in _read(idea)
    removed, skipped, failed = idea_gates.process_file(
        str(idea), frozenset({"country"}), dry_run=False, backup=True
    )
    assert (removed, skipped, failed) == (1, 0, False)
    assert "allowed" not in _read(idea)
    assert list(idea.parent.glob("ideas.txt.backup.*"))


def test_standardize_staged_in_process_routes_and_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    focus_file = tmp_path / "common" / "national_focus" / "TST.txt"
    focus_file.parent.mkdir(parents=True)
    _write(focus_file, "focus_tree = {\n\tfocus = {\n\t\tid = TST_focus\n\t}\n}\n")
    other = tmp_path / "README.txt"
    _write(other, "plain\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "standardize_staged.py",
            "common/national_focus/TST.txt",
            "README.txt",
            "missing.txt",
        ],
    )
    assert standardize_staged.main() == 1
    assert "focus = {" in _read(focus_file)


def test_standardize_staged_error_is_nonzero(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["standardize_staged.py", "events/TST.txt"])

    def fail_standardize(*_args):
        raise RuntimeError("boom")

    monkeypatch.setattr(standardize_staged, "standardize_file", fail_standardize)
    monkeypatch.setattr(standardize_staged.os.path, "exists", lambda _path: True)
    assert standardize_staged.main() == 1
