"""Focus reward audit: the parser, reward totals, branches, forks, stacking and the CLI."""

import json

import focus_reward_audit as A
import pytest
from shared.suite import run_tool_script, write_tree

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
	}
}
"""

_CONTEXT = {
    "common/scripted_effects/00_scripted_effects.txt": _STANDARD_EFFECTS,
    "common/scripted_effects/tst_effects.txt": _TAG_EFFECTS,
    "common/dynamic_modifiers/tst.txt": _DYNAMIC_MODIFIERS,
    "common/ideas/tst.txt": _IDEAS,
}


def _focus(focus_id, *, after=(), against=(), reward=""):
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
    lines.append("\t\tcompletion_reward = {\n" + reward + "\n\t\t}")
    return "\tfocus = {\n" + "\n".join(lines) + "\n\t}\n"


def _tree(*focuses):
    return "focus_tree = {\n\tid = TST_tree\n" + "".join(focuses) + "}\n"


def _widgets(level):
    return f"add_building_construction = {{ type = widget_plant level = {level} }}"


def _mod(tmp_path, *focuses):
    return write_tree(
        tmp_path / "mod",
        {**_CONTEXT, "common/national_focus/tst.txt": _tree(*focuses)},
    )


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


# case: (error shown, focus tree text, extra arguments)
_ERROR_CASES = {
    "no focus of the tag": (
        "error: no TST_ focuses",
        "focus_tree = { focus = { id = OTH_x } }",
        [],
    ),
    "missing file": ("error: file not found", "", ["--file", "nowhere.txt"]),
}


@pytest.mark.parametrize(
    ("error", "tree", "extra"), _ERROR_CASES.values(), ids=_ERROR_CASES
)
def test_cli_exits_with_a_message_when_there_is_nothing_to_audit(
    tmp_path, error, tree, extra
):
    root = write_tree(
        tmp_path / "mod", {**_CONTEXT, "common/national_focus/x.txt": tree}
    )

    with pytest.raises(SystemExit, match=error):
        A.main(["--tag", "TST", "--root", str(root), *extra])
