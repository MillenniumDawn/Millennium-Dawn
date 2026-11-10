"""Shared HOI4 script execution model for STALKER source tests."""

from collections import Counter

from ai_race_state_model_test import RaceScript


class ScriptArray(list):
    def get(self, index, default=0):
        return self[index] if 0 <= index < len(self) else default


class StalkerModel(RaceScript):
    """Execute STALKER source with scope, temp and stubbed-effect support."""

    def __init__(self, tags=("---", "USA", "YEM", "PER", "TAL", "AFG", "CHI")):
        self.effects, self.triggers = {}, {}
        self.countries, self.globals, self.temps = {}, {}, {}
        self.scope_stack, self.events = [], []
        self.global_flags, self.external = {}, Counter()
        self.stubs = set()
        self.goto(2005, 1)
        for ident, tag in enumerate(tags):
            self.country(ident, tag=tag)
            self.countries[ident].update(states=[], exists=ident != 0)

    @staticmethod
    def _unqualified_temp_name(name):
        while isinstance(name, str) and (
            name.startswith("PREV.") or name.startswith("ROOT.")
        ):
            name = name.split(".", 1)[1]
        return name

    def state(self, ident, controller):
        self.country(ident, tag=f"state_{ident}")
        self.countries[ident].update(controller=controller, states=[])
        self.countries[ident]["vars"].update(
            infrastructure=3, arms_factory=2, industrial_complex=2
        )
        self.countries[controller]["states"].append(ident)

    def tag(self, token):
        return next(
            (ident for ident, data in self.countries.items() if data["tag"] == token),
            None,
        )

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
            temp_name = self._unqualified_temp_name(name)
            if temp_name != name and temp_name in self.temps:
                return self.temps[temp_name]
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
        if key in {
            "set_temp_variable",
            "add_to_temp_variable",
            "subtract_from_temp_variable",
            "multiply_temp_variable",
            "divide_temp_variable",
            "clamp_temp_variable",
        }:
            self.execute_statement(statement, identifier)
            return True
        if key == "country_exists":
            return self.condition_statement(
                (operand, "=", [("exists", "=", "yes")]), identifier
            )
        if key.isdigit():
            return self.scoped(operand, identifier, int(key), condition=True)
        if key.startswith("var:") or key == "controller" or self.tag(key) is not None:
            return self.scoped(
                operand, identifier, self.value(key, identifier), condition=True
            )
        if key == "has_state_flag":
            return self._flag(self.countries[identifier]["flags"], operand)
        if key == "is_controlled_by":
            return self.value("controller", identifier) == self.value(
                operand, identifier
            )
        if key in {
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
            return self.comparisons[comparison](value, self.value(operand, identifier))
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

    def run(self, name, identifier):
        if name in self.stubs:
            self.external[name, identifier] += 1
        else:
            self.execute(self.effects[name], identifier)

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
            self.execute(operand, identifier)
        elif key in self.stubs:
            self.run(key, identifier)
        elif key.isdigit():
            self.scoped(operand, identifier, int(key))
        elif key == "controller" or self.tag(key) is not None:
            self.scoped(operand, identifier, self.value(key, identifier))
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
        elif key in {"add_opinion_modifier", "add_dynamic_modifier", "damage_building"}:
            self.external[key, identifier] += 1
        else:
            super().execute([statement], identifier)
