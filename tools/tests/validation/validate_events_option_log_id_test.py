"""Event option logs that cite another option's id (issue #5266)."""

import validate_events as events
from shared.suite import write_under_str as _write
from shared_utils import validation_config
from validate_events import Validator


def _validator(tmp_path):
    return Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def _event(option_body: str, event_id: str = "foo.1") -> str:
    return (
        "country_event = {\n"
        f"\tid = {event_id}\n"
        f"\ttitle = {event_id}.t\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n" + option_body + "\t}\n"
        "}\n"
    )


def test_executed_form_citing_another_option_is_an_error(tmp_path):
    body = (
        "\t\tname = foo.1.b\n"
        '\t\tlog = "[GetDateText]: [This.GetName]: foo.1.a executed"\n'
        "\t\tadd_political_power = 10\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_id()
    assert [(i.message, i.file, i.line) for i in v._issues] == [
        ("foo.1.b log cites foo.1.a", "Ev.txt", 7)
    ]
    assert v._issues[0].category == "event-option-log-id"
    assert v.errors_found == 1
    assert v.warnings_found == 0


def test_matching_executed_form_is_not_flagged(tmp_path):
    body = (
        "\t\tname = foo.1.a\n"
        '\t\tlog = "[GetDateText]: [This.GetName]: foo.1.a executed"\n'
        "\t\tadd_political_power = 10\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_id()
    assert v._issues == []


def test_event_word_form_citing_another_option_is_flagged(tmp_path):
    body = (
        "\t\tname = foo.1.a\n"
        '\t\tlog = "[GetDateText]: Event foo.1.b"\n'
        "\t\tadd_political_power = 10\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_id()
    assert v._issues[0].message == "foo.1.a log cites foo.1.b"
    assert v.errors_found == 1


def test_wrong_option_letter_is_flagged(tmp_path):
    body = (
        "\t\tname = foo.1.a\n"
        '\t\tlog = "[GetDateText]: Event foo.1 Option b"\n'
        "\t\tadd_political_power = 10\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_id()
    assert v._issues[0].message == "foo.1.a log says Option b"
    assert v.errors_found == 1


def test_config_exempt_option_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "_OPTION_LOG_ID_EXEMPT", frozenset({"foo.1.a"}))
    body = (
        "\t\tname = foo.1.a\n"
        '\t\tlog = "[GetDateText]: [This.GetName]: foo.1.b executed"\n'
        "\t\tadd_political_power = 10\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_id()
    assert v._issues == []


def test_option_log_id_exempt_is_a_config_list():
    entries = validation_config("validate_events", "option_log_id_exempt")
    assert isinstance(entries, dict)
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in entries.items())


def test_run_validations_runs_the_check(tmp_path, monkeypatch):
    v = _validator(tmp_path)
    called = []
    monkeypatch.setattr(v, "validate_option_log_id", lambda: called.append(True))
    v.run_validations()
    assert called == [True]


def test_shared_loc_name_with_this_event_log_is_not_flagged(tmp_path):
    body = (
        "\t\tname = isisNews.1301.a\n"
        '\t\tlog = "[GetDateText]: [This.GetName]: isisNews.1302.a executed"\n'
        "\t\tadd_political_power = 10\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body, event_id="isisNews.1302"))
    v = _validator(tmp_path)
    v.validate_option_log_id()
    assert v._issues == []


def test_empty_tree_reports_nothing(tmp_path):
    v = _validator(tmp_path)
    v.validate_option_log_id()
    assert v._issues == []


def test_worker_handles_skipped_and_missing_files(tmp_path):
    assert (
        events._extract_event_log_id_mismatches(
            str(tmp_path / "tools/edge.txt"), mod_path=str(tmp_path)
        )
        == []
    )
    assert (
        events._extract_event_log_id_mismatches(
            str(tmp_path / "events/missing.txt"), mod_path=str(tmp_path)
        )
        == []
    )
