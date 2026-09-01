"""Unit tests for validate_simplifications.

Pin the two detectors and, critically, the safety suppressions: merging
consecutive same-scope blocks is only valid in AND/sequential contexts, never
under OR / random_list / count_triggers, and never for non-deterministic
(random_*) or iterator scopes.
"""

import runpy
import sys

import pytest
import validate_simplifications as vs
from validate_simplifications import (
    _count_children,
    _find_bare_not,
    _find_count_collapsible,
    _find_empty_trigger_blocks,
    _find_government_match,
    _find_mergeable,
    _find_random_controlled_shortcut,
    _find_scope_expansion,
    _find_two_bucket_random,
    _iter_direct_assignments,
    _scan_composite,
    strip_comments,
)


def _merge_lines(text):
    return sorted(line for line, _ in _find_mergeable(strip_comments(text)))


def _expansion(text):
    return [(tag, flat) for _, tag, flat in _find_scope_expansion(strip_comments(text))]


def _random(text):
    return [chance for _, chance in _find_two_bucket_random(strip_comments(text))]


def _count(text):
    return [(line, n) for line, n in _find_count_collapsible(strip_comments(text))]


def _empty(text):
    return [kw for _, kw in _find_empty_trigger_blocks(strip_comments(text))]


def _gov(text):
    return [rep for _, rep in _find_government_match(strip_comments(text))]


def _not(text):
    return [(line, n) for line, n in _find_bare_not(strip_comments(text))]


def _controlled(text):
    return list(_find_random_controlled_shortcut(strip_comments(text)))


def _all_five(target, scoped_tmpl):
    """Build an exhaustive 5-clause OR. *scoped_tmpl* formats one clause's
    scoped side given the ideology, e.g. '{t} = {{ has_government = {i} }}'."""
    clauses = "\n".join(
        "  AND = {{ has_government = {i}  {s} }}".format(
            i=i, s=scoped_tmpl.format(t=target, i=i)
        )
        for i in ("democratic", "communism", "fascism", "neutrality", "nationalist")
    )
    return "OR = {{\n{c}\n}}\n".format(c=clauses)


# --- scope-merge: positive cases -------------------------------------------


def test_consecutive_tag_blocks_merge():
    assert _merge_lines("USA = { a = yes }\nUSA = { b = yes }\n") == [2]


def test_consecutive_state_id_blocks_merge():
    assert _merge_lines("10 = { add = 1 }\n10 = { add = 2 }\n") == [2]


def test_magic_scope_chain_merges():
    assert _merge_lines("PREV.PREV = { a }\nPREV.PREV = { b }\n") == [2]


def test_var_scope_merges():
    assert _merge_lines("var:foo = { a }\nvar:foo = { b }\n") == [2]


def test_three_in_a_row_flags_each_redundant_block():
    assert _merge_lines("USA = { a }\nUSA = { b }\nUSA = { c }\n") == [2, 3]


def test_nested_consecutive_blocks_merge():
    assert _merge_lines("USA = {\n  PREV = { a }\n  PREV = { b }\n}\n") == [3]


def test_comment_between_blocks_still_merges():
    assert _merge_lines("USA = { a }\n# note\nUSA = { b }\n") == [3]


# --- scope-merge: must NOT flag --------------------------------------------


def test_intervening_statement_blocks_merge():
    assert _merge_lines("USA = { a }\nadd_stability = 0.1\nUSA = { b }\n") == []


def test_intervening_block_blocks_merge():
    assert _merge_lines("USA = { a }\nset_variable = { x = 1 }\nUSA = { b }\n") == []


def test_different_tags_do_not_merge():
    assert _merge_lines("USA = { a }\nGER = { b }\n") == []


def test_random_scope_never_merges():
    assert _merge_lines("random_country = { a }\nrandom_country = { b }\n") == []


def test_iterator_scope_never_merges():
    assert _merge_lines("every_country = { a }\nevery_country = { b }\n") == []


def test_if_blocks_never_merge():
    assert _merge_lines("if = { limit = { x } }\nif = { limit = { y } }\n") == []


def test_and_not_blocks_never_merge():
    assert _merge_lines("AND = { a }\nAND = { b }\n") == []
    assert _merge_lines("NOT = { a }\nNOT = { b }\n") == []


def test_focus_blocks_never_merge():
    assert _merge_lines("focus = { id = x }\nfocus = { id = y }\n") == []


def test_or_parent_suppresses_merge():
    # OR(A, B) must NOT become A AND B.
    text = "OR = {\n UKR = { is_subject_of = POL }\n UKR = { is_in_faction_with = POL }\n}\n"
    assert _merge_lines(text) == []


def test_random_list_buckets_suppressed():
    # Two 50%-weight buckets are not state-50 scopes.
    text = "random_list = {\n 50 = { add_stability = 0.1 }\n 50 = { add_war_support = 0.1 }\n}\n"
    assert _merge_lines(text) == []


def test_count_triggers_parent_suppresses_merge():
    text = "count_triggers = {\n USA = { a }\n USA = { b }\n amount = 1\n}\n"
    assert _merge_lines(text) == []


def test_merge_still_flags_under_and_parent():
    assert _merge_lines("AND = {\n USA = { a }\n USA = { b }\n}\n") == [3]


# --- scope-expansion -------------------------------------------------------


def test_exists_yes_collapses_to_country_exists():
    assert _expansion("USA = { exists = yes }\n") == [("USA", "country_exists = USA")]


def test_is_puppet_yes_collapses():
    assert _expansion("GER = { is_puppet = yes }\n") == [("GER", "is_puppet_of = GER")]


def test_multi_condition_block_not_flagged():
    assert _expansion("USA = { exists = yes has_war = yes }\n") == []


def test_exists_no_left_alone():
    # NOT-context-dependent; deliberately not suggested.
    assert _expansion("USA = { exists = no }\n") == []


def test_non_tag_scope_not_flagged_for_expansion():
    assert _expansion("owner = { exists = yes }\n") == []


# --- two-bucket random_list ------------------------------------------------


def test_5050_empty_bucket_collapses():
    text = "random_list = { 50 = { add_to_variable = { x = 1 } } 50 = {} }\n"
    assert _random(text) == [50]


def test_weighted_empty_bucket_computes_chance():
    # 30 fires the effect, 70 does nothing -> 30% chance.
    text = "random_list = { 30 = { add_stability = 0.1 } 70 = { } }\n"
    assert _random(text) == [30]


def test_both_buckets_nonempty_not_flagged():
    text = "random_list = { 50 = { add_stability = 0.1 } 50 = { add_war_support = 0.1 } }\n"
    assert _random(text) == []


def test_three_buckets_not_flagged():
    text = "random_list = { 33 = { a = yes } 33 = { b = yes } 34 = {} }\n"
    assert _random(text) == []


def test_both_empty_not_flagged():
    assert _random("random_list = { 50 = {} 50 = {} }\n") == []


def test_bucket_with_modifier_not_flagged():
    # random = { chance = N } has no modifier support; the conversion is invalid.
    text = (
        "random_list = {\n"
        "\t40 = {\n"
        "\t\tmodifier = {\n"
        "\t\t\tfactor = 0.80\n"
        "\t\t\thas_idea = recession\n"
        "\t\t}\n"
        "\t\tdecrease_economic_growth = yes\n"
        "\t}\n"
        "\t60 = { }\n"
        "}\n"
    )
    assert _random(text) == []


# --- identical adjacent create_unit -> count -------------------------------


def test_two_identical_create_units_collapse():
    text = (
        'create_unit = { division = "x" owner = ALG }\n'
        'create_unit = { division = "x" owner = ALG }\n'
    )
    assert _count(text) == [(1, 2)]


def test_three_identical_create_units_collapse_to_count_3():
    body = 'create_unit = { division = "x" owner = RAJ }\n'
    assert _count(body * 3) == [(1, 3)]


def test_whitespace_only_difference_still_collapses():
    text = (
        'create_unit = {\n  division = "x"\n  owner = ALG\n}\n'
        'create_unit = { division = "x" owner = ALG }\n'
    )
    assert _count(text) == [(1, 2)]


def test_different_division_does_not_collapse():
    text = (
        'create_unit = { division = "x" owner = ALG }\n'
        'create_unit = { division = "y" owner = ALG }\n'
    )
    assert _count(text) == []


def test_state_wrapped_create_units_not_flagged_here():
    # Each create_unit lives in its own state scope -> braces separate them, so
    # the count detector skips it (the state-id merge detector covers this).
    text = (
        '410 = { create_unit = { division = "x" owner = AFG } }\n'
        '410 = { create_unit = { division = "x" owner = AFG } }\n'
    )
    assert _count(text) == []


def test_intervening_effect_breaks_run():
    text = (
        'create_unit = { division = "x" owner = ALG }\n'
        "set_temp_variable = { t = 1 }\n"
        'create_unit = { division = "x" owner = ALG }\n'
    )
    assert _count(text) == []


def test_blocks_with_own_count_not_flagged():
    text = (
        'create_unit = { division = "x" owner = ALG count = 1 }\n'
        'create_unit = { division = "x" owner = ALG count = 1 }\n'
    )
    assert _count(text) == []


# --- empty visible / available / allowed -----------------------------------


def test_empty_visible_flagged():
    assert _empty("visible = { }\n") == ["visible"]


def test_empty_available_multiline_flagged():
    assert _empty("available = {\n\n}\n") == ["available"]


def test_empty_block_with_only_comment_flagged():
    assert _empty("visible = {\n\t# todo\n}\n") == ["visible"]


def test_nonempty_visible_not_flagged():
    assert _empty("visible = { has_country_flag = x }\n") == []


def test_other_empty_blocks_not_flagged():
    # Only visible/available/allowed are safe to delete; limit/trigger are not.
    assert _empty("limit = { }\ntrigger = { }\n") == []


# --- government-match enumeration: positive cases --------------------------


def test_exhaustive_same_government_collapses():
    assert _gov(_all_five("FROM", "{t} = {{ has_government = {i} }}")) == [
        "has_government = FROM"
    ]


def test_scoped_first_order_collapses():
    # ARM = { has_government = X } before the bare check (france.txt shape).
    text = (
        "OR = {\n"
        + "\n".join(
            "  AND = {{ ARM = {{ has_government = {i} }}  has_government = {i} }}".format(
                i=i
            )
            for i in ("democratic", "communism", "fascism", "neutrality", "nationalist")
        )
        + "\n}\n"
    )
    assert _gov(text) == ["has_government = ARM"]


def test_inner_not_different_government_collapses():
    assert _gov(_all_five("SYR", "{t} = {{ NOT = {{ has_government = {i} }} }}")) == [
        "NOT = { has_government = SYR }"
    ]


def test_outer_not_different_government_collapses():
    assert _gov(_all_five("FROM", "NOT = {{ {t} = {{ has_government = {i} }} }}")) == [
        "NOT = { has_government = FROM }"
    ]


# --- government-match enumeration: must NOT flag ---------------------------


def test_non_exhaustive_three_ideologies_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  FROM = { has_government = democratic } }\n"
        "  AND = { has_government = communism  FROM = { has_government = communism } }\n"
        "  AND = { has_government = fascism  FROM = { has_government = fascism } }\n"
        "}\n"
    )
    assert _gov(text) == []


def test_mixed_or_with_extra_condition_not_flagged():
    # raids.txt shape: a same-gov AND beside unrelated OR operands.
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  FROM = { has_government = democratic } }\n"
        "  has_war = yes\n"
        "}\n"
    )
    assert _gov(text) == []


def test_extra_clause_gate_not_flagged():
    # Syria SyriaFocus.78 shape: exhaustive (all five groups), but one clause
    # carries an original_tag gate, so it is not a clean two-condition
    # comparison and must not collapse (the gate would be silently dropped).
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  FROM = { has_government = democratic } }\n"
        "  AND = { has_government = communism  FROM = { has_government = communism } }\n"
        "  AND = { has_government = fascism  FROM = { has_government = fascism } }\n"
        "  AND = { has_government = neutrality  FROM = { has_government = neutrality } }\n"
        "  AND = { original_tag = PAL  has_government = nationalist  FROM = { has_government = nationalist } }\n"
        "}\n"
    )
    assert _gov(text) == []


def test_extra_bare_condition_in_clause_not_flagged():
    # Every clause carries an extra `has_war = yes`; collapsing to
    # `has_government = FROM` would silently drop it.
    text = (
        "OR = {\n"
        + "\n".join(
            "  AND = {{ has_government = {i}  has_war = yes  "
            "FROM = {{ has_government = {i} }} }}".format(i=i)
            for i in ("democratic", "communism", "fascism", "neutrality", "nationalist")
        )
        + "\n}\n"
    )
    assert _gov(text) == []


def test_extra_scope_block_in_clause_not_flagged():
    # A second scope block (GER = { exists = yes }) is a real gate the collapse
    # would drop.
    text = (
        "OR = {\n"
        + "\n".join(
            "  AND = {{ has_government = {i}  GER = {{ exists = yes }}  "
            "FROM = {{ has_government = {i} }} }}".format(i=i)
            for i in ("democratic", "communism", "fascism", "neutrality", "nationalist")
        )
        + "\n}\n"
    )
    assert _gov(text) == []


def test_unrelated_not_inside_scope_not_misclassified():
    # NOT wraps an unrelated trigger, not has_government; must not be read as a
    # "different government" clause (and the extra trigger makes it non-clean).
    text = (
        "OR = {\n"
        + "\n".join(
            "  AND = {{ has_government = {i}  "
            "FROM = {{ NOT = {{ has_war = yes }} has_government = {i} }} }}".format(i=i)
            for i in ("democratic", "communism", "fascism", "neutrality", "nationalist")
        )
        + "\n}\n"
    )
    assert _gov(text) == []


def test_double_negation_collapses_to_same():
    # NOT = { FROM = { NOT = { has_government = X } } } is "same government".
    text = (
        "OR = {\n"
        + "\n".join(
            "  AND = {{ has_government = {i}  "
            "NOT = {{ FROM = {{ NOT = {{ has_government = {i} }} }} }} }}".format(i=i)
            for i in ("democratic", "communism", "fascism", "neutrality", "nationalist")
        )
        + "\n}\n"
    )
    assert _gov(text) == ["has_government = FROM"]


def test_inconsistent_target_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  FROM = { has_government = democratic } }\n"
        "  AND = { has_government = communism  SYR = { has_government = communism } }\n"
        "  AND = { has_government = fascism  FROM = { has_government = fascism } }\n"
        "  AND = { has_government = neutrality  FROM = { has_government = neutrality } }\n"
        "  AND = { has_government = nationalist  FROM = { has_government = nationalist } }\n"
        "}\n"
    )
    assert _gov(text) == []


def test_mixed_sense_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  FROM = { has_government = democratic } }\n"
        "  AND = { has_government = communism  FROM = { NOT = { has_government = communism } } }\n"
        "  AND = { has_government = fascism  FROM = { has_government = fascism } }\n"
        "  AND = { has_government = neutrality  FROM = { has_government = neutrality } }\n"
        "  AND = { has_government = nationalist  FROM = { has_government = nationalist } }\n"
        "}\n"
    )
    assert _gov(text) == []


# --- bare multi-child NOT ----------------------------------------------------


def test_two_child_not_flagged():
    assert _not("NOT = { tag = USA tag = CHI }\n") == [(1, 2)]


def test_not_or_wrapper_clean():
    assert _not("NOT = { OR = { tag = USA tag = CHI } }\n") == []


def test_not_and_wrapper_clean():
    assert _not("NOT = { AND = { tag = USA has_war = yes } }\n") == []


def test_single_trigger_not_clean():
    assert _not("NOT = { has_capitulated = yes }\n") == []


def test_nested_not_inside_or_still_detected():
    text = "OR = {\n  tag = USA\n  NOT = { tag = GER tag = ITA }\n}\n"
    assert _not(text) == [(3, 2)]


def test_single_child_multiline_clean():
    text = "NOT = {\n\thas_country_flag = some_flag\n}\n"
    assert _not(text) == []


def test_block_child_beside_scalar_flagged():
    # An OR wrapper plus a trailing bare trigger is still two children.
    assert _not("NOT = { OR = { tag = USA tag = CHI } has_war = yes }\n") == [(1, 2)]


def test_random_state_controller_tag_root_collapses():
    text = (
        "random_state = {\n"
        "  limit = { controller = { tag = ROOT } }\n"
        "  add_stability = 0.1\n"
        "}\n"
    )
    assert _controlled(text) == [(1, "controller = { tag = ROOT }")]


def test_random_state_controller_tag_from_with_other_limit_collapses():
    text = (
        "random_state = {\n"
        "  limit = {\n"
        "    controller = { tag = FROM }\n"
        "    free_building_slots = { building = dockyard size > 1 }\n"
        "  }\n"
        "}\n"
    )
    assert _controlled(text) == [(1, "controller = { tag = FROM }")]


def test_random_state_is_controlled_by_collapses():
    text = "random_state = { limit = { is_controlled_by = ROOT is_coastal = yes } }\n"
    assert _controlled(text) == [(1, "is_controlled_by = ROOT")]


def test_comparison_before_controller_still_flagged():
    text = (
        "random_state = {\n"
        "  limit = {\n"
        "    infrastructure > 0\n"
        "    controller = { tag = ROOT }\n"
        "  }\n"
        "}\n"
    )
    assert _controlled(text) == [(1, "controller = { tag = ROOT }")]


def test_random_state_without_controller_not_flagged():
    assert _controlled("random_state = { limit = { is_owned_by = GER } }\n") == []


def test_random_owned_state_controller_not_flagged():
    text = "random_owned_state = { limit = { controller = { tag = ROOT } } }\n"
    assert _controlled(text) == []


def test_nested_or_controller_not_flagged():
    text = (
        "random_state = {\n"
        "  limit = { OR = { controller = { tag = ROOT } is_coastal = yes } }\n"
        "}\n"
    )
    assert _controlled(text) == []


def test_not_controller_not_flagged():
    text = "random_state = {\n  limit = { NOT = { controller = { tag = ROOT } } }\n}\n"
    assert _controlled(text) == []


def test_controller_original_tag_not_flagged():
    text = "random_state = { limit = { controller = { original_tag = SUD } } }\n"
    assert _controlled(text) == []


def test_controller_extra_condition_not_flagged():
    text = (
        "random_state = {\n  limit = { controller = { tag = ROOT has_war = yes } }\n}\n"
    )
    assert _controlled(text) == []


def test_controller_in_effect_body_not_flagged():
    text = (
        "random_state = {\n"
        "  limit = { is_coastal = yes }\n"
        "  controller = { add_stability = 0.1 }\n"
        "}\n"
    )
    assert _controlled(text) == []


def test_scan_pattern_matches_direct_common_file_only():
    from validate_simplifications import _matches_relative_pattern

    assert _matches_relative_pattern("common/test.txt", ["common/*.txt"])
    assert not _matches_relative_pattern("common/nested/test.txt", ["common/*.txt"])


def test_scan_patterns_preserve_recursive_overlap_without_absolute_prefix():
    from validate_simplifications import _matches_relative_pattern

    patterns = ["common/*.txt", "common/**/*.txt"]
    assert _matches_relative_pattern("common/test.txt", patterns)
    assert _matches_relative_pattern("common/nested/test.txt", patterns)
    assert not _matches_relative_pattern("other/common/test.txt", patterns)


# --- malformed input must never crash or false-flag ------------------------


def test_unterminated_tag_block_is_not_an_expansion():
    assert _expansion("USA = { exists = yes\n") == []


def test_logical_operator_header_is_not_a_tag_scope():
    # NOT/AND are three-caps tokens but never country scopes.
    assert _expansion("NOT = { exists = yes }\n") == []


def test_unterminated_random_list_is_skipped():
    assert _random("random_list = { 50 = { a = yes } 50 = {}\n") == []


def test_final_bucket_flush_against_body_end_still_collapses():
    # No trailing whitespace after the last bucket: the walker must finish on
    # the loop condition, not on a failed search.
    assert _random("random_list = { 50 = { add_stability = 0.1 } 50 = {}}") == [50]


def test_quoted_brace_between_buckets_is_treated_as_malformed():
    # `"z = {"` looks like a bucket opener to the header regex but never
    # balances; the walker must bail instead of reporting a bogus collapse.
    text = 'random_list = { 50 = { a = yes } log = "z = {" 60 = { } }\n'
    assert _random(text) == []


def test_non_weight_child_is_not_a_bucket_list():
    assert _random("random_list = { 50 = { a = yes } foo = { } }\n") == []


def test_zero_total_weight_is_skipped():
    # 0/0 has no meaningful chance to suggest.
    assert _random("random_list = { 0 = { a = yes } 0 = { } }\n") == []


def test_unterminated_create_unit_stops_the_run():
    assert _count('create_unit = { division = "x"\n') == []


def test_unterminated_visible_block_is_skipped():
    assert _empty("visible = {\n") == []


def test_unterminated_random_state_is_skipped():
    assert (
        _controlled("random_state = { limit = { controller = { tag = ROOT } }\n") == []
    )


def test_random_state_without_a_limit_is_skipped():
    assert _controlled("random_state = { add_stability = 0.1 }\n") == []


def test_limit_after_another_child_is_still_found():
    text = (
        "random_state = { prioritize = yes limit = { controller = { tag = ROOT } } }\n"
    )
    assert _controlled(text) == [(1, "controller = { tag = ROOT }")]


# --- government-match rejections -------------------------------------------


def test_two_bare_government_checks_in_one_clause_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  has_government = communism  "
        "FROM = { has_government = democratic } }\n"
        "}\n"
    )
    assert _gov(text) == []


def test_quoted_brace_inside_a_clause_not_flagged():
    text = "OR = {\n" '  AND = { has_government = democratic  log = "x = {" }\n' "}\n"
    assert _gov(text) == []


def test_bare_not_without_a_scope_block_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  NOT = { has_war = yes } }\n"
        "}\n"
    )
    assert _gov(text) == []


def test_outer_not_with_an_extra_trigger_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  "
        "NOT = { has_war = yes  FROM = { has_government = democratic } } }\n"
        "}\n"
    )
    assert _gov(text) == []


def test_outer_not_wrapping_an_unrelated_trigger_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  NOT = { FROM = { has_war = yes } } }\n"
        "}\n"
    )
    assert _gov(text) == []


def test_unterminated_or_block_is_skipped():
    assert _gov("OR = {\n  AND = { has_government = democratic }\n") == []


def test_non_and_child_of_or_not_flagged():
    assert _gov("OR = {\n  FROM = { has_government = democratic }\n}\n") == []


def test_quoted_and_opener_after_a_clause_not_flagged():
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  FROM = { has_government = democratic } }\n"
        '  log = "AND = {"\n'
        "}\n"
    )
    assert _gov(text) == []


def test_bare_condition_beside_two_clauses_not_flagged():
    # Leftover text outside the AND spans means collapsing would drop a gate.
    text = (
        "OR = {\n"
        "  AND = { has_government = democratic  FROM = { has_government = democratic } }\n"
        "  AND = { has_government = communism  FROM = { has_government = communism } }\n"
        "  has_war = yes\n"
        "}\n"
    )
    assert _gov(text) == []


# --- child counting --------------------------------------------------------


def test_children_counted_up_to_the_body_end():
    # Body ends flush with the last value, with no trailing whitespace.
    assert _not("NOT = { tag = USA tag = CHI}\n") == [(1, 2)]


def test_unparseable_child_stops_the_count():
    assert _not("NOT = { garbage }\n") == []


def test_unterminated_not_block_is_skipped():
    assert _not("NOT = { tag = USA\n") == []


def test_quoted_child_value_counts_as_one_child():
    assert _count_children(' name = "alpha" other = yes') == 2


def test_unterminated_quoted_value_stops_the_count():
    assert _count_children(' name = "alpha other = yes') == 1


def test_unterminated_child_block_stops_the_count():
    assert _count_children(" a = { c = 1") == 1


def test_missing_child_value_stops_the_count():
    assert _count_children(" tag =") == 1


# --- direct child iteration ------------------------------------------------


def test_direct_assignments_walk_to_the_body_end():
    assert list(_iter_direct_assignments(" a = yes")) == [("a", "yes", False)]


def test_direct_assignments_stop_on_an_unparseable_child():
    assert list(_iter_direct_assignments(" garbage")) == []


def test_direct_assignments_stop_on_an_unterminated_block():
    assert list(_iter_direct_assignments(" a = { b = 1")) == []


def test_direct_assignments_yield_quoted_values_verbatim():
    assert list(_iter_direct_assignments(' a = "x y" b = yes')) == [
        ("a", '"x y"', False),
        ("b", "yes", False),
    ]


def test_direct_assignments_stop_on_an_unterminated_quote():
    assert list(_iter_direct_assignments(' a = "x')) == []


def test_direct_assignments_stop_on_a_missing_value():
    assert list(_iter_direct_assignments(" a =")) == []


# --- scope merging ---------------------------------------------------------


def test_relation_scope_blocks_merge():
    assert _merge_lines("owner = { a = yes }\nowner = { b = yes }\n") == [2]


def test_final_block_without_a_trailing_newline_still_merges():
    assert _merge_lines("USA = { a = yes }\nUSA = { b = yes }") == [2]


def test_unterminated_block_stops_the_merge_walk():
    assert _merge_lines("USA = { a = yes }\nUSA = { b = yes\n") == []


# --- composite pass and validator wiring -----------------------------------


def test_composite_runs_only_the_not_pass_outside_the_effect_dirs():
    text = "ai_strategy = {\n  allowed = { NOT = { tag = USA tag = GER } }\n}\n"
    findings = _scan_composite(text, "common/ai_strategy/test.txt")
    assert [line for _message, line in findings] == [2]
    assert "NOT with 2 children" in findings[0][0]


def test_composite_skips_a_path_outside_both_pattern_sets():
    text = "USA = { a = yes }\nUSA = { b = yes }\nNOT = { tag = USA tag = GER }\n"
    assert _scan_composite(text, "history/countries/USA.txt") == []


def test_composite_reports_every_detector():
    text = (
        "USA = { exists = yes }\n"
        "random_list = { 30 = { add_stability = 0.1 } 70 = { } }\n"
        'create_unit = { division = "x" owner = ALG }\n'
        'create_unit = { division = "x" owner = ALG }\n'
        "visible = { }\n"
        + _all_five("FROM", "{t} = {{ has_government = {i} }}")
        + "random_state = { limit = { is_controlled_by = ROOT } }\n"
    )
    messages = [m for m, _line in _scan_composite(text, "common/national_focus/t.txt")]

    assert any("use `country_exists = USA`" in m for m in messages)
    assert any("random = { chance = 30" in m for m in messages)
    assert any("identical adjacent `create_unit`" in m for m in messages)
    assert any("empty `visible = { }` block" in m for m in messages)
    assert any("use `has_government = FROM`" in m for m in messages)
    assert any("use `random_controlled_state`" in m for m in messages)


def test_composite_runs_both_passes_inside_the_effect_dirs():
    text = "USA = { a = yes }\nUSA = { b = yes }\nNOT = { tag = USA tag = GER }\n"
    findings = _scan_composite(text, "common/national_focus/test.txt")
    messages = [message for message, _line in findings]
    assert any("can be merged into one" in m for m in messages)
    assert any("NOT with 2 children" in m for m in messages)


def test_validator_reports_findings_with_file_and_line(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/national_focus/test_tree.txt",
        "focus_tree = {\n"
        "\tid = test_tree\n"
        "\tfocus = {\n"
        "\t\tid = TST_focus\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tUSA = { add_stability = 0.01 }\n"
        "\t\t\tUSA = { add_war_support = 0.01 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    write_path(
        tmp_path,
        "common/ai_strategy/test_ai.txt",
        "ai_strategy = {\n\tallowed = { NOT = { tag = USA tag = GER } }\n}\n",
    )

    validator = vs.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    found = {(issue.file, issue.line) for issue in validator._issues}
    assert found == {
        ("common/national_focus/test_tree.txt", 7),
        ("common/ai_strategy/test_ai.txt", 2),
    }
    assert {issue.severity for issue in validator._issues} == {"warning"}
    assert {issue.category for issue in validator._issues} == {"simplification"}


def test_clean_tree_reports_nothing(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/national_focus/clean.txt",
        "focus_tree = {\n\tid = clean\n}\n",
    )

    validator = vs.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    assert validator._issues == []


def test_cli_entry_point_exits_zero(tmp_path, monkeypatch, write_path):
    write_path(
        tmp_path,
        "common/national_focus/clean.txt",
        "focus_tree = {\n\tid = clean\n}\n",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [vs.__file__, "--path", str(tmp_path), "--workers", "1", "--no-color"],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(vs.__file__, run_name="__main__")

    assert exit_info.value.code == 0
