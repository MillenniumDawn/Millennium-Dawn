"""Check TOP lifecycle wiring and inspect its opt-in HOI4 game.log markers.

Run ``wiring`` before launching the mod. In a new campaign, open the HOI4
console and enter ``effect TOP_enable_diagnostics = yes``. Let two
weekly pulses pass, then run ``log <game.log> --expect-mode limited`` (or
``full`` / ``off``). Log evidence proves the hooks executed in that campaign;
the static wiring check alone does not.

To check the shared operation slot, begin and finish one person operation and
one organization operation in the same fresh game session, then run
``operations <game.log>``. The trace is emitted only while diagnostics are on.
"""

from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from shared_utils import extract_block_from_text, strip_comments  # noqa: E402

PROBE_RE = re.compile(
    r"TOP_PROBE mode=(?P<mode>-?\d+(?:\.\d+)?) "
    r"clock=(?P<clock>-?\d+(?:\.\d+)?) "
    r"registry=(?P<registry>-?\d+(?:\.\d+)?) "
    r"country_ticks=(?P<country_ticks>-?\d+(?:\.\d+)?)"
)
SLOT_RE = re.compile(
    r"TOP_SLOT event=(?P<event>begin|end) actor=(?P<actor>[A-Z0-9_]+) "
    r"kind=(?P<kind>\d+(?:\.\d+)?) id=(?P<id>\d+(?:\.\d+)?) "
    r"seq=(?P<seq>\d+(?:\.\d+)?) clock=(?P<clock>\d+(?:\.\d+)?)"
)
MODES = {"off": 0, "limited": 1, "full": 2}


def named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", text)
    if match is None:
        raise ValueError(f"Missing block: {name}")
    body, end = extract_block_from_text(text, match.start())
    if end == -1:
        raise ValueError(f"Unbalanced block: {name}")
    return body


def check_wiring(root: Path) -> list[str]:
    """Return missing source links; this is not an engine execution test."""
    paths = {
        "startup": "common/on_actions/00_on_actions.txt",
        "weekly": "common/on_actions/MD_on_actions.txt",
        "ct": "common/scripted_effects/00_ct_effects.txt",
        "effects": "common/scripted_effects/00_targeted_operations_effects.txt",
        "game_rule": "common/game_rules/01_targeted_operations.txt",
        "registry": "common/scripted_effects/01_targeted_operations_registry.txt",
        "triggers": "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "case_triggers": "common/scripted_triggers/04_targeted_operations_cases.txt",
        "redesign_triggers": "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "person_cases": "common/scripted_effects/04_targeted_operations_cases.txt",
        "organization_cases": "common/scripted_effects/07_targeted_operations_organization_cases.txt",
    }
    try:
        source = {
            name: strip_comments((root / path).read_text(encoding="utf-8-sig"))
            for name, path in paths.items()
        }
    except OSError as error:
        return [f"Cannot read TOP wiring source: {error}"]
    failures = []

    def require(block: str, call: str, location: str) -> None:
        if re.search(rf"(?m)^\s*{re.escape(call)}\s*=\s*yes\s*$", block) is None:
            failures.append(f"{location} does not call {call}")

    def get_block(text: str, name: str) -> str:
        try:
            return named_block(text, name)
        except ValueError as error:
            failures.append(str(error))
            return ""

    require(
        get_block(source["startup"], "on_startup"), "TOP_cache_game_rule", "on_startup"
    )
    ct_global = named_block(source["ct"], "counter_terror_global_setup")
    require(ct_global, "TOP_initialize_global", "counter_terror_global_setup")
    require(ct_global, "create_staggered_cycle", "counter_terror_global_setup")
    require(
        get_block(source["ct"], "create_staggered_cycle"),
        "add_on_creation",
        "create_staggered_cycle",
    )
    require(
        get_block(source["ct"], "add_on_creation"),
        "counter_terror_nation_startup",
        "add_on_creation",
    )
    require(
        get_block(source["ct"], "counter_terror_nation_startup"),
        "TOP_country_initialize",
        "counter_terror_nation_startup",
    )
    require(
        get_block(source["ct"], "ct_staggered_country_tick"),
        "TOP_country_tick",
        "ct_staggered_country_tick",
    )
    weekly = named_block(source["weekly"], "on_weekly")
    country_buckets = len(
        re.findall(r"(?m)^\s*ct_staggered_country_tick\s*=\s*yes\s*$", weekly)
    )
    if country_buckets != 4:
        failures.append(
            f"on_weekly dispatches {country_buckets} CT country buckets; expected four"
        )
    guard = weekly.find("has_global_flag = on_weekly_global_done")
    if guard < 0:
        failures.append("on_weekly lacks the existing global once-per-week guard")
    else:
        guard_block, end = extract_block_from_text(
            weekly, weekly.rfind("if = {", 0, guard)
        )
        if end == -1:
            failures.append("on_weekly global guard is unbalanced")
        else:
            require(guard_block, "TOP_global_weekly", "on_weekly global guard")

    effects = source["effects"]
    game_rule = get_block(source["game_rule"], "TOP_game_rule")
    cache_rule = get_block(effects, "TOP_cache_game_rule")
    for option in (
        "TOP_limited_sandbox_option",
        "TOP_full_sandbox_option",
        "TOP_disabled_option",
    ):
        if re.search(rf"(?m)^\s*name\s*=\s*{option}\s*$", game_rule) is None:
            failures.append(f"TOP_game_rule lacks {option}")
    for option in ("TOP_limited_sandbox_option", "TOP_full_sandbox_option"):
        if (
            re.search(
                rf"has_game_rule\s*=\s*\{{\s*rule\s*=\s*TOP_game_rule\s+option\s*=\s*{option}\s*\}}",
                cache_rule,
            )
            is None
        ):
            failures.append(f"TOP_cache_game_rule does not read {option}")
    require(
        get_block(effects, "TOP_initialize_global"),
        "TOP_setup_registry",
        "TOP_initialize_global",
    )
    require(
        get_block(effects, "TOP_country_initialize"),
        "TOP_resize_country_arrays",
        "TOP_country_initialize",
    )
    if "set_global_flag = TOP_diagnostics_enabled" not in get_block(
        effects, "TOP_enable_diagnostics"
    ):
        failures.append("TOP_enable_diagnostics does not set the diagnostic flag")
    global_weekly = get_block(effects, "TOP_global_weekly")
    require(global_weekly, "TOP_cache_game_rule", "TOP_global_weekly")
    require(global_weekly, "TOP_initialize_global", "TOP_global_weekly")
    if "add_to_variable = { global.TOP_clock = 7 }" not in global_weekly:
        failures.append("TOP_global_weekly does not advance the clock by seven")
    if (
        "TOP_diagnostics_enabled" not in global_weekly
        or "TOP_PROBE mode=" not in global_weekly
    ):
        failures.append("TOP_global_weekly lacks the opt-in native probe log")
    country_tick = get_block(effects, "TOP_country_tick")
    require(country_tick, "TOP_country_initialize", "TOP_country_tick")
    if (
        "TOP_diagnostics_enabled" not in country_tick
        or "global.TOP_diag_country_ticks = 1" not in country_tick
    ):
        failures.append("TOP_country_tick lacks the opt-in diagnostic counter")
    if (
        "check_variable = { TOP_known^num = global.TOP_registry_capacity }"
        not in country_tick
    ):
        failures.append("TOP_country_tick counts countries without initialized storage")
    get_block(source["registry"], "TOP_setup_registry")
    resize = get_block(source["registry"], "TOP_resize_country_arrays")
    capacity = re.search(
        r"global\.TOP_registry_capacity\s*=\s*(\d+)", source["registry"]
    )
    if capacity is None:
        failures.append("TOP registry lacks a numeric capacity")
    elif (
        re.search(
            rf"resize_array\s*=\s*\{{\s*TOP_known\s*=\s*{capacity.group(1)}\s*\}}",
            resize,
        )
        is None
    ):
        failures.append(
            "TOP_resize_country_arrays does not resize TOP_known to capacity"
        )
    if "has_game_rule" in source["triggers"]:
        failures.append(
            "TOP scripted triggers evaluate has_game_rule before a game exists"
        )
    if "is_ai = no" not in get_block(source["triggers"], "TOP_human_offense"):
        failures.append("TOP_human_offense lacks the player-only gate")
    slot = get_block(source["case_triggers"], "TOP_operation_slot_available")
    if "check_variable = { TOP_operation_subject_kind = 0 }" not in slot:
        failures.append("TOP_operation_slot_available does not require an empty slot")
    slot_uses = sum(
        len(re.findall(r"(?m)^\s*TOP_operation_slot_available\s*=\s*yes\s*$", text))
        for text in (source["case_triggers"], source["redesign_triggers"])
    )
    if slot_uses < 2:
        failures.append(
            "Person and organization operations do not share the single slot gate"
        )
    for name in ("TOP_trace_slot_begin", "TOP_trace_slot_end"):
        if "TOP_diagnostics_enabled" not in get_block(source["effects"], name):
            failures.append(f"{name} is not diagnostic-only")
    for source_name, label, ends in (
        ("person_cases", "person", 3),
        ("organization_cases", "organization", 3),
    ):
        text = source[source_name]
        if text.count("TOP_trace_slot_begin = yes") != 1:
            failures.append(f"{label} operation begin lacks one slot trace")
        if text.count("TOP_trace_slot_end = yes") != ends:
            failures.append(f"{label} operation releases lack {ends} slot traces")
    return failures


def parse_probes(log: str) -> list[dict[str, Decimal]]:
    probes = []
    for match in PROBE_RE.finditer(log):
        probes.append(
            {name: Decimal(value) for name, value in match.groupdict().items()}
        )
    return probes


def check_probes(
    probes: list[dict[str, Decimal]], mode: str, capacity: int, min_samples: int = 2
) -> list[str]:
    failures = []
    if min_samples < 2:
        return ["TOP_PROBE requires at least two samples"]
    if len(probes) < min_samples:
        return [f"Found {len(probes)} TOP_PROBE samples; need {min_samples}"]
    expected_mode = MODES[mode]
    for number, probe in enumerate(probes, 1):
        for name, value in probe.items():
            if Decimal(str(value)) != Decimal(str(value)).to_integral_value():
                failures.append(f"Sample {number}: non-integral {name} {value}")
        if probe["mode"] != expected_mode:
            failures.append(f"Sample {number}: mode {probe['mode']} != {expected_mode}")
        expected_capacity = 0 if mode == "off" else capacity
        if probe["registry"] != expected_capacity:
            failures.append(
                f"Sample {number}: registry {probe['registry']} != {expected_capacity}"
            )
        if mode == "off" and (probe["clock"] != 0 or probe["country_ticks"] != 0):
            failures.append(f"Sample {number}: Off mode advanced TOP state")
    if mode != "off":
        for number, probe in enumerate(probes, 1):
            if probe["clock"] <= 0 or probe["clock"] % 7:
                failures.append(
                    f"Sample {number}: clock {probe['clock']:g} is not a positive multiple of seven"
                )
        for previous, current in zip(probes, probes[1:]):
            if current["clock"] - previous["clock"] != 7:
                failures.append("TOP clock did not advance by seven between samples")
        for number, probe in enumerate(probes[1:], 2):
            if probe["country_ticks"] <= 0:
                failures.append(f"Sample {number}: no staggered country tick")
    return failures


def parse_slot_events(log: str) -> list[dict[str, str | Decimal]]:
    events = []
    for match in SLOT_RE.finditer(log):
        values = match.groupdict()
        events.append(
            {
                "event": values["event"],
                "actor": values["actor"],
                **{
                    name: Decimal(values[name])
                    for name in ("kind", "id", "seq", "clock")
                },
            }
        )
    return events


def check_slot_events(events: list[dict[str, str | Decimal]]) -> list[str]:
    failures = []
    active: dict[str, tuple[int, int, int]] = {}
    completed = {1: 0, 2: 0}
    for number, event in enumerate(events, 1):
        actor = str(event["actor"])
        if any(
            Decimal(str(event[name])) != Decimal(str(event[name])).to_integral_value()
            for name in ("kind", "id", "seq", "clock")
        ):
            failures.append(f"Trace {number}: non-integral slot value for {actor}")
            continue
        slot = (int(event["kind"]), int(event["id"]), int(event["seq"]))
        if slot[0] not in completed or slot[1] <= 0 or slot[2] <= 0:
            failures.append(f"Trace {number}: invalid slot {slot} for {actor}")
            continue
        if event["event"] == "begin":
            if actor in active:
                failures.append(
                    f"Trace {number}: {actor} began {slot} while {active[actor]} was active"
                )
            else:
                active[actor] = slot
        elif actor not in active:
            failures.append(f"Trace {number}: {actor} ended {slot} without a begin")
        elif active[actor] != slot:
            failures.append(
                f"Trace {number}: {actor} ended {slot} instead of {active[actor]}"
            )
        else:
            completed[slot[0]] += 1
            del active[actor]
    for actor, slot in active.items():
        failures.append(f"{actor} still holds slot {slot}")
    for kind, label in ((1, "person"), (2, "organization")):
        if completed[kind] == 0:
            failures.append(f"No completed {label} operation in TOP_SLOT trace")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="mod checkout to inspect"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("wiring", help="check static hook reachability")
    log_parser = subparsers.add_parser(
        "log", help="check opt-in native game.log markers"
    )
    log_parser.add_argument("game_log", type=Path)
    log_parser.add_argument("--expect-mode", choices=MODES, required=True)
    log_parser.add_argument("--min-samples", type=int, default=2)
    operations_parser = subparsers.add_parser(
        "operations", help="check native person and organization slot transitions"
    )
    operations_parser.add_argument("game_log", type=Path)
    args = parser.parse_args(argv)
    if args.command == "log" and args.min_samples < 2:
        parser.error("--min-samples must be at least 2")

    if args.command == "wiring":
        failures = check_wiring(args.root)
        label = "static TOP lifecycle wiring"
    elif args.command == "log":
        registry = (
            args.root / "common/scripted_effects/01_targeted_operations_registry.txt"
        ).read_text(encoding="utf-8")
        match = re.search(r"global\.TOP_registry_capacity\s*=\s*(\d+)", registry)
        if match is None:
            parser.error("generated registry lacks TOP_registry_capacity")
        probes = parse_probes(args.game_log.read_text(encoding="utf-8-sig"))
        failures = check_probes(
            probes, args.expect_mode, int(match.group(1)), args.min_samples
        )
        label = f"{len(probes)} native TOP_PROBE samples in {args.expect_mode} mode"
    else:
        events = parse_slot_events(args.game_log.read_text(encoding="utf-8-sig"))
        failures = check_slot_events(events)
        label = f"{len(events)} native TOP_SLOT transitions"
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"PASS: {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
