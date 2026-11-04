"""Game log summary: record parsing, the report, the JSON form and the CLI."""

import json
import sys
from collections import Counter

import pytest
import summarize_game_log as S
from shared.suite import write_text

_ECONOMY = (
    "{country}: Weekly Economic Update: Treasury: {treasury} Treasury Rate: 2 "
    "Debt: {debt} Interest Rate: 4 Population Tax Rate: 6 Corporate Tax Rate: 8"
)
_INFLATION = "Brazil: Inflation Update: Current Inflation Rate: {rate}%"

# (day of May 2007, payload), one second apart from 23:59:51. The session
# crosses midnight and the days are out of order near the end.
_RECORDS = [
    (1, "Brazil: Focus BRA_early"),
    (2, "Brazil: Focus BRA_protect"),
    (2, "Brazil: Decision remove old_decision"),
    (2, "Brazil: Decision Remove old_upper"),
    (2, "Brazil: Decision cabinet"),
    (2, "Brazil: add idea market_reform"),
    (2, "Brazil: remove idea market_reform"),
    (2, "Brazil: diplomatic action phase trade"),
    (2, _ECONOMY.format(country="Brazil", treasury=-12.5, debt=100)),
    (2, _INFLATION.format(rate=2.5)),
    (2, "Brazil: DEBUG: noisy trace"),
    (2, "Brazil: AI Tax: noisy tax"),
    (2, "Brazil: ordinary message"),
    (2, "Brazil: routine executed"),
    (2, "Iraq annexed Iraq - self annexation"),
    (2, "Brazil annexed North Korea - conquest"),
    (2, "Iraq: iraq_civil_war.69.a executed"),
    (2, "Brazil: election.10.b executed"),
    (2, "Korea: reform.1.a executed"),
    (2, "Côte d'Ivoire: referendum.1.a executed"),
    (23, _ECONOMY.format(country="Brazil", treasury=20, debt=200)),
    (23, _INFLATION.format(rate=4)),
    (22, _ECONOMY.format(country="Brazil", treasury=10, debt=150)),
    (22, _INFLATION.format(rate=3)),
    (23, _ECONOMY.format(country="Korea", treasury=1000, debt=0)),
    (24, _ECONOMY.format(country="Brazil", treasury=30, debt=300)),
    (24, _INFLATION.format(rate=5)),
    (24, "Anonymous payload without country separator"),
]


def _record(index, day, payload):
    seconds = (23 * 3600 + 59 * 60 + 51 + index) % 86400
    wall = f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"
    return (
        f"[{wall}][2007.05.{day:02d}.01][effectbase.cpp:1783]:  1:00, {day} May, "
        f"2007: {payload}\n"
    )


@pytest.fixture
def log(tmp_path):
    # The first two lines are not scripted records and are skipped.
    lines = [
        "[23:59:50] engine startup without scripted payload\n",
        "1:00, 21 May, 2007: Brazil: Focus missing_date\n",
    ]
    lines += [_record(index, *record) for index, record in enumerate(_RECORDS)]
    return write_text(tmp_path / "game.log", "".join(lines))


@pytest.fixture
def data(log):
    return S.parse(log)


def test_parse_classifies_each_record(data):
    categories = {
        "focus": 2,
        "decision_remove": 2,
        "decision": 1,
        "idea_add": 1,
        "idea_remove": 1,
        "diplomacy": 1,
        "economy": 5,
        "inflation": 4,
        "spam": 2,
        "other": 2,
        "effect": 1,
        "annexation": 2,
        "event": 4,
    }

    assert data["stats"] == {
        "lines": 30,
        "parsed": 28,
        "skipped": 2,
        "wall_first": (23, 59, 50),
        "wall_last": (0, 0, 18),
        "game_first": (20070501, " 1 May 2007"),
        "game_last": (20070524, "24 May 2007"),
    }
    assert {name: data["categories"][name] for name in categories} == categories
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


def test_parse_keeps_only_records_inside_the_date_range(log):
    filtered = S.parse(log, since=S.date_key(2007, 5, 2), until=20070523)

    assert filtered["stats"]["parsed"] == 24
    # The 23 May update wins over the 22 May one read after it.
    assert filtered["economy"]["Brazil"]["debt"] == 200.0
    assert filtered["inflation"]["Brazil"][2] == 4.0
    assert "BRA_early" not in filtered["focuses"]["Brazil"]
    assert filtered["focuses"]["Brazil"]["BRA_protect"] == 1


@pytest.mark.parametrize(
    ("argument", "key"),
    [
        (None, None),
        ("", None),
        ("2007", 20070101),
        ("2007-05", 20070501),
        ("2007.05.23", 20070523),
    ],
)
def test_date_argument_fills_the_missing_month_and_day(argument, key):
    assert S.parse_date_arg(argument) == key


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0, "0"),
        (1200, "1.20k"),
        (-1_000_000, "-1.00M"),
        (2_000_000_000, "2.00B"),
        ("not numeric", "not numeric"),
    ],
)
def test_human_scales_a_number_to_its_unit(value, text):
    assert S.human(value) == text


@pytest.mark.parametrize(
    ("value", "text"), [(4002, "4,002"), (-14936, "-14,936"), ("unknown", "unknown")]
)
def test_money_groups_thousands(value, text):
    assert S.money(value) == text


# case: (countries in the log, name typed, name resolved)
_NAME_CASES = {
    "other case": (["Brazil"], "bRaZiL", "Brazil"),
    "part of the name": (["Korea"], "Kore", "Korea"),
    # Niger and Nigeria, Sudan and South Sudan: the exact name wins.
    "exact match before a longer name": (["North Korea", "Korea"], "korea", "Korea"),
    "unknown": (["Brazil"], "Atlantis", "Atlantis"),
}


@pytest.mark.parametrize(
    ("countries", "typed", "name"), _NAME_CASES.values(), ids=_NAME_CASES
)
def test_country_name_resolves_by_case_then_by_substring(countries, typed, name):
    assert S.resolve_name({"activity": Counter(countries)}, typed) == name


def test_country_selection_resolves_and_dedupes_requested_names(data):
    selected = S.pick_countries(data, ["brazil", "Kore", "Brazil"], 2)

    assert selected[:2] == ["Brazil", "Korea"]
    assert len(selected) == len(set(selected))


# With nothing requested the player is guessed: the country with the most
# decisions, or the most active one when no decision was logged.
# case: ({country: log entries}, {country: decisions taken}, countries picked)
_GUESS_CASES = {
    "most decisions, not most active": ({"A": 5, "B": 1}, {"B": 1}, ["B"]),
    "no decisions": ({"Fallback": 1}, {}, ["Fallback"]),
    "empty log": ({}, {}, []),
}


@pytest.mark.parametrize(
    ("activity", "decisions", "picked"), _GUESS_CASES.values(), ids=_GUESS_CASES
)
def test_country_selection_guesses_the_player(activity, decisions, picked):
    data = {
        "activity": Counter(activity),
        "decisions": {
            country: Counter(some_decision=count)
            for country, count in decisions.items()
        },
    }

    assert S.pick_countries(data, [], 0) == picked


def test_report_on_a_log_with_no_records_says_nothing_was_detected(tmp_path):
    quiet = write_text(tmp_path / "quiet.log", "not a scripted MD record\n")

    report = S.report(S.parse(quiet))

    assert "(none detected)" in report
    assert "In-game span" not in report


def test_report_covers_the_session_and_each_focus_country(data):
    report = S.report(data, countries=["Brazil", "Missing"], top=2)

    for section in (
        "Real session : 23:59:50 -> 00:00:18  (0h00m)",
        "National finances",
        "Brazil  ->  North Korea",
        "Politics (elections / recognitions / unions)",
        "Country focus: Brazil",
        "Country focus: Missing",
        "No scripted log entries found",
        "Most-used decisions",
        "Ideas / laws adopted",
        "Notable events involving Brazil",
    ):
        assert section in report
    # Event chains and diplomacy are detail-only sections.
    assert "Event chains fired" not in report
    assert "Diplomatic actions" not in report


def test_detailed_report_adds_event_chains_and_diplomacy(data):
    detailed = S.report(data, countries=["Brazil"], top=1, detail=True)

    assert "Event chains fired (by namespace)" in detailed
    assert "Diplomatic actions (1 total)" in detailed
    assert "election" in detailed


def test_json_form_drops_internal_keys_and_unknown_countries(data):
    obj = json.loads(S.to_json(data, countries=["Brazil", "Missing"], top=1))

    assert obj["session"]["lines"] == 30
    assert obj["session"]["wall_first"] == [23, 59, 50]
    assert obj["most_active"][0][0] == "Brazil"
    # The self-annexation is left out.
    assert obj["annexations"] == [
        {"date": " 2 May 2007", "actor": "Brazil", "target": "North Korea"}
    ]
    assert obj["focus_countries"]["Brazil"]["economy"]["debt"] == 300.0
    assert "Missing" not in obj["focus_countries"]
    assert "_dk" not in json.dumps(obj)


def _main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["summarize_game_log.py", *map(str, argv)])
    S.main()


def test_cli_report_applies_countries_detail_and_the_date_range(
    log, monkeypatch, capsys
):
    _main(
        monkeypatch,
        log,
        *("--country", "Brazil,Korea", "--top-countries", "1", "--detail"),
        *("--top", "2", "--since", "2007-05-02", "--until", "2007.05.23"),
    )

    output = capsys.readouterr().out
    assert "Country focus: Brazil" in output
    assert "Country focus: Korea" in output
    assert "Diplomatic actions" in output
    # The 24 May debt of 300 is outside the range.
    assert "300" not in output


def test_cli_json_without_a_deep_dive_has_no_focus_countries(log, monkeypatch, capsys):
    _main(monkeypatch, log, "--json", "--no-deep-dive", "--country", "Missing")

    output = json.loads(capsys.readouterr().out)
    assert output["focus_countries"] == {}
    assert output["session"]["parsed"] == 28


# case: (log contents, or None for a missing file; error)
@pytest.mark.parametrize(
    ("contents", "error"),
    [
        (None, "error: file not found"),
        ("not a scripted MD record\n", "error: no scripted MD log entries"),
    ],
    ids=["missing file", "no scripted records"],
)
def test_cli_exits_when_there_is_nothing_to_summarize(
    tmp_path, monkeypatch, contents, error
):
    path = tmp_path / "other.log"
    if contents is not None:
        write_text(path, contents)

    with pytest.raises(SystemExit, match=error):
        _main(monkeypatch, path)
