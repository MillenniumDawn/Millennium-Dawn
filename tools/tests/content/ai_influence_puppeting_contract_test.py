"""AI influence puppeting wiring contracts, not an HOI4 runtime simulation."""

import re

import pytest
from shared.paths import REPO_ROOT
from shared_utils import iter_statements, read_script

TRIGGERS = read_script(
    str(REPO_ROOT / "common/scripted_triggers/00_influence_scripted_triggers.txt")
)


def _block(script, name):
    matches = [body for key, _, body in iter_statements(script) if key == name]
    assert len(matches) == 1, name
    assert matches[0] is not None, name
    return matches[0]


def _shape(script):
    return [
        (key, _shape(body) if body is not None else value)
        for key, value, body in iter_statements(script)
    ]


@pytest.fixture(scope="module")
def puppet_trigger():
    return _block(TRIGGERS, "make_puppet_action_available")


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
            [("add_to_temp_variable", [("AI_country_score", "100")])],
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
    matches = [
        body
        for key, _, body in iter_statements(_block(script, effect))
        if key == "if" and _shape(_block(body, "limit")) == gate
    ]
    assert len(matches) == 1
    assert _shape(matches[0]) == [("limit", gate), *outcome]


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
