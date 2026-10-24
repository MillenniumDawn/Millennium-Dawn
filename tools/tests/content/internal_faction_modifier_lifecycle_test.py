"""Source contracts for the PR #5989 internal-faction modifier cleanup.

These checks do not prove whether swap_ideas invokes on_remove in the engine.
"""

import re
from pathlib import Path

import pytest
from shared.suite import read_text
from shared_utils import (
    blank_quoted_strings,
    extract_block_from_text,
    iter_statements,
    strip_comments,
)

ROOT = Path(__file__).resolve().parents[3]
IDEAS_SOURCE = strip_comments(
    read_text(ROOT / "common/ideas/AA_law_internal_factions.txt")
)
EFFECTS_SOURCE = strip_comments(
    read_text(ROOT / "common/scripted_effects/00_internal_faction_effects.txt")
)

# Internal faction idea id to the dynamic modifier it adds and removes.
FACTION_MODIFIERS = {
    "small_medium_business_owners": "small_medium_business_owners_dynamic_modifier",
    "international_bankers": "international_bankers_dynamic_modifier",
    "fossil_fuel_industry": "fossil_fuel_industry_dynamic_modifier",
    "industrial_conglomerates": "industrial_conglomerates_dynamic_modifier",
    "oligarchs": "oligarchs_dynamic_modifier",
    "maritime_industry": "maritime_industry_dynamic_modifier",
    "defense_industry": "defense_industry_dynamic_modifier",
    "the_military": "the_military_dynamic_modifier",
    "intelligence_community": "intelligence_community_dynamic_modifier",
    "labour_unions": "labour_unions_dynamic_modifier",
    "landowners": "landowners_dynamic_modifier",
    "farmers": "farmers_dynamic_modifier",
    "communist_cadres": "communist_cadres_dynamic_modifier",
    "the_priesthood": "the_priesthood_dynamic_modifier",
    "the_ulema": "the_ulema_dynamic_modifier",
    "the_clergy": "the_clergy_dynamic_modifier",
    "wahabi_ulema": "wahabi_ulema_dynamic_modifier",
    "the_donju": "the_donju_dynamic_modifier",
    "saudi_royal_family": "saudi_royal_family_dynamic_modifier",
    "iranian_quds_force": "iranian_quds_force_dynamic_modifier",
    "foreign_jihadis": "foreign_jihadis_force_dynamic_modifier",
    "wall_street": "wall_street_force_dynamic_modifier",
    "chaebols": "chaebols_force_dynamic_modifier",
}


def _named_blocks(body, name):
    return [
        nested
        for key, _, nested in iter_statements(body)
        if key == name and nested is not None
    ]


def _one_named_block(body, name):
    blocks = _named_blocks(body, name)
    assert len(blocks) == 1, f"expected one {name} block, found {len(blocks)}"
    return blocks[0]


def _faction_idea_blocks(source=IDEAS_SOURCE):
    ideas = _one_named_block(source, "ideas")
    factions = _one_named_block(ideas, "internal_factions")
    return {
        key: block for key, _, block in iter_statements(factions) if block is not None
    }


def _is_modifier_effect(statement, effect, modifier):
    key, scalar, arguments = statement
    return (
        key == effect
        and scalar is None
        and arguments is not None
        and list(iter_statements(arguments)) == [("modifier", modifier, None)]
    )


def _all_modifier_arguments(body, effect):
    values = []
    for key, _, nested in iter_statements(body):
        if key == effect and nested is not None:
            values.extend(
                scalar
                for arg, scalar, _ in iter_statements(nested)
                if arg == "modifier" and scalar is not None
            )
        elif nested is not None:
            values.extend(_all_modifier_arguments(nested, effect))
    return values


def _assert_guarded_removal(body, modifier):
    removals = _all_modifier_arguments(body, "remove_dynamic_modifier")
    assert removals == [
        modifier
    ], f"expected one removal of {modifier}, found {removals}"

    guarded = False
    for conditional in _named_blocks(body, "if"):
        limits = _named_blocks(conditional, "limit")
        if len(limits) != 1:
            continue
        guards = list(iter_statements(limits[0]))
        if (
            len(guards) == 1
            and _is_modifier_effect(guards[0], "has_dynamic_modifier", modifier)
            and any(
                _is_modifier_effect(statement, "remove_dynamic_modifier", modifier)
                for statement in iter_statements(conditional)
            )
        ):
            guarded = True
            break

    assert guarded, f"{modifier} removal must use its matching presence guard"


def _assert_idea_on_remove(idea_block, modifier):
    on_remove = _one_named_block(idea_block, "on_remove")
    _assert_guarded_removal(on_remove, modifier)


def _fallback_branch(cleanup, idea):
    matching = []
    for conditional in _named_blocks(cleanup, "if"):
        limits = _named_blocks(conditional, "limit")
        if len(limits) != 1:
            continue
        for absence_check in _named_blocks(limits[0], "NOT"):
            if list(iter_statements(absence_check)) == [("has_idea", idea, None)]:
                matching.append((conditional, limits[0]))

    assert (
        len(matching) == 1
    ), f"expected one cleanup branch for absent {idea}, found {len(matching)}"
    branch, limit = matching[0]
    conditions = list(iter_statements(limit))
    assert (
        len(conditions) == 2
        and (
            "has_variable",
            f"{idea}_opinion",
            None,
        )
        in conditions
    ), f"cleanup for {idea} must require only absence and prior opinion"
    return branch


def _assert_fallback_removal(cleanup, idea, modifier):
    branch = _fallback_branch(cleanup, idea)
    _assert_guarded_removal(branch, modifier)


def _assert_on_add_cleanup(idea_block):
    on_add = _one_named_block(idea_block, "on_add")
    calls = [
        (key, scalar, nested)
        for key, scalar, nested in _unconditional_effects(on_add)
        if key == "if_no_longer_has_faction_clear_previous"
    ]
    assert calls == [("if_no_longer_has_faction_clear_previous", "yes", None)]


def _unconditional_effects(body):
    for key, scalar, nested in iter_statements(body):
        if key == "hidden_effect" and nested is not None:
            yield from _unconditional_effects(nested)
        else:
            yield key, scalar, nested


def _wrong_removal_modifier(text, modifier):
    match = re.search(r"\bremove_dynamic_modifier\s*=\s*\{", blank_quoted_strings(text))
    assert match is not None, "expected modifier removal for mutation"
    arguments, end = extract_block_from_text(text, match.start())
    assert end > 0 and list(iter_statements(arguments)) == [
        ("modifier", modifier, None)
    ]
    return (
        text[: match.start()]
        + "remove_dynamic_modifier = { modifier = wrong_dynamic_modifier }"
        + text[end:]
    )


def _remove_named_block(text, name):
    match = re.search(rf"\b{re.escape(name)}\s*=\s*\{{", blank_quoted_strings(text))
    assert match is not None, f"expected to find {name} block for mutation"
    _, end = extract_block_from_text(text, match.start())
    assert end > 0, f"expected a balanced {name} block for mutation"
    return text[: match.start()] + text[end:]


def test_main_contains_the_23_repaired_internal_faction_ideas():
    assert set(_faction_idea_blocks()) == set(FACTION_MODIFIERS)


@pytest.mark.parametrize(
    ("idea", "modifier"), FACTION_MODIFIERS.items(), ids=FACTION_MODIFIERS.keys()
)
def test_idea_on_remove_clears_its_modifier_for_plain_removal(idea, modifier):
    _assert_idea_on_remove(_faction_idea_blocks()[idea], modifier)


@pytest.mark.parametrize(
    ("idea", "modifier"), FACTION_MODIFIERS.items(), ids=FACTION_MODIFIERS.keys()
)
def test_fallback_clears_its_modifier_after_the_faction_leaves(idea, modifier):
    cleanup = _one_named_block(
        EFFECTS_SOURCE, "if_no_longer_has_faction_clear_previous"
    )
    _assert_fallback_removal(cleanup, idea, modifier)


@pytest.mark.parametrize("idea", FACTION_MODIFIERS, ids=FACTION_MODIFIERS.keys())
def test_every_faction_on_add_wires_the_swap_cleanup_fallback(idea):
    _assert_on_add_cleanup(_faction_idea_blocks()[idea])


def test_wrong_idea_modifier_mutation_is_rejected():
    idea = "small_medium_business_owners"
    modifier = FACTION_MODIFIERS[idea]
    on_remove = _one_named_block(_faction_idea_blocks()[idea], "on_remove")
    mutated = _wrong_removal_modifier(on_remove, modifier)
    with pytest.raises(AssertionError, match="expected one removal"):
        _assert_guarded_removal(mutated, modifier)


def test_missing_idea_modifier_mutation_is_rejected():
    idea = "small_medium_business_owners"
    modifier = FACTION_MODIFIERS[idea]
    on_remove = _one_named_block(_faction_idea_blocks()[idea], "on_remove")
    mutated = _remove_named_block(on_remove, "remove_dynamic_modifier")
    with pytest.raises(AssertionError, match="expected one removal"):
        _assert_guarded_removal(mutated, modifier)


def test_missing_idea_on_remove_callback_mutation_is_rejected():
    idea = "small_medium_business_owners"
    idea_block = _faction_idea_blocks()[idea]
    mutated = _remove_named_block(idea_block, "on_remove")
    with pytest.raises(AssertionError, match="expected one on_remove block"):
        _assert_idea_on_remove(mutated, FACTION_MODIFIERS[idea])


def test_wrong_fallback_modifier_mutation_is_rejected():
    idea = "small_medium_business_owners"
    modifier = FACTION_MODIFIERS[idea]
    cleanup = _one_named_block(
        EFFECTS_SOURCE, "if_no_longer_has_faction_clear_previous"
    )
    branch = _fallback_branch(cleanup, idea)
    mutated = _wrong_removal_modifier(branch, modifier)
    with pytest.raises(AssertionError, match="expected one removal"):
        _assert_guarded_removal(mutated, modifier)


def test_missing_fallback_modifier_mutation_is_rejected():
    idea = "small_medium_business_owners"
    modifier = FACTION_MODIFIERS[idea]
    cleanup = _one_named_block(
        EFFECTS_SOURCE, "if_no_longer_has_faction_clear_previous"
    )
    branch = _fallback_branch(cleanup, idea)
    mutated = _remove_named_block(branch, "remove_dynamic_modifier")
    with pytest.raises(AssertionError, match="expected one removal"):
        _assert_guarded_removal(mutated, modifier)


# case: cleanup source rejected as an unsafe or ineffective presence guard.
_INVALID_GUARDS = {
    "wrong-presence-guard": (
        "if = { limit = { has_dynamic_modifier = { modifier = other } } "
        "remove_dynamic_modifier = { modifier = target } }"
    ),
    "unconditional-removal": (
        "if = { limit = { has_dynamic_modifier = { modifier = target } } } "
        "remove_dynamic_modifier = { modifier = target }"
    ),
    "blocked-presence-guard": (
        "if = { limit = { has_dynamic_modifier = { modifier = target } "
        "always = no } remove_dynamic_modifier = { modifier = target } }"
    ),
    "idea-gated-removal": (
        "if = { limit = { has_dynamic_modifier = { modifier = target } "
        "has_idea = previous_faction } "
        "remove_dynamic_modifier = { modifier = target } }"
    ),
    "contradictory-presence-guard": (
        "if = { limit = { has_dynamic_modifier = { modifier = target } "
        "NOT = { has_dynamic_modifier = { modifier = target } } } "
        "remove_dynamic_modifier = { modifier = target } }"
    ),
}


@pytest.mark.parametrize("script", _INVALID_GUARDS.values(), ids=_INVALID_GUARDS)
def test_unrelated_or_blocked_modifier_guards_do_not_count_as_cleanup(script):
    with pytest.raises(AssertionError, match="matching presence guard"):
        _assert_guarded_removal(script, "target")


def test_guard_and_wrong_modifier_mutation_do_not_depend_on_statement_layout():
    script = strip_comments(
        "if={limit={has_idea=unrelated_idea} "
        'log="remove_dynamic_modifier={modifier=target}"}\r\n'
        "if={\r\n"
        "remove_dynamic_modifier={modifier=target}\r\n"
        "# Unrelated comment with { and modifier=target\r\n"
        "limit={has_dynamic_modifier={modifier=target}}\r\n}"
    )
    _assert_guarded_removal(script, "target")
    mutated = _wrong_removal_modifier(script, "target")
    with pytest.raises(AssertionError, match="expected one removal"):
        _assert_guarded_removal(mutated, "target")
    missing = _remove_named_block(script, "remove_dynamic_modifier")
    with pytest.raises(AssertionError, match="expected one removal"):
        _assert_guarded_removal(missing, "target")


def test_blocked_fallback_guard_mutation_is_rejected():
    idea = "small_medium_business_owners"
    cleanup = _one_named_block(
        EFFECTS_SOURCE, "if_no_longer_has_faction_clear_previous"
    )
    branch = _fallback_branch(cleanup, idea)
    limit = _one_named_block(branch, "limit")
    mutated = branch.replace(limit, limit + " always = no", 1)
    with pytest.raises(AssertionError, match="only absence and prior opinion"):
        _assert_fallback_removal(
            "if = {" + mutated + "}", idea, FACTION_MODIFIERS[idea]
        )


# case: (on_add body, whether it guarantees a cleanup call in the same scope).
_ON_ADD_CASES = {
    "direct": ("if_no_longer_has_faction_clear_previous=yes", True),
    "hidden": (
        "hidden_effect={if_no_longer_has_faction_clear_previous=yes}",
        True,
    ),
    "tooltip-only": (
        "effect_tooltip={if_no_longer_has_faction_clear_previous=yes}",
        False,
    ),
    "conditional-only": (
        "if={limit={always=no} if_no_longer_has_faction_clear_previous=yes}",
        False,
    ),
    "different-scope": (
        "GER={if_no_longer_has_faction_clear_previous=yes}",
        False,
    ),
    "disabled-call": ("if_no_longer_has_faction_clear_previous=no", False),
}


@pytest.mark.parametrize(("body", "wired"), _ON_ADD_CASES.values(), ids=_ON_ADD_CASES)
def test_on_add_cleanup_wiring_requires_executable_effects_in_the_same_scope(
    body, wired
):
    idea_block = "on_add={" + body + "}"
    if wired:
        _assert_on_add_cleanup(idea_block)
    else:
        with pytest.raises(AssertionError):
            _assert_on_add_cleanup(idea_block)
