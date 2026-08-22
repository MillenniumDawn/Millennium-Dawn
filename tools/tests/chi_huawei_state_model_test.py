import json
import re
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = ROOT / "events" / "CHI_huawei_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "CHI_huawei_effects.txt"
LENOVO_EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "CHI_lenovo_effects.txt"
TRIGGERS_PATH = ROOT / "common" / "scripted_triggers" / "CHI_huawei_triggers.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "CHI_huawei_ideas.txt"
LOCALISATION_PATH = ROOT / "localisation" / "english" / "MD_focus_CHI_l_english.yml"
COMMON_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_effects.txt"
)
DISPATCH_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_dispatch_effects.txt"
)
ON_ACTIONS_PATH = (
    ROOT
    / "common"
    / "scripted_effects"
    / "00_corporate_history_monthly_dispatch_effects.txt"
)
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
DASHBOARD_PATH = ROOT / "common" / "decisions" / "CHI_corporate_systems_dashboard.txt"
DASHBOARD_CATEGORY_PATH = (
    ROOT / "common" / "decisions" / "categories" / "99_CHI_decision_categories.txt"
)
DASHBOARD_SCRIPTED_LOCALISATION_PATH = (
    ROOT
    / "common"
    / "scripted_localisation"
    / "CHI_corporate_systems_dashboard_scripted_localisation.txt"
)
CORPORATE_TRIGGERS_PATH = (
    ROOT / "common" / "scripted_triggers" / "MD_corporate_history_triggers.txt"
)

AXES = (
    "CHI_huawei_carrier_reach",
    "CHI_huawei_standards_leverage",
    "CHI_huawei_consumer_position",
    "CHI_huawei_silicon_autonomy",
    "CHI_huawei_software_ecosystem",
    "CHI_huawei_supply_resilience",
    "CHI_huawei_trusted_market_access",
)
INITIAL = (4, 2, 1, 2, 2, 3, 5)

ROUTES = (
    (
        ("CHI_huawei_global_rnd_network", (1, 1, 0, 0, 0, 0, 1)),
        ("CHI_huawei_domestic_network_priority", (1, 0, 0, 0, 0, 1, -1)),
        ("CHI_huawei_acquisition_led_expansion", (2, 0, 1, 0, 0, -1, 0)),
    ),
    (
        ("CHI_huawei_h3c_exit", (1, 0, 0, 0, 0, 1, 0)),
        ("CHI_huawei_h3c_control", (0, 0, 1, 0, 1, -1, 0)),
        ("CHI_huawei_open_enterprise_networking", (-1, 2, 0, 0, 0, 0, 1)),
    ),
    (
        ("CHI_huawei_symantec_joint_stack", (0, 1, 0, 0, 1, 0, 1)),
        ("CHI_huawei_carrier_pure_play", (1, 0, 0, 0, -1, 1, 0)),
        ("CHI_huawei_internal_security_storage", (0, 0, 0, 0, 2, 1, -1)),
    ),
    (
        ("CHI_huawei_lte_scale_leadership", (1, 1, 0, 0, 0, 0, 1)),
        ("CHI_huawei_lte_standards_licensing", (0, 2, 0, 0, 1, 0, 0)),
        ("CHI_huawei_lte_trusted_market_model", (1, 0, 0, 0, 0, -1, 2)),
    ),
    (
        ("CHI_huawei_integrated_ict_group", (0, 0, 0, 0, 1, 1, 0)),
        ("CHI_huawei_carrier_network_core", (2, 0, -1, 0, 0, 0, 0)),
        ("CHI_huawei_consumer_first_reorganization", (0, 0, 2, 0, 1, 0, -1)),
    ),
    (
        ("CHI_huawei_global_assurance_response", (0, 0, 0, 0, 0, 1, -2)),
        ("CHI_huawei_us_ringfence", (-1, 0, 0, 0, 0, 1, 1)),
        ("CHI_huawei_confrontational_substitution", (0, 0, 0, 1, 0, 2, -3)),
    ),
    (
        ("CHI_huawei_5g_moonshot", (1, 2, 0, 0, 0, 0, 0)),
        ("CHI_huawei_open_interoperability_5g", (0, 2, 0, 0, 1, 0, 1)),
        ("CHI_huawei_cloud_enterprise_priority", (0, -1, 1, 0, 2, 0, 0)),
    ),
    (
        ("CHI_huawei_premium_consumer_kirin", (0, 0, 3, 2, 0, 0, 0)),
        ("CHI_huawei_honor_mass_market", (0, 0, 4, 0, 0, -1, -1)),
        ("CHI_huawei_carrier_device_ecosystem", (1, 0, 2, 0, 1, 0, 0)),
    ),
    (
        ("CHI_huawei_device_cloud_chip_stack", (0, 0, 1, 1, 2, 0, 0)),
        ("CHI_huawei_open_cloud_partnership", (0, 0, 0, 0, 2, -1, 1)),
        ("CHI_huawei_mobile_ai_specialization", (0, -1, 1, 2, 0, 0, 0)),
    ),
    (
        ("CHI_huawei_full_stack_ai", (0, 1, 0, 1, 1, 0, 0)),
        ("CHI_huawei_separated_business_discipline", (0, 0, 0, 0, 0, 1, 1)),
        ("CHI_huawei_open_ai_ecosystem", (0, -1, 0, 0, 2, 0, 1)),
    ),
    (
        ("CHI_huawei_continuity_legal_defense", (0, 0, 0, 0, 0, 2, -3)),
        ("CHI_huawei_compliance_settlement", (0, -1, 0, -1, 0, 0, 2)),
        ("CHI_huawei_domestic_market_retreat", (-2, 0, 0, 1, 0, 2, -2)),
    ),
    (
        ("CHI_huawei_harmony_hms_full_ecosystem", (0, 0, 1, 0, 2, 0, -1)),
        ("CHI_huawei_openharmony_federation", (0, 1, -1, 0, 2, 0, 1)),
        ("CHI_huawei_android_compatibility_bridge", (0, 0, 1, 0, 0, 0, 2)),
    ),
    (
        ("CHI_huawei_honor_divested_core_preserved", (0, 0, -2, 1, 0, 1, 0)),
        ("CHI_huawei_honor_retained_rationed", (0, 0, 1, -1, 0, -2, 0)),
        ("CHI_huawei_consumer_stack_spun_out", (0, 0, -1, 0, 1, 2, -1)),
    ),
    (
        ("CHI_huawei_mate60_full_stack_return", (0, 0, 2, 2, 0, 1, 0)),
        ("CHI_huawei_cautious_yield_ramp", (0, 0, -1, 1, 0, 2, 0)),
        ("CHI_huawei_ascend_cloud_redirection", (0, -1, 0, 2, 1, 0, 0)),
    ),
)

EXPECTED_OUTCOMES = {
    "AAAAAAAAAABBAA": ("global", (8, 8, 4, 8, 9, 8, 9)),
    "AAAAAAAAAAAABA": ("consumer", (8, 8, 9, 7, 9, 7, 2)),
    "AAAAAAACAAAAAB": ("carrier_cloud", (9, 8, 2, 6, 10, 10, 2)),
    "AAAAAAAAAAABAA": ("patent", (8, 9, 4, 9, 9, 10, 4)),
    "AAAAAAAAAAAAAA": ("sovereign", (8, 8, 6, 9, 9, 10, 2)),
    "AAAAAAAAAAAABB": ("fortress", (8, 8, 6, 6, 9, 8, 2)),
}

FOCUS_READS = {
    "CHI_Digital_Silk_Road",
    "CHI_huawei_zte_export",
    "CHI_hisilicon_kirin",
    "CHI_cloud_computing_triumvirate",
    "CHI_smic_advanced_node",
    "CHI_domestic_eda",
    "CHI_smee_lithography",
    "CHI_hua_hong_mature_node",
    "CHI_sicarrier_euv",
    "CHI_mature_node_counter_offensive",
}

ONE_SHOTS = (
    (
        (None, None, ("CAT_internet_tech", "0.10"), None, False),
        (None, None, ("CAT_industry", "0.10"), None, False),
        ("-4.00", None, ("CAT_computing_tech", "0.15"), None, False),
    ),
    (
        ("2.00", None, None, None, False),
        ("-3.00", None, ("CAT_computing_tech", "0.15"), None, False),
        (None, None, ("CAT_internet_tech", "0.15"), None, False),
    ),
    (
        (None, None, ("CAT_encryption_tech", "0.10"), None, False),
        (None, None, ("CAT_industry", "0.10"), None, False),
        ("-4.00", None, ("CAT_encryption_tech", "0.15"), None, False),
    ),
    (
        (None, None, ("CAT_internet_tech", "0.10"), None, False),
        (None, 5, ("CAT_internet_tech", "0.15"), None, False),
        ("-3.00", None, None, ("CHI_huawei_security_scrutiny", 730), False),
    ),
    (
        (None, None, ("CAT_computing_tech", "0.10"), None, False),
        (None, None, ("CAT_internet_tech", "0.10"), None, False),
        ("-3.00", None, ("CAT_computing_tech", "0.15"), None, False),
    ),
    (
        (None, None, None, ("CHI_huawei_security_scrutiny", 1095), False),
        (None, None, None, ("CHI_huawei_security_scrutiny", 730), False),
        (
            None,
            None,
            ("CAT_encryption_tech", "0.10"),
            ("CHI_huawei_security_scrutiny", 1460),
            False,
        ),
    ),
    (
        ("-4.00", None, ("CAT_internet_tech", "0.15"), None, False),
        (None, 5, ("CAT_internet_tech", "0.10"), None, False),
        (None, None, ("CAT_computing_tech", "0.15"), None, False),
    ),
    (
        (None, None, ("CAT_microchips", "0.15"), None, False),
        ("2.00", None, None, None, False),
        (None, None, ("CAT_computing_tech", "0.10"), None, False),
    ),
    (
        (None, None, ("CAT_ai", "0.10"), None, False),
        (None, None, ("CAT_computing_tech", "0.15"), None, False),
        (None, None, ("CAT_ai", "0.15"), None, False),
    ),
    (
        (None, None, ("CAT_ai", "0.15"), None, True),
        (None, 5, ("CAT_computing_tech", "0.10"), None, False),
        (None, None, ("CAT_internet_tech", "0.15"), None, False),
    ),
    (
        (None, None, None, ("CHI_huawei_entity_list_shock", 1825), False),
        ("-3.00", -10, None, ("CHI_huawei_entity_list_shock", 730), False),
        (
            None,
            None,
            ("CAT_microchips", "0.15"),
            ("CHI_huawei_entity_list_shock", 1460),
            False,
        ),
    ),
    (
        (
            None,
            None,
            ("CAT_computing_tech", "0.15"),
            ("CHI_huawei_ecosystem_migration_burden", 1460),
            False,
        ),
        (
            None,
            None,
            ("CAT_internet_tech", "0.15"),
            ("CHI_huawei_ecosystem_migration_burden", 730),
            False,
        ),
        (
            None,
            None,
            ("CAT_internet_tech", "0.10"),
            ("CHI_huawei_ecosystem_migration_burden", 365),
            False,
        ),
    ),
    (
        ("1.00", None, None, ("CHI_huawei_foundry_chokepoint", 1825), False),
        ("-2.00", None, None, ("CHI_huawei_foundry_chokepoint", 2555), False),
        ("2.00", None, None, ("CHI_huawei_foundry_chokepoint", 1095), False),
    ),
    (
        (
            None,
            None,
            ("CAT_microchips", "0.15"),
            ("CHI_huawei_domestic_yield_ramp", 1095),
            False,
        ),
        (
            None,
            None,
            ("CAT_microchips", "0.10"),
            ("CHI_huawei_domestic_yield_ramp", 730),
            False,
        ),
        (None, None, ("CAT_ai", "0.15"), None, True),
    ),
)


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


def _event_block(text: str, event_number: int) -> str:
    event_id = f"CHI_huawei_events.{event_number}"
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


def _first_indented_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^\t{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing {name} block"
    return _extract_block(text, match.start())


def _option_child_block(option: str, name: str) -> str:
    match = re.search(rf"(?m)^\t\t{re.escape(name)}\s*=\s*\{{", option)
    assert match, f"Missing option {name} block"
    return _extract_block(option, match.start())


def _idea_block(text: str, idea: str) -> str:
    match = re.search(rf"(?m)^\t\t{re.escape(idea)}\s*=\s*\{{", text)
    assert match, f"Missing idea {idea}"
    return _extract_block(text, match.start())


def _axis_writes(text: str) -> List[Tuple[str, int]]:
    return [
        (axis, int(value))
        for axis, value in re.findall(
            r"add_to_variable\s*=\s*\{\s*"
            r"(CHI_huawei_[A-Za-z0-9_]+)\s*=\s*(-?\d+)\s*\}",
            text,
        )
        if axis in AXES
    ]


def _apply_route(route: str) -> Tuple[int, ...]:
    state = list(INITIAL)
    for event_index, letter in enumerate(route):
        choice_index = ord(letter) - ord("A")
        delta = ROUTES[event_index][choice_index][1]
        state = [max(0, min(10, value + change)) for value, change in zip(state, delta)]
    return tuple(state)


def _resolve(state: Tuple[int, ...]) -> str:
    carrier, standards, consumer, silicon, software, resilience, trusted = state
    if carrier >= 8 and standards >= 8 and trusted >= 7:
        return "global"
    if consumer >= 8 and software >= 8:
        return "consumer"
    if carrier >= 9 and software >= 7 and silicon <= 6:
        return "carrier_cloud"
    if standards >= 9:
        return "patent"
    if silicon >= 7 and software >= 7 and resilience >= 6:
        return "sovereign"
    return "fortress"


def _one_shot(option: str):
    treasury_match = re.search(r"treasury_change\s*=\s*(-?\d+\.\d+)", option)
    political_match = re.search(r"add_political_power\s*=\s*(-?\d+)", option)
    research_match = re.search(
        r"add_tech_bonus\s*=\s*\{.*?bonus\s*=\s*(\d+\.\d+).*?"
        r"uses\s*=\s*1.*?category\s*=\s*([A-Za-z0-9_]+).*?\}",
        option,
        flags=re.DOTALL,
    )
    timed_match = re.search(
        r"add_timed_idea\s*=\s*\{\s*idea\s*=\s*([A-Za-z0-9_]+)\s+"
        r"days\s*=\s*(\d+)\s*\}",
        option,
    )
    research = (
        (research_match.group(2), research_match.group(1)) if research_match else None
    )
    timed = (timed_match.group(1), int(timed_match.group(2))) if timed_match else None
    return (
        treasury_match.group(1) if treasury_match else None,
        int(political_match.group(1)) if political_match else None,
        research,
        timed,
        "gpu_refresh_accelerator_demand = yes" in option,
    )


def test_initial_state_and_all_visible_routes_match_the_contract():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "CHI_huawei_initialize_state")

    for axis, value in zip(AXES, INITIAL):
        assert f"set_variable = {{ {axis} = {value} }}" in initialize

    for event_number, expected_routes in enumerate(ROUTES, start=1):
        event = _event_block(events, event_number)
        trigger = _first_indented_block(event, "trigger")
        options = _option_blocks(event)
        assert len(options) == 3
        assert "is_triggered_only = yes" in event
        assert "fire_only_once = yes" in event
        assert "original_tag = CHI" in trigger
        assert "NOT = { has_country_flag = collapsed_nation }" in trigger
        immediate = _first_indented_block(event, "immediate")
        assert "CHI_huawei_initialize_state = yes" in immediate
        assert (
            f"set_country_flag = CHI_corporate_history_midyear_huawei_events_"
            f"{event_number}_resolved" in immediate
        )
        sibling_flags = {route[0] for route in expected_routes}
        trigger_flags = set(
            re.findall(r"has_country_flag\s*=\s*(CHI_huawei_[A-Za-z0-9_]+)", trigger)
        )
        assert trigger_flags == sibling_flags

        for option_index, (option, (flag, delta)) in enumerate(
            zip(options, expected_routes)
        ):
            suffix = "abc"[option_index]
            option_key = f"CHI_huawei_events.{event_number}.{suffix}"
            option_flags = re.findall(
                r"set_country_flag\s*=\s*(CHI_huawei_[A-Za-z0-9_]+)", option
            )
            expected_writes = [
                (axis, change) for axis, change in zip(AXES, delta) if change
            ]
            assert option_flags == [flag]
            assert sorted(_axis_writes(option)) == sorted(expected_writes)
            assert option.count("CHI_huawei_clamp_state = yes") == 1
            assert "hidden_effect = {" in option
            assert f"name = {option_key}" in option
            assert f"custom_effect_tooltip = {option_key}_tt" in option
            assert f'{option_key} executed"' in option


def test_visible_one_shots_match_the_locked_balance_table():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    ordinary_options = []
    for event_number, expected_options in enumerate(ONE_SHOTS, start=1):
        options = _option_blocks(_event_block(events, event_number))
        ordinary_options.extend(options)
        assert [_one_shot(option) for option in options] == list(expected_options)
        for option, expected in zip(options, expected_options):
            treasury, political, research, timed_idea, gpu_refresh = expected
            assert len(re.findall(r"treasury_change\s*=", option)) == int(
                treasury is not None
            )
            assert len(re.findall(r"add_political_power\s*=", option)) == int(
                political is not None
            )
            assert len(re.findall(r"add_tech_bonus\s*=", option)) == int(
                research is not None
            )
            assert len(re.findall(r"add_timed_idea\s*=", option)) == int(
                timed_idea is not None
            )
            assert option.count("gpu_refresh_accelerator_demand = yes") == int(
                gpu_refresh
            )

    for forbidden in (
        "add_building_construction",
        "add_offsite_building",
        "add_research_slot",
        "complete_national_focus",
        "CHI_economy_",
        "internet_station",
        "country_event =",
        "add_opinion_modifier",
    ):
        assert forbidden not in "\n".join(ordinary_options)


def test_historical_steps_match_route_a_and_are_reward_free():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    historical_graph = []
    for event_number, routes in enumerate(ROUTES, start=1):
        block = _named_block(
            effects, f"CHI_huawei_apply_historical_step_{event_number}"
        )
        historical_graph.append(block)
        flag, delta = routes[0]
        route_flags = {route[0] for route in routes}
        assert re.findall(
            r"set_country_flag\s*=\s*(CHI_huawei_[A-Za-z0-9_]+)", block
        ) == [flag]
        assert (
            set(re.findall(r"has_country_flag\s*=\s*(CHI_huawei_[A-Za-z0-9_]+)", block))
            == route_flags
        )
        assert sorted(_axis_writes(block)) == sorted(
            (axis, change) for axis, change in zip(AXES, delta) if change
        )
        assert block.count("CHI_huawei_initialize_state = yes") == 1
        assert block.count("CHI_huawei_clamp_state = yes") == 1

    call_graph = historical_graph + [
        _named_block(effects, "CHI_huawei_initialize_state"),
        _named_block(effects, "CHI_huawei_clamp_state"),
        _named_block(effects, "CHI_huawei_apply_historical_step_15"),
        _named_block(effects, "CHI_huawei_reconstruct_history"),
        _named_block(effects, "CHI_huawei_resolve_capstone"),
    ]
    call_graph.extend(
        _named_block(effects, f"CHI_huawei_apply_{outcome}")
        for outcome in (
            "global_connectivity_federation",
            "consumer_ecosystem_power",
            "carrier_cloud_utility",
            "patent_standards_house",
            "sovereign_full_stack",
            "resilient_technology_fortress",
        )
    )
    call_graph.extend(
        _named_block(effects, name)
        for name in (
            "CHI_huawei_clear_era_ideas",
            "CHI_huawei_set_global_telecom_challenger",
            "CHI_huawei_set_integrated_ict_champion",
            "CHI_huawei_set_contested_technology_champion",
            "CHI_huawei_set_full_stack_return",
            "CHI_huawei_clear_capstone_ideas",
        )
    )
    graph = "\n".join(call_graph)
    for forbidden in (
        "modify_treasury_effect",
        "treasury_change",
        "add_political_power",
        "add_tech_bonus",
        "add_timed_idea",
        "gpu_refresh_accelerator_demand",
        "country_event =",
        "add_building_construction",
    ):
        assert forbidden not in graph

    assert _apply_route("A" * 14) == (8, 8, 6, 9, 9, 10, 2)


def test_capstone_routes_are_reachable_and_priority_resolved():
    for route, (outcome, expected_state) in EXPECTED_OUTCOMES.items():
        state = _apply_route(route)
        assert state == expected_state
        assert _resolve(state) == outcome

    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    resolver = _named_block(effects, "CHI_huawei_resolve_capstone")
    ordered_calls = (
        "CHI_huawei_apply_global_connectivity_federation",
        "CHI_huawei_apply_consumer_ecosystem_power",
        "CHI_huawei_apply_carrier_cloud_utility",
        "CHI_huawei_apply_patent_standards_house",
        "CHI_huawei_apply_sovereign_full_stack",
        "CHI_huawei_apply_resilient_technology_fortress",
    )
    positions = [resolver.index(call) for call in ordered_calls]
    assert positions == sorted(positions)


def test_scripted_capstone_thresholds_applicators_and_visible_priority():
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    qualifiers = {
        "global_connectivity_federation": (
            ("CHI_huawei_carrier_reach", "8", "greater_than_or_equals"),
            ("CHI_huawei_standards_leverage", "8", "greater_than_or_equals"),
            ("CHI_huawei_trusted_market_access", "7", "greater_than_or_equals"),
        ),
        "consumer_ecosystem_power": (
            ("CHI_huawei_consumer_position", "8", "greater_than_or_equals"),
            ("CHI_huawei_software_ecosystem", "8", "greater_than_or_equals"),
        ),
        "carrier_cloud_utility": (
            ("CHI_huawei_carrier_reach", "9", "greater_than_or_equals"),
            ("CHI_huawei_software_ecosystem", "7", "greater_than_or_equals"),
            ("CHI_huawei_silicon_autonomy", "6", "less_than_or_equals"),
        ),
        "patent_standards_house": (
            ("CHI_huawei_standards_leverage", "9", "greater_than_or_equals"),
        ),
        "sovereign_full_stack": (
            ("CHI_huawei_silicon_autonomy", "7", "greater_than_or_equals"),
            ("CHI_huawei_software_ecosystem", "7", "greater_than_or_equals"),
            ("CHI_huawei_supply_resilience", "6", "greater_than_or_equals"),
        ),
    }

    qualifier_names = []
    for outcome, expected_checks in qualifiers.items():
        qualifier = f"CHI_huawei_qualifies_{outcome}"
        qualifier_names.append(qualifier)
        block = _named_block(triggers, qualifier)
        checks = tuple(
            re.findall(
                r"check_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_]+)\s+"
                r"value\s*=\s*(\d+)\s+compare\s*=\s*([A-Za-z0-9_]+)\s*\}",
                block,
            )
        )
        assert checks == expected_checks

    any_threshold = _named_block(
        triggers, "CHI_huawei_qualifies_any_threshold_capstone"
    )
    assert set(
        re.findall(r"(CHI_huawei_qualifies_[A-Za-z0-9_]+)\s*=\s*yes", any_threshold)
    ) == set(qualifier_names)
    fallback = _named_block(
        triggers, "CHI_huawei_qualifies_resilient_technology_fortress"
    )
    assert "NOT = { CHI_huawei_qualifies_any_threshold_capstone = yes }" in fallback

    outcomes = tuple(qualifiers) + ("resilient_technology_fortress",)
    outcome_ideas = {f"CHI_huawei_{outcome}" for outcome in outcomes}
    has_capstone = _named_block(triggers, "CHI_huawei_has_capstone_outcome")
    assert (
        set(re.findall(r"has_idea\s*=\s*(CHI_huawei_[A-Za-z0-9_]+)", has_capstone))
        == outcome_ideas
    )
    for outcome in outcomes:
        idea = f"CHI_huawei_{outcome}"
        applicator = _named_block(effects, f"CHI_huawei_apply_{outcome}")
        assert applicator.count("CHI_huawei_clear_era_ideas = yes") == 1
        assert applicator.count("CHI_huawei_clear_capstone_ideas = yes") == 1
        assert re.findall(
            r"add_ideas\s*=\s*(CHI_huawei_[A-Za-z0-9_]+)", applicator
        ) == [idea]
        assert len(re.findall(rf"(?m)^\t\t{re.escape(idea)}\s*=\s*\{{", ideas)) == 1

    assert "CHI_huawei_capstone_resolved" not in effects
    assert "CHI_huawei_capstone_resolved" not in events

    capstone_event = _event_block(events, 15)
    assert "NOT = { CHI_huawei_has_capstone_outcome = yes }" in capstone_event
    options = _option_blocks(capstone_event)
    expected_option_suffixes = ("a", "b", "c", "d_option", "e_option", "f_option")
    expected_qualifiers = qualifier_names + [
        "CHI_huawei_qualifies_resilient_technology_fortress"
    ]
    for index, (option, suffix, qualifier, outcome) in enumerate(
        zip(options, expected_option_suffixes, expected_qualifiers, outcomes)
    ):
        assert f"name = CHI_huawei_events.15.{suffix}" in option
        assert f"trigger = {{ {qualifier} = yes }}" in option
        assert f"CHI_huawei_apply_{outcome} = yes" in option
        if 0 < index < 5:
            ai = _option_child_block(option, "ai_chance")
            assert set(qualifier_names[:index]).issubset(
                set(re.findall(r"CHI_huawei_qualifies_[A-Za-z0-9_]+", ai))
            )
            assert "factor = 0" in ai


def test_era_burden_and_capstone_ideas_match_locked_modifiers():
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    expected = {
        "CHI_huawei_global_telecom_challenger": {
            "offices_productivity": "0.03",
            "research_speed_factor": "0.01",
        },
        "CHI_huawei_integrated_ict_champion": {
            "offices_productivity": "0.05",
            "production_factory_efficiency_gain_factor": "0.03",
            "research_speed_factor": "0.02",
        },
        "CHI_huawei_contested_technology_champion": {
            "cyber_defense_rating_modifier": "2",
            "research_speed_factor": "0.03",
            "consumer_goods_factor": "0.01",
        },
        "CHI_huawei_full_stack_return": {
            "research_speed_factor": "0.04",
            "industry_chip_consumption_modifier": "-0.03",
            "production_factory_efficiency_gain_factor": "0.03",
        },
        "CHI_huawei_security_scrutiny": {
            "offices_productivity": "-0.03",
            "foreign_influence_defense_modifier": "-0.05",
        },
        "CHI_huawei_entity_list_shock": {
            "microchip_export_multiplier_modifier": "-0.10",
            "production_factory_max_efficiency_factor": "-0.03",
            "consumer_goods_factor": "0.01",
        },
        "CHI_huawei_ecosystem_migration_burden": {
            "offices_productivity": "-0.03",
            "civilian_chip_consumption_modifier": "0.05",
        },
        "CHI_huawei_foundry_chokepoint": {
            "industry_chip_consumption_modifier": "0.08",
            "microchip_export_multiplier_modifier": "-0.10",
            "production_factory_efficiency_gain_factor": "-0.05",
        },
        "CHI_huawei_domestic_yield_ramp": {
            "industry_chip_consumption_modifier": "0.04",
            "production_factory_max_efficiency_factor": "-0.02",
            "research_speed_factor": "0.02",
        },
        "CHI_huawei_global_connectivity_federation": {
            "offices_productivity": "0.06",
            "political_power_factor": "0.04",
            "foreign_influence_defense_modifier": "0.05",
        },
        "CHI_huawei_consumer_ecosystem_power": {
            "offices_productivity": "0.07",
            "microchip_export_multiplier_modifier": "0.06",
            "consumer_goods_factor": "-0.01",
        },
        "CHI_huawei_carrier_cloud_utility": {
            "offices_productivity": "0.05",
            "production_factory_efficiency_gain_factor": "0.05",
            "industry_chip_consumption_modifier": "-0.04",
        },
        "CHI_huawei_patent_standards_house": {
            "research_speed_factor": "0.05",
            "political_power_factor": "0.05",
            "microchip_export_multiplier_modifier": "0.04",
        },
        "CHI_huawei_sovereign_full_stack": {
            "research_speed_factor": "0.05",
            "cyber_defense_rating_modifier": "3",
            "civilian_chip_consumption_modifier": "-0.04",
            "industry_chip_consumption_modifier": "-0.04",
        },
        "CHI_huawei_resilient_technology_fortress": {
            "cyber_defense_rating_modifier": "4",
            "foreign_influence_defense_modifier": "0.10",
            "research_speed_factor": "0.03",
            "consumer_goods_factor": "0.02",
        },
    }

    for idea, expected_modifiers in expected.items():
        block = _idea_block(ideas, idea)
        modifiers = dict(
            re.findall(
                r"(?m)^\t\t\t\t([A-Za-z0-9_]+)\s*=\s*(-?\d+(?:\.\d+)?)$",
                block,
            )
        )
        assert modifiers == expected_modifiers
        assert re.search(r"(?m)^\t\t\tpicture\s*=\s*[A-Za-z0-9_]+$", block)
        assert "allowed = { original_tag = CHI }" in block
        assert "allowed_civil_war = { always = yes }" in block


def test_reconstruction_owns_the_only_completion_marker_write():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    completion_write = "set_country_flag = CHI_huawei_reconstruct_complete"
    initialize = _named_block(effects, "CHI_huawei_initialize_state")
    resolver = _named_block(effects, "CHI_huawei_resolve_capstone")
    reconstruction = _named_block(effects, "CHI_huawei_reconstruct_history")

    assert "NOT = { has_country_flag = CHI_huawei_state_initialized }" in initialize
    assert initialize.count("set_country_flag = CHI_huawei_state_initialized") == 1
    assert initialize.count("CHI_huawei_clamp_state = yes") == 1
    assert "NOT = { CHI_huawei_has_capstone_outcome = yes }" in resolver
    for event_number in range(1, 16):
        assert (
            reconstruction.count(
                f"CHI_huawei_apply_historical_step_{event_number} = yes"
            )
            == 1
        )
    assert effects.count(completion_write) == 1
    assert completion_write in reconstruction
    completion_branches = [
        block
        for match in re.finditer(r"(?m)^\t\tif\s*=\s*\{", reconstruction)
        if completion_write in (block := _extract_block(reconstruction, match.start()))
    ]
    assert len(completion_branches) == 1
    completion_branch = completion_branches[0]
    assert "date > 2026.3.31" in completion_branch
    assert "CHI_huawei_has_capstone_outcome = yes" in completion_branch
    assert (
        "NOT = { has_country_flag = CHI_huawei_reconstruct_complete }"
        in completion_branch
    )
    assert completion_write not in events


def test_dispatch_omits_2000_and_delivers_both_2019_events():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    dispatch = DISPATCH_PATH.read_text(encoding="utf-8")
    on_actions = ON_ACTIONS_PATH.read_text(encoding="utf-8")

    assert "CHI_corporate_trigger_year_2000" not in dispatch
    assert "CHI_corporate_trigger_year_2000" not in on_actions
    scheduler = _named_block(effects, "CHI_huawei_schedule_current_year_events")
    assert scheduler.count("id = CHI_huawei_events.1 ") == 1

    year_2019 = _named_block(dispatch, "CHI_corporate_trigger_year_2019")
    assert "id = CHI_huawei_events.11 days = 135" in year_2019
    assert "id = CHI_huawei_events.12 days = 220" in year_2019
    scheduler_2019 = [
        block
        for match in re.finditer(r"(?m)^[ \t]+if\s*=\s*\{", scheduler)
        if (block := _extract_block(scheduler, match.start())).count(
            "id = CHI_huawei_events."
        )
        == 1
    ]
    dispatch_2019 = [
        block
        for match in re.finditer(r"(?m)^[ \t]+if\s*=\s*\{", year_2019)
        if (block := _extract_block(year_2019, match.start())).count(
            "id = CHI_huawei_events."
        )
        == 1
    ]
    for event_number, delay, route_index in ((11, 135, 10), (12, 220, 11)):
        delivery = f"id = CHI_huawei_events.{event_number} days = {delay}"
        siblings = {route[0] for route in ROUTES[route_index]}
        for blocks in (scheduler_2019, dispatch_2019):
            matching = [block for block in blocks if delivery in block]
            assert len(matching) == 1
            assert (
                set(
                    re.findall(
                        r"has_country_flag\s*=\s*(CHI_huawei_[A-Za-z0-9_]+)",
                        matching[0],
                    )
                )
                - {"CHI_huawei_start_year_events_scheduled"}
                == siblings
            )


def test_huawei_and_lenovo_use_independent_monthly_completion_guards():
    common_effects = COMMON_EFFECTS_PATH.read_text(encoding="utf-8")
    monthly = _named_block(common_effects, "CHI_corporate_history_monthly_outcomes")

    assert "NOT = { has_country_flag = CHI_lenovo_reconstruct_complete }" in monthly
    assert "NOT = { has_country_flag = CHI_huawei_reconstruct_complete }" in monthly
    assert monthly.count("CHI_lenovo_reconstruct_history = yes") == 1
    assert monthly.count("CHI_huawei_reconstruct_history = yes") == 2
    assert (
        "CHI_lenovo_reconstruct_complete CHI_huawei_reconstruct_complete" not in monthly
    )


def test_lenovo_missing_usa_fallbacks_guard_foreign_checks():
    effects = LENOVO_EFFECTS_PATH.read_text(encoding="utf-8")
    guarded_fallback = re.compile(
        r"NOT = \{ country_exists = USA \}\s+"
        r"AND = \{\s+country_exists = USA\s+has_war_with = USA\s+\}\s+"
        r"AND = \{\s+country_exists = USA\s+"
        r"USA = \{ has_country_flag = collapsed_nation \}\s+\}"
    )

    assert len(guarded_fallback.findall(effects)) == 3
    assert effects.count("USA = { has_country_flag = collapsed_nation }") == 3


def test_dashboard_is_read_only_authoritative_and_off_gated():
    dashboard = DASHBOARD_PATH.read_text(encoding="utf-8")
    category_file = DASHBOARD_CATEGORY_PATH.read_text(encoding="utf-8")
    scripted_localisation = DASHBOARD_SCRIPTED_LOCALISATION_PATH.read_text(
        encoding="utf-8"
    )
    corporate_triggers = CORPORATE_TRIGGERS_PATH.read_text(encoding="utf-8")
    localisation = LOCALISATION_PATH.read_text(encoding="utf-8-sig")
    scorecard = _first_indented_block(
        dashboard, "CHI_corporate_systems_huawei_scorecard"
    )
    category = _named_block(category_file, "CHI_corporate_systems_dashboard_category")
    meaningful_state = _named_block(
        corporate_triggers, "CHI_corporate_systems_has_meaningful_state"
    )

    assert "cost = 0" in scorecard
    assert "visible = { CHI_corporate_systems_has_meaningful_state = yes }" in scorecard
    assert "tooltip = CHI_corporate_systems_read_only_tt" in scorecard
    assert "always = no" in scorecard
    assert "ai_will_do = { base = 0 }" in scorecard
    assert "corporate_history_enabled = yes" in category
    assert "NOT = { has_country_flag = collapsed_nation }" in category
    assert "has_country_flag = CHI_huawei_state_initialized" in meaningful_state
    assert "has_country_flag = CHI_huawei_reconstruct_complete" in meaningful_state
    for axis in AXES:
        assert f"[?{axis}|0] / 10" in localisation
    assert "[CHI_corporate_systems_huawei_era]" in localisation
    assert "[CHI_corporate_systems_huawei_outcome]" in localisation
    assert (
        "trigger = { CHI_huawei_has_capstone_outcome = yes }" in scripted_localisation
    )
    assert "CHI_huawei_capstone_resolved" not in scripted_localisation
    for idea in (
        "CHI_huawei_global_telecom_challenger",
        "CHI_huawei_integrated_ict_champion",
        "CHI_huawei_contested_technology_champion",
        "CHI_huawei_full_stack_return",
        "CHI_huawei_global_connectivity_federation",
        "CHI_huawei_consumer_ecosystem_power",
        "CHI_huawei_carrier_cloud_utility",
        "CHI_huawei_patent_standards_house",
        "CHI_huawei_sovereign_full_stack",
        "CHI_huawei_resilient_technology_fortress",
    ):
        assert f"has_idea = {idea}" in scripted_localisation
    for forbidden in ("set_variable", "set_country_flag", "add_ideas", "remove_ideas"):
        assert forbidden not in dashboard
        assert forbidden not in scripted_localisation


def test_startup_modes_and_full_terminal_grace_match_delivery_contract():
    common_effects = COMMON_EFFECTS_PATH.read_text(encoding="utf-8")
    dispatch_text = ON_ACTIONS_PATH.read_text(encoding="utf-8")
    bootstrap = _named_block(dispatch_text, "corporate_history_country_bootstrap")
    dispatch = _named_block(dispatch_text, "corporate_history_monthly_dispatch")
    chi = min(
        (
            block
            for match in re.finditer(r"(?m)^\tif\s*=\s*\{", bootstrap)
            if "original_tag = CHI"
            in (block := _extract_block(bootstrap, match.start()))
        ),
        key=len,
    )
    full = min(
        (
            block
            for match in re.finditer(r"(?m)^\t\tif\s*=\s*\{", chi)
            if "corporate_history_full_enabled = yes"
            in (block := _extract_block(chi, match.start()))
        ),
        key=len,
    )

    assert chi.index("CHI_huawei_reconstruct_history = yes") < chi.index(
        "corporate_history_full_enabled = yes"
    )
    assert "CHI_huawei_schedule_current_year_events = yes" in full
    assert "CHI_huawei_events.90" not in bootstrap
    assert "corporate_history_enabled = yes" in dispatch
    assert "corporate_history_country_bootstrap = yes" in dispatch
    assert "corporate_history_initialize_midyear_recovery = yes" in dispatch
    assert "corporate_history_recover_midyear_events = yes" in dispatch

    monthly = _named_block(common_effects, "CHI_corporate_history_monthly_outcomes")
    assert "date > 2026.4.30" in monthly
    assert monthly.count("CHI_huawei_reconstruct_history = yes") == 2


def test_event_ai_uses_only_the_selected_national_focus_context():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    focus_reads = set(
        re.findall(r"has_completed_focus\s*=\s*(CHI_[A-Za-z0-9_]+)", events)
    )
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(item for item in manifest["chains"] if item["root"] == "CHI_huawei")

    assert focus_reads == FOCUS_READS
    assert set(chain["allowed_reads"]) == FOCUS_READS

    for event_number in (4, 7):
        carrier = _option_blocks(_event_block(events, event_number))[0]
        assert "has_completed_focus = CHI_Digital_Silk_Road" in carrier
        assert "has_completed_focus = CHI_huawei_zte_export" in carrier
    assert "CHI_Digital_Silk_Road" not in _event_block(events, 1)

    for event_number in (8, 9):
        integration = _option_blocks(_event_block(events, event_number))[0]
        assert "has_completed_focus = CHI_hisilicon_kirin" in integration

    for event_number in (13, 14):
        autonomy, resilience = _option_blocks(_event_block(events, event_number))[:2]
        for focus in (
            "CHI_smic_advanced_node",
            "CHI_domestic_eda",
            "CHI_smee_lithography",
            "CHI_sicarrier_euv",
        ):
            assert f"has_completed_focus = {focus}" in autonomy
        for focus in (
            "CHI_hua_hong_mature_node",
            "CHI_mature_node_counter_offensive",
        ):
            assert f"has_completed_focus = {focus}" in resilience

    cloud_events = {
        event_number
        for event_number in range(1, 15)
        if "CHI_cloud_computing_triumvirate" in _event_block(events, event_number)
    }
    assert cloud_events == {7, 9, 10, 14}


def test_manifest_registers_the_huawei_tier_one_contract():
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(item for item in manifest["chains"] if item["root"] == "CHI_huawei")
    outcomes = {
        "CHI_huawei_global_connectivity_federation",
        "CHI_huawei_consumer_ecosystem_power",
        "CHI_huawei_carrier_cloud_utility",
        "CHI_huawei_patent_standards_house",
        "CHI_huawei_sovereign_full_stack",
        "CHI_huawei_resilient_technology_fortress",
    }

    assert chain["name"] == "Huawei"
    assert chain["tag"] == "CHI"
    assert chain["namespace"] == "CHI_huawei_events"
    assert chain["tier"] == 1
    assert chain["owned_prefixes"] == ["CHI_huawei"]
    assert set(chain["variables"]) == set(AXES)
    assert all(
        bounds == {"min": 0, "max": 10} for bounds in chain["variables"].values()
    )
    assert chain["requires_current_year_scheduler"] is True
    assert chain["allow_yearly_scheduler_duplicates"] is True
    assert chain["full_start_strategies"] == [
        "yearly_dispatcher",
        "current_year_scheduler",
        "reconstruction",
    ]
    assert chain["outcomes_only_strategy"] == "reconstruction"
    assert chain["monthly_driver"] == "CHI_corporate_history_monthly_outcomes"
    assert chain["terminal_marker"] == "CHI_huawei_reconstruct_complete"
    assert chain["terminal_date"] == "2026-03-31"
    assert set(chain["outcome_ideas"]) == outcomes
    assert chain["expected_callers"] == {}
    assert chain["effect_preview_policy"] == "explicit"
    assert chain["bridge_refresh_policy"] == "none"
    assert chain["ai_bankruptcy_exceptions"] == []
    assert chain["allowed_writes"] == []
    assert chain["dependency_order"] == []


def test_ai_has_expected_bases_and_bankruptcy_fallback():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    costly_options = {
        1: (2,),
        2: (1,),
        3: (2,),
        4: (2,),
        5: (2,),
        7: (0,),
        11: (1,),
        13: (1,),
    }

    for event_number in range(1, 15):
        options = _option_blocks(_event_block(events, event_number))
        assert len(options) == 3
        for option, expected_base in zip(options, (50, 30, 20)):
            assert f"base = {expected_base}" in option
        assert "factor = 10" in options[0]
        assert "is_historical_focus_on = yes" in options[0]
        for alternative in options[1:]:
            assert "factor = 0" in alternative
            assert "is_historical_focus_on = yes" in alternative
        for option_index in costly_options.get(event_number, ()):
            assert (
                "has_active_mission = bankruptcy_incoming_collapse"
                in options[option_index]
            )

    event_seven = _option_blocks(_event_block(events, 7))
    assert "has_active_mission = bankruptcy_incoming_collapse" in event_seven[0]
    assert (
        "NOT = { has_active_mission = bankruptcy_incoming_collapse }" in event_seven[1]
    )
    assert "factor = 2" in event_seven[1]
    assert (
        "NOT = { has_active_mission = bankruptcy_incoming_collapse }"
        not in event_seven[2]
    )

    event_thirteen_b = _option_blocks(_event_block(events, 13))[1]
    assert "factor = 0.25" in event_thirteen_b
    assert (
        "check_variable = { var = CHI_huawei_supply_resilience value = 4 compare = less_than_or_equals }"
        in event_thirteen_b
    )


def test_english_localisation_inventory_and_encoding():
    raw = LOCALISATION_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    localisation = raw.decode("utf-8-sig")
    assert localisation.startswith("l_english:")
    keys = re.findall(r"(?m)^ ([^:#\r\n]+):", localisation)
    key_counts = {key: keys.count(key) for key in set(keys)}

    events = EVENTS_PATH.read_text(encoding="utf-8")
    event_references = set(
        re.findall(
            r"(?:title|desc|name|custom_effect_tooltip)\s*=\s*"
            r"(CHI_huawei_events\.[A-Za-z0-9_.]+)",
            events,
        )
    )
    assert event_references
    for key in event_references:
        assert key_counts.get(key) == 1

    axes = {axis for axis in AXES}
    era_ideas = {
        "CHI_huawei_global_telecom_challenger",
        "CHI_huawei_integrated_ict_champion",
        "CHI_huawei_contested_technology_champion",
        "CHI_huawei_full_stack_return",
    }
    burdens = {
        "CHI_huawei_security_scrutiny",
        "CHI_huawei_entity_list_shock",
        "CHI_huawei_ecosystem_migration_burden",
        "CHI_huawei_foundry_chokepoint",
        "CHI_huawei_domestic_yield_ramp",
    }
    capstones = {
        "CHI_huawei_global_connectivity_federation",
        "CHI_huawei_consumer_ecosystem_power",
        "CHI_huawei_carrier_cloud_utility",
        "CHI_huawei_patent_standards_house",
        "CHI_huawei_sovereign_full_stack",
        "CHI_huawei_resilient_technology_fortress",
    }
    qualification_tooltips = {
        "CHI_huawei_qualifies_global_connectivity_federation",
        "CHI_huawei_qualifies_consumer_ecosystem_power",
        "CHI_huawei_qualifies_carrier_cloud_utility",
        "CHI_huawei_qualifies_patent_standards_house",
        "CHI_huawei_qualifies_sovereign_full_stack",
        "CHI_huawei_qualifies_resilient_technology_fortress",
    }
    dashboard_keys = {
        "CHI_corporate_systems_huawei_scorecard",
        "CHI_corporate_systems_huawei_scorecard_desc",
        "CHI_corporate_systems_huawei_era_global",
        "CHI_corporate_systems_huawei_era_integrated",
        "CHI_corporate_systems_huawei_era_contested",
        "CHI_corporate_systems_huawei_era_full_stack",
        "CHI_corporate_systems_huawei_era_capstone",
        "CHI_corporate_systems_huawei_era_pending",
        "CHI_corporate_systems_huawei_era_not_initialized",
        "CHI_corporate_systems_huawei_outcome_global",
        "CHI_corporate_systems_huawei_outcome_consumer",
        "CHI_corporate_systems_huawei_outcome_carrier_cloud",
        "CHI_corporate_systems_huawei_outcome_patent",
        "CHI_corporate_systems_huawei_outcome_sovereign",
        "CHI_corporate_systems_huawei_outcome_fortress",
        "CHI_corporate_systems_huawei_outcome_pending",
        "CHI_corporate_systems_huawei_outcome_not_initialized",
    }
    for key in axes | era_ideas | burdens | capstones:
        assert key_counts.get(key) == 1
        assert key_counts.get(f"{key}_desc") == 1
    for key in qualification_tooltips:
        assert key_counts.get(key) == 1
    for key in dashboard_keys:
        assert key_counts.get(key) == 1

    huawei_start = localisation.index("\n CHI_huawei_events.1.t:")
    huawei_block = localisation[huawei_start:]
    assert "—" not in huawei_block
    assert "…" not in huawei_block
