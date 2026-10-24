"""Source contracts for the PR #5989 internal-faction modifier cleanup.

These checks do not prove whether swap_ideas invokes on_remove in the engine.
"""

from pathlib import Path

import pytest
from shared.suite import read_text
from shared_utils import iter_statements, strip_comments

ROOT = Path(__file__).resolve().parents[3]
IDEAS_SOURCE = strip_comments(
    read_text(ROOT / "common/ideas/AA_law_internal_factions.txt")
)
EFFECTS_SOURCE = strip_comments(
    read_text(ROOT / "common/scripted_effects/00_internal_faction_effects.txt")
)


def _blocks(body, name):
    return [block for key, _, block in iter_statements(body) if key == name and block]


def _one_block(body, name):
    blocks = _blocks(body, name)
    assert len(blocks) == 1, f"expected one {name} block, found {len(blocks)}"
    return blocks[0]


def _modifier(block):
    return next((v for k, v, _ in iter_statements(block) if k == "modifier"), None)


def _faction_ideas():
    factions = _one_block(_one_block(IDEAS_SOURCE, "ideas"), "internal_factions")
    return {key: block for key, _, block in iter_statements(factions) if block}


def _initializer_branches():
    initializer = _one_block(
        EFFECTS_SOURCE, "initialize_internal_faction_dynamic_modifiers"
    )
    return _blocks(initializer, "if")


def _faction_modifiers():
    """Idea -> the dynamic modifier the shared initializer adds for it."""
    pairs = {}
    for branch in _initializer_branches():
        limit = " ".join(_blocks(branch, "limit"))
        ideas = [v for k, v, _ in iter_statements(limit) if k == "has_idea"]
        added = [_modifier(b) for b in _blocks(branch, "add_dynamic_modifier")]
        if len(ideas) == 1 and len(added) == 1:
            pairs[ideas[0]] = added[0]
    return pairs


FACTION_MODIFIERS = _faction_modifiers()


def _removes(body, modifier):
    """Whether these effects remove `modifier` without a has_idea or always = no gate."""
    for key, _, block in iter_statements(body):
        if not block:
            continue
        if key == "remove_dynamic_modifier" and _modifier(block) == modifier:
            return True
        if key in {"if", "else_if"}:
            gates = iter_statements(" ".join(_blocks(block, "limit")))
            if any(k == "has_idea" or (k, v) == ("always", "no") for k, v, _ in gates):
                continue
        if key in {"if", "else_if", "else", "hidden_effect"} and _removes(
            block, modifier
        ):
            return True
    return False


def _unconditional_effects(body):
    for key, scalar, nested in iter_statements(body):
        if key == "hidden_effect" and nested:
            yield from _unconditional_effects(nested)
        else:
            yield key, scalar, nested


def test_every_initialized_modifier_belongs_to_a_faction():
    added = sum(
        len(_blocks(branch, "add_dynamic_modifier"))
        for branch in _initializer_branches()
    )
    assert FACTION_MODIFIERS and len(FACTION_MODIFIERS) == added
    assert set(FACTION_MODIFIERS) <= set(_faction_ideas())


@pytest.mark.parametrize(("idea", "modifier"), FACTION_MODIFIERS.items())
def test_idea_on_remove_clears_its_modifier(idea, modifier):
    assert _removes(_one_block(_faction_ideas()[idea], "on_remove"), modifier)


@pytest.mark.parametrize(("idea", "modifier"), FACTION_MODIFIERS.items())
def test_fallback_clears_its_modifier_after_the_faction_leaves(idea, modifier):
    cleanup = _one_block(EFFECTS_SOURCE, "if_no_longer_has_faction_clear_previous")
    assert any(
        ("has_idea", idea, None) in iter_statements(absent)
        and _removes(branch, modifier)
        for branch in _blocks(cleanup, "if")
        for absent in _blocks(" ".join(_blocks(branch, "limit")), "NOT")
    )


@pytest.mark.parametrize("idea", FACTION_MODIFIERS)
def test_every_faction_on_add_runs_the_swap_fallback(idea):
    on_add = _one_block(_faction_ideas()[idea], "on_add")
    assert ("if_no_longer_has_faction_clear_previous", "yes", None) in list(
        _unconditional_effects(on_add)
    )


# case: (effects, whether they remove `target`)
_REMOVAL_CASES = {
    "direct": ("remove_dynamic_modifier = { modifier = target }", True),
    "presence guard": (
        "if = { limit = { has_dynamic_modifier = { modifier = target } } "
        "remove_dynamic_modifier = { modifier = target } }",
        True,
    ),
    "hidden": (
        "hidden_effect = { remove_dynamic_modifier = { modifier = target } }",
        True,
    ),
    "wrong modifier": ("remove_dynamic_modifier = { modifier = other }", False),
    "idea gate": (
        "if = { limit = { has_idea = faction } "
        "remove_dynamic_modifier = { modifier = target } }",
        False,
    ),
    "disabled": (
        "if = { limit = { always = no } "
        "remove_dynamic_modifier = { modifier = target } }",
        False,
    ),
    "tooltip only": (
        "effect_tooltip = { remove_dynamic_modifier = { modifier = target } }",
        False,
    ),
}


@pytest.mark.parametrize(
    ("body", "removes"), _REMOVAL_CASES.values(), ids=_REMOVAL_CASES
)
def test_removal_ignores_gated_and_display_only_effects(body, removes):
    assert _removes(body, "target") is removes
