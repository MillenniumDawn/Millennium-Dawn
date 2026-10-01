"""Regressions for requirement lines resolved through scripted triggers.

HOI4 expands a scripted-trigger call in `available` into the lines its body
renders. A custom trigger tooltip reached under an odd number of NOT blocks
renders its negative key, and a flag check renders a loc key named after the flag.
Either one missing shows the player a raw token (the BRI apply decisions
showed `gdp_per_capita_greater_than_30_tt_NOT` and `bri_pipeline_busy`).
"""

import pytest
import validate_variables as V

GDP_TRIGGER = (
    "TST_rich = {\n"
    "\tcustom_trigger_tooltip = {\n"
    "\t\ttooltip = TST_rich_tt\n"
    "\t\tcheck_variable = { gdp_per_capita > 29.999 }\n"
    "\t}\n"
    "}\n"
)


@pytest.fixture(params=["custom_trigger_tooltip", "custom_override_tooltip"])
def tooltip_wrapper(request):
    return request.param


@pytest.fixture
def gdp_trigger(tooltip_wrapper):
    return GDP_TRIGGER.replace("custom_trigger_tooltip", tooltip_wrapper)


def _run(tmp_path, write_path, triggers, decision, loc=""):
    write_path(tmp_path, "common/scripted_triggers/test.txt", triggers)
    write_path(tmp_path, "common/decisions/test.txt", decision)
    loc_file = tmp_path / "localisation" / "english" / "test_l_english.yml"
    loc_file.parent.mkdir(parents=True, exist_ok=True)
    with open(loc_file, "w", encoding="utf-8-sig", newline="") as file:
        file.write(f"l_english:\n{loc}")
    v = V.Validator(str(tmp_path), use_colors=False, workers=1)
    v.validate_unlocalised_available_flags()
    v.validate_negated_trigger_tooltips()
    return v._issues


def _decision(available):
    return f"TST_category = {{\n\tTST_decision = {{\n\t\tavailable = {{\n{available}\t\t}}\n\t}}\n}}\n"


def test_negated_call_needs_not_key(tmp_path, write_path, gdp_trigger):
    issues = _run(
        tmp_path,
        write_path,
        gdp_trigger,
        _decision("\t\t\tNOT = { TST_rich = yes }\n"),
        ' TST_rich_tt: "Rich"\n',
    )
    assert len(issues) == 1
    assert "TST_rich_tt_NOT" in issues[0].message
    assert issues[0].severity == V.Severity.ERROR
    assert issues[0].category == "unlocalised-negated-trigger-tooltip"
    assert issues[0].line == 4


def test_negated_call_with_not_key_passes(tmp_path, write_path, gdp_trigger):
    issues = _run(
        tmp_path,
        write_path,
        gdp_trigger,
        _decision("\t\t\tNOT = { TST_rich = yes }\n"),
        ' TST_rich_tt: "Rich"\n TST_rich_tt_NOT: "Not rich"\n',
    )
    assert issues == []


def test_call_with_no_is_negated(tmp_path, write_path, gdp_trigger):
    issues = _run(tmp_path, write_path, gdp_trigger, _decision("\t\t\tTST_rich = no\n"))
    assert ["TST_rich_tt_NOT" in i.message for i in issues] == [True]


def test_positive_call_needs_no_not_key(tmp_path, write_path, gdp_trigger):
    issues = _run(
        tmp_path, write_path, gdp_trigger, _decision("\t\t\tTST_rich = yes\n")
    )
    assert issues == []


def test_double_negation_through_nested_trigger(tmp_path, write_path, gdp_trigger):
    triggers = gdp_trigger + "TST_poor = {\n\tNOT = { TST_rich = yes }\n}\n"
    issues = _run(
        tmp_path, write_path, triggers, _decision("\t\t\tNOT = { TST_poor = yes }\n")
    )
    assert issues == []


def test_direct_negated_tooltip_needs_not_key(tmp_path, write_path, tooltip_wrapper):
    issues = _run(
        tmp_path,
        write_path,
        "",
        _decision(
            "\t\t\tNOT = {\n"
            f"\t\t\t\t{tooltip_wrapper} = {{ tooltip = TST_direct_tt always = yes }}\n"
            "\t\t\t}\n"
        ),
    )
    assert ["TST_direct_tt_NOT" in i.message for i in issues] == [True]


def test_wrapped_call_is_exempt(tmp_path, write_path, gdp_trigger, tooltip_wrapper):
    issues = _run(
        tmp_path,
        write_path,
        gdp_trigger,
        _decision(
            f"\t\t\t{tooltip_wrapper} = {{\n"
            "\t\t\t\ttooltip = TST_outer_tt\n"
            "\t\t\t\tNOT = { TST_rich = yes }\n"
            "\t\t\t}\n"
        ),
    )
    assert issues == []


@pytest.mark.parametrize("via_trigger", [False, True])
@pytest.mark.parametrize("localised", [False, True])
def test_explicit_negative_key(
    tmp_path, write_path, tooltip_wrapper, via_trigger, localised
):
    tooltip = (
        f"{tooltip_wrapper} = {{\n"
        "\tnot_tooltip = TST_negative_tt\n"
        "\ttooltip = TST_positive_tt\n"
        "\talways = yes\n"
        "}\n"
    )
    triggers = ""
    available = f"NOT = {{ {tooltip} }}\n"
    if via_trigger:
        triggers = (
            f"TST_inner = {{\n{tooltip}}}\n" "TST_outer = {\n\tTST_inner = no\n}\n"
        )
        available = "TST_outer = yes\n"
    loc = ' TST_positive_tt: "Positive"\n'
    if localised:
        loc += ' TST_negative_tt: "Negative"\n'
    else:
        loc += ' TST_positive_tt_NOT: "Unused"\n'
    issues = _run(tmp_path, write_path, triggers, _decision(available), loc)
    if localised:
        assert issues == []
    else:
        assert len(issues) == 1
        assert "TST_negative_tt" in issues[0].message
        assert issues[0].severity == V.Severity.ERROR
        assert issues[0].category == "unlocalised-negated-trigger-tooltip"


def test_flag_inside_scripted_trigger_needs_loc(tmp_path, write_path):
    triggers = (
        "TST_can_apply = {\n"
        "\tNOT = { has_country_flag = TST_busy }\n"
        "\thidden_trigger = { has_country_flag = TST_hidden }\n"
        "}\n"
        "TST_outer = {\n\tTST_can_apply = yes\n}\n"
    )
    issues = _run(tmp_path, write_path, triggers, _decision("\t\t\tTST_outer = yes\n"))
    assert len(issues) == 1
    assert "TST_busy" in issues[0].message
    assert "via scripted trigger TST_outer" in issues[0].message
    assert issues[0].category == "unlocalised-available-flag"


def test_recursive_triggers_terminate(tmp_path, write_path):
    triggers = "TST_a = {\n\tTST_b = yes\n}\nTST_b = {\n\tTST_a = yes\n}\n"
    assert _run(tmp_path, write_path, triggers, _decision("\t\t\tTST_a = yes\n")) == []
