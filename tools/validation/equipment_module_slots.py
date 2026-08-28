"""Cross-check equipment variant modules against hull slot rules.

The engine silently drops a module assigned to a slot that does not exist on the
hull, or whose module category is not in that slot's ``allowed_module_categories``
— the design loads but the AI builds a crippled ship (see upstream PR #2510,
which fixed ~200 screen-hull fire-control modules pointing at the plain
``module_fire_control_system_category`` where the slot only accepts the screen
category). Slot rules differ per hull, so every variant is validated against the
hull its ``type`` names. Ship hulls, tank chassis and plane airframes all follow
the same rules, so "hull" here means any of the three.

A slot value in ``target_variant.modules`` references either a concrete module
(resolved to its ``category``) or a category token directly (the
``{ module = <category> upgrade = current }`` form the generic designs use, which
means "current best module of this category"). Both are legal references; the
category — resolved or literal — must appear in the slot's allowed set.

Slots marked ``required = yes`` are enforced on top of the category rules: a
design that leaves one without a module — omitted, or an explicit ``= empty`` —
is refused outright. ``create_equipment_variant`` fails at effect time with
equipment_effects.cpp's 'Design lacks one or more required modules', and an AI
template that does it can never be matched by any design the AI produces.

Hulls also cap how many modules of a category (or a specific module) may be
equipped, via ``module_count_limit = { category = X count < N }``. ``count < 2``
means at most one. A module can further refuse a hull by equipment type:
``forbid_equipment_type`` fires when the hull has any of those types, and
``forbid_equipment_type_exact_match`` fires only when the hull's type set is
exactly that token (so ``armor`` forbids an MBT but not an amphibious clone).

Three things have to be resolved before a slot's allowed set is known. A module's
own ``allowed_module_categories`` is keyed by slot and widens that slot while the
module is equipped, which is how a tank's gun picks its own ammunition. An empty
``allowed_module_categories`` on the hull is therefore not the same as an absent
one — absent is unconstrained, empty means the modules decide. And
``duplicate_archetypes`` clones whole families at load, so hulls like
``medium_tank_destroyer_chassis_2`` exist in game while appearing in no file.
"""

import glob
import logging
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import find_matching_brace, strip_comments, strip_inline_comment

# Ship hulls live only in files carrying one of these engine hull-type markers,
# so the ship/land-air split needs no per-hull annotation.
_SHIP_HULL_MARKERS = ("screen_ship", "capital_ship", "= submarine", "= carrier")

_NAME_BLOCK_RE = re.compile(r"([A-Za-z_][\w.]*)\s*=\s*\{")
_ASSIGN_RE = re.compile(r"([A-Za-z_]\w*)\s*=\s*")
_CATEGORY_TOKEN_RE = re.compile(r"[A-Za-z_]\w*")


def _iter_blocks(text: str, lo: int, hi: int):
    """Yield ``(name, body_lo, body_hi, header_start)`` for each ``name = { ... }``
    block at the top level of the ``text[lo:hi]`` span (nested blocks skipped)."""
    pos = lo
    while pos < hi:
        m = _NAME_BLOCK_RE.search(text, pos, hi)
        if not m:
            return
        open_idx = text.index("{", m.end() - 1)
        close = find_matching_brace(text, open_idx)
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


def _first_at_depth0(
    text: str, lo: int, hi: int, key: str, value_pattern: str
) -> Optional[str]:
    """First ``key = <value_pattern>`` at brace-depth 0 of the ``text[lo:hi]`` span.
    Comments must already be blanked so ``#`` braces don't skew the depth count."""
    for m in re.compile(r"\b" + re.escape(key) + r"\s*=\s*" + value_pattern).finditer(
        text, lo, hi
    ):
        seg = text[lo : m.start()]
        if seg.count("{") == seg.count("}"):
            return m.group(1)
    return None


def _scalar(text: str, lo: int, hi: int, key: str) -> Optional[str]:
    """First ``key = value`` at brace-depth 0 of the ``text[lo:hi]`` span."""
    return _first_at_depth0(text, lo, hi, key, r"([A-Za-z_]\w*)")


def _quoted_scalar(text: str, lo: int, hi: int, key: str) -> Optional[str]:
    """First ``key = "value"`` at brace-depth 0 of the ``text[lo:hi]`` span."""
    return _first_at_depth0(text, lo, hi, key, r'"([^"]*)"')


def blank_comments(text: str) -> str:
    """Replace every ``#`` comment with spaces, preserving line lengths and
    offsets so character positions still map to the original line numbers."""
    lines = []
    for line in text.split("\n"):
        code = strip_inline_comment(line)
        lines.append(code + " " * (len(line) - len(code)))
    return "\n".join(lines)


# ---- hull slot rules -------------------------------------------------------


@dataclass
class _Slot:
    """One module_slots entry: its allowed categories and required-ness."""

    allowed: Optional[Set[str]]  # None when the slot declares no allowed set
    required: bool


def _parse_slot_categories(text: str, lo: int, hi: int) -> Dict[str, Optional[_Slot]]:
    """slot name -> :class:`_Slot` (allowed category set, required flag).

    ``allowed`` is None when the slot declares no
    ``allowed_module_categories``, meaning unconstrained.

    An empty block is not the same as an absent one: it means the hull permits
    nothing on its own and the slot is filled entirely by what the equipped
    modules unlock, which is how a tank's gun picks its own ammunition.
    """
    slots: Dict[str, Optional[_Slot]] = {}
    for slot, blo, bhi, _ in _iter_blocks(text, lo, hi):
        cats: Optional[Set[str]] = None
        required = bool(
            re.search(r"\brequired\s*=\s*yes\b", _depth0_text(text, blo, bhi))
        )
        for key, clo, chi, _ in _iter_blocks(text, blo, bhi):
            if key == "allowed_module_categories":
                cats = set(_CATEGORY_TOKEN_RE.findall(text[clo:chi]))
        slots[slot] = _Slot(cats, required)
    return slots


def _named_type_tokens(text: str, lo: int, hi: int, key: str) -> Set[str]:
    """Tokens from ``key = X`` or ``key = { X Y }`` at this block's top level.

    A ``key = { ... }`` block wins. Depth-0 stripping removes that block, so a
    scalar scan afterwards would swallow the next identifier (``for_each`` on
    duplicate_archetypes) as if it were the type.
    """
    tokens: Set[str] = set()
    found_block = False
    for name, blo, bhi, _ in _iter_blocks(text, lo, hi):
        if name == key:
            found_block = True
            tokens.update(_CATEGORY_TOKEN_RE.findall(text[blo:bhi]))
    if found_block:
        return tokens
    body = _depth0_text(text, lo, hi)
    m = re.search(r"\b" + re.escape(key) + r"\s*=\s*([A-Za-z_]\w*)", body)
    if m:
        tokens.add(m.group(1))
    return tokens


def _parse_count_limits(text: str, lo: int, hi: int) -> Dict[Tuple[str, str], int]:
    """``(kind, name) -> N`` for each ``module_count_limit`` with ``count < N``.

    ``kind`` is ``category`` or ``module``. Duplicate keys keep the stricter
    (smaller) N, which is what applying both limits would do anyway.
    """
    limits: Dict[Tuple[str, str], int] = {}
    for key, blo, bhi, _ in _iter_blocks(text, lo, hi):
        if key != "module_count_limit":
            continue
        body = text[blo:bhi]
        cnt = re.search(r"\bcount\s*<\s*(\d+)", body)
        if not cnt:
            continue
        try:
            n = int(cnt.group(1))
        except ValueError:
            continue
        cat = re.search(r"\bcategory\s*=\s*(\w+)", body)
        mod = re.search(r"\bmodule\s*=\s*(\w+)", body)
        if cat:
            ident: Tuple[str, str] = ("category", cat.group(1))
        elif mod:
            ident = ("module", mod.group(1))
        else:
            continue
        prev = limits.get(ident)
        limits[ident] = n if prev is None else min(prev, n)
    return limits


def _merge_count_limits(
    parent: Dict[Tuple[str, str], int], child: Dict[Tuple[str, str], int]
) -> Dict[Tuple[str, str], int]:
    out = dict(parent)
    for ident, n in child.items():
        prev = out.get(ident)
        out[ident] = n if prev is None else min(prev, n)
    return out


@dataclass
class _Hull:
    slots: Optional[Dict[str, Optional[_Slot]]]
    archetype: Optional[str]
    inherit: bool
    types: Set[str]
    count_limits: Dict[Tuple[str, str], int]


def parse_hulls(text: str) -> Dict[str, _Hull]:
    """Parse an equipment file into ``{hull: _Hull}``. Hulls with
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
            count_limits = _parse_count_limits(text, hlo, hhi)
            types = _named_type_tokens(text, hlo, hhi, "type")
            if slots is None and not inherit and not am:
                continue
            hulls[hull] = _Hull(
                slots=slots,
                archetype=arch,
                inherit=inherit,
                types=types,
                count_limits=count_limits,
            )
    return hulls


def parse_duplicate_archetypes(
    text: str,
) -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    """(generated archetype -> source, generated archetype -> type set).

    ``duplicate_archetypes`` clones a whole family at load: the tank-destroyer
    and SPAA chassis are copies of ``medium_tank_chassis``, so
    ``medium_tank_destroyer_chassis_2`` exists in game with the slots of
    ``medium_tank_chassis_2`` while appearing in no equipment file. The clone's
    ``type`` replaces the source's (``{ armor amphibious }``, not just ``armor``).
    """
    dups: Dict[str, str] = {}
    types: Dict[str, Set[str]] = {}
    for name, blo, bhi, _ in _iter_blocks(text, 0, len(text)):
        if name != "duplicate_archetypes":
            continue
        for dup, dlo, dhi, _ in _iter_blocks(text, blo, bhi):
            m = re.search(r"\barchetype\s*=\s*(\w+)", _depth0_text(text, dlo, dhi))
            if m:
                dups[dup] = m.group(1)
                types[dup] = _named_type_tokens(text, dlo, dhi, "type")
    return dups, types


def resolve_hull_slots(
    hulls: Dict[str, _Hull],
) -> Dict[str, Optional[Dict[str, Optional[_Slot]]]]:
    """hull -> resolved slot map, chasing ``module_slots = inherit`` to the
    archetype. None marks a hull whose slots cannot be resolved."""
    resolved: Dict[str, Optional[Dict[str, Optional[_Slot]]]] = {}

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


def resolve_hull_types(hulls: Dict[str, _Hull]) -> Dict[str, Set[str]]:
    """hull -> equipment type tokens, walking ``archetype`` when the hull
    itself does not declare ``type``."""
    resolved: Dict[str, Set[str]] = {}

    def resolve(name: str, seen: frozenset) -> Set[str]:
        if name in resolved:
            return resolved[name]
        hull = hulls.get(name)
        if hull is None:
            return set()
        if hull.types:
            resolved[name] = set(hull.types)
        elif hull.archetype and hull.archetype not in seen:
            resolved[name] = set(resolve(hull.archetype, seen | {name}))
        else:
            resolved[name] = set()
        return resolved[name]

    for name in hulls:
        resolve(name, frozenset())
    return resolved


def resolve_count_limits(
    hulls: Dict[str, _Hull],
) -> Dict[str, Dict[Tuple[str, str], int]]:
    """hull -> merged ``module_count_limit`` map, parent then child.

    A child that restates a limit keeps the stricter N; a child that omits
    the block inherits the archetype's limits in full. That matches hulls
    which only add a tighter cap on top of the archetype list.
    """
    resolved: Dict[str, Dict[Tuple[str, str], int]] = {}

    def resolve(name: str, seen: frozenset) -> Dict[Tuple[str, str], int]:
        if name in resolved:
            return resolved[name]
        hull = hulls.get(name)
        if hull is None:
            return {}
        parent: Dict[Tuple[str, str], int] = {}
        if hull.archetype and hull.archetype not in seen:
            parent = resolve(hull.archetype, seen | {name})
        resolved[name] = _merge_count_limits(parent, hull.count_limits)
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


def _module_slot_unlocks(text: str, lo: int, hi: int) -> Dict[str, Set[str]]:
    """slot -> categories this module adds to that slot while it is equipped.

    A module's own ``allowed_module_categories`` is keyed by slot, unlike a
    hull's flat token list: ``tank_base_tank_turret`` is what lets NERA armor
    into ``armor_type_slot``, and the turret-less designs cannot use it.
    """
    unlocks: Dict[str, Set[str]] = {}
    for key, blo, bhi, _ in _iter_blocks(text, lo, hi):
        if key != "allowed_module_categories":
            continue
        for slot, slo, shi, _ in _iter_blocks(text, blo, bhi):
            unlocks.setdefault(slot, set()).update(
                _CATEGORY_TOKEN_RE.findall(text[slo:shi])
            )
    return unlocks


@dataclass
class _ModuleIndex:
    category: Dict[str, str]
    unlocks: Dict[str, Dict[str, Set[str]]]
    forbid_types: Dict[str, Set[str]]
    forbid_exact: Dict[str, Set[str]]
    parent: Dict[str, str]


def parse_equipment_modules(text: str) -> _ModuleIndex:
    """Parse an ``equipment_modules`` file.

    Nested ``module_category`` keys inside ``can_convert_from`` and
    ``module_count_limit`` are ignored — neither says what the module is.
    """
    mods: Dict[str, str] = {}
    unlocks: Dict[str, Dict[str, Set[str]]] = {}
    forbid_types: Dict[str, Set[str]] = {}
    forbid_exact: Dict[str, Set[str]] = {}
    parent: Dict[str, str] = {}
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
            if not cat:
                continue
            mods[mod] = cat
            slot_unlocks = _module_slot_unlocks(text, mlo, mhi)
            if slot_unlocks:
                unlocks[mod] = slot_unlocks
            forbids = _named_type_tokens(text, mlo, mhi, "forbid_equipment_type")
            if forbids:
                forbid_types[mod] = forbids
            exact = _named_type_tokens(
                text, mlo, mhi, "forbid_equipment_type_exact_match"
            )
            if exact:
                forbid_exact[mod] = exact
            par = _scalar(text, mlo, mhi, "parent")
            if par:
                parent[mod] = par
    return _ModuleIndex(mods, unlocks, forbid_types, forbid_exact, parent)


def _inherit_module_forbids(
    declared: Dict[str, Set[str]], parents: Dict[str, str]
) -> Dict[str, Set[str]]:
    """Fill undeclared forbids from ``parent =``, so a child that restates
    nothing still carries the parent's type bans."""
    resolved: Dict[str, Set[str]] = {}

    def resolve(name: str, seen: frozenset) -> Set[str]:
        if name in resolved:
            return resolved[name]
        own = declared.get(name)
        parent = parents.get(name)
        if own is not None or parent is None or parent in seen:
            resolved[name] = set(own or ())
        else:
            resolved[name] = set(resolve(parent, seen | {name}))
        return resolved[name]

    for name in set(declared) | set(parents):
        resolve(name, frozenset())
    return {name: types for name, types in resolved.items() if types}


@dataclass
class EquipmentIndex:
    """Everything a variant check needs about the equipment tree."""

    hull_slots: Dict[str, Optional[Dict[str, Optional[_Slot]]]]
    module_category: Dict[str, str]
    known_categories: Set[str]
    # Keyed by module *and* by category: a generic AI design names the category
    # it wants the best available of, so anything in it may end up equipped.
    slot_unlocks: Dict[str, Dict[str, Set[str]]]
    ship_hulls: Set[str]
    hull_types: Dict[str, Set[str]]
    hull_count_limits: Dict[str, Dict[Tuple[str, str], int]]
    module_forbid_types: Dict[str, Set[str]]
    module_forbid_exact: Dict[str, Set[str]]


# ---- variant module assignments -------------------------------------------


def _refs_from_block(text: str, lo: int, hi: int) -> List[str]:
    body = text[lo:hi]
    ao = re.search(r"any_of\s*=\s*\{", body)
    if ao:
        inner_open = lo + ao.end() - 1
        inner_close = find_matching_brace(text, inner_open)
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
            close = find_matching_brace(text, j)
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


def _iter_named_blocks(text: str, lo: int, hi: int, name: str):
    """Yield ``(body_lo, body_hi)`` for every ``name = { ... }`` block at any
    nesting depth of the ``text[lo:hi]`` span."""
    for key, blo, bhi, _ in _iter_blocks(text, lo, hi):
        if key == name:
            yield blo, bhi
        else:
            yield from _iter_named_blocks(text, blo, bhi, name)


@dataclass
class Finding:
    line: int
    kind: str  # unknown_hull | unknown_slot | unknown_module | category_mismatch | missing_required_module | count_limit_exceeded | forbidden_equipment_type
    message: str
    hull: str = ""


def _module_forbidden(mod: str, hull_types: Set[str], index: EquipmentIndex) -> bool:
    if hull_types & index.module_forbid_types.get(mod, set()):
        return True
    exact = index.module_forbid_exact.get(mod, set())
    return bool(exact) and hull_types == exact


def _ref_forbidden(ref: str, hull_types: Set[str], index: EquipmentIndex) -> bool:
    """Whether *ref* cannot be equipped on a hull with *hull_types*.

    A category token is forbidden only when every module in that category is,
    because the AI (or ``upgrade = current``) can still pick an allowed one.
    """
    if ref == "empty":
        return False
    if ref in index.module_category:
        return _module_forbidden(ref, hull_types, index)
    if ref not in index.known_categories:
        return False
    members = [mod for mod, cat in index.module_category.items() if cat == ref]
    return bool(members) and all(
        _module_forbidden(mod, hull_types, index) for mod in members
    )


def _assignment_identities(
    refs: List[str], index: EquipmentIndex
) -> Optional[Tuple[Optional[str], Optional[str]]]:
    """Shared (module, category) of *refs*, or None when they disagree.

    Count limits only charge a slot when every option would count the same
    way, so an ``any_of`` mixing a limited category with an unlimited one
    is not a definite over-cap.
    """
    live = [ref for ref in refs if ref != "empty"]
    if not live:
        return None
    modules: Set[Optional[str]] = set()
    categories: Set[Optional[str]] = set()
    for ref in live:
        if ref in index.module_category:
            modules.add(ref)
            categories.add(index.module_category[ref])
        elif ref in index.known_categories:
            modules.add(None)
            categories.add(ref)
        else:
            return None
    module = next(iter(modules)) if len(modules) == 1 else None
    category = next(iter(categories)) if len(categories) == 1 else None
    if module is None and category is None:
        return None
    return module, category


def _flag_required_slots(
    findings: List[Finding],
    slots: Dict[str, Optional[_Slot]],
    hull: str,
    line: int,
    filled: Optional[Set[str]] = None,
) -> None:
    """Findings for every required slot the design leaves without a module.

    ``slot = empty`` leaves the slot without a module just like an omitted
    slot, so neither satisfies a ``required = yes`` entry.
    """
    for slot in sorted(slots):
        entry = slots[slot]
        if not entry or not entry.required:
            continue
        if filled is not None and slot in filled:
            continue
        findings.append(
            Finding(
                line,
                "missing_required_module",
                f"hull '{hull}' requires slot '{slot}' and the design leaves "
                f"it empty — the engine refuses the variant ('Design lacks one "
                f"or more required modules')",
                hull,
            )
        )


def _flag_count_limits(
    findings: List[Finding],
    index: EquipmentIndex,
    hull: str,
    assignments: List[Tuple[str, List[str], int]],
    line: int,
) -> None:
    limits = index.hull_count_limits.get(hull) or {}
    if not limits:
        return
    counts: Dict[Tuple[str, str], int] = {}
    for _, refs, _ in assignments:
        ident = _assignment_identities(refs, index)
        if ident is None:
            continue
        module, category = ident
        if module is not None:
            key = ("module", module)
            counts[key] = counts.get(key, 0) + 1
        if category is not None:
            key = ("category", category)
            counts[key] = counts.get(key, 0) + 1
    for ident, cap in sorted(limits.items()):
        used = counts.get(ident, 0)
        if used < cap:
            continue
        kind, name = ident
        findings.append(
            Finding(
                line,
                "count_limit_exceeded",
                f"hull '{hull}' limits {kind} '{name}' to fewer than {cap}, "
                f"but the design equips {used}",
                hull,
            )
        )


def _check_variant(
    text: str,
    vlo: int,
    vhi: int,
    index: EquipmentIndex,
    findings: List[Finding],
    *,
    require_known_hull: bool,
    require_filled_slots: bool,
) -> None:
    """Validate one variant body's ``modules`` block against its hull's slots.

    With *require_known_hull* an unresolvable ``type`` is a real error. Without
    it the variant is skipped, which is what a caller indexing only part of the
    equipment tree needs. With *require_filled_slots* every ``required = yes``
    slot of the hull must receive a module — the engine refuses the variant
    otherwise (equipment_effects.cpp, 'Design lacks one or more required
    modules').
    """
    hull = _scalar(text, vlo, vhi, "type")
    mods_span = None
    for key, mlo, mhi, _ in _iter_blocks(text, vlo, vhi):
        if key == "modules":
            mods_span = (mlo, mhi)
            break
    if mods_span is None:
        if require_filled_slots and hull is not None:
            slots = index.hull_slots.get(hull)
            if slots is not None:
                _flag_required_slots(
                    findings, slots, hull, text.count("\n", 0, vlo) + 1
                )
        return
    if hull is None:
        return
    if hull not in index.hull_slots:
        if require_known_hull:
            findings.append(
                Finding(
                    text.count("\n", 0, mods_span[0]) + 1,
                    "unknown_hull",
                    f"variant type '{hull}' is not a defined hull",
                    hull,
                )
            )
        return
    slots = index.hull_slots[hull]
    if slots is None:
        return

    assignments = _parse_module_assignments(text, *mods_span)
    # Modules widen each other's slots, so the whole design has to be read
    # before any one assignment can be judged.
    unlocked: Dict[str, Set[str]] = {}
    for _, refs, _ in assignments:
        for ref in refs:
            for slot, cats in index.slot_unlocks.get(ref, {}).items():
                unlocked.setdefault(slot, set()).update(cats)

    for slot, refs, off in assignments:
        line = text.count("\n", 0, off) + 1
        if slot not in slots:
            findings.append(
                Finding(
                    line,
                    "unknown_slot",
                    f"hull '{hull}' has no slot '{slot}' — module "
                    f"assignment is silently ignored",
                    hull,
                )
            )
            continue
        entry = slots[slot]
        allowed = entry.allowed if entry else None
        if allowed is not None and slot in unlocked:
            allowed = allowed | unlocked[slot]
        for ref in refs:
            if ref == "empty":
                continue
            if ref in index.module_category:
                eff = index.module_category[ref]
            elif ref in index.known_categories:
                eff = ref
            else:
                findings.append(
                    Finding(
                        line,
                        "unknown_module",
                        f"'{ref}' in slot '{slot}' on hull '{hull}' is "
                        f"neither a defined module nor a module category",
                        hull,
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
                        hull,
                    )
                )

        hull_types = index.hull_types.get(hull, set())
        live_refs = [ref for ref in refs if ref != "empty"]
        if (
            hull_types
            and live_refs
            and all(_ref_forbidden(ref, hull_types, index) for ref in live_refs)
        ):
            shown = ", ".join(live_refs)
            findings.append(
                Finding(
                    line,
                    "forbidden_equipment_type",
                    f"'{shown}' in slot '{slot}' is forbidden on hull "
                    f"'{hull}' (types {{{', '.join(sorted(hull_types))}}})",
                    hull,
                )
            )

    if require_filled_slots:
        filled = {
            slot for slot, refs, _ in assignments if any(ref != "empty" for ref in refs)
        }
        _flag_required_slots(
            findings, slots, hull, text.count("\n", 0, mods_span[0]) + 1, filled
        )

    _flag_count_limits(
        findings,
        index,
        hull,
        assignments,
        text.count("\n", 0, mods_span[0]) + 1,
    )


def _check_all(
    content: str,
    index: EquipmentIndex,
    block: str,
    *,
    require_known_hull: bool,
    require_filled_slots: bool,
) -> List[Finding]:
    text = blank_comments(content)
    findings: List[Finding] = []
    for vlo, vhi in _iter_named_blocks(text, 0, len(text), block):
        _check_variant(
            text,
            vlo,
            vhi,
            index,
            findings,
            require_known_hull=require_known_hull,
            require_filled_slots=require_filled_slots,
        )
    findings.sort(key=lambda f: f.line)
    return findings


def check_target_variants(content: str, index: EquipmentIndex) -> List[Finding]:
    """Validate every ``target_variant`` design's module assignments against its
    hull's slot rules. Returns findings sorted by line.

    These are AI equipment templates, whose ``type`` always names a hull the mod
    defines, so an unresolvable one is reported rather than skipped. Required
    slots are checked too: a template that leaves one empty cannot be matched
    by any design the AI produces, so the roles it covers quietly degrade.
    """
    return _check_all(
        content,
        index,
        "target_variant",
        require_known_hull=True,
        require_filled_slots=True,
    )


def check_created_variants(content: str, index: EquipmentIndex) -> List[Finding]:
    """Same slot/category check for ``create_equipment_variant`` effects, which
    are what focus rewards, events, decisions and history files use.

    These blocks sit at arbitrary depth inside effect scopes. A variant whose
    ``type`` is not indexed is skipped: unlike an AI template, the effect is also
    used for equipment archetypes that declare no ``module_slots`` at all.

    A design that leaves a ``required = yes`` slot without a module — an omitted
    slot or an explicit ``= empty`` — is refused by the engine at effect time
    (equipment_effects.cpp: 'Invalid module setup. Design lacks one or more
    required modules'), so every required slot of a resolvable hull must be
    filled, including when the block carries no ``modules`` at all.
    """
    return _check_all(
        content,
        index,
        "create_equipment_variant",
        require_known_hull=False,
        require_filled_slots=True,
    )


def parse_variant_names(content: str) -> List[Tuple[str, str, int]]:
    """``(type, name, line)`` for every ``create_equipment_variant`` in *content*.

    Blocks missing either field are skipped: an OOB ``version_name`` lookup can
    never resolve to them.
    """
    text = blank_comments(content)
    out: List[Tuple[str, str, int]] = []
    for vlo, vhi in _iter_named_blocks(text, 0, len(text), "create_equipment_variant"):
        etype = _scalar(text, vlo, vhi, "type")
        name = _quoted_scalar(text, vlo, vhi, "name")
        if etype and name:
            out.append((etype, name, text.count("\n", 0, vlo) + 1))
    return out


def _clone_family(mapping: dict, duplicates: Dict[str, str]) -> None:
    """Copy each source hull's value onto the cloned archetype and its family.

    The clone takes the source's name suffix, so ``medium_tank_chassis_2``
    becomes ``medium_tank_destroyer_chassis_2``. An explicit definition of the
    same name always wins.
    """
    for dup, src in duplicates.items():
        if src in mapping:
            mapping.setdefault(dup, mapping[src])
        prefix = src + "_"
        src_len = len(src)
        for name, item in list(mapping.items()):
            if name.startswith(prefix):
                mapping.setdefault(dup + name[src_len:], item)


def _apply_duplicate_types(
    types: Dict[str, Set[str]],
    duplicates: Dict[str, str],
    dup_types: Dict[str, Set[str]],
) -> None:
    """Stamp each clone family with the duplicate's own type set."""
    for dup, src in duplicates.items():
        clone_types = set(dup_types.get(dup) or types.get(src, set()))
        types.setdefault(dup, set(clone_types))
        prefix = src + "_"
        src_len = len(src)
        for name in list(types):
            if name.startswith(prefix):
                types.setdefault(dup + name[src_len:], set(clone_types))


def build_indexes(hull_texts: List[str], module_texts: List[str]) -> EquipmentIndex:
    """Build the index from the raw text of the hull and module definition files."""
    hulls: Dict[str, _Hull] = {}
    duplicates: Dict[str, str] = {}
    dup_types: Dict[str, Set[str]] = {}
    ship_hulls: Set[str] = set()
    for text in hull_texts:
        stripped = strip_comments(text)
        parsed = parse_hulls(stripped)
        hulls.update(parsed)
        dups, extra_types = parse_duplicate_archetypes(stripped)
        duplicates.update(dups)
        dup_types.update(extra_types)
        if any(marker in text for marker in _SHIP_HULL_MARKERS):
            ship_hulls.update(parsed)
    resolved = resolve_hull_slots(hulls)
    hull_types = resolve_hull_types(hulls)
    count_limits = resolve_count_limits(hulls)
    _clone_family(resolved, duplicates)
    _clone_family(count_limits, duplicates)
    _apply_duplicate_types(hull_types, duplicates, dup_types)

    module_category: Dict[str, str] = {}
    module_unlocks: Dict[str, Dict[str, Set[str]]] = {}
    forbid_types: Dict[str, Set[str]] = {}
    forbid_exact: Dict[str, Set[str]] = {}
    parents: Dict[str, str] = {}
    for text in module_texts:
        parsed_mods = parse_equipment_modules(strip_comments(text))
        module_category.update(parsed_mods.category)
        module_unlocks.update(parsed_mods.unlocks)
        forbid_types.update(parsed_mods.forbid_types)
        forbid_exact.update(parsed_mods.forbid_exact)
        parents.update(parsed_mods.parent)
    forbid_types = _inherit_module_forbids(forbid_types, parents)
    forbid_exact = _inherit_module_forbids(forbid_exact, parents)

    slot_unlocks: Dict[str, Dict[str, Set[str]]] = {}
    categories: Set[str] = set(module_category.values())
    for mod, per_slot in module_unlocks.items():
        for ref in (mod, module_category[mod]):
            by_slot = slot_unlocks.setdefault(ref, {})
            for slot, cats in per_slot.items():
                by_slot.setdefault(slot, set()).update(cats)
                categories.update(cats)

    for slots in resolved.values():
        for slot_entry in (slots or {}).values():
            if slot_entry and slot_entry.allowed:
                categories.update(slot_entry.allowed)
    return EquipmentIndex(
        resolved,
        module_category,
        categories,
        slot_unlocks,
        ship_hulls,
        hull_types,
        count_limits,
        forbid_types,
        forbid_exact,
    )


def _read_text(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            return f.read()
    except OSError:
        logging.warning(
            "Could not read equipment file %s; its hulls/modules are not indexed",
            filepath,
        )
        return ""


def build_equipment_index(units_dir: str) -> EquipmentIndex:
    """Index every hull and module under *units_dir* (``common/units/equipment``)."""
    hull_texts = [
        _read_text(fp) for fp in sorted(glob.iglob(os.path.join(units_dir, "*.txt")))
    ]
    module_texts = [
        _read_text(fp)
        for fp in sorted(glob.iglob(os.path.join(units_dir, "modules", "*.txt")))
    ]
    return build_indexes(hull_texts, module_texts)
