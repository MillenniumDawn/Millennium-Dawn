"""Regression tests for scripted GUI window references."""

import sys

import pytest
import validate_scripted_gui as V
from run_validator_batch import selected_specs

SCRIPTED_GUI_FILE = "common/scripted_guis/00_MD_economyview_scripted_guis.txt"
GUI_FILE = "interface/windows.gui"


@pytest.fixture
def window_repo(tmp_path, write_path):
    def build(window, gui="", parent=None):
        parent_line = f"\t\tparent_window_name = {parent}\n" if parent else ""
        write_path(tmp_path, GUI_FILE, gui)
        write_path(
            tmp_path,
            SCRIPTED_GUI_FILE,
            "scripted_gui = {\n"
            "\tinvestments = {\n"
            "\t\tcontext_type = selected_state_context\n"
            f"\t\twindow_name = {window}\n"
            + parent_line
            + "\t\tparent_window_token = selected_state_view\n"
            "\t}\n"
            "}\n",
        )
        return V.Validator(
            mod_path=str(tmp_path), use_colors=False, workers=1, no_cache=True
        )

    return build


@pytest.mark.parametrize(
    "window",
    ["investments_treasury_container", "investments_int_investments_container"],
)
@pytest.mark.parametrize("quoted", [False, True])
def test_undefined_investment_window_is_reported(window_repo, window, quoted):
    value = f'"{window}"' if quoted else window
    validator = window_repo(value)

    validator.run_validations()

    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("MISSING_WINDOW", SCRIPTED_GUI_FILE, 2)]
    assert f'window_name = "{window}"' in validator._issues[0].message
    assert validator._issues[0].severity == "error"
    assert validator.errors_found == 1


@pytest.mark.parametrize("quoted", [False, True])
def test_container_in_another_gui_file_resolves(
    tmp_path, write_path, window_repo, quoted
):
    window = "investments_treasury_container"
    value = f'"{window}"' if quoted else window
    validator = window_repo(value)
    write_path(
        tmp_path,
        "interface/investments.gui",
        f"guiTypes = {{\n\tcontainerWindowType = {{ name = {value} }}\n}}\n",
    )

    validator.run_validations()

    assert validator._issues == []


@pytest.mark.parametrize("gui_type", ["buttonType", "iconType", "gridBoxType"])
def test_non_container_element_cannot_satisfy_window_name(window_repo, gui_type):
    validator = window_repo(
        "investments_treasury_container",
        f'{gui_type} = {{ name = "investments_treasury_container" }}\n',
    )

    validator.run_validations()

    assert [issue.category for issue in validator._issues] == ["MISSING_WINDOW"]


def test_window_names_are_case_sensitive(window_repo):
    validator = window_repo(
        "investments_treasury_container",
        "containerWindowType = { name = Investments_treasury_container }\n",
    )

    validator.run_validations()

    assert [issue.category for issue in validator._issues] == ["MISSING_WINDOW"]


def test_commented_container_does_not_hide_a_missing_window(window_repo):
    validator = window_repo(
        "investments_treasury_container",
        '# containerWindowType = { name = "investments_treasury_container" }\n',
    )

    validator.run_validations()

    assert [issue.category for issue in validator._issues] == ["MISSING_WINDOW"]


def test_commented_window_reference_is_ignored(tmp_path, write_path, window_repo):
    validator = window_repo(
        "live_window", "containerWindowType = { name = live_window }\n"
    )
    write_path(
        tmp_path,
        SCRIPTED_GUI_FILE,
        "scripted_gui = {\n"
        "\tinvestments = {\n"
        '\t\t# window_name = "investments_treasury_container"\n'
        "\t\twindow_name = live_window\n"
        "\t}\n"
        "}\n",
    )

    validator.run_validations()

    assert validator._issues == []


@pytest.mark.parametrize("window", ["live_window", "top_bar", "missing_window"])
def test_parent_is_checked_even_when_window_resolves(window_repo, window):
    validator = window_repo(
        window,
        "containerWindowType = { name = live_window }\n",
        parent="missing_parent",
    )

    validator.run_validations()

    expected = ["MISSING_PARENT_WINDOW"]
    if window == "missing_window":
        expected.insert(0, "MISSING_WINDOW")
    assert [issue.category for issue in validator._issues] == expected


@pytest.mark.parametrize("parent", ["parent_window", "parent_window_instance"])
def test_named_parent_and_its_instance_resolve(window_repo, parent):
    validator = window_repo(
        "live_window",
        "containerWindowType = { name = live_window }\n"
        "containerWindowType = { name = parent_window }\n",
        parent=parent,
    )

    validator.run_validations()

    assert validator._issues == []


@pytest.mark.parametrize(
    "window, expected",
    [("live_window", []), ("investments_treasury_container", ["MISSING_WINDOW"])],
)
def test_staged_script_checks_unstaged_gui_definitions(
    tmp_path, window_repo, monkeypatch, window, expected
):
    window_repo(window, "containerWindowType = { name = live_window }\n")
    monkeypatch.setenv("MD_STAGED_FILES", SCRIPTED_GUI_FILE)
    validator = V.Validator(
        mod_path=str(tmp_path),
        use_colors=False,
        workers=1,
        no_cache=True,
        staged_only=True,
    )

    validator.run_validations()

    assert [issue.category for issue in validator._issues] == expected


def test_unreadable_scripted_gui_directory_is_a_hard_error(window_repo, monkeypatch):
    validator = window_repo("live_window")

    def fail_listdir(path):
        raise PermissionError(f"Cannot read {path}")

    monkeypatch.setattr(V.os, "listdir", fail_listdir)

    validator.run_validations()

    issue = next(
        issue
        for issue in validator._issues
        if issue.category == "SCRIPTED_GUI_READ_ERROR"
    )
    assert issue.severity == "error"
    assert issue.file.replace("\\", "/") == "common/scripted_guis"
    assert "Cannot read" in issue.message
    assert validator.errors_found == 1


def test_missing_window_fails_strict_cli(tmp_path, window_repo, monkeypatch):
    window_repo("investments_treasury_container")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_scripted_gui.py",
            "--path",
            str(tmp_path),
            "--strict",
            "--no-color",
            "--no-cache",
            "--workers",
            "1",
        ],
    )

    with pytest.raises(SystemExit) as result:
        V.main()

    assert result.value.code == 1


@pytest.mark.parametrize("group", ["scripted-guis", "interface"])
def test_ci_selects_scripted_gui_validation_for_both_sources(group):
    spec = next(
        spec
        for spec in selected_specs("targeted-a", {group})
        if spec.name == "scripted-gui"
    )
    assert spec.strict is True
