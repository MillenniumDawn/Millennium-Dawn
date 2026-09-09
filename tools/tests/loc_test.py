"""Parsing and failure handling tests for the localization helper."""

import runpy
import sys

import loc
import pytest
from shared.paths import TOOLS_DIR


def _write(path, text):
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return path


def test_main_fails_when_localisation_output_cannot_be_written(tmp_path, monkeypatch):
    source = tmp_path / "focus.txt"
    source.write_text(
        "focus_tree = {\n\tfocus = {\n\t\tid = test_focus\n\t}\n}\n",
        encoding="utf-8",
    )
    output = tmp_path / "output.yml"

    def fail_write(*_args, **_kwargs):
        raise OSError("read-only")

    monkeypatch.setattr(loc, "atomic_write_text", fail_write)
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(output)])

    try:
        loc.main()
    except SystemExit as error:
        assert "Could not write file" in str(error)
    else:
        assert False, "loc.main should fail when the output cannot be written"


def test_main_creates_single_bom_localisation_file(tmp_path, monkeypatch):
    source = tmp_path / "focus.txt"
    source.write_text(
        "focus_tree = {\n\tfocus = {\n\t\tid = test_focus\n\t}\n}\n",
        encoding="utf-8",
    )
    output = tmp_path / "output.yml"
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(output)])

    loc.main()
    first = output.read_bytes()
    loc.main()

    assert first.startswith(b"\xef\xbb\xbf")
    assert first.count(b"\xef\xbb\xbf") == 1
    assert output.read_bytes() == first


def test_readfile_reports_a_source_it_cannot_open(tmp_path, capsys):
    keys, kinds = loc.readfile(str(tmp_path / "absent.txt"))

    assert keys == []
    assert kinds == (False, False, False, False)
    assert "Could not read file" in capsys.readouterr().out


def test_readfile_collects_event_title_desc_and_option_keys(tmp_path):
    source = _write(
        tmp_path / "events.txt",
        "add_namespace = test\n"
        "country_event = {\n"
        "\tid = test.1\n"
        "\ttitle = test.1.t\n"
        "\tdesc = test.1.d\n"
        "\toption = {\n"
        "\t\tname = test.1.a\n"
        "\t}\n"
        "}\n",
    )

    keys, kinds = loc.readfile(str(source))

    assert keys == ["test.1.t", "test.1.d", "test.1.a"]
    assert kinds[0] is True


def test_readfile_collects_idea_name_and_desc_keys(tmp_path):
    source = _write(
        tmp_path / "ideas.txt",
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\tTEST_idea = {\n"
        "\t\t\tpicture = x\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )

    keys, kinds = loc.readfile(str(source))

    assert keys == ["TEST_idea", "TEST_idea_desc"]
    assert kinds[2] is True


def test_readfile_collects_technology_keys(tmp_path):
    # Detection only sticks while every brace-opening line names "technologies";
    # any other nested block flips the parser into decision mode.
    source = _write(
        tmp_path / "technologies.txt",
        "technologies = {\n"
        "\tinfantry_technologies = {\n"
        "\t\tsmall_arms_technologies = {\n"
        "\t\t\tresearch_cost = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )

    keys, kinds = loc.readfile(str(source))

    assert keys == ["small_arms_technologies", "small_arms_technologies_desc"]
    assert kinds == (False, False, False, False)


def test_readfile_collects_decision_and_category_keys(tmp_path):
    source = _write(
        tmp_path / "decisions.txt",
        "political_actions = {\n"
        "\tTEST_decision = {\n"
        "\t\tcost = 50\n"
        "\t\tcomplete_effect = { add_political_power = 1 }\n"
        "\t}\n"
        "}\n",
    )

    keys, kinds = loc.readfile(str(source))

    assert "TEST_decision" in keys
    assert "TEST_decision_desc" in keys
    assert "political_actions" in keys
    assert kinds[3] is True


def test_readfile_defaults_to_categories_without_decision_markers(tmp_path):
    source = _write(
        tmp_path / "categories.txt",
        "# header comment before any block\nTEST_category = {\n\ticon = generic\n}\n",
    )

    keys, _kinds = loc.readfile(str(source))

    assert keys == ["TEST_category", "TEST_category_desc"]


def test_main_tags_every_generated_line_with_todo(tmp_path, monkeypatch):
    source = _write(
        tmp_path / "focus.txt",
        "focus_tree = {\n"
        "\tfocus = {\n\t\tid = TEST_one\n\t}\n"
        "\tfocus = {\n\t\tid = TEST_two\n\t}\n"
        "}\n",
    )
    output = tmp_path / "output.yml"
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(output), "--todo"])

    loc.main()

    lines = output.read_text(encoding="utf-8-sig").splitlines()
    assert lines.count(" #TODO") == 4
    assert ' TEST_one: "Test One "' in lines
    assert ' TEST_one_desc: "Test One Desc "' in lines


def test_main_drops_sprite_tokens_from_generated_names(tmp_path, monkeypatch, capsys):
    source = _write(
        tmp_path / "focus.txt",
        "focus_tree = {\n\tfocus = {\n\t\tid = SPR_banner\n\t}\n}\n",
    )
    output = tmp_path / "output.yml"
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(output)])

    loc.main()

    assert ' SPR_banner: "Banner "' in output.read_text(encoding="utf-8-sig")
    assert "hah pink shirt" in capsys.readouterr().out


def test_main_fails_when_the_output_cannot_be_read(tmp_path, monkeypatch):
    source = _write(
        tmp_path / "focus.txt",
        "focus_tree = {\n\tfocus = {\n\t\tid = TEST_focus\n\t}\n}\n",
    )
    unreadable = tmp_path / "output-dir"
    unreadable.mkdir()
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(unreadable)])

    with pytest.raises(SystemExit, match="Could not read file"):
        loc.main()


def test_script_entry_point_requires_both_arguments(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["loc.py"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(TOOLS_DIR / "loc.py"), run_name="__main__")

    assert exit_info.value.code == 2
