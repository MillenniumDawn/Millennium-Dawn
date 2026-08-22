"""Filesystem indexing and Clausewitz parsing helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from shared_utils import extract_block_from_text, strip_comments

from .model import (
    _ADD_IDEA_RE,
    _BLOCK_HEADER_RE,
    _EFFECT_YES_RE,
    _EVENT_ALT,
    _EVENT_DEF_RE,
    _EVENT_KEYWORDS,
    _EVENT_LONG_CALL_RE,
    _EVENT_SHORT_CALL_RE,
    _ID_RE,
    _IMMEDIATE_RE,
    _MARKER_TRIGGER_RE,
    _OPTION_RE,
    _REMOVE_IDEA_BLOCK_RE,
    _REMOVE_IDEA_RE,
    _TOP_LEVEL_BLOCK_RE,
    _USA_2000_STARTUP_EVENTS,
    BlockDef,
    CallSite,
    ChainConfig,
    EventDef,
    IdeaDef,
)


class ParsingMixin:
    def _collect_text_files(
        self, patterns: Sequence[str], ignore_staged: bool = True
    ) -> List[str]:
        seen: Set[str] = set()
        files: List[str] = []
        for pattern in patterns:
            for path in self._collect_files([pattern], ignore_staged=ignore_staged):
                if path not in seen:
                    seen.add(path)
                    files.append(path)
        return files

    def _load_top_level_blocks(
        self, patterns: Sequence[str]
    ) -> Dict[str, List[BlockDef]]:
        results: Dict[str, List[BlockDef]] = {}
        for filepath in self._collect_text_files(patterns):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            for match in _TOP_LEVEL_BLOCK_RE.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                name = match.group(1)
                results.setdefault(name, []).append(
                    BlockDef(
                        name,
                        self._relpath(filepath),
                        self._line(text, match.start()),
                        body,
                    )
                )
        return results

    def _load_events(self) -> Dict[str, EventDef]:
        events: Dict[str, EventDef] = {}
        for filepath in self._collect_text_files(["events/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            rel = self._relpath(filepath)
            for match in _EVENT_DEF_RE.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                id_match = _ID_RE.search(body)
                if not id_match:
                    continue
                event_id = id_match.group(1)
                event_def = EventDef(
                    event_id=event_id,
                    file=rel,
                    line=self._line(text, match.start()),
                    body=body,
                    hidden=bool(re.search(r"\bhidden\s*=\s*yes\b", body)),
                )
                event_def.options = self._nested_blocks(
                    body,
                    _OPTION_RE,
                    f"{event_id}:option",
                    rel,
                    event_def.line,
                )
                event_def.immediates = self._nested_blocks(
                    body,
                    _IMMEDIATE_RE,
                    f"{event_id}:immediate",
                    rel,
                    event_def.line,
                )
                events[event_id] = event_def
        return events

    def _load_idea_definitions(
        self, chains: Sequence[ChainConfig], event_defs: Dict[str, EventDef]
    ) -> Dict[str, IdeaDef]:
        idea_ids: Set[str] = set()
        chain_effects = self._load_top_level_blocks(
            ["common/scripted_effects/**/*_effects.txt"]
        )
        for chain in chains:
            idea_ids.update(chain.outcome_ideas)
            prefixes = chain.outcome_idea_prefixes
            if not prefixes:
                continue
            bodies = [
                effect.body
                for defs in chain_effects.values()
                for effect in defs
                if effect.name.startswith(chain.root)
            ]
            bodies.extend(
                event.body
                for event in event_defs.values()
                if event.event_id.startswith(chain.namespace + ".")
            )
            for body in bodies:
                idea_ids.update(self._idea_ids_in(body, prefixes))
        if not idea_ids:
            return {}

        results: Dict[str, IdeaDef] = {}
        idea_pattern = re.compile(
            r"(?m)^\s*("
            + "|".join(sorted(re.escape(i) for i in idea_ids))
            + r")\s*=\s*\{"
        )
        for filepath in self._collect_text_files(["common/ideas/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            rel = self._relpath(filepath)
            for match in idea_pattern.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                idea_id = match.group(1)
                results[idea_id] = IdeaDef(
                    idea_id=idea_id,
                    file=rel,
                    line=self._line(text, match.start()),
                    body=body,
                )
        return results

    def _idea_ids_in(self, body: str, prefixes: Sequence[str]) -> Set[str]:
        found: Set[str] = set()
        for pattern in (_ADD_IDEA_RE, _REMOVE_IDEA_RE):
            for match in pattern.finditer(body):
                idea_id = match.group(1)
                if any(idea_id.startswith(prefix) for prefix in prefixes):
                    found.add(idea_id)
        for match in _REMOVE_IDEA_BLOCK_RE.finditer(body):
            block, end = extract_block_from_text(body, match.end() - 1)
            if end == -1:
                continue
            for idea_id in re.findall(r"\b([A-Za-z0-9_]+)\b", block):
                if any(idea_id.startswith(prefix) for prefix in prefixes):
                    found.add(idea_id)
        return found

    def _load_event_call_sites(
        self,
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
        namespaces: Set[str],
    ) -> Dict[str, List[CallSite]]:
        tracked = frozenset(event_defs)
        call_sites: Dict[str, List[CallSite]] = {event_id: [] for event_id in tracked}

        for defs in effect_defs.values():
            for effect in defs:
                for target, line in self._find_event_calls(
                    effect.body, effect.line, tracked
                ):
                    call_sites.setdefault(target, []).append(
                        CallSite(target, effect.file, line, "effect", effect.name)
                    )

        for event in event_defs.values():
            for idx, option in enumerate(event.options, start=1):
                owner = f"{event.event_id}.option_{idx}"
                for target, line in self._find_event_calls(
                    option.body, option.line, tracked
                ):
                    call_sites.setdefault(target, []).append(
                        CallSite(target, option.file, line, "event-option", owner)
                    )
            for idx, immediate in enumerate(event.immediates, start=1):
                owner = f"{event.event_id}.immediate_{idx}"
                for target, line in self._find_event_calls(
                    immediate.body, immediate.line, tracked
                ):
                    call_sites.setdefault(target, []).append(
                        CallSite(target, immediate.file, line, "event-immediate", owner)
                    )

        generic_patterns = [
            "common/decisions/**/*.txt",
            "common/national_focus/**/*.txt",
            "common/on_actions/**/*.txt",
        ]
        for filepath in self._collect_text_files(generic_patterns):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            rel = self._relpath(filepath)
            for target, line in self._find_event_calls(text, 1, tracked):
                call_sites.setdefault(target, []).append(
                    CallSite(target, rel, line, "script", f"{rel}:{line}")
                )

        startup_ids = frozenset(_USA_2000_STARTUP_EVENTS).intersection(tracked)
        startup_needles = tuple(event_id.encode("ascii") for event_id in startup_ids)
        covered = (
            "common/decisions/",
            "common/national_focus/",
            "common/on_actions/",
            "common/scripted_effects/",
        )
        for filepath in self._collect_text_files(
            ["common/**/*.txt", "history/**/*.txt"]
        ):
            rel = self._relpath(filepath)
            normalized = rel.replace("\\", "/")
            if normalized.startswith(covered):
                continue
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            if not any(needle in raw for needle in startup_needles):
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            for target, line in self._find_event_calls(text, 1, startup_ids):
                call_sites.setdefault(target, []).append(
                    CallSite(target, rel, line, "script", f"{rel}:{line}")
                )
        return call_sites

    def _find_event_calls(
        self, text: str, base_line: int, tracked_ids: Iterable[str]
    ) -> List[Tuple[str, int]]:
        tracked = set(tracked_ids)
        results: List[Tuple[str, int]] = []
        for match in _EVENT_SHORT_CALL_RE.finditer(text):
            target = match.group(1)
            if tracked and target not in tracked:
                continue
            results.append((target, base_line + self._line(text, match.start()) - 1))
        for match in _EVENT_LONG_CALL_RE.finditer(text):
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                continue
            id_match = _ID_RE.search(body)
            if not id_match:
                continue
            target = id_match.group(1)
            if tracked and target not in tracked:
                continue
            results.append((target, base_line + self._line(text, match.start()) - 1))
        return results

    def _event_namespaces_in_text(self, text: str) -> Set[str]:
        namespaces = set()
        for target, _line in self._find_event_calls(text, 1, frozenset()):
            if "." in target:
                namespaces.add(target.split(".", 1)[0])
        return namespaces

    def _nested_blocks(
        self,
        text: str,
        pattern: re.Pattern[str],
        owner: str,
        file: str,
        base_line: int,
    ) -> List[BlockDef]:
        blocks = []
        for match in pattern.finditer(text):
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                continue
            blocks.append(
                BlockDef(
                    owner,
                    file,
                    base_line + self._line(text, match.start()) - 1,
                    body,
                )
            )
        return blocks

    def _require_effect(
        self, effect_defs: Dict[str, List[BlockDef]], effect_name: str, message: str
    ) -> List[Tuple[str, str, int]]:
        if effect_name in effect_defs:
            return []
        return [(message, f"common/scripted_effects/{effect_name}.txt", 0)]

    def _dedupe_callers(self, callers: Sequence[CallSite]) -> List[CallSite]:
        by_key: Dict[str, CallSite] = {}
        for caller in callers:
            by_key.setdefault(caller.key, caller)
        return list(by_key.values())

    def _effect_call_counts(
        self, effect_defs: Dict[str, List[BlockDef]], targets: Sequence[str]
    ) -> Dict[str, List[Tuple[str, int, str]]]:
        target_set = set(targets)
        counts: Dict[str, List[Tuple[str, int, str]]] = {name: [] for name in targets}
        for defs in effect_defs.values():
            for effect in defs:
                for match in _EFFECT_YES_RE.finditer(effect.body):
                    name = match.group(1)
                    if name in target_set:
                        counts[name].append(
                            (
                                effect.file,
                                effect.line
                                + self._line(effect.body, match.start())
                                - 1,
                                effect.name,
                            )
                        )
        return counts

    def _flag_is_produced(
        self, flag: str, effect_defs: Dict[str, List[BlockDef]]
    ) -> bool:
        return bool(self._flag_producers(flag, effect_defs))

    def _flag_producers(
        self, flag: str, effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, int]]:
        producers = []
        pattern = re.compile(r"\bset_country_flag\s*=\s*" + re.escape(flag) + r"\b")
        for defs in effect_defs.values():
            for effect in defs:
                for match in pattern.finditer(effect.body):
                    producers.append(
                        (
                            effect.file,
                            effect.line + self._line(effect.body, match.start()) - 1,
                        )
                    )
        return producers

    def _monthly_consumers(
        self, flag: str, effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, int]]:
        consumers = []
        pattern = re.compile(re.escape(flag))
        for name, defs in effect_defs.items():
            if not name.endswith("_corporate_history_monthly_outcomes"):
                continue
            for effect in defs:
                for match in pattern.finditer(effect.body):
                    consumers.append(
                        (
                            effect.file,
                            effect.line + self._line(effect.body, match.start()) - 1,
                        )
                    )
                    break
        return consumers

    def _event_definition_sites(
        self, tracked: FrozenSet[str]
    ) -> Dict[str, List[Tuple[str, int]]]:
        sites: Dict[str, List[Tuple[str, int]]] = {event_id: [] for event_id in tracked}
        for filepath in self._collect_text_files(["events/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            for match in _EVENT_DEF_RE.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                id_match = _ID_RE.search(body)
                if id_match and id_match.group(1) in tracked:
                    sites[id_match.group(1)].append(
                        (self._relpath(filepath), self._line(text, match.start()))
                    )
        return sites

    def _direct_block_text(self, body: str) -> str:
        residual: List[str] = []
        cursor = 0
        for _child, start, end, _nested in self._iter_direct_child_blocks(body):
            residual.append(body[cursor:start])
            cursor = end
        residual.append(body[cursor:])
        return "".join(residual)

    def _event_delays_in_body(self, body: str, event_id: str) -> List[int]:
        delays: List[int] = []
        for match in _EVENT_LONG_CALL_RE.finditer(body):
            call, end = extract_block_from_text(body, match.end() - 1)
            if end == -1:
                continue
            id_match = _ID_RE.search(call)
            if not id_match or id_match.group(1) != event_id:
                continue
            days_match = re.search(r"\bdays\s*=\s*(\d+)\b", call)
            if days_match:
                delays.append(int(days_match.group(1)))
        return delays

    def _direct_event_calls(
        self, body: str, event_id: str
    ) -> List[Tuple[int, Optional[int]]]:
        calls: List[Tuple[int, Optional[int]]] = []
        for child, start, _end, call in self._iter_direct_child_blocks(body):
            if child not in _EVENT_KEYWORDS:
                continue
            id_match = _ID_RE.search(call)
            if not id_match or id_match.group(1) != event_id:
                continue
            days_match = re.search(r"\bdays\s*=\s*(\d+)\b", call)
            calls.append((start, int(days_match.group(1)) if days_match else None))
        short_pattern = re.compile(
            rf"\b(?:{_EVENT_ALT})\s*=\s*{re.escape(event_id)}\b(?!\s*\{{)"
        )
        direct_text = self._direct_block_text(body)
        for match in short_pattern.finditer(direct_text):
            calls.append((match.start(), None))
        return calls

    def _event_guard_branches(self, body: str, event_id: str) -> List[str]:
        branches: List[str] = []
        for child, _start, _end, branch in self._iter_direct_child_blocks(body):
            if child not in ("if", "else_if"):
                continue
            if self._direct_event_calls(branch, event_id):
                branches.append(branch)
            branches.extend(self._event_guard_branches(branch, event_id))
        return branches

    def _has_direct_negated_country_flag(self, trigger: str, flag: str) -> bool:
        for child, _start, _end, body in self._iter_direct_child_blocks(trigger):
            if child.upper() != "NOT":
                continue
            if re.fullmatch(rf"\s*has_country_flag\s*=\s*{re.escape(flag)}\s*", body):
                return True
        return False

    def _iter_direct_child_blocks(
        self, text: str
    ) -> Iterable[Tuple[str, int, int, str]]:
        pos = 0
        while True:
            match = _BLOCK_HEADER_RE.search(text, pos)
            if not match:
                return
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                pos = match.end()
                continue
            yield match.group(1), match.start(), end, body
            pos = end

    def _direct_child_block(self, text: str, name: str):
        matches = [
            body
            for child, _start, _end, body in self._iter_direct_child_blocks(text)
            if child == name
        ]
        return matches[0] if len(matches) == 1 else None

    def _negated_marker_in_trigger(
        self, text: str, negated: bool = False, disjunction: bool = False
    ) -> bool:
        """True when a sibling-marker check sits under an odd number of NOTs.

        Only ``NOT``/``OR``/``AND`` are descended into: a marker read inside a
        scope switch guards a different country, and a positive marker check is
        a branch selector rather than a replay guard. Siblings of a conjunction
        are AND-ed, so two bare markers under one ``NOT`` mean "not both at
        once" and still let the branch replay; only ``OR`` may carry a set.
        """
        residual: List[str] = []
        cursor = 0
        markers = 0
        for name, start, end, body in self._iter_direct_child_blocks(text):
            residual.append(text[cursor:start])
            cursor = end
            upper = name.upper()
            if upper == "NOT":
                if self._negated_marker_in_trigger(body, not negated):
                    return True
            elif upper in ("OR", "AND"):
                if self._negated_marker_in_trigger(body, negated, upper == "OR"):
                    return True
            elif upper in ("HAS_COUNTRY_FLAG", "HAS_IDEA"):
                markers += 1
        residual.append(text[cursor:])
        markers += len(_MARKER_TRIGGER_RE.findall("".join(residual)))
        if not negated:
            return False
        return markers >= 1 if disjunction else markers == 1

    def _dedupe_findings(
        self, findings: Sequence[Tuple[str, str, int]]
    ) -> List[Tuple[str, str, int]]:
        seen: Set[Tuple[str, str, int]] = set()
        deduped: List[Tuple[str, str, int]] = []
        for finding in findings:
            if finding not in seen:
                seen.add(finding)
                deduped.append(finding)
        return deduped

    def _relpath(self, path: os.PathLike | str) -> str:
        return os.path.relpath(str(path), self.mod_path)

    @staticmethod
    def _line(text: str, pos: int) -> int:
        return text.count("\n", 0, pos) + 1
