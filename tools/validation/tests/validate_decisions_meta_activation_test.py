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
            ["cyber_op_slot_0_gps_tracking", "cyber_op_slot_11_infra_tracking"],
            set(),
            {"cyber_op_slot_[SLOT]_[TYPE]"},
            monkeypatch,
        )
        == []
    )


def test_placeholder_name_respects_prefix_and_suffix(monkeypatch):
    assert _unused(
        ["investments_project_0_target_decision", "unrelated_target_decision"],
        {"investments_project_[INDEX]_target_decision"},
        set(),
        monkeypatch,
    ) == ["unrelated_target_decision"]


def test_placeholder_needs_something_in_the_gap(monkeypatch):
    # A placeholder always substitutes to something, so the bare prefix+suffix
    # concatenation is not one of the names the template can build.
    assert _unused(
        ["cyber_op_slot_tracking"],
        set(),
        {"cyber_op_slot_[TYPE]tracking"},
        monkeypatch,
    ) == ["cyber_op_slot_tracking"]


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
