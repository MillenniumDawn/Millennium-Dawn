from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
RULE_PATH = ROOT / "common" / "game_rules" / "00_game_rules.txt"
TRIGGERS_PATH = ROOT / "common" / "scripted_triggers" / "MD_linux_system_triggers.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "MD_linux_system_effects.txt"
ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "02_linux_system_on_actions.txt"
ON_ACTIONS_DIR = ROOT / "common" / "on_actions"
EVENTS_PATH = ROOT / "events" / "MD_linux_system_events.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "MD_linux_system_ideas.txt"
DECISIONS_PATH = ROOT / "common" / "decisions" / "MD_linux_system_decisions.txt"
CATEGORY_PATH = (
    ROOT / "common" / "decisions" / "categories" / "MD_linux_system_categories.txt"
)
BRIDGE_PATH = ROOT / "common" / "scripted_effects" / "USA_corporate_systems_effects.txt"
STORAGE_EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_dell_effects.txt"
STORAGE_EVENTS_PATH = ROOT / "events" / "United States.txt"
STORAGE_DRIVER_PATH = (
    ROOT / "common" / "scripted_effects" / "USA_oem_legacy_effects.txt"
)
IBM_EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_ibm_effects.txt"
IBM_EVENTS_PATH = ROOT / "events" / "USA_ibm_events.txt"
GLOBAL_LOC_PATH = ROOT / "localisation" / "english" / "MD_linux_system_l_english.yml"
RULE_LOC_PATH = ROOT / "localisation" / "english" / "MD_game_rules_l_english.yml"
USA_LOC_PATH = ROOT / "localisation" / "english" / "MD_focus_USA_l_english.yml"

VARIABLE_BOUNDS = {
    "linux_system_base_deployment": {"min": 0, "max": 10},
    "linux_system_base_stewardship": {"min": 0, "max": 10},
    "linux_system_base_assurance": {"min": 0, "max": 10},
    "linux_system_adapter_deployment": {"min": -2, "max": 2},
    "linux_system_adapter_stewardship": {"min": -2, "max": 2},
    "linux_system_adapter_assurance": {"min": -2, "max": 2},
    "linux_system_effective_deployment": {"min": 0, "max": 10},
    "linux_system_effective_stewardship": {"min": 0, "max": 10},
    "linux_system_effective_assurance": {"min": 0, "max": 10},
    "linux_system_base_support_model": {"min": 0, "max": 3},
    "linux_system_adapter_support_model": {"min": 0, "max": 3},
    "linux_system_effective_support_model": {"min": 0, "max": 3},
    "linux_system_milestone_stage": {"min": 0, "max": 5},
}

NEUTRAL_BASELINE = [
    {"stage": 0, "deployment": 2, "stewardship": 3, "assurance": 3, "support_model": 0},
    {"stage": 1, "deployment": 3, "stewardship": 3, "assurance": 3, "support_model": 0},
    {"stage": 2, "deployment": 4, "stewardship": 3, "assurance": 3, "support_model": 0},
    {"stage": 3, "deployment": 5, "stewardship": 3, "assurance": 4, "support_model": 0},
    {"stage": 4, "deployment": 6, "stewardship": 3, "assurance": 4, "support_model": 0},
    {"stage": 5, "deployment": 7, "stewardship": 3, "assurance": 5, "support_model": 0},
]

HISTORICAL_ROUTES = {
    "BRA": "upstream",
    "CHI": "national",
    "ENG": "upstream",
    "FRA": "national",
    "GER": "upstream",
    "RAJ": "national",
    "SOV": "national",
    "USA": "enterprise",
}

PARTICIPANT_TAGS = [
    "BRA",
    "CHI",
    "ENG",
    "FRA",
    "GER",
    "POL",
    "RAJ",
    "SOV",
    "USA",
    "VEN",
]

EVENT_DELTAS = {
    1: [(1, 2, 0, 1), (2, 0, 1, 2), (0, -1, -1, 0)],
    2: [(1, 1, 1, 1), (1, 0, 2, 2), (1, 0, 2, 3), (0, 0, -1, 0)],
    3: [(0, 1, 1, 1), (1, 0, 2, 2), (0, 0, 2, 3), (0, 0, -1, 0)],
    4: [(2, 2, 1, 1), (2, 0, 2, 2), (1, 0, 2, 3)],
    5: [(0, 2, 1, 1), (0, 0, 2, 2), (0, 0, 2, 3), (-1, 0, -2, 0)],
}


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


def _linux_driver_hosts() -> list[tuple[str, str]]:
    hosts = []
    pattern = re.compile(r"(?m)^\s*(on_[A-Za-z0-9_]+)\s*=\s*\{")
    for path in sorted(ON_ACTIONS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            if match.group(1) == "on_actions":
                continue
            block = _extract_block(text, text.index("{", match.start()))
            if "linux_system_monthly_driver = yes" in block:
                hosts.append((match.group(1), block))
    return hosts


def _event_map(text: str, namespace: str) -> dict[int, str]:
    events = {}
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, text.index("{", match.start()))
        event_id = re.search(rf"(?m)^\s*id\s*=\s*{re.escape(namespace)}\.(\d+)", block)
        if event_id:
            events[int(event_id.group(1))] = block
    return events


def _option_blocks(event: str) -> list[str]:
    return [
        _extract_block(event, event.index("{", match.start()))
        for match in re.finditer(r"(?m)^\s*option\s*=\s*\{", event)
    ]


def _numeric_modifier_map(idea_block: str) -> dict[str, float | int]:
    modifier_match = re.search(r"(?m)^\s*modifier\s*=\s*\{", idea_block)
    if not modifier_match:
        return {}
    modifier = _extract_block(idea_block, idea_block.index("{", modifier_match.start()))
    parsed = {}
    for key, raw_value in re.findall(
        r"\b([a-zA-Z0-9_@]+)\s*=\s*(-?\d+(?:\.\d+)?)\b", modifier
    ):
        value = float(raw_value)
        parsed[key] = int(value) if value.is_integer() else value
    return parsed


def _axis_delta(option: str, variable: str) -> int:
    match = re.search(
        rf"add_to_variable\s*=\s*\{{\s*{re.escape(variable)}\s*=\s*(-?\d+)",
        option,
    )
    return int(match.group(1)) if match else 0


def _localisation_keys(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    return re.findall(r"(?m)^ ([^\s:#][^:]*):", text)


def _shared_system() -> dict:
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 6
    systems = [
        system
        for system in manifest["shared_systems"]
        if system["namespace"] == "linux_system_events"
    ]
    assert len(systems) == 1
    return systems[0]


def test_schema_v6_declares_the_public_linux_contract_exactly():
    system = _shared_system()

    assert system["root"] == "linux_system"
    assert system["dispatcher_host"] == "country_local"
    assert system["participant_array"] == ""
    assert system["participant_tags"] == PARTICIPANT_TAGS
    assert system["game_rule"] == {
        "id": "rule_linux_ecosystem",
        "options": ["full", "outcomes_only", "off"],
        "default": "full",
    }
    assert system["variables"] == VARIABLE_BOUNDS
    assert system["initial_state"] == {
        "deployment": 2,
        "stewardship": 3,
        "assurance": 3,
        "support_model": 0,
        "milestone_stage": 0,
    }
    assert system["support_model_codes"] == {
        "mixed": 0,
        "upstream": 1,
        "enterprise": 2,
        "national": 3,
    }
    assert system["support_model_precedence"] == "non_mixed_base_else_adapter"
    assert system["reconstruction_baseline"] == NEUTRAL_BASELINE
    assert system["historical_routes"] == HISTORICAL_ROUTES
    assert system["event_ids"] == [
        f"linux_system_events.{index}" for index in range(1, 6)
    ]


def test_rule_modes_and_public_effect_surface_are_stable():
    rules = RULE_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    system = _shared_system()

    rule = _named_block(rules, "rule_linux_ecosystem")
    assert _named_block(rule, "default").count("name = full") == 1
    assert rule.count("name = full") == 1
    assert rule.count("name = outcomes_only") == 1
    assert rule.count("name = off") == 1

    assert "option = outcomes_only" in _named_block(
        triggers, "linux_system_outcomes_only_enabled"
    )
    full = _named_block(triggers, "linux_system_full_enabled")
    assert "option = outcomes_only" in full
    assert "option = off" in full
    enabled = _named_block(triggers, "linux_system_enabled")
    assert "linux_system_full_enabled = yes" in enabled
    assert "linux_system_outcomes_only_enabled = yes" in enabled

    assert set(system["scripted_effects"]) == {
        "linux_system_reconstruct_country",
        *(f"linux_system_schedule_event_{index}" for index in range(1, 6)),
        "linux_system_schedule_year_events",
        *(f"linux_system_activate_event_{index}" for index in range(1, 6)),
        "linux_system_recover_due_events",
        "linux_system_clear_owned_artifacts",
        "linux_system_monthly_driver",
    }
    for effect in system["scripted_effects"]:
        assert len(re.findall(rf"(?m)^{re.escape(effect)}\s*=\s*\{{", effects)) == 1


def test_driver_uses_only_declared_country_monthly_hosts():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    driver_hosts = _linux_driver_hosts()
    on_actions = "\n".join(block for _host, block in driver_hosts)
    combined = effects + on_actions

    assert "every_country" not in combined
    assert "random_country" not in combined
    assert "global.linux_system_participants" not in combined
    assert not re.search(r"\b(?:add_to|remove_from|clear)_array\b", combined)

    assert {host for host, _block in driver_hosts} == {
        f"on_monthly_{tag}" for tag in PARTICIPANT_TAGS
    }
    assert len(driver_hosts) == len(PARTICIPANT_TAGS)
    assert on_actions.count("linux_system_monthly_driver = yes") == len(
        PARTICIPANT_TAGS
    )
    for tag in PARTICIPANT_TAGS:
        monthly_host = next(
            block for host, block in driver_hosts if host == f"on_monthly_{tag}"
        )
        assert monthly_host.count("linux_system_monthly_driver = yes") == 1

    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    participant_trigger = _named_block(triggers, "linux_system_is_participant")
    assert (
        re.findall(r"\boriginal_tag\s*=\s*([A-Z0-9]{3})\b", participant_trigger)
        == PARTICIPANT_TAGS
    )
    assert not re.search(r"(?<!original_)\btag\s*=", participant_trigger)

    monthly = _named_block(effects, "linux_system_monthly_driver")
    for excluded in (
        "tag = ABK",
        "tag = ZOM",
        "MD_special_countries = yes",
        "collapsed_nation",
    ):
        assert excluded in monthly
    assert "linux_system_initialize_state = yes" in monthly
    assert "linux_system_is_participant = yes" in monthly
    assert "linux_system_reconstruct_country = yes" in monthly
    assert "linux_system_full_enabled = yes" in monthly
    assert "linux_system_schedule_year_events = yes" in monthly
    assert "linux_system_recover_due_events = yes" in monthly
    assert "linux_system_clear_owned_artifacts = yes" in monthly


def test_country_lifecycle_skips_collapsed_and_restores_missed_or_future_state():
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")

    needs_reconstruction = _named_block(
        triggers, "linux_system_country_needs_reconstruction"
    )
    for index in range(1, 6):
        assert f"GLOBAL_linux_system_milestone_{index}_reached" not in effects
        assert f"GLOBAL_linux_system_milestone_{index}_reached" not in triggers
        assert (
            f"NOT = {{ has_country_flag = linux_system_event_{index}_resolved }}"
            in needs_reconstruction
        )

        schedule = _named_block(effects, f"linux_system_schedule_event_{index}")
        activate = _named_block(effects, f"linux_system_activate_event_{index}")
        assert "linux_system_full_enabled = yes" in schedule
        assert "NOT = { has_country_flag = collapsed_nation }" in schedule
        assert "NOT = { has_country_flag = collapsed_nation }" in activate
        assert f"id = linux_system_events.{index}" in schedule
        assert f"id = linux_system_events.{index}" in activate

    schedule_year = _named_block(effects, "linux_system_schedule_year_events")
    recovery = _named_block(effects, "linux_system_recover_due_events")
    monthly = _named_block(effects, "linux_system_monthly_driver")
    for index in range(1, 6):
        assert f"linux_system_schedule_event_{index} = yes" in schedule_year
        assert f"linux_system_activate_event_{index} = yes" in recovery
    assert monthly.index("linux_system_reconstruct_country = yes") < monthly.index(
        "linux_system_schedule_year_events = yes"
    )
    assert "linux_system_country_needs_reconstruction = yes" in _named_block(
        effects, "linux_system_reconstruct_country"
    )


def test_reconstruction_has_no_cost_or_reward_side_effects():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    storage = STORAGE_EFFECTS_PATH.read_text(encoding="utf-8")
    blocks = [_named_block(effects, "linux_system_reconstruct_country")]
    blocks.extend(
        _named_block(effects, f"linux_system_reconstruct_event_{index}")
        for index in range(1, 6)
    )
    blocks.append(_named_block(storage, "USA_oem_storage_reconstruct_history"))
    reconstruction = "\n".join(blocks)

    for forbidden in (
        "country_event =",
        "modify_treasury_effect",
        "add_political_power",
        "add_tech_bonus",
        "add_timed_idea",
    ):
        assert forbidden not in reconstruction

    for stage in NEUTRAL_BASELINE[1:]:
        block = _named_block(
            effects, f"linux_system_reconstruct_event_{stage['stage']}"
        )
        assert f"linux_system_base_deployment = {stage['deployment']}" in block
        assert f"linux_system_base_stewardship = {stage['stewardship']}" in block
        assert f"linux_system_base_assurance = {stage['assurance']}" in block
        assert f"linux_system_base_support_model = {stage['support_model']}" in block


def test_off_cleanup_removes_all_linux_owned_state_but_not_storage_state():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    clear = _named_block(effects, "linux_system_clear_country_state")
    owned = _named_block(triggers, "linux_system_has_owned_artifacts")

    for decision in _shared_system()["programs"]:
        assert f"remove_decision = {decision}" in clear
        assert f"has_decision = {decision}" in owned
    for index in range(1, 6):
        assert f"clr_country_flag = linux_system_event_{index}_expected" in clear
        assert f"clr_country_flag = linux_system_event_{index}_pending" in clear
        assert f"clr_country_flag = linux_system_event_{index}_resolved" in clear
    for cleared in (
        "linux_system_initialized",
        "linux_system_country_bootstrapped",
        "linux_system_dirty",
    ):
        assert f"clr_country_flag = {cleared}" in clear
    for variable in VARIABLE_BOUNDS:
        assert f"clear_variable = {variable}" in clear
    assert "set_variable" not in clear
    assert "global." not in effects
    assert "GLOBAL_linux_system_milestone_" not in effects
    assert "USA_oem_storage_" not in clear
    assert "linux_system_usa_storage_legacy_" not in clear
    assert "linux_system_program_cooldown" not in clear
    assert "linux_system_program_cooldown" not in owned


def test_global_events_have_exact_lifecycle_and_state_deltas():
    text = EVENTS_PATH.read_text(encoding="utf-8")
    events = _event_map(text, "linux_system_events")

    assert set(events) == set(range(1, 6))
    assert "news_event" not in text
    assert "major = yes" not in text
    for event_number, expected_deltas in EVENT_DELTAS.items():
        event = events[event_number]
        assert "is_triggered_only = yes" in event
        assert "linux_system_full_enabled = yes" in event
        assert f"has_country_flag = linux_system_event_{event_number}_expected" in event
        assert f"has_country_flag = linux_system_event_{event_number}_pending" in event
        assert (
            f"NOT = {{ has_country_flag = linux_system_event_{event_number}_resolved }}"
            in event
        )
        options = _option_blocks(event)
        assert len(options) == len(expected_deltas)
        for option, expected in zip(options, expected_deltas):
            actual = (
                _axis_delta(option, "linux_system_base_deployment"),
                _axis_delta(option, "linux_system_base_stewardship"),
                _axis_delta(option, "linux_system_base_assurance"),
                int(
                    re.search(
                        r"set_variable\s*=\s*\{\s*linux_system_base_support_model\s*=\s*(\d)",
                        option,
                    ).group(1)
                ),
            )
            assert actual == expected
            assert (
                f"clr_country_flag = linux_system_event_{event_number}_expected"
                in option
            )
            assert (
                f"clr_country_flag = linux_system_event_{event_number}_pending"
                in option
            )
            assert (
                f"set_country_flag = linux_system_event_{event_number}_resolved"
                in option
            )
            expected_route_markers = 1 if event_number in (2, 3, 4) else 0
            assert (
                option.count(
                    f"set_country_flag = linux_system_event_{event_number}_route_"
                )
                == expected_route_markers
            )
            assert "linux_system_mark_dirty = yes" in option
            assert "linux_system_recalculate_state = yes" in option
            assert "log = " in option


def test_event_costs_rewards_and_fallbacks_match_the_design():
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"), "linux_system_events")
    event_1 = _option_blocks(events[1])
    event_2 = _option_blocks(events[2])
    event_3 = _option_blocks(events[3])
    event_4 = _option_blocks(events[4])
    event_5 = _option_blocks(events[5])

    for option in event_1[:2]:
        assert "bonus = 0.05" in option
        assert "uses = 1" in option
        assert "category = CAT_computing_tech" in option
    assert "add_tech_bonus" not in event_1[2]

    assert [
        "linux_system_pay_gdp_0_2_percent",
        "linux_system_pay_gdp_0_1_percent",
        "linux_system_pay_gdp_0_2_percent",
    ] == [
        re.search(r"linux_system_pay_gdp_0_[12]_percent", option).group(0)
        for option in event_2[:3]
    ]
    assert [
        "add_political_power = -50",
        "add_political_power = -25",
        "add_political_power = -50",
    ] == [
        re.search(r"add_political_power = -\d+", option).group(0)
        for option in event_2[:3]
    ]
    assert "linux_system_pay_gdp" not in event_2[3]
    assert "add_political_power" not in event_2[3]

    assert "linux_system_shared_updates_program days = 365" in event_3[0]
    assert "linux_system_pay_gdp_0_1_percent = yes" in event_3[1]
    assert "linux_system_pay_gdp_0_2_percent = yes" in event_3[2]
    assert "linux_system_national_signing_program days = 365" in event_3[2]
    assert "modifier = { factor = 0 }" in event_3[3]

    event_4_categories = (
        "CAT_internet_tech",
        "CAT_internet_tech",
        "CAT_encryption_tech",
    )
    assert len(event_4) == len(event_4_categories)
    for option, category in zip(event_4, event_4_categories):
        assert "bonus = 0.05" in option
        assert "uses = 1" in option
        assert f"category = {category}" in option

    assert "linux_system_pay_gdp_0_1_percent = yes" in event_5[0]
    assert "add_political_power = -25" in event_5[0]
    assert "linux_system_pay_gdp_0_1_percent = yes" in event_5[1]
    assert "add_political_power = -50" in event_5[1]
    assert "linux_system_pay_gdp_0_2_percent = yes" in event_5[2]
    assert "add_political_power = -50" in event_5[2]
    assert "linux_system_fragile_estate days = 365" in event_5[3]
    assert "linux_system_pay_gdp" not in event_5[3]


def test_late_start_events_always_have_a_non_usa_description():
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"), "linux_system_events")

    offered_routes = {
        2: ("upstream", "enterprise", "national", "mixed"),
        3: ("upstream", "enterprise", "national", "mixed"),
        4: ("upstream", "enterprise", "national"),
    }
    for event_number, previous in ((3, 2), (4, 3), (5, 4)):
        event = events[event_number]
        assert "NOT = { original_tag = USA }" in event
        for route in offered_routes[previous]:
            assert (
                f"NOT = {{ has_country_flag = linux_system_event_{previous}_route_{route} }}"
                in event
            )


def test_dispatch_and_recovery_own_every_expected_pending_resolved_marker():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    on_actions = "\n".join(block for _host, block in _linux_driver_hosts())
    system = _shared_system()

    assert on_actions.count("linux_system_monthly_driver = yes") == len(
        PARTICIPANT_TAGS
    )
    assert "on_daily" not in on_actions
    assert "on_startup" not in on_actions
    assert "ABK =" not in on_actions
    for index in range(1, 6):
        markers = system["lifecycle_markers"][f"linux_system_events.{index}"]
        assert markers == [
            f"linux_system_event_{index}_expected",
            f"linux_system_event_{index}_pending",
            f"linux_system_event_{index}_resolved",
        ]
        schedule = _named_block(effects, f"linux_system_schedule_event_{index}")
        assert f"set_country_flag = linux_system_event_{index}_expected" in schedule
        assert f"flag = linux_system_event_{index}_pending" in schedule
        assert f"id = linux_system_events.{index}" in schedule
        assert f"GLOBAL_linux_system_milestone_{index}_reached" not in effects

    recovery = _named_block(effects, "linux_system_recover_due_events")
    repair = _named_block(effects, "linux_system_repair_delivery_markers")
    assert "linux_system_repair_delivery_markers = yes" in recovery
    for index in range(1, 6):
        assert f"has_country_flag = linux_system_event_{index}_pending" in repair
        assert (
            f"NOT = {{ has_country_flag = linux_system_event_{index}_expected }}"
            in repair
        )
        assert f"set_country_flag = linux_system_event_{index}_expected" in repair
        assert (
            f"NOT = {{ has_country_flag = linux_system_event_{index}_resolved }}"
            in recovery
        )
        assert f"linux_system_activate_event_{index} = yes" in recovery
        activation = _named_block(effects, f"linux_system_activate_event_{index}")
        assert "linux_system_outcomes_only_enabled = yes" in activation
        assert f"linux_system_reconstruct_event_{index} = yes" in activation
        assert f"id = linux_system_events.{index} days = 1" in activation

    monthly = _named_block(effects, "linux_system_monthly_driver")
    assert "linux_system_full_enabled = yes" in monthly
    assert "linux_system_schedule_year_events = yes" in monthly
    assert "linux_system_recover_due_events = yes" in monthly
    assert "linux_system_outcomes_only_enabled = yes" in monthly
    assert "linux_system_reconstruct_country = yes" in monthly
    assert "linux_system_clear_owned_artifacts = yes" in monthly
    assert "linux_system_startup_bootstrap" not in effects


def test_persistent_and_timed_ideas_match_the_manifest_exactly():
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    system = _shared_system()

    persistent = system["adoption_ideas"] + system["support_ideas"]
    assert len(persistent) == 8
    for idea in persistent:
        block = _named_block(ideas, idea)
        assert "allowed = { NOT = { original_tag = USA } }" in block
        assert _numeric_modifier_map(block) == system["persistent_idea_modifiers"][idea]

    for idea, expected in system["timed_idea_modifiers"].items():
        assert _numeric_modifier_map(_named_block(ideas, idea)) == expected

    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    refresh = _named_block(effects, "linux_system_refresh_ideas")
    assert "original_tag = USA" in refresh
    assert "linux_system_clear_adoption_ideas = yes" in refresh
    assert "linux_system_clear_support_ideas = yes" in refresh


def test_program_cost_duration_slot_and_bankruptcy_contract():
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    category = CATEGORY_PATH.read_text(encoding="utf-8")
    system = _shared_system()

    assert "linux_system_full_enabled = yes" in _named_block(
        category, "linux_system_programs"
    )
    slot = _named_block(triggers, "linux_system_program_slot_available")
    assert "linux_system_program_cooldown" not in slot
    assert "NOT = { linux_system_has_active_program = yes }" in slot

    for decision, contract in system["programs"].items():
        block = _named_block(decisions, decision)
        assert f"cost = {contract['political_power']}" in block
        assert f"days_remove = {contract['duration_days']}" in block
        assert "fire_only_once = no" in block
        assert "linux_system_full_enabled = yes" in block
        assert "linux_system_program_slot_available = yes" in block
        assert f"remove_ideas = {contract['idea']}" in block
        assert contract["cooldown_days"] == 0
        assert "linux_system_program_cooldown" not in block
        assert block.count("log = ") >= 2
        assert "has_active_mission = bankruptcy_incoming_collapse" in block

    procurement = _named_block(decisions, "linux_system_public_procurement")
    assert "NOT = { original_tag = USA }" in procurement


def test_storage_chain_has_complete_lifecycle_and_safe_reconstruction():
    assert not STORAGE_EVENTS_PATH.read_bytes().startswith(b"\xef\xbb\xbf")
    event_text = STORAGE_EVENTS_PATH.read_text(encoding="utf-8")
    events = _event_map(event_text, "USA_oem_events")
    effects = STORAGE_EFFECTS_PATH.read_text(encoding="utf-8")
    driver_effects = STORAGE_DRIVER_PATH.read_text(encoding="utf-8")
    system = _shared_system()

    for index in range(16, 24):
        event = events[index]
        markers = system["storage_lifecycle_markers"][f"USA_oem_events.{index}"]
        assert markers == [
            f"USA_oem_storage_event_{index}_expected",
            f"USA_oem_storage_event_{index}_pending",
            f"USA_oem_storage_event_{index}_resolved",
        ]
        assert "corporate_history_full_enabled = yes" in event
        assert "linux_system_full_enabled = yes" not in event
        assert f"has_country_flag = USA_oem_storage_event_{index}_expected" in event
        assert f"has_country_flag = USA_oem_storage_event_{index}_pending" in event
        assert (
            f"NOT = {{ has_country_flag = USA_oem_storage_event_{index}_resolved }}"
            in event
        )
        immediate = _named_block(event, "immediate")
        initialize = "linux_system_initialize_state = yes"
        recalculate = "linux_system_recalculate_state = yes"
        assert immediate.count(initialize) == 1
        assert immediate.count(recalculate) == 1
        assert immediate.index(initialize) < immediate.index(recalculate)
        for option in _option_blocks(event):
            assert (
                f"clr_country_flag = USA_oem_storage_event_{index}_expected" in option
            )
            assert f"clr_country_flag = USA_oem_storage_event_{index}_pending" in option
            assert (
                f"set_country_flag = USA_oem_storage_event_{index}_resolved" in option
            )
            assert "linux_system_recalculate_state = yes" in option

        schedule = _named_block(driver_effects, "USA_oem_storage_schedule_year_events")
        due = _named_block(driver_effects, "USA_oem_storage_schedule_due_events")
        assert f"USA_oem_events.{index}" in schedule
        assert f"USA_oem_storage_event_{index}_resolved" in schedule
        assert f"USA_oem_storage_event_{index}_pending" in schedule
        assert f"USA_oem_storage_event_{index}_expected" in due

    reconstruct = _named_block(effects, "USA_oem_storage_reconstruct_history")
    assert "corporate_history_enabled = yes" in reconstruct
    assert "linux_system_enabled = yes" not in reconstruct
    assert "linux_system_outcomes_only_enabled = yes" not in reconstruct
    for forbidden in (
        "add_political_power",
        "modify_treasury_effect",
        "add_tech_bonus",
        "add_timed_idea",
        "USA_oem_storage_firmware_2015_resolved",
        "USA_dell_storage_bridge_initialized",
    ):
        assert forbidden not in reconstruct

    repair = _named_block(effects, "USA_oem_storage_repair_delivery_markers")
    recovery = _named_block(effects, "USA_oem_storage_recover_pending_events")
    assert "corporate_history_full_enabled = yes" in recovery
    assert "linux_system_full_enabled = yes" not in recovery
    assert "USA_oem_storage_repair_delivery_markers = yes" in recovery
    for index in range(16, 24):
        assert f"has_country_flag = USA_oem_storage_event_{index}_pending" in repair
        assert (
            f"NOT = {{ has_country_flag = USA_oem_storage_event_{index}_expected }}"
            in repair
        )
        assert f"set_country_flag = USA_oem_storage_event_{index}_expected" in repair

    monthly = _named_block(driver_effects, "USA_oem_storage_monthly_driver")
    assert "corporate_history_enabled = yes" in monthly
    assert "linux_system_enabled = yes" not in monthly
    assert "corporate_history_full_enabled = yes" in monthly
    assert "linux_system_full_enabled = yes" not in monthly
    assert "USA_oem_storage_schedule_year_events = yes" in monthly
    assert "USA_oem_storage_schedule_due_events = yes" in monthly
    assert "USA_oem_storage_reconstruct_history = yes" in monthly
    assert "USA_oem_storage_clear_linux_pending_markers = yes" in monthly
    assert "USA_oem_storage_clear_legacy_linux_adapter_state = yes" in monthly

    mark_dirty = _named_block(
        EFFECTS_PATH.read_text(encoding="utf-8"), "linux_system_mark_dirty"
    )
    assert "linux_system_enabled = yes" in mark_dirty


def test_storage_legacy_import_is_once_only_read_only_and_bounded():
    effects = STORAGE_EFFECTS_PATH.read_text(encoding="utf-8")
    import_block = _named_block(effects, "USA_oem_storage_import_legacy_linux_state")

    assert (
        "NOT = { has_country_flag = linux_system_usa_storage_legacy_imported }"
        in import_block
    )
    assert "set_country_flag = linux_system_usa_storage_legacy_imported" in import_block
    assert "linux_system_usa_storage_legacy_route_upstream" in import_block
    assert "linux_system_usa_storage_legacy_route_enterprise" in import_block
    assert (
        "clamp_variable = { var = linux_system_usa_storage_legacy_import_level min = 1 max = 2 }"
        in import_block
    )
    assert not re.search(
        r"(?:set|add_to|subtract_from|multiply|divide)_variable\s*=\s*"
        r"\{\s*USA_oem_storage_policy\s*=",
        effects,
    )

    core = EFFECTS_PATH.read_text(encoding="utf-8")
    adapter = _named_block(core, "linux_system_refresh_usa_adapter")
    strict = _named_block(adapter, "if")
    assert "USA_ibm_state_initialized" in strict
    assert "USA_oem_storage_event_18_route_enterprise" in adapter
    assert "linux_system_adapter_stewardship = 1" in adapter
    assert "linux_system_adapter_assurance = 1" in adapter
    assert "USA_oem_storage_event_18_route_upstream" in adapter
    assert "linux_system_adapter_deployment = 1" in adapter


def test_usa_bridge_reads_base_only_and_caps_linux_to_one_per_axis():
    bridge_text = BRIDGE_PATH.read_text(encoding="utf-8")
    bridge = _named_block(bridge_text, "USA_corporate_systems_linux_contribution")

    assert "linux_system_adapter_" not in bridge
    assert "linux_system_effective_" not in bridge
    for expected in (
        "linux_system_base_deployment > 5",
        "linux_system_base_stewardship > 6",
        "linux_system_base_stewardship < 3",
        "linux_system_base_assurance > 6",
        "linux_system_base_assurance < 3",
        "linux_system_base_support_model = 2",
        "linux_system_base_support_model = 3",
    ):
        assert expected in bridge
    for operation in re.findall(
        r"(?:add_to|subtract_from)_temp_variable\s*=\s*\{[^}]+\}", bridge
    ):
        assert re.search(r"= 1\s*\}", operation)

    rebuild = _named_block(
        bridge_text, "USA_corporate_systems_rebuild_company_contributions"
    )
    assert "USA_corporate_systems_linux_contribution = yes" in rebuild
    for axis in (
        "open_standards",
        "vertical_integration",
        "supply_resilience",
        "security_control",
        "national_compute_stack",
    ):
        assert (
            f"clamp_temp_variable = {{ var = USA_oem_contribution_{axis} min = -3 max = 3 }}"
            in rebuild
        )

    linux_only = _named_block(
        bridge_text, "USA_corporate_systems_rebuild_linux_only_axes"
    )
    assert "USA_corporate_systems_linux_contribution = yes" in linux_only
    assert "USA_ibm_initialize_state" not in linux_only
    for axis in (
        "open_standards",
        "vertical_integration",
        "supply_resilience",
        "security_control",
        "national_compute_stack",
    ):
        assert f"set_variable = {{ USA_oem_effective_{axis} = 5 }}" in linux_only
        assert f"set_variable = {{ USA_oem_{axis} = 5 }}" not in linux_only

    update = _named_block(bridge_text, "USA_corporate_systems_update_economic_bridge")
    assert "linux_system_enabled = yes" in update
    assert "has_country_flag = linux_system_initialized" in update
    assert "USA_corporate_systems_rebuild_linux_only_axes = yes" in update


def test_ibm_linux_markers_conditionals_and_event_ceiling_are_stable():
    event_text = IBM_EVENTS_PATH.read_text(encoding="utf-8")
    effects = IBM_EFFECTS_PATH.read_text(encoding="utf-8")
    events = _event_map(event_text, "USA_ibm_events")

    assert not (set(events) & set(range(51, 90)))
    assert 90 in events
    marker_families = {
        13: ("USA_ibm_common_layer_strategy", "USA_ibm_proprietary_linux_strategy"),
        25: (
            "USA_ibm_community_boundary_protected",
            "USA_ibm_corporate_boundary_enforced",
        ),
        31: ("USA_ibm_linuxone_established", "USA_ibm_proprietary_mainframe_retained"),
        39: (
            "USA_ibm_maintainer_governance_protected",
            "USA_ibm_maintainer_crisis_exposed",
        ),
        40: ("USA_ibm_staffed_continuity", "USA_ibm_automated_continuity"),
        47: (
            "USA_ibm_retreat_to_software_platform",
            "USA_ibm_integrated_stack_retained",
        ),
    }
    for event_number, markers in marker_families.items():
        for marker in markers:
            assert f"set_country_flag = {marker}" in events[event_number]
            if event_number != 47:
                assert marker in effects

    first_ibm_route = _option_blocks(events[13])[0]
    assert "bonus = 0.05" in first_ibm_route
    assert "uses = 1" in first_ibm_route
    assert "category = CAT_computing_tech" in first_ibm_route
    for event_number in (28, 34):
        assert "USA_ibm_redhat_neutral" in events[event_number]
        assert "USA_ibm_redhat_absorbed" in events[event_number]
        assert f"USA_ibm_events.{event_number}.d_no_red_hat" in events[event_number]
    assert "USA_oem_storage_policy" not in events[39]
    assert "linux_system_effective_stewardship" in events[39]
    assert "linux_system_effective_support_model" in events[39]
    assert "USA_ibm_events.40.d_no_linuxone" in events[40]
    assert "USA_ibm_events.40.a_no_linuxone" in events[40]
    assert "USA_ibm_events.40.b_no_linuxone" in events[40]
    assert "USA_ibm_maintainer_crisis_occurred" in events[47]


def test_english_localisation_is_bom_prefixed_unique_and_complete():
    system = _shared_system()
    paths = tuple(ROOT / path for path in system["files"]["localisation"])
    declared_keys = set(system["localisation_keys"])
    declared_key_counts = {key: 0 for key in declared_keys}

    for path in paths:
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")
        text = path.read_text(encoding="utf-8-sig")
        assert re.search(r"(?m)^l_english:\s*$", text)
        assert not re.search(r"(?m)^ {2,}[^ #\r\n][^:]*:", text)
        for key in _localisation_keys(path):
            if key in declared_key_counts:
                declared_key_counts[key] += 1

    assert set(declared_key_counts.values()) == {1}
    global_text = GLOBAL_LOC_PATH.read_text(encoding="utf-8-sig")
    assert "linux_system_status:" not in global_text
    assert "—" not in global_text
    assert (
        'USA_ibm_events.39.t: "The Maintainer Governance Crisis"'
        in USA_LOC_PATH.read_text(encoding="utf-8-sig")
    )


def test_declared_native_reads_are_exact_and_system_never_writes_native_state():
    system = _shared_system()
    core_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            EFFECTS_PATH,
            TRIGGERS_PATH,
            ON_ACTIONS_PATH,
            EVENTS_PATH,
            IDEAS_PATH,
            DECISIONS_PATH,
            CATEGORY_PATH,
        )
    )
    native_token = r"(?:USA|ENG|GER|FRA|BRA|RAJ|SOV|CHI|POL|VEN)_[A-Za-z0-9_]+"
    native_target = rf"(?:[A-Za-z0-9_]+[.:])*({native_token})"
    flag_write = (
        r"(?:set|clr|modify)_"
        r"(?:character|country|country_pmc|global|mio|project|state|unit_leader)_flag"
    )
    variable_block_write = (
        r"(?:set_variable|add_to_variable|subtract_from_variable|multiply_variable|"
        r"divide_variable|modulo_variable|clamp_variable|randomize_variable|"
        r"set_variable_to_random)"
    )
    array_block_write = r"(?:add_to_array|remove_from_array|resize_array)"
    actual_reads = set()
    for pattern in (
        rf"(?:has_country_flag|has_idea|has_completed_focus)\s*=\s*{native_target}",
        rf"check_variable\s*=\s*\{{\s*(?:var\s*=\s*)?{native_target}",
    ):
        actual_reads.update(re.findall(pattern, core_text))
    assert actual_reads == set(system["allowed_native_reads"])

    writes = re.findall(
        rf"{flag_write}\s*=\s*(?:\{{\s*flag\s*=\s*)?{native_target}",
        core_text,
    )
    writes.extend(
        re.findall(
            rf"{flag_write}\s*=\s*\{{[^{{}}]*?\bflag\s*=\s*{native_target}",
            core_text,
            re.DOTALL,
        )
    )
    writes.extend(
        re.findall(
            rf"{variable_block_write}\s*=\s*\{{\s*(?:var\s*=\s*)?{native_target}",
            core_text,
        )
    )
    writes.extend(
        re.findall(
            rf"{variable_block_write}\s*=\s*\{{[^{{}}]*?\bvar\s*=\s*{native_target}",
            core_text,
            re.DOTALL,
        )
    )
    writes.extend(
        re.findall(
            rf"(?:clear|round)_variable\s*=\s*"
            rf"(?:\{{[^{{}}]*?\b(?:var|which)\s*=\s*)?{native_target}",
            core_text,
            re.DOTALL,
        )
    )
    writes.extend(
        re.findall(
            rf"{array_block_write}\s*=\s*\{{\s*(?:array\s*=\s*)?{native_target}",
            core_text,
        )
    )
    writes.extend(
        re.findall(
            rf"{array_block_write}\s*=\s*\{{[^{{}}]*?\barray\s*=\s*{native_target}",
            core_text,
            re.DOTALL,
        )
    )
    writes.extend(
        re.findall(
            rf"clear_array\s*=\s*" rf"(?:\{{[^{{}}]*?\barray\s*=\s*)?{native_target}",
            core_text,
            re.DOTALL,
        )
    )
    for output in ("value", "index"):
        writes.extend(
            re.findall(
                rf"(?:find_highest_in_array|find_lowest_in_array)\s*=\s*"
                rf"\{{[^{{}}]*?\b{output}\s*=\s*{native_target}",
                core_text,
                re.DOTALL,
            )
        )
    writes.extend(
        re.findall(
            rf"(?:add_ideas|remove_ideas|add_idea|remove_idea)\s*=\s*"
            rf"{native_target}",
            core_text,
        )
    )
    writes.extend(
        re.findall(
            rf"add_timed_idea\s*=\s*\{{[^{{}}]*?\bidea\s*=\s*{native_target}",
            core_text,
            re.DOTALL,
        )
    )
    writes.extend(
        re.findall(
            rf"(?:complete_national_focus|uncomplete_national_focus|unlock_national_focus)"
            rf"\s*=\s*(?:\{{\s*focus\s*=\s*)?{native_target}",
            core_text,
        )
    )
    writes.extend(
        re.findall(
            rf"(?:country_event|news_event)\s*=\s*"
            rf"(?:\{{[^{{}}]*?\bid\s*=\s*)?{native_target}",
            core_text,
            re.DOTALL,
        )
    )
    for idea_block in re.findall(
        r"(?:add_ideas|remove_ideas)\s*=\s*\{([^{}]*)\}", core_text, re.DOTALL
    ):
        writes.extend(re.findall(native_token, idea_block))
    assert writes == []
