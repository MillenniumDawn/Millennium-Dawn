"""Manifest, subsystem, localisation, ownership, and economic integration checks."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Mapping, Sequence, Set, Tuple

from shared_utils import blank_quoted_strings, extract_block_from_text, strip_comments

from .model import (
    _ADD_IDEA_RE,
    _BLOCK_IDENTIFIER,
    _CLAMP_VAR_RE,
    _CORPORATE_MODES,
    _EFFECT_YES_RE,
    _EVENT_KEYWORDS,
    _INDEPENDENT_DERIVED_POLICY,
    _INDEPENDENT_EVENT_POLICY,
    _INDEPENDENT_SUBSYSTEM_FIELDS,
    _LOC_KEY_PREFIX_RE,
    _READ_KEYWORDS,
    _SET_VAR_RE,
    _VALID_LOC_VALUE_RE,
    _WRITE_KEYWORDS,
    AuxiliaryLifecycleConfig,
    BlockDef,
    Bound,
    ChainConfig,
    EventDef,
    IdeaDef,
    IndependentSubsystemConfig,
    _collect_native_write_tokens,
    _is_finite_number,
    _is_repeatable_decision,
    _program_lifecycle_findings,
)


class ContentIntegrationMixin:
    def _load_manifest(self) -> List[ChainConfig]:
        if not self._manifest_path.exists():
            self.add_error(
                "Corporate-history manifest",
                f"Missing manifest: {self._manifest_path.relative_to(self._root)}",
            )
            return []
        try:
            payload = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.add_error(
                "Corporate-history manifest",
                f"Failed to load {self._manifest_path.relative_to(self._root)}: {exc}",
            )
            return []

        self._manifest_payload = payload
        self._independent_subsystems = ()

        raw_chains = payload.get("chains")
        if not isinstance(raw_chains, list) or not raw_chains:
            self.add_error(
                "Corporate-history manifest",
                "Manifest requires a non-empty chains list",
            )
            return []

        contract_version = int(payload.get("schema_version", 1))
        self._independent_subsystems = self._load_independent_subsystems(
            payload, contract_version
        )
        required_v2 = (
            "full_start_strategies",
            "outcomes_only_strategy",
            "monthly_driver",
            "terminal_marker",
            "terminal_date",
            "outcome_ideas",
            "expected_callers",
            "dependency_order",
            "localisation_prefixes",
            "effect_preview_policy",
            "bridge_refresh_policy",
        )
        chains = []
        for index, raw in enumerate(raw_chains):
            if not isinstance(raw, dict):
                self.add_error(
                    "Corporate-history manifest",
                    f"chains[{index}] must be an object",
                )
                continue
            missing = [field for field in required_v2 if field not in raw]
            if contract_version >= 2 and missing:
                self.add_error(
                    "Corporate-history manifest",
                    f"chains[{index}] is missing required fields: {', '.join(missing)}",
                )
                continue
            try:
                bounds = {
                    name: Bound(Decimal(str(cfg["min"])), Decimal(str(cfg["max"])))
                    for name, cfg in raw.get("variables", {}).items()
                }
                expected_callers = {
                    event_id: tuple(callers)
                    for event_id, callers in raw.get("expected_callers", {}).items()
                }
                auxiliary_lifecycles = tuple(
                    AuxiliaryLifecycleConfig(
                        root=str(auxiliary["root"]),
                        tag=str(auxiliary["tag"]),
                        reconstruction_effect=str(auxiliary["reconstruction_effect"]),
                        scheduler_effect=str(auxiliary["scheduler_effect"]),
                        monthly_driver=str(auxiliary["monthly_driver"]),
                        terminal_marker=str(auxiliary["terminal_marker"]),
                        terminal_date=str(auxiliary["terminal_date"]),
                        expected_yearly_callers={
                            str(event_id): str(caller)
                            for event_id, caller in auxiliary[
                                "expected_yearly_callers"
                            ].items()
                        },
                    )
                    for auxiliary in raw.get("auxiliary_lifecycles", [])
                )
                chain = ChainConfig(
                    name=raw["name"],
                    tag=raw["tag"],
                    namespace=raw["namespace"],
                    root=raw["root"],
                    tier=int(raw["tier"]),
                    owned_prefixes=tuple(raw.get("owned_prefixes", [raw["root"]])),
                    variables=bounds,
                    outcome_idea_prefixes=tuple(raw.get("outcome_idea_prefixes", [])),
                    requires_current_year_scheduler=bool(
                        raw.get("requires_current_year_scheduler", False)
                    ),
                    allow_yearly_scheduler_duplicates=bool(
                        raw.get("allow_yearly_scheduler_duplicates", False)
                    ),
                    callerless_anchors=set(raw.get("callerless_anchors", [])),
                    allowed_multiple_callers=set(
                        raw.get("allowed_multiple_callers", [])
                    ),
                    allowed_reads=tuple(raw.get("allowed_reads", [])),
                    allowed_writes=tuple(raw.get("allowed_writes", [])),
                    full_start_strategies=tuple(raw.get("full_start_strategies", [])),
                    outcomes_only_strategy=str(raw.get("outcomes_only_strategy", "")),
                    declared_monthly_driver=str(raw.get("monthly_driver", "")),
                    terminal_marker=str(raw.get("terminal_marker", "")),
                    terminal_date=str(raw.get("terminal_date", "")),
                    outcome_ideas=tuple(raw.get("outcome_ideas", [])),
                    expected_callers=expected_callers,
                    dependency_order=tuple(raw.get("dependency_order", [])),
                    localisation_prefixes=tuple(raw.get("localisation_prefixes", [])),
                    effect_preview_policy=str(
                        raw.get("effect_preview_policy", "engine_or_explicit")
                    ),
                    tooltip_exemptions={
                        str(option): str(reason)
                        for option, reason in raw.get("tooltip_exemptions", {}).items()
                    },
                    bridge_refresh_policy=str(raw.get("bridge_refresh_policy", "none")),
                    ai_bankruptcy_exceptions=tuple(
                        raw.get("ai_bankruptcy_exceptions", [])
                    ),
                    auxiliary_completion_markers=tuple(
                        raw.get("auxiliary_completion_markers", [])
                    ),
                    auxiliary_lifecycles=auxiliary_lifecycles,
                    allow_multiple_completion_producers=bool(
                        raw.get("allow_multiple_completion_producers", False)
                    ),
                )
            except (KeyError, TypeError, ValueError) as exc:
                self.add_error(
                    "Corporate-history manifest",
                    f"chains[{index}] is invalid: {exc}",
                )
                continue
            if chain.outcomes_only_strategy not in ("", "reconstruction", "suppressed"):
                self.add_error(
                    "Corporate-history manifest",
                    f"{chain.name} has invalid outcomes_only_strategy {chain.outcomes_only_strategy}",
                )
                continue
            if chain.requires_current_year_scheduler != (
                "current_year_scheduler" in chain.full_start_strategies
            ):
                self.add_error(
                    "Corporate-history manifest",
                    f"{chain.name} requires_current_year_scheduler disagrees with full_start_strategies",
                )
            chains.append(chain)
        return chains

    def _load_independent_subsystems(
        self, payload: Mapping[str, object], contract_version: int
    ) -> Tuple[IndependentSubsystemConfig, ...]:
        raw_subsystems = payload.get("independent_subsystems")
        if raw_subsystems is None and contract_version < 6:
            return ()
        if not isinstance(raw_subsystems, list) or not raw_subsystems:
            self.add_error(
                "Corporate-history manifest",
                "Schema v6 requires a non-empty independent_subsystems list",
            )
            return ()

        configs: List[IndependentSubsystemConfig] = []
        array_fields = (
            "namespaces",
            "event_ids",
            "owner_tags",
            "reconstruction_effects",
            "scheduler_entrypoints",
            "effect_roots",
        )
        for index, raw in enumerate(raw_subsystems):
            label = f"independent_subsystems[{index}]"
            if not isinstance(raw, dict):
                self.add_error(
                    "Corporate-history manifest", f"{label} must be an object"
                )
                continue
            actual_fields = set(raw)
            missing = sorted(_INDEPENDENT_SUBSYSTEM_FIELDS - actual_fields)
            extra = sorted(actual_fields - _INDEPENDENT_SUBSYSTEM_FIELDS)
            if missing or extra:
                details = []
                if missing:
                    details.append(f"missing required fields: {', '.join(missing)}")
                if extra:
                    details.append(f"has unsupported fields: {', '.join(extra)}")
                self.add_error(
                    "Corporate-history manifest", f"{label} {'; '.join(details)}"
                )
                continue
            if not all(
                isinstance(raw[field], list)
                and all(isinstance(value, str) and value for value in raw[field])
                for field in array_fields
            ):
                self.add_error(
                    "Corporate-history manifest",
                    f"{label} list fields must contain only non-empty strings",
                )
                continue
            subsystem_id = raw["id"]
            kind = raw["kind"]
            mode_policy = raw["mode_policy"]
            if not all(
                isinstance(value, str) and value
                for value in (subsystem_id, kind, mode_policy)
            ):
                self.add_error(
                    "Corporate-history manifest",
                    f"{label} id, kind, and mode_policy must be non-empty strings",
                )
                continue
            duplicate_fields = [
                field
                for field in array_fields
                if len(raw[field]) != len(set(raw[field]))
            ]
            if duplicate_fields:
                self.add_error(
                    "Corporate-history manifest",
                    f"{label} contains duplicate values in: {', '.join(duplicate_fields)}",
                )
                continue
            configs.append(
                IndependentSubsystemConfig(
                    subsystem_id=subsystem_id,
                    kind=kind,
                    namespaces=tuple(raw["namespaces"]),
                    event_ids=tuple(raw["event_ids"]),
                    owner_tags=tuple(raw["owner_tags"]),
                    reconstruction_effects=tuple(raw["reconstruction_effects"]),
                    scheduler_entrypoints=tuple(raw["scheduler_entrypoints"]),
                    effect_roots=tuple(raw["effect_roots"]),
                    mode_policy=mode_policy,
                )
            )
        return tuple(configs)

    def _validate_independent_subsystems(
        self,
        subsystems: Sequence[IndependentSubsystemConfig],
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
    ) -> List[Tuple[str, str, int]]:
        if int(self._manifest_payload.get("schema_version", 1)) < 6:
            return []

        findings: List[Tuple[str, str, int]] = []
        manifest = "tools/corporate_history_contract.json"
        expected_contracts = {
            "cross_tag_gpu_development": (
                "cross_tag_event_system",
                _INDEPENDENT_EVENT_POLICY,
            ),
            "israel_oem_historical_flavour": (
                "country_event_system",
                _INDEPENDENT_EVENT_POLICY,
            ),
            "legacy_usa_oem_storage_history": (
                "country_event_system",
                _INDEPENDENT_EVENT_POLICY,
            ),
            "physical_compute_stack": (
                "derived_aggregate",
                _INDEPENDENT_DERIVED_POLICY,
            ),
        }
        ids = [subsystem.subsystem_id for subsystem in subsystems]
        for subsystem_id in sorted(set(ids)):
            count = ids.count(subsystem_id)
            if count != 1:
                findings.append(
                    (
                        f"Independent subsystem id {subsystem_id} is declared {count} times",
                        manifest,
                        1,
                    )
                )
        missing_contracts = sorted(set(expected_contracts) - set(ids))
        unexpected_contracts = sorted(set(ids) - set(expected_contracts))
        if missing_contracts:
            findings.append(
                (
                    "Schema v6 is missing independent subsystems: "
                    + ", ".join(missing_contracts),
                    manifest,
                    1,
                )
            )
        if unexpected_contracts:
            findings.append(
                (
                    "Schema v6 has unexpected independent subsystems: "
                    + ", ".join(unexpected_contracts),
                    manifest,
                    1,
                )
            )

        namespace_owners: Dict[str, List[str]] = defaultdict(list)
        for chain in chains:
            namespace_owners[chain.namespace].append(f"chain:{chain.root}")
        raw_shared = self._manifest_payload.get("shared_systems", [])
        if isinstance(raw_shared, list):
            for index, raw_system in enumerate(raw_shared):
                if not isinstance(raw_system, dict):
                    continue
                namespace = raw_system.get("namespace")
                if isinstance(namespace, str) and namespace:
                    root = raw_system.get("root", index)
                    namespace_owners[namespace].append(f"shared:{root}")
        for subsystem in subsystems:
            for namespace in subsystem.namespaces:
                namespace_owners[namespace].append(
                    f"independent:{subsystem.subsystem_id}"
                )
        for namespace, owners in sorted(namespace_owners.items()):
            if len(owners) != 1:
                findings.append(
                    (
                        f"Namespace {namespace} requires exactly one contract owner; found {', '.join(owners)}",
                        manifest,
                        1,
                    )
                )

        event_owners: Dict[str, List[str]] = defaultdict(list)
        effect_root_owners: Dict[str, List[str]] = defaultdict(list)
        for subsystem in subsystems:
            expected = expected_contracts.get(subsystem.subsystem_id)
            if expected and (subsystem.kind, subsystem.mode_policy) != expected:
                findings.append(
                    (
                        f"{subsystem.subsystem_id} must use kind {expected[0]} and mode_policy {expected[1]}",
                        manifest,
                        1,
                    )
                )
            for event_id in subsystem.event_ids:
                event_owners[event_id].append(subsystem.subsystem_id)
            for effect_root in subsystem.effect_roots:
                effect_root_owners[effect_root].append(subsystem.subsystem_id)

            if subsystem.mode_policy == _INDEPENDENT_EVENT_POLICY:
                required_lists = {
                    "namespaces": subsystem.namespaces,
                    "event_ids": subsystem.event_ids,
                    "owner_tags": subsystem.owner_tags,
                    "reconstruction_effects": subsystem.reconstruction_effects,
                    "scheduler_entrypoints": subsystem.scheduler_entrypoints,
                    "effect_roots": subsystem.effect_roots,
                }
                empty = [name for name, values in required_lists.items() if not values]
                if empty:
                    findings.append(
                        (
                            f"{subsystem.subsystem_id} requires non-empty declarations for: {', '.join(empty)}",
                            manifest,
                            1,
                        )
                    )
                if (
                    subsystem.subsystem_id == "cross_tag_gpu_development"
                    and len(subsystem.effect_roots) != 1
                ):
                    findings.append(
                        (
                            f"{subsystem.subsystem_id} requires exactly one authoritative effect root; found {len(subsystem.effect_roots)}",
                            manifest,
                            1,
                        )
                    )
            elif subsystem.mode_policy == _INDEPENDENT_DERIVED_POLICY:
                nonempty = [
                    name
                    for name, values in (
                        ("namespaces", subsystem.namespaces),
                        ("event_ids", subsystem.event_ids),
                        ("reconstruction_effects", subsystem.reconstruction_effects),
                        ("scheduler_entrypoints", subsystem.scheduler_entrypoints),
                    )
                    if values
                ]
                if nonempty:
                    findings.append(
                        (
                            f"{subsystem.subsystem_id} is derived-only and must leave these declarations empty: {', '.join(nonempty)}",
                            manifest,
                            1,
                        )
                    )
                if not subsystem.owner_tags or len(subsystem.effect_roots) != 1:
                    findings.append(
                        (
                            f"{subsystem.subsystem_id} requires owner_tags and exactly one derived effect root",
                            manifest,
                            1,
                        )
                    )
            else:
                findings.append(
                    (
                        f"{subsystem.subsystem_id} has unsupported mode_policy {subsystem.mode_policy}",
                        manifest,
                        1,
                    )
                )

            invalid_tags = [
                tag
                for tag in subsystem.owner_tags
                if not re.fullmatch(r"[A-Z0-9]{3}", tag)
            ]
            if invalid_tags:
                findings.append(
                    (
                        f"{subsystem.subsystem_id} has invalid owner tags: {', '.join(invalid_tags)}",
                        manifest,
                        1,
                    )
                )
            wildcard_ids = [
                event_id
                for event_id in subsystem.event_ids
                if any(char in event_id for char in "*?[]")
            ]
            if wildcard_ids:
                findings.append(
                    (
                        f"{subsystem.subsystem_id} event_ids must be explicit: {', '.join(wildcard_ids)}",
                        manifest,
                        1,
                    )
                )
            wrong_namespace = [
                event_id
                for event_id in subsystem.event_ids
                if "." not in event_id
                or event_id.split(".", 1)[0] not in subsystem.namespaces
            ]
            if wrong_namespace:
                findings.append(
                    (
                        f"{subsystem.subsystem_id} has event IDs outside its namespaces: {', '.join(wrong_namespace)}",
                        manifest,
                        1,
                    )
                )

            declared = set(subsystem.event_ids)
            defined = {
                event_id
                for event_id in event_defs
                if "." in event_id and event_id.split(".", 1)[0] in subsystem.namespaces
            }
            missing_events = sorted(declared - set(event_defs))
            undeclared_events = sorted(defined - declared)
            if missing_events:
                findings.append(
                    (
                        f"{subsystem.subsystem_id} declares missing events: {', '.join(missing_events)}",
                        "events",
                        1,
                    )
                )
            if undeclared_events:
                findings.append(
                    (
                        f"{subsystem.subsystem_id} omits explicit namespace events: {', '.join(undeclared_events)}",
                        "events",
                        1,
                    )
                )

            for effect_name in (
                *subsystem.reconstruction_effects,
                *subsystem.scheduler_entrypoints,
                *subsystem.effect_roots,
            ):
                definitions = effect_defs.get(effect_name, [])
                if len(definitions) != 1:
                    findings.append(
                        (
                            f"{subsystem.subsystem_id} requires exactly one declared effect {effect_name}; found {len(definitions)}",
                            (
                                definitions[0].file
                                if definitions
                                else "common/scripted_effects"
                            ),
                            definitions[0].line if definitions else 1,
                        )
                    )

        for event_id, owners in sorted(event_owners.items()):
            if len(owners) != 1:
                findings.append(
                    (
                        f"Event {event_id} requires exactly one independent subsystem owner; found {', '.join(owners)}",
                        manifest,
                        1,
                    )
                )
        for effect_root, owners in sorted(effect_root_owners.items()):
            if len(owners) != 1:
                findings.append(
                    (
                        f"Effect root {effect_root} requires exactly one independent subsystem owner; found {', '.join(owners)}",
                        manifest,
                        1,
                    )
                )

        children = self._effect_call_children(effect_defs)
        scheduler_closures: Dict[str, Set[str]] = {}
        dispatch_closures: Dict[str, Set[str]] = {}
        root_closures: Dict[str, Set[str]] = {}
        for subsystem in subsystems:
            scheduler_closures[subsystem.subsystem_id] = self._effect_descendants(
                subsystem.scheduler_entrypoints, children
            )
            dispatch_closures[subsystem.subsystem_id] = {
                *scheduler_closures[subsystem.subsystem_id],
                *subsystem.effect_roots,
            }
            root_closures[subsystem.subsystem_id] = self._effect_descendants(
                (
                    *subsystem.effect_roots,
                    *subsystem.scheduler_entrypoints,
                    *subsystem.reconstruction_effects,
                ),
                children,
            )

        direct_calls = self._independent_event_call_sites(
            effect_defs, event_defs, set(event_owners)
        )
        scheduler_reachability = {
            subsystem.subsystem_id: self._independent_scheduler_reachability(
                dispatch_closures[subsystem.subsystem_id],
                effect_defs,
                event_defs,
                set(event_owners),
            )
            for subsystem in subsystems
        }
        scheduler_effects = {
            subsystem_id: reachable[0]
            for subsystem_id, reachable in scheduler_reachability.items()
        }
        scheduler_events = {
            subsystem_id: reachable[1]
            for subsystem_id, reachable in scheduler_reachability.items()
        }
        callerless_compatibility_anchors: Set[str] = set()
        for subsystem in subsystems:
            if subsystem.mode_policy != _INDEPENDENT_EVENT_POLICY:
                continue
            scheduler_closure = scheduler_effects[subsystem.subsystem_id]
            for event_id in subsystem.event_ids:
                sites = direct_calls.get(event_id, [])
                if not sites:
                    event = event_defs.get(event_id)
                    if (
                        event is not None
                        and event_id.endswith(".90")
                        and event.hidden
                        and re.search(r"\bis_triggered_only\s*=\s*yes\b", event.body)
                    ):
                        callerless_compatibility_anchors.add(event_id)
                        continue
                    findings.append(
                        (
                            f"{event_id} has no declared scheduler path",
                            event.file if event else "events",
                            event.line if event else 1,
                        )
                    )
                    continue
                owner_subsystems = {
                    owner.subsystem_id
                    for owner in subsystems
                    if event_id in scheduler_events.get(owner.subsystem_id, set())
                }
                bypasses = [
                    site
                    for site in sites
                    if (site.kind == "effect" and site.owner not in scheduler_closure)
                    or (
                        site.kind == "event"
                        and site.owner
                        not in scheduler_events.get(subsystem.subsystem_id, set())
                    )
                    or site.kind not in {"effect", "event"}
                ]
                if owner_subsystems != {subsystem.subsystem_id}:
                    rendered = ", ".join(sorted(owner_subsystems)) or "none"
                    event = event_defs.get(event_id)
                    findings.append(
                        (
                            f"{event_id} requires one declared scheduler owner {subsystem.subsystem_id}; found {rendered}",
                            event.file if event else "events",
                            event.line if event else 1,
                        )
                    )
                for bypass in bypasses:
                    findings.append(
                        (
                            f"{event_id} is dispatched outside {subsystem.subsystem_id} scheduler entrypoints by {bypass.owner}",
                            bypass.file,
                            bypass.line,
                        )
                    )

        (
            effect_modes,
            event_modes,
            effect_traces,
            event_traces,
        ) = self._independent_mode_graph(
            effect_defs,
            set(event_owners),
            direct_calls,
            event_defs_for_expansion=event_defs,
        )
        for subsystem in subsystems:
            closure = root_closures[subsystem.subsystem_id]
            findings.extend(
                self._independent_foreign_write_findings(
                    subsystem,
                    closure,
                    effect_defs,
                    event_defs,
                    set(event_owners),
                )
            )
            if subsystem.mode_policy == _INDEPENDENT_DERIVED_POLICY:
                called_events = sorted(
                    {
                        event_id
                        for effect_name in closure
                        for definition in effect_defs.get(effect_name, [])
                        for event_id, _line in self._find_event_calls(
                            definition.body, definition.line, frozenset()
                        )
                    }
                )
                if called_events:
                    findings.append(
                        (
                            f"{subsystem.subsystem_id} is derived-only but reaches events: {', '.join(called_events)}",
                            manifest,
                            1,
                        )
                    )
                continue

            for effect_root in subsystem.effect_roots:
                modes = effect_modes.get(effect_root, set())
                missing_modes = {"full", "outcomes_only"} - modes
                if missing_modes:
                    findings.append(
                        (
                            f"{effect_root} is not reachable from a monthly on_action in: {', '.join(sorted(missing_modes))}",
                            effect_defs.get(
                                effect_root,
                                [BlockDef(effect_root, "common/on_actions", 1, "")],
                            )[0].file,
                            1,
                        )
                    )
                traces = [
                    trace
                    for mode in _CORPORATE_MODES
                    for trace in effect_traces.get((effect_root, mode), [])
                ]
                hosts: Dict[str, Set[str]] = defaultdict(set)
                for trace in traces:
                    hosts[trace.host].add(trace.host_file)
                expected_hosts = {f"on_monthly_{tag}" for tag in subsystem.owner_tags}
                if set(hosts) != expected_hosts or any(
                    len(files) != 1 for files in hosts.values()
                ):
                    rendered = ", ".join(
                        f"{path}:{host}"
                        for host, paths in sorted(hosts.items())
                        for path in sorted(paths)
                    )
                    findings.append(
                        (
                            f"{effect_root} requires one authoritative tag-local monthly host per owner ({', '.join(sorted(expected_hosts))}); found {rendered or 'none'}",
                            traces[0].file if traces else "common/on_actions",
                            traces[0].line if traces else 1,
                        )
                    )
                for trace in traces:
                    if not trace.host.startswith("on_monthly"):
                        findings.append(
                            (
                                f"{effect_root} is reached from forbidden host {trace.host}",
                                trace.host_file,
                                trace.line,
                            )
                        )
                    if any(block == "ABK" for block in trace.block_path):
                        findings.append(
                            (
                                f"{effect_root} must not use ABK as a singleton host",
                                trace.host_file,
                                trace.line,
                            )
                        )

            for reconstruction in subsystem.reconstruction_effects:
                modes = effect_modes.get(reconstruction, set())
                if "outcomes_only" not in modes:
                    findings.append(
                        (
                            f"{reconstruction} is unreachable in outcomes_only",
                            effect_defs.get(
                                reconstruction,
                                [
                                    BlockDef(
                                        reconstruction, "common/scripted_effects", 1, ""
                                    )
                                ],
                            )[0].file,
                            1,
                        )
                    )
                if "off" in modes:
                    trace = effect_traces[(reconstruction, "off")][0]
                    findings.append(
                        (
                            f"{reconstruction} is reachable in Off mode",
                            trace.file,
                            trace.line,
                        )
                    )
            for scheduler in subsystem.scheduler_entrypoints:
                modes = effect_modes.get(scheduler, set())
                if "full" not in modes:
                    findings.append(
                        (
                            f"{scheduler} is unreachable in Full mode",
                            effect_defs.get(
                                scheduler,
                                [BlockDef(scheduler, "common/scripted_effects", 1, "")],
                            )[0].file,
                            1,
                        )
                    )
                for forbidden_mode in ("outcomes_only", "off"):
                    if forbidden_mode in modes:
                        trace = effect_traces[(scheduler, forbidden_mode)][0]
                        findings.append(
                            (
                                f"{scheduler} is reachable in {forbidden_mode} mode",
                                trace.file,
                                trace.line,
                            )
                        )
            for event_id in subsystem.event_ids:
                if event_id in callerless_compatibility_anchors:
                    continue
                modes = event_modes.get(event_id, set())
                if "full" not in modes:
                    event = event_defs.get(event_id)
                    findings.append(
                        (
                            f"{event_id} is unreachable in Full mode",
                            event.file if event else "events",
                            event.line if event else 1,
                        )
                    )
                for forbidden_mode in ("outcomes_only", "off"):
                    if forbidden_mode in modes:
                        trace = event_traces[(event_id, forbidden_mode)][0]
                        findings.append(
                            (
                                f"{event_id} is reachable in {forbidden_mode} mode",
                                trace.file,
                                trace.line,
                            )
                        )
        return self._dedupe_findings(findings)

    def _effect_descendants(
        self, roots: Iterable[str], children: Mapping[str, Sequence[str]]
    ) -> Set[str]:
        reachable: Set[str] = set()
        pending = list(roots)
        while pending:
            effect_name = pending.pop()
            if effect_name in reachable:
                continue
            reachable.add(effect_name)
            pending.extend(children.get(effect_name, ()))
        return reachable

    def _independent_foreign_write_findings(
        self,
        subsystem: IndependentSubsystemConfig,
        reachable_effects: Set[str],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Mapping[str, EventDef],
        declared_event_ids: Set[str],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        owned_events = [
            event_defs[event_id]
            for event_id in subsystem.event_ids
            if event_id in event_defs
        ]
        event_effect_roots = {
            match.group(1)
            for event in owned_events
            for match in _EFFECT_YES_RE.finditer(event.body)
            if match.group(1) in effect_defs
        }
        expanded_effects = set(reachable_effects)
        expanded_effects.update(
            self._effect_descendants(
                event_effect_roots, self._effect_call_children(effect_defs)
            )
        )

        def foreign_tokens(body: str) -> List[str]:
            prefixes = tuple(
                sorted(
                    {
                        f"{match.group(1)}_"
                        for match in re.finditer(
                            r"\b([A-Z][A-Z0-9]{2})_[A-Za-z0-9_]+", body
                        )
                    }
                )
            )
            if not prefixes:
                return []
            return [
                token
                for token in sorted(_collect_native_write_tokens(body, prefixes))
                if token not in declared_event_ids
                and (tag_match := re.match(r"([A-Z][A-Z0-9]{2})_", token))
                and tag_match.group(1) not in subsystem.owner_tags
            ]

        for effect_name in expanded_effects:
            for definition in effect_defs.get(effect_name, []):
                for token in foreign_tokens(definition.body):
                    findings.append(
                        (
                            f"{subsystem.subsystem_id} reaches foreign-owner write {token} through {effect_name}",
                            definition.file,
                            definition.line,
                        )
                    )
        for event in owned_events:
            for token in foreign_tokens(event.body):
                findings.append(
                    (
                        f"{subsystem.subsystem_id} event {event.event_id} writes foreign-owner state {token}",
                        event.file,
                        event.line,
                    )
                )
        return findings

    def _validate_economic_layers(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        chains: Sequence[ChainConfig],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        schema_version = int(self._manifest_payload.get("schema_version", 1))
        raw_layers = self._manifest_payload.get("economic_layers")
        if raw_layers is None and schema_version < 3:
            return findings
        if not isinstance(raw_layers, list) or not raw_layers:
            return [
                (
                    "Schema v3 requires a non-empty economic_layers list",
                    "tools/corporate_history_contract.json",
                    1,
                )
            ]

        required_fields = (
            "name",
            "tag",
            "updater",
            "bridge",
            "effect_file",
            "dynamic_modifier_file",
            "decision_file",
            "idea_file",
            "scripted_localisation_file",
            "localisation_file",
            "initialized_flag",
            "variables",
            "source_variables",
            "cdf",
            "modifier_families",
            "policy_programs",
            "dashboard_variables",
            "scripted_localisation",
            "localisation_keys",
        )

        chain_variables = {variable for chain in chains for variable in chain.variables}
        for index, raw_layer in enumerate(raw_layers):
            if not isinstance(raw_layer, dict):
                findings.append(
                    (
                        f"economic_layers[{index}] must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue
            missing = [field for field in required_fields if field not in raw_layer]
            if missing:
                findings.append(
                    (
                        f"economic_layers[{index}] is missing required fields: {', '.join(missing)}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            layer_name = str(raw_layer["name"])

            def read_layer_file(field: str) -> Tuple[str, str]:
                relative = str(raw_layer[field])
                path = self._root / relative
                try:
                    return relative, path.read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                except OSError:
                    findings.append(
                        (f"{layer_name} is missing {field} {relative}", relative, 1)
                    )
                    return relative, ""

            effect_file, effect_text_raw = read_layer_file("effect_file")
            dynamic_file, dynamic_text_raw = read_layer_file("dynamic_modifier_file")
            decision_file, decision_text_raw = read_layer_file("decision_file")
            idea_file, idea_text_raw = read_layer_file("idea_file")
            scripted_loc_file, scripted_loc_text_raw = read_layer_file(
                "scripted_localisation_file"
            )
            localisation_file, localisation_text = read_layer_file("localisation_file")
            effect_text = strip_comments(effect_text_raw)
            dynamic_text = strip_comments(dynamic_text_raw)
            decision_text = strip_comments(decision_text_raw)
            idea_text = strip_comments(idea_text_raw)
            scripted_loc_text = strip_comments(scripted_loc_text_raw)

            updater = str(raw_layer["updater"])
            bridge = str(raw_layer["bridge"])
            updater_defs = effect_defs.get(updater, [])
            if len(updater_defs) != 1:
                findings.append(
                    (
                        f"{layer_name} requires exactly one authoritative updater {updater}; found {len(updater_defs)}",
                        effect_file,
                        1,
                    )
                )
                updater_body = effect_text
            else:
                updater_body = updater_defs[0].body
                if updater_defs[0].file.replace("\\", "/") != effect_file.replace(
                    "\\", "/"
                ):
                    findings.append(
                        (
                            f"{updater} must be defined in {effect_file}",
                            updater_defs[0].file,
                            updater_defs[0].line,
                        )
                    )

            bridge_defs = effect_defs.get(bridge, [])
            if len(bridge_defs) != 1:
                findings.append(
                    (
                        f"{layer_name} bridge {bridge} must have exactly one definition",
                        effect_file,
                        1,
                    )
                )
            else:
                calls = len(
                    re.findall(
                        rf"\b{re.escape(updater)}\s*=\s*yes\b", bridge_defs[0].body
                    )
                )
                if calls != 1:
                    findings.append(
                        (
                            f"{bridge} must call {updater} exactly once; found {calls}",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )

            for token in ("ln", "log", "sqrt", "exp", "pow"):
                if re.search(rf"\b{token}\s*=", effect_text):
                    findings.append(
                        (
                            f"{layer_name} uses unsupported scripted math operator {token}",
                            effect_file,
                            1,
                        )
                    )
            for forbidden_gate in (
                "corporate_history_full_enabled",
                "corporate_history_outcomes_only_enabled",
            ):
                if forbidden_gate in updater_body:
                    findings.append(
                        (
                            f"{updater} must be mode-neutral and cannot read {forbidden_gate}",
                            effect_file,
                            1,
                        )
                    )
            for required_gate in (
                "corporate_history_enabled",
                "collapsed_nation",
                str(raw_layer["initialized_flag"]),
            ):
                if required_gate not in updater_body:
                    findings.append(
                        (
                            f"{updater} is missing required gate or cleanup symbol {required_gate}",
                            effect_file,
                            1,
                        )
                    )
            if "force_update_dynamic_modifier" in effect_text:
                findings.append(
                    (
                        f"{layer_name} must not force-update dynamic modifiers",
                        effect_file,
                        1,
                    )
                )

            daily_files = []
            for filepath in self._collect_text_files(["common/on_actions/**/*.txt"]):
                try:
                    on_action_text = Path(filepath).read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                except OSError:
                    continue
                if updater in strip_comments(on_action_text):
                    daily_files.append(self._relpath(filepath))
            for daily_file in daily_files:
                findings.append(
                    (
                        f"{updater} must be reached through the economic bridge, not an on-action",
                        daily_file,
                        1,
                    )
                )

            raw_variables = raw_layer["variables"]
            declared_variables: Set[str] = set()
            if not isinstance(raw_variables, dict) or not raw_variables:
                findings.append(
                    (
                        f"{layer_name} requires declared bounded variables",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                raw_variables = {}
            script_clamps = {
                match.group(1): (Decimal(match.group(2)), Decimal(match.group(3)))
                for match in _CLAMP_VAR_RE.finditer(effect_text)
            }
            for variable, raw_bound in raw_variables.items():
                declared_variables.add(str(variable))
                try:
                    expected = (
                        Decimal(str(raw_bound["min"])),
                        Decimal(str(raw_bound["max"])),
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    findings.append(
                        (
                            f"{layer_name} has invalid bounds for {variable}: {exc}",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                if script_clamps.get(str(variable)) != expected:
                    findings.append(
                        (
                            f"{updater} must clamp {variable} to economic-layer bounds {expected[0]}..{expected[1]}",
                            effect_file,
                            1,
                        )
                    )
                if not re.search(
                    rf"\bclear_variable\s*=\s*{re.escape(str(variable))}\b",
                    updater_body,
                ):
                    findings.append(
                        (
                            f"{updater} Off cleanup must clear {variable}",
                            effect_file,
                            1,
                        )
                    )

            for match in _SET_VAR_RE.finditer(effect_text):
                variable = match.group(1)
                if variable in chain_variables:
                    findings.append(
                        (
                            f"{layer_name} writes company-owned variable {variable}",
                            effect_file,
                            self._line(effect_text, match.start()),
                        )
                    )
                elif (
                    variable.startswith("USA_oem_")
                    and variable not in declared_variables
                    and not variable.endswith("_display")
                ):
                    findings.append(
                        (
                            f"{layer_name} writes undeclared persistent variable {variable}",
                            effect_file,
                            self._line(effect_text, match.start()),
                        )
                    )

            for source_variable in raw_layer["source_variables"]:
                if not re.search(
                    rf"\b{re.escape(str(source_variable))}\b", updater_body
                ):
                    findings.append(
                        (
                            f"{updater} does not read declared source variable {source_variable}",
                            effect_file,
                            1,
                        )
                    )

            cdf = raw_layer["cdf"]
            if not isinstance(cdf, dict):
                findings.append(
                    (
                        f"{layer_name} CDF contract must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                knots = cdf.get("knots", [])
                values = cdf.get("values", [])
                cdf_lists = isinstance(knots, list) and isinstance(values, list)
                cdf_numeric = cdf_lists and all(
                    _is_finite_number(value) for value in (*knots, *values)
                )
                if cdf_lists and not cdf_numeric:
                    findings.append(
                        (
                            f"{layer_name} CDF knots and values must contain only finite numbers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                if not cdf_lists or (
                    cdf_numeric
                    and (
                        len(knots) != len(values)
                        or len(knots) < 2
                        or any(left >= right for left, right in zip(knots, knots[1:]))
                        or any(left >= right for left, right in zip(values, values[1:]))
                        or any(value < 0 or value > 1 for value in values)
                    )
                ):
                    findings.append(
                        (
                            f"{layer_name} CDF knots and values must be paired, monotonic, and bounded",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                if cdf_numeric:
                    for value in values:
                        if str(value) not in effect_text:
                            findings.append(
                                (
                                    f"{layer_name} CDF script is missing contracted value {value}",
                                    effect_file,
                                    1,
                                )
                            )
                if not re.search(
                    r"clamp_temp_variable\s*=\s*\{\s*var\s*=\s*USA_oem_cdf_output\s+min\s*=\s*0\s+max\s*=\s*1",
                    effect_text,
                ):
                    findings.append(
                        (
                            f"{layer_name} CDF output must clamp to 0..1",
                            effect_file,
                            1,
                        )
                    )

            all_modifier_members: List[str] = []
            families = raw_layer["modifier_families"]
            if not isinstance(families, list) or not families:
                findings.append(
                    (
                        f"{layer_name} requires modifier families",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                families = []
            for family in families:
                if not isinstance(family, dict):
                    continue
                family_name = str(family.get("name", "unnamed"))
                members = family.get("members", [])
                thresholds = family.get("thresholds", [])
                score = str(family.get("score", ""))
                if isinstance(thresholds, list) and not all(
                    _is_finite_number(threshold) for threshold in thresholds
                ):
                    findings.append(
                        (
                            f"{layer_name} modifier family {family_name} thresholds must contain only finite numbers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                if (
                    not isinstance(members, list)
                    or not isinstance(thresholds, list)
                    or len(members) != len(thresholds) + 1
                    or any(
                        left >= right for left, right in zip(thresholds, thresholds[1:])
                    )
                ):
                    findings.append(
                        (
                            f"{layer_name} modifier family {family_name} has invalid members or thresholds",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                if score not in declared_variables:
                    findings.append(
                        (
                            f"{layer_name} modifier family {family_name} reads undeclared score {score}",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                for threshold in thresholds:
                    threshold_text = str(threshold)
                    if not re.search(
                        rf"check_variable\s*=\s*\{{\s*{re.escape(score)}\s*<\s*{re.escape(threshold_text)}\s*\}}",
                        updater_body,
                    ):
                        findings.append(
                            (
                                f"{layer_name} modifier family {family_name} is missing threshold {threshold_text} for {score}",
                                effect_file,
                                1,
                            )
                        )
                for member in members:
                    member = str(member)
                    all_modifier_members.append(member)
                    definitions = len(
                        re.findall(rf"(?m)^{re.escape(member)}\s*=\s*\{{", dynamic_text)
                    )
                    if definitions != 1:
                        findings.append(
                            (
                                f"Dynamic modifier {member} must be defined exactly once; found {definitions}",
                                dynamic_file,
                                1,
                            )
                        )
                    if not re.search(
                        rf"\badd_dynamic_modifier\s*=\s*\{{\s*modifier\s*=\s*{re.escape(member)}\b",
                        updater_body,
                    ):
                        findings.append(
                            (
                                f"{updater} never assigns dynamic modifier {member}",
                                effect_file,
                                1,
                            )
                        )
                    remove_count = len(
                        re.findall(
                            rf"\bremove_dynamic_modifier\s*=\s*\{{\s*modifier\s*=\s*{re.escape(member)}\b",
                            updater_body,
                        )
                    )
                    if remove_count < len(members) + 1:
                        findings.append(
                            (
                                f"{updater} must clear {member} in every {family_name} tier branch and Off cleanup",
                                effect_file,
                                1,
                            )
                        )
                    if not re.search(
                        rf"\bremove_dynamic_modifier\s*=\s*\{{\s*modifier\s*=\s*{re.escape(member)}\b",
                        updater_body,
                    ):
                        findings.append(
                            (
                                f"{updater} never clears dynamic modifier {member}",
                                effect_file,
                                1,
                            )
                        )

            programs = raw_layer["policy_programs"]
            if not isinstance(programs, list) or len(programs) != 4:
                findings.append(
                    (
                        f"{layer_name} requires exactly four policy programs",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                programs = []
            program_ideas: List[str] = []
            for program_index, program in enumerate(programs):
                if not isinstance(program, dict):
                    findings.append(
                        (
                            f"{layer_name} policy_programs[{program_index}] must be an object",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                decision = str(program.get("decision", ""))
                idea = str(program.get("idea", ""))
                days = int(program.get("days", 0))
                cooldown_days = int(program.get("cooldown_days", 0))
                program_ideas.append(idea)
                findings.extend(
                    _program_lifecycle_findings(
                        decision,
                        program,
                        "days",
                        "concurrent",
                        "tools/corporate_history_contract.json",
                    )
                )
                if str(program.get("cleanup_owner", "")) != updater:
                    findings.append(
                        (
                            f"{decision} must declare {updater} as its cleanup owner",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                decision_match = re.search(
                    rf"(?m)^\s*{re.escape(decision)}\s*=\s*\{{", decision_text
                )
                if decision_match is None:
                    findings.append(
                        (f"Missing policy decision {decision}", decision_file, 1)
                    )
                    continue
                decision_body, end = extract_block_from_text(
                    decision_text, decision_match.end() - 1
                )
                if end == -1:
                    findings.append(
                        (
                            f"Could not parse policy decision {decision}",
                            decision_file,
                            1,
                        )
                    )
                    continue
                available_match = re.search(r"\bavailable\s*=\s*\{", decision_body)
                available_body = ""
                if available_match is not None:
                    available_body, _ = extract_block_from_text(
                        decision_body, available_match.end() - 1
                    )
                timed_pattern = re.compile(
                    rf"\badd_timed_idea\s*=\s*\{{\s*idea\s*=\s*{re.escape(idea)}\s+days\s*=\s*{days}\s*\}}"
                )
                if len(timed_pattern.findall(decision_body)) != 1:
                    findings.append(
                        (
                            f"{decision} must add {idea} once for {days} days",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                cooldown_pattern = re.compile(
                    rf"\bdays_re_enable\s*=\s*{cooldown_days}\b"
                )
                if len(cooldown_pattern.findall(decision_body)) != 1:
                    findings.append(
                        (
                            f"{decision} must declare a {cooldown_days}-day cooldown",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                if not _is_repeatable_decision(decision_body):
                    findings.append(
                        (
                            f"{decision} must remain reusable after its declared cooldown",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                if str(program.get("refresh_policy")) != "block_while_active":
                    findings.append(
                        (
                            f"{decision} must declare block_while_active refresh policy",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                if not re.search(
                    rf"NOT\s*=\s*\{{\s*has_idea\s*=\s*{re.escape(idea)}\s*\}}",
                    available_body,
                ):
                    findings.append(
                        (
                            f"{decision} must block while {idea} is active",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                if not re.search(
                    r"NOT\s*=\s*\{\s*has_country_flag\s*=\s*collapsed_nation\s*\}",
                    available_body,
                ):
                    findings.append(
                        (
                            f"{decision} must be unavailable after national collapse",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                definitions = len(
                    re.findall(rf"(?m)^\s*{re.escape(idea)}\s*=\s*\{{", idea_text)
                )
                if definitions != 1:
                    findings.append(
                        (
                            f"Policy idea {idea} must be defined exactly once; found {definitions}",
                            idea_file,
                            1,
                        )
                    )
                if not re.search(
                    rf"\bremove_ideas\s*=\s*\{{[^}}]*\b{re.escape(idea)}\b",
                    updater_body,
                    re.DOTALL,
                ):
                    findings.append(
                        (
                            f"{updater} Off/collapse cleanup must remove {idea}",
                            effect_file,
                            1,
                        )
                    )

            dashboard_text = decision_text + "\n" + localisation_text
            for variable in raw_layer["dashboard_variables"]:
                if str(variable) not in dashboard_text:
                    findings.append(
                        (
                            f"{layer_name} dashboard does not read authoritative output {variable}",
                            localisation_file,
                            1,
                        )
                    )
            for name in raw_layer["scripted_localisation"]:
                if not re.search(
                    rf"\bname\s*=\s*{re.escape(str(name))}\b", scripted_loc_text
                ):
                    findings.append(
                        (
                            f"Missing scripted localisation {name}",
                            scripted_loc_file,
                            1,
                        )
                    )

            localisation_keys = set(raw_layer["localisation_keys"])
            localisation_keys.update(program_ideas)
            localisation_keys.update(f"{idea}_desc" for idea in program_ideas)
            localisation_keys.update(all_modifier_members)
            localisation_keys.update(
                f"{member}_desc" for member in all_modifier_members
            )
            defined_loc_keys = {
                match.group(1)
                for line in localisation_text.splitlines()
                if (match := _LOC_KEY_PREFIX_RE.match(line))
            }
            for key in sorted(localisation_keys):
                if key not in defined_loc_keys:
                    findings.append(
                        (
                            f"Missing English real-options localisation key {key}",
                            localisation_file,
                            1,
                        )
                    )

            try:
                localisation_bytes = (self._root / localisation_file).read_bytes()
            except OSError:
                localisation_bytes = b""
            if localisation_bytes and not localisation_bytes.startswith(
                b"\xef\xbb\xbf"
            ):
                findings.append(
                    (
                        f"{localisation_file} must retain its UTF-8 BOM",
                        localisation_file,
                        1,
                    )
                )

        return findings

    def _discover_core_namespaces(
        self,
        startup_defs: Sequence[BlockDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> Set[str]:
        namespaces: Set[str] = set()
        for defs in effect_defs.values():
            for effect in defs:
                if effect.name.endswith("_corporate_trigger_year_2001") or (
                    "_corporate_trigger_year_" in effect.name
                ):
                    namespaces.update(self._event_namespaces_in_text(effect.body))
        for startup in startup_defs:
            namespaces.update(self._event_namespaces_in_text(startup.body))
        return namespaces

    def _validate_manifest_coverage(
        self,
        chains: Sequence[ChainConfig],
        core_namespaces: Set[str],
        chain_by_namespace: Dict[str, ChainConfig],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        for identity_field, values in (
            ("name", [chain.name for chain in chains]),
            ("namespace", [chain.namespace for chain in chains]),
            ("root", [chain.root for chain in chains]),
        ):
            for value in sorted(set(values)):
                count = values.count(value)
                if count > 1:
                    findings.append(
                        (
                            f"Manifest {identity_field} {value} is declared {count} times",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
        root_values = [chain.root for chain in chains]
        auxiliary_roots = [
            lifecycle.root
            for chain in chains
            for lifecycle in chain.auxiliary_lifecycles
        ]
        for root in sorted(set(auxiliary_roots)):
            count = auxiliary_roots.count(root)
            if root in root_values or count != 1:
                findings.append(
                    (
                        f"Auxiliary lifecycle root {root} must be unique; found {count + root_values.count(root)} declarations",
                        "tools/corporate_history_contract.json",
                        0,
                    )
                )
        for chain in chains:
            if len(chain.dependency_order) != len(set(chain.dependency_order)):
                findings.append(
                    (
                        f"{chain.name} dependency_order contains duplicate roots",
                        "tools/corporate_history_contract.json",
                        0,
                    )
                )
            for dependency in chain.dependency_order:
                count = root_values.count(dependency)
                if dependency == chain.root:
                    findings.append(
                        (
                            f"{chain.name} cannot depend on its own root {dependency}",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
                elif count != 1:
                    findings.append(
                        (
                            f"{chain.name} dependency {dependency} must match exactly one manifest root; found {count}",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
            declared_auxiliary_markers = {
                lifecycle.terminal_marker for lifecycle in chain.auxiliary_lifecycles
            }
            if declared_auxiliary_markers != set(chain.auxiliary_completion_markers):
                findings.append(
                    (
                        f"{chain.name} auxiliary lifecycle markers differ from auxiliary_completion_markers",
                        "tools/corporate_history_contract.json",
                        0,
                    )
                )
        for namespace in sorted(core_namespaces):
            if namespace not in chain_by_namespace:
                findings.append(
                    (f"Unregistered corporate-history namespace {namespace}", "", 0)
                )
        return findings

    def _validate_cross_chain_ownership(
        self,
        chains: Sequence[ChainConfig],
        chain_by_root: Dict[str, ChainConfig],
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        del chain_by_root
        findings = []
        ownership_patterns: List[Tuple[ChainConfig, str, re.Pattern[str]]] = []
        for chain in chains:
            for prefix in chain.owned_prefixes:
                ownership_patterns.append(
                    (
                        chain,
                        prefix,
                        re.compile(r"\b" + re.escape(prefix) + r"[A-Za-z0-9_]*\b"),
                    )
                )

        for chain in chains:
            for event in event_defs.values():
                if not event.event_id.startswith(chain.namespace + "."):
                    continue
                findings.extend(
                    self._cross_chain_findings_in_text(
                        chain,
                        event.body,
                        event.file,
                        event.line,
                        ownership_patterns,
                    )
                )
            for name, definitions in effect_defs.items():
                if not name.startswith(chain.root):
                    continue
                for definition in definitions:
                    findings.extend(
                        self._cross_chain_findings_in_text(
                            chain,
                            definition.body,
                            definition.file,
                            definition.line,
                            ownership_patterns,
                        )
                    )
        return self._dedupe_findings(findings)

    def _cross_chain_findings_in_text(
        self,
        chain: ChainConfig,
        text: str,
        rel: str,
        base_line: int,
        ownership_patterns: Sequence[Tuple[ChainConfig, str, re.Pattern[str]]],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        stack: List[str] = []
        for offset, raw_line in enumerate(text.splitlines()):
            line_no = base_line + offset
            code = blank_quoted_strings(raw_line)
            headers = re.findall(r"(" + _BLOCK_IDENTIFIER + r")\s*=\s*\{", code)
            stack.extend(headers)
            tokens: List[Tuple[ChainConfig, str]] = []
            seen_tokens: Set[Tuple[str, str]] = set()
            for owner, _prefix, pattern in ownership_patterns:
                if owner is chain:
                    continue
                for token in pattern.findall(code):
                    key = (owner.root, token)
                    if key not in seen_tokens:
                        seen_tokens.add(key)
                        tokens.append((owner, token))
            for owner, token in sorted(tokens, key=lambda item: item[1]):
                if self._line_is_cross_write(code, owner, stack):
                    if not self._is_allowed(token, chain.allowed_writes):
                        findings.append(
                            (
                                f"{chain.name} writes {token}, owned by {owner.name}, outside declared exceptions",
                                rel,
                                line_no,
                            )
                        )
                elif self._line_is_cross_read(code, stack):
                    if not self._is_allowed(token, chain.allowed_reads):
                        label = (
                            "read-only AI/flavour use"
                            if any(ctx in ("ai_chance", "trigger") for ctx in stack)
                            else "read"
                        )
                        findings.append(
                            (
                                f"{chain.name} has undeclared cross-chain {label} of {token}, owned by {owner.name}",
                                rel,
                                line_no,
                            )
                        )
            closes = code.count("}")
            while closes > 0 and stack:
                stack.pop()
                closes -= 1
        return findings

    def _validate_localisation_contract(
        self, chains: Sequence[ChainConfig], event_defs: Dict[str, EventDef]
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        all_key_locations: Dict[str, List[Tuple[str, int]]] = {}
        scoped_key_locations: Dict[str, List[Tuple[str, int]]] = {}
        prefixes = tuple(
            prefix
            for chain in chains
            for prefix in (chain.localisation_prefixes or (chain.namespace, chain.root))
        )
        for filepath in self._collect_text_files(["localisation/english/**/*.yml"]):
            path = Path(filepath)
            try:
                raw = path.read_bytes()
                text = raw.decode("utf-8-sig")
            except (OSError, UnicodeDecodeError):
                continue
            rel = self._relpath(path)
            file_has_scoped_key = False
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = _LOC_KEY_PREFIX_RE.match(line)
                if not match:
                    continue
                key = match.group(1)
                is_scoped = key.startswith(prefixes)
                if not _VALID_LOC_VALUE_RE.match(line):
                    if is_scoped:
                        file_has_scoped_key = True
                        findings.append(
                            (
                                f"Malformed English corporate-history localisation value {key}",
                                rel,
                                line_no,
                            )
                        )
                    continue
                all_key_locations.setdefault(key, []).append((rel, line_no))
                if not is_scoped:
                    continue
                file_has_scoped_key = True
                scoped_key_locations.setdefault(key, []).append((rel, line_no))
            if file_has_scoped_key:
                if not raw.startswith(b"\xef\xbb\xbf"):
                    findings.append(
                        ("English OEM localisation file is missing a UTF-8 BOM", rel, 1)
                    )

        for key, locations in sorted(scoped_key_locations.items()):
            if len(locations) > 1:
                findings.append(
                    (
                        f"English OEM localisation key {key} is defined {len(locations)} times",
                        locations[0][0],
                        locations[0][1],
                    )
                )

        for chain in chains:
            seen_option_keys: Set[str] = set()
            chain_events = [
                event
                for event_id, event in event_defs.items()
                if event_id.startswith(chain.namespace + ".") and not event.hidden
            ]
            for event in chain_events:
                referenced = []
                for pattern in (
                    r"\btitle\s*=\s*([A-Za-z0-9_.-]+)",
                    r"\bdesc\s*=\s*([A-Za-z0-9_.-]+)",
                    r"\btext\s*=\s*([A-Za-z0-9_.-]+)",
                ):
                    referenced.extend(re.findall(pattern, event.body))
                for option in event.options:
                    name_match = re.search(
                        r"\bname\s*=\s*([A-Za-z0-9_.-]+)", option.body
                    )
                    if not name_match:
                        continue
                    option_key = name_match.group(1)
                    seen_option_keys.add(option_key)
                    referenced.append(option_key)
                    tooltip_keys = re.findall(
                        r"\b(?:custom_effect_tooltip|tooltip)\s*=\s*([A-Za-z0-9_.-]+)",
                        option.body,
                    )
                    referenced.extend(tooltip_keys)
                    if (
                        chain.effect_preview_policy == "explicit"
                        and self._option_has_mechanical_effect(option.body, chain)
                        and f"{option_key}_tt" not in tooltip_keys
                        and option_key not in chain.tooltip_exemptions
                    ):
                        findings.append(
                            (
                                f"{option_key} requires exact custom_effect_tooltip = {option_key}_tt",
                                option.file,
                                option.line,
                            )
                        )
                for key in referenced:
                    if key not in all_key_locations:
                        findings.append(
                            (
                                f"Missing English corporate-history localisation key {key}",
                                event.file,
                                event.line,
                            )
                        )
            for idea_id in chain.outcome_ideas:
                for key in (idea_id, f"{idea_id}_desc"):
                    if key not in all_key_locations:
                        findings.append(
                            (
                                f"Missing English outcome localisation key {key}",
                                "localisation/english",
                                0,
                            )
                        )
            for option_key, reason in chain.tooltip_exemptions.items():
                if not reason.strip():
                    findings.append(
                        (
                            f"Tooltip exemption {option_key} requires a reason",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
                if option_key not in seen_option_keys:
                    findings.append(
                        (
                            f"Tooltip exemption {option_key} does not match a visible option in {chain.namespace}",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
        return self._dedupe_findings(findings)

    def _option_has_mechanical_effect(self, body: str, chain: ChainConfig) -> bool:
        if any(
            token in body
            for token in (
                "modify_treasury_effect",
                "add_political_power",
                "add_stability",
                "add_war_support",
                "add_ideas",
                "remove_ideas",
                "add_tech_bonus",
                "add_research_slot",
            )
        ):
            return True
        return any(variable in body for variable in chain.variables)

    def _validate_economic_bridge(
        self,
        chains: Sequence[ChainConfig],
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        immediate_chains = [
            chain for chain in chains if chain.bridge_refresh_policy == "immediate"
        ]
        if not immediate_chains:
            return []
        findings: List[Tuple[str, str, int]] = []
        update_defs = effect_defs.get(
            "USA_corporate_systems_update_economic_bridge", []
        )
        clear_defs = effect_defs.get(
            "USA_corporate_systems_clear_economic_bridge_ideas", []
        )
        rebuild_defs = effect_defs.get(
            "USA_corporate_systems_rebuild_company_contributions", []
        )
        if len(update_defs) != 1 or len(clear_defs) != 1 or len(rebuild_defs) != 1:
            return [
                (
                    "USA economic bridge requires exactly one update, clear, and contribution rebuild effect",
                    "common/scripted_effects/USA_corporate_systems_effects.txt",
                    0,
                )
            ]

        update = update_defs[0]
        thresholds = [
            int(value)
            for value in re.findall(
                r"USA_corporate_systems_economic_integration_score\s*<\s*(\d+)",
                update.body,
            )
        ]
        if thresholds != [15, 22, 29, 38]:
            findings.append(
                (
                    f"USA economic bridge thresholds must be 15, 22, 29, 38; found {thresholds}",
                    update.file,
                    update.line,
                )
            )
        expected_ideas = {
            f"USA_corporate_systems_economic_integration_{level}"
            for level in range(1, 6)
        }
        if set(_ADD_IDEA_RE.findall(update.body)) != expected_ideas:
            findings.append(
                (
                    "USA economic bridge update must select each of its five tier ideas",
                    update.file,
                    update.line,
                )
            )
        clear = clear_defs[0]
        if not all(idea in clear.body for idea in expected_ideas):
            findings.append(
                (
                    "USA economic bridge cleanup must remove all five tier ideas",
                    clear.file,
                    clear.line,
                )
            )
        if "corporate_history_enabled = yes" not in update.body or not all(
            marker in update.body
            for marker in (
                "USA_corporate_systems_clear_derived_axes = yes",
                "USA_corporate_systems_clear_economic_bridge_ideas = yes",
            )
        ):
            findings.append(
                (
                    "USA economic bridge must clear derived axes and tier ideas when corporate history is Off",
                    update.file,
                    update.line,
                )
            )

        contribution_axes = (
            "open_standards",
            "vertical_integration",
            "supply_resilience",
            "security_control",
            "national_compute_stack",
        )
        contribution_body = rebuild_defs[0].body
        for axis in contribution_axes:
            variable = f"USA_oem_contribution_{axis}"
            if not re.search(
                rf"\bset_temp_variable\s*=\s*\{{\s*{variable}\s*=\s*0\s*\}}",
                contribution_body,
            ):
                findings.append(
                    (
                        f"USA economic bridge must reset {variable} before accumulation",
                        rebuild_defs[0].file,
                        rebuild_defs[0].line,
                    )
                )
            if not re.search(
                rf"\bclamp_temp_variable\s*=\s*\{{\s*var\s*=\s*{variable}\s+min\s*=\s*-3\s+max\s*=\s*3\s*\}}",
                contribution_body,
            ):
                findings.append(
                    (
                        f"USA economic bridge must clamp {variable} to -3..3",
                        rebuild_defs[0].file,
                        rebuild_defs[0].line,
                    )
                )

        effective_defs = effect_defs.get(
            "USA_corporate_systems_rebuild_effective_axes", []
        )
        if len(effective_defs) != 1:
            findings.append(
                (
                    "USA economic bridge requires exactly one effective-axis rebuild effect",
                    "common/scripted_effects/USA_corporate_systems_effects.txt",
                    0,
                )
            )
        else:
            for axis in contribution_axes:
                variable = f"USA_oem_effective_{axis}"
                if not re.search(
                    rf"\bclamp_variable\s*=\s*\{{\s*var\s*=\s*{variable}\s+min\s*=\s*0\s+max\s*=\s*10\s*\}}",
                    effective_defs[0].body,
                ):
                    findings.append(
                        (
                            f"USA economic bridge must clamp {variable} to 0..10",
                            effective_defs[0].file,
                            effective_defs[0].line,
                        )
                    )

        effect_lookup = {name: defs[0] for name, defs in effect_defs.items() if defs}
        for chain in immediate_chains:
            company = chain.root.split("_", 1)[-1]
            contribution_name = f"USA_corporate_systems_{company}_contribution"
            contribution = effect_lookup.get(contribution_name)
            if contribution is None:
                findings.append(
                    (
                        f"{chain.name} declares an immediate bridge refresh without {contribution_name}",
                        "common/scripted_effects/USA_corporate_systems_effects.txt",
                        0,
                    )
                )
                continue
            if (
                len(
                    re.findall(
                        rf"\b{re.escape(contribution_name)}\s*=\s*yes\b",
                        contribution_body,
                    )
                )
                != 1
            ):
                findings.append(
                    (
                        f"USA economic bridge must accumulate {contribution_name} exactly once",
                        rebuild_defs[0].file,
                        rebuild_defs[0].line,
                    )
                )
            contribution_tokens = set(
                re.findall(
                    r"\b(?:has_country_flag|has_idea)\s*=\s*([A-Za-z0-9_]+)",
                    contribution.body,
                )
            )
            for event in event_defs.values():
                if not event.event_id.startswith(chain.namespace + "."):
                    continue
                immediate_mutates = any(
                    self._body_writes_tokens(
                        immediate.body, contribution_tokens, effect_lookup
                    )
                    for immediate in event.immediates
                )
                immediate_refreshes = any(
                    self._body_reaches_effect(
                        immediate.body,
                        "USA_corporate_systems_update_economic_bridge",
                        effect_lookup,
                    )
                    for immediate in event.immediates
                )
                for option in event.options:
                    mutates_contribution = (
                        immediate_mutates
                        or self._body_writes_tokens(
                            option.body, contribution_tokens, effect_lookup
                        )
                    )
                    if (
                        mutates_contribution
                        and not immediate_refreshes
                        and not self._body_reaches_effect(
                            option.body,
                            "USA_corporate_systems_update_economic_bridge",
                            effect_lookup,
                        )
                    ):
                        findings.append(
                            (
                                f"{event.event_id} changes a USA bridge contribution without an immediate refresh",
                                option.file,
                                option.line,
                            )
                        )
        return self._dedupe_findings(findings)

    def _body_reaches_effect(
        self,
        body: str,
        target: str,
        effect_lookup: Mapping[str, BlockDef],
        seen: FrozenSet[str] = frozenset(),
    ) -> bool:
        for match in _EFFECT_YES_RE.finditer(body):
            name = match.group(1)
            if name == target:
                return True
            if name in seen or name not in effect_lookup:
                continue
            if self._body_reaches_effect(
                effect_lookup[name].body, target, effect_lookup, seen | {name}
            ):
                return True
        return False

    def _body_writes_tokens(
        self,
        body: str,
        tokens: Iterable[str],
        effect_lookup: Mapping[str, BlockDef],
        seen: FrozenSet[str] = frozenset(),
    ) -> bool:
        for token in tokens:
            escaped = re.escape(token)
            if re.search(
                rf"\b(?:set_country_flag|clr_country_flag|add_ideas|remove_ideas)\s*=\s*(?:\{{[^}}]*\b)?{escaped}\b",
                body,
                re.DOTALL,
            ) or re.search(
                rf"\b(?:set_variable|add_to_variable|subtract_from_variable|multiply_variable|divide_variable)\s*=\s*\{{\s*{escaped}\s*=",
                body,
            ):
                return True
        for match in _EFFECT_YES_RE.finditer(body):
            name = match.group(1)
            if name in seen or name not in effect_lookup:
                continue
            if self._body_writes_tokens(
                effect_lookup[name].body, tokens, effect_lookup, seen | {name}
            ):
                return True
        return False

    def _global_flag_write_sites(
        self, flag: str
    ) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
        paths = [
            "common/**/*.txt",
            "events/**/*.txt",
            "history/**/*.txt",
        ]
        patterns = {
            "set": re.compile(
                rf"\bset_global_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
            ),
            "clear": re.compile(
                rf"\bclr_global_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
            ),
        }
        writes: Dict[str, List[Tuple[str, int]]] = {"set": [], "clear": []}
        marker = flag.encode("ascii")
        for filepath in self._collect_text_files(paths):
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            if marker not in raw:
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            for kind, pattern in patterns.items():
                writes[kind].extend(
                    (self._relpath(filepath), self._line(text, match.start()))
                    for match in pattern.finditer(text)
                )
        return writes["set"], writes["clear"]

    def _country_flag_write_sites(
        self, flags: Iterable[str]
    ) -> Dict[str, Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]]:
        tracked = tuple(flags)
        writes = {flag: ([], []) for flag in tracked}
        needles = {flag: flag.encode("ascii") for flag in tracked}
        for filepath in self._collect_text_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        ):
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            present = [flag for flag in tracked if needles[flag] in raw]
            if not present:
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            for flag in present:
                set_pattern = re.compile(
                    rf"\bset_country_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
                )
                clear_pattern = re.compile(
                    rf"\bclr_country_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
                )
                sets, clears = writes[flag]
                sets.extend(
                    (self._relpath(filepath), self._line(text, match.start()))
                    for match in set_pattern.finditer(text)
                )
                clears.extend(
                    (self._relpath(filepath), self._line(text, match.start()))
                    for match in clear_pattern.finditer(text)
                )
        return writes

    def _outcome_ideas_added(
        self,
        body: str,
        chain: ChainConfig,
        effect_defs: Dict[str, List[BlockDef]],
        seen: FrozenSet[str] = frozenset(),
    ) -> Set[str]:
        found = {
            match.group(1)
            for match in _ADD_IDEA_RE.finditer(body)
            if (
                match.group(1) in chain.outcome_ideas
                if chain.outcome_ideas
                else any(
                    match.group(1).startswith(prefix)
                    for prefix in chain.outcome_idea_prefixes
                )
            )
        }
        for match in _EFFECT_YES_RE.finditer(body):
            name = match.group(1)
            if (
                not name.startswith(chain.root)
                or name in seen
                or name not in effect_defs
            ):
                continue
            found |= self._outcome_ideas_added(
                effect_defs[name][0].body, chain, effect_defs, seen | {name}
            )
        return found

    def _outcome_ideas_for_chain(
        self, chain: ChainConfig, idea_defs: Dict[str, IdeaDef]
    ) -> Set[str]:
        if chain.outcome_ideas:
            return set(chain.outcome_ideas)
        results = set()
        for idea_id in idea_defs:
            if any(
                idea_id.startswith(prefix) for prefix in chain.outcome_idea_prefixes
            ):
                results.add(idea_id)
        return results

    def _line_is_cross_write(
        self, line: str, owner: ChainConfig, stack: Sequence[str]
    ) -> bool:
        if any(keyword in line for keyword in _WRITE_KEYWORDS):
            return True
        if any(keyword in line for keyword in _EVENT_KEYWORDS):
            return True
        if any(context in ("ai_chance", "trigger") for context in stack):
            return False
        return bool(
            re.search(r"\b([A-Za-z0-9_]+)\s*=\s*yes\b", line)
            and any(prefix in line for prefix in owner.owned_prefixes)
        )

    def _line_is_cross_read(self, line: str, stack: Sequence[str]) -> bool:
        if any(keyword in line for keyword in _READ_KEYWORDS):
            return True
        return bool(
            any(context in ("ai_chance", "trigger") for context in stack)
            and re.search(r"\b[A-Za-z0-9_]+\s*=\s*yes\b", line)
        )

    def _is_allowed(self, token: str, patterns: Sequence[str]) -> bool:
        """Exact match only, so an exception never covers a neighbouring symbol."""
        return token in patterns
