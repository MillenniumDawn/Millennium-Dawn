from dataclasses import dataclass, fields, replace
from typing import Optional
from partial_success import PartialSuccess

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

    def applyFlatBonus(self, bonus: "EquipmentStats") -> PartialSuccess["EquipmentStats"]:
        warnings: list[str] = []
        updates = {}
        for field in fields(self):
            base = getattr(self, field.name)
            increase = getattr(bonus, field.name)
            if increase is None:
                continue
            if base is None:
                warnings.append(f"Bonus declared for {field.name} but base value is None.")
            else:
                updates[field.name] = base + increase

        return PartialSuccess(replace(self, **updates), warnings)


@dataclass(frozen=True)
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

@dataclass(frozen=True)
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

class AirEquipmentStats(EquipmentStats):
    """Stats specific to air equipment."""
    air_attack: Optional[float] = None
    """Amount of damage done against other planes."""
    air_defence: Optional[float] = None
    """How many hits a plane takes before being shot down."""
    air_range: Optional[float] = None
    """Maximum operational range of the aircraft in kilometers."""
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

class Equipment:
    """Equipment used by units.
    They are defined in common/units/equipment/**.txt files.
    """
    def __init__(self, tag: str, is_archetype: bool, archetype: Optional['Equipment'], is_buildable: bool, stats: EquipmentStats):
        self.tag = tag
        self.is_archetype = is_archetype
        self.is_buildable = is_buildable
        self.archetype = archetype
        self.stats = stats