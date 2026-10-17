"""Tests for scripted GUI parsing."""

import sys

import pytest
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


def test_dirty_bound_to_engine_timer_is_flagged(tmp_path, write_path):
    write_path(tmp_path, "interface/windows.gui", _GUI)
    write_path(
        tmp_path,
        "common/scripted_guis/main.txt",
        "scripted_gui = {\n"
        "\ttimer_one = {\n"
        "\t\tcontext_type = player_context\n"
        "\t\tdirty = global.date\n"
        "\t}\n"
        "\ttimer_two = {\n"
        "\t\tcontext_type = player_context\n"
        "\t\tdirty = global.num_days\n"
        "\t}\n"
        "}\n",
    )

    validator = _run(tmp_path)

    assert [(i.category, i.severity) for i in validator._issues] == [
        ("DIRTY_TIMER_GLOBAL", "warning"),
        ("DIRTY_TIMER_GLOBAL", "warning"),
    ]
    assert "dirty = global.date" in validator._issues[0].message
    assert "dirty = global.num_days" in validator._issues[1].message


def test_dirty_bound_to_written_counter_is_clean(tmp_path, write_path):
    write_path(tmp_path, "interface/windows.gui", _GUI)
    write_path(
        tmp_path,
        "common/scripted_guis/main.txt",
        "scripted_gui = {\n"
        "\tcountered = {\n"
        "\t\tcontext_type = player_context\n"
        "\t\tdirty = global.my_counter\n"
        "\t}\n"
        "}\n",
    )
    write_path(
        tmp_path,
        "events/writes.txt",
        "add_to_variable = { global.my_counter = 1 }\n",
    )

    validator = _run(tmp_path)

    assert validator._issues == []


def test_dead_handlers_are_reported_in_name_order(tmp_path, write_path):
    names = [f"gone_{letter}" for letter in "jihgfedcba"]
    write_path(
        tmp_path,
        "common/scripted_guis/main.txt",
        "scripted_gui = {\n\tquiet = {\n\t\tcontext_type = player_context\n\t}\n"
        "\tdead = {\n\t\tcontext_type = player_context\n"
        + "".join(f"\t\t{name}_click = {{ }}\n" for name in names)
        + "\t}\n}\n",
    )

    validator = _run(tmp_path)

    assert [(i.category, i.message, i.file, i.line) for i in validator._issues] == [
        (
            "DEAD_HANDLER",
            f"Scripted GUI in 'dead' references '{name}_click' but no "
            f"button/icon named '{name}' exists in any .gui file",
            "common/scripted_guis/main.txt",
            5,
        )
        for name in sorted(names)
    ]


@pytest.mark.parametrize(
    "name, expected",
    [("name_", True), ("x_TAG_y", True), ("ordinary", False)],
)
def test_template_names(name, expected):
    assert V._looks_like_template(name) is expected


def test_normalise_path():
    assert V._normalise_path(r"./common\\x.txt") == "common//x.txt"


def test_gui_parser_records_named_elements_and_windows():
    parsed = V._parse_gui_text(
        'containerWindowType = { name = "window" }\n'
        "buttonType = { name = button }\n"
        "buttonType = { visible = yes }\n",
        "interface/test.gui",
    )
    assert set(parsed["elements"]) == {"window", "button"}
    assert parsed["containers"] == ["window"]
    assert parsed["windows"] == ["window"]
    assert parsed["unsupported_button_origos"] == []


def test_gui_parser_skips_an_unclosed_block():
    assert V._parse_gui_text("buttonType = {", "interface/broken.gui") == {
        "elements": {},
        "element_files": {},
        "containers": [],
        "windows": [],
        "unsupported_button_origos": [],
    }


def test_button_origo_reports_only_direct_button_properties(tmp_path, write_path):
    gui = """containerWindowType = {
 name = "legal_container"
 origo = center
 buttonType = {
  name = "bad_button"
  text = "quoted { origo = not_a_property }"
  # origo = commented_out
  OrIgO = center # } ignored comment brace
  iconType = { name = "nested_icon" origo = center }
  containerWindowType = {
   name = "nested_container"
   origo = center
   BuTtOnTyPe = {
    name = "nested_bad_button"
    ORIGO = center
   }
  }
 }
}
buttonType = {
 origo = center
}
"""
    write_path(tmp_path, "interface/nested.gui", gui)

    validator = _run(tmp_path)

    assert [
        (issue.category, issue.severity, issue.file, issue.line)
        for issue in validator._issues
    ] == [
        ("BUTTON_ORIGO_UNSUPPORTED", "error", "interface/nested.gui", 8),
        ("BUTTON_ORIGO_UNSUPPORTED", "error", "interface/nested.gui", 15),
        ("BUTTON_ORIGO_UNSUPPORTED", "error", "interface/nested.gui", 21),
    ]


def test_scripted_gui_parser_reads_every_field():
    blocks, triggers = _parse_scripted_gui_text(
        "scripted_gui = {\n\tname = {\n"
        "\t\tcontext_type = player_context\n"
        "\t\twindow_name = window\n"
        "\t\tparent_window_name = parent\n"
        "\t\tparent_window_token = token\n"
        "\t\tdirty = global.x\n"
        "\t\tai_test_scopes = test_self_country\n"
        "\t\tentry_container = foo_TAG_bar\n"
        "\t\tbutton_alt_control_click_enabled = { }\n"
        "\t}\n}\n",
        "common/scripted_guis/x.txt",
    )
    assert blocks[0]["parent_window_token"] == "token"
    assert "button_alt_control_click_enabled" in triggers


def test_scripted_gui_parser_skips_an_unclosed_block():
    assert _parse_scripted_gui_text("scripted_gui = { bad = {", "x.txt") == ([], set())


def test_variable_writes_and_reads():
    assert V._parse_var_writes_text(
        "set_global_variable = { global.written = 1 }\n"
        "set_variable = { var = ROOT.local }\n"
        "global.read = yes\n"
        "dirty = global.only_dirty\n"
    ) == ({"written", "local"}, {"written", "read"})


def test_full_run_reports_every_cross_reference_category(tmp_path, write_path):
    write_path(
        tmp_path,
        "interface/windows.gui",
        "containerWindowType = {\n"
        "\tname = good_window\n"
        "\tbuttonType = { name = good_button }\n"
        "}\n",
    )
    write_path(
        tmp_path,
        "common/scripted_guis/test.txt",
        """scripted_gui = {
\tgood = {
\t\tcontext_type = selected_country_context
\t\twindow_name = good_window
\t\tdirty = global.written
\t\tai_test_scopes = test_self_country
\t\tgood_button_click = { }
\t}
\tbad = {
\t\tcontext_type = invalid_context
\t\twindow_name = missing_window
\t\tparent_window_name = missing_parent
\t\tdirty = local_var
\t\tai_test_scopes = invalid_scope
\t\tmissing_button_visible = { }
\t\tentry_container = missing_container
\t\tentry_container = foo_TAG_bar
\t}
\tplayer_scopes = {
\t\tcontext_type = player_context
\t\tai_test_scopes = test_self_country
\t}
\tselected_bad = {
\t\tcontext_type = selected_country_context
\t\tai_test_scopes = invalid_scope
\t}
\tvanilla = {
\t\tcontext_type = player_context
\t\twindow_name = top_bar
\t\tparent_window_name = top_bar_instance
\t}
\tno_context = { dirty = yes }
\tglobal_none = { dirty = global.never_written }
}
""",
    )
    write_path(
        tmp_path,
        "events/writes.txt",
        "set_global_variable = { global.written = 1 }\nglobal.local_var = yes\n",
    )
    write_path(
        tmp_path,
        "localisation/english/gui_l_english.yml",
        'l_english:\nkey:0 "[!good_button_click] [!never_click]"\n',
    )

    validator = _run(tmp_path)

    assert {issue.category for issue in validator._issues} == {
        "DEAD_HANDLER",
        "DEAD_BANG_REF",
        "MISSING_WINDOW",
        "MISSING_PARENT_WINDOW",
        "MISSING_ENTRY_CONTAINER",
        "INVALID_CONTEXT_TYPE",
        "DIRTY_SCOPE_MISMATCH",
        "DIRTY_VAR_UNDEFINED",
        "INVALID_AI_TEST_SCOPE",
        "AI_TEST_SCOPES_NOT_APPLICABLE",
    }
    assert any("global.never_written" in issue.message for issue in validator._issues)


def _clean_repo(tmp_path, write_path):
    write_path(
        tmp_path, "interface/good.gui", "containerWindowType = { name = good_window }\n"
    )
    write_path(
        tmp_path,
        "common/scripted_guis/good.txt",
        "scripted_gui = { good = { context_type = player_context } }\n",
    )
    write_path(tmp_path, "localisation/english/good.yml", 'l_english:\nkey:0 "ok"\n')


@pytest.mark.parametrize("staged_only", [False, True], ids=["full", "staged"])
def test_clean_repo_passes(tmp_path, write_path, monkeypatch, staged_only):
    _clean_repo(tmp_path, write_path)
    monkeypatch.setenv("MD_STAGED_FILES", str(tmp_path / "interface/good.gui"))
    assert _run(tmp_path, staged_only=staged_only)._issues == []


# case: (path argument relative to the repo, exit code)
@pytest.mark.parametrize(
    "path, code", [(".", 0), ("missing", 1)], ids=["repo", "missing"]
)
def test_cli_exit_code(tmp_path, write_path, monkeypatch, path, code):
    _clean_repo(tmp_path, write_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_scripted_gui.py", "--path", str(tmp_path / path), "--workers", "1"],
    )
    with pytest.raises(SystemExit) as result:
        V.main()
    assert result.value.code == code


def test_button_origo_fails_strict_cli(tmp_path, write_path, monkeypatch):
    _clean_repo(tmp_path, write_path)
    write_path(
        tmp_path,
        "interface/good.gui",
        "containerWindowType = { name = good_window }\n"
        "buttonType = { origo = center }\n",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_scripted_gui.py", "--path", str(tmp_path), "--strict"],
    )

    with pytest.raises(SystemExit) as result:
        V.main()

    assert result.value.code == 1
