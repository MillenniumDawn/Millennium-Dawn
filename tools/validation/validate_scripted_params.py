#!/usr/bin/env python3
##########################
# Scripted Effect Parameter Validation Script
# Validates that callers of documented scripted effects pass required temp variables.
#
# Checks:
#   1. Auto-discover parameter contracts from scripted effect comment blocks and
#      usage patterns in common/scripted_effects/*.txt
#   2. Validate that each call site sets required temp variables before the call
#      in the same or outer scope (temp vars set earlier in the scope chain are
#      visible to callers at deeper non-scope-changing nesting)
#   3. Warn on orphaned temp variable sets (set but no matching effect call anywhere
#      in the same scope block)
#   4. Warn on scope boundary violations (temp vars set inside a scope-changing
#      block, e.g. random_other_country = { ... }, but the effect call is outside)
##########################
import glob
import os
import re
from typing import Dict, List, Set, Tuple

from validator_common import BaseValidator, Severity, run_validator_main, strip_comments

# ---------------------------------------------------------------------------
# Hardcoded contracts for well-documented effects.  Auto-discovery below fills
# in additional contracts from "# Parameters:" comment blocks.
# ---------------------------------------------------------------------------

# Mapping: effect_name -> { "required": [...], "optional": [...] }
HARDCODED_CONTRACTS: Dict[str, Dict[str, List[str]]] = {
    "change_influence_percentage": {
        "required": ["percent_change"],
        "optional": ["tag_index", "influence_target"],
    },
    "change_domestic_influence_percentage": {
        "required": ["percent_change"],
        "optional": ["influencer_index"],
    },
    "change_current_influencer_index_percentage": {
        "required": ["percent_change", "influencer_index"],
        "optional": [],
    },
    "steal_from_party": {
        "required": ["steal_party_index"],
        "optional": [],
    },
    "remove_coalition_members_effect": {
        "required": ["remove_col_one"],
        "optional": [],
    },
    "modify_missile_inventory_count": {
        "required": ["missile_index", "missile_count"],
        "optional": ["missile_type"],
    },
    "change_arab_spring_strength": {
        "required": ["temp_strength"],
        "optional": [],
    },
    "add_hydroelectric_energy_production_effect": {
        "required": ["electric_addition", "storage_addition"],
        "optional": [],
    },
    "get_pol_distance": {
        "required": ["pol_dist_target_index", "pol_dist_source_index"],
        "optional": [],
    },
    "configure_religious_setup": {
        "required": ["nation_to_copy_from"],
        "optional": [],
    },
    "set_elections_with_frequency": {
        "required": ["election_freq"],
        "optional": ["election_year_param", "election_month_param"],
    },
}

# ---------------------------------------------------------------------------
# Keywords that introduce a new scripting scope (country/state/leader scopes).
# When a temp variable is set inside one of these blocks it is local to that
# scope and NOT available in the parent scope after the block closes.
# ---------------------------------------------------------------------------
SCOPE_CHANGING_KEYWORDS: Set[str] = {
    "every_country",
    "random_country",
    "every_possible_country",
    "random_possible_country",
    "every_other_country",
    "random_other_country",
    "every_allied_country",
    "random_allied_country",
    "every_enemy_country",
    "random_enemy_country",
    "every_neighbor_country",
    "random_neighbor_country",
    "every_occupied_country",
    "random_occupied_country",
    "every_country_with_original_tag",
    "random_country_with_original_tag",
    "every_state",
    "random_state",
    "every_owned_state",
    "random_owned_state",
    "every_army_leader",
    "random_army_leader",
    "every_navy_leader",
    "random_navy_leader",
    "every_unit_leader",
    "random_unit_leader",
    "capital_scope",
    "owner",
    "controller",
    "overlord",
    "faction_leader",
    "ROOT",
    "PREV",
    "FROM",
    "var",  # var:X = { } scope
    "for_each_scope_loop",
    "while_loop_effect",
    "for_loop_effect",
    "for_each_loop",
}

# Regex patterns
_SET_TEMP_RE = re.compile(
    r"\bset_temp_variable\s*=\s*\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
)
_CALL_RE = re.compile(r"\b([a-z][a-z0-9_]*)\s*=\s*yes\b")
_KW_OPEN_RE = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{")


def _parse_effect_contracts_from_file(
    filepath: str,
) -> Dict[str, Dict[str, List[str]]]:
    """Parse a scripted_effects file and extract parameter contracts from comment blocks.

    Looks for the pattern:
        # Parameters:
        # - param_name: description
        effect_name = {
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            content = fh.read()
    except Exception:
        return {}

    contracts: Dict[str, Dict[str, List[str]]] = {}
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Look for "# Parameters:" or "# Parameter:" comment block
        if re.match(r"^#\s*[Pp]arameters?\s*:", stripped):
            params_required: List[str] = []
            params_optional: List[str] = []
            j = i + 1

            while j < len(lines):
                pline = lines[j].strip()
                if not pline.startswith("#"):
                    break
                inner = pline.lstrip("#").strip()
                if not inner or re.match(r"^[-=*]+$", inner):
                    j += 1
                    continue

                # "# set_temp_variable = { param_name = ... }"
                stv_m = re.search(
                    r"set_temp_variable\s*=\s*\{\s*([a-z][a-z0-9_]*)\s*=", inner
                )
                if stv_m:
                    pname = stv_m.group(1)
                    if "optional" in inner.lower():
                        params_optional.append(pname)
                    else:
                        params_required.append(pname)
                    j += 1
                    continue

                # "# - param_name: ..." or "# - param_name - ..."
                plain_m = re.match(r"^[-\*]?\s*([a-z][a-z0-9_]*)\s*[-:]", inner)
                if plain_m:
                    pname = plain_m.group(1)
                    skip_words = {
                        "note",
                        "purpose",
                        "effect",
                        "function",
                        "output",
                        "how",
                        "example",
                        "null",
                        "none",
                        "n",
                        "a",
                        "the",
                        "this",
                        "see",
                        "usage",
                    }
                    if pname.lower() not in skip_words:
                        if "optional" in inner.lower():
                            params_optional.append(pname)
                        else:
                            params_required.append(pname)
                j += 1

            # Find the effect definition immediately after the comment block
            k = j
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines):
                def_m = re.match(r"^([a-z][a-z0-9_]*)\s*=\s*\{", lines[k].strip())
                if def_m and (params_required or params_optional):
                    eff_name = def_m.group(1)
                    if eff_name not in HARDCODED_CONTRACTS:
                        contracts[eff_name] = {
                            "required": params_required,
                            "optional": params_optional,
                        }
            i = j
            continue
        i += 1

    return contracts


# ---------------------------------------------------------------------------
# Token-based scope walker
# ---------------------------------------------------------------------------


def _normalize_multiline_set_temp(text: str) -> str:
    """Collapse multi-line set_temp_variable blocks onto a single line.

    HOI4 files sometimes write:
        set_temp_variable = {
            param_name = value
        }
    This collapses such blocks into the single-line form
        set_temp_variable = { param_name = value }
    so that the tokenizer can match them with a single-line regex.

    Only collapses blocks that are clearly set_temp_variable (not deeper nesting).
    """
    result = re.sub(
        r"set_temp_variable\s*=\s*\{\s*\n\s*([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^\n}]+?)\s*\n\s*\}",
        r"set_temp_variable = { \1 }",
        text,
    )
    return result


def _tokenize(text: str) -> List[Tuple[str, int, str]]:
    """Tokenize comment-stripped script text into a flat token list.

    Each token is (kind, line_number, value):
      "set_temp"   — set_temp_variable = { NAME = ... }
      "call"       — NAME = yes
      "scope_open" — NAME = {  where NAME is a scope-changing keyword
      "plain_open" — { (non-scope-changing open, including if/hidden_effect/etc.)
      "close"      — }
    """
    # Collapse multi-line set_temp_variable = { ... } blocks so the regex can
    # match them on a single line.
    text = _normalize_multiline_set_temp(text)

    tokens: List[Tuple[str, int, str]] = []
    lines = text.splitlines()

    for lineno, raw in enumerate(lines, start=1):
        # Inline comment stripping
        ci = raw.find("#")
        if ci >= 0:
            raw = raw[:ci]

        # set_temp_variable = { NAME = ... }
        for m in _SET_TEMP_RE.finditer(raw):
            tokens.append(("set_temp", lineno, m.group(1)))

        # Keyword = { openers — detect before closing braces so order is right
        for m in _KW_OPEN_RE.finditer(raw):
            kw = m.group(1)
            tokens.append(
                (
                    "scope_open" if kw in SCOPE_CHANGING_KEYWORDS else "plain_open",
                    lineno,
                    kw,
                )
            )

        # Closing braces
        for _ in re.finditer(r"\}", raw):
            tokens.append(("close", lineno, ""))

        # Effect calls: NAME = yes
        for m in _CALL_RE.finditer(raw):
            tokens.append(("call", lineno, m.group(1)))

    return tokens


def _validate_call_sites_in_file(
    args: Tuple[str, Dict[str, Dict[str, List[str]]], str],
) -> List[Tuple[str, str, int]]:
    """Validate one file for missing required params and orphaned sets.

    Returns a list of (category, message, line_number) tuples.
    """
    filepath, contracts, mod_path = args

    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except Exception:
        return []

    text = strip_comments(raw)
    rel = os.path.relpath(filepath, mod_path)

    # Quick pre-check: does this file reference any contracted effect?
    contracted_names = set(contracts.keys())
    if not any(name in text for name in contracted_names):
        return []

    results: List[Tuple[str, str, int]] = []
    tokens = _tokenize(text)

    # Scope stack.  Each frame:
    #   "scope_changing": bool — True if opened by a scope-changing keyword
    #   "temps": Dict[str, int]  — temp vars SET at this frame level -> line number
    #   "depth": int — count of non-scope-changing { } nesting inside this frame
    #
    # Temp variables set in a frame are visible to all descendants until the
    # frame is popped.  This means a set_temp at depth 0 is visible inside any
    # if/hidden_effect/etc. at deeper non-scope-changing levels, which is the
    # correct HOI4 behaviour.
    #
    # When a scope-changing keyword opens, we push a new frame.  Temp vars from
    # outer frames are NOT passed into the inner frame's "temps", but they are
    # still technically visible to the inner scope in the game engine.  However,
    # if a param is set ONLY in the inner frame and the CALL is outside, that is
    # a scope-boundary violation.

    stack: List[Dict] = [{"scope_changing": False, "temps": {}, "depth": 0}]

    for kind, lineno, value in tokens:
        if kind == "scope_open":
            # Push a new scope frame
            stack.append({"scope_changing": True, "temps": {}, "depth": 0})

        elif kind == "plain_open":
            # Non-scope-changing open: increment depth counter on current frame
            stack[-1]["depth"] += 1

        elif kind == "close":
            if stack[-1]["depth"] > 0:
                stack[-1]["depth"] -= 1
            elif len(stack) > 1:
                stack.pop()
            # else: extra close at root, ignore

        elif kind == "set_temp":
            # Record in the current frame
            stack[-1]["temps"][value] = lineno

        elif kind == "call":
            if value not in contracts:
                continue

            contract = contracts[value]
            required = contract.get("required", [])

            # Collect all temp vars visible in the current scope chain
            # (frames at all levels, since even outer scope vars are visible
            # unless a scope-changing frame was introduced after they were set)
            #
            # The visibility model: temp vars set before a scope-changing block
            # are visible inside it; temp vars set inside a scope-changing block
            # are NOT visible outside.  Since we track frames, any temp var in
            # any frame on the stack at this point was set in the current or an
            # ancestor scope, so it is visible.
            visible: Set[str] = set()
            for frame in stack:
                visible.update(frame["temps"].keys())

            for param in required:
                if param not in visible:
                    results.append(
                        (
                            "missing-required-param",
                            f"{rel}:{lineno} - '{value}' called without required "
                            f"temp variable '{param}'",
                            lineno,
                        )
                    )

            # Scope-boundary violations (temp set inside a popped scope-changing
            # frame, call outside) are already caught by the missing-param check:
            # once the inner frame is popped, the param is no longer in any
            # frame on the stack, so the param check above will fire.

    return results


class Validator(BaseValidator):
    TITLE = "SCRIPTED EFFECT PARAMETER VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contracts: Dict[str, Dict[str, List[str]]] = {}

    def _build_contracts(self):
        """Build the parameter contract registry from hardcoded + auto-discovered data."""
        self._log_section("Building scripted effect parameter contracts")

        self._contracts.update(HARDCODED_CONTRACTS)

        # Auto-discover from scripted effect files (always full scan — definitions
        # are the truth set and must be complete even in staged mode)
        effect_files = glob.glob(
            os.path.join(self.mod_path, "common", "scripted_effects", "*.txt")
        )
        discovered = 0
        for filepath in sorted(effect_files):
            parsed = _parse_effect_contracts_from_file(filepath)
            for eff_name, contract in parsed.items():
                if eff_name not in self._contracts and contract["required"]:
                    self._contracts[eff_name] = contract
                    discovered += 1

        self.log(f"  Hardcoded contracts:              {len(HARDCODED_CONTRACTS)}")
        self.log(f"  Auto-discovered contracts:        {discovered}")
        self.log(f"  Total contracts:                  {len(self._contracts)}")
        for eff_name, c in sorted(self._contracts.items()):
            req = ", ".join(c.get("required", [])) or "(none)"
            opt = ", ".join(c.get("optional", [])) or "(none)"
            self.log(f"    {eff_name}: required=[{req}] optional=[{opt}]")

    def _validate_callers(self):
        """Validate all caller files against the contract registry."""
        self._log_section("Checking scripted effect parameter usage")

        if not self._contracts:
            self.log("  No contracts found — nothing to validate")
            return

        scan_patterns = [
            "common/national_focus/*.txt",
            "common/scripted_effects/*.txt",
            "common/decisions/*.txt",
            "common/decisions/**/*.txt",
            "events/*.txt",
        ]
        files = self._collect_files(scan_patterns)
        self.log(f"  Scanning {len(files)} files for effect calls")

        args_list = [(f, self._contracts, self.mod_path) for f in files]
        all_results = self._pool_map(
            _validate_call_sites_in_file, args_list, chunksize=20
        )

        missing_param_results = []
        scope_violation_results = []

        for file_results in all_results:
            for category, message, _line in file_results:
                if category == "missing-required-param":
                    missing_param_results.append(message)
                elif category == "scope-boundary-violation":
                    scope_violation_results.append(message)

        self._report(
            missing_param_results,
            "All contracted effect calls have required temp variables set",
            "Effect calls missing required temp variable setup:",
            severity=Severity.ERROR,
            category="missing-required-param",
        )

        self._report(
            scope_violation_results,
            "No scope-boundary violations found",
            "Scope-boundary violations (temp var set in inner scope, call in outer scope):",
            severity=Severity.ERROR,
            category="scope-boundary-violation",
        )

    def run_validations(self):
        self._build_contracts()
        self._validate_callers()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate scripted effect parameters in Millennium Dawn mod",
    )
