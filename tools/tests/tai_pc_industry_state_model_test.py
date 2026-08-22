import datetime
import json
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from simulate_corporate_history import ScriptIndex, run_scenarios

EVENTS_PATH = ROOT / "events" / "TAI_pc_industry_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "TAI_pc_industry_effects.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "TAI_pc_industry_ideas.txt"
LOCALISATION_PATH = ROOT / "localisation" / "english" / "MD_focus_TAI_l_english.yml"
COMMON_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_effects.txt"
)
DISPATCH_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_dispatch_effects.txt"
)
ON_ACTIONS_PATH = (
    ROOT / "common" / "on_actions" / "02_oem_corporate_history_monthly_on_actions.txt"
)
MONTHLY_DISPATCH_PATH = (
    ROOT
    / "common"
    / "scripted_effects"
    / "00_corporate_history_monthly_dispatch_effects.txt"
)
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
SCENARIOS_PATH = ROOT / "tools" / "corporate_history_scenarios.json"

AXES = (
    "TAI_pc_component_depth",
    "TAI_pc_global_brand_reach",
    "TAI_pc_platform_independence",
    "TAI_pc_systems_breadth",
)
INITIAL = (7, 4, 3, 4)

ROUTES = (
    (
        ("TAI_acer_brand_led_restructuring", (0, 2, 0, 1)),
        ("TAI_acer_integrated_manufacturing", (2, 0, 0, 1)),
        ("TAI_acer_hybrid_production_network", (1, 1, 0, 1)),
    ),
    (
        ("TAI_via_x86_confrontation", (1, 0, 1, 0)),
        ("TAI_via_early_settlement", (0, 1, 0, 1)),
        ("TAI_via_chipset_retreat", (2, 0, -1, 0)),
    ),
    (
        ("TAI_via_cross_license_settlement", (0, 0, 1, 0)),
        ("TAI_via_prolonged_litigation", (1, 0, 2, 0)),
        ("TAI_via_licensed_partnership", (0, 1, -1, 1)),
    ),
    (
        ("TAI_msi_notebook_entry", (0, 1, 0, 1)),
        ("TAI_msi_component_specialization", (2, 0, 0, 0)),
        ("TAI_msi_server_systems", (1, 0, 0, 2)),
    ),
    (
        ("TAI_via_c7_low_power", (0, 0, 1, 1)),
        ("TAI_via_broad_cpu_program", (0, 0, 2, 1)),
        ("TAI_via_chipset_licensing", (2, 0, -1, 0)),
    ),
    (
        ("TAI_asus_rog_enthusiast_identity", (1, 1, 0, 0)),
        ("TAI_asus_component_leadership", (2, 0, 0, 0)),
        ("TAI_asus_mass_market_systems", (0, 2, 0, 2)),
    ),
    (
        ("TAI_gigabyte_joint_venture_approved", (0, 0, 0, 1)),
        ("TAI_gigabyte_independent_components", (2, 0, 0, 0)),
        ("TAI_gigabyte_systems_investment", (0, 1, 0, 2)),
    ),
    (
        ("TAI_gigabyte_joint_venture_suspended", (1, 1, 0, 0)),
        ("TAI_gigabyte_joint_venture_revived", (0, 1, 0, 2)),
        ("TAI_gigabyte_independent_systems", (0, 1, 0, 2)),
    ),
    (
        ("TAI_msi_gaming_notebooks", (0, 1, 0, 1)),
        ("TAI_msi_consumer_notebooks", (0, 2, 0, 1)),
        ("TAI_msi_professional_systems", (1, 0, 0, 2)),
    ),
    (
        ("TAI_asus_eee_value_mobility", (0, 2, 0, 1)),
        ("TAI_asus_premium_notebooks", (0, 2, 0, 1)),
        ("TAI_asus_component_platforms", (2, 0, 0, 0)),
    ),
    (
        ("TAI_acer_gateway_acquisition", (0, 1, 0, 1)),
        ("TAI_acer_organic_brand_growth", (0, 2, 0, 1)),
        ("TAI_acer_profitability_discipline", (0, 1, 0, 1)),
    ),
    (
        ("TAI_asus_brand_oem_separation", (1, 1, 0, 0)),
        ("TAI_asus_vertical_integration", (1, 0, 0, 2)),
        ("TAI_asus_component_oem_retreat", (2, -1, 0, 0)),
    ),
    (
        ("TAI_via_nano_focused_platform", (0, 0, 1, 1)),
        ("TAI_via_third_x86_ecosystem", (1, 0, 3, 1)),
        ("TAI_via_ip_licensing_platform", (1, 1, -2, 0)),
    ),
    (
        ("TAI_acer_margin_reset", (0, -1, 0, 0)),
        ("TAI_acer_market_share_drive", (0, 1, 0, 1)),
        ("TAI_acer_premium_systems_reset", (0, 1, 0, 2)),
    ),
)

MILESTONES = (
    (1, 2000, "2000.3.1", 60),
    (2, 2001, "2001.9.7", 249),
    (3, 2003, "2003.4.7", 96),
    (4, 2004, "2004.5.1", 121),
    (5, 2005, "2005.5.27", 146),
    (6, 2006, "2006.6.1", 151),
    (7, 2006, "2006.8.8", 219),
    (8, 2007, "2007.3.22", 80),
    (9, 2007, "2007.4.15", 104),
    (10, 2007, "2007.6.5", 155),
    (11, 2007, "2007.8.27", 238),
    (12, 2007, "2007.10.30", 302),
    (13, 2008, "2008.5.29", 149),
    (14, 2011, "2011.3.31", 89),
    (15, 2013, "2013.6.30", 180),
)

OUTCOMES = {
    "global_component_commonwealth": "TAI_pc_global_component_commonwealth",
    "branded_systems_powerhouse": "TAI_pc_branded_systems_powerhouse",
    "full_spectrum_computing_ecosystem": ("TAI_pc_full_spectrum_computing_ecosystem"),
    "fragmented_margin_squeeze": "TAI_pc_fragmented_margin_squeeze",
}


def _extract_block(text: str, start: int) -> str:
    opening = text.index("{", start)
    depth = 0
    in_comment = False
    in_string = False
    escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == "#":
            in_comment = True
        elif character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError("Unclosed scripted block")


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing block {name}"
    return _extract_block(text, match.start())


def _script_day_after(value: str) -> str:
    year, month, day = (int(part) for part in value.split("."))
    next_day = datetime.date(year, month, day) + datetime.timedelta(days=1)
    return f"{next_day.year}.{next_day.month}.{next_day.day}"


def _event_block(text: str, event_number: int) -> str:
    event_id = f"TAI_pc_industry_events.{event_number}"
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, match.start())
        if re.search(rf"\bid\s*=\s*{re.escape(event_id)}\b", block):
            return block
    raise AssertionError(f"Missing event {event_id}")


def _option_blocks(event: str) -> List[str]:
    return [
        _extract_block(event, match.start())
        for match in re.finditer(r"(?m)^\toption\s*=\s*\{", event)
    ]


def _assignment_blocks(text: str, key: str) -> List[str]:
    return [
        _extract_block(text, match.start())
        for match in re.finditer(rf"\b{re.escape(key)}\s*=\s*\{{", text)
    ]


def _has_bankruptcy_zero_modifier(option: str) -> bool:
    ai_chance_blocks = _assignment_blocks(option, "ai_chance")
    assert len(ai_chance_blocks) == 1
    for modifier in _assignment_blocks(ai_chance_blocks[0], "modifier"):
        factor_zero = re.search(r"\bfactor\s*=\s*0(?:\.0+)?(?=\s|\})", modifier)
        bankruptcy = re.search(
            r"\bhas_active_mission\s*=\s*bankruptcy_incoming_collapse\b",
            modifier,
        )
        if factor_zero and bankruptcy:
            return True
    return False


def _idea_block(text: str, idea: str) -> str:
    match = re.search(rf"(?m)^\t\t{re.escape(idea)}\s*=\s*\{{", text)
    assert match, f"Missing idea {idea}"
    return _extract_block(text, match.start())


def _axis_writes(text: str) -> List[Tuple[str, int]]:
    return [
        (axis, int(value))
        for axis, value in re.findall(
            r"add_to_variable\s*=\s*\{\s*" r"(TAI_pc_[A-Za-z0-9_]+)\s*=\s*(-?\d+)\s*\}",
            text,
        )
        if axis in AXES
    ]


def _apply_route(route: str) -> Tuple[Tuple[int, ...], Set[str]]:
    state = list(INITIAL)
    flags = set()
    for event_index, letter in enumerate(route):
        choice_index = ord(letter) - ord("A")
        flag, delta = ROUTES[event_index][choice_index]
        flags.add(flag)
        state = [max(0, min(10, value + change)) for value, change in zip(state, delta)]
    return tuple(state), flags


def _resolve(state: Tuple[int, ...], flags: Set[str]) -> str:
    component, brand, platform, systems = state
    if (
        min(state) >= 8
        and "TAI_via_third_x86_ecosystem" in flags
        and "TAI_gigabyte_independent_systems" in flags
        and flags & {"TAI_asus_brand_oem_separation", "TAI_asus_vertical_integration"}
        and flags & {"TAI_msi_consumer_notebooks", "TAI_msi_professional_systems"}
        and flags & {"TAI_acer_premium_systems_reset", "TAI_acer_margin_reset"}
    ):
        return "full_spectrum_computing_ecosystem"
    if (
        brand >= 9
        and systems >= 8
        and "TAI_acer_profitability_discipline" in flags
        and "TAI_asus_brand_oem_separation" in flags
        and flags & {"TAI_msi_consumer_notebooks", "TAI_msi_professional_systems"}
        and flags & {"TAI_acer_margin_reset", "TAI_acer_premium_systems_reset"}
    ):
        return "branded_systems_powerhouse"
    if (
        component >= 9
        and "TAI_gigabyte_independent_components" in flags
        and "TAI_asus_component_leadership" in flags
        and "TAI_msi_component_specialization" in flags
        and flags
        & {
            "TAI_gigabyte_joint_venture_suspended",
            "TAI_gigabyte_independent_systems",
        }
        and flags & {"TAI_asus_component_oem_retreat", "TAI_asus_brand_oem_separation"}
        and flags
        & {
            "TAI_msi_gaming_notebooks",
            "TAI_msi_consumer_notebooks",
            "TAI_msi_professional_systems",
        }
        and flags & {"TAI_via_nano_focused_platform", "TAI_via_ip_licensing_platform"}
    ):
        return "global_component_commonwealth"
    return "fragmented_margin_squeeze"


def test_initial_state_clamp_and_manifest_bounds_match():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "TAI_pc_industry_initialize_state")
    clamp = _named_block(effects, "TAI_pc_industry_clamp_state")

    for axis, value in zip(AXES, INITIAL):
        assert f"set_variable = {{ {axis} = {value} }}" in initialize
        assert f"set_temp_variable = {{ corp_value = {axis} }}" in clamp
        assert f"set_variable = {{ {axis} = corp_value }}" in clamp
    assert clamp.count("corporate_history_clamp_value = yes") == len(AXES)

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(
        item for item in manifest["chains"] if item["root"] == "TAI_pc_industry"
    )
    assert chain["name"] == "Taiwan's PC Giants"
    assert chain["tag"] == "TAI"
    assert chain["namespace"] == "TAI_pc_industry_events"
    assert chain["tier"] == 1
    assert set(chain["variables"]) == set(AXES)
    assert all(
        bounds == {"min": 0, "max": 10} for bounds in chain["variables"].values()
    )
    assert chain["owned_prefixes"] == [
        "TAI_pc_industry",
        "TAI_asus",
        "TAI_gigabyte",
        "TAI_acer",
        "TAI_msi",
        "TAI_via",
    ]
    assert chain["allowed_reads"] == []
    assert chain["allowed_writes"] == []
    assert chain["dependency_order"] == []


def test_visible_event_routes_are_distinct_clamped_and_consumed_later():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    resolver = _named_block(effects, "TAI_pc_industry_resolve_capstone")
    event_ids = re.findall(
        r"(?m)^\s*id\s*=\s*(TAI_pc_industry_events\.\d+)\s*$", events
    )
    assert event_ids == [f"TAI_pc_industry_events.{number}" for number in range(1, 16)]
    assert len(event_ids) == len(set(event_ids))

    for event_number, expected_routes in enumerate(ROUTES, start=1):
        event = _event_block(events, event_number)
        options = _option_blocks(event)
        assert len(options) == 3
        assert "is_triggered_only = yes" in event
        assert "fire_only_once = yes" in event
        assert "original_tag = TAI" in event
        assert "rule_corporate_history" not in event
        assert f"TAI_pc_industry_event_{event_number:02d}_resolved" in event
        for marker in ("pending", "delivery_expected", "startup_skipped"):
            assert (
                f"clr_country_flag = "
                f"TAI_pc_industry_event_{event_number:02d}_{marker}" in event
            )

        later_events = "\n".join(
            _event_block(events, later) for later in range(event_number + 1, 15)
        )
        consumer_text = later_events + "\n" + resolver
        for option_index, (option, (flag, delta)) in enumerate(
            zip(options, expected_routes)
        ):
            suffix = "abc"[option_index]
            key = f"TAI_pc_industry_events.{event_number}.{suffix}"
            option_flags = re.findall(
                r"set_country_flag\s*=\s*"
                r"(TAI_(?:acer|asus|gigabyte|msi|via)_[A-Za-z0-9_]+)",
                option,
            )
            assert option_flags == [flag]
            assert sorted(_axis_writes(option)) == sorted(
                (axis, change) for axis, change in zip(AXES, delta) if change
            )
            assert option.count("TAI_pc_industry_clamp_state = yes") == 1
            assert f"name = {key}" in option
            assert f"custom_effect_tooltip = {key}_tt" in option
            assert f'{key} executed"' in option
            assert "ai_chance = { base = " in option
            assert f"has_country_flag = {flag}" in consumer_text

    capstone = _event_block(events, 15)
    assert len(_option_blocks(capstone)) == 1
    assert "TAI_pc_industry_resolve_capstone = yes" in capstone
    assert "set_country_flag = TAI_pc_industry_reconstruct_complete" in capstone
    assert "TAI_pc_industry_events.90" not in events
    assert "TAI_pc_industry_reconstruct_history = {" in effects


def test_material_costs_are_bankruptcy_safe_and_via_premium_is_gated():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    for event_number in range(1, 15):
        options = _option_blocks(_event_block(events, event_number))
        assert any(
            not re.search(r"treasury_change\s*=\s*-(?:[5-9]|\d{2,})\.\d+", option)
            for option in options
        )
        for option in options:
            material_cost = re.search(
                r"treasury_change\s*=\s*-(?:[5-9]|\d{2,})\.\d+", option
            )
            if material_cost:
                assert _has_bankruptcy_zero_modifier(option)

    via_premium = _option_blocks(_event_block(events, 13))[1]
    for required in (
        "TAI_via_x86_confrontation",
        "TAI_via_cross_license_settlement",
        "TAI_via_c7_low_power",
        "TAI_via_broad_cpu_program",
    ):
        assert f"has_country_flag = {required}" in via_premium
    assert (
        "check_variable = { var = TAI_pc_platform_independence value = 6 "
        "compare = greater_than_or_equals }" in via_premium
    )
    assert "treasury_change = -8.00" in via_premium
    assert "add_political_power = -25" in via_premium


def test_bankruptcy_guard_requires_zero_factor_and_predicate_in_same_modifier():
    split_guard = """
option = {
	ai_chance = {
		modifier = { factor = 0 has_country_flag = unrelated }
		modifier = {
			factor = 2
			has_active_mission = bankruptcy_incoming_collapse
		}
	}
}
"""
    combined_guard = """
option = {
	ai_chance = {
		modifier = {
			factor = 0
			has_active_mission = bankruptcy_incoming_collapse
		}
	}
}
"""
    assert not _has_bankruptcy_zero_modifier(split_guard)
    assert _has_bankruptcy_zero_modifier(combined_guard)


def test_historical_reconstruction_is_idempotent_reward_free_and_fragmented():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    historical_blocks = []
    for event_number, routes in enumerate(ROUTES, start=1):
        block = _named_block(
            effects, f"TAI_pc_industry_apply_historical_event_{event_number:02d}"
        )
        historical_blocks.append(block)
        flag, delta = routes[0]
        company_flags = re.findall(
            r"set_country_flag\s*=\s*"
            r"(TAI_(?:acer|asus|gigabyte|msi|via)_[A-Za-z0-9_]+)",
            block,
        )
        assert company_flags == [flag]
        assert sorted(_axis_writes(block)) == sorted(
            (axis, change) for axis, change in zip(AXES, delta) if change
        )
        assert "NOT = { OR = {" in block
        assert block.count("TAI_pc_industry_clamp_state = yes") == 1
        assert f"TAI_pc_industry_event_{event_number:02d}_resolved" in block

    reconstruction = _named_block(effects, "TAI_pc_industry_reconstruct_history")
    reconstruction_graph = "\n".join(historical_blocks) + "\n" + reconstruction
    for forbidden in (
        "modify_treasury_effect",
        "treasury_change",
        "add_political_power",
        "add_stability",
        "add_tech_bonus",
        "add_timed_idea",
        "add_building_construction",
        "add_offsite_building",
        "country_event =",
    ):
        assert forbidden not in reconstruction_graph

    for event_number, _year, date, _delay in MILESTONES:
        assert f"date > {date}" in reconstruction
        assert f"TAI_pc_industry_event_{event_number:02d}_resolved" in reconstruction
        assert (
            f"TAI_pc_industry_event_{event_number:02d}_delivery_expected"
            in reconstruction
        )
    assert "set_country_flag = TAI_pc_industry_reconstruct_complete" in reconstruction

    state, flags = _apply_route("A" * 14)
    assert state == (10, 9, 7, 10)
    assert _resolve(state, flags) == "fragmented_margin_squeeze"


def test_all_capstones_are_reachable_priority_ordered_and_mutually_exclusive():
    routes = {
        "full_spectrum_computing_ecosystem": "AAAAAACCCAAABA",
        "branded_systems_powerhouse": "AAAAAAAABACAAA",
        "global_component_commonwealth": "AAABABBAAAAAAA",
        "fragmented_margin_squeeze": "A" * 14,
    }
    for expected, route in routes.items():
        state, flags = _apply_route(route)
        assert _resolve(state, flags) == expected

    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    assert "TAI_pc_industry_outcome_" not in effects
    resolver = _named_block(effects, "TAI_pc_industry_resolve_capstone")
    ordered_calls = (
        "TAI_pc_industry_apply_full_spectrum_computing_ecosystem",
        "TAI_pc_industry_apply_branded_systems_powerhouse",
        "TAI_pc_industry_apply_global_component_commonwealth",
        "TAI_pc_industry_apply_fragmented_margin_squeeze",
    )
    positions = [resolver.index(call) for call in ordered_calls]
    assert positions == sorted(positions)

    clear = _named_block(effects, "TAI_pc_industry_clear_capstone_outcome")
    for suffix, idea in OUTCOMES.items():
        assert idea in clear
        applicator = _named_block(effects, f"TAI_pc_industry_apply_{suffix}")
        assert applicator.count("TAI_pc_industry_clear_capstone_outcome = yes") == 1
        assert f"add_ideas = {idea}" in applicator
        assert "set_country_flag = TAI_pc_industry_capstone_resolved" in applicator
        assert len(re.findall(rf"(?m)^\t\t{re.escape(idea)}\s*=\s*\{{", ideas)) == 1


def test_delivery_markers_recovery_and_dispatch_cover_every_milestone():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    dispatch = DISPATCH_PATH.read_text(encoding="utf-8")
    on_actions = ON_ACTIONS_PATH.read_text(encoding="utf-8")
    monthly_dispatch = MONTHLY_DISPATCH_PATH.read_text(encoding="utf-8")
    current_year = _named_block(effects, "TAI_pc_industry_schedule_current_year_events")
    recovery = _named_block(effects, "TAI_pc_industry_recover_missing_events")

    for event_number, year, date, delay in MILESTONES:
        prefix = f"TAI_pc_industry_event_{event_number:02d}"
        if event_number > 1:
            wrapper = _named_block(
                effects, f"TAI_pc_industry_schedule_event_{event_number:02d}"
            )
            assert f"NOT = {{ has_country_flag = {prefix}_resolved }}" in wrapper
            assert (
                f"NOT = {{ has_country_flag = {prefix}_delivery_expected }}" in wrapper
            )
            assert f"NOT = {{ has_country_flag = {prefix}_pending }}" in wrapper
            assert f"set_country_flag = {prefix}_delivery_expected" in wrapper
            assert f"flag = {prefix}_pending value = 1 days = {delay + 60}" in wrapper
            assert (
                f"country_event = {{ id = TAI_pc_industry_events.{event_number} "
                f"days = {delay} }}" in wrapper
            )

        event = _event_block(events, event_number)
        assert f"set_country_flag = {prefix}_resolved" in event
        assert f"clr_country_flag = {prefix}_pending" in event
        assert f"clr_country_flag = {prefix}_delivery_expected" in event
        assert f"clr_country_flag = {prefix}_startup_skipped" in event

        assert f"pc_recovery_target = {event_number}" in recovery
        assert f"pc_recovery_target = {event_number}" in current_year
        assert f"flag = {prefix}_pending value = 1 days = 65" in current_year
        assert (
            f"country_event = {{ id = TAI_pc_industry_events.{event_number} "
            "days = 5 }" in current_year
        )
        assert f"date > {date}" in recovery
        assert f"has_start_date < {year}.1.2" in current_year

    assert "TAI_pc_industry_start_year_events_scheduled" in current_year
    assert (
        "set_country_flag = TAI_pc_industry_start_year_events_scheduled" in current_year
    )

    events_by_year = {}
    for event_number, year, _date, _delay in MILESTONES[1:]:
        events_by_year.setdefault(year, []).append(event_number)
    for year, event_numbers in events_by_year.items():
        year_effect = _named_block(dispatch, f"TAI_corporate_trigger_year_{year}")
        for event_number in event_numbers:
            assert (
                f"TAI_pc_industry_schedule_event_{event_number:02d} = yes"
                in year_effect
            )
        assert monthly_dispatch.count(f"TAI_corporate_trigger_year_{year} = yes") == 1
    assert on_actions.count("TAI_corporate_history_monthly_outcomes = yes") == 1
    assert "TAI_pc_industry_events." not in monthly_dispatch


def test_exact_milestone_start_dates_are_marked_for_reconstruction():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    current_year = _named_block(effects, "TAI_pc_industry_schedule_current_year_events")
    skipped_blocks = {}
    for match in re.finditer(r"(?m)^[ \t]*else_if\s*=\s*\{", current_year):
        block = _extract_block(current_year, match.start())
        marker = re.search(
            r"set_country_flag\s*=\s*" r"TAI_pc_industry_event_(\d{2})_startup_skipped",
            block,
        )
        if marker:
            event_number = int(marker.group(1))
            assert event_number not in skipped_blocks
            skipped_blocks[event_number] = block

    assert set(skipped_blocks) == set(range(1, len(MILESTONES) + 1))
    for event_number, _year, milestone, _delay in MILESTONES:
        block = skipped_blocks[event_number]
        assert f"has_start_date < {_script_day_after(milestone)}" in block
        assert (
            f"NOT = {{ has_country_flag = "
            f"TAI_pc_industry_event_{event_number:02d}_resolved }}" in block
        )


def test_startup_modes_monthly_terminal_and_scenarios_match_contract():
    common = COMMON_EFFECTS_PATH.read_text(encoding="utf-8")
    monthly_dispatch_text = MONTHLY_DISPATCH_PATH.read_text(encoding="utf-8")
    bootstrap = _named_block(
        monthly_dispatch_text, "corporate_history_country_bootstrap"
    )
    dispatch = _named_block(monthly_dispatch_text, "corporate_history_monthly_dispatch")
    monthly = _named_block(common, "TAI_corporate_history_monthly_outcomes")

    assert "corporate_history_enabled = yes" in dispatch
    assert "corporate_history_country_bootstrap = yes" in dispatch
    assert "corporate_history_initialize_midyear_recovery = yes" in dispatch
    assert "corporate_history_full_enabled = yes" in bootstrap
    assert "country_event = TAI_pc_industry_events.90" not in bootstrap
    assert "set_temp_variable = { pc_schedule_mode = 0 }" in bootstrap
    assert "TAI_pc_industry_schedule_current_year_events = yes" in bootstrap
    assert "TAI_pc_industry_reconstruct_history = yes" in bootstrap
    assert "corporate_history_full_enabled = yes" in monthly
    assert "corporate_history_outcomes_only_enabled = yes" in monthly
    assert (
        "NOT = { has_country_flag = TAI_pc_industry_reconstruct_complete }" in monthly
    )
    assert "TAI_pc_industry_monthly_driver = yes" in monthly

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    chain = next(
        item for item in manifest["chains"] if item["root"] == "TAI_pc_industry"
    )
    assert chain["terminal_marker"] == "TAI_pc_industry_reconstruct_complete"
    assert chain["terminal_date"] == "2013-06-30"
    assert chain["monthly_driver"] == "TAI_corporate_history_monthly_outcomes"
    assert set(chain["outcome_ideas"]) == set(OUTCOMES.values())
    assert chain["full_start_strategies"] == [
        "yearly_dispatcher",
        "current_year_scheduler",
        "reconstruction",
    ]
    assert chain["outcomes_only_strategy"] == "reconstruction"

    scripts = ScriptIndex.load(ROOT)
    for event_id, callers in chain["expected_callers"].items():
        expected_effects = {
            caller.removeprefix("effect:")
            for caller in callers
            if caller.startswith("effect:")
        }
        actual_effects = set(scripts.event_callers.get(event_id, ()))
        recovery_effects = {
            caller
            for caller in actual_effects
            if caller == "TAI_corporate_history_recover_midyear_events"
            or caller.startswith("TAI_pc_industry_recover_")
        }
        assert actual_effects == expected_effects | recovery_effects

    scenario_names = [
        item["name"]
        for item in scenarios["scenarios"]
        if item.get("chain") == "TAI_pc_industry"
    ]
    assert set(scenario_names) == {
        "tai_pc_industry_full_2000_complete_lifecycle",
        "tai_pc_industry_full_2007_january_start",
        "tai_pc_industry_outcomes_only_2014_terminal",
        "tai_pc_industry_disabled",
    }
    results, passed = run_scenarios(
        manifest,
        scenarios,
        scenario_names,
        scripts,
    )
    assert passed, results


def test_localisation_inventory_encoding_and_chain_ownership_are_clean():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    localisation = LOCALISATION_PATH.read_text(encoding="utf-8-sig")
    assert LOCALISATION_PATH.read_bytes().startswith(b"\xef\xbb\xbf")

    keys = set(re.findall(r"(?m)^ ([A-Za-z0-9_.]+):", localisation))
    referenced = set(
        re.findall(
            r"(?m)^\s*(?:title|desc|name|custom_effect_tooltip)\s*=\s*"
            r"(TAI_pc_industry_events\.[A-Za-z0-9_.]+)\s*$",
            events,
        )
    )
    for idea in OUTCOMES.values():
        referenced.add(idea)
        referenced.add(f"{idea}_desc")
    assert referenced <= keys
    assert len(referenced) == 124

    combined = events + "\n" + effects
    assert not re.search(r"TAI_(?:tsmc|foxconn)_[A-Za-z0-9_]+", combined)
    assert not re.search(
        r"TAI_(?:asrock|wistron|benq|pegatron)_[A-Za-z0-9_]+", combined
    )
    persistent_writes = re.findall(
        r"(?:set|clr)_country_flag\s*=\s*" r"(TAI_[A-Za-z0-9_]+)",
        combined,
    )
    allowed_prefixes = (
        "TAI_pc_industry",
        "TAI_asus",
        "TAI_gigabyte",
        "TAI_acer",
        "TAI_msi",
        "TAI_via",
    )
    assert persistent_writes
    assert all(flag.startswith(allowed_prefixes) for flag in persistent_writes)

    for idea in OUTCOMES.values():
        block = _idea_block(ideas, idea)
        assert "picture = " in block
        assert "allowed = { original_tag = TAI }" in block
