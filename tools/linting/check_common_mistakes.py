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
  - NOT = { country_exists = TAG } alongside a TAG = { ... } scope switch in the
    same AND block — always false; caller meant OR = { ... }. Multi-statement
    NOTs (NAND) and scopes checking only flags/variables (valid on dead tags)
    are exempt.
  - Consecutive same-tag scope blocks that should be merged
  - send_embargo/break_embargo without has_dlc = "By Blood Alone" guard
  - divide_variable by a variable without a zero guard
  - Duplicate consecutive add_to_variable / add_to_temp_variable lines
  - every_country with has_idea = X_member when a pre-built array exists
    (display_individual_scopes loops exempt -- conversion collapses their output)
  - is_in_faction = TAG (boolean trigger misused with a tag; should be is_in_faction_with)
  - has_trade_agreement_with (not a valid trigger; MD uses has_country_flag = trade_agreement@TAG)
  - Dynamic triggers inside decision allowed blocks (allowed is evaluated once at game start)
  - is_X_nation triggers in runtime contexts (available, effect, limit) — use has_country_flag = X_flag instead
  - check_variable with inline >= or <= (silently mis-parsed; use compare = ... or a strict inequality)
  - Tautological OR = { X = yes X = no } (always true; remove the OR)
  - percent_change set without a reachable change_influence_percentage = yes (silent no-op / loop-scope bug)
  - check_expr operand chained with a raw comparator symbol (greater_than > 6),
    a check_variable-style leftover; block form or a bare scalar are both valid
  - every_owned_controlled_state (does not exist; use every_controlled_state)
  - random_select_amount set to a variable/decimal instead of an integer literal
  - log = "...Focus X" / "...Decision X" / "...Event X" where X doesn't match the
    enclosing focus/decision/event id (copy-paste bug from duplicating a neighbor)
  - hidden_trigger = { } directly inside custom_trigger_tooltip (redundant nesting)
  - Malformed leader rotations in common/scripted_effects/*_political_leaders.txt:
    a tier that advances its counter by anything but 1, a do_not_retire guard that
    doesn't undo its own tier's increment, a gap or an undiscriminated duplicate in a
    branch's tier numbers, a second if/else_if branch on an already-handled set_
    ideology flag, an always-false NOT = { check_variable = { b = 0 } }, and a branch
    counting with another ideology's leader counter. set_leader kills the country
    leader before dispatching, so every one of these hands the country a randomly
    generated leader.
  - add_to_faction = X where X is not a country (a faction name like BRICS, or a
    lowercase id) -- add_to_faction adds the ARGUMENT country to the current
    scope's faction; it takes a country tag or scope ref, never a faction name.
  - create_faction = X (deprecated; use create_faction_from_template = TEMPLATE
    for DLC compatibility)
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
_RE_POSSIBLE_OPEN_WB = re.compile(r"\bpossible\s*=\s*\{")
_RE_ALLOWED_TAG = re.compile(r"allowed\s*=\s*\{\s*tag\s*=\s*\w+\s*\}")
_RE_ALLOWED_CIVIL_WAR = re.compile(r"allowed_civil_war\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_CANCEL = re.compile(r"cancel\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_AI_WILL_DO = re.compile(r"ai_will_do\s*=\s*\{[^{]*?\bfactor\b\s*=")
_RE_DIVISION = re.compile(r"/\s*(100|1000|10|50|200|500)\b")
# check_variable only accepts =, >, < inline; >= and <= are silently mis-parsed
# (no error.log entry) and the check never matches. Long form needs compare = ...
_RE_CHECK_VAR_GE_LE = re.compile(r"check_variable\s*=\s*\{[^}]*?(>=|<=)")
# check_expr operands accept block form (greater_than = { value = X }) or a bare
# scalar (greater_than = 6) -- both are valid. A raw comparator symbol chained
# after the operator keyword (greater_than > 6) is a check_variable-style
# leftover that parses silently wrong. Longest names first so alternation
# doesn't stop at a prefix.
_RE_CHECK_EXPR_OPEN = re.compile(r"\bcheck_expr\s*=\s*\{")
_RE_CHECK_EXPR_BAD_OPERAND = re.compile(
    r"\b(greater_than_or_equals|less_than_or_equals|greater_than|less_than|"
    r"not_equals|equals)\s*([><])\s*\S"
)
_RE_EVERY_OWNED_CONTROLLED_STATE = re.compile(r"\bevery_owned_controlled_state\b")
_RE_RANDOM_SELECT_AMOUNT = re.compile(r"\brandom_select_amount\s*=\s*([^\s}]+)")
_RE_BARE_INT = re.compile(r"^-?\d+$")
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
_RE_FOCUS_ID_IN_BLOCK = re.compile(r"\bid\s*=\s*([\w-]+)")
_RE_COMPLETE_FOCUS = re.compile(r"\bcomplete_national_focus\s*=\s*([\w-]+)")
_RE_UNLOCK_FOCUS = re.compile(r"\bunlock_national_focus\s*=\s*([\w-]+)")
_RE_ACTIVATE_DECISION = re.compile(r"\bactivate_decision\s*=\s*([\w-]+)")
_RE_FOCUS_ANY_BLOCK_OPEN = re.compile(
    r"^\s*(?:focus|shared_focus|joint_focus)\s*=\s*\{"
)
_RE_LOG_FOCUS_TOKEN = re.compile(r'log\s*=\s*"[^"]*\bFocus\s+([\w-]+)', re.IGNORECASE)
# "Decision <keyword...> <id>" tolerates a chain of filler words before the real
# id: the block-name keywords (remove/complete/completed/timeout/cancel/add,
# describing which effect block logged the line) and, in a couple of legacy
# logs, a spelled-out "effect" after the keyword ("Decision cancel effect X"
# for a cancel_effect block). Strip all leading filler tokens, then compare
# whatever's left to the decision's own id.
_DECISION_LOG_FILLER_WORDS = {
    "remove",
    "complete",
    "completed",
    "timeout",
    "cancel",
    "add",
    "effect",
}
_RE_LOG_DECISION_MARKER = re.compile(r'log\s*=\s*"[^"]*\bDecision\b', re.IGNORECASE)
_RE_NEXT_WORD = re.compile(r"\s+([\w-]+)")
# Event ids are namespace.number (dots), unlike focus/decision ids -- \w+ alone
# would truncate at the dot.
_RE_EVENT_DEF_OPEN = re.compile(
    r"^(?:country_event|news_event|operative_leader_event|unit_leader_event)\s*=\s*\{"
)
_RE_EVENT_ID_IN_BLOCK = re.compile(r"^\s*id\s*=\s*([\w.]+)")
_RE_OPTION_NAME_IN_BLOCK = re.compile(r"^\s*name\s*=\s*([\w.]+)")
# Two log conventions coexist: the bare event id followed by a separate
# "Option <letter>" phrase ("Event HKG_contract.1 Option a"), and the option's
# own full dotted name standing in for the id ("event satellites.2.a" ==
# namespace.number.letter). [\w.]+ is greedy, so on the second style it
# swallows the trailing ".<letter>" into the token -- checked against both
# forms below rather than assuming the bare id alone.
_RE_LOG_EVENT_TOKEN = re.compile(r'log\s*=\s*"[^"]*\bEvent\s+([\w.]+)', re.IGNORECASE)
_RE_LOG_EVENT_OPTION_SUFFIX = re.compile(r"\s+Option\s+([a-zA-Z])\b", re.IGNORECASE)
_RE_CUSTOM_TRIGGER_TOOLTIP_OPEN = re.compile(r"\bcustom_trigger_tooltip\s*=\s*\{")
_RE_HIDDEN_TRIGGER_OPEN = re.compile(r"\bhidden_trigger\s*=\s*\{")
_RE_FOCUS_BLOCK_OPEN = re.compile(r"^\s*focus\s*=\s*\{")
# A focus block that declares war via create_wargoal/declare_war at the focus
# OWNER's scope must carry the matching will_lead_to_war_with hint so the AI
# prepares. A war effect nested inside another country's scope (SAU = {
# declare_war_on = ... }) makes that THIRD PARTY go to war, not the owner, so it
# obligates no hint. effect_tooltip / hidden_effect / if / OR preserve the owner
# scope and still count; ROOT/THIS reset back to the owner.
_RE_WILL_LEAD_TO_WAR = re.compile(r"\bwill_lead_to_war_with\b")
_RE_SCRIPT_TOKEN = re.compile(r"[{}=]|[A-Za-z_][\w:.@]*")
_RE_QUOTED_STRING = re.compile(r'"[^"]*"')
# Tokens for the leader-rotation tree parser: braces, the comparison operators a
# limit can use, and everything else as one word (ideology names carry '-').
_RE_SCRIPT_NODE = re.compile(r"[{}]|[<>]=?|=|[^\s{}=<>]+")
_NODE_OPERATORS = {"=", "<", ">", "<=", ">="}
_TIER_KEYWORDS = {"if", "else_if"}
_LEADER_EFFECT_PREFIX = "set_leader_"
_LEADER_COUNTER_SUFFIX = "_leader"
_SET_IDEOLOGY_PREFIX = "set_"
_DO_NOT_RETIRE_FLAG = "do_not_retire"
_RE_TAG_SCOPE = re.compile(r"^[A-Z]{2,3}$")
_LOGIC_SCOPE_TOKENS = {"AND", "OR", "NOT"}
_OWNER_RESET_SCOPE_TOKENS = {"ROOT", "THIS"}
_FOREIGN_COUNTRY_SCOPE_TOKENS = {
    "random_country",
    "random_other_country",
    "every_country",
    "every_other_country",
    "every_neighbor_country",
    "random_neighbor_country",
    "every_enemy_country",
    "random_enemy_country",
    "every_subject_country",
    "random_subject_country",
}
_RE_WHITESPACE_COLLAPSE = re.compile(r"\s+")
_RE_AVAILABLE_OPEN = re.compile(r"\bavailable\s*=\s*\{")
_RE_TOPLEVEL_WORD = re.compile(r"^\w")
_RE_INDENTED_WORD = re.compile(r"^\s+\w")
_RE_BLOCK_ID = re.compile(r"\s*([\w-]+)\s*=\s*\{")
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
# add_to_faction adds the ARGUMENT country to the current scope's faction, so it
# takes a country tag or scope ref -- never a faction id (add_to_faction = BRICS
# is a no-op; BRICS is a faction, not a country). The value captures identifier
# chars only so a trailing } / whitespace ends the token.
_RE_ADD_TO_FACTION = re.compile(r"\badd_to_faction\s*=\s*([A-Za-z0-9_:.@\[\]]+)")
# create_faction is deprecated in MD; factions must be built via
# create_faction_from_template for DLC compatibility. The trailing \s*=
# requirement alone rules out create_faction_from_template (the replacement),
# and \b at the start rules out on_create_faction (the on_actions hook) since
# _ is a word char and leaves no boundary between the trailing on_ and create.
_RE_CREATE_FACTION_DEPRECATED = re.compile(r"\bcreate_faction\s*=")
_ADD_TO_FACTION_SCOPE_KEYWORDS = {
    "ROOT",
    "FROM",
    "PREV",
    "THIS",
    "OWNER",
    "CONTROLLER",
    "CAPITAL",
}
_RE_DECISION_ALLOWED_DYNAMIC = re.compile(
    r"\b(?:num_of_factories|has_opinion|strength_ratio|"
    r"has_army_size|has_navy_size|has_political_power|date)\b"
)
_RE_IS_X_NATION = re.compile(r"\bis_([a-z][a-z_]*_)?nation\s*=\s*yes\b")
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
# Token scanner for the single-valued-trigger contradiction check: braces and
# `trigger = value` for each mutually-exclusive trigger, in source order, so
# single-line `NOT = { tag = USA tag = CHI }` is caught alongside multi-line.
# Built from _MUTUALLY_EXCLUSIVE_TRIGGERS (single source of truth) so adding a
# trigger there extends the check; longest name first so original_tag wins the
# alternation over tag.
_RE_MUTEX_TRIGGER_TOKEN = re.compile(
    r"\{|\}|\b("
    + "|".join(
        re.escape(t)
        for t in sorted(_MUTUALLY_EXCLUSIVE_TRIGGERS, key=lambda t: (-len(t), t))
    )
    + r")\s*=\s*([\w.]+)"
)

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
      - complete_national_focus = ID / unlock_national_focus = ID / activate_decision
        = ID, so the checkers can skip flagging items reached by script. A focus gated
        behind available = { always = no } is reachable once a parent focus unlocks it.
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
                    for m in _RE_UNLOCK_FOCUS.finditer(content):
                        focuses.add(m.group(1))
                    for m in _RE_ACTIVATE_DECISION.finditer(content):
                        decisions.add(m.group(1))
                    for m in _RE_SET_NATION_FLAG.finditer(content):
                        nation_flags.add(m.group(1))
                except Exception:
                    pass
    return focuses, decisions, nation_flags


def _targeted_mode(args) -> bool:
    """True when the run is scoped to an explicit small file set (pre-commit
    positional args, --files, --mode staged/diff) rather than the whole repo."""
    return (
        bool(getattr(args, "filenames", None))
        or bool(getattr(args, "files", None))
        or getattr(args, "mode", "all") in ("staged", "diff")
    )


def _files_need_global_refs(files_list) -> bool:
    """True if any targeted file could trigger a check that consumes the global
    reference sets: focus/decision available = { always = no } (needs completion
    refs) or is_X_nation (needs real nation flags). Reads the small targeted set
    once so a clean set can skip the ~2s full-tree scan; unreadable files force
    the scan to stay safe.
    """
    for fp in files_list:
        nf = fp.replace("\\", "/")
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            return True
        if _RE_IS_X_NATION.search(content):
            return True
        if (
            "common/national_focus" in nf or "common/decisions" in nf
        ) and _RE_AVAILABLE_ALWAYS_NO.search(content):
            return True
    return False


def _get_block(lines, start):
    """Collect the complete brace-delimited block starting at lines[start].
    Returns (block_lines, next_idx) where next_idx is the first index after the block.
    Works on any list — passing a sub-list is safe.
    """
    code = _code_for_depth(lines[start])
    depth = code.count("{") - code.count("}")
    j = start + 1
    while depth > 0 and j < len(lines):
        code = _code_for_depth(lines[j])
        depth += code.count("{") - code.count("}")
        j += 1
    return lines[start:j], j


def _code_for_depth(line):
    """Like strip_inline_comment, but also blanks quoted strings before brace
    counting. A log string can contain a stray brace (e.g. a formatted-loc
    placeholder); left unblanked it would drift the depth count for whatever
    manual brace-tracking scans past it.
    """
    return _RE_QUOTED_STRING.sub('""', strip_inline_comment(line))


def _check_focus_available_always_no(lines):
    """Flag available = { always = no } with no completion mechanism.

    Valid completion mechanisms (all skip the flag):
      - bypass block present (focus auto-bypasses when conditions fire)
      - complete_national_focus = FOCUS_ID found elsewhere in the codebase
      - unlock_national_focus = FOCUS_ID found elsewhere (a parent focus unlocks it,
        which overrides the always = no gate)

    Only flags when available=always-no AND no mechanism is present,
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
                                    "available = { always = no } with no bypass, complete_national_focus,"
                                    " or unlock_national_focus -- focus is permanently unreachable;"
                                    " add a bypass block or reach it via complete/unlock_national_focus",
                                )
                            )
                            break
        else:
            i += 1
    return issues


def _scope_frame_kind(opener, owner_tag=None):
    """Classify a `<opener> = { ... }` block by how it affects country scope."""
    if opener is None or opener in _LOGIC_SCOPE_TOKENS:
        return "neutral"
    if opener in _OWNER_RESET_SCOPE_TOKENS or (owner_tag and opener == owner_tag):
        return "reset"
    if opener in _FOREIGN_COUNTRY_SCOPE_TOKENS:
        return "foreign"
    if opener.startswith("var:") or opener.startswith("event_target:"):
        return "foreign"
    if _RE_TAG_SCOPE.match(opener):
        return "foreign"
    return "neutral"


def _focus_owner_tag(code):
    """Owner tag inferred from the focus id prefix (e.g. PER_alawites -> PER)."""
    id_match = _RE_FOCUS_ID_IN_BLOCK.search("".join(code))
    if id_match:
        prefix = id_match.group(1).split("_", 1)[0]
        if _RE_TAG_SCOPE.match(prefix):
            return prefix
    return None


def _war_declared_at_owner_scope(code):
    """True if a create_wargoal/declare_war fires at the focus owner's scope.

    Walks the block's brace structure tracking country-scope changes. A war
    effect inside a foreign-country scope (SAU = { declare_war_on = ... }) is a
    proxy war the owner sponsors, not the owner going to war, so it does not
    require a will_lead_to_war_with hint. ROOT/THIS and the owner's own tag
    (PER = { ... } inside a PER_ focus) reset back to the owner.
    """
    owner_tag = _focus_owner_tag(code)
    text = _RE_QUOTED_STRING.sub('""', "\n".join(code))
    stack = []
    last_ident = None
    opener_pending = None
    for tok in _RE_SCRIPT_TOKEN.findall(text):
        if tok == "=":
            opener_pending = last_ident
        elif tok == "{":
            stack.append(_scope_frame_kind(opener_pending, owner_tag))
            opener_pending = None
            last_ident = None
        elif tok == "}":
            if stack:
                stack.pop()
            opener_pending = None
            last_ident = None
        else:
            if tok == "create_wargoal" or tok == "declare_war_on":
                in_foreign = False
                for kind in reversed(stack):
                    if kind == "foreign":
                        in_foreign = True
                        break
                    if kind == "reset":
                        break
                if not in_foreign:
                    return True
            last_ident = tok
            opener_pending = None
    return False


def _check_focus_missing_war_hint(lines):
    """Flag focus blocks that declare war but carry no will_lead_to_war_with hint.

    A focus whose completion_reward calls create_wargoal/declare_war at the
    OWNER's scope should set will_lead_to_war_with = TAG so the AI prepares for
    the war. create_wargoal inside an effect_tooltip still counts; a war effect
    nested in another country's scope (a sponsored proxy war) does not. The hint
    anywhere in the block clears the focus.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        if _RE_FOCUS_BLOCK_OPEN.match(lines[i]):
            start = i
            block, i = _get_block(lines, start)
            code = [strip_inline_comment(bl) for bl in block]
            if _war_declared_at_owner_scope(code) and not any(
                _RE_WILL_LEAD_TO_WAR.search(c) for c in code
            ):
                id_match = _RE_FOCUS_ID_IN_BLOCK.search("".join(code))
                focus_id = id_match.group(1) if id_match else "<unknown>"
                issues.append(
                    (
                        start + 1,
                        f"Focus {focus_id} has create_wargoal but no will_lead_to_war_with"
                        " -- add will_lead_to_war_with = TAG so the AI prepares for war",
                    )
                )
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
        code = _RE_QUOTED_STRING.sub('""', strip_inline_comment(line))
        if not code.strip():
            continue

        last_end = 0
        for m in _RE_MUTEX_TRIGGER_TOKEN.finditer(code):
            tok = m.group(0)
            if tok == "{":
                preceding = code[last_end : m.start()]
                is_not = bool(_RE_NOT_EQ.search(preceding))
                is_or = bool(_RE_OR_EQ.search(preceding))
                stack.append((is_or, is_not, {}))
            elif tok == "}":
                if len(stack) > 1:
                    popped_or, popped_not, popped_triggers = stack.pop()
                    if popped_or:
                        last_end = m.end()
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
            else:
                stack[-1][2].setdefault(m.group(1), []).append((i + 1, m.group(2)))
            last_end = m.end()

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
# Ordered tokens for the embargo DLC-guard scan: braces, the BBA guard, and the
# embargo effects, so an inline guard is attributed to the correct frame.
_RE_DLC_TOKEN = re.compile(
    r'\{|\}|has_dlc\s*=\s*"By Blood Alone"|\b(?:send_embargo|break_embargo)\b'
)
_RE_IF_BEFORE_BRACE = re.compile(r"\b(?:if|else_if)\s*=\s*$")
# trigger/available/visible/allowed gate the whole enclosing object, so a guard
# inside one covers its siblings (unlike an if, which only guards its own body).
_RE_GATE_BEFORE_BRACE = re.compile(r"\b(?:trigger|available|visible|allowed)\s*=\s*$")
_RE_ADD_TO_VAR = re.compile(
    r"^\s*(add_to_variable|add_to_temp_variable)\s*=\s*\{.*\}\s*$"
)
_RE_DIVIDE_VAR = re.compile(r"\bdivide_variable\s*=\s*\{\s*(\S+)\s*=\s*(\S+)\s*\}")

# Globals that are guaranteed non-zero at game start, so dividing by them
# never produces NaN. Hand-maintained: add a global here when it represents a
# count/population/total that the mod initialises to a positive value in
# scripted_effects or history. The `^num` suffix counts an array's entries.
_NONZERO_GLOBAL_DIVISORS = frozenset(
    {
        "global.UN_general_assembly^num",
    }
)
_RE_EVERY_COUNTRY_OPEN = re.compile(r"^\s*(every_other_country|every_country)\s*=\s*\{")
_RE_ANY_COUNTRY_OPEN = re.compile(r"^\s*(any_other_country|any_country)\s*=\s*\{")
# Maps each bloc-membership idea to the global array that should track it.
# MD-specific; hand-maintained. When a new bloc with a membership idea + backing
# array is added (see common/ideas/ and the bloc's scripted_effects), add it here
# or the idea/array consistency check won't cover it. Array names are
# inconsistently pluralized in the mod; these are the canonical spellings.
# LoAS variants: a swap_ideas upgrade means members hold ONE of the two, so a
# loop over either idea alone undercounts -- the array is the source of truth.
# Multi-array ideas (p5_member, at_member, RAJ_BRICS) are excluded: one loop
# over a single array cannot express them.
_MEMBER_IDEA_TO_ARRAY = {
    "EU_member": "global.EU_member",
    "NATO_member": "global.nato_members",
    "CSTO_member": "global.CSTO_member",
    "AU_member": "global.AU_member",
    "LoAS_member": "global.arab_league_members",
    "LoAS_member_upd": "global.arab_league_members",
    "OAU_member": "global.OAU_member",
    "ecowas_member_state": "global.ECOWAS_member",
    "idea_gcc_member_state": "global.gcc_member_state",
    "faction_warsaw_pact_idea": "global.WARSAW_PACT_member",
    "RAJ_BRICS_associate": "global.BRICS_associates",
    "RAJ_BRICS_observer": "global.BRICS_observers",
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


# Tokens for the country_exists-vs-scope contradiction: braces and
# `country_exists = TAG` assignments. The preceding text before each `{`
# is inspected to classify it as NOT / OR / country-scope / plain AND.
_RE_CE_TOKEN = re.compile(r"\{|\}|country_exists\s*=\s*([A-Z]{3})")
_RE_CE_SCOPE_TAG = re.compile(r"\b([A-Z]{3})\s*=\s*$")
_CE_LOGIC_TAGS = {"AND", "OR", "NOT", "FOR", "ALL"}
_RE_CE_STMT = re.compile(r"[=<>]+")
_RE_CE_TRIGGER_KEY = re.compile(r"\b([a-z][a-zA-Z0-9_@.:]*)\s*[=<>]")
_RE_CE_BRACE_BLOCK = re.compile(r"\{[^{}]*\}")
# Flag/variable trigger blocks carry arbitrary parameter and variable names;
# blank them before the key scan so those names don't read as live triggers.
_RE_CE_VAR_BLOCK = re.compile(
    r"\b(?:check_variable|has_variable|is_variable_equals|has_country_flag"
    r"|has_global_flag)\s*=\s*\{[^{}]*\}"
)
# Triggers that hold on a non-existent tag (flags and variables persist on
# dead/unreleased countries). A scope block built only from these is
# satisfiable alongside NOT = { country_exists = TAG }.
_CE_DEAD_TAG_SAFE = {
    "has_country_flag",
    "has_global_flag",
    "has_variable",
    "check_variable",
    "is_variable_equals",
}


def _ce_blank_nested(text, pattern):
    while True:
        new = pattern.sub(" ", text)
        if new == text:
            return text
        text = new


def _check_country_exists_scope_contradiction(lines):
    """Flag an AND block with both `NOT = { country_exists = TAG }` and a
    `TAG = { ... }` country-scope switch as direct siblings.

    The scope switch to TAG fails (always false) when TAG is absent, and the
    NOT is only true when TAG is absent, so their AND is unconditionally false
    -- a dead bypass/available gate. The caller meant OR = { ... }.

    Not flagged: the positive guard-then-scope idiom (`country_exists = TAG`
    next to `TAG = { ... }`), a NOT with several statements (NAND -- no child
    is individually negated), and scope blocks whose triggers all hold on a
    non-existent tag (flag/variable checks -- see _CE_DEAD_TAG_SAFE).
    """
    issues = []
    # Stack frame: [is_or, is_not, opens_tag, open_line, children, texts].
    # opens_tag is "" for non-scope blocks (plain AND / OR / NOT) and the
    # 3-letter tag for a country-scope switch. texts interleaves the frame's
    # own code with each closed child's re-bracketed text, so a frame's full
    # source can be reconstructed for the NAND and dead-tag-safe scans.
    # children entries: (line, kind, tag) where kind is "country_exists"
    # (raw, inside a NOT), "not_country_exists" (emitted from a closed NOT),
    # or "scope_switch" (emitted from a closed country-scope block).
    stack = [[False, False, "", 0, [], []]]

    for i, line in enumerate(lines):
        code = _code_for_depth(line)
        if not code.strip():
            continue
        last_end = 0
        for m in _RE_CE_TOKEN.finditer(code):
            tok = m.group(0)
            preceding = code[last_end : m.start()]
            stack[-1][5].append(preceding)
            if tok == "{":
                is_not = bool(_RE_NOT_EQ.search(preceding))
                is_or = bool(_RE_OR_EQ.search(preceding))
                opens_tag = ""
                if not is_not and not is_or:
                    sm = _RE_CE_SCOPE_TAG.search(preceding)
                    if sm and sm.group(1) not in _CE_LOGIC_TAGS:
                        opens_tag = sm.group(1) or ""
                stack.append([is_or, is_not, opens_tag, i + 1, [], []])
            elif tok == "}":
                if len(stack) > 1:
                    popped = stack.pop()
                    (
                        popped_or,
                        popped_not,
                        popped_tag,
                        pop_line,
                        popped_children,
                        popped_texts,
                    ) = popped
                    block_text = " ".join(popped_texts)
                    stack[-1][5].append("{ " + block_text + " }")
                    parent = stack[-1][4]
                    if popped_or:
                        pass
                    elif popped_not:
                        ce_children = [
                            (cl, ctag)
                            for cl, ck, ctag in popped_children
                            if ck == "country_exists"
                        ]
                        # Direct statements = assignments/comparisons left after
                        # blanking child blocks, plus the country_exists tokens
                        # (consumed, never in text). A NOT with several is a
                        # NAND: no child is individually negated.
                        direct = _ce_blank_nested(block_text, _RE_CE_BRACE_BLOCK)
                        n_stmts = len(_RE_CE_STMT.findall(direct)) + len(ce_children)
                        if n_stmts <= 1:
                            for cl, ctag in ce_children:
                                parent.append((cl, "not_country_exists", ctag))
                    elif popped_tag:
                        scan = _ce_blank_nested(block_text, _RE_CE_VAR_BLOCK)
                        keys = _RE_CE_TRIGGER_KEY.findall(scan)
                        if keys and not all(k in _CE_DEAD_TAG_SAFE for k in keys):
                            parent.append((pop_line, "scope_switch", popped_tag))
                    else:
                        not_exists = [
                            (cl, ctag)
                            for cl, ck, ctag in popped_children
                            if ck == "not_country_exists"
                        ]
                        scopes = {
                            ctag
                            for _cl, ck, ctag in popped_children
                            if ck == "scope_switch"
                        }
                        for n_line, n_tag in not_exists:
                            if n_tag in scopes:
                                issues.append(
                                    (
                                        n_line,
                                        f"AND block has NOT = {{ "
                                        f"country_exists = {n_tag} }} alongside"
                                        f" a {n_tag} = {{ ... }} scope switch --"
                                        f" always false (the scope fails when"
                                        f" {n_tag} is absent, the NOT is only"
                                        f" true then); use OR = {{ ... }} to"
                                        f" match either condition",
                                    )
                                )
            else:
                tag = m.group(1)
                stack[-1][4].append((i + 1, "country_exists", tag))
            last_end = m.end()
        stack[-1][5].append(code[last_end:])

    return issues


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
        if _RE_TOPLEVEL_WORD.match(lines[i]) and "{" in code:
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
                        if in_allowed:
                            allowed_depth += dbl_code.count("{") - dbl_code.count("}")
                            if _RE_DECISION_ALLOWED_DYNAMIC.search(dbl_code):
                                trigger = _RE_DECISION_ALLOWED_DYNAMIC.search(
                                    dbl_code
                                ).group()
                                if trigger not in ("original_tag", "tag"):
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
    # Each frame: [is_if, guarded, is_gate]. A has_dlc token marks the nearest
    # enclosing if-frame guarded so an inline `if = { limit = { has_dlc } }` guard
    # stays scoped to that if and cannot leak to a sibling embargo in the parent
    # frame. With no enclosing if, a has_dlc inside a gate (trigger/available/
    # visible/allowed) instead marks that gate's PARENT, since the gate covers the
    # whole enclosing object and every sibling effect in it.
    stack = []

    for i, line in enumerate(lines):
        # Blank quoted strings so a stray { or } in a log/loc string can't desync
        # the if/guard stack; keep the BBA guard literal so its token still matches.
        code = _RE_QUOTED_STRING.sub(
            lambda mm: mm.group(0) if mm.group(0) == '"By Blood Alone"' else '""',
            strip_inline_comment(line),
        )
        last_end = 0
        for m in _RE_DLC_TOKEN.finditer(code):
            tok = m.group(0)
            if tok == "{":
                preceding = code[last_end : m.start()]
                stack.append(
                    [
                        bool(_RE_IF_BEFORE_BRACE.search(preceding)),
                        False,
                        bool(_RE_GATE_BEFORE_BRACE.search(preceding)),
                    ]
                )
            elif tok == "}":
                if stack:
                    stack.pop()
            elif tok.startswith("has_dlc"):
                target = next((f for f in reversed(stack) if f[0]), None)
                if target is not None:
                    target[1] = True
                else:
                    gate_idx = next(
                        (idx for idx in range(len(stack) - 1, -1, -1) if stack[idx][2]),
                        None,
                    )
                    if gate_idx is not None:
                        stack[gate_idx - 1 if gate_idx > 0 else 0][1] = True
                    elif stack:
                        stack[-1][1] = True
            else:
                if not any(f[1] for f in stack):
                    issues.append(
                        (
                            i + 1,
                            f'{tok} without has_dlc = "By Blood Alone" guard'
                            f' -- wrap in if = {{ limit = {{ has_dlc = "By Blood Alone" }} }}',
                        )
                    )
            last_end = m.end()

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
                if (
                    divisor not in guarded_vars
                    and divisor not in _NONZERO_GLOBAL_DIVISORS
                ):
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


def _check_is_x_nation_runtime(lines, filepath=""):
    """Flag is_X_nation triggers in runtime contexts (available, visible, effect).

    The is_X_nation scripted triggers iterate over tag lists and are relatively
    expensive. In runtime contexts (available, visible, effect blocks, limit clauses),
    use the pre-computed has_country_flag = X_flag instead for O(1) lookup.

    Safe to use in allowed = { } which is evaluated once at game start, in
    achievements' possible = { } (effectively an allowed -- evaluated once), and
    in common/scripted_triggers/ where these triggers are defined and compose each
    other (e.g. is_horn_of_africa_nation references is_somali_nation) -- the cost
    is realized at the call site, not the definition.
    """
    if "common/scripted_triggers" in filepath.replace("\\", "/"):
        return []
    issues = []
    in_allowed = False
    allowed_depth = 0
    brace_depth = 0

    for i, line in enumerate(lines, 1):
        code = strip_inline_comment(line)

        opens = code.count("{")
        closes = code.count("}")

        # Check for allowed / possible block start (possible = game-start gate too)
        if (
            _RE_ALLOWED_OPEN_WB.search(code) and "allowed_civil_war" not in code
        ) or _RE_POSSIBLE_OPEN_WB.search(code):
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
                # Skip the flag-definition site: an `if = { limit = { is_X_nation = yes } ... }`
                # whose body sets the matching X_nation_flag. That is the trigger->flag
                # conversion this check recommends; the O(n) trigger is unavoidable there.
                window = " ".join(lines[i - 1 : i + 2])
                if re.search(
                    r"set_country_flag\s*=\s*(?:\{\s*flag\s*=\s*)?"
                    + re.escape(flag_name)
                    + r"\b",
                    window,
                ):
                    continue
                issues.append(
                    (
                        i,
                        f"is_X_nation in runtime context -- use has_country_flag = {flag_name} for O(1) lookup (allowed = {{ }} is OK for game-start checks)",
                    )
                )

    return issues


def _match_member_ideas(text):
    """Return [(idea, array)] for each array-backed membership idea *text* tests.

    Returns [] (suppressed) when:
      - has_idea is inside a NOT block (filtering OUT members, not iterating them)
      - has_idea is nested inside an OVERLORD or other sub-scope check
      - The text contains an OR with non-array-backed ideas (too complex to convert)
    """
    hits = []
    for idea, array in _MEMBER_IDEA_TO_ARRAY.items():
        re_has, re_not, re_scope = _MEMBER_IDEA_PATTERNS[idea]
        if not re_has.search(text):
            continue
        if re_not.search(text):
            continue
        if re_scope.search(text):
            continue
        hits.append((idea, array))
    if hits:
        or_match = _RE_OR_CONTENT.search(text)
        if or_match:
            other_ideas = _RE_HAS_IDEA.findall(or_match.group(1))
            if any(x not in _MEMBER_IDEA_TO_ARRAY for x in other_ideas):
                return []
    return hits


_RE_ON_HOOK_OPEN = re.compile(r"\bon_(add|remove)\s*=\s*\{")
_RE_ADD_TO_GLOBAL_ARRAY = re.compile(
    r"add_to_array\s*=\s*\{\s*(?:array\s*=\s*)?(global\.\w+)"
)
_RE_REMOVE_FROM_GLOBAL_ARRAY = re.compile(
    r"remove_from_array\s*=\s*\{\s*(?:array\s*=\s*)?(global\.\w+)"
)


def _check_on_add_array_symmetry(lines):
    """Flag on_add blocks that add to a global array the sibling on_remove
    never removes from.

    An idea granted then removed leaves a stale array entry (the Arab League
    membership bug class). Siblings share the same enclosing block, so hooks
    are grouped by the innermost open block at their line.
    """
    issues = []
    stack = []
    groups = {}
    for i, raw in enumerate(lines):
        code = strip_inline_comment(raw)
        m = _RE_ON_HOOK_OPEN.search(code)
        if m:
            parent = stack[-1] if stack else -1
            block, _ = _get_block(lines, i)
            text = " ".join(strip_inline_comment(b) for b in block)
            entry = groups.setdefault(parent, {"adds": [], "removes": set()})
            if m.group(1) == "add":
                for arr in _RE_ADD_TO_GLOBAL_ARRAY.findall(text):
                    entry["adds"].append((arr, i + 1))
            else:
                entry["removes"].update(_RE_REMOVE_FROM_GLOBAL_ARRAY.findall(text))
        for ch in code:
            if ch == "{":
                stack.append(i)
            elif ch == "}" and stack:
                stack.pop()
    for entry in groups.values():
        for arr, ln in entry["adds"]:
            if arr not in entry["removes"]:
                issues.append(
                    (
                        ln,
                        f"on_add adds to {arr} but the sibling on_remove never"
                        f" removes from it -- removing the idea leaves a stale"
                        f" array entry",
                    )
                )
    return issues


def _check_every_country_member_array(lines):
    """Flag every_country/every_other_country over a membership idea when a
    pre-built array exists.

    The known member ideas (see _MEMBER_IDEA_TO_ARRAY) all have corresponding
    global arrays. for_each_scope_loop over the array iterates ~30 members
    instead of 200+ tags. See simplification-patterns.md § "Convert
    every_country Over Bloc Membership".
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        open_match = _RE_EVERY_COUNTRY_OPEN.match(lines[i])
        if open_match:
            open_line = i
            block, next_i = _get_block(lines, i)
            # Display-only loops: for_each_scope_loop's tooltip param collapses
            # the per-country output these loops exist to render.
            if any(
                "display_individual_scopes" in strip_inline_comment(bl) for bl in block
            ):
                i = next_i
                continue
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

            hits = _match_member_ideas(limit_text)
            if hits:
                ideas = ", ".join(idea for idea, _ in hits)
                arrays = sorted({array for _, array in hits})
                token = open_match.group(1)
                guard = (
                    " and keep the self-exclusion as if = { limit = { NOT = { tag = ROOT } } }"
                    if token == "every_other_country"
                    else ""
                )
                if len(arrays) == 1:
                    advice = (
                        f"use for_each_scope_loop = {{ array = {arrays[0]} }}"
                        f" instead (narrower iteration, better performance){guard}"
                    )
                else:
                    advice = (
                        f"split into one for_each_scope_loop per array"
                        f" ({', '.join(arrays)}) with mutual-exclusion guards"
                        f" (see simplification-patterns.md){guard}"
                    )
                issues.append(
                    (open_line + 1, f"{token} with has_idea = {ideas} -- {advice}")
                )
            i = next_i
        else:
            i += 1
    return issues


def _check_any_country_member_array(lines):
    """Flag any_country/any_other_country testing a membership idea when a
    pre-built array exists.

    any_of_scopes over the bloc's global array checks ~30 members instead of
    all 200+ tags. Trigger aggregations do NOT auto-skip dead array entries
    (annexed tags linger), so negated / all-quantified forms need an
    OR = { <condition> exists = no } guard.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        open_match = _RE_ANY_COUNTRY_OPEN.match(lines[i])
        if open_match:
            open_line = i
            block, next_i = _get_block(lines, i)
            body = " ".join(strip_inline_comment(bl).strip() for bl in block[:30])
            hits = _match_member_ideas(body)
            if hits:
                ideas = ", ".join(idea for idea, _ in hits)
                arrays = sorted({array for _, array in hits})
                if len(arrays) == 1:
                    advice = f"use any_of_scopes = {{ array = {arrays[0]} }} instead"
                else:
                    advice = (
                        f"use one any_of_scopes per array"
                        f" ({', '.join(arrays)}) inside an OR instead"
                    )
                issues.append(
                    (
                        open_line + 1,
                        f"{open_match.group(1)} with has_idea = {ideas} -- {advice}"
                        f" (checks only members; when negating or using"
                        f" all_of_scopes, add OR = {{ ... exists = no }} --"
                        f" stale array entries do not auto-skip in triggers)",
                    )
                )
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


def _check_check_expr_bad_operand(lines):
    """Flag check_expr operands chained with a raw >/< comparator symbol
    (a check_variable-style leftover) instead of block form or a bare scalar."""
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        if _RE_CHECK_EXPR_OPEN.search(strip_inline_comment(lines[i])):
            start = i
            block, i = _get_block(lines, start)
            for k, bl in enumerate(block):
                m = _RE_CHECK_EXPR_BAD_OPERAND.search(strip_inline_comment(bl))
                if m:
                    op, sym = m.group(1), m.group(2)
                    issues.append(
                        (
                            start + k + 1,
                            f"check_expr operand '{op}' chained with a raw '{sym}' -- "
                            f"use block form {op} = {{ value = X }} or a bare scalar "
                            f"({op} = X), not '{op} {sym} X'",
                        )
                    )
        else:
            i += 1
    return issues


def _check_every_owned_controlled_state(lines):
    """Flag every_owned_controlled_state, which does not exist -- use every_controlled_state."""
    issues = []
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        code_part = strip_inline_comment(line) if "#" in line else line
        if _RE_EVERY_OWNED_CONTROLLED_STATE.search(code_part):
            issues.append(
                (
                    line_num,
                    "every_owned_controlled_state does not exist -- use every_controlled_state",
                )
            )
    return issues


def _add_to_faction_value_ok(value):
    """True when value is a country add_to_faction can take: a 3-letter tag, a
    country scope keyword or dotted scope chain (PREV.PREV), a var:/event_target:
    ref, or a dynamic [square-bracket] token. A faction name (BRICS, lowercase
    ids) is none of these and is flagged.
    """
    return (
        (len(value) == 3 and _RE_TAG_SCOPE.match(value) is not None)
        or value in _ADD_TO_FACTION_SCOPE_KEYWORDS
        or value.startswith(("var:", "event_target:"))
        or "." in value
        or "[" in value
    )


def _check_add_to_faction_country(lines):
    """Flag add_to_faction with a non-country argument (a faction name).

    add_to_faction adds the ARGUMENT country to the current scope's faction, so
    it takes a country tag or scope ref (ROOT/FROM/PREV/THIS/var:), never a
    faction id -- add_to_faction = BRICS silently does nothing since BRICS is a
    faction, not a country. To add a member to a bloc, scope to a faction member
    and pass the new member's tag.
    """
    issues = []
    for line_num, line in enumerate(lines, 1):
        if "add_to_faction" not in line or line.strip().startswith("#"):
            continue
        code_part = _code_for_depth(line)
        for m in _RE_ADD_TO_FACTION.finditer(code_part):
            value = m.group(1)
            if not _add_to_faction_value_ok(value):
                issues.append(
                    (
                        line_num,
                        f"add_to_faction = {value} is not a country -- add_to_faction "
                        f"takes a country tag or scope (ROOT/FROM/PREV/THIS/var:), not a "
                        f"faction name; it adds that country to the current scope's faction",
                    )
                )
    return issues


def _check_create_faction_deprecated(lines):
    """Flag create_faction = X, deprecated in MD in favor of
    create_faction_from_template for DLC compatibility.
    """
    issues = []
    for line_num, line in enumerate(lines, 1):
        if "create_faction" not in line or line.strip().startswith("#"):
            continue
        code_part = _code_for_depth(line)
        if _RE_CREATE_FACTION_DEPRECATED.search(code_part):
            issues.append(
                (
                    line_num,
                    "create_faction is deprecated -- use create_faction_from_template "
                    "= TEMPLATE instead for DLC compatibility",
                )
            )
    return issues


def _check_random_select_amount_literal(lines):
    """Flag random_select_amount set to anything but an integer literal."""
    issues = []
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        code_part = strip_inline_comment(line) if "#" in line else line
        m = _RE_RANDOM_SELECT_AMOUNT.search(code_part)
        if m and not _RE_BARE_INT.match(m.group(1)):
            issues.append(
                (
                    line_num,
                    f"random_select_amount = {m.group(1)} is not an integer literal -- "
                    f"random_select_amount requires a literal int",
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


def _find_focus_log_mismatches(lines):
    """Return (line_idx, tok_start, tok_end, focus_id, bad_token) for each
    log = "...Focus <token>" line inside a focus/shared_focus/joint_focus block
    where token doesn't match the block's own id.

    Suppressed when the mismatched token is completed/unlocked elsewhere in the
    same block via complete_national_focus / unlock_national_focus -- that's a
    focus intentionally completing or unlocking a sibling and logging the
    sibling's id, not a copy-paste bug. Shared by _check_focus_log_id and
    fix_log_ids.py so both use the same detection.
    """
    results = []
    i = 0
    n = len(lines)
    while i < n:
        if _RE_FOCUS_ANY_BLOCK_OPEN.match(lines[i]):
            start = i
            block, i = _get_block(lines, start)
            code_lines = [strip_inline_comment(bl) for bl in block]
            text = "".join(code_lines)
            id_match = _RE_FOCUS_ID_IN_BLOCK.search(text)
            if not id_match:
                continue
            focus_id = id_match.group(1)
            suppressed = set(_RE_COMPLETE_FOCUS.findall(text)) | set(
                _RE_UNLOCK_FOCUS.findall(text)
            )
            for k, cl in enumerate(code_lines):
                m = _RE_LOG_FOCUS_TOKEN.search(cl)
                if m:
                    token = m.group(1)
                    if token != focus_id and token not in suppressed:
                        results.append(
                            (start + k, m.start(1), m.end(1), focus_id, token)
                        )
        else:
            i += 1
    return results


def _check_focus_log_id(lines):
    """Flag log = "...Focus <token>" lines whose token doesn't match the
    enclosing focus/shared_focus/joint_focus block's own id -- almost always a
    copy-paste leftover from duplicating a neighboring focus.
    """
    issues = []
    for line_idx, _s, _e, focus_id, token in _find_focus_log_mismatches(lines):
        issues.append(
            (
                line_idx + 1,
                f"log references Focus {token}, but the enclosing focus is "
                f"{focus_id} -- likely copy-paste; fix the log id",
            )
        )
    return issues


def _decision_log_token_span(line):
    """Return (token, start, end) for the id referenced by a
    `log = "...Decision ..."` line, skipping leading filler words
    (_DECISION_LOG_FILLER_WORDS), or None if the line has no such log
    statement (or nothing substantive follows the filler words).
    """
    marker = _RE_LOG_DECISION_MARKER.search(line)
    if not marker:
        return None
    pos = marker.end()
    while True:
        m = _RE_NEXT_WORD.match(line, pos)
        if not m:
            return None
        token = m.group(1)
        if token.lower() in _DECISION_LOG_FILLER_WORDS:
            pos = m.end()
            continue
        return token, m.start(1), m.end(1)


def _find_decision_log_mismatches(lines):
    """Return (line_idx, tok_start, tok_end, decision_id, bad_token) for each
    log = "...Decision ..." line inside a decision block whose referenced id
    doesn't match the enclosing decision's own key.

    Enclosing decision = the block key at depth 1 (the category is depth 0),
    same category/decision traversal as _check_decision_allowed_dynamic.
    Shared by _check_decision_log_id and fix_log_ids.py.
    """
    results = []
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
                    dec_id_match = _RE_BLOCK_ID.match(cat_block[k])
                    dec_id = dec_id_match.group(1) if dec_id_match else None
                    if dec_id:
                        for p, dbl in enumerate(dec_block):
                            dbl_code = strip_inline_comment(dbl)
                            token_span = _decision_log_token_span(dbl_code)
                            if token_span:
                                token, tstart, tend = token_span
                                if token != dec_id:
                                    results.append(
                                        (
                                            cat_start + k + p,
                                            tstart,
                                            tend,
                                            dec_id,
                                            token,
                                        )
                                    )
                    k = next_k
                else:
                    k += 1
        else:
            i += 1
    return results


def _check_decision_log_id(lines):
    """Flag log = "...Decision ..." lines whose referenced id doesn't match
    the enclosing decision (tolerating remove/complete/completed/timeout/
    cancel/effect filler words: "Decision remove X", "Decision cancel effect
    X") -- almost always a copy-paste leftover from duplicating a neighboring
    decision.
    """
    issues = []
    for line_idx, _s, _e, dec_id, token in _find_decision_log_mismatches(lines):
        issues.append(
            (
                line_idx + 1,
                f"log references Decision {token}, but the enclosing decision "
                f"is {dec_id} -- likely copy-paste; fix the log id",
            )
        )
    return issues


def _check_event_log_id(lines):
    """Flag log = "...Event <token>..." lines inside a country_event /
    news_event / operative_leader_event / unit_leader_event block where token
    matches neither the block's own id nor the enclosing option's own declared
    `name = ` (its real identity), or -- for the bare-id form -- where a
    separate "Option <x>" phrase names a letter that doesn't match the suffix
    of that same `name = `.

    Ground-truthed against the option's own `name = ` line rather than a
    computed sequential letter: option lettering isn't always contiguous
    (e.g. singapore.101 skips from .c straight to .e), so a position-based
    a/b/c/... expectation would false-positive on those.

    Only top-level event definitions count (column 0); a nested
    `country_event = { id = X days = N }` is a scheduling effect call, not a
    definition, and is skipped since it never starts at column 0.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        if _RE_EVENT_DEF_OPEN.match(lines[i]):
            start = i
            block, i = _get_block(lines, start)
            event_id = None
            for bl in block:
                m = _RE_EVENT_ID_IN_BLOCK.match(strip_inline_comment(bl))
                if m:
                    event_id = m.group(1)
                    break
            if not event_id:
                continue
            j = 1
            block_n = len(block)
            while j < block_n - 1:
                bl_code = strip_inline_comment(block[j])
                if _RE_OPTION_BLOCK_OPEN.search(bl_code):
                    opt_block, next_j = _get_block(block, j)
                    own_name = None
                    for obl in opt_block:
                        nm = _RE_OPTION_NAME_IN_BLOCK.match(strip_inline_comment(obl))
                        if nm:
                            own_name = nm.group(1)
                            break
                    own_suffix = None
                    if own_name and own_name.startswith(event_id + "."):
                        own_suffix = own_name[len(event_id) + 1 :]
                    for p, obl in enumerate(opt_block):
                        obl_code = strip_inline_comment(obl)
                        m = _RE_LOG_EVENT_TOKEN.search(obl_code)
                        if not m:
                            continue
                        token = m.group(1)
                        if own_name and token == own_name:
                            continue
                        if token == event_id:
                            om = _RE_LOG_EVENT_OPTION_SUFFIX.match(obl_code, m.end())
                            if (
                                om
                                and own_suffix
                                and om.group(1).lower() != own_suffix.lower()
                            ):
                                issues.append(
                                    (
                                        start + j + p + 1,
                                        f"log says Option {om.group(1)} but "
                                        f"this option's own name is "
                                        f"{own_name} -- fix the option "
                                        f"letter",
                                    )
                                )
                            continue
                        if own_name:
                            issues.append(
                                (
                                    start + j + p + 1,
                                    f"log references Event {token}, but this "
                                    f"option's own name is {own_name} -- "
                                    f"likely copy-paste; fix the log id",
                                )
                            )
                    j = next_j
                else:
                    j += 1
        else:
            i += 1
    return issues


def _check_hidden_trigger_in_ctt(lines):
    """Flag hidden_trigger = { } at relative depth 1 inside
    custom_trigger_tooltip.

    Everything inside custom_trigger_tooltip besides the tooltip line is
    already the hidden trigger the tooltip describes -- wrapping it in
    hidden_trigger adds a redundant nesting level with no effect.
    """
    issues = []
    i = 0
    n = len(lines)
    while i < n:
        code = _code_for_depth(lines[i])
        if _RE_CUSTOM_TRIGGER_TOOLTIP_OPEN.search(code):
            depth = code.count("{") - code.count("}")
            j = i + 1
            while depth > 0 and j < n:
                c2 = _code_for_depth(lines[j])
                if depth == 1 and _RE_HIDDEN_TRIGGER_OPEN.search(c2):
                    issues.append(
                        (
                            j + 1,
                            "hidden_trigger = { } directly inside "
                            "custom_trigger_tooltip is redundant -- unwrap its "
                            "children to the tooltip's own depth",
                        )
                    )
                depth += c2.count("{") - c2.count("}")
                j += 1
            i = j
        else:
            i += 1
    return issues


class _Node:
    """One `key = value` or `key = { ... }` statement, with its 1-based line."""

    __slots__ = ("key", "op", "value", "line", "children")

    def __init__(self, key, op, value, line, children):
        self.key = key
        self.op = op
        self.value = value
        self.line = line
        self.children = children


def _parse_script_nodes(tokens, i):
    """Recursive-descent parse of (token, line) pairs into a _Node tree.
    Returns (children, index_after_the_closing_brace).
    """
    children = []
    n = len(tokens)
    while i < n:
        tok, line = tokens[i]
        if tok == "}":
            return children, i + 1
        if i + 2 < n and tokens[i + 1][0] in _NODE_OPERATORS:
            op = tokens[i + 1][0]
            if tokens[i + 2][0] == "{":
                sub, i = _parse_script_nodes(tokens, i + 3)
                children.append(_Node(tok, op, None, line, sub))
            else:
                children.append(_Node(tok, op, tokens[i + 2][0], line, []))
                i += 3
            continue
        i += 1
    return children, i


def _parse_script_tree(lines):
    tokens = [
        (m.group(0), line_num)
        for line_num, line in enumerate(lines, 1)
        for m in _RE_SCRIPT_NODE.finditer(_code_for_depth(line))
    ]
    return _parse_script_nodes(tokens, 0)[0]


def _first_child(node, key):
    for child in node.children:
        if child.key == key:
            return child
    return None


def _is_b_guard(node):
    """NOT = { check_variable = { b = N } } -- the cascade guard every tier past the
    first carries, not a discriminating condition."""
    if node.key != "NOT" or len(node.children) != 1:
        return False
    check = node.children[0]
    return (
        check.key == "check_variable"
        and len(check.children) == 1
        and check.children[0].key == "b"
    )


def _leader_tier_check(limit):
    """(counter_name, tier_number) for a limit's `check_variable = { X_leader = N }`."""
    for child in limit.children:
        if child.key != "check_variable" or len(child.children) != 1:
            continue
        var = child.children[0]
        if (
            var.key.endswith(_LEADER_COUNTER_SUFFIX)
            and var.op == "="
            and var.value
            and _RE_BARE_INT.match(var.value)
        ):
            return var.key, int(var.value)
    return None


def _tier_discriminates(limit, counter):
    """True when a tier gates on anything beyond its counter check and the b-guard.

    Duplicate tier numbers are legitimate when a second condition picks between them
    (ERI splits on an ETH flag, ISR on party flags, CZE on a date), so a discriminated
    tier is never reported as a duplicate.
    """
    for child in limit.children:
        if (
            child.key == "check_variable"
            and len(child.children) == 1
            and child.children[0].key == counter
        ):
            continue
        if _is_b_guard(child):
            continue
        return True
    return False


def _branch_flag(node):
    """The set_<ideology> flag an if/else_if branch gates on, or None."""
    limit = _first_child(node, "limit")
    if limit is None:
        return None
    for child in limit.children:
        if (
            child.key == "has_country_flag"
            and child.value
            and child.value.startswith(_SET_IDEOLOGY_PREFIX)
        ):
            return child.value
    return None


def _branch_discriminates(node, flag):
    limit = _first_child(node, "limit")
    return any(
        not (child.key == "has_country_flag" and child.value == flag)
        for child in limit.children
    )


def _collect_leader_tiers(node, guarded, tiers):
    """Gather the tier if/else_if blocks under one ideology branch.

    Tiers may sit directly under the branch or inside a nested container (JAP wraps
    them in date blocks) -- a container's own limit discriminates every tier below it,
    so the same tier number appearing under two containers is not a duplicate.
    """
    for child in node.children:
        if child.key not in _TIER_KEYWORDS or _branch_flag(child):
            continue
        limit = _first_child(child, "limit")
        if limit is None:
            continue
        tier = _leader_tier_check(limit)
        if tier:
            counter, number = tier
            tiers.append(
                (child, counter, number, guarded or _tier_discriminates(limit, counter))
            )
        else:
            _collect_leader_tiers(child, True, tiers)


def _counter_delta(node, effect_key):
    """The variable leaf of a `<effect_key> = { <var> = N }` directly under node."""
    for child in node.children:
        if child.key != effect_key or len(child.children) != 1:
            continue
        var = child.children[0]
        if var.value and _RE_BARE_INT.match(var.value):
            return var
    return None


def _do_not_retire_subtract(tier):
    for child in tier.children:
        if child.key not in _TIER_KEYWORDS:
            continue
        limit = _first_child(child, "limit")
        if limit is None:
            continue
        flag = _first_child(limit, "has_country_flag")
        if flag is None or flag.value != _DO_NOT_RETIRE_FLAG:
            continue
        return _counter_delta(child, "subtract_from_variable")
    return None


def _check_leader_tier(tier, counter, number, issues):
    """Increment and do_not_retire rollback for one tier."""
    add = _counter_delta(tier, "add_to_variable")
    step = None
    if add and add.key == counter:
        step = int(add.value)
        if step != 1:
            issues.append(
                (
                    add.line,
                    f"tier {counter} = {number} advances the counter by {step} -- every "
                    f"tier must advance it by exactly 1 (the tier index is not the step); "
                    f"{step} leaves later leaders unreachable",
                )
            )

    subtract = _do_not_retire_subtract(tier)
    if subtract is None:
        return
    if subtract.key != counter:
        issues.append(
            (
                subtract.line,
                f"do_not_retire subtracts from {subtract.key}, but this tier advances "
                f"{counter} -- the leader retires anyway and {subtract.key} is driven "
                f"below its own tier 0",
            )
        )
    elif step is not None and int(subtract.value) != step:
        issues.append(
            (
                subtract.line,
                f"do_not_retire subtracts {subtract.value} from {counter} but the tier "
                f"added {step} -- they must cancel out or do_not_retire does not keep "
                f"the leader",
            )
        )


def _check_leader_branch(branch, flag, tiers, counter_owners, issues):
    groups = {}
    for tier, counter, number, discriminated in tiers:
        groups.setdefault(counter, []).append((tier, number, discriminated))

    own_counter = flag[len(_SET_IDEOLOGY_PREFIX) :] + _LEADER_COUNTER_SUFFIX
    for counter, entries in groups.items():
        # An off-name counter used nowhere else is just an odd name (socalism_leader);
        # one that another ideology also drives, or that sits next to this branch's own
        # counter, is a copy-paste -- the two rotations then share one index.
        borrowed = counter != own_counter and (
            own_counter in groups or len(counter_owners[counter]) > 1
        )
        if borrowed:
            issues.append(
                (
                    entries[0][0].line,
                    f"tiers under {flag} count with {counter}, not {own_counter} -- the "
                    f"two ideologies share one counter, so each election skips leaders in "
                    f"the other's rotation",
                )
            )

        increments = False
        plain_tiers = {}
        for tier, number, discriminated in entries:
            add = _counter_delta(tier, "add_to_variable")
            increments = increments or (add is not None and add.key == counter)
            _check_leader_tier(tier, counter, number, issues)
            if discriminated:
                continue
            if number in plain_tiers:
                issues.append(
                    (
                        tier.line,
                        f"duplicate tier {counter} = {number} (already handled at line "
                        f"{plain_tiers[number]}) with no further condition to tell the two "
                        f"apart -- one of the leaders is unreachable",
                    )
                )
            else:
                plain_tiers[number] = tier.line

        # A lookup-table branch sets its counter elsewhere and never advances it, so its
        # tier numbers carry no ordering to check. A borrowed counter is numbered against
        # the branch it was copied from.
        if not increments or borrowed:
            continue
        numbers = sorted({number for _t, number, _d in entries})
        missing = [n for n in range(numbers[-1]) if n not in numbers]
        if missing:
            gap = missing[0]
            stranded = next(tier for tier, number, _d in entries if number > gap)
            issues.append(
                (
                    stranded.line,
                    f"no tier for {counter} = {gap} under {flag} -- the counter never "
                    f"reaches {gap + 1}, so this leader and every later one can never fire",
                )
            )


def _collect_leader_branches(container, branches, issues):
    """Gather the ideology branches under a set_leader_TAG body, flagging any that a
    same-flag branch earlier in its if/else_if chain already shadows."""
    plain_branches = {}
    for child in container.children:
        if not child.children:
            continue
        if child.key == "if":
            plain_branches = {}
        flag = _branch_flag(child) if child.key in _TIER_KEYWORDS else None
        if flag is None:
            _collect_leader_branches(child, branches, issues)
            continue
        if flag in plain_branches:
            issues.append(
                (
                    child.line,
                    f"duplicate {flag} branch (already handled at line "
                    f"{plain_branches[flag]}) -- if/else_if stops at the first match, so "
                    f"this branch never runs",
                )
            )
        elif not _branch_discriminates(child, flag):
            plain_branches[flag] = child.line
        branches.append((child, flag))


def _check_impossible_b_guards(node, issues):
    for child in node.children:
        if _is_b_guard(child) and child.children[0].children[0].value == "0":
            issues.append(
                (
                    child.line,
                    "NOT = { check_variable = { b = 0 } } is always false -- b reads 0 "
                    "when unset, so this tier can never fire (the guard counts from 1)",
                )
            )
        _check_impossible_b_guards(child, issues)


def _check_leader_rotation(lines):
    """Flag malformed leader rotations in common/scripted_effects/*_political_leaders.txt.

    set_leader kills the country leader before dispatching to set_leader_TAG, so a tier
    that can never fire hands the country a randomly generated leader instead of the
    authored one.
    """
    issues = []
    for root in _parse_script_tree(lines):
        if not root.key.startswith(_LEADER_EFFECT_PREFIX):
            continue
        branches = []
        _collect_leader_branches(root, branches, issues)

        branch_tiers = []
        counter_owners = {}
        for branch, flag in branches:
            tiers = []
            _collect_leader_tiers(branch, False, tiers)
            branch_tiers.append((branch, flag, tiers))
            for _tier, counter, _number, _discriminated in tiers:
                counter_owners.setdefault(counter, set()).add(flag)

        for branch, flag, tiers in branch_tiers:
            _check_leader_branch(branch, flag, tiers, counter_owners, issues)
        _check_impossible_b_guards(root, issues)
    return sorted(issues)


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
    normalized_filepath = filepath.replace("\\", "/")
    is_common_or_events_file = (
        "common/" in normalized_filepath or "events/" in normalized_filepath
    )
    is_event_file = "events/" in normalized_filepath
    is_political_leaders_file = normalized_filepath.endswith("_political_leaders.txt")

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
            depth_code = _code_for_depth(line)
            brace_depth += depth_code.count("{") - depth_code.count("}")

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

        div_match = _RE_DIVISION.search(_RE_QUOTED_STRING.sub('""', code_part))
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
    issues.extend(_check_country_exists_scope_contradiction(lines))

    if is_focus_file:
        issues.extend(_check_focus_available_always_no(lines))
        issues.extend(_check_focus_missing_war_hint(lines))
        issues.extend(_check_focus_log_id(lines))
    if is_decision_file:
        issues.extend(_check_decision_available_always_no(lines))
        issues.extend(_check_decision_allowed_dynamic(lines))
        issues.extend(_check_decision_log_id(lines))
    if is_event_file:
        issues.extend(_check_event_log_id(lines))
    if is_political_leaders_file:
        issues.extend(_check_leader_rotation(lines))

    issues.extend(_check_hidden_trigger_in_ctt(lines))
    issues.extend(_check_consecutive_scope_blocks(lines))
    issues.extend(_check_embargo_dlc_guard(lines))
    issues.extend(_check_divide_variable_zero_guard(lines))
    issues.extend(_check_duplicate_add_to_variable(lines))
    issues.extend(_check_every_country_member_array(lines))
    issues.extend(_check_any_country_member_array(lines))
    issues.extend(_check_on_add_array_symmetry(lines))
    issues.extend(_check_empty_log_only_blocks(lines))
    issues.extend(_check_is_x_nation_runtime(lines, filepath))
    issues.extend(_check_influence_setter_scope(lines))
    issues.extend(_check_check_var_ge_le(lines))
    issues.extend(_check_add_to_faction_country(lines))
    issues.extend(_check_create_faction_deprecated(lines))
    issues.extend(_check_tautological_or(lines))
    issues.extend(_check_check_expr_bad_operand(lines))
    issues.extend(_check_random_select_amount_literal(lines))
    if is_common_or_events_file:
        issues.extend(_check_every_owned_controlled_state(lines))

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

    # The available=always-no and is_X_nation checks need completion refs and
    # real nation flags gathered from the whole tree (~2s). A full `all` run
    # always scans. A targeted run (pre-commit args, --files, staged/diff) skips
    # the scan only when none of its files can trigger those checks; scanning
    # otherwise, so a script-completed focus in an unstaged file is not
    # false-positived.
    global _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS, _REAL_NATION_FLAGS
    if _targeted_mode(args) and not _files_need_global_refs(files_list):
        _SCRIPT_COMPLETED_FOCUSES = set()
        _SCRIPT_COMPLETED_DECISIONS = set()
        _REAL_NATION_FLAGS = set()
        timings.append(("scan global refs (skipped)", 0.0))
    else:
        with Timer("scan global refs") as t:
            (
                _SCRIPT_COMPLETED_FOCUSES,
                _SCRIPT_COMPLETED_DECISIONS,
                _REAL_NATION_FLAGS,
            ) = _scan_global_refs(root_dir)
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
