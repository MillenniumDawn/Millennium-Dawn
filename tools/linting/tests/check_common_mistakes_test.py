"""
Unit tests for the checks added to check_common_mistakes.py (in file order):

  1. Consecutive same-tag scope blocks
  2. send_embargo / break_embargo without DLC guard
  3. divide_variable without zero guard
  4. Duplicate consecutive add_to_variable lines
  5. every_country with has_idea = X_member when array exists
  6. any_country/any_other_country with has_idea = X_member (trigger context)
  7. on_add adds to a global array the sibling on_remove never removes from
  8. has_idea mutex inside NOT/AND blocks
  9. change_influence_percentage setter with no matching call
  10. check_variable with inline >= / <=
  11. tautological OR = { X = yes X = no }
  12. dynamic triggers in decision allowed blocks
  13. focus declares war without will_lead_to_war_with
  14. check_expr operand chained with a raw comparator symbol
  15. every_owned_controlled_state (nonexistent effect)
  16. random_select_amount set to a non-integer-literal
  17. focus/decision/event log = "..." referencing the wrong id (Check C)
  18. hidden_trigger = { } directly inside custom_trigger_tooltip (Check E1)
  19. malformed country leader rotations in *_political_leaders.txt
  20. country_exists scope contradiction — NOT = { country_exists = TAG }
  21. single-valued-trigger contradiction, including single-line forms
  22. embargo DLC guard must not leak an inline guard to the parent frame
  23. is_X_nation regex matches multi-segment nation names
  24. _get_block ignores braces inside quoted strings
  25. ideas brace tracking ignores braces inside comments (check_file)
  26. division check does not fire inside quoted strings (check_file)
  27. mutex-trigger regex built from _MUTUALLY_EXCLUSIVE_TRIGGERS
  28. embargo guard stack is quote-aware (stray brace in log/loc string)
  29. _files_need_global_refs pre-scan gate matches whitespace-flexible form
  30. add_to_faction with a non-country argument (a faction name)
  31. create_faction is deprecated (use create_faction_from_template)
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from check_common_mistakes import (
    _RE_IS_X_NATION,
    _check_add_to_faction_country,
    _check_any_country_member_array,
    _check_check_expr_bad_operand,
    _check_check_var_ge_le,
    _check_consecutive_scope_blocks,
    _check_country_exists_scope_contradiction,
    _check_create_faction_deprecated,
    _check_decision_allowed_dynamic,
    _check_decision_log_id,
    _check_divide_variable_zero_guard,
    _check_duplicate_add_to_variable,
    _check_embargo_dlc_guard,
    _check_event_log_id,
    _check_every_country_member_array,
    _check_every_owned_controlled_state,
    _check_focus_log_id,
    _check_focus_missing_war_hint,
    _check_has_idea_mutex_in_not_block,
    _check_hidden_trigger_in_ctt,
    _check_influence_setter_scope,
    _check_leader_rotation,
    _check_mutually_exclusive_contradictions,
    _check_on_add_array_symmetry,
    _check_random_select_amount_literal,
    _check_tautological_or,
    _files_need_global_refs,
    _get_block,
    check_file,
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

# 3j. Allowlisted divisor (invariant non-zero) → no flag
assert_finds(
    _check_divide_variable_zero_guard,
    [
        "\tdivide_variable = { global.target_civ_count = global.UN_general_assembly^num }\n",
    ],
    0,
    "allowlisted divisor suppresses flag",
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
        "\t\t\t\thas_idea = the_military\n",
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


# 5i. every_other_country with member idea → flag, message mentions ROOT guard
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_other_country = {\n",
        "\t\tlimit = { has_idea = NATO_member }\n",
        "\t\tadd_opinion_modifier = { target = ROOT modifier = test }\n",
        "\t}\n",
    ],
    1,
    "every_other_country with NATO_member flagged",
)

# 5j. for_each_scope_loop itself → no flag (already converted)
assert_finds(
    _check_every_country_member_array,
    [
        "\tfor_each_scope_loop = {\n",
        "\t\tarray = global.nato_members\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    0,
    "for_each_scope_loop not flagged",
)


# any_country/any_other_country with member idea (trigger context)

print("\n── any_country member array ──")

# Simple any_country testing EU_member → flag
assert_finds(
    _check_any_country_member_array,
    [
        "\tany_country = {\n",
        "\t\thas_idea = EU_member\n",
        "\t\thas_war_with = ROOT\n",
        "\t}\n",
    ],
    1,
    "any_country with EU_member flagged",
)

# any_other_country → flag
assert_finds(
    _check_any_country_member_array,
    [
        "\tany_other_country = {\n",
        "\t\thas_idea = NATO_member\n",
        "\t}\n",
    ],
    1,
    "any_other_country with NATO_member flagged",
)

# NOT-wrapped member idea → no flag (testing non-membership)
assert_finds(
    _check_any_country_member_array,
    [
        "\tany_country = {\n",
        "\t\tNOT = { has_idea = NATO_member }\n",
        "\t\thas_war_with = ROOT\n",
        "\t}\n",
    ],
    0,
    "any_country with NOT-wrapped idea not flagged",
)

# OR mixing array-backed and non-array ideas → no flag
assert_finds(
    _check_any_country_member_array,
    [
        "\tany_country = {\n",
        "\t\tOR = {\n",
        "\t\t\thas_idea = EU_member\n",
        "\t\t\thas_idea = the_military\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "any_country OR with non-array idea not flagged",
)

# LoAS mapping: arab league array is idea-synced now
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = { has_idea = LoAS_member }\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    1,
    "every_country with LoAS_member flagged",
)

# OR of both LoAS variants → same array → single-loop advice, one finding
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = {\n",
        "\t\t\tOR = {\n",
        "\t\t\t\thas_idea = LoAS_member\n",
        "\t\t\t\thas_idea = LoAS_member_upd\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    1,
    "OR of LoAS variants flagged once (same array)",
)

# OR spanning two DIFFERENT arrays → still one finding, split-loop advice
assert_finds(
    _check_every_country_member_array,
    [
        "\tevery_country = {\n",
        "\t\tlimit = {\n",
        "\t\t\tOR = {\n",
        "\t\t\t\thas_idea = EU_member\n",
        "\t\t\t\thas_idea = NATO_member\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t\tadd_stability = 0.05\n",
        "\t}\n",
    ],
    1,
    "OR spanning two arrays flagged once with split advice",
)

# Non-member idea → no flag
assert_finds(
    _check_any_country_member_array,
    [
        "\tany_country = {\n",
        "\t\thas_idea = some_other_idea\n",
        "\t}\n",
    ],
    0,
    "any_country with non-member idea not flagged",
)

# any_of_scopes itself → no flag (already converted)
assert_finds(
    _check_any_country_member_array,
    [
        "\tany_of_scopes = {\n",
        "\t\tarray = global.EU_member\n",
        "\t\thas_war_with = ROOT\n",
        "\t}\n",
    ],
    0,
    "any_of_scopes not flagged",
)


# on_add/on_remove global-array symmetry (Arab League stale-entry bug class)

print("\n── on_add array symmetry ──")

# on_add adds to array, on_remove doesn't remove → flag
assert_finds(
    _check_on_add_array_symmetry,
    [
        "ideas = {\n",
        "\tcountry = {\n",
        "\t\tbloc_member = {\n",
        "\t\t\ton_add = {\n",
        "\t\t\t\tadd_to_array = { global.bloc_members = THIS }\n",
        "\t\t\t}\n",
        "\t\t\ton_remove = {\n",
        '\t\t\t\tlog = "x"\n',
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "on_add without matching on_remove removal flagged",
)

# Symmetric hooks → no flag (guarded forms included)
assert_finds(
    _check_on_add_array_symmetry,
    [
        "ideas = {\n",
        "\tcountry = {\n",
        "\t\tbloc_member = {\n",
        "\t\t\ton_add = {\n",
        "\t\t\t\tif = {\n",
        "\t\t\t\t\tlimit = { NOT = { is_in_array = { global.bloc_members = THIS } } }\n",
        "\t\t\t\t\tadd_to_array = { global.bloc_members = THIS }\n",
        "\t\t\t\t}\n",
        "\t\t\t}\n",
        "\t\t\ton_remove = {\n",
        "\t\t\t\tif = {\n",
        "\t\t\t\t\tlimit = { NOT = { has_idea = bloc_member_upd } }\n",
        "\t\t\t\t\tremove_from_array = { global.bloc_members = THIS }\n",
        "\t\t\t\t}\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "symmetric guarded hooks not flagged",
)

# on_add with no on_remove block at all → flag
assert_finds(
    _check_on_add_array_symmetry,
    [
        "ideas = {\n",
        "\tcountry = {\n",
        "\t\tbloc_member = {\n",
        "\t\t\ton_add = {\n",
        "\t\t\t\tadd_to_array = { global.bloc_members = THIS }\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "on_add with no on_remove at all flagged",
)

# on_remove-only (adds happen in join effects) → no flag
assert_finds(
    _check_on_add_array_symmetry,
    [
        "ideas = {\n",
        "\tcountry = {\n",
        "\t\tbloc_member = {\n",
        "\t\t\ton_remove = {\n",
        "\t\t\t\tremove_from_array = { global.bloc_members = THIS }\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "remove-only hooks not flagged",
)

# Two sibling ideas each symmetric → no cross-contamination between groups
assert_finds(
    _check_on_add_array_symmetry,
    [
        "ideas = {\n",
        "\tcountry = {\n",
        "\t\tbloc_a = {\n",
        "\t\t\ton_add = { add_to_array = { global.a_members = THIS } }\n",
        "\t\t\ton_remove = { remove_from_array = { global.a_members = THIS } }\n",
        "\t\t}\n",
        "\t\tbloc_b = {\n",
        "\t\t\ton_add = { add_to_array = { global.b_members = THIS } }\n",
        "\t\t\ton_remove = { remove_from_array = { global.a_members = THIS } }\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "sibling idea removing the WRONG array flagged once",
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


# add_to_faction with a non-country argument (a faction name)

print("\n── add_to_faction non-country argument ──")

# faction name (uppercase, not a 3-letter tag) → flag
assert_finds(
    _check_add_to_faction_country,
    [
        "\tadd_to_faction = BRICS\n",
    ],
    1,
    "add_to_faction = BRICS (faction name) flagged",
)

# lowercase faction id → flag
assert_finds(
    _check_add_to_faction_country,
    [
        "\tadd_to_faction = warsaw_pact\n",
    ],
    1,
    "add_to_faction = warsaw_pact (lowercase faction id) flagged",
)

# 3-letter country tag → no flag
assert_finds(
    _check_add_to_faction_country,
    [
        "\tadd_to_faction = FIN\n",
    ],
    0,
    "add_to_faction = FIN (country tag) not flagged",
)

# scope keyword → no flag
assert_finds(
    _check_add_to_faction_country,
    [
        "\tadd_to_faction = ROOT\n",
    ],
    0,
    "add_to_faction = ROOT (scope keyword) not flagged",
)

# tag inside a scope switch → no flag (value is the 3-letter tag)
assert_finds(
    _check_add_to_faction_country,
    [
        "\tSOV = { add_to_faction = FIN }\n",
    ],
    0,
    "add_to_faction = FIN inside SOV scope not flagged",
)

# dotted scope chain (tricky-but-legal) → no flag
assert_finds(
    _check_add_to_faction_country,
    [
        "\tadd_to_faction = PREV.PREV\n",
    ],
    0,
    "add_to_faction = PREV.PREV (scope chain) not flagged",
)

# var: reference → no flag
assert_finds(
    _check_add_to_faction_country,
    [
        "\tadd_to_faction = var:ally_tag\n",
    ],
    0,
    "add_to_faction = var:ally_tag not flagged",
)

# faction name inside a comment → no flag
assert_finds(
    _check_add_to_faction_country,
    [
        "\t# add_to_faction = BRICS\n",
    ],
    0,
    "add_to_faction = BRICS in comment not flagged",
)


# 31. create_faction is deprecated (use create_faction_from_template)

print("\n── create_faction deprecated ──")

# bare form → flag
assert_finds(
    _check_create_faction_deprecated,
    [
        "\tcreate_faction = some_id\n",
    ],
    1,
    "create_faction = some_id (bare) flagged",
)

# quoted form → flag
assert_finds(
    _check_create_faction_deprecated,
    [
        '\tcreate_faction = "Name"\n',
    ],
    1,
    'create_faction = "Name" (quoted) flagged',
)

# inside a scope block → flag
assert_finds(
    _check_create_faction_deprecated,
    [
        "\tFROM = { create_faction = X }\n",
    ],
    1,
    "create_faction inside FROM scope block flagged",
)

# create_faction_from_template (the replacement) → no flag
assert_finds(
    _check_create_faction_deprecated,
    [
        "\tcreate_faction_from_template = faction_template_nato\n",
    ],
    0,
    "create_faction_from_template not flagged",
)

# on_create_faction (on_actions hook) → no flag; \b doesn't separate on_ from
# create since _ is a word char, but the trailing \s*= requirement alone
# rules this out too since neither on_ nor a bare hook name is followed by =
# immediately after create_faction.
assert_finds(
    _check_create_faction_deprecated,
    [
        "\ton_create_faction = {\n",
    ],
    0,
    "on_create_faction hook line not flagged",
)

# commented-out line → no flag
assert_finds(
    _check_create_faction_deprecated,
    [
        "\t# create_faction = X\n",
    ],
    0,
    "create_faction = X in comment not flagged",
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


# 11. Dynamic triggers in decision allowed blocks

print("\n── Dynamic trigger in decision allowed block ──")

# 11a. has_opinion directly inside allowed → flag
assert_finds(
    _check_decision_allowed_dynamic,
    [
        "GRE_decisions_category = {\n",
        "\tGRE_some_decision = {\n",
        "\t\tallowed = {\n",
        "\t\t\thas_opinion = { target = CHI value > 0 }\n",
        "\t\t}\n",
        "\t\tcomplete_effect = { add_political_power = 10 }\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "has_opinion inside multi-line allowed flagged",
)

# 11b. Single-line allowed = { original_tag } followed by available with
#      has_opinion → no flag (the bug: in_allowed bled into available)
assert_finds(
    _check_decision_allowed_dynamic,
    [
        "GRE_decisions_category = {\n",
        "\tGRE_some_decision = {\n",
        "\t\tallowed = { original_tag = GRE }\n",
        "\t\tavailable = {\n",
        "\t\t\tcountry_exists = CHI\n",
        "\t\t\thas_opinion = { target = CHI value > 0 }\n",
        "\t\t}\n",
        "\t\tcomplete_effect = { add_political_power = 10 }\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "has_opinion in available after single-line allowed not flagged",
)

# 11c. Single-line allowed = { has_opinion } → still flag
assert_finds(
    _check_decision_allowed_dynamic,
    [
        "GRE_decisions_category = {\n",
        "\tGRE_some_decision = {\n",
        "\t\tallowed = { has_opinion = { target = CHI value > 0 } }\n",
        "\t\tcomplete_effect = { add_political_power = 10 }\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "has_opinion in single-line allowed still flagged",
)

# 10. Focus declares war without will_lead_to_war_with

print("\n── Focus missing war hint ──")

# 10a. create_wargoal without the hint → flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_invade_morocco\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\tcreate_wargoal = { type = annex_everything target = MOR }\n",
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "create_wargoal without will_lead_to_war_with flagged",
)

# 10b. create_wargoal with the hint → no flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_invade_morocco\n",
        "\t\twill_lead_to_war_with = MOR\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\tcreate_wargoal = { type = annex_everything target = MOR }\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "create_wargoal with will_lead_to_war_with not flagged",
)

# 10c. declare_war without the hint → flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_strike_first\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\tdeclare_war_on = { target = MOR type = annex_everything }\n",
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "declare_war without will_lead_to_war_with flagged",
)

# 10d. focus that does not declare war → no flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_build_economy\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\tadd_political_power = 50\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "focus without create_wargoal not flagged",
)

# 10e. one compliant + one non-compliant focus → exactly one flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_good\n",
        "\t\twill_lead_to_war_with = MOR\n",
        "\t\tcompletion_reward = { create_wargoal = { target = MOR } }\n",
        "\t}\n",
        "\tfocus = {\n",
        "\t\tid = ALG_bad\n",
        "\t\tcompletion_reward = { create_wargoal = { target = TUN } }\n",
        "\t}\n",
    ],
    1,
    "only the focus missing the hint is flagged",
)

# 10f. create_wargoal inside effect_tooltip (display-only) still counts → flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_tooltip_only\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\teffect_tooltip = {\n",
        "\t\t\t\tcreate_wargoal = { target = MOR }\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "create_wargoal in effect_tooltip without hint flagged",
)

# 10g. war effect nested in a foreign country's scope (sponsored proxy war) →
# the owner does not go to war, so no hint is required → no flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = PER_arm_the_rebels\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\thidden_effect = {\n",
        "\t\t\t\tSAU = {\n",
        "\t\t\t\t\tdeclare_war_on = { target = QTF type = annex_everything }\n",
        "\t\t\t\t}\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "proxy war in a foreign scope not flagged",
)

# 10h. owner war restored via ROOT inside a foreign loop → still owner → flag
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_loop_then_owner\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\tevery_country = {\n",
        "\t\t\t\tROOT = {\n",
        "\t\t\t\t\tcreate_wargoal = { target = MOR }\n",
        "\t\t\t\t}\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "owner war reached via ROOT inside a foreign scope flagged",
)

# 10i. owner scoping into its OWN tag (PER_ focus, PER = { create_wargoal }) is
# still the owner going to war → flag when no hint
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = PER_alawites_in_syria\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\tPER = {\n",
        "\t\t\t\tcreate_wargoal = { type = annex_everything target = SYR }\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "owner self-scope create_wargoal without hint flagged",
)


# 10j. add_ai_strategy with type = declare_war (AI strategy value, not the
# declare_war_on effect) must NOT be flagged — it is not a war declaration.
assert_finds(
    _check_focus_missing_war_hint,
    [
        "\tfocus = {\n",
        "\t\tid = ALG_ai_strategy_only\n",
        "\t\tcompletion_reward = {\n",
        "\t\t\tadd_ai_strategy = { type = declare_war id = MOR value = 200 }\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "add_ai_strategy type = declare_war not flagged",
)


# 11. check_expr bad operand (inline operator/scalar instead of block form)

print("\n── check_expr bad operand ──")

# 11a. inline double-operator (greater_than > 6) → flag
assert_finds(
    _check_check_expr_bad_operand,
    [
        "check_expr = {\n",
        "\tvalue = my_var\n",
        "\tgreater_than > 6\n",
        "}\n",
    ],
    1,
    "check_expr greater_than > 6 flagged",
)

# 11b. bare scalar (greater_than = 6) → valid syntax, not flagged
assert_finds(
    _check_check_expr_bad_operand,
    [
        "check_expr = {\n",
        "\tvalue = my_var\n",
        "\tgreater_than = 6\n",
        "}\n",
    ],
    0,
    "check_expr greater_than = 6 (bare scalar) not flagged",
)

# 11c. less_than double-operator → flag
assert_finds(
    _check_check_expr_bad_operand,
    [
        "check_expr = {\n",
        "\tvalue = my_var\n",
        "\tless_than > 0.40\n",
        "}\n",
    ],
    1,
    "check_expr less_than > 0.40 flagged",
)

# 11d. correct block form, multi-line → no flag
assert_finds(
    _check_check_expr_bad_operand,
    [
        "check_expr = {\n",
        "\tvalue = my_var\n",
        "\tgreater_than = { value = 6 }\n",
        "}\n",
    ],
    0,
    "check_expr correct block form (multi-line) not flagged",
)

# 11e. correct block form, single line (real repo pattern) → no flag
assert_finds(
    _check_check_expr_bad_operand,
    [
        "check_expr = { value = global.EU_pop_ratio_yes greater_than = { value = 0.65 } }\n",
    ],
    0,
    "check_expr correct block form (single line) not flagged",
)

# 11e2. real repo bare-scalar pattern (resource storage) → no flag
assert_finds(
    _check_check_expr_bad_operand,
    [
        "\t\tlimit = { check_expr = { value = steel_in_storage equals = 0 } }\n",
    ],
    0,
    "check_expr bare-scalar 'equals = 0' (real repo pattern) not flagged",
)

# 11f. same bare-scalar shape outside any check_expr block → not flagged (scoping)
assert_finds(
    _check_check_expr_bad_operand,
    [
        "limit = {\n",
        "\tvalue = CPD_cost_raw_temp\n",
        "\tgreater_than = 20\n",
        "}\n",
    ],
    0,
    "bare-operand shape outside check_expr not flagged",
)


# 12. every_owned_controlled_state (nonexistent effect)

print("\n── every_owned_controlled_state ──")

# 12a. nonexistent effect → flag
assert_finds(
    _check_every_owned_controlled_state,
    [
        "\tevery_owned_controlled_state = {\n",
        "\t\tadd_stability = 0.01\n",
        "\t}\n",
    ],
    1,
    "every_owned_controlled_state flagged",
)

# 12b. correct effect → no flag
assert_finds(
    _check_every_owned_controlled_state,
    [
        "\tevery_controlled_state = {\n",
        "\t\tadd_stability = 0.01\n",
        "\t}\n",
    ],
    0,
    "every_controlled_state not flagged",
)

# 12c. inside a comment → no flag
assert_finds(
    _check_every_owned_controlled_state,
    [
        "\t# every_owned_controlled_state = { }\n",
    ],
    0,
    "every_owned_controlled_state in comment not flagged",
)


# 13. random_select_amount with a variable

print("\n── random_select_amount literal ──")

# 13a. global variable → flag
assert_finds(
    _check_random_select_amount_literal,
    [
        "\trandom_select_amount = global.my_count\n",
    ],
    1,
    "random_select_amount with global variable flagged",
)

# 13b. var: reference → flag
assert_finds(
    _check_random_select_amount_literal,
    [
        "\trandom_select_amount = var:foo\n",
    ],
    1,
    "random_select_amount with var: reference flagged",
)

# 13c. decimal → flag
assert_finds(
    _check_random_select_amount_literal,
    [
        "\trandom_select_amount = 2.5\n",
    ],
    1,
    "random_select_amount with decimal flagged",
)

# 13d. integer literal → no flag
assert_finds(
    _check_random_select_amount_literal,
    [
        "\trandom_select_amount = 3\n",
    ],
    0,
    "random_select_amount with integer literal not flagged",
)


# 15a. Focus log-id mismatch (Check C)

print("\n── Focus log-id mismatch ──")

# Basic copy-paste bug: log names a sibling focus's id -> flag
assert_finds(
    _check_focus_log_id,
    [
        "\tfocus = {\n",
        "\t\tid = ABK_our_place\n",
        "\t\tcompletion_reward = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus ABK_tourism1"\n',
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "focus log referencing a different focus id flagged",
)

# Log matches the enclosing focus's own id -> no flag
assert_finds(
    _check_focus_log_id,
    [
        "\tfocus = {\n",
        "\t\tid = ABK_our_place\n",
        "\t\tcompletion_reward = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus ABK_our_place"\n',
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "focus log matching its own id not flagged",
)

# Mismatch suppressed by complete_national_focus targeting the logged id in the
# same block -- this focus intentionally completes a sibling and logs it
assert_finds(
    _check_focus_log_id,
    [
        "\tfocus = {\n",
        "\t\tid = ABK_our_place\n",
        "\t\tcompletion_reward = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus ABK_tourism1"\n',
        "\t\t\tcomplete_national_focus = ABK_tourism1\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "mismatch suppressed by complete_national_focus in same block",
)

# Mismatch suppressed by unlock_national_focus targeting the logged id
assert_finds(
    _check_focus_log_id,
    [
        "\tfocus = {\n",
        "\t\tid = ABK_our_place\n",
        "\t\tcompletion_reward = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus ABK_tourism1"\n',
        "\t\t\tunlock_national_focus = ABK_tourism1\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "mismatch suppressed by unlock_national_focus in same block",
)

# shared_focus block also checked, lowercase "focus" + "executed" suffix style
assert_finds(
    _check_focus_log_id,
    [
        "shared_focus = {\n",
        "\tid = GCC_the_gcc\n",
        "\tcompletion_reward = {\n",
        '\t\tlog = "[GetDateText]: [This.GetName]: focus GCC_economic_union executed"\n',
        "\t}\n",
        "}\n",
    ],
    1,
    "shared_focus block with lowercase 'focus' log flagged",
)

# joint_focus block, log matches its own id -> no flag
assert_finds(
    _check_focus_log_id,
    [
        "\tjoint_focus = {\n",
        "\t\tid = NKR_economy_start\n",
        "\t\tcompletion_reward = {\n",
        '\t\t\tlog = "[GetDateText]: [This.GetName]: focus NKR_economy_start executed"\n',
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "joint_focus block matching its own id not flagged",
)


# 15b. Decision log-id mismatch (Check C)

print("\n── Decision log-id mismatch ──")

# Basic copy-paste bug: complete_effect log names a different decision's id
assert_finds(
    _check_decision_log_id,
    [
        "LAT_decisions_category = {\n",
        "\tLAT_reopen_the_vef_microchip_plant = {\n",
        "\t\tcomplete_effect = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision POR_expand_the_neves_corvo_mine"\n',
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "decision log referencing a different decision id flagged",
)

# "Decision remove <id>" keyword tolerance -- id matches -> no flag
assert_finds(
    _check_decision_log_id,
    [
        "UAR_decisions_category = {\n",
        "\tUAR_integrate_MAU = {\n",
        "\t\tremove_effect = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision remove UAR_integrate_MAU"\n',
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "'Decision remove <own id>' keyword tolerance not flagged",
)

# "Decision remove <id>" keyword tolerance -- id mismatched -> flag
assert_finds(
    _check_decision_log_id,
    [
        "NKO_decisions_category = {\n",
        "\tNKO_resource_extraction = {\n",
        "\t\tremove_effect = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision remove BNKO_resource_extraction"\n',
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "'Decision remove <wrong id>' (typo) still flagged",
)

# "Decision cancel effect <id>" double filler-word tolerance -- id matches
assert_finds(
    _check_decision_log_id,
    [
        "NATO_decisions_category = {\n",
        "\tNATO_CSTO_breach_mission = {\n",
        "\t\tcancel_effect = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision cancel effect NATO_CSTO_breach_mission"\n',
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "'Decision cancel effect <own id>' double-filler tolerance not flagged",
)

# Keyword-only log (nothing substantive follows) -- not flagged, no token to compare
assert_finds(
    _check_decision_log_id,
    [
        "SOME_decisions_category = {\n",
        "\tSOME_decision = {\n",
        "\t\tcomplete_effect = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision"\n',
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "keyword-only log with no id token not flagged",
)

# Log buried several if/limit levels deep still attributed to the correct
# enclosing decision, not a sibling in the same category
assert_finds(
    _check_decision_log_id,
    [
        "MIX_decisions_category = {\n",
        "\tMIX_first_decision = {\n",
        "\t\tcomplete_effect = {\n",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision MIX_first_decision"\n',
        "\t\t}\n",
        "\t}\n",
        "\tMIX_second_decision = {\n",
        "\t\tcomplete_effect = {\n",
        "\t\t\tif = {\n",
        "\t\t\t\tlimit = { always = yes }\n",
        "\t\t\t\tif = {\n",
        "\t\t\t\t\tlimit = { always = yes }\n",
        '\t\t\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision MIX_first_decision"\n',
        "\t\t\t\t}\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    1,
    "nested-if log correctly attributed to its own enclosing decision",
)


# 15c. Event log-id / option-letter mismatch (Check C)

print("\n── Event log-id / option-letter mismatch ──")

# Bare id + separate "Option <letter>" matching position -> no flag
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = HKG_contract.1\n",
        "\toption = {\n",
        "\t\tname = HKG_contract.1.a\n",
        '\t\tlog = "[GetDateText]: [Root.GetName]: Event HKG_contract.1 Option a"\n',
        "\t}\n",
        "}\n",
    ],
    0,
    "bare id + matching Option letter not flagged",
)

# Bare id + Option letter that doesn't match this option's own name -> flag
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = HKG_contract.1\n",
        "\toption = {\n",
        "\t\tname = HKG_contract.1.b\n",
        '\t\tlog = "[GetDateText]: [Root.GetName]: Event HKG_contract.1 Option a"\n',
        "\t}\n",
        "}\n",
    ],
    1,
    "Option letter not matching own name flagged",
)

# Event id itself mismatched -> flag
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = estonia.104\n",
        "\toption = {\n",
        "\t\tname = estonia.104.a\n",
        '\t\tlog = "[GetDateText]: [This.GetName]: event estonia.103.a executed"\n',
        "\t}\n",
        "}\n",
    ],
    1,
    "log referencing the wrong event id flagged",
)

# Full dotted name matching the option's own name (a/b/c style) -> no flag
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = satellites.2\n",
        "\toption = {\n",
        "\t\tname = satellites.2.a\n",
        '\t\tlog = "[GetDateText]: [Root.GetName]: event satellites.2.a"\n',
        "\t}\n",
        "}\n",
    ],
    0,
    "full dotted name matching own name not flagged",
)

# Numeric 'oN' suffix convention matching own name -> no flag
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = estonia.7\n",
        "\toption = {\n",
        "\t\tname = estonia.7.o2\n",
        '\t\tlog = "[GetDateText]: [This.GetName]: event estonia.7.o2 executed"\n',
        "\t}\n",
        "}\n",
    ],
    0,
    "numeric oN suffix matching own name not flagged",
)

# Numeric 'oN' suffix copy-pasted from a sibling option -> flag
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = estonia.7\n",
        "\toption = {\n",
        "\t\tname = estonia.7.o1\n",
        '\t\tlog = "[GetDateText]: [This.GetName]: event estonia.7.o1 executed"\n',
        "\t}\n",
        "\toption = {\n",
        "\t\tname = estonia.7.o2\n",
        '\t\tlog = "[GetDateText]: [This.GetName]: event estonia.7.o1 executed"\n',
        "\t}\n",
        "}\n",
    ],
    1,
    "oN suffix copy-pasted from a sibling option flagged",
)

# Non-sequential option lettering (skips a letter): log matches the option's
# own name -> not flagged even though the position-based letter would differ
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = singapore.101\n",
        "\toption = {\n",
        "\t\tname = singapore.101.c\n",
        '\t\tlog = "[GetDateText]: [THIS.GetName]: event singapore.101.c"\n',
        "\t}\n",
        "\toption = {\n",
        "\t\tname = singapore.101.e\n",
        '\t\tlog = "[GetDateText]: [THIS.GetName]: event singapore.101.e"\n',
        "\t}\n",
        "}\n",
    ],
    0,
    "non-sequential option lettering (c then e) not flagged",
)

# Nested country_event effect call (id + days, indented) is a scheduling call,
# not a definition -- must not be scanned as its own event block
assert_finds(
    _check_event_log_id,
    [
        "country_event = {\n",
        "\tid = china.68\n",
        "\toption = {\n",
        "\t\tname = china.68.a\n",
        '\t\tlog = "[GetDateText]: [Root.GetName]: event china.68.a"\n',
        "\t\thidden_effect = {\n",
        "\t\t\tcountry_event = {\n",
        "\t\t\t\tid = china.69\n",
        "\t\t\t\tdays = 35\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "nested country_event scheduling call not treated as a definition",
)


# 15d. hidden_trigger inside custom_trigger_tooltip (Check E1)

print("\n── hidden_trigger inside custom_trigger_tooltip ──")

# hidden_trigger at relative depth 1 -> flag
assert_finds(
    _check_hidden_trigger_in_ctt,
    [
        "\t\t\tcustom_trigger_tooltip = {\n",
        "\t\t\t\ttooltip = GER_had_civilwar_TT\n",
        "\t\t\t\thidden_trigger = {\n",
        "\t\t\t\t\thas_country_flag = GER_constitutional_government\n",
        "\t\t\t\t}\n",
        "\t\t\t}\n",
    ],
    1,
    "hidden_trigger at depth 1 inside custom_trigger_tooltip flagged",
)

# hidden_trigger nested under OR (relative depth 2) -> not flagged
assert_finds(
    _check_hidden_trigger_in_ctt,
    [
        "\tcustom_trigger_tooltip = {\n",
        "\t\ttooltip = GCC_jihadist_government_tt\n",
        "\t\tOR = {\n",
        "\t\t\thidden_trigger = {\n",
        "\t\t\t\thas_country_flag = test_flag\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "hidden_trigger nested under OR (depth 2) not flagged",
)

# hidden_trigger as a sibling AFTER custom_trigger_tooltip closes -> not flagged
assert_finds(
    _check_hidden_trigger_in_ctt,
    [
        "\t\t\tcustom_trigger_tooltip = {\n",
        "\t\t\t\ttooltip = ISR_judicial_pres_TT\n",
        "\t\t\t}\n",
        "\t\t\thidden_trigger = {\n",
        "\t\t\t\thas_country_flag = ISR_judicial\n",
        "\t\t\t}\n",
    ],
    0,
    "hidden_trigger as a sibling outside custom_trigger_tooltip not flagged",
)

# Quote-blanking regression: a log string containing a literal '{' inside the
# custom_trigger_tooltip block must not drift the depth count and mask the
# hidden_trigger that follows
assert_finds(
    _check_hidden_trigger_in_ctt,
    [
        "\tcustom_trigger_tooltip = {\n",
        "\t\ttooltip = TEST_TT\n",
        '\t\tlog = "test { brace"\n',
        "\t\thidden_trigger = {\n",
        "\t\t\thas_country_flag = test_flag\n",
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "stray brace inside a quoted log string doesn't mask the hidden_trigger",
)


# 17. Malformed country leader rotations (set_leader_TAG)

print("\n── Leader rotation (political_leaders) ──")


def _tier(counter, number, guard="", increment=1, retire=None, undo=None, tail=""):
    """One rotation tier: counter check, increment, kill, create, do_not_retire undo."""
    retire = counter if retire is None else retire
    undo = increment if undo is None else undo
    return [
        f"\t\tif = {{ limit = {{ check_variable = {{ {counter} = {number} }} {guard}}}\n",
        f"\t\t\tadd_to_variable = {{ {counter} = {increment} }}\n",
        "\t\t\thidden_effect = { kill_country_leader = yes }\n",
        "\t\t\tcreate_country_leader = {\n",
        f'\t\t\t\tname = "Leader {number}"\n',
        "\t\t\t\tideology = conservatism\n",
        "\t\t\t}\n",
        f"\t\t\tif = {{ limit = {{ has_country_flag = do_not_retire }} subtract_from_variable = {{ {retire} = {undo} }} }}\n",
        *tail,
        "\t\t}\n",
    ]


def _rotation(*tiers, flag="set_conservatism"):
    return [
        "set_leader_TST = {\n",
        f"\tif = {{ limit = {{ has_country_flag = {flag} }}\n",
        *[line for tier in tiers for line in tier],
        "\t}\n",
        "}\n",
    ]


_B_GUARD = "NOT = { check_variable = { b = 1 } } "

assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 0),
        _tier("conservatism_leader", 1, guard=_B_GUARD),
        _tier("conservatism_leader", 2, guard=_B_GUARD),
    ),
    0,
    "well-formed 3-tier rotation",
)

# Descending tiers self-guard (only one can match top-down) -- CAS/CSA/FIJ/USB idiom
assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 2),
        _tier("conservatism_leader", 1),
        _tier("conservatism_leader", 0),
    ),
    0,
    "descending tier order not flagged",
)

# b = 2 / b = 3 cascade past a terminal b = 1 -- SWE/UKR/ANT/SIN, deliberate
assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier(
            "conservatism_leader",
            0,
            tail=[
                "\t\t\tif = { limit = { date < 2016.1.2 } set_temp_variable = { b = 1 } }\n"
            ],
        ),
        _tier(
            "conservatism_leader",
            1,
            guard="NOT = { check_variable = { b = 2 } } ",
            tail=["\t\t\tset_temp_variable = { b = 2 }\n"],
        ),
    ),
    0,
    "b = 2 cascade guard not flagged",
)

assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 0),
        _tier("conservatism_leader", 1, guard=_B_GUARD, increment=2),
    ),
    1,
    "add_to_variable = 2 flagged (tier index used as the step)",
)

assert_finds(
    _check_leader_rotation,
    _rotation(_tier("conservatism_leader", 0, increment=0)),
    1,
    "add_to_variable = 0 flagged (counter never advances)",
)

assert_finds(
    _check_leader_rotation,
    _rotation(_tier("conservatism_leader", 0, undo=0)),
    1,
    "do_not_retire subtracting 0 flagged (no-op guard)",
)

assert_finds(
    _check_leader_rotation,
    _rotation(_tier("conservatism_leader", 0, retire="socialism_leader")),
    1,
    "do_not_retire subtracting another ideology's counter flagged",
)

assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 0),
        _tier("conservatism_leader", 2, guard=_B_GUARD),
    ),
    1,
    "tier gap flagged (no tier 1)",
)

assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 1),
        _tier("conservatism_leader", 2, guard=_B_GUARD),
    ),
    1,
    "rotation not starting at tier 0 flagged",
)

assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 0),
        _tier("conservatism_leader", 0, guard=_B_GUARD),
    ),
    1,
    "duplicate tier number flagged",
)

# ERI/ISR/CZE split a tier number on a second condition -- both stay reachable
assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 0, guard="has_country_flag = TST_coup "),
        _tier("conservatism_leader", 0, guard="NOT = { has_country_flag = TST_coup } "),
    ),
    0,
    "duplicate tier discriminated by a flag not flagged",
)

# JAP wraps its tiers in date containers; the same tier number under each is fine
assert_finds(
    _check_leader_rotation,
    [
        "set_leader_TST = {\n",
        "\tif = { limit = { has_country_flag = set_conservatism }\n",
        "\t\tif = { limit = { date < 2002.12.10 }\n",
        *_tier("conservatism_leader", 0),
        "\t\t}\n",
        "\t\tif = { limit = { date > 2002.12.10 }\n",
        *_tier("conservatism_leader", 0),
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "same tier number under two date containers not flagged",
)

# ITA-style lookup table: the counter is set elsewhere, tiers never advance it
assert_finds(
    _check_leader_rotation,
    [
        "set_leader_TST = {\n",
        "\tif = { limit = { has_country_flag = set_liberalism }\n",
        "\t\tif = { limit = { check_variable = { liberalism_leader = 1 } }\n",
        '\t\t\tcreate_country_leader = { name = "A" ideology = liberalism }\n',
        "\t\t}\n",
        "\t\tif = { limit = { check_variable = { liberalism_leader = 3 } }\n",
        '\t\t\tcreate_country_leader = { name = "B" ideology = liberalism }\n',
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ],
    0,
    "lookup-table branch with no increment not gap-checked",
)

assert_finds(
    _check_leader_rotation,
    [
        "set_leader_TST = {\n",
        "\tif = { limit = { has_country_flag = set_conservatism }\n",
        *_tier("conservatism_leader", 0),
        "\t}\n",
        "\telse_if = { limit = { has_country_flag = set_conservatism }\n",
        *_tier("conservatism_leader", 0),
        "\t}\n",
        "}\n",
    ],
    1,
    "duplicate set_conservatism branch flagged",
)

assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("conservatism_leader", 0),
        _tier("conservatism_leader", 1, guard="NOT = { check_variable = { b = 0 } } "),
    ),
    1,
    "NOT = { check_variable = { b = 0 } } flagged (always false)",
)

assert_finds(
    _check_leader_rotation,
    [
        "set_leader_TST = {\n",
        "\tif = { limit = { has_country_flag = set_conservatism }\n",
        *_tier("conservatism_leader", 0),
        "\t}\n",
        "\telse_if = { limit = { has_country_flag = set_Monarchist }\n",
        *_tier("conservatism_leader", 0),
        "\t}\n",
        "}\n",
    ],
    1,
    "branch counting with another ideology's counter flagged",
)

# CAS/PHI carry off-name counters (socalism_leader) that nothing else drives -- harmless
assert_finds(
    _check_leader_rotation,
    _rotation(
        _tier("socalism_leader", 0),
        _tier("socalism_leader", 1, guard=_B_GUARD),
        flag="set_socialism",
    ),
    0,
    "off-name counter owned by a single branch not flagged",
)


# Guardrails: confirm the three new checks stay silent on known-valid patterns

print("\n── Guardrails: no new-check false positives ──")

_GUARDRAIL_SNIPPETS = [
    ("num_of_factories > 5 (valid trigger)", ["\tnum_of_factories > 5\n"]),
    (
        "nested else inside if body",
        [
            "\tif = {\n",
            "\t\tlimit = { always = yes }\n",
            "\t\tif = {\n",
            "\t\t\tlimit = { always = yes }\n",
            "\t\t\tadd_stability = 0.01\n",
            "\t\t}\n",
            "\t\telse = {\n",
            "\t\t\tadd_stability = -0.01\n",
            "\t\t}\n",
            "\t}\n",
        ],
    ),
    (
        "mean_time_to_happen block",
        [
            "\tmean_time_to_happen = {\n",
            "\t\tdays = 10\n",
            "\t\tmodifier = {\n",
            "\t\t\tfactor = 2\n",
            "\t\t\tis_debug = yes\n",
            "\t\t}\n",
            "\t}\n",
        ],
    ),
]

for _label, _snippet in _GUARDRAIL_SNIPPETS:
    for _check_fn in (
        _check_check_expr_bad_operand,
        _check_every_owned_controlled_state,
        _check_random_select_amount_literal,
    ):
        assert_finds(_check_fn, _snippet, 0, f"{_check_fn.__name__} on {_label}")


# Hyphenated ids: log-id checks must see the full token, not the \w+ prefix

_HYPHEN_FOCUS_OK = [
    "\tfocus = {\n",
    "\t\tid = TST_austria-este\n",
    "\t\tcompletion_reward = {\n",
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus TST_austria-este"\n',
    "\t\t}\n",
    "\t}\n",
]
_HYPHEN_FOCUS_BAD = [
    "\tfocus = {\n",
    "\t\tid = TST_austria-este\n",
    "\t\tcompletion_reward = {\n",
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus TST_austria-lorraine"\n',
    "\t\t}\n",
    "\t}\n",
]
assert_finds(
    _check_focus_log_id, _HYPHEN_FOCUS_OK, 0, "hyphenated focus id, log matches"
)
assert_finds(
    _check_focus_log_id, _HYPHEN_FOCUS_BAD, 1, "hyphenated focus id, log mismatch"
)

_HYPHEN_DECISION_OK = [
    "category_test = {\n",
    "\tCommunist-State_invite = {\n",
    "\t\tcomplete_effect = {\n",
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision Communist-State_invite"\n',
    "\t\t}\n",
    "\t}\n",
    "}\n",
]
_HYPHEN_DECISION_BAD = [
    "category_test = {\n",
    "\tCommunist-State_invite = {\n",
    "\t\tcomplete_effect = {\n",
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision Communist-State_remove"\n',
    "\t\t}\n",
    "\t}\n",
    "}\n",
]
assert_finds(
    _check_decision_log_id,
    _HYPHEN_DECISION_OK,
    0,
    "hyphenated decision id, log matches",
)
assert_finds(
    _check_decision_log_id,
    _HYPHEN_DECISION_BAD,
    1,
    "hyphenated decision id, log mismatch",
)

# AND directly under NOT is the sanctioned NAND disambiguation -- never redundant

from cleanup_or import find_redundant_and_blocks, simplify_and_block

_AND_UNDER_NOT = [
    "\ttrigger = {\n",
    "\t\tNOT = {\n",
    "\t\t\tAND = {\n",
    "\t\t\t\toriginal_tag = AUS\n",
    "\t\t\t\thas_war = yes\n",
    "\t\t\t}\n",
    "\t\t}\n",
    "\t}\n",
]
assert_finds(find_redundant_and_blocks, _AND_UNDER_NOT, 0, "AND under NOT not flagged")
_simplified = simplify_and_block(_AND_UNDER_NOT)
if _simplified == _AND_UNDER_NOT:
    passed += 1
    print("  PASS  simplify_and_block keeps AND under NOT")
else:
    failed += 1
    print("  FAIL  simplify_and_block keeps AND under NOT")

_BARE_AND = [
    "\ttrigger = {\n",
    "\t\tAND = {\n",
    "\t\t\thas_war = yes\n",
    "\t\t}\n",
    "\t}\n",
]
assert_finds(find_redundant_and_blocks, _BARE_AND, 1, "bare AND still flagged")


# 18. country_exists scope contradiction — NOT = { country_exists = TAG }
# alongside TAG = { ... } in the same AND block is always false (scope fails
# when TAG is absent, NOT is only true then) -> dead bypass/gate.

print("\n── country_exists scope contradiction ──")

# Dead bypass: NOT = { country_exists = CAN } + CAN = { ... } siblings.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tbypass = {\n",
        "\t\tCAN = { is_subject_of = USA }\n",
        "\t\tNOT = { country_exists = CAN }\n",
        "\t}\n",
    ],
    1,
    "NOT country_exists + TAG scope switch in AND bypass flagged",
)

# Same bug, NOT block first then scope switch (order-independent).
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tavailable = {\n",
        "\t\tNOT = { country_exists = CAN }\n",
        "\t\tCAN = { has_government = democratic }\n",
        "\t}\n",
    ],
    1,
    "order-independent: NOT then scope switch flagged",
)

# Multi-line NOT block.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tbypass = {\n",
        "\t\tCAN = { is_subject_of = USA }\n",
        "\t\tNOT = {\n",
        "\t\t\tcountry_exists = CAN\n",
        "\t\t}\n",
        "\t}\n",
    ],
    1,
    "multi-line NOT = { country_exists = CAN } flagged",
)

# OR-wrapped is the correct form -> not flagged.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tbypass = {\n",
        "\t\tOR = {\n",
        "\t\t\tNOT = { country_exists = CAN }\n",
        "\t\t\tCAN = { is_subject_of = USA }\n",
        "\t\t}\n",
        "\t}\n",
    ],
    0,
    "OR-wrapped (intended form) not flagged",
)

# Positive guard + scope switch is the correct idiom -> not flagged.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tavailable = {\n",
        "\t\tcountry_exists = CAN\n",
        "\t\tCAN = { has_government = democratic }\n",
        "\t}\n",
    ],
    0,
    "positive country_exists + scope switch (guard idiom) not flagged",
)

# NOT = { TAG = { ... } } (NOT wrapping a scope switch, not country_exists) is
# a different construct and must NOT be flagged.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tlimit = {\n",
        "\t\tJOR = { influence_higher_10 = yes }\n",
        "\t\tNOT = { JOR = { influence_higher_20 = yes } }\n",
        "\t}\n",
    ],
    0,
    "NOT wrapping a scope switch (not country_exists) not flagged",
)

# Multi-statement NOT is a NAND (not both at once), satisfiable with the tag
# alive -> not flagged (real case: IRQ_reintegration_of_kurdistan).
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tavailable = {\n",
        "\t\tNOT = {\n",
        "\t\t\tcountry_exists = KUR\n",
        "\t\t\tcountry_exists = PUK\n",
        "\t\t}\n",
        "\t\tKUR = { is_subject_of = IRQ }\n",
        "\t}\n",
    ],
    0,
    "multi-child NOT (NAND) not flagged",
)

# NOT mixing country_exists with another trigger is also a NAND -> not flagged.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tbypass = {\n",
        "\t\tNOT = {\n",
        "\t\t\thas_war_with = AFG\n",
        "\t\t\tcountry_exists = AFG\n",
        "\t\t}\n",
        "\t\tAFG = { is_subject = yes }\n",
        "\t}\n",
    ],
    0,
    "NOT mixing country_exists with another trigger (NAND) not flagged",
)

# Flags and variables persist on dead/unreleased tags, so a scope checking only
# those is satisfiable next to NOT country_exists -> not flagged (real case:
# SubjectRussia separatism tracking on not-yet-released subjects).
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tlimit = {\n",
        "\t\tNOT = { country_exists = CHE }\n",
        "\t\tCHE = { NOT = { has_country_flag = SUB_subject_rebellion_flag } }\n",
        "\t}\n",
    ],
    0,
    "scope checking only flags on a dead tag not flagged",
)

assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tvisible = {\n",
        "\t\tNOT = { country_exists = PTR }\n",
        "\t\tPTR = { check_variable = { separatism > 10 } }\n",
        "\t}\n",
    ],
    0,
    "scope checking only variables on a dead tag not flagged",
)

# A live-country property (opinion) cannot hold for an absent tag -> flagged
# even when mixed with flag checks.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tcancel = {\n",
        "\t\tBLZ = { has_opinion = { target = CAN value < 24 } }\n",
        "\t\tNOT = { country_exists = BLZ }\n",
        "\t}\n",
    ],
    1,
    "scope with live-country trigger (has_opinion) still flagged",
)

# Different tags in the same AND block -> no contradiction.
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tbypass = {\n",
        "\t\tCAN = { is_subject_of = USA }\n",
        "\t\tNOT = { country_exists = MEX }\n",
        "\t}\n",
    ],
    0,
    "different tags in AND block not flagged",
)

# A stray } in a log string inside the scope block must not desync the frame
# stack and drop the finding (quote-blanking, same as the embargo guard).
assert_finds(
    _check_country_exists_scope_contradiction,
    [
        "\tbypass = {\n",
        "\t\tCAN = {\n",
        '\t\t\tlog = "closing } here"\n',
        "\t\t\tis_subject_of = USA\n",
        "\t\t}\n",
        "\t\tNOT = { country_exists = CAN }\n",
        "\t}\n",
    ],
    1,
    "stray } in a log string inside the scope block still flagged",
)


def assert_eq(actual, expected, label):
    global passed, failed
    if actual == expected:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}: expected {expected!r}, got {actual!r}")


def _isx_nation_matches(lines):
    return [
        (i + 1, line) for i, line in enumerate(lines) if _RE_IS_X_NATION.search(line)
    ]


def _run_check_file(rel_path, text):
    root = tempfile.mkdtemp()
    fp = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        return check_file(fp)
    finally:
        shutil.rmtree(root, ignore_errors=True)


# 19. single-valued-trigger contradiction, including single-line forms

print("\n── single-valued trigger contradiction ──")

assert_finds(
    _check_mutually_exclusive_contradictions,
    ["\tNOT = { tag = USA tag = CHI }\n"],
    1,
    "single-line NOT with two tag values flagged",
)
assert_finds(
    _check_mutually_exclusive_contradictions,
    ["\tlimit = { has_government = communism has_government = nationalist }\n"],
    1,
    "single-line AND with two has_government values flagged",
)
assert_finds(
    _check_mutually_exclusive_contradictions,
    ["\tOR = { tag = USA tag = CHI }\n"],
    0,
    "single-line OR with two tag values not flagged",
)
assert_finds(
    _check_mutually_exclusive_contradictions,
    [
        "\tNOT = {\n",
        "\t\ttag = USA\n",
        "\t\ttag = CHI\n",
        "\t}\n",
    ],
    1,
    "multi-line NOT contradiction still flagged (regression)",
)
assert_finds(
    _check_mutually_exclusive_contradictions,
    ["\tlimit = { has_government = communism }\n"],
    0,
    "single value not flagged",
)
assert_finds(
    _check_mutually_exclusive_contradictions,
    ['\tlog = "NOT = { tag = USA tag = CHI }"\n'],
    0,
    "contradiction shape inside a quoted string not flagged",
)


# 20. embargo DLC guard must not leak an inline guard to the parent frame

print("\n── embargo DLC guard inline-leak ──")

assert_finds(
    _check_embargo_dlc_guard,
    [
        "ISR = {\n",
        '\tif = { limit = { has_dlc = "By Blood Alone" } }\n',
        "\tsend_embargo = TAG\n",
        "}\n",
    ],
    1,
    "inline guard does not cover a sibling embargo outside the if",
)
assert_finds(
    _check_embargo_dlc_guard,
    ['\tif = { limit = { has_dlc = "By Blood Alone" } send_embargo = TAG }\n'],
    0,
    "single-line guard covers a same-line inline embargo",
)
assert_finds(
    _check_embargo_dlc_guard,
    [
        "option = {\n",
        '\ttrigger = { has_dlc = "By Blood Alone" }\n',
        "\tsend_embargo = FROM\n",
        "}\n",
    ],
    0,
    "trigger-gated has_dlc covers a sibling embargo in the same option",
)


# 21. is_X_nation regex matches multi-segment nation names

print("\n── is_X_nation multi-segment names ──")

assert_finds(
    _isx_nation_matches,
    ["\tis_horn_of_africa_nation = yes\n"],
    1,
    "multi-segment is_horn_of_africa_nation matched",
)
assert_finds(
    _isx_nation_matches,
    ["\tis_arab_nation = yes\n"],
    1,
    "single-segment is_arab_nation matched",
)
assert_finds(
    _isx_nation_matches,
    ["\tis_nation = yes\n"],
    1,
    "bare is_nation matched",
)
assert_finds(
    _isx_nation_matches,
    ["\thas_war = yes\n"],
    0,
    "non-nation trigger not matched",
)


# 22. _get_block ignores braces inside quoted strings

print("\n── _get_block quote-blanking ──")

_GET_BLOCK_LINES = [
    "foo = {\n",
    '\tlog = "a { brace in a string"\n',
    "\tbar = yes\n",
    "}\n",
    "next = yes\n",
]
_block, _next = _get_block(_GET_BLOCK_LINES, 0)
assert_eq(_next, 4, "_get_block stops at the real closing brace (quoted { ignored)")
assert_eq(
    "next = yes\n" not in _block,
    True,
    "_get_block does not swallow past the block on a quoted brace",
)


# 23. ideas brace tracking ignores braces inside comments (check_file)

print("\n── ideas comment-brace tracking ──")

_IDEAS_WITH_COMMENT_BRACE = (
    "ideas = {\n"
    "\tcountry = {\n"
    "\t\tFOO_idea = {\n"
    "\t\t\t# this comment has an extra { brace\n"
    "\t\t\tallowed = { tag = FOO }\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)
_ideas_issues = _run_check_file(
    os.path.join("common", "ideas", "probe.txt"), _IDEAS_WITH_COMMENT_BRACE
)
assert_eq(
    any("civil war split-offs" in msg for _fp, _ln, msg in _ideas_issues),
    True,
    "allowed = { tag } still caught after a comment brace (no desync)",
)

_IDEAS_ORIGINAL_TAG = (
    "ideas = {\n"
    "\tcountry = {\n"
    "\t\tFOO_idea = {\n"
    "\t\t\t# comment with { brace\n"
    "\t\t\tallowed = { original_tag = FOO }\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)
_ideas_ok = _run_check_file(
    os.path.join("common", "ideas", "probe2.txt"), _IDEAS_ORIGINAL_TAG
)
assert_eq(
    any("civil war split-offs" in msg for _fp, _ln, msg in _ideas_ok),
    False,
    "correct original_tag idea not flagged",
)


# 24. division check does not fire inside quoted strings (check_file)

print("\n── division check quote-blanking ──")

_DIV_ISSUES = _run_check_file(
    "probe.txt",
    "effect = {\n"
    "\tset_variable = { x = whatever / 100 }\n"
    '\tlog = "progress 50/100 complete"\n'
    "}\n",
)
_div_lines = [ln for _fp, ln, msg in _DIV_ISSUES if "multiplication instead" in msg]
assert_eq(
    _div_lines, [2], "division flagged only for the real / 100, not the quoted one"
)


# 25. mutex-trigger regex is built from _MUTUALLY_EXCLUSIVE_TRIGGERS, so every
# member of the set (not just tag / has_government) is covered.

print("\n── single-valued trigger regex from set ──")

assert_finds(
    _check_mutually_exclusive_contradictions,
    [
        "\tNOT = { has_country_leader_ideology = communism"
        " has_country_leader_ideology = fascism }\n"
    ],
    1,
    "has_country_leader_ideology contradiction covered by set-driven regex",
)
assert_finds(
    _check_mutually_exclusive_contradictions,
    ["\tNOT = { original_tag = USA tag = CHI }\n"],
    0,
    "original_tag and tag are different triggers -- not a single-trigger contradiction",
)


# 26. embargo guard stack is quote-aware: a stray brace in a log/loc string must
# not desync the if/guard frames (a stray } previously popped the guard frame).

print("\n── embargo guard quote-blanking ──")

assert_finds(
    _check_embargo_dlc_guard,
    [
        "if = {\n",
        '\tlimit = { has_dlc = "By Blood Alone" }\n',
        '\tlog = "closing } here"\n',
        "\tsend_embargo = TAG\n",
        "}\n",
    ],
    0,
    "stray } in a log string does not pop the BBA guard frame",
)
assert_finds(
    _check_embargo_dlc_guard,
    [
        "effect = {\n",
        '\tlog = "stray { brace"\n',
        "\tsend_embargo = TAG\n",
        "}\n",
    ],
    1,
    "stray { in a log string does not hide an ungated embargo",
)


# 27. _files_need_global_refs pre-scan gate matches the whitespace-flexible
#     _RE_AVAILABLE_ALWAYS_NO downstream check, so a spaceless always=no is not
#     skipped (which would surface as a false-positive unreachable-focus finding)

print("\n── _files_need_global_refs whitespace-flexible gate ──")


def _needs_global_refs(rel_path, text):
    root = tempfile.mkdtemp()
    fp = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        return _files_need_global_refs([fp])
    finally:
        shutil.rmtree(root, ignore_errors=True)


assert_eq(
    _needs_global_refs(
        "common/national_focus/test.txt",
        "focus = {\n\tavailable = { always = no }\n}\n",
    ),
    True,
    "canonical available = { always = no } forces the global-refs scan",
)
assert_eq(
    _needs_global_refs(
        "common/national_focus/test.txt",
        "focus = {\n\tavailable={always=no}\n}\n",
    ),
    True,
    "spaceless available={always=no} still forces the global-refs scan",
)
assert_eq(
    _needs_global_refs(
        "common/national_focus/test.txt",
        "focus = {\n\tavailable = { has_war = yes }\n}\n",
    ),
    False,
    "focus without available always-no does not force the scan",
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
