#!/usr/bin/env python3
"""Generate a branch-summary effect tooltip for a national focus.

Given a focus tree file and a target focus id, this rebuilds the target focus's
``completion_reward`` so it ends with an ``effect_tooltip = { ... }`` block that
previews the rewards of every focus *under* the target (its descendants via the
``prerequisite`` graph). ``effect_tooltip`` renders the contained effects'
tooltips without applying them, so the player sees the whole branch's payoff on
the parent focus.

The summary is AGGREGATED, not a per-focus list: ``walk_effects`` folds every
descendant's rewards into an ``Aggregate`` (sums per dynamic-modifier variable,
total treasury, building/resource/slot counts, deduped distinct effects), and
``render_aggregate`` emits one combined block. To capture a newly handled effect
kind, add a branch to the if/elif chain in ``walk_effects`` and (if it needs a
new bucket) a field on ``Aggregate`` plus its rendering. The extractor is
deliberately partial: conditionals, hidden_effect, random, nested previews,
opinion changes, add_dynamic_modifier, sub-nation scopes and unknown keywords are
intentionally skipped, so the preview is an approximation, not exhaustive.

The inserted block is delimited by marker comments so re-running replaces it in
place instead of stacking duplicates.

Usage:
    python generate_branch_summary_tooltip.py <focus_file> <focus_id> [<focus_id> ...]
    python generate_branch_summary_tooltip.py <focus_file> --list <focus_id>

The generic header loc key (focus_branch_effects_header) is ensured in
localisation/english/MD_tooltips_l_english.yml.
"""

import argparse
import os
import re
import sys

MARKER_BEGIN = "# >>> AUTO-GENERATED BRANCH SUMMARY (generate_branch_summary_tooltip.py) - do not edit by hand"
MARKER_END = "# <<< AUTO-GENERATED BRANCH SUMMARY"

HEADER_LOC_KEY = "focus_branch_effects_header"
HEADER_LOC_VALUE = (
    "\\n§YPath Summary:§!"
)

# ----------------------------------------------------------------------------
# Low-level text helpers (comment- and string-aware brace scanning)
# ----------------------------------------------------------------------------


def mask(text):
    """Return a same-length copy with comment and string *contents* blanked.

    Quote and brace characters that live inside strings/comments are turned
    into spaces so brace scanning over the mask maps 1:1 onto the raw text.
    """
    out = list(text)
    in_str = False
    in_comment = False
    escaped = False  # previous char was an unescaped backslash inside a string
    n = len(text)
    for i in range(n):
        c = text[i]
        if in_comment:
            if c == "\n":
                in_comment = False
            else:
                out[i] = " "
        elif in_str:
            if c == "\\" and not escaped:
                escaped = True
                out[i] = " "
            elif c == '"' and not escaped:
                in_str = False
            else:
                escaped = False
                out[i] = " "
        else:
            if c == "#":
                in_comment = True
                out[i] = " "
            elif c == '"':
                in_str = True
                escaped = False
    return "".join(out)


def match_brace(masked, open_idx):
    """Given index of a '{' in *masked*, return index just past its match."""
    depth = 0
    n = len(masked)
    i = open_idx
    while i < n:
        c = masked[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def leading_tabs(line):
    return len(line) - len(line.lstrip("\t"))


def format_block(text, base):
    """Re-indent a snippet from scratch using brace depth, so the result is
    cleanly tabbed regardless of the source's whitespace. Blank lines dropped.
    One statement per line is assumed (true for completion_reward contents)."""
    out = []
    depth = 0
    for raw_line in text.split("\n"):
        s = raw_line.strip()
        if not s:
            continue
        ms = mask(s)
        lead_close = 0
        for ch in ms:
            if ch == "}":
                lead_close += 1
            elif ch.isspace():
                continue
            else:
                break
        line_depth = max(0, depth - lead_close)
        out.append("\t" * (base + line_depth) + s)
        depth += ms.count("{") - ms.count("}")
        if depth < 0:
            depth = 0
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Focus-tree parsing
# ----------------------------------------------------------------------------


class Focus:
    __slots__ = ("id", "start", "end", "body_start", "body_end", "prereqs", "cr_span")

    def __init__(self, fid, start, end, body_start, body_end):
        self.id = fid
        self.start = start  # index of 'focus' keyword
        self.end = end  # index past the focus block's closing '}'
        self.body_start = body_start  # index just past focus '{'
        self.body_end = body_end  # index of focus closing '}'
        self.prereqs = []  # list of sets (each set = one OR-prerequisite group)
        self.cr_span = None  # (open_brace_idx, end_idx) of completion_reward block


_FOCUS_RE = re.compile(r"\bfocus\s*=\s*\{")
_ID_RE = re.compile(r"\bid\s*=\s*([A-Za-z0-9_]+)")
_PREREQ_RE = re.compile(r"\bprerequisite\s*=\s*\{")
_PREREQ_FOCUS_RE = re.compile(r"\bfocus\s*=\s*([A-Za-z0-9_]+)")
_CR_RE = re.compile(r"\bcompletion_reward\s*=\s*\{")


def parse_focuses(raw, masked):
    """Parse every ``focus = { ... }`` definition out of the file."""
    focuses = []
    for m in _FOCUS_RE.finditer(masked):
        open_idx = masked.index("{", m.start())
        end = match_brace(masked, open_idx)
        if end == -1:
            continue
        body_start = open_idx + 1
        body_end = end - 1
        body_masked = masked[body_start:body_end]
        id_m = _ID_RE.search(body_masked)
        if not id_m:
            continue
        fid = id_m.group(1)
        f = Focus(fid, m.start(), end, body_start, body_end)

        # Prerequisites: each prerequisite block is an OR-group of focuses.
        for pm in _PREREQ_RE.finditer(body_masked):
            p_open = body_masked.index("{", pm.start())
            p_end = match_brace(body_masked, p_open)
            if p_end == -1:
                continue
            inner = body_masked[p_open + 1 : p_end - 1]
            group = {fm.group(1) for fm in _PREREQ_FOCUS_RE.finditer(inner)}
            if group:
                f.prereqs.append(group)

        # completion_reward span (absolute indices into raw/masked).
        cr_m = _CR_RE.search(body_masked)
        if cr_m:
            cr_open = body_start + body_masked.index("{", cr_m.start())
            cr_end = match_brace(masked, cr_open)
            if cr_end != -1:
                f.cr_span = (cr_open, cr_end)

        focuses.append(f)
    return focuses


def build_children(focuses):
    """Map parent id -> ordered list of direct child ids (prerequisite edges)."""
    children = {f.id: [] for f in focuses}
    for f in focuses:
        parents = set()
        for group in f.prereqs:
            parents |= group
        for p in parents:
            if p in children:
                children[p].append(f.id)
    return children


def descendants_in_order(target, children, focuses):
    """Return descendants of *target* (excluding itself) in breadth-first tier
    order, breaking ties by source position for stable, readable output."""
    order = {f.id: i for i, f in enumerate(focuses)}
    seen = set()
    result = []
    frontier = sorted(children.get(target, []), key=lambda c: order.get(c, 1 << 30))
    while frontier:
        nxt = []
        for fid in frontier:
            if fid in seen or fid == target:
                continue
            seen.add(fid)
            result.append(fid)
            nxt.extend(children.get(fid, []))
        frontier = sorted(set(nxt) - seen, key=lambda c: order.get(c, 1 << 30))
    return result


# ----------------------------------------------------------------------------
# Effect recognition + aggregation
# ----------------------------------------------------------------------------

# Display labels for the condensed building count lines. Prefer MD's canonical
# plural building loc token ($type_plural$) so the wording stays in sync with the
# rest of the game and localises; fall back to literal English where no plural
# loc key exists. Unknown types use a title-cased token.
BUILDING_NAMES = {
    "offices": "$offices_plural$",
    "industrial_complex": "$industrial_complex_plural$",
    "arms_factory": "$arms_factory_plural$",
    "dockyard": "$dockyard_plural$",
    "microchip_plant": "$microchip_plant_plural$",
    "renewable_energy_infra": "$renewable_energy_infra_plural$",
    "agriculture_district": "$agriculture_district_plural$",
    "fuel_silo": "$fuel_silo_plural$",
    "anti_air_building": "$anti_air_building_plural$",
    "rail_way": "$rail_way_plural$",
    "infrastructure": "Infrastructure",
    "nuclear_reactor": "Nuclear Reactors",
    "synthetic_refinery": "Synthetic Refineries",
    "supply_node": "Supply Nodes",
    "radar_station": "Radar Stations",
}
RESOURCE_NAMES = {
    "steel": "Steel",
    "tungsten": "Tungsten",
    "chromium": "Chromium",
    "oil": "Oil",
    "aluminium": "Aluminium",
    "rubber": "Rubber",
    "uranium": "Uranium",
    "lead": "Lead",
}
# Per-resource text icons (interface/modifiericons_texticons.gfx). Resources
# without a dedicated icon fall back to the generic resources texticon.
RESOURCE_TEXTICONS = {
    "steel": "£steel_texticon",
    "oil": "£oil_texticon",
    "aluminium": "£aluminium_texticon",
    "rubber": "£rubber_texticon",
}
GENERIC_RESOURCE_TEXTICON = "£resources_texticon"
# Country-scope scalar effects that sum cleanly and render natively.
COUNTRY_SCALARS = {
    "add_stability",
    "add_war_support",
    "add_political_power",
    "add_manpower",
}
# Distinct (non-numeric) country-scope effects: deduped and listed once each.
# Deliberately excludes add_timed_idea (temporary, not worth previewing),
# activate_mission/activate_decision/unlock_decision_tooltip (not summarised), and
# focus-specific scalar custom_effect_tooltip lines (can't be combined, too long).
DISTINCT_KEEP = {
    "add_ideas",
    "add_idea",
    "add_tech_bonus",
}
# Temp variable reused to feed the condensed count tooltips.
AMOUNT_VAR = "focus_branch_amount"
# change_<group>_opinion = yes
_OPINION_RE = re.compile(r"^change_([a-z_]+)_opinion$")
# Scope blocks: state ids (digits) get recursed into for buildings/resources.
# Sub-nation TAG scopes (SCO/WAS/NIR/...) are intentionally not recursed into.
_STATE_RE = re.compile(r"^\d+$")
_NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def iter_statements(body, masked_body):
    """Yield (lhs, value_is_block, raw_statement, inner_raw) for each
    ``lhs = rhs`` pair at the top level of *body*."""
    n = len(body)
    i = 0
    lhs_re = re.compile(r"(\S+)\s*=\s*")
    while i < n:
        # skip whitespace
        while i < n and masked_body[i].isspace():
            i += 1
        if i >= n:
            break
        m = lhs_re.match(masked_body, i)
        if not m:
            # Unparseable token; skip to next whitespace to stay in sync.
            j = i
            while j < n and not masked_body[j].isspace():
                j += 1
            i = j
            continue
        lhs = m.group(1)
        val_start = m.end()
        if val_start < n and masked_body[val_start] == "{":
            end = match_brace(masked_body, val_start)
            if end == -1:
                break
            raw = body[i:end]
            inner = body[val_start + 1 : end - 1]
            yield lhs, True, raw, inner
            i = end
        else:
            # scalar token
            j = val_start
            while j < n and not masked_body[j].isspace():
                j += 1
            raw = body[i:j]
            scalar = body[val_start:j]
            yield lhs, False, raw, scalar
            i = j


class Aggregate:
    """Running totals across all summarised focuses."""

    def __init__(self):
        self.modifier_order = []  # dynamic modifiers in first-seen order
        self.modifier_vars = {}  # (modifier, var) -> [sum, tooltip_key]
        self.treasury = 0.0
        self.country_scalars = {}  # add_stability/... -> sum
        self.buildings = {}  # building type -> summed levels
        self.resources = {}  # resource type -> summed amount
        self.slots = 0.0  # add_extra_state_shared_building_slots total
        self.distinct = []  # ordered deduped raw snippets
        self._distinct_seen = set()

    def add_distinct(self, snippet):
        key = re.sub(r"\s+", " ", snippet).strip()
        if key and key not in self._distinct_seen:
            self._distinct_seen.add(key)
            self.distinct.append(snippet.strip())


def _f(text):
    text = text.strip()
    return float(text) if _NUM_RE.match(text) else None


def walk_effects(body, agg):
    """Walk one completion_reward / scope body, folding recognised effects into
    *agg*. Handlers key off the effect name (which is itself scope-specific in MD
    grammar), so no scope argument is needed. Conditionals, hidden_effect,
    random, nested effect_tooltip, opinion changes, flags, events, sub-nation TAG
    scopes and unknown keywords are intentionally skipped (extend the handlers
    below to capture more)."""
    masked_body = mask(body)
    current_modifier = None
    pending_treasury = None  # numeric treasury_change awaiting modify_treasury_effect

    for lhs, is_block, raw, inner in iter_statements(body, masked_body):
        # dynamic-modifier header: generic, kept; sets the bucket for the
        # following add_to_variable lines.
        if lhs == "custom_effect_tooltip" and is_block:
            if re.search(r"localization_key\s*=\s*modifies_dynamic_modifier_tt", inner):
                mm = re.search(r"\bMODIFIER\s*=\s*(\w+)", inner)
                current_modifier = mm.group(1) if mm else None
            continue
        # focus-specific scalar custom_effect_tooltip lines are intentionally
        # dropped: they can't be combined and would bloat the summary.
        if lhs == "custom_effect_tooltip":
            continue

        if lhs == "set_temp_variable" and is_block:
            tm = re.search(r"\btreasury_change\s*=\s*(-?\d+(?:\.\d+)?)\b", inner)
            if tm:
                pending_treasury = float(tm.group(1))
            continue

        # opinion changes are intentionally not summarised (too noisy)
        if _OPINION_RE.match(lhs) and not is_block:
            continue
        if lhs == "modify_treasury_effect" and not is_block:
            if pending_treasury is not None:
                agg.treasury += pending_treasury
                pending_treasury = None
            continue

        if lhs in COUNTRY_SCALARS and not is_block:
            v = _f(inner)
            if v is not None:
                agg.country_scalars[lhs] = agg.country_scalars.get(lhs, 0.0) + v
            continue

        if lhs in ("add_to_variable", "subtract_from_variable") and is_block:
            sign = -1.0 if lhs == "subtract_from_variable" else 1.0
            vm = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(-?\d+(?:\.\d+)?)\b", inner)
            tt = re.search(r"\btooltip\s*=\s*([A-Za-z0-9_]+)", inner)
            if vm and current_modifier:
                # Only variables under a dynamic-modifier header are summarised.
                # Bare opinion adds (e.g. international_bankers_opinion) and other
                # bare/sub-nation vars have no modifier bucket and are skipped.
                var, val = vm.group(1), sign * float(vm.group(2))
                key = (current_modifier, var)
                if key not in agg.modifier_vars:
                    if current_modifier not in agg.modifier_order:
                        agg.modifier_order.append(current_modifier)
                    agg.modifier_vars[key] = [0.0, tt.group(1) if tt else None]
                agg.modifier_vars[key][0] += val
                if tt and not agg.modifier_vars[key][1]:
                    agg.modifier_vars[key][1] = tt.group(1)
            continue

        if lhs == "add_building_construction" and is_block:
            t = re.search(r"\btype\s*=\s*(\w+)", inner)
            lv = re.search(r"\blevel\s*=\s*(-?\d+(?:\.\d+)?)", inner)
            if t and lv:
                agg.buildings[t.group(1)] = agg.buildings.get(t.group(1), 0.0) + float(
                    lv.group(1)
                )
            continue
        if lhs == "add_resource" and is_block:
            t = re.search(r"\btype\s*=\s*(\w+)", inner)
            am = re.search(r"\bamount\s*=\s*(-?\d+(?:\.\d+)?)", inner)
            if t and am:
                agg.resources[t.group(1)] = agg.resources.get(t.group(1), 0.0) + float(
                    am.group(1)
                )
            continue
        if lhs == "add_extra_state_shared_building_slots" and not is_block:
            v = _f(inner)
            if v is not None:
                agg.slots += v
            continue

        if lhs in DISTINCT_KEEP:
            agg.add_distinct(raw)
            continue

        # recurse into state scopes only (always exist; safe inside effect_tooltip)
        if is_block and _STATE_RE.match(lhs):
            walk_effects(inner, agg)
            continue

        # everything else intentionally skipped (see docstring)


def fmt_num(v):
    if v == int(v):
        return str(int(v))
    return ("%.4f" % v).rstrip("0").rstrip(".")


# ----------------------------------------------------------------------------
# Block assembly + file editing
# ----------------------------------------------------------------------------


def collapse_newlines(parts):
    """Collapse runs of bare ``newline = yes`` separators to one and drop a
    leading/trailing separator."""
    result = []
    for p in parts:
        if p == "newline = yes" and (not result or result[-1] == "newline = yes"):
            continue
        result.append(p)
    while result and result[-1] == "newline = yes":
        result.pop()
    while result and result[0] == "newline = yes":
        result.pop(0)
    return result


def render_aggregate(agg, loc_defs):
    """Render *agg* into base-0 effect_tooltip lines. New loc keys needed for
    the condensed count tooltips are added to *loc_defs* (key -> value)."""
    parts = []

    # dynamic-modifier variable changes, grouped by modifier, values summed
    for modifier in agg.modifier_order:
        nonzero = [
            (var, val, tt)
            for (mod, var), (val, tt) in agg.modifier_vars.items()
            if mod == modifier and val != 0
        ]
        if not nonzero:
            continue  # all of this modifier's vars cancelled out; skip the header
        parts.append(
            "custom_effect_tooltip = { localization_key = "
            f"modifies_dynamic_modifier_tt MODIFIER = {modifier} }}"
        )
        for var, val, tt in nonzero:
            tip = f" tooltip = {tt}" if tt else ""
            parts.append(f"add_to_variable = {{ {var} = {fmt_num(val)}{tip} }}")
        parts.append("newline = yes")

    # flat country scalars (stability, war support, ...)
    for key, val in agg.country_scalars.items():
        if val != 0:
            parts.append(f"{key} = {fmt_num(val)}")
    parts.append("newline = yes")

    # treasury, summed
    if agg.treasury != 0:
        parts.append(f"set_temp_variable = {{ treasury_change = {fmt_num(agg.treasury)} }}")
        parts.append("modify_treasury_effect = yes")
        parts.append("newline = yes")

    # condensed counts: buildings, resources, building slots
    def count_line(loc_key, amount, label, verb):
        loc_defs.setdefault(
            loc_key, f'{verb} §Y[?{AMOUNT_VAR}|0]§! {label}'
        )
        parts.append(f"set_temp_variable = {{ {AMOUNT_VAR} = {fmt_num(amount)} }}")
        parts.append(f"custom_effect_tooltip = {loc_key}")

    for btype, levels in agg.buildings.items():
        if levels == 0:
            continue
        label = BUILDING_NAMES.get(btype, btype.replace("_", " ").title())
        count_line(f"focus_branch_build_{btype}", levels, label, "Construct")
    for rtype, amount in agg.resources.items():
        if amount == 0:
            continue
        icon = RESOURCE_TEXTICONS.get(rtype, GENERIC_RESOURCE_TEXTICON)
        name = RESOURCE_NAMES.get(rtype, rtype.replace("_", " ").title())
        count_line(f"focus_branch_resource_{rtype}", amount, f"{icon} {name}", "Add")
    if agg.slots != 0:
        count_line(
            "focus_branch_slots", agg.slots, "shared building slots", "Add"
        )
    parts.append("newline = yes")

    # distinct non-numeric effects (ideas, tech bonuses, missions, decisions,
    # descriptive custom tooltips), deduped
    parts.extend(agg.distinct)

    return collapse_newlines(parts)


def build_summary_block(target, descendants, raw, focuses_by_id, base_tabs, loc_defs):
    """Construct the marker-delimited combined summary for *target*."""
    agg = Aggregate()
    for fid in descendants:
        f = focuses_by_id[fid]
        if not f.cr_span:
            continue
        cr_open, cr_end = f.cr_span
        walk_effects(raw[cr_open + 1 : cr_end - 1], agg)

    inner_parts = render_aggregate(agg, loc_defs)
    if not inner_parts:
        return None

    inner = "\n".join(inner_parts)
    block_base0 = (
        f"{MARKER_BEGIN}\n"
        f"custom_effect_tooltip = {HEADER_LOC_KEY}\n"
        f"effect_tooltip = {{\n"
        f"{inner}\n"
        f"}}\n"
        f"{MARKER_END}"
    )
    # Recompute all indentation from brace depth and place at base_tabs.
    return format_block(block_base0, base_tabs)


def strip_existing_block(focus_body):
    """Remove a previously generated marker-delimited block from *focus_body*."""
    begin = focus_body.find(MARKER_BEGIN)
    if begin == -1:
        return focus_body, False
    end = focus_body.find(MARKER_END, begin)
    if end == -1:
        return focus_body, False
    # extend to end of the MARKER_END line
    line_end = focus_body.find("\n", end)
    if line_end == -1:
        line_end = len(focus_body)
    else:
        line_end += 1
    # also swallow the indentation/newline immediately preceding the begin marker
    line_start = focus_body.rfind("\n", 0, begin)
    line_start = 0 if line_start == -1 else line_start + 1
    return focus_body[:line_start] + focus_body[line_end:], True


def process_target(raw, target, loc_defs):
    """Return (new_raw, message). Re-derives parse state from *raw* each call so
    multiple targets can be applied sequentially. New count-tooltip loc keys are
    collected into *loc_defs*."""
    masked = mask(raw)
    focuses = parse_focuses(raw, masked)
    by_id = {f.id: f for f in focuses}
    if target not in by_id:
        return raw, f"ERROR: focus '{target}' not found"

    # 1) strip any stale block inside the target focus first
    tf = by_id[target]
    focus_text = raw[tf.start : tf.end]
    stripped, removed = strip_existing_block(focus_text)
    if removed:
        raw = raw[: tf.start] + stripped + raw[tf.end :]
        masked = mask(raw)
        focuses = parse_focuses(raw, masked)
        by_id = {f.id: f for f in focuses}
        tf = by_id[target]

    if not tf.cr_span:
        return raw, f"ERROR: focus '{target}' has no completion_reward"

    children = build_children(focuses)
    descendants = descendants_in_order(target, children, focuses)
    if not descendants:
        return raw, f"WARNING: focus '{target}' has no descendants; nothing to do"

    cr_open, cr_end = tf.cr_span
    # Indent everything off the completion_reward line itself, so it is correct
    # whether the reward is multi-line or a one-liner.
    cr_line_start = raw.rfind("\n", 0, cr_open) + 1
    cr_indent = leading_tabs(raw[cr_line_start:cr_open])
    base_tabs = cr_indent + 1

    block = build_summary_block(target, descendants, raw, by_id, base_tabs, loc_defs)
    if block is None:
        return raw, f"WARNING: no recognised effects under '{target}'"

    # Insert just before the closing brace. Keep existing inner content (drop only
    # its trailing whitespace) so the block always lands INSIDE completion_reward,
    # even when the open and close braces share one line.
    inner = raw[cr_open + 1 : cr_end - 1].rstrip()
    rebuilt = (
        raw[cr_line_start:cr_open + 1]
        + inner
        + "\n"
        + block
        + "\n"
        + ("\t" * cr_indent)
        + "}"
    )
    new_raw = raw[:cr_line_start] + rebuilt + raw[cr_end:]
    return new_raw, (
        f"OK: '{target}' summarised {len(descendants)} descendant focus(es)"
    )


# ----------------------------------------------------------------------------
# Localisation keys
# ----------------------------------------------------------------------------


_LOC_REL = ("localisation", "english", "MD_tooltips_l_english.yml")


def find_loc_file(focus_file):
    """Locate MD_tooltips_l_english.yml by walking up from the focus file. Falls
    back to the conventional <mod>/common/national_focus/<file> layout. Returns
    the path or None."""
    start = os.path.dirname(os.path.abspath(focus_file))
    d = start
    while True:
        candidate = os.path.join(d, *_LOC_REL)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    guess = os.path.normpath(os.path.join(start, "..", "..", *_LOC_REL))
    return guess if os.path.isfile(guess) else None


def ensure_loc(loc_path, loc_defs):
    """Append any missing key from *loc_defs* (key -> value) to MD_tooltips,
    preserving the UTF-8 BOM. Existing keys are left untouched."""
    with open(loc_path, "r", encoding="utf-8-sig", newline="") as fh:
        content = fh.read()
    added = []
    for key, value in loc_defs.items():
        if re.search(rf"^\s*{re.escape(key)}\s*:", content, re.MULTILINE):
            continue
        if not content.endswith("\n"):
            content += "\n"
        content += f' {key}: "{value}"\n'
        added.append(key)
    if added:
        with open(loc_path, "w", encoding="utf-8-sig", newline="") as fh:
            fh.write(content)
        print(f"  loc: added {len(added)} key(s) to MD_tooltips_l_english.yml")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("focus_file", help="focus tree .txt file")
    ap.add_argument("focus_ids", nargs="*", help="target focus id(s)")
    ap.add_argument(
        "--list", metavar="FOCUS", help="list descendants of FOCUS and exit"
    )
    args = ap.parse_args()

    with open(args.focus_file, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()

    if args.list:
        masked = mask(raw)
        focuses = parse_focuses(raw, masked)
        children = build_children(focuses)
        if args.list not in {f.id for f in focuses}:
            print(f"ERROR: focus '{args.list}' not found", file=sys.stderr)
            sys.exit(1)
        ds = descendants_in_order(args.list, children, focuses)
        print(f"{args.list}: {len(ds)} descendant(s)")
        for d in ds:
            print(f"  {d}")
        return

    if not args.focus_ids:
        ap.error("provide at least one focus id (or use --list)")

    new_raw = raw
    messages = []
    loc_defs = {HEADER_LOC_KEY: HEADER_LOC_VALUE}
    for target in args.focus_ids:
        new_raw, msg = process_target(new_raw, target, loc_defs)
        messages.append(msg)
        print(f"  {msg}")

    if any(m.startswith("ERROR") for m in messages):
        sys.exit(1)

    if new_raw != raw:
        # Resolve the loc file BEFORE writing the focus file, so we never leave
        # the focus referencing loc keys we failed to add.
        loc_path = find_loc_file(args.focus_file)
        if loc_path is None:
            print(
                "  ERROR: MD_tooltips_l_english.yml not found; the focus would "
                "reference undefined loc keys. Aborting without writing.",
                file=sys.stderr,
            )
            sys.exit(1)
        with open(args.focus_file, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_raw)
        print(f"  wrote {args.focus_file}")
        ensure_loc(loc_path, loc_defs)
    else:
        print("  no changes")


if __name__ == "__main__":
    main()
