"""Tests for tools/analysis/focus_overlap_report.py."""

from __future__ import annotations

import json
from decimal import Decimal

import focus_overlap_report as report
import pytest
from shared.suite import write_under
from shared_utils import blank_quoted_strings


def focus(body: str) -> str:
    return "\tfocus = {\n" + body + "\n\t}\n"


def tree_offset() -> str:
    return focus(
        "\t\tid = a\n\t\tx = 4\n\t\ty = 0\n"
        "\t\toffset = { x = 9 trigger = { has_focus_tree = abbott_tree } }"
    )


def parse(text: str):
    return report.parse_focus_file(blank_quoted_strings(text))


def positions(text: str, **scenario):
    focuses = parse(text)
    return focuses, report.resolve_positions(focuses, report.Scenario(**scenario))


class TestParsing:
    def test_reads_position_and_parent(self):
        focuses = parse(
            focus("\t\tid = a\n\t\tx = 4\n\t\ty = 2")
            + focus("\t\tid = b\n\t\tx = 1\n\t\ty = 1\n\t\trelative_position_id = a")
        )
        assert set(focuses) == {"a", "b"}
        assert (focuses["a"].x, focuses["a"].y) == (4, 2)
        assert focuses["b"].relative_to == "a"

    def test_nested_x_is_not_read_as_the_focus_position(self):
        focuses = parse(
            focus(
                "\t\tid = a\n\t\tx = 4\n\t\ty = 2\n"
                "\t\toffset = { x = -9 trigger = { has_completed_focus = z } }"
            )
        )
        assert (focuses["a"].x, focuses["a"].y) == (4, 2)
        assert focuses["a"].offsets[0].dx == -9

    def test_prerequisite_groups_are_kept_separate(self):
        focuses = parse(
            focus(
                "\t\tid = c\n\t\tx = 0\n\t\ty = 0\n"
                "\t\tprerequisite = { focus = a focus = b }\n"
                "\t\tprerequisite = { focus = d }"
            )
        )
        assert focuses["c"].prereq_groups == [["a", "b"], ["d"]]

    def test_shared_focus_blocks_are_parsed(self):
        text = "shared_focus = {\n\tid = s\n\tx = 3\n\ty = 1\n}\n"
        assert parse(text)["s"].kind == "shared_focus"


class TestPositions:
    def test_relative_chain_three_deep(self):
        text = (
            focus("\t\tid = a\n\t\tx = 10\n\t\ty = 0")
            + focus("\t\tid = b\n\t\tx = 2\n\t\ty = 1\n\t\trelative_position_id = a")
            + focus("\t\tid = c\n\t\tx = -1\n\t\ty = 3\n\t\trelative_position_id = b")
        )
        _focuses, resolved = positions(text)
        assert resolved["a"] == (10, 0)
        assert resolved["b"] == (12, 1)
        assert resolved["c"] == (11, 4)

    def test_offset_applies_only_when_its_trigger_holds(self):
        text = focus(
            "\t\tid = a\n\t\tx = 20\n\t\ty = 0\n"
            "\t\toffset = { x = -8 trigger = { has_completed_focus = p } }"
        )
        assert positions(text)[1]["a"] == (20, 0)
        assert positions(text, completed=frozenset({"p"}))[1]["a"] == (12, 0)

    def test_offset_moves_the_whole_subtree(self):
        text = focus(
            "\t\tid = a\n\t\tx = 20\n\t\ty = 0\n"
            "\t\toffset = { y = -12 trigger = { date > 2005.10.1 } }"
        ) + focus("\t\tid = b\n\t\tx = 1\n\t\ty = 2\n\t\trelative_position_id = a")
        assert positions(text, date=(2006, 1, 1))[1]["b"] == (21, -10)
        assert positions(text, date=(2001, 1, 1))[1]["b"] == (21, 2)

    def test_unknown_trigger_leaves_the_offset_off(self):
        text = focus(
            "\t\tid = a\n\t\tx = 5\n\t\ty = 0\n"
            "\t\toffset = { x = -5 trigger = { has_country_flag = whatever } }"
        )
        assert positions(text)[1]["a"] == (5, 0)

    def test_relative_position_cycle_does_not_recurse_forever(self):
        text = focus(
            "\t\tid = a\n\t\tx = 1\n\t\ty = 1\n\t\trelative_position_id = b"
        ) + focus("\t\tid = b\n\t\tx = 2\n\t\ty = 2\n\t\trelative_position_id = a")
        assert positions(text)[1]["a"] == (3, 3)


class TestVisibility:
    def visible(self, text, **scenario):
        focuses = parse(text)
        return report.resolve_visibility(focuses, report.Scenario(**scenario))

    def test_allow_branch_hides_its_own_focus(self):
        text = focus(
            "\t\tid = a\n\t\tx = 0\n\t\ty = 0\n"
            "\t\tallow_branch = { has_completed_focus = p }"
        )
        assert self.visible(text)["a"] is False
        assert self.visible(text, completed=frozenset({"p"}))["a"] is True

    def test_descendant_is_hidden_through_its_prerequisite(self):
        text = focus(
            "\t\tid = a\n\t\tx = 0\n\t\ty = 0\n"
            "\t\tallow_branch = { has_completed_focus = p }"
        ) + focus("\t\tid = b\n\t\tx = 0\n\t\ty = 1\n\t\tprerequisite = { focus = a }")
        assert self.visible(text)["b"] is False

    def test_second_prerequisite_path_keeps_a_focus_visible(self):
        text = (
            focus(
                "\t\tid = a\n\t\tx = 0\n\t\ty = 0\n"
                "\t\tallow_branch = { has_completed_focus = p }"
            )
            + focus("\t\tid = b\n\t\tx = 2\n\t\ty = 0")
            + focus(
                "\t\tid = c\n\t\tx = 0\n\t\ty = 1\n"
                "\t\tprerequisite = { focus = a focus = b }"
            )
        )
        assert self.visible(text)["c"] is True

    def test_unknown_allow_branch_trigger_keeps_the_focus_visible(self):
        text = focus(
            "\t\tid = a\n\t\tx = 0\n\t\ty = 0\n"
            "\t\tallow_branch = { has_country_flag = whatever }"
        )
        assert self.visible(text)["a"] is True

    def test_date_bounded_branch_closes_after_its_window(self):
        text = focus(
            "\t\tid = a\n\t\tx = 0\n\t\ty = 0\n\t\tallow_branch = { date < 2005.10.1 }"
        )
        assert self.visible(text, date=(2001, 1, 1))["a"] is True
        assert self.visible(text, date=(2006, 1, 1))["a"] is False


class TestReport:
    def two_in_one_cell(self):
        return focus(
            "\t\tid = a\n\t\tx = 3\n\t\ty = 1\n"
            "\t\tallow_branch = { has_completed_focus = p }"
        ) + focus("\t\tid = b\n\t\tx = 3\n\t\ty = 1")

    def build(self, text, region=None, adjacent=False, show_map=False, **scenario):
        focuses = parse(text)
        state = report.Scenario(**scenario)
        return report.build_report(
            focuses,
            report.resolve_positions(focuses, state),
            report.resolve_visibility(focuses, state),
            state,
            region,
            adjacent,
            show_map,
        )

    def test_shared_cell_is_reported_only_while_both_are_visible(self):
        text = self.two_in_one_cell()
        assert self.build(text)["collisions"] == []
        collisions = self.build(text, completed=frozenset({"p"}))["collisions"]
        assert len(collisions) == 1
        assert (collisions[0]["x"], collisions[0]["y"]) == (3, 1)
        assert [entry["id"] for entry in collisions[0]["focuses"]] == ["a", "b"]

    def test_region_filters_the_report(self):
        text = self.two_in_one_cell()
        state = {"completed": frozenset({"p"})}
        assert self.build(text, region=(0, 2, 0, 9), **state)["collisions"] == []
        assert self.build(text, region=(0, 9, 0, 9), **state)["collisions"] != []

    def test_adjacent_columns_are_reported_separately(self):
        text = focus("\t\tid = a\n\t\tx = 3\n\t\ty = 1") + focus(
            "\t\tid = b\n\t\tx = 4\n\t\ty = 1"
        )
        built = self.build(text, adjacent=True)
        assert built["collisions"] == []
        assert [(p["left"]["id"], p["right"]["id"]) for p in built["adjacent"]] == [
            ("a", "b")
        ]

    def test_two_columns_apart_is_not_adjacent(self):
        text = focus("\t\tid = a\n\t\tx = 3\n\t\ty = 1") + focus(
            "\t\tid = b\n\t\tx = 5\n\t\ty = 1"
        )
        assert self.build(text, adjacent=True)["adjacent"] == []

    def test_map_is_ordered_by_row_then_column(self):
        text = (
            focus("\t\tid = a\n\t\tx = 5\n\t\ty = 1")
            + focus("\t\tid = b\n\t\tx = 1\n\t\ty = 1")
            + focus("\t\tid = c\n\t\tx = 9\n\t\ty = 0")
        )
        built = self.build(text, show_map=True)
        assert [entry["id"] for entry in built["map"]] == ["c", "b", "a"]

    def test_text_output_names_both_sides_of_a_collision(self):
        built = self.build(self.two_in_one_cell(), completed=frozenset({"p"}))
        text = report.format_text(built)
        assert "Overlapping cells (1):" in text
        assert "(3,1)" in text
        assert "a (l1)" in text

    def test_fractional_cells_are_written_as_json_numbers(self):
        text = (
            focus("\t\tid = a\n\t\tx = 1.5\n\t\ty = 2.5")
            + focus("\t\tid = b\n\t\tx = 0.75\n\t\ty = 2\n\t\trelative_position_id = c")
            + focus("\t\tid = c\n\t\tx = 0.75\n\t\ty = 0.5")
            + focus("\t\tid = d\n\t\tx = 2.5\n\t\ty = 2.5")
            + focus(
                "\t\tid = e\n\t\tx = 0.5\n\t\ty = 0.5\n\t\trelative_position_id = f"
            )
            + focus("\t\tid = f\n\t\tx = 0.5\n\t\ty = 0.5")
        )
        built = self.build(text, adjacent=True, show_map=True)
        assert json.loads(json.dumps(built)) == built
        collision = built["collisions"][0]
        assert (collision["x"], collision["y"]) == (1.5, 2.5)
        assert type(collision["x"]) is float and type(collision["y"]) is float
        assert [entry["id"] for entry in collision["focuses"]] == ["a", "b"]
        pairs = [(p["y"], p["left"]["id"], p["right"]["id"]) for p in built["adjacent"]]
        assert pairs == [(2.5, "b", "d")]
        assert type(built["adjacent"][0]["y"]) is float
        cells = {entry["id"]: (entry["x"], entry["y"]) for entry in built["map"]}
        assert cells["c"] == (0.75, 0.5)
        assert [type(value) for value in cells["c"]] == [float, float]
        assert cells["e"] == (1, 1)
        assert [type(value) for value in cells["e"]] == [int, int]
        assert "(1.5,2.5)" in report.format_text(built)


class TestCoordinates:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("3", 3),
            ("-2", -2),
            ("+4", 4),
            ("2.0", 2),
            ("1.50", Decimal("1.5")),
            (".5", Decimal("0.5")),
            ("-4.5", Decimal("-4.5")),
        ],
    )
    def test_whole_values_stay_ints_and_fractions_stay_exact(self, value, expected):
        parsed = report.parse_coordinate(value)
        assert parsed == expected
        assert type(parsed) is type(expected)

    @pytest.mark.parametrize("value", ["", "1e3", "nan", "1.2.3", "@column"])
    def test_non_numeric_value_is_rejected(self, value):
        with pytest.raises(ValueError, match="expected a number"):
            report.parse_coordinate(value)

    def test_fractional_focus_and_offset_coordinates_are_read(self):
        focuses, resolved = positions(
            focus(
                "\t\tid = a\n\t\tx = 1.5\n\t\ty = -4.5\n"
                "\t\toffset = { x = 0.5 y = -1.5 trigger = { always = yes } }"
            )
        )
        assert (focuses["a"].x, focuses["a"].y) == (Decimal("1.5"), Decimal("-4.5"))
        assert (focuses["a"].offsets[0].dx, focuses["a"].offsets[0].dy) == (
            Decimal("0.5"),
            Decimal("-1.5"),
        )
        assert resolved["a"] == (2, -6)

    def test_fractions_that_add_up_land_on_the_same_cell(self):
        text = (
            focus("\t\tid = a\n\t\tx = 0.1\n\t\ty = 0")
            + focus("\t\tid = b\n\t\tx = 0.2\n\t\ty = 1\n\t\trelative_position_id = a")
            + focus("\t\tid = c\n\t\tx = 0.3\n\t\ty = 1")
        )
        _focuses, resolved = positions(text)
        assert resolved["b"] == resolved["c"] == (Decimal("0.3"), 1)


class TestFocusTree:
    def test_has_focus_tree_is_unknown_without_a_tree(self):
        assert report.evaluate("has_focus_tree = t", report.Scenario()) is None
        assert positions(tree_offset())[1]["a"] == (4, 0)

    def test_has_focus_tree_compares_with_the_scenario_tree(self):
        scenario = report.Scenario(focus_tree="t")
        assert report.evaluate("has_focus_tree = t", scenario) is True
        assert report.evaluate("has_focus_tree = u", scenario) is False
        assert report.evaluate("NOT = { has_focus_tree = u }", scenario) is True

    def test_offset_follows_the_scenario_tree(self):
        assert positions(tree_offset(), focus_tree="abbott_tree")[1]["a"] == (13, 0)
        assert positions(tree_offset(), focus_tree="other_tree")[1]["a"] == (4, 0)

    def test_file_tree_is_known_only_when_the_file_has_one(self):
        one = "focus_tree = {\n\tid = t\n" + focus("\t\tid = a") + "}\n"
        two = one + one.replace("id = t", "id = u")
        assert report.file_focus_tree(one) == "t"
        assert report.file_focus_tree(two) is None
        assert report.file_focus_tree("shared_focus = {\n\tid = s\n}\n") is None


class TestCli:
    def test_json_output_carries_the_scenario(self, tmp_path, capsys):
        path = write_under(
            tmp_path, "tree.txt", "focus_tree = {\n" + focus("\t\tid = a") + "}\n"
        )
        exit_code = report.main(
            ["--file", str(path), "--date", "2006.1.1", "--format", "json"]
        )
        payload = json.loads(capsys.readouterr().out)
        assert exit_code == 0
        assert payload["scenario"]["date"] == "2006.1.1"
        assert payload["focuses"] == 1

    @pytest.mark.parametrize(
        "extra,tree,x",
        [
            ([], "abbott_tree", 13),
            (["--tree", "other_tree"], "other_tree", 4),
        ],
    )
    def test_tree_comes_from_the_file_unless_given(
        self, tmp_path, capsys, extra, tree, x
    ):
        path = write_under(
            tmp_path,
            "tree.txt",
            "focus_tree = {\n\tid = abbott_tree\n" + tree_offset() + "}\n",
        )
        report.main(["--file", str(path), "--map", "--format", "json", *extra])
        payload = json.loads(capsys.readouterr().out)
        assert payload["scenario"]["focus_tree"] == tree
        assert (payload["map"][0]["x"], payload["map"][0]["y"]) == (x, 0)

    def test_fractional_coordinates_are_printed(self, tmp_path, capsys):
        path = write_under(tmp_path, "tree.txt", focus("\t\tid = a\n\t\tx = 1.5"))
        assert report.main(["--file", str(path), "--map"]) == 0
        output = capsys.readouterr().out
        assert "tree=-" in output
        assert "(1.5,  0) a (l1)" in output

    def test_bad_date_is_rejected(self, tmp_path):
        path = write_under(tmp_path, "tree.txt", focus("\t\tid = a"))
        try:
            report.main(["--file", str(path), "--date", "not-a-date"])
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError("expected argparse to reject the date")
