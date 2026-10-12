"""Tests for validate_ai_weight_order (issue #5738).

AI weight modifiers run in order on a running total, so a positive `add` after
a `factor = 0` modifier brings the zeroed weight back.
"""

import pytest
import validate_ai_weight_order as V

ZERO = "\tmodifier = { factor = 0 has_war = yes }\n"
ADD = "\tmodifier = { add = 5 has_stability > 0.5 }\n"


def _block(*modifiers, name="ai_chance"):
    return name + " = {\n\tbase = 10\n" + "".join(modifiers) + "}\n"


def _lines(script):
    return [line for line, _ in V.scan_text(script)]


def test_add_after_zero_reports_the_add_line():
    assert _lines(_block(ZERO, ADD)) == [4]


@pytest.mark.parametrize("name", ["ai_chance", "ai_will_do"])
def test_message_names_the_block(name):
    [(_, message)] = V.scan_text(_block(ZERO, ADD, name=name))
    assert message.startswith(f"{name} adds after a factor = 0 modifier")


def test_zero_after_the_adds_is_clean():
    assert _lines(_block(ADD, ZERO)) == []


@pytest.mark.parametrize(
    "later",
    [
        "\tmodifier = { add = -5 has_war = yes }\n",
        "\tmodifier = { add = 0 has_war = yes }\n",
        "\tmodifier = { add = bonus_weight has_war = yes }\n",
        "\tmodifier = { factor = 2 has_war = yes }\n",
    ],
)
def test_only_a_positive_literal_add_counts(later):
    assert _lines(_block(ZERO, later)) == []


@pytest.mark.parametrize("factor", ["0.5", "0.05", "10"])
def test_only_an_exact_zero_factor_counts(factor):
    scaled = "\tmodifier = { factor = " + factor + " has_war = yes }\n"
    assert _lines(_block(scaled, ADD)) == []


def test_decimal_zero_factor_counts():
    assert _lines(_block("\tmodifier = { factor = 0.0 has_war = yes }\n", ADD)) == [4]


def test_root_level_factor_is_not_a_modifier():
    assert _lines("ai_will_do = {\n\tfactor = 0\n" + ADD + "}\n") == []


def test_add_inside_a_nested_block_is_not_the_modifiers_own():
    nested = "\tmodifier = {\n\t\tfactor = 2\n\t\tsome_math = { add = 5 }\n\t}\n"
    assert _lines(_block(ZERO, nested)) == []


def test_a_non_modifier_child_block_is_not_read():
    stray = "\tsome_block = { factor = 0 }\n"
    assert _lines(_block(stray, ADD)) == []


def test_zero_and_add_in_one_modifier_is_clean():
    assert _lines(_block("\tmodifier = { factor = 0 add = 5 }\n")) == []


def test_commented_out_add_is_ignored():
    assert _lines(_block(ZERO, "\t# modifier = { add = 5 }\n")) == []


def test_each_block_is_reported_once_at_its_first_add():
    script = _block(ZERO, ADD, ADD) + _block(ADD, ZERO) + _block(ZERO, ADD)
    assert _lines(script) == [4, 15]


def test_unclosed_block_is_skipped():
    assert _lines("ai_chance = {\n\tbase = 10\n" + ZERO + ADD) == []


def test_scan_file_skips_files_without_a_factor(tmp_path):
    path = tmp_path / "quiet.txt"
    path.write_text("ai_chance = { base = 1 }\n", encoding="utf-8")
    assert V.scan_file((str(path), str(tmp_path))) == []


def test_validator_warns_with_file_and_line(tmp_path, write_path):
    write_path(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n\tid = foo.1\n\toption = {\n\t\tname = foo.1.a\n"
        "\t\tai_chance = {\n\t\t\tbase = 10\n\t\t" + ZERO + "\t\t" + ADD + "\t\t}\n"
        "\t}\n}\n",
    )
    write_path(tmp_path, "common/decisions/Clean.txt", _block(ADD, ZERO))
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)
    validator.run_validations()

    assert [
        (issue.severity, issue.category, issue.file, issue.line)
        for issue in validator._issues
    ] == [("warning", "ai-weight-zero-then-add", "events/Ev.txt", 8)]
    assert validator.warnings_found == 1
    assert validator.errors_found == 0
