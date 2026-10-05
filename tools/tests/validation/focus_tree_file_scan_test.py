"""Each focus file is read, comment-stripped and brace-paired once, then every
per-file check runs from that one source.

These pin the exact findings that path produces (file, line, message), the
brace pairs against find_matching_brace, the iterators validate_variables
imports, the pooled run, the disk cache, and what a staged run reads.
"""

import random
import re

import pytest
import validate_focus_tree as V
from shared.suite import write_under_str as _write
from shared_utils import extract_block_from_text

FOCUS_DIR = "common/national_focus"

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


# ---------------------------------------------------------------------------
# Findings through the shared source
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Money effects called only inside a preview
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Brace pairs
# ---------------------------------------------------------------------------

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


def test_a_focus_brace_in_a_string_that_closes_past_its_tree_is_skipped(tmp_path):
    """Parsed inside the tree body, the quoted `focus = {` never closes there,
    so only the real focus after it is registered."""
    path = _write(
        tmp_path,
        SCAN_PATH,
        "focus_tree = {\n"
        "\tid = tree_a\n"
        '\tlog = "focus = { id = TAG_in_string"\n'
        "\tfocus = { id = TAG_real }\n"
        "}\n"
        'x = { " }\n',
    )

    assert V._FocusFile(path, str(tmp_path)).parse()["trees"] == [
        {"focuses": [("TAG_real", 4, [])], "shared_refs": set()}
    ]


# ---------------------------------------------------------------------------
# Helpers validate_variables imports
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Literal-led patterns
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Search filters at the top level
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Pool and disk cache
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Staged runs
# ---------------------------------------------------------------------------

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
    validator = V.Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, missing_icons=True
    )
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
