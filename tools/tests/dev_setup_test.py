"""Behavior tests for developer environment checks."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import dev_setup  # noqa: E402


def test_check_node_rejects_unparseable_version(monkeypatch):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: "not-a-version")

    assert dev_setup.check_node() == (False, "not-a-version")


def test_spec_satisfied_enforces_exact_and_minimum_versions():
    assert dev_setup._spec_satisfied("requests==2.34.2", "2.34.2")
    assert not dev_setup._spec_satisfied("requests==2.34.2", "2.34.1")
    assert dev_setup._spec_satisfied("pytest>=9.1.0", "9.2.0")
    assert not dev_setup._spec_satisfied("pytest>=9.1.0", "9.0.9")


def test_check_group_rejects_mismatched_version(monkeypatch, capsys):
    monkeypatch.setattr(dev_setup, "_group_packages", lambda _group: ["demo==2.0.0"])
    monkeypatch.setattr(dev_setup.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(dev_setup.importlib.metadata, "version", lambda _name: "1.0.0")
    assert not dev_setup._check_group("runtime", "Runtime")
    assert "requires demo==2.0.0" in capsys.readouterr().out


def test_check_node_accepts_supported_version(monkeypatch):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: "v24.1.0")

    assert dev_setup.check_node() == (True, "v24.1.0")
