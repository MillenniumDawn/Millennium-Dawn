import json
from collections import Counter
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest
from great_ai_race_state_model_test import _named_block, _parse_race_script
from targeted_operations_helpers_test import TargetedScript

ROOT = Path(__file__).resolve().parents[2]


class ScriptArray(list):
    def get(self, index, default=0):
        return self[index] if 0 <= index < len(self) else default


def _seed_bda_archive(variables, entries):
    for target, row, token in entries:
        variables["TOP_bda_archive_row"][target] = row
        variables["TOP_bda_archive_token"][target] = token
        variables["TOP_archive_subject_kind"][row] = 1
        variables["TOP_archive_subject_id"][row] = target
        variables["TOP_archive_bda_token"][row] = token


class TargetScript(TargetedScript):
    """Execute TOP source while recording separately owned engine and legacy effects."""

    def __init__(self):
        self.effects = {}
        for filename in (
            "00_targeted_operations_effects.txt",
            "01_targeted_operations_world.txt",
            "01_targeted_operations_registry.txt",
            "04_targeted_operations_cases.txt",
            "06_targeted_operations_redesign.txt",
            "07_targeted_operations_organization_cases.txt",
            "08_targeted_operations_resolution.txt",
            "09_targeted_operations_depth.txt",
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
        succession = (
            ROOT / "common/scripted_effects/01_targeted_operations_successors.txt"
        ).read_text(encoding="utf-8")
        self.effects.update(
            _parse_race_script(
                _named_block(succession, "TOP_select_authored_successor")
            )
        )
        self.effects["STALKER_check_top_zone_crisis"] = [
            ("set_temp_variable", "=", [("STALKER_top_zone_crisis", "=", "0")])
        ]
        self.triggers = _parse_race_script(
            (
                ROOT / "common/scripted_triggers/01_targeted_operations_triggers.txt"
            ).read_text(encoding="utf-8")
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_triggers/04_targeted_operations_cases.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/02_targeted_operations_authorization_triggers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/03_targeted_operations_political_roster.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/07_targeted_operations_redesign.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_triggers/05_targeted_operations_runtime.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/05_targeted_operations_arg_wrappers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_triggers/99_STALKER_scripted_triggers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        # The STALKER organization gates scope into state 698; the harness keeps those groups inactive.
        for name in (
            "STALKER_top_zone_organization_active",
            "STALKER_top_sircaa_active",
        ):
            self.triggers[name] = [("always", "=", "no")]
        self.countries, self.globals, self.temps = {}, {}, {}
        self.scope_stack, self.events = [], []
        self.global_flags, self.external = {}, Counter()
        self.ineligible_roles = set()
        self.protection_overrides = {}
        self.legacy_first_removals = []
        self.random_draws = 0
        self.today = date(2005, 1, 1)
        self.mode = "TOP_limited_sandbox_option"
        self.stubs = {
            "TOP_initialize_global",
            "TOP_refresh_view",
            "TOP_update_iraq_progress",
            "TOP_apply_legacy_outcome",
            "TOP_apply_legacy_release",
            "TOP_retire_registered_character",
            "TOP_apply_legacy_assessment",
            "TOP_apply_office_successor",
            "TOP_exploit_capture",
            "TOP_apply_exposure",
            "TOP_start_exposed_kill_crisis",
            "TOP_review_tick",
            "TOP_cancel_review",
            "TOP_begin_review",
            "TOP_get_defensive_modifiers",
            "TOP_security_country_tick",
            "TOP_get_protection_country",
            "TOP_build_view",
            "TOP_prepare_authored_service",
            "TOP_refresh_visit_dossiers",
            "TOP_political_country_opportunities",
            "TOP_visit_country_opportunities",
            "TOP_process_visits",
            "TOP_process_crisis",
            "TOP_initialize_doctrine",
            "TOP_seed_public_subjects",
            "international_systems_force_update",
            "STALKER_refresh_zone_administration",
        }
        manifest = json.loads(
            (ROOT / "tools/data/targeted_operations.json").read_text(encoding="utf-8")
        )
        tags = ["---", "USA", "YEM", "PER", "TAL", "AFG", "IRQ", "ISI", "PAK"]
        for group in manifest["groups"]:
            for tag in (
                [group["host"]]
                + group.get("movement_hosts", [])
                + group.get("regional_hosts", [])
            ):
                if tag not in tags:
                    tags.append(tag)
        for ident, tag in enumerate(tags):
            self.country(ident, tag=tag)
            self.countries[ident].update(states=[], exists=ident != 0)
        self.countries[1]["techs"].update(
            {"special_forces_tech_1", "decryption1", "decryption2"}
        )
        self.countries[1]["vars"]["political_power"] = 500
        self.state(100, 1)
        self.state(101, 2)
        self.state(102, 3)
        self.run("TOP_setup_registry", 1)
        self.run("TOP_initialize_redesign_global", 1)
        self.globals.update(
            TOP_rule_mode=1,
            TOP_active_targets=ScriptArray(),
            active_terror_orgs=ScriptArray([0, 10]),
            active_terror_org_threat_lvl=ScriptArray([50, 40]),
        )
        capacity = int(self.globals["TOP_registry_capacity"])
        for field in (
            "TOP_visit_status",
            "TOP_visit_token",
            "TOP_visit_planned_token",
            "TOP_visit_active_token",
            "TOP_visit_story",
            "TOP_visit_start",
            "TOP_visit_until",
            "TOP_visit_execution_until",
            "TOP_visit_host",
            "TOP_visit_state",
            "TOP_visit_return_host",
            "TOP_visit_return_state",
        ):
            self.globals.setdefault(field, ScriptArray([0] * capacity))
        for ident in range(1, len(tags)):
            self.run("TOP_country_initialize", ident)

    def state(self, ident, controller):
        self.country(ident, tag=f"state_{ident}")
        self.countries[ident].update(controller=controller, states=[])
        self.countries[ident]["vars"]["infrastructure"] = 3
        self.countries[ident]["vars"]["arms_factory"] = 2
        self.countries[ident]["vars"]["industrial_complex"] = 2
        self.countries[ident]["resources"] = ["oil"]
        self.countries[controller]["states"].append(ident)

    def tag(self, token):
        return next(
            (ident for ident, data in self.countries.items() if data["tag"] == token),
            None,
        )

    def protection_country(self, target):
        if int(target) in self.protection_overrides:
            return self.protection_overrides[int(target)]
        protection_tags = {
            64: "PER",
            129: "SOV",
            130: "SOV",
            131: "BLR",
            132: "UKR",
            133: "PER",
            134: "PER",
            135: "PER",
            136: "PER",
            137: "PER",
            138: "PER",
            139: "PER",
            140: "PER",
            141: "USA",
            144: "CHI",
            146: "NKO",
            147: "BRM",
            150: "TUR",
            152: "BRA",
            153: "EGY",
            156: "IND",
            158: "SAU",
            159: "ISR",
            160: "VEN",
        }
        return self.tag(protection_tags.get(int(target), "---"))

    def _scope(self, name, identifier):
        if name.startswith("PREV."):
            return self._scope(name[5:], self.scope_stack[-1])
        if "^" in name:
            array, index = name.split("^", 1)
            scope, key = super()._scope(array, identifier)
            values = scope.setdefault(key, ScriptArray())
            if not isinstance(values, ScriptArray):
                values = ScriptArray(values)
                scope[key] = values
            return values, int(self.value(index, identifier))
        return super()._scope(name, identifier)

    def value(self, name, identifier):
        if isinstance(name, str):
            if name in {"THIS", "THIS.id", "ROOT"}:
                return identifier
            if name == "PREV":
                return self.scope_stack[-1]
            if name == "controller":
                return self.countries[identifier].get("controller", 0)
            if name.startswith("var:"):
                return self.value(name[4:], identifier)
            if name.endswith("^num"):
                return len(self.value(name[:-4], identifier) or [])
            country = self.tag(name)
            if country is not None:
                return country
        return super().value(name, identifier)

    def scoped(self, operand, identifier, target, condition=False):
        self.scope_stack.append(identifier)
        try:
            if condition:
                return self.condition(operand, target)
            self.execute(operand, target)
        finally:
            self.scope_stack.pop()

    def condition_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key in {
            "set_temp_variable",
            "add_to_temp_variable",
            "subtract_from_temp_variable",
            "multiply_temp_variable",
            "divide_temp_variable",
            "clamp_temp_variable",
        }:
            self.execute_statement(statement, identifier)
            result = True
        elif key.startswith("var:") or key == "controller" or self.tag(key) is not None:
            result = self.scoped(
                operand, identifier, self.value(key, identifier), condition=True
            )
        elif key == "raid_show_target_intervention_check":
            result = operand == "yes"
        elif key == "has_state_flag":
            result = self._flag(self.countries[identifier]["flags"], operand)
        elif key == "TOP_authored_role_eligible":
            # No longer parameterised: the caller sets TOP_role_target,
            # because the engine cannot substitute $PARAM$ for a trigger.
            result = (
                self.value("TOP_role_target", identifier) not in self.ineligible_roles
            )
        elif key == "TOP_authored_civilian_mandate_valid":
            result = operand == "no"
        elif key == "TOP_review_pending":
            pending = (
                self.value("TOP_proposal_stage", identifier) > 0
                or self.value("TOP_review_event_open", identifier) > 0
            )
            result = pending == (operand == "yes")
        elif key == "TOP_vip_protection_country":
            protection = self.protection_country(
                self.value("TOP_vip_target", identifier)
            )
            result = (identifier == protection) == (operand == "yes")
        elif key == "TOP_target_protection_at_war":
            result = operand == "no"
        elif key in {
            "TOP_case_visit_review_valid",
            "TOP_case_visit_approval_fits",
        }:
            result = operand != "no"
        elif key == "is_in_array":
            name, _, member = operand[0]
            result = self.value(member, identifier) in (
                self.value(name, identifier) or []
            )
        elif key == "is_controlled_by":
            result = self.value("controller", identifier) == self.value(
                operand, identifier
            )
        elif key in {
            "num_of_controlled_states",
            "has_political_power",
            "arms_factory",
            "industrial_complex",
            "infrastructure",
        }:
            value = (
                len(self.countries[identifier]["states"])
                if key == "num_of_controlled_states"
                else self.countries[identifier]["vars"].get(
                    "political_power" if key == "has_political_power" else key, 0
                )
            )
            result = self.comparisons[comparison](
                value, self.value(operand, identifier)
            )
        elif key in {"has_war_with", "is_in_faction_with"}:
            result = self.value(operand, identifier) in self.countries[identifier].get(
                key, set()
            )
        elif key == "has_opinion":
            result = False
        elif key == "has_civil_war":
            result = self.countries[identifier].get("civil_war", False) == (
                operand == "yes"
            )
        elif key == "state_has_any_resource":
            result = bool(self.countries[identifier].get("resources", [])) == (
                operand == "yes"
            )
        elif key == "has_intelligence_agency":
            result = self.countries[identifier].get("intelligence_agency", False) == (
                operand == "yes"
            )
        elif key == "has_country_leader":
            result = True
        elif key == "is_subject":
            result = bool(self.countries[identifier].get("overlord", 0)) == (
                operand == "yes"
            )
        else:
            result = super().condition_statement(statement, identifier)
        return result

    def run(self, name, identifier):
        if name in self.stubs:
            self.external[name, identifier] += 1
            if name == "TOP_get_protection_country":
                self.temps["TOP_security_country"] = self.protection_country(
                    self.value("TOP_target", identifier)
                )
            if name == "TOP_apply_legacy_outcome":
                self.legacy_first_removals.append(
                    self.value("TOP_first_removal", identifier)
                )
        else:
            self.execute(self.effects[name], identifier)

    def call(self, name, identifier=1, **arguments):
        # Scripted effects no longer take parameters: the engine does not
        # substitute $PARAM$ for an effect any more than for a trigger, so each
        # reads a TOP_arg_* temp variable the caller sets first.
        for key, value in arguments.items():
            self.temps[f"TOP_arg_{key.lower()}"] = value
        self.execute(self.effects[name], identifier)

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key in self.stubs:
            self.run(key, identifier)
        elif key == "controller" or self.tag(key) is not None:
            self.scoped(operand, identifier, self.value(key, identifier))
        elif key in {"random_controlled_state", "capital_scope"}:
            states = self.countries[identifier]["states"]
            limits = [value for name, _, value in operand if name == "limit"]
            body = [entry for entry in operand if entry[0] != "limit"]
            for state in states:
                if limits and not all(
                    self.scoped(limit, identifier, state, condition=True)
                    for limit in limits
                ):
                    continue
                self.scoped(body, identifier, state)
                break
        elif key == "resize_array":
            name, _, size = operand[0]
            scope, name = self._scope(name, identifier)
            array = scope.setdefault(name, ScriptArray())
            size = int(self.value(size, identifier))
            array[:] = (array + [0] * size)[:size]
        elif key in {"for_each_loop", "for_loop_effect"}:
            data = {name: value for name, _, value in operand}
            if key == "for_each_loop":
                entries = enumerate(list(self.value(data["array"], identifier) or []))
                metadata = {"array", "index", "value"}
            else:
                start = int(self.value(data.get("start", 0), identifier))
                end = int(self.value(data["end"], identifier))
                if data.get("compare") == "less_than_or_equals":
                    end += 1
                entries = enumerate(range(start, end, int(data.get("add", 1))))
                metadata = {"start", "end", "compare", "add", "value"}
            for index, value in entries:
                self.temps[data.get("value", "v")] = value
                if "index" in data:
                    self.temps[data["index"]] = index
                self.execute(
                    [entry for entry in operand if entry[0] not in metadata], identifier
                )
        elif key == "remove_from_array":
            data = {name: value for name, _, value in operand}
            if "array" in data:
                array = self.value(data["array"], identifier)
                array.pop(int(self.value(data["index"], identifier)))
            else:
                name, _, value = operand[0]
                array = self.value(name, identifier) or []
                member = self.value(value, identifier)
                if member in array:
                    array.remove(member)
        elif key == "modulo_variable":
            name, _, value = operand[0]
            scope, name = self._scope(name, identifier)
            scope[name] %= self.value(value, identifier)
        elif key == "random":
            data = {name: value for name, _, value in operand}
            self.random_draws += 1
            if self.value(data["chance"], identifier) > 0:
                self.execute(
                    [entry for entry in operand if entry[0] != "chance"], identifier
                )
        elif key == "randomize_temp_variable":
            data = {name: value for name, _, value in operand}
            self.random_draws += 1
            self.temps[data["var"]] = self.value(data["min"], identifier)
        elif key == "add_political_power":
            variables = self.countries[identifier]["vars"]
            variables["political_power"] = variables.get(
                "political_power", 0
            ) + self.value(operand, identifier)
        elif key == "add_stability":
            variables = self.countries[identifier]["vars"]
            variables["stability"] = variables.get("stability", 0) + self.value(
                operand, identifier
            )
        elif key == "add_opinion_modifier":
            self.external[key, identifier] += 1
        elif key == "damage_building":
            self.external[key, identifier] += 1
        elif key == "add_dynamic_modifier":
            self.external[key, identifier] += 1
        else:
            super().execute_statement(statement, identifier)

    def target(self, ident=11, status=1, *, host=2, state=101, actor=1):
        for field, value in (("status", status), ("host", host), ("state", state)):
            self.globals[f"TOP_{field}"][ident] = value
        if status == 1 and ident not in self.globals["TOP_active_targets"]:
            self.globals["TOP_active_targets"].append(ident)
        variables = self.countries[actor]["vars"]
        variables["TOP_selected"] = ident
        variables["TOP_selected_kind"] = 1
        dossiers = variables.setdefault("TOP_dossiers", ScriptArray())
        if ident not in dossiers:
            dossiers.append(ident)
        for field, value in (
            ("known", 1),
            ("confidence", 85),
            ("identity_confidence", 85),
            ("location_confidence", 85),
            ("pattern_confidence", 85),
            ("package_state", 1),
            ("lead_state", state),
            ("lead_host", host),
            ("assessment", status),
        ):
            variables[f"TOP_{field}"][ident] = value
        return variables

    def activate_stalker_zone(self, state=101, *, activity=70, containment=40):
        self.global_flags["GLOBAL_STALKER_zone_registry_initialized"] = None
        self.countries[state]["flags"].update(
            STALKER_zone_active=None,
            STALKER_zone_anchor=None,
        )
        self.countries[state]["vars"].update(
            STALKER_zone_activity=activity,
            STALKER_zone_containment=containment,
        )
        # Zone activation seeds the society that STALKER_clamp_zone_society clamps.
        for faction in (
            "stalkers",
            "duty",
            "freedom",
            "bandits",
            "monolith",
            "scientists",
            "military",
            "exploitation",
        ):
            self.countries[state]["vars"].setdefault(f"STALKER_zone_{faction}", 0)

    def organization_truth(self, group=12, *, host=2, state=101, public=False):
        if public:
            self.globals["TOP_group_public_identity"][group] = 1
        for field, value in (
            ("window", 1),
            ("created", 1),
            ("destroyed", 0),
            ("host", host),
            ("state", state),
        ):
            self.globals[f"TOP_group_{field}"][group] = value

    def authorize(self, target=11, method=1, *, host=2, state=101, actor=1, begin=True):
        variables = self.target(target, host=host, state=state, actor=actor)
        for field, value in (
            ("host", host),
            ("state", state),
            ("method", method),
            ("until", 91),
            ("phase", 2),
            ("due", 0),
            ("sequence", target),
            ("facility", 2),
            ("assurance", 85),
            ("rigor", 1),
            ("identity", 85),
            ("location", 85),
            ("pattern", 85),
            ("lead_age", 0),
            ("access", method),
            ("host_posture", 4 if method == 5 else 1),
            ("doctrine", 2),
            ("capability", 85),
            ("protection", host),
            ("exposure_score", 65),
            ("harm_risk", 15),
        ):
            variables[f"TOP_case_{field}"][target] = value
        active = variables.setdefault("TOP_active_cases", ScriptArray())
        if target not in active:
            active.append(target)
        self.call("TOP_load_case", actor, TARGET=target)
        self.temps.update(
            TOP_target=target,
            TOP_method=method,
            TOP_operation_state=state,
            target_state=state,
            TOP_facility_kind=2,
        )
        if begin:
            self.call("TOP_begin_person_operation", actor, TARGET=target)
        return variables

    def authorize_organization(
        self, group=2, objective=1, *, host=3, state=102, actor=1, begin=True
    ):
        variables = self.countries[actor]["vars"]
        self.globals["TOP_group_created"][group] = 1
        self.globals["TOP_group_window"][group] = 1
        self.globals["TOP_group_destroyed"][group] = 0
        self.globals["TOP_group_class"][group] = 1
        self.globals["TOP_group_host"][group] = host
        self.globals["TOP_group_state"][group] = state
        variables["TOP_selected_kind"] = 2
        variables["TOP_selected_organization"] = group
        if group not in variables["TOP_organization_dossiers"]:
            variables["TOP_organization_dossiers"].append(group)
        for field, value in (
            ("known", 1),
            ("verification", 85),
            ("location", 85),
            ("activity", 85),
            ("lead_age", 0),
            ("lead_state", state),
            ("lead_host", host),
            ("package_state", 1),
        ):
            variables[f"TOP_org_{field}"][group] = value
        for field, value in (
            ("host", host),
            ("state", state),
            ("until", 91),
            ("phase", 2),
            ("due", 0),
            ("sequence", group),
            ("objective", objective),
            ("verification", 85),
            ("location", 85),
            ("activity", 85),
            ("lead_age", 0),
            ("access", 3),
            ("host_posture", 1),
            ("doctrine", 2),
            ("capability", 85),
            ("exposure_score", 45),
            ("harm_risk", 15),
        ):
            variables[f"TOP_org_case_{field}"][group] = value
        if group not in variables["TOP_active_organization_cases"]:
            variables["TOP_active_organization_cases"].append(group)
        if begin:
            self.call("TOP_begin_organization_operation", actor, GROUP=group)
        self.temps["TOP_group_target"] = group
        return variables

    def persisted_clone(self):
        restored = TargetScript()
        restored.countries = deepcopy(self.countries)
        restored.globals = deepcopy(self.globals)
        restored.global_flags = deepcopy(self.global_flags)
        restored.ineligible_roles = set(self.ineligible_roles)
        restored.today, restored.mode = self.today, self.mode
        return restored


def case_snapshot(script, target, actor=1):
    variables = script.countries[actor]["vars"]
    return {
        name: value[target]
        for name, value in variables.items()
        if name.startswith("TOP_case_") and isinstance(value, list)
    }


@pytest.mark.parametrize("initial", [0, 1, 2, 3, 4])
def test_import_enrolls_only_active_people_once_and_consumes_location(initial):
    script = TargetScript()
    script.globals["TOP_status"][11] = initial
    script.temps["TOP_import_state"] = 101
    script.call("TOP_import_target_location", 2, TARGET=11)
    script.call("TOP_import_target_location", 2, TARGET=11)
    assert script.globals["TOP_active_targets"].count(11) == int(initial < 2)
    assert script.globals["TOP_status"][11] == (1 if initial < 2 else initial)
    assert script.temps["TOP_import_state"] == 0


def test_capture_release_recapture_does_not_repeat_lifetime_rewards():
    script = TargetScript()
    variables = script.target()
    script.call("TOP_capture_target", TARGET=11)
    rewarded_pp = variables["political_power"]
    threat = list(script.globals["active_terror_org_threat_lvl"])
    script.run("TOP_release_selected", 1)
    script.call("TOP_capture_target", TARGET=11)
    assert script.globals["TOP_status"][11] == 2
    assert script.globals["TOP_removals"][11] == 1
    assert variables["political_power"] == rewarded_pp
    assert script.globals["active_terror_org_threat_lvl"] == threat
    assert script.globals["TOP_exploited"][11] == 0
    assert script.globals["TOP_exploitation_until"][11] == 14
    assert script.external["TOP_exploit_capture", 1] == 0
    assert script.legacy_first_removals == [1, 0]


def test_transferred_prisoner_is_known_and_manageable_by_recipient():
    script = TargetScript()
    variables = script.target(status=2)
    script.globals["TOP_custodian"][11] = 1
    variables["TOP_transfer_country"] = 2
    script.run("TOP_transfer_selected", 1)
    recipient = script.countries[2]["vars"]
    assert script.globals["TOP_custodian"][11] == 2
    assert script.globals["TOP_custody_state"][11] == 101
    assert script.globals["TOP_custody_state"][0] == 0
    assert recipient["TOP_known"][11] == 1
    assert recipient["TOP_assessment"][11] == 2
    assert 11 in recipient["TOP_dossiers"]
    recipient["TOP_selected"] = 11
    assert script.condition(script.triggers["TOP_custody_owned"], 2)


def test_delayed_assessment_retains_original_method_state_and_uncertainty():
    script = TargetScript()
    variables = script.authorize()
    script.temps["TOP_tier"] = 2
    script.run("TOP_complete_operation", 1)
    assert variables["TOP_archive_result"][0] == 5
    assert variables["TOP_assessment"][11] == 5
    script.authorize(12, method=4, host=3, state=102)
    variables["TOP_case_due"][12] = 100
    script.globals["TOP_state"][11] = 102
    script.globals["TOP_clock"] = 15
    script.run("TOP_process_timers", 1)
    assert variables["TOP_assessment"][11] == 3
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_result"][0] == 3
    assert variables["TOP_archive_target"][0] == 11
    assert variables["TOP_archive_method"][0] == 1
    assert variables["TOP_archive_state"][0] == 101


def test_legacy_capture_cannot_borrow_an_unrelated_mandate():
    script = TargetScript()
    variables = script.authorize(target=12, method=4)
    script.target(11)
    script.call("TOP_capture_target", TARGET=11)
    assert variables["TOP_archive_target"][0] == 11
    assert variables["TOP_archive_method"][0] == 0
    assert variables["TOP_archive_state"][0] == 101


@pytest.mark.parametrize(
    ("outcome", "status"),
    (("TOP_capture_target", 2), ("TOP_kill_target", 3)),
)
def test_legacy_result_cannot_borrow_a_loaded_case_for_the_same_target(outcome, status):
    script = TargetScript()
    variables = script.authorize(target=11, method=5, host=2, state=101)

    script.call(outcome, TARGET=11)

    assert script.globals["TOP_status"][11] == status
    assert variables["TOP_archive_method"][0] == 0
    assert variables["TOP_archive_sequence"][0] == 0
    if status == 2:
        assert script.globals["TOP_custodian"][11] == 1
    else:
        assert variables["TOP_bda_method"][11] == 0

    script.run("TOP_process_cases", 1)
    assert variables["TOP_case_phase"][11] == 5
    assert variables["TOP_assessment"][11] == 6
    assert variables["TOP_operation_subject_kind"] == 0
    assert variables["TOP_operation_subject_id"] == 0


@pytest.mark.parametrize("objective", (1, 2, 3))
def test_facility_sabotage_damages_the_map_without_removing_a_person(objective):
    script = TargetScript()
    variables = script.authorize_organization(objective=objective, host=2, state=101)
    original_person_status = list(script.globals["TOP_status"])
    script.run("TOP_resolve_organization_operation", 1)
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_subject_kind"][0] == 2
    assert variables["TOP_archive_subject_id"][0] == 2
    assert variables["TOP_archive_objective"][0] == objective
    assert variables["TOP_archive_result"][0] == 11
    assert script.external["damage_building", 101] == 1
    assert variables["TOP_report_objective"] == objective
    assert variables["TOP_report_impact"] == objective
    assert script.globals["TOP_group_disruption_type"][2] == objective
    assert script.globals["TOP_group_disruption_until"][2] == 90
    assert script.globals["TOP_status"] == original_person_status


def test_successful_person_operation_disturbs_an_active_stalker_zone():
    script = TargetScript()
    variables = script.authorize(method=1, state=101)
    state = script.countries[101]["vars"]
    script.activate_stalker_zone()
    snapshot = variables["TOP_case_state"][11]
    script.temps["TOP_tier"] = 2

    script.run("TOP_resolve_person_operation", 1)

    assert variables["TOP_case_result"][11] == 3
    assert state["STALKER_zone_activity"] == 80
    assert state["STALKER_zone_containment"] == 30
    assert variables["TOP_case_state"][11] == snapshot
    assert script.external["STALKER_refresh_zone_administration", 2] == 1


def test_successful_organization_sabotage_disturbs_an_active_stalker_zone():
    script = TargetScript()
    variables = script.authorize_organization(objective=1, host=2, state=101)
    state = script.countries[101]["vars"]
    script.activate_stalker_zone()

    script.run("TOP_resolve_organization_operation", 1)

    assert variables["TOP_archive_result"][0] == 11
    assert state["STALKER_zone_activity"] == 80
    assert state["STALKER_zone_containment"] == 30
    assert script.external["STALKER_refresh_zone_administration", 2] == 1


def test_no_contact_person_operation_does_not_disturb_a_stalker_zone():
    script = TargetScript()
    variables = script.authorize(method=1, state=101)
    state = script.countries[101]["vars"]
    script.activate_stalker_zone()
    variables["TOP_case_identity"][11] = 0
    script.temps["TOP_tier"] = 2

    script.run("TOP_resolve_person_operation", 1)

    assert variables["TOP_case_result"][11] == 1
    assert state["STALKER_zone_activity"] == 70
    assert state["STALKER_zone_containment"] == 40
    assert script.external["STALKER_refresh_zone_administration", 2] == 0


def test_successful_person_operation_leaves_zone_unchanged_when_scenario_is_off():
    script = TargetScript()
    variables = script.authorize(method=1, state=101)
    state = script.countries[101]["vars"]
    state.update(STALKER_zone_activity=70, STALKER_zone_containment=40)
    state_flags = script.countries[101]["flags"]
    state_flags.update(STALKER_zone_active=None, STALKER_zone_anchor=None)
    script.temps["TOP_tier"] = 2

    script.run("TOP_resolve_person_operation", 1)

    assert variables["TOP_case_result"][11] == 3
    assert state["STALKER_zone_activity"] == 70
    assert state["STALKER_zone_containment"] == 40
    assert script.external["STALKER_refresh_zone_administration", 2] == 0


def test_top_zone_disturbance_clamps_society_bounds():
    script = TargetScript()
    script.authorize(method=1, state=101)
    state = script.countries[101]["vars"]
    script.activate_stalker_zone(activity=95, containment=5)
    script.temps["TOP_tier"] = 2

    script.run("TOP_resolve_person_operation", 1)

    assert state["STALKER_zone_activity"] == 100
    assert state["STALKER_zone_containment"] == 0


@pytest.mark.parametrize(
    "objective,arms,infrastructure,available",
    [
        (1, 0, 1, True),
        (1, 1, 0, False),
        (2, 1, 0, True),
        (2, 0, 1, True),
        (2, 0, 0, False),
        (3, 0, 0, True),
    ],
)
def test_organization_facility_availability_matches_objective_fallbacks(
    objective, arms, infrastructure, available
):
    script = TargetScript()
    state = script.countries[101]["vars"]
    state.update(arms_factory=arms, infrastructure=infrastructure, industrial_complex=0)
    script.temps.update(TOP_facility_state=101, TOP_facility_objective=objective)

    assert (
        script.condition(script.triggers["TOP_organization_facility_available"], 1)
        == available
    )


@pytest.mark.parametrize("objective", (1, 2))
def test_organization_operation_cannot_report_damage_when_no_fallback_exists(
    objective,
):
    script = TargetScript()
    variables = script.authorize_organization(
        objective=objective, host=2, state=101, begin=False
    )
    script.countries[101]["vars"].update(arms_factory=0, infrastructure=0)

    script.call("TOP_begin_organization_operation", GROUP=2)
    assert variables["TOP_org_case_phase"][2] == 2

    variables["TOP_org_case_phase"][2] = 3
    script.temps["TOP_group_target"] = 2
    script.run("TOP_resolve_organization_operation", 1)
    assert variables["TOP_archive_result"][0] == 9
    assert script.external["damage_building", 101] == 0
    assert script.globals["TOP_group_disruption_type"][2] == 0


def test_training_report_records_infrastructure_fallback():
    script = TargetScript()
    variables = script.authorize_organization(objective=2, host=2, state=101)
    script.countries[101]["vars"].update(arms_factory=0, infrastructure=1)

    script.run("TOP_resolve_organization_operation", 1)

    assert variables["TOP_report_result"] == 11
    assert variables["TOP_report_objective"] == 2
    assert variables["TOP_report_impact"] == 1
    assert script.external["damage_building", 101] == 1


def test_failed_organization_report_records_attempt_without_damage():
    script = TargetScript()
    variables = script.authorize_organization(objective=1, host=2, state=101)
    variables["TOP_org_case_verification"][2] = 0

    script.run("TOP_resolve_organization_operation", 1)

    assert variables["TOP_report_result"] == 1
    assert variables["TOP_report_objective"] == 1
    assert variables["TOP_report_impact"] == 0
    assert script.external["damage_building", 101] == 0
    assert script.globals["TOP_group_disruption_type"][2] == 0


def test_open_field_report_preserves_queued_objective_and_impact_after_reload():
    script = TargetScript()
    variables = script.authorize_organization(group=2, objective=2, host=3, state=102)
    script.run("TOP_resolve_organization_operation", 1)
    assert variables["TOP_report_objective"] == 2
    assert variables["TOP_report_impact"] == 2

    variables["TOP_selected_organization"] = 3
    variables["TOP_org_case_objective"][2] = 1
    script.authorize_organization(group=3, objective=3, host=2, state=101)
    script.countries[101]["vars"]["industrial_complex"] = 0
    script.run("TOP_resolve_organization_operation", 1)
    assert script.external["add_dynamic_modifier", 101] == 1
    assert variables["TOP_report_subject_ids"] == [3]
    assert variables["TOP_report_objectives"] == [3]
    assert variables["TOP_report_impacts"] == [4]

    script.temps.update(
        TOP_report_enqueue_kind=1,
        TOP_report_enqueue_id=11,
        TOP_report_enqueue_result=1,
        TOP_report_enqueue_state=101,
        TOP_report_enqueue_host=2,
        TOP_report_enqueue_objective=0,
        TOP_report_enqueue_impact=0,
    )
    script.run("TOP_queue_field_report", 1)
    restored = script.persisted_clone()
    reports = restored.countries[1]["vars"]

    assert reports["TOP_report_subject_id"] == 2
    assert reports["TOP_report_objective"] == 2
    assert reports["TOP_report_impact"] == 2
    restored.run("TOP_finish_field_report", 1)
    assert reports["TOP_report_subject_kind"] == 2
    assert reports["TOP_report_subject_id"] == 3
    assert reports["TOP_report_objective"] == 3
    assert reports["TOP_report_impact"] == 4
    restored.run("TOP_finish_field_report", 1)
    assert reports["TOP_report_subject_kind"] == 1
    assert reports["TOP_report_subject_id"] == 11
    assert reports["TOP_report_objective"] == 0
    assert reports["TOP_report_impact"] == 0
    assert reports["TOP_report_subject_ids"] == []


def test_partner_operation_revalidates_cooperative_posture_before_execution():
    script = TargetScript()
    variables = script.authorize(method=5, begin=False)
    variables["TOP_case_host_posture"][11] = 5
    script.call("TOP_begin_person_operation", TARGET=11)
    assert variables["TOP_case_phase"][11] == 2
    assert script.globals["TOP_attempts"][11] == 0
    assert variables["TOP_archive_cursor"] == 0
    assert variables["TOP_operation_subject_kind"] == 0

    variables["TOP_case_host_posture"][11] = 4
    script.call("TOP_begin_person_operation", TARGET=11)
    assert variables["TOP_case_phase"][11] == 3
    assert variables["TOP_operation_subject_kind"] == 1


@pytest.mark.parametrize(
    "trigger", ["TOP_native_authorized", "TOP_mission_binding_valid"]
)
def test_changed_state_controller_invalidates_authorization(trigger):
    script = TargetScript()
    script.authorize()
    # These triggers no longer take parameters; they read temp variables.
    script.temps.update({"TOP_arg_target": 11, "TOP_arg_method": 1})
    statements = script.triggers[trigger]
    assert script.condition(statements, 1)
    script.countries[101]["controller"] = 3
    assert not script.condition(statements, 1)


def test_organization_execution_revalidates_the_recorded_state_controller():
    script = TargetScript()
    variables = script.authorize_organization(
        objective=1, host=2, state=101, begin=False
    )
    script.temps["TOP_arg_group"] = 2
    statements = script.triggers["TOP_can_begin_organization_operation"]
    assert script.condition(statements, 1)
    script.countries[101]["controller"] = 3
    assert not script.condition(statements, 1)
    script.call("TOP_begin_organization_operation", GROUP=2)
    assert variables["TOP_org_case_phase"][2] == 2


def test_ai_cannot_designate_collect_or_begin_a_person_operation():
    script = TargetScript()
    variables = script.target()
    script.countries[1]["ai"] = True
    variables["TOP_package_state"][11] = 0
    power = variables["political_power"]
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][11] == 0
    assert variables["political_power"] == power

    variables["TOP_package_state"][11] = 1
    script.run("TOP_collect_selected", 1)
    assert variables["TOP_collecting_subjects"] == []

    script.authorize(begin=False)
    script.call("TOP_begin_person_operation", TARGET=11)
    assert variables["TOP_case_phase"][11] == 2
    assert variables["TOP_operation_subject_kind"] == 0


def test_ai_cannot_begin_an_organization_operation():
    script = TargetScript()
    variables = script.authorize_organization(begin=False)
    script.countries[1]["ai"] = True
    script.call("TOP_begin_organization_operation", GROUP=2)
    assert variables["TOP_org_case_phase"][2] == 2
    assert variables["TOP_operation_subject_kind"] == 0


def test_ai_can_assign_vip_protection_without_gaining_offensive_authority():
    script = TargetScript()
    defender_id = script.tag("PER")
    defender = script.target(135, host=defender_id, state=102, actor=defender_id)
    script.globals["TOP_leader_role"][135] = 4
    script.countries[defender_id]["ai"] = True
    defender.update(political_power=25, treasury=0.25)
    script.temps["TOP_arg_target"] = 135

    assert script.condition(script.triggers["TOP_can_assign_vip_detail"], defender_id)
    assert not script.condition(script.triggers["TOP_human_offense"], defender_id)


def test_vip_detail_is_pruned_when_the_authored_protection_country_changes():
    script = TargetScript()
    protector = script.tag("PER")
    replacement = max(script.countries) + 1
    script.country(replacement, tag="HEZ")
    variables = script.target(135, host=protector, state=102, actor=protector)
    script.globals["TOP_leader_role"][135] = 4
    variables["TOP_vip_assignments"].append(135)
    variables["TOP_vip_until"][135] = 91

    script.run("TOP_refresh_vip_details", protector)
    assert variables["TOP_vip_assignments"] == [135]

    script.protection_overrides[135] = replacement
    script.run("TOP_refresh_vip_details", protector)

    assert variables["TOP_vip_assignments"] == []


def test_traveling_leader_deception_uses_the_authored_protection_country():
    class FalseLocationScript(TargetScript):
        def __init__(self):
            self.random_chances = []
            super().__init__()

        def execute_statement(self, statement, identifier):
            key, _, operand = statement
            if key == "random":
                fields = {name: value for name, _, value in operand}
                self.random_chances.append(self.value(fields["chance"], identifier))
                return
            super().execute_statement(statement, identifier)

    script = FalseLocationScript()
    protector = script.tag("SOV")
    visitor_host = script.tag("USA")
    script.target(129, host=visitor_host, state=100)
    script.temps["TOP_target"] = 129
    script.countries[protector]["vars"]["TOP_deception_until"] = 91
    script.countries[visitor_host]["vars"]["TOP_deception_until"] = 0
    script.random_chances.clear()

    script.run("TOP_maybe_false_person_location", 1)

    assert script.random_chances == [40]

    script.countries[protector]["vars"]["TOP_deception_until"] = 0
    script.countries[visitor_host]["vars"]["TOP_deception_until"] = 91
    script.random_chances.clear()
    script.run("TOP_maybe_false_person_location", 1)

    assert script.random_chances == [15]


def test_ai_custodian_can_transfer_after_exploitation_while_human_keeps_control():
    script = TargetScript()
    script.target(11, status=2)
    script.globals["TOP_custodian"][11] = 1
    script.globals["TOP_affiliation"][11] = 1
    script.globals["TOP_group_host"][1] = 2
    script.countries[1]["ai"] = True

    script.call("TOP_ai_manage_custody", TARGET=11)
    assert script.globals["TOP_custodian"][11] == 2

    script.globals["TOP_custodian"][11] = 1
    script.countries[1]["ai"] = False
    script.call("TOP_ai_manage_custody", TARGET=11)
    assert script.globals["TOP_custodian"][11] == 1


def test_generated_native_raids_have_no_offensive_ai_weight():
    raids = (ROOT / "common/raids/targeted_operations_raids.txt").read_text(
        encoding="utf-8"
    )
    assert raids.count("ai_will_do = {") > 0
    assert raids.count("ai_will_do = { base = 0 }") == raids.count("ai_will_do = {")
    assert "TOP_ai_choose_operation" not in "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in (ROOT / "common/scripted_effects").glob("*targeted_operations*.txt")
    )


@pytest.mark.parametrize("group,target,host", [(1, 7, 5), (3, 36, 7)])
def test_later_targets_can_activate_after_original_host_loses_territory(
    group, target, host
):
    script = TargetScript()
    script.state(110, host)
    script.globals["TOP_window"][target] = 1
    script.globals["TOP_group_window"][group] = 1
    script.run(f"TOP_activate_group_{group}", 1)
    assert script.globals["TOP_status"][target] == 1
    assert script.globals["TOP_host"][target] == host
    assert script.globals["TOP_state"][target] == 110
    assert script.globals["TOP_active_targets"].count(target) == 1


def test_exhausted_succession_preserves_group_and_cannot_redirect_backlash():
    script = TargetScript()
    script.target(12, status=3)
    script.globals["TOP_office"][12] = 1
    for index in range(65, 129):
        script.globals["TOP_generated_used"][index] = 1
        script.globals["TOP_status"][index] = 3
    script.temps["TOP_target"] = 12
    script.run("TOP_choose_successor", 1)
    assert script.globals["TOP_group_leader"][2] == 0
    assert script.globals["TOP_active_targets"] == []
    assert script.globals["active_terror_orgs"] == [0, 10]
    script.globals["TOP_backlash"][2] = 3
    script.run("TOP_global_monthly", 1)
    assert script.globals["active_terror_org_threat_lvl"] == [50, 41]
    assert script.globals["TOP_backlash"][2] == 2
    assert script.globals["TOP_backlash"][0] == 0


@pytest.mark.parametrize("first_outcome", ["TOP_capture_target", "TOP_kill_target"])
def test_competing_countries_cannot_resolve_or_reward_the_same_person_twice(
    first_outcome,
):
    script = TargetScript()
    script.target()
    script.countries[2]["vars"]["political_power"] = 200
    script.call(first_outcome, TARGET=11)
    first_status = script.globals["TOP_status"][11]
    script.call("TOP_capture_target", 2, TARGET=11)
    script.call("TOP_kill_target", 2, TARGET=11)
    assert script.globals["TOP_status"][11] == first_status
    assert script.globals["TOP_removals"][11] == 1
    assert script.countries[2]["vars"]["political_power"] == 200
    assert script.countries[2]["vars"]["TOP_archive_cursor"] == 0
    assert script.external["TOP_exploit_capture", 2] == 0


@pytest.mark.parametrize("writes", [128, 129, 257])
def test_archive_rollover_retains_exactly_the_most_recent_128_results(writes):
    script = TargetScript()
    variables = script.authorize()
    script.temps["TOP_result"] = 9
    for day in range(writes):
        script.globals["TOP_clock"] = day
        script.run("TOP_archive_result", 1)
    assert variables["TOP_archive_cursor"] == writes % 128
    assert len(variables["TOP_archive_rows"]) == 128
    assert len(set(variables["TOP_archive_rows"])) == 128
    assert set(variables["TOP_archive_day"]) == set(range(writes - 128, writes))
    for field in ("target", "result", "method", "day", "state"):
        assert len(variables[f"TOP_archive_{field}"]) == 128


def test_last_registry_slot_has_all_arrays_and_can_be_resolved():
    script = TargetScript()
    capacity = len(script.globals["TOP_status"])
    target = capacity - 1
    variables = script.target(target)
    script.call("TOP_capture_target", TARGET=target)
    script.call("TOP_kill_target", TARGET=target)
    assert script.globals["TOP_status"][target] == 3
    assert script.globals["TOP_removals"][target] == 1
    assert variables["TOP_capture_exploited"][target] == 0
    assert script.globals["TOP_exploited"][target] == 0
    for name, array in script.globals.items():
        if (
            name.startswith("TOP_")
            and isinstance(array, list)
            and name
            not in {
                "TOP_active_targets",
                "TOP_pending_actors",
                "TOP_backlash",
                "TOP_detained_targets",
                "TOP_detained_next",
            }
            and not name.startswith("TOP_group_")
        ):
            assert len(array) == capacity, name
    for name, array in variables.items():
        if (
            name.startswith("TOP_")
            and isinstance(array, list)
            and name
            not in {
                "TOP_dossiers",
                "TOP_pending_assessments",
                "TOP_active_cases",
                "TOP_cases_to_close",
                "TOP_retired_native_bindings",
                "TOP_vip_assignments",
                "TOP_collecting_subjects",
                "TOP_organization_dossiers",
                "TOP_active_organization_cases",
                "TOP_attribution_pending_people",
                "TOP_attribution_pending_organizations",
                "TOP_liaison_partners",
                "TOP_liaison_sources",
                "TOP_visible_members",
                "TOP_transfer_recipients",
                "TOP_custody_event_queue",
                "TOP_report_subject_kinds",
                "TOP_report_subject_ids",
                "TOP_report_results",
                "TOP_report_states",
                "TOP_report_hosts",
                "TOP_report_objectives",
                "TOP_report_impacts",
                "TOP_bda_notice_targets",
                "TOP_bda_notice_assessments",
                "TOP_bda_notice_sequences",
                "TOP_bda_notice_rows",
                "TOP_pressure_notice_kinds",
                "TOP_pressure_notice_ids",
                "TOP_pressure_notice_tiers",
                "TOP_pressure_notice_actors",
                "TOP_visible_history",
            }
            and not name.startswith("TOP_archive_")
            and not name.startswith("TOP_history_")
            and not name.startswith("TOP_org_")
        ):
            assert len(array) == capacity, name


@pytest.mark.parametrize("boundary", ["reserved", "one_past_end"])
def test_reserved_and_out_of_bounds_ids_cannot_resolve(boundary):
    script = TargetScript()
    target = 0 if boundary == "reserved" else len(script.globals["TOP_status"])
    before = deepcopy(script.globals)
    script.call("TOP_capture_target", TARGET=target)
    assert script.globals == before
    assert script.countries[1]["vars"]["TOP_archive_cursor"] == 0


@pytest.mark.parametrize(
    "mode,expected_mode",
    [
        ("TOP_limited_sandbox_option", 1),
        ("TOP_full_sandbox_option", 2),
        ("TOP_disabled_option", 0),
    ],
)
def test_game_rule_cache_initializes_fresh_campaign(mode, expected_mode):
    script = TargetScript()
    script.mode = mode
    script.globals.pop("TOP_rule_mode")
    script.run("TOP_cache_game_rule", 1)
    assert script.globals.get("TOP_rule_mode", 0) == expected_mode


def test_disabled_rule_keeps_global_and_country_state_inert():
    script = TargetScript()
    script.target()
    script.mode = "TOP_disabled_option"
    script.globals["TOP_rule_mode"] = 0
    before = deepcopy((script.globals, script.countries))
    script.call("TOP_capture_target", TARGET=11)
    script.call("TOP_import_target_location", 2, TARGET=12)
    script.run("TOP_global_weekly", 1)
    script.run("TOP_global_monthly", 1)
    assert (script.globals, script.countries) == before


@pytest.mark.parametrize(
    "target,method,state", [(12, 1, 101), (11, 2, 101), (11, 1, 102)]
)
def test_native_callback_for_a_superseded_binding_cannot_touch_current_case(
    target, method, state
):
    script = TargetScript()
    variables = script.authorize()
    original_case = case_snapshot(script, 11)
    script.globals["TOP_status"][12] = 1
    script.temps.update(
        actor_country=1,
        target_state=state,
        TOP_target=target,
        TOP_method=method,
        TOP_tier=2,
    )
    script.call("TOP_native_result_args")
    assert script.globals["TOP_status"][11] == 1
    assert script.globals["TOP_status"][12] == 1
    assert script.globals["TOP_attempts"][11] == 0
    assert case_snapshot(script, 11) == original_case
    assert variables["TOP_archive_cursor"] == 0


@pytest.mark.parametrize("identity,expected", [(85, 3), (60, 6)])
def test_lethal_bda_waits_fourteen_days_and_never_rerolls_physical_truth(
    identity, expected
):
    script = TargetScript()
    variables = script.authorize(method=3)
    variables["TOP_case_identity"][11] = identity
    script.run("TOP_complete_operation", 1)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_removals"][11] == 1
    assert variables["TOP_attempts"][11] == 1
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_physical"][0] == 3
    assert variables["TOP_assessment"][11] == 5
    assert variables["TOP_case_phase"][11] == 4

    script.globals["TOP_clock"] = 7
    script.run("TOP_process_timers", 1)
    assert variables["TOP_assessment"][11] == 5
    assert variables["TOP_case_phase"][11] == 4

    script.globals["TOP_clock"] = 14
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_removals"][11] == 1
    assert script.globals["TOP_attempts"][11] == 1
    assert variables["TOP_assessment"][11] == expected
    assert variables["TOP_case_phase"][11] == 5
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_result"][0] == expected
    assert variables["TOP_archive_physical"][0] == 3
    assert variables["TOP_archive_method"][0] == 3
    assert variables["TOP_archive_state"][0] == 101


def test_country_tick_does_not_convert_global_death_truth_into_local_bda():
    script = TargetScript()
    observer = script.target(11, actor=3)
    observer["TOP_assessment"][11] = 1
    script.call("TOP_kill_target", 1, TARGET=11)

    script.run("TOP_country_tick", 3)

    assert script.globals["TOP_confirmed_dead"][11] == 1
    assert observer["TOP_assessment"][11] == 1


def test_confirmed_investigation_upgrades_the_matching_open_leader_crisis():
    script = TargetScript()
    variables = script.authorize(begin=False)
    script.globals["TOP_leader_role"][11] = 1
    variables["TOP_case_attribution"][11] = 3
    variables["TOP_case_crisis_opened"][11] = 1
    variables["TOP_case_protection"][11] = 2
    variables["TOP_case_result"][11] = 3
    script.globals.update(
        TOP_crisis_active=1,
        TOP_crisis_actor=1,
        TOP_crisis_target=11,
        TOP_crisis_protection=2,
        TOP_crisis_attribution=2,
        TOP_crisis_tension=40,
    )
    script.temps.update(TOP_target=11, TOP_result=3)

    script.run("TOP_apply_shared_consequences", 1)

    assert script.globals["TOP_crisis_attribution"] == 3
    assert script.globals["TOP_crisis_tension"] == 40


def test_annexed_custodian_hands_prisoner_to_prison_controller_without_losing_credit():
    script = TargetScript()
    script.target()
    script.call("TOP_capture_target", TARGET=11)
    assert script.globals["TOP_custody_state"][11] == 100
    assert script.globals["TOP_detained_targets"] == [11]
    script.countries[1]["exists"] = False
    script.countries[100]["controller"] = 3
    script.run("TOP_update_detained_targets", 2)
    script.run("TOP_update_detained_targets", 2)
    recipient = script.countries[3]["vars"]
    assert script.globals["TOP_status"][11] == 2
    assert script.globals["TOP_custodian"][11] == 3
    assert script.globals["TOP_custody_state"][11] == 102
    assert script.globals["TOP_detained_targets"] == [11]
    assert script.globals["TOP_removals"][11] == 1
    assert 11 not in script.globals["TOP_active_targets"]
    assert recipient["TOP_known"][11] == 1
    assert recipient["TOP_assessment"][11] == 2
    assert recipient["TOP_dossiers"] == [11]
    assert script.external["TOP_exploit_capture", 3] == 0
    assert script.external["TOP_update_iraq_progress", 2] == 2


@pytest.mark.parametrize("end_custody", ["TOP_release_selected", "TOP_kill_target"])
def test_released_or_dead_people_leave_bounded_detention_processing(end_custody):
    script = TargetScript()
    script.target()
    script.call("TOP_capture_target", TARGET=11)
    if end_custody == "TOP_kill_target":
        script.call(end_custody, TARGET=11)
    else:
        script.run(end_custody, 1)
    script.run("TOP_update_detained_targets", 2)
    assert script.globals["TOP_detained_targets"] == []


def test_returning_org_identity_reopens_activation_without_resurrecting_removed_people():
    script = TargetScript()
    script.globals["TOP_group_window"][2] = 1
    script.globals["TOP_status"][12] = 3
    script.globals["TOP_window"][12] = 1
    script.globals["TOP_window"][13] = 1
    script.run("TOP_reconcile_organizations", 1)
    script.globals["active_terror_orgs"] = ScriptArray([0, 14])
    script.run("TOP_reconcile_organizations", 1)
    assert script.globals["TOP_group_destroyed"][2] == 1
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_status"][13] == 0
    script.globals["active_terror_orgs"].append(10)
    script.run("TOP_reconcile_organizations", 1)
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_group_destroyed"][2] == 0
    assert script.globals["TOP_status"][12] == 3
    assert script.globals["TOP_status"][13] == 1
    assert script.globals["TOP_active_targets"] == [13]
    script.temps["TOP_target"] = 13
    script.run("TOP_find_org", 1)
    assert script.temps["TOP_org_slot"] == 2


def test_designation_allows_multiple_persistent_packages_in_one_host():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_package_state"][11] = 0
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][11] == 1
    script.target(12)
    variables["TOP_package_state"][12] = 0
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][12] == 1
    script.target(13, host=3, state=102)
    variables["TOP_package_state"][13] = 0
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][13] == 1
    assert variables.get("TOP_active_cases", []) == []
    assert variables["political_power"] == 425

    script.countries[3]["vars"]["political_power"] = 100
    script.target(11, actor=3)
    script.countries[3]["vars"]["TOP_package_state"][11] = 0
    script.run("TOP_designate_selected", 3)
    assert script.countries[3]["vars"]["TOP_package_state"][11] == 1
    assert script.countries[3]["vars"]["political_power"] == 75


def fire_native_callback(script, target=11, method=1, tier=2, state=101):
    """Run a raid callback from its own instance scope.

    TOP_native_result_args reads TOP_target, TOP_method and TOP_tier: raids set
    them inline because common/raids/ is parsed before the scripted effects
    register, so a parameterised call there cannot resolve.
    """
    script.country(1000, tag="raid_instance")
    script.countries[1000]["vars"].update(actor_country=1, target_state=state)
    script.temps.pop("target_state", None)
    script.temps.update(TOP_target=target, TOP_method=method, TOP_tier=tier)
    script.call("TOP_native_result_args", 1000)


def test_native_callback_loads_its_person_case_while_another_host_is_selected():
    script = TargetScript()
    variables = script.authorize()
    script.authorize(12, host=3, state=102, begin=False)
    other = case_snapshot(script, 12)
    fire_native_callback(script)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_status"][12] == 1
    assert variables["TOP_case_phase"][11] == 4
    assert case_snapshot(script, 12) == other
    assert variables["TOP_archive_target"][0] == 11
    assert variables["TOP_archive_state"][0] == 101


@pytest.mark.parametrize("method", (1, 2))
def test_native_preparation_waits_for_its_callback_instead_of_timed_resolution(method):
    script = TargetScript()
    variables = script.authorize(method=method)
    assert variables["TOP_case_phase"][11] == 3
    assert variables["TOP_case_due"][11] == 0

    script.globals["TOP_clock"] = 28
    script.run("TOP_process_timers", 1)

    assert variables["TOP_case_phase"][11] == 3
    assert variables["TOP_operation_subject_kind"] == 1
    assert script.globals["TOP_status"][11] == 1
    assert variables["TOP_attempts"][11] == 0
    assert variables["TOP_archive_cursor"] == 0

    fire_native_callback(script, method=method)
    assert variables["TOP_attempts"][11] == 1
    assert variables["TOP_archive_cursor"] == 1


def test_external_resolution_releases_a_matching_preparation_slot_immediately():
    script = TargetScript()
    variables = script.authorize(method=1)
    sequence = variables["TOP_case_sequence"][11]
    assert variables["TOP_operation_sequence"] == sequence

    script.call("TOP_capture_target", 3, TARGET=11)
    script.run("TOP_process_cases", 1)

    assert variables["TOP_case_phase"][11] == 5
    assert variables["TOP_operation_subject_kind"] == 0
    assert variables["TOP_operation_subject_id"] == 0
    assert variables["TOP_operation_sequence"] == 0
    assert variables["TOP_assessment"][11] == 6


def test_exact_duration_dispatches_fire_on_the_due_day():
    script = TargetScript()
    person = script.authorize(method=3)
    assert person["TOP_case_due"][11] == 28
    script.globals["TOP_clock"] = 28
    script.run("TOP_process_cases", 1)
    assert person["TOP_attempts"][11] == 1

    organization = script.authorize_organization(group=2)
    assert organization["TOP_org_case_due"][2] == 56
    script.globals["TOP_clock"] = 56
    script.run("TOP_process_organization_cases", 1)
    assert organization["TOP_org_case_phase"][2] == 5

    script.globals["TOP_active_targets"].append(12)
    script.globals["TOP_pressure"][12] = 10
    script.globals["TOP_pressure_decay_due"] = 56
    script.run("TOP_decay_pressure", 1)
    assert script.globals["TOP_pressure"][12] == 5
    assert script.globals["TOP_pressure_decay_due"] == 84


def test_expired_mandates_return_frozen_person_and_organization_packages():
    script = TargetScript()
    person = script.authorize(begin=False)
    person["TOP_package_state"][11] = 3
    person["TOP_case_until"][11] = 28
    script.globals["TOP_clock"] = 28

    script.run("TOP_process_cases", 1)

    assert person["TOP_case_phase"][11] == 0
    assert person["TOP_package_state"][11] == 1

    organization = script.authorize_organization(group=2, begin=False)
    organization["TOP_org_package_state"][2] = 3
    organization["TOP_org_case_until"][2] = 56
    script.globals["TOP_clock"] = 56

    script.run("TOP_process_organization_cases", 1)

    assert organization["TOP_org_case_phase"][2] == 0
    assert organization["TOP_org_package_state"][2] == 1


def test_stale_case_close_cannot_thaw_a_newer_frozen_package():
    script = TargetScript()
    variables = script.authorize(begin=False)
    variables["TOP_package_state"][11] = 3
    variables["TOP_case_sequence"][11] = 99

    script.call("TOP_close_case", TARGET=11, SEQUENCE=11)

    assert variables["TOP_case_phase"][11] == 2
    assert variables["TOP_package_state"][11] == 3


def test_report_clock_makes_packages_stale_on_the_first_week_after_day_57():
    script = TargetScript()
    variables = script.target()
    variables["TOP_lead_report_clock"][11] = 0
    script.temps["TOP_arg_target"] = 11

    script.globals["TOP_clock"] = 56
    assert script.condition(script.triggers["TOP_person_package_ready"], 1)
    script.globals["TOP_clock"] = 63
    assert not script.condition(script.triggers["TOP_person_package_ready"], 1)

    variables["TOP_org_package_state"][2] = 1
    variables["TOP_org_verification"][2] = 85
    variables["TOP_org_location"][2] = 85
    variables["TOP_org_activity"][2] = 85
    variables["TOP_org_lead_state"][2] = 101
    variables["TOP_org_lead_host"][2] = 2
    variables["TOP_org_lead_report_clock"][2] = 7
    script.temps["TOP_group_target"] = 2
    assert script.condition(script.triggers["TOP_organization_package_ready"], 1)
    script.globals["TOP_clock"] = 70
    assert not script.condition(script.triggers["TOP_organization_package_ready"], 1)


def test_pressure_notice_queue_preserves_concurrent_subjects():
    script = TargetScript()
    host = script.countries[2]["vars"]

    script.temps.update(
        TOP_pressure_enqueue_kind=1,
        TOP_pressure_enqueue_id=129,
        TOP_pressure_enqueue_tier=1,
        TOP_pressure_enqueue_actor=1,
    )
    script.run("TOP_enqueue_pressure_notice", 2)
    script.temps.update(
        TOP_pressure_enqueue_kind=2,
        TOP_pressure_enqueue_id=12,
        TOP_pressure_enqueue_tier=3,
        TOP_pressure_enqueue_actor=3,
    )
    script.run("TOP_enqueue_pressure_notice", 2)

    assert host["TOP_pressure_notice_kinds"] == [1, 2]
    assert host["TOP_pressure_notice_ids"] == [129, 12]
    assert host["TOP_pressure_notice_tiers"] == [1, 3]
    assert host["TOP_pressure_notice_actors"] == [1, 3]
    assert host["TOP_pressure_notice_id"] == 129

    script.run("TOP_finish_pressure_notice", 2)
    assert host["TOP_pressure_notice_kinds"] == [2]
    assert host["TOP_pressure_notice_id"] == 12
    assert host["TOP_pressure_notice_actor"] == 3

    script.run("TOP_finish_pressure_notice", 2)
    assert host["TOP_pressure_notice_kinds"] == []
    assert host["TOP_pressure_notice_open"] == 0


def test_organization_pressure_rechecks_affiliated_member_thresholds():
    script = TargetScript()
    variables = script.target(11)
    group = int(script.globals["TOP_affiliation"][11])
    script.globals["TOP_pressure"][11] = 0
    script.temps.update(TOP_group_target=group, TOP_group_pressure_gain=50)

    script.run("TOP_add_group_pressure", 1)

    assert script.globals["TOP_group_pressure"][group] == 50
    assert script.globals["TOP_pressure_tier"][11] == 1
    assert script.countries[2]["vars"]["TOP_pressure_notice_id"] == 11
    script.temps["TOP_target"] = 11
    script.run("TOP_get_effective_person_pressure", 1)
    assert script.temps["TOP_effective_pressure"] == 25
    assert variables["TOP_package_state"][11] == 1


def test_effective_pressure_cancels_planned_travel_at_the_highest_tier():
    script = TargetScript()
    script.target(11)
    group = int(script.globals["TOP_affiliation"][11])
    script.temps["TOP_visit_trigger_target"] = 11
    script.globals["TOP_pressure"][11] = 74
    script.globals["TOP_group_pressure"][group] = 0
    gate = script.triggers["TOP_visit_pressure_allows_travel"]

    assert script.condition(gate, 1)

    script.globals["TOP_pressure"][11] = 50
    script.globals["TOP_group_pressure"][group] = 50
    assert not script.condition(gate, 1)


@pytest.mark.parametrize(("method", "status"), ((3, 3), (4, 2)))
def test_completed_attempt_keeps_pressure_without_warning_for_a_removed_person(
    method, status
):
    script = TargetScript()
    variables = script.authorize(target=11, method=method, host=2, state=101)
    group = int(script.globals["TOP_affiliation"][11])
    script.temps.update(TOP_target=11, TOP_method=method, TOP_tier=2)

    script.run("TOP_complete_operation", 1)

    assert script.globals["TOP_status"][11] == status
    assert script.globals["TOP_pressure"][11] == 55
    assert script.globals["TOP_group_pressure"][group] == 13.75
    assert script.globals["TOP_pressure_tier"][11] == 2
    defender = script.countries[2]["vars"]
    assert defender["TOP_pressure_notice_open"] == 0
    assert defender["TOP_pressure_notice_ids"] == []
    assert variables["TOP_case_result"][11] == status


def test_ai_cannot_choose_collection_focus_or_facility_objective():
    script = TargetScript()
    variables = script.target(11)
    script.countries[1]["ai"] = True
    variables["TOP_collection_focus"][11] = 1

    script.run("TOP_cycle_person_collection_focus", 1)
    assert variables["TOP_collection_focus"][11] == 1

    variables["TOP_selected_kind"] = 2
    variables["TOP_selected"] = 0
    variables["TOP_selected_organization"] = 2
    variables["TOP_org_known"][2] = 1
    variables["TOP_org_package_state"][2] = 1
    variables["TOP_org_collection_focus"][2] = 1
    variables["TOP_selected_facility"] = 1

    script.run("TOP_cycle_organization_collection_focus", 1)
    script.run("TOP_cycle_selected_facility", 1)

    assert variables["TOP_org_collection_focus"][2] == 1
    assert variables["TOP_selected_facility"] == 1


def test_facility_objective_cannot_change_after_review_or_case_freezes_it():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_selected_kind"] = 2
    variables["TOP_selected"] = 0
    variables["TOP_selected_organization"] = 2
    variables["TOP_org_known"][2] = 1
    variables["TOP_selected_facility"] = 1

    script.run("TOP_cycle_selected_facility", 1)
    assert variables["TOP_selected_facility"] == 2

    variables.update(
        TOP_selected_facility=1,
        TOP_proposal_stage=1,
        TOP_proposal_subject_kind=2,
        TOP_proposal_subject_id=2,
    )
    script.run("TOP_cycle_selected_facility", 1)
    assert variables["TOP_selected_facility"] == 1

    variables["TOP_proposal_stage"] = 0
    variables["TOP_org_case_phase"][2] = 2
    variables["TOP_org_case_objective"][2] = 1
    script.run("TOP_cycle_selected_facility", 1)
    assert variables["TOP_selected_facility"] == 1
    assert variables["TOP_org_case_objective"][2] == 1


def test_foreign_leader_remains_operationally_eligible_after_arriving_on_a_visit():
    script = TargetScript()
    runtime = _parse_race_script(
        (ROOT / "common/scripted_effects/05_targeted_operations_runtime.txt").read_text(
            encoding="utf-8"
        )
    )
    script.effects.update(runtime)
    script.run("TOP_setup_extended_runtime", 1)
    script.mode = "TOP_full_sandbox_option"
    script.globals["TOP_rule_mode"] = 2
    variables = script.target(129)
    group = int(script.globals["TOP_affiliation"][129])
    foreign_host = script.tag("SOV")
    assert foreign_host not in (None, 1)
    script.state(200, foreign_host)
    script.globals["TOP_group_host"][group] = foreign_host
    script.globals["TOP_host"][129] = foreign_host
    script.globals["TOP_state"][129] = 200
    script.countries[1].setdefault("is_in_faction_with", set()).add(foreign_host)
    script.globals["TOP_visit_token"][129] = 1
    script.globals["TOP_visit_planned_token"][129] = 1
    script.globals["TOP_visit_status"][129] = 1
    script.globals["TOP_visit_story"][129] = 1
    script.globals["TOP_visit_host"][129] = 1
    script.globals["TOP_visit_state"][129] = 100
    script.temps["TOP_target"] = 129

    assert script.condition(script.triggers["TOP_person_operational_eligible"], 1)

    script.call("TOP_activate_visit", TARGET=129, STATE=100, STORY=1)

    assert script.globals["TOP_host"][129] == 1
    assert script.globals["TOP_state"][129] == 100
    assert script.condition(script.triggers["TOP_person_operational_eligible"], 1)
    assert variables["TOP_selected"] == 129

    script.countries[foreign_host]["vars"].update(
        political_power=25,
        treasury=0.25,
    )
    script.temps.update(TOP_arg_target=129, TOP_target=129)
    assert script.condition(script.triggers["TOP_can_assign_vip_detail"], foreign_host)
    assert not script.condition(script.triggers["TOP_can_assign_vip_detail"], 1)

    script.temps["TOP_pressure_amount"] = 25
    script.run("TOP_add_person_pressure", 1)
    protector = script.countries[foreign_host]["vars"]
    visit_host = script.countries[1]["vars"]
    assert protector["TOP_pressure_notice_id"] == 129
    assert 129 in protector["TOP_pressure_notice_ids"]
    assert 129 not in visit_host["TOP_pressure_notice_ids"]


def test_authored_civilian_public_figure_has_a_protection_country():
    script = TargetScript()
    script.today = date(2012, 1, 1)
    script.target(141, host=1, state=100)
    script.temps["TOP_target"] = 141

    script.run("TOP_get_protection_country", 2)

    assert script.temps["TOP_security_country"] == 1


def test_ai_liaison_bootstraps_public_reports_without_creating_packages():
    script = TargetScript()
    source = script.countries[2]["vars"]
    requester = script.countries[1]["vars"]
    script.countries[2]["ai"] = True
    script.globals["TOP_status"][129] = 1
    script.globals["TOP_public_identity"][129] = 1
    script.globals["TOP_host"][129] = 2
    script.globals["TOP_state"][129] = 101
    source.update(
        TOP_incoming_liaison_actor=1,
        TOP_incoming_liaison_kind=1,
        TOP_incoming_liaison_id=129,
    )
    script.temps["TOP_liaison_response_reliability"] = 1

    script.run("TOP_answer_liaison_request", 2)

    assert source["TOP_identity_confidence"][129] == 100
    assert source["TOP_location_confidence"][129] == 0
    assert source["TOP_pattern_confidence"][129] == 0
    assert requester["TOP_identity_confidence"][129] == 100
    assert requester["TOP_location_confidence"][129] == 0
    assert requester["TOP_pattern_confidence"][129] == 0
    assert requester["TOP_lead_state"][129] == 0
    assert requester["TOP_lead_host"][129] == 0
    assert source["TOP_package_state"][129] == 0
    assert requester["TOP_package_state"][129] == 0

    script.organization_truth(12, host=2, state=101, public=True)
    source.update(
        TOP_incoming_liaison_actor=1,
        TOP_incoming_liaison_kind=2,
        TOP_incoming_liaison_id=12,
    )
    script.temps["TOP_liaison_response_reliability"] = 1
    script.run("TOP_answer_liaison_request", 2)

    assert requester["TOP_org_verification"][12] == 100
    assert requester["TOP_org_location"][12] == 0
    assert requester["TOP_org_activity"][12] == 0
    assert requester["TOP_org_lead_state"][12] == 0
    assert requester["TOP_org_lead_host"][12] == 0
    assert requester["TOP_org_package_state"][12] == 0


def test_public_organization_seed_writes_the_authored_group_state():
    script = TargetScript()
    variables = script.countries[1]["vars"]
    script.stubs.remove("TOP_seed_public_subjects")
    script.globals["TOP_group_state"][0] = 0
    script.organization_truth(12, host=2, state=0, public=True)

    script.run("TOP_seed_public_subjects", 1)

    assert script.globals["TOP_group_state"][12] == 101
    assert script.globals["TOP_group_state"][0] == 0
    assert variables["TOP_org_known"][12] == 1
    assert variables["TOP_org_verification"][12] == 100


def test_person_lead_adapter_exposes_the_affiliated_organization():
    script = TargetScript()
    script.target(1)
    group = int(script.globals["TOP_affiliation"][1])

    script.call("TOP_add_target_lead", TARGET=1, AMOUNT=5)

    variables = script.countries[1]["vars"]
    assert variables["TOP_org_known"][group] == 1
    assert group in variables["TOP_organization_dossiers"]
    assert variables["TOP_org_lead_state"][group] == 0
    assert variables["TOP_org_lead_host"][group] == 0
    assert variables["TOP_org_lead_report_clock"][group] == 0


def test_strategic_crisis_wrapper_restores_its_case_context():
    script = TargetScript()
    variables = script.authorize(begin=False)
    variables["TOP_case_host"][11] = 2
    variables["TOP_case_state"][11] = 101
    variables["TOP_case_consent"][11] = 1
    variables["TOP_case_visit_token"][11] = 7
    variables["TOP_case_visit_status"][11] = 2
    variables["TOP_case_visit_story"][11] = 4
    variables.update(
        TOP_authorized_host=3,
        TOP_authorized_consent=0,
        TOP_authorized_visit_token=0,
        TOP_authorized_visit_status=0,
        TOP_authorized_visit_story=0,
    )
    script.temps["TOP_target"] = 11

    script.run("TOP_start_strategic_leader_crisis", 1)

    assert variables["TOP_authorized_host"] == 2
    assert variables["TOP_authorized_consent"] == 1
    assert variables["TOP_authorized_visit_token"] == 7
    assert variables["TOP_authorized_visit_status"] == 2
    assert variables["TOP_authorized_visit_story"] == 4
    assert script.temps["TOP_operation_state"] == 101


def test_waiting_mandates_close_at_expiry_but_prepared_native_case_survives():
    script = TargetScript()
    person = script.authorize(begin=False)
    person["TOP_case_until"][11] = 91
    script.globals["TOP_clock"] = 91
    script.run("TOP_process_cases", 1)
    assert person["TOP_case_phase"][11] == 0

    organization = script.authorize_organization(group=2, begin=False)
    organization["TOP_org_case_until"][2] = 98
    script.globals["TOP_clock"] = 98
    script.run("TOP_process_organization_cases", 1)
    assert organization["TOP_org_case_phase"][2] == 0

    script.globals["TOP_clock"] = 0
    native = script.authorize(target=12, method=1)
    native["TOP_case_until"][12] = 105
    script.globals["TOP_clock"] = 106
    script.run("TOP_process_cases", 1)
    assert native["TOP_case_phase"][12] == 3


def test_begun_timed_operations_finish_after_the_waiting_mandate_expires():
    person_script = TargetScript()
    person = person_script.authorize(method=3)
    person["TOP_case_until"][11] = 1
    person_script.globals["TOP_clock"] = 28

    person_script.run("TOP_process_cases", 1)

    assert person["TOP_attempts"][11] == 1
    assert person["TOP_case_phase"][11] == 4

    organization_script = TargetScript()
    organization = organization_script.authorize_organization(group=2)
    organization["TOP_org_case_until"][2] = 1
    organization_script.globals["TOP_clock"] = 28

    organization_script.run("TOP_process_organization_cases", 1)

    assert organization["TOP_org_case_phase"][2] == 5


def test_async_resolution_reloads_the_case_selected_in_the_open_view():
    script = TargetScript()
    script.effects.update(
        _parse_race_script(
            (
                ROOT / "common/scripted_effects/01_targeted_operations_view.txt"
            ).read_text(encoding="utf-8")
        )
    )
    script.stubs.remove("TOP_build_view")
    variables = script.authorize(target=11, method=3)
    script.authorize(target=12, method=4, host=3, state=102, begin=False)
    variables["TOP_selected"] = 12
    variables["TOP_selected_kind"] = 1
    script.temps.update(TOP_target=11, TOP_method=3, TOP_tier=0)

    script.run("TOP_complete_operation", 1)

    assert variables["TOP_authorized_target"] == 12
    assert variables["TOP_authorized_method"] == 4
    assert variables["TOP_case_phase"][12] == 2
    assert variables["TOP_operation_subject_id"] == 0


def test_new_case_generation_clears_prior_displayed_consequence_state():
    script = TargetScript()
    variables = script.target(11)
    for field, value in (("attribution", 3), ("harm", 3), ("result", 6)):
        variables[f"TOP_case_{field}"][11] = value
    variables["TOP_case_archive_row"][11] = 7
    variables["TOP_case_archive_token"][11] = 9

    script.call("TOP_open_person_review_case", TARGET=11)

    for field in ("attribution", "harm", "result", "archive_row", "archive_token"):
        assert variables[f"TOP_case_{field}"][11] == 0

    variables["TOP_org_case_attribution"][2] = 3
    variables["TOP_org_case_harm"][2] = 3
    variables["TOP_org_case_result"][2] = 7
    variables["TOP_org_case_archive_row"][2] = 8
    variables["TOP_org_case_archive_token"][2] = 10
    script.call("TOP_open_organization_review_case", GROUP=2)

    for field in ("attribution", "harm", "result", "archive_row", "archive_token"):
        assert variables[f"TOP_org_case_{field}"][2] == 0


@pytest.mark.parametrize("succeeds", (False, True), ids=("failed", "raised"))
def test_attribution_investigation_applies_consequences_only_when_tier_rises(succeeds):
    class InvestigationScript(TargetScript):
        def execute_statement(self, statement, identifier):
            key, _op, operand = statement
            if key != "random":
                return super().execute_statement(statement, identifier)
            data = {name: value for name, _, value in operand}
            self.random_draws += 1
            if succeeds and self.value(data["chance"], identifier) > 0:
                self.execute(
                    [entry for entry in operand if entry[0] != "chance"], identifier
                )

    script = InvestigationScript()
    variables = script.authorize(target=11, method=3, host=2, begin=False)
    script.authorize_organization(group=2, objective=1, host=3, begin=False)
    script.globals["TOP_clock"] = 14

    variables["TOP_case_attribution"][11] = 1
    variables["TOP_case_attribution_due"][11] = 14
    variables["TOP_case_attribution_investigated"][11] = 0
    variables["TOP_case_result"][11] = 1
    variables["TOP_case_archive_row"][11] = 0
    variables["TOP_case_archive_token"][11] = variables["TOP_case_sequence"][11]
    variables["TOP_archive_subject_kind"][0] = 1
    variables["TOP_archive_subject_id"][0] = 11
    variables["TOP_archive_sequence"][0] = variables["TOP_case_sequence"][11]
    variables["TOP_archive_attribution"][0] = 1
    variables["TOP_attribution_pending_people"] = ScriptArray([11])

    variables["TOP_org_case_attribution"][2] = 1
    variables["TOP_org_case_attribution_due"][2] = 14
    variables["TOP_org_case_attribution_investigated"][2] = 0
    variables["TOP_org_case_result"][2] = 7
    variables["TOP_org_case_archive_row"][2] = 1
    variables["TOP_org_case_archive_token"][2] = variables["TOP_org_case_sequence"][2]
    variables["TOP_archive_subject_kind"][1] = 2
    variables["TOP_archive_subject_id"][1] = 2
    variables["TOP_archive_sequence"][1] = variables["TOP_org_case_sequence"][2]
    variables["TOP_archive_attribution"][1] = 1
    variables["TOP_attribution_pending_organizations"] = ScriptArray([2])

    script.run("TOP_process_attribution_investigations", 1)

    expected = 2 if succeeds else 1
    assert variables["TOP_case_attribution"][11] == expected
    assert variables["TOP_org_case_attribution"][2] == expected
    assert variables["TOP_archive_attribution"][0] == expected
    assert variables["TOP_archive_attribution"][1] == expected
    expected_consequences = 1 if succeeds else 0
    assert script.external["add_opinion_modifier", 2] == expected_consequences
    assert script.external["add_opinion_modifier", 3] == expected_consequences


def test_inactive_former_officeholder_moves_to_cold_and_can_reactivate():
    script = TargetScript()
    script.effects.update(
        _parse_race_script(
            (
                ROOT / "common/scripted_effects/01_targeted_operations_view.txt"
            ).read_text(encoding="utf-8")
        )
    )
    script.stubs.remove("TOP_build_view")
    variables = script.target(129)
    script.ineligible_roles.add(129)
    variables["TOP_status_filter"] = 0
    script.run("TOP_build_view", 1)
    assert variables["TOP_view_subject_active"] == 0
    assert 129 not in variables["TOP_visible_people"]

    variables["TOP_status_filter"] = 1
    script.run("TOP_build_view", 1)
    assert 129 in variables["TOP_visible_people"]

    script.ineligible_roles.remove(129)
    variables["TOP_status_filter"] = 0
    script.run("TOP_build_view", 1)
    assert variables["TOP_view_subject_active"] == 1
    assert 129 in variables["TOP_visible_people"]


@pytest.mark.parametrize("restore", [False, True], ids=["live", "persisted_state"])
def test_waiting_timed_mandates_execute_sequentially_through_one_slot(restore):
    script = TargetScript()
    script.authorize(method=3)
    script.authorize(12, method=4, host=3, state=102)
    if restore:
        script = script.persisted_clone()
    variables = script.countries[1]["vars"]
    assert variables["TOP_case_phase"][11] == 3
    assert variables["TOP_case_phase"][12] == 2
    variables["TOP_selected"] = 0
    script.temps.clear()
    script.globals["TOP_clock"] = 29
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_status"][12] == 1
    assert variables["TOP_case_phase"][11] == 4
    assert variables["TOP_case_phase"][12] == 2
    assert variables["TOP_attempts"][11] == 1
    assert variables["TOP_attempts"][12] == 0

    script.call("TOP_begin_person_operation", TARGET=12)
    assert variables["TOP_case_phase"][12] == 3
    script.globals["TOP_clock"] = 58
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][12] == 2
    assert variables["TOP_archive_cursor"] == 2
    assert variables["TOP_attempts"][11] == variables["TOP_attempts"][12] == 1
    assert set(variables["TOP_archive_target"][:2]) == {11, 12}


def test_assessment_holds_host_after_expiry_and_revoke_until_recorded_confirmation():
    script = TargetScript()
    variables = script.authorize()
    script.temps["TOP_tier"] = 2
    script.run("TOP_complete_operation", 1)
    assert variables["TOP_case_phase"][11] == 4
    script.authorize(12, host=3, state=102, begin=False)
    variables["TOP_case_until"][12] = 300
    other = case_snapshot(script, 12)
    variables["TOP_selected"] = 11
    script.run("TOP_revoke_authorization", 1)
    script.run("TOP_confirm_assessment", 1)
    assert variables["TOP_case_phase"][11] == 4
    script.globals["TOP_clock"] = 100
    script.run("TOP_process_timers", 1)
    assert variables["TOP_case_phase"][11] == 5
    script.call("TOP_find_host_case", HOST=2)
    assert script.temps["TOP_host_case"] == 11
    script.run("TOP_revoke_authorization", 1)
    assert variables["TOP_case_phase"][11] == 5
    script.run("TOP_confirm_assessment", 1)
    assert variables["TOP_case_phase"][11] == 0
    assert variables["TOP_active_cases"] == [12]
    assert case_snapshot(script, 12) == other
    assert script.globals["TOP_status"][11] == 3


def test_another_countrys_kill_changes_global_truth_before_local_reporting():
    script = TargetScript()
    variables = script.authorize()
    script.call("TOP_kill_target", 3, TARGET=11)
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_confirmed_dead"][11] == 1
    assert variables["TOP_case_phase"][11] == 5
    assert variables["TOP_assessment"][11] == 6
    script.run("TOP_confirm_assessment", 1)
    assert variables["TOP_case_phase"][11] == 0


@pytest.mark.parametrize("action", ["close", "revoke", "expire"])
def test_closing_one_case_preserves_other_hosts_and_rejects_its_late_callback(action):
    script = TargetScript()
    variables = script.authorize(begin=action != "expire")
    script.authorize(12, host=3, state=102)
    variables["TOP_case_until"][12] = 300
    other = case_snapshot(script, 12)
    variables["TOP_selected"] = 11
    if action == "close":
        script.call("TOP_close_case", TARGET=11, SEQUENCE=999)
        assert variables["TOP_case_phase"][11] == 3
        script.call("TOP_close_case", TARGET=11, SEQUENCE=11)
    elif action == "revoke":
        script.run("TOP_revoke_authorization", 1)
    else:
        script.globals["TOP_clock"] = 100
        script.run("TOP_process_timers", 1)
    assert variables["TOP_case_phase"][11] == 0
    assert case_snapshot(script, 12) == other
    assert variables["TOP_active_cases"] == [12]
    fire_native_callback(script)
    assert script.globals["TOP_status"][11] == 1
    assert script.globals["TOP_status"][12] == 1
    assert variables["TOP_archive_cursor"] == 0
    assert case_snapshot(script, 12) == other


def test_cancelled_timed_case_cannot_complete_after_other_host_is_authorized():
    script = TargetScript()
    variables = script.authorize(method=3)
    script.authorize(12, method=4, host=3, state=102)
    assert variables["TOP_case_phase"][12] == 2
    variables["TOP_selected"] = 11
    script.run("TOP_revoke_authorization", 1)
    script.call("TOP_begin_person_operation", TARGET=12)
    script.globals["TOP_clock"] = 29
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][11] == 1
    assert script.globals["TOP_status"][12] == 2
    assert variables["TOP_attempts"][11] == 0
    assert variables["TOP_attempts"][12] == 1
    assert variables["TOP_archive_target"][0] == 12


def test_person_window_cannot_force_a_network_into_existence_before_its_window():
    script = TargetScript()
    script.run("TOP_open_windows_2006", 1)
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_status"][11] == 0
    script.run("TOP_open_windows_2009", 1)
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_status"][11] == 1


def test_native_stand_down_releases_capacity_without_retiring_the_prepared_tuple():
    script = TargetScript()
    variables = script.authorize(method=1)
    sequence = variables["TOP_case_sequence"][11]
    variables["TOP_selected"] = 11

    script.run("TOP_stand_down_selected", 1)

    assert variables["TOP_case_phase"][11] == 2
    assert variables["TOP_case_sequence"][11] == sequence
    assert variables["TOP_operation_subject_kind"] == 0
    assert variables["TOP_operation_subject_id"] == 0
    assert variables["TOP_operation_sequence"] == 0
    assert variables["TOP_case_native_prepared"][11] == 1
    assert variables.get("TOP_retired_native_bindings", []) == []

    script.call("TOP_begin_person_operation", TARGET=11)
    assert variables["TOP_case_phase"][11] == 3
    assert variables["TOP_case_sequence"][11] == sequence
    assert variables["TOP_case_native_prepared"][11] == 1
    fire_native_callback(script, tier=2)
    assert variables["TOP_case_native_prepared"][11] == 0
    assert script.globals["TOP_status"][11] == 3
    assert variables["TOP_archive_cursor"] == 1


def test_stood_down_native_callback_resolves_without_clearing_a_newer_slot():
    script = TargetScript()
    variables = script.authorize(method=1)
    variables["TOP_selected"] = 11
    script.run("TOP_stand_down_selected", 1)
    script.authorize(12, method=3, host=3, state=102)

    assert variables["TOP_operation_subject_id"] == 12
    assert variables["TOP_case_phase"][11] == 2
    fire_native_callback(script, target=11, method=1, tier=1, state=101)

    assert variables["TOP_case_native_prepared"][11] == 0
    assert variables["TOP_attempts"][11] == 1
    assert variables["TOP_archive_target"][0] == 11
    assert variables["TOP_operation_subject_kind"] == 1
    assert variables["TOP_operation_subject_id"] == 12
    assert variables["TOP_operation_sequence"] == 12


@pytest.mark.parametrize(
    "invalidation",
    ("expired", "inactive", "role", "access", "controller", "visit"),
)
def test_invalid_stood_down_native_callback_retires_without_resolving(invalidation):
    script = TargetScript()
    method = 2 if invalidation == "access" else 1
    variables = script.authorize(method=method)
    variables["TOP_selected"] = 11
    script.run("TOP_stand_down_selected", 1)

    if invalidation == "expired":
        script.globals["TOP_clock"] = variables["TOP_case_until"][11]
    elif invalidation == "inactive":
        script.globals["TOP_status"][11] = 2
    elif invalidation == "role":
        script.ineligible_roles.add(11)
    elif invalidation == "access":
        script.countries[1]["techs"].remove("special_forces_tech_1")
    elif invalidation == "controller":
        script.countries[101]["controller"] = 3
    else:
        capacity = int(script.globals["TOP_registry_capacity"])
        for field in (
            "TOP_visit_active_token",
            "TOP_visit_story",
            "TOP_visit_status",
            "TOP_visit_execution_until",
        ):
            script.globals.setdefault(field, ScriptArray([0] * capacity))
        variables["TOP_case_visit_status"][11] = 2
        variables["TOP_case_visit_token"][11] = 7
        variables["TOP_case_visit_story"][11] = 1
        script.globals["TOP_visit_active_token"][11] = 8
        script.globals["TOP_visit_story"][11] = 1
        script.globals["TOP_visit_status"][11] = 2
        script.globals["TOP_visit_execution_until"][11] = 100

    fire_native_callback(script, method=method)

    assert script.globals["TOP_status"][11] == (2 if invalidation == "inactive" else 1)
    assert variables["TOP_attempts"][11] == 0
    assert variables["TOP_case_phase"][11] == 0
    assert variables["TOP_case_native_prepared"][11] == 0
    assert len(variables["TOP_retired_native_bindings"]) == 1


def test_revoking_a_stood_down_native_case_retires_its_unresolved_tuple():
    script = TargetScript()
    variables = script.authorize(method=1)
    variables["TOP_selected"] = 11

    script.run("TOP_stand_down_selected", 1)
    script.run("TOP_revoke_authorization", 1)

    assert variables["TOP_case_phase"][11] == 0
    assert variables["TOP_case_native_prepared"][11] == 0
    assert len(variables["TOP_retired_native_bindings"]) == 1


def test_completed_native_callback_does_not_burn_a_reusable_tuple():
    script = TargetScript()
    variables = script.authorize(method=1)

    fire_native_callback(script, tier=1)
    assert script.globals["TOP_status"][11] == 1
    assert variables["TOP_case_native_prepared"][11] == 0
    assert variables.get("TOP_retired_native_bindings", []) == []

    sequence = variables["TOP_case_sequence"][11]
    script.call("TOP_close_case", TARGET=11, SEQUENCE=sequence)
    script.authorize(method=1)
    fire_native_callback(script, tier=1)

    assert variables["TOP_archive_cursor"] == 2
    assert variables.get("TOP_retired_native_bindings", []) == []


def test_training_disruption_is_frozen_as_a_native_success_probability_bonus():
    baseline = TargetScript()
    baseline_variables = baseline.authorize(method=1)
    assert baseline_variables["TOP_case_native_success_bonus"][11] == 0
    fire_native_callback(baseline, tier=1)
    assert baseline.globals["TOP_status"][11] == 1
    assert baseline_variables["TOP_archive_result"][0] == 8

    disrupted = TargetScript()
    group = int(disrupted.globals["TOP_affiliation"][11])
    disrupted.globals["TOP_group_disruption_type"][group] = 2
    disrupted.globals["TOP_group_disruption_until"][group] = 90
    disrupted_variables = disrupted.authorize(method=1)
    assert disrupted_variables["TOP_case_native_success_bonus"][11] == 10
    fire_native_callback(disrupted, tier=1)
    assert disrupted.globals["TOP_status"][11] == 1
    assert disrupted_variables["TOP_archive_result"][0] == 8


def test_custody_event_queue_preserves_two_same_day_captures():
    script = TargetScript()
    first = script.target(11)
    script.target(12)

    script.call("TOP_capture_target", TARGET=11)
    script.call("TOP_capture_target", TARGET=12)

    assert first["TOP_custody_event_open"] == 1
    assert first["TOP_custody_event_target"] == 11
    assert first["TOP_custody_event_queue"] == [12]

    script.run("TOP_finish_custody_event", 1)
    assert first["TOP_custody_event_open"] == 1
    assert first["TOP_custody_event_target"] == 12
    assert first["TOP_custody_event_queue"] == []

    script.run("TOP_finish_custody_event", 1)
    assert first["TOP_custody_event_open"] == 0
    assert first["TOP_custody_event_target"] == 0


def test_capture_initializes_exploitation_and_archive_before_custody_dispatch():
    resolution = _named_block(
        (ROOT / "common/scripted_effects/00_targeted_operations_effects.txt").read_text(
            encoding="utf-8"
        ),
        "TOP_resolve_target",
    )

    assert resolution.index(
        "global.TOP_exploitation_until^TOP_target"
    ) < resolution.index("TOP_archive_result = yes")
    assert resolution.index("TOP_archive_result = yes") < resolution.index(
        "TOP_queue_custody_event = yes"
    )


def test_bda_notice_queue_preserves_assessment_and_sequence_snapshots():
    script = TargetScript()
    variables = script.countries[1]["vars"]

    _seed_bda_archive(variables, ((11, 0, 41), (12, 1, 42)))

    script.call("TOP_queue_bda_notice", TARGET=11, ASSESSMENT=3, SEQUENCE=41)
    script.call("TOP_queue_bda_notice", TARGET=12, ASSESSMENT=6, SEQUENCE=42)

    assert variables["TOP_bda_notice_open"] == 1
    assert variables["TOP_bda_notice_target"] == 11
    assert variables["TOP_bda_notice_assessment"] == 3
    assert variables["TOP_bda_notice_sequence"] == 41
    assert variables["TOP_bda_notice_targets"] == [12]
    assert variables["TOP_bda_notice_assessments"] == [6]
    assert variables["TOP_bda_notice_sequences"] == [42]
    assert variables["TOP_bda_notice_rows"] == [1]

    script.run("TOP_finish_bda_notice", 1)
    assert variables["TOP_bda_notice_target"] == 12
    assert variables["TOP_bda_notice_assessment"] == 6
    assert variables["TOP_bda_notice_sequence"] == 42


def test_bda_dispatch_discards_a_stale_head_before_opening_the_next_notice():
    script = TargetScript()
    variables = script.countries[1]["vars"]
    variables["TOP_bda_notice_open"] = 1
    entries = ((11, 0, 41), (12, 1, 42))
    _seed_bda_archive(variables, entries)
    for target, _, token in entries:
        script.call("TOP_queue_bda_notice", TARGET=target, ASSESSMENT=3, SEQUENCE=token)

    variables["TOP_archive_bda_token"][0] = 99
    variables["TOP_bda_notice_open"] = 0
    script.run("TOP_dispatch_next_bda_notice", 1)

    assert variables["TOP_bda_notice_open"] == 1
    assert variables["TOP_bda_notice_target"] == 12
    assert variables["TOP_bda_notice_sequence"] == 42
    assert variables["TOP_bda_notice_targets"] == []
    assert variables["TOP_bda_notice_rows"] == []


def test_stood_down_callback_cannot_overwrite_an_open_field_report():
    script = TargetScript()
    variables = script.authorize(target=11, method=1, host=2, state=101)
    variables["TOP_selected"] = 11
    script.run("TOP_stand_down_selected", 1)
    script.authorize(target=12, method=3, host=3, state=102)
    script.temps.update(TOP_target=12, TOP_method=3, TOP_tier=2)
    script.run("TOP_complete_operation", 1)

    assert variables["TOP_report_open"] == 1
    assert variables["TOP_report_subject_kind"] == 1
    assert variables["TOP_report_subject_id"] == 12
    assert variables["TOP_report_state"] == 102
    assert variables["TOP_report_host"] == 3

    fire_native_callback(script, target=11, method=1, tier=1, state=101)

    assert variables["TOP_report_subject_id"] == 12
    assert variables["TOP_report_subject_ids"] == [11]
    assert variables["TOP_report_states"] == [101]
    assert variables["TOP_report_hosts"] == [2]

    script.run("TOP_finish_field_report", 1)
    assert variables["TOP_report_open"] == 1
    assert variables["TOP_report_subject_id"] == 11
    assert variables["TOP_report_state"] == 101
    assert variables["TOP_report_host"] == 2
    assert variables["TOP_report_subject_ids"] == []


def test_custody_archive_tracks_transfer_release_and_contextual_exchange():
    script = TargetScript()
    variables = script.target(11)
    script.call("TOP_capture_target", TARGET=11)
    assert variables["TOP_archive_disposition"][0] == 1
    assert variables["TOP_archive_custodian"][0] == 1

    variables["TOP_transfer_country"] = 2
    script.run("TOP_transfer_selected", 1)
    assert variables["TOP_archive_disposition"][0] == 3
    assert variables["TOP_archive_custodian"][0] == 2

    recipient = script.countries[2]["vars"]
    assert recipient["TOP_custody_event_open"] == 1
    assert recipient["TOP_custody_event_target"] == 11
    recipient["TOP_selected_kind"] = 1
    recipient["TOP_selected"] = 11
    script.run("TOP_release_selected", 2)
    assert variables["TOP_archive_disposition"][0] == 5
    assert variables["TOP_archive_custodian"][0] == 2

    script.target(12)
    script.call("TOP_capture_target", TARGET=12)
    variables["TOP_selected"] = 12
    assert not script.condition(script.triggers["TOP_can_exchange_selected"], 1)
    script.call("TOP_offer_exchange", TARGET=12, COUNTRY=2)
    assert script.condition(script.triggers["TOP_can_exchange_selected"], 1)
    script.run("TOP_exchange_selected", 1)
    assert script.globals["TOP_status"][12] == 1
    assert variables["TOP_archive_disposition"][1] == 4
    assert variables["TOP_archive_custodian"][1] == 1


def test_ai_custodian_can_accept_an_exchange_without_changing_its_selection():
    script = TargetScript()
    variables = script.target(12)
    script.countries[1]["ai"] = True
    variables["TOP_selected_kind"] = 2
    variables["TOP_selected"] = 0
    variables["TOP_selected_organization"] = 17
    script.call("TOP_capture_target", TARGET=12)

    script.call("TOP_offer_exchange", TARGET=12, COUNTRY=2)

    assert script.globals["TOP_status"][12] == 1
    assert script.globals["TOP_custodian"][12] == 0
    assert variables["TOP_archive_disposition"][0] == 4
    assert variables["TOP_archive_custodian"][0] == 1
    assert variables["TOP_exchange_country"][12] == 0
    assert variables["TOP_exchange_until"][12] == 0
    assert variables["TOP_selected_kind"] == 2
    assert variables["TOP_selected"] == 0
    assert variables["TOP_selected_organization"] == 17


def test_repeated_custody_episodes_update_only_their_own_archive_rows():
    script = TargetScript()
    variables = script.target(11)

    script.call("TOP_capture_target", TARGET=11)
    first_token = variables["TOP_archive_custody_token"][0]
    script.run("TOP_release_selected", 1)
    assert variables["TOP_archive_disposition"][0] == 5

    script.call("TOP_capture_target", TARGET=11)
    second_token = variables["TOP_archive_custody_token"][1]
    assert second_token > first_token
    script.run("TOP_prosecute_selected", 1)

    assert variables["TOP_archive_disposition"][0] == 5
    assert variables["TOP_archive_custodian"][0] == 1
    assert variables["TOP_archive_disposition"][1] == 2
    assert variables["TOP_archive_custodian"][1] == 1
