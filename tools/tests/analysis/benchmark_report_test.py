"""Behavioral tests for tools/analysis/benchmark_report.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from shared.suite import run_tool_script

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.analysis import benchmark_report  # noqa: E402

_MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _line(date: tuple[int, int, int], who: str, message: str) -> str:
    """A scripted log line in the shape the game writes, with the 1:00 clock."""
    year, month, day = date
    stamp = f"[12:00:00][{year}.{month:02d}.{day:02d}.01]"
    clock = f"1:00, {day} {_MONTH_NAMES[month - 1]}, {year}"
    return f"{stamp}: {stamp}:  {clock}: {who}: {message}"


def _monthly(
    month: int,
    tag: str,
    civilian: int,
    military: int,
    gdp: int,
    per_capita: float,
    at_war: int = 0,
    debt: int = 0,
    states: int | None = None,
) -> str:
    message = (
        f"Monthly Benchmark: Civilian: {civilian} Military: {military} GDP: {gdp} "
        f"GDP per Capita: {per_capita} Inflation: 0.02 Population Tax: 25 "
        f"Corporate Tax: 20 Debt: {debt} Interest Rate: 3.4 Treasury Rate: 1.5 "
        f"Political Power: 50 Daily PP: 2.5 At War: {at_war}"
    )
    if states is not None:
        message += f" States: {states}"
    return _line((2000, month, 1), tag, message)


def _economy(month: int, tag: str, arms: int) -> list[str]:
    """Resource balance, imports and construction lines for one tag and month."""
    return [
        _line(
            (2000, month, 1),
            tag,
            "Resource Balance (net): Oil: -4 Steel: 6 Microchips Produced: 7 "
            "Microchips Consumed: 2",
        ),
        _line((2000, month, 1), tag, "Resource Imports: Oil: 3 Steel: 0"),
        _line(
            (2000, month, 1),
            tag,
            f"Construction: Arms: {arms} Dockyards: 1 Agriculture: 2 Fossil Plants: 3 "
            "Reactors: 0 Renewables: 4 Enrichment: 0 Internet: 1 Rail Terminals: 2 "
            "Energy Deficit: 2 Nuclear Fuel: 1.5",
        ),
    ]


def _laws(day: int, who: str, bureaucracy: str, police: str) -> str:
    message = (
        f"Spending Laws (law/expected/offset): Bureaucracy: {bureaucracy} "
        f"Police: {police} Balance Ratio: 0.5 AI Balance: 0.25 "
        "Raw (B/P/E/H/S): 1.5/2.5/3.5/4.5/5.5"
    )
    return _line((2000, 2, day), who, message)


def _weekly(day: int, who: str, rate: float, pop_tax: int) -> str:
    message = (
        f"Weekly Economic Update: Treasury: 5 Treasury Rate: {rate} Debt: 10 "
        f"Interest Rate: 3 Population Tax Rate: {pop_tax} Corporate Tax Rate: 23"
    )
    return _line((2000, 2, day), who, message)


def _investment(date: tuple[int, int, int], who: str) -> str:
    message = (
        "Investment Succeeded: project type 5 (x 1) in Somewhere, "
        "Project Duration: 299, Nation Elsewhere, score = 167"
    )
    return _line(date, who, message)


_BAD_STAMP_CAPITULATION = (
    "[12:00:00][2000.03.04.23]: [12:00:00][2000.03.05.01]:  "
    "1:00, 5 March, 2000: BBB: Capitulated to AAA: "
    "Debt Ratio: 2 Interest Rate: 12 Treasury Rate: -1.5"
)

_OLD_PREFIX_MONTHLY = (
    "[2000.02.01.1]: 0:0, src: AAA: Monthly Benchmark: Civilian: 9 Military: 3 "
    "GDP: 100 GDP per Capita: 5.5 Inflation: 0.02 Population Tax: 25 "
    "Corporate Tax: 20 Debt: 0 Interest Rate: 3.4 Treasury Rate: 1.5 "
    "Political Power: 50 Daily PP: 2.5 At War: 0"
)

_ERROR_LOG = [
    "[12:00:00][no_game_date]: Sub-unit 'Light_Armor' has 'group = support' but no 'support' in its type list",
    "[12:00:01][2000.01.01.13]: AI tried to post an invalid command: order_assign_command",
    '[12:00:02][no_game_date]: Error: "Unexpected token: context_type, near line: 7" in file: "common/x.txt" near line: 7',
    "[12:00:03][no_game_date]: Invalid trigger 'FOO' in tests/one.txt line : 12",
    "[12:00:03][no_game_date]: Invalid trigger 'BAR' in tests/two.txt line : 40",
    "[12:00:03][no_game_date]: Invalid trigger 'BAZ' in tests/two.txt line : 41",
    '[12:00:04][no_game_date]: Error: "Unknown trigger-type: ABC, near line: 3" in file: "tests/one.txt" near line: 5',
    '[12:00:04][no_game_date]: Error: "Unknown trigger-type: DEF, near line: 9" in file: "tests/two.txt" near line: 11',
]


def _run_a() -> list[str]:
    """Four months. The last has one of three countries, so it is not fully reported."""
    lines = []
    for month, civilian, military, gdp, at_war in [
        (2, 10, 4, 100, 1),
        (3, 11, 5, 120, 1),
        (4, 12, 6, 140, 1),
        (5, 13, 7, 160, 0),
    ]:
        lines.append(_monthly(month, "AAA", civilian, military, gdp, 5.5, at_war))
        if month < 5:
            lines.append(_monthly(month, "BBB", 5, 1, 200, 3.0))
            lines.append(
                _monthly(
                    month, "CCC", 6, 2, 300, 4.0, at_war=int(month == 2), debt=2500
                )
            )
    lines += _economy(2, "AAA", 5) + _economy(3, "AAA", 6)
    lines += [
        _line(
            (2000, 3, 1),
            "AAA",
            "Probe 1234: Owned Arms: 4 Controlled Arms: 2 At War: 1",
        ),
        _line(
            (2000, 2, 10),
            "AAA",
            "War Declared on BBB: Attacker Debt Ratio: 0.5 Interest Rate: 8 "
            "Treasury Rate: 1 Crisis: 0 Defender Debt Ratio: 1.2 Interest Rate: 9.5 "
            "Treasury Rate: -1 Crisis: 1",
        ),
        _BAD_STAMP_CAPITULATION,
        _laws(7, "Alpha Land", "2/3/0", "3/3/0"),
        _laws(10, "Alpha Land", "2/3/0", "3/3/0"),
        _laws(14, "Alpha Land", "3/3/0", "3/3/0"),
        _laws(21, "Alpha Land", "2/3/1", "4/2/0"),
        _laws(7, "Beta Land", "2/2/0", "3/3/0"),
        _weekly(7, "Alpha Land", 0.1, 25),
        _weekly(14, "Alpha Land", 3.0, 25),
        _weekly(21, "Alpha Land", 3.5, 26),
        _weekly(28, "Alpha Land", 3.5, 26),
        _weekly(7, "Beta Land", 1, 25),
        _weekly(14, "Beta Land", 1.2, 25),
        _weekly(7, "Gamma Land", 0.1, 25),
        _line((2000, 2, 14), "Gamma Land", "Weekly Economic Update: Treasury: 5"),
        _weekly(21, "Gamma Land", 9.0, 25),
    ]
    debt = "Decision bankruptcy_default (Debt: 15.29b, Interest Rate: 50%, GDP: 0.1b)"
    lines += [
        _line((2000, 2, 9), "Alpha Land", debt),
        _line((2000, 3, 10), "Alpha Land", debt),
        _line((2000, 2, 9), "Alpha Land", "Decision utility_x"),
        _line((2000, 2, 9), "Beta Land", "Decision utility_x"),
        _line((2000, 2, 9), "Alpha Land", "T_ev.1.a"),
        _line((2000, 2, 10), "Alpha Land", "T_ev.1.a"),
        _line((2000, 2, 10), "Alpha Land", "T_ev.2.b"),
        _line((2000, 2, 9), "Alpha Land", "Focus ZZ_first"),
        _line((2000, 2, 10), "Alpha Land", "Focus ZZ_first"),
        _line((2000, 2, 9), "Alpha Land", "Idea bureau_03 removed"),
        _line((2000, 2, 10), "Alpha Land", "Idea bureau_03 removed"),
        _line((2000, 2, 10), "Alpha Land", "add idea defence_03"),
        _investment((2000, 2, 9), "Alpha Land"),
        _investment((2000, 2, 10), "Alpha Land"),
        _investment((2001, 6, 1), "Alpha Land"),
        _investment((2001, 6, 1), "Beta Land"),
    ]
    return lines


def _run_b() -> list[str]:
    """Two full months, the first of them in the older line prefix, plus a skipped tag."""
    lines = [_OLD_PREFIX_MONTHLY, _monthly(3, "AAA", 11, 3, 110, 5.5)]
    for month in (2, 3):
        lines += [
            _monthly(month, "BBB", 5, 1, 200, 3.0),
            _monthly(month, "CCC", 6, 2, 300, 4.0, debt=2500),
            _monthly(month, "ZZZ", 50, 9, 1000, 9.0, states=0),
        ]
    debt = "Decision bankruptcy_default (Debt: 15.29b, Interest Rate: 50%, GDP: 0.1b)"
    lines += [
        _line((2000, 2, 9), "Alpha Land", debt),
        _line((2000, 2, 9), "Alpha Land", "Decision utility_x"),
        _line((2000, 2, 9), "Alpha Land", "T_ev.1.a"),
        _line((2000, 2, 9), "Alpha Land", "T_ev.2.b"),
    ]
    return lines


def _write(path: Path, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def _write_logs(tmp_path: Path) -> dict[str, str]:
    _write(tmp_path / "a.log", _run_a())
    _write(tmp_path / "b.log", _run_b())
    _write(tmp_path / "error.log", _ERROR_LOG)
    _write(tmp_path / "late.log", [_monthly(7, "AAA", 10, 4, 100, 5.5)])
    return {
        "a": str(tmp_path / "a.log"),
        "b": str(tmp_path / "b.log"),
        "err": str(tmp_path / "error.log"),
        "late": str(tmp_path / "late.log"),
        "dir": tmp_path.name,
    }


def _run(
    tmp_path: Path, monkeypatch, capsys, args: list[str]
) -> tuple[int, str, str, dict[str, str]]:
    paths = _write_logs(tmp_path)
    argv = ["benchmark_report.py", *(arg.format(**paths) for arg in args)]
    monkeypatch.setattr(sys, "argv", argv)
    code = benchmark_report.main()
    captured = capsys.readouterr()
    return code, captured.out, captured.err, paths


_ALPHA = "Alpha Land"
_COMPARE = ["compare", "a={a}", "b={b}", "--majors", "AAA", "--also", "BBB"]
_COMPARE += ["--skip", "ZZZ"]
_COUNTS = ["counts", "a={a}", "b={b}", "--who", _ALPHA]
_LAW_LABEL = "Spending Laws"

# case: (arguments, fragment the report must contain; {a} {b} {err} {dir} are filled in)
_REPORT_CASES = {
    "compare: last month every run fully reported": (
        _COMPARE,
        "Compared at 2000-03 (last month every run fully reported).\n- a: reached 2000-04\n- b: reached 2000-03",
    ),
    "compare: skipped tag leaves the totals": (
        _COMPARE,
        "| Countries | 3 | 3 | 3 | 3 |",
    ),
    "compare: thousands separator": (
        _COMPARE,
        "| Total debt | 2,500 | 2,500 | 2,500 | 2,500 |",
    ),
    "compare: tag in no run is gone": (
        [*_COMPARE, "--also", "NOPE"],
        "| NOPE | gone |",
    ),
    "compare: major in no run shows dashes": (
        [*_COMPARE, "--majors", "NOPE"],
        "| 2000-03 |" + " - |" * 16,
    ),
    "compare: one run without construction lines": (
        ["compare", "b={b}", "--majors", "AAA", "--skip", "ZZZ"],
        "## Majors' construction, start to 2000-03",
    ),
    "compare: world GDP at the first and last common month": (
        _COMPARE,
        "| World GDP | 600 | 620 | 600 | 610 |",
    ),
    "compare: top table extras and start to end": (
        _COMPARE,
        "| AAA | 10 -> 11 | 4 -> 5 |",
    ),
    "compare: top table interest and treasury rate to one decimal": (
        _COMPARE,
        "| 0 -> 0 | 3.4 | 25/20 | 2.0% | 1.5 | 50 | 2.50 |",
    ),
    "compare: resource shortfall counts the short countries": (
        _COMPARE,
        "| Oil | 1 | -4.0 | 0 | 0.0 |",
    ),
    "compare: top table lists the short resource": (
        _COMPARE,
        "| Oil -4 |",
    ),
    "compare: net balance with imports and chips": (
        _COMPARE,
        "| AAA | -4 (3) | 6 (0) | - (-) | - (-) | - (-) | - (-) | - (-) | - (-) | 7/2 |",
    ),
    "compare: other buildings and nuclear fuel to one decimal": (
        _COMPARE,
        "| AAA | a | 5 -> 6 | 1 -> 1 | 2 -> 2 | 3 -> 3 | 0 -> 0 | 4 -> 4 | 0 -> 0 | 1 -> 1 | 2 -> 2 | 2 | 1.5 |",
    ),
    "compare: majors over time uses the comparison month": (
        _COMPARE,
        "| 2000-03 | 50 | 2.50 | 11 (-) | - | 120 | 0 | 2.0% | 25/20 |",
    ),
    "compare: attacker and defender interest kept apart": (
        _COMPARE,
        "| 2000-02-10 | AAA | BBB | 0.50, 8.0%, no | 1.20, 9.5%, yes |",
    ),
    "compare: capitulation date from the last bracket": (
        _COMPARE,
        "| 2000-03-05 | BBB | AAA | 2.00 | 12.0% | -1.5 |",
    ),
    "compare: law churn with reversal and moved offset": (
        _COMPARE,
        "Countries with a reversal: 1",
    ),
    "compare: law churn row": (
        _COMPARE,
        "| Bureaucracy | 2 | 1 | 1 | 0 |\n| Police | 1 | 0 | 0 | 1 |",
    ),
    "series: colon in the clock and field names with spaces": (
        ["series", "{a}", "AAA", "--fields", "GDP,GDP per Capita"],
        "| 2000-03-01 | 120 | 5.5 |",
    ),
    "series: every keeps the last row": (
        ["series", "{a}", "AAA", "--fields", "GDP", "--every", "2"],
        "| 2000-05-01 | 160 |\n\n3 rows",
    ),
    "series: older line prefix": (
        ["series", "{b}", "AAA", "--fields", "Civilian"],
        "| 2000-02-01 | 9 |",
    ),
    "series: changes only": (
        [
            "series",
            "{a}",
            _ALPHA,
            "--label",
            "Weekly Economic Update",
            "--fields",
            "Population Tax Rate,Corporate Tax Rate",
            "--changes",
        ],
        "| 2000-02-21 | 26 | 23 |\n\n2 rows",
    ),
    "series: spending law triplet and raw": (
        [
            "series",
            "{a}",
            _ALPHA,
            "--label",
            _LAW_LABEL,
            "--fields",
            "Bureaucracy,Bureaucracy Expected,Bureaucracy Offset,Raw Police",
        ],
        "| 2000-02-21 | 2 | 3 | 1 | 2.5 |",
    ),
    "series: no fields lists every field": (
        ["series", "{a}", "AAA", "--label", "Probe"],
        "| Date | Owned Arms | Controlled Arms | At War |",
    ),
    "series: probe label prefix": (
        ["series", "{a}", "AAA", "--label", "Probe", "--fields", "Owned Arms,At War"],
        "| 2000-03-01 | 4 | 1 |",
    ),
    "series: jumps across every subject": (
        [
            "series",
            "{a}",
            "*",
            "--label",
            "Weekly Economic Update",
            "--fields",
            "Treasury Rate",
            "--jumps",
            "1",
        ],
        "| Alpha Land | 2000-02-14 | Treasury Rate | 0.1 | 3 |\n\n1 jumps",
    ),
    "spread: quartiles and count below": (
        ["spread", "x={a}", "GDP", "--below", "150"],
        "| 2000-02 | 100.0/200.0/300.0 (n=3, 1 below 150) |",
    ),
    "spread: one country in a month": (
        ["spread", "x={a}", "GDP", "--below", "150"],
        "| 2000-05 | 160.0/160.0/160.0 (n=1, 0 below 150) |",
    ),
    "spread: country without states is left out": (
        ["spread", "x={b}", "GDP"],
        "| 2000-02 | 100.0/200.0/300.0 (n=3) |",
    ),
    "wars: spell from the first to the last war month, short spell dropped": (
        ["wars", "{a}"],
        "## War spells ({dir})\n\n| Tag | From | To | Months | Military | Civilian | GDP |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        "| AAA | 2000-02 | 2000-04 | 3 | 4 -> 6 | 10 -> 12 | 100 -> 140 |\n\n"
        "## Wars ({dir})",
    ),
    "wars: min civilian drops small countries": (
        ["wars", "{a}", "--min-civilian", "11"],
        "| --- | --- | --- | --- | --- | --- | --- |\n\n## Wars ({dir})",
    ),
    "wars: declarations and capitulations": (
        ["wars", "{a}"],
        "| 2000-03-05 | BBB | AAA | 2.00 | 12.0% | -1.5 |",
    ),
    "counts: decision id before a parenthesis": (
        _COUNTS,
        "| bankruptcy_default | 2 | 1 |\n| utility_x | 1 | 1 |\n| Total | 3 | 2 |",
    ),
    "counts: before keeps earlier months": (
        _COUNTS + ["--before", "2000.03"],
        "| Total | 2 | 2 |",
    ),
    "counts: match filters the ids": (
        ["counts", "a={a}", "b={b}", "--match", "^bankruptcy"],
        "| Total | 2 | 1 |",
    ),
    "counts: top cuts the rows": (
        _COUNTS + ["--top", "1"],
        "1 more rows not shown (--top)",
    ),
    "counts: option diff hides equal rows": (
        _COUNTS + ["--kind", "option", "--diff"],
        "| T_ev.1.a | 2 | 1 |\n| Total | 3 | 2 |",
    ),
    "counts: focus": (
        _COUNTS + ["--kind", "focus"],
        "| ZZ_first | 2 | 0 |",
    ),
    "counts: idea added and removed forms": (
        _COUNTS + ["--kind", "idea"],
        "| Idea bureau_03 removed | 2 | 0 |\n| add idea defence_03 | 1 | 0 |",
    ),
    "counts: investment by year": (
        ["counts", "a={a}", "--kind", "investment", "--by-year"],
        "| Item | 2000 | 2001 | Total |\n| --- | --- | --- | --- |\n"
        "| Alpha Land | 2 | 1 | 3 |\n| Beta Land | 0 | 1 | 1 |\n| All | 2 | 2 | 4 |",
    ),
    "laws: ranking row": (
        ["laws", "{a}"],
        "| 1 | 3 | +1 | Alpha Land |",
    ),
    "laws: ranking order and reversal count": (
        ["laws", "{a}"],
        "| 0 | 0 | +0 | Beta Land |\n\nCountries with a reversal: 1",
    ),
    "laws: one law": (
        ["laws", "{a}", "--law", "Police"],
        "| 0 | 1 | +2 | Alpha Land |",
    ),
    "laws: country trace skips an unchanged sample": (
        ["laws", "{a}", "--who", _ALPHA, "--law", "Bureaucracy"],
        "| 2000-02-07 | 2/3/0 | 0.5 | 0.25 |\n| 2000-02-14 | 3/3/0 | 0.5 | 0.25 |\n"
        "| 2000-02-21 | 2/3/1 | 0.5 | 0.25 |",
    ),
    "errors: shapes collapse paths, quoted names, tags and numbers": (
        ["errors", "{err}"],
        "     3  Invalid trigger 'FOO' in tests/one.txt line : 12\n     2  Error: \"Unknown trigger-type: ABC, near line: 3\"",
    ),
    "errors: noise is dropped and counted": (
        ["errors", "{err}"],
        "5 lines in 2 shapes (3 known noise lines dropped)",
    ),
    "errors: start skips leading lines": (
        ["errors", "{err}", "--start", "3"],
        "5 lines in 2 shapes (0 known noise lines dropped)",
    ),
    "volume: kind without the subject": (
        ["volume", "{a}"],
        "10  Monthly Benchmark: Civilian: # Military: #",
    ),
}


@pytest.mark.parametrize(
    "args, fragment", _REPORT_CASES.values(), ids=list(_REPORT_CASES)
)
def test_report(tmp_path, monkeypatch, capsys, args, fragment):
    code, out, _, paths = _run(tmp_path, monkeypatch, capsys, args)
    assert code == 0
    assert fragment.format(**paths) in out


def test_missing_log_is_reported(tmp_path, monkeypatch, capsys):
    code, _, err, _ = _run(
        tmp_path, monkeypatch, capsys, ["series", "{a}.missing", "AAA"]
    )
    assert code == 1
    assert "a.log.missing" in err


def test_series_for_an_unknown_subject_is_reported(tmp_path, monkeypatch, capsys):
    code, _, err, _ = _run(tmp_path, monkeypatch, capsys, ["series", "{a}", "NOBODY"])
    assert code == 1
    assert 'no "Monthly Benchmark" lines for NOBODY' in err


def test_compare_needs_benchmark_lines(tmp_path, monkeypatch, capsys):
    code, _, err, _ = _run(tmp_path, monkeypatch, capsys, ["compare", "x={err}"])
    assert code == 1
    assert "x: no Monthly Benchmark lines" in err


# command: (arguments with a run that ends before the other starts, message)
_NO_SHARED_MONTH_CASES = {
    "compare": (["compare", "a={a}", "late={late}"], "share no fully reported month"),
    "spread": (["spread", "a={a}", "late={late}", "GDP"], 'no "GDP" month shared'),
}


@pytest.mark.parametrize(
    "args, message", _NO_SHARED_MONTH_CASES.values(), ids=list(_NO_SHARED_MONTH_CASES)
)
def test_runs_without_a_shared_month(tmp_path, monkeypatch, capsys, args, message):
    code, _, err, _ = _run(tmp_path, monkeypatch, capsys, args)
    assert code == 1
    assert message in err


# arguments: message argparse prints
_BAD_ARGUMENT_CASES = {
    "before needs a year": (["counts", "a={a}", "--before", "20x"], "expected YYYY"),
    "every must be positive": (["series", "{a}", "AAA", "--every", "0"], "1 or more"),
}


@pytest.mark.parametrize(
    "args, message", _BAD_ARGUMENT_CASES.values(), ids=list(_BAD_ARGUMENT_CASES)
)
def test_bad_arguments_are_rejected(tmp_path, monkeypatch, capsys, args, message):
    with pytest.raises(SystemExit) as raised:
        _run(tmp_path, monkeypatch, capsys, args)
    assert raised.value.code == 2
    assert message in capsys.readouterr().err


def test_script_runs_on_its_own(tmp_path):
    paths = _write_logs(tmp_path)
    result = run_tool_script(
        "analysis/benchmark_report.py", "series", paths["a"], "AAA", "--fields", "GDP"
    )
    assert result.returncode == 0
    assert "| 2000-03-01 | 120 |" in result.stdout


def test_invalid_utf8_is_decoded_and_reported(tmp_path, monkeypatch, capsys):
    bad = tmp_path / "bad.log"
    with open(bad, "wb") as handle:
        handle.write(_monthly(2, "AAA", 10, 4, 100, 5.5).encode("utf-8") + b"\n")
        handle.write(b"[12:00:00][no_game_date]: caf\xe9\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["benchmark_report.py", "series", str(bad), "AAA", "--fields", "GDP"],
    )
    assert benchmark_report.main() == 0
    captured = capsys.readouterr()
    assert "| 2000-02-01 | 100 |" in captured.out
    assert "1 lines had invalid UTF-8" in captured.err
