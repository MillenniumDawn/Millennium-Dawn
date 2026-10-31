"""History validator: the technology, special-project and building parsers, the
per-country checks, and the full run over a synthetic mod."""

import os
from collections import defaultdict

import pytest
import validate_history as V
from shared.suite import (
    assert_findings,
    build_validator,
    checks_called_by_run,
    run_validator,
    write_tree,
)
from shared.suite import write_under_str as _write

_TECH_FILE = "common/technologies/test.txt"
_PROJECT_FILE = "common/special_projects/projects/test.txt"
_IDEAS_FILE = "common/ideas/test.txt"
_COUNTRY_FILE = "history/countries/TST - Test.txt"
_NSB = "No Step Back"
_BBA = "By Blood Alone"


@pytest.fixture(autouse=True)
def _no_disk_cache(monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")


def _text(*parts):
    return "\n".join(parts) + "\n"


def _block(head, *parts):
    """`head = { ... }` with each part one tab in. A part may span lines."""
    lines = [line for part in parts for line in part.split("\n")]
    return f"{head} = {{\n" + "".join(f"\t{line}\n" for line in lines) + "}"


def _dlc(name):
    return f'has_dlc = "{name}"'


def _if(limit, *parts, otherwise=()):
    """An `if` block. `limit=None` leaves the limit out. `otherwise` parts go in
    the `else` nested inside it, where HOI4 puts an else."""
    body = [f"limit = {{ {limit} }}"] if limit else []
    body += parts
    if otherwise:
        body.append(_block("else", *otherwise))
    return _block("if", *body)


def _techs(*names):
    return "set_technology = { " + " ".join(f"{name} = 1" for name in names) + " }"


def _complete(project):
    return f"complete_special_project = sp:{project}"


def _variant(name, *slots):
    """A create_equipment_variant block. `name=None` leaves the name out."""
    parts = [f'name = "{name}"'] if name else []
    parts += ["type = frigate_hull_2", _block("modules", *slots)]
    return _block("create_equipment_variant", *parts)


def _state(owner, *buildings):
    """A state file. `owner=None` leaves the owner out."""
    parts = [f"owner = {owner}"] if owner else []
    return _text(
        _block("state", _block("history", *parts, _block("buildings", *buildings)))
    )


def _undecodable(tmp_path, relative):
    """A file whose bytes are not valid UTF-8, as a corrupt file would be."""
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe technologies = {\n}\n")
    return str(path)


def _country(tmp_path, body):
    return _write(tmp_path, _COUNTRY_FILE, body)


# ---- technology files --------------------------------------------------------

# case: (technology file, techs, {tech: prerequisites}, {module: enabling techs},
#        {tech: DLC gates})
_TECH_FILE_CASES = {
    # A variable and a blank line are skipped.
    "blocks over several lines": (
        _text(
            _block(
                "technologies",
                "@base_year = 1965",
                _block(
                    "root_tech",
                    _block("path", "leads_to_tech = child_tech"),
                    _block("enable_equipment_modules", "engine_2", "", "armor_plate"),
                    _block("allow_branch", f"NOT = {{ {_dlc(_BBA)} }}"),
                ),
                _block("child_tech", "category = armor"),
            ),
        ),
        {"root_tech", "child_tech"},
        {"child_tech": {"root_tech"}},
        {"engine_2": {"root_tech"}, "armor_plate": {"root_tech"}},
        {"root_tech": [("forbid", _BBA)]},
    ),
    # Only allow_branch gates a tech: the has_dlc in ai_will_do does not.
    "blocks on one line": (
        _text(
            _block(
                "technologies",
                _block(
                    "root_tech",
                    "path = { research_cost_coeff = 1 leads_to_tech = child_tech }",
                    "enable_equipment_modules = { engine_2 armor_plate }",
                    f"allow_branch = {{ {_dlc(_NSB)} }}",
                    _block(
                        "ai_will_do",
                        f"modifier = {{ factor = 0 NOT = {{ {_dlc(_BBA)} }} }}",
                    ),
                ),
                _block("child_tech", _block("path", "leads_to_tech = leaf_tech")),
            )
        ),
        {"root_tech", "child_tech"},
        {"child_tech": {"root_tech"}, "leaf_tech": {"child_tech"}},
        {"engine_2": {"root_tech"}, "armor_plate": {"root_tech"}},
        {"root_tech": [("require", _NSB)]},
    ),
    "no technologies wrapper": (
        "some_other_root = {\n\tfoo = bar\n}\n",
        set(),
        {},
        {},
        {},
    ),
}


@pytest.mark.parametrize(
    ("text", "techs", "prerequisites", "modules", "gates"),
    _TECH_FILE_CASES.values(),
    ids=_TECH_FILE_CASES,
)
def test_technology_graph_is_read_from_tech_files(
    tmp_path, text, techs, prerequisites, modules, gates
):
    _write(tmp_path, _TECH_FILE, text)
    _undecodable(tmp_path, "common/technologies/broken.txt")

    assert V.parse_tech_dependencies(str(tmp_path)) == (
        prerequisites,
        techs,
        modules,
        gates,
    )


def test_tech_file_parses_without_the_optional_maps():
    text, techs, prerequisites, _modules, _gates = _TECH_FILE_CASES[
        "blocks over several lines"
    ]
    found_prerequisites, found_techs = defaultdict(set), set()

    V._parse_tech_file(text, found_prerequisites, found_techs)

    assert (found_techs, found_prerequisites) == (techs, prerequisites)


def test_dlc_gate_spreads_only_through_fully_gated_prerequisites():
    # shared_tech stays reachable under the DLC through neutral_root.
    prerequisites = {
        "arty_1": {"arty_0"},
        "arty_2": {"arty_1"},
        "shared_tech": {"arty_0", "neutral_root"},
    }
    gate = [("forbid", _NSB)]

    assert V.propagate_dlc_reqs(prerequisites, {"arty_0": gate}) == {
        "arty_0": gate,
        "arty_1": gate,
        "arty_2": gate,
    }


_FOO = "foo = { allow = { is_special_project_completed = sp:sp_x } }"

# case: (technology file, {tech: projects its allow block requires})
_TECH_PROJECT_CASES = {
    "two projects under a ROOT scope": (
        _text(
            _block(
                "technologies",
                _block(
                    "gen_6_medium",
                    _block(
                        "allow",
                        _block(
                            "ROOT",
                            "is_special_project_completed = sp:sp_aircraft",
                            "is_special_project_completed = sp:sp_autonomous",
                        ),
                    ),
                ),
            )
        ),
        {"gen_6_medium": {"sp_aircraft", "sp_autonomous"}},
    ),
    # The block is not read as a tech, but the tech after it still parses.
    "brace on the next line": (
        _text(
            _block(
                "technologies",
                "@base_year = 1965",
                "odd_block =",
                "{",
                "\tis_special_project_completed = sp:sp_hidden",
                "}",
                _block(
                    "real_tech",
                    _block("allow", "is_special_project_completed = sp:sp_real"),
                ),
            )
        ),
        {"real_tech": {"sp_real"}},
    ),
    # The wrapper is never a tech named `technologies`.
    "duplicated wrapper": (
        f"technologies = {{\ntechnologies = {{\n\t{_FOO}\n}}\n}}\n",
        {"foo": {"sp_x"}},
    ),
    "no trailing newline": (f"technologies = {{\n\t{_FOO} }}", {"foo": {"sp_x"}}),
    "no technologies wrapper": ("some_other_root = {\n\tfoo = bar\n}\n", {}),
}


@pytest.mark.parametrize(
    ("text", "required"), _TECH_PROJECT_CASES.values(), ids=_TECH_PROJECT_CASES
)
def test_required_projects_are_read_from_tech_allow_blocks(tmp_path, text, required):
    _write(tmp_path, _TECH_FILE, text)

    assert V.parse_tech_sp_requirements(str(tmp_path)) == required


# ---- special-project files ---------------------------------------------------

_PROJECTS = _text(
    _block("sp_two_dlcs", f"allowed = {{ {_dlc(_NSB)} {_dlc(_BBA)} }}"),
    _block("sp_tag_locked", "allowed = { original_tag = LBA }"),
    _block(
        "sp_open",
        "allowed = { always = yes }",
        _block(
            "project_output",
            _block(
                "custom_effect_tooltip",
                "localization_key = SP_SOMETHING_ELSE",
                "TECH = decoy_tech",
            ),
            _block(
                "country_effects",
                _block(
                    "custom_effect_tooltip",
                    "localization_key = SP_UNLOCK_TECH",
                    "TECH = mbt_tech",
                ),
            ),
            _block(
                "facility_state_effects",
                "set_building_level = { level = 1 }",
                _block("set_building_level", "type = microchip_plant", "level = 1"),
            ),
        ),
    ),
    # No allowed block.
    _block(
        "sp_bare",
        _block(
            "project_output",
            _block(
                "facility_state_effects",
                "set_building_level = { type = microchip_plant }",
            ),
        ),
    ),
)


def test_project_files_yield_dlc_gates_claims_and_building_grants(tmp_path):
    _write(tmp_path, _PROJECT_FILE, _PROJECTS)
    mod = str(tmp_path)

    assert V.parse_sp_allowed_dlc(mod) == {"sp_two_dlcs": [_BBA, _NSB]}
    assert V.parse_sp_always_yes(mod) == {"sp_open"}
    assert V.parse_sp_output_claims(mod) == {"sp_open": ["mbt_tech"]}
    assert V.parse_project_granted_buildings(mod) == {
        "microchip_plant": {"sp_open", "sp_bare"}
    }


_CLAIM = "sp:sp_a: project_output claims to unlock tech_y, but tech_y is gated by "

# case: ({project: techs it gates}, findings for sp_a claiming tech_y)
_OUTPUT_CLAIM_CASES = {
    "claim matches": ({"sp_a": {"tech_y"}}, []),
    "tech gated by another project": (
        {"sp_a": {"tech_x"}, "sp_b": {"tech_y"}},
        [_CLAIM + "sp:sp_b"],
    ),
    "this project gates another tech": (
        {"sp_a": {"tech_x"}},
        [_CLAIM + "no project; this project gates tech_x"],
    ),
    "this project gates nothing": (
        {},
        [_CLAIM + "no project, and this project gates nothing"],
    ),
}


@pytest.mark.parametrize(
    ("gated", "findings"), _OUTPUT_CLAIM_CASES.values(), ids=_OUTPUT_CLAIM_CASES
)
def test_project_output_must_claim_a_tech_the_project_gates(gated, findings):
    assert V.validate_sp_output_consistency(gated, {"sp_a": ["tech_y"]}) == findings


# ---- nuclear_status ideas, state buildings and their owners ------------------


def _status_group(*members):
    return _text(_block("ideas", _block("nuclear_status", *members)))


_NUCLEAR_ENERGY = _block("nuclear_energy", "cost = 300")

# case: (ideas file, or None for an unreadable one; non-default members)
_NUCLEAR_STATUS_CASES = {
    # The default member is granted to every country. A nested block is not one.
    "default member": (
        _status_group(
            "use_list_view = yes",
            _block("non_nuclear_power", "default = yes", "cost = 300"),
            _block(
                "nuclear_energy", "cost = 300", "available = { has_tech = reactor_01 }"
            ),
            _block("nuclear_power_def", "cost = 300"),
        ),
        {"nuclear_energy", "nuclear_power_def"},
    ),
    "another group": (
        _text(_block("ideas", _block("nuclear_stance", "foo = {}"))),
        set(),
    ),
    "unreadable file": (None, set()),
    "brace on the next line": (
        _status_group("odd_member =", "{", "\tcost = 300", "}", _NUCLEAR_ENERGY),
        {"nuclear_energy"},
    ),
    "member on the closing line": (
        "ideas = {\n\tnuclear_status = {\n\t\tnuclear_energy = { cost = 300 } }\n}\n",
        {"nuclear_energy"},
    ),
}


@pytest.mark.parametrize(
    ("text", "members"), _NUCLEAR_STATUS_CASES.values(), ids=_NUCLEAR_STATUS_CASES
)
def test_nuclear_status_members_exclude_the_default(tmp_path, text, members):
    if text is None:
        _undecodable(tmp_path, _IDEAS_FILE)
    else:
        _write(tmp_path, _IDEAS_FILE, text)

    assert V.parse_nuclear_status_ideas(str(tmp_path)) == members


def test_state_building_owners_count_top_level_levels_of_one_or_more(tmp_path):
    _undecodable(tmp_path, "history/states/broken.txt")
    write_tree(
        tmp_path,
        {
            # A level of zero and a building under a province do not count.
            "history/states/1-Test.txt": _state(
                "TST",
                "nuclear_reactor = 1 # trailing comment",
                "microchip_plant = 0",
                _block("1234", "naval_base = 9"),
            ),
            "history/states/2-Unowned.txt": _state(None, "nuclear_reactor = 1"),
            "history/states/3-Other.txt": _state("OTH"),
        },
    )
    tracked = {"nuclear_reactor", "microchip_plant", "naval_base"}

    assert V.parse_state_building_owners(str(tmp_path), tracked) == {
        "nuclear_reactor": {"TST"}
    }
    assert V._get_state_owners(str(tmp_path)) == {"TST", "OTH"}


def test_country_contents_are_read_by_tag_with_comments_stripped(tmp_path):
    _country(tmp_path, "# complete_special_project = sp:sp_x\ncapital = 1\n")
    _undecodable(tmp_path, "history/countries/BAD - Bad.txt")

    tag_files = V._tag_country_file_map(str(tmp_path))
    contents = V._load_country_contents(tag_files, {"TST", "BAD", "ZZZ"})

    assert tag_files["TST"].endswith("TST - Test.txt")
    assert set(contents) == {"TST"}
    assert "capital" in contents["TST"] and "sp_x" not in contents["TST"]


# case: (the owner's country file, or None when it has none; finding fragments)
_REACTOR_CASES = {
    "no nuclear_status idea": (
        "add_ideas = { non_nuclear_power }",
        [("TST", "grants no nuclear_status idea")],
    ),
    "idea granted": ("add_ideas = { nuclear_energy }", []),
    "no country file": (None, [("TST", "no history/countries/")]),
}


@pytest.mark.parametrize(
    ("content", "findings"), _REACTOR_CASES.values(), ids=_REACTOR_CASES
)
def test_reactor_owner_needs_a_nuclear_status_idea(content, findings):
    contents = {} if content is None else {"TST": content}

    assert_findings(
        V._find_reactor_owners_without_nuclear_status(
            {"TST"}, {"nuclear_energy", "nuclear_power_def"}, contents
        ),
        findings,
    )


# case: (projects granting the plant, the owner's country file or None,
#        finding fragments)
_GRANTED_BUILDING_CASES = {
    "another project completed": (
        {"sp_chips"},
        _complete("sp_composites"),
        [("SWE", "microchip_plant", "sp:sp_chips")],
    ),
    "one of two granting projects completed": (
        {"sp_a", "sp_b"},
        _complete("sp_b"),
        [],
    ),
    "no country file": ({"sp_chips"}, None, [("SWE", "no history/countries/")]),
}


@pytest.mark.parametrize(
    ("projects", "content", "findings"),
    _GRANTED_BUILDING_CASES.values(),
    ids=_GRANTED_BUILDING_CASES,
)
def test_project_granted_building_needs_its_project(projects, content, findings):
    contents = {} if content is None else {"SWE": content}

    assert_findings(
        V._find_buildings_without_granting_project(
            {"microchip_plant": {"SWE"}}, {"microchip_plant": projects}, contents
        ),
        findings,
    )


# ---- country file parsers ----------------------------------------------------

_MBT_ONLY = [({"mbt_tech"}, set(), "unconditional")]

# case: (history text, [(techs, completed projects, DLC configuration)])
_HISTORY_TEXT_CASES = {
    "tech at level 0": (
        "set_technology = { disabled_tech = 0 enabled_tech = 1 }",
        [({"enabled_tech"}, set(), "unconditional")],
    ),
    "has_dlc outside an if": (_text(_dlc(_NSB), _techs("mbt_tech")), _MBT_ONLY),
    "project without the sp: prefix": (
        _text("complete_special_project = sp_armor", _techs("mbt_tech")),
        _MBT_ONLY,
    ),
    "unbalanced braces": (
        _text(
            "add_ideas = { idea_a idea_b }", "}", "{", _techs("mbt_tech"), "capital ="
        ),
        _MBT_ONLY,
    ),
    "if and its else": (
        _if(
            _dlc(_NSB),
            _complete("sp_armor"),
            _techs("mbt_tech"),
            otherwise=[_techs("MBT_1")],
        ),
        [
            ({"MBT_1"}, set(), "NOT No Step Back"),
            ({"mbt_tech"}, {"sp_armor"}, "No Step Back"),
        ],
    ),
    "negated limit": (
        _if(f"NOT = {{ {_dlc(_NSB)} }}", _techs("legacy_tech")),
        [
            ({"legacy_tech"}, set(), "NOT No Step Back"),
            (set(), set(), "No Step Back"),
        ],
    ),
    # An else_if negates its if and adds the DLC of its own limit.
    "else_if with its own DLC": (
        _if(
            _dlc(_NSB),
            _techs("nsb_tech"),
            _block("else_if", f"limit = {{ {_dlc(_BBA)} }}", _techs("bba_tech")),
        ),
        [
            (set(), set(), "NOT By Blood Alone + NOT No Step Back"),
            ({"bba_tech"}, set(), "By Blood Alone + NOT No Step Back"),
            ({"nsb_tech"}, set(), "NOT By Blood Alone + No Step Back"),
            ({"nsb_tech"}, set(), "By Blood Alone + No Step Back"),
        ],
    ),
    # Regression: the tech after the nested else stays in the enclosing if.
    "tech after a nested else": (
        _if(
            _dlc(_BBA),
            _techs("gen_4"),
            _if(
                "has_country_flag = foo",
                _techs("gen_3"),
                otherwise=[_techs("gen_2")],
            ),
            _techs("awacs"),
        ),
        [
            (set(), set(), "NOT By Blood Alone"),
            ({"gen_4", "gen_3", "gen_2", "awacs"}, set(), "By Blood Alone"),
        ],
    ),
}


@pytest.mark.parametrize(
    ("text", "branches"), _HISTORY_TEXT_CASES.values(), ids=_HISTORY_TEXT_CASES
)
def test_history_text_yields_techs_and_projects_per_dlc_configuration(text, branches):
    assert V._parse_history_text(text) == branches


def test_context_label_splits_into_present_and_absent_dlcs():
    assert V._context_dlcs("No Step Back +  + NOT By Blood Alone") == ({_NSB}, {_BBA})
    assert V._context_dlcs("unconditional") == (set(), set())


_ENGINE_2 = "engine_slot = engine_2"

# case: (history text, [(variant, modules, DLCs gating it)])
_VARIANT_CASES = {
    "empty slot": (
        _variant("Naresuan Class", "battery_slot = ship_battery_2", "aa_slot = empty"),
        [("Naresuan Class", {"ship_battery_2"}, frozenset())],
    ),
    "unnamed variant in a DLC block": (
        _if(_dlc(_BBA), _variant(None, _ENGINE_2)),
        [("?", {"engine_2"}, frozenset({_BBA}))],
    ),
    "no modules block": (
        _block("create_equipment_variant", 'name = "Stock"', "type = frigate_hull_2"),
        [("Stock", set(), frozenset())],
    ),
    # Only an if whose own limit has a positive has_dlc gates the variant.
    "negated, flag-limited and limitless ifs": (
        _text(
            _if(f"NOT = {{ {_dlc(_NSB)} }}", _variant("Negated", _ENGINE_2)),
            _if("has_country_flag = some_flag", _variant("Flagged", _ENGINE_2)),
            _if(None, _variant("Bare", _ENGINE_2)),
        ),
        [(name, {"engine_2"}, frozenset()) for name in ("Negated", "Flagged", "Bare")],
    ),
}


@pytest.mark.parametrize(
    ("text", "variants"), _VARIANT_CASES.values(), ids=_VARIANT_CASES
)
def test_equipment_variants_carry_their_modules_and_dlc_gates(text, variants):
    assert V._parse_variants_text(text) == variants


def test_oob_references_record_key_and_line_and_skip_comments(tmp_path):
    path = _country(
        tmp_path,
        _text(
            "capital = 1",
            'oob = "TST_1990"',
            '# oob = "TST_commented"',
            'set_air_oob = "TST_1990_air"',
            'set_naval_oob = "TST_1990_naval"',
        ),
    )

    assert V._get_oob_refs(path) == [
        ("TST_1990", 2, "oob"),
        ("TST_1990_air", 4, "set_air_oob"),
        ("TST_1990_naval", 5, "set_naval_oob"),
    ]


def test_missing_country_file_yields_nothing(tmp_path):
    gone, mod = str(tmp_path / "gone.txt"), str(tmp_path)

    assert V.parse_history_file(gone, mod) == []
    assert V.parse_equipment_variants(gone, mod) == []
    assert V.validate_country_sp_misplacement((gone, {"sp_x"}, mod)) == []
    assert V._get_oob_refs(gone) == []


def test_unreadable_country_file_is_reported(tmp_path):
    path = _undecodable(tmp_path, _COUNTRY_FILE)
    finding = ["TST - Test.txt: could not read file"]

    assert V.validate_capital_defined(path) == finding
    assert V.validate_ruling_party_assigned(path) == finding


# ---- per-country checks ------------------------------------------------------

_KNOWN_TECHS = {"child_tech", "root_tech", "root_a", "root_b", "nsb_child", "nsb_root"}

# case: (country file, {tech: prerequisites}, findings)
_PREREQUISITE_CASES = {
    "prerequisite missing": (
        _techs("child_tech"),
        {"child_tech": {"root_tech"}},
        ["TST - Test.txt: child_tech requires root_tech"],
    ),
    "one of two prerequisites granted": (
        _techs("root_a", "child_tech"),
        {"child_tech": {"root_a", "root_b"}},
        [],
    ),
    "neither of two prerequisites": (
        _techs("child_tech"),
        {"child_tech": {"root_a", "root_b"}},
        ["TST - Test.txt: child_tech requires one of: root_a, root_b"],
    ),
    # A tech the graph does not know may come from files that are not parsed.
    "unknown tech": (_techs("dlc_only_tech"), {"dlc_only_tech": {"root_tech"}}, []),
    "missing in one DLC branch": (
        _text(_techs("root_tech"), _if(_dlc(_NSB), _techs("nsb_child"))),
        {"nsb_child": {"nsb_root"}},
        ["TST - Test.txt: nsb_child requires nsb_root [No Step Back]"],
    ),
}


@pytest.mark.parametrize(
    ("text", "prerequisites", "findings"),
    _PREREQUISITE_CASES.values(),
    ids=_PREREQUISITE_CASES,
)
def test_granted_tech_needs_a_prerequisite(tmp_path, text, prerequisites, findings):
    args = (_country(tmp_path, text), prerequisites, _KNOWN_TECHS, str(tmp_path))

    assert V.validate_country_file(args) == findings


_ENGINE_4 = _variant("Type 32", "engine_slot = engine_4")
_NEEDS_ADVANCED = {"engine_4": {"advanced_engines"}}
_NO_ENGINE_TECH = (
    'TST - Test.txt: variant "Type 32" uses engine_4 without enabling tech '
)

# case: (country file, {module: enabling techs}, findings)
_EQUIPMENT_CASES = {
    "enabling tech not granted": (
        _text(_techs("basic_engines"), _ENGINE_4),
        _NEEDS_ADVANCED,
        [_NO_ENGINE_TECH + "advanced_engines"],
    ),
    "module needs no tech": (_ENGINE_4, {}, []),
    "neither of two enabling techs": (
        _ENGINE_4,
        {"engine_4": {"engines_b", "engines_a"}},
        [_NO_ENGINE_TECH + "one of: engines_a, engines_b"],
    ),
    # Both DLCs are active in normal play, so a tech from any branch counts.
    "tech granted in a DLC branch": (
        _text(_if(_dlc(_BBA), _techs("advanced_engines")), _ENGINE_4),
        _NEEDS_ADVANCED,
        [],
    ),
    "same variant twice": (
        _text(_ENGINE_4, _ENGINE_4),
        _NEEDS_ADVANCED,
        [_NO_ENGINE_TECH + "advanced_engines"],
    ),
    "commented variant": (
        '# create_equipment_variant = { name = "Ghost" '
        "modules = { engine_slot = engine_4 } }\n",
        _NEEDS_ADVANCED,
        [],
    ),
}


@pytest.mark.parametrize(
    ("text", "module_techs", "findings"),
    _EQUIPMENT_CASES.values(),
    ids=_EQUIPMENT_CASES,
)
def test_variant_module_needs_an_enabling_tech(tmp_path, text, module_techs, findings):
    args = (_country(tmp_path, text), module_techs, str(tmp_path))

    assert V.validate_country_equipment(args) == findings


_DLC_GATES = {"legacy_arty": [("forbid", _NSB)], "nsb_arty": [("require", _NSB)]}

# case: (techs in the No Step Back if, techs in its else, findings)
_DLC_BRANCH_CASES = {
    "each tech in its own branch": (["nsb_arty"], ["legacy_arty"], []),
    "fallback tech in the DLC branch": (
        ["nsb_arty", "legacy_arty"],
        ["legacy_arty"],
        [
            'TST - Test.txt: legacy_arty is granted while "No Step Back" is active, '
            "but its tech branch requires that DLC be absent [No Step Back]"
        ],
    ),
    "DLC tech in the else": (
        ["nsb_arty"],
        ["nsb_arty"],
        [
            'TST - Test.txt: nsb_arty is granted while "No Step Back" is inactive, '
            "but its tech branch requires that DLC [NOT No Step Back]"
        ],
    ),
}


@pytest.mark.parametrize(
    ("inside", "outside", "findings"),
    _DLC_BRANCH_CASES.values(),
    ids=_DLC_BRANCH_CASES,
)
def test_dlc_gated_tech_must_sit_in_a_matching_branch(
    tmp_path, inside, outside, findings
):
    text = _if(_dlc(_NSB), _techs(*inside), otherwise=[_techs(*outside)])
    args = (_country(tmp_path, text), _DLC_GATES, str(tmp_path))

    assert V.validate_country_dlc_techs(args) == findings


_NOT_COMPLETED = "TST - Test.txt: %s requires special project sp:%s but it is not completed at game start [%s]"
_ANY = "any DLC configuration"
_NSB_BRANCHES = _if(_dlc(_NSB), _techs("mbt_tech"), otherwise=[_techs("MBT_1")])

# case: (country file, {tech: required projects}, {project: DLCs it needs},
#        findings)
_PROJECT_REQUIREMENT_CASES = {
    "project never completed": (
        _techs("mbt_tech"),
        {"mbt_tech": {"sp_armor"}},
        {},
        [_NOT_COMPLETED % ("mbt_tech", "sp_armor", _ANY)],
    ),
    "project completed": (
        _text(_complete("sp_armor"), _techs("mbt_tech")),
        {"mbt_tech": {"sp_armor"}},
        {},
        [],
    ),
    "one of two projects completed": (
        _text(_complete("sp_a"), _techs("gen_6")),
        {"gen_6": {"sp_a", "sp_b"}},
        {},
        [_NOT_COMPLETED % ("gen_6", "sp_b", _ANY)],
    ),
    "two projects missing": (
        _techs("gen_6"),
        {"gen_6": {"sp_a", "sp_b"}},
        {},
        [
            "TST - Test.txt: gen_6 requires special projects sp:sp_a, sp:sp_b "
            "but they are not completed at game start [any DLC configuration]"
        ],
    ),
    # A generic project completed only in a DLC block leaves the else uncovered.
    "generic project completed in one branch": (
        _if(
            _dlc(_BBA),
            _complete("sp_awacs"),
            _techs("awacs"),
            otherwise=[_techs("awacs")],
        ),
        {"awacs": {"sp_awacs"}},
        {},
        [_NOT_COMPLETED % ("awacs", "sp_awacs", "NOT By Blood Alone")],
    ),
    "DLC project, tech granted with the DLC": (
        _NSB_BRANCHES,
        {"mbt_tech": {"sp_armor"}},
        {"sp_armor": [_NSB]},
        [_NOT_COMPLETED % ("mbt_tech", "sp_armor", "No Step Back")],
    ),
    # Without either DLC the project does not exist, so the tech is not locked.
    "project needing two DLCs, tech granted without one": (
        _NSB_BRANCHES,
        {"MBT_1": {"sp_nuke"}},
        {"sp_nuke": [_BBA, _NSB]},
        [],
    ),
}


@pytest.mark.parametrize(
    ("text", "required", "project_dlcs", "findings"),
    _PROJECT_REQUIREMENT_CASES.values(),
    ids=_PROJECT_REQUIREMENT_CASES,
)
def test_granted_tech_needs_its_projects_completed(
    tmp_path, text, required, project_dlcs, findings
):
    args = (_country(tmp_path, text), required, project_dlcs, str(tmp_path))

    assert V.validate_country_sp_requirements(args) == findings


# case: (country file, finding fragments). sp_helicopter is always available.
_MISPLACEMENT_CASES = {
    "completed only in a DLC block": (
        _if(_dlc(_NSB), _complete("sp_helicopter")),
        [("sp:sp_helicopter", 'only inside a "No Step Back" block')],
    ),
    "also completed unconditionally": (
        _text(_complete("sp_helicopter"), _if(_dlc(_NSB), _complete("sp_helicopter"))),
        [],
    ),
    "project that is not always available": (
        _if(_dlc("Gotterdammerung"), _complete("sp_warhead")),
        [],
    ),
    # A guard of {DLC: absent} is not a positive DLC block.
    "completed in the else of a DLC block": (
        _if(_dlc(_NSB), _techs("mbt_tech"), otherwise=[_complete("sp_helicopter")]),
        [],
    ),
}


@pytest.mark.parametrize(
    ("text", "findings"), _MISPLACEMENT_CASES.values(), ids=_MISPLACEMENT_CASES
)
def test_always_available_project_is_not_completed_only_in_a_dlc_block(
    tmp_path, text, findings
):
    args = (_country(tmp_path, text), {"sp_helicopter"}, str(tmp_path))

    assert_findings(V.validate_country_sp_misplacement(args), findings)


# case: (country file, existing OOB files, tags owning a state, findings)
_OOB_CASES = {
    "land OOB exists": ('oob = "TST_1990"\n', {"TST_1990"}, {"TST"}, []),
    "air OOB only": (
        'set_air_oob = "TST_1990_air"\n',
        {"TST_1990_air"},
        {"TST"},
        [("TST - Test.txt: TST owns states at game start", "no land OOB")],
    ),
    "missing OOB file": (
        'capital = 1\noob = "TST_1990"\nset_oob = "TST_gone"\n',
        {"TST_1990"},
        {"TST"},
        [
            'TST - Test.txt:3 - set_oob references "TST_gone" but no '
            "history/units/TST_gone.txt file exists"
        ],
    ),
    "owns no state": ("capital = 1\n", set(), {"OTH"}, []),
}


@pytest.mark.parametrize(
    ("text", "existing", "owners", "findings"), _OOB_CASES.values(), ids=_OOB_CASES
)
def test_state_owner_needs_a_land_oob_that_exists(
    tmp_path, text, existing, owners, findings
):
    args = (_country(tmp_path, text), existing, owners)

    assert_findings(V.validate_oob_references(args), findings)


_NO_CAPITAL = ["TST - Test.txt: no capital defined"]

# case: (country file, findings)
_CAPITAL_CASES = {
    "column zero": ("capital = 700\n", []),
    "indented": ("\tcapital = 700\n", []),
    "missing": ('oob = "TST_1990"\n', _NO_CAPITAL),
    "inside a quoted string": ('log = "capital = 700"\n', _NO_CAPITAL),
}


@pytest.mark.parametrize(
    ("text", "findings"), _CAPITAL_CASES.values(), ids=_CAPITAL_CASES
)
def test_country_file_needs_a_capital(tmp_path, text, findings):
    assert V.validate_capital_defined(_country(tmp_path, text)) == findings


_START = "start_politics_input = yes"
_NO_PARTY = "TST - Test.txt: %sstart_politics_input does not assign ruling_party (0-23) after it"


def _party(index):
    return f"set_variable = {{ ruling_party = {index} }}"


def _dated(*parts, date="2000.1.1"):
    return _block(date, *parts)


# start_politics_input clears ruling_party, so the same block must set it again.
# case: (country file, label of each block reported)
_RULING_PARTY_CASES = {
    "no start_politics_input": ("capital = 1", []),
    "assigned after": (_dated(_START, _party(2)), []),
    "nothing assigned": (_dated(_START), ["2000.1.1: "]),
    "assigned before": (_dated(_party(2), _START), ["2000.1.1: "]),
    # Only set_variable sets the 0-23 index. set_politics takes an ideology.
    "set_politics block": (
        _dated(_START, "set_politics = { ruling_party = 3 }"),
        ["2000.1.1: "],
    ),
    "commented assignment": (_dated(_START, "# " + _party(2)), ["2000.1.1: "]),
    "index 24": (_dated(_START, _party(24)), ["2000.1.1: "]),
    "cleared again after the assignment": (
        _dated(_START, _party(14), _START),
        ["2000.1.1: "],
    ),
    "each date block on its own": (
        _text(_dated(_START, _party(2)), _dated(_START, date="2017.1.1")),
        ["2017.1.1: "],
    ),
    "before the date blocks": (_text(_START, _dated(_START, _party(2))), [""]),
}


@pytest.mark.parametrize(
    ("text", "labels"), _RULING_PARTY_CASES.values(), ids=_RULING_PARTY_CASES
)
def test_start_politics_input_needs_a_ruling_party_after_it(tmp_path, text, labels):
    path = _country(tmp_path, text)

    assert V.validate_ruling_party_assigned(path) == [
        _NO_PARTY % label for label in labels
    ]


# ---- the full run ------------------------------------------------------------

_GOOD_COUNTRY = _text(
    "capital = 1",
    'oob = "TST_1990"',
    "add_ideas = { nuclear_energy }",
    _complete("sp_microchip"),
    _complete("sp_open"),
    _START,
    _party(2),
    _techs("root_tech", "child_tech", "sp_tech"),
    _variant("Type 32", _ENGINE_2),
)

_BAD_COUNTRY = _text(
    'oob = "BAD_missing"',
    "add_ideas = { non_nuclear_power }",
    _START,
    _techs("child_tech", "sp_tech"),
    _if(_dlc(_NSB), _complete("sp_open"), otherwise=[_techs("nsb_tech")]),
    _variant("Ghost", "engine_slot = engine_9"),
)

_BOTH_PLANTS = ("nuclear_reactor = 1", "microchip_plant = 1")

_MOD = {
    "common/technologies/md.txt": _text(
        _block(
            "technologies",
            _block(
                "root_tech",
                _block("path", "leads_to_tech = child_tech"),
                _block("enable_equipment_modules", "engine_2"),
            ),
            _block("child_tech", "category = armor"),
            _block("advanced_engines", _block("enable_equipment_modules", "engine_9")),
            _block(
                "sp_tech",
                _block("allow", "is_special_project_completed = sp:sp_microchip"),
            ),
            _block("nsb_tech", _block("allow_branch", _dlc(_NSB))),
        )
    ),
    "common/special_projects/projects/md.txt": _text(
        _block(
            "sp_microchip",
            "allowed = { always = yes }",
            _block(
                "project_output",
                _block(
                    "custom_effect_tooltip",
                    "localization_key = SP_UNLOCK_TECH",
                    "TECH = sp_tech",
                ),
                _block(
                    "facility_state_effects",
                    _block("set_building_level", "type = microchip_plant", "level = 1"),
                ),
            ),
        ),
        _block("sp_open", "allowed = { always = yes }"),
    ),
    "common/ideas/md.txt": _status_group(
        _block("non_nuclear_power", "default = yes"), _NUCLEAR_ENERGY
    ),
    "history/units/TST_1990.txt": "units = {\n}\n",
    "history/states/1-Test.txt": _state("TST", *_BOTH_PLANTS),
    _COUNTRY_FILE: _GOOD_COUNTRY,
}

_BROKEN = {
    "history/states/2-Bad.txt": _state("BAD", *_BOTH_PLANTS),
    "history/countries/BAD - Bad.txt": _BAD_COUNTRY,
    "common/special_projects/projects/bad.txt": _text(
        _block(
            "sp_liar",
            _block(
                "project_output",
                _block(
                    "custom_effect_tooltip",
                    "localization_key = SP_UNLOCK_TECH",
                    "TECH = child_tech",
                ),
            ),
        )
    ),
}


def test_run_validations_calls_every_check(tmp_path, monkeypatch):
    called, checks = checks_called_by_run(
        build_validator(V.Validator, tmp_path), monkeypatch
    )

    assert called == checks


def test_clean_mod_passes_every_check(tmp_path):
    validator = run_validator(V.Validator, write_tree(tmp_path, _MOD))

    assert validator._issues == []
    assert validator.errors_found == 0


def test_each_check_reports_its_own_finding(tmp_path):
    validator = run_validator(V.Validator, write_tree(tmp_path, {**_MOD, **_BROKEN}))
    messages = sorted(issue.message for issue in validator._issues)

    assert messages == [
        "BAD - Bad.txt: child_tech requires root_tech",
        "BAD - Bad.txt: no capital defined",
        'BAD - Bad.txt: nsb_tech is granted while "No Step Back" is inactive, '
        "but its tech branch requires that DLC [NOT No Step Back]",
        "BAD - Bad.txt: sp:sp_open is always-available but is completed only "
        'inside a "No Step Back" block - hoist it to unconditional scope so '
        "players without that DLC still complete it",
        "BAD - Bad.txt: sp_tech requires special project sp:sp_microchip but it "
        "is not completed at game start [any DLC configuration]",
        "BAD - Bad.txt: start_politics_input does not assign "
        "ruling_party (0-23) after it",
        'BAD - Bad.txt: variant "Ghost" uses engine_9 without enabling tech '
        "advanced_engines",
        "BAD: owns a state starting with microchip_plant but never completes "
        "the granting special project (sp:sp_microchip)",
        "BAD: owns a state with a nuclear_reactor at game start but grants no "
        "nuclear_status idea (nuclear_energy)",
        'oob references "BAD_missing" but no history/units/BAD_missing.txt file exists',
        "sp:sp_liar: project_output claims to unlock child_tech, but child_tech "
        "is gated by no project, and this project gates nothing",
    ]
    # Every finding is an error, and the OOB one carries its file and line.
    assert validator.errors_found == len(messages)
    oob = next(issue for issue in validator._issues if "BAD_missing" in issue.message)
    assert (oob.file, oob.line) == ("BAD - Bad.txt", 1)


def test_building_checks_skip_without_ideas_or_projects(tmp_path):
    # No nuclear_status group and no building grant: skip, do not flag each owner.
    skipped = ("common/ideas/md.txt", "common/special_projects/projects/md.txt")
    files = {path: text for path, text in _MOD.items() if path not in skipped}

    validator = run_validator(V.Validator, write_tree(tmp_path, files))

    assert validator._issues == []


# case: (MD_STAGED_FILES, country files the staged run checks)
_STAGED_CASES = {
    "one staged country": ("history/countries/TST - Test.txt", ["TST - Test.txt"]),
    "nothing staged": ("", []),
}


@pytest.mark.parametrize(
    ("staged", "checked"), _STAGED_CASES.values(), ids=_STAGED_CASES
)
def test_staged_run_checks_only_staged_country_files(
    tmp_path, monkeypatch, staged, checked
):
    write_tree(tmp_path, {**_MOD, "history/countries/BAD - Bad.txt": _BAD_COUNTRY})
    monkeypatch.setenv("MD_STAGED_FILES", staged)

    validator = build_validator(V.Validator, tmp_path, staged_only=True)

    assert [os.path.basename(f) for f in validator._get_history_files()] == checked


_INFLUENCE_WRITE = "add_to_array = { influence_array = USA.id }"
_INFLUENCE_INIT = "init_influence = yes"
_INFLUENCE_SORT = "sort_influence = yes"
_INFLUENCE_VALID = f"{_INFLUENCE_INIT}\n{_INFLUENCE_WRITE}\n{_INFLUENCE_SORT}"
# case: (source, expected message fragments and lines)
_INFLUENCE_CASES = {
    "valid": (_INFLUENCE_VALID, []),
    "missing initialization after branch join": (
        'if = { limit = { has_dlc = "X" } init_influence = yes add_to_array = { influence_array = USA.id } }\nadd_to_array = { influence_array_val = 50 }\nsort_influence = yes',
        [("initialize influence", 2)],
    ),
    "enclosing conditional setup": (
        f'{_INFLUENCE_INIT}\nif = {{ limit = {{ has_dlc = "X" }} {_INFLUENCE_WRITE} }}\n{_INFLUENCE_SORT}',
        [],
    ),
    "conditional late reset": (
        f"{_INFLUENCE_VALID}\nif = {{ limit = {{ always = yes }} {_INFLUENCE_INIT} }}",
        [("clears earlier", 4)],
    ),
    "root write in foreign scope": (
        f'GER = {{ {_INFLUENCE_VALID.replace("influence_array =", "ROOT.influence_array =")} }}',
        [("initialize influence", 2), ("add sort_influence", 2)],
    ),
    "recalculate sorts": (
        _INFLUENCE_VALID.replace("sort_influence", "recalculate_influence"),
        [],
    ),
    "multiline value write": (
        "init_influence = yes\nadd_to_array = {\ninfluence_array_val = 250\n}\nsort_influence = yes",
        [],
    ),
    "pre-fix Japan": (
        f"{_INFLUENCE_WRITE}\n{_INFLUENCE_INIT}\n{_INFLUENCE_SORT}",
        [("initialize influence", 1), ("clears earlier", 2)],
    ),
    "premature sort": (
        f"{_INFLUENCE_INIT}\n{_INFLUENCE_SORT}\n{_INFLUENCE_WRITE}",
        [("before a later", 2), ("add sort_influence", 3)],
    ),
    "missing sort": (
        f"{_INFLUENCE_INIT}\n{_INFLUENCE_WRITE}",
        [("add sort_influence", 2)],
    ),
    "later write": (
        f"{_INFLUENCE_VALID}\nadd_to_array = {{ influence_array_val = 250 }}",
        [("before a later", 3), ("add sort_influence", 4)],
    ),
    "no setup": (
        f"{_INFLUENCE_SORT}\n{_INFLUENCE_INIT}\nadd_to_array = {{ influence_targets = CHI }}",
        [],
    ),
    "comments and strings": (
        f'# { _INFLUENCE_WRITE}\nlog = "{_INFLUENCE_WRITE}"\n{_INFLUENCE_INIT}',
        [],
    ),
    "separate dates": (
        f"2000.1.1 = {{\n{_INFLUENCE_VALID}\n}}\n2017.1.1 = {{ {_INFLUENCE_INIT} }}",
        [],
    ),
    "separate countries": (
        f"GER = {{\n{_INFLUENCE_VALID}\n}}\nFRA = {{ {_INFLUENCE_INIT} }}",
        [],
    ),
    "unrelated block": (f"effect_tooltip = {{ {_INFLUENCE_WRITE} }}", []),
    "separate branches": (
        f"if = {{ limit = {{ always = yes }}\n{_INFLUENCE_VALID}\n}} else = {{ {_INFLUENCE_INIT} }}",
        [],
    ),
    "transparent wrapper": (
        f"{_INFLUENCE_INIT}\nhidden_effect = {{ {_INFLUENCE_WRITE} }}\n{_INFLUENCE_SORT}",
        [],
    ),
    "qualified current": (
        _INFLUENCE_VALID.replace("influence_array =", "TST.influence_array ="),
        [],
    ),
    "foreign writes": (
        _INFLUENCE_VALID.replace("influence_array =", "GER.influence_array ="),
        [("initialize influence", 2), ("add sort_influence", 2)],
    ),
    "ignored non-call": (
        f"init_influence = no\n{_INFLUENCE_WRITE}\n{_INFLUENCE_SORT}",
        [("initialize influence", 2)],
    ),
}


@pytest.mark.parametrize(
    "source,expected", _INFLUENCE_CASES.values(), ids=_INFLUENCE_CASES
)
def test_influence_order(source, expected):
    findings = V.check_influence_order(source, "TST")
    assert len(findings) == len(expected)
    for fragment, line in expected:
        assert any(
            fragment in message and line == found_line
            for message, found_line in findings
        )


def test_influence_order_reports_staged_country_only(tmp_path):
    path = _country(tmp_path, _INFLUENCE_WRITE)
    _write(tmp_path, "history/countries/OTHER.txt", _INFLUENCE_WRITE)
    validator = build_validator(V.Validator, tmp_path)
    validator.staged_only = True
    validator.staged_files = [path]
    validator.validate_influence_order()
    assert len(validator._issues) == 2
    assert all(issue.severity == V.Severity.WARNING for issue in validator._issues)
    assert {
        (issue.file, issue.line, issue.category) for issue in validator._issues
    } == {(_COUNTRY_FILE, 1, "history-influence-order")}
