from pathlib import Path

import pytest
from great_ai_race_state_model_test import _parse_race_script
from targeted_operations_core_test import TargetScript
from targeted_operations_helpers_test import TargetedScript

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = ROOT / "common/scripted_effects/03_targeted_operations_security.txt"
TRIGGERS = ROOT / "common/scripted_triggers/03_targeted_operations_security.txt"


class SecurityScript(TargetedScript):
    """Execute policy source with roster and economy interfaces as fixtures."""

    country_trigger_fields = {
        "has_political_power": "power",
        "num_of_controlled_states": "states",
    }

    def __init__(self):
        self.effects = _parse_race_script(EFFECTS.read_text(encoding="utf-8"))
        self.triggers = _parse_race_script(TRIGGERS.read_text(encoding="utf-8"))
        self.globals = {"TOP_clock": 7}
        self.temps, self.scope_stack, self.charges = {}, [], []
        self.enabled = True
        self.protected = {1: 2, 2: 0}
        self.countries = {
            identifier: {
                "vars": {"treasury": 10},
                "exists": identifier > 0,
                "ai": False,
                "eligible": True,
                "official": False,
                "power": 200,
                "states": 1,
                "flags": {},
            }
            for identifier in (0, 1, 2, 3)
        }

    def condition_statement(self, statement, identifier):
        key, comparison, operand = statement
        country = self.countries[identifier]
        if key.startswith("var:"):
            target = self.value(key[4:], identifier)
            result = self.condition(operand, target)
        elif key == "TOP_enabled":
            result = self.enabled == (operand == "yes")
        elif key == "TOP_country_eligible":
            eligible = self.enabled and country["exists"] and country["eligible"]
            result = eligible == (operand == "yes")
        elif key == "TOP_has_protected_official":
            result = country["official"] == (operand == "yes")
        else:
            result = super().condition_statement(statement, identifier)
        return result

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key == "add_political_power":
            self.countries[identifier]["power"] += self.value(operand, identifier)
        elif key == "TOP_get_protection_country":
            self.temps["TOP_security_country"] = self.protected.get(
                self.temps.get("TOP_target"), 0
            )
        else:
            super().execute_statement(statement, identifier)

    def run(self, name, identifier=1):
        if name == "modify_treasury_effect":
            amount = self.temps["treasury_change"]
            self.countries[identifier]["vars"]["treasury"] += amount
            self.charges.append((identifier, amount))
        else:
            self.execute(self.effects[name], identifier)

    def purchase(self, track, level, identifier=2):
        # $TRACK$ was spliced into the variable name, so there is one effect per
        # track now, and $LEVEL$ is read from a temp variable.
        self.temps["TOP_arg_level"] = level
        self.execute([(f"TOP_purchase_{track}_policy", "=", "yes")], identifier)

    def modifiers(self, target=1, attacker=1):
        self.temps["TOP_target"] = target
        self.run("TOP_get_defensive_modifiers", attacker)
        return tuple(
            self.temps[f"TOP_defensive_{name}"]
            for name in ("collection_penalty", "success_penalty", "exposure_bonus")
        )


@pytest.mark.parametrize("level,pp,cash", [(1, 25, 0.25), (2, 40, 0.75), (3, 60, 1.5)])
@pytest.mark.parametrize("track", ["protection", "counterintelligence"])
def test_policy_charges_once_and_applies_only_its_track(track, level, pp, cash):
    game = SecurityScript()
    country = game.countries[2]
    country["power"] = pp
    country["vars"]["treasury"] = cash
    game.purchase(track, level)
    assert country["power"] == 0
    assert country["vars"]["treasury"] == 0
    assert game.charges == [(2, -cash)]
    assert country["vars"][f"TOP_{track}_until"] == 189
    expected = (0, 5 * level, 0) if track == "protection" else (3 * level, 0, 5 * level)
    assert game.modifiers() == expected


@pytest.mark.parametrize(
    "field,value",
    [("power", 24.999), ("treasury", 0.24), ("eligible", False), ("states", 0)],
)
def test_purchase_refuses_unaffordable_or_ineligible_country(field, value):
    game = SecurityScript()
    country = game.countries[2]
    (country["vars"] if field == "treasury" else country)[field] = value
    game.purchase("protection", 1)
    assert game.charges == []
    assert "TOP_protection_until" not in country["vars"]


@pytest.mark.parametrize("level", [-1, 0, 4, 100])
def test_invalid_policy_level_does_not_spend_or_create_policy(level):
    game = SecurityScript()
    game.purchase("protection", level)
    assert game.charges == []
    assert game.modifiers() == (0, 0, 0)


def test_renewal_replaces_tier_and_expiry_without_stacking():
    game = SecurityScript()
    game.purchase("protection", 3)
    game.purchase("counterintelligence", 2)
    game.globals["TOP_clock"] = 35
    game.purchase("protection", 1)
    country = game.countries[2]["vars"]
    assert country["TOP_protection_until"] == 217
    assert country["TOP_counterintelligence_until"] == 189
    assert game.modifiers() == (6, 5, 10)


def test_expiry_is_effective_without_a_country_tick():
    game = SecurityScript()
    game.purchase("protection", 3)
    game.purchase("counterintelligence", 3)
    game.globals["TOP_clock"] = 188
    assert game.modifiers() == (9, 15, 15)
    game.globals["TOP_clock"] = 189
    assert game.modifiers() == (0, 0, 0)
    game.run("TOP_security_refresh_view", 2)
    assert game.countries[2]["vars"]["TOP_protection_days"] == 0


def test_stand_down_clears_both_policies_without_refund():
    game = SecurityScript()
    game.purchase("protection", 3)
    game.purchase("counterintelligence", 3)
    game.run("TOP_security_stand_down", 2)
    assert game.modifiers() == (0, 0, 0)
    assert game.charges == [(2, -1.5), (2, -1.5)]
    assert game.countries[2]["vars"]["treasury"] == 7


def test_unknown_or_retired_mapping_resets_previous_official_modifiers():
    game = SecurityScript()
    game.purchase("protection", 3)
    game.purchase("counterintelligence", 3)
    assert game.modifiers() == (9, 15, 15)
    assert game.modifiers(target=2) == (0, 0, 0)
    game.protected[1] = 0
    assert game.modifiers() == (0, 0, 0)


def test_annexed_or_domestic_protection_country_gives_no_foreign_bonus():
    game = SecurityScript()
    game.purchase("protection", 3)
    assert game.modifiers(attacker=2) == (0, 0, 0)
    game.countries[2]["exists"] = False
    assert game.modifiers() == (0, 0, 0)


def test_target_selection_and_host_do_not_determine_protection():
    game = SecurityScript()
    game.purchase("protection", 3)
    game.countries[1]["vars"].update(TOP_selected=2, TOP_pending_host=3)
    assert game.modifiers(target=1) == (0, 15, 0)
    assert game.modifiers(target=2) == (0, 0, 0)


def test_independent_protection_owners_do_not_share_policy_levels():
    game = SecurityScript()
    game.protected[2] = 3
    game.purchase("protection", 3, identifier=2)
    game.purchase("counterintelligence", 1, identifier=3)
    assert game.modifiers(target=1) == (0, 15, 0)
    assert game.modifiers(target=2) == (3, 0, 5)


def test_disabled_system_neither_spends_nor_applies_existing_policy():
    game = SecurityScript()
    game.purchase("protection", 3)
    game.enabled = False
    game.purchase("counterintelligence", 3)
    assert game.modifiers() == (0, 0, 0)
    assert game.charges == [(2, -1.5)]


def test_ai_policy_changes_do_not_dirty_the_human_window():
    game = SecurityScript()
    game.countries[2]["ai"] = True
    game.purchase("protection", 3)
    assert "TOP_security_dirty" not in game.countries[2]["vars"]


def test_defensive_access_does_not_require_offensive_country_eligibility():
    game = SecurityScript()
    game.countries[2].update(eligible=False, official=True)
    game.purchase("protection", 2)
    assert game.modifiers() == (0, 10, 0)


def test_wartime_ai_buys_basic_policies_once_and_preserves_active_tiers():
    game = SecurityScript()
    country = game.countries[2]
    country.update(ai=True, official=True, war=True)
    game.run("TOP_security_country_tick", 2)
    assert game.modifiers() == (3, 5, 5)
    assert len(game.charges) == 2
    game.run("TOP_security_country_tick", 2)
    assert len(game.charges) == 2
    game.purchase("protection", 3)
    game.run("TOP_security_country_tick", 2)
    assert game.modifiers() == (3, 15, 5)


@pytest.mark.parametrize(
    "restriction", ["peace", "no_official", "low_power", "low_cash"]
)
def test_ai_avoids_unneeded_or_unaffordable_defensive_spending(restriction):
    game = SecurityScript()
    country = game.countries[2]
    country.update(ai=True, official=True, war=True)
    if restriction == "peace":
        country["war"] = False
    elif restriction == "no_official":
        country["official"] = False
    elif restriction == "low_power":
        country["power"] = 100
    else:
        country["vars"]["treasury"] = 2
    game.run("TOP_security_country_tick", 2)
    assert game.charges == []


def test_parody_badge_has_explicit_non_sponsorship_hover_text():
    path = ROOT / "localisation/english/MD_targeted_operations_security_l_english.yml"
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "Sponsored by Palantir(TM)" in text
    assert "in-game parody" in text
    assert "no actual sponsorship, endorsement, or affiliation" in text


def test_successful_lethal_operation_preserves_pre_retirement_exposure_bonus():
    class ExposureScript(TargetScript):
        def __init__(self):
            super().__init__()
            self.effects.update(_parse_race_script(EFFECTS.read_text(encoding="utf-8")))
            self.triggers.update(
                _parse_race_script(TRIGGERS.read_text(encoding="utf-8"))
            )
            self.stubs.difference_update(
                {"TOP_get_defensive_modifiers", "TOP_apply_exposure"}
            )
            self.stubs.add("TOP_get_protection_country")
            self.exposure_rolls = []

        def run(self, name, identifier):
            if name == "TOP_get_protection_country":
                alive = self.value("global.TOP_status^TOP_target", identifier) == 1
                self.temps["TOP_security_country"] = 2 if alive else 0
            else:
                super().run(name, identifier)

        def execute_statement(self, statement, identifier):
            key, comparison, operand = statement
            if key == "random":
                data = {name: value for name, _, value in operand}
                self.exposure_rolls.append(self.value(data["chance"], identifier))
            else:
                super().execute_statement(statement, identifier)

    game = ExposureScript()
    game.authorize(target=129, method=3)
    game.countries[2]["vars"].update(
        TOP_counterintelligence_level=3, TOP_counterintelligence_until=182
    )
    game.temps["TOP_tier"] = 2
    game.run("TOP_complete_operation", 1)
    assert game.globals["TOP_status"][129] == 3
    assert game.external["TOP_retire_registered_character", 1] == 1
    assert game.temps["TOP_operation_exposure_bonus"] == 15
    assert game.exposure_rolls[0] == 40
    game.run("TOP_get_defensive_modifiers", 1)
    assert game.temps["TOP_defensive_exposure_bonus"] == 0
