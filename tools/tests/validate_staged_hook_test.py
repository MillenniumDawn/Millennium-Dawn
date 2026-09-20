"""Behavior tests for the pre-commit staged-file validator dispatcher."""

import subprocess
from types import SimpleNamespace

import pytest
import validate_staged as staged


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch):
    monkeypatch.delenv("MD_SKIP_VALIDATE", raising=False)
    monkeypatch.setenv("MD_TIMING", "0")
    monkeypatch.setenv("MD_STAGED_FILES", "")


def stub_runs(monkeypatch, returncodes=None):
    """Record every validator invocation and hand back canned return codes."""
    calls = []
    codes = dict(returncodes or {})

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        script = cmd[1].rsplit("/", 1)[-1]
        return SimpleNamespace(returncode=codes.get(script, 0))

    monkeypatch.setattr(staged.subprocess, "run", fake_run)
    return calls


def scripts(calls):
    return [cmd[1].rsplit("/", 1)[-1] for cmd, _ in calls]


def test_get_staged_files_splits_the_git_listing(monkeypatch):
    recorded = {}

    def fake_run(cmd, **kwargs):
        recorded["cmd"] = cmd
        return SimpleNamespace(stdout="events/a.txt\ncommon/b.txt\n")

    monkeypatch.setattr(staged.subprocess, "run", fake_run)

    assert staged.get_staged_files() == ["events/a.txt", "common/b.txt"]
    assert recorded["cmd"][:4] == ["git", "diff", "--cached", "--name-only"]


def test_get_staged_files_is_empty_for_a_clean_index(monkeypatch):
    monkeypatch.setattr(
        staged.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout="\n  \n")
    )

    assert staged.get_staged_files() == []


def test_opt_out_env_skips_every_validator(monkeypatch):
    monkeypatch.setenv("MD_SKIP_VALIDATE", "1")
    calls = stub_runs(monkeypatch)
    monkeypatch.setattr(
        staged, "get_staged_files", lambda: pytest.fail("git must not be consulted")
    )

    assert staged.main() == 0
    assert calls == []


def test_clean_index_runs_no_validators(monkeypatch, capsys):
    calls = stub_runs(monkeypatch)
    monkeypatch.setattr(staged, "get_staged_files", lambda: [])

    assert staged.main() == 0
    assert calls == []
    assert "Running" not in capsys.readouterr().out


def test_only_validators_matching_the_staged_paths_run(monkeypatch, capsys):
    calls = stub_runs(monkeypatch)
    monkeypatch.setattr(
        staged, "get_staged_files", lambda: ["localisation/english/x_l_english.yml"]
    )

    assert staged.main() == 0
    assert scripts(calls) == ["validate_localisation.py"]
    assert "Running localisation validator..." in capsys.readouterr().out


def test_suffix_must_match_as_well_as_the_prefix(monkeypatch):
    calls = stub_runs(monkeypatch)
    monkeypatch.setattr(staged, "get_staged_files", lambda: ["interface/panel.gfx"])

    assert staged.main() == 0
    assert calls == []


def test_a_staged_file_fans_out_to_every_matching_validator(monkeypatch):
    calls = stub_runs(monkeypatch)
    monkeypatch.setattr(
        staged, "get_staged_files", lambda: ["common/national_focus/USA.txt"]
    )

    assert staged.main() == 0
    assert scripts(calls) == [
        "validate_variables.py",
        "validate_cosmetic_tags.py",
        "validate_ideas.py",
        "validate_focus_tree.py",
        "validate_scripted_params.py",
    ]


def test_staged_file_list_is_exported_to_the_validators(monkeypatch):
    stub_runs(monkeypatch)
    monkeypatch.setattr(staged, "get_staged_files", lambda: ["events/a.txt"])

    staged.main()

    assert staged.os.environ["MD_STAGED_FILES"] == "events/a.txt"


def test_a_failing_validator_fails_the_hook(monkeypatch):
    stub_runs(monkeypatch, {"validate_events.py": 1})
    monkeypatch.setattr(staged, "get_staged_files", lambda: ["events/a.txt"])

    assert staged.main() == 1


def test_one_failure_does_not_stop_the_remaining_validators(monkeypatch):
    calls = stub_runs(monkeypatch, {"validate_variables.py": 1})
    monkeypatch.setattr(
        staged, "get_staged_files", lambda: ["common/scripted_effects/x.txt"]
    )

    assert staged.main() == 1
    assert "validate_scripted_params.py" in scripts(calls)


def test_a_timeout_is_reported_and_fails_the_hook(monkeypatch, capsys):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(staged.subprocess, "run", fake_run)
    monkeypatch.setattr(staged, "get_staged_files", lambda: ["events/a.txt"])

    assert staged.main() == 1
    assert (
        "ERROR: events validator timed out after 5 minutes" in capsys.readouterr().out
    )


def test_timing_summary_lists_each_validator(monkeypatch, capsys):
    monkeypatch.setenv("MD_TIMING", "1")
    stub_runs(monkeypatch)
    monkeypatch.setattr(
        staged, "get_staged_files", lambda: ["localisation/english/x_l_english.yml"]
    )

    staged.main()

    err = capsys.readouterr().err
    assert "Validator timing:" in err
    assert "localisation" in err
    assert "total" in err


def test_timing_bars_stay_empty_when_no_time_elapses(monkeypatch, capsys):
    monkeypatch.setenv("MD_TIMING", "1")
    monkeypatch.setattr(staged.time, "perf_counter", lambda: 1.0)
    stub_runs(monkeypatch)
    monkeypatch.setattr(
        staged, "get_staged_files", lambda: ["localisation/english/x_l_english.yml"]
    )

    staged.main()

    assert "░" * 20 in capsys.readouterr().err


def test_timing_summary_is_suppressed_when_nothing_ran(monkeypatch, capsys):
    monkeypatch.setenv("MD_TIMING", "1")
    stub_runs(monkeypatch)
    monkeypatch.setattr(staged, "get_staged_files", lambda: ["README.md"])

    staged.main()

    assert "Validator timing:" not in capsys.readouterr().err


def test_every_validator_entry_is_wired_for_staged_strict_runs():
    for validator in staged.VALIDATORS:
        assert validator["cmd"][0] == "python3"
        assert validator["cmd"][1].startswith("tools/validation/validate_")
        assert {"--staged", "--strict", "--no-color"} <= set(validator["cmd"])
        assert validator["prefixes"]
        assert validator["suffix"].startswith(".")
