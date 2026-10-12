import re
from pathlib import Path

from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import TargetScript
from targeted_operations_model_test import _extract_block, _parse_race_script

ROOT = Path(__file__).resolve().parents[3]


def test_cleared_or_decayed_assessment_axes_do_not_show_stale_sources():
    localisation = (
        ROOT / "common/scripted_localisation/05_targeted_operations_sources.txt"
    ).read_text(encoding="utf-8")
    for name, confidence in (
        ("TOP_selected_axis_2_source", "TOP_location_confidence"),
        ("TOP_selected_axis_3_source", "TOP_pattern_confidence"),
        ("TOP_selected_axis_2_source", "TOP_org_location"),
        ("TOP_selected_axis_3_source", "TOP_org_activity"),
    ):
        match = re.search(rf"name = {name}\b", localisation)
        assert match
        definition = _extract_block(
            localisation, localisation.rfind("defined_text", 0, match.start())
        )
        subject = (
            "TOP_selected_organization"
            if confidence.startswith("TOP_org_")
            else "TOP_selected"
        )
        gate = f"check_variable = {{ {confidence}^{subject} > 0 }}"
        assert definition.count(gate) == 5


def test_public_identity_and_authored_lead_keep_distinct_sources():
    script = TargetScript()
    variables = script.target(11)
    script.globals["TOP_public_identity"][11] = 1
    variables["TOP_identity_confidence"][11] = 0
    variables["TOP_identity_source"][11] = 0
    variables["TOP_lead_state"][11] = 0
    script.execute(script.effects["TOP_seed_public_subjects"], 1)

    assert variables["TOP_identity_confidence"][11] == 100
    assert variables["TOP_identity_source"][11] == 1
    assert variables["TOP_lead_state"][11] == 0
    assert variables["TOP_lead_source"][11] == 0

    variables["TOP_location_confidence"][11] = 0
    variables["TOP_pattern_confidence"][11] = 0
    script.call("TOP_add_target_lead", TARGET=11, AMOUNT=10)

    assert variables["TOP_identity_source"][11] == 1
    assert variables["TOP_location_source"][11] == 2
    assert variables["TOP_pattern_source"][11] == 2
    assert variables["TOP_lead_source"][11] == 2


def test_focused_collection_relabels_only_axes_that_increase():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_identity_confidence"][11] = 100
    variables["TOP_identity_source"][11] = 1
    variables["TOP_location_source"][11] = 2
    variables["TOP_pattern_source"][11] = 2
    variables["TOP_lead_source"][11] = 2
    variables["TOP_collection_focus"][11] = 1
    script.temps.update(TOP_target=11, TOP_gain=20)

    script.run("TOP_apply_person_collection_gain", 1)

    assert variables["TOP_identity_source"][11] == 1
    assert variables["TOP_location_source"][11] == 3
    assert variables["TOP_pattern_source"][11] == 3
    assert variables["TOP_lead_source"][11] == 2

    variables["TOP_collection_focus"][11] = 2
    script.globals["TOP_clock"] = 100
    script.run("TOP_apply_person_collection_gain", 1)
    assert variables["TOP_lead_source"][11] == 3


def test_liaison_source_changes_only_for_accepted_assessment_and_lead():
    script = TargetScript()
    variables = script.target(11)
    script.globals["TOP_clock"] = 100
    variables["TOP_enabled"] = 1
    variables["TOP_lead_report_clock"][11] = 95
    variables["TOP_lead_age"][11] = 5
    for field in ("identity", "location", "pattern", "lead"):
        variables[f"TOP_{field}_source"][11] = 3
    script.temps.update(
        TOP_liaison_snapshot_kind=1,
        TOP_liaison_snapshot_id=11,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=50,
        TOP_liaison_axis_3=50,
        TOP_liaison_state=102,
        TOP_liaison_host=3,
        TOP_liaison_age=20,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert [
        variables[f"TOP_{field}_source"][11]
        for field in ("identity", "location", "pattern", "lead")
    ] == [3, 3, 3, 3]
    assert variables["TOP_lead_state"][11] == 101

    script.temps.update(TOP_liaison_axis_2=95, TOP_liaison_age=1)
    variables["TOP_view_lead_age"] = 5
    script.run("TOP_merge_liaison_snapshot", 1)
    assert [
        variables[f"TOP_{field}_source"][11]
        for field in ("identity", "location", "pattern", "lead")
    ] == [3, 4, 3, 4]
    assert variables["TOP_lead_state"][11] == 102
    assert variables["TOP_view_lead_age"] == 1


def test_liaison_confidence_gain_does_not_relabel_unchanged_local_lead():
    script = TargetScript()
    variables = script.target(11)
    script.globals["TOP_clock"] = 100
    for field, value in (
        ("TOP_lead_state", 101),
        ("TOP_lead_host", 2),
        ("TOP_lead_age", 10),
        ("TOP_lead_report_clock", 90),
    ):
        variables[field][11] = value
    variables["TOP_lead_source"][11] = 3
    variables["TOP_location_confidence"][11] = 20
    script.temps.update(
        TOP_liaison_snapshot_kind=1,
        TOP_liaison_snapshot_id=11,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=80,
        TOP_liaison_axis_3=50,
        TOP_liaison_state=101,
        TOP_liaison_host=2,
        TOP_liaison_age=10,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )

    script.run("TOP_merge_liaison_snapshot", 1)

    assert variables["TOP_location_source"][11] == 4
    assert variables["TOP_lead_source"][11] == 3
    assert variables["TOP_lead_report_clock"][11] == 90


def test_liaison_age_cache_requires_matching_subject_kind_for_overlapping_ids():
    script = TargetScript()
    variables = script.target(2)
    script.organization_truth(2, state=101, public=True)
    script.globals["TOP_group_class"][2] = 1
    variables["TOP_org_known"][2] = 1
    variables["TOP_enabled"] = 1
    variables["TOP_view_lead_age"] = 99
    variables["TOP_lead_age"][2] = 11
    script.globals["TOP_clock"] = 100

    script.temps.update(
        TOP_liaison_snapshot_kind=2,
        TOP_liaison_snapshot_id=2,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=95,
        TOP_liaison_axis_3=50,
        TOP_liaison_state=102,
        TOP_liaison_host=3,
        TOP_liaison_age=1,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_view_lead_age"] == 99

    variables["TOP_selected_kind"] = 2
    variables["TOP_selected_organization"] = 2
    variables["TOP_view_lead_age"] = 88
    variables["TOP_org_lead_age"][2] = 12
    script.temps.update(TOP_liaison_snapshot_kind=1)
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_view_lead_age"] == 88


def test_organization_sources_follow_authored_collection_and_liaison_reports():
    script = TargetScript()
    script.organization_truth(2, state=101, public=True)
    variables = script.countries[1]["vars"]
    script.call("TOP_add_organization_lead", GROUP=2, AMOUNT=10)
    assert variables["TOP_org_verification_source"][2] == 1
    assert variables["TOP_org_location_source"][2] == 2
    assert variables["TOP_org_activity_source"][2] == 2
    assert variables["TOP_org_lead_source"][2] == 2

    variables["TOP_org_collection_focus"][2] = 1
    script.temps.update(TOP_group_target=2, TOP_gain=12)
    script.run("TOP_apply_organization_collection_gain", 1)
    assert variables["TOP_org_verification_source"][2] == 1
    assert variables["TOP_org_location_source"][2] == 3
    assert variables["TOP_org_activity_source"][2] == 3

    script.globals["TOP_clock"] = 100
    variables["TOP_enabled"] = 1
    variables["TOP_selected_kind"] = 2
    variables["TOP_selected_organization"] = 2
    variables["TOP_org_lead_report_clock"][2] = 95
    script.temps.update(
        TOP_liaison_snapshot_kind=2,
        TOP_liaison_snapshot_id=2,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=5,
        TOP_liaison_axis_3=5,
        TOP_liaison_state=102,
        TOP_liaison_host=3,
        TOP_liaison_age=20,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_org_lead_source"][2] == 2
    script.temps.update(TOP_liaison_axis_2=95, TOP_liaison_age=1)
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_org_location_source"][2] == 4
    assert variables["TOP_org_lead_source"][2] == 4
    variables["TOP_view_lead_age"] = 5
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_view_lead_age"] == 1


def test_host_report_labels_only_axes_it_can_raise():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_send_host_request")
    review.globals["TOP_clock"] = 1
    review.actor["TOP_identity_confidence^1"] = 100
    review.actor["TOP_identity_source^1"] = 1
    review.actor["TOP_location_confidence^1"] = 95
    review.actor["TOP_location_source^1"] = 3
    review.actor["TOP_lead_source^1"] = 3
    review.call("TOP_answer_host_request", identifier=2, POSTURE=2)

    assert review.actor["TOP_identity_source^1"] == 1
    assert review.actor["TOP_location_confidence^1"] == 100
    assert review.actor["TOP_location_source^1"] == 5
    assert review.actor["TOP_lead_source^1"] == 5


def test_host_report_marks_encoded_person_and_organization_leads():
    encoded_state = -10737.40617
    person = ReviewScript()
    person.ready_for_host()
    person.run("TOP_send_host_request")
    person.globals["TOP_clock"] = 1
    person.actor["TOP_lead_state^1"] = encoded_state
    person.actor["TOP_lead_report_clock^1"] = 0
    person.call("TOP_answer_host_request", identifier=2, POSTURE=2)
    assert person.actor["TOP_lead_source^1"] == 5

    host_answer = (
        ROOT
        / "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
    ).read_text(encoding="utf-8")
    assert (
        "NOT = { check_variable = { TOP_org_lead_state^TOP_proposal_subject_id = 0 } }"
        in host_answer
    )


def test_review_return_records_resumed_collection():
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)

    review.run("TOP_return_recorded_collection")

    rows = review.actor["TOP_history_rows"]
    assert review.actor[f"TOP_history_event^{int(rows[-1])}"] == 2
    assert review.actor[f"TOP_history_subject_kind^{int(rows[-1])}"] == 1
    assert review.actor[f"TOP_history_subject_id^{int(rows[-1])}"] == 1


def test_source_and_freshness_dispatchers_require_a_current_lead():
    source = (
        ROOT / "common/scripted_localisation/05_targeted_operations_sources.txt"
    ).read_text(encoding="utf-8")
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_selected"] = 11
    variables["TOP_lead_source"][11] = 3

    for name, expected_when_present in (
        ("TOP_selected_lead_source", "TOP_source_3"),
        ("TOP_selected_lead_freshness", "TOP_lead_freshness_known"),
    ):
        start = source.rfind("defined_text = {", 0, source.index(f"name = {name}"))
        entries = _parse_race_script(_extract_block(source, start))["defined_text"]

        def selected_key():
            for key, _, fields in entries:
                if key != "text":
                    continue
                values = {field: value for field, _, value in fields}
                if "trigger" not in values or script.condition(values["trigger"], 1):
                    return values["localization_key"]
            raise AssertionError("No matching defined text")

        variables["TOP_lead_state"][11] = -10737.40617
        assert selected_key() == expected_when_present
        variables["TOP_lead_state"][11] = 0
        assert selected_key() == (
            "TOP_source_0"
            if name == "TOP_selected_lead_source"
            else "TOP_lead_freshness_none"
        )


def test_person_case_milestones_follow_real_package_transitions():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_package_state"][11] = 0
    script.run("TOP_designate_selected", 1)
    script.call("TOP_open_person_review_case", TARGET=11)
    script.call("TOP_close_case", TARGET=11, SEQUENCE=1)
    script.run("TOP_abandon_person_package", 1)
    script.run("TOP_designate_selected", 1)

    rows = variables["TOP_history_rows"]
    assert [variables["TOP_history_event"][int(row)] for row in rows] == [1, 4, 8, 9, 1]
    assert [variables["TOP_history_package_cycle"][int(row)] for row in rows] == [
        1,
        1,
        1,
        1,
        2,
    ]
    assert [variables["TOP_history_case_sequence"][int(row)] for row in rows] == [
        0,
        1,
        1,
        0,
        0,
    ]


def test_preparation_operation_and_reports_use_separate_milestones():
    person = TargetScript()
    person_variables = person.authorize(method=1)
    assert person_variables["TOP_history_event"][0] == 6
    assert person_variables["TOP_history_reason"][0] == 31
    person.temps["TOP_tier"] = 2
    person.run("TOP_complete_operation", 1)
    person_events = [
        person_variables["TOP_history_event"][int(row)]
        for row in person_variables["TOP_history_rows"]
    ]
    assert person_events[:3] == [6, 10, 7]

    organization = TargetScript()
    organization_variables = organization.authorize_organization(objective=2)
    assert organization_variables["TOP_history_event"][0] == 10
    assert organization_variables["TOP_history_reason"][0] == 42
    organization.run("TOP_resolve_organization_operation", 1)
    assert organization_variables["TOP_history_event"][1] == 7


def test_history_rows_retain_package_and_case_keys_and_roll_over():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_history_cycle"][11] = 1
    variables["TOP_case_sequence"][11] = 5
    script.globals["TOP_clock"] = 40
    script.temps["TOP_history_current_event"] = 4
    script.call("TOP_log_person_milestone", TARGET=11)

    assert variables["TOP_history_rows"] == [0]
    assert variables["TOP_history_package_cycle"][0] == 1
    assert variables["TOP_history_case_sequence"][0] == 5
    assert variables["TOP_history_day"][0] == 40

    variables["TOP_history_cycle"][11] = 2
    variables["TOP_case_sequence"][11] = 9
    script.globals["TOP_clock"] = 60
    script.temps["TOP_history_current_event"] = 1
    script.call("TOP_log_person_milestone", TARGET=11)
    assert variables["TOP_history_package_cycle"][1] == 2
    assert variables["TOP_history_case_sequence"][1] == 0

    for day in range(61, 190):
        script.globals["TOP_clock"] = day
        script.temps["TOP_history_current_event"] = 2
        script.call("TOP_log_person_milestone", TARGET=11)

    assert len(variables["TOP_history_rows"]) == 128
    assert variables["TOP_history_rows"][0] == 3
    assert variables["TOP_history_day"][0] == 187
    assert variables["TOP_history_day"][1] == 188
    assert variables["TOP_history_day"][2] == 189


def test_history_view_follows_selected_subject():
    script = TargetScript()
    variables = script.target(11)
    script.target(12)
    view = (ROOT / "common/scripted_effects/01_targeted_operations_view.txt").read_text(
        encoding="utf-8"
    )
    script.effects.update(_parse_race_script(view))
    script.stubs.remove("TOP_build_view")
    variables["TOP_tab"] = 6
    for target in (11, 12):
        variables["TOP_history_cycle"][target] = 1
        script.temps["TOP_history_current_event"] = 1
        script.call("TOP_log_person_milestone", TARGET=target)

    variables["TOP_selected"] = 11
    script.run("TOP_build_view", 1)
    assert variables["TOP_visible_history"] == [0]
    variables["TOP_selected"] = 12
    script.run("TOP_build_view", 1)
    assert variables["TOP_visible_history"] == [1]


def test_history_wrap_refreshes_an_open_tab_when_another_subject_replaces_its_row():
    script = TargetScript()
    variables = script.target(11)
    script.target(12)
    variables["TOP_tab"] = 6
    variables["TOP_selected_kind"] = 1
    variables["TOP_selected"] = 11
    variables["TOP_history_rows"] = [0]
    variables["TOP_visible_history"] = [0]
    variables["TOP_history_cursor"] = 0
    before = script.external["TOP_refresh_view", 1]
    script.temps["TOP_history_current_event"] = 2

    script.call("TOP_log_person_milestone", TARGET=12)

    assert variables["TOP_visible_history"] == []
    assert script.external["TOP_refresh_view", 1] == before + 1
