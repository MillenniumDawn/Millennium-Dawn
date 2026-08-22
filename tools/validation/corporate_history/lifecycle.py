"""Game-rule modes, lifecycle state, reconstruction, and completion checks."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from shared_utils import extract_block_from_text, strip_comments

from .model import (
    _CLAMP_VAR_RE,
    _CORPORATE_MODES,
    _CUSTOM_EFFECT_REWARDS,
    _DIRECT_CORP_CLAMP_RE,
    _EFFECT_YES_RE,
    _EVENT_KEYWORDS,
    _EVENT_SHORT_CALL_RE,
    _ID_RE,
    _NATIVE_CONTRACT_ROLES,
    _SCRIPT_TOKEN_CAPTURE,
    _SET_TEMP_CORP_RE,
    _SET_VAR_RE,
    _TOP_LEVEL_BLOCK_RE,
    BlockDef,
    CallSite,
    ChainConfig,
    EventDef,
    IdeaDef,
    ModeGraphResult,
    ModeTrace,
    _collect_native_write_tokens,
    _is_repeatable_decision,
    _native_token_fragment,
    _program_lifecycle_findings,
    _removes_active_decision,
)


class LifecycleMixin:
    @staticmethod
    def _combine_condition_truth(
        values: Sequence[Optional[bool]], union: bool
    ) -> Optional[bool]:
        if union:
            if any(value is True for value in values):
                return True
            if any(value is None for value in values):
                return None
            return False
        if any(value is False for value in values):
            return False
        if any(value is None for value in values):
            return None
        return True

    def _mode_tag_condition_truth(
        self,
        text: str,
        mode: Optional[str],
        host_tag: Optional[str],
        union: bool = False,
    ) -> Tuple[Optional[bool], bool]:
        """Evaluate known mode/tag atoms while preserving unknown runtime predicates."""
        values: List[Optional[bool]] = []
        has_mode_atom = False
        residual: List[str] = []
        cursor = 0
        for name, start, end, body in self._iter_direct_child_blocks(text):
            residual.append(text[cursor:start])
            cursor = end
            upper = name.upper()
            if upper in {"NOT", "OR", "AND"}:
                nested, nested_has_mode = self._mode_tag_condition_truth(
                    body, mode, host_tag, union=upper == "OR"
                )
                has_mode_atom = has_mode_atom or nested_has_mode
                if upper == "NOT" and nested is not None:
                    nested = not nested
                values.append(nested)
            else:
                values.append(None)
        residual.append(text[cursor:])
        direct = "".join(residual)

        trigger_modes = {
            "corporate_history_full_enabled": {"full"},
            "corporate_history_outcomes_only_enabled": {"outcomes_only"},
            "corporate_history_enabled": {"full", "outcomes_only"},
        }
        mode_pattern = re.compile(
            r"\b(corporate_history_full_enabled|corporate_history_outcomes_only_enabled|corporate_history_enabled)\s*=\s*(yes|no)\b"
        )
        for match in mode_pattern.finditer(direct):
            has_mode_atom = True
            if mode is None:
                values.append(None)
                continue
            value = mode in trigger_modes[match.group(1)]
            values.append(value if match.group(2) == "yes" else not value)
        direct = mode_pattern.sub("", direct)

        tag_pattern = re.compile(r"\boriginal_tag\s*=\s*([A-Z0-9]{3})\b")
        for match in tag_pattern.finditer(direct):
            values.append(None if host_tag is None else match.group(1) == host_tag)
        direct = tag_pattern.sub("", direct)
        if direct.strip():
            values.append(None)

        return self._combine_condition_truth(values, union), has_mode_atom

    def _mode_constraint(self, text: str, union: bool = False) -> Optional[Set[str]]:
        possible: Set[str] = set()
        has_mode_atom = False
        for mode in _CORPORATE_MODES:
            truth, mode_atom = self._mode_tag_condition_truth(
                text, mode, None, union=union
            )
            has_mode_atom = has_mode_atom or mode_atom
            if truth is not False:
                possible.add(mode)
        return possible if has_mode_atom else None

    @staticmethod
    def _participant_tags_are_valid(raw_tags: object) -> bool:
        return (
            isinstance(raw_tags, list)
            and bool(raw_tags)
            and all(isinstance(tag, str) for tag in raw_tags)
            and len(raw_tags) == len(set(raw_tags))
            and all(re.fullmatch(r"[A-Z0-9]{3}", tag) for tag in raw_tags)
        )

    def _participant_trigger_is_exact(
        self, trigger_text: str, trigger_name: str, participant_tags: Sequence[str]
    ) -> bool:
        blocks = []
        for match in _TOP_LEVEL_BLOCK_RE.finditer(trigger_text):
            if match.group(1) != trigger_name:
                continue
            body, end = extract_block_from_text(trigger_text, match.end() - 1)
            if end != -1:
                blocks.append(strip_comments(body))
        if len(blocks) != 1:
            return False

        children = list(self._iter_direct_child_blocks(blocks[0]))
        if len(children) != 1 or children[0][0] != "OR":
            return False
        _name, start, end, body = children[0]
        if (blocks[0][:start] + blocks[0][end:]).strip():
            return False

        tag_pattern = re.compile(r"\boriginal_tag\s*=\s*([A-Z0-9]{3})\b")
        observed_tags = tag_pattern.findall(body)
        return (
            observed_tags == list(participant_tags)
            and not tag_pattern.sub("", body).strip()
        )

    def _participant_driver_hosts(
        self, on_action_texts: Mapping[str, str], driver_name: str
    ) -> List[str]:
        driver_pattern = re.compile(rf"\b{re.escape(driver_name)}\s*=\s*yes\b")
        hosts: List[str] = []
        for text in on_action_texts.values():
            for match in _TOP_LEVEL_BLOCK_RE.finditer(text):
                if match.group(1) != "on_actions":
                    continue
                outer_body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                for host, _start, _child_end, body in self._iter_direct_child_blocks(
                    outer_body
                ):
                    hosts.extend(
                        [host] * len(driver_pattern.findall(strip_comments(body)))
                    )
        return hosts

    def _participant_dispatch_is_exact(
        self,
        on_action_texts: Mapping[str, str],
        driver_name: str,
        participant_tags: Sequence[str],
    ) -> bool:
        driver_hosts = self._participant_driver_hosts(on_action_texts, driver_name)
        expected_hosts = {f"on_monthly_{tag}" for tag in participant_tags}
        return set(driver_hosts) == expected_hosts and len(driver_hosts) == len(
            expected_hosts
        )

    def _independent_mode_graph(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        tracked_event_ids: Set[str],
        direct_event_calls: Optional[Mapping[str, Sequence[CallSite]]] = None,
        event_defs_for_expansion: Optional[Mapping[str, EventDef]] = None,
    ) -> ModeGraphResult:
        tracked = frozenset(tracked_event_ids)
        expands_events = event_defs_for_expansion is not None
        cache_key = (id(effect_defs), tracked, expands_events)
        cached = self._independent_mode_graph_cache.get(cache_key)
        if cached is not None:
            return cached
        if not tracked and not expands_events:
            for (
                cached_effects_id,
                _cached_tracked,
                cached_expands,
            ), cached_result in self._independent_mode_graph_cache.items():
                if cached_effects_id == id(effect_defs) and not cached_expands:
                    return cached_result[0], {}, cached_result[2], {}

        effect_modes: Dict[str, Set[str]] = defaultdict(set)
        event_modes: Dict[str, Set[str]] = defaultdict(set)
        effect_traces: Dict[Tuple[str, str], List[ModeTrace]] = defaultdict(list)
        event_traces: Dict[Tuple[str, str], List[ModeTrace]] = defaultdict(list)
        pending = deque()
        pending_events = deque()
        visited: Set[Tuple[str, str, str, str]] = set()
        visited_events: Set[Tuple[str, str, str, str]] = set()
        relevant_effects = self._mode_graph_relevant_effects(
            effect_defs,
            tracked_event_ids,
            direct_event_calls,
            event_defs_for_expansion,
        )

        def record_event(
            event_id: str,
            mode: str,
            owner: str,
            file: str,
            line: int,
            host: str,
            host_file: str,
            block_path: Tuple[str, ...],
        ) -> None:
            if event_id not in tracked_event_ids:
                return
            trace = ModeTrace(owner, file, line, host, host_file, block_path)
            event_modes[event_id].add(mode)
            event_traces[(event_id, mode)].append(trace)
            if event_defs_for_expansion is not None:
                pending_events.append(
                    (event_id, mode, host, host_file, block_path + (event_id,))
                )

        def record_effect(
            effect_name: str,
            mode: str,
            owner: str,
            file: str,
            line: int,
            host: str,
            host_file: str,
            block_path: Tuple[str, ...],
        ) -> None:
            if effect_name not in effect_defs or effect_name not in relevant_effects:
                return
            trace = ModeTrace(owner, file, line, host, host_file, block_path)
            effect_modes[effect_name].add(mode)
            effect_traces[(effect_name, mode)].append(trace)
            pending.append(
                (effect_name, mode, host, host_file, block_path + (effect_name,))
            )

        def walk(
            body: str,
            mode: str,
            owner: str,
            file: str,
            base_line: int,
            host: str,
            host_file: str,
            host_tag: Optional[str],
            block_path: Tuple[str, ...],
        ) -> None:
            children = list(self._iter_direct_child_blocks(body))
            segments: List[Tuple[int, str]] = []
            cursor = 0
            for _name, start, end, _nested in children:
                segments.append((cursor, body[cursor:start]))
                cursor = end
            segments.append((cursor, body[cursor:]))
            for segment_start, segment in segments:
                for match in _EFFECT_YES_RE.finditer(segment):
                    line = (
                        base_line + self._line(body, segment_start + match.start()) - 1
                    )
                    record_effect(
                        match.group(1),
                        mode,
                        owner,
                        file,
                        line,
                        host,
                        host_file,
                        block_path,
                    )
                for match in _EVENT_SHORT_CALL_RE.finditer(segment):
                    line = (
                        base_line + self._line(body, segment_start + match.start()) - 1
                    )
                    record_event(
                        match.group(1),
                        mode,
                        owner,
                        file,
                        line,
                        host,
                        host_file,
                        block_path,
                    )

            remaining = {mode}
            conditional_chain = False
            for name, start, _end, nested in children:
                child_line = base_line + self._line(body, start) - 1
                if name in _EVENT_KEYWORDS:
                    id_match = _ID_RE.search(nested)
                    if id_match:
                        record_event(
                            id_match.group(1),
                            mode,
                            owner,
                            file,
                            child_line,
                            host,
                            host_file,
                            block_path,
                        )
                    conditional_chain = False
                    remaining = {mode}
                    continue
                if name == "limit":
                    continue
                if name == "if":
                    remaining = {mode}
                    conditional_chain = True
                    limit = self._direct_child_block(nested, "limit") or ""
                    truth, _has_mode_atom = self._mode_tag_condition_truth(
                        limit, mode, host_tag
                    )
                    branch = {mode} if truth is not False else set()
                    if truth is True and branch:
                        remaining.clear()
                elif name == "else_if" and conditional_chain:
                    limit = self._direct_child_block(nested, "limit") or ""
                    truth, _has_mode_atom = self._mode_tag_condition_truth(
                        limit, mode, host_tag
                    )
                    branch = set(remaining) if truth is not False else set()
                    if truth is True and branch:
                        remaining.clear()
                elif name == "else" and conditional_chain:
                    branch = set(remaining)
                    remaining.clear()
                else:
                    conditional_chain = False
                    remaining = {mode}
                    branch = {mode}
                if mode in branch:
                    walk(
                        nested,
                        mode,
                        owner,
                        file,
                        child_line,
                        host,
                        host_file,
                        host_tag,
                        block_path + (name,),
                    )

        for filepath in self._collect_text_files(["common/on_actions/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            rel = self._relpath(filepath)
            for match in _TOP_LEVEL_BLOCK_RE.finditer(text):
                outer_body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                outer_name = match.group(1)
                hosts: List[Tuple[str, int, str]] = []
                if outer_name == "on_actions":
                    hosts.extend(
                        (name, start, body)
                        for name, start, _child_end, body in self._iter_direct_child_blocks(
                            outer_body
                        )
                        if name.startswith("on_")
                    )
                elif outer_name.startswith("on_"):
                    hosts.append((outer_name, 0, outer_body))
                for host, host_start, host_body in hosts:
                    host_line = (
                        self._line(text, match.start())
                        + self._line(outer_body, host_start)
                        - 1
                    )
                    host_tag_match = re.fullmatch(
                        r"on_(?:daily|weekly|monthly|yearly)_([A-Z0-9]{3})",
                        host,
                    )
                    host_tag = host_tag_match.group(1) if host_tag_match else None
                    for mode in _CORPORATE_MODES:
                        walk(
                            host_body,
                            mode,
                            f"on_action:{host}",
                            rel,
                            host_line,
                            host,
                            rel,
                            host_tag,
                            (outer_name, host),
                        )

        while pending or pending_events:
            while pending:
                effect_name, mode, host, host_file, block_path = pending.popleft()
                key = (effect_name, mode, host, host_file)
                if key in visited:
                    continue
                visited.add(key)
                host_tag_match = re.fullmatch(
                    r"on_(?:daily|weekly|monthly|yearly)_([A-Z0-9]{3})", host
                )
                host_tag = host_tag_match.group(1) if host_tag_match else None
                for definition in effect_defs.get(effect_name, []):
                    walk(
                        definition.body,
                        mode,
                        effect_name,
                        definition.file,
                        definition.line,
                        host,
                        host_file,
                        host_tag,
                        block_path,
                    )
            while pending_events:
                event_id, mode, host, host_file, block_path = pending_events.popleft()
                key = (event_id, mode, host, host_file)
                if key in visited_events:
                    continue
                visited_events.add(key)
                event = (
                    event_defs_for_expansion.get(event_id)
                    if event_defs_for_expansion is not None
                    else None
                )
                if event is None:
                    continue
                host_tag_match = re.fullmatch(
                    r"on_(?:daily|weekly|monthly|yearly)_([A-Z0-9]{3})", host
                )
                host_tag = host_tag_match.group(1) if host_tag_match else None
                walk(
                    event.body,
                    mode,
                    event_id,
                    event.file,
                    event.line,
                    host,
                    host_file,
                    host_tag,
                    block_path,
                )
        result = effect_modes, event_modes, effect_traces, event_traces
        self._independent_mode_graph_cache[cache_key] = result
        return result

    def _mode_graph_relevant_effects(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        tracked_event_ids: Set[str],
        direct_event_calls: Optional[Mapping[str, Sequence[CallSite]]],
        event_defs_for_expansion: Optional[Mapping[str, EventDef]],
    ) -> Set[str]:
        """Effects that can lead from an on-action to a contract-owned target.

        Walking every effect reachable from every on-action expands most of the mod's
        scripted-effect graph three times.  The mode contract only needs ancestors of
        declared subsystem/core targets and effects that directly dispatch tracked
        events; direct-event ownership is validated separately across the repository.
        """
        targets = {
            "corporate_history_country_bootstrap",
            "corporate_history_monthly_dispatch",
            "corporate_history_initialize_midyear_recovery",
            "corporate_history_recover_midyear_events",
        }
        for subsystem in self._independent_subsystems:
            targets.update(subsystem.effect_roots)
            targets.update(subsystem.scheduler_entrypoints)
            targets.update(subsystem.reconstruction_effects)

        raw_chains = self._manifest_payload.get("chains", [])
        if isinstance(raw_chains, list):
            for raw_chain in raw_chains:
                if not isinstance(raw_chain, dict):
                    continue
                root = raw_chain.get("root")
                monthly_driver = raw_chain.get("monthly_driver")
                if isinstance(root, str) and root:
                    targets.update(
                        {
                            f"{root}_reconstruct_history",
                            f"{root}_schedule_current_year_events",
                        }
                    )
                if isinstance(monthly_driver, str) and monthly_driver:
                    targets.add(monthly_driver)
                auxiliary_lifecycles = raw_chain.get("auxiliary_lifecycles", [])
                if not isinstance(auxiliary_lifecycles, list):
                    continue
                for lifecycle in auxiliary_lifecycles:
                    if not isinstance(lifecycle, dict):
                        continue
                    for field in (
                        "reconstruction_effect",
                        "scheduler_effect",
                        "monthly_driver",
                    ):
                        value = lifecycle.get(field)
                        if isinstance(value, str) and value:
                            targets.add(value)

        if direct_event_calls is None:
            if tracked_event_ids:
                for owner, definitions in effect_defs.items():
                    if any(
                        self._find_event_calls(
                            definition.body, definition.line, tracked_event_ids
                        )
                        for definition in definitions
                    ):
                        targets.add(owner)
        else:
            targets.update(
                site.owner
                for sites in direct_event_calls.values()
                for site in sites
                if site.kind == "effect"
            )

        if event_defs_for_expansion is not None:
            event_effect_roots = {
                match.group(1)
                for event_id in tracked_event_ids
                if (event := event_defs_for_expansion.get(event_id)) is not None
                for match in _EFFECT_YES_RE.finditer(event.body)
                if match.group(1) in effect_defs
            }
            targets.update(
                self._effect_descendants(
                    event_effect_roots, self._effect_call_children(effect_defs)
                )
            )

        parents = self._effect_call_parents(effect_defs)
        relevant: Set[str] = set()
        pending = list(targets)
        while pending:
            effect_name = pending.pop()
            if effect_name in relevant:
                continue
            relevant.add(effect_name)
            pending.extend(parents.get(effect_name, ()))
        return relevant

    def _validate_reusable_decision_lifecycles(
        self, effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        schema_version = int(self._manifest_payload.get("schema_version", 1))
        raw_systems = self._manifest_payload.get("reusable_decision_lifecycles")
        if raw_systems is None:
            if schema_version >= 5:
                findings.append(
                    (
                        "Schema v5 requires reusable_decision_lifecycles",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            return findings
        if not isinstance(raw_systems, list) or not raw_systems:
            return [
                (
                    "reusable_decision_lifecycles must be a non-empty list",
                    "tools/corporate_history_contract.json",
                    1,
                )
            ]

        seen_decisions: Set[str] = set()
        valid_kinds = {"timed_idea", "cadence_only", "construction_project"}
        valid_cooldown_modes = {"days_re_enable", "active_duration"}

        for system_index, raw_system in enumerate(raw_systems):
            if not isinstance(raw_system, dict):
                findings.append(
                    (
                        f"reusable_decision_lifecycles[{system_index}] must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue
            missing_system_fields = [
                field
                for field in ("name", "decision_file", "programs")
                if field not in raw_system
            ]
            if missing_system_fields:
                findings.append(
                    (
                        f"reusable_decision_lifecycles[{system_index}] is missing: "
                        + ", ".join(missing_system_fields),
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            system_name = str(raw_system["name"])
            decision_file = str(raw_system["decision_file"])
            decision_path = self._root / decision_file
            try:
                decision_text = decision_path.read_text(
                    encoding="utf-8-sig", errors="replace"
                )
            except OSError:
                findings.append(
                    (f"{system_name} is missing {decision_file}", decision_file, 1)
                )
                continue

            decision_blocks_by_indent: Dict[int, Dict[str, str]] = {0: {}, 1: {}}
            offset = 0
            for line in decision_text.splitlines(keepends=True):
                match = re.match(r"^(\t?)([^\t#][A-Za-z0-9_.:-]*)\s*=\s*\{", line)
                if match is not None:
                    opening_brace = offset + line.index("{")
                    block, end = extract_block_from_text(decision_text, opening_brace)
                    if end != -1:
                        indent = len(match.group(1))
                        decision_blocks_by_indent[indent][match.group(2)] = block
                offset += len(line)

            localisation_file = str(raw_system.get("localisation_file", ""))
            localisation_values: Dict[str, str] = {}
            if localisation_file:
                try:
                    localisation_text = (self._root / localisation_file).read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                except OSError:
                    findings.append(
                        (
                            f"{system_name} is missing {localisation_file}",
                            localisation_file,
                            1,
                        )
                    )
                else:
                    for line in localisation_text.splitlines():
                        match = re.match(r'^\s*([^\s:#]+):\d*\s+"(.*)"\s*$', line)
                        if match is not None:
                            localisation_values[match.group(1)] = match.group(2)

            programs = raw_system["programs"]
            if not isinstance(programs, list) or not programs:
                findings.append(
                    (
                        f"{system_name} programs must be a non-empty list",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            declared_decisions = {
                str(program.get("decision", ""))
                for program in programs
                if isinstance(program, dict)
            }
            matching_indents = [
                indent
                for indent, blocks in decision_blocks_by_indent.items()
                if declared_decisions & blocks.keys()
            ]
            decision_indent = matching_indents[0] if matching_indents else 1
            decision_blocks = decision_blocks_by_indent[decision_indent]
            actionable_decisions = {
                decision
                for decision, body in decision_blocks.items()
                if "complete_effect = {" in body
            }
            if actionable_decisions != declared_decisions:
                missing = sorted(actionable_decisions - declared_decisions)
                extra = sorted(declared_decisions - actionable_decisions)
                details = []
                if missing:
                    details.append(f"undeclared: {', '.join(missing)}")
                if extra:
                    details.append(f"not actionable: {', '.join(extra)}")
                findings.append(
                    (
                        f"{system_name} reusable decision coverage differs from its file"
                        + (f" ({'; '.join(details)})" if details else ""),
                        decision_file,
                        1,
                    )
                )

            cooldown_markers = {
                str(marker)
                for marker in raw_system.get("forbidden_cooldown_markers", [])
            }
            for program_index, program in enumerate(programs):
                if not isinstance(program, dict):
                    findings.append(
                        (
                            f"{system_name} programs[{program_index}] must be an object",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                missing_program_fields = [
                    field
                    for field in (
                        "decision",
                        "kind",
                        "active_days",
                        "cooldown_mode",
                        "cooldown_days",
                    )
                    if field not in program
                ]
                if missing_program_fields:
                    findings.append(
                        (
                            f"{system_name} programs[{program_index}] is missing: "
                            + ", ".join(missing_program_fields),
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue

                decision = str(program["decision"])
                kind = str(program["kind"])
                cooldown_mode = str(program["cooldown_mode"])
                try:
                    active_days = int(program["active_days"])
                    cooldown_days = int(program["cooldown_days"])
                except (TypeError, ValueError):
                    findings.append(
                        (
                            f"{decision} lifecycle durations must be integers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue

                if decision in seen_decisions:
                    findings.append(
                        (
                            f"Reusable decision {decision} is declared more than once",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                seen_decisions.add(decision)
                if kind not in valid_kinds:
                    findings.append(
                        (
                            f"{decision} has unsupported lifecycle kind {kind}",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                if cooldown_mode not in valid_cooldown_modes:
                    findings.append(
                        (
                            f"{decision} has unsupported cooldown mode {cooldown_mode}",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue

                decision_body = decision_blocks.get(decision, "")
                if not decision_body:
                    findings.append(
                        (f"Missing reusable decision {decision}", decision_file, 1)
                    )
                    continue
                _decision_match = re.search(
                    r"^" + "\t" * decision_indent + re.escape(decision) + r"\s*=\s*\{",
                    decision_text,
                    re.MULTILINE,
                )
                decision_line = (
                    self._line(decision_text, _decision_match.start())
                    if _decision_match
                    else 1
                )
                if not _is_repeatable_decision(decision_body):
                    findings.append(
                        (
                            f"{decision} must declare fire_only_once = no",
                            decision_file,
                            decision_line,
                        )
                    )

                if kind == "timed_idea":
                    if not 1 <= active_days <= 365:
                        findings.append(
                            (
                                f"{decision} temporary program must last 1 to 365 days",
                                "tools/corporate_history_contract.json",
                                1,
                            )
                        )
                    idea = str(program.get("idea", ""))
                    duration_source = str(program.get("duration_source", ""))
                    source_body = decision_body
                    source_file = decision_file
                    if duration_source and duration_source != "decision":
                        source_defs = effect_defs.get(duration_source, [])
                        if len(source_defs) != 1:
                            findings.append(
                                (
                                    f"{decision} requires exactly one duration source "
                                    f"{duration_source}",
                                    str(raw_system.get("effect_file", decision_file)),
                                    1,
                                )
                            )
                            source_body = ""
                        else:
                            source_body = source_defs[0].body
                            source_file = source_defs[0].file
                    timed_pattern = re.compile(
                        rf"\badd_timed_idea\s*=\s*\{{\s*idea\s*=\s*"
                        rf"{re.escape(idea)}\s+days\s*=\s*{active_days}\s*\}}"
                    )
                    if len(timed_pattern.findall(strip_comments(source_body))) != 1:
                        findings.append(
                            (
                                f"{decision} must apply {idea} once for {active_days} days",
                                source_file,
                                1,
                            )
                        )

                    cleanup_effect = str(program.get("cleanup_effect", ""))
                    cleanup_defs = effect_defs.get(cleanup_effect, [])
                    if len(cleanup_defs) != 1:
                        findings.append(
                            (
                                f"{decision} requires exactly one cleanup effect "
                                f"{cleanup_effect}",
                                "tools/corporate_history_contract.json",
                                1,
                            )
                        )
                    else:
                        cleanup_body = strip_comments(cleanup_defs[0].body)
                        removes_idea = re.search(
                            rf"\bremove_ideas\s*=\s*(?:{re.escape(idea)}|"
                            rf"\{{[^}}]*\b{re.escape(idea)}\b)",
                            cleanup_body,
                            re.DOTALL,
                        )
                        if removes_idea is None:
                            findings.append(
                                (
                                    f"{cleanup_effect} must remove {idea}",
                                    cleanup_defs[0].file,
                                    cleanup_defs[0].line,
                                )
                            )
                        if program.get(
                            "cleanup_decision"
                        ) and not _removes_active_decision(cleanup_body, decision):
                            findings.append(
                                (
                                    f"{cleanup_effect} must remove active decision {decision}",
                                    cleanup_defs[0].file,
                                    cleanup_defs[0].line,
                                )
                            )
                elif active_days != 0:
                    findings.append(
                        (
                            f"{decision} {kind} lifecycle must use active_days = 0",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )

                if cooldown_mode == "days_re_enable":
                    if not 1 <= cooldown_days <= 365:
                        findings.append(
                            (
                                f"{decision} re-enable period must last 1 to 365 days",
                                "tools/corporate_history_contract.json",
                                1,
                            )
                        )
                    cooldown_pattern = re.compile(
                        rf"\bdays_re_enable\s*=\s*{cooldown_days}\b"
                    )
                    if len(cooldown_pattern.findall(decision_body)) != 1:
                        findings.append(
                            (
                                f"{decision} must declare a {cooldown_days}-day re-enable period",
                                decision_file,
                                decision_line,
                            )
                        )
                    if kind == "timed_idea" and cooldown_days != active_days:
                        findings.append(
                            (
                                f"{decision} re-enable period must equal its active duration",
                                "tools/corporate_history_contract.json",
                                1,
                            )
                        )
                else:
                    if kind != "timed_idea" or cooldown_days != 0:
                        findings.append(
                            (
                                f"{decision} active-duration cadence requires a timed idea "
                                "and zero post-program cooldown",
                                "tools/corporate_history_contract.json",
                                1,
                            )
                        )
                    duration_pattern = re.compile(
                        rf"\bdays_remove\s*=\s*{active_days}\b"
                    )
                    if len(duration_pattern.findall(decision_body)) != 1:
                        findings.append(
                            (
                                f"{decision} must remain active for {active_days} days",
                                decision_file,
                                decision_line,
                            )
                        )
                    for cooldown_marker in sorted(cooldown_markers):
                        if cooldown_marker in decision_body:
                            findings.append(
                                (
                                    f"{decision} may not start post-program cooldown "
                                    f"{cooldown_marker}",
                                    decision_file,
                                    decision_line,
                                )
                            )

                if kind == "construction_project":
                    mission = str(program.get("mission", ""))
                    try:
                        project_days = int(program.get("project_days", 0))
                    except (TypeError, ValueError):
                        project_days = 0
                    mission_body = decision_blocks.get(mission, "")
                    if not mission_body or not re.search(
                        rf"\bdays_mission_timeout\s*=\s*{project_days}\b",
                        mission_body,
                    ):
                        findings.append(
                            (
                                f"{decision} construction mission {mission} must last "
                                f"{project_days} days",
                                decision_file,
                                decision_line,
                            )
                        )
                    if (
                        project_days > 365
                        and not str(program.get("long_duration_reason", "")).strip()
                    ):
                        findings.append(
                            (
                                f"{decision} construction timer over 365 days needs a reason",
                                "tools/corporate_history_contract.json",
                                1,
                            )
                        )

                expected_localisation_days = (
                    active_days if kind == "timed_idea" else cooldown_days
                )
                for key in program.get("localisation_keys", []):
                    key = str(key)
                    value = localisation_values.get(key)
                    if value is None:
                        findings.append(
                            (
                                f"Missing lifecycle localisation key {key}",
                                localisation_file,
                                1,
                            )
                        )
                        continue
                    if str(expected_localisation_days) not in value:
                        findings.append(
                            (
                                f"{key} must state {expected_localisation_days} days",
                                localisation_file,
                                1,
                            )
                        )
                    if expected_localisation_days != 730 and "730" in value:
                        findings.append(
                            (
                                f"{key} still claims a 730-day lifecycle",
                                localisation_file,
                                1,
                            )
                        )

        return findings

    def _validate_shared_systems(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        schema_version = int(self._manifest_payload.get("schema_version", 1))
        raw_systems = self._manifest_payload.get("shared_systems")
        if raw_systems is None and schema_version < 4:
            return findings
        if not isinstance(raw_systems, list) or not raw_systems:
            return [
                (
                    "Schema v4 requires a non-empty shared_systems list",
                    "tools/corporate_history_contract.json",
                    1,
                )
            ]

        required_fields = (
            "name",
            "root",
            "namespace",
            "game_rule",
            "dispatcher_host",
            "participant_array",
            "event_ids",
            "variables",
            "initial_state",
            "support_model_codes",
            "support_model_precedence",
            "reconstruction_baseline",
            "historical_routes",
            "scripted_effects",
            "files",
            "lifecycle_markers",
            "storage_lifecycle_markers",
            "adoption_ideas",
            "support_ideas",
            "persistent_idea_modifiers",
            "owned_timed_ideas",
            "timed_idea_modifiers",
            "programs",
            "excluded_generic_idea_tags",
            "reconstruction_effect",
            "cleanup_effect",
            "refresh_ideas_effect",
            "allowed_native_reads",
            "native_write_prefixes",
            "localisation_keys",
            "usa_bridge_effect",
        )
        required_files = (
            "rule",
            "trigger",
            "effect",
            "on_action",
            "event",
            "idea",
            "decision",
            "category",
            "bridge",
            "ibm_event",
        )

        for index, raw_system in enumerate(raw_systems):
            if not isinstance(raw_system, dict):
                findings.append(
                    (
                        f"shared_systems[{index}] must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue
            versioned_required_fields = required_fields + (
                ("participant_tags",) if schema_version >= 6 else ()
            )
            missing = [
                field for field in versioned_required_fields if field not in raw_system
            ]
            if missing:
                findings.append(
                    (
                        f"shared_systems[{index}] is missing required fields: {', '.join(missing)}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            name = str(raw_system["name"])
            root = str(raw_system["root"])
            namespace = str(raw_system["namespace"])
            files = raw_system["files"]
            if not isinstance(files, dict):
                findings.append(
                    (
                        f"{name} files must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue
            missing_files = [field for field in required_files if field not in files]
            if missing_files:
                findings.append(
                    (
                        f"{name} files is missing: {', '.join(missing_files)}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            declared_text: Dict[str, str] = {}
            for role, relative in files.items():
                if role in ("localisation", "integration"):
                    continue
                path = self._root / str(relative)
                if not path.is_file():
                    findings.append(
                        (f"{name} missing {role} file {relative}", str(relative), 1)
                    )
                    continue
                try:
                    declared_text[role] = path.read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                except OSError as exc:
                    findings.append(
                        (
                            f"{name} cannot read {role} file {relative}: {exc}",
                            str(relative),
                            1,
                        )
                    )

            game_rule = raw_system["game_rule"]
            if not isinstance(game_rule, dict):
                findings.append(
                    (
                        f"{name} game_rule must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                rule_id = str(game_rule.get("id", ""))
                options = game_rule.get("options")
                default = str(game_rule.get("default", ""))
                mode_defs = self._load_top_level_blocks(
                    [str(files["rule"]), str(files["trigger"])]
                )
                rule_defs = mode_defs.get(rule_id, [])
                if len(rule_defs) != 1:
                    findings.append(
                        (
                            f"{name} requires exactly one {rule_id}; found {len(rule_defs)}",
                            str(files["rule"]),
                            rule_defs[0].line if rule_defs else 1,
                        )
                    )
                elif options != ["full", "outcomes_only", "off"] or default != "full":
                    findings.append(
                        (
                            f"{name} game rule must declare Full, Outcomes Only, and Off with Full default",
                            str(files["rule"]),
                            rule_defs[0].line,
                        )
                    )
                elif not all(
                    re.search(rf"\bname\s*=\s*{re.escape(option)}\b", rule_defs[0].body)
                    for option in options
                ):
                    findings.append(
                        (
                            f"{name} game-rule script does not contain all declared options",
                            rule_defs[0].file,
                            rule_defs[0].line,
                        )
                    )
                trigger_names = (
                    f"{root}_full_enabled",
                    f"{root}_outcomes_only_enabled",
                    f"{root}_enabled",
                )
                for trigger_name in trigger_names:
                    definitions = mode_defs.get(trigger_name, [])
                    if len(definitions) != 1:
                        findings.append(
                            (
                                f"{name} requires exactly one {trigger_name}; found {len(definitions)}",
                                str(files["trigger"]),
                                definitions[0].line if definitions else 1,
                            )
                        )

            expected_variable_bounds = {
                f"{root}_base_deployment": (0, 10),
                f"{root}_base_stewardship": (0, 10),
                f"{root}_base_assurance": (0, 10),
                f"{root}_adapter_deployment": (-2, 2),
                f"{root}_adapter_stewardship": (-2, 2),
                f"{root}_adapter_assurance": (-2, 2),
                f"{root}_effective_deployment": (0, 10),
                f"{root}_effective_stewardship": (0, 10),
                f"{root}_effective_assurance": (0, 10),
                f"{root}_base_support_model": (0, 3),
                f"{root}_adapter_support_model": (0, 3),
                f"{root}_effective_support_model": (0, 3),
                f"{root}_milestone_stage": (0, 5),
            }
            raw_variables = raw_system["variables"]
            normalized_bounds: Dict[str, Tuple[Decimal, Decimal]] = {}
            if isinstance(raw_variables, dict):
                for variable, bounds in raw_variables.items():
                    if (
                        not isinstance(bounds, dict)
                        or "min" not in bounds
                        or "max" not in bounds
                    ):
                        continue
                    try:
                        normalized_bounds[str(variable)] = (
                            Decimal(str(bounds["min"])),
                            Decimal(str(bounds["max"])),
                        )
                    except (ValueError, TypeError):
                        pass
            expected_normalized = {
                variable: (Decimal(str(bounds[0])), Decimal(str(bounds[1])))
                for variable, bounds in expected_variable_bounds.items()
            }
            if normalized_bounds != expected_normalized:
                findings.append(
                    (
                        f"{name} must declare the exact bounded base, adapter, effective, support, and milestone variables",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            expected_initial_state = {
                "deployment": 2,
                "stewardship": 3,
                "assurance": 3,
                "support_model": 0,
                "milestone_stage": 0,
            }
            if raw_system["initial_state"] != expected_initial_state:
                findings.append(
                    (
                        f"{name} must declare the approved 2/3/3 Mixed initial state",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            if raw_system["support_model_codes"] != {
                "mixed": 0,
                "upstream": 1,
                "enterprise": 2,
                "national": 3,
            } or raw_system["support_model_precedence"] != (
                "non_mixed_base_else_adapter"
            ):
                findings.append(
                    (
                        f"{name} must declare support codes 0..3 and base-first precedence",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            expected_baseline = [
                {
                    "stage": stage,
                    "deployment": deployment,
                    "stewardship": stewardship,
                    "assurance": assurance,
                    "support_model": 0,
                }
                for stage, deployment, stewardship, assurance in (
                    (0, 2, 3, 3),
                    (1, 3, 3, 3),
                    (2, 4, 3, 3),
                    (3, 5, 3, 4),
                    (4, 6, 3, 4),
                    (5, 7, 3, 5),
                )
            ]
            if raw_system["reconstruction_baseline"] != expected_baseline:
                findings.append(
                    (
                        f"{name} must declare the approved neutral reconstruction baseline",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            expected_historical_routes = {
                "BRA": "upstream",
                "CHI": "national",
                "ENG": "upstream",
                "FRA": "national",
                "GER": "upstream",
                "RAJ": "national",
                "SOV": "national",
                "USA": "enterprise",
            }
            if raw_system["historical_routes"] != expected_historical_routes:
                findings.append(
                    (
                        f"{name} must declare the approved national historical routes",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            effect_text = declared_text.get("effect", "")
            effect_lookup = {
                effect_name: definitions[0]
                for effect_name, definitions in effect_defs.items()
                if len(definitions) == 1
            }

            def reachable_effects(effect_name: str) -> Dict[str, BlockDef]:
                reachable: Dict[str, BlockDef] = {}
                pending = (
                    [effect_lookup[effect_name]] if effect_name in effect_lookup else []
                )
                while pending:
                    effect = pending.pop()
                    if effect.name in reachable:
                        continue
                    reachable[effect.name] = effect
                    for call in _EFFECT_YES_RE.finditer(effect.body):
                        target = call.group(1)
                        if (
                            target.startswith(root)
                            and target in effect_lookup
                            and target not in reachable
                        ):
                            pending.append(effect_lookup[target])
                return reachable

            clamp_bounds = {
                match.group(1): (Decimal(match.group(2)), Decimal(match.group(3)))
                for match in _CLAMP_VAR_RE.finditer(strip_comments(effect_text))
            }
            for variable, bounds in expected_normalized.items():
                if clamp_bounds.get(variable) != bounds:
                    findings.append(
                        (
                            f"{name} must clamp {variable} to {bounds[0]}..{bounds[1]}",
                            str(files["effect"]),
                            1,
                        )
                    )

            scripted_effects = raw_system["scripted_effects"]
            if not isinstance(scripted_effects, list) or not scripted_effects:
                findings.append(
                    (
                        f"{name} scripted_effects must be a non-empty list",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                for effect_name in scripted_effects:
                    definitions = effect_defs.get(str(effect_name), [])
                    if len(definitions) != 1:
                        findings.append(
                            (
                                f"{name} requires exactly one {effect_name}; found {len(definitions)}",
                                str(files["effect"]),
                                definitions[0].line if definitions else 1,
                            )
                        )

            event_ids = raw_system["event_ids"]
            if event_ids != [f"{namespace}.{number}" for number in range(1, 6)]:
                findings.append(
                    (
                        f"{name} must reserve exactly {namespace}.1 through {namespace}.5",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                event_ids = []
            for event_id in event_ids:
                event = event_defs.get(str(event_id))
                if event is None:
                    findings.append(
                        (f"{name} missing event {event_id}", str(files["event"]), 1)
                    )
                    continue
                if event.file.replace("\\", "/") != str(files["event"]).replace(
                    "\\", "/"
                ):
                    findings.append(
                        (
                            f"{event_id} is outside its declared event file",
                            event.file,
                            event.line,
                        )
                    )
                if "is_triggered_only = yes" not in event.body:
                    findings.append(
                        (f"{event_id} must be triggered-only", event.file, event.line)
                    )
                if not event.options:
                    findings.append(
                        (
                            f"{event_id} requires at least one option",
                            event.file,
                            event.line,
                        )
                    )
            event_text = declared_text.get("event", "")
            if re.search(r"\bnews_event\s*=", event_text):
                findings.append(
                    (
                        f"{name} must not define global news events",
                        str(files["event"]),
                        1,
                    )
                )
            undeclared_events = {
                event_id
                for event_id in event_defs
                if event_id.startswith(f"{namespace}.")
                and event_id not in set(event_ids)
            }
            if undeclared_events:
                findings.append(
                    (
                        f"{name} has undeclared events: {', '.join(sorted(undeclared_events))}",
                        str(files["event"]),
                        1,
                    )
                )

            system_text = "\n".join(
                declared_text.get(role, "") for role in ("effect", "on_action", "event")
            )
            for event_id, markers in raw_system["lifecycle_markers"].items():
                if (
                    event_id not in event_ids
                    or not isinstance(markers, list)
                    or len(markers) != 3
                ):
                    findings.append(
                        (
                            f"{name} lifecycle declaration for {event_id} must list expected, pending, and resolved markers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                for marker in markers:
                    if str(marker) not in system_text:
                        findings.append(
                            (
                                f"{event_id} never uses lifecycle marker {marker}",
                                str(files["effect"]),
                                1,
                            )
                        )

            if re.search(r"\b(?:every_country|random_country)\s*=", system_text):
                findings.append(
                    (
                        f"{name} may not use every_country or random_country",
                        str(files["effect"]),
                        1,
                    )
                )
            participant_array = str(raw_system["participant_array"])
            raw_participant_tags = raw_system.get("participant_tags", [])
            participant_tags = (
                [str(tag) for tag in raw_participant_tags]
                if isinstance(raw_participant_tags, list)
                else []
            )
            on_action_text = declared_text.get("on_action", "")
            dispatcher_host = str(raw_system["dispatcher_host"])
            if schema_version >= 6:
                if participant_array or re.search(
                    r"\bglobal\.linux_system_participants\b", system_text
                ):
                    findings.append(
                        (
                            f"{name} must use country-local participation state without a global registry",
                            str(files["effect"]),
                            1,
                        )
                    )

                participant_tags_are_valid = self._participant_tags_are_valid(
                    raw_participant_tags
                )
                if not participant_tags_are_valid:
                    findings.append(
                        (
                            f"{name} must declare a non-empty list of unique three-character participant tags",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )

                on_action_texts: Dict[str, str] = {}
                on_action_dir = self._root / "common" / "on_actions"
                for path in sorted(on_action_dir.glob("*.txt")):
                    try:
                        on_action_texts[str(path)] = path.read_text(
                            encoding="utf-8-sig", errors="replace"
                        )
                    except OSError as exc:
                        findings.append(
                            (
                                f"{name} cannot read on-action file {path}: {exc}",
                                str(path),
                                1,
                            )
                        )

                driver_name = f"{root}_monthly_driver"
                participant_trigger_name = f"{root}_is_participant"
                monthly_defs = effect_defs.get(driver_name, [])
                participant_gate_is_present = len(monthly_defs) == 1 and bool(
                    re.search(
                        rf"\b{re.escape(participant_trigger_name)}\s*=\s*yes\b",
                        monthly_defs[0].body,
                    )
                )
                if dispatcher_host != "country_local":
                    findings.append(
                        (
                            f"{name} dispatcher_host must be country_local",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                if (
                    participant_tags_are_valid
                    and not self._participant_dispatch_is_exact(
                        on_action_texts, driver_name, participant_tags
                    )
                ):
                    findings.append(
                        (
                            f"{name} must call {driver_name} exactly once from each declared on_monthly_TAG host and nowhere else",
                            "common/on_actions",
                            1,
                        )
                    )
                if (
                    participant_tags_are_valid
                    and not self._participant_trigger_is_exact(
                        declared_text.get("trigger", ""),
                        participant_trigger_name,
                        participant_tags,
                    )
                ):
                    findings.append(
                        (
                            f"{participant_trigger_name} must contain exactly the declared participant tags",
                            str(files["trigger"]),
                            1,
                        )
                    )
                if not participant_gate_is_present:
                    findings.append(
                        (
                            f"{driver_name} must require {participant_trigger_name}",
                            str(files["effect"]),
                            1,
                        )
                    )
            else:
                if (
                    participant_array not in effect_text
                    or "is_in_array" not in effect_text
                    or "add_to_array" not in effect_text
                    or "remove_from_array" not in effect_text
                ):
                    findings.append(
                        (
                            f"{name} participant registry must deduplicate registration and support removal",
                            str(files["effect"]),
                            1,
                        )
                    )
                if (
                    f"{dispatcher_host} =" not in on_action_text
                    or "on_monthly" not in on_action_text
                ):
                    findings.append(
                        (
                            f"{name} must use {dispatcher_host} as its monthly dispatcher host",
                            str(files["on_action"]),
                            1,
                        )
                    )
                if re.search(
                    rf"\boriginal_tag\s*=\s*{re.escape(dispatcher_host)}\b",
                    system_text,
                ):
                    findings.append(
                        (
                            f"{dispatcher_host} may dispatch {name} but may not own gameplay state",
                            str(files["effect"]),
                            1,
                        )
                    )

            reconstruction_name = str(raw_system["reconstruction_effect"])
            reconstruction_defs = effect_defs.get(reconstruction_name, [])
            if len(reconstruction_defs) == 1:
                forbidden_reconstruction = (
                    "add_political_power",
                    "modify_treasury_effect",
                    "add_tech_bonus",
                    "add_timed_idea",
                    "add_stability",
                    "add_war_support",
                    "add_building_construction",
                )
                for effect in reachable_effects(reconstruction_name).values():
                    for token in forbidden_reconstruction:
                        if re.search(rf"\b{token}\b", effect.body):
                            findings.append(
                                (
                                    f"{reconstruction_name} transitively contains forbidden side effect {token} through {effect.name}",
                                    effect.file,
                                    effect.line,
                                )
                            )

            adoption_ideas = raw_system["adoption_ideas"]
            support_ideas = raw_system["support_ideas"]
            idea_ids = (
                adoption_ideas + support_ideas
                if isinstance(adoption_ideas, list) and isinstance(support_ideas, list)
                else []
            )
            idea_text = declared_text.get("idea", "")
            owned_timed_ideas = raw_system["owned_timed_ideas"]
            if not isinstance(owned_timed_ideas, list):
                owned_timed_ideas = []
                findings.append(
                    (
                        f"{name} owned_timed_ideas must be a list",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            all_owned_ideas = [*idea_ids, *owned_timed_ideas]
            for idea_id in all_owned_ideas:
                if (
                    len(
                        re.findall(
                            rf"(?m)^\s*{re.escape(str(idea_id))}\s*=\s*\{{", idea_text
                        )
                    )
                    != 1
                ):
                    findings.append(
                        (f"{name} missing idea {idea_id}", str(files["idea"]), 1)
                    )

            def normalize_modifier_contract(
                payload: object,
            ) -> Dict[str, Dict[str, Decimal]]:
                normalized: Dict[str, Dict[str, Decimal]] = {}
                if not isinstance(payload, dict):
                    return normalized
                for idea_id, modifiers in payload.items():
                    if not isinstance(modifiers, dict):
                        continue
                    try:
                        normalized[str(idea_id)] = {
                            str(modifier): Decimal(str(value))
                            for modifier, value in modifiers.items()
                        }
                    except (ValueError, TypeError):
                        continue
                return normalized

            expected_persistent_modifiers = {
                f"{root}_experimental_adoption": {},
                f"{root}_institutional_adoption": {
                    "research_speed_factor": Decimal("0.005"),
                    "offices_productivity": Decimal("0.005"),
                },
                f"{root}_infrastructure_standard": {
                    "research_speed_factor": Decimal("0.005"),
                    "country_productivity_growth_modifier": Decimal("0.005"),
                    "offices_productivity": Decimal("0.01"),
                    "cyber_defense_rating_modifier": Decimal("1"),
                },
                f"{root}_broad_economic_adoption": {
                    "research_speed_factor": Decimal("0.01"),
                    "country_productivity_growth_modifier": Decimal("0.01"),
                    "offices_productivity": Decimal("0.02"),
                    "corporate_tax_income_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_mixed_linux_estate": {
                    "research_speed_factor": Decimal("-0.01"),
                    "cyber_defense_rating_modifier": Decimal("-1"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_upstream_partnership": {
                    "research_speed_factor": Decimal("0.01"),
                    "receiving_investment_cost_modifier": Decimal("-0.025"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_enterprise_distribution": {
                    "offices_productivity": Decimal("0.01"),
                    "corporate_tax_income_multiplier_modifier": Decimal("0.01"),
                    "internal_investments_money_cost_modifier": Decimal("0.025"),
                },
                f"{root}_national_baseline": {
                    "cyber_defense_rating_modifier": Decimal("2"),
                    "research_speed_factor": Decimal("-0.005"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.02"),
                },
            }
            persistent_modifiers = normalize_modifier_contract(
                raw_system["persistent_idea_modifiers"]
            )
            if persistent_modifiers != expected_persistent_modifiers:
                findings.append(
                    (
                        f"{name} must declare the approved persistent economic modifier matrix",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            expected_timed_modifiers = {
                f"{root}_shared_updates_program": {
                    "research_speed_factor": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_national_signing_program": {
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.02")
                },
                f"{root}_upstream_maintenance_program": {
                    "research_speed_factor": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_enterprise_support_program": {
                    "country_productivity_growth_modifier": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("-0.01"),
                },
                f"{root}_lifecycle_hardening_program": {
                    "cyber_defense_rating_modifier": Decimal("2"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_public_procurement_program": {
                    "research_speed_factor": Decimal("0.01"),
                    "country_productivity_growth_modifier": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.02"),
                },
            }
            timed_modifiers = normalize_modifier_contract(
                raw_system["timed_idea_modifiers"]
            )
            if timed_modifiers != expected_timed_modifiers:
                findings.append(
                    (
                        f"{name} must declare the approved timed economic modifier matrix",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            declared_modifier_contract = {
                **persistent_modifiers,
                **timed_modifiers,
            }
            for idea_id, expected_modifiers in declared_modifier_contract.items():
                match = re.search(rf"(?m)^\s*{re.escape(idea_id)}\s*=\s*\{{", idea_text)
                if match is None:
                    continue
                idea_body, _ = extract_block_from_text(idea_text, match.end() - 1)
                modifier_match = re.search(r"\bmodifier\s*=\s*\{", idea_body)
                modifier_body = ""
                if modifier_match is not None:
                    modifier_body, _ = extract_block_from_text(
                        idea_body, modifier_match.end() - 1
                    )
                actual_modifiers = {
                    modifier: Decimal(value)
                    for modifier, value in re.findall(
                        r"(?m)^\s*([a-z][a-z0-9_]*)\s*=\s*"
                        r"(-?(?:\d+(?:\.\d*)?|\.\d+))\s*$",
                        strip_comments(modifier_body),
                    )
                }
                if actual_modifiers != expected_modifiers:
                    findings.append(
                        (
                            f"{idea_id} modifiers do not match the shared-system contract",
                            str(files["idea"]),
                            1,
                        )
                    )

            expected_programs = {
                f"{root}_fund_upstream_maintenance": {
                    "political_power": 25,
                    "gdp_fraction": 0.001,
                    "program_class": "operational",
                    "duration_days": 180,
                    "cooldown_days": 0,
                    "deployment": 0,
                    "stewardship": 1,
                    "assurance": 1,
                    "support_model": None,
                    "idea": f"{root}_upstream_maintenance_program",
                    "cleanup_owner": f"{root}_clear_country_state",
                },
                f"{root}_contract_enterprise_support": {
                    "political_power": 25,
                    "gdp_fraction": 0.001,
                    "program_class": "operational",
                    "duration_days": 180,
                    "cooldown_days": 0,
                    "deployment": 1,
                    "stewardship": 0,
                    "assurance": 1,
                    "support_model": 2,
                    "idea": f"{root}_enterprise_support_program",
                    "cleanup_owner": f"{root}_clear_country_state",
                },
                f"{root}_harden_lifecycle": {
                    "political_power": 35,
                    "gdp_fraction": 0.001,
                    "program_class": "major_commitment",
                    "duration_days": 365,
                    "cooldown_days": 0,
                    "deployment": 0,
                    "stewardship": 0,
                    "assurance": 2,
                    "support_model": None,
                    "idea": f"{root}_lifecycle_hardening_program",
                    "cleanup_owner": f"{root}_clear_country_state",
                },
                f"{root}_public_procurement": {
                    "political_power": 50,
                    "gdp_fraction": 0.002,
                    "program_class": "operational",
                    "duration_days": 180,
                    "cooldown_days": 0,
                    "deployment": 1,
                    "stewardship": 1,
                    "assurance": 1,
                    "support_model": None,
                    "idea": f"{root}_public_procurement_program",
                    "cleanup_owner": f"{root}_clear_country_state",
                },
            }
            if raw_system["programs"] != expected_programs:
                findings.append(
                    (
                        f"{name} must declare the approved program costs, durations, and state changes",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            program_effects = {
                f"{root}_fund_upstream_maintenance": (
                    f"{root}_apply_upstream_maintenance_program"
                ),
                f"{root}_contract_enterprise_support": (
                    f"{root}_apply_enterprise_support_program"
                ),
                f"{root}_harden_lifecycle": (
                    f"{root}_apply_lifecycle_hardening_program"
                ),
                f"{root}_public_procurement": (
                    f"{root}_apply_public_procurement_program"
                ),
            }
            decision_text = declared_text.get("decision", "")
            trigger_text = declared_text.get("trigger", "")
            category_text = declared_text.get("category", "")
            if f"{root}_full_enabled = yes" not in category_text:
                findings.append(
                    (
                        f"{name} decision category must be visible only in Full mode",
                        str(files["category"]),
                        1,
                    )
                )
            for program_id, program in expected_programs.items():
                findings.extend(
                    _program_lifecycle_findings(
                        program_id,
                        program,
                        "duration_days",
                        "sequential",
                        "tools/corporate_history_contract.json",
                    )
                )
                match = re.search(
                    rf"(?m)^\s*{re.escape(program_id)}\s*=\s*\{{", decision_text
                )
                if match is None:
                    findings.append(
                        (
                            f"{name} missing program {program_id}",
                            str(files["decision"]),
                            1,
                        )
                    )
                    continue
                decision_body, _ = extract_block_from_text(
                    decision_text, match.end() - 1
                )
                if not re.search(
                    rf"\bcost\s*=\s*{program['political_power']}\b", decision_body
                ) or not re.search(
                    rf"\bdays_remove\s*=\s*{program['duration_days']}\b",
                    decision_body,
                ):
                    findings.append(
                        (
                            f"{program_id} must use its declared PP cost and active duration",
                            str(files["decision"]),
                            1,
                        )
                    )
                if not _is_repeatable_decision(decision_body):
                    findings.append(
                        (
                            f"{program_id} must remain reusable after its declared cooldown",
                            str(files["decision"]),
                            1,
                        )
                    )
                for block_name in ("complete_effect", "remove_effect"):
                    block_match = re.search(rf"\b{block_name}\s*=\s*\{{", decision_body)
                    if block_match is None:
                        findings.append(
                            (
                                f"{program_id} is missing {block_name}",
                                str(files["decision"]),
                                1,
                            )
                        )
                        continue
                    block_body, _ = extract_block_from_text(
                        decision_body, block_match.end() - 1
                    )
                    if not re.match(r"\s*log\s*=", strip_comments(block_body)):
                        findings.append(
                            (
                                f"{program_id} {block_name} must log first",
                                str(files["decision"]),
                                1,
                            )
                        )
                    if block_name == "remove_effect":
                        cooldown_pattern = re.compile(
                            rf"set_country_flag\s*=\s*\{{\s*flag\s*=\s*"
                            rf"{root}_program_cooldown\s+days\s*=\s*"
                            rf"{program['cooldown_days']}\b"
                        )
                        if program["cooldown_days"] and not cooldown_pattern.search(
                            block_body
                        ):
                            findings.append(
                                (
                                    f"{program_id} must begin its declared cooldown "
                                    "when it ends",
                                    str(files["decision"]),
                                    1,
                                )
                            )
                        elif not program["cooldown_days"] and (
                            f"{root}_program_cooldown" in strip_comments(block_body)
                        ):
                            findings.append(
                                (
                                    f"{program_id} may not extend the shared slot after "
                                    "its active lifecycle",
                                    str(files["decision"]),
                                    1,
                                )
                            )
                if f"{root}_full_enabled = yes" not in decision_body:
                    findings.append(
                        (
                            f"{program_id} must be exposed only in Full mode",
                            str(files["decision"]),
                            1,
                        )
                    )
                if (
                    "has_active_mission = bankruptcy_incoming_collapse"
                    not in decision_body
                ):
                    findings.append(
                        (
                            f"{program_id} must block AI during bankruptcy collapse",
                            str(files["decision"]),
                            1,
                        )
                    )

                apply_name = program_effects[program_id]
                apply_defs = effect_defs.get(apply_name, [])
                if len(apply_defs) != 1:
                    findings.append(
                        (
                            f"{program_id} requires exactly one {apply_name}",
                            str(files["effect"]),
                            1,
                        )
                    )
                    continue
                apply_body = apply_defs[0].body
                gdp_suffix = "0_1" if program["gdp_fraction"] == 0.001 else "0_2"
                if f"{root}_pay_gdp_{gdp_suffix}_percent = yes" not in apply_body:
                    findings.append(
                        (
                            f"{apply_name} does not charge its declared GDP fraction",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                for axis in ("deployment", "stewardship", "assurance"):
                    delta = program[axis]
                    change = rf"add_to_variable\s*=\s*\{{\s*{root}_base_{axis}\s*=\s*{delta}\s*\}}"
                    if delta and not re.search(change, apply_body):
                        findings.append(
                            (
                                f"{apply_name} is missing {axis} {delta:+d}",
                                apply_defs[0].file,
                                apply_defs[0].line,
                            )
                        )
                support_model = program["support_model"]
                support_pattern = (
                    rf"set_variable\s*=\s*\{{\s*{root}_base_support_model\s*="
                )
                if support_model is None and re.search(support_pattern, apply_body):
                    findings.append(
                        (
                            f"{apply_name} may not change the support model",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                elif support_model is not None and not re.search(
                    support_pattern + rf"\s*{support_model}\s*\}}", apply_body
                ):
                    findings.append(
                        (
                            f"{apply_name} must set support model {support_model}",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                if not re.search(
                    rf"add_timed_idea\s*=\s*\{{\s*idea\s*=\s*{re.escape(str(program['idea']))}\s+days\s*=\s*{program['duration_days']}\s*\}}",
                    apply_body,
                ):
                    findings.append(
                        (
                            f"{apply_name} must apply its declared timed idea",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                if f"{root}_program_cooldown" in apply_body:
                    findings.append(
                        (
                            f"{apply_name} may not start cooldown before the program ends",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )

            if not all(
                str(program["idea"]) in trigger_text
                for program in expected_programs.values()
            ):
                findings.append(
                    (
                        f"{name} active-program trigger must cover all four program ideas",
                        str(files["trigger"]),
                        1,
                    )
                )
            procurement_match = re.search(
                rf"(?m)^\s*{root}_public_procurement\s*=\s*\{{", decision_text
            )
            if procurement_match is not None:
                procurement_body, _ = extract_block_from_text(
                    decision_text, procurement_match.end() - 1
                )
                if not re.search(
                    r"NOT\s*=\s*\{\s*original_tag\s*=\s*USA\s*\}",
                    procurement_body,
                ):
                    findings.append(
                        (
                            f"{root}_public_procurement must be hidden for USA",
                            str(files["decision"]),
                            1,
                        )
                    )
            refresh_name = str(raw_system["refresh_ideas_effect"])
            refresh_defs = effect_defs.get(refresh_name, [])
            if len(refresh_defs) == 1:
                refresh_body = refresh_defs[0].body
                refresh_owned_text = "\n".join(
                    effect.body for effect in reachable_effects(refresh_name).values()
                )
                missing_ideas = [
                    idea for idea in idea_ids if str(idea) not in refresh_owned_text
                ]
                if missing_ideas:
                    findings.append(
                        (
                            f"{refresh_name} does not own every declared idea: {', '.join(missing_ideas)}",
                            refresh_defs[0].file,
                            refresh_defs[0].line,
                        )
                    )
                if raw_system["excluded_generic_idea_tags"] != ["USA"] or not re.search(
                    r"NOT\s*=\s*\{\s*original_tag\s*=\s*USA\s*\}", refresh_body
                ):
                    findings.append(
                        (
                            f"{refresh_name} must exclude USA from both generic idea families",
                            refresh_defs[0].file,
                            refresh_defs[0].line,
                        )
                    )

            cleanup_name = str(raw_system["cleanup_effect"])
            cleanup_defs = effect_defs.get(cleanup_name, [])
            if len(cleanup_defs) == 1:
                cleanup_body = cleanup_defs[0].body
                cleanup_owned_text = "\n".join(
                    effect.body for effect in reachable_effects(cleanup_name).values()
                )
                cleanup_missing = [
                    idea
                    for idea in all_owned_ideas
                    if str(idea) not in cleanup_owned_text
                ]
                missing_participant_cleanup = (
                    schema_version < 6 and participant_array not in cleanup_body
                )
                if cleanup_missing or missing_participant_cleanup:
                    findings.append(
                        (
                            f"{cleanup_name} must remove every owned idea"
                            + (
                                " and the participant entry"
                                if schema_version < 6
                                else ""
                            ),
                            cleanup_defs[0].file,
                            cleanup_defs[0].line,
                        )
                    )
                active_decisions_missing = [
                    program_id
                    for program_id in expected_programs
                    if not _removes_active_decision(cleanup_owned_text, program_id)
                ]
                if active_decisions_missing:
                    findings.append(
                        (
                            f"{cleanup_name} must cancel every active program decision: "
                            f"{', '.join(active_decisions_missing)}",
                            cleanup_defs[0].file,
                            cleanup_defs[0].line,
                        )
                    )

            prefixes = tuple(
                str(prefix) for prefix in raw_system["native_write_prefixes"]
            )
            allowed_reads = {str(token) for token in raw_system["allowed_native_reads"]}
            native_contract_text = strip_comments(
                "\n".join(
                    declared_text.get(role, "") for role in _NATIVE_CONTRACT_ROLES
                )
            )
            native_reads: Set[str] = set()
            for pattern in (
                re.compile(
                    r"\b(?:has_country_flag|has_idea|has_completed_focus)\s*=\s*"
                    + _SCRIPT_TOKEN_CAPTURE
                ),
                re.compile(
                    r"\bcheck_variable\s*=\s*\{\s*(?:var\s*=\s*)?"
                    + _SCRIPT_TOKEN_CAPTURE
                ),
            ):
                for token in pattern.findall(native_contract_text):
                    fragment = _native_token_fragment(token, prefixes)
                    if fragment:
                        native_reads.add(fragment)
            undeclared_reads = native_reads - allowed_reads
            if undeclared_reads:
                findings.append(
                    (
                        f"{name} has undeclared native reads: {', '.join(sorted(undeclared_reads))}",
                        str(files["effect"]),
                        1,
                    )
                )
            unused_reads = allowed_reads - native_reads
            if unused_reads:
                findings.append(
                    (
                        f"{name} declares unused native reads: {', '.join(sorted(unused_reads))}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            native_writes = _collect_native_write_tokens(native_contract_text, prefixes)
            if native_writes:
                findings.append(
                    (
                        f"{name} writes native-system state: {', '.join(sorted(native_writes))}",
                        str(files["effect"]),
                        1,
                    )
                )

            localisation_files = files.get("localisation")
            if not isinstance(localisation_files, list) or not localisation_files:
                findings.append(
                    (
                        f"{name} requires declared English localisation files",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                localisation_text = ""
                for relative in localisation_files:
                    path = self._root / str(relative)
                    if not path.is_file():
                        findings.append(
                            (
                                f"{name} missing localisation file {relative}",
                                str(relative),
                                1,
                            )
                        )
                        continue
                    raw_bytes = path.read_bytes()
                    if not raw_bytes.startswith(b"\xef\xbb\xbf"):
                        findings.append(
                            (f"{relative} must retain a UTF-8 BOM", str(relative), 1)
                        )
                    localisation_text += (
                        raw_bytes.decode("utf-8-sig", errors="replace") + "\n"
                    )
                for key in raw_system["localisation_keys"]:
                    if not re.search(
                        rf"(?m)^ {re.escape(str(key))}:\d*\s", localisation_text
                    ):
                        findings.append(
                            (
                                f"{name} missing localisation key {key}",
                                str(localisation_files[0]),
                                1,
                            )
                        )

            integration_files = files.get("integration")
            integration_text = ""
            if isinstance(integration_files, list):
                for relative in integration_files:
                    path = self._root / str(relative)
                    if path.is_file():
                        integration_text += (
                            path.read_text(encoding="utf-8-sig", errors="replace")
                            + "\n"
                        )
            for event_id, markers in raw_system["storage_lifecycle_markers"].items():
                if not isinstance(markers, list) or len(markers) != 3:
                    findings.append(
                        (
                            f"{name} storage lifecycle declaration for {event_id} must list expected, pending, and resolved markers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                for marker in markers:
                    if str(marker) not in integration_text:
                        findings.append(
                            (
                                f"{event_id} never uses lifecycle marker {marker}",
                                str(files["integration"][0]),
                                1,
                            )
                        )

            ibm_event_text = declared_text.get("ibm_event", "")
            added_ibm_events = sorted(
                number
                for number in (
                    int(value)
                    for value in re.findall(
                        r"\bid\s*=\s*USA_ibm_events\.(\d+)", ibm_event_text
                    )
                )
                if number > 50 and number != 90
            )
            if added_ibm_events:
                findings.append(
                    (
                        f"IBM story events may not extend beyond .50: {added_ibm_events}",
                        str(files["ibm_event"]),
                        1,
                    )
                )

            bridge_name = str(raw_system["usa_bridge_effect"])
            bridge_defs = effect_defs.get(bridge_name, [])
            if len(bridge_defs) != 1:
                findings.append(
                    (
                        f"{name} requires exactly one {bridge_name}; found {len(bridge_defs)}",
                        str(files["bridge"]),
                        bridge_defs[0].line if bridge_defs else 1,
                    )
                )
            else:
                bridge_body = bridge_defs[0].body
                required_base_reads = (
                    f"{root}_base_deployment",
                    f"{root}_base_stewardship",
                    f"{root}_base_assurance",
                    f"{root}_base_support_model",
                )
                if not all(token in bridge_body for token in required_base_reads):
                    findings.append(
                        (
                            f"{bridge_name} must read all four generic base-state inputs",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )
                if (
                    f"{root}_adapter_" in bridge_body
                    or f"{root}_effective_" in bridge_body
                ):
                    findings.append(
                        (
                            f"{bridge_name} may not read adapter or effective Linux state",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )
                contribution_changes = re.findall(
                    r"(?:add_to_temp_variable|subtract_from_temp_variable)\s*=\s*\{\s*"
                    r"USA_oem_contribution_[A-Za-z0-9_]+\s*=\s*"
                    r"(-?(?:\d+(?:\.\d*)?|\.\d+))\s*\}",
                    bridge_body,
                )
                if any(abs(float(value)) > 1 for value in contribution_changes):
                    findings.append(
                        (
                            f"{bridge_name} contributions must be limited to one point per axis",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )

        return findings

    def _validate_mode_contract(
        self, mode_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        rule_defs = mode_defs.get("rule_corporate_history", [])
        if len(rule_defs) != 1:
            return [
                (
                    f"rule_corporate_history requires exactly one definition; found {len(rule_defs)}",
                    "common/game_rules/00_game_rules.txt",
                    rule_defs[0].line if rule_defs else 0,
                )
            ]

        rule = rule_defs[0]
        options: List[Tuple[str, str]] = []
        for child, _start, _end, body in self._iter_direct_child_blocks(rule.body):
            if child not in ("default", "option"):
                continue
            name = re.search(r"\bname\s*=\s*([A-Za-z0-9_]+)", body)
            if name:
                options.append((child, name.group(1)))
        if options != [
            ("default", "full"),
            ("option", "outcomes_only"),
            ("option", "disabled"),
        ]:
            findings.append(
                (
                    "rule_corporate_history must define Full, Outcomes Only, and Disabled in that order",
                    rule.file,
                    rule.line,
                )
            )

        full = mode_defs.get("corporate_history_full_enabled", [])
        outcomes = mode_defs.get("corporate_history_outcomes_only_enabled", [])
        enabled = mode_defs.get("corporate_history_enabled", [])
        expected_rule_checks = {
            "corporate_history_full_enabled": ("outcomes_only", "disabled"),
            "corporate_history_outcomes_only_enabled": ("outcomes_only",),
        }
        for name, defs in (
            ("corporate_history_full_enabled", full),
            ("corporate_history_outcomes_only_enabled", outcomes),
            ("corporate_history_enabled", enabled),
        ):
            if len(defs) != 1:
                findings.append(
                    (
                        f"{name} requires exactly one definition; found {len(defs)}",
                        "common/scripted_triggers/MD_corporate_history_triggers.txt",
                        defs[0].line if defs else 0,
                    )
                )
        if len(full) == 1:
            body = full[0].body
            for option in expected_rule_checks["corporate_history_full_enabled"]:
                pattern = (
                    r"NOT\s*=\s*\{\s*has_game_rule\s*=\s*\{\s*rule\s*=\s*"
                    r"rule_corporate_history\s+option\s*=\s*" + option + r"\s*\}\s*\}"
                )
                if not re.search(pattern, body):
                    findings.append(
                        (
                            f"corporate_history_full_enabled does not exclude {option}",
                            full[0].file,
                            full[0].line,
                        )
                    )
        if len(outcomes) == 1 and not re.search(
            r"has_game_rule\s*=\s*\{\s*rule\s*=\s*rule_corporate_history\s+option\s*=\s*outcomes_only\s*\}",
            outcomes[0].body,
        ):
            findings.append(
                (
                    "corporate_history_outcomes_only_enabled does not select outcomes_only",
                    outcomes[0].file,
                    outcomes[0].line,
                )
            )
        if len(enabled) == 1 and not all(
            marker in enabled[0].body
            for marker in (
                "corporate_history_full_enabled = yes",
                "corporate_history_outcomes_only_enabled = yes",
            )
        ):
            findings.append(
                (
                    "corporate_history_enabled must combine Full and Outcomes Only",
                    enabled[0].file,
                    enabled[0].line,
                )
            )
        return findings

    def _validate_lifecycle_metadata(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        schema_v6 = int(self._manifest_payload.get("schema_version", 1)) >= 6
        startup_defs = effect_defs.get("corporate_history_on_startup", [])
        startup_full_branches = [
            self._startup_full_branch(startup.body) for startup in startup_defs
        ]
        startup_outcomes_branches = [
            self._startup_outcomes_branch(startup.body) for startup in startup_defs
        ]
        bootstrap_defs = effect_defs.get("corporate_history_country_bootstrap", [])
        bootstrap_branches: Dict[str, List[str]] = {}

        def country_branches(tag: str) -> List[str]:
            if tag not in bootstrap_branches:
                bootstrap_branches[tag] = [
                    branch
                    for bootstrap in bootstrap_defs
                    for branch in self._country_bootstrap_tag_branches(
                        bootstrap.body, tag
                    )
                ]
            return bootstrap_branches[tag]

        for chain in chains:
            if (
                "reconstruction" in chain.full_start_strategies
                or chain.outcomes_only_strategy == "reconstruction"
            ):
                findings.extend(
                    self._validate_terminal_date(
                        chain.name,
                        chain.reconstruct_effect,
                        chain.completion_flag,
                        chain.terminal_date,
                        effect_defs,
                    )
                )
            for lifecycle in chain.auxiliary_lifecycles:
                findings.extend(
                    self._validate_terminal_date(
                        f"{chain.name} auxiliary {lifecycle.root}",
                        lifecycle.reconstruction_effect,
                        lifecycle.terminal_marker,
                        lifecycle.terminal_date,
                        effect_defs,
                    )
                )
                reconstruction = effect_defs.get(lifecycle.reconstruction_effect, [])
                scheduler = effect_defs.get(lifecycle.scheduler_effect, [])
                if len(reconstruction) != 1:
                    findings.append(
                        (
                            f"{lifecycle.root} requires exactly one reconstruction effect {lifecycle.reconstruction_effect}",
                            "common/scripted_effects",
                            reconstruction[0].line if reconstruction else 0,
                        )
                    )
                if len(scheduler) != 1:
                    findings.append(
                        (
                            f"{lifecycle.root} requires exactly one scheduler effect {lifecycle.scheduler_effect}",
                            "common/scripted_effects",
                            scheduler[0].line if scheduler else 0,
                        )
                    )
                    continue
                if schema_v6:
                    local_branches = country_branches(lifecycle.tag)
                    reconstruction_calls = sum(
                        self._direct_effect_call_count(
                            branch, lifecycle.reconstruction_effect
                        )
                        for branch in local_branches
                    )
                    if reconstruction_calls != 1:
                        findings.append(
                            (
                                f"{lifecycle.reconstruction_effect} requires exactly one direct {lifecycle.tag} country-bootstrap registration; found {reconstruction_calls}",
                                "common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt",
                                bootstrap_defs[0].line if bootstrap_defs else 0,
                            )
                        )
                    full_branches = [
                        full_branch
                        for branch in local_branches
                        for full_branch in self._country_bootstrap_full_branches(branch)
                    ]
                    scheduler_calls = sum(
                        len(
                            re.findall(
                                rf"\b{re.escape(lifecycle.scheduler_effect)}\s*=\s*yes\b",
                                branch,
                            )
                        )
                        for branch in full_branches
                    )
                    if scheduler_calls != 1:
                        findings.append(
                            (
                                f"{lifecycle.scheduler_effect} requires exactly one Full-mode {lifecycle.tag} country-bootstrap registration; found {scheduler_calls}",
                                "common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt",
                                bootstrap_defs[0].line if bootstrap_defs else 0,
                            )
                        )
                else:
                    if not any(
                        f"{lifecycle.reconstruction_effect} = yes" in branch
                        for branch in startup_full_branches
                    ):
                        findings.append(
                            (
                                f"{lifecycle.reconstruction_effect} is not registered in the Full startup branch",
                                "common/scripted_effects/00_corporate_history_effects.txt",
                                0,
                            )
                        )
                    if not any(
                        f"{lifecycle.reconstruction_effect} = yes" in branch
                        for branch in startup_outcomes_branches
                    ):
                        findings.append(
                            (
                                f"{lifecycle.reconstruction_effect} is not registered in the Outcomes Only startup branch",
                                "common/scripted_effects/00_corporate_history_effects.txt",
                                0,
                            )
                        )
                    if not any(
                        f"{lifecycle.scheduler_effect} = yes" in branch
                        for branch in startup_full_branches
                    ):
                        findings.append(
                            (
                                f"{lifecycle.scheduler_effect} is not registered in the Full startup branch",
                                "common/scripted_effects/00_corporate_history_effects.txt",
                                0,
                            )
                        )
                monthly = effect_defs.get(lifecycle.monthly_driver, [])
                if (
                    len(monthly) != 1
                    or f"{lifecycle.reconstruction_effect} = yes" not in monthly[0].body
                    or lifecycle.terminal_marker not in monthly[0].body
                ):
                    findings.append(
                        (
                            f"{lifecycle.reconstruction_effect} lacks a completion-guarded call from {lifecycle.monthly_driver}",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            monthly[0].line if monthly else 0,
                        )
                    )

                scheduled_events = {
                    target
                    for target, _line in self._find_event_calls(
                        scheduler[0].body, scheduler[0].line, frozenset()
                    )
                }
                expected_events = set(lifecycle.expected_yearly_callers)
                if scheduled_events != expected_events:
                    findings.append(
                        (
                            f"{lifecycle.scheduler_effect} events differ from expected_yearly_callers: expected {', '.join(sorted(expected_events)) or 'none'}; found {', '.join(sorted(scheduled_events)) or 'none'}",
                            scheduler[0].file,
                            scheduler[0].line,
                        )
                    )
                for event_id, dispatcher in lifecycle.expected_yearly_callers.items():
                    event = event_defs.get(event_id)
                    if event is None:
                        findings.append(
                            (
                                f"{lifecycle.root} expected yearly event {event_id} is undefined",
                                scheduler[0].file,
                                scheduler[0].line,
                            )
                        )
                        continue
                    actual_yearly = {
                        caller.owner
                        for caller in self._dedupe_callers(call_sites.get(event_id, []))
                        if caller.kind == "effect"
                        and "_corporate_trigger_year_" in caller.owner
                    }
                    if actual_yearly != {dispatcher}:
                        findings.append(
                            (
                                f"{event_id} yearly callers differ from the auxiliary lifecycle: expected {dispatcher}; found {', '.join(sorted(actual_yearly)) or 'none'}",
                                event.file,
                                event.line,
                            )
                        )
                    scheduler_callers = {
                        caller.owner
                        for caller in self._dedupe_callers(call_sites.get(event_id, []))
                        if caller.kind == "effect"
                        and caller.owner == lifecycle.scheduler_effect
                    }
                    if scheduler_callers != {lifecycle.scheduler_effect}:
                        findings.append(
                            (
                                f"{event_id} is not called by auxiliary scheduler {lifecycle.scheduler_effect}",
                                event.file,
                                event.line,
                            )
                        )
                    year_match = re.search(
                        r"_corporate_trigger_year_(\d{4})$", dispatcher
                    )
                    expected_year = int(year_match.group(1)) if year_match else -1
                    windows = self._scheduler_window_years(scheduler[0], event_id)
                    if windows != {expected_year}:
                        findings.append(
                            (
                                f"{lifecycle.scheduler_effect} must schedule {event_id} only in the {expected_year} January 1 window; found {', '.join(str(year) for year in sorted(windows)) or 'none'}",
                                scheduler[0].file,
                                scheduler[0].line,
                            )
                        )
        return self._dedupe_findings(findings)

    def _validate_terminal_date(
        self,
        label: str,
        reconstruction_effect: str,
        terminal_marker: str,
        terminal_date: str,
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        definitions = effect_defs.get(reconstruction_effect, [])
        if len(definitions) != 1:
            return [
                (
                    f"{label} terminal date cannot be checked without exactly one {reconstruction_effect}",
                    "common/scripted_effects",
                    definitions[0].line if definitions else 0,
                )
            ]
        try:
            parsed = date.fromisoformat(terminal_date)
        except ValueError:
            return [
                (
                    f"{label} has invalid terminal_date {terminal_date}",
                    "tools/corporate_history_contract.json",
                    0,
                )
            ]
        expected = f"{parsed.year}.{parsed.month}.{parsed.day}"
        actual = self._terminal_guard_dates(definitions[0].body, terminal_marker)
        if actual == {expected}:
            return []
        return [
            (
                f"{label} terminal marker {terminal_marker} must use date > {expected}; found {', '.join(sorted(actual)) or 'none'}",
                definitions[0].file,
                definitions[0].line,
            )
        ]

    def _terminal_guard_dates(self, body: str, marker: str) -> Set[str]:
        dates: Set[str] = set()
        marker_pattern = re.compile(
            rf"\bset_country_flag\s*=\s*(?:{re.escape(marker)}\b|\{{\s*flag\s*=\s*{re.escape(marker)}\b)"
        )
        for name, _start, _end, child in self._iter_direct_child_blocks(body):
            limit = self._direct_child_block(child, "limit")
            if name in ("if", "else_if") and limit and marker_pattern.search(child):
                dates.update(
                    re.findall(r"\bdate\s*>\s*(\d{4}\.\d{1,2}\.\d{1,2})", limit)
                )
            dates.update(self._terminal_guard_dates(child, marker))
        return dates

    def _validate_core_chain_mode_paths(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
    ) -> List[Tuple[str, str, int]]:
        if int(self._manifest_payload.get("schema_version", 1)) < 6:
            return []

        findings: List[Tuple[str, str, int]] = []
        chain_events: Dict[str, ChainConfig] = {
            event_id: chain
            for chain in chains
            for event_id in event_defs
            if event_id.startswith(chain.namespace + ".")
        }
        core_event_ids = set(chain_events)
        all_event_ids = frozenset(event_defs)
        event_parents: Dict[str, Set[str]] = defaultdict(set)
        for source_id, event in event_defs.items():
            for target_id, _line in self._find_event_calls(
                event.body, event.line, all_event_ids
            ):
                event_parents[target_id].add(source_id)

        relevant_events = set(core_event_ids)
        pending_events = list(core_event_ids)
        while pending_events:
            event_id = pending_events.pop()
            for parent in event_parents.get(event_id, ()):
                if parent in relevant_events:
                    continue
                relevant_events.add(parent)
                pending_events.append(parent)

        (
            effect_modes,
            event_modes,
            effect_traces,
            event_traces,
        ) = self._independent_mode_graph(
            effect_defs,
            relevant_events,
            event_defs_for_expansion=event_defs,
        )

        def require_modes(
            symbol: str,
            modes: Set[str],
            traces: Mapping[Tuple[str, str], Sequence[ModeTrace]],
            required: Set[str],
            label: str,
            file: str,
            line: int,
            expected_host: Optional[str] = None,
        ) -> None:
            missing = required - modes
            if missing:
                findings.append(
                    (
                        f"{label} {symbol} is unreachable in: {', '.join(sorted(missing))}",
                        file,
                        line,
                    )
                )
            for forbidden_mode in ("outcomes_only", "off"):
                if forbidden_mode in required or forbidden_mode not in modes:
                    continue
                trace = traces[(symbol, forbidden_mode)][0]
                findings.append(
                    (
                        f"{label} {symbol} is reachable in {forbidden_mode} mode",
                        trace.file,
                        trace.line,
                    )
                )
            for mode in modes:
                for trace in traces.get((symbol, mode), ()):
                    if not trace.host.startswith("on_monthly"):
                        findings.append(
                            (
                                f"{label} {symbol} is reached from forbidden host {trace.host}",
                                trace.host_file,
                                trace.line,
                            )
                        )
                    elif expected_host and trace.host != expected_host:
                        findings.append(
                            (
                                f"{label} {symbol} is reached from {trace.host}; expected {expected_host}",
                                trace.host_file,
                                trace.line,
                            )
                        )

        for chain in chains:
            expected_host = f"on_monthly_{chain.tag}"
            reconstruct_defs = effect_defs.get(chain.reconstruct_effect, [])
            reconstruct_required: Set[str] = set()
            if "reconstruction" in chain.full_start_strategies:
                reconstruct_required.add("full")
            if chain.outcomes_only_strategy == "reconstruction":
                reconstruct_required.add("outcomes_only")
            if reconstruct_required:
                require_modes(
                    chain.reconstruct_effect,
                    effect_modes.get(chain.reconstruct_effect, set()),
                    effect_traces,
                    reconstruct_required,
                    "Reconstruction effect",
                    (
                        reconstruct_defs[0].file
                        if reconstruct_defs
                        else "common/scripted_effects"
                    ),
                    reconstruct_defs[0].line if reconstruct_defs else 1,
                    expected_host,
                )

            scheduler_modes = effect_modes.get(chain.scheduler_effect, set())
            if scheduler_modes:
                scheduler_defs = effect_defs.get(chain.scheduler_effect, [])
                require_modes(
                    chain.scheduler_effect,
                    scheduler_modes,
                    effect_traces,
                    {"full"},
                    "Current-year scheduler",
                    (
                        scheduler_defs[0].file
                        if scheduler_defs
                        else "common/scripted_effects"
                    ),
                    scheduler_defs[0].line if scheduler_defs else 1,
                    expected_host,
                )

        for event_id, chain in sorted(chain_events.items()):
            event = event_defs[event_id]
            expected_callers = chain.expected_callers.get(event_id)
            if expected_callers == () or event_id in chain.callerless_anchors:
                continue
            for caller in self._dedupe_callers(call_sites.get(event_id, [])):
                if caller.kind == "script":
                    findings.append(
                        (
                            f"Core event {event_id} has unregistered direct script caller {caller.owner}",
                            caller.file,
                            caller.line,
                        )
                    )
            require_modes(
                event_id,
                event_modes.get(event_id, set()),
                event_traces,
                {"full"},
                "Core event",
                event.file,
                event.line,
            )

        return self._dedupe_findings(findings)

    def _validate_tier_one_contract(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        idea_defs: Dict[str, IdeaDef],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        schema_v6 = int(self._manifest_payload.get("schema_version", 1)) >= 6
        startup_defs = effect_defs.get("corporate_history_on_startup", [])
        startup_full_branches = [
            self._startup_full_branch(startup.body) for startup in startup_defs
        ]
        startup_outcomes_branches = [
            self._startup_outcomes_branch(startup.body) for startup in startup_defs
        ]
        monthly_defs = {
            name: defs[0] for name, defs in effect_defs.items() if len(defs) == 1
        }
        bootstrap_defs = effect_defs.get("corporate_history_country_bootstrap", [])
        bootstrap_branches: Dict[str, List[str]] = {}

        def country_branches(tag: str) -> List[str]:
            if tag not in bootstrap_branches:
                bootstrap_branches[tag] = [
                    branch
                    for bootstrap in bootstrap_defs
                    for branch in self._country_bootstrap_tag_branches(
                        bootstrap.body, tag
                    )
                ]
            return bootstrap_branches[tag]

        if not schema_v6:
            startup_callers = self._script_effect_call_sites(
                "corporate_history_on_startup"
            )
            if len(startup_callers) != 1:
                findings.append(
                    (
                        f"corporate_history_on_startup requires exactly one on-action caller; found {len(startup_callers)}",
                        (
                            startup_callers[0][0]
                            if startup_callers
                            else "common/on_actions/00_on_actions.txt"
                        ),
                        startup_callers[0][1] if startup_callers else 0,
                    )
                )
        for driver in sorted({chain.monthly_driver for chain in chains}):
            driver_callers = self._script_effect_call_sites(driver)
            if len(driver_callers) != 1:
                findings.append(
                    (
                        f"{driver} requires exactly one matching on-monthly caller; found {len(driver_callers)}",
                        driver_callers[0][0] if driver_callers else "common/on_actions",
                        driver_callers[0][1] if driver_callers else 0,
                    )
                )

        for chain in chains:
            if chain.outcomes_only_strategy == "reconstruction":
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.reconstruct_effect,
                        f"{chain.name} is missing its declared Outcomes Only reconstruction effect",
                    )
                )
                if not self._flag_is_produced(chain.completion_flag, effect_defs):
                    findings.append(
                        (
                            f"{chain.completion_flag} is never produced",
                            f"common/scripted_effects/{chain.root}_effects.txt",
                            0,
                        )
                    )
                if schema_v6:
                    reconstruction_calls = sum(
                        self._direct_effect_call_count(branch, chain.reconstruct_effect)
                        for branch in country_branches(chain.tag)
                    )
                    startup_anchor_ids = [
                        event_id
                        for event_id, callers in chain.expected_callers.items()
                        if event_id.endswith(".90")
                        and callers == ("effect:corporate_history_country_bootstrap",)
                        and (startup_anchor := event_defs.get(event_id)) is not None
                        and any(
                            f"{chain.reconstruct_effect} = yes" in immediate.body
                            for immediate in startup_anchor.immediates
                        )
                    ]
                    startup_anchor_calls = sum(
                        len(self._direct_event_calls(branch, event_id))
                        + len(self._event_guard_branches(branch, event_id))
                        for event_id in startup_anchor_ids
                        for branch in country_branches(chain.tag)
                    )
                    registrations = reconstruction_calls + startup_anchor_calls
                    if registrations != 1:
                        findings.append(
                            (
                                f"{chain.reconstruct_effect} requires exactly one direct or documented startup-anchor {chain.tag} country-bootstrap registration; found {registrations}",
                                "common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt",
                                bootstrap_defs[0].line if bootstrap_defs else 0,
                            )
                        )
                elif not any(
                    f"{chain.reconstruct_effect} = yes" in branch
                    for branch in startup_outcomes_branches
                ):
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} is not registered in the Outcomes Only startup branch",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            0,
                        )
                    )
                monthly = monthly_defs.get(chain.monthly_driver)
                if (
                    monthly is None
                    or f"{chain.reconstruct_effect} = yes" not in monthly.body
                    or chain.completion_flag not in monthly.body
                ):
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} lacks a completion-guarded call from {chain.monthly_driver}",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            monthly.line if monthly else 0,
                        )
                    )
            if "current_year_scheduler" in chain.full_start_strategies:
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.scheduler_effect,
                        f"{chain.name} is missing its declared current-year scheduler",
                    )
                )
                if not schema_v6 and not any(
                    self._startup_reaches_scheduler(chain, branch, event_defs)
                    for branch in startup_full_branches
                ):
                    findings.append(
                        (
                            f"{chain.scheduler_effect} is not reachable from the Full startup branch",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            0,
                        )
                    )
            if chain.tier != 1:
                continue
            if chain.variables:
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.initialize_effect,
                        f"{chain.name} is missing its initialization effect",
                    )
                )
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.clamp_effect,
                        f"{chain.name} is missing its clamp effect",
                    )
                )
            findings.extend(
                self._require_effect(
                    effect_defs,
                    chain.reconstruct_effect,
                    f"{chain.name} is missing its reconstruction effect",
                )
            )
            event_90 = event_defs.get(chain.hidden_ninety_id)
            if schema_v6:
                reconstruction_anchor = any(
                    self._direct_effect_call_count(branch, chain.reconstruct_effect)
                    for branch in country_branches(chain.tag)
                )
                reconstruction_host = "corporate_history_country_bootstrap"
            else:
                reconstruction_anchor = any(
                    f"{chain.reconstruct_effect} = yes" in branch
                    for branch in startup_full_branches
                )
                reconstruction_host = "corporate_history_on_startup"
            if (event_90 is None or not event_90.hidden) and not reconstruction_anchor:
                file = f"events/{chain.namespace}.txt"
                line = event_90.line if event_90 else 0
                findings.append(
                    (
                        f"{chain.hidden_ninety_id} is missing or not hidden and "
                        f"{chain.reconstruct_effect} is not called directly from "
                        f"{reconstruction_host}",
                        event_90.file if event_90 else file,
                        line,
                    )
                )
            if not self._flag_is_produced(chain.completion_flag, effect_defs):
                findings.append(
                    (
                        f"{chain.completion_flag} is never produced",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            if schema_v6:
                if not any(
                    self._chain_is_registered_in_startup(chain, branch)
                    for branch in country_branches(chain.tag)
                ):
                    findings.append(
                        (
                            f"{chain.name} is missing its {chain.tag} registration in corporate_history_country_bootstrap",
                            "common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt",
                            bootstrap_defs[0].line if bootstrap_defs else 0,
                        )
                    )
            elif not startup_defs or not any(
                self._chain_is_registered_in_startup(chain, startup.body)
                for startup in startup_defs
            ):
                findings.append(
                    (
                        f"{chain.name} is missing startup registration in corporate_history_on_startup",
                        "common/scripted_effects/00_corporate_history_effects.txt",
                        0,
                    )
                )
            monthly = monthly_defs.get(chain.monthly_driver)
            if (
                monthly is None
                or f"{chain.reconstruct_effect} = yes" not in monthly.body
            ):
                findings.append(
                    (
                        f"{chain.reconstruct_effect} is not called from {chain.monthly_driver}",
                        "common/scripted_effects/00_corporate_history_effects.txt",
                        monthly.line if monthly else 0,
                    )
                )
            if (
                chain.requires_current_year_scheduler
                and chain.scheduler_effect not in effect_defs
            ):
                findings.append(
                    (
                        f"{chain.name} is missing its current-year scheduler {chain.scheduler_effect}",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            if not self._has_terminal_resolver(chain, effect_defs):
                findings.append(
                    (
                        f"{chain.name} is missing a terminal resolver effect",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            outcome_ids = self._outcome_ideas_for_chain(chain, idea_defs)
            if not outcome_ids:
                findings.append(
                    (
                        f"{chain.name} has no permanent outcome ideas registered under {', '.join(chain.outcome_idea_prefixes)}",
                        f"common/ideas/{chain.root}_ideas.txt",
                        0,
                    )
                )
            if not self._has_cleanup_path(chain, effect_defs, event_defs, outcome_ids):
                findings.append(
                    (
                        f"{chain.name} is missing a mutually exclusive cleanup effect",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            for idea_id in sorted(outcome_ids):
                idea = idea_defs.get(idea_id)
                if idea is None:
                    findings.append(
                        (
                            f"Missing outcome idea definition {idea_id}",
                            f"common/ideas/{chain.root}_ideas.txt",
                            0,
                        )
                    )
                    continue
                if not re.search(
                    rf"\ballowed\s*=\s*\{{\s*original_tag\s*=\s*{re.escape(chain.tag)}\s*\}}",
                    idea.body,
                ):
                    findings.append(
                        (
                            f"{idea_id} is missing allowed = {{ original_tag = {chain.tag} }}",
                            idea.file,
                            idea.line,
                        )
                    )
                if not re.search(
                    r"\ballowed_civil_war\s*=\s*\{\s*always\s*=\s*yes\s*\}",
                    idea.body,
                ):
                    findings.append(
                        (
                            f"{idea_id} is missing allowed_civil_war = {{ always = yes }}",
                            idea.file,
                            idea.line,
                        )
                    )
        return findings

    def _validate_clamp_coverage(
        self,
        chains: Sequence[ChainConfig],
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        effect_lookup = {name: defs[0] for name, defs in effect_defs.items() if defs}
        for chain in chains:
            if not chain.variables:
                continue
            clamp = effect_lookup.get(chain.clamp_effect)
            if clamp is not None:
                reachable_clamps = self._reachable_chain_effects(
                    chain, clamp, effect_lookup
                )
                declared_bounds: Dict[str, Tuple[Decimal, Decimal]] = {}
                for effect in reachable_clamps.values():
                    declared_bounds.update(
                        {
                            match.group(1): (
                                Decimal(match.group(2)),
                                Decimal(match.group(3)),
                            )
                            for match in _CLAMP_VAR_RE.finditer(effect.body)
                        }
                    )
                    declared_bounds.update(self._indirect_temp_clamps(effect.body))
                for variable, bound in chain.variables.items():
                    expected = (bound.minimum, bound.maximum)
                    standard_clamp = expected == (0, 10) and re.search(
                        rf"\bset_temp_variable\s*=\s*\{{\s*corp_value\s*=\s*{re.escape(variable)}\s*\}}"
                        rf".*?\bcorporate_history_clamp_value\s*=\s*yes\b"
                        rf".*?\bset_variable\s*=\s*\{{\s*{re.escape(variable)}\s*=\s*corp_value\s*\}}",
                        "\n".join(effect.body for effect in reachable_clamps.values()),
                        re.DOTALL,
                    )
                    if declared_bounds.get(variable) != expected and not standard_clamp:
                        findings.append(
                            (
                                f"{chain.clamp_effect} must clamp {variable} to manifest bounds {bound.minimum}..{bound.maximum}",
                                clamp.file,
                                clamp.line,
                            )
                        )
            saw_clamped_option = False
            saw_mutating_option = False
            for event in event_defs.values():
                if not event.event_id.startswith(chain.namespace + "."):
                    continue
                for option in [*event.options, *event.immediates]:
                    pending, used_clamp, mutated = self._trace_mutation_path(
                        option.body, chain, effect_lookup, set()
                    )
                    if not mutated:
                        continue
                    saw_mutating_option = True
                    if used_clamp:
                        saw_clamped_option = True
                    if pending:
                        findings.append(
                            (
                                f"{event.event_id} option at line {option.line} mutates bounded variables without a later {chain.clamp_effect} call",
                                option.file,
                                option.line,
                            )
                        )
            if saw_mutating_option and not saw_clamped_option:
                findings.append(
                    (
                        f"{chain.name} clamps bounded variables only at initialization",
                        f"events/{chain.namespace}.txt",
                        0,
                    )
                )
        return findings

    def _indirect_temp_clamps(self, body: str) -> Dict[str, Tuple[int, int]]:
        pattern = re.compile(
            r"\bset_temp_variable\s*=\s*\{\s*corp_value\s*=\s*([A-Za-z0-9_]+)\s*\}"
            r".*?\bclamp_temp_variable\s*=\s*\{\s*var\s*=\s*corp_value\s+min\s*=\s*(-?\d+)\s+max\s*=\s*(-?\d+)\s*\}"
            r".*?\bset_variable\s*=\s*\{\s*\1\s*=\s*corp_value\s*\}",
            re.DOTALL,
        )
        return {
            match.group(1): (int(match.group(2)), int(match.group(3)))
            for match in pattern.finditer(body)
        }

    def _validate_reconstruction_safety(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        effect_lookup = {name: defs[0] for name, defs in effect_defs.items() if defs}
        for chain in chains:
            reconstruct = effect_lookup.get(chain.reconstruct_effect)
            if reconstruct is None:
                continue
            reachable = self._reachable_chain_effects(chain, reconstruct, effect_lookup)
            for effect in reachable.values():
                for label, pattern in _CUSTOM_EFFECT_REWARDS:
                    if pattern.search(effect.body):
                        findings.append(
                            (
                                f"{chain.reconstruct_effect} transitively replays {label} through {effect.name}",
                                effect.file,
                                effect.line,
                            )
                        )
                event_calls = self._find_event_calls(
                    effect.body, effect.line, frozenset()
                )
                for target, line in event_calls:
                    event = event_defs.get(target)
                    target_namespace = target.split(".", 1)[0]
                    is_declared_cross_chain = any(
                        target.startswith(prefix) for prefix in chain.allowed_writes
                    )
                    is_delivery_effect = "_schedule_" in effect.name
                    has_silent_catchup_guard = (
                        f"NOT = {{ has_country_flag = {chain.root}_catchup_silent }}"
                        in effect.body
                        and f"set_country_flag = {chain.root}_catchup_silent"
                        in reconstruct.body
                    )
                    if (event is not None and event.hidden) or is_delivery_effect:
                        continue
                    if has_silent_catchup_guard:
                        continue
                    if target_namespace != chain.namespace and is_declared_cross_chain:
                        continue
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} transitively fires an event through {effect.name}",
                            effect.file,
                            line,
                        )
                    )
            if not self._flag_is_produced(
                chain.completion_flag,
                {name: [effect] for name, effect in reachable.items()},
            ):
                findings.append(
                    (
                        f"{chain.reconstruct_effect} never sets {chain.completion_flag}",
                        reconstruct.file,
                        reconstruct.line,
                    )
                )
            for block in self._nested_blocks(
                reconstruct.body,
                re.compile(r"\b(?:if|else_if)\s*=\s*\{"),
                chain.reconstruct_effect,
                reconstruct.file,
                reconstruct.line,
            ):
                if not self._block_has_state_change(block.body, chain):
                    continue
                if "date >" not in block.body:
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} has a state-changing block without a date guard",
                            block.file,
                            block.line,
                        )
                    )
                if not self._has_marker_guard(block.body):
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} has a state-changing block without sibling-marker guards",
                            block.file,
                            block.line,
                        )
                    )
        return self._dedupe_findings(findings)

    def _reachable_chain_effects(
        self,
        chain: ChainConfig,
        root_effect: BlockDef,
        effect_lookup: Dict[str, BlockDef],
    ) -> Dict[str, BlockDef]:
        reachable: Dict[str, BlockDef] = {}
        pending = [root_effect]
        while pending:
            effect = pending.pop()
            if effect.name in reachable:
                continue
            reachable[effect.name] = effect
            for match in _EFFECT_YES_RE.finditer(effect.body):
                name = match.group(1)
                if (
                    name.startswith(chain.root)
                    and name in effect_lookup
                    and name not in reachable
                ):
                    pending.append(effect_lookup[name])
        return reachable

    def _validate_completion_markers(
        self, chains: Sequence[ChainConfig], effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, str, int]]:
        findings = []
        discovered_flags: Set[str] = set()
        for defs in effect_defs.values():
            for effect in defs:
                discovered_flags.update(
                    re.findall(r"\b([A-Za-z0-9_]+_reconstruct_complete)\b", effect.body)
                )
        owners: Dict[str, List[ChainConfig]] = {}
        for chain in chains:
            declared_markers = (
                chain.completion_flag,
                *chain.auxiliary_completion_markers,
            )
            for marker in declared_markers:
                if marker in discovered_flags:
                    owners.setdefault(marker, []).append(chain)
        for flag in sorted(discovered_flags):
            chain_owners = owners.get(flag, [])
            if len(chain_owners) != 1:
                findings.append(
                    (f"{flag} has {len(chain_owners)} owning chains", "", 0)
                )
                continue
            producers = self._flag_producers(flag, effect_defs)
            if not producers:
                findings.append((f"{flag} has no producers", "", 0))
            elif (
                len(producers) > 1
                and not chain_owners[0].allow_multiple_completion_producers
            ):
                findings.append(
                    (
                        f"{flag} has {len(producers)} producers",
                        producers[0][0],
                        producers[0][1],
                    )
                )
            consumers = self._monthly_consumers(flag, effect_defs)
            if len(consumers) != 1:
                file = (
                    consumers[0][0]
                    if consumers
                    else "common/scripted_effects/00_corporate_history_effects.txt"
                )
                line = consumers[0][1] if consumers else 0
                findings.append(
                    (
                        f"{flag} has {len(consumers)} intended monthly-driver consumers",
                        file,
                        line,
                    )
                )
        return findings

    def _has_terminal_resolver(
        self, chain: ChainConfig, effect_defs: Dict[str, List[BlockDef]]
    ) -> bool:
        """The reconstruct ladder must silently land one of the chain's outcomes.

        A name check (``*resolve*``) says nothing about behaviour and misses the
        player-choice capstones that resolve inline in the ladder.
        """
        reconstruct = effect_defs.get(chain.reconstruct_effect)
        if not reconstruct or not chain.outcome_idea_prefixes:
            return False
        return bool(self._outcome_ideas_added(reconstruct[0].body, chain, effect_defs))

    def _has_cleanup_path(
        self,
        chain: ChainConfig,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        outcome_ids: Set[str],
    ) -> bool:
        """A chain must clear competing outcomes somewhere it can act atomically.

        The cleanup may live in a chain-owned effect or directly in a capstone
        option; what matters is that one block drops at least two competing
        outcome ideas, not which file it sits in.
        """
        if not outcome_ids:
            return False
        bodies = [
            effect.body
            for defs in effect_defs.values()
            for effect in defs
            if effect.name.startswith(chain.root)
        ]
        bodies.extend(
            option.body
            for event in event_defs.values()
            if event.event_id.startswith(chain.namespace + ".")
            for option in event.options
        )
        for body in bodies:
            if "remove_ideas" not in body:
                continue
            removed = sum(
                1
                for idea_id in outcome_ids
                if re.search(r"\b" + re.escape(idea_id) + r"\b", body)
            )
            if removed == len(outcome_ids):
                return True
        return False

    def _trace_mutation_path(
        self,
        text: str,
        chain: ChainConfig,
        effect_lookup: Dict[str, BlockDef],
        seen: Set[str],
        pending: bool = False,
    ) -> Tuple[bool, bool, bool]:
        ops: List[Tuple[int, str, str]] = []
        effect_names = set(effect_lookup)
        for match in _SET_VAR_RE.finditer(text):
            variable = match.group(1)
            if variable in chain.variables:
                ops.append((match.start(), "mutate", variable))
        for match in _CLAMP_VAR_RE.finditer(text):
            variable = match.group(1)
            if variable in chain.variables:
                ops.append((match.start(), "clamp", variable))
        for match in _SET_TEMP_CORP_RE.finditer(text):
            variable = match.group(1)
            if variable in chain.variables:
                ops.append((match.start(), "prepare-clamp", variable))
        for match in _DIRECT_CORP_CLAMP_RE.finditer(text):
            ops.append((match.start(), "direct-clamp", "corp"))
        for match in _EFFECT_YES_RE.finditer(text):
            name = match.group(1)
            if name in effect_names:
                ops.append((match.start(), "call", name))
        ops.sort(key=lambda item: item[0])

        used_clamp = False
        mutated = False
        prepared = False
        for _pos, kind, value in ops:
            if kind == "mutate":
                pending = True
                mutated = True
            elif kind == "clamp":
                if pending:
                    pending = False
                    used_clamp = True
            elif kind == "prepare-clamp":
                if pending:
                    prepared = True
            elif kind == "direct-clamp":
                if pending and prepared:
                    pending = False
                    used_clamp = True
                    prepared = False
            elif kind == "call":
                if value == chain.clamp_effect:
                    if pending:
                        pending = False
                        used_clamp = True
                    continue
                if value in seen:
                    continue
                callee = effect_lookup[value]
                pending, callee_used, callee_mutated = self._trace_mutation_path(
                    callee.body, chain, effect_lookup, seen | {value}, pending
                )
                used_clamp = used_clamp or callee_used
                mutated = mutated or callee_mutated
        return pending, used_clamp, mutated

    def _block_has_state_change(self, body: str, chain: ChainConfig) -> bool:
        if re.search(r"\bset_country_flag\b|\badd_ideas\b|\bremove_ideas\b", body):
            return True
        return any(variable in body for variable in chain.variables)

    def _has_marker_guard(self, body: str) -> bool:
        # Special case: reconstruction-complete flag setting is always valid
        if "set_country_flag = " in body and "_reconstruct_complete" in body:
            return True
        limit = self._direct_child_block(body, "limit")
        if limit is None:
            return False
        return self._negated_marker_in_trigger(limit)
