"""set_renewable_hotspots.py against the shipped map and state history."""

import sys

import pytest
from shared.paths import REPO_ROOT
from shared.suite import load_tool_module

pytest.importorskip("numpy", reason="numpy is in the optional analysis group")
pytest.importorskip("PIL", reason="Pillow is in the optional analysis group")
hots = load_tool_module("balance/set_renewable_hotspots.py")


def test_dry_run_rates_the_real_states_and_writes_nothing(monkeypatch, capsys):
    states = sorted((REPO_ROOT / "history" / "states").glob("*.txt"))
    before = [path.read_bytes() for path in states]
    monkeypatch.setattr(
        sys, "argv", ["set_renewable_hotspots.py", "--root", str(REPO_ROOT)]
    )

    assert hots.main() == 0

    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "mean capacity factor" in out
    assert [path.read_bytes() for path in states] == before
