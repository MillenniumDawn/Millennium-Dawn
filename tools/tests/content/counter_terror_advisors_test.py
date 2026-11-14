from pathlib import Path

import pytest
from script_model import TempScriptModel, _parse_race_script

ROOT = Path(__file__).resolve().parents[3]


class AdvisorEvent(TempScriptModel):
    def __init__(self, recipient, sender):
        self.scopes = {"ROOT": recipient, "FROM": sender}
        self.countries, self.globals, self.temps = {}, {}, {}
        self.events, self.tokens = [], []
        self.country(recipient, tag=recipient)
        self.country(sender, tag=sender)

    def condition_statement(self, statement, identifier):
        key, _, operand = statement
        if key in self.scopes:
            return self.condition(operand, self.scopes[key])
        if key == "tag":
            return identifier == self.scopes.get(operand, operand)
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key in self.scopes:
            self.execute(operand, self.scopes[key])
        elif key == "add_operation_token":
            fields = {name: value for name, _, value in operand}
            target = self.scopes.get(fields["tag"], fields["tag"])
            self.tokens.append((identifier, target, fields["token"]))
        elif key == "set_country_flag":
            flag = operand.replace("@FROM", f"@{self.scopes['FROM']}")
            super().execute_statement((key, comparison, flag), identifier)
        elif key not in {"name", "trigger", "log", "ai_chance"}:
            super().execute_statement(statement, identifier)


@pytest.mark.parametrize(
    ("recipient", "sender"),
    [
        ("ACE", "USA"),
        ("AFG", "USA"),
        ("ISR", "USA"),
        ("AFG", "ACE"),
        ("ISR", "ACE"),
        ("ACE", "ACE"),
        ("USA", "USA"),
    ],
)
def test_accepted_advisors_preserve_support_without_ace_operation_assets(
    recipient, sender
):
    source = (ROOT / "events/Counter Terror.txt").read_text(encoding="utf-8")
    events = _parse_race_script("events = {\n" + source + "\n}")["events"]
    event = next(
        body
        for key, _, body in events
        if key == "country_event" and ("id", "=", "MD_terror.13") in body
    )
    option = next(
        body
        for key, _, body in event
        if key == "option" and ("name", "=", "MD_terror.13.a") in body
    )
    script = AdvisorEvent(recipient, sender)

    script.execute(option, recipient)

    receiving_country = script.countries[recipient]
    if recipient == sender:
        assert "foreign_counter_terror_support" not in receiving_country["vars"]
        assert receiving_country["flags"] == {}
        assert script.events == []
    else:
        assert receiving_country["vars"]["foreign_counter_terror_support"] == 1
        assert receiving_country["flags"] == {f"has_ct_advisor_from@{sender}": None}
        assert script.events == [(sender, "MD_terror.15")]
    expected = (
        [(sender, recipient, "token_foreign_advisors")]
        if recipient != sender and recipient != "ACE"
        else []
    )
    assert script.tokens == expected
