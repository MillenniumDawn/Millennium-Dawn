"""Tests for `validate_mios.py` (MIO organization definitions)."""

import random
import re

import pytest
import validate_mios as V
from shared.suite import write_under


def _validator(tmp_path):
    return V.Validator(str(tmp_path), workers=1)


def _assert_issues(issues, expected):
    """Issues match *expected* in order. An entry is a category, or a tuple of a
    category and fragments of `<severity> line <n>: <message>`."""
    rows = [(i.category, f"{i.severity} line {i.line}: {i.message}") for i in issues]
    assert len(rows) == len(expected), rows
    for (category, text), entry in zip(rows, expected):
        want, *fragments = (entry,) if isinstance(entry, str) else entry
        assert category == want and all(f in text for f in fragments), (entry, rows)


def test_commented_org_blocks_are_not_parsed():
    text = (
        "# BAD_org = {\n"
        "#   allowed = { original_tag = BAD }\n"
        "# }\n"
        "GENERIC_live_org = { allowed = { always = yes } }\n"
    )
    clean = V.blank_comments(text)
    assert [org_id for _start, _end, org_id in V._block_spans(clean)] == [
        "GENERIC_live_org"
    ]


_NO_LOC = frozenset()

_BLOCK_CHECKS = {
    "id": lambda v, org, body, loc: v._check_id(org, "f.txt", 3),
    "allowed": lambda v, org, body, loc: v._check_allowed(org, body, "f.txt", 3),
    "initial_trait": lambda v, org, body, loc: v._check_initial_trait(
        org, body, "f.txt", 3
    ),
    "position": lambda v, org, body, loc: v._check_positions(org, body, "f.txt", 3),
    "organization_modifier": lambda v, org, body, loc: v._check_org_modifier_range(
        body, "f.txt", 3
    ),
    "on_complete": lambda v, org, body, loc: v._check_on_complete(body, "f.txt", 3),
    "header": lambda v, org, body, loc: v._check_header_text(
        org, body, "f.txt", 3, loc
    ),
    "trait loc": lambda v, org, body, loc: v._check_trait_localisation(
        org, body, "f.txt", 3, loc
    ),
}

# check: {case: (org id, org body, English loc keys, expected issues)}
_BLOCK_CASES = {
    "id": {
        "lowercase generic id is shared": (
            "generic_AFV_equipment_organization",
            "",
            _NO_LOC,
            [],
        ),
        "uppercase GENERIC id is shared": (
            "GENERIC_marshall_tractor_works",
            "",
            _NO_LOC,
            [],
        ),
        "id without a tag prefix": (
            "norinco_manufacturer",
            "",
            _NO_LOC,
            [("org-id-format", "line 4:")],
        ),
    },
    "allowed": {
        "tag matches the id": (
            "ISR_rafael_materiel_manufacturer",
            "\tallowed = { original_tag = ISR }\n",
            _NO_LOC,
            [],
        ),
        "tag differs from the id": (
            "FRA_naval_manufacturer",
            "\tallowed = { original_tag = GER }\n",
            _NO_LOC,
            [("org-allowed-tag", "original_tag = FRA")],
        ),
        "id without a tag prefix": (
            "norinco_manufacturer",
            "\tallowed = { always = yes }\n",
            _NO_LOC,
            [],
        ),
    },
    "initial_trait": {
        "named after the org tag": (
            "GER_mercedes_manufacturer",
            "initial_trait = {\n\tname = GER_Mercedes_trait\n}",
            _NO_LOC,
            [],
        ),
        "named without the org tag": (
            "NKO_second_economic_committee",
            "initial_trait = {\n\tname = tank_facility_foundry\n}",
            _NO_LOC,
            ["initial-trait-name"],
        ),
        "generic initial trait reference": (
            "ARG_fabricaciones_militares_manufacturer",
            "initial_trait = {\n"
            "\tname = generic_mio_initial_trait_infantry_manufacturer\n}",
            _NO_LOC,
            [],
        ),
    },
    "position": {
        "x inside the bounds": (
            "TST_org",
            "\tposition = { x = -1 y = 0 }\n",
            _NO_LOC,
            [],
        ),
        "x past the bounds": (
            "TST_org",
            "\tposition = { x = 12 y = 3 }\n",
            _NO_LOC,
            ["trait-x-bounds"],
        ),
        "exempt shared org": (
            "generic_naval_equipment_organization",
            "\tposition = { x = 16 y = 0 }\n",
            _NO_LOC,
            [],
        ),
        "shared org not on the exempt list": (
            "generic_some_new_org",
            "\tposition = { x = 16 y = 0 }\n",
            _NO_LOC,
            ["trait-x-bounds"],
        ),
    },
    "organization_modifier": {
        "whole-number percentage": (
            "TST_org",
            "\tinitial_trait = {\n"
            "\t\torganization_modifier = {\n"
            "\t\t\tmilitary_industrial_organization_size_up_requirement = -3\n"
            "\t\t}\n"
            "\t}\n",
            _NO_LOC,
            [("org-modifier-out-of-range", "line 6:")],
        ),
        "fractional percentages": (
            "TST_org",
            "\torganization_modifier = {\n"
            "\t\tmilitary_industrial_organization_size_up_requirement = -0.15\n"
            "\t\tmilitary_industrial_organization_research_bonus = 0.10\n"
            "\t}\n",
            _NO_LOC,
            [],
        ),
        "task capacity is exempt from the range": (
            "TST_org",
            "\torganization_modifier = "
            "{ military_industrial_organization_task_capacity = 3 }\n",
            _NO_LOC,
            [],
        ),
    },
    "on_complete": {
        "empty": (
            "TST_org",
            "\ton_complete = {\n\t}\n",
            _NO_LOC,
            ["on-complete-empty"],
        ),
        "with an effect": (
            "TST_org",
            "\ton_complete = { expenditure_for_mio_upgrade = yes }\n",
            _NO_LOC,
            [],
        ),
    },
    "header": {
        "literal string": (
            "AST_nioa_australia_material",
            'tree_header_text = {\n\ttext = "Lithgow Lineage"\n\tx = 1\n}',
            _NO_LOC,
            [
                (
                    "header-text-not-tokenized",
                    "error line",
                    "AST_nioa_australia_material_mio_header_<slug>",
                )
            ],
        ),
        "token with loc": (
            "NKO_1_bureau_materiel_manufacturer",
            "tree_header_text = {\n\ttext = NKO_mio_header_armor\n\tx = 1\n}",
            frozenset({"NKO_mio_header_armor"}),
            [],
        ),
        "token resolves through the tag prefix": (
            "ALG_khenchela_arms_manufacturer",
            "tree_header_text = {\n\ttext = mio_header_foo\n\tx = 1\n}",
            frozenset({"ALG_mio_header_foo"}),
            [],
        ),
        "token without loc": (
            "ENG_supacat_utility_manufacturer",
            "tree_header_text = {\n\ttext = x\n\tx = 2\n}",
            _NO_LOC,
            [("header-text-loc-missing", "error line 4:")],
        ),
        "shared org has no tag fallback": (
            "GENERIC_mil_kamov_rotorworks",
            "tree_header_text = {\n\ttext = kamov_header\n\tx = 2\n}",
            frozenset({"GEN_kamov_header"}),
            ["header-text-loc-missing"],
        ),
        "block without a text key": (
            "GRE_org",
            "tree_header_text = {\n\tx = 1\n}",
            _NO_LOC,
            [],
        ),
    },
    "trait loc": {
        "name with loc": (
            "ALG_khenchela_arms_manufacturer",
            "trait = {\n\ttoken = ALG_khenchela_trait_desert_hardened\n"
            "\tname = ALG_khenchela_trait_desert_hardened\n}",
            frozenset({"ALG_khenchela_trait_desert_hardened"}),
            [],
        ),
        "name without loc": (
            "ROM_romarm_material_manufacturer",
            "trait = {\n\ttoken = ROM_romarm_export_ammo\n"
            "\tname = ROM_romarm_trait_export_ammo\n}",
            _NO_LOC,
            [("trait-loc-missing", "error line", "ROM_romarm_trait_export_ammo")],
        ),
        "nameless trait resolves through the org token": (
            "FRA_arquus_manufacturer",
            "trait = {\n\ttoken = FRA_arquus_griffon_vbmr\n}",
            frozenset({"FRA_arquus_manufacturer_FRA_arquus_griffon_vbmr"}),
            [],
        ),
        "nameless trait without the org token": (
            "FRA_arquus_manufacturer",
            "trait = {\n\ttoken = FRA_arquus_griffon_vbmr\n}",
            _NO_LOC,
            [("trait-loc-missing", "name = FRA_arquus_griffon_vbmr")],
        ),
        "initial_trait name without loc": (
            "ARG_bersa_manufacturer",
            "initial_trait = {\n\tname = generic_infantry_equipment_organization\n}",
            _NO_LOC,
            ["trait-loc-missing"],
        ),
        "trait without a name or token": (
            "GRE_org",
            "trait = {\n\tposition = { x = 1 }\n}",
            _NO_LOC,
            [],
        ),
    },
}


@pytest.mark.parametrize(
    ("check", "org_id", "body", "loc_keys", "expected"),
    [
        pytest.param(check, *case, id=f"{check}: {name}")
        for check, cases in _BLOCK_CASES.items()
        for name, case in cases.items()
    ],
)
def test_org_block_checks(tmp_path, check, org_id, body, loc_keys, expected):
    v = _validator(tmp_path)
    _BLOCK_CHECKS[check](v, org_id, body, loc_keys)
    _assert_issues(v._issues, expected)


def test_staged_english_localisation_scans_all_mios(tmp_path, monkeypatch):
    org_dir = tmp_path / V.ORG_DIR
    org_dir.mkdir(parents=True)
    (org_dir / "MD_TEST_organizations.txt").write_text(
        "TST_test_org = {\n"
        "\tallowed = { original_tag = TST }\n"
        "\ttrait = {\n"
        "\t\tname = TST_missing_trait\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    (loc_dir / "MD_mio_l_english.yml").write_text(
        'l_english:\n other:0 "Other"\n', encoding="utf-8-sig"
    )
    monkeypatch.setenv("MD_STAGED_FILES", "localisation/english/MD_mio_l_english.yml")

    v = V.Validator(str(tmp_path), staged_only=True, workers=1)
    v.run_validations()

    assert [issue.category for issue in v._issues] == ["trait-loc-missing"]


def test_full_run_on_fixture_dir(tmp_path):
    org_dir = tmp_path / V.ORG_DIR
    org_dir.mkdir(parents=True)
    (org_dir / "MD_TEST_organizations.txt").write_text(
        "TST_bad_org = {\n"
        "\tallowed = { original_tag = GER }\n"
        "\tinitial_trait = {\n"
        "\t\tname = wrong_name\n"
        "\t}\n"
        "\tposition = { x = 12 y = 0 }\n"
        "\ton_complete = {\n"
        "\t}\n"
        "}\n"
        "\n"
        "generic_shared = {\n"
        "\tallowed = { always = no }\n"
        "}\n"
    )
    v = _validator(tmp_path)
    v.run_validations()
    assert sorted(i.category for i in v._issues) == [
        "initial-trait-name",
        "on-complete-empty",
        "org-allowed-tag",
        "trait-loc-missing",
        "trait-x-bounds",
    ]
    by_cat = {i.category: i for i in v._issues}
    assert "org-id-format" not in by_cat
    assert by_cat["org-allowed-tag"].severity == "error"
    assert by_cat["on-complete-empty"].severity == "error"
    assert by_cat["trait-x-bounds"].severity == "error"
    assert by_cat["initial-trait-name"].severity == "error"
    assert by_cat["trait-loc-missing"].severity == "error"


# ---- equipment_bonus dead-stat checks (issue #3044) ------------------------

_EQUIPMENT = """
equipments = {
\tAA_Equipment = {
\t\tis_archetype = yes
\t\treliability = 0.9
\t\tair_attack = 0.375
\t}
\tcnc_equipment_type = {
\t\tis_archetype = yes
\t\treliability = 0.9
\t\tmax_organisation = 0.2
\t}
\tcorvette = {
\t\tis_archetype = yes
\t\ttype = screen_ship
\t\treliability = 0.9
\t\tbuild_cost_ic = 900
\t}
}
"""


def _equipment_index(tmp_path):
    equipment_dir = tmp_path / "common" / "units" / "equipment"
    equipment_dir.mkdir(parents=True, exist_ok=True)
    (equipment_dir / "MD_test_equipment.txt").write_text(_EQUIPMENT, encoding="utf-8")
    return V.build_equipment_stat_index(str(tmp_path))


_SHARED_TYPES = "\tequipment_type = {\n\t\tAA_Equipment\n\t}\n"


def _run_org_check(tmp_path, body, org_id="TST_org"):
    body = V.blank_comments(body)
    v = _validator(tmp_path)
    v._org_bodies = {org_id: body, "generic_shared": _SHARED_TYPES}
    v._check_org_trait_bonuses(org_id, body, "f.txt", 0, _equipment_index(tmp_path))
    return v


_MANPADS_ORG = (
    "\tequipment_type = {\n"
    "\t\tAA_Equipment\n"
    "\t}\n"
    "\ttrait = {\n"
    "\t\ttoken = TST_trait\n"
    "\t\tequipment_bonus = {\n"
    "\t\t\tmax_organisation = 0.10\n"
    "\t\t}\n"
    "\t}\n"
)

_BOTH_TYPES = "\tequipment_type = {\n\t\tAA_Equipment\n\t\tcnc_equipment_type\n\t}\n"

_DEAD_BONUS = "\t\tequipment_bonus = { max_organisation = 0.10 }\n"

# case: (org body, expected issues)
_BONUS_CASES = {
    "stat the equipment lacks": (
        _MANPADS_ORG,
        [("mio-bonus-no-base-stat", "error line 7:", "max_organisation")],
    ),
    "stat the equipment declares": (
        _MANPADS_ORG.replace("max_organisation = 0.10", "air_attack = 0.10"),
        [],
    ),
    # The trait limits itself to the half without the stat: dead, not partial.
    "limit_to_equipment_type narrows the scope": (
        _BOTH_TYPES
        + "\ttrait = {\n\t\tlimit_to_equipment_type = { AA_Equipment }\n"
        + _DEAD_BONUS
        + "\t}\n",
        ["mio-bonus-no-base-stat"],
    ),
    "partial coverage": (
        _BOTH_TYPES + "\ttrait = {\n" + _DEAD_BONUS + "\t}\n",
        [
            (
                "mio-bonus-partial-base-stat",
                "error line",
                "AA_Equipment",
                "cnc_equipment_type",
            )
        ],
    ),
    # An org's one initial_trait cannot be split, so partial coverage is unfixable.
    "initial_trait partial coverage is accepted": (
        _BOTH_TYPES + "\tinitial_trait = {\n" + _DEAD_BONUS + "\t}\n",
        [],
    ),
    "initial_trait wholly dead bonus": (
        _SHARED_TYPES + "\tinitial_trait = {\n" + _DEAD_BONUS + "\t}\n",
        ["mio-bonus-no-base-stat"],
    ),
    "named initial_trait bonus": (
        "\tequipment_type = { AA_Equipment }\n"
        "\tinitial_trait = {\n"
        "\t\tname = TST_org_trait\n"
        "\t\tequipment_bonus = { max_organisation = 0.05 }\n"
        "\t}\n",
        ["mio-bonus-no-base-stat"],
    ),
    "include supplies the equipment type": (
        "\tinclude = generic_shared\n\ttrait = {\n" + _DEAD_BONUS + "\t}\n",
        ["mio-bonus-no-base-stat"],
    ),
    "include of an unknown org supplies nothing": (
        "\tinclude = generic_missing\n\ttrait = {\n" + _DEAD_BONUS + "\t}\n",
        [],
    ),
    "unresolvable type suppresses the bonus check": (
        "\tequipment_type = {\n\t\thelicopter_equipment\n\t}\n"
        "\ttrait = {\n" + _DEAD_BONUS + "\t}\n",
        ["mio-equipment-type-unknown"],
    ),
    "commented-out bonus": (
        "\tequipment_type = { AA_Equipment }\n"
        "\ttrait = {\n"
        "\t\tequipment_bonus = {\n"
        "\t\t\t# max_organisation = 0.10\n"
        "\t\t\tair_attack = 0.05\n"
        "\t\t}\n"
        "\t}\n",
        [],
    ),
}


@pytest.mark.parametrize(("body", "expected"), _BONUS_CASES.values(), ids=_BONUS_CASES)
def test_org_trait_equipment_bonus(tmp_path, body, expected):
    _assert_issues(_run_org_check(tmp_path, body)._issues, expected)


def test_zero_base_exempt_stat_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "ZERO_BASE_EXEMPT_STATS", frozenset({"max_organisation"}))
    assert _run_org_check(tmp_path, _MANPADS_ORG)._issues == []


# ---- naval production_bonus checks (issue #3878) ---------------------------

_EFFICIENCY = "production_efficiency_gain_factor = 0.10"

# case: (equipment_type, production_bonus, trait limit, expected issues)
_PRODUCTION_CASES = {
    "efficiency gain on a naval scope": (
        "corvette",
        _EFFICIENCY,
        "",
        [("mio-production-bonus-naval", "error line", "corvette")],
    ),
    "conversion speed on a naval scope": (
        "corvette",
        "production_conversion_speed_factor = 0.15",
        "",
        ["mio-production-bonus-naval"],
    ),
    # A type category owns no `types` entry, so it resolves only as a category.
    "type category counts as naval": (
        "screen_ship",
        "production_efficiency_cap_factor = 0.08",
        "",
        ["mio-production-bonus-naval"],
    ),
    "efficiency gain on a land scope": ("AA_Equipment", _EFFICIENCY, "", []),
    "live production keys on a naval scope": (
        "corvette",
        "production_capacity_factor = 0.10 production_cost_factor = -0.05",
        "",
        [],
    ),
    "mixed naval scope": (
        "AA_Equipment corvette",
        _EFFICIENCY,
        "",
        [
            (
                "mio-production-bonus-partial-naval",
                "warning line",
                "corvette",
                "AA_Equipment",
            )
        ],
    ),
    "limit narrows a mixed org onto ships": (
        "AA_Equipment corvette",
        _EFFICIENCY,
        "\t\tlimit_to_equipment_type = { corvette }\n",
        ["mio-production-bonus-naval"],
    ),
}


@pytest.mark.parametrize(
    ("equipment_type", "bonus", "limit", "expected"),
    _PRODUCTION_CASES.values(),
    ids=_PRODUCTION_CASES,
)
def test_org_trait_production_bonus(tmp_path, equipment_type, bonus, limit, expected):
    body = (
        f"\tequipment_type = {{ {equipment_type} }}\n"
        "\ttrait = {\n"
        "\t\ttoken = TST_trait\n"
        f"{limit}"
        f"\t\tproduction_bonus = {{ {bonus} }}\n"
        "\t}\n"
    )
    _assert_issues(_run_org_check(tmp_path, body)._issues, expected)


def _archetype(name, *stats):
    lines = "".join(f"\t\t\t{stat}\n" for stat in stats)
    return f"\t\t{name} = {{\n{lines}\t\t}}\n"


# case: (equipment_bonus archetype blocks, file, expected issues)
_NESTED_CASES = {
    "each archetype is checked separately": (
        _archetype("AA_Equipment", "max_organisation = 0.03")
        + _archetype("cnc_equipment_type", "max_organisation = 0.03"),
        "p.txt",
        [("mio-bonus-no-base-stat", "AA_Equipment")],
    ),
    "production keys are not equipment stats": (
        _archetype(
            "AA_Equipment",
            "production_cost_factor = -0.1",
            "production_efficiency_cap_factor = 0.05",
            "instant = yes",
        ),
        "p.txt",
        [],
    ),
    "unknown archetype reports only the type": (
        _archetype("not_an_archetype", "max_organisation = 0.03"),
        "p.txt",
        ["mio-equipment-type-unknown"],
    ),
    "same_as_mio in a policy is a keyword": (
        _archetype("same_as_mio", "max_organisation = 0.03")
        + _archetype("AA_Equipment", "max_organisation = 0.03"),
        f"{V.POLICY_DIR}/p.txt",
        ["mio-bonus-no-base-stat"],
    ),
    "same_as_mio in company traits is an archetype": (
        _archetype("same_as_mio", "max_organisation = 0.03")
        + _archetype("AA_Equipment", "max_organisation = 0.03"),
        V.COMPANY_TRAIT_FILE,
        ["mio-equipment-type-unknown", "mio-bonus-no-base-stat"],
    ),
}


@pytest.mark.parametrize(
    ("archetypes", "rel", "expected"), _NESTED_CASES.values(), ids=_NESTED_CASES
)
def test_nested_equipment_bonus(tmp_path, archetypes, rel, expected):
    text = f"mio_policy_test = {{\n\tequipment_bonus = {{\n{archetypes}\t}}\n}}\n"
    v = _validator(tmp_path)
    v._check_nested_equipment_bonus(text, rel, _equipment_index(tmp_path))
    _assert_issues(v._issues, expected)


def test_type_and_child_sharing_a_stat_is_flagged(tmp_path):
    equipment_dir = tmp_path / "common" / "units" / "equipment"
    equipment_dir.mkdir(parents=True, exist_ok=True)
    (equipment_dir / "MD_ships.txt").write_text(
        "equipments = {\n"
        "\thelicopter_operator = {\n"
        "\t\tis_archetype = yes\n"
        "\t\ttype = carrier\n"
        "\t\tbuild_cost_ic = 28000\n"
        "\t}\n"
        "\tcarrier = {\n"
        "\t\tis_archetype = yes\n"
        "\t\ttype = carrier\n"
        "\t\tbuild_cost_ic = 40000\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    text = (
        "mio_policy_test = {\n"
        "\tequipment_bonus = {\n"
        "\t\tcarrier = {\n"
        "\t\t\tbuild_cost_ic = -0.25\n"
        "\t\t}\n"
        "\t\thelicopter_operator = {\n"
        "\t\t\tbuild_cost_ic = -0.25\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    v = _validator(tmp_path)
    v._check_nested_equipment_bonus(
        text, "p.txt", V.build_equipment_stat_index(str(tmp_path))
    )
    assert [i.category for i in v._issues] == ["bonus-type-archetype-stack"]
    assert v._issues[0].severity == "error"
    assert "helicopter_operator" in v._issues[0].message
    assert "carrier" in v._issues[0].message


# ---- mio: reference reachability (issue #3049) -----------------------------

_REFERENCE_ORGS = """\
ENG_lockheed_martin_manufacturer = {
\tallowed = { original_tag = ENG }
}

GRE_eas_materiel_manufacturer = {
\tallowed = { original_tag = GRE }
}

CHI_norinco_manufacturer = {
\tallowed = { OR = { original_tag = CHI original_tag = HKG } }
}

SOV_uralvagonzavod_tank_manufacturer = {
\tallowed = { original_tag = SOV }
}

GENERIC_open_organization = {
\tallowed = { always = yes }
}

USA_boeing_aircraft_manufacturer = {
\tallowed = { is_usa_or_breakaway = yes }
}
"""

_REFERENCE_TAGS = (
    "ENG = { }\nGRE = { }\nCHI = { }\nHKG = { }\nSOV = { }\nNKO = { }\n"
    "USA = { }\nTEX = { }\n"
)

_REFERENCE_TRIGGERS = """\
is_usa_or_breakaway = {
\tOR = {
\t\toriginal_tag = USA
\t\toriginal_tag = TEX
\t}
}
"""


def _reference_validator(tmp_path):
    org_dir = tmp_path / V.ORG_DIR
    org_dir.mkdir(parents=True)
    (org_dir / "MD_TEST_organizations.txt").write_text(
        _REFERENCE_ORGS, encoding="utf-8"
    )
    tag_dir = tmp_path / V.COUNTRY_TAG_DIR
    tag_dir.mkdir(parents=True)
    (tag_dir / "00_countries.txt").write_text(_REFERENCE_TAGS, encoding="utf-8")
    trigger_dir = tmp_path / V.SCRIPTED_TRIGGER_DIR
    trigger_dir.mkdir(parents=True)
    (trigger_dir / "99_USA_scripted_triggers.txt").write_text(
        _REFERENCE_TRIGGERS, encoding="utf-8"
    )
    return _validator(tmp_path)


def _focus(focus_id: str, body: str, available: str = "") -> str:
    available = f"\t\tavailable = {{ {available} }}\n" if available else ""
    return (
        "focus_tree = {\n"
        "\tfocus = {\n"
        f"\t\tid = {focus_id}\n"
        f"{available}"
        "\t\tcompletion_reward = {\n"
        f"{body}"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


_GREECE_FOCUS_FILE = "common/national_focus/05_greece.txt"

# case: (text, file, expected issues)
_REFERENCE_CASES = {
    "unknown org": (
        _focus("GRE_test", "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturr\n"),
        _GREECE_FOCUS_FILE,
        [("mio-reference-unknown", "error line")],
    ),
    "design team of another tag": (
        _focus(
            "GRE_m270_mlrs",
            "\t\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n",
        ),
        _GREECE_FOCUS_FILE,
        [("mio-reference-wrong-tag", "GRE scope")],
    ),
    "design team of the same tag": (
        _focus(
            "GRE_m270_mlrs", "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturer\n"
        ),
        _GREECE_FOCUS_FILE,
        [],
    ),
    # `allowed = { OR = { ... } }` needs balanced-brace parsing.
    "multi-tag allowed block": (
        _focus("HKG_test", "\t\t\tdesign_team = mio:CHI_norinco_manufacturer\n"),
        "common/national_focus/05_china.txt",
        [],
    ),
    "scripted trigger allowed block reaches a tag it names": (
        "\tcreate_equipment_variant = {\n"
        "\t\tdesign_team = mio:USA_boeing_aircraft_manufacturer\n\t}\n",
        "history/countries/TEX - Texas.txt",
        [],
    ),
    "scripted trigger allowed block excludes a tag it omits": (
        "\tcreate_equipment_variant = {\n"
        "\t\tdesign_team = mio:USA_boeing_aircraft_manufacturer\n\t}\n",
        "history/countries/GRE - Greece.txt",
        ["mio-reference-wrong-tag"],
    ),
    "explicit country scope wins over the focus owner": (
        _focus(
            "CHI_NKO_labor_export",
            "\t\t\tCHI = {\n"
            "\t\t\t\tmio:CHI_norinco_manufacturer = {\n"
            "\t\t\t\t\tunlock_mio_trait_tooltip = CHI_nko_juche_production\n"
            "\t\t\t\t}\n"
            "\t\t\t}\n",
            available="original_tag = NKO",
        ),
        "common/national_focus/03_china_north_korea_joint.txt",
        [],
    ),
    # completion_reward_joint_member runs as the other participant.
    "joint focus member scope": (
        "joint_focus = {\n"
        "\tid = CHI_SOV_defense_industrial\n"
        "\tjoint_trigger = {\n"
        "\t\tOR = {\n"
        "\t\t\toriginal_tag = CHI\n"
        "\t\t\toriginal_tag = SOV\n"
        "\t\t}\n"
        "\t}\n"
        "\tavailable = { original_tag = CHI }\n"
        "\tcompletion_reward_joint_member = {\n"
        "\t\tmio:SOV_uralvagonzavod_tank_manufacturer = {\n"
        "\t\t\tunlock_mio_trait_tooltip = SOV_chi_rare_earth_supply\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        "common/national_focus/03_china_russia_joint.txt",
        [],
    ),
    "history filename supplies the tag": (
        "\tset_variant_name = {\n"
        "\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n\t}\n",
        "history/countries/GRE - Greece.txt",
        ["mio-reference-wrong-tag"],
    ),
    # An event's ROOT is whoever fired it, so only existence is checked.
    "event option scope is not guessed": (
        "country_event = {\n"
        "\tid = iranian_focus.117\n"
        "\toption = {\n"
        "\t\tcreate_equipment_variant = {\n"
        "\t\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        "events/Iran.txt",
        [],
    ),
    "commented-out reference": (
        _focus(
            "GRE_test", "\t\t\t# design_team = mio:SWE_does_not_exist_manufacturer\n"
        ),
        _GREECE_FOCUS_FILE,
        [],
    ),
    "org open to every tag": (
        _focus("GRE_test", "\t\t\tdesign_team = mio:GENERIC_open_organization\n"),
        _GREECE_FOCUS_FILE,
        [],
    ),
    "reference outside every focus block": (
        "focus_tree = {\n"
        "\tid = greece\n"
        "\tmio:ENG_lockheed_martin_manufacturer = { }\n"
        "\tfocus = {\n"
        "\t\tid = GRE_other\n"
        "\t}\n"
        "}\n",
        _GREECE_FOCUS_FILE,
        [],
    ),
    "focus without an id falls back to the tags it names": (
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tavailable = { original_tag = GRE }\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        _GREECE_FOCUS_FILE,
        ["mio-reference-wrong-tag"],
    ),
    "focus id prefix that is not a tag": (
        _focus(
            "generic_industrial_base",
            "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturer\n",
            available="original_tag = GRE",
        ),
        _GREECE_FOCUS_FILE,
        [],
    ),
    "history filename without a known tag": (
        "\tdesign_team = mio:ENG_lockheed_martin_manufacturer\n",
        "history/countries/ZZZ - Nowhere.txt",
        [],
    ),
}


@pytest.mark.parametrize(
    ("text", "rel", "expected"), _REFERENCE_CASES.values(), ids=_REFERENCE_CASES
)
def test_mio_references(tmp_path, text, rel, expected):
    v = _reference_validator(tmp_path)
    v._check_mio_references(V.blank_comments(text), rel)
    _assert_issues(v._issues, expected)


def test_scripted_trigger_allowed_block_pins_the_tag(tmp_path):
    v = _reference_validator(tmp_path)
    body = "\tallowed = { is_usa_or_breakaway = yes }\n"
    v._check_allowed("USA_boeing_aircraft_manufacturer", body, "f.txt", 0)
    assert not v._issues
    v._check_allowed("GRE_eas_materiel_manufacturer", body, "f.txt", 0)
    assert [i.category for i in v._issues] == ["org-allowed-tag"]


def test_org_index_is_built_once_and_survives_an_unreadable_file(tmp_path):
    v = _reference_validator(tmp_path)
    (tmp_path / V.ORG_DIR / "broken.txt").mkdir()

    first = v._org_allowed_tags()

    assert first["GRE_eas_materiel_manufacturer"] == frozenset({"GRE"})
    assert v._org_allowed_tags() is first


def test_country_tags_are_built_once_and_survive_an_unreadable_file(tmp_path):
    v = _reference_validator(tmp_path)
    (tmp_path / V.COUNTRY_TAG_DIR / "broken.txt").mkdir()

    first = v._country_tags()

    assert "GRE" in first
    assert v._country_tags() is first


# ---- parser and check edge cases -------------------------------------------


def test_named_sub_blocks_walks_nested_bodies_to_the_end():
    body = "AA_Equipment = { limit = { always = yes } max_organisation = 0.03 }"
    assert [name for name, _start, _inner in V._named_sub_blocks(body)] == [
        "AA_Equipment"
    ]


# ---- full-repo runs --------------------------------------------------------

_RUN_ORGS = """\
TST_test_org = {
\tallowed = { original_tag = TST }
\tequipment_type = {
\t\tAA_Equipment
\t}
\tinitial_trait = {
\t\tname = TST_test_org_trait
\t}
\ttrait = {
\t\tname = TST_test_org_dead_trait
\t\tequipment_bonus = { max_organisation = 0.10 }
\t}
}
"""

_RUN_POLICY = """\
mio_policy_test = {
\tequipment_bonus = {
\t\tAA_Equipment = {
\t\t\tmax_organisation = 0.03
\t\t}
\t}
}
"""

_RUN_COMPANY_TRAIT = """\
TST_company_trait = {
\tequipment_bonus = {
\t\tAA_Equipment = {
\t\t\treliability = 0.05
\t\t}
\t}
}
"""

_RUN_FOCUS = """\
focus_tree = {
\tfocus = {
\t\tid = TST_industry
\t\tcompletion_reward = {
\t\t\tdesign_team = mio:TST_missing_org
\t\t}
\t}
}
"""


def _run_repo(tmp_path):
    write_under(tmp_path, f"{V.ORG_DIR}/MD_TEST_organizations.txt", _RUN_ORGS)
    write_under(tmp_path, f"{V.POLICY_DIR}/MD_TEST_policies.txt", _RUN_POLICY)
    write_under(tmp_path, V.COMPANY_TRAIT_FILE, _RUN_COMPANY_TRAIT)
    write_under(tmp_path, f"{V.COUNTRY_TAG_DIR}/00_countries.txt", "TST = { }\n")
    write_under(tmp_path, "common/national_focus/05_test.txt", _RUN_FOCUS)
    write_under(
        tmp_path,
        "localisation/english/MD_mio_l_english.yml",
        'l_english:\n TST_test_org_trait:0 "Trait"\n'
        ' TST_test_org_dead_trait:0 "Dead"\n',
    )
    _equipment_index(tmp_path)
    return tmp_path


def test_full_run_covers_orgs_policies_and_references(tmp_path):
    _run_repo(tmp_path)
    v = _validator(tmp_path)

    v.run_validations()

    categories = sorted(i.category for i in v._issues)
    assert categories == [
        "mio-bonus-no-base-stat",
        "mio-bonus-no-base-stat",
        "mio-reference-unknown",
    ]
    assert {i.file for i in v._issues} == {
        f"{V.ORG_DIR}/MD_TEST_organizations.txt",
        f"{V.POLICY_DIR}/MD_TEST_policies.txt",
        "common/national_focus/05_test.txt",
    }


_COVERAGE_EQUIPMENT = """
equipments = {
\tsmall_plane_airframe = { is_archetype = yes }
\tsmall_plane_airframe_1 = { archetype = small_plane_airframe }
\tmedium_plane_airframe = {
\t\tis_archetype = yes
\t\ttype = { test_fighter }
\t}
\tmedium_plane_airframe_1 = { archetype = medium_plane_airframe }
}
duplicate_archetypes = {
\tsmall_plane_cas_airframe = { archetype = small_plane_airframe }
}
"""

_COVERAGE_GROUPS = """
mio_cat_test_medium = {
\tequipment_type = {
\t\tmedium_plane_airframe
\t}
}
"""

_COVERAGE_FILE = "history/countries/TST - Test.txt"


def _coverage_issues(tmp_path, org_types, variant):
    """Issues for one variant written against a TST_org listing *org_types*."""
    write_under(
        tmp_path,
        f"{V.ORG_DIR}/MD_TST_organizations.txt",
        f"TST_org = {{\n\tequipment_type = {{ {org_types} }}\n}}\n",
    )
    write_under(tmp_path, "common/units/equipment/MD_test.txt", _COVERAGE_EQUIPMENT)
    write_under(tmp_path, "common/equipment_groups/mio_test.txt", _COVERAGE_GROUPS)
    v = _validator(tmp_path)
    v._org_bodies = v._load_org_bodies()
    text = "create_equipment_variant = {\n" f"{variant}" "}\n"
    v._check_design_team_coverage(
        text, _COVERAGE_FILE, V.build_equipment_stat_index(str(tmp_path))
    )
    return v._issues


def _team(variant_type, team="\tdesign_team = mio:TST_org\n"):
    return f"\ttype = {variant_type}\n{team}"


# case: (TST_org equipment_type, create_equipment_variant body, expected issues)
_COVERAGE_CASES = {
    "type outside the org's equipment_type": (
        "small_plane_airframe",
        _team("medium_plane_airframe_1"),
        [
            (
                "mio-design-team-type-uncovered",
                "warning line 3:",
                "medium_plane_airframe",
            )
        ],
    ),
    "type listed directly": (
        "medium_plane_airframe",
        _team("medium_plane_airframe"),
        [],
    ),
    "type covered through a mio_cat group": (
        "mio_cat_test_medium",
        _team("medium_plane_airframe_1"),
        [],
    ),
    "numbered type listed directly": (
        "medium_plane_airframe_1",
        _team("medium_plane_airframe_1"),
        [],
    ),
    "type covered through its category": (
        "test_fighter",
        _team("medium_plane_airframe_1"),
        [],
    ),
    "numbered type matches its archetype": (
        "small_plane_airframe",
        _team("small_plane_airframe_1"),
        [],
    ),
    "clone is its own archetype": (
        "small_plane_airframe",
        _team("small_plane_cas_airframe_1"),
        [("mio-design-team-type-uncovered", "small_plane_cas_airframe")],
    ),
    "missing design team": (
        "small_plane_airframe",
        _team("medium_plane_airframe_1", ""),
        [],
    ),
    "missing type": ("small_plane_airframe", "\tdesign_team = mio:TST_org\n", []),
    "undefined vanilla type is skipped": (
        "small_plane_airframe",
        _team("fighter_equipment_1"),
        [],
    ),
}


@pytest.mark.parametrize(
    ("org_types", "variant", "expected"),
    _COVERAGE_CASES.values(),
    ids=_COVERAGE_CASES,
)
def test_design_team_coverage(tmp_path, org_types, variant, expected):
    _assert_issues(_coverage_issues(tmp_path, org_types, variant), expected)


def test_unreadable_and_undecodable_files_do_not_stop_the_run(tmp_path):
    _run_repo(tmp_path)
    (tmp_path / V.ORG_DIR / "broken.txt").mkdir()
    (tmp_path / V.POLICY_DIR / "broken.txt").mkdir()
    (tmp_path / "common" / "decisions").mkdir(parents=True)
    (tmp_path / "common" / "decisions" / "broken.txt").mkdir()
    (tmp_path / "common" / "decisions" / "latin1.txt").write_bytes(
        b"design_team = mio:TST_test_org # caf\xe9\n"
    )
    v = _validator(tmp_path)

    v.run_validations()

    assert sorted(i.category for i in v._issues) == [
        "mio-bonus-no-base-stat",
        "mio-bonus-no-base-stat",
        "mio-reference-unknown",
    ]


def test_a_staged_equipment_edit_rescans_every_org(tmp_path, monkeypatch):
    _run_repo(tmp_path)
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/units/equipment/MD_test_equipment.txt"
    )
    v = V.Validator(str(tmp_path), staged_only=True, workers=1)

    v.run_validations()

    assert sorted(i.category for i in v._issues) == [
        "mio-bonus-no-base-stat",
        "mio-bonus-no-base-stat",
    ]


def test_a_staged_scripted_trigger_rescans_orgs_and_references(tmp_path, monkeypatch):
    orgs = _REFERENCE_ORGS.replace(
        "GRE_eas_materiel_manufacturer = {\n\tallowed = { original_tag = GRE }",
        "GRE_eas_materiel_manufacturer = {\n\tallowed = { is_usa_or_breakaway = yes }",
    )
    write_under(tmp_path, f"{V.ORG_DIR}/MD_TEST_organizations.txt", orgs)
    write_under(
        tmp_path,
        f"{V.COUNTRY_TAG_DIR}/00_countries.txt",
        _REFERENCE_TAGS,
    )
    write_under(
        tmp_path,
        f"{V.SCRIPTED_TRIGGER_DIR}/99_USA_scripted_triggers.txt",
        _REFERENCE_TRIGGERS,
    )
    write_under(
        tmp_path,
        "common/national_focus/05_greece.txt",
        _focus(
            "GRE_test",
            "\t\t\tdesign_team = mio:GRE_eas_materiel_manufacturer\n",
        ),
    )
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/scripted_triggers/99_USA_scripted_triggers.txt"
    )
    v = V.Validator(str(tmp_path), staged_only=True, workers=1)

    v.run_validations()

    assert sorted(i.category for i in v._issues) == [
        "mio-reference-wrong-tag",
        "org-allowed-tag",
    ]


def test_staged_run_with_no_mio_input_skips(tmp_path, monkeypatch):
    _run_repo(tmp_path)
    write_under(tmp_path, "interface/unrelated.txt", "guiTypes = { }\n")
    monkeypatch.setenv("MD_STAGED_FILES", "interface/unrelated.txt")
    v = V.Validator(str(tmp_path), staged_only=True, workers=1)

    v.run_validations()

    assert v._issues == []
    assert any("No staged MIO files" in line for line in v.output_lines)


def test_staged_interface_edit_rescans_all_mios(tmp_path, monkeypatch):
    _run_repo(tmp_path)
    sprite = tmp_path / "interface" / "mio.gfx"
    sprite.parent.mkdir(parents=True)
    sprite.write_text("spriteType = { name = GFX_test }\n", encoding="utf-8")
    monkeypatch.setenv("MD_STAGED_FILES", "interface/mio.gfx")

    v = V.Validator(str(tmp_path), staged_only=True, workers=1)

    assert v._org_files()


def test_staged_sprite_deletion_rescans_all_mios(tmp_path):
    _run_repo(tmp_path)
    sprite = tmp_path / "interface" / "mio.gfx"
    sprite.parent.mkdir(parents=True)
    sprite.write_text("spriteType = { name = GFX_test }\n", encoding="utf-8")
    sprite.unlink()
    v = V.Validator(str(tmp_path))
    v.staged_only = True
    v.staged_files = [sprite]

    assert v._org_files()


def _sprite_set(*names):
    return frozenset(names) | {f"GFX_pad_{i}" for i in range(V._MIN_SPRITE_INDEX)}


# case: (sprite names, text, expected issues)
_ICON_CASES = {
    "icon that is not a GFX name": (
        _sprite_set(),
        "\ticon = x # TODO: needs a company logo",
        [("mio-icon-not-gfx", "line 1:")],
    ),
    "unresolved GFX icon": (
        _sprite_set("GFX_idea_other_org"),
        "\ticon = GFX_idea_ALG_seriana\n",
        [("mio-icon-unresolved", "warning line")],
    ),
    "resolved GFX icons": (
        _sprite_set(
            "GFX_idea_ALG_khenchela_arms", "GFX_generic_mio_trait_icon_reliability"
        ),
        "\ticon = GFX_idea_ALG_khenchela_arms\n"
        "\ttrait = {\n\t\ticon = GFX_generic_mio_trait_icon_reliability\n\t}\n",
        [],
    ),
    "small sprite index skips resolution": (
        frozenset({"GFX_something"}),
        "\ticon = GFX_idea_missing\n",
        [],
    ),
    "quoted icon value": (
        _sprite_set(),
        '\ticon = "bare_token"\n',
        ["mio-icon-not-gfx"],
    ),
    "quoted assignment and punctuation in a name": (
        _sprite_set("GFX_company-logo"),
        '\tdesc = "icon = not_a_reference"\n'
        "\ticon = GFX_company-logo # comment icon = fake\n",
        [],
    ),
    "empty value": (_sprite_set(), "\ticon = {}\n", ["mio-icon-not-gfx"]),
}


@pytest.mark.parametrize(
    ("sprites", "text", "expected"), _ICON_CASES.values(), ids=_ICON_CASES
)
def test_icons(tmp_path, sprites, text, expected):
    v = _validator(tmp_path)
    v._sprites = sprites
    v._check_icons(text, "orgs.txt")
    _assert_issues(v._issues, expected)


def _geometry_trait(
    token, x=None, y=None, rel=None, parents=None, any_parents=None, mutual=None
):
    text = "\ttrait = {\n\t\ttoken = " + token + "\n"
    if parents:
        text += "\t\tall_parents = { " + " ".join(parents) + " }\n"
    if any_parents:
        text += "\t\tany_parent = { " + " ".join(any_parents) + " }\n"
    if mutual:
        text += "\t\tmutually_exclusive = { " + " ".join(mutual) + " }\n"
    if rel:
        text += "\t\trelative_position_id = " + rel + "\n"
    if x is not None or y is not None:
        text += "\t\tposition = { x = " + str(x) + " y = " + str(y) + " }\n"
    text += "\t}\n"
    return text


def _index(*bodies):
    index = {}
    for body in bodies:
        for token, trait in V._parse_org_traits(body).items():
            index.setdefault(token, trait)
    return index


def _geometry_validator(tmp_path, index):
    v = _validator(tmp_path)
    v._traits = index
    v._reported_mutex_rows = set()
    return v


def test_real_mio_relative_position_is_trait_level():
    body = (
        "\ttrait = {\n"
        "\t\ttoken = AST_bae_trait_hull_reinforcement\n"
        "\t\tall_parents = { AST_bae_trait_combat_system_integration }\n"
        "\t\trelative_position_id = AST_bae_trait_combat_system_integration\n"
        "\t\tposition = { x = 0 y = 1 }\n"
        "\t}\n"
    )

    trait = V._parse_org_traits(body)["AST_bae_trait_hull_reinforcement"]

    assert trait.rel == "AST_bae_trait_combat_system_integration"
    assert (trait.x, trait.y) == (0, 1)


def test_nested_relative_position_is_not_a_trait_anchor():
    body = (
        "\ttrait = {\n"
        "\t\ttoken = TST_nested_relative\n"
        "\t\tposition = { x = 0 y = 1 relative_position_id = wrong }\n"
        "\t}\n"
    )

    trait = V._parse_org_traits(body)["TST_nested_relative"]

    assert trait.rel is None


_T = _geometry_trait

# case: (org body, another org's body, expected issues)
_GEOMETRY_CASES = {
    "child below its parent": (
        _T("root", x=0, y=0) + _T("child", x=0, y=1, rel="root", parents=["root"]),
        "",
        [],
    ),
    "child on its parent's row": (
        _T("root", x=0, y=0) + _T("child", x=0, y=0, rel="root", parents=["root"]),
        "",
        [("trait-geometry-parent-row", "error line", "`child`", "`root`")],
    ),
    "child above its parent's row": (
        _T("root", x=0, y=2) + _T("child", x=0, y=1, parents=["root"]),
        "",
        ["trait-geometry-parent-row"],
    ),
    "relative position chain across orgs": (
        _T("mid", x=0, y=1, rel="cross_org_root")
        + _T("leaf", x=0, y=1, rel="mid", parents=["mid"]),
        _T("cross_org_root", x=2, y=5),
        [],
    ),
    "unresolvable anchor": (_T("orphan", x=0, y=1, rel="missing_anchor"), "", []),
    "position anchor cycle": (
        _T("a", x=0, y=1, rel="b")
        + _T("b", x=0, y=1, rel="a")
        + _T("child", x=0, y=1, rel="a", parents=["a"]),
        "",
        [],
    ),
    "mutually exclusive traits on different rows": (
        _T("left", x=0, y=2, mutual=["right"]) + _T("right", x=1, y=3),
        "",
        [("trait-geometry-mutex-row", "error line")],
    ),
    "mutually exclusive traits sharing a row": (
        _T("left", x=0, y=2, mutual=["right"]) + _T("right", x=1, y=2),
        "",
        [],
    ),
    "all_parents with mutually exclusive parents": (
        _T("left", x=0, y=0, mutual=["right"])
        + _T("right", x=1, y=0)
        + _T("child", x=0, y=1, parents=["left", "right"]),
        "",
        [("trait-geometry-mutex-parents", "error line", "any_parent")],
    ),
    "any_parent with mutually exclusive parents": (
        _T("left", x=0, y=0, mutual=["right"])
        + _T("right", x=1, y=0)
        + _T("child", x=0, y=1, any_parents=["left", "right"]),
        "",
        [],
    ),
    "unknown parent, anchor and mutex tokens": (
        _T(
            "child",
            x=0,
            y=1,
            rel="no_such_anchor",
            parents=["ghost_parent"],
            mutual=["ghost_peer"],
        ),
        "",
        [],
    ),
}


@pytest.mark.parametrize(
    ("body", "other_org", "expected"),
    _GEOMETRY_CASES.values(),
    ids=_GEOMETRY_CASES,
)
def test_trait_geometry(tmp_path, body, other_org, expected):
    v = _geometry_validator(tmp_path, _index(body, other_org))
    v._check_trait_geometry("TST_org", body, "orgs.txt", 0)
    _assert_issues(v._issues, expected)


# ---- edge-case files through a full run ------------------------------------

_EDGE_TST = f"{V.ORG_DIR}/MD_TST_organizations.txt"
_EDGE_TSU = f"{V.ORG_DIR}/MD_TSU_organizations.txt"
_EDGE_FOCUS = "common/national_focus/05_edge.txt"

# Line 1 is an org, line 2 a comment full of check tokens, line 5 hides a brace
# and a `#` in a string, the trait nests three blocks deep, and the file ends
# without a newline on an org whose quoted `{` never closes.
_EDGE_TST_TEXT = (
    "TST_first = { allowed = { original_tag = TST } on_complete = { } }\n"
    "# TST_ghost = { trait = { token = TST_ghost_trait position = { x = 99 } }"
    " icon = bad mio:TST_ghost }\n"
    "TST_edge_org = {\n"
    "\tallowed = { original_tag = GER }\n"
    '\tdesc = "a {brace} and # hash"\n'
    "\ticon = edge_icon # icon = in_comment\n"
    "\ticon = GFX_missing_edge\n"
    "\ttrait = {\n"
    "\t\ttoken = TST_edge_trait\n"
    "\t\tposition = { x = 12 y = 0 }\n"
    "\t\ton_complete = {\n"
    "\t\t\tif = { limit = { always = yes } }\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
    'TST_last = { allowed = { original_tag = TST } desc = "{" trait = {'
    " token = TST_last_trait position = { x = 10 y = 0 } } }"
)

_EDGE_TSU_TEXT = (
    "TSU_crlf_org = {\r\n"
    "\tallowed = { original_tag = TSU }\r\n"
    "\ttrait = { token = TSU_crlf_trait position = { x = 11 y = 1 } }\r\n"
    "}\r\n"
)

# CRLF and read as bytes, so the `\r` stays in the scanned text.
_EDGE_FOCUS_TEXT = (
    "mio:TST_missing_first = { }\r\n"
    "focus_tree = {\r\n"
    "\tshared_focus = {\r\n"
    "\t\tid = TSU_shared # mio:TST_commented\r\n"
    '\t\tlog = "{ # mio:TST_in_string }"\r\n'
    "\t\tcompletion_reward = {\r\n"
    "\t\t\tdesign_team = mio:TST_edge_org\r\n"
    "\t\t\tTST = { if = { limit = { always = yes } mio:TSU_crlf_org = { } } }\r\n"
    "\t\t}\r\n"
    "\t}\r\n"
    "}\r\n"
    "mio:TST_missing_last = { }"
)


def _unknown_reference(org_id, line):
    return (
        "mio-reference-unknown",
        _EDGE_FOCUS,
        line,
        f"mio:{org_id} matches no MIO definition in {V.ORG_DIR}/ "
        "(ids are case-sensitive)",
    )


def _nameless_trait(path, line, org_id, token):
    return (
        "trait-loc-missing",
        path,
        line,
        f"trait '{token}' has no name and no '{org_id}_{token}' localisation key;"
        f" add name = {token} plus a loc entry",
    )


def _x_bounds(path, line, x):
    return (
        "trait-x-bounds",
        path,
        line,
        f"trait position x = {x} must stay inside 0..9",
    )


_EDGE_FINDINGS = [
    (
        "mio-icon-not-gfx",
        _EDGE_TST,
        6,
        "icon = edge_icon is not a GFX_ sprite name; the engine renders a blank icon",
    ),
    (
        "mio-icon-unresolved",
        _EDGE_TST,
        7,
        "icon = GFX_missing_edge matches no spriteType in any interface/*.gfx "
        "(mod or vanilla)",
    ),
    (
        "on-complete-empty",
        _EDGE_TST,
        1,
        "on_complete is empty; add expenditure_for_mio_upgrade = yes or custom effects",
    ),
    (
        "org-allowed-tag",
        _EDGE_TST,
        3,
        "MIO TST_edge_org must pin its tag with allowed = { original_tag = TST }",
    ),
    _x_bounds(_EDGE_TST, 10, 12),
    _nameless_trait(_EDGE_TST, 8, "TST_edge_org", "TST_edge_trait"),
    _x_bounds(_EDGE_TST, 16, 10),
    _nameless_trait(_EDGE_TST, 16, "TST_last", "TST_last_trait"),
    _x_bounds(_EDGE_TSU, 3, 11),
    _nameless_trait(_EDGE_TSU, 3, "TSU_crlf_org", "TSU_crlf_trait"),
    _unknown_reference("TST_missing_first", 1),
    _unknown_reference("TST_in_string", 5),
    (
        "mio-reference-wrong-tag",
        _EDGE_FOCUS,
        7,
        "mio:TST_edge_org is allowed only for GER, so it does not resolve in TSU scope",
    ),
    (
        "mio-reference-wrong-tag",
        _EDGE_FOCUS,
        8,
        "mio:TSU_crlf_org is allowed only for TSU, so it does not resolve in TST scope",
    ),
    _unknown_reference("TST_missing_last", 12),
]


def _write_edge_repo(tmp_path):
    write_under(tmp_path, _EDGE_TST, _EDGE_TST_TEXT)
    write_under(tmp_path, _EDGE_TSU, _EDGE_TSU_TEXT)
    write_under(tmp_path, _EDGE_FOCUS, _EDGE_FOCUS_TEXT)
    write_under(
        tmp_path,
        f"{V.COUNTRY_TAG_DIR}/00_countries.txt",
        "TST = { }\nTSU = { }\nGER = { }\n",
    )


def _edge_rows(tmp_path, *, workers, sprites=None):
    """Findings of one full run and whether it forked the worker pool."""
    v = V.Validator(str(tmp_path), workers=workers)
    if sprites is not None:
        v._sprites = sprites
    try:
        v.run_validations()
        pooled = v._pool is not None
    finally:
        if v._pool is not None:
            v._pool.terminate()
            v._pool.join()
    return [(i.category, i.file, i.line, i.message) for i in v._issues], pooled


def test_edge_case_files_report_exact_findings_in_order(tmp_path):
    """Quoted braces and `#`, a token-filled comment, first and last lines, a
    missing final newline, CRLF org and reference files, and a `shared_focus`
    owner all keep their findings, lines and order."""
    _write_edge_repo(tmp_path)

    rows, _pooled = _edge_rows(tmp_path, workers=1, sprites=_sprite_set())

    assert rows == _EDGE_FINDINGS


def test_pooled_run_matches_the_in_process_run_in_order(tmp_path, monkeypatch):
    """Twelve .gfx files cross the pool threshold for the sprite index, which
    also holds enough sprites to resolve icons."""
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    monkeypatch.setenv("MD_NO_CACHE", "1")
    _write_edge_repo(tmp_path)
    for index in range(12):
        sprites = "".join(
            f"\tspriteType = {{ name = GFX_pad_{index}_{n} }}\n" for n in range(100)
        )
        write_under(
            tmp_path,
            f"interface/pad_{index:02}.gfx",
            f"spriteTypes = {{\n{sprites}}}\n",
        )

    in_process, forked = _edge_rows(tmp_path, workers=1)
    pooled, pool_used = _edge_rows(tmp_path, workers=2)

    assert (forked, pool_used) == (False, True)
    assert pooled == in_process == _EDGE_FINDINGS


# ---- equivalence with the character walks these scans replaced -------------


def _walk_block_end(text, open_brace_end):
    depth = 1
    i = open_brace_end
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return i


def _walk_left_open_braces(text, pos):
    """Every `{` a leftward walk from *pos* meets at depth zero, innermost first."""
    found = []
    depth = 0
    for i in range(pos - 1, -1, -1):
        if text[i] == "}":
            depth += 1
        elif text[i] == "{":
            if depth:
                depth -= 1
            else:
                found.append(i)
    return found


def _random_texts(pieces, seed, count=400, longest=30):
    rng = random.Random(seed)
    for _ in range(count):
        yield "".join(rng.choice(pieces) for _ in range(rng.randint(0, longest)))


def test_block_end_matches_the_character_walk():
    fixed = ["", "}", "{", " { } }", "a { b { c { d } } } e", "{ { {", '" { "}']
    for text in [*fixed, *_random_texts('{}"# a\n', seed=1)]:
        for start in range(len(text) + 1):
            assert V._block_end(text, start) == _walk_block_end(text, start), (
                text,
                start,
            )


def test_open_braces_match_the_leftward_walk():
    fixed = ["} a { a } } a", "{ a { { a } a", "a } } { a"]
    for text in [*fixed, *_random_texts("{}a\n", seed=2)]:
        positions = [i for i, char in enumerate(text) if char == "a"]
        for pos, stack in zip(positions, V._open_braces(text, positions)):
            assert list(reversed(stack)) == _walk_left_open_braces(text, pos), (
                text,
                pos,
            )


def test_focus_spans_match_the_line_anchored_regex():
    pieces = [
        "focus = {",
        "shared_focus = {",
        "joint_focus={",
        "has_completed_focus = {",
        "focus_tree = {",
        "focus\n=\n{",
        "\t",
        " ",
        "\n",
        "}",
        "x",
    ]
    for text in _random_texts(pieces, seed=3):
        expected = [
            (m.start(), _walk_block_end(text, m.end()))
            for m in V.FOCUS_BLOCK_RE.finditer(text)
        ]
        assert V._focus_spans(text) == expected, text


_LOOKBEHIND_FORMS = [
    (V.ORIGINAL_TAG_RE, r"\boriginal_tag\s*=\s*([A-Z][A-Z0-9_]{1,7})\b"),
    (V._POSITION_BLOCK_RE, r"(?<![A-Za-z0-9_])position\s*=\s*\{([^{}]*)\}"),
    (
        V._RELATIVE_POSITION_RE,
        r"(?<![A-Za-z0-9_])relative_position_id\s*=\s*([A-Za-z0-9_]+)",
    ),
    (
        V._PARENT_BLOCK_RE,
        r"(?<![A-Za-z0-9_])(all_parents|any_parent|parent)\s*=\s*\{([^{}]*)\}",
    ),
    (
        V._MUTUALLY_EXCLUSIVE_RE,
        r"(?<![A-Za-z0-9_])mutually_exclusive\s*=\s*\{([^{}]*)\}",
    ),
    (V.HEADER_TEXT_RE, r'(?<![A-Za-z0-9_])text\s*=\s*("[^"]*"|[^\s{}]+)'),
    (V.NAME_RE, r"(?<![A-Za-z0-9_])name\s*=\s*([A-Za-z0-9_]+)"),
    (V.TOKEN_RE, r"(?<![A-Za-z0-9_])token\s*=\s*([A-Za-z0-9_]+)"),
    (V.MIO_REFERENCE_RE, r"(?<![A-Za-z0-9_])mio:([A-Za-z0-9_]+)"),
    (V.BLOCK_TAG_RE, r"(?<![A-Za-z0-9_])(?:original_)?tag\s*=\s*([A-Z][A-Z0-9]{2})\b"),
    (V.INCLUDE_RE, r"(?<![A-Za-z0-9_])include\s*=\s*([A-Za-z0-9_]+)"),
]

_PATTERN_PIECES = [
    *(
        "original_tag tag position relative_position_id all_parents any_parent"
        " parent mutually_exclusive text name token mio: include trait"
        " initial_trait GER x _ 1 é = { }"
    ).split(),
    " ",
    '"',
    "\n",
]


def test_literal_first_patterns_match_the_lookbehind_forms():
    # `\b` counts a non-ASCII letter as a word character; the others do not.
    fixed = ["éoriginal_tag = GER", "étoken = a", "xmio:a mio:b", "original_tag=GER"]
    for text in [*fixed, *_random_texts(_PATTERN_PIECES, seed=4)]:
        for new, old in _LOOKBEHIND_FORMS:
            got = [(m.span(), m.groups()) for m in new.finditer(text)]
            want = [(m.span(), m.groups()) for m in re.finditer(old, text)]
            assert got == want, (old, text)
        for keyword in ("trait", "initial_trait"):
            opener = re.compile(r"(?<![A-Za-z0-9_])" + keyword + r"\s*=\s*\{")
            want_blocks = [
                (m.start(), text[m.end() : _walk_block_end(text, m.end()) - 1])
                for m in opener.finditer(text)
            ]
            assert V._sub_blocks(text, keyword) == want_blocks, (keyword, text)


def test_relative_position_scan_matches_the_depth_walk():
    old = re.compile(r"(?<![A-Za-z0-9_])relative_position_id\s*=\s*([A-Za-z0-9_]+)")
    pieces = ["relative_position_id = a", "relative_position_id = b", "{", "}", " "]
    for text in _random_texts(pieces + ["_"], seed=5):
        body = "trait = { token = t " + text + " }"
        inner = V._sub_blocks(body, "trait")[0][1]
        depth = 0
        expected = None
        for index, char in enumerate(inner):
            if char in "{}":
                depth += 1 if char == "{" else -1
            elif depth == 0 and (match := old.match(inner, index)):
                expected = match.group(1)
                break
        assert V._parse_org_traits(body)["t"].rel == expected, text


def test_icon_lines_match_counting_from_the_top():
    pieces = ["icon = a", 'icon="b c"', "xicon = d", "# icon = e", '"', "#"]
    for text in _random_texts(pieces + ["\n", "\r\n", "\x0c", " ", "{"], seed=6):
        expected = []
        offset = 0
        for raw_line in text.splitlines():
            code, _comment = V.split_code_and_comment(raw_line)
            for match in V.ICON_ASSIGNMENT_RE.finditer(V.blank_quoted_strings(code)):
                expected.append(text.count("\n", 0, offset + match.start()) + 1)
            offset += len(raw_line) + 1
        assert [line for _name, line in V._iter_icon_values(text)] == expected, text
