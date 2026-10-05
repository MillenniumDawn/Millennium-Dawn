import os
import sys
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Optional, TypeAlias, TypeVar, cast

import pyradox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))

from pyradox_utils import normalize_bool, normalize_scalar, normalize_type, parse_file

RawEquipmentValue: TypeAlias = "pyradox.Tree | Equipment"
RawEquipmentMap: TypeAlias = dict[str, RawEquipmentValue]
RawEquipmentDict: TypeAlias = dict[str, object]


@dataclass(frozen=True)
class EquipmentStats:
    """Stats that all equipment types have in common.
    All stats are optional to facilitate partial definitions for bonuses and modifications.
    It doesn't mean that it is sensible to leave them all undefined in actual equipment definitions.

    Wiki source: https://hoi4.paradoxwikis.com/Equipment_modding#All
    """

    lend_lease_cost: Optional[float] = None
    """Space taken up in convoys, measured in convoy units."""
    build_cost_ic: Optional[float] = None
    """Production Cost - How much factory output this piece of equipment needs."""
    manpower: Optional[float] = None
    """Cost in manpower to produce (ie.: how much manpower is required to staff a unit of this equipment)."""
    can_license: Optional[bool] = None
    """Indicates whether this equipment can be licensed for production by other countries."""
    is_convertable: Optional[bool] = None
    """Indicates whether units of this equipment can be converted or upgraded to other types."""
    reliability: Optional[float] = None
    """Indicates the overall reliability of the equipment."""

    def applyFlatBonus(self, bonus: "EquipmentStats") -> "EquipmentStats":
        """Apply a flat bonus from another EquipmentStats object.

        If a stat in the bonus object is None, it will be ignored.

        Args:
            bonus: The EquipmentStats object containing the bonuses to apply.

        Returns:
            A new EquipmentStats object with the bonuses applied.
        """
        updates: dict[str, float] = {}
        for field in fields(self):
            base = self.get_or_default(field.name, 0)
            increase = bonus.get_or_default(field.name, 0)
            if not increase:
                continue

            updates[field.name] = base + increase

        return replace(self, **updates)

    def is_empty(self) -> bool:
        """Check if all stats are None."""
        return all(getattr(self, field.name) is None for field in fields(self))

    @classmethod
    def average_field_values(cls, values: list["EquipmentStats"]) -> "EquipmentStats":
        """Return a per-field mean over the traits that actually contribute to each stat."""
        if not values:
            return cls()

        averaged: dict[str, float] = {}
        for field in fields(cls):
            samples = [
                getattr(item, field.name)
                for item in values
                if item.get_or_default(field.name, None) is not None
            ]
            if samples:
                averaged[field.name] = sum(samples) / len(samples)
        return cls(**cast(Any, averaged))

    T = TypeVar("T")

    def get_or_default(self, attribute_name: str, default: T) -> float | T:
        """Get the value of an attribute, or return a default if it is None or doesn't exist."""
        try:
            value = getattr(self, attribute_name)
            if value is None:
                return default
            return value
        except AttributeError:
            return default

    def score(self, weights: Optional["EquipmentStats"] = None) -> float:
        """Calculate a score for the equipment based on its defined stats."""
        if weights is None:
            weights = AllEquipmentStats()

        total_score = 0.0
        negative_is_better = [
            "build_cost_ic",
            "lend_lease_cost",
            "manpower",
            "sub_visibility",
            "surface_visibility",
            "fuel_consumption",
        ]
        for field in fields(self):
            value = getattr(self, field.name)
            if value is not None:
                if field.name in negative_is_better:
                    value = abs(value)
                total_score += value * weights.get_or_default(field.name, 1)
        return total_score

    def __repr__(self) -> str:
        non_none_fields = [
            f"\n    {field.name}={value:.2f}"
            for field in fields(self)
            if (value := getattr(self, field.name)) is not None
        ]
        joined = ",".join(non_none_fields)
        return f"{self.__class__.__name__}({joined})"


@dataclass(frozen=True, repr=False)
class LandEquipmentStats(EquipmentStats):
    """Stats specific to land equipment.

    All stats are optional to facilitate partial definitions for bonuses and modifications.
    It doesn't mean that it is sensible to leave them all undefined in actual equipment definitions.

    Wiki source: https://hoi4.paradoxwikis.com/Equipment_modding#Land
    """

    reliability: Optional[float] = None
    maximum_speed: Optional[float] = None
    soft_attack: Optional[float] = None
    """How many attacks the unit can make versus enemies with low hardness."""
    hard_attack: Optional[float] = None
    """How many attacks the unit can make versus enemies with high hardness."""
    air_attack: Optional[float] = None
    """How much damage can be done against airplanes. High Air Attack also helps to counter enemy Air Superiority effects."""
    ap_attack: Optional[float] = None
    """Piercing - Having equal or greater Piercing to the targets Armor value to do more damage."""
    breakthrough: Optional[float] = None
    """How many enemy attacks a unit can attempt to avoid while on the offensive."""
    defense: Optional[float] = None
    """How many attacks a unit can avoid whilst on the defensive."""
    max_strength: Optional[float] = None
    """HP - Strength represents how much damage this unit can suffer before it is destroyed."""
    armor_value: Optional[float] = None
    """Armor that is higher than the opponents Piercing value reduces damage taken and the amount of attacks the unit can do in a combat."""
    hardness: Optional[float] = None
    """Represents how how hard the unit is for damage calculation purposes. Low hardness = more soft damage, high hardness = more hard damage."""
    entrenchment: Optional[float] = None
    """The ability to make proper defensive entrenchments before a hostile attack."""
    recon: Optional[float] = None
    """Increases the chance that this unit can pick better tactics in battle."""
    additional_collateral_damage: Optional[float] = None
    """Additional damage inflicted on the state's infrastructure and fortifications hosting the battle and this unit.

    Wiki source: https://hoi4.paradoxwikis.com/Land_battle#Collateral_damage
    """
    supply_consumption: Optional[float] = None
    """How much supply a unit equipped with this equipment consumes per day."""
    suppression: Optional[float] = None
    """Units with this equipment have this much increased suppression capability against population resistance."""


@dataclass(frozen=True, repr=False)
class NavalEquipmentStats(EquipmentStats):
    """Stats specific to naval equipment.

    All stats are optional to facilitate partial definitions for bonuses and modifications.
    It doesn't mean that it is sensible to leave them all undefined in actual equipment definitions.

    Wiki source: https://hoi4.paradoxwikis.com/Equipment_modding#Naval
    Additional source: common/units/equipment/modules/MD_ship_modules.txt
    """

    naval_speed: Optional[float] = None
    """Maximum speed in kilometres per hour of the ship, higher means faster in combat and contributes to evasion."""
    lg_armor_piercing: Optional[float] = None
    """Light gun armor piercing - Determines how much armor ship's gun attacks can pierce."""
    lg_attack: Optional[float] = None
    """Light gun attack - How much damage the ship does with guns and land attack missiles (more effective against screens)."""
    hg_armor_piercing: Optional[float] = None
    """Heavy gun armor piercing - Determines how much armor ship's heavy gun attack can pierce."""
    hg_attack: Optional[float] = None
    """Heavy gun attack - How much damage the ship does with heavy guns (more effective against larger ships)."""
    torpedo_attack: Optional[float] = None
    """Torpedo attack - How much damage the ship does with torpedoes (more effective against capital ships)."""
    anti_air_attack: Optional[float] = None
    """Anti-air attack - How much anti-air firepower the ship carries for shooting down enemy planes."""
    surface_detection: Optional[float] = None
    """Surface detection - Ability to detect surface vessels."""
    sub_attack: Optional[float] = None
    """Submarine attack - How much damage the ship does against submarines."""
    sub_detection: Optional[float] = None
    """Submarine detection - Ability to detect submarines."""
    surface_visibility: Optional[float] = None
    """Surface visibility - Represents a ship's profile. The higher the value the more the ship is easy to spot and especially hit."""
    sub_visibility: Optional[float] = None
    """Submarine visibility - Represents a submarine's profile. The higher the value the more the submarine is easy to spot and especially hit."""
    armor_value: Optional[float] = None
    """Armor value - Armor is compared to enemy piercing: the more piercing is lower than armor, the more damage is reduced, the more piercing is higher than armor, the more critical hit chance increases."""
    naval_range: Optional[float] = None
    """Naval range - Maximum operational range of the ship in kilometers from its nearest naval base."""
    fuel_consumption: Optional[float] = None
    """Fuel consumption - Represents the rate at which the ship consumes fuel."""
    mines_planting: Optional[float] = None
    """Mine planting - Represents the equipment's ability to plant naval mines."""
    max_organisation: Optional[float] = None
    """Max organisation - Represents the maximum organisation of the ship. Even if used in "add stats" it actually multiplies the base organisation of the ship."""
    mines_sweeping: Optional[float] = None
    """Mine sweeping - Represents the equipment's ability to detect and clear naval mines."""
    carrier_size: Optional[float] = None
    """Carrier size - Number of planes that can operate from the ship."""


@dataclass(frozen=True, repr=False)
class AirEquipmentStats(EquipmentStats):
    """Stats specific to air equipment."""

    maximum_speed: Optional[float] = None
    """Maximum speed of the aircraft."""
    air_attack: Optional[float] = None
    """Amount of damage done against other planes."""
    air_defence: Optional[float] = None
    """How many hits a plane takes before being shot down."""
    air_range: Optional[float] = None
    """Maximum operational range of the aircraft in kilometers. When a modifier, is a percentage."""
    air_agility: Optional[float] = None
    """How agile a plane is. Agility effects how easy it is to hit another plane, and avoid being hit"""
    air_ground_attack: Optional[float] = None
    """Damage done to ground forces during CAS missions."""
    air_bombing: Optional[float] = None
    """Damage done to strategic targets during bombing missions."""
    air_superiority: Optional[float] = None
    """How much a plane equipped with this helps the overall air superiority of a strategic area."""
    naval_strike_attack: Optional[float] = None
    """Damage done to naval units during naval strike missions."""
    naval_strike_targetting: Optional[float] = None
    """How likely it is to hit a ship."""
    # TODO move those two to a specialized airframe class
    default_carrier_composition_weight: Optional[float] = None
    """Influences carrier composition weight. (Unknown what exactly this affects, but is defined on the airframe)"""
    carrier_capable: Optional[bool] = None
    """Indicates whether the aircraft can operate from a carrier. (Defined on the airframe)"""
    surface_detection: Optional[float] = None
    """Represents the equipment's ability to detect ships."""
    sub_detection: Optional[float] = None
    """Represents the equipment's ability to detect submarines."""


@dataclass(frozen=True, repr=False)
class AllEquipmentStats(LandEquipmentStats, NavalEquipmentStats, AirEquipmentStats):
    """Union of every stat field, for use as a cross-domain weight vector."""


_LAND_TYPE_TOKENS = {
    "infantry",
    "armor",
    "anti_tank",
    "artillery",
    "support",
    "rocket_artillery",
    "motorized",
    "mechanized",
    "fighting",
    "mountain",
    "infantry",
    "amphibious",
}

_NAVAL_TYPE_TOKENS = {
    "screen_ship",
    "capital_ship",
    "carrier",
    "convoy",
    "support_ship",
    "submarine",
    "flying_boat",
    "destroyer",
    "frigate",
    "corvette",
    "cruiser",
    "battleship",
}

_AIR_TYPE_TOKENS = {
    "fighter",
    "cas",
    "interceptor",
    "naval_bomber",
    "tactical_bomber",
    "scout_plane",
    "strat_bomber",
    "transport_plane",
    "suicide",
}


def _field_names(cls: type[EquipmentStats]) -> set[str]:
    return {field.name for field in fields(cls)}


_LAND_STAT_KEYS = _field_names(LandEquipmentStats)
_NAVAL_STAT_KEYS = _field_names(NavalEquipmentStats)
_AIR_STAT_KEYS = _field_names(AirEquipmentStats)

_DEFAULT_EQUIPMENT_INDEX: Optional[dict[str, "Equipment"]] = None


@dataclass
class Equipment:
    """Equipment used by units.
    They are defined in common/units/equipment/**.txt files.
    """

    tag: str
    """Unique identifier for the equipment."""
    is_archetype: bool
    """Indicates if this equipment is an archetype."""
    archetype: Optional["Equipment"]
    """Reference to the archetype equipment if this is not an archetype."""
    types: list[str]
    """List of equipment types this equipment belongs to."""
    is_buildable: bool
    """Indicates if this equipment can be built."""
    stats: EquipmentStats
    """Stats associated with this equipment."""

    def __init__(
        self,
        tag: str,
        is_archetype: bool,
        archetype: Optional["Equipment"],
        types: list[str],
        is_buildable: bool,
        stats: EquipmentStats,
    ):
        self.tag = tag
        self.is_archetype = is_archetype
        self.is_buildable = is_buildable
        self.archetype = archetype
        self.types = types
        self.stats = stats

    @staticmethod
    def _normalize_bool(value: object) -> bool:
        return normalize_bool(value)

    @staticmethod
    def _normalize_scalar(value: object) -> object:
        return normalize_scalar(value)

    @staticmethod
    def _normalize_type(value: object) -> list[str]:
        return normalize_type(value)

    @staticmethod
    def _merge_inherited_data(
        base_data: RawEquipmentDict, override_data: RawEquipmentDict
    ) -> RawEquipmentDict:
        merged = dict(base_data)
        merged.update(override_data)
        return merged

    @classmethod
    def _resolve_reference(
        cls, name: object, archetypes: RawEquipmentMap
    ) -> Optional["Equipment"]:
        if name is None:
            return None
        ref = archetypes.get(str(name))
        if ref is None:
            return None
        if isinstance(ref, Equipment):
            return ref
        if isinstance(ref, pyradox.Tree):
            return cls.read_equipment(str(name), ref, archetypes)
        return None

    @staticmethod
    def _as_python_data(
        raw_equipment: pyradox.Tree | RawEquipmentDict,
    ) -> RawEquipmentDict:
        if isinstance(raw_equipment, dict):
            return raw_equipment
        if isinstance(raw_equipment, pyradox.Tree):
            return cast(RawEquipmentDict, raw_equipment.to_python())
        raise TypeError(f"Unexpected equipment format: {type(raw_equipment)!r}")

    @staticmethod
    def _detect_stats_class(raw_data: dict[str, object]) -> type[EquipmentStats]:
        type_tokens = set()
        for token in Equipment._normalize_type(raw_data.get("type")):
            type_tokens.add(token)

        if type_tokens & _NAVAL_TYPE_TOKENS:
            return NavalEquipmentStats
        if type_tokens & _AIR_TYPE_TOKENS:
            return AirEquipmentStats
        if type_tokens & _LAND_TYPE_TOKENS:
            return LandEquipmentStats

        if any(key in raw_data for key in _NAVAL_STAT_KEYS):
            return NavalEquipmentStats
        if any(key in raw_data for key in _AIR_STAT_KEYS):
            return AirEquipmentStats
        if any(key in raw_data for key in _LAND_STAT_KEYS):
            return LandEquipmentStats

        interface_category = str(raw_data.get("interface_category", "")).lower()
        if "ship" in interface_category or "naval" in interface_category:
            return NavalEquipmentStats
        if "air" in interface_category or "plane" in interface_category:
            return AirEquipmentStats
        if "land" in interface_category:
            return LandEquipmentStats

        return LandEquipmentStats

    @staticmethod
    def _read_stats(
        raw_equipment: pyradox.Tree, archetypes: RawEquipmentMap
    ) -> EquipmentStats:
        raw_data = Equipment._as_python_data(raw_equipment)
        merged_data: RawEquipmentDict = {}

        archetype_name = raw_data.get("archetype")
        if archetype_name is not None and str(archetype_name) in archetypes:
            inherited = archetypes[str(archetype_name)]
            if isinstance(inherited, pyradox.Tree):
                merged_data = Equipment._merge_inherited_data(
                    merged_data, Equipment._as_python_data(inherited)
                )

        parent_name = raw_data.get("parent")
        if parent_name is not None and str(parent_name) in archetypes:
            inherited = archetypes[str(parent_name)]
            if isinstance(inherited, pyradox.Tree):
                merged_data = Equipment._merge_inherited_data(
                    merged_data, Equipment._as_python_data(inherited)
                )

        merged_data = Equipment._merge_inherited_data(merged_data, raw_data)

        stats_class = Equipment._detect_stats_class(merged_data)
        allowed_fields = {field.name for field in fields(stats_class)}

        stat_values: dict[str, object] = {}
        for key, value in merged_data.items():
            if key in allowed_fields:
                stat_values[key] = Equipment._normalize_scalar(value)

        return stats_class(
            **{
                field.name: cast(Any, stat_values.get(field.name))
                for field in fields(stats_class)
            }
        )

    @classmethod
    def read_equipment(
        cls, tag: str, raw_equipment: pyradox.Tree, archetypes: RawEquipmentMap
    ) -> "Equipment":
        if type(raw_equipment) is not pyradox.Tree:
            raise TypeError(
                f"Unexpected equipment format for {tag}: {type(raw_equipment)!r}"
            )

        raw_data = Equipment._as_python_data(raw_equipment)
        archetype_ref = Equipment._resolve_reference(
            raw_data.get("archetype"), archetypes
        )
        if archetype_ref is not None:
            archetype = archetype_ref
        else:
            archetype = None

        is_buildable = Equipment._normalize_bool(raw_data.get("is_buildable", True))
        types = Equipment._normalize_type(raw_data.get("type"))
        stats = Equipment._read_stats(raw_equipment, archetypes)
        is_archetype = Equipment._normalize_bool(raw_data.get("is_archetype", False))
        return cls(tag, is_archetype, archetype, types, is_buildable, stats)

    @classmethod
    def from_file(cls, file_path: str) -> dict[str, "Equipment"]:
        """Parses all equipments data from a given file."""
        return cls._read_all(cls._raw_entries(file_path))

    @staticmethod
    def _raw_entries(file_path: str | Path) -> RawEquipmentMap:
        raw: pyradox.Tree = parse_file(file_path)
        entries = cast(pyradox.Tree, raw["equipments"]) if "equipments" in raw else raw
        return {str(key): cast(pyradox.Tree, entries[key]) for key in entries.keys()}

    @classmethod
    def _read_all(cls, equip_by_tag: RawEquipmentMap) -> dict[str, "Equipment"]:
        return {
            key: cls.read_equipment(key, cast(pyradox.Tree, value), equip_by_tag)
            for key, value in equip_by_tag.items()
        }

    @classmethod
    def from_directory(
        cls, path: str | Path = "common/units/equipment/"
    ) -> dict[str, "Equipment"]:
        """Parses all equipment files in a directory tree, including cross-file archetype references."""
        root = Path(path)
        if not root.exists():
            raise FileNotFoundError(path)
        if not root.is_dir():
            raise NotADirectoryError(path)

        equip_by_tag: RawEquipmentMap = {}
        for file_path in sorted(root.rglob("*.txt")):
            if file_path.is_file():
                equip_by_tag.update(cls._raw_entries(file_path))

        return cls._read_all(equip_by_tag)

    @staticmethod
    def load_default_equipment_index() -> dict[str, "Equipment"]:
        """Load and cache the default equipment index from mod equipment files."""
        global _DEFAULT_EQUIPMENT_INDEX
        if _DEFAULT_EQUIPMENT_INDEX is not None:
            return _DEFAULT_EQUIPMENT_INDEX

        try:
            _DEFAULT_EQUIPMENT_INDEX = Equipment.from_directory()
        except (FileNotFoundError, NotADirectoryError):
            _DEFAULT_EQUIPMENT_INDEX = {}
        return _DEFAULT_EQUIPMENT_INDEX

    @classmethod
    def get_equipment_index(
        cls,
        equipment_index: Optional[dict[str, "Equipment"]] = None,
    ) -> dict[str, "Equipment"]:
        """Return a caller-provided index or the cached default singleton."""
        return (
            equipment_index
            if equipment_index is not None
            else Equipment.load_default_equipment_index()
        )


if __name__ == "__main__":
    equipments = Equipment.from_directory("common/units/equipment/")
    for tag, equipment in equipments.items():
        print(f"{tag}: {equipment}")
