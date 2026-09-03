"""Index which stats each equipment token actually declares a base value for.

``equipment_bonus`` values are percentages of the equipment's base stat, so a
bonus naming a stat the target equipment never declares multiplies zero and does
nothing (upstream issue #3044: MANPADS carry no ``max_organisation``, yet several
MIO traits grant them +10% of it). Answering "is this bonus live?" needs the set
of stats every archetype in scope actually declares, which five separate sources
contribute to:

* ``equipments = { }`` entries — a variant's stats union into its ``archetype``,
  because MD re-states nearly every stat on every variant while inheritance runs
  the other way.
* modules — a hull declaring module slots gets its attack and armour from
  ``add_stats``/``multiply_stats`` blocks in ``modules/``, never from the hull.
  Only the modules its slots actually accept count: pooling every module would
  hand ships' ``max_organisation`` to tank chassis and hide the real findings.
* ``duplicate_archetypes`` — clones a whole family at load, so
  ``small_plane_cas_airframe`` exists in game while appearing in no
  ``equipments`` block; its ``for_each`` block adds stats the base lacks, and its
  ``substitute`` names the carrier twin.
* ``type`` categories — MIO ``equipment_type`` accepts a category as well as an
  archetype (``organizations/documentation.info``: "Equipment archetypes &
  categories"), so ``submarine`` has to resolve to the union of every hull
  declaring ``type = submarine``.
* ``common/equipment_groups/`` — the ``mio_cat_*`` tokens expand to member lists.

The index deliberately keeps structural keys (``year``, ``priority``,
``archetype``, ...) alongside the real stats. It is only ever membership-tested
against stat names read out of an ``equipment_bonus``, and no bonus stat shares a
name with a structural key, so filtering them would buy nothing and need
maintaining.
"""

import glob
import os
import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set

from equipment_module_slots import (
    EquipmentIndex,
    _depth0_text,
    _iter_blocks,
    _read_text,
    blank_comments,
    build_indexes,
)

EQUIPMENT_DIR = os.path.join("common", "units", "equipment")
EQUIPMENT_GROUP_DIR = os.path.join("common", "equipment_groups")

_MODULE_STAT_BLOCKS = ("add_stats", "multiply_stats", "add_average_stats")

# The value must sit on the key's own line. Nested blocks are stripped before
# this runs, so a greedy `\s*` would let `upgrades = {...}` swallow the next
# line's `reliability = 0.9` and silently drop that stat.
_ASSIGN_RE = re.compile(r"([A-Za-z_]\w*)[^\S\n]*=[^\S\n]*([^\s{}]+)")
_TOKEN_RE = re.compile(r"[A-Za-z_]\w*")


def _is_nonzero(value: str) -> bool:
    """Whether *value* gives the stat a base to apply a percentage to.

    A stat written as an explicit ``0`` is no better than an absent one — that is
    how ``infantry_weapons_type`` declares ``armor_value``. Anything that is not a
    plain number (a scripted constant such as ``@corvette_org``) is assumed live,
    since guessing it dead would invent findings.
    """
    try:
        return float(value) != 0.0
    except ValueError:
        return True


def _depth0_stats(text: str, lo: int, hi: int) -> Set[str]:
    """Keys assigned a non-zero scalar at brace-depth 0 of ``text[lo:hi]``."""
    return {
        key
        for key, value in _ASSIGN_RE.findall(_depth0_text(text, lo, hi))
        if _is_nonzero(value)
    }


def _set_stats(text: str, lo: int, hi: int) -> Set[str]:
    """Stats a ``for_each`` block gives a non-zero value via ``stat = { set = N }``."""
    stats: Set[str] = set()
    for stat, slo, shi, _ in _iter_blocks(text, lo, hi):
        m = re.search(r"\bset\s*=\s*(\S+)", text[slo:shi])
        if m and _is_nonzero(m.group(1)):
            stats.add(stat)
    return stats


def _type_tokens(text: str, lo: int, hi: int) -> Set[str]:
    """The ``type = X`` / ``type = { X Y }`` category tokens of one entry."""
    body = _depth0_text(text, lo, hi)
    m = re.search(r"\btype\s*=\s*([A-Za-z_]\w*)", body)
    tokens = {m.group(1)} if m else set()
    for name, blo, bhi, _ in _iter_blocks(text, lo, hi):
        if name == "type":
            tokens |= set(_TOKEN_RE.findall(text[blo:bhi]))
    return tokens


@dataclass
class _Entry:
    stats: Set[str]
    archetype: Optional[str]
    types: Set[str]


@dataclass(frozen=True)
class EquipmentStatIndex:
    """Lookup for equipment tokens used by ``equipment_type`` and
    ``equipment_bonus``."""

    stats: Dict[str, FrozenSet[str]]
    groups: Dict[str, List[str]]

    def resolve(self, token: str) -> Optional[FrozenSet[str]]:
        """Stats *token* declares a base for, or None when nothing defines it."""
        return self.stats.get(token)

    def expand(self, token: str) -> List[str]:
        """Member tokens of a ``mio_cat_*`` group, or ``[token]`` when it is not
        a group."""
        return list(self.groups.get(token, (token,)))


def _parse_equipment_file(text: str, entries: Dict[str, _Entry]) -> None:
    """Fold one ``common/units/equipment/*.txt`` file into *entries*."""
    n = len(text)
    for name, blo, bhi, _ in _iter_blocks(text, 0, n):
        if name == "equipments":
            for entry, elo, ehi, _ in _iter_blocks(text, blo, bhi):
                keys = _depth0_stats(text, elo, ehi)
                archetype = None
                am = re.search(
                    r"\barchetype\s*=\s*([A-Za-z_]\w*)", _depth0_text(text, elo, ehi)
                )
                if am:
                    archetype = am.group(1)
                existing = entries.get(entry)
                if existing is None:
                    entries[entry] = _Entry(
                        stats=keys,
                        archetype=archetype,
                        types=_type_tokens(text, elo, ehi),
                    )
                else:
                    existing.stats |= keys
                    existing.archetype = existing.archetype or archetype
                    existing.types |= _type_tokens(text, elo, ehi)


def _parse_duplicates(text: str) -> Dict[str, _Entry]:
    """Clone name -> the stats its ``for_each`` block adds on top of its base.

    ``substitute`` names the carrier-borne twin, which the engine generates from
    the same definition and which MIOs reference by that name.
    """
    dups: Dict[str, _Entry] = {}
    for name, blo, bhi, _ in _iter_blocks(text, 0, len(text)):
        if name != "duplicate_archetypes":
            continue
        for dup, dlo, dhi, _ in _iter_blocks(text, blo, bhi):
            body = _depth0_text(text, dlo, dhi)
            am = re.search(r"\barchetype\s*=\s*([A-Za-z_]\w*)", body)
            stats: Set[str] = set()
            for key, klo, khi, _ in _iter_blocks(text, dlo, dhi):
                if key == "for_each":
                    stats |= _set_stats(text, klo, khi)
            types = _type_tokens(text, dlo, dhi)
            names = [dup]
            sm = re.search(r"\bsubstitute\s*=\s*([A-Za-z_]\w*)", body)
            if sm:
                names.append(sm.group(1))
            for alias in names:
                dups[alias] = _Entry(
                    stats=set(stats),
                    archetype=am.group(1) if am else None,
                    types=set(types),
                )
    return dups


def _module_stats(texts: List[str]) -> Dict[str, Set[str]]:
    """Module name -> the stat names it can set."""
    stats: Dict[str, Set[str]] = {}
    for text in texts:
        for container, clo, chi, _ in _iter_blocks(text, 0, len(text)):
            if container != "equipment_modules":
                continue
            for module, mlo, mhi, _ in _iter_blocks(text, clo, chi):
                keys: Set[str] = set()
                for name, blo, bhi, _ in _iter_blocks(text, mlo, mhi):
                    if name in _MODULE_STAT_BLOCKS:
                        keys |= _depth0_stats(text, blo, bhi)
                if keys:
                    stats.setdefault(module, set()).update(keys)
    return stats


def _hull_module_stats(
    index: EquipmentIndex, module_stats: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:
    """Hull -> stats reachable through the modules its slots accept.

    A slot's ``allowed_module_categories`` is widened by whatever the modules it
    already accepts unlock (how a tank's gun picks its own ammunition), so the
    category set is expanded to a fixed point before the stats are collected.
    """
    by_category: Dict[str, Set[str]] = {}
    for module, category in index.module_category.items():
        keys = module_stats.get(module)
        if keys:
            by_category.setdefault(category, set()).update(keys)

    result: Dict[str, Set[str]] = {}
    for hull, slots in index.hull_slots.items():
        if not slots:
            continue
        categories: Set[str] = set()
        for allowed in slots.values():
            if allowed:
                categories |= allowed
        pending = set(categories)
        while pending:
            category = pending.pop()
            for unlocked in index.slot_unlocks.get(category, {}).values():
                new = unlocked - categories
                categories |= new
                pending |= new
        keys = set()
        for category in categories:
            keys |= by_category.get(category, set())
        if keys:
            result[hull] = keys
    return result


def _parse_groups(texts: List[str]) -> Dict[str, List[str]]:
    """``mio_cat_*`` group token -> member equipment tokens."""
    groups: Dict[str, List[str]] = {}
    for text in texts:
        for name, blo, bhi, _ in _iter_blocks(text, 0, len(text)):
            for key, klo, khi, _ in _iter_blocks(text, blo, bhi):
                if key == "equipment_type":
                    groups[name] = _TOKEN_RE.findall(text[klo:khi])
    return groups


def build_index(
    equipment_texts: List[str], module_texts: List[str], group_texts: List[str]
) -> EquipmentStatIndex:
    """Build the index from already-read file contents."""
    equipment_texts = [blank_comments(t) for t in equipment_texts]
    module_texts = [blank_comments(t) for t in module_texts]
    group_texts = [blank_comments(t) for t in group_texts]

    entries: Dict[str, _Entry] = {}
    for text in equipment_texts:
        _parse_equipment_file(text, entries)
    duplicates: Dict[str, _Entry] = {}
    for text in equipment_texts:
        duplicates.update(_parse_duplicates(text))

    module_index = build_indexes(equipment_texts, module_texts)
    hull_stats = _hull_module_stats(module_index, _module_stats(module_texts))

    stats: Dict[str, Set[str]] = {}
    types: Dict[str, Set[str]] = {}
    for name, entry in entries.items():
        root = entry.archetype or name
        for token in {name, root}:
            stats.setdefault(token, set()).update(entry.stats)
            stats[token] |= hull_stats.get(token, set())
            types.setdefault(token, set()).update(entry.types)

    # A clone inherits its base's stats; resolve after the base is complete.
    for name, entry in duplicates.items():
        base = stats.get(entry.archetype or "", set())
        stats.setdefault(name, set()).update(
            entry.stats | base | hull_stats.get(name, set())
        )
        types.setdefault(name, set()).update(
            entry.types | types.get(entry.archetype or "", set())
        )

    # A category resolves to the union of every equipment declaring it.
    for name, tokens in types.items():
        for category in tokens:
            stats.setdefault(category, set()).update(stats.get(name, set()))

    return EquipmentStatIndex(
        stats={k: frozenset(v) for k, v in stats.items()},
        groups=_parse_groups(group_texts),
    )


def build_equipment_stat_index(mod_path: str) -> EquipmentStatIndex:
    """Index every equipment token defined under *mod_path*."""
    equipment_dir = os.path.join(mod_path, EQUIPMENT_DIR)
    equipment_texts = [
        _read_text(fp)
        for fp in sorted(glob.iglob(os.path.join(equipment_dir, "*.txt")))
    ]
    module_texts = [
        _read_text(fp)
        for fp in sorted(glob.iglob(os.path.join(equipment_dir, "modules", "*.txt")))
    ]
    group_texts = [
        _read_text(fp)
        for fp in sorted(
            glob.iglob(os.path.join(mod_path, EQUIPMENT_GROUP_DIR, "*.txt"))
        )
    ]
    return build_index(equipment_texts, module_texts, group_texts)
