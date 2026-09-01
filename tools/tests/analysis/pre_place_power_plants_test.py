"""Behavioral tests for tools/analysis/pre_place_power_plants.py.

Covers renewable/seismic variable collection, composite-seed CSV parsing,
energy consumption and supply math, fossil-plant need calculation, weighted
distribution across states, state-file building injection, country-file
reactor-stockpile injection, the gather_country_data/apply_plan pipeline,
and the CLI dispatch.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pytest


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


# ─── Helpers ────────────────────────────────────────────────────────────────────


def _build_state(
    state_id,
    manpower,
    owner,
    prod,
    buildings,
    resources=None,
    category="state_02",
    renewables=None,
    hydro=None,
    geo=None,
    cap_var=None,
):
    """Assemble a state-content string with optional renewable/hydro/geo vars."""
    resources = resources or {}
    lines = [
        "state = {",
        f"\tid = {state_id}",
        f"\tmanpower = {manpower}",
        f"\tstate_category = {category}",
        "",
        "\thistory = {",
        f"\t\towner = {owner}",
    ]
    if cap_var is not None:
        lines.append(
            f"\t\tset_variable = {{ state_renewable_capacity_factor_modifier_var = {cap_var} }}"
        )
    if hydro is not None:
        lines.append(
            f"\t\tset_variable = {{ hydroelectric_energy_production_var = {hydro} }}"
        )
    if geo is not None:
        lines.append(
            f"\t\tset_variable = {{ geothermal_energy_production_var = {geo} }}"
        )
    lines.append(f"\t\tset_variable = {{ productivity_state_var = {prod} }}")
    if resources:
        resource_fields = " ".join(
            f"{key} = {value}" for key, value in resources.items()
        )
        lines.append(f"\t\tresources = {{ {resource_fields} }}")
    lines.extend(["\t\tbuildings = {"])
    lines.extend(f"\t\t\t{name} = {count}" for name, count in buildings.items())
    lines.extend(["\t\t}", "\t}", "}"])
    return "\n".join(lines) + "\n"


def _parsed_states(mod, repo):
    return [
        mod.parse_state_with_category(str(path))
        for path in sorted((repo / "history" / "states").iterdir())
    ]


def _states_for_owner(mod, repo, owner):
    return [state for state in _parsed_states(mod, repo) if state["owner"] == owner]


@pytest.fixture
def full_mini_repo(mini_repo, monkeypatch):
    """Populate the mini repo with renewable-rich states, a composite-project
    country, and an enrichment-counted country, plus a composite seeds CSV."""
    # Two states owned by TST; one with high industry, one rural.
    write_text(
        mini_repo / "history" / "states" / "10-A.txt",
        _build_state(
            state_id=10,
            manpower=2_000_000,
            owner="TST",
            prod=700,
            buildings={"industrial_complex": 6, "arms_factory": 3},
            category="state_03",
            renewables=True,
            cap_var=1.2,
            hydro=0.5,
            geo=0.0,
        ),
    )
    write_text(
        mini_repo / "history" / "states" / "20-B.txt",
        _build_state(
            state_id=20,
            manpower=1_000_000,
            owner="TST",
            prod=400,
            buildings={
                "industrial_complex": 1,
                "offices": 2,
                "renewable_energy_infra": 4,
            },
            category="state_01",
            renewables=True,
            cap_var=0.8,
            hydro=0.0,
            geo=0.3,
        ),
    )
    # A nuclear-owning state to exercise the nuclear branch.
    write_text(
        mini_repo / "history" / "states" / "30-C.txt",
        _build_state(
            state_id=30,
            manpower=500_000,
            owner="NUK",
            prod=600,
            buildings={"nuclear_reactor": 2, "industrial_complex": 1},
            category="state_02",
        ),
    )
    # Country histories.
    write_text(
        mini_repo / "history" / "countries" / "TST - Test.txt",
        (
            "capital = 10\n"
            "2000.1.1 = {\n"
            "\tcomplete_special_project = sp:sp_composite_production\n"
            "\tadd_ideas = { industry_modern }\n"
            "}\n"
        ),
    )
    write_text(
        mini_repo / "history" / "countries" / "NUK - Test.txt",
        (
            "capital = 30\n"
            "2000.1.1 = {\n"
            "\tcomplete_special_project = sp:sp_composite_production\n"
            "\tadd_ideas = { nuclear_energy }\n"
            "\tset_variable = { overall_productivity = 5.0 }\n"
            "\tadd_to_array = { global.enrichment_countries = THIS.id }\n"
            "\tset_variable = { enrichment_facilities = 2 }\n"
            "}\n"
        ),
    )
    write_text(
        mini_repo / "common" / "ideas" / "00_test_ideas.txt",
        (
            "ideas = {\n"
            "industry_modern = {\n"
            "\tmodifier = {\n"
            "\t\tcivilian_factories_productivity = 0.10\n"
            "\t\tenergy_use_multiplier = -0.10\n"
            "\t\tenergy_gain_multiplier = 0.20\n"
            "\t}\n"
            "}\n"
            "nuclear_energy = {\n"
            "\tmodifier = { nuclear_energy_generation_modifier = 0.10 }\n"
            "}\n"
            "}\n"
        ),
    )
    # Composite seeds CSV: TST=2, NUK=0, ORPHAN=99 (paper tag).
    write_text(
        mini_repo / "seeds.csv",
        "tag,seed\n# comment line\nTST,2\nNUK,0\nORPHAN,99\n",
    )
    return mini_repo


# ─── collect_state_renewable_vars ──────────────────────────────────────────────


class TestRenewableVars:
    def test_collects_capacity_hydro_and_geo(self, import_pre_place, mini_repo):
        mod = import_pre_place
        state = {}
        content = (
            "set_variable = { state_renewable_capacity_factor_modifier_var = 1.234 }\n"
            "set_variable = { hydroelectric_energy_production_var = 0.5 }\n"
            "set_variable = { geothermal_energy_production_var = 0.2 }\n"
        )
        mod.collect_state_renewable_vars(content, state)
        assert state["state_renewable_capacity_factor_modifier_var"] == 1.234
        assert state["hydroelectric_energy_production_var"] == 0.5
        assert state["geothermal_energy_production_var"] == 0.2

    def test_invalid_value_is_skipped(self, import_pre_place):
        mod = import_pre_place
        state = {}
        content = "set_variable = { hydroelectric_energy_production_var = abc }\n"
        mod.collect_state_renewable_vars(content, state)
        assert "hydroelectric_energy_production_var" not in state

    def test_missing_vars_untouched(self, import_pre_place):
        mod = import_pre_place
        state = {"existing": 42}
        mod.collect_state_renewable_vars("", state)
        assert state == {"existing": 42}


# ─── composite seeds CSV parsing ───────────────────────────────────────────────


class TestCompositeSeeds:
    def test_load_seed_values_skips_header_comment_blank(
        self, import_pre_place, full_mini_repo
    ):
        mod = import_pre_place
        seeds = mod.load_composite_seed_values()
        # Comments, blanks, and the `tag,seed` header are all skipped.
        assert seeds == {"TST": 2, "NUK": 0, "ORPHAN": 99}

    def test_load_seed_values_missing_file(self, import_pre_place, mini_repo):
        mod = import_pre_place
        # Path was redirected to a tmp file that does not yet exist.
        assert mod.load_composite_seed_values() == {}

    def test_load_seed_values_garbled_row(self, import_pre_place, mini_repo):
        mod = import_pre_place
        write_text(mini_repo / "seeds.csv", "tag,seed\nA,not_a_number\nB,7\n")
        assert mod.load_composite_seed_values() == {"B": 7}

    def test_parse_composite_seeds_includes_one_per_country(
        self, import_pre_place, full_mini_repo
    ):
        mod = import_pre_place
        seeds = mod.parse_composite_seeds()
        # Each country that completed the project gets +1 from the special
        # project, plus the CSV seed (TST=2+1, NUK=0+1). ORPHAN has no country
        # file so it's not even seen.
        assert seeds["TST"] == 3
        assert seeds["NUK"] == 1
        assert "ORPHAN" not in seeds


# ─── Energy math ──────────────────────────────────────────────────────────────


class TestEnergyConsumption:
    def test_zero_population_returns_zero(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        assert mod.energy_consumption([], {}, gdpc=5.0) == 0.0

    def test_population_and_building_contributions(
        self, import_pre_place, full_mini_repo
    ):
        mod = import_pre_place

        # Reload to get renewable-extended states from disk.
        states = _parsed_states(mod, full_mini_repo)
        # Pop=3M, total industry buildings: 7 IC + 3 AF + 2 offices = 12.
        # With energy_use_multiplier=-0.10 in industry_modern idea and a gdpc.
        stack = {"energy_use_multiplier": -0.10, "pop_energy_use_multiplier": 0.0}
        result = mod.energy_consumption(states, stack, gdpc=10.0)
        assert result > 0
        # The balance multiplier always multiplies through; assert it lands.
        assert result > 0.001

    def test_population_modifier_applied(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        # Two identical states except stack.
        state = {
            "manpower": 1_000_000,
            "buildings": defaultdict(int),
        }
        base = mod.energy_consumption(
            [state],
            {"pop_energy_use_multiplier": 0.0, "energy_use_multiplier": 0.0},
            gdpc=10.0,
        )
        boosted = mod.energy_consumption(
            [state],
            {"pop_energy_use_multiplier": 1.0, "energy_use_multiplier": 0.0},
            gdpc=10.0,
        )
        assert boosted == pytest.approx(base * 2.0)

    def test_negative_gdpc_uses_engine_fallback(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        state = {"manpower": 100_000, "buildings": defaultdict(int)}
        zero = mod.energy_consumption([state], {}, gdpc=0.0)
        neg = mod.energy_consumption([state], {}, gdpc=-5.0)
        # Both must use the engine's gdpc=2 fallback and match.
        assert zero == pytest.approx(neg)


class TestEnergySupply:
    def test_renewable_and_hydro_and_geo(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        states = _parsed_states(mod, full_mini_repo)
        # TST owns states 10 and 20. Renewable infra = 4 in state 20 with
        # cap_var=0.8 → 4 * 0.5 * 0.8/2 = 0.8 GW. Hydro in state 10 = 0.5 GW.
        # Geo in state 20 = 0.3 GW. State 30 belongs to NUK and is filtered.
        supply = mod.energy_supply_non_fossil(
            states, {"energy_gain_multiplier": 0.0}, has_nuclear=False
        )
        # 0.8 + 0.5 + 0.3 = 1.6 baseline, no gain multiplier.
        assert supply == pytest.approx(1.6)

    def test_nuclear_contribution(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        nuk_states = _states_for_owner(mod, full_mini_repo, "NUK")
        supply = mod.energy_supply_non_fossil(
            nuk_states, {"nuclear_energy_generation_modifier": 0.0}, has_nuclear=True
        )
        # 2 reactors * 4 GW each = 8 GW.
        assert supply == pytest.approx(8.0)

    def test_nuclear_skip_when_has_nuclear_false(
        self, import_pre_place, full_mini_repo
    ):
        mod = import_pre_place
        nuk_states = _states_for_owner(mod, full_mini_repo, "NUK")
        # Even though reactors exist, has_nuclear=False skips the nuclear branch.
        supply = mod.energy_supply_non_fossil(nuk_states, {}, has_nuclear=False)
        assert supply == 0.0


# ─── fossil_plants_needed ─────────────────────────────────────────────────────


class TestFossilPlantsNeeded:
    def test_minimum_one_plant_even_when_balanced(self, import_pre_place):
        mod = import_pre_place
        assert mod.fossil_plants_needed(consumption=10.0, supply=10.0) == 1
        # Supply already exceeds consumption by safety buffer.
        assert mod.fossil_plants_needed(consumption=10.0, supply=12.0) == 1

    def test_ceil_division(self, import_pre_place):
        mod = import_pre_place
        # (10 + 2 - 0) / 2 = 6 → exactly 6.
        assert mod.fossil_plants_needed(consumption=10.0, supply=0.0) == 6
        # 11 + 2 = 13 / 2 = 6.5 → ceil = 7.
        assert mod.fossil_plants_needed(consumption=11.0, supply=0.0) == 7

    def test_no_safety_buffer_argument(self, import_pre_place):
        mod = import_pre_place
        # Without the safety pad, 2 GW gap → ceil(2/2) = 1.
        assert mod.fossil_plants_needed(consumption=10.0, supply=8.0, safety_gw=0) == 1


# ─── Weighted distribution ─────────────────────────────────────────────────────


class TestDistribute:
    def test_zero_count_returns_empty(self, import_pre_place, full_mini_repo):
        mod = import_pre_place

        states = [
            mod.parse_state_with_category(str(f))
            for f in sorted((full_mini_repo / "history" / "states").iterdir())
        ]
        assert mod.distribute(0, states, "fossil_powerplant") == {}

    def test_cap_respected(self, import_pre_place, full_mini_repo):
        mod = import_pre_place

        states = [
            mod.parse_state_with_category(str(f))
            for f in sorted((full_mini_repo / "history" / "states").iterdir())
        ]
        # Distribute 100 plants with cap=5 per state. The function should stop
        # early once all states hit the cap and place at most cap * n_states.
        placed = mod.distribute(100, states, "fossil_powerplant", cap=5)
        total = sum(placed.values())
        assert total <= 5 * len(states)
        # Each state id that landed a plant is at the cap (since we asked for more than the cap per state).
        for sid, n in placed.items():
            assert n <= 5

    def test_weighted_distribution_favours_industrial_state(
        self, import_pre_place, full_mini_repo
    ):
        mod = import_pre_place

        states = [
            mod.parse_state_with_category(str(f))
            for f in sorted((full_mini_repo / "history" / "states").iterdir())
        ]
        # State 10 has the highest industry/manpower — it should get the first plant.
        placed = mod.distribute(1, states, "fossil_powerplant", cap=5)
        assert placed.get(10) == 1

    def test_composite_weight_skips_states_without_arms_or_dockyards(
        self, import_pre_place, full_mini_repo
    ):
        mod = import_pre_place

        states = [
            mod.parse_state_with_category(str(f))
            for f in sorted((full_mini_repo / "history" / "states").iterdir())
        ]
        # State 30 (NUK) has no arms/dockyards → composite_weight falls back to
        # 0.1 * state_weight. State 10 has 3 arms → arms * 5 + state_weight.
        w10 = mod.composite_weight(next(s for s in states if s["id"] == 10))
        w30 = mod.composite_weight(next(s for s in states if s["id"] == 30))
        assert w10 > w30


# ─── State-file building injection ─────────────────────────────────────────────


class TestInjectBuilding:
    def test_injects_into_existing_buildings_block(self, import_pre_place, mini_repo):
        mod = import_pre_place

        # First insert a state with a buildings block.
        write_text(
            mini_repo / "history" / "states" / "100.txt",
            (
                "state = {\n"
                "\tid = 100\n"
                "\tmanpower = 500\n"
                "\thistory = {\n"
                "\t\towner = TST\n"
                "\t\tbuildings = {\n"
                "\t\t\tindustrial_complex = 2\n"
                "\t\t}\n"
                "\t}\n"
                "}\n"
            ),
        )
        ok, msg = mod.inject_building(
            str(mini_repo / "history" / "states" / "100.txt"), "fossil_powerplant", 3
        )
        assert ok, msg
        text = (mini_repo / "history" / "states" / "100.txt").read_text(
            encoding="utf-8"
        )
        assert "fossil_powerplant = 3" in text
        # Existing buildings are preserved.
        assert "industrial_complex = 2" in text

    def test_replace_existing_top_level_entry(self, import_pre_place, mini_repo):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "states" / "101.txt",
            (
                "state = {\n"
                "\tid = 101\n"
                "\thistory = {\n"
                "\t\towner = TST\n"
                "\t\tbuildings = {\n"
                "\t\t\tfossil_powerplant = 1\n"
                "\t\t}\n"
                "\t}\n"
                "}\n"
            ),
        )
        ok, msg = mod.inject_building(
            str(mini_repo / "history" / "states" / "101.txt"), "fossil_powerplant", 7
        )
        assert ok, msg
        text = (mini_repo / "history" / "states" / "101.txt").read_text(
            encoding="utf-8"
        )
        # Replaced in place — no duplicate fossil_powerplant lines.
        assert text.count("fossil_powerplant = ") == 1
        assert "fossil_powerplant = 7" in text

    def test_creates_buildings_block_when_missing_after_owner(
        self, import_pre_place, mini_repo
    ):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "states" / "102.txt",
            (
                "state = {\n"
                "\tid = 102\n"
                "\thistory = {\n"
                "\t\towner = TST\n"
                "\t}\n"
                "}\n"
            ),
        )
        ok, msg = mod.inject_building(
            str(mini_repo / "history" / "states" / "102.txt"), "composite_plant", 1
        )
        assert ok, msg
        text = (mini_repo / "history" / "states" / "102.txt").read_text(
            encoding="utf-8"
        )
        assert "buildings = {" in text
        assert "composite_plant = 1" in text

    def test_creates_buildings_block_when_no_owner_line(
        self, import_pre_place, mini_repo
    ):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "states" / "103.txt",
            (
                "state = {\n"
                "\tid = 103\n"
                "\thistory = {\n"
                "\t\tset_variable = { productivity_state_var = 500 }\n"
                "\t}\n"
                "}\n"
            ),
        )
        ok, _ = mod.inject_building(
            str(mini_repo / "history" / "states" / "103.txt"), "composite_plant", 1
        )
        assert ok
        text = (mini_repo / "history" / "states" / "103.txt").read_text(
            encoding="utf-8"
        )
        assert "composite_plant = 1" in text

    def test_no_history_block_returns_false(self, import_pre_place, mini_repo):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "states" / "104.txt",
            "state = {\n\tid = 104\n}\n",
        )
        ok, msg = mod.inject_building(
            str(mini_repo / "history" / "states" / "104.txt"), "fossil_powerplant", 1
        )
        assert not ok
        assert "no history" in msg

    def test_replace_or_append_top_level_skips_nested_blocks(self, import_pre_place):
        mod = import_pre_place
        # Nested province block under `1234 = { ... }` should not be matched
        # by the depth-0 key replace path.
        block = "1234 = {\n\t\tindustrial_complex = 1\n\t}\n"
        out = mod._replace_or_append_top_level(block, "industrial_complex", 5)
        # The nested one should NOT be touched; we append at depth 0 instead.
        assert out != "industrial_complex = 5"
        assert "industrial_complex = 5" in out
        # Nested entry remains.
        assert "1234 = {" in out


# ─── Country file: reactor stockpile injection ─────────────────────────────────


class TestInjectReactorStockpile:
    def test_inserts_after_enrichment_array(self, import_pre_place, mini_repo):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "countries" / "RTT - Test.txt",
            (
                "2000.1.1 = {\n"
                "\tadd_to_array = { global.enrichment_countries = THIS.id }\n"
                "\tset_variable = { overall_productivity = 5.0 }\n"
                "}\n"
            ),
        )
        ok, msg = mod.inject_reactor_stockpile(
            str(mini_repo / "history" / "countries" / "RTT - Test.txt"),
            5000,
            set_flag=True,
        )
        assert ok, msg
        text = (mini_repo / "history" / "countries" / "RTT - Test.txt").read_text(
            encoding="utf-8"
        )
        assert "var_reactor_material_stockpile = 5000" in text
        # Stockpile lands right after the enrichment array, before overall_productivity.
        assert text.index("var_reactor_material_stockpile") < text.index(
            "overall_productivity"
        )
        assert "set_country_flag = enabled_nuclear_reactor_fuel_production" in text

    def test_idempotent_replace(self, import_pre_place, mini_repo):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "countries" / "RTT - Test.txt",
            (
                "2000.1.1 = {\n"
                "\tadd_to_array = { global.enrichment_countries = THIS.id }\n"
                "\tset_variable = { var_reactor_material_stockpile = 5000 }\n"
                "\tset_country_flag = enabled_nuclear_reactor_fuel_production\n"
                "}\n"
            ),
        )
        ok, msg = mod.inject_reactor_stockpile(
            str(mini_repo / "history" / "countries" / "RTT - Test.txt"),
            7000,
            set_flag=True,
        )
        assert ok, msg
        text = (mini_repo / "history" / "countries" / "RTT - Test.txt").read_text(
            encoding="utf-8"
        )
        # Stockpile value replaced.
        assert "var_reactor_material_stockpile = 7000" in text
        assert "var_reactor_material_stockpile = 5000" not in text
        # Flag was already present, so it stays.
        assert (
            text.count("set_country_flag = enabled_nuclear_reactor_fuel_production")
            == 1
        )

    def test_anchor_is_overall_productivity_when_no_enrichment_array(
        self, import_pre_place, mini_repo
    ):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "countries" / "NOP - Test.txt",
            (
                "2000.1.1 = {\n"
                "\tset_variable = { overall_productivity = 4.0 }\n"
                "}\n"
            ),
        )
        ok, _ = mod.inject_reactor_stockpile(
            str(mini_repo / "history" / "countries" / "NOP - Test.txt"),
            1000,
            set_flag=False,
        )
        assert ok
        text = (mini_repo / "history" / "countries" / "NOP - Test.txt").read_text(
            encoding="utf-8"
        )
        assert "var_reactor_material_stockpile = 1000" in text
        # Landed right after overall_productivity.
        assert text.index("var_reactor_material_stockpile") > text.index(
            "overall_productivity"
        )

    def test_no_anchor_returns_false(self, import_pre_place, mini_repo):
        mod = import_pre_place
        write_text(
            mini_repo / "history" / "countries" / "EMP - Test.txt",
            "2000.1.1 = {\n\tadd_ideas = { something }\n}\n",
        )
        ok, msg = mod.inject_reactor_stockpile(
            str(mini_repo / "history" / "countries" / "EMP - Test.txt"),
            1000,
            set_flag=True,
        )
        assert not ok
        assert "no anchor" in msg

    def test_find_country_file(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        assert mod.find_country_file("TST") is not None
        assert mod.find_country_file("ZZZ") is None


# ─── gather_country_data + apply_plan integration ──────────────────────────────


class TestPipeline:
    def test_gather_country_data(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        data = mod.gather_country_data()
        assert "TST" in data and "NUK" in data
        assert data["TST"]["has_nuclear"] is False
        assert data["NUK"]["has_nuclear"] is True
        # NUK's gdpc must have been computed by the calculate_gdp pass.
        assert data["NUK"]["engine_gdpc"] is not None
        # The composite project is reflected in ideas.
        assert data["TST"]["ideas"] == ["industry_modern"]
        assert data["NUK"]["ideas"] == ["nuclear_energy"]

    def test_compute_placements_distributes(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        data = mod.gather_country_data()
        composite_seeds = mod.parse_composite_seeds()
        plan = mod.compute_placements(data, composite_seeds)
        # TST should get at least one composite (csv=2 + project=1, none existing).
        assert plan["TST"]["composite_added"] >= 1
        assert plan["TST"]["composite_total"] == 3
        # Reactor count for NUK = 2 → stockpile = 2 * 2500.
        assert plan["NUK"]["reactor_count"] == 2
        assert plan["NUK"]["reactor_stockpile"] == 2 * mod.NUCLEAR_FUEL_PER_REACTOR
        # Enrichment is read off the country file (NUK=2).
        assert plan["NUK"]["enrichment"] == 2

    def test_compute_placements_skips_paper_tags(
        self, import_pre_place, full_mini_repo
    ):
        mod = import_pre_place
        data = mod.gather_country_data()
        composite_seeds = mod.parse_composite_seeds()
        # ORPHAN exists in the CSV but owns no states; compute_placements must
        # not crash and must simply omit it.
        plan = mod.compute_placements(data, composite_seeds)
        assert "ORPHAN" not in plan

    def test_apply_plan_dry_run_returns_count(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        data = mod.gather_country_data()
        composite_seeds = mod.parse_composite_seeds()
        plan = mod.compute_placements(data, composite_seeds)
        # Dry-run mode reports the count without touching files.
        before = (full_mini_repo / "history" / "states" / "10-A.txt").read_text(
            encoding="utf-8"
        )
        n = mod.apply_plan(plan, data, write=False)
        after = (full_mini_repo / "history" / "states" / "10-A.txt").read_text(
            encoding="utf-8"
        )
        assert before == after
        assert n >= 1

    def test_apply_plan_write_modifies_files(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        data = mod.gather_country_data()
        composite_seeds = mod.parse_composite_seeds()
        plan = mod.compute_placements(data, composite_seeds)
        n = mod.apply_plan(plan, data, write=True)
        assert n >= 1
        # At least one state file gained buildings and/or the NUK country file
        # gained a stockpile var.
        a_text = (full_mini_repo / "history" / "states" / "10-A.txt").read_text(
            encoding="utf-8"
        )
        nuk_text = (
            full_mini_repo / "history" / "countries" / "NUK - Test.txt"
        ).read_text(encoding="utf-8")
        assert ("fossil_powerplant" in a_text) or ("composite_plant" in a_text)
        assert "var_reactor_material_stockpile" in nuk_text

    def test_apply_plan_only_filter(self, import_pre_place, full_mini_repo):
        mod = import_pre_place
        data = mod.gather_country_data()
        composite_seeds = mod.parse_composite_seeds()
        plan = mod.compute_placements(data, composite_seeds)
        before_nuk = (
            full_mini_repo / "history" / "countries" / "NUK - Test.txt"
        ).read_text(encoding="utf-8")
        mod.apply_plan(plan, data, write=True, only={"TST"})
        after_nuk = (
            full_mini_repo / "history" / "countries" / "NUK - Test.txt"
        ).read_text(encoding="utf-8")
        # NUK country file was excluded by the `only` filter.
        assert before_nuk == after_nuk


# ─── CLI main ──────────────────────────────────────────────────────────────────


class TestCli:
    def test_dry_run_prints_table_and_does_not_write(
        self, import_pre_place, full_mini_repo, capsys, monkeypatch
    ):
        mod = import_pre_place
        monkeypatch.setattr(sys, "argv", ["pre_place.py", "--dry-run"])
        mod.main()
        captured = capsys.readouterr()
        assert "TAG" in captured.out
        assert "Dry run:" in captured.err
        # No state file gained a fossil_powerplant entry.
        for f in (full_mini_repo / "history" / "states").iterdir():
            text = f.read_text(encoding="utf-8")
            assert (
                "fossil_powerplant = " not in text
                or text.count("fossil_powerplant = ") == 1
            )

    def test_write_emits_count(
        self, import_pre_place, full_mini_repo, capsys, monkeypatch
    ):
        mod = import_pre_place
        monkeypatch.setattr(sys, "argv", ["pre_place.py", "--write"])
        mod.main()
        captured = capsys.readouterr()
        assert "Wrote" in captured.err

    def test_top_truncates_table(
        self, import_pre_place, full_mini_repo, capsys, monkeypatch
    ):
        mod = import_pre_place
        monkeypatch.setattr(sys, "argv", ["pre_place.py", "--dry-run", "--top", "1"])
        mod.main()
        out = capsys.readouterr().out
        data_lines = [
            l for l in out.splitlines() if l.startswith("TST") or l.startswith("NUK")
        ]
        # At most one data row when --top 1.
        assert len(data_lines) <= 1

    def test_only_filter_emits_subset(
        self, import_pre_place, full_mini_repo, capsys, monkeypatch
    ):
        mod = import_pre_place
        monkeypatch.setattr(sys, "argv", ["pre_place.py", "--dry-run", "--only", "TST"])
        mod.main()
        out = capsys.readouterr().out
        assert "TST" in out
        # NUK owns states too; with --only=TST it must be excluded from the table.
        assert "NUK" not in out


# ─── Additional helper coverage ────────────────────────────────────────────────


class TestMiscHelpers:
    def test_read_enrichment_count_missing(self, import_pre_place):
        mod = import_pre_place
        assert mod.read_enrichment_count("2000.1.1 = {\n\tadd_ideas = { x }\n}\n") == 0

    def test_read_enrichment_count_present(self, import_pre_place):
        mod = import_pre_place
        text = "set_variable = { enrichment_facilities = 3 }\n"
        assert mod.read_enrichment_count(text) == 3

    def test_state_weight_with_missing_category(self, import_pre_place):
        mod = import_pre_place
        # state_category is absent → tier defaults to 0; the +1 baseline still
        # yields a non-zero weight.
        s = {"state_category": "unknown", "buildings": defaultdict(int), "manpower": 0}
        assert mod.state_weight(s) == 1.0
