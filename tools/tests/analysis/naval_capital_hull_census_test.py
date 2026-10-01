"""Behavioral tests for tools/analysis/naval_capital_hull_census.py.

Builds a tiny synthetic units file + OOB directory so the capital set and
the census are both derived from real on-disk parsing, not mocks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ANALYSIS_DIR = Path(__file__).resolve().parents[2] / "analysis"
sys.path.insert(0, str(ANALYSIS_DIR))

import naval_capital_hull_census as census  # noqa: E402

NAVAL_UNITS_TEXT = (
    "sub_units = {\n"
    "\tcruiser = {\n"
    "\t\ttype = { capital_ship }\n"
    "\t}\n"
    "\tdestroyer = {\n"
    "\t\ttype = { capital_ship }\n"
    "\t}\n"
    "\tscreen_destroyer = {\n"
    "\t\ttype = { screen_ship }\n"
    "\t}\n"
    "\tcorvette = {\n"
    "\t\ttype = { screen_ship }\n"
    "\t}\n"
    "}\n"
)


def _write(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


@pytest.fixture
def naval_units_file(tmp_path: Path) -> Path:
    path = tmp_path / "MD_naval_units.txt"
    _write(path, NAVAL_UNITS_TEXT)
    return path


@pytest.fixture
def units_dir(tmp_path: Path) -> Path:
    units = tmp_path / "units"
    units.mkdir()
    _write(
        units / "AAA_2000_naval_mtg.txt",
        "units = {\n"
        '\tship = { name = "A" definition = cruiser }\n'
        '\tship = { name = "B" definition = screen_destroyer }\n'
        '\tship = { name = "C" definition = corvette }\n'
        "}\n",
    )
    _write(
        units / "BBB_2000_naval_mtg.txt",
        "units = {\n"
        '\tship = { name = "D" definition = screen_destroyer }\n'
        '\tship = { name = "E" definition = corvette }\n'
        "}\n",
    )
    _write(units / "not_a_naval_oob.txt", "irrelevant = { text = 1 }\n")
    return units


class TestCapitalShipDefinitions:
    def test_reads_capital_ship_typed_sub_units_only(self, naval_units_file):
        assert census.capital_ship_definitions(str(naval_units_file)) == [
            "cruiser",
            "destroyer",
        ]


class TestCensusFile:
    def test_counts_hulls_and_capital_flag_by_definition(
        self, units_dir, naval_units_file
    ):
        capital_defs = set(census.capital_ship_definitions(str(naval_units_file)))
        result = census.census_file(
            str(units_dir / "AAA_2000_naval_mtg.txt"), capital_defs
        )
        assert result.tag == "AAA"
        assert result.total == 3
        assert result.capital == 1
        assert result.by_definition == {
            "cruiser": 1,
            "screen_destroyer": 1,
            "corvette": 1,
        }


class TestRunCensus:
    def test_only_reads_naval_mtg_files_and_flags_zero_capital_navies(
        self, units_dir, naval_units_file
    ):
        results = census.run_census(str(units_dir), str(naval_units_file))
        by_tag = {r.tag: r for r in results}
        assert set(by_tag) == {"AAA", "BBB"}
        assert by_tag["AAA"].capital == 1
        assert by_tag["BBB"].capital == 0
