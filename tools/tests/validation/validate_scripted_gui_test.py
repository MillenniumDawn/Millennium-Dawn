"""Tests for scripted GUI parsing."""

import validate_scripted_gui as V
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


def test_empty_scripted_gui_wrapper_yields_nothing():
    assert _parse_scripted_gui_text("scripted_gui = {}\n", "x.txt") == ([], set())


_GUI = """containerWindowType = {
\tname = "good_window"
\tbuttonType = { name = good_button }
}
containerWindowType = { name = list_entry }
containerWindowType = { name = parent_window }
containerWindowType = { name = real_parent }
"""

_SGUI = """scripted_gui = {
\tparented = {
\t\tcontext_type = player_context
\t\tparent_window_name = parent_window
\t\tgood_button_click = { }
\t}
\tinstanced = {
\t\tcontext_type = player_context
\t\tparent_window_name = real_parent_instance
\t}
\tvanilla_parent = {
\t\tcontext_type = player_context
\t\tparent_window_name = top_bar
\t}
\tlisted = {
\t\tcontext_type = player_context
\t\twindow_name = good_window
\t\tentry_container = list_entry
\t}
\twritten_dirty = {
\t\tcontext_type = player_context
\t\tdirty = written_var
\t}
\tcountry_dirty = {
\t\tcontext_type = player_context
\t\tdirty = never_written_var
\t}
}
"""


def _repo(tmp_path, write_path):
    write_path(tmp_path, "interface/windows.gui", _GUI)
    write_path(tmp_path, "interface/notes.txt", "not a gui file\n")
    write_path(tmp_path, "common/scripted_guis/main.txt", _SGUI)
    write_path(tmp_path, "common/ideas/notes.md", "not scanned\n")
    write_path(tmp_path, "events/writes.txt", "set_variable = { written_var = 1 }\n")
    write_path(
        tmp_path, "localisation/english/gui_l_english.yml", 'l_english:\n k:0 "ok"\n'
    )
    write_path(tmp_path, "localisation/english/notes.txt", "not a loc file\n")


def _run(tmp_path, **kwargs):
    validator = V.Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, no_cache=True, **kwargs
    )
    validator.run_validations()
    return validator


def test_resolvable_parent_windows_and_containers_are_clean(tmp_path, write_path):
    _repo(tmp_path, write_path)

    validator = _run(tmp_path)

    assert [(i.category, i.message) for i in validator._issues] == [
        (
            "DIRTY_VAR_UNDEFINED",
            "Scripted GUI 'country_dirty' has dirty = never_written_var but no "
            "effect ever writes that variable — the GUI never refreshes",
        )
    ]


def test_undecodable_inputs_are_reported_and_skipped(tmp_path, write_path):
    _repo(tmp_path, write_path)
    latin1 = b'name = "caf\xe9"\n'
    (tmp_path / "interface" / "broken.gui").write_bytes(latin1)
    (tmp_path / "common" / "scripted_guis" / "broken.txt").mkdir()
    (tmp_path / "common" / "broken.txt").write_bytes(latin1)
    (tmp_path / "localisation" / "english" / "broken_l_english.yml").write_bytes(latin1)

    validator = _run(tmp_path)

    warnings = [line for line in validator.output_lines if "could not read" in line]
    assert len(warnings) == 2
    assert [i.category for i in validator._issues] == ["DIRTY_VAR_UNDEFINED"]


def test_repeated_bang_ref_on_one_line_is_reported_once(tmp_path, write_path):
    _repo(tmp_path, write_path)
    write_path(
        tmp_path,
        "localisation/english/bang_l_english.yml",
        'l_english:\n k:0 "[!never_click] then [!never_click]"\n',
    )

    validator = _run(tmp_path)

    assert [i.category for i in validator._issues].count("DEAD_BANG_REF") == 1


def test_dirty_check_survives_a_missing_events_directory(tmp_path, write_path):
    write_path(tmp_path, "interface/windows.gui", _GUI)
    write_path(
        tmp_path,
        "common/scripted_guis/main.txt",
        "scripted_gui = {\n"
        "\tcountry_dirty = {\n"
        "\t\tcontext_type = player_context\n"
        "\t\tdirty = never_written_var\n"
        "\t}\n"
        "}\n",
    )

    validator = _run(tmp_path)

    assert [i.category for i in validator._issues] == ["DIRTY_VAR_UNDEFINED"]


def test_staged_mode_suppresses_findings_outside_the_staged_set(
    tmp_path, write_path, monkeypatch
):
    _repo(tmp_path, write_path)
    monkeypatch.setenv("MD_STAGED_FILES", "interface/windows.gui")

    validator = _run(tmp_path, staged_only=True)

    assert validator._issues == []


def test_repo_without_interface_or_scripted_guis_is_a_clean_pass(tmp_path):
    validator = _run(tmp_path)
    assert validator._issues == []
