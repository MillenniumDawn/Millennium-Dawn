from copy import deepcopy
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Optional, cast

import pyradox

# Importing equipment puts tools/utils on sys.path for pyradox_utils.
from equipment import (
    AirEquipmentStats,
    Equipment,
    EquipmentStats,
    LandEquipmentStats,
    NavalEquipmentStats,
)
from pyradox_utils import (
    as_mapping,
    as_trait_list,
    dedupe_preserve_order,
    normalize_node,
    parse_file,
    stats_value,
    token_list,
)

_SPECIAL_INCLUDE_KEYS = {
    "include",
    "delete_included_values",
    "add_trait",
    "remove_trait",
    "override_trait",
}


def _field_names(cls: type[EquipmentStats]) -> set[str]:
    """Return dataclass field names for an EquipmentStats subclass."""
    return {item.name for item in fields(cls)}


_LAND_STAT_KEYS = _field_names(LandEquipmentStats)
_NAVAL_STAT_KEYS = _field_names(NavalEquipmentStats)
_AIR_STAT_KEYS = _field_names(AirEquipmentStats)
_BASE_STAT_KEYS = _field_names(EquipmentStats)

#########################
### Parsing functions ###
#########################


def _expand_equipment_tokens(
    tokens: list[str], equipment_groups: dict[str, "EquipmentGroup"]
) -> set[str]:
    """Expand group tokens to member equipment types, keeping raw tokens otherwise."""
    expanded: set[str] = set()
    for token in tokens:
        group = equipment_groups.get(token)
        if group is None:
            expanded.add(token)
            continue
        expanded.update(group.types)
    return expanded


def _iter_original_tags(value: object) -> list[str]:
    """Collect explicit original_tag values from an allowed-block structure."""
    normalized = normalize_node(value)
    found: list[str] = []  # Country tags collected from nested allowed blocks.

    def walk(node: object):
        if isinstance(node, dict):
            for key, inner in node.items():
                if key == "original_tag":
                    found.extend(token_list(inner))
                else:
                    walk(inner)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)

    walk(normalized)
    return dedupe_preserve_order(found)


def _iter_required_country_flags(*values: object) -> list[str]:
    """Collect positive has_country_flag checks from nested trigger structures."""
    found: list[str] = []  # Country flags collected from allowed/visible/available.

    def walk(node: object, *, negated: bool = False):
        normalized = normalize_node(node)
        if isinstance(normalized, dict):
            for key, inner in normalized.items():
                key_str = str(key)
                is_not_branch = key_str == "NOT"
                if key_str == "has_country_flag" and not negated:
                    found.extend(token_list(inner))
                    continue
                walk(inner, negated=negated or is_not_branch)
            return
        if isinstance(normalized, list):
            for item in normalized:
                walk(item, negated=negated)

    for value in values:
        walk(value)
    return dedupe_preserve_order(found)


def _stats_value(value: object) -> object:
    """Coerce common script scalar forms into Python bool/int/float values."""
    return stats_value(value)


def _detect_stats_class(stat_keys: set[str]) -> type[EquipmentStats]:
    """Choose the most specific stats class matching the provided stat keys."""
    if stat_keys <= _BASE_STAT_KEYS:
        return EquipmentStats
    if stat_keys & _NAVAL_STAT_KEYS:
        return NavalEquipmentStats
    if stat_keys & _AIR_STAT_KEYS:
        return AirEquipmentStats
    if stat_keys & _LAND_STAT_KEYS:
        return LandEquipmentStats
    return EquipmentStats


def _parse_equipment_bonus(
    value: object,
    stats_class: Optional[type[EquipmentStats]] = None,
) -> EquipmentStats:
    """Parse a trait equipment_bonus block into an EquipmentStats instance."""
    mapping = normalize_node(value)
    if not isinstance(mapping, dict):
        return stats_class() if stats_class is not None else EquipmentStats()

    raw_stats = {
        str(key): _stats_value(inner) for key, inner in mapping.items()
    }  # Raw stat key -> normalized value.
    selected_class = stats_class or _detect_stats_class(set(raw_stats))
    allowed = {
        item.name for item in fields(selected_class)
    }  # Fields accepted by the selected stats dataclass.
    stat_values: dict[str, object] = {
        key: inner for key, inner in raw_stats.items() if key in allowed
    }  # Filtered stat key -> value payload passed to dataclass constructor.
    return selected_class(**cast(Any, stat_values))


def _detect_stats_class_from_equipment_scope(
    applies_to: set[str],
    equipment_index: dict[str, Equipment],
) -> Optional[type[EquipmentStats]]:
    """Infer the best stats class from concrete equipment matched by scope tokens."""
    resolved_classes: set[type[EquipmentStats]] = (
        set()
    )  # Stats dataclass types observed in applies_to scope.
    for token in applies_to:
        equipment = equipment_index.get(token)
        if equipment is None:
            continue
        resolved_classes.add(type(equipment.stats))

    if len(resolved_classes) == 1:
        return next(iter(resolved_classes))
    if len(resolved_classes) > 1:
        return EquipmentStats
    return None


def _merge_trait(
    base: dict[str, object], override: dict[str, object]
) -> dict[str, object]:
    """Merge override_trait data into a base trait payload."""
    merged = deepcopy(base)

    delete_values = token_list(override.get("delete_included_values"))
    for key in delete_values:
        merged.pop(key, None)

    for key, value in override.items():
        if key in {"token", "delete_included_values"}:
            continue
        merged[str(key)] = deepcopy(cast(object, value))
    return merged


def _apply_trait_operations(data: dict[str, object]) -> dict[str, object]:
    """Apply remove/override/add trait operations to one resolved org payload."""
    traits = as_trait_list(
        data.get("trait")
    )  # Mutable list of trait blocks for this resolved organization.

    remove_tokens = set(token_list(data.get("remove_trait")))  # Trait tokens to remove.
    if remove_tokens:
        traits = [
            trait
            for trait in traits
            if str(normalize_node(trait.get("token", ""))) not in remove_tokens
        ]

    overrides = as_trait_list(
        data.get("override_trait")
    )  # Override trait blocks keyed by token.
    for override in overrides:
        token = str(normalize_node(override.get("token", "")))
        if not token:
            continue

        replaced = False
        for index, trait in enumerate(traits):
            if str(normalize_node(trait.get("token", ""))) != token:
                continue
            traits[index] = _merge_trait(trait, override)
            replaced = True
            break

        if not replaced:
            traits.append(_merge_trait({}, override))

    traits.extend(as_trait_list(data.get("add_trait")))

    mutated = deepcopy(
        data
    )  # Final resolved organization block after trait operations.
    if traits:
        mutated["trait"] = traits
    else:
        mutated.pop("trait", None)

    for key in ("add_trait", "remove_trait", "override_trait"):
        mutated.pop(key, None)
    return mutated


def _resolve_data(
    org_id: str,
    raw_orgs: dict[str, pyradox.Tree],
    cache: dict[str, dict[str, object]],
    active: set[str],
) -> dict[str, object]:
    """Resolve the data for a given organization ID.

    If the organization does not include another organization, its data is used as-is.

    If the organization includes another organization, the included data is merged recursively.
    Applies include chains recursively, supports include-cycle detection, and
    executes trait operations (add/remove/override) on the effective tree.
    """
    if org_id in cache:
        return deepcopy(cache[org_id])
    if org_id in active:
        chain = " -> ".join([*active, org_id])
        raise ValueError(f"MIO include cycle detected: {chain}")
    if org_id not in raw_orgs:
        raise KeyError(f"Unknown MIO include target: {org_id}")

    active.add(org_id)
    data = as_mapping(raw_orgs[org_id])  # Raw organization payload for org_id.
    include_name = data.get("include")

    if include_name is not None:
        resolved = _resolve_inclusion(
            org_id, raw_orgs, cache, active, data, include_name
        )
    else:
        stripped = {
            key: deepcopy(value)
            for key, value in data.items()
            if key not in {"delete_included_values", "include"}
        }  # Org payload with include-control keys removed.
        resolved = _apply_trait_operations(stripped)

    active.remove(org_id)
    cache[org_id] = deepcopy(resolved)
    return deepcopy(resolved)


def _resolve_inclusion(org_id, raw_orgs, cache, active, data, include_name):
    included_org = str(normalize_node(include_name))
    if included_org not in raw_orgs:
        raise KeyError(f"MIO '{org_id}' includes unknown organization '{included_org}'")

    merged = _resolve_data(
        included_org, raw_orgs, cache, active
    )  # Effective payload inherited from included org.
    delete_values = token_list(data.get("delete_included_values"))
    for key in delete_values:
        merged.pop(key, None)

    for key, value in data.items():
        if key in _SPECIAL_INCLUDE_KEYS:
            continue
        merged[key] = deepcopy(cast(object, value))

    for key in ("add_trait", "remove_trait", "override_trait"):
        if key in data:
            merged[key] = deepcopy(cast(object, data[key]))

    resolved = _apply_trait_operations(merged)
    return resolved


########################
### Type Definitions ###
########################


@dataclass
class EquipmentGroup:
    """Equipment-group definition used by MIO equipment scopes.

    Parsed from common/equipment_groups/mio_equipment_groups.txt.

    Attributes:
        name: Group token used in MIO equipment_type blocks.
        types: Expanded equipment archetype/type tokens contained by the group.
    """

    name: str
    types: list[str]

    @classmethod
    def from_file(
        cls,
        file_path: str = "common/equipment_groups/mio_equipment_groups.txt",
    ) -> dict[str, "EquipmentGroup"]:
        """Load equipment groups from a HOI4 group-definition file.

        Args:
            file_path: Path to the equipment group definition file.

        Returns:
            Mapping of group token to EquipmentGroup.
        """
        raw_data = parse_file(file_path)
        groups: dict[str, EquipmentGroup] = {}
        for key in raw_data.keys():
            token = str(key)
            value = raw_data[key]
            if not isinstance(value, pyradox.Tree):
                continue
            parsed = as_mapping(value)
            groups[token] = cls(
                name=token,
                types=dedupe_preserve_order(token_list(parsed.get("equipment_type"))),
            )
        return groups


@dataclass
class Trait:
    """Resolved trait node from a parsed MIO tree.

    Attributes:
        token: Unique trait identifier in one organization tree.
        name: Localisation key token for the trait display name.
        applies_to: Expanded equipment tokens the trait bonuses affect.
        bonuses: Parsed equipment_bonus values as EquipmentStats.
        mutually_exclusive: Resolved references to exclusive traits.
        parent: Resolved single-parent link from parent tokens.
        all_parents: Resolved AND-parent dependency links.
        any_parents: Resolved OR-parent dependency links.
        parent_tokens: Raw parent tokens parsed from parent blocks.
        all_parent_tokens: Raw parent tokens parsed from all_parents blocks.
        any_parent_tokens: Raw parent tokens parsed from any_parent blocks.
        mutually_exclusive_tokens: Raw mutually exclusive trait tokens.
    """

    token: str
    name: str
    applies_to: set[str]
    """Expanded equipment tokens this trait applies to."""
    bonuses: EquipmentStats
    mutually_exclusive: list["Trait"] = field(default_factory=list)
    parent: "Trait | None" = None
    all_parents: list["Trait"] = field(default_factory=list)
    any_parents: list["Trait"] = field(default_factory=list)
    parent_tokens: list[str] = field(default_factory=list)
    all_parent_tokens: list[str] = field(default_factory=list)
    any_parent_tokens: list[str] = field(default_factory=list)
    mutually_exclusive_tokens: list[str] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Trait):
            return NotImplemented
        return (
            self.token == other.token
            and self.name == other.name
            and self.applies_to == other.applies_to
        )

    def __hash__(self) -> int:
        return hash((self.token, self.name, frozenset(self.applies_to)))


@dataclass(frozen=False)
class MIO:
    """Military Industrial Organization.

    Mutable to allow additive modifications to the countries when parsing with
    merge_generics.
    """

    token: str
    """Token identifying this MIO."""
    countries: set[str]
    equipment_types: set[str]
    research_categories: set[str]
    include: str | None = None
    """Token of the MIO that is the basis for this one."""
    traits: list[Trait] = field(default_factory=list)
    required_flags: set[str] = field(default_factory=set)
    """Flags required for this MIO."""

    @staticmethod
    def _build_trait(
        trait_data: dict[str, object],
        default_applies_to: set[str],
        equipment_groups: dict[str, EquipmentGroup],
        equipment_index: dict[str, Equipment],
    ) -> Trait:
        """Create one Trait from raw trait data.

        If limit_to_equipment_type exists, applies_to is built from that limit;
        otherwise it inherits the full resolved MIO equipment scope.
        """
        token = str(normalize_node(trait_data.get("token", "")))
        if not token:
            raise ValueError("Trait without token found while parsing MIO")

        name_value = normalize_node(trait_data.get("name"))
        name = str(name_value) if name_value is not None else token

        limit_tokens = token_list(trait_data.get("limit_to_equipment_type"))
        applies_to: set[str] = (
            _expand_equipment_tokens(limit_tokens, equipment_groups)
            if limit_tokens
            else set(default_applies_to)
        )

        parent_tokens = dedupe_preserve_order(token_list(trait_data.get("parent")))
        all_parent_tokens = dedupe_preserve_order(
            token_list(trait_data.get("all_parents"))
        )
        any_parent_tokens = dedupe_preserve_order(
            token_list(trait_data.get("any_parent"))
        )
        mutually_exclusive_tokens = dedupe_preserve_order(
            token_list(trait_data.get("mutually_exclusive"))
        )

        stats_class = _detect_stats_class_from_equipment_scope(
            applies_to,
            equipment_index,
        )

        return Trait(
            token=token,
            name=name,
            applies_to=applies_to,
            bonuses=_parse_equipment_bonus(
                trait_data.get("equipment_bonus"),
                stats_class=stats_class,
            ),
            parent_tokens=parent_tokens,
            all_parent_tokens=all_parent_tokens,
            any_parent_tokens=any_parent_tokens,
            mutually_exclusive_tokens=mutually_exclusive_tokens,
        )

    @staticmethod
    def _link_traits(traits: list[Trait]):
        """Resolve token-based trait references into object links."""
        by_token = {trait.token: trait for trait in traits}
        for trait in traits:
            if trait.parent_tokens:
                trait.parent = by_token.get(trait.parent_tokens[0])
            trait.all_parents = [
                by_token[token]
                for token in trait.all_parent_tokens
                if token in by_token
            ]
            trait.any_parents = [
                by_token[token]
                for token in trait.any_parent_tokens
                if token in by_token
            ]
            trait.mutually_exclusive = [
                by_token[token]
                for token in trait.mutually_exclusive_tokens
                if token in by_token
            ]

    @classmethod
    def _from_resolved_data(
        cls,
        name: str,
        data: dict[str, object],
        equipment_groups: dict[str, EquipmentGroup],
        equipment_index: dict[str, Equipment],
        include: str | None = None,
    ) -> "MIO":
        """Build a fully typed MIO object from resolved raw organization data."""
        countries = _iter_original_tags(
            data.get("allowed")
        )  # Country tags permitted to use this MIO.
        required_flags = _iter_required_country_flags(
            data.get("allowed"),
            data.get("visible"),
            data.get("available"),
        )  # Country flags required by MIO visibility/availability logic.
        equipment_tokens = dedupe_preserve_order(
            token_list(data.get("equipment_type"))
        )  # Raw equipment scope tokens.
        equipment_types = _expand_equipment_tokens(
            equipment_tokens, equipment_groups
        )  # Expanded equipment scope tokens.
        research_categories = dedupe_preserve_order(
            token_list(data.get("research_categories"))
        )  # Research category tokens this MIO can affect.

        traits = [
            MIO._build_trait(
                trait_data,
                equipment_types,
                equipment_groups,
                equipment_index,
            )
            for trait_data in as_trait_list(data.get("trait"))
        ]  # Fully parsed trait objects for this MIO.
        MIO._link_traits(traits)

        return cls(
            token=name,
            countries=set(countries),
            equipment_types=set(equipment_types),
            research_categories=set(research_categories),
            include=include,
            traits=traits,
            required_flags=set(required_flags),
        )

    @classmethod
    def _parse_raw_organizations(
        cls,
        raw_orgs: dict[str, pyradox.Tree],
        equipment_groups: dict[str, EquipmentGroup],
        equipment_index: Optional[dict[str, Equipment]] = None,
    ) -> dict[str, "MIO"]:
        """Parse already-loaded raw organization trees into typed MIO objects."""
        resolved_equipment_index = Equipment.get_equipment_index(equipment_index)

        cache: dict[str, dict[str, object]] = (
            {}
        )  # MIO token -> resolved include-expanded payload.
        parsed: dict[str, MIO] = {}  # MIO token -> typed MIO object.
        for org_id in raw_orgs:
            raw_data = as_mapping(raw_orgs[org_id])
            include_name = raw_data.get("include")
            include_token = (
                str(normalize_node(include_name)) if include_name is not None else None
            )

            resolved = _resolve_data(org_id, raw_orgs, cache, set())
            parsed[org_id] = cls._from_resolved_data(
                org_id,
                resolved,
                equipment_groups,
                resolved_equipment_index,
                include=include_token,
            )

        return parsed

    @classmethod
    def from_directory(
        cls,
        path: str | Path,
        equipment_groups: dict[str, EquipmentGroup],
        merge_generics: bool,
        equipment_index: Optional[dict[str, Equipment]] = None,
    ) -> dict[str, "MIO"]:
        """Parse all MIO organizations in a directory tree.

        Args:
            path: Directory containing organization .txt files.
            equipment_groups: Group map used to expand equipment scopes.

        Returns:
            Mapping of organization token to parsed MIO object.
        """
        root = Path(path)
        if not root.exists():
            raise FileNotFoundError(path)
        if not root.is_dir():
            raise NotADirectoryError(path)

        raw_orgs: dict[str, pyradox.Tree] = (
            {}
        )  # MIO token -> raw pyradox tree from files.
        for file_path in sorted(root.rglob("*.txt")):
            if not file_path.is_file():
                continue

            raw = parse_file(file_path)
            for key in raw.keys():
                value = raw[key]
                if isinstance(value, pyradox.Tree):
                    raw_orgs[str(key)] = value

        result = cls._parse_raw_organizations(
            raw_orgs, equipment_groups, equipment_index
        )
        if merge_generics:
            result = cls._merge_generics(result)
        return result

    @staticmethod
    def _merge_generics(mios: dict[str, "MIO"]) -> dict[str, "MIO"]:
        """Removes MIO that are just renamed generics.
        Adds the countries of those MIO to the countries of the referenced generics.
        """
        result: dict[str, "MIO"] = dict()
        for token, mio in mios.items():
            if mio.include is not None:
                included: "MIO" = mios[mio.include]
                if included.traits == mio.traits:
                    included.countries.update(mio.countries)
                continue
            result[token] = mio
        return result

    def sum_bonuses_for(
        self, equipment_type: Equipment, weights: Optional[EquipmentStats] = None
    ) -> "BonusReport":
        """Calculate the total and per-stat average bonuses this MIO provides to a type.

        The aggregate bonus is the sum across all matching traits. The averaged report is
        computed per stat using only the traits that actually improve that stat, so empty
        contributions are excluded from that stat's denominator.
        """
        stats_class = type(equipment_type.stats)
        total: EquipmentStats = (
            stats_class()
        )  # Running total bonus accumulated across matching traits.
        matching_traits: list[Trait] = []  # Traits that apply to equipment_type.

        for trait in self.traits:
            if equipment_type.tag not in trait.applies_to:
                continue
            total = total.applyFlatBonus(trait.bonuses)
            matching_traits.append(trait)

        average_boost = stats_class.average_field_values(
            [trait.bonuses for trait in matching_traits]
        )
        return BonusReport(
            mio=self,
            boost=total,
            n_traits=len(matching_traits),
            score=total.score(weights),
            averaged_boost=average_boost,
        )

    def __hash__(self) -> int:
        return hash(
            (self.token, frozenset(self.countries), frozenset(self.equipment_types))
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MIO):
            return NotImplemented
        return (
            self.token == other.token
            and self.countries == other.countries
            and self.equipment_types == other.equipment_types
        )


@dataclass(frozen=True)
class BonusReport:
    mio: MIO
    """The MIO providing the boost"""
    boost: EquipmentStats
    """The boost provided by the MIO if it is completely applied"""
    n_traits: int
    """How many traits contributed to the boost"""
    score: float
    """The overall score of the boost, typically calculated from the EquipmentStats"""
    averaged_boost: EquipmentStats
    """The boost provided by the MIO averaged over the number of contributing traits"""

    def is_empty(self) -> bool:
        """Check if no traits contributed to the boost."""
        return self.n_traits == 0

    def to_pretty_display(self) -> str:
        buffer = f"MIO: {self.mio.token}, countries: [{', '.join(self.mio.countries)}], score: {self.score:.2f}, n_traits: {self.n_traits}\n"
        for boosted in fields(self.boost):
            if self.boost.get_or_default(boosted.name, None) is None:
                continue
            value = getattr(self.boost, boosted.name)
            buffer += f"  {boosted.name}: {value:.2f} (avg: {getattr(self.averaged_boost, boosted.name):.2f})\n"
        return buffer
