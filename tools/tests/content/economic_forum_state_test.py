"""Source-level regressions for forum objections, UI invalidation and bid dialogs."""

import operator
import re

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
        self.tag = "SIN"
        self.date = "2020.1.1"
        self.stability = 0.5
        self.war = False
        self.roll = 0
        self.events = []
        self.refreshes = 0

    def name(self, token):
        if "^" in token and not token.endswith("^num"):
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
            return not any(self._condition(child) for child in node.children)
        if key == "tooltip":
            return True
        if key == "check_variable":
            return all(
                COMPARISONS[child.op](self.number(child.key), self.number(child.value))
                for child in node.children
            )
        if key == "is_in_array":
            array = value(node, "array") or node.children[0].key
            member = value(node, "value") or node.children[0].value
            return any(
                self.number(f"{array}^{index}") == self.number(member)
                for index in range(int(self.number(f"{array}^num")))
            )
        if key == "original_tag":
            return self.tag == node.value
        if key == "has_stability":
            return COMPARISONS[node.op](self.stability, float(node.value))
        if key == "has_war":
            return self.war == (node.value == "yes")
        if key == "date":
            return COMPARISONS[node.op](
                tuple(map(int, self.date.split("."))),
                tuple(map(int, node.value.split("."))),
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
                    amount *= self.number(value(target, "multiply") or "1")
                    amount += self.number(value(target, "add") or "0")
                else:
                    amount = self.number(target.value)
                self.variables[name] = amount + (
                    self.variables.get(name, 0) if key.startswith("add_") else 0
                )
            elif key == "resize_array":
                array = value(node, "array")
                size = int(self.number(value(node, "size")))
                old_size = int(self.variables.get(f"{array}^num", 0))
                for index in range(old_size, size):
                    self.variables[f"{array}^{index}"] = self.number(
                        value(node, "value")
                    )
                self.variables[f"{array}^num"] = size
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


# Slot: decision suffix, month, identity tracks, eligible founders, PP cost, first year.
_NEW_FORUMS = {
    9: ("asean", 2, (0, 4, 5), "SIN MAY IND SIA VIE", 100, 2000),
    10: ("south_asian", 7, (0, 4, 5), "RAJ BAN SRI NEP", 100, 2000),
    11: ("pacific", 8, (1, 4, 5), "FIJ PAP SAM", 50, 2000),
    12: ("caribbean", 12, (2, 4, 5), "JAM TRI BAR", 50, 2000),
    13: ("andean", 2, (1, 4, 5), "COL PRU ECU BOL", 100, 2000),
    14: ("southern_cone", 7, (1, 2, 4), "BRA ARG URG PAR", 100, 2000),
    15: ("maghreb", 8, (1, 2, 4), "MOR ALG TUN", 100, 2000),
    16: ("adriatic", 12, (0, 2, 4), "CRO SLV ALB", 50, 2000),
    17: ("east_african", 3, (0, 4, 5), "KEN TNZ UGA RWA", 50, 2000),
    18: ("tokyo", 9, (0, 2, 3), "JAP", 100, 2000),
    19: ("astana", 5, (1, 2, 4), "KAZ", 100, 2008),
    20: ("fii", 10, (0, 1, 2), "SAU", 100, 2017),
}


@pytest.mark.parametrize("array", ["host", "state_led", "prestige", "month"])
def test_registry_has_twenty_one_aligned_slots_and_preserves_incumbents(array):
    entries = [
        value(node, f"global.econ_forum_{array}")
        for node in EFFECTS["econ_forum_setup"].children
        if node.key == "add_to_array"
        and value(node, f"global.econ_forum_{array}") is not None
    ]
    expected = {
        "host": ["SWI", "0", "SOV"] + ["0"] * 18,
        "state_led": ["0"] + ["1"] * 20,
        "prestige": ["80", "0", "35"] + ["0"] * 18,
        "month": list(
            map(
                str,
                [1, 9, 6, 3, 11, 5, 10, 4, 1]
                + [row[1] for row in _NEW_FORUMS.values()],
            )
        ),
    }
    assert entries == expected[array]


def test_all_forum_array_allocations_and_size_guards_match_registry():
    allocations = {}
    for node in _walk(list(EFFECTS.values())):
        if node.key == "resize_array":
            array = value(node, "array")
            size = value(node, "size")
            allocations.setdefault(array, set()).add(size)
            assert size not in {"9", "54"}, array
        if node.key == "check_variable":
            for child in node.children:
                if child.key.endswith("^num"):
                    assert child.value != "9", child.key
    for array, sizes in allocations.items():
        if array in {"global.econ_forum_tracks", "global.econ_forum_track_prestige"}:
            assert sizes == {"126"}
        elif array.startswith("global.econ_forum_") or array in {
            "econ_forum_status",
            "econ_forum_last",
            "econ_forum_streak",
            "econ_forum_agenda",
            "econ_forum_sponsor_cycle",
            "econ_forum_bid_cycle",
            "econ_forum_boycott",
            "econ_forum_boycott_cycle",
            "econ_forum_keynote_booked",
            "econ_forum_request_cycle",
            "econ_forum_ceremony",
            "econ_forum_keynote_hard",
            "econ_forum_room",
        }:
            assert sizes == {"21"}, array
    assert {
        "global.econ_forum_cycle",
        "global.econ_forum_guest_speakers",
        "global.econ_forum_tracks",
        "global.econ_forum_track_prestige",
    } <= allocations.keys()


@pytest.mark.parametrize("size", [0, 9, 20, 21])
def test_country_arrays_initialize_through_highest_slot_without_reset(size):
    forum = ForumScript()
    arrays = {
        value(node, "array")
        for node in _walk(EFFECTS["econ_forum_ensure_country_arrays"].children)
        if node.key == "resize_array"
    }
    for array in arrays:
        forum.variables[f"{array}^num"] = size
        for index in range(size):
            forum.variables[f"{array}^{index}"] = 7
    forum.execute(EFFECTS["econ_forum_ensure_country_arrays"].children)
    for array in arrays:
        assert forum.variables[f"{array}^num"] == 21
        assert [forum.variables[f"{array}^{i}"] for i in range(21)] == [7] * size + [
            0
        ] * (21 - size)


@pytest.mark.parametrize("slot", _NEW_FORUMS)
def test_new_forum_identity_selects_exactly_three_tracks(slot):
    forum = ForumScript()
    forum.variables["ef_i"] = slot
    selected = []
    for track in range(6):
        forum.variables["ef_t"] = track
        if forum.condition(TRIGGERS["econ_forum_track_in_identity"].children):
            selected.append(track)
    assert tuple(selected) == _NEW_FORUMS[slot][2]


@pytest.mark.parametrize("slot", [0, 8, 9, 20])
def test_track_selection_caps_at_three_without_touching_neighbor_forum(slot):
    forum = ForumScript()
    forum.variables["ef_i"] = slot
    for track in (5, 5, 0, 4, 1):
        forum.variables["ef_t"] = track
        forum.execute(EFFECTS["econ_forum_select_track"].children)
    assert forum.variables[f"global.econ_forum_track_count^{slot}"] == 3
    assert {
        key
        for key, val in forum.variables.items()
        if key.startswith("global.econ_forum_tracks^") and val
    } == {f"global.econ_forum_tracks^{slot * 6 + track}" for track in (0, 4, 5)}


def _child(node, key):
    return next(child for child in node.children if child.key == key)


@pytest.mark.parametrize("slot", _NEW_FORUMS)
def test_new_forum_founders_cost_dates_and_fresh_availability(slot):
    suffix, _, _, founders, cost, year = _NEW_FORUMS[slot]
    category = _definitions("common/decisions/econ_forum_decisions.txt")[
        "econ_forum_category"
    ]
    decision = _child(category, f"econ_forum_found_{suffix}")
    assert value(decision, "cost") == str(cost)
    assert value(decision, "fire_only_once") == "yes"
    visible = _child(decision, "visible")
    available = _child(decision, "available")
    forum = ForumScript()
    forum.date = f"{year}.1.1"
    for tag in founders.split():
        forum.tag = tag
        assert forum.condition(visible.children), tag
        assert forum.condition(available.children), tag
    forum.tag = "USA"
    assert not forum.condition(visible.children)
    forum.tag = founders.split()[0]
    for key in (
        "econ_forum_hosted",
        f"global.econ_forum_host^{slot}",
        f"global.econ_forum_seat^{slot}",
    ):
        forum.variables[key] = 1
        assert not forum.condition(available.children), key
        del forum.variables[key]
    forum.war = True
    assert not forum.condition(available.children)
    forum.war = False
    forum.stability = 0.4
    assert not forum.condition(available.children)
    forum.stability = 0.5
    if year > 2000:
        forum.date = f"{year-1}.12.31"
        assert not forum.condition(available.children)
    complete = list(_walk(_child(decision, "complete_effect").children))
    assert any(
        node.key == "set_temp_variable" and value(node, "ef_i") == str(slot)
        for node in complete
    )
    assert any(
        node.key == "econ_forum_found" and node.value == "yes" for node in complete
    )
    ai = _child(decision, "ai_will_do")
    assert float(value(ai, "base")) == 0.1
    modifier = _child(ai, "modifier")
    assert value(modifier, "factor") == "0"
    reserve = _child(modifier, "has_political_power")
    assert reserve.op == "<" and float(reserve.value) >= cost + 50


@pytest.mark.parametrize("slot", _NEW_FORUMS)
def test_new_forum_core_members_cover_founders_and_regional_partners(slot):
    branch = next(
        node
        for node in _walk(TRIGGERS["econ_forum_is_core_member"].children)
        if node.key == "AND"
        and any(
            child.key == "check_variable" and value(child, "ef_i") == str(slot)
            for child in node.children
        )
    )
    forum = ForumScript()
    forum.variables["ef_i"] = slot
    partners = {18: " KOR CHI TAI", 19: " UZB KYR TAJ TRK", 20: " UAE QAT KUW OMA BHR"}
    for tag in (_NEW_FORUMS[slot][3] + partners.get(slot, "")).split():
        forum.tag = tag
        assert forum.condition(branch.children), tag
    forum.tag = "USA"
    assert not forum.condition(branch.children)


# Getter: scope path, variable (or state flag), localization prefix.
_NAME_CONTEXTS = {
    "name_hosted": ((), "econ_forum_hosted", "name"),
    "name_invited": (
        ("event_target:econ_forum_invite_seat",),
        "has_state_flag",
        "name",
    ),
    "name_founded": (("FROM",), "econ_forum_hosted", "name"),
    "name_news_rival": (("FROM",), "econ_forum_news_rival", "name"),
    "row_name": ((), "v", "short"),
    "row_full_name": ((), "v", "name"),
    "leader_name": ((), "econ_forum_screen_leader^v", "short"),
    "name_bid": ((), "econ_forum_bid_forum", "name"),
    "name_ceremony": (
        ("event_target:econ_forum_ceremony_host",),
        "econ_forum_hosted",
        "name",
    ),
    "name_request": ((), "econ_forum_request_forum", "name"),
    "name_room": (("event_target:econ_forum_room_host",), "econ_forum_hosted", "name"),
    "name_talks": (
        ("event_target:econ_forum_talks_host",),
        "econ_forum_hosted",
        "name",
    ),
}


@pytest.mark.parametrize("getter", _NAME_CONTEXTS)
@pytest.mark.parametrize("slot", range(21))
def test_every_name_context_resolves_registry_slot_with_correct_scope(getter, slot):
    definitions = script_nodes(
        (
            REPO_ROOT
            / "common/scripted_localisation/01_econ_forum_scripted_localisation.txt"
        ).read_text(encoding="utf-8")
    )
    definition = next(
        node for node in definitions if value(node, "name") == f"econ_forum_{getter}"
    )
    scopes, variable, prefix = _NAME_CONTEXTS[getter]
    matches = []
    fallback = None
    for text in definition.children:
        if text.key != "text":
            continue
        gates = [node for node in text.children if node.key == "trigger"]
        if not gates:
            fallback = value(text, "localization_key")
            continue
        gate = gates[0]
        for scope in scopes:
            gate = _child(gate, scope)
        if variable == "has_state_flag":
            match = value(gate, variable) == f"econ_forum_seat_{slot}"
        else:
            comparison = _child(_child(gate, "check_variable"), variable)
            assert comparison.op == "="
            match = comparison.value == str(slot)
        if match:
            matches.append(value(text, "localization_key"))
    assert matches == [f"econ_forum_{prefix}_{slot}"] or (
        slot == 0 and not matches and fallback == f"econ_forum_{prefix}_0"
    )


@pytest.mark.parametrize("slot", _NEW_FORUMS)
def test_new_forum_invitation_seat_flags_and_english_keys_exist(slot):
    branches = [
        node
        for node in _walk(EFFECTS["econ_forum_register_host"].children)
        if node.key == "if"
        and any(
            flag.key == "set_state_flag" and flag.value == f"econ_forum_seat_{slot}"
            for flag in node.children
        )
    ]
    assert len(branches) == 1
    limit = _child(branches[0], "limit")
    assert value(_child(limit, "check_variable"), "ef_i") == str(slot)
    text = (REPO_ROOT / "localisation/english/MD_econ_forum_l_english.yml").read_text(
        encoding="utf-8-sig"
    )
    suffix = _NEW_FORUMS[slot][0]
    for key in (
        f"econ_forum_name_{slot}",
        f"econ_forum_short_{slot}",
        f"econ_forum_found_{suffix}",
        f"econ_forum_found_{suffix}_desc",
        f"econ_forum_found_{suffix}_tt",
    ):
        assert re.search(rf'^\s*{key}:\d?\s+"[^"\n]+"', text, re.MULTILINE), key


def test_forum_rows_remain_dynamic_and_scrollable_without_vertical_slot_cap():
    gui = _definitions("interface/MD_international_forums.gui")
    panel = next(
        node
        for node in _walk(list(gui.values()))
        if value(node, "name") == "forums_rows_panel"
    )
    assert value(panel, "verticalScrollbar")
    grid = next(node for node in panel.children if node.key == "gridboxType")
    assert value(grid, "name") == "forums_rows_grid"
    assert not any(node.key == "max_slots_vertical" for node in grid.children)
    scripted = _definitions("common/scripted_guis/01_international_forums_gui.txt")
    rows = next(
        node
        for node in _walk(list(scripted.values()))
        if node.key == "forums_rows_grid"
    )
    assert value(rows, "array") == "econ_forum_screen_rows"
    loop = next(
        node
        for node in EFFECTS["econ_forum_build_screen"].children
        if node.key == "for_loop_effect"
    )
    assert value(loop, "end") == "global.econ_forum_host^num"
    assert any(
        node.key == "add_to_array"
        and value(node, "array") == "econ_forum_screen_rows"
        and value(node, "value") == "es_i"
        for node in _walk(loop.children)
    )


@pytest.mark.parametrize("array", ["cycle", "guest_speakers"])
@pytest.mark.parametrize("size", [0, 20, 21])
def test_global_cycle_arrays_initialize_highest_slot_and_preserve_existing(array, size):
    name = f"global.econ_forum_{array}"
    branch = next(
        node
        for node in EFFECTS["econ_forum_open_preparation"].children
        if node.key == "if"
        and any(
            child.key == "resize_array" and value(child, "array") == name
            for child in node.children
        )
    )
    forum = ForumScript()
    forum.variables[f"{name}^num"] = size
    for index in range(size):
        forum.variables[f"{name}^{index}"] = 7
    forum.execute([branch])
    assert forum.variables[f"{name}^num"] == 21
    assert [forum.variables[f"{name}^{i}"] for i in range(21)] == [7] * size + [0] * (
        21 - size
    )


# Tag, already hosting, regional-power membership, category visibility.
_CATEGORY_VISIBILITY = {
    **{
        f"new founder {tag}": (tag, False, False, True)
        for row in _NEW_FORUMS.values()
        for tag in row[3].split()
    },
    **{
        f"existing founder {tag}": (tag, False, False, True)
        for tag in "POL CZE HUN SLO CHI NRY DEN ICE FIN SWE CAN SOV USA".split()
    },
    "unrelated minor": ("BHU", False, False, False),
    "existing host": ("BHU", True, False, True),
    "regional power": ("BHU", False, True, True),
}


@pytest.mark.parametrize(
    "tag,hosted,regional,visible",
    _CATEGORY_VISIBILITY.values(),
    ids=_CATEGORY_VISIBILITY,
)
def test_founders_can_reach_decision_category_without_power_rank(
    tag, hosted, regional, visible
):
    category = _definitions("common/decisions/categories/00_econ_forum_categories.txt")[
        "econ_forum_category"
    ]
    forum = ForumScript()
    forum.tag = tag
    if hosted:
        forum.variables["econ_forum_hosted"] = 0
    if regional:
        forum.variables.update(
            {
                "global.PR_regional_or_greater_powers^num": 1,
                "global.PR_regional_or_greater_powers^0": 1,
            }
        )
    assert forum.condition(_child(category, "visible").children) is visible


@pytest.mark.parametrize("slot", [1, *range(3, 21)])
@pytest.mark.parametrize("state", ["unfounded", "occupied", "vacant"])
def test_standing_getters_resolve_own_slot_for_occupied_and_vacant_seats(slot, state):
    definitions = script_nodes(
        (
            REPO_ROOT
            / "common/scripted_localisation/01_econ_forum_scripted_localisation.txt"
        ).read_text(encoding="utf-8")
    )
    definition = next(
        node
        for node in definitions
        if value(node, "name") == f"econ_forum_standing_line_{slot}"
    )
    forum = ForumScript()
    # Neighboring forums are occupied; they must not determine this slot's text.
    for neighbor in range(21):
        forum.variables[f"global.econ_forum_host^{neighbor}"] = 1
        forum.variables[f"global.econ_forum_seat^{neighbor}"] = 1
    forum.variables[f"global.econ_forum_host^{slot}"] = int(state == "occupied")
    forum.variables[f"global.econ_forum_seat^{slot}"] = int(state != "unfounded")
    selected = next(
        value(text, "localization_key")
        for text in definition.children
        if text.key == "text"
        and all(
            forum.condition(trigger.children)
            for trigger in text.children
            if trigger.key == "trigger"
        )
    )
    expected = {
        "unfounded": "econ_forum_standing_unfounded",
        "occupied": f"econ_forum_standing_{slot}",
        "vacant": f"econ_forum_standing_{slot}_vacant",
    }
    assert selected == expected[state]
