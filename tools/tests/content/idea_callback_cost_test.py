"""Money commitments of representative live ideas and callbacks."""

from pathlib import Path

import pytest
from validate_events import (
    CostLookups,
    _scripted_effect_bodies,
    chooser_costs,
    costly_scripted_effects,
    effect_payment_nodes,
    idea_callbacks,
    money_commitment_effects,
    resolve_payments,
)
from validator_common import idea_money_modifiers, script_commits_money, strip_comments

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def graph():
    paths = (
        "common/ideas/AA_law_budget.txt",
        "common/ideas/AA_law_economics.txt",
        "common/ideas/czech_republic.txt",
    )
    texts = [
        strip_comments((ROOT / path).read_text(encoding="utf-8-sig")) for path in paths
    ]
    ideas = idea_money_modifiers(texts)
    effect_texts = [
        strip_comments(path.read_text(encoding="utf-8-sig"))
        for path in (ROOT / "common/scripted_effects").glob("*.txt")
    ]
    bodies = _scripted_effect_bodies(effect_texts)
    lookups = CostLookups(
        costly_scripted_effects(effect_texts),
        {},
        money_commitment_effects(bodies, ideas),
        ideas,
        idea_callbacks(texts),
    )
    return lookups, resolve_payments({}, effect_payment_nodes(bodies, lookups))


@pytest.mark.parametrize(
    "effect",
    [
        "swap_ideas = { remove_idea = bureau_02 add_idea = bureau_01 }",
        "swap_ideas = { remove_idea = bureau_01 add_idea = bureau_02 }",
        "add_ideas = stable_growth",
        "swap_ideas = { remove_idea = recession add_idea = stable_growth }",
        "add_timed_idea = { idea = CZE_tatra_expansion1_idea days = 440 }",
    ],
)
def test_live_idea_callbacks_do_not_prove_no_cost(graph, effect):
    lookups, payments = graph
    # Includes unresolved callback costs; this is not a claim of a proven charge.
    assert "money" in chooser_costs(effect, lookups, payments, frozenset({"CZE"}))


def test_live_bureaucracy_cut_still_has_no_modifier_increase(graph):
    lookups, _payments = graph
    effect = "swap_ideas = { remove_idea = bureau_02 add_idea = bureau_01 }"
    assert not script_commits_money(effect, lookups.ideas)
