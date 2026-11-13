"""Events fired inside an every_*/for_each_* iterator.

A fire_only_once event reaches only the first recipient of a loop, so the call
site is flagged unless a ROOT or tag scope pins the recipient. A major event
already broadcasts to every country, so a loop repeats the broadcast and a
pinned scope does not help. `random_country` and `random_state` pick once and
are not iterators.
"""

import os

import pytest
import validate_events as V
from shared.suite import (
    build_validator,
    call_site_scan,
    event_block,
    write_tree,
    write_under_str,
)

_CALLER = "common/f.txt"
_TRACKED = frozenset({"foo.1"})
_CHECKS = {
    "fof": (
        "validate_fire_only_once_in_loop",
        "fire_only_once = yes",
        V._FOF_IN_LOOP_MSG,
    ),
    "major": ("validate_major_event_in_loop", "major = yes", V._MAJOR_IN_LOOP_MSG),
}


def _nest(*scopes):
    """The last item, inside the scopes before it, inside `x = { }`."""
    *blocks, body = ("x", *scopes)
    lines = ["\t" * depth + name + " = {" for depth, name in enumerate(blocks)]
    lines += ["\t" * len(blocks) + line for line in body.split("\n")]
    lines += ["\t" * depth + "}" for depth in reversed(range(len(blocks)))]
    return "\n".join(lines) + "\n"


def _event(event_id, *fields):
    return event_block(event_id, *fields, f"option = {{ name = {event_id}.a }}")


def _findings(section, *lines, event_id="foo.1", caller=_CALLER):
    message = _CHECKS[section][2].format(eid=event_id)
    return [f"{os.path.normpath(caller)}:{line} - {message}" for line in lines]


_FIRE = "country_event = foo.1"

# case: (caller, line the fire_only_once check reports, line the major check reports)
_LOOP_CASES = {
    "every_country": (_nest("every_country", _FIRE), 3, 3),
    "for_each_scope_loop": (
        _nest(
            "for_each_scope_loop",
            "array = global.bloc\ncountry_event = { id = foo.1 days = 1 }",
        ),
        4,
        4,
    ),
    "id after another argument": (
        _nest("every_country", "country_event = { days = 20 id = foo.1 }"),
        3,
        3,
    ),
    # The keyword set once had `operative_event`, which is not a keyword.
    "operative_leader_event": (
        _nest("every_country", "operative_leader_event = foo.1"),
        3,
        3,
    ),
    # A `}` inside a quoted string must not close the iterator early.
    "brace in a quoted log": (
        _nest("every_country", 'log = "unbalanced brace } inside a string"\n' + _FIRE),
        4,
        4,
    ),
    "random_country alone": (_nest("random_country", _FIRE), None, None),
    "random_country inside a loop": (
        _nest("every_country", "random_country", _FIRE),
        4,
        4,
    ),
    "ROOT scope inside the loop": (_nest("every_country", "ROOT", _FIRE), None, 4),
    "tag scope inside the loop": (
        _nest("every_country", "SAU", "country_event = { id = foo.1 days = 2 }"),
        None,
        4,
    ),
    # A pinned scope outside the loop does not fix the recipient.
    "loop inside a ROOT scope": (_nest("ROOT", "every_country", _FIRE), 4, 4),
    "loop without an event call": (
        _nest("every_country", "add_political_power = 5"),
        None,
        None,
    ),
}


@pytest.mark.parametrize(
    ("caller", "fof_line", "major_line"), _LOOP_CASES.values(), ids=_LOOP_CASES
)
def test_tracked_event_fired_in_a_loop(tmp_path, caller, fof_line, major_line):
    path = write_under_str(tmp_path, _CALLER, caller)

    for section, line in (("fof", fof_line), ("major", major_line)):
        expected = _findings(section, line) if line else []
        assert call_site_scan(path, section, tmp_path, _TRACKED) == expected


@pytest.mark.parametrize("section", _CHECKS)
def test_untracked_event_fired_in_a_loop_is_not_reported(tmp_path, section):
    path = write_under_str(tmp_path, _CALLER, _nest("every_country", _FIRE))

    assert call_site_scan(path, section, tmp_path) == []


# case: (event fields, metadata the parser must read)
_METADATA_CASES = {
    "fire_only_once": (["fire_only_once = yes"], {"fire_only_once": True}),
    "commented hidden and triggered only": (
        ["#is_triggered_only = yes", "#hidden = yes"],
        {"is_triggered_only": False, "is_hidden": False},
    ),
    "major": (["major = yes"], {"is_major": True}),
    "commented major": (["#major = yes"], {"is_major": False}),
    "is_major trigger in an option": (
        ["option = {\n\t\tname = foo.1.b\n\t\ttrigger = { is_major = yes }\n\t}"],
        {"is_major": False},
    ),
}


@pytest.mark.parametrize(
    ("fields", "expected"), _METADATA_CASES.values(), ids=_METADATA_CASES
)
def test_event_metadata_ignores_comments_and_nested_triggers(fields, expected):
    metadata, _ = V._parse_event_metadata(_event("foo.1", *fields), "Ev.txt")

    assert len(metadata) == 1
    assert {key: metadata[0][key] for key in expected} == expected


def _staged_caller_mod(tmp_path, field):
    """A tracked event in an unstaged file, fired from a loop in a staged one."""
    write_tree(
        tmp_path,
        {
            "events/def.txt": "add_namespace = foo\n" + _event("foo.1", field),
            "common/caller.txt": _nest("every_country", _FIRE),
        },
    )
    validator = build_validator(V.Validator, tmp_path)
    validator.staged_only = True
    validator.staged_files = [str(tmp_path / "common" / "caller.txt")]
    return validator


@pytest.mark.parametrize(("check", "field", "_message"), _CHECKS.values(), ids=_CHECKS)
def test_staged_caller_is_checked_against_unstaged_definitions(
    tmp_path, check, field, _message
):
    validator = _staged_caller_mod(tmp_path, field)

    getattr(validator, check)()

    assert [(issue.severity, issue.line) for issue in validator._issues] == [
        (V.Severity.ERROR, 3)
    ]


@pytest.mark.parametrize(("check", "_field", "_message"), _CHECKS.values(), ids=_CHECKS)
def test_check_does_not_scan_when_no_event_is_tracked(
    tmp_path, monkeypatch, check, _field, _message
):
    validator = _staged_caller_mod(tmp_path, "hidden = yes")
    validator.staged_only = False
    validator._get_fire_only_once_ids()
    validator._get_major_event_ids()
    monkeypatch.setattr(
        validator, "_pool_map", lambda *a, **k: pytest.fail("scanned for no events")
    )

    getattr(validator, check)()

    assert validator._issues == []


# One walk serves both checks. Lines 6-8 hold a brace, a call in a comment and a
# call in a string; none may move or add a finding.
_NESTED_LOOPS = (
    "fx = {\n"
    "\tevery_country = {\n"
    "\t\tevery_owned_state = {\n"
    "\t\t\tfor_each_scope_loop = {\n"
    "\t\t\t\tarray = global.list\n"
    '\t\t\t\tlog = "brace } inside a string"\n'
    "\t\t\t\t# country_event = fof.1\n"
    '\t\t\t\tlog = "country_event = fof.1"\n'
    "\t\t\t\tnews_event = { id = maj.1 days = 1 }\n"
    "\t\t\t\tcountry_event = fof.1\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\t\tROOT = {\n"
    "\t\t\tcountry_event = fof.1\n"
    "\t\t\tnews_event = maj.1\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
    "country_event = fof.1"
)
_EFFECTS = "common/scripted_effects/f.txt"


def _shared_scan(tmp_path, caller):
    write_tree(
        tmp_path,
        {
            "events/Ev.txt": _event("fof.1", "fire_only_once = yes")
            + _event("maj.1", "major = yes"),
            _EFFECTS: caller,
        },
    )
    return build_validator(V.Validator, tmp_path)._get_shared_call_site_scan()


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_three_deep_iterators_report_both_checks_from_one_walk(tmp_path, newline):
    shared = _shared_scan(tmp_path, _NESTED_LOOPS.replace("\n", newline))
    path = tmp_path / _EFFECTS
    fof = _findings("fof", 10, event_id="fof.1", caller=_EFFECTS)
    major = _findings("major", 9, 15, event_id="maj.1", caller=_EFFECTS)

    assert shared["fof"] == fof
    assert shared["major"] == major
    assert call_site_scan(path, "fof", tmp_path, frozenset({"fof.1"})) == fof
    assert call_site_scan(path, "major", tmp_path, frozenset({"maj.1"})) == major


def test_for_each_only_caller_reaches_the_in_loop_walk(tmp_path):
    caller = "gx = {\n\tfor_each_scope_loop = {\n\t\tarray = global.list\n\t\tstate_event = maj.1\n\t}\n}\n"

    shared = _shared_scan(tmp_path, caller)

    assert shared["major"] == _findings("major", 4, event_id="maj.1", caller=_EFFECTS)
    assert shared["fof"] == []
