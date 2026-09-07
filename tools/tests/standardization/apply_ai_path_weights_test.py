"""Tests for tools/standardization/apply_ai_path_weights.py."""

from __future__ import annotations

import apply_ai_path_weights as tool
import pytest

MAP = """
group historical owner=DEN_ai_historical_path not=DEN_ai_not_historical_path
group socialist owner_flag=DEN_SOCIALIST_FOCUS_PATH not=DEN_ai_not_socialist_path
boost 25

DEN_legacy historical
DEN_guarded socialist 150
DEN_naked historical
DEN_inline historical
DEN_neutral -
"""

TREE = """focus_tree = {
	id = den

	focus = {
		id = DEN_legacy
		x = 0
		ai_will_do = {
			base = 50
			modifier = {
				factor = 150
				has_global_flag = DEN_HISTORICAL_FOCUS_PATH
			}
			modifier = {
				factor = 0
				is_historical_focus_on = yes
				NOT = { has_global_flag = DEN_HISTORICAL_FOCUS_PATH }
			}
			modifier = {
				factor = 0
				DEN_ai_rival_of_historical_path = yes
			}
		}
	}

	focus = {
		id = DEN_guarded
		x = 1
		ai_will_do = {
			base = 1
			modifier = {
				factor = 0
				can_staff_an_arms_industry = no
			}
			modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse }
			modifier = { factor = 2 ai_is_threatened = yes }
			modifier = { factor = 0 DEN_ai_not_socialist_path = yes }
		}
	}

	focus = {
		id = DEN_naked
		x = 2
	}

	focus = {
		id = DEN_inline
		x = 4
		ai_will_do = { base = 80 }
	}

	focus = {
		id = DEN_neutral
		x = 3
		ai_will_do = {
			base = 1
			modifier = { factor = 0 DEN_ai_not_socialist_path = yes }
			modifier = { factor = 3 date > 2010.1.1 }
		}
	}
}
"""


def run(text: str = TREE, mapping: str = MAP):
    lines = text.splitlines(keepends=True)
    output, notes = tool.apply(lines, tool.parse_mapping(mapping), "DEN")
    return "".join(output), notes


class TestMapping:
    def test_groups_and_assignments(self):
        mapping = tool.parse_mapping(MAP)
        assert mapping.groups["historical"].owner == "DEN_ai_historical_path = yes"
        assert mapping.groups["socialist"].owner == (
            "has_global_flag = DEN_SOCIALIST_FOCUS_PATH"
        )
        assert mapping.assignments["DEN_guarded"] == ("socialist", 150.0)
        assert mapping.assignments["DEN_legacy"] == ("historical", 25.0)
        assert mapping.assignments["DEN_neutral"] == (None, 0.0)

    def test_undeclared_group_is_rejected(self):
        with pytest.raises(tool.MappingError):
            tool.parse_mapping("DEN_x ghost")

    def test_group_without_a_kill_trigger_is_rejected(self):
        with pytest.raises(tool.MappingError):
            tool.parse_mapping("group a owner=DEN_ai_a_path")

    def test_trigger_names_are_whitelisted(self):
        with pytest.raises(tool.MappingError):
            tool.parse_mapping("group a owner=DEN}_ai_a not=DEN_ai_not_a")

    def test_comments_are_ignored(self):
        mapping = tool.parse_mapping("# note\ngroup a owner=X not=Y\nDEN_z a  # why")
        assert mapping.assignments["DEN_z"][0] == "a"


class TestRewrite:
    def test_legacy_three_modifier_shape_collapses(self):
        output, _ = run()
        assert "\t\t\tbase = 50\n" in output
        assert "modifier = { factor = 25 DEN_ai_historical_path = yes }" in output
        assert "modifier = { factor = 0 DEN_ai_not_historical_path = yes }" in output
        assert "is_historical_focus_on" not in output
        assert "DEN_ai_rival_of_historical_path" not in output

    def test_guards_are_preserved_in_order(self):
        output, _ = run()
        block = output.split("id = DEN_guarded")[1].split("focus = {")[0]
        assert "can_staff_an_arms_industry = no" in block
        assert "has_active_mission = bankruptcy_incoming_collapse" in block
        assert "ai_is_threatened = yes" in block
        assert block.index("can_staff") < block.index("bankruptcy_incoming_collapse")
        assert block.index("ai_is_threatened") < block.index("factor = 150")

    def test_path_modifiers_are_emitted_last(self):
        """A later `add` would resurrect a focus an earlier `factor = 0` killed."""
        output, _ = run()
        block = output.split("id = DEN_guarded")[1].split("focus = {")[0]
        modifiers = [
            line.strip() for line in block.splitlines() if "modifier = {" in line
        ]
        assert modifiers[-2:] == [
            "modifier = { factor = 150 has_global_flag = DEN_SOCIALIST_FOCUS_PATH }",
            "modifier = { factor = 0 DEN_ai_not_socialist_path = yes }",
        ]

    def test_a_focus_without_ai_will_do_gets_one(self):
        output, _ = run()
        block = output.split("id = DEN_naked")[1].split("focus = {")[0]
        assert "ai_will_do = {" in block
        assert "base = 1" in block
        assert "modifier = { factor = 25 DEN_ai_historical_path = yes }" in block

    def test_single_line_ai_will_do_keeps_its_base(self):
        output, _ = run()
        block = output.split("id = DEN_inline")[1].split("focus = {")[0]
        assert "base = 80" in block
        assert "modifier = { factor = 25 DEN_ai_historical_path = yes }" in block
        assert "modifier = { factor = 0 DEN_ai_not_historical_path = yes }" in block

    def test_inline_ai_will_do_with_a_nested_block_is_rejected(self):
        with pytest.raises(tool.MappingError):
            run(
                text=TREE.replace(
                    "ai_will_do = { base = 80 }",
                    "ai_will_do = { base = 80 modifier = { factor = 2 } }",
                )
            )

    def test_un_owning_strips_path_modifiers_and_keeps_the_rest(self):
        output, _ = run()
        block = output.split("id = DEN_neutral")[1]
        assert "DEN_ai_not_socialist_path" not in block
        assert "modifier = { factor = 3 date > 2010.1.1 }" in block

    def test_removed_modifiers_are_reported(self):
        _, notes = run()
        assert any("DEN_legacy: removed" in note for note in notes)
        assert sum(1 for note in notes if note.startswith("DEN_legacy")) == 3

    def test_idempotent(self):
        once, _ = run()
        twice, _ = run(once)
        assert once == twice

    def test_output_has_no_carriage_returns_and_uses_tabs(self):
        output, _ = run()
        assert "\r" not in output
        assert "\n    modifier" not in output

    def test_unknown_focus_id_is_rejected(self):
        with pytest.raises(tool.MappingError):
            run(mapping="group a owner=X not=Y\nDEN_ghost a")

    def test_duplicate_focus_ids_are_rejected(self):
        doubled = TREE + TREE.split("focus_tree = {")[1]
        with pytest.raises(tool.MappingError):
            run(text=doubled)

    def test_unbalanced_braces_abort(self):
        with pytest.raises(tool.MappingError):
            run(
                text=TREE.replace(
                    "\tfocus = {\n\t\tid = DEN_naked",
                    "\tfocus = {\n\t\t{\n\t\tid = DEN_naked",
                )
            )


class TestPathModifierDetection:
    def test_guard_is_never_path_owned(self):
        block = "modifier = { factor = 0 can_staff_an_arms_industry = no }"
        assert not tool.is_path_modifier(block, "DEN")

    def test_bare_historical_killswitch_is_replaced(self):
        block = "modifier = { factor = 0 is_historical_focus_on = yes }"
        assert tool.is_path_modifier(block, "DEN")

    def test_historical_boost_is_kept(self):
        block = "modifier = { factor = 2 is_historical_focus_on = yes }"
        assert not tool.is_path_modifier(block, "DEN")

    def test_another_country_flag_is_not_touched(self):
        block = "modifier = { factor = 0 has_global_flag = SWE_SOCIALIST_FOCUS_PATH }"
        assert not tool.is_path_modifier(block, "DEN")

    def test_unrelated_global_flag_is_not_touched(self):
        block = "modifier = { factor = 0 has_global_flag = GLOBAL_nato_disabled }"
        assert not tool.is_path_modifier(block, "DEN")
