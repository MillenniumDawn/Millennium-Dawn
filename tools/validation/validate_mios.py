#!/usr/bin/env python3
"""Validate Military-Industrial Organization definitions in Millennium Dawn.

Rules from .claude/docs/mio-reference.md + AGENTS.md:
  * org ids are TAG_organization_name (3-uppercase tag prefix); the shared
    GENERIC_/generic_ orgs are exempt
  * orgs pin their tag with allowed = { original_tag = TAG }
  * initial traits are named TAG_<...>_trait (or reference a shared
    generic_* trait from MD_generic_organization.txt)
  * trait grid x never exceeds 9 (negative x is the standard organic-layout
    first column; only the upper bound is a finding)
  * on_complete blocks are never empty (they need expenditure_for_mio_upgrade
    = yes or custom effects)
  * tree_header_text uses a localisation key, never a literal quoted string
  * tree header keys and trait/initial_trait names resolve to an English
    localisation key (TAG_<key> fallback included)
  * equipment_bonus stats reach equipment that declares a base for them, since
    the bonus is a percentage and 10% of an undeclared stat is still nothing
"""

import glob
import re
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

from equipment_module_slots import blank_comments
from equipment_stats import EquipmentStatIndex, build_equipment_stat_index
from validator_common import BaseValidator, run_validator_main

ORG_DIR = "common/military_industrial_organization/organizations"
POLICY_DIR = "common/military_industrial_organization/policies"
COMPANY_TRAIT_FILE = "common/country_leader/defense_company_traits.txt"

# Top-level org definition: `TAG_name = {` at column 0.
ORG_DEF_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE)
TAG_PREFIX_RE = re.compile(r"^([A-Z]{3})_")
SHARED_PREFIXES = ("GENERIC_", "generic_")

# Shared generic trees are wider than the country-MIO grid; their branch roots are
# absolute-positioned lane origins at x = 10..16 and their children stay relative.
X_BOUNDS_EXEMPT_ORGS = frozenset(
    {
        "generic_AFV_equipment_organization",
        "generic_air_equipment_organization",
        "generic_fixed_wing_and_helicopter_equipment_organization",
        "generic_infantry_equipment_organization",
        "generic_mixed_naval_equipment_organization",
        "generic_naval_equipment_organization",
        "generic_naval_light_equipment_organization",
        "generic_small_naval_Manufacturer",
        "generic_specialized_helicopter_aa_at_organization",
        "generic_tank_equipment_organization",
        "generic_utility_vehicle_manufacturer",
    }
)

ORIGINAL_TAG_RE = re.compile(r"\boriginal_tag\s*=\s*([A-Z][A-Z0-9_]{1,7})\b")
INITIAL_TRAIT_NAME_RE = re.compile(
    r"initial_trait\s*=\s*\{\s*name\s*=\s*([A-Za-z0-9_]+)"
)
POSITION_X_RE = re.compile(r"position\s*=\s*\{\s*x\s*=\s*(-?\d+)")
ON_COMPLETE_RE = re.compile(r"on_complete\s*=\s*\{([^{}]*)\}")

# The lookbehind keeps `text` from matching `tree_header_text` and `trait`
# from matching `initial_trait`.
HEADER_TEXT_RE = re.compile(r'(?<![A-Za-z0-9_])text\s*=\s*("[^"]*"|[^\s{}]+)')
NAME_RE = re.compile(r"(?<![A-Za-z0-9_])name\s*=\s*([A-Za-z0-9_]+)")
TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_])token\s*=\s*([A-Za-z0-9_]+)")

INCLUDE_RE = re.compile(r"(?<![A-Za-z0-9_])include\s*=\s*([A-Za-z0-9_]+)")
NAMED_BLOCK_RE = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")
BONUS_STAT_RE = re.compile(r"([A-Za-z_]\w*)[^\S\n]*=[^\S\n]*([^\s{}]+)")
EQUIPMENT_TOKEN_RE = re.compile(r"[A-Za-z_]\w*")

# Legal inside an equipment_bonus block but not equipment stats: these scale
# production of that archetype, so they have no base stat to be dead against.
NON_STAT_BONUS_KEYS = frozenset(
    {
        "instant",
        "production_cost_factor",
        "production_efficiency_gain_factor",
        "production_efficiency_cap_factor",
        "production_resource_penalty_factor",
    }
)

# Stats the engine gives a non-zero default, so a percentage bonus bites even
# though no MD equipment file declares a base. Empty until one is confirmed in
# game — an entry here silences a real finding, so it needs evidence, not a
# hunch. The open candidates are the naval *_factor keys
# (naval_light_gun_hit_chance_factor, naval_heavy_gun_hit_chance_factor,
# naval_torpedo_damage_reduction_factor, naval_weather_penalty_factor).
ZERO_BASE_EXEMPT_STATS: FrozenSet[str] = frozenset()

LocKeys = Union[FrozenSet[str], Set[str]]


def _block_spans(text: str) -> List[Tuple[int, int, str]]:
    """Yield (start, end, key) spans of every top-level `key = {` block."""
    spans = []
    for m in ORG_DEF_RE.finditer(text):
        depth = 1
        i = m.end()
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        spans.append((m.start(), i, m.group(1)))
    return spans


def _sub_blocks(body: str, keyword: str) -> List[Tuple[int, str]]:
    """Yield (start_offset_in_body, inner_text) for each `keyword = { ... }`."""
    pattern = re.compile(r"(?<![A-Za-z0-9_])" + keyword + r"\s*=\s*\{")
    blocks = []
    for m in pattern.finditer(body):
        depth = 1
        i = m.end()
        while i < len(body) and depth > 0:
            if body[i] == "{":
                depth += 1
            elif body[i] == "}":
                depth -= 1
            i += 1
        blocks.append((m.start(), body[m.end() : i - 1]))
    return blocks


def _named_sub_blocks(body: str) -> List[Tuple[str, int, str]]:
    """Yield (name, start_offset, inner_text) for each `name = { ... }` at the
    top level of *body*."""
    blocks = []
    i = 0
    n = len(body)
    while i < n:
        m = NAMED_BLOCK_RE.search(body, i)
        if not m:
            break
        depth = 1
        j = m.end()
        while j < n and depth > 0:
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
            j += 1
        blocks.append((m.group(1), m.start(), body[m.end() : j - 1]))
        i = j
    return blocks


class Validator(BaseValidator):
    TITLE = "MIOS"
    STAGED_EXTENSIONS = (".txt", ".yml")

    # org id -> comment-blanked body, for resolving `include` across files.
    _org_bodies: Dict[str, str] = {}

    def _org_files(self) -> List[str]:
        pattern = str(Path(self.mod_path) / ORG_DIR / "*.txt")
        files = sorted(glob.glob(pattern))
        if not self.staged_only:
            return files
        staged = {Path(f).resolve() for f in self.staged_files or []}
        localisation_dir = (Path(self.mod_path) / "localisation" / "english").resolve()
        if any(
            path.suffix == ".yml" and path.is_relative_to(localisation_dir)
            for path in staged
        ):
            return files
        # An equipment edit can strip the base stat a live bonus relied on, so it
        # has to re-scan every org, not just the ones staged alongside it.
        if any(self._is_equipment_input(path) for path in staged):
            return files
        return [f for f in files if Path(f).resolve() in staged]

    def _is_equipment_input(self, path: Path) -> bool:
        for directory in ("common/units/equipment", "common/equipment_groups"):
            root = (Path(self.mod_path) / directory).resolve()
            if path.is_relative_to(root):
                return True
        return False

    def _bonus_files(self) -> List[str]:
        """Files carrying the nested `equipment_bonus = { ARCHETYPE = {...} }`
        form: MIO policies and the country-leader company traits."""
        files = sorted(glob.glob(str(Path(self.mod_path) / POLICY_DIR / "*.txt")))
        company_traits = Path(self.mod_path) / COMPANY_TRAIT_FILE
        if company_traits.is_file():
            files.append(str(company_traits))
        if not self.staged_only:
            return files
        staged = {Path(f).resolve() for f in self.staged_files or []}
        if any(self._is_equipment_input(path) for path in staged):
            return files
        return [f for f in files if Path(f).resolve() in staged]

    def run_validations(self):
        files = self._org_files()
        bonus_files = self._bonus_files()
        if self.staged_only and not files and not bonus_files:
            self.log("No staged MIO files found — skipping MIO validation", "warning")
            return

        loc_keys = self._load_localisation_keys()
        equipment = build_equipment_stat_index(self.mod_path)
        self._org_bodies = {}

        org_count = 0
        for filepath in files:
            try:
                text = Path(filepath).read_text(encoding="utf-8")
            except OSError:
                continue
            rel = Path(filepath).relative_to(self.mod_path).as_posix()
            # blank_comments preserves offsets, so line numbers still line up
            # while a commented-out bonus can no longer be read as live script.
            clean = blank_comments(text)
            for start, end, org_id in _block_spans(text):
                org_count += 1
                body = text[start:end]
                self._org_bodies[org_id] = clean[start:end]
                body_offset = text.count("\n", 0, start)
                self._check_id(org_id, rel, body_offset)
                self._check_allowed(org_id, body, rel, body_offset)
                self._check_initial_trait(org_id, body, rel, body_offset)
                self._check_positions(org_id, body, rel, body_offset)
                self._check_on_complete(body, rel, body_offset)
                self._check_header_text(org_id, body, rel, body_offset, loc_keys)
                self._check_trait_localisation(org_id, body, rel, body_offset, loc_keys)
                self._check_org_equipment_bonus(
                    org_id, clean[start:end], rel, body_offset, equipment
                )

        for filepath in bonus_files:
            try:
                text = Path(filepath).read_text(encoding="utf-8")
            except OSError:
                continue
            rel = Path(filepath).relative_to(self.mod_path).as_posix()
            self._check_nested_equipment_bonus(blank_comments(text), rel, equipment)

        self.log(
            f"  Scanned {len(files) + len(bonus_files)} files | "
            f"{org_count} organizations"
        )

    @staticmethod
    def _is_shared(org_id: str) -> bool:
        return org_id.startswith(SHARED_PREFIXES)

    def _check_id(self, org_id: str, rel: str, body_offset: int):
        if self._is_shared(org_id):
            return
        if not TAG_PREFIX_RE.match(org_id):
            self.add_error(
                "org-id-format",
                f"MIO ID {org_id} must be TAG_organization_name",
                rel,
                body_offset + 1,
            )

    def _check_allowed(self, org_id: str, body: str, rel: str, body_offset: int):
        if self._is_shared(org_id):
            return
        m = TAG_PREFIX_RE.match(org_id)
        if not m:
            return
        tag = m.group(1)
        if not any(m2.group(1) == tag for m2 in ORIGINAL_TAG_RE.finditer(body)):
            self.add_error(
                "org-allowed-tag",
                f"MIO {org_id} must pin its tag with "
                f"allowed = {{ original_tag = {tag} }}",
                rel,
                body_offset + 1,
            )

    def _check_initial_trait(self, org_id: str, body: str, rel: str, body_offset: int):
        m = INITIAL_TRAIT_NAME_RE.search(body)
        if not m:
            return
        name = m.group(1)
        line = body_offset + body.count("\n", 0, m.start()) + 1
        if name.startswith("generic_"):
            return
        prefix = org_id.split("_", 1)[0]
        if not name.startswith(prefix + "_") or not name.endswith("_trait"):
            self.add_warning(
                "initial-trait-name",
                f"initial_trait name '{name}' must be {prefix}_<name>_trait "
                f"(e.g. {prefix}_norinco_trait)",
                rel,
                line,
            )

    def _check_positions(self, org_id: str, body: str, rel: str, body_offset: int):
        if org_id in X_BOUNDS_EXEMPT_ORGS:
            return
        for m in POSITION_X_RE.finditer(body):
            try:
                x = int(m.group(1))
            except ValueError:
                continue
            if x > 9:
                self.add_warning(
                    "trait-x-bounds",
                    f"trait position x = {x} must stay inside 0..9",
                    rel,
                    body_offset + body.count("\n", 0, m.start()) + 1,
                )

    @staticmethod
    def _owner_tag(org_id: str) -> Optional[str]:
        m = TAG_PREFIX_RE.match(org_id)
        return m.group(1) if m else None

    @staticmethod
    def _resolves(key: str, tag: Optional[str], loc_keys: LocKeys) -> bool:
        """The engine prefers TAG_<key> and falls back to the bare key."""
        return key in loc_keys or (tag is not None and f"{tag}_{key}" in loc_keys)

    def _check_header_text(
        self, org_id: str, body: str, rel: str, body_offset: int, loc_keys: LocKeys
    ):
        tag = self._owner_tag(org_id)
        for start, inner in _sub_blocks(body, "tree_header_text"):
            m = HEADER_TEXT_RE.search(inner)
            if not m:
                continue
            value = m.group(1)
            line = body_offset + body.count("\n", 0, start) + 1
            if value.startswith('"'):
                self.add_error(
                    "header-text-not-tokenized",
                    f"tree_header_text uses a literal string {value}; use a "
                    f"localisation key (e.g. {org_id}_mio_header_<slug>)",
                    rel,
                    line,
                )
            elif not self._resolves(value, tag, loc_keys):
                self.add_error(
                    "header-text-loc-missing",
                    f"tree_header_text key '{value}' has no English localisation entry",
                    rel,
                    line,
                )

    def _check_trait_localisation(
        self, org_id: str, body: str, rel: str, body_offset: int, loc_keys: LocKeys
    ):
        tag = self._owner_tag(org_id)
        blocks = _sub_blocks(body, "initial_trait") + _sub_blocks(body, "trait")
        for start, inner in blocks:
            name = NAME_RE.search(inner)
            token = TOKEN_RE.search(inner)
            line = body_offset + body.count("\n", 0, start) + 1
            if name:
                key = name.group(1)
                if self._resolves(key, tag, loc_keys):
                    continue
                message = f"trait name '{key}' has no English localisation entry"
            elif token:
                # Nameless traits fall back to <org_id>_<token>.
                key = f"{org_id}_{token.group(1)}"
                if self._resolves(key, tag, loc_keys):
                    continue
                message = (
                    f"trait '{token.group(1)}' has no name and no '{key}' "
                    f"localisation key; add name = {token.group(1)} plus a loc entry"
                )
            else:
                continue
            self.add_error("trait-loc-missing", message, rel, line)

    def _org_equipment_types(self, org_id: str, body: str) -> List[str]:
        """The equipment an org's traits apply to, following `include` for the
        thin orgs that carry nothing but a reference to a shared tree."""
        seen = set()
        while True:
            blocks = _sub_blocks(body, "equipment_type")
            if blocks:
                return EQUIPMENT_TOKEN_RE.findall(blocks[0][1])
            m = INCLUDE_RE.search(body)
            if not m or m.group(1) in seen:
                return []
            seen.add(org_id)
            org_id = m.group(1)
            included = self._org_bodies.get(org_id)
            if included is None:
                return []
            body = included

    def _resolve_scope(
        self, tokens: Sequence[str], equipment: EquipmentStatIndex, rel: str, line: int
    ) -> Optional[Dict[str, FrozenSet[str]]]:
        """Equipment token -> its declared stats, or None if any token is
        unresolvable.

        A partial scope would invent findings — every stat the missing equipment
        supplies would read as dead — so an unresolvable token reports itself and
        stops the bonus check for that block.
        """
        scope: Dict[str, FrozenSet[str]] = {}
        resolved = True
        for token in tokens:
            for member in equipment.expand(token):
                stats = equipment.resolve(member)
                if stats is None:
                    self.add_warning(
                        "mio-equipment-type-unknown",
                        f"equipment type '{member}' matches no equipment "
                        f"archetype, type category or mio_cat_ group",
                        rel,
                        line,
                    )
                    resolved = False
                else:
                    scope[member] = stats
        return scope if resolved else None

    def _report_bonus(
        self,
        inner: str,
        scope: Dict[str, FrozenSet[str]],
        rel: str,
        line_of,
    ):
        """Flag every stat in one equipment_bonus block that no equipment in
        *scope* declares a base for."""
        for m in BONUS_STAT_RE.finditer(inner):
            stat = m.group(1)
            if stat in NON_STAT_BONUS_KEYS or stat in ZERO_BASE_EXEMPT_STATS:
                continue
            dead = sorted(name for name, stats in scope.items() if stat not in stats)
            if not dead:
                continue
            line = line_of(m.start())
            if len(dead) == len(scope):
                self.add_warning(
                    "mio-bonus-no-base-stat",
                    f"equipment_bonus '{stat}' is inert: {', '.join(dead)} "
                    f"{'declares' if len(dead) == 1 else 'declare'} no base "
                    f"value for it, so a percentage bonus stays 0",
                    rel,
                    line,
                )
            else:
                live = sorted(set(scope) - set(dead))
                self.add_warning(
                    "mio-bonus-partial-base-stat",
                    f"equipment_bonus '{stat}' is inert on "
                    f"{', '.join(dead)} (no base value); it only applies to "
                    f"{', '.join(live)}",
                    rel,
                    line,
                )

    def _check_org_equipment_bonus(
        self,
        org_id: str,
        body: str,
        rel: str,
        body_offset: int,
        equipment: EquipmentStatIndex,
    ):
        org_types = self._org_equipment_types(org_id, body)
        if not org_types:
            return
        for start, inner in _sub_blocks(body, "initial_trait") + _sub_blocks(
            body, "trait"
        ):
            trait_line = body_offset + body.count("\n", 0, start) + 1
            limits = _sub_blocks(inner, "limit_to_equipment_type")
            tokens = (
                EQUIPMENT_TOKEN_RE.findall(limits[0][1]) if limits else list(org_types)
            )
            scope = self._resolve_scope(tokens, equipment, rel, trait_line)
            if not scope:
                continue
            inner_offset = body_offset + body.count("\n", 0, start)
            for bonus_start, bonus in _sub_blocks(inner, "equipment_bonus"):
                offset = inner_offset + inner.count("\n", 0, bonus_start)
                self._report_bonus(
                    bonus,
                    scope,
                    rel,
                    lambda pos, o=offset, b=bonus: o + b.count("\n", 0, pos) + 1,
                )

    def _check_nested_equipment_bonus(
        self, text: str, rel: str, equipment: EquipmentStatIndex
    ):
        """Policies and country-leader company traits key their equipment_bonus
        by archetype, so each nested block is its own scope."""
        for start, block in _sub_blocks(text, "equipment_bonus"):
            block_offset = text.count("\n", 0, start)
            for token, token_start, inner in _named_sub_blocks(block):
                line = block_offset + block.count("\n", 0, token_start) + 1
                scope = self._resolve_scope([token], equipment, rel, line)
                if not scope:
                    continue
                offset = block_offset + block.count("\n", 0, token_start)
                self._report_bonus(
                    inner,
                    scope,
                    rel,
                    lambda pos, o=offset, b=inner: o + b.count("\n", 0, pos) + 1,
                )

    def _check_on_complete(self, body: str, rel: str, body_offset: int):
        for m in ON_COMPLETE_RE.finditer(body):
            if m.group(1).strip():
                continue
            line = body_offset + body.count("\n", 0, m.start()) + 1
            self.add_error(
                "on-complete-empty",
                "on_complete is empty; add expenditure_for_mio_upgrade = yes "
                "or custom effects",
                rel,
                line,
            )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate MIO organization definitions")
