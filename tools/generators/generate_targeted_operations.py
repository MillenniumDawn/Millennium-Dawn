"""Compile the authored target registry and identity-bound native raid definitions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

GLOBAL_FIELDS = (
    "status",
    "confirmed_dead",
    "state",
    "host",
    "custodian",
    "custody_state",
    "custody_actor",
    "custody_sequence",
    "affiliation",
    "political",
    "civilian",
    "security",
    "attempts",
    "removals",
    "first_outcome",
    "window",
    "office",
    "generated_used",
    "pressure",
    "public_identity",
    "leader_role",
    "consequence_profile",
)
COUNTRY_FIELDS = (
    "legacy_report_pending",
    "known",
    "confidence",
    "lead_state",
    "lead_host",
    "lead_age",
    "lead_report_clock",
    "assessment",
    "mandates",
    "attempts",
    "bda_due",
    "bda_result",
    "bda_method",
    "bda_state",
    "bda_token",
    "bda_archive_row",
    "bda_archive_token",
    "bda_identity",
    "capture_exploited",
    "exchange_country",
    "exchange_until",
    "identity_confidence",
    "location_confidence",
    "pattern_confidence",
    "identity_source",
    "location_source",
    "pattern_source",
    "lead_source",
    "history_cycle",
    "package_state",
    "collection_focus",
    "liaison_age",
    "liaison_reliability",
)
GROUP_FIELDS = (
    "ct",
    "leader",
    "created",
    "destroyed",
    "window",
    "class",
    "public_identity",
    "host",
    "state",
    "pressure",
    "disruption_type",
    "disruption_until",
    "facility_objectives",
    "fixed_state",
)
ORG_COUNTRY_FIELDS = (
    "known",
    "verification",
    "location",
    "activity",
    "verification_source",
    "location_source",
    "activity_source",
    "lead_source",
    "history_cycle",
    "lead_state",
    "lead_host",
    "lead_age",
    "lead_report_clock",
    "package_state",
    "collection_focus",
    "mandates",
    "liaison_age",
    "liaison_reliability",
)
ROOT = Path(__file__).resolve().parents[2]
TARGET_CLASSES = {"militant", "official", "civilian"}
GROUP_CLASS_IDS = {
    "militant_network": 1,
    "state_security": 2,
    "political_executive": 3,
    "civilian_organization": 4,
}
GROUP_CLASSES = set(GROUP_CLASS_IDS)
LOCATION_POLICIES = {"group_hq", "country_capital", "target_state", "fixed_state"}
CLASS_LOCATION_POLICIES = {
    "militant_network": {"group_hq", "fixed_state"},
    "state_security": {"country_capital", "target_state"},
    "political_executive": {"country_capital", "target_state"},
    "civilian_organization": {"country_capital", "target_state", "fixed_state"},
}
FACILITY_OBJECTIVE_BITS = {"command": 1, "training": 2, "funding": 4}
FACILITY_OBJECTIVE_DEFAULTS = {
    "militant_network": 7,
    "state_security": 7,
    "political_executive": 5,
    "civilian_organization": 5,
}
LEADER_ROLE_IDS = {
    "none": 0,
    "head_of_state": 1,
    "head_of_government": 2,
    "senior_political": 3,
    "state_security_official": 4,
    "civilian_public_figure": 5,
}
CONSEQUENCE_PROFILE_IDS = {
    "militant": 1,
    "state_security": 2,
    "political_leader": 3,
    "civilian_public": 4,
}
STABLE_GROUP_KEYS = (
    "aq",
    "aqap",
    "isi",
    "ttp",
    "boko",
    "shabaab",
    "aqim",
    "lra",
    "ji",
    "asg",
    "iraq",
    "irgc",
    "russian_executive",
    "belarus_presidency",
    "ukraine_presidency",
    "iran_supreme_office",
    "irgc_command",
    "irgc_ground",
    "irgc_aerospace",
    "irgc_navy",
    "tpusa",
    "isis_k",
    "jnim",
    "isis_somalia",
    "china_presidency",
    "north_korea_supreme_office",
    "myanmar_executive",
    "turkiye_presidency",
    "brazil_presidency",
    "egypt_presidency",
    "indonesia_presidency",
    "saudi_executive",
    "israel_premiership",
    "venezuela_presidency",
    "stalker_monolith",
    "stalker_artifact_smugglers",
    "stalker_sircaa",
)
STABLE_TARGET_KEYS = (
    "osama_bin_laden",
    "ayman_al_zawahiri",
    "khalid_sheikh_mohammed",
    "ramzi_bin_al_shibh",
    "mohammed_atef",
    "abu_faraj_al_libbi",
    "abu_yahya_al_libi",
    "atiyah_abd_al_rahman",
    "saif_al_adel",
    "abu_muhammad_al_masri",
    "anwar_al_awlaki",
    "nasir_al_wuhayshi",
    "qasim_al_raymi",
    "khalid_al_batarfi",
    "ibrahim_al_asiri",
    "abu_fatima_al_jaheishi",
    "turki_al_binali",
    "lavdrim_muhaxheri",
    "gulmurod_khalimov",
    "abdullah_ahmed_al_mashadani",
    "ahmed_khalal_al_juhayshi",
    "fares_reif_al_naima",
    "abu_ahmad_al_alwani",
    "abu_muhammad_al_shimali",
    "ayad_al_jumaili",
    "khairy_abed_mahmoud_al_taey",
    "abdul_wahid_khutnayer_ahmad",
    "abu_jihad_shishani",
    "abu_musab_al_zarqawi",
    "abu_ayyub_al_masri",
    "abu_omar_al_baghdadi",
    "abu_bakr_al_baghdadi",
    "abu_muhammad_al_adnani",
    "abu_omar_al_shishani",
    "abu_ibrahim_al_hashimi_al_qurashi",
    "abu_hafs_al_hashimi_al_qurashi",
    "nek_muhammad_wazir",
    "baitullah_mehsud",
    "hakimullah_mehsud",
    "maulana_fazlullah",
    "noor_wali_mehsud",
    "omar_khalid_khorasani",
    "abubakar_shekau",
    "abu_musab_al_barnawi",
    "ahmed_abdi_godane",
    "ahmed_diriye",
    "abdelmalek_droukdel",
    "mokhtar_belmokhtar",
    "abdelhamid_abu_zeid",
    "joseph_kony",
    "hambali",
    "noordin_mohammad_top",
    "dulmatin",
    "khadaffy_janjalani",
    "isnilon_hapilon",
    "saddam_hussein",
    "qusay_hussein",
    "uday_hussein",
    "abid_hamid_mahmud",
    "ali_hassan_al_majid",
    "izzat_ibrahim_al_douri",
    "hani_abd_al_latif_tilfah",
    "aziz_salih_al_numan",
    "qasem_soleimani",
    "vladimir_putin",
    "dmitry_medvedev",
    "alexander_lukashenko",
    "volodymyr_zelenskyy",
    "ali_khamenei",
    "mojtaba_khamenei",
    "mohammad_ali_jafari",
    "hossein_salami",
    "mohammad_pakpour",
    "esmail_qaani",
    "amir_ali_hajizadeh",
    "ali_fadavi",
    "charlie_kirk",
    "saad_bin_atef_al_awlaki",
    "abu_ubaydah_yusuf_al_anabi",
    "xi_jinping",
    "sanaullah_ghafari",
    "kim_jong_un",
    "min_aung_hlaing",
    "iyad_ag_ghali",
    "jehad_serwan_mostafa",
    "recep_tayyip_erdogan",
    "ibrahim_ahmed_mahmoud_al_qosi",
    "luiz_inacio_lula_da_silva",
    "abdel_fattah_el_sisi",
    "hamza_salih_bin_said_al_ghamdi",
    "abd_al_rahman_al_maghrebi",
    "prabowo_subianto",
    "abdiqadir_mumin",
    "mohammed_bin_salman",
    "benjamin_netanyahu",
    "nicolas_maduro",
)


def block(name: str, lines: list[str]) -> str:
    return name + " = {\n" + "\n".join("\t" + line for line in lines) + "\n}\n"


def objective_mask(objectives: object) -> int:
    if (
        not isinstance(objectives, list)
        or not objectives
        or len(objectives) != len(set(objectives))
        or any(objective not in FACILITY_OBJECTIVE_BITS for objective in objectives)
    ):
        raise ValueError(
            "Facility objectives must be a nonempty set of known objectives"
        )
    return sum(FACILITY_OBJECTIVE_BITS[objective] for objective in objectives)


def group_objective_mask(data: dict, group: dict) -> int:
    objectives = group.get(
        "facility_objectives",
        data["facility_objective_defaults"][group["group_class"]],
    )
    return objective_mask(objectives)


def load_manifest(root: Path) -> dict:
    with (root / "tools/data/targeted_operations.json").open(
        encoding="utf-8"
    ) as stream:
        data = json.load(stream)
    if data.get("version") != 4:
        raise ValueError("Targeted Operations manifest must use schema version 4")
    defaults = data.get("facility_objective_defaults")
    if not isinstance(defaults, dict) or set(defaults) != GROUP_CLASSES:
        raise ValueError("Facility objective defaults must cover every group class")
    for group_class, expected in FACILITY_OBJECTIVE_DEFAULTS.items():
        if objective_mask(defaults[group_class]) != expected:
            raise ValueError(f"Invalid facility objective default for {group_class}")

    ids = [target["id"] for target in data["targets"]]
    expected_ids = list(range(1, data["generated_start"])) + list(
        range(data["generated_end"], data["capacity"])
    )
    if ids != expected_ids:
        raise ValueError(
            "Authored IDs must preserve slots 1-64 and follow the reserved generated interval"
        )
    if not (
        data["generated_start"] == 65
        and data["generated_end"] == 129
        and data["generated_end"] <= data["capacity"] <= 838
    ):
        raise ValueError("Invalid registry capacity")
    if tuple(target["key"] for target in data["targets"]) != STABLE_TARGET_KEYS:
        raise ValueError("Authored person keys must retain their stable IDs")
    group_id_list = [group["id"] for group in data["groups"]]
    group_ids = set(group_id_list)
    if group_id_list != list(range(1, len(data["groups"]) + 1)):
        raise ValueError(
            "Organization identities must preserve slots 1-12 and append consecutive groups"
        )
    if tuple(group["key"] for group in data["groups"]) != STABLE_GROUP_KEYS:
        raise ValueError("Organization keys must retain their stable IDs")
    ct_ids = [group["ct_id"] for group in data["groups"] if "ct_id" in group]
    if any(type(ident) is not int or not 0 <= ident <= 14 for ident in ct_ids) or len(
        set(ct_ids)
    ) != len(ct_ids):
        raise ValueError("Duplicate or out-of-range CT identity")
    if len({target["key"] for target in data["targets"]}) != len(ids):
        raise ValueError("Duplicate target key")
    groups = {group["id"]: group for group in data["groups"]}
    for target in data["targets"]:
        if target["group"] not in group_ids or any(
            i not in ids for i in target["successors"]
        ):
            raise ValueError(f"Invalid affiliation or successor for {target['id']}")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", target["key"]):
            raise ValueError(f"Invalid target key for {target['id']}")
        if target.get("target_class") not in TARGET_CLASSES:
            raise ValueError(f"Invalid target class for {target['id']}")
        group = groups[target["group"]]
        group_class = group.get("group_class")
        allowed_group_classes = {
            "militant": {"militant_network"},
            "official": {"state_security", "political_executive"},
            "civilian": {"civilian_organization"},
        }[target["target_class"]]
        if group_class not in allowed_group_classes:
            raise ValueError(f"Target class does not match group for {target['id']}")
        if type(target.get("public_identity")) is not bool:
            raise ValueError(f"Invalid public identity for target {target['id']}")
        expected_public = target["target_class"] != "militant"
        if target["public_identity"] != expected_public:
            raise ValueError(
                f"Public identity does not match target class for {target['id']}"
            )
        leader_role = target.get("leader_role")
        if leader_role not in LEADER_ROLE_IDS:
            raise ValueError(f"Invalid leader role for target {target['id']}")
        consequence_profile = target.get("consequence_profile")
        if consequence_profile not in CONSEQUENCE_PROFILE_IDS:
            raise ValueError(f"Invalid consequence profile for target {target['id']}")
        expected_profile = {
            "militant_network": "militant",
            "state_security": "state_security",
            "political_executive": "political_leader",
            "civilian_organization": "civilian_public",
        }[group_class]
        if consequence_profile != expected_profile:
            raise ValueError(
                f"Consequence profile does not match group for {target['id']}"
            )
        role_eligibility = target.get("role_eligibility", {})
        eligibility_kind = role_eligibility.get("kind")
        political_roles = {"head_of_state", "head_of_government", "senior_political"}
        serving_roles = political_roles | {"state_security_official"}
        if leader_role in serving_roles:
            if (
                eligibility_kind != "serving_state_role"
                or not role_eligibility.get("office_keys")
                or role_eligibility.get("trigger")
                != f"TOP_authored_role_eligible = {{ TARGET = {target['id']} }}"
            ):
                raise ValueError(
                    f"Incomplete serving leader binding for {target['id']}"
                )
        if (
            leader_role == "civilian_public_figure"
            and eligibility_kind != "civilian_exception_only"
        ):
            raise ValueError(f"Incomplete civilian leader binding for {target['id']}")
        if eligibility_kind == "serving_state_role" and leader_role == "none":
            raise ValueError(f"Serving official lacks a leader role for {target['id']}")
        if (
            eligibility_kind == "civilian_exception_only"
            and leader_role != "civilian_public_figure"
        ):
            raise ValueError(
                f"Civilian exception lacks a leader role for {target['id']}"
            )
        if target["historical_outcome"].get("force_in_campaign") is not False:
            raise ValueError("Historical outcomes cannot force campaign removals")
        if not 2000 <= target["activation_year"] <= 2032:
            raise ValueError(f"Invalid authored opportunity year for {target['id']}")
        if not target["sources"]:
            raise ValueError(f"Missing authoring provenance for {target['id']}")
        if any(source not in data["sources"] for source in target["sources"]):
            raise ValueError(f"Unknown source for {target['id']}")
    for group in data["groups"]:
        if group.get("group_class") not in GROUP_CLASSES:
            raise ValueError(f"Invalid group class for {group['id']}")
        if group.get("location_policy") not in LOCATION_POLICIES:
            raise ValueError(f"Invalid location policy for {group['id']}")
        if (
            group["location_policy"]
            not in CLASS_LOCATION_POLICIES[group["group_class"]]
        ):
            raise ValueError(
                f"Location policy does not match class for group {group['id']}"
            )
        if group["location_policy"] == "fixed_state" and (
            type(group.get("state")) is not int or group["state"] < 1
        ):
            raise ValueError(f"Fixed-state group lacks a state: {group['id']}")
        if "activation_condition" in group and (
            type(group["activation_condition"]) is not str
            or not group["activation_condition"].strip()
        ):
            raise ValueError(f"Empty activation condition for group {group['id']}")
        if "ct_id" in group and group["group_class"] != "militant_network":
            raise ValueError(
                f"Only militant networks can use a CT identity: {group['id']}"
            )
        if type(group.get("public_identity")) is not bool:
            raise ValueError(f"Invalid public identity for group {group['id']}")
        expected_public = group["group_class"] != "militant_network"
        if group["public_identity"] != expected_public:
            raise ValueError(
                f"Public identity does not match class for group {group['id']}"
            )
        group_objective_mask(data, group)
        succession = group.get("succession", [])
        if len(succession) != len(set(succession)):
            raise ValueError(f"Duplicate successor for organization {group['id']}")
    affiliations = {t["id"]: t["group"] for t in data["targets"]}
    targets = {target["id"]: target for target in data["targets"]}
    for group in data["groups"]:
        for successor in group.get("succession", []):
            if affiliations.get(successor) != group["id"]:
                raise ValueError(
                    "Organization successor belongs to another organization"
                )
            if (
                targets[successor]["role_eligibility"].get("kind")
                != "authored_successor_pool"
            ):
                raise ValueError(
                    "Organization successor is not in an authored successor pool"
                )
            expected = [ident for ident in group["succession"] if ident != successor]
            if targets[successor]["successors"] != expected:
                raise ValueError(f"Incomplete successor binding for {successor}")
    for target in data["targets"]:
        if target["id"] in target["successors"] or len(target["successors"]) != len(
            set(target["successors"])
        ):
            raise ValueError(f"Duplicate or self successor for {target['id']}")
        if any(affiliations[i] != target["group"] for i in target["successors"]):
            raise ValueError("Person successor belongs to another organization")
        if target["successors"]:
            expected = [
                ident
                for ident in groups[target["group"]].get("succession", [])
                if ident != target["id"]
            ]
            if target["successors"] != expected:
                raise ValueError(f"Incomplete successor binding for {target['id']}")

    trigger_text = (
        root / "common/scripted_triggers/03_targeted_operations_political_roster.txt"
    ).read_text(encoding="utf-8")
    retirement_text = (
        root / "common/scripted_effects/03_targeted_operations_political_roster.txt"
    ).read_text(encoding="utf-8")
    for target in data["targets"]:
        if target["leader_role"] in {
            "head_of_state",
            "head_of_government",
            "senior_political",
            "state_security_official",
        }:
            ident = target["id"]
            if f"TOP_person_{ident}_serving = {{" not in trigger_text:
                raise ValueError(f"Missing serving trigger for leader {ident}")
            if f"check_variable = {{ TOP_target = {ident} }}" not in retirement_text:
                raise ValueError(f"Missing retirement handling for leader {ident}")
    return data


def registry(data: dict) -> str:
    capacity = data["capacity"]
    group_capacity = max(group["id"] for group in data["groups"]) + 1
    lines = [
        f"set_variable = {{ global.TOP_registry_capacity = {capacity} }}",
    ]
    lines += [
        f"resize_array = {{ global.TOP_{field} = {capacity} }}"
        for field in GLOBAL_FIELDS
    ]
    for field in GROUP_FIELDS:
        lines.append(
            f"resize_array = {{ global.TOP_group_{field} = {group_capacity} }}"
        )
    lines += [
        f"resize_array = {{ global.TOP_backlash = {group_capacity} }}",
        "set_variable = { global.TOP_clock = 0 }",
    ]
    for group in data["groups"]:
        gid = group["id"]
        lines += [
            f"set_variable = {{ global.TOP_group_ct^{gid} = {group.get('ct_id', -1)} }}",
            f"set_variable = {{ global.TOP_group_class^{gid} = {GROUP_CLASS_IDS[group['group_class']]} }}",
            f"set_variable = {{ global.TOP_group_public_identity^{gid} = {int(group['public_identity'])} }}",
            f"set_variable = {{ global.TOP_group_facility_objectives^{gid} = {group_objective_mask(data, group)} }}",
        ]
        if group["location_policy"] == "fixed_state":
            lines.append(f"set_variable = {{ global.TOP_group_fixed_state^{gid} = 1 }}")
    for target in data["targets"]:
        ident = target["id"]
        lines += [
            f"set_variable = {{ global.TOP_affiliation^{ident} = {target['group']} }}",
            f"set_variable = {{ global.TOP_political^{ident} = {int(target['target_class'] in {'official', 'civilian'})} }}",
            f"set_variable = {{ global.TOP_public_identity^{ident} = {int(target['public_identity'])} }}",
            f"set_variable = {{ global.TOP_leader_role^{ident} = {LEADER_ROLE_IDS[target['leader_role']]} }}",
            f"set_variable = {{ global.TOP_consequence_profile^{ident} = {CONSEQUENCE_PROFILE_IDS[target['consequence_profile']]} }}",
        ]
        if target["target_class"] == "civilian":
            lines.append(f"set_variable = {{ global.TOP_civilian^{ident} = 1 }}")
    for ident in range(data["generated_start"], data["generated_end"]):
        group = (ident - data["generated_start"]) % 10 + 1
        lines += [
            f"set_variable = {{ global.TOP_affiliation^{ident} = {group} }}",
            f"set_variable = {{ global.TOP_consequence_profile^{ident} = {CONSEQUENCE_PROFILE_IDS['militant']} }}",
        ]
    output = block("TOP_setup_registry", lines)
    output += "\n" + block(
        "TOP_resize_country_arrays",
        [f"resize_array = {{ TOP_{field} = {capacity} }}" for field in COUNTRY_FIELDS]
        + [
            f"resize_array = {{ TOP_org_{field} = {group_capacity} }}"
            for field in ORG_COUNTRY_FIELDS
        ]
        + [
            f"resize_array = {{ TOP_archive_{field} = 128 }}"
            for field in (
                "target",
                "result",
                "method",
                "day",
                "state",
                "disposition",
                "custody_token",
            )
        ],
    )
    years = sorted(
        {target["activation_year"] for target in data["targets"]}
        | {group["year"] for group in data["groups"]}
    )
    for year in years:
        output += "\n" + block(
            f"TOP_open_windows_{year}",
            [
                f"set_variable = {{ global.TOP_window^{t['id']} = 1 }}"
                for t in data["targets"]
                if t["activation_year"] == year
            ]
            + [
                f"set_variable = {{ global.TOP_group_window^{g['id']} = 1 }}"
                for g in data["groups"]
                if g["year"] == year
            ]
            + [
                f"set_variable = {{ global.TOP_group_created^{g['id']} = 1 }}"
                for g in data["groups"]
                if g["year"] == year
                and "ct_id" not in g
                and "activation_condition" not in g
            ],
        )
    output += "\n" + block(
        "TOP_open_start_windows",
        [
            f"if = {{ limit = {{ date > {year - 1}.12.31 }} TOP_open_windows_{year} = yes }}"
            for year in years
        ],
    )
    output += "\n" + block(
        "TOP_activate_candidates",
        ["TOP_prepare_authored_service = yes"]
        + [f"TOP_activate_group_{g['id']} = yes" for g in data["groups"]],
    )
    for group in data["groups"]:
        gid = group["id"]
        conditions = [
            f"check_variable = {{ global.TOP_group_destroyed^{gid} = 0 }}",
            f"check_variable = {{ global.TOP_group_window^{gid} = 1 }}",
        ]
        if gid == 3:
            conditions.append(
                "OR = { ISI = { exists = yes } has_global_flag = GLOBAL_operation_iraqi_freedom_succeeded IRQ = { has_war = yes } }"
            )
        if "activation_condition" in group:
            conditions.append(group["activation_condition"])
        lines = ["if = {", "\tlimit = { " + " ".join(conditions) + " }"]
        lines += [
            f"\tTOP_choose_location_{gid} = yes",
            "\tif = {",
            "\t\tlimit = { NOT = { check_variable = { TOP_activation_state = 0 } } }",
            "\t\tvar:TOP_activation_state = { set_temp_variable = { PREV.TOP_activation_host = controller } }",
            f"\t\tset_variable = {{ global.TOP_group_state^{gid} = TOP_activation_state }}",
            f"\t\tset_variable = {{ global.TOP_group_host^{gid} = TOP_activation_host }}",
        ]
        if "activation_condition" in group:
            lines.append(f"\t\tset_variable = {{ global.TOP_group_created^{gid} = 1 }}")
        for target in (t for t in data["targets"] if t["group"] == gid):
            ident = target["id"]
            role_gate = (
                f" TOP_authored_role_eligible_{ident} = yes" if ident >= 129 else ""
            )
            lines += [
                "\t\tif = {",
                f"\t\t\tlimit = {{ check_variable = {{ global.TOP_status^{ident} = 0 }} check_variable = {{ global.TOP_window^{ident} = 1 }}{role_gate} }}",
                f"\t\t\tset_variable = {{ global.TOP_status^{ident} = 1 }}",
                f"\t\t\tset_variable = {{ global.TOP_host^{ident} = TOP_activation_host }}",
                f"\t\t\tset_variable = {{ global.TOP_state^{ident} = TOP_activation_state }}",
                f"\t\t\tadd_to_array = {{ global.TOP_active_targets = {ident} }}",
                "\t\t}",
            ]
        lines += ["\t}", "}"]
        output += "\n" + block(f"TOP_activate_group_{gid}", lines)
        location = [
            "set_temp_variable = { TOP_activation_state = 0 }",
            "set_temp_variable = { TOP_activation_host = 0 }",
        ]
        if group["location_policy"] == "group_hq" and "ct_id" in group:
            location += [
                f"set_temp_variable = {{ TOP_group = {gid} }}",
                "TOP_find_group_org = yes",
                "if = {",
                "\tlimit = { check_variable = { TOP_org_slot > -1 } NOT = { check_variable = { global.active_terror_hq^TOP_org_slot = 0 } } }",
                "\tvar:global.active_terror_hq^TOP_org_slot = {",
                "\t\tif = { limit = { controller = { exists = yes } } set_temp_variable = { ROOT.TOP_activation_state = THIS } }",
                "\t}",
                "}",
            ]
        hosts = dict.fromkeys(
            group.get("movement_hosts", [])
            + [group["host"]]
            + group.get("regional_hosts", [])
        )
        if group["location_policy"] == "fixed_state":
            state = group["state"]
            location += [
                "if = {",
                f"	limit = {{ {state} = {{ controller = {{ exists = yes }} }} }}",
                f"	{state} = {{ set_temp_variable = {{ ROOT.TOP_activation_state = THIS }} }}",
                "}",
            ]
            hosts = {}
        for host in hosts:
            if group["location_policy"] == "country_capital":
                location += [
                    "if = {",
                    f"\tlimit = {{ check_variable = {{ TOP_activation_state = 0 }} {host} = {{ exists = yes num_of_controlled_states > 0 }} }}",
                    f"\t{host} = {{ capital_scope = {{ if = {{ limit = {{ controller = {{ exists = yes }} }} set_temp_variable = {{ ROOT.TOP_activation_state = THIS }} }} }} }}",
                    "}",
                ]
                continue
            location += [
                "if = {",
                f"\tlimit = {{ check_variable = {{ TOP_activation_state = 0 }} {host} = {{ exists = yes num_of_controlled_states > 0 }} }}",
                f"\t{host} = {{ random_controlled_state = {{ set_temp_variable = {{ ROOT.TOP_activation_state = THIS }} }} }}",
                "}",
            ]
        output += "\n" + block(f"TOP_choose_location_{gid}", location)
    return output


def raid(ident: int, method: int) -> str:
    drone = method == 1
    kind = "drone" if drone else "capture"
    lines = [
        f"category = {'drone_strike_raids' if drone else 'special_forces_raids'}",
        (
            "custom_map_icon = GFX_raid_type_icon_targeted_drone_strike"
            if drone
            else "custom_map_icon = GFX_raid_type_icon_direct_action_raid_supply"
        ),
        f"days_to_prepare = {14 if drone else 28}",
        "days_re_enable = 30",
        "command_power = 20",
        "arrow = { type = line }",
        "allowed = { TOP_enabled = yes }",
        f"visible = {{ check_variable = {{ TOP_case_phase^{ident} = 3 }} check_variable = {{ TOP_case_method^{ident} = {method} }} }}",
        f"show_target = {{ TOP_native_gate_{ident}_{method} = yes }}",
        "available = {",
        f"\tTOP_native_gate_{ident}_{method} = yes",
    ]
    if not drone:
        lines.append("\thas_tech = special_forces_tech_1")
    lines += [
        "}",
        f"launchable = {{ TOP_native_gate_{ident}_{method} = yes }}",
        "target_type = { state = { always = yes } }",
        "unit_requirements = {",
    ]
    lines += [
        (
            "\tequipment = { type = { small_plane_suicide_airframe cv_small_plane_suicide_airframe } amount = { min = 1 } }"
            if drone
            else "\tbattalion_types = { Special_Forces = { min = 2 } }"
        )
    ]
    lines += [
        "}",
        "launch_sound = raid_launch_marine",
        "target_icon = GFX_other_target_icon",
        (
            "starting_point = { types = { air_base } }"
            if drone
            else "starting_point = { types = { air_base naval_base } }"
        ),
        "success_factors = {",
        "\tsuccess = {",
        f"\t\tbase = {0.15 if drone else 0.25}",
        "\t\tintel = { weight = 0.5 start_weight = -0.1 start_reference = 10 reference = 100 }",
        (
            "\t\texperience = { weight = 0.3 start_weight = -0.2 reference = 1 }"
            if drone
            else "\t\texperience = { weight = 0.5 start_weight = -0.25 reference = 0.75 }"
        ),
        "\t\tTOP_native_success_bonus = {",
        "\t\t\tscope = country",
        f"\t\t\tformula = {{ base = 1 modifier = {{ factor = var:TOP_case_native_success_bonus^{ident} }} }}",
        "\t\t\tweight = 1",
        "\t\t\treference = 100",
        "\t\t\tcan_actor_affect = no",
        "\t\t\tcan_target_affect = no",
        "\t\t}",
        "\t\tTOP_native_success_penalty = {",
        "\t\t\tscope = country",
        f"\t\t\tformula = {{ base = 1 modifier = {{ factor = var:TOP_case_native_success_penalty^{ident} }} }}",
        "\t\t\tweight = -1",
        "\t\t\treference = 100",
        "\t\t\tcan_actor_affect = no",
        "\t\t\tcan_target_affect = no",
        "\t\t}",
    ]
    if drone:
        lines += [
            "\t\tair_agility = { reference = 200 weight = 0.5 start_weight = -0.5 }",
            "\t\treliability = { reference = 1 weight = 0.2 start_weight = -0.1 }",
            "\t\tanti_air = { reference = 5 weight = -0.25 }",
            "\t\tradar = { reference = 1 weight = -0.15 }",
        ]
    else:
        lines += [
            "\t\torganisation = { reference = 100 weight = 0.2 start_weight = -0.1 }",
            "\t\tstrength = { reference = 1 weight = 0.15 start_weight = -0.05 }",
        ]
    lines += [
        "\t}",
        "\tcritical = { base = 0.05 }",
        "\tdisaster = { base = 0.05 }",
        "}",
        "success_levels = {",
    ]
    for tier, name in enumerate(
        ("failure", "limited_success", "success", "critical_success")
    ):
        lines += [
            f"\t{name} = {{",
            "\t\tactor_effects = {",
            f"\t\t\tset_temp_variable = {{ TOP_target = {ident} }}",
            f"\t\t\tset_temp_variable = {{ TOP_method = {method} }}",
            f"\t\t\tset_temp_variable = {{ TOP_tier = {tier} }}",
            "\t\t\tTOP_native_result_args = yes",
            "\t\t}",
            "\t}",
        ]
    lines += [
        "}",
        "ai_will_do = { base = 0 }",
    ]
    return block(f"TOP_{kind}_{ident}", lines)


def names(data: dict) -> dict[str, str]:
    result = {str(t["id"]): t["name"] for t in data["targets"]}
    roots = ["Kamal", "Yusuf", "Farid", "Salim", "Nabil", "Hamid", "Musa"]
    regional = {
        4: ["Rahim Khan", "Daud Wazir", "Karim Shah", "Rafiq Khan"],
        5: ["Musa Umar", "Sani Bello", "Ibrahim Yusuf", "Ali Garba"],
        6: ["Yusuf Hassan", "Mahad Ali", "Abdi Mahmud", "Omar Farah"],
        8: ["Ojok Okello", "Otim Ocen", "Ochan Ouma", "Oryem Otim"],
        9: ["Rizal Pratama", "Arif Santoso", "Dimas Yusuf", "Fajar Rahman"],
        10: ["Amir Sulaiman", "Karim Usman", "Rashid Hassan", "Faisal Ali"],
    }
    for ident in range(data["generated_start"], data["generated_end"]):
        ordinal = ident - data["generated_start"]
        pool = regional.get(ordinal % 10 + 1, roots)
        result[str(ident)] = (
            f"{pool[(ordinal // 10) % len(pool)]} (Successor {ordinal + 1})"
        )
    return result


def localisation(data: dict) -> str:
    lines = ["l_english:"]
    for ident, name in names(data).items():
        lines += [
            f' TOP_person_{ident}: "{name}"',
            f' TOP_drone_{ident}: "Remote Strike: {name}"',
            f' TOP_drone_{ident}_desc: "Conduct the authorized native map operation against this target package."',
            f' TOP_capture_{ident}: "Capture Raid: {name}"',
            f' TOP_capture_{ident}_desc: "Attempt to secure this target alive through a native special-forces raid."',
        ]
    for target in data["targets"]:
        lines.append(
            f' TOP_person_{target["id"]}_role: "{target["role"].replace("_", " ").title()}"'
        )
        if target.get("legacy_isi_id") is not None:
            ident, name = target["id"], target["name"]
            lines += [
                f' TOP_legacy_person_{ident}_dead_t: "Death of {name} Confirmed"',
                f' TOP_legacy_person_{ident}_dead_d: "The death of Islamic State figure {name} has been confirmed following a targeted operation. The organization must replace the lost experience and contacts while adapting to the disruption."',
                f' TOP_legacy_person_{ident}_captured_t: "{name} Detained"',
                f' TOP_legacy_person_{ident}_captured_d: "Islamic State figure {name} has been taken into custody. Intelligence assessment and detention arrangements are continuing as the organization adapts to the loss of a senior member."',
            ]
    lines += [
        ' TOP_legacy_bin_laden_captured_t: "Osama bin Laden Detained"',
        ' TOP_legacy_bin_laden_captured_d: "Osama bin Laden has been taken into custody. His detention removes the leader of al-Qaeda from its active network and opens a new phase of intelligence assessment and decisions over his custody."',
        ' TOP_legacy_bin_laden_dead_d: "The death of Osama bin Laden has been confirmed following a targeted operation. Al-Qaeda has lost its leader, but surviving networks and potential successors remain active."',
        ' TOP_legacy_saddam_captured_d: "Saddam Hussein has been taken into custody. His detention counts toward the hunt for Iraqi fugitives, while any prosecution or sentence requires him to remain securely detained."',
        ' TOP_legacy_soleimani_dead_d: "The death of Qasem Soleimani has been confirmed following a targeted operation. Iran and other regional governments are considering their responses, with consequences depending on the campaign and the authority behind the operation."',
    ]
    lines += [
        ' TOP_political_authority: "Exceptional Political Authority"',
        ' TOP_political_authority_desc: "Serving officials require exceptional authority before an operation can enter review. Civilian political figures require an explicit mandate from an authored campaign crisis."',
        ' TOP_civilian_emergency_case: "Extend the Emergency Mandate"',
        ' TOP_civilian_emergency_case_desc: "An authoritarian government facing civil war in the United States, or fighting a war against the United States, may use its political crisis to extend a coercive mandate to civilian activist Charlie Kirk. The case remains subject to senior review. A domestic mandate permits an exceptional lethal review only while the civil war and political crisis continue. The decision reduces Stability and War Support."',
    ]
    for group in data["groups"]:
        lines.append(f' TOP_group_{group["id"]}: "{group["name"]}"')
    return "\n".join(lines) + "\n"


def dispatch(data: dict) -> str:
    output = ""
    selectors = [
        ("TOP_selected_name", "TOP_selected"),
        ("TOP_person_row_name", "v"),
        ("TOP_open_visit_name", "TOP_open_visit_target"),
    ]
    latest_year = max(target["activation_year"] for target in data["targets"])
    selectors += [
        (f"TOP_modern_{year}_name", f"TOP_modern_{year}_target")
        for year in range(2024, latest_year + 1)
    ]
    for name, variable in selectors:
        lines = [f"name = {name}"]
        lines += [
            f"text = {{ trigger = {{ check_variable = {{ {variable} = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        lines.append("text = { localization_key = TOP_no_target }")
        output += block("defined_text", lines) + "\n"
    output += block(
        "defined_text",
        ["name = TOP_selected_organization_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_selected_organization = {group['id']} }} }} localization_key = TOP_group_{group['id']} }}"
            for group in data["groups"]
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_organization_row_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ v = {group['id']} }} }} localization_key = TOP_group_{group['id']} }}"
            for group in data["groups"]
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_proposal_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_proposal_subject_kind = 2 }} check_variable = {{ TOP_proposal_subject_id = {group['id']} }} }} localization_key = TOP_group_{group['id']} }}"
            for group in data["groups"]
        ]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_proposal_subject_kind = 1 }} check_variable = {{ TOP_proposal_target = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_archive_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_archive_subject_kind^v = 2 }} check_variable = {{ TOP_archive_subject_id^v = {group['id']} }} }} localization_key = TOP_group_{group['id']} }}"
            for group in data["groups"]
        ]
        + [
            f"text = {{ trigger = {{ NOT = {{ check_variable = {{ TOP_archive_subject_kind^v = 2 }} }} check_variable = {{ TOP_archive_subject_id^v = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_incoming_subject_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_incoming_subject_kind = 2 }} check_variable = {{ TOP_incoming_subject_id = {group['id']} }} }} localization_key = TOP_group_{group['id']} }}"
            for group in data["groups"]
        ]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_incoming_subject_kind = 1 }} check_variable = {{ TOP_incoming_subject_id = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_report_subject_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_report_subject_kind = 2 }} check_variable = {{ TOP_report_subject_id = {group['id']} }} }} localization_key = TOP_group_{group['id']} }}"
            for group in data["groups"]
        ]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_report_subject_kind = 1 }} check_variable = {{ TOP_report_subject_id = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_incoming_liaison_subject_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_incoming_liaison_kind = 2 }} check_variable = {{ TOP_incoming_liaison_id = {group['id']} }} }} localization_key = TOP_group_{group['id']} }}"
            for group in data["groups"]
        ]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_incoming_liaison_kind = 1 }} check_variable = {{ TOP_incoming_liaison_id = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_custody_event_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_custody_event_target = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_bda_notice_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_bda_notice_target = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_selected_group"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ global.TOP_affiliation^TOP_selected = {g['id']} }} }} localization_key = TOP_group_{g['id']} }}"
            for g in data["groups"]
        ]
        + ["text = { localization_key = TOP_no_target }"],
    )
    output += "\n" + block(
        "defined_text",
        [
            "name = TOP_selected_role",
            "text = { trigger = { check_variable = { global.TOP_office^TOP_selected = 1 } } localization_key = TOP_role_leader }",
        ]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_selected = {t['id']} }} }} localization_key = TOP_person_{t['id']}_role }}"
            for t in data["targets"]
        ]
        + ["text = { localization_key = TOP_role_successor }"],
    )
    output += "\n" + block(
        "defined_text",
        ["name = TOP_proposal_role_name"]
        + [
            f"text = {{ trigger = {{ check_variable = {{ TOP_proposal_target = {target['id']} }} }} localization_key = TOP_person_{target['id']}_role }}"
            for target in data["targets"]
        ]
        + ["text = { localization_key = TOP_role_successor }"],
    )
    return output


def native_gates(data: dict) -> str:
    """One concrete gate per raid.

    A raid cannot call TOP_native_authorized with parameters: common/raids/ is
    parsed before the scripted trigger files register, and the engine does not
    substitute $PARAM$ for a trigger in any case. Each gate sets the temp
    variables the trigger reads and is called as a plain `= yes`.
    """
    blocks = []
    for ident in range(1, data["capacity"]):
        for method in (1, 2):
            blocks.append(
                "\n".join(
                    [
                        f"TOP_native_gate_{ident}_{method} = {{",
                        f"\tset_temp_variable = {{ TOP_arg_target = {ident} }}",
                        f"\tset_temp_variable = {{ TOP_arg_method = {method} }}",
                        "\tTOP_native_authorized = yes",
                        "}",
                    ]
                )
            )
    header = (
        "# Generated by tools/generators/generate_targeted_operations.py.\n"
        "# One gate per raid; see native_gates() for why raids cannot call the\n"
        "# parameterised trigger directly.\n\n"
    )
    return header + "\n\n".join(blocks) + "\n"


def render(data: dict) -> dict[str, str]:
    raids = (
        "types = {\n"
        + "\n".join(
            "\n".join("\t" + line for line in raid(ident, method).splitlines())
            for ident in range(1, data["capacity"])
            for method in (1, 2)
        )
        + "\n}\n"
    )
    return {
        "common/scripted_effects/01_targeted_operations_registry.txt": registry(data),
        "common/scripted_effects/01_targeted_operations_successors.txt": successors(
            data
        ),
        "common/raids/targeted_operations_raids.txt": raids,
        "common/scripted_triggers/06_targeted_operations_native_gates.txt": native_gates(
            data
        ),
        "common/scripted_localisation/01_targeted_operations_names.txt": dispatch(data),
        "localisation/english/MD_targeted_operations_roster_l_english.yml": localisation(
            data
        ),
    }


def successors(data: dict) -> str:
    lines = ["set_temp_variable = { TOP_candidate = 0 }"]
    for group in data["groups"]:
        for ident in group.get("succession", []):
            lines.append(
                f"if = {{ limit = {{ check_variable = {{ TOP_group = {group['id']} }} check_variable = {{ TOP_candidate = 0 }} check_variable = {{ global.TOP_status^{ident} = 1 }} }} set_temp_variable = {{ TOP_candidate = {ident} }} }}"
            )
    output = block("TOP_select_authored_successor", lines)
    installations, retirements = [], []
    people = names(data)
    movement_tags = {2: "AQY", 3: "ISI", 4: "TTP", 6: "SHB"}
    for ident in range(data["generated_start"], data["generated_end"]):
        group = (ident - data["generated_start"]) % 10 + 1
        tag = movement_tags.get(group)
        if tag:
            name = people[str(ident)]
            installations += [
                "if = {",
                f"\tlimit = {{ check_variable = {{ TOP_target = {ident} }} check_variable = {{ global.TOP_status^{ident} = 1 }} }}",
                f"\t{tag} = {{",
                "\t\tif = {",
                f'\t\t\tlimit = {{ exists = yes has_government = fascism NOT = {{ has_country_leader = {{ name = "{name}" ruling_only = yes }} }} }}',
                f'\t\t\tcreate_country_leader = {{ name = "{name}" picture = "gfx/interface/scripted_gui/countries/IRQ/card_unknown.dds" ideology = Caliphate traits = {{ salafist_Caliphate }} }}',
                f"\t\t\tset_variable = {{ Caliphate_leader = {1000 + ident} }}",
                "\t\t}",
                "\t}",
                "}",
            ]
            retirements.append(
                f'if = {{ limit = {{ check_variable = {{ TOP_target = {ident} }} }} {tag} = {{ if = {{ limit = {{ has_country_leader = {{ name = "{name}" ruling_only = yes }} }} kill_country_leader = yes }} }} }}'
            )
    output += "\n" + block("TOP_install_generated_office", installations)
    output += "\n" + block("TOP_retire_generated_office", retirements)
    return output


def generate(root: Path, check: bool = False) -> list[str]:
    changed = []
    for relative, content in render(load_manifest(root)).items():
        path = root / relative
        encoding = "utf-8-sig" if path.suffix == ".yml" else "utf-8"
        current = None
        if path.exists():
            with path.open(encoding=encoding, newline="") as stream:
                current = stream.read()
        if current != content:
            changed.append(relative)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("w", encoding=encoding, newline="") as stream:
                    stream.write(content)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = generate(args.root, args.check)
    if args.check and changed:
        print("Generated target definitions are stale: " + ", ".join(changed))
        return 1
    print(
        f"Target registry: {len(changed)} generated files {'differ' if args.check else 'updated'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
