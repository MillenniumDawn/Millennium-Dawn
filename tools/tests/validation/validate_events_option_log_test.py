"""Event options carrying a log while running no effects (issue #3677)."""

from shared.suite import write_under_str as _write
from validate_events import Validator, find_option_logs_without_effects


def _validator(tmp_path):
    return Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def _event(option_body: str) -> str:
    return (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\ttitle = foo.1.t\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n" + option_body + "\t}\n"
        "}\n"
    )


_LOG = '\t\tlog = "[GetDateText]: [This.GetName]: foo.1.a executed"\n'


def test_name_and_log_only_is_flagged(tmp_path):
    _write(tmp_path, "events/Ev.txt", _event("\t\tname = foo.1.a\n" + _LOG))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert [(i.message, i.file, i.line) for i in v._issues] == [
        ("foo.1.a", "Ev.txt", 7)
    ]
    assert v._issues[0].category == "event-option-log-without-effect"
    assert v.warnings_found == 1
    assert v.errors_found == 0


def test_trigger_and_ai_chance_are_not_effects(tmp_path):
    body = (
        "\t\tname = foo.1.a\n"
        + _LOG
        + "\t\ttrigger = { has_country_flag = foo_flag }\n"
        "\t\tai_chance = {\n\t\t\tbase = 1\n\t\t}\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert len(v._issues) == 1


def test_log_before_name_still_resolves_the_option_name(tmp_path):
    _write(tmp_path, "events/Ev.txt", _event(_LOG + "\t\tname = foo.1.a\n"))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert [(i.message, i.line) for i in v._issues] == [("foo.1.a", 6)]


def test_real_effect_is_not_flagged(tmp_path):
    body = "\t\tname = foo.1.a\n" + _LOG + "\t\tset_country_flag = foo_flag\n"
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert v._issues == []


def test_hidden_effect_counts_as_an_effect(tmp_path):
    body = (
        "\t\tname = foo.1.a\n"
        + _LOG
        + "\t\thidden_effect = { set_country_flag = foo_flag }\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert v._issues == []


def test_effect_tooltip_counts_as_an_effect(tmp_path):
    body = (
        "\t\tname = foo.1.a\n"
        + _LOG
        + "\t\teffect_tooltip = { add_political_power = 10 }\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert v._issues == []


def test_log_nested_in_an_if_is_not_an_option_level_log(tmp_path):
    body = (
        "\t\tname = foo.1.a\n"
        "\t\tif = {\n"
        "\t\t\tlimit = { has_country_flag = foo_flag }\n" + "\t" + _LOG + "\t\t}\n"
    )
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert v._issues == []


def test_commented_out_log_is_ignored(tmp_path):
    body = "\t\tname = foo.1.a\n\t\t#" + _LOG.lstrip("\t")
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert v._issues == []


def test_two_logs_in_one_option_report_both_lines(tmp_path):
    _write(tmp_path, "events/Ev.txt", _event("\t\tname = foo.1.a\n" + _LOG + _LOG))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert sorted(i.line for i in v._issues) == [7, 8]


def test_braces_inside_a_log_string_do_not_break_the_scan(tmp_path):
    body = '\t\tname = foo.1.a\n\t\tlog = "closing } brace"\n'
    _write(tmp_path, "events/Ev.txt", _event(body))
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert [i.line for i in v._issues] == [7]


def test_empty_tree_reports_nothing(tmp_path):
    v = _validator(tmp_path)
    v.validate_option_log_without_effect()
    assert v._issues == []


def test_detector_returns_name_and_line_pairs():
    text = (
        "option = {\n"
        "\tname = foo.1.a\n"
        '\tlog = "foo.1.a executed"\n'
        "}\n"
        "option = {\n"
        '\tlog = "foo.1.b executed"\n'
        "\tadd_political_power = 10\n"
        "}\n"
    )
    assert find_option_logs_without_effects(text) == [("foo.1.a", 3)]


def test_detector_labels_an_unnamed_option():
    text = 'option = {\n\tlog = "orphan"\n}\n'
    assert find_option_logs_without_effects(text) == [("unnamed option", 2)]
