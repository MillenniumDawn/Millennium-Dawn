"""Shared manifest mutations for TOP generator contract checks."""


def mutate_manifest(data: dict, defect: str) -> None:
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
        data["facility_objective_defaults"]["state_security"] = ["command", "funding"]
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
    elif defect == "duplicate_successor":
        data["targets"][0]["successors"].append(data["targets"][0]["successors"][0])
    elif defect == "incomplete_successor":
        data["targets"][0]["successors"].pop()
    elif defect == "missing_authored_pool":
        next(group for group in data["groups"] if group["id"] == 22)["succession"] = []
    elif defect == "activation_year":
        data["targets"][0]["activation_year"] = 1999
    elif defect == "missing_sources":
        data["targets"][0]["sources"] = []
    else:
        raise ValueError(f"Unknown manifest defect: {defect}")
