"""Targeted Operations test helpers built on the shared script model."""

import json
import shutil
from pathlib import Path

import pytest
from script_model import (
    ScriptModel,
)
from script_model import (
    _extract_block as _extract_block,
)
from script_model import (
    _named_block as _named_block,
)
from script_model import (
    _parse_race_script as _parse_race_script,
)
from script_model import (
    _substitute_script_parameters as _substitute_script_parameters,
)


class TargetedScript(ScriptModel):
    """Share engine dispatch while keeping each suite's modeled interfaces explicit."""

    country_trigger_fields = {}

    @staticmethod
    def _unqualified_temp_name(name):
        while isinstance(name, str) and (
            name.startswith("PREV.") or name.startswith("ROOT.")
        ):
            name = name.split(".", 1)[1]
        return name

    def value(self, name, identifier):
        if name == "THIS":
            return identifier
        temp_name = self._unqualified_temp_name(name)
        if temp_name != name and temp_name in self.temps:
            return self.temps[temp_name]
        return super().value(name, identifier)

    def condition(self, statements, identifier):
        # Collection triggers write temporary values, so evaluate every statement.
        outcomes = [
            self.condition_statement(statement, identifier)
            for statement in self._active_statements(statements, identifier)
        ]
        return all(outcomes)

    def condition_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key in {"if", "else_if", "else"}:
            return self.condition(operand, identifier)
        if key == "set_temp_variable":
            self.execute([statement], identifier)
            return True
        if key == "country_exists":
            return self.condition_statement(
                (operand, "=", [("exists", "=", "yes")]), identifier
            )
        if key == "is_capital":
            country = self.countries[identifier]
            controller = self.countries.get(country.get("controller"), {})
            states = controller.get("states", [])
            capital = (
                bool(states and states[0] == identifier)
                if isinstance(states, list)
                else country.get("capital", False)
            )
            return capital == (operand == "yes")
        if key.startswith("event_target:"):
            target = getattr(self, "event_targets", {}).get(key.split(":", 1)[1])
            if target is None:
                return False
            self.scope_stack.append(identifier)
            try:
                return self.condition(operand, target)
            finally:
                self.scope_stack.pop()
        if key in self.country_trigger_fields:
            actual = self.countries[identifier][self.country_trigger_fields[key]]
            return self.comparisons[comparison](actual, self.value(operand, identifier))
        if key in {"any_of", "all_of"}:
            fields = {name: value for name, _, value in operand}
            body = [
                entry
                for entry in operand
                if entry[0] not in {"array", "value", "index"}
            ]
            outcomes = []
            for index, member in enumerate(
                self.value(fields["array"], identifier) or []
            ):
                self.temps[fields.get("value", "v")] = member
                self.temps[fields.get("index", "index")] = index
                outcomes.append(self.condition(body, identifier))
            return any(outcomes) if key == "any_of" else all(outcomes)
        return super().condition([statement], identifier)

    def execute(self, statements, identifier):
        for statement in self._active_statements(statements, identifier):
            self.execute_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key in {
            "set_temp_variable",
            "add_to_temp_variable",
            "subtract_from_temp_variable",
            "multiply_temp_variable",
            "divide_temp_variable",
        }:
            name, operator, value = operand[0]
            normalized = self._unqualified_temp_name(name)
            super().execute(
                [(key, comparison, [(normalized, operator, value)])], identifier
            )
        elif key == "clamp_temp_variable":
            normalized = []
            for name, operator, value in operand:
                if name == "var":
                    value = self._unqualified_temp_name(value)
                normalized.append((name, operator, value))
            super().execute([(key, comparison, normalized)], identifier)
        elif key in {"if", "else_if", "else", "hidden_effect"}:
            self.execute(statement[2], identifier)
        else:
            super().execute([statement], identifier)


"""Shared manifest mutations for TOP generator contract checks."""


def mutate_manifest(data: dict, defect: str) -> None:
    if defect == "duplicate_id":
        data["targets"][1]["id"] = data["targets"][0]["id"]
    elif defect == "duplicate_key":
        data["targets"][1]["key"] = data["targets"][0]["key"]
    elif defect == "duplicate_group":
        data["groups"][1]["id"] = data["groups"][0]["id"]
    elif defect == "duplicate_ct_slot":
        data["groups"][1]["ct_id"] = data["groups"][0]["ct_id"]
    elif defect == "foreign_successor":
        data["targets"][0]["successors"].append(64)
    elif defect == "missing_successor":
        data["targets"][0]["successors"].append(999)
    elif defect == "foreign_group_successor":
        data["groups"][0]["succession"].append(64)
    elif defect == "generated_overlap":
        data["targets"][-1]["id"] = 65
    elif defect == "generated_end":
        data["generated_end"] = 130
    elif defect == "capacity":
        data["capacity"] += 1
    elif defect == "target_class":
        data["targets"][0]["target_class"] = "person"
    elif defect == "group_class":
        data["groups"][0]["group_class"] = "organization"
    elif defect == "location_policy":
        data["groups"][0]["location_policy"] = "random_state"
    elif defect == "unknown_source":
        data["targets"][0]["sources"].append("missing_source")
    elif defect == "stable_target_key":
        data["targets"][0]["key"], data["targets"][1]["key"] = (
            data["targets"][1]["key"],
            data["targets"][0]["key"],
        )
    elif defect == "stable_group_key":
        data["groups"][0]["key"], data["groups"][1]["key"] = (
            data["groups"][1]["key"],
            data["groups"][0]["key"],
        )
    elif defect == "negative_ct_slot":
        data["groups"][0]["ct_id"] = -1
    elif defect == "group_public_identity":
        data["groups"][0]["public_identity"] = True
    elif defect == "target_public_identity":
        data["targets"][0]["public_identity"] = True
    elif defect == "facility_default":
        data["facility_objective_defaults"]["state_security"] = ["command", "funding"]
    elif defect == "empty_facility_override":
        data["groups"][0]["facility_objectives"] = []
    elif defect == "unknown_facility_override":
        data["groups"][0]["facility_objectives"] = ["safehouse"]
    elif defect == "leader_role":
        data["targets"][0]["leader_role"] = "president"
    elif defect == "leader_office":
        leader = next(
            target for target in data["targets"] if target["leader_role"] != "none"
        )
        leader["role_eligibility"]["office_keys"] = []
    elif defect == "consequence_profile":
        data["targets"][0]["consequence_profile"] = "political_leader"
    elif defect == "duplicate_successor":
        data["targets"][0]["successors"].append(data["targets"][0]["successors"][0])
    elif defect == "incomplete_successor":
        data["targets"][0]["successors"].pop()
    elif defect == "missing_authored_pool":
        next(group for group in data["groups"] if group["id"] == 22)["succession"] = []
    elif defect == "activation_year":
        data["targets"][0]["activation_year"] = 1999
    elif defect == "missing_sources":
        data["targets"][0]["sources"] = []
    else:
        raise ValueError(f"Unknown manifest defect: {defect}")


def read_top_source(root, folder):
    """Read the system's definitions in engine load order, independent of file splits."""
    paths = sorted((root / folder).glob("*targeted_operations*.txt"))
    assert paths, f"No TOP source in {folder}"
    return "\n".join(path.read_text(encoding="utf-8-sig") for path in paths)


ROOT = Path(__file__).resolve().parents[2]

MANIFEST_DEFECT_ERRORS = {
    "duplicate_id": "Authored IDs must preserve slots 1-64",
    "duplicate_key": "Authored person keys must retain their stable IDs",
    "duplicate_group": "Organization identities must preserve slots 1-12",
    "duplicate_ct_slot": "Duplicate or out-of-range CT identity",
    "foreign_successor": "Incomplete successor binding for 1",
    "missing_successor": "Invalid affiliation or successor for 1",
    "foreign_group_successor": "Incomplete successor binding for 1",
    "generated_overlap": "Authored IDs must preserve slots 1-64",
    "generated_end": "Authored IDs must preserve slots 1-64",
    "capacity": "Authored IDs must preserve slots 1-64",
    "target_class": "Invalid target class for 1",
    "group_class": "Target class does not match group for 1",
    "location_policy": "Invalid location policy for 1",
    "unknown_source": "Unknown source for 1",
    "stable_target_key": "Authored person keys must retain their stable IDs",
    "stable_group_key": "Organization keys must retain their stable IDs",
    "negative_ct_slot": "Duplicate or out-of-range CT identity",
    "group_public_identity": "Public identity does not match class for group 1",
    "target_public_identity": "Public identity does not match target class for 1",
    "facility_default": "Invalid facility objective default for state_security",
    "empty_facility_override": "Facility objectives must be a nonempty set",
    "unknown_facility_override": "Facility objectives must be a nonempty set",
    "leader_role": "Invalid leader role for target 1",
    "leader_office": "Incomplete serving leader binding for 129",
    "consequence_profile": "Consequence profile does not match group for 1",
    "duplicate_successor": "Incomplete successor binding for 1",
    "incomplete_successor": "Incomplete successor binding for 1",
    "missing_authored_pool": "Authored successor missing from group pool: 145",
    "activation_year": "Invalid authored opportunity year for 1",
    "missing_sources": "Missing authoring provenance for 1",
}


LEADER_ROLES = {
    "head_of_state",
    "head_of_government",
    "senior_political",
    "state_security_official",
}


def write_manifest_root(root: Path, data: dict, stub_from: dict = None) -> Path:
    """Write a manifest beside the TOP sources that load_manifest cross-checks.

    With stub_from, write minimal serving and retirement bindings for that
    manifest's leaders instead of copying game content, for tool-only checkouts.
    """
    triggers = root / "common/scripted_triggers"
    effects = root / "common/scripted_effects"
    for target in (triggers, effects):
        target.mkdir(parents=True, exist_ok=True)
    if stub_from is None:
        for folder, target in (
            ("common/scripted_triggers", triggers),
            ("common/scripted_effects", effects),
        ):
            for path in (ROOT / folder).glob("*targeted_operations*.txt"):
                shutil.copyfile(path, target / path.name)
    else:
        leaders = [
            target["id"]
            for target in stub_from["targets"]
            if target["leader_role"] in LEADER_ROLES
        ]
        (triggers / "targeted_operations_stub.txt").write_text(
            "".join(f"TOP_person_{ident}_serving = {{\n}}\n" for ident in leaders),
            encoding="utf-8",
        )
        (effects / "targeted_operations_stub.txt").write_text(
            "".join(
                f"check_variable = {{ TOP_target = {ident} }}\n" for ident in leaders
            ),
            encoding="utf-8",
        )
    manifest_path = root / "tools/data/targeted_operations.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        json.dump(data, stream)
    return root


def read(relative: str) -> str:
    source_path = ROOT / relative
    if not source_path.exists() and not (ROOT / Path(relative).parts[0]).exists():
        pytest.skip("game content not checked out (sparse checkout)")
    return source_path.read_text(encoding="utf-8-sig")


def block(relative: str, name: str) -> str:
    return _named_block(read(relative), name)
