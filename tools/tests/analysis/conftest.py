"""Shared fixtures for analysis-tool coverage tests.

Each fixture builds a synthetic, self-contained mini-repo in a tmpdir shaped
just enough to drive the production modules' parsers, calculations, and
file writes. We do not patch the modules' module-level BASE_DIR/STATES_DIR/
IDEAS_DIR/COUNTRIES_DIR constants — the production code is exercised as a
real reader of a real on-disk tree. Tests only patch sys.argv / argparse so
the CLI entry points run with controlled arguments.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ANALYSIS_DIR = Path(__file__).resolve().parents[2] / "analysis"
REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    """A tmpdir laid out like the real repo: history/states, history/countries,
    common/ideas, and tools/analysis/. Returns the root Path."""
    (tmp_path / "history" / "states").mkdir(parents=True)
    (tmp_path / "history" / "countries").mkdir(parents=True)
    (tmp_path / "common" / "ideas").mkdir(parents=True)
    (tmp_path / "tools" / "analysis").mkdir(parents=True)
    return tmp_path


def write_text(path: Path, content: str) -> None:
    """Write text with the LF-only newline discipline required by AGENTS.md."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def _state_file(name: str, body: str) -> str:
    return f"{name}.txt\n{body}"


def _country_file(tag: str, body: str) -> str:
    return f"{tag} - Test.txt\n{body}"


@pytest.fixture
def state_a_text() -> str:
    """A minimal state with id, manpower, owner, productivity, one building, one resource."""
    return (
        "state = {\n"
        "\tid = 100\n"
        '\tname = "STATE_TEST_A"\n'
        "\tmanpower = 1500000\n"
        "\tstate_category = state_03\n"
        "\n"
        "\thistory = {\n"
        "\t\towner = TST\n"
        "\t\tset_variable = { state_renewable_capacity_factor_modifier_var = 1.0 }\n"
        "\t\tset_variable = { productivity_state_var = 700 }\n"
        "\t\tresources = { steel = 4.0 }\n"
        "\t\tbuildings = {\n"
        "\t\t\tindustrial_complex = 4\n"
        "\t\t\tarms_factory = 2\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


@pytest.fixture
def state_b_text() -> str:
    return (
        "state = {\n"
        "\tid = 200\n"
        '\tname = "STATE_TEST_B"\n'
        "\tmanpower = 800000\n"
        "\tstate_category = state_02\n"
        "\n"
        "\thistory = {\n"
        "\t\towner = TST\n"
        "\t\tset_variable = { state_renewable_capacity_factor_modifier_var = 1.0 }\n"
        "\t\tset_variable = { productivity_state_var = 500 }\n"
        "\t\tresources = { oil = 6.0 aluminium = 2.0 }\n"
        "\t\tbuildings = {\n"
        "\t\t\tindustrial_complex = 2\n"
        "\t\t\toffices = 3\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


@pytest.fixture
def country_tst_text() -> str:
    return (
        "capital = 100\n"
        "2000.1.1 = {\n"
        "\tadd_ideas = {\n"
        "\t\thigh_health\n"
        "\t\tindustry_modern\n"
        "\t}\n"
        "\tset_variable = { gdp_per_capita = 12.5 }\n"
        "}\n"
    )


@pytest.fixture
def idea_high_health_text() -> str:
    return (
        "ideas = {\n"
        "high_health = {\n"
        "\tmodifier = {\n"
        "\t\tcivilian_factories_productivity = 0.10\n"
        "\t\ttotal_workforce_modifier = 0.05\n"
        "\t}\n"
        "}\n"
        "industry_modern = {\n"
        "\tmodifier = {\n"
        "\t\tcivilian_factories_productivity = 0.05\n"
        "\t\tmilitary_factories_productivity = 0.08\n"
        "\t\tlocal_resources_factor = 0.15\n"
        "\t}\n"
        "}\n"
        "unrelated_idea = {\n"
        "\tmodifier = {\n"
        "\t\tpolitical_power_gain = 0.5\n"
        "\t}\n"
        "}\n"
        "}\n"
    )


@pytest.fixture
def populated_mini_repo(
    mini_repo: Path,
    state_a_text: str,
    state_b_text: str,
    country_tst_text: str,
    idea_high_health_text: str,
) -> Path:
    """A tmp repo containing one TST country with two states, one country
    history, and two ideas. Returns the root path."""
    write_text(mini_repo / "history" / "states" / "100-A.txt", state_a_text)
    write_text(mini_repo / "history" / "states" / "200-B.txt", state_b_text)
    write_text(mini_repo / "history" / "countries" / "TST - Test.txt", country_tst_text)
    write_text(
        mini_repo / "common" / "ideas" / "00_test_ideas.txt", idea_high_health_text
    )
    return mini_repo


@pytest.fixture
def import_estimate_gdp(monkeypatch, mini_repo: Path):
    """Import tools.analysis.estimate_gdp with its BASE_DIR/STATES_DIR/COUNTRIES_DIR/
    IDEAS_DIR redirected to the tmp mini_repo. Returns the module."""
    import importlib

    # Pre-insert the repo's tools/ dir so `import estimate_gdp` works without
    # package context (the module lives at tools/analysis/estimate_gdp.py).
    tools_dir = str(REPO_ROOT / "tools" / "analysis")
    monkeypatch.syspath_prepend(tools_dir)
    # Wipe any cached import from earlier tests so a fresh module loads with
    # our monkeypatched constants.
    sys.modules.pop("estimate_gdp", None)
    mod = importlib.import_module("estimate_gdp")
    monkeypatch.setattr(mod, "BASE_DIR", str(mini_repo), raising=False)
    monkeypatch.setattr(
        mod, "STATES_DIR", str(mini_repo / "history" / "states"), raising=False
    )
    monkeypatch.setattr(
        mod, "COUNTRIES_DIR", str(mini_repo / "history" / "countries"), raising=False
    )
    monkeypatch.setattr(
        mod, "IDEAS_DIR", str(mini_repo / "common" / "ideas"), raising=False
    )
    return mod


@pytest.fixture
def import_pre_place(import_estimate_gdp, monkeypatch, mini_repo: Path):
    """Import tools.analysis.pre_place_power_plants with the same redirects as
    estimate_gdp (it re-imports the constants) plus its CSV path."""
    import importlib

    tools_dir = str(REPO_ROOT / "tools" / "analysis")
    monkeypatch.syspath_prepend(tools_dir)
    # Make sure shared_utils is importable too (pre_place reads atomic_write_text).
    monkeypatch.syspath_prepend(str(REPO_ROOT / "tools"))
    sys.modules.pop("pre_place_power_plants", None)
    mod = importlib.import_module("pre_place_power_plants")
    # pre_place reads COMPOSITE_SEED_CSV relative to its own __file__; rewrite
    # it to a tmp file we'll create in each test as needed.
    monkeypatch.setattr(
        mod, "COMPOSITE_SEED_CSV", str(mini_repo / "seeds.csv"), raising=False
    )
    return mod


@pytest.fixture
def import_redistribute(import_estimate_gdp, monkeypatch, mini_repo: Path):
    """Import tools.analysis.redistribute_productivity with STATES_DIR redirected."""
    import importlib

    tools_dir = str(REPO_ROOT / "tools" / "analysis")
    monkeypatch.syspath_prepend(tools_dir)
    sys.modules.pop("redistribute_productivity", None)
    mod = importlib.import_module("redistribute_productivity")
    monkeypatch.setattr(
        mod, "STATES_DIR", str(mini_repo / "history" / "states"), raising=False
    )
    return mod
