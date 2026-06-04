"""Unit tests for validate_simplifications.

Pin the two detectors and, critically, the safety suppressions: merging
consecutive same-scope blocks is only valid in AND/sequential contexts, never
under OR / random_list / count_triggers, and never for non-deterministic
(random_*) or iterator scopes.
"""

from validate_simplifications import (
    _find_mergeable,
    _find_scope_expansion,
    _find_two_bucket_random,
    strip_comments,
)


def _merge_lines(text):
    return sorted(line for line, _ in _find_mergeable(strip_comments(text)))


def _expansion(text):
    return [(tag, flat) for _, tag, flat in _find_scope_expansion(strip_comments(text))]


def _random(text):
    return [chance for _, chance in _find_two_bucket_random(strip_comments(text))]


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
