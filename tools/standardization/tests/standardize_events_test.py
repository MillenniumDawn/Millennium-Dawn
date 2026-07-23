"""Tests for the event standardizer.

Regression guard for the log-injection bug: `_option_has_effects` scanned the
option HEADER line and so always returned True, injecting a `log =` line into
effectless options (violating "log only if the option has effects"). It must scan
only the option body, and the injected log's indent must follow the body (2-tab
files get a 2-tab line, not a hardcoded 3-tab one).
"""

from standardize_events import (
    EventStandardizer,
    _option_has_effects,
    _option_log_line,
)


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
