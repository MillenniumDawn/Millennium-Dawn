from great_ai_race_state_model_test import RaceScript


class TargetedScript(RaceScript):
    """Share engine dispatch while keeping each suite's modeled interfaces explicit."""

    country_trigger_fields = {}

    def value(self, name, identifier):
        if name == "THIS":
            return identifier
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
        if key in self.country_trigger_fields:
            actual = self.countries[identifier][self.country_trigger_fields[key]]
            return self.comparisons[comparison](actual, self.value(operand, identifier))
        if key in {"any_of", "all_of"}:
            fields = {name: value for name, _, value in operand}
            body = [entry for entry in operand if entry[0] not in {"array", "value"}]
            outcomes = []
            for member in self.value(fields["array"], identifier) or []:
                self.temps[fields.get("value", "v")] = member
                outcomes.append(self.condition(body, identifier))
            return any(outcomes) if key == "any_of" else all(outcomes)
        return super().condition([statement], identifier)

    def execute(self, statements, identifier):
        for statement in self._active_statements(statements, identifier):
            self.execute_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        if statement[0] in {"if", "else_if", "else", "hidden_effect"}:
            self.execute(statement[2], identifier)
        else:
            super().execute([statement], identifier)
