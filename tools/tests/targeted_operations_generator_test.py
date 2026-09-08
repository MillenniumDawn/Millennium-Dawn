import importlib.util
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest
from great_ai_race_state_model_test import _named_block, _parse_race_script

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "targeted_operations_generator",
    ROOT / "tools/generators/generate_targeted_operations.py",
)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


@pytest.fixture
def manifest():
    return GENERATOR.load_manifest(ROOT)


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate_id",
        "duplicate_key",
        "duplicate_group",
        "duplicate_ct_slot",
        "foreign_successor",
        "missing_successor",
        "foreign_group_successor",
        "generated_overlap",
        "generated_end",
        "capacity",
    ],
)
def test_manifest_rejects_ambiguous_or_cross_group_identities(
    tmp_path, manifest, defect
):
    data = deepcopy(manifest)
    if defect == "duplicate_id":
        data["targets"][1]["id"] = data["targets"][0]["id"]
    elif defect == "duplicate_key":
        data["targets"][1]["key"] = data["targets"][0]["key"]
    elif defect == "duplicate_group":
        data["groups"][1]["id"] = data["groups"][0]["id"]
    elif defect == "duplicate_ct_slot":
        data["groups"][1]["ct_id"] = data["groups"][0]["ct_id"]
    elif defect == "foreign_successor":
        data["targets"][0]["successors"].append(64)
    elif defect == "missing_successor":
        data["targets"][0]["successors"].append(999)
    elif defect == "foreign_group_successor":
        data["groups"][0]["succession"].append(64)
    elif defect == "generated_overlap":
        data["targets"][-1]["id"] = 65
    elif defect == "generated_end":
        data["generated_end"] = 130
    else:
        data["capacity"] += 1
    path = tmp_path / "tools/data/targeted_operations.json"
    path.parent.mkdir(parents=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        json.dump(data, stream)
    with pytest.raises(ValueError):
        GENERATOR.load_manifest(tmp_path)


def test_render_is_deterministic_and_tracked_outputs_are_current(manifest):
    assert GENERATOR.render(manifest) == GENERATOR.render(deepcopy(manifest))
    assert GENERATOR.generate(ROOT, check=True) == []


def test_registry_contains_full_launch_roster_and_all_legacy_isi_people(manifest):
    assert {target["id"] for target in manifest["targets"]} == set(range(1, 65)) | set(
        range(129, manifest["capacity"])
    )
    isi = [
        target
        for target in manifest["targets"]
        if target.get("legacy_isi_id") is not None
    ]
    assert {target["legacy_isi_id"] for target in isi} == set(range(1, 14))
    assert {target["id"] for target in isi} == set(range(16, 29))
    legacy = _parse_race_script(
        _named_block(
            (ROOT / "common/scripted_effects/99_ISI_scripted_effects.txt").read_text(
                encoding="utf-8"
            ),
            "ISI_setup_hvt_pool",
        )
    )["ISI_setup_hvt_pool"]
    loop = next(operand for key, _, operand in legacy if key == "for_loop_effect")
    bounds = {key: operand for key, _, operand in loop}
    assert int(bounds["start"]) == 1
    assert int(bounds["end"]) == 13
    assert bounds["compare"] == "less_than_or_equals"


def test_every_authored_location_host_resolves_to_a_real_country(manifest):
    countries = set()
    for path in (ROOT / "common/country_tags").glob("*.txt"):
        countries.update(
            re.findall(
                r"(?m)^\s*([A-Z0-9]{3})\s*=", path.read_text(encoding="utf-8-sig")
            )
        )
    hosts = {
        host
        for group in manifest["groups"]
        for host in [group["host"]]
        + group.get("movement_hosts", [])
        + group.get("regional_hosts", [])
    }
    assert hosts <= countries, sorted(hosts - countries)


def test_all_native_raids_bind_their_own_person_method_and_callback(manifest):
    text = GENERATOR.render(manifest)["common/raids/targeted_operations_raids.txt"]
    definitions = re.findall(r"(?m)^\s*(TOP_(drone|capture)_(\d+))\s*=", text)
    expected = {
        (f"TOP_{kind}_{ident}", kind, str(ident))
        for ident in range(1, manifest["capacity"])
        for kind in ("drone", "capture")
    }
    assert set(definitions) == expected
    assert len(definitions) == 2 * (manifest["capacity"] - 1)
    assert "has_dlc" not in text
    for token, kind, target in definitions:
        raid = _named_block(text, token)
        method = "1" if kind == "drone" else "2"
        visible = _named_block(raid, "visible")
        assert f"TOP_case_phase^{target} = 2" in visible
        assert f"TOP_case_method^{target} = {method}" in visible
        assert "TOP_authorized_target" not in visible
        # common/raids/ is parsed before the scripted trigger and effect files
        # register, and the engine does not substitute $PARAM$ for a trigger, so
        # each raid names its own gate and sets its own result variables.
        expected_gate = f"TOP_native_gate_{target}_{method}"
        for gate in ("show_target", "available", "launchable"):
            statements = _parse_race_script(_named_block(raid, gate))[gate]
            assert any(
                key == expected_gate and operand == "yes"
                for key, _, operand in statements
            ), (token, gate)
            assert not any(key == "TOP_native_authorized" for key, _, _ in statements)

        for tier, outcome in enumerate(
            ("failure", "limited_success", "success", "critical_success")
        ):
            levels = _named_block(raid, "success_levels")
            effects = _parse_race_script(
                _named_block(_named_block(levels, outcome), "actor_effects")
            )["actor_effects"]
            temps = {}
            for key, _, operand in effects:
                if key == "set_temp_variable":
                    for name, _, value in operand:
                        temps[name] = value
            assert temps == {
                "TOP_target": target,
                "TOP_method": method,
                "TOP_tier": str(tier),
            }, (token, outcome)
            assert any(key == "TOP_native_result_args" for key, _, _ in effects), (
                token,
                outcome,
            )


def test_every_raid_has_a_gate_that_binds_its_own_person_and_method(manifest):
    """The gate is the only thing carrying the binding into the raid."""
    rendered = GENERATOR.render(manifest)
    gates = rendered["common/scripted_triggers/06_targeted_operations_native_gates.txt"]
    raids = rendered["common/raids/targeted_operations_raids.txt"]

    defined = set(re.findall(r"(?m)^(TOP_native_gate_\d+_\d+) =", gates))
    expected = {
        f"TOP_native_gate_{ident}_{method}"
        for ident in range(1, manifest["capacity"])
        for method in (1, 2)
    }
    assert defined == expected

    for ident in range(1, manifest["capacity"]):
        for method in (1, 2):
            body = _named_block(gates, f"TOP_native_gate_{ident}_{method}")
            assert f"TOP_arg_target = {ident}" in body
            assert f"TOP_arg_method = {method}" in body
            assert "TOP_native_authorized = yes" in body

    # nothing in the generated raids may pass parameters
    assert "TOP_native_authorized = {" not in raids
    assert "TOP_native_result = {" not in raids


def test_generated_names_and_roles_have_english_localisation(manifest):
    output = GENERATOR.render(manifest)
    roster = output["localisation/english/MD_targeted_operations_roster_l_english.yml"]
    keys = set(re.findall(r"(?m)^ ([A-Za-z0-9_]+):", roster))
    for ident in range(1, manifest["capacity"]):
        assert {
            f"TOP_person_{ident}",
            f"TOP_drone_{ident}",
            f"TOP_capture_{ident}",
        } <= keys
    for target in manifest["targets"]:
        assert f"TOP_person_{target['id']}_role" in keys
    for path in (ROOT / "localisation/english").glob(
        "*targeted_operations*_l_english.yml"
    ):
        keys.update(
            re.findall(r"(?m)^ ([A-Za-z0-9_]+):", path.read_text(encoding="utf-8-sig"))
        )
    dispatch = output["common/scripted_localisation/01_targeted_operations_names.txt"]
    referenced = set(re.findall(r"localization_key\s*=\s*([A-Za-z0-9_]+)", dispatch))
    assert referenced <= keys, sorted(referenced - keys)


def test_reserved_successors_and_political_civilian_identity_are_separate(manifest):
    output = GENERATOR.render(manifest)
    registry = output["common/scripted_effects/01_targeted_operations_registry.txt"]
    assert "global.TOP_registry_capacity = 142" in registry
    for field in ("ct", "leader", "created", "destroyed", "window"):
        assert f"resize_array = {{ global.TOP_group_{field} = 22 }}" in registry
    generated = range(manifest["generated_start"], manifest["generated_end"])
    assert set(generated) == set(range(65, 129))
    for ident in generated:
        assert f"global.TOP_affiliation^{ident} =" in registry
    for field in GENERATOR.GLOBAL_FIELDS:
        assert f"resize_array = {{ global.TOP_{field} = 142 }}" in registry
    names = output["localisation/english/MD_targeted_operations_roster_l_english.yml"]
    for target in manifest["targets"]:
        ident = target["id"]
        assert f"TOP_person_{ident}: \"{target['name']}\"" in names
    assert {t["id"] for t in manifest["targets"] if t.get("civilian")} == {141}
    assert "global.TOP_civilian^141 = 1" in registry
    for ident in range(129, 142):
        assert f"TOP_authored_role_eligible_{ident} = yes" in registry
        assert f"global.TOP_political^{ident} = 1" in registry
    successors = output["common/scripted_effects/01_targeted_operations_successors.txt"]
    assert "TOP_person_129" not in successors
