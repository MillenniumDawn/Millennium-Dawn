import json
import re
from datetime import date
from pathlib import Path

import pytest
from great_ai_race_state_model_test import _named_block, _parse_race_script
from targeted_operations_helpers_test import TargetedScript

ROOT = Path(__file__).resolve().parents[2]


class PoliticalScript(TargetedScript):
    """Execute authored role and mandate source with engine identities as fixtures."""

    country_trigger_fields = {
        "has_stability": "stability",
        "has_war_support": "support",
    }

    def __init__(self):
        source = (
            ROOT / "common/scripted_effects/03_targeted_operations_political_roster.txt"
        ).read_text(encoding="utf-8")
        # Country-leader traits are an engine-owned literal list, outside this evaluator.
        self.effects = _parse_race_script(
            re.sub(r"traits\s*=\s*\{[^{}]*\}", "traits = {}", source)
        )
        self.triggers = _parse_race_script(
            (
                ROOT
                / "common/scripted_triggers/03_targeted_operations_political_roster.txt"
            ).read_text(encoding="utf-8")
        )
        self.tags = {
            tag: index
            for index, tag in enumerate(
                (
                    "USA",
                    "SOV",
                    "BLR",
                    "UKR",
                    "PER",
                    "HEZ",
                    "IRQ",
                    "CHI",
                    "NKO",
                    "BRM",
                    "TUR",
                    "BRA",
                    "EGY",
                    "IND",
                    "SAU",
                    "ISR",
                    "VEN",
                ),
                1,
            )
        }
        self.countries = {
            index: {
                "tag": tag,
                "vars": {"ruling_party": 8},
                "exists": True,
                "government": "communism",
                "leader": "Other leader",
                "characters": set(),
                "ideas": set(),
                "civil_war": False,
                "wars": set(),
                "support": 0.7,
                "stability": 0.4,
                "eligible": True,
            }
            for tag, index in self.tags.items()
        }
        manifest = json.loads(
            (ROOT / "tools/data/targeted_operations.json").read_text(encoding="utf-8")
        )
        capacity = manifest["capacity"]
        self.globals = {"TOP_clock": 10, "TOP_registry_capacity": capacity}
        self.globals["active_terror_orgs"] = []
        self.globals.update({f"TOP_status^{i}": 1 for i in range(1, capacity)})
        for target in manifest["targets"]:
            ident = target["id"]
            self.globals[f"TOP_political^{ident}"] = int(
                target["target_class"] in {"official", "civilian"}
            )
            self.globals[f"TOP_civilian^{ident}"] = int(
                target["target_class"] == "civilian"
            )
        self.temps, self.scope_stack, self.leads = {}, [], []
        self.today, self.enabled = date(2026, 1, 1), True

    def value(self, name, identifier):
        if isinstance(name, str):
            if name in self.tags:
                return self.tags[name]
            if name == "THIS":
                return identifier
            if name.startswith("var:"):
                name = name[4:]
            if "^" in name:
                field, index = name.split("^", 1)
                name = f"{field}^{int(self.value(index, identifier))}"
        return super().value(name, identifier)

    def condition_statement(self, statement, identifier):
        key, comparison, operand = statement
        country = self.countries[identifier]
        if key in self.tags:
            result = self.condition(operand, self.tags[key])
        elif key in {"TOP_enabled", "TOP_country_eligible"}:
            eligible = self.enabled and (key == "TOP_enabled" or country["eligible"])
            result = eligible == (operand == "yes")
        elif key == "TOP_exceptional_authority":
            result = operand == "yes"
        elif key == "has_country_leader":
            data = dict(((name, value) for name, _, value in operand))
            assert data.get("ruling_only") == "yes"
            result = country["leader"] == data["name"].strip('"')
        elif key == "has_character":
            result = operand in country["characters"]
        elif key == "has_government":
            result = country["government"] == operand
        elif key == "has_civil_war":
            result = country["civil_war"] == (operand == "yes")
        elif key == "has_war_with":
            result = self.value(operand, identifier) in country["wars"]
        else:
            result = super().condition_statement(statement, identifier)
        return result

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        country = self.countries[identifier]
        if key in self.tags:
            self.execute(operand, self.tags[key])
        elif key in {"add_ideas", "remove_ideas"}:
            if key == "add_ideas":
                country["ideas"].add(operand)
            else:
                country["ideas"].discard(operand)
        elif key in {"recruit_character", "retire_character"}:
            if key == "recruit_character":
                country["characters"].add(operand)
            else:
                country["characters"].discard(operand)
        elif key == "kill_country_leader":
            country["leader"] = "Engine successor"
        elif key == "create_country_leader":
            data = dict(((name, value) for name, _, value in operand))
            country["leader"] = data["name"].strip('"')
        elif key.startswith("set_leader_"):
            country["leader"] = "Existing office successor"
        elif key in {"add_stability", "add_war_support"}:
            field = "stability" if key == "add_stability" else "support"
            country[field] += self.value(operand, identifier)
        elif key in {"TOP_add_target_lead", "TOP_grant_target_mandate"}:
            data = {name: self.value(value, identifier) for name, _, value in operand}
            target = int(data["TARGET"])
            if key == "TOP_add_target_lead":
                self.leads.append((identifier, target, data["AMOUNT"]))
            else:
                country["vars"][f"TOP_mandates^{target}"] = (
                    self.globals["TOP_clock"] + 365
                )
        elif key == "for_loop_effect":
            data = dict(((name, value) for name, _, value in operand))
            body = [
                entry for entry in operand if entry[0] not in {"start", "end", "value"}
            ]
            for index in range(
                int(self.value(data["start"], identifier)),
                int(self.value(data["end"], identifier)),
            ):
                self.temps[data["value"]] = index
                self.execute(body, identifier)
        else:
            super().execute_statement(statement, identifier)

    def run(self, name, identifier=1):
        self.execute(self.effects[name], identifier)

    # These triggers used to take a TARGET parameter. The engine does not
    # substitute $PARAM$ for a scripted trigger, so each now reads a temp
    # variable the caller sets first.
    TARGET_TEMPS = {
        "TOP_authored_role_eligible": "TOP_role_target",
        "TOP_authored_civilian_mandate_valid": "TOP_civilian_valid_target",
        "TOP_authored_capture_override": "TOP_civilian_valid_target",
    }

    def trigger(self, name, target=None, actor="USA"):
        if target is not None:
            self.temps[self.TARGET_TEMPS[name]] = target
        return self.condition([(name, "=", "yes")], self.tags[actor])

    def protect(self, target):
        self.temps["TOP_target"] = target
        self.run("TOP_get_protection_country")
        return self.temps["TOP_security_country"]

    def retire(self, target):
        self.globals[f"TOP_status^{target}"] = 2
        self.temps["TOP_target"] = target
        self.run("TOP_retire_political_roster")

    def enact_civilian_case(self, actor="USA"):
        parsed = _parse_race_script(
            (ROOT / "common/decisions/targeted_operations_political.txt").read_text(
                encoding="utf-8"
            )
        )
        category = parsed["TOP_political_authority"]
        decision = next(
            body for name, _, body in category if name == "TOP_civilian_emergency_case"
        )
        complete = next(body for name, _, body in decision if name == "complete_effect")
        self.execute(complete, self.tags[actor])


@pytest.mark.parametrize(
    "target,tag,name",
    [
        (129, "SOV", "Vladimir Putin"),
        (130, "SOV", "Dimitry Medvedev"),
        (130, "SOV", "Dmitry Medvedev"),
        (131, "BLR", "Alexander Lukashenko"),
        (132, "UKR", "Volodymyr Zelenskyy"),
        (133, "PER", "Ali Khamenei"),
        (134, "PER", "Mojtaba Khamenei"),
        (144, "CHI", "Xi Jinping"),
        (146, "NKO", "Kim Jong-un"),
        (147, "BRM", "Min Aung Hlaing"),
        (150, "TUR", "Recep Tayyip Erdoğan"),
        (152, "BRA", "Luiz Inácio Lula da Silva"),
        (153, "EGY", "Abdel Fattah el-Sisi"),
        (156, "IND", "Prabowo Subianto"),
        (158, "SAU", "Mohammed bin Salman Al-Saud"),
        (159, "ISR", "Benjamin Netanyahu"),
        (160, "VEN", "Nicolás Maduro"),
        (64, "PER", "Qasem Soleimani"),
        (56, "IRQ", "Saddam Hussein"),
    ],
)
def test_country_protection_requires_exact_active_serving_identity(target, tag, name):
    game = PoliticalScript()
    country = game.countries[game.tags[tag]]
    country["leader"] = name
    country["government"] = "nationalist"
    assert game.protect(target) == game.tags[tag]
    assert game.trigger("TOP_has_protected_official", actor=tag)
    for status in (0, 2, 3, 4):
        game.globals[f"TOP_status^{target}"] = status
        assert game.protect(target) == 0
        assert not game.trigger("TOP_has_protected_official", actor=tag)


def test_civilian_host_is_never_a_protection_owner():
    game = PoliticalScript()
    game.globals["TOP_host^141"] = game.tags["USA"]
    assert game.protect(141) == 0
    assert not game.trigger("TOP_has_protected_official", actor="USA")


def test_separate_supreme_office_succeeds_without_replacing_president():
    game = PoliticalScript()
    iran = game.countries[game.tags["PER"]]
    iran["ideas"].add("PER_sayyid_ali_hosseini_khamenei")
    assert game.protect(133) == game.tags["PER"]
    assert game.trigger("TOP_has_protected_official", actor="PER")
    game.retire(133)
    assert iran["leader"] == "Other leader"
    assert iran["ideas"] == {"PER_top_mojtaba_supreme_leader"}
    assert game.protect(134) == game.tags["PER"]
    game.retire(134)
    assert not iran["ideas"]
    assert iran["leader"] == "Other leader"


def test_supreme_ruler_succession_preserves_regime_and_available_candidate():
    game = PoliticalScript()
    iran = game.countries[game.tags["PER"]]
    iran["leader"] = "Ali Khamenei"
    game.retire(133)
    assert iran["leader"] == "Mojtaba Khamenei"
    assert iran["government"] == "communism"
    game.retire(134)
    assert iran["leader"] == "Existing office successor"


@pytest.mark.parametrize(
    "target,tag",
    [
        (129, "SOV"),
        (130, "SOV"),
        (131, "BLR"),
        (132, "UKR"),
        (133, "PER"),
        (134, "PER"),
    ],
)
def test_retirement_never_removes_an_unrelated_current_ruler(target, tag):
    game = PoliticalScript()
    game.retire(target)
    assert game.countries[game.tags[tag]]["leader"] == "Other leader"


@pytest.mark.parametrize(
    "target,token",
    [
        (135, "PER_mohammad_jafari"),
        (136, "PER_top_hossein_salami"),
        (137, "PER_mohammad_pakpour"),
        (138, "PER_top_esmail_qaani"),
        (139, "PER_amir_hajizadeh"),
        (140, "PER_ali_fadavi"),
    ],
)
def test_irgc_roles_need_recruited_character_and_current_service(target, token):
    game = PoliticalScript()
    iran = game.countries[game.tags["PER"]]
    assert not game.trigger("TOP_authored_role_eligible", target)
    iran["characters"].add(token)
    assert game.trigger("TOP_authored_role_eligible", target)
    assert game.protect(target) == game.tags["PER"]
    iran["government"] = "democratic"
    assert not game.trigger("TOP_authored_role_eligible", target)
    assert game.protect(target) == 0
    game.retire(target)
    assert token not in iran["characters"]


@pytest.mark.parametrize(
    "target,token", [(136, "PER_top_hossein_salami"), (138, "PER_top_esmail_qaani")]
)
def test_added_advisors_are_recruited_once_and_never_resurrected(target, token):
    game = PoliticalScript()
    iran = game.countries[game.tags["PER"]]
    game.globals.update({f"TOP_window^{target}": 1, f"TOP_status^{target}": 0})
    game.run("TOP_prepare_authored_service")
    assert token in iran["characters"]
    game.retire(target)
    game.run("TOP_prepare_authored_service")
    assert token not in iran["characters"]


def test_domestic_civilian_mandate_survives_its_cost_and_remains_target_specific():
    game = PoliticalScript()
    usa = game.countries[game.tags["USA"]]
    usa.update(civil_war=True, support=0.61)
    assert game.trigger("TOP_civilian_emergency_case_available")
    game.enact_civilian_case()
    assert usa["support"] == pytest.approx(0.56)
    assert usa["stability"] == pytest.approx(0.35)
    assert game.leads == [(game.tags["USA"], 141, 40)]
    assert game.trigger("TOP_authored_civilian_mandate_valid", 141)
    assert game.trigger("TOP_authored_capture_override", 141)
    for target in (0, 64, 129, 140, 142):
        assert not game.trigger("TOP_authored_capture_override", target)
    assert not game.trigger("TOP_civilian_emergency_case_available")


@pytest.mark.parametrize(
    "ended",
    [
        "civil_war",
        "government",
        "support",
        "stability",
        "expired",
        "custody",
        "origin",
        "disabled",
    ],
)
def test_civilian_mandate_loses_authority_immediately_when_crisis_ends(ended):
    game = PoliticalScript()
    usa = game.countries[game.tags["USA"]]
    usa["civil_war"] = True
    game.enact_civilian_case()
    if ended == "expired":
        game.globals["TOP_clock"] = usa["vars"]["TOP_mandates^141"]
    elif ended == "custody":
        game.globals["TOP_status^141"] = 2
    elif ended == "origin":
        usa["vars"]["TOP_civilian_mandate_origin"] = 2
    elif ended == "disabled":
        game.enabled = False
    else:
        usa[ended] = {
            "civil_war": False,
            "government": "democratic",
            "support": 0.5,
            "stability": 0.45,
        }[ended]
    assert not game.trigger("TOP_authored_civilian_mandate_valid", 141)
    assert not game.trigger("TOP_authored_capture_override", 141)


def test_foreign_civilian_mandate_requires_live_war_and_cannot_override_capture():
    game = PoliticalScript()
    russia = game.countries[game.tags["SOV"]]
    russia["wars"].add(game.tags["USA"])
    game.enact_civilian_case("SOV")
    assert game.trigger("TOP_authored_civilian_mandate_valid", 141, "SOV")
    assert not game.trigger("TOP_authored_capture_override", 141, "SOV")
    russia["wars"].clear()
    assert not game.trigger("TOP_authored_civilian_mandate_valid", 141, "SOV")


def test_wartime_opportunities_use_one_serving_person_and_a_country_cooldown():
    game = PoliticalScript()
    game.countries[game.tags["SOV"]]["leader"] = "Vladimir Putin"
    game.globals["TOP_host^129"] = game.tags["SOV"]
    game.countries[game.tags["USA"]]["wars"].add(game.tags["SOV"])
    game.run("TOP_political_country_opportunities")
    game.run("TOP_political_country_opportunities")
    assert game.leads == [(game.tags["USA"], 129, 25)]
    game.globals["TOP_clock"] += 91
    game.countries[game.tags["SOV"]]["leader"] = "Another leader"
    game.run("TOP_political_country_opportunities")
    assert len(game.leads) == 1


def test_maduro_retirement_has_an_idempotent_venezuelan_successor():
    source = (ROOT / "common/scripted_effects/VEN_political_leaders.txt").read_text(
        encoding="utf-8"
    )
    helper = _named_block(source, "TOP_retire_VEN_nicolas_maduro")
    assert (
        'has_country_leader = { name = "Nicolás Maduro" ruling_only = yes }' in helper
    )
    assert 'name = "Delcy Rodríguez"' in helper
    assert "ideology = anarchist_communism" in helper
    assert (ROOT / "gfx/leaders/generic_politicians/latin_female_001.dds").is_file()
