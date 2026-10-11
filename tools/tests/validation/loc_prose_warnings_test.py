"""Prose heuristics keep runtime text opaque and report advisory, located findings."""

import json
from pathlib import Path

import pytest
import validate_localisation as VL
from shared.suite import write_under_str, yml_scan
from validator_common import Severity


def _scan(value, key="sample_desc"):
    return VL._scan_prose_text(f'l_english:\n {key}: "{value}"\n', "sample.yml")


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
    findings = _scan(value)
    assert len(findings) == 1
    finding = findings[0]
    assert (finding.category, finding.severity, finding.file, finding.line) == (
        category,
        Severity.WARNING,
        "sample.yml",
        2,
    )
    assert finding.message.startswith("sample_desc:")


@pytest.mark.parametrize("value", ["TODO", "TBD", "TDA", "WIP", "PLACEHOLDER"])
def test_exact_placeholder_in_any_value(value):
    assert [issue.category for issue in _scan(value, "title")] == ["loc-placeholder"]


@pytest.mark.parametrize(
    "value",
    [
        "A TODO list.",
        "PLACEHOLDERS",
        "todo",
        "§YTODO§!",
        "we we're ready.",
        "He had. Had he?",
        "the, the end.",
        r"the\nthe end.",
        "III VII viii CCC NATO",
        "Mmm Naaah mmm naaah",
        "Seeeker and SEEEKER",
        "maaaaan uhhh",
        "We are here for them.",
        "We are here for them!",
        "Invest in the [THIS.GetName]",
        "Invest in the $TARGET$",
        "Invest in the £target",
        "the [the the seeeker] the end.",
        "the $the_the_seeeker$ the end.",
        "the £the_the_seeeker the end.",
        "the [SCOPE.GetName] the end.",
        "see[SCOPE.GetName]eker",
        "the §§ the end.",
        "the $$ the end.",
        "that §Y[GetName]§! that end.",
        "seeeker_key",
        "123seeeker",
        "",
    ],
)
def test_nonfindings(value):
    assert _scan(value) == []


def test_stretched_exemption_matches_only_whole_words():
    assert [issue.category for issue in _scan("The mmmaaaaan arrived.")] == [
        "loc-tripled-letter"
    ]


def test_non_event_description_suffix_is_checked():
    assert _scan("We must invest in the")[0].category == "loc-dangling-description"


@pytest.mark.parametrize("key", ["event.1.d", "event.1.desc", "custom_text"])
def test_event_description_keys_are_checked(key):
    issues = VL._scan_prose_text(
        f'l_english:\n {key}: "We must invest in the"\n', "sample.yml", {key}
    )
    assert [issue.category for issue in issues] == ["loc-dangling-description"]


@pytest.mark.parametrize(
    "key", ["focus", "event.1.t", "event.1.a", "event.1.d", "focus_desc_extra"]
)
def test_other_suffixes_are_not_descriptions(key):
    assert _scan("We must invest in the", key) == []


def test_exemptions_are_scoped_to_key_and_word(monkeypatch):
    monkeypatch.setattr(VL, "_REPEATED_WORD_EXEMPTIONS", {"sample_desc:had"})
    monkeypatch.setattr(VL, "_DANGLING_DESCRIPTION_EXEMPTIONS", {"sample_desc:them"})
    assert _scan("We had had enough of them") == []
    assert [i.category for i in _scan("We had had enough of them", "other_desc")] == [
        "loc-repeated-word",
        "loc-dangling-description",
    ]
    assert _scan("The the end.")[0].category == "loc-repeated-word"
    assert _scan("We must invest in the")[0].category == "loc-dangling-description"


def test_all_occurrences_and_contractions():
    assert [i.category for i in _scan("the the the seeeker seeeker")] == [
        "loc-repeated-word",
        "loc-repeated-word",
        "loc-tripled-letter",
        "loc-repeated-word",
        "loc-tripled-letter",
    ]
    assert _scan("we're we're ready")[0].category == "loc-repeated-word"


def test_worker_preserves_comments_bom_crlf_and_inline_hashes(tmp_path):
    path = write_under_str(
        tmp_path,
        "fixture.yml",
        "\ufeffl_english:\r\n # the the seeeker\r\n\r\n"
        ' the_the_seeeker: "Clean." # "the the seeeker"\r\n'
        ' sample:0 "# the the seeeker"\r\n',
    )
    issues = yml_scan(path, "prose")
    assert [(i.category, i.line) for i in issues] == [
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
    validator = VL.Validator(str(tmp_path), use_colors=False, workers=1)
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


def test_typo_watchlist_match_is_an_error(tmp_path):
    write_under_str(
        tmp_path,
        "localisation/english/a_l_english.yml",
        'l_english:\n a: "seperate"\n',
    )
    validator = VL.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.validate_typo_watchlist()
    assert [(i.severity, i.category) for i in validator._issues] == [
        (Severity.ERROR, "loc-typo-watchlist")
    ]


def test_staged_selection_does_not_expand_to_other_english_files(tmp_path, monkeypatch):
    for name in ("selected", "untouched"):
        write_under_str(
            tmp_path,
            f"localisation/english/{name}.yml",
            'l_english:\n desc: "WIP"\n',
        )
    monkeypatch.setenv("MD_STAGED_FILES", "localisation/english/selected.yml")
    validator = VL.Validator(str(tmp_path), staged_only=True, workers=1)
    validator.validate_prose_conventions()
    assert [(i.file, i.category) for i in validator._issues] == [
        ("selected.yml", "loc-placeholder")
    ]


@pytest.mark.parametrize(
    "event_type",
    [
        "country_event",
        "news_event",
        "state_event",
        "unit_leader_event",
        "operative_leader_event",
    ],
)
@pytest.mark.parametrize(
    "description",
    [
        "desc = actual_text",
        'desc = "actual_text"',
        "desc = { text = actual_text trigger = { always = yes } }",
    ],
)
@pytest.mark.parametrize("staged_only", [False, True])
def test_event_descriptions_follow_references_not_suffixes(
    tmp_path, monkeypatch, event_type, description, staged_only
):
    write_under_str(
        tmp_path,
        "events/nested/fixture.txt",
        "add_namespace = sample\n"
        "country_event = sample.2\n"
        "# desc = commented.d\n"
        "other_block = { desc = unrelated.d }\n"
        f"{event_type} = {{\n"
        " id = sample.1\n"
        f" {description}\n"
        " desc = { text = alternate_text trigger = { always = no } }\n"
        ' immediate = { log = "{ desc = quoted.d }" }\n'
        " option = { name = ukr_light_transport_tender.1.d }\n"
        " option = { name = sample.1.d }\n"
        "}\n",
    )
    relative = "localisation/english/fixture.yml"
    write_under_str(
        tmp_path,
        relative,
        'l_english:\n actual_text: "We must invest in the"\n'
        ' alternate_text: "We must invest in the"\n'
        ' ukr_light_transport_tender.1.d: "Select the §YDozor-A§!"\n'
        ' sample.1.d: "Choose one of them"\n'
        ' commented.d: "We must invest in the"\n'
        ' unrelated.d: "We must invest in the"\n'
        ' quoted.d: "We must invest in the"\n',
    )
    monkeypatch.setenv("MD_STAGED_FILES", relative)
    validator = VL.Validator(
        str(tmp_path), staged_only=staged_only, use_colors=False, workers=1
    )
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


@pytest.mark.parametrize("value", ["Select the §YDozor-A§!", "Model-A", "Model–A"])
def test_vehicle_suffix_is_not_a_dangling_article(value):
    assert _scan(value) == []


FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "loc_prose_5127.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda fixture: fixture["name"])
def test_exact_historical_strings(fixture):
    text = "l_english:\n" + fixture["line"] + "\n"
    assert [
        issue.category for issue in VL._scan_prose_text(text, "historical.yml")
    ] == (fixture["categories"])
    assert len(VL._scan_typos_text(text, "historical.yml")) == fixture["typos"]


@pytest.mark.parametrize("value", ["Straße STRASSE", "café CAFÉ", "we’re we’re ready"])
def test_non_ascii_repetition_keeps_full_casefold_matching(value):
    assert [issue.category for issue in _scan(value)] == ["loc-repeated-word"]
