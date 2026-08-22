"""Corporate History contract data model and shared parsing definitions."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from typing import (
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared_utils import blank_quoted_strings, strip_comments

TITLE = "CORPORATE HISTORY CONTRACT VALIDATION"

_EVENT_KEYWORDS = (
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
)
_EVENT_ALT = "|".join(_EVENT_KEYWORDS)
_EVENT_DEF_RE = re.compile(r"(?m)^(" + _EVENT_ALT + r")\s*=\s*\{")
_BLOCK_IDENTIFIER = r"[A-Za-z0-9_.:@^\[\]-]+"
_TOP_LEVEL_BLOCK_RE = re.compile(r"(?m)^(" + _BLOCK_IDENTIFIER + r")\s*=\s*\{")
_OPTION_RE = re.compile(r"\boption\s*=\s*\{")
_IMMEDIATE_RE = re.compile(r"\bimmediate\s*=\s*\{")
_ID_RE = re.compile(r"\bid\s*=\s*([A-Za-z0-9_.]+)")
_EVENT_SHORT_CALL_RE = re.compile(
    r"\b(?:" + _EVENT_ALT + r")\s*=\s*([A-Za-z0-9_.]+)\b(?!\s*\{)"
)
_EVENT_LONG_CALL_RE = re.compile(r"\b(?:" + _EVENT_ALT + r")\s*=\s*\{")
_EFFECT_YES_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*=\s*yes\b")
_SET_VAR_RE = re.compile(
    r"\b(?:set_variable|add_to_variable|subtract_from_variable|multiply_variable|divide_variable)\s*=\s*\{\s*([A-Za-z0-9_]+)"
)
_CLAMP_VAR_RE = re.compile(
    r"\bclamp_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_]+)\s+min\s*=\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s+max\s*=\s*(-?(?:\d+(?:\.\d*)?|\.\d+))"
)
_SET_TEMP_CORP_RE = re.compile(
    r"\bset_temp_variable\s*=\s*\{\s*corp_value\s*=\s*([A-Za-z0-9_]+)\s*\}"
)
_DIRECT_CORP_CLAMP_RE = re.compile(r"\bcorporate_history_clamp_value\s*=\s*yes\b")
_ADD_IDEA_RE = re.compile(r"\badd_ideas\s*=\s*([A-Za-z0-9_]+)")
_REMOVE_IDEA_RE = re.compile(r"\bremove_ideas\s*=\s*([A-Za-z0-9_]+)")
_REMOVE_IDEA_BLOCK_RE = re.compile(r"\bremove_ideas\s*=\s*\{")
_BLOCK_HEADER_RE = re.compile(r"([A-Za-z0-9_.:@^\[\]-]+)\s*=\s*\{")
_MARKER_TRIGGER_RE = re.compile(r"\b(?:has_country_flag|has_idea)\s*=")
_LOC_KEY_PREFIX_RE = re.compile(r"^\s*([^\s:#]+):\d*(?:\s+.*)?$")
_VALID_LOC_VALUE_RE = re.compile(r'^\s*[^\s:#]+:\d*\s+"(?:\\.|[^"\\])*"\s*(?:#.*)?$')
_SCRIPT_TOKEN_CAPTURE = r"([A-Za-z0-9_.:@^\[\]-]+)"
_SCRIPT_TOKEN_RE = re.compile(r"[A-Za-z0-9_.:@^\[\]-]+")
_NATIVE_FLAG_WRITE_EFFECT_PATTERN = (
    r"(?:set|clr|modify)_"
    r"(?:character|country|country_pmc|global|mio|project|state|unit_leader)_flag"
)
_NATIVE_VARIABLE_BLOCK_EFFECTS = (
    "set_variable",
    "add_to_variable",
    "subtract_from_variable",
    "multiply_variable",
    "divide_variable",
    "modulo_variable",
    "clamp_variable",
    "randomize_variable",
    "set_variable_to_random",
)
_NATIVE_VARIABLE_BLOCK_EFFECT_PATTERN = (
    r"(?:" + "|".join(_NATIVE_VARIABLE_BLOCK_EFFECTS) + r")"
)
_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS = ("clear_variable", "round_variable")
_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECT_PATTERN = (
    r"(?:" + "|".join(_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS) + r")"
)
_NATIVE_ARRAY_BLOCK_EFFECTS = ("add_to_array", "remove_from_array", "resize_array")
_NATIVE_ARRAY_BLOCK_EFFECT_PATTERN = (
    r"(?:" + "|".join(_NATIVE_ARRAY_BLOCK_EFFECTS) + r")"
)
_NATIVE_WRITE_PATTERNS = (
    re.compile(
        r"\b" + _NATIVE_FLAG_WRITE_EFFECT_PATTERN + r"\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_FLAG_WRITE_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\bflag\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b" + _NATIVE_VARIABLE_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{\s*"
        r"(?:var\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_VARIABLE_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\bvar\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b"
        + _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECT_PATTERN
        + r"\s*=\s*"
        + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\b(?:var|which)\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b" + _NATIVE_ARRAY_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{\s*"
        r"(?:array\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_ARRAY_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\barray\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(r"\bclear_array\s*=\s*" + _SCRIPT_TOKEN_CAPTURE),
    re.compile(
        r"\bclear_array\s*=\s*\{[^{}]*?\barray\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:find_highest_in_array|find_lowest_in_array)\s*=\s*\{[^{}]*?"
        r"\bvalue\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:find_highest_in_array|find_lowest_in_array)\s*=\s*\{[^{}]*?"
        r"\bindex\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:add_ideas|remove_ideas|add_idea|remove_idea)\s*=\s*"
        + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\badd_timed_idea\s*=\s*\{[^{}]*?\bidea\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:complete_national_focus|uncomplete_national_focus|unlock_national_focus)\s*=\s*"
        r"(?:\{\s*focus\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b(?:" + _EVENT_ALT + r")\s*=\s*"
        r"(?:\{[^{}]*?\bid\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
)
_NATIVE_IDEA_BLOCK_RE = re.compile(
    r"\b(?:add_ideas|remove_ideas)\s*=\s*\{([^{}]*)\}", re.DOTALL
)
_NATIVE_CONTRACT_ROLES = (
    "effect",
    "trigger",
    "on_action",
    "event",
    "idea",
    "decision",
    "category",
)
_CUSTOM_EFFECT_REWARDS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("Political Power", re.compile(r"\badd_political_power\b")),
    ("Stability", re.compile(r"\badd_stability\b")),
    ("War Support", re.compile(r"\badd_war_support\b")),
    ("treasury changes", re.compile(r"\bmodify_treasury_effect\b")),
    ("research bonuses", re.compile(r"\badd_tech_bonus\b|\badd_research_slot\b")),
    (
        "factories",
        re.compile(
            r"\badd_building_construction\b[\s\S]{0,120}\b(?:industrial_complex|arms_factory|dockyard|office_park)\b"
        ),
    ),
    (
        "microchip plants",
        re.compile(
            r"\badd_building_construction\b[\s\S]{0,120}\bmicrochip_plant\b|\bproduction_speed_microchip_plant_factor\b"
        ),
    ),
    (
        "one-time economic rewards",
        re.compile(r"\badd_extra_state_shared_building_slots\b|\badd_resource\b"),
    ),
)


def _native_token_fragment(token: str, prefixes: Tuple[str, ...]) -> Optional[str]:
    for fragment in re.split(r"[.:@^\[\]]+", token):
        if fragment.startswith(prefixes):
            return fragment
    return None


def _collect_native_write_tokens(text: str, prefixes: Tuple[str, ...]) -> Set[str]:
    native_writes: Set[str] = set()
    for pattern in _NATIVE_WRITE_PATTERNS:
        for token in pattern.findall(text):
            fragment = _native_token_fragment(token, prefixes)
            if fragment:
                native_writes.add(fragment)
    for idea_block in _NATIVE_IDEA_BLOCK_RE.findall(text):
        for token in _SCRIPT_TOKEN_RE.findall(idea_block):
            fragment = _native_token_fragment(token, prefixes)
            if fragment:
                native_writes.add(fragment)
    return native_writes


_WRITE_KEYWORDS = (
    "set_country_flag",
    "clr_country_flag",
    "set_variable",
    "add_to_variable",
    "subtract_from_variable",
    "multiply_variable",
    "divide_variable",
    "clamp_variable",
    "add_ideas",
    "remove_ideas",
)
_READ_KEYWORDS = ("has_country_flag", "has_idea", "check_variable")
_OEM_STARTUP_EFFECT = "OEM_corporate_history_startup_bootstrap"
_OEM_STARTUP_FLAG = "GLOBAL_oem_corporate_history_startup_dispatched"
_OEM_STARTUP_ON_ACTION = "common/on_actions/01_oem_corporate_history_on_actions.txt"
_USA_2000_STARTUP_EVENTS = (
    "USA_oem_events.13",
    "gpu_development.1",
    "USA_ibm_events.12",
    "USA_ibm_events.13",
    "USA_ibm_events.90",
    "USA_e3_events.1",
    "USA_e3_events.90",
    "USA_hp_events.1",
)
_INDEPENDENT_SUBSYSTEM_FIELDS = frozenset(
    {
        "id",
        "kind",
        "namespaces",
        "event_ids",
        "owner_tags",
        "reconstruction_effects",
        "scheduler_entrypoints",
        "effect_roots",
        "mode_policy",
    }
)
_INDEPENDENT_EVENT_POLICY = "full_events_outcomes_reconstruct_off_inert"
_INDEPENDENT_DERIVED_POLICY = "derived_only"
_CORPORATE_MODES = frozenset({"full", "outcomes_only", "off"})


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and Decimal(str(value)).is_finite()
    )


def _is_repeatable_decision(text: str) -> bool:
    code = blank_quoted_strings(strip_comments(text))
    return bool(re.search(r"(?m)^\s*fire_only_once\s*=\s*no\s*$", code))


# Reusable corporate/computing policy programs are recurring government
# programmes, not construction projects: six months for operational levers,
# one year for major commitments, and never a two-year hold on the decision.
PROGRAM_CLASS_DURATION_DAYS: Mapping[str, int] = {
    "operational": 180,
    "major_commitment": 365,
}
REUSABLE_PROGRAM_MAX_DURATION_DAYS = 365
REUSABLE_PROGRAM_MAX_LOCKOUT_DAYS = 365


def _program_lifecycle_findings(
    label: str,
    program: Mapping[str, object],
    duration_key: str,
    lockout_model: str,
    source: str,
) -> List[Tuple[str, str, int]]:
    """Check one declared program against the approved duration classes.

    ``lockout_model`` is ``concurrent`` when the re-enable timer runs alongside
    the timed idea (``days_re_enable``) and ``sequential`` when the cooldown
    only starts once the active program ends (``days_remove`` + cooldown flag).
    """

    findings: List[Tuple[str, str, int]] = []
    program_class = str(program.get("program_class", ""))
    expected = PROGRAM_CLASS_DURATION_DAYS.get(program_class)
    if expected is None:
        findings.append(
            (
                f"{label} must declare program_class as one of "
                + ", ".join(sorted(PROGRAM_CLASS_DURATION_DAYS)),
                source,
                1,
            )
        )
        return findings

    duration = int(program.get(duration_key, 0))
    cooldown = int(program.get("cooldown_days", 0))
    if duration != expected:
        findings.append(
            (
                f"{label} is class {program_class} and must last {expected} days, not {duration}",
                source,
                1,
            )
        )
    if duration > REUSABLE_PROGRAM_MAX_DURATION_DAYS:
        findings.append(
            (
                f"{label} is a reusable policy and must not impose a "
                f"{duration}-day active program",
                source,
                1,
            )
        )
    if cooldown > duration:
        findings.append(
            (
                f"{label} cooldown ({cooldown} days) must not outlast its "
                f"{duration}-day program",
                source,
                1,
            )
        )
    lockout = (
        duration + cooldown
        if lockout_model == "sequential"
        else max(duration, cooldown)
    )
    if lockout > REUSABLE_PROGRAM_MAX_LOCKOUT_DAYS:
        findings.append(
            (
                f"{label} locks the player out for {lockout} days; reusable "
                "policies must return within one year",
                source,
                1,
            )
        )
    if not str(program.get("cleanup_owner", "")):
        findings.append(
            (f"{label} must declare the effect that owns its cleanup", source, 1)
        )
    return findings


def _removes_active_decision(text: str, decision_id: str) -> bool:
    code = blank_quoted_strings(strip_comments(text))
    return bool(
        re.search(
            rf"(?m)^\s*remove_decision\s*=\s*{re.escape(decision_id)}\s*$",
            code,
        )
    )


@dataclass(frozen=True)
class Bound:
    minimum: Decimal
    maximum: Decimal


@dataclass(frozen=True)
class AuxiliaryLifecycleConfig:
    root: str
    tag: str
    reconstruction_effect: str
    scheduler_effect: str
    monthly_driver: str
    terminal_marker: str
    terminal_date: str
    expected_yearly_callers: Mapping[str, str]


@dataclass(frozen=True)
class IndependentSubsystemConfig:
    subsystem_id: str
    kind: str
    namespaces: Tuple[str, ...]
    event_ids: Tuple[str, ...]
    owner_tags: Tuple[str, ...]
    reconstruction_effects: Tuple[str, ...]
    scheduler_entrypoints: Tuple[str, ...]
    effect_roots: Tuple[str, ...]
    mode_policy: str


@dataclass(frozen=True)
class ModeTrace:
    owner: str
    file: str
    line: int
    host: str
    host_file: str
    block_path: Tuple[str, ...]


ModeGraphResult = Tuple[
    Dict[str, Set[str]],
    Dict[str, Set[str]],
    Dict[Tuple[str, str], List[ModeTrace]],
    Dict[Tuple[str, str], List[ModeTrace]],
]


@dataclass
class ChainConfig:
    name: str
    tag: str
    namespace: str
    root: str
    tier: int
    owned_prefixes: Tuple[str, ...]
    variables: Dict[str, Bound]
    outcome_idea_prefixes: Tuple[str, ...]
    requires_current_year_scheduler: bool
    allow_yearly_scheduler_duplicates: bool
    callerless_anchors: Set[str]
    allowed_multiple_callers: Set[str]
    allowed_reads: Tuple[str, ...]
    allowed_writes: Tuple[str, ...]
    full_start_strategies: Tuple[str, ...] = ()
    outcomes_only_strategy: str = ""
    declared_monthly_driver: str = ""
    terminal_marker: str = ""
    terminal_date: str = ""
    outcome_ideas: Tuple[str, ...] = ()
    expected_callers: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)
    dependency_order: Tuple[str, ...] = ()
    localisation_prefixes: Tuple[str, ...] = ()
    effect_preview_policy: str = "engine_or_explicit"
    tooltip_exemptions: Mapping[str, str] = field(default_factory=dict)
    bridge_refresh_policy: str = "none"
    ai_bankruptcy_exceptions: Tuple[str, ...] = ()
    auxiliary_completion_markers: Tuple[str, ...] = ()
    auxiliary_lifecycles: Tuple[AuxiliaryLifecycleConfig, ...] = ()
    allow_multiple_completion_producers: bool = False

    @property
    def completion_flag(self) -> str:
        return self.terminal_marker or f"{self.root}_reconstruct_complete"

    @property
    def reconstruct_effect(self) -> str:
        return f"{self.root}_reconstruct_history"

    @property
    def initialize_effect(self) -> str:
        return f"{self.root}_initialize_state"

    @property
    def clamp_effect(self) -> str:
        return f"{self.root}_clamp_state"

    @property
    def scheduler_effect(self) -> str:
        return f"{self.root}_schedule_current_year_events"

    @property
    def hidden_ninety_id(self) -> str:
        return f"{self.namespace}.90"

    @property
    def monthly_driver(self) -> str:
        return (
            self.declared_monthly_driver
            or f"{self.tag}_corporate_history_monthly_outcomes"
        )


@dataclass
class BlockDef:
    name: str
    file: str
    line: int
    body: str


@dataclass
class EventDef:
    event_id: str
    file: str
    line: int
    body: str
    hidden: bool
    options: List[BlockDef] = field(default_factory=list)
    immediates: List[BlockDef] = field(default_factory=list)


@dataclass
class IdeaDef:
    idea_id: str
    file: str
    line: int
    body: str


@dataclass
class CallSite:
    target: str
    file: str
    line: int
    kind: str
    owner: str

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.owner}"


__all__ = [name for name in globals() if not name.startswith("__")]
