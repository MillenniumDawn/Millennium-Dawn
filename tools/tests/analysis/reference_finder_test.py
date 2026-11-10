"""The "find unreferenced X" analysis tools and calculate_days.py."""

import sys

import calculate_days
import find_idea_references as ideas
import find_scripted_loc_references as scripted_loc
import pytest
from shared.suite import write_tree

_IDEAS_FILE = "common/ideas/TST.txt"


def _ideas(*entries):
    body = "".join(f"\t\t{entry} = {{\n\t\t}}\n" for entry in entries)
    return f"ideas = {{\n\tcountry = {{\n{body}\t}}\n}}\n"


# case: (ideas file text, extracted names)
_IDEA_NAME_CASES = {
    "ideas at depth two": (_ideas("TST_one", "TST_two"), ["TST_one", "TST_two"]),
    "a repeated name once": (_ideas("TST_one", "TST_one"), ["TST_one"]),
    "keyword and tag-like keys": (_ideas("modifier", "allowed", "TST"), []),
    "keys inside an idea": (
        "ideas = {\n\tcountry = {\n\t\tTST_one = {\n"
        "\t\t\tmodifier = {\n\t\t\t}\n\t\t}\n\t}\n}\n",
        ["TST_one"],
    ),
    "a block opened at another depth": ("TST_top = {\n}\n", []),
}


@pytest.mark.parametrize(
    ("text", "names"), _IDEA_NAME_CASES.values(), ids=_IDEA_NAME_CASES
)
def test_extract_idea_names(tmp_path, text, names):
    path = write_tree(tmp_path, {_IDEAS_FILE: text}) / _IDEAS_FILE
    assert ideas.extract_idea_names(path) == names


_DECISION = "common/decisions/d.txt"
_MIO = "common/military_industrial_organization/organizations/TST.txt"

# case: (files, (file, line) references to TST_idea)
_IDEA_REFERENCE_CASES = {
    "has_idea": ({_DECISION: "a = { has_idea = TST_idea }\n"}, [(_DECISION, 1)]),
    "bare name in an add_ideas block": (
        {_DECISION: "add_ideas = {\n\tTST_other\n\tTST_idea\n}\nTST_idea\n"},
        [(_DECISION, 3)],
    ),
    "braces in a comment do not hold the block open": (
        {_DECISION: "add_ideas = { # }\n\tTST_idea\n}\nTST_idea\n"},
        [(_DECISION, 2)],
    ),
    "mention outside an idea effect": (
        {_DECISION: "set_country_flag = TST_idea\n"},
        [],
    ),
    "name inside a longer token": ({_DECISION: "has_idea = TST_idea_two\n"}, []),
    "own definition is not a reference": ({_IDEAS_FILE: _ideas("TST_idea")}, []),
    "has_idea in another ideas file": (
        {
            _IDEAS_FILE: _ideas("TST_idea"),
            "common/ideas/other.txt": "allowed = {\n\thas_idea = TST_idea\n}\n",
        },
        [("common/ideas/other.txt", 2)],
    ),
    "add_ideas in a MIO trait": ({_MIO: "add_ideas = TST_idea\n"}, [(_MIO, 1)]),
    "name built from a scope substitution": (
        {_DECISION: "remove_ideas = TST_[THISTAG]\n"},
        [(_DECISION, 1)],
    ),
}


@pytest.mark.parametrize(
    ("files", "expected"), _IDEA_REFERENCE_CASES.values(), ids=_IDEA_REFERENCE_CASES
)
def test_idea_references(tmp_path, monkeypatch, files, expected):
    monkeypatch.setattr(ideas, "REPO_ROOT", tmp_path)
    write_tree(tmp_path, files)
    search = ideas.make_idea_searcher([tmp_path / d for d in ideas.SEARCH_DIRS])

    refs = search(["TST_idea"])

    assert [(rel, line) for rel, line, _text in refs["TST_idea"]] == expected


def test_idea_search_with_no_names_finds_nothing(tmp_path):
    assert ideas.make_idea_searcher([tmp_path])([]) == {}


_LOC_SOURCE = "common/scripted_localisation/TST.txt"

# case: (scripted localisation file text, extracted names)
_LOC_NAME_CASES = {
    "defined_text names": (
        "defined_text = {\n\tname = GetOne\n}\ndefined_text = {\n\tname = GetTwo\n}\n",
        ["GetOne", "GetTwo"],
    ),
    "a repeated name once": ("name = GetOne\nname = GetOne\n", ["GetOne"]),
    "name with trailing tokens": ("name = GetOne # note\n", []),
}


@pytest.mark.parametrize(
    ("text", "names"), _LOC_NAME_CASES.values(), ids=_LOC_NAME_CASES
)
def test_extract_scripted_loc_names(tmp_path, text, names):
    path = write_tree(tmp_path, {_LOC_SOURCE: text}) / _LOC_SOURCE
    assert scripted_loc.extract_scripted_loc_names(path) == names


# case: (files, (file, line) references to GetOne)
_LOC_REFERENCE_CASES = {
    "own definition line is not a reference": (
        {_LOC_SOURCE: "defined_text = {\n\tname = GetOne\n}\n"},
        [],
    ),
    "another file's name line is a reference": (
        {"common/scripted_localisation/other.txt": "name = GetOne\n"},
        [("common/scripted_localisation/other.txt", 1)],
    ),
    "bracketed use in localisation": (
        {"localisation/english/a_l_english.yml": ' A:0 "[GetOne]"\n'},
        [("localisation/english/a_l_english.yml", 1)],
    ),
    "bare word in localisation": (
        {"localisation/english/a_l_english.yml": ' A:0 "GetOne"\n'},
        [],
    ),
    "non-yml file under localisation": (
        {"localisation/english/notes.txt": "[GetOne]\n"},
        [],
    ),
    "gui text": (
        {"interface/a.gui": 'text = "[GetOne]"\n'},
        [("interface/a.gui", 1)],
    ),
    "one reference per line": (
        {"events/e.txt": "desc = GetOne GetOne\n"},
        [("events/e.txt", 1)],
    ),
}


@pytest.mark.parametrize(
    ("files", "expected"), _LOC_REFERENCE_CASES.values(), ids=_LOC_REFERENCE_CASES
)
def test_scripted_loc_references(tmp_path, monkeypatch, files, expected):
    monkeypatch.setattr(scripted_loc, "REPO_ROOT", tmp_path)
    write_tree(tmp_path, files)
    dirs = [tmp_path / d for d in (*scripted_loc.SEARCH_DIRS, "common")]
    search = scripted_loc.make_scripted_loc_searcher(dirs, tmp_path / _LOC_SOURCE)

    refs = search(["GetOne"])

    assert [(rel, line) for rel, line, _text in refs["GetOne"]] == expected


def test_scripted_loc_search_with_no_names_finds_nothing(tmp_path):
    search = scripted_loc.make_scripted_loc_searcher([tmp_path], tmp_path / "x.txt")
    assert search([]) == {}


@pytest.fixture
def idea_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(ideas, "REPO_ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    write_tree(
        tmp_path,
        {
            _IDEAS_FILE: _ideas("TST_used", "TST_unused"),
            "common/decisions/d.txt": "a = { has_idea = TST_used }\n",
        },
    )
    return tmp_path


def _run_ideas(monkeypatch, *args, answer="n"):
    monkeypatch.setattr(sys, "argv", ["find_idea_references.py", *args])
    monkeypatch.setattr("builtins.input", lambda _prompt: answer)
    ideas.main()


def test_unreferenced_ideas_are_listed(idea_repo, monkeypatch, capsys):
    _run_ideas(monkeypatch, _IDEAS_FILE, "--no-report")

    out = capsys.readouterr().out
    assert "UNREFERENCED IDEAS (consider removing):\n  - TST_unused\n" in out
    assert "  Referenced: 1\n" in out
    assert "TST_used" not in out
    assert not list(idea_repo.glob("*.txt"))


def test_show_all_lists_each_reference(idea_repo, monkeypatch, capsys):
    _run_ideas(monkeypatch, _IDEAS_FILE, "--show-all", "--no-report")

    out = capsys.readouterr().out
    assert "Referenced: TST_used (1 refs)" in out
    assert "common/decisions/d.txt:1 -> a = { has_idea = TST_used }" in out


def test_all_referenced_says_so(idea_repo, monkeypatch, capsys):
    write_tree(idea_repo, {"common/decisions/e.txt": "has_idea = TST_unused\n"})

    _run_ideas(monkeypatch, _IDEAS_FILE, "--no-report")

    assert "All ideas are referenced" in capsys.readouterr().out


# case: (extra args, report file prefix, lines the report holds)
_REPORT_CASES = {
    "unreferenced": (
        (),
        "unreferenced_ideas_TST_",
        ["Unreferenced Ideas Report", "  - TST_unused"],
    ),
    "show all": (
        ("--show-all",),
        "all_idea_references_TST_",
        ["All Idea References Report", "  TST_used (1 refs):"],
    ),
}


@pytest.mark.parametrize(
    ("args", "prefix", "lines"), _REPORT_CASES.values(), ids=_REPORT_CASES
)
def test_report_is_written_on_request(idea_repo, monkeypatch, args, prefix, lines):
    _run_ideas(monkeypatch, _IDEAS_FILE, *args, answer="y")

    (report,) = idea_repo.glob("*.txt")
    assert report.name.startswith(prefix)
    assert set(lines) <= set(report.read_text(encoding="utf-8").splitlines())


def test_closed_prompt_writes_no_report(idea_repo, monkeypatch):
    def closed(_prompt):
        raise EOFError

    monkeypatch.setattr(sys, "argv", ["find_idea_references.py", _IDEAS_FILE])
    monkeypatch.setattr("builtins.input", closed)

    ideas.main()

    assert not list(idea_repo.glob("*.txt"))


@pytest.mark.parametrize(
    ("files", "message"),
    [({}, "not found"), ({_IDEAS_FILE: "ideas = {\n}\n"}, "No ideas found")],
    ids=["missing file", "file without ideas"],
)
def test_finder_exits_without_ideas(tmp_path, monkeypatch, files, message):
    monkeypatch.chdir(tmp_path)
    write_tree(tmp_path, files)

    with pytest.raises(SystemExit, match=message):
        _run_ideas(monkeypatch, _IDEAS_FILE, "--no-report")


def test_scripted_loc_finder_reports_an_unused_name(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(scripted_loc, "REPO_ROOT", tmp_path)
    write_tree(
        tmp_path,
        {
            _LOC_SOURCE: "defined_text = {\n\tname = GetUsed\n}\n"
            "defined_text = {\n\tname = GetUnused\n}\n",
            "localisation/english/a_l_english.yml": ' A:0 "[GetUsed]"\n',
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["find_scripted_loc_references.py", str(tmp_path / _LOC_SOURCE), "--no-report"],
    )

    scripted_loc.main()

    out = capsys.readouterr().out
    assert "  - GetUnused\n" in out
    assert "  - GetUsed\n" not in out


# case: (answers, printed lines)
_DAY_CASES = {
    "start date": (["2000.1.1"], ["Days since 2000: 0"]),
    "later year and month": (["2001.3.2"], ["Days since 2000: 425"]),
    "year before 2000": (["1999.1.1"], ["Error: Year is less than 2000."]),
    "month out of range": (["2000.13.1"], ["Error: Month out of range."]),
    "no leap day": (["2004.2.29"], ["Error: Days out of range."]),
    "loop keeps asking": (
        ["2000.0.1", "2000.12.31"],
        ["Error: Month out of range.", "Days since 2000: 364"],
    ),
}


@pytest.mark.parametrize(("answers", "printed"), _DAY_CASES.values(), ids=_DAY_CASES)
def test_calculate_days(monkeypatch, capsys, answers, printed):
    pending = iter(answers)

    def answer(_prompt):
        try:
            return next(pending)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", answer)

    with pytest.raises(EOFError):
        calculate_days.main()

    assert capsys.readouterr().out.splitlines() == printed
