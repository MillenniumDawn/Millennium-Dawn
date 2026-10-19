"""Variable checks in the localisation validator: [?name] reads in English loc,
check_variable and has_variable reads in script, and name@target dynamic
variables. Each read must name a variable some script writes or the engine
supplies."""

import re

import pytest
import validate_localisation as VL
from shared.suite import build_validator, write_under_str
from validator_common import Severity


@pytest.fixture
def engine_doc(tmp_path):
    """Write the vanilla dynamic variable docs with these headings."""

    def write(*names):
        write_under_str(
            tmp_path,
            "resources/documentation/dynamic_variables_documentation.md",
            "# Dynamic Variables\n\n" + "".join(f"### {n}\n\n" for n in names),
        )

    yield write
    VL._engine_loc_vars.cache_clear()


def _script(tmp_path, body, relative="common/e.txt"):
    write_under_str(tmp_path, relative, body)


def _rows(tmp_path, check):
    validator = build_validator(VL.Validator, tmp_path)
    getattr(validator, check)()
    return [(i.severity, i.category, i.message) for i in validator._issues]


def _unwritten_names(tmp_path):
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_unwritten_script_variables()
    return {i.message.split(" - ")[0] for i in validator._issues}


# ---- what a [?...] names -------------------------------------------------------

# case: (text inside [?...], variable name or "" for none)
_VAR_NAME_CASES = {
    "format suffix": ("CZE_cssd_stability|%.2+", "CZE_cssd_stability"),
    "scope word hop": ("ROOT.GER_Troop_anger", "GER_Troop_anger"),
    "state hop": ("145.GRE_SUPPORT", "GRE_SUPPORT"),
    "tag hop": ("GER.troop_anger", "troop_anger"),
    "colon hop behind a dot": ("FROM.CONTROLLER:gdp_per_capita|Y", "gdp_per_capita"),
    "colon hop": ("var:influence_level", "influence_level"),
    "targeted engine variable": ("modifier@conscription_factor|Y%2", "modifier"),
    "targeted resource": ("resource@oil", "resource"),
    "variable target": ("cyber_defense_rating@var:target", "cyber_defense_rating"),
    "bare scope": ("ROOT", ""),
    "array element": ("var:FROM.influence_array^0", ""),
    "promote": ("current_nation.UNSCGetResolutionTypePassDesc", ""),
}


@pytest.mark.parametrize(
    ("raw", "expected"), _VAR_NAME_CASES.values(), ids=_VAR_NAME_CASES
)
def test_loc_var_name(raw, expected):
    assert VL._loc_var_name(raw) == expected


# ---- [?name] reads in English loc --------------------------------------------


def test_unwritten_loc_variable_is_an_error(tmp_path):
    """A [?name] no script writes renders as 0, so it must be reported."""
    write_under_str(
        tmp_path,
        "localisation/english/t_l_english.yml",
        ' a_key: "Written: [?written_var|0] Unwritten: [?never_written_var|0]"\n',
    )
    _script(tmp_path, "x = {\n\tset_variable = { written_var = 3 }\n}\n")
    assert _rows(tmp_path, "validate_variable_references") == [
        (
            Severity.ERROR,
            "loc-unwritten-variable",
            "never_written_var - t_l_english.yml",
        )
    ]


# Writes in common, events and history all count, with or without a scope.
# case: (directory, write target)
_WRITE_SCOPE_CASES = {
    "common": ("common", "written_var"),
    "events": ("events", "written_var"),
    "history": ("history/states", "written_var"),
    "state scope": ("common", "145.written_var"),
    "scope word": ("common", "ROOT.written_var"),
}


@pytest.mark.parametrize(
    ("directory", "target"), _WRITE_SCOPE_CASES.values(), ids=_WRITE_SCOPE_CASES
)
def test_loc_variable_writes_count_from_every_script_folder(
    tmp_path, directory, target
):
    write_under_str(
        tmp_path,
        "localisation/english/t_l_english.yml",
        ' a_key: "[?145.written_var] [?missing_var]"\n',
    )
    _script(tmp_path, f"set_variable = {{ {target} = 3 }}\n", f"{directory}/e.txt")
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_variable_references()
    assert [i.message for i in validator._issues] == ["missing_var - t_l_english.yml"]


def test_unwritten_targeted_loc_variable_is_reported(tmp_path, engine_doc):
    """[?name@target] uses the prefix; a typo of a documented name is reported."""
    engine_doc("resource_imported")
    write_under_str(
        tmp_path,
        "localisation/english/t_l_english.yml",
        ' a_key: "[?resource_imported@oil|+0] [?resource_improted@tungsten|+0]"\n',
    )
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_variable_references()
    assert [i.message for i in validator._issues] == [
        "resource_improted - t_l_english.yml"
    ]


# ---- name@target in script ----------------------------------------------------


def test_unknown_targeted_dynamic_variable_is_an_error(tmp_path, engine_doc):
    engine_doc("resource_imported", "resource_produced")
    _script(
        tmp_path,
        "microchip_update = {\n"
        "\tcheck_variable = { resource_produced@tungsten = 0 }\n"
        "\tcheck_variable = { resource_improted@tungsten = 0 }\n"
        "}\n",
    )
    assert _rows(tmp_path, "validate_targeted_dynamic_variables") == [
        (Severity.ERROR, "unknown-dynamic-variable", "resource_improted - e.txt")
    ]


# case: (script body)
_KNOWN_TARGETED_CASES = {
    "written targeted variable": (
        "x = {\n"
        "\tset_variable = { recognition_pressure_end@var:open_state = 1 }\n"
        "\tcheck_variable = { recognition_pressure_end@var:open_state > 0 }\n"
        "\tcheck_variable = { resource_imported@oil > 0 }\n"
        "}\n"
    ),
    "flag at a scope": (
        "x = {\n"
        "\thas_country_flag = trade_agreement@ROOT\n"
        "\tset_country_flag = {\n"
        "\t\tflag = recognition_campaign_from@ROOT\n"
        "\t\tdays = 210\n"
        "\t}\n"
        "\tcheck_variable = { resource_imported@steel > 0 }\n"
        "}\n"
    ),
    "extra engine variable": "x = { check_variable = { strength_ratio@THIS < 1.3 } }\n",
}


@pytest.mark.parametrize(
    "body", _KNOWN_TARGETED_CASES.values(), ids=_KNOWN_TARGETED_CASES
)
def test_known_targeted_variables_are_clean(tmp_path, engine_doc, body):
    engine_doc("resource_imported")
    _script(tmp_path, body)
    assert _rows(tmp_path, "validate_targeted_dynamic_variables") == []


# ---- check_variable and has_variable reads -----------------------------------


def test_unwritten_check_variable_is_a_warning(tmp_path, engine_doc):
    engine_doc("num_days")
    _script(
        tmp_path,
        "x = {\n"
        "\tset_variable = { written_var = 3 }\n"
        "\tcheck_variable = { written_var > 0 }\n"
        "\tcheck_variable = { never_written_var > 0 }\n"
        "\tcheck_variable = { num_days > 5 }\n"
        "}\n",
    )
    assert _rows(tmp_path, "validate_unwritten_script_variables") == [
        (Severity.WARNING, "script-unwritten-variable", "never_written_var - e.txt")
    ]


# case: (file, script body, names reported)
_SCRIPT_READ_CASES = {
    "has_variable": (
        "common/e.txt",
        "x = {\n"
        "\tset_variable = { ruling_party = 1 }\n"
        "\thas_variable = ruling_party\n"
        "\thas_variable = missing_party\n"
        "}\n",
        {"missing_party"},
    ),
    "engine random and vanilla writes": (
        "common/e.txt",
        "x = {\n"
        "\tcheck_variable = { random < 0.5 }\n"
        "\thas_variable = historical_capital_for_country\n"
        "\thas_variable = collaboration_formed_by\n"
        "}\n",
        {"collaboration_formed_by"},
    ),
    "a read allowed in one vanilla file": (
        "common/autonomous_states/lar_collaboration_government.txt",
        "x = {\n\thas_variable = collaboration_formed_by\n}\n",
        set(),
    ),
    "loop binders": (
        "common/e.txt",
        "x = {\n"
        "\tfor_each_loop = { array = stations value = current_station_id }\n"
        "\tcheck_variable = { current_station_id > 0 }\n"
        "\tfind_highest_in_array = { array = gdp_array value = max index = max_index }\n"
        "\tcheck_variable = { max > 0 }\n"
        "\tcheck_variable = { max_index > 0 }\n"
        "}\n",
        set(),
    ),
    "loop binder nested in another loop": (
        "common/e.txt",
        "x = {\n"
        "\tfor_loop_effect = {\n"
        "\t\tend = 3\n"
        "\t\tfind_highest_in_array = { array = gdp_array value = max index = max_index }\n"
        "\t\tcheck_variable = { max > 0 }\n"
        "\t\tcheck_variable = { max_index > 0 }\n"
        "\t}\n"
        "}\n",
        set(),
    ),
    "any_of and all_of bind only their own value": (
        "common/e.txt",
        "x = {\n"
        "\tset_variable = { existing_var = 1 }\n"
        "\tany_of = { array = orbit_array value = sat_orbit_model\n"
        "\t\tcheck_variable = { var = existing_var value = nested_unwritten }\n"
        "\t\tother = { index = nested_unwritten_index }\n"
        "\t}\n"
        "\tall_of = { array = orbit_array value = another_orbit_model }\n"
        "\tcheck_variable = { sat_orbit_model > 0 }\n"
        "\tcheck_variable = { another_orbit_model > 0 }\n"
        "\tcheck_variable = { nested_unwritten > 0 }\n"
        "\tcheck_variable = { nested_unwritten_index > 0 }\n"
        "\tother = { value = unbound_orbit_model }\n"
        "\tcheck_variable = { unbound_orbit_model > 0 }\n"
        "}\n",
        {"nested_unwritten", "nested_unwritten_index", "unbound_orbit_model"},
    ),
    "dynamic list value": (
        "common/scripted_guis/menu.txt",
        "scripted_gui = { menu = {\n"
        "\tdynamic_lists = { topbar_menu = { array = Root.menu value = topbar_menu_v\n"
        "\t\tother = { value = nested_menu_value }\n"
        "\t} }\n"
        "\tcheck_variable = { topbar_menu_v > 0 }\n"
        "\tcheck_variable = { nested_menu_value > 0 }\n"
        "\tcheck_variable = { missing_menu_v > 0 }\n"
        "\tother = { value = unrelated_value }\n"
        "\tcheck_variable = { unrelated_value > 0 }\n"
        "} }\n",
        {"missing_menu_v", "nested_menu_value", "unrelated_value"},
    ),
    "number-prefixed names": (
        "common/decisions/campaign.txt",
        "x = {\n"
        "\tadd_to_variable = { var = 500_days_completed value = 1 }\n"
        "\tcheck_variable = { 500_days_completed = 1 }\n"
        "\thas_variable = 500_days_completed\n"
        "\tcheck_variable = { 600_days_missing > 0 }\n"
        "}\n",
        {"600_days_missing"},
    ),
    "tooltip and script constant": (
        "common/e.txt",
        "x = {\n"
        "\tset_variable = { ENG_scottish_agitation = 1 }\n"
        "\tset_variable = { var_GNSS_mil_system_idx = 1 }\n"
        "\tcheck_variable = {\n"
        "\t\ttooltip = ENG_scottish_agitation_rising_tt\n"
        "\t\tvar = ENG_scottish_agitation\n"
        "\t\tvalue = 9\n"
        "\t\tcompare = greater_than\n"
        "\t}\n"
        "\tcheck_variable = { var_GNSS_mil_system_idx > @GNSS_sat_idx_base }\n"
        "}\n",
        set(),
    ),
    "token compare": (
        "common/e.txt",
        "x = {\n"
        "\tadd_to_array = { md_alerts = 1 }\n"
        "\tcheck_variable = { md_alerts^alert_idx = token:md_negative_nuclear_fuel }\n"
        "}\n",
        set(),
    ),
}


@pytest.mark.parametrize(
    ("relative", "body", "expected"),
    _SCRIPT_READ_CASES.values(),
    ids=_SCRIPT_READ_CASES,
)
def test_script_reads(tmp_path, relative, body, expected):
    _script(tmp_path, body, relative)
    assert _unwritten_names(tmp_path) == expected


def test_occupation_law_engine_values_are_not_global_exemptions(tmp_path):
    reads = (
        "\tcheck_variable = { uncapped_resistance_target > 0 }\n"
        "\tcheck_variable = { resistance_target_without_law > 0 }\n"
        "\tcheck_variable = { garrison_min_support_ratio > 0 }\n"
    )
    _script(
        tmp_path,
        "x = {\n" + reads + "}\n",
        "common/occupation_laws/occupation_laws.txt",
    )
    _script(tmp_path, "x = {\n" + reads + "}\n", "common/decisions/other.txt")
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_unwritten_script_variables()
    assert len(validator._issues) == 3
    assert all("other.txt" in issue.message for issue in validator._issues)


# The targeted check reports name@target; the read check must not report it again.
def test_check_variable_targeted_typo_is_not_double_counted(tmp_path, engine_doc):
    engine_doc("resource_imported")
    _script(tmp_path, "x = { check_variable = { resource_improted@tungsten = 0 } }\n")
    assert _unwritten_names(tmp_path) == set()


def test_script_reads_keep_their_lines_across_crlf_and_skipped_blocks(tmp_path):
    path = write_under_str(
        tmp_path,
        "common/reads.txt",
        "check_variable = { first_var > 0 }\r\n"
        "# check_variable = { commented_var > 0 }\r\n"
        'log = "# { quoted"\r\n'
        "check_variable = { [dyn] > 0 }\r\n"
        "has_variable = has_var\r\n"
        "check_variable = {\r\n"
        "\tmulti_var > 0\r\n"
        "}\r\n"
        "x = { check_variable = { last_var > 0 } }",
    )

    assert VL.process_txt_for_script_var_reads((path,)) == [
        ("has_var", "reads.txt", 5),
        ("first_var", "reads.txt", 1),
        ("multi_var", "reads.txt", 6),
        ("last_var", "reads.txt", 9),
    ]


def test_writes_behind_each_literal_gate_still_count(tmp_path):
    _script(
        tmp_path, "x = { add_to_array = { gated_list = 1 } }\n", "common/arrays.txt"
    )
    _script(
        tmp_path,
        "x = {\n"
        "\t# set_variable = { commented_var = 1 }\n"
        "\tset_variable = { gated_var = 1 }\n"
        "}",
        "common/vars.txt",
    )
    _script(
        tmp_path,
        "x = {\n"
        "\tcheck_variable = { gated_list > 0 }\n"
        "\tcheck_variable = { gated_var > 0 }\n"
        "\tcheck_variable = { commented_var > 0 }\n"
        "}\n",
        "events/reads.txt",
    )
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_unwritten_script_variables()
    assert [(i.message, i.file, i.line) for i in validator._issues] == [
        ("commented_var - reads.txt", "reads.txt", 4)
    ]


# The look-behind stands in for a leading \b, so each case must agree with it.
@pytest.mark.parametrize(
    ("text", "spans"),
    [
        ("check_variable = {", [(0, 18)]),
        ("xcheck_variable = {", []),
        ("Öcheck_variable={", []),
        ("\tcheck_variable={", [(1, 17)]),
    ],
)
def test_check_variable_opener_matches_only_where_a_word_boundary_does(text, spans):
    assert [m.span() for m in VL._CHECK_VARIABLE_OPEN_RE.finditer(text)] == spans
    assert spans == [m.span() for m in re.finditer(r"\bcheck_variable\s*=\s*\{", text)]
