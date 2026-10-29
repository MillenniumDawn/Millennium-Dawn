"""Custom-cost payment detection against real scripted and calculated charges."""

import pytest
import validate_decisions as decisions
from shared.paths import REPO_ROOT
from shared.suite import decision_factory, decisions_results_for, read_text
from shared_utils import iter_statements, strip_comments
from validate_events import costly_scripted_effects


@pytest.fixture(scope="module")
def cost_effects():
    return costly_scripted_effects(
        strip_comments(read_text(REPO_ROOT / "common/scripted_effects" / filename))
        for filename in ["00_budget_effects.txt", "99_SOV_scripted_effects.txt"]
    )


@pytest.mark.parametrize(
    "filename,token,kind",
    [
        ("Russia.txt", "SOV_mobilise_omon", "command power"),
        ("Russia.txt", "SOV_mobilise_sobr", "command power"),
        ("Italy.txt", "extraordinary_church_donation", "treasury"),
    ],
)
@pytest.mark.parametrize("phase", ["complete_effect", "remove_effect"])
def test_custom_cost_must_be_paid_when_taken(
    monkeypatch, cost_effects, filename, token, kind, phase
):
    source = strip_comments(read_text(REPO_ROOT / "common/decisions" / filename))
    body = next(
        body
        for _, _, category in iter_statements(source)
        if category is not None
        for name, _, body in iter_statements(category)
        if name == token and body is not None
    )
    raw = f"\t{token} = {{{body}\t}}"
    if phase == "remove_effect":
        raw = raw.replace("complete_effect =", "remove_effect =", 1)
    factory = decision_factory(raw, filename)
    monkeypatch.setattr(
        decisions, "load_cost_lookups", lambda validator: (cost_effects, {})
    )

    findings = decisions_results_for(
        [factory], monkeypatch, "validate_custom_cost_charged"
    )

    if phase == "complete_effect":
        assert findings == []
    else:
        assert len(findings) == 1
        assert f"charges {kind} in remove_effect, not complete_effect" in findings[0][0]
