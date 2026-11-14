"""Tests for validate_special_projects: unlock tooltips (#6382), inherit list (#2360)."""

import pytest
import validate_special_projects as V
from shared.suite import (
    assert_findings,
    build_validator,
    checks_called_by_run,
    run_validator,
    write_tree,
)

_PROJECTS = "common/special_projects/projects/p.txt"
_TECHS = "common/technologies/t.txt"
_FOCUSES = "common/national_focus/f.txt"


def _ways(trigger):
    return sorted(
        sorted(f"{kind}:{name}" for kind, name in way)
        for way in V.ways_in(trigger, 0, len(trigger))
    )


# case: (trigger body, ways in as sorted "kind:id" members)
_WAYS_CASES = {
    "single tech": ("has_tech = a", [["tech:a"]]),
    "members in a scope are needed together": (
        "FROM = { has_tech = a is_special_project_completed = sp:p }",
        [["project:p", "tech:a"]],
    ),
    "or splits into ways": (
        "OR = { has_tech = a AND = { has_tech = b has_completed_focus = f }"
        " NOT = { has_tech = c } }",
        [["focus:f", "tech:b"], ["tech:a"]],
    ),
    "nested or preserves alternatives": (
        "OR = { has_tech = a OR = { has_tech = b has_tech = c } }",
        [["tech:a"], ["tech:b"], ["tech:c"]],
    ),
    "or of non-members leaves the rest": (
        "OR = { original_tag = GER original_tag = FRA } has_tech = a",
        [["tech:a"]],
    ),
    "if chain branches are ways": (
        'if = { limit = { has_dlc = "X" } has_tech = a }'
        ' else_if = { limit = { has_dlc = "Y" } has_tech = b }'
        " else = { has_tech = c }",
        [["tech:a"], ["tech:b"], ["tech:c"]],
    ),
    "a lone if is needed and its limit is not": (
        "if = { limit = { has_tech = x } has_completed_focus = f }"
        " FROM = { has_tech = a }",
        [["focus:f", "tech:a"]],
    ),
    "a tag-only branch does not excuse others": (
        "if = { limit = { original_tag = CHI } always = yes }"
        " else = { has_tech = a }",
        [["tech:a"]],
    ),
    "negations are not needed": (
        "has_tech = a NOT = { has_tech = b } NOR = { has_tech = c }"
        " NAND = { has_tech = d } count_triggers = { amount = 1 has_tech = e }",
        [["tech:a"]],
    ),
}


@pytest.mark.parametrize(
    ("trigger", "expected"), _WAYS_CASES.values(), ids=list(_WAYS_CASES)
)
def test_ways_in(trigger, expected):
    assert _ways(trigger) == expected


def _rows(validator):
    return [
        f"{i.severity} {i.category} {i.file}:{i.line} {i.message}"
        for i in validator._issues
    ]


def _tooltip(project, key="SP_UNLOCK_PROJECT"):
    return f"custom_effect_tooltip = {{ localization_key = {key} PROJECT = {project} }}"


def _techs(*bodies):
    return "technologies = {\n" + "".join(bodies) + "}\n"


def _tech(name, *lines):
    reward = "\n".join(f"\t\t\t{line}" for line in lines)
    return f"\t{name} = {{\n\t\ton_research_complete = {{\n{reward}\n\t\t}}\n\t}}\n"


def _project(name, *lines):
    return f"{name} = {{\n" + "".join(f"\t{line}\n" for line in lines) + "}\n"


_NEEDS_A = _project("sp_a", "available = { FROM = { has_tech = a } }")
_MISSING_A = (
    f"warning sp-unlock-tooltip-missing {_PROJECTS}:1 special project sp_a is "
    "unlocked by a, but no SP_UNLOCK_PROJECT tooltip there names it"
)

# case: (files, findings as "severity category file:line message")
_TOOLTIP_CASES = {
    "announced": (
        {_PROJECTS: _NEEDS_A, _TECHS: _techs(_tech("a", _tooltip("sp_a")))},
        [],
    ),
    "missing": ({_PROJECTS: _NEEDS_A}, [_MISSING_A]),
    "one tooltip covers a way that needs two": (
        {
            _PROJECTS: _project(
                "sp_a", "available = { FROM = { has_tech = a has_tech = b } }"
            ),
            _TECHS: _techs(_tech("a", _tooltip("sp_a"))),
        },
        [],
    ),
    "misplaced": (
        {_PROJECTS: _NEEDS_A, _TECHS: _techs(_tech("c", _tooltip("sp_a")))},
        [
            f"warning sp-unlock-tooltip-misplaced {_TECHS}:4 c has an "
            "SP_UNLOCK_PROJECT tooltip for sp_a, which it does not unlock",
            _MISSING_A,
        ],
    ),
    "unknown project": (
        {_PROJECTS: _NEEDS_A, _TECHS: _techs(_tech("a", _tooltip("sp:sp_a")))},
        [
            (
                "misplaced",
                "a has an SP_UNLOCK_PROJECT tooltip for unknown special project sp:sp_a",
            ),
            _MISSING_A,
        ],
    ),
    "another tooltip key does not count": (
        {
            _PROJECTS: _NEEDS_A
            + _project("sp_b", "available = { FROM = { has_tech = a } }"),
            _TECHS: _techs(_tech("a", _tooltip("sp_a", "OTHER"), _tooltip("sp_b"))),
        },
        [_MISSING_A],
    ),
    "a commented tooltip does not count": (
        {_PROJECTS: _NEEDS_A, _TECHS: _techs(_tech("a", "# " + _tooltip("sp_a")))},
        [_MISSING_A],
    ),
    "a brace in a quoted string keeps the owner": (
        {
            _PROJECTS: _NEEDS_A,
            _TECHS: _techs(_tech("a", 'log = "{"', _tooltip("sp_a"))),
        },
        [],
    ),
    "visible counts toward the ways in": (
        {
            _PROJECTS: _project(
                "sp_a",
                "visible = { FROM = { has_tech = v } }",
                "available = { FROM = { has_tech = a } }",
            ),
            _TECHS: _techs(_tech("v", _tooltip("sp_a"))),
        },
        [],
    ),
    "focus owners and completions": (
        {
            _PROJECTS: "".join(
                _project(f"sp_{f}", f"available = {{ has_completed_focus = {f} }}")
                for f in ("f1", "f2", "f3")
            ),
            _FOCUSES: (
                "focus_tree = {\n\tfocus = {\n\t\tid = f1\n"
                f"\t\tcompletion_reward = {{ {_tooltip('sp_f1')} }}\n\t}}\n}}\n"
                "shared_focus = {\n\tid = f2\n"
                "\tcompletion_reward = { complete_special_project = sp:sp_f2 }\n}\n"
                "joint_focus = {\n\tid = f3\n"
                f"\tcompletion_reward = {{ {_tooltip('sp_f3')} }}\n}}\n"
            ),
        },
        [],
    ),
    "a parent project announces its child": (
        {
            _PROJECTS: (
                _project("sp_parent", f"project_output = {{ {_tooltip('sp_child')} }}")
                + _project(
                    "sp_child",
                    "special_project_parent = { sp_parent }",
                    "available = { FROM = { has_tech = a } }",
                )
                + _project("sp_orphan", "special_project_parent = { sp_parent }")
            ),
        },
        [],
    ),
}


@pytest.mark.parametrize(
    ("files", "expected"), _TOOLTIP_CASES.values(), ids=list(_TOOLTIP_CASES)
)
def test_unlock_tooltips(tmp_path, files, expected):
    write_tree(tmp_path, files)

    validator = build_validator(V.Validator, tmp_path)
    validator.validate_unlock_tooltips()

    assert_findings(_rows(validator), expected)


_INHERIT = V._INHERIT_FILE
_OPEN = "allowed = { always = yes }"


def _inherit(*projects, effect=V._INHERIT_EFFECT, comment=""):
    lines = "".join(f"\tcomplete_special_project = sp:{p}\n" for p in projects)
    return f"{effect} = {{\n{comment}{lines}}}\n"


_NOT_COPIED = (
    f"error sp-inherit-missing {_PROJECTS}:1 special project sp_a is open to "
    f"every country, but {V._INHERIT_EFFECT} does not copy it"
)

_LOCKED = "allowed = { original_tag = GER }"
_NO_EFFECT = (
    f"error sp-inherit-effect-missing {_INHERIT}:1 {V._INHERIT_EFFECT} is not defined"
)

# case: (project lines, inherit file text or None for no file, findings)
_INHERIT_CASES = {
    "listed": ([_OPEN], _inherit("sp_a"), []),
    "not listed": ([_OPEN], _inherit(), [_NOT_COPIED]),
    "no allowed block is open": ([], _inherit(), [_NOT_COPIED]),
    "dlc and game rule gates are open": (
        [
            'allowed = { OR = { has_dlc = "X" AND = { NOT = { has_game_rule = '
            "{ rule = r option = o } } } } }"
        ],
        _inherit(),
        [_NOT_COPIED],
    ),
    "an equals sign in a quoted string is not a trigger": (
        ['allowed = { has_dlc = "a = b" }'],
        _inherit(),
        [_NOT_COPIED],
    ),
    "a country project is skipped": ([_LOCKED], _inherit(), []),
    "a disabled project is skipped": (["allowed = { always = no }"], _inherit(), []),
    "always no closes a project even under NOT": (
        ["allowed = { NOT = { always = no } }"],
        _inherit(),
        [],
    ),
    "a comparison closes a project": (
        ["allowed = { date > 2010.1.1 }"],
        _inherit(),
        [],
    ),
    "every allowed block must be open": ([_OPEN, _LOCKED], _inherit(), []),
    "a country project in the list": (
        [_LOCKED],
        _inherit("sp_a"),
        [
            f"error sp-inherit-locked {_INHERIT}:2 {V._INHERIT_EFFECT} copies "
            "country or scenario project sp_a"
        ],
    ),
    "a commented line does not count": (
        [_OPEN],
        _inherit(comment="\t# complete_special_project = sp:sp_a\n"),
        [_NOT_COPIED],
    ),
    "unknown project": (
        [_OPEN],
        _inherit("sp_a", "sp_gone"),
        [
            f"error sp-inherit-unknown {_INHERIT}:3 {V._INHERIT_EFFECT} copies "
            "unknown special project sp_gone"
        ],
    ),
    "effect not defined": (
        [_OPEN],
        _inherit("sp_a", effect="other_effect"),
        [_NO_EFFECT],
    ),
    "effect file missing": ([_OPEN], None, [_NO_EFFECT]),
}


@pytest.mark.parametrize(
    ("lines", "inherit", "expected"), _INHERIT_CASES.values(), ids=list(_INHERIT_CASES)
)
def test_inherit_list(tmp_path, lines, inherit, expected):
    files = {_PROJECTS: _project("sp_a", *lines)}
    if inherit is not None:
        files[_INHERIT] = inherit
    write_tree(tmp_path, files)

    validator = run_validator(V.Validator, tmp_path)

    assert_findings(_rows(validator), expected)


def test_run_validations_calls_every_check(tmp_path, monkeypatch):
    called, checks = checks_called_by_run(
        build_validator(V.Validator, tmp_path), monkeypatch
    )
    assert called == checks
