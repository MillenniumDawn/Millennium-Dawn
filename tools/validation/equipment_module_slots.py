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


@dataclass
class _Hull:
    slots: Optional[Dict[str, Optional[_Slot]]]
    archetype: Optional[str]
    inherit: bool


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
            if slots is None and not inherit and not am:
                continue
            hulls[hull] = _Hull(slots=slots, archetype=arch, inherit=inherit)
    return hulls


def parse_duplicate_archetypes(text: str) -> Dict[str, str]:
    """generated archetype name -> the archetype it copies.

    ``duplicate_archetypes`` clones a whole family at load: the tank-destroyer
    and SPAA chassis are copies of ``medium_tank_chassis``, so
    ``medium_tank_destroyer_chassis_2`` exists in game with the slots of
    ``medium_tank_chassis_2`` while appearing in no equipment file.
    """
    dups: Dict[str, str] = {}
    for name, blo, bhi, _ in _iter_blocks(text, 0, len(text)):
        if name != "duplicate_archetypes":
            continue
        for dup, dlo, dhi, _ in _iter_blocks(text, blo, bhi):
            m = re.search(r"\barchetype\s*=\s*(\w+)", _depth0_text(text, dlo, dhi))
            if m:
                dups[dup] = m.group(1)
    return dups


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


def parse_equipment_modules(
    text: str,
) -> Tuple[Dict[str, str], Dict[str, Dict[str, Set[str]]]]:
    """(module -> top-level ``category``, module -> slot unlocks).

    Nested ``module_category`` keys inside ``can_convert_from`` and
    ``module_count_limit`` are ignored — neither says what the module is.
    """
    mods: Dict[str, str] = {}
    unlocks: Dict[str, Dict[str, Set[str]]] = {}
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
    return mods, unlocks


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
    kind: str  # unknown_hull | unknown_slot | unknown_module | category_mismatch | missing_required_module
    message: str
    hull: str = ""


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

    if require_filled_slots:
        filled = {
            slot for slot, refs, _ in assignments if any(ref != "empty" for ref in refs)
        }
        _flag_required_slots(
            findings, slots, hull, text.count("\n", 0, mods_span[0]) + 1, filled
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


def _add_duplicate_hulls(
    resolved: Dict[str, Optional[Dict[str, Optional[_Slot]]]],
    duplicates: Dict[str, str],
) -> None:
    """Register each cloned archetype and its whole numbered family.

    The clone takes the source's name suffix, so ``medium_tank_chassis_2``
    becomes ``medium_tank_destroyer_chassis_2``. An explicit definition of the
    same name always wins.
    """
    for dup, src in duplicates.items():
        if resolved.get(src) is not None:
            resolved.setdefault(dup, resolved[src])
        prefix = src + "_"
        for name, slots in list(resolved.items()):
            if slots is not None and name.startswith(prefix):
                resolved.setdefault(dup + name[len(src) :], slots)


def build_indexes(hull_texts: List[str], module_texts: List[str]) -> EquipmentIndex:
    """Build the index from the raw text of the hull and module definition files."""
    hulls: Dict[str, _Hull] = {}
    duplicates: Dict[str, str] = {}
    ship_hulls: Set[str] = set()
    for text in hull_texts:
        stripped = strip_comments(text)
        parsed = parse_hulls(stripped)
        hulls.update(parsed)
        duplicates.update(parse_duplicate_archetypes(stripped))
        if any(marker in text for marker in _SHIP_HULL_MARKERS):
            ship_hulls.update(parsed)
    resolved = resolve_hull_slots(hulls)
    _add_duplicate_hulls(resolved, duplicates)

    module_category: Dict[str, str] = {}
    module_unlocks: Dict[str, Dict[str, Set[str]]] = {}
    for text in module_texts:
        mods, unlocks = parse_equipment_modules(strip_comments(text))
        module_category.update(mods)
        module_unlocks.update(unlocks)

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
        resolved, module_category, categories, slot_unlocks, ship_hulls
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
