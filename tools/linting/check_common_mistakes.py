#!/usr/bin/env python3
"""
Check for common scripting mistakes in HOI4 mod files.

Detects mechanically-checkable rule violations from CLAUDE.md:
  - threat/has_war_support/has_stability comparisons >= 1 (all are 0.0-1.0 ranges)
  - allowed = { always = no } in country/hidden_ideas idea categories (redundant default; checked once at load, bypassed by add_ideas)
  - allowed = { tag = TAG } in country/hidden_ideas (breaks civil war split-offs; use original_tag)
  - allowed_civil_war = { always = no } in ideas (no effect, remove it)
  - cancel = { always = no } in ideas (checked hourly, never true; redundant default)
  - ai_will_do root-level factor = N (should be base = N; factor only valid in modifier children)
  - Division instead of multiplication (/ 100 -> * 0.01)
  - Multiple values of a single-valued trigger (has_government, tag, original_tag,
    has_country_leader_ideology) at the same AND/NOT depth — always false (AND) or
    always true (NOT); caller meant OR = { ... } or separate NOT blocks.
  - Multiple has_idea checks from the same mutex group (e.g. intervention doctrines)
    at the same AND/NOT depth — same logic as above; only one slot can be filled at a
    time so the block is always false (AND) or always true (NOT).
  - Consecutive same-tag scope blocks that should be merged
  - send_embargo/break_embargo without has_dlc = "By Blood Alone" guard
  - divide_variable by a variable without a zero guard
  - Duplicate consecutive add_to_variable / add_to_temp_variable lines
  - every_country with has_idea = X_member when a pre-built array exists
  - is_in_faction = TAG (boolean trigger misused with a tag; should be is_in_faction_with)
  - has_trade_agreement_with (not a valid trigger; MD uses has_country_flag = trade_agreement@TAG)
  - Dynamic triggers inside decision allowed blocks (allowed is evaluated once at game start)
  - is_X_nation triggers in runtime contexts (available, effect, limit) — use has_country_flag = X_flag instead
  - check_variable with inline >= or <= (silently mis-parsed; use compare = ... or a strict inequality)
  - Tautological OR = { X = yes X = no } (always true; remove the OR)
  - percent_change set without a reachable change_influence_percentage = yes (silent no-op / loop-scope bug)
"""

import os
import re
import sys

_RE_THREAT = re.compile(r"(?<!\w)threat\s*([><]=?)\s*(\d+\.?\d*)")
_RE_WAR_SUPPORT = re.compile(r"(?<!\w)has_war_support\s*([><]=?)\s*(\d+\.?\d*)")
_RE_STABILITY = re.compile(r"(?<!\w)has_stability\s*([><]=?)\s*(\d+\.?\d*)")
_RE_ALLOWED_ALWAYS_NO = re.compile(r"allowed\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_ALLOWED_OPEN = re.compile(r"allowed\s*=\s*\{")
_RE_ALLOWED_OPEN_WB = re.compile(r"\ballowed\s*=\s*\{")
_RE_ALLOWED_TAG = re.compile(r"allowed\s*=\s*\{\s*tag\s*=\s*\w+\s*\}")
_RE_ALLOWED_CIVIL_WAR = re.compile(r"allowed_civil_war\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_CANCEL = re.compile(r"cancel\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_AI_WILL_DO = re.compile(r"ai_will_do\s*=\s*\{[^{]*?\bfactor\b\s*=")
_RE_DIVISION = re.compile(r"/\s*(100|1000|10|50|200|500)\b")
# check_variable only accepts =, >, < inline; >= and <= are silently mis-parsed
# (no error.log entry) and the check never matches. Long form needs compare = ...
_RE_CHECK_VAR_GE_LE = re.compile(r"check_variable\s*=\s*\{[^}]*?(>=|<=)")
# Tautological OR covering both polarities of one trigger (X = yes / X = no) is
# always true. Captures both tokens + values; caller checks token match in code.
_RE_TAUTOLOGICAL_OR = re.compile(
    r"\bOR\s*=\s*\{\s*(\w+)\s*=\s*(yes|no)\s+(\w+)\s*=\s*(yes|no)\s*\}"
)
# percent_change is the shared temp-var argument for the whole influence-percentage
# effect family (change_influence_percentage, change_domestic_influence_percentage,
# change_current_influencer_index_percentage). Any of them counts as a consumer.
_RE_PERCENT_CHANGE_SETTER = re.compile(r"\bpercent_change\b")
_RE_CHANGE_INFLUENCE_CALL = re.compile(
    r"\bchange_[a-z_]*influence[a-z_]*percentage\s*=\s*yes\b"
)
# Country-iteration loops re-scope each pass, so loop-local temp vars are only
# valid if the invocation lives inside the same loop block.
_RE_INFLUENCE_LOOP_OPEN = re.compile(
    r"^\s*(?:every|random)_[a-z_]*country[a-z_]*\s*=\s*\{"
)
_RE_IDEAS_BLOCK = re.compile(r"^ideas\s*=\s*\{")
_RE_CATEGORY = re.compile(r"^(\w+)\s*=\s*\{")
_RE_AVAILABLE_ALWAYS_NO = re.compile(r"\bavailable\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_VISIBLE_ALWAYS_NO = re.compile(r"\bvisible\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_BYPASS_OPEN = re.compile(r"\bbypass\s*=\s*\{")
_RE_BYPASS_TRIVIAL = re.compile(r"\bbypass\s*=\s*\{\s*always\s*=\s*(?:yes|no)\s*\}")
_RE_DECISION_MARKER = re.compile(
    r"\bcomplete_effect\s*=\s*\{|\bfire_only_once\s*=|\bactivation\s*=\s*\{|\bdays_mission_timeout\s*="
)
_RE_FOCUS_ID_IN_BLOCK = re.compile(r"\bid\s*=\s*(\w+)")
_RE_COMPLETE_FOCUS = re.compile(r"\bcomplete_national_focus\s*=\s*(\w+)")
_RE_ACTIVATE_DECISION = re.compile(r"\bactivate_decision\s*=\s*(\w+)")
_RE_OR_BLOCK_OPEN = re.compile(r"^\s*OR\s*=\s*\{")
_RE_NOT_BLOCK_OPEN = re.compile(r"^\s*NOT\s*=\s*\{")
_RE_TRIGGER_ASSIGN = re.compile(r"^(\w+)\s*=\s*([\w.]+)$")
_RE_FOCUS_BLOCK_OPEN = re.compile(r"^\s*focus\s*=\s*\{")
_RE_WHITESPACE_COLLAPSE = re.compile(r"\s+")
_RE_AVAILABLE_OPEN = re.compile(r"\bavailable\s*=\s*\{")
_RE_TOPLEVEL_WORD = re.compile(r"^\w")
_RE_INDENTED_WORD = re.compile(r"^\s+\w")
_RE_BLOCK_ID = re.compile(r"\s*(\w+)\s*=\s*\{")
_RE_LOGIC_SCOPE = re.compile(r"^\s*(NOT|OR|AND)\s*=\s*\{")
_RE_CLOSE_BRACE_LINE = re.compile(r"^(\s*)\}\s*$")
_RE_LEADING_INDENT = re.compile(r"^(\s*)")
_RE_IF_OPEN = re.compile(r"\bif\s*=\s*\{")
_RE_ELSE_OPEN = re.compile(r"\belse\s*=\s*\{")
_RE_CLAMP_GUARD = re.compile(
    r"clamp(?:_temp)?_variable\s*=\s*\{[^}]*var\s*=\s*(\S+)[^}]*min\s*=\s*([\d.]+)"
)
_RE_CHECK_VAR_GT = re.compile(r"check_variable\s*=\s*\{\s*(\S+)\s*>\s*[\d.]+\s*\}")
_RE_CHECK_VAR_LE = re.compile(r"check_variable\s*=\s*\{\s*(\S+)\s*[<=]\s*[\d.]+\s*\}")
_RE_SET_VAR_NONZERO = re.compile(r"set_variable\s*=\s*\{\s*(\S+)\s*=\s*(-?[\d.]+)\s*\}")
_RE_LIMIT_OPEN = re.compile(r"\blimit\s*=\s*\{")
_RE_IF_ELSE_OPEN = re.compile(r"\b(if|else_if|else)\s*=\s*\{")
_RE_HAS_IDEA = re.compile(r"has_idea\s*=\s*(\w+)")
_RE_OR_CONTENT = re.compile(r"OR\s*=\s*\{([^}]*)\}")
_RE_LOG_ONLY_EFFECT = re.compile(r"log\s*=\s*\"[^\"]+\"\s*$")
_RE_OPTION_BLOCK_OPEN = re.compile(r"\boption\s*=\s*\{")
_RE_COMPLETE_EFFECT_OPEN = re.compile(r"\bcomplete_effect\s*=\s*\{")
_RE_REMOVE_EFFECT_OPEN = re.compile(r"\bremove_effect\s*=\s*\{")
_RE_IS_IN_FACTION_TAG = re.compile(r"\bis_in_faction\s*=\s*(?!yes\b|no\b)(\w+)")
_RE_TRADE_AGREEMENT_WITH = re.compile(r"\bhas_trade_agreement_with\s*=")
_RE_DECISION_ALLOWED_DYNAMIC = re.compile(
    r"\b(?:num_of_factories|has_opinion|strength_ratio|"
    r"has_army_size|has_navy_size|has_political_power|date)\b"
)
_RE_IS_X_NATION = re.compile(r"\bis_([a-z]+_)?nation\s*=\s*yes\b")
_RE_SET_NATION_FLAG = re.compile(
    r"set_country_flag\s*=\s*(?:\{\s*flag\s*=\s*)?(\w+_nation_flag)\b"
)

# Single-valued country triggers. A country has exactly one government/tag/etc,
# so two checks at the same AND depth can never both be true — caller almost
# always meant to wrap them in OR. Inside NOT, the block is always true and
# pointless — caller meant separate NOT blocks or NOT = { OR = { ... } }.
_MUTUALLY_EXCLUSIVE_TRIGGERS = {
    "has_government",
    "tag",
    "original_tag",
    "has_country_leader_ideology",
}

# Idea slots where only one idea from the group can be active at a time. Two
# `has_idea = X` checks for ideas in the same group inside a single AND block
# are always false; inside a NOT block they are always true. The classic bug
# from CLAUDE.md is `NOT = { has_idea = intervention_isolation
# has_idea = intervention_local_security }` — silently true forever because no
# country has both intervention doctrines at once.
# Keep in sync with the mutually-exclusive idea slots defined in common/ideas/.
# Hand-maintained: add a group here when a new exclusive-idea slot is introduced
# (grep common/ideas/ for the slot's idea names), or the AND/NOT-trap check
# silently won't cover it.
_MUTEX_IDEA_GROUPS = {
    "intervention_doctrine": {
        "intervention_isolation",
        "intervention_local_security",
        "intervention_limited_interventionism",
        "intervention_regional_interventionism",
        "intervention_global_interventionism",
    },
}
# Reverse index: idea -> group_name (for O(1) lookup)
_IDEA_TO_MUTEX_GROUP = {
    idea: group_name
    for group_name, ideas in _MUTEX_IDEA_GROUPS.items()
    for idea in ideas
}
# Token scanner for the mutex check: finds braces and has_idea tokens in order so
# single-line patterns like `NOT = { has_idea = X has_idea = Y }` are caught.
_RE_MUTEX_TOKEN = re.compile(r"\{|\}|has_idea\s*=\s*(\w+)")
_RE_NOT_EQ = re.compile(r"\bNOT\s*=\s*$")
_RE_OR_EQ = re.compile(r"\bOR\s*=\s*$")

# Populated by main() before spawning Pool workers; propagated via initializer.
_SCRIPT_COMPLETED_FOCUSES: set = set()
_SCRIPT_COMPLETED_DECISIONS: set = set()
# Nation-group flags actually set somewhere (set_country_flag = X_nation_flag).
# The is_X_nation check only suggests a flag that really exists.
_REAL_NATION_FLAGS: set = set()


def _init_worker(focuses, decisions, nation_flags):
    global _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS, _REAL_NATION_FLAGS
    _SCRIPT_COMPLETED_FOCUSES = focuses
    _SCRIPT_COMPLETED_DECISIONS = decisions
    _REAL_NATION_FLAGS = nation_flags


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cleanup_or import find_redundant_and_blocks, find_single_condition_or_blocks
from shared_utils import (
    Timer,
    clean_filepath,
    collect_files_by_mode,
    create_linting_parser,
    get_non_selectable_idea_categories,
    get_root_dir,
    print_timing_summary,
    run_with_pool,
    strip_inline_comment,
)


def _scan_global_refs(root_dir):
    """Return (focus_ids, decision_ids, nation_flags) gathered across the codebase.

    Scans all .txt files for:
      - complete_national_focus = ID / activate_decision = ID, so the checkers can
        skip flagging intentionally script-completed items.
      - set_country_flag = X_nation_flag, so the is_X_nation check only suggests a
        flag that the codebase actually sets (e.g. cartel has no nation flag).
    """
    focuses: set = set()
    decisions: set = set()
    nation_flags: set = set()
    for directory in ["common", "events", "history"]:
        dir_path = os.path.join(root_dir, directory)
        if not os.path.exists(dir_path):
            continue
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                if not filename.endswith(".txt"):
                    continue
                fp = os.path.join(root, filename)
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    for m in _RE_COMPLETE_FOCUS.finditer(content):
                        focuses.add(m.group(1))
                    for m in _RE_ACTIVATE_DECISION.finditer(content):
                        decisions.add(m.group(1))
                    for m in _RE_SET_NATION_FLAG.finditer(content):
                        nation_flags.add(m.group(1))
                except Exception:
                    pass
    return focuses, decisions, nation_flags


def _get_block(lines, start):
    """Collect the complete brace-delimited block starting at lines[start].
    Returns (block_lines, next_idx) where next_idx is the first index after the block.
    Works on any list — passing a sub-list is safe.
    """
    code = strip_inline_comment(lines[start])
    depth = code.count("{") - code.count("}")
    j = start + 1
    while depth > 0 and j < len(lines):
        code = strip_inline_comment(lines[j])
        depth += code.count("{") - code.count("}")
        j += 1
    return lines[start:j], j


def _check_focus_available_always_no(lines):
    """Flag available = { always = no } with no completion mechanism.

    Valid completion mechanisms (all skip the flag):
      - bypass block present (focus auto-bypasses when conditions fire)
      - complete_national_focus = FOCUS_ID found elsewhere in the codebase

    Only flags when available=always-no AND neither mechanism is present,
    meaning the focus is permanently unreachable.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        if _RE_FOCUS_BLOCK_OPEN.match(lines[i]):
            start = i
            block, i = _get_block(lines, start)
            norm = _RE_WHITESPACE_COLLAPSE.sub(" ", "".join(block))
            if _RE_AVAILABLE_ALWAYS_NO.search(norm):
                id_match = _RE_FOCUS_ID_IN_BLOCK.search(norm)
                focus_id = id_match.group(1) if id_match else None
                has_bypass = bool(_RE_BYPASS_OPEN.search(norm))
                script_completed = focus_id and focus_id in _SCRIPT_COMPLETED_FOCUSES
                if not has_bypass and not script_completed:
                    for k, bl in enumerate(block):
                        if _RE_AVAILABLE_OPEN.search(bl):
                            issues.append(
                                (
                                    start + k + 1,
                                    "available = { always = no } with no bypass or complete_national_focus"
                                    " -- focus is permanently unreachable;"
                                    " add a bypass block or trigger it via complete_national_focus",
                                )
                            )
                            break
        else:
            i += 1
    return issues


def _check_mutually_exclusive_contradictions(lines):
    """Flag blocks with multiple values of a single-valued trigger at the same AND depth.

    Example bug:
        SOV = {
            has_government = communism
            has_government = nationalist
        }
    A country has exactly one government, so this evaluates to false forever.
    Caller meant OR = { has_government = communism has_government = nationalist }.

    Inside NOT the inverse bug appears:
        NOT = {
            tag = USA
            tag = CHI
        }
    which is NOT(A AND B) — always true since a country is only one tag at a
    time. Caller meant separate NOT blocks or NOT = { OR = { ... } }.
    """
    issues = []
    # Stack entries: (is_or, is_not, {trigger: [(line_num, value), ...]})
    stack = [(False, False, {})]

    for i, line in enumerate(lines):
        code = strip_inline_comment(line)
        stripped = code.strip()
        if not stripped:
            continue

        if "{" not in code and "}" not in code:
            m = _RE_TRIGGER_ASSIGN.match(stripped)
            if m and m.group(1) in _MUTUALLY_EXCLUSIVE_TRIGGERS:
                stack[-1][2].setdefault(m.group(1), []).append((i + 1, m.group(2)))

        is_or = bool(_RE_OR_BLOCK_OPEN.match(line))
        is_not = bool(_RE_NOT_BLOCK_OPEN.match(line))

        opens = code.count("{")
        closes = code.count("}")

        for k in range(opens):
            # Only the first open on a line carries the OR/NOT keyword
            if k == 0:
                stack.append((is_or, is_not, {}))
            else:
                stack.append((False, False, {}))

        for _ in range(closes):
            if len(stack) > 1:
                popped_or, popped_not, popped_triggers = stack.pop()
                if popped_or:
                    continue
                for trigger, entries in popped_triggers.items():
                    values = {v for _, v in entries}
                    if len(values) < 2:
                        continue
                    first_line = entries[0][0]
                    vals_str = ", ".join(sorted(values))
                    if popped_not:
                        msg = (
                            f"NOT = {{ }} contains multiple '{trigger}' values"
                            f" ({vals_str}) -- always true since a country has"
                            f" only one {trigger}; use separate NOT blocks or"
                            f" NOT = {{ OR = {{ ... }} }}"
                        )
                    else:
                        msg = (
                            f"multiple '{trigger}' values in same AND block"
                            f" ({vals_str}) -- always false since a country has"
                            f" only one {trigger}; wrap in OR = {{ }} to match any"
                        )
                    issues.append((first_line, msg))

    return issues


def _check_has_idea_mutex_in_not_block(lines):
    """Flag NOT/AND blocks containing 2+ has_idea checks from the same mutex group.

    Example bug (from raid_target_eligible before fix):
        NOT = {
            has_idea = intervention_local_security
            has_idea = intervention_isolation
        }
    Both ideas are in the intervention-doctrine mutex group. A country can hold
    at most one at a time, so the AND inside NOT is always false, and the NOT
    is always true — the gate it was supposed to enforce is silently bypassed.
    Caller almost always meant `NOT = { OR = { ... } }` or separate NOT blocks.

    Inside a non-NOT AND block, two same-group has_idea checks are always false
    (a country can't be in both slots), so the entire surrounding modifier or
    trigger never fires — usually also a bug.
    """
    issues = []
    # Stack entries: (is_or, is_not, {group_name: [(line_num, idea_name), ...]})
    stack = [(False, False, {})]

    for i, line in enumerate(lines):
        code = strip_inline_comment(line)
        if not code.strip():
            continue

        last_end = 0
        for m in _RE_MUTEX_TOKEN.finditer(code):
            tok = m.group(0)
            if tok == "{":
                preceding = code[last_end : m.start()]
                is_not = bool(_RE_NOT_EQ.search(preceding))
                is_or = bool(_RE_OR_EQ.search(preceding))
                stack.append((is_or, is_not, {}))
            elif tok == "}":
                if len(stack) > 1:
                    popped_or, popped_not, popped_groups = stack.pop()
                    # OR is the intended way to express "any of these mutex ideas"
                    if popped_or:
                        last_end = m.end()
                        continue
                    for group_name, entries in popped_groups.items():
                        ideas_set = {idea for _, idea in entries}
                        if len(ideas_set) < 2:
                            continue
                        first_line = entries[0][0]
                        ideas_str = ", ".join(sorted(ideas_set))
                        if popped_not:
                            msg = (
                                f"NOT = {{ }} contains multiple {group_name} ideas "
                                f"({ideas_str}) -- always true since they're mutually "
                                f"exclusive; use NOT = {{ OR = {{ ... }} }} or "
                                f"separate NOT blocks per idea"
                            )
                        else:
                            msg = (
                                f"AND block contains multiple {group_name} ideas "
                                f"({ideas_str}) -- always false since they're mutually "
                                f"exclusive; wrap in OR = {{ }} to match any"
                            )
                        issues.append((first_line, msg))
            else:
                idea = m.group(1)
                group = _IDEA_TO_MUTEX_GROUP.get(idea)
                if group is not None:
                    stack[-1][2].setdefault(group, []).append((i + 1, idea))
            last_end = m.end()

    return issues


_RE_DAYS_MISSION_TIMEOUT = re.compile(r"\bdays_mission_timeout\s*=")

_RE_COUNTRY_SCOPE_OPEN = re.compile(
    r"^(\s*)([A-Z]{3}|FROM|ROOT|PREV|OWNER|CAPITAL)\s*=\s*\{"
)
_LOGIC_KEYWORDS = {"NOT", "OR", "AND", "IF", "GFX", "GUI", "ROW"}
_RE_EMBARGO = re.compile(r"\b(send_embargo|break_embargo)\s*=")
_RE_DLC_BBA = re.compile(r'has_dlc\s*=\s*"By Blood Alone"')
_RE_ADD_TO_VAR = re.compile(
    r"^\s*(add_to_variable|add_to_temp_variable)\s*=\s*\{.*\}\s*$"
)
_RE_DIVIDE_VAR = re.compile(r"\bdivide_variable\s*=\s*\{\s*(\S+)\s*=\s*(\S+)\s*\}")
_RE_EVERY_COUNTRY_OPEN = re.compile(r"^\s*every_country\s*=\s*\{")
# Maps each bloc-membership idea to the global array that should track it.
# MD-specific; hand-maintained. When a new bloc with a membership idea + backing
# array is added (see common/ideas/ and the bloc's scripted_effects), add it here
# or the idea/array consistency check won't cover it.
_MEMBER_IDEA_TO_ARRAY = {
    "EU_member": "global.EU_member",
    "NATO_member": "global.nato_members",
    "CSTO_member": "global.CSTO_member",
    "AU_member": "global.AU_member",
}
_MEMBER_IDEA_PATTERNS = {
    idea: (
        re.compile(r"has_idea\s*=\s*" + re.escape(idea)),
        re.compile(r"NOT\s*=\s*\{[^}]*has_idea\s*=\s*" + re.escape(idea)),
        re.compile(
            r"(OVERLORD|FACTION_LEADER)\s*=\s*\{[^}]*has_idea\s*=\s*" + re.escape(idea)
        ),
    )
    for idea in _MEMBER_IDEA_TO_ARRAY
}


def _check_decision_available_always_no(lines):
    """Flag available = { always = no } in decisions with no valid completion mechanism.

    Valid mechanisms (all skip the flag):
      - visible = { always = no } (decision is script-triggered, invisible to player)
      - days_mission_timeout (timer missions auto-complete via timeout_effect)
      - activate_decision = DECISION_ID found elsewhere in the codebase

    Only flags when available=always-no AND none of the above are present.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        code = strip_inline_comment(lines[i])
        # Category block: starts at column 0 with a word and {
        if (
            _RE_TOPLEVEL_WORD.match(lines[i])
            and "{" in code
            and not lines[i].lstrip().startswith("#")
        ):
            cat_start = i
            cat_block, i = _get_block(lines, cat_start)
            k = 1  # skip category header line
            while k < len(cat_block) - 1:  # skip closing } line
                bl = cat_block[k]
                bl_code = strip_inline_comment(bl)
                if _RE_INDENTED_WORD.match(bl) and "{" in bl_code:
                    dec_block, next_k = _get_block(cat_block, k)
                    norm = _RE_WHITESPACE_COLLAPSE.sub(" ", "".join(dec_block))
                    dec_id_match = _RE_BLOCK_ID.match(cat_block[k])
                    dec_id = dec_id_match.group(1) if dec_id_match else None
                    if (
                        _RE_DECISION_MARKER.search(norm)
                        and _RE_AVAILABLE_ALWAYS_NO.search(norm)
                        and not _RE_VISIBLE_ALWAYS_NO.search(norm)
                        and not _RE_DAYS_MISSION_TIMEOUT.search(norm)
                        and (
                            dec_id is None or dec_id not in _SCRIPT_COMPLETED_DECISIONS
                        )
                    ):
                        for p, dbl in enumerate(dec_block):
                            if _RE_AVAILABLE_OPEN.search(dbl):
                                issues.append(
                                    (
                                        cat_start + k + p + 1,
                                        "available = { always = no } without visible = { always = no }"
                                        " -- add visible = { always = no } for script-triggered decisions,"
                                        " or set a real available condition",
                                    )
                                )
                                break
                    k = next_k
                else:
                    k += 1
        else:
            i += 1
    return issues


def _check_decision_allowed_dynamic(lines):
    """Flag dynamic triggers inside decision allowed blocks.

    Decision `allowed` is evaluated once at game start and locked. Dynamic
    game-state conditions (factory counts, opinion, government, flags, variables)
    belong in `available` or `visible` instead.

    Only checks files in common/decisions/.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        code = strip_inline_comment(lines[i])
        if (
            _RE_TOPLEVEL_WORD.match(lines[i])
            and "{" in code
            and not lines[i].lstrip().startswith("#")
        ):
            cat_start = i
            cat_block, i = _get_block(lines, cat_start)
            k = 1
            while k < len(cat_block) - 1:
                bl = cat_block[k]
                bl_code = strip_inline_comment(bl)
                if _RE_INDENTED_WORD.match(bl) and "{" in bl_code:
                    dec_block, next_k = _get_block(cat_block, k)
                    norm = _RE_WHITESPACE_COLLAPSE.sub(" ", "".join(dec_block))
                    if not _RE_DECISION_MARKER.search(norm):
                        k = next_k
                        continue
                    in_allowed = False
                    allowed_depth = 0
                    for p, dbl in enumerate(dec_block):
                        dbl_code = strip_inline_comment(dbl)
                        if (
                            not in_allowed
                            and _RE_ALLOWED_OPEN_WB.search(dbl_code)
                            and "allowed_civil_war" not in dbl_code
                        ):
                            in_allowed = True
                            allowed_depth = dbl_code.count("{") - dbl_code.count("}")
                        elif in_allowed:
                            allowed_depth += dbl_code.count("{") - dbl_code.count("}")
                            if _RE_DECISION_ALLOWED_DYNAMIC.search(dbl_code):
                                trigger = _RE_DECISION_ALLOWED_DYNAMIC.search(
                                    dbl_code
                                ).group()
                                if trigger == "original_tag" or trigger == "tag":
                                    pass
                                else:
                                    issues.append(
                                        (
                                            cat_start + k + p + 1,
                                            f"dynamic trigger '{trigger}' in decision allowed block -- allowed is evaluated once at game start; move to available",
                                        )
                                    )
                            if allowed_depth <= 0:
                                in_allowed = False
                    k = next_k
                else:
                    k += 1
        else:
            i += 1
    return issues


def _check_consecutive_scope_blocks(lines):
    """Flag consecutive scope blocks targeting the same country tag.

    Two adjacent TAG = { } blocks (separated only by blank lines) can be merged
    into one, reducing tooltip nesting for the player.

    Suppresses when:
      - Blocks are inside OR, NOT, or AND parents (merging changes logic)
      - Blocks are in different parent scopes (depth dipped between them)
    """
    issues = []
    # Use a full brace stack to track all scope opens/closes.
    # Each entry: (tag_or_None, depth_at_open, lineno)
    stack = []
    depth = 0
    # Track the last closed country-tag block
    prev_tag = None
    prev_indent = None
    prev_open = None
    prev_close = None
    prev_close_depth = None
    # Track minimum depth seen since last tag-block close
    min_depth_since_close = 999999
    # Track OR/NOT/AND depths
    logic_depths = set()

    for i, line in enumerate(lines):
        lineno = i + 1
        code = strip_inline_comment(line)
        stripped = code.strip()

        # Detect logic keyword scopes
        if _RE_LOGIC_SCOPE.match(code):
            logic_depths.add(depth + 1)

        m_tag_open = _RE_COUNTRY_SCOPE_OPEN.match(line)

        opens = code.count("{")
        closes = code.count("}")

        # Push opens
        for k in range(opens):
            tag = None
            if k == 0 and m_tag_open and m_tag_open.group(2) not in _LOGIC_KEYWORDS:
                tag = m_tag_open.group(2)
            stack.append((tag, depth + k + 1, lineno))

        # Check for consecutive tag blocks BEFORE popping closes
        if m_tag_open and m_tag_open.group(2) not in _LOGIC_KEYWORDS:
            tag = m_tag_open.group(2)
            indent = m_tag_open.group(1)
            inside_logic = any(d <= depth for d in logic_depths)
            # Same parent = depth never dipped below where both blocks live
            same_parent = (
                prev_close_depth is not None and min_depth_since_close >= depth
            )
            if (
                not inside_logic
                and same_parent
                and prev_tag == tag
                and prev_indent == indent
                and prev_close is not None
                and (lineno - prev_close) <= 4
            ):
                between = lines[prev_close:i]
                if all(l.strip() == "" for l in between):
                    issues.append(
                        (
                            lineno,
                            f"consecutive {tag} = {{ }} blocks (first at line"
                            f" {prev_open}) -- merge into a single scope block"
                            f" to reduce tooltip nesting",
                        )
                    )

        # Pop closes and track tag-block closings
        for k in range(closes):
            if stack:
                closed_tag, closed_depth, closed_open_line = stack.pop()
                if closed_tag:
                    prev_tag = closed_tag
                    prev_indent = _RE_LEADING_INDENT.match(
                        lines[closed_open_line - 1]
                    ).group(1)
                    prev_open = closed_open_line
                    prev_close = lineno
                    prev_close_depth = depth + opens - (k + 1)
                    min_depth_since_close = prev_close_depth

        new_depth = depth + opens - closes

        # Track min depth for same-parent detection
        if prev_close is not None:
            min_depth_since_close = min(min_depth_since_close, new_depth)

        # Clean up logic depths
        for d in list(logic_depths):
            if d > new_depth:
                logic_depths.discard(d)

        # Non-blank, non-scope lines reset prev_tag at the same indent
        if stripped and not m_tag_open and not _RE_CLOSE_BRACE_LINE.match(line):
            line_indent = _RE_LEADING_INDENT.match(line).group(1)
            if line_indent == prev_indent:
                prev_tag = None

        depth = new_depth

    return issues


def _check_embargo_dlc_guard(lines):
    """Flag send_embargo/break_embargo without a has_dlc = "By Blood Alone" guard.

    These effects crash or silently fail without the BBA DLC. Every call must
    be inside an if block that checks has_dlc = "By Blood Alone".
    """
    issues = []
    depth = 0
    dlc_guard_stack = []

    for i, line in enumerate(lines):
        code = strip_inline_comment(line)

        if _RE_DLC_BBA.search(code):
            if dlc_guard_stack:
                dlc_guard_stack[-1] = True

        opens = code.count("{")
        closes = code.count("}")

        if _RE_IF_OPEN.search(code):
            for _ in range(opens):
                depth += 1
                dlc_guard_stack.append(False)
        else:
            for _ in range(opens):
                depth += 1
                dlc_guard_stack.append(
                    dlc_guard_stack[-1] if dlc_guard_stack else False
                )

        m = _RE_EMBARGO.search(code)
        if m:
            guarded = any(dlc_guard_stack)
            if not guarded:
                issues.append(
                    (
                        i + 1,
                        f'{m.group(1)} without has_dlc = "By Blood Alone" guard'
                        f' -- wrap in if = {{ limit = {{ has_dlc = "By Blood Alone" }} }}',
                    )
                )

        for _ in range(closes):
            if dlc_guard_stack:
                dlc_guard_stack.pop()
            depth = max(0, depth - 1)

    return issues


def _check_divide_variable_zero_guard(lines):
    """Flag divide_variable where the divisor is a variable without a zero guard.

    Division by a variable that could be zero produces NaN.
    Recognized guards (suppress the warning):
      - check_variable { divisor > 0 } in enclosing scope
      - clamp_variable / clamp_temp_variable { var = divisor min = N } where N > 0
      - set_variable { divisor = N } where N != 0 (variable is initialized)
      - Division inside an else block whose sibling if checks divisor = 0 or < threshold
    """
    issues = []
    guarded_vars = set()
    depth = 0
    depth_stack = []  # stack of (depth, set_of_vars_guarded_at_this_depth)
    # Track the last if-block's checked variable for else-block inference
    last_if_checked_var = None

    for i, line in enumerate(lines):
        code = strip_inline_comment(line)

        opens = code.count("{")
        closes = code.count("}")

        # Detect if-block checking a variable = 0 or < threshold
        if _RE_IF_OPEN.search(code):
            check_m = _RE_CHECK_VAR_LE.search(code)
            if check_m:
                last_if_checked_var = check_m.group(1)
            else:
                last_if_checked_var = None

        # Detect else block — the if's checked var is safe in this branch
        if _RE_ELSE_OPEN.search(code) and last_if_checked_var:
            guarded_vars.add(last_if_checked_var)
            depth_stack.append((depth + opens, last_if_checked_var))
            last_if_checked_var = None

        # Detect clamp guards
        clamp_m = _RE_CLAMP_GUARD.search(code)
        if clamp_m:
            try:
                if float(clamp_m.group(2)) > 0:
                    guarded_vars.add(clamp_m.group(1))
            except ValueError:
                pass

        # Detect check_variable > 0 guards
        check_guard_m = _RE_CHECK_VAR_GT.search(code)
        if check_guard_m:
            guarded_vars.add(check_guard_m.group(1))

        # Detect set_variable with a non-zero literal (variable is initialized)
        set_var_m = _RE_SET_VAR_NONZERO.search(code)
        if set_var_m:
            try:
                if float(set_var_m.group(2)) != 0:
                    guarded_vars.add(set_var_m.group(1))
            except ValueError:
                pass

        # Check divide_variable
        m = _RE_DIVIDE_VAR.search(code)
        if m:
            divisor = m.group(2)
            try:
                float(divisor)
            except ValueError:
                if divisor not in guarded_vars:
                    issues.append(
                        (
                            i + 1,
                            f"divide_variable by '{divisor}' without a zero guard"
                            f" -- add check_variable = {{ {divisor} > 0 }} before dividing",
                        )
                    )

        # Update depth and clean up guarded vars when scopes close
        new_depth = depth + opens - closes
        while depth_stack and depth_stack[-1][0] > new_depth:
            _, var = depth_stack.pop()
            guarded_vars.discard(var)
        depth = new_depth

    return issues


def _check_duplicate_add_to_variable(lines):
    """Flag exact-duplicate consecutive add_to_variable / add_to_temp_variable lines.

    Identical adjacent lines are almost always copy-paste errors. Legitimate
    double-adds (e.g., intentionally adding 0.10 twice) should use the summed
    value directly.
    """
    issues = []
    prev_stripped = None
    prev_lineno = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            # Blank lines and comments break the consecutive chain
            prev_stripped = None
            continue
        if (
            _RE_ADD_TO_VAR.match(line)
            and prev_stripped is not None
            and stripped == prev_stripped
        ):
            issues.append(
                (
                    i + 1,
                    f"duplicate consecutive add_to_variable line (same as line"
                    f" {prev_lineno}) -- likely copy-paste error; use the"
                    f" combined value in a single line",
                )
            )
        prev_stripped = stripped
        prev_lineno = i + 1
    return issues


def _check_empty_log_only_blocks(lines):
    """Flag option/complete_effect blocks where log is the only content.

    A log statement with no actual effects is pointless -- remove it.
    Exception: remove_effect blocks in decisions should always have logs for debugging.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        block_start = None
        block_type = None

        for pattern, btype in [
            (_RE_OPTION_BLOCK_OPEN, "option"),
            (_RE_COMPLETE_EFFECT_OPEN, "complete_effect"),
        ]:
            if pattern.search(line):
                block_start = i
                block_type = btype
                break

        if block_start is not None:
            block_lines, next_i = _get_block(lines, block_start)
            content_lines = [
                l.strip()
                for l in block_lines[1:-1]
                if l.strip() and not l.strip().startswith("#")
            ]

            if len(content_lines) == 1 and _RE_LOG_ONLY_EFFECT.match(content_lines[0]):
                issues.append(
                    (
                        block_start + 1,
                        f'log = "..." is the only content in this {block_type} block -- '
                        "remove it (logs should accompany effects, not replace them)",
                    )
                )
            i = next_i
        else:
            i += 1
    return issues


def _check_is_x_nation_runtime(lines):
    """Flag is_X_nation triggers in runtime contexts (available, visible, effect).

    The is_X_nation scripted triggers iterate over tag lists and are relatively
    expensive. In runtime contexts (available, visible, effect blocks, limit clauses),
    use the pre-computed has_country_flag = X_flag instead for O(1) lookup.

    Safe to use in allowed = { } which is evaluated once at game start.
    """
    issues = []
    in_allowed = False
    allowed_depth = 0
    brace_depth = 0

    for i, line in enumerate(lines, 1):
        code = strip_inline_comment(line)

        opens = code.count("{")
        closes = code.count("}")

        # Check for allowed block start
        if _RE_ALLOWED_OPEN_WB.search(code) and "allowed_civil_war" not in code:
            in_allowed = True
            allowed_depth = brace_depth + opens - closes

        # Update brace depth after checking for allowed
        brace_depth += opens - closes

        # Check if we exited allowed block
        if in_allowed and brace_depth <= allowed_depth - 1:
            in_allowed = False
            allowed_depth = 0

        # Flag is_X_nation if not in allowed block
        if not in_allowed:
            match = _RE_IS_X_NATION.search(code)
            if match:
                nation_type = match.group(1) if match.group(1) else ""
                flag_name = (
                    f"{nation_type}nation_flag" if nation_type else "nation_flag"
                )
                # Only suggest a flag the codebase actually sets. Some triggers
                # (e.g. is_cartel_nation) have no flag fast path, so there is no
                # O(1) replacement to recommend.
                if flag_name not in _REAL_NATION_FLAGS:
                    continue
                issues.append(
                    (
                        i,
                        f"is_X_nation in runtime context -- use has_country_flag = {flag_name} for O(1) lookup (allowed = {{ }} is OK for game-start checks)",
                    )
                )

    return issues


def _check_every_country_member_array(lines):
    """Flag every_country { limit = { has_idea = X_member } } when a pre-built array exists.

    The known member ideas (EU_member, NATO_member, CSTO_member, AU_member) all
    have corresponding global arrays. Using for_each_scope_loop with the array
    is cheaper and more correct.

    Suppresses when:
      - has_idea is inside a NOT block (filtering OUT members, not iterating them)
      - has_idea is nested inside an OVERLORD or other sub-scope check
      - The limit contains an OR with non-array-backed ideas (too complex to convert)
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        if _RE_EVERY_COUNTRY_OPEN.match(lines[i]):
            open_line = i
            block, next_i = _get_block(lines, i)
            # Only check the first-level limit block, not nested if-limits.
            # The limit is typically within the first 5 lines of every_country.
            limit_text = ""
            depth = 0
            in_limit = False
            limit_depth_start = 0
            for bl in block[:30]:
                bc = strip_inline_comment(bl)
                # Only match the every_country's own limit (depth == 1,
                # i.e. directly inside every_country = { }).
                # Reject lines where limit is preceded by if/else on the
                # same line (those are nested limits, not the top-level one).
                if (
                    _RE_LIMIT_OPEN.search(bc)
                    and depth == 1
                    and not in_limit
                    and not _RE_IF_ELSE_OPEN.search(bc)
                ):
                    in_limit = True
                    limit_depth_start = depth
                if in_limit:
                    limit_text += " " + bc.strip()
                    depth += bc.count("{") - bc.count("}")
                    if depth <= limit_depth_start:
                        break
                else:
                    depth += bc.count("{") - bc.count("}")

            for idea, array in _MEMBER_IDEA_TO_ARRAY.items():
                re_has, re_not, re_scope = _MEMBER_IDEA_PATTERNS[idea]
                if not re_has.search(limit_text):
                    continue
                if re_not.search(limit_text):
                    continue
                if re_scope.search(limit_text):
                    continue
                or_match = _RE_OR_CONTENT.search(limit_text)
                if or_match:
                    or_content = or_match.group(1)
                    other_ideas = _RE_HAS_IDEA.findall(or_content)
                    non_array_ideas = [
                        x for x in other_ideas if x not in _MEMBER_IDEA_TO_ARRAY
                    ]
                    if non_array_ideas:
                        continue
                issues.append(
                    (
                        open_line + 1,
                        f"every_country with has_idea = {idea} -- use"
                        f" for_each_scope_loop = {{ array = {array} }} instead"
                        f" (narrower iteration, better performance)",
                    )
                )
                break
            i = next_i
        else:
            i += 1
    return issues


def _check_influence_setter_scope(lines):
    """Flag change_influence_percentage temp-var setters that never reach the effect.

    Two silent no-op patterns (both valid syntax, so the engine logs nothing):
      - A `percent_change` setter in a file that never calls change_influence_percentage.
      - `percent_change` set inside an every_/random_*country loop with no
        change_influence_percentage = yes inside that same loop block; the loop
        re-scopes each pass, so the call (outside the loop) sees stale/default values.

    Does NOT touch absent tag_index/influence_target -- those default to
    ROOT.id / THIS.id and are intentionally omitted across the codebase.
    """
    issues = []
    if not any(
        _RE_PERCENT_CHANGE_SETTER.search(strip_inline_comment(ln)) for ln in lines
    ):
        return issues

    file_has_call = any(
        _RE_CHANGE_INFLUENCE_CALL.search(strip_inline_comment(ln)) for ln in lines
    )
    if not file_has_call:
        for i, line in enumerate(lines, 1):
            if _RE_PERCENT_CHANGE_SETTER.search(strip_inline_comment(line)):
                issues.append(
                    (
                        i,
                        "percent_change is set but change_influence_percentage = yes is never "
                        "called in this file -- the setter is a silent no-op",
                    )
                )
        return issues

    i = 0
    n = len(lines)
    while i < n:
        if _RE_INFLUENCE_LOOP_OPEN.match(strip_inline_comment(lines[i])):
            block, next_i = _get_block(lines, i)
            block_code = [strip_inline_comment(bl) for bl in block]
            has_setter = any(_RE_PERCENT_CHANGE_SETTER.search(c) for c in block_code)
            has_call = any(_RE_CHANGE_INFLUENCE_CALL.search(c) for c in block_code)
            if has_setter and not has_call:
                issues.append(
                    (
                        i + 1,
                        "percent_change set inside a country-iteration loop with no "
                        "change_influence_percentage = yes in the same loop -- the call must "
                        "live inside the loop or it runs on stale/default values",
                    )
                )
            i = next_i
        else:
            i += 1
    return issues


def _check_check_var_ge_le(lines):
    """Flag check_variable blocks using inline >= or <= (silently mis-parsed)."""
    issues = []
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        code_part = strip_inline_comment(line) if "#" in line else line
        cv_match = _RE_CHECK_VAR_GE_LE.search(code_part)
        if cv_match:
            op = cv_match.group(1)
            kind = "greater_than_or_equals" if op == ">=" else "less_than_or_equals"
            issues.append(
                (
                    line_num,
                    f"check_variable does not accept '{op}' inline (silently mis-parsed) -- "
                    f"use compare = {kind} or rewrite as a strict inequality",
                )
            )
    return issues


def _check_tautological_or(lines):
    """Flag OR = { X = yes X = no } blocks, which are always true."""
    issues = []
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        code_part = strip_inline_comment(line) if "#" in line else line
        or_match = _RE_TAUTOLOGICAL_OR.search(code_part)
        if (
            or_match
            and or_match.group(1) == or_match.group(3)
            and ({or_match.group(2), or_match.group(4)} == {"yes", "no"})
        ):
            token = or_match.group(1)
            issues.append(
                (
                    line_num,
                    f"tautological OR = {{ {token} = yes {token} = no }} is always true -- "
                    "remove the OR (fold any intended amount into base = N)",
                )
            )
    return issues


def check_file(filepath):
    """Check a single file for common mistakes. Returns list of (filepath, line_num, message) tuples."""
    issues = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return issues

    is_ideas = "common/ideas" in filepath
    is_focus_file = "common/national_focus" in filepath
    is_decision_file = "common/decisions" in filepath
    is_ai_file = (
        is_focus_file
        or is_decision_file
        or "common/military_industrial_organization" in filepath
    )

    # Only track idea categories for idea files (non-selectable vs selectable)
    # Dynamically parsed from common/idea_tags/*.txt
    FLAGGED_IDEA_CATEGORIES = get_non_selectable_idea_categories()
    current_category = None
    brace_depth = 0
    ideas_depth = None
    # Multi-line allowed block tracking (flags only if sole content is always = no)
    in_allowed_block = False
    allowed_block_start_line = 0
    allowed_block_depth = 0
    allowed_block_lines = []

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        if is_ideas:
            brace_depth += stripped.count("{") - stripped.count("}")

            if _RE_IDEAS_BLOCK.match(stripped):
                ideas_depth = brace_depth - 1
            if ideas_depth is not None and brace_depth == ideas_depth + 2:
                cat_match = _RE_CATEGORY.match(stripped)
                if cat_match:
                    current_category = cat_match.group(1)
            elif ideas_depth is not None and brace_depth <= ideas_depth + 1:
                current_category = None

        if stripped.startswith("#"):
            continue

        code_part = strip_inline_comment(line) if "#" in line else line

        # threat is 0.0-1.0; exclude add_threat/named_threat which use absolute values
        threat_match = _RE_THREAT.search(code_part)
        if (
            threat_match
            and "add_threat" not in code_part
            and "named_threat" not in code_part
        ):
            value = float(threat_match.group(2))
            if value >= 1.0:
                issues.append(
                    (
                        line_num,
                        f"threat {threat_match.group(1)} {value} looks like a percentage -- threat is 0.0-1.0 (use {round(value / 100.0, 4)}?)",
                    )
                )

        for trigger_name, pattern in (
            ("has_war_support", _RE_WAR_SUPPORT),
            ("has_stability", _RE_STABILITY),
        ):
            ws_match = pattern.search(code_part)
            if ws_match:
                value = float(ws_match.group(2))
                if value >= 1.0:
                    issues.append(
                        (
                            line_num,
                            f"{trigger_name} {ws_match.group(1)} {ws_match.group(2)} looks like a percentage -- {trigger_name} is 0.0-1.0 (use {round(value / 100.0, 4)}?)",
                        )
                    )

        if is_ideas and current_category in FLAGGED_IDEA_CATEGORIES:
            if _RE_ALLOWED_ALWAYS_NO.search(code_part):
                issues.append(
                    (
                        line_num,
                        f"allowed = {{ always = no }} is the default for ideas in '{current_category}' -- remove it (checked once at load; add_ideas bypasses it)",
                    )
                )
            elif _RE_ALLOWED_OPEN.search(code_part) and "}" not in code_part:
                in_allowed_block = True
                allowed_block_start_line = line_num
                allowed_block_depth = brace_depth
                allowed_block_lines = []
            if _RE_ALLOWED_TAG.search(code_part):
                issues.append(
                    (
                        line_num,
                        "allowed = { tag = TAG } breaks for civil war split-offs -- use original_tag = TAG instead",
                    )
                )

        # Multi-line allowed block: flag only if sole content is always = no
        if in_allowed_block:
            if brace_depth < allowed_block_depth:
                content_lines = [
                    l for l in allowed_block_lines if l not in ("", "{", "}")
                ]
                if content_lines == ["always = no"]:
                    issues.append(
                        (
                            allowed_block_start_line,
                            f"allowed = {{ always = no }} is the default for ideas in '{current_category}' -- remove it (checked once at load; add_ideas bypasses it)",
                        )
                    )
                in_allowed_block = False
                allowed_block_lines = []
            elif stripped and not _RE_ALLOWED_OPEN.match(stripped):
                allowed_block_lines.append(stripped)

        if is_ideas:
            if _RE_ALLOWED_CIVIL_WAR.search(code_part):
                issues.append(
                    (
                        line_num,
                        "allowed_civil_war = { always = no } has no effect -- remove it",
                    )
                )
            if _RE_CANCEL.search(code_part):
                issues.append(
                    (
                        line_num,
                        "cancel = { always = no } is checked hourly and never true -- remove it (redundant default)",
                    )
                )

        # [^{]*? stops before any nested { so modifier = { factor = X } children are not flagged
        if is_ai_file and _RE_AI_WILL_DO.search(code_part):
            issues.append(
                (
                    line_num,
                    "ai_will_do root-level 'factor =' should be 'base =' -- factor is only valid inside modifier = { } children",
                )
            )

        faction_match = _RE_IS_IN_FACTION_TAG.search(code_part)
        if faction_match:
            tag = faction_match.group(1)
            issues.append(
                (
                    line_num,
                    f"is_in_faction = {tag} is invalid -- is_in_faction takes yes/no; use is_in_faction_with = {tag}",
                )
            )

        if _RE_TRADE_AGREEMENT_WITH.search(code_part):
            issues.append(
                (
                    line_num,
                    "has_trade_agreement_with is not a valid trigger -- use has_country_flag = trade_agreement@TAG",
                )
            )

        div_match = _RE_DIVISION.search(code_part)
        if div_match:
            divisor = int(div_match.group(1))
            multiplier = 1.0 / divisor
            mult_str = (
                str(int(multiplier))
                if multiplier == int(multiplier)
                else f"{multiplier:g}"
            )
            issues.append(
                (
                    line_num,
                    f"use multiplication instead of division (/ {divisor} -> * {mult_str})",
                )
            )

    for ln, msg in find_single_condition_or_blocks(lines):
        issues.append((ln, msg))
    for ln, msg in find_redundant_and_blocks(lines):
        issues.append((ln, msg))
    issues.extend(_check_mutually_exclusive_contradictions(lines))
    issues.extend(_check_has_idea_mutex_in_not_block(lines))

    if is_focus_file:
        issues.extend(_check_focus_available_always_no(lines))
    if is_decision_file:
        issues.extend(_check_decision_available_always_no(lines))
        issues.extend(_check_decision_allowed_dynamic(lines))

    issues.extend(_check_consecutive_scope_blocks(lines))
    issues.extend(_check_embargo_dlc_guard(lines))
    issues.extend(_check_divide_variable_zero_guard(lines))
    issues.extend(_check_duplicate_add_to_variable(lines))
    issues.extend(_check_every_country_member_array(lines))
    issues.extend(_check_empty_log_only_blocks(lines))
    issues.extend(_check_is_x_nation_runtime(lines))
    issues.extend(_check_influence_setter_scope(lines))
    issues.extend(_check_check_var_ge_le(lines))
    issues.extend(_check_tautological_or(lines))

    return [(filepath, ln, msg) for ln, msg in issues]


def main():
    parser = create_linting_parser("Check for common HOI4 scripting mistakes")
    args = parser.parse_args()

    timings = []
    root_dir = get_root_dir()

    with Timer("file collection") as t:
        files_list = collect_files_by_mode(args, root_dir)
    timings.append(("file collection", t.elapsed))

    if not files_list:
        print("No files to check")
        return 0

    # Always scan globally (~1.3s): the available=always-no and is_X_nation checks
    # depend on completion refs and real nation flags, and they run in every mode
    # (pre-commit --mode staged, CI positional args). Skipping the scan there made
    # both checks false-positive on legitimately script-completed focuses and on
    # triggers with no flag fast path.
    global _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS, _REAL_NATION_FLAGS
    with Timer("scan global refs") as t:
        _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS, _REAL_NATION_FLAGS = (
            _scan_global_refs(root_dir)
        )
    timings.append(("scan global refs", t.elapsed))

    print(f"Checking {len(files_list)} files for common mistakes...")

    with Timer("checking") as t:
        results = run_with_pool(
            check_file,
            files_list,
            args.workers,
            initializer=_init_worker,
            initargs=(
                _SCRIPT_COMPLETED_FOCUSES,
                _SCRIPT_COMPLETED_DECISIONS,
                _REAL_NATION_FLAGS,
            ),
        )
    timings.append(("checking", t.elapsed))

    all_issues = [issue for file_issues in results for issue in file_issues]

    for filepath, line_num, message in sorted(all_issues):
        print(f"{clean_filepath(filepath)}:{line_num}: {message}")
    # Summary after processing all issues
    print(f"------\nChecked {len(files_list)} files")
    if all_issues:
        print(f"Found {len(all_issues)} issue(s)")
        print("Issues found - fix them before committing")
        print_timing_summary(timings)
        return 1
    print("No issues found")
    print("Check PASSED")
    print_timing_summary(timings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
