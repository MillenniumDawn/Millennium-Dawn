"""Tests for the `available` block checks in validate_variables.py.

Inside a player-facing `available` block a bare check_variable renders no
tooltip line, a flag check renders its raw token unless a localisation key is
named after the flag, a scripted trigger built from bare flag checks renders
nothing, and a negated tooltip needs its _NOT key. A decision or branch only
the AI can reach is exempt.
"""

import pytest
import validate_variables as V
from shared.suite import variable_scan
from shared.suite import write_under as _write


def _validator(tmp_path, **kwargs):
    return V.Validator(str(tmp_path), use_colors=False, workers=1, **kwargs)


# --- available blocks -------------------------------------------------------


def test_check_variable_outside_available_is_not_flagged(tmp_path):
    """A stray `}` must not pop the block stack and mislabel the enclosing block."""
    path = _write(
        tmp_path,
        "common/national_focus/focus.txt",
        "}\n"
        "my_focus = {\n"
        "\tcompletion_reward = {\n"
        "\t\tcheck_variable = { TST_var > 5 }\n"
        "\t}\n"
        "}\n",
    )

    assert variable_scan(path, "available", tmp_path) == []


def test_untooltipped_check_variable_in_available_is_reported(tmp_path):
    _write(
        tmp_path,
        "common/decisions/dec.txt",
        "TST_category = {\n"
        "\tTST_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { TST_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_untooltipped_available_checks()

    assert [(i.category, i.severity, i.file, i.line) for i in validator._issues] == [
        (
            "untooltipped-available-check",
            V.Severity.ERROR,
            "common/decisions/dec.txt",
            4,
        )
    ]


def test_repeated_unlocalised_flag_in_one_file_is_reported_once(tmp_path):
    _write(
        tmp_path,
        "common/decisions/dec.txt",
        "TST_category = {\n"
        "\tTST_first = {\n"
        "\t\tavailable = { has_country_flag = TST_no_loc }\n"
        "\t}\n"
        "\tTST_second = {\n"
        "\t\tavailable = { has_country_flag = TST_no_loc }\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unlocalised_available_flags()

    assert [i.line for i in validator._issues] == [3]


_BORDER_TRIGGER = "TST_border_available = {\n\thas_global_flag = TST_border_open\n}\n"


def test_scripted_trigger_index_survives_an_unreadable_definition_file(tmp_path):
    (tmp_path / "common" / "scripted_triggers" / "broken.txt").mkdir(parents=True)
    _write(tmp_path, "common/scripted_triggers/border.txt", _BORDER_TRIGGER)
    validator = _validator(tmp_path)

    assert validator._collect_scripted_trigger_flag_names() == frozenset(
        {"TST_border_available"}
    )


def test_scripted_trigger_body_with_a_stray_close_brace():
    assert V._scripted_trigger_body_has_unwrapped_global_flag("} has_global_flag = x")


@pytest.mark.parametrize(
    "decisions, lines",
    [
        (None, []),
        (
            "TST_category = {\n"
            "\tTST_decision = {\n"
            "\t\tavailable = {\n"
            "\t\t\tTST_border_available = yes\n"
            "\t\t}\n"
            "\t}\n"
            "}\n",
            [4],
        ),
    ],
    ids=["no player-facing file", "bare call in available"],
)
def test_untooltipped_available_scripted_trigger(tmp_path, decisions, lines):
    _write(tmp_path, "common/scripted_triggers/border.txt", _BORDER_TRIGGER)
    if decisions is not None:
        _write(tmp_path, "common/decisions/dec.txt", decisions)
    validator = _validator(tmp_path)

    validator.validate_untooltipped_available_scripted_trigger()

    assert [(i.category, i.file, i.line) for i in validator._issues] == [
        (
            "untooltipped-available-scripted-trigger",
            "common/decisions/dec.txt",
            line,
        )
        for line in lines
    ]


def test_scripted_trigger_call_scan_survives_a_stray_close_brace(tmp_path):
    path = _write(
        tmp_path,
        "common/decisions/dec.txt",
        "}\n"
        "my_category = {\n"
        "\tmy_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\ttst_border_available = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )

    issues = variable_scan(
        path, "scripted", tmp_path, flagged_names=frozenset({"tst_border_available"})
    )

    assert [issue[2] for issue in issues] == [5]


def test_repeat_lookups_reuse_the_memoized_index(tmp_path):
    """Each index is harvested repo-wide; recomputing it per check is wasted work."""
    _write(tmp_path, "common/scripted_triggers/border.txt", _BORDER_TRIGGER)
    _write(
        tmp_path,
        "common/dynamic_modifiers/dyn.txt",
        "TST_modifier = {\n\tpolitical_power_factor = TST_pp\n}\n",
    )
    validator = _validator(tmp_path)

    assert validator._get_ai_only_categories() is validator._get_ai_only_categories()
    assert (
        validator._collect_scripted_trigger_flag_names()
        is validator._collect_scripted_trigger_flag_names()
    )
    assert (
        validator._collect_dynamic_modifier_vars()
        is validator._collect_dynamic_modifier_vars()
    )


# The AI-only exemption keys off the decisions path.
_DECISION_REL = "common/decisions/src.txt"
_FLAGGED = frozenset({"pak_raj_border_available"})
# Scan section -> a trigger that section reports when it sits bare in `available`.
_TRIGGERS = {
    "available": "check_variable = { my_var > 5 }",
    "scripted": "pak_raj_border_available = yes",
    "available_flags": "has_country_flag = ENG_deal_flag",
}
_ALL = tuple(_TRIGGERS)
_BARE = "my_decision = {\n\tavailable = {\n\t\t{t}\n\t}\n}\n"


def _available_scan(
    tmp_path, section, text, ai_categories=frozenset(), rel="src.txt", flagged=_FLAGGED
):
    path = _write(tmp_path, rel, text)
    return variable_scan(
        path,
        section,
        tmp_path,
        ai_categories=ai_categories,
        flagged_names=flagged if section == "scripted" else frozenset(),
    )


def _ai_split(ai_body, else_body="has_war = no", limit="is_ai = yes"):
    """`available` holding an AI-only `if` branch beside its human `else` half."""
    return (
        "my_focus = {\n"
        "\tavailable = {\n"
        "\t\tif = {\n"
        f"\t\t\tlimit = {{ {limit} }}\n"
        f"\t\t\t{ai_body}\n"
        "\t\t}\n"
        "\t\telse = {\n"
        f"\t\t\t{else_body}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def _in_decision(gate):
    return (
        "some_category = {\n"
        "\tmy_decision = {\n"
        f"\t\t{gate}\n"
        "\t\tavailable = {\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


# (id, sections, script with `{t}` for the trigger, finding lines, scan kwargs)
_AVAILABLE_CASES = [
    ("bare", _ALL, _BARE, [3], {}),
    (
        "custom_trigger_tooltip",
        ("scripted", "available_flags"),
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_trigger_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [],
        {},
    ),
    ("visible", _ALL, "my_decision = {\n\tvisible = {\n\t\t{t}\n\t}\n}\n", [], {}),
    (
        "ai_only_category",
        ("scripted",),
        _in_decision("cost = 25"),
        [],
        {"rel": _DECISION_REL, "ai_categories": frozenset({"some_category"})},
    ),
    ("ai_only_if_branch", ("available",), _ai_split("{t}"), [], {}),
    (
        "is_ai_nested_in_or",
        ("available",),
        _in_decision("visible = { OR = { is_ai = yes is_debug = yes } }"),
        [5],
        {"rel": _DECISION_REL},
    ),
    (
        "ordinary_category_beside_an_ai_one",
        ("available",),
        "ai_category = {\n"
        "\tai_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
        "human_category = {\n"
        "\thuman_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [11],
        {"rel": _DECISION_REL, "ai_categories": frozenset({"ai_category"})},
    ),
    (
        "sibling_of_an_ai_only_decision",
        ("available",),
        "some_category = {\n"
        "\tai_decision = {\n"
        "\t\tvisible = { is_ai = yes }\n"
        "\t\tavailable = {\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "\thuman_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [10],
        {"rel": _DECISION_REL},
    ),
    (
        # The span walk is decisions-only: a focus is not a category/decision pair.
        "focus_tree_with_is_ai",
        ("available",),
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tid = MY_focus\n"
        "\t\tavailable = {\n"
        "\t\t\tis_ai = yes\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [6],
        {"rel": "common/national_focus/my_tree.txt"},
    ),
    (
        "wrapper_several_levels_above",
        ("available",),
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_trigger_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\tNOT = { OR = { {t} } }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [],
        {},
    ),
    (
        "else_if_ai_branch",
        ("scripted",),
        "my_focus = {\n"
        "\tavailable = {\n"
        "\t\tif = {\n"
        "\t\t\tlimit = { has_war = yes }\n"
        "\t\t\thas_war = yes\n"
        "\t\t}\n"
        "\t\telse_if = {\n"
        "\t\t\tlimit = { is_ai = yes }\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [],
        {},
    ),
    (
        # The scan stops walking braces once no is_ai remains ahead; a later
        # branch with no is_ai at all must still reach the stack walk.
        "branch_after_the_last_is_ai",
        ("scripted",),
        _ai_split("has_war = no") + "my_other_focus = {\n"
        "\tavailable = {\n"
        "\t\tif = {\n"
        "\t\t\tlimit = { has_war = no }\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [16],
        {},
    ),
]


@pytest.mark.parametrize(
    ("section", "script", "lines", "kwargs"),
    [
        pytest.param(section, script, lines, kwargs, id=f"{name}-{section}")
        for name, sections, script, lines, kwargs in _AVAILABLE_CASES
        for section in sections
    ],
)
def test_available_finding_lines(tmp_path, section, script, lines, kwargs):
    text = script.replace("{t}", _TRIGGERS[section])
    out = _available_scan(tmp_path, section, text, **kwargs)
    assert [finding[2] for finding in out] == lines


def test_bare_available_findings_name_the_problem(tmp_path):
    def message(section):
        text = _BARE.replace("{t}", _TRIGGERS[section])
        return _available_scan(tmp_path, section, text)[0][0]

    assert "renders no tooltip line" in message("available")
    assert "—" not in message("available")
    assert "pak_raj_border_available" in message("scripted")
    assert "resolves to a scripted trigger" in message("scripted")
    assert message("available_flags") == "ENG_deal_flag"


@pytest.mark.parametrize(
    ("body", "lines"),
    [
        pytest.param(
            # check_variable's own `tooltip` field renders the requirement line.
            "\t\tcheck_variable = {\n"
            "\t\t\ttooltip = my_tt\n"
            "\t\t\tvar = my_var\n"
            "\t\t\tvalue = 5\n"
            "\t\t\tcompare = less_than\n"
            "\t\t}\n",
            [],
            id="inline_tooltip",
        ),
        pytest.param(
            "\t\tcheck_variable = {\n"
            "\t\t\tvar = my_var\n"
            "\t\t\tvalue = { base = 2 add = 3 }\n"
            "\t\t\tcompare = less_than\n"
            "\t\t\ttooltip = my_tt\n"
            "\t\t}\n",
            [],
            id="inline_tooltip_after_a_nested_value_block",
        ),
        pytest.param(
            "\t\tcheck_variable = {\n"
            "\t\t\tvar = my_var\n"
            "\t\t\tvalue = 5\n"
            "\t\t\tcompare = less_than\n"
            "\t\t}\n",
            [3],
            id="long_form_without_tooltip",
        ),
        pytest.param(
            "\t\tcheck_variable = { tooltip = my_tt var = a value = 5 compare = less_than }\n"
            "\t\tcheck_variable = { b > 2 }\n",
            [4],
            id="inline_tooltip_does_not_mask_the_next_check",
        ),
        pytest.param(
            "\t\tNOT = { OR = { check_variable = { a > 1 } check_variable = { b > 2 } } }\n",
            [3, 3],
            id="nested_in_boolean",
        ),
    ],
)
def test_check_variable_forms(tmp_path, body, lines):
    text = "my_decision = {\n\tavailable = {\n" + body + "\t}\n}\n"
    out = _available_scan(tmp_path, "available", text)
    assert [finding[2] for finding in out] == lines


@pytest.mark.parametrize(
    ("body", "names"),
    [
        pytest.param(
            "\t\thas_country_flag = { flag = ENG_deal_flag value > 0 }\n",
            ["ENG_deal_flag"],
            id="long_form",
        ),
        pytest.param(
            "\t\tNOT = { OR = { has_country_flag = a has_country_flag = b } }\n",
            ["a", "b"],
            id="nested_in_boolean",
        ),
        pytest.param(
            "\t\thas_country_flag = trade_agreement@PREV\n", [], id="dynamic_flag"
        ),
        pytest.param(
            "\t\thas_country_flag = a\n\t\thas_country_flag = b\n",
            ["a", "b"],
            id="two_distinct_flags",
        ),
    ],
)
def test_flag_forms(tmp_path, body, names):
    text = "my_decision = {\n\tavailable = {\n" + body + "\t}\n}\n"
    out = _available_scan(tmp_path, "available_flags", text)
    assert sorted(finding[0] for finding in out) == names


@pytest.mark.parametrize(
    ("text", "flag", "block"),
    [
        (
            "ENG_welsh_referendum = {\n"
            "\tcancel_trigger = {\n"
            "\t\tOR = {\n"
            "\t\t\tcountry_exists = WAS\n"
            "\t\t\thas_country_flag = ENG_devolution_purged\n"
            "\t\t}\n"
            "\t}\n"
            "}\n",
            "ENG_devolution_purged",
            "cancel_trigger",
        ),
        (
            "focus = {\n"
            "\tid = NRY_focus\n"
            "\tbypass = { has_country_flag = NRY_UK_DECLINED }\n"
            "}\n",
            "NRY_UK_DECLINED",
            "bypass",
        ),
    ],
    ids=["cancel_trigger", "bypass"],
)
def test_flag_in_other_player_facing_blocks(tmp_path, text, flag, block):
    out = _available_scan(tmp_path, "available_flags", text)
    assert len(out) == 1
    assert out[0][0] == flag
    assert out[0][4] == block


def test_only_unlocalised_flags_reported(tmp_path):
    _write(
        tmp_path,
        "localisation/english/test_l_english.yml",
        '﻿l_english:\n ENG_known_flag:0 "Known"\n',
    )
    _write(
        tmp_path,
        "common/decisions/test.txt",
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thas_country_flag = ENG_known_flag\n"
        "\t\thas_country_flag = ENG_unknown_flag\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unlocalised_available_flags()

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert "ENG_unknown_flag" in issue.message
    assert "ENG_known_flag" not in issue.message
    assert issue.severity == V.Severity.ERROR
    assert issue.category == "unlocalised-available-flag"


_WRAPPED_AU_TRIGGER = (
    "can_do_african_union_focus = {\n"
    "\tcustom_trigger_tooltip = {\n"
    "\t\ttooltip = can_do_african_union_focus_tt\n"
    "\t\tcheck_variable = { global.african_union_western_outlook_share > 0.50 }\n"
    "\t}\n"
    "\tcustom_trigger_tooltip = {\n"
    "\t\ttooltip = african_union_available_mandate_tt\n"
    "\t\thas_global_flag = african_union_mandate_granted\n"
    "\t}\n"
    "}\n"
)


@pytest.mark.parametrize(
    ("text", "name", "indexed"),
    [
        pytest.param(
            _WRAPPED_AU_TRIGGER,
            "can_do_african_union_focus",
            False,
            id="custom_trigger_tooltip_in_body",
        ),
        pytest.param(
            "mixed_trigger = {\n"
            "\tcustom_trigger_tooltip = {\n"
            "\t\ttooltip = wrapped_tt\n"
            "\t\thas_global_flag = WRAP_ok\n"
            "\t}\n"
            "\thas_global_flag = BARE_bad\n"
            "}\n",
            "mixed_trigger",
            True,
            id="mixed_wrapped_and_bare",
        ),
        pytest.param(
            # A builtin block name at depth 0 of a scripted_triggers file must
            # never be indexed. Filtering happens when the index is built, not
            # in the pool worker, which trusts whatever name set it is handed.
            "if = {\n\thas_global_flag = GLOBAL_x\n}\n",
            "if",
            False,
            id="builtin_block_name",
        ),
    ],
)
def test_scripted_trigger_index(tmp_path, text, name, indexed):
    _write(tmp_path, "common/scripted_triggers/t.txt", text)
    names = _validator(tmp_path)._collect_scripted_trigger_flag_names()
    assert (name in names) is indexed


@pytest.mark.parametrize(
    ("triggers", "caller_rel", "caller", "reported"),
    [
        pytest.param(
            "pak_raj_border_available = {\n"
            "\tNOT = { has_global_flag = GLOBAL_pak_raj_border_war_active }\n"
            "}\n"
            "pak_raj_border_pair_valid = {\n"
            "\tis_puppet = no\n"
            "}\n",
            "common/decisions/test.txt",
            _BARE.replace("{t}", _TRIGGERS["scripted"]),
            "pak_raj_border_available",
            id="bare call to a flagged trigger",
        ),
        pytest.param(
            _WRAPPED_AU_TRIGGER,
            "common/national_focus/au.txt",
            "shared_focus = {\n"
            "\tid = AFRICAN_UNION_shared_focus_create_investment_bank\n"
            "\tavailable = {\n"
            "\t\tcan_do_african_union_focus = yes\n"
            "\t}\n"
            "}\n",
            None,
            id="bare call to a wrapped trigger",
        ),
    ],
)
def test_validator_reports_bare_calls_to_flagged_triggers(
    tmp_path, triggers, caller_rel, caller, reported
):
    _write(tmp_path, "common/scripted_triggers/t.txt", triggers)
    _write(tmp_path, caller_rel, caller)
    validator = _validator(tmp_path)

    validator.validate_untooltipped_available_scripted_trigger()

    if reported is None:
        assert validator._issues == []
    else:
        assert len(validator._issues) == 1
        issue = validator._issues[0]
        assert reported in issue.message
        assert issue.severity == V.Severity.ERROR
        assert issue.category == "untooltipped-available-scripted-trigger"


# --- requirement lines through scripted triggers ----------------------------

_GDP_TRIGGER = (
    "TST_rich = {\n"
    "\tcustom_trigger_tooltip = {\n"
    "\t\ttooltip = TST_rich_tt\n"
    "\t\tcheck_variable = { gdp_per_capita > 29.999 }\n"
    "\t}\n"
    "}\n"
)


def _requirement_issues(tmp_path, triggers, available, loc=""):
    _write(tmp_path, "common/scripted_triggers/test.txt", triggers)
    _write(
        tmp_path,
        "common/decisions/test.txt",
        "TST_category = {\n\tTST_decision = {\n\t\tavailable = {\n"
        f"{available}\t\t}}\n\t}}\n}}\n",
    )
    _write(
        tmp_path,
        "localisation/english/test_l_english.yml",
        f"﻿l_english:\n{loc}",
    )
    validator = _validator(tmp_path)
    validator.validate_unlocalised_available_flags()
    validator.validate_negated_trigger_tooltips()
    return validator._issues


@pytest.mark.parametrize(
    ("triggers", "available", "loc", "reported"),
    [
        pytest.param(
            _GDP_TRIGGER,
            "\t\t\tNOT = { TST_rich = yes }\n",
            ' TST_rich_tt: "Rich"\n',
            "TST_rich_tt_NOT",
            id="negated call needs the _NOT key",
        ),
        pytest.param(
            _GDP_TRIGGER,
            "\t\t\tNOT = { TST_rich = yes }\n",
            ' TST_rich_tt: "Rich"\n TST_rich_tt_NOT: "Not rich"\n',
            None,
            id="negated call with the _NOT key",
        ),
        pytest.param(
            _GDP_TRIGGER,
            "\t\t\tTST_rich = no\n",
            "",
            "TST_rich_tt_NOT",
            id="a call with no is negated",
        ),
        pytest.param(
            _GDP_TRIGGER, "\t\t\tTST_rich = yes\n", "", None, id="positive call"
        ),
        pytest.param(
            _GDP_TRIGGER + "TST_poor = {\n\tNOT = { TST_rich = yes }\n}\n",
            "\t\t\tNOT = { TST_poor = yes }\n",
            "",
            None,
            id="double negation through a nested trigger",
        ),
        pytest.param(
            "",
            "\t\t\tNOT = {\n"
            "\t\t\t\tcustom_trigger_tooltip = { tooltip = TST_direct_tt always = yes }\n"
            "\t\t\t}\n",
            "",
            "TST_direct_tt_NOT",
            id="negated tooltip written in place",
        ),
        pytest.param(
            _GDP_TRIGGER.replace("custom_trigger_tooltip", "custom_override_tooltip"),
            "\t\t\tcustom_override_tooltip = {\n"
            "\t\t\t\ttooltip = TST_outer_tt\n"
            "\t\t\t\tNOT = { TST_rich = yes }\n"
            "\t\t\t}\n",
            "",
            None,
            id="call wrapped in its own tooltip is exempt",
        ),
        pytest.param(
            "TST_a = {\n\tTST_b = yes\n}\nTST_b = {\n\tTST_a = yes\n}\n",
            "\t\t\tTST_a = yes\n",
            "",
            None,
            id="recursive triggers terminate",
        ),
    ],
)
def test_negated_trigger_tooltips(tmp_path, triggers, available, loc, reported):
    issues = _requirement_issues(tmp_path, triggers, available, loc)
    if reported is None:
        assert issues == []
    else:
        assert [reported in issue.message for issue in issues] == [True]
        assert issues[0].severity == V.Severity.ERROR
        assert issues[0].category == "unlocalised-negated-trigger-tooltip"


def test_negated_call_reports_the_line_of_the_call(tmp_path):
    issues = _requirement_issues(
        tmp_path,
        _GDP_TRIGGER,
        "\t\t\tNOT = { TST_rich = yes }\n",
        ' TST_rich_tt: "Rich"\n',
    )
    assert [issue.line for issue in issues] == [4]


@pytest.mark.parametrize(
    ("wrapper", "via_trigger", "localised"),
    [
        ("custom_trigger_tooltip", False, False),
        ("custom_trigger_tooltip", False, True),
        ("custom_trigger_tooltip", True, False),
        ("custom_override_tooltip", True, False),
    ],
)
def test_explicit_negative_key(tmp_path, wrapper, via_trigger, localised):
    tooltip = (
        f"{wrapper} = {{\n"
        "\tnot_tooltip = TST_negative_tt\n"
        "\ttooltip = TST_positive_tt\n"
        "\talways = yes\n"
        "}\n"
    )
    triggers = ""
    available = f"NOT = {{ {tooltip} }}\n"
    if via_trigger:
        triggers = (
            f"TST_inner = {{\n{tooltip}}}\nTST_outer = {{\n\tTST_inner = no\n}}\n"
        )
        available = "TST_outer = yes\n"
    loc = ' TST_positive_tt: "Positive"\n'
    loc += (
        ' TST_negative_tt: "Negative"\n'
        if localised
        else ' TST_positive_tt_NOT: "Unused"\n'
    )

    issues = _requirement_issues(tmp_path, triggers, available, loc)

    if localised:
        assert issues == []
    else:
        assert len(issues) == 1
        assert "TST_negative_tt" in issues[0].message
        assert issues[0].severity == V.Severity.ERROR
        assert issues[0].category == "unlocalised-negated-trigger-tooltip"


def test_flag_inside_a_scripted_trigger_needs_loc(tmp_path):
    triggers = (
        "TST_can_apply = {\n"
        "\tNOT = { has_country_flag = TST_busy }\n"
        "\thidden_trigger = { has_country_flag = TST_hidden }\n"
        "}\n"
        "TST_outer = {\n\tTST_can_apply = yes\n}\n"
    )

    issues = _requirement_issues(tmp_path, triggers, "\t\t\tTST_outer = yes\n")

    assert len(issues) == 1
    assert "TST_busy" in issues[0].message
    assert "via scripted trigger TST_outer" in issues[0].message
    assert issues[0].category == "unlocalised-available-flag"
