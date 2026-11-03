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
from typing import Dict, Iterable, List, NamedTuple, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import find_matching_brace, strip_comments, strip_inline_comment

# Ship hulls live only in files carrying one of these engine hull-type markers,
# so the ship/land-air split needs no per-hull annotation.
_SHIP_HULL_MARKERS = ("screen_ship", "capital_ship", "= submarine", "= carrier")

_NAME_BLOCK_RE = re.compile(r"([A-Za-z_][\w.]*)\s*=\s*\{")
_ASSIGN_RE = re.compile(r"([A-Za-z_]\w*)\s*[=<>]\s*")
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


_DEPTH_EVENT_RE = re.compile(r'["{}]')


def _depth0_text(text: str, lo: int, hi: int) -> str:
    """The ``text[lo:hi]`` span with every nested ``{...}`` block removed, so a
    regex sees only this block's own scalar assignments.

    A quote toggles string state unless a backslash precedes it, and braces
    inside a string are kept as text.
    """
    out: List[str] = []
    depth = 0
    in_str = False
    run_start = lo
    # Depth only changes at a quote or brace, so copy the runs between them.
    for m in _DEPTH_EVENT_RE.finditer(text, lo, hi):
        i = m.start()
        c = text[i]
        if depth == 0:
            out.append(text[run_start:i])
        run_start = i + 1
        if c == '"' or in_str:
            if c == '"' and text[i - 1] != "\\":
                in_str = not in_str
            if depth == 0:
                out.append(c)
        elif c == "{":
            depth += 1
        else:
            depth -= 1
    if depth == 0:
        out.append(text[run_start:hi])
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
    if "#" not in text:
        return text
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
        n = int(cnt.group(1))
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
    upgrades: Optional[Set[str]] = None
    parent: Optional[str] = None
    type_override: Optional[str] = None
    allowed_types: Optional[Set[str]] = None
    is_archetype: bool = False


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
            upgrades = None
            parent = None
            inherit = bool(re.search(r"\bmodule_slots\s*=\s*inherit", body))
            for key, klo, khi, _ in _iter_blocks(text, hlo, hhi):
                if key == "module_slots" and slots is None:
                    slots = _parse_slot_categories(text, klo, khi)
                elif key == "upgrades":
                    upgrades = set(_CATEGORY_TOKEN_RE.findall(text[klo:khi]))
            pm = re.search(r"\bparent\s*=\s*(\w+)", body)
            if pm:
                parent = pm.group(1)
            count_limits = _parse_count_limits(text, hlo, hhi)
            types = _named_type_tokens(text, hlo, hhi, "type")
            is_archetype = bool(re.search(r"\bis_archetype\s*=\s*yes\b", body))
            if (
                slots is None
                and not inherit
                and not am
                and upgrades is None
                and not is_archetype
            ):
                continue
            override = re.search(r"\btype_override\s*=\s*(\w+)", body)
            hulls[hull] = _Hull(
                slots=slots,
                archetype=arch,
                inherit=inherit,
                types=types,
                count_limits=count_limits,
                upgrades=upgrades,
                parent=parent,
                type_override=override.group(1) if override else None,
                allowed_types=_named_type_tokens(text, hlo, hhi, "allowed_types")
                or None,
                is_archetype=is_archetype,
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


def _resolve_up_chain(hulls: Dict[str, _Hull], field_name: str) -> dict:
    """hull -> the field's own value, else the nearest one up the ``parent``
    chain, else up the ``archetype`` chain. Hulls with no value anywhere are left
    out, so callers treat them as unknown."""

    def find(name: str):
        for link in ("parent", "archetype"):
            seen: Set[str] = set()
            cur: Optional[str] = name
            while cur and cur not in seen:
                seen.add(cur)
                hull = hulls.get(cur)
                if hull is None:
                    break
                if getattr(hull, field_name) is not None:
                    return getattr(hull, field_name)
                cur = getattr(hull, link)
        return None

    resolved = {name: find(name) for name in hulls}
    return {name: found for name, found in resolved.items() if found is not None}


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
    added_types: Dict[str, Set[str]]
    exact_category_forbids: Dict[str, Dict[str, Set[str]]]


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
    added_types: Dict[str, Set[str]] = {}
    exact_category: Dict[str, Dict[str, Set[str]]] = {}
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
            added = _named_type_tokens(text, mlo, mhi, "add_equipment_type")
            if added:
                added_types[mod] = added
            for key, blo, bhi, _ in _iter_blocks(text, mlo, mhi):
                if key == "forbid_equipment_type_exact_match_for_category":
                    for category, hull_type in re.findall(
                        r"(\w+)\s*=\s*(\w+)", text[blo:bhi]
                    ):
                        exact_category.setdefault(mod, {}).setdefault(
                            category, set()
                        ).add(hull_type)
    return _ModuleIndex(
        mods, unlocks, forbid_types, forbid_exact, parent, added_types, exact_category
    )


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
    hull_upgrades: Dict[str, Set[str]]
    hull_sources: Dict[str, str]
    non_modular_hulls: Set[str]
    archetypes: Set[str]
    upgrade_max: Dict[str, int]
    hull_type_overrides: Dict[str, str]
    hull_allowed_types: Dict[str, Set[str]]
    module_added_types: Dict[str, Set[str]]
    module_exact_category_forbids: Dict[str, Dict[str, Set[str]]]


# ---- variant module assignments -------------------------------------------


def _refs_from_block(text: str, lo: int, hi: int) -> List[str]:
    refs = []
    for name, blo, bhi, _ in _iter_blocks(text, lo, hi):
        if name == "any_of":
            refs.extend(_CATEGORY_TOKEN_RE.findall(text[blo:bhi]))
    refs.extend(
        match.group(1)
        for match in re.finditer(
            r"\bmodule\s*(?:=\s*[<>]?|[<>])\s*([A-Za-z_]\w*)",
            _depth0_text(text, lo, hi),
        )
    )
    return refs or _CATEGORY_TOKEN_RE.findall(text[lo:hi])


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
    last = text.rfind(name, lo, hi)
    for key, blo, bhi, header in _iter_blocks(text, lo, hi):
        if header > last:
            return
        if key == name:
            yield blo, bhi
        elif text.find(name, blo, bhi) != -1:
            yield from _iter_named_blocks(text, blo, bhi, name)


@dataclass
class Finding:
    line: int
    kind: str  # a key of KIND_LABELS
    message: str
    hull: str = ""


KIND_LABELS = {
    "unknown_hull": "unknown hull type",
    "archetype_type": "type is an archetype",
    "modules_on_non_modular": "modules on a non-modular type",
    "unknown_slot": "slot not on hull",
    "unknown_module": "unknown module reference",
    "category_mismatch": "module category not allowed in slot",
    "missing_required_module": "required slot left empty",
    "count_limit_exceeded": "module count limit exceeded",
    "forbidden_equipment_type": "module forbidden on hull type",
    "type_override_role": "main weapon sets a type the hull does not allow",
    "exact_category_conflict": "modules conflict on hull type",
    "unsupported_upgrade": "unsupported upgrade",
    "undefined_upgrade": "undefined upgrade",
    "invalid_upgrade_level": "upgrade level out of range",
    "ship_upgrade": "upgrades on a ship",
    "role_icon_out_of_range": "role_icon_index out of range",
    "unknown_name_group": "unknown name_group",
    "name_group_country": "name_group for another country",
    "unknown_model": "unknown model",
}

# Their engine effect comes from tooling or designer behavior, not an engine
# error or documentation, so they advise and do not gate.
ADVISORY_KINDS = {
    "exact_category_conflict",
    "ship_upgrade",
    "role_icon_out_of_range",
    "name_group_country",
}


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


_Assignments = List[Tuple[str, List[str], int]]


def _type_override_problems(
    index: EquipmentIndex, hull: str, assignments: _Assignments
) -> Iterable[Tuple[int, str, str]]:
    """A plane's ``type_override`` module sets its type, which must be one the
    hull's ``allowed_types`` lists. A category reference can still resolve to a
    fitting module, so only literal modules count."""
    override = index.hull_type_overrides.get(hull)
    allowed = index.hull_allowed_types.get(hull)
    if not override or not allowed:
        return
    allowed = allowed | index.hull_types.get(hull, set())
    for slot, refs, off in assignments:
        live = [ref for ref in refs if ref != "empty"]
        added = [index.module_added_types.get(ref) for ref in live]
        if slot != override or not live or not all(added):
            continue
        if any(types & allowed for types in added if types):
            continue
        gives = sorted(set().union(*(types for types in added if types)))
        yield (
            off,
            "type_override_role",
            f"'{', '.join(live)}' in {slot} sets type {'/'.join(gives)}, which "
            f"hull '{hull}' does not allow ({', '.join(sorted(allowed))})",
        )


def _exact_category_problems(
    index: EquipmentIndex, hull: str, assignments: _Assignments
) -> Iterable[Tuple[int, str, str]]:
    """``forbid_equipment_type_exact_match_for_category``: on a hull with exactly
    that one type, the module refuses every module of the named category."""
    hull_types = index.hull_types.get(hull, set())
    identities = [
        (slot, _assignment_identities(refs, index), off)
        for slot, refs, off in assignments
    ]
    for slot, identity, _ in identities:
        rules = index.module_exact_category_forbids.get(identity[0]) if identity else {}
        if not identity or not rules:
            continue
        for other_slot, other, off in identities:
            if other_slot == slot or not other:
                continue
            if rules.get(other[1], set()) & hull_types and len(hull_types) == 1:
                yield (
                    off,
                    "exact_category_conflict",
                    f"'{identity[0]}' in {slot} refuses category {other[1]} "
                    f"in {other_slot} on hull '{hull}'",
                )


def _check_variant(
    text: str,
    vlo: int,
    vhi: int,
    index: EquipmentIndex,
    findings: List[Finding],
) -> None:
    """Validate one variant body's ``type`` and ``modules`` against its hull.

    Every ``required = yes`` slot must receive a module: the engine refuses the
    variant otherwise (equipment_effects.cpp, 'Design lacks one or more required
    modules').
    """
    hull = _first_at_depth0(text, vlo, vhi, "type", r"([A-Za-z_]\w*)(?![\w:.@\[$])")
    if hull is None:
        return
    mods_span = None
    for key, mlo, mhi, _ in _iter_blocks(text, vlo, vhi):
        if key == "modules":
            mods_span = (mlo, mhi)
            break
    mods_line = text.count("\n", 0, mods_span[0] if mods_span else vlo) + 1
    if hull not in index.hull_slots:
        spelling = next(
            (name for name in index.hull_slots if name.lower() == hull.lower()), None
        )
        hint = f"; the definition is spelled '{spelling}'" if spelling else ""
        findings.append(
            Finding(
                mods_line,
                "unknown_hull",
                f"variant type '{hull}' is not a defined hull{hint}",
                hull,
            )
        )
        return
    if hull in index.archetypes:
        findings.append(
            Finding(
                mods_line,
                "archetype_type",
                f"variant type '{hull}' is an archetype; name a concrete type",
                hull,
            )
        )
    assignments = _parse_module_assignments(text, *mods_span) if mods_span else []
    if assignments and hull in index.non_modular_hulls:
        findings.append(
            Finding(
                mods_line,
                "modules_on_non_modular",
                f"type '{hull}' has no module slots; the engine ignores its modules",
                hull,
            )
        )
        return
    slots = index.hull_slots[hull]
    if slots is None:
        return
    if mods_span is None:
        _flag_required_slots(findings, slots, hull, mods_line)
        return

    # Modules widen each other's slots, so the whole design has to be read
    # before any one assignment can be judged.
    unlocked: Dict[str, Set[str]] = {}
    hull_types = index.hull_types.get(hull, set())
    for _, refs, _ in assignments:
        for ref in refs:
            modules = (
                [ref]
                if ref in index.module_category
                else [
                    mod
                    for mod, category in index.module_category.items()
                    if category == ref
                ]
            )
            for module in modules:
                if not _module_forbidden(module, hull_types, index):
                    for slot, cats in index.slot_unlocks.get(module, {}).items():
                        unlocked.setdefault(slot, set()).update(cats)

    for slot, refs, off in assignments:
        line = mods_line + text.count("\n", mods_span[0], off)
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

    filled = {
        slot for slot, refs, _ in assignments if any(ref != "empty" for ref in refs)
    }
    _flag_required_slots(findings, slots, hull, mods_line, filled)

    _flag_count_limits(findings, index, hull, assignments, mods_line)
    for off, kind, message in (
        *_type_override_problems(index, hull, assignments),
        *_exact_category_problems(index, hull, assignments),
    ):
        line = mods_line + text.count("\n", mods_span[0], off)
        findings.append(Finding(line, kind, message, hull))


class CreatedVariants(NamedTuple):
    """Comment-blanked file text and the body span of each created variant."""

    text: str
    spans: List[Tuple[int, int]]


def created_variant_spans(content: str) -> CreatedVariants:
    """Walk *content* once for every ``create_equipment_variant`` block.

    The created-variant checks and the name index all read this one result.
    """
    text = blank_comments(content)
    return CreatedVariants(
        text, list(_iter_named_blocks(text, 0, len(text), "create_equipment_variant"))
    )


def _check_all(
    text: str, spans: Iterable[Tuple[int, int]], index: EquipmentIndex
) -> List[Finding]:
    findings: List[Finding] = []
    for vlo, vhi in spans:
        _check_variant(text, vlo, vhi, index, findings)
    findings.sort(key=lambda f: f.line)
    return findings


def _target_variant_spans(text: str) -> Iterable[Tuple[int, int]]:
    return _iter_named_blocks(text, 0, len(text), "target_variant")


def check_target_variants(content: str, index: EquipmentIndex) -> List[Finding]:
    """Validate every ``target_variant`` design's type and module assignments
    against its hull. Returns findings sorted by line.

    A template that leaves a required slot empty cannot be matched by any design
    the AI produces, so the roles it covers quietly degrade.
    """
    text = blank_comments(content)
    return _check_all(text, _target_variant_spans(text), index)


def check_created_variants(
    variants: CreatedVariants, index: EquipmentIndex
) -> List[Finding]:
    """Same check for ``create_equipment_variant`` effects, which are what focus
    rewards, events, decisions and history files use. These blocks sit at
    arbitrary depth inside effect scopes.

    A design that leaves a ``required = yes`` slot without a module — an omitted
    slot or an explicit ``= empty`` — is refused by the engine at effect time
    (equipment_effects.cpp: 'Invalid module setup. Design lacks one or more
    required modules'), so every required slot of a resolvable hull must be
    filled, including when the block carries no ``modules`` at all.
    """
    return _check_all(variants.text, variants.spans, index)


_UPGRADE_ENTRY_RE = re.compile(r"([A-Za-z_]\w*)\s*=\s*(\{|-?\d+)?")
_WEIGHT_TERM_RE = re.compile(r"\b(?:base|add)\s*=\s*(-?\d+)")


def _weight_terms(text: str, lo: int, hi: int) -> int:
    return sum(int(value) for value in _WEIGHT_TERM_RE.findall(text, lo, hi))


def _weighted_levels(text: str, lo: int, hi: int) -> List[int]:
    """Levels a weighted upgrade proves it reaches: with and without its one
    ``modifier``. Several modifiers may exclude each other and a factor scales,
    so those prove nothing."""
    blocks = list(_iter_blocks(text, lo, hi))
    if (
        len(blocks) > 1
        or any(key != "modifier" for key, *_ in blocks)
        or "factor" in text[lo:hi]
    ):
        return []
    total = _weight_terms(text, lo, hi)
    conditional = sum(_weight_terms(text, blo, bhi) for _, blo, bhi, _ in blocks)
    return [total - conditional, total]


def _upgrade_entries(
    text: str, lo: int, hi: int
) -> Iterable[Tuple[str, List[int], int]]:
    """(upgrade, levels it can reach, offset) per entry."""
    pos = lo
    while True:
        m = _UPGRADE_ENTRY_RE.search(text, pos, hi)
        if not m:
            return
        pos = m.end()
        levels = [0]
        if m.group(2) == "{":
            close = find_matching_brace(text, m.end() - 1)
            levels = _weighted_levels(text, m.end(), close if close != -1 else hi)
            pos = close + 1 if close != -1 else hi
        elif m.group(2):
            levels = [int(m.group(2))]
        yield m.group(1), levels, m.start()


def _upgrade_findings(
    text: str, spans: Iterable[Tuple[int, int]], index: EquipmentIndex
) -> List[Finding]:
    findings: List[Finding] = []
    for vlo, vhi in spans:
        etype = _scalar(text, vlo, vhi, "type")
        if not etype:
            continue
        allowed = index.hull_upgrades.get(etype)
        name = _quoted_scalar(text, vlo, vhi, "name")
        label = f"'{name}' - " if name else ""
        for key, ulo, uhi, _ in _iter_blocks(text, vlo, vhi):
            if key != "upgrades":
                continue
            entries = list(_upgrade_entries(text, ulo, uhi))
            if entries and etype in index.ship_hulls:
                findings.append(
                    Finding(
                        text.count("\n", 0, ulo) + 1,
                        "ship_upgrade",
                        f"{label}ship '{etype}' sets upgrades; the ship designer "
                        "has none, so the engine likely ignores them",
                        etype,
                    )
                )
            for upgrade, levels, offset in entries:
                line = text.count("\n", 0, offset) + 1
                cap = index.upgrade_max.get(upgrade)
                if index.upgrade_max and cap is None:
                    findings.append(
                        Finding(
                            line,
                            "undefined_upgrade",
                            f"{label}upgrade '{upgrade}' is not defined in "
                            "common/units/equipment/upgrades",
                            etype,
                        )
                    )
                    continue
                if allowed is not None and upgrade not in allowed:
                    findings.append(
                        Finding(
                            line,
                            "unsupported_upgrade",
                            f"{label}Type '{etype}' does not support upgrades "
                            f"'{upgrade}'",
                            etype,
                        )
                    )
                invalid = [
                    level
                    for level in levels
                    if level < 0 or (cap is not None and level > cap)
                ]
                if invalid:
                    findings.append(
                        Finding(
                            line,
                            "invalid_upgrade_level",
                            f"{label}upgrade '{upgrade}' level {invalid[0]} is "
                            f"outside 0 to max_level {cap}",
                            etype,
                        )
                    )
    findings.sort(key=lambda f: f.line)
    return findings


def check_created_variant_upgrades(
    variants: CreatedVariants, index: EquipmentIndex
) -> List[Finding]:
    """Flag ``upgrades`` entries the type does not list (the engine logs "Type 'X'
    does not support upgrades 'Y'"), entries no upgrade file defines, and levels
    outside the upgrade's ``max_level``. A type with no resolvable upgrade list
    skips the first rule only.
    """
    return _upgrade_findings(variants.text, variants.spans, index)


def check_target_variant_upgrades(content: str, index: EquipmentIndex) -> List[Finding]:
    """The same upgrade rules for AI ``target_variant`` designs."""
    text = blank_comments(content)
    return _upgrade_findings(text, _target_variant_spans(text), index)


# ---- variant references outside the equipment tree -------------------------

_AIR_TYPES = {
    "fighter",
    "cas",
    "naval_bomber",
    "tactical_bomber",
    "strategic_bomber",
    "interceptor",
    "air_transport",
    "suicide",
    "scout_plane",
}
_ROLE_STRIPS = (
    "GFX_naval_equipment_role_icons",
    "GFX_plane_niche_icon_strip",
    "GFX_niche_icon_strip",
)
_ENTITY_NAME_RE = re.compile(r'\bname\s*=\s*"?([^"\s{}]+)"?')


def entity_names_from_text(raw: str) -> Set[str]:
    """Lowercased ``entity`` names in one .asset or .gfx file."""
    text = blank_comments(raw)
    names: Set[str] = set()
    for lo, hi in _iter_named_blocks(text, 0, len(text), "entity"):
        match = _ENTITY_NAME_RE.search(_depth0_text(text, lo, hi))
        if match:
            names.add(match.group(1).lower())
    return names


def _role_strip(hull: str, index: EquipmentIndex) -> str:
    if hull in index.ship_hulls:
        return _ROLE_STRIPS[0]
    if index.hull_types.get(hull, set()) & _AIR_TYPES:
        return _ROLE_STRIPS[1]
    return _ROLE_STRIPS[2]


def role_strip_frames(gfx_texts: Iterable[str]) -> Dict[str, int]:
    """Frame count of each equipment role icon strip that declares one."""
    frames: Dict[str, int] = {}
    for raw in gfx_texts:
        for strip in _ROLE_STRIPS:
            if strip not in raw:
                continue
            match = re.search(
                rf'name\s*=\s*"?{strip}"?\s[^}}]*?noOfFrames\s*=\s*(\d+)',
                blank_comments(raw),
                re.IGNORECASE,
            )
            if match:
                frames[strip] = int(match.group(1))
    return frames


def _role_icon_finding(
    text: str,
    lo: int,
    hi: int,
    hull: Optional[str],
    index: EquipmentIndex,
    frames: Dict[str, int],
) -> Optional[Finding]:
    role = re.search(r"\brole_icon_index\s*=\s*(\d+)", _depth0_text(text, lo, hi))
    if not role or not hull:
        return None
    strip = _role_strip(hull, index)
    count = frames.get(strip)
    if count is None or 1 <= int(role.group(1)) <= count:
        return None
    return Finding(
        text.count("\n", 0, lo) + 1,
        "role_icon_out_of_range",
        f"role_icon_index = {role.group(1)} on '{hull}' is outside {strip} "
        f"(1 to {count})",
        hull,
    )


def check_target_variant_role_icons(
    content: str, index: EquipmentIndex, frames: Dict[str, int]
) -> List[Finding]:
    """AI designs carry ``role_icon_index`` beside their ``target_variant``."""
    text = blank_comments(content)
    findings: List[Finding] = []
    for _, glo, ghi, _ in _iter_blocks(text, 0, len(text)):
        for _, dlo, dhi, _ in _iter_blocks(text, glo, ghi):
            for key, vlo, vhi, _ in _iter_blocks(text, dlo, dhi):
                if key == "target_variant":
                    finding = _role_icon_finding(
                        text,
                        dlo,
                        dhi,
                        _scalar(text, vlo, vhi, "type"),
                        index,
                        frames,
                    )
                    if finding:
                        findings.append(finding)
                    break
    return findings


def check_created_variant_references(
    variants: CreatedVariants,
    index: EquipmentIndex,
    name_groups: Dict[str, Set[str]],
    entities: Optional[Set[str]],
    frames: Dict[str, int],
    country: Optional[str] = None,
) -> List[Finding]:
    """Check ``name_group``, ``model``, and ``role_icon_index``.

    *entities* is None when the workspace ships no entity files. *name_groups*
    maps each group to its ``for_countries``. *country* is the file's own tag.
    """
    text = variants.text
    findings: List[Finding] = []
    for vlo, vhi in variants.spans:
        hull = _scalar(text, vlo, vhi, "type")
        line = text.count("\n", 0, vlo) + 1
        body = _depth0_text(text, vlo, vhi)
        group = re.search(r'\bname_group\s*=\s*"?(\w+)"?', body)
        if group and name_groups:
            owners = name_groups.get(group.group(1))
            if owners is None:
                findings.append(
                    Finding(
                        line,
                        "unknown_name_group",
                        f"name_group '{group.group(1)}' is not defined in "
                        "common/units/names_ships",
                        hull or "",
                    )
                )
            elif country and owners and country not in owners:
                findings.append(
                    Finding(
                        line,
                        "name_group_country",
                        f"name_group '{group.group(1)}' is for "
                        f"{', '.join(sorted(owners))}, not {country}",
                        hull or "",
                    )
                )
        model = re.search(r'\bmodel\s*=\s*"?([^"\s{}]+)"?', body)
        if model and entities is not None and model.group(1).lower() not in entities:
            findings.append(
                Finding(
                    line,
                    "unknown_model",
                    f"model '{model.group(1)}' matches no entity in gfx/entities, "
                    "gfx/models, or vanilla",
                    hull or "",
                )
            )
        finding = _role_icon_finding(text, vlo, vhi, hull, index, frames)
        if finding:
            findings.append(finding)
    findings.sort(key=lambda f: f.line)
    return findings


def parse_variant_names(variants: CreatedVariants) -> List[Tuple[str, str, int]]:
    """``(type, name, line)`` for every ``create_equipment_variant`` block.

    Blocks missing either field are skipped: an OOB ``version_name`` lookup can
    never resolve to them.
    """
    text = variants.text
    out: List[Tuple[str, str, int]] = []
    for vlo, vhi in variants.spans:
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


def _parse_upgrade_levels(texts: Iterable[str]) -> Dict[str, int]:
    """upgrade -> ``max_level`` from the upgrade definition files."""
    levels: Dict[str, int] = {}
    for raw in texts:
        text = blank_comments(raw)
        for _, lo, hi, _ in _iter_blocks(text, 0, len(text)):
            for name, ulo, uhi, _ in _iter_blocks(text, lo, hi):
                level = re.search(
                    r"\bmax_level\s*=\s*(\d+)", _depth0_text(text, ulo, uhi)
                )
                if level:
                    levels[name] = int(level.group(1))
    return levels


def build_indexes(
    hull_texts: List[str],
    module_texts: List[str],
    upgrade_texts: Iterable[str] = (),
) -> EquipmentIndex:
    """Build the index from the raw text of the equipment definition files."""
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
    hull_upgrades = _resolve_up_chain(hulls, "upgrades")
    type_overrides = _resolve_up_chain(hulls, "type_override")
    allowed_types = _resolve_up_chain(hulls, "allowed_types")
    archetypes = {name for name, hull in hulls.items() if hull.is_archetype}
    archetypes.update(dup for dup, src in duplicates.items() if src in archetypes)
    hull_sources = {name: name for name in hulls}
    _clone_family(hull_sources, duplicates)
    non_modular_hulls = {
        name for name, hull in hulls.items() if hull.slots is None and not hull.inherit
    }
    non_modular_hulls.update(
        name for name, source in hull_sources.items() if source in non_modular_hulls
    )
    _clone_family(resolved, duplicates)
    _clone_family(count_limits, duplicates)
    _clone_family(hull_upgrades, duplicates)
    _clone_family(type_overrides, duplicates)
    _clone_family(allowed_types, duplicates)
    _apply_duplicate_types(hull_types, duplicates, dup_types)

    module_category: Dict[str, str] = {}
    module_unlocks: Dict[str, Dict[str, Set[str]]] = {}
    forbid_types: Dict[str, Set[str]] = {}
    forbid_exact: Dict[str, Set[str]] = {}
    added_types: Dict[str, Set[str]] = {}
    exact_category: Dict[str, Dict[str, Set[str]]] = {}
    parents: Dict[str, str] = {}
    for text in module_texts:
        parsed_mods = parse_equipment_modules(strip_comments(text))
        module_category.update(parsed_mods.category)
        module_unlocks.update(parsed_mods.unlocks)
        forbid_types.update(parsed_mods.forbid_types)
        forbid_exact.update(parsed_mods.forbid_exact)
        added_types.update(parsed_mods.added_types)
        exact_category.update(parsed_mods.exact_category_forbids)
        parents.update(parsed_mods.parent)
    forbid_types = _inherit_module_forbids(forbid_types, parents)
    forbid_exact = _inherit_module_forbids(forbid_exact, parents)
    added_types = _inherit_module_forbids(added_types, parents)

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
        hull_upgrades,
        hull_sources,
        non_modular_hulls,
        archetypes,
        _parse_upgrade_levels(upgrade_texts),
        type_overrides,
        allowed_types,
        added_types,
        exact_category,
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
    upgrade_texts = [
        _read_text(fp)
        for fp in sorted(glob.iglob(os.path.join(units_dir, "upgrades", "*.txt")))
    ]
    return build_indexes(hull_texts, module_texts, upgrade_texts)
