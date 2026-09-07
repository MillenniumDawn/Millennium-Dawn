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
)
COUNTRY_FIELDS = (
    "legacy_report_pending",
    "known",
    "confidence",
    "lead_state",
    "lead_host",
    "lead_age",
    "assessment",
    "mandates",
    "attempts",
    "bda_due",
    "bda_result",
    "bda_method",
    "bda_state",
    "capture_exploited",
)
ROOT = Path(__file__).resolve().parents[2]


def block(name: str, lines: list[str]) -> str:
    return name + " = {\n" + "\n".join("\t" + line for line in lines) + "\n}\n"


def load_manifest(root: Path) -> dict:
    with (root / "tools/data/targeted_operations.json").open(
        encoding="utf-8"
    ) as stream:
        data = json.load(stream)
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
    group_ids = {group["id"] for group in data["groups"]}
    if (
        group_ids != set(range(1, max(group_ids) + 1))
        or len(group_ids) != len(data["groups"])
        or max(group_ids) < 12
    ):
        raise ValueError(
            "Organization identities must preserve slots 1-12 and append consecutive groups"
        )
    ct_ids = [group["ct_id"] for group in data["groups"] if group["ct_id"] >= 0]
    if len(set(ct_ids)) != len(ct_ids) or any(i > 14 for i in ct_ids):
        raise ValueError("Duplicate or out-of-range CT identity")
    if len({target["key"] for target in data["targets"]}) != len(ids):
        raise ValueError("Duplicate target key")
    for target in data["targets"]:
        if target["group"] not in group_ids or any(
            i not in ids for i in target["successors"]
        ):
            raise ValueError(f"Invalid affiliation or successor for {target['id']}")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", target["key"]):
            raise ValueError(f"Invalid target key for {target['id']}")
        if target["historical_outcome"].get("force_in_campaign") is not False:
            raise ValueError("Historical outcomes cannot force campaign removals")
        if not 2000 <= target["activation_year"] <= 2026:
            raise ValueError(f"Invalid authored opportunity year for {target['id']}")
        if not target["sources"]:
            raise ValueError(f"Missing authoring provenance for {target['id']}")
    affiliations = {t["id"]: t["group"] for t in data["targets"]}
    for group in data["groups"]:
        for successor in group.get("succession", []):
            if affiliations.get(successor) != group["id"]:
                raise ValueError("Office successor belongs to another organization")
    for target in data["targets"]:
        if any(affiliations[i] != target["group"] for i in target["successors"]):
            raise ValueError("Person successor belongs to another organization")
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
    for field in ("ct", "leader", "created", "destroyed", "window"):
        lines.append(
            f"resize_array = {{ global.TOP_group_{field} = {group_capacity} }}"
        )
    lines += [
        f"resize_array = {{ global.TOP_backlash = {group_capacity} }}",
        "set_variable = { global.TOP_clock = 0 }",
    ]
    for group in data["groups"]:
        lines.append(
            f"set_variable = {{ global.TOP_group_ct^{group['id']} = {group['ct_id']} }}"
        )
    for target in data["targets"]:
        ident = target["id"]
        lines.append(
            f"set_variable = {{ global.TOP_affiliation^{ident} = {target['group']} }}"
        )
        lines.append(
            f"set_variable = {{ global.TOP_political^{ident} = {int(target.get('political', ident >= 56))} }}"
        )
        if target.get("civilian", False):
            lines.append(f"set_variable = {{ global.TOP_civilian^{ident} = 1 }}")
    for ident in range(data["generated_start"], data["generated_end"]):
        group = (ident - data["generated_start"]) % 10 + 1
        lines.append(f"set_variable = {{ global.TOP_affiliation^{ident} = {group} }}")
    output = block("TOP_setup_registry", lines)
    output += "\n" + block(
        "TOP_resize_country_arrays",
        [f"resize_array = {{ TOP_{field} = {capacity} }}" for field in COUNTRY_FIELDS]
        + [
            f"resize_array = {{ TOP_archive_{field} = 128 }}"
            for field in ("target", "result", "method", "day", "state")
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
        lines = ["if = {", "\tlimit = { " + " ".join(conditions) + " }"]
        lines += [
            f"\tTOP_choose_location_{gid} = yes",
            "\tif = {",
            "\t\tlimit = { check_variable = { TOP_activation_state > 0 } }",
            "\t\tvar:TOP_activation_state = { set_temp_variable = { TOP_activation_host = controller } }",
        ]
        for target in (t for t in data["targets"] if t["group"] == gid):
            ident = target["id"]
            role_gate = (
                f" TOP_authored_role_eligible = {{ TARGET = {ident} }}"
                if ident >= 129
                else ""
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
        location = ["set_temp_variable = { TOP_activation_state = 0 }"]
        if group["ct_id"] >= 0:
            location += [
                f"set_temp_variable = {{ TOP_group = {gid} }}",
                "TOP_find_group_org = yes",
                "if = {",
                "\tlimit = { check_variable = { TOP_org_slot > -1 } check_variable = { global.active_terror_hq^TOP_org_slot > 0 } }",
                "\tvar:global.active_terror_hq^TOP_org_slot = {",
                "\t\tif = { limit = { controller = { exists = yes } } set_temp_variable = { TOP_activation_state = THIS } }",
                "\t}",
                "}",
            ]
        for host in dict.fromkeys(
            group.get("movement_hosts", [])
            + [group["host"]]
            + group.get("regional_hosts", [])
        ):
            location += [
                "if = {",
                f"\tlimit = {{ check_variable = {{ TOP_activation_state = 0 }} {host} = {{ exists = yes num_of_controlled_states > 0 }} }}",
                f"\t{host} = {{ random_controlled_state = {{ set_temp_variable = {{ TOP_activation_state = THIS }} }} }}",
                "}",
            ]
        output += "\n" + block(f"TOP_choose_location_{gid}", location)
    return output


def raid(ident: int, method: int) -> str:
    drone = method == 1
    kind = "drone" if drone else "capture"
    lines = [
        f"category = {'drone_strike_raids' if drone else 'special_forces_raids'}",
        f"days_to_prepare = {14 if drone else 28}",
        "days_re_enable = 30",
        "command_power = 20",
        "arrow = { type = line }",
        "allowed = { TOP_enabled = yes }",
        f"visible = {{ check_variable = {{ TOP_case_phase^{ident} = 2 }} check_variable = {{ TOP_case_method^{ident} = {method} }} }}",
        f"show_target = {{ TOP_native_authorized = {{ TARGET = {ident} METHOD = {method} }} }}",
        "available = {",
        f"\tTOP_native_authorized = {{ TARGET = {ident} METHOD = {method} }}",
    ]
    if not drone:
        lines.append("\thas_tech = special_forces_tech_1")
    lines += [
        "}",
        f"launchable = {{ TOP_native_authorized = {{ TARGET = {ident} METHOD = {method} }} }}",
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
            "\t\texperience = { weight = 0.3 start_weight = -0.2 reference = 1000 }"
            if drone
            else "\t\texperience = { weight = 0.5 start_weight = -0.25 reference = 0.75 }"
        ),
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
            f"\t\t\tTOP_native_result = {{ TARGET = {ident} METHOD = {method} TIER = {tier} }}",
            "\t\t}",
            "\t}",
        ]
    lines += [
        "}",
        f"ai_will_do = {{ base = 0 modifier = {{ add = 50 TOP_native_authorized = {{ TARGET = {ident} METHOD = {method} }} }} }}",
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
        if 16 <= target["id"] <= 28:
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
    for name, variable in (
        ("TOP_selected_name", "TOP_selected"),
        ("TOP_authorized_name", "TOP_authorized_target"),
        ("TOP_proposal_name", "TOP_proposal_target"),
        ("TOP_row_name", "v"),
        ("TOP_archive_name", "TOP_archive_target^v"),
        ("TOP_modern_2024_name", "TOP_modern_2024_target"),
        ("TOP_modern_2025_name", "TOP_modern_2025_target"),
        ("TOP_modern_2026_name", "TOP_modern_2026_target"),
    ):
        lines = [f"name = {name}"]
        lines += [
            f"text = {{ trigger = {{ check_variable = {{ {variable} = {ident} }} }} localization_key = TOP_person_{ident} }}"
            for ident in range(1, data["capacity"])
        ]
        lines.append("text = { localization_key = TOP_no_target }")
        output += block("defined_text", lines) + "\n"
    output += block(
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
    return output


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
