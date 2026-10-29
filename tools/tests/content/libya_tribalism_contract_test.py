"""Evaluate Libya tribal loyalty weights and lifecycle effects from shipped scripts."""

import operator

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statement_ops, iter_statements, strip_comments

_DISABLED = "LBA_tribalism_disabled"
_LOYALTY = (
    "tripolitania_loyalty",
    "cyrenaica_loyalty",
    "fezzan_loyalty",
)
_STATES = (393, 391, 919, 397, 395, 396, 579, 1101, 1100, 392, 918, 920)
_EFFECTS_SOURCE = strip_comments(
    read_text(REPO_ROOT / "common/scripted_effects/99_LBA_scripted_effects.txt")
)
_DECISIONS_SOURCE = strip_comments(read_text(REPO_ROOT / "common/decisions/libya.txt"))
_EVENTS_SOURCE = strip_comments(read_text(REPO_ROOT / "events/Libya.txt"))
_ON_ACTIONS_SOURCE = strip_comments(
    read_text(REPO_ROOT / "common/on_actions/99_LBA_on_actions.txt")
)
_SCRIPTED_EFFECTS = {
    name: body for name, _, body in iter_statements(_EFFECTS_SOURCE) if body is not None
}


def _block(source, name):
    assert source is not None
    blocks = [
        body
        for key, _, body in iter_statements(source)
        if key == name and body is not None
    ]
    assert len(blocks) == 1, (name, len(blocks))
    return blocks[0]


def _value(source, name):
    assert source is not None
    values = [scalar for key, scalar, _ in iter_statements(source) if key == name]
    assert len(values) == 1 and values[0] is not None, (name, values)
    return values[0]


def _script_blocks(source):
    for key, _, body in iter_statements(source):
        if body is not None:
            yield key, body
            yield from _script_blocks(body)


def _find_block(source, name):
    matches = [body for key, body in _script_blocks(source) if key == name]
    assert len(matches) == 1, (name, len(matches))
    return matches[0]


def _tribal_decisions():
    category = _block(_DECISIONS_SOURCE, "libya_oil_nationalisation")
    return {
        name: body
        for name, _, body in iter_statements(category)
        if body is not None
        and any(variable in _block(body, "ai_will_do") for variable in _LOYALTY)
    }


TRIBAL_DECISIONS = _tribal_decisions()


class LibyaEffectFixture:
    """Run the limited effect/trigger subset used by the tribalism lifecycle."""

    comparisons = {"=": operator.eq, ">": operator.gt, "<": operator.lt}
    modifiers = (
        "libya_tribalism_loyal_dynamic_modifier",
        "libya_tribalism_neutral_dynamic_modifier",
        "libya_tribalism_bad_dynamic_modifier",
    )

    def __init__(
        self, variables=None, flags=(), source_variables=None, source_flags=(), ai=False
    ):
        self.root = {"variables": dict(variables or {}), "flags": set(flags), "ai": ai}
        self.source = {
            "variables": dict(source_variables or {}),
            "flags": set(source_flags),
        }
        self.states = [{"id": state, "modifiers": set()} for state in _STATES]
        self.scope = self.root
        self.temps = {}
        self.dirty_updates = 0

    def _number(self, value, scope):
        if value in self.root["variables"]:
            return self.root["variables"][value]
        if value in self.temps:
            return self.temps[value]
        if value.startswith("FROM."):
            return self.source["variables"].get(value.removeprefix("FROM."), 0)
        try:
            return float(value)
        except ValueError:
            return scope.get("variables", {}).get(value, 0)

    def condition(self, source, scope=None):
        scope = scope or self.scope
        results = []
        for key, comparison, scalar, body in iter_statement_ops(source):
            if key in {"OR", "NOT"}:
                assert body is not None
                checks = [
                    self.condition_entry(entry, scope)
                    for entry in iter_statements(body)
                ]
                result = any(checks) if key == "OR" else not all(checks)
                results.append(result)
            elif key in {"ROOT", "FROM"}:
                target = self.root if key == "ROOT" else self.source
                results.append(self.condition(body, target))
            elif key == "has_country_flag":
                results.append(scalar in scope.get("flags", set()))
            elif key == "has_dynamic_modifier":
                modifier = _value(body, "modifier")
                results.append(modifier in scope.get("modifiers", set()))
            elif key == "check_variable":
                assert body is not None
                [(variable, operation, threshold, nested)] = list(
                    iter_statement_ops(body)
                )
                assert nested is None and operation in self.comparisons
                assert variable is not None and threshold is not None
                results.append(
                    self.comparisons[operation](
                        self._number(variable, scope), float(threshold)
                    )
                )
            elif key == "state":
                assert scalar is not None
                results.append(int(scalar) == scope["id"])
            elif key == "is_owned_by":
                results.append(scalar == "ROOT")
            elif key == "is_ai":
                results.append(self.root["ai"] == (scalar == "yes"))
            elif key == "always":
                results.append(scalar == "yes")
            else:
                raise AssertionError(f"Unsupported tribalism trigger: {key}")
        return all(results)

    def condition_entry(self, entry, scope):
        key, scalar, body = entry
        return self.condition(
            f"{key} = {{ {body} }}" if body is not None else f"{key} = {scalar}",
            scope,
        )

    def apply_effects(self, source, scope=None):
        prior_scope = self.scope
        self.scope = scope or prior_scope
        branch_taken = None
        for key, scalar, body in iter_statements(source):
            if key in {"if", "else_if", "else"}:
                if key == "if":
                    branch_taken = False
                else:
                    assert branch_taken is not None
                assert body is not None
                matches = not branch_taken and (
                    key == "else" or self.condition(_block(body, "limit"), self.scope)
                )
                if matches:
                    branch_taken = True
                    self.apply_effects(body, self.scope)
                continue
            branch_taken = None
            if key in {"limit", "log", "custom_effect_tooltip"}:
                continue
            if key in {"hidden_effect", "ROOT"}:
                assert body is not None
                self.apply_effects(body, self.root if key == "ROOT" else self.scope)
            elif key == "FROM":
                assert body is not None
                self.apply_effects(body, self.source)
            elif key == "every_owned_state":
                assert body is not None
                limits = [
                    block
                    for name, _, block in iter_statements(body)
                    if name == "limit" and block is not None
                ]
                assert len(limits) <= 1
                for state in self.states:
                    if not limits or self.condition(limits[0], state):
                        self.apply_effects(body, state)
            elif key == "set_country_flag":
                assert scalar is not None
                self.scope.setdefault("flags", set()).add(scalar)
            elif key == "clr_country_flag":
                assert scalar is not None
                self.scope.setdefault("flags", set()).discard(scalar)
            elif key == "clear_variable":
                assert scalar is not None
                self.scope.setdefault("variables", {}).pop(scalar, None)
            elif key in {"set_variable", "set_temp_variable"}:
                assert body is not None
                [(name, _, value, nested)] = list(iter_statement_ops(body))
                assert name is not None and value is not None and nested is None
                target = self.root["variables"] if key == "set_variable" else self.temps
                target[name] = self._number(value, self.scope)
            elif key in {"multiply_temp_variable", "subtract_from_temp_variable"}:
                assert body is not None
                [(name, _, value, nested)] = list(iter_statement_ops(body))
                assert name is not None and value is not None and nested is None
                number = self._number(value, self.scope)
                self.temps[name] = (
                    self.temps[name] * number
                    if key == "multiply_temp_variable"
                    else self.temps[name] - number
                )
            elif key in {"add_dynamic_modifier", "remove_dynamic_modifier"}:
                assert body is not None
                modifier = _value(body, "modifier")
                if key == "add_dynamic_modifier":
                    self.scope.setdefault("modifiers", set()).add(modifier)
                else:
                    self.scope.setdefault("modifiers", set()).discard(modifier)
            elif key == "update_lba_dirty_variable":
                self.dirty_updates += 1
            elif key in _SCRIPTED_EFFECTS:
                self.apply_effects(_SCRIPTED_EFFECTS[key])
            elif key == "random_list":
                continue
            else:
                raise AssertionError(f"Unsupported tribalism effect: {key}")
        self.scope = prior_scope


def _civil_war_tribal_branch():
    on_actions = _block(_ON_ACTIONS_SOURCE, "on_actions")
    on_declare_war = _block(on_actions, "on_declare_war")
    effect = _block(on_declare_war, "effect")
    for key, _, civil_war in iter_statements(effect):
        if key != "if":
            continue
        limit = _block(civil_war, "limit")
        root_limit = _block(limit, "ROOT")
        from_limit = _block(limit, "FROM")
        if ("original_tag", "LBA", None) in list(iter_statements(root_limit)) and (
            "original_tag",
            "LBA",
            None,
        ) in list(iter_statements(from_limit)):
            root_effects = _block(civil_war, "ROOT")
            entries = list(iter_statements(root_effects))
            for index, (child, _, body) in enumerate(entries):
                if (
                    child == "if"
                    and body is not None
                    and "LBA_tribalism_disabled" in _block(body, "limit")
                    and index + 1 < len(entries)
                    and entries[index + 1][0] == "else"
                    and entries[index + 1][2] is not None
                ):
                    return root_effects, body, entries[index + 1][2]
    raise AssertionError("Libyan civil-war variable copy block not found")


def test_all_sixteen_resource_decision_weights_ignore_disabled_loyalty():
    assert len(TRIBAL_DECISIONS) == 16
    low = {name: 0.1 for name in _LOYALTY}
    moderate = {name: 0.3 for name in _LOYALTY}
    healthy = {name: 0.9 for name in _LOYALTY}

    def weight(decision, disabled, variables):
        fixture = EconomicScriptFixture(
            {"interest_rate": 0, "domestic_influence_amount": 100, **variables},
            predicates={
                "has_country_flag": lambda flag, _: flag == _DISABLED and disabled,
                "has_active_mission": lambda *_: False,
                "ai_has_high_deficit": False,
            },
        )
        return fixture.weight(script_block(decision, "ai_will_do"))

    for decision in TRIBAL_DECISIONS.values():
        healthy_active = weight(decision, False, healthy)
        active_low = weight(decision, False, low)
        active_moderate = weight(decision, False, moderate)
        assert active_low == 0
        assert active_moderate == pytest.approx(healthy_active * 0.1)

        disabled_low = weight(decision, True, low)
        disabled_moderate = weight(decision, True, moderate)
        disabled_cleared = weight(decision, True, {})
        assert disabled_low == healthy_active
        assert disabled_moderate == healthy_active
        assert disabled_cleared == healthy_active


@pytest.mark.parametrize("ai", [False, True])
def test_disable_effect_clears_loyalty_and_all_owned_tribal_modifiers(ai):
    world = LibyaEffectFixture(
        {name: 0.7 for name in _LOYALTY},
        flags={_DISABLED},
        ai=ai,
    )
    for state in world.states:
        state["modifiers"].update(world.modifiers)

    world.apply_effects(_block(_EFFECTS_SOURCE, "lba_disable_tribalism"))

    assert _DISABLED in world.root["flags"]
    assert not set(_LOYALTY) & world.root["variables"].keys()
    assert all(not state["modifiers"] for state in world.states)
    assert world.dirty_updates == (0 if ai else 1)


@pytest.mark.parametrize(
    "decision,loyalty",
    [
        ("libya_attack_ansar_al_sharia_in_derna", "cyrenaica_loyalty"),
        ("libya_attack_ansar_al_sharia_in_ajdabiya", "cyrenaica_loyalty"),
        ("libya_attack_ansar_al_sharia_in_sabha", "fezzan_loyalty"),
    ],
)
def test_antiinsurgency_probability_has_default_when_tribalism_is_disabled(
    decision, loyalty
):
    script = _find_block(_DECISIONS_SOURCE, decision)
    for disabled, expected in ((False, 0.6 * 0.75), (True, 0.75)):
        world = LibyaEffectFixture(
            {loyalty: 0.6}, flags={_DISABLED} if disabled else ()
        )
        world.apply_effects(_block(script, "remove_effect"))
        assert world.temps["chance_of_success"] == expected
        assert world.temps["chance_of_failure"] == 1 - expected


def test_routine_modifier_refresh_preserves_loyalty_values():
    values = dict(zip(_LOYALTY, (0.8, 0.4, 0.1)))
    world = LibyaEffectFixture(values)
    world.apply_effects(_block(_EFFECTS_SOURCE, "libya_update_tribalism_modifiers"))
    assert world.root["variables"] == values
    assert all(
        world.modifiers[0] in state["modifiers"]
        for state in world.states
        if state["id"] in {393, 391, 919}
    )


def test_civil_war_inheritance_cleans_disabled_and_copies_active_tribalism():
    root_effects, disabled_branch, active_branch = _civil_war_tribal_branch()
    disabled = LibyaEffectFixture(
        {name: 0.3 for name in _LOYALTY},
        source_variables={name: 0.8 for name in _LOYALTY},
        source_flags={_DISABLED},
    )
    for state in disabled.states:
        state["modifiers"].update(disabled.modifiers)
    assert disabled.condition(_block(disabled_branch, "limit"))
    disabled.apply_effects(disabled_branch)
    assert _DISABLED in disabled.root["flags"]
    assert not set(_LOYALTY) & disabled.root["variables"].keys()
    assert all(not state["modifiers"] for state in disabled.states)

    active = LibyaEffectFixture(source_variables=dict(zip(_LOYALTY, (0.8, 0.6, 0.4))))
    assert not active.condition(_block(disabled_branch, "limit"))
    active.apply_effects(active_branch)
    assert {name: active.root["variables"][name] for name in _LOYALTY} == active.source[
        "variables"
    ]
    assert _DISABLED not in active.root["flags"]
    effects = list(iter_statements(root_effects))
    tribal_index = next(
        index for index, (_, _, body) in enumerate(effects) if body == disabled_branch
    )
    assert any(
        key == "libya_copy_country_flags" for key, _, _ in effects[tribal_index + 1 :]
    )


@pytest.mark.parametrize(
    "decision,target",
    [
        ("libya_tribalism_tripolitanian_revolt", "TRP"),
        ("libya_tribalism_cyrenaica_revolt", "CYR"),
        ("libya_tribalism_fezzan_revolt", "FEZ"),
    ],
)
def test_disabled_tribalism_cancels_pending_revolt(decision, target):
    category = _block(_DECISIONS_SOURCE, "libya_libyan_tribalism")
    body = _block(category, decision)
    for disabled, exists, expected in (
        (False, False, False),
        (True, False, True),
        (False, True, True),
    ):
        fixture = EconomicScriptFixture(
            {},
            predicates={
                "has_country_flag": lambda flag, _: flag == _DISABLED and disabled,
                "country_exists": lambda tag, _: tag == target and exists,
            },
        )
        assert fixture.condition(script_block(body, "cancel_trigger")) is expected


def test_libya_paid_rail_offer_is_free_of_recipient_cost_weight_penalties():
    offer = next(
        body
        for key, _, body in iter_statements(_EVENTS_SOURCE)
        if key == "country_event"
        and body is not None
        and ("id", "LibyaFocus.34", None) in list(iter_statements(body))
    )
    receiver_option = next(
        body
        for key, _, body in iter_statements(offer)
        if key == "option" and body is not None and ("LibyaFocus.34.a" in body)
    )
    payment_gate = _block(_block(receiver_option, "if"), "limit")

    def evaluate(pays_all, bankrupt, deficit):
        from_fixture = EconomicScriptFixture(
            {},
            predicates={
                "has_country_flag": lambda flag, _: (
                    flag == "LBA_railroad_deal_libya_pays_all" and pays_all
                )
            },
        )
        fixture = EconomicScriptFixture(
            {"interest_rate": 0},
            predicates={
                "FROM": lambda _, body: from_fixture.condition(body),
                "has_active_mission": lambda *_: bankrupt,
                "ai_has_high_deficit": deficit,
                "has_opinion": lambda *_: False,
                "has_country_flag": False,
            },
        )
        paid_by_receiver = fixture.condition(payment_gate)
        weight = fixture.weight(script_block(receiver_option, "ai_chance"))
        expected = 80 * (0.25 if bankrupt and paid_by_receiver else 1)
        if deficit and paid_by_receiver:
            expected *= 0.5
        assert paid_by_receiver is (not pays_all)
        assert weight == expected

    for pays_all in (False, True):
        for bankrupt in (False, True):
            for deficit in (False, True):
                evaluate(pays_all, bankrupt, deficit)
