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
        "target_class",
        "group_class",
        "location_policy",
        "unknown_source",
        "stable_target_key",
        "stable_group_key",
        "negative_ct_slot",
        "group_public_identity",
        "target_public_identity",
        "facility_default",
        "empty_facility_override",
        "unknown_facility_override",
        "leader_role",
        "leader_office",
        "consequence_profile",
        "duplicate_successor",
        "incomplete_successor",
        "fixed_state_without_state",
        "empty_activation_condition",
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
    elif defect == "capacity":
        data["capacity"] += 1
    elif defect == "target_class":
        data["targets"][0]["target_class"] = "person"
    elif defect == "group_class":
        data["groups"][0]["group_class"] = "organization"
    elif defect == "location_policy":
        data["groups"][0]["location_policy"] = "random_state"
    elif defect == "unknown_source":
        data["targets"][0]["sources"].append("missing_source")
    elif defect == "stable_target_key":
        data["targets"][0]["key"], data["targets"][1]["key"] = (
            data["targets"][1]["key"],
            data["targets"][0]["key"],
        )
    elif defect == "stable_group_key":
        data["groups"][0]["key"], data["groups"][1]["key"] = (
            data["groups"][1]["key"],
            data["groups"][0]["key"],
        )
    elif defect == "negative_ct_slot":
        data["groups"][0]["ct_id"] = -1
    elif defect == "group_public_identity":
        data["groups"][0]["public_identity"] = True
    elif defect == "target_public_identity":
        data["targets"][0]["public_identity"] = True
    elif defect == "facility_default":
        data["facility_objective_defaults"]["state_security"] = [
            "command",
            "funding",
        ]
    elif defect == "empty_facility_override":
        data["groups"][0]["facility_objectives"] = []
    elif defect == "unknown_facility_override":
        data["groups"][0]["facility_objectives"] = ["safehouse"]
    elif defect == "leader_role":
        data["targets"][0]["leader_role"] = "president"
    elif defect == "leader_office":
        leader = next(
            target for target in data["targets"] if target["leader_role"] != "none"
        )
        leader["role_eligibility"]["office_keys"] = []
    elif defect == "consequence_profile":
        data["targets"][0]["consequence_profile"] = "political_leader"
    elif defect == "fixed_state_without_state":
        fixed = next(g for g in data["groups"] if g["location_policy"] == "fixed_state")
        del fixed["state"]
    elif defect == "empty_activation_condition":
        data["groups"][0]["activation_condition"] = " "
    elif defect == "duplicate_successor":
        data["targets"][0]["successors"].append(data["targets"][0]["successors"][0])
    else:
        data["targets"][0]["successors"].pop()
    path = tmp_path / "tools/data/targeted_operations.json"
    path.parent.mkdir(parents=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        json.dump(data, stream)
    with pytest.raises(ValueError):
        GENERATOR.load_manifest(tmp_path)


def test_facility_overrides_can_add_or_remove_known_objectives(manifest):
    data = deepcopy(manifest)
    political = next(
        group
        for group in data["groups"]
        if group["group_class"] == "political_executive"
    )
    political["facility_objectives"] = ["training"]
    assert GENERATOR.group_objective_mask(data, political) == 2


@pytest.mark.parametrize("missing", ["serving", "retirement"])
def test_registered_leaders_require_serving_and_retirement_bindings(
    tmp_path, manifest, missing
):
    manifest_path = tmp_path / "tools/data/targeted_operations.json"
    trigger_path = (
        tmp_path
        / "common/scripted_triggers/03_targeted_operations_political_roster.txt"
    )
    effect_path = (
        tmp_path / "common/scripted_effects/03_targeted_operations_political_roster.txt"
    )
    for path in (manifest_path, trigger_path, effect_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        json.dump(manifest, stream)
    trigger_text = (
        ROOT / "common/scripted_triggers/03_targeted_operations_political_roster.txt"
    ).read_text(encoding="utf-8")
    effect_text = (
        ROOT / "common/scripted_effects/03_targeted_operations_political_roster.txt"
    ).read_text(encoding="utf-8")
    if missing == "serving":
        trigger_text = trigger_text.replace(
            "TOP_person_129_serving = {", "TOP_person_129_unbound = {", 1
        )
    else:
        effect_text = effect_text.replace(
            "check_variable = { TOP_target = 129 }",
            "check_variable = { TOP_target = 999 }",
        )
    trigger_path.write_text(trigger_text, encoding="utf-8", newline="")
    effect_path.write_text(effect_text, encoding="utf-8", newline="")
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
    assert text.count("ai_will_do = { base = 0 }") == len(definitions)
    assert "add = 50 TOP_native_gate" not in text
    for token, kind, target in definitions:
        raid = _named_block(text, token)
        method = "1" if kind == "drone" else "2"
        visible = _named_block(raid, "visible")
        assert f"TOP_case_phase^{target} = 3" in visible
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
        success = _named_block(_named_block(raid, "success_factors"), "success")
        assert "TOP_native_success_bonus" in success
        assert "TOP_native_success_penalty" in success
        assert f"var:TOP_case_native_success_bonus^{target}" in success
        assert f"var:TOP_case_native_success_penalty^{target}" in success
        assert "weight = 1" in success
        assert "weight = -1" in success

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


@pytest.mark.parametrize("method", [1, 2])
def test_native_raid_map_icons_resolve_to_existing_sprites(method):
    icon = re.search(r"(?m)^\s*custom_map_icon\s*=\s*(\w+)", GENERATOR.raid(1, method))
    sprites = (ROOT / "interface/military_raids/MD_military_raids.gfx").read_text(
        encoding="utf-8-sig"
    )
    names = set(re.findall(r'name\s*=\s*"([^"]+)"', sprites))
    assert icon is not None
    assert icon.group(1) in names


@pytest.mark.parametrize("method", [1, 2])
def test_native_raid_experience_reaches_full_weight_on_the_engine_scale(method):
    raid = GENERATOR.raid(1, method)
    factors = _named_block(raid, "success_factors")
    success = _named_block(factors, "success")
    experience = _parse_race_script(_named_block(success, "experience"))["experience"]
    fields = {key: float(operand) for key, _, operand in experience}
    assert 0 < fields["reference"] <= 1
    assert fields["start_weight"] < fields["weight"]


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


def test_registry_emits_legacy_and_three_axis_person_and_organization_state(manifest):
    output = GENERATOR.render(manifest)
    registry = output["common/scripted_effects/01_targeted_operations_registry.txt"]
    assert "global.TOP_registry_capacity = 161" in registry
    for field in GENERATOR.GROUP_FIELDS:
        assert f"resize_array = {{ global.TOP_group_{field} = 38 }}" in registry
    for field in GENERATOR.ORG_COUNTRY_FIELDS:
        assert f"resize_array = {{ TOP_org_{field} = 38 }}" in registry
    generated = range(manifest["generated_start"], manifest["generated_end"])
    assert set(generated) == set(range(65, 129))
    for ident in generated:
        assert f"global.TOP_affiliation^{ident} =" in registry
        assert f"global.TOP_consequence_profile^{ident} = 1" in registry
    for field in GENERATOR.GLOBAL_FIELDS:
        assert f"resize_array = {{ global.TOP_{field} = 161 }}" in registry
    for field in GENERATOR.COUNTRY_FIELDS:
        assert f"resize_array = {{ TOP_{field} = 161 }}" in registry
    names = output["localisation/english/MD_targeted_operations_roster_l_english.yml"]
    for target in manifest["targets"]:
        ident = target["id"]
        assert f"TOP_person_{ident}: \"{target['name']}\"" in names
    assert {
        t["id"] for t in manifest["targets"] if t["target_class"] == "civilian"
    } == {141}
    assert "global.TOP_civilian^141 = 1" in registry
    for target in manifest["targets"]:
        ident = target["id"]
        political = int(target["target_class"] in {"official", "civilian"})
        assert f"global.TOP_political^{ident} = {political}" in registry
        assert (
            f"global.TOP_public_identity^{ident} = {int(target['public_identity'])}"
            in registry
        )
        assert (
            f"global.TOP_leader_role^{ident} = "
            f"{GENERATOR.LEADER_ROLE_IDS[target['leader_role']]}" in registry
        )
        assert (
            f"global.TOP_consequence_profile^{ident} = "
            f"{GENERATOR.CONSEQUENCE_PROFILE_IDS[target['consequence_profile']]}"
            in registry
        )
        if ident >= 129:
            assert f"TOP_authored_role_eligible_{ident} = yes" in registry
    for group in manifest["groups"]:
        ident = group["id"]
        assert (
            f"global.TOP_group_class^{ident} = "
            f"{GENERATOR.GROUP_CLASS_IDS[group['group_class']]}" in registry
        )
        assert (
            f"global.TOP_group_public_identity^{ident} = "
            f"{int(group['public_identity'])}" in registry
        )
        assert (
            f"global.TOP_group_facility_objectives^{ident} = "
            f"{GENERATOR.group_objective_mask(manifest, group)}" in registry
        )
        expected_ct = group.get("ct_id", -1)
        assert f"global.TOP_group_ct^{ident} = {expected_ct}" in registry
        activation = _named_block(registry, f"TOP_activate_group_{ident}")
        assert f"global.TOP_group_state^{ident} = TOP_activation_state" in activation
        assert f"global.TOP_group_host^{ident} = TOP_activation_host" in activation
    resize = _named_block(registry, "TOP_resize_country_arrays")
    assert "set_variable" not in resize
    assert "resize_array = { TOP_lead_report_clock = 161 }" in resize
    assert "resize_array = { TOP_org_lead_report_clock = 38 }" in resize
    successors = output["common/scripted_effects/01_targeted_operations_successors.txt"]
    assert "TOP_person_129" not in successors


def test_manifest_declares_classes_location_policy_and_2027_2032_roster(manifest):
    assert manifest["version"] == 4
    assert manifest["capacity"] == 161
    assert set(manifest["facility_objective_defaults"]) == set(
        GENERATOR.GROUP_CLASS_IDS
    )
    assert {
        group_class: GENERATOR.objective_mask(objectives)
        for group_class, objectives in manifest["facility_objective_defaults"].items()
    } == GENERATOR.FACILITY_OBJECTIVE_DEFAULTS
    assert all(
        {
            "target_class",
            "leader_role",
            "public_identity",
            "consequence_profile",
        }
        <= target.keys()
        for target in manifest["targets"]
    )
    assert all(
        "political" not in target and "civilian" not in target
        for target in manifest["targets"]
    )
    assert all(
        {"group_class", "location_policy"} <= group.keys()
        for group in manifest["groups"]
    )
    expected = {
        142: ("saad_bin_atef_al_awlaki", 2027, "militant", 2),
        143: ("abu_ubaydah_yusuf_al_anabi", 2027, "militant", 7),
        144: ("xi_jinping", 2027, "official", 25),
        145: ("sanaullah_ghafari", 2028, "militant", 22),
        146: ("kim_jong_un", 2028, "official", 26),
        147: ("min_aung_hlaing", 2028, "official", 27),
        148: ("iyad_ag_ghali", 2029, "militant", 23),
        149: ("jehad_serwan_mostafa", 2029, "militant", 6),
        150: ("recep_tayyip_erdogan", 2029, "official", 28),
        151: ("ibrahim_ahmed_mahmoud_al_qosi", 2030, "militant", 2),
        152: ("luiz_inacio_lula_da_silva", 2030, "official", 29),
        153: ("abdel_fattah_el_sisi", 2030, "official", 30),
        154: ("hamza_salih_bin_said_al_ghamdi", 2031, "militant", 1),
        155: ("abd_al_rahman_al_maghrebi", 2031, "militant", 1),
        156: ("prabowo_subianto", 2031, "official", 31),
        157: ("abdiqadir_mumin", 2032, "militant", 24),
        158: ("mohammed_bin_salman", 2032, "official", 32),
        159: ("benjamin_netanyahu", 2032, "official", 33),
    }
    actual = {
        target["id"]: (
            target["key"],
            target["activation_year"],
            target["target_class"],
            target["group"],
        )
        for target in manifest["targets"]
        if 142 <= target["id"] < 160
    }
    assert actual == expected
    maduro = next(target for target in manifest["targets"] if target["id"] == 160)
    assert (
        maduro["key"],
        maduro["activation_year"],
        maduro["target_class"],
        maduro["group"],
    ) == ("nicolas_maduro", 2026, "official", 34)
    assert maduro["historical_outcome"]["force_in_campaign"] is False
    assert "doj_absolute_resolve_2026" in maduro["sources"]
    groups = {group["key"]: group for group in manifest["groups"]}
    for key in ("isis_k", "jnim", "isis_somalia"):
        assert "ct_id" not in groups[key]
        assert groups[key]["group_class"] == "militant_network"
        assert groups[key]["public_identity"] is False
        assert groups[key]["location_policy"] == "group_hq"
    for key in (
        "iraq",
        "irgc",
        "irgc_command",
        "irgc_ground",
        "irgc_aerospace",
        "irgc_navy",
    ):
        assert groups[key]["group_class"] == "state_security"
        assert groups[key]["public_identity"] is True
        assert GENERATOR.group_objective_mask(manifest, groups[key]) == 7
    assert groups["tpusa"]["group_class"] == "civilian_organization"
    assert groups["tpusa"]["public_identity"] is True
    for group in manifest["groups"]:
        if 25 <= group["id"] <= 34:
            assert "ct_id" not in group
            assert group["group_class"] == "political_executive"
            assert group["public_identity"] is True
            assert group["location_policy"] == "country_capital"
            assert GENERATOR.group_objective_mask(manifest, group) == 5
    public_people = {
        target["id"] for target in manifest["targets"] if target["public_identity"]
    }
    assert set(range(56, 65)) | set(range(129, 142)) <= public_people
    assert set(range(135, 141)) <= public_people
    unbound_future_pool = {142, 143, 145, 148, 157}
    assert all(
        next(target for target in manifest["targets"] if target["id"] == ident)[
            "leader_role"
        ]
        == "none"
        for ident in unbound_future_pool
    )
    assert all(
        ident not in group.get("succession", [])
        for ident in unbound_future_pool
        for group in manifest["groups"]
    )


def test_future_windows_names_and_placement_are_generated_from_manifest(manifest):
    output = GENERATOR.render(manifest)
    registry = output["common/scripted_effects/01_targeted_operations_registry.txt"]
    dispatch = output["common/scripted_localisation/01_targeted_operations_names.txt"]
    for year in range(2027, 2033):
        assert f"TOP_open_windows_{year}" in registry
        assert f"name = TOP_modern_{year}_name" in dispatch
    capital_group = _named_block(registry, "TOP_choose_location_25")
    assert "CHI = { capital_scope =" in capital_group
    militant_group = _named_block(registry, "TOP_choose_location_22")
    assert "TOP_find_group_org" not in militant_group
    assert "AFG = { random_controlled_state =" in militant_group


def test_non_ct_organizations_activate_on_their_authored_windows(manifest):
    registry = GENERATOR.render(manifest)[
        "common/scripted_effects/01_targeted_operations_registry.txt"
    ]
    for group in manifest["groups"]:
        window = _named_block(registry, f"TOP_open_windows_{group['year']}")
        assert f"global.TOP_group_window^{group['id']} = 1" in window
        if "ct_id" not in group:
            assert f"global.TOP_group_created^{group['id']} = 1" in window


def test_stalker_organizations_sit_in_the_zone_and_wait_for_their_gate(manifest):
    groups = {group["key"]: group for group in manifest["groups"]}
    registry = GENERATOR.render(manifest)[
        "common/scripted_effects/01_targeted_operations_registry.txt"
    ]
    expected = {
        "stalker_monolith": (35, "STALKER_top_zone_organization_active = yes"),
        "stalker_artifact_smugglers": (
            36,
            "STALKER_top_zone_organization_active = yes",
        ),
        "stalker_sircaa": (37, "STALKER_top_sircaa_active = yes"),
    }
    for key, (ident, condition) in expected.items():
        group = groups[key]
        assert group["id"] == ident
        assert group["location_policy"] == "fixed_state"
        assert group["state"] == 698
        activation = _named_block(registry, f"TOP_activate_group_{ident}")
        assert condition in activation
        location = _named_block(registry, f"TOP_choose_location_{ident}")
        assert (
            "698 = { set_temp_variable = { ROOT.TOP_activation_state = THIS } }"
            in location
        )
        assert "random_controlled_state" not in location
    assert "STALKER_" not in _named_block(registry, "TOP_activate_group_1")
