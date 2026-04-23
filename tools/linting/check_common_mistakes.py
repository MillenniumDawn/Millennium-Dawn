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
"""

import argparse
import os
import re
import subprocess
import sys
from multiprocessing import Pool

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
        if re.match(r"^\s*focus\s*=\s*\{", lines[i]):
            start = i
            block, i = _get_block(lines, start)
            norm = re.sub(r"\s+", " ", "".join(block))
            if _RE_AVAILABLE_ALWAYS_NO.search(norm):
                id_match = _RE_FOCUS_ID_IN_BLOCK.search(norm)
                focus_id = id_match.group(1) if id_match else None
                has_bypass = bool(_RE_BYPASS_OPEN.search(norm))
                script_completed = focus_id and focus_id in _SCRIPT_COMPLETED_FOCUSES
                if not has_bypass and not script_completed:
                    for k, bl in enumerate(block):
                        if re.search(r"\bavailable\s*=\s*\{", bl):
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
            re.match(r"^\w", lines[i])
            and "{" in code
            and not lines[i].lstrip().startswith("#")
        ):
            cat_start = i
            cat_block, i = _get_block(lines, cat_start)
            k = 1  # skip category header line
            while k < len(cat_block) - 1:  # skip closing } line
                bl = cat_block[k]
                bl_code = bl.split("#")[0]
                if re.match(r"^\s+\w", bl) and "{" in bl_code:
                    dec_block, next_k = _get_block(cat_block, k)
                    norm = re.sub(r"\s+", " ", "".join(dec_block))
                    dec_id_match = re.match(r"\s*(\w+)\s*=\s*\{", cat_block[k])
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
                            if re.search(r"\bavailable\s*=\s*\{", dbl):
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


def get_git_diff_files(base_branch="main", staged_only=False):
    """Get list of modified .txt files from git diff."""
    try:
        if staged_only:
            cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"]
        else:
            cmd = [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMRT",
                f"{base_branch}...HEAD",
            ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        modified_files = []
        for file in result.stdout.strip().split("\n"):
            if file and file.endswith(".txt"):
                if any(
                    file.startswith(d + "/") for d in ["common", "events", "history"]
                ):
                    if os.path.exists(file):
                        modified_files.append(file)
        return modified_files
    except subprocess.CalledProcessError:
        return []


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

    return [(filepath, ln, msg) for ln, msg in issues]


def get_all_files(root_dir):
    """Get all .txt files from relevant directories."""
    files = []
    for directory in ["common", "events", "history"]:
        dir_path = os.path.join(root_dir, directory)
        if os.path.exists(dir_path):
            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    if filename.endswith(".txt"):
                        files.append(os.path.join(root, filename))
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Check for common HOI4 scripting mistakes"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "diff", "staged"],
        default="all",
        help="Check mode: all files, git diff files, or staged files only (default: all)",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch for diff comparison (default: main)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 4,
        help="Number of parallel workers (default: CPU count)",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files to check (positional argument for pre-commit)",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))

    if args.filenames:
        files_list = [f for f in args.filenames if os.path.exists(f)]
    elif args.mode == "staged":
        files_list = get_git_diff_files(staged_only=True)
    elif args.mode == "diff":
        files_list = get_git_diff_files(base_branch=args.base_branch)
    else:
        files_list = get_all_files(root_dir)

    if not files_list:
        print("No files to check")
        return 0

    # Build script-completion sets before forking workers so they inherit via fork.
    global _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS
    _SCRIPT_COMPLETED_FOCUSES, _SCRIPT_COMPLETED_DECISIONS = _scan_script_completed(
        root_dir
    )

    print(f"Checking {len(files_list)} files for common mistakes...")

    with Pool(processes=args.workers) as pool:
        results = pool.map(check_file, files_list)

    all_issues = [issue for file_issues in results for issue in file_issues]

    for filepath, line_num, message in sorted(all_issues):
        print(f"WARNING: {clean_filepath(filepath)}:{line_num}: {message}")

    print(f"------\nChecked {len(files_list)} files")
    if all_issues:
        print(f"Found {len(all_issues)} issue(s)")
        print("Check FAILED")
        return 1
    else:
        print("No issues found")
        print("Check PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
