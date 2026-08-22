import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = ROOT / "events" / "UKR_strategic_industry_events.txt"
EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "UKR_strategic_industry_effects.txt"
)
TRIGGERS_PATH = (
    ROOT / "common" / "scripted_triggers" / "UKR_strategic_industry_triggers.txt"
)
IDEAS_PATH = ROOT / "common" / "ideas" / "UKR_strategic_industry_ideas.txt"
LOCALISATION_PATH = ROOT / "localisation" / "english" / "MD_focus_UKR_l_english.yml"
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
MONTHLY_ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "99_UKR_on_actions.txt"
CORPORATE_TRIGGERS_PATH = (
    ROOT / "common" / "scripted_triggers" / "MD_corporate_history_triggers.txt"
)
DASHBOARD_PATH = ROOT / "common" / "decisions" / "UKR_corporate_systems_dashboard.txt"
DASHBOARD_CATEGORY_PATH = (
    ROOT / "common" / "decisions" / "categories" / "99_UKR_decision_categories.txt"
)
DASHBOARD_LOC_PATH = (
    ROOT
    / "common"
    / "scripted_localisation"
    / "UKR_corporate_systems_dashboard_scripted_localisation.txt"
)
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
UKR_DYNAMIC_PATH = (
    ROOT / "common" / "dynamic_modifiers" / "99_UKR_dynamic_modifiers.txt"
)

AXES = {
    "UKR_strategic_industry_strategic_capacity": 4,
    "UKR_strategic_industry_post_soviet_exposure": 7,
    "UKR_strategic_industry_workforce_retention": 4,
    "UKR_strategic_industry_distributed_production": 0,
}

PICTURES = {
    1: "GFX_ukr_2000",
    2: "GFX_passenger_plane",
    3: "GFX_generic_factory",
    4: "GFX_news_missilesPointingUp",
    5: "GFX_trade_agreement",
    6: "GFX_raid_international_sanctions",
    7: "GFX_stock_market",
    8: "GFX_politics_negotiations",
    9: "GFX_ukr_army",
    10: "GFX_court",
    11: "GFX_broken_infrastructure",
    12: "GFX_generic_factory",
    13: "GFX_political_deal",
    14: "GFX_rheinmetall_event_picture",
    15: "GFX_eastern_europe",
}

GOVERNANCE_FLAGS = (
    "UKR_strategic_industry_governance_preserved",
    "UKR_strategic_industry_governance_corporatized",
    "UKR_strategic_industry_governance_managed_mixed",
    "UKR_strategic_industry_governance_fragmented_private",
    "UKR_strategic_industry_governance_neglected",
)

PARTNER_FLAGS = (
    "UKR_strategic_industry_partner_post_soviet",
    "UKR_strategic_industry_partner_western",
    "UKR_strategic_industry_partner_chinese",
    "UKR_strategic_industry_partner_multivector",
    "UKR_strategic_industry_partner_independent",
)

MOTOR_SICH_FLAGS = (
    "UKR_strategic_industry_motor_sich_state_control",
    "UKR_strategic_industry_motor_sich_domestic_private",
    "UKR_strategic_industry_motor_sich_chinese_control",
    "UKR_strategic_industry_motor_sich_security_seized",
    "UKR_strategic_industry_motor_sich_fragmented",
)

WARTIME_FLAGS = (
    "UKR_strategic_industry_wartime_priority_dispersed",
    "UKR_strategic_industry_wartime_priority_centralized",
    "UKR_strategic_industry_wartime_priority_allied_repair",
    "UKR_strategic_industry_wartime_priority_workforce_preservation",
)

CAPSTONES = (
    "UKR_strategic_industry_restored_aerospace_power",
    "UKR_strategic_industry_western_integrated_defense_industry",
    "UKR_strategic_industry_independent_distributed_industry",
    "UKR_strategic_industry_chinese_capital_corridor",
    "UKR_strategic_industry_renewed_post_soviet_integration",
    "UKR_strategic_industry_diminished_specialist_base",
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


def _smallest_block_containing(text: str, needle: str) -> str:
    candidates = []
    for match in re.finditer(r"\{", text):
        try:
            block = _extract_block(text, match.start())
        except AssertionError:
            continue
        if needle in block:
            candidates.append(block)
    assert candidates, f"Missing containing block for {needle}"
    return min(candidates, key=len)


def _event_map(text: str) -> dict[int, str]:
    events = {}
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, text.index("{", match.start()))
        event_id = re.search(
            r"(?m)^\tid\s*=\s*UKR_strategic_industry_events\.(\d+)", block
        )
        assert event_id
        events[int(event_id.group(1))] = block
    return events


def _option_blocks(event: str) -> list[str]:
    return [
        _extract_block(event, event.index("{", match.start()))
        for match in re.finditer(r"(?m)^\toption\s*=\s*\{", event)
    ]


def _dynamic_backing_variables(text: str, modifier: str) -> set[str]:
    block = _named_block(text, modifier)
    return set(re.findall(r"=\s*var:(UKR_[A-Za-z0-9_]+)\s*$", block, re.M))


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
    initialize = _named_block(effects, "UKR_strategic_industry_initialize_state")
    clamp = _named_block(effects, "UKR_strategic_industry_clamp_state")

    for variable, initial in AXES.items():
        assert f"set_variable = {{ {variable} = {initial} }}" in initialize
        assert f"set_temp_variable = {{ corp_value = {variable} }}" in clamp
        assert f"set_variable = {{ {variable} = corp_value }}" in clamp
    assert clamp.count("corporate_history_clamp_value = yes") == len(AXES)

    assert set(events) == set(range(1, 16))
    for event_number, picture in PICTURES.items():
        event = events[event_number]
        assert "is_triggered_only = yes" in event
        assert "hidden = yes" not in event
        assert f"picture = {picture}" in event
        assert f"title = UKR_strategic_industry_events.{event_number}.t" in event
        assert f"desc = UKR_strategic_industry_events.{event_number}.d" in event


def test_route_families_and_capstones_are_exclusive():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    families = (
        (
            GOVERNANCE_FLAGS,
            "UKR_strategic_industry_clear_governance",
        ),
        (PARTNER_FLAGS, "UKR_strategic_industry_clear_partner"),
        (
            MOTOR_SICH_FLAGS,
            "UKR_strategic_industry_clear_motor_sich_ownership",
        ),
        (WARTIME_FLAGS, "UKR_strategic_industry_clear_wartime_priority"),
    )

    for flags, clear_effect in families:
        clear = _named_block(effects, clear_effect)
        for flag in flags:
            assert f"clr_country_flag = {flag}" in clear

    for event_number in range(1, 16):
        for option in _option_blocks(events[event_number]):
            for flags, clear_effect in families:
                selected = {
                    flag for flag in flags if f"set_country_flag = {flag}" in option
                }
                if selected:
                    assert len(selected) == 1
                    assert f"{clear_effect} = yes" in option

    clear_terminal = _named_block(
        effects, "UKR_strategic_industry_clear_terminal_outcome"
    )
    for idea in CAPSTONES:
        assert idea in clear_terminal
    applicators = {
        "UKR_strategic_industry_apply_restored_aerospace_power": CAPSTONES[0],
        "UKR_strategic_industry_apply_western_integrated_defense_industry": CAPSTONES[
            1
        ],
        "UKR_strategic_industry_apply_independent_distributed_industry": CAPSTONES[2],
        "UKR_strategic_industry_apply_chinese_capital_corridor": CAPSTONES[3],
        "UKR_strategic_industry_apply_renewed_post_soviet_integration": CAPSTONES[4],
        "UKR_strategic_industry_apply_diminished_specialist_base": CAPSTONES[5],
    }
    for effect_name, idea in applicators.items():
        block = _named_block(effects, effect_name)
        assert "UKR_strategic_industry_clear_terminal_outcome = yes" in block
        assert f"add_ideas = {idea}" in block

    terminal_outcome = _named_block(
        triggers, "UKR_strategic_industry_terminal_outcome_present"
    )
    for idea in CAPSTONES:
        assert f"has_idea = {idea}" in terminal_outcome
    finalize = _named_block(effects, "UKR_strategic_industry_finalize_terminal_state")
    assert "set_country_flag = UKR_strategic_industry_event_15_resolved" in finalize


def test_rupture_and_war_are_state_led_and_cover_split_russian_tags():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))

    rupture = _named_block(triggers, "UKR_strategic_industry_russian_rupture_trigger")
    assert "any_enemy_country = { original_tag = SOV }" in rupture
    assert "has_country_flag = UKR_donbass_rise" in rupture
    assert "has_idea = UKR_civil_war" in rupture
    assert "is_subject_of = SOV" in rupture
    assert "is_owned_by = SOV" in rupture
    assert "is_controlled_by = SOV" in rupture

    qualifying_war = _named_block(
        triggers, "UKR_strategic_industry_qualifying_major_war_trigger"
    )
    assert "is_at_war" not in triggers
    assert "has_war = yes" in qualifying_war
    assert "any_enemy_country" in qualifying_war
    assert "original_tag = SOV" in qualifying_war
    assert "is_major = yes" in qualifying_war
    russian_war = _named_block(triggers, "UKR_strategic_industry_russian_war_trigger")
    assert "any_enemy_country = { original_tag = SOV }" in russian_war

    monthly = _named_block(effects, "UKR_strategic_industry_monthly_driver")
    rupture_delivery = _smallest_block_containing(
        monthly, "country_event = { id = UKR_strategic_industry_events.6 days = 1 }"
    )
    assert "UKR_strategic_industry_russian_rupture_trigger = yes" in rupture_delivery
    war_delivery = _smallest_block_containing(
        monthly, "country_event = { id = UKR_strategic_industry_events.9 days = 1 }"
    )
    assert "UKR_strategic_industry_event_09_resolved" in war_delivery
    assert "UKR_strategic_industry_event_09_pending" in war_delivery
    assert "months_at_war" not in effects + triggers

    relocation = _named_block(triggers, "UKR_strategic_industry_relocation_eligible")
    for state in (694, 698, 1087):
        assert f"controls_state = {state}" in relocation

    event_6 = events[6]
    assert event_6.index("UKR_strategic_industry_apply_rupture_shock = yes") < (
        event_6.index("\toption = {")
    )
    shock = _named_block(effects, "UKR_strategic_industry_apply_rupture_shock")
    assert "UKR_strategic_industry_post_soviet_exposure < 4" in shock
    assert "UKR_strategic_industry_post_soviet_exposure < 8" in shock
    assert "UKR_strategic_industry_strategic_capacity = -1" in shock
    assert "UKR_strategic_industry_strategic_capacity = -2" in shock
    assert "UKR_strategic_industry_strategic_capacity = -3" in shock
    for idea, days in (
        ("UKR_strategic_industry_rupture_mild", 365),
        ("UKR_strategic_industry_rupture_moderate", 730),
        ("UKR_strategic_industry_rupture_severe", 1095),
    ):
        assert f"add_timed_idea = {{ idea = {idea} days = {days} }}" in shock


def test_every_visible_event_has_a_no_cost_ai_fallback_and_spending_is_guarded():
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    for event_number in range(1, 16):
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
            treasury_change = re.search(
                r"treasury_change\s*=\s*(-?\d+(?:\.\d+)?)", option
            )
            assert treasury_change
            if float(treasury_change.group(1)) >= 0:
                continue
            ai_chance = _named_block(option, "ai_chance")
            assert re.search(
                r"modifier\s*=\s*\{\s*factor\s*=\s*0\s+"
                r"has_active_mission\s*=\s*bankruptcy_incoming_collapse\s*\}",
                ai_chance,
            )


def test_peace_cleanup_preserves_a_later_one_time_war_response():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    monthly = _named_block(effects, "UKR_strategic_industry_monthly_driver")

    assert "UKR_strategic_industry_clear_wartime_ideas = yes" in monthly
    assert "clr_country_flag = UKR_strategic_industry_motor_sich_wartime_transfer" in (
        monthly
    )
    assert "set_country_flag = UKR_strategic_industry_event_10_resolved" in monthly
    assert "country_event = { id = UKR_strategic_industry_events.11 days = 90 }" in (
        monthly
    )
    assert (
        "flag = UKR_strategic_industry_terminal_peace_window_active value = 1 days = 180"
        in (monthly)
    )

    war_delivery = _smallest_block_containing(
        monthly, "country_event = { id = UKR_strategic_industry_events.9 days = 1 }"
    )
    assert "UKR_strategic_industry_terminal_outcome_present" not in war_delivery
    assert "UKR_strategic_industry_terminal_outcome_present" not in _named_block(
        events[9], "trigger"
    )
    finalize = _named_block(effects, "UKR_strategic_industry_finalize_terminal_state")
    assert "UKR_strategic_industry_event_09_resolved" not in finalize

    terminal_corpus = "\n".join(
        (
            effects,
            EVENTS_PATH.read_text(encoding="utf-8"),
            TRIGGERS_PATH.read_text(encoding="utf-8"),
            CORPORATE_TRIGGERS_PATH.read_text(encoding="utf-8"),
            DASHBOARD_LOC_PATH.read_text(encoding="utf-8"),
        )
    )
    assert "UKR_strategic_industry_terminal_resolved" not in terminal_corpus
    assert "UKR_strategic_industry_terminal_outcome_present = yes" in events[15]

    disruption = _named_block(effects, "UKR_strategic_industry_apply_war_disruption")
    assert (
        "NOT = { has_country_flag = UKR_strategic_industry_war_disruption_applied }"
        in disruption
    )
    assert "set_country_flag = UKR_strategic_industry_war_disruption_applied" in (
        disruption
    )
    assert "set_country_flag = UKR_strategic_industry_war_observed" in disruption


def test_dynamic_modifier_backing_state_and_existing_rewards_are_read_only():
    dynamic_text = UKR_DYNAMIC_PATH.read_text(encoding="utf-8")
    economic_variables = _dynamic_backing_variables(
        dynamic_text, "UKR_economic_reforms_modifier"
    )
    military_variables = _dynamic_backing_variables(
        dynamic_text, "UKR_military_reforms_modifier"
    )
    assert len(economic_variables) >= 15
    assert len(military_variables) >= 40
    assert "UKR_strategic_industry" not in dynamic_text

    chain_paths = (
        EVENTS_PATH,
        EFFECTS_PATH,
        TRIGGERS_PATH,
        IDEAS_PATH,
        DASHBOARD_PATH,
        DASHBOARD_LOC_PATH,
    )
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in chain_paths)
    _assert_no_variable_writes(corpus, economic_variables | military_variables)
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
        "ukr_industry_points",
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
        "UKR_strategic_industry_initialize_state = yes",
        "UKR_strategic_industry_reconstruct_history = yes",
    ):
        assert call in bootstrap
    assert "UKR_strategic_industry_events.90" not in bootstrap
    monthly_dispatch = _named_block(
        monthly_dispatch_text, "corporate_history_monthly_dispatch"
    )
    assert "corporate_history_country_bootstrap = yes" in monthly_dispatch
    assert "corporate_history_initialize_midyear_recovery = yes" in monthly_dispatch
    assert "corporate_history_recover_midyear_events = yes" in monthly_dispatch

    monthly = _named_block(common, "UKR_corporate_history_monthly_outcomes")
    assert "UKR_strategic_industry_schedule_current_year_events = yes" in monthly
    assert "UKR_strategic_industry_monthly_driver = yes" in monthly
    full_driver = _smallest_block_containing(
        monthly, "UKR_strategic_industry_monthly_driver = yes"
    )
    assert "corporate_history_full_enabled = yes" in full_driver
    assert "corporate_history_enabled = yes" not in full_driver
    assert "corporate_history_outcomes_only_enabled = yes" in monthly
    assert "UKR_strategic_industry_reconstruct_history = yes" in monthly
    assert "UKR_corporate_history_monthly_outcomes = yes" in monthly_on_actions

    schedule_years = {
        2: 2001,
        3: 2003,
        4: 2005,
        5: 2008,
        7: 2016,
        8: 2020,
        13: 2023,
        14: 2023,
        15: 2026,
    }
    for event_number, year in schedule_years.items():
        year_block = _named_block(dispatch, f"UKR_corporate_trigger_year_{year}")
        delivery = year_block
        if event_number == 2:
            assert "UKR_strategic_industry_dispatch_event_02 = yes" in year_block
            delivery += _named_block(
                dispatch, "UKR_strategic_industry_dispatch_event_02"
            )
        assert f"UKR_strategic_industry_schedule_event_{event_number:02d} = yes" in (
            delivery
        )
        year_router = _named_block(
            monthly_dispatch_text, f"corporate_history_dispatch_year_{year}"
        )
        assert "original_tag = UKR" in year_router
        assert f"UKR_corporate_trigger_year_{year} = yes" in year_router
    assert "UKR_strategic_industry_schedule_event_06" not in dispatch
    assert "UKR_strategic_industry_schedule_event_09" not in dispatch

    category_block = _named_block(category, "UKR_corporate_systems_dashboard_category")
    assert "allowed = { original_tag = UKR }" in category_block
    assert "priority = 144" in category_block
    assert "visible_when_empty = yes" in category_block
    assert "corporate_history_enabled = yes" in category_block
    assert "NOT = { has_country_flag = collapsed_nation }" in category_block
    decision_ids = re.findall(
        r"(?m)^\t(UKR_corporate_systems_[a-z0-9_]+)\s*=\s*\{", dashboard
    )
    assert len(decision_ids) == 6
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
    assert "UKR_strategic_industry_meaningful_state = yes" in corporate_triggers
    assert "UKR_strategic_industry_terminal_outcome_present = yes" in corporate_triggers

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(
        item for item in manifest["chains"] if item["root"] == "UKR_strategic_industry"
    )
    assert chain["name"] == "Ukrainian Strategic Industry"
    assert chain["tag"] == "UKR"
    assert chain["namespace"] == "UKR_strategic_industry_events"
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
    assert chain["monthly_driver"] == "UKR_corporate_history_monthly_outcomes"
    assert chain["terminal_marker"] == "UKR_strategic_industry_reconstruct_complete"
    assert chain["terminal_date"] == "2026-01-01"
    assert chain["allowed_writes"] == []
    assert "UKR_strategic_industry_events.90" not in chain["expected_callers"]


def test_new_english_surface_contains_no_banned_dash_character():
    new_paths = (
        EVENTS_PATH,
        EFFECTS_PATH,
        TRIGGERS_PATH,
        IDEAS_PATH,
        DASHBOARD_PATH,
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
        if "UKR_strategic_industry" in line or "UKR_corporate_systems_" in line
    ]
    assert new_lines
    assert "\u2014" not in "\n".join(new_lines)
