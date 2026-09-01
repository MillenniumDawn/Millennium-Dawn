"""Behavioral tests for tools/standardization/standardize.py.

Exercises the seven subcommands end-to-end against small real fixtures.
Focuses on the dispatch surface -- parser setup, file existence checks, and
each subcommand path -- without depending on the actual standardizer
internals.
"""

import subprocess
import sys
from pathlib import Path

import pytest

_CLI = Path(__file__).resolve().parents[2] / "standardization" / "standardize.py"


def _run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(_CLI), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_no_subcommand_exits_one():
    result = _run()
    assert result.returncode == 1


def test_unknown_subcommand_exits_nonzero():
    result = _run("nope", "/tmp/does_not_matter.txt")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_missing_input_file_reports_error(tmp_path):
    target = tmp_path / "nope.txt"
    result = _run("focus", str(target))
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_focus_subcommand_runs(tmp_path):
    """Focus subcommand has inline logic (not run_standardizer)."""
    src = tmp_path / "focus.txt"
    src.write_text(
        "focus_tree = {\n"
        "id = TST_tree\n"
        "country = { factor = 0 }\n"
        "focus = {\n"
        "id = TST_simple\n"
        "icon = GFX_goal_generic_political_pressure\n"
        "x = 0\n"
        "y = 0\n"
        "cost = 10\n"
        "complete_effect = { add_political_power = 1 }\n"
        "}\n"
        "}\n",
        encoding="utf-8",
    )
    result = _run("focus", str(src))
    assert result.returncode == 0


def test_focus_subcommand_with_output_and_backup(tmp_path):
    src = tmp_path / "focus.txt"
    out = tmp_path / "out.txt"
    src.write_text(
        "focus_tree = {\n"
        "id = TST_tree\n"
        "country = { factor = 0 }\n"
        "focus = {\n"
        "id = TST_simple\n"
        "icon = GFX_goal_generic_political_pressure\n"
        "x = 0\n"
        "y = 0\n"
        "cost = 10\n"
        "complete_effect = { add_political_power = 1 }\n"
        "}\n"
        "}\n",
        encoding="utf-8",
    )
    result = _run("focus", str(src), "-o", str(out), "--backup")
    assert result.returncode == 0
    assert out.exists()


def test_event_subcommand_runs(tmp_path):
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
    result = _run("event", str(src), "-o", str(out))
    assert result.returncode == 0
    assert out.exists()


def test_decision_subcommand_runs(tmp_path):
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
    result = _run("decision", str(src), "-o", str(out))
    assert result.returncode == 0
    assert out.exists()


def test_idea_subcommand_runs(tmp_path):
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
    result = _run("idea", str(src), "-o", str(out))
    assert result.returncode == 0
    assert out.exists()


def test_mio_subcommand_runs(tmp_path):
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
    result = _run("mio", str(src), "-o", str(out))
    assert result.returncode == 0
    assert out.exists()


def test_history_subcommand_runs(tmp_path):
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
    result = _run("history", str(src), "-o", str(out))
    assert result.returncode == 0
    assert out.exists()


def test_localisation_subcommand_with_mod_root(tmp_path):
    src = tmp_path / "tst_l_english.yml"
    out = tmp_path / "tst_out.yml"
    (tmp_path / "localisation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "common").mkdir(parents=True, exist_ok=True)
    src.write_text('l_english:\n "x" : "y"\n', encoding="utf-8")
    result = _run("localisation", str(src), "-o", str(out), "--mod-root", str(tmp_path))
    assert result.returncode == 0


def test_localisation_subcommand_no_mod_root_fails(tmp_path):
    src = tmp_path / "lone_l_english.yml"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text('l_english:\n "x" : "y"\n', encoding="utf-8")
    result = _run("localisation", str(src))
    # Either no-detect -> explicit error, or the standardizer exits non-zero.
    assert result.returncode != 0


def test_main_focus_inline_branch(tmp_path, monkeypatch):
    """Exercise the inline focus branch of main() in-process."""
    import standardize

    src = tmp_path / "focus.txt"
    src.write_text(
        "focus_tree = {\n"
        "id = TST_inline\n"
        "country = { factor = 0 }\n"
        "focus = {\n"
        "id = TST_inline_focus\n"
        "icon = GFX_goal_generic_political_pressure\n"
        "x = 0\n"
        "y = 0\n"
        "cost = 10\n"
        "complete_effect = { add_political_power = 1 }\n"
        "}\n"
        "}\n",
        encoding="utf-8",
    )

    backup_calls = []
    monkeypatch.setattr(
        "shared_utils.create_backup",
        lambda path, _calls=backup_calls: _calls.append(path) or True,
    )

    saved = sys.argv[:]
    sys.argv = [
        "standardize.py",
        "focus",
        str(src),
        "-o",
        str(tmp_path / "out.txt"),
        "--backup",
    ]
    try:
        standardize.main()
    except SystemExit as exc:
        assert exc.code in (None, 0), f"unexpected exit: {exc.code}"
    finally:
        sys.argv = saved

    assert backup_calls == [str(src)]
    assert (tmp_path / "out.txt").exists()


def test_main_focus_returns_one_when_backup_fails(tmp_path, monkeypatch):
    """Backup failure path inside the focus inline branch."""
    import standardize

    src = tmp_path / "focus.txt"
    src.write_text(
        "focus_tree = { id = TST_bk, country = { factor = 0 } }\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("shared_utils.create_backup", lambda path: False)

    saved = sys.argv[:]
    sys.argv = ["standardize.py", "focus", str(src), "--backup"]
    try:
        with pytest.raises(SystemExit) as exc:
            standardize.main()
    finally:
        sys.argv = saved
    assert exc.value.code == 1


def test_main_localisation_returns_one_when_mod_root_missing(tmp_path, monkeypatch):
    """Localisation branch with _detect_mod_root returning None."""
    import standardize

    src = tmp_path / "orphan.yml"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text('l_english:\n "x" : "y"\n', encoding="utf-8")
    monkeypatch.setattr("standardize._detect_mod_root", lambda path: None)

    saved = sys.argv[:]
    sys.argv = ["standardize.py", "localisation", str(src)]
    try:
        with pytest.raises(SystemExit) as exc:
            standardize.main()
    finally:
        sys.argv = saved
    assert exc.value.code == 1
