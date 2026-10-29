"""Logging tool: the add and remove pass of each processor, the block helpers
and the CLI."""

import runpy
import sys

import logging_tool
import pytest
from shared.paths import TOOLS_DIR
from shared.suite import write_text

_LOG = 'log = "[GetDateText]: [Root.GetName]: '
_ANY_LOG = 'log = "[GetDateText]'


def _padded(text):
    return text + "# padding to clear the 100 byte floor\n" * 4


def _read(path):
    return path.read_text(encoding="utf-8")


# ---- output and read helpers -------------------------------------------------


def test_idea_add_fails_when_output_cannot_be_written(tmp_path, monkeypatch, capsys):
    write_text(
        tmp_path / "common/ideas/ideas.txt",
        _padded(
            "ideas = {\n\tcountry = {\n\t\tidea_one = {\n\t\t\ton_add = {\n"
            "\t\t\t\tadd_political_power = 1\n\t\t\t}\n\t\t}\n\t}\n}\n"
        ),
    )
    real_open = open

    def fail_write(path, mode="r", *args, **kwargs):
        if "w" in mode:
            raise OSError("read-only")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(logging_tool, "open", fail_write, raising=False)

    with pytest.raises(OSError, match="read-only"):
        logging_tool.idea_add(str(tmp_path))
    assert "Could not write ideas.txt" in capsys.readouterr().out


def test_atomic_output_is_written_when_the_wrapped_function_fails(tmp_path):
    output = tmp_path / "atomic.txt"

    @logging_tool._flush_atomic_outputs
    def write_then_fail():
        handle = logging_tool.open(output, "w", encoding="utf-8", newline="")
        handle.write("saved before failure\n")
        raise RuntimeError("expected failure")

    with pytest.raises(RuntimeError, match="expected failure"):
        write_then_fail()

    assert _read(output) == "saved before failure\n"
    assert logging_tool._pending_outputs == []


# case: (file contents, or None for a missing file; size floor; lines read)
@pytest.mark.parametrize(
    ("contents", "floor", "lines"),
    [
        ("first\nsecond\n", 1, ["first\n", "second\n"]),
        ("first\nsecond\n", 100, None),
        (None, 1, None),
    ],
    ids=["at the floor", "below the floor", "missing file"],
)
def test_quiet_read_returns_lines_only_for_a_readable_file_at_the_floor(
    tmp_path, contents, floor, lines
):
    source = tmp_path / "source.txt"
    if contents is not None:
        write_text(source, contents)

    assert logging_tool._read_lines_if_large_enough(source, min_size=floor) == lines


def test_warning_read_rejects_a_file_below_the_size_floor(tmp_path):
    source = write_text(tmp_path / "tiny.txt", "x\n")

    assert logging_tool._read_lines_or_warn(source, "tiny.txt") is None


# ---- block helpers -----------------------------------------------------------


@pytest.mark.parametrize(
    ("level", "line", "after"),
    [(0, "{ nested { } }\n", 0), (1, 'log = "}"\n', 1)],
    ids=["balanced", "brace in a string"],
)
def test_brace_level_ignores_braces_inside_strings(level, line, after):
    assert logging_tool._update_brace_level(level, line) == after


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


# ---- focuses -----------------------------------------------------------------


def test_focus_add_then_remove_logs_each_reward_that_runs_something(tmp_path):
    focus_dir = tmp_path / "common" / "national_focus"
    source = write_text(
        focus_dir / "focuses.txt",
        _padded("""focus_tree = {
\tfocus = {
\t\tid = TEST_regular
\t\tcompletion_reward = {
\t\t\tadd_political_power = 1
\t\t}
\t}
\tfocus = {
\t\tid = TEST_orphan
\t}
\tfocus = {
\t\tid = TEST_inline
\t\tcompletion_reward = { add_political_power = 3 }
\t}
\tfocus = {
\t\tid = TEST_logged
\t\tcompletion_reward = {
\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus TEST_logged"
\t\t\tadd_political_power = 4
\t\t}
\t}
\tfocus = {
\t\tid = TEST_dead
\t\tcompletion_reward = {
\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus TEST_dead"
\t\t}
\t}
}
shared_focus = {
\tid = TEST_shared # inline id comment
\tcompletion_reward = { add_political_power = 2 }
}
"""),
    )
    write_text(focus_dir / "short.txt", "focus = {\n")
    write_text(focus_dir / "notes.md", "focus = {\n")
    before = _read(source)

    assert logging_tool.focus_add(tmp_path, dry_run=True) == 3
    assert _read(source) == before
    assert logging_tool.focus_add(tmp_path) == 3

    content = _read(source)
    assert content.count(_LOG + "Focus ") == 5
    assert (
        "\t\tcompletion_reward = {\n"
        f'\t\t\t{_LOG}Focus TEST_regular"\n'
        "\t\t\tadd_political_power = 1\n"
    ) in content
    assert (
        "\t\tcompletion_reward = {\n"
        f'\t\t\t{_LOG}Focus TEST_inline"\n'
        "\t\t\tadd_political_power = 3\n"
        "\t\t}\n"
    ) in content
    assert (
        "\tcompletion_reward = {\n"
        f'\t\t{_LOG}Focus TEST_shared"\n'
        "\t\tadd_political_power = 2\n"
        "\t}\n"
    ) in content
    assert "TEST_orphan" in content
    assert content.count("Focus TEST_dead") == 1
    assert logging_tool.focus_add(tmp_path) == 0

    assert logging_tool.focus_remove(tmp_path) == 5
    removed = _read(source)
    assert _LOG + "Focus " not in removed
    assert "add_political_power = 1" in removed


def test_focus_add_skips_dead_blocks_and_quoted_ids(tmp_path):
    source = write_text(
        tmp_path / "common" / "national_focus" / "focuses.txt",
        _padded(
            "focus_tree = {\n"
            "\tfocus = {\n"
            "\t\tcost = 1\n"
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
    content = _read(source)
    # A '#' inside quotes is part of the id, not an inline comment.
    assert 'Focus "TEST#quoted"' in content
    assert content.count("[GetDateText]") == 1
    assert "\t\tcompletion_reward = {\n\t\t}\n" in content


# ---- events ------------------------------------------------------------------


def test_event_add_then_remove_handles_a_bom_and_packed_immediates(tmp_path):
    # Event files start with a byte-order mark.
    source = write_text(
        tmp_path / "events" / "events.txt",
        "﻿" + _padded("""country_event = {
\tid = TEST.1
\ttitle = test_title
\timmediate = {
\t\tset_country_flag = one
\t}
\toption = { name = test_option }
}
news_event = {
\tid = PLAIN_ID
\timmediate = { hidden_effect = { set_country_flag = two } }
}
unit_leader_event = {
\tid = TEST.2
\tdays = 2
}
state_event = {
\tid = TEST.3
\timmediate = {
\t}
\toption = { name = state_option }
}
country_event = {
\tid = TEST.4
\timmediate = {
\t\tlog = "[GetDateText]: [Root.GetName]: event TEST.4"
\t}
}
"""),
    )

    assert logging_tool.event_add(tmp_path) == 2
    content = _read(source)
    assert content.count(_ANY_LOG) == 3
    assert (
        "\timmediate = {\n" f'\t\t{_LOG}event TEST.1"\n' "\t\tset_country_flag = one\n"
    ) in content
    assert (
        "\timmediate = {\n"
        f'\t\t{_LOG}event PLAIN_ID"\n'
        "\t\thidden_effect = { set_country_flag = two }\n"
        "\t}\n"
    ) in content
    assert "\timmediate = {\n\t}\n" in content
    assert logging_tool.event_add(tmp_path) == 0

    assert logging_tool.event_remove(tmp_path) == 3
    removed = _read(source)
    assert _ANY_LOG not in removed
    assert "set_country_flag = one" in removed


def test_event_add_targets_only_immediate_blocks_that_run_something(tmp_path):
    events = tmp_path / "events"
    source = write_text(
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
    write_text(events / "notes.md", _padded("country_event = {\n"))
    write_text(events / "small.txt", "country_event = {\n")
    (events / "broken.txt").write_bytes(b"\xff" * 200)

    assert logging_tool.event_add(tmp_path) == 1
    content = _read(source)
    assert "\tid = TEST.1 # inline note\n" in content
    assert (
        "\timmediate = {\n" f'\t\t{_LOG}event TEST.1"\n' "\t\tset_country_flag = t1\n"
    ) in content
    assert content.count("[GetDateText]") == 2
    assert _read(events / "small.txt") == "country_event = {\n"
    assert (events / "broken.txt").read_bytes() == b"\xff" * 200


def test_event_remove_skips_unreadable_and_undersized_files(tmp_path, capsys):
    events = tmp_path / "events"
    write_text(events / "notes.md", _padded('log = "[GetDateText]: x"\n'))
    write_text(events / "small.txt", 'log = "[GetDateText]: x"\n')
    (events / "broken.txt").write_bytes(b"\xff" * 200)

    assert logging_tool.event_remove(tmp_path) == 0
    assert "broken.txt" in capsys.readouterr().out
    assert _read(events / "small.txt") == 'log = "[GetDateText]: x"\n'


# ---- ideas -------------------------------------------------------------------


def test_idea_add_then_remove_keeps_comments_and_skips_helper_files(tmp_path):
    ideas_dir = tmp_path / "common" / "ideas"
    source = write_text(
        ideas_dir / "ideas.txt",
        _padded("""ideas = {
\tcategory = {
\t\tTEST_idea = { # keep this comment
\t\t\tname = TEST_idea
\t\t\ton_add = { # keep this too
\t\t\t\tset_country_flag = on
\t\t\t}
\t\t\ton_remove = { clr_country_flag = on }
\t\t}
\t\tTEST_dead = {
\t\t\ton_add = { }
\t\t\ton_remove = {
\t\t\t\tlog = "[GetDateText]: [Root.GetName]: remove idea TEST_dead"
\t\t\t}
\t\t}
\t}
}
"""),
    )
    helper = write_text(ideas_dir / "_helper.txt", _padded("helper = {\n"))
    write_text(ideas_dir / "small.txt", "ideas = {\n")

    assert logging_tool.idea_add(tmp_path) == 2
    content = _read(source)
    assert "TEST_idea = { # keep this comment" in content
    assert (
        "\t\t\ton_add = { # keep this too\n"
        f'\t\t\t\t{_LOG}add idea TEST_idea"\n'
        "\t\t\t\tset_country_flag = on\n"
    ) in content
    assert (
        "\t\t\ton_remove = {\n"
        f'\t\t\t\t{_LOG}remove idea TEST_idea"\n'
        "\t\t\t\tclr_country_flag = on\n"
        "\t\t\t}\n"
    ) in content
    assert "\t\t\ton_add = { }\n" in content
    assert content.count("TEST_dead") == 2
    assert logging_tool.idea_add(tmp_path) == 0

    assert logging_tool.idea_remove(tmp_path) == 3
    assert _ANY_LOG not in _read(source)
    assert _ANY_LOG not in _read(helper)


def test_idea_remove_reports_an_unreadable_entry(tmp_path, capsys):
    (tmp_path / "common" / "ideas" / "broken.txt").mkdir(parents=True)

    assert logging_tool.idea_remove(tmp_path) == 0
    assert "Could not read broken.txt" in capsys.readouterr().out


# ---- decisions ---------------------------------------------------------------


def test_decision_add_then_remove_logs_each_effect_and_names_the_target(tmp_path):
    decisions_dir = tmp_path / "common" / "decisions"
    source = write_text(
        decisions_dir / "decisions.txt",
        _padded("""decision_category = {
\tTEST_decision = {
\t\ttarget_trigger = { always = yes }
\t\tcomplete_effect = { add_political_power = 1 }
\t\tremove_effect = {
\t\t\tadd_political_power = -1
\t\t}
\t\ttimeout_effect = { add_political_power = 2 }
\t}
\tTEST_plain = { # inline note
\t\tcomplete_effect = {
\t\t\tadd_political_power = 5
\t\t}
\t}
\tTEST_no_effect = {
\t\tvisible = { always = yes }
\t\tcomplete_effect = {
\t\t}
\t\tremove_effect = { log = "[GetDateText]: [Root.GetName]: Decision remove TEST_no_effect" }
\t}
}
"""),
    )
    categories = write_text(decisions_dir / "categories.txt", _padded("category = {\n"))
    write_text(decisions_dir / "empty.txt", _padded("# no decisions here\n"))

    assert logging_tool.decision_add(tmp_path) == 4
    content = _read(source)
    assert content.count("Decision TEST_decision target: [From.GetName]") == 1
    assert content.count("Decision remove TEST_decision target: [From.GetName]") == 1
    assert (
        "\t\ttimeout_effect = {\n"
        f'\t\t\t{_LOG}Decision timeout TEST_decision target: [From.GetName]"\n'
        "\t\t\tadd_political_power = 2\n"
        "\t\t}\n"
    ) in content
    # Only a targeted decision names its target.
    assert "\tTEST_plain = { # inline note\n" in content
    assert f'{_LOG}Decision TEST_plain"\n' in content
    assert "\t\tcomplete_effect = {\n\t\t}\n" in content
    assert content.count("TEST_no_effect") == 2
    assert _read(categories) == _padded("category = {\n")
    assert logging_tool.decision_add(tmp_path) == 0

    with open(source, "a", encoding="utf-8", newline="") as handle:
        handle.write('log = "[GetDateText]: complete_effect regression"\n')
    assert logging_tool.decision_remove(tmp_path) == 6
    removed = _read(source)
    assert _LOG + "Decision" not in removed
    assert "complete_effect = {\n\t\t}\n" in removed


def test_decision_add_skips_entries_it_cannot_size_or_decode(
    tmp_path, monkeypatch, capsys
):
    decisions = tmp_path / "common" / "decisions"
    write_text(decisions / "notes.md", _padded("decision_category = {\n"))
    write_text(decisions / "tiny.txt", "decision_category = {\n")
    write_text(decisions / "vanished.txt", _padded("decision_category = {\n"))
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


def test_decision_remove_skips_an_undersized_file(tmp_path):
    tiny = write_text(
        tmp_path / "common/decisions/tiny.txt", 'log = "[GetDateText]: keep me"\n'
    )

    assert logging_tool.decision_remove(tmp_path) == 0
    assert _read(tiny) == 'log = "[GetDateText]: keep me"\n'


# ---- technologies ------------------------------------------------------------


def test_tech_add_then_remove_handles_generated_and_legacy_logs(tmp_path, capsys):
    tech_dir = tmp_path / "common" / "technologies"
    source = write_text(
        tech_dir / "technologies.txt",
        _padded("""technologies = {
\tTEST_tech = { # technology comment
\t\ton_research_complete = { # effect comment
\t\t\tset_country_flag = researched
\t\t}
\t}
\tTEST_second = {
\t\ton_research_complete = { set_country_flag = second }
\t}
\tTEST_silent = {
\t\tname = TEST_silent
\t}
\tTEST_dead = {
\t\ton_research_complete = {
\t\t\tlog = "[GetDateText]: [Root.GetName]: add tech TEST_dead"
\t\t}
\t}
}
"""),
    )

    assert logging_tool.tech_add(tmp_path) == 2
    content = _read(source)
    assert content.count("add tech TEST_") == 3
    assert "TEST_tech = { # technology comment" in content
    assert (
        "\t\ton_research_complete = { # effect comment\n"
        f'\t\t\t{_LOG}add tech TEST_tech"\n'
        "\t\t\tset_country_flag = researched\n"
    ) in content
    assert (
        "\t\ton_research_complete = {\n"
        f'\t\t\t{_LOG}add tech TEST_second"\n'
        "\t\t\tset_country_flag = second\n"
        "\t\t}\n"
    ) in content
    assert "on_research_complete" not in content.split("TEST_silent")[1].split("}")[0]
    assert logging_tool.tech_add(tmp_path) == 0

    legacy = write_text(
        tech_dir / "legacy.txt",
        _padded("""technologies = {
\tLEGACY = {
\t\ton_research_complete = {
\t\t\tlog = "[GetDateText]: [Root.GetName]: legacy"
\t\t}
\t}
}
"""),
    )
    assert logging_tool.tech_remove(tmp_path) == 8
    assert "Deleted logging at line" in capsys.readouterr().out
    assert _ANY_LOG not in _read(source)
    assert _ANY_LOG not in _read(legacy)


def test_tech_helpers_skip_non_txt_and_undersized_files(tmp_path):
    tech = tmp_path / "common" / "technologies"
    write_text(tech / "notes.md", _padded("technologies = {\n"))
    small = write_text(tech / "small.txt", "technologies = {\n")

    assert logging_tool.tech_add(tmp_path) == 0
    assert logging_tool.tech_remove(tmp_path) == 0
    assert _read(small) == "technologies = {\n"


# ---- the CLI -----------------------------------------------------------------

_SKIP_ALL = [
    "--skip-events",
    "--skip-focus",
    "--skip-ideas",
    "--skip-decisions",
    "--skip-tech",
]


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


def test_main_reports_a_dry_run_removal_with_every_processor_skipped(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["logging_tool.py", str(tmp_path), "--remove", "--dry-run", *_SKIP_ALL],
    )

    logging_tool.main()

    output = capsys.readouterr().out
    assert f"Processing mod at: {tmp_path}" in output
    assert "Mode: Removing logs (dry run)" in output
    assert "Would modify 0 entries" in output
    assert "Processing events..." not in output


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
