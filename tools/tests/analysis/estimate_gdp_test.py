"""Behavioral tests for tools/analysis/estimate_gdp.py.

Exercises the tokenizer, idea parser, country-history parser, state-file
parser, modifier stack builder, GDP calculation, finalize step, and the CLI
dispatch paths (--top, --all, explicit tags, error exits). All on-disk
fixtures live in a synthetic mini_repo so the production module reads and
parses real text — no mocks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def write_text(path: Path, content: str) -> None:
    """LF-only text write — mirrors the discipline in conftest.py."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def _parsed_states(mod, repo):
    states_dir = repo / "history" / "states"
    return [
        mod.parse_state_file_from_content(
            (states_dir / name).read_text(encoding="utf-8"), name
        )
        for name in ("100-A.txt", "200-B.txt")
    ]


class TestTokenizerAndIdeaParser:
    """Token parsing + idea modifier extraction (comments, strings, nested blocks)."""

    def test_tokenize_handles_strings_and_braces(self, import_estimate_gdp):
        mod = import_estimate_gdp
        toks = mod._tokenize('a = "b c" d = { e = 1 }')
        kinds = [t[0] for t in toks]
        assert kinds == [
            "WORD",
            "EQ",
            "STR",
            "WORD",
            "EQ",
            "OPEN",
            "WORD",
            "EQ",
            "WORD",
            "CLOSE",
        ]
        # The string token keeps the contents but no quotes.
        assert toks[2] == ("STR", "b c")

    def test_extract_ideas_skips_comments_and_unrelated_modifiers(
        self, import_estimate_gdp
    ):
        mod = import_estimate_gdp
        content = (
            "ideas = {\n"
            "  # a leading comment\n"
            "  my_idea = {\n"
            "    modifier = { civilian_factories_productivity = 0.20 }\n"
            "  }\n"
            "  other = {\n"
            "    modifier = { political_power_gain = 0.10 }\n"  # not in GDP_MODIFIER_KEYS
            "  }\n"
            "}\n"
        )
        out = {}
        mod._extract_ideas_from_content(content, out)
        # Only the GDP-relevant modifier survives; the political_power_gain is dropped.
        assert out == {"my_idea": {"civilian_factories_productivity": 0.20}}

    def test_extract_ideas_sums_duplicate_keys_across_blocks(self, import_estimate_gdp):
        mod = import_estimate_gdp
        content = (
            "ideas = {\n"
            "  dual = {\n"
            "    modifier = { civilian_factories_productivity = 0.10 }\n"
            "  }\n"
            "  dual = {\n"
            "    modifier = { civilian_factories_productivity = 0.05 }\n"
            "  }\n"
            "}\n"
        )
        out = {}
        mod._extract_ideas_from_content(content, out)
        # Two sibling definitions for the same idea accumulate.
        assert out["dual"]["civilian_factories_productivity"] == pytest.approx(0.15)

    def test_parse_idea_tokens_records_depth_zero_parent(self, import_estimate_gdp):
        mod = import_estimate_gdp
        # A `modifier = { ... }` block whose key sits at the top level of the
        # ideas file uses the file's outer context_stack parent as its idea
        # name — and depth-zero modifier blocks at the top of `ideas = { ... }`
        # are recorded under that parent ("ideas" in this case).
        content = (
            "ideas = {\n"
            "  only = {\n"
            "    modifier = { civilian_factories_productivity = 0.20 }\n"
            "  }\n"
            "  modifier = { civilian_factories_productivity = 0.99 }\n"
            "}\n"
        )
        out = {}
        mod._extract_ideas_from_content(content, out)
        assert out["only"]["civilian_factories_productivity"] == pytest.approx(0.20)
        # depth-0 modifier lands under the top-level context name.
        assert out["ideas"]["civilian_factories_productivity"] == pytest.approx(0.99)

    def test_parse_all_ideas_skips_non_txt_and_unreadable(
        self, import_estimate_gdp, mini_repo
    ):
        mod = import_estimate_gdp
        # .DS_Store is not a .txt and must be skipped, not crash.
        (mini_repo / "common" / "ideas" / ".DS_Store").write_bytes(b"\x00\x01")
        # A real .txt file with a known-good idea still parses.
        (mini_repo / "common" / "ideas" / "ideas.txt").write_text(
            "ideas = { one = { modifier = { total_workforce_modifier = 0.5 } } }\n",
            encoding="utf-8",
        )
        db = mod.parse_all_ideas()
        assert "one" in db
        assert db["one"]["total_workforce_modifier"] == 0.5


class TestCountryHistoryParser:
    """parse_country_history: tag dispatch, ideas list, seeded gdpc, capital."""

    def test_extracts_ideas_and_capital(self, import_estimate_gdp, populated_mini_repo):
        mod = import_estimate_gdp
        info = mod.parse_country_history("TST")
        assert info["ideas"] == ["high_health", "industry_modern"]
        assert info["capital"] == 100
        assert info["seeded_gdpc"] == 12.5

    def test_dynamic_resource_extraction_vars_are_captured(
        self, import_estimate_gdp, mini_repo
    ):
        mod = import_estimate_gdp

        body = (
            "capital = 5\n"
            "2000.1.1 = {\n"
            "  set_variable = { oil_resource_extraction_modifier = 0.10 }\n"
            "  set_variable = { steel_resource_extraction_factor = -0.05 }\n"
            "  set_variable = { unrelated_var = 9 }\n"  # ignored
            "  set_variable = { gdp_per_capita = 7.0 }\n"
            "}\n"
        )
        write_text(mini_repo / "history" / "countries" / "DYN - Test.txt", body)
        info = mod.parse_country_history("DYN")
        assert info["seeded_gdpc"] == 7.0
        # The regex matches `*resource_extraction*` so both names land in the dict.
        assert info["dynamic_resource_vars"][
            "oil_resource_extraction_modifier"
        ] == pytest.approx(0.10)
        assert info["dynamic_resource_vars"][
            "steel_resource_extraction_factor"
        ] == pytest.approx(-0.05)
        assert "unrelated_var" not in info["dynamic_resource_vars"]

    def test_unknown_tag_returns_empty(self, import_estimate_gdp, populated_mini_repo):
        mod = import_estimate_gdp
        info = mod.parse_country_history("ZZZ")
        assert info == {
            "ideas": [],
            "seeded_gdpc": None,
            "dynamic_resource_vars": {},
            "capital": None,
        }


class TestStateParser:
    """parse_state_file_from_content: id, manpower, productivity, owner,
    resources, and history.buildings traversal."""

    def test_extracts_id_owner_manpower_and_productivity(self, import_estimate_gdp):
        mod = import_estimate_gdp
        content = (
            "state = {\n"
            "  id = 42\n"
            "  manpower = 100\n"
            "  owner = TST\n"
            "  history = { set_variable = { productivity_state_var = 1234 } }\n"
            "}\n"
        )
        s = mod.parse_state_file_from_content(content, "fake.txt")
        assert s["id"] == 42
        assert s["manpower"] == 100
        assert s["owner"] == "TST"
        assert s["productivity"] == 1234

    def test_resources_block_parses_known_types_only(self, import_estimate_gdp):
        mod = import_estimate_gdp
        content = (
            "state = {\n"
            "  id = 1\n"
            "  owner = TST\n"
            "  history = {\n"
            "    resources = { steel = 4.5 oil = 1.0 magic = 99.0 }\n"
            "  }\n"
            "}\n"
        )
        s = mod.parse_state_file_from_content(content, "x.txt")
        assert s["resources"]["steel"] == 4.5
        assert s["resources"]["oil"] == 1.0
        assert "magic" not in s["resources"]

    def test_buildings_block_counts_top_level_keys(self, import_estimate_gdp):
        mod = import_estimate_gdp
        # The state has both a top-level `industrial_complex` (counted) and a
        # province-nested block (NOT counted as a state-level building).
        content = (
            "state = {\n"
            "  id = 7\n"
            "  owner = TST\n"
            "  history = {\n"
            "    buildings = {\n"
            "      industrial_complex = 3\n"
            "      arms_factory = 1\n"
            "      infrastructure = 2\n"
            "      1234 = {\n"
            "        naval_base = 1\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        s = mod.parse_state_file_from_content(content, "x.txt")
        assert s["buildings"]["industrial_complex"] == 3
        assert s["buildings"]["arms_factory"] == 1
        assert s["buildings"]["infrastructure"] == 2
        # Nested province blocks must not pollute the top-level count.
        assert "naval_base" not in s["buildings"]

    def test_state_file_io_roundtrip(self, import_estimate_gdp, mini_repo):
        mod = import_estimate_gdp

        write_text(
            mini_repo / "history" / "states" / "round.txt",
            "state = {\nid = 9\nowner = TST\nmanpower = 11\n}\n",
        )
        s = mod.parse_state_file(str(mini_repo / "history" / "states" / "round.txt"))
        assert s["id"] == 9
        assert s["owner"] == "TST"
        assert s["manpower"] == 11


class TestModifierStackAndGdp:
    """build_modifier_stack + calculate_gdp + finalize_gdp."""

    def test_build_modifier_stack_sums_all_ideas(self, import_estimate_gdp):
        mod = import_estimate_gdp
        idea_db = {
            "a": {"civilian_factories_productivity": 0.10},
            "b": {
                "civilian_factories_productivity": 0.05,
                "local_resources_factor": 0.20,
            },
            "missing": {"civilian_factories_productivity": 0.99},  # unused
        }
        stack = mod.build_modifier_stack(["a", "b"], idea_db)
        assert stack["civilian_factories_productivity"] == pytest.approx(0.15)
        assert stack["local_resources_factor"] == pytest.approx(0.20)
        # Missing ideas contribute nothing — the dict is keyed only by what was hit.
        assert "missing" not in stack

    def test_calculate_gdp_returns_none_when_no_population(self, import_estimate_gdp):
        mod = import_estimate_gdp
        assert mod.calculate_gdp([]) is None
        assert mod.calculate_gdp([{"manpower": 0}]) is None

    def test_calculate_gdp_realistic_two_state_country(
        self, import_estimate_gdp, populated_mini_repo
    ):
        mod = import_estimate_gdp
        result = mod.calculate_gdp(_parsed_states(mod, populated_mini_repo))
        assert result is not None
        # population = 1.5M + 0.8M = 2.3M
        assert result["population"] == 2_300_000
        assert result["population_m"] == pytest.approx(2.3)
        # Pop-weighted productivity = (700*1.5 + 500*0.8)/2.3
        assert result["overall_productivity"] == pytest.approx(
            (700 * 1.5 + 500 * 0.8) / 2.3, rel=1e-3
        )
        # Building GDP: industrial_complex (17.5 each, no mod bonus) + arms_factory (1.5 each) + offices (50*3)
        assert result["buildings"]["industrial_complex"] == 6  # 4 + 2
        assert result["buildings"]["arms_factory"] == 2
        assert result["buildings"]["offices"] == 3
        assert result["gdp_from_buildings"] > 0
        # Resource GDP: steel 4 * 1.0 (no per-resource factor) + oil 6 * 1.0 + aluminium 2 * 1.0 = 12
        # Multiplied by RESOURCE_GDP_COEFF = 0.5 → 6.0
        assert result["total_resources"] == pytest.approx(12.0)
        assert result["gdp_from_resources"] == pytest.approx(6.0)
        assert result["num_states"] == 2

    def test_finalize_gdp_applies_productivity_mult_and_healthcare(
        self, import_estimate_gdp, populated_mini_repo
    ):
        mod = import_estimate_gdp
        result = mod.calculate_gdp(_parsed_states(mod, populated_mini_repo))
        # The high_health idea has no GDP modifier by itself; finalize uses
        # HEALTH_GDP_MULT["health_XX"] — but our test idea is named "high_health"
        # not "health_01..06", so health_idea defaults to None.
        mod.finalize_gdp(result, health_idea=None, seeded_gdpc=None)
        # No healthcare: gdp_total == gdp_pre_healthcare * productivity_mult.
        assert result["gdp_total"] == pytest.approx(
            result["gdp_pre_healthcare"] * result["productivity_mult"]
        )
        # Scaled fields mirror unscaled values times productivity_mult.
        assert result["gdp_from_buildings_scaled"] == pytest.approx(
            result["gdp_from_buildings"] * result["productivity_mult"]
        )
        # No healthcare contribution.
        assert result["gdp_from_healthcare"] == 0.0
        # Floor on gdp_total prevents negative or zero values.
        assert result["gdp_total"] >= 0.1

    def test_finalize_gdp_uses_seeded_gdpc_for_healthcare(
        self, import_estimate_gdp, populated_mini_repo
    ):
        mod = import_estimate_gdp
        result = mod.calculate_gdp(_parsed_states(mod, populated_mini_repo))
        # health_06 → 2.20 multiplier. With seeded gdpc=12.5 and population_total
        # in hundred-thousands (2_300_000 / 100_000 = 23): healthcare_raw
        # = 23 * 0.01 * 12.5 * 2.20 = 6.325.
        mod.finalize_gdp(result, health_idea="health_06", seeded_gdpc=12.5)
        expected_raw = 23 * 0.01 * 12.5 * 2.20
        expected_total = (result["gdp_pre_healthcare"] + expected_raw) * result[
            "productivity_mult"
        ]
        assert result["gdp_total"] == pytest.approx(expected_total)
        assert result["gdp_from_healthcare"] == pytest.approx(
            expected_raw * result["productivity_mult"]
        )
        assert result["health_idea"] == "health_06"


class TestEndToEndCountry:
    """compute_country_gdp wires the parsers → modifier stack → finalize."""

    def test_end_to_end(self, import_estimate_gdp, populated_mini_repo):
        mod = import_estimate_gdp
        idea_db = mod.parse_all_ideas()
        # Build states from on-disk files (parse_state_file_from_content is
        # already redirected to the mini_repo by import_estimate_gdp's patching).
        states = []
        for name in ("100-A.txt", "200-B.txt"):
            with open(
                populated_mini_repo / "history" / "states" / name, "r", encoding="utf-8"
            ) as f:
                states.append(mod.parse_state_file_from_content(f.read(), name))
        result = mod.compute_country_gdp("TST", states, idea_db)
        assert result is not None
        assert result["tag"] == "TST"
        assert result["starting_ideas"] == ["high_health", "industry_modern"]
        # Modifier stack came from the two real ideas parsed from the tmp file.
        # civilian_factories_productivity is in GDP_MODIFIER_KEYS, so it must
        # have aggregated.
        assert "civilian_factories_productivity" in result["modifier_stack"]
        # political_power_gain is NOT in GDP_MODIFIER_KEYS, so it must not
        # have leaked through the idea extractor.
        assert "political_power_gain" not in result["modifier_stack"]
        assert result["gdp_total"] >= 0.1

    def test_dynamic_resource_vars_extend_modifier_stack(
        self, import_estimate_gdp, mini_repo
    ):
        mod = import_estimate_gdp

        write_text(
            mini_repo / "history" / "countries" / "RES - Test.txt",
            (
                "2000.1.1 = {\n"
                "  set_variable = { oil_resource_extraction_var = 0.10 }\n"
                "  add_ideas = { industry_modern }\n"
                "}\n"
            ),
        )
        # Reuse the existing idea file from the populated fixture by adding a
        # resource-rich state owned by RES.
        write_text(
            mini_repo / "history" / "states" / "300-C.txt",
            (
                "state = {\n"
                "  id = 300\n"
                "  owner = RES\n"
                "  manpower = 500000\n"
                "  history = {\n"
                "    set_variable = { productivity_state_var = 600 }\n"
                "    resources = { oil = 5.0 }\n"
                "    buildings = { industrial_complex = 2 }\n"
                "  }\n"
                "}\n"
            ),
        )
        idea_db = mod.parse_all_ideas()
        with open(
            mini_repo / "history" / "states" / "300-C.txt", "r", encoding="utf-8"
        ) as f:
            state = mod.parse_state_file_from_content(f.read(), "300-C.txt")
        result = mod.compute_country_gdp("RES", [state], idea_db)
        assert result is not None
        # Every per-resource factor key should have received +0.10 from the
        # dynamic variable.
        for factor_key in mod.RESOURCE_FACTOR_KEYS.values():
            assert result["modifier_stack"][factor_key] == pytest.approx(0.10)


class TestCliMain:
    """The main() entrypoint: argv parsing, --top/--all, error exits, no-arg help."""

    def test_no_args_prints_docstring_and_exits_1(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py"])
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Estimate a nation's starting GDP" in captured.out

    def test_top_with_no_value_exits_1(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "--top"])
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1
        assert "--top requires an integer" in capsys.readouterr().err

    def test_top_with_non_integer_exits_1(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "--top", "five"])
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1
        assert "expects an integer" in capsys.readouterr().err

    def test_top_with_negative_exits_1(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "--top", "-3"])
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1
        assert "non-negative integer" in capsys.readouterr().err

    def test_top_with_explicit_tags_exits_1(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "--top", "5", "TST"])
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1
        assert "cannot be combined" in capsys.readouterr().err

    def test_explicit_tag_prints_per_country_breakdown(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "TST"])
        mod.main()
        out = capsys.readouterr().out
        assert "TST - GDP Estimation" in out
        assert "GDP Total:" in out
        assert "Buildings:" in out

    def test_verbose_lists_modifier_stack(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "TST", "-v"])
        mod.main()
        out = capsys.readouterr().out
        assert "Active GDP Modifiers" in out
        assert "civilian_factories_productivity" in out

    def test_unknown_tag_warns_and_skips(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "ZZZ"])
        mod.main()
        out = capsys.readouterr().out
        assert "WARNING: No states found for ZZZ" in out

    def test_all_prints_ranked_table(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "--all"])
        mod.main()
        out = capsys.readouterr().out
        # Table header present and TST appears in the ranked body.
        assert "Rank" in out
        assert "TAG" in out
        assert "TST" in out

    def test_top_zero_returns_all_ranked_untrimmed(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "--top", "0"])
        mod.main()
        out = capsys.readouterr().out
        # The header row plus the data row should both be present even when
        # the slice would otherwise truncate everything.
        assert "TAG" in out
        assert "TST" in out

    def test_top_truncates_to_n(
        self, import_estimate_gdp, populated_mini_repo, capsys, monkeypatch
    ):
        mod = import_estimate_gdp
        monkeypatch.setattr(sys, "argv", ["estimate_gdp.py", "--top", "1"])
        mod.main()
        out = capsys.readouterr().out
        # The ranked table should have a header line plus one data row.
        data_lines = [l for l in out.splitlines() if l.startswith("   1")]
        assert len(data_lines) == 1
