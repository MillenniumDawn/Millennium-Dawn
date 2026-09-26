#!/usr/bin/env python3
# Check every technology category reference against common/technology_tags/,
# and the tag set itself against the naming, localisation and usage rules.
# An unknown category name compiles silently and grants nothing, so a focus,
# event or idea can promise a research bonus and deliver zero. Two live cases
# motivated this: CAT_encryption (the token is CAT_encryption_tech) sat in eight
# idea research_bonus blocks, and CAT_computer_systems is a real token that
# means armour computer systems, so computing content using it bought tank tech.
import difflib
import os
import re
import sys
from typing import Dict, FrozenSet, Iterable, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import FileOpener
from validator_common import BaseValidator, Severity, run_validator_main

# The tag block in common/technology_tags/. Every bare token inside it is a
# category, whatever its case: a wrongly cased token must still load so the
# format check can name it.
_CATEGORIES_BLOCK_RE = re.compile(r"(?i)\btechnology_categories\s*=\s*\{")
_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

# Every tag is CAT_ followed by lowercase words (#4250).
_TAG_FORMAT_RE = re.compile(r"^CAT_[a-z0-9_]+$")

# Tags renamed in the #4250 rework, keyed lowercase: an unknown reference is
# looked up case-insensitively here before falling back to string similarity.
_LEGACY_CATEGORIES = {
    "cat_3d": "CAT_3d_printing",
    "cat_olv": "CAT_orbital_launch_vehicles",
    "cat_a_uav": "CAT_air_drones",
    "cat_aa": "CAT_anti_air",
    "cat_aa_missiles": "CAT_naval_anti_air_missiles",
    "cat_abm": "CAT_surface_to_air_missiles",
    "cat_afv": "CAT_armored_fighting_vehicles",
    "cat_afv_weapons": "CAT_infantry_fighting_vehicles",
    "cat_agriculture_tech": "CAT_agriculture",
    "cat_ai": "CAT_artificial_intelligence",
    "cat_air_camera": "CAT_targeting_pods",
    "cat_air_engine": "CAT_air_engines",
    "cat_air_eqp": "CAT_aircraft",
    "cat_air_ground_weapons": "CAT_air_to_ground_weapons",
    "cat_air_naval_weapons": "CAT_air_to_naval_weapons",
    "cat_air_spc": "CAT_air_modules",
    "cat_air_wpn": "CAT_air_weapons",
    "cat_airborne": "CAT_special_forces_equipment",
    "cat_airmobile": "CAT_special_forces_equipment",
    "cat_alcm": "CAT_cruise_missiles",
    "cat_apc": "CAT_armored_personnel_carriers",
    "cat_armor_engines": "CAT_tank_engines",
    "cat_armor_weapons": "CAT_tank_guns",
    "cat_armour": "CAT_tank_armor",
    "cat_armour_ds": "CAT_tank_defensive_systems",
    "cat_art_ammo": "CAT_artillery_ammunition",
    "cat_arty": "CAT_towed_artillery",
    "cat_as_fighter": "CAT_medium_aircraft",
    "cat_as_missiles": "CAT_naval_anti_ship_missiles",
    "cat_at": "CAT_anti_tank",
    "cat_atk_heli": "CAT_attack_helicopters",
    "cat_atk_sub": "CAT_attack_submarines",
    "cat_awacs": "CAT_airborne_early_warning",
    "cat_carrier": "CAT_aircraft_carriers",
    "cat_cas": "CAT_air_to_ground_weapons",
    "cat_cm": "CAT_cruise_missiles",
    "cat_cnc": "CAT_command_and_control_equipment",
    "cat_computer_systems": "CAT_tank_computer_systems",
    "cat_computing_tech": "CAT_information_technology",
    "cat_construction_tech": "CAT_construction",
    "cat_corvette": "CAT_corvettes",
    "cat_cruiser": "CAT_cruisers",
    "cat_cv_l_s_fighter": "CAT_light_aircraft",
    "cat_cv_mr_fighter": "CAT_medium_aircraft",
    "cat_cze": "CAT_czech_engines",
    "cat_d_sub": "CAT_attack_submarines",
    "cat_decryption_tech": "CAT_decryption",
    "cat_destroyer": "CAT_destroyers",
    "cat_electrical_tech": "CAT_energy",
    "cat_encryption_tech": "CAT_encryption",
    "cat_excavation_tech": "CAT_excavation",
    "cat_fighter": "CAT_medium_aircraft",
    "cat_fixed_wing": "CAT_aircraft",
    "cat_frigate": "CAT_frigates",
    "cat_fuel_oil": "CAT_fuel_refining",
    "cat_genes": "CAT_genetics",
    "cat_glcm": "CAT_ground_launched_cruise_missiles",
    "cat_gnss": "CAT_navigation_satellites",
    "cat_h_air": "CAT_heavy_aircraft",
    "cat_h_at": "CAT_heavy_anti_tank",
    "cat_heli": "CAT_helicopters",
    "cat_heli_atgm": "CAT_helicopter_atgm",
    "cat_heli_defense": "CAT_helicopter_defense_systems",
    "cat_heli_drone": "CAT_helicopter_drones",
    "cat_heli_engine": "CAT_helicopter_engines",
    "cat_heli_gunpods": "CAT_helicopter_gun_pods",
    "cat_heli_modules": "CAT_helicopter_modules",
    "cat_heli_nose_gun": "CAT_helicopter_nose_guns",
    "cat_heli_rocketpods": "CAT_helicopter_rocket_pods",
    "cat_hscm": "CAT_hypersonic_cruise_missiles",
    "cat_icbm": "CAT_intercontinental_ballistic_missiles",
    "cat_ifv": "CAT_infantry_fighting_vehicles",
    "cat_inf": "CAT_infantry",
    "cat_inf_wep": "CAT_small_arms",
    "cat_internet_tech": "CAT_internet",
    "cat_irbm": "CAT_intermediate_range_ballistic_missiles",
    "cat_l_aa": "CAT_manpads",
    "cat_l_at": "CAT_light_anti_tank",
    "cat_l_drone": "CAT_land_drones",
    "cat_l_fighter": "CAT_light_aircraft",
    "cat_l_s_fighter": "CAT_light_aircraft",
    "cat_large_plane": "CAT_heavy_aircraft",
    "cat_m_sub": "CAT_missile_submarines",
    "cat_marine": "CAT_special_forces_equipment",
    "cat_mbt": "CAT_tanks",
    "cat_medium_plane": "CAT_medium_aircraft",
    "cat_missile": "CAT_missiles",
    "cat_mr_fighter": "CAT_medium_aircraft",
    "cat_naval_air": "CAT_medium_aircraft",
    "cat_naval_all": "CAT_naval",
    "cat_naval_engine": "CAT_naval_engines",
    "cat_naval_plane": "CAT_heavy_aircraft",
    "cat_naval_radar_drone": "CAT_naval_recon_drones",
    "cat_naval_radar_jammer": "CAT_naval_radar_jammers",
    "cat_naval_railgun": "CAT_naval_railguns",
    "cat_naval_stealth": "CAT_naval_stealth_ships",
    "cat_nfibers": "CAT_nanofibers",
    "cat_nuke_sub": "CAT_submarines",
    "cat_nvg": "CAT_night_vision",
    "cat_patrolboat": "CAT_patrol_boats",
    "cat_pds": "CAT_naval_point_defense_systems",
    "cat_rec_tank": "CAT_light_tanks",
    "cat_renewable": "CAT_renewable_energy",
    "cat_s_fighter": "CAT_light_aircraft",
    "cat_sam": "CAT_surface_to_air_missiles",
    "cat_satellite": "CAT_satellites",
    "cat_slcm": "CAT_cruise_missiles",
    "cat_small_plane": "CAT_light_aircraft",
    "cat_sp_aa": "CAT_self_propelled_anti_air",
    "cat_sp_arty": "CAT_self_propelled_artillery",
    "cat_sp_r_arty": "CAT_self_propelled_artillery",
    "cat_special_forces": "CAT_special_forces_equipment",
    "cat_str_bomber": "CAT_heavy_aircraft",
    "cat_sub": "CAT_submarines",
    "cat_surface_ship": "CAT_surface_ships",
    "cat_trans_heli": "CAT_transport_helicopters",
    "cat_trans_plane": "CAT_heavy_aircraft",
    "cat_trans_ship": "CAT_landing_craft",
    "cat_util": "CAT_utility_vehicles",
    "cat_vls_air_systems": "CAT_vertical_launch_anti_air_missiles",
    "cat_vls_land_systems": "CAT_vertical_launch_surface_missiles",
    "cat_vls_systems": "CAT_naval_vertical_launch_systems",
    "cat_wings": "CAT_wing_designs",
}

# `category = CAT_x` in add_tech_bonus / add_doctrine_cost_reduction blocks.
_CATEGORY_ASSIGN_RE = re.compile(r"\bcategory\s*=\s*((?i:cat_)\w+)")

# research_bonus = { CAT_x = 0.05 } — the keys are categories. ai_focuses and
# ai_strategy_plans weight categories the same way in research = { CAT_x = 5.0 }.
_KEYED_BLOCK_RE = re.compile(r"\b(?:research_bonus|research)\s*=\s*\{")
_KEYED_CATEGORY_RE = re.compile(r"((?i:cat_)\w+)\s*=")

# MIO research_categories = { CAT_x CAT_y } and, in tech files only, a tech's
# own categories = { }. Outside common/technologies/ a `categories` block is a
# doctrine or sub-unit category list, not a tech category reference.
_LISTED_BLOCK_RE = re.compile(r"\bresearch_categories\s*=\s*\{")
_TECH_CATEGORIES_RE = re.compile(r"\bcategories\s*=\s*\{")

_TAGS_GLOB = "common/technology_tags/**/*.txt"
_TECH_DIR = "common/technologies/"
_TECH_GLOB = _TECH_DIR + "**/*.txt"
_VALIDATE_PATTERNS = [
    "common/**/*.txt",
    "events/**/*.txt",
]


def _brace_span(text: str, open_idx: int) -> int:
    """Index just past the block whose opening brace is at *open_idx*."""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(text)


def _block_bodies(text: str, opener: "re.Pattern") -> Iterable[Tuple[str, int]]:
    """(body, body_offset) of every block *opener* introduces."""
    for m in opener.finditer(text):
        open_idx = text.index("{", m.start())
        end = _brace_span(text, open_idx)
        yield text[open_idx + 1 : end], open_idx + 1


def _references(text: str, tech_file: bool = False) -> List[Tuple[str, int]]:
    """Every (category_name, char_offset) this text references.

    Deliberately narrow: `category = CAT_x`, the keys of a research_bonus or
    research block, the tokens of a research_categories block and, for tech
    files, the tokens of a categories block. A bare CAT_ token elsewhere is not
    a category reference, which is what keeps
    `has_country_flag = CAT_revolted_against_spain` (a Catalonia flag) and
    `name = CAT_tribute` (a tech-bonus name) out of this.
    """
    found: List[Tuple[str, int]] = []
    for m in _CATEGORY_ASSIGN_RE.finditer(text):
        found.append((m.group(1), m.start(1)))
    for body, offset in _block_bodies(text, _KEYED_BLOCK_RE):
        for km in _KEYED_CATEGORY_RE.finditer(body):
            found.append((km.group(1), offset + km.start(1)))
    listed = [_LISTED_BLOCK_RE]
    if tech_file:
        listed.append(_TECH_CATEGORIES_RE)
    for opener in listed:
        for body, offset in _block_bodies(text, opener):
            for tm in _TOKEN_RE.finditer(body):
                found.append((tm.group(0), offset + tm.start()))
    return found


def _tag_tokens(text: str) -> List[Tuple[str, int]]:
    """Every (token, char_offset) declared inside a technology_categories block."""
    found: List[Tuple[str, int]] = []
    for body, offset in _block_bodies(text, _CATEGORIES_BLOCK_RE):
        for tm in _TOKEN_RE.finditer(body):
            found.append((tm.group(0), offset + tm.start()))
    return found


def load_known_categories(paths: Iterable[str]) -> FrozenSet[str]:
    """Every category token declared in the given technology_tags files."""
    known: Set[str] = set()
    for path in paths:
        try:
            text = FileOpener.open_text_file(path, strip_comments_flag=True)
        except (OSError, UnicodeDecodeError):
            continue
        known.update(name for name, _ in _tag_tokens(text))
    return frozenset(known)


def _suggest(name: str, known: FrozenSet[str], by_lower: Dict[str, str]) -> str:
    """The real tag an unknown reference most likely meant, or ''."""
    lowered = name.lower()
    if lowered in by_lower:
        return by_lower[lowered]
    legacy = _LEGACY_CATEGORIES.get(lowered)
    if legacy in known:
        return legacy
    close = difflib.get_close_matches(name, known, n=1, cutoff=0.6)
    return close[0] if close else ""


def _check_file(args) -> List[Tuple[str, str, int]]:
    """Worker: return (category, relpath, line) for unknown references."""
    filepath, known, mod_path = args
    try:
        text = FileOpener.open_text_file(filepath, strip_comments_flag=True)
    except (OSError, UnicodeDecodeError):
        return []
    rel = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    out: List[Tuple[str, str, int]] = []
    for name, offset in _references(text, tech_file=rel.startswith(_TECH_DIR)):
        if name in known:
            continue
        out.append((name, rel, text.count("\n", 0, offset) + 1))
    return out


def _tech_categories(args) -> Set[str]:
    """Worker: every category token a tech file assigns."""
    (filepath,) = args
    try:
        text = FileOpener.open_text_file(filepath, strip_comments_flag=True)
    except (OSError, UnicodeDecodeError):
        return set()
    return {
        tm.group(0)
        for body, _ in _block_bodies(text, _TECH_CATEGORIES_RE)
        for tm in _TOKEN_RE.finditer(body)
    }


class Validator(BaseValidator):
    TITLE = "TECHNOLOGY CATEGORY VALIDATION"

    def _load_known_categories(self) -> FrozenSet[str]:
        """Every category token declared under common/technology_tags/."""
        known = load_known_categories(
            self._collect_files([_TAGS_GLOB], ignore_staged=True)
        )
        self.log(f"  Known category set: {len(known)} names")
        return known

    def _declared_tags(self) -> List[Tuple[str, str, int]]:
        """(token, relpath, line) for every declaration, in file order."""
        out: List[Tuple[str, str, int]] = []
        for path in self._collect_files([_TAGS_GLOB], ignore_staged=True):
            try:
                text = FileOpener.open_text_file(path, strip_comments_flag=True)
            except (OSError, UnicodeDecodeError):
                continue
            rel = os.path.relpath(path, self.mod_path).replace(os.sep, "/")
            for name, offset in _tag_tokens(text):
                out.append((name, rel, text.count("\n", 0, offset) + 1))
        return out

    def validate_category_references(self, known: FrozenSet[str]):
        self._log_section("Checking technology category references...")
        if not known:
            self._report(
                [
                    (
                        "No technology categories found under common/technology_tags/",
                        "common/technology_tags",
                        0,
                    )
                ],
                "",
                "Technology category set is empty:",
                severity=Severity.ERROR,
                category="tech-category-set-missing",
            )
            return

        # _collect_files already applies should_skip_file against the mod-relative
        # path. Re-filtering on the absolute path here would skip everything when
        # mod_path itself lives under .claude/worktrees/.
        files = self._collect_files(_VALIDATE_PATTERNS)
        self.log(f"  Checking {len(files)} files...")
        batches = self._pool_map(
            _check_file, [(f, known, self.mod_path) for f in files], chunksize=30
        )

        # Report each unknown name once: repeated use is not evidence of validity
        # and would otherwise bury the finding under identical lines.
        first_seen: Dict[str, Tuple[str, int]] = {}
        for batch in batches:
            for name, rel, line in batch:
                first_seen.setdefault(name, (rel, line))

        by_lower = {k.lower(): k for k in known}
        formatted = []
        for name, (rel, line) in sorted(
            first_seen.items(), key=lambda kv: (kv[1][0], kv[1][1])
        ):
            suggestion = _suggest(name, known, by_lower)
            hint = f", did you mean '{suggestion}'?" if suggestion else ""
            formatted.append((f"Unknown technology category '{name}'{hint}", rel, line))

        self._report(
            formatted,
            "No unknown technology categories found",
            "Unknown technology categories (compile silently, grant nothing):",
            severity=Severity.ERROR,
            category="unknown-tech-category",
        )

    def validate_tag_definitions(self, known: FrozenSet[str]):
        """Every declared tag is CAT_lowercase, localised and used by a tech."""
        if not known:
            return
        self._log_section("Checking technology category definitions...")
        declared = self._declared_tags()

        self._report(
            [
                (f"Technology category '{name}' is not CAT_lowercase", rel, line)
                for name, rel, line in declared
                if not _TAG_FORMAT_RE.match(name)
            ],
            "All technology categories are CAT_lowercase",
            "Technology categories not named CAT_lowercase:",
            severity=Severity.ERROR,
            category="tech-category-name-format",
        )

        loc_keys = self._load_localisation_keys()
        unlocalised = []
        for name, rel, line in declared:
            missing = [k for k in (name, f"{name}_research") if k not in loc_keys]
            if missing:
                unlocalised.append(
                    (
                        f"Technology category '{name}' has no English loc key "
                        f"{', '.join(missing)}",
                        rel,
                        line,
                    )
                )
        self._report(
            unlocalised,
            "All technology categories are localised",
            "Technology categories missing a name or _research loc key:",
            severity=Severity.ERROR,
            category="tech-category-unlocalised",
        )

        tech_files = self._collect_files([_TECH_GLOB], ignore_staged=True)
        used: Set[str] = set()
        for cats in self._pool_map(_tech_categories, [(f,) for f in tech_files]):
            used.update(cats)
        self._report(
            [
                (
                    f"Technology category '{name}' is not used by any technology",
                    rel,
                    line,
                )
                for name, rel, line in declared
                if name not in used
            ],
            "All technology categories are used by a technology",
            "Technology categories no technology carries:",
            severity=Severity.ERROR,
            category="tech-category-unused",
        )

    def run_validations(self):
        known = self.cached("tech_categories", self._load_known_categories)
        self.validate_category_references(known)
        self.validate_tag_definitions(known)


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate technology category references in Millennium Dawn mod",
    )
