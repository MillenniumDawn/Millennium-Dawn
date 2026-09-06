"""Tests for tools/analysis/focus_overlap_report.py."""

from __future__ import annotations

import json

import focus_overlap_report as report
from shared.suite import write_under


def focus(body: str) -> str:
    return "\tfocus = {\n" + body + "\n\t}\n"


def parse(text: str):
    return report.parse_focus_file(report.blank_quoted_strings(text))


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

    def test_bad_date_is_rejected(self, tmp_path):
        path = write_under(tmp_path, "tree.txt", focus("\t\tid = a"))
        try:
            report.main(["--file", str(path), "--date", "not-a-date"])
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError("expected argparse to reject the date")
