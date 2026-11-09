"""Tests for validate_focus_tree.py."""

import argparse
import os
import random
import re

import pytest
import validate_focus_tree as V
from shared.suite import checks_called_by_run
from shared.suite import write_under_str as _write
from shared_utils import extract_block_from_text

FOCUS_DIR = "common/national_focus"


def _focus_file(tmp_path, body, name="test.txt"):
    return _write(tmp_path, f"{FOCUS_DIR}/{name}", body)


def _validator(tmp_path, **kwargs):
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)


def _messages(validator):
    return [i.message for i in validator._issues]


def _sprite_index(*names):
    return frozenset({f"GFX_filler_{i}" for i in range(1000)} | set(names))


def _source(tmp_path, body):
    return V._FocusFile(_focus_file(tmp_path, body), str(tmp_path))


@pytest.mark.parametrize("missing_icons", [True, False])
def test_run_validations_calls_every_check(tmp_path, monkeypatch, missing_icons):
    validator = _validator(tmp_path, missing_icons=missing_icons)
    called, checks = checks_called_by_run(validator, monkeypatch)
    assert called == [
        check for check in checks if missing_icons or check != "validate_focus_icons"
    ]


def test_missing_icons_flag_is_registered():
    parser = argparse.ArgumentParser()
    V._add_extra_args(parser)
    assert parser.parse_args([]).missing_icons is False
    assert parser.parse_args(["--missing-icons"]).missing_icons is True


# --- duplicate IDs, orphans and prerequisites -------------------------------

DUPLICATE_TREES = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
\tfocus = { id = TAG_focus_unique x = 2 y = 0 cost = 1 }
}
focus_tree = {
\tid = tree_b
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
}
"""


def test_duplicate_focus_id_lists_every_definition(tmp_path):
    _focus_file(tmp_path, DUPLICATE_TREES)
    v = _validator(tmp_path)
    v.validate_duplicate_focus_ids()

    focus_path = os.path.join("common", "national_focus", "test.txt")
    assert _messages(v) == [
        f"Duplicate focus ID 'TAG_focus_a' defined 2 times:"
        f" {focus_path}:3, {focus_path}:8"
    ]
    assert v._issues[0].line == 3
    assert v._issues[0].category == "duplicate-focus-id"


def test_registry_keeps_the_first_definition_of_a_shared_focus(tmp_path):
    """A shared focus redefined in another file is listed twice for the
    duplicate check but resolves to its first definition everywhere else."""
    parsed = [
        {
            "filepath": "a.txt",
            "shared_defs": {"TAG_shared_s": {"line": 1, "prereq_groups": [["P"]]}},
            "trees": [],
        },
        {
            "filepath": "b.txt",
            "shared_defs": {"TAG_shared_s": {"line": 9, "prereq_groups": []}},
            "trees": [],
        },
    ]
    all_focuses, focus_info = _validator(tmp_path)._build_focus_registry(parsed)

    assert all_focuses["TAG_shared_s"] == [("a.txt", 1), ("b.txt", 9)]
    assert focus_info["TAG_shared_s"] == ("a.txt", 1, [["P"]])


ORPHAN_TREES = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
\tfocus = {
\t\tid = TAG_focus_orphan
\t\tx = 2
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_elsewhere }
\t}
\tfocus = {
\t\tid = TAG_focus_ghost
\t\tx = 4
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_nowhere }
\t}
\tfocus = {
\t\tid = TAG_focus_ok
\t\tx = 6
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_a }
\t}
}
focus_tree = {
\tid = tree_b
\tfocus = { id = TAG_focus_elsewhere x = 0 y = 0 cost = 1 }
}
"""


def test_orphan_focus_reported_only_when_the_target_exists_elsewhere(tmp_path):
    """A prerequisite defined in another tree is an orphan; one defined nowhere
    belongs to the missing-prerequisite check instead."""
    _focus_file(tmp_path, ORPHAN_TREES)
    v = _validator(tmp_path)
    v.validate_orphan_focuses()

    assert _messages(v) == [
        "Orphan focus 'TAG_focus_orphan': prerequisite group"
        " ['TAG_focus_elsewhere'] not present in tree"
    ]
    assert v._issues[0].line == 4
    assert v._issues[0].category == "orphan-focus"


@pytest.mark.parametrize(
    "trees",
    [DUPLICATE_TREES, ORPHAN_TREES],
    ids=["duplicate ID is one graph node", "undefined prerequisite adds no edge"],
)
def test_dependency_cycles_ignore_duplicates_and_undefined_targets(tmp_path, trees):
    _focus_file(tmp_path, trees)
    v = _validator(tmp_path)
    v.validate_dependency_cycles()
    assert v._issues == []


MISSING_PREREQ_TREES = """shared_focus = {
\tid = TAG_shared_s
\tx = 0
\ty = 0
\tcost = 1
\tprerequisite = { focus = TAG_focus_MISSPELLED }
}
shared_focus = {
\tid = TAG_shared_t
\tx = 0
\ty = 2
\tcost = 1
\tprerequisite = { focus = TAG_focus_misspelled focus = TAG_shared_absent }
}
focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_misspelled x = 0 y = 0 cost = 1 }
\tfocus = {
\t\tid = TAG_focus_b
\t\tx = 2
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_SHARED_S }
\t}
\tfocus = {
\t\tid = TAG_focus_c
\t\tx = 4
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_absent }
\t\tprerequisite = { focus = TAG_shared_absent }
\t}
}
"""


def test_missing_prerequisites_report_case_mismatches_and_dedupe(tmp_path):
    _focus_file(tmp_path, MISSING_PREREQ_TREES)
    v = _validator(tmp_path)
    v.validate_missing_prerequisite_targets()

    assert _messages(v) == [
        "Missing prerequisite target 'TAG_focus_MISSPELLED' (referenced by"
        " 'TAG_shared_s'): case-mismatch reference 'TAG_focus_MISSPELLED' —"
        " defined as 'TAG_focus_misspelled' (works on Windows, fails on Linux)",
        "Missing prerequisite target 'TAG_shared_absent' (referenced by"
        " 'TAG_shared_t')",
        "Missing prerequisite target 'TAG_SHARED_S' (referenced by"
        " 'TAG_focus_b'): case-mismatch reference 'TAG_SHARED_S' — defined as"
        " 'TAG_shared_s' (works on Windows, fails on Linux)",
        "Missing prerequisite target 'TAG_focus_absent' (referenced by 'TAG_focus_c')",
    ]
    assert {i.category for i in v._issues} == {"missing-prerequisite"}


RELATIVE_POSITION_TREES = """shared_focus = {
\tid = TAG_shared_root
\tx = 0
\ty = 0
\tcost = 1
}
focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_root x = 0 y = 0 cost = 1 }
\tfocus = {
\t\tid = TAG_focus_forward
\t\tx = 0
\t\ty = 1
\t\tcost = 1
\t\trelative_position_id = TAG_focus_late
\t}
\tfocus = {
\t\tid = TAG_focus_late
\t\tx = 2
\t\ty = 1
\t\tcost = 1
\t\trelative_position_id = TAG_focus_root
\t}
\tfocus = {
\t\tid = TAG_focus_shared_anchor
\t\tx = 0
\t\ty = 1
\t\tcost = 1
\t\trelative_position_id = TAG_shared_root
\t}
\tfocus = {
\t\tid = TAG_focus_other_file
\t\tx = 0
\t\ty = 1
\t\tcost = 1
\t\trelative_position_id = TAG_focus_elsewhere
\t}
\tfocus = {
\t\tid = TAG_focus_ghost
\t\tx = 0
\t\ty = 1
\t\tcost = 1
\t\trelative_position_id = TAG_focus_nowhere
\t}
}
"""


def test_relative_position_forward_and_missing_targets(tmp_path):
    """A target defined later in the same file and one defined nowhere are
    reported; a shared focus above, a focus in another file, and an earlier
    focus are clean."""
    _focus_file(tmp_path, RELATIVE_POSITION_TREES)
    _focus_file(
        tmp_path,
        "focus_tree = {\n\tid = tree_b\n"
        "\tfocus = { id = TAG_focus_elsewhere x = 0 y = 0 cost = 1 }\n}\n",
        name="other.txt",
    )
    v = _validator(tmp_path)
    v.validate_relative_position_targets()

    assert _messages(v) == [
        "Focus 'TAG_focus_forward' uses relative_position_id 'TAG_focus_late',"
        " which is defined later in the file - move 'TAG_focus_late' above it",
        "Focus 'TAG_focus_ghost' uses relative_position_id 'TAG_focus_nowhere',"
        " which no focus defines",
    ]
    assert [i.line for i in v._issues] == [14, 42]
    assert [i.category for i in v._issues] == [
        "relative-position-forward-ref",
        "relative-position-missing-target",
    ]
    assert all(i.severity == V.Severity.ERROR for i in v._issues)


# --- localisation -----------------------------------------------------------


def test_missing_focus_loc_keys_reported_per_key(tmp_path):
    _focus_file(
        tmp_path,
        "focus_tree = {\n"
        "\tid = tree_a\n"
        "\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }\n"
        "\tfocus = { id = TAG_focus_b x = 2 y = 0 cost = 1 }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "localisation/english/md_l_english.yml",
        "l_english:\n"
        ' TAG_focus_a:0 "A"\n'
        ' TAG_focus_a_desc:0 "A desc"\n'
        ' TAG_focus_b:0 "B"\n',
    )
    v = _validator(tmp_path)
    v.validate_missing_loc_keys()

    assert _messages(v) == [
        "Missing loc key 'TAG_focus_b_desc' for focus 'TAG_focus_b'"
    ]
    assert v._issues[0].category == "missing-loc-key"


_LOC_YML = "localisation/english/md_l_english.yml"

# case: (title, description, (category, line, message) per finding)
_LOC_COLOR_CASES = {
    "colored title": (
        "§Ycolored§! title",
        "Plain",
        [
            (
                "focus-title-color-code",
                2,
                "Focus title 'TAG_focus_a' uses color code §Y — titles carry no color",
            )
        ],
    ),
    "palette colors in the description": (
        "Clean title",
        "Use §Ythis§! or §Gthat§! or §Rcost§!",
        [],
    ),
    "off-palette color in the description": (
        "Clean title",
        "Off palette §Lbad§! code",
        [
            (
                "focus-desc-color-palette",
                3,
                "Focus description 'TAG_focus_a_desc' uses color code §L — use"
                " §Y, §G or §R",
            )
        ],
    ),
    "escaped section sign": ("Clean title", "See 15 U.S.C. §§ 1 for details", []),
}


@pytest.mark.parametrize(
    "title, desc, expected", _LOC_COLOR_CASES.values(), ids=_LOC_COLOR_CASES
)
def test_focus_loc_colors(tmp_path, title, desc, expected):
    _focus_file(
        tmp_path,
        "focus_tree = {\n\tid = tree_a\n"
        "\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }\n}\n",
    )
    _write(
        tmp_path,
        _LOC_YML,
        f'l_english:\n TAG_focus_a:0 "{title}"\n TAG_focus_a_desc:0 "{desc}"\n',
    )
    v = _validator(tmp_path)
    v.validate_focus_loc_colors()

    assert [(i.category, i.file, i.line, i.message) for i in v._issues] == [
        (category, _LOC_YML, line, message) for category, line, message in expected
    ]


# --- focus icons ------------------------------------------------------------

ICON_TREE = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 icon = GFX_known }
\tfocus = { id = TAG_focus_b x = 2 y = 0 cost = 1 icon = GFX_ghost }
\tfocus = { id = TAG_focus_c x = 4 y = 0 cost = 1 icon = "GFX_[?var]" }
}
"""


@pytest.mark.parametrize(
    "sprites, expected",
    [
        (
            _sprite_index("GFX_known"),
            ["Missing icon sprite 'GFX_ghost' for focus 'TAG_focus_b'"],
        ),
        (frozenset({"GFX_a"}), []),
    ],
    ids=["missing sprite", "sprite index failed to load"],
)
def test_focus_icons(tmp_path, monkeypatch, sprites, expected):
    _focus_file(tmp_path, ICON_TREE)
    monkeypatch.setattr(V, "build_sprite_index", lambda *a, **kw: sprites)
    v = _validator(tmp_path, missing_icons=True)
    v.validate_focus_icons()

    assert _messages(v) == expected
    assert {i.category for i in v._issues} <= {"missing-focus-icon"}


# --- staged reporting scope -------------------------------------------------

PROBLEM_TREE = """focus_tree = {
\tid = tree_a
\tcountry = { tag = SWE }
\tfocus = {
\t\tid = TAG_focus_a
\t\tx = 0
\t\ty = 0
\t\tcost = 1
\t\ticon = GFX_ghost
\t\trelative_position_id = TAG_focus_b
\t\tprerequisite = { focus = TAG_focus_b }
\t\tcompletion_reward = {
\t\t\tGER = { country_event = offer.1 }
\t\t\tadd_political_power = -50
\t\t\tadd_tech_bonus = { bonus = 0.5 uses = 1 category = infantry_tech }
\t\t}
\t}
\tfocus = {
\t\tid = TAG_focus_b
\t\tx = 2
\t\ty = 0
\t\tcost = 1
\t\ticon = GFX_ghost
\t\tprerequisite = { focus = TAG_focus_a }
\t}
}
focus_tree = {
\tid = tree_duplicate
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
}
"""

CLEAN_TREE = """focus_tree = {
\tid = tree_clean
\tfocus = {
\t\tid = TAG_focus_clean
\t\tx = 0
\t\ty = 0
\t\tcost = 1
\t\ticon = GFX_known
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t}
}
"""


def _problem_and_clean_mod(tmp_path, monkeypatch):
    _focus_file(tmp_path, PROBLEM_TREE, name="unstaged.txt")
    staged = _focus_file(tmp_path, CLEAN_TREE, name="staged.txt")
    _write(
        tmp_path,
        "localisation/english/md_l_english.yml",
        'l_english:\n TAG_focus_clean:0 "C"\n TAG_focus_clean_desc:0 "C desc"\n',
    )
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_known")
    )
    return staged


@pytest.mark.parametrize("staged", [True, False], ids=["staged file", "no file"])
def test_findings_in_unstaged_files_are_not_reported(tmp_path, monkeypatch, staged):
    staged_path = _problem_and_clean_mod(tmp_path, monkeypatch)
    v = _validator(tmp_path, missing_icons=True)
    v.staged_only = True
    v.staged_files = [staged_path] if staged else []

    v.run_validations()

    assert v._issues == []
    assert v._get_staged_paths() == (
        {os.path.join("common", "national_focus", "staged.txt")} if staged else set()
    )


def test_the_same_findings_are_reported_in_a_full_run(tmp_path, monkeypatch):
    """The staged runs above must be silent because of scope, not because the
    fixture is clean."""
    _problem_and_clean_mod(tmp_path, monkeypatch)
    v = _validator(tmp_path, missing_icons=True)

    v.run_validations()

    assert {i.category for i in v._issues} >= {
        "duplicate-focus-id",
        "dependency-cycle",
        "missing-focus-icon",
        "missing-loc-key",
        "missing-cross-country-tooltip",
        "pp-malus-completion-reward",
        "missing-search-filters",
        "relative-position-forward-ref",
    }


# --- structural defaults ----------------------------------------------------

# case: (focus bodies inside one tree, (category, line) per finding)
_STRUCTURAL_CASES = {
    "defaults, dead gate and empty blocks": (
        "\tfocus = {\n"
        "\t\tid = TAG_writes_defaults\n"
        "\t\tx = 0 y = 0 cost = 1\n"
        "\t\tcancel_if_invalid = yes\n"
        "\t\tcontinue_if_invalid = no\n"
        "\t\tavailable_if_capitulated = no\n"
        "\t}\n"
        "\tfocus = {\n"
        "\t\tid = TAG_dead_gate\n"
        "\t\tx = 2 y = 0 cost = 1\n"
        "\t\tavailable = { always = no }\n"
        "\t\tbypass = { country_exists = PAL }\n"
        "\t}\n"
        "\tfocus = {\n"
        "\t\tid = TAG_empty_blocks\n"
        "\t\tx = 4 y = 0 cost = 1\n"
        "\t\tmutually_exclusive = { }\n"
        "\t\tavailable = { }\n"
        "\t}\n"
        "\tfocus = {\n"
        "\t\tid = TAG_clean\n"
        "\t\tx = 6 y = 0 cost = 1\n"
        "\t}\n",
        [
            ("focus-default-write", 5),
            ("focus-default-write", 6),
            ("focus-default-write", 7),
            ("focus-always-no-bypass", 12),
            ("focus-empty-block", 18),
            ("focus-empty-block", 19),
        ],
    ),
    "always = no without a bypass": (
        "\tfocus = {\n"
        "\t\tid = TAG_event_driven\n"
        "\t\tx = 0 y = 0 cost = 1\n"
        "\t\tavailable = { always = no }\n"
        "\t}\n",
        [],
    ),
    "multiline always = no with a bypass": (
        "\tfocus = {\n"
        "\t\tid = TAG_dead_gate\n"
        "\t\tx = 0 y = 0 cost = 1\n"
        "\t\tavailable = {\n"
        "\t\t\talways = no\n"
        "\t\t}\n"
        "\t\tbypass = { country_exists = PAL }\n"
        "\t}\n",
        [("focus-always-no-bypass", 5)],
    ),
}


@pytest.mark.parametrize(
    "focuses, expected", _STRUCTURAL_CASES.values(), ids=_STRUCTURAL_CASES
)
def test_structural_defaults(tmp_path, focuses, expected):
    _focus_file(tmp_path, "focus_tree = {\n\tid = tree\n" + focuses + "}\n")
    v = _validator(tmp_path)
    v.validate_structural_defaults()

    assert [(i.category, i.line) for i in v._issues] == expected


# --- one read per file: findings through the shared source -------------------

# Line 5 is a comment holding every check's token; line 10 hides a brace and a
# `#` in a string; TAG_nested builds three blocks deep; the file has no
# trailing newline, so the last finding sits on the last line.
SCAN_TREE = (
    "shared_focus = { id = TAG_first cost = 1 }\n"
    "focus_tree = {\n"
    "\tid = tree_a\n"
    "\tcountry = { tag = SWE }\n"
    "\t# focus = { id = TAG_ghost completion_reward = { add_political_power = -9"
    " GER = { country_event = x.1 } } cancel_if_invalid = yes }\n"
    "\tfocus = {\n"
    "\t\tid = TAG_quoted\n"
    "\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
    "\t\tcompletion_reward = {\n"
    '\t\t\tlog = "brace } and # hash"\n'
    "\t\t\tadd_political_power = -25\n"
    "\t\t}\n"
    "\t}\n"
    "\tfocus = {\n"
    "\t\tid = TAG_nested\n"
    "\t\tsearch_filters = { FOCUS_FILTER_INDUSTRY }\n"
    "\t\tprerequisite = { focus = TAG_absent }\n"
    "\t\tcompletion_reward = {\n"
    "\t\t\tif = {\n"
    "\t\t\t\trandom_owned_state = {\n"
    "\t\t\t\t\tadd_building_construction = { type = arms_factory level = 1 }\n"
    "\t\t\t\t}\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\t}\n"
    "\tfocus = {\n"
    "\t\tid = TAG_offer\n"
    "\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
    "\t\trelative_position_id = TAG_defaults\n"
    "\t\tcompletion_reward = { GER = { country_event = offer.1 } }\n"
    "\t}\n"
    "\tfocus = {\n"
    "\t\tid = TAG_defaults\n"
    "\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
    "\t\tcancel_if_invalid = yes\n"
    "\t\tmutually_exclusive = { }\n"
    "\t\tavailable = { always = no }\n"
    "\t\tbypass = { has_war = yes }\n"
    "\t}\n"
    "}\n"
    "shared_focus = { id = TAG_last search_filters = { FOCUS_FILTER_POLITICAL }"
    " prerequisite = { focus = TAG_gone } }"
)

SCAN_PATH = f"{FOCUS_DIR}/scan.txt"

# The line numbers the checks reported before the single-read rewrite. The
# relative_position_id and structural lines are taken from the block keyword
# plus the offset inside the body, so they sit one line above their token.
SCAN_FINDINGS = [
    (
        "missing-prerequisite",
        SCAN_PATH,
        41,
        "Missing prerequisite target 'TAG_gone' (referenced by 'TAG_last')",
    ),
    (
        "missing-prerequisite",
        SCAN_PATH,
        14,
        "Missing prerequisite target 'TAG_absent' (referenced by 'TAG_nested')",
    ),
    (
        "relative-position-forward-ref",
        SCAN_PATH,
        28,
        "Focus 'TAG_offer' uses relative_position_id 'TAG_defaults', which is"
        " defined later in the file - move 'TAG_defaults' above it",
    ),
    *[
        (
            "focus-coordinate-unresolved",
            SCAN_PATH,
            line,
            f"Focus tree 'tree_a': focus '{name}' has missing or nonnumeric coordinates",
        )
        for name, line in (
            ("TAG_defaults", 32),
            ("TAG_nested", 14),
            ("TAG_offer", 26),
            ("TAG_quoted", 6),
        )
    ],
    (
        "missing-search-filters",
        SCAN_PATH,
        1,
        "Focus 'TAG_first' missing search_filters",
    ),
    (
        "missing-can-staff-guard",
        SCAN_PATH,
        14,
        "Focus 'TAG_nested' builds arms_factory but its ai_will_do has no"
        " factor = 0 modifier with can_staff_an_arms_industry = no",
    ),
    (
        "missing-cross-country-tooltip",
        SCAN_PATH,
        26,
        "1 focus(es) fire an event to another nation without a TT_IF_THEY_ACCEPT"
        " tooltip: TAG_offer (line 26)",
    ),
    (
        "pp-malus-completion-reward",
        SCAN_PATH,
        11,
        "Focus 'TAG_quoted' completion_reward applies a PP malus (negative"
        " add_political_power) — focus time is the cost; verify this is intended",
    ),
    (
        "focus-default-write",
        SCAN_PATH,
        34,
        "Focus 'TAG_defaults' writes the engine default 'cancel_if_invalid = yes'"
        " - omit it",
    ),
    (
        "focus-always-no-bypass",
        SCAN_PATH,
        36,
        "Focus 'TAG_defaults' pairs available = { always = no } with a bypass"
        " - use a matching condition instead",
    ),
    ("focus-empty-block", SCAN_PATH, 35, "Focus 'TAG_defaults' has an empty block"),
]


def _rows(validator):
    return [
        (issue.category, issue.file, issue.line, issue.message)
        for issue in validator._issues
        if issue.category != "missing-loc-key"
    ]


def _run(tmp_path, workers=1):
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=workers)
    try:
        validator.run_validations()
        assert (validator._pool is not None) == (workers > 1)
    finally:
        if validator._pool is not None:
            validator._pool.terminate()
            validator._pool.join()
    return _rows(validator)


@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_every_scan_reports_the_exact_file_line_and_message(tmp_path, newline):
    _write(tmp_path, SCAN_PATH, SCAN_TREE.replace("\n", newline))

    assert _run(tmp_path) == SCAN_FINDINGS


def test_a_file_whose_tokens_sit_only_in_comments_reports_nothing(tmp_path):
    _write(
        tmp_path,
        SCAN_PATH,
        "focus_tree = {\n"
        "\tcountry = { tag = SWE }\n"
        "\tfocus = {\n"
        "\t\tid = TAG_commented x = 0 y = 0\n"
        "\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
        "\t\t# cancel_if_invalid = yes available = { always = no } bypass = { }\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\t# GER = { country_event = offer.1 } add_political_power = -5\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )

    assert _run(tmp_path) == []


def test_pooled_run_matches_the_in_process_run_in_order(tmp_path):
    """Twelve focus, event and scripted-effect files each cross the pool
    threshold. The hidden offer.1 event silences the cross-country finding and
    builder_7 makes TAG_calls a dockyard builder, so both pooled pre-passes
    show in the findings."""
    for index in range(12):
        _write(tmp_path, f"{FOCUS_DIR}/scan_{index:02}.txt", SCAN_TREE)
        _write(
            tmp_path,
            f"events/ev_{index:02}.txt",
            f"country_event = {{ id = offer.{index} hidden = yes }}\n",
        )
        _write(
            tmp_path,
            f"common/scripted_effects/fx_{index:02}.txt",
            f"builder_{index} = {{ add_building_construction = {{ type = dockyard }} }}\n",
        )
    calls = f"{FOCUS_DIR}/calls.txt"
    _write(
        tmp_path,
        calls,
        "focus_tree = { focus = { id = TAG_calls search_filters ="
        " { FOCUS_FILTER_INDUSTRY } completion_reward = { builder_7 = yes } } }\n",
    )

    in_process = _run(tmp_path, workers=1)
    pooled = _run(tmp_path, workers=2)

    assert pooled == in_process
    assert (
        "missing-can-staff-guard",
        calls,
        1,
        "Focus 'TAG_calls' builds dockyard but its ai_will_do has no factor = 0"
        " modifier with can_staff_an_dockyard = no",
    ) in in_process
    pp_malus = next(
        row for row in SCAN_FINDINGS if row[0] == "pp-malus-completion-reward"
    )
    assert (pp_malus[0], f"{FOCUS_DIR}/scan_11.txt", 11, pp_malus[3]) in in_process
    assert "missing-cross-country-tooltip" not in {row[0] for row in in_process}


def test_cache_hits_when_warm_and_recomputes_only_the_changed_file(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write(tmp_path, SCAN_PATH, SCAN_TREE)
    other = f"{FOCUS_DIR}/other.txt"
    _write(tmp_path, other, "focus_tree = { focus = { id = TAG_other } }\n")
    _write(
        tmp_path,
        "events/ev.txt",
        "country_event = { id = e.1 option = { } option = { } }\n",
    )
    _write(
        tmp_path, "common/scripted_effects/fx.txt", "fx = { add_political_power = 1 }\n"
    )
    cold = _run(tmp_path)

    paired = []
    original = V._brace_pairs

    def counted(text):
        paired.append(text)
        return original(text)

    def miss(*_args):
        raise AssertionError("expected a cache hit")

    monkeypatch.setattr(V, "_brace_pairs", counted)
    with monkeypatch.context() as patch:
        patch.setattr(V, "_parse_scripted_effect_file", miss)
        patch.setattr(V, "_is_tag_routed", miss)
        warm = _run(tmp_path)
    assert paired == []

    _write(tmp_path, other, "focus_tree = { focus = { id = TAG_renamed } }\n")
    changed = _run(tmp_path)

    assert warm == cold
    assert len(paired) == 1 and "TAG_renamed" in paired[0]
    assert (
        "missing-search-filters",
        other,
        1,
        "Focus 'TAG_renamed' missing search_filters",
    ) in changed
    assert [row for row in changed if "TAG_other" in row[3]] == []


STAGED_PATH = f"{FOCUS_DIR}/staged.txt"
UNSTAGED_PATH = f"{FOCUS_DIR}/unstaged.txt"
PER_FILE_SCANS = (
    "_scan_missing_search_filters",
    "_scan_ai_guards",
    "_scan_cross_country_fires",
    "_scan_pp_malus",
    "_scan_focus_structural",
    "_scan_focus_icons",
)


def _staged_mod(tmp_path):
    """A staged file that fires an offer and anchors on a focus defined only in
    the unstaged file, which carries findings of its own."""
    staged = _write(
        tmp_path,
        STAGED_PATH,
        "focus_tree = {\n"
        "\tcountry = { tag = SWE }\n"
        "\tfocus = {\n"
        "\t\tid = TAG_staged\n"
        "\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
        "\t\trelative_position_id = TAG_elsewhere\n"
        "\t\tcompletion_reward = { GER = { country_event = offer.1 } }\n"
        "\t}\n"
        "}\n",
    )
    _write(
        tmp_path,
        UNSTAGED_PATH,
        "focus_tree = { focus = { id = TAG_elsewhere"
        " completion_reward = { add_political_power = -5 } } }\n",
    )
    _write(tmp_path, "localisation/english/focus_l_english.yml", "l_english:\n")
    _write(tmp_path, "common/scripted_effects/fx.txt", "fx = { add_stability = 1 }\n")
    _write(tmp_path, "events/ev.txt", "country_event = { id = ev.1 hidden = yes }\n")
    return staged


def _staged_run(tmp_path, staged_files):
    validator = _validator(tmp_path, missing_icons=True)
    validator.staged_only = True
    validator.staged_files = staged_files
    validator.run_validations()
    return _rows(validator)


def _never(*_args, **_kwargs):
    raise AssertionError("a staged run read what it cannot report")


def test_staged_run_checks_only_the_staged_focus_file(tmp_path, monkeypatch):
    staged = _staged_mod(tmp_path)
    scanned = {name: [] for name in PER_FILE_SCANS}
    for name in PER_FILE_SCANS:
        original = getattr(V, name)

        def record(source, *payload, name=name, original=original):
            scanned[name].append(source.filepath)
            return original(source, *payload)

        monkeypatch.setattr(V, name, record)
    monkeypatch.setattr(V.Validator, "_load_focus_loc_values", _never)

    _staged_run(tmp_path, [staged])

    assert scanned == {name: [staged] for name in PER_FILE_SCANS}


def test_staged_run_with_no_focus_file_reads_nothing(tmp_path, monkeypatch):
    _staged_mod(tmp_path)
    loc = str(tmp_path / "localisation/english/focus_l_english.yml")
    for name in (
        "_parse_focus_text",
        "_scripted_effect_facts",
        "_notification_ids_in_file",
        *PER_FILE_SCANS,
    ):
        monkeypatch.setattr(V, name, _never)
    for method in ("_load_focus_loc_values", "_load_localisation_keys"):
        monkeypatch.setattr(V.Validator, method, _never)

    assert _staged_run(tmp_path, [loc]) == []


def test_staged_run_reports_the_staged_files_findings(tmp_path):
    """The offer still fires, the anchor resolves against the unstaged file,
    and the unstaged file's own PP malus stays out."""
    staged = _staged_mod(tmp_path)

    assert _staged_run(tmp_path, [staged]) == [
        (
            "focus-coordinate-unresolved",
            STAGED_PATH,
            3,
            "Focus tree 'tree at line 1': focus 'TAG_staged' has missing or nonnumeric coordinates",
        ),
        (
            "missing-cross-country-tooltip",
            STAGED_PATH,
            3,
            "1 focus(es) fire an event to another nation without a"
            " TT_IF_THEY_ACCEPT tooltip: TAG_staged (line 3)",
        ),
    ]


# --- parser, brace pairs and patterns ---------------------------------------

MISSING = f"{FOCUS_DIR}/gone.txt"


def test_read_mod_text_returns_empty_instead_of_raising(tmp_path):
    assert V._read_mod_text(str(tmp_path / MISSING), str(tmp_path)) == ""
    outside = str(tmp_path.parent / "outside.txt")
    assert V._read_mod_text(outside, str(tmp_path)) == ""


_UNREADABLE_WORKERS = {
    "icons": lambda source: source.icons(),
    "pp_malus": lambda source: source.pp_malus(),
    "missing_search_filters": lambda source: source.missing_search_filters(),
    "structural": lambda source: source.structural(),
    "relative_positions": lambda source: source.relative_positions(),
    "ai_guards": lambda source: source.ai_guards({}, frozenset()),
    "cross_country_fires": lambda source: source.cross_country_fires(frozenset()),
}


@pytest.mark.parametrize(
    "worker", _UNREADABLE_WORKERS.values(), ids=_UNREADABLE_WORKERS
)
def test_worker_returns_empty_for_an_unreadable_file(tmp_path, worker):
    assert worker(V._FocusFile(str(tmp_path / MISSING), str(tmp_path))) == []


def test_parse_focus_file_returns_an_empty_structure_for_an_unreadable_file(tmp_path):
    path = str(tmp_path / MISSING)
    assert V._FocusFile(path, str(tmp_path)).parse() == {
        "filepath": path,
        "trees": [],
        "shared_defs": {},
    }


EMPTY_BLOCKS = """focus_tree = {}
shared_focus = {}
shared_focus = {
\tx = 0
}
shared_focus = {
\tid = TAG_shared_s
\tx = 0
\ty = 0
\tcost = 1
\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\tprerequisite = { }
}
focus_tree = {
\tid = test_tree
\tshared_focus = TAG_shared_s
\tfocus = {}
\tfocus = {
\t\tx = 0
\t}
\tfocus = {
\t\tid = TAG_focus_a
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t\tprerequisite = { }
\t\tcompletion_reward = {
\t\t\tadd_building_construction = {}
\t\t\tadd_tech_bonus = {}
\t\t}
\t\tai_will_do = {}
\t}
\tfocus = {
\t\tid = TAG_focus_b
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t\tcompletion_reward = {}
\t\tai_will_do = {
\t\t\tbase = 1
\t\t\tmodifier = {}
\t\t}
\t}
\tfocus = {
\t\tid = TAG_focus_c
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t\tcompletion_reward = { add_political_power = 10 }
\t}
}
"""


def test_empty_blocks_and_id_less_focuses_are_skipped_by_the_parser(tmp_path):
    source = _source(tmp_path, EMPTY_BLOCKS)
    parsed = source.parse()

    assert parsed["shared_defs"] == {
        "TAG_shared_s": {"line": 6, "filepath": source.filepath, "prereq_groups": []}
    }
    assert len(parsed["trees"]) == 1
    tree = parsed["trees"][0]
    assert [f[0] for f in tree["focuses"]] == [
        "TAG_focus_a",
        "TAG_focus_b",
        "TAG_focus_c",
    ]
    assert tree["shared_refs"] == {"TAG_shared_s"}
    assert all(f[2] == [] for f in tree["focuses"])


def test_empty_blocks_are_skipped_by_the_per_focus_workers(tmp_path):
    source = _source(tmp_path, EMPTY_BLOCKS)

    assert source.icons() == []
    assert source.pp_malus() == []
    assert source.missing_search_filters() == []


def test_empty_reward_and_ai_will_do_blocks_yield_no_guard_facts(tmp_path):
    data = _source(tmp_path, EMPTY_BLOCKS).ai_guards({}, frozenset())

    assert [d["id"] for d in data] == [
        "TAG_shared_s",
        "TAG_focus_a",
        "TAG_focus_b",
        "TAG_focus_c",
    ]
    assert all(d["buildings"] == set() and d["guards"] == set() for d in data)
    assert all(d["has_cost"] is False for d in data)


def test_a_focus_brace_in_a_string_that_closes_past_its_tree_is_skipped(tmp_path):
    """Parsed inside the tree body, the quoted `focus = {` never closes there,
    so only the real focus after it is registered."""
    source = _source(
        tmp_path,
        "focus_tree = {\n"
        "\tid = tree_a\n"
        '\tlog = "focus = { id = TAG_in_string"\n'
        "\tfocus = { id = TAG_real }\n"
        "}\n"
        'x = { " }\n',
    )

    assert source.parse()["trees"] == [
        {"focuses": [("TAG_real", 4, [])], "shared_refs": set()}
    ]


BRACE_CASES = [
    'a = { log = "}" b = { c = { d = 1 } } }',
    'x = { s = "a \\" { b" }',
    '"{" y = { }',
    "} } stray = { inner = { } } {",
    "open = { never = { closes",
    "crlf = {\r\n\tk = { v = 1 }\r\n}",
    'q = { "unterminated { }',
]


@pytest.mark.parametrize("text", BRACE_CASES)
def test_brace_pairs_match_find_matching_brace_from_every_offset(text):
    pairs = V._brace_pairs(text)

    for start in range(len(text) + 1):
        assert V._block_at(text, start, pairs) == extract_block_from_text(
            text, start
        ), start


def test_brace_pairs_match_find_matching_brace_on_random_text():
    rng = random.Random(20261002)
    for _ in range(400):
        text = "".join(rng.choice('{}"\\ a\n') for _ in range(rng.randint(0, 40)))
        pairs = V._brace_pairs(text)
        for start in range(len(text) + 1):
            assert V._block_at(text, start, pairs) == extract_block_from_text(
                text, start
            ), (text, start)


def test_brace_pairs_record_unclosed_braces_and_skip_quoted_ones():
    #       0123456789012345678901
    text = 'a { b { } " { " } { c'

    assert V._brace_pairs(text) == {2: 16, 6: 8, 18: -1}


HELPER_TEXT = (
    "focus = {}\n"
    "shared_focus = {\n"
    "\tid = TAG_s\n"
    '\tcompletion_reward = { log = "}" add_stability = 0.1 }\n'
    "\tcompletion_reward_joint_member = { a = { b = { c = 1 } } }\n"
    "}\n"
    "joint_focus = { x = 1 }\n"
    "focus = { id = TAG_open completion_reward = { never_closes = {\n"
)
HELPER_BLOCKS = [
    (
        "TAG_s",
        '\n\tid = TAG_s\n\tcompletion_reward = { log = "}" add_stability = 0.1 }\n'
        "\tcompletion_reward_joint_member = { a = { b = { c = 1 } } }\n",
        11,
        156,
    ),
    (None, " x = 1 ", 157, 180),
]
HELPER_REWARDS = [
    (' log = "}" add_stability = 0.1 ', 41, 94),
    (" a = { b = { c = 1 } } ", 96, 154),
]


@pytest.mark.parametrize("with_pairs", [False, True], ids=["old-call", "pairs"])
def test_imported_iterators_keep_their_output(with_pairs):
    """validate_variables calls both without pairs; the output is the same."""
    kwargs = {"pairs": V._brace_pairs(HELPER_TEXT)} if with_pairs else {}

    assert list(V._iter_focus_blocks_with_id(HELPER_TEXT, **kwargs)) == HELPER_BLOCKS
    assert list(V._iter_reward_blocks(HELPER_TEXT, 11, 156, **kwargs)) == (
        HELPER_REWARDS
    )
    assert list(V._iter_reward_blocks(HELPER_TEXT, 157, 180, **kwargs)) == []
    # The first reward opens inside the span but closes past it.
    assert list(V._iter_reward_blocks(HELPER_TEXT, 11, 70, **kwargs)) == []


# Each pattern now leads with its literal; it must match exactly where its
# `\b`-led original did, near misses included.
WORD_BOUNDARY_ORIGINALS = {
    "_FOCUS_TREE_START": r"\bfocus_tree\s*=\s*\{",
    "_SHARED_FOCUS_DEF_START": r"\b(?:shared_focus|joint_focus)\s*=\s*\{",
    "_FOCUS_ID_RE": r"\bfocus\s*=\s*\{",
    "_ICON_LINE_RE": r'\bicon\s*=\s*(?:"([^"]*)"|([^\s{}]+))',
    "_RELATIVE_POSITION_RE": r"\brelative_position_id\s*=\s*(\S+)",
    "_PREREQ_BLOCK_RE": r"\bprerequisite\s*=\s*\{([^}]*)\}",
    "_SHARED_REF_RE": r"\bshared_focus\s*=\s*(\w+)",
    "_REWARD_BLOCK_RE": (
        r"\bcompletion_reward(?:_joint_originator|_joint_member)?\s*=\s*\{"
    ),
    "_EFFECT_TOOLTIP_START": r"\beffect_tooltip\s*=\s*\{",
    "_PP_MALUS_RE": r"\badd_political_power\s*=\s*(-\d+(?:\.\d+)?)\b",
    "_AI_WILL_DO_START": r"\bai_will_do\s*=\s*\{",
    "_MODIFIER_START": r"\bmodifier\s*=\s*\{",
    "_ADD_BUILDING_START": r"\badd_building_construction\s*=\s*\{",
    "_TREASURY_CHANGE_RE": (
        r"\btreasury_change\s*=\s*(-?\d+(?:\.\d+)?|\{|[A-Za-z_][\w.]*)"
        r"|\bvar\s*=\s*treasury_change\b"
    ),
    "_MODIFY_TREASURY_RE": r"\bmodify_treasury_effect(\w*)\s*=\s*yes\b",
    "_MODIFY_DEBT_RE": r"\bmodify_debt_effect\s*=\s*yes\b",
    "_SEARCH_FILTERS_RE": r"\bsearch_filters\s*=\s*\{([^{}]*)\}",
    "_COUNTRY_EVENT_RE": r"\bcountry_event\b",
    "_EVENT_OPTION_RE": r"\boption\s*=\s*\{",
    "_EVENT_HIDDEN_RE": r"\bhidden\s*=\s*yes\b",
    "_FT_COUNTRY_BLOCK_RE": r"\bcountry\s*=\s*\{",
    "_RE_EMPTY_MUTEX": r"\bmutually_exclusive\s*=\s*\{\s*\}",
    "_RE_EMPTY_AVAILABLE": r"\bavailable\s*=\s*\{\s*\}",
}

PATTERN_SAMPLE = "\n".join(
    f"{prefix}{keyword} = {value}"
    for prefix in ("", "x", "_", ".", "é", "\t")
    for keyword in (
        "focus_tree",
        "shared_focus",
        "joint_focus",
        "focus",
        "icon",
        "relative_position_id",
        "prerequisite",
        "completion_reward",
        "completion_reward_joint_member",
        "effect_tooltip",
        "add_political_power",
        "ai_will_do",
        "modifier",
        "add_building_construction",
        "treasury_change",
        "var",
        "modify_treasury_effect",
        "modify_treasury_effect_corruption",
        "modify_debt_effect",
        "search_filters",
        "country_event",
        "option",
        "hidden",
        "country",
        "mutually_exclusive",
        "available",
    )
    for value in ("{ }", "{ focus = a }", "yes", "-5", "treasury_change", '"GFX x"')
)


@pytest.mark.parametrize("name", sorted(WORD_BOUNDARY_ORIGINALS))
def test_literal_led_patterns_match_where_their_word_boundary_originals_did(name):
    original = re.compile(WORD_BOUNDARY_ORIGINALS[name])
    expected = [(m.span(), m.groups()) for m in original.finditer(PATTERN_SAMPLE)]

    found = getattr(V, name).finditer(PATTERN_SAMPLE)

    assert [(m.span(), m.groups()) for m in found] == expected
    assert expected


def test_anonymous_block_has_no_label():
    body = "color = { { 1 } }"
    label, opener = V._enclosing_block_label(body, body.index("1"))
    assert label is None
    assert body[opener] == "{"


@pytest.mark.parametrize(
    "text, end",
    [
        ("effect_tooltip = {}\nadd_political_power = -5\n", None),
        ("effect_tooltip = { add_political_power = -5 }", 20),
    ],
    ids=["empty body", "body past the bounds"],
)
def test_effect_tooltip_span_needs_a_body_inside_the_bounds(text, end):
    assert V._effect_tooltip_spans(text, 0, len(text) if end is None else end) == []


# --- search filters ---------------------------------------------------------


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("} search_filters = { A }", {"A"}),
        ("x = { search_filters = { B } } search_filters = { C D }", {"C", "D"}),
        ("x = { search_filters = { B } }", set()),
        ("search_filters = { E } search_filters = { F }", {"E"}),
        ("my_search_filters = { G }", set()),
    ],
)
def test_top_level_search_filters(body, expected):
    assert V._top_level_search_filters(body) == expected


@pytest.mark.parametrize(
    "fields",
    [
        "",
        "completion_reward = {\n\t\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n\t\t}",
    ],
    ids=["no search_filters", "search_filters only in a nested block"],
)
def test_focus_without_top_level_search_filters_warns(tmp_path, fields):
    _focus_file(
        tmp_path,
        "focus_tree = {\n\tid = test_tree\n"
        "\tfocus = {\n\t\tid = TAG_focus_a\n\t\tx = 1\n\t\ty = 1\n\t\tcost = 1\n"
        f"\t\t{fields}\n\t}}\n}}\n",
    )
    v = _validator(tmp_path)
    v.validate_missing_search_filters()

    assert [(i.category, i.severity, i.message) for i in v._issues] == [
        (
            "missing-search-filters",
            V.Severity.WARNING,
            "Focus 'TAG_focus_a' missing search_filters",
        )
    ]


def test_search_filter_worker_checks_shared_and_joint_focus_blocks(tmp_path):
    source = _source(
        tmp_path,
        "shared_focus = {\n"
        "\tid = TAG_shared_a\n\tx = 1\n\ty = 1\n\tcost = 1\n"
        "\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
        "}\n\n"
        "joint_focus = {\n\tid = TAG_joint_a\n\tx = 3\n\ty = 3\n\tcost = 1\n}\n\n"
        "focus_tree = {\n\tid = test_tree\n"
        "\tfocus = {\n\t\tid = TAG_focus_a\n\t\tcost = 1\n\t\tx = 5\n\t\ty = 5\n\t}\n"
        "}\n",
    )

    missing = source.missing_search_filters()
    assert {item[0] for item in missing} == {"TAG_joint_a", "TAG_focus_a"}


# --- PP malus ---------------------------------------------------------------

PP_TEMPLATE = """focus_tree = {{
\tid = test_tree
\tfocus = {{
\t\tid = TAG_focus_a
\t\tx = 0
\t\ty = 0
\t\tcost = 1
\t\t{extra}
\t\tcompletion_reward = {{
\t\t\t{reward}
\t\t}}
\t}}
}}
"""

# case: (completion_reward body, other focus fields, flagged focus IDs)
_PP_MALUS_CASES = {
    "negative PP in the reward": ("add_political_power = -50", "", {"TAG_focus_a"}),
    "positive PP": ("add_political_power = 50", "", set()),
    "negative PP inside an effect_tooltip": (
        "effect_tooltip = {\n\t\t\t\tadd_political_power = -50\n\t\t\t}",
        "",
        set(),
    ),
    "negative PP in select_effect": (
        "newline = yes",
        "select_effect = {\n\t\t\tadd_political_power = -50\n\t\t}",
        set(),
    ),
    "negative PP in bypass": (
        "newline = yes",
        "bypass = {\n\t\t\tadd_political_power = -50\n\t\t}",
        set(),
    ),
    "variable PP": ("add_political_power = some_var", "", set()),
}


@pytest.mark.parametrize(
    "reward, extra, expected", _PP_MALUS_CASES.values(), ids=_PP_MALUS_CASES
)
def test_pp_malus_worker(tmp_path, reward, extra, expected):
    source = _source(tmp_path, PP_TEMPLATE.format(reward=reward, extra=extra))
    assert {d[0] for d in source.pp_malus()} == expected


@pytest.mark.parametrize(
    "focus_id, warnings",
    [("TAG_focus_a", 1), (sorted(V._PP_MALUS_EXEMPT_FOCUS_IDS)[0], 0)],
    ids=["warning, not error", "exempt focus"],
)
def test_pp_malus_report(tmp_path, focus_id, warnings):
    _focus_file(
        tmp_path,
        PP_TEMPLATE.format(reward="add_political_power = -100", extra="").replace(
            "TAG_focus_a", focus_id
        ),
    )
    v = _validator(tmp_path)
    v.validate_pp_malus_in_rewards()
    assert (v.warnings_found, v.errors_found) == (warnings, 0)


# --- ai_will_do guards ------------------------------------------------------

FOCUS_TEMPLATE = """focus_tree = {{
\tid = test_tree
\tfocus = {{
\t\tid = TAG_focus_a
\t\tx = 0
\t\ty = 0
\t\tcost = 2
\t\t{extra}
\t\tcompletion_reward = {{
\t\t\t{reward}
\t\t}}
\t\tai_will_do = {{
\t\t\tbase = 1
\t\t\t{modifiers}
\t\t}}
\t}}
}}
"""

GUARD_FLAT_FORM = """modifier = {
\t\t\t\tfactor = 0
\t\t\t\tcan_staff_an_industrial_complex = no
\t\t\t}"""

BANKRUPTCY_GUARD = """modifier = {
\t\t\t\tfactor = 0
\t\t\t\thas_active_mission = bankruptcy_incoming_collapse
\t\t\t}"""

EFFECTS = """one_random_industrial_complex = {
\trandom_owned_controlled_state = {
\t\tadd_building_construction = {
\t\t\ttype = industrial_complex
\t\t\tlevel = 1
\t\t\tinstant_build = yes
\t\t}
\t}
}
grant_pp_effect = {
\tadd_political_power = 25
}
"""

STAFFABLE_MAP = {"one_random_industrial_complex": frozenset({"industrial_complex"})}


def _write_effects_file(tmp_path, extra=""):
    _write(tmp_path, "common/scripted_effects/00_scripted_effects.txt", EFFECTS + extra)


def _spend(amount):
    """A reward that sets treasury_change and applies it via the budget effect."""
    return (
        f"set_temp_variable = {{ treasury_change = {amount} }}\n"
        "\t\t\tmodify_treasury_effect = yes"
    )


def _guard_facts(tmp_path, reward, modifiers=""):
    source = _source(
        tmp_path,
        FOCUS_TEMPLATE.format(extra="", reward=reward, modifiers=modifiers),
    )
    return source.ai_guards(STAFFABLE_MAP, frozenset())


def test_scripted_effect_facts_resolve_direct_and_wrapper_chains(tmp_path):
    _write_effects_file(
        tmp_path,
        extra="direct_builder = {\n\tadd_building_construction = {\n"
        "\t\ttype = arms_factory\n\t}\n}\n"
        "builder_wrapper = {\n\tdirect_builder = yes\n}\n"
        "builder_outer = {\n\tbuilder_wrapper = yes\n}\n"
        "direct_money = {\n\tset_temp_variable = { treasury_change = -7 }\n"
        "\tmodify_treasury_effect = yes\n}\n"
        "money_wrapper = {\n\tdirect_money = yes\n}\n"
        "money_outer = {\n\tmoney_wrapper = yes\n}\n",
    )
    validator = _validator(tmp_path)

    staffable = validator._staffable_effect_map()
    money = validator._money_cost_effect_names()
    assert staffable["direct_builder"] == frozenset({"arms_factory"})
    assert staffable["builder_outer"] == frozenset({"arms_factory"})
    assert {"direct_money", "money_wrapper", "money_outer"} <= money


def test_scripted_effect_sources_are_read_once_for_both_indexes(tmp_path, monkeypatch):
    _write_effects_file(tmp_path)
    reads = []
    original = V._read_scripted_effect_file

    def read(filepath, mod_path):
        reads.append(filepath)
        return original(filepath, mod_path)

    monkeypatch.setattr(V, "_read_scripted_effect_file", read)
    validator = _validator(tmp_path)
    validator._staffable_effect_map()
    validator._money_cost_effect_names()

    assert len(reads) == 1


def test_scripted_effect_parser_skips_empty_blocks():
    text = (
        "empty_effect = {}\n"
        "builder = {\n"
        "\tadd_building_construction = {}\n"
        "\tadd_building_construction = {\n"
        "\t\ttype = arms_factory\n"
        "\t}\n"
        "}\n"
    )
    bodies, staffable, money = V._parse_scripted_effect_file(text)

    assert "empty_effect" not in bodies
    assert staffable == {"builder": frozenset({"arms_factory"})}
    assert money == frozenset()


_ARMS_FACTORY = (
    "add_building_construction = {\n"
    "\t\t\t\ttype = arms_factory\n"
    "\t\t\t\tlevel = 1\n"
    "\t\t\t\tinstant_build = yes\n"
    "\t\t\t}"
)


def _factor_zero(*conditions):
    return "modifier = {\n\t\t\t\tfactor = 0\n\t\t\t\t" + "\n".join(conditions) + "\n}"


# case: (completion_reward body, ai_will_do modifiers, buildings, guards)
_STAFF_GUARD_CASES = {
    "OR guard": (
        "one_random_industrial_complex = yes",
        _factor_zero(
            "OR = {\nhas_active_mission = bankruptcy_incoming_collapse\n"
            "can_staff_an_industrial_complex = no\n}"
        ),
        {"industrial_complex"},
        set(),
    ),
    "AND guard": (
        "one_random_industrial_complex = yes",
        _factor_zero(
            "AND = {\nhas_active_mission = bankruptcy_incoming_collapse\n"
            "can_staff_an_industrial_complex = no\n}"
        ),
        {"industrial_complex"},
        {"bankruptcy_incoming_collapse", "can_staff_an_industrial_complex"},
    ),
    "NOT yes guard": (
        "one_random_industrial_complex = yes",
        _factor_zero("NOT = { can_staff_an_industrial_complex = yes }"),
        {"industrial_complex"},
        {"can_staff_an_industrial_complex"},
    ),
    "negated guard under OR": (
        "add_building_construction = { type = arms_factory level = 1 }",
        _factor_zero(
            "OR = {\nNOT = { can_staff_an_arms_industry = yes }\n"
            "has_country_flag = TAG_flag\n}"
        ),
        {"arms_factory"},
        set(),
    ),
    "guard with a nonzero factor": (
        "one_random_industrial_complex = yes",
        "modifier = {\nfactor = 0.5\ncan_staff_an_industrial_complex = no\n}",
        {"industrial_complex"},
        set(),
    ),
    "direct add_building_construction": (_ARMS_FACTORY, "", {"arms_factory"}, set()),
    "building inside an effect_tooltip": (
        "GER = { country_event = x.1 }\n"
        "\t\t\tcustom_effect_tooltip = TT_IF_THEY_ACCEPT\n"
        "\t\t\teffect_tooltip = {\n\t\t\t\tGER = {\n\t\t\t\t\t"
        + _ARMS_FACTORY
        + "\n\t\t\t\t}\n\t\t\t}",
        "",
        set(),
        set(),
    ),
    "builder effect inside an effect_tooltip": (
        "effect_tooltip = {\n\t\t\t\tone_random_industrial_complex = yes\n\t\t\t}",
        "",
        set(),
        set(),
    ),
    "building beside an effect_tooltip": (
        _ARMS_FACTORY
        + "\n\t\t\teffect_tooltip = {\n\t\t\t\tone_random_industrial_complex = yes\n"
        "\t\t\t}",
        "",
        {"arms_factory"},
        set(),
    ),
}


@pytest.mark.parametrize(
    "reward, modifiers, buildings, guards",
    _STAFF_GUARD_CASES.values(),
    ids=_STAFF_GUARD_CASES,
)
def test_staff_guard_facts(tmp_path, reward, modifiers, buildings, guards):
    (facts,) = _guard_facts(tmp_path, reward, modifiers)
    assert (facts["buildings"], facts["guards"]) == (buildings, guards)


def _gdp_scale(source, factor):
    return (
        f"set_temp_variable = {{ treasury_change = {source} }}\n"
        f"multiply_temp_variable = {{ treasury_change = {factor} }}\n"
        "modify_treasury_effect = yes"
    )


_SPEND_MONEY = frozenset({"spend_money_effect"})

# case: (completion_reward body, money-spending effects, (spend, has_cost, unknown))
_MONEY_COST_CASES = {
    "negative changes add up": (
        _spend(-7) + "\n" + _spend(-3),
        frozenset(),
        (10.0, True, False),
    ),
    "positive change is income": (_spend(50), frozenset(), (0.0, False, False)),
    "change applied twice": (
        "set_temp_variable = { treasury_change = -3 }\n"
        "modify_treasury_effect = yes\n"
        "modify_treasury_effect = yes",
        frozenset(),
        (6.0, True, False),
    ),
    "largest spend across if and else": (
        "if = {\n"
        "\tlimit = { original_tag = SAU }\n"
        "\tset_temp_variable = { treasury_change = -14 }\n"
        "}\n"
        "else = { set_temp_variable = { treasury_change = -3.5 } }\n"
        "modify_treasury_effect = yes",
        frozenset(),
        (14.0, True, False),
    ),
    "corruption variant of the treasury effect": (
        "set_temp_variable = { treasury_change = -7 }\n"
        "modify_treasury_effect_corruption = yes",
        frozenset(),
        (0.0, True, True),
    ),
    "computed change": (
        "set_temp_variable = { treasury_change = { value = 5 multiply = -1 } }\n"
        "modify_treasury_effect = yes",
        frozenset(),
        (0.0, True, True),
    ),
    "bare identifier change": (
        "set_temp_variable = { treasury_change = needed_money }\n"
        "modify_treasury_effect = yes",
        frozenset(),
        (0.0, True, True),
    ),
    "change mutated by a variable": (
        "set_temp_variable = { treasury_change = -4 }\n"
        "add_to_temp_variable = { treasury_change = extra_cost }\n"
        "modify_treasury_effect = yes\n",
        frozenset(),
        (0.0, True, True),
    ),
    "apply with no set": (
        "modify_treasury_effect = yes\n",
        frozenset(),
        (0.0, True, True),
    ),
    "check_variable only reads the change": (
        "check_variable = { treasury_change = 0 }\n",
        frozenset(),
        (0.0, False, False),
    ),
    "spend inside an effect_tooltip": (
        "effect_tooltip = {\n" + _spend(-20) + "\n}",
        frozenset(),
        (0.0, False, False),
    ),
    "modify_debt_effect": (
        "modify_debt_effect = yes\n",
        frozenset(),
        (0.0, True, True),
    ),
    "modify_debt_effect inside an effect_tooltip": (
        "effect_tooltip = { modify_debt_effect = yes }\n",
        frozenset(),
        (0.0, False, False),
    ),
    "money effect after unrelated keys": (
        "add_political_power = 5\nspend_money_effect = yes\n",
        _SPEND_MONEY,
        (0.0, True, True),
    ),
    "no money key": (
        "add_political_power = 5\nadd_stability = 0.05\n",
        _SPEND_MONEY,
        (0.0, False, False),
    ),
    # The multiply's own literal used to be misread as a fresh set.
    "gdp_total scaled by a negative": (
        _gdp_scale("gdp_total", -0.05),
        frozenset(),
        (0.0, True, True),
    ),
    "gdp_total scaled by a positive is income": (
        _gdp_scale("gdp_total", 0.05),
        frozenset(),
        (0.0, False, False),
    ),
    "gdp_per_capita scaled by a positive is income": (
        _gdp_scale("gdp_per_capita", 0.18),
        frozenset(),
        (0.0, False, False),
    ),
    "scoped gdp source keeps its sign": (
        _gdp_scale("GER.gdp_per_capita", 0.02),
        frozenset(),
        (0.0, False, False),
    ),
    "signed variable scaled by a positive": (
        _gdp_scale("signed_balance", 0.05),
        frozenset(),
        (0.0, True, True),
    ),
    "scoped unknown source": (
        _gdp_scale("JAP.int_investments", 0.07),
        frozenset(),
        (0.0, True, True),
    ),
    # Sibling branches are alternatives, not a chain that toggles the sign.
    "negative scales in sibling branches": (
        "set_temp_variable = { treasury_change = gdp_per_capita }\n"
        "if = {\n"
        "\tlimit = { has_country_flag = flag_a }\n"
        "\tmultiply_temp_variable = { treasury_change = -0.225 }\n"
        "}\n"
        "else = {\n"
        "\tmultiply_temp_variable = { treasury_change = -0.25 }\n"
        "}\n"
        "modify_treasury_effect = yes",
        frozenset(),
        (0.0, True, True),
    ),
    "spending branch beside a gdp income branch": (
        "if = {\n"
        "\tlimit = { has_country_flag = flag_a }\n"
        "\tset_temp_variable = { treasury_change = -20 }\n"
        "}\n"
        "else = {\n"
        "\tset_temp_variable = { treasury_change = gdp_total }\n"
        "\tmultiply_temp_variable = { treasury_change = 0.05 }\n"
        "}\n"
        "modify_treasury_effect = yes",
        frozenset(),
        (0.0, True, True),
    ),
}


@pytest.mark.parametrize(
    "body, money, expected", _MONEY_COST_CASES.values(), ids=_MONEY_COST_CASES
)
def test_body_money_cost(body, money, expected):
    assert V._body_money_cost(body, money) == expected


def test_money_effect_called_only_inside_a_preview_keeps_the_guard(tmp_path):
    """The reward previews a scripted spend it never makes, so the bankruptcy
    guard is not reported as unneeded and the spend is not counted."""
    _write(
        tmp_path,
        "common/scripted_effects/spend.txt",
        "spend_money_effect = {\n"
        "\tset_temp_variable = { treasury_change = -10 }\n"
        "\tmodify_treasury_effect = yes\n"
        "}\n",
    )
    path = _write(
        tmp_path,
        SCAN_PATH,
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tid = TAG_preview x = 0 y = 0\n"
        "\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\teffect_tooltip = { spend_money_effect = yes }\n"
        "\t\t}\n"
        "\t\tai_will_do = {\n"
        "\t\t\tbase = 1\n"
        "\t\t\tmodifier = {\n"
        "\t\t\t\tfactor = 0\n"
        "\t\t\t\thas_active_mission = bankruptcy_incoming_collapse\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )

    facts = V._FocusFile(path, str(tmp_path)).ai_guards(
        {}, frozenset({"spend_money_effect"})
    )

    assert [
        (d["id"], d["line"], d["has_cost"], d["previewed_cost"]) for d in facts
    ] == [("TAG_preview", 2, False, True)]
    assert _run(tmp_path) == []


def _staff_message(focus_id="TAG_focus_a"):
    return (
        f"Focus '{focus_id}' builds industrial_complex but its ai_will_do has no"
        " factor = 0 modifier with can_staff_an_industrial_complex = no"
    )


_ENERGY_CHAIN = (
    "factory_with_energy_check = {\n"
    "\tif = {\n"
    "\t\tlimit = { check_variable = { energy_deficit < 1 } }\n"
    "\t\tone_random_industrial_complex = yes\n"
    "\t}\n"
    "}\n"
    "deep_factory_with_energy_check = {\n"
    "\tfactory_with_energy_check = yes\n"
    "}\n"
)
_SPEND_EFFECT = (
    "spend_money_effect = {\n"
    "\tset_temp_variable = { treasury_change = -10 }\n"
    "\tmodify_treasury_effect = yes\n"
    "}\n"
)
_PREVIEWED_SPEND = (
    "FRA = { country_event = { id = test.1 days = 1 } }\n"
    "\t\t\tcustom_effect_tooltip = TT_IF_THEY_ACCEPT\n"
    "\t\t\teffect_tooltip = {\n"
    "\t\t\t\tset_temp_variable = { treasury_change = -6 }\n"
    "\t\t\t\tmodify_treasury_effect = yes\n"
    "\t\t\t}"
)

# case: (extra scripted effects, other focus fields, reward, modifiers,
#        (category, message) per finding)
_GUARD_REPORT_CASES = {
    "building without a guard": (
        "",
        "",
        "one_random_industrial_complex = yes",
        "",
        [("missing-can-staff-guard", _staff_message())],
    ),
    "building with a guard": (
        "",
        "",
        "one_random_industrial_complex = yes",
        GUARD_FLAT_FORM,
        [],
    ),
    "effect that neither builds nor spends": ("", "", "grant_pp_effect = yes", "", []),
    "builder behind an effect chain": (
        _ENERGY_CHAIN,
        "",
        "deep_factory_with_energy_check = yes",
        "",
        [("missing-can-staff-guard", _staff_message())],
    ),
    "spend at the threshold": (
        "",
        "",
        _spend(-5),
        "",
        [
            (
                "missing-bankruptcy-guard",
                "1 focus(es) spending >= 5bn without the bankruptcy guard:"
                " TAG_focus_a (line 3)",
            )
        ],
    ),
    "spend below the threshold": ("", "", _spend(-3), "", []),
    "spend with the guard": ("", "", _spend(-7), BANKRUPTCY_GUARD, []),
    "scripted spend without the guard": (
        _SPEND_EFFECT,
        "",
        "spend_money_effect = yes",
        "",
        [
            (
                "missing-bankruptcy-guard-scripted",
                "1 focus(es) spending money via a scripted effect (amount unknown)"
                " without the bankruptcy guard: TAG_focus_a (line 3)",
            )
        ],
    ),
    "guard without a cost": (
        "",
        "",
        "add_political_power = 50",
        BANKRUPTCY_GUARD,
        [
            (
                "unneeded-bankruptcy-guard",
                "1 focus(es) with a bankruptcy guard but no money cost (guard"
                " unneeded): TAG_focus_a (line 3)",
            )
        ],
    ),
    "guard on a cost paid in a preview": (
        "",
        "",
        _PREVIEWED_SPEND,
        BANKRUPTCY_GUARD,
        [],
    ),
    "money focus without an economic filter": (
        "",
        "search_filters = { FOCUS_FILTER_POLITICAL }",
        _spend(-7),
        BANKRUPTCY_GUARD,
        [
            (
                "focus-filter-mismatch",
                "1 money/building focus(es) tagged neither economic nor military"
                " (search_filter mismatch): TAG_focus_a (line 3)",
            )
        ],
    ),
    "money focus with an economic filter": (
        "",
        "search_filters = { FOCUS_FILTER_ECONOMY }",
        _spend(-7),
        BANKRUPTCY_GUARD,
        [],
    ),
}


@pytest.mark.parametrize(
    "effects, extra, reward, modifiers, expected",
    _GUARD_REPORT_CASES.values(),
    ids=_GUARD_REPORT_CASES,
)
def test_ai_will_do_guards(tmp_path, effects, extra, reward, modifiers, expected):
    _write_effects_file(tmp_path, effects)
    _focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(extra=extra, reward=reward, modifiers=modifiers),
    )
    v = _validator(tmp_path)
    v.validate_ai_will_do_guards()

    assert [(i.category, i.message) for i in v._issues] == expected
    assert v.warnings_found == len(expected)


def test_bankruptcy_warnings_aggregate_per_file(tmp_path):
    _write_effects_file(tmp_path)
    focus = (
        "\tfocus = {\n"
        "\t\tid = {id}\n"
        "\t\tx = 0\n"
        "\t\ty = 0\n"
        "\t\tcost = 2\n"
        "\t\tcompletion_reward = { " + _spend(-7) + " }\n"
        "\t\tai_will_do = { base = 1 }\n"
        "\t}\n"
    )
    _focus_file(
        tmp_path,
        "focus_tree = {\n\tid = test_tree\n"
        + focus.replace("{id}", "TAG_focus_a")
        + focus.replace("{id}", "TAG_focus_b")
        + "}\n",
    )
    v = _validator(tmp_path)
    v.validate_ai_will_do_guards()

    assert _messages(v) == [
        "2 focus(es) spending >= 5bn without the bankruptcy guard:"
        " TAG_focus_a (line 3), TAG_focus_b (line 12)"
    ]


# --- cross-country event tooltips -------------------------------------------

OWNER = frozenset({"BUL"})

# case: (completion_reward body, the fire is foreign)
_FIRE_TARGET_CASES = {
    "literal foreign tag": ("GER = { country_event = { id = x.1 } }", True),
    "bare fire": ("country_event = x.1", False),
    "ROOT scope": ("ROOT = { country_event = x.1 }", False),
    "owner tag": ("BUL = { country_event = x.1 }", False),
    "inside an if": (
        "if = { limit = { country_exists = TUR } TUR = { country_event = x.1 } }",
        True,
    ),
    "inside a control-flow wrapper": (
        "random = { FRA = { country_event = x.1 } }",
        True,
    ),
    "inside hidden_effect": (
        "hidden_effect = { FRA = { country_event = x.1 } }",
        False,
    ),
    "hidden_effect above a wrapper": (
        "hidden_effect = { if = { limit = { x = y } FRA = { country_event = x.1 } } }",
        False,
    ),
    "country iterator": ("every_other_country = { country_event = x.1 }", True),
    "event target": ("event_target:foe = { country_event = x.1 }", True),
    "logic keyword": ("NOT = { country_event = x.1 }", False),
}


@pytest.mark.parametrize(
    "body, foreign", _FIRE_TARGET_CASES.values(), ids=_FIRE_TARGET_CASES
)
def test_country_event_target_is_foreign(body, foreign):
    assert (
        V._country_event_target_is_foreign(body, body.index("country_event"), OWNER)
        is foreign
    )


TREE_TEMPLATE = """focus_tree = {{
\tid = test_tree
\tcountry = {{
\t\tfactor = 0
\t\tmodifier = {{
\t\t\tadd = 20
\t\t\ttag = BUL
\t\t}}
\t}}
\tfocus = {{
\t\tid = BUL_focus_a
\t\tx = 0
\t\ty = 0
\t\tcost = 1
\t\tcompletion_reward = {{
\t\t\t{reward}
\t\t}}
\t}}
}}
"""

_OFFER = "GER = { country_event = { id = x.1 days = 1 } }"

# case: (completion_reward body, notification event IDs, focus flagged)
_CROSS_COUNTRY_CASES = {
    "foreign fire without a tooltip": (_OFFER, frozenset(), True),
    "TT_IF_THEY_ACCEPT": (
        _OFFER + "\n\t\t\tcustom_effect_tooltip = TT_IF_THEY_ACCEPT",
        frozenset(),
        False,
    ),
    "TT_IF_THIS_ACCEPTS inside the target scope": (
        "GER = {\n"
        "\t\t\t\tcountry_event = x.1\n"
        "\t\t\t\tcustom_effect_tooltip = TT_IF_THIS_ACCEPTS\n"
        "\t\t\t}\n"
        "\t\t\teffect_tooltip = { add_stability = 0.05 }",
        frozenset(),
        False,
    ),
    "TT_IF_EACH_ACCEPTS": (
        "custom_effect_tooltip = TT_IF_EACH_ACCEPTS\n"
        "\t\t\teffect_tooltip = { add_stability = 0.05 }\n"
        "\t\t\tGER = { country_event = x.1 }\n"
        "\t\t\tFRA = { country_event = x.1 }",
        frozenset(),
        False,
    ),
    "owner tag from the country block": (
        "BUL = { country_event = x.1 }",
        frozenset(),
        False,
    ),
    "notification target": (_OFFER, frozenset({"x.1"}), False),
    "bare notification target": (
        "GER = { country_event = x.1 }",
        frozenset({"x.1"}),
        False,
    ),
    "unrelated notification": (_OFFER, frozenset({"other.9"}), True),
    # The preview shows what a decision does elsewhere.
    "fire inside an effect_tooltip": (
        "activate_decision = d\n\t\t\teffect_tooltip = { GER = { country_event = x.1 } }",
        frozenset(),
        False,
    ),
}


@pytest.mark.parametrize(
    "reward, notifications, flagged",
    _CROSS_COUNTRY_CASES.values(),
    ids=_CROSS_COUNTRY_CASES,
)
def test_cross_country_fires(tmp_path, reward, notifications, flagged):
    source = _source(tmp_path, TREE_TEMPLATE.format(reward=reward))
    fires = source.cross_country_fires(notifications)
    assert [d["id"] for d in fires] == (["BUL_focus_a"] if flagged else [])


def test_cross_country_owner_from_original_tag(tmp_path):
    tree = TREE_TEMPLATE.replace("tag = BUL", "original_tag = BUL").format(
        reward="BUL = { country_event = x.1 }"
    )
    assert _source(tmp_path, tree).cross_country_fires(frozenset()) == []


def test_cross_country_worker_handles_an_empty_country_block(tmp_path):
    """With no owner tag declared, a literal tag scope is still foreign."""
    source = _source(
        tmp_path,
        "focus_tree = {\n"
        "\tid = test_tree\n"
        "\tcountry = {}\n"
        "\tfocus = {\n\t\tx = 0\n\t}\n"
        "\tfocus = {\n"
        "\t\tid = TAG_focus_a\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tGER = { country_event = foo.1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    data = source.cross_country_fires(frozenset())
    assert [d["id"] for d in data] == ["TAG_focus_a"]


def _cross_country_tree(count):
    lines = ["focus_tree = {", "\tid = tree_a", "\tcountry = { tag = SWE }"]
    for i in range(count):
        lines += [
            "\tfocus = {",
            f"\t\tid = TAG_focus_{i}",
            f"\t\tx = {i * 2}",
            "\t\ty = 0",
            "\t\tcost = 1",
            "\t\tcompletion_reward = {",
            f"\t\t\tGER = {{ country_event = offer.{i} }}",
            "\t\t}",
            "\t}",
        ]
    lines.append("}")
    return "\n".join(lines) + "\n"


def test_cross_country_findings_aggregate_per_file(tmp_path):
    _focus_file(tmp_path, _cross_country_tree(4))
    v = _validator(tmp_path)
    v.validate_cross_country_event_tooltips()

    assert _messages(v) == [
        "4 focus(es) fire an event to another nation without a"
        " TT_IF_THEY_ACCEPT tooltip: TAG_focus_0 (line 4), TAG_focus_1"
        " (line 13), TAG_focus_2 (line 22) and 1 more"
    ]
    assert v._issues[0].line == 4
    assert v._issues[0].category == "missing-cross-country-tooltip"


# A nested fire is not a definition; tag-routed options give nobody a choice
# unless the tags overlap, one option is negated or one is ungated.
EVENTS = """country_event = {
\tid = offer.1
\toption = { name = offer.1.a add_political_power = 10 }
\toption = { name = offer.1.b }
}

country_event = {
\tid = notice.1
\toption = { name = notice.1.a }
}

country_event = {
\tid = flavor.1
\toption = { name = flavor.1.a }
\toption = {
\t\tname = flavor.1.b
\t\tlog = "[GetDateText]: [This.GetName]: flavor.1.b executed"
\t\tai_chance = { base = 1 }
\t}
}

country_event = {
\tid = quiet.1
\thidden = yes
\toption = { name = quiet.1.a add_political_power = 10 }
\toption = { name = quiet.1.b }
}

country_event = {
\tid = fires_others.1
\toption = {
\t\tname = fires_others.1.a
\t\tGER = { country_event = { id = nested.1 days = 1 } }
\t}
\toption = { name = fires_others.1.b }
}

country_event = {
\tid = routed.1
\toption = {
\t\tname = routed.1.a
\t\ttrigger = { original_tag = UKR }
\t\tadd_political_power = 10
\t}
\toption = {
\t\tname = routed.1.b
\t\ttrigger = { original_tag = SOV }
\t\tadd_political_power = 10
\t}
}

country_event = {
\tid = routed_shared.1
\toption = {
\t\tname = routed_shared.1.a
\t\ttrigger = { tag = UKR }
\t\tadd_political_power = 10
\t}
\toption = {
\t\tname = routed_shared.1.b
\t\ttrigger = { OR = { tag = UKR tag = SOV } }
\t}
}

country_event = {
\tid = routed_negated.1
\toption = {
\t\tname = routed_negated.1.a
\t\ttrigger = { tag = UKR }
\t\tadd_political_power = 10
\t}
\toption = {
\t\tname = routed_negated.1.b
\t\ttrigger = { NOT = { tag = UKR } }
\t}
}

country_event = {
\tid = half_routed.1
\toption = {
\t\tname = half_routed.1.a
\t\ttrigger = { tag = UKR }
\t\tadd_political_power = 10
\t}
\toption = { name = half_routed.1.b }
}
"""

# An empty, id-less or never-closing block yields nothing. An option opener in
# a quoted string aborts option parsing, so quoted.1 stays a notification.
UNPARSEABLE_EVENTS = """country_event = {}
country_event = {
\tis_triggered_only = yes
\toption = { name = noid.a }
\toption = { name = noid.b }
}
country_event = {
\tid = quoted.1
\tdesc = "option = { fake"
\toption = { name = quoted.1.a }
\toption = { name = quoted.1.b }
}
country_event = {
\tid = answerable.1
\toption = { name = answerable.1.a add_political_power = 5 }
\toption = { name = answerable.1.b add_stability = 0.05 }
}
country_event = {
\tid = unclosed.1
\toption = { name = unclosed.1.a add_political_power = 5 }
\toption = { name = unclosed.1.b add_stability = 0.05 }
"""


def test_notification_event_ids(tmp_path):
    _write(tmp_path, "events/Empty.txt", "")
    _write(tmp_path, "events/test_events.txt", EVENTS)
    _write(tmp_path, "events/Unparseable.txt", UNPARSEABLE_EVENTS)

    assert _validator(tmp_path)._notification_event_ids() == frozenset(
        {"notice.1", "quiet.1", "flavor.1", "routed.1", "quoted.1"}
    )


@pytest.mark.parametrize(
    "options",
    [
        ["trigger = { tag = UKR }", "trigger = { OR = { tag = UKR tag = SOV } }"],
        ["trigger = { tag = UKR }", "trigger = { NOT = { tag = UKR } }"],
        ["trigger = { tag = UKR }", "name = x"],
        ["trigger = { tag = UKR }"],
    ],
    ids=["overlapping tags", "negated tag", "ungated option", "single option"],
)
def test_options_that_are_not_tag_routed(options):
    assert not V._is_tag_routed(options)


def test_flavor_only_bails_on_an_unbalanced_inert_block():
    """An option that cannot be parsed counts as carrying an outcome, so the
    cross-country tooltip check stays noisy rather than silently exempting it."""
    assert (
        V._is_flavor_only(["\n\tname = foo.1.a\n\tai_chance = { base = 10\n"]) is False
    )


# --- layout and coordinates -------------------------------------------------


def _write_layout(root, text, name="tree.txt"):
    return _write(root, f"{FOCUS_DIR}/{name}", text)


def _layout_validator(root, staged=None):
    value = _validator(root)
    if staged is not None:
        value.staged_only = True
        value.staged_files = staged
    value.validate_focus_overlap()
    return value


@pytest.mark.parametrize("x, count", [(-1, 1), (-2, 0)])
def test_brazil_before_and_after_5122(tmp_path, x, count):
    _write_layout(
        tmp_path,
        "focus_tree = { id = brazil_focus\n"
        "focus = { id = BRA_nossa_economia x = -12 y = 0 }\n"
        "focus = { id = BRA_internationalize_the_real x = 0 y = 1 "
        "relative_position_id = BRA_nossa_economia }\n"
        f"focus = {{ id = BRA_growth_through_freedom x = {x} y = 1 "
        "relative_position_id = BRA_nossa_economia }\n}",
    )
    value = _layout_validator(tmp_path)
    assert value.errors_found == 0
    assert len(value._issues) == count
    assert value.layout_counts["overlap_pairs"] == count
    if count:
        issue = value._issues[0]
        assert issue.category == "focus-coordinate-overlap"
        assert issue.severity == V.Severity.WARNING
        assert "(-13, 1)" in issue.message and "(-12, 1)" in issue.message
        assert issue.file == f"{FOCUS_DIR}/tree.txt"


def test_direct_fields_and_line_numbers_ignore_effects_strings_and_comments(tmp_path):
    path = _write_layout(
        tmp_path,
        "# focus_tree = { id = ghost }\n"
        'log = "focus_tree = { id = fake focus = { id = bad } }"\n'
        'focus_tree = {\n id = "real"\n'
        " shared_focus = { SH_a SH_b }\n"
        ' focus = { id = "a" x = -2 y = +1\n'
        " completion_reward = { x = 999 y = 99 offset = {} allow_branch = {} }\n"
        " }\n focus = { x = 2 y = 1 completion_reward = { id = nested } }\n"
        "}\nshared_focus = { id = SH_a x = 0 y = 0 }\n"
        "joint_focus = { id = SH_b x = 2 y = 0 }\n",
    )
    data = V._FocusFile(path, str(tmp_path)).layout()
    assert len(data["trees"]) == 1
    tree = data["trees"][0]
    assert (tree["id"], tree["line"], tree["shared_refs"]) == (
        "real",
        3,
        ["SH_a", "SH_b"],
    )
    assert len(tree["focuses"]) == 1
    focus = tree["focuses"][0]
    assert (focus["id"], focus["line"], focus["x"], focus["y"]) == ("a", 6, -2, 1)
    assert not focus["offset"] and not focus["allow_branch"]
    assert [item["id"] for item in data["shared"]] == ["SH_a", "SH_b"]


def test_escaped_quotes_cannot_supply_coordinates(tmp_path):
    path = _write_layout(
        tmp_path,
        "focus_tree = { focus = { id = a x = 0 y = 0 "
        'desc = "text \\" x = 99 y = 99" } }',
    )
    focus = V._FocusFile(path, str(tmp_path)).layout()["trees"][0]["focuses"][0]
    assert (focus["x"], focus["y"]) == (0, 0)


def test_dynamic_markers_and_prerequisites_survive_cached_scan(tmp_path):
    path = _write_layout(
        tmp_path,
        "focus_tree = { id = dynamic "
        "focus = { id = gate x = 0 y = 0 allow_branch = { always = yes } } "
        "focus = { id = moved x = 0 y = 0 offset = { x = 3 y = 0 } "
        "prerequisite = { focus = gate ignored = other focus = {} } } }",
    )
    focuses = V._FocusFile(path, str(tmp_path)).layout()["trees"][0]["focuses"]
    assert focuses[0]["allow_branch"] is True
    assert focuses[1]["offset"] is True
    assert focuses[1]["prerequisites"] == [["gate"]]
    value = _layout_validator(tmp_path)
    assert value.layout_counts["dynamic_skipped"] == 2
    assert value.layout_counts["overlap_pairs"] == 0


def test_prerequisite_order_and_mutex_rows_are_reported_as_warnings(tmp_path):
    path = _write_layout(
        tmp_path,
        "focus_tree = { id = rows "
        "focus = { id = parent x = 0 y = 1 } "
        "focus = { id = child x = 4 y = 0 prerequisite = { focus = parent } "
        "mutually_exclusive = { focus = other } } "
        "focus = { id = other x = 8 y = 2 mutually_exclusive = { focus = child } } }",
    )
    data = V._FocusFile(path, str(tmp_path)).layout()
    child = next(
        focus for focus in data["trees"][0]["focuses"] if focus["id"] == "child"
    )
    assert child["prerequisites"] == [["parent"]]
    assert child["mutually_exclusive"] == ["other"]

    value = _layout_validator(tmp_path)
    categories = {issue.category for issue in value._issues}
    assert categories == {
        "focus-prerequisite-row-order",
        "focus-mutually-exclusive-row",
    }
    assert all(issue.severity == V.Severity.WARNING for issue in value._issues)
    assert value.layout_counts["prerequisite_order_pairs"] == 1
    assert value.layout_counts["mutually_exclusive_row_pairs"] == 1


def test_nested_allow_branch_terms_feed_the_branch_leak_check(tmp_path):
    gate = "if = { limit = { has_game_rule = { option = HIDE } } NOT = { has_completed_focus = rival } }"
    path = _write_layout(
        tmp_path,
        "focus_tree = { id = leak "
        f"focus = {{ id = gate x = 0 y = 0 allow_branch = {{ {gate} }} }} "
        "focus = { id = middle x = 0 y = 1 prerequisite = { focus = gate } } "
        "focus = { id = child x = 0 y = 2 allow_branch = { has_game_rule = { option = no } } "
        "prerequisite = { focus = middle } } }",
    )
    focuses = V._FocusFile(path, str(tmp_path)).layout()["trees"][0]["focuses"]
    assert focuses[0]["branch_terms"] == ["has_completed_focus=rival", "option=HIDE"]
    assert focuses[1]["branch_terms"] == []
    assert _layout_validator(tmp_path).layout_counts["branch_leaks"] == 1


def test_hide_rule_terms_are_tagged_and_the_rule_check_dropped(tmp_path):
    rule = "has_game_rule = { rule = obsolete_focus_branches_visibility option = HIDE }"
    path = _write_layout(
        tmp_path,
        "focus_tree = { id = rule focus = { id = gate x = 0 y = 0 allow_branch = { "
        "date < 2006.7.1 "
        f"if = {{ limit = {{ {rule} }} NOT = {{ has_completed_focus = rival }} }} }} }} }}",
    )
    focus = V._FocusFile(path, str(tmp_path)).layout()["trees"][0]["focuses"][0]
    assert focus["branch_terms"] == [
        "date=2006.7.1",
        "hide_rule:has_completed_focus=rival",
    ]


@pytest.mark.parametrize(
    "coordinates", ["y = 0", "x = invalid y = 0", "x = @column y = 0", "x = {} y = 0"]
)
def test_missing_or_nonnumeric_coordinates_are_unknown(tmp_path, coordinates):
    _write_layout(tmp_path, f"focus_tree = {{ focus = {{ id = a {coordinates} }} }}")
    value = _layout_validator(tmp_path)
    assert value.layout_counts["unresolved"] == 1
    assert value._issues[0].category == "focus-coordinate-unresolved"


def _shared_tree(root):
    host = _write_layout(
        root,
        "focus_tree = { id = tree shared_focus = SH_root\n"
        "focus = { id = anchor x = 4 y = 0 }\n"
        "focus = { id = local x = 4 y = 1 } }",
    )
    shared = _write_layout(
        root,
        "shared_focus = { id = SH_root x = 0 y = 1 relative_position_id = anchor }\n"
        "shared_focus = { id = SH_child x = 2 y = 1 relative_position_id = SH_root "
        "prerequisite = { focus = SH_root } }",
        "shared.txt",
    )
    return host, shared


def test_shared_staged_change_checks_unstaged_importer(tmp_path):
    host, shared = _shared_tree(tmp_path)
    value = _layout_validator(tmp_path, [shared])
    assert value.layout_counts["selected_trees"] == 1
    assert value.layout_counts["instances"] == 4
    assert value.layout_counts["overlap_pairs"] == 1
    assert host not in value.staged_files
    assert "SH_root" in value._issues[0].message


@pytest.mark.parametrize("delete_file", [False, True])
def test_removed_shared_definition_rechecks_consumer(tmp_path, delete_file):
    _, shared = _shared_tree(tmp_path)
    if delete_file:
        os.unlink(shared)
    else:
        _write_layout(tmp_path, "# shared definition removed\n", "shared.txt")
    value = _layout_validator(tmp_path, [shared])
    assert value.layout_counts["selected_trees"] == 1
    assert any(
        "imported shared focus 'SH_root'" in issue.message for issue in value._issues
    )


def test_deleted_paths_preserved_from_shared_staged_selection(tmp_path, monkeypatch):
    _, shared = _shared_tree(tmp_path)
    os.unlink(shared)
    monkeypatch.setenv("MD_STAGED_FILES", f"{FOCUS_DIR}/shared.txt")
    value = V.Validator(str(tmp_path), staged_only=True, workers=1, use_colors=False)
    value.validate_focus_overlap()
    assert shared in value.staged_files
    assert value.layout_counts["selected_trees"] == 1


def test_staged_without_focus_changes_does_not_read_files(tmp_path, monkeypatch):
    _shared_tree(tmp_path)

    def unexpected(*_args):
        raise AssertionError("unexpected file read")

    monkeypatch.setattr(V, "_read_mod_text", unexpected)
    value = _layout_validator(tmp_path, [])
    assert value.layout_counts["selected_trees"] == 0
    assert value._issues == []


def test_layout_cache_reuses_parse_then_invalidates_shared_coordinates(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _, shared = _shared_tree(tmp_path)
    assert _layout_validator(tmp_path).layout_counts["overlap_pairs"] == 1
    original = V._scan_focus_layout
    scanned = []

    def counted(source):
        scanned.append(source.filepath)
        return original(source)

    monkeypatch.setattr(V, "_scan_focus_layout", counted)
    assert _layout_validator(tmp_path).layout_counts["overlap_pairs"] == 1
    assert scanned == []
    _write_layout(tmp_path, "shared_focus = { id = SH_root x = 7 y = 1 }", "shared.txt")
    assert _layout_validator(tmp_path, [shared]).layout_counts["overlap_pairs"] == 0
    assert scanned == [shared]


def test_parser_keeps_trees_separate_and_skips_unclosed_tree(tmp_path):
    path = _write_layout(
        tmp_path,
        "focus_tree = { id = a focus = { id = same x = 0 y = 0 } }\n"
        "focus_tree = { id = b focus = { id = same x = 0 y = 0 } }\n"
        "focus_tree = {",
    )
    source = V._FocusFile(path, str(tmp_path))
    assert [tree["id"] for tree in source.layout()["trees"]] == ["a", "b"]
    assert _layout_validator(tmp_path).layout_counts["overlap_pairs"] == 0
