import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from simulate_corporate_history import ScriptIndex, run_scenarios

EVENTS_PATH = ROOT / "events" / "FRA_corporate_systems_events.txt"
NOKIA_EVENTS_PATH = ROOT / "events" / "FRA_nokia_response_events.txt"
EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "FRA_corporate_systems_effects.txt"
)
TRIGGERS_PATH = (
    ROOT / "common" / "scripted_triggers" / "FRA_corporate_systems_triggers.txt"
)
IDEAS_PATH = ROOT / "common" / "ideas" / "FRA_corporate_systems_ideas.txt"
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
FRA_ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "99_FRA_on_actions.txt"
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
SCENARIOS_PATH = ROOT / "tools" / "corporate_history_scenarios.json"
DASHBOARD_PATH = ROOT / "common" / "decisions" / "FRA_corporate_systems_dashboard.txt"

AXES = {
    "sov": "FRA_corporate_strategic_sovereignty",
    "eu": "FRA_corporate_european_integration",
    "tel": "FRA_corporate_telecom_capacity",
    "semi": "FRA_corporate_semiconductor_capacity",
    "dig": "FRA_corporate_digital_infrastructure",
    "alu": "FRA_corporate_alcatel_health",
    "st": "FRA_corporate_stmicroelectronics_health",
    "orange": "FRA_corporate_orange_health",
    "debt": "FRA_corporate_debt_pressure",
    "china": "FRA_corporate_chinese_vendor_dependency",
}
BASELINE = {
    "sov": "6",
    "eu": "5",
    "tel": "6",
    "semi": "6",
    "dig": "4",
    "alu": "6",
    "st": "6",
    "orange": "5",
    "debt": "2",
    "china": "0",
}
EVENT_ORDER = (
    20,
    1,
    21,
    2,
    11,
    10,
    22,
    23,
    24,
    3,
    12,
    13,
    4,
    14,
    15,
    5,
    16,
    6,
    25,
    26,
    7,
    17,
    27,
    28,
)
EXPECTED_ROUTES = {
    1: (
        ("alcatel_aggressive_restructuring", {"alu": "0.8", "debt": "-0.6"}),
        ("alcatel_strategic_rd_protection", {"sov": "0.4", "alu": "0.6"}),
        ("alcatel_hold_the_line", {"alu": "-1.0", "debt": "0.8"}),
    ),
    2: (
        ("alcatel_microelectronics_sold_to_st", {"alu": "0.3", "debt": "-0.3"}),
        ("alcatel_microelectronics_retained", {"sov": "0.3", "debt": "0.4"}),
        ("alcatel_microelectronics_external_sale", {"sov": "-0.4", "debt": "-0.5"}),
    ),
    3: (
        (
            "lucent_combination_approved",
            {"sov": "-0.4", "tel": "0.6", "alu": "0.7"},
        ),
        ("lucent_strategic_guarantees", {"sov": "-0.1", "alu": "0.5"}),
        (
            "lucent_combination_opposed",
            {"sov": "0.6", "tel": "-0.2", "alu": "-0.5"},
        ),
    ),
    4: (
        ("alcatel_integration_restructured", {"alu": "0.6", "debt": "-0.4"}),
        ("alcatel_french_rd_shielded", {"sov": "0.3", "alu": "0.3"}),
        ("alcatel_integration_delayed", {"alu": "-0.7", "debt": "0.5"}),
    ),
    5: (
        (
            "alcatel_secured_refinancing",
            {"sov": "-0.2", "alu": "0.6", "debt": "-0.8"},
        ),
        (
            "alcatel_state_financing",
            {"sov": "0.5", "alu": "0.8", "debt": "-0.6"},
        ),
        ("alcatel_fire_sale", {"tel": "-0.6", "alu": "0.3", "debt": "-1.1"}),
    ),
    6: (
        ("alcatel_shift_plan", {"tel": "0.8", "alu": "1.0", "debt": "-0.5"}),
        ("alcatel_national_champion", {"sov": "0.8", "alu": "0.7"}),
        ("alcatel_restructuring_rejected", {"alu": "-0.9", "debt": "0.6"}),
    ),
    7: (
        ("nokia_rd_commitments_enforced", {"sov": "0.4", "eu": "0.4"}),
        ("nokia_unrestricted_integration", {"sov": "-0.3", "alu": "0.4"}),
        (
            "nokia_exceptional_french_control",
            {"sov": "0.6", "eu": "-0.5", "alu": "-0.3"},
        ),
    ),
    10: (
        (
            "st_alcatel_microelectronics_acquired",
            {"sov": "0.2", "semi": "0.4", "st": "0.5"},
        ),
        ("st_alcatel_strategic_assets_acquired", {"semi": "0.2", "st": "0.3"}),
        ("st_alcatel_microelectronics_declined", {"st": "0.2"}),
    ),
    11: (
        ("crolles2_multinational_alliance", {"sov": "-0.1", "semi": "0.6"}),
        ("crolles2_french_led_program", {"sov": "0.5", "semi": "0.4"}),
        ("crolles2_capital_exposure_minimized", {"semi": "0.1", "st": "0.2"}),
    ),
    12: (
        (
            "crolles_selective_alliances",
            {"sov": "0.2", "semi": "0.3", "st": "0.3"},
        ),
        ("crolles_public_research", {"sov": "0.6", "semi": "0.5"}),
        ("crolles_leading_edge_retreat", {"semi": "-0.5", "st": "0.4"}),
    ),
    13: (
        (
            "st_nxp_wireless_consolidated",
            {"semi": "0.5", "st": "0.2", "debt": "0.3"},
        ),
        ("st_wireless_independent", {"sov": "0.3", "st": "-0.1"}),
        ("st_wireless_divested", {"semi": "-0.6", "st": "0.4"}),
    ),
    14: (
        ("st_ericsson_formed", {"eu": "0.5", "semi": "0.6", "debt": "0.7"}),
        (
            "st_ericsson_financial_limits",
            {"eu": "0.5", "semi": "0.4", "debt": "0.3"},
        ),
        ("st_ericsson_rejected", {"sov": "0.4", "eu": "-0.2", "semi": "-0.3"}),
    ),
    15: (
        ("nano2012_protected", {"sov": "0.4", "semi": "0.5", "st": "0.5"}),
        ("semiconductor_countercyclical_push", {"semi": "0.8"}),
        ("semiconductor_austerity", {"semi": "-0.3", "st": "0.6"}),
    ),
    16: (
        (
            "st_ericsson_orderly_exit",
            {"semi": "-0.5", "st": "0.8", "debt": "-1.0"},
        ),
        (
            "st_ericsson_technology_absorbed",
            {"sov": "0.4", "semi": "-0.2", "st": "0.3"},
        ),
        (
            "st_ericsson_continued",
            {"semi": "0.3", "st": "-0.7", "debt": "1.2"},
        ),
    ),
    17: (
        (
            "european_microelectronics_ipcei",
            {"sov": "0.6", "eu": "1.0", "semi": "0.8"},
        ),
        (
            "france_first_semiconductor_program",
            {"sov": "0.9", "eu": "-0.5", "semi": "0.6"},
        ),
        ("market_led_semiconductors", {"semi": "-0.2", "st": "0.2"}),
    ),
    20: (
        (
            "orange_acquired",
            {"dig": "0.8", "orange": "0.8", "debt": "1.2"},
        ),
        (
            "orange_smaller_mobile_strategy",
            {"dig": "0.4", "orange": "0.4", "debt": "0.4"},
        ),
        ("orange_acquisition_rejected", {"dig": "-0.7", "debt": "-0.4"}),
    ),
    21: (
        ("mobilcom_settlement", {"orange": "-0.4", "debt": "0.5"}),
        ("mobilcom_state_bridge", {"sov": "0.4", "debt": "0.2"}),
        ("mobilcom_liabilities_contested", {"orange": "-0.5", "debt": "-0.2"}),
    ),
    22: (
        ("ambition_ft_recapitalization", {"orange": "1.2", "debt": "-1.5"}),
        (
            "ambition_ft_state_rescue",
            {"sov": "0.5", "orange": "1.0", "debt": "-1.8"},
        ),
        ("ambition_ft_austerity", {"dig": "-0.6", "debt": "-1.0"}),
    ),
    23: (
        (
            "orange_state_minority",
            {"sov": "-0.5", "eu": "0.2", "orange": "0.3"},
        ),
        ("orange_public_majority", {"sov": "0.7"}),
        ("orange_deeper_privatization", {"sov": "-1.0", "orange": "0.5"}),
    ),
    24: (
        ("orange_competitive_convergence", {"dig": "0.8"}),
        (
            "orange_alcatel_procurement",
            {"sov": "0.4", "tel": "0.4", "dig": "0.6", "alu": "0.5"},
        ),
        ("orange_global_sourcing", {"sov": "-0.5", "dig": "1.0", "china": "2"}),
    ),
    25: (
        ("orange_unified_brand", {"dig": "0.1", "orange": "0.5"}),
        ("france_telecom_domestic_brand", {"sov": "0.2", "orange": "-0.3"}),
        ("orange_dual_brand", {"sov": "0.1", "dig": "0.2"}),
    ),
    26: (
        ("orange_fiber_investment", {"dig": "1.0"}),
        ("orange_strategic_fiber", {"sov": "0.3", "dig": "1.5"}),
        ("orange_fiber_deferred", {"dig": "-0.5", "orange": "0.2"}),
    ),
    27: (
        (
            "orange_5g_nokia_ericsson",
            {"sov": "0.5", "eu": "0.8", "dig": "0.6", "china": "-1"},
        ),
        (
            "orange_5g_huawei",
            {"sov": "-0.8", "dig": "0.8", "china": "5"},
        ),
        (
            "orange_5g_multivendor",
            {"sov": "0.1", "eu": "0.3", "dig": "0.5", "china": "-1"},
        ),
    ),
    28: (
        (
            "5g_restrictive_authorizations",
            {"sov": "0.6", "eu": "0.3", "china": "-3"},
        ),
        (
            "5g_long_term_huawei",
            {"sov": "-0.5", "dig": "0.4", "china": "2"},
        ),
        (
            "5g_rapid_diversification",
            {"sov": "0.8", "tel": "0.5", "china": "-4"},
        ),
    ),
}
ANNUAL_EVENTS = {
    2001: ((1, 59), (21, 151)),
    2002: ((2, 90), (11, 101), (10, 104), (22, 337)),
    2004: ((23, 250),),
    2005: ((24, 59),),
    2006: ((3, 333),),
    2007: ((12, 364),),
    2008: ((13, 100), (4, 244)),
    2009: ((14, 31), (15, 59)),
    2011: ((5, 151),),
    2012: ((16, 335),),
    2013: ((6, 169), (25, 181)),
    2015: ((26, 59),),
    2016: ((7, 3),),
    2018: ((17, 351),),
    2020: ((27, 30),),
}
TIMED_IDEAS = {
    "FRA_corporate_systems_telecom_crash_restructuring",
    "FRA_corporate_systems_merger_integration_costs",
    "FRA_corporate_systems_credit_refinancing_burden",
    "FRA_corporate_systems_shift_plan_restructuring",
    "FRA_corporate_systems_fab_underutilization",
    "FRA_corporate_systems_wireless_exit_costs",
    "FRA_corporate_systems_mobilcom_settlement_burden",
    "FRA_corporate_systems_ambition_ft_restructuring",
    "FRA_corporate_systems_vendor_replacement_burden",
}
CAPSTONE_IDEAS = (
    "FRA_corporate_systems_european_strategic_autonomy",
    "FRA_corporate_systems_french_national_champions",
    "FRA_corporate_systems_china_connected_infrastructure",
    "FRA_corporate_systems_globalized_technology_market",
    "FRA_corporate_systems_resilient_multivendor_network",
)


def _extract_block(text, brace_index):
    depth = 0
    quoted = False
    escaped = False
    for index in range(brace_index, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace_index + 1 : index]
    raise AssertionError("unbalanced scripted block")


def _named_block(text, name):
    match = re.search(rf"(?m)^[ \t]*{re.escape(name)}\s*=\s*\{{", text)
    assert match, name
    return _extract_block(text, text.index("{", match.start()))


def _child_blocks(text, name):
    pattern = re.compile(rf"(?m)^[ \t]*{re.escape(name)}\s*=\s*\{{")
    return [
        _extract_block(text, text.index("{", match.start()))
        for match in pattern.finditer(text)
    ]


def _event_block(text, event_id):
    match = re.search(rf"(?m)^\tid\s*=\s*{re.escape(event_id)}$", text)
    assert match, event_id
    start = text.rfind("country_event = {", 0, match.start())
    assert start >= 0
    return _extract_block(text, text.index("{", start))


def _state_deltas(block):
    pattern = re.compile(
        r"add_to_variable\s*=\s*\{\s*"
        r"(FRA_corporate_[A-Za-z0-9_]+)\s*=\s*(-?\d+(?:\.\d+)?)\s*\}"
    )
    return {variable: Decimal(value) for variable, value in pattern.findall(block)}


def _expected_deltas(short_deltas):
    return {AXES[name]: Decimal(value) for name, value in short_deltas.items()}


def _effect_definitions(text):
    return {
        match.group(1): _extract_block(text, text.index("{", match.start()))
        for match in re.finditer(r"(?m)^([A-Za-z0-9_]+)\s*=\s*\{", text)
    }


def _apply_path(adapter, picks):
    state = {name: Decimal(value) for name, value in BASELINE.items()}
    for name, value in adapter.items():
        state[name] += Decimal(value)
    for event_id in EVENT_ORDER:
        if event_id not in picks:
            continue
        short_deltas = EXPECTED_ROUTES[event_id][picks[event_id]][1]
        for name, value in short_deltas.items():
            state[name] = min(
                Decimal("10"),
                max(Decimal("0"), state[name] + Decimal(value)),
            )
    return state


def _outcome(state):
    if (
        state["eu"] >= 8
        and state["tel"] >= 7
        and state["semi"] >= 7
        and state["china"] <= 4
    ):
        return "european"
    if (
        state["sov"] >= 8
        and state["tel"] >= 6
        and state["semi"] >= 6
        and state["debt"] <= 5
    ):
        return "french"
    if state["dig"] >= 7 and state["china"] >= 7:
        return "china"
    if (
        state["sov"] <= 4
        and state["dig"] >= 7
        and state["orange"] >= 6
        and state["st"] >= 6
    ):
        return "globalized"
    return "resilient"


def test_state_matrix_baseline_clamps_and_historical_defaults():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "FRA_corporate_systems_initialize_state")
    clamp = _named_block(effects, "FRA_corporate_systems_clamp_state")

    for short_name, variable in AXES.items():
        assert f"set_variable = {{ {variable} = {BASELINE[short_name]} }}" in initialize
        assert f"set_temp_variable = {{ corp_value = {variable} }}" in clamp
        assert f"set_variable = {{ {variable} = corp_value }}" in clamp
    assert initialize.count("set_variable = {") == 10
    assert clamp.count("corporate_history_clamp_value = yes") == 10

    for event_id, routes in EXPECTED_ROUTES.items():
        for suffix, expected in routes:
            effect = _named_block(effects, f"FRA_corporate_systems_apply_{suffix}")
            assert _state_deltas(effect) == _expected_deltas(expected)
            assert f"set_country_flag = FRA_corporate_systems_{suffix}" in effect
            assert "FRA_corporate_systems_initialize_state = yes" in effect
            assert effect.rfind("FRA_corporate_systems_clamp_state = yes") > max(
                (effect.rfind(variable) for variable in _expected_deltas(expected)),
                default=-1,
            )

    historical_ids = tuple(event_id for event_id in EXPECTED_ROUTES if event_id != 28)
    for event_id in historical_ids:
        historical = _named_block(
            effects, f"FRA_corporate_systems_apply_historical_step_{event_id}"
        )
        default_suffix, expected = EXPECTED_ROUTES[event_id][0]
        assert _state_deltas(historical) == _expected_deltas(expected)
        assert (
            f"set_country_flag = FRA_corporate_systems_{default_suffix}" in historical
        )
        assert "FRA_corporate_systems_clamp_state = yes" in historical
        for reward in (
            "add_political_power",
            "add_stability",
            "add_tech_bonus",
            "add_timed_idea",
        ):
            assert reward not in historical
    assert "FRA_corporate_systems_apply_historical_step_28" not in effects


def test_reconstruction_is_reward_free_ordered_and_terminal():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    definitions = _effect_definitions(effects)
    reachable = set()
    pending = ["FRA_corporate_systems_reconstruct_history"]
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        body = definitions[name]
        for called in re.findall(
            r"\b(FRA_corporate_systems_[A-Za-z0-9_]+)\s*=\s*yes", body
        ):
            if called in definitions:
                pending.append(called)

    reward_free_body = "\n".join(definitions[name] for name in sorted(reachable))
    for reward in (
        "add_political_power",
        "add_stability",
        "add_tech_bonus",
        "add_timed_idea",
    ):
        assert reward not in reward_free_body

    reconstruct = definitions["FRA_corporate_systems_reconstruct_history"]
    ordered = (
        "apply_historical_step_2",
        "apply_historical_step_11",
        "apply_historical_step_10",
    )
    assert [reconstruct.index(name) for name in ordered] == sorted(
        reconstruct.index(name) for name in ordered
    )
    assert (
        "date > 2008.7.31 } FRA_corporate_systems_apply_historical_step_13 = yes"
        in reconstruct
    )
    assert "date > 2020.7.22" in reconstruct
    assert (
        "set_country_flag = FRA_corporate_systems_reconstruct_complete" in reconstruct
    )

    complete = definitions["FRA_corporate_systems_complete_terminal_state"]
    assert "date > 2020.7.22" in complete
    assert "FRA_corporate_systems_5g_route_terminal_ready = yes" in complete
    assert "FRA_corporate_systems_resolve_capstone = yes" in complete
    assert "set_country_flag = FRA_corporate_systems_reconstruct_complete" in complete


def test_all_capstones_are_reachable_with_priority_and_terminal_fallbacks():
    all_a = {event_id: 0 for event_id in EXPECTED_ROUTES if event_id != 28}
    french = {
        **all_a,
        3: 2,
        6: 1,
        7: 2,
        11: 1,
        17: 1,
        23: 1,
        24: 1,
        26: 1,
        27: 2,
    }
    china = {
        **all_a,
        2: 2,
        7: 2,
        10: 2,
        14: 1,
        17: 2,
        23: 2,
        24: 2,
        25: 2,
        26: 1,
        27: 1,
        28: 1,
    }
    globalized = {
        **all_a,
        2: 2,
        7: 1,
        10: 2,
        12: 2,
        13: 2,
        14: 1,
        15: 2,
        17: 2,
        23: 2,
        24: 2,
        25: 2,
        26: 1,
        27: 2,
    }
    fallback = {
        **all_a,
        1: 1,
        2: 2,
        3: 1,
        4: 1,
        6: 1,
        7: 1,
        10: 2,
        11: 2,
        12: 2,
        13: 1,
        14: 1,
        15: 2,
        17: 2,
        20: 2,
        21: 2,
        22: 2,
        23: 1,
        25: 1,
        26: 2,
    }
    fallback.pop(27)
    adapters = {
        "enhanced": {"sov": "-0.4", "eu": "1.0", "tel": "0.8"},
        "acceptance": {"sov": "-0.8", "eu": "0.8"},
    }
    paths = {
        "european": (adapters["enhanced"], all_a),
        "french": (adapters["enhanced"], french),
        "china": (adapters["acceptance"], china),
        "globalized": (adapters["acceptance"], globalized),
        "resilient": (adapters["acceptance"], fallback),
    }

    states = {
        expected: _apply_path(adapter, picks)
        for expected, (adapter, picks) in paths.items()
    }
    assert {expected: _outcome(state) for expected, state in states.items()} == {
        expected: expected for expected in paths
    }
    assert states["resilient"]["dig"] < Decimal("4.5")

    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    thresholds = {
        "qualifies_european_strategic_autonomy": (
            ("FRA_corporate_european_integration", "8", "greater_than_or_equals"),
            ("FRA_corporate_telecom_capacity", "7", "greater_than_or_equals"),
            ("FRA_corporate_semiconductor_capacity", "7", "greater_than_or_equals"),
            ("FRA_corporate_chinese_vendor_dependency", "4", "less_than_or_equals"),
        ),
        "qualifies_french_national_champions": (
            ("FRA_corporate_strategic_sovereignty", "8", "greater_than_or_equals"),
            ("FRA_corporate_telecom_capacity", "6", "greater_than_or_equals"),
            ("FRA_corporate_semiconductor_capacity", "6", "greater_than_or_equals"),
            ("FRA_corporate_debt_pressure", "5", "less_than_or_equals"),
        ),
        "qualifies_china_connected_infrastructure": (
            ("FRA_corporate_digital_infrastructure", "7", "greater_than_or_equals"),
            ("FRA_corporate_chinese_vendor_dependency", "7", "greater_than_or_equals"),
        ),
        "qualifies_globalized_technology_market": (
            ("FRA_corporate_strategic_sovereignty", "4", "less_than_or_equals"),
            ("FRA_corporate_digital_infrastructure", "7", "greater_than_or_equals"),
            ("FRA_corporate_orange_health", "6", "greater_than_or_equals"),
            ("FRA_corporate_stmicroelectronics_health", "6", "greater_than_or_equals"),
        ),
    }
    for trigger_name, comparisons in thresholds.items():
        block = _named_block(triggers, f"FRA_corporate_systems_{trigger_name}")
        for variable, value, comparison in comparisons:
            assert (
                f"check_variable = {{ var = {variable} value = {value} "
                f"compare = {comparison} }}" in block
            )

    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    resolver = _named_block(effects, "FRA_corporate_systems_resolve_capstone")
    positions = [
        resolver.index(f"FRA_corporate_systems_apply_{suffix} = yes")
        for suffix in (
            "european_strategic_autonomy",
            "french_national_champions",
            "china_connected_infrastructure",
            "globalized_technology_market",
            "resilient_multivendor_network",
        )
    ]
    assert positions == sorted(positions)

    terminal_ready = _named_block(
        triggers, "FRA_corporate_systems_5g_route_terminal_ready"
    )
    assert "NOT = { FRA_corporate_systems_orange_operational = yes }" in terminal_ready
    assert "value = 4.5 compare = less_than" in terminal_ready
    assert "FRA_corporate_systems_huawei_authorization_resolved = yes" in terminal_ready


def test_event_surface_ai_fallback_and_atomic_route_contract():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    visible_ids = tuple(EXPECTED_ROUTES)
    assert events.count("country_event = {") == 24

    gated_options = 0
    for event_id in visible_ids:
        event = _event_block(events, f"FRA_corporate_systems_events.{event_id}")
        assert "is_triggered_only = yes" in event
        trigger = _child_blocks(event, "trigger")[0]
        assert "corporate_history_full_enabled = yes" in trigger
        assert "original_tag = FRA" in trigger
        assert "NOT = { has_country_flag = collapsed_nation }" in trigger
        assert f"FRA_corporate_systems_event_{event_id}_eligible = yes" in trigger
        assert (
            f"immediate = {{ FRA_corporate_systems_mark_event_{event_id}_delivered = yes }}"
            in event
        )
        options = _child_blocks(event, "option")
        assert len(options) == 3
        for option, base, (suffix, _deltas) in zip(
            options, (50, 30, 20), EXPECTED_ROUTES[event_id]
        ):
            assert f"ai_chance = {{ base = {base} }}" in option
            assert f"FRA_corporate_systems_apply_{suffix} = yes" in option
            gated_options += len(_child_blocks(option, "trigger"))
        assert not _child_blocks(options[2], "trigger")
    assert gated_options == 7

    event_10 = _child_blocks(
        _event_block(events, "FRA_corporate_systems_events.10"), "option"
    )
    for option in event_10[:2]:
        assert (
            "has_country_flag = FRA_corporate_systems_alcatel_microelectronics_sold_to_st"
            in option
        )
    event_14 = _child_blocks(
        _event_block(events, "FRA_corporate_systems_events.14"), "option"
    )
    assert "country_exists = SWE" in event_14[0]
    assert "FRA_corporate_systems_st_nxp_wireless_consolidated" in event_14[0]
    assert "country_exists = SWE" in event_14[1]
    event_24_b = _child_blocks(
        _event_block(events, "FRA_corporate_systems_events.24"), "option"
    )[1]
    assert "FRA_corporate_systems_alcatel_operational = yes" in event_24_b
    event_27 = _child_blocks(
        _event_block(events, "FRA_corporate_systems_events.27"), "option"
    )
    assert "country_exists = FIN" in event_27[0]
    assert "country_exists = SWE" in event_27[0]
    assert "country_exists = CHI" in event_27[1]


def test_nokia_bridge_is_idempotent_partner_safe_and_off_mode_safe():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    adapters = {
        "acceptance": {"sov": "-0.8", "eu": "0.8"},
        "enhanced_commitments": {"sov": "-0.4", "eu": "1.0", "tel": "0.8"},
        "block": {"sov": "0.8", "alu": "-0.8"},
    }
    for suffix, expected in adapters.items():
        effect = _named_block(effects, f"FRA_corporate_systems_record_nokia_{suffix}")
        outer = _child_blocks(effect, "if")[0]
        assert "corporate_history_enabled = yes" in outer
        assert "original_tag = FRA" in outer
        assert "NOT = { has_country_flag = collapsed_nation }" in outer
        assert "FRA_corporate_systems_initialize_state = yes" in outer
        assert _state_deltas(effect) == _expected_deltas(expected)
        assert "FRA_corporate_systems_has_nokia_transaction_record = yes" in outer
        assert (
            "FRA_corporate_systems_initialize_state = yes"
            not in effect[: effect.index("if = {")]
        )
        assert not _state_deltas(effect[: effect.index("if = {")])

    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    offer = _named_block(triggers, "FRA_corporate_systems_nokia_offer_eligible")
    assert "FRA_corporate_systems_alcatel_operational = yes" in offer
    assert "country_exists = FIN" in offer
    assert "FRA_corporate_systems_has_nokia_transaction_record = yes" in offer
    insolvency = _named_block(triggers, "FRA_corporate_systems_alcatel_insolvent")
    assert "value = 0 compare = less_than_or_equals" in insolvency
    operational = _named_block(triggers, "FRA_corporate_systems_alcatel_operational")
    assert "value = 0 compare = greater_than" in operational

    bridge_event = NOKIA_EVENTS_PATH.read_text(encoding="utf-8")
    event = _event_block(bridge_event, "FRA_nokia_response_events.1")
    assert (
        "NOT = { has_country_flag = FRA_corporate_systems_state_initialized }" in event
    )
    assert "FRA_corporate_systems_nokia_offer_eligible = yes" in event
    for option, adapter, callback in zip(
        _child_blocks(event, "option"),
        (
            "record_nokia_acceptance",
            "record_nokia_enhanced_commitments",
            "record_nokia_block",
        ),
        ("FIN_nokia_events.95", "FIN_nokia_events.95", "FIN_nokia_events.96"),
    ):
        assert f"FRA_corporate_systems_{adapter} = yes" in option
        assert callback in option


def test_current_year_yearly_and_monthly_delivery_paths_are_exact():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    dispatch = DISPATCH_PATH.read_text(encoding="utf-8")
    on_actions = ON_ACTIONS_PATH.read_text(encoding="utf-8")
    scheduler = _named_block(
        effects, "FRA_corporate_systems_schedule_current_year_events"
    )
    recovery = _named_block(effects, "FRA_corporate_systems_recover_missing_events")

    current_year_events = {20: (2000, 121)}
    for year, events in ANNUAL_EVENTS.items():
        for event_id, days in events:
            current_year_events[event_id] = (year, days)
            wrapper = _named_block(dispatch, f"FRA_corporate_trigger_year_{year}")
            assert "country_exists = FRA" in wrapper
            assert "original_tag = FRA" in wrapper
            assert "NOT = { has_country_flag = collapsed_nation }" in wrapper
            assert (
                f"NOT = {{ FRA_corporate_systems_event_{event_id}_resolved = yes }}"
                in wrapper
            )
            assert (
                f"country_event = {{ id = FRA_corporate_systems_events.{event_id} "
                f"days = {days} }}" in wrapper
            )
        year_router = _named_block(
            on_actions, f"corporate_history_dispatch_year_{year}"
        )
        assert "original_tag = FRA" in year_router
        assert f"FRA_corporate_trigger_year_{year} = yes" in year_router

    for event_id, (year, days) in current_year_events.items():
        call = (
            f"country_event = {{ id = FRA_corporate_systems_events.{event_id} "
            f"days = {days} }}"
        )
        # The scheduler nests the chain gate and the scheduled-flag guard above
        # the per-year windows, so several enclosing `if` blocks contain the call.
        # The innermost one that still carries a start-date bound is the window.
        assert scheduler.count(call) == 1
        windows = [
            block
            for block in _child_blocks(scheduler, "if")
            if call in block and "has_start_date" in block
        ]
        assert windows
        window = min(windows, key=len)
        assert f"NOT = {{ has_start_date < {year}.1.1 }}" in window
        assert f"has_start_date < {year}.1.2" in window
        assert (
            f"NOT = {{ FRA_corporate_systems_event_{event_id}_resolved = yes }}"
            in window
        )

    for event_id in EXPECTED_ROUTES:
        recovery_blocks = [
            block
            for block in _child_blocks(recovery, "if")
            if f"FRA_corporate_systems_events.{event_id} days = 5" in block
        ]
        assert len(recovery_blocks) == 1
        block = recovery_blocks[0]
        assert (
            f"has_country_flag = FRA_corporate_systems_event_{event_id}_delivery_expected"
            in block
        )
        assert (
            f"NOT = {{ has_country_flag = FRA_corporate_systems_event_{event_id}_pending }}"
            in block
        )
        assert f"FRA_corporate_systems_event_{event_id}_eligible = yes" in block
        assert "days = 65" in block
        assert (
            f"country_event = {{ id = FRA_corporate_systems_events.{event_id} days = 5 }}"
            in block
        )
        marker = _named_block(
            effects, f"FRA_corporate_systems_mark_event_{event_id}_delivered"
        )
        assert (
            f"clr_country_flag = FRA_corporate_systems_event_{event_id}_delivery_expected"
            in marker
        )
        assert (
            f"clr_country_flag = FRA_corporate_systems_event_{event_id}_pending"
            in marker
        )

    assert "FRA_corporate_systems_events.28" not in scheduler
    huawei = _named_block(effects, "FRA_corporate_systems_apply_orange_5g_huawei")
    assert "FRA_corporate_systems_events.28 days = 174" in huawei


def test_startup_modes_monthly_recovery_and_dashboard_state_are_registered():
    common = COMMON_EFFECTS_PATH.read_text(encoding="utf-8")
    dispatch_text = ON_ACTIONS_PATH.read_text(encoding="utf-8")
    bootstrap = _named_block(dispatch_text, "corporate_history_country_bootstrap")
    fra = min(
        (
            block
            for block in _child_blocks(bootstrap, "if")
            if "original_tag = FRA" in block
            and "FRA_corporate_systems_reconstruct_history = yes" in block
        ),
        key=len,
    )
    bootstrap_calls = (
        "FRA_corporate_systems_initialize_state = yes",
        "FRA_corporate_systems_reconstruct_history = yes",
    )
    assert [fra.index(call) for call in bootstrap_calls] == sorted(
        fra.index(call) for call in bootstrap_calls
    )
    assert "FRA_corporate_systems_events.90" not in bootstrap
    dispatch = _named_block(dispatch_text, "corporate_history_monthly_dispatch")
    assert "corporate_history_enabled = yes" in dispatch
    assert "corporate_history_country_bootstrap = yes" in dispatch
    assert "corporate_history_initialize_midyear_recovery = yes" in dispatch
    assert "corporate_history_recover_midyear_events = yes" in dispatch

    monthly = _named_block(common, "FRA_corporate_history_monthly_outcomes")
    assert "corporate_history_outcomes_only_enabled = yes" in monthly
    assert "FRA_corporate_systems_reconstruct_history = yes" in monthly
    assert "corporate_history_full_enabled = yes" in monthly
    assert "FRA_corporate_systems_schedule_current_year_events = yes" in monthly
    assert "FRA_corporate_systems_sync_nokia_response = yes" in monthly
    assert "FRA_corporate_systems_recover_missing_events = yes" in monthly
    assert "FRA_corporate_systems_complete_terminal_state = yes" in monthly
    fra_on_actions = FRA_ON_ACTIONS_PATH.read_text(encoding="utf-8")
    assert "on_monthly_FRA" in fra_on_actions
    assert "FRA_corporate_history_monthly_outcomes = yes" in fra_on_actions

    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    meaningful = _named_block(triggers, "FRA_corporate_systems_has_meaningful_state")
    capstone = _named_block(triggers, "FRA_corporate_systems_has_capstone_outcome")
    assert "FRA_corporate_systems_state_initialized" in meaningful
    assert "FRA_corporate_systems_reconstruct_complete" in meaningful
    assert "FRA_corporate_systems_has_capstone_outcome = yes" in meaningful
    for idea in CAPSTONE_IDEAS:
        assert f"has_idea = {idea}" in capstone

    dashboard = DASHBOARD_PATH.read_text(encoding="utf-8")
    assert (
        dashboard.count(
            "visible = { FRA_corporate_systems_has_meaningful_state = yes }"
        )
        == 5
    )
    for forbidden in ("set_variable", "set_country_flag", "add_ideas", "remove_ideas"):
        assert forbidden not in dashboard

    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    for idea in TIMED_IDEAS | set(CAPSTONE_IDEAS):
        block = _named_block(ideas, idea)
        assert "picture = " in block
        assert "allowed = { original_tag = FRA }" in block
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    assert not re.search(
        r"set_country_flag\s*=\s*FRA_corporate_systems_[A-Za-z0-9_]*capstone",
        effects,
    )


def test_contract_callers_and_scenarios_match_the_live_scripts():
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    chain = next(
        item for item in manifest["chains"] if item["root"] == "FRA_corporate_systems"
    )

    assert chain["name"] == "France Corporate Systems"
    assert chain["tag"] == "FRA"
    assert chain["namespace"] == "FRA_corporate_systems_events"
    assert chain["tier"] == 1
    assert set(chain["variables"]) == set(AXES.values())
    assert all(
        bounds == {"min": 0, "max": 10} for bounds in chain["variables"].values()
    )
    assert chain["allowed_writes"] == []
    assert set(chain["allowed_reads"]) == {
        "FRA_nokia_alu_commitments_accepted",
        "FRA_nokia_alu_commitments_enhanced",
        "FRA_nokia_alu_transaction_blocked",
    }
    assert chain["dependency_order"] == ["FIN_nokia"]
    assert chain["terminal_marker"] == "FRA_corporate_systems_reconstruct_complete"
    assert chain["terminal_date"] == "2020-07-22"
    assert set(chain["outcome_ideas"]) == set(CAPSTONE_IDEAS)

    scripts = ScriptIndex.load(ROOT)
    for event_id, callers in chain["expected_callers"].items():
        expected_effects = {
            caller.removeprefix("effect:")
            for caller in callers
            if caller.startswith("effect:")
        }
        assert set(scripts.event_callers.get(event_id, ())) == expected_effects

    scenario_names = [
        item["name"]
        for item in scenarios["scenarios"]
        if item.get("chain") == "FRA_corporate_systems"
    ]
    assert set(scenario_names) == {
        "france_corporate_systems_full_2000_current_year",
        "france_corporate_systems_full_2020_current_year",
        "france_corporate_systems_outcomes_only_2021",
        "france_corporate_systems_disabled_2020",
    }
    results, passed = run_scenarios(
        manifest,
        scenarios,
        scenario_names,
        scripts,
    )
    assert passed, results
