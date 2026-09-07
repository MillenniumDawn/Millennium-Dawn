import re
from pathlib import Path

import pytest
from great_ai_race_state_model_test import _extract_block, _parse_race_script

ROOT = Path(__file__).resolve().parents[2]
COUNTRY_TRIGGERS = {"is_subject", "is_subject_of", "is_in_faction_with"}


def _body(statements, name):
    matches = [value for key, _op, value in statements if key == name]
    assert len(matches) == 1, f"Expected one {name}, found {len(matches)}"
    return matches[0]


def _walk(statements):
    for key, op, value in statements:
        yield key, op, value
        if isinstance(value, list):
            yield from _walk(value)


@pytest.fixture(scope="module")
def investment_gates():
    source = (ROOT / "events/investments_events.txt").read_text(encoding="utf-8")
    events = [
        _parse_race_script(_extract_block(source, match.start()))["country_event"]
        for match in re.finditer(r"(?m)^country_event\s*=\s*\{", source)
    ]
    event = next(
        body for body in events if _body(body, "id") == "investments_event.500"
    )
    guards = []
    for key, _op, country in _walk(_body(event, "immediate")):
        if key != "var:AI_best_country":
            continue
        for statement, _op, guard in country:
            if statement != "if":
                continue
            for effect, _op, loop in guard:
                if (
                    effect == "for_each_scope_loop"
                    and ("array", "=", "controlled_states") in loop
                ):
                    guards.append((guard, loop))
    assert len(guards) == 1
    guard, loop = guards[0]
    return _body(guard, "limit"), _body(_body(loop, "if"), "limit")


def _country_condition(statements, subject_of, same_faction, at_war):
    def evaluate(key, op, value):
        assert op == "="
        if key == "OR":
            return any(evaluate(*statement) for statement in value)
        if key == "check_variable":
            variable, comparison, expected = value[0]
            assert len(value) == 1
            assert (variable, comparison) == ("tgt_at_war_with_investor", "=")
            return int(at_war) == int(expected)
        if key == "is_subject":
            return (subject_of is not None) == (value == "yes")
        if key == "is_subject_of":
            assert value == "ROOT"
            return subject_of == "investor"
        if key == "is_in_faction_with":
            assert value == "ROOT"
            return same_faction
        raise AssertionError(f"Unsupported country eligibility trigger {key}")

    return all(evaluate(*statement) for statement in statements)


def test_investment_diplomacy_gate_runs_before_entering_state_scope(investment_gates):
    country_gate, state_gate = investment_gates
    assert COUNTRY_TRIGGERS <= {key for key, _op, _value in _walk(country_gate)}
    assert COUNTRY_TRIGGERS.isdisjoint(key for key, _op, _value in _walk(state_gate))


@pytest.mark.parametrize(
    "subject_of,same_faction,at_war,expected",
    [
        (None, False, False, True),
        (None, True, False, True),
        ("investor", False, False, True),
        ("other", False, False, False),
        ("other", True, False, True),
        (None, False, True, False),
        (None, True, True, False),
        ("investor", False, True, False),
        ("other", True, True, False),
    ],
)
def test_investment_country_eligibility(
    investment_gates, subject_of, same_faction, at_war, expected
):
    country_gate, _state_gate = investment_gates
    assert (
        _country_condition(country_gate, subject_of, same_faction, at_war) is expected
    )
