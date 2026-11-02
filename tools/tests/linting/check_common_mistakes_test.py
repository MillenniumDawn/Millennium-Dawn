"""Tests for the `_check_*` scanners in check_common_mistakes.py.

_COUNT_CASES holds one table per check: label, expected finding count, the
script lines, and any extra arguments. _EXACT_CASES pins the exact findings of
one flagged input per check. The tests after them cover the scanner helpers
and the rules a count cannot show. check_file, main() and the common/ readers
are in check_common_mistakes_entrypoints_test.py.
"""

from collections.abc import Callable

import check_common_mistakes as common_mistakes
import pytest
from check_common_mistakes import (
    _RE_IS_X_NATION,
    _ai_zero_modifier_conditions,
    _check_active_decision_defined,
    _check_add_to_faction_country,
    _check_ai_daily_flag_cache,
    _check_any_country_member_array,
    _check_bare_statement_token,
    _check_building_missing_province,
    _check_check_expr_bad_operand,
    _check_check_var_ge_le,
    _check_consecutive_scope_blocks,
    _check_country_exists_scope_contradiction,
    _check_create_faction_deprecated,
    _check_daily_mastery_index,
    _check_decision_allowed_dynamic,
    _check_decision_available_always_no,
    _check_decision_log_id,
    _check_divide_variable_zero_guard,
    _check_duplicate_add_to_variable,
    _check_else_with_limit,
    _check_embargo_dlc_guard,
    _check_empty_log_only_blocks,
    _check_equipment_bonus,
    _check_equipment_type_defined,
    _check_event_ai_historical_bankruptcy_fallback,
    _check_event_log_id,
    _check_every_country_member_array,
    _check_every_owned_controlled_state,
    _check_focus_available_always_no,
    _check_focus_log_id,
    _check_focus_missing_war_hint,
    _check_has_idea_mutex_in_not_block,
    _check_has_opinion_modifier_block,
    _check_hidden_trigger_in_ctt,
    _check_influence_setter_scope,
    _check_invalid_is_at_war,
    _check_is_x_nation_runtime,
    _check_leader_rotation,
    _check_log_nested_quote,
    _check_modifier_ref_defined,
    _check_mutually_exclusive_contradictions,
    _check_nested_province_block,
    _check_nor_block,
    _check_on_add_array_symmetry,
    _check_random_select_amount_literal,
    _check_redundant_avoid_starting_wars,
    _check_retired_ideology_flags,
    _check_shadowed_branches,
    _check_stat_effect_magnitude,
    _check_tautological_or,
    _check_var_index_shorthand,
    _check_while_loop_max_iterations,
    _check_wrong_stat_trigger,
    _get_block,
    _negates_bankruptcy_mission,
)
from cleanup_or import find_redundant_and_blocks, find_single_condition_or_blocks
from shared.suite import write_under_str

_WAR_CHAIN_EVENTS = {
    "alg_war.1": (
        "country_event = {\n"
        "\tid = alg_war.1\n"
        "\toption = {\n"
        "\t\tdeclare_war_on = { target = MOR type = annex_everything }\n"
        "\t}\n"
        "}\n"
    ),
    "alg_chain.1": (
        "country_event = {\n"
        "\tid = alg_chain.1\n"
        "\toption = {\n"
        "\t\tadd_political_power = 50\n"
        "\t\tcountry_event = alg_chain.2\n"
        "\t}\n"
        "}\n"
    ),
    "alg_chain.2": (
        "country_event = {\n"
        "\tid = alg_chain.2\n"
        "\toption = {\n"
        "\t\tALG = {\n"
        "\t\t\tcreate_wargoal = { type = annex_everything target = TUN }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    ),
    "alg_peace.1": (
        "country_event = {\n"
        "\tid = alg_peace.1\n"
        "\toption = {\n"
        "\t\tadd_political_power = 50\n"
        "\t}\n"
        "}\n"
    ),
}

_chain_lines = [
    "\tfocus = {\n",
    "\t\tid = ALG_escalate\n",
    "\t\tcompletion_reward = {\n",
    "\t\t\tcountry_event = { id = alg_chain.1 days = 1 }\n",
    "\t\t}\n",
    "\t}\n",
]


def _chain(first, second):
    """An if/else_if pair whose limits hold `first` and `second`."""
    return [
        "effect = {\n",
        f"\tif = {{ limit = {{ {first} }} add_stability = 0.1 }}\n",
        f"\telse_if = {{ limit = {{ {second} }} add_stability = 0.2 }}\n",
        "}\n",
    ]


def _tier(counter, number, guard="", increment=1, retire=None, undo=None, tail=None):
    """One rotation tier: counter check, increment, kill, create, do_not_retire undo."""
    retire = counter if retire is None else retire
    undo = increment if undo is None else undo
    tail = [] if tail is None else tail
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


def _rotation(*tiers, slot=1):
    return [
        "set_leader_TST = {\n",
        f"\tif = {{ limit = {{ check_variable = {{ ruling_party = {slot} }} }}\n",
        *[line for tier in tiers for line in tier],
        "\t}\n",
        "}\n",
    ]


_B_GUARD = "NOT = { check_variable = { b = 1 } } "

_CUB_DAILY_CACHE = [
    "on_actions = {\n",
    "\ton_daily_CUB = {\n",
    "\t\teffect = {\n",
    "\t\t\tif = {\n",
    "\t\t\t\tlimit = { is_ai = yes }\n",
    "\t\t\t\tif = {\n",
    "\t\t\t\t\tlimit = { CUB_ai_can_attack_hai_uncached_trigger = yes }\n",
    "\t\t\t\t\tset_country_flag = CUB_ai_can_attack_hai\n",
    "\t\t\t\t}\n",
    "\t\t\t\telse = { clr_country_flag = CUB_ai_can_attack_hai }\n",
    "\t\t\t}\n",
    "\t\t}\n",
    "\t}\n",
    "}\n",
]


def _logged_decision(text):
    """TST_decision whose complete_effect carries one log line."""
    return [
        "TST_category = {\n",
        "\tTST_decision = {\n",
        "\t\tcomplete_effect = {\n",
        f'\t\t\tlog = "{text}"\n',
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ]


def _war_brake(ratio, strategy="avoid_starting_wars value = -200"):
    return [
        "CUB_avoid_starting_wars = {\n",
        "\tallowed = { original_tag = CUB }\n",
        "\tenable = {\n",
        "\t\thas_war = yes\n",
        f"\t\tenemies_strength_ratio > {ratio}\n",
        "\t}\n",
        "\tabort_when_not_enabled = yes\n",
        "\n",
        f"\tai_strategy = {{ type = {strategy} }}\n",
        "}\n",
    ]


_COUNT_CASES: dict[
    Callable[..., list[tuple[int, str]]],
    list[tuple[str, int, list[str], *tuple[object, ...]]],
] = {
    _check_consecutive_scope_blocks: [
        (
            "blocks inside OR not flagged",
            0,
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
        ),
        (
            "blocks inside NOT not flagged",
            0,
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
        ),
        (
            "gap > 4 lines not flagged",
            0,
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
        ),
        (
            "consecutive FROM blocks flagged",
            1,
            [
                "\t\tFROM = {\n",
                "\t\t\tadd_stability = 0.05\n",
                "\t\t}\n",
                "\t\tFROM = {\n",
                "\t\t\tadd_war_support = 0.05\n",
                "\t\t}\n",
            ],
        ),
        (
            "a non-blank line between blocks blocks the merge hint",
            0,
            [
                "\t\tSOV = {\n",
                "\t\t\tadd_stability = 0.05\n",
                "\t\t}\n",
                "\t\t\tadd_war_support = 0.05\n",
                "\t\tSOV = {\n",
                "\t\t\tadd_stability = 0.05\n",
                "\t\t}\n",
            ],
        ),
        ("stray closing brace absorbed", 0, ["}\n"]),
    ],
    _check_embargo_dlc_guard: [
        (
            "inline guard does not cover a sibling embargo outside the if",
            1,
            [
                "ISR = {\n",
                '\tif = { limit = { has_dlc = "By Blood Alone" } }\n',
                "\tsend_embargo = TAG\n",
                "}\n",
            ],
        ),
        (
            "single-line guard covers a same-line inline embargo",
            0,
            ['\tif = { limit = { has_dlc = "By Blood Alone" } send_embargo = TAG }\n'],
        ),
        (
            "trigger-gated has_dlc covers a sibling embargo in the same option",
            0,
            [
                "option = {\n",
                '\ttrigger = { has_dlc = "By Blood Alone" }\n',
                "\tsend_embargo = FROM\n",
                "}\n",
            ],
        ),
        (
            "stray closing brace still leaves an embargo unguarded",
            1,
            ["}\n", "\tsend_embargo = { target = USA }\n"],
        ),
        (
            "a DLC check outside every block guards nothing",
            1,
            ['has_dlc = "By Blood Alone"\n', "send_embargo = { target = USA }\n"],
        ),
        (
            "a gateless DLC check guards its own block",
            0,
            [
                "\tsome_block = {\n",
                '\t\thas_dlc = "By Blood Alone"\n',
                "\t\tsend_embargo = { target = USA }\n",
                "\t}\n",
            ],
        ),
    ],
    _check_divide_variable_zero_guard: [
        (
            "literal divisor not flagged",
            0,
            [
                "\tdivide_variable = { cost = 100 }\n",
            ],
        ),
        (
            "check_variable guard suppresses flag",
            0,
            [
                "\tif = {\n",
                "\t\tlimit = { check_variable = { global.count > 0 } }\n",
                "\t\tdivide_variable = { global.avg = global.count }\n",
                "\t}\n",
            ],
        ),
        (
            "clamp_variable guard suppresses flag",
            0,
            [
                "\tclamp_variable = { var = divisor min = 0.001 }\n",
                "\tdivide_variable = { result = divisor }\n",
            ],
        ),
        (
            "clamp_temp_variable guard suppresses flag",
            0,
            [
                "\tclamp_temp_variable = { var = tmp_div min = 0.1 }\n",
                "\tdivide_variable = { result = tmp_div }\n",
            ],
        ),
        (
            "clamp with min=0 still flagged",
            1,
            [
                "\tclamp_variable = { var = divisor min = 0 }\n",
                "\tdivide_variable = { result = divisor }\n",
            ],
        ),
        (
            "else-block after if { var = 0 } suppresses flag",
            0,
            [
                "\tif = { limit = { check_variable = { workers = 0 } }\n",
                "\t\tset_variable = { fulfillment = 1 }\n",
                "\t}\n",
                "\telse = {\n",
                "\t\tdivide_variable = { fulfillment = workers }\n",
                "\t}\n",
            ],
        ),
        (
            "set_variable with non-zero literal suppresses flag",
            0,
            [
                "\tset_variable = { SPR_regulare_cap_ratio = 2000 }\n",
                "\tdivide_variable = { SPR_regulare_cap = SPR_regulare_cap_ratio }\n",
            ],
        ),
        (
            "set_variable with zero still flagged",
            1,
            [
                "\tset_variable = { my_divisor = 0 }\n",
                "\tdivide_variable = { result = my_divisor }\n",
            ],
        ),
        (
            "allowlisted divisor suppresses flag",
            0,
            [
                "\tdivide_variable = { global.target_civ_count = global.UN_general_assembly^num }\n",
            ],
        ),
        (
            "a malformed clamp minimum is not a zero guard",
            1,
            [
                "\tclamp_variable = { var = my_var min = . max = 5 }\n",
                "\tdivide_variable = { total = my_var }\n",
            ],
        ),
        (
            "a malformed set_variable literal is not an initialisation",
            1,
            [
                "\tset_variable = { my_var = .. }\n",
                "\tdivide_variable = { total = my_var }\n",
            ],
        ),
    ],
    _check_duplicate_add_to_variable: [
        (
            "duplicate add_to_temp_variable flagged",
            1,
            [
                "\tadd_to_temp_variable = { tmp = 10 }\n",
                "\tadd_to_temp_variable = { tmp = 10 }\n",
            ],
        ),
        (
            "blank line between duplicates not flagged",
            0,
            [
                "\tadd_to_variable = { score = 5 }\n",
                "\n",
                "\tadd_to_variable = { score = 5 }\n",
            ],
        ),
    ],
    _check_every_country_member_array: [
        (
            "has_idea inside NOT block not flagged",
            0,
            [
                "\tevery_country = {\n",
                "\t\tlimit = {\n",
                "\t\t\tNOT = { has_idea = NATO_member }\n",
                "\t\t}\n",
                "\t\tadd_stability = 0.05\n",
                "\t}\n",
            ],
        ),
        (
            "OR with non-array idea suppresses flag",
            0,
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
        ),
        (
            "has_idea inside OVERLORD not flagged",
            0,
            [
                "\tevery_country = {\n",
                "\t\tlimit = {\n",
                "\t\t\tOVERLORD = { has_idea = NATO_member }\n",
                "\t\t}\n",
                "\t\tadd_stability = 0.05\n",
                "\t}\n",
            ],
        ),
        (
            "has_idea in body if-block (not limit) not flagged",
            0,
            [
                "\tevery_country = {\n",
                "\t\tsetup_employment_variables = yes\n",
                "\t\tif = { limit = { has_idea = NATO_member }\n",
                "\t\t\tadd_to_tech_sharing_group = NATO_Tech_Share\n",
                "\t\t}\n",
                "\t}\n",
            ],
        ),
        (
            "for_each_scope_loop not flagged",
            0,
            [
                "\tfor_each_scope_loop = {\n",
                "\t\tarray = global.nato_members\n",
                "\t\tadd_stability = 0.05\n",
                "\t}\n",
            ],
        ),
        (
            "OR of LoAS variants flagged once (same array)",
            1,
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
        ),
        (
            "OR spanning two arrays flagged once with split advice",
            1,
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
        ),
        (
            "display-only country loops are exempt",
            0,
            [
                "every_country = {\n",
                "\tlimit = { has_idea = NATO_member }\n",
                "\tdisplay_individual_scopes = yes\n",
                "}\n",
            ],
        ),
    ],
    _check_any_country_member_array: [
        (
            "any_other_country with NATO_member flagged",
            1,
            [
                "\tany_other_country = {\n",
                "\t\thas_idea = NATO_member\n",
                "\t}\n",
            ],
        ),
        (
            "any_country with NOT-wrapped idea not flagged",
            0,
            [
                "\tany_country = {\n",
                "\t\tNOT = { has_idea = NATO_member }\n",
                "\t\thas_war_with = ROOT\n",
                "\t}\n",
            ],
        ),
        (
            "any_country OR with non-array idea not flagged",
            0,
            [
                "\tany_country = {\n",
                "\t\tOR = {\n",
                "\t\t\thas_idea = EU_member\n",
                "\t\t\thas_idea = the_military\n",
                "\t\t}\n",
                "\t}\n",
            ],
        ),
        (
            "any_of_scopes not flagged",
            0,
            [
                "\tany_of_scopes = {\n",
                "\t\tarray = global.EU_member\n",
                "\t\thas_war_with = ROOT\n",
                "\t}\n",
            ],
        ),
    ],
    _check_on_add_array_symmetry: [
        (
            "on_add without matching on_remove removal flagged",
            1,
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
        ),
        (
            "remove-only hooks not flagged",
            0,
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
        ),
        (
            "sibling idea removing the WRONG array flagged once",
            1,
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
        ),
    ],
    _check_has_idea_mutex_in_not_block: [
        (
            "single intervention idea in NOT not flagged",
            0,
            [
                "trigger = {\n",
                "\tNOT = { has_idea = intervention_isolation }\n",
                "}\n",
            ],
        ),
        (
            "ideas from different groups not flagged",
            0,
            [
                "trigger = {\n",
                "\tNOT = {\n",
                "\t\thas_idea = intervention_isolation\n",
                "\t\thas_idea = NATO_member\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "single-line AND with two intervention doctrines flagged",
            1,
            [
                "modifier = { AND = { has_idea = intervention_isolation has_idea = intervention_limited_interventionism } }\n",
            ],
        ),
        ("stray closing brace absorbed", 0, ["}\n"]),
    ],
    _check_influence_setter_scope: [
        (
            "setter in loop with call outside loop flagged",
            1,
            [
                "\trandom_other_country = {\n",
                "\t\tset_temp_variable = { percent_change = 3 }\n",
                "\t\tset_temp_variable = { influence_target = PREV.id }\n",
                "\t}\n",
                "\tchange_influence_percentage = yes\n",
            ],
        ),
        (
            "setter and call both inside loop not flagged",
            0,
            [
                "\trandom_other_country = {\n",
                "\t\tset_temp_variable = { percent_change = 3 }\n",
                "\t\tchange_influence_percentage = yes\n",
                "\t}\n",
            ],
        ),
        (
            "no setter present not flagged",
            0,
            [
                "\tchange_influence_percentage = yes\n",
            ],
        ),
    ],
    _check_check_var_ge_le: [
        (
            "inline <= flagged",
            1,
            [
                "\tcheck_variable = { my_var <= 5 }\n",
            ],
        ),
        (
            "strict > not flagged",
            0,
            [
                "\tcheck_variable = { my_var > 5 }\n",
            ],
        ),
        (
            ">= in comment not flagged",
            0,
            [
                "\t# check_variable = { my_var >= 5 }\n",
            ],
        ),
    ],
    _check_add_to_faction_country: [
        (
            "add_to_faction = warsaw_pact (lowercase faction id) flagged",
            1,
            [
                "\tadd_to_faction = warsaw_pact\n",
            ],
        ),
        (
            "add_to_faction = FIN (country tag) not flagged",
            0,
            [
                "\tadd_to_faction = FIN\n",
            ],
        ),
        (
            "add_to_faction = ROOT (scope keyword) not flagged",
            0,
            [
                "\tadd_to_faction = ROOT\n",
            ],
        ),
        (
            "add_to_faction = PREV.PREV (scope chain) not flagged",
            0,
            [
                "\tadd_to_faction = PREV.PREV\n",
            ],
        ),
        (
            "add_to_faction = var:ally_tag not flagged",
            0,
            [
                "\tadd_to_faction = var:ally_tag\n",
            ],
        ),
        (
            "add_to_faction = BRICS in comment not flagged",
            0,
            [
                "\t# add_to_faction = BRICS\n",
            ],
        ),
    ],
    _check_create_faction_deprecated: [
        (
            'create_faction = "Name" (quoted) flagged',
            1,
            [
                '\tcreate_faction = "Name"\n',
            ],
        ),
        (
            "on_create_faction hook line not flagged",
            0,
            [
                "\ton_create_faction = {\n",
            ],
        ),
        (
            "create_faction = X in comment not flagged",
            0,
            [
                "\t# create_faction = X\n",
            ],
        ),
    ],
    _check_tautological_or: [
        (
            "OR { X = no X = yes } flagged",
            1,
            [
                "\t\tOR = { is_historical_focus_on = no is_historical_focus_on = yes }\n",
            ],
        ),
        (
            "OR with different tokens not flagged",
            0,
            [
                "\t\tOR = { is_historical_focus_on = yes is_debug = no }\n",
            ],
        ),
        (
            "OR with both yes not flagged",
            0,
            [
                "\t\tOR = { has_war = yes has_war = yes }\n",
            ],
        ),
        (
            "tautological OR in comment not flagged",
            0,
            [
                "\t\t# OR = { is_historical_focus_on = yes is_historical_focus_on = no }\n",
            ],
        ),
    ],
    _check_decision_allowed_dynamic: [
        (
            "has_opinion inside multi-line allowed flagged",
            1,
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
        ),
        (
            "has_opinion in available after multi-line allowed not flagged",
            0,
            [
                "GRE_decisions_category = {\n",
                "\tGRE_some_decision = {\n",
                "\t\tallowed = {\n",
                "\t\t\toriginal_tag = GRE\n",
                "\t\t}\n",
                "\t\tavailable = {\n",
                "\t\t\thas_opinion = { target = CHI value > 0 }\n",
                "\t\t}\n",
                "\t\tcomplete_effect = { add_political_power = 10 }\n",
                "\t}\n",
                "}\n",
            ],
        ),
    ],
    _check_focus_missing_war_hint: [
        (
            "proxy war in a foreign scope not flagged",
            0,
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
        ),
        (
            "owner war reached via ROOT inside a foreign scope flagged",
            1,
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
        ),
        (
            "focus sending a war event without hint flagged",
            1,
            [
                "\tfocus = {\n",
                "\t\tid = ALG_press_claim\n",
                "\t\tcompletion_reward = {\n",
                "\t\t\tcountry_event = {\n",
                "\t\t\t\tid = alg_war.1\n",
                "\t\t\t\tdays = 1\n",
                "\t\t\t}\n",
                "\t\t}\n",
                "\t}\n",
            ],
            _WAR_CHAIN_EVENTS,
        ),
        (
            "focus sending a peaceful event not flagged",
            0,
            [
                "\tfocus = {\n",
                "\t\tid = ALG_hold_talks\n",
                "\t\tcompletion_reward = {\n",
                "\t\t\tcountry_event = { id = alg_peace.1 days = 1 }\n",
                "\t\t}\n",
                "\t}\n",
            ],
            _WAR_CHAIN_EVENTS,
        ),
        (
            "focus reaching war through a chained event flagged",
            1,
            _chain_lines,
            _WAR_CHAIN_EVENTS,
        ),
        (
            "war event sent through dynamic state owners not flagged",
            0,
            [
                "\tfocus = {\n",
                "\t\tid = ALG_contact_owners\n",
                "\t\tcompletion_reward = {\n",
                "\t\t\t19 = { OWNER = { country_event = alg_war.1 } }\n",
                "\t\t\t298 = { owner = { country_event = alg_war.1 } }\n",
                "\t\t}\n",
                "\t}\n",
            ],
            _WAR_CHAIN_EVENTS,
        ),
        (
            "war event sent inside effect_tooltip not flagged",
            0,
            [
                "\tfocus = {\n",
                "\t\tid = ALG_show_plan\n",
                "\t\tcompletion_reward = {\n",
                "\t\t\teffect_tooltip = {\n",
                "\t\t\t\tcountry_event = { id = alg_war.1 }\n",
                "\t\t\t}\n",
                "\t\t}\n",
                "\t}\n",
            ],
            _WAR_CHAIN_EVENTS,
        ),
        (
            "war event with will_lead_to_war_with not flagged",
            0,
            [
                "\tfocus = {\n",
                "\t\tid = ALG_ready_for_war\n",
                "\t\twill_lead_to_war_with = MOR\n",
                "\t\tcompletion_reward = {\n",
                "\t\t\tcountry_event = { id = alg_war.1 days = 1 }\n",
                "\t\t}\n",
                "\t}\n",
            ],
            _WAR_CHAIN_EVENTS,
        ),
        (
            "unresolvable sent event not flagged",
            0,
            [
                "\tfocus = {\n",
                "\t\tid = ALG_unknown_signal\n",
                "\t\tcompletion_reward = {\n",
                "\t\t\tcountry_event = { id = alg_missing.9 days = 1 }\n",
                "\t\t}\n",
                "\t}\n",
            ],
            _WAR_CHAIN_EVENTS,
        ),
        (
            "proxy war and an untagged focus exempt",
            0,
            [
                "\n",
                "focus = {\n",
                "\tid = generic_focus\n",
                "\tavailable = { NOT = { has_war = yes } }\n",
                "\tcompletion_reward = {\n",
                "\t\tvar:my_ally = { declare_war_on = ROOT }\n",
                "\t}\n",
                "}\n",
            ],
        ),
    ],
    _check_check_expr_bad_operand: [
        (
            "check_expr greater_than > 6 flagged",
            1,
            [
                "check_expr = {\n",
                "\tvalue = my_var\n",
                "\tgreater_than > 6\n",
                "}\n",
            ],
        ),
        (
            "check_expr less_than > 0.40 flagged",
            1,
            [
                "check_expr = {\n",
                "\tvalue = my_var\n",
                "\tless_than > 0.40\n",
                "}\n",
            ],
        ),
        (
            "check_expr greater_than = 6 (bare scalar) not flagged",
            0,
            [
                "check_expr = {\n",
                "\tvalue = my_var\n",
                "\tgreater_than = 6\n",
                "}\n",
            ],
        ),
    ],
    _check_every_owned_controlled_state: [
        (
            "every_owned_controlled_state flagged",
            1,
            [
                "\tevery_owned_controlled_state = {\n",
                "\t\tadd_stability = 0.01\n",
                "\t}\n",
            ],
        ),
        (
            "every_controlled_state not flagged",
            0,
            [
                "\tevery_controlled_state = {\n",
                "\t\tadd_stability = 0.01\n",
                "\t}\n",
            ],
        ),
        (
            "every_owned_controlled_state in comment not flagged",
            0,
            [
                "\t# every_owned_controlled_state = { }\n",
            ],
        ),
    ],
    _check_random_select_amount_literal: [
        (
            "random_select_amount with decimal flagged",
            1,
            [
                "\trandom_select_amount = 2.5\n",
            ],
        ),
        (
            "random_select_amount with integer literal not flagged",
            0,
            [
                "\trandom_select_amount = 3\n",
            ],
        ),
    ],
    _check_focus_log_id: [
        (
            "mismatch suppressed by unlock_national_focus in same block",
            0,
            [
                "\tfocus = {\n",
                "\t\tid = ABK_our_place\n",
                "\t\tcompletion_reward = {\n",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus ABK_tourism1"\n',
                "\t\t\tunlock_national_focus = ABK_tourism1\n",
                "\t\t}\n",
                "\t}\n",
            ],
        ),
        (
            "shared_focus block with lowercase 'focus' log flagged",
            1,
            [
                "shared_focus = {\n",
                "\tid = GCC_the_gcc\n",
                "\tcompletion_reward = {\n",
                '\t\tlog = "[GetDateText]: [This.GetName]: focus GCC_economic_union executed"\n',
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "hyphenated focus id, log matches",
            0,
            [
                "\tfocus = {\n",
                "\t\tid = TST_austria-este\n",
                "\t\tcompletion_reward = {\n",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus TST_austria-este"\n',
                "\t\t}\n",
                "\t}\n",
            ],
        ),
        (
            "no id to compare against",
            0,
            ["\n", "focus = {\n", '\tlog = "[GetDateText]: Focus TAG_other"\n', "}\n"],
        ),
    ],
    _check_decision_log_id: [
        (
            "'Decision remove <own id>' keyword tolerance not flagged",
            0,
            [
                "UAR_decisions_category = {\n",
                "\tUAR_integrate_MAU = {\n",
                "\t\tremove_effect = {\n",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision remove UAR_integrate_MAU"\n',
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "'Decision cancel effect <own id>' double-filler tolerance not flagged",
            0,
            [
                "NATO_decisions_category = {\n",
                "\tNATO_CSTO_breach_mission = {\n",
                "\t\tcancel_effect = {\n",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision cancel effect NATO_CSTO_breach_mission"\n',
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "keyword-only log with no id token not flagged",
            0,
            [
                "SOME_decisions_category = {\n",
                "\tSOME_decision = {\n",
                "\t\tcomplete_effect = {\n",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision"\n',
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "hyphenated decision id, log matches",
            0,
            [
                "category_test = {\n",
                "\tTest-State_invite = {\n",
                "\t\tcomplete_effect = {\n",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision Test-State_invite"\n',
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "hyphenated decision id, log mismatch",
            1,
            [
                "category_test = {\n",
                "\tTest-State_invite = {\n",
                "\t\tcomplete_effect = {\n",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision Test-State_remove"\n',
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "malformed block header skipped",
            0,
            [
                "test_category = {\n",
                "\tsome thing = {\n",
                '\t\tlog = "[GetDateText]: Decision other_decision"\n',
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "log with no Decision word naming another id flagged",
            1,
            _logged_decision("[GetDateText]: [Root.GetName]: TST_other"),
        ),
        (
            "log with no Decision word, filler word and trailing space flagged",
            1,
            _logged_decision("[GetDateText]: [Root.GetName]: add TST_other "),
        ),
        (
            "log with no Decision word naming its own id not flagged",
            0,
            _logged_decision("[GetDateText]: [Root.GetName]: TST_decision"),
        ),
        (
            "free text after the standard prefix not flagged",
            0,
            _logged_decision("[GetDateText]: [Root.GetName]: Operation succeeded"),
        ),
        (
            "filler word alone is not an id",
            0,
            _logged_decision("[GetDateText]: [Root.GetName]: remove"),
        ),
        (
            "Mission log naming another id flagged",
            1,
            _logged_decision("[GetDateText]: [Root.GetName]: Mission TST_other"),
        ),
        (
            "effect block name before its own id not flagged",
            0,
            _logged_decision(
                "[GetDateText]: [Root.GetName]: mission timeout_effect TST_decision"
            ),
        ),
        (
            "id built at runtime not flagged",
            0,
            _logged_decision("[GetDateText]: [Root.GetName]: Mission TST_[?x.id]_end"),
        ),
    ],
    _check_event_log_id: [
        (
            "option-executed phrasing citing another option flagged",
            1,
            [
                "country_event = {\n",
                "\tid = brotherhood.6\n",
                "\toption = {\n",
                "\t\tname = brotherhood.6.a\n",
                '\t\tlog = "[GetDateText]: [This.GetName]: brotherhood.6.b option executed"\n',
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "bare id + matching Option letter not flagged",
            0,
            [
                "country_event = {\n",
                "\tid = HKG_contract.1\n",
                "\toption = {\n",
                "\t\tname = HKG_contract.1.a\n",
                '\t\tlog = "[GetDateText]: [Root.GetName]: Event HKG_contract.1 Option a"\n',
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "oN suffix copy-pasted from a sibling option flagged",
            1,
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
        ),
        (
            "nested country_event scheduling call not treated as a definition",
            0,
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
        ),
        (
            "shared loc name with this event's log id not flagged",
            0,
            [
                "news_event = {\n",
                "\tid = isisNews.1302\n",
                "\toption = {\n",
                "\t\tname = isisNews.1301.a\n",
                '\t\tlog = "[GetDateText]: [This.GetName]: isisNews.1302.a executed"\n',
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "non-event dotted log endings not treated as event ids",
            0,
            [
                "country_event = {\n",
                "\tid = tst.11\n",
                "\toption = {\n",
                "\t\tname = tst.11.a\n",
                '\t\tlog = "[GetDateText]: [This.GetName]: ROOT.capital"\n',
                '\t\tlog = "[GetDateText]: [This.GetName]: v1.2"\n',
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "event without an id",
            0,
            [
                "\n",
                "country_event = {\n",
                "\toption = {\n",
                '\t\tlog = "[GetDateText]: Event other.1"\n',
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "option without a name",
            0,
            [
                "country_event = {\n",
                "\tid = test.1\n",
                "\toption = {\n",
                '\t\tlog = "[GetDateText]: Event other.1"\n',
                "\t}\n",
                "}\n",
            ],
        ),
    ],
    _check_hidden_trigger_in_ctt: [
        (
            "hidden_trigger nested under OR (depth 2) not flagged",
            0,
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
        ),
        (
            "stray brace inside a quoted log string doesn't mask the hidden_trigger",
            1,
            [
                "\tcustom_trigger_tooltip = {\n",
                "\t\ttooltip = TEST_TT\n",
                '\t\tlog = "test { brace"\n',
                "\t\thidden_trigger = {\n",
                "\t\t\thas_country_flag = test_flag\n",
                "\t\t}\n",
                "\t}\n",
            ],
        ),
    ],
    _check_leader_rotation: [
        (
            "do_not_retire subtracting 0 flagged (no-op guard)",
            1,
            _rotation(_tier("conservatism_leader", 0, undo=0)),
        ),
        (
            "do_not_retire subtracting another ideology's counter flagged",
            1,
            _rotation(_tier("conservatism_leader", 0, retire="socialism_leader")),
        ),
        (
            "tier gap flagged (no tier 1)",
            1,
            _rotation(
                _tier("conservatism_leader", 0),
                _tier("conservatism_leader", 2, guard=_B_GUARD),
            ),
        ),
        (
            "rotation not starting at tier 0 flagged",
            1,
            _rotation(
                _tier("conservatism_leader", 1),
                _tier("conservatism_leader", 2, guard=_B_GUARD),
            ),
        ),
        (
            "duplicate tier number flagged",
            1,
            _rotation(
                _tier("conservatism_leader", 0),
                _tier("conservatism_leader", 0, guard=_B_GUARD),
            ),
        ),
        (
            "duplicate tier discriminated by a flag not flagged",
            0,
            _rotation(
                _tier("conservatism_leader", 0, guard="has_country_flag = TST_coup "),
                _tier(
                    "conservatism_leader",
                    0,
                    guard="NOT = { has_country_flag = TST_coup } ",
                ),
            ),
        ),
        (
            "same tier number under two date containers not flagged",
            0,
            [
                "set_leader_TST = {\n",
                "\tif = { limit = { check_variable = { ruling_party = 1 } }\n",
                "\t\tif = { limit = { date < 2002.12.10 }\n",
                *_tier("conservatism_leader", 0),
                "\t\t}\n",
                "\t\tif = { limit = { date > 2002.12.10 }\n",
                *_tier("conservatism_leader", 0),
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "lookup-table branch with no increment not gap-checked",
            0,
            [
                "set_leader_TST = {\n",
                "\tif = { limit = { check_variable = { ruling_party = 2 } }\n",
                "\t\tif = { limit = { check_variable = { liberalism_leader = 1 } }\n",
                '\t\t\tcreate_country_leader = { name = "A" ideology = liberalism }\n',
                "\t\t}\n",
                "\t\tif = { limit = { check_variable = { liberalism_leader = 3 } }\n",
                '\t\t\tcreate_country_leader = { name = "B" ideology = liberalism }\n',
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "duplicate set_conservatism branch flagged",
            1,
            [
                "set_leader_TST = {\n",
                "\tif = { limit = { check_variable = { ruling_party = 1 } }\n",
                *_tier("conservatism_leader", 0),
                "\t}\n",
                "\telse_if = { limit = { check_variable = { ruling_party = 1 } }\n",
                *_tier("conservatism_leader", 0),
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "NOT = { check_variable = { b = 0 } } flagged (always false)",
            1,
            _rotation(
                _tier("conservatism_leader", 0),
                _tier(
                    "conservatism_leader",
                    1,
                    guard="NOT = { check_variable = { b = 0 } } ",
                ),
            ),
        ),
        (
            "branch counting with another ideology's counter flagged",
            1,
            [
                "set_leader_TST = {\n",
                "\tif = { limit = { check_variable = { ruling_party = 1 } }\n",
                *_tier("conservatism_leader", 0),
                "\t}\n",
                "\telse_if = { limit = { check_variable = { ruling_party = 23 } }\n",
                *_tier("conservatism_leader", 0),
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "off-name counter owned by a single branch not flagged",
            0,
            _rotation(
                _tier("socalism_leader", 0),
                _tier("socalism_leader", 1, guard=_B_GUARD),
                slot=3,
            ),
        ),
        (
            "incomplete branches tolerated",
            0,
            [
                "other_effect = {\n",
                "\tadd_political_power = 1\n",
                "}\n",
                "set_leader_TST = {\n",
                "\tclr_country_flag = temp_flag\n",
                "\tif = {\n",
                "\t\tadd_political_power = 1\n",
                "\t}\n",
                "\tif = {\n",
                "\t\tlimit = { check_variable = { ruling_party = 1 } date > 2010.1.1 }\n",
                "\t\tif = {\n",
                "\t\t\tadd_political_power = 1\n",
                "\t\t}\n",
                "\t\tif = {\n",
                "\t\t\tlimit = { check_variable = { b = 1 } check_variable = { conservatism_leader = 0 } }\n",
                "\t\t\tadd_to_variable = { conservatism_leader = step_size }\n",
                '\t\t\tcreate_country_leader = { name = "L" traits = { some_trait } }\n',
                "\t\t\tif = {\n",
                "\t\t\t\tadd_political_power = 1\n",
                "\t\t\t}\n",
                "\t\t\tif = {\n",
                "\t\t\t\tlimit = { has_war = yes }\n",
                "\t\t\t\tadd_political_power = 1\n",
                "\t\t\t}\n",
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
    ],
    _check_retired_ideology_flags: [
        (
            "retired ideology flags flagged regardless of operation or layout",
            3,
            [
                "test_trigger = {\n",
                "\thas_country_flag\n",
                "\t\t=\n",
                "\t\tset_conservatism\n",
                "}\n",
                "test_effect = {\n",
                "\tset_country_flag = {\n",
                "\t\tvalue = 1\n",
                "\t\tflag = set_Kingdom\n",
                "\t}\n",
                "}\n",
                "cleanup_effect = { clr_country_flag = set_Nat_Autocracy }\n",
            ],
        ),
        (
            "commented and quoted retired ideology flags ignored",
            0,
            [
                "# has_country_flag = set_conservatism\n",
                'log = "set_country_flag = set_Kingdom"\n',
            ],
        ),
    ],
    _check_country_exists_scope_contradiction: [
        (
            "multi-line NOT = { country_exists = CAN } flagged",
            1,
            [
                "\tbypass = {\n",
                "\t\tCAN = { is_subject_of = USA }\n",
                "\t\tNOT = {\n",
                "\t\t\tcountry_exists = CAN\n",
                "\t\t}\n",
                "\t}\n",
            ],
        ),
        (
            "OR-wrapped (intended form) not flagged",
            0,
            [
                "\tbypass = {\n",
                "\t\tOR = {\n",
                "\t\t\tNOT = { country_exists = CAN }\n",
                "\t\t\tCAN = { is_subject_of = USA }\n",
                "\t\t}\n",
                "\t}\n",
            ],
        ),
        (
            "NOT wrapping a scope switch (not country_exists) not flagged",
            0,
            [
                "\tlimit = {\n",
                "\t\tJOR = { influence_higher_10 = yes }\n",
                "\t\tNOT = { JOR = { influence_higher_20 = yes } }\n",
                "\t}\n",
            ],
        ),
        (
            "NOT mixing country_exists with another trigger (NAND) not flagged",
            0,
            [
                "\tbypass = {\n",
                "\t\tNOT = {\n",
                "\t\t\thas_war_with = AFG\n",
                "\t\t\tcountry_exists = AFG\n",
                "\t\t}\n",
                "\t\tAFG = { is_subject = yes }\n",
                "\t}\n",
            ],
        ),
        (
            "scope checking only flags on a dead tag not flagged",
            0,
            [
                "\tlimit = {\n",
                "\t\tNOT = { country_exists = CHE }\n",
                "\t\tCHE = { NOT = { has_country_flag = SUB_subject_rebellion_flag } }\n",
                "\t}\n",
            ],
        ),
        (
            "scope checking only variables on a dead tag not flagged",
            0,
            [
                "\tvisible = {\n",
                "\t\tNOT = { country_exists = PTR }\n",
                "\t\tPTR = { check_variable = { separatism > 10 } }\n",
                "\t}\n",
            ],
        ),
        (
            "stray } in a log string inside the scope block still flagged",
            1,
            [
                "\tbypass = {\n",
                "\t\tCAN = {\n",
                '\t\t\tlog = "closing } here"\n',
                "\t\t\tis_subject_of = USA\n",
                "\t\t}\n",
                "\t\tNOT = { country_exists = CAN }\n",
                "\t}\n",
            ],
        ),
    ],
    _check_mutually_exclusive_contradictions: [
        (
            "single-line OR with two tag values not flagged",
            0,
            ["\tOR = { tag = USA tag = CHI }\n"],
        ),
        ("single value not flagged", 0, ["\tlimit = { has_government = communism }\n"]),
        (
            "contradiction shape inside a quoted string not flagged",
            0,
            ['\tlog = "NOT = { tag = USA tag = CHI }"\n'],
        ),
        (
            "has_country_leader_ideology contradiction covered by set-driven regex",
            1,
            [
                "\tNOT = { has_country_leader_ideology = communism"
                " has_country_leader_ideology = fascism }\n"
            ],
        ),
        (
            "original_tag and tag are different triggers -- not a single-trigger contradiction",
            0,
            ["\tNOT = { original_tag = USA tag = CHI }\n"],
        ),
    ],
    _check_building_missing_province: [
        (
            "naval_base without province flagged",
            1,
            [
                "\t\t\tadd_building_construction = {\n",
                "\t\t\t\ttype = naval_base\n",
                "\t\t\t\tlevel = 2\n",
                "\t\t\t\tinstant_build = yes\n",
                "\t\t\t}\n",
            ],
        ),
        (
            "supply_node with literal province not flagged",
            0,
            [
                "\t\t\tadd_building_construction = {\n",
                "\t\t\t\ttype = supply_node\n",
                "\t\t\t\tlevel = 1\n",
                "\t\t\t\tprovince = 12299\n",
                "\t\t\t}\n",
            ],
        ),
        (
            "state-level building without province not flagged",
            0,
            [
                "\t\t\tadd_building_construction = {\n",
                "\t\t\t\ttype = industrial_complex\n",
                "\t\t\t\tlevel = 2\n",
                "\t\t\t}\n",
            ],
        ),
        (
            "single-line construction without province flagged",
            1,
            ["\t\t\tadd_building_construction = { type = naval_base level = 2 }\n"],
        ),
    ],
    _check_event_ai_historical_bankruptcy_fallback: [
        (
            "eligible fallback keeps historical bankruptcy event valid",
            0,
            [
                "country_event = {\n",
                "\tid = test_events.2\n",
                "\toption = {\n",
                "\t\tname = test_events.2.a\n",
                "\t\tai_chance = {\n",
                "\t\t\tbase = 50\n",
                "\t\t\tmodifier = {\n",
                "\t\t\t\tfactor = 0\n",
                "\t\t\t\thas_active_mission = bankruptcy_incoming_collapse\n",
                "\t\t\t}\n",
                "\t\t}\n",
                "\t}\n",
                "\toption = {\n",
                "\t\tname = test_events.2.b\n",
                "\t\tai_chance = { base = 50 }\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "an add after factor = 0 restores the option and clears the finding",
            0,
            [
                "country_event = {\n",
                "\tid = test_events.3\n",
                "\toption = {\n",
                "\t\tname = test_events.3.a\n",
                "\t\tai_chance = {\n",
                "\t\t\tbase = 50\n",
                "\t\t\tmodifier = {\n",
                "\t\t\t\tfactor = 0\n",
                "\t\t\t\thas_active_mission = bankruptcy_incoming_collapse\n",
                "\t\t\t}\n",
                "\t\t\tmodifier = {\n",
                "\t\t\t\tadd = 30\n",
                "\t\t\t\thas_active_mission = bankruptcy_incoming_collapse\n",
                "\t\t\t}\n",
                "\t\t}\n",
                "\t}\n",
                "\toption = {\n",
                "\t\tname = test_events.3.b\n",
                "\t\tai_chance = {\n",
                "\t\t\tbase = 50\n",
                "\t\t\tmodifier = {\n",
                "\t\t\t\tfactor = 0\n",
                "\t\t\t\tis_historical_focus_on = yes\n",
                "\t\t\t}\n",
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "an option its own trigger rules out is not a usable fallback",
            1,
            [
                "country_event = {\n",
                "\tid = test_events.4\n",
                "\toption = {\n",
                "\t\tname = test_events.4.a\n",
                "\t\tai_chance = {\n",
                "\t\t\tbase = 50\n",
                "\t\t\tmodifier = {\n",
                "\t\t\t\tfactor = 0\n",
                "\t\t\t\thas_active_mission = bankruptcy_incoming_collapse\n",
                "\t\t\t}\n",
                "\t\t}\n",
                "\t}\n",
                "\toption = {\n",
                "\t\tname = test_events.4.b\n",
                "\t\ttrigger = { NOT = { has_active_mission = bankruptcy_incoming_collapse } }\n",
                "\t\tai_chance = { base = 50 }\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "an unconditional add also restores a zeroed option",
            0,
            [
                "country_event = {\n",
                "\tid = test_events.6\n",
                "\toption = {\n",
                "\t\tname = test_events.6.a\n",
                "\t\tai_chance = {\n",
                "\t\t\tbase = 50\n",
                "\t\t\tmodifier = {\n",
                "\t\t\t\tfactor = 0\n",
                "\t\t\t\thas_active_mission = bankruptcy_incoming_collapse\n",
                "\t\t\t}\n",
                "\t\t\tmodifier = { add = 30 }\n",
                "\t\t}\n",
                "\t}\n",
                "\toption = {\n",
                "\t\tname = test_events.6.b\n",
                "\t\tai_chance = { base = 50 modifier = { factor = 0 is_historical_focus_on = yes } }\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "single-line ai_chance blocks are parsed for modifiers",
            1,
            [
                "country_event = {\n",
                "\tid = test_events.5\n",
                "\toption = {\n",
                "\t\tname = test_events.5.a\n",
                "\t\tai_chance = { base = 50 modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse } }\n",
                "\t}\n",
                "\toption = {\n",
                "\t\tname = test_events.5.b\n",
                "\t\tai_chance = { base = 50 modifier = { factor = 0 is_historical_focus_on = yes } }\n",
                "\t}\n",
                "}\n",
            ],
        ),
    ],
    _check_invalid_is_at_war: [
        (
            "is_at_war assignments flagged",
            2,
            ["\tlimit = { is_at_war = yes }\n", "\tis_at_war = no\n"],
        ),
        (
            "comments, quoted strings, and has_war are not flagged",
            0,
            [
                "\t# is_at_war = yes\n",
                '\tlog = "is_at_war = no"\n',
                "\thas_war = yes\n",
            ],
        ),
    ],
    _check_has_opinion_modifier_block: [
        (
            "block-form has_opinion_modifier flagged",
            1,
            ["\thas_opinion_modifier = { target = CHI modifier = exploited_us }\n"],
        ),
        (
            "scalar, quoted, and commented has_opinion_modifier forms not flagged",
            0,
            [
                "\thas_opinion_modifier = exploited_us\n",
                '\tlog = "has_opinion_modifier = { target = CHI }"\n',
                "\t# has_opinion_modifier = { target = CHI }\n",
            ],
        ),
    ],
    _check_wrong_stat_trigger: [
        (
            "bare stat names and has_command_power flagged",
            4,
            [
                "\tavailable = { emerging_reactionaries_are_in_power = yes stability > 0.5 }\n",
                "\twar_support < 0.3\n",
                "\tpolitical_power > 50\n",
                "\thas_command_power > 20\n",
            ],
        ),
        (
            "has_ triggers, variable blocks, modifiers, and comments not flagged",
            0,
            [
                "\thas_stability > 0.5\n",
                "\tcommand_power > 20\n",
                "\tcheck_variable = { stability > 0.6 }\n",
                "\tcheck_variable = {\n",
                "\t\tstability < 0.1\n",
                "\t}\n",
                "\tstability = 0.05\n",
                "\tmax_manpower > 5\n",
                "\t# stability > 0.5\n",
            ],
        ),
        (
            "comparison after a closed variable block flagged",
            1,
            [
                "\tcheck_variable = {\n",
                "\t\tstability < 0.1\n",
                "\t}\n",
                "\tstability > 0.5\n",
            ],
        ),
    ],
    _check_stat_effect_magnitude: [
        ("fraction not flagged", 0, ["\tadd_stability = 0.05\n"]),
        ("negative fraction not flagged", 0, ["\tadd_stability = -0.1\n"]),
        ("stability of 1 flagged", 1, ["\tadd_stability = 1\n"]),
        ("stability of -1 flagged", 1, ["\tadd_stability = -1\n"]),
        ("war support of 15 flagged", 1, ["\tadd_war_support = 15\n"]),
        ("variable not flagged", 0, ["\tadd_stability = var_name\n"]),
        ("decimal magnitude flagged", 1, ["\tadd_stability = 1.5\n"]),
        ("expression not flagged", 0, ["\tadd_stability = 5 * 0.01\n"]),
        ("comment not flagged", 0, ["\t# add_stability = 1\n"]),
        (
            "whole number before a closing brace flagged",
            1,
            ["\tTAG = { add_stability = 1 }\n"],
        ),
        (
            "whole number inside a log string not flagged",
            0,
            ['\tlog = "add_stability = 1"\n'],
        ),
    ],
    _check_else_with_limit: [
        (
            "limit directly inside else flagged",
            1,
            [
                "\t\t\telse = {\n",
                "\t\t\t\tlimit = { has_idea = boat_arrivals_ast_4 }\n",
                "\t\t\t\tadd_stability = 0.02\n",
                "\t\t\t}\n",
            ],
        ),
        (
            "limit on a scope nested in else not flagged",
            0,
            [
                "\telse = { random_country = { limit = { owns_state = 835 } "
                "country_event = { id = pandemic_events.1 } } }\n"
            ],
        ),
        (
            "plain else not flagged",
            0,
            ["\t\t\telse = {\n", "\t\t\t\tadd_stability = 0.02\n", "\t\t\t}\n"],
        ),
    ],
    _check_nested_province_block: [
        (
            "province = { province = <id> } flagged",
            1,
            [
                "\t\t\tadd_building_construction = {\n",
                "\t\t\t\ttype = coastal_bunker\n",
                "\t\t\t\tlevel = 4\n",
                "\t\t\t\tprovince = {\n",
                "\t\t\t\t\tprovince = 1269\n",
                "\t\t\t\t}\n",
                "\t\t\t}\n",
            ],
        ),
        (
            "province selector block not flagged",
            0,
            [
                "\t\t\tadd_building_construction = {\n",
                "\t\t\t\ttype = bunker\n",
                "\t\t\t\tprovince = {\n",
                "\t\t\t\t\tall_provinces = yes\n",
                "\t\t\t\t\tlimit_to_border = yes\n",
                "\t\t\t\t}\n",
                "\t\t\t}\n",
            ],
        ),
    ],
    _check_log_nested_quote: [
        (
            "comment swallowed into a log string flagged",
            1,
            [
                '\t\t\tlog = "[GetDateText]: [This.GetName]: pacific_solution.3.a # '
                '"Excellent news." executed"\n'
            ],
        ),
        (
            "well-formed log line not flagged",
            0,
            ['\t\tlog = "[GetDateText]: [Root.GetName]: Focus AST_old_reliable"\n'],
        ),
    ],
    _check_equipment_bonus: [
        (
            "named bonus on a real enum token not flagged",
            0,
            [
                "\t\t\tadd_equipment_bonus = { name = AST_old_reliable bonus = { "
                "infantry_weapons_type = { build_cost_ic = -0.10 } } }\n"
            ],
        ),
        (
            "vanilla archetype as a bonus type flagged",
            1,
            [
                "\t\t\tadd_equipment_bonus = { name = AST_old_reliable bonus = { "
                "infantry_equipment = { build_cost_ic = -0.10 } } }\n"
            ],
        ),
        (
            "project stands in for name",
            0,
            [
                "\t\t\tadd_equipment_bonus = { project = FROM bonus = { "
                "fighter = { build_cost_ic = 0.15 } } }\n"
            ],
        ),
    ],
    _check_equipment_type_defined: [
        (
            "vanilla archetype MD renamed flagged",
            1,
            [
                "\t\t\tadd_equipment_to_stockpile = {\n",
                "\t\t\t\ttype = infantry_equipment\n",
                "\t\t\t\tamount = -2200\n",
                "\t\t\t}\n",
            ],
        ),
        (
            "miscased equipment name flagged",
            1,
            ["\t\t\tsend_equipment = { type = Anti_air_2 amount = 50 target = LEB }\n"],
        ),
        (
            "engine-generated clone variant not flagged",
            0,
            [
                "\t\t\tadd_equipment_to_stockpile = { type = medium_tank_destroyer_chassis_0 "
                "amount = 10 }\n"
            ],
        ),
        (
            "building type left alone",
            0,
            ["\t\t\tadd_building_construction = { type = air_base level = 2 }\n"],
        ),
        (
            "equipment effect without a type ignored",
            0,
            ["\tadd_equipment_to_stockpile = { amount = 100 }\n"],
        ),
    ],
    _check_active_decision_defined: [
        (
            "mission naming no decision flagged",
            1,
            ["\t\t\t\thas_active_mission = EH_europe_defense_line_destruction_2\n"],
        ),
        (
            "mission naming a real decision not flagged",
            0,
            ["\t\t\t\thas_active_mission = EH_europe_defense_line_destruction\n"],
        ),
        (
            "commented-out trigger not flagged",
            0,
            ["\t\t\t\t# has_active_mission = EH_nope\n"],
        ),
    ],
    _check_modifier_ref_defined: [
        (
            "miscased relation modifier flagged",
            1,
            [
                "\tadd_relation_modifier = { target = UKR modifier = UKR_World_Economical_Relations }\n"
            ],
        ),
        (
            "defined relation modifier not flagged",
            0,
            [
                "\tadd_relation_modifier = { target = UKR modifier = UKR_world_economical_relations }\n"
            ],
        ),
        (
            "miscased opinion modifier flagged",
            1,
            [
                "\t\t\t\tadd_opinion_modifier = { target = BRM modifier = Military_Partnership }\n"
            ],
        ),
        (
            "defined opinion modifier not flagged",
            0,
            [
                "\t\t\t\tadd_opinion_modifier = { target = BRM modifier = military_partnership }\n"
            ],
        ),
    ],
    _check_ai_daily_flag_cache: [
        (
            "on_daily block that only set/clears a flag flagged",
            1,
            _CUB_DAILY_CACHE,
            "common/on_actions/99_CUB_on_actions.txt",
        ),
        (
            "on_daily block that also does real work not flagged",
            0,
            _CUB_DAILY_CACHE[:6]
            + [
                "\t\t\t\tadd_political_power = 5\n",
                "\t\t\t\tset_country_flag = CUB_did_a_thing\n",
                "\t\t\t\tclr_country_flag = CUB_did_a_thing\n",
            ]
            + _CUB_DAILY_CACHE[-4:],
            "common/on_actions/99_CUB_on_actions.txt",
        ),
        (
            "one-way latch (set with no matching clr) not flagged",
            0,
            [
                "on_actions = {\n",
                "\ton_daily_CUB = {\n",
                "\t\teffect = {\n",
                "\t\t\tset_country_flag = CUB_one_way_latch\n",
                "\t\t}\n",
                "\t}\n",
                "}\n",
            ],
            "common/on_actions/99_CUB_on_actions.txt",
        ),
        (
            "allowlisted on_daily_BOS not flagged",
            0,
            [ln.replace("on_daily_CUB", "on_daily_BOS") for ln in _CUB_DAILY_CACHE],
            "common/on_actions/MD_event_on_actions.txt",
        ),
        (
            "check is scoped to common/on_actions",
            0,
            _CUB_DAILY_CACHE,
            "common/scripted_effects/00_scripted_effects.txt",
        ),
    ],
    _check_redundant_avoid_starting_wars: [
        (
            "stricter-than-mod-wide ratio flagged",
            1,
            _war_brake("1.2"),
            "common/ai_strategy/CUB.txt",
        ),
        (
            "looser ratio than the mod-wide block not flagged",
            0,
            _war_brake("0.5"),
            "common/ai_strategy/CUB.txt",
        ),
        (
            "block carrying a targeted strategy not flagged",
            0,
            _war_brake("1.2", "declare_war id = HAI value = -4000"),
            "common/ai_strategy/CUB.txt",
        ),
        (
            "the mod-wide file itself is exempt",
            0,
            _war_brake("1.2"),
            "common/ai_strategy/MD_war_declaration_ai.txt",
        ),
        (
            "brake on a gate the strength ratio cannot express not flagged",
            0,
            [
                "BLR_avoid_nato_wars = {\n",
                "\tallowed = { original_tag = BLR }\n",
                "\tenable = {\n",
                "\t\thas_war = yes\n",
                "\t\tany_enemy_country = { is_in_faction_with = USA }\n",
                "\t}\n",
                "\tabort_when_not_enabled = yes\n",
                "\n",
                "\tai_strategy = { type = avoid_starting_wars value = -200 }\n",
                "}\n",
            ],
            "common/ai_strategy/BLR.txt",
        ),
    ],
    _check_bare_statement_token: [
        (
            "one-line bare call in NOT flagged",
            1,
            ["\tNOT = { GER_ai_not_historical_path }\n"],
        ),
        (
            "multi-line bare call in OR flagged",
            1,
            ["\tOR = {\n", "\t\tsome_trigger\n", "\t}\n"],
        ),
        (
            "list blocks not flagged",
            0,
            ["tags = { GER FRA }\n", "mutually_exclusive = { a b }\n"],
        ),
        (
            "mission_type_stats limit list not flagged",
            0,
            ["mission_type_stats = { limit = { cas attack_logistics } }\n"],
        ),
    ],
    _check_daily_mastery_index: [
        (
            "single-line and multi-line add_daily_mastery index flagged",
            2,
            [
                "\tadd_daily_mastery = { name = X track = operational_theory index = 1 days = 90 amount = 1 }\n",
                "\tadd_daily_mastery = {\n",
                "\t\tname = X\n",
                "\t\tindex = 4\n",
                "\t\tdays = 90\n",
                "\t}\n",
            ],
        ),
        (
            "add_daily_mastery without index, comments, quoted strings, and other blocks not flagged",
            0,
            [
                "\tadd_daily_mastery = { name = X track = training days = 90 amount = 1 }\n",
                "\tadd_daily_mastery = { name = X folder = land days = 90 amount = 1 } # index = 1\n",
                '\tlog = "add_daily_mastery = { index = 1 }"\n',
                "\tadd_to_array = { array = a value = 1 index = 0 }\n",
                "\tadd_mastery = { amount = 25 track = infantry }\n",
            ],
        ),
    ],
    _check_focus_available_always_no: [
        (
            "focus with a bypass is reachable",
            0,
            [
                "\n",
                "focus = {\n",
                "\tid = TAG_locked\n",
                "\tavailable = { always = no }\n",
                "\tbypass = { has_war = yes }\n",
                "}\n",
            ],
        ),
    ],
    _check_decision_available_always_no: [
        (
            "visible = { always = no } is a completion mechanism",
            0,
            [
                "\n",
                "test_category = {\n",
                "\n",
                "\tmy_decision = {\n",
                "\t\tfire_only_once = yes\n",
                "\t\tavailable = { always = no }\n",
                "\t\tvisible = { always = no }\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "a mission timeout is a completion mechanism",
            0,
            [
                "\n",
                "test_category = {\n",
                "\n",
                "\tmy_decision = {\n",
                "\t\tfire_only_once = yes\n",
                "\t\tavailable = { always = no }\n",
                "\t\tdays_mission_timeout = 30\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "block without a decision marker is not a decision",
            0,
            [
                "test_category = {\n",
                "\tnot_a_decision = {\n",
                "\t\tavailable = { always = no }\n",
                "\t}\n",
                "}\n",
            ],
        ),
    ],
    _check_empty_log_only_blocks: [
        (
            "commented-out effect block ignored",
            0,
            ['\t\t# completion_reward = { log = "x" }\n'],
        ),
        (
            "log beside a real effect kept",
            0,
            [
                "\toption = {\n",
                '\t\tlog = "[GetDateText]: Event test.1 Option a"\n',
                "\t\tadd_political_power = 10\n",
                "\t}\n",
                "\tcompletion_reward = {\n",
                '\t\tlog = "x"\n',
                "\t\tif = {\n",
                "\t\t\tlimit = { has_war = yes }\n",
                '\t\t\tlog = "branch"\n',
                "\t\t}\n",
                "\t}\n",
                '\t\tremove_effect = { log = "x" add_stability = 0.1 }\n',
            ],
        ),
    ],
    _check_while_loop_max_iterations: [
        (
            "while loop without max_iterations is clean",
            0,
            ["\twhile_loop_effect = {\n", "\t\tbreak = loop_done\n", "\t}\n"],
        ),
    ],
    _check_nor_block: [
        ("NOR block flagged", 1, ["\tNOR = { has_war = yes }\n"]),
        ("NOR in a comment not flagged", 0, ["\t# NOR = { has_war = yes }\n"]),
        ("NOR as a name prefix not flagged", 0, ["\tNORMANDY_flag = yes\n"]),
    ],
    _check_var_index_shorthand: [
        ("var:x^i shorthand flagged", 1, ["\tset_variable = { x = var:a^i }\n"]),
        ("shorthand in a comment not flagged", 0, ["\t# var:a^i\n"]),
    ],
    _check_shadowed_branches: [
        (
            "lower bound before a higher one flagged",
            1,
            _chain("check_variable = { x > 10 }", "check_variable = { x > 20 }"),
        ),
        (
            "higher bound first, then else, clean",
            0,
            [
                *_chain("check_variable = { x > 20 }", "check_variable = { x > 10 }")[
                    :-1
                ],
                "\telse = { add_stability = 0.3 }\n",
                "}\n",
            ],
        ),
        (
            "branch shadowed by two earlier ones reported once",
            2,
            [
                "effect = {\n",
                "\tif = { limit = { check_variable = { x > 10 } } add_stability = 0.1 }\n",
                "\telse_if = { limit = { check_variable = { x > 20 } } add_stability = 0.2 }\n",
                "\telse_if = { limit = { check_variable = { x > 30 } } add_stability = 0.3 }\n",
                "}\n",
            ],
        ),
        (
            "tighter less-than bound after a looser one flagged",
            1,
            _chain("check_variable = { x < 5 }", "check_variable = { x < 3 }"),
        ),
        (
            "bare comparison bounds flagged",
            1,
            _chain("has_stability > 0.5", "has_stability > 0.75"),
        ),
        (
            "bounds on different triggers not compared",
            0,
            _chain("has_stability > 0.5", "has_war_support > 0.75"),
        ),
        (
            "earlier limit contained in a later one flagged",
            1,
            _chain("has_idea = a", "has_idea = a has_war = yes"),
        ),
        (
            "opposite operators not ordered",
            0,
            _chain("check_variable = { x > 10 }", "check_variable = { x < 5 }"),
        ),
        (
            "equality is not a bound",
            0,
            _chain("check_variable = { x = 20 }", "check_variable = { x = 10 }"),
        ),
        (
            "variables on different scopes not compared",
            0,
            _chain(
                "check_variable = { 169.troops < 1 }",
                "check_variable = { 1122.troops < 1 }",
            ),
        ),
        (
            "different quoted values not compared",
            0,
            _chain('has_dlc = "La Resistance"', 'has_dlc = "By Blood Alone"'),
        ),
        (
            "else_if written inside the if body flagged",
            1,
            [
                "effect = {\n",
                "\tif = { limit = { has_idea = a } add_stability = 0.1\n",
                "\t\telse_if = { limit = { has_idea = a } add_stability = 0.2 }\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "inner chain's else_if is not the outer chain's",
            0,
            [
                "effect = {\n",
                "\tif = { limit = { has_idea = a }\n",
                "\t\tif = { limit = { has_idea = b } add_stability = 0.1 }\n",
                "\t\telse_if = { limit = { has_idea = a } add_stability = 0.2 }\n",
                "\t}\n",
                "}\n",
            ],
        ),
        (
            "a new if starts a new chain",
            0,
            [
                "effect = {\n",
                "\tif = { limit = { has_idea = a } add_stability = 0.1 }\n",
                "\tif = { limit = { has_idea = b } add_stability = 0.2 }\n",
                "\telse_if = { limit = { has_idea = a } add_stability = 0.3 }\n",
                "}\n",
            ],
        ),
    ],
}


@pytest.mark.parametrize(
    ("check", "expected", "lines", "args"),
    [
        pytest.param(check, expected, lines, args, id=f"{check.__name__}: {label}")
        for check, rows in _COUNT_CASES.items()
        for label, expected, lines, *args in rows
    ],
)
def test_finding_count(monkeypatch, check, expected, lines, args):
    monkeypatch.setattr(common_mistakes, "_REAL_NATION_FLAGS", set())
    monkeypatch.setattr(common_mistakes, "_SCRIPT_COMPLETED_FOCUSES", set())
    monkeypatch.setattr(common_mistakes, "_SCRIPT_COMPLETED_DECISIONS", set())
    findings = check(lines, *args)
    assert len(findings) == expected, findings


# 48. Exact findings per check. check_file shares one _Source per file and
# skips a check, or a line, whose literal is absent, so each case pins the
# exact (line, message) and covers every alternative a gate literal stands for.

_DECISION_SHELL = ["TST_category = {\n", "\tTST_decision = {\n"]
_DECISION_END = ["\t}\n", "}\n"]
_ON_ACTIONS = "common/on_actions/TST_on_actions.txt"


_LOG_ONLY = 'log = "..." is the only effect in this {} block -- delete the block (a log records an effect that never runs)'
_REDUNDANT_AND = "redundant AND = { } wrapper (AND is the default scope) -- run tools/cleanup_or.py to fix"
_EQUIPMENT_UNDEFINED = "{} type = tst_fake_equipment is not defined in common/units/equipment/ -- the effect is a silent no-op"
_EMBARGO = '{} without has_dlc = "By Blood Alone" guard -- wrap in if = {{ limit = {{ has_dlc = "By Blood Alone" }} }}'
_FOCUS_LOG = "log references Focus TST_b, but the enclosing focus is TST_a -- likely copy-paste; fix the log id"
_FOCUS_WAR = "Focus TST_war has create_wargoal but no will_lead_to_war_with -- add will_lead_to_war_with = TAG so the AI prepares for war"
_NO_PROVINCE = "add_building_construction type = naval_base has no province -- it is a provincial building, so the engine rejects the effect and nothing is built; add province = <id> or province = { all_provinces = yes ... }"
_MAX_ITERATIONS = "max_iterations is not a valid while_loop_effect key -- the engine ignores it; bound the loop with its break variable"
_DAILY_MASTERY_INDEX = "index is not a valid add_daily_mastery key -- the engine rejects it (Invalid effect 'index'); filter with track, sub_doctrine, grand_doctrine or folder"
_DUPLICATE_ADD = "duplicate consecutive add_to_variable line (same as line {}) -- likely copy-paste error; use the combined value in a single line"
_IS_X_NATION = "is_X_nation in runtime context -- use has_country_flag = {} for O(1) lookup (allowed = {{ }} is OK for game-start checks)"

# Captured from the checker before the shared-_Source refactor.
_EXPECTED = {
    "single-condition OR": [
        (
            2,
            "redundant OR = { } wrapper around single condition -- run tools/cleanup_or.py to fix",
        )
    ],
    "redundant AND": [(2, _REDUNDANT_AND)],
    "AND after a closed OR": [(5, _REDUNDANT_AND)],
    "two tags in one AND": [
        (
            2,
            "multiple 'tag' values in same AND block (CHI, USA) -- always false since a country has only one tag; wrap in OR = { } to match any",
        )
    ],
    "two original_tags in one NOT": [
        (
            1,
            "NOT = { } contains multiple 'original_tag' values (CHI, USA) -- always true since a country has only one original_tag; use separate NOT blocks or NOT = { OR = { ... } }",
        )
    ],
    "two governments in one AND": [
        (
            1,
            "multiple 'has_government' values in same AND block (communism, democratic) -- always false since a country has only one has_government; wrap in OR = { } to match any",
        )
    ],
    "two intervention ideas in one NOT": [
        (
            2,
            "NOT = { } contains multiple intervention_doctrine ideas (intervention_isolation, intervention_local_security) -- always true since they're mutually exclusive; use NOT = { OR = { ... } } or separate NOT blocks per idea",
        )
    ],
    "NOT country_exists beside the same scope": [
        (
            2,
            "AND block has NOT = { country_exists = GER } alongside a GER = { ... } scope switch -- always false (the scope fails when GER is absent, the NOT is only true then); use OR = { ... } to match either condition",
        )
    ],
    "retired ideology flag": [
        (
            1,
            "retired ideology flag set_conservatism -- gate on ruling_party (slot 0: western_autocrats_are_in_power)",
        )
    ],
    "unreachable focus": [
        (
            3,
            "available = { always = no } with no bypass, complete_national_focus, or unlock_national_focus -- focus is permanently unreachable; add a bypass block or reach it via complete/unlock_national_focus",
        )
    ],
    "focus war without hint": [(1, _FOCUS_WAR)],
    "focus declare_war_on without hint": [(1, _FOCUS_WAR)],
    "focus log names another focus": [(3, _FOCUS_LOG)],
    "shared_focus log names another focus": [(3, _FOCUS_LOG)],
    "joint_focus log names another focus": [(3, _FOCUS_LOG)],
    "unreachable decision": [
        (
            3,
            "available = { always = no } without visible = { always = no } -- add visible = { always = no } for script-triggered decisions, or set a real available condition",
        )
    ],
    "dynamic trigger in decision allowed": [
        (
            3,
            "dynamic trigger 'has_political_power' in decision allowed block -- allowed is evaluated once at game start; move to available",
        )
    ],
    "decision log names another decision": [
        (
            3,
            "log references Decision TST_other, but the enclosing decision is TST_decision -- likely copy-paste; fix the log id",
        )
    ],
    "every event option zeroed under bankruptcy": [
        (
            1,
            "event tst.1 gives every AI option factor 0 under historical focus plus bankruptcy -- keep at least one sub-$5 or non-spending fallback eligible",
        )
    ],
    "country_event log names another option": [
        (
            5,
            "log references Event tst.1.b, but this option's own name is tst.1.a -- likely copy-paste; fix the log id",
        )
    ],
    "news_event log names the wrong option letter": [
        (
            5,
            "log says Option b but this option's own name is tst.1.a -- fix the option letter",
        )
    ],
    "country_event executed-form log names another option": [
        (
            5,
            "log references Event tst.1.a, but this option's own name is tst.1.b -- likely copy-paste; fix the log id",
        )
    ],
    "leader tier advances by two": [
        (
            4,
            "tier conservatism_leader = 0 advances the counter by 2 -- every tier must advance it by exactly 1 (the tier index is not the step); 2 leaves later leaders unreachable",
        )
    ],
    "hidden_trigger inside custom_trigger_tooltip": [
        (
            3,
            "hidden_trigger = { } directly inside custom_trigger_tooltip is redundant -- unwrap its children to the tooltip's own depth",
        )
    ],
    "consecutive tag scopes": [
        (
            5,
            "consecutive SOV = { } blocks (first at line 1) -- merge into a single scope block to reduce tooltip nesting",
        )
    ],
    "tag scope closed beside an effect": [],
    "send_embargo unguarded": [(1, _EMBARGO.format("send_embargo"))],
    "break_embargo unguarded": [(1, _EMBARGO.format("break_embargo"))],
    "divide by an unguarded variable": [
        (
            1,
            "divide_variable by 'tst_divisor' without a zero guard -- add check_variable = { tst_divisor > 0 } before dividing",
        )
    ],
    "duplicate add_to_variable": [(2, _DUPLICATE_ADD.format(1))],
    "duplicate add_to_temp_variable": [(3, _DUPLICATE_ADD.format(2))],
    "every_country over a member idea": [
        (
            1,
            "every_country with has_idea = EU_member -- use for_each_scope_loop = { array = global.EU_member } instead (narrower iteration, better performance)",
        )
    ],
    "every_other_country over a member idea": [
        (
            1,
            "every_other_country with has_idea = NATO_member -- use for_each_scope_loop = { array = global.nato_members } instead (narrower iteration, better performance) and keep the self-exclusion as if = { limit = { NOT = { tag = ROOT } } }",
        )
    ],
    "any_country over a member idea": [
        (
            1,
            "any_country with has_idea = NATO_member -- use any_of_scopes = { array = global.nato_members } instead (checks only members; when negating or using all_of_scopes, add OR = { ... exists = no } -- stale array entries do not auto-skip in triggers)",
        )
    ],
    "any_other_country over a member idea": [
        (
            1,
            "any_other_country with has_idea = EU_member -- use any_of_scopes = { array = global.EU_member } instead (checks only members; when negating or using all_of_scopes, add OR = { ... exists = no } -- stale array entries do not auto-skip in triggers)",
        )
    ],
    "on_add adds what on_remove keeps": [
        (
            2,
            "on_add adds to global.tst_members but the sibling on_remove never removes from it -- removing the idea leaves a stale array entry",
        )
    ],
    "log-only option": [(1, _LOG_ONLY.format("option"))],
    "log-only effect blocks": [
        (1, _LOG_ONLY.format("complete_effect")),
        (2, _LOG_ONLY.format("on_add")),
        (3, _LOG_ONLY.format("on_remove")),
        (4, _LOG_ONLY.format("completion_reward")),
        (5, _LOG_ONLY.format("immediate")),
    ],
    "is_X_nation at runtime": [(1, _IS_X_NATION.format("arab_nation_flag"))],
    "is_nation at runtime": [(2, _IS_X_NATION.format("nation_flag"))],
    "daily flag cache": [
        (
            2,
            "on_daily_TST only refreshes country flags (TST_war) -- ai_strategy enable and focus ai_will_do are already evaluated lazily; write the condition inline instead of caching it daily",
        )
    ],
    "per-tag war brake": [
        (
            1,
            "CUB_avoid_starting_wars gates avoid_starting_wars on enemies_strength_ratio > 0.9 -- a strict subset of MD_avoid_new_wars_when_outmatched (> 0.75), so it never fires on a tick that block does not already own",
        )
    ],
    "percent_change without a call": [
        (
            1,
            "percent_change is set but change_influence_percentage = yes is never called in this file -- the setter is a silent no-op",
        )
    ],
    "percent_change set inside a random_country loop": [
        (
            1,
            "percent_change set inside a country-iteration loop with no change_influence_percentage = yes in the same loop -- the call must live inside the loop or it runs on stale/default values",
        )
    ],
    "check_variable >=": [
        (
            1,
            "check_variable does not accept '>=' inline (silently mis-parsed) -- use compare = greater_than_or_equals or rewrite as a strict inequality",
        )
    ],
    "add_to_faction a faction": [
        (
            1,
            "add_to_faction = BRICS is not a country -- add_to_faction takes a country tag or scope (ROOT/FROM/PREV/THIS/var:), not a faction name; it adds that country to the current scope's faction",
        )
    ],
    "create_faction": [
        (
            1,
            "create_faction is deprecated -- use create_faction_from_template = TEMPLATE instead for DLC compatibility",
        )
    ],
    "tautological OR": [
        (
            1,
            "tautological OR = { has_war = yes has_war = no } is always true -- remove the OR (fold any intended amount into base = N)",
        )
    ],
    "check_expr raw comparator": [
        (
            2,
            "check_expr operand 'greater_than' chained with a raw '>' -- use block form greater_than = { value = X } or a bare scalar (greater_than = X), not 'greater_than > X'",
        )
    ],
    "random_select_amount variable": [
        (
            1,
            "random_select_amount = var:x is not an integer literal -- random_select_amount requires a literal int",
        )
    ],
    "NOR": [
        (
            1,
            "NOR is not a HOI4 trigger keyword -- use separate NOT blocks or NOT = { OR = { ... } }",
        )
    ],
    "stability >": [(1, "stability > is not a trigger -- use has_stability >")],
    "has_command_power <": [
        (1, "has_command_power < is not a trigger -- use command_power <")
    ],
    "is_at_war": [(1, "is_at_war is not a HOI4 trigger -- use has_war = yes/no")],
    "has_opinion_modifier block": [
        (1, "has_opinion_modifier takes a modifier ID, not a block")
    ],
    "while_loop_effect max_iterations": [(2, _MAX_ITERATIONS)],
    "while_loop_effect split across lines": [(2, _MAX_ITERATIONS)],
    "add_daily_mastery index": [(1, _DAILY_MASTERY_INDEX)],
    "add_daily_mastery index split across lines": [(3, _DAILY_MASTERY_INDEX)],
    "var:x^i shorthand": [
        (
            1,
            "var:a^ is the shorthand form -- write the full array name, e.g. var:my_array^i",
        )
    ],
    "limit inside else": [
        (
            3,
            "limit inside an else block -- else takes no condition, so the engine rejects the block and the branch never runs; use else_if",
        )
    ],
    "log with a second quote": [
        (
            1,
            "log string contains a second quoted run -- it closes the value early and the engine parses the remainder as effects; keep the log to one quoted string",
        )
    ],
    "equipment bonus without a name": [
        (
            1,
            "add_equipment_bonus has no name = <loc key> (or project) -- the engine drops the whole effect",
        ),
        (
            1,
            "add_equipment_bonus bonus type 'tst_not_a_bonus' is not in script_enum_equipment_bonus_type -- the engine rejects the bonus",
        ),
    ],
    "stockpile of undefined equipment": [
        (1, _EQUIPMENT_UNDEFINED.format("add_equipment_to_stockpile"))
    ],
    "send_equipment of undefined equipment": [
        (1, _EQUIPMENT_UNDEFINED.format("send_equipment"))
    ],
    "production of undefined equipment": [
        (1, _EQUIPMENT_UNDEFINED.format("add_equipment_production"))
    ],
    "subsidy of undefined equipment": [
        (1, _EQUIPMENT_UNDEFINED.format("add_equipment_subsidy"))
    ],
    "has_active_mission naming nothing": [
        (
            1,
            "has_active_mission = tst_fake_mission names no decision in common/decisions/ -- the trigger is always false",
        )
    ],
    "undefined opinion modifier": [
        (
            1,
            "add_opinion_modifier modifier = tst_fake_modifier is not defined in common/opinion_modifiers/ -- nothing is applied",
        )
    ],
    "undefined relation modifier": [
        (
            1,
            "add_relation_modifier modifier = tst_fake_modifier is not defined in common/modifiers/ -- nothing is applied",
        )
    ],
    "every_owned_controlled_state": [
        (1, "every_owned_controlled_state does not exist -- use every_controlled_state")
    ],
    "provincial building without province": [(1, _NO_PROVINCE)],
    "add_building_construction split across lines": [(1, _NO_PROVINCE)],
    "province block naming an id": [
        (
            3,
            "province = { province = <id> } is not a valid selector -- the engine rejects the add_building token and nothing is built; write province = <id>",
        )
    ],
    "bare trigger call": [
        (
            1,
            'bare "tst_trigger" inside NOT = { }: add "= yes" to call the scripted trigger/effect',
        )
    ],
    "shadowed else_if": [
        (
            3,
            "else_if never runs -- the branch at line 2 already matches whenever this limit holds, and if/else_if stops at the first match",
        )
    ],
    "war support 15": [
        (
            1,
            "add_war_support = 15 is at least 100% -- add_war_support takes a fraction (0.05 is 5%)",
        )
    ],
}


def _exact(case_id, check, lines, *args):
    return pytest.param(check, lines, args, _EXPECTED[case_id], id=case_id)


_EXACT_CASES = [
    _exact(
        "single-condition OR",
        find_single_condition_or_blocks,
        ["\ttrigger = {\n", "\t\tOR = { has_war = yes }\n", "\t}\n"],
    ),
    _exact(
        "redundant AND",
        find_redundant_and_blocks,
        ["\ttrigger = {\n", "\t\tAND = { has_war = yes }\n", "\t}\n"],
    ),
    _exact(
        "AND after a closed OR",
        find_redundant_and_blocks,
        [
            "OR = {\n",
            "\ta = yes\n",
            "\tb = yes\n",
            "}\n",
            "AND = {\n",
            "\tc = yes\n",
            "}\n",
        ],
    ),
    _exact(
        "two tags in one AND",
        _check_mutually_exclusive_contradictions,
        ["limit = {\n", "\ttag = USA\n", "\ttag = CHI\n", "}\n"],
    ),
    _exact(
        "two original_tags in one NOT",
        _check_mutually_exclusive_contradictions,
        ["NOT = { original_tag = USA original_tag = CHI }\n"],
    ),
    _exact(
        "two governments in one AND",
        _check_mutually_exclusive_contradictions,
        ["limit = { has_government = democratic has_government = communism }\n"],
    ),
    _exact(
        "two intervention ideas in one NOT",
        _check_has_idea_mutex_in_not_block,
        [
            "NOT = {\n",
            "\thas_idea = intervention_isolation\n",
            "\thas_idea = intervention_local_security\n",
            "}\n",
        ],
    ),
    _exact(
        "NOT country_exists beside the same scope",
        _check_country_exists_scope_contradiction,
        [
            "available = {\n",
            "\tNOT = { country_exists = GER }\n",
            "\tGER = { has_war = yes }\n",
            "}\n",
        ],
    ),
    _exact(
        "retired ideology flag",
        _check_retired_ideology_flags,
        ["if = { limit = { has_country_flag = set_conservatism } }\n"],
    ),
    _exact(
        "unreachable focus",
        _check_focus_available_always_no,
        [
            "focus = {\n",
            "\tid = TST_unreachable\n",
            "\tavailable = { always = no }\n",
            "}\n",
        ],
    ),
    _exact(
        "focus war without hint",
        _check_focus_missing_war_hint,
        [
            "focus = {\n",
            "\tid = TST_war\n",
            "\tcompletion_reward = { create_wargoal = { type = annex_everything target = GER } }\n",
            "}\n",
        ],
    ),
    _exact(
        "focus declare_war_on without hint",
        _check_focus_missing_war_hint,
        [
            "focus = {\n",
            "\tid = TST_war\n",
            "\tcompletion_reward = { declare_war_on = { target = GER type = annex_everything } }\n",
            "}\n",
        ],
    ),
    _exact(
        "focus log names another focus",
        _check_focus_log_id,
        [
            "focus = {\n",
            "\tid = TST_a\n",
            '\tlog = "[GetDateText]: Focus TST_b"\n',
            "}\n",
        ],
    ),
    _exact(
        "shared_focus log names another focus",
        _check_focus_log_id,
        ["shared_focus = {\n", "\tid = TST_a\n", '\tlog = "Focus TST_b"\n', "}\n"],
    ),
    _exact(
        "joint_focus log names another focus",
        _check_focus_log_id,
        ["joint_focus = {\n", "\tid = TST_a\n", '\tlog = "Focus TST_b"\n', "}\n"],
    ),
    _exact(
        "unreachable decision",
        _check_decision_available_always_no,
        _DECISION_SHELL
        + [
            "\t\tavailable = { always = no }\n",
            "\t\tcomplete_effect = { add_political_power = 10 }\n",
        ]
        + _DECISION_END,
    ),
    _exact(
        "dynamic trigger in decision allowed",
        _check_decision_allowed_dynamic,
        _DECISION_SHELL
        + [
            "\t\tallowed = { has_political_power > 10 }\n",
            "\t\tcomplete_effect = { add_political_power = 10 }\n",
        ]
        + _DECISION_END,
    ),
    _exact(
        "decision log names another decision",
        _check_decision_log_id,
        _DECISION_SHELL
        + ['\t\tcomplete_effect = { log = "[GetDateText]: Decision TST_other" }\n']
        + _DECISION_END,
    ),
    _exact(
        "every event option zeroed under bankruptcy",
        _check_event_ai_historical_bankruptcy_fallback,
        [
            "news_event = {\n",
            "\tid = tst.1\n",
            "\toption = {\n",
            "\t\tname = tst.1.a\n",
            "\t\tai_chance = { base = 5 modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse } }\n",
            "\t}\n",
            "}\n",
        ],
    ),
    _exact(
        "country_event log names another option",
        _check_event_log_id,
        [
            "country_event = {\n",
            "\tid = tst.1\n",
            "\toption = {\n",
            "\t\tname = tst.1.a\n",
            '\t\tlog = "[GetDateText]: Event tst.1.b"\n',
            "\t}\n",
            "}\n",
        ],
    ),
    _exact(
        "news_event log names the wrong option letter",
        _check_event_log_id,
        [
            "news_event = {\n",
            "\tid = tst.1\n",
            "\toption = {\n",
            "\t\tname = tst.1.a\n",
            '\t\tlog = "Event tst.1 Option b"\n',
            "\t}\n",
            "}\n",
        ],
    ),
    _exact(
        "country_event executed-form log names another option",
        _check_event_log_id,
        [
            "country_event = {\n",
            "\tid = tst.1\n",
            "\toption = {\n",
            "\t\tname = tst.1.b\n",
            '\t\tlog = "[GetDateText]: [This.GetName]: tst.1.a executed"\n',
            "\t}\n",
            "}\n",
        ],
    ),
    _exact(
        "leader tier advances by two",
        _check_leader_rotation,
        _rotation(_tier("conservatism_leader", 0, increment=2)),
    ),
    _exact(
        "hidden_trigger inside custom_trigger_tooltip",
        _check_hidden_trigger_in_ctt,
        [
            "custom_trigger_tooltip = {\n",
            "\ttooltip = TST_tt\n",
            "\thidden_trigger = { has_war = yes }\n",
            "}\n",
        ],
    ),
    _exact(
        "consecutive tag scopes",
        _check_consecutive_scope_blocks,
        [
            "\tSOV = {\n",
            "\t\tadd_stability = 0.05\n",
            "\t}\n",
            "\n",
            "\tSOV = {\n",
            "\t\tadd_war_support = 0.05\n",
            "\t}\n",
        ],
    ),
    _exact(
        "tag scope closed beside an effect",
        _check_consecutive_scope_blocks,
        [
            "\tSOV = {\n",
            "\t\tadd_stability = 0.05\n",
            "\t} add_political_power = 1\n",
            "\n",
            "\tSOV = {\n",
            "\t\tadd_war_support = 0.05\n",
            "\t}\n",
        ],
    ),
    _exact(
        "send_embargo unguarded", _check_embargo_dlc_guard, ["\tsend_embargo = GER\n"]
    ),
    _exact(
        "break_embargo unguarded", _check_embargo_dlc_guard, ["\tbreak_embargo = GER\n"]
    ),
    _exact(
        "divide by an unguarded variable",
        _check_divide_variable_zero_guard,
        ["\tdivide_variable = { tst_value = tst_divisor }\n"],
    ),
    _exact(
        "duplicate add_to_variable",
        _check_duplicate_add_to_variable,
        ["\tadd_to_variable = { x = 1 }\n", "\tadd_to_variable = { x = 1 }\n"],
    ),
    _exact(
        "duplicate add_to_temp_variable",
        _check_duplicate_add_to_variable,
        [
            "x = 1\n",
            "\tadd_to_temp_variable = { x = 1 }\n",
            "\tadd_to_temp_variable = { x = 1 }\n",
        ],
    ),
    _exact(
        "every_country over a member idea",
        _check_every_country_member_array,
        [
            "every_country = {\n",
            "\tlimit = { has_idea = EU_member }\n",
            "\tadd_political_power = 1\n",
            "}\n",
        ],
    ),
    _exact(
        "every_other_country over a member idea",
        _check_every_country_member_array,
        [
            "\tevery_other_country = {\n",
            "\t\tlimit = { has_idea = NATO_member }\n",
            "\t}\n",
        ],
    ),
    _exact(
        "any_country over a member idea",
        _check_any_country_member_array,
        ["any_country = {\n", "\thas_idea = NATO_member\n", "}\n"],
    ),
    _exact(
        "any_other_country over a member idea",
        _check_any_country_member_array,
        ["\tany_other_country = { has_idea = EU_member }\n"],
    ),
    _exact(
        "on_add adds what on_remove keeps",
        _check_on_add_array_symmetry,
        [
            "TST_idea = {\n",
            "\ton_add = { add_to_array = { global.tst_members = THIS } }\n",
            "\ton_remove = { add_political_power = 1 }\n",
            "}\n",
        ],
    ),
    _exact(
        "log-only option",
        _check_empty_log_only_blocks,
        [
            "option = {\n",
            "\tname = tst.1.a\n",
            '\tlog = "Event tst.1 Option a"\n',
            "}\n",
        ],
    ),
    _exact(
        "log-only effect blocks",
        _check_empty_log_only_blocks,
        [
            'complete_effect = { log = "a" }\n',
            'on_add = { log = "b" }\n',
            'on_remove = { log = "c" }\n',
            'completion_reward = { log = "d" }\n',
            "immediate = {\n",
            '\tlog = "e"\n',
            "}\n",
        ],
    ),
    _exact(
        "is_X_nation at runtime",
        _check_is_x_nation_runtime,
        ["available = { is_arab_nation = yes }\n"],
    ),
    _exact(
        "is_nation at runtime",
        _check_is_x_nation_runtime,
        ["available = {\n", "\tis_nation = yes\n", "}\n"],
    ),
    _exact(
        "daily flag cache",
        _check_ai_daily_flag_cache,
        [
            "on_actions = {\n",
            "\ton_daily_TST = {\n",
            "\t\teffect = {\n",
            "\t\t\tif = { limit = { has_war = yes } set_country_flag = TST_war }\n",
            "\t\t\telse = { clr_country_flag = TST_war }\n",
            "\t\t}\n",
            "\t}\n",
            "}\n",
        ],
        _ON_ACTIONS,
    ),
    _exact(
        "per-tag war brake",
        _check_redundant_avoid_starting_wars,
        _war_brake("0.9"),
        "common/ai_strategy/TST.txt",
    ),
    _exact(
        "percent_change without a call",
        _check_influence_setter_scope,
        ["\tset_temp_variable = { percent_change = 5 }\n"],
    ),
    _exact(
        "percent_change set inside a random_country loop",
        _check_influence_setter_scope,
        [
            "random_country = {\n",
            "\tset_temp_variable = { percent_change = 5 }\n",
            "}\n",
            "change_influence_percentage = yes\n",
        ],
    ),
    _exact(
        "check_variable >=", _check_check_var_ge_le, ["\tcheck_variable = { x >= 1 }\n"]
    ),
    _exact(
        "add_to_faction a faction",
        _check_add_to_faction_country,
        ["\tadd_to_faction = BRICS\n"],
    ),
    _exact(
        "create_faction",
        _check_create_faction_deprecated,
        ["\tcreate_faction = TST_faction\n"],
    ),
    _exact(
        "tautological OR",
        _check_tautological_or,
        ["\tOR = { has_war = yes has_war = no }\n"],
    ),
    _exact(
        "check_expr raw comparator",
        _check_check_expr_bad_operand,
        ["check_expr = {\n", "\tgreater_than > 6\n", "}\n"],
    ),
    _exact(
        "random_select_amount variable",
        _check_random_select_amount_literal,
        ["\trandom_select_amount = var:x\n"],
    ),
    _exact("NOR", _check_nor_block, ["\tNOR = { has_war = yes }\n"]),
    _exact("stability >", _check_wrong_stat_trigger, ["\tstability > 0.5\n"]),
    _exact(
        "has_command_power <", _check_wrong_stat_trigger, ["\thas_command_power < 5\n"]
    ),
    _exact("is_at_war", _check_invalid_is_at_war, ["\tis_at_war = yes\n"]),
    _exact(
        "has_opinion_modifier block",
        _check_has_opinion_modifier_block,
        ["\thas_opinion_modifier = { target = GER }\n"],
    ),
    _exact(
        "while_loop_effect max_iterations",
        _check_while_loop_max_iterations,
        ["while_loop_effect = {\n", "\tmax_iterations = 5\n", "}\n"],
    ),
    _exact(
        "while_loop_effect split across lines",
        _check_while_loop_max_iterations,
        ["while_loop_effect\n", "= { max_iterations = 5 }\n"],
    ),
    _exact(
        "add_daily_mastery index",
        _check_daily_mastery_index,
        [
            "\tadd_daily_mastery = { track = leadership index = 4 days = 90 amount = 1 }\n"
        ],
    ),
    _exact(
        "add_daily_mastery index split across lines",
        _check_daily_mastery_index,
        [
            "\tadd_daily_mastery\n",
            "\t= {\n",
            "\t\tindex = 1\n",
            "\t\tdays = 90\n",
            "\t}\n",
        ],
    ),
    _exact(
        "var:x^i shorthand",
        _check_var_index_shorthand,
        ["\tset_variable = { x = var:a^i }\n"],
    ),
    _exact(
        "limit inside else",
        _check_else_with_limit,
        [
            "if = { limit = { has_war = yes } }\n",
            "else = {\n",
            "\tlimit = { has_war = no }\n",
            "}\n",
        ],
    ),
    _exact(
        "log with a second quote",
        _check_log_nested_quote,
        ['\tlog = "Focus x" # "note"\n'],
    ),
    _exact(
        "equipment bonus without a name",
        _check_equipment_bonus,
        [
            "add_equipment_bonus = {\n",
            "\tbonus = { tst_not_a_bonus = { build_cost_ic = -0.1 } }\n",
            "}\n",
        ],
    ),
    _exact(
        "stockpile of undefined equipment",
        _check_equipment_type_defined,
        ["\tadd_equipment_to_stockpile = { type = tst_fake_equipment amount = 1 }\n"],
    ),
    _exact(
        "send_equipment of undefined equipment",
        _check_equipment_type_defined,
        ["\tsend_equipment = { type = tst_fake_equipment amount = 1 target = GER }\n"],
    ),
    _exact(
        "production of undefined equipment",
        _check_equipment_type_defined,
        [
            "\tadd_equipment_production = { equipment = { type = tst_fake_equipment } }\n"
        ],
    ),
    _exact(
        "subsidy of undefined equipment",
        _check_equipment_type_defined,
        ["\tadd_equipment_subsidy = { type = tst_fake_equipment cic = 1 }\n"],
    ),
    _exact(
        "has_active_mission naming nothing",
        _check_active_decision_defined,
        ["\thas_active_mission = tst_fake_mission\n"],
    ),
    _exact(
        "undefined opinion modifier",
        _check_modifier_ref_defined,
        ["\tadd_opinion_modifier = { target = GER modifier = tst_fake_modifier }\n"],
    ),
    _exact(
        "undefined relation modifier",
        _check_modifier_ref_defined,
        ["\tadd_relation_modifier = { target = GER modifier = tst_fake_modifier }\n"],
    ),
    _exact(
        "every_owned_controlled_state",
        _check_every_owned_controlled_state,
        ["\tevery_owned_controlled_state = { add_manpower = 1 }\n"],
    ),
    _exact(
        "provincial building without province",
        _check_building_missing_province,
        ["add_building_construction = { type = naval_base level = 1 }\n"],
    ),
    _exact(
        "add_building_construction split across lines",
        _check_building_missing_province,
        ["add_building_construction\n", "= { type = naval_base level = 1 }\n"],
    ),
    _exact(
        "province block naming an id",
        _check_nested_province_block,
        [
            "add_building_construction = {\n",
            "\ttype = bunker\n",
            "\tprovince = { province = 123 }\n",
            "}\n",
        ],
    ),
    _exact(
        "bare trigger call", _check_bare_statement_token, ["\tNOT = { tst_trigger }\n"]
    ),
    _exact(
        "shadowed else_if",
        _check_shadowed_branches,
        _chain("has_idea = a", "has_idea = a"),
    ),
    _exact(
        "war support 15",
        _check_stat_effect_magnitude,
        ["\tadd_war_support = 15\n"],
    ),
]


@pytest.mark.parametrize("check, lines, args, expected", _EXACT_CASES)
def test_exact_findings(monkeypatch, check, lines, args, expected):
    monkeypatch.setattr(
        common_mistakes, "_REAL_NATION_FLAGS", {"arab_nation_flag", "nation_flag"}
    )
    monkeypatch.setattr(common_mistakes, "_SCRIPT_COMPLETED_FOCUSES", set())
    monkeypatch.setattr(common_mistakes, "_SCRIPT_COMPLETED_DECISIONS", set())
    assert check(lines, *args) == expected


_IS_AT_WAR = "is_at_war is not a HOI4 trigger -- use has_war = yes/no"


def test_match_on_a_line_with_a_trailing_comment():
    assert _check_invalid_is_at_war(["\tis_at_war = yes # legacy\n"]) == [
        (1, _IS_AT_WAR)
    ]
    # A comment cut drops the newline; the joined text still keeps one line per line.
    assert _check_while_loop_max_iterations(
        ["x = 1 # note\n", "while_loop_effect = { max_iterations = 5 }\n"]
    ) == [(2, _MAX_ITERATIONS)]


def test_get_block_stops_at_the_real_brace_after_a_quoted_one():
    lines = [
        "foo = {\n",
        '\tlog = "a { brace in a string"\n',
        "\tbar = yes\n",
        "}\n",
        "next = yes\n",
    ]
    assert _get_block(lines, 0) == (lines[:4], 4)


def test_explode_braces_keeps_the_tail_after_the_last_brace():
    assert common_mistakes._explode_braces("option = { base = 5 } # note") == [
        "option = {",
        " base = 5 }",
        " # note",
    ]


@pytest.mark.parametrize(
    ("line", "matches"),
    [("\tis_horn_of_africa_nation = yes\n", True), ("\thas_war = yes\n", False)],
)
def test_is_x_nation_pattern(line, matches):
    assert bool(_RE_IS_X_NATION.search(line)) is matches


def test_is_x_nation_flagged_only_when_a_real_flag_exists(monkeypatch):
    lines = ["\tavailable = { is_arab_nation = yes }\n"]
    monkeypatch.setattr(common_mistakes, "_REAL_NATION_FLAGS", set())
    assert _check_is_x_nation_runtime(lines) == []

    monkeypatch.setattr(common_mistakes, "_REAL_NATION_FLAGS", {"arab_nation_flag"})
    issues = _check_is_x_nation_runtime(lines)

    assert len(issues) == 1
    assert "has_country_flag = arab_nation_flag" in issues[0][1]


@pytest.mark.parametrize(
    ("lines", "filepath"),
    [
        pytest.param(
            ["\tallowed = {\n", "\t\tis_arab_nation = yes\n", "\t}\n"],
            "",
            id="inside an allowed block",
        ),
        pytest.param(
            [
                "\tif = {\n",
                "\t\tlimit = { is_arab_nation = yes }\n",
                "\t\tset_country_flag = arab_nation_flag\n",
                "\t}\n",
            ],
            "",
            id="at the flag definition site",
        ),
        pytest.param(
            ["\tis_arab_nation = yes\n"],
            "common\\scripted_triggers\\MD_nations.txt",
            id="where the triggers are defined",
        ),
    ],
)
def test_is_x_nation_is_free(monkeypatch, lines, filepath):
    monkeypatch.setattr(common_mistakes, "_REAL_NATION_FLAGS", {"arab_nation_flag"})
    assert _check_is_x_nation_runtime(lines, filepath) == []


def test_decision_activated_by_script_is_kept(monkeypatch):
    monkeypatch.setattr(common_mistakes, "_SCRIPT_COMPLETED_DECISIONS", {"my_decision"})
    lines = [
        "test_category = {\n",
        "\tmy_decision = {\n",
        "\t\tfire_only_once = yes\n",
        "\t\tavailable = { always = no }\n",
        "\t}\n",
        "}\n",
    ]
    assert _check_decision_available_always_no(lines) == []


def test_decision_traversal_skips_blank_and_markerless_blocks():
    lines = [
        "\n",
        "test_category = {\n",
        "\n",
        "\tnot_a_decision = {\n",
        "\t\tallowed = { has_opinion = { target = USA value > 50 } }\n",
        "\t}\n",
        "\tmy_decision = {\n",
        "\t\tfire_only_once = yes\n",
        "\t\tallowed = { has_army_size = { size > 10 } }\n",
        "\t}\n",
        "}\n",
    ]

    issues = _check_decision_allowed_dynamic(lines)

    assert len(issues) == 1
    assert "dynamic trigger 'has_army_size'" in issues[0][1]


def test_any_country_over_two_blocs_is_told_to_split():
    lines = [
        "any_country = {\n",
        "\thas_idea = EU_member\n",
        "\thas_idea = NATO_member\n",
        "}\n",
    ]

    issues = _check_any_country_member_array(lines)

    assert len(issues) == 1
    assert "use one any_of_scopes per array" in issues[0][1]


def test_war_hint_names_an_unidentified_focus():
    lines = [
        "focus = {\n",
        "\tcompletion_reward = { declare_war_on = USA }\n",
        "}\n",
    ]

    issues = _check_focus_missing_war_hint(lines)

    assert len(issues) == 1
    assert "Focus <unknown> has create_wargoal" in issues[0][1]


def _use_event_tree(monkeypatch, tmp_path, text):
    """Point the event-chain lookup at a fresh events/ tree holding text."""
    write_under_str(tmp_path, "events/chain.txt", text)
    monkeypatch.setattr(common_mistakes, "get_root_dir", lambda: str(tmp_path))
    monkeypatch.setattr(common_mistakes, "_EVENT_INDEX_BUILT", False)
    monkeypatch.setattr(common_mistakes, "_EVENT_INDEX", {})
    monkeypatch.setattr(common_mistakes, "_EVENT_BLOCKS", {})


def test_event_chain_uses_the_first_definition_of_a_repeated_id(tmp_path, monkeypatch):
    _use_event_tree(
        monkeypatch,
        tmp_path,
        "country_event = {\n"
        "\tid = dup.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { declare_war_on = { target = MOR type = annex_everything } }\n"
        "}\n"
        "country_event = {\n"
        "\tid = dup.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { add_political_power = 10 }\n"
        "}\n",
    )
    lines = [
        "focus = {\n",
        "\tid = ALG_dup\n",
        "\tcompletion_reward = { country_event = dup.1 }\n",
        "}\n",
    ]
    assert _check_focus_missing_war_hint(lines) == [
        (
            1,
            "Focus ALG_dup sends event dup.1 leading to war but has no"
            " will_lead_to_war_with -- add will_lead_to_war_with = TAG so the AI"
            " prepares for war",
        )
    ]


def test_event_chain_loads_definition_after_an_earlier_send(tmp_path, monkeypatch):
    _use_event_tree(
        monkeypatch,
        tmp_path,
        "".join(_WAR_CHAIN_EVENTS.values()).replace(
            "country_event = alg_chain.2", "country_event = { id = alg_chain.2 }"
        ),
    )
    result = _check_focus_missing_war_hint(_chain_lines)
    assert len(result) == 1
    assert "alg_chain.1 -> alg_chain.2" in result[0][1]


def test_event_definitions_ignore_comments_and_nested_sends():
    content = (
        "# country_event = { id = fake.1 option = { } }\n"
        "country_event = {\n"
        " id = real.1\n"
        " is_triggered_only = yes\n"
        " immediate = {\n"
        "  # } declare_war_on = { target = MOR }\n"
        "  country_event = { id = real.2 }\n"
        " }\n"
        "}\n"
    )
    blocks = list(common_mistakes._iter_event_definitions(content))
    assert len(blocks) == 1
    assert "id = real.1" in blocks[0]
    assert "declare_war_on" not in blocks[0]
    assert blocks[0].endswith("}\n}")


def test_event_chain_revisits_shared_event_with_more_depth_remaining():
    events = {
        "start.1": "option = { country_event = long.1 country_event = shared.1 }",
        "long.1": "option = { country_event = long.2 }",
        "long.2": "option = { country_event = shared.1 }",
        "shared.1": "option = { country_event = war.1 }",
        "war.1": "option = { declare_war_on = { target = MOR } }",
    }
    assert common_mistakes._event_chain_leads_to_war("start.1", "ALG", events) == (
        True,
        ["start.1", "shared.1", "war.1"],
    )


def _log_only_block_types(lines):
    issues = _check_empty_log_only_blocks(lines)
    return [message.split("this ")[1].split(" block")[0] for _line, message in issues]


@pytest.mark.parametrize(
    ("lines", "kinds"),
    [
        pytest.param(
            [
                "\toption = {\n",
                "\t\tname = test.1.a\n",
                '\t\tlog = "[GetDateText]: Event test.1 Option a"\n',
                "\t\ttrigger = { always = yes }\n",
                "\t\tai_chance = { base = 1 }\n",
                "\t}\n",
                "\tcomplete_effect = {\n",
                "\t\t# a comment does not count as content\n",
                '\t\tlog = "[GetDateText]: Decision my_decision"\n',
                "\t}\n",
            ],
            ["option", "complete_effect"],
            id="option and complete_effect",
        ),
        pytest.param(
            [
                f'\t{kind} = {{\n\t\tlog = "x"\n\t}}\n'
                for kind in (
                    "remove_effect",
                    "timeout_effect",
                    "cancel_effect",
                    "on_add",
                    "on_remove",
                    "completion_reward",
                    "select_effect",
                    "immediate",
                )
            ],
            [
                "remove_effect",
                "timeout_effect",
                "cancel_effect",
                "on_add",
                "on_remove",
                "completion_reward",
                "select_effect",
                "immediate",
            ],
            id="every logged effect block kind",
        ),
        pytest.param(
            [
                '\t\tcompletion_reward = { log = "[GetDateText]: Focus TST_x" }\n',
                '\t\ton_remove = { log = "" }  # trailing comment\n',
                "\t\tremove_effect = { }\n",
            ],
            ["completion_reward", "on_remove"],
            id="packed blocks",
        ),
    ],
)
def test_log_only_block_kinds(lines, kinds):
    assert _log_only_block_types(lines) == kinds


@pytest.mark.parametrize(
    ("modifier", "expected"),
    [
        *(
            pytest.param([body], ("none", False), id=body)
            for body in (
                "modifier = { NOT = { has_war = yes } factor = 0 }",
                "factor = 0 is_historical_focus_on = yes",
                "modifier = { factor = 0 is_historical_focus_on = yes stray }",
                "modifier = { add = abc is_historical_focus_on = yes }",
                "modifier = { add = -1 is_historical_focus_on = yes }",
                "modifier = { has_war = yes factor = 0 }",
                "modifier = { factor = 0 }",
            )
        ),
        pytest.param(
            [
                "modifier = {\n",
                "\tfactor = 0\n",
                "\tNAND = {\n",
                "\t\tis_historical_focus_on = yes\n",
                "\t\thas_active_mission = bankruptcy_incoming_collapse\n",
                "\t}\n",
                "}\n",
            ],
            ("none", False),
            id="brace-valued condition",
        ),
    ],
)
def test_ai_zero_modifier_conditions(modifier, expected):
    assert _ai_zero_modifier_conditions(modifier) == expected


def test_unrelated_not_beside_the_mission_is_not_a_negation():
    assert not _negates_bankruptcy_mission(
        "NOT = { has_war = yes } has_active_mission = bankruptcy_incoming_collapse"
    )
