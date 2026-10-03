from pathlib import Path

from targeted_operations_core_test import TargetScript
from targeted_operations_model_test import _parse_race_script

ROOT = Path(__file__).resolve().parents[2]
CT_SETUP = _parse_race_script(
    (ROOT / "common/scripted_effects/00_ct_effects.txt").read_text(encoding="utf-8")
)["counter_terror_global_setup"]


def test_registry_initialization_precedes_country_startup():
    calls = [name for name, _, _ in CT_SETUP]
    assert calls.index("TOP_initialize_global") < calls.index("create_staggered_cycle")


def test_country_case_arrays_use_registry_capacity_at_startup():
    script = TargetScript()
    script.globals.clear()
    script.globals.update(TOP_rule_mode=1)
    country_vars = script.countries[1]["vars"]
    country_vars.clear()

    initialized = []
    for name, _, operand in CT_SETUP:
        if name == "TOP_initialize_global":
            assert operand == "yes"
            script.run("TOP_setup_registry", 1)
            initialized.append(name)
        elif name == "create_staggered_cycle":
            assert operand == "yes"
            script.run("TOP_country_initialize", 1)
            initialized.append(name)

    assert sorted(initialized) == ["TOP_initialize_global", "create_staggered_cycle"]
    capacity = script.globals["TOP_registry_capacity"]
    assert capacity == 161
    assert len(country_vars["TOP_known"]) == capacity

    case_arrays = [
        operand[0][0]
        for name, _, operand in script.effects["TOP_initialize_cases"]
        if name == "resize_array"
    ]
    assert len(case_arrays) == len(set(case_arrays)) == 39
    assert "TOP_case_native_prepared" in case_arrays
    assert "TOP_case_native_success_bonus" in case_arrays
    assert "TOP_case_native_success_penalty" in case_arrays
    assert all(name.startswith("TOP_case_") for name in case_arrays)
    assert {
        "TOP_case_identity",
        "TOP_case_location",
        "TOP_case_pattern",
        "TOP_case_lead_age",
        "TOP_case_access",
        "TOP_case_host_posture",
        "TOP_case_doctrine",
        "TOP_case_attribution",
        "TOP_case_harm",
        "TOP_case_oversight",
    } <= set(case_arrays)
    assert {name: len(country_vars[name]) for name in case_arrays} == {
        name: capacity for name in case_arrays
    }

    organization_arrays = [
        operand[0][0]
        for name, _, operand in script.effects["TOP_initialize_organization_cases"]
        if name == "resize_array"
    ]
    group_capacity = len(script.globals["TOP_group_class"])
    assert len(organization_arrays) == len(set(organization_arrays))
    assert all(name.startswith("TOP_org_case_") for name in organization_arrays)
    assert "TOP_org_case_protection" in organization_arrays
    assert {name: len(country_vars[name]) for name in organization_arrays} == {
        name: group_capacity for name in organization_arrays
    }
