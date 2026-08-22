"""Scheduler reachability, owner-local dispatch, and startup checks."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import (
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

from shared_utils import strip_comments

from .model import (
    _CORPORATE_MODES,
    _EFFECT_YES_RE,
    _OEM_STARTUP_EFFECT,
    _OEM_STARTUP_FLAG,
    _OEM_STARTUP_ON_ACTION,
    _USA_2000_STARTUP_EVENTS,
    BlockDef,
    CallSite,
    ChainConfig,
    EventDef,
)


class SchedulerMixin:
    def _independent_scheduler_reachability(
        self,
        dispatch_effects: Set[str],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Mapping[str, EventDef],
        tracked_event_ids: Set[str],
    ) -> Tuple[Set[str], Set[str]]:
        """Follow effect/event edges from one subsystem's declared dispatchers."""
        children = self._effect_call_children(effect_defs)
        reachable_effects = self._effect_descendants(dispatch_effects, children)
        reachable_events: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for effect_name in tuple(reachable_effects):
                for definition in effect_defs.get(effect_name, []):
                    for event_id, _line in self._find_event_calls(
                        definition.body, definition.line, tracked_event_ids
                    ):
                        if event_id not in reachable_events:
                            reachable_events.add(event_id)
                            changed = True
            for event_id in tuple(reachable_events):
                event = event_defs.get(event_id)
                if event is None:
                    continue
                for child_event, _line in self._find_event_calls(
                    event.body, event.line, tracked_event_ids
                ):
                    if child_event not in reachable_events:
                        reachable_events.add(child_event)
                        changed = True
                event_effects = {
                    match.group(1)
                    for match in _EFFECT_YES_RE.finditer(event.body)
                    if match.group(1) in effect_defs
                }
                expanded_effects = self._effect_descendants(event_effects, children)
                if not expanded_effects.issubset(reachable_effects):
                    reachable_effects.update(expanded_effects)
                    changed = True
        return reachable_effects, reachable_events

    def _independent_event_call_sites(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Mapping[str, EventDef],
        tracked_ids: Set[str],
    ) -> Dict[str, List[CallSite]]:
        sites: Dict[str, List[CallSite]] = defaultdict(list)
        for owner, definitions in effect_defs.items():
            for definition in definitions:
                for event_id, line in self._find_event_calls(
                    definition.body, definition.line, tracked_ids
                ):
                    sites[event_id].append(
                        CallSite(event_id, definition.file, line, "effect", owner)
                    )
        for owner, event in event_defs.items():
            for event_id, line in self._find_event_calls(
                event.body, event.line, tracked_ids
            ):
                sites[event_id].append(
                    CallSite(event_id, event.file, line, "event", owner)
                )
        for filepath in self._collect_text_files(
            ["common/**/*.txt", "history/**/*.txt"]
        ):
            rel = self._relpath(filepath)
            normalized = rel.replace("\\", "/")
            if normalized.startswith("common/scripted_effects/"):
                continue
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            for event_id, line in self._find_event_calls(text, 1, tracked_ids):
                sites[event_id].append(
                    CallSite(event_id, rel, line, "script", f"{rel}:{line}")
                )
        return sites

    def _start_date_window(self, block: str) -> Optional[int]:
        """Year of the `NOT = { has_start_date < Y.1.1 } ... has_start_date < Y.1.2` pair.

        The lower bound always sits in the block's own limit. The upper bound may
        sit there too, or — where the block opens a whole-year window and its arms
        split January 1 from the rest (Nintendo, Russian Computing Sovereignty) —
        in the limit of a direct child arm. A sibling milestone's window is never
        consulted.
        """
        own = self._direct_child_block(block, "limit") or ""
        lower = re.search(
            r"NOT\s*=\s*\{\s*has_start_date\s*<\s*(\d{4})\.1\.1\s*\}",
            own,
        )
        if not lower:
            return None
        candidates = [own] + [
            self._direct_child_block(child, "limit") or ""
            for name, _s, _e, child in self._iter_direct_child_blocks(block)
            if name in ("if", "else_if")
        ]
        for text in candidates:
            upper = re.search(r"\bhas_start_date\s*<\s*(\d{4})\.1\.2\b", text)
            if upper and upper.group(1) == lower.group(1):
                return int(lower.group(1))
        return None

    def _scheduler_window_years(self, scheduler: BlockDef, event_id: str) -> Set[int]:
        years: Set[int] = set()
        self._collect_window_years(
            scheduler.body, scheduler.line, event_id, None, years
        )
        return years

    def _collect_window_years(
        self,
        body: str,
        line: int,
        event_id: str,
        inherited: Optional[int],
        years: Set[int],
    ) -> None:
        """Walk if/else_if children tracking the innermost start-date window in scope.

        Schedulers hoist their chain-level guard (`*_start_year_events_scheduled`,
        and for France the whole rule/tag/collapse gate) into an outer `if`, so the
        January-1 window can sit one or more levels above the block that queues the
        event. Only the window matters here; the enclosing guards are checked
        elsewhere.
        """

        def count_calls(text: str) -> int:
            return sum(
                1
                for target, _line in self._find_event_calls(text, line, frozenset())
                if target == event_id
            )

        for name, _start, _end, child in self._iter_direct_child_blocks(body):
            if name not in ("if", "else_if"):
                continue
            total = count_calls(child)
            if not total:
                continue
            window = self._start_date_window(child)
            if window is None:
                window = inherited
            nested = sum(
                count_calls(grandchild)
                for grandname, _gs, _ge, grandchild in self._iter_direct_child_blocks(
                    child
                )
                if grandname in ("if", "else_if")
            )
            # Queued directly by this block rather than only by a nested one.
            if total > nested and window is not None:
                years.add(window)
            if nested:
                self._collect_window_years(child, line, event_id, window, years)

    def _validate_event_reachability(
        self,
        chains: Sequence[ChainConfig],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        schema_v6 = int(self._manifest_payload.get("schema_version", 1)) >= 6
        for chain in chains:
            for event_id, event in sorted(event_defs.items()):
                if not event_id.startswith(chain.namespace + "."):
                    continue
                callers = self._dedupe_callers(call_sites.get(event_id, []))
                event_owner_tag = next(
                    (
                        lifecycle.tag
                        for lifecycle in chain.auxiliary_lifecycles
                        if event_id in lifecycle.expected_yearly_callers
                    ),
                    chain.tag,
                )
                recovery_key = (
                    f"effect:{event_owner_tag}_corporate_history_recover_midyear_events"
                )
                recovery_keys = {
                    caller.key
                    for caller in callers
                    if caller.key == recovery_key
                    or (
                        caller.kind == "effect"
                        and caller.owner.startswith(f"{chain.root}_recover_")
                    )
                }
                if schema_v6:
                    for caller in callers:
                        if (
                            caller.kind == "effect"
                            and caller.owner.endswith(
                                "_corporate_history_recover_midyear_events"
                            )
                            and caller.key != recovery_key
                        ):
                            findings.append(
                                (
                                    f"{event_id} has foreign midyear-recovery caller {caller.key}; expected {recovery_key}",
                                    caller.file,
                                    caller.line,
                                )
                            )
                expected = chain.expected_callers.get(event_id)
                if expected is not None:
                    actual_keys = tuple(sorted(caller.key for caller in callers))
                    effective_expected = set(expected)
                    if schema_v6:
                        effective_expected.update(recovery_keys)
                    expected_keys = tuple(sorted(effective_expected))
                    if actual_keys != expected_keys:
                        findings.append(
                            (
                                f"{event_id} callers differ from the manifest: expected {', '.join(expected_keys) or 'none'}; found {', '.join(actual_keys) or 'none'}",
                                event.file,
                                event.line,
                            )
                        )
                    continue
                ordinary_callers = [
                    caller
                    for caller in callers
                    if not (schema_v6 and caller.key in recovery_keys)
                ]
                if not callers and event_id not in chain.callerless_anchors:
                    findings.append(
                        (
                            f"{event_id} has no direct callers and is not a declared custom/pre-2000 anchor",
                            event.file,
                            event.line,
                        )
                    )
                    continue
                if len(ordinary_callers) <= 1:
                    continue
                if self._multiple_callers_allowed(chain, event_id, ordinary_callers):
                    continue
                caller_desc = ", ".join(sorted(c.owner for c in ordinary_callers))
                findings.append(
                    (
                        f"{event_id} has multiple direct callers: {caller_desc}",
                        event.file,
                        event.line,
                    )
                )
        return findings

    def _validate_oem_startup_architecture(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
    ) -> List[Tuple[str, str, int]]:
        if int(self._manifest_payload.get("schema_version", 1)) >= 6:
            return self._validate_country_local_monthly_architecture(effect_defs)
        on_action_path = self._root.joinpath(*_OEM_STARTUP_ON_ACTION.split("/"))
        if (
            not on_action_path.exists()
            and not set(_USA_2000_STARTUP_EVENTS).intersection(event_defs)
            and _OEM_STARTUP_EFFECT not in effect_defs
            and not {
                "gpu_development_schedule_current_year_events",
                "USA_ibm_schedule_prehistory",
                "USA_e3_schedule_current_year_events",
            }.intersection(effect_defs)
        ):
            return []

        findings: List[Tuple[str, str, int]] = []
        on_action_text = ""
        if on_action_path.exists():
            on_action_text = strip_comments(
                on_action_path.read_text(encoding="utf-8-sig", errors="replace")
            )
        else:
            findings.append(
                (
                    "The authoritative OEM startup on-action file is missing",
                    _OEM_STARTUP_ON_ACTION,
                    0,
                )
            )

        definition_sites = self._event_definition_sites(
            frozenset(_USA_2000_STARTUP_EVENTS)
        )
        for event_id in _USA_2000_STARTUP_EVENTS:
            sites = definition_sites.get(event_id, [])
            if len(sites) != 1:
                findings.append(
                    (
                        f"USA 2000 startup event {event_id} requires exactly one definition; found {len(sites)}",
                        sites[0][0] if sites else "events",
                        sites[0][1] if sites else 0,
                    )
                )

        bootstrap_defs = effect_defs.get(_OEM_STARTUP_EFFECT, [])
        if len(bootstrap_defs) != 1:
            findings.append(
                (
                    f"{_OEM_STARTUP_EFFECT} requires exactly one definition; found {len(bootstrap_defs)}",
                    "common/scripted_effects/00_corporate_history_effects.txt",
                    bootstrap_defs[0].line if bootstrap_defs else 0,
                )
            )

        bootstrap_callers = self._script_effect_call_sites(_OEM_STARTUP_EFFECT)
        normalized_callers = [
            (path.replace("\\", "/"), line) for path, line in bootstrap_callers
        ]
        if len(normalized_callers) != 1 or (
            normalized_callers and normalized_callers[0][0] != _OEM_STARTUP_ON_ACTION
        ):
            callers = ", ".join(f"{path}:{line}" for path, line in normalized_callers)
            findings.append(
                (
                    f"{_OEM_STARTUP_EFFECT} requires exactly one caller in {_OEM_STARTUP_ON_ACTION}; found {callers or 'none'}",
                    _OEM_STARTUP_ON_ACTION,
                    normalized_callers[0][1] if normalized_callers else 0,
                )
            )

        repository_script_patterns = [
            "common/**/*.txt",
            "events/**/*.txt",
            "history/**/*.txt",
        ]
        direct_bootstrap_callers = self._raw_script_call_sites(
            _OEM_STARTUP_EFFECT, repository_script_patterns
        )
        normalized_direct_bootstrap_callers = [
            (path.replace("\\", "/"), line) for path, line in direct_bootstrap_callers
        ]
        if len(normalized_direct_bootstrap_callers) != 1 or (
            normalized_direct_bootstrap_callers
            and normalized_direct_bootstrap_callers[0][0] != _OEM_STARTUP_ON_ACTION
        ):
            rendered = ", ".join(
                f"{path}:{line}" for path, line in normalized_direct_bootstrap_callers
            )
            findings.append(
                (
                    f"{_OEM_STARTUP_EFFECT} requires exactly one direct repository caller in {_OEM_STARTUP_ON_ACTION}; found {rendered or 'none'}",
                    (
                        direct_bootstrap_callers[0][0]
                        if direct_bootstrap_callers
                        else _OEM_STARTUP_ON_ACTION
                    ),
                    direct_bootstrap_callers[0][1] if direct_bootstrap_callers else 0,
                )
            )

        direct_corporate_callers = self._raw_script_call_sites(
            "corporate_history_on_startup", ["common/on_actions/**/*.txt"]
        )
        if direct_corporate_callers:
            rendered = ", ".join(
                f"{path.replace(os.sep, '/')}:{line}"
                for path, line in direct_corporate_callers
            )
            findings.append(
                (
                    f"corporate_history_on_startup must not be called directly from on_actions; found {rendered}",
                    direct_corporate_callers[0][0],
                    direct_corporate_callers[0][1],
                )
            )

        scoped_calls = 0
        for wrapper, _start, _end, wrapper_body in self._iter_direct_child_blocks(
            on_action_text
        ):
            if wrapper != "on_actions":
                continue
            for (
                child,
                _child_start,
                _child_end,
                startup_body,
            ) in self._iter_direct_child_blocks(wrapper_body):
                if child != "on_startup":
                    continue
                tag_match = re.search(r"\btag\s*=\s*ABK\b", startup_body)
                if tag_match:
                    file_tag_match = re.search(r"\btag\s*=\s*ABK\b", on_action_text)
                    findings.append(
                        (
                            "OEM on_startup tests tag = ABK in ROOT=None instead of entering ABK scope",
                            _OEM_STARTUP_ON_ACTION,
                            self._line(
                                on_action_text,
                                file_tag_match.start() if file_tag_match else 0,
                            ),
                        )
                    )
                effect_body = self._direct_child_block(startup_body, "effect")
                if effect_body is None:
                    continue
                abk_body = self._direct_child_block(effect_body, "ABK")
                if abk_body and re.search(
                    rf"\b{re.escape(_OEM_STARTUP_EFFECT)}\s*=\s*yes\b",
                    self._direct_block_text(abk_body),
                ):
                    scoped_calls += 1
        if scoped_calls != 1:
            findings.append(
                (
                    f"OEM startup requires exactly one on_actions -> on_startup -> effect -> ABK scoped bootstrap call; found {scoped_calls}",
                    _OEM_STARTUP_ON_ACTION,
                    0,
                )
            )

        guarded_body = ""
        direct_guarded_body = ""
        bootstrap = bootstrap_defs[0] if len(bootstrap_defs) == 1 else None
        if bootstrap is not None:
            bootstrap_children = list(self._iter_direct_child_blocks(bootstrap.body))
            guarded_blocks = []
            for child, _start, _end, body in bootstrap_children:
                if child != "if":
                    continue
                limit = self._direct_child_block(body, "limit") or ""
                if self._is_exact_global_flag_guard(limit, _OEM_STARTUP_FLAG):
                    guarded_blocks.append(body)
            if (
                len(bootstrap_children) != 1
                or len(guarded_blocks) != 1
                or self._direct_block_text(bootstrap.body).strip()
            ):
                findings.append(
                    (
                        f"{_OEM_STARTUP_EFFECT} requires one sole direct NOT has_global_flag guard for {_OEM_STARTUP_FLAG}; found {len(guarded_blocks)} valid guards across {len(bootstrap_children)} direct blocks",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )
            else:
                guarded_body = guarded_blocks[0]
                direct_guarded_body = self._direct_block_text(guarded_body)

            set_pattern = re.compile(
                rf"\bset_global_flag\s*=\s*{re.escape(_OEM_STARTUP_FLAG)}\b"
            )
            sets = list(set_pattern.finditer(bootstrap.body))
            if (
                len(sets) != 1
                or not guarded_body
                or not set_pattern.search(direct_guarded_body)
            ):
                findings.append(
                    (
                        f"{_OEM_STARTUP_EFFECT} must set {_OEM_STARTUP_FLAG} exactly once inside its guarded branch",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )
            else:
                marker_match = set_pattern.search(guarded_body)
                executable_block_before_marker = bool(
                    marker_match
                    and any(
                        child != "limit" and start < marker_match.start()
                        for child, start, _end, _body in self._iter_direct_child_blocks(
                            guarded_body
                        )
                    )
                )
                marker_is_first_direct_statement = bool(
                    re.match(
                        rf"\s*set_global_flag\s*=\s*{re.escape(_OEM_STARTUP_FLAG)}\b",
                        direct_guarded_body,
                    )
                )
                if (
                    not marker_is_first_direct_statement
                    or executable_block_before_marker
                ):
                    findings.append(
                        (
                            f"{_OEM_STARTUP_EFFECT} must set {_OEM_STARTUP_FLAG} before dispatching startup work and as its first direct effect statement",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )

            marker_sets, marker_clears = self._global_flag_write_sites(
                _OEM_STARTUP_FLAG
            )
            if len(marker_sets) != 1 or marker_sets[0][0] != bootstrap.file:
                rendered = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}" for path, line in marker_sets
                )
                findings.append(
                    (
                        f"{_OEM_STARTUP_FLAG} must be set only by {_OEM_STARTUP_EFFECT}; found {rendered or 'none'}",
                        marker_sets[0][0] if marker_sets else bootstrap.file,
                        marker_sets[0][1] if marker_sets else bootstrap.line,
                    )
                )
            if marker_clears:
                rendered = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}"
                    for path, line in marker_clears
                )
                findings.append(
                    (
                        f"{_OEM_STARTUP_FLAG} must never be cleared; found {rendered}",
                        marker_clears[0][0],
                        marker_clears[0][1],
                    )
                )

            if not re.search(
                r"\bcorporate_history_on_startup\s*=\s*yes\b",
                direct_guarded_body,
            ):
                findings.append(
                    (
                        "corporate_history_on_startup must be called directly from the guarded OEM bootstrap",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )

        corporate_owners: List[Tuple[str, int]] = []
        corporate_pattern = re.compile(r"\bcorporate_history_on_startup\s*=\s*yes\b")
        for name, definitions in effect_defs.items():
            for definition in definitions:
                corporate_owners.extend(
                    (
                        name,
                        definition.line
                        + self._line(definition.body, match.start())
                        - 1,
                    )
                    for match in corporate_pattern.finditer(definition.body)
                )
        if [owner for owner, _line in corporate_owners] != [_OEM_STARTUP_EFFECT]:
            findings.append(
                (
                    "corporate_history_on_startup must have the OEM bootstrap as its sole scripted-effect owner",
                    (
                        bootstrap.file
                        if bootstrap is not None
                        else "common/scripted_effects/00_corporate_history_effects.txt"
                    ),
                    corporate_owners[0][1] if corporate_owners else 0,
                )
            )
        direct_corporate_callers = self._raw_script_call_sites(
            "corporate_history_on_startup", repository_script_patterns
        )
        if len(direct_corporate_callers) != 1 or (
            bootstrap is not None
            and direct_corporate_callers
            and direct_corporate_callers[0][0] != bootstrap.file
        ):
            rendered = ", ".join(
                f"{path.replace(os.sep, '/')}:{line}"
                for path, line in direct_corporate_callers
            )
            findings.append(
                (
                    f"corporate_history_on_startup requires {_OEM_STARTUP_EFFECT} as its sole direct repository caller; found {rendered or 'none'}",
                    (
                        direct_corporate_callers[0][0]
                        if direct_corporate_callers
                        else (
                            bootstrap.file
                            if bootstrap is not None
                            else "common/scripted_effects"
                        )
                    ),
                    direct_corporate_callers[0][1] if direct_corporate_callers else 0,
                )
            )

        usa_branches = self._oem_startup_country_branches(guarded_body, "USA")
        if len(usa_branches) != 1:
            findings.append(
                (
                    f"The guarded OEM bootstrap requires exactly one explicit USA country branch; found {len(usa_branches)}",
                    bootstrap.file if bootstrap is not None else _OEM_STARTUP_ON_ACTION,
                    bootstrap.line if bootstrap is not None else 0,
                )
            )
        else:
            usa_limit, usa_scope = usa_branches[0]
            if not self._is_exact_country_exists_limit(usa_limit, "USA"):
                findings.append(
                    (
                        "The OEM bootstrap USA scope must be entered from an unconditionally country_exists = USA branch",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )
            direct_usa_scope = self._direct_block_text(usa_scope)
            for effect_name in (
                "gpu_development_reconstruct_history",
                "gpu_development_schedule_current_year_events",
            ):
                count = len(
                    re.findall(rf"\b{re.escape(effect_name)}\s*=\s*yes\b", usa_scope)
                )
                if count != 1:
                    findings.append(
                        (
                            f"USA startup requires exactly one {effect_name} call; found {count}",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )
                elif not re.search(
                    rf"\b{re.escape(effect_name)}\s*=\s*yes\b", direct_usa_scope
                ):
                    findings.append(
                        (
                            f"USA startup must call {effect_name} directly in USA scope without a Corporate History gate",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )
            dell_gate = ""
            for child, _start, _end, body in self._iter_direct_child_blocks(usa_scope):
                if child not in ("if", "else_if"):
                    continue
                limit = self._direct_child_block(body, "limit") or ""
                if self._is_exact_dell_2000_full_limit(
                    limit
                ) and self._direct_event_calls(body, "USA_oem_events.13"):
                    dell_gate = body
                if (
                    "corporate_history_full_enabled = yes" in limit
                    and "gpu_development_schedule_current_year_events = yes" in body
                ):
                    findings.append(
                        (
                            "USA GPU startup is incorrectly gated by Corporate History Full mode",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )
            if not dell_gate:
                findings.append(
                    (
                        "USA_oem_events.13 is not reachable from the USA bootstrap under its 2000 Full-mode gate",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )

        startup_defs = effect_defs.get("corporate_history_on_startup", [])
        startup = startup_defs[0] if len(startup_defs) == 1 else None
        full_branch = self._startup_full_branch(startup.body) if startup else ""
        outcomes_branch = self._startup_outcomes_branch(startup.body) if startup else ""
        if startup is None:
            findings.append(
                (
                    f"corporate_history_on_startup requires exactly one definition; found {len(startup_defs)}",
                    "common/scripted_effects/00_corporate_history_effects.txt",
                    startup_defs[0].line if startup_defs else 0,
                )
            )
        else:
            if not full_branch:
                findings.append(
                    (
                        "corporate_history_on_startup is missing its Full-mode branch",
                        startup.file,
                        startup.line,
                    )
                )
            if not outcomes_branch:
                findings.append(
                    (
                        "corporate_history_on_startup is missing its Outcomes Only branch",
                        startup.file,
                        startup.line,
                    )
                )
            full_only_symbols = (
                "USA_oem_events.13",
                "USA_ibm_events.12",
                "USA_ibm_events.13",
                "USA_ibm_events.90",
                "USA_ibm_schedule_prehistory",
                "USA_e3_events.1",
                "USA_e3_events.90",
                "USA_e3_schedule_current_year_events",
                "USA_hp_events.1",
            )
            full_only_effects = {
                "USA_ibm_schedule_prehistory",
                "USA_e3_schedule_current_year_events",
            }
            full_only_events = {
                "USA_oem_events.13",
                "USA_ibm_events.12",
                "USA_ibm_events.13",
                "USA_ibm_events.90",
                "USA_e3_events.1",
                "USA_e3_events.90",
                "USA_hp_events.1",
            }
            outcomes_effects, outcomes_events = self._mixed_script_descendants(
                outcomes_branch, effect_defs, event_defs
            )
            if (
                any(symbol in outcomes_branch for symbol in full_only_symbols)
                or full_only_effects.intersection(outcomes_effects)
                or full_only_events.intersection(outcomes_events)
            ):
                findings.append(
                    (
                        "Outcomes Only schedules a Full-mode USA corporate popup",
                        startup.file,
                        startup.line,
                    )
                )
            if any(
                child == "else"
                for child, _start, _end, _body in self._iter_direct_child_blocks(
                    startup.body
                )
            ):
                findings.append(
                    (
                        "Corporate History Off must leave startup inert; an else branch is present",
                        startup.file,
                        startup.line,
                    )
                )
            direct_children = [
                child
                for child, _start, _end, _body in self._iter_direct_child_blocks(
                    startup.body
                )
            ]
            if (
                direct_children != ["if", "else_if"]
                or self._direct_block_text(startup.body).strip()
            ):
                findings.append(
                    (
                        "Corporate History startup must contain only its direct Full and Outcomes Only branches so Off remains inert",
                        startup.file,
                        startup.line,
                    )
                )

        full_usa_branches = self._oem_startup_country_branches(full_branch, "USA")
        full_usa_scopes = [scope for _limit, scope in full_usa_branches]
        full_usa_body = "\n".join(full_usa_scopes)
        if full_branch and not full_usa_scopes:
            findings.append(
                (
                    "Corporate History Full startup does not enter an explicit USA scope",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )
        anchor_branches = [
            (limit, scope)
            for limit, scope in full_usa_branches
            if self._direct_event_calls(scope, "USA_ibm_events.90")
            or self._direct_event_calls(scope, "USA_e3_events.90")
        ]
        anchor_shape_valid = False
        anchor_calls_valid = False
        if len(anchor_branches) == 1:
            anchor_limit, anchor_scope = anchor_branches[0]
            anchor_shape_valid = self._is_exact_country_exists_limit(
                anchor_limit, "USA"
            )
            ibm_calls = self._direct_event_calls(anchor_scope, "USA_ibm_events.90")
            e3_calls = self._direct_event_calls(anchor_scope, "USA_e3_events.90")
            anchor_calls_valid = bool(
                len(ibm_calls) == 1
                and ibm_calls[0][1] == 1
                and len(e3_calls) == 1
                and e3_calls[0][1] == 1
            )
        if full_branch and not anchor_shape_valid:
            findings.append(
                (
                    "IBM and E3 startup anchors must share one reachable country_exists = USA branch with no additional gate",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )
        elif full_branch and not anchor_calls_valid:
            findings.append(
                (
                    "IBM and E3 startup anchors must both be queued directly at days = 1 in their USA branch",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )

        expected_callers = {
            "USA_oem_events.13": ("effect", _OEM_STARTUP_EFFECT),
            "gpu_development.1": (
                "effect",
                "gpu_development_schedule_current_year_events",
            ),
            "USA_ibm_events.12": ("effect", "USA_ibm_schedule_prehistory"),
            "USA_ibm_events.13": ("effect", "USA_ibm_schedule_prehistory"),
            "USA_ibm_events.90": ("effect", "corporate_history_on_startup"),
            "USA_e3_events.1": (
                "effect",
                "USA_e3_schedule_current_year_events",
            ),
            "USA_e3_events.90": ("effect", "corporate_history_on_startup"),
            "USA_hp_events.1": ("effect", "corporate_history_on_startup"),
        }
        for event_id, expected in expected_callers.items():
            actual = [
                (caller.kind, caller.owner) for caller in call_sites.get(event_id, [])
            ]
            if actual != [expected]:
                rendered = ", ".join(f"{kind}:{owner}" for kind, owner in actual)
                event = event_defs.get(event_id)
                findings.append(
                    (
                        f"{event_id} requires sole caller {expected[0]}:{expected[1]}; found {rendered or 'none'}",
                        event.file if event else "events",
                        event.line if event else 0,
                    )
                )

        findings.extend(
            self._validate_usa_2000_startup_schedule(
                effect_defs,
                event_defs,
                bootstrap,
                startup,
                full_branch,
                full_usa_body,
            )
        )

        yearly_path = (
            self._root / "common" / "scripted_effects" / "00_yearly_effects.txt"
        )
        if yearly_path.exists():
            yearly_text = strip_comments(
                yearly_path.read_text(encoding="utf-8-sig", errors="replace")
            )
            forbidden = (
                _OEM_STARTUP_EFFECT,
                "corporate_history_on_startup",
                "gpu_development_schedule_current_year_events",
                *_USA_2000_STARTUP_EVENTS,
            )
            for symbol in forbidden:
                match = re.search(rf"\b{re.escape(symbol)}\b", yearly_text)
                if match:
                    findings.append(
                        (
                            f"OEM startup symbol {symbol} must remain outside upstream-owned 00_yearly_effects.txt",
                            "common/scripted_effects/00_yearly_effects.txt",
                            self._line(yearly_text, match.start()),
                        )
                    )

        return self._dedupe_findings(findings)

    def _validate_country_local_monthly_architecture(
        self, effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        deprecated = (
            _OEM_STARTUP_EFFECT,
            "corporate_history_on_startup",
        )
        for effect_name in deprecated:
            definitions = effect_defs.get(effect_name, [])
            if definitions:
                findings.append(
                    (
                        f"Deprecated singleton startup effect {effect_name} must be removed",
                        definitions[0].file,
                        definitions[0].line,
                    )
                )
        old_on_action = self._root.joinpath(*_OEM_STARTUP_ON_ACTION.split("/"))
        if old_on_action.exists():
            findings.append(
                (
                    "The deprecated ABK OEM startup on-action file must be removed",
                    _OEM_STARTUP_ON_ACTION,
                    1,
                )
            )

        required_effects = (
            "corporate_history_country_bootstrap",
            "corporate_history_monthly_dispatch",
            *(f"corporate_history_dispatch_year_{year}" for year in range(2000, 2027)),
        )
        for effect_name in required_effects:
            definitions = effect_defs.get(effect_name, [])
            if len(definitions) != 1:
                findings.append(
                    (
                        f"Country-local monthly architecture requires exactly one {effect_name}; found {len(definitions)}",
                        (
                            definitions[0].file
                            if definitions
                            else "common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt"
                        ),
                        definitions[0].line if definitions else 1,
                    )
                )

        root = "corporate_history_monthly_dispatch"
        effect_modes, _event_modes, effect_traces, _event_traces = (
            self._independent_mode_graph(effect_defs, set())
        )
        root_modes = effect_modes.get(root, set())
        for mode in ("full", "outcomes_only"):
            if mode not in root_modes:
                findings.append(
                    (
                        f"{root} is not reachable from a country-local monthly host in {mode}",
                        "common/on_actions",
                        1,
                    )
                )
        traces = [
            trace
            for mode in _CORPORATE_MODES
            for trace in effect_traces.get((root, mode), [])
        ]
        for trace in traces:
            if not trace.host.startswith("on_monthly"):
                findings.append(
                    (
                        f"{root} is reached from forbidden host {trace.host}",
                        trace.host_file,
                        trace.line,
                    )
                )
            if any(block == "ABK" for block in trace.block_path):
                findings.append(
                    (
                        f"{root} must not use ABK as a singleton host",
                        trace.host_file,
                        trace.line,
                    )
                )

        if int(self._manifest_payload.get("schema_version", 1)) >= 6:
            raw_chains = self._manifest_payload.get("chains", [])
            drivers_by_tag: Dict[str, Set[str]] = defaultdict(set)
            if isinstance(raw_chains, list):
                for raw_chain in raw_chains:
                    if not isinstance(raw_chain, dict):
                        continue
                    tag = str(raw_chain.get("tag", ""))
                    driver = str(raw_chain.get("monthly_driver", ""))
                    if tag and driver:
                        drivers_by_tag[tag].add(driver)

            expected_pairs: Set[Tuple[str, str]] = set()
            declared_drivers: Set[str] = set()
            for tag, drivers in sorted(drivers_by_tag.items()):
                if len(drivers) != 1:
                    findings.append(
                        (
                            f"Schema v6 requires one monthly driver for {tag}; found {', '.join(sorted(drivers)) or 'none'}",
                            str(self._manifest_path),
                            1,
                        )
                    )
                    continue
                driver = next(iter(drivers))
                declared_drivers.add(driver)
                expected_pairs.add((f"on_monthly_{tag}", driver))

            actual_pairs: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
            for trace in traces:
                path_drivers = declared_drivers.intersection(trace.block_path)
                if len(path_drivers) != 1:
                    rendered = ", ".join(sorted(path_drivers)) or "none"
                    findings.append(
                        (
                            f"{root} must pass through exactly one declared monthly driver; found {rendered}",
                            trace.host_file,
                            trace.line,
                        )
                    )
                    continue
                driver = next(iter(path_drivers))
                actual_pairs[(trace.host, driver)].add(trace.host_file)

            for host, driver in sorted(expected_pairs - set(actual_pairs)):
                findings.append(
                    (
                        f"{root} requires country-local path {host} -> {driver}; found none",
                        "common/on_actions",
                        1,
                    )
                )
            for host, driver in sorted(set(actual_pairs) - expected_pairs):
                files = ", ".join(sorted(actual_pairs[(host, driver)]))
                findings.append(
                    (
                        f"{root} has undeclared country-local path {host} -> {driver} in {files}",
                        next(iter(actual_pairs[(host, driver)])),
                        1,
                    )
                )
            for (host, driver), files in sorted(actual_pairs.items()):
                if (host, driver) in expected_pairs and len(files) != 1:
                    findings.append(
                        (
                            f"{root} requires one host file for {host} -> {driver}; found {len(files)}",
                            next(iter(files)),
                            1,
                        )
                    )

        root_defs = effect_defs.get(root, [])
        if len(root_defs) == 1:
            body = root_defs[0].body
            for year in range(2000, 2027):
                dispatcher = f"corporate_history_dispatch_year_{year}"
                count = len(re.findall(rf"\b{re.escape(dispatcher)}\s*=\s*yes\b", body))
                if count != 1:
                    findings.append(
                        (
                            f"{root} must reach {dispatcher} exactly once; found {count}",
                            root_defs[0].file,
                            root_defs[0].line,
                        )
                    )
            if re.search(r"\b(?:set|clr)_global_flag\b|\bglobal\.", body):
                findings.append(
                    (
                        f"{root} must keep chronology state country-local",
                        root_defs[0].file,
                        root_defs[0].line,
                    )
                )

        forbidden_sites = []
        forbidden_patterns = {
            symbol: re.compile(rf"\b{re.escape(symbol)}\b")
            for symbol in (*deprecated, _OEM_STARTUP_FLAG)
        }
        for filepath in self._collect_text_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        ):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            for symbol, pattern in forbidden_patterns.items():
                for match in pattern.finditer(text):
                    forbidden_sites.append(
                        (
                            f"Deprecated singleton startup symbol {symbol} remains",
                            self._relpath(filepath),
                            self._line(text, match.start()),
                        )
                    )
        findings.extend(forbidden_sites)
        return self._dedupe_findings(findings)

    def _validate_dispatchers(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        defined_dispatchers = {
            name: defs
            for name, defs in effect_defs.items()
            if "_corporate_trigger_year_" in name
        }
        yearly_calls = self._effect_call_counts(
            effect_defs, [name for name in defined_dispatchers]
        )
        registered_namespaces = {chain.namespace for chain in chains}
        defined_events = set(event_defs)

        schema_v6 = int(self._manifest_payload.get("schema_version", 1)) >= 6
        for name, defs in sorted(defined_dispatchers.items()):
            if len(defs) != 1:
                for definition in defs:
                    findings.append(
                        (
                            f"{name} requires exactly one definition; found {len(defs)}",
                            definition.file,
                            definition.line,
                        )
                    )
                continue
            definition = defs[0]
            callers = yearly_calls.get(name, [])
            on_action_callers = (
                [] if schema_v6 else self._script_effect_call_sites(name)
            )
            call_count = len(callers) + len(on_action_callers)
            if call_count != 1:
                findings.append(
                    (
                        f"{name} requires exactly one yearly-dispatch caller; found {call_count}",
                        definition.file,
                        definition.line,
                    )
                )
            year_match = re.search(r"_corporate_trigger_year_(\d{4})$", name)
            if call_count == 1 and year_match:
                expected_owner = (
                    f"corporate_history_dispatch_year_{year_match.group(1)}"
                    if schema_v6
                    else f"trigger_year_{year_match.group(1)}_events"
                )
                if callers:
                    if callers[0][2] != expected_owner:
                        findings.append(
                            (
                                f"{name} must be called by {expected_owner}; found {callers[0][2]}",
                                callers[0][0],
                                callers[0][1],
                            )
                        )
                else:
                    on_action_file, on_action_line = on_action_callers[0]
                    expected_on_action = (
                        "common/on_actions/01_oem_corporate_history_on_actions.txt"
                    )
                    if on_action_file.replace("\\", "/") != expected_on_action:
                        findings.append(
                            (
                                f"{name} must be called by {expected_owner} or the dedicated OEM yearly on-action; found {on_action_file}",
                                on_action_file,
                                on_action_line,
                            )
                        )

            all_scheduled = self._find_event_calls(
                definition.body, definition.line, frozenset()
            )
            guarded_targets: List[str] = []
            for child, _start, _end, body in self._iter_direct_child_blocks(
                definition.body
            ):
                if child not in ("if", "else_if"):
                    continue
                limit = self._direct_child_block(body, "limit")
                if not limit or "corporate_history_full_enabled = yes" not in limit:
                    continue
                guarded_targets.extend(
                    target
                    for target, _line in self._find_event_calls(
                        body, definition.line, frozenset()
                    )
                )
            if len(guarded_targets) != len(all_scheduled):
                findings.append(
                    (
                        f"{name} schedules events outside its corporate_history_full_enabled branch",
                        definition.file,
                        definition.line,
                    )
                )
            scheduled = all_scheduled
            counts: Dict[str, int] = {}
            for target, _line in scheduled:
                counts[target] = counts.get(target, 0) + 1
                if target not in defined_events:
                    findings.append(
                        (
                            f"{name} calls undefined event {target}",
                            definition.file,
                            definition.line,
                        )
                    )
            for target, count in sorted(counts.items()):
                if count > 1:
                    findings.append(
                        (
                            f"{name} schedules {target} {count} times",
                            definition.file,
                            definition.line,
                        )
                    )

        yearly_inline = effect_defs
        for defs in yearly_inline.values():
            for block in defs:
                if not block.file.endswith(
                    "common\\scripted_effects\\00_yearly_effects.txt"
                ) and not block.file.endswith(
                    "common/scripted_effects/00_yearly_effects.txt"
                ):
                    continue
                for target, line in self._find_event_calls(
                    block.body, block.line, defined_events
                ):
                    namespace = target.split(".", 1)[0]
                    if namespace in registered_namespaces:
                        findings.append(
                            (
                                f"{target} is scheduled inline in 00_yearly_effects.txt instead of through its corporate dispatcher",
                                block.file,
                                line,
                            )
                        )
        return self._dedupe_findings(findings)

    def _multiple_callers_allowed(
        self, chain: ChainConfig, event_id: str, callers: Sequence[CallSite]
    ) -> bool:
        if event_id in chain.allowed_multiple_callers:
            return True
        if not chain.allow_yearly_scheduler_duplicates:
            return False
        owners = {caller.owner for caller in callers if caller.kind == "effect"}
        if len(owners) != len(callers):
            return False
        if chain.scheduler_effect not in owners:
            return False
        yearly = [owner for owner in owners if "_corporate_trigger_year_" in owner]
        return len(yearly) == 1 and len(owners) == 2

    def _oem_startup_country_branches(
        self, body: str, tag: str
    ) -> List[Tuple[str, str]]:
        country_exists = re.compile(rf"\bcountry_exists\s*=\s*{re.escape(tag)}\b")
        branches: List[Tuple[str, str]] = []
        for child, _start, _end, branch in self._iter_direct_child_blocks(body):
            if child not in ("if", "else_if"):
                continue
            limit = self._direct_child_block(branch, "limit") or ""
            if country_exists.search(limit):
                scope = self._direct_child_block(branch, tag)
                if scope is not None:
                    branches.append((limit, scope))
        return branches

    def _country_scopes_in_branches(self, body: str, tag: str) -> List[str]:
        scopes: List[str] = []
        country_exists = re.compile(rf"\bcountry_exists\s*=\s*{re.escape(tag)}\b")
        for child, _start, _end, branch in self._iter_direct_child_blocks(body):
            if child not in ("if", "else_if"):
                continue
            limit = self._direct_child_block(branch, "limit") or ""
            scope = self._direct_child_block(branch, tag)
            if country_exists.search(limit) and scope is not None:
                scopes.append(scope)
        return scopes

    def _is_exact_country_exists_limit(self, limit: str, tag: str) -> bool:
        return bool(
            re.fullmatch(rf"\s*country_exists\s*=\s*{re.escape(tag)}\s*", limit)
        )

    def _is_exact_yes_trigger(self, limit: str, trigger: str) -> bool:
        return self._direct_has_exact_clauses(
            limit, (rf"\b{re.escape(trigger)}\s*=\s*yes\b",)
        )

    def _is_exact_dell_2000_full_limit(self, limit: str) -> bool:
        return self._direct_has_exact_clauses(
            limit,
            (
                r"\bdate\s*<\s*2001\.1\.1\b",
                r"\bcorporate_history_full_enabled\s*=\s*yes\b",
            ),
        )

    def _direct_has_exact_clauses(
        self, text: str, patterns: Sequence[str], allow_blocks: bool = False
    ) -> bool:
        if not allow_blocks and list(self._iter_direct_child_blocks(text)):
            return False
        residual = self._direct_block_text(text)
        for pattern in patterns:
            residual, count = re.subn(pattern, "", residual, count=1)
            if count != 1 or re.search(pattern, residual):
                return False
        return not residual.strip()

    def _exact_not_terms(self, text: str, expected: Iterable[str]) -> bool:
        children = list(self._iter_direct_child_blocks(text))
        if any(name.upper() != "NOT" for name, _s, _e, _body in children):
            return False
        actual = [" ".join(body.split()) for _name, _s, _e, body in children]
        return sorted(actual) == sorted(expected)

    def _is_exact_hp_2000_limit(self, limit: str) -> bool:
        return bool(
            self._direct_has_exact_clauses(
                limit,
                (
                    r"\bcountry_exists\s*=\s*USA\b",
                    r"\bhas_start_date\s*<\s*2000\.1\.2\b",
                ),
                allow_blocks=True,
            )
            and self._exact_not_terms(limit, ("has_start_date < 2000.1.1",))
        )

    def _is_exact_e3_2000_limit(self, limit: str) -> bool:
        return bool(
            self._direct_has_exact_clauses(
                limit,
                (r"\bhas_start_date\s*<\s*2000\.1\.2\b",),
                allow_blocks=True,
            )
            and self._exact_not_terms(
                limit,
                (
                    "has_start_date < 2000.1.1",
                    "has_country_flag = USA_e3_opening_context_seen",
                ),
            )
        )

    def _is_exact_ibm_queue_limit(
        self, limit: str, scheduled_flag: str, resolved_flag: str
    ) -> bool:
        return bool(
            not self._direct_block_text(limit).strip()
            and self._exact_not_terms(
                limit,
                (
                    f"has_country_flag = {scheduled_flag}",
                    f"has_country_flag = {resolved_flag}",
                ),
            )
        )

    def _scheduler_has_replay_guard(
        self, scheduler: BlockDef, event_id: str, scheduled_flag: str
    ) -> bool:
        candidates = [
            (end, body)
            for name, _start, end, body in self._iter_direct_child_blocks(
                scheduler.body
            )
            if name == "if" and self._event_delays_in_body(body, event_id)
        ]
        if len(candidates) != 1:
            return False
        outer_end, outer_body = candidates[0]
        limit = self._direct_child_block(outer_body, "limit") or ""
        if not self._is_exact_country_flag_guard(limit, scheduled_flag):
            return False
        pattern = re.compile(rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b")
        clear_pattern = re.compile(
            rf"\bclr_country_flag\s*=\s*{re.escape(scheduled_flag)}\b"
        )
        all_sets = list(pattern.finditer(scheduler.body))
        direct_sets = list(pattern.finditer(self._direct_block_text(scheduler.body)))
        return bool(
            len(all_sets) == 1
            and len(direct_sets) == 1
            and all_sets[0].start() >= outer_end
            and not clear_pattern.search(scheduler.body)
        )

    def _is_exact_country_flag_guard(self, limit: str, flag: str) -> bool:
        children = list(self._iter_direct_child_blocks(limit))
        if len(children) != 1 or children[0][0].upper() != "NOT":
            return False
        return bool(
            not self._direct_block_text(limit).strip()
            and re.fullmatch(
                rf"\s*has_country_flag\s*=\s*{re.escape(flag)}\s*",
                children[0][3],
            )
        )

    def _is_exact_gpu_2000_limit(self, limit: str) -> bool:
        if not self._direct_has_exact_clauses(
            limit,
            (r"\bhas_start_date\s*<\s*2000\.1\.2\b",),
            allow_blocks=True,
        ):
            return False
        not_terms: List[str] = []
        owner_sets: List[Set[str]] = []
        for name, _start, _end, body in self._iter_direct_child_blocks(limit):
            upper = name.upper()
            if upper == "NOT" and not list(self._iter_direct_child_blocks(body)):
                not_terms.append(" ".join(body.split()))
                continue
            if upper == "OR" and not list(self._iter_direct_child_blocks(body)):
                tags = re.findall(r"\boriginal_tag\s*=\s*([A-Z]{3})\b", body)
                residual = re.sub(r"\boriginal_tag\s*=\s*[A-Z]{3}\b", "", body)
                if residual.strip() or len(tags) != len(set(tags)):
                    return False
                owner_sets.append(set(tags))
                continue
            return False
        return bool(
            sorted(not_terms)
            == sorted(
                (
                    "has_country_flag = collapsed_nation",
                    "has_start_date < 2000.1.1",
                    "has_country_flag = gpu_development_1_resolved",
                )
            )
            and owner_sets == [{"USA", "CAN", "TAI"}]
        )

    def _is_exact_global_flag_guard(self, limit: str, flag: str) -> bool:
        children = list(self._iter_direct_child_blocks(limit))
        if len(children) != 1 or children[0][0].upper() != "NOT":
            return False
        if self._direct_block_text(limit).strip():
            return False
        not_body = children[0][3]
        return bool(
            re.fullmatch(rf"\s*has_global_flag\s*=\s*{re.escape(flag)}\s*", not_body)
        )

    def _event_is_owned_and_collapse_guarded(
        self, event: Optional[EventDef], tag: str
    ) -> bool:
        if event is None:
            return False
        trigger = self._direct_child_block(event.body, "trigger")
        if trigger is None:
            return False
        return bool(
            self._has_positive_original_tag(trigger, tag)
            and self._has_direct_negated_country_flag(trigger, "collapsed_nation")
        )

    def _event_matches_exact_trigger(
        self,
        event: Optional[EventDef],
        direct_clauses: Sequence[str],
        negated_terms: Sequence[str],
    ) -> bool:
        if event is None:
            return False
        trigger = self._direct_child_block(event.body, "trigger")
        if trigger is None:
            return False
        return bool(
            self._direct_has_exact_clauses(trigger, direct_clauses, allow_blocks=True)
            and self._exact_not_terms(trigger, negated_terms)
        )

    def _gpu_event_matches_exact_trigger(self, event: Optional[EventDef]) -> bool:
        if event is None:
            return False
        trigger = self._direct_child_block(event.body, "trigger")
        if trigger is None or self._direct_block_text(trigger).strip():
            return False
        not_terms: List[str] = []
        owners: List[Set[str]] = []
        for name, _start, _end, body in self._iter_direct_child_blocks(trigger):
            upper = name.upper()
            if upper == "NOT" and not list(self._iter_direct_child_blocks(body)):
                not_terms.append(" ".join(body.split()))
                continue
            if upper == "OR" and not list(self._iter_direct_child_blocks(body)):
                tags = re.findall(r"\boriginal_tag\s*=\s*([A-Z]{3})\b", body)
                residual = re.sub(r"\boriginal_tag\s*=\s*[A-Z]{3}\b", "", body)
                if residual.strip() or len(tags) != len(set(tags)):
                    return False
                owners.append(set(tags))
                continue
            return False
        return bool(
            sorted(not_terms)
            == sorted(
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = gpu_development_1_resolved",
                )
            )
            and owners == [{"USA", "CAN", "TAI"}]
        )

    def _has_positive_original_tag(
        self, trigger: str, tag: str, negated: bool = False
    ) -> bool:
        direct = self._direct_block_text(trigger)
        if not negated and re.search(
            rf"\boriginal_tag\s*=\s*{re.escape(tag)}\b", direct
        ):
            return True
        for name, _start, _end, body in self._iter_direct_child_blocks(trigger):
            upper = name.upper()
            if upper == "NOT":
                if self._has_positive_original_tag(body, tag, not negated):
                    return True
            elif upper in ("AND", "OR") and self._has_positive_original_tag(
                body, tag, negated
            ):
                return True
        return False

    def _validate_usa_2000_startup_schedule(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        bootstrap: Optional[BlockDef],
        startup: Optional[BlockDef],
        full_branch: str,
        full_usa_body: str,
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []

        def sole_effect(name: str) -> Optional[BlockDef]:
            definitions = effect_defs.get(name, [])
            if len(definitions) != 1:
                findings.append(
                    (
                        f"USA 2000 startup schedule requires exactly one {name}; found {len(definitions)}",
                        "common/scripted_effects",
                        definitions[0].line if definitions else 0,
                    )
                )
                return None
            return definitions[0]

        gpu_scheduler = sole_effect("gpu_development_schedule_current_year_events")
        ibm_scheduler = sole_effect("USA_ibm_schedule_prehistory")
        e3_scheduler = sole_effect("USA_e3_schedule_current_year_events")
        scheduled_flag_owners = {
            "gpu_development_start_year_events_scheduled": gpu_scheduler,
            "USA_e3_start_year_events_scheduled": e3_scheduler,
            "USA_ibm_event_12_scheduled": ibm_scheduler,
            "USA_ibm_event_13_scheduled": ibm_scheduler,
        }
        scheduled_flag_writes = self._country_flag_write_sites(scheduled_flag_owners)
        for flag, owner in scheduled_flag_owners.items():
            sets, clears = scheduled_flag_writes[flag]
            expected_file = owner.file.replace("\\", "/") if owner else ""
            actual_files = [path.replace("\\", "/") for path, _line in sets]
            if len(sets) != 1 or actual_files != [expected_file] or clears:
                rendered_sets = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}" for path, line in sets
                )
                rendered_clears = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}" for path, line in clears
                )
                findings.append(
                    (
                        f"{flag} must be set only by {owner.name if owner else 'its scheduler'} and never cleared; sets {rendered_sets or 'none'}, clears {rendered_clears or 'none'}",
                        owner.file if owner else "common/scripted_effects",
                        owner.line if owner else 0,
                    )
                )
        for scheduler, event_id, scheduled_flag in (
            (
                gpu_scheduler,
                "gpu_development.1",
                "gpu_development_start_year_events_scheduled",
            ),
            (
                e3_scheduler,
                "USA_e3_events.1",
                "USA_e3_start_year_events_scheduled",
            ),
        ):
            if scheduler and not self._scheduler_has_replay_guard(
                scheduler, event_id, scheduled_flag
            ):
                findings.append(
                    (
                        f"{scheduler.name} must guard all start-year queues with {scheduled_flag} and set it directly after dispatch",
                        scheduler.file,
                        scheduler.line,
                    )
                )
        for scheduler, event_id in (
            (gpu_scheduler, "gpu_development.1"),
            (e3_scheduler, "USA_e3_events.1"),
        ):
            if scheduler and self._scheduler_window_years(scheduler, event_id) != {
                2000
            }:
                findings.append(
                    (
                        f"{scheduler.name} must schedule {event_id} only in the 2000 January 1 window",
                        scheduler.file,
                        scheduler.line,
                    )
                )

        if gpu_scheduler:
            gpu_branches = self._event_guard_branches(
                gpu_scheduler.body, "gpu_development.1"
            )
            gpu_guard_valid = False
            if len(gpu_branches) == 1:
                gpu_limit = self._direct_child_block(gpu_branches[0], "limit") or ""
                gpu_guard_valid = bool(
                    self._is_exact_gpu_2000_limit(gpu_limit)
                    and self._has_positive_original_tag(gpu_limit, "USA")
                )
            if not gpu_guard_valid:
                findings.append(
                    (
                        "gpu_development.1 must be directly scheduled by one exact 2000 window that permits USA and excludes collapsed nations",
                        gpu_scheduler.file,
                        gpu_scheduler.line,
                    )
                )

        if e3_scheduler:
            e3_branches = self._event_guard_branches(
                e3_scheduler.body, "USA_e3_events.1"
            )
            e3_limit = (
                self._direct_child_block(e3_branches[0], "limit") or ""
                if len(e3_branches) == 1
                else ""
            )
            if len(e3_branches) != 1 or not self._is_exact_e3_2000_limit(e3_limit):
                findings.append(
                    (
                        "USA_e3_events.1 must be directly scheduled by one exact 2000 January 1 window",
                        e3_scheduler.file,
                        e3_scheduler.line,
                    )
                )

        sources = {
            "USA_oem_events.13": (bootstrap, bootstrap.body if bootstrap else "", 90),
            "gpu_development.1": (
                gpu_scheduler,
                gpu_scheduler.body if gpu_scheduler else "",
                110,
            ),
            "USA_ibm_events.90": (
                startup,
                full_usa_body,
                1,
            ),
            "USA_e3_events.90": (
                startup,
                full_usa_body,
                1,
            ),
            "USA_hp_events.1": (
                startup,
                full_usa_body,
                153,
            ),
            "USA_ibm_events.12": (
                ibm_scheduler,
                ibm_scheduler.body if ibm_scheduler else "",
                30,
            ),
            "USA_ibm_events.13": (
                ibm_scheduler,
                ibm_scheduler.body if ibm_scheduler else "",
                120,
            ),
            "USA_e3_events.1": (
                e3_scheduler,
                e3_scheduler.body if e3_scheduler else "",
                131,
            ),
        }
        delays: Dict[str, int] = {}
        for event_id, (owner, body, expected_delay) in sources.items():
            actual_delays = self._event_delays_in_body(body, event_id)
            if actual_delays != [expected_delay]:
                findings.append(
                    (
                        f"USA 2000 startup schedule requires {event_id} at days = {expected_delay}; found {', '.join(str(value) for value in actual_delays) or 'none'}",
                        owner.file if owner else "common/scripted_effects",
                        owner.line if owner else 0,
                    )
                )
            if len(actual_delays) == 1:
                delays[event_id] = actual_delays[0]

        ibm_anchor = event_defs.get("USA_ibm_events.90")
        ibm_early_branch = False
        if ibm_anchor:
            for immediate in ibm_anchor.immediates:
                for child, _start, _end, body in self._iter_direct_child_blocks(
                    immediate.body
                ):
                    limit = self._direct_child_block(body, "limit") or ""
                    if (
                        child == "if"
                        and self._direct_has_exact_clauses(
                            limit, (r"\bdate\s*<\s*2000\.2\.1\b",)
                        )
                        and "USA_ibm_initialize_state = yes"
                        in self._direct_block_text(body)
                        and "USA_ibm_schedule_prehistory = yes"
                        in self._direct_block_text(body)
                    ):
                        ibm_early_branch = True
        if not ibm_early_branch:
            findings.append(
                (
                    "USA_ibm_events.90 does not initialize IBM and call its prehistory scheduler on an early-2000 start",
                    ibm_anchor.file if ibm_anchor else "events/USA_ibm_events.txt",
                    ibm_anchor.line if ibm_anchor else 0,
                )
            )

        e3_anchor = event_defs.get("USA_e3_events.90")
        e3_immediate = (
            "\n".join(
                self._direct_block_text(immediate.body)
                for immediate in e3_anchor.immediates
            )
            if e3_anchor
            else ""
        )
        if not (
            len(re.findall(r"\bUSA_e3_reconstruct_history\s*=\s*yes\b", e3_immediate))
            == 1
            and len(
                re.findall(
                    r"\bUSA_e3_schedule_current_year_events\s*=\s*yes\b",
                    e3_immediate,
                )
            )
            == 1
        ):
            findings.append(
                (
                    "USA_e3_events.90 does not reconstruct E3 and call its current-year scheduler",
                    e3_anchor.file if e3_anchor else "events/USA_e3_events.txt",
                    e3_anchor.line if e3_anchor else 0,
                )
            )

        trigger_contracts = {
            "USA_oem_events.13": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
            "USA_ibm_events.12": (
                (
                    r"\boriginal_tag\s*=\s*USA\b",
                    r"\bhas_country_flag\s*=\s*USA_ibm_event_12_scheduled\b",
                ),
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = USA_ibm_event_12_resolved",
                ),
            ),
            "USA_ibm_events.13": (
                (
                    r"\boriginal_tag\s*=\s*USA\b",
                    r"\bhas_country_flag\s*=\s*USA_ibm_event_13_scheduled\b",
                ),
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = USA_ibm_event_13_resolved",
                ),
            ),
            "USA_ibm_events.90": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
            "USA_e3_events.1": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = USA_e3_opening_context_seen",
                ),
            ),
            "USA_e3_events.90": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
            "USA_hp_events.1": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
        }
        for event_id, (direct_clauses, negated_terms) in trigger_contracts.items():
            event = event_defs.get(event_id)
            if event and not self._event_matches_exact_trigger(
                event, direct_clauses, negated_terms
            ):
                findings.append(
                    (
                        f"{event_id} must retain its exact viable USA 2000 trigger contract",
                        event.file,
                        event.line,
                    )
                )

        gpu_event = event_defs.get("gpu_development.1")
        if gpu_event and not self._gpu_event_matches_exact_trigger(gpu_event):
            findings.append(
                (
                    "gpu_development.1 must retain its exact viable 2000 owner and replay trigger contract",
                    gpu_event.file,
                    gpu_event.line,
                )
            )

        if ibm_scheduler:
            for number in (12, 13):
                event_id = f"USA_ibm_events.{number}"
                scheduled_flag = f"USA_ibm_event_{number}_scheduled"
                resolved_flag = f"USA_ibm_event_{number}_resolved"
                branches = self._event_guard_branches(ibm_scheduler.body, event_id)
                valid_branch = False
                if len(branches) == 1:
                    branch = branches[0]
                    limit = self._direct_child_block(branch, "limit") or ""
                    direct = self._direct_block_text(branch)
                    set_match = re.search(
                        rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                        direct,
                    )
                    direct_set_count = len(
                        re.findall(
                            rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                            direct,
                        )
                    )
                    calls = self._direct_event_calls(branch, event_id)
                    event_position = calls[0][0] if len(calls) == 1 else -1
                    before_event = (
                        self._direct_block_text(branch[:event_position])
                        if event_position >= 0
                        else ""
                    )
                    before_set_count = len(
                        re.findall(
                            rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                            before_event,
                        )
                    )
                    valid_branch = bool(
                        set_match
                        and direct_set_count == 1
                        and before_set_count == 1
                        and event_position >= 0
                        and self._is_exact_ibm_queue_limit(
                            limit, scheduled_flag, resolved_flag
                        )
                    )
                if not valid_branch:
                    findings.append(
                        (
                            f"{event_id} must set {scheduled_flag} directly before queueing under scheduled/resolved replay guards",
                            ibm_scheduler.file,
                            ibm_scheduler.line,
                        )
                    )

                event = event_defs.get(event_id)
                trigger = (
                    self._direct_child_block(event.body, "trigger") if event else None
                )
                trigger_direct = self._direct_block_text(trigger or "")
                resolved_direct = (
                    "\n".join(
                        self._direct_block_text(immediate.body)
                        for immediate in event.immediates
                    )
                    if event
                    else ""
                )
                if not re.search(
                    rf"\bhas_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                    trigger_direct,
                ) or not re.search(
                    rf"\bset_country_flag\s*=\s*{re.escape(resolved_flag)}\b",
                    resolved_direct,
                ):
                    findings.append(
                        (
                            f"{event_id} must consume {scheduled_flag} and directly set {resolved_flag}",
                            event.file if event else "events/USA_ibm_events.txt",
                            event.line if event else 0,
                        )
                    )

        hp_guarded = False
        for limit, scope in self._oem_startup_country_branches(full_branch, "USA"):
            hp_calls = self._direct_event_calls(scope, "USA_hp_events.1")
            if (
                len(hp_calls) == 1
                and hp_calls[0][1] == 153
                and self._is_exact_hp_2000_limit(limit)
            ):
                hp_guarded = True
        if full_branch and not hp_guarded:
            findings.append(
                (
                    "USA_hp_events.1 is not guarded to the exact 2000.1.1 bookmark",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )

        if len(delays) == len(sources):
            start = date(2000, 1, 1)
            ibm_anchor_date = start + timedelta(days=delays["USA_ibm_events.90"])
            e3_anchor_date = start + timedelta(days=delays["USA_e3_events.90"])
            actual_schedule = {
                "USA_ibm_events.90": ibm_anchor_date,
                "USA_e3_events.90": e3_anchor_date,
                "USA_ibm_events.12": ibm_anchor_date
                + timedelta(days=delays["USA_ibm_events.12"]),
                "USA_oem_events.13": start
                + timedelta(days=delays["USA_oem_events.13"]),
                "gpu_development.1": start
                + timedelta(days=delays["gpu_development.1"]),
                "USA_ibm_events.13": ibm_anchor_date
                + timedelta(days=delays["USA_ibm_events.13"]),
                "USA_e3_events.1": e3_anchor_date
                + timedelta(days=delays["USA_e3_events.1"]),
                "USA_hp_events.1": start + timedelta(days=delays["USA_hp_events.1"]),
            }
            expected_schedule = {
                "USA_ibm_events.90": date(2000, 1, 2),
                "USA_e3_events.90": date(2000, 1, 2),
                "USA_ibm_events.12": date(2000, 2, 1),
                "USA_oem_events.13": date(2000, 3, 31),
                "gpu_development.1": date(2000, 4, 20),
                "USA_ibm_events.13": date(2000, 5, 1),
                "USA_e3_events.1": date(2000, 5, 12),
                "USA_hp_events.1": date(2000, 6, 2),
            }
            for event_id, expected_date in expected_schedule.items():
                if actual_schedule[event_id] != expected_date:
                    findings.append(
                        (
                            f"USA 2000 startup schedule resolves {event_id} on {actual_schedule[event_id].isoformat()}; expected {expected_date.isoformat()}",
                            (
                                sources[event_id][0].file
                                if sources[event_id][0]
                                else "common/scripted_effects"
                            ),
                            sources[event_id][0].line if sources[event_id][0] else 0,
                        )
                    )

        return findings

    def _startup_full_branch(self, startup_body: str) -> str:
        """The Full-rule arm of corporate_history_on_startup, or an empty string.

        Outcomes Only always reconstructs; only the Full arm proves a later start
        still catches its chain up without the hidden .90 anchor.
        """
        for name, _start, _end, body in self._iter_direct_child_blocks(startup_body):
            if name != "if":
                continue
            limit = self._direct_child_block(body, "limit")
            if limit and self._is_exact_yes_trigger(
                limit, "corporate_history_full_enabled"
            ):
                return body
        return ""

    def _startup_outcomes_branch(self, startup_body: str) -> str:
        for name, _start, _end, body in self._iter_direct_child_blocks(startup_body):
            if name != "else_if":
                continue
            limit = self._direct_child_block(body, "limit")
            if limit and self._is_exact_yes_trigger(
                limit, "corporate_history_outcomes_only_enabled"
            ):
                return body
        return ""

    def _country_bootstrap_tag_branches(
        self, bootstrap_body: str, tag: str
    ) -> List[str]:
        branches: List[str] = []
        original_tag = rf"\boriginal_tag\s*=\s*{re.escape(tag)}\b"
        for name, _start, _end, body in self._iter_direct_child_blocks(bootstrap_body):
            if name not in ("if", "else_if"):
                continue
            limit = self._direct_child_block(body, "limit") or ""
            if self._direct_has_exact_clauses(limit, (original_tag,)):
                branches.append(body)
        return branches

    def _country_bootstrap_full_branches(self, tag_branch: str) -> List[str]:
        branches: List[str] = []
        for name, _start, _end, body in self._iter_direct_child_blocks(tag_branch):
            if name not in ("if", "else_if"):
                continue
            limit = self._direct_child_block(body, "limit") or ""
            if self._mode_constraint(limit) == {"full"}:
                branches.append(body)
        return branches

    def _direct_effect_call_count(self, body: str, effect_name: str) -> int:
        direct = self._direct_block_text(body)
        return len(re.findall(rf"\b{re.escape(effect_name)}\s*=\s*yes\b", direct))

    def _startup_reaches_scheduler(
        self, chain: ChainConfig, startup_body: str, event_defs: Dict[str, EventDef]
    ) -> bool:
        if f"{chain.scheduler_effect} = yes" in startup_body:
            return True
        anchor = event_defs.get(chain.hidden_ninety_id)
        if anchor is None or chain.hidden_ninety_id not in startup_body:
            return False
        return any(
            f"{chain.scheduler_effect} = yes" in immediate.body
            for immediate in anchor.immediates
        )

    def _script_effect_call_sites(self, effect_name: str) -> List[Tuple[str, int]]:
        if self._effect_call_parents_cache is None:
            effect_defs = self._load_top_level_blocks(
                ["common/scripted_effects/**/*.txt"]
            )
            self._effect_call_parents_cache = self._effect_call_parents(effect_defs)
            self._effect_call_children_cache = self._effect_call_children(effect_defs)
        parents = self._effect_call_parents_cache
        children = self._effect_call_children_cache or {}

        reachable = {effect_name}
        pending = [effect_name]
        while pending:
            target = pending.pop()
            for parent in parents.get(target, set()):
                if parent in reachable:
                    continue
                reachable.add(parent)
                pending.append(parent)

        if self._on_action_effect_calls_cache is None:
            self._on_action_effect_calls_cache = defaultdict(list)
            for filepath in self._collect_text_files(["common/on_actions/**/*.txt"]):
                try:
                    text = strip_comments(
                        Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                    )
                except OSError:
                    continue
                rel = self._relpath(filepath)
                line = 1
                cursor = 0
                for match in _EFFECT_YES_RE.finditer(text):
                    line += text.count("\n", cursor, match.start())
                    cursor = match.start()
                    self._on_action_effect_calls_cache[match.group(1)].append(
                        (rel, line, match.start())
                    )

        callers: List[Tuple[str, int, str, int]] = []
        for name in reachable.intersection(self._on_action_effect_calls_cache):
            path_count = self._effect_path_count(name, effect_name, children)
            for rel, line, offset in self._on_action_effect_calls_cache[name]:
                callers.extend((rel, line, name, offset) for _path in range(path_count))
        return [(path, line) for path, line, _name, _offset in sorted(callers)]

    def _effect_call_parents(
        self, effect_defs: Dict[str, List[BlockDef]]
    ) -> Dict[str, Set[str]]:
        parents: Dict[str, Set[str]] = {}
        for owner, definitions in effect_defs.items():
            for definition in definitions:
                for match in _EFFECT_YES_RE.finditer(definition.body):
                    parents.setdefault(match.group(1), set()).add(owner)
        return parents

    def _effect_call_children(
        self, effect_defs: Dict[str, List[BlockDef]]
    ) -> Dict[str, List[str]]:
        effect_names = set(effect_defs)
        children: Dict[str, List[str]] = {}
        for owner, definitions in effect_defs.items():
            for definition in definitions:
                for match in _EFFECT_YES_RE.finditer(definition.body):
                    child = match.group(1)
                    if child in effect_names:
                        children.setdefault(owner, []).append(child)
        return children

    def _effect_path_count(
        self,
        source: str,
        target: str,
        children: Dict[str, List[str]],
        visiting: Optional[FrozenSet[str]] = None,
    ) -> int:
        if source == target:
            return 1
        active = visiting or frozenset()
        if source in active:
            return 0
        active = active | {source}
        count = 0
        for child in children.get(source, []):
            count += self._effect_path_count(child, target, children, active)
            if count >= 2:
                return 2
        return count

    def _mixed_script_descendants(
        self,
        body: str,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
    ) -> Tuple[Set[str], Set[str]]:
        reachable_effects: Set[str] = set()
        reachable_events: Set[str] = set()
        pending_bodies = [body]
        while pending_bodies:
            current = pending_bodies.pop()
            for match in _EFFECT_YES_RE.finditer(current):
                name = match.group(1)
                if name in reachable_effects or name not in effect_defs:
                    continue
                reachable_effects.add(name)
                pending_bodies.extend(
                    definition.body for definition in effect_defs[name]
                )
            for event_id, _line in self._find_event_calls(current, 1, frozenset()):
                if event_id in reachable_events:
                    continue
                reachable_events.add(event_id)
                event = event_defs.get(event_id)
                if event is not None:
                    pending_bodies.append(event.body)
        return reachable_effects, reachable_events

    def _raw_script_call_sites(
        self, effect_name: str, patterns: Sequence[str]
    ) -> List[Tuple[str, int]]:
        pattern = re.compile(rf"\b{re.escape(effect_name)}\s*=\s*yes\b")
        needle = effect_name.encode("ascii")
        callers: List[Tuple[str, int]] = []
        for filepath in self._collect_text_files(patterns):
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            if needle not in raw:
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            callers.extend(
                (self._relpath(filepath), self._line(text, match.start()))
                for match in pattern.finditer(text)
            )
        return callers

    def _chain_is_registered_in_startup(self, chain: ChainConfig, body: str) -> bool:
        markers = (
            f"{chain.reconstruct_effect} = yes",
            f"{chain.scheduler_effect} = yes",
            chain.hidden_ninety_id,
            f"{chain.namespace}.1",
        )
        return any(marker in body for marker in markers)
