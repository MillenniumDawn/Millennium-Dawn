"""Event option log checks.

An option that only logs runs no effects (issue #3677). A log that cites another
option's id points the reader at the wrong option (issue #5266).
"""

import pytest
import validate_events as V
from shared.suite import build_validator, write_tree
from shared_utils import validation_config

_NAME = "\t\tname = foo.1.a\n"
_LOG = '\t\tlog = "[GetDateText]: [This.GetName]: foo.1.a executed"\n'
_EFFECT = "\t\tadd_political_power = 10\n"
_CATEGORIES = {
    "validate_option_log_without_effect": "event-option-log-without-effect",
    "validate_option_log_id": "event-option-log-id",
}


def _event(option_body, event_id="foo.1"):
    """One event whose option body starts on line 6."""
    return (
        f"country_event = {{\n\tid = {event_id}\n\ttitle = {event_id}.t\n"
        "\tis_triggered_only = yes\n\toption = {\n" + option_body + "\t}\n}\n"
    )


def _log(text):
    return f'\t\tlog = "[GetDateText]: {text}"\n'


# check: {case: (event, (message, line) per finding)}
_OPTION_LOG_CASES = {
    "validate_option_log_without_effect": {
        "name and log only": (_event(_NAME + _LOG), [("foo.1.a", 7)]),
        "trigger and ai_chance are not effects": (
            _event(
                _NAME
                + _LOG
                + "\t\ttrigger = { has_country_flag = foo_flag }\n"
                + "\t\tai_chance = {\n\t\t\tbase = 1\n\t\t}\n"
            ),
            [("foo.1.a", 7)],
        ),
        "unnamed option": (_event(_LOG), [("unnamed option", 6)]),
        "brace inside the log string": (
            _event(_NAME + '\t\tlog = "closing } brace"\n'),
            [("foo.1.a", 7)],
        ),
        "real effect": (_event(_NAME + _LOG + _EFFECT), []),
        "numeric state scope": (
            _event(_NAME + _LOG + "\t\t652 = { MSC_elect_sobyanin_edro = yes }\n"),
            [],
        ),
        "quoted tag scope": (
            _event(_NAME + _LOG + '\t\t"LGN" = { change_tag_from = CAR }\n'),
            [],
        ),
        # Only a log at the option's own depth counts.
        "log nested in an if": (
            _event(
                _NAME
                + "\t\tif = {\n\t\t\tlimit = { has_country_flag = foo_flag }\n\t"
                + _LOG
                + "\t\t}\n"
            ),
            [],
        ),
        "commented-out log": (_event(_NAME + "\t\t#" + _LOG.lstrip("\t")), []),
    },
    "validate_option_log_id": {
        "another option's id": (
            _event("\t\tname = foo.1.b\n" + _LOG + _EFFECT),
            [("foo.1.b log cites foo.1.a", 7)],
        ),
        "its own id": (_event(_NAME + _LOG + _EFFECT), []),
        "dotted endings that are not event ids": (
            _event(
                _NAME
                + _log("[This.GetName]: 2025.5")
                + _log("[This.GetName]: ROOT.capital")
                + _log("[This.GetName]: v1.2")
                + _EFFECT
            ),
            [],
        ),
        "id with a numeric namespace suffix": (
            _event(_NAME + _log("[This.GetName]: CZE_Army_2000.01") + _EFFECT),
            [("foo.1.a log cites CZE_Army_2000.01", 7)],
        ),
        "Event word form": (
            _event(_NAME + _log("Event foo.1.b") + _EFFECT),
            [("foo.1.a log cites foo.1.b", 7)],
        ),
        "wrong option letter": (
            _event(_NAME + _log("Event foo.1 Option b") + _EFFECT),
            [("foo.1.a log says Option b", 7)],
        ),
        "config exemption": (
            _event(
                "\t\tname = exempt.1.a\n"
                + _log("[This.GetName]: exempt.1.b executed")
                + _EFFECT,
                "exempt.1",
            ),
            [],
        ),
    },
}


@pytest.mark.parametrize(
    ("check", "event", "expected"),
    [
        pytest.param(check, *case, id=f"{check}: {name}")
        for check, cases in _OPTION_LOG_CASES.items()
        for name, case in cases.items()
    ],
)
def test_option_log_check(tmp_path, monkeypatch, check, event, expected):
    monkeypatch.setattr(V, "_OPTION_LOG_ID_EXEMPT", frozenset({"exempt.1.a"}))
    write_tree(tmp_path, {"events/Ev.txt": event})
    validator = build_validator(V.Validator, tmp_path)

    getattr(validator, check)()

    assert sorted(
        (i.message, i.line, i.file, i.category, i.severity) for i in validator._issues
    ) == [
        (message, line, "Ev.txt", _CATEGORIES[check], V.Severity.ERROR)
        for message, line in expected
    ]


def test_log_id_worker_skips_unreadable_and_ignored_files(tmp_path):
    mismatch = _event("\t\tname = foo.1.b\n" + _LOG + _EFFECT)
    write_tree(tmp_path, {"tools/edge.txt": mismatch})

    for relative in ("tools/edge.txt", "events/missing.txt"):
        path = str(tmp_path / relative)
        assert V._extract_event_log_id_mismatches(path, mod_path=str(tmp_path)) == []


def test_option_log_id_exemptions_map_an_option_to_a_reason():
    entries = validation_config("validate_events", "option_log_id_exempt")

    assert isinstance(entries, dict)
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in entries.items())
