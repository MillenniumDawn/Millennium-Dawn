"""AI influence puppeting wiring contracts, not an HOI4 runtime simulation."""

import re

import pytest
from shared.paths import REPO_ROOT
from shared_utils import (
    extract_block_from_text,
    iter_statement_ops,
    iter_statements,
    read_script,
)

TRIGGERS = read_script(
    str(REPO_ROOT / "common/scripted_triggers/00_influence_scripted_triggers.txt")
)
SCORING = read_script(
    str(REPO_ROOT / "common/scripted_effects/99_AI_influence_scripted_effects.txt")
)


def _block(script, name):
    matches = [body for key, _, body in iter_statements(script) if key == name]
    assert len(matches) == 1, name
    assert matches[0] is not None, name
    return matches[0]


def _shape(script):
    return [
        (
            (key, _shape(body) if body is not None else value)
            if operator == "="
            else (key, operator, value)
        )
        for key, operator, value, body in iter_statement_ops(script)
    ]


def _rule(script, condition):
    matches = [
        body
        for key, _, body in iter_statements(script)
        if key == "if" and _shape(_block(body, "limit")) == condition
    ]
    assert len(matches) == 1, condition
    return matches[0]


@pytest.fixture(scope="module")
def influence_scoring():
    return _block(SCORING, "AI_influence_country_selection_calculation")


@pytest.fixture(scope="module")
def saturation_rule(influence_scoring):
    loop = _block(influence_scoring, "for_loop_effect")
    assert ("value", "v") in _shape(loop)
    entry = _block(loop, "if")
    owner = _block(_block(entry, "limit"), "check_variable")
    assert re.fullmatch(r"\s*influence_array\^v\s*=\s*PREV\.id\s*", owner)
    matches = [
        body
        for key, _, body in iter_statements(entry)
        if key == "if" and ("coup_is_available", "no") in _shape(_block(body, "limit"))
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture(scope="module")
def puppet_trigger():
    return _block(TRIGGERS, "make_puppet_action_available")


@pytest.fixture(scope="module")
def influence_pulse():
    script = read_script(str(REPO_ROOT / "common/on_actions/MD_on_actions.txt"))
    anchor = "un_check_if_valid_for_sanctions = yes"
    assert script.count(anchor) == 1
    start = script.index("if = {", script.index(anchor))
    pulse, end = extract_block_from_text(script, start)
    assert end > start
    return pulse


@pytest.mark.parametrize(
    "influence,eligible",
    [(79.998, False), (79.999, False), (80, True), (80.999, True), (81, True)],
)
def test_ai_and_player_puppeting_share_the_eighty_percent_boundary(
    puppet_trigger, influence, eligible
):
    player = _block(
        _block(TRIGGERS, "is_top_eighty_influencer"), "custom_trigger_tooltip"
    )
    thresholds = []
    for script in (puppet_trigger, player):
        checks = [
            body for key, _, body in iter_statements(script) if key == "check_variable"
        ]
        assert len(checks) == 2
        assert checks[1] is not None
        match = re.fullmatch(r"\s*influence_array_val\^0\s*>\s*([0-9.]+)\s*", checks[1])
        assert match is not None
        thresholds.append(float(match[1]))
    assert thresholds[0] == thresholds[1]
    assert (influence > thresholds[0]) is eligible


@pytest.mark.parametrize(
    "filename,effect,outcome",
    [
        (
            "99_AI_influence_scripted_effects.txt",
            "AI_influence_country_selection_calculation",
            [
                ("add_to_temp_variable", [("AI_country_score", "50")]),
                (
                    "if",
                    [
                        (
                            "limit",
                            [
                                ("PREV", [("has_navy_size", [("size", "<", "1")])]),
                                ("NOT", [("is_on_same_continent_as", "PREV")]),
                                ("NOT", [("is_neighbor_of", "PREV")]),
                            ],
                        ),
                        ("add_to_temp_variable", [("AI_country_score", "-20")]),
                    ],
                ),
            ],
        ),
        (
            "00_influence_scripted_effects.txt",
            "spread_influence",
            [("make_puppet_action", "yes")],
        ),
    ],
)
def test_target_bonus_and_execution_use_the_same_puppeting_gate(
    filename, effect, outcome
):
    script = read_script(str(REPO_ROOT / "common/scripted_effects" / filename))
    gate = [("make_puppet_action_available", "yes")]
    assert _shape(_rule(_block(script, effect), gate)) == [("limit", gate), *outcome]


def test_disable_ai_puppeting_rule_gates_every_target(puppet_trigger):
    assert _shape(_block(puppet_trigger, "has_game_rule")) == [
        ("rule", "rule_disable_ai_influence_puppeting"),
        ("option", "no"),
    ]
    rules = read_script(str(REPO_ROOT / "common/game_rules/00_game_rules.txt"))
    rule = _block(rules, "rule_disable_ai_influence_puppeting")
    assert ("name", "no") in _shape(_block(rule, "default"))
    assert ("name", "yes") in _shape(_block(rule, "option"))


def test_western_outlook_rule_checks_the_influencing_country(puppet_trigger):
    gates = [body for key, _, body in iter_statements(puppet_trigger) if key == "if"]
    matches = [
        body
        for body in gates
        if _shape(_block(body, "limit"))
        == [
            (
                "has_game_rule",
                [("rule", "rule_disable_western_outlook_features"), ("option", "yes")],
            )
        ]
    ]
    assert len(matches) == 1
    assert _shape(_block(matches[0], "PREV")) == [
        ("NOT", [("has_government", "democratic")])
    ]


def test_china_north_korea_exception_is_preserved(puppet_trigger):
    gates = [body for key, _, body in iter_statements(puppet_trigger) if key == "if"]
    matches = [
        body
        for body in gates
        if _shape(_block(body, "limit"))
        == [("original_tag", "NKO"), ("PREV", [("original_tag", "CHI")])]
    ]
    assert len(matches) == 1
    assert ("always", "no") in _shape(matches[0])


def test_puppeting_requires_matching_outlooks_and_an_independent_peaceful_target(
    puppet_trigger,
):
    shape = _shape(puppet_trigger)
    assert ("has_government", "PREV") in shape
    assert ("is_subject", "no") in shape
    assert ("has_war", "no") in shape
    checks = [
        body
        for key, _, body in iter_statements(puppet_trigger)
        if key == "check_variable"
    ]
    assert checks[0] is not None
    assert re.fullmatch(r"\s*influence_array\^0\s*=\s*PREV\s*", checks[0])


@pytest.mark.parametrize(
    "at_war,in_crisis,expected_chance",
    [(False, False, 100), (True, False, 50), (False, True, 50), (True, True, 50)],
)
def test_monthly_influence_throttle_does_not_stack(
    influence_pulse, at_war, in_crisis, expected_chance
):
    throttle = _block(influence_pulse, "if")
    conditions = _block(_block(throttle, "limit"), "OR")
    assert _shape(conditions) == [
        ("has_war", "yes"),
        ("ai_has_major_economic_problems", "yes"),
    ]
    random = _block(throttle, "random")
    assert _shape(random) == [("chance", "50"), ("country_event", "influence.500")]
    assert _shape(_block(influence_pulse, "else")) == [
        ("country_event", "influence.500")
    ]
    country = {"has_war": at_war, "ai_has_major_economic_problems": in_crisis}
    throttled = any(country[key] for key, _, _ in iter_statements(conditions))
    chance = int(dict(_shape(random))["chance"]) if throttled else 100
    assert chance == expected_chance


def test_monthly_influence_keeps_ai_pp_and_bankruptcy_guards(influence_pulse):
    guard = _shape(_block(influence_pulse, "limit"))
    assert ("is_ai", "yes") in guard
    assert ("has_political_power", ">", "200") in guard
    assert ("NOT", [("has_active_mission", "bankruptcy_incoming_collapse")]) in guard


@pytest.mark.parametrize("no_navy", [False, True])
@pytest.mark.parametrize("same_continent", [False, True])
@pytest.mark.parametrize("neighbor", [False, True])
def test_overseas_penalty_exempts_border_neighbors(
    influence_scoring, no_navy, same_continent, neighbor
):
    bonus = _rule(influence_scoring, [("make_puppet_action_available", "yes")])
    penalty = _block(bonus, "if")
    assert _shape(_block(penalty, "limit")) == [
        ("PREV", [("has_navy_size", [("size", "<", "1")])]),
        ("NOT", [("is_on_same_continent_as", "PREV")]),
        ("NOT", [("is_neighbor_of", "PREV")]),
    ]
    score = int(dict(_shape(_block(bonus, "add_to_temp_variable")))["AI_country_score"])
    if no_navy and not same_continent and not neighbor:
        score += int(
            dict(_shape(_block(penalty, "add_to_temp_variable")))["AI_country_score"]
        )
    assert score == (30 if no_navy and not same_continent and not neighbor else 50)


@pytest.mark.parametrize("subject", [False, True])
def test_existing_subjects_have_a_soft_target_scope_penalty(influence_scoring, subject):
    condition = [("is_subject", "yes")]
    rule = _rule(influence_scoring, condition)
    assert _shape(rule) == [
        ("limit", condition),
        ("add_to_temp_variable", [("AI_country_score", "-20")]),
    ]
    score = int(dict(_shape(_block(rule, "add_to_temp_variable")))["AI_country_score"])
    assert (score if subject else 0) == (-20 if subject else 0)
    selection = _block(SCORING, "AI_select_influence_target")
    target = _block(_block(selection, "for_each_scope_loop"), "if")
    assert _shape(_block(target, "limit")) == [("THIS", [("exists", "yes")])]


@pytest.mark.parametrize("production", [0, 9.999, 10, 1000])
def test_resource_bonus_is_capped_and_uses_target_production(
    influence_scoring, production
):
    condition = [("check_variable", [("total_resource_amount", ">", "9.999")])]
    rule = _rule(influence_scoring, condition)
    assert _shape(rule) == [
        ("limit", condition),
        ("add_to_temp_variable", [("AI_country_score", "20")]),
    ]
    comparison = _shape(_block(_block(rule, "limit"), "check_variable"))[0]
    score = int(dict(_shape(_block(rule, "add_to_temp_variable")))["AI_country_score"])
    assert (score if production > float(comparison[2]) else 0) == (
        20 if production >= 10 else 0
    )


def test_resource_total_covers_domestic_production_of_all_defined_resources():
    money = read_script(str(REPO_ROOT / "common/scripted_effects/00_money_system.txt"))
    update = _block(money, "update_state_variables")
    totals = [
        body
        for key, _, body in iter_statements(update)
        if key == "set_variable"
        and body is not None
        and any(name == "total_resource_amount" for name, _, _ in iter_statements(body))
    ]
    assert len(totals) == 1
    fields = _shape(_block(totals[0], "total_resource_amount"))
    assert fields[0][0] == "value"
    assert all(key == "add" for key, _ in fields[1:])
    resources = read_script(str(REPO_ROOT / "common/resources/00_resources.txt"))
    names = {key for key, _, _ in iter_statements(_block(resources, "resources"))}
    assert {value for _, value in fields} == {
        f"resource_produced@{name}" for name in names
    }
    assert len(fields) == len(names)
    assert ("update_state_variables", "yes") in _shape(
        _block(money, "ingame_update_setup")
    )


@pytest.mark.parametrize("same_continent", [False, True])
@pytest.mark.parametrize("independent", [False, True])
@pytest.mark.parametrize("same_outlook", [False, True])
def test_regional_integration_bonus_requires_independence_and_matching_outlook(
    influence_scoring, same_continent, independent, same_outlook
):
    condition = [("country_exists", "PREV"), ("is_on_same_continent_as", "PREV")]
    rule = _rule(influence_scoring, condition)
    integration = _block(rule, "if")
    assert _shape(_block(integration, "limit")) == [
        ("is_subject", "no"),
        ("has_government", "PREV"),
    ]
    score = 0
    if same_continent:
        score += int(
            dict(_shape(_block(rule, "add_to_temp_variable")))["AI_country_score"]
        )
        if independent and same_outlook:
            score += int(
                dict(_shape(_block(integration, "add_to_temp_variable")))[
                    "AI_country_score"
                ]
            )
    assert score == (
        25 + (10 if independent and same_outlook else 0) if same_continent else 0
    )


@pytest.mark.parametrize("influence", [94.998, 94.999, 95, 100])
@pytest.mark.parametrize("coup", [False, True])
@pytest.mark.parametrize("manipulation", [False, True])
@pytest.mark.parametrize("puppeting", [False, True])
def test_saturation_penalty_requires_own_dominance_and_no_available_political_action(
    saturation_rule, influence, coup, manipulation, puppeting
):
    limit = _block(saturation_rule, "limit")
    comparison = _block(limit, "check_variable")
    match = re.fullmatch(r"\s*influence_array_val\^v\s*>\s*([0-9.]+)\s*", comparison)
    assert match is not None
    gates = [
        (key, value)
        for key, value, _ in iter_statements(limit)
        if key != "check_variable"
    ]
    assert gates == [
        ("coup_is_available", "no"),
        ("manipulate_politics_action_available", "no"),
        ("make_puppet_action_available", "no"),
    ]
    available = {
        "coup_is_available": coup,
        "manipulate_politics_action_available": manipulation,
        "make_puppet_action_available": puppeting,
    }
    penalized = influence > float(match[1]) and all(
        available[key] == (value == "yes") for key, value in gates
    )
    score = int(
        dict(_shape(_block(saturation_rule, "add_to_temp_variable")))[
            "AI_country_score"
        ]
    )
    assert (score if penalized else 0) == (
        -50 if influence >= 95 and not any(available.values()) else 0
    )
