"""Tests for the event standardizer.

Regression guard for the log-injection bug: `_option_has_effects` scanned the
option HEADER line and so always returned True, injecting a `log =` line into
effectless options (violating "log only if the option has effects"). It must scan
only the option body, and the injected log's indent must follow the body (2-tab
files get a 2-tab line, not a hardcoded 3-tab one).
"""

import sys

import standardize_events
from standardize_events import (
    EventStandardizer,
    _option_body,
    _option_has_effects,
    _option_indent,
    _option_log_line,
)


def test_standardize_file_writes_lf_on_every_platform(tmp_path):
    source = tmp_path / "events.txt"
    source.write_bytes("\n".join(_EVENT).encode("utf-8") + b"\n")

    assert EventStandardizer().standardize_file(str(source), str(source))

    assert b"\r\n" not in source.read_bytes()


def _option(lines):
    return [line + "\n" for line in lines]


def _standardize_event(lines):
    std = EventStandardizer()
    block = [line + "\n" for line in lines]
    return std.format_block(std.extract_properties(block))


def test_effectless_option_has_no_effects():
    option = _option(
        [
            "\toption = {",
            "\t\tname = test.1.a",
            "\t\tai_chance = { factor = 1 }",
            "\t}",
        ]
    )
    assert not _option_has_effects(option)


def test_option_with_effect_detected():
    option = _option(
        [
            "\toption = {",
            "\t\tname = test.1.b",
            "\t\tadd_political_power = 10",
            "\t}",
        ]
    )
    assert _option_has_effects(option)


def test_log_line_indent_matches_2tab_body():
    option = _option(
        [
            "\toption = {",
            "\t\tname = test.1.a",
            "\t\tadd_political_power = 10",
            "\t}",
        ]
    )
    assert (
        _option_log_line(option)
        == '\t\tlog = "[GetDateText]: [This.GetName]: test.1.a executed"'
    )


def test_log_line_indent_matches_3tab_body():
    option = _option(
        [
            "\t\toption = {",
            "\t\t\tname = test.1.a",
            "\t\t\tadd_political_power = 10",
            "\t\t}",
        ]
    )
    assert (
        _option_log_line(option)
        == '\t\t\tlog = "[GetDateText]: [This.GetName]: test.1.a executed"'
    )


_EVENT = [
    "country_event = {",
    "\tid = test.1",
    "\ttitle = test.1.t",
    "\tdesc = test.1.d",
    "\tis_triggered_only = yes",
    "",
    "\toption = {",
    "\t\tname = test.1.a",
    "\t\tadd_political_power = 10",
    "\t}",
    "",
    "\toption = {",
    "\t\tname = test.1.b",
    "\t\tai_chance = { factor = 1 }",
    "\t}",
    "}",
]


def test_effectless_option_gets_no_log_effectful_does():
    text = "\n".join(_standardize_event(_EVENT))
    # Effectful option gets exactly one log, indented at the 2-tab body.
    assert '\t\tlog = "[GetDateText]: [This.GetName]: test.1.a executed"' in text
    assert text.count("log =") == 1
    # Effectless option (name + ai_chance only) gets no log.
    assert "test.1.b executed" not in text


def test_content_preserved():
    text = "\n".join(_standardize_event(_EVENT))
    for token in (
        "id = test.1",
        "title = test.1.t",
        "desc = test.1.d",
        "add_political_power = 10",
        "name = test.1.b",
        "ai_chance = { factor = 1 }",
    ):
        assert token in text


def test_event_idempotent():
    once = _standardize_event(_EVENT)
    twice = _standardize_event(once)
    assert once == twice


_COMMENTED_EVENT = [
    "country_event = {",
    "\tid = test.2",
    "\tis_triggered_only = yes",
    "",
    "\t# We stand by our allies!",
    "\toption = {",
    "\t\tname = test.2.a",
    "\t}",
    "",
    "\t# Let them fall...",
    "\toption = {",
    "\t\tname = test.2.b",
    "\t}",
    "}",
]


def test_comment_hugs_the_option_it_describes():
    out = _standardize_event(_COMMENTED_EVENT)
    pairs = [
        (line.strip(), out[i + 1].strip())
        for i, line in enumerate(out)
        if line.lstrip().startswith("#")
    ]
    assert pairs == [
        ("# We stand by our allies!", "option = { name = test.2.a }"),
        ("# Let them fall...", "option = { name = test.2.b }"),
    ]


def test_comment_after_the_last_option_is_kept():
    out = _standardize_event(_COMMENTED_EVENT[:-1] + ["\t# Nothing follows this", "}"])
    assert "\t# Nothing follows this" in out


def test_packed_single_line_option_effect_detected():
    # A fully packed option (header + body + closer on one physical line) must
    # still have its effects detected -- previously the empty [1:-1] slice hid them.
    option = _option(["\toption = { name = test.1.a  add_political_power = 10 }"])
    assert _option_has_effects(option)


def test_packed_effectless_option_not_detected():
    option = _option(["\toption = { name = test.1.a  ai_chance = { factor = 1 } }"])
    assert not _option_has_effects(option)


_PACKED_EVENT = [
    "country_event = {",
    "\tid = test.2",
    "\ttitle = test.2.t",
    "\tdesc = test.2.d",
    "\tis_triggered_only = yes",
    "",
    "\toption = { name = test.2.a  add_political_power = 10 }",
    "}",
]


def test_packed_option_gets_log_inside_block():
    out = _standardize_event(_PACKED_EVENT)
    text = "\n".join(out)
    # Effect preserved and the log lands inside the option's braces, not after it.
    assert "add_political_power = 10" in text
    log_idx = next(i for i, ln in enumerate(out) if "test.2.a executed" in ln)
    open_idx = next(i for i, ln in enumerate(out) if ln.strip() == "option = {")
    close_idx = next(
        i for i, ln in enumerate(out) if i > open_idx and ln.strip() == "}"
    )
    assert open_idx < log_idx < close_idx


def test_packed_option_standardization_idempotent():
    once = _standardize_event(_PACKED_EVENT)
    twice = _standardize_event(once)
    assert once == twice


def test_multiline_option_packed_interior_line_effect_detected():
    # Multi-line option whose body packs an effect after a skipped statement on
    # one physical interior line -- effect detection must still fire.
    option = _option(
        [
            "\toption = {",
            "\t\tname = test.1.a",
            "\t\tai_chance = { factor = 1 }  add_political_power = 10",
            "\t}",
        ]
    )
    assert _option_has_effects(option)


def test_multiline_ai_chance_only_has_no_effects():
    # (defect) an option whose only body is name + a multi-line ai_chance (with a
    # nested modifier block) must not be misread as having effects — brace depth
    # has to be tracked so the ai_chance interior is swallowed whole.
    option = _option(
        [
            "\toption = {",
            "\t\tname = bul_mech.19.b",
            "\t\tai_chance = {",
            "\t\t\tbase = 40",
            "\t\t\tmodifier = {",
            "\t\t\t\tadd = 30",
            "\t\t\t\thas_opinion = { target = BUL value < 0 }",
            "\t\t\t}",
            "\t\t}",
            "\t}",
        ]
    )
    assert not _option_has_effects(option)


def test_statement_packed_on_closer_line_detected():
    # (defect) an effect jammed onto the closer line (`add_pp = 10 }`) was hidden
    # by the plain [1:-1] body slice — the closer's code must be scanned too.
    option = _option(
        [
            "\toption = {",
            "\t\tname = test.5.a",
            "\t\tadd_political_power = 10 }",
        ]
    )
    assert _option_has_effects(option)


_MULTILINE_AI_CHANCE_EVENT = [
    "country_event = {",
    "\tid = test.4",
    "\ttitle = test.4.t",
    "\tdesc = test.4.d",
    "\tis_triggered_only = yes",
    "",
    "\toption = {",
    "\t\tname = test.4.b",
    "\t\tai_chance = {",
    "\t\t\tbase = 40",
    "\t\t\tmodifier = {",
    "\t\t\t\tadd = 30",
    "\t\t\t\thas_opinion = { target = BUL value < 0 }",
    "\t\t\t}",
    "\t\t}",
    "\t}",
    "}",
]


def test_multiline_ai_chance_only_option_gets_no_log():
    text = "\n".join(_standardize_event(_MULTILINE_AI_CHANCE_EVENT))
    # Effectless option (name + multi-line ai_chance only) gets no log.
    assert "test.4.b executed" not in text
    assert "log =" not in text


_PACKED_INTERIOR_EVENT = [
    "country_event = {",
    "\tid = test.3",
    "\ttitle = test.3.t",
    "\tdesc = test.3.d",
    "\tis_triggered_only = yes",
    "",
    "\toption = {",
    "\t\tname = test.3.a",
    "\t\tai_chance = { factor = 1 }  add_political_power = 10",
    "\t}",
    "}",
]


def test_multiline_packed_interior_option_gets_log():
    text = "\n".join(_standardize_event(_PACKED_INTERIOR_EVENT))
    # Effect on the packed interior line is detected, so the option gets its log.
    assert '\t\tlog = "[GetDateText]: [This.GetName]: test.3.a executed"' in text
    assert "add_political_power = 10" in text


_HEADER_COMMENT_EVENT = [
    "country_event = { # 2001 Election Notification (Khatami vs Tavakkoli)",
] + _EVENT[1:]


def test_header_comment_preserved():
    out = _standardize_event(_HEADER_COMMENT_EVENT)
    assert (
        out[0]
        == "country_event = { # 2001 Election Notification (Khatami vs Tavakkoli)"
    )


def test_header_comment_idempotent():
    once = _standardize_event(_HEADER_COMMENT_EVENT)
    assert _standardize_event(once) == once


def test_header_without_comment_unchanged():
    assert _standardize_event(_EVENT)[0] == "country_event = {"


def test_no_blank_line_before_closing_brace():
    # (defect) every section appended a trailing blank, so the last one always
    # left a dead line above `}`.
    out = _standardize_event(_EVENT)
    assert out[-1] == "}"
    assert out[-2].strip() != ""


def test_blank_lines_separate_groups_not_terminate_them():
    out = _standardize_event(_EVENT)
    blanks = [i for i, line in enumerate(out) if line.strip() == ""]
    # Exactly two: header group -> option, and option -> option.
    assert len(blanks) == 2
    for i in blanks:
        assert out[i - 1].strip() and out[i + 1].strip()


_MINIMAL_EVENT = [
    "country_event = {",
    "\tid = test.6",
    "\tis_triggered_only = yes",
    "}",
]


def test_event_without_options_has_no_stray_blank():
    # An event with nothing after the header group must not gain a gap from the
    # absent option/trigger/immediate sections.
    assert _standardize_event(_MINIMAL_EVENT) == [
        "country_event = {",
        "\tid = test.6",
        "\tis_triggered_only = yes",
        "}",
    ]


_NEWS_EVENT = [
    "news_event = {",
    "\tid = test.7",
    "\ttitle = test.7.t",
    "\ttitle = {",
    "\t\ttrigger = { has_war = yes }",
    "\t\ttext = test.7.t.war",
    "\t}",
    "\tdesc = test.7.d",
    "\tpicture = GFX_report_event_generic",
    "\tmajor = yes",
    "\thidden = no",
    "\tfire_only_once = yes",
    "",
    "\tmean_time_to_happen = {",
    "\t\tdays = 30",
    "\t}",
    "",
    "\t# only once the war starts",
    "\ttrigger = {",
    "\t\thas_war = yes",
    "\t}",
    "",
    "\timmediate = {",
    "\t\tset_country_flag = TST_reported",
    "\t}",
    "}",
]


def test_news_event_header_conditional_title_and_blocks_are_kept():
    out = _standardize_event(_NEWS_EVENT)
    assert out == [
        "news_event = {",
        "\tid = test.7",
        "\ttitle = test.7.t",
        "\ttitle = {",
        "\t\ttrigger = { has_war = yes }",
        "\t\ttext = test.7.t.war",
        "\t}",
        "\tdesc = test.7.d",
        "\tpicture = GFX_report_event_generic",
        "\tmajor = yes",
        "\thidden = no",
        "\tfire_only_once = yes",
        "",
        "\tmean_time_to_happen = { days = 30 }",
        "",
        "\t# only once the war starts",
        "\ttrigger = { has_war = yes }",
        "",
        "\timmediate = { set_country_flag = TST_reported }",
        "}",
    ]
    assert _standardize_event(out) == out


def test_event_without_a_trigger_gate_gains_is_triggered_only():
    assert _standardize_event(
        ["country_event = {", "\ttitle = test.8.t", "\tdesc = test.8.d", "}"]
    ) == [
        "country_event = {",
        "\ttitle = test.8.t",
        "\tdesc = test.8.d",
        "\tis_triggered_only = yes",
        "}",
    ]


def test_mean_time_to_happen_suppresses_the_injected_gate():
    out = _standardize_event(
        [
            "country_event = {",
            "\tid = test.9",
            "\tmean_time_to_happen = {",
            "\t\tdays = 30",
            "\t}",
            "}",
        ]
    )
    assert "is_triggered_only" not in "\n".join(out)


def test_option_body_of_a_malformed_option_is_empty():
    assert _option_body(["\toption = yes\n"]) == []


def test_option_body_survives_a_missing_closer():
    assert _option_body(
        ["\toption = {\n", "\t\tname = test.1.a\n", "\t\t# cut off\n"]
    ) == ["\t\tname = test.1.a\n"]


def test_option_indent_falls_back_when_the_body_gives_none():
    assert _option_indent(["\toption = {\n", "\n", "\t\tname = x\n", "\t}\n"]) == "\t\t"
    assert _option_indent(["\toption = {\n", "\t}\n"]) == "\t\t\t"


def test_option_log_line_falls_back_to_a_literal_name():
    assert (
        _option_log_line(["\toption = {\n", "\t\tadd_political_power = 10\n", "\t}\n"])
        == '\t\tlog = "[GetDateText]: [This.GetName]: option executed"'
    )


def test_option_effect_scan_ignores_blanks_and_comments():
    option = [
        "\toption = {\n",
        "\n",
        "\t\t# just a note\n",
        "\t\tname = test.1.a\n",
        "\t}\n",
    ]
    assert not _option_has_effects(option)


def test_main_standardizes_the_named_file(tmp_path, monkeypatch):
    source = tmp_path / "events.txt"
    output = tmp_path / "out.txt"
    with open(source, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(_EVENT) + "\n")
    monkeypatch.setattr(
        sys, "argv", ["standardize_events.py", str(source), "-o", str(output)]
    )

    standardize_events.main()

    with open(output, "r", encoding="utf-8", newline="") as handle:
        assert "test.1.a executed" in handle.read()
