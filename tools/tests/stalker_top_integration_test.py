import pytest
from great_ai_race_state_model_test import _parse_race_script
from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import TargetScript

ZONE_CRISIS = _parse_race_script(
    "x = { set_temp_variable = { STALKER_top_zone_crisis = 1 } }"
)["x"]


def _review(crisis, pattern):
    review = ReviewScript()
    if crisis:
        review.effects["STALKER_check_top_zone_crisis"] = ZONE_CRISIS
    review.actor.update(
        TOP_proposal_target=1,
        TOP_proposal_method=1,
        TOP_proposal_pattern=pattern,
        TOP_proposal_host_posture=1,
        TOP_proposal_doctrine=4,
        TOP_proposal_rigor=1,
    )
    review.actor["TOP_case_visit_status^1"] = 0
    return review


def test_zone_crisis_lowers_person_exposure_and_raises_harm():
    calm, crisis = _review(False, 80), _review(True, 80)
    calm.run("TOP_calculate_person_proposal_risks")
    crisis.run("TOP_calculate_person_proposal_risks")

    assert calm.actor["TOP_proposal_exposure_score"] == 95
    assert crisis.actor["TOP_proposal_exposure_score"] == 80
    assert calm.actor["TOP_proposal_harm_risk"] == 30
    assert crisis.actor["TOP_proposal_harm_risk"] == 40


def test_zone_crisis_harm_respects_the_ordinary_cap():
    person, organization = _review(True, 0), _review(True, 0)
    person.run("TOP_calculate_person_proposal_risks")
    organization.run("TOP_calculate_organization_proposal_risks")

    assert person.actor["TOP_proposal_harm_risk"] == 40
    assert organization.actor["TOP_proposal_harm_risk"] == 40


def test_zone_crisis_lowers_organization_exposure():
    calm, crisis = _review(False, 80), _review(True, 80)
    calm.run("TOP_calculate_organization_proposal_risks")
    crisis.run("TOP_calculate_organization_proposal_risks")

    assert (
        calm.actor["TOP_proposal_exposure_score"]
        - crisis.actor["TOP_proposal_exposure_score"]
        == 15
    )

@pytest.mark.parametrize("method", [1, 2])
def test_zone_crisis_adds_native_success_bonus_without_replacing_disruption(method):
    calm = TargetScript()
    calm_variables = calm.authorize(method=method)
    assert calm_variables["TOP_case_native_success_bonus"][11] == 0

    crisis = TargetScript()
    crisis.effects["STALKER_check_top_zone_crisis"] = ZONE_CRISIS
    group = int(crisis.globals["TOP_affiliation"][11])
    crisis.globals["TOP_group_disruption_type"][group] = 2
    crisis.globals["TOP_group_disruption_until"][group] = 90
    crisis_variables = crisis.authorize(method=method)
    assert crisis_variables["TOP_case_native_success_bonus"][11] == 20
