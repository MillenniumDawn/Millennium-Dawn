"""Behavioral tests for tools/analysis/event_load.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.analysis import event_load  # noqa: E402

YEARLY = """MD_event_on_startup_events = {
\tUSA = { country_event = { id = usa.1 days = 5 } }
\tPOL = {
\t\tcountry_event = { id = poland.1 days = 9 }
\t}
}

trigger_year_2001_events = {
\tUSA = {
\t\tcountry_event = { id = usa.2 days = 40 }
\t\tUSA_widget_milestone_2001 = yes
\t}
\tgpu_milestone_2001 = yes
}

trigger_year_2002_events = {
\tUSA = { country_event = { id = usa.4 days = 300 } }
}
"""

EFFECTS = """USA_widget_milestone_2001 = {
\tcountry_event = { id = usa.3 days = 55 }
}

gpu_milestone_2001 = {
\tUSA = { country_event = { id = shared.1 days = 60 } }
\tPOL = { country_event = { id = shared.1 days = 60 } }
}
"""


@pytest.fixture
def mod(tmp_path):
    """A minimal mod tree with a yearly pulse and one scripted effect file."""
    effects = tmp_path / "common" / "scripted_effects"
    effects.mkdir(parents=True)
    with open(
        effects / "00_yearly_effects.txt", "w", encoding="utf-8", newline=""
    ) as fh:
        fh.write(YEARLY)
    with open(effects / "99_effects.txt", "w", encoding="utf-8", newline="") as fh:
        fh.write(EFFECTS)
    return tmp_path


def test_scope_of_reads_both_block_shapes():
    block = "\tUSA = { country_event = { id = a.1 days = 1 } }\n\tPOL = {\n\t\tx = yes\n\t}\n"
    assert "a.1" in event_load.scope_of("USA", block)
    assert "x = yes" in event_load.scope_of("POL", block)
    assert event_load.scope_of("GER", block) == ""


def test_deliveries_follows_a_scripted_effect_call():
    bodies = {"inner": "\tcountry_event = { id = b.1 days = 7 }\n"}
    found = event_load.deliveries(
        "\tcountry_event = { id = a.1 days = 3 }\n\tinner = yes\n", bodies
    )
    assert sorted(found) == [("a.1", 3), ("b.1", 7)]


def test_deliveries_survives_a_cycle():
    bodies = {
        "a": "\tb = yes\n",
        "b": "\ta = yes\n\tcountry_event = { id = c.1 days = 2 }\n",
    }
    assert event_load.deliveries("\ta = yes\n", bodies) == [("c.1", 2)]


def test_deliveries_defaults_a_missing_day_offset_to_zero():
    assert event_load.deliveries("country_event = { id = a.1 }", {}) == [("a.1", 0)]


@pytest.mark.parametrize(
    "days,window,expected",
    [
        ([], 30, 0),
        ([1], 30, 1),
        ([1, 5, 40], 30, 2),
        ([1, 2, 3], 30, 3),
        ([1, 31], 30, 1),
    ],
)
def test_busiest_counts_the_fullest_window(days, window, expected):
    assert event_load.busiest(days, window) == expected


def test_collect_attributes_the_startup_pulse_to_the_bookmark_year(mod):
    rows = event_load.collect("USA", str(mod))
    assert ("usa.1", 5) in rows[event_load.STARTUP_YEAR]


def test_collect_resolves_a_milestone_wrapper(mod):
    rows = event_load.collect("USA", str(mod))
    assert ("usa.3", 55) in rows["2001"], (
        "an effect called inside the tag scope must resolve"
    )


def test_collect_resolves_a_shared_milestone_that_scopes_into_the_tag(mod):
    rows = event_load.collect("USA", str(mod))
    assert ("shared.1", 60) in rows["2001"], (
        "a top-level call scoping into the tag must resolve"
    )


def test_collect_keeps_tags_apart(mod):
    usa = event_load.collect("USA", str(mod))
    pol = event_load.collect("POL", str(mod))
    assert ("poland.1", 9) in pol[event_load.STARTUP_YEAR]
    assert ("poland.1", 9) not in usa[event_load.STARTUP_YEAR]
    assert ("shared.1", 60) in pol["2001"], "both tags get the shared milestone"


def test_main_reports_a_clustered_year(mod, monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["event_load", "--tag", "USA", "--path", str(mod), "--threshold", "2"],
    )
    assert event_load.main() == 0
    out = capsys.readouterr().out
    assert "USA scheduled event load" in out
    assert "clustered" in out
    assert "by namespace:" in out


def test_main_emits_json(mod, monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["event_load", "--tag", "USA", "--path", str(mod), "--json"]
    )
    assert event_load.main() == 0
    import json

    payload = json.loads(capsys.readouterr().out)
    assert payload["tag"] == "USA"
    assert payload["years"]["2002"]["count"] == 1


def test_main_handles_a_tag_with_nothing_scheduled(mod, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["event_load", "--tag", "ZZZ", "--path", str(mod)])
    assert event_load.main() == 0
    assert "no scheduled deliveries" in capsys.readouterr().out
