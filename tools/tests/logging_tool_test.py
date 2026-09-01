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
        "ideas = {\n\tidea_one = {\n\t\tname = idea_one\n\t}\n}\n" + "# filler\n" * 20,
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


def test_find_log_targets_skips_entities_that_already_log():
    lines = [
        "ideas = {\n",
        "\tcountry = {\n",
        "\t\tlogged = {\n",
        '\t\t\ton_add = { log = "already there" }\n',
        "\t\t}\n",
        "\t\tunlogged = {\n",
        "\t\t\tname = unlogged\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ]

    assert logging_tool._find_log_targets(
        lines, depth=2, log_prefix="on_add = { log = "
    ) == [6]


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param(["a\n", "b\n", "}\n", "c\n", "d\n"], id="two-lines-ahead"),
        pytest.param(["a\n", "}\n", "c\n", "d\n", "e\n"], id="next-line"),
        pytest.param(["a\n", "# c\n", "\n", "\n", "}\n", "x\n"], id="after-blanks"),
    ],
)
def test_check_triggered_detects_a_close_brace_at_every_lookahead(lines):
    assert logging_tool.check_triggered(1, lines)


def test_focus_add_handles_preexisting_logs_and_unnamed_focuses(tmp_path):
    source = _write(
        tmp_path / "common" / "national_focus" / "focuses.txt",
        _padded(
            'log = "[GetDateText]: stray log before any focus"\n'
            "focus = {\n"
            "\tid = {\n"
            "\tcompletion_reward = {\n"
            "\t\tadd_political_power = 1\n"
            "\t}\n"
            "}\n"
            "focus = {\n"
            '\tid = "TEST#quoted"\n'
            "\tcompletion_reward = {\n"
            "\t\tadd_political_power = 2\n"
            "\t}\n"
            "}\n"
        ),
    )

    assert logging_tool.focus_add(tmp_path) == 2
    content = source.read_text(encoding="utf-8")
    assert "Focus Error, focus name not found" in content
    # A '#' inside quotes is part of the id, not an inline comment.
    assert 'Focus "TEST#quoted"' in content


def test_event_add_keeps_inline_comments_and_leaves_logged_events_alone(tmp_path):
    events = tmp_path / "events"
    source = _write(
        events / "events.txt",
        _padded(
            "country_event = {\n"
            "\tid = TEST.1 # inline note\n"
            "\ttitle = t1\n"
            "\tdesc = d1\n"
            "\toption = { name = o1 }\n"
            "}\n"
            "news_event = {\n"
            "\tid = TEST.2\n"
            "\ttitle = t2\n"
            '\tlog = "manual"\n'
            "\tdesc = d2\n"
            "}\n"
            "unit_leader_event = { days = 3 }\n"
            "filler_a = x\n"
            "filler_b = y\n"
            "filler_c = z\n"
        ),
    )
    _write(events / "notes.md", _padded("country_event = {\n"))
    _write(events / "small.txt", "country_event = {\n")
    (events / "broken.txt").write_bytes(b"\xff" * 200)

    assert logging_tool.event_add(tmp_path) == 1
    content = source.read_text(encoding="utf-8")
    assert "\tid = TEST.1 #inline note\n" in content
    assert (
        '\timmediate = {log = "[GetDateText]: [Root.GetName]: event TEST.1"}\n'
        in content
    )
    # TEST.2 already carries a log line, so it must not gain a second one.
    assert content.count("immediate = {log =") == 1
    assert (events / "small.txt").read_text(encoding="utf-8") == "country_event = {\n"


def test_event_add_skips_the_event_after_a_triggered_only_one(tmp_path):
    source = _write(
        tmp_path / "events" / "events.txt",
        _padded(
            "country_event = {\n"
            "\tid = TEST.9\n"
            "\tdays = 2\n"
            "}\n"
            "news_event = {\n"
            "\tid = TEST.8\n"
            "\ttitle = t\n"
            "\tdesc = d\n"
            "\toption = { name = o }\n"
            "}\n"
        ),
    )

    assert logging_tool.event_add(tmp_path) == 0
    assert "immediate = {log =" not in source.read_text(encoding="utf-8")


def test_event_remove_skips_unreadable_and_undersized_files(tmp_path, capsys):
    events = tmp_path / "events"
    _write(events / "notes.md", _padded('immediate = {log = "x"}\n'))
    _write(events / "small.txt", 'immediate = {log = "x"}\n')
    (events / "broken.txt").write_bytes(b"\xff" * 200)

    assert logging_tool.event_remove(tmp_path) == 0
    assert "broken.txt" in capsys.readouterr().out
    assert (events / "small.txt").read_text(encoding="utf-8") == (
        'immediate = {log = "x"}\n'
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
    assert "add_political_power = -1 }" in content


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
    assert "Could not read" in out
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
