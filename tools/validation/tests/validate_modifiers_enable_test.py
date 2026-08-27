"""Tests for the redundant dynamic-modifier `enable` gate check.

Unlike an idea's `allowed`, `enable` is re-evaluated at runtime, so a trigger
that can never be false costs something on every pass. The gates that must
survive are the ones that go false while the modifier is still attached:
`05_internal_factions_modifiers.txt` has no `remove_dynamic_modifier` anywhere,
so its `has_idea` gates are the only thing switching a lost faction off.
"""

from validate_modifiers import Validator, _redundant_enable_gates


def _messages(body):
    return [message for message, _line in _redundant_enable_gates(body)]


def test_always_yes_flagged():
    body = "\n\tenable = { always = yes }\n\tstability_factor = FOO_stab\n"
    assert len(_messages(body)) == 1
    assert "always = yes" in _messages(body)[0]


def test_one_line_tag_gate_flagged():
    body = "\n\tenable = { original_tag = FOO }\n\tstability_factor = FOO_stab\n"
    assert "FOO" in _messages(body)[0]


def test_multiline_tag_gate_flagged():
    body = "\n\tenable = {\n\t\toriginal_tag = FOO\n\t}\n\tstability_factor = x\n"
    assert len(_messages(body)) == 1


def test_tag_gate_flagged_alongside_a_real_trigger():
    body = (
        "\n\tenable = {\n"
        "\t\toriginal_tag = FOO\n"
        "\t\tNOT = { has_country_flag = collapsed_nation }\n"
        "\t}\n"
    )
    assert len(_messages(body)) == 1


def test_has_idea_gate_not_flagged():
    body = "\n\tenable = { has_idea = the_military }\n\tstability_factor = x\n"
    assert _messages(body) == []


def test_country_exists_gate_not_flagged():
    body = "\n\tenable = { country_exists = ISR }\n\tlocal_building_slots = 2\n"
    assert _messages(body) == []


def test_tag_inside_or_branch_not_flagged():
    body = (
        "\n\tenable = {\n"
        "\t\tOR = {\n"
        "\t\t\toriginal_tag = SOV\n"
        "\t\t\toriginal_tag = TAJ\n"
        "\t\t}\n"
        "\t}\n"
    )
    assert _messages(body) == []


def test_no_enable_block_is_not_a_finding():
    assert _redundant_enable_gates("\n\tstability_factor = FOO_stab\n") == []


def test_enable_nested_in_remove_trigger_not_flagged():
    # The stripper only touches a direct child of the modifier; the validator
    # has to agree or it reports a finding no tool will ever fix.
    body = "\n\tremove_trigger = {\n\t\tenable = { always = yes }\n\t}\n"
    assert _messages(body) == []


def test_top_level_enable_found_after_an_earlier_nested_block():
    body = (
        "\n\tremove_trigger = {\n"
        "\t\tNOT = { has_idea = x }\n"
        "\t}\n"
        "\tenable = { original_tag = FOO }\n"
    )
    assert len(_messages(body)) == 1


def test_line_offset_points_at_the_gate():
    body = "\n\ticon = GFX_idea_x\n\tenable = {\n\t\toriginal_tag = FOO\n\t}\n"
    _message, line = _redundant_enable_gates(body)[0]
    assert body.split("\n")[line].strip() == "original_tag = FOO"


def test_validator_reports_redundant_gate_as_error(tmp_path):
    path = tmp_path / "common" / "dynamic_modifiers" / "test.txt"
    path.parent.mkdir(parents=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write("FOO_modifier = {\n\tenable = { always = yes }\n}\n")

    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator.validate_redundant_enable_gates()

    assert validator.errors_found == 1
    assert validator.warnings_found == 0
