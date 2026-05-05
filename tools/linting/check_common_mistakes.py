#!/usr/bin/env python3
"""
Check for common scripting mistakes in HOI4 mod files.

Detects mechanically-checkable rule violations from CLAUDE.md:
  - threat/has_war_support/has_stability comparisons >= 1 (all are 0.0-1.0 ranges)
  - allowed = { always = no } in country/hidden_ideas idea categories (default, hurts performance)
  - allowed = { tag = TAG } in country/hidden_ideas (breaks civil war split-offs; use original_tag)
  - allowed_civil_war = { always = no } in ideas (no effect, remove it)
  - cancel = { always = no } in ideas (checked hourly, never true)
  - ai_will_do root-level factor = N (should be base = N; factor only valid in modifier children)
  - Division instead of multiplication (/ 100 -> * 0.01)
  - Multiple values of a single-valued trigger (has_government, tag, original_tag,
    has_country_leader_ideology) at the same AND/NOT depth — always false (AND) or
    always true (NOT); caller meant OR = { ... } or separate NOT blocks.
  - Consecutive same-tag scope blocks that should be merged
  - send_embargo/break_embargo without has_dlc = "By Blood Alone" guard
  - divide_variable by a variable without a zero guard
  - Duplicate consecutive add_to_variable / add_to_temp_variable lines
  - every_country with has_idea = X_member when a pre-built array exists
  - is_in_faction = TAG (boolean trigger misused with a tag; should be is_in_faction_with)
  - has_trade_agreement_with (not a valid trigger; MD uses has_country_flag = trade_agreement@TAG)
  - Dynamic triggers inside decision allowed blocks (allowed is evaluated once at game start)
"""

import os
import re
import sys

# Compiled patterns — done once at import, not per file/line
_RE_THREAT = re.compile(r"(?<!\w)threat\s*([><]=?)\s*(\d+\.?\d*)")
_RE_WAR_SUPPORT = re.compile(r"(?<!\w)has_war_support\s*([><]=?)\s*(\d+\.?\d*)")
_RE_STABILITY = re.compile(r"(?<!\w)has_stability\s*([><]=?)\s*(\d+\.?\d*)")
_RE_ALLOWED_ALWAYS_NO = re.compile(r"allowed\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_ALLOWED_OPEN = re.compile(r"allowed\s*=\s*\{")
_RE_ALLOWED_TAG = re.compile(r"allowed\s*=\s*\{\s*tag\s*=\s*\w+\s*\}")
_RE_ALLOWED_CIVIL_WAR = re.compile(r"allowed_civil_war\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_CANCEL = re.compile(r"cancel\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_AI_WILL_DO = re.compile(r"ai_will_do\s*=\s*\{[^{]*?\bfactor\b\s*=")
_RE_DIVISION = re.compile(r"/\s*(100|1000|10|50|200|500)\b")
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

# Populated by main() before spawning Pool workers; inherited via fork on Unix.
_SCRIPT_COMPLETED_FOCUSES: set = set()
_SCRIPT_COMPLETED_DECISIONS: set = set()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cleanup_or import find_redundant_and_blocks, find_single_condition_or_blocks
from path_utils import clean_filepath
from shared_utils import (
    Timer,
    collect_files_by_mode,
    create_linting_parser,
    get_all_txt_files,
    get_git_diff_files,
    get_root_dir,
    print_timing_summary,
    run_with_pool,
)


def _scan_script_completed(root_dir):
    """Return (focus_ids, decision_ids) that are script-triggered across the codebase.

    Scans all .txt files for complete_national_focus = ID and activate_decision = ID
    so the checkers can skip flagging intentionally script-completed items.
    """
    focuses: set = set()
    decisions: set = set()
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
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for m in _RE_COMPLETE_FOCUS.finditer(content):
                        focuses.add(m.group(1))
                    for m in _RE_ACTIVATE_DECISION.finditer(content):
                        decisions.add(m.group(1))
                except Exception:
                    pass
    return focuses, decisions


def _get_block(lines, start):
    """Collect the complete brace-delimited block starting at lines[start].
    Returns (block_lines, next_idx) where next_idx is the first index after the block.
    Works on any list — passing a sub-list is safe.
    """
    code = lines[start].split("#")[0]
    depth = code.count("{") - code.count("}")
    j = start + 1
    while depth > 0 and j < len(lines):
        code = lines[j].split("#")[0]
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
        code = line.split("#")[0]
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


_RE_DAYS_MISSION_TIMEOUT = re.compile(r"\bdays_mission_timeout\s*=")

# --- New patterns for branch-cleanup checks ---
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
        code = lines[i].split("#")[0]
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
                bl_code = bl.split("#")[0]
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
        code = lines[i].split("#")[0]
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
                bl_code = bl.split("#")[0]
                if _RE_INDENTED_WORD.match(bl) and "{" in bl_code:
                    dec_block, next_k = _get_block(cat_block, k)
                    norm = _RE_WHITESPACE_COLLAPSE.sub(" ", "".join(dec_block))
                    if not _RE_DECISION_MARKER.search(norm):
                        k = next_k
                        continue
                    in_allowed = False
                    allowed_depth = 0
                    for p, dbl in enumerate(dec_block):
                        dbl_code = dbl.split("#")[0]
                        if (
                            not in_allowed
                            and re.search(r"\ballowed\s*=\s*\{", dbl_code)
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
        code = line.split("#")[0]
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
    # Track enclosing if-blocks and whether they contain the DLC check.
    # Stack entries: (brace_depth_at_open, has_dlc_guard)
    depth = 0
    dlc_guard_stack = []
    # We track whether ANY enclosing if-block has the DLC guard.

    for i, line in enumerate(lines):
        code = line.split("#")[0]
        stripped = code.strip()

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
      - Division inside an else block whose sibling if checks divisor = 0 or < threshold
    """
    issues = []
    # Track guarded variables per scope depth.
    # When we see a clamp or check_variable > 0 for a var, add it.
    # When we enter an else block whose if checked var = 0 or var < N, add it.
    # Pop when scope closes.
    guarded_vars = set()
    depth = 0
    depth_stack = []  # stack of (depth, set_of_vars_guarded_at_this_depth)
    # Track the last if-block's checked variable for else-block inference
    last_if_checked_var = None

    for i, line in enumerate(lines):
        code = line.split("#")[0]
        stripped = code.strip()

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
                bc = bl.split("#")[0]
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


def check_file(filepath):
    """Check a single file for common mistakes. Returns list of (filepath, line_num, message) tuples."""
    issues = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
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

    # Only track idea categories for idea files (country/hidden_ideas vs others)
    FLAGGED_IDEA_CATEGORIES = {"country", "hidden_ideas"}
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

        # Brace/category tracking is only needed for idea files
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

        code_part = line.split("#")[0] if "#" in line else line

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
            # Single-line forms
            if _RE_ALLOWED_ALWAYS_NO.search(code_part):
                issues.append(
                    (
                        line_num,
                        f"allowed = {{ always = no }} is the default for ideas in '{current_category}' -- remove it (hurts performance)",
                    )
                )
            elif _RE_ALLOWED_OPEN.search(code_part) and "}" not in code_part:
                # Opening of a multi-line allowed block — collect its contents
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
                            f"allowed = {{ always = no }} is the default for ideas in '{current_category}' -- remove it (hurts performance)",
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
                        "cancel = { always = no } is checked hourly and never true -- remove it",
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

    if is_focus_file:
        issues.extend(_check_focus_available_always_no(lines))
    if is_decision_file:
        issues.extend(_check_decision_available_always_no(lines))
        issues.extend(_check_decision_allowed_dynamic(lines))

    # Multi-line checks applicable to all script files
    issues.extend(_check_consecutive_scope_blocks(lines))
    issues.extend(_check_embargo_dlc_guard(lines))
    issues.extend(_check_divide_variable_zero_guard(lines))
    issues.extend(_check_duplicate_add_to_variable(lines))
    issues.extend(_check_every_country_member_array(lines))
    issues.extend(_check_empty_log_only_blocks(lines))

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

    # In staged/pre-commit mode, skip the expensive global scan (reads 6000+ files).
    # CI runs --mode all for full coverage.
    global _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS
    if getattr(args, "filenames", None) or args.mode == "staged":
        _SCRIPT_COMPLETED_FOCUSES = set()
        _SCRIPT_COMPLETED_DECISIONS = set()
    else:
        with Timer("scan script-completed refs") as t:
            _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS = (
                _scan_script_completed(root_dir)
            )
        timings.append(("scan script-completed refs", t.elapsed))

    print(f"Checking {len(files_list)} files for common mistakes...")

    with Timer("checking") as t:
        results = run_with_pool(check_file, files_list, args.workers)
    timings.append(("checking", t.elapsed))

    all_issues = [issue for file_issues in results for issue in file_issues]

    for filepath, line_num, message in sorted(all_issues):
        print(f"{clean_filepath(filepath)}:{line_num}: {message}")
    # Summary after processing all issues
    print(f"------\nChecked {len(files_list)} files")
    if all_issues:
        print(f"Found {len(all_issues)} issue(s)")
        print("Issues found (non-blocking)")
    else:
        print("No issues found")
        print("Check PASSED")
    print_timing_summary(timings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
