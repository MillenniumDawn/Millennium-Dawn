"""Tests for the in-memory standardization entry point.

`standardize_api` is what the pre-commit router and validate_standardization.py
both drive, so routing lives in one place and neither of them has to write a
file to find out what the formatter would produce.
"""

from typing import cast

import pytest
import standardize_api
from standardize_api import (
    focus_content_changes,
    kind_for_path,
    standardize_lines,
    standardize_text,
)

_ROUTED = [
    ("common/national_focus/05_poland.txt", "focus"),
    ("events/Gulf.txt", "event"),
    ("common/decisions/Sudan.txt", "decision"),
    ("common/decisions/categories/MD_categories.txt", "decision"),
    ("common/ideas/Bosnian.txt", "idea"),
    ("common/military_industrial_organization/organizations/MD_ARG.txt", "mio"),
    ("common/military_industrial_organization/policies/_land_policies.txt", "mio"),
    ("common/technologies/infantry.txt", "technology"),
    ("history/countries/ARA - Arabistan.txt", "history"),
    ("common/ai_equipment/FRA_tank.txt", "indent"),
    ("common/characters/FRA.txt", "indent"),
    ("common/scripted_effects/FRA_political_leaders.txt", "indent"),
    ("common/scripted_triggers/99_FRA_scripted_triggers.txt", "indent"),
]

_UNROUTED = [
    "common/units/MD_land_units.txt",
    "events/Gulf.yml",
    # Localisation stays unrouted: its standardizer needs a full-mod content
    # index per run, which the in-memory checker cannot build per file.
    "localisation/english/MD_focus_SER_l_english.yml",
    "common/national_focus/notes.md",
]


@pytest.mark.parametrize("path,expected", _ROUTED)
def test_kind_for_path_routes_owned_paths(path, expected):
    assert kind_for_path(path) == expected


def test_routes_have_only_supported_standardizer_kinds():
    assert {kind for _prefix, kind in standardize_api.ROUTES} == {
        "focus",
        "event",
        "decision",
        "idea",
        "mio",
        "technology",
        "history",
        "indent",
    }


@pytest.mark.parametrize("path", _UNROUTED)
def test_kind_for_path_ignores_unowned_paths(path):
    assert kind_for_path(path) is None


def test_kind_for_path_accepts_absolute_and_windows_separators():
    assert kind_for_path("D:/checkout/common/ideas/Bosnian.txt") == "idea"
    assert kind_for_path("D:\\checkout\\events\\Gulf.txt") == "event"


_MESSY_EVENT = """country_event = {
\tid = test.1
\tis_triggered_only = yes
\ttitle = test.1.t
\tdesc = test.1.d
\toption = {
\t\tname = test.1.a
\t}
}
"""


def test_standardize_text_is_idempotent():
    once = standardize_text("event", _MESSY_EVENT)
    assert once is not None
    assert standardize_text("event", once) == once


def test_standardize_text_returns_none_when_no_block_matches():
    assert standardize_text("event", "# just a comment\n") is None


def test_standardize_text_touches_no_file(tmp_path):
    source = tmp_path / "events.txt"
    source.write_text(_MESSY_EVENT, encoding="utf-8")

    standardize_text("event", source.read_text(encoding="utf-8"))

    assert source.read_text(encoding="utf-8") == _MESSY_EVENT


def test_standardize_lines_matches_standardize_text():
    lines = cast(list[str], _MESSY_EVENT.splitlines(keepends=True))
    from_lines = standardize_lines("event", lines)

    assert from_lines is not None
    assert "".join(line + "\n" for line in from_lines) == standardize_text(
        "event", _MESSY_EVENT
    )


def test_focus_standardization_never_reports_no_op():
    # A focus file is always rewritten (spacing is normalized line by line), so
    # the focus branch has no "nothing matched" case for a checker to skip.
    assert standardize_text("focus", "focus_tree = {\n\tid = test\n}\n") is not None


_MESSY_HISTORY = """capital = 652

2000.1.1 = {
\tset_country_flag = TST_alpha
\tcomplete_special_project = sp:sp_space_program
}
"""


def test_history_text_reorders_dated_blocks_and_is_idempotent():
    once = standardize_text("history", _MESSY_HISTORY)
    assert once is not None
    assert once != _MESSY_HISTORY
    assert once.index("Special Projects") < once.index("Country Flags")
    assert standardize_text("history", once) == once


def test_history_text_accepts_a_mod_root(tmp_path):
    once = standardize_text("history", _MESSY_HISTORY, mod_root=str(tmp_path))
    assert once is not None
    assert standardize_text("history", once, mod_root=str(tmp_path)) == once


def test_history_text_returns_none_when_no_dated_block_matches():
    assert standardize_text("history", "# just a comment\n") is None


def test_history_text_fixes_tabs_inside_and_outside_dated_blocks():
    once = standardize_text(
        "history",
        "note = {\n    x = 1\n}\n\n2000.1.1 = {\nif = {\n"
        "limit = { always = yes }\n      set_country_flag = TST_alpha\n}\n}\n",
    )

    assert once is not None
    assert "note = {\n\tx = 1\n}\n" in once
    assert (
        "\tif = {\n\t\tlimit = { always = yes }\n"
        "\t\tset_country_flag = TST_alpha\n\t}\n" in once
    )
    assert standardize_text("history", once) == once


# case: kind, source -> comments the standardizer must keep
_KEPT_COMMENTS = {
    "decision and category opener": (
        "decision",
        "TST_cat = { # cat note\n\tTST_d = { # dec note\n\t\ticon = x\n\t}\n}\n",
        ["TST_cat = { # cat note\n", "\tTST_d = { # dec note\n"],
    ),
    "organization opener": (
        "mio",
        "TST_org = {\t\t# org note\n\tname = x\n}\n",
        ["TST_org = { # org note\n"],
    ),
    "history idea and add_ideas opener": (
        "history",
        "2000.1.1 = {\n\tadd_ideas = { # list note\n\t\tTST_a # idea note\n\t}\n}\n",
        ["\t\t# list note\n", "\t\tTST_a # idea note\n"],
    ),
}


@pytest.mark.parametrize(
    ("kind", "source", "kept"), _KEPT_COMMENTS.values(), ids=_KEPT_COMMENTS
)
def test_comments_on_an_opener_or_an_idea_survive(kind, source, kept):
    once = standardize_text(kind, source)

    assert once is not None
    for text in kept:
        assert text in once
    assert standardize_text(kind, once) == once


@pytest.mark.parametrize(
    "source",
    [
        "2000.1.1 = {\n\tadd_ideas = { # note\n\t\tTST_a\n\t}\n}\n",
        "2000.1.1 = {\n\tadd_ideas = {\n\t\tTST_a\n\t} # note\n}\n",
    ],
    ids=["opener", "closer"],
)
def test_comment_on_an_add_ideas_delimiter_keeps_the_braces_balanced(source):
    once = standardize_text("history", source)

    assert once == (
        "2000.1.1 = {\n\n\tadd_ideas = {\n\t\t# note\n"
        "\t\t# Country Content\n\t\tTST_a\n\t}\n}\n"
    )
    assert standardize_text("history", once) == once


def test_indent_text_fixes_only_tabs_and_spacing():
    messy = (
        "# Header {\n"
        "TST_effect = {\n"
        "    if = {limit={always = yes}\n"
        '\t\t\t\tlog = "keep  {  this"  # keep  this\n'
        "\n"
        "  }\n"
        "}\n"
    )
    once = standardize_text("indent", messy)

    assert once == (
        "# Header {\n"
        "TST_effect = {\n"
        "\tif = { limit = { always = yes }\n"
        '\t\tlog = "keep  {  this" # keep  this\n'
        "\n"
        "\t}\n"
        "}\n"
    )
    assert standardize_text("indent", once) == once


def _focus(body, focus_id="TST_first", kind="focus"):
    return f"{kind} = {{\n\tid = {focus_id}\n{body}\n}}\n"


# case: original property bodies, rewritten bodies, changed property (None is safe)
_FOCUS_CONTENT_CASES = {
    "root order and whitespace": ("x = 0\ny = 1", "y=1\nx=0", None),
    "touching delimiters": (
        "available={NOT={has_war=yes}}",
        "available = { NOT = { has_war = yes } }",
        None,
    ),
    "root AI factor": (
        "ai_will_do = { factor = 2 modifier = { factor = 0 always = yes } }",
        "ai_will_do = { base = 2 modifier = { factor = 0 always = yes } }",
        None,
    ),
    "existing base prevents factor rename": (
        "ai_will_do = { base = 2 factor = 3 }",
        "ai_will_do = { base = 2 base = 3 }",
        "ai_will_do",
    ),
    "implicit AI default": ("", "ai_will_do = { base = 1 }", None),
    "explicit defaults": (
        "cancel_if_invalid = yes\ncontinue_if_invalid = no\navailable_if_capitulated = no",
        "",
        None,
    ),
    "nondefault retained": ("cancel_if_invalid = no", "", "cancel_if_invalid"),
    "empty no-ops": (
        "available = {}\nbypass = {}\ncancel = {}\nmutually_exclusive = {}",
        "",
        None,
    ),
    "log-only effects": (
        'completion_reward = { log = "old" }\nselect_effect = {}\nbypass_effect = {}',
        "",
        None,
    ),
    "logging and comment braces": (
        "completion_reward = { add_political_power = 5 } # }\n# focus = {",
        'completion_reward = { log = "Focus TST_first }" add_political_power = 5 }',
        None,
    ),
    "duplicate blocks merged": (
        "available = { always = yes }\navailable = { has_war = no }",
        "available = { always = yes has_war = no }",
        None,
    ),
    "offset field order": (
        "offset = { trigger = { always = yes } y = 2 x = 1 }",
        "offset = { x = 1 y = 2 trigger = { always = yes } }",
        None,
    ),
    "scalar changed": ("x = 1", "x = 2", "x"),
    "reward value changed": (
        "completion_reward = { add_political_power = 5 }",
        "completion_reward = { add_political_power = 6 }",
        "completion_reward",
    ),
    "effect order changed": (
        "completion_reward = { set_temp_variable = { n = 5 } TST_effect = yes }",
        "completion_reward = { TST_effect = yes set_temp_variable = { n = 5 } }",
        "completion_reward",
    ),
    "scope changed": (
        "completion_reward = { ROOT = { add_political_power = 5 } }",
        "completion_reward = { FROM = { add_political_power = 5 } }",
        "completion_reward",
    ),
    "nested AI factor changed": (
        "ai_will_do = { base = 2 modifier = { factor = 0 always = yes } }",
        "ai_will_do = { base = 2 modifier = { base = 0 always = yes } }",
        "ai_will_do",
    ),
    "repeated prerequisite order changed": (
        "prerequisite = { focus = TST_a }\nprerequisite = { focus = TST_b }",
        "prerequisite = { focus = TST_b }\nprerequisite = { focus = TST_a }",
        "prerequisite",
    ),
    "repeated property dropped": (
        "icon = first\nicon = second",
        "icon = first",
        "icon",
    ),
    "quoted values preserved": (
        'available = { has_country_flag = "name # { first" }',
        'available = { has_country_flag = "name # { second" }',
        "available",
    ),
    "operator changed": ("available = { x > 1 }", "available = { x < 1 }", "available"),
    "math log retained": (
        "completion_reward = { set_variable = { n = { value = 2 log = 3 } } }",
        "completion_reward = { set_variable = { n = { value = 2 log = 4 } } }",
        "completion_reward",
    ),
}


@pytest.mark.parametrize(
    ("before", "after", "changed"),
    _FOCUS_CONTENT_CASES.values(),
    ids=_FOCUS_CONTENT_CASES,
)
def test_focus_content_preservation(before, after, changed):
    findings = focus_content_changes(_focus(before), _focus(after))

    assert findings == (
        [] if changed is None else [(1, f"TST_first: {changed} content changed")]
    )


_FOCUS_IDENTITY_CASES = {
    "ID": (_focus(""), _focus("", focus_id="TST_other")),
    "kind": (_focus(""), _focus("", kind="shared_focus")),
    "missing focus": (_focus(""), ""),
    "inline ID dropped": ("focus = { id = TST_first }", "focus = {}"),
    "order": (
        _focus("") + _focus("", focus_id="TST_second"),
        _focus("", focus_id="TST_second") + _focus(""),
    ),
}


@pytest.mark.parametrize(
    ("before", "after"), _FOCUS_IDENTITY_CASES.values(), ids=_FOCUS_IDENTITY_CASES
)
def test_focus_identity_changes_are_reported(before, after):

    assert focus_content_changes(before, after) == [
        (0, "focus IDs, kinds, or order changed")
    ]


@pytest.mark.parametrize(
    ("before", "after"),
    [("focus = { id = TST_first", ""), ("", "focus = { id = TST_first")],
    ids=["source", "rewrite"],
)
def test_unbalanced_focus_cannot_pass_preservation(before, after):
    with pytest.raises(ValueError, match="unbalanced focus block"):
        focus_content_changes(before, after)


def test_focus_headers_inside_strings_do_not_define_focuses():
    source = 'header = "focus = { id = TST_fake }"\n' + _focus("")

    assert focus_content_changes(source, _focus("")) == []
