"""Behavioral tests for tools/analysis/gdp_seeds.py on the synthetic mini_repo."""

from __future__ import annotations

from pathlib import Path

import pytest


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def country_path(repo: Path) -> Path:
    return repo / "history" / "countries" / "TST - Test.txt"


def write_country(repo: Path, seeds: str, newline: str = "\n") -> Path:
    path = country_path(repo)
    lines = [
        "capital = 100",
        "2000.1.1 = {",
        "\tadd_ideas = {",
        "\t\thealth_06",
        "\t}",
        *seeds.splitlines(),
        "}",
    ]
    write_text(path, newline.join(lines) + newline)
    return path


POP_WEIGHTED = round((700 * 1.5 + 500 * 0.8) / 2.3)


class TestSuggestions:
    def test_productivity_is_pop_weighted_state_mean(
        self, import_gdp_seeds, populated_mini_repo
    ):
        mod = import_gdp_seeds
        by_owner = mod.load_states_by_owner()
        idea_db = mod.estimate_gdp.parse_all_ideas()
        suggestion = mod.suggest_seeds("TST", by_owner["TST"], idea_db)
        assert suggestion["overall_productivity"] == POP_WEIGHTED

    def test_gdp_per_capita_is_the_converged_value(
        self, import_gdp_seeds, populated_mini_repo
    ):
        mod = import_gdp_seeds
        write_country(populated_mini_repo, "\tset_variable = { gdp_per_capita = 1 }")
        states = mod.load_states_by_owner()["TST"]
        suggestion = mod.suggest_seeds("TST", states, {})
        result = mod.estimate_gdp.compute_country_gdp("TST", states, {})
        mod.estimate_gdp.finalize_gdp(result, "health_06", suggestion["gdp_per_capita"])
        assert result["gdp_per_capita"] == pytest.approx(
            suggestion["gdp_per_capita"], abs=0.002
        )

    def test_paths_map_to_tags(self, import_gdp_seeds, populated_mini_repo):
        mod = import_gdp_seeds
        targets = [
            str(populated_mini_repo / "history" / "states" / "100-A.txt"),
            "history/countries/TST - Test.txt",
            "abc",
            "common/ideas/00_test_ideas.txt",
        ]
        assert mod.tags_from_targets(targets) == ["TST", "ABC"]


class TestCli:
    def test_check_reports_and_never_writes(
        self, import_gdp_seeds, populated_mini_repo, capsys
    ):
        mod = import_gdp_seeds
        path = write_country(
            populated_mini_repo,
            "\tset_variable = { gdp_per_capita = 1.000 }\n"
            "\tset_variable = { overall_productivity = 900 }",
        )
        before = read_text(path)
        state = populated_mini_repo / "history" / "states" / "100-A.txt"
        assert mod.main([str(state)]) == 0
        out = capsys.readouterr().out
        assert "TST" in out and "--write TST" in out
        assert read_text(path) == before

    def test_write_rewrites_only_seed_lines_and_keeps_crlf(
        self, import_gdp_seeds, populated_mini_repo
    ):
        mod = import_gdp_seeds
        path = write_country(
            populated_mini_repo,
            "\tset_variable = { gdp_per_capita = 1.000 }\n"
            "\tset_variable = { var = overall_productivity value = 900 }",
            newline="\r\n",
        )
        assert mod.main(["--write", "TST"]) == 0
        content = read_text(path)
        assert content.count("\r\n") == content.count("\n")
        assert f"{{ var = overall_productivity value = {POP_WEIGHTED} }}" in content
        assert "gdp_per_capita = 1.000" not in content
        assert "\t\thealth_06\r\n" in content

    def test_write_rejects_paths(self, import_gdp_seeds, populated_mini_repo):
        mod = import_gdp_seeds
        state = populated_mini_repo / "history" / "states" / "100-A.txt"
        assert mod.main(["--write", str(state)]) == 2
        assert mod.main(["--write"]) == 2

    def test_duplicate_seed_lines_are_reported_not_written(
        self, import_gdp_seeds, populated_mini_repo, capsys
    ):
        mod = import_gdp_seeds
        path = write_country(
            populated_mini_repo,
            "\tset_variable = { gdp_per_capita = 1.000 }\n"
            "\tset_variable = { gdp_per_capita = 2.000 }\n"
            "\tset_variable = { overall_productivity = 900 }",
        )
        assert mod.main(["--write", "TST"]) == 0
        content = read_text(path)
        assert "gdp_per_capita = 1.000" in content
        assert "gdp_per_capita = 2.000" in content
        assert f"overall_productivity = {POP_WEIGHTED}" in content
        assert "gdp_per_capita: 2 seed lines, not written" in capsys.readouterr().out

    def test_missing_seed_line_is_not_added(
        self, import_gdp_seeds, populated_mini_repo
    ):
        mod = import_gdp_seeds
        path = write_country(populated_mini_repo, "")
        before = read_text(path)
        assert mod.main(["--write", "TST"]) == 0
        assert read_text(path) == before
