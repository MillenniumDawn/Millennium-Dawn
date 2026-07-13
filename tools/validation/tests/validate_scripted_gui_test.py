"""Tests for scripted GUI parsing."""

from validate_scripted_gui import _parse_scripted_gui_text


def test_parse_all_top_level_scripted_gui_wrappers():
    text = """scripted_gui = {
	first_gui = {
		context_type = player_context
		first_button_click = { }
	}
}

scripted_gui = {
	second_gui = {
		context_type = invalid_context
		window_name = missing_window
		second_button_visible = { }
	}
}
"""

    blocks, trigger_names = _parse_scripted_gui_text(
        text, "common/scripted_guis/test.txt"
    )

    assert [block["name"] for block in blocks] == ["first_gui", "second_gui"]
    second = blocks[1]
    assert second["context_type"] == "invalid_context"
    assert second["window_name"] == "missing_window"
    expected_handler = ("second_button", "visible")
    assert expected_handler in second["handlers"]
    assert "second_button_visible" in trigger_names
