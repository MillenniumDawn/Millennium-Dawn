"""Regressions for meta_effect-constructed decision activations.

`activate_mission = cyber_op_slot_[SLOT]_[TYPE]` reaches the activation scan
with its placeholders intact, so the unused-decision check has to match on the
constant text around each `[...]` instead of literally.
"""

import validate_decisions as V


class _FakeValidator(V.Validator):
    """Validator whose _report collects results instead of rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collected = []

    def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
        self.collected.extend(results)


def _unused(tokens, activated_decisions, activated_missions, monkeypatch):
    factories = [
        V.DecisionFactory(
            f"{token} = {{\n\tallowed = {{ always = no }}\n}}", source_basename="X.txt"
        )
        for token in tokens
    ]
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(V, "parse_all_decision_factories", lambda mod_path: factories)
    monkeypatch.setattr(
        validator,
        "_get_activation_removal_scan",
        lambda: (activated_decisions, activated_missions, set()),
    )
    validator.validate_unused_decisions()
    return validator.collected


def test_placeholder_name_covers_matching_tokens(monkeypatch):
    assert (
        _unused(
            ["cyber_op_slot_0_gps_tracking", "cyber_op_slot_9_infra_tracking"],
            set(),
            {"cyber_op_slot_[SLOT]_[TYPE]"},
            monkeypatch,
        )
        == []
    )


def test_investment_placeholder_covers_defined_slots(monkeypatch):
    assert _unused(
        ["investments_project_0_target_decision", "unrelated_target_decision"],
        {"investments_project_[INDEX]_target_decision"},
        set(),
        monkeypatch,
    ) == ["unrelated_target_decision"]


def test_cyber_placeholder_rejects_out_of_domain_slot_and_type(monkeypatch):
    assert _unused(
        ["cyber_op_slot_10_gps_tracking", "cyber_op_slot_0_typo_tracking"],
        set(),
        {"cyber_op_slot_[SLOT]_[TYPE]"},
        monkeypatch,
    ) == ["cyber_op_slot_0_typo_tracking", "cyber_op_slot_10_gps_tracking"]


def test_investment_placeholder_rejects_out_of_domain_slot(monkeypatch):
    assert _unused(
        ["investments_project_15_target_decision"],
        {"investments_project_[INDEX]_target_decision"},
        set(),
        monkeypatch,
    ) == ["investments_project_15_target_decision"]


def test_unknown_placeholder_template_does_not_match(monkeypatch):
    assert _unused(
        ["custom_slot_0_mission"],
        set(),
        {"custom_slot_[SLOT]_mission"},
        monkeypatch,
    ) == ["custom_slot_0_mission"]


def test_targeted_mission_matches_the_decision_scan(monkeypatch):
    # A mission with a target is activated by activate_targeted_decision, which
    # lands in the decision set rather than the mission set.
    assert (
        _unused(
            ["investments_project_3_target_decision"],
            {"investments_project_3_target_decision"},
            set(),
            monkeypatch,
        )
        == []
    )


def test_unactivated_decision_still_flagged(monkeypatch):
    assert _unused(
        ["get_md_light_infantry"],
        {"get_blackwater_light_infantry"},
        {"get_wagner_light_infantry"},
        monkeypatch,
    ) == ["get_md_light_infantry"]


def test_activation_scan_uses_only_shipped_content_roots(tmp_path):
    shipped = tmp_path / "common" / "scripted_effects" / "effects.txt"
    shipped.parent.mkdir(parents=True)
    shipped.write_text("activate_mission = shipped_mission\n", encoding="utf-8")

    archived = tmp_path / "resources" / "archive.txt"
    archived.parent.mkdir()
    archived.write_text("activate_mission = archived_mission\n", encoding="utf-8")

    decisions, missions, removals = V.Validator(
        str(tmp_path), workers=1
    )._get_activation_removal_scan()

    assert decisions == set()
    assert missions == {"shipped_mission"}
    assert removals == set()
