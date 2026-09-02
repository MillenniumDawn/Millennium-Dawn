"""Tests for tools/analysis/ai_path_report.py."""

from __future__ import annotations

import ai_path_report as report


def parse(body: str, tag: str = "DEN"):
    return report.parse_expr(body, tag)


def parent_child_focuses():
    return {
        "a": report.Focus(id="a", line=1, kind="focus"),
        "b": report.Focus(id="b", line=2, kind="focus", prereq_groups=[["a"]]),
    }


class TestStatements:
    def test_scalar_block_and_quoted_values(self):
        body = 'name = "DEN_AI" option = { name = HISTORICAL } flag = X'
        assert list(report.iter_statements(body)) == [
            ("name", "DEN_AI", None),
            ("option", None, " name = HISTORICAL "),
            ("flag", "X", None),
        ]

    def test_nested_blocks_are_not_yielded_twice(self):
        body = "a = { b = { c = 1 } } d = 2"
        keys = [key for key, _, _ in report.iter_statements(body)]
        assert keys == ["a", "d"]

    def test_comparison_operators_are_yielded(self):
        body = "has_stability > 0.66 threat < 0.4"
        assert list(report.iter_statements(body)) == [
            ("has_stability", "0.66", None),
            ("threat", "0.4", None),
        ]


class TestEvaluator:
    def test_flag_predicate(self):
        expr = parse("has_global_flag = DEN_SOCIALIST_FOCUS_PATH")
        assert report.evaluate(expr, "DEN_SOCIALIST_FOCUS_PATH", False, {}) is True
        assert report.evaluate(expr, "DEN_MONARCHIST_FOCUS_PATH", False, {}) is False
        assert report.evaluate(expr, None, False, {}) is False

    def test_historical_predicate(self):
        expr = parse("is_historical_focus_on = yes")
        assert report.evaluate(expr, None, True, {}) is True
        assert report.evaluate(expr, None, False, {}) is False

    def test_unknown_trigger_never_counts_as_a_kill(self):
        expr = parse("has_government = democratic")
        assert report.evaluate(expr, None, True, {}) is None

    def test_comparison_only_body_never_counts_as_a_kill(self):
        expr = parse("has_stability > 0.66")
        assert report.evaluate(expr, None, True, {}) is None

    def test_not_wrapped_flag_is_an_exemption(self):
        expr = parse("NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }")
        assert report.evaluate(expr, "DEN_SOCIALIST_FOCUS_PATH", False, {}) is False
        assert report.evaluate(expr, None, False, {}) is True

    def test_or_short_circuits_past_unknown(self):
        expr = parse(
            "OR = { has_government = democratic is_historical_focus_on = yes }"
        )
        assert report.evaluate(expr, None, True, {}) is True
        assert report.evaluate(expr, None, False, {}) is None

    def test_and_with_a_false_child_is_false_despite_unknown(self):
        expr = parse("has_government = democratic is_historical_focus_on = yes")
        assert report.evaluate(expr, None, False, {}) is False

    def test_nested_scripted_triggers_expand(self):
        triggers = {
            "DEN_ai_western_path": parse(
                "OR = { has_global_flag = DEN_HISTORICAL_FOCUS_PATH"
                " has_global_flag = DEN_EU_FOCUS_PATH }"
            ),
            "DEN_ai_not_socialist_path": parse(
                "NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }"
                " OR = { is_historical_focus_on = yes DEN_ai_western_path = yes }"
            ),
        }
        expr = parse("DEN_ai_not_socialist_path = yes")
        assert report.evaluate(expr, "DEN_EU_FOCUS_PATH", False, triggers) is True
        assert (
            report.evaluate(expr, "DEN_SOCIALIST_FOCUS_PATH", True, triggers) is False
        )
        assert report.evaluate(expr, None, False, triggers) is False

    def test_cycles_terminate_as_unknown(self):
        triggers = {
            "DEN_ai_a_path": parse("DEN_ai_b_path = yes"),
            "DEN_ai_b_path": parse("DEN_ai_a_path = yes"),
        }
        assert (
            report.evaluate(parse("DEN_ai_a_path = yes"), None, True, triggers) is None
        )

    def test_missing_trigger_definition_is_unknown(self):
        assert report.evaluate(parse("DEN_ai_ghost_path = yes"), None, True, {}) is None

    def test_expand_trigger_reaches_flags_transitively(self):
        triggers = {
            "DEN_ai_alt_path": parse("DEN_ai_west_path = yes"),
            "DEN_ai_west_path": parse("has_global_flag = DEN_EU_FOCUS_PATH"),
        }
        assert "DEN_EU_FOCUS_PATH" in report._expand_trigger(
            "DEN_ai_alt_path", triggers
        )


FOCUS_FILE = """
focus_tree = {
	id = den
	country = { factor = 0 modifier = { add = 10 original_tag = DEN } }

	focus = {
		id = DEN_root
		x = 0
		y = 0
		ai_will_do = {
			base = 1
			modifier = { factor = 25 DEN_ai_historical_path = yes }
			modifier = { factor = 0 DEN_ai_not_historical_path = yes }
		}
	}

	focus = {
		id = DEN_child
		prerequisite = { focus = DEN_root }
		mutually_exclusive = { focus = DEN_other }
		available = { has_completed_focus = DEN_root }
		ai_will_do = {
			base = 1
			modifier = {
				factor = 0
				can_staff_an_arms_industry = no
			}
			modifier = { factor = 25 has_global_flag = DEN_SOCIALIST_FOCUS_PATH }
			modifier = { factor = 0 DEN_ai_not_socialist_path = yes }
		}
	}

	focus = {
		id = DEN_other
		prerequisite = { focus = DEN_root }
		available = { always = no }
		completion_reward = {
			delete_unit = { disband = yes }
		}
		ai_will_do = { base = 1 }
	}

	focus = {
		id = DEN_additive
		prerequisite = { focus = DEN_root }
		ai_will_do = {
			base = 1
			modifier = { add = 50 has_global_flag = DEN_SOCIALIST_FOCUS_PATH }
		}
	}
}
"""


class TestFocusParsing:
    def setup_method(self):
        self.focuses = report.parse_focus_file(FOCUS_FILE, "DEN")
        self.by_id = {focus.id: focus for focus in self.focuses}

    def test_every_focus_is_found_and_the_tree_header_is_not(self):
        assert sorted(self.by_id) == [
            "DEN_additive",
            "DEN_child",
            "DEN_other",
            "DEN_root",
        ]

    def test_prerequisites_and_mutex(self):
        assert self.by_id["DEN_child"].prereq_groups == [["DEN_root"]]
        assert self.by_id["DEN_child"].mutex == ["DEN_other"]

    def test_guard_modifier_is_not_path_related(self):
        guards = [m for m in self.by_id["DEN_child"].modifiers if m.guard]
        assert len(guards) == 1
        assert not guards[0].path_related

    def test_one_line_and_multi_line_modifiers_parse_alike(self):
        modifiers = self.by_id["DEN_child"].modifiers
        assert [m.op for m in modifiers] == ["factor", "factor", "factor"]
        assert modifiers[1].tokens == ("DEN_SOCIALIST_FOCUS_PATH",)

    def test_always_no_and_danger_rewards(self):
        other = self.by_id["DEN_other"]
        assert other.always_off
        assert other.dangers == ["delete_unit"]

    def test_additive_path_modifier_is_reported(self):
        findings = report._owner_findings(self.focuses, "DEN", [], {})
        assert findings["additive"] == ["DEN_additive"]

    def test_unused_flag_detection_expands_triggers(self):
        triggers = {
            "DEN_ai_historical_path": parse(
                "OR = { is_historical_focus_on = yes"
                " has_global_flag = DEN_HISTORICAL_FOCUS_PATH }"
            ),
            "DEN_ai_not_historical_path": parse(
                "has_global_flag = DEN_SOCIALIST_FOCUS_PATH"
            ),
        }
        findings = report._owner_findings(
            self.focuses,
            "DEN",
            [
                "DEN_HISTORICAL_FOCUS_PATH",
                "DEN_SOCIALIST_FOCUS_PATH",
                "DEN_DEAD_FOCUS_PATH",
            ],
            triggers,
        )
        assert findings["unused_flags"] == ["DEN_DEAD_FOCUS_PATH"]


class TestReachability:
    def test_single_member_group_with_a_dead_parent_orphans_the_child(self):
        focuses = parent_child_focuses()
        alive = {"a": False, "b": True}
        assert report.unreachable_focuses(alive, focuses) == {"b"}

    def test_or_group_with_one_survivor_is_not_an_orphan(self):
        focuses = {
            "a": report.Focus(id="a", line=1, kind="focus"),
            "b": report.Focus(id="b", line=2, kind="focus"),
            "c": report.Focus(id="c", line=3, kind="focus", prereq_groups=[["a", "b"]]),
        }
        alive = {"a": False, "b": True, "c": True}
        assert report.unreachable_focuses(alive, focuses) == set()

    def test_orphaning_propagates_transitively(self):
        focuses = {
            "a": report.Focus(id="a", line=1, kind="focus"),
            "b": report.Focus(id="b", line=2, kind="focus", prereq_groups=[["a"]]),
            "c": report.Focus(id="c", line=3, kind="focus", prereq_groups=[["b"]]),
        }
        alive = {"a": False, "b": True, "c": True}
        assert report.unreachable_focuses(alive, focuses) == {"b", "c"}

    def test_a_dead_focus_is_not_also_counted_as_an_orphan(self):
        focuses = parent_child_focuses()
        alive = {"a": False, "b": False}
        assert report.unreachable_focuses(alive, focuses) == set()


class TestWeights:
    def test_killswitch_wins_over_a_boost(self):
        focus = report.parse_focus_file(FOCUS_FILE, "DEN")[1]
        triggers = {
            "DEN_ai_not_socialist_path": parse(
                "NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }"
                " is_historical_focus_on = yes"
            )
        }
        assert focus.id == "DEN_child"
        weight, _ = report.focus_weight(
            focus, report.State("HISTORICAL", None, True), triggers
        )
        assert weight == 0

    def test_owned_path_keeps_its_boost(self):
        focus = report.parse_focus_file(FOCUS_FILE, "DEN")[1]
        triggers = {
            "DEN_ai_not_socialist_path": parse(
                "NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }"
                " is_historical_focus_on = yes"
            )
        }
        weight, _ = report.focus_weight(
            focus,
            report.State("SOCIALIST", "DEN_SOCIALIST_FOCUS_PATH", True),
            triggers,
        )
        assert weight == 25

    def test_no_path_without_historical_ai_leaves_the_base(self):
        focus = report.parse_focus_file(FOCUS_FILE, "DEN")[1]
        triggers = {
            "DEN_ai_not_socialist_path": parse(
                "NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }"
                " is_historical_focus_on = yes"
            )
        }
        weight, _ = report.focus_weight(
            focus, report.State("NO_PATH", None, False), triggers
        )
        assert weight == 1


ROSTER_FILE = """
set_leader_DEN = {
	if = { limit = { has_country_flag = set_conservatism }
		if = { limit = { check_variable = { conservatism_leader = 0 } }
			add_to_variable = { conservatism_leader = 1 }
			create_country_leader = { name = "Anders Fogh" ideology = conservatism }
			if = { limit = { date < 2009.4.5 } set_temp_variable = { b = 1 } }
		}
		if = { limit = { check_variable = { conservatism_leader = 1 } NOT = { check_variable = { b = 1 } } }
			add_to_variable = { conservatism_leader = 1 }
			create_country_leader = { name = "Lars Rasmussen" ideology = conservatism }
			set_temp_variable = { b = 1 }
		}
	}
	else_if = { limit = { has_country_flag = set_socialism }
		if = { limit = { check_variable = { socialism_leader = 0 } }
			add_to_variable = { socialism_leader = 1 }
			create_country_leader = { name = "Mette Frederiksen" ideology = socialism }
			if = { limit = { date < 2016.1.2 } set_temp_variable = { b = 1 } }
		}
	}
}
"""

WALKER_IMMEDIATE = """
	log = "[GetDateText]: [Root.GetName]: event denmark_md.400"
	if = {
		limit = { date > 2022.10.24 }
		set_variable = { conservatism_leader = 6 }
		set_temp_variable = { rul_party_temp = 1 }
	}
	else_if = {
		limit = { date > 2019.7.23 }
		set_variable = { socialism_leader = 1 }
		set_temp_variable = { rul_party_temp = 3 }
	}
	else = {
		set_variable = { socialism_leader = 0 }
		set_temp_variable = { rul_party_temp = 3 }
	}

	if = {
		limit = { NOT = { is_in_array = { ruling_party = rul_party_temp } } }
		change_ruling_party_effect = yes
		set_elections_60_months = yes
	}
	else = {
		set_ruling_leader = yes
		set_leader = yes
	}
"""


class TestDayOffsets:
    def test_january_tick_is_day_zero(self):
        assert report.day_offset_to_date(2001, 0) == (2001, 1, 1)

    def test_offset_matches_the_counts_already_in_yearly_effects(self):
        assert report.day_offset_to_date(2001, 158) == (2001, 6, 8)
        assert report.day_offset_to_date(2022, 298) == (2022, 10, 26)

    def test_leap_years_are_ignored_like_the_mod_does(self):
        assert report.day_offset_to_date(2024, 364) == (2024, 12, 31)


class TestRoster:
    def setup_method(self):
        self.roster = report.parse_leader_roster(ROSTER_FILE, "DEN")

    def test_every_subideology_branch_is_found(self):
        assert sorted(self.roster) == ["conservatism", "socialism"]

    def test_entries_keep_their_declared_pointer_index(self):
        assert [(x.index, x.name) for x in self.roster["conservatism"]] == [
            (0, "Anders Fogh"),
            (1, "Lars Rasmussen"),
        ]

    def test_end_of_tenure_dates_and_terminal_entry(self):
        entries = self.roster["conservatism"]
        assert entries[0].until == (2009, 4, 5)
        assert entries[1].until is None

    def test_bookmark_marker_is_not_a_real_date(self):
        assert self.roster["socialism"][0].until in report.BOOKMARK_DATES


class TestYearSchedule:
    def test_tag_scoped_events_are_collected_with_their_year(self):
        text = (
            "trigger_year_2001_events = {\n"
            "\tDEN = { country_event = { id = denmark_md.400 days = 158 } }\n"
            "\tSWE = { country_event = { id = sweden.1 days = 10 } }\n"
            "}\n"
            "trigger_year_2022_events = {\n"
            "\tDEN = { country_event = { id = denmark_md.400 days = 298 } }\n"
            "}\n"
        )
        assert report.parse_year_schedule(text, "DEN") == [
            (2001, "denmark_md.400", 158),
            (2022, "denmark_md.400", 298),
        ]


class TestWalker:
    def setup_method(self):
        self.walker = report.parse_walker(WALKER_IMMEDIATE)

    def test_the_date_chain_stops_before_the_change_or_advance_tail(self):
        assert [branch.kind for branch in self.walker.chain] == [
            "if",
            "else_if",
            "else",
        ]

    def test_each_branch_carries_its_bound_party_and_roster_index(self):
        assert self.walker.chain[0].after == (2022, 10, 24)
        assert self.walker.chain[0].party == 1
        assert self.walker.chain[0].pointer == ("conservatism", 6)
        assert self.walker.chain[2].after is None
        assert self.walker.chain[2].pointer == ("socialism", 0)

    def test_the_sanctioned_tail_is_not_read_as_an_unbounded_party_change(self):
        assert not self.walker.chain[-1].changes_party

    def test_a_clean_walker_pins_nothing(self):
        assert not self.walker.pins_leader

    def test_change_leader_temp_is_detected(self):
        pinned = report.parse_walker(
            "if = { limit = { date > 2015.5.6 } "
            "set_temp_variable = { change_leader_temp = 1 } "
            "change_ruling_party_effect = yes }"
        )
        assert pinned.pins_leader

    def test_a_blind_advance_branch_asserts_no_index(self):
        blind = report.parse_walker(
            "if = { limit = { date > 2010.5.11 } "
            "set_temp_variable = { rul_party_temp = 1 } }"
            " else = { set_ruling_leader = yes set_leader = yes }"
        )
        assert [branch.pointer for branch in blind.chain] == [None, None]
        assert blind.chain[1].advances

    def test_dates_resolve_down_the_descending_chain(self):
        chain = self.walker.chain
        assert report.resolve_branch(chain, (2024, 7, 5)) is chain[0]
        assert report.resolve_branch(chain, (2021, 1, 1)) is chain[1]
        assert report.resolve_branch(chain, (2005, 5, 5)) is chain[2]


class TestPartyIndices:
    def test_indices_are_read_from_set_ruling_leader(self):
        text = (
            "set_ruling_leader = {\n"
            "\tif = { limit = { is_in_array = { ruling_party = 0 } }\n"
            "\t\tset_country_flag = set_Western_Autocracy\n"
            "\t}\n"
            "\telse_if = { limit = { is_in_array = { ruling_party = 3 } }\n"
            "\t\tset_country_flag = set_socialism\n"
            "\t}\n"
            "}\n"
        )
        assert report.parse_party_indices(text) == {
            0: "Western_Autocracy",
            3: "socialism",
        }


class TestLocalisation:
    def test_two_sentence_counter_ignores_highlights_and_scopes(self):
        text = (
            "The §8Social Democrats§! win the chamber. "
            "Denmark leaves the union it helped build."
        )
        assert report.count_sentences(text) == 2

    def test_a_scope_substitution_does_not_add_a_sentence(self):
        assert report.count_sentences("[Root.GetName] holds the line. It works.") == 2

    def test_one_sentence_is_detected(self):
        assert report.count_sentences("Only this.") == 1


HISTORY_FILE = """
capital = 1
add_ideas = {
	limited_conscription
	DEN_mafia
	DEN_brain_drain
}
add_dynamic_modifier = { modifier = DEN_ageing_population }
set_variable = { DEN_ageing_population_var = -0.75 }
set_variable = { DEN_reserve_var = 0.5 }
81 = {
	add_dynamic_modifier = { modifier = roma_capitale_modifier }
	set_variable = { roma_capitale_var = -0.6 }
}
2004.1.1 = {
	add_ideas = { DEN_euro_entry }
}
"""


class TestCureScanning:
    def test_scalar_and_block_idea_removals(self):
        block = "remove_ideas = DEN_mafia remove_ideas = { DEN_a DEN_b }"
        assert report._scan_cures(block) == ["DEN_mafia", "DEN_a", "DEN_b"]

    def test_swap_ideas_reports_only_the_removed_side(self):
        block = "swap_ideas = { add_idea = DEN_new remove_idea = DEN_old }"
        assert report._scan_cures(block) == ["DEN_old"]

    def test_dynamic_modifier_and_variable_relief(self):
        block = (
            "remove_dynamic_modifier = { modifier = DEN_ageing_population }"
            " add_to_variable = { DEN_stability_factor_var = 0.05 }"
        )
        assert report._scan_cures(block) == [
            "DEN_ageing_population",
            "DEN_stability_factor_var",
        ]

    def test_subtracting_from_a_variable_is_not_relief(self):
        assert report._scan_cures("subtract_from_variable = { DEN_x = 0.05 }") == []

    def test_a_focus_records_the_cures_in_its_completion_reward(self):
        focuses = report.parse_focus_file(
            "focus = { id = DEN_fix completion_reward = {"
            " remove_ideas = DEN_mafia } ai_will_do = { base = 1 } }",
            "DEN",
        )
        assert focuses[0].cures == ["DEN_mafia"]


class TestBurdens:
    def test_state_blocks_are_dropped_and_dated_blocks_kept(self):
        scoped = report.country_scope(HISTORY_FILE)
        assert "roma_capitale_modifier" not in scoped
        assert "DEN_euro_entry" in scoped
        assert len(scoped) == len(HISTORY_FILE)

    def test_variable_seed_reads_both_forms(self):
        assert report._variable_seed(" DEN_x = -0.75 ") == ("DEN_x", -0.75)
        assert report._variable_seed(" var = DEN_y value = -1 ") == ("DEN_y", -1.0)

    def test_only_country_ideas_count_as_burdens(self):
        assert report._is_country_idea("DEN_mafia", "DEN") is True
        assert report._is_country_idea("mafia_DEN", "DEN") is True
        assert report._is_country_idea("limited_conscription", "DEN") is False


class TestDecisionUsability:
    def test_a_zero_base_decision_is_unreachable_for_the_ai(self):
        decision = report._build_decision(
            "DEN_repeal",
            "DEN_cat",
            "available = { has_idea = DEN_mafia }"
            " complete_effect = { remove_ideas = DEN_mafia }"
            " ai_will_do = { base = 0 }",
        )
        assert decision.base == 0
        assert decision.ai_blocked is False
        assert decision.cures == ("DEN_mafia",)

    def test_an_is_ai_no_gate_blocks_the_decision(self):
        decision = report._build_decision(
            "DEN_player_only",
            "DEN_cat",
            "visible = { is_ai = no } ai_will_do = { base = 100 }",
        )
        assert decision.ai_blocked is True

    def test_a_decision_without_ai_will_do_keeps_the_default_base(self):
        assert report._build_decision("DEN_x", "DEN_cat", "cost = 25").base == 1.0


class TestCrisisWeighting:
    def test_a_purely_path_weighted_cure_focus_is_flat(self):
        focus = report.parse_focus_file(FOCUS_FILE, "DEN")[1]
        assert report._has_priority_boost(focus) is False

    def test_a_crisis_modifier_counts_as_a_boost(self):
        focus = report.parse_focus_file(
            "focus = { id = DEN_fix ai_will_do = { base = 1"
            " modifier = { factor = 5 has_idea = DEN_mafia } } }",
            "DEN",
        )[0]
        assert report._has_priority_boost(focus) is True

    def test_a_raised_base_counts_as_a_boost(self):
        focus = report.parse_focus_file(
            "focus = { id = DEN_fix ai_will_do = { base = 40 } }", "DEN"
        )[0]
        assert report._has_priority_boost(focus) is True


class TestCureReachability:
    def test_a_killswitched_cure_leaves_no_live_relief(self):
        focuses = report.parse_focus_file(FOCUS_FILE, "DEN")
        by_id = {focus.id: focus for focus in focuses}
        triggers = {
            "DEN_ai_historical_path": parse("is_historical_focus_on = yes"),
            "DEN_ai_not_historical_path": parse(
                "NOT = { is_historical_focus_on = yes }"
            ),
            "DEN_ai_not_socialist_path": parse(
                "NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }"
                " is_historical_focus_on = yes"
            ),
        }
        live = report.live_focuses(
            focuses, by_id, report.State("HISTORICAL", None, True), triggers
        )
        assert "DEN_root" in live
        assert "DEN_child" not in live

    def test_an_orphaned_cure_does_not_count_as_live(self):
        focuses = report.parse_focus_file(FOCUS_FILE, "DEN")
        by_id = {focus.id: focus for focus in focuses}
        triggers = {
            "DEN_ai_historical_path": parse("is_historical_focus_on = yes"),
            "DEN_ai_not_historical_path": parse(
                "NOT = { is_historical_focus_on = yes }"
            ),
            "DEN_ai_not_socialist_path": parse(
                "NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }"
                " is_historical_focus_on = yes"
            ),
        }
        live = report.live_focuses(
            focuses,
            by_id,
            report.State("SOCIALIST", "DEN_SOCIALIST_FOCUS_PATH", False),
            triggers,
        )
        assert "DEN_root" not in live
        assert "DEN_child" not in live
