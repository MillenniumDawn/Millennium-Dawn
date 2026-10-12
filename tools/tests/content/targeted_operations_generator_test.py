import importlib.util
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest
from targeted_operations_model_test import _named_block, _parse_race_script

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "targeted_operations_generator",
    ROOT / "tools/generators/generate_targeted_operations.py",
)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


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
