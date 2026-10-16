"""Idea validator: the parser and its quality findings, the reference scans,
and the undefined-reference, quality, localisation, icon, category-frame,
unused and bonus-stack checks, then the run and its command line.

The pool workers are called directly with the text and files the validator
would hand them. The checks run on a miniature mod under tmp_path.
"""

import argparse
import os
import runpy
import sys

import pytest
import shared_utils
import validate_ideas
from shared.suite import checks_called_by_run
from shared.suite import issue_rows as _findings
from shared.suite import write_under as _write
from validate_ideas import (
    _META_PREFIX_SENTINEL,
    IdeaIssue,
    SpriteSet,
    Validator,
    _add_extra_args,
    _check_file_for_refs,
    _extract_idea_refs_from_blocks,
    _extract_swap_idea_refs,
    _idea_categories_frame_count,
    _is_placeholder_texture,
    _missing_icon_message,
    _on_add_is_log_only,
    _parse_ideas_from_file,
    _parse_ideas_from_text,
    _scan_idea_refs,
    _scan_idea_refs_for_unused,
    _weekly_modifier_issues,
)
from validator_batches import BATCHES
from validator_common import Severity, casefold_index

NO_CATEGORIES: frozenset = frozenset()
SLOTLESS = frozenset({"country", "hidden_ideas"})

IDEA_TAGS = """idea_categories = {
\thidden_ideas = { hidden = yes }
\tcountry = { type = national_spirit }
\tpolitical_advisor = { slot = political_advisor }
}
"""


def _validator(root, **kwargs):
    kwargs.setdefault("unused_ideas", False)
    return Validator(str(root), use_colors=False, workers=1, **kwargs)


def _ideas(category, *ideas):
    """An ideas file with one category holding the given idea bodies."""
    return "ideas = {\n\t" + category + " = {\n" + "\n".join(ideas) + "\n\t}\n}\n"


def _idea(name, *lines):
    body = "".join("\t\t\t" + line + "\n" for line in lines)
    return "\t\t" + name + " = {\n" + body + "\t\t}"


def _issue_types(text, slotless=SLOTLESS):
    return {issue.issue_type for issue in _parse_ideas_from_text(text, slotless)[1]}


# case: (idea files, grant call sites, expected (file, line, message fragment))
_WEEKLY_MODIFIER_CASES = {
    "war support on permanent country idea": (
        {
            "common/ideas/test.txt": _ideas(
                "country",
                _idea("PERMANENT", "modifier = { weekly_war_support = 0.01 }"),
            )
        },
        {
            "common/national_focus/test.txt": (
                "completion_reward = { add_ideas = PERMANENT }"
            )
        },
        [
            ("common/ideas/test.txt", 3, "weekly_war_support"),
            ("common/ideas/test.txt", 3, "permanent grant"),
        ],
    ),
    "stability on permanent list grant": (
        {
            "common/ideas/test.txt": _ideas(
                "country",
                _idea("PERMANENT", "modifier = { weekly_stability = 0.01 }"),
            )
        },
        {"history/countries/AAA.txt": "add_ideas = { PERMANENT }"},
        [
            ("common/ideas/test.txt", 3, "weekly_stability"),
            ("common/ideas/test.txt", 3, "permanent grant"),
        ],
    ),
    "timed-only country idea is excluded": (
        {
            "common/ideas/test.txt": _ideas(
                "country",
                _idea("TEMPORARY", "modifier = { weekly_stability = 0.01 }"),
            )
        },
        {
            "events/test.txt": (
                "add_timed_idea = { idea = TEMPORARY days = 30 }\n"
                "effect_tooltip = { add_ideas = TEMPORARY }"
            )
        },
        [],
    ),
    "tooltip-only grant does not establish permanence": (
        {
            "common/ideas/test.txt": _ideas(
                "country",
                _idea("TOOLTIP_ONLY", "modifier = { weekly_stability = 0.01 }"),
            )
        },
        {"events/test.txt": "effect_tooltip = { add_ideas = TOOLTIP_ONLY }"},
        [
            (
                "common/ideas/test.txt",
                3,
                "no statically resolved grant",
            )
        ],
    ),
    "mixed timed and permanent usage is advisory": (
        {
            "common/ideas/test.txt": _ideas(
                "country",
                _idea("MIXED", "modifier = { weekly_war_support = 0.01 }"),
            )
        },
        {
            "events/test.txt": (
                "add_timed_idea = { idea = MIXED days = 30 }\nadd_idea = MIXED"
            )
        },
        [("common/ideas/test.txt", 3, "mixed timed and permanent grants")],
    ),
    "nested modifier and unrelated categories are ignored": (
        _ideas(
            "country",
            _idea("NESTED", "on_add = { modifier = { weekly_stability = 1 } }"),
        )
        + _ideas(
            "political_advisor",
            _idea("ADVISOR", "modifier = { weekly_stability = 1 }"),
        ),
        {"events/test.txt": "add_idea = NESTED\nadd_idea = ADVISOR"},
        [],
    ),
    "targeted modifier is not a national idea modifier": (
        {
            "common/ideas/test.txt": _ideas(
                "country",
                _idea(
                    "TARGETED",
                    "targeted_modifier = { weekly_stability = 0.01 }",
                ),
            )
        },
        {"events/test.txt": "add_idea = TARGETED"},
        [],
    ),
    "unresolved grant remains advisory": (
        {
            "common/ideas/test.txt": _ideas(
                "country",
                _idea("DYNAMIC", "modifier = { weekly_stability = 0.01 }"),
            )
        },
        {"common/scripted_effects/test.txt": "add_idea = [dynamic_idea]"},
        [("common/ideas/test.txt", 3, "no statically resolved grant")],
    ),
}


@pytest.mark.parametrize(
    "idea_files,script_files,expected",
    _WEEKLY_MODIFIER_CASES.values(),
    ids=_WEEKLY_MODIFIER_CASES.keys(),
)
def test_weekly_modifiers_require_a_permanent_national_idea(
    idea_files, script_files, expected
):
    if isinstance(idea_files, str):
        idea_files = {"common/ideas/test.txt": idea_files}
    findings = _weekly_modifier_issues(idea_files, script_files)
    assert len(findings) == len({(path, line) for path, line, _ in expected})
    assert all(
        any(
            (path, line) == (expected_path, expected_line) and fragment in message
            for path, line, message in findings
        )
        for expected_path, expected_line, fragment in expected
    )


# ---- parsing ---------------------------------------------------------------------

# case: (ideas file text, {idea: (category, name override, picture)})
_PARSE_CASES = {
    "picture and name fields": (
        _ideas(
            "country",
            _idea(
                "WITH_pic",
                "picture = some_pic",
                "modifier = { stability_factor = 0.05 }",
            ),
            _idea("NO_pic", "modifier = { stability_factor = 0.05 }"),
            _idea("RENAMED", "name = SHARED_key", "picture = pic_two"),
        ),
        {
            "WITH_pic": ("country", None, "some_pic"),
            "NO_pic": ("country", None, None),
            "RENAMED": ("country", "SHARED_key", "pic_two"),
        },
    ),
    "hyphen in a picture": (
        _ideas("materiel_manufacturer", _idea("CO", "picture = Colt-Defense")),
        {"CO": ("materiel_manufacturer", None, "Colt-Defense")},
    ),
    "dynamic picture": (
        _ideas("country", _idea("DYNAMIC", "picture = [GetIcon]")),
        {"DYNAMIC": ("country", None, "[GetIcon]")},
    ),
    "schema key at idea level is not an idea": (
        _ideas(
            "country",
            "\t\tmodifier = { stability_factor = 0.1 }",
            _idea("REAL_idea", "picture = x"),
        ),
        {"REAL_idea": ("country", None, "x")},
    ),
    "nested effects and braces in log strings": (
        _ideas(
            "country",
            _idea(
                "FIRST_idea",
                "on_add = {",
                '\tlog = "brace } and picture = fake"',
                "\tcreate_equipment_variant = {",
                '\t\tname = "Equipment Name"',
                "\t}",
                "}",
                'picture = "first"',
            ),
            "\t\tSECOND_idea = { picture = second }",
        ),
        {
            "FIRST_idea": ("country", None, "first"),
            "SECOND_idea": ("country", None, "second"),
        },
    ),
    "only the ideas root is read": (
        "other = {\n\tcountry = {\n\t\tFAKE_idea = { picture = x }\n\t}\n}\n"
        + _ideas("country", _idea("REAL_idea", "picture = x")),
        {"REAL_idea": ("country", None, "x")},
    ),
    "a commented idea is not an idea": (
        _ideas(
            "country",
            "\t\t# FAKE_idea = { picture = x }",
            _idea("REAL_idea", "picture = x"),
        ),
        {"REAL_idea": ("country", None, "x")},
    ),
}


@pytest.mark.parametrize(("text", "defined"), _PARSE_CASES.values(), ids=_PARSE_CASES)
def test_parse_ideas(text, defined):
    assert _parse_ideas_from_text(text, NO_CATEGORIES) == (defined, [])


@pytest.mark.parametrize("compact", (False, True), ids=["one per line", "one line"])
def test_inline_ideas_keep_their_own_fields_and_issue_lines(compact):
    lines = [
        "ideas = {",
        "\tcountry = {",
        "\t\tFIRST_idea = { name = shared_key picture = first }",
        "\t\tEMPTY_idea = {}",
        "\t\tSECOND_idea = { picture = second cancel = { always = no } }",
        "\t}",
        "}",
    ]
    text = " ".join(lines) if compact else "\n".join(lines)

    defined, issues = _parse_ideas_from_text(text, NO_CATEGORIES)

    assert defined == {
        "FIRST_idea": ("country", "shared_key", "first"),
        "EMPTY_idea": ("country", None, None),
        "SECOND_idea": ("country", None, "second"),
    }
    assert [(i.idea_name, i.issue_type, i.line) for i in issues] == [
        ("SECOND_idea", "cancel-always-no", 1 if compact else 5),
    ]


def test_empty_ideas_file_parses_to_nothing(tmp_path):
    path = _write(tmp_path, "common/ideas/empty.txt", "")
    assert _parse_ideas_from_file(str(path), str(tmp_path), NO_CATEGORIES) == ({}, [])


@pytest.mark.parametrize("gate", ("allowed", "available"))
def test_category_set_is_part_of_the_parser_cache_key(tmp_path, gate):
    idea_file = _write(
        tmp_path,
        "common/ideas/test.txt",
        _ideas("custom_slotless", _idea("my_idea", f"{gate} = {{ always = yes }}")),
    )

    _defined, first = _parse_ideas_from_file(str(idea_file), str(tmp_path), frozenset())
    _defined, second = _parse_ideas_from_file(
        str(idea_file), str(tmp_path), frozenset({"custom_slotless"})
    )

    assert first == []
    assert {issue.issue_type for issue in second} == {f"{gate}-in-slotless-category"}


# ---- quality findings from the parser --------------------------------------------

_SLOTLESS_ALLOWED = "allowed-in-slotless-category"
_SLOTLESS_AVAILABLE = "available-in-slotless-category"
_BARE_TAG = "tag-not-original-tag"
_REDUNDANT_TAG = "redundant-tag-and-original-tag"

# `country` and `hidden_ideas` have no slot, so add_idea is the only way in and it
# consults neither allowed nor available. allowed_civil_war and cancel stay live.
# `tag =` breaks for civil-war split-offs, whose runtime tag changes.
# case: (category, idea body lines, issue types)
_QUALITY_CASES = {
    "allowed in country": (
        "country",
        ["allowed = { original_tag = ISR }"],
        {_SLOTLESS_ALLOWED},
    ),
    "available in country": (
        "country",
        ["available = { emerging_communist_state_are_in_power = yes }"],
        {_SLOTLESS_AVAILABLE},
    ),
    "allowed in hidden ideas": (
        "hidden_ideas",
        ["allowed = {", "\thas_country_flag = some_flag", "}"],
        {_SLOTLESS_ALLOWED},
    ),
    "available in hidden ideas": (
        "hidden_ideas",
        ["available = {", "\thas_country_flag = some_flag", "}"],
        {_SLOTLESS_AVAILABLE},
    ),
    "allowed in a slotted category": (
        "tank_manufacturer",
        ["allowed = { original_tag = ISR }"],
        set(),
    ),
    "available in a slotted category": (
        "tank_manufacturer",
        ["available = { original_tag = ISR }"],
        set(),
    ),
    "no gate": ("country", ["picture = GFX_idea_x"], set()),
    "allowed_civil_war alone": (
        "country",
        ["allowed_civil_war = { always = yes }"],
        set(),
    ),
    "cancel alone": ("country", ["cancel = { always = yes }"], set()),
    "both gates": (
        "country",
        ["allowed = { original_tag = ISR }", "available = { always = yes }"],
        {_SLOTLESS_ALLOWED, _SLOTLESS_AVAILABLE},
    ),
    # A slotless idea never gets two findings for the same block.
    "always-no allowed in country": (
        "country",
        ["allowed = { always = no }"],
        {_SLOTLESS_ALLOWED},
    ),
    # Slotted ideas are grouped by slot name, so check_common_mistakes.py owns this.
    "always-no allowed in a slot": (
        "political_advisor",
        ["allowed = { always = no }"],
        set(),
    ),
    "bare tag": ("political_reforms", ["allowed = { tag = ISR }"], {_BARE_TAG}),
    "original tag": ("political_reforms", ["allowed = { original_tag = ISR }"], set()),
    "runtime tag": ("political_reforms", ["allowed = { tag = ISR_CW_0 }"], {_BARE_TAG}),
    # A nested block before `tag =` must not end the allowed block early.
    "tag after a nested block": (
        "political_reforms",
        ["allowed = {", "\tNOT = { has_global_flag = x }", "\ttag = ISR", "}"],
        {_BARE_TAG},
    ),
    "tag and original tag together": (
        "political_reforms",
        ["allowed = { original_tag = ISR tag = ISR }"],
        {_REDUNDANT_TAG},
    ),
    # Alternatives in OR branches are a shared idea, not a redundant pair.
    "tag and original tag in different branches": (
        "political_reforms",
        [
            "allowed = {",
            "\tOR = {",
            "\t\toriginal_tag = ISR",
            "\t\ttag = USA",
            "\t}",
            "}",
        ],
        {_BARE_TAG},
    ),
    "bare tag in a slotless category": (
        "country",
        ["allowed = { tag = ISR }"],
        {_SLOTLESS_ALLOWED, _BARE_TAG},
    ),
}


@pytest.mark.parametrize(
    ("category", "lines", "expected"), _QUALITY_CASES.values(), ids=_QUALITY_CASES
)
def test_quality_issue_types(category, lines, expected):
    assert _issue_types(_ideas(category, _idea("my_idea", *lines))) == expected


def test_cancel_always_no_and_log_only_on_add_carry_the_idea_line():
    text = _ideas(
        "country",
        _idea("CANCEL_idea", "cancel = { always = no }", "picture = x"),
        _idea(
            "LOG_idea",
            "on_add = {",
            '\tlog = "[GetDateText]: traced"',
            "}",
            "picture = x",
        ),
    )
    issues = _parse_ideas_from_text(text, NO_CATEGORIES)[1]
    assert [(i.idea_name, i.issue_type, i.line) for i in issues] == [
        ("CANCEL_idea", "cancel-always-no", 3),
        ("LOG_idea", "on-add-log-only", 7),
    ]


def test_equipment_bonus_without_instant_is_recorded_per_equipment():
    text = (
        "ideas = {\n\tcountry = {\n\t\tBONUS_idea = {\n\t\t\tequipment_bonus = {\n"
        "\t\t\t\tinfantry_weapons_type = { soft_attack = 0.05 instant = yes }\n"
        "\t\t\t\tartillery_equipment = {\n\t\t\t\t\tsoft_attack = 0.05\n\t\t\t\t}\n"
        "\t\t\t\tinstant_tank = { build_cost_ic = -0.1 instant = no }\n"
        "\t\t\t}\n\t\t}\n\t}\n}\n"
    )

    issues = _parse_ideas_from_text(text, NO_CATEGORIES)[1]

    assert [(i.idea_name, i.issue_type, i.line, i.detail) for i in issues] == [
        ("BONUS_idea", "equipment-bonus-not-instant", 6, "artillery_equipment"),
        ("BONUS_idea", "equipment-bonus-not-instant", 9, "instant_tank"),
    ]


# case: (idea text, on_add holds only logs)
_ON_ADD_CASES = {
    "log only": ('idea = {\n\ton_add = {\n\t\tlog = "x"\n\t}\n}', True),
    "log with a blank and a comment": (
        'idea = {\n\ton_add = {\n\n\t\t# note\n\t\tlog = "x"\n\t}\n}',
        True,
    ),
    "log and an effect": (
        'idea = {\n\ton_add = {\n\t\tlog = "x"\n\t\tadd_stability = 0.05\n\t}\n}',
        False,
    ),
    "no on_add": ("idea = {\n\tpicture = x\n}", False),
    "a second on_add with effects": (
        'idea = {\n\ton_add = {\n\t\tlog = "x"\n\t}\n'
        "\ton_add = {\n\t\tadd_stability = 0.05\n\t}\n}",
        False,
    ),
}


@pytest.mark.parametrize(
    ("text", "expected"), _ON_ADD_CASES.values(), ids=_ON_ADD_CASES
)
def test_on_add_is_log_only(text, expected):
    assert _on_add_is_log_only(text) is expected


# ---- reference scans -----------------------------------------------------------


def test_block_refs_skip_assignments_comments_and_nested_blocks():
    text = """
    add_ideas = {
        first_block_idea
        idea = yes
        if = {
            limit = { has_country_flag = enabled }
            add_ideas = nested_idea
        }
        # commented_out_idea
        second_block_idea
    }
    remove_ideas = {
        modifier = { factor = 2 }
        third_block_idea fourth_block_idea
    }
    add_ideas = { fifth_block_idea }
    """
    refs = set(_scan_idea_refs(text))

    assert refs >= {
        "first_block_idea",
        "second_block_idea",
        "third_block_idea",
        "fourth_block_idea",
        "fifth_block_idea",
        "nested_idea",
    }
    assert refs.isdisjoint(
        {
            "idea",
            "yes",
            "if",
            "limit",
            "enabled",
            "commented_out_idea",
            "modifier",
            "factor",
            "2",
        }
    )


def test_single_line_and_swap_refs_are_scanned():
    text = (
        "remove_ideas = OLD_spirit\n"
        "has_idea = NKO_Marxism-Leninism\n"
        "swap_ideas = { remove_idea = SWAP_old add_idea = SWAP_new }\n"
    )
    assert set(_scan_idea_refs(text)) >= {
        "OLD_spirit",
        "NKO_Marxism-Leninism",
        "SWAP_old",
        "SWAP_new",
    }


def test_quoted_and_nested_entries_do_not_swallow_sibling_names():
    text = (
        "add_ideas = {\n"
        '\t"QUOTED_spirit"\n'
        "\tif = {\n"
        '\t\tlimit = { has_country_flag = "brace } inside" }\n'
        "\t\t# a skipped comment\n"
        "\t}\n"
        "\tPLAIN_spirit\n"
        "}\n"
    )
    assert _extract_idea_refs_from_blocks(text) == ["QUOTED_spirit", "PLAIN_spirit"]


def test_unclosed_add_ideas_block_yields_no_refs():
    assert _extract_idea_refs_from_blocks("add_ideas = {\n\tSPIRIT_one\n") == []


def test_swap_block_refs_are_collected():
    text = (
        "focus = {\n\tcompletion_reward = {\n\t\tswap_ideas = {\n"
        "\t\t\tremove_idea = OLD_spirit\n\t\t\tadd_idea = NEW_spirit\n"
        "\t\t}\n\t}\n}\n"
    )
    assert _extract_swap_idea_refs(text) == ["OLD_spirit", "NEW_spirit"]


def _ref_check(path, defined, tmp_path):
    return _check_file_for_refs(
        (str(path), frozenset(defined), casefold_index(defined), str(tmp_path))
    )


def test_undefined_and_case_mismatched_refs_are_separated(tmp_path):
    path = _write(
        tmp_path,
        "events/MD_test.txt",
        "option = {\n"
        "\thas_idea = KNOWN_idea\n"
        "\thas_idea = known_idea\n"
        "\tadd_ideas = missing_idea\n"
        "\tadd_ideas = generic_spirit\n"
        "\tadd_ideas = var:dynamic_token\n"
        "\tadd_ideas = tribute_[ROOTTAG]\n"
        "\tadd_ideas = 420\n"
        "\tadd_ideas = ab\n"
        "}\n",
    )

    assert _ref_check(path, {"KNOWN_idea"}, tmp_path) == [
        "MD_test.txt: case-mismatch idea reference 'known_idea' — defined as "
        "'KNOWN_idea' (works on Windows, fails on Linux)",
        "MD_test.txt: undefined idea reference 'missing_idea'",
    ]


@pytest.mark.parametrize(
    "relative, body",
    [
        ("gfx/notes.txt", "has_idea = missing_idea\n"),
        ("events/empty.txt", ""),
        ("events/other.txt", "add_stability = 0.05\n"),
    ],
    ids=["ignored directory", "empty file", "no idea keyword"],
)
def test_ref_check_finds_nothing_to_scan(tmp_path, relative, body):
    assert _ref_check(_write(tmp_path, relative, body), set(), tmp_path) == []


_UNUSED_SCAN_CASES = {
    "every keyword form": (
        "grant = {\n"
        "\tcompletion_reward = { add_ideas = SPIRIT_one }\n"
        "\tadd_ideas = { SPIRIT_two SPIRIT_three }\n"
        "\tadd_timed_idea = { idea = SPIRIT_four days = 30 }\n"
        "\tswap_ideas = { remove_idea = SPIRIT_five add_idea = SPIRIT_six }\n"
        "\thas_idea = SPIRIT_seven\n"
        "\tadd_Ideas = SPIRIT_eight\n"
        "}\n",
        {
            f"SPIRIT_{n}"
            for n in ("one", "two", "three", "four", "five", "six", "seven", "eight")
        },
        set(),
    ),
    "meta prefix": (
        "x = { add_timed_idea = { idea = tribute_idea_[ROOTTAG] days = 30 } }\n",
        {_META_PREFIX_SENTINEL + "tribute_idea_"},
        set(),
    ),
    "literal tokens": (
        "setup = {\n"
        "\tadd_to_array = { global.ideas = token:SPIRIT_one }\n"
        "\tadd_to_array = { array = global.ideas value = token:SPIRIT_two }\n"
        "\tset_temp_variable = { idea = token:SPIRIT_three-four }\n"
        "\tadd_to_array = { global.ideas = token:SPIRIT_one_extra }\n"
        "\t# add_to_array = { global.ideas = token:DEAD_spirit }\n"
        "}\n",
        {"SPIRIT_one", "SPIRIT_two", "SPIRIT_three-four", "SPIRIT_one_extra"},
        {"SPIRIT_three", "DEAD_spirit"},
    ),
    "a definition is not a reference": (
        "DEAD_idea = {\n picture = x\n modifier = { stability_factor = 0.1 }\n}\n",
        set(),
        {"DEAD_idea"},
    ),
}


@pytest.mark.parametrize(
    ("body", "found", "absent"), _UNUSED_SCAN_CASES.values(), ids=_UNUSED_SCAN_CASES
)
def test_unused_scan_references(tmp_path, body, found, absent):
    path = _write(tmp_path, "common/scripted_effects/grants.txt", body)
    refs = set(_scan_idea_refs_for_unused((str(path), str(tmp_path))))
    assert found <= refs
    assert not refs & absent


@pytest.mark.parametrize(
    "relative, body",
    [("gfx/notes.txt", "add_ideas = SPIRIT_one\n"), ("common/empty.txt", "")],
    ids=["ignored directory", "empty file"],
)
def test_unused_scan_finds_nothing_to_scan(tmp_path, relative, body):
    path = _write(tmp_path, relative, body)
    assert _scan_idea_refs_for_unused((str(path), str(tmp_path))) == []


# ---- icons -----------------------------------------------------------------------

SPRITES = SpriteSet.build(
    {"GFX_idea_known_pic", "GFX_idea_AUTO", "GFX_idea_shared_key", "GFX_idea_CasedPic"},
    {"GFX_idea_wip_pic"},
)
HIDDEN = frozenset({"hidden_ideas"})

# case: (idea, category, name override, picture, sprites, message or None)
_ICON_CASES = {
    "picture defined": ("AUTO", "country", None, "known_pic", SPRITES, None),
    "picture undefined": (
        "X",
        "country",
        None,
        "nope",
        SPRITES,
        "X: picture = nope -> GFX_idea_nope (undefined)",
    ),
    "placeholder art": (
        "X",
        "country",
        None,
        "wip_pic",
        SPRITES,
        "X: picture = wip_pic -> GFX_idea_wip_pic (placeholder art)",
    ),
    "case mismatch": (
        "X",
        "country",
        None,
        "casedpic",
        SPRITES,
        "X: picture = casedpic -> GFX_idea_casedpic "
        "(case mismatch, defined as GFX_idea_CasedPic)",
    ),
    # A placeholder sprite still anchors the case-mismatch report.
    "case mismatch on a placeholder": (
        "X",
        "country",
        None,
        "wipcased",
        SpriteSet.build(set(), {"GFX_idea_WipCased"}),
        "X: picture = wipcased -> GFX_idea_wipcased "
        "(case mismatch, defined as GFX_idea_WipCased)",
    ),
    "auto-icon defined": ("AUTO", "country", None, None, SPRITES, None),
    "auto-icon undefined": (
        "LONELY",
        "country",
        None,
        None,
        SPRITES,
        "LONELY: auto-icon GFX_idea_LONELY (undefined)",
    ),
    "name override sprite": ("X", "country", "shared_key", None, SPRITES, None),
    "hidden category": ("X", "hidden_ideas", None, "nope", SPRITES, None),
    "character token": ("X", "character", None, None, SPRITES, None),
    "dynamic picture": ("X", "country", None, "[GetIcon]", SPRITES, None),
}


@pytest.mark.parametrize(
    ("idea", "category", "override", "picture", "sprites", "expected"),
    _ICON_CASES.values(),
    ids=_ICON_CASES,
)
def test_missing_icon_message(idea, category, override, picture, sprites, expected):
    assert (
        _missing_icon_message(idea, category, override, picture, sprites, HIDDEN)
        == expected
    )


@pytest.mark.parametrize(
    "texture, expected",
    [
        ("gfx/interface/ideas/WIP_idea.dds", True),
        ("gfx\\interface\\ideas\\wip_idea.dds", True),
        ("gfx/interface/ideas/politics/large_power.dds", False),
    ],
    ids=["upper case", "backslashes", "real art"],
)
def test_placeholder_texture(texture, expected):
    assert _is_placeholder_texture(texture) is expected


def _sprite_set(tmp_path, monkeypatch, gfx, manifest=frozenset(), vanilla_files=()):
    if gfx:
        _write(tmp_path, "interface/ideas.gfx", gfx)
    monkeypatch.setattr(
        "validate_gfx_references._vanilla_gfx_files", lambda: list(vanilla_files)
    )
    monkeypatch.setattr(
        "validate_gfx_references._load_vanilla_sprite_manifest", lambda: manifest
    )
    return _validator(tmp_path)._build_idea_sprite_set()


_WIP_SPRITE = (
    'spriteType = {{\n name = "{name}"\n'
    ' texturefile = "gfx/interface/ideas/WIP_idea.dds"\n}}\n'
)


def test_sprite_on_placeholder_art_is_not_defined(tmp_path, monkeypatch):
    sprites = _sprite_set(
        tmp_path, monkeypatch, _WIP_SPRITE.format(name="GFX_idea_todo")
    )
    assert sprites.placeholders == frozenset({"GFX_idea_todo"})
    assert "GFX_idea_todo" not in sprites.defined


# The mod definition wins at load time, so a vanilla sprite of the same name
# does not rescue an idea pointed at placeholder art.
def test_placeholder_shadowing_a_vanilla_name_still_reports(tmp_path, monkeypatch):
    sprites = _sprite_set(
        tmp_path,
        monkeypatch,
        _WIP_SPRITE.format(name="GFX_idea_shadowed"),
        manifest=frozenset({"GFX_idea_shadowed"}),
    )
    assert (
        _missing_icon_message("TEST_idea", "country", None, "shadowed", sprites, HIDDEN)
        == "TEST_idea: picture = shadowed -> GFX_idea_shadowed (placeholder art)"
    )


@pytest.mark.parametrize(
    "gfx, manifest",
    [
        ('spriteType = { name = "GFX_idea_resolved" }', frozenset()),
        (None, frozenset({"GFX_idea_resolved"})),
    ],
    ids=["mod gfx", "vanilla manifest"],
)
def test_sprite_index_resolves_mod_and_manifest_sprites(
    tmp_path, monkeypatch, gfx, manifest
):
    sprites = _sprite_set(tmp_path, monkeypatch, gfx, manifest=manifest)
    assert "GFX_idea_resolved" in sprites.defined


def test_sprite_index_reads_vanilla_gfx_files(tmp_path, monkeypatch):
    vanilla = _write(
        tmp_path,
        "vanilla/interface/core.gfx",
        'spriteType = { name = "GFX_idea_vanilla_pic" }\n',
    )
    sprites = _sprite_set(
        tmp_path,
        monkeypatch,
        'spriteType = { name = "GFX_idea_mod" }\n',
        vanilla_files=[str(vanilla)],
    )
    assert {"GFX_idea_mod", "GFX_idea_vanilla_pic"} <= sprites.defined


def test_missing_icons_skip_hidden_and_character_categories(tmp_path, no_vanilla_gfx):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path, "interface/ideas.gfx", 'spriteType = { name = "GFX_idea_known" }\n'
    )
    ideas = _write(
        tmp_path,
        "common/ideas/x.txt",
        "ideas = {\n\tcountry = {\n\t\tNO_icon = {\n\t\t}\n\t}\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_missing_icons(
        {
            "WITH_pic": ("country", None, "known"),
            "NO_icon": ("country", None, None),
            "HIDDEN_idea": ("hidden_ideas", None, None),
            "CHAR_token": ("character", None, None),
        },
        {str(ideas): ["NO_icon"]},
    )

    assert [
        (i.severity, i.category, i.message, i.file, i.line) for i in validator._issues
    ] == [
        (
            Severity.WARNING,
            "missing-idea-icon",
            "country: NO_icon: auto-icon GFX_idea_NO_icon (undefined)",
            "common/ideas/x.txt",
            3,
        )
    ]


def test_empty_idea_scope_skips_the_sprite_index(tmp_path, monkeypatch):
    validator = _validator(tmp_path)
    monkeypatch.setattr(
        validator,
        "_build_idea_sprite_set",
        lambda: pytest.fail("sprite index loaded"),
    )
    validator.validate_missing_icons({}, {})
    assert validator.errors_found == 0


# ---- category icon frames ------------------------------------------------------


def _frames_sprite(frames):
    line = f" noOfFrames = {frames}\n" if frames else ""
    return (
        'spriteType = {\n name = "GFX_idea_categories"\n'
        ' texturefile = "gfx/interface/idea_categories.dds"\n' + line + "}\n"
    )


@pytest.mark.parametrize(
    "gfx, expected",
    [
        (_frames_sprite(6), 6),
        (_frames_sprite(None), 1),
        ('spriteType = { name = "GFX_something_else" }', None),
    ],
    ids=["noOfFrames", "no frame line", "no sprite"],
)
def test_frame_count(tmp_path, gfx, expected):
    _write(tmp_path, "x.gfx", gfx)
    assert _idea_categories_frame_count([str(tmp_path)]) == expected


def test_frame_count_first_dir_wins(tmp_path):
    _write(
        tmp_path,
        "mod/a.gfx",
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 9 }',
    )
    _write(
        tmp_path,
        "van/b.gfx",
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 6 }',
    )
    assert (
        _idea_categories_frame_count([str(tmp_path / "mod"), str(tmp_path / "van")])
        == 9
    )


def test_frame_count_of_a_missing_dir_is_none():
    assert _idea_categories_frame_count(["/no/such/dir"]) is None


def test_frame_count_ignores_an_unlistable_directory(tmp_path, monkeypatch):
    real_listdir = os.listdir

    def failing_listdir(path):
        if str(path) == str(tmp_path):
            raise PermissionError("denied")
        return real_listdir(path)

    monkeypatch.setattr(os, "listdir", failing_listdir)
    assert _idea_categories_frame_count([str(tmp_path)]) is None


def test_frame_count_skips_a_gfx_entry_it_cannot_read(tmp_path):
    (tmp_path / "a_unreadable.gfx").mkdir()
    _write(
        tmp_path,
        "b_ideas.gfx",
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 4 }\n',
    )
    assert _idea_categories_frame_count([str(tmp_path)]) == 4


def test_category_frame_check_is_skipped_without_the_sprite(tmp_path, monkeypatch):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    monkeypatch.setattr(
        "validate_gfx_references._find_vanilla_interface_dir", lambda: None
    )
    validator = _validator(tmp_path)
    validator.validate_category_icon_frames()
    assert validator._issues == []


def test_category_frame_shortage_names_the_overflow(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "common/idea_tags/00_idea.txt",
        "idea_categories = {\n"
        "\thidden_ideas = { hidden = yes }\n"
        "\tcountry = { type = national_spirit }\n"
        "\tmilitary_staff = { character_slot = chief_of_staff }\n"
        "\tnational_status = { slot = religion }\n"
        "\tpolitical_advisor = { slot = political_advisor }\n"
        "\teconomy = { slot = economy }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "interface/ideas.gfx",
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 1 }\n',
    )
    monkeypatch.setattr(
        "validate_gfx_references._find_vanilla_interface_dir", lambda: None
    )
    validator = _validator(tmp_path)

    validator.validate_category_icon_frames()

    assert [issue.message for issue in validator._issues] == [
        "3 politics-view idea categories defined but GFX_idea_categories has only "
        "1 frame(s) — these render a missing icon: political_advisor, economy. "
        "Add frames to the sprite (noOfFrames) and the idea_categories.dds strip."
    ]


# ---- parse_all, undefined references and quality --------------------------------

QUALITY_IDEAS = """ideas = {
\tcountry = {
\t\tCANCEL_idea = {
\t\t\tcancel = { always = no }
\t\t\tpicture = shared
\t\t}
\t\tLOG_idea = {
\t\t\ton_add = {
\t\t\t\tlog = "traced"
\t\t\t}
\t\t\tpicture = shared
\t\t}
\t\tCIVIL_idea = {
\t\t\tallowed_civil_war = { always = no }
\t\t\tpicture = shared
\t\t}
\t}
\tpolitical_advisor = {
\t\tTAG_advisor = {
\t\t\tallowed = { tag = ISR }
\t\t\tpicture = shared
\t\t}
\t\tTAG_advisor_two = {
\t\t\tallowed = { original_tag = ISR tag = ISR }
\t\t\tpicture = shared
\t\t}
\t}
}
"""


def test_character_idea_tokens_join_the_defined_set(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path,
        "common/ideas/clean.txt",
        "ideas = {\n\tcountry = {\n\t\tCLEAN_idea = { picture = x }\n\t}\n}\n",
    )
    _write(
        tmp_path,
        "common/characters/TAG.txt",
        "characters = {\n\tTAG_leader = {\n"
        "\t\tadvisor = { idea_token = TAG_leader_token }\n"
        "\t\tadvisor = { idea_token = TAG_leader_token }\n"
        "\t\tadvisor = { idea_token = CLEAN_idea }\n"
        "\t}\n}\n",
    )
    _write(
        tmp_path,
        "common/characters/OTH.txt",
        "characters = {\n\tOTH_leader = {\n\t\tcountry_leader = { ideology = a }\n\t}\n}\n",
    )
    validator = _validator(tmp_path)

    defined, issues_by_file, ideas_by_file = validator._parse_all_ideas()

    assert defined["TAG_leader_token"] == ("character", None, None)
    assert defined["CLEAN_idea"][0] == "country"
    assert issues_by_file == {}
    assert list(ideas_by_file.values()) == [["CLEAN_idea"]]


def test_repeated_undefined_reference_is_reported_once(tmp_path):
    _write(
        tmp_path,
        "events/MD_test.txt",
        "option = {\n\thas_idea = nope_idea\n\thas_idea = nope_idea\n}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_undefined_idea_refs({})
    assert [(i.severity, i.message) for i in validator._issues] == [
        (Severity.ERROR, "MD_test.txt: undefined idea reference 'nope_idea'")
    ]


@pytest.mark.parametrize(
    "consumer_path",
    [
        "history/countries/test.txt",
        "common/on_actions/test.txt",
        "common/scripted_triggers/test.txt",
    ],
)
def test_staged_idea_consumer_is_scanned(tmp_path, consumer_path):
    path = _write(tmp_path, consumer_path, "has_idea = undefined_test_idea\n")
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator.staged_files = [str(path)]
    validator.validate_undefined_idea_refs({})
    assert [issue.message for issue in validator._issues] == [
        "test.txt: undefined idea reference 'undefined_test_idea'"
    ]


def test_quality_issues_carry_their_idea_file_and_line(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/ideas/quality.txt", QUALITY_IDEAS)
    _write(tmp_path, "common/ideas/placeholder.txt", "")
    validator = _validator(tmp_path)
    _defined, issues_by_file, _ideas_by_file = validator._parse_all_ideas()

    validator.validate_idea_quality(issues_by_file)

    assert sorted((i.line, i.message, i.file) for i in validator._issues) == [
        (
            3,
            "'CANCEL_idea' has cancel = { always = no } (checked hourly, always false)",
            "common/ideas/quality.txt",
        ),
        (
            7,
            "'LOG_idea' has on_add = { log = ... } with no real effects"
            " (drop the on_add block — tracing-only logs are dead weight)",
            "common/ideas/quality.txt",
        ),
        (
            14,
            "redundant allowed_civil_war = { always = no }",
            "common/ideas/quality.txt",
        ),
        (
            19,
            "'TAG_advisor' uses tag = ISR in allowed"
            " (use original_tag for civil war safety)",
            "common/ideas/quality.txt",
        ),
        (
            23,
            "'TAG_advisor_two' has both tag and original_tag = ISR in allowed"
            " (drop the tag = ...; original_tag already restricts it)",
            "common/ideas/quality.txt",
        ),
    ]
    assert validator.warnings_found == 5


def test_weekly_modifier_is_a_warning_in_idea_quality(tmp_path):
    _write(
        tmp_path,
        "common/ideas/weekly.txt",
        _ideas("country", _idea("WEEKLY", "modifier = { weekly_stability = 0.01 }")),
    )
    _write(tmp_path, "events/grant.txt", "add_idea = WEEKLY\n")
    validator = _validator(tmp_path)

    validator.validate_idea_quality({})

    assert [
        (issue.severity, issue.category, issue.file, issue.line, issue.message)
        for issue in validator._issues
    ] == [
        (
            Severity.WARNING,
            "idea-quality",
            "common/ideas/weekly.txt",
            3,
            "WEEKLY uses weekly_stability on a country idea (permanent grant)",
        )
    ]


@pytest.mark.parametrize("gate", ("allowed", "available"))
def test_a_slotless_gate_is_an_error_under_the_target_root(tmp_path, gate):
    _write(
        tmp_path,
        "common/idea_tags/00_idea.txt",
        "idea_categories = {\n\tcustom_slotless = { type = national_spirit }\n}\n",
    )
    _write(
        tmp_path,
        "common/ideas/test.txt",
        _ideas("custom_slotless", _idea("my_idea", f"{gate} = {{ always = yes }}")),
    )
    validator = _validator(tmp_path)
    _defined, issues_by_file, _ideas_by_file = validator._parse_all_ideas()

    validator.validate_idea_quality(issues_by_file)

    assert [i.severity for i in validator._issues] == [Severity.ERROR]


def test_quality_report_ignores_an_issue_type_it_has_no_message_for(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    validator = _validator(tmp_path)

    validator.validate_idea_quality(
        {
            str(tmp_path / "common" / "ideas" / "quality.txt"): [
                IdeaIssue("KNOWN_idea", "country", 4, "cancel-always-no"),
                IdeaIssue("ODD_idea", "country", 9, "not-a-rendered-type"),
            ]
        }
    )

    assert [issue.line for issue in validator._issues] == [4]


def test_non_instant_bonus_is_skipped_for_configured_idea_prefixes(
    tmp_path, monkeypatch
):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    monkeypatch.setattr(validate_ideas, "_INSTANT_EXEMPT_PREFIXES", ("sp_",))
    validator = _validator(tmp_path)

    validator.validate_idea_quality(
        {
            str(tmp_path / "common" / "ideas" / "quality.txt"): [
                IdeaIssue(
                    "sp_idea", "country", 4, "equipment-bonus-not-instant", "convoy"
                ),
                IdeaIssue(
                    "TAG_idea", "country", 9, "equipment-bonus-not-instant", "convoy"
                ),
            ]
        }
    )

    assert [(issue.line, issue.message) for issue in validator._issues] == [
        (
            9,
            "'TAG_idea' equipment_bonus convoy has no instant = yes (the bonus"
            " only reaches newly created variants; add instant = yes, or exempt"
            " the idea in validation_config.json)",
        )
    ]


def test_idea_tag_change_invalidates_the_aggregate_cache(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    tag_file = "common/idea_tags/00_idea.txt"
    _write(
        tmp_path,
        tag_file,
        "idea_categories = {\n\tcustom_slotless = { type = national_spirit }\n}\n",
    )
    _write(
        tmp_path,
        "common/ideas/test.txt",
        _ideas("custom_slotless", _idea("my_idea", "allowed = { always = yes }")),
    )
    shared_utils._slotless_idea_categories_cached.cache_clear()
    _defined, first_issues, _by_file = _validator(tmp_path)._parse_all_ideas()

    _write(
        tmp_path,
        tag_file,
        "idea_categories = {\n"
        "\tcustom_slotless = { type = national_spirit slot = political_advisor }\n"
        "}\n",
    )
    shared_utils._slotless_idea_categories_cached.cache_clear()
    _defined, second_issues, _by_file = _validator(tmp_path)._parse_all_ideas()

    assert {
        issue.issue_type for issues in first_issues.values() for issue in issues
    } == {_SLOTLESS_ALLOWED}
    assert second_issues == {}


# ---- localisation ---------------------------------------------------------------

MISSING_LOC_IDEAS = """ideas = {
\thidden_ideas = {
\t\tTAG_hidden = {
\t\t}
\t}
\tcountry = {
\t\tTAG_present = {
\t\t}
\t\tTAG_renamed = {
\t\t\tname = TAG_present
\t\t}
\t\tTAG_no_desc = {
\t\t}
\t\tTAG_absent = {
\t\t}
\t}
}
"""


def _missing_loc_findings(tmp_path, **kwargs):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/ideas/test.txt", MISSING_LOC_IDEAS)
    _write(
        tmp_path,
        "common/characters/TAG.txt",
        "characters = {\n\tTAG_person = {\n\t\tadvisor = {\n"
        "\t\t\tidea_token = TAG_person_token\n\t\t}\n\t}\n}\n",
    )
    _write(
        tmp_path,
        "localisation/english/MD_test_l_english.yml",
        ' l_english:\n TAG_present:0 "Present"\n TAG_present_desc:0 "Desc"\n'
        ' TAG_no_desc:0 "No Desc"\n',
    )
    validator = _validator(tmp_path, **kwargs)
    defined, _issues, ideas_by_file = validator._parse_all_ideas()
    validator.validate_missing_localisation(defined, ideas_by_file)
    return _findings(validator)


_ABSENT = "'TAG_absent' (country) is missing loc key 'TAG_absent'"


@pytest.mark.parametrize(
    "flags, expected",
    [
        ({}, [_ABSENT]),
        (
            {"missing_loc": True},
            [
                _ABSENT,
                "'TAG_absent' (country) is missing loc key 'TAG_absent_desc'",
                "'TAG_no_desc' (country) is missing loc key 'TAG_no_desc_desc'",
            ],
        ),
    ],
    ids=["name keys", "with --missing-loc"],
)
def test_missing_localisation(tmp_path, flags, expected):
    findings = _missing_loc_findings(tmp_path, **flags)
    assert [message for _category, message, _file, _line in findings] == expected
    assert findings[0][2:] == ("common/ideas/test.txt", 14)


def test_name_and_desc_severities_follow_the_definition(tmp_path, no_vanilla_gfx):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path,
        "common/ideas/inline.txt",
        "ideas = { country = {\n"
        "\tDIRECT_idea = { picture = shared }\n"
        "\tRENAMED_idea = { name = shared_name picture = shared }\n"
        "\tMISSING_idea = { picture = shared }\n"
        "} }\n",
    )
    _write(
        tmp_path,
        "localisation/english/MD_inline_l_english.yml",
        'l_english:\n DIRECT_idea: "Direct Name"\n'
        ' DIRECT_idea_desc: "Direct description."\n'
        ' shared_name: "Shared Name"\n shared_name_desc: "Shared description."\n',
    )
    validator = _validator(tmp_path, missing_loc=True)

    validator.validate_missing_localisation(*_defined_and_files(validator))

    assert [(i.severity, i.message, i.line) for i in validator._issues] == [
        (
            Severity.ERROR,
            "'MISSING_idea' (country) is missing loc key 'MISSING_idea'",
            4,
        ),
        (
            Severity.WARNING,
            "'MISSING_idea' (country) is missing loc key 'MISSING_idea_desc'",
            4,
        ),
    ]


def _defined_and_files(validator):
    defined, _issues, ideas_by_file = validator._parse_all_ideas()
    return defined, ideas_by_file


# Sharing focus strings through `name = X` is intentional, not a collision.
def test_a_name_override_resolves_to_the_shared_key(tmp_path):
    _write(
        tmp_path,
        "common/idea_tags/00_idea.txt",
        "idea_categories = {\n\tcountry = { type = national_spirit }\n}\n",
    )
    _write(
        tmp_path,
        "common/ideas/test.txt",
        _ideas("country", _idea("COL_idea", "name = shared_key", "picture = shared")),
    )
    validator = _validator(tmp_path)
    defined, ideas_by_file = _defined_and_files(validator)
    assert defined["COL_idea"] == ("country", "shared_key", "shared")

    validator.validate_missing_localisation(defined, ideas_by_file)
    assert [i.message for i in validator._issues] == [
        "'COL_idea' (country) is missing loc key 'shared_key'"
    ]

    _write(
        tmp_path,
        "localisation/english/collide_l_english.yml",
        'l_english:\n shared_key:0 "Shared"\n shared_key_desc:0 "Shared desc"\n',
    )
    shared = _validator(tmp_path)
    shared.validate_missing_localisation(*_defined_and_files(shared))
    assert shared._issues == []


def test_missing_localisation_reads_no_loc_without_idea_files_in_scope(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "validate_localisation.get_all_loc_keys",
        lambda *_args, **_kwargs: pytest.fail("loc index was loaded"),
    )
    validator = _validator(tmp_path)
    validator.validate_missing_localisation({"TAG_absent": ("country", None, None)}, {})
    assert validator._issues == []


def test_loc_consolidation_only_suggests_true_duplicates(tmp_path):
    _write(
        tmp_path,
        "localisation/english/MD_test_l_english.yml",
        " l_english:\n"
        ' TIER_one:0 "Shared Name"\n'
        ' TIER_two:0 "Shared Name"\n'
        " TIER_one_desc:0 $TIER_desc$\n"
        ' SOLO_idea:0 "Solo Name"\n'
        ' SPLIT_one:0 "Split Name"\n'
        ' SPLIT_two:0 "Split Name"\n'
        ' SPLIT_one_desc:0 "First"\n'
        ' SPLIT_two_desc:0 "Second"\n'
        ' RENAMED_idea:0 "Shared Name"\n',
    )
    ideas_file = str(_write(tmp_path, "common/ideas/test.txt", "ideas = { }\n"))
    defined = {
        name: ("country", None, None)
        for name in ("TIER_one", "TIER_two", "SOLO_idea", "SPLIT_one", "SPLIT_two")
    }
    defined["RENAMED_idea"] = ("country", "TIER_one", None)
    defined["NO_LOC_idea"] = ("country", None, None)
    validator = _validator(tmp_path)

    validator.validate_loc_consolidation(
        defined, {ideas_file: sorted(defined) + ["UNKNOWN_idea"]}
    )

    assert [(i.severity, i.message) for i in validator._issues] == [
        (
            Severity.WARNING,
            "test.txt: 2 ideas share display name '\"Shared Name\"': TIER_one, TIER_two"
            " — set `name = TIER_one` on TIER_two and drop their duplicate loc keys",
        )
    ]


# ---- unused ideas -----------------------------------------------------------------


def _write_unused_mod(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path,
        "common/ideas/spirits.txt",
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\tUSED_spirit = { picture = x }\n"
        "\t\tDEAD_spirit = { picture = x }\n"
        "\t\tTOKEN_spirit = { picture = x }\n"
        "\t\tTABLE_spirit = { picture = x }\n"
        "\t\tMETA_spirit_TAG = { picture = x }\n"
        "\t}\n"
        "\tpolitical_advisor = {\n"
        "\t\tADVISOR_idea = { picture = x }\n"
        "\t}\n"
        "}\n",
    )
    _write(
        tmp_path, "common/synchronized_dynamic_tokens/MD_tokens.txt", "TOKEN_spirit\n"
    )
    _write(
        tmp_path,
        "events/MD_grants.txt",
        "grant = {\n"
        "\tadd_ideas = USED_spirit\n"
        "\tadd_to_array = { global.ideas = token:TABLE_spirit }\n"
        "\tadd_timed_idea = { idea = META_spirit_[ROOTTAG] days = 30 }\n"
        "}\n",
    )


def _unused(tmp_path, staged_files=None):
    validator = _validator(tmp_path, unused_ideas=True)
    defined, _issues, ideas_by_file = validator._parse_all_ideas()
    if staged_files is not None:
        ideas_by_file = {
            path.replace("/", "\\"): ideas for path, ideas in ideas_by_file.items()
        }
        validator.staged_only = True
        validator.staged_files = staged_files
    validator.validate_unused_ideas(defined, ideas_by_file)
    return validator


def test_only_the_never_referenced_spirit_is_flagged_as_unused(tmp_path):
    _write_unused_mod(tmp_path)
    validator = _unused(tmp_path)
    assert _findings(validator) == [
        (
            "unused-idea",
            "'DEAD_spirit' (country) is defined but never referenced",
            "common/ideas/spirits.txt",
            0,
        )
    ]
    assert validator.warnings_found == 1


def test_staged_mode_limits_unused_ideas_to_staged_files(tmp_path):
    _write_unused_mod(tmp_path)
    _write(
        tmp_path,
        "common/ideas/extra.txt",
        "ideas = {\n\tcountry = {\n\t\tOTHER_dead_spirit = { picture = x }\n\t}\n}\n",
    )
    validator = _unused(tmp_path, staged_files=["common/ideas/extra.txt"])
    assert [issue.message for issue in validator._issues] == [
        "'OTHER_dead_spirit' (country) is defined but never referenced"
    ]


def test_staged_mode_with_no_candidate_ideas_reports_nothing(tmp_path):
    _write_unused_mod(tmp_path)
    assert _unused(tmp_path, staged_files=["events/MD_grants.txt"])._issues == []


# ---- equipment bonus stacking --------------------------------------------------------


def test_type_and_child_equipment_bonus_is_flagged(tmp_path):
    _write(
        tmp_path,
        "common/units/equipment/ships.txt",
        "equipments = {\n"
        "\thelicopter_operator = {\n\t\tis_archetype = yes\n\t\ttype = carrier\n"
        "\t\tbuild_cost_ic = 28000\n\t}\n"
        "\tcarrier = {\n\t\tis_archetype = yes\n\t\ttype = carrier\n"
        "\t\tbuild_cost_ic = 40000\n\t}\n"
        "}\n",
    )
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path,
        "common/ideas/navy.txt",
        "ideas = {\n\tcountry = {\n\t\tNAVY_act = {\n\t\t\tequipment_bonus = {\n"
        "\t\t\t\tcarrier = { build_cost_ic = -0.25 }\n"
        "\t\t\t\thelicopter_operator = { build_cost_ic = -0.25 }\n"
        "\t\t\t}\n\t\t}\n\t}\n}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_equipment_bonus_stack()
    assert [(i.category, i.file) for i in validator._issues] == [
        ("bonus-type-archetype-stack", "common/ideas/navy.txt")
    ]
    assert "helicopter_operator" in validator._issues[0].message


# ---- the run -------------------------------------------------------------------------

RUN_IDEAS = """ideas = {
\tcountry = {
\t\tTIER_one = {
\t\t\tpicture = shared
\t\t}
\t\tTIER_two = {
\t\t\tpicture = shared
\t\t}
\t\tDEAD_spirit = {
\t\t\tpicture = shared
\t\t}
\t}
}
"""

RUN_LOC = (
    " l_english:\n"
    ' TIER_one:0 "Shared Name"\n'
    ' TIER_one_desc:0 "Desc"\n'
    ' TIER_two:0 "Shared Name"\n'
    ' TIER_two_desc:0 "Desc"\n'
)


def _write_run_mod(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/ideas/test.txt", RUN_IDEAS)
    _write(tmp_path, "common/synchronized_dynamic_tokens/MD_tokens.txt", "")
    _write(
        tmp_path,
        "events/MD_grants.txt",
        "grant = {\n\tadd_ideas = TIER_one\n\tadd_ideas = TIER_two\n}\n",
    )
    _write(tmp_path, "localisation/english/MD_test_l_english.yml", RUN_LOC)
    _write(
        tmp_path,
        "interface/ideas.gfx",
        'spriteType = { name = "GFX_idea_shared" }\n'
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 2 }\n',
    )


def test_run_calls_every_check(tmp_path, monkeypatch):
    validator = _validator(tmp_path, missing_loc=True, suggest_consolidation=True)
    monkeypatch.setattr(validator, "_parse_all_ideas", lambda: ({}, {}, {"f": ["x"]}))
    validator.unused_ideas = True
    called, checks = checks_called_by_run(validator, monkeypatch)
    assert called == checks


_DEAD_NAME = (
    "missing-idea-localisation",
    Severity.ERROR,
    "'DEAD_spirit' (country) is missing loc key 'DEAD_spirit'",
)

# A staged row adds an ideas file full of quality findings outside the staged set.
# case: (validator flags, staged files or None, findings)
_RUN_CASES = {
    "default flags report the always-on checks": (
        {"unused_ideas": True},
        None,
        [
            (
                "unused-idea",
                Severity.WARNING,
                "'DEAD_spirit' (country) is defined but never referenced",
            )
        ],
    ),
    "--missing-name-loc": ({"missing_name_loc": True}, None, [_DEAD_NAME]),
    "--missing-name-loc staged on the idea file": (
        {"missing_name_loc": True},
        ["common/ideas/test.txt"],
        [_DEAD_NAME],
    ),
    "staged without an idea file skips quality": (
        {"suggest_consolidation": True},
        ["events/MD_grants.txt"],
        [],
    ),
}


@pytest.mark.parametrize(
    ("flags", "staged", "expected"), _RUN_CASES.values(), ids=_RUN_CASES
)
def test_run(tmp_path, no_vanilla_gfx, flags, staged, expected):
    _write_run_mod(tmp_path)
    validator = _validator(tmp_path, **flags)
    if staged is not None:
        _write(tmp_path, "common/ideas/quality.txt", QUALITY_IDEAS)
        validator.staged_only = True
        validator.staged_files = staged
    validator.run_validations()
    assert [(i.category, i.severity, i.message) for i in validator._issues] == expected


def test_optional_flags_enable_the_advisory_checks(tmp_path, no_vanilla_gfx):
    _write_run_mod(tmp_path)
    validator = _validator(tmp_path, missing_loc=True, suggest_consolidation=True)

    validator.run_validations()

    assert {issue.category for issue in validator._issues} == {
        "loc-consolidation",
        "missing-idea-localisation",
    }
    assert any(
        "is missing loc key 'DEAD_spirit_desc'" in issue.message
        for issue in validator._issues
    )


def test_staged_run_reports_quality_for_the_staged_idea_file(tmp_path, no_vanilla_gfx):
    _write_run_mod(tmp_path)
    _write(tmp_path, "common/ideas/quality.txt", QUALITY_IDEAS)
    _write(
        tmp_path,
        "common/ideas/unstaged.txt",
        _ideas(
            "country",
            _idea("OTHER_idea", "cancel = { always = no }", "picture = shared"),
        ),
    )
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator.staged_files = ["common/ideas/quality.txt"]

    validator.run_validations()

    assert {issue.category for issue in validator._issues} == {"idea-quality"}
    assert validator.warnings_found == 5


def test_staged_idea_tags_change_runs_the_full_quality_scan():
    validator = Validator("/nonexistent", use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = ["common/idea_tags/00_idea.txt"]
    all_issues = {
        "common/ideas/test.txt": [IdeaIssue("my_idea", "country", 1, _SLOTLESS_ALLOWED)]
    }
    validator._parse_all_ideas = lambda: ({}, all_issues, {})
    calls = []
    validator.validate_idea_quality = calls.append
    for name in (
        "validate_undefined_idea_refs",
        "validate_category_icon_frames",
        "validate_missing_icons",
        "validate_unused_ideas",
        "validate_equipment_bonus_stack",
    ):
        setattr(validator, name, lambda *_args: None)

    validator.run_validations()

    assert calls == [all_issues]


# ---- command line ---------------------------------------------------------------------


def test_extra_cli_arguments_default_to_the_documented_values(tmp_path):
    assert Validator(str(tmp_path), use_colors=False, workers=1).unused_ideas is True
    parser = argparse.ArgumentParser()
    _add_extra_args(parser)

    defaults = parser.parse_args([])
    assert (
        defaults.missing_name_loc,
        defaults.missing_loc,
        defaults.unused_ideas,
        defaults.suggest_consolidation,
    ) == (False, False, True, False)
    assert parser.parse_args(["--no-unused-ideas"]).unused_ideas is False
    assert parser.parse_args(["--missing-name-loc"]).missing_name_loc is True
    assert parser.parse_args(["--missing-loc"]).missing_loc is True
    assert parser.parse_args(["--suggest-consolidation"]).suggest_consolidation is True


def _run_script(tmp_path, monkeypatch, *flags):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            validate_ideas.__file__,
            "--path",
            str(tmp_path),
            "--strict",
            "--workers",
            "1",
            "--no-color",
            "--no-unused-ideas",
            *flags,
        ],
    )
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(validate_ideas.__file__, run_name="__main__")
    return exit_info.value.code


def test_script_entry_point_exits_nonzero_under_strict(tmp_path, monkeypatch):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/synchronized_dynamic_tokens/MD_tokens.txt", "")
    _write(tmp_path, "events/MD_test.txt", "option = {\n\thas_idea = nope_idea\n}\n")
    monkeypatch.setattr("validate_gfx_references._vanilla_gfx_files", lambda: [])
    assert _run_script(tmp_path, monkeypatch) == 1


@pytest.mark.parametrize(
    ("name_override", "descriptions_only", "expected_code"),
    [
        (None, False, 1),
        ("shared_missing", False, 1),
        ("shared_missing_desc", False, 1),
        (None, True, 0),
    ],
)
def test_strict_core_gate_fails_only_for_missing_idea_names(
    tmp_path,
    monkeypatch,
    no_vanilla_gfx,
    capsys,
    name_override,
    descriptions_only,
    expected_code,
):
    _write_run_mod(tmp_path)
    spec = next(spec for spec in BATCHES["core"] if spec.name == "ideas")
    assert spec.strict is True
    flags = list(spec.args)
    if name_override:
        _write(
            tmp_path,
            "common/ideas/test.txt",
            RUN_IDEAS.replace(
                "DEAD_spirit = {", f"DEAD_spirit = {{ name = {name_override}"
            ),
        )
    if descriptions_only:
        _write(
            tmp_path,
            "localisation/english/MD_test_l_english.yml",
            RUN_LOC + ' DEAD_spirit: "Dead Spirit"\n',
        )
        flags = ["--missing-loc"]

    assert _run_script(tmp_path, monkeypatch, *flags) == expected_code
    missing_key = (
        "DEAD_spirit_desc" if descriptions_only else name_override or "DEAD_spirit"
    )
    assert f"missing loc key '{missing_key}'" in capsys.readouterr().err
