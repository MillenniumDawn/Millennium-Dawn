"""Tool-side lists, exemptions, and contracts checked against the live game tree."""

import re

import pytest
import validate_building_guards
import validate_decisions
import validate_dlc_guards
import validate_influence_calls
import validate_scripted_params
from shared.paths import REPO_ROOT
from shared_utils import PARTY_SLOT_NAMES
from standardize_api import standardize_text
from validate_focus_tree import _PP_MALUS_EXEMPT_FOCUS_IDS
from validate_modifiers import _harvest_doctrine_folder_cost_factors
from validate_tech_categories import _LEGACY_CATEGORIES, load_known_categories

from tools.publishing import publish_workshop as pw

_BUDGET = "common/scripted_effects/00_budget_effects.txt"
_POLITICS = "common/scripted_effects/00_MD_politicsview_scripted_effects.txt"


def test_party_indices_match_the_runtime_party_localisation():
    source = (
        REPO_ROOT / "common/scripted_localisation/01_politics_scripted_localisation.txt"
    )
    text = source.read_text(encoding="utf-8")
    pairs = re.findall(
        r"party_index\s*=\s*(\d+).*?localization_key\s*=\s*"
        r'"\[([A-Za-z0-9_-]+)_L\]"',
        text,
        re.S,
    )
    runtime_names = {int(slot): name for slot, name in pairs}

    assert len(pairs) == 24
    assert runtime_names == PARTY_SLOT_NAMES


def test_real_frontend_files_match_the_fixed_production_locale_contract():
    localisation = REPO_ROOT / "localisation"
    frontends = pw.frontend_loc_files(REPO_ROOT)
    assert set(localisation.glob("*/MD_frontend_l_*.yml")) == set(frontends)

    for path in sorted(frontends):
        rel = path.relative_to(REPO_ROOT).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for key in pw.VERSION_LOC_KEYS:
            matches = [line for line in lines if line.split(":", 1)[0].strip() == key]
            assert len(matches) == 1, f"{rel}: expected exactly one {key}"
            assert (
                len(pw.VERSION_TOKEN.findall(matches[0])) == 1
            ), f"{rel}: {key} must have exactly one complete version token"
            banner = pw.BANNER_VERSION.search(matches[0])
            assert (
                banner and banner["marker"]
            ), f"{rel}: {key} must follow its version with a dev marker"


def test_province_building_list_covers_every_province_max_building():
    """`_PROVINCE_BUILDINGS` is a hand-kept mirror of the buildings that carry a
    province_max level cap; this fails when a new one is added to the game."""
    text = (REPO_ROOT / "common" / "buildings" / "00_buildings.txt").read_text(
        encoding="utf-8-sig"
    )
    declared = set()
    building = None
    for line in text.splitlines():
        match = re.match(r"^\t([A-Za-z_][A-Za-z0-9_]*) = \{", line)
        if match:
            building = match.group(1)
        elif building and re.search(r"\bprovince_max\s*=", line):
            declared.add(building)
    assert declared
    assert declared <= validate_building_guards._PROVINCE_BUILDINGS


def _focus_ids_with_pp_malus():
    """Focus ids in the real tree that still carry a literal negative
    add_political_power, found by walking back to the nearest preceding id."""
    id_or_malus = re.compile(
        r"^\s*(?:id\s*=\s*(\S+)|(add_political_power\s*=\s*-\d))", re.MULTILINE
    )
    found = set()
    for path in sorted((REPO_ROOT / "common" / "national_focus").glob("*.txt")):
        current = None
        for m in id_or_malus.finditer(
            path.read_text(encoding="utf-8-sig", errors="replace")
        ):
            if m.group(1):
                current = m.group(1)
            elif current:
                found.add(current)
    return found


def test_pp_malus_exemptions_are_still_live():
    stale = sorted(_PP_MALUS_EXEMPT_FOCUS_IDS - _focus_ids_with_pp_malus())
    assert not stale, (
        "_PP_MALUS_EXEMPT_FOCUS_IDS names focuses that no longer apply a PP "
        f"malus: {stale}. Remove them from the exemption set."
    )


def test_spain_focus_tree_is_clean():
    path = REPO_ROOT / "common" / "national_focus" / "05_spain.txt"
    raw = path.read_text(encoding="utf-8")
    setter = "set_temp_variable = { influence_target = THIS }"
    assert raw.count(setter) == 6
    assert validate_influence_calls.scan_file((str(path), str(REPO_ROOT))) == []
    assert len(validate_influence_calls.scan_text(raw.replace(setter, ""))) == 6


@pytest.mark.parametrize(
    "rel, effect, required, optional",
    [
        (_BUDGET, "modify_treasury_effect", ["treasury_change"], []),
        (_BUDGET, "modify_debt_effect", ["debt_change"], []),
        (
            _BUDGET,
            "modify_international_investment_effect",
            ["int_investment_change"],
            [],
        ),
        (
            _POLITICS,
            "change_relative_party_popularity",
            [],
            ["party_index", "party_popularity_increase", "temp_outlook_increase"],
        ),
    ],
)
def test_game_file_still_declares_the_contract(rel, effect, required, optional):
    # the contract is a comment block, so a stray edit can switch the check off
    contracts = validate_scripted_params._parse_effect_contracts_from_file(
        str(REPO_ROOT / rel)
    )
    assert contracts[effect] == {"required": required, "optional": optional}


def test_legacy_table_targets_exist_and_keys_do_not():
    known = load_known_categories(
        sorted((REPO_ROOT / "common" / "technology_tags").glob("*.txt"))
    )
    known_lower = {k.lower() for k in known}
    assert set(_LEGACY_CATEGORIES.values()) <= known
    assert not set(_LEGACY_CATEGORIES) & known_lower


def test_unannounced_category_exemptions_are_still_live():
    names = set(validate_decisions.parse_decision_categories(str(REPO_ROOT)))
    stale = sorted(validate_decisions._UNANNOUNCED_CATEGORY_EXEMPT - names)
    assert not stale, (
        "unannounced_category_exempt names categories that no longer exist: "
        f"{stale}. Remove them from validation_config.json."
    )


def test_poland_logistics_focus_uses_the_matching_aircraft_tree():
    guards = validate_dlc_guards
    mod_path = f"{REPO_ROOT}/"
    folder_gates = guards.parse_folder_gates(mod_path)
    project_gates = guards.parse_project_gates(mod_path)
    tech_gates, category_gates, project_tech_gates = guards.parse_tech_gates(
        mod_path, folder_gates, project_gates
    )
    path = REPO_ROOT / "common" / "national_focus" / "05_poland.txt"
    scanner = guards.Scanner(
        guards._sanitize(path.read_text(encoding="utf-8-sig")),
        tech_gates,
        category_gates,
        project_gates,
        project_tech_gates,
        guards._AVAILABILITY,
    )
    scanner.walk(0, len(scanner.text), guards.Context())
    assert scanner.findings == []


def _tech_ids(text):
    ids = []
    depth = 0
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        match = re.match(r"\s*(\w+)\s*=\s*\{", code)
        if match and depth == 1:
            ids.append(match.group(1))
        depth += code.count("{") - code.count("}")
    return ids


@pytest.mark.parametrize(
    "path",
    sorted((REPO_ROOT / "common" / "technologies").glob("*.txt")),
    ids=lambda p: p.name,
)
def test_real_technology_files_round_trip(path):
    text = path.read_text(encoding="utf-8")
    first = standardize_text("technology", text)
    assert first is not None
    assert first.count("{") == first.count("}")
    assert _tech_ids(first) == _tech_ids(text)
    assert standardize_text("technology", first) == first


def test_shipped_doctrine_folders_cover_the_netherlands_ideas():
    """The five folders MD ships are exactly the five modifiers in use."""
    shipped = REPO_ROOT / "common" / "doctrines" / "folders" / "doctrine_folders.txt"
    harvested = _harvest_doctrine_folder_cost_factors([str(shipped)])
    assert "equipment_doctrine_cost_factor" in harvested
    for vanilla in ("air", "land", "naval", "special_forces"):
        assert f"{vanilla}_doctrine_cost_factor" in harvested
