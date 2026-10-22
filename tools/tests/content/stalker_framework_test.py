"""Source regressions for the isolated Zone; native scheduling/scopes remain unverified."""

import re
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

import pytest
from shared.suite import _economic_statements, script_block
from shared_utils import strip_comments

ROOT = Path(__file__).resolve().parents[3]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def entries(source):
    source = re.sub(r"\b(\d+)(?=\s*=\s*\{)", r"state_\1", strip_comments(source))
    source = source.replace("^num", "_array_num")
    return _economic_statements(source)


class ZoneFixture:
    """Execute this slice's branches; record engine effects instead of emulating them."""

    def __init__(self, *, enabled=True, reference=True):
        self.effects = {}
        for name in ("scripted_effects", "zone_placements", "pulse_effects"):
            self.effects.update(
                (key, body)
                for key, _, _, body in entries(
                    read(f"common/scripted_effects/99_STALKER_{name}.txt")
                )
            )
        self.triggers = {
            key: body
            for key, _, _, body in entries(
                read("common/scripted_triggers/99_STALKER_scripted_triggers.txt")
            )
        }
        self.nodes = defaultdict(
            lambda: {
                "vars": defaultdict(float),
                "flags": {},
                "modifiers": {},
                "exists": True,
                "ai": False,
                "pp": 100,
                "missions": set(),
                "controller": 0,
                "infrastructure": 1,
            }
        )
        self.nodes[0]["exists"] = False
        self.nodes[698]["controller"] = 1
        self.globals = defaultdict(float)
        self.global_flags = set()
        self.temps = {}
        self.targets = {}
        self.rules = {
            "rule_stalker_scenario": "ENABLED" if enabled else "DISABLED",
            "rule_stalker_kaimanov_global_zones": (
                "REFERENCE_MAP" if reference else "DISABLED"
            ),
        }
        self.root, self.previous, self.froms = 1, [], [698]
        self.day = 0
        self.native, self.events = [], []
        self.roll = 99

    def scope(self, key, scope):
        if key.startswith("state_") and key.removeprefix("state_").isdigit():
            return int(key.removeprefix("state_"))
        if key == "ROOT":
            return self.root
        if key == "PREV":
            return self.previous[-1]
        if key == "FROM":
            return self.froms[0]
        if key == "FROM.FROM":
            return self.froms[1]
        if key == "controller":
            return self.nodes[scope]["controller"]
        if key.startswith("event_target:"):
            return self.targets[key.split(":", 1)[1]]
        return None

    def storage(self, name, scope):
        if name.startswith("global."):
            return self.globals, name.removeprefix("global.")
        if name.startswith("PREV."):
            scope = self.previous[-1]
            name = name.removeprefix("PREV.")
        return self.nodes[scope]["vars"], name

    def value(self, name, scope):
        if name == "THIS":
            return scope
        try:
            return float(name)
        except ValueError:
            pass
        if name in self.temps:
            return self.temps[name]
        count = name.endswith("_array_num")
        storage, key = self.storage(name.removesuffix("_array_num"), scope)
        if count:
            return len(storage.get(key, []))
        return storage[key]

    def flag(self, name, scope):
        flags = self.nodes[scope]["flags"]
        return name in flags and (flags[name] is None or flags[name] > self.day)

    def scoped(self, body, scope, target, *, condition=False):
        self.previous.append(scope)
        try:
            return (
                self.condition(body, target)
                if condition
                else self.execute(body, target)
            )
        finally:
            self.previous.pop()

    def condition(self, source, scope):
        checks = []
        for key, op, scalar, body in entries(source):
            target = self.scope(key, scope)
            if target is not None:
                checks.append(self.scoped(body, scope, target, condition=True))
            elif key in self.triggers:
                checks.append(
                    self.condition(self.triggers[key], scope) == (scalar == "yes")
                )
            elif key in {"NOT", "AND", "OR"}:
                children = [
                    self.condition(
                        f"{name} {operator} "
                        + (f"{{ {nested} }}" if nested is not None else value),
                        scope,
                    )
                    for name, operator, value, nested in entries(body)
                ]
                result = any(children) if key == "OR" else all(children)
                checks.append(not result if key == "NOT" else result)
            elif key == "check_variable":
                name, operation, threshold, _ = entries(body)[0]
                a, b = self.value(name, scope), self.value(threshold, scope)
                checks.append(
                    {"=": a == b, ">": a > b, "<": a < b, ">=": a >= b, "<=": a <= b}[
                        operation
                    ]
                )
            elif key == "has_game_rule":
                fields = {name: value for name, _, value, _ in entries(body)}
                checks.append(self.rules[fields["rule"]] == fields["option"])
            elif key == "has_global_flag":
                checks.append(scalar in self.global_flags)
            elif key == "has_state_flag":
                checks.append(self.flag(scalar, scope))
            elif key == "has_dynamic_modifier":
                name = entries(body)[0][2]
                modifiers = self.nodes[scope]["modifiers"]
                checks.append(
                    name in modifiers
                    and (modifiers[name] is None or modifiers[name] > self.day)
                )
            elif key == "is_in_array":
                name, _, value, _ = entries(body)[0]
                storage, key = self.storage(name, scope)
                checks.append(self.value(value, scope) in storage.get(key, []))
            elif key == "is_controlled_by":
                holder = self.scope(scalar, scope)
                assert holder is not None
                checks.append(self.nodes[scope]["controller"] == holder)
            elif key in {"exists", "is_ai"}:
                field = "ai" if key == "is_ai" else key
                checks.append(self.nodes[scope][field] == (scalar == "yes"))
            elif key == "has_political_power":
                assert op == "<"
                checks.append(self.nodes[scope]["pp"] < float(scalar))
            elif key == "has_active_mission":
                checks.append(scalar in self.nodes[scope]["missions"])
            elif key == "has_event_target":
                checks.append(scalar in self.targets)
            elif key == "infrastructure":
                assert op == ">"
                checks.append(self.nodes[scope]["infrastructure"] > float(scalar))
            else:
                raise AssertionError(f"Unmodeled condition: {key}")
        return all(checks)

    def execute(self, source, scope):
        taken = None
        for key, op, scalar, body in entries(source):
            if key in {"if", "else_if", "else"}:
                if key == "if":
                    taken = False
                assert taken is not None
                if not taken and (
                    key == "else" or self.condition(script_block(body, "limit"), scope)
                ):
                    taken = True
                    self.execute(body, scope)
                continue
            taken = None
            if key in {"limit", "log", "custom_effect_tooltip"}:
                continue
            target = self.scope(key, scope)
            if target is not None:
                self.scoped(body, scope, target)
            elif key in self.effects:
                self.execute(self.effects[key], scope)
            elif key == "random_country":
                self.scoped(body, scope, 1)
            elif key == "for_each_scope_loop":
                array = next(
                    value for name, _, value, _ in entries(body) if name == "array"
                )
                storage, name = self.storage(array, scope)
                for member in list(storage.get(name, [])):
                    rest = body[body.index("\n", body.index("array")) + 1 :]
                    self.scoped(rest, scope, member)
            elif key in {
                "set_variable",
                "add_to_variable",
                "multiply_variable",
                "set_temp_variable",
                "add_to_temp_variable",
                "subtract_from_temp_variable",
                "multiply_temp_variable",
            }:
                name, _, operand, _ = entries(body)[0]
                storage, name = (
                    (self.temps, name) if "temp" in key else self.storage(name, scope)
                )
                value = self.value(operand, scope)
                if key.startswith("add"):
                    value += storage.get(name, 0)
                elif key.startswith("subtract"):
                    value = storage.get(name, 0) - value
                elif key.startswith("multiply"):
                    value *= storage.get(name, 0)
                storage[name] = value
            elif key in {"clamp_variable", "clamp_temp_variable"}:
                fields = {name: value for name, _, value, _ in entries(body)}
                name = fields["var"]
                storage, name = (
                    (self.temps, name) if "temp" in key else self.storage(name, scope)
                )
                assert name in storage, f"Clamping unwritten variable: {name}"
                storage[name] = min(
                    max(storage[name], float(fields["min"])), float(fields["max"])
                )
            elif key == "set_global_flag":
                self.global_flags.add(scalar)
            elif key == "set_state_flag":
                fields = (
                    {name: value for name, _, value, _ in entries(body)} if body else {}
                )
                name = fields.get("flag", scalar)
                self.nodes[scope]["flags"][name] = (
                    self.day + float(fields["days"]) if "days" in fields else None
                )
            elif key == "clr_state_flag":
                self.nodes[scope]["flags"].pop(scalar, None)
            elif key == "add_to_array":
                name, _, operand, _ = entries(body)[0]
                storage, name = self.storage(name, scope)
                storage.setdefault(name, []).append(self.value(operand, scope))
            elif key == "add_dynamic_modifier":
                fields = {name: value for name, _, value, _ in entries(body)}
                self.nodes[scope]["modifiers"][fields["modifier"]] = (
                    self.day + float(fields["days"]) if "days" in fields else None
                )
            elif key == "remove_dynamic_modifier":
                self.nodes[scope]["modifiers"].pop(entries(body)[0][2])
            elif key == "save_event_target_as":
                self.targets[scalar] = scope
            elif key == "country_event":
                self.events.append((scope, scalar, self.targets.copy()))
            elif key == "random":
                chance = self.value(entries(body)[0][2], scope)
                self.native.append(("random", scope, chance))
                if self.roll < chance:
                    self.execute(body[body.index("\n") + 1 :], scope)
            elif key in {"small_expenditure", "damage_building", "add_stability"}:
                self.native.append((key, scope, scalar if body is None else body))
            elif key == "hidden_effect":
                self.execute(body, scope)
            else:
                raise AssertionError(f"Unmodeled effect: {key}")

    def run(self, name, scope=1):
        self.execute(self.effects[name], scope)

    def start(self):
        actions = script_block(
            read("common/on_actions/99_STALKER_on_actions.txt"), "on_actions"
        )
        self.execute(script_block(script_block(actions, "on_startup"), "effect"), 0)

    def activate(self):
        self.start()
        self.run("STALKER_activate_zone_001_ukraine")

    def answer(self, letter, *, actor=None, event_index=0):
        country, event, self.targets = deepcopy(self.events[event_index])
        assert event == "STALKER.1"
        self.root = country if actor is None else actor
        event = next(
            body
            for key, _, _, body in entries(read("events/STALKER.txt"))
            if key == "country_event"
            and ("id", "=", "STALKER.1", None) in entries(body)
        )
        option = next(
            body
            for key, _, _, body in entries(event)
            if key == "option"
            and ("name", "=", f"STALKER.1.{letter}", None) in entries(body)
        )
        self.execute(script_block(option, "hidden_effect"), self.root)

    def transfer(self, holder):
        self.froms = [self.nodes[698]["controller"], 698]
        self.nodes[698]["controller"] = holder
        self.root = holder
        actions = script_block(
            read("common/on_actions/99_STALKER_on_actions.txt"), "on_actions"
        )
        self.execute(
            script_block(script_block(actions, "on_state_control_changed"), "effect"),
            holder,
        )


def test_disabled_startup_and_direct_activation_have_no_state_changes():
    script = ZoneFixture(enabled=False)
    script.start()
    script.run("STALKER_activate_zone_001_ukraine")
    script.run("STALKER_monthly_pulse")
    assert not script.global_flags
    assert not script.globals
    assert not script.nodes[698]["flags"]
    assert not script.events and not script.native


@pytest.mark.parametrize("reference,expected", [(False, 1), (True, 31)])
def test_registry_is_inert_idempotent_and_has_unique_stable_anchors(
    reference, expected
):
    script = ZoneFixture(reference=reference)
    script.start()
    script.start()
    anchors = script.globals["STALKER_zone_anchor_states"]
    assert len(anchors) == len(set(anchors)) == expected
    identifiers = {script.nodes[state]["vars"]["STALKER_zone_id"] for state in anchors}
    assert identifiers == (set(range(1, 32)) if reference else {1})
    assert not script.events
    assert not any(
        "STALKER_zone_active" in script.nodes[state]["flags"] for state in anchors
    )
    assert not any(script.nodes[state]["modifiers"] for state in anchors)


def test_2008_activation_is_once_and_only_the_original_zone_is_active():
    script = ZoneFixture()
    script.activate()
    first = deepcopy(script.events)
    script.run("STALKER_activate_zone_001_ukraine")
    assert script.events == first
    assert script.globals["STALKER_active_zone_anchors"] == [698]
    assert script.flag("STALKER_zone_policy_pending", 698)
    assert script.nodes[698]["vars"]["STALKER_zone_activity"] == 60
    assert script.nodes[1]["vars"]["STALKER_zone_upkeep_factor"] == 0.01
    yearly = script_block(
        read("common/scripted_effects/00_yearly_effects.txt"),
        "trigger_year_2008_events",
    )
    dispatch = next(
        body
        for key, _, _, body in entries(yearly)
        if key == "if" and "STALKER_activate_zone_001_ukraine" in body
    )
    assert "STALKER_scenario_enabled = yes" in script_block(dispatch, "limit")


@pytest.mark.parametrize(
    "letter,containment,exploitation,research", [("a", 60, 0, 0), ("b", 30, 30, 0.015)]
)
def test_policies_charge_the_controller_once_and_refresh_actual_administration(
    letter, containment, exploitation, research
):
    script = ZoneFixture()
    script.activate()
    script.answer(letter)
    assert script.nodes[698]["vars"]["STALKER_zone_containment"] == containment
    assert script.nodes[698]["vars"]["STALKER_zone_exploitation"] == exploitation
    assert script.nodes[1]["vars"]["STALKER_zone_research_factor"] == research
    assert script.nodes[1]["vars"]["STALKER_zone_garrison_factor"] == -0.005
    assert [call for call in script.native if call[0] == "small_expenditure"] == [
        ("small_expenditure", 1, "yes")
    ]
    before = deepcopy(script.native)
    script.answer("b" if letter == "a" else "a")
    assert script.native == before


def test_pending_policy_follows_control_and_stale_choices_cannot_charge_old_holder():
    script = ZoneFixture()
    script.activate()
    script.transfer(2)
    assert "STALKER_zone_administration" not in script.nodes[1]["modifiers"]
    assert "STALKER_zone_administration" in script.nodes[2]["modifiers"]
    assert script.nodes[1]["vars"]["STALKER_zone_upkeep_factor"] == 0
    assert script.nodes[2]["vars"]["STALKER_zone_upkeep_factor"] == 0.01
    script.answer("b")
    assert not script.native
    assert script.flag("STALKER_zone_policy_pending", 698)
    script.answer("b", event_index=1)
    assert ("small_expenditure", 2, "yes") in script.native
    assert script.nodes[2]["vars"]["STALKER_zone_research_factor"] == 0.015


def test_absent_controller_does_not_lose_activation_or_allow_stale_policy_rewards():
    script = ZoneFixture()
    script.nodes[698]["controller"] = 0
    script.activate()
    assert script.globals["STALKER_active_zone_anchors"] == [698]
    assert not script.events
    script.transfer(2)
    script.answer("a")
    assert ("small_expenditure", 2, "yes") in script.native


def test_policy_expiry_prevents_late_costs_and_does_not_block_the_first_emission():
    script = ZoneFixture()
    script.activate()
    script.day = 60
    script.answer("a")
    assert not script.native
    script.day = 89
    script.run("STALKER_monthly_emission_pulse")
    assert not script.native
    script.day = 90
    script.run("STALKER_monthly_emission_pulse")
    assert ("add_stability", 1, "-0.02") in script.native
    assert not any(call[0] == "random" for call in script.native)
    assert script.events[-1][1] == "STALKER.2"
    assert script.nodes[698]["flags"]["STALKER_emission_cooldown"] == 270
    before = deepcopy(script.native)
    script.day = 269
    script.run("STALKER_monthly_emission_pulse")
    assert script.native == before


@pytest.mark.parametrize(
    "activity,exploitation,containment,risk",
    [(0, 0, 100, 2), (60, 30, 30, 12), (100, 100, 0, 20)],
)
def test_recurring_emission_risk_uses_live_values_and_bounds(
    activity, exploitation, containment, risk
):
    script = ZoneFixture()
    script.activate()
    script.answer("a")
    state = script.nodes[698]
    state["flags"].pop("STALKER_first_emission_pending")
    state["flags"].pop("STALKER_emission_cooldown")
    state["vars"].update(
        STALKER_zone_activity=activity,
        STALKER_zone_exploitation=exploitation,
        STALKER_zone_containment=containment,
    )
    script.run("STALKER_monthly_emission_pulse")
    assert script.native[-1] == ("random", 698, risk)


@pytest.mark.parametrize("containment,extra", [(24, True), (25, False)])
@pytest.mark.parametrize("infrastructure", [0, 1])
def test_emission_penalties_use_post_emission_containment_and_existing_buildings(
    containment, extra, infrastructure
):
    script = ZoneFixture()
    script.activate()
    script.answer("a")
    script.nodes[698]["vars"]["STALKER_zone_containment"] = containment
    script.nodes[698]["infrastructure"] = infrastructure
    script.day = 90
    script.native.clear()
    script.run("STALKER_trigger_emission", 698)
    assert (("add_stability", 1, "-0.01") in script.native) == extra
    assert any(call[0] == "damage_building" for call in script.native) == bool(
        infrastructure
    )
    assert script.nodes[698]["vars"]["STALKER_zone_activity"] == 70
    before = deepcopy(script.native)
    script.run("STALKER_trigger_emission", 698)
    assert script.native == before


@pytest.mark.parametrize(
    "blocked",
    [
        None,
        "player",
        "affordable",
        "treasury",
        "bankruptcy",
        "pending",
        "contained",
        "cooldown",
    ],
)
def test_ai_relief_is_paid_bounded_and_shares_the_containment_cooldown(blocked):
    script = ZoneFixture()
    script.activate()
    script.answer("a")
    state, holder = script.nodes[698], script.nodes[1]
    state["vars"]["STALKER_zone_containment"] = 20
    holder.update(ai=True, pp=10)
    holder["vars"]["treasury"] = 10
    if blocked == "player":
        holder["ai"] = False
    elif blocked == "affordable":
        holder["pp"] = 50
    elif blocked == "treasury":
        holder["vars"]["treasury"] = 9
    elif blocked == "bankruptcy":
        holder["missions"].add("bankruptcy_incoming_collapse")
    elif blocked == "pending":
        state["flags"]["STALKER_zone_policy_pending"] = 60
    elif blocked == "contained":
        state["vars"]["STALKER_zone_containment"] = 30
    elif blocked == "cooldown":
        state["flags"]["STALKER_zone_reinforced"] = 180
    before = state["vars"]["STALKER_zone_containment"]
    script.native.clear()
    script.run("STALKER_monthly_ai_zone_relief_pulse")
    assert state["vars"]["STALKER_zone_containment"] == before + (0 if blocked else 20)
    assert script.native == ([] if blocked else [("small_expenditure", 1, "yes")])
    first = deepcopy(script.native)
    script.run("STALKER_monthly_ai_zone_relief_pulse")
    assert script.native == first
    if not blocked:
        script.day = 180
        state["vars"]["STALKER_zone_containment"] = 20
        script.run("STALKER_monthly_ai_zone_relief_pulse")
        assert script.native == first * 2


def test_decision_target_gates_and_completion_reject_transfer_and_repeat_rewards():
    script = ZoneFixture()
    script.activate()
    script.answer("a")
    decision = script_block(
        script_block(
            read("common/decisions/STALKER_decisions.txt"),
            "STALKER_zone_management_category",
        ),
        "STALKER_reinforce_zone_containment",
    )
    assert ("cost", "=", "50", None) in entries(decision)
    assert ("days_re_enable", "=", "180", None) in entries(decision)
    assert script.condition(script_block(decision, "target_trigger"), 1)
    script.native.clear()
    script.execute(script_block(decision, "complete_effect"), 1)
    assert script.nodes[698]["vars"]["STALKER_zone_containment"] == 80
    assert script.native == [("small_expenditure", 1, "yes")]
    assert not script.condition(script_block(decision, "target_trigger"), 1)
    script.execute(script_block(decision, "complete_effect"), 1)
    assert len(script.native) == 1
    script.transfer(2)
    script.root = 1
    script.execute(script_block(decision, "complete_effect"), 1)
    assert len(script.native) == 1


def test_slice_defines_every_own_call_and_carries_no_later_subsystem_dependencies():
    sources = []
    for folder in ("common", "events"):
        sources.extend(path for path in (ROOT / folder).rglob("*STALKER*.txt"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    definitions = set(re.findall(r"(?m)^((?:STALKER_|GLOBAL_STALKER_)\w+) = \{", text))
    calls = set(re.findall(r"\b(STALKER_\w+)\s*=\s*(?:yes|no)\b", text))
    assert calls <= definitions, calls - definitions
    modifiers = entries(
        read("common/dynamic_modifiers/00_STALKER_dynamic_modifiers.txt")
    )
    assert {name for name, _, _, _ in modifiers} == {
        "STALKER_zone_presence",
        "STALKER_emission_disruption",
        "STALKER_zone_administration",
    }
    for excluded in (
        "TOP_",
        "FBC_",
        "DEUSEX_",
        "METALGEAR_",
        "ai_race_",
        "STALKER_zone_profile",
    ):
        assert excluded not in text
    assert set(ZoneFixture().triggers) == {
        "STALKER_scenario_enabled",
        "STALKER_is_zone_location",
        "STALKER_is_active_zone",
        "STALKER_is_active_zone_anchor",
        "STALKER_controls_active_zone",
    }


def test_fixture_executes_numeric_state_scopes_and_rejects_unsupported_statements():
    script = ZoneFixture()
    script.execute("698 = { set_variable = { marker = 1 } }", 1)
    assert script.nodes[698]["vars"]["marker"] == 1
    assert "marker" not in script.nodes[1]["vars"]
    with pytest.raises(AssertionError, match="Unmodeled effect"):
        script.execute("not_a_supported_effect = yes", 1)
    with pytest.raises(AssertionError, match="Malformed or unconsumed"):
        entries("garbage set_variable = { marker = 1 }")


def test_resolved_policy_and_research_follow_transfer_without_a_new_choice():
    script = ZoneFixture()
    script.activate()
    script.answer("b")
    count = len(script.events)
    script.transfer(2)
    assert len(script.events) == count
    assert script.nodes[1]["vars"]["STALKER_zone_research_factor"] == 0
    assert script.nodes[2]["vars"]["STALKER_zone_research_factor"] == 0.015
    assert "STALKER_zone_administration" not in script.nodes[1]["modifiers"]
    assert "STALKER_zone_administration" in script.nodes[2]["modifiers"]


@pytest.mark.parametrize(
    "activity,containment,exploitation,expected",
    [
        (0, 95, 0, (0, 100, 0)),
        (5, 0, 3, (0, 20, 0)),
        (100, 60, 30, (90, 80, 25)),
    ],
)
def test_reinforcement_clamps_each_meter_and_cannot_be_repeated_until_expiry(
    activity, containment, exploitation, expected
):
    script = ZoneFixture()
    script.activate()
    script.answer("b")
    variables = script.nodes[698]["vars"]
    variables.update(
        STALKER_zone_activity=activity,
        STALKER_zone_containment=containment,
        STALKER_zone_exploitation=exploitation,
    )
    script.run("STALKER_reinforce_containment", 698)
    names = ("activity", "containment", "exploitation")
    assert tuple(variables[f"STALKER_zone_{name}"] for name in names) == expected
    before = dict(variables)
    script.run("STALKER_reinforce_containment", 698)
    assert variables == before
    assert script.nodes[698]["flags"]["STALKER_zone_reinforced"] == 180


def test_rule_defaults_and_event_ids_match_the_isolated_milestone():
    rules = read("common/game_rules/10_STALKER_game_rules.txt")
    master = script_block(rules, "rule_stalker_scenario")
    assert ("name", "=", "DISABLED", None) in entries(script_block(master, "default"))
    reference = script_block(rules, "rule_stalker_kaimanov_global_zones")
    assert ("name", "=", "REFERENCE_MAP", None) in entries(
        script_block(reference, "default")
    )
    events = read("events/STALKER.txt")
    assert set(re.findall(r"\bid = (STALKER\.\d+)", events)) == {
        "STALKER.1",
        "STALKER.2",
    }
    text = read("localisation/english/MD_STALKER_l_english.yml")
    assert "event_target:STALKER_zone_event_target.GetName" not in text


def test_notice_sprites_match_upstream_definitions_with_exact_case():
    sprites = set()
    for path in (ROOT / "interface").glob("*.gfx"):
        sprites.update(
            re.findall(
                r'\bname\s*=\s*"(GFX_[^"]+)"', path.read_text(encoding="utf-8-sig")
            )
        )
    pictures = set(re.findall(r"\bpicture = (GFX_\w+)", read("events/STALKER.txt")))
    assert pictures <= sprites, pictures - sprites
