"""Failure handling and edge-case tests for the logging tool."""

import runpy
import sys

import logging_tool
import pytest
from shared.paths import TOOLS_DIR


def test_idea_add_fails_when_output_cannot_be_written(tmp_path, monkeypatch):
    ideas = tmp_path / "common" / "ideas"
    ideas.mkdir(parents=True)
    source = ideas / "ideas.txt"
    source.write_text(
        "ideas = {\n\tcountry = {\n\t\tidea_one = {\n\t\t\ton_add = {\n"
        "\t\t\t\tadd_political_power = 1\n\t\t\t}\n\t\t}\n\t}\n}\n" + "# filler\n" * 20,
        encoding="utf-8",
    )
    real_open = open

    def fail_write(path, mode="r", *args, **kwargs):
        if "w" in mode:
            raise OSError("read-only")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(logging_tool, "open", fail_write, raising=False)

    try:
        logging_tool.idea_add(str(tmp_path))
    except OSError as error:
        assert "read-only" in str(error)
    else:
        assert False, "idea_add should fail when the output cannot be written"


def _write(path, text, encoding="utf-8"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=encoding, newline="") as handle:
        handle.write(text)
    return path


def _padded(text):
    return text + "# padding to clear the 100 byte floor\n" * 4


def test_read_helpers_reject_a_file_below_the_size_floor(tmp_path):
    source = _write(tmp_path / "tiny.txt", "x\n")

    assert logging_tool._read_lines_or_warn(source, "tiny.txt") is None


@pytest.mark.parametrize(
    "block,expected",
    [
        pytest.param(["\ton_add = { }\n"], False, id="empty-packed"),
        pytest.param(["\ton_add = {\n", "\t}\n"], False, id="empty-multiline"),
        pytest.param(
            ["\ton_add = {\n", "\t\t# note\n", "\t}\n"], False, id="comment-only"
        ),
        pytest.param(['\ton_add = { log = "x" }\n'], False, id="log-only-packed"),
        pytest.param(
            ["\ton_add = {\n", '\t\tlog = "x"\n', "\t}\n"],
            False,
            id="log-only-multiline",
        ),
        pytest.param(
            ["\ton_add = { add_political_power = 1 }\n"], True, id="content-packed"
        ),
        pytest.param(
            ["\ton_add = {\n", "\t\tadd_political_power = 1\n", "\t}\n"],
            True,
            id="content-multiline",
        ),
        pytest.param(
            ["\ton_add = {\n", "\t\tadd_political_power = 1 }\n"],
            True,
            id="content-on-closer",
        ),
        pytest.param(
            [
                "\ton_add = {\n",
                '\t\tlog = "x"\n',
                "\t\tadd_political_power = 1\n",
                "\t}\n",
            ],
            False,
            id="logged-multiline",
        ),
        pytest.param(
            ['\ton_add = { log = "x" remove_ideas = { y } }\n'],
            False,
            id="logged-packed",
        ),
        pytest.param(
            ["\ton_add = {\n", "\t\tadd_political_power = 1\n"], False, id="unclosed"
        ),
    ],
)
def test_needs_log_only_for_a_block_that_runs_something_unlogged(block, expected):
    assert logging_tool._needs_log(block) is expected


def test_logged_opener_keeps_comments_and_explodes_packed_blocks():
    assert logging_tool._logged_opener("\t\ton_add = { # note\n", "add idea x") == (
        "\t\ton_add = { # note\n"
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: add idea x"\n'
    )
    assert logging_tool._logged_opener(
        "\t\ton_add = { set_variable = { a = 1 } } # note\n", "add idea x"
    ) == (
        "\t\ton_add = { # note\n"
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: add idea x"\n'
        "\t\t\tset_variable = { a = 1 }\n"
        "\t\t}\n"
    )


def test_focus_add_skips_dead_blocks_and_quoted_ids(tmp_path):
    source = _write(
        tmp_path / "common" / "national_focus" / "focuses.txt",
        _padded(
            "focus_tree = {\n"
            "\tfocus = {\n"
            "\t\tcompletion_reward = {\n"
            "\t\t\tadd_political_power = 1\n"
            "\t\t}\n"
            "\t}\n"
            "\tfocus = {\n"
            '\t\tid = "TEST#quoted"\n'
            "\t\tcompletion_reward = {\n"
            "\t\t\tadd_political_power = 2\n"
            "\t\t}\n"
            "\t}\n"
            "\tfocus = {\n"
            "\t\tid = TEST_empty\n"
            "\t\tcompletion_reward = {\n"
            "\t\t}\n"
            "\t}\n"
            "}\n"
        ),
    )

    assert logging_tool.focus_add(tmp_path) == 1
    content = source.read_text(encoding="utf-8")
    # A '#' inside quotes is part of the id, not an inline comment.
    assert 'Focus "TEST#quoted"' in content
    assert content.count("[GetDateText]") == 1
    assert "\t\tcompletion_reward = {\n\t\t}\n" in content


def test_event_add_targets_only_immediate_blocks_that_run_something(tmp_path):
    events = tmp_path / "events"
    source = _write(
        events / "events.txt",
        _padded(
            "country_event = {\n"
            "\tid = TEST.1 # inline note\n"
            "\ttitle = t1\n"
            "\timmediate = {\n"
            "\t\tset_country_flag = t1\n"
            "\t}\n"
            "\toption = {\n"
            "\t\tname = o1\n"
            "\t\tcountry_event = {\n"
            "\t\t\tid = TEST.2\n"
            "\t\t\tdays = 3\n"
            "\t\t}\n"
            "\t}\n"
            "}\n"
            "news_event = {\n"
            "\tid = TEST.2\n"
            "\timmediate = {\n"
            '\t\tlog = "manual"\n'
            "\t\tset_country_flag = t2\n"
            "\t}\n"
            "}\n"
            "news_event = {\n"
            "\tid = TEST.3\n"
            '\timmediate = { log = "[GetDateText]: dead" }\n'
            "}\n"
            "unit_leader_event = { id = TEST.4 days = 3 }\n"
        ),
    )
    _write(events / "notes.md", _padded("country_event = {\n"))
    _write(events / "small.txt", "country_event = {\n")
    (events / "broken.txt").write_bytes(b"\xff" * 200)

    assert logging_tool.event_add(tmp_path) == 1
    content = source.read_text(encoding="utf-8")
    assert "\tid = TEST.1 # inline note\n" in content
    assert (
        "\timmediate = {\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: event TEST.1"\n'
        "\t\tset_country_flag = t1\n"
    ) in content
    assert content.count("[GetDateText]") == 2
    assert (events / "small.txt").read_text(encoding="utf-8") == "country_event = {\n"
    assert (events / "broken.txt").read_bytes() == b"\xff" * 200


def test_event_remove_skips_unreadable_and_undersized_files(tmp_path, capsys):
    events = tmp_path / "events"
    _write(events / "notes.md", _padded('log = "[GetDateText]: x"\n'))
    _write(events / "small.txt", 'log = "[GetDateText]: x"\n')
    (events / "broken.txt").write_bytes(b"\xff" * 200)

    assert logging_tool.event_remove(tmp_path) == 0
    assert "broken.txt" in capsys.readouterr().out
    assert (events / "small.txt").read_text(encoding="utf-8") == (
        'log = "[GetDateText]: x"\n'
    )


def test_idea_remove_reports_an_unreadable_entry(tmp_path, capsys):
    (tmp_path / "common" / "ideas" / "broken.txt").mkdir(parents=True)

    assert logging_tool.idea_remove(tmp_path) == 0
    assert "Could not read broken.txt" in capsys.readouterr().out


def test_decision_add_covers_single_and_multi_line_effect_blocks(tmp_path):
    source = _write(
        tmp_path / "common" / "decisions" / "decisions.txt",
        _padded(
            "decision_category = {\n"
            "\tTEST_alpha = { # inline note\n"
            "\t\tcomplete_effect = {\n"
            "\t\t\tadd_political_power = 1\n"
            "\t\t}\n"
            "\t\tremove_effect = { add_political_power = -1 }\n"
            "\t\ttimeout_effect = {\n"
            "\t\t\tadd_political_power = 2\n"
            "\t\t}\n"
            "\t}\n"
            "}\n"
        ),
    )

    assert logging_tool.decision_add(tmp_path) == 3
    content = source.read_text(encoding="utf-8")
    assert 'log = "[GetDateText]: [Root.GetName]: Decision TEST_alpha"' in content
    assert (
        'log = "[GetDateText]: [Root.GetName]: Decision remove TEST_alpha"' in content
    )
    assert (
        'log = "[GetDateText]: [Root.GetName]: Decision timeout TEST_alpha"' in content
    )
    assert (
        "\t\tremove_effect = {\n"
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision remove TEST_alpha"\n'
        "\t\t\tadd_political_power = -1\n"
        "\t\t}\n"
    ) in content
    assert logging_tool.decision_add(tmp_path) == 0


def test_decision_add_skips_entries_it_cannot_size_or_decode(
    tmp_path, monkeypatch, capsys
):
    decisions = tmp_path / "common" / "decisions"
    _write(decisions / "notes.md", _padded("decision_category = {\n"))
    _write(decisions / "tiny.txt", "decision_category = {\n")
    _write(decisions / "vanished.txt", _padded("decision_category = {\n"))
    (decisions / "badenc.txt").write_bytes(b"\xff" * 200)

    real_getsize = logging_tool.os.path.getsize

    def flaky_getsize(path):
        if str(path).endswith("vanished.txt"):
            raise OSError("stale file handle")
        return real_getsize(path)

    monkeypatch.setattr(logging_tool.os.path, "getsize", flaky_getsize)

    assert logging_tool.decision_add(tmp_path) == 0
    out = capsys.readouterr().out
    assert "Could not read vanished.txt" in out
    assert "Could not read badenc.txt" in out
    assert (decisions / "badenc.txt").read_bytes() == b"\xff" * 200


def test_decision_remove_skips_an_undersized_file(tmp_path, capsys):
    decisions = tmp_path / "common" / "decisions"
    _write(decisions / "tiny.txt", 'log = "[GetDateText]: keep me"\n')

    assert logging_tool.decision_remove(tmp_path) == 0
    assert (decisions / "tiny.txt").read_text(encoding="utf-8") == (
        'log = "[GetDateText]: keep me"\n'
    )


def test_tech_helpers_skip_non_txt_and_undersized_files(tmp_path):
    tech = tmp_path / "common" / "technologies"
    _write(tech / "notes.md", _padded("technologies = {\n"))
    _write(tech / "small.txt", "technologies = {\n")

    assert logging_tool.tech_add(tmp_path) == 0
    assert logging_tool.tech_remove(tmp_path) == 0
    assert (tech / "small.txt").read_text(encoding="utf-8") == "technologies = {\n"


def test_main_runs_every_processor_against_an_empty_mod(tmp_path, monkeypatch, capsys):
    for relative in (
        "events",
        "common/national_focus",
        "common/ideas",
        "common/decisions",
        "common/technologies",
    ):
        (tmp_path / relative).mkdir(parents=True)
    monkeypatch.setattr(sys, "argv", ["logging_tool.py", str(tmp_path)])

    logging_tool.main()

    output = capsys.readouterr().out
    for step in ("events", "national focus", "ideas", "decisions", "technologies"):
        assert f"Processing {step}..." in output
    assert "Mode: Adding logs\n" in output
    assert "Modified 0 entries" in output


_SKIP_ALL = [
    "--skip-events",
    "--skip-focus",
    "--skip-ideas",
    "--skip-decisions",
    "--skip-tech",
]


@pytest.mark.parametrize(
    "leading,trailing",
    [
        pytest.param([], _SKIP_ALL, id="path-first"),
        pytest.param(["--dry-run"], _SKIP_ALL, id="flag-first"),
        pytest.param(_SKIP_ALL + ["--dry-run"], [], id="path-last"),
    ],
)
def test_main_rejoins_a_path_argparse_split_on_spaces(
    monkeypatch, capsys, leading, trailing
):
    missing = "/nonexistent/mod path"
    monkeypatch.setattr(
        sys, "argv", ["logging_tool.py"] + leading + [missing] + trailing
    )

    logging_tool.main()

    assert f"Processing mod at: {missing}" in capsys.readouterr().out


def test_script_entry_point_requires_a_mod_path(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["logging_tool.py"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(TOOLS_DIR / "logging_tool.py"), run_name="__main__")

    assert exit_info.value.code == 2
