"""Source-evaluated affordability and loss weights in Canadian event choices."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statements, strip_comments


@pytest.fixture(scope="module")
def canadian_options():
    source = strip_comments(read_text(REPO_ROOT / "events/Canada.txt"))
    options = {}
    for key, _, event in iter_statements(source):
        if key != "country_event" or event is None:
            continue
        event_id = next(
            value for name, value, _ in iter_statements(event) if name == "id"
        )
        options[event_id] = {}
        for key, _, option in iter_statements(event):
            if key != "option" or option is None:
                continue
            option_name = next(
                value for name, value, _ in iter_statements(option) if name == "name"
            )
            options[event_id][option_name] = option
    return options


def _option(canadian_options, event_id, name):
    return canadian_options[event_id][name]


def _weight(
    option,
    *,
    bankruptcy=False,
    deficit=False,
    stability=0.6,
    war_support=0.6,
    historical=False,
):
    chance = next(
        (body for key, _, body in iter_statements(option) if key == "ai_chance"),
        None,
    )
    if chance is None:
        return 1
    chance = script_block(option, "ai_chance")
    for source, replacement in (
        (
            "has_active_mission = bankruptcy_incoming_collapse",
            "check_variable = { bankruptcy_risk = 1 }",
        ),
        ("ai_has_high_deficit = yes", "check_variable = { high_deficit = 1 }"),
        ("has_stability < 0.3", "check_variable = { stability < 0.3 }"),
        ("has_war_support < 0.2", "check_variable = { war_support < 0.2 }"),
    ):
        chance = chance.replace(source, replacement)
    return EconomicScriptFixture(
        {
            "bankruptcy_risk": float(bankruptcy),
            "high_deficit": float(deficit),
            "stability": stability,
            "war_support": war_support,
        },
        predicates={"is_historical_focus_on": historical},
    ).weight(chance)


_TREASURY_OPTIONS = (
    ("canada.502", "canada.502.a"),
    ("canada.504", "canada.504.a"),
    ("canada.700", "canada.700.b"),
    ("canada.701", "canada.701.b"),
    ("canada_md_politics.2", "canada_md_politics.2.b"),
    ("canada_md_politics.4", "canada_md_politics.4.a"),
    ("canada_md_politics.10", "canada_md_politics.10.a"),
    ("canada_md_politics.14", "canada_md_politics.14.b"),
    ("canada_md_politics.20", "canada_md_politics.20.b"),
    ("canada_md_politics.25", "canada_md_politics.25.a"),
    ("canada.320", "canada.320.b"),
    ("canada.321", "canada.321.b"),
    ("canada.323", "canada.323.a"),
    ("canada.330", "canada.330.b"),
    ("canada.331", "canada.331.a"),
    ("canada.334", "canada.334.a"),
    ("keystonepipeline_can.1", "keystonepipeline_can.1.a"),
    ("keystonepipeline_can.2", "keystonepipeline_can.1.a"),
    ("keystonepipeline_can.3", "keystonepipeline_can.1.a"),
    ("keystonepipeline_usa.0", "keystonepipeline_usa.0.a"),
)

_PP_OPTIONS = (
    ("canada.5", "canada.5.a"),
    ("canada.7", "canada.7.c"),
    ("canada.100", "canada.100.b"),
    ("canada.700", "canada.700.c"),
    ("canada.701", "canada.701.c"),
    ("canada_md_politics.25", "canada_md_politics.25.b"),
    ("canada_md_politics.26", "canada_md_politics.26.a"),
    ("canada.312", "canada.312.a"),
    ("canada.322", "canada.322.a"),
    ("canada.324", "canada.324.b"),
    ("canada.331", "canada.331.b"),
)

_STAT_LOSSES = (
    ("canada.7", "canada.7.c", "stability"),
    ("canada_md_politics.7", "canada_md_politics.7.a", "stability"),
    ("canada_md_politics.7", "canada_md_politics.7.b", "war_support"),
    ("canada_md_politics.8", "canada_md_politics.8.a", "stability"),
    ("canada_md_politics.8", "canada_md_politics.8.b", "war_support"),
    ("canada_md_politics.10", "canada_md_politics.10.b", "stability"),
    ("canada_md_politics.14", "canada_md_politics.14.a", "stability"),
    ("canada_md_politics.22", "canada_md_politics.22.a", "war_support"),
    ("canada_md_politics.22", "canada_md_politics.22.b", "stability"),
    ("keystonepipeline_can.1", "keystonepipeline_can.1.a", "stability"),
)


@pytest.mark.parametrize("event_id,option_name", _TREASURY_OPTIONS)
@pytest.mark.parametrize(
    "bankruptcy,deficit,factor",
    [(True, False, 0.25), (False, True, 0.5), (True, True, 0.125)],
)
def test_treasury_choices_discount_financial_risk(
    canadian_options, event_id, option_name, bankruptcy, deficit, factor
):
    option = _option(canadian_options, event_id, option_name)
    baseline = _weight(option)
    stressed = _weight(option, bankruptcy=bankruptcy, deficit=deficit)
    assert baseline > 0
    assert stressed == pytest.approx(baseline * factor)


@pytest.mark.parametrize("event_id,option_name", _PP_OPTIONS)
def test_political_power_choices_remain_possible_but_discount_bankruptcy(
    canadian_options, event_id, option_name
):
    option = _option(canadian_options, event_id, option_name)
    baseline = _weight(option)
    stressed = _weight(option, bankruptcy=True)
    assert baseline > 0
    assert stressed == pytest.approx(baseline * 0.25)


@pytest.mark.parametrize("event_id,option_name,stat", _STAT_LOSSES)
def test_stat_losses_discount_options_at_low_current_stat(
    canadian_options, event_id, option_name, stat
):
    option = _option(canadian_options, event_id, option_name)
    baseline = _weight(option)
    stressed = (
        _weight(option, war_support=0.1)
        if stat == "war_support"
        else _weight(option, stability=0.2)
    )
    assert baseline > 0
    assert stressed == pytest.approx(baseline * 0.25)


def test_cost_modifiers_preserve_historical_path_weights(canadian_options):
    paid = _option(canadian_options, "canada.312", "canada.312.a")
    fallback = _option(canadian_options, "canada.312", "canada.312.b")
    assert _weight(paid, historical=True) == 500
    assert _weight(paid, historical=True, bankruptcy=True) == 125
    assert _weight(fallback, historical=True) == 0
    assert _weight(fallback, historical=True, bankruptcy=True) == 50

    forbidden_path = _option(canadian_options, "canada.320", "canada.320.b")
    assert _weight(forbidden_path, historical=True, bankruptcy=True, deficit=True) == 0
