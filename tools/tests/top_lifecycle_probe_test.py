"""Focused checks for TOP source wiring and native log probe evaluation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import top_lifecycle_probe

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    "common/on_actions/00_on_actions.txt",
    "common/on_actions/MD_on_actions.txt",
    "common/scripted_effects/00_ct_effects.txt",
    "common/scripted_effects/00_targeted_operations_effects.txt",
    "common/game_rules/01_targeted_operations.txt",
    "common/scripted_effects/01_targeted_operations_registry.txt",
    "common/scripted_triggers/01_targeted_operations_triggers.txt",
    "common/scripted_triggers/04_targeted_operations_cases.txt",
    "common/scripted_triggers/07_targeted_operations_redesign.txt",
    "common/scripted_effects/04_targeted_operations_cases.txt",
    "common/scripted_effects/07_targeted_operations_organization_cases.txt",
)


def copy_sources(root):
    for relative in SOURCE_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())


def test_current_system_wiring_is_reachable():
    assert top_lifecycle_probe.check_wiring(ROOT) == []


def test_wiring_detects_removed_country_tick(tmp_path):
    copy_sources(tmp_path)
    ct_effects = tmp_path / "common/scripted_effects/00_ct_effects.txt"
    ct_effects.write_bytes(
        ct_effects.read_bytes().replace(b"TOP_country_tick = yes", b"always = yes")
    )
    weekly = tmp_path / "common/on_actions/MD_on_actions.txt"
    weekly.write_bytes(
        weekly.read_bytes().replace(b"ct_staggered_country_tick = yes", b"always = yes")
    )
    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "ct_staggered_country_tick does not call TOP_country_tick" in failures
    assert "on_weekly dispatches 0 CT country buckets; expected four" in failures


def test_wiring_requires_human_only_offense_and_shared_single_slot(tmp_path):
    copy_sources(tmp_path)
    triggers = tmp_path / "common/scripted_triggers/01_targeted_operations_triggers.txt"
    triggers.write_bytes(triggers.read_bytes().replace(b"\tis_ai = no", b"", 1))
    cases = tmp_path / "common/scripted_triggers/04_targeted_operations_cases.txt"
    cases.write_bytes(
        cases.read_bytes().replace(
            b"TOP_operation_subject_kind = 0", b"TOP_operation_subject_kind = 1"
        )
    )
    redesign = tmp_path / "common/scripted_triggers/07_targeted_operations_redesign.txt"
    redesign.write_bytes(
        redesign.read_bytes().replace(
            b"TOP_operation_slot_available = yes", b"always = yes"
        )
    )

    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "TOP_human_offense lacks the player-only gate" in failures
    assert "TOP_operation_slot_available does not require an empty slot" in failures
    assert (
        "Person and organization operations do not share the single slot gate"
        in failures
    )


def test_limited_mode_requires_weekly_country_ticks():
    probes = top_lifecycle_probe.parse_probes(
        "[2000.1.8] TOP_PROBE mode=1 clock=7 registry=161 country_ticks=0\n"
        "[2000.1.15] TOP_PROBE mode=1 clock=14 registry=161 country_ticks=32\n"
    )
    assert top_lifecycle_probe.check_probes(probes, "limited", 161) == []


def test_off_mode_stays_inert():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=0 clock=0 registry=0 country_ticks=0\n" * 2
    )
    assert top_lifecycle_probe.check_probes(probes, "off", 161) == []
    probes[1]["clock"] = 7
    assert "Sample 2: Off mode advanced TOP state" in top_lifecycle_probe.check_probes(
        probes, "off", 161
    )


def test_probe_rejects_duplicate_weekly_dispatch_and_missing_country_tick():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=2 clock=7 registry=161 country_ticks=0\n"
        "TOP_PROBE mode=2 clock=7 registry=161 country_ticks=0\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "full", 161)
    assert "TOP clock did not advance by seven between samples" in failures
    assert "Sample 2: no staggered country tick" in failures


def test_probe_requires_enough_native_samples():
    assert top_lifecycle_probe.check_probes([], "limited", 161) == [
        "Found 0 TOP_PROBE samples; need 2"
    ]
    assert top_lifecycle_probe.check_probes([], "off", 161, min_samples=0) == [
        "TOP_PROBE requires at least two samples"
    ]


def test_enabled_probe_clocks_start_on_the_seven_day_phase():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=1 clock=1 registry=161 country_ticks=1\n"
        "TOP_PROBE mode=1 clock=8 registry=161 country_ticks=1\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "limited", 161)
    assert "Sample 1: clock 1 is not a positive multiple of seven" in failures
    assert "Sample 2: clock 8 is not a positive multiple of seven" in failures


def test_slot_trace_accepts_completed_person_and_organization_operations():
    events = top_lifecycle_probe.parse_slot_events(
        "TOP_SLOT event=begin actor=USA kind=1 id=12 seq=3 clock=14\n"
        "TOP_SLOT event=begin actor=FRA kind=2 id=7 seq=1 clock=14\n"
        "TOP_SLOT event=end actor=USA kind=1 id=12 seq=3 clock=42\n"
        "TOP_SLOT event=end actor=FRA kind=2 id=7 seq=1 clock=42\n"
    )
    assert top_lifecycle_probe.check_slot_events(events) == []


def test_slot_trace_rejects_overlap_and_mismatched_release():
    events = top_lifecycle_probe.parse_slot_events(
        "TOP_SLOT event=begin actor=USA kind=1 id=12 seq=3 clock=14\n"
        "TOP_SLOT event=begin actor=USA kind=2 id=7 seq=1 clock=14\n"
        "TOP_SLOT event=end actor=USA kind=1 id=12 seq=4 clock=42\n"
    )
    failures = top_lifecycle_probe.check_slot_events(events)
    assert "Trace 2: USA began (2, 7, 1) while (1, 12, 3) was active" in failures
    assert "Trace 3: USA ended (1, 12, 4) instead of (1, 12, 3)" in failures
    assert "USA still holds slot (1, 12, 3)" in failures


def test_wiring_detects_missing_organization_slot_trace(tmp_path):
    copy_sources(tmp_path)
    cases = (
        tmp_path
        / "common/scripted_effects/07_targeted_operations_organization_cases.txt"
    )
    cases.write_bytes(cases.read_bytes().replace(b"TOP_trace_slot_begin = yes", b""))
    assert (
        "organization operation begin lacks one slot trace"
        in top_lifecycle_probe.check_wiring(tmp_path)
    )


def test_wiring_requires_a_console_diagnostics_setter(tmp_path):
    copy_sources(tmp_path)
    effects = tmp_path / "common/scripted_effects/00_targeted_operations_effects.txt"
    effects.write_bytes(
        effects.read_bytes().replace(
            b"set_global_flag = TOP_diagnostics_enabled", b"always = yes"
        )
    )
    assert (
        "TOP_enable_diagnostics does not set the diagnostic flag"
        in top_lifecycle_probe.check_wiring(tmp_path)
    )


def test_wiring_reports_unreadable_source(tmp_path):
    assert (
        "Cannot read TOP wiring source" in top_lifecycle_probe.check_wiring(tmp_path)[0]
    )


def test_named_block_reports_missing_or_unbalanced_blocks():
    with pytest.raises(ValueError, match="Missing block: TOP_missing"):
        top_lifecycle_probe.named_block("", "TOP_missing")
    with pytest.raises(ValueError, match="Unbalanced block: TOP_missing"):
        top_lifecycle_probe.named_block("TOP_missing = {", "TOP_missing")


def test_probe_rejects_wrong_mode_and_registry_capacity():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=2 clock=7 registry=160 country_ticks=0\n"
        "TOP_PROBE mode=2 clock=14 registry=160 country_ticks=1\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "limited", 161)
    assert "Sample 1: mode 2 != 1" in failures
    assert "Sample 1: registry 160 != 161" in failures


def test_slot_trace_rejects_invalid_and_orphaned_transitions():
    events = top_lifecycle_probe.parse_slot_events(
        "TOP_SLOT event=begin actor=USA kind=0 id=0 seq=0 clock=7\n"
        "TOP_SLOT event=end actor=USA kind=1 id=12 seq=3 clock=14\n"
    )
    failures = top_lifecycle_probe.check_slot_events(events)
    assert "Trace 1: invalid slot (0, 0, 0) for USA" in failures
    assert "Trace 2: USA ended (1, 12, 3) without a begin" in failures


def test_cli_reads_generated_capacity_and_reports_off_mode(tmp_path, capsys):
    log = tmp_path / "game.log"
    log.write_text(
        "TOP_PROBE mode=0 clock=0 registry=0 country_ticks=0\n" * 2,
        encoding="utf-8",
    )
    assert (
        top_lifecycle_probe.main(
            ["--root", str(ROOT), "log", str(log), "--expect-mode", "off"]
        )
        == 0
    )
    assert "PASS: 2 native TOP_PROBE samples in off mode" in capsys.readouterr().out


def test_cli_rejects_fewer_than_two_required_samples(tmp_path):
    log = tmp_path / "game.log"
    log.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="2"):
        top_lifecycle_probe.main(
            ["log", str(log), "--expect-mode", "off", "--min-samples", "0"]
        )


def test_off_rule_preserves_achievements():
    rules = (ROOT / "common/game_rules/01_targeted_operations.txt").read_text(
        encoding="utf-8"
    )
    off = rules[rules.index("name = TOP_disabled_option") :]
    assert "allow_achievements = yes" in off[: off.index("}")]


def test_cli_reports_slot_trace_failures(tmp_path, capsys):
    log = tmp_path / "game.log"
    log.write_text("", encoding="utf-8")
    assert top_lifecycle_probe.main(["operations", str(log)]) == 1
    assert "No completed person operation" in capsys.readouterr().out


def test_cli_rejects_registry_without_capacity(tmp_path):
    registry = tmp_path / "common/scripted_effects/01_targeted_operations_registry.txt"
    registry.parent.mkdir(parents=True)
    registry.write_text("TOP_setup_registry = {}\n", encoding="utf-8")
    log = tmp_path / "game.log"
    log.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="2"):
        top_lifecycle_probe.main(
            ["--root", str(tmp_path), "log", str(log), "--expect-mode", "off"]
        )


def test_wiring_ignores_commented_diagnostic_and_clock_effects(tmp_path):
    copy_sources(tmp_path)
    effects = tmp_path / "common/scripted_effects/00_targeted_operations_effects.txt"
    effects.write_bytes(
        effects.read_bytes()
        .replace(
            b"set_global_flag = TOP_diagnostics_enabled",
            b"# set_global_flag = TOP_diagnostics_enabled",
        )
        .replace(
            b"add_to_variable = { global.TOP_clock = 7 }",
            b"# add_to_variable = { global.TOP_clock = 7 }",
        )
    )
    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "TOP_enable_diagnostics does not set the diagnostic flag" in failures
    assert "TOP_global_weekly does not advance the clock by seven" in failures


def test_wiring_requires_game_rule_and_exact_option_ids(tmp_path):
    copy_sources(tmp_path)
    rule = tmp_path / "common/game_rules/01_targeted_operations.txt"
    rule.write_bytes(
        rule.read_bytes().replace(
            b"name = TOP_full_sandbox_option", b"name = TOP_renamed_full_option"
        )
    )
    assert (
        "TOP_game_rule lacks TOP_full_sandbox_option"
        in top_lifecycle_probe.check_wiring(tmp_path)
    )
    rule.unlink()
    assert (
        "Cannot read TOP wiring source" in top_lifecycle_probe.check_wiring(tmp_path)[0]
    )


def test_wiring_requires_country_storage_and_checked_tick_counter(tmp_path):
    copy_sources(tmp_path)
    registry = tmp_path / "common/scripted_effects/01_targeted_operations_registry.txt"
    registry.write_bytes(
        registry.read_bytes().replace(
            b"resize_array = { TOP_known = 161 }",
            b"# resize_array = { TOP_known = 161 }",
        )
    )
    effects = tmp_path / "common/scripted_effects/00_targeted_operations_effects.txt"
    effects.write_bytes(
        effects.read_bytes().replace(
            b"check_variable = { TOP_known^num = global.TOP_registry_capacity }",
            b"always = yes",
        )
    )
    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "TOP_resize_country_arrays does not resize TOP_known to capacity" in failures
    assert "TOP_country_tick counts countries without initialized storage" in failures


def test_probe_rejects_each_missing_weekly_country_tick():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=1 clock=7 registry=161 country_ticks=0\n"
        "TOP_PROBE mode=1 clock=14 registry=161 country_ticks=32\n"
        "TOP_PROBE mode=1 clock=21 registry=161 country_ticks=0\n"
    )
    assert "Sample 3: no staggered country tick" in top_lifecycle_probe.check_probes(
        probes, "limited", 161
    )


def test_probe_rejects_fractional_lifecycle_values():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=1.5 clock=7.5 registry=161.5 country_ticks=0\n"
        "TOP_PROBE mode=1.5 clock=14.5 registry=161.5 country_ticks=3.5\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "limited", 161)
    for field in ("mode", "clock", "registry"):
        assert f"Sample 1: non-integral {field}" in "\n".join(failures)
    assert "Sample 2: non-integral country_ticks 3.5" in failures


def test_slot_trace_rejects_fractional_values():
    events = top_lifecycle_probe.parse_slot_events(
        "TOP_SLOT event=begin actor=USA kind=1.5 id=12 seq=3 clock=14\n"
    )
    assert (
        "Trace 1: non-integral slot value for USA"
        in top_lifecycle_probe.check_slot_events(events)
    )
