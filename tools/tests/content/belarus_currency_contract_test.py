"""Currency-spirit contracts, not an HOI4 runtime simulation."""

from pathlib import Path

import pytest
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statements, read_script
from validate_localisation import _parse_loc_keys_from_text

ROOT = Path(__file__).resolve().parents[3]
CURRENCY = "BLR_unstable_national_currency"
TIERS = (CURRENCY + "4", CURRENCY, CURRENCY + "2", CURRENCY + "3")
RECOVERY_FOCUSES = (
    "BLR_true_political_and_national_freedom",
    "BLR_Chinese_yuan",
    "BLR_Energy_conflict_over",
    "BLR_Linking_foreign_currency",
    "BLR_Market_Economy",
    "BLR_Communism_start",
)


def _identified_block(source, kind, identifier):
    blocks = [
        body
        for key, _, body in iter_statements(source)
        if key == kind
        and body is not None
        and ("id", identifier, None) in list(iter_statements(body))
    ]
    assert len(blocks) == 1, identifier
    return blocks[0]


@pytest.fixture(scope="module")
def sources():
    return {
        name: read_script(str(ROOT / path))
        for name, path in {
            "effects": "common/scripted_effects/99_BLR_scripted_effects.txt",
            "events": "events/belarus.txt",
            "focuses": "common/national_focus/05_belarus.txt",
            "ideas": "common/ideas/Belarusian.txt",
        }.items()
    }


def _run_currency(source, effects, ideas):
    fixture = EconomicScriptFixture(
        {}, predicates={"has_idea": lambda idea, _: idea in ideas}
    )
    for key, _, scalar, body in fixture.active(source):
        if key in effects:
            assert scalar == "yes"
            _run_currency(effects[key], effects, ideas)
        elif key == "swap_ideas":
            assert body is not None
            swap = {name: value for name, value, _ in iter_statements(body)}
            ideas.remove(swap["remove_idea"])
            ideas.add(swap["add_idea"])
        elif key == "remove_ideas":
            ideas.remove(scalar)
        elif key == "add_ideas":
            ideas.add(scalar)
        else:
            assert key in {
                "name",
                "log",
                "add_stability",
                "add_political_power",
                "country_event",
            }, key


# case: (initial tiers, sequence, expected tiers)
_TRANSITIONS = {
    "crisis_removed": ((), ("crisis",), ()),
    "crisis_worst": ((TIERS[0],), ("crisis",), (TIERS[0],)),
    "crisis_severe": ((TIERS[1],), ("crisis",), (TIERS[0],)),
    "crisis_moderate": ((TIERS[2],), ("crisis",), (TIERS[0],)),
    "crisis_mild": ((TIERS[3],), ("crisis",), (TIERS[0],)),
    "credit_removed": ((), ("credit",), ()),
    "credit_worst": ((TIERS[0],), ("credit",), (TIERS[2],)),
    "credit_severe": ((TIERS[1],), ("credit",), (TIERS[2],)),
    "credit_moderate": ((TIERS[2],), ("credit",), (TIERS[2],)),
    "credit_mild": ((TIERS[3],), ("credit",), (TIERS[3],)),
    "remove_all_tiers": (TIERS, ("remove",), ()),
    "remove_missing": ((), ("remove",), ()),
    "reform_before_credit": ((TIERS[1],), ("crisis", "remove", "credit"), ()),
    "lukashenko_removed": ((), ("lukashenko",), ()),
    "lukashenko_worst": ((TIERS[0],), ("lukashenko",), (TIERS[1],)),
}


@pytest.mark.parametrize(
    "initial,sequence,expected", _TRANSITIONS.values(), ids=_TRANSITIONS
)
def test_currency_transitions_preserve_recovery(sources, initial, sequence, expected):
    effects = {
        name: script_block(sources["effects"], name)
        for name in ("BLR_idea_currency_crisis", "BLR_remove_unstable_currency")
    }
    credit = _identified_block(sources["events"], "country_event", "belarus_another.16")
    tree = script_block(sources["focuses"], "focus_tree")
    lukashenko = _identified_block(tree, "focus", "BLR_Lykashenko")
    steps = {
        "crisis": effects["BLR_idea_currency_crisis"],
        "remove": effects["BLR_remove_unstable_currency"],
        "credit": script_block(credit, "option"),
        "lukashenko": script_block(
            script_block(lukashenko, "completion_reward"), "hidden_effect"
        ),
    }
    ideas = {"unrelated_idea", *initial}
    for step in sequence:
        _run_currency(steps[step], effects, ideas)
    assert ideas == {"unrelated_idea", *expected}


@pytest.mark.parametrize("focus", RECOVERY_FOCUSES)
def test_recovery_focus_removes_every_currency_tier(sources, focus):
    tree = script_block(sources["focuses"], "focus_tree")
    reward = script_block(_identified_block(tree, "focus", focus), "completion_reward")
    assert "BLR_remove_unstable_currency = yes" in reward


def test_each_crisis_option_runs_the_currency_crisis_effect(sources):
    crisis = _identified_block(sources["events"], "country_event", "belarus_another.40")
    options = [
        body
        for key, _, body in iter_statements(crisis)
        if key == "option" and body is not None
    ]
    assert len(options) == 3
    for option in options:
        assert ("BLR_idea_currency_crisis", "yes", None) in list(
            iter_statements(option)
        )


@pytest.mark.parametrize(
    "tier,stability,pressure",
    [
        (TIERS[0], -0.15, 0.30),
        (TIERS[1], -0.10, 0.20),
        (TIERS[2], -0.05, 0.10),
        (TIERS[3], -0.025, 0.05),
    ],
)
def test_currency_tiers_use_approved_monetary_penalties(
    sources, tier, stability, pressure
):
    country = script_block(script_block(sources["ideas"], "ideas"), "country")
    idea = script_block(country, tier)
    assert not any(key == "name" for key, _, _ in iter_statements(idea))
    modifiers = {}
    for key, value, nested in iter_statements(script_block(idea, "modifier")):
        assert value is not None and nested is None
        modifiers[key] = float(value)
    assert modifiers == {
        "stability_factor": stability,
        "currency_strength_modifier": -pressure,
        "inflation_gain_multiplier_modifier": pressure,
        "econ_cycle_upg_cost_multiplier_modifier": pressure,
    }


def test_currency_descriptions_explain_verified_removal_paths():
    english = dict(
        _parse_loc_keys_from_text(
            read_text(ROOT / "localisation/english/MD_focus_BLR_l_english.yml")
        )
    )
    for tier in TIERS:
        description = english[tier + "_desc"]
        assert description.count("§W--------------§!") == 1
        assert "$BLR_currency_recovery_tt$" in description
    footer = english["BLR_currency_recovery_tt"]
    assert "will be §RRemoved§!" in footer
    for focus in (
        "BLR_Energy_conflict_over",
        "BLR_true_political_and_national_freedom",
        "BLR_Linking_foreign_currency",
    ):
        assert focus in RECOVERY_FOCUSES
        assert english[focus]
        assert f"${focus}$" in footer
