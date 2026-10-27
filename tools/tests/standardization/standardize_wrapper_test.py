"""Behavioral tests for tools/standardization/standardize.py."""

import sys
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def isolate_import_path(monkeypatch):
    monkeypatch.setattr(sys, "path", sys.path[:])


_LEGACY_MODIFIER_FOCUS = """focus_tree = {
\tid = TST_tree
\tcountry = {
\t\tfactor = 0
\t}

\tfocus = {
\t\tid = TST_legacy
\t\ticon = GFX_goal_generic_political_pressure
\t\tx = 0
\t\ty = 0
\t\tcost = 10
\t\tcustom_effect_tooltip = { MODIFIER = TST_Legacy_modifier }
\t}
}
"""

_SIMPLE_FOCUS = """focus_tree = {
id = TST_tree
country = { factor = 0 }
focus = {
id = TST_simple
icon = GFX_goal_generic_political_pressure
x = 0
y = 0
cost = 10
complete_effect = { add_political_power = 1 }
}
}
"""


def _run_main(monkeypatch, capsys, *args):
    """Run the documented CLI entry point in process and collect its result."""
    original_path = sys.path[:]
    try:
        import standardize
    finally:
        sys.path[:] = original_path

    monkeypatch.setattr(sys, "argv", ["standardize.py", *map(str, args)])
    try:
        standardize.main()
    except SystemExit as exc:
        if exc.code is None:
            returncode = 0
        elif isinstance(exc.code, int):
            returncode = exc.code
        else:
            print(exc.code, file=sys.stderr)
            returncode = 1
    else:
        returncode = 0
    captured = capsys.readouterr()
    return SimpleNamespace(
        returncode=returncode, stdout=captured.out, stderr=captured.err
    )


@pytest.mark.parametrize(
    "command",
    [
        "focus",
        "event",
        "decision",
        "idea",
        "mio",
        "technology",
        "history",
        "localisation",
    ],
)
def test_subcommand_help_lists_common_file_options(command, monkeypatch, capsys):
    result = _run_main(monkeypatch, capsys, command, "--help")

    assert result.returncode == 0
    assert "-o" in result.stdout and "--output" in result.stdout
    assert "-b" in result.stdout and "--backup" in result.stdout
    assert "-v" in result.stdout and "--verbose" in result.stdout
    assert "--no-color" not in result.stdout


def test_focus_help_has_focus_only_option(monkeypatch, capsys):
    result = _run_main(monkeypatch, capsys, "focus", "--help")

    assert "--check-naming" in result.stdout
    assert "--mod-root" not in result.stdout


def test_localisation_help_has_localisation_only_option(monkeypatch, capsys):
    result = _run_main(monkeypatch, capsys, "localisation", "--help")

    assert "--mod-root" in result.stdout
    assert "--check-naming" not in result.stdout


def test_event_rejects_no_color(monkeypatch, capsys):
    result = _run_main(monkeypatch, capsys, "event", "input.txt", "--no-color")

    assert result.returncode == 2
    assert "unrecognized arguments: --no-color" in result.stderr


def test_no_subcommand_exits_one(monkeypatch, capsys):
    result = _run_main(monkeypatch, capsys)
    assert result.returncode == 1


def test_string_system_exit_matches_script_error(monkeypatch, capsys):
    import standardize

    monkeypatch.setattr(standardize, "main", lambda: sys.exit("failed"))

    result = _run_main(monkeypatch, capsys)

    assert result.returncode == 1
    assert result.stderr == "failed\n"


def test_unknown_subcommand_exits_nonzero(monkeypatch, capsys):
    result = _run_main(monkeypatch, capsys, "nope", "/tmp/does_not_matter.txt")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_missing_input_file_reports_error(tmp_path, monkeypatch, capsys):
    target = tmp_path / "nope.txt"
    result = _run_main(monkeypatch, capsys, "focus", target)
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_focus_subcommand_runs(tmp_path, monkeypatch, capsys):
    """Focus subcommand has inline logic (not run_standardizer)."""
    src = tmp_path / "focus.txt"
    src.write_text(_SIMPLE_FOCUS, encoding="utf-8")

    result = _run_main(monkeypatch, capsys, "focus", src)
    assert result.returncode == 0


def test_focus_subcommand_with_output_and_backup(tmp_path, monkeypatch, capsys):
    src = tmp_path / "focus.txt"
    out = tmp_path / "out.txt"
    src.write_text(_SIMPLE_FOCUS, encoding="utf-8")

    result = _run_main(monkeypatch, capsys, "focus", src, "-o", out, "--backup")
    assert result.returncode == 0
    assert out.exists()


def test_event_subcommand_runs(tmp_path, monkeypatch, capsys):
    src = tmp_path / "event.txt"
    out = tmp_path / "event_out.txt"
    src.write_text(
        "country_event = {\n"
        "id=EVT_test.1\n"
        "title = EVT_test.1.t\n"
        "desc = EVT_test.1.d\n"
        "picture = GFX_evt_test\n"
        "is_triggered_only = yes\n"
        "option = { name = OK }\n"
        "}\n",
        encoding="utf-8",
    )
    result = _run_main(monkeypatch, capsys, "event", src, "-o", out)
    assert result.returncode == 0
    assert out.exists()


def test_decision_subcommand_runs(tmp_path, monkeypatch, capsys):
    src = tmp_path / "decision.txt"
    out = tmp_path / "decision_out.txt"
    src.write_text(
        "TAG_test = {\n"
        "TAG_test_decision = {\n"
        "icon = GFX_decision_test\n"
        "allowed = { always = yes }\n"
        "available = { always = yes }\n"
        "complete_effect = { add_political_power = 1 }\n"
        "}\n"
        "}\n",
        encoding="utf-8",
    )
    result = _run_main(monkeypatch, capsys, "decision", src, "-o", out)
    assert result.returncode == 0
    assert out.exists()


def test_idea_subcommand_runs(tmp_path, monkeypatch, capsys):
    src = tmp_path / "idea.txt"
    out = tmp_path / "idea_out.txt"
    src.write_text(
        "ideas = {\n"
        "country = {\n"
        "TST_test_idea = {\n"
        "picture = GFX_idea_test\n"
        "modifier = { test_factor = 0.1 }\n"
        "}\n"
        "}\n"
        "}\n",
        encoding="utf-8",
    )
    result = _run_main(monkeypatch, capsys, "idea", src, "-o", out)
    assert result.returncode == 0
    assert out.exists()


def test_mio_subcommand_runs(tmp_path, monkeypatch, capsys):
    src = tmp_path / "mio.txt"
    out = tmp_path / "mio_out.txt"
    src.write_text(
        "TST_organization = {\n"
        "name = TST_org\n"
        "icon = GFX_mio_test\n"
        "allowed = { original_tag = TST }\n"
        "equipment_type = { type = mio_equipment_test }\n"
        "tree_type = single_tree\n"
        "initial_trait = {\n"
        "organization_modifier = { military_industrial_organization_size = 1 }\n"
        "}\n"
        "}\n",
        encoding="utf-8",
    )
    result = _run_main(monkeypatch, capsys, "mio", src, "-o", out)
    assert result.returncode == 0
    assert out.exists()


def test_history_subcommand_runs(tmp_path, monkeypatch, capsys):
    src = tmp_path / "country_history.txt"
    out = tmp_path / "country_out.txt"
    src.write_text(
        "capital = 123\n"
        "2000.1.1 = {\n"
        'oob = "TST_2000.txt"\n'
        "set_politics = { ruling_party = democratic elections_allowed = yes }\n"
        "}\n",
        encoding="utf-8",
    )
    result = _run_main(monkeypatch, capsys, "history", src, "-o", out)
    assert result.returncode == 0
    assert out.exists()


def test_localisation_subcommand_with_mod_root(tmp_path, monkeypatch, capsys):
    src = tmp_path / "tst_l_english.yml"
    out = tmp_path / "tst_out.yml"
    (tmp_path / "localisation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "common").mkdir(parents=True, exist_ok=True)
    src.write_text('l_english:\n "x" : "y"\n', encoding="utf-8")
    result = _run_main(
        monkeypatch, capsys, "localisation", src, "-o", out, "--mod-root", tmp_path
    )
    assert result.returncode == 0


def test_localisation_subcommand_no_mod_root_fails(tmp_path, monkeypatch, capsys):
    src = tmp_path / "lone_l_english.yml"
    src.write_text('l_english:\n "x" : "y"\n', encoding="utf-8")
    result = _run_main(monkeypatch, capsys, "localisation", src)
    assert result.returncode != 0


def test_main_focus_inline_branch(tmp_path, monkeypatch, capsys):
    """A requested backup is created before the focus file is written."""
    src = tmp_path / "focus.txt"
    src.write_text(_SIMPLE_FOCUS.replace("TST_simple", "TST_inline"), encoding="utf-8")

    backup_calls = []
    monkeypatch.setattr(
        "shared_utils.create_backup",
        lambda path, _calls=backup_calls: _calls.append(path) or True,
    )

    result = _run_main(
        monkeypatch, capsys, "focus", src, "-o", tmp_path / "out.txt", "--backup"
    )

    assert result.returncode == 0
    assert backup_calls == [str(src)]
    assert (tmp_path / "out.txt").exists()


def test_main_focus_returns_one_when_backup_fails(tmp_path, monkeypatch, capsys):
    """Backup failure path inside the focus inline branch."""
    src = tmp_path / "focus.txt"
    src.write_text(
        "focus_tree = { id = TST_bk, country = { factor = 0 } }\n", encoding="utf-8"
    )
    monkeypatch.setattr("shared_utils.create_backup", lambda path: False)

    result = _run_main(monkeypatch, capsys, "focus", src, "--backup")
    assert result.returncode == 1


def test_main_localisation_returns_one_when_mod_root_missing(
    tmp_path, monkeypatch, capsys
):
    """Localisation branch with _detect_mod_root returning None."""
    src = tmp_path / "orphan.yml"
    src.write_text('l_english:\n "x" : "y"\n', encoding="utf-8")
    monkeypatch.setattr("standardize._detect_mod_root", lambda path: None)

    result = _run_main(monkeypatch, capsys, "localisation", src)
    assert result.returncode == 1


def test_focus_legacy_name_does_not_block_standardization_by_default(
    tmp_path, monkeypatch, capsys
):
    """A pre-existing violation elsewhere must not reject an unrelated edit."""
    source = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    source.write_text(_LEGACY_MODIFIER_FOCUS, encoding="utf-8")

    result = _run_main(monkeypatch, capsys, "focus", source, "-o", output)

    assert result.returncode == 0
    assert output.exists()
    assert "TST_Legacy_modifier" in output.read_text(encoding="utf-8")


def test_focus_check_naming_flag_is_forwarded(tmp_path, monkeypatch, capsys):
    source = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    source.write_text(_LEGACY_MODIFIER_FOCUS, encoding="utf-8")

    result = _run_main(
        monkeypatch, capsys, "focus", source, "-o", output, "--check-naming"
    )

    assert result.returncode != 0
    assert not output.exists()
