"""set_energy_tech_scurves.py against the shipped industry.txt."""

import sys
from pathlib import Path

import pytest
from shared.suite import load_tool_module

pytest.importorskip("scipy", reason="scipy is in the optional analysis group")
sc = load_tool_module("balance/set_energy_tech_scurves.py")


def test_dry_run_finds_every_chain_tech_and_writes_nothing(monkeypatch, capsys):
    industry = Path(sc.INDUSTRY)
    before = industry.read_bytes()
    monkeypatch.setattr(sys, "argv", ["set_energy_tech_scurves.py"])

    assert sc.main() == 0

    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "best source by year" in out
    assert industry.read_bytes() == before
