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


def test_check_node_accepts_supported_version(monkeypatch):
    monkeypatch.setattr(dev_setup, "_resolve_tool", lambda name: [name])
    monkeypatch.setattr(dev_setup, "get_version", lambda command: "v24.1.0")

    assert dev_setup.check_node() == (True, "v24.1.0")
