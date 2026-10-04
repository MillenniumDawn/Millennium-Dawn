from pathlib import Path

import pytest
from targeted_operations_core_test import ScriptArray, TargetScript
from targeted_operations_model_test import _named_block, _parse_race_script

ROOT = Path(__file__).resolve().parents[2]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class IntelligenceScript(TargetScript):
    def __init__(self, roll=0):
        super().__init__()
        gui = _named_block(
            source("common/scripted_guis/00_missiles_scripted_guis.txt"),
            "MD_CT_system_gui",
        )
        for name, destination in (
            ("effects", self.effects),
            ("triggers", self.triggers),
        ):
            destination.update(
                (key, body)
                for key, _, body in _parse_race_script(_named_block(gui, name))[name]
            )
        self.stubs.update({"international_systems_update", "custom_effect_tooltip"})
        self.roll = roll
        self.globals["num_days"] = 0
        self.globals["active_terror_orgs"] = ScriptArray([0, 10, 33])
        self.countries[1]["vars"].update(
            selected_org=0,
            ct_mass_gather_store_var=ScriptArray([0, 3, 7]),
            international_terror_org_temp_specific_intel=ScriptArray([0, 0, 0]),
        )

    def condition_statement(self, statement, identifier):
        if statement[0] == "custom_trigger_tooltip":
            return self.condition(
                [entry for entry in statement[2] if entry[0] != "tooltip"], identifier
            )
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        if statement[0] == "randomize_temp_variable":
            fields = {key: value for key, _, value in statement[2]}
            assert fields == {
                "var": "num_add",
                "min": "0",
                "max": "5",
                "distribution": "uniform",
            }
            self.temps[fields["var"]] = self.roll
        else:
            super().execute_statement(statement, identifier)


@pytest.mark.parametrize("slot", [0, 1, 2])
@pytest.mark.parametrize("roll", [0, 2.5, 5])
def test_gather_then_exploit_uses_only_the_selected_organization(slot, roll):
    script = IntelligenceScript(roll)
    variables = script.countries[1]["vars"]
    variables["selected_org"] = slot
    before = list(variables["ct_mass_gather_store_var"])
    assert script.condition(script.triggers["mass_gathering_button_click_enabled"], 1)

    script.run("mass_gathering_button_click", 1)

    expected = before.copy()
    expected[slot] += roll + 1
    assert variables["ct_mass_gather_store_var"] == expected
    assert variables["political_power"] == 400
    assert script.countries[1]["flags"]["recent_ct_intel_op"] == 210
    assert not script.condition(
        script.triggers["mass_gathering_button_click_enabled"], 1
    )
    assert script.condition(
        script.triggers["exploit_intelligence_button_click_enabled"], 1
    )

    script.run("exploit_intelligence_button_click", 1)

    boost = [0, 0, 0]
    boost[slot] = expected[slot] * 1.25
    expected[slot] = 0
    assert variables["ct_mass_gather_store_var"] == expected
    assert variables["international_terror_org_temp_specific_intel"] == boost
    assert variables["political_power"] == 400
    assert script.external["international_systems_update", 1] == 2
    assert not script.condition(
        script.triggers["exploit_intelligence_button_click_enabled"], 1
    )


@pytest.mark.parametrize("slot", [-1, 3])
def test_invalid_organization_cannot_gather_or_exploit(slot):
    script = IntelligenceScript()
    script.countries[1]["vars"]["selected_org"] = slot
    for action in ("mass_gathering", "exploit_intelligence"):
        assert not script.condition(
            script.triggers[f"{action}_button_click_enabled"], 1
        )


def test_player_and_ai_gather_into_the_same_organization_array():
    write = "add_to_variable = { ct_mass_gather_store_var^selected_org = num_add }"
    player = _named_block(
        source("common/scripted_guis/00_missiles_scripted_guis.txt"),
        "mass_gathering_button_click",
    )
    assert write in player
    assert write in source("common/scripted_effects/00_ct_ai_effects.txt")


def panel_body_key(script):
    definitions = _parse_race_script(
        "root = {\n"
        + source("common/scripted_localisation/01_targeted_operations_status.txt")
        + "\n}"
    )["root"]
    panel = next(
        body for _, _, body in definitions if ("name", "=", "TOP_panel_body") in body
    )
    for kind, _, body in panel:
        if kind != "text":
            continue
        fields = {key: value for key, _, value in body}
        if script.condition(fields.get("trigger", []), 1):
            return fields["localization_key"]
    raise AssertionError("No Dossiers body matched")


@pytest.mark.parametrize("tab", [0, 1, 2, 3, 4])
@pytest.mark.parametrize("has_person", [False, True])
@pytest.mark.parametrize("selected", [0, 11])
def test_operations_center_person_tabs_require_a_known_typed_selection(
    tab, has_person, selected
):
    script = TargetScript()
    if has_person:
        script.target(11)
    script.countries[1]["vars"].update(
        TOP_tab=tab, TOP_selected=selected, TOP_selected_kind=1
    )

    if tab == 4:
        expected = "TOP_archive_help"
    elif not has_person or selected == 0:
        expected = "TOP_select_subject_body"
    else:
        expected = {
            0: "TOP_person_dossier_body",
            1: "TOP_person_package_body",
            2: "TOP_person_authority_body",
            3: "TOP_person_custody_body",
        }[tab]
    assert panel_body_key(script) == expected


@pytest.mark.parametrize("selected", [-1, 12, 161])
def test_operations_center_rejects_invalid_or_undiscovered_person_selections(selected):
    script = TargetScript()
    script.target(11)
    script.countries[1]["vars"].update(
        TOP_selected=selected, TOP_selected_kind=1, TOP_tab=0
    )
    assert panel_body_key(script) == "TOP_select_subject_body"


@pytest.mark.parametrize(
    ("tab", "expected"),
    [
        (0, "TOP_organization_dossier_body"),
        (1, "TOP_organization_package_body"),
        (2, "TOP_organization_authority_body"),
        (3, "TOP_organization_custody_disabled_body"),
        (4, "TOP_archive_help"),
    ],
)
def test_operations_center_organization_tabs_use_separate_lifecycle(tab, expected):
    script = TargetScript()
    script.authorize_organization(group=2, begin=False)
    script.countries[1]["vars"]["TOP_tab"] = tab

    assert panel_body_key(script) == expected


def test_unselected_operations_center_explains_cold_dossier_workflow():
    localisation = source(
        "localisation/english/MD_targeted_operations_redesign_l_english.yml"
    )
    line = next(
        line
        for line in localisation.splitlines()
        if line.startswith(" TOP_select_subject_body:")
    )
    _, _, value = line.strip().partition(":")

    assert "[TOP_selected_" not in value
    assert "[?TOP_" not in value
    assert "pick a target" in value
    assert "§YCold§!" in value
    assert "no open case yet" in value
    assert value.index("Designate Case") < value.index("Collect Intelligence")
    assert value.index("Collect Intelligence") < value.index("Authority")
    assert "review and, if approved" in value
    assert value.index("Authority") < value.index("Begin Preparation / Operation")
