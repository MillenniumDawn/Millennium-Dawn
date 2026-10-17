from collections import Counter

import pytest
from targeted_operations_core_test import ROOT, TargetScript
from targeted_operations_model_test import _parse_race_script


class CrisisOpinionScript(TargetScript):
    """Execute crisis responses with native opinion-target restrictions."""

    def __init__(self):
        super().__init__()
        self.effects.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_effects/05_targeted_operations_runtime.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.crisis_events = _parse_race_script(
            "events = {\n"
            + (ROOT / "events/Targeted Operations Runtime.txt").read_text(
                encoding="utf-8"
            )
            + "\n}"
        )["events"]
        self.stubs.add("TOP_cleanup_crisis")
        self.stubs.discard("TOP_process_crisis")
        self.opinions = Counter()
        self.changes = Counter()
        self.globals.update(
            TOP_clock=100,
            TOP_crisis_active=1,
            TOP_crisis_token=7,
            TOP_crisis_until=200,
            TOP_crisis_actor=1,
            TOP_crisis_protection=2,
            TOP_crisis_host=3,
            TOP_crisis_story=1,
            TOP_crisis_visit_token=1,
            TOP_crisis_tension=50,
            TOP_crisis_sanctions_threshold=30,
            TOP_crisis_ultimatum_threshold=85,
            TOP_crisis_actor_response=1,
            TOP_crisis_settlement_apology_pp=-25,
        )
        for actor in (1, 2, 3):
            self.countries[actor]["vars"]["TOP_crisis_token"] = 7
        self.countries[3]["vars"].update(
            TOP_crisis_participant_pending=1,
            TOP_crisis_participant_token=7,
        )

    def condition_statement(self, statement, identifier):
        if statement[0] == "subtract_from_temp_variable":
            self.execute_statement(statement, identifier)
            return True
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key in {"add_opinion_modifier", "reverse_add_opinion_modifier"}:
            fields = {name: value for name, _, value in operand}
            target = fields["target"]
            assert not target.startswith(
                "var:"
            ), "The native opinion effect rejects variable scopes as its target"
            target = self.value(target, identifier)
            source, recipient = identifier, target
            if key == "reverse_add_opinion_modifier":
                source, recipient = recipient, source
            self.opinions[source, recipient, fields["modifier"]] += 1
        elif key in {"add_stability", "add_war_support"}:
            self.changes[key, identifier] += self.value(operand, identifier)
        else:
            super().execute_statement(statement, identifier)

    def choose(self, event_id, option_name, actor):
        event = next(
            body
            for key, _, body in self.crisis_events
            if key == "country_event" and ("id", "=", event_id) in body
        )
        assert self.condition(
            dict((key, value) for key, _, value in event)["trigger"], actor
        )
        option = next(
            body
            for key, _, body in event
            if key == "option" and ("name", "=", option_name) in body
        )
        fields = dict((key, value) for key, _, value in option)
        assert self.condition(fields.get("trigger", []), actor)
        self.execute(
            [
                entry
                for entry in option
                if entry[0] not in {"name", "trigger", "ai_chance"}
            ],
            actor,
        )


@pytest.mark.parametrize(
    "effect,expired,modifier",
    [
        ("TOP_apply_crisis_sanctions", False, "harsh_sanctions"),
        ("TOP_process_crisis", True, "harsh_sanctions"),
        ("TOP_settle_crisis", False, "TOP_crisis_settlement"),
    ],
)
def test_crisis_resolution_keeps_both_opinion_directions(effect, expired, modifier):
    script = CrisisOpinionScript()
    if expired:
        script.globals["TOP_crisis_until"] = 99

    script.run(effect, 2)

    assert script.opinions == Counter({(1, 2, modifier): 1, (2, 1, modifier): 1})
    if modifier == "harsh_sanctions":
        assert script.changes == Counter({("add_stability", 1): -0.01})
    else:
        assert script.countries[1]["vars"]["political_power"] == 475
    if effect != "TOP_apply_crisis_sanctions":
        assert script.external["TOP_cleanup_crisis", 2] == 1


@pytest.mark.parametrize(
    "event,option,actor,target,modifier",
    [
        ("TOP_crisis.1", "TOP_crisis.1.b", 2, 1, "TOP_sovereignty_violation"),
        ("TOP_crisis.4", "TOP_crisis.4.a", 3, 2, "established_diplomatic_relations"),
        ("TOP_crisis.4", "TOP_crisis.4.b", 3, 1, "established_diplomatic_relations"),
        ("TOP_crisis.3", "TOP_crisis.3.c", 2, 1, "TOP_sovereignty_violation"),
    ],
)
def test_crisis_option_changes_only_the_respondents_opinion(
    event, option, actor, target, modifier
):
    script = CrisisOpinionScript()

    script.choose(event, option, actor)

    assert script.opinions == Counter({(actor, target, modifier): 1})


@pytest.mark.parametrize("effect", ["TOP_apply_crisis_sanctions", "TOP_settle_crisis"])
@pytest.mark.parametrize("invalid", ["disabled", "stale", "expired"])
def test_invalid_crisis_does_not_apply_opinions_or_costs(effect, invalid):
    script = CrisisOpinionScript()
    if invalid == "disabled":
        script.globals["TOP_rule_mode"] = 0
    elif invalid == "stale":
        script.countries[2]["vars"]["TOP_crisis_token"] = 6
    else:
        script.globals["TOP_crisis_until"] = 99

    script.run(effect, 2)

    assert not script.opinions
    assert not script.changes
    assert script.countries[1]["vars"]["political_power"] == 500


def test_sanctions_require_the_recorded_victim():
    script = CrisisOpinionScript()

    script.run("TOP_apply_crisis_sanctions", 3)

    assert not script.opinions
    assert not script.changes


def test_crisis_with_annexed_principal_cleans_up_instead_of_repeating_ultimatum():
    script = CrisisOpinionScript()
    script.globals.update(TOP_crisis_tension=100, TOP_crisis_until=99)
    script.countries[2]["exists"] = False

    script.run("TOP_process_crisis", 1)

    assert script.external["TOP_cleanup_crisis", 1] == 1
    assert not script.opinions
    assert not script.events
