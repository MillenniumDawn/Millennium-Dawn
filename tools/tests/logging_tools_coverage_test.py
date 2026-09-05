"""Branch coverage for the logging and game-log summary tools."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import logging_tool
import pytest
import summarize_game_log


def write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=encoding, newline="") as handle:
        handle.write(content)


def padded(content: str) -> str:
    return content + "# coverage filler\n" * 12


def test_logging_helpers_cover_io_comments_and_trigger_boundaries(
    tmp_path, capsys, monkeypatch
):
    source = tmp_path / "source.txt"
    write_text(source, "first\nsecond\n")
    assert logging_tool._read_lines(source) == ["first\n", "second\n"]
    assert logging_tool._read_lines_if_large_enough(source, min_size=1) == [
        "first\n",
        "second\n",
    ]
    assert logging_tool._read_lines_if_large_enough(source, min_size=100) is None
    assert logging_tool._read_lines_or_warn(source, "source.txt", min_size=1) == [
        "first\n",
        "second\n",
    ]
    missing = tmp_path / "missing.txt"
    assert logging_tool._read_lines(missing) is None
    assert logging_tool._read_lines_if_large_enough(missing) is None
    assert logging_tool._read_lines_or_warn(missing, "missing.txt") is None
    assert "Could not read" in capsys.readouterr().out

    def fail_read(*args, **kwargs):
        raise UnicodeError("invalid source encoding")

    monkeypatch.setattr(logging_tool, "open", fail_read)
    assert logging_tool._read_lines(source) is None
    assert "invalid source encoding" in capsys.readouterr().out
    monkeypatch.undo()

    def fail_output(*args, **kwargs):
        raise OSError("read-only output")

    monkeypatch.setattr(logging_tool, "open", fail_output)
    with pytest.raises(OSError, match="read-only output"):
        logging_tool._open_output_or_raise(source, "source.txt", dry_run=False)
    assert "Could not write source.txt" in capsys.readouterr().out
    monkeypatch.undo()

    event = tmp_path / "event.txt"
    write_text(event, "event = {\n", encoding="utf-8-sig")
    assert logging_tool._read_event_lines(event, "event.txt") == ["event = {\n"]
    assert logging_tool._read_event_lines(missing, "missing.txt") is None
    assert "missing.txt" in capsys.readouterr().out

    directory = tmp_path / "directory"
    directory.mkdir()
    write_text(directory / "one.txt", "one\n")
    write_text(directory / "two.txt", "two\n")
    paths = dict(logging_tool._iter_directory_paths(tmp_path, "directory"))
    assert set(paths) == {"one.txt", "two.txt"}
    assert Path(paths["one.txt"]).read_text(encoding="utf-8") == "one\n"

    lines = [
        "ideas = {\n",
        "\tcategory = {\n",
        "\t\tone = { # preserve\n",
        "\t\t\tname = one\n",
        "\t\ttwo = {\n",
        '\t\t\ton_add = { log = "already" }\n',
        "\t\tthree = {\n",
        "\t\t\tname = three\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ]
    assert logging_tool._find_log_targets(
        lines, depth=2, log_prefix="on_add = { log = "
    ) == [3]
    assert logging_tool._added_log_block(
        "\t\tone = { # preserve\n",
        header_indent="\t\t",
        log_indent="\t\t\t",
        effect="on_add = { log =",
        entity_kind="idea",
    ) == (
        "\t\tone = { #preserve\n"
        '\t\t\ton_add = { log = "[GetDateText]: [Root.GetName]: add idea one" }\n'
    )
    assert logging_tool._added_log_block(
        "tech_one = {\n",
        header_indent="\t",
        log_indent="\t\t",
        effect="on_research_complete = {log =",
        entity_kind="tech",
    ).endswith('add tech tech_one" }\n')

    assert logging_tool._update_brace_level(0, "{ nested { } }\n") == 0
    assert logging_tool._update_brace_level(2, "no braces\n") == 2
    assert logging_tool.check_triggered(4, ["event = {\n"] * 4)
    assert logging_tool.check_triggered(3, ["event = {\n"] * 4)
    assert logging_tool.check_triggered(2, ["event = {\n"] * 4)
    assert logging_tool.check_triggered(
        1, ["event = {\n", "title = x\n", "days = 2\n", "}\n"]
    )
    assert logging_tool.check_triggered(
        1, ["event = {\n", "days = 2\n", "title = x\n", "}\n"]
    )
    assert logging_tool.check_triggered(
        2, ["event = {\n", "title = x\n", "}\n", "tail = x\n"]
    )
    assert logging_tool.check_triggered(1, ["event = {\n", "# comment\n", "\n", "}\n"])
    assert not logging_tool.check_triggered(
        1,
        [
            "event = {\n",
            "title = x\n",
            "other = x\n",
            "description = x\n",
            "}\n",
        ],
    )
    assert not logging_tool.check_triggered(
        1, ["event = {\n", "# comment\n", "\n", "\n"]
    )


def test_logging_atomic_flushes_even_when_wrapped_function_fails(tmp_path):
    output = tmp_path / "atomic.txt"

    @logging_tool._flush_atomic_outputs
    def write_then_fail():
        handle = logging_tool.open(output, "w", encoding="utf-8", newline="")
        handle.write("saved before failure\n")
        raise RuntimeError("expected failure")

    with pytest.raises(RuntimeError, match="expected failure"):
        write_then_fail()
    assert output.read_text(encoding="utf-8") == "saved before failure\n"
    assert logging_tool._pending_outputs == []


def test_focus_add_remove_and_dry_run(tmp_path):
    focus_dir = tmp_path / "common" / "national_focus"
    source = focus_dir / "focuses.txt"
    write_text(
        source,
        padded("""focus = {
\tid = TEST_regular
\tcompletion_reward = {
\t\tadd_political_power = 1
\t}
}
shared_focus = {
\tid = TEST_shared # inline id comment
\tcompletion_reward = { add_political_power = 2 }
}
focus = {
\tid = TEST_orphan
}
focus = {
\tid = TEST_inline
\tcompletion_reward = { add_political_power = 3 }
}
"""),
    )
    write_text(focus_dir / "short.txt", "focus = {\n")
    write_text(focus_dir / "notes.md", "focus = {\n")

    assert logging_tool.focus_add(tmp_path) == 3
    content = source.read_text(encoding="utf-8")
    assert content.count("[GetDateText]: [Root.GetName]: Focus ") == 3
    assert "Focus TEST_regular" in content
    assert "Focus TEST_shared" in content
    assert "Focus TEST_inline" in content
    assert "TEST_orphan" in content

    before = content
    assert logging_tool.focus_add(tmp_path, dry_run=True) == 0
    assert source.read_text(encoding="utf-8") == before
    assert logging_tool.focus_remove(tmp_path) == 3
    removed = source.read_text(encoding="utf-8")
    assert "[GetDateText]: [Root.GetName]: Focus " not in removed
    assert "add_political_power = 1" in removed


def test_event_add_remove_handles_bom_untriggered_and_malformed_ids(tmp_path):
    event_dir = tmp_path / "events"
    source = event_dir / "events.txt"
    write_text(
        source,
        padded("""country_event = {
\tid = TEST.1
\ttitle = test_title
\tdescription = test_description
\toption = { name = test_option }
}
news_event = {
\tid = PLAIN_ID
\ttitle = plain_title
\tdescription = plain_description
\toption = { name = plain_option }
}
immediate = {log = "existing log"}
unit_leader_event = {
\tid = TEST.2
\tdays = 2
}
state_event = {
\tid = TEST.3
\ttitle = state_title
\tdescription = state_description
\toption = { name = state_option }
}
"""),
        encoding="utf-8-sig",
    )

    assert logging_tool.event_add(tmp_path) == 2
    content = source.read_text(encoding="utf-8")
    assert content.count('immediate = {log = "[GetDateText]') == 2
    assert "id = TEST.1" in content
    assert "id = TEST.3" in content
    assert "id = PLAIN_ID\n" in content
    assert "id = TEST.2" in content

    with open(source, "a", encoding="utf-8", newline="") as handle:
        handle.write('\timmediate = {log = "unfinished log"\n')
    assert logging_tool.event_remove(tmp_path) == 4
    removed = source.read_text(encoding="utf-8")
    assert 'immediate = {log = "[GetDateText]' not in removed
    assert "\timmediate = {\n" in removed


def test_idea_add_remove_preserves_comments_and_skips_helpers(tmp_path):
    ideas_dir = tmp_path / "common" / "ideas"
    source = ideas_dir / "ideas.txt"
    write_text(
        source,
        padded("""ideas = {
\tcategory = {
\t\tTEST_idea = { # keep this comment
\t\t\tname = TEST_idea
\t\t}
\t}
}
"""),
    )
    write_text(ideas_dir / "_helper.txt", padded("helper = {\n"))
    write_text(ideas_dir / "small.txt", "ideas = {\n")

    assert logging_tool.idea_add(tmp_path) == 1
    content = source.read_text(encoding="utf-8")
    assert "TEST_idea = { #keep this comment" in content
    assert (
        'on_add = { log = "[GetDateText]: [Root.GetName]: add idea TEST_idea" }'
        in content
    )
    assert logging_tool.idea_remove(tmp_path) == 1
    assert 'on_add = { log = "[GetDateText]' not in source.read_text(encoding="utf-8")
    assert 'on_add = { log = "[GetDateText]' not in (
        ideas_dir / "_helper.txt"
    ).read_text(encoding="utf-8")


def test_decision_add_remove_covers_effect_shapes_and_targets(tmp_path):
    decisions_dir = tmp_path / "common" / "decisions"
    source = decisions_dir / "decisions.txt"
    write_text(
        source,
        padded("""decision_category = {
\tTEST_decision = {
\t\ttarget_trigger = { always = yes }
\t\tcomplete_effect = { add_political_power = 1 }
\t\tremove_effect = {
\t\t\tadd_political_power = -1
\t\t}
\t\ttimeout_effect = { add_political_power = 2 }
\t}
\tTEST_no_effect = {
\t\tvisible = { always = yes }
\t}
}
"""),
    )
    write_text(decisions_dir / "categories.txt", padded("category = {\n"))
    write_text(decisions_dir / "empty.txt", padded("# no decisions here\n"))

    assert logging_tool.decision_add(tmp_path) == 3
    content = source.read_text(encoding="utf-8")
    assert content.count("Decision TEST_decision target: [From.GetName]") == 1
    assert content.count("Decision remove TEST_decision target: [From.GetName]") == 1
    assert content.count("Decision timeout TEST_decision target: [From.GetName]") == 1
    assert "complete_effect = {" in content
    assert "remove_effect = {" in content
    assert "timeout_effect = {" in content
    with open(source, "a", encoding="utf-8", newline="") as handle:
        handle.write('log = "[GetDateText]: complete_effect regression"\n')
    assert logging_tool.decision_remove(tmp_path) == 4
    removed = source.read_text(encoding="utf-8")
    assert 'log = "[GetDateText]: [Root.GetName]: Decision' not in removed
    assert "complete_effect = {\n\t\t}\n" in removed


def test_tech_add_remove_handles_generated_and_legacy_log_shapes(tmp_path, capsys):
    tech_dir = tmp_path / "common" / "technologies"
    source = tech_dir / "technologies.txt"
    write_text(
        source,
        padded("""technologies = {
\tTEST_tech = { # technology comment
\t\tname = TEST_tech
\t}
\tTEST_second = {
\t\tname = TEST_second
\t}
}
"""),
    )

    assert logging_tool.tech_add(tmp_path) == 2
    content = source.read_text(encoding="utf-8")
    assert content.count("add tech TEST_") == 2
    assert "TEST_tech = { #technology comment" in content

    legacy = tech_dir / "legacy.txt"
    write_text(
        legacy,
        padded("""technologies = {
\tLEGACY = {
\t\ton_research_complete = {
\t\t\tlog = \"[GetDateText]: [Root.GetName]: legacy\"
\t\t}
\t}
}
"""),
    )
    assert logging_tool.tech_remove(tmp_path) == 5
    assert "Deleted logging at line" in capsys.readouterr().out
    assert 'log = "[GetDateText]' not in source.read_text(encoding="utf-8")
    assert 'log = "[GetDateText]' not in legacy.read_text(encoding="utf-8")


def test_logging_main_reports_remove_mode_with_all_processors_skipped(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "logging_tool.py",
            str(tmp_path),
            "--remove",
            "--dry-run",
            "--skip-events",
            "--skip-focus",
            "--skip-ideas",
            "--skip-decisions",
            "--skip-tech",
        ],
    )
    logging_tool.main()
    output = capsys.readouterr().out
    assert f"Processing mod at: {tmp_path}" in output
    assert "Mode: Removing logs (dry run)" in output
    assert "Would modify 0 entries" in output
    assert "Processing events..." not in output

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "logging_tool.py",
            str(tmp_path),
            "--dry-run",
            "--skip-events",
            "--skip-focus",
            "--skip-ideas",
            "--skip-decisions",
            "--skip-tech",
        ],
    )
    logging_tool.main()
    output = capsys.readouterr().out
    assert "Mode: Adding logs (dry run)" in output
    assert "Would modify 0 entries" in output


def make_log_line(
    wall: str, date: str, day: int, month: str, year: int, payload: str
) -> str:
    return (
        f"[{wall}][{date}.01][effectbase.cpp:1783]:  1:00, {day} {month}, "
        f"{year}: {payload}\n"
    )


def build_game_log(path: Path) -> None:
    lines = [
        "[23:59:50] engine startup without scripted payload\n",
        "1:00, 21 May, 2007: Brazil: Focus missing_date\n",
        make_log_line(
            "23:59:51", "2007.05.01", 1, "May", 2007, "Brazil: Focus BRA_early"
        ),
        make_log_line(
            "23:59:52", "2007.05.02", 2, "May", 2007, "Brazil: Focus BRA_protect"
        ),
        make_log_line(
            "23:59:53",
            "2007.05.02",
            2,
            "May",
            2007,
            "Brazil: Decision remove old_decision",
        ),
        make_log_line(
            "23:59:54",
            "2007.05.02",
            2,
            "May",
            2007,
            "Brazil: Decision Remove old_upper",
        ),
        make_log_line(
            "23:59:55", "2007.05.02", 2, "May", 2007, "Brazil: Decision cabinet"
        ),
        make_log_line(
            "23:59:56", "2007.05.02", 2, "May", 2007, "Brazil: add idea market_reform"
        ),
        make_log_line(
            "23:59:57",
            "2007.05.02",
            2,
            "May",
            2007,
            "Brazil: remove idea market_reform",
        ),
        make_log_line(
            "23:59:58",
            "2007.05.02",
            2,
            "May",
            2007,
            "Brazil: diplomatic action phase trade",
        ),
        make_log_line(
            "23:59:59",
            "2007.05.02",
            2,
            "May",
            2007,
            "Brazil: Weekly Economic Update: Treasury: -12.5 Treasury Rate: 1.5 Debt: 100 Interest Rate: 3.2 Population Tax Rate: 5 Corporate Tax Rate: 7",
        ),
        make_log_line(
            "00:00:00",
            "2007.05.02",
            2,
            "May",
            2007,
            "Brazil: Inflation Update: Current Inflation Rate: 2.5%",
        ),
        make_log_line(
            "00:00:01", "2007.05.02", 2, "May", 2007, "Brazil: DEBUG: noisy trace"
        ),
        make_log_line(
            "00:00:02", "2007.05.02", 2, "May", 2007, "Brazil: AI Tax: noisy tax"
        ),
        make_log_line(
            "00:00:03", "2007.05.02", 2, "May", 2007, "Brazil: ordinary message"
        ),
        make_log_line(
            "00:00:04", "2007.05.02", 2, "May", 2007, "Brazil: routine executed"
        ),
        make_log_line(
            "00:00:05",
            "2007.05.02",
            2,
            "May",
            2007,
            "Iraq annexed Iraq - self annexation",
        ),
        make_log_line(
            "00:00:06",
            "2007.05.02",
            2,
            "May",
            2007,
            "Brazil annexed North Korea - conquest",
        ),
        make_log_line(
            "00:00:07",
            "2007.05.02",
            2,
            "May",
            2007,
            "Iraq: iraq_civil_war.69.a executed",
        ),
        make_log_line(
            "00:00:08", "2007.05.02", 2, "May", 2007, "Brazil: election.10.b executed"
        ),
        make_log_line(
            "00:00:09", "2007.05.02", 2, "May", 2007, "Korea: reform.1.a executed"
        ),
        make_log_line(
            "00:00:10",
            "2007.05.02",
            2,
            "May",
            2007,
            "Côte d'Ivoire: referendum.1.a executed",
        ),
        make_log_line(
            "00:00:11",
            "2007.05.23",
            23,
            "May",
            2007,
            "Brazil: Weekly Economic Update: Treasury: 20 Treasury Rate: 2 Debt: 200 Interest Rate: 4 Population Tax Rate: 6 Corporate Tax Rate: 8",
        ),
        make_log_line(
            "00:00:12",
            "2007.05.23",
            23,
            "May",
            2007,
            "Brazil: Inflation Update: Current Inflation Rate: 4%",
        ),
        make_log_line(
            "00:00:13",
            "2007.05.22",
            22,
            "May",
            2007,
            "Brazil: Weekly Economic Update: Treasury: 10 Treasury Rate: 2 Debt: 150 Interest Rate: 4 Population Tax Rate: 6 Corporate Tax Rate: 8",
        ),
        make_log_line(
            "00:00:14",
            "2007.05.22",
            22,
            "May",
            2007,
            "Brazil: Inflation Update: Current Inflation Rate: 3%",
        ),
        make_log_line(
            "00:00:15",
            "2007.05.23",
            23,
            "May",
            2007,
            "Korea: Weekly Economic Update: Treasury: 1000 Treasury Rate: 1 Debt: 0 Interest Rate: 1 Population Tax Rate: 4 Corporate Tax Rate: 5",
        ),
        make_log_line(
            "00:00:16",
            "2007.05.24",
            24,
            "May",
            2007,
            "Brazil: Weekly Economic Update: Treasury: 30 Treasury Rate: 2 Debt: 300 Interest Rate: 4 Population Tax Rate: 6 Corporate Tax Rate: 8",
        ),
        make_log_line(
            "00:00:17",
            "2007.05.24",
            24,
            "May",
            2007,
            "Brazil: Inflation Update: Current Inflation Rate: 5%",
        ),
        make_log_line(
            "00:00:18",
            "2007.05.24",
            24,
            "May",
            2007,
            "Anonymous payload without country separator",
        ),
    ]
    write_text(path, "".join(lines))


def test_parse_classifies_realistic_records_and_date_filters(tmp_path):
    log = tmp_path / "game.log"
    build_game_log(log)
    data = summarize_game_log.parse(log)

    assert data["stats"] == {
        "lines": 30,
        "parsed": 28,
        "skipped": 2,
        "wall_first": (23, 59, 50),
        "wall_last": (0, 0, 18),
        "game_first": (20070501, " 1 May 2007"),
        "game_last": (20070524, "24 May 2007"),
    }
    assert data["categories"]["focus"] == 2
    assert data["categories"]["decision_remove"] == 2
    assert data["categories"]["decision"] == 1
    assert data["categories"]["idea_add"] == 1
    assert data["categories"]["idea_remove"] == 1
    assert data["categories"]["diplomacy"] == 1
    assert data["categories"]["economy"] == 5
    assert data["categories"]["inflation"] == 4
    assert data["categories"]["spam"] == 2
    assert data["categories"]["other"] == 2
    assert data["categories"]["effect"] == 1
    assert data["categories"]["annexation"] == 2
    assert data["categories"]["event"] == 4
    assert data["economy"]["Brazil"]["debt"] == 300.0
    assert data["inflation"]["Brazil"][2] == 5.0
    assert data["annexations"] == [
        (20070502, " 2 May 2007", "Iraq", "Iraq"),
        (20070502, " 2 May 2007", "Brazil", "North Korea"),
    ]
    assert data["conflicts"] == [
        (20070502, " 2 May 2007", "Iraq", "iraq_civil_war", "conflict"),
        (20070502, " 2 May 2007", "Brazil", "election", "politics"),
        (20070502, " 2 May 2007", "Côte d'Ivoire", "referendum", "politics"),
    ]

    filtered = summarize_game_log.parse(
        log, since=summarize_game_log.date_key(2007, 5, 2), until=20070523
    )
    assert filtered["stats"]["parsed"] == 24
    assert filtered["economy"]["Brazil"]["debt"] == 200.0
    assert filtered["inflation"]["Brazil"][2] == 4.0
    assert "BRA_early" not in filtered["focuses"]["Brazil"]
    assert filtered["focuses"]["Brazil"]["BRA_protect"] == 1


def test_summary_helpers_render_reports_json_and_country_selection(tmp_path):
    log = tmp_path / "game.log"
    build_game_log(log)
    data = summarize_game_log.parse(log)

    assert summarize_game_log.date_key(2007, 5, 2) == 20070502
    assert summarize_game_log.fmt_date(2007, 5, 2) == " 2 May 2007"
    assert summarize_game_log.human(0) == "0"
    assert summarize_game_log.human(1200) == "1.20k"
    assert summarize_game_log.human(-1_000_000) == "-1.00M"
    assert summarize_game_log.human(2_000_000_000) == "2.00B"
    assert summarize_game_log.human("not numeric") == "not numeric"
    assert summarize_game_log.money(4002) == "4,002"
    assert summarize_game_log.money(-14936) == "-14,936"
    assert summarize_game_log.money("unknown") == "unknown"
    assert summarize_game_log.resolve_name(data, "bRaZiL") == "Brazil"
    assert summarize_game_log.resolve_name(data, "Kore") == "Korea"
    assert summarize_game_log.resolve_name(data, "Atlantis") == "Atlantis"

    selected = summarize_game_log.pick_countries(data, ["brazil", "Kore", "Brazil"], 2)
    assert selected[:2] == ["Brazil", "Korea"]
    assert len(selected) == len(set(selected))
    assert summarize_game_log.pick_countries(data, [], 0) == ["Brazil"]
    activity_only = {
        "activity": Counter({"Fallback": 1}),
        "decisions": defaultdict(Counter),
    }
    assert summarize_game_log.pick_countries(activity_only, [], 0) == ["Fallback"]
    assert (
        summarize_game_log.pick_countries(
            {"activity": Counter(), "decisions": defaultdict(Counter)}, [], 0
        )
        == []
    )

    empty_data = {
        "stats": {
            "lines": 0,
            "parsed": 0,
            "skipped": 0,
            "wall_first": None,
            "wall_last": None,
            "game_first": None,
            "game_last": None,
        },
        "activity": Counter(),
        "categories": Counter(),
        "focuses": defaultdict(Counter),
        "decisions": defaultdict(Counter),
        "events": defaultdict(dict),
        "conflicts": [],
        "annexations": [],
        "economy": {},
        "inflation": {},
        "country_events": defaultdict(list),
        "ideas": defaultdict(Counter),
        "diplomacy": defaultdict(Counter),
        "events_by_country": defaultdict(Counter),
    }
    empty_report = summarize_game_log.report(empty_data)
    assert "(none detected)" in empty_report
    assert "In-game span" not in empty_report

    report = summarize_game_log.report(data, countries=["Brazil", "Missing"], top=2)
    assert "Real session : 23:59:50 -> 00:00:18  (0h00m)" in report
    assert "National finances" in report
    assert "Brazil  ->  North Korea" in report
    assert "Politics (elections / recognitions / unions)" in report
    assert "Country focus: Brazil" in report
    assert "Country focus: Missing" in report
    assert "No scripted log entries found" in report
    assert "Most-used decisions" in report
    assert "Ideas / laws adopted" in report
    assert "Notable events involving Brazil" in report
    assert "Event chains fired" not in report
    assert "Diplomatic actions" not in report

    detailed = summarize_game_log.report(data, countries=["Brazil"], top=1, detail=True)
    assert "Event chains fired (by namespace)" in detailed
    assert "Diplomatic actions (1 total)" in detailed
    assert "election" in detailed

    obj = json.loads(
        summarize_game_log.to_json(data, countries=["Brazil", "Missing"], top=1)
    )
    assert obj["session"]["lines"] == 30
    assert obj["session"]["wall_first"] == [23, 59, 50]
    assert obj["most_active"][0][0] == "Brazil"
    assert obj["annexations"] == [
        {"date": " 2 May 2007", "actor": "Brazil", "target": "North Korea"}
    ]
    assert obj["focus_countries"]["Brazil"]["economy"]["debt"] == 300.0
    assert "Missing" not in obj["focus_countries"]
    assert "_dk" not in json.dumps(obj)


def test_summarize_cli_success_json_and_exit_errors(tmp_path, monkeypatch, capsys):
    log = tmp_path / "game.log"
    build_game_log(log)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_game_log.py",
            str(log),
            "--country",
            "Brazil,Korea",
            "--top-countries",
            "1",
            "--detail",
            "--top",
            "2",
            "--since",
            "2007-05-02",
            "--until",
            "2007.05.23",
        ],
    )
    summarize_game_log.main()
    report_output = capsys.readouterr().out
    assert "Country focus: Brazil" in report_output
    assert "Country focus: Korea" in report_output
    assert "Diplomatic actions" in report_output
    assert "300" not in report_output

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_game_log.py",
            str(log),
            "--json",
            "--no-deep-dive",
            "--country",
            "Missing",
        ],
    )
    summarize_game_log.main()
    json_output = json.loads(capsys.readouterr().out)
    assert json_output["focus_countries"] == {}
    assert json_output["session"]["parsed"] == 28

    missing = tmp_path / "does-not-exist.log"
    monkeypatch.setattr(sys, "argv", ["summarize_game_log.py", str(missing)])
    with pytest.raises(SystemExit, match="error: file not found"):
        summarize_game_log.main()

    empty_log = tmp_path / "empty.log"
    write_text(empty_log, "not a scripted MD record\n")
    monkeypatch.setattr(sys, "argv", ["summarize_game_log.py", str(empty_log)])
    with pytest.raises(SystemExit, match="error: no scripted MD log entries"):
        summarize_game_log.main()


def test_summarize_parse_date_argument_shapes():
    assert summarize_game_log.parse_date_arg(None) is None
    assert summarize_game_log.parse_date_arg("") is None
    assert summarize_game_log.parse_date_arg("2007") == 20070101
    assert summarize_game_log.parse_date_arg("2007-05") == 20070501
    assert summarize_game_log.parse_date_arg("2007.05.23") == 20070523
