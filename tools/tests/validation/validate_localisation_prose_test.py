"""Localisation prose checks: the typo watchlist, the dash, backtick and quote
conventions, and the advisory heuristics (repeated words, tripled letters,
placeholders and cut-off descriptions). All of them read loc values only."""

import json
import re
from pathlib import Path

import pytest
import validate_localisation as VL
from shared.paths import REPO_ROOT
from shared.suite import build_validator, write_under_str, yml_scan
from validator_common import Severity


def _typos(value, key="K"):
    return VL._scan_typos_text(f'l_english:\n {key}:0 "{value}"\n', "t.yml")


def _prose(value, key="sample_desc", event_keys=frozenset()):
    return VL._scan_prose_text(
        f'l_english:\n {key}: "{value}"\n', "sample.yml", event_keys
    )


def _categories(value, key="sample_desc", event_keys=frozenset()):
    return [issue.category for issue in _prose(value, key, event_keys)]


# ---- typo watchlist ----------------------------------------------------------

_AIRFORCE = "t.yml - line 2 - 'Airforce' -> 'Air Force'"

# case: (key, loc value, findings)
_TYPO_CASES = {
    "flagged in any case": ("K", "The Airforce arrived.", [_AIRFORCE]),
    "correct spellings": ("K", "The Air Force will separate the units.", []),
    "context-dependent words are not listed": (
        "K",
        "It's a matter of civilisation.",
        [],
    ),
    "keys are not scanned": ("airforce", "Some correct value", []),
    "runtime references are opaque": (
        "K",
        "$Airforce$ [Unloyal] £Airforce [?defence_breakdown_airforce|-3]",
        [],
    ),
    "prose around references": (
        "K",
        "The Airforce uses [Airforce] and £Airforce.",
        [_AIRFORCE],
    ),
}


@pytest.mark.parametrize(
    ("key", "value", "expected"), _TYPO_CASES.values(), ids=_TYPO_CASES
)
def test_typo_watchlist(key, value, expected):
    assert _typos(value, key) == expected


def test_typo_scan_finds_whole_words_on_every_line_shape(tmp_path):
    path = write_under_str(
        tmp_path,
        "localisation/english/typo_l_english.yml",
        "l_english:\r\n"
        ' A:0 "Seperate, sepe[X]rate, seperate2 and #seperate {x}"\r\n'
        ' B:0 "plain words only"\r\n'
        ' C:0 "Café Isreal xseperate"',
    )

    assert yml_scan(path, "typos") == [
        "typo_l_english.yml - line 2 - 'Seperate' -> 'separate'",
        "typo_l_english.yml - line 2 - 'seperate' -> 'separate'",
        "typo_l_english.yml - line 2 - 'seperate' -> 'separate'",
        "typo_l_english.yml - line 4 - 'Isreal' -> 'Israel'",
    ]


# The token scan is a fast path for this regex; each value must agree with it.
@pytest.mark.parametrize(
    "value",
    [
        "Seperate!",
        "SEPERATE_x",
        "sepe[x]rate",
        "Café seperate",
        "a seperated b",
        "Disproportinate, bocme",
    ],
)
def test_typo_tokens_match_a_full_regex_scan(value):
    prose = VL._TYPO_RUNTIME_REFERENCE_RE.sub("", value)
    expected = [m.group(0) for m in VL._TYPO_RE.finditer(prose)]

    assert [line.split("'")[1] for line in _typos(value)] == expected


def test_every_watchlist_entry_is_one_word_token():
    assert all(re.fullmatch(r"\w+", typo) for typo in VL._TYPO_WATCHLIST)


def test_exempt_phrase_suppresses_a_watchlist_hit(monkeypatch):
    monkeypatch.setattr(VL, "_TYPO_EXEMPTIONS", {"seperate"})
    assert _typos("seperate") == []


def test_typo_watchlist_covers_every_doc_token():
    # "it's" is possessive-rule context-dependent; "civilisation" is a
    # legitimate British spelling. Both are left out of the watchlist.
    excluded = {"it's", "civilisation"}
    doc = REPO_ROOT / ".claude" / "docs" / "typo-watchlist.md"
    tokens = set()
    for line in doc.read_text(encoding="utf-8").splitlines():
        columns = line.split("|")
        if len(columns) >= 2:
            tokens.update(m.lower() for m in re.findall(r"`([^`]+)`", columns[1]))
    missing = tokens - excluded - set(VL._TYPO_WATCHLIST)
    assert (
        not missing
    ), f"typo-watchlist.md tokens missing from _TYPO_WATCHLIST: {missing}"


# ---- dash, backtick and quote conventions ------------------------------------

# case: (loc value, [(category, severity)])
_CONVENTION_CASES = {
    "clean": ("Their economy answers to us. Their borders remain intact.", []),
    "em dash": (
        "Their economy answers to us\u2014intact.",
        [("loc-em-dash", Severity.WARNING)],
    ),
    "spaced en dash": (
        "Accept the proposal – deepen our alliance",
        [("loc-spaced-en-dash", Severity.WARNING)],
    ),
    "spaced en dash between numbers is a range": (
        "Born 9 October 1959 – 27 February 2015.",
        [],
    ),
    "backtick apostrophe": (
        "we`ll see.",
        [("loc-backtick-apostrophe", Severity.WARNING)],
    ),
    "odd number of escaped quotes": (
        'He said: \\"go now.',
        [("loc-unbalanced-quote", Severity.ERROR)],
    ),
    "balanced escaped quotes": ('He said: \\"go\\" and \\"stay\\".', []),
}


@pytest.mark.parametrize(
    ("value", "expected"), _CONVENTION_CASES.values(), ids=_CONVENTION_CASES
)
def test_prose_conventions(value, expected):
    issues = _prose(value, key="key")
    assert [(i.category, i.severity, i.file, i.line) for i in issues] == [
        (category, severity, "sample.yml", 2) for category, severity in expected
    ]


# case: (key, file)
_EN_DASH_EXEMPTION_CASES = {
    "exempt key": ("name_key", "sample.yml"),
    "exempt file": ("p", "parties_l_english.yml"),
}


@pytest.mark.parametrize(
    ("key", "basename"),
    _EN_DASH_EXEMPTION_CASES.values(),
    ids=_EN_DASH_EXEMPTION_CASES,
)
def test_spaced_en_dash_exemptions(monkeypatch, key, basename):
    monkeypatch.setattr(VL, "_SPACED_EN_DASH_EXEMPTIONS", frozenset({"name_key"}))
    monkeypatch.setattr(
        VL, "_SPACED_EN_DASH_EXEMPT_FILES", frozenset({"parties_l_english.yml"})
    )
    text = f'l_english:\n {key}:0 "Land Systems – Mowag GmbH"\n'
    assert VL._scan_prose_text(text, basename) == []


# ---- advisory heuristics -----------------------------------------------------


# Each category reports the key, a warning, and the line it came from.
@pytest.mark.parametrize(
    "value, category",
    [
        ("against the THE regime", "loc-repeated-word"),
        ("asylum seeeker", "loc-tripled-letter"),
        ("WIP", "loc-placeholder"),
        ("which'll require them", "loc-dangling-description"),
        ("the §Ythe§! regime", "loc-repeated-word"),
        ("see§[GetColor]eker§!", "loc-tripled-letter"),
        ("which'll require §Ythem§!", "loc-dangling-description"),
    ],
)
def test_warning_has_category_key_and_original_location(value, category):
    findings = _prose(value)
    assert [(f.category, f.severity, f.file, f.line) for f in findings] == [
        (category, Severity.WARNING, "sample.yml", 2)
    ]
    assert findings[0].message.startswith("sample_desc:")


@pytest.mark.parametrize("value", ["TODO", "TBD", "TDA", "WIP", "PLACEHOLDER"])
def test_exact_placeholder_in_any_value(value):
    assert _categories(value, "title") == ["loc-placeholder"]


@pytest.mark.parametrize(
    "value",
    [
        "A TODO list.",
        "todo",
        "§YTODO§!",
        "we we're ready.",
        "the, the end.",
        r"the\nthe end.",
        "III VII viii CCC NATO",
        "Mmm Naaah mmm naaah",
        "Seeeker and SEEEKER",
        "We are here for them.",
        "Invest in the [THIS.GetName]",
        "the [the the seeeker] the end.",
        "the $the_the_seeeker$ the end.",
        "the £the_the_seeeker the end.",
        "the §§ the end.",
        "seeeker_key",
        "123seeeker",
        "",
        "Select the §YDozor-A§!",
        "Model–A",
    ],
)
def test_nonfindings(value):
    assert _prose(value) == []


# case: (loc value, key, event description keys, categories)
_HEURISTIC_CASES = {
    "stretched exemption matches whole words only": (
        "The mmmaaaaan arrived.",
        "sample_desc",
        frozenset(),
        ["loc-tripled-letter"],
    ),
    "a _desc key is a description": (
        "We must invest in the",
        "sample_desc",
        frozenset(),
        ["loc-dangling-description"],
    ),
    "an event desc key is a description": (
        "We must invest in the",
        "custom_text",
        frozenset({"custom_text"}),
        ["loc-dangling-description"],
    ),
    "a .d suffix alone is not a description": (
        "We must invest in the",
        "event.1.d",
        frozenset(),
        [],
    ),
    "_desc inside a key is not a description": (
        "We must invest in the",
        "focus_desc_extra",
        frozenset(),
        [],
    ),
    "every occurrence is reported": (
        "the the the seeeker seeeker",
        "sample_desc",
        frozenset(),
        [
            "loc-repeated-word",
            "loc-repeated-word",
            "loc-tripled-letter",
            "loc-repeated-word",
            "loc-tripled-letter",
        ],
    ),
    "repeated contraction": (
        "we're we're ready",
        "sample_desc",
        frozenset(),
        ["loc-repeated-word"],
    ),
    "repeat matching casefolds": (
        "Straße STRASSE",
        "sample_desc",
        frozenset(),
        ["loc-repeated-word"],
    ),
    "curly apostrophe contraction": (
        "we’re we’re ready",
        "sample_desc",
        frozenset(),
        ["loc-repeated-word"],
    ),
}


@pytest.mark.parametrize(
    ("value", "key", "event_keys", "expected"),
    _HEURISTIC_CASES.values(),
    ids=_HEURISTIC_CASES,
)
def test_prose_heuristics(value, key, event_keys, expected):
    assert _categories(value, key, event_keys) == expected


def test_exemptions_are_scoped_to_key_and_word(monkeypatch):
    monkeypatch.setattr(VL, "_REPEATED_WORD_EXEMPTIONS", {"sample_desc:had"})
    monkeypatch.setattr(VL, "_DANGLING_DESCRIPTION_EXEMPTIONS", {"sample_desc:them"})
    assert _prose("We had had enough of them") == []
    assert _categories("We had had enough of them", "other_desc") == [
        "loc-repeated-word",
        "loc-dangling-description",
    ]
    assert _categories("The the end.") == ["loc-repeated-word"]
    assert _categories("We must invest in the") == ["loc-dangling-description"]


_FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "loc_prose_5127.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("fixture", _FIXTURES, ids=lambda fixture: fixture["name"])
def test_exact_historical_strings(fixture):
    text = "l_english:\n" + fixture["line"] + "\n"
    assert [
        issue.category for issue in VL._scan_prose_text(text, "historical.yml")
    ] == fixture["categories"]
    assert len(VL._scan_typos_text(text, "historical.yml")) == fixture["typos"]


# ---- the shared scan and event descriptions ----------------------------------


def test_worker_preserves_comments_bom_crlf_and_inline_hashes(tmp_path):
    path = write_under_str(
        tmp_path,
        "fixture.yml",
        "\ufeffl_english:\r\n # the the seeeker\r\n\r\n"
        ' the_the_seeeker: "Clean." # "the the seeeker"\r\n'
        ' sample:0 "# the the seeeker"\r\n',
    )
    assert [(i.category, i.line) for i in yml_scan(path, "prose")] == [
        ("loc-repeated-word", 5),
        ("loc-tripled-letter", 5),
    ]


def test_shared_scan_reads_each_english_file_once_and_reports_every_category(
    tmp_path, monkeypatch
):
    path = write_under_str(
        tmp_path,
        "localisation/english/a_l_english.yml",
        'l_english:\n a: "the the seeeker — we`ll \\"wait"\n'
        ' b: "WIP"\n c_desc: "which will require them"\n d: "seperate"\n',
    )
    write_under_str(tmp_path, "localisation/french/a.yml", 'l_french:\n a: "WIP"\n')
    calls = []
    original = VL.read_text_strict

    def read(filename):
        calls.append(filename)
        return original(filename)

    monkeypatch.setattr(VL, "read_text_strict", read)
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_prose_conventions()
    validator.validate_typo_watchlist()
    assert calls == [path]
    assert {i.category for i in validator._issues} == {
        "loc-repeated-word",
        "loc-tripled-letter",
        "loc-placeholder",
        "loc-dangling-description",
        "loc-em-dash",
        "loc-backtick-apostrophe",
        "loc-unbalanced-quote",
        "loc-typo-watchlist",
    }
    assert {i.category for i in validator._issues if i.severity == Severity.ERROR} == {
        "loc-unbalanced-quote",
        "loc-typo-watchlist",
    }
    assert validator.errors_found == 2
    assert validator.warnings_found == 6


_EVENTS = (
    "add_namespace = sample\n"
    "country_event = sample.2\n"
    "# desc = commented.d\n"
    "other_block = {{ desc = unrelated.d }}\n"
    "{event_type} = {{\n"
    " id = sample.1\n"
    " {description}\n"
    " desc = {{ text = alternate_text trigger = {{ always = no }} }}\n"
    ' immediate = {{ log = "{{ desc = quoted.d }}" }}\n'
    " option = {{ name = ukraine_light_transport_tender.1.d }}\n"
    " option = {{ name = sample.1.d }}\n"
    "}}\n"
)

# case: (event type, desc line, staged run)
_EVENT_DESCRIPTION_CASES = {
    "country_event": ("country_event", "desc = actual_text", False),
    "news_event": ("news_event", "desc = actual_text", False),
    "state_event": ("state_event", "desc = actual_text", False),
    "unit_leader_event": ("unit_leader_event", "desc = actual_text", False),
    "operative_leader_event": ("operative_leader_event", "desc = actual_text", False),
    "quoted desc": ("country_event", 'desc = "actual_text"', False),
    "staged run reads every event": ("country_event", "desc = actual_text", True),
}


@pytest.mark.parametrize(
    ("event_type", "description", "staged_only"),
    _EVENT_DESCRIPTION_CASES.values(),
    ids=_EVENT_DESCRIPTION_CASES,
)
def test_event_descriptions_follow_references_not_suffixes(
    tmp_path, monkeypatch, event_type, description, staged_only
):
    write_under_str(
        tmp_path,
        "events/nested/fixture.txt",
        _EVENTS.format(event_type=event_type, description=description),
    )
    relative = "localisation/english/fixture.yml"
    write_under_str(
        tmp_path,
        relative,
        'l_english:\n actual_text: "We must invest in the"\n'
        ' alternate_text: "We must invest in the"\n'
        ' ukraine_light_transport_tender.1.d: "Select the §YDozor-A§!"\n'
        ' sample.1.d: "Choose one of them"\n'
        ' commented.d: "We must invest in the"\n'
        ' unrelated.d: "We must invest in the"\n'
        ' quoted.d: "We must invest in the"\n',
    )
    monkeypatch.setenv("MD_STAGED_FILES", relative)
    validator = build_validator(VL.Validator, tmp_path, staged_only=staged_only)
    validator.validate_prose_conventions()
    assert [(issue.category, issue.line) for issue in validator._issues] == [
        ("loc-dangling-description", 2),
        ("loc-dangling-description", 3),
    ]


def test_event_description_d_key_survives_worker_pool(
    tmp_path, monkeypatch, pool_sizes
):
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    write_under_str(
        tmp_path,
        "events/fixture.txt",
        "country_event = { id = sample.1 desc = sample.1.d "
        "option = { name = sample.1.a } }\n",
    )
    for index in range(12):
        write_under_str(
            tmp_path,
            f"localisation/english/f{index:02}.yml",
            'l_english:\n sample.1.d: "We must invest in the"\n',
        )

    def run(workers):
        validator = VL.Validator(str(tmp_path), use_colors=False, workers=workers)
        try:
            validator.validate_prose_conventions()
            return [(i.category, i.file, i.line) for i in validator._issues]
        finally:
            validator._close_pool()

    pooled = run(2)
    assert pool_sizes and set(pool_sizes) == {2}
    assert pooled == run(1)
    assert len(pooled) == 12
    assert all(row[0] == "loc-dangling-description" for row in pooled)
