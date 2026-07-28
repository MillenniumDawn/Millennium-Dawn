#!/usr/bin/env python3
"""Cross-check naval AI-equipment variant modules against ship-hull slot rules.

The engine silently drops a module assigned to a slot that does not exist on the
hull, or whose module category is not in that slot's ``allowed_module_categories``
— the design loads but the AI builds a crippled ship (see upstream PR #2510,
which fixed ~200 screen-hull fire-control modules pointing at the plain
``module_fire_control_system_category`` where the slot only accepts the screen
category). Slot rules differ per hull, so every variant is validated against the
hull its ``type`` names.

A slot value in ``target_variant.modules`` references either a concrete module
(resolved to its ``category``) or a category token directly (the
``{ module = <category> upgrade = current }`` form the generic designs use, which
means "current best module of this category"). Both are legal references; the
category — resolved or literal — must appear in the slot's allowed set.
"""

import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import strip_comments, strip_inline_comment

_NAME_BLOCK_RE = re.compile(r"([A-Za-z_][\w.]*)\s*=\s*\{")
_ASSIGN_RE = re.compile(r"([A-Za-z_]\w*)\s*=\s*")
_CATEGORY_TOKEN_RE = re.compile(r"module_\w+")


def _match_brace(text: str, open_idx: int) -> int:
    """Index of the ``}`` matching the ``{`` at *open_idx*, or -1 if unbalanced.
    Braces inside double-quoted strings are ignored."""
    depth = 0
    in_str = False
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"' and text[i - 1] != "\\":
            in_str = not in_str
        elif not in_str:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def _iter_blocks(text: str, lo: int, hi: int):
    """Yield ``(name, body_lo, body_hi, header_start)`` for each ``name = { ... }``
    block at the top level of the ``text[lo:hi]`` span (nested blocks skipped)."""
    pos = lo
    while pos < hi:
        m = _NAME_BLOCK_RE.search(text, pos, hi)
        if not m:
            return
        open_idx = text.index("{", m.end() - 1)
        close = _match_brace(text, open_idx)
        if close == -1 or close > hi:
            return
        yield m.group(1), open_idx + 1, close, m.start()
        pos = close + 1


def _depth0_text(text: str, lo: int, hi: int) -> str:
    """The ``text[lo:hi]`` span with every nested ``{...}`` block removed, so a
    regex sees only this block's own scalar assignments."""
    out: List[str] = []
    depth = 0
    in_str = False
    i = lo
    while i < hi:
        c = text[i]
        if c == '"' and text[i - 1] != "\\":
            in_str = not in_str
            if depth == 0:
                out.append(c)
        elif c == "{" and not in_str:
            depth += 1
        elif c == "}" and not in_str:
            depth -= 1
        elif depth == 0:
            out.append(c)
        i += 1
    return "".join(out)


def _scalar(text: str, lo: int, hi: int, key: str) -> Optional[str]:
    """First ``key = value`` at brace-depth 0 of the ``text[lo:hi]`` span.
    Comments must already be blanked so ``#`` braces don't skew the depth count."""
    for m in re.compile(r"\b" + re.escape(key) + r"\s*=\s*([A-Za-z_]\w*)").finditer(
        text, lo, hi
    ):
        seg = text[lo : m.start()]
        if seg.count("{") == seg.count("}"):
            return m.group(1)
    return None


def blank_comments(text: str) -> str:
    """Replace every ``#`` comment with spaces, preserving line lengths and
    offsets so character positions still map to the original line numbers."""
    lines = []
    for line in text.split("\n"):
        code = strip_inline_comment(line)
        lines.append(code + " " * (len(line) - len(code)))
    return "\n".join(lines)


# ---- hull slot rules -------------------------------------------------------


def _parse_slot_categories(
    text: str, lo: int, hi: int
) -> Dict[str, Optional[Set[str]]]:
    """slot name -> allowed category set (None when the slot declares no
    ``allowed_module_categories``, meaning unconstrained)."""
    slots: Dict[str, Optional[Set[str]]] = {}
    for slot, blo, bhi, _ in _iter_blocks(text, lo, hi):
        cats: Optional[Set[str]] = None
        for key, clo, chi, _ in _iter_blocks(text, blo, bhi):
            if key == "allowed_module_categories":
                cats = set(_CATEGORY_TOKEN_RE.findall(text[clo:chi]))
        slots[slot] = cats
    return slots


@dataclass
class _Hull:
    slots: Optional[Dict[str, Optional[Set[str]]]]
    archetype: Optional[str]
    inherit: bool


def parse_ship_hulls(text: str) -> Dict[str, _Hull]:
    """Parse a ship-equipment file into ``{hull: _Hull}``. Hulls with
    ``module_slots = inherit`` carry no slots until resolved against their
    archetype (see :func:`resolve_hull_slots`)."""
    hulls: Dict[str, _Hull] = {}
    n = len(text)
    containers: List[Tuple[int, int]] = []
    for name, blo, bhi, _ in _iter_blocks(text, 0, n):
        if name == "equipments":
            containers.append((blo, bhi))
    if not containers:
        containers.append((0, n))
    for lo, hi in containers:
        for hull, hlo, hhi, _ in _iter_blocks(text, lo, hi):
            body = _depth0_text(text, hlo, hhi)
            arch = None
            am = re.search(r"\barchetype\s*=\s*(\w+)", body)
            if am:
                arch = am.group(1)
            slots = None
            inherit = bool(re.search(r"\bmodule_slots\s*=\s*inherit", body))
            for key, klo, khi, _ in _iter_blocks(text, hlo, hhi):
                if key == "module_slots":
                    slots = _parse_slot_categories(text, klo, khi)
                    break
            if slots is None and not inherit and not am:
                continue
            hulls[hull] = _Hull(slots=slots, archetype=arch, inherit=inherit)
    return hulls


def resolve_hull_slots(
    hulls: Dict[str, _Hull],
) -> Dict[str, Optional[Dict[str, Optional[Set[str]]]]]:
    """hull -> resolved slot map, chasing ``module_slots = inherit`` to the
    archetype. None marks a hull whose slots cannot be resolved."""
    resolved: Dict[str, Optional[Dict[str, Optional[Set[str]]]]] = {}

    def resolve(name: str, seen: frozenset):
        if name in resolved:
            return resolved[name]
        hull = hulls.get(name)
        if hull is None:
            return None
        if hull.slots is not None:
            resolved[name] = hull.slots
        elif hull.inherit and hull.archetype and hull.archetype not in seen:
            resolved[name] = resolve(hull.archetype, seen | {name})
        else:
            resolved[name] = None
        return resolved[name]

    for name in hulls:
        resolve(name, frozenset())
    return resolved


# ---- module -> category ----------------------------------------------------


def _top_level_category(text: str, lo: int, hi: int) -> Optional[str]:
    depth = 0
    for line in text[lo:hi].split("\n"):
        code = strip_inline_comment(line)
        if depth == 0:
            m = re.match(r"\s*category\s*=\s*(\w+)", code)
            if m:
                return m.group(1)
        depth += code.count("{") - code.count("}")
    return None


def parse_ship_modules(text: str) -> Dict[str, str]:
    """module name -> its top-level ``category`` (nested ``module_category``
    keys inside ``can_convert_from`` are ignored)."""
    mods: Dict[str, str] = {}
    n = len(text)
    containers = [
        (blo, bhi)
        for name, blo, bhi, _ in _iter_blocks(text, 0, n)
        if name == "equipment_modules"
    ]
    if not containers:
        containers.append((0, n))
    for lo, hi in containers:
        for mod, mlo, mhi, _ in _iter_blocks(text, lo, hi):
            cat = _top_level_category(text, mlo, mhi)
            if cat:
                mods[mod] = cat
    return mods


# ---- variant module assignments -------------------------------------------


def _refs_from_block(text: str, lo: int, hi: int) -> List[str]:
    body = text[lo:hi]
    ao = re.search(r"any_of\s*=\s*\{", body)
    if ao:
        inner_open = lo + ao.end() - 1
        inner_close = _match_brace(text, inner_open)
        return re.findall(r"[A-Za-z_]\w*", text[inner_open + 1 : inner_close])
    mm = re.search(r"\bmodule\s*=\s*(?:[<>]\s*)?([A-Za-z_]\w*)", body)
    if mm:
        return [mm.group(1)]
    return _CATEGORY_TOKEN_RE.findall(body)


def _parse_module_assignments(
    text: str, lo: int, hi: int
) -> List[Tuple[str, List[str], int]]:
    """(slot, [referenced tokens], header_offset) for each assignment in a
    ``modules = { ... }`` span."""
    out: List[Tuple[str, List[str], int]] = []
    pos = lo
    while pos < hi:
        m = _ASSIGN_RE.search(text, pos, hi)
        if not m:
            break
        slot = m.group(1)
        j = m.end()
        while j < hi and text[j] in " \t\r\n":
            j += 1
        if j < hi and text[j] == "{":
            close = _match_brace(text, j)
            if close == -1:
                break
            out.append((slot, _refs_from_block(text, j + 1, close), m.start()))
            pos = close + 1
        else:
            tok = re.match(r"(?:[<>]\s*)?([A-Za-z_]\w*)", text[j:hi])
            if tok:
                out.append((slot, [tok.group(1)], m.start()))
                pos = j + tok.end()
            else:
                pos = j
    return out


def _iter_target_variants(text: str, lo: int, hi: int):
    for name, blo, bhi, _ in _iter_blocks(text, lo, hi):
        if name == "target_variant":
            yield blo, bhi
        else:
            yield from _iter_target_variants(text, blo, bhi)


@dataclass
class Finding:
    line: int
    kind: str  # unknown_hull | unknown_slot | unknown_module | category_mismatch
    message: str


def check_naval_variants(
    content: str,
    hull_slots: Dict[str, Optional[Dict[str, Optional[Set[str]]]]],
    module_category: Dict[str, str],
    known_categories: Set[str],
) -> List[Finding]:
    """Validate every ``category = naval`` variant's module assignments against
    its hull's slot rules. Returns findings sorted by line."""
    text = blank_comments(content)
    findings: List[Finding] = []
    for tname, tlo, thi, _ in _iter_blocks(text, 0, len(text)):
        if _scalar(text, tlo, thi, "category") != "naval":
            continue
        for vlo, vhi in _iter_target_variants(text, tlo, thi):
            hull = _scalar(text, vlo, vhi, "type")
            mods_span = None
            for key, mlo, mhi, _ in _iter_blocks(text, vlo, vhi):
                if key == "modules":
                    mods_span = (mlo, mhi)
                    break
            if mods_span is None or hull is None:
                continue
            if hull not in hull_slots:
                findings.append(
                    Finding(
                        text.count("\n", 0, mods_span[0]) + 1,
                        "unknown_hull",
                        f"variant type '{hull}' is not a defined ship hull",
                    )
                )
                continue
            slots = hull_slots[hull]
            if slots is None:
                continue
            for slot, refs, off in _parse_module_assignments(text, *mods_span):
                line = text.count("\n", 0, off) + 1
                if slot not in slots:
                    findings.append(
                        Finding(
                            line,
                            "unknown_slot",
                            f"hull '{hull}' has no slot '{slot}' — module "
                            f"assignment is silently ignored",
                        )
                    )
                    continue
                allowed = slots[slot]
                for ref in refs:
                    if ref == "empty":
                        continue
                    if ref in module_category:
                        eff = module_category[ref]
                    elif ref in known_categories:
                        eff = ref
                    else:
                        findings.append(
                            Finding(
                                line,
                                "unknown_module",
                                f"'{ref}' in slot '{slot}' on hull '{hull}' is "
                                f"neither a defined module nor a module category",
                            )
                        )
                        continue
                    if allowed is not None and eff not in allowed:
                        findings.append(
                            Finding(
                                line,
                                "category_mismatch",
                                f"'{ref}' (category {eff}) is not allowed in slot "
                                f"'{slot}' on hull '{hull}'; that slot accepts "
                                f"{{{', '.join(sorted(allowed))}}}",
                            )
                        )
    findings.sort(key=lambda f: f.line)
    return findings


def build_indexes(
    hull_texts: List[str], module_texts: List[str]
) -> Tuple[
    Dict[str, Optional[Dict[str, Optional[Set[str]]]]], Dict[str, str], Set[str]
]:
    """Build (resolved hull->slots, module->category, known category names) from
    the raw text of the ship-hull and module definition files."""
    hulls: Dict[str, _Hull] = {}
    for text in hull_texts:
        hulls.update(parse_ship_hulls(strip_comments(text)))
    resolved = resolve_hull_slots(hulls)

    hull_categories: Set[str] = set()
    for slots in resolved.values():
        if not slots:
            continue
        for cats in slots.values():
            if cats:
                hull_categories.update(cats)

    module_category: Dict[str, str] = {}
    for text in module_texts:
        # Ship categories only appear in the ship module file, so a cheap
        # substring test skips parsing the tank/plane/arty module trees.
        if not any(c in text for c in hull_categories):
            continue
        module_category.update(parse_ship_modules(strip_comments(text)))

    known_categories = set(module_category.values()) | hull_categories
    return resolved, module_category, known_categories
