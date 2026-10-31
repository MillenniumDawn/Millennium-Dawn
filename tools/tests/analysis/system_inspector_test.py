"""Behavioral tests for tools/analysis/system_inspector.py on a synthetic mod tree."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from shared.suite import write_under_str

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.analysis import system_inspector  # noqa: E402

FILES = {
    "common/scripted_effects/ZZZ_effects.txt": """ZZZ_start = {
\tZZZ_missing_effect = yes
\tset_country_flag = ZZZ_started
\tset_variable = { global.ZZZ_counter = 1 }
\tif = { limit = { check_variable = { global.ZZZ_never_written > 0 } } country_event = zzz.1 }
\tcountry_event = zzz.9
\tshared_helper = yes
}

ZZZ_orphan = {
\tlog = "nobody calls this"
}
""",
    "common/scripted_triggers/ZZZ_triggers.txt": """ZZZ_ready = {
\thas_country_flag = ZZZ_started
\thas_country_flag = ZZZ_never_set
}
""",
    "events/ZZZ.txt": """add_namespace = zzz

country_event = {
\tid = zzz.1
\ttitle = zzz.1.t
\tdesc = zzz.1.d
\tis_triggered_only = yes

\toption = {
\t\tname = zzz.1.a
\t\tZZZ_start = yes
\t}
}

country_event = {
\tid = zzz.2
\ttitle = zzz.2.t
\tdesc = zzz.2.d
\tis_triggered_only = yes
}
""",
    "localisation/english/ZZZ_l_english.yml": """﻿l_english:
 zzz.1.t: "Title"
 zzz.1.a: "Option"
 zzz.2.t: "Title"
 zzz.2.d: "Desc"
""",
    "common/scripted_effects/shared_effects.txt": """shared_helper = {
\tlog = "shared"
}

uses_the_system = {
\tif = { limit = { ZZZ_ready = yes } }
}
""",
    "common/on_actions/00_on_actions.txt": """on_actions = {
\ton_startup = { effect = { ZZZ_start = yes } }
}
""",
}


@pytest.fixture
def mod_root(tmp_path: Path) -> Path:
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    return tmp_path


def inspect_mod(root: Path) -> dict:
    return system_inspector.inspect(system_inspector.read_tree(root), r"ZZZ", ("ZZZ_",))


@pytest.fixture
def report(mod_root: Path) -> dict:
    return inspect_mod(mod_root)


def test_files_and_definitions_belong_to_the_system(report):
    paths = {e["path"] for entries in report["files"].values() for e in entries}
    assert paths == {
        "common/scripted_effects/ZZZ_effects.txt",
        "common/scripted_triggers/ZZZ_triggers.txt",
        "events/ZZZ.txt",
        "localisation/english/ZZZ_l_english.yml",
    }
    assert report["definitions"]["scripted_effect"] == ["ZZZ_orphan", "ZZZ_start"]
    assert report["definitions"]["scripted_trigger"] == ["ZZZ_ready"]
    assert report["definitions"]["event"] == ["zzz.1", "zzz.2"]


def test_hooks_list_outside_files_that_reach_in(report):
    assert report["hooks"] == {
        "common/on_actions/00_on_actions.txt": ["ZZZ_start"],
        "common/scripted_effects/shared_effects.txt": ["ZZZ_ready"],
    }


def test_dependencies_name_the_outside_definition_and_its_file(report):
    assert report["dependencies"]["scripted_effect"] == [
        {
            "name": "shared_helper",
            "defined_in": "common/scripted_effects/shared_effects.txt",
        }
    ]


def test_unresolved_references_point_at_nothing(report):
    unresolved = report["unresolved"]
    assert unresolved["calls"] == ["ZZZ_missing_effect"]
    assert unresolved["events"] == ["zzz.9"]
    assert unresolved["localisation"] == ["zzz.1.d"]
    assert unresolved["flags_never_set"] == ["country:ZZZ_never_set"]
    assert unresolved["globals_never_written"] == ["ZZZ_never_written"]


def test_unused_definitions_are_never_referenced(report):
    assert report["unused"] == {
        "scripted_effects_and_triggers": ["ZZZ_orphan"],
        "triggered_only_events": ["zzz.2"],
    }


def test_script_language_words_are_not_hooks_or_dependencies(tmp_path):
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    write_under_str(
        tmp_path,
        "common/scripted_effects/00_scriptlanguage.txt",
        "yes = { custom_effect_tooltip = script.0.yes }\n",
    )
    report = system_inspector.inspect(
        system_inspector.read_tree(tmp_path), r"ZZZ", ("ZZZ_",)
    )
    names = [e["name"] for e in report["dependencies"]["scripted_effect"]]
    assert "yes" not in names


def test_cli_prints_json_and_rejects_a_pattern_with_no_files(tmp_path, capsys):
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    code = system_inspector.main(
        ["--path-pattern", "ZZZ", "--prefix", "ZZZ_", "--root", str(tmp_path), "--json"]
    )
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["unresolved"]["calls"] == ["ZZZ_missing_effect"]

    assert (
        system_inspector.main(["--path-pattern", "NOPE", "--root", str(tmp_path)]) == 1
    )
    assert "No files" in capsys.readouterr().err


def test_cli_rejects_an_invalid_pattern_before_reading_the_tree(capsys, monkeypatch):
    def unexpected_scan(_root):
        pytest.fail("read_tree must not run for an invalid path pattern")

    monkeypatch.setattr(system_inspector, "read_tree", unexpected_scan)
    assert system_inspector.main(["--path-pattern", "["]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Invalid --path-pattern '[':")


def test_text_report_honours_sections(tmp_path, capsys):
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    system_inspector.main(
        [
            "--path-pattern",
            "ZZZ",
            "--prefix",
            "ZZZ_",
            "--root",
            str(tmp_path),
            "--section",
            "unused",
        ]
    )
    out = capsys.readouterr().out
    assert "== unused" in out
    assert "ZZZ_orphan" in out
    assert "== hooks" not in out


def test_top_preset_keeps_semantic_links_when_effect_files_are_folded(tmp_path):
    reports = []
    for layout in ("split", "folded"):
        root = tmp_path / layout
        for relative, text in FILES.items():
            relative = relative.replace("ZZZ", "targeted_operations")
            text = text.replace("ZZZ", "TOP").replace("zzz", "top")
            if (
                layout == "split"
                and relative
                == "common/scripted_effects/targeted_operations_effects.txt"
            ):
                start, orphan = text.split("\n\nTOP_orphan", 1)
                write_under_str(root, relative, start + "\n")
                write_under_str(
                    root,
                    "common/scripted_effects/targeted_operations_other.txt",
                    "TOP_orphan" + orphan,
                )
            else:
                write_under_str(root, relative, text)
        preset = system_inspector.PRESETS["top"]
        report = system_inspector.inspect(
            system_inspector.read_tree(root), preset.path_pattern, preset.prefixes
        )
        assert report["definitions"]["scripted_effect"] == ["TOP_orphan", "TOP_start"]
        assert report["definitions"]["scripted_trigger"] == ["TOP_ready"]
        assert report["definitions"]["event"] == ["top.1", "top.2"]
        assert report["unresolved"]["calls"] == ["TOP_missing_effect"]
        assert {item["name"] for item in report["dependencies"]["scripted_effect"]} == {
            "shared_helper"
        }
        assert report["hooks"]
        reports.append(report)
    for section in ("definitions", "hooks", "dependencies", "unresolved", "unused"):
        assert reports[0][section] == reports[1][section], section


@pytest.mark.parametrize("id_first", [True, False])
def test_nested_dispatch_is_not_an_event_definition(mod_root, id_first):
    ident = "id = zzz.1"
    nested = "immediate = { country_event = { id = zzz.9 days = 1 } }"
    fields = [ident, nested] if id_first else [nested, ident]
    write_under_str(
        mod_root,
        "events/ZZZ.txt",
        "country_event = {\n"
        + "\n".join(fields)
        + '\nis_triggered_only = yes\nlog = "escaped \\"quote\\" and { braces }"\n}\n',
    )
    report = inspect_mod(mod_root)
    assert report["definitions"]["event"] == ["zzz.1"]
    assert report["unresolved"]["events"] == ["zzz.9"]
    assert system_inspector.event_blocks(
        system_inspector.read_tree(mod_root).code["events/ZZZ.txt"]
    ) == [("zzz.1", True)]


def test_missing_option_label_is_reported_without_treating_other_names_as_loc(mod_root):
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_l_english.yml",
        FILES["localisation/english/ZZZ_l_english.yml"].replace(
            ' zzz.1.a: "Option"\n', ""
        ),
    )
    write_under_str(
        mod_root,
        "common/characters/ZZZ_characters.txt",
        'characters = { ZZZ_character = { name = "ZZZ_person_name" } }\n',
    )
    assert inspect_mod(mod_root)["unresolved"]["localisation"] == ["zzz.1.a", "zzz.1.d"]


@pytest.mark.parametrize("message", ["ZZZ_orphan", "A report mentions ZZZ_orphan"])
def test_prose_cannot_create_hooks_dependencies_or_hide_unused_symbols(
    mod_root, message
):
    write_under_str(
        mod_root,
        "common/on_actions/00_on_actions.txt",
        f'on_actions = {{ on_startup = {{ effect = {{ log = "{message}" }} }} }}\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/outside.txt",
        'outside_helper = { log = "unused" }\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_prose.txt",
        'ZZZ_prose = { log = "outside_helper" }\n',
    )
    report = inspect_mod(mod_root)
    assert "common/on_actions/00_on_actions.txt" not in report["hooks"]
    assert "ZZZ_orphan" in report["unused"]["scripted_effects_and_triggers"]
    assert "outside_helper" not in [
        entry["name"] for entry in report["dependencies"]["scripted_effect"]
    ]


def test_quoted_display_name_cannot_hide_an_unused_effect(mod_root):
    write_under_str(
        mod_root,
        "common/characters/outside.txt",
        'characters = { outside_character = { name = "ZZZ_orphan" } }\n',
    )
    report = inspect_mod(mod_root)
    assert "common/characters/outside.txt" not in report["hooks"]
    assert "ZZZ_orphan" in report["unused"]["scripted_effects_and_triggers"]


def test_quoted_identifiers_and_scripted_loc_remain_references(mod_root):
    write_under_str(
        mod_root,
        "common/ideas/outside.txt",
        "ideas = { country = { outside_idea = { } } }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_quoted.txt",
        'ZZZ_quoted = { add_ideas = "outside_idea" }\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_localisation/ZZZ_text.txt",
        "defined_text = {\n name = ZZZ_display\n}\n",
    )
    write_under_str(
        mod_root,
        "interface/outside.gui",
        'instantTextBoxType = { text = "Report: [ZZZ_display]" }\n',
    )
    report = inspect_mod(mod_root)
    assert report["dependencies"]["idea"] == [
        {"name": "outside_idea", "defined_in": "common/ideas/outside.txt"}
    ]
    assert report["hooks"]["interface/outside.gui"] == ["ZZZ_display"]


@pytest.mark.parametrize(
    "read_kind,write_kind",
    [
        ("country", "global"),
        ("global", "country"),
        ("state", "character"),
        ("character", "state"),
        ("project", "country"),
        ("unit_leader", "country"),
        ("mio", "country"),
    ],
)
@pytest.mark.parametrize("block_value", [False, True])
def test_flag_resolution_requires_matching_scope(
    mod_root, read_kind, write_kind, block_value
):
    value = "{ flag = ZZZ_same_name }" if block_value else "ZZZ_same_name"
    write_under_str(
        mod_root,
        "common/scripted_effects/outside_flags.txt",
        f"outside_flags = {{ set_{write_kind}_flag = {value} }}\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_triggers/ZZZ_flags.txt",
        f"ZZZ_flags = {{ has_{read_kind}_flag = {value} }}\n",
    )
    assert (
        f"{read_kind}:ZZZ_same_name"
        in inspect_mod(mod_root)["unresolved"]["flags_never_set"]
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/outside_flags.txt",
        f"outside_flags = {{ set_{read_kind}_flag = {value} }}\n",
    )
    assert (
        f"{read_kind}:ZZZ_same_name"
        not in inspect_mod(mod_root)["unresolved"]["flags_never_set"]
    )


def test_modifier_definitions_have_hooks_and_dependencies(mod_root):
    write_under_str(
        mod_root,
        "common/modifier_definitions/ZZZ_modifiers.txt",
        "ZZZ_applied_power = { color_type = bad }\n",
    )
    write_under_str(
        mod_root,
        "common/modifier_definitions/outside.txt",
        "outside_power = { color_type = bad }\n",
    )
    write_under_str(
        mod_root,
        "common/synchronized_dynamic_tokens/MD_tokens.txt",
        "ZZZ_applied_power\n",
    )
    write_under_str(
        mod_root,
        "common/dynamic_modifiers/ZZZ_dynamic.txt",
        "ZZZ_dynamic = { enable = { always = yes } outside_power = ZZZ_power }\n",
    )
    report = inspect_mod(mod_root)
    assert report["hooks"]["common/synchronized_dynamic_tokens/MD_tokens.txt"] == [
        "ZZZ_applied_power"
    ]
    assert report["dependencies"]["modifier_definition"] == [
        {
            "name": "outside_power",
            "defined_in": "common/modifier_definitions/outside.txt",
        }
    ]


@pytest.mark.parametrize("indent", ["", " "])
@pytest.mark.parametrize("version", ["", "0"])
def test_english_keys_resolve_with_zero_or_one_space_indent(mod_root, indent, version):
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_label_l_english.yml",
        f'l_english:\n{indent}ZZZ_label:{version} "Known label"\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_label.txt",
        "ZZZ_show_label = { custom_effect_tooltip = ZZZ_label }\n",
    )
    assert inspect_mod(mod_root)["unresolved"]["localisation"] == ["zzz.1.d"]


def test_gui_only_localisation_is_checked(mod_root):
    write_under_str(
        mod_root,
        "interface/ZZZ_dashboard.gui",
        'guiTypes = { instantTextBoxType = { text = "ZZZ_dashboard_title" } }\n',
    )
    assert "ZZZ_dashboard_title" in inspect_mod(mod_root)["unresolved"]["localisation"]
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_dashboard_l_english.yml",
        'l_english:\n ZZZ_dashboard_title: "Dashboard"\n',
    )
    assert (
        "ZZZ_dashboard_title" not in inspect_mod(mod_root)["unresolved"]["localisation"]
    )


def test_bare_definitions_remain_linkable_without_linking_language_helpers(mod_root):
    write_under_str(
        mod_root,
        "common/ideas/ZZZ_ideas.txt",
        "ideas = { country = { asio = { } ausfta = { } } }\n",
    )
    write_under_str(
        mod_root,
        "common/ideas/outside.txt",
        "ideas = { country = { thirdparty = { } } }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_bare.txt",
        "ZZZ_use_bare = { add_ideas = thirdparty }\n"
        + "\n".join(f"{name} = {{ }}" for name in ("yes", "no", "from", "for")),
    )
    write_under_str(
        mod_root,
        "common/national_focus/outside.txt",
        "focus = { available = { always = yes } completion_reward = { "
        "add_ideas = asio remove_ideas = ausfta } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["hooks"]["common/national_focus/outside.txt"] == ["asio", "ausfta"]
    assert report["dependencies"]["idea"] == [
        {"name": "thirdparty", "defined_in": "common/ideas/outside.txt"}
    ]


@pytest.mark.parametrize("loc_file", ["ZZZ_labels", "outside_labels"])
def test_localisation_cannot_hide_unused_code(mod_root, loc_file):
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_bare_orphan.txt",
        "bare_orphan = { }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_triggers/ZZZ_lonely_trigger.txt",
        "ZZZ_lonely_trigger = { always = yes }\n",
    )
    write_under_str(
        mod_root,
        f"localisation/english/{loc_file}_l_english.yml",
        'l_english:\n ZZZ_orphan: "Label"\n bare_orphan: "Label"\n'
        ' ZZZ_lonely_trigger: "Label"\n zzz.2: "Label"\n',
    )
    assert inspect_mod(mod_root)["unused"] == {
        "scripted_effects_and_triggers": [
            "ZZZ_lonely_trigger",
            "ZZZ_orphan",
            "bare_orphan",
        ],
        "triggered_only_events": ["zzz.2"],
    }


@pytest.mark.parametrize(
    "text,line_count",
    [
        ("", 0),
        ("foo", 1),
        ("foo\n", 1),
        ("\n", 1),
        ("foo\nbar", 2),
        ("foo\nbar\n", 2),
        ("foo\r\n", 1),
    ],
)
def test_line_counts_do_not_include_an_empty_eof_line(tmp_path, text, line_count):
    write_under_str(tmp_path, "common/scripted_effects/ZZZ_lines.txt", text)
    report = inspect_mod(tmp_path)
    assert report["files"]["scripted_effect"] == [
        {"path": "common/scripted_effects/ZZZ_lines.txt", "lines": line_count}
    ]
    assert f"{line_count} lines" in system_inspector.render(report, ("files",), 10)


def test_weighted_event_pools_report_missing_dispatches(mod_root):
    write_under_str(
        mod_root,
        "common/on_actions/ZZZ_on_actions.txt",
        "on_actions = { on_weekly = { random_events = { "
        '100 = 0 100 = zzz.1 200 = "zzz.99" } '
        "other_block = { 100 = zzz.98 } } }\n",
    )
    assert inspect_mod(mod_root)["unresolved"]["events"] == ["zzz.9", "zzz.99"]


def test_localisation_global_substitutions_are_reads_but_prose_is_not_code(mod_root):
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_status_l_english.yml",
        'l_english:\n ZZZ_status: "[?global.ZZZ_loc_only|0] [?global.ZZZ_counter|0]"\n'
        ' ZZZ_prose: "global.ZZZ_plaintext set_variable = { global.ZZZ_loc_only = 1 }"\n'
        ' # ZZZ_comment: "[?global.ZZZ_comment|0]"\n',
    )
    assert inspect_mod(mod_root)["unresolved"]["globals_never_written"] == [
        "ZZZ_loc_only",
        "ZZZ_never_written",
    ]
    write_under_str(
        mod_root,
        "common/scripted_effects/outside_global.txt",
        "outside_global = { set_variable = { global.ZZZ_loc_only = 1 } }\n",
    )
    assert inspect_mod(mod_root)["unresolved"]["globals_never_written"] == [
        "ZZZ_never_written"
    ]


def test_focus_ids_are_direct_definitions_with_external_hooks(mod_root):
    write_under_str(
        mod_root,
        "common/national_focus/ZZZ_focus.txt",
        "focus_tree = { id = ZZZ_tree focus = { id = ZZZ_root } }\n"
        "shared_focus = { completion_reward = { country_event = { id = zzz.9 } } "
        'id = "ZZZ_shared" }\n'
        "joint_focus = { id = ZZZ_joint }\n",
    )
    write_under_str(
        mod_root,
        "events/outside_focus.txt",
        "country_event = { id = outside.1 trigger = { has_completed_focus = ZZZ_root } "
        "immediate = { complete_national_focus = ZZZ_shared } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["definitions"]["focus"] == ["ZZZ_joint", "ZZZ_root", "ZZZ_shared"]
    assert report["hooks"]["events/outside_focus.txt"] == ["ZZZ_root", "ZZZ_shared"]
    assert "ZZZ_tree" not in report["definitions"]["focus"]


def test_parameterized_calls_are_checked_without_counting_definitions(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_parameterized.txt",
        "ZZZ_parameterized = { ZZZ_missing_block = { TARGET = USA } "
        "shared_helper = { AMOUNT = 2 } ZZZ_start = { TARGET = USA } }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_guis/ZZZ_windows.txt",
        "scripted_gui = { ZZZ_window = { window_name = ZZZ_window } }\n",
    )
    write_under_str(
        mod_root,
        "common/ideas/ZZZ_ideas.txt",
        "ideas = { country = { ZZZ_idea = { } } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["unresolved"]["calls"] == ["ZZZ_missing_block", "ZZZ_missing_effect"]
    assert report["dependencies"]["scripted_effect"] == [
        {
            "name": "shared_helper",
            "defined_in": "common/scripted_effects/shared_effects.txt",
        }
    ]


@pytest.mark.parametrize("field", ["pdx_tooltip", "pdx_tooltip_delayed", "buttonText"])
@pytest.mark.parametrize("quoted", [False, True])
def test_gui_tooltips_and_button_labels_resolve_localisation(mod_root, field, quoted):
    value = '"ZZZ_gui_label"' if quoted else "ZZZ_gui_label"
    write_under_str(
        mod_root,
        "interface/ZZZ_dashboard.gui",
        f"guiTypes = {{ buttonType = {{ {field} = {value} }} }}\n",
    )
    assert "ZZZ_gui_label" in inspect_mod(mod_root)["unresolved"]["localisation"]
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_gui_l_english.yml",
        'l_english:\n ZZZ_gui_label:0 "Label"\n',
    )
    assert "ZZZ_gui_label" not in inspect_mod(mod_root)["unresolved"]["localisation"]


@pytest.mark.parametrize("scripted_kind", ["scripted_effects", "scripted_triggers"])
@pytest.mark.parametrize("call_value", ["yes", "no", "{ AMOUNT = 1 }"])
def test_shared_idea_name_is_not_a_scripted_dependency_until_called(
    mod_root, scripted_kind, call_value
):
    write_under_str(
        mod_root,
        f"common/{scripted_kind}/outside_economy.txt",
        "recession = { }\n",
    )
    idea_file = "common/ideas/ZZZ_economy.txt"
    idea = "ideas = { country = { recession = { available = { has_idea = recession }"
    write_under_str(mod_root, idea_file, idea + " } } }\n")
    kind = scripted_kind.removesuffix("s")
    assert not any(
        entry["name"] == "recession"
        for entry in inspect_mod(mod_root)["dependencies"].get(kind, ())
    )
    write_under_str(
        mod_root,
        idea_file,
        idea
        + f" {'on_remove' if scripted_kind == 'scripted_effects' else 'allowed'}"
        + f" = {{ recession = {call_value} }} }} }} }}\n",
    )
    assert {
        "name": "recession",
        "defined_in": f"common/{scripted_kind}/outside_economy.txt",
    } in inspect_mod(mod_root)["dependencies"][kind]


def test_variable_keys_gui_handlers_and_categories_are_not_calls(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_math.txt",
        "ZZZ_math = { set_variable = { ZZZ_rate = { value = 2 multiply = 3 } } "
        "add_to_temp_variable = { ZZZ_total = { value = 1 } } }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_guis/ZZZ_windows.txt",
        "scripted_gui = { ZZZ_window = { "
        "triggers = { ZZZ_button_click_enabled = { always = yes } } "
        "effects = { ZZZ_button_click = { ZZZ_start = yes ZZZ_gui_missing = yes } } "
        "dynamic_lists = { ZZZ_grid = { array = ZZZ_rows } } } }\n",
    )
    write_under_str(
        mod_root,
        "common/raids/ZZZ_raids.txt",
        "types = { ZZZ_raid = { visible = { ZZZ_ready = yes } success_factors = { "
        "success = { ZZZ_factor = { scope = country weight = 1 } } } } }\n",
    )
    write_under_str(
        mod_root,
        "common/ai_strategy/ZZZ_ai.txt",
        "ZZZ_ai_plan = { enable = { ZZZ_ready = yes } }\n",
    )
    write_under_str(
        mod_root,
        "common/decisions/ZZZ_decisions.txt",
        "ZZZ_category = { ZZZ_decision = { complete_effect = { ZZZ_start = yes } } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["unresolved"]["calls"] == ["ZZZ_gui_missing", "ZZZ_missing_effect"]


def test_digit_leading_names_are_tokens(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_triggers/ZZZ_popularity.txt",
        "10_percent_ZZZ_popularity = { always = yes }\n",
    )
    write_under_str(
        mod_root,
        "events/caller.txt",
        "country_event = { id = caller.1 trigger = { 10_percent_ZZZ_popularity = yes } }\n",
    )
    report = inspect_mod(mod_root)
    assert "10_percent_ZZZ_popularity" in report["hooks"]["events/caller.txt"]
    assert (
        "10_percent_ZZZ_popularity"
        not in report["unused"]["scripted_effects_and_triggers"]
    )


def test_a_system_definition_is_not_a_dependency_of_another_kind(mod_root):
    write_under_str(
        mod_root,
        "common/decisions/ZZZ_decisions.txt",
        "ZZZ_category = { shared_name = { complete_effect = { ZZZ_start = yes } } }\n",
    )
    write_under_str(
        mod_root,
        "common/ideas/outside_ideas.txt",
        "ideas = { country = { shared_name = { } used_idea = { } } }\n",
    )
    assert "idea" not in inspect_mod(mod_root)["dependencies"]
    write_under_str(
        mod_root,
        "common/decisions/ZZZ_decisions.txt",
        "ZZZ_category = { shared_name = { visible = { has_idea = shared_name } } }\n",
    )
    assert inspect_mod(mod_root)["dependencies"]["idea"] == [
        {"name": "shared_name", "defined_in": "common/ideas/outside_ideas.txt"}
    ]


def test_raid_categories_and_technologies_are_dependencies(mod_root):
    write_under_str(
        mod_root,
        "common/raids/categories/raid_categories.txt",
        "categories = { strike_raids = { intel_source = civilian } }\n",
    )
    write_under_str(
        mod_root,
        "common/technologies/outside.txt",
        "technologies = { robotics_1 = { research_cost = 1 } }\n",
    )
    write_under_str(
        mod_root,
        "common/raids/ZZZ_raids.txt",
        "types = { ZZZ_raid = { category = strike_raids "
        "allowed = { has_tech = robotics_1 } } }\n",
    )
    dependencies = inspect_mod(mod_root)["dependencies"]
    assert dependencies["raid_category"][0]["name"] == "strike_raids"
    assert dependencies["technology"][0]["name"] == "robotics_1"


def test_inline_scripted_loc_and_loc_calls_are_linked(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_localisation/ZZZ_loc.txt",
        "defined_text = { name = ZZZ_inline text = { localization_key = zzz.2.t } }\n"
        "defined_text = {\n\tname = ZZZ_block\n\ttext = { localization_key = zzz.2.t }\n}\n",
    )
    write_under_str(
        mod_root,
        "localisation/english/outside_l_english.yml",
        '﻿l_english:\n outside_key: "Shows [ZZZ_inline] and [Root.GetName]"\n',
    )
    report = inspect_mod(mod_root)
    assert report["definitions"]["scripted_loc"] == ["ZZZ_block", "ZZZ_inline"]
    assert report["hooks"]["localisation/english/outside_l_english.yml"] == [
        "ZZZ_inline"
    ]


def test_non_script_common_files_have_no_calls(mod_root):
    write_under_str(
        mod_root,
        "common/units/names_divisions/ZZZ_names.txt",
        "ZZZ_INF_01 = { name = Infantry for_countries = { ZZZ } }\n",
    )
    write_under_str(
        mod_root,
        "common/ai_equipment/ZZZ_naval.txt",
        "ZZZ_roles = { category = naval ZZZ_Escort = { priority = { base = 1 } } }\n",
    )
    write_under_str(
        mod_root,
        "common/bop/ZZZ.txt",
        "ZZZ_bop_category = { range = { id = ZZZ_centre on_activate = { ZZZ_start = yes } } }\n",
    )
    assert inspect_mod(mod_root)["unresolved"]["calls"] == ["ZZZ_missing_effect"]


def test_game_rule_names_and_groups_are_localisation(mod_root):
    write_under_str(
        mod_root,
        "common/game_rules/ZZZ_rules.txt",
        "ZZZ_rule = { name = ZZZ_rule_name group = ZZZ_rules_group "
        "default = { name = ZZZ_on text = ZZZ_on_text } }\n",
    )
    assert {"ZZZ_rule_name", "ZZZ_rules_group", "ZZZ_on_text"} <= set(
        inspect_mod(mod_root)["unresolved"]["localisation"]
    )
    assert "ZZZ_on" not in inspect_mod(mod_root)["unresolved"]["localisation"]


def test_balance_of_power_ai_equipment_and_modifier_tooltips(mod_root):
    write_under_str(
        mod_root,
        "common/bop/ZZZ.txt",
        "ZZZ_bop_category = { initial_value = 0 }\n",
    )
    write_under_str(
        mod_root,
        "events/bop_reader.txt",
        "country_event = { id = bop_reader.1 "
        "trigger = { has_power_balance = { id = ZZZ_bop_category } } }\n",
    )
    write_under_str(
        mod_root,
        "common/ai_equipment/ZZZ_ships.txt",
        "ZZZ_battleships = { category = naval available_for = { ZZZ } roles = { naval } "
        "priority = { base = 1 } blocked_for = { YYY } ZZZ_battleship = { } }\n",
    )
    write_under_str(
        mod_root,
        "common/dynamic_modifiers/ZZZ_modifiers.txt",
        "ZZZ_modifier = { custom_modifier_tooltip = ZZZ_modifier_tt }\n",
    )
    report = inspect_mod(mod_root)
    assert "ZZZ_bop_category" in report["hooks"]["events/bop_reader.txt"]
    assert report["definitions"]["ai_equipment"] == ["ZZZ_battleship"]
    assert "ZZZ_modifier_tt" in report["unresolved"]["localisation"]


def test_leader_traits_are_definitions_not_calls(mod_root):
    write_under_str(
        mod_root,
        "common/country_leader/ZZZ_traits.txt",
        "leader_traits = { ZZZ_trait = { random = no } }\n",
    )
    write_under_str(
        mod_root,
        "common/unit_leader/ZZZ_traits.txt",
        "leader_traits = { ZZZ_general = { type = land } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["unresolved"]["calls"] == ["ZZZ_missing_effect"]
    assert report["definitions"]["country_leader_trait"] == ["ZZZ_trait"]
    assert report["definitions"]["unit_leader_trait"] == ["ZZZ_general"]


def test_hyphenated_loc_keys_and_tokens_are_whole(mod_root):
    write_under_str(
        mod_root,
        "common/characters/ZZZ.txt",
        "characters = { ZZZ_hans-peter = { name = ZZZ_hans-peter } }\n",
    )
    write_under_str(
        mod_root,
        "history/countries/YYY - Why.txt",
        "recruit_character = ZZZ_hans-peter\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_tooltips.txt",
        "ZZZ_tooltips = { custom_effect_tooltip = ZZZ_less_-10_tt }\n",
    )
    report = inspect_mod(mod_root)
    assert "ZZZ_hans-peter" in report["hooks"]["history/countries/YYY - Why.txt"]
    assert "ZZZ_less_-10_tt" in report["unresolved"]["localisation"]
    assert "ZZZ_less_" not in report["unresolved"]["localisation"]


def test_a_same_named_outside_definition_is_not_a_hook(mod_root):
    write_under_str(
        mod_root,
        "common/national_focus/ZZZ_focus.txt",
        "focus_tree = { focus = { id = shared_focus_name } }\n",
    )
    write_under_str(
        mod_root,
        "common/ideas/outside_ideas.txt",
        "ideas = { country = { shared_focus_name = { } } }\n",
    )
    assert "common/ideas/outside_ideas.txt" not in inspect_mod(mod_root)["hooks"]
    write_under_str(
        mod_root,
        "common/ideas/outside_ideas.txt",
        "ideas = { country = { shared_focus_name = { "
        "allowed = { has_completed_focus = shared_focus_name } } } }\n",
    )
    assert inspect_mod(mod_root)["hooks"]["common/ideas/outside_ideas.txt"] == [
        "shared_focus_name"
    ]


def test_scoped_loc_calls_count_and_commented_ones_do_not(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_localisation/ZZZ_loc.txt",
        "defined_text = { name = ZZZ_flavor text = { localization_key = zzz.2.t } }\n"
        "defined_text = { name = ZZZ_display text = { localization_key = zzz.2.t } }\n",
    )
    write_under_str(
        mod_root,
        "localisation/english/outside_l_english.yml",
        '﻿l_english:\n live: "Shows [ROOT.ZZZ_flavor]"\n' ' # old: "[ZZZ_display]"\n',
    )
    hooks = inspect_mod(mod_root)["hooks"]
    assert hooks["localisation/english/outside_l_english.yml"] == ["ZZZ_flavor"]


def test_randomize_variable_writes_a_global(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_roll.txt",
        "ZZZ_roll = { randomize_variable = { var = global.ZZZ_roll min = 0 max = 10 } "
        "if = { limit = { check_variable = { global.ZZZ_roll > 5 } } } }\n",
    )
    assert (
        "ZZZ_roll" not in inspect_mod(mod_root)["unresolved"]["globals_never_written"]
    )


def test_quoted_gui_sprites_link_in_both_directions(mod_root):
    write_under_str(
        mod_root,
        "interface/outside.gfx",
        'spriteTypes = { spriteType = { name = "GFX_external_icon" } }\n',
    )
    write_under_str(
        mod_root,
        "interface/ZZZ.gfx",
        'spriteTypes = { spriteType = { name = "GFX_ZZZ_icon" } }\n',
    )
    write_under_str(
        mod_root,
        "interface/ZZZ.gui",
        'guiTypes = { iconType = { name = "a" SpriteType = "GFX_external_icon" } }\n',
    )
    write_under_str(
        mod_root,
        "interface/outside.gui",
        'guiTypes = { buttonType = { name = "b" quadTextureSprite = "GFX_ZZZ_icon" } }\n',
    )
    report = inspect_mod(mod_root)
    assert report["dependencies"]["sprite"] == [
        {"name": "GFX_external_icon", "defined_in": "interface/outside.gfx"}
    ]
    assert report["hooks"]["interface/outside.gui"] == ["GFX_ZZZ_icon"]


def test_missing_scripted_loc_substitution_in_system_yml_is_unresolved(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_localisation/ZZZ_text.txt",
        "defined_text = {\n name = ZZZ_display\n}\n",
    )
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_extra_l_english.yml",
        '﻿l_english:\n ZZZ_label: "Status: [ZZZ_missing] [ZZZ_display] [Root.GetName]"\n',
    )
    unresolved = inspect_mod(mod_root)["unresolved"]["localisation"]
    assert "ZZZ_missing" in unresolved
    assert "ZZZ_display" not in unresolved
    assert "GetName" not in unresolved
