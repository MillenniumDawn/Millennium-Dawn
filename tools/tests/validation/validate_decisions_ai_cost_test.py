"""Decisions whose ai_will_do ignores a money cost (issue #5738)."""

import pytest
import validate_decisions as V
from shared.suite import decision_factory, decisions_results_for
from validate_events import costly_scripted_effects

_CHECK = "validate_ai_will_do_ignores_cost"
_EFFECTS = costly_scripted_effects(
    ["pay_the_bill = {\n\tadd_to_variable = { treasury = -3 }\n}\n"]
)
_CHARGE = "\t\tadd_to_variable = { treasury = -5 }\n"
_FLAT = "\tai_will_do = { base = 10 }\n"
_GUARDED = (
    "\tai_will_do = {\n\t\tbase = 10\n\t\tmodifier = { factor = 0 "
    "has_active_mission = bankruptcy_incoming_collapse }\n\t}\n"
)


def _decision(*parts, name="dec_one"):
    return decision_factory(name + " = {\n" + "".join(parts) + "}")


def _effect(body, block="complete_effect"):
    return "\t" + block + " = {\n" + body + "\t}\n"


def _results(monkeypatch, *factories):
    monkeypatch.setattr(V, "load_cost_lookups", lambda validator: (_EFFECTS, {}))
    return decisions_results_for(list(factories), monkeypatch, _CHECK)


def test_flat_weight_on_a_treasury_charge_is_flagged(monkeypatch):
    results = _results(monkeypatch, _decision(_effect(_CHARGE), _FLAT))
    assert len(results) == 1
    assert results[0].startswith("dec_one")
    assert results[0].endswith("X.txt - ai_will_do ignores the treasury cost")


def test_missing_ai_will_do_is_flagged(monkeypatch):
    assert len(_results(monkeypatch, _decision(_effect(_CHARGE)))) == 1


def test_charge_through_a_scripted_effect_is_flagged(monkeypatch):
    decision = _decision(_effect("\t\tpay_the_bill = yes\n"), _FLAT)
    assert len(_results(monkeypatch, decision)) == 1


def test_remove_effect_charge_is_flagged(monkeypatch):
    decision = _decision("\tdays_remove = 30\n", _effect(_CHARGE, "remove_effect"))
    assert len(_results(monkeypatch, decision)) == 1


def test_both_money_kinds_are_listed_once(monkeypatch):
    decision = _decision(
        _effect(_CHARGE),
        _effect("\t\tadd_to_variable = { debt = 4 }\n", "remove_effect"),
        _FLAT,
    )
    results = _results(monkeypatch, decision)
    assert len(results) == 1
    assert results[0].endswith("ai_will_do ignores the debt, treasury cost")


def test_treasury_custom_cost_trigger_adds_the_note(monkeypatch):
    decision = _decision(
        "\tcustom_cost_trigger = { check_variable = { treasury > 5 } }\n",
        _effect(_CHARGE),
        _FLAT,
    )
    [result] = _results(monkeypatch, decision)
    assert result.endswith("(behind a treasury custom_cost_trigger; verify)")


@pytest.mark.parametrize(
    "parts",
    [
        (_effect(_CHARGE), _GUARDED),
        (_effect("\t\tadd_to_variable = { treasury = 5 }\n"), _FLAT),
        (_effect("\t\tadd_political_power = -50\n"), _FLAT),
        (_effect("\t\tFROM = {\n\t" + _CHARGE + "\t\t}\n"), _FLAT),
        (_effect(_CHARGE), "\tai_will_do = { base = 0 }\n"),
        (_effect(_CHARGE), _FLAT, "\tavailable = { is_ai = no }\n"),
        (_effect(_CHARGE), _FLAT, "\tvisible = { always = no }\n"),
        ("\tdays_mission_timeout = 90\n", _effect(_CHARGE)),
        (
            "\tdays_mission_timeout = 90\n\tselectable_mission = yes\n",
            _effect(_CHARGE, "remove_effect"),
            _FLAT,
        ),
    ],
    ids=[
        "bankruptcy modifier",
        "income",
        "political power only",
        "another country pays",
        "AI never takes it",
        "player only",
        "never visible",
        "plain mission",
        "selectable mission timeout",
    ],
)
def test_not_flagged(monkeypatch, parts):
    assert _results(monkeypatch, _decision(*parts)) == []


def test_zero_base_with_an_add_is_still_checked(monkeypatch):
    weights = (
        "\tai_will_do = {\n\t\tbase = 0\n"
        "\t\tmodifier = { add = 5 has_war = yes }\n\t}\n"
    )
    assert len(_results(monkeypatch, _decision(_effect(_CHARGE), weights))) == 1


def test_fractional_base_is_not_read_as_zero(monkeypatch):
    weights = "\tai_will_do = { base = 0.5 }\n"
    assert len(_results(monkeypatch, _decision(_effect(_CHARGE), weights))) == 1


def test_selectable_mission_complete_effect_is_checked(monkeypatch):
    decision = _decision(
        "\tdays_mission_timeout = 90\n\tselectable_mission = yes\n",
        _effect(_CHARGE),
        _FLAT,
    )
    assert len(_results(monkeypatch, decision)) == 1


def test_validator_reads_the_mods_scripted_effects(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/00_bills.txt",
        "pay_the_bill = {\n\tadd_to_variable = { treasury = -3 }\n}\n",
    )
    write_path(
        tmp_path,
        "common/decisions/Bills.txt",
        "bills_category = {\n\tdec_bill = {\n\t\tcomplete_effect = {\n"
        "\t\t\tpay_the_bill = yes\n\t\t}\n\t\tai_will_do = { base = 10 }\n\t}\n}\n",
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)
    validator.validate_ai_will_do_ignores_cost()

    assert [(issue.severity, issue.category) for issue in validator._issues] == [
        ("warning", "decision-ai-will-do-ignores-cost")
    ]
    assert "dec_bill" in validator._issues[0].message
