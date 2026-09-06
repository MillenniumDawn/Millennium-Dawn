"""Behavior tests for the on_actions event-reference validator.

Covers the events-tree scan, the on_actions block parser, and the validator's
dated polls, references, lifecycle wiring, triggered-only, and duplicate checks.
"""

import runpy
import sys

import pytest
import validate_on_actions
from shared.suite import write_under as _write
from validate_on_actions import (
    Validator,
    _event_calls_effect,
    _extract_random_events_ids,
    _parse_on_actions_file,
    _parse_on_actions_text,
    _scan_date_polls_file,
    _scan_event_file,
    _scan_event_text,
)

EVENTS = """add_namespace = test

country_event = {
\tid = test.1
\tis_triggered_only = yes
}

country_event = {
\tid = test.mtth
\tmean_time_to_happen = { days = 10 }
}
"""

ON_ACTIONS = """on_actions = {
\ton_startup = {
\t\teffect = {
\t\t\tcountry_event = test.1
\t\t\tcountry_event = test.1
\t\t\tcountry_event = test.MTTH
\t\t\tcountry_event = test.missing
\t\t\tcountry_event = test.mtth
\t\t}
\t}
}
"""

ON_ACTIONS_FILE = "common/on_actions/MD_test.txt"


def _issues(validator, category):
    return [
        (issue.message, issue.file, issue.line)
        for issue in validator._issues
        if issue.category == category
    ]


def test_event_effect_call_is_scoped_to_the_matching_event():
    text = """country_event = {
\tid = faction_goal_cache.1
\tfaction_goal_update_daily_caches = yes
}
country_event = {
\tid = faction_goal_cache.2
}
"""

    assert not _event_calls_effect(
        text, "faction_goal_cache.2", "faction_goal_update_daily_caches"
    )


def test_event_scan_collects_ids_and_triggered_only_flags():
    text = """add_namespace = test

country_event = {
\tid = test.1
\tis_triggered_only = yes
}

news_event = {
\tid = test.2
}

country_event = {
\ttitle = test.no_id
}
"""

    assert _scan_event_text(text) == ({"test.1", "test.2"}, {"test.1"})


def test_event_scan_of_a_missing_file_is_empty(tmp_path):
    assert _scan_event_file((str(tmp_path / "gone.txt"), str(tmp_path))) == (
        set(),
        set(),
    )


def test_event_scan_reads_and_caches_a_real_file(tmp_path):
    path = _write(
        tmp_path,
        "events/MD_test.txt",
        EVENTS + "# country_event = { id = commented.1 }\n",
    )

    first = _scan_event_file((str(path), str(tmp_path)))
    second = _scan_event_file((str(path), str(tmp_path)))

    assert first == ({"test.1", "test.mtth"}, {"test.1"})
    assert second == first


def test_random_events_pool_ids_are_extracted():
    text = """on_actions = {
\ton_startup = {
\t\trandom_events = {
\t\t\t50 = econvent.1
\t\t\t50 = econvent.2
\t\t}
\t}
}
"""

    assert _extract_random_events_ids(text) == {"econvent.1", "econvent.2"}


def test_repeated_random_events_entry_is_a_duplicate():
    text = """on_actions = {
\ton_startup = {
\t\trandom_events = {
\t\t\t50 = econvent.1
\t\t\t50 = econvent.1
\t\t}
\t}
}
"""

    refs, dupes = _parse_on_actions_text(text, "f.txt")

    assert refs == [("econvent.1", "on_startup", 4, "f.txt")]
    assert dupes == [("econvent.1", "on_startup", 5, "f.txt")]


def test_same_event_in_exclusive_branches_is_not_a_duplicate():
    text = """on_actions = {
\ton_startup = {
\t\tif = {
\t\t\tlimit = { has_country_flag = a }
\t\t\tcountry_event = test.1
\t\t}
\t\telse = {
\t\t\tcountry_event = test.1
\t\t}
\t}
}
"""

    refs, dupes = _parse_on_actions_text(text, "f.txt")

    assert [(eid, line) for eid, _block, line, _f in refs] == [
        ("test.1", 5),
        ("test.1", 8),
    ]
    assert dupes == []


def test_long_form_call_is_not_counted_twice():
    text = """on_actions = {
\ton_startup = {
\t\tcountry_event = { id = test.1 days = 5 }
\t}
}
"""

    refs, dupes = _parse_on_actions_text(text, "f.txt")

    assert refs == [("test.1", "on_startup", 3, "f.txt")]
    assert dupes == []


def test_sub_block_keyword_is_not_read_as_an_on_action_name():
    text = """on_actions = {
\teffect = {
\t\tcountry_event = test.1
\t}
\ton_startup = {
\t\tcountry_event = test.1
\t}
}
"""

    refs, dupes = _parse_on_actions_text(text, "f.txt")

    assert refs == [("test.1", "on_startup", 6, "f.txt")]
    assert dupes == []


def test_on_action_closing_at_end_of_file_still_parses():
    text = "on_actions = {\n\ton_startup = {\n\t\tcountry_event = test.1\n\t}}"

    assert _parse_on_actions_text(text, "f.txt") == (
        [("test.1", "on_startup", 3, "f.txt")],
        [],
    )


def test_unbalanced_on_action_block_yields_nothing():
    text = "on_actions = {\n\ton_daily = {\n\t\tcountry_event = test.1\n"

    assert _parse_on_actions_text(text, "f.txt") == ([], [])


def test_parsing_a_missing_on_actions_file_is_empty(tmp_path):
    assert _parse_on_actions_file((str(tmp_path / "gone.txt"), str(tmp_path))) == (
        [],
        [],
    )
    assert _scan_date_polls_file((str(tmp_path / "gone.txt"), str(tmp_path))) == []


def test_comments_are_stripped_before_parsing(tmp_path):
    path = _write(
        tmp_path,
        ON_ACTIONS_FILE,
        "on_actions = {\n\ton_startup = {\n"
        "\t\t# country_event = commented.1\n"
        "\t\tcountry_event = test.1\n\t}\n}\n",
    )

    refs, dupes = _parse_on_actions_file((str(path), str(tmp_path)))

    assert refs == [("test.1", "on_startup", 4, str(path))]
    assert dupes == []


def _mod_with_refs(tmp_path):
    _write(tmp_path, "events/MD_test.txt", EVENTS)
    _write(tmp_path, ON_ACTIONS_FILE, ON_ACTIONS)
    return Validator(str(tmp_path), use_colors=False, workers=1)


def test_full_run_reports_each_reference_problem_once(tmp_path):
    validator = _mod_with_refs(tmp_path)

    validator.run_validations()

    assert _issues(validator, "missing-event-ref") == [
        (
            "Undefined event 'test.MTTH' referenced in on_action 'on_startup': "
            "case-mismatch reference 'test.MTTH' — defined as 'test.mtth'"
            " (works on Windows, fails on Linux)",
            ON_ACTIONS_FILE,
            6,
        ),
        (
            "Undefined event 'test.missing' referenced in on_action 'on_startup'",
            ON_ACTIONS_FILE,
            7,
        ),
    ]
    assert _issues(validator, "non-triggered-on-action") == [
        (
            "Event 'test.mtth' in on_action 'on_startup' lacks is_triggered_only = yes"
            " (may also fire on its own MTTH)",
            ON_ACTIONS_FILE,
            8,
        )
    ]
    assert _issues(validator, "duplicate-event-ref") == [
        (
            "Duplicate event reference 'test.1' in on_action 'on_startup'",
            ON_ACTIONS_FILE,
            5,
        )
    ]
    assert (validator.errors_found, validator.warnings_found) == (2, 2)


def test_defined_event_ids_are_cached_after_the_first_scan(tmp_path):
    validator = _mod_with_refs(tmp_path)

    first = validator._get_defined_event_ids()
    second = validator._get_defined_event_ids()

    assert first == ({"test.1", "test.mtth"}, {"test.1"})
    assert second[0] is first[0]
    assert second[1] is first[1]


def test_clean_on_actions_file_reports_nothing(tmp_path):
    _write(tmp_path, "events/MD_test.txt", EVENTS)
    _write(
        tmp_path,
        ON_ACTIONS_FILE,
        "on_actions = {\n\ton_startup = {\n\t\tcountry_event = test.1\n\t}\n}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []
    assert (validator.errors_found, validator.warnings_found) == (0, 0)


def _faction_cache_validator(tmp_path, on_create_body, event_effect=True):
    effect = "\tfaction_goal_update_daily_caches = yes\n" if event_effect else ""
    _write(
        tmp_path,
        "events/MD_faction_goal_cache_events.txt",
        "add_namespace = faction_goal_cache\n"
        "country_event = {\n"
        "\tid = faction_goal_cache.2\n"
        "\tis_triggered_only = yes\n"
        f"{effect}"
        "}\n",
    )
    _write(
        tmp_path,
        ON_ACTIONS_FILE,
        "on_actions = {\n"
        "\ton_create_faction = {\n"
        f"{on_create_body}"
        "\t}\n"
        "}\n",
    )
    return Validator(str(tmp_path), use_colors=False, workers=1)


def test_missing_faction_cache_creation_wiring_is_reported(tmp_path):
    validator = _faction_cache_validator(tmp_path, "\t\teffect = { }\n")

    validator.validate_faction_goal_cache_creation()

    issues = _issues(validator, "missing-faction-goal-cache-lifecycle")
    assert len(issues) == 1
    assert "on_create_faction must schedule faction_goal_cache.2" in issues[0][0]


def test_faction_cache_creation_event_is_accepted(tmp_path):
    validator = _faction_cache_validator(
        tmp_path,
        "\t\teffect = {\n"
        "\t\t\tcountry_event = { id = faction_goal_cache.2 hours = 1 }\n"
        "\t\t}\n",
    )

    validator.validate_faction_goal_cache_creation()

    assert _issues(validator, "missing-faction-goal-cache-lifecycle") == []


def test_faction_cache_creation_event_must_update_the_cache(tmp_path):
    validator = _faction_cache_validator(
        tmp_path,
        "\t\teffect = {\n"
        "\t\t\tcountry_event = { id = faction_goal_cache.2 hours = 1 }\n"
        "\t\t}\n",
        event_effect=False,
    )

    validator.validate_faction_goal_cache_creation()

    issues = _issues(validator, "missing-faction-goal-cache-lifecycle")
    assert len(issues) == 1
    assert "must call faction_goal_update_daily_caches" in issues[0][0]


def test_faction_cache_event_body_scan_reads_unstaged_events(tmp_path):
    validator = _faction_cache_validator(
        tmp_path,
        "\t\teffect = {\n"
        "\t\t\tcountry_event = { id = faction_goal_cache.2 hours = 1 }\n"
        "\t\t}\n",
    )
    validator.staged_only = True
    validator.staged_files = [str(tmp_path / ON_ACTIONS_FILE)]

    validator.validate_faction_goal_cache_creation()

    assert _issues(validator, "missing-faction-goal-cache-lifecycle") == []


def test_dated_pulse_poll_is_reported_with_its_source_line(tmp_path):
    _write(
        tmp_path,
        "common/on_actions/pulse.txt",
        "on_actions = {\n"
        "\ton_monthly_TAG = {\n"
        "\t\teffect = {\n"
        "\t\t\tif = {\n"
        "\t\t\t\tlimit = { date > 2005.1.1 }\n"
        "\t\t\t\tcountry_event = historical.1\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.validate_deterministic_date_polls()

    assert _issues(validator, "deterministic-date-poll") == [
        (
            "Event 'historical.1' is polled by dated on_action 'on_monthly_TAG'; "
            "schedule it from 00_yearly_effects.txt",
            "common/on_actions/pulse.txt",
            6,
        )
    ]


def test_script_entry_point_exits_nonzero_under_strict(tmp_path, monkeypatch):
    _mod_with_refs(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            validate_on_actions.__file__,
            "--path",
            str(tmp_path),
            "--strict",
            "--workers",
            "1",
            "--no-color",
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(validate_on_actions.__file__, run_name="__main__")

    assert exit_info.value.code == 1
