from collections import Counter
from pathlib import Path

import pytest
from targeted_operations_core_test import TargetScript
from targeted_operations_model_test import _parse_race_script

ROOT = Path(__file__).resolve().parents[3]


def _event(event_id, filename):
    blocks = _parse_race_script(
        "source = {" + (ROOT / filename).read_text(encoding="utf-8") + "}"
    )["source"]
    return next(
        body
        for kind, _, body in blocks
        if kind == "country_event" and ("id", "=", event_id) in body
    )


def _option(event_id, name, filename):
    return next(
        body
        for key, _, body in _event(event_id, filename)
        if key == "option" and ("name", "=", name) in body
    )


class StalkerScript(TargetScript):
    """Execute story effects with the shared scope and timed-flag interpreter."""

    def __init__(self):
        super().__init__()
        self.state(698, 2)
        for filename in (
            "99_STALKER_scripted_effects.txt",
            "99_STALKER_world_effects.txt",
            "99_STALKER_strelok_effects.txt",
            "99_STALKER_intel_effects.txt",
            "99_STALKER_faction_wars_effects.txt",
            "99_STALKER_society_effects.txt",
            "99_STALKER_top_effects.txt",
        ):
            self.effects.update(
                _parse_race_script(
                    (ROOT / "common/scripted_effects" / filename).read_text(
                        encoding="utf-8"
                    )
                )
            )
        self.triggers.update(
            {
                name: [("always", "=", "yes")]
                for name in (
                    "STALKER_scenario_enabled",
                    "STALKER_is_active_zone_anchor",
                )
            }
        )
        self.stubs.update(
            {
                "STALKER_target_zone",
                "STALKER_refresh_zone_administration",
                "small_expenditure",
            }
        )
        self.external = Counter()
        self.actor = 1
        for identifier, tag in enumerate(
            ("ENG", "FRA", "SOV", "IND", "BEL", "GER"), 900
        ):
            if self.tag(tag) is None:
                self.country(identifier, tag=tag)
            identifier = self.tag(tag)
            self.countries[identifier].update(states=[], ideas={"EU_member"})
        self.countries[self.tag("CHI")]["ideas"] = {"EU_member"}
        self.countries[698]["vars"]["STALKER_zone_id"] = 1
        self.countries[698]["controller"] = 2
        self.globals["p5_sc_members"] = [
            self.tag(tag) for tag in ("USA", "ENG", "FRA", "SOV", "CHI", "IND")
        ]
        self.goto(2012, 1)

    def value(self, name, identifier):
        if name == "ROOT":
            return self.actor
        if name == "event_target:STALKER_zone_event_target":
            return 698
        if isinstance(name, str) and name.startswith("PREV."):
            scope, key = self._scope(name, identifier)
            return scope.get(key, 0)
        return super().value(name, identifier)

    def condition_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "PREV":
            return self.scoped(
                operand, identifier, self.value(key, identifier), condition=True
            )
        if key.isdigit():
            return self.scoped(operand, identifier, int(key), condition=True)
        if key == "event_target:STALKER_zone_event_target":
            return self.scoped(operand, identifier, 698, condition=True)
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key in {"set_state_flag", "clr_state_flag"}:
            super().execute_statement(
                (key.replace("state", "country"), "=", operand), identifier
            )
        elif key == "every_country":
            limits = next(body for name, _, body in operand if name == "limit")
            body = [entry for entry in operand if entry[0] != "limit"]
            for country, data in self.countries.items():
                if "controller" not in data and data["exists"]:
                    if self.scoped(limits, identifier, country, condition=True):
                        self.scoped(body, identifier, country)
        elif key in {"ROOT", "PREV", "event_target:STALKER_zone_event_target"}:
            self.scoped(operand, identifier, self.value(key, identifier))
        elif key == "FROM":
            self.scoped(operand, identifier, 698)
        elif key == "set_temp_variable_to_random":
            fields = {name: value for name, _, value in operand}
            self.temps[fields["var"]] = float(fields["max"])
        elif key.isdigit():
            self.scoped(operand, identifier, int(key))
        else:
            super().execute_statement(statement, identifier)

    def hidden_option(self, event_id, name, filename):
        self.execute(
            next(
                body
                for key, _, body in _option(event_id, name, filename)
                if key == "hidden_effect"
            ),
            self.actor,
        )

    def prepare_original_zone(self):
        self.actor = 2
        self.run("STALKER_initialize_zone_society", 698)
        self.countries[698]["vars"].update(
            STALKER_zone_activity=50,
            STALKER_zone_containment=50,
            STALKER_zone_exploitation=50,
        )


@pytest.mark.parametrize("permanent_controller", [False, True])
def test_council_queues_the_live_permanent_roster_once(permanent_controller):
    script = StalkerScript()
    zone_controller = script.tag("IND") if permanent_controller else 2
    script.countries[698]["controller"] = zone_controller
    script.run("STALKER_schedule_security_council", 1)
    recipients = [country for country, event in script.events if event == "STALKER.137"]
    expected = set(script.globals["p5_sc_members"]) | {zone_controller}
    assert set(recipients) == expected
    assert len(recipients) == len(expected)
    assert script.globals["STALKER_unsc_expected"] == len(expected)
    script.run("STALKER_schedule_security_council", 1)
    assert len(script.events) == len(expected)


def test_council_keeps_the_assigned_zone_seat_when_control_changes():
    script = StalkerScript()
    script.run("STALKER_schedule_security_council", 1)
    script.countries[698]["controller"] = 3
    script.run("STALKER_refresh_unsc_expected", 1)
    assert script.globals["STALKER_unsc_expected"] == 7
    for member in script.globals["p5_sc_members"]:
        script.countries[member]["flags"]["STALKER_unsc_voted"] = None
    script.globals["STALKER_unsc_ballots"] = 6
    script.run("STALKER_finish_security_council", 1)
    assert "STALKER_unsc_resolved" not in script.global_flags
    script.countries[2]["flags"]["STALKER_unsc_voted"] = None
    script.globals["STALKER_unsc_ballots"] = 7
    script.run("STALKER_finish_security_council", 1)
    assert "STALKER_unsc_resolved" in script.global_flags


@pytest.mark.parametrize("voted,expected", [(False, 6), (True, 7)])
def test_annexed_seats_drop_only_uncast_ballots(voted, expected):
    script = StalkerScript()
    script.run("STALKER_schedule_security_council", 1)
    member = script.tag("IND")
    script.countries[member]["exists"] = False
    if voted:
        script.countries[member]["flags"]["STALKER_unsc_voted"] = None
        script.globals["STALKER_unsc_ballots"] = 1
    script.run("STALKER_refresh_unsc_expected", 1)
    assert script.globals["STALKER_unsc_expected"] == expected


@pytest.mark.parametrize("option", ["a", "b", "c"])
@pytest.mark.parametrize("invalid", ["controller", "zone_id", "inactive", "resolved"])
def test_stale_raid_options_cannot_choose_a_route_or_charge_the_former_controller(
    option, invalid
):
    script = StalkerScript()
    script.actor = 2
    script.countries[2]["vars"]["political_power"] = 100
    body = _option("STALKER.161", f"STALKER.161.{option}", "events/STALKER_strelok.txt")
    trigger = next(value for key, _, value in body if key == "trigger")
    assert script.condition(trigger, script.actor)
    if invalid == "controller":
        script.countries[698]["controller"] = 3
    elif invalid == "zone_id":
        script.countries[698]["vars"]["STALKER_zone_id"] = 2
    elif invalid == "inactive":
        script.triggers["STALKER_is_active_zone_anchor"] = [("always", "=", "no")]
    else:
        script.global_flags["STALKER_2012_resolved"] = None
    assert not script.condition(trigger, script.actor)
    before = script.countries[698]["vars"].copy()
    script.hidden_option(
        "STALKER.161", f"STALKER.161.{option}", "events/STALKER_strelok.txt"
    )
    assert "STALKER_2012_route" not in script.globals
    assert script.countries[2]["vars"]["political_power"] == 100
    assert script.countries[698]["vars"] == before


@pytest.mark.parametrize("mercenaries,intel,leader", [(39, 100, 11), (41, 0, 6)])
def test_intel_drift_refreshes_the_leader_when_mercenaries_gain_or_lose_the_lead(
    mercenaries, intel, leader
):
    script = StalkerScript()
    script.globals["STALKER_active_zone_anchors"] = [698]
    variables = script.countries[698]["vars"]
    script.run("STALKER_initialize_zone_society", 698)
    variables.update(
        STALKER_zone_military=40,
        STALKER_zone_mercenaries=mercenaries,
        STALKER_zone_foreign_intel=intel,
        STALKER_zone_exploitation=0,
    )
    script.countries[698]["flags"].update(
        STALKER_mercenary_cooldown=None, STALKER_foreign_agents_cooldown=None
    )
    script.run("STALKER_update_zone_leader", 698)
    assert variables["STALKER_zone_leader"] != leader
    script.run("STALKER_monthly_intel_pulse", 1)
    assert variables["STALKER_zone_leader"] == leader


@pytest.mark.parametrize("containment", [50, 25, 15])
@pytest.mark.parametrize("shelter", [False, True])
@pytest.mark.parametrize("shielding", [False, True])
def test_emission_stability_uses_the_unscoped_temp_across_controller_scope(
    containment, shelter, shielding
):
    script = StalkerScript()
    state = script.countries[698]
    state["vars"].update(
        STALKER_zone_containment=containment,
        STALKER_zone_activity=40,
        STALKER_zone_mutants=10,
        STALKER_emission_stability=0.4,
    )
    if shelter:
        state["flags"]["STALKER_emission_shelter"] = None
    if shielding:
        script.countries[2]["flags"]["STALKER_psi_shielding"] = None
    script.run("STALKER_trigger_emission", 698)
    expected = 0 if shielding else (-0.005 if shelter else -0.02)
    if not shielding and containment - (0 if shelter else 5) < 20:
        expected -= 0.01
    assert script.countries[2]["vars"].get("stability", 0) == pytest.approx(expected)
    assert "STALKER_emission_shelter" not in state["flags"]
    assert state["vars"]["STALKER_emission_stability"] == 0.4


def test_lost_2012_carrier_reaches_the_new_controller_once_after_the_due_date():
    script = StalkerScript()
    script.global_flags["STALKER_2012_dispatched"] = None
    script.countries[2]["exists"] = False
    script.countries[698]["controller"] = 3
    script.goto(2012, 3)
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert not script.events
    script.goto(2012, 4)
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert script.events == [(3, "STALKER.161")]
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert len(script.events) == 1
    script.countries[698]["controller"] = 4
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert script.events[-1] == (4, "STALKER.161")
    script.global_flags["STALKER_2012_resolved"] = None
    script.countries[698]["controller"] = 5
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert len(script.events) == 2


@pytest.mark.parametrize("zone_id", [1, 2, 27])
@pytest.mark.parametrize(
    "event_id,option,filename",
    [
        ("STALKER.27", "a", "events/STALKER_international.txt"),
        ("STALKER.27", "b", "events/STALKER_international.txt"),
        ("STALKER.46", "a", "events/STALKER_regional.txt"),
        ("STALKER.47", "b", "events/STALKER_regional.txt"),
    ],
)
def test_generic_zone_options_cannot_populate_original_only_factions(
    zone_id, event_id, option, filename
):
    script = StalkerScript()
    script.actor = 2
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_initialize_zone_society", 698)
    for field in ("activity", "containment", "exploitation", "mutants"):
        variables[f"STALKER_zone_{field}"] = 50
    before = variables.copy()
    script.hidden_option(event_id, f"{event_id}.{option}", filename)
    assert variables["STALKER_zone_duty"] == (
        before["STALKER_zone_duty"]
        + (
            10
            if event_id == "STALKER.27" and option == "a"
            else 5 if event_id == "STALKER.46" else 0
        )
        if zone_id == 1
        else 0
    )
    assert variables["STALKER_zone_freedom"] == (
        before["STALKER_zone_freedom"]
        + (
            10
            if event_id == "STALKER.27" and option == "b"
            else 5 if event_id == "STALKER.47" else 0
        )
        if zone_id == 1
        else 0
    )
    assert variables != before


@pytest.mark.parametrize("zone_id", [1, 2, 27])
def test_trader_rewards_keep_freedom_in_the_original_zone(zone_id):
    script = StalkerScript()
    script.actor = 2
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_initialize_zone_society", 698)
    variables.update(STALKER_zone_containment=50, STALKER_zone_exploitation=50)
    category = _parse_race_script(
        (ROOT / "common/decisions/STALKER_decisions.txt").read_text(encoding="utf-8")
    )
    decision = next(
        body
        for decisions in category.values()
        for key, _, body in decisions
        if key == "STALKER_license_cordon_trader"
    )
    complete = next(body for key, _, body in decision if key == "complete_effect")
    hidden = next(body for key, _, body in complete if key == "hidden_effect")
    script.execute(hidden, 2)
    assert variables["STALKER_zone_freedom"] == (25 if zone_id == 1 else 0)
    assert variables["STALKER_zone_stalkers"] == 30
    assert variables["STALKER_zone_exploitation"] == 60


@pytest.mark.parametrize("zone_id", [1, 2, 27])
@pytest.mark.parametrize("backed", [2, 3])
def test_tearling_gathering_cannot_make_absent_factions_win(zone_id, backed):
    script = StalkerScript()
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_initialize_zone_society", 698)
    script.run("STALKER_start_tearling_drive", 698)
    variables["STALKER_zone_tearling_backed"] = backed
    script.run("STALKER_gather_tearlings", 698)
    duty = (15 if backed == 2 else 10) if zone_id == 1 else 0
    freedom = (15 if backed == 3 else 10) if zone_id == 1 else 0
    assert variables["STALKER_zone_tearlings_duty"] == duty
    assert variables["STALKER_zone_tearlings_freedom"] == freedom
    assert variables["STALKER_zone_tearlings_stalkers"] == 10


@pytest.mark.parametrize("zone_id", [1, 2, 27])
@pytest.mark.parametrize("option,backed", [("b", 2), ("c", 3)])
def test_absent_factions_cannot_accept_paid_tearling_backing(zone_id, option, backed):
    script = StalkerScript()
    script.actor = 2
    script.countries[2]["vars"]["political_power"] = 50
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_start_tearling_drive", 698)
    body = _option(
        "STALKER.150", f"STALKER.150.{option}", "events/STALKER_faction_wars.txt"
    )
    trigger = next(value for key, _, value in body if key == "trigger")
    assert script.condition(trigger, 2) == (zone_id == 1)
    script.hidden_option(
        "STALKER.150", f"STALKER.150.{option}", "events/STALKER_faction_wars.txt"
    )
    assert variables["STALKER_zone_tearling_backed"] == (backed if zone_id == 1 else 0)
    assert script.countries[2]["vars"]["political_power"] == (
        25 if zone_id == 1 else 50
    )
