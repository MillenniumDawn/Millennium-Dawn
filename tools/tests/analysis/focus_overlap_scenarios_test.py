"""Scenario-report uncertainty and CLI regressions supporting layout review."""

import runpy
import sys

import focus_overlap_report as report
import pytest
from shared.suite import write_under


@pytest.mark.parametrize(
    "trigger,expected",
    [
        ("OR = { always = no always = yes }", True),
        ("OR = { always = no has_country_flag = unknown }", None),
        ("OR = { always = no }", False),
        ("OR = { }", False),
        ("NOT = { always = yes }", False),
        ("NOT = { always = no }", True),
        ("NOT = { has_country_flag = unknown }", None),
        ("AND = { always = yes original_tag = POL }", True),
        ("hidden_trigger = { tag = POL }", True),
        ("custom_trigger_tooltip = { always = no }", False),
        ("custom_trigger_tooltip = { tooltip = label always = yes }", None),
        ("any_country = { tag = POL }", None),
        ("tag = GER", False),
        ("date > invalid", None),
        ("date = 2006.1.1", None),
        ("date > 2006.1.1", False),
        ("date < 2006.1.1", False),
    ],
)
def test_three_valued_scenario_boundaries(trigger, expected):
    assert report.evaluate(trigger, report.Scenario(date=(2006, 1, 1))) is expected


def test_absent_scenario_date_cannot_prove_branch_or_offset():
    focuses = report.parse_focus_file(
        "focus = { id = A x = 5 y = 1 "
        "allow_branch = { date > 2006.1.1 } "
        "offset = { x = -5 trigger = { date > 2006.1.1 } } }"
    )
    scenario = report.Scenario()
    assert report.resolve_visibility(focuses, scenario) == {"A": True}
    assert report.resolve_positions(focuses, scenario) == {"A": (5, 1)}


@pytest.mark.parametrize("parent", ["missing", "B"])
def test_unresolvable_prerequisite_visibility_remains_conservative(parent):
    focuses = {
        "A": report.Focus("A", 1, "focus", prereq_groups=[[parent]]),
        "B": report.Focus("B", 2, "focus", prereq_groups=[["A"]]),
    }
    assert report.resolve_visibility(focuses, report.Scenario()) == {
        "A": True,
        "B": True,
    }


def test_region_validation_and_inclusive_edges():
    region = report.parse_region("-2,3,-1,4")
    assert report.in_region((-2, -1), region)
    assert report.in_region((3, 4), region)
    assert not report.in_region((4, 4), region)
    assert not report.in_region((3, 5), region)
    with pytest.raises(ValueError, match="x0,x1,y0,y1"):
        report.parse_region("1,2,3")
    with pytest.raises(ValueError):
        report.parse_region("1,2,3,unknown")


def test_duplicate_ids_keep_first_and_empty_prerequisites_are_ignored():
    focuses = report.parse_focus_file(
        "focus = { id = A x = 2 prerequisite = { ignored = yes } "
        "offset = { x = 1 unknown = yes } } "
        "\nfocus = { id = A x = 9 }"
    )
    assert focuses["A"].x == 2
    assert focuses["A"].prereq_groups == []
    assert focuses["A"].offsets[0].dx == 1


@pytest.mark.parametrize("as_script", [False, True])
def test_text_cli_reports_collision_adjacency_and_filtered_map(
    tmp_path, capsys, monkeypatch, as_script
):
    path = write_under(
        tmp_path,
        "layout.txt",
        "focus_tree = {\n"
        "focus = { id = A x = -1 y = 1 }\n"
        "focus = { id = B x = -1 y = 1 }\n"
        "focus = { id = C x = 0 y = 1 }\n"
        "focus = { id = outside x = 10 y = 1 } }",
    )
    args = ["--file", str(path), "--region=-1,0,1,1", "--adjacent", "--map"]
    if as_script:
        monkeypatch.setattr(sys, "path", list(sys.path))
        monkeypatch.setattr(sys, "argv", [report.__file__, *args])
        with pytest.raises(SystemExit) as error:
            runpy.run_path(report.__file__, run_name="__main__")
        assert error.value.code == 0
    else:
        assert report.main(args) == 0
    output = capsys.readouterr().out
    assert "Overlapping cells (1):" in output
    assert "Adjacent columns (1):" in output
    assert "Visible focuses (3):" in output
    assert "outside" not in output
    assert all(f"{name} (l" in output for name in ("A", "B", "C"))
