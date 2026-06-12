"""
Unit tests for the checks added to check_common_mistakes.py:

  1. Consecutive same-tag scope blocks
  2. send_embargo / break_embargo without DLC guard
  3. divide_variable without zero guard
  4. Duplicate consecutive add_to_variable lines
  5. every_country with has_idea = X_member when array exists
  6. has_idea mutex inside NOT/AND blocks
  7. change_influence_percentage setter with no matching call
  8. check_variable with inline >= / <=
  9. tautological OR = { X = yes X = no }
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from check_common_mistakes import (
    _check_check_var_ge_le,
    _check_consecutive_scope_blocks,
    _check_divide_variable_zero_guard,
    _check_duplicate_add_to_variable,
    _check_embargo_dlc_guard,
    _check_every_country_member_array,
    _check_has_idea_mutex_in_not_block,
    _check_influence_setter_scope,
    _check_tautological_or,
)

passed = 0
failed = 0


def assert_finds(check_fn, lines, expected_count, label):
    global passed, failed
    result = check_fn(lines)
    if len(result) == expected_count:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(
            f"  FAIL  {label}: expected {expected_count} finding(s), got {len(result)}"
        )
        for ln, msg in result:
            print(f"        line {ln}: {msg}")


# 1. Consecutive same-tag scope blocks

print("\n── Consecutive scope blocks ──")

# 1a. Basic case: two adjacent TAG blocks → flag
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\t\tSOV = {\n",
        "\t\t\tadd_stability = 0.05\n",
        "\t\t}\n",
        "\t\tSOV = {\n",
        "\t\t\tadd_war_support = 0.05\n",
        "\t\t}\n",
    ],
    1,
    "basic consecutive SOV blocks flagged",
)

# 1b. Different tags → no flag
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\t\tSOV = {\n",
        "\t\t\tadd_stability = 0.05\n",
        "\t\t}\n",
        "\t\tUSA = {\n",
        "\t\t\tadd_war_support = 0.05\n",
        "\t\t}\n",
    ],
    0,
    "different tags not flagged",
)

# 1c. Blocks in different parent scopes (available vs completion_reward) → no flag
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\tavailable = {\n",
        "\t\tJOR = {\n",
        "\t\t\texists = yes\n",
        "\t\t}\n",
        "\t}\n",
        "\tcompletion_reward = {\n",
        "\t\tJOR = {\n",
        "\t\t\tcountry_event = foo.1\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "different parent scopes (available vs completion_reward) not flagged",
)

# 1d. Blocks inside OR → no flag (merging changes OR semantics)
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\tOR = {\n",
        "\t\tSOV = {\n",
        "\t\t\texists = yes\n",
        "\t\t}\n",
        "\t\tSOV = {\n",
        "\t\t\thas_war = yes\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "blocks inside OR not flagged",
)

# 1e. Blocks inside NOT → no flag (merging changes NOT semantics)
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\tNOT = {\n",
        "\t\tLEB = {\n",
        "\t\t\texists = yes\n",
        "\t\t}\n",
        "\t\tLEB = {\n",
        "\t\t\thas_war = yes\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "blocks inside NOT not flagged",
)

# 1f. Three consecutive blocks → flag both pairs (or at least 2 findings)
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\t\tBLR = {\n",
        "\t\t\tadd_opinion = yes\n",
        "\t\t}\n",
        "\t\tBLR = {\n",
        "\t\t\tcountry_event = foo.1\n",
        "\t\t}\n",
        "\t\tBLR = {\n",
        "\t\t\tset_country_flag = bar\n",
        "\t\t}\n",
    ],
    2,
    "three consecutive blocks produce two findings",
)

# 1g. Intervening non-blank line resets tracking → no flag
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\t\tSOV = {\n",
        "\t\t\tadd_stability = 0.05\n",
        "\t\t}\n",
        "\t\tadd_political_power = 50\n",
        "\t\tSOV = {\n",
        "\t\t\tadd_war_support = 0.05\n",
        "\t\t}\n",
    ],
    0,
    "intervening code between blocks not flagged",
)

# 1h. Blocks in different if/else_if branches → no flag
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\tif = {\n",
        "\t\tlimit = { always = yes }\n",
        "\t\tKAZ = {\n",
        "\t\t\tcountry_event = foo.1\n",
        "\t\t}\n",
        "\t}\n",
        "\telse_if = {\n",
        "\t\tlimit = { always = no }\n",
        "\t\tKAZ = {\n",
        "\t\t\tcountry_event = foo.2\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "blocks in different if/else_if branches not flagged",
)

# 1i. Gap > 4 lines → no flag
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\t\tSOV = {\n",
        "\t\t\tadd_stability = 0.05\n",
        "\t\t}\n",
        "\n",
        "\n",
        "\n",
        "\n",
        "\n",
        "\t\tSOV = {\n",
        "\t\t\tadd_war_support = 0.05\n",
        "\t\t}\n",
    ],
    0,
    "gap > 4 lines not flagged",
)

# 1j. FROM scope blocks (non-3-letter) → flag
assert_finds(
    _check_consecutive_scope_blocks,
    [
        "\t\tFROM = {\n",
        "\t\t\tadd_stability = 0.05\n",
        "\t\t}\n",
        "\t\tFROM = {\n",
        "\t\t\tadd_war_support = 0.05\n",
        "\t\t}\n",
    ],
    1,
    "consecutive FROM blocks flagged",
)


# 2. send_embargo / break_embargo without DLC guard

print("\n── Embargo DLC guard ──")

# 2a. Ungated embargo → flag
assert_finds(
    _check_embargo_dlc_guard,
    [
        "option = {\n",
        "\tname = test.1.a\n",
        "\tsend_embargo = TAG\n",
        "}\n",
    ],
    1,
    "ungated send_embargo flagged",
)

# 2b. Gated embargo → no flag
assert_finds(
    _check_embargo_dlc_guard,
    [
        "option = {\n",
        "\tname = test.1.a\n",
        "\tif = {\n",
        '\t\tlimit = { has_dlc = "By Blood Alone" }\n',
        "\t\tsend_embargo = TAG\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "DLC-gated send_embargo not flagged",
)

# 2c. break_embargo also caught
assert_finds(
    _check_embargo_dlc_guard,
    [
        "\tbreak_embargo = TAG\n",
    ],
    1,
    "ungated break_embargo flagged",
)

# 2d. DLC guard in outer scope covers inner embargo
assert_finds(
    _check_embargo_dlc_guard,
    [
        "if = {\n",
        '\tlimit = { has_dlc = "By Blood Alone" }\n',
        "\tTAG = {\n",
        "\t\tsend_embargo = OTHER\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "outer DLC guard covers inner embargo",
)


# 3. divide_variable without zero guard

print("\n── Divide variable zero guard ──")

# 3a. Unguarded division by variable → flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tdivide_variable = { global.avg = global.count }\n",
    ],
    1,
    "unguarded variable division flagged",
)

# 3b. Division by literal number → no flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tdivide_variable = { cost = 100 }\n",
    ],
    0,
    "literal divisor not flagged",
)

# 3c. Guarded by check_variable → no flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tif = {\n",
        "\t\tlimit = { check_variable = { global.count > 0 } }\n",
        "\t\tdivide_variable = { global.avg = global.count }\n",
        "\t}\n",
    ],
    0,
    "check_variable guard suppresses flag",
)

# 3d. Guarded by clamp_variable → no flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tclamp_variable = { var = divisor min = 0.001 }\n",
        "\tdivide_variable = { result = divisor }\n",
    ],
    0,
    "clamp_variable guard suppresses flag",
)

# 3e. Guarded by clamp_temp_variable → no flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tclamp_temp_variable = { var = tmp_div min = 0.1 }\n",
        "\tdivide_variable = { result = tmp_div }\n",
    ],
    0,
    "clamp_temp_variable guard suppresses flag",
)

# 3f. Clamp with min = 0 → still flag (doesn't prevent zero)
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tclamp_variable = { var = divisor min = 0 }\n",
        "\tdivide_variable = { result = divisor }\n",
    ],
    1,
    "clamp with min=0 still flagged",
)

# 3g. Division in else block after if checking divisor = 0 → no flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tif = { limit = { check_variable = { workers = 0 } }\n",
        "\t\tset_variable = { fulfillment = 1 }\n",
        "\t}\n",
        "\telse = {\n",
        "\t\tdivide_variable = { fulfillment = workers }\n",
        "\t}\n",
    ],
    0,
    "else-block after if { var = 0 } suppresses flag",
)

# 3h. Guarded by set_variable with non-zero literal → no flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tset_variable = { SPR_regulare_cap_ratio = 2000 }\n",
        "\tdivide_variable = { SPR_regulare_cap = SPR_regulare_cap_ratio }\n",
    ],
    0,
    "set_variable with non-zero literal suppresses flag",
)

# 3i. set_variable with zero → still flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tset_variable = { my_divisor = 0 }\n",
        "\tdivide_variable = { result = my_divisor }\n",
    ],
    1,
    "set_variable with zero still flagged",
)


# 4. Duplicate consecutive add_to_variable

print("\n── Duplicate add_to_variable ──")

# 4a. Exact duplicate → flag
assert_finds(
    _check_duplicate_add_to_variable,
    [
        "\tadd_to_variable = { POTEF_attack = 0.10 tooltip = tt }\n",
        "\tadd_to_variable = { POTEF_attack = 0.10 tooltip = tt }\n",
    ],
    1,
    "exact duplicate add_to_variable flagged",
)

# 4b. Different values → no flag
assert_finds(
    _check_duplicate_add_to_variable,
    [
        "\tadd_to_variable = { POTEF_attack = 0.10 tooltip = tt }\n",
        "\tadd_to_variable = { POTEF_defence = 0.10 tooltip = tt }\n",
    ],
    0,
    "different variable names not flagged",
)

# 4c. Same variable but separated by other code → no flag
assert_finds(
    _check_duplicate_add_to_variable,
    [
        "\tadd_to_variable = { score = 5 }\n",
        "\tset_variable = { other = 1 }\n",
        "\tadd_to_variable = { score = 5 }\n",
    ],
    0,
    "non-consecutive duplicates not flagged",
)

# 4d. add_to_temp_variable also caught
assert_finds(
    _check_duplicate_add_to_variable,
    [
        "\tadd_to_temp_variable = { tmp = 10 }\n",
        "\tadd_to_temp_variable = { tmp = 10 }\n",
    ],
    1,
    "duplicate add_to_temp_variable flagged",
)

# 4e. Blank lines between duplicates → no flag (not consecutive)
assert_finds(
    _check_duplicate_add_to_variable,
    [
        "\tadd_to_variable = { score = 5 }\n",
        "\n",
        "\tadd_to_variable = { score = 5 }\n",
    ],
    0,
    "blank line between duplicates not flagged",
)


# 5. every_country with has_idea = X_member

print("\n── every_country member array ──")

# 5a. Simple every_country with EU_member → flag
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = { has_idea = EU_member }\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    1,
    "every_country with EU_member flagged",
)

# 5b. NATO_member → flag
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = { has_idea = NATO_member }\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    1,
    "every_country with NATO_member flagged",
)

# 5c. Non-member idea → no flag
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = { has_idea = some_other_idea }\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    0,
    "non-member idea not flagged",
)

# 5d. has_idea inside NOT → no flag (filtering OUT members)
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = {\n",
        "\t\t\tNOT = { has_idea = NATO_member }\n",
        "\t\t}\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    0,
    "has_idea inside NOT block not flagged",
)

# 5e. has_idea in OR with non-array ideas → no flag (too complex)
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = {\n",
        "\t\t\tOR = {\n",
        "\t\t\t\thas_idea = EU_member\n",
        "\t\t\t\thas_idea = LoAS_member\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    0,
    "OR with non-array idea suppresses flag",
)

# 5f. has_idea inside OVERLORD scope → no flag
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = {\n",
        "\t\t\tOVERLORD = { has_idea = NATO_member }\n",
        "\t\t}\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    0,
    "has_idea inside OVERLORD not flagged",
)

# 5g. has_idea in limit with additional conditions → flag (still convertible)
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = {\n",
        "\t\t\thas_idea = EU_member\n",
        "\t\t\thas_government = democratic\n",
        "\t\t}\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    1,
    "has_idea with additional conditions still flagged",
)

# 5h. has_idea NOT in the limit (nested inside body if-block) → no flag
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tsetup_employment_variables = yes\n",
        "\t\tif = { limit = { has_idea = NATO_member }\n",
        "\t\t\tadd_to_tech_sharing_group = NATO_Tech_Share\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "has_idea in body if-block (not limit) not flagged",
)


# has_idea mutex inside NOT block (raid_target_eligible bug)

print("\n── has_idea mutex inside NOT/AND blocks ──")

# Classic raid_target_eligible bug: two intervention ideas inside one NOT block
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "raid_target_eligible = {\n",
        "\tNOT = {\n",
        "\t\thas_idea = intervention_local_security\n",
        "\t\thas_idea = intervention_isolation\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "NOT block with two intervention doctrines flagged",
)

# Same trap inside an AND block (also broken — always false)
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "modifier = {\n",
        "\tAND = {\n",
        "\t\thas_idea = intervention_isolation\n",
        "\t\thas_idea = intervention_limited_interventionism\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "AND block with two intervention doctrines flagged",
)

# Same group split across separate NOT blocks — not flagged (this is the FIX)
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "raid_target_eligible = {\n",
        "\tNOT = { has_idea = intervention_local_security }\n",
        "\tNOT = { has_idea = intervention_isolation }\n",
        "}\n",
    ],
    0,
    "separate NOT blocks for same group not flagged",
)

# Two intervention ideas inside OR — not flagged (OR is the intended structure)
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "trigger = {\n",
        "\tNOT = {\n",
        "\t\tOR = {\n",
        "\t\t\thas_idea = intervention_isolation\n",
        "\t\t\thas_idea = intervention_local_security\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "NOT { OR { ... } } not flagged",
)

# Single intervention idea in a NOT block — fine
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "trigger = {\n",
        "\tNOT = { has_idea = intervention_isolation }\n",
        "}\n",
    ],
    0,
    "single intervention idea in NOT not flagged",
)

# Ideas from different mutex groups inside one NOT — not flagged (no false positive)
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "trigger = {\n",
        "\tNOT = {\n",
        "\t\thas_idea = intervention_isolation\n",
        "\t\thas_idea = NATO_member\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "ideas from different groups not flagged",
)

# Single-line NOT block with two mutex ideas — must be caught, not silently skipped
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "trigger = {\n",
        "\tNOT = { has_idea = intervention_isolation has_idea = intervention_local_security }\n",
        "}\n",
    ],
    1,
    "single-line NOT with two intervention doctrines flagged",
)

# Single-line AND block with two mutex ideas — also caught
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "modifier = { AND = { has_idea = intervention_isolation has_idea = intervention_limited_interventionism } }\n",
    ],
    1,
    "single-line AND with two intervention doctrines flagged",
)

# Single-line OR block with two mutex ideas — not flagged (OR is the intended structure)
assert_finds(
    _check_has_idea_mutex_in_not_block,
    [
        "trigger = { OR = { has_idea = intervention_isolation has_idea = intervention_local_security } }\n",
    ],
    0,
    "single-line OR with mutex ideas not flagged",
)


# 7. change_influence_percentage setter scope

print("\n── Influence setter scope ──")

# 7a. percent_change setter, no call anywhere in file → flag
assert_finds(
    _check_influence_setter_scope,
    [
        "\tset_temp_variable = { percent_change = 3 }\n",
        "\tset_temp_variable = { tag_index = THIS.id }\n",
    ],
    1,
    "percent_change setter with no call flagged",
)

# 7b. setter + matching call in same flat scope → no flag
assert_finds(
    _check_influence_setter_scope,
    [
        "\tset_temp_variable = { percent_change = 3 }\n",
        "\tchange_influence_percentage = yes\n",
    ],
    0,
    "setter with matching call not flagged",
)

# 7c. setter inside loop, call outside loop → flag (stale/default values)
assert_finds(
    _check_influence_setter_scope,
    [
        "\trandom_other_country = {\n",
        "\t\tset_temp_variable = { percent_change = 3 }\n",
        "\t\tset_temp_variable = { influence_target = PREV.id }\n",
        "\t}\n",
        "\tchange_influence_percentage = yes\n",
    ],
    1,
    "setter in loop with call outside loop flagged",
)

# 7d. setter and call both inside the loop → no flag
assert_finds(
    _check_influence_setter_scope,
    [
        "\trandom_other_country = {\n",
        "\t\tset_temp_variable = { percent_change = 3 }\n",
        "\t\tchange_influence_percentage = yes\n",
        "\t}\n",
    ],
    0,
    "setter and call both inside loop not flagged",
)

# 7e. no percent_change setter at all → no flag
assert_finds(
    _check_influence_setter_scope,
    [
        "\tchange_influence_percentage = yes\n",
    ],
    0,
    "no setter present not flagged",
)


# 8. check_variable with inline >= / <=

print("\n── check_variable inline >= / <= ──")

# 8a. inline >= → flag
assert_finds(
    _check_check_var_ge_le,
    [
        "\tcheck_variable = { my_var >= 5 }\n",
    ],
    1,
    "inline >= flagged",
)

# 8b. inline <= → flag
assert_finds(
    _check_check_var_ge_le,
    [
        "\tcheck_variable = { my_var <= 5 }\n",
    ],
    1,
    "inline <= flagged",
)

# 8c. strict inequality → no flag
assert_finds(
    _check_check_var_ge_le,
    [
        "\tcheck_variable = { my_var > 5 }\n",
    ],
    0,
    "strict > not flagged",
)

# 8d. compare = syntax → no flag
assert_finds(
    _check_check_var_ge_le,
    [
        "\tcheck_variable = { var = my_var value = 5 compare = greater_than_or_equals }\n",
    ],
    0,
    "compare = syntax not flagged",
)

# 8e. >= inside a comment → no flag
assert_finds(
    _check_check_var_ge_le,
    [
        "\t# check_variable = { my_var >= 5 }\n",
    ],
    0,
    ">= in comment not flagged",
)


# 9. Tautological OR = { X = yes X = no }

print("\n── Tautological OR ──")

# 9a. classic tautology → flag
assert_finds(
    _check_tautological_or,
    [
        "\t\tmodifier = { add = 1 OR = { is_historical_focus_on = yes is_historical_focus_on = no } }\n",
    ],
    1,
    "OR { X = yes X = no } flagged",
)

# 9b. reversed order (no then yes) → flag
assert_finds(
    _check_tautological_or,
    [
        "\t\tOR = { is_historical_focus_on = no is_historical_focus_on = yes }\n",
    ],
    1,
    "OR { X = no X = yes } flagged",
)

# 9c. different tokens → no flag
assert_finds(
    _check_tautological_or,
    [
        "\t\tOR = { is_historical_focus_on = yes is_debug = no }\n",
    ],
    0,
    "OR with different tokens not flagged",
)

# 9d. both yes → no flag
assert_finds(
    _check_tautological_or,
    [
        "\t\tOR = { has_war = yes has_war = yes }\n",
    ],
    0,
    "OR with both yes not flagged",
)

# 9e. tautology inside a comment → no flag
assert_finds(
    _check_tautological_or,
    [
        "\t\t# OR = { is_historical_focus_on = yes is_historical_focus_on = no }\n",
    ],
    0,
    "tautological OR in comment not flagged",
)


# Summary


def test_no_failures():
    """pytest entry point: fails the suite if any module-level assertion failed."""
    assert failed == 0, f"{failed} assertion(s) failed (see stdout)"


if __name__ == "__main__":
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        print("SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)
