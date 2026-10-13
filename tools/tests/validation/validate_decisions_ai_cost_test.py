"""Decisions whose ai_will_do ignores a money cost (issue #5738)."""

import pytest
import validate_decisions as V
from shared.suite import (
    decision_factory,
    decisions_results_for,
    issue_rows,
    run_validator,
)
from validate_events import costly_scripted_effects

_CATEGORY = "decision-ai-will-do-ignores-cost"
_BILL = "pay_the_bill = {\n\tadd_to_variable = { treasury = -3 }\n}\n"
_EFFECTS = costly_scripted_effects([_BILL])
_CHARGE = "\t\tadd_to_variable = { treasury = -5 }\n"
_FLAT = "\tai_will_do = { base = 10 }\n"
_GUARDED = (
    "\tai_will_do = {\n\t\tbase = 10\n\t\tmodifier = { factor = 0 "
    "has_active_mission = bankruptcy_incoming_collapse }\n\t}\n"
)
_ZERO_BASE_ADD = (
    "\tai_will_do = {\n\t\tbase = 0\n\t\tmodifier = { add = 5 has_war = yes }\n\t}\n"
)
_MISSION = "\tdays_mission_timeout = 90\n"
_SELECTABLE = _MISSION + "\tselectable_mission = yes\n"
_GATE = "\tcustom_cost_trigger = { check_variable = { treasury > 5 } }\n"


def _effect(body, block="complete_effect"):
    return "\t" + block + " = {\n" + body + "\t}\n"


_PAID = _effect(_CHARGE)
_TIMEOUT = _effect(_CHARGE, "remove_effect")

# name: (decision parts, what the finding says ai_will_do ignores, or None)
_CASES = {
    "flat weight": ((_PAID, _FLAT), "treasury cost"),
    "no ai_will_do": ((_PAID,), "treasury cost"),
    "scripted effect": ((_effect("\t\tpay_the_bill = yes\n"), _FLAT), "treasury cost"),
    "remove_effect": (("\tdays_remove = 30\n", _TIMEOUT), "treasury cost"),
    "two kinds listed once": (
        (
            _PAID,
            _effect("\t\tadd_to_variable = { debt = 4 }\n", "remove_effect"),
            _FLAT,
        ),
        "debt, treasury cost",
    ),
    "treasury cost gate": (
        (_GATE, _PAID, _FLAT),
        "treasury cost (behind a treasury custom_cost_trigger; verify)",
    ),
    "zero base with an add": ((_PAID, _ZERO_BASE_ADD), "treasury cost"),
    "fractional base": ((_PAID, "\tai_will_do = { base = 0.5 }\n"), "treasury cost"),
    "selectable mission": ((_SELECTABLE, _PAID, _FLAT), "treasury cost"),
    "bankruptcy modifier": ((_PAID, _GUARDED), None),
    "income": ((_effect("\t\tadd_to_variable = { treasury = 5 }\n"), _FLAT), None),
    "political power only": ((_effect("\t\tadd_political_power = -50\n"), _FLAT), None),
    "another country pays": (
        (_effect("\t\tFROM = {\n\t" + _CHARGE + "\t\t}\n"), _FLAT),
        None,
    ),
    "AI never takes it": ((_PAID, "\tai_will_do = { base = 0 }\n"), None),
    "player only": ((_PAID, _FLAT, "\tavailable = { is_ai = no }\n"), None),
    "never visible": ((_PAID, _FLAT, "\tvisible = { always = no }\n"), None),
    "plain mission": ((_MISSION, _PAID), None),
    "selectable mission timeout": ((_SELECTABLE, _TIMEOUT, _FLAT), None),
}


@pytest.mark.parametrize(("parts", "ignored"), _CASES.values(), ids=_CASES)
def test_ai_will_do_ignores_cost(monkeypatch, parts, ignored):
    monkeypatch.setattr(V, "load_cost_lookups", lambda validator: (_EFFECTS, {}))
    factory = decision_factory("dec_one = {\n" + "".join(parts) + "}")
    results = decisions_results_for(
        [factory], monkeypatch, "validate_ai_will_do_ignores_cost"
    )
    expected = f"{'dec_one':<55}X.txt - ai_will_do ignores the {ignored}"
    assert results == ([expected] if ignored else [])


def test_validator_reads_the_mods_scripted_effects(tmp_path, write_path):
    write_path(tmp_path, "common/scripted_effects/00_bills.txt", _BILL)
    write_path(
        tmp_path,
        "common/decisions/Bills.txt",
        "bills_category = {\n\tdec_bill = {\n\t\tcomplete_effect = {\n"
        "\t\t\tpay_the_bill = yes\n\t\t}\n\t\tai_will_do = { base = 10 }\n\t}\n}\n",
    )
    rows = issue_rows(run_validator(V.Validator, tmp_path))

    assert [message for category, message, _, _ in rows if category == _CATEGORY] == [
        f"{'dec_bill':<55}Bills.txt - ai_will_do ignores the treasury cost"
    ]
