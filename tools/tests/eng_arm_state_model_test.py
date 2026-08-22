import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = ROOT / "events" / "ENG_arm_holdings_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "ENG_arm_holdings_effects.txt"
TRIGGERS_PATH = ROOT / "common" / "scripted_triggers" / "ENG_arm_holdings_triggers.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "ENG_arm_holdings_ideas.txt"
LOCALISATION_PATH = ROOT / "localisation" / "english" / "MD_focus_ENG_l_english.yml"
COMMON_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_effects.txt"
)
DISPATCH_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_dispatch_effects.txt"
)
MONTHLY_DISPATCH_PATH = (
    ROOT
    / "common"
    / "scripted_effects"
    / "00_corporate_history_monthly_dispatch_effects.txt"
)
MONTHLY_ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "99_ENG_on_actions.txt"
CORPORATE_TRIGGERS_PATH = (
    ROOT / "common" / "scripted_triggers" / "MD_corporate_history_triggers.txt"
)
DASHBOARD_PATH = ROOT / "common" / "decisions" / "ENG_corporate_systems_dashboard.txt"
DASHBOARD_CATEGORY_PATH = (
    ROOT / "common" / "decisions" / "categories" / "99_ENG_decision_categories.txt"
)
DASHBOARD_LOC_PATH = (
    ROOT
    / "common"
    / "scripted_localisation"
    / "ENG_corporate_systems_dashboard_scripted_localisation.txt"
)
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
ENG_DYNAMIC_PATH = (
    ROOT / "common" / "dynamic_modifiers" / "99_ENG_dynamic_modifiers.txt"
)

AXES = {
    "ENG_arm_holdings_ecosystem_strength": 3,
    "ENG_arm_holdings_domestic_value_capture": 3,
    "ENG_arm_holdings_strategic_control": 1,
}

PICTURES = {
    1: "GFX_computer",
    2: "GFX_computer",
    3: "GFX_computer",
    4: "GFX_generic_library",
    5: "GFX_stock_market",
    6: "GFX_computer",
    7: "GFX_political_deal",
    8: "GFX_court",
    9: "GFX_politics_negotiations",
    10: "GFX_stock_market",
}

OWNERSHIP_FLAGS = (
    "ENG_arm_holdings_softbank_light",
    "ENG_arm_holdings_softbank_undertakings",
    "ENG_arm_holdings_british_consortium",
    "ENG_arm_holdings_golden_share",
    "ENG_arm_holdings_nvidia_control",
)

PROPOSAL_FLAGS = (
    "ENG_arm_holdings_nvidia_support",
    "ENG_arm_holdings_nvidia_conditions",
    "ENG_arm_holdings_nvidia_full_review",
    "ENG_arm_holdings_nvidia_rejection",
)

RESOLUTION_FLAGS = (
    "ENG_arm_holdings_nvidia_completed",
    "ENG_arm_holdings_nvidia_completed_with_remedies",
    "ENG_arm_holdings_nvidia_abandoned",
    "ENG_arm_holdings_nvidia_rejected",
)

CAPSTONES = (
    "ENG_arm_holdings_british_founded_global_platform",
    "ENG_arm_holdings_british_golden_share_settlement",
    "ENG_arm_holdings_sovereign_architecture_champion",
    "ENG_arm_holdings_nvidia_arm_compute_platform",
)


def _extract_block(text: str, brace_index: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace_index : index + 1]
    raise AssertionError("Unbalanced scripted block")


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing block {name}"
    return _extract_block(text, text.index("{", match.start()))


def _event_map(text: str) -> dict[int, str]:
    events = {}
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, text.index("{", match.start()))
        event_id = re.search(r"(?m)^\tid\s*=\s*ENG_arm_holdings_events\.(\d+)", block)
        assert event_id
        events[int(event_id.group(1))] = block
    return events


def _option_blocks(event: str) -> list[str]:
    return [
        _extract_block(event, event.index("{", match.start()))
        for match in re.finditer(r"(?m)^\toption\s*=\s*\{", event)
    ]


def _option(event: str, localisation_key: str) -> str:
    for option in _option_blocks(event):
        if re.search(rf"(?m)^\t\tname\s*=\s*{re.escape(localisation_key)}\s*$", option):
            return option
    raise AssertionError(f"Missing option {localisation_key}")


def _dynamic_backing_variables(text: str, modifier: str) -> set[str]:
    block = _named_block(text, modifier)
    return set(re.findall(r"(?m)^\s*[a-z0-9_]+\s*=\s*(ENG_[A-Za-z0-9_]+)\s*$", block))


def _assert_no_variable_writes(text: str, variables: set[str]) -> None:
    for variable in variables:
        escaped = re.escape(variable)
        assert not re.search(
            rf"(?:set|add_to|subtract_from|multiply|divide)_variable\s*=\s*"
            rf"\{{\s*{escaped}\s*=",
            text,
        )
        assert not re.search(
            rf"clamp_variable\s*=\s*\{{[^}}]*\bvar\s*=\s*{escaped}\b",
            text,
            re.S,
        )


def test_initialization_clamps_and_event_surface_are_exact():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    initialize = _named_block(effects, "ENG_arm_holdings_initialize_state")
    clamp = _named_block(effects, "ENG_arm_holdings_clamp_state")

    for variable, initial in AXES.items():
        assert f"set_variable = {{ {variable} = {initial} }}" in initialize
        assert f"set_temp_variable = {{ corp_value = {variable} }}" in clamp
        assert f"set_variable = {{ {variable} = corp_value }}" in clamp
    assert clamp.count("corporate_history_clamp_value = yes") == len(AXES)

    assert set(events) == set(range(1, 11))
    for event_number, picture in PICTURES.items():
        event = events[event_number]
        assert "is_triggered_only = yes" in event
        assert "hidden = yes" not in event
        assert f"picture = {picture}" in event
        assert f"title = ENG_arm_holdings_events.{event_number}.t" in event
        assert f"desc = ENG_arm_holdings_events.{event_number}.d" in event


def test_route_families_and_capstones_are_exclusive():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))

    clear_ownership = _named_block(effects, "ENG_arm_holdings_clear_ownership_route")
    clear_proposal = _named_block(
        effects, "ENG_arm_holdings_clear_nvidia_proposal_route"
    )
    clear_resolution = _named_block(effects, "ENG_arm_holdings_clear_nvidia_resolution")
    clear_terminal = _named_block(effects, "ENG_arm_holdings_clear_terminal_outcome")

    for flag in OWNERSHIP_FLAGS:
        assert f"clr_country_flag = {flag}" in clear_ownership
    for flag in PROPOSAL_FLAGS:
        assert f"clr_country_flag = {flag}" in clear_proposal
    for flag in RESOLUTION_FLAGS:
        assert f"clr_country_flag = {flag}" in clear_resolution
    for idea in CAPSTONES:
        assert idea in clear_terminal

    ownership_options = {
        "ENG_arm_holdings_events.5.a": "ENG_arm_holdings_softbank_light",
        "ENG_arm_holdings_events.5.b": "ENG_arm_holdings_softbank_undertakings",
        "ENG_arm_holdings_events.5.c": "ENG_arm_holdings_british_consortium",
        "ENG_arm_holdings_events.5.d_option": "ENG_arm_holdings_golden_share",
    }
    for key, flag in ownership_options.items():
        option = _option(events[5], key)
        assert "ENG_arm_holdings_clear_ownership_route = yes" in option
        assert f"set_country_flag = {flag}" in option

    proposal_options = {
        "ENG_arm_holdings_events.7.a": "ENG_arm_holdings_nvidia_support",
        "ENG_arm_holdings_events.7.b": "ENG_arm_holdings_nvidia_conditions",
        "ENG_arm_holdings_events.7.c": "ENG_arm_holdings_nvidia_full_review",
        "ENG_arm_holdings_events.7.d_option": "ENG_arm_holdings_nvidia_rejection",
    }
    for key, flag in proposal_options.items():
        option = _option(events[7], key)
        assert "ENG_arm_holdings_clear_nvidia_proposal_route = yes" in option
        assert f"set_country_flag = {flag}" in option

    applicators = {
        "ENG_arm_holdings_apply_british_founded_capstone": CAPSTONES[0],
        "ENG_arm_holdings_apply_golden_share_capstone": CAPSTONES[1],
        "ENG_arm_holdings_apply_sovereign_champion_capstone": CAPSTONES[2],
        "ENG_arm_holdings_apply_nvidia_control_capstone": CAPSTONES[3],
    }
    for effect_name, idea in applicators.items():
        block = _named_block(effects, effect_name)
        assert "ENG_arm_holdings_clear_terminal_outcome = yes" in block
        assert f"add_ideas = {idea}" in block


def test_rejection_cannot_complete_and_acquisition_suppresses_the_ipo():
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")

    rejection = _option(events[7], "ENG_arm_holdings_events.7.d_option")
    assert "set_country_flag = ENG_arm_holdings_nvidia_rejection" in rejection
    assert "set_country_flag = ENG_arm_holdings_event_08_resolved" in rejection
    assert "set_country_flag = ENG_arm_holdings_event_08_not_applicable" in rejection
    assert "ENG_arm_holdings_has_active_nvidia_proposal = yes" in events[8]
    active_proposal = _named_block(
        triggers, "ENG_arm_holdings_has_active_nvidia_proposal"
    )
    assert (
        "NOT = { has_country_flag = ENG_arm_holdings_nvidia_rejection }"
        in active_proposal
    )

    for key, required_route in (
        ("ENG_arm_holdings_events.9.a", "ENG_arm_holdings_nvidia_support"),
        ("ENG_arm_holdings_events.9.b", "ENG_arm_holdings_nvidia_conditions"),
    ):
        option = _option(events[9], key)
        trigger = _named_block(option, "trigger")
        assert f"has_country_flag = {required_route}" in trigger
        assert "ENG_arm_holdings_nvidia_rejection" not in trigger
        assert "set_country_flag = ENG_arm_holdings_event_10_resolved" in option
        assert "set_country_flag = ENG_arm_holdings_nvidia_control" in option
        assert "ENG_arm_holdings_apply_nvidia_control_capstone = yes" in option

    ipo_trigger = _named_block(events[10], "trigger")
    assert (
        "NOT = { has_country_flag = ENG_arm_holdings_event_10_resolved }" in ipo_trigger
    )
    assert (
        "NOT = { has_country_flag = ENG_arm_holdings_terminal_resolved }" in ipo_trigger
    )
    schedule_ipo = _named_block(effects, "ENG_arm_holdings_schedule_event_10")
    assert "NOT = { has_country_flag = ENG_arm_holdings_event_10_resolved }" in (
        schedule_ipo
    )
    assert "NOT = { has_country_flag = ENG_arm_holdings_terminal_resolved }" in (
        schedule_ipo
    )


def test_every_visible_event_has_a_no_cost_ai_fallback_and_spending_is_guarded():
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    for event_number in range(1, 11):
        options = _option_blocks(events[event_number])
        free_options = [
            option for option in options if "modify_treasury_effect = yes" not in option
        ]
        assert free_options
        assert any(
            int(re.search(r"\bbase\s*=\s*(\d+)", option).group(1)) >= 20
            for option in free_options
        )
        for option in options:
            if "modify_treasury_effect = yes" not in option:
                continue
            ai_chance = _named_block(option, "ai_chance")
            assert re.search(
                r"modifier\s*=\s*\{\s*factor\s*=\s*0\s+"
                r"has_active_mission\s*=\s*bankruptcy_incoming_collapse\s*\}",
                ai_chance,
            )


def test_dynamic_modifier_backing_state_and_existing_rewards_are_read_only():
    dynamic_text = ENG_DYNAMIC_PATH.read_text(encoding="utf-8")
    backing_variables = _dynamic_backing_variables(dynamic_text, "ENG_economy_modifier")
    assert len(backing_variables) >= 50
    assert "ENG_arm_holdings" not in dynamic_text

    chain_paths = (
        EVENTS_PATH,
        EFFECTS_PATH,
        TRIGGERS_PATH,
        IDEAS_PATH,
        DASHBOARD_PATH,
        DASHBOARD_LOC_PATH,
    )
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in chain_paths)
    _assert_no_variable_writes(corpus, backing_variables)
    for forbidden in (
        "add_dynamic_modifier",
        "remove_dynamic_modifier",
        "force_update_dynamic_modifier",
        "complete_national_focus",
        "uncomplete_national_focus",
        "add_building_construction",
        "set_building_level",
        "create_military_industrial_organization",
        "add_military_industrial_organization",
        "add_offsite_building",
    ):
        assert forbidden not in corpus


def test_dispatch_modes_dashboard_and_contract_are_wired():
    common = COMMON_EFFECTS_PATH.read_text(encoding="utf-8")
    dispatch = DISPATCH_PATH.read_text(encoding="utf-8")
    monthly_dispatch_text = MONTHLY_DISPATCH_PATH.read_text(encoding="utf-8")
    monthly_on_actions = MONTHLY_ON_ACTIONS_PATH.read_text(encoding="utf-8")
    dashboard = DASHBOARD_PATH.read_text(encoding="utf-8")
    category = DASHBOARD_CATEGORY_PATH.read_text(encoding="utf-8")
    dashboard_loc = DASHBOARD_LOC_PATH.read_text(encoding="utf-8")
    corporate_triggers = CORPORATE_TRIGGERS_PATH.read_text(encoding="utf-8")

    bootstrap = _named_block(
        monthly_dispatch_text, "corporate_history_country_bootstrap"
    )
    for call in (
        "ENG_arm_holdings_initialize_state = yes",
        "ENG_arm_holdings_reconstruct_history = yes",
    ):
        assert call in bootstrap
    assert "ENG_arm_holdings_events.90" not in bootstrap
    monthly_dispatch = _named_block(
        monthly_dispatch_text, "corporate_history_monthly_dispatch"
    )
    assert "corporate_history_country_bootstrap = yes" in monthly_dispatch
    assert "corporate_history_initialize_midyear_recovery = yes" in monthly_dispatch
    assert "corporate_history_recover_midyear_events = yes" in monthly_dispatch

    monthly = _named_block(common, "ENG_corporate_history_monthly_outcomes")
    assert "corporate_history_outcomes_only_enabled = yes" in monthly
    assert "ENG_arm_holdings_reconstruct_history = yes" in monthly
    assert "corporate_history_full_enabled = yes" in monthly
    assert "ENG_arm_holdings_monthly_driver = yes" in monthly
    assert "ENG_corporate_history_monthly_outcomes = yes" in monthly_on_actions

    schedule_years = {
        2: 2002,
        3: 2007,
        4: 2010,
        5: 2016,
        6: 2018,
        7: 2020,
        8: 2021,
        9: 2022,
        10: 2023,
    }
    for event_number, year in schedule_years.items():
        year_block = _named_block(dispatch, f"ENG_corporate_trigger_year_{year}")
        delivery = year_block
        if event_number == 2:
            assert "ENG_arm_holdings_dispatch_event_02 = yes" in year_block
            delivery += _named_block(dispatch, "ENG_arm_holdings_dispatch_event_02")
        assert f"ENG_arm_holdings_schedule_event_{event_number:02d} = yes" in delivery
        year_router = _named_block(
            monthly_dispatch_text, f"corporate_history_dispatch_year_{year}"
        )
        assert "original_tag = ENG" in year_router
        assert f"ENG_corporate_trigger_year_{year} = yes" in year_router

    category_block = _named_block(category, "ENG_corporate_systems_dashboard_category")
    assert "allowed = { original_tag = ENG }" in category_block
    assert "priority = 144" in category_block
    assert "visible_when_empty = yes" in category_block
    assert "corporate_history_enabled = yes" in category_block
    assert "NOT = { has_country_flag = collapsed_nation }" in category_block
    decision_ids = re.findall(
        r"(?m)^\t(ENG_corporate_systems_[a-z0-9_]+)\s*=\s*\{", dashboard
    )
    assert len(decision_ids) == 5
    for decision_id in decision_ids:
        decision = _named_block(dashboard, decision_id)
        assert "cost = 0" in decision
        assert "always = no" in decision
        assert "ai_will_do = { base = 0 }" in decision
        assert not re.search(
            r"\b(?:complete_effect|remove_effect|timeout_effect|cancel_effect)\s*=",
            decision,
        )
    for forbidden in ("set_variable", "set_country_flag", "add_ideas", "remove_ideas"):
        assert forbidden not in dashboard_loc
    assert "ENG_arm_holdings_state_initialized" in corporate_triggers
    assert "ENG_arm_holdings_terminal_resolved" in corporate_triggers

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(
        item for item in manifest["chains"] if item["root"] == "ENG_arm_holdings"
    )
    assert chain["name"] == "Arm Holdings"
    assert chain["tag"] == "ENG"
    assert chain["namespace"] == "ENG_arm_holdings_events"
    assert chain["tier"] == 1
    assert chain["variables"] == {variable: {"min": 0, "max": 10} for variable in AXES}
    assert set(chain["outcome_ideas"]) == set(CAPSTONES)
    assert chain["requires_current_year_scheduler"] is True
    assert chain["allow_yearly_scheduler_duplicates"] is True
    assert chain["full_start_strategies"] == [
        "yearly_dispatcher",
        "current_year_scheduler",
        "reconstruction",
    ]
    assert chain["outcomes_only_strategy"] == "reconstruction"
    assert chain["monthly_driver"] == "ENG_corporate_history_monthly_outcomes"
    assert chain["terminal_marker"] == "ENG_arm_holdings_reconstruct_complete"
    assert chain["terminal_date"] == "2023-09-14"
    assert chain["allowed_writes"] == []
    assert "ENG_arm_holdings_events.90" not in chain["expected_callers"]


def test_new_english_surface_contains_no_banned_dash_character():
    new_paths = (
        EVENTS_PATH,
        EFFECTS_PATH,
        TRIGGERS_PATH,
        IDEAS_PATH,
        DASHBOARD_PATH,
        DASHBOARD_CATEGORY_PATH,
        DASHBOARD_LOC_PATH,
    )
    for path in new_paths:
        assert "\u2014" not in path.read_text(encoding="utf-8")

    raw = LOCALISATION_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    localisation = raw.decode("utf-8-sig")
    new_lines = [
        line
        for line in localisation.splitlines()
        if "ENG_arm_holdings" in line or "ENG_corporate_systems_" in line
    ]
    assert new_lines
    assert "\u2014" not in "\n".join(new_lines)
