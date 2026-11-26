"""Focus reward audit: the parser, reward totals, branches, forks, stacking and the CLI."""

import json

import focus_reward_audit as A
import pytest
from shared.suite import run_tool_script, write_text, write_tree

# One if/else effect (the richest branch counts once) and one loop that selects two
# states, both priced by their first constant treasury_change.
_STANDARD_EFFECTS = """one_state_widget_plant = {
	if = {
		limit = { free_building_slots = { building = widget_plant size > 0 } }
		add_building_construction = { type = widget_plant level = 1 instant_build = yes }
	}
	else = {
		ROOT = {
			every_controlled_state = {
				limit = { free_shared_building_slots = yes }
				random_select_amount = 1
				add_building_construction = { type = widget_plant level = 1 }
			}
		}
	}
	CONTROLLER = {
		if = { limit = { NOT = { check_variable = { skip_payment = 1 } } }
			set_temp_variable = { treasury_change = -7.5 }
			modify_treasury_effect = yes
		}
	}
}

two_random_widget_plant = {
	every_controlled_state = {
		limit = { free_shared_building_slots = yes }
		random_select_amount = 2
		add_building_construction = { type = widget_plant level = 1 }
	}
	if = { limit = { NOT = { check_variable = { skip_payment = 1 } } }
		set_temp_variable = { treasury_change = -15 }
		modify_treasury_effect = yes
	}
}

unrelated_effect = { add_stability = 0.1 }
"""

# TST_loop_effect calls itself: expansion must stop.
_TAG_EFFECTS = """TST_bonus_effect = { add_political_power = 10 }
TST_loop_effect = {
	TST_loop_effect = yes
	add_stability = 0.01
}
"""

_DYNAMIC_MODIFIERS = """TST_dyn = {
	icon = "GFX_x"
	custom_modifier_tooltip = TST_tooltip
	tst_output_factor = TST_output_var
	enable = { always = yes }
}
"""

_IDEAS = """ideas = {
	country = {
		TST_idea_a = { modifier = { tst_output_factor = 0.15 } }
		TST_idea_b = { modifier = { tst_output_factor = 0.10 tst_flat_value = 4 } }
		TST_idea_alt = { modifier = { tst_output_factor = 0.15 } }
		TST_idea_old = { modifier = { tst_output_factor = 0.20 } }
		TST_idea_new = { modifier = { tst_output_factor = 0.25 } }
		TST_idea_six = { modifier = { m1 = 1 m2 = 1 m3 = 1 m4 = 1 m5 = 1 m6 = 1 } }
		TST_idea_five = { modifier = { m1 = 1 m2 = 1 m3 = 1 m4 = 1 m5 = 1 } }
			TST_idea_gate_a = { modifier = { stability_factor = 0.15 } }
			TST_idea_gate_b = { modifier = { stability_factor = 0.15 } }
			TST_idea_gate_big = { modifier = { stability_factor = 0.20 } }
			TST_idea_gate_shared = { modifier = { stability_factor = 0.10 } }
	}
}
"""

_CONTEXT = {
    "common/scripted_effects/00_scripted_effects.txt": _STANDARD_EFFECTS,
    "common/scripted_effects/tst_effects.txt": _TAG_EFFECTS,
    "common/dynamic_modifiers/tst.txt": _DYNAMIC_MODIFIERS,
    "common/ideas/tst.txt": _IDEAS,
}


def _focus(focus_id, *, after=(), against=(), available="", reward=""):
    """One focus of 7 days; `after` is one OR prerequisite, `against` its forks."""
    lines = [f"\t\tid = {focus_id}", "\t\tcost = 1"]
    if after:
        lines.append(
            "\t\tprerequisite = { " + " ".join(f"focus = {a}" for a in after) + " }"
        )
    if against:
        lines.append(
            "\t\tmutually_exclusive = { "
            + " ".join(f"focus = {a}" for a in against)
            + " }"
        )
    if available:
        lines.append("\t\tavailable = { " + available + " }")
    lines.append("\t\tcompletion_reward = {\n" + reward + "\n\t\t}")
    return "\tfocus = {\n" + "\n".join(lines) + "\n\t}\n"


def _tree(*focuses):
    return "focus_tree = {\n\tid = TST_tree\n" + "".join(focuses) + "}\n"


def _widgets(level):
    return f"add_building_construction = {{ type = widget_plant level = {level} }}"


def _mod(tmp_path, *focuses, events=""):
    files = {**_CONTEXT, "common/national_focus/tst.txt": _tree(*focuses)}
    if events:
        files["events/tst.txt"] = events
    return write_tree(tmp_path / "mod", files)


def _event(event_id, *options, immediate=""):
    """One country event; each option is the body of a named `option`."""
    lines = [f"country_event = {{\n\tid = {event_id}"]
    if immediate:
        lines.append(f"\timmediate = {{ {immediate} }}")
    lines += [
        f"\toption = {{ name = {event_id}.{chr(97 + n)} {body} }}"
        for n, body in enumerate(options)
    ]
    return "\n".join(lines) + "\n}\n"


def _audit(capsys, root, *args):
    A.main(["--tag", "TST", "--root", str(root), "--json", *map(str, args)])
    return json.loads(capsys.readouterr().out)


def _branch(report, root_id):
    return next(b for b in report["branches"] if b["root"] == root_id)


# --- parser -------------------------------------------------------------------

# case: (script text, the parsed nodes written back out)
_PARSE_CASES = {
    "a comment hides its brace": ("a = { b = 1 } # }", "{ a = { b = 1 } }"),
    "a string keeps its braces": ('log = "} { #"', '{ log = "} { #" }'),
    "bare tokens and comparisons": ("ids = { x y } n >= 3", "{ ids = { x y } n >= 3 }"),
    "a stray close brace does not end the file": ("a = 1 } b = 2", "{ a = 1 b = 2 }"),
}


@pytest.mark.parametrize(("text", "written"), _PARSE_CASES.values(), ids=_PARSE_CASES)
def test_parse_reads_blocks_without_trusting_braces_in_strings_and_comments(
    text, written
):
    assert A.show(A.parse(text)) == written


def test_parse_keeps_line_numbers():
    assert [node.line for node in A.parse("a = 1\n\nb = { c = 2 }\n")] == [1, 3]


# --- standard building effects ------------------------------------------------


def test_standard_effects_count_the_richest_branch_and_the_selected_states():
    table = A.standard_effects(A.parse(_STANDARD_EFFECTS))

    assert table == {
        "one_state_widget_plant": A.StandardEffect({"widget_plant": 1.0}, -7.5),
        "two_random_widget_plant": A.StandardEffect({"widget_plant": 2.0}, -15.0),
    }


# --- rewards ------------------------------------------------------------------

# case: (completion_reward body, always fields, conditional fields), fields as in reward_row
_REWARD_CASES = {
    "direct building": (
        _widgets(2),
        {"buildings": {"widget_plant": 2}},
        {},
    ),
    "standard effect: buildings and price": (
        "one_state_widget_plant = yes",
        {"buildings": {"widget_plant": 1}, "money": -7.5},
        {},
    ),
    "an offsite building has its own prefix": (
        "add_offsite_building = { type = widget_plant level = 2 }",
        {"buildings": {"offsite_widget_plant": 2}},
        {},
    ),
    "standard effect: a loop of two states": (
        "two_random_widget_plant = yes",
        {"buildings": {"widget_plant": 2}, "money": -15},
        {},
    ),
    "standard effect: skip_payment waives the price": (
        "set_temp_variable = { skip_payment = 1 } one_state_widget_plant = yes",
        {"buildings": {"widget_plant": 1}, "money": 0},
        {},
    ),
    "treasury constants add up before the payment": (
        "set_temp_variable = { treasury_change = -20 } "
        "add_to_temp_variable = { treasury_change = -5 } modify_treasury_effect = yes",
        {"money": -25, "unquantified": []},
        {},
    ),
    "treasury formula is unquantified, not zero": (
        "set_temp_variable = { treasury_change = { value = gdp_total multiply = -0.02 } } "
        "modify_treasury_effect = yes",
        {"money": 0, "unquantified": ["money { value = gdp_total multiply = -0.02 }"]},
        {},
    ),
    "a treasury operation that is no sum is unquantified": (
        "set_temp_variable = { treasury_change = 10 } "
        "multiply_temp_variable = { treasury_change = 2 } modify_treasury_effect = yes",
        {"money": 0, "unquantified": ["money multiply_temp_variable 2"]},
        {},
    ),
    "pp, stability and war support": (
        "add_political_power = 25 add_stability = 0.05 add_war_support = -0.5",
        {"pp": 25, "stability": 0.05, "war_support": -0.5},
        {},
    ),
    "permanent and timed ideas": (
        "add_ideas = { TST_idea_a TST_idea_b } "
        "add_timed_idea = { idea = TST_idea_alt days = 365 }",
        {
            "permanent": ["TST_idea_a", "TST_idea_b"],
            "timed": [{"idea": "TST_idea_alt", "days": 365}],
        },
        {},
    ),
    "add_ideas with days is timed": (
        "add_ideas = { idea = TST_idea_alt days = 30 }",
        {"permanent": [], "timed": [{"idea": "TST_idea_alt", "days": 30}]},
        {},
    ),
    "a swap replaces and remove_ideas removes": (
        "swap_ideas = { remove_idea = TST_idea_old add_idea = TST_idea_new } "
        "remove_ideas = TST_idea_a",
        {
            "permanent": ["TST_idea_new"],
            "removed": ["TST_idea_old", "TST_idea_a"],
            "swaps": [{"from": "TST_idea_old", "to": "TST_idea_new"}],
        },
        {},
    ),
    "an if chain is conditional and counts its richest branch": (
        "if = { limit = { always = yes } add_political_power = 10 } "
        "else = { " + _widgets(3) + " }",
        {"pp": 0, "buildings": {}},
        {"pp": 0, "buildings": {"widget_plant": 3}},
    ),
    "a random_list is conditional": (
        "random_list = { 50 = { add_political_power = 30 } 50 = { add_political_power = 5 } }",
        {"pp": 0},
        {"pp": 30},
    ),
    "a random chance is conditional": (
        "random = { chance = 25 add_political_power = 30 }",
        {"pp": 0},
        {"pp": 30},
    ),
    "other countries are skipped": (
        "OTH = { add_political_power = 100 } every_other_country = { add_political_power = 200 } "
        "TST = { add_political_power = 1 }",
        {"pp": 1},
        {},
    ),
    "a state loop is counted once and says so": (
        "every_owned_state = { " + _widgets(1) + " }",
        {
            "buildings": {"widget_plant": 1},
            "unquantified": ["every_owned_state loop counted once"],
        },
        {},
    ),
    "a for_each_loop is counted once and says so": (
        "for_each_loop = { array = tst_list " + _widgets(1) + " }",
        {
            "buildings": {"widget_plant": 1},
            "unquantified": ["for_each_loop loop counted once"],
        },
        {},
    ),
    "a for_each_scope_loop is counted once and says so": (
        "for_each_scope_loop = { array = tst_list " + _widgets(1) + " }",
        {
            "buildings": {"widget_plant": 1},
            "unquantified": ["for_each_scope_loop loop counted once"],
        },
        {},
    ),
    "a while_loop_effect is counted once and says so": (
        "while_loop_effect = { limit = { always = yes } " + _widgets(1) + " }",
        {
            "buildings": {"widget_plant": 1},
            "unquantified": ["while_loop_effect loop counted once"],
        },
        {},
    ),
    "tag effects expand once": (
        "TST_bonus_effect = yes TST_loop_effect = yes",
        {"pp": 10, "stability": 0.01},
        {},
    ),
    "tooltips, strings and comments do not count": (
        'effect_tooltip = { add_political_power = 99 } log = "an { unclosed"\n'
        "# add_political_power = 7 }\nadd_political_power = 3",
        {"pp": 3},
        {},
    ),
    "dynamic modifier variables": (
        "add_to_variable = { TST_output_var = 0.5 tooltip = x_tt } "
        "subtract_from_variable = { TST_output_var = 0.25 } "
        "add_to_variable = { TST_unlinked_var = 5 }",
        {"variables": {"TST_output_var": 0.25}},
        {},
    ),
    "a variable amount is unquantified": (
        "add_to_variable = { TST_output_var = some_temp }",
        {"variables": {}, "unquantified": ["TST_output_var some_temp"]},
        {},
    ),
}


@pytest.fixture(scope="module")
def reward_focuses(tmp_path_factory):
    root = write_tree(
        tmp_path_factory.mktemp("rewards"),
        {
            **_CONTEXT,
            "common/national_focus/tst.txt": _tree(
                *(
                    _focus(f"TST_case_{n}", reward=case[0])
                    for n, case in enumerate(_REWARD_CASES.values())
                )
            ),
        },
    )
    ctx = A.load_context(root, "TST")
    _, focuses = A.read_focuses(root, "TST", [], ctx)
    return {focus.id: focus for focus in focuses}


@pytest.mark.parametrize(
    ("number", "case"), list(enumerate(_REWARD_CASES.values())), ids=_REWARD_CASES
)
def test_reward_totals(reward_focuses, number, case):
    _, always, conditional = case
    focus = reward_focuses[f"TST_case_{number}"]

    for reward, expected in ((focus.always, always), (focus.maybe, conditional)):
        row = A.reward_row(reward)
        assert {key: row[key] for key in expected} == expected


# --- branches, forks and stacking ---------------------------------------------


def _fork_tree():
    return (
        _focus("TST_root", reward=_widgets(1)),
        _focus(
            "TST_left", after=["TST_root"], against=["TST_right"], reward=_widgets(3)
        ),
        _focus(
            "TST_right", after=["TST_root"], against=["TST_left"], reward=_widgets(1)
        ),
        _focus("TST_left_child", after=["TST_left"], reward=_widgets(2)),
        _focus("TST_other_root", reward=_widgets(4)),
    )


def test_exclusive_forks_are_a_range_not_a_sum(tmp_path, capsys):
    report = _audit(capsys, _mod(tmp_path, *_fork_tree()))

    branch = _branch(report, "TST_root")
    assert branch["focuses"] == 4
    # root + right on the lightest path, root + left + left_child on the heaviest;
    # a sum of every focus would be 7.
    assert branch["metrics"]["buildings"] == {"min": 2, "max": 6}
    assert branch["metrics"]["days"] == {"min": 14, "max": 21}
    assert _branch(report, "TST_other_root")["metrics"]["buildings"] == {
        "min": 4,
        "max": 4,
    }


def test_a_fork_lists_what_each_alternative_leads_to(tmp_path, capsys):
    report = _audit(capsys, _mod(tmp_path, *_fork_tree()))

    [fork] = _branch(report, "TST_root")["forks"]
    assert [(arm["focus"], arm["focuses"], arm["buildings"]) for arm in fork] == [
        ("TST_left", 2, 5),
        ("TST_right", 1, 1),
    ]


def _stacking_tree():
    return (
        _focus("TST_s_root", reward="add_to_variable = { TST_output_var = 0.05 }"),
        _focus(
            "TST_s_a",
            after=["TST_s_root"],
            against=["TST_s_b"],
            reward="add_ideas = TST_idea_a",
        ),
        _focus(
            "TST_s_b",
            after=["TST_s_root"],
            against=["TST_s_a"],
            reward="add_ideas = TST_idea_alt",
        ),
        # idea_a again: an idea granted twice applies once.
        _focus(
            "TST_s_a_child",
            after=["TST_s_a"],
            reward="add_ideas = { TST_idea_b TST_idea_a }",
        ),
        _focus("TST_ladder_1", reward="add_ideas = TST_idea_old"),
        _focus(
            "TST_ladder_2",
            after=["TST_ladder_1"],
            reward="swap_ideas = { remove_idea = TST_idea_old add_idea = TST_idea_new }",
        ),
    )


def _stacked(report, root_id):
    return {
        row["key"]: (row["sum"], [source for source, _ in row["from"]])
        for row in _branch(report, root_id)["stacking"]
    }


def test_stacking_flags_the_best_path_and_not_the_alternatives_summed(tmp_path, capsys):
    report = _audit(capsys, _mod(tmp_path, *_stacking_tree()))

    # a-path: idea_a 0.15 + idea_b 0.10 + variable 0.05. Summing the alternative idea_alt
    # or the repeated idea_a would give 0.45 or more; tst_flat_value is no factor.
    assert _stacked(report, "TST_s_root") == {
        "tst_output_factor": (0.3, ["TST_idea_a", "TST_idea_b", "TST_output_var"])
    }


def test_stacking_drops_a_swapped_out_spirit(tmp_path, capsys):
    report = _audit(capsys, _mod(tmp_path, *_stacking_tree()))

    assert _stacked(report, "TST_ladder_1") == {
        "tst_output_factor": (0.25, ["TST_idea_new"])
    }


def test_stacking_judges_a_swap_ladder_by_its_last_rung(tmp_path, capsys):
    report = _audit(
        capsys,
        _mod(
            tmp_path,
            _focus("TST_w_root"),
            _focus(
                "TST_w_ladder",
                after=["TST_w_root"],
                against=["TST_w_flat"],
                reward="add_ideas = TST_idea_old",
            ),
            _focus(
                "TST_w_rung",
                after=["TST_w_ladder"],
                reward="swap_ideas = { remove_idea = TST_idea_old add_idea = TST_idea_new }",
            ),
            _focus(
                "TST_w_flat",
                after=["TST_w_root"],
                against=["TST_w_ladder"],
                reward="add_ideas = { TST_idea_a TST_idea_alt }",
            ),
        ),
    )

    # The ladder ends at 0.25 and the flat arm gives 0.30. Scoring the swapped-out
    # 0.20 as well would make the ladder look like 0.45 and pick it.
    assert _stacked(report, "TST_w_root") == {
        "tst_output_factor": (0.3, ["TST_idea_a", "TST_idea_alt"])
    }


# case: a modifier key stacking checks, besides the `_factor` one that the trees above use
_FACTOR_KEYS = {
    "_multiplier suffix": "tst_output_multiplier",
    "_modifier suffix": "tst_output_modifier",
}


@pytest.mark.parametrize("key", _FACTOR_KEYS.values(), ids=_FACTOR_KEYS)
def test_stacking_checks_multiplier_and_modifier_keys(key):
    assert A.is_factor(key)


def test_stacking_flags_only_what_passes_the_limit(tmp_path, capsys):
    report = _audit(capsys, _mod(tmp_path, *_stacking_tree()), "--stack-limit", "0.35")

    assert report["stack_limit"] == 0.35
    assert [row for b in report["branches"] for row in b["stacking"]] == []


def test_outliers_rank_density_and_flag_spirits_with_many_modifiers(tmp_path, capsys):
    report = _audit(
        capsys,
        _mod(
            tmp_path,
            *_fork_tree(),
            _focus("TST_spirits", reward="add_ideas = { TST_idea_six TST_idea_five }"),
        ),
        "--top",
        "2",
    )

    outliers = report["outliers"]
    assert [row["focus"] for row in outliers["buildings_per_day"]] == [
        "TST_other_root",
        "TST_left",
    ]
    assert outliers["buildings_per_day"][0]["types"] == {"widget_plant": 4}
    assert [(s["idea"], s["modifiers"]) for s in outliers["spirits"]] == [
        ("TST_idea_six", 6)
    ]


# --- path choices: flags and leaders -------------------------------------------


def _path_tree(kind, *gated):
    """A fork whose arms set TST_A and TST_B, then the focuses gated on them."""
    return (
        _focus("TST_root"),
        _focus(
            "TST_a",
            after=["TST_root"],
            against=["TST_b"],
            reward=f"set_{kind}_flag = TST_A " + _widgets(1),
        ),
        _focus(
            "TST_b",
            after=["TST_root"],
            against=["TST_a"],
            reward=f"set_{kind}_flag = TST_B",
        ),
        *gated,
    )


def _gated(focus_id, available, reward=""):
    return _focus(focus_id, after=["TST_root"], available=available, reward=reward)


def _buildings(report, root_id="TST_root"):
    bounds = _branch(report, root_id)["metrics"]["buildings"]
    return bounds["min"], bounds["max"]


# case: (available of a focus worth 5 buildings, lowest and highest buildings of the
# branch). Path a is worth 1 building and path b none, so ignoring the gate gives 5..6.
_GATE_PATHS = {
    "needs a flag of path a": ("has_KIND_flag = TST_A", (0, 6)),
    "needs a flag of path b": ("has_KIND_flag = TST_B", (1, 5)),
    "needs either flag": (
        "OR = { has_KIND_flag = TST_A has_KIND_flag = TST_B }",
        (5, 6),
    ),
    "needs a flag inside an AND": (
        "AND = { has_KIND_flag = TST_B always = yes }",
        (1, 5),
    ),
    "forbids a flag": ("NOT = { has_KIND_flag = TST_A }", (1, 5)),
}


@pytest.mark.parametrize("kind", ["global", "country"])
@pytest.mark.parametrize(
    ("available", "expected"), _GATE_PATHS.values(), ids=_GATE_PATHS
)
def test_branch_totals_count_only_paths_the_flags_allow(
    tmp_path, capsys, kind, available, expected
):
    gated = _gated("TST_gated", available.replace("KIND", kind), _widgets(5))

    report = _audit(capsys, _mod(tmp_path, *_path_tree(kind, gated)))

    assert _buildings(report) == expected


@pytest.mark.parametrize("kind", ["global", "country"])
def test_stacking_takes_one_path_flag_not_both(tmp_path, capsys, kind):
    tree = _path_tree(
        kind,
        _gated("TST_only_a", f"has_{kind}_flag = TST_A", "add_ideas = TST_idea_gate_a"),
        _gated("TST_only_b", f"has_{kind}_flag = TST_B", "add_ideas = TST_idea_gate_b"),
    )

    report = _audit(capsys, _mod(tmp_path, *tree), "--stack-limit", "0.1")

    # Both paths together would be 0.30.
    [row] = _branch(report, "TST_root")["stacking"]
    assert (row["key"], row["sum"], row["path"]) == (
        "stability_factor",
        0.15,
        [f"{kind} flag TST_A"],
    )
    assert [source for source, _ in row["from"]] == ["TST_idea_gate_a"]


def test_flags_set_below_an_exclusive_focus_are_paths_too(tmp_path, capsys):
    report = _audit(
        capsys,
        _mod(
            tmp_path,
            _focus("TST_root"),
            _focus("TST_x", after=["TST_root"], against=["TST_y"]),
            _focus("TST_y", after=["TST_root"], against=["TST_x"]),
            _focus("TST_x_deep", after=["TST_x"], reward="set_global_flag = TST_X"),
            _focus("TST_y_deep", after=["TST_y"], reward="set_global_flag = TST_Y"),
            _gated("TST_needs_x", "has_global_flag = TST_X", _widgets(2)),
            _gated("TST_needs_y", "has_global_flag = TST_Y", _widgets(3)),
        ),
    )

    assert _buildings(report) == (2, 3)
    assert [(p["choice"], p["setters"], p["gates"]) for p in report["paths"]] == [
        ("global flag TST_X", ["TST_x_deep"], 1),
        ("global flag TST_Y", ["TST_y_deep"], 1),
    ]


def test_flags_without_an_exclusive_setter_gate_nothing(tmp_path, capsys):
    report = _audit(
        capsys,
        _mod(
            tmp_path,
            _focus("TST_root", reward="set_global_flag = TST_FREE"),
            _gated("TST_late", "has_global_flag = TST_FREE", _widgets(1)),
            _gated("TST_event", "has_global_flag = TST_SET_ELSEWHERE", _widgets(2)),
        ),
    )

    assert report["paths"] == []
    assert _buildings(report) == (3, 3)


def test_a_focus_may_forbid_a_flag_it_or_its_child_sets(tmp_path, capsys):
    report = _audit(
        capsys,
        _mod(
            tmp_path,
            _focus("TST_root"),
            _focus(
                "TST_x",
                after=["TST_root"],
                against=["TST_y"],
                available="NOT = { has_global_flag = TST_LATER }",
                reward=_widgets(1),
            ),
            _focus(
                "TST_x_child",
                after=["TST_x"],
                reward="set_global_flag = TST_LATER " + _widgets(4),
            ),
            _focus(
                "TST_y",
                after=["TST_root"],
                against=["TST_x"],
                available="NOT = { has_global_flag = TST_SELF }",
                reward="set_global_flag = TST_SELF " + _widgets(2),
            ),
        ),
    )

    assert _buildings(report) == (2, 5)


_ADA = 'has_country_leader = { name = "Ada Test" }'
_BO = 'has_country_leader = { name = "Bo Test" }'


def _leader_tree():
    return (
        _focus("TST_root"),
        _focus(
            "TST_ada",
            after=["TST_root"],
            available=_ADA,
            reward="add_ideas = { TST_idea_gate_a TST_idea_gate_shared } "
            + _widgets(3),
        ),
        _focus(
            "TST_bo",
            after=["TST_root"],
            available=_BO,
            reward="add_ideas = { TST_idea_gate_big TST_idea_gate_shared } "
            + _widgets(1),
        ),
        _focus(
            "TST_not_bo",
            after=["TST_root"],
            available="NOT = { " + _BO + " }",
            reward=_widgets(10),
        ),
        _focus("TST_any", after=["TST_root"], reward=_widgets(100)),
    )


def test_leaders_are_exclusive_choices_in_totals_and_stacking(tmp_path, capsys):
    report = _audit(capsys, _mod(tmp_path, *_leader_tree()))

    # Ada: 3 + 10 + 100. Bo: 1 + 100. Summing both leaders would give 114.
    assert _buildings(report) == (101, 113)
    assert [(p["choice"], p["kind"], p["gates"]) for p in report["paths"]] == [
        ("leader Ada Test", "leader", 1),
        ("leader Bo Test", "leader", 2),
    ]
    # Bo stacks 0.30 and Ada 0.25. The idea both grant counts on either path, so
    # Bo's path keeps it even though Ada's focus is listed first.
    [row] = _branch(report, "TST_root")["stacking"]
    assert (row["sum"], row["path"]) == (0.3, ["leader Bo Test"])
    assert [source for source, _ in row["from"]] == [
        "TST_idea_gate_big",
        "TST_idea_gate_shared",
    ]


_SET_A = "set_country_flag = TST_A"
_SET_B = "set_country_flag = TST_B"

# case: (events file, buildings of the focus that needs each TST_ flag, extra focuses,
# lowest and highest buildings of the branch). A choice gives the worst and best
# option, 3..5 here. A flag that gates nothing gives the sum of every focus, 8..8.
_EVENT_PATHS = {
    "options of one event, set in a hidden_effect": (
        _event("tst.1", f"hidden_effect = {{ {_SET_A} }}", _SET_B),
        {"A": 5, "B": 3},
        (),
        (3, 5),
    ),
    "a flag that two options of the event set": (
        _event("tst.1", _SET_A, _SET_B, _SET_A),
        {"A": 5, "B": 3},
        (),
        (3, 5),
    ),
    "a flag that a second event sets": (
        _event("tst.1", _SET_A, _SET_B) + _event("tst.2", _SET_A),
        {"A": 5, "B": 3},
        (),
        (8, 8),
    ),
    "a flag that immediate sets": (
        _event("tst.1", _SET_A, _SET_B, immediate=_SET_A),
        {"A": 5, "B": 3},
        (),
        (8, 8),
    ),
    "a flag that a focus sets under an if": (
        _event("tst.1", _SET_A, _SET_B),
        {"A": 5, "B": 3},
        (
            _focus(
                "TST_sets_a",
                after=["TST_root"],
                reward="if = { limit = { always = yes } " + _SET_A + " }",
            ),
        ),
        (8, 8),
    ),
    "an option that sets no flag a focus needs": (
        _event("tst.1", _SET_A, _SET_B),
        {"A": 5},
        (),
        (5, 5),
    ),
    "two flags of one option are no alternatives": (
        _event("tst.1", _SET_A + " set_country_flag = TST_C", _SET_B),
        {"A": 5, "B": 3, "C": 2},
        (),
        (3, 7),
    ),
    "a path takes an option of each event": (
        _event("tst.1", _SET_A, _SET_B)
        + _event("tst.2", "set_country_flag = TST_C", "set_country_flag = TST_D"),
        {"A": 5, "B": 3, "C": 4, "D": 1},
        (),
        (4, 9),
    ),
}


@pytest.mark.parametrize(
    ("events", "gates", "extra", "expected"), _EVENT_PATHS.values(), ids=_EVENT_PATHS
)
def test_branch_totals_count_only_paths_an_event_allows(
    tmp_path, capsys, events, gates, extra, expected
):
    gated = [
        _gated(f"TST_needs_{flag}", f"has_country_flag = TST_{flag}", _widgets(n))
        for flag, n in gates.items()
    ]
    tree = (_focus("TST_root"), *gated, *extra)

    report = _audit(capsys, _mod(tmp_path, *tree, events=events))

    assert _buildings(report) == expected


def test_paths_section_lists_event_options_and_stacking_names_the_choice(
    tmp_path, capsys
):
    tree = (
        _focus("TST_root"),
        _gated("TST_only_a", "has_country_flag = TST_A", "add_ideas = TST_idea_gate_a"),
        _gated("TST_only_b", "has_country_flag = TST_B", "add_ideas = TST_idea_gate_b"),
    )
    # The second option has no name, so it is labeled by its place in the event.
    events = (
        f"country_event = {{ id = tst.1 option = {{ name = tst.1.a {_SET_A} }} "
        f"option = {{ {_SET_B} }} }}"
    )
    root = _mod(tmp_path, *tree, events=events)

    A.main(["--tag", "TST", "--root", str(root), "--stack-limit", "0.1", "--paths"])

    assert {
        "  country flag TST_A: set by tst.1.a; gates 1 focuses; branches TST_root",
        "  country flag TST_B: set by tst.1 option 2; gates 1 focuses; "
        "branches TST_root",
        "  TST_root: stability_factor +0.15  <- TST_idea_gate_a +0.15"
        "  [country flag TST_A]",
    } <= set(capsys.readouterr().out.splitlines())


# case: (an `available` body, the sets of which one must hold, the forbidden tokens)
_GATE_READS = {
    "a flag": ("has_global_flag = A", [["global flag A"]], []),
    "a flag block": (
        "has_country_flag = { flag = A days > 3 }",
        [["country flag A"]],
        [],
    ),
    "a leader without its quotes": (_ADA, [["leader Ada Test"]], []),
    "AND and a tooltip wrapper": (
        "AND = { has_global_flag = A } "
        "custom_trigger_tooltip = { tooltip = tt has_country_flag = B }",
        [["global flag A"], ["country flag B"]],
        [],
    ),
    "a hidden_trigger wrapper": (
        "hidden_trigger = { has_global_flag = A }",
        [["global flag A"]],
        [],
    ),
    "an OR of tests": (
        "OR = { has_global_flag = A has_country_flag = B }",
        [["country flag B", "global flag A"]],
        [],
    ),
    "an OR with another condition": (
        "OR = { has_global_flag = A has_war = yes }",
        [],
        [],
    ),
    "a NOT of one test": ("NOT = { has_global_flag = A }", [], ["global flag A"]),
    "a NOT of two tests": (
        "NOT = { has_global_flag = A has_global_flag = B }",
        [],
        [],
    ),
    "another country's scope": ("OTH = { has_global_flag = A }", [], []),
}


@pytest.mark.parametrize(
    ("text", "needs", "forbids"), _GATE_READS.values(), ids=_GATE_READS
)
def test_read_gates(text, needs, forbids):
    found_needs, found_forbids = A.read_gates(A.parse(text))

    assert ([sorted(block) for block in found_needs], sorted(found_forbids)) == (
        needs,
        forbids,
    )


def test_paths_section_lists_flags_and_stacking_names_the_choice(tmp_path, capsys):
    tree = _path_tree(
        "global",
        _gated("TST_only_a", "has_global_flag = TST_A", "add_ideas = TST_idea_gate_a"),
        _gated("TST_only_b", "has_global_flag = TST_B", "add_ideas = TST_idea_gate_b"),
    )
    root = _mod(tmp_path, *tree)

    A.main(["--tag", "TST", "--root", str(root), "--stack-limit", "0.1", "--paths"])

    lines = capsys.readouterr().out.splitlines()
    assert (
        "  global flag TST_A: set by TST_a; gates 1 focuses; branches TST_root" in lines
    )
    assert (
        "  TST_root: stability_factor +0.15  <- TST_idea_gate_a +0.15"
        "  [global flag TST_A]"
    ) in lines


def test_a_tree_without_gates_has_no_paths(tmp_path, capsys):
    root = _mod(tmp_path, *_stacking_tree())

    report = _audit(capsys, root)
    assert report["paths"] == []
    assert [r["path"] for b in report["branches"] for r in b["stacking"]] == [[], []]

    A.main(["--tag", "TST", "--root", str(root)])
    assert "== paths" not in capsys.readouterr().out

    A.main(["--tag", "TST", "--root", str(root), "--paths"])
    lines = capsys.readouterr().out.splitlines()
    heading = lines.index("== paths (choices that exclude each other) ==")
    assert lines[heading + 1] == "  none"


# --- CLI --------------------------------------------------------------------------


def test_script_prints_the_text_report_on_its_own(tmp_path):
    root = _mod(tmp_path, *_fork_tree())

    result = run_tool_script(
        "analysis/focus_reward_audit.py", "--tag", "TST", "--root", root
    )

    assert result.returncode == 0, result.stderr
    assert "TST focus reward audit" in result.stdout
    assert "TST_root" in result.stdout
    assert "== stacking over 0.2 ==" in result.stdout


def test_json_report_uppercases_the_tag_and_reads_a_named_file(tmp_path, capsys):
    root = _mod(tmp_path, *_fork_tree())
    other = write_tree(
        tmp_path / "other", {"tree.txt": _tree(_focus("TST_alone", reward=_widgets(1)))}
    )

    report = _audit(capsys, root, "--file", other / "tree.txt")

    assert report["tag"] == "TST"
    assert [f["id"] for f in report["focuses"]] == ["TST_alone"]
    assert report["standard_effects"] == 2
    assert report["dynamic_variables"] == 1


def test_text_report_lists_forks_and_focuses_on_request(tmp_path, capsys):
    formula = (
        "set_temp_variable = { treasury_change = { value = gdp_total multiply = -0.02 } } "
        "modify_treasury_effect = yes"
    )
    root = _mod(tmp_path, *_fork_tree(), _focus("TST_formula", reward=formula))

    A.main(["--tag", "tst", "--root", str(root), "--forks", "--focuses"])

    lines = capsys.readouterr().out.splitlines()
    assert any(
        line.startswith("  TST_root: TST_left [2 focuses, buildings 5")
        for line in lines
    )
    assert "  TST_other_root  7d  buildings widget_plant 4" in lines
    assert (
        "  unquantified rewards in 1 focuses (formulas, state loops); "
        "--focuses shows them"
    ) in lines
    assert (
        "  TST_formula  7d  unquantified: money { value = gdp_total multiply = -0.02 }"
        in lines
    )


# case: (error shown, focus tree text or bytes, extra arguments with {root} filled in)
_ERROR_CASES = {
    "no focus of the tag": (
        "error: no TST_ focuses",
        "focus_tree = { focus = { id = OTH_x } }",
        [],
    ),
    "missing file": ("error: file not found", "", ["--file", "nowhere.txt"]),
    "unreadable file": ("error: cannot read", "", ["--file", "{root}"]),
    "bad bytes name their file": (
        r"error: input is not valid UTF-8: .*x\.txt",
        b"\xff\xfe\n",
        [],
    ),
}


@pytest.mark.parametrize(
    ("error", "tree", "extra"), _ERROR_CASES.values(), ids=_ERROR_CASES
)
def test_cli_exits_with_a_message_when_it_cannot_audit(tmp_path, error, tree, extra):
    root = write_tree(tmp_path / "mod", _CONTEXT)
    focus_file = root / "common" / "national_focus" / "x.txt"
    if isinstance(tree, bytes):
        focus_file.parent.mkdir(parents=True)
        focus_file.write_bytes(tree)
    else:
        write_text(focus_file, tree)

    with pytest.raises(SystemExit, match=error):
        A.main(
            ["--tag", "TST", "--root", str(root), *(a.format(root=root) for a in extra)]
        )
