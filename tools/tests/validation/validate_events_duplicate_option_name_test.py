"""Event options that share a name while running unconditionally.

Options with mutually exclusive triggers may share one label on purpose. An
option with no trigger always displays, so its twin's label shows beside it
(issue #6827).
"""

import pytest
import validate_events as V
from shared.suite import build_validator, write_tree

_TITLE = (
    "country_event = {\n\tid = foo.1\n\ttitle = foo.1.t\n\tis_triggered_only = yes\n"
)
_MESSAGE = "has no trigger but reuses a sibling option's name"


def _option(name="foo.1.a", trigger="", effects=""):
    gate = f"\t\ttrigger = {{\n{trigger}\t\t}}\n" if trigger else ""
    return f"\toption = {{\n\t\tname = {name}\n" + gate + effects + "\t}\n"


def _event(*options, event_id="foo.1"):
    return _TITLE.replace("foo.1", event_id) + "".join(options) + "}\n"


def _finding(line, name="foo.1.a"):
    return f"event foo.1: option {name} {_MESSAGE}", line


# case: (event source, (message, option line) findings)
_SCAN_CASES = {
    "two untriggered options share a name": (
        _event(_option(), _option()),
        [_finding(6), _finding(9)],
    ),
    "distinct names": (_event(_option(), _option("foo.1.b")), []),
    "one untriggered option beside a gated twin": (
        _event(_option(trigger="\t\t\thas_country_flag = foo_flag\n"), _option()),
        [_finding(12)],
    ),
    "mutually exclusive triggers may share a name": (
        _event(
            _option(trigger="\t\t\toriginal_tag = FRA\n"),
            _option(trigger="\t\t\tNOT = { original_tag = FRA }\n"),
        ),
        [],
    ),
    "quoted name values are compared": (
        _event(_option('"foo.1.a"'), _option('"foo.1.a"', effects="\t\tfoo = yes\n")),
        [_finding(6), _finding(9)],
    ),
    "identical scripted labels": (
        _event(_option('"[GetChoice]"'), _option('"[GetChoice]"')),
        [_finding(6, "[GetChoice]"), _finding(9, "[GetChoice]")],
    ),
    "same prefix but distinct scripted labels": (
        _event(_option('"choice [GetFirst]"'), _option('"choice [GetSecond]"')),
        [],
    ),
    "effect name before option name": (
        _event(
            "option = { set_province_name = { id = 1 name = town }\n"
            "name = foo.1.a }\n",
            _option(),
        ),
        [_finding(6), _finding(8)],
    ),
    # The same name in two events is not a collision.
    "same name in separate events": (
        _event(_option()) + _event(_option(), event_id="foo.2"),
        [],
    ),
}


@pytest.mark.parametrize("text, expected", _SCAN_CASES.values(), ids=_SCAN_CASES.keys())
def test_duplicate_option_name_scan(text, expected):
    assert V.find_untriggered_duplicate_option_names(text) == expected


def test_validator_reports_error_for_each_untriggered_option(tmp_path):
    write_tree(tmp_path, {"events/Ev.txt": _event(_option(), _option())})
    validator = build_validator(V.Validator, tmp_path)

    validator.validate_duplicate_option_names()

    assert [
        (issue.category, issue.severity, issue.file, issue.line, issue.message)
        for issue in validator._issues
    ] == [
        (
            "event-option-duplicate-name",
            "error",
            "events/Ev.txt",
            6,
            f"event foo.1: option foo.1.a {_MESSAGE}",
        ),
        (
            "event-option-duplicate-name",
            "error",
            "events/Ev.txt",
            9,
            f"event foo.1: option foo.1.a {_MESSAGE}",
        ),
    ]


def test_worker_skips_unreadable_and_ignored_files(tmp_path):
    write_tree(tmp_path, {"tools/edge.txt": _event(_option(), _option())})

    for relative in ("tools/edge.txt", "events/missing.txt"):
        path = str(tmp_path / relative)
        assert (
            V._extract_untriggered_duplicate_option_names(path, mod_path=str(tmp_path))
            == []
        )
