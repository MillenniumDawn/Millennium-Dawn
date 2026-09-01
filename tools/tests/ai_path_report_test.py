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
