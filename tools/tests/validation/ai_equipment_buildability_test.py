"""Starting-research candidates, fallbacks, and bounded unknown cases."""

import ai_equipment_buildability as B
import pytest
from shared.suite import assert_findings, build_validator, run_tool_script, write_tree
from validate_ai_equipment import Validator
from validator_common import Severity

_AI = "common/ai_equipment/shared.txt"
_HISTORY = "history/countries/AAA - Test.txt"
_HULLS = """equipments = {
    test_hull = {
        type = screen_ship
        module_slots = {
            gun = { required = yes allowed_module_categories = { guns } }
            extra = { allowed_module_categories = { guns } }
        }
    }
    future_hull = {
        archetype = test_hull
        module_slots = inherit
    }
}
"""
_MODULES = """equipment_modules = {
    gun_1 = { category = guns }
    gun_2 = { category = guns }
    unknown_gun = { category = guns }
    utility = { category = utilities }
}
"""
_TECHS = """technologies = {
    hull_research = {
        enable_equipments = { test_hull }
    }
    future_research = {
        enable_equipments = { future_hull }
    }
    weapons_1 = {
        enable_equipment_modules = { gun_1 }
    }
    weapons_2 = {
        enable_equipment_modules = { gun_2 }
    }
    utility_research = {
        enable_equipment_modules = { utility }
    }
}
"""
_START = "2000.1.1 = { set_technology = { hull_research = 1 weapons_1 = 1 } }"
_MISSING = "ai-buildability-missing-unlock"
_UNKNOWN = "ai-buildability-unresolved"


def _design(name="current", slots="gun = gun_2", hull="test_hull", extra=""):
    return f"""{name} = {{
    {extra}
    target_variant = {{ type = {hull} modules = {{ {slots} }} }}
}}
"""


def _group(designs, name="shared", users="AAA", extra=""):
    return f"""{name} = {{
    category = naval
    roles = {{ naval_frigate }}
    available_for = {{ {users} }}
    {extra}
    {designs}
}}
"""


def _tree(tmp_path, case):
    files = {
        _AI: case.get("groups", _group(case.get("designs", _design()))),
        _HISTORY: case.get("history", _START),
        "common/units/equipment/hulls.txt": case.get("hulls", _HULLS),
        "common/units/equipment/modules/test.txt": _MODULES,
        "common/technologies/test.txt": _TECHS,
        "common/bookmarks/test.txt": "bookmarks = { bookmark = { date = 2000.1.1.12 } }",
    }
    files.update(case.get("files", {}))
    write_tree(tmp_path, files)
    return tmp_path


_AMMO_HULLS = """equipments = {
    test_hull = {
        type = armor
        module_slots = {
            main_armament_slot = { required = yes allowed_module_categories = { weapons } }
            ammunition_load_slot = { required = yes allowed_module_categories = { } }
            secondary_armament_slot = { allowed_module_categories = { weapons } }
        }
    }
}
"""
_AMMO_MODULES = """equipment_modules = {
    small_autocannon_3 = {
        category = weapons
        allowed_module_categories = { ammunition_load_slot = { autocannon_ammo } }
    }
    afv_machine_gun_3 = {
        category = weapons
        allowed_module_categories = { ammunition_load_slot = { machine_gun_ammo } }
    }
    banned_autocannon = {
        category = weapons
        forbid_equipment_type_exact_match = armor
        allowed_module_categories = { ammunition_load_slot = { autocannon_ammo } }
    }
    inherited_weapon = { category = weapons parent = small_autocannon_3 }
    autocannon_rounds = { category = autocannon_ammo }
    machine_gun_rounds = { category = machine_gun_ammo }
}
"""
_AMMO_CASES = {
    "USA APC before aaa631c76f": (
        "main_armament_slot = { any_of = { small_autocannon_3 afv_machine_gun_3 } } ammunition_load_slot = machine_gun_ammo",
        [("ai-equipment-incompatible-ammo", "small_autocannon_3", "machine_gun_ammo")],
    ),
    "USA APC corrected pairing": (
        "main_armament_slot = small_autocannon_3 ammunition_load_slot = autocannon_ammo",
        [],
    ),
    "both weapon families have ammo": (
        "main_armament_slot = { any_of = { small_autocannon_3 afv_machine_gun_3 } } ammunition_load_slot = { any_of = { autocannon_ammo machine_gun_ammo } }",
        [],
    ),
    "weapon category is not one compatible representative": (
        "main_armament_slot = weapons ammunition_load_slot = machine_gun_ammo",
        [
            (
                "ai-equipment-incompatible-ammo",
                "small_autocannon_3",
                "machine_gun_ammo",
            ),
            ("ai-equipment-ammo-unresolved", "inherited_weapon", "allowance"),
        ],
    ),
    "repeated module alternatives": (
        "main_armament_slot = { module = small_autocannon_3 module = afv_machine_gun_3 } ammunition_load_slot = machine_gun_ammo",
        [("ai-equipment-incompatible-ammo", "small_autocannon_3", "machine_gun_ammo")],
    ),
    "module and any_of alternatives": (
        "main_armament_slot = { module = afv_machine_gun_3 any_of = { small_autocannon_3 } } ammunition_load_slot = machine_gun_ammo",
        [("ai-equipment-incompatible-ammo", "small_autocannon_3", "machine_gun_ammo")],
    ),
    "repeated any_of alternatives": (
        "main_armament_slot = { any_of = { small_autocannon_3 } any_of = { afv_machine_gun_3 } } ammunition_load_slot = machine_gun_ammo",
        [("ai-equipment-incompatible-ammo", "small_autocannon_3", "machine_gun_ammo")],
    ),
    "another equipped weapon can enable ammo": (
        "main_armament_slot = { any_of = { small_autocannon_3 afv_machine_gun_3 } } secondary_armament_slot = afv_machine_gun_3 ammunition_load_slot = machine_gun_ammo",
        [],
    ),
    "forbidden weapon is not a selectable alternative": (
        "main_armament_slot = { any_of = { banned_autocannon afv_machine_gun_3 } } ammunition_load_slot = machine_gun_ammo",
        [],
    ),
    "ammo before nested weapon selection": (
        "ammunition_load_slot = machine_gun_ammo main_armament_slot = { any_of = { small_autocannon_3 afv_machine_gun_3 } }",
        [("ai-equipment-incompatible-ammo", "small_autocannon_3", "machine_gun_ammo")],
    ),
    "current selection remains unresolved": (
        "main_armament_slot = { module = weapons upgrade = current } ammunition_load_slot = machine_gun_ammo",
        [("ai-equipment-ammo-unresolved", "shared/current")],
    ),
    "range selection remains unresolved": (
        "main_armament_slot > small_autocannon_3 ammunition_load_slot = autocannon_ammo",
        [("ai-equipment-ammo-unresolved", "shared/current")],
    ),
}


@pytest.mark.parametrize(("slots", "expected"), _AMMO_CASES.values(), ids=_AMMO_CASES)
def test_weapon_ammunition_alternatives(tmp_path, slots, expected):
    design = _design(
        slots=slots,
        extra="priority = { factor = 0 } enable = { date > 2099.1.1 }",
    ).replace(
        "type = test_hull", "type = test_hull upgrades = { tank_nsb_armor_upgrade = 1 }"
    )
    _tree(
        tmp_path,
        {
            "groups": _group(design).replace("category = naval", "category = land"),
            "hulls": _AMMO_HULLS,
            "files": {"common/units/equipment/modules/test.txt": _AMMO_MODULES},
        },
    )
    validator = build_validator(Validator, tmp_path)
    validator._validate_variant_modules()
    assert_findings(
        [f"{issue.category}: {issue.message}" for issue in validator._issues],
        expected,
    )
    assert all(issue.severity == Severity.WARNING for issue in validator._issues)
    assert validator.errors_found == 0


# case: source changes, expected (category, message fragments) findings.
_CASES = {
    "literal pin": {
        "expected": [
            (
                _MISSING,
                (
                    "AAA",
                    "shared/current",
                    "naval_frigate",
                    "gun_2",
                    "weapons_2",
                    "no usable starting fallback",
                ),
            )
        ]
    },
    "researched literal": {
        "history": _START + "\nset_technology = { weapons_2 = 1 }",
        "expected": [],
    },
    "alternative": {
        "designs": _design(slots="gun = { any_of = { gun_2 gun_1 } }"),
        "expected": [],
    },
    "repeated alternatives": {
        "designs": _design(slots="gun = { module = gun_2 module = gun_1 }"),
        "expected": [],
    },
    "category with unknown alternative": {
        "designs": _design(slots="gun = guns"),
        "expected": [],
    },
    "current refit": {
        "designs": _design(slots="gun = { module = guns upgrade = current }"),
        "expected": [(_UNKNOWN, ("module selection", "role coverage unresolved"))],
    },
    "range": {
        "designs": _design(slots="gun > gun_1"),
        "expected": [(_UNKNOWN, ("module selection",))],
    },
    "equals range": {
        "designs": _design(slots="gun = > gun_1"),
        "expected": [(_UNKNOWN, ("module selection",))],
    },
    "duplicate slot is unresolved": {
        "designs": _design(slots="gun = gun_2 gun = gun_1"),
        "expected": [(_UNKNOWN, ("module selection",))],
    },
    "parent version is unresolved": {
        "groups": _group(
            _design().replace("type = test_hull", "type = test_hull parent_version = 1")
        ),
        "expected": [(_UNKNOWN, ("module selection",))],
    },
    "future hull": {"designs": _design(hull="future_hull"), "expected": []},
    "future enable": {
        "designs": _design(extra="enable = { has_tech = weapons_2 }"),
        "expected": [],
    },
    "future date enable": {
        "designs": _design(extra="enable = { date > 2010.1.1 }"),
        "expected": [],
    },
    "live date enable": {
        "designs": _design(extra="enable = { date > 1999.1.1 }"),
        "expected": [(_MISSING, ("weapons_2",))],
    },
    "foreign tag enable": {
        "designs": _design(extra="enable = { tag = BBB }"),
        "expected": [],
    },
    "decisive OR enable": {
        "designs": _design(
            extra="enable = { OR = { has_country_flag = unknown has_tech = hull_research } }"
        ),
        "expected": [(_MISSING, ("weapons_2",))],
    },
    "NOR enable": {
        "designs": _design(
            extra="enable = { NOT = { has_tech = hull_research has_tech = weapons_2 } }"
        ),
        "expected": [],
    },
    "unknown enable": {
        "designs": _design(extra="enable = { has_country_flag = future }"),
        "expected": [(_UNKNOWN, ("enable condition",))],
    },
    "future priority": {
        "designs": _design(
            extra="priority = { base = -1 modifier = { add = 1000 has_tech = weapons_2 } }"
        ),
        "expected": [(_UNKNOWN, ("nonpositive priority",))],
    },
    "live priority": {
        "designs": _design(
            extra="priority = { base = -1 modifier = { add = 1000 has_tech = hull_research } }"
        ),
        "expected": [(_MISSING, ("weapons_2",))],
    },
    "non-finite priority": {
        "designs": _design(extra="priority = " + "9" * 400),
        "expected": [(_UNKNOWN, ("priority",))],
    },
    "unknown priority": {
        "designs": _design(
            extra="priority = { factor = 100 modifier = { factor = 2 has_war = yes } }"
        ),
        "expected": [(_UNKNOWN, ("dynamic", "priority"))],
    },
    "later research is not starting research": {
        "history": _START + "\n2017.1.1 = { set_technology = { weapons_2 = 1 } }",
        "expected": [(_MISSING, ("weapons_2", "2000.1.1"))],
    },
    "conditional research": {
        "history": _START
        + "\nif = { limit = { has_country_flag = research } set_technology = { weapons_2 = 1 } }",
        "expected": [(_UNKNOWN, ("module selection",))],
    },
    "removed research": {
        "history": _START
        + "\nset_technology = { weapons_2 = 1 }\nset_technology = { weapons_2 = 0 }",
        "expected": [(_MISSING, ("weapons_2",))],
    },
    "scripted research": {
        "history": _START + "\ngive_research = yes",
        "files": {
            "common/scripted_effects/test.txt": "give_research = { set_technology = { weapons_2 = 1 } }"
        },
        "expected": [],
    },
    "foreign research is not guaranteed": {
        "history": _START + "\nBBB = { set_technology = { weapons_2 = 1 } }",
        "expected": [(_UNKNOWN, ("module selection",))],
    },
    "alternative unlocking technology": {
        "files": {
            "common/technologies/alternative.txt": "technologies = { alternate_weapons = { enable_equipment_modules = { gun_2 } } }"
        },
        "history": _START + "\nset_technology = { alternate_weapons = 1 }",
        "expected": [],
    },
    "cross-slot count limit": {
        "hulls": _HULLS.replace(
            "type = screen_ship",
            "type = screen_ship module_count_limit = { category = guns count < 2 }",
        ),
        "designs": _design(slots="gun = gun_1 extra = gun_1"),
        "expected": [(_UNKNOWN, ("slot-valid",))],
    },
    "shared research differs": {
        "groups": _group(_design(), users="AAA BBB"),
        "files": {
            "history/countries/BBB - Other.txt": _START
            + "\nset_technology = { weapons_2 = 1 }"
        },
        "expected": [(_MISSING, ("AAA", "weapons_2"))],
    },
    "usable fallback": {
        "groups": _group(_design())
        + _group(_design("fallback", "gun = gun_1"), "other"),
        "expected": [(_MISSING, ("current", "usable fallback: fallback"))],
    },
    "blocked fallback": {
        "groups": _group(_design())
        + _group(
            _design("fallback", "gun = gun_1"), "other", extra="blocked_for = { AAA }"
        ),
        "expected": [(_MISSING, ("current", "no usable starting fallback"))],
    },
    "future fallback": {
        "designs": _design() + _design("next", hull="future_hull"),
        "expected": [(_MISSING, ("current", "no usable starting fallback"))],
    },
    "unknown fallback": {
        "designs": _design()
        + _design("other", "gun = { module = guns upgrade = current }"),
        "expected": [
            (_MISSING, ("current", "role coverage unresolved")),
            (_UNKNOWN, ("other", "role coverage unresolved")),
        ],
    },
    "slot-valid alternative": {
        "history": _START + "\nset_technology = { utility_research = 1 }",
        "designs": _design(slots="gun = { any_of = { utility gun_1 } }"),
        "expected": [],
    },
    "slot-invalid selection is separate": {
        "history": _START + "\nset_technology = { utility_research = 1 }",
        "designs": _design(slots="gun = utility"),
        "expected": [(_UNKNOWN, ("slot-valid",))],
    },
    "required slot omitted": {
        "designs": _design(slots="extra = gun_1"),
        "expected": [(_UNKNOWN, ("slot-valid",))],
    },
    "optional empty": {
        "designs": _design(slots="gun = gun_1 extra = empty"),
        "expected": [],
    },
    "global availability ignores filename": {
        "groups": _group(_design(), users=""),
        "files": {"history/countries/BBB - Other.txt": _START},
        "expected": [(_MISSING, ("AAA",)), (_MISSING, ("BBB",))],
    },
    "missing history": {
        "groups": _group(_design(), users="ZZZ"),
        "expected": [(_UNKNOWN, ("ZZZ", "missing country history"))],
    },
    "missing bookmark": {
        "files": {"common/bookmarks/test.txt": ""},
        "expected": [(_UNKNOWN, ("No bookmark start date",))],
    },
    "unknown hull": {
        "designs": _design(hull="unknown_hull"),
        "expected": [(_UNKNOWN, ("unknown or dynamic hull",))],
    },
    "unknown module unlock": {
        "designs": _design(slots="gun = unknown_gun"),
        "expected": [(_UNKNOWN, ("module selection",))],
    },
    "unplaced requirements": {
        "designs": _design(
            slots="gun = gun_1", extra="requirements = { module = gun_2 }"
        ),
        "expected": [(_UNKNOWN, ("requirements",))],
    },
    "upgrades": {
        "groups": _group(
            _design(slots="gun = gun_1").replace(
                "type = test_hull", "type = test_hull upgrades = { engine = 2 }"
            )
        ),
        "expected": [(_UNKNOWN, ("upgrades",))],
    },
    "DLC research": {
        "history": _START
        + '\nif = { limit = { has_dlc = "Test DLC" } set_technology = { weapons_2 = 1 } }',
        "expected": [(_MISSING, ("weapons_2", "NOT Test DLC"))],
    },
    "DLC design enable": {
        "history": _START
        + '\nif = { limit = { has_dlc = "Test DLC" } set_technology = { weapons_2 = 1 } }',
        "designs": _design(extra='enable = { has_dlc = "Test DLC" }'),
        "expected": [],
    },
    "DLC folder": {
        "files": {
            "common/technology_tags/test.txt": 'technology_folders = { test_folder = { available = { has_dlc = "Test DLC" } } }',
            "common/technologies/test.txt": _TECHS.replace(
                "enable_equipments = { test_hull }",
                "enable_equipments = { test_hull }\nfolder = { name = test_folder }",
            ),
        },
        "expected": [(_MISSING, ("weapons_2", "[start 2000.1.1; Test DLC]"))],
    },
}


@pytest.mark.parametrize("case", _CASES.values(), ids=_CASES)
def test_starting_candidates(tmp_path, case):
    _tree(tmp_path, case)
    validator = build_validator(Validator, tmp_path, check_buildability=True)
    validator._validate_buildability()
    issues = validator._issues
    assert_findings(
        [f"{issue.category}: {issue.message}" for issue in issues],
        [(category, *fragments) for category, fragments in case["expected"]],
    )
    assert all(issue.severity == Severity.WARNING for issue in issues)
    assert all(issue.file == _AI and issue.line > 0 for issue in issues)
    assert validator.errors_found == 0


@pytest.mark.parametrize("limit", ("selections", "DLC"))
def test_work_bounds_are_unresolved(tmp_path, monkeypatch, limit):
    case = {
        "designs": _design(slots="gun = guns"),
        "history": _START
        + '\nif = { limit = { has_dlc = "Test DLC" } set_technology = { weapons_2 = 1 } }',
    }
    monkeypatch.setattr(
        B, "_MAX_SELECTIONS" if limit == "selections" else "_MAX_DLC_CONFIGS", 1
    )
    _tree(tmp_path, case)
    validator = build_validator(Validator, tmp_path, check_buildability=True)
    validator._validate_buildability()
    assert validator._issues
    assert all(issue.category == _UNKNOWN for issue in validator._issues)


def test_buildability_is_opt_in_and_called_by_run(tmp_path, monkeypatch):
    validator = build_validator(Validator, tmp_path)
    called = []
    for name in (
        "_validate_coverage",
        "_validate_variant_modules",
        "_validate_history_consistency",
        "_validate_buildability",
    ):
        monkeypatch.setattr(validator, name, lambda name=name: called.append(name))
    validator.run_validations()
    assert called == [
        "_validate_coverage",
        "_validate_variant_modules",
        "_validate_history_consistency",
    ]
    called.clear()
    validator.check_buildability = True
    validator.run_validations()
    assert called == [
        "_validate_coverage",
        "_validate_variant_modules",
        "_validate_history_consistency",
        "_validate_buildability",
    ]


@pytest.mark.parametrize(
    "staged",
    (
        _AI,
        "common/units/equipment/hulls.txt",
        "common/ai_equipment/deleted.txt",
        "common/technologies/deleted.txt",
        "common/technologies/test.txt",
        "common/technology_tags/test.txt",
        "common/bookmarks/test.txt",
        "common/scripted_effects/test.txt",
        _HISTORY,
        "common/ideas/unrelated.txt",
    ),
)
def test_staged_dependency_selection(tmp_path, monkeypatch, staged):
    _tree(tmp_path, {})
    monkeypatch.setenv("MD_STAGED_FILES", staged)
    validator = build_validator(
        Validator, tmp_path, check_buildability=True, staged_only=True
    )
    validator._validate_buildability()
    assert [issue.category for issue in validator._issues] == (
        [] if "unrelated" in staged else [_MISSING]
    )


def test_unreadable_input_is_not_empty_research(tmp_path):
    _tree(tmp_path, {})
    (tmp_path / _HISTORY).write_bytes(b"\xff")
    validator = build_validator(Validator, tmp_path, check_buildability=True)
    validator._validate_buildability()
    assert [issue.category for issue in validator._issues] == [_UNKNOWN]
    assert "could not be read" in validator._issues[0].message


def test_strict_cli_keeps_new_findings_advisory(tmp_path):
    _tree(tmp_path, {})
    result = run_tool_script(
        "validation/validate_ai_equipment.py",
        "--path",
        tmp_path,
        "--strict",
        "--check-buildability",
        "--no-color",
        "--no-cache",
        "--workers",
        "1",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "weapons_2" in result.stdout + result.stderr
