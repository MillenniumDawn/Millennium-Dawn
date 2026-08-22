"""Shared fixtures for Corporate History contract regression tests."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from validate_corporate_history_contract import (
    _NATIVE_ARRAY_BLOCK_EFFECTS,
    _NATIVE_CONTRACT_ROLES,
    _NATIVE_VARIABLE_BLOCK_EFFECTS,
    _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS,
    Validator,
    _collect_native_write_tokens,
    _is_repeatable_decision,
    _removes_active_decision,
)


def _write(root: Path, relative: str, text: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_loc(root: Path, relative: str, text: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))


def _manifest(
    callerless=None,
    other_callerless=None,
    allowed_reads=None,
    with_other_chain=False,
    variables=None,
    allow_multiple_completion_producers=False,
):
    chains = [
        {
            "name": "TestCo",
            "tag": "USA",
            "namespace": "USA_test_events",
            "root": "USA_test",
            "tier": 1,
            "full_start_strategies": [
                "yearly_dispatcher",
                "current_year_scheduler",
                "reconstruction",
            ],
            "outcomes_only_strategy": "reconstruction",
            "monthly_driver": "USA_corporate_history_monthly_outcomes",
            "terminal_marker": "USA_test_reconstruct_complete",
            "terminal_date": "2001-03-01",
            "outcome_ideas": ["USA_test_outcome_a", "USA_test_outcome_b"],
            "expected_callers": {},
            "dependency_order": [],
            "localisation_prefixes": ["USA_test"],
            "effect_preview_policy": "engine_or_explicit",
            "bridge_refresh_policy": "none",
            "owned_prefixes": ["USA_test"],
            "variables": (
                {"USA_test_state": {"min": 0, "max": 10}}
                if variables is None
                else variables
            ),
            "outcome_idea_prefixes": ["USA_test_outcome_"],
            "requires_current_year_scheduler": True,
            "allow_yearly_scheduler_duplicates": True,
            "callerless_anchors": callerless or [],
            "allowed_multiple_callers": [],
            "allowed_reads": allowed_reads or [],
            "allowed_writes": [],
            "allow_multiple_completion_producers": allow_multiple_completion_producers,
        }
    ]
    if with_other_chain:
        chains.append(
            {
                "name": "OtherCo",
                "tag": "USA",
                "namespace": "USA_other_events",
                "root": "USA_other",
                "tier": 2,
                "full_start_strategies": ["yearly_dispatcher"],
                "outcomes_only_strategy": "suppressed",
                "monthly_driver": "USA_corporate_history_monthly_outcomes",
                "terminal_marker": "USA_other_reconstruct_complete",
                "terminal_date": "2001-03-01",
                "outcome_ideas": [],
                "expected_callers": {},
                "dependency_order": [],
                "localisation_prefixes": ["USA_other"],
                "effect_preview_policy": "engine_or_explicit",
                "bridge_refresh_policy": "none",
                "owned_prefixes": ["USA_other"],
                "variables": {},
                "outcome_idea_prefixes": [],
                "requires_current_year_scheduler": False,
                "allow_yearly_scheduler_duplicates": False,
                "callerless_anchors": other_callerless or [],
                "allowed_multiple_callers": [],
                "allowed_reads": [],
                "allowed_writes": [],
            }
        )
    return {"schema_version": 2, "chains": chains}


def _base_events(include_hidden_ninety=True, include_anchor=False):
    blocks = ["""add_namespace = USA_test_events

country_event = {
\tid = USA_test_events.1
\ttitle = USA_test_events.1.t
\tdesc = USA_test_events.1.d
\tpicture = GFX_test
\tis_triggered_only = yes
\toption = {
\t\tname = USA_test_events.1.a
\t\thidden_effect = {
\t\t\tadd_to_variable = { USA_test_state = 1 }
\t\t\tUSA_test_clamp_state = yes
\t\t}
\t}
}
""".strip()]
    if include_anchor:
        blocks.append("""
country_event = {
\tid = USA_test_events.2
\ttitle = USA_test_events.2.t
\tdesc = USA_test_events.2.d
\tpicture = GFX_test
\tis_triggered_only = yes
\toption = { name = USA_test_events.2.a }
}
""".strip())
    if include_hidden_ninety:
        blocks.append("""
country_event = {
\tid = USA_test_events.90
\thidden = yes
\tis_triggered_only = yes
\tfire_only_once = yes
\timmediate = { USA_test_reconstruct_history = yes }
}
""".strip())
    return "\n\n".join(blocks) + "\n"


def _base_effects():
    return """USA_test_initialize_state = {
\tif = {
\t\tlimit = { NOT = { has_country_flag = USA_test_state_initialized } }
\t\tset_variable = { USA_test_state = 0 }
\t\tset_country_flag = USA_test_state_initialized
\t}
\tUSA_test_clamp_state = yes
}

USA_test_clamp_state = {
\tclamp_variable = { var = USA_test_state min = 0 max = 10 }
}

USA_test_schedule_current_year_events = {
\tif = {
\t\tlimit = {
\t\t\tNOT = { has_start_date < 2001.1.1 }
\t\t\thas_start_date < 2001.1.2
\t\t}
\t\tcountry_event = { id = USA_test_events.1 days = 10 }
\t}
}

USA_test_clear_capstone_outcome = {
\tremove_ideas = {
\t\tUSA_test_outcome_a
\t\tUSA_test_outcome_b
\t}
}

USA_test_resolve_capstone = {
\tUSA_test_clear_capstone_outcome = yes
\tadd_ideas = USA_test_outcome_a
\tset_country_flag = USA_test_outcome_a_resolved
}

USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t\tNOT = { has_country_flag = USA_test_branch_a }
\t\t\tNOT = { has_country_flag = USA_test_branch_b }
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.3.1
\t\t\tNOT = { has_idea = USA_test_outcome_a }
\t\t\tNOT = { has_idea = USA_test_outcome_b }
\t\t}
\t\tUSA_test_resolve_capstone = yes
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _base_core_effects(monthly_registration=True, startup_reconstructs=False):
    startup_body = (
        "USA_test_reconstruct_history = yes"
        if startup_reconstructs
        else "country_event = { id = USA_test_events.90 days = 1 }"
    )
    monthly_call = (
        "\t\tUSA_test_reconstruct_history = yes\n" if monthly_registration else ""
    )
    return f"""corporate_history_on_startup = {{
\tif = {{
\t\tlimit = {{ corporate_history_full_enabled = yes }}
\t\tif = {{
\t\t\tlimit = {{ country_exists = USA }}
\t\t\tUSA = {{
\t\t\t\tUSA_test_schedule_current_year_events = yes
\t\t\t\t{startup_body}
\t\t\t}}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{ corporate_history_outcomes_only_enabled = yes }}
\t\tif = {{
\t\t\tlimit = {{ country_exists = USA }}
\t\t\tUSA = {{ USA_test_reconstruct_history = yes }}
\t\t}}
\t}}
}}

USA_corporate_history_monthly_outcomes = {{
\tif = {{
\t\tlimit = {{
\t\t\tcorporate_history_outcomes_only_enabled = yes
\t\t\toriginal_tag = USA
\t\t\tNOT = {{ has_country_flag = collapsed_nation }}
\t\t\tNOT = {{ has_country_flag = USA_test_reconstruct_complete }}
\t\t}}
{monthly_call}\t}}
}}
"""


def _base_dispatch(duplicate=False):
    extra = (
        "\n\t\t\tcountry_event = { id = USA_test_events.1 days = 20 }"
        if duplicate
        else ""
    )
    return f"""USA_corporate_trigger_year_2001 = {{
\tif = {{
\t\tlimit = {{
\t\t\tcountry_exists = USA
\t\t\tcorporate_history_full_enabled = yes
\t\t}}
\t\tUSA = {{
\t\t\tcountry_event = {{ id = USA_test_events.1 days = 10 }}{extra}
\t\t}}
\t}}
}}
"""


def _base_yearly():
    return """startup_events = {
\tcorporate_history_on_startup = yes
}

trigger_year_2001_events = {
\tUSA_corporate_trigger_year_2001 = yes
}
"""


def _base_ideas(missing_civil_war=False):
    civ = "" if missing_civil_war else "\t\t\tallowed_civil_war = { always = yes }\n"
    return f"""ideas = {{
\tcountry = {{
\t\tUSA_test_outcome_a = {{
\t\t\tpicture = GFX_test
\t\t\tallowed = {{ original_tag = USA }}
{civ}\t\t}}

\t\tUSA_test_outcome_b = {{
\t\t\tpicture = GFX_test
\t\t\tallowed = {{ original_tag = USA }}
\t\t\tallowed_civil_war = {{ always = yes }}
\t\t}}
\t}}
}}
"""


def _build_fixture(
    root: Path,
    *,
    callerless=None,
    include_hidden_ninety=True,
    include_anchor=False,
    monthly_registration=True,
    duplicate_dispatch=False,
    missing_clamp=False,
    treasury_in_reconstruct=False,
    duplicate_complete=False,
    missing_civil_war=False,
    reconstruct_body=None,
    startup_reconstructs=False,
    manifest_overrides=None,
    cross_chain_reads=(),
    cross_chain_trigger_reads=(),
    cross_chain_effect_calls=(),
    cleanup_in_option=False,
    drop_cleanup_effect=False,
    drop_state_effects=False,
    allow_multiple_completion_producers=False,
    extra_effects="",
):
    manifest = _manifest(
        callerless,
        allow_multiple_completion_producers=allow_multiple_completion_producers,
        **(manifest_overrides or {}),
    )
    _write(root, "tools/corporate_history_contract.json", json.dumps(manifest))
    _write(
        root,
        "common/scripted_triggers/MD_corporate_history_triggers.txt",
        """corporate_history_full_enabled = {
	NOT = { has_game_rule = { rule = rule_corporate_history option = outcomes_only } }
	NOT = { has_game_rule = { rule = rule_corporate_history option = disabled } }
}
corporate_history_outcomes_only_enabled = {
	has_game_rule = { rule = rule_corporate_history option = outcomes_only }
}
corporate_history_enabled = {
	OR = {
		corporate_history_full_enabled = yes
		corporate_history_outcomes_only_enabled = yes
	}
}
""",
    )
    _write(
        root,
        "common/game_rules/00_game_rules.txt",
        """rule_corporate_history = {
	default = { name = full }
	option = { name = outcomes_only }
	option = { name = disabled }
}
""",
    )
    _write(
        root,
        "common/scripted_effects/00_corporate_history_effects.txt",
        _base_core_effects(
            monthly_registration=monthly_registration,
            startup_reconstructs=startup_reconstructs,
        ),
    )
    _write(
        root,
        "common/scripted_effects/00_corporate_history_dispatch_effects.txt",
        _base_dispatch(duplicate=duplicate_dispatch),
    )
    _write(root, "common/scripted_effects/00_yearly_effects.txt", _base_yearly())
    effects = _base_effects()
    if reconstruct_body is not None:
        head, _sep, _tail = effects.partition("USA_test_reconstruct_history = {")
        effects = f"{head}USA_test_reconstruct_history = {{\n{reconstruct_body}}}\n"
    if drop_state_effects:
        head, _sep, tail = effects.partition(
            "USA_test_schedule_current_year_events = {"
        )
        del head
        effects = "USA_test_schedule_current_year_events = {" + tail
        effects = effects.replace("\tUSA_test_clamp_state = yes\n", "")
    if cleanup_in_option or drop_cleanup_effect:
        effects = effects.replace(
            "USA_test_clear_capstone_outcome = {\n"
            "\tremove_ideas = {\n"
            "\t\tUSA_test_outcome_a\n"
            "\t\tUSA_test_outcome_b\n"
            "\t}\n"
            "}\n\n",
            "",
        ).replace("\tUSA_test_clear_capstone_outcome = yes\n", "")
    if treasury_in_reconstruct:
        effects = effects.replace(
            "\t\tset_country_flag = USA_test_branch_a\n",
            "\t\tset_country_flag = USA_test_branch_a\n\t\tmodify_treasury_effect = yes\n",
        )
    if duplicate_complete:
        effects += "\nUSA_test_extra_complete = {\n\tset_country_flag = USA_test_reconstruct_complete\n}\n"
    if extra_effects:
        effects += "\n" + extra_effects
    _write(root, "common/scripted_effects/USA_test_effects.txt", effects)
    _write(
        root,
        "common/on_actions/MD_event_on_actions.txt",
        """on_startup = { effect = { corporate_history_on_startup = yes } }
on_monthly_USA = { effect = { USA_corporate_history_monthly_outcomes = yes } }
""",
    )
    events = _base_events(
        include_hidden_ninety=include_hidden_ninety, include_anchor=include_anchor
    )
    if missing_clamp or drop_state_effects:
        events = events.replace("\n\t\t\tUSA_test_clamp_state = yes", "")
    if cleanup_in_option:
        events = events.replace(
            "\t\tname = USA_test_events.1.a\n",
            "\t\tname = USA_test_events.1.a\n"
            "\t\tremove_ideas = {\n"
            "\t\t\tUSA_test_outcome_a\n"
            "\t\t\tUSA_test_outcome_b\n"
            "\t\t}\n",
        )
    if cross_chain_reads or cross_chain_trigger_reads:
        flag_reads = [f"\t\t\thas_country_flag = {flag}" for flag in cross_chain_reads]
        trigger_reads = [
            f"\t\t\tmodifier = {{ add = 5 {trigger} = yes }}"
            for trigger in cross_chain_trigger_reads
        ]
        reads = "\n".join(flag_reads + trigger_reads)
        events = events.replace(
            "\t\tname = USA_test_events.1.a\n",
            f"\t\tname = USA_test_events.1.a\n\t\tai_chance = {{\n\t\t\tbase = 10\n{reads}\n\t\t}}\n",
        )
    if cross_chain_effect_calls:
        calls = "\n".join(f"\t\t{effect} = yes" for effect in cross_chain_effect_calls)
        events = events.replace(
            "\t\tname = USA_test_events.1.a\n",
            f"\t\tname = USA_test_events.1.a\n{calls}\n",
        )
    _write(root, "events/USA_test_events.txt", events)
    _write(root, "common/ideas/USA_test_ideas.txt", _base_ideas(missing_civil_war))
    _write_loc(
        root,
        "localisation/english/MD_focus_USA_l_english.yml",
        """l_english:
 USA_test_events.1.t: "Test event"
 USA_test_events.1.d: "Test description."
 USA_test_events.1.a: "Choose the test"
 USA_test_events.2.t: "Test anchor"
 USA_test_events.2.d: "Test anchor description."
 USA_test_events.2.a: "Choose the anchor"
 USA_test_outcome_a: "Outcome A"
 USA_test_outcome_a_desc: "The first outcome."
 USA_test_outcome_b: "Outcome B"
 USA_test_outcome_b_desc: "The second outcome."
""",
    )


def _messages(root: Path):
    validator = Validator(
        mod_path=str(root), use_colors=False, workers=1, no_cache=True
    )
    validator.run_all_validations()
    return [issue.message for issue in validator._issues]


def _enable_bridge_fixture(root: Path, *, refresh: str):
    manifest_path = root / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["bridge_refresh_policy"] = "immediate"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    events_path = root / "events/USA_test_events.txt"
    events = events_path.read_text(encoding="utf-8")
    if refresh == "transitive":
        mutation = "\t\tUSA_test_finish_bridge = yes\n"
    else:
        mutation = "\t\tset_country_flag = USA_test_bridge_outcome\n"
        if refresh == "direct":
            mutation += "\t\tUSA_corporate_systems_update_economic_bridge = yes\n"
    events_path.write_text(
        events.replace(
            "\t\tname = USA_test_events.1.a\n",
            "\t\tname = USA_test_events.1.a\n" + mutation,
        ),
        encoding="utf-8",
    )

    axes = (
        "open_standards",
        "vertical_integration",
        "supply_resilience",
        "security_control",
        "national_compute_stack",
    )
    reset = "\n".join(
        f"\tset_temp_variable = {{ USA_oem_contribution_{axis} = 0 }}" for axis in axes
    )
    contribution_clamps = "\n".join(
        f"\tclamp_temp_variable = {{ var = USA_oem_contribution_{axis} min = -3 max = 3 }}"
        for axis in axes
    )
    effective = "\n".join(
        f"\tset_variable = {{ USA_oem_effective_{axis} = 0 }}\n"
        f"\tadd_to_variable = {{ USA_oem_effective_{axis} = USA_oem_contribution_{axis} }}\n"
        f"\tclamp_variable = {{ var = USA_oem_effective_{axis} min = 0 max = 10 }}"
        for axis in axes
    )
    score = "\n".join(
        (
            f"\t\tset_temp_variable = {{ USA_corporate_systems_economic_integration_score = USA_oem_effective_{axes[0]} }}",
            *(
                f"\t\tadd_to_temp_variable = {{ USA_corporate_systems_economic_integration_score = USA_oem_effective_{axis} }}"
                for axis in axes[1:]
            ),
        )
    )
    helper = (
        "USA_test_finish_bridge = {\n"
        "\tset_country_flag = USA_test_bridge_outcome\n"
        "\tUSA_corporate_systems_update_economic_bridge = yes\n"
        "}\n\n"
        if refresh == "transitive"
        else ""
    )
    _write(
        root,
        "common/scripted_effects/USA_corporate_systems_effects.txt",
        f"""{helper}USA_corporate_systems_clear_economic_bridge_ideas = {{
\tremove_ideas = {{
\t\tUSA_corporate_systems_economic_integration_1
\t\tUSA_corporate_systems_economic_integration_2
\t\tUSA_corporate_systems_economic_integration_3
\t\tUSA_corporate_systems_economic_integration_4
\t\tUSA_corporate_systems_economic_integration_5
\t}}
}}

USA_corporate_systems_clear_derived_axes = {{
\tset_variable = {{ USA_oem_effective_open_standards = 0 }}
}}

USA_corporate_systems_test_contribution = {{
\tif = {{
\t\tlimit = {{ has_country_flag = USA_test_bridge_outcome }}
\t\tadd_to_temp_variable = {{ USA_oem_contribution_open_standards = 1 }}
\t}}
}}

USA_corporate_systems_rebuild_company_contributions = {{
{reset}
\tUSA_corporate_systems_test_contribution = yes
{contribution_clamps}
}}

USA_corporate_systems_rebuild_effective_axes = {{
{effective}
}}

USA_corporate_systems_update_economic_bridge = {{
\tif = {{
\t\tlimit = {{ corporate_history_enabled = yes }}
\t\tUSA_corporate_systems_rebuild_company_contributions = yes
\t\tUSA_corporate_systems_rebuild_effective_axes = yes
{score}
\t\tif = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 15 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_1
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 22 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_2
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 29 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_3
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 38 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_4
\t\t}}
\t\telse = {{ add_ideas = USA_corporate_systems_economic_integration_5 }}
\t}}
\telse = {{
\t\tUSA_corporate_systems_clear_derived_axes = yes
\t\tUSA_corporate_systems_clear_economic_bridge_ideas = yes
\t}}
}}
""",
    )


def _enable_economic_layer_fixture(root: Path):
    manifest_path = root / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 3
    manifest["economic_layers"] = [
        {
            "name": "Test Real Options",
            "tag": "USA",
            "updater": "USA_oem_update_real_options_economy",
            "bridge": "USA_corporate_systems_update_economic_bridge",
            "effect_file": "common/scripted_effects/USA_oem_real_options_effects.txt",
            "dynamic_modifier_file": "common/dynamic_modifiers/05_USA_oem_test.txt",
            "decision_file": "common/decisions/USA_oem_test.txt",
            "idea_file": "common/ideas/USA_oem_test_ideas.txt",
            "scripted_localisation_file": "common/scripted_localisation/USA_oem_test.txt",
            "localisation_file": "localisation/english/MD_focus_USA_l_english.yml",
            "initialized_flag": "USA_oem_real_options_initialized",
            "variables": {"USA_oem_option_value": {"min": 0, "max": 100}},
            "source_variables": ["USA_oem_effective_open_standards"],
            "cdf": {
                "input_min": -3,
                "input_max": 3,
                "output_min": 0,
                "output_max": 1,
                "knots": [0, 1],
                "values": [0.5, 0.84134],
            },
            "modifier_families": [
                {
                    "name": "investment_climate",
                    "score": "USA_oem_option_value",
                    "thresholds": [50],
                    "members": [
                        "USA_oem_investment_climate_1",
                        "USA_oem_investment_climate_2",
                    ],
                }
            ],
            "policy_programs": [
                {
                    "decision": f"USA_oem_policy_{number}",
                    "idea": f"USA_oem_program_{number}",
                    "program_class": (
                        "major_commitment" if number in {2, 4} else "operational"
                    ),
                    "days": 365 if number in {2, 4} else 180,
                    "cooldown_days": 365 if number in {2, 4} else 180,
                    "refresh_policy": "block_while_active",
                    "cleanup_owner": "USA_oem_update_real_options_economy",
                }
                for number in range(1, 5)
            ],
            "dashboard_variables": ["USA_oem_option_value_display"],
            "scripted_localisation": ["USA_oem_investment_climate_label"],
            "localisation_keys": [
                "USA_corporate_systems_real_options",
                "USA_corporate_systems_real_options_desc",
            ],
        }
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    _write(
        root,
        "common/scripted_effects/USA_oem_real_options_effects.txt",
        """USA_corporate_systems_update_economic_bridge = {
	USA_oem_update_real_options_economy = yes
}

USA_oem_update_real_options_economy = {
	if = {
		limit = {
			corporate_history_enabled = yes
			original_tag = USA
			NOT = { has_country_flag = collapsed_nation }
		}
		set_country_flag = USA_oem_real_options_initialized
		set_temp_variable = { USA_oem_test_source = USA_oem_effective_open_standards }
		set_variable = { USA_oem_option_value = { value = 50 clamp = { min = 0 max = 100 } } }
		clamp_variable = { var = USA_oem_option_value min = 0 max = 100 }
		set_variable = { USA_oem_option_value_display = { value = USA_oem_option_value round = yes } }
		set_temp_variable = { USA_oem_cdf_output = 0.5 }
		if = {
			limit = { check_variable = { USA_oem_cdf_input > 0 } }
			set_temp_variable = { USA_oem_cdf_output = 0.84134 }
		}
		clamp_temp_variable = { var = USA_oem_cdf_output min = 0 max = 1 }
		if = {
			limit = { check_variable = { USA_oem_option_value < 50 } }
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
			add_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
		}
		else = {
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
			add_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
		}
	}
	else = {
		clr_country_flag = USA_oem_real_options_initialized
		remove_ideas = {
			USA_oem_program_1
			USA_oem_program_2
			USA_oem_program_3
			USA_oem_program_4
		}
		clear_variable = USA_oem_option_value
		clear_variable = USA_oem_option_value_display
		remove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
		remove_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
	}
}
""",
    )
    _write(
        root,
        "common/dynamic_modifiers/05_USA_oem_test.txt",
        """USA_oem_investment_climate_1 = {
	enable = { always = yes }
	productivity_growth_modifier = -0.01
}

USA_oem_investment_climate_2 = {
	enable = { always = yes }
	productivity_growth_modifier = 0.01
}
""",
    )

    decisions = []
    idea_blocks = []
    loc_lines = [
        ' USA_corporate_systems_real_options: "Real Options"',
        ' USA_corporate_systems_real_options_desc: "[?USA_oem_option_value_display|0]"',
        ' USA_oem_investment_climate_1: "Frozen"',
        ' USA_oem_investment_climate_1_desc: "Frozen investment."',
        ' USA_oem_investment_climate_2: "Investable"',
        ' USA_oem_investment_climate_2_desc: "Investable conditions."',
    ]
    for number in range(1, 5):
        program_days = 365 if number in {2, 4} else 180
        decisions.append(f"""USA_oem_policy_{number} = {{
	days_re_enable = {program_days}

	fire_only_once = no

	available = {{
		NOT = {{ has_country_flag = collapsed_nation }}
		NOT = {{ has_idea = USA_oem_program_{number} }}
	}}
	complete_effect = {{
		add_timed_idea = {{ idea = USA_oem_program_{number} days = {program_days} }}
	}}
}}""")
        idea_blocks.append(f"""USA_oem_program_{number} = {{
	picture = generic_economic_increase
	allowed = {{ original_tag = USA }}
	allowed_civil_war = {{ always = yes }}
}}""")
        loc_lines.extend(
            [
                f' USA_oem_policy_{number}_desc: "Runs for {program_days} days."',
                f' USA_oem_policy_{number}_tt: "Temporary program for {program_days} days."',
                f' USA_oem_program_{number}: "Program {number}"',
                f' USA_oem_program_{number}_desc: "Program {number} description."',
            ]
        )
    _write(root, "common/decisions/USA_oem_test.txt", "\n\n".join(decisions))
    indented_ideas = "\n\n".join(
        "\t\t" + block.replace("\n", "\n\t\t") for block in idea_blocks
    )
    _write(
        root,
        "common/ideas/USA_oem_test_ideas.txt",
        f"ideas = {{\n\tcountry = {{\n{indented_ideas}\n\t}}\n}}\n",
    )
    _write(
        root,
        "common/scripted_localisation/USA_oem_test.txt",
        """defined_text = {
	name = USA_oem_investment_climate_label
	text = { localization_key = USA_oem_investment_climate_1 }
}
""",
    )
    loc_path = root / "localisation/english/MD_focus_USA_l_english.yml"
    existing_loc = loc_path.read_text(encoding="utf-8-sig")
    _write_loc(
        root,
        "localisation/english/MD_focus_USA_l_english.yml",
        existing_loc + "\n" + "\n".join(loc_lines) + "\n",
    )


def _enable_reusable_lifecycle_fixture(root: Path):
    _enable_economic_layer_fixture(root)
    manifest_path = root / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    layer = manifest["economic_layers"][0]
    manifest["reusable_decision_lifecycles"] = [
        {
            "name": "Test Real Options",
            "decision_file": layer["decision_file"],
            "effect_file": layer["effect_file"],
            "localisation_file": layer["localisation_file"],
            "programs": [
                {
                    "decision": program["decision"],
                    "kind": "timed_idea",
                    "idea": program["idea"],
                    "active_days": program["days"],
                    "cooldown_mode": "days_re_enable",
                    "cooldown_days": program["cooldown_days"],
                    "duration_source": "decision",
                    "localisation_keys": [
                        f"{program['decision']}_desc",
                        f"{program['decision']}_tt",
                    ],
                    "cleanup_effect": "USA_oem_update_real_options_economy",
                }
                for program in layer["policy_programs"]
            ],
        }
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


_COMPLETE_BRANCH = """\tif = {
\t\tlimit = {
\t\t\tdate > 2001.3.1
\t\t\tNOT = { has_idea = USA_test_outcome_a }
\t\t\tNOT = { has_idea = USA_test_outcome_b }
\t\t}
\t\tUSA_test_resolve_capstone = yes
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
"""


def _reconstruct(branch: str) -> str:
    return branch + _COMPLETE_BRANCH


_UNGUARDED_MESSAGE = (
    "USA_test_reconstruct_history has a state-changing block "
    "without sibling-marker guards"
)


def _guarded_branch(limit_body: str) -> str:
    return (
        "\tif = {\n"
        "\t\tlimit = {\n"
        "\t\t\tdate > 2001.2.1\n"
        f"{limit_body}"
        "\t\t}\n"
        "\t\tset_country_flag = USA_test_branch_a\n"
        "\t\tadd_to_variable = { USA_test_state = 1 }\n"
        "\t\tUSA_test_clamp_state = yes\n"
        "\t}\n"
    )


def _schema_v6_dispatcher_messages(root: Path) -> list[str]:
    validator = Validator(str(root), no_color=True)
    chains = validator._load_manifest()
    validator._manifest_payload["schema_version"] = 6
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    return [
        message
        for message, _file, _line in validator._validate_dispatchers(
            chains, effect_defs, event_defs, {}
        )
    ]


__all__ = [
    "Decimal",
    "Path",
    "Validator",
    "_COMPLETE_BRANCH",
    "_NATIVE_ARRAY_BLOCK_EFFECTS",
    "_NATIVE_CONTRACT_ROLES",
    "_NATIVE_VARIABLE_BLOCK_EFFECTS",
    "_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS",
    "_UNGUARDED_MESSAGE",
    "_base_core_effects",
    "_base_dispatch",
    "_base_effects",
    "_base_events",
    "_base_ideas",
    "_base_yearly",
    "_build_fixture",
    "_collect_native_write_tokens",
    "_enable_bridge_fixture",
    "_enable_economic_layer_fixture",
    "_enable_reusable_lifecycle_fixture",
    "_guarded_branch",
    "_is_repeatable_decision",
    "_manifest",
    "_messages",
    "_reconstruct",
    "_removes_active_decision",
    "_schema_v6_dispatcher_messages",
    "_write",
    "_write_loc",
    "json",
    "pytest",
]
