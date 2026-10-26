import copy
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest
from targeted_operations_helpers import (
    _named_block,
    _parse_race_script,
    mutate_manifest,
)

from tools.generators import generate_targeted_operations as GENERATOR

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def manifest():
    return GENERATOR.load_manifest(ROOT)


def test_existing_representations_resolve_to_shipped_files(manifest):
    for target in manifest["targets"]:
        for representation in target["existing_representations"]:
            assert (ROOT / representation["path"]).is_file(), (
                target["id"],
                representation["path"],
            )


@pytest.mark.parametrize("missing", ["serving", "retirement"])
def test_registered_leaders_require_serving_and_retirement_bindings(
    tmp_path, manifest, missing
):
    manifest_path = tmp_path / "tools/data/targeted_operations.json"
    trigger_path = (
        tmp_path / "common/scripted_triggers/01_targeted_operations_triggers.txt"
    )
    effect_path = (
        tmp_path
        / "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
    )
    for path in (manifest_path, trigger_path, effect_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        json.dump(manifest, stream)
    trigger_text = (
        ROOT / "common/scripted_triggers/01_targeted_operations_triggers.txt"
    ).read_text(encoding="utf-8")
    effect_text = (
        ROOT
        / "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
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
    with trigger_path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(trigger_text)
    with effect_path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(effect_text)
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


@pytest.mark.parametrize("method", [1, 2])
def test_native_raid_map_icons_resolve_to_existing_sprites(method):
    icon = re.search(r"(?m)^\s*custom_map_icon\s*=\s*(\w+)", GENERATOR.raid(1, method))
    sprite_path = ROOT / "interface/military_raids/MD_military_raids.gfx"
    if not sprite_path.exists() and not (ROOT / "interface").exists():
        pytest.skip("game content not checked out (sparse checkout)")
    sprites = sprite_path.read_text(encoding="utf-8-sig")
    names = set(re.findall(r'name\s*=\s*"([^"]+)"', sprites))
    assert icon is not None
    assert icon.group(1) in names


def test_generated_names_and_roles_have_english_localisation(manifest):
    output = GENERATOR.render(manifest)
    roster = output["localisation/english/MD_targeted_operations_roster_l_english.yml"]
    keys = set(re.findall(r"(?m)^ ([A-Za-z0-9_]+):", roster))
    for ident in range(1, manifest["capacity"]):
        assert {
            f"TOP_person_{ident}",
            f"raid_type_TOP_drone_{ident}",
            f"raid_type_TOP_capture_{ident}",
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


def test_every_later_window_year_is_opened_by_the_yearly_dispatch(manifest):
    yearly = (ROOT / "common/scripted_effects/00_yearly_effects.txt").read_text(
        encoding="utf-8"
    )
    years = {target["activation_year"] for target in manifest["targets"]} | {
        group["year"] for group in manifest["groups"]
    }
    missing = [
        year
        for year in sorted(years)
        if year > 2000 and f"TOP_open_windows_{year} = yes" not in yearly
    ]
    assert missing == []


REGISTRY_PATH = ROOT / "common/scripted_effects/01_targeted_operations_registry.txt"


MANIFEST_RELATIVE = Path("tools/data/targeted_operations.json")


def write_manifest(root: Path, data: dict) -> None:
    path = root / MANIFEST_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        json.dump(data, stream)


def test_checked_in_registry_matches_manifest() -> None:
    manifest = GENERATOR.load_manifest(ROOT)
    assert GENERATOR.render(manifest)[
        str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/")
    ] == REGISTRY_PATH.read_text(encoding="utf-8")


def test_authored_successor_requires_group_pool_even_without_successors(
    tmp_path: Path,
) -> None:
    manifest = copy.deepcopy(GENERATOR.load_manifest(ROOT))
    group = next(group for group in manifest["groups"] if group["id"] == 22)
    group["succession"] = []
    write_manifest(tmp_path, manifest)
    with pytest.raises(
        ValueError, match="Authored successor missing from group pool: 145"
    ):
        GENERATOR.load_manifest(tmp_path)


def test_authored_identity_keys_cannot_be_reassigned(tmp_path: Path) -> None:
    manifest = copy.deepcopy(GENERATOR.load_manifest(ROOT))
    manifest["targets"][0]["key"], manifest["targets"][1]["key"] = (
        manifest["targets"][1]["key"],
        manifest["targets"][0]["key"],
    )
    write_manifest(tmp_path, manifest)
    with pytest.raises(ValueError, match="retain their stable IDs"):
        GENERATOR.load_manifest(tmp_path)


def test_historical_outcome_cannot_force_a_campaign_removal(tmp_path: Path) -> None:
    manifest = copy.deepcopy(GENERATOR.load_manifest(ROOT))
    manifest["targets"][0]["historical_outcome"]["force_in_campaign"] = True
    write_manifest(tmp_path, manifest)
    with pytest.raises(ValueError, match="cannot force campaign removals"):
        GENERATOR.load_manifest(tmp_path)


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
        "activation_year",
        "missing_sources",
    ],
)
def test_manifest_rejects_invalid_identity_and_provenance(
    tmp_path: Path, defect: str
) -> None:
    data = copy.deepcopy(GENERATOR.load_manifest(ROOT))
    mutate_manifest(data, defect)

    write_manifest(tmp_path, data)
    with pytest.raises(ValueError):
        GENERATOR.load_manifest(tmp_path)


def test_facility_objectives_can_override_known_defaults() -> None:
    data = copy.deepcopy(GENERATOR.load_manifest(ROOT))
    group = next(
        group
        for group in data["groups"]
        if group["group_class"] == "political_executive"
    )
    group["facility_objectives"] = ["training"]
    assert GENERATOR.group_objective_mask(data, group) == 2


def test_check_reports_drift_without_rewriting_output(tmp_path: Path) -> None:
    write_manifest(tmp_path, GENERATOR.load_manifest(ROOT))
    for relative in (
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
    ):
        roster = tmp_path / relative
        roster.parent.mkdir(parents=True, exist_ok=True)
        with roster.open("w", encoding="utf-8", newline="") as stream:
            stream.write((ROOT / relative).read_text(encoding="utf-8"))
    output = tmp_path / "common/scripted_effects/01_targeted_operations_registry.txt"
    with output.open("w", encoding="utf-8", newline="") as stream:
        stream.write("stale\n")

    changed = GENERATOR.generate(tmp_path, check=True)
    assert "common/scripted_effects/01_targeted_operations_registry.txt" in changed
    assert output.read_text(encoding="utf-8") == "stale\n"
