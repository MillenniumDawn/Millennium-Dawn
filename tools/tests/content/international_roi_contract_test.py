"""The 3% annual ROI contract from investments-guide.md and PR #5879.

The shipped 0.019 weekly conversion is approximate, not an exact 1/52 year.
Only the pure rate calculation is executed; native weekly accrual is not modeled.
"""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block


@pytest.fixture(scope="module")
def roi_effect():
    source = read_text(REPO_ROOT / "common/scripted_effects/00_money_system.txt")
    return script_block(source, "calculate_int_investments_rate")


# case: (principal, ROI modifier, cap, reinvest mode, collected, reinvested)
_ROI_CASES = {
    "collect base return": (100, 0, 0.2, 0, 0.057, 0),
    "reinvest base return": (100, 0, 0.2, 1, 0, 0.057),
    "split base return": (100, 0, 0.2, 2, 0.0285, 0.0285),
    "positive modifier": (100, 0.02, 0.2, 0, 0.095, 0),
    "negative modifier floors return": (100, -0.04, 0.2, 0, 0, 0),
    "national cap limits return": (100, 0.5, 0.1, 0, 0.19, 0),
    "no principal": (0, 0, 0.2, 2, 0, 0),
}


@pytest.mark.parametrize(
    "principal,modifier,cap,mode,collected,reinvested",
    _ROI_CASES.values(),
    ids=_ROI_CASES,
)
def test_roi_rate_splits_one_weekly_return_without_changing_principal(
    roi_effect, principal, modifier, cap, mode, collected, reinvested
):
    script = EconomicScriptFixture(
        {
            "int_investments": principal,
            "modifier@return_on_investment_modifier": modifier,
            "global.roi_rate_cap": cap,
            "@math_expressions_max": 100000000,
            "int_reinvest_mode": mode,
            "int_investments_collected_rate": -99,
            "int_investments_reinvest_rate": -99,
        }
    )
    script.execute(roi_effect)
    assert script.values["int_investments_collected_rate"] == pytest.approx(collected)
    assert script.values["int_investments_reinvest_rate"] == pytest.approx(reinvested)
    assert script.values["int_investments_rate"] == pytest.approx(
        collected + reinvested
    )
    assert script.values["int_investments"] == principal
    assert script.calls == []
