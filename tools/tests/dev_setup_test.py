"""Behavior tests for developer environment checks."""

import os
import sys
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

import dev_setup
import pytest

Version = namedtuple("Version", "major minor micro releaselevel serial")

CHECKS = {
    "check_python": True,
    "check_pre_commit": True,
    "check_hooks_installed": True,
    "check_pip_packages": True,
    "check_dev_packages": True,
    "check_bun": True,
    "check_docs_deps": True,
}
INSTALLS = {
    "install_pre_commit": True,
    "install_hooks": True,
    "install_pip_packages": True,
    "install_dev_packages": True,
    "install_docs_deps": True,
}


def completed(returncode=0, stdout=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout)


def stub_run(monkeypatch, handler=lambda cmd: completed()):
    """Replace dev_setup.run; the handler may return a result or an exception."""
    calls = []

    def fake_run(cmd, check=True, capture=False, cwd=None):
        calls.append(cmd)
        result = handler(cmd)
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(dev_setup, "run", fake_run)
    return calls


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


# ── thin wrappers ───────────────────────────────────────────────────────────


def test_run_passes_text_mode_and_working_directory(monkeypatch, tmp_path):
    recorded = {}

    def fake_run(cmd, **kwargs):
        recorded.update(kwargs)
        recorded["cmd"] = cmd
        return completed()

    monkeypatch.setattr(dev_setup.subprocess, "run", fake_run)

    dev_setup.run(["git", "status"], check=False, capture=True, cwd=tmp_path)

    assert recorded["cmd"] == ["git", "status"]
    assert recorded["check"] is False
    assert recorded["capture_output"] is True
    assert recorded["text"] is True
    assert recorded["cwd"] == tmp_path


@pytest.mark.parametrize(("ok", "expected"), [(True, "OK"), (False, "MISSING")])
def test_check_mark_labels_status(ok, expected):
    assert dev_setup.check_mark(ok) == expected


def test_get_version_returns_the_last_token(monkeypatch):
    stub_run(monkeypatch, lambda cmd: completed(stdout="pre-commit 4.5.0\n"))

    assert dev_setup.get_version(["pre-commit", "--version"]) == "4.5.0"


def test_get_version_is_none_when_the_command_fails(monkeypatch):
    stub_run(monkeypatch, lambda cmd: completed(returncode=1, stdout="boom"))

    assert dev_setup.get_version(["bun", "--version"]) is None


def test_get_version_is_none_when_the_binary_is_absent(monkeypatch):
    stub_run(monkeypatch, lambda cmd: FileNotFoundError("bun"))

    assert dev_setup.get_version(["bun", "--version"]) is None


# ── tool resolution ─────────────────────────────────────────────────────────


def test_resolve_tool_falls_back_to_the_bare_name():
    assert dev_setup._resolve_tool("pre-commit") == ["pre-commit"]


def test_resolve_tool_prefers_an_installed_nvm_node(monkeypatch, tmp_path):
    node = tmp_path / ".nvm" / "versions" / "node" / "v26.0.0" / "bin" / "node"
    write(node, "#!/bin/sh\n")
    node.chmod(0o755)
    monkeypatch.setattr(dev_setup.Path, "home", staticmethod(lambda: tmp_path))

    assert dev_setup._resolve_tool("node") == [str(node)]


def test_resolve_tool_prefers_the_home_bun(monkeypatch, tmp_path):
    bun = tmp_path / ".bun" / "bin" / "bun"
    write(bun, "#!/bin/sh\n")
    bun.chmod(0o755)
    monkeypatch.setattr(dev_setup.Path, "home", staticmethod(lambda: tmp_path))

    assert dev_setup._resolve_tool("bun") == [str(bun)]


@pytest.mark.skipif(os.name == "nt", reason="os.access(X_OK) is not meaningful on nt")
def test_resolve_tool_ignores_a_non_executable_candidate(monkeypatch, tmp_path):
    bun = tmp_path / ".bun" / "bin" / "bun"
    write(bun, "not a program\n")
    bun.chmod(0o644)
    monkeypatch.setattr(dev_setup.Path, "home", staticmethod(lambda: tmp_path))

    assert dev_setup._resolve_tool("bun") == ["bun"]


def test_resolve_tool_survives_an_unreadable_candidate(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup.Path, "home", staticmethod(lambda: tmp_path))

    def boom(self, *args, **kwargs):
        raise OSError("filesystem is unhappy")

    monkeypatch.setattr(dev_setup.Path, "exists", boom)

    assert dev_setup._resolve_tool("bun") == ["bun"]


# ── interpreter / venv probes ───────────────────────────────────────────────


def test_in_virtualenv_detects_a_diverging_base_prefix(monkeypatch):
    monkeypatch.setattr(sys, "base_prefix", "/usr", raising=False)
    monkeypatch.setattr(sys, "prefix", "/usr/local/venv")

    assert dev_setup.in_virtualenv() is True


def test_in_virtualenv_is_false_for_a_system_interpreter(monkeypatch):
    monkeypatch.delattr(sys, "real_prefix", raising=False)
    monkeypatch.setattr(sys, "base_prefix", "/usr", raising=False)
    monkeypatch.setattr(sys, "prefix", "/usr")

    assert dev_setup.in_virtualenv() is False


def test_is_externally_managed_reads_the_pep668_marker(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup.sysconfig, "get_path", lambda _name: str(tmp_path))
    assert dev_setup.is_externally_managed() is False

    write(tmp_path / "EXTERNALLY-MANAGED", "[externally-managed]\n")
    assert dev_setup.is_externally_managed() is True


def test_venv_python_path_is_none_without_a_venv(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)

    assert dev_setup.venv_python_path() is None


def test_venv_python_path_is_none_for_an_empty_venv_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    (tmp_path / ".venv").mkdir()

    assert dev_setup.venv_python_path() is None


def test_venv_python_path_finds_the_interpreter(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    ext = ".exe" if os.name == "nt" else ""
    python = tmp_path / ".venv" / bin_dir / f"python{ext}"
    write(python, "")

    assert dev_setup.venv_python_path() == python


def test_create_venv_reuses_an_existing_interpreter(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    ext = ".exe" if os.name == "nt" else ""
    python = tmp_path / ".venv" / bin_dir / f"python{ext}"
    write(python, "")
    calls = stub_run(monkeypatch)

    assert dev_setup.create_venv() == python
    assert calls == []
    assert "Using existing local virtual environment" in capsys.readouterr().out


def test_create_venv_builds_a_new_environment(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    ext = ".exe" if os.name == "nt" else ""
    python = tmp_path / ".venv" / bin_dir / f"python{ext}"

    def handler(cmd):
        write(python, "")
        return completed()

    calls = stub_run(monkeypatch, handler)

    assert dev_setup.create_venv() == python
    assert calls == [[sys.executable, "-m", "venv", str(tmp_path / ".venv")]]
    assert "Creating local virtual environment" in capsys.readouterr().out


def test_create_venv_raises_when_the_interpreter_never_appears(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    stub_run(monkeypatch)

    with pytest.raises(RuntimeError, match="Failed to create venv"):
        dev_setup.create_venv()


def test_reexec_with_hands_the_argv_tail_to_the_new_interpreter(monkeypatch, capsys):
    recorded = {}
    monkeypatch.setattr(
        dev_setup.os,
        "execv",
        lambda path, argv: recorded.update(path=path, argv=argv),
    )
    monkeypatch.setattr(sys, "argv", ["dev_setup.py", "--docs"])

    dev_setup.reexec_with(Path("/venv/bin/python"))

    assert recorded["path"] == "/venv/bin/python"
    assert recorded["argv"][0] == "/venv/bin/python"
    assert recorded["argv"][-1] == "--docs"
    assert "Switching to venv Python" in capsys.readouterr().out


# ── individual checks ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("version", "ok", "note"),
    [
        ((3, 13, 1), True, "(recommended)"),
        ((3, 11, 4), True, "3.12+ recommended"),
        ((3, 9, 18), False, "too old"),
    ],
)
def test_check_python_grades_the_interpreter(version, ok, note, monkeypatch, capsys):
    monkeypatch.setattr(sys, "version_info", Version(*version, "final", 0))

    assert dev_setup.check_python() is ok
    assert note in capsys.readouterr().out


def test_check_pre_commit_reports_the_module_version(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "get_version", lambda cmd: "4.5.0")
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: None)

    assert dev_setup.check_pre_commit() is True
    assert "pre-commit: 4.5.0" in capsys.readouterr().out


def test_check_pre_commit_falls_back_to_path_without_a_venv(monkeypatch):
    probed = []

    def fake_version(cmd):
        probed.append(cmd)
        return "4.5.0" if cmd[0] == "pre-commit" else None

    monkeypatch.setattr(dev_setup, "get_version", fake_version)
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: None)

    assert dev_setup.check_pre_commit() is True
    assert probed[-1] == ["pre-commit", "--version"]


def test_check_pre_commit_does_not_leave_the_venv(monkeypatch, tmp_path, capsys):
    probed = []

    def fake_version(cmd):
        probed.append(cmd)
        return None

    monkeypatch.setattr(dev_setup, "get_version", fake_version)
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: tmp_path / "python")

    assert dev_setup.check_pre_commit() is False
    assert len(probed) == 1
    assert "pre-commit: not installed" in capsys.readouterr().out


def test_check_hooks_installed_rejects_a_hooks_path_override(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    stub_run(monkeypatch, lambda cmd: completed(stdout="/elsewhere/hooks\n"))

    assert dev_setup.check_hooks_installed() is False
    assert "core.hooksPath is set to '/elsewhere/hooks'" in capsys.readouterr().out


def test_check_hooks_installed_reports_a_missing_hook(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    stub_run(monkeypatch, lambda cmd: FileNotFoundError("git"))

    assert dev_setup.check_hooks_installed() is False
    assert "Git hooks: MISSING" in capsys.readouterr().out


def test_check_hooks_installed_accepts_a_pre_commit_hook(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: False)
    stub_run(monkeypatch, lambda cmd: completed(stdout=""))
    write(tmp_path / ".git" / "hooks" / "pre-commit", "#!/bin/sh\nexec pre-commit\n")

    assert dev_setup.check_hooks_installed() is True


def test_check_hooks_installed_requires_the_venv_interpreter(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: True)
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: tmp_path / "python")
    stub_run(monkeypatch, lambda cmd: completed(stdout=""))
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    write(hook, "#!/bin/sh\nexec /usr/bin/python -m pre-commit\n")

    assert dev_setup.check_hooks_installed() is False

    write(hook, f"#!/bin/sh\nexec {sys.executable} -m pre-commit\n")
    assert dev_setup.check_hooks_installed() is True
    assert "Git hooks: OK" in capsys.readouterr().out


# ── dependency-group inspection ─────────────────────────────────────────────


def test_group_packages_is_empty_without_a_pyproject(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "PYPROJECT", tmp_path / "absent.toml")

    assert dev_setup._group_packages("runtime") == []


def test_group_packages_reads_the_named_group(monkeypatch, tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    write(
        pyproject,
        "[dependency-groups]\n"
        'runtime = [\n  "requests>=2.32",\n  "pillow",\n]\n'
        'dev = [\n  "pytest>=9.1.0",\n]\n',
    )
    monkeypatch.setattr(dev_setup, "PYPROJECT", pyproject)

    assert dev_setup._group_packages("runtime") == ["requests>=2.32", "pillow"]
    assert dev_setup._group_packages("analysis") == []


def test_version_tuple_ignores_non_numeric_separators():
    assert dev_setup._version_tuple("2.34.2") == (2, 34, 2)
    assert dev_setup._version_tuple("v24.15.0") == (24, 15, 0)


def test_spec_satisfied_enforces_exact_and_minimum_versions():
    assert dev_setup._spec_satisfied("requests==2.34.2", "2.34.2")
    assert not dev_setup._spec_satisfied("requests==2.34.2", "2.34.1")
    assert dev_setup._spec_satisfied("pytest>=9.1.0", "9.2.0")
    assert not dev_setup._spec_satisfied("pytest>=9.1.0", "9.0.9")


def test_spec_satisfied_accepts_an_unpinned_package():
    assert dev_setup._spec_satisfied("pillow", "11.0.0")


def test_spec_satisfied_rejects_an_unparseable_spec():
    assert not dev_setup._spec_satisfied("requests~=2.34", "2.34.2")


def test_check_group_reports_a_missing_group(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_group_packages", lambda _group: [])

    assert not dev_setup._check_group("analysis", "Analysis")
    assert "group 'analysis' not found in pyproject.toml" in capsys.readouterr().out


def test_check_group_reports_an_uninstalled_package(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_group_packages", lambda _group: ["demo>=1.0"])
    monkeypatch.setattr(dev_setup.importlib.util, "find_spec", lambda _name: None)

    assert not dev_setup._check_group("runtime", "Runtime")
    assert "Runtime: demo (missing)" in capsys.readouterr().out


def test_check_group_reports_an_unregistered_distribution(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_group_packages", lambda _group: ["demo"])
    monkeypatch.setattr(dev_setup.importlib.util, "find_spec", lambda _name: object())

    def missing(_name):
        raise dev_setup.importlib.metadata.PackageNotFoundError(_name)

    monkeypatch.setattr(dev_setup.importlib.metadata, "version", missing)

    assert not dev_setup._check_group("runtime", "Runtime")
    assert "demo (version unknown)" in capsys.readouterr().out


def test_check_group_rejects_mismatched_version(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_group_packages", lambda _group: ["demo==2.0.0"])
    monkeypatch.setattr(dev_setup.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(dev_setup.importlib.metadata, "version", lambda _name: "1.0.0")
    assert not dev_setup._check_group("runtime", "Runtime")
    assert "requires demo==2.0.0" in capsys.readouterr().out


def test_check_group_maps_distribution_names_to_import_names(monkeypatch, capsys):
    imported = []

    def fake_find_spec(name):
        imported.append(name)
        return object()

    monkeypatch.setattr(
        dev_setup, "_group_packages", lambda _group: ["pillow>=11", "pyyaml", "ruff"]
    )
    monkeypatch.setattr(dev_setup.importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(dev_setup.importlib.metadata, "version", lambda _name: "11.1.0")

    assert dev_setup._check_group("runtime", "Tool dependencies") is True
    assert imported == ["PIL", "yaml", "ruff"]
    assert "Tool dependencies: OK" in capsys.readouterr().out


def test_package_checks_target_the_runtime_and_dev_groups(monkeypatch):
    seen = []
    monkeypatch.setattr(
        dev_setup,
        "_check_group",
        lambda group, label: seen.append(group) or True,
    )

    assert dev_setup.check_pip_packages() is True
    assert dev_setup.check_dev_packages() is True
    assert seen == ["runtime", "dev"]


# ── docs toolchain ──────────────────────────────────────────────────────────


def test_check_node_rejects_unparseable_version(monkeypatch):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: "not-a-version")

    assert dev_setup.check_node() == (False, "not-a-version")


def test_check_node_accepts_supported_version(monkeypatch):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: "v24.1.0")

    assert dev_setup.check_node() == (True, "v24.1.0")


def test_check_node_rejects_an_outdated_major(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: "v20.11.0")

    assert dev_setup.check_node() == (False, "v20.11.0")
    assert "too old (need v24+)" in capsys.readouterr().out


def test_check_node_reports_an_absent_node(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: None)

    assert dev_setup.check_node() == (False, None)
    assert "Node.js: not installed" in capsys.readouterr().out


@pytest.mark.parametrize(("version", "installed"), [("1.2.3", True), (None, False)])
def test_check_bun_follows_the_version_probe(version, installed, monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: version)

    assert dev_setup.check_bun() is installed
    assert ("1.2.3" if installed else "not installed") in capsys.readouterr().out


def test_check_docs_deps_requires_a_populated_node_modules(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "DOCS_DIR", tmp_path)
    assert dev_setup.check_docs_deps() is False

    (tmp_path / "node_modules").mkdir()
    assert dev_setup.check_docs_deps() is False

    write(tmp_path / "node_modules" / "astro" / "package.json", "{}")
    assert dev_setup.check_docs_deps() is True


# ── installers ──────────────────────────────────────────────────────────────


def test_install_pre_commit_succeeds_on_the_first_attempt(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: True)
    calls = stub_run(monkeypatch)

    assert dev_setup.install_pre_commit() is True
    assert calls == [[sys.executable, "-m", "pip", "install", "pre-commit"]]
    assert "Installing pre-commit" in capsys.readouterr().out


def test_install_pre_commit_retries_with_user_scope(monkeypatch):
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: True)
    calls = stub_run(monkeypatch, lambda cmd: completed(returncode=1))

    assert dev_setup.install_pre_commit() is False
    assert calls[1] == [sys.executable, "-m", "pip", "install", "--user", "pre-commit"]


def test_install_pre_commit_switches_into_a_venv_when_externally_managed(monkeypatch):
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: False)
    monkeypatch.setattr(dev_setup, "is_externally_managed", lambda: True)
    monkeypatch.setattr(dev_setup, "create_venv", lambda: Path("/venv/bin/python"))
    switched = []
    monkeypatch.setattr(dev_setup, "reexec_with", switched.append)
    stub_run(monkeypatch)

    dev_setup.install_pre_commit()

    assert switched == [Path("/venv/bin/python")]


def test_ensure_hooks_path_unset_clears_a_redundant_override(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    default = str(tmp_path / ".git" / "hooks")
    calls = stub_run(monkeypatch, lambda cmd: completed(stdout=f"{default}\n"))

    dev_setup._ensure_hooks_path_unset()

    assert calls[-1] == ["git", "config", "--unset-all", "core.hooksPath"]
    assert "Unsetting redundant core.hooksPath" in capsys.readouterr().out


def test_ensure_hooks_path_unset_keeps_a_deliberate_override(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    calls = stub_run(monkeypatch, lambda cmd: completed(stdout="/custom/hooks\n"))

    dev_setup._ensure_hooks_path_unset()

    assert len(calls) == 1


def test_ensure_hooks_path_unset_ignores_an_empty_setting(monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    calls = stub_run(monkeypatch, lambda cmd: completed(stdout="\n"))

    dev_setup._ensure_hooks_path_unset()

    assert len(calls) == 1


def test_ensure_hooks_path_unset_tolerates_a_missing_git(monkeypatch):
    stub_run(monkeypatch, lambda cmd: FileNotFoundError("git"))

    dev_setup._ensure_hooks_path_unset()


def test_install_hooks_clears_the_override_then_installs(monkeypatch, capsys):
    cleared = []
    monkeypatch.setattr(
        dev_setup, "_ensure_hooks_path_unset", lambda: cleared.append(1)
    )
    calls = stub_run(monkeypatch)

    assert dev_setup.install_hooks() is True
    assert cleared == [1]
    assert calls == [[sys.executable, "-m", "pre_commit", "install"]]
    assert "Installing git hooks" in capsys.readouterr().out


def test_install_hooks_reports_a_failed_install(monkeypatch):
    monkeypatch.setattr(dev_setup, "_ensure_hooks_path_unset", lambda: None)
    stub_run(monkeypatch, lambda cmd: completed(returncode=1))

    assert dev_setup.install_hooks() is False


def test_pip_install_group_upgrades_pip_then_installs_the_group(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: True)
    monkeypatch.setattr(dev_setup, "PYPROJECT", Path("/repo/pyproject.toml"))
    calls = stub_run(monkeypatch)

    assert dev_setup._pip_install_group("runtime", "tool dependencies") is True
    assert calls[0][-3:] == ["install", "--upgrade", "pip"]
    assert calls[1][-2:] == ["--group", "/repo/pyproject.toml:runtime"]
    assert "Installing tool dependencies" in capsys.readouterr().out


def test_pip_install_group_retries_with_user_scope(monkeypatch):
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: True)
    monkeypatch.setattr(dev_setup, "PYPROJECT", Path("/repo/pyproject.toml"))

    def handler(cmd):
        return completed(returncode=0 if "--upgrade" in cmd else 1)

    calls = stub_run(monkeypatch, handler)

    assert dev_setup._pip_install_group("dev", "dev/test dependencies") is False
    assert "--user" in calls[2]


def test_pip_install_group_switches_into_a_venv_when_externally_managed(monkeypatch):
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: False)
    monkeypatch.setattr(dev_setup, "is_externally_managed", lambda: True)
    monkeypatch.setattr(dev_setup, "create_venv", lambda: Path("/venv/bin/python"))
    switched = []
    monkeypatch.setattr(dev_setup, "reexec_with", switched.append)
    stub_run(monkeypatch)

    dev_setup._pip_install_group("runtime", "tool dependencies")

    assert switched == [Path("/venv/bin/python")]


def test_package_installers_target_the_runtime_and_dev_groups(monkeypatch):
    seen = []
    monkeypatch.setattr(
        dev_setup,
        "_pip_install_group",
        lambda group, label: seen.append((group, label)) or True,
    )

    assert dev_setup.install_pip_packages() is True
    assert dev_setup.install_dev_packages() is True
    assert [group for group, _ in seen] == ["runtime", "dev"]


def test_install_docs_deps_runs_bun_install_in_the_docs_directory(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(dev_setup, "DOCS_DIR", tmp_path)
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    recorded = {}

    def fake_run(cmd, check=True, capture=False, cwd=None):
        recorded["cmd"] = cmd
        recorded["cwd"] = cwd
        return completed()

    monkeypatch.setattr(dev_setup, "run", fake_run)

    assert dev_setup.install_docs_deps() is True
    assert recorded == {"cmd": ["bun", "install"], "cwd": tmp_path}
    assert "Installing docs dependencies" in capsys.readouterr().out


# ── main() ──────────────────────────────────────────────────────────────────


@pytest.fixture
def setup_env(monkeypatch):
    """Stub every probe and installer so main() can be driven by state alone."""
    state = {**CHECKS, **INSTALLS, "check_node": (True, "v24.0.0")}
    calls = []

    def patch(name):
        def stub(*_args, **_kwargs):
            calls.append(name)
            return state[name]

        monkeypatch.setattr(dev_setup, name, stub)

    for name in state:
        patch(name)
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: None)
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: True)
    monkeypatch.setattr(dev_setup, "reexec_with", lambda python: calls.append("reexec"))
    return SimpleNamespace(state=state, calls=calls)


def run_main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["dev_setup.py", *argv])
    with pytest.raises(SystemExit) as exc:
        dev_setup.main()
    return exc.value.code


def test_check_mode_reports_a_ready_environment(setup_env, monkeypatch, capsys):
    assert run_main(monkeypatch, "--check") == 0
    assert "Everything is set up." in capsys.readouterr().out
    assert not any(name.startswith("install_") for name in setup_env.calls)


def test_check_mode_ignores_the_docs_stack_unless_asked(setup_env, monkeypatch, capsys):
    setup_env.state["check_bun"] = False

    assert run_main(monkeypatch, "--check") == 0
    assert "Bun" not in capsys.readouterr().out.split("Everything")[1]


def test_check_mode_fails_on_a_missing_component(setup_env, monkeypatch, capsys):
    setup_env.state["check_hooks_installed"] = False

    assert run_main(monkeypatch, "--check") == 1
    assert "Some components need setup." in capsys.readouterr().out


def test_check_mode_with_docs_fails_on_a_missing_docs_dependency(
    setup_env, monkeypatch
):
    setup_env.state["check_docs_deps"] = False

    assert run_main(monkeypatch, "--check", "--docs") == 1


def test_main_reexecs_into_the_local_venv(setup_env, monkeypatch, tmp_path):
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: tmp_path / "python")
    monkeypatch.setattr(dev_setup, "in_virtualenv", lambda: False)

    run_main(monkeypatch, "--check")

    assert "reexec" in setup_env.calls


def test_main_stops_on_an_unsupported_python(setup_env, monkeypatch, capsys):
    setup_env.state["check_python"] = False

    assert run_main(monkeypatch) == 1
    assert "Python 3.10+ is required" in capsys.readouterr().out
    assert not any(name.startswith("install_") for name in setup_env.calls)


def test_main_installs_only_what_is_missing(setup_env, monkeypatch, capsys):
    setup_env.state["check_pre_commit"] = False
    setup_env.state["check_dev_packages"] = False

    assert run_main(monkeypatch) == 0
    assert "install_pre_commit" in setup_env.calls
    assert "install_dev_packages" in setup_env.calls
    assert "install_pip_packages" not in setup_env.calls
    assert "install_hooks" not in setup_env.calls
    assert "Setup complete." in capsys.readouterr().out


def test_main_installs_the_git_hooks_when_absent(setup_env, monkeypatch):
    setup_env.state["check_hooks_installed"] = False

    assert run_main(monkeypatch) == 0
    assert "install_hooks" in setup_env.calls


def test_main_reports_a_failed_installer(setup_env, monkeypatch, capsys):
    setup_env.state["check_pip_packages"] = False
    setup_env.state["install_pip_packages"] = False

    assert run_main(monkeypatch) == 1
    assert "Setup finished with some issues." in capsys.readouterr().out


def test_main_prints_the_posix_activation_hint(
    setup_env, monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: tmp_path / "python")
    monkeypatch.setattr(dev_setup.os, "name", "posix")

    assert run_main(monkeypatch) == 0
    assert (
        f"source {tmp_path / '.venv' / 'bin' / 'activate'}" in capsys.readouterr().out
    )


def test_main_prints_the_windows_activation_hint(
    setup_env, monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(dev_setup, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(dev_setup, "venv_python_path", lambda: tmp_path / "python")
    monkeypatch.setattr(dev_setup.os, "name", "nt")

    assert run_main(monkeypatch) == 0
    out = capsys.readouterr().out
    assert "activate.bat" in out
    assert "Activate.ps1" in out


def test_docs_setup_installs_the_missing_docs_dependencies(
    setup_env, monkeypatch, capsys
):
    setup_env.state["check_docs_deps"] = False

    assert run_main(monkeypatch, "--docs") == 0
    assert "install_docs_deps" in setup_env.calls
    assert "cd docs && bun run dev" in capsys.readouterr().out


def test_docs_setup_does_not_reprobe_a_working_toolchain(setup_env, monkeypatch):
    run_main(monkeypatch, "--docs")

    assert setup_env.calls.count("check_node") == 1
    assert setup_env.calls.count("check_bun") == 1


def test_docs_setup_demands_a_modern_node(setup_env, monkeypatch, capsys):
    setup_env.state["check_node"] = (False, "v20.0.0")

    assert run_main(monkeypatch, "--docs") == 1
    out = capsys.readouterr().out
    assert "Node.js 24+ is required for docs" in out
    assert "install_docs_deps" not in setup_env.calls


def test_docs_setup_demands_bun(setup_env, monkeypatch, capsys):
    setup_env.state["check_bun"] = False

    assert run_main(monkeypatch, "--docs") == 1
    assert "Bun is required for docs" in capsys.readouterr().out
