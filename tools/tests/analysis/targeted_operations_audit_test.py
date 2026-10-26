"""Audit discovery and failure handling on synthetic checkouts."""

from pathlib import Path

import pytest

from tools.analysis import targeted_operations_audit as audit


@pytest.mark.parametrize("folder", ["", "content", "analysis/nested"])
def test_discovery_includes_system_checks_and_excludes_unrelated_tools(
    tmp_path, folder
):
    suites = tmp_path / "tools/tests" / folder
    suites.mkdir(parents=True)
    included = [
        suites / "targeted_operations_behavior_test.py",
        suites / "top_lifecycle_probe_behavior_test.py",
    ]
    excluded = [suites / "unrelated_test.py", suites / "targeted_operations_helpers.py"]
    for path in included + excluded:
        path.touch()
    assert audit.discover_tests(tmp_path) == sorted(included)


@pytest.mark.parametrize(
    "generator_result,pytest_result,expected", [(0, 0, 0), (0, 5, 5), (2, 0, 1)]
)
def test_audit_runs_discovered_checks_and_propagates_failure(
    tmp_path, monkeypatch, generator_result, pytest_result, expected
):
    suite = tmp_path / "tools/tests/content/targeted_operations_behavior_test.py"
    suite.parent.mkdir(parents=True)
    suite.touch()
    calls = []

    def run(command):
        calls.append(command)
        if "pytest" in command:
            assert "no:cacheprovider" in command
            assert Path(command[command.index("--basetemp") + 1]).parent.is_dir()
            assert command[-1] == suite.relative_to(tmp_path).as_posix()
            return pytest_result
        return generator_result

    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "run", run)
    assert audit.main() == expected
    assert len(calls) == (1 if generator_result else 2)
    assert not (tmp_path / ".pytest_cache").exists()


def test_empty_discovery_fails_without_running_an_unscoped_suite(
    tmp_path, monkeypatch, capsys
):
    calls = []
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "run", lambda command: calls.append(command) or 0)
    assert audit.main() == 1
    assert len(calls) == 1
    assert "No Targeted Operations tests discovered" in capsys.readouterr().err


def test_subprocess_exit_status_is_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    assert audit.run([audit.sys.executable, "-c", "raise SystemExit(7)"]) == 7
