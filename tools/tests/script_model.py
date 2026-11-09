"""Execute HOI4 scripted effects and triggers for source-level model tests."""

import operator
import re
from datetime import date


def _extract_block(text: str, start: int) -> str:
    opening = text.index("{", start)
    depth = 0
    in_comment = False
    in_string = False
    escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == "#":
            in_comment = True
        elif character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError("Unclosed scripted block")


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^[ \t]*{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing block {name}"
    return _extract_block(text, match.start())


def _parse_race_script(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}=<>]|[^\s{}=<>]+', text)
    tokens = [token for token in tokens if not token.startswith("#")]
    cursor = 0

    def block():
        nonlocal cursor
        result = []
        while cursor < len(tokens) and tokens[cursor] != "}":
            if cursor + 1 >= len(tokens) or tokens[cursor + 1] not in {"=", "<", ">"}:
                result.append(tokens[cursor])
                cursor += 1
                continue
            key, comparison, value = tokens[cursor : cursor + 3]
            cursor += 3
            if value == "{":
                value = block()
                assert (
                    cursor < len(tokens) and tokens[cursor] == "}"
                ), "Unclosed scripted block"
                cursor += 1
            result.append((key, comparison, value))
        return result

    return {key: value for key, _comparison, value in block()}


def _substitute_script_parameters(statements, arguments):
    def substitute(value):
        if isinstance(value, list):
            return [
                (substitute(key), op, substitute(operand)) for key, op, operand in value
            ]
        return re.sub(r"\$([A-Za-z0-9_]+)\$", lambda match: arguments[match[1]], value)

    return substitute(statements)


class ScriptModel:
    """Model HOI4 script semantics; subclasses load source and stub owner systems."""

    globals: dict
    countries: dict
    scope_stack: list
    temps: dict
    mode: str
    global_flags: dict
    triggers: dict
    charges: list
    effects: dict
    events: list
    unlocked_categories: set

    durations = (0, 36, 60, 12, 0)
    costs = (0, 50, 150, 400, 1000)
    criteria = ("civs", "network", "power", "microchips", "composites", "oil")
    comparisons = {
        "=": operator.eq,
        ">": operator.gt,
        "<": operator.lt,
        "equals": operator.eq,
        "greater_than": operator.gt,
        "less_than": operator.lt,
        "greater_than_or_equals": operator.ge,
        "less_than_or_equals": operator.le,
        "not_equals": operator.ne,
    }

    def fire_event(self, event_id, identifier):
        self.events.append((identifier, event_id))

    def goto(self, year, month, day=1):
        self.today = date(year, month, day)
        self.globals.update(
            year=year, month=month, num_days=(self.today - date(2000, 1, 1)).days
        )

    def country(self, identifier, *, ai=False, tag="CAN", capability=50):
        country = {
            "vars": {
                "treasury": 100000,
                "gdp_total": 1000,
                "display_expense": 2,
                "treasury_rate": 10,
            },
            "flags": {},
            "techs": {"artificial_intelligence_7", "artificial_intelligence_8"},
            "exists": True,
            "ai": ai,
            "tag": tag,
            "capability": capability,
            "ratios": [1] * 6,
            "ledger": [],
            "missions": set(),
        }
        self.countries[identifier] = country
        self.globals.setdefault("countries", []).append(identifier)
        return country

    def _scope(self, name, identifier):
        if name.startswith("global."):
            return self.globals, name[7:]
        if name.startswith("PREV."):
            return self._scope(name[5:], self.scope_stack[-1])
        return self.countries[identifier]["vars"], name

    def value(self, name, identifier):
        if isinstance(name, list):
            result = 0
            matched = False
            for index, (key, _op, operand) in enumerate(name):
                if key == "value" and index:
                    raise AssertionError("value is only the base of a math expression")
                if key in {"if", "else"}:
                    if key == "if":
                        matched = False
                    limit = next(
                        (value for field, _, value in operand if field == "limit"), []
                    )
                    if not matched and (key == "else" or self.value(limit, identifier)):
                        matched = True
                        result = self.value(
                            [("value", "=", str(result))]
                            + [entry for entry in operand if entry[0] != "limit"],
                            identifier,
                        )
                    continue
                if key == "clamp":
                    limits = {key: value for key, _op, value in operand}
                    if "min" in limits:
                        result = max(result, self.value(limits["min"], identifier))
                    if "max" in limits:
                        result = min(result, self.value(limits["max"], identifier))
                    continue
                number = self.value(operand, identifier)
                if key == "value":
                    result = number
                elif key == "add":
                    result += number
                elif key == "subtract":
                    result -= number
                elif key == "multiply":
                    result *= number
                elif key == "divide":
                    result /= number
                elif key == "min":
                    result = min(result, number)
                elif key == "max":
                    result = max(result, number)
                elif key in self.comparisons:
                    result = int(self.comparisons[key](result, number))
                else:
                    raise AssertionError(f"Unsupported expression {key}")
            return result
        if name == "THIS.id":
            return identifier
        if name.startswith("token:"):
            return name.removeprefix("token:")
        try:
            return float(name)
        except ValueError:
            pass
        if name.endswith("^num"):
            return len(self.value(name[:-4], identifier))
        if name in self.temps:
            return self.temps[name]
        scope, key = self._scope(name, identifier)
        return scope.get(
            key,
            (
                []
                if key
                in {
                    "countries",
                    "ai_race_all_initialized",
                    "ai_race_participants",
                    "ai_race_ai_countries",
                }
                else 0
            ),
        )

    def _flag(self, flags, name):
        return name in flags and (
            flags[name] is None or flags[name] > self.globals["num_days"]
        )

    def _active_statements(self, statements, identifier):
        """Resolve branches lazily so preceding effects can change later limits."""
        matched = False
        for key, comparison, operand in statements:
            if key not in {"if", "else_if", "else"}:
                yield key, comparison, operand
                continue
            if key == "if":
                matched = False
            data = {name: value for name, _op, value in operand}
            if not matched and (
                key == "else" or self.condition(data["limit"], identifier)
            ):
                matched = True
                yield key, comparison, [
                    entry for entry in operand if entry[0] != "limit"
                ]

    def condition(self, statements, identifier):
        country = self.countries[identifier]
        outcomes = []
        for key, comparison, operand in self._active_statements(statements, identifier):
            if key in {"if", "else_if", "else"}:
                result = self.condition(operand, identifier)
            elif key in {"AND", "OR", "NOT"}:
                values = [self.condition([entry], identifier) for entry in operand]
                result = any(values) if key == "OR" else all(values)
                if key == "NOT":
                    result = not result
            elif key == "check_variable":
                data = {key: value for key, _op, value in operand}
                if "var" in data:
                    left, right, comparison = (
                        data["var"],
                        data["value"],
                        data.get("compare", "equals"),
                    )
                else:
                    left, comparison, right = operand[0]
                assert not isinstance(
                    right, list
                ), "check_variable needs a scalar value"
                result = self.comparisons[comparison](
                    self.value(left, identifier), self.value(right, identifier)
                )
            elif key == "has_game_rule":
                data = {key: value for key, _op, value in operand}
                result = self.mode == data["option"]
            elif key == "date":
                result = self.comparisons[comparison](
                    self.today, date(*map(int, operand.split(".")))
                )
            elif key == "has_country_flag":
                result = self._flag(country["flags"], operand)
            elif key == "has_global_flag":
                result = self._flag(self.global_flags, operand)
            elif key == "has_variable":
                scope, name = self._scope(operand, identifier)
                result = name in scope
            elif key == "is_in_array":
                name, _op, value = operand[0]
                member = (
                    identifier if value == "THIS" else self.value(value, identifier)
                )
                result = member in (self.value(name, identifier) or [])
            elif key == "has_tech":
                result = operand in country["techs"]
            elif key == "can_research":
                result = (
                    operand in country.get("researchable", set())
                    and operand not in country["techs"]
                )
            elif key == "has_active_mission":
                result = operand in country["missions"]
            elif key == "exists":
                result = country["exists"] == (operand == "yes")
            elif key == "is_ai":
                result = country["ai"] == (operand == "yes")
            elif key == "has_war":
                result = country.get("war", False) == (operand == "yes")
            elif key in {"tag", "original_tag"}:
                result = country["tag"] == operand
            elif key == "has_idea":
                result = operand in country.get("ideas", set())
            elif key == "has_dynamic_modifier":
                data = {key: value for key, _op, value in operand}
                result = data["modifier"] in country.get("dynamic_modifiers", set())
            elif key == "always":
                result = operand == "yes"
            elif key in {
                "amount_research_slots",
                "num_of_available_civilian_factories",
            }:
                result = self.comparisons[comparison](
                    self.value(key, identifier), self.value(operand, identifier)
                )
            elif key == "any_controlled_state":
                assert operand == [("always", "=", "yes")]
                result = bool(country.get("states", []))
            elif key == "free_building_slots":
                data = {key: value for key, _op, value in operand}
                assert data["building"] != "nuclear_facility" or "province" in data
                size = next(entry for entry in operand if entry[0] == "size")
                result = self.comparisons[size[1]](
                    country["free_slots"].get(data["building"], 0),
                    self.value(size[2], identifier),
                )
            elif key == "can_construct_building":
                assert identifier < 0, "Construction availability requires state scope"
                result = getattr(self, "root", None) == country[
                    "country_id"
                ] and country["constructible_buildings"].get(operand, False)
            elif key == "is_special_project_completed":
                result = operand in country.get("projects", set())
            elif key == "is_debug":
                result = operand == "yes"
            elif key in self.triggers:
                if isinstance(operand, list):
                    arguments = {key: value for key, _op, value in operand}
                    result = self.condition(
                        _substitute_script_parameters(self.triggers[key], arguments),
                        identifier,
                    )
                else:
                    result = self.condition(self.triggers[key], identifier) == (
                        operand == "yes"
                    )
            else:
                raise AssertionError(f"Unsupported trigger {key}")
            outcomes.append(result)
        return all(outcomes)

    def run(self, name, identifier):
        country, variables = (
            self.countries[identifier],
            self.countries[identifier]["vars"],
        )
        if name in {
            "ai_race_ai_discover_candidates",
            "ai_race_ai_refresh_plans",
            "ai_race_ai_clear_all_plans",
        }:
            return
        elif name == "ai_race_refresh_operating_state":
            stage = int(variables.get("ai_race_stage", 0))
            variables.update(
                ai_race_current_required_months=self.durations[stage],
                ai_race_current_readiness=min(country["ratios"]),
            )
            variables.setdefault("ai_race_capacity_settled", 1)
            leader = (
                stage == 4
                and self.globals.get("ai_race_first_finisher_id") == identifier
            )
            variables["ai_race_bonus"] = (
                (stage + int(leader)) * 0.01 * min(country["ratios"])
                if self.mode == "full"
                else 0
            )
            variables["ai_race_demand_power"] = (
                (0, 2, 8, 25, 60)[stage] if self.mode == "full" else 0
            )
        elif name == "ai_race_refresh_offer":
            stage = int(variables.get("ai_race_stage", 0))
            offered = stage + 1 if stage < 4 else 0
            readiness = min(country["ratios"])
            rate = 0.45 + 0.4 * (1 - readiness)
            principal = variables["gdp_total"] * rate
            for key, value in {
                "stage": offered,
                "cost": self.costs[offered],
                "readiness": readiness,
                "principal": principal,
                "payment": principal / 520,
                "rate": rate,
                "required_months": self.durations[stage],
            }.items():
                variables[f"ai_race_offer_{key}"] = value
            for key, ratio in zip(self.criteria, country["ratios"]):
                for field, value in {
                    "ratio": ratio,
                    "required": 100,
                    "available": ratio * 100,
                }.items():
                    variables[f"ai_race_offer_{key}_{field}"] = value
        elif name == "ai_race_rebuild_country_metrics":
            variables["ai_race_capability_external"] = max(
                0, country["capability"] - variables.get("ai_race_capability_stock", 0)
            )
            variables["ai_race_capability"] = country["capability"]
        elif name == "ai_race_create_financing":
            country["ledger"].append(
                (
                    variables["ai_race_stage"],
                    variables["ai_race_offer_principal"],
                    variables["ai_race_offer_payment"],
                    520,
                )
            )
        elif name == "ai_race_clear_finance_state":
            country["ledger"].clear()
        elif name == "ai_race_clear_capacity_state":
            for key in list(variables):
                if key.startswith(
                    (
                        "ai_race_current_",
                        "ai_race_offer_",
                        "ai_race_capacity_",
                        "ai_race_demand_",
                        "ai_race_bonus",
                    )
                ):
                    variables.pop(key)
        elif name == "modify_treasury_effect":
            assert not self._flag(country["flags"], "MD_skip_treasury_cost")
            amount = self.value("treasury_change", identifier)
            variables["treasury"] += amount
            self.charges.append((identifier, amount))
        else:
            self.execute(self.effects[name], identifier)

    def execute(self, statements, identifier):
        for key, _comparison, operand in self._active_statements(
            statements, identifier
        ):
            if key in {"if", "else_if", "else"}:
                self.execute(operand, identifier)
            elif key.startswith("var:"):
                self.scope_stack.append(identifier)
                try:
                    self.execute(operand, self.value(key[4:], identifier))
                finally:
                    self.scope_stack.pop()
            elif key == "for_each_scope_loop":
                data = {key: value for key, _op, value in operand}
                for member in list(self.value(data["array"], identifier) or []):
                    self.scope_stack.append(identifier)
                    try:
                        self.execute(
                            [entry for entry in operand if entry[0] != "array"], member
                        )
                    finally:
                        self.scope_stack.pop()
            elif key == "for_each_loop":
                data = {key: value for key, _op, value in operand}
                for member in list(self.value(data["array"], identifier) or []):
                    self.temps[data["value"]] = member
                    self.execute(
                        [
                            entry
                            for entry in operand
                            if entry[0] not in {"array", "value"}
                        ],
                        identifier,
                    )
            elif key == "while_loop_effect":
                data = {key: value for key, _op, value in operand}
                count = 0
                while self.condition(data["limit"], identifier):
                    count += 1
                    assert count <= 1000, "Race loop did not terminate"
                    self.execute(
                        [entry for entry in operand if entry[0] != "limit"], identifier
                    )
            elif key in {"clear_variable", "clear_array"}:
                scope, name = self._scope(operand, identifier)
                if key == "clear_array":
                    scope[name] = []
                else:
                    scope.pop(name, None)
            elif key in {
                "set_variable",
                "set_temp_variable",
                "add_to_variable",
                "add_to_temp_variable",
                "subtract_from_variable",
                "subtract_from_temp_variable",
                "multiply_variable",
                "multiply_temp_variable",
                "divide_variable",
                "divide_temp_variable",
            }:
                name, _op, raw = operand[0]
                value = self.value(raw, identifier)
                scope, name = (
                    (self.temps, name)
                    if "temp_variable" in key
                    else self._scope(name, identifier)
                )
                previous = scope.get(name, 0)
                if key.startswith("add_to"):
                    value += previous
                elif key.startswith("subtract_from"):
                    value = previous - value
                elif key.startswith("multiply"):
                    value *= previous
                elif key.startswith("divide"):
                    value = previous / value
                scope[name] = value
            elif key in {"clamp_variable", "clamp_temp_variable"}:
                data = {key: value for key, _op, value in operand}
                scope, name = (
                    (self.temps, data["var"])
                    if key == "clamp_temp_variable"
                    else self._scope(data["var"], identifier)
                )
                # HOI4 logs "Unknow variable" for clamp_variable on an unset variable.
                if key == "clamp_variable":
                    exists = (
                        name < len(scope) if isinstance(scope, list) else name in scope
                    )
                    assert exists, f"clamp_variable on unset {data['var']}"
                value = self.value(data["var"], identifier)
                if "min" in data:
                    value = max(value, self.value(data["min"], identifier))
                if "max" in data:
                    value = min(value, self.value(data["max"], identifier))
                scope[name] = value
            elif key in {"add_to_array", "remove_from_array"}:
                name, _op, raw = operand[0]
                scope, name = self._scope(name, identifier)
                member = identifier if raw == "THIS" else self.value(raw, identifier)
                if key == "add_to_array":
                    scope.setdefault(name, []).append(member)
                elif member in scope.get(name, []):
                    scope[name].remove(member)
            elif key in {
                "set_country_flag",
                "set_global_flag",
                "clr_country_flag",
                "clr_global_flag",
            }:
                flags = (
                    self.global_flags
                    if "global_flag" in key
                    else self.countries[identifier]["flags"]
                )
                if key.startswith("clr"):
                    flags.pop(operand, None)
                else:
                    data = (
                        {key: value for key, _op, value in operand}
                        if isinstance(operand, list)
                        else {"flag": operand, "value": "1"}
                    )
                    # This harness models shorthand presence checks, which reject zero.
                    if float(data.get("value", 0)) == 0:
                        flags.pop(data["flag"], None)
                        continue
                    flags[data["flag"]] = (
                        self.globals["num_days"] + float(data["days"])
                        if "days" in data
                        else None
                    )
            elif key in {"country_event", "news_event"}:
                event_id = (
                    dict((name, value) for name, _op, value in operand)["id"]
                    if isinstance(operand, list)
                    else operand
                )
                self.fire_event(event_id, identifier)
            elif key == "remove_dynamic_modifier":
                data = {key: value for key, _op, value in operand}
                self.countries[identifier].setdefault(
                    "dynamic_modifiers", set()
                ).discard(data["modifier"])
            elif key == "unlock_decision_category_tooltip":
                self.unlocked_categories.append((identifier, operand))
            elif key == "log":
                continue
            elif key == "meta_effect":
                data = {key: value for key, _op, value in operand}
                arguments = {}
                for argument, expression in data.items():
                    if argument == "text":
                        continue
                    match = re.fullmatch(r'"\[\?(\w+)\.GetTokenKey\]"', expression)
                    assert match, f"Unsupported meta expression {expression}"
                    arguments[argument] = self.value(match[1], identifier)

                def substitute(value):
                    if isinstance(value, list):
                        return [
                            (substitute(key), op, substitute(raw))
                            for key, op, raw in value
                        ]
                    return re.sub(
                        r"\[([A-Za-z0-9_]+)\]",
                        lambda match: arguments[match[1]],
                        value,
                    )

                self.execute(substitute(data["text"]), identifier)
            elif key in self.effects and isinstance(operand, list):
                arguments = {key: value for key, _op, value in operand}
                self.execute(
                    _substitute_script_parameters(self.effects[key], arguments),
                    identifier,
                )
            elif key in self.effects or key in {
                "ai_race_ai_discover_candidates",
                "ai_race_ai_refresh_plans",
                "ai_race_ai_clear_all_plans",
                "ai_race_refresh_operating_state",
                "ai_race_refresh_offer",
                "ai_race_create_financing",
                "ai_race_clear_capacity_state",
                "ai_race_clear_finance_state",
                "modify_treasury_effect",
            }:
                self.run(key, identifier)
            else:
                raise AssertionError(f"Unsupported effect {key}")


class ScriptArray(list):
    def get(self, index, default=0):
        return self[index] if 0 <= index < len(self) else default


class TempScriptModel(ScriptModel):
    """Read temps through PREV and ROOT and evaluate every collection trigger."""

    country_trigger_fields = {}
    temp_effects = {
        "set_temp_variable",
        "add_to_temp_variable",
        "subtract_from_temp_variable",
        "multiply_temp_variable",
        "divide_temp_variable",
    }

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
        if key in self.temp_effects or key == "clamp_temp_variable":
            self.execute_statement(statement, identifier)
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
        if key in self.temp_effects:
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
        else:
            super().execute([statement], identifier)


class ScopedScriptModel(TempScriptModel):
    """Add country and state scopes, indexed arrays and stubbed effects."""

    stubs = frozenset()
    country_fields = {
        "num_of_controlled_states",
        "has_political_power",
        "arms_factory",
        "industrial_complex",
        "infrastructure",
    }

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
        if key in self.country_fields:
            value = (
                len(self.countries[identifier]["states"])
                if key == "num_of_controlled_states"
                else self.countries[identifier]["vars"].get(
                    "political_power" if key == "has_political_power" else key, 0
                )
            )
            return self.comparisons[comparison](value, self.value(operand, identifier))
        return super().condition_statement(statement, identifier)

    def run(self, name, identifier):
        if name in self.stubs:
            self.external[name, identifier] += 1
        else:
            self.execute(self.effects[name], identifier)

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key in self.stubs:
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
            super().execute_statement(statement, identifier)
