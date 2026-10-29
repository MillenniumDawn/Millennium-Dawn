"""Tests for validate_oob_units.py.

The create_unit ensure, guard and owner rules live in
validate_oob_units_create_unit_test.py.
"""

import pytest
import validate_oob_units as oob
from equipment_module_slots import created_variant_spans
from shared.suite import (
    checks_called_by_run,
    initialize_git_repository,
    run_git,
    write_tree,
)
from shared.suite import write_under as _write
from validate_oob_units import (
    TemplateLimits,
    Validator,
    _build_block_nodes,
    _check_created_units,
    _closest_if,
    _container_for,
    _country_scope_path,
    _deepest_node_at,
    _deleted_template_names,
    _effect_template_closure,
    _extract_division_group_keys,
    _extract_unit_refs_from_blocks,
    _is_positive_if_limit_condition,
    _parse_canonical_units_file,
    _parse_division_string,
    _runs_in_if_true_branch,
    _scope_label,
    build_variant_name_index,
    build_variant_registry,
    check_attributed_archetypes,
    check_misplaced_support,
    check_named_variant_refs,
    check_oob_variant_refs,
    check_template_slots,
    division_template_entries,
    find_load_oob_references,
    read_template_limits,
    validate_namelist_file,
    validate_oob_division_groups_file,
    validate_oob_file,
    variant_tag_from_path,
)
from validator_common import strip_comments

_BS = chr(92)

_LAND_UNITS = """sub_units = {
\t# a stripped comment leaves a blank line at depth 1
\tArm_Inf_Bat = {
\t\tmap_icon_category = infantry
\t\tneed = {
\t\t\tinfantry_weapons = 100
\t\t}
\t}
\t@spacer = 1
\tMech_Inf_Bat = {
\t\tneed_equipment = {
\t\t\tutil_vehicle_equipment = 40
\t\t}
\t}
}
"""

_NAVAL_UNITS = """sub_units = {
\tcorvette = {
\t\tmap_icon_category = ship
\t\tneed = {
\t\t\tship_hull_corvette = 1
\t\t}
\t}
}
"""


def _validator(tmp_path, workers=1, **kwargs):
    return Validator(
        mod_path=str(tmp_path), use_colors=False, workers=workers, **kwargs
    )


def _messages(validator):
    return [issue.message for issue in validator._issues]


def _write_units(tmp_path):
    _write(tmp_path, "common/units/MD_land_units.txt", _LAND_UNITS)
    _write(tmp_path, "common/units/MD_naval_units.txt", _NAVAL_UNITS)


def test_run_validations_calls_every_check(tmp_path, monkeypatch):
    called, checks = checks_called_by_run(_validator(tmp_path), monkeypatch)
    assert called == checks


_MISSING_FILE_WORKERS = {
    "unit references": lambda path, root: validate_oob_file((path, set(), {}, root)),
    "namelist": lambda path, root: validate_namelist_file((path, set(), {}, root)),
    "division_names_group": lambda path, root: validate_oob_division_groups_file(
        (path, {"USA_ARM"}, {}, root)
    ),
    "create_unit": lambda path, root: _check_created_units(
        (path, "gone.txt", root, frozenset(), {}, {}, frozenset())
    ),
}


@pytest.mark.parametrize(
    "worker", _MISSING_FILE_WORKERS.values(), ids=_MISSING_FILE_WORKERS
)
def test_worker_returns_nothing_for_a_missing_file(tmp_path, worker):
    assert worker(str(tmp_path / "gone.txt"), str(tmp_path)) == []


# --- canonical units and namelists ------------------------------------------


def test_parse_canonical_units_file_skips_non_definition_lines():
    assert _parse_canonical_units_file(_LAND_UNITS) == {"Arm_Inf_Bat", "Mech_Inf_Bat"}


def test_build_canonical_units_reads_each_source_once_for_both_indexes(
    tmp_path, monkeypatch
):
    _write_units(tmp_path)
    calls = []
    original = oob.disk_cache.per_file_cached_by_content

    def cached(*args, **kwargs):
        calls.append(args[1])
        return original(*args, **kwargs)

    monkeypatch.setattr(oob.disk_cache, "per_file_cached_by_content", cached)
    validator = _validator(tmp_path)
    validator._build_canonical_units()

    assert calls == ["oob_units.composite", "oob_units.composite"]
    assert validator.canonical == {"Arm_Inf_Bat", "Mech_Inf_Bat", "corvette"}
    assert validator.namelist_canonical == {
        "Arm_Inf_Bat",
        "Mech_Inf_Bat",
        "corvette",
        "infantry_weapons",
        "util_vehicle_equipment",
        "ship_hull_corvette",
    }


# case: (namelist path under common/units, content, warning messages)
_NAMELIST_CASES = {
    "wrong-case division_types token": (
        "names_divisions/USA_names_divisions.txt",
        "USA_ARM = {\n"
        '\tname = "Armored Divisions"\n'
        "\tfor_countries = { USA }\n"
        '\tdivision_types = { "arm_inf_bat" }\n'
        "}\n",
        [
            "USA_names_divisions.txt: unknown division_types token 'arm_inf_bat' "
            "(did you mean 'Arm_Inf_Bat'?)"
        ],
    ),
    "canonical division_types tokens": (
        "names_divisions/USA_names_divisions.txt",
        "USA_ARM = {\n"
        '\tname = "Armored Divisions"\n'
        '\tdivision_types = { "Arm_Inf_Bat" "Mech_Inf_Bat" }\n'
        "}\n",
        [],
    ),
    "vanilla ship_types token": (
        "names_ships/USA_ship_names.txt",
        "USA_SHIPS = {\n"
        "\tname = NAME_THEME_SHIPS\n"
        "\tfor_countries = { USA }\n"
        "\ttype = ship\n"
        "\tship_types = {\n\t\tcorvette\n\t\tlight_cruiser\n\t}\n"
        "}\n",
        ["USA_ship_names.txt: unknown ship_types token 'light_cruiser'"],
    ),
    "names outside ship_types and comments are not tokens": (
        "names_ships/USA_ship_names.txt",
        "USA_CORVETTES = {\n"
        "\tname = NAME_THEME_CORVETTES\n"
        "\tship_types = { corvette } # submarine\n"
        '\tfallback_name = "LHA-%d"\n'
        '\tunique = { "LHA" "submarine" "light_cruiser" "heavy_cruiser" }\n'
        "}\n",
        [],
    ),
    "vanilla ship design block key": (
        "names/00_USA_names.txt",
        'USA = {\n\tsubmarine = {\n\t\tprefix = ""\n\t\tgeneric = { "Ship" }\n'
        "\t\tunique = { }\n\t}\n}\n",
        ["00_USA_names.txt: unknown namelist block key 'submarine'"],
    ),
    "block key naming an equipment type": (
        "names/00_USA_names.txt",
        "USA = {\n"
        '\tinfantry_weapons = {\n\t\tprefix = "Rifle"\n\t}\n'
        '\tnot_a_real_unit_key = {\n\t\tprefix = "Ghost"\n\t}\n'
        "}\n",
        ["00_USA_names.txt: unknown namelist block key 'not_a_real_unit_key'"],
    ),
}


@pytest.mark.parametrize(
    "rel, content, expected", _NAMELIST_CASES.values(), ids=_NAMELIST_CASES
)
def test_namelist_references(tmp_path, rel, content, expected):
    _write_units(tmp_path)
    _write(tmp_path, f"common/units/{rel}", content)
    validator = _validator(tmp_path)
    validator._build_canonical_units()
    validator.validate_namelist_references()

    assert validator.warnings_found == len(expected)
    assert _messages(validator) == expected


def test_namelist_file_in_an_unknown_directory_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write(
        tmp_path,
        "common/units/names_other/USA.txt",
        "USA = {\n\tnot_a_real_unit_key = {\n\t\tprefix = X\n\t}\n}\n",
    )
    assert validate_namelist_file((str(path), set(), {}, str(tmp_path))) == []


# --- unit references and division name groups -------------------------------


def test_unknown_unit_in_an_oob_file_suggests_the_closest_name(tmp_path):
    _write_units(tmp_path)
    _write(
        tmp_path,
        "history/units/SWE_1990.txt",
        "division_template = {\n"
        '\tname = "Infantry Brigade"\n'
        "\tregiments = {\n"
        "\t\tArm_Inf_Bt = { x = 0 y = 0 }\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)
    validator._build_canonical_units()
    validator.validate_unit_references()

    assert validator.errors_found == 1
    assert _messages(validator) == [
        "SWE_1990.txt: unknown unit 'Arm_Inf_Bt' (did you mean 'Arm_Inf_Bat'?)"
    ]


def test_extract_unit_refs_reads_both_block_and_count_forms():
    content = (
        "division_template = {\n"
        '\tname = "Infantry Brigade"\n'
        "\tdivision_names_group = USA_INF\n"
        "\tregiments = {\n"
        "\t\tArm_Inf_Bat = {\n"
        "\t\t\tx = 0\n"
        "\t\t\ty = 0\n"
        "\t\t}\n"
        "\n"
        "\t\tMech_Inf_Bat = 2\n"
        "\t}\n"
        "\tsupport = {\n"
        "\t\tengineer = { x = 0 y = 0 }\n"
        "\t}\n"
        "}\n"
    )
    assert _extract_unit_refs_from_blocks(content) == {
        "Arm_Inf_Bat",
        "Mech_Inf_Bat",
        "engineer",
    }


def test_extract_division_group_keys_only_takes_top_level_blocks():
    content = (
        "USA_ARM = {\n"
        '\tname = "Armored Divisions"\n'
        "\tfallback_name = {\n"
        "\t\tfoo = bar\n"
        "\t}\n"
        "}\n"
        "USA_INF = {\n"
        '\tname = "Infantry Divisions"\n'
        "}\n"
    )
    assert _extract_division_group_keys(content) == {"USA_ARM", "USA_INF"}


def test_unknown_division_names_group_suggests_the_closest_group(tmp_path):
    _write(tmp_path, "common/units/names_divisions/empty.txt", "")
    _write(
        tmp_path,
        "common/units/names_divisions/SWE.txt",
        "SWE_ARM = {\n\tname = NAME_SWE_ARM\n}\n",
    )
    _write(
        tmp_path,
        "history/units/SWE_1990.txt",
        "units = {\n"
        "\tdivision = {\n"
        "\t\tdivision_names_group = SWE_ARM\n"
        "\t\tdivision_names_group = SWE_ARMM\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_division_names_group_references()

    assert validator.errors_found == 1
    assert _messages(validator) == [
        "unknown division_names_group 'SWE_ARMM' (did you mean 'SWE_ARM'?)"
    ]
    assert validator._issues[0].line == 4


_AIR_WING_NAMES = "SWE = {\n\tair_wing_names_template = AIR_WING_NAME_SWE\n}\n"

# case: (files beside the SWE namelist, (category, severity, message) per finding)
_AIR_WING_CASES = {
    "template without a loc key": (
        {"common/units/names/empty.txt": ""},
        [
            (
                "air-wing-template-loc",
                "warning",
                "air_wing_names_template references undefined loc key "
                "'AIR_WING_NAME_SWE'",
            )
        ],
    ),
    "template with a loc key": (
        {
            "localisation/english/MD_names_l_english.yml": (
                'l_english:\n AIR_WING_NAME_SWE:0 "%d. Flygflottilj"\n'
            )
        },
        [],
    ),
}


@pytest.mark.parametrize(
    "files, expected", _AIR_WING_CASES.values(), ids=_AIR_WING_CASES
)
def test_air_wing_names_template_loc(tmp_path, files, expected):
    write_tree(tmp_path, {"common/units/names/00_SWE_names.txt": _AIR_WING_NAMES})
    write_tree(tmp_path, files)
    validator = _validator(tmp_path)
    validator.validate_air_wing_names_template_loc()

    assert [
        (issue.category, issue.severity, issue.message) for issue in validator._issues
    ] == expected


# --- created equipment variants ---------------------------------------------

_HULLS = """
equipments = {
\ttest_tank_chassis = {
\t\tis_archetype = yes
\t\ttype = { armor }
\t\tmodule_slots = {
\t\t\tturret_type_slot = {
\t\t\t\trequired = yes
\t\t\t\tallowed_module_categories = {
\t\t\t\t\ttest_turret_type
\t\t\t\t}
\t\t\t}
\t\t\tarmor_type_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = {
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\ttest_tank_chassis_1 = {
\t\tarchetype = test_tank_chassis
\t\tmodule_slots = inherit
\t}
}
"""

_MODULES = """
equipment_modules = {
\ttest_turret = {
\t\tcategory = test_turret_type
\t\tallowed_module_categories = {
\t\t\tarmor_type_slot = { test_composite_armor_type }
\t\t}
\t}
\ttest_plain_turret = {
\t\tcategory = test_turret_type
\t}
\ttest_composite_armor = {
\t\tcategory = test_composite_armor_type
\t}
}
"""


def _variant(modules_body):
    return (
        "create_equipment_variant = {\n"
        '\tname = "Test Tank"\n'
        "\ttype = test_tank_chassis_1\n"
        "\tmodules = {\n"
        f"{modules_body}"
        "\t}\n"
        "}\n"
    )


_UNLOCKED = (
    "\t\tturret_type_slot = test_turret\n\t\tarmor_type_slot = test_composite_armor\n"
)
_NOT_UNLOCKED = (
    "\t\tturret_type_slot = test_plain_turret\n"
    "\t\tarmor_type_slot = test_composite_armor\n"
)
_VARIANT_SOURCES = (
    "events/05_test.txt",
    "common/national_focus/05_test.txt",
    "common/decisions/05_test.txt",
    "history/countries/TST - Test.txt",
    "common/scripted_effects/05_test.txt",
    "common/special_projects/05_test.txt",
)
_NOT_ALLOWED = "EQUIPMENT VARIANT: module category not allowed in slot"

# case: (variant sources, (file, category) per finding)
_CREATED_VARIANT_CASES = {
    "module the turret does not unlock, in every source": (
        dict.fromkeys(_VARIANT_SOURCES, _variant(_NOT_UNLOCKED)),
        [(rel, _NOT_ALLOWED) for rel in _VARIANT_SOURCES],
    ),
    # Without the unlock rule every real tank design here is a false positive.
    "module the turret unlocks": ({"events/05_test.txt": _variant(_UNLOCKED)}, []),
    # The required turret slot is filled so the unknown slot stands alone.
    "slot the chassis lacks": (
        {
            "events/05_test.txt": _variant(
                "\t\tfixed_ship_battery_slot = test_turret\n"
                "\t\tturret_type_slot = test_turret\n"
            )
        },
        [("events/05_test.txt", "EQUIPMENT VARIANT: slot not on hull")],
    ),
}


@pytest.mark.parametrize(
    "sources, expected",
    _CREATED_VARIANT_CASES.values(),
    ids=_CREATED_VARIANT_CASES,
)
def test_created_variant_modules(tmp_path, sources, expected):
    write_tree(
        tmp_path,
        {
            "common/units/equipment/MD_test_tank_chassis.txt": _HULLS,
            "common/units/equipment/modules/MD_test_tank_modules.txt": _MODULES,
            **sources,
        },
    )
    validator = _validator(tmp_path)
    validator.validate_created_variant_modules()

    assert sorted(
        (issue.file, issue.severity, issue.category) for issue in validator._issues
    ) == sorted((rel, "error", category) for rel, category in expected)


@pytest.mark.parametrize(
    "files, log_line",
    [
        ({}, "  No files with equipment variants to check"),
        (
            {"events/SWE.txt": "country_event = {\n\tid = swe.1\n}\n"},
            "  No create_equipment_variant effects in scope — skipping",
        ),
    ],
    ids=["no variant sources", "no variant in any source"],
)
def test_created_variant_check_skips_without_a_variant(
    tmp_path, monkeypatch, files, log_line
):
    (tmp_path / "common" / "units" / "equipment").mkdir(parents=True)
    write_tree(tmp_path, files)
    validator = _validator(tmp_path)
    logged = []
    monkeypatch.setattr(validator, "log", lambda msg, *a, **k: logged.append(msg))
    validator.validate_created_variant_modules()

    assert validator._issues == []
    assert log_line in logged


def test_variant_sources_preserve_staged_and_full_scopes(tmp_path):
    staged_path = _write(tmp_path, "events/05_staged.txt", _variant(_UNLOCKED))
    _write(tmp_path, "events/06_full.txt", _variant(_UNLOCKED))

    validator = _validator(tmp_path, staged_only=True)
    validator.staged_files = [str(staged_path)]

    staged = validator._get_variant_sources(ignore_staged=False)
    full = validator._get_variant_sources(ignore_staged=True)
    assert {rel for rel, _ in staged} == {"events/05_staged.txt"}
    assert {rel for rel, _ in full} == {
        "events/05_staged.txt",
        "events/06_full.txt",
    }

    full_validator = _validator(tmp_path)
    assert full_validator._get_variant_sources(
        ignore_staged=False
    ) is full_validator._get_variant_sources(ignore_staged=True)


# --- OOB and production equipment references --------------------------------

_CHI_HISTORY = "history/countries/CHI - China.txt"
_CHI_VARIANTS = """
2000.1.1 = {
\tcreate_equipment_variant = {
\t\tname = "Type 053H3 Class"
\t\ttype = frigate_hull_3
\t\tname_group = CHI_FRIGATE_HISTORICAL
\t\tparent_version = 0
\t\tmodules = {
\t\t\tfixed_ship_engine_slot = module_light_surface_diesel_power_1
\t\t}
\t}
\tcreate_equipment_variant = {
\t\tname = "Naresuan Class"
\t\ttype = frigate_hull_2
\t\tparent_version = 1
\t\tmodules = {
\t\t\tfixed_ship_engine_slot = module_light_surface_diesel_power_1
\t\t}
\t}
}
"""


def _ship(hull, name, **fields):
    attrs = " ".join(f"{k} = {v}" for k, v in fields.items())
    return (
        'units = { fleet = { task_force = { ship = { name = "Test" '
        f'equipment = {{ {hull} = {{ amount = 1 {attrs} version_name = "{name}" }} }}'
        " } } } }"
    )


def _fallback(tag, hull, name):
    return (
        f"{tag} has no '{hull}' variant named \"{name}\": "
        "the ship falls back to version 0 of the hull"
    )


@pytest.mark.parametrize(
    "rel, tag",
    [
        (_CHI_HISTORY, "CHI"),
        ("history\\countries\\USA - USA.txt", "USA"),
        ("events/Egypt.txt", None),
    ],
)
def test_variant_tag_from_path(rel, tag):
    assert variant_tag_from_path(rel) == tag


# case: (file declaring _CHI_VARIANTS, OOB content, finding messages)
_OOB_VARIANT_CASES = {
    "creator has the variant": (
        _CHI_HISTORY,
        _ship("frigate_hull_3", "Type 053H3 Class", owner="SIA", creator="CHI"),
        [],
    ),
    "creator has the name on another hull": (
        _CHI_HISTORY,
        _ship("frigate_hull_3", "Naresuan Class", owner="SIA", creator="CHI"),
        [_fallback("CHI", "frigate_hull_3", "Naresuan Class")],
    ),
    "owner stands in for a missing creator": (
        _CHI_HISTORY,
        _ship("frigate_hull_2", "Naresuan Class", owner="CHI"),
        [],
    ),
    "owner without the variant": (
        _CHI_HISTORY,
        _ship("frigate_hull_2", "Naresuan Class", owner="SIA"),
        [_fallback("SIA", "frigate_hull_2", "Naresuan Class")],
    ),
    # Egypt's carrier purchase creates its design in FRA scope inside an event.
    "variant created outside history counts for any tag": (
        "events/Egypt.txt",
        _ship("frigate_hull_3", "Type 053H3 Class", owner="EGY", creator="FRA"),
        [],
    ),
    "ship without a version_name": (
        _CHI_HISTORY,
        'units = { fleet = { task_force = { ship = { name = "Test" '
        "equipment = { frigate_hull_3 = { amount = 1 owner = CHI } } } } } }",
        [],
    ),
    "creator that is not a tag": (
        _CHI_HISTORY,
        _ship("frigate_hull_3", "Naresuan Class", owner="SIA", creator="ROOT"),
        [],
    ),
}


@pytest.mark.parametrize(
    "source, content, expected",
    _OOB_VARIANT_CASES.values(),
    ids=_OOB_VARIANT_CASES,
)
def test_oob_variant_refs(source, content, expected):
    by_tag, wildcard = build_variant_name_index(
        [(source, created_variant_spans(_CHI_VARIANTS))]
    )
    findings = check_oob_variant_refs(content, by_tag, wildcard)
    assert [finding.message for finding in findings] == expected


def _variant_source(tag, variants):
    content = "\n".join(
        f'create_equipment_variant = {{ name = "{name}" type = {equipment} }}'
        for equipment, name in variants
    )
    rel = f"history/countries/{tag} - Test.txt"
    return rel, created_variant_spans(content)


_MIG_VARIANTS = [("medium_plane_airframe_1", "MiG-X")]

_DEFAULT_EQUIPMENT_NAME_CASES = {
    "country name": (
        ' SOV_medium_plane_airframe_1: "MiG-X"\n',
        {"SOV_medium_plane_airframe_1": "MiG-X"},
    ),
    "generic name": (
        ' medium_plane_airframe_1: "Medium aircraft"\n',
        {"medium_plane_airframe_1": "Medium aircraft"},
    ),
    "numbered key with BOM and CRLF": (
        '\ufeffl_english:\r\n SOV_medium_plane_airframe_1:0 "MiG-X" # comment\r\n',
        {"SOV_medium_plane_airframe_1": "MiG-X"},
    ),
    "escaped quotes and hash in name": (
        r' SOV_medium_plane_airframe_1: "MiG-\"X\" #1"',
        {"SOV_medium_plane_airframe_1": r"MiG-\"X\" #1"},
    ),
    "unrelated keys and archetypes": (
        '# SOV_medium_plane_airframe_1: "Commented"\n'
        ' SOV_ghost_airframe: "Unknown type"\n'
        ' SOV_plane_archetype: "Archetype"\n'
        ' SOV_medium_plane_airframe_1_desc: "Description"\n'
        ' sov_medium_plane_airframe_1: "Wrong tag case"\n',
        {},
    ),
    "last definition wins": (
        ' SOV_medium_plane_airframe_1: "Old"\n SOV_medium_plane_airframe_1: "New"\n',
        {"SOV_medium_plane_airframe_1": "New"},
    ),
}


@pytest.mark.parametrize(
    "localisation, expected",
    _DEFAULT_EQUIPMENT_NAME_CASES.values(),
    ids=_DEFAULT_EQUIPMENT_NAME_CASES,
)
def test_default_equipment_name_index(localisation, expected):
    assert (
        oob.build_default_equipment_name_index(
            [
                "equipments = { medium_plane_airframe_1 = { archetype = plane_archetype } plane_archetype = { is_archetype = yes } }"
            ],
            [localisation],
        )
        == expected
    )


_NAMED_VARIANT_CONSUMERS = {
    "air wing": (
        '696 = { medium_plane_airframe_1 = { owner = "UKR" creator = "SOV" '
        'amount = 12 version_name = "MiG-X" } }'
    ),
    "forced equipment": (
        "division = { force_equipment_variants = { medium_plane_airframe_1 = "
        '{ owner = UKR creator = SOV version_name = "MiG-X" } } }'
    ),
    "serialized forced equipment": (
        'create_unit = { division = "division_template = \\"Air\\" '
        "start_equipment_factor = 1 force_equipment_variants = { "
        "medium_plane_airframe_1 = { owner = UKR creator = SOV "
        'version_name = \\"MiG-X\\" } }" owner = ROOT }'
    ),
    "stockpile": (
        "add_equipment_to_stockpile = { type = medium_plane_airframe_1 "
        'variant_name = "MiG-X" amount = 12 producer = SOV }'
    ),
    "production version": (
        "add_equipment_production = { equipment = { type = medium_plane_airframe_1 "
        'creator = "SOV" version_name = "MiG-X" } amount = 12 }'
    ),
    "production variant with outer producer": (
        "add_equipment_production = { producer = SOV equipment = { "
        'type = medium_plane_airframe_1 variant_name = "MiG-X" } amount = 12 }'
    ),
}

# check: (consumer text, producer definition sources, (kind, line, message fragments))
_NAMED_VARIANT_CASES = {
    "air wing matches producer type and name": (
        _NAMED_VARIANT_CONSUMERS["air wing"],
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "air wing reports medium subtype mismatch": (
        '696 = { medium_plane_fighter_airframe_1 = { owner = "UKR" creator = "SOV" '
        'amount = 12 version_name = "MiG-X" } }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [
            (
                "wrong_variant_type",
                1,
                (
                    "SOV",
                    "MiG-X",
                    "medium_plane_airframe_1",
                    "medium_plane_fighter_airframe_1",
                ),
            )
        ],
    ),
    "air wing reports small versus medium mismatch": (
        '696 = { small_plane_airframe_1 = { owner = "UKR" creator = "SOV" '
        'amount = 12 version_name = "MiG-X" } }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [
            (
                "wrong_variant_type",
                1,
                ("medium_plane_airframe_1", "small_plane_airframe_1"),
            )
        ],
    ),
    "creator selects producer instead of owner": (
        '696 = { medium_plane_airframe_1 = { owner = "UKR" creator = "SOV" '
        'amount = 12 version_name = "MiG-X" } }',
        [
            _variant_source("SOV", _MIG_VARIANTS),
            _variant_source("UKR", [("medium_plane_fighter_airframe_1", "MiG-X")]),
        ],
        [],
    ),
    "name under owner does not satisfy producer": (
        "add_equipment_to_stockpile = { type = medium_plane_airframe_1 "
        'variant_name = "MiG-X" amount = 12 producer = SIA owner = UKR }',
        [_variant_source("UKR", _MIG_VARIANTS)],
        [("unknown_named_variant", 1, ("SIA", "MiG-X", "medium_plane_airframe_1"))],
    ),
    "same name under another producer does not mask wrong type": (
        "add_equipment_to_stockpile = { type = medium_plane_fighter_airframe_1 "
        'variant_name = "MiG-X" amount = 12 producer = SOV }',
        [
            _variant_source("SOV", _MIG_VARIANTS),
            _variant_source("UKR", [("medium_plane_fighter_airframe_1", "MiG-X")]),
        ],
        [
            (
                "wrong_variant_type",
                1,
                (
                    "SOV",
                    "MiG-X",
                    "medium_plane_airframe_1",
                    "medium_plane_fighter_airframe_1",
                ),
            )
        ],
    ),
    "force equipment variants resolves literal entry": (
        _NAMED_VARIANT_CONSUMERS["forced equipment"],
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "force equipment variant reports a subtype mismatch": (
        "division = { force_equipment_variants = { small_plane_airframe_1 = "
        '{ owner = UKR creator = SOV version_name = "MiG-X" } } }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [
            (
                "wrong_variant_type",
                1,
                ("medium_plane_airframe_1", "small_plane_airframe_1"),
            )
        ],
    ),
    "serialized create unit force equipment variant resolves": (
        _NAMED_VARIANT_CONSUMERS["serialized forced equipment"],
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "serialized create unit variant reports wrong subtype": (
        'create_unit = { division = "division_template = \\"Air\\" '
        "start_equipment_factor = 1 force_equipment_variants = { "
        "small_plane_airframe_1 = { owner = UKR creator = SOV "
        'version_name = \\"MiG-X\\" } }" owner = ROOT }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [
            (
                "wrong_variant_type",
                1,
                ("medium_plane_airframe_1", "small_plane_airframe_1"),
            )
        ],
    ),
    "stockpile variant name resolves": (
        _NAMED_VARIANT_CONSUMERS["stockpile"],
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "production version name resolves": (
        _NAMED_VARIANT_CONSUMERS["production version"],
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "production reports a subtype mismatch": (
        "add_equipment_production = { equipment = { type = small_plane_airframe_1 "
        'creator = SOV version_name = "MiG-X" } amount = 12 }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [
            (
                "wrong_variant_type",
                1,
                ("medium_plane_airframe_1", "small_plane_airframe_1"),
            )
        ],
    ),
    "production variant name uses outer producer": (
        _NAMED_VARIANT_CONSUMERS["production variant with outer producer"],
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "unresolved literal name is reported": (
        "add_equipment_to_stockpile = { type = medium_plane_airframe_1 "
        'variant_name = "Ghost" amount = 12 producer = SOV }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [("unknown_named_variant", 1, ("SOV", "Ghost", "medium_plane_airframe_1"))],
    ),
    "comments and dynamic names are ignored": (
        '# medium_plane_airframe_1 = { creator = SOV version_name = "Ghost" }\n'
        "add_equipment_to_stockpile = { type = medium_plane_airframe_1 "
        'variant_name = "[ROOT.GetName]" amount = 12 producer = SOV }\n'
        "add_equipment_to_stockpile = { type = medium_plane_airframe_1 "
        'variant_name = "$dynamic_variant$" amount = 12 producer = SOV }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "dynamic producer and type are ignored": (
        "add_equipment_to_stockpile = { type = var:equipment "
        'variant_name = "MiG-X" amount = 12 producer = ROOT.id }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "dynamic creator does not fall back to literal wing owner": (
        "696 = { small_plane_airframe_1 = { creator = ROOT owner = SOV "
        'version_name = "MiG-X" amount = 1 } }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "dynamic creator does not fall back to forced equipment owner": (
        "force_equipment_variants = { small_plane_airframe_1 = { "
        'creator = event_target:producer owner = SOV version_name = "MiG-X" } }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "dynamic production creator does not fall back to outer producer": (
        "add_equipment_production = { producer = SOV equipment = { "
        'creator = ROOT type = small_plane_airframe_1 version_name = "MiG-X" } }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
    "same producer can define the same name on multiple types": (
        "add_equipment_to_stockpile = { type = small_plane_airframe_1 "
        'variant_name = "MiG-X" amount = 1 producer = SOV }',
        [_variant_source("SOV", _MIG_VARIANTS + [("small_plane_airframe_1", "MiG-X")])],
        [],
    ),
    "unscoped effect definition does not prove a producer type mismatch": (
        "add_equipment_to_stockpile = { type = medium_plane_airframe_1 "
        'variant_name = "MiG-X" amount = 12 producer = SOV }',
        [
            _variant_source("SOV", []),
            (
                "events/Some Event.txt",
                created_variant_spans(
                    'create_equipment_variant = { name = "MiG-X" type = small_plane_airframe_1 }'
                ),
            ),
        ],
        [],
    ),
    "AI target variant design is not a history reference": (
        "target_variant = { type = medium_plane_fighter_airframe_1 " 'name = "MiG-X" }',
        [_variant_source("SOV", _MIG_VARIANTS)],
        [],
    ),
}


@pytest.mark.parametrize(
    "content, sources, expected",
    _NAMED_VARIANT_CASES.values(),
    ids=_NAMED_VARIANT_CASES,
)
def test_named_variant_refs(content, sources, expected):
    by_tag, wildcard = build_variant_name_index(sources)
    findings = check_named_variant_refs(
        content,
        by_tag,
        wildcard,
        variant_registry=build_variant_registry(sources),
    )

    assert len(findings) == len(expected)
    assert [
        (
            finding.kind,
            finding.line,
            all(fragment in finding.message for fragment in fragments),
        )
        for finding, (kind, line, fragments) in zip(findings, expected)
    ] == [(kind, line, True) for kind, line, _ in expected]


@pytest.mark.parametrize(
    "content", _NAMED_VARIANT_CONSUMERS.values(), ids=_NAMED_VARIANT_CONSUMERS
)
@pytest.mark.parametrize(
    "definition", ["explicit", "country default", "generic default"]
)
@pytest.mark.parametrize(
    "wrong_type", [False, True], ids=["matching type", "wrong type"]
)
def test_named_variant_identity_across_consumers(
    tmp_path, content, definition, wrong_type
):
    requested_type = (
        "small_plane_airframe_1" if wrong_type else "medium_plane_airframe_1"
    )
    history = (
        'create_equipment_variant = { name = "MiG-X" type = transport_helicopter_1 }'
    )
    localisation = "l_english:\n"
    if definition == "explicit":
        history += '\ncreate_equipment_variant = { name = "MiG-X" type = medium_plane_airframe_1 }'
    else:
        prefix = "SOV_" if definition == "country default" else ""
        localisation += f' {prefix}medium_plane_airframe_1: "MiG-X"\n'
    consumer_path = "history/units/UKR_2000_bba.txt"
    write_tree(
        tmp_path,
        {
            "common/units/equipment/planes.txt": (
                "equipments = { medium_plane_airframe_1 = {} "
                "small_plane_airframe_1 = {} transport_helicopter_1 = {} }"
            ),
            "history/countries/SOV - Russia.txt": history,
            "localisation/english/nested/equipment_l_english.yml": localisation,
            "localisation/english/nested/other_l_english.yml": 'l_english:\n UKR_medium_plane_airframe_1: "Other producer"\n',
            "localisation/french/equipment_l_french.yml": 'l_french:\n SOV_small_plane_airframe_1: "MiG-X"\n',
            consumer_path: content.replace("medium_plane_airframe_1", requested_type),
        },
    )
    validator = _validator(tmp_path, staged_only=True)
    validator.staged_files = [str(tmp_path / consumer_path)]
    validator.validate_oob_variant_references()

    assert validator.warnings_found == 0
    assert validator.errors_found == int(wrong_type)
    assert [
        (issue.category, issue.file, issue.line, issue.severity)
        for issue in validator._issues
    ] == (
        [
            (
                "NAMED VARIANT: name exists for a different equipment type",
                consumer_path,
                1,
                "error",
            )
        ]
        if wrong_type
        else []
    )


# case: (default name keys, explicit variants, expected finding kinds)
_DEFAULT_VARIANT_CASES = {
    "producer default resolves": ({"SOV_medium_plane_airframe_1": "MiG-X"}, [], []),
    "generic default resolves without a country override": (
        {"medium_plane_airframe_1": "MiG-X"},
        [],
        [],
    ),
    "another producer does not satisfy the name": (
        {"UKR_medium_plane_airframe_1": "MiG-X"},
        [],
        ["wrong_variant_type"],
    ),
    "another type does not satisfy the name": (
        {"SOV_small_plane_airframe_1": "MiG-X"},
        [],
        ["wrong_variant_type"],
    ),
    "country name overrides generic name": (
        {"medium_plane_airframe_1": "MiG-X", "SOV_medium_plane_airframe_1": "Other"},
        [],
        ["wrong_variant_type"],
    ),
    "names remain case sensitive": (
        {"SOV_medium_plane_airframe_1": "mig-X"},
        [],
        ["wrong_variant_type"],
    ),
    "two default equipment types can share a name": (
        {"SOV_medium_plane_airframe_1": "MiG-X", "SOV_small_plane_airframe_1": "MiG-X"},
        [],
        [],
    ),
    "explicit variant still resolves beside a different default": (
        {"SOV_medium_plane_airframe_1": "Other"},
        _MIG_VARIANTS,
        [],
    ),
}


@pytest.mark.parametrize(
    "defaults, variants, expected",
    _DEFAULT_VARIANT_CASES.values(),
    ids=_DEFAULT_VARIANT_CASES,
)
@pytest.mark.parametrize("contextual", [False, True])
def test_named_variant_default_identity(defaults, variants, expected, contextual):
    sources = [_variant_source("SOV", [("transport_helicopter_1", "MiG-X"), *variants])]
    by_tag, wildcard = build_variant_name_index(sources)
    findings = check_named_variant_refs(
        _NAMED_VARIANT_CONSUMERS["stockpile"],
        by_tag,
        wildcard,
        variant_registry=build_variant_registry(sources) if contextual else None,
        default_equipment_names=defaults,
    )
    assert [finding.kind for finding in findings] == expected


def test_named_variant_refs_respect_dlc_country_context():
    source = (
        "history/countries/SOV - Russia.txt",
        created_variant_spans(
            'if = { limit = { has_dlc = "By Blood Alone" } '
            'create_equipment_variant = { name = "MiG-X" '
            "type = medium_plane_airframe_1 } else = { "
            'create_equipment_variant = { name = "MiG-X" '
            "type = small_plane_airframe_1 } } }"
        ),
    )
    by_tag, wildcard = build_variant_name_index([source])
    context_index = build_variant_registry([source])
    content = (
        "add_equipment_to_stockpile = { type = small_plane_airframe_1 "
        'variant_name = "MiG-X" amount = 12 producer = SOV }'
    )

    assert (
        check_named_variant_refs(
            content,
            by_tag,
            wildcard,
            source_path="history/units/UKR_2000_nonbba.txt",
            variant_registry=context_index,
        )
        == []
    )
    assert (
        check_named_variant_refs(
            content,
            by_tag,
            wildcard,
            source_path="history/units/UKR_2000_bba.txt",
            variant_registry=context_index,
        )[0].kind
        == "wrong_variant_type"
    )


def _archetype_message(producer):
    return (
        f"'convoy' is an archetype but is attributed to {producer}, "
        "name the concrete equipment instead"
    )


# case: (production content, finding messages)
_ARCHETYPE_CASES = {
    "production line with a creator": (
        "units = {\n"
        "\tadd_equipment_production = {\n"
        '\t\tequipment = { type = convoy creator = "SIA" }\n'
        "\t\trequested_factories = 1\n"
        "\t}\n"
        "}",
        [_archetype_message("SIA")],
    ),
    "stockpile with a producer": (
        "add_equipment_to_stockpile = { type = convoy amount = 40 producer = GRE }",
        [_archetype_message("GRE")],
    ),
    "production line without an equipment type": (
        "add_equipment_production = {\n\tproducer = SWE\n\tamount = 10\n}\n",
        [],
    ),
    "concrete equipment with a producer": (
        "add_equipment_to_stockpile = { type = convoy_1 amount = 40 producer = GRE }",
        [],
    ),
    # calculate_starting_utility_stockpile grants the archetype unattributed.
    "archetype without a producer": (
        "add_equipment_to_stockpile = { type = convoy amount = dockyard_increase }",
        [],
    ),
    "commented-out production line": (
        '#\tadd_equipment_production = { equipment = { type = convoy creator = "SIA" } }',
        [],
    ),
}


@pytest.mark.parametrize(
    "content, expected", _ARCHETYPE_CASES.values(), ids=_ARCHETYPE_CASES
)
def test_attributed_archetypes(content, expected):
    findings = check_attributed_archetypes(content, {"convoy"})
    assert [finding.message for finding in findings] == expected


_FRIGATES = """equipments = {
\tship_hull_frigate = {
\t\tis_archetype = yes
\t\ttype = { naval }
\t\tmodule_slots = {
\t\t}
\t}
\tfrigate_hull_2 = {
\t\tarchetype = ship_hull_frigate
\t\tmodule_slots = inherit
\t}
}
"""
_SWE_HISTORY = "history/countries/SWE - Sweden.txt"
_SWE_VARIANT = (
    'create_equipment_variant = {\n\tname = "Naresuan Class"\n'
    "\ttype = frigate_hull_2\n}\n"
)
_SWE_SHIP = {"owner": "SWE", "creator": "SWE"}

# case: (files beside the frigates and SWE's variant, (category, message) per finding)
_VARIANT_REFERENCE_RUN_CASES = {
    "ship version_name without a variant": (
        {
            "history/units/SWE_1990.txt": _ship(
                "frigate_hull_2", "Ghost Class", **_SWE_SHIP
            ),
            "history/units/SWE_army.txt": "units = {\n}\n",
        },
        [
            (
                "OOB SHIP: version_name has no matching equipment variant",
                _fallback("SWE", "frigate_hull_2", "Ghost Class"),
            )
        ],
    ),
    "ship version_name with a variant": (
        {
            "history/units/SWE_1990.txt": _ship(
                "frigate_hull_2", "Naresuan Class", **_SWE_SHIP
            )
        },
        [],
    ),
    "production line naming an archetype": (
        {
            _SWE_HISTORY: _SWE_VARIANT + "add_equipment_production = {\n"
            '\tequipment = {\n\t\ttype = ship_hull_frigate\n\t\tcreator = "SWE"\n\t}\n'
            "\trequested_factories = 1\n"
            "}\n"
        },
        [
            (
                "PRODUCTION: archetype attributed to a producer",
                "'ship_hull_frigate' is an archetype but is attributed to SWE, "
                "name the concrete equipment instead",
            )
        ],
    ),
    "stockpile uses a default without any explicit variants": (
        {
            _SWE_HISTORY: "",
            "localisation/english/equipment_l_english.yml": 'l_english:\n SWE_frigate_hull_2: "Base Class"\n',
            "history/units/SWE_2000_nsb.txt": (
                "add_equipment_to_stockpile = { type = frigate_hull_2 "
                'variant_name = "Base Class" producer = SWE amount = 1 }'
            ),
        },
        [],
    ),
    "stockpile name on the wrong equipment type": (
        {
            "history/units/SWE_2000_nsb.txt": (
                "add_equipment_to_stockpile = { type = destroyer_hull_2 "
                'variant_name = "Naresuan Class" producer = SWE amount = 1 }'
            )
        },
        [
            (
                "NAMED VARIANT: name exists for a different equipment type",
                'SWE defines named variant "Naresuan Class" for frigate_hull_2, '
                "not requested equipment type destroyer_hull_2",
            )
        ],
    ),
}


@pytest.mark.parametrize(
    "files, expected",
    _VARIANT_REFERENCE_RUN_CASES.values(),
    ids=_VARIANT_REFERENCE_RUN_CASES,
)
def test_oob_variant_references(tmp_path, files, expected):
    write_tree(
        tmp_path,
        {
            "common/units/equipment/MD_ships.txt": _FRIGATES,
            _SWE_HISTORY: _SWE_VARIANT,
            **files,
        },
    )
    validator = _validator(tmp_path)
    validator.validate_oob_variant_references()

    assert validator.errors_found == len(expected)
    assert [(issue.category, issue.message) for issue in validator._issues] == expected
    assert all(issue.severity == "error" for issue in validator._issues)


_DEFAULT_SHIP_LOC = 'l_english:\n SWE_frigate_hull_2: "Naresuan Class"\n'
_DEFAULT_SHIP_LOC_PATH = "localisation/english/equipment_l_english.yml"
_SHIP_EQUIPMENT_PATH = "common/units/equipment/MD_ships.txt"

# case: (definition path, original definition, replacement or deletion, category, severity)
_STAGED_VARIANT_DEFINITION_CASES = {
    "staged rename": (
        _SWE_HISTORY,
        _SWE_VARIANT,
        'create_equipment_variant = { name = "Renamed Class" type = frigate_hull_2 }',
        "NAMED VARIANT: unresolved producer, type, and name",
        "warning",
    ),
    "staged type change": (
        _SWE_HISTORY,
        _SWE_VARIANT,
        _SWE_VARIANT.replace("frigate_hull_2", "destroyer_hull_2"),
        "NAMED VARIANT: name exists for a different equipment type",
        "error",
    ),
    "default name rename": (
        _DEFAULT_SHIP_LOC_PATH,
        _DEFAULT_SHIP_LOC,
        _DEFAULT_SHIP_LOC.replace("Naresuan Class", "Renamed Class"),
        "NAMED VARIANT: name exists for a different equipment type",
        "error",
    ),
    "default name deletion": (
        _DEFAULT_SHIP_LOC_PATH,
        _DEFAULT_SHIP_LOC,
        None,
        "NAMED VARIANT: name exists for a different equipment type",
        "error",
    ),
    "default equipment deletion": (
        _SHIP_EQUIPMENT_PATH,
        _FRIGATES,
        None,
        "NAMED VARIANT: name exists for a different equipment type",
        "error",
    ),
}


@pytest.mark.parametrize(
    "definition_path, original, updated, expected_category, expected_severity",
    _STAGED_VARIANT_DEFINITION_CASES.values(),
    ids=_STAGED_VARIANT_DEFINITION_CASES,
)
def test_staged_variant_definition_change_rescans_unchanged_consumers(
    tmp_path,
    monkeypatch,
    definition_path,
    original,
    updated,
    expected_category,
    expected_severity,
):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    consumer_path = "history/units/SWE_2000_nsb.txt"
    write_tree(
        tmp_path,
        {
            _SWE_HISTORY: _SWE_VARIANT.replace("frigate_hull_2", "destroyer_hull_2"),
            _SHIP_EQUIPMENT_PATH: _FRIGATES,
            _DEFAULT_SHIP_LOC_PATH: (
                _DEFAULT_SHIP_LOC if definition_path != _SWE_HISTORY else "l_english:\n"
            ),
            consumer_path: "add_equipment_to_stockpile = { type = frigate_hull_2 "
            'variant_name = "Naresuan Class" producer = SWE amount = 1 }',
            definition_path: original,
        },
    )
    initialize_git_repository(tmp_path, "history", "common", "localisation")
    if updated is None:
        (tmp_path / definition_path).unlink()
    else:
        _write(tmp_path, definition_path, updated)
    run_git(tmp_path, "add", definition_path)
    monkeypatch.setenv("MD_STAGED_FILES", definition_path)

    validator = _validator(tmp_path, staged_only=True)
    validator.validate_oob_variant_references()

    assert [
        (issue.category, issue.file, issue.line, issue.severity)
        for issue in validator._issues
    ] == [(expected_category, consumer_path, 1, expected_severity)]


@pytest.mark.parametrize("change", ["rename", "type", "delete"])
def test_staged_variant_definition_change_rescans_unchanged_ship(
    tmp_path, monkeypatch, change
):
    variant_path = _SWE_HISTORY
    consumer_path = "history/units/SWE_2000_naval_mtg.txt"
    write_tree(
        tmp_path,
        {
            variant_path: _SWE_VARIANT,
            consumer_path: _ship("frigate_hull_2", "Naresuan Class", **_SWE_SHIP),
        },
    )
    initialize_git_repository(tmp_path, "history/countries", "history/units")
    if change == "delete":
        (tmp_path / variant_path).unlink()
    else:
        _write(
            tmp_path,
            variant_path,
            _SWE_VARIANT.replace(
                "Naresuan Class" if change == "rename" else "frigate_hull_2",
                "Renamed Class" if change == "rename" else "destroyer_hull_2",
            ),
        )
    run_git(tmp_path, "add", variant_path)
    monkeypatch.setenv("MD_STAGED_FILES", variant_path)

    validator = _validator(tmp_path, staged_only=True)
    validator.validate_oob_variant_references()

    assert [
        (issue.category, issue.file, issue.severity) for issue in validator._issues
    ] == [
        (
            "OOB SHIP: version_name has no matching equipment variant",
            consumer_path,
            "error",
        )
    ]


_EVENT_VARIANT_PATH = "events/Purchase.txt"
_SCOPED_VARIANT = "SWE = {\n" + _SWE_VARIANT + "}\n"
_DLC_VARIANT = 'if = { limit = { has_dlc = "Man the Guns" }\n' + _SCOPED_VARIANT + "}\n"

# case: (original sources, replacement sources, rescan unchanged consumers)
_STAGED_VARIANT_SCOPE_CASES = {
    "unrelated edit without variants": (
        {_EVENT_VARIANT_PATH: "add_political_power = 1\n"},
        {_EVENT_VARIANT_PATH: "add_political_power = 2\n"},
        False,
    ),
    "unrelated edit beside a variant": (
        {_EVENT_VARIANT_PATH: _SCOPED_VARIANT + "add_political_power = 1\n"},
        {_EVENT_VARIANT_PATH: _SCOPED_VARIANT + "add_political_power = 2\n"},
        False,
    ),
    "comment inside a variant": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {_SWE_HISTORY: _SWE_VARIANT.replace("type =", "# a comment\n\ttype =")},
        False,
    ),
    "whitespace inside a variant": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {_SWE_HISTORY: _SWE_VARIANT.replace("\t", "    ")},
        False,
    ),
    "module edit preserves variant identity": (
        {_SWE_HISTORY: _SWE_VARIANT.replace("\n}", "\nmodules = { engine = old }\n}")},
        {_SWE_HISTORY: _SWE_VARIANT.replace("\n}", "\nmodules = { engine = new }\n}")},
        False,
    ),
    "variant name edit": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {_SWE_HISTORY: _SWE_VARIANT.replace("Naresuan Class", "Renamed Class")},
        True,
    ),
    "variant type edit": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {_SWE_HISTORY: _SWE_VARIANT.replace("frigate_hull_2", "destroyer_hull_2")},
        True,
    ),
    "variant addition": (
        {_EVENT_VARIANT_PATH: "add_political_power = 1\n"},
        {_EVENT_VARIANT_PATH: _SCOPED_VARIANT},
        True,
    ),
    "variant block deletion": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {_SWE_HISTORY: "add_political_power = 1\n"},
        True,
    ),
    "variant file deletion": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {},
        True,
    ),
    "variant file addition": (
        {},
        {_SWE_HISTORY: _SWE_VARIANT},
        True,
    ),
    "producer scope edit": (
        {_EVENT_VARIANT_PATH: _SCOPED_VARIANT},
        {_EVENT_VARIANT_PATH: _SCOPED_VARIANT.replace("SWE =", "CHI =")},
        True,
    ),
    "DLC condition edit": (
        {_EVENT_VARIANT_PATH: _DLC_VARIANT},
        {_EVENT_VARIANT_PATH: _DLC_VARIANT.replace("Man the Guns", "By Blood Alone")},
        True,
    ),
    "history date edit": (
        {_SWE_HISTORY: "2000.1.1 = {\n" + _SWE_VARIANT + "}\n"},
        {_SWE_HISTORY: "2017.1.1 = {\n" + _SWE_VARIANT + "}\n"},
        True,
    ),
    "file rename changes producer": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {"history/countries/NOR - Norway.txt": _SWE_VARIANT},
        True,
    ),
    "file rename preserves producer": (
        {_SWE_HISTORY: _SWE_VARIANT},
        {"history/countries/SWE - Renamed.txt": _SWE_VARIANT},
        False,
    ),
}


@pytest.mark.parametrize("scope", ["staged", "branch"])
@pytest.mark.parametrize(
    "original, updated, rescan",
    _STAGED_VARIANT_SCOPE_CASES.values(),
    ids=_STAGED_VARIANT_SCOPE_CASES,
)
def test_staged_variant_reference_scope(
    tmp_path, monkeypatch, original, updated, rescan, scope
):
    consumer_path = "history/units/SWE_2000_nsb.txt"
    write_tree(
        tmp_path,
        {
            consumer_path: "add_equipment_to_stockpile = { type = frigate_hull_2 "
            'variant_name = "Missing Class" producer = SWE amount = 1 }',
            **original,
        },
    )
    initialize_git_repository(tmp_path, ".")
    run_git(tmp_path, "branch", "-M", "main")
    run_git(tmp_path, "switch", "-c", "feature")
    for path in original.keys() - updated.keys():
        (tmp_path / path).unlink()
    write_tree(tmp_path, updated)
    run_git(tmp_path, "add", ".")
    if scope == "branch":
        run_git(tmp_path, "commit", "-m", "change sources")
    monkeypatch.setenv(
        "MD_STAGED_FILES", "\n".join(dict.fromkeys([*original, *updated]))
    )

    validator = _validator(tmp_path, staged_only=True)
    validator.validate_oob_variant_references()

    assert [issue.file for issue in validator._issues] == (
        [consumer_path] if rescan else []
    )


def test_unresolved_named_variant_is_reported_as_warning(tmp_path):
    consumer_path = "history/units/SWE_2000_nsb.txt"
    write_tree(
        tmp_path,
        {
            _SWE_HISTORY: _SWE_VARIANT,
            consumer_path: (
                "add_equipment_to_stockpile = { type = frigate_hull_2 "
                'variant_name = "Unknown Class" producer = SWE amount = 1 }'
            ),
        },
    )
    validator = _validator(tmp_path)
    validator.validate_oob_variant_references()

    assert validator.errors_found == 0
    assert validator.warnings_found == 1
    assert validator._issues[0].message == (
        'Unresolved named variant "Unknown Class" for producer SWE '
        "and equipment type frigate_hull_2"
    )
    assert [
        (issue.category, issue.file, issue.line, issue.severity)
        for issue in validator._issues
    ] == [
        (
            "NAMED VARIANT: unresolved producer, type, and name",
            consumer_path,
            1,
            "warning",
        )
    ]


def test_staged_event_without_unit_constructs_skips_variant_indexes(
    tmp_path, monkeypatch
):
    (tmp_path / "common/units/equipment").mkdir(parents=True)
    event = _write(tmp_path, "events/Algeria.txt", "country_event = { id = foo.1 }\n")

    def _boom(*_args, **_kwargs):
        raise AssertionError("full-repo OOB index should be skipped")

    monkeypatch.setenv("MD_STAGED_FILES", "events/Algeria.txt")
    monkeypatch.setattr("validate_oob_units.build_variant_name_index", _boom)
    monkeypatch.setattr("validate_oob_units.build_division_template_index", _boom)
    monkeypatch.setattr("validate_oob_units.build_equipment_index", _boom)
    validator = _validator(tmp_path, staged_only=True)
    validator.staged_files = [str(event)]
    validator.validate_oob_variant_references()
    validator.validate_created_units()
    validator.validate_created_variant_modules()
    assert validator._issues == []


# --- load_oob ---------------------------------------------------------------

_LOAD_OOB_EDGES = (
    'load_oob = "TST_2000"\n# load_oob = GHOST\nx = { load_oob="TST_late" }'
)


@pytest.mark.parametrize(
    "content, refs",
    [
        (
            "# load_oob = ignored\n"
            'load_oob = "quoted"\n'
            "load_oob = bare\n"
            'load_oob = "[ROOT.GetTag]_reinforcements"\n'
            "load_oob = $runtime_target$\n",
            [("quoted", 2), ("bare", 3)],
        ),
        (_LOAD_OOB_EDGES, [("TST_2000", 1), ("TST_late", 3)]),
        (_LOAD_OOB_EDGES.replace("\n", "\r\n"), [("TST_2000", 1), ("TST_late", 3)]),
    ],
    ids=["comments and dynamic targets", "first and last lines", "crlf"],
)
def test_find_load_oob_references(content, refs):
    assert find_load_oob_references(content) == refs


def _missing_oob(target):
    return (
        f'load_oob references "{target}", but no history/units/{target}.txt file exists'
    )


# case: (files, MD_STAGED_FILES or None for a full run, (file, line, message) per finding)
_LOAD_OOB_CASES = {
    "missing target": (
        {
            "history/units/present.txt": "units = { }\n",
            "events/test.txt": 'load_oob = "present"\nload_oob = missing\n',
        },
        None,
        [("events/test.txt", 2, _missing_oob("missing"))],
    ),
    "staged target rescans every caller": (
        {"events/unchanged.txt": "load_oob = removed\n"},
        "history/units/removed.txt",
        [("events/unchanged.txt", 1, _missing_oob("removed"))],
    ),
    "staged caller without a target change": (
        {
            "events/changed.txt": "load_oob = missing\n",
            "events/unchanged.txt": "load_oob = also_missing\n",
        },
        "events/changed.txt",
        [("events/changed.txt", 1, _missing_oob("missing"))],
    ),
}


@pytest.mark.parametrize(
    "files, staged, expected", _LOAD_OOB_CASES.values(), ids=_LOAD_OOB_CASES
)
def test_load_oob_references(tmp_path, monkeypatch, files, staged, expected):
    write_tree(tmp_path, files)
    if staged:
        monkeypatch.setenv("MD_STAGED_FILES", staged)
    validator = _validator(tmp_path, staged_only=bool(staged))
    validator.validate_load_oob_references()

    assert [
        (issue.category, issue.file, issue.line, issue.message)
        for issue in validator._issues
    ] == [("unknown-load-oob", *finding) for finding in expected]


def test_full_validator_rescans_unchanged_callers_when_a_target_moves(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    target = _write(tmp_path, "history/units/target.txt", "units = { }\n")
    _write(tmp_path, "events/unchanged.txt", "load_oob = target\n")

    initialize_git_repository(tmp_path, "history/units", "events")
    target.rename(tmp_path / "target.txt")
    run_git(tmp_path, "add", "-A")
    monkeypatch.setenv("MD_STAGED_FILES", "target.txt")

    validator = _validator(tmp_path, staged_only=True)
    validator.run_validations()

    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("unknown-load-oob", "events/unchanged.txt", 1)]


# --- block tree and scanners ------------------------------------------------


def _shape(text):
    return [(n["label"], n["line"], n["parent"]) for n in _build_block_nodes(text)]


# case: (text, (label, line, parent) per block)
_BLOCK_TREE_CASES = {
    "first line to an unterminated last line": (
        "a = {\n\tb = { }\n}\nc = { d = { } }",
        [("a", 1, -1), ("b", 2, 0), ("c", 4, -1), ("d", 4, 2)],
    ),
    "quoted braces and escaped quotes": (
        'a = {\n\tlog = "x { ' + _BS + '" } #"\n\tb = { }\n}\n',
        [("a", 1, -1), ("b", 3, 0)],
    ),
    "unclosed quote ends at the line break": (
        'a = {\n\tname = "open\n\tb = { }\n}\n',
        [("a", 1, -1), ("b", 3, 0)],
    ),
    "brace on the next line": (
        "a =\n{\n\tb = { }\n}\nc = { }",
        [("a", 2, -1), ("b", 3, 0), ("c", 5, -1)],
    ),
    "crlf": (
        "a =\r\n{\r\n\tb = { }\r\n}\r\nc = { }",
        [("a", 2, -1), ("b", 3, 0), ("c", 5, -1)],
    ),
    "block without a key": ("outer = { { } }", [("outer", 1, -1), (None, 1, 0)]),
}


@pytest.mark.parametrize(
    "text, expected", _BLOCK_TREE_CASES.values(), ids=_BLOCK_TREE_CASES
)
def test_block_tree(text, expected):
    assert _shape(text) == expected


def _index_of(nodes, label):
    return next(i for i, node in enumerate(nodes) if node["label"] == label)


_NESTED = "outer = { inner = { } }"
_IF_BEFORE_OUTER = "if = { limit = { } }\nouter = { inner = { } }"

# case: (text, probe on its block nodes, result)
_BLOCK_HELPER_CASES = {
    "top-level block has no container": (
        _NESTED,
        lambda nodes: [_container_for(nodes, 0), _container_for(nodes, 1)],
        [-1, 0],
    ),
    "no node outside every block": (
        _NESTED,
        lambda nodes: _deepest_node_at(nodes, 0),
        -1,
    ),
    "no if encloses the node": (_NESTED, lambda nodes: _closest_if(nodes, 1), -1),
    "if that does not enclose the node is not its guard": (
        _IF_BEFORE_OUTER,
        lambda nodes: _is_positive_if_limit_condition(
            nodes, _index_of(nodes, "inner"), _index_of(nodes, "if")
        ),
        False,
    ),
    "node outside an if is not in its true branch": (
        _IF_BEFORE_OUTER,
        lambda nodes: _runs_in_if_true_branch(
            nodes, _index_of(nodes, "inner"), _index_of(nodes, "if")
        ),
        False,
    ),
    "ROOT resets the country scope path": (
        "SWE = { ROOT = { capital_scope = { } } }",
        lambda nodes: _country_scope_path(nodes, _index_of(nodes, "capital_scope")),
        ("ROOT",),
    ),
}


@pytest.mark.parametrize(
    "text, probe, expected",
    _BLOCK_HELPER_CASES.values(),
    ids=_BLOCK_HELPER_CASES,
)
def test_block_helpers(text, probe, expected):
    assert probe(_build_block_nodes(text)) == expected


@pytest.mark.parametrize(
    "label, scope",
    [
        ("123", None),
        ("NOT", None),
        ("SWE", "SWE"),
        ("event_target:ally", "event_target:ally"),
    ],
)
def test_scope_label(label, scope):
    assert _scope_label(label) == scope


# case: ([(path, content or None for a missing file)], effect -> template names)
_EFFECT_CLOSURE_CASES = {
    "unknown calls and empty files": (
        [
            ("common/scripted_effects/empty.txt", ""),
            (
                "common/scripted_effects/md.txt",
                "ensure_militia = {\n"
                '\tdivision_template = { name = "Militia" }\n'
                "\tsome_effect_defined_elsewhere = yes\n"
                "}\n",
            ),
        ],
        {"ensure_militia": frozenset({"Militia"})},
    ),
    "only top-level effects are keys": (
        [
            (
                "common/scripted_effects/tst.txt",
                "# commented_effect = { }\n"
                '{ stray = { has_template = "Stray" } }\n'
                "ensure_guard = {\n"
                "\tinner_effect = {\n"
                '\t\tdivision_template = { name = "Guard" }\n'
                "\t}\n"
                "\tcall_other = yes\n"
                "}\n"
                'call_other = {\n\tif = { limit = { has_template = "Other" } }\n}',
            )
        ],
        {
            "ensure_guard": frozenset({"Guard", "Other"}),
            "call_other": frozenset({"Other"}),
        },
    ),
}


@pytest.mark.parametrize(
    "files, expected", _EFFECT_CLOSURE_CASES.values(), ids=_EFFECT_CLOSURE_CASES
)
def test_effect_template_closure(tmp_path, files, expected):
    paths = [str(_write(tmp_path, rel, content)) for rel, content in files]
    assert _effect_template_closure(str(tmp_path), paths) == expected


# case: ([(path, content or None for a missing file)], deleted template names)
_DELETED_NAME_CASES = {
    "unreadable file and nameless block": (
        [
            ("gone.txt", None),
            (
                "common/ideas/md.txt",
                "delete_unit_template_and_units = {\n\t\tdisband = yes\n}\n"
                "delete_unit_template_and_units = {\n"
                '\t\tdivision_template = "Militia"\n'
                "}\n",
            ),
        ],
        frozenset({"Militia"}),
    ),
    "commented-out delete": (
        [
            (
                "events/A.txt",
                "# delete_unit_template_and_units = "
                '{ division_template = "Ghost" }\n',
            ),
            (
                "events/B.txt",
                "x = { delete_unit_template_and_units = "
                '{ division_template = "Real" } }',
            ),
        ],
        frozenset({"Real"}),
    ),
}


@pytest.mark.parametrize(
    "files, expected", _DELETED_NAME_CASES.values(), ids=_DELETED_NAME_CASES
)
def test_deleted_template_names(tmp_path, files, expected):
    paths = [
        str(tmp_path / rel if content is None else _write(tmp_path, rel, content))
        for rel, content in files
    ]
    assert _deleted_template_names(str(tmp_path), paths) == expected


_TEMPLATE_SOURCE = (
    '# division_template = { name = "Commented" }\n'
    "OPR = {\n"
    '\tdivision_template = {\n\t\tname = "Guard"\n\t\tregiments = { }\n\t}\n'
    "}\n"
    'division_template = { name = "[ROOT.GetAdjective] Guard" }\n'
    'event_target:ally = { division_template = { name = "Ally" } }'
)


def test_template_entries_resolve_owners_per_file():
    assert division_template_entries(
        "common/scripted_effects/tst.txt", _TEMPLATE_SOURCE
    ) == [("Guard", "OPR"), ("Ally", None)]
    assert division_template_entries("history/units/TST.txt", _TEMPLATE_SOURCE) == [
        ("Guard", None),
        ("Ally", None),
    ]


# --- create_unit division strings and blocks --------------------------------


def _esc(value):
    return _BS + '"' + value + _BS + '"'


def _division(template: str | None = "Militia", extra=" start_equipment_factor = 1.0"):
    body = "name = " + _esc("1st Brigade")
    if template is not None:
        body += " division_template = " + _esc(template)
    return body + extra


def _fev(entry):
    return 'division_template = "Militia" force_equipment_variants = ' + entry


def _malformed(message):
    return ("malformed-division", "division string " + message)


# case: (division string, issues, template)
_DIVISION_STRING_CASES = {
    "unclosed quote after a valid pair": (
        'division_template = "Militia" "unterminated',
        [_malformed("unclosed quote")],
        "Militia",
    ),
    "leading string token": (
        '"Militia"',
        [_malformed("leftover token: Militia")],
        None,
    ),
    "key without an equals": ("name", [_malformed("leftover token: name")], None),
    "key without a value": ("name =", [_malformed("name is missing a value")], None),
    "unknown key with a block value is skipped whole": (
        'mystery = { a = { b = c } } division_template = "Militia"',
        [("unknown-division-key", "division string unknown key(s): mystery")],
        "Militia",
    ),
    "force_equipment_variants that is not a block": (
        _fev("5"),
        [_malformed("force_equipment_variants is not a block")],
        "Militia",
    ),
    "entry key that is not an identifier": (
        _fev('{ "x" = { } }'),
        [_malformed("force_equipment_variants does not parse")],
        "Militia",
    ),
    "entry without an equals": (
        _fev("{ infantry_equipment }"),
        [_malformed("force_equipment_variants does not parse")],
        "Militia",
    ),
    "entry that is not a block": (
        _fev("{ infantry_equipment = 5 }"),
        [
            _malformed("force_equipment_variants 'infantry_equipment' is not a block"),
            _malformed("force_equipment_variants does not parse"),
        ],
        "Militia",
    ),
    "entry field key that is not an identifier": (
        _fev('{ infantry_equipment = { "owner" = SWE } }'),
        [
            _malformed("force_equipment_variants 'infantry_equipment' does not parse"),
            _malformed("force_equipment_variants does not parse"),
        ],
        "Militia",
    ),
    "entry field without an equals": (
        _fev("{ infantry_equipment = { owner } }"),
        [
            _malformed("force_equipment_variants 'infantry_equipment' does not parse"),
            _malformed("leftover token: }"),
        ],
        "Militia",
    ),
    "entry field without a value": (
        _fev("{ infantry_equipment = { owner ="),
        [
            _malformed("force_equipment_variants 'infantry_equipment' does not parse"),
            _malformed("force_equipment_variants is not a block"),
        ],
        "Militia",
    ),
    "amount that is not a number": (
        _fev("{ infantry_equipment = { amount = many } }"),
        [
            _malformed(
                "force_equipment_variants 'infantry_equipment' amount must be a number"
            )
        ],
        "Militia",
    ),
    "owner that is not a tag": (
        _fev("{ infantry_equipment = { owner = 5 } }"),
        [
            _malformed(
                "force_equipment_variants 'infantry_equipment' owner must be a tag"
            )
        ],
        "Militia",
    ),
    "unclosed entry": (
        _fev("{ infantry_equipment = { owner = SWE"),
        [
            _malformed("force_equipment_variants 'infantry_equipment' is not a block"),
            _malformed("force_equipment_variants is not a block"),
        ],
        "Militia",
    ),
}


@pytest.mark.parametrize(
    "text, issues, template",
    _DIVISION_STRING_CASES.values(),
    ids=_DIVISION_STRING_CASES,
)
def test_parse_division_string(text, issues, template):
    assert _parse_division_string(text) == (issues, template)


def _template_block(name):
    return (
        "\tdivision_template = {\n"
        f'\t\tname = "{name}"\n'
        "\t\tregiments = {\n"
        "\t\t\tL_Inf_Bat = { x = 0 y = 0 }\n"
        "\t\t}\n"
        "\t}\n"
    )


def _create_unit_issues(tmp_path, content, deleted=frozenset()):
    path = _write(tmp_path, "events/TST.txt", content)
    return _check_created_units(
        (str(path), "events/TST.txt", str(tmp_path), deleted, {}, {}, frozenset())
    )


def _capital_create_unit(division, extra=""):
    return (
        "capital_scope = {\n"
        "\tcreate_unit = {\n"
        f'\t\tdivision = "{division}"\n'
        "\t\towner = ROOT\n"
        f"{extra}"
        "\t}\n"
        "}\n"
    )


# case: (content, deleted template names, (category, message) per issue)
_CREATE_UNIT_CASES = {
    "top-level create_unit": (
        f'create_unit = {{\n\tdivision = "{_division()}"\n\towner = ROOT\n}}\n',
        frozenset(),
        [
            (
                "CREATE UNIT: not in a state scope",
                "1: create_unit outside a state scope (effect does nothing at "
                "country scope)",
            )
        ],
    ),
    "unknown create_unit key": (
        _capital_create_unit(_division(), "\t\tmystery = { foo = bar }\n"),
        frozenset(),
        [("CREATE UNIT: unknown key", "2: create_unit unknown key(s): mystery")],
    ),
    "unknown division string key": (
        _capital_create_unit(_division(extra=" start_equipment_factor = 1 bogus = 1")),
        frozenset(),
        [
            (
                "CREATE UNIT: unknown key in division string",
                "2: division string unknown key(s): bogus",
            )
        ],
    ),
    "division string without a template": (
        _capital_create_unit(_division(template=None)),
        frozenset({"Militia"}),
        [
            (
                "CREATE UNIT: division string lacks division_template",
                '2: division string lacks division_template="..."',
            )
        ],
    ),
    "execute_effect state block is a state scope": (
        "select_state_effect = {\n"
        "\texecute_effect = yes\n"
        "\tstate = yes\n"
        "\tcreate_unit = {\n"
        f'\t\tdivision = "{_division()}"\n'
        "\t\towner = ROOT\n"
        "\t}\n"
        "}\n",
        frozenset(),
        [],
    ),
    "ROOT-scope template covers a country-scoped spawn": (
        "completion_reward = {\n"
        + _template_block("Militia")
        + _template_block("Other")
        + "\tSWE = {\n"
        "\t\tif = {\n"
        '\t\t\tlimit = { has_template = "Other" }\n'
        "\t\t\tcapital_scope = {\n"
        "\t\t\t\tcreate_unit = {\n"
        f'\t\t\t\t\tdivision = "{_division()}"\n'
        "\t\t\t\t\towner = SWE\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        frozenset({"Militia"}),
        [],
    ),
}


@pytest.mark.parametrize(
    "content, deleted, expected", _CREATE_UNIT_CASES.values(), ids=_CREATE_UNIT_CASES
)
def test_created_units(tmp_path, content, deleted, expected):
    issues = _create_unit_issues(tmp_path, content, deleted)
    assert [(issue.category, issue.message) for issue in issues] == expected


_EVENT_WITH_CREATE_UNITS = (
    "# create_unit = { owner = ROOT }\n"
    "country_event = {\n"
    "\toption = {\n"
    "\t\tcapital_scope =\n"
    "\t\t{\n"
    '\t\t\tlog = "} #"\n'
    "\t\t\tcreate_unit = {\n"
    f'\t\t\t\tdivision = "{_division()}"\n'
    "\t\t\t}\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
    "create_unit = { owner = ROOT }"
)


@pytest.mark.parametrize(
    "content",
    [_EVENT_WITH_CREATE_UNITS, _EVENT_WITH_CREATE_UNITS.replace("\n", "\r\n")],
    ids=["lf", "crlf"],
)
def test_create_unit_lines_skip_comments_and_quoted_braces(tmp_path, content):
    issues = _create_unit_issues(tmp_path, content)
    assert [(issue.file, issue.line, issue.message) for issue in issues] == [
        ("events/TST.txt", 7, "7: create_unit missing `owner`"),
        (
            "events/TST.txt",
            13,
            "13: create_unit outside a state scope (effect does nothing at "
            "country scope)",
        ),
        ("events/TST.txt", 13, "13: create_unit missing `division` string"),
    ]


_FOREIGN = "CREATE UNIT: foreign-only static template definition"


def _event(filler):
    return "# filler\n" * filler + (
        "country_event = {\n"
        "\toption = {\n"
        "\t\tcapital_scope = {\n"
        "\t\t\tcreate_unit = {\n"
        f'\t\t\t\tdivision = "{_division("Guard")}"\n'
        "\t\t\t\towner = TST\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}"
    )


def _write_mod(tmp_path, events):
    _write(
        tmp_path,
        "common/scripted_effects/tst_templates.txt",
        'OPR = {\n\tdivision_template = {\n\t\tname = "Guard"\n\t}\n}\n',
    )
    for index in range(events):
        _write(tmp_path, f"events/TST_{index:02}.txt", _event(index))


def _foreign(index, filler):
    line = filler + 4
    return (
        f"events/TST_{index:02}.txt",
        line,
        f"{line}: create_unit uses division_template 'Guard', but only static "
        "definitions found for OPR; none found for TST",
    )


def _findings(tmp_path, workers=1):
    validator = _validator(tmp_path, workers=workers)
    assert validator.workers == workers
    validator.run_all_validations()
    assert {issue.category for issue in validator._issues} <= {_FOREIGN}
    return [(i.file, i.line, i.message) for i in validator._issues]


def test_pooled_run_matches_the_in_process_run(tmp_path, monkeypatch):
    # Eleven event files plus the template file clear the pool threshold for
    # both the template index and the create_unit pass.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    _write_mod(tmp_path, 11)

    pooled = _findings(tmp_path, workers=2)
    assert pooled == _findings(tmp_path)
    assert sorted(pooled) == [_foreign(index, index) for index in range(11)]


def test_warm_cache_reuses_the_cold_scan_until_a_file_changes(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write_mod(tmp_path, 2)
    cold = _findings(tmp_path)
    assert sorted(cold) == [_foreign(0, 0), _foreign(1, 1)]

    build_nodes = oob._build_block_nodes
    template_entries = oob.division_template_entries

    def must_not_run(*_args):
        raise AssertionError("a warm run must reuse the cached scan")

    monkeypatch.setattr(oob, "_build_block_nodes", must_not_run)
    monkeypatch.setattr(oob, "division_template_entries", must_not_run)
    assert _findings(tmp_path) == cold

    parsed_line_counts = []

    def record(text):
        parsed_line_counts.append(text.count("\n"))
        return build_nodes(text)

    monkeypatch.setattr(oob, "_build_block_nodes", record)
    monkeypatch.setattr(oob, "division_template_entries", template_entries)
    _write(tmp_path, "events/TST_00.txt", _event(3))
    assert sorted(_findings(tmp_path)) == [_foreign(0, 3), _foreign(1, 1)]
    # The edit rebuilds the stat-keyed template index (templates file and both
    # events) but re-parses only the edited event for its create_unit checks.
    assert sorted(parsed_line_counts) == [5, 10, 12, 12]


# --- airborne templates -----------------------------------------------------

_PARADROP_UNITS = """sub_units = {
\tPara_Inf_Bat = {
\t\tcan_be_parachuted = yes
\t}
\tPara_Support_Comp = {
\t\tcan_be_parachuted = yes
\t}
\tSP_Arty_Bat = {
\t\tcan_be_parachuted = no
\t}
\tNested_Flag_Comp = {
\t\tneed = {
\t\t\tcan_be_parachuted = yes
\t\t}
\t}
}
"""


def _paradrop_template(name, unit, block="support", repeat=1):
    rows = f"\t\t{unit} = {{ x = 0 y = 0 }}\n" * repeat
    return (
        "division_template = {\n"
        f'\tname = "{name}"\n'
        "\tregiments = {\n"
        "\t\tPara_Inf_Bat = { x = 0 y = 0 }\n"
        "\t}\n"
        f"\t{block} = {{\n{rows}\t}}\n"
        "}\n"
    )


def _paradrop_issues(tmp_path, name, unit, **template_kwargs):
    _write(tmp_path, "common/units/MD_land_units.txt", _PARADROP_UNITS)
    _write(
        tmp_path,
        "history/units/SWE_2000.txt",
        _paradrop_template(name, unit, **template_kwargs),
    )
    validator = _validator(tmp_path)
    validator._build_canonical_units()
    validator.validate_airborne_templates()
    return validator._issues


def test_airborne_template_with_a_non_parachutable_unit_warns(tmp_path):
    issues = _paradrop_issues(tmp_path, "Parachute Brigade", "SP_Arty_Bat")
    assert [
        (issue.severity, issue.category, issue.file, issue.line) for issue in issues
    ] == [
        (
            "warning",
            "airborne-template-not-parachutable",
            "history/units/SWE_2000.txt",
            7,
        )
    ]
    assert "'Parachute Brigade' (line 1) uses 'SP_Arty_Bat'" in issues[0].message


_PARACHUTE = "Parachute Brigade"
_SWE_AIRBORNE = "history/units/SWE_2000.txt:Airborne Brigade"

# case: (template name, unit, template layout, air assault allowlist, warnings)
_PARADROP_CASES = {
    "regiments block": (_PARACHUTE, "SP_Arty_Bat", {"block": "regiments"}, (), 1),
    "regimental_support block": (
        _PARACHUTE,
        "SP_Arty_Bat",
        {"block": "regimental_support"},
        (),
        1,
    ),
    "unit repeated in one template": (_PARACHUTE, "SP_Arty_Bat", {"repeat": 3}, (), 1),
    "flag nested in a sub-block": (_PARACHUTE, "Nested_Flag_Comp", {}, (), 1),
    "only parachutable units": (_PARACHUTE, "Para_Support_Comp", {}, (), 0),
    "name that is not airborne": (
        "Separate Artillery Brigade",
        "SP_Arty_Bat",
        {},
        (),
        0,
    ),
    "allowlisted air assault template": (
        "Airborne Brigade",
        "SP_Arty_Bat",
        {},
        (_SWE_AIRBORNE,),
        0,
    ),
    "allowlist entry for another file": (
        "Airborne Brigade",
        "SP_Arty_Bat",
        {},
        ("history/units/SYR_2000.txt:Airborne Brigade",),
        1,
    ),
}


@pytest.mark.parametrize(
    "name, unit, layout, allowlist, warnings",
    _PARADROP_CASES.values(),
    ids=_PARADROP_CASES,
)
def test_airborne_templates(
    tmp_path, monkeypatch, name, unit, layout, allowlist, warnings
):
    monkeypatch.setattr(oob, "_AIR_ASSAULT_TEMPLATES", frozenset(allowlist))
    issues = _paradrop_issues(tmp_path, name, unit, **layout)
    assert [issue.category for issue in issues] == [
        "airborne-template-not-parachutable"
    ] * warnings


@pytest.mark.parametrize(
    "name, airborne",
    [
        ("Parachute Brigade", True),
        ("Airborne Division", True),
        ("Brigada VDV", True),
        ("Desant Brigade", True),
        ("Separate Infantry BDE", False),
    ],
)
def test_airborne_name_patterns(name, airborne):
    assert any(pattern.search(name) for pattern in oob._AIRBORNE_NAME_RES) is airborne


# --- division template layout -----------------------------------------------

_SLOT = "template-slot"
_LOCKED = "template-locked-row"
_PREFIX = "template 'Test Brigade' (line 1): "
_OOB = "history/units/TST_2000.txt"
# Millennium Dawn's defines: three open rows, two more from doctrines.
_LIMITS = TemplateLimits(
    grids={"regiments": (5, 5), "regimental_support": (5, 3), "support": (1, 5)},
    open_rows=3,
    required_battalions=(1, 3, 5),
    column_bonus={"UKR": 1},
)
_DEFINES = (
    "NDefines.NMilitary.MIN_DIVISION_BRIGADE_HEIGHT = 3 -- 4\n"
    "\tNDefines.NMilitary.MAX_REGIMENTAL_SUPPORT_HEIGHT = 3\t\t-- Max height\n"
    "-- NDefines.NMilitary.MAX_DIVISION_BRIGADE_WIDTH = 9\n"
    "NDefines.NMilitary.REGIMENTAL_SUPPORT_REQUIRED_BATTALIONS = { 1, 3, 5 } -- rows\n"
)
_DOCTRINES = (
    "centralized_command = {\n"
    "\tavailable = {\n\t\tOR = { has_war = no }\n\t}\n"
    "\tadditional_brigade_column_size = 1\n"
    "\trewards = {\n"
    "\t\tdivision_structure = {\n"
    "\t\t\tadditional_brigade_column_size = 1\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
    "mobile_infantry = {\n"
    "\tplanning_speed = 0.1\n"
    "}\n"
)


def _slot_block(name, slots):
    rows = "".join(f"\t\tUnit = {{ x = {x} y = {y} }}\n" for x, y in slots)
    return f"\t{name} = {{\n{rows}\t}}\n"


def _slot_template(**blocks):
    """One template; the first block's units start on line 4."""
    body = "".join(_slot_block(name, slots) for name, slots in blocks.items())
    return f'division_template = {{\n\tname = "Test Brigade"\n{body}}}\n'


def _locked(units, row):
    return (
        f"{units} regiments unit(s) on row y = {row} or higher, locked without "
        "a doctrine that adds additional_brigade_column_size"
    )


# case: (template text, file, (line, category, message) per finding)
_SLOT_CASES = {
    "contiguous layout": (
        _slot_template(
            regiments=[(0, 0), (0, 1), (0, 2), (1, 0)],
            regimental_support=[(0, 0), (0, 1), (1, 0)],
            support=[(0, 0), (0, 1)],
        ),
        _OOB,
        [],
    ),
    "skipped row": (
        _slot_template(regiments=[(0, 0), (0, 2)]),
        _OOB,
        [(5, _SLOT, "regiments column x = 0 skips row y = 1")],
    ),
    # The #5420 shape: y = 0, 1, 3 where 0, 1, 2 was meant.
    "row that jumps to y = 3": (
        _slot_template(regiments=[(0, 0), (0, 1), (0, 3)]),
        _OOB,
        [
            (6, _LOCKED, _locked(1, 3)),
            (6, _SLOT, "regiments column x = 0 skips row y = 2"),
        ],
    ),
    "column that starts below the first row": (
        _slot_template(regiments=[(0, 1)]),
        _OOB,
        [(4, _SLOT, "regiments column x = 0 skips row y = 0")],
    ),
    "skipped column": (
        _slot_template(regiments=[(0, 0), (2, 0), (2, 1)]),
        _OOB,
        [(5, _SLOT, "regiments skips column x = 1")],
    ),
    "slot used twice": (
        _slot_template(regiments=[(0, 0), (0, 0)]),
        _OOB,
        [(5, _SLOT, "regiments slot x = 0 y = 0 is already used on line 4")],
    ),
    "unit without both coordinates": (
        _slot_template(regiments=[(0, 0), (0, 1)]).replace("x = 0 y = 1", "x = 0"),
        _OOB,
        [(5, _SLOT, "regiments unit 'Unit' has no readable x and y")],
    ),
    "regimental support skipping a regiments column": (
        _slot_template(regiments=[(0, 0), (1, 0), (2, 0)], regimental_support=[(2, 0)]),
        _OOB,
        [],
    ),
    "regimental support without its regiments column": (
        _slot_template(regiments=[(0, 0)], regimental_support=[(1, 0)]),
        _OOB,
        [
            (
                7,
                _SLOT,
                "regimental_support column x = 1 has no regiments column x = 1",
            )
        ],
    ),
    "regimental support row without enough battalions": (
        _slot_template(
            regiments=[(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
            regimental_support=[(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
        ),
        _OOB,
        [
            (
                12,
                _SLOT,
                "regimental_support slot x = 0 y = 1 needs 3 battalions in "
                "regiments column x = 0, which has 2",
            ),
            (
                15,
                _SLOT,
                "regimental_support slot x = 1 y = 2 needs 5 battalions in "
                "regiments column x = 1, which has 3",
            ),
        ],
    ),
    "regimental support row gap and reuse": (
        _slot_template(regiments=[(0, 0)], regimental_support=[(0, 1), (0, 1)]),
        _OOB,
        [
            (7, _SLOT, "regimental_support column x = 0 skips row y = 0"),
            (
                7,
                _SLOT,
                "regimental_support slot x = 0 y = 1 needs 3 battalions in "
                "regiments column x = 0, which has 1",
            ),
            (
                8,
                _SLOT,
                "regimental_support slot x = 0 y = 1 is already used on line 7",
            ),
        ],
    ),
    "regiments past the grid width": (
        _slot_template(regiments=[(x, 0) for x in range(6)]),
        _OOB,
        [(9, _SLOT, "regiments slot x = 5 y = 0 is outside the 5x5 grid")],
    ),
    "support past the grid width": (
        _slot_template(support=[(0, 0), (1, 0)]),
        _OOB,
        [(5, _SLOT, "support slot x = 1 y = 0 is outside the 1x5 grid")],
    ),
    "support past the grid height": (
        _slot_template(support=[(0, y) for y in range(6)]),
        _OOB,
        [(9, _SLOT, "support slot x = 0 y = 5 is outside the 1x5 grid")],
    ),
    "commented-out unit does not fill a gap": (
        _slot_template(regiments=[(0, 0), (0, 1), (0, 2)]).replace(
            "\t\tUnit = { x = 0 y = 1 }", "\t\t#Unit = { x = 0 y = 1 }"
        ),
        _OOB,
        [(6, _SLOT, "regiments column x = 0 skips row y = 1")],
    ),
    "each template has its own grid": (
        _slot_template(regiments=[(0, 0)]) + _slot_template(regiments=[(0, 0)]),
        _OOB,
        [],
    ),
    "rows past the base height": (
        _slot_template(regiments=[(0, y) for y in range(5)] + [(1, 0)]),
        _OOB,
        [(7, _LOCKED, _locked(2, 3))],
    ),
    "starting doctrine opens a row for that tag only": (
        _slot_template(regiments=[(0, y) for y in range(5)]),
        "history/units/UKR_2000.txt",
        [(8, _LOCKED, _locked(1, 4))],
    ),
}


@pytest.mark.parametrize("raw, rel, expected", _SLOT_CASES.values(), ids=_SLOT_CASES)
def test_template_slots(raw, rel, expected):
    text = strip_comments(raw)
    findings = check_template_slots(text, _build_block_nodes(text), rel, _LIMITS)
    assert findings == [
        (line, category, _PREFIX + message) for line, category, message in expected
    ]


_MISPLACED = "template-misplaced-support"
_BARRED = {"support": {"Arty_Battery"}, "regimental_support": {"hq_engineer"}}
_SUPPORT_UNITS = """sub_units = {
\tArty_Battery = {
\t\tgroup = support
\t\tdivisional = no
\t}
\thq_engineer = {
\t\tgroup = support
\t\tregimental = no
\t}
}
"""


def _dropped(block, unit, flag):
    return f"{block} lists '{unit}', which sets {flag} = no, so the game drops it"


# case: (template text, (line, message) per finding)
_MISPLACED_CASES = {
    "regimental company in support": (
        _paradrop_template("Test Brigade", "Arty_Battery"),
        [(7, _dropped("support", "Arty_Battery", "divisional"))],
    ),
    "divisional company in regimental support": (
        _paradrop_template("Test Brigade", "hq_engineer", block="regimental_support"),
        [(7, _dropped("regimental_support", "hq_engineer", "regimental"))],
    ),
    "each company in the block it allows": (
        _paradrop_template("Test Brigade", "Arty_Battery", block="regimental_support")
        + _paradrop_template("Test Brigade", "hq_engineer"),
        [],
    ),
    "company without a placement flag": (
        _paradrop_template("Test Brigade", "Weapons_company"),
        [],
    ),
    "flags apply to support blocks only": (
        _paradrop_template("Test Brigade", "Arty_Battery", block="regiments"),
        [],
    ),
    "each misplaced entry is its own finding": (
        _paradrop_template("Test Brigade", "Arty_Battery", repeat=2),
        [
            (7, _dropped("support", "Arty_Battery", "divisional")),
            (8, _dropped("support", "Arty_Battery", "divisional")),
        ],
    ),
}


@pytest.mark.parametrize(
    "raw, expected", _MISPLACED_CASES.values(), ids=_MISPLACED_CASES
)
def test_misplaced_support(raw, expected):
    text = strip_comments(raw)
    assert check_misplaced_support(text, _build_block_nodes(text), _BARRED) == [
        (line, _MISPLACED, _PREFIX + message) for line, message in expected
    ]


def test_misplaced_support_reads_flags_from_unit_files(tmp_path):
    _write(tmp_path, "common/units/MD_regimental_support.txt", _SUPPORT_UNITS)
    _write(tmp_path, _OOB, _paradrop_template("Test Brigade", "Arty_Battery"))
    validator = _validator(tmp_path)
    validator._build_canonical_units()
    validator.validate_template_slots()
    assert [
        (issue.severity, issue.file, issue.line)
        for issue in validator._issues
        if issue.category == _MISPLACED
    ] == [("warning", _OOB, 7)]


def test_limits_come_from_the_defines_and_starting_doctrines(tmp_path):
    write_tree(
        tmp_path,
        {
            "common/defines/MD_defines.lua": _DEFINES,
            "common/doctrines/subdoctrines/land/combat.txt": _DOCTRINES,
            "history/countries/UKR - Ukraine.txt": (
                "set_sub_doctrine = centralized_command\n"
                "add_mastery = {\n\tamount = 25\n"
                "\tsub_doctrine = centralized_command\n}\n"
            ),
            "history/countries/GER - Germany.txt": (
                "set_sub_doctrine = {\n\tsub_doctrine = mobile_infantry\n}\n"
                "2017.1.1 = {\n\tset_sub_doctrine = centralized_command\n}\n"
            ),
        },
    )
    assert read_template_limits(str(tmp_path)) == _LIMITS


def test_limits_fall_back_to_vanilla_without_defines(tmp_path):
    assert read_template_limits(str(tmp_path)) == TemplateLimits(
        grids={"regiments": (5, 5), "regimental_support": (5, 1), "support": (1, 5)},
        open_rows=4,
        required_battalions=(3,),
        column_bonus={},
    )


_SET_CENTRALIZED = "set_sub_doctrine = centralized_command\n"
_TWO_REWARDS = _DOCTRINES.replace(
    "\t\t\tadditional_brigade_column_size = 1\n",
    "\t\t\tplanning_speed = 0.05\n",
    1,
).replace(
    "\t\t}\n\t}\n}\nmobile_infantry",
    "\t\t}\n"
    "\t\tdivision_structure_two = {\n"
    "\t\t\tadditional_brigade_column_size = 1\n"
    "\t\t}\n"
    "\t}\n}\nmobile_infantry",
)


def _mastery(amount, doctrine="centralized_command", extra=""):
    return f"add_mastery = {{ amount = {amount} sub_doctrine = {doctrine}{extra} }}\n"


# case: (defines, doctrines file, UKR history, extra rows per tag)
_COLUMN_BONUS_CASES = {
    "mastery reaches the default threshold": (
        "",
        _DOCTRINES,
        _SET_CENTRALIZED + _mastery(100),
        {"UKR": 2},
    ),
    "mastery amounts add up": (
        "",
        _DOCTRINES,
        _SET_CENTRALIZED + _mastery(60) + _mastery(40),
        {"UKR": 2},
    ),
    "mastery in another doctrine": (
        "",
        _DOCTRINES,
        _SET_CENTRALIZED + _mastery(100, "mobile_infantry"),
        {"UKR": 1},
    ),
    "mastery in a doctrine that is not set": (
        "",
        _DOCTRINES,
        "set_sub_doctrine = mobile_infantry\n" + _mastery(100),
        {},
    ),
    "dynamic mastery amount": (
        "",
        _DOCTRINES,
        _SET_CENTRALIZED + _mastery("ROOT.x"),
        {"UKR": 1},
    ),
    "mastery with a filter the check does not model": (
        "",
        _DOCTRINES,
        _SET_CENTRALIZED + _mastery(100, extra=" index = 0"),
        {"UKR": 1},
    ),
    "mastery in a dated block": (
        "",
        _DOCTRINES,
        _SET_CENTRALIZED + "2000.1.1 = {\n\t" + _mastery(100) + "}\n",
        {"UKR": 1},
    ),
    "reward threshold from the define": (
        "NDefines.NDoctrines.DEFAULT_REWARD_MASTERY = 50.0\n",
        _DOCTRINES,
        _SET_CENTRALIZED + _mastery(50),
        {"UKR": 2},
    ),
    "reward threshold from the reward": (
        "",
        _DOCTRINES.replace(
            "division_structure = {\n", "division_structure = {\n\t\t\tmastery = 50\n"
        ),
        _SET_CENTRALIZED + _mastery(50),
        {"UKR": 2},
    ),
    "second reward below its cumulative cost": (
        "",
        _TWO_REWARDS,
        _SET_CENTRALIZED + _mastery(100),
        {"UKR": 1},
    ),
    "second reward at its cumulative cost": (
        "",
        _TWO_REWARDS,
        _SET_CENTRALIZED + _mastery(200),
        {"UKR": 2},
    ),
}


@pytest.mark.parametrize(
    "defines, doctrines, history, expected",
    _COLUMN_BONUS_CASES.values(),
    ids=_COLUMN_BONUS_CASES,
)
def test_starting_column_bonus(tmp_path, defines, doctrines, history, expected):
    files = {
        "common/doctrines/subdoctrines/land/combat.txt": doctrines,
        "history/countries/UKR - Ukraine.txt": history,
    }
    if defines:
        files["common/defines/MD_defines.lua"] = defines
    write_tree(tmp_path, files)
    assert read_template_limits(str(tmp_path)).column_bonus == expected


@pytest.mark.parametrize(
    "rel",
    [
        _OOB,
        "common/national_focus/tst.txt",
        "common/scripted_effects/00_AI_scripted_effects.txt",
        "events/Tst.txt",
    ],
)
def test_full_run_reports_both_categories_for_every_template_source(tmp_path, rel):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(
        tmp_path,
        rel,
        _slot_template(regiments=[(0, 0), (0, 2)])
        + _slot_template(regiments=[(0, y) for y in range(4)]),
    )

    validator = _validator(tmp_path)
    validator.run_all_validations()

    assert [
        (issue.severity, issue.category, issue.file, issue.line)
        for issue in validator._issues
        if issue.category.startswith("template-")
    ] == [
        ("error", _SLOT, rel, 5),
        ("warning", _LOCKED, rel, 14),
    ]


# --- air base capacity ------------------------------------------------------

_AIRBASE = "airbase-over-capacity"
_SWE_AIR = "history/units/SWE_2000_bba.txt"
_NOR_AIR = "history/units/NOR_2000_bba.txt"
_STATE_10 = "history/states/10-Test.txt"
_BUILDINGS_1 = "\t\tbuildings = {\n\t\t\tair_base = 1\n\t\t}\n"


def _state_file(history):
    return f"state = {{\n\tid = 10\n\thistory = {{\n{history}\t}}\n}}\n"


def _air_oob(*states):
    """`air_wings` with one wing per amount: ``(state id, [amounts])`` pairs."""
    body = ""
    for state_id, amounts in states:
        body += f"\t{state_id} = {{\n"
        for amount in amounts:
            body += (
                f'\t\tsmall_plane_airframe_1 = {{ owner = "SWE" amount = {amount} }}\n'
            )
        body += "\t}\n"
    return "air_wings = {\n" + body + "}\n"


_OVER = "state 10 starts with 25 planes, but air_base 1 holds 24"

# case: (files over the base tree, staged files or None, (file, line, message))
_AIRBASE_CASES = {
    "over capacity": ({_SWE_AIR: _air_oob((10, [25]))}, None, [(_SWE_AIR, 2, _OVER)]),
    "at capacity": ({_SWE_AIR: _air_oob((10, [24]))}, None, []),
    "wings in one state add up": (
        {_SWE_AIR: _air_oob((10, [12, 13]))},
        None,
        [(_SWE_AIR, 2, _OVER)],
    ),
    "state repeated in one file": (
        {_SWE_AIR: _air_oob((10, [12]), (10, [13]))},
        None,
        [(_SWE_AIR, 2, _OVER)],
    ),
    "commented wing": (
        {
            _SWE_AIR: _air_oob((10, [24])).replace(
                "\t}", "\t\t# small_plane_airframe_1 = { amount = 1 }\n\t}"
            )
        },
        None,
        [],
    ),
    "commented air base": (
        {
            _SWE_AIR: _air_oob((10, [25])),
            _STATE_10: _state_file(
                _BUILDINGS_1.replace(
                    "\t\t\tair_base", "\t\t\t# air_base = 5\n\t\t\tair_base"
                )
            ),
        },
        None,
        [(_SWE_AIR, 2, _OVER)],
    ),
    "dated air base is not the start level": (
        {
            _SWE_AIR: _air_oob((10, [25])),
            _STATE_10: _state_file(
                _BUILDINGS_1
                + "\t\t2010.1.1 = {\n\t\t\tbuildings = {\n\t\t\t\tair_base = 5\n"
                "\t\t\t}\n\t\t}\n"
            ),
        },
        None,
        [(_SWE_AIR, 2, _OVER)],
    ),
    "unknown state": (
        {_SWE_AIR: _air_oob((99, [1]))},
        None,
        [(_SWE_AIR, 2, "state 99 starts with 1 planes, but air_base 0 holds 0")],
    ),
    "carrier wing is not a state": (
        {_SWE_AIR: _air_oob(('"HSwMS Test (R01)"', [25]), (10, [24]))},
        None,
        [],
    ),
    "vanilla capacity without the define": (
        {_SWE_AIR: _air_oob((10, [25])), "common/defines/MD_defines.lua": ""},
        None,
        [],
    ),
    "shared base": (
        {_SWE_AIR: _air_oob((10, [13])), _NOR_AIR: _air_oob((10, [12]))},
        None,
        [
            (_NOR_AIR, 2, _OVER.replace("planes", "planes (shared with SWE)")),
            (_SWE_AIR, 2, _OVER.replace("planes", "planes (shared with NOR)")),
        ],
    ),
    "staged file counts unstaged wings": (
        {_SWE_AIR: _air_oob((10, [13])), _NOR_AIR: _air_oob((10, [12]))},
        [_SWE_AIR],
        [(_SWE_AIR, 2, _OVER.replace("planes", "planes (shared with NOR)"))],
    ),
}


@pytest.mark.parametrize(
    "files, staged, expected", _AIRBASE_CASES.values(), ids=_AIRBASE_CASES
)
def test_airbase_capacity(tmp_path, files, staged, expected):
    write_tree(
        tmp_path,
        {
            "common/defines/MD_defines.lua": (
                "\tNDefines.NBuildings.AIRBASE_CAPACITY_MULT = 24\n"
            ),
            _STATE_10: _state_file(_BUILDINGS_1),
            **files,
        },
    )
    validator = _validator(tmp_path, staged_only=staged is not None)
    if staged is not None:
        validator.staged_files = [str(tmp_path / rel) for rel in staged]

    validator.validate_airbase_capacity()

    assert [
        (issue.severity, issue.category, issue.file, issue.line, issue.message)
        for issue in validator._issues
    ] == [("warning", _AIRBASE, *finding) for finding in expected]


def test_clean_mod_passes_every_oob_check(tmp_path):
    _write_units(tmp_path)
    write_tree(
        tmp_path,
        {
            "common/units/equipment/MD_ships.txt": _FRIGATES,
            "common/units/names_divisions/SWE.txt": (
                "SWE_ARM = {\n\tname = NAME_SWE_ARM\n}\n"
            ),
            _SWE_HISTORY: _SWE_VARIANT,
            "history/units/SWE_1990.txt": (
                "division_template = {\n"
                '\tname = "Infantry Brigade"\n'
                "\tdivision_names_group = SWE_ARM\n"
                "\tregiments = {\n"
                "\t\tArm_Inf_Bat = { x = 0 y = 0 }\n"
                "\t}\n"
                "}\n" + _ship("frigate_hull_2", "Naresuan Class", **_SWE_SHIP)
            ),
        },
    )
    validator = _validator(tmp_path)
    validator.run_validations()

    assert validator._issues == []
    assert validator.errors_found == 0
    assert validator.warnings_found == 0
