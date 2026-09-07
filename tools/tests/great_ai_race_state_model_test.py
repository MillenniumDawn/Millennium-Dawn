import copy
import operator
import re
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "00_great_ai_race_effects.txt"
PROGRESSION_PATH = (
    ROOT / "common" / "scripted_effects" / "03_great_ai_race_progression_effects.txt"
)
TRIGGERS_PATH = ROOT / "common" / "scripted_triggers" / "MD_great_ai_race_triggers.txt"
ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "MD_on_actions.txt"
GAME_RULES_PATH = ROOT / "common" / "game_rules" / "00_game_rules.txt"
DECISIONS_PATH = ROOT / "common" / "decisions" / "MD_great_ai_race_decisions.txt"
GAME_RULES_LOC_PATH = ROOT / "localisation" / "english" / "MD_game_rules_l_english.yml"
RACE_LOC_PATH = ROOT / "localisation" / "english" / "MD_great_ai_race_l_english.yml"

COUNTRY_CAPABILITIES = (
    "capability",
    "compute",
    "talent",
    "deployment",
    "control_capacity",
    "public_confidence",
)
COUNTRY_DERIVED_STATE = (
    "ai_race_public_alarm",
    "ai_race_control_debt",
    "ai_race_frontier_gap",
    "ai_race_rank",
)
GLOBAL_STATE = (
    "global.ai_race_frontier_capability",
    "global.ai_race_temperature",
    "global.ai_race_frontier_pressure",
    "global.ai_race_leader_id",
    "global.ai_race_epoch",
    "global.ai_race_last_processed_quarter",
    "global.ai_race_dirty_update_var",
)
UPSTREAM_PREFIXES = (
    "USA_ai_core_",
    "CHI_huawei_",
    "CHI_ic_inf_nsc",
    "energy_",
    "unfulfilled_energy_",
    "country_microchip_",
    "research_slots_",
)


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


def _variable_write_targets(text: str) -> set[str]:
    targets = set(
        re.findall(
            r"\b(?:set_variable|add_to_variable|subtract_from_variable)\s*=\s*"
            r"\{\s*([A-Za-z0-9_.]+)\s*=",
            text,
        )
    )
    targets.update(re.findall(r"\bclear_variable\s*=\s*([A-Za-z0-9_.]+)", text))
    targets.update(
        re.findall(
            r"\bclamp_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_.]+)",
            text,
        )
    )
    return targets


def test_race_is_the_sole_writer_of_its_persistent_state():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    writes = _variable_write_targets(effects)

    assert writes
    assert all(
        target.startswith("ai_race_") or target.startswith("global.ai_race_")
        for target in writes
    )
    assert not any(target.startswith(UPSTREAM_PREFIXES) for target in writes)

    country_flags = re.findall(
        r"\b(?:set_country_flag|clr_country_flag)\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)",
        effects,
    )
    global_flags = re.findall(
        r"\b(?:set_global_flag|clr_global_flag)\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)",
        effects,
    )
    arrays = re.findall(
        r"\b(?:add_to_array|clear_array)\s*=\s*(?:\{\s*)?([A-Za-z0-9_.]+)",
        effects,
    )

    assert country_flags and all(flag.startswith("AI_RACE_") for flag in country_flags)
    assert global_flags and all(
        flag.startswith("GLOBAL_ai_race_") for flag in global_flags
    )
    assert arrays and all(array.startswith("global.ai_race_") for array in arrays)


def test_first_enabled_pulse_publishes_without_advancing_scheduled_state():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    on_actions = ON_ACTIONS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "ai_race_initialize_global")
    rebuild = _named_block(effects, "ai_race_rebuild_derived_state")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    quarterly = _named_block(effects, "ai_race_quarterly_reconcile")

    assert initialize.index("set_global_flag = GLOBAL_ai_race_initialized") < (
        initialize.index("ai_race_rebuild_derived_state = yes")
    )
    assert dispatch.index("ai_race_initialize_global = yes") < dispatch.index(
        "check_variable = { global.month = 1 }"
    )
    assert "ai_race_rebuild_country_metrics = yes" in rebuild
    assert "ai_race_rebuild_frontier_and_ranking = yes" in rebuild
    assert "global.ai_race_epoch" not in rebuild
    assert "global.ai_race_last_processed_quarter" not in rebuild
    assert "global.ai_race_dirty_update_var" not in rebuild
    assert "ai_race_rebuild_derived_state = yes" in quarterly
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert on_actions.count("ai_race_monthly_dispatch = yes") == 1


def test_modes_cleanup_and_participant_reentry_have_live_routes():
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    rules = GAME_RULES_PATH.read_text(encoding="utf-8")
    on_actions = ON_ACTIONS_PATH.read_text(encoding="utf-8")

    full = _named_block(triggers, "ai_race_full_mode")
    outcomes = _named_block(triggers, "ai_race_outcomes_only_mode")
    enabled = _named_block(triggers, "ai_race_enabled")
    eligible = _named_block(triggers, "ai_race_eligible_participant")
    refresh = _named_block(effects, "ai_race_refresh_participants")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    teardown = _named_block(effects, "ai_race_teardown_global")
    rule = _named_block(rules, "rule_ai_race")

    assert "option = outcomes_only" in full
    assert "option = disabled" in full
    assert "option = outcomes_only" in outcomes
    assert "ai_race_full_mode = yes" in enabled
    assert "ai_race_outcomes_only_mode = yes" in enabled
    assert "NOT = { has_country_flag = collapsed_nation }" in eligible
    assert "original_tag" not in eligible
    assert "date > 2015.12.31" in eligible
    assert "has_tech = artificial_intelligence_7" in eligible
    assert "array = global.ai_race_all_initialized" in refresh
    assert "array = global.ai_race_all_initialized" in teardown
    discovery = _named_block(effects, "ai_race_discover_participants")
    assert "array = global.countries" in discovery
    assert "ai_race_initialize_country = yes" in discovery
    assert "ai_race_teardown_global = yes" in dispatch
    assert "ai_race_clear_country_state = yes" in teardown
    assert "clr_global_flag = GLOBAL_ai_race_initialized" in teardown
    assert "ai_race_monthly_dispatch = yes" in on_actions
    assert "name = full" in rule
    assert "name = outcomes_only" in rule
    assert "name = disabled" in rule


def test_country_adapters_use_one_energy_guard_and_all_ai_technology_tiers():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    rebuild = _named_block(effects, "ai_race_rebuild_country_metrics")

    assert "has_country_flag = USA_ai_core_state_initialized" in rebuild
    assert "CHI_corporate_systems_has_meaningful_state = yes" in rebuild
    assert "has_country_flag = CHI_huawei_state_initialized" in rebuild
    assert rebuild.count("check_variable = { energy_difference_variable < 0 }") == 2
    assert "check_variable = { energy_balance < 0 }" not in rebuild
    assert "unfulfilled_energy_demand_var" not in rebuild

    for tier in range(1, 15):
        assert (
            len(
                re.findall(
                    rf"\bhas_tech\s*=\s*artificial_intelligence_{tier}\b", rebuild
                )
            )
            == 2
        )

    first_clear = rebuild.index("clear_variable = ai_race_capability_external")
    first_owner_read = rebuild.index("USA_ai_core_frontier_capability")
    first_total = rebuild.index("set_variable = { ai_race_capability =")
    assert first_clear < first_owner_read < first_total


def test_rebuild_is_idempotent_and_quarter_wrapper_owns_replay_mutation():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")
    rebuild = _named_block(effects, "ai_race_rebuild_derived_state")
    quarterly = _named_block(effects, "ai_race_quarterly_reconcile")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    debug_repair = _named_block(effects, "ai_race_debug_repair")

    assert not any(
        target.endswith("_stock") for target in _variable_write_targets(metrics)
    )
    for capability in COUNTRY_CAPABILITIES:
        assert f"clear_variable = ai_race_{capability}_external" in metrics
        assert (
            f"set_variable = {{ ai_race_{capability} = ai_race_{capability}_stock }}"
            in metrics
        )
        assert (
            f"add_to_variable = {{ ai_race_{capability} = ai_race_{capability}_external }}"
            in metrics
        )

    for scheduled in (
        "global.ai_race_epoch",
        "global.ai_race_last_processed_quarter",
        "global.ai_race_dirty_update_var",
    ):
        assert scheduled not in rebuild
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert "global.ai_race_dirty_update_var" in quarterly
    assert "global.ai_race_last_processed_quarter" in dispatch
    assert "ai_race_quarterly_reconcile = yes" not in debug_repair
    assert "ai_race_rebuild_derived_state = yes" in debug_repair


def test_ranking_replay_guards_and_clamps_match_the_documented_bounds():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    repair_country = _named_block(effects, "ai_race_repair_country_state")
    repair_global = _named_block(effects, "ai_race_repair_global_state")
    ranking = _named_block(effects, "ai_race_rebuild_frontier_and_ranking")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")

    for capability in COUNTRY_CAPABILITIES:
        for suffix in ("_stock", "_external", ""):
            variable = f"ai_race_{capability}{suffix}"
            assert (
                f"clamp_variable = {{ var = {variable} min = 0 max = 100 }}"
                in repair_country
            )
    for variable in COUNTRY_DERIVED_STATE[:2]:
        assert (
            f"clamp_variable = {{ var = {variable} min = 0 max = 100 }}"
            in repair_country
        )
    assert (
        "clamp_variable = { var = ai_race_frontier_gap min = -100 max = 0 }"
        in repair_country
    )
    assert (
        "clamp_variable = { var = ai_race_rank min = 0 max = global.ai_race_all_initialized^num }"
        in repair_country
    )
    for variable in GLOBAL_STATE[:3]:
        assert (
            f"clamp_variable = {{ var = {variable} min = 0 max = 100 }}"
            in repair_global
        )

    assert "ai_race_sort_participants = yes" in ranking
    assert "global.ai_race_first_finisher_id" not in ranking
    assert (
        "ai_race_effective_capability > global.ai_race_frontier_capability" in ranking
    )
    assert (
        "set_variable = { ai_race_frontier_gap = ai_race_effective_capability }"
        in ranking
    )
    assert (
        "subtract_from_variable = { ai_race_frontier_gap = global.ai_race_frontier_capability }"
        in ranking
    )
    assert "global.ai_race_last_processed_quarter = ai_race_current_quarter" in dispatch
    for month in (1, 4, 7, 10):
        assert f"check_variable = {{ global.month = {month} }}" in dispatch


def test_debug_and_playable_decisions_have_localisation_and_logging():
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    rules_loc_bytes = GAME_RULES_LOC_PATH.read_bytes()
    race_loc_bytes = RACE_LOC_PATH.read_bytes()

    for payload in (rules_loc_bytes, race_loc_bytes):
        assert payload.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in payload
        assert b":0" not in payload

    rules_loc = rules_loc_bytes.decode("utf-8-sig")
    race_loc = race_loc_bytes.decode("utf-8-sig")
    for key in (
        "RULE_AI_RACE",
        "RULE_AI_RACE_FULL",
        "RULE_AI_RACE_FULL_DESC",
        "RULE_AI_RACE_OUTCOMES_ONLY",
        "RULE_AI_RACE_OUTCOMES_ONLY_DESC",
        "RULE_AI_RACE_OFF",
        "RULE_AI_RACE_OFF_DESC",
    ):
        assert re.search(rf"(?m)^ {key}: ", rules_loc)
    for key in (
        "AI_RACE_debug_category",
        "AI_RACE_debug_category_desc",
        "AI_RACE_debug_readout",
        "AI_RACE_debug_readout_desc",
        "AI_RACE_debug_repair",
        "AI_RACE_debug_repair_desc",
    ):
        assert re.search(rf"(?m)^ {key}: ", race_loc)

    for decision in ("research", "implementation", "expansion", "frontier"):
        name = f"AI_RACE_review_{decision}"
        block = _named_block(decisions, name)
        assert f"Decision {name}" in block
        assert re.search(rf"(?m)^ {name}: ", race_loc)
    assert "Emergency AI Financing" in race_loc
    assert "Outstanding AI Financing" in race_loc
    assert "Capacity Shortfall" in race_loc


def _parse_race_script(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}=<>]|[^\s{}=<>]+', text)
    tokens = [token for token in tokens if not token.startswith("#")]
    cursor = 0

    def block():
        nonlocal cursor
        result = []
        while cursor < len(tokens) and tokens[cursor] != "}":
            key, comparison, value = tokens[cursor : cursor + 3]
            cursor += 3
            if value == "{":
                value = block()
                assert tokens[cursor] == "}"
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


class RaceScript:
    """Execute race source; stub only the separately tested owner-system boundaries."""

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

    def __init__(self, mode="full", corporate_mode="full"):
        self.effects = _parse_race_script(
            EFFECTS_PATH.read_text(encoding="utf-8")
            + PROGRESSION_PATH.read_text(encoding="utf-8")
        )
        self.triggers = _parse_race_script(TRIGGERS_PATH.read_text(encoding="utf-8"))
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_triggers/MD_great_ai_race_ai_triggers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        for filename, names in (
            (
                "00_economic_triggers.txt",
                ("ai_has_high_deficit", "ai_has_major_economic_problems"),
            ),
            ("00_investment_scripted_triggers.txt", ("investment_ai_offer_pending",)),
        ):
            parsed = _parse_race_script(
                (ROOT / "common/scripted_triggers" / filename).read_text(
                    encoding="utf-8"
                )
            )
            self.triggers.update({name: parsed[name] for name in names})
        self.mode, self.corporate_mode = mode, corporate_mode
        self.countries, self.globals, self.temps = {}, {}, {}
        self.scope_stack = []
        self.global_flags, self.events, self.charges = {}, [], []
        self.unlocked_categories = []
        self.today = date(2016, 1, 1)
        self.goto(2016, 1)

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
            for key, _op, operand in name:
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
                result = member in self.value(name, identifier)
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
                size = next(entry for entry in operand if entry[0] == "size")
                result = self.comparisons[size[1]](
                    country["free_slots"].get(data["building"], 0),
                    self.value(size[2], identifier),
                )
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
                for member in list(self.value(data["array"], identifier)):
                    self.scope_stack.append(identifier)
                    try:
                        self.execute(
                            [entry for entry in operand if entry[0] != "array"], member
                        )
                    finally:
                        self.scope_stack.pop()
            elif key == "for_each_loop":
                data = {key: value for key, _op, value in operand}
                for member in list(self.value(data["array"], identifier)):
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
                value = self.value(data["var"], identifier)
                if "min" in data:
                    value = max(value, self.value(data["min"], identifier))
                if "max" in data:
                    value = min(value, self.value(data["max"], identifier))
                scope[name] = value
            elif key == "add_to_array":
                name, _op, raw = operand[0]
                scope, name = self._scope(name, identifier)
                scope.setdefault(name, []).append(
                    identifier if raw == "THIS" else self.value(raw, identifier)
                )
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
                self.events.append((identifier, event_id))
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


def test_harness_rejects_the_unsupported_temporary_clear_effect():
    race = RaceScript()
    race.country(1)
    with pytest.raises(AssertionError, match="Unsupported effect clear_temp_variable"):
        race.execute([("clear_temp_variable", "=", "counter")], 1)


def test_harness_rejects_math_blocks_inside_variable_comparisons():
    race = RaceScript()
    race.country(1)
    script = _parse_race_script(
        "trigger = { check_variable = { var = counter value = { value = 2 multiply = 8 } } }"
    )["trigger"]
    with pytest.raises(AssertionError, match="check_variable needs a scalar value"):
        race.condition(script, 1)


@pytest.mark.parametrize("initial, expected", [(0, 23), (1, 15), (2, 18)])
def test_harness_branches_observe_mutations_and_keep_nested_chains_independent(
    initial, expected
):
    race = RaceScript()
    country = race.country(1)
    country["vars"]["counter"] = initial
    script = _parse_race_script("""
        effects = {
            if = {
                limit = { check_variable = { counter = 0 } }
                set_variable = { counter = 1 }
                if = {
                    limit = { check_variable = { counter = 2 } }
                    set_variable = { counter = 100 }
                }
                else_if = {
                    limit = { check_variable = { counter = 1 } }
                    add_to_variable = { counter = 2 }
                }
                else = { set_variable = { counter = 1000 } }
            }
            else_if = {
                limit = { check_variable = { counter = 1 } }
                add_to_variable = { counter = 4 }
            }
            else = { add_to_variable = { counter = 6 } }
            if = {
                limit = { check_variable = { counter > 4 } }
                add_to_variable = { counter = 10 }
            }
            else = { add_to_variable = { counter = 20 } }
        }
        trigger = {
            if = {
                limit = { check_variable = { counter > 20 } }
                check_variable = { counter = 23 }
            }
            else = { check_variable = { counter < 20 } }
        }
        """)
    race.execute(script["effects"], 1)
    assert country["vars"]["counter"] == expected
    assert race.condition(script["trigger"], 1)
    country["vars"]["counter"] = 24
    assert not race.condition(script["trigger"], 1)


@pytest.mark.parametrize(
    "value, present", [("", False), ("value = 0", False), ("value = 1", True)]
)
def test_harness_timed_flag_presence_requires_nonzero_value(value, present):
    race = RaceScript()
    country = race.country(1)
    statements = _parse_race_script(
        f"effect = {{ set_country_flag = {{ flag = pending days = 9 {value} }} }}"
    )["effect"]
    race.execute(statements, 1)
    assert race._flag(country["flags"], "pending") is present
    race.goto(2016, 1, 9)
    assert race._flag(country["flags"], "pending") is present
    race.goto(2016, 1, 10)
    assert not race._flag(country["flags"], "pending")


def _enrolled_race(
    *,
    stage=0,
    month=1,
    year=2016,
    ai=False,
    ratios=None,
    mode="full",
    corporate_mode="full",
):
    race = RaceScript(mode, corporate_mode)
    country = race.country(1, ai=ai)
    race.goto(year, month)
    race.run("ai_race_refresh_dashboard", 1)
    country["vars"]["ai_race_stage"] = stage
    country["vars"]["ai_race_stage_months"] = race.durations[stage]
    country["vars"]["ai_race_stage_entry_month"] = (year - 1) * 12 + month
    if ratios is not None:
        country["ratios"] = ratios
    race.run("ai_race_refresh_operating_state", 1)
    return race, country


def _review_and_commit(race, identifier=1, financing=False):
    race.temps["ai_race_requested_stage"] = (
        race.countries[identifier]["vars"].get("ai_race_stage", 0) + 1
    )
    race.run("ai_race_begin_review", identifier)
    race.temps["ai_race_requested_financing"] = int(financing)
    race.run("ai_race_commit_review", identifier)


@pytest.mark.parametrize(
    "financing,ratios,principal",
    [(False, [1] * 6, 0), (True, [1, 1, 0.75, 1, 1, 1], 550), (True, [0] * 6, 850)],
)
def test_executed_normal_and_emergency_transactions(financing, ratios, principal):
    race, country = _enrolled_race(ratios=ratios)
    _review_and_commit(race, financing=financing)
    assert country["vars"]["ai_race_stage"] == 1
    assert country["vars"].get("ai_race_stage_months", 0) == 0
    assert race.charges == [(1, -50)]
    assert country["vars"]["treasury"] == 99950
    assert len(country["ledger"]) == int(financing)
    if financing:
        stage, approved, weekly, term = country["ledger"][0]
        assert (stage, approved, term) == pytest.approx((1, principal, 520))
        assert weekly * term == pytest.approx(approved)


@pytest.mark.parametrize(
    "change",
    [
        "treasury",
        "gdp",
        "ratio",
        "date",
        "tech",
        "bankruptcy",
        "skip_cost",
        "unsettled",
    ],
)
def test_executed_confirmation_rechecks_and_charges_nothing_on_invalid_state(change):
    race, country = _enrolled_race()
    race.temps["ai_race_requested_stage"] = 1
    race.run("ai_race_begin_review", 1)
    if change == "treasury":
        country["vars"]["treasury"] = 49.999
    elif change == "gdp":
        country["vars"]["gdp_total"] += 1
    elif change == "ratio":
        country["ratios"][0] = 0.999
    elif change == "date":
        race.goto(2015, 12, 31)
    elif change == "tech":
        country["techs"].clear()
    elif change == "bankruptcy":
        country["missions"].add("bankruptcy_incoming_collapse")
    elif change == "skip_cost":
        country["flags"]["MD_skip_treasury_cost"] = None
    else:
        country["vars"]["ai_race_capacity_settled"] = 0
    race.temps["ai_race_requested_financing"] = 0
    race.run("ai_race_commit_review", 1)
    assert race.charges == []
    assert country["vars"]["ai_race_stage"] == 0
    assert country["ledger"] == []
    assert race.events[-1] == (1, "ai_race.11")


@pytest.mark.parametrize("action", ["cancel", "expired", "duplicate"])
def test_executed_cancel_expiry_and_duplicate_confirmation(action):
    race, country = _enrolled_race()
    race.temps["ai_race_requested_stage"] = 1
    race.run("ai_race_begin_review", 1)
    race.temps["ai_race_requested_financing"] = 0
    if action == "cancel":
        race.run("ai_race_defer_review", 1)
    elif action == "expired":
        race.goto(2016, 1, 8)
    else:
        race.run("ai_race_commit_review", 1)
    race.run("ai_race_commit_review", 1)
    assert len(race.charges) == (1 if action == "duplicate" else 0)
    assert "AI_RACE_review_pending" not in country["flags"]


def test_executed_pending_lock_prevents_duplicate_dialogs_and_eventually_expires():
    race, _country = _enrolled_race()
    race.temps["ai_race_requested_stage"] = 1
    race.run("ai_race_begin_review", 1)
    race.run("ai_race_begin_review", 1)
    assert race.events == [(1, "ai_race.1")]
    race.goto(2016, 1, 10)
    race.run("ai_race_begin_review", 1)
    assert race.events == [(1, "ai_race.1"), (1, "ai_race.1")]


def test_executed_earliest_months_reach_terminal_in_january_2025_without_entry_credit():
    race, country = _enrolled_race(ai=True)
    for year in range(2016, 2026):
        for month in range(1, 13):
            if (year, month) > (2025, 1):
                break
            race.goto(year, month)
            race.run("ai_race_monthly_dispatch", 1)
            if (year, month) in {(2016, 1), (2019, 1), (2024, 1), (2025, 1)}:
                expected = {(2016, 1): 1, (2019, 1): 2, (2024, 1): 3, (2025, 1): 4}[
                    (year, month)
                ]
                assert country["vars"]["ai_race_stage"] == expected
                assert country["vars"].get("ai_race_stage_months", 0) == 0
    assert race.charges == [(1, -50), (1, -150), (1, -400), (1, -1000)]
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert race.events == [(1, "ai_race_news.1")]


def test_executed_progress_survives_shortage_and_repair_without_replay():
    race, country = _enrolled_race(ratios=[0.5] * 6)
    _review_and_commit(race, financing=True)
    race.goto(2016, 2)
    race.run("ai_race_monthly_dispatch", 1)
    assert country["vars"]["ai_race_stage_months"] == 1
    ledger = copy.deepcopy(country["ledger"])
    country["ratios"] = [0] * 6
    for action in (
        "ai_race_debug_repair",
        "ai_race_refresh_dashboard",
        "ai_race_monthly_dispatch",
    ):
        race.run(action, 1)
    reloaded = copy.deepcopy(race)
    reloaded.run("ai_race_monthly_dispatch", 1)
    assert reloaded.countries[1]["vars"]["ai_race_stage_months"] == 1
    assert reloaded.countries[1]["ledger"] == ledger
    assert country["vars"]["ai_race_effective_capability"] == 0
    country["ratios"] = [1] * 6
    race.run("ai_race_refresh_dashboard", 1)
    assert country["vars"]["ai_race_effective_capability"] == 50
    assert country["ledger"] == ledger


@pytest.mark.parametrize("mode", ["full", "outcomes_only", "disabled"])
@pytest.mark.parametrize("corporate_mode", ["full", "outcomes_only", "disabled"])
def test_executed_mode_cross_product_and_late_start(mode, corporate_mode):
    race = RaceScript(mode, corporate_mode)
    country = race.country(1, ai=True)
    race.goto(2030, 6)
    race.run("ai_race_monthly_dispatch", 1)
    assert country["vars"].get("ai_race_stage", 0) == (1 if mode == "full" else 0)
    assert len(race.charges) == (1 if mode == "full" else 0)
    assert race.globals.get("ai_race_all_initialized", []) == (
        [] if mode == "disabled" else [1]
    )
    assert "ai_race_first_finisher_id" not in race.globals


def test_executed_generic_discovery_inactivity_return_and_off_cleanup():
    race = RaceScript()
    country = race.country(1, tag="BRA")
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1]
    _review_and_commit(race)
    country["exists"] = False
    race.goto(2016, 2)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_participants"] == []
    assert country["vars"]["ai_race_stage"] == 1
    country["exists"] = True
    country["techs"].clear()
    race.goto(2016, 3)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_participants"] == [1]
    assert country["vars"]["ai_race_stage_months"] == 1
    country["exists"] = False
    country["vars"]["debt"] = 123
    race.mode = "disabled"
    race.run("ai_race_monthly_dispatch", 1)
    assert not any(key.startswith("ai_race_") for key in country["vars"])
    assert country["flags"] == {}
    assert country["vars"]["debt"] == 123
    assert race.globals["ai_race_all_initialized"] == []


def test_executed_human_enrollment_between_discovery_and_next_january():
    race = RaceScript()
    race.country(1)
    later = race.country(2, tag="IND")
    later["techs"].clear()
    race.run("ai_race_monthly_dispatch", 1)
    race.goto(2016, 2)
    later["techs"].add("artificial_intelligence_7")
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1]
    race.run("ai_race_refresh_dashboard", 2)
    assert race.globals["ai_race_all_initialized"] == [1, 2]
    assert race.charges == []
    assert not later["vars"].get("ai_race_stage_months")


@pytest.mark.parametrize("mode", ["full", "outcomes_only", "disabled"])
@pytest.mark.parametrize("corporate_mode", ["full", "outcomes_only", "disabled"])
@pytest.mark.parametrize("year, ai", [(2015, False), (2016, False), (2016, True)])
def test_technology_completion_announces_human_enrollment_once_before_interaction(
    mode, corporate_mode, year, ai
):
    race = RaceScript(mode, corporate_mode)
    country = race.country(1, ai=ai)
    race.goto(year, 6)
    technology = _named_block(
        (ROOT / "common/technologies/engineering.txt").read_text(encoding="utf-8"),
        "artificial_intelligence_7",
    )
    completed = _parse_race_script(_named_block(technology, "on_research_complete"))[
        "on_research_complete"
    ]
    race.execute(completed, 1)
    eligible_human = mode != "disabled" and year >= 2016 and not ai
    assert race.unlocked_categories == (
        [(1, "AI_RACE_category")] if eligible_human else []
    )
    assert race.globals.get("ai_race_all_initialized", []) == (
        [1] if eligible_human else []
    )
    race.execute(completed, 1)
    assert len(race.unlocked_categories) == int(eligible_human)
    assert race.charges == country["ledger"] == []
    assert country["vars"].get("ai_race_stage", 0) == 0


def test_executed_ranking_stage_progress_capability_id_and_frontier_are_distinct():
    race = RaceScript()
    for identifier, stage, progress, capability in [
        (4, 1, 10, 80),
        (3, 2, 0, 20),
        (2, 1, 11, 50),
        (1, 1, 11, 50),
    ]:
        country = race.country(identifier, capability=capability)
        race.run("ai_race_initialize_country", identifier)
        country["vars"].update(
            ai_race_stage=stage,
            ai_race_stage_months=progress,
            ai_race_effective_capability=capability,
        )
    race.run("ai_race_rebuild_frontier_and_ranking", 4)
    assert race.globals["ai_race_ranked_participants"] == [3, 1, 2, 4]
    assert race.globals["ai_race_leader_id"] == 3
    assert race.globals["ai_race_frontier_capability"] == 80
    assert race.countries[3]["vars"]["ai_race_frontier_gap"] == -60
    assert "ai_race_first_finisher_id" not in race.globals


@pytest.mark.parametrize("reverse", [False, True])
def test_executed_simultaneous_autonomous_terminal_candidates_have_one_historical_winner(
    reverse,
):
    race = RaceScript()
    for identifier, capability in (
        [(3, 60), (2, 80), (1, 80)] if not reverse else [(1, 80), (2, 80), (3, 60)]
    ):
        country = race.country(identifier, ai=True, capability=capability)
        race.run("ai_race_initialize_country", identifier)
        country["vars"].update(
            ai_race_stage=3,
            ai_race_stage_months=11,
            ai_race_stage_entry_month=2024 * 12 + 1,
        )
    race.goto(2025, 1)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert all(
        country["vars"]["ai_race_stage"] == 4 for country in race.countries.values()
    )
    assert [event for event in race.events if event[1] == "ai_race_news.1"] == [
        (1, "ai_race_news.1")
    ]
    race.countries[1]["exists"] = False
    race.run("ai_race_rebuild_derived_state", 2)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert race.globals["ai_race_leader_id"] == 2


@pytest.mark.parametrize(
    "constraint", ["allowed", "readiness", "debt", "weekly", "reserve"]
)
def test_executed_autonomous_emergency_policy_boundaries(constraint):
    race, country = _enrolled_race(ai=True, ratios=[0.75] * 6)
    country["vars"]["debt"] = 599.999
    if constraint == "readiness":
        country["ratios"][5] = 0.749
    elif constraint == "debt":
        country["vars"]["debt"] = 600
    elif constraint == "weekly":
        country["vars"]["treasury_rate"] = 550 / 520 - 0.001
    elif constraint == "reserve":
        country["vars"]["treasury"] = 50 + (2 + 550 / 520) * 52 - 0.001
    race.run("ai_race_autonomous_purchase", 1)
    assert bool(country["ledger"]) is (constraint == "allowed")
    assert len(race.charges) == (1 if constraint == "allowed" else 0)


@pytest.mark.parametrize(
    "stage,year,technology", [(0, 2016, 7), (1, 2019, 7), (2, 2024, 8), (3, 2025, 8)]
)
def test_executed_stage_dates_technology_and_completed_work_are_all_required(
    stage, year, technology
):
    race, country = _enrolled_race(stage=stage, year=year)
    race.goto(year - 1, 12, 31)
    assert not race.condition(race.triggers["ai_race_can_review"], 1)
    race.goto(year, 1)
    assert race.condition(race.triggers["ai_race_can_review"], 1)
    country["techs"].discard(f"artificial_intelligence_{technology}")
    assert not race.condition(race.triggers["ai_race_can_review"], 1)
    country["techs"].add(f"artificial_intelligence_{technology}")
    if stage:
        country["vars"]["ai_race_stage_months"] -= 1
        assert not race.condition(race.triggers["ai_race_can_review"], 1)


@pytest.mark.parametrize("criterion", range(6))
def test_executed_direct_funding_requires_every_readiness_boundary(criterion):
    race, country = _enrolled_race()
    country["ratios"][criterion] = 0.999
    _review_and_commit(race)
    assert race.charges == []
    country["ratios"][criterion] = 1
    _review_and_commit(race)
    assert race.charges == [(1, -50)]


def test_executed_two_human_finishers_receive_reports_but_only_one_world_announcement():
    race, first = _enrolled_race(stage=3, year=2025)
    second = race.country(2, tag="JAP")
    race.run("ai_race_initialize_country", 2)
    second["vars"].update(ai_race_stage=3, ai_race_stage_months=12)
    race.run("ai_race_refresh_operating_state", 2)
    _review_and_commit(race)
    _review_and_commit(race, identifier=2)
    assert first["vars"]["ai_race_stage"] == second["vars"]["ai_race_stage"] == 4
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert [
        (country, event)
        for country, event in race.events
        if event in {"ai_race_news.1", "ai_race.10"}
    ] == [(1, "ai_race_news.1"), (1, "ai_race.10"), (2, "ai_race.10")]


def test_executed_annual_discovery_enrolls_new_ai_without_resetting_existing_history():
    race, first = _enrolled_race()
    _review_and_commit(race)
    later = race.country(2, ai=True)
    later["techs"].clear()
    race.run("ai_race_monthly_dispatch", 1)
    later["techs"].add("artificial_intelligence_7")
    race.goto(2016, 12)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1]
    race.goto(2017, 1)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1, 2]
    assert first["vars"]["ai_race_stage"] == later["vars"]["ai_race_stage"] == 1
    assert later["vars"].get("ai_race_stage_months", 0) == 0


def test_executed_outcomes_cleanup_preserves_historical_first_until_off():
    race, country = _enrolled_race(stage=3, year=2025, ratios=[0.5] * 6)
    _review_and_commit(race, financing=True)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert country["vars"]["ai_race_bonus"] == pytest.approx(0.025)
    assert country["vars"]["ai_race_demand_power"] == 60
    country["vars"]["debt"] = 77
    race.mode = "outcomes_only"
    race.run("ai_race_refresh_dashboard", 1)
    assert country["vars"].get("ai_race_stage", 0) == 0
    assert country["ledger"] == []
    assert country["vars"]["debt"] == 77
    assert country["vars"]["ai_race_bonus"] == 0
    assert country["vars"]["ai_race_demand_power"] == 0
    assert country["vars"]["ai_race_effective_capability"] == 50
    assert race.globals["ai_race_ranked_participants"] == [1]
    assert race.globals["ai_race_first_finisher_id"] == 1

    race.mode = "full"
    second = race.country(2, tag="JAP")
    race.run("ai_race_initialize_country", 2)
    second["vars"].update(ai_race_stage=3, ai_race_stage_months=12)
    race.run("ai_race_refresh_operating_state", 2)
    _review_and_commit(race, identifier=2)
    assert second["vars"]["ai_race_stage"] == 4
    assert second["vars"]["ai_race_bonus"] == pytest.approx(0.04)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert [event for event in race.events if event[1] == "ai_race_news.1"] == [
        (1, "ai_race_news.1")
    ]

    race.mode = "disabled"
    race.run("ai_race_monthly_dispatch", 1)
    assert "ai_race_first_finisher_id" not in race.globals
