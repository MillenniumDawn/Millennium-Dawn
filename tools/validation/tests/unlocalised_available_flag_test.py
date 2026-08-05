"""Regressions for the unlocalised-available-flag check in validate_variables.

HOI4 renders the requirement line for a `has_country_flag` check inside a
player-facing `available` block from a localisation key named after the flag
itself. With no such key the player reads the raw flag token instead of a
human-readable requirement.

`visible` is deliberately not covered, for the same reason as the
untooltipped-`check_variable` check: a failing visible hides the object
outright, so no requirement line renders either way.
"""

import validate_variables as V


def _findings(tmp_path, text):
    f = tmp_path / "src.txt"
    f.write_text(text, encoding="utf-8")
    return V.process_file_for_available_flags((str(f), str(tmp_path)))


def test_shorthand_flag_in_available_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n\tavailable = {\n\t\thas_country_flag = ENG_deal_flag\n\t}\n}\n",
    )
    assert len(out) == 1
    assert out[0][0] == "ENG_deal_flag"
    assert out[0][2] == 3


def test_long_form_flag_in_available_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thas_country_flag = { flag = ENG_deal_flag value > 0 }\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1
    assert out[0][0] == "ENG_deal_flag"


def test_nested_in_boolean_still_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tNOT = { OR = { has_country_flag = a has_country_flag = b } }\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 2


def test_custom_trigger_tooltip_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_trigger_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\thas_country_flag = a\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_hidden_trigger_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thidden_trigger = { has_country_flag = a }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_custom_override_tooltip_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_override_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\thas_country_flag = a\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_visible_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n\tvisible = {\n\t\thas_country_flag = a\n\t}\n}\n",
    )
    assert out == []


def test_complete_effect_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tcomplete_effect = {\n"
        "\t\tif = { limit = { has_country_flag = a } add_political_power = 10 }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_ai_will_do_modifier_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tai_will_do = {\n"
        "\t\tbase = 10\n"
        "\t\tmodifier = { factor = 0 has_country_flag = a }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_dynamic_flag_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thas_country_flag = trade_agreement@PREV\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_commented_line_ignored(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n\tavailable = {\n\t\t# has_country_flag = a\n\t}\n}\n",
    )
    assert out == []


def test_single_line_available_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n\tavailable = { has_country_flag = a }\n}\n",
    )
    assert len(out) == 1


def test_two_distinct_flags_both_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thas_country_flag = a\n"
        "\t\thas_country_flag = b\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 2
    names = {o[0] for o in out}
    assert names == {"a", "b"}


def test_only_unlocalised_flags_reported(tmp_path):
    loc = tmp_path / "localisation" / "english"
    loc.mkdir(parents=True)
    (loc / "test_l_english.yml").write_text(
        'l_english:\n ENG_known_flag:0 "Known"\n',
        encoding="utf-8-sig",
    )
    dec = tmp_path / "common" / "decisions"
    dec.mkdir(parents=True)
    (dec / "test.txt").write_text(
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thas_country_flag = ENG_known_flag\n"
        "\t\thas_country_flag = ENG_unknown_flag\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )

    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_unlocalised_available_flags()

    assert len(v._issues) == 1
    issue = v._issues[0]
    assert "ENG_unknown_flag" in issue.message
    assert "ENG_known_flag" not in issue.message
    assert issue.severity == V.Severity.WARNING
    assert issue.category == "unlocalised-available-flag"
