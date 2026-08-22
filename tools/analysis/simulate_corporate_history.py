#!/usr/bin/env python3
"""Run deterministic, check-only corporate-history scenario simulations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Set, Tuple

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))

from shared_utils import extract_block_from_text, strip_comments

LABEL = "STATIC SCENARIO SIMULATION"
_BLOCK_RE = re.compile(r"(?m)^([A-Za-z0-9_.:@^\[\]-]+)\s*=\s*\{")
# _BLOCK_RE is anchored to column 0 for top-level definitions; nested blocks are
# indented, so walking inside an effect needs an unanchored form.
_NESTED_BLOCK_RE = re.compile(r"([A-Za-z0-9_.:@^\[\]-]+)\s*=\s*\{")
_EFFECT_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*=\s*yes\b")
_EVENT_SHORT_RE = re.compile(
    r"\b(?:country_event|news_event|state_event)\s*=\s*([A-Za-z0-9_.]+)\b(?!\s*\{)"
)
_EVENT_LONG_RE = re.compile(
    r"\b(?:country_event|news_event|state_event)\s*=\s*\{[^{}]*?\bid\s*=\s*([A-Za-z0-9_.]+)",
    re.DOTALL,
)


@dataclass(frozen=True)
class ScriptIndex:
    effects: Mapping[str, str]
    event_callers: Mapping[str, FrozenSet[str]]

    @classmethod
    def load(cls, mod_root: Path) -> "ScriptIndex":
        effects: Dict[str, str] = {}
        callers: Dict[str, Set[str]] = {}
        effects_root = mod_root / "common" / "scripted_effects"
        if not effects_root.is_dir():
            raise ScenarioError(f"missing scripted-effects tree: {effects_root}")
        for path in sorted(effects_root.rglob("*.txt")):
            text = strip_comments(
                path.read_text(encoding="utf-8-sig", errors="replace")
            )
            for match in _BLOCK_RE.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                name = match.group(1)
                if name in effects:
                    continue
                effects[name] = body
                for event_id in _event_calls(body):
                    callers.setdefault(event_id, set()).add(name)
        return cls(
            effects=effects,
            event_callers={
                event_id: frozenset(owners) for event_id, owners in callers.items()
            },
        )

    def reaches_marker(self, effect: str, marker: str) -> bool:
        return self._reaches_marker(effect, marker, frozenset())

    def _reaches_marker(self, effect: str, marker: str, seen: FrozenSet[str]) -> bool:
        if effect in seen or effect not in self.effects:
            return False
        body = self.effects[effect]
        flag_pattern = re.compile(
            rf"\bset_country_flag\s*=\s*(?:{re.escape(marker)}\b|\{{\s*flag\s*=\s*{re.escape(marker)}\b)"
        )
        idea_pattern = re.compile(
            rf"\badd_ideas\s*=\s*(?:{re.escape(marker)}\b|\{{[^}}]*\b{re.escape(marker)}\b[^}}]*\}})",
            re.DOTALL,
        )
        if flag_pattern.search(body) or idea_pattern.search(body):
            return True
        return any(
            self._reaches_marker(called, marker, seen | {effect})
            for called in _EFFECT_RE.findall(body)
        )

    def terminal_dates(self, effect: str, marker: str) -> FrozenSet[str]:
        body = self.effects.get(effect, "")
        marker_pattern = re.compile(
            rf"\bset_country_flag\s*=\s*(?:{re.escape(marker)}\b|\{{\s*flag\s*=\s*{re.escape(marker)}\b)"
        )
        dates: Set[str] = set()
        for match in re.finditer(r"\b(?:if|else_if)\s*=\s*\{", body):
            child, end = extract_block_from_text(body, match.end() - 1)
            if end == -1 or not marker_pattern.search(child):
                continue
            dates.update(re.findall(r"\bdate\s*>\s*(\d{4}\.\d{1,2}\.\d{1,2})", child))
        if not dates:
            return frozenset()
        latest = max(
            dates,
            key=lambda value: tuple(int(part) for part in value.split(".")),
        )
        return frozenset({latest})

    def scheduler_years(self, scheduler: str, event_id: str) -> FrozenSet[int]:
        years: Set[int] = set()
        _collect_scheduler_years(self.effects.get(scheduler, ""), event_id, None, years)
        return frozenset(years)


def _event_calls(body: str) -> Set[str]:
    return set(_EVENT_SHORT_RE.findall(body)) | set(_EVENT_LONG_RE.findall(body))


def _direct_child_blocks(body: str) -> List[Tuple[str, str]]:
    """(name, body) of the blocks one level down, skipping nested ones."""
    children: List[Tuple[str, str]] = []
    pos = 0
    while True:
        match = _NESTED_BLOCK_RE.search(body, pos)
        if not match:
            return children
        child, end = extract_block_from_text(body, match.end() - 1)
        if end == -1:
            pos = match.end()
            continue
        children.append((match.group(1), child))
        pos = end


def _block_limit(block: str) -> str:
    return next(
        (child for name, child in _direct_child_blocks(block) if name == "limit"), ""
    )


def _start_date_window(block: str) -> Optional[int]:
    """Year of the `NOT = { has_start_date < Y.1.1 } ... has_start_date < Y.1.2` pair.

    The lower bound always sits in the block's own limit. The upper bound may sit
    there too, or — where the block opens a whole-year window and its arms split
    January 1 from the rest (Nintendo, Russian Computing Sovereignty) — in the
    limit of a direct child arm. A sibling milestone's window is never consulted.
    """
    own = _block_limit(block)
    lower = re.search(
        r"NOT\s*=\s*\{\s*has_start_date\s*<\s*(\d{4})\.1\.1\s*\}",
        own,
    )
    if not lower:
        return None
    candidates = [own] + [
        _block_limit(child)
        for name, child in _direct_child_blocks(block)
        if name in ("if", "else_if")
    ]
    for text in candidates:
        upper = re.search(r"\bhas_start_date\s*<\s*(\d{4})\.1\.2\b", text)
        if upper and upper.group(1) == lower.group(1):
            return int(lower.group(1))
    return None


def _count_event_calls(body: str, event_id: str) -> int:
    return sum(
        1
        for target in _EVENT_SHORT_RE.findall(body) + _EVENT_LONG_RE.findall(body)
        if target == event_id
    )


def _collect_scheduler_years(
    body: str, event_id: str, inherited: Optional[int], years: Set[int]
) -> None:
    """Walk if/else_if children tracking the innermost start-date window in scope.

    Schedulers hoist their chain-level guard into an outer `if`, so a milestone's
    January-1 window can sit above the block that queues the event. The window is
    read from each block's own `limit`, never from a sibling milestone's.
    """
    for name, child in _direct_child_blocks(body):
        if name not in ("if", "else_if"):
            continue
        total = _count_event_calls(child, event_id)
        if not total:
            continue
        window = _start_date_window(child)
        if window is None:
            window = inherited
        nested = sum(
            _count_event_calls(grandchild, event_id)
            for gname, grandchild in _direct_child_blocks(child)
            if gname in ("if", "else_if")
        )
        if total > nested and window is not None:
            years.add(window)
        if nested:
            _collect_scheduler_years(child, event_id, window, years)


class ScenarioError(ValueError):
    """Raised when a scenario or manifest entry is malformed."""


def _load_json(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenarioError(f"cannot load {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ScenarioError(f"{path} must contain a JSON object")
    return payload


def _parse_date(value: object, label: str) -> date:
    if not isinstance(value, str):
        raise ScenarioError(f"{label} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ScenarioError(f"{label} is not an ISO date: {value}") from exc


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _require_integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ScenarioError(f"{label} must be an integer")
    return value


def _bridge_idea(score: int) -> str:
    if score < 15:
        level = 1
    elif score < 22:
        level = 2
    elif score < 29:
        level = 3
    elif score < 38:
        level = 4
    else:
        level = 5
    return f"USA_corporate_systems_economic_integration_{level}"


def _simulate_bridge(scenario: Mapping[str, object]) -> Dict[str, object]:
    if scenario.get("mode") == "disabled":
        return {
            "applied_deltas": [],
            "cleared": True,
            "effective_axes": [],
            "idea": None,
            "score": 0,
        }

    effective_axes: List[int] = []
    applied_deltas: List[int] = []
    for index, raw_axis in enumerate(scenario.get("axes", [])):
        if not isinstance(raw_axis, dict):
            raise ScenarioError(f"axes[{index}] must be an object")
        base = _require_integer(raw_axis.get("base", 0), f"axes[{index}].base")
        contribution = _require_integer(
            raw_axis.get("contribution", 0), f"axes[{index}].contribution"
        )
        effective = _clamp(base + contribution, 0, 10)
        effective_axes.append(effective)
        applied_deltas.append(effective - base)

    if effective_axes:
        score = sum(effective_axes)
    else:
        score = _clamp(_require_integer(scenario.get("score", 0), "score"), 0, 50)
    return {
        "applied_deltas": applied_deltas,
        "cleared": False,
        "effective_axes": effective_axes,
        "idea": _bridge_idea(score),
        "score": score,
    }


def _chain_index(manifest: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
    result: Dict[str, Mapping[str, object]] = {}
    schema_version = manifest.get("schema_version", 1)
    if type(schema_version) is not int or schema_version < 1:
        raise ScenarioError("manifest schema_version must be a positive integer")
    chains = manifest.get("chains", [])
    if not isinstance(chains, list):
        raise ScenarioError("manifest chains must be a list")
    for raw_chain in chains:
        if not isinstance(raw_chain, dict) or not isinstance(
            raw_chain.get("root"), str
        ):
            raise ScenarioError("each manifest chain must have a string root")
        root = raw_chain["root"]
        if root in result:
            raise ScenarioError(f"duplicate manifest chain root: {root}")
        chain = dict(raw_chain)
        chain["_schema_version"] = schema_version
        result[root] = chain
        for auxiliary in raw_chain.get("auxiliary_lifecycles", []):
            if not isinstance(auxiliary, dict) or not isinstance(
                auxiliary.get("root"), str
            ):
                raise ScenarioError(f"{root} has a malformed auxiliary lifecycle")
            auxiliary_root = auxiliary["root"]
            if auxiliary_root in result:
                raise ScenarioError(
                    f"duplicate manifest lifecycle root: {auxiliary_root}"
                )
            result[auxiliary_root] = {
                "root": auxiliary_root,
                "tag": auxiliary.get("tag"),
                "full_start_strategies": [
                    "yearly_dispatcher",
                    "current_year_scheduler",
                    "reconstruction",
                ],
                "outcomes_only_strategy": "reconstruction",
                "terminal_marker": auxiliary.get("terminal_marker"),
                "terminal_date": auxiliary.get("terminal_date"),
                "dependency_order": [],
                "expected_callers": raw_chain.get("expected_callers", {}),
                "reconstruction_effect": auxiliary.get("reconstruction_effect"),
                "scheduler_effect": auxiliary.get("scheduler_effect"),
                "expected_yearly_callers": auxiliary.get("expected_yearly_callers", {}),
                "_schema_version": schema_version,
            }
    return result


def _recovery_callers(
    chain: Mapping[str, object], actual_callers: Set[str]
) -> Set[str]:
    owner = chain.get("tag")
    root = chain.get("root")
    generic = (
        f"{owner}_corporate_history_recover_midyear_events"
        if isinstance(owner, str)
        else ""
    )
    native_prefix = f"{root}_recover_" if isinstance(root, str) else ""
    return {
        caller
        for caller in actual_callers
        if caller == generic or (native_prefix and caller.startswith(native_prefix))
    }


def _simulate_history(
    scenario: Mapping[str, object],
    chains: Mapping[str, Mapping[str, object]],
    scripts: Optional[ScriptIndex] = None,
) -> Dict[str, object]:
    root = scenario.get("chain")
    if not isinstance(root, str) or root not in chains:
        raise ScenarioError(f"unknown scenario chain: {root}")
    chain = chains[root]
    mode = scenario.get("mode")
    if mode not in ("full", "outcomes_only", "disabled"):
        raise ScenarioError(f"unsupported corporate-history mode: {mode}")
    if scenario.get("owner") != chain.get("tag"):
        raise ScenarioError(f"{root} scenario owner must be {chain.get('tag')}")

    raw_dependencies = scenario.get("dependencies")
    if not isinstance(raw_dependencies, list) or not all(
        isinstance(dependency, str) for dependency in raw_dependencies
    ):
        raise ScenarioError(f"{root} scenario dependencies must be a list of chains")
    declared_dependencies = list(chain.get("dependency_order", []))
    if raw_dependencies != declared_dependencies:
        raise ScenarioError(
            f"{root} scenario dependencies must exactly match dependency_order: "
            f"expected {declared_dependencies}, found {raw_dependencies}"
        )
    missing_chains = set(raw_dependencies) - set(chains)
    if missing_chains:
        raise ScenarioError(
            f"{root} scenario dependencies are absent from the manifest: "
            f"{', '.join(sorted(missing_chains))}"
        )

    start = _parse_date(scenario.get("start_date"), "start_date")
    raw_owner_available = scenario.get("owner_available_from")
    owner_available = (
        start
        if raw_owner_available is None
        else _parse_date(raw_owner_available, "owner_available_from")
    )
    activation = max(start, owner_available)
    schema_version = int(chain.get("_schema_version", 1))
    initial_markers = set(scenario.get("initial_markers", []))
    strategies = set(chain.get("full_start_strategies", []))
    outcomes_strategy = chain.get("outcomes_only_strategy")
    reconstruction_effect = str(
        chain.get("reconstruction_effect", f"{root}_reconstruct_history")
    )
    scheduler_effect = str(
        chain.get("scheduler_effect", f"{root}_schedule_current_year_events")
    )
    can_reconstruct = bool(
        strategies.intersection(
            {"hidden_anchor", "persistent_catchup", "reconstruction"}
        )
    )
    if scripts is not None:
        if can_reconstruct and reconstruction_effect not in scripts.effects:
            raise ScenarioError(
                f"{root} declares reconstruction without {reconstruction_effect}"
            )
        if (
            "current_year_scheduler" in strategies
            and scheduler_effect not in scripts.effects
        ):
            raise ScenarioError(
                f"{root} declares current-year scheduling without {scheduler_effect}"
            )

    visible: List[str] = []
    reconstructed: List[str] = []
    stranded: List[str] = []
    for index, raw_milestone in enumerate(scenario.get("milestones", [])):
        if not isinstance(raw_milestone, dict):
            raise ScenarioError(f"milestones[{index}] must be an object")
        event_id = raw_milestone.get("event_id")
        marker = raw_milestone.get("marker")
        if not isinstance(event_id, str) or not isinstance(marker, str):
            raise ScenarioError(f"milestones[{index}] needs event_id and marker")
        if marker in initial_markers:
            continue
        milestone_date = _parse_date(
            raw_milestone.get("date"), f"milestones[{index}].date"
        )
        if scripts is not None:
            actual_callers = set(scripts.event_callers.get(event_id, frozenset()))
            declared_callers = chain.get("expected_callers", {}).get(event_id)
            if isinstance(declared_callers, list):
                declared_effect_callers = {
                    caller.removeprefix("effect:")
                    for caller in declared_callers
                    if isinstance(caller, str) and caller.startswith("effect:")
                }
                effective_declared_callers = set(declared_effect_callers)
                if schema_version >= 6:
                    effective_declared_callers.update(
                        _recovery_callers(chain, actual_callers)
                    )
                if actual_callers != effective_declared_callers:
                    raise ScenarioError(
                        f"{event_id} scripted callers differ from the contract: "
                        f"expected {sorted(effective_declared_callers)}, found {sorted(actual_callers)}"
                    )
                declared_years = {
                    int(match.group(1))
                    for caller in declared_effect_callers
                    if (match := re.search(r"_corporate_trigger_year_(\d{4})$", caller))
                }
                if declared_years and declared_years != {milestone_date.year}:
                    raise ScenarioError(
                        f"{event_id} milestone year differs from its yearly caller: "
                        f"expected {sorted(declared_years)}, found {milestone_date.year}"
                    )
                if scheduler_effect in declared_effect_callers and (
                    scripts.scheduler_years(scheduler_effect, event_id)
                    != {milestone_date.year}
                ):
                    raise ScenarioError(
                        f"{event_id} scheduler window differs from its milestone year "
                        f"{milestone_date.year}"
                    )
            expected_yearly = chain.get("expected_yearly_callers", {}).get(event_id)
            if isinstance(expected_yearly, str):
                actual_yearly = {
                    caller
                    for caller in actual_callers
                    if "_corporate_trigger_year_" in caller
                }
                if actual_yearly != {expected_yearly}:
                    raise ScenarioError(
                        f"{event_id} yearly caller differs from the auxiliary lifecycle: "
                        f"expected {expected_yearly}, found {sorted(actual_yearly)}"
                    )
                year_match = re.search(
                    r"_corporate_trigger_year_(\d{4})$", expected_yearly
                )
                expected_year = int(year_match.group(1)) if year_match else -1
                if scripts.scheduler_years(scheduler_effect, event_id) != {
                    expected_year
                }:
                    raise ScenarioError(
                        f"{event_id} scheduler window does not match {expected_yearly}"
                    )
        if mode == "disabled":
            continue
        marker_reconstructable = scripts is None or scripts.reaches_marker(
            reconstruction_effect, marker
        )
        if mode == "outcomes_only":
            if (
                milestone_date < activation
                and outcomes_strategy == "reconstruction"
                and marker_reconstructable
            ):
                reconstructed.append(marker)
            continue
        if milestone_date < activation:
            (
                reconstructed
                if can_reconstruct and marker_reconstructable
                else stranded
            ).append(marker)
        elif milestone_date.year == activation.year:
            january_first = activation.month == 1 and activation.day == 1
            actual_callers = (
                set()
                if scripts is None
                else set(scripts.event_callers.get(event_id, frozenset()))
            )
            scheduler_matches = scripts is None or (
                activation.year in scripts.scheduler_years(scheduler_effect, event_id)
                and scheduler_effect in scripts.event_callers.get(event_id, frozenset())
            )
            recovery_matches = scripts is None or bool(
                _recovery_callers(chain, actual_callers)
            )
            if "current_year_scheduler" in strategies and (
                (schema_version >= 6 and (scheduler_matches or recovery_matches))
                or (schema_version < 6 and january_first and scheduler_matches)
            ):
                visible.append(event_id)
            else:
                stranded.append(marker)
        elif "yearly_dispatcher" in strategies and (
            scripts is None or scripts.event_callers.get(event_id)
        ):
            visible.append(event_id)

    completion_markers: List[str] = []
    terminal_date = chain.get("terminal_date")
    terminal_marker = chain.get("terminal_marker")
    if (
        mode != "disabled"
        and isinstance(terminal_date, str)
        and isinstance(terminal_marker, str)
    ):
        terminal = _parse_date(terminal_date, f"{root}.terminal_date")
        expected_terminal = f"{terminal.year}.{terminal.month}.{terminal.day}"
        terminal_matches = scripts is None or scripts.terminal_dates(
            reconstruction_effect, terminal_marker
        ) == {expected_terminal}
        if scripts is not None and not terminal_matches:
            actual = sorted(
                scripts.terminal_dates(reconstruction_effect, terminal_marker)
            )
            raise ScenarioError(
                f"{root} terminal guard differs from the manifest: "
                f"expected date > {expected_terminal}, found {actual}"
            )
        if (
            activation > terminal
            and terminal_matches
            and (
                (mode == "outcomes_only" and outcomes_strategy == "reconstruction")
                or (mode == "full" and can_reconstruct)
            )
        ):
            completion_markers.append(terminal_marker)

    return {
        "completion_markers": sorted(completion_markers),
        "dependencies": list(raw_dependencies),
        "reconstructed_markers": sorted(reconstructed),
        "stranded_markers": sorted(stranded),
        "visible_events": sorted(visible),
    }


def simulate_scenario(
    scenario: Mapping[str, object],
    chains: Mapping[str, Mapping[str, object]],
    scripts: Optional[ScriptIndex] = None,
) -> Dict[str, object]:
    scenario_type = scenario.get("type")
    if scenario_type == "bridge":
        return _simulate_bridge(scenario)
    if scenario_type == "corporate_history":
        return _simulate_history(scenario, chains, scripts)
    raise ScenarioError(f"unsupported scenario type: {scenario_type}")


def run_scenarios(
    manifest: Mapping[str, object],
    scenario_payload: Mapping[str, object],
    names: Sequence[str] = (),
    scripts: Optional[ScriptIndex] = None,
) -> Tuple[List[Dict[str, object]], bool]:
    chains = _chain_index(manifest)
    raw_scenarios = scenario_payload.get("scenarios", [])
    if not isinstance(raw_scenarios, list):
        raise ScenarioError("scenarios must be a list")
    selected = set(names)
    results: List[Dict[str, object]] = []
    seen: set[str] = set()
    passed = True
    for raw_scenario in raw_scenarios:
        if not isinstance(raw_scenario, dict) or not isinstance(
            raw_scenario.get("name"), str
        ):
            raise ScenarioError("each scenario must have a string name")
        name = raw_scenario["name"]
        if name in seen:
            raise ScenarioError(f"duplicate scenario name: {name}")
        seen.add(name)
        if selected and name not in selected:
            continue
        actual = simulate_scenario(raw_scenario, chains, scripts)
        expected = raw_scenario.get("expected", {})
        if not isinstance(expected, dict):
            raise ScenarioError(f"{name}.expected must be an object")
        mismatches = {
            key: {"expected": value, "actual": actual.get(key)}
            for key, value in expected.items()
            if actual.get(key) != value
        }
        passed = passed and not mismatches
        results.append(
            {
                "name": name,
                "passed": not mismatches,
                "actual": actual,
                "mismatches": mismatches,
            }
        )
    missing = selected - seen
    if missing:
        raise ScenarioError(f"unknown scenario names: {', '.join(sorted(missing))}")
    return results, passed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true", help="run all scenarios")
    selection.add_argument("--scenario", action="append", help="run one named scenario")
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable results"
    )
    parser.add_argument(
        "--manifest", type=Path, default=TOOLS_ROOT / "corporate_history_contract.json"
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=TOOLS_ROOT / "corporate_history_scenarios.json",
    )
    parser.add_argument(
        "--mod-path",
        type=Path,
        default=TOOLS_ROOT.parent,
        help="mod root whose scripted effects are checked against each scenario",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _load_json(args.manifest)
        scenarios = _load_json(args.scenarios)
        scripts = ScriptIndex.load(args.mod_path)
        results, passed = run_scenarios(
            manifest, scenarios, args.scenario or (), scripts
        )
    except ScenarioError as exc:
        print(f"{LABEL}: configuration error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {"label": LABEL, "passed": passed, "results": results},
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(LABEL)
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{status}] {result['name']}")
            for key, mismatch in result["mismatches"].items():
                print(
                    f"  {key}: expected {mismatch['expected']!r}, got {mismatch['actual']!r}"
                )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
