"""Coverage tests for the parallel content-validation dispatcher.

The dispatcher (`tools/precommit_validate.py`) replaces ~20 individual
`md-validate-*` pre-commit hooks. The risk of that consolidation is *coverage*:
if a registry rule drifts from the validator's old `files:` regex, a validator
could silently stop running on some paths. These tests pin which validators a
given staged path selects, so an unintended coverage change fails CI.
"""

import subprocess
import sys

import precommit_validate as dispatcher
import pytest
from precommit_validate import _REGISTRY
from shared.suite import initialize_git_repository, run_git

_BY_SCRIPT = {spec.script: spec for spec in _REGISTRY}


def _run_dispatcher_with_stubbed_runner(monkeypatch, argv):
    """Stub the dispatcher's subprocess runner and argv; return recorded calls."""
    calls = []

    def run(spec, _mod_path, env, _no_color, _inner_workers):
        calls.append((spec.script, env["MD_STAGED_FILES"]))
        return (spec.script, 0, "", "", 0.0)

    monkeypatch.setattr(dispatcher, "_run", run)
    monkeypatch.setattr(sys, "argv", argv)
    return calls


def _selected(path):
    """Set of validator scripts the dispatcher runs for a single staged path."""
    return {spec.script for spec in _REGISTRY if spec.matches([path])}


# path -> the exact set of commit-stage validators the dispatcher selects.
# Only run-on-commit validators are folded in; the expensive cross-reference
# ones (cosmetic_tags, variables, focus_tree, decisions, modifiers,
# scripted_params, simplifications, localisation, factions, history_techs, ...)
# are stages:[manual] in the config and intentionally absent here.
_GOLDEN = {
    "common/national_focus/france.txt": {
        "validate_agency_upgrades",
        "validate_style",
        "validate_ideas",
        "validate_events",
        "validate_oob_units",
        "validate_characters",
    },
    "common/idea_tags/00_idea.txt": {
        "validate_style",
        "validate_ideas",
        "validate_events",
    },
    "events/Syria.txt": {
        "validate_agency_upgrades",
        "validate_style",
        "validate_ideas",
        "validate_events",
        "validate_oob_units",
        "validate_characters",
    },
    "common/decisions/Sudan.txt": {
        "validate_agency_upgrades",
        "validate_style",
        "validate_ideas",
        "validate_events",
        "validate_oob_units",
        "validate_characters",
    },
    "common/on_actions/00_on_actions.txt": {
        "validate_style",
        "validate_ideas",
        "validate_oob_units",
        "validate_events",
        "validate_characters",
    },
    "common/operations/00_operations.txt": {
        "validate_style",
        "validate_events",
        "validate_oob_units",
    },
    "common/resistance_compliance_modifiers/resistance_modifiers.txt": {
        "validate_style",
        "validate_events",
        "validate_oob_units",
    },
    "common/scripted_guis/00_missiles_scripted_guis.txt": {
        "validate_style",
        "validate_events",
        "validate_oob_units",
    },
    "common/scripted_triggers/00_triggers.txt": {
        "validate_style",
        "validate_ideas",
        "validate_events",
    },
    "common/scripted_effects/00_x.txt": {
        "validate_agency_upgrades",
        "validate_style",
        "validate_oob_units",
        "validate_ideas",
        "validate_events",
        "validate_characters",
    },
    "common/units/MD_land_units.txt": {
        "validate_style",
        "validate_oob_units",
        "validate_ai_navy",
        "validate_events",
    },
    "common/ai_templates/x.txt": {
        "validate_style",
        "validate_oob_units",
        "validate_ai_roles",
        "validate_events",
    },
    "common/ai_strategy/CAN.txt": {
        "validate_style",
        "validate_ai_roles",
        "validate_events",
    },
    "common/ai_navy/x.txt": {
        "validate_style",
        "validate_ai_navy",
        "validate_events",
    },
    "common/ai_equipment/x.txt": {
        "validate_style",
        "validate_ai_equipment",
        "validate_events",
    },
    "common/intelligence_agency_upgrades/x.txt": {
        "validate_style",
        "validate_agency_upgrades",
        "validate_events",
    },
    "localisation/english/MD_focus_SER_l_english.yml": {
        "validate_ideas",
        "validate_mios",
    },
    "common/factions/x.txt": {"validate_style", "validate_events"},
    "common/military_industrial_organization/organizations/MD_ISR_organizations.txt": {
        "validate_style",
        "validate_mios",
        "validate_events",
    },
    "common/military_industrial_organization/policies/_land_policies.txt": {
        "validate_style",
        "validate_mios",
        "validate_events",
    },
    "common/units/equipment/MD_anti_air.txt": {
        "validate_style",
        "validate_mios",
        "validate_events",
        "validate_ai_navy",
        "validate_oob_units",
    },
    "common/equipment_groups/mio_equipment_groups.txt": {
        "validate_style",
        "validate_mios",
        "validate_events",
    },
    "history/countries/x.txt": {
        "validate_agency_upgrades",
        "validate_style",
        "validate_ideas",
        "validate_oob_units",
        "validate_events",
        "validate_characters",
    },
}


def test_golden_selection():
    for path, expected in _GOLDEN.items():
        expected = set(expected)
        if path.endswith(".txt") and not any(
            token in path for token in ("Changelog.txt", "AUTHORS.txt", "/descriptions")
        ):
            expected.add("validate_common_mistakes")
        assert _selected(path) == expected, path


def test_style_excludes_changelog_and_authors():
    # Old md-validate-style hook excluded these; the run-gate must match.
    assert "validate_style" not in _selected("Changelog.txt")
    assert "validate_style" not in _selected("AUTHORS.txt")
    assert "validate_style" not in _selected("common/units/descriptions_units.txt")


def test_style_runs_on_normal_txt():
    assert "validate_style" in _selected("common/national_focus/france.txt")


def test_interface_sprite_changes_run_reference_validation():
    assert _selected("interface/mio_icons.gfx") == {
        "validate_agency_upgrades",
        "validate_mios",
    }


def test_dispatcher_keeps_gfx_through_main_filter(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "test@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")
    target = tmp_path / "interface" / "mio_icons.gfx"
    target.parent.mkdir(parents=True)
    target.write_text("spriteTypes = {\n}\n", encoding="utf-8")
    run_git(tmp_path, "add", "-A")

    calls = _run_dispatcher_with_stubbed_runner(
        monkeypatch, ["precommit_validate.py", "--path", str(tmp_path)]
    )

    assert dispatcher.main() == 0
    mio_calls = [env for script, env in calls if script == "validate_mios"]
    assert mio_calls == ["interface/mio_icons.gfx"]


def test_agency_upgrades_routes_definitions_and_call_sources():
    spec = _BY_SCRIPT["validate_agency_upgrades"]
    assert spec.matches(["common/intelligence_agency_upgrades/x.txt"])
    assert spec.matches(["common/national_focus/x.txt"])
    assert spec.matches(["common/decisions/x.txt"])
    assert spec.matches(["common/factions/goals/x.txt"])
    assert spec.matches(["common/scripted_effects/x.txt"])
    assert spec.matches(["events/x.txt"])
    assert spec.matches(["history/countries/x.txt"])
    assert spec.matches(["interface/x.gfx"])
    assert not spec.matches(["common/on_actions/00_on_actions.txt"])
    assert not spec.matches(["localisation/english/x_l_english.yml"])


def test_ai_equipment_is_warning_only():
    # Mirrors the hook: validate_ai_equipment runs without --strict.
    assert not _BY_SCRIPT["validate_ai_equipment"].strict


def test_strict_validators_are_strict():
    for script in ("validate_events", "validate_ideas", "validate_oob_units"):
        assert _BY_SCRIPT[script].strict


def test_manual_validators_not_folded():
    # These are stages:[manual] in the config and must stay out of the
    # commit-stage dispatcher, or they would run on every commit.
    folded = set(_BY_SCRIPT)
    for script in (
        "validate_cosmetic_tags",
        "validate_localisation",
        "validate_focus_tree",
        "validate_variables",
        "validate_decisions",
        "validate_modifiers",
        "validate_scripted_params",
        "validate_simplifications",
    ):
        assert script not in folded


@pytest.mark.parametrize(
    ("strict", "no_color", "flags"),
    [(True, True, ["--strict", "--no-color"]), (False, False, [])],
)
def test_dispatcher_subprocess_contract(monkeypatch, tmp_path, strict, no_color, flags):
    spec = dispatcher._Spec("validate_stub", [("events/", ".txt")], strict=strict)
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return type(
            "Result",
            (),
            {"returncode": 1, "stdout": "finding", "stderr": ""},
        )()

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)
    env = {"MD_STAGED_FILES": "events/test.txt"}
    result = dispatcher._run(spec, str(tmp_path), env, no_color, 3)

    assert captured["command"][2:] == ["--staged", "--workers", "3", *flags]
    assert captured["env"] is env
    assert captured["timeout"] == 300
    assert result[:4] == ("validate_stub", 1, "finding", "")


@pytest.mark.parametrize(
    ("captured", "stdout", "stderr"),
    [
        pytest.param(
            {"output": b"out", "stderr": b"err"}, "out", "err", id="bytes are decoded"
        ),
        pytest.param({}, "", "", id="nothing captured"),
    ],
)
def test_a_validator_that_times_out_exits_124(
    tmp_path, monkeypatch, captured, stdout, stderr
):
    def timed_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("validator", 300, **captured)

    monkeypatch.setattr(dispatcher.subprocess, "run", timed_out)
    spec = dispatcher._Spec("validate_stub", [("events/", ".txt")])

    result = dispatcher._run(spec, str(tmp_path), {}, True, 1)

    assert result[:4] == (
        "validate_stub",
        124,
        stdout,
        f"{stderr}\nvalidate_stub: TIMED OUT after 300s",
    )


@pytest.mark.parametrize(
    ("skip", "staged", "message"),
    [
        pytest.param("1", ["events/x.txt"], "skipping", id="MD_SKIP_VALIDATE is set"),
        pytest.param(None, [], "nothing to validate", id="nothing staged"),
        pytest.param(
            None,
            ["Changelog.txt"],
            "No content validators match",
            id="no validator takes the file",
        ),
    ],
)
def test_dispatcher_exits_clean_without_running_a_validator(
    monkeypatch, capsys, skip, staged, message
):
    monkeypatch.delenv("MD_SKIP_VALIDATE", raising=False)
    if skip:
        monkeypatch.setenv("MD_SKIP_VALIDATE", skip)
    monkeypatch.setattr(dispatcher, "_discover_staged", lambda *_args: staged)
    calls = _run_dispatcher_with_stubbed_runner(monkeypatch, ["precommit_validate.py"])

    assert dispatcher.main() == 0
    assert calls == []
    assert message in capsys.readouterr().out


def test_a_failing_validator_blocks_the_commit_and_shows_its_output(
    monkeypatch, capsys
):
    monkeypatch.delenv("MD_SKIP_VALIDATE", raising=False)
    spec = dispatcher._Spec("validate_stub", [("events/", ".txt")])
    monkeypatch.setattr(dispatcher, "_REGISTRY", [spec])
    monkeypatch.setattr(dispatcher, "_discover_staged", lambda *_args: ["events/x.txt"])
    monkeypatch.setattr(
        dispatcher,
        "_run",
        lambda *_args: ("validate_stub", 1, "stdout text", "stderr text", 0.1),
    )
    monkeypatch.setattr(sys, "argv", ["precommit_validate.py"])

    assert dispatcher.main() == 1
    output = capsys.readouterr().out
    assert "stdout text" in output and "stderr text" in output
    assert "[FAIL] validate_stub" in output
    assert "1 validator(s) failed" in output


def test_precommit_dispatcher_routes_history_general_templates():
    assert "validate_oob_units" in {
        spec.script
        for spec in _REGISTRY
        if spec.matches(["history/general/template.txt"])
    }


def test_precommit_dispatcher_selects_oob_for_a_moved_history_target(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    target = tmp_path / "history" / "units" / "target.txt"
    target.parent.mkdir(parents=True)
    with target.open("w", encoding="utf-8", newline="") as output_file:
        output_file.write("units = { }\n")

    initialize_git_repository(tmp_path, "history/units")
    target.rename(tmp_path / "target.txt")
    run_git(tmp_path, "add", "-A")

    destination = str(tmp_path / "target.txt")
    paths = dispatcher._discover_staged(str(tmp_path), [destination])

    assert "history/units/target.txt" in paths
    assert "validate_oob_units" in {
        spec.script for spec in _REGISTRY if spec.matches(paths)
    }

    calls = _run_dispatcher_with_stubbed_runner(
        monkeypatch,
        ["precommit_validate.py", "--path", str(tmp_path), destination],
    )

    dispatcher.main()

    oob_calls = [env for script, env in calls if script == "validate_oob_units"]
    assert oob_calls == ["target.txt\nhistory/units/target.txt"]


def test_dispatcher_takes_passed_files_and_staged_deletions(tmp_path, monkeypatch):
    # A merge commit stages main's files but passes only the conflicted ones.
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    events = tmp_path / "events"
    events.mkdir()
    for name in ("passed", "unpassed", "deleted"):
        (events / f"{name}.txt").write_text("a = 1\n", encoding="utf-8")
    initialize_git_repository(tmp_path, "events")
    for name in ("passed", "unpassed"):
        (events / f"{name}.txt").write_text("a = 2\n", encoding="utf-8")
    (events / "deleted.txt").unlink()
    run_git(tmp_path, "add", "-A")

    paths = dispatcher._discover_staged(str(tmp_path), [str(events / "passed.txt")])

    assert paths == ["events/passed.txt", "events/deleted.txt"]


def test_no_match_outside_scope():
    # A .lua define, a gui file, a texture — none are owned by this dispatcher.
    assert _selected("common/defines/00_defines.lua") == set()
    assert _selected("interface/x.gui") == set()
    assert _selected("gfx/x.dds") == set()
