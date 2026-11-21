"""Check references against the synchronized dynamic token registry."""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import strip_comments
from validator_common import (
    DYNAMIC_TOKEN_FILE,
    BaseValidator,
    load_dynamic_token_names,
    run_validator_main,
)

CATEGORY = "unregistered-dynamic-token"

# See resources/documentation/dynamic_variables_documentation.md for token targets.
_TOKEN_TARGET_GAME_VARS = (
    "avg_units_acclimation",
    "building_level",
    "damaged_building_level",
    "days_decision_timeout",
    "days_mission_timeout",
    "faction_resource_extracted",
    "global_resource_extracted",
    "leader_modifier",
    "modifier",
    "non_damaged_building_level",
    "num_armies_with_type",
    "num_battalions_with_type",
    "num_deployed_planes_with_type",
    "num_equipment",
    "num_equipment_in_armies",
    "num_equipment_in_armies_k",
    "num_ships_with_type",
    "num_target_equipment",
    "num_target_equipment_in_armies",
    "num_target_equipment_in_armies_k",
    "num_units_defensive_combats_on",
    "num_units_offensive_combats_against",
    "num_units_on_climate",
    "num_units_with_type",
    "party_popularity",
    "party_popularity_100",
    "resource",
    "resource_consumed",
    "resource_exported",
    "resource_imported",
    "resource_produced",
    "sum_unit_terrain_modifier",
    "unit_modifier",
)
_TOKEN_REF_RE = re.compile(
    r"\b(?:token:|(?:"
    + "|".join(_TOKEN_TARGET_GAME_VARS)
    + r")@)([A-Za-z0-9_]+(?:[.\-][A-Za-z0-9_]+)*)"
)

# Vanilla names in use when the check landed. New tokens go in MD_tokens.txt.
_ENGINE_KNOWN_TOKENS = frozenset(
    {
        # buildings
        "air_base",
        "arms_factory",
        "dockyard",
        "fuel_silo",
        "industrial_complex",
        "infrastructure",
        "naval_base",
        "nuclear_reactor",
        "rail_way",
        "rocket_site",
        "supply_node",
        "synthetic_refinery",
        # modifiers
        "agency_upgrade_time",
        "commando_trait_chance_factor",
        "conscription_factor",
        "consumer_goods_expected_value",
        "consumer_goods_factor",
        "industrial_capacity_dockyard",
        "industrial_capacity_factory",
        "local_resources_factor",
        "min_export",
        "political_power_factor",
        "political_power_gain",
        "production_speed_buildings_factor",
        "research_speed_factor",
        "stability_factor",
        "stability_weekly",
        "war_support_factor",
        # equipment and ship types
        "artillery_equipment",
        "capital",
        "carrier",
        "convoy",
        "heavy_tank_chassis",
        "medium_plane_airframe",
        "medium_tank_chassis",
        "small_plane_airframe",
        "small_plane_cas_airframe",
        "small_plane_naval_bomber_airframe",
        "support_ship",
        # ideologies
        "communism",
        "democratic",
        "fascism",
        "neutrality",
        "ruling_party",
        # terrain and climate
        "cold_climate",
        "fort",
        # resources
        "aluminium",
        "chromium",
        "oil",
        "rubber",
        "steel",
        "tungsten",
    }
)


def scan_dynamic_tokens_text(
    cleaned: str, rel: str, registered: frozenset[str]
) -> list[tuple[str, str, int]]:
    """Scan text with comments removed but quoted strings intact."""
    issues: list[tuple[str, str, int]] = []
    if "token:" not in cleaned and "@" not in cleaned:
        return issues
    seen: set[str] = set()
    for match in _TOKEN_REF_RE.finditer(cleaned):
        token = match.group(1)
        # Runtime substitutions and var: targets do not name literal tokens.
        if cleaned.startswith(("[", "$", ":"), match.end()):
            continue
        if token in registered or token in _ENGINE_KNOWN_TOKENS or token in seen:
            continue
        seen.add(token)
        line = cleaned[: match.start()].count("\n") + 1
        issues.append(
            (
                f"{match.group(0)} uses a token that is not registered in"
                f" {DYNAMIC_TOKEN_FILE} (the engine logs a dynamic-token OOS"
                " warning at load)",
                rel,
                line,
            )
        )
    return issues


def registered_dynamic_tokens(mod_path: str) -> frozenset[str]:
    if not os.path.isfile(os.path.join(mod_path, DYNAMIC_TOKEN_FILE)):
        return frozenset()
    return frozenset(load_dynamic_token_names(mod_path))


def _scan_file(args: tuple[str, str, frozenset[str]]) -> list[tuple[str, str, int]]:
    filename, mod_path, registered = args
    text = Path(filename).read_text(encoding="utf-8-sig")
    return scan_dynamic_tokens_text(
        strip_comments(text), os.path.relpath(filename, mod_path), registered
    )


class Validator(BaseValidator):
    TITLE = "DYNAMIC TOKEN VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml", ".gui"]

    def run_validations(self):
        files = (
            self._collect_files(
                ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
            )
            + self._collect_files(["localisation/english/**/*.yml"])
            + self._collect_files(["interface/**/*.gui"])
        )
        if not files:
            return
        self._log_section("Checking script tokens against MD_tokens.txt...")
        registered = registered_dynamic_tokens(self.mod_path)
        args = [(path, self.mod_path, registered) for path in files]
        for message, path, line in self._pool_flat_map(_scan_file, args):
            self.add_error(CATEGORY, message, path, line)


if __name__ == "__main__":
    run_validator_main(Validator, "Validate synchronized dynamic token references")
