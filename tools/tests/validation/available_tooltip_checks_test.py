"""Regressions for the three `available` block checks in validate_variables.

Inside a player-facing `available` block a bare check_variable renders no
tooltip line, a flag check renders its raw token unless a localisation key is
named after the flag, and a scripted trigger built from bare flag checks
renders nothing at all. Each must sit under a tooltip wrapper. A decision or
branch only the AI can reach is exempt: no human reads its requirement line.

`visible` is deliberately not covered: a failing visible hides the object
outright, so no tooltip renders either way.
"""

import pytest
import validate_variables as V
from shared.suite import variable_scan

# The AI-only exemption keys off the decisions path, so a test that wants it
# has to write the file where decisions actually live.
_DECISION_REL = "common/decisions/src.txt"
_FLAGGED = frozenset({"pak_raj_border_available"})

# Scan section -> a trigger that section reports when it sits bare in `available`.
_TRIGGERS = {
    "available": "check_variable = { my_var > 5 }",
    "scripted": "pak_raj_border_available = yes",
    "available_flags": "has_country_flag = ENG_deal_flag",
}
_ALL = tuple(_TRIGGERS)
_CHECK = ("available",)
_SCRIPTED = ("scripted",)
_CHECK_AND_FLAG = ("available", "available_flags")
_CHECK_AND_SCRIPTED = ("available", "scripted")


def _scan(
    tmp_path, section, text, ai_categories=frozenset(), rel="src.txt", flagged=_FLAGGED
):
    f = tmp_path / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    return variable_scan(
        f,
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


_BARE = "my_decision = {\n\tavailable = {\n\t\t{t}\n\t}\n}\n"
_AI_ONLY_SIBLINGS = (
    "some_category = {\n"
    "\thuman_decision = {\n"
    "\t\tavailable = {\n"
    "\t\t\t{t}\n"
    "\t\t}\n"
    "\t}\n"
    "\tfirst_ai_decision = {\n"
    "\t\tvisible = { is_ai = yes }\n"
    "\t\tavailable = {\n"
    "\t\t\t{t}\n"
    "\t\t}\n"
    "\t}\n"
    "\tsecond_ai_decision = {\n"
    "\t\tvisible = { is_ai = yes }\n"
    "\t\tavailable = {\n"
    "\t\t\t{t}\n"
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
_CASES = [
    ("bare", _ALL, _BARE, [3], {}),
    (
        "custom_trigger_tooltip",
        _ALL,
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
    (
        "hidden_trigger",
        _ALL,
        "my_decision = {\n\tavailable = {\n\t\thidden_trigger = { {t} }\n\t}\n}\n",
        [],
        {},
    ),
    (
        # 42 repo-wide uses wrap bare variable checks this way.
        "custom_override_tooltip",
        _ALL,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_override_tooltip = {\n"
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
        "commented",
        _ALL,
        "my_decision = {\n\tavailable = {\n\t\t# {t}\n\t}\n}\n",
        [],
        {},
    ),
    (
        # An unblanked `}` inside a quoted string would pop the stack early and
        # hide the real finding below it.
        "brace_in_log_string",
        _CHECK_AND_SCRIPTED,
        "my_decision = {\n"
        "\tcomplete_effect = {\n"
        '\t\tlog = "[GetDateText]: broken } brace"\n'
        "\t}\n"
        "\tavailable = {\n"
        "\t\t{t}\n"
        "\t}\n"
        "}\n",
        [6],
        {},
    ),
    (
        "single_line_available",
        _CHECK_AND_FLAG,
        "my_decision = {\n\tavailable = { {t} }\n}\n",
        [2],
        {},
    ),
    (
        "effect_limit",
        _CHECK_AND_FLAG,
        "my_decision = {\n"
        "\tcomplete_effect = {\n"
        "\t\tif = { limit = { {t} } add_political_power = 10 }\n"
        "\t}\n"
        "}\n",
        [],
        {},
    ),
    (
        "ai_will_do_modifier",
        _CHECK_AND_FLAG,
        "my_decision = {\n"
        "\tai_will_do = {\n"
        "\t\tbase = 10\n"
        "\t\tmodifier = { factor = 0 {t} }\n"
        "\t}\n"
        "}\n",
        [],
        {},
    ),
    # Nobody reads a requirement line on a decision no human player can see.
    (
        "ai_only_decision",
        _ALL,
        _in_decision("visible = { is_ai = yes }"),
        [],
        {"rel": _DECISION_REL},
    ),
    (
        "is_ai_in_available",
        _ALL,
        "some_category = {\n"
        "\tmy_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tis_ai = yes\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [],
        {"rel": _DECISION_REL},
    ),
    (
        "ai_only_category",
        _ALL,
        _in_decision("cost = 25"),
        [],
        {"rel": _DECISION_REL, "ai_categories": frozenset({"some_category"})},
    ),
    ("ai_only_if_branch", _ALL, _ai_split("{t}"), [], {}),
    (
        "human_else_branch",
        _ALL,
        _ai_split("has_war = no", else_body="{t}"),
        [8],
        {},
    ),
    (
        "is_ai_in_allowed",
        _CHECK,
        _in_decision("allowed = { is_ai = yes }"),
        [],
        {"rel": _DECISION_REL},
    ),
    (
        "is_ai_in_available_of_ai_category",
        _CHECK,
        "some_category = {\n"
        "\tmy_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tis_ai = yes\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [],
        {"rel": _DECISION_REL, "ai_categories": frozenset({"some_category"})},
    ),
    (
        "is_ai_nested_in_or",
        _CHECK,
        _in_decision("visible = { OR = { is_ai = yes is_debug = yes } }"),
        [5],
        {"rel": _DECISION_REL},
    ),
    (
        "ordinary_category_beside_an_ai_one",
        _CHECK,
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
        _CHECK,
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
        # The span walk used to land back on each decision's closing brace,
        # driving its depth count negative so only the first decision in a
        # category was ever tested.
        "ai_only_decisions_after_a_sibling",
        _CHECK,
        _AI_ONLY_SIBLINGS,
        [4],
        {"rel": _DECISION_REL},
    ),
    (
        # `common/decisions/categories/` holds the categories themselves, not
        # the category -> decision nesting the span walk assumes.
        "category_definition_file",
        _CHECK,
        "my_category = {\n"
        "\tvisible = { is_ai = yes }\n"
        "\tavailable = {\n"
        "\t\t{t}\n"
        "\t}\n"
        "}\n",
        [4],
        {"rel": "common/decisions/categories/cat.txt"},
    ),
    (
        # The span walk is decisions-only: a focus is not a category/decision pair.
        "focus_tree_with_is_ai",
        _CHECK,
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
        "anonymous_state_scope",
        _CHECK,
        "my_decision = {\n\tavailable = {\n\t\t828 = { {t} }\n\t}\n}\n",
        [3],
        {},
    ),
    (
        # `limit` at trigger level is not an effect limit: still player-facing.
        "if_limit_inside_available",
        _CHECK,
        "my_focus = {\n"
        "\tavailable = {\n"
        "\t\tif = {\n"
        "\t\t\tlimit = { is_ai = no }\n"
        "\t\t\t{t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        [5],
        {},
    ),
    (
        "wrapper_several_levels_above",
        _CHECK,
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
        "conditional_is_ai_branch",
        _SCRIPTED,
        _ai_split("{t}", limit="OR = { is_ai = yes tag = FOO }"),
        [5],
        {},
    ),
    ("is_ai_no_branch", _SCRIPTED, _ai_split("{t}", limit="is_ai = no"), [5], {}),
    (
        "else_if_ai_branch",
        _SCRIPTED,
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
        _SCRIPTED,
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
    (
        # A name that never resolved to an indexed scripted trigger is out of scope.
        "unknown_trigger_name",
        _SCRIPTED,
        "my_decision = {\n\tavailable = {\n\t\tsome_other_trigger = yes\n\t}\n}\n",
        [],
        {},
    ),
    ("no_flagged_names", _SCRIPTED, _BARE, [], {"flagged": frozenset()}),
]


@pytest.mark.parametrize(
    ("section", "script", "lines", "kwargs"),
    [
        pytest.param(section, script, lines, kwargs, id=f"{name}-{section}")
        for name, sections, script, lines, kwargs in _CASES
        for section in sections
    ],
)
def test_finding_lines(tmp_path, section, script, lines, kwargs):
    text = script.replace("{t}", _TRIGGERS[section])
    out = _scan(tmp_path, section, text, **kwargs)
    assert [finding[2] for finding in out] == lines


def test_bare_findings_name_the_problem(tmp_path):
    def message(section):
        text = _BARE.replace("{t}", _TRIGGERS[section])
        return _scan(tmp_path, section, text)[0][0]

    assert "renders no tooltip line" in message("available")
    assert "—" not in message("available")
    assert "pak_raj_border_available" in message("scripted")
    assert "resolves to a scripted trigger" in message("scripted")
    assert message("available_flags") == "ENG_deal_flag"


# --- check_variable only ----------------------------------------------------


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
    out = _scan(tmp_path, "available", text)
    assert [finding[2] for finding in out] == lines


# --- flags only -------------------------------------------------------------


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
    out = _scan(tmp_path, "available_flags", text)
    assert sorted(finding[0] for finding in out) == names


def test_global_flag_reports_its_scope(tmp_path):
    out = _scan(
        tmp_path,
        "available_flags",
        "my_decision = {\n\tavailable = {\n\t\thas_global_flag = GLOBAL_deal_flag\n\t}\n}\n",
    )
    assert len(out) == 1
    assert out[0][0] == "GLOBAL_deal_flag"
    assert out[0][3] == "global"


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
    out = _scan(tmp_path, "available_flags", text)
    assert len(out) == 1
    assert out[0][0] == flag
    assert out[0][4] == block


def test_hidden_trigger_in_cancel_trigger_ok(tmp_path):
    out = _scan(
        tmp_path,
        "available_flags",
        "my_mission = {\n"
        "\tcancel_trigger = {\n"
        "\t\thidden_trigger = { has_country_flag = a }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_only_unlocalised_flags_reported(tmp_path):
    loc = tmp_path / "localisation" / "english"
    loc.mkdir(parents=True)
    (loc / "test_l_english.yml").write_text(
        'l_english:\n ENG_known_flag:0 "Known"\n',
        encoding="utf-8-sig",
    )
    dec = tmp_path / "common" / "decisions"
    dec.mkdir(parents=True)
    (dec / "test.txt").write_text(
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thas_country_flag = ENG_known_flag\n"
        "\t\thas_country_flag = ENG_unknown_flag\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )

    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_unlocalised_available_flags()

    assert len(v._issues) == 1
    issue = v._issues[0]
    assert "ENG_unknown_flag" in issue.message
    assert "ENG_known_flag" not in issue.message
    assert issue.severity == V.Severity.ERROR
    assert issue.category == "unlocalised-available-flag"


# --- scripted trigger index -------------------------------------------------


def _index_names(tmp_path, text):
    trig_dir = tmp_path / "common" / "scripted_triggers"
    trig_dir.mkdir(parents=True)
    (trig_dir / "t.txt").write_text(text, encoding="utf-8")
    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    return v._collect_scripted_trigger_flag_names()


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
            "au_mandate_ready = {\n"
            "\tcustom_override_tooltip = {\n"
            "\t\ttooltip = african_union_available_mandate_tt\n"
            "\t\thas_global_flag = african_union_mandate_granted\n"
            "\t}\n"
            "}\n",
            "au_mandate_ready",
            False,
            id="custom_override_tooltip_in_body",
        ),
        pytest.param(
            "hidden_mandate = {\n"
            "\thidden_trigger = { has_global_flag = african_union_mandate_granted }\n"
            "}\n",
            "hidden_mandate",
            False,
            id="hidden_trigger_in_body",
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
    assert (name in _index_names(tmp_path, text)) is indexed


def _validator_issues(tmp_path, triggers, caller_rel, caller):
    trig_dir = tmp_path / "common" / "scripted_triggers"
    trig_dir.mkdir(parents=True)
    (trig_dir / "t.txt").write_text(triggers, encoding="utf-8")
    path = tmp_path / caller_rel
    path.parent.mkdir(parents=True)
    path.write_text(caller, encoding="utf-8")
    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_untooltipped_available_scripted_trigger()
    return v._issues


def test_validator_reports_a_bare_call_to_a_flagged_trigger(tmp_path):
    issues = _validator_issues(
        tmp_path,
        "pak_raj_border_available = {\n"
        "\tNOT = { has_global_flag = GLOBAL_pak_raj_border_war_active }\n"
        "}\n"
        "pak_raj_border_pair_valid = {\n"
        "\tis_puppet = no\n"
        "}\n",
        "common/decisions/test.txt",
        _BARE.replace("{t}", _TRIGGERS["scripted"]),
    )
    assert len(issues) == 1
    assert "pak_raj_border_available" in issues[0].message
    assert issues[0].severity == V.Severity.ERROR
    assert issues[0].category == "untooltipped-available-scripted-trigger"


def test_validator_accepts_a_bare_call_to_a_wrapped_trigger(tmp_path):
    issues = _validator_issues(
        tmp_path,
        _WRAPPED_AU_TRIGGER,
        "common/national_focus/au.txt",
        "shared_focus = {\n"
        "\tid = AFRICAN_UNION_shared_focus_create_investment_bank\n"
        "\tavailable = {\n"
        "\t\tcan_do_african_union_focus = yes\n"
        "\t}\n"
        "}\n",
    )
    assert issues == []
