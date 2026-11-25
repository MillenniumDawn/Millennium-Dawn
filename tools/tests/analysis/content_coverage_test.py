"""Content coverage report: the mod scan, the log scan, the report and the CLI."""

import calendar
import json
import sys
from collections import Counter

import content_coverage as C
import pytest
from shared.suite import run_tool_script, write_text, write_tree

_FOCUS_FILE = """focus_tree = {
	id = TST_focus_tree
	shared_focus = TST_joint_one

	# focus = { id = TST_commented }
	focus = {
		id = TST_first
		prerequisite = { focus = TST_unrelated }
		completion_reward = {
			log = "an unclosed { brace in a string"
			country_event = { id = tst.99 }
		}
	}
	focus = { id = TST_second }
	focus = { id = OTH_other }
}

joint_focus = {
	id = TST_joint_one
}
"""

_DECISION_FILE = """TST_category = {
	TST_fired_decision = { icon = generic }
	TST_idle_decision = { icon = generic }
	OTH_decision = { icon = generic }
}
"""

_EVENT_FILE = """add_namespace = tst

country_event = {
	id = tst.1
	trigger = { original_tag = TST }
	option = {
		name = tst.1.a
		country_event = { id = tst.99 days = 3 }
	}
	option = { name = tst.1.b }
}

country_event = {
	id = tst.2
	is_triggered_only = yes
}

news_event = {
	id = tst.3
	trigger = { original_tag = TST }
}
"""

# Another tag leads `shared`, and `nested` names TST only below the top of its trigger.
_OTHER_EVENT_FILE = """country_event = { id = shared.1 trigger = { original_tag = OTH } }
country_event = { id = shared.2 trigger = { original_tag = OTH } }
country_event = { id = shared.3 trigger = { original_tag = TST } }
country_event = {
	id = nested.1
	trigger = { OR = { original_tag = TST original_tag = OTH } }
	option = { ai_chance = { modifier = { original_tag = TST } } }
}
"""

_MOD = {
    "common/national_focus/tst.txt": _FOCUS_FILE,
    "common/national_focus/other.txt": "focus_tree = { focus = { id = OTH_only } }\n",
    "common/decisions/tst.txt": _DECISION_FILE,
    "common/decisions/categories/tst.txt": "TST_category = { TST_in_categories = { } }\n",
    "events/tst.txt": _EVENT_FILE,
    "events/other.txt": _OTHER_EVENT_FILE,
}


def _line(date, payload):
    year, month, day = date.split("-")
    stamp = f"[17:40:45][{year}.{month}.{day}.01]"
    month_name = calendar.month_name[int(month)]
    return f"{stamp}[effectbase.cpp:1783]: {stamp}:  1:00, {int(day)} {month_name}, {year}: {payload}\n"


_LOG_LINES = [
    "[17:40:44] engine startup without a scripted payload\n",
    # The two bracketed dates differ: the later one is the real time.
    "[17:40:45][2001.03.04.23]: [17:40:45][2001.03.05.01]:  1:00, 5 March, 2001: "
    "Test Land: Focus TST_first\n",
    _line("2001-06-01", "Test Land: Focus TST_undefined_focus"),
    _line("2001-06-02", "Test Land: Focus OTH_first"),
    _line("2001-04-09", "Test Land: Decision TST_fired_decision target: Elsewhere"),
    _line("2001-04-01", "Test Land: Decision TST_fired_decision"),
    _line("2001-04-02", "Test Land: Decision remove TST_fired_decision"),
    _line("2001-04-03", "Test Land: Decision Remove TST_fired_decision"),
    _line("2001-07-01", "Test Land: Decision TST_undefined_decision"),
    _line("2000-06-02", "Other Land: tst.1.a executed"),
    _line("2000-01-15", "Test Land: tst.1.a executed   "),
    _line("2000-01-16", "Test Land: tst.1.b executed"),
    _line("2000-09-09", "Test Land: tst.3 reviewed after a government change"),
    _line("2000-10-10", "Test Land: tst.404.a executed"),
    _line("2000-11-11", "Test Land: shared.1.a executed"),
    _line("2000-12-12", "Test Land: Weekly Economic Update: Treasury: 1"),
]

# kind: (fired ids by first date, never fired, fired but not found, percent)
_REPORT = {
    "focuses": (
        ["TST_first"],
        ["TST_second", "TST_joint_one"],
        ["TST_undefined_focus"],
        33.3,
    ),
    "decisions": (
        ["TST_fired_decision"],
        ["TST_idle_decision"],
        ["TST_undefined_decision"],
        50.0,
    ),
    "events": (["tst.1", "tst.3"], ["tst.2"], ["tst.404"], 66.7),
}


@pytest.fixture
def root(tmp_path):
    return write_tree(tmp_path / "mod", _MOD)


@pytest.fixture
def log(tmp_path):
    return write_text(tmp_path / "game.log", "".join(_LOG_LINES))


@pytest.fixture
def report(root, log):
    defined, namespaces = C.scan_static(root, "TST", [])
    return C.build_report(
        "TST", log, defined, namespaces, C.scan_log(log, "TST", namespaces)
    )


# case: (kind, ids the scan defines, in file order)
_DEFINED_CASES = {
    "focuses: tree and joint blocks, no prefix or reference strays": (
        "focuses",
        ["TST_first", "TST_second", "TST_joint_one"],
    ),
    "decisions: category children only, not categories/": (
        "decisions",
        ["TST_fired_decision", "TST_idle_decision"],
    ),
    "events: depth-0 events of the claimed namespace only": (
        "events",
        ["tst.1", "tst.2", "tst.3"],
    ),
}


@pytest.mark.parametrize(("kind", "ids"), _DEFINED_CASES.values(), ids=_DEFINED_CASES)
def test_static_scan_defines_what_the_tag_owns(root, kind, ids):
    defined, namespaces = C.scan_static(root, "TST", [])

    assert defined[kind] == ids
    assert namespaces == ["tst"]


def test_namespace_option_replaces_the_original_tag_rule(root):
    defined, namespaces = C.scan_static(root, "TST", ["shared", "nested"])

    assert namespaces == ["nested", "shared"]
    assert defined["events"] == ["shared.1", "shared.2", "shared.3", "nested.1"]


# case: (tag counts of one namespace, whether TST leads)
_LEADS_CASES = {
    "named alone": (Counter(TST=1), True),
    "named most": (Counter(TST=3, OTH=2), True),
    "tied": (Counter(TST=2, OTH=2), False),
    "behind": (Counter(TST=1, OTH=2), False),
    "not named": (Counter(OTH=1), False),
    "no tags": (Counter(), False),
}


@pytest.mark.parametrize(("counts", "leads"), _LEADS_CASES.values(), ids=_LEADS_CASES)
def test_a_tag_leads_a_namespace_only_by_being_named_most(counts, leads):
    assert C.leads(counts, "TST") is leads


# case: (text, nested blocks)
_BLOCK_CASES = {
    "named blocks": ("a = { b = 1 } c = { }", [("a", " b = 1 "), ("c", " ")]),
    "anonymous block and stray close": (
        "a = { x } { y } }",
        [("a", " x "), ("", " y ")],
    ),
}


@pytest.mark.parametrize(("text", "blocks"), _BLOCK_CASES.values(), ids=_BLOCK_CASES)
def test_split_block_returns_the_nested_blocks(text, blocks):
    assert C.split_block(text)[1] == blocks


# case: (kind, {id: (first date, count, options)})
_HITS_CASES = {
    "focuses: later of two bracketed dates, other prefix ignored": (
        "focuses",
        {
            "TST_first": ("2001-03-05", 1, {}),
            "TST_undefined_focus": ("2001-06-01", 1, {}),
        },
    ),
    "decisions: target text and removals do not count": (
        "decisions",
        {
            "TST_fired_decision": ("2001-04-01", 2, {}),
            "TST_undefined_decision": ("2001-07-01", 1, {}),
        },
    ),
    "events: options group under the event, earliest line wins": (
        "events",
        {
            "tst.1": ("2000-01-15", 3, {"a": 2, "b": 1}),
            "tst.3": ("2000-09-09", 1, {}),
            "tst.404": ("2000-10-10", 1, {"a": 1}),
        },
    ),
}


@pytest.mark.parametrize(("kind", "expected"), _HITS_CASES.values(), ids=_HITS_CASES)
def test_log_scan_counts_each_id_once_per_line(log, kind, expected):
    hits = C.scan_log(log, "TST", ["tst"])[kind]

    assert {
        key: (hit.first, hit.count, dict(hit.options)) for key, hit in hits.items()
    } == expected


def test_log_scan_without_namespaces_finds_no_events(log):
    hits = C.scan_log(log, "TST", [])

    assert hits["events"] == {}
    assert "TST_first" in hits["focuses"]


@pytest.mark.parametrize(("kind", "expected"), _REPORT.items(), ids=list(_REPORT))
def test_report_splits_fired_never_fired_and_not_found(report, kind, expected):
    fired, never, not_found, percent = expected
    data = report[kind]

    assert [row["id"] for row in data["fired_list"]] == fired
    assert data["never_fired"] == never
    assert [row["id"] for row in data["fired_not_found"]] == not_found
    assert (data["fired"], data["percent"]) == (len(fired), percent)


def test_report_percent_is_none_when_nothing_is_defined():
    assert C.kind_report([], {})["percent"] is None


def test_text_report_opens_with_the_counts_then_lists_each_section(report):
    lines = C.format_text(report).splitlines()

    assert lines[1:5] == [
        "  focuses    1/3  33.3%",
        "  decisions  1/2  50.0%",
        "  events     2/3  66.7%",
        "  event namespaces: tst",
    ]
    assert "  2000-01-15      3x  tst.1  [a x2, b]" in lines
    assert "== events: never fired (1) ==" in lines
    assert "== focuses: fired but not found in the scan (1) ==" in lines


def test_text_report_names_the_percent_n_a_without_definitions():
    empty = {"tag": "TST", "log": "x", "namespaces": []}
    empty.update({kind: C.kind_report([], {}) for kind in C.KINDS})

    text = C.format_text(empty)

    assert "  focuses    0/0  n/a" in text
    assert "event namespaces: (none)" in text


def _main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["content_coverage.py", *map(str, argv)])
    C.main()


def test_cli_json_report_uppercases_the_tag(root, log, monkeypatch, capsys):
    _main(monkeypatch, "--tag", "tst", "--log", log, "--root", root, "--json")

    output = json.loads(capsys.readouterr().out)
    assert output["tag"] == "TST"
    assert output["namespaces"] == ["tst"]
    assert output["events"]["fired"] == 2


def test_cli_namespace_option_changes_the_event_scan(root, log, monkeypatch, capsys):
    _main(
        monkeypatch,
        *("--tag", "TST", "--log", log, "--root", root, "--json"),
        *("--namespace", "shared"),
    )

    output = json.loads(capsys.readouterr().out)
    assert output["namespaces"] == ["shared"]
    assert output["events"]["fired"] == 1


_BAD_BYTES = b"\xff\xfe\n"

# case: (error shown, setup(log path, mod root) or None for no log, tree holds a mod)
_ERROR_CASES = {
    "missing log": ("error: file not found", None, True),
    "unreadable log": (
        "error: cannot read .*game.log",
        lambda log, mod: log.mkdir(),
        True,
    ),
    "bad bytes name the log": (
        "error: input is not valid UTF-8: .*game.log",
        lambda log, mod: log.write_bytes(_BAD_BYTES),
        True,
    ),
    "bad bytes name a mod file": (
        "error: input is not valid UTF-8: .*bad.txt",
        lambda log, mod: (mod / "events" / "bad.txt").write_bytes(_BAD_BYTES),
        True,
    ),
    "no mod directories": ("error: no common/national_focus", None, False),
}


@pytest.mark.parametrize(
    ("error", "setup", "has_mod"), _ERROR_CASES.values(), ids=_ERROR_CASES
)
def test_cli_exits_with_a_message_when_it_cannot_scan(
    tmp_path, monkeypatch, error, setup, has_mod
):
    log = tmp_path / "game.log"
    mod = write_tree(tmp_path / "mod", _MOD if has_mod else {"unrelated.txt": ""})
    if setup:
        setup(log, mod)

    with pytest.raises(SystemExit, match=error):
        _main(monkeypatch, "--tag", "TST", "--log", log, "--root", mod)


def test_script_runs_on_its_own(root, log):
    result = run_tool_script(
        "analysis/content_coverage.py", "--tag", "TST", "--log", log, "--root", root
    )

    assert result.returncode == 0, result.stderr
    assert "TST content coverage" in result.stdout
