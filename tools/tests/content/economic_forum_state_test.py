"""Source-level regressions for forum objections, UI invalidation and bid dialogs."""

import operator

import pytest
from equipment_variant_context import script_nodes, value
from shared.paths import REPO_ROOT


def _definitions(path):
    return {
        node.key: node
        for node in script_nodes((REPO_ROOT / path).read_text(encoding="utf-8"))
    }


TRIGGERS = _definitions("common/scripted_triggers/01_econ_forum_triggers.txt")
TRIGGERS.update(_definitions("common/scripted_triggers/01_political_triggers.txt"))
EFFECTS = _definitions("common/scripted_effects/01_econ_forum_effects.txt")
BID_EVENT = next(
    node
    for node in script_nodes(
        (REPO_ROOT / "events/EconomicForums.txt").read_text(encoding="utf-8")
    )
    if value(node, "id") == "econ_forum.6"
)
COMPARISONS = {"=": operator.eq, ">": operator.gt, "<": operator.lt}


def _walk(nodes):
    for node in nodes:
        yield node
        yield from _walk(node.children)


def _cash_charges(nodes):
    charges = []
    for index, node in enumerate(nodes):
        if node.key == "modify_treasury_effect":
            assert index > 0, "Cash charge has no local amount"
            amount = nodes[index - 1]
            assert amount.key == "set_temp_variable"
            assert len(amount.children) == 1
            assert amount.children[0].key == "treasury_change"
            assert not amount.children[
                0
            ].children, "Forum prices must not scale with GDP"
            charges.append(float(amount.children[0].value))
        charges.extend(_cash_charges(node.children))
    return charges


def _effect_closure(name, seen=None):
    seen = set() if seen is None else seen
    if name in seen:
        return
    seen.add(name)
    for node in _walk(EFFECTS[name].children):
        yield node
        if node.key in EFFECTS and node.value == "yes":
            yield from _effect_closure(node.key, seen)


def test_forum_cash_inventory_has_only_fixed_one_off_purchases():
    decisions = _definitions("common/decisions/econ_forum_decisions.txt")
    roots = {f"effect:{name}": node for name, node in EFFECTS.items()}
    roots.update(
        {
            f"decision:{node.key}": node
            for node in decisions["econ_forum_category"].children
        }
    )
    assert {
        name: charges
        for name, node in roots.items()
        if (charges := _cash_charges(node.children))
    } == {
        "effect:econ_forum_sponsor_session": [-1.5],
        "effect:econ_forum_ai_prepare": [-3, -2],
        "decision:econ_forum_message_media": [-2],
        "decision:econ_forum_secure_sponsors": [-3],
    }


@pytest.mark.parametrize(
    "effect",
    [
        "setup",
        "send_invitation",
        "send_personal_invitation",
        "answer_invitation",
        "select_track",
        "book_ceremony",
        "record_attendance",
        "corporate_delegations",
        "reward_host",
    ],
)
def test_regular_forum_flows_do_not_charge_cash_or_borrow(effect):
    for node in _effect_closure(f"econ_forum_{effect}"):
        assert node.key not in {
            "modify_treasury_effect",
            "modify_debt_effect",
            "small_expenditure",
            "medium_expenditure",
            "large_expenditure",
        }
        if node.key in {"set_variable", "add_to_variable", "subtract_from_variable"}:
            assert node.children[0].key not in {"treasury", "debt", "treasury_rate"}


def test_forum_cash_uses_the_canonical_unscaled_billion_unit():
    budget = _definitions("common/scripted_effects/00_budget_effects.txt")
    writes = [
        node
        for node in _walk(budget["modify_treasury_effect"].children)
        if node.key == "add_to_variable"
    ]
    assert len(writes) == 1
    assert [(node.key, node.value, node.children) for node in writes[0].children] == [
        ("treasury", "treasury_change", [])
    ]


class ForumScript:
    """Execute the tested source branches; no game-engine or GUI simulation."""

    def __init__(self, *, outlook="neutrality", party=14, elections=True, ai=False):
        self.variables = {"THIS.id": 1, "ruling_party": party}
        self.outlook = outlook
        self.elections = elections
        self.ai = ai
        self.pp = 100
        self.roll = 0
        self.events = []
        self.refreshes = 0

    def name(self, token):
        if "^" in token:
            array, index = token.split("^", 1)
            return f"{array}^{int(self.number(index))}"
        return token

    def number(self, token):
        try:
            return float(token)
        except ValueError:
            return self.variables.get(self.name(token), 0)

    def condition(self, nodes):
        return all(self._condition(node) for node in nodes)

    def _condition(self, node):
        key = node.key
        if key in {"AND", "custom_trigger_tooltip"}:
            return self.condition(node.children)
        if key == "OR":
            return any(self._condition(child) for child in node.children)
        if key == "NOT":
            return not self.condition(node.children)
        if key == "tooltip":
            return True
        if key == "check_variable":
            return all(
                COMPARISONS[child.op](self.number(child.key), self.number(child.value))
                for child in node.children
            )
        if key == "has_variable":
            return self.name(node.value) in self.variables
        if key == "has_government":
            return self.outlook == node.value
        if key == "has_elections":
            return self.elections == (node.value == "yes")
        if key == "is_ai":
            return self.ai == (node.value == "yes")
        if key == "has_idea":
            return False
        if key == "has_political_power":
            return COMPARISONS[node.op](self.pp, self.number(node.value))
        if key in TRIGGERS:
            return self.condition(TRIGGERS[key].children)
        raise AssertionError(f"Unsupported forum condition: {key}")

    def execute(self, nodes):
        matched = False
        for node in nodes:
            key = node.key
            if key in {"if", "else_if"}:
                limit = next(child for child in node.children if child.key == "limit")
                take = self.condition(limit.children) and (key == "if" or not matched)
                matched = take if key == "if" else matched or take
                if take:
                    self.execute([c for c in node.children if c.key != "limit"])
            elif key == "else":
                if not matched:
                    self.execute(node.children)
                matched = True
            elif key == "hidden_effect":
                self.execute(node.children)
            elif key in {
                "set_variable",
                "set_temp_variable",
                "add_to_variable",
                "add_to_temp_variable",
            }:
                target = node.children[0]
                name = self.name(target.key)
                if target.children:
                    amount = self.number(value(target, "value"))
                    amount += self.number(value(target, "add") or "0")
                else:
                    amount = self.number(target.value)
                self.variables[name] = amount + (
                    self.variables.get(name, 0) if key.startswith("add_") else 0
                )
            elif key == "clear_variable":
                self.variables.pop(self.name(node.value), None)
            elif key == "set_temp_variable_to_random":
                self.variables[value(node, "var")] = self.roll
            elif key == "add_political_power":
                self.pp += self.number(node.value)
            elif key == "country_event":
                self.events.append(node.value)
            elif key == "econ_forum_refresh_open_screens":
                self.refreshes += 1
            elif key in EFFECTS:
                self.execute(EFFECTS[key].children)
            elif key not in {
                "name",
                "trigger",
                "log",
                "custom_effect_tooltip",
                "ai_chance",
            }:
                raise AssertionError(f"Unsupported forum effect: {key}")

    def bid(self, forum):
        self.variables["v"] = forum
        self.execute(EFFECTS["econ_forum_bid_to_speak"].children)

    def dismiss(self, option):
        choice = next(
            node
            for node in BID_EVENT.children
            if node.key == "option" and value(node, "name") == f"econ_forum.6.{option}"
        )
        gates = [node for node in choice.children if node.key == "trigger"]
        assert all(self.condition(gate.children) for gate in gates)
        self.execute(choice.children)


# Speaker, outlook, ruling-party slot, elections, whether the government objects.
_OBJECTIONS = {
    "Land Western autocracy": (1, "democratic", 0, False, False),
    "Land elected Non-Aligned": (1, "neutrality", 14, True, True),
    "Zizek actual fascists": (5, "nationalist", 21, False, True),
    "Zizek Salafist kingdom": (5, "fascism", 10, False, False),
    "Zizek Salafist caliphate": (5, "fascism", 11, False, False),
    "Dimon communist state": (6, "communism", 4, False, True),
    "Dimon anarchist communists": (6, "communism", 5, True, True),
    "Dimon Non-Aligned communists": (6, "neutrality", 19, False, True),
    "Dimon Emerging autocrats": (6, "communism", 7, False, False),
    "Dimon Shiite government": (6, "communism", 9, False, False),
}


@pytest.mark.parametrize(
    "speaker,outlook,party,elections,objects", _OBJECTIONS.values(), ids=_OBJECTIONS
)
def test_speaker_objections_follow_government_not_outlook_labels(
    speaker, outlook, party, elections, objects
):
    forum = ForumScript(outlook=outlook, party=party, elections=elections)
    forum.variables.update({"ef_i": 0, "global.econ_forum_controversial^0": speaker})
    assert (
        forum.condition(TRIGGERS["econ_forum_objects_to_speaker"].children) is objects
    )


@pytest.mark.parametrize("effect", ["answer_invitation", "decline_ceremony"])
def test_event_replies_invalidate_open_forum_screens_after_all_branches(effect):
    tail = EFFECTS[f"econ_forum_{effect}"].children[-1]
    assert (tail.key, tail.value) == ("econ_forum_refresh_open_screens", "yes")


def _guest(*, ai=False):
    forum = ForumScript(ai=ai)
    for index in (0, 1):
        forum.variables.update(
            {
                f"global.econ_forum_host^{index}": index + 10,
                f"global.econ_forum_preparing^{index}": 1,
                f"global.econ_forum_cycle^{index}": 1,
                f"global.econ_forum_speakers^{index}": 0,
                f"econ_forum_status^{index}": 3,
            }
        )
    return forum


@pytest.mark.parametrize("first", [0, 1])
@pytest.mark.parametrize("won,option", [(True, "a"), (True, "b"), (False, "a")])
def test_pending_bid_keeps_its_context_until_either_result_option(first, won, option):
    forum = _guest()
    forum.roll = 0 if won else 99
    forum.bid(first)
    assert forum.pp == 75
    assert forum.variables["econ_forum_bid_forum"] == first
    assert forum.variables["econ_forum_bid_result"] == int(won)
    context = dict(forum.variables)
    forum.roll = 99 if won else 0
    forum.bid(1 - first)
    assert forum.events == ["econ_forum.6"]
    assert forum.pp == 75
    assert {key: val for key, val in forum.variables.items() if key != "v"} == {
        key: val for key, val in context.items() if key != "v"
    }
    forum.dismiss(option)
    assert "econ_forum_bid_forum" not in forum.variables
    assert "econ_forum_bid_result" not in forum.variables
    assert "econ_forum_bid_tag" not in forum.variables
    assert forum.variables.get(f"econ_forum_keynote_hard^{first}", 0) == int(
        option == "b"
    )
    assert forum.variables.get(f"econ_forum_keynote_hard^{1 - first}", 0) == 0
    assert forum.refreshes == 2
    forum.roll = 0
    forum.bid(1 - first)
    assert forum.events == ["econ_forum.6", "econ_forum.6"]
    assert forum.pp == 50
    assert forum.variables["econ_forum_bid_forum"] == 1 - first


def test_ai_bids_have_no_pending_human_result_lock():
    forum = _guest(ai=True)
    forum.bid(0)
    forum.bid(1)
    assert forum.pp == 50
    assert forum.events == []
    assert "econ_forum_bid_forum" not in forum.variables
    assert forum.variables["econ_forum_keynote_booked^0"] == 2
    assert forum.variables["econ_forum_keynote_booked^1"] == 2
