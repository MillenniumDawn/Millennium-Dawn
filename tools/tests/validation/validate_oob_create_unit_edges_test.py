"""Edge cases in the create_unit checks of validate_oob_units.py.

Covers the malformed division-string shapes persistent.cpp rejects, the block
walkers behind the scope/ordering checks, and the create_unit paths the main
create_unit suite does not exercise: a top-level effect, an unknown nested key,
a ROOT scope reset, and a ROOT-scope template covering a country-scoped spawn.
"""

from validate_oob_units import (
    _build_block_nodes,
    _check_created_units,
    _closest_if,
    _container_for,
    _country_scope_path,
    _deepest_node_at,
    _is_positive_if_limit_condition,
    _parse_division_string,
    _runs_in_if_true_branch,
    _scope_label,
)

_BS = chr(92)


def _esc(value):
    return _BS + '"' + value + _BS + '"'


def _division(template="Militia", extra=""):
    body = "name = " + _esc("1st Brigade")
    if template is not None:
        body += " division_template = " + _esc(template)
    return body + extra


def _run(tmp_path, content, subdir="common/national_focus", deleted=frozenset()):
    target = tmp_path / subdir / "test.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _check_created_units((str(target), "test.txt", str(tmp_path), deleted, {}))


def _kinds(issues):
    return sorted(issue.category for issue in issues)


def _template(name):
    return (
        "\tdivision_template = {\n"
        f'\t\tname = "{name}"\n'
        "\t\tregiments = {\n"
        "\t\t\tL_Inf_Bat = { x = 0 y = 0 }\n"
        "\t\t}\n"
        "\t}\n"
    )


# --- division string schema -------------------------------------------------


def test_unclosed_quote_after_a_valid_pair_is_reported():
    issues, template = _parse_division_string(
        'division_template = "Militia" "unterminated'
    )
    assert template == "Militia"
    assert issues == [("malformed-division", "division string unclosed quote")]


def test_leading_string_token_is_leftover():
    issues, _ = _parse_division_string('"Militia"')
    assert ("malformed-division", "division string leftover token: Militia") in issues


def test_key_without_an_equals_is_leftover():
    issues, _ = _parse_division_string("name")
    assert ("malformed-division", "division string leftover token: name") in issues


def test_key_without_a_value_is_reported():
    issues, _ = _parse_division_string("name =")
    assert ("malformed-division", "division string name is missing a value") in issues


def test_unknown_key_with_a_block_value_is_skipped_whole():
    issues, template = _parse_division_string(
        'mystery = { a = { b = c } } division_template = "Militia"'
    )
    assert template == "Militia"
    assert issues == [
        ("unknown-division-key", "division string unknown key(s): mystery")
    ]


def test_force_equipment_variants_must_be_a_block():
    issues, _ = _parse_division_string(
        'division_template = "Militia" force_equipment_variants = 5'
    )
    assert (
        "malformed-division",
        "division string force_equipment_variants is not a block",
    ) in issues


def test_force_equipment_variants_entry_key_must_be_an_identifier():
    issues, _ = _parse_division_string(
        'division_template = "Militia" force_equipment_variants = { "x" = { } }'
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants does not parse",
        )
    ]


def test_force_equipment_variants_entry_needs_an_equals():
    issues, _ = _parse_division_string(
        'division_template = "Militia" force_equipment_variants = { infantry_equipment }'
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants does not parse",
        )
    ]


def test_force_equipment_variants_block_must_be_closed():
    issues, _ = _parse_division_string(
        'division_template = "Militia" '
        "force_equipment_variants = { infantry_equipment = { owner = SWE }"
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants is not a block",
        )
    ]


def test_force_equipment_variants_entry_must_be_a_block():
    issues, _ = _parse_division_string(
        'division_template = "Militia" force_equipment_variants = { infantry_equipment = 5 }'
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants 'infantry_equipment' is not a block",
        ),
        (
            "malformed-division",
            "division string force_equipment_variants does not parse",
        ),
    ]


def test_force_equipment_variants_entry_key_inside_must_be_an_identifier():
    issues, _ = _parse_division_string(
        'division_template = "Militia" '
        'force_equipment_variants = { infantry_equipment = { "owner" = SWE } }'
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants 'infantry_equipment' does not parse",
        ),
        (
            "malformed-division",
            "division string force_equipment_variants does not parse",
        ),
    ]


def test_force_equipment_variants_entry_field_needs_an_equals():
    issues, _ = _parse_division_string(
        'division_template = "Militia" '
        "force_equipment_variants = { infantry_equipment = { owner } }"
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants 'infantry_equipment' does not parse",
        ),
        ("malformed-division", "division string leftover token: }"),
    ]


def test_force_equipment_variants_entry_field_needs_a_value():
    issues, _ = _parse_division_string(
        'division_template = "Militia" '
        "force_equipment_variants = { infantry_equipment = { owner ="
    )
    assert (
        "malformed-division",
        "division string force_equipment_variants 'infantry_equipment' does not parse",
    ) in issues


def test_force_equipment_variants_amount_must_be_a_number():
    issues, _ = _parse_division_string(
        'division_template = "Militia" '
        "force_equipment_variants = { infantry_equipment = { amount = many } }"
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants 'infantry_equipment' "
            "amount must be a number",
        )
    ]


def test_force_equipment_variants_owner_must_be_a_tag():
    issues, _ = _parse_division_string(
        'division_template = "Militia" '
        "force_equipment_variants = { infantry_equipment = { owner = 5 } }"
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants 'infantry_equipment' "
            "owner must be a tag",
        )
    ]


def test_unclosed_force_equipment_variants_entry_reports_both_levels():
    issues, _ = _parse_division_string(
        'division_template = "Militia" '
        "force_equipment_variants = { infantry_equipment = { owner = SWE"
    )
    assert issues == [
        (
            "malformed-division",
            "division string force_equipment_variants 'infantry_equipment' is not a block",
        ),
        (
            "malformed-division",
            "division string force_equipment_variants is not a block",
        ),
    ]


# --- block-tree helpers -----------------------------------------------------


def test_block_without_a_key_has_no_label():
    nodes = _build_block_nodes("outer = { { } }")
    assert [node["label"] for node in nodes] == ["outer", None]


def test_container_of_a_top_level_block_is_none():
    nodes = _build_block_nodes("outer = { inner = { } }")
    assert _container_for(nodes, 0) == -1
    assert _container_for(nodes, 1) == 0


def test_scope_label_rejects_state_ids_and_trigger_keywords():
    assert _scope_label("123") is None
    assert _scope_label("NOT") is None
    assert _scope_label("SWE") == "SWE"
    assert _scope_label("event_target:ally") == "event_target:ally"


def test_deepest_node_at_returns_none_outside_every_block():
    nodes = _build_block_nodes("outer = { inner = { } }")
    assert _deepest_node_at(nodes, 0) == -1


def test_closest_if_returns_none_without_an_enclosing_if():
    nodes = _build_block_nodes("outer = { inner = { } }")
    assert _closest_if(nodes, 1) == -1


def test_an_if_that_does_not_enclose_the_node_is_not_its_guard():
    nodes = _build_block_nodes("if = { limit = { } }\nouter = { inner = { } }")
    outer_child = next(i for i, node in enumerate(nodes) if node["label"] == "inner")
    if_idx = next(i for i, node in enumerate(nodes) if node["label"] == "if")
    assert _is_positive_if_limit_condition(nodes, outer_child, if_idx) is False


def test_a_node_outside_an_if_never_runs_in_its_true_branch():
    nodes = _build_block_nodes("if = { limit = { } }\nouter = { inner = { } }")
    inner = next(i for i, node in enumerate(nodes) if node["label"] == "inner")
    if_idx = next(i for i, node in enumerate(nodes) if node["label"] == "if")
    assert _runs_in_if_true_branch(nodes, inner, if_idx) is False


def test_root_scope_block_resets_the_country_scope_path():
    nodes = _build_block_nodes("SWE = { ROOT = { capital_scope = { } } }")
    capital = next(
        i for i, node in enumerate(nodes) if node["label"] == "capital_scope"
    )
    assert _country_scope_path(nodes, capital) == ("ROOT",)


# --- create_unit blocks in context ------------------------------------------


def test_missing_file_yields_no_issues(tmp_path):
    assert (
        _check_created_units(
            (str(tmp_path / "gone.txt"), "gone.txt", str(tmp_path), frozenset(), {})
        )
        == []
    )


def test_top_level_create_unit_is_out_of_scope(tmp_path):
    issues = _run(
        tmp_path,
        "create_unit = {\n" f'\tdivision = "{_division()}"\n' "\towner = ROOT\n" "}\n",
    )
    assert _kinds(issues) == ["CREATE UNIT: not in a state scope"]


def test_unknown_nested_key_is_reported(tmp_path):
    issues = _run(
        tmp_path,
        "capital_scope = {\n"
        "\tcreate_unit = {\n"
        f'\t\tdivision = "{_division()}"\n'
        "\t\towner = ROOT\n"
        "\t\tmystery = { foo = bar }\n"
        "\t}\n"
        "}\n",
    )
    assert _kinds(issues) == ["CREATE UNIT: unknown key"]
    assert "mystery" in issues[0].message


def test_create_unit_without_a_division_string_is_reported(tmp_path):
    issues = _run(
        tmp_path,
        "capital_scope = {\n\tcreate_unit = {\n\t\towner = ROOT\n\t}\n}\n",
    )
    assert _kinds(issues) == ["CREATE UNIT: missing division string"]


def test_zero_factor_and_unknown_division_key_are_both_reported(tmp_path):
    division = _division(extra=" start_equipment_factor = 0 bogus = 1")
    issues = _run(
        tmp_path,
        "capital_scope = {\n"
        "\tcreate_unit = {\n"
        f'\t\tdivision = "{division}"\n'
        "\t\towner = ROOT\n"
        "\t}\n"
        "}\n",
    )
    assert _kinds(issues) == [
        "CREATE UNIT: equipment/manpower factor is zero",
        "CREATE UNIT: unknown key in division string",
    ]


def test_division_string_without_a_template_stops_the_ordering_check(tmp_path):
    issues = _run(
        tmp_path,
        "capital_scope = {\n"
        "\tcreate_unit = {\n"
        f'\t\tdivision = "{_division(template=None)}"\n'
        "\t\towner = ROOT\n"
        "\t}\n"
        "}\n",
        deleted=frozenset({"Militia"}),
    )
    assert _kinds(issues) == ["CREATE UNIT: division string lacks division_template"]


def test_execute_effect_state_block_counts_as_a_state_scope(tmp_path):
    issues = _run(
        tmp_path,
        "select_state_effect = {\n"
        "\texecute_effect = yes\n"
        "\tstate = yes\n"
        "\tcreate_unit = {\n"
        f'\t\tdivision = "{_division()}"\n'
        "\t\towner = ROOT\n"
        "\t}\n"
        "}\n",
        subdir="common/scripted_guis",
    )
    assert issues == []


def test_root_scope_template_covers_a_country_scoped_spawn(tmp_path):
    content = (
        "completion_reward = {\n"
        + _template("Militia")
        + _template("Other")
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
        "}\n"
    )
    assert _run(tmp_path, content, deleted=frozenset({"Militia"})) == []


def test_root_reset_makes_a_root_template_the_same_scope(tmp_path):
    content = (
        "completion_reward = {\n" + _template("Militia") + "\tSWE = {\n"
        "\t\tROOT = {\n"
        "\t\t\tcapital_scope = {\n"
        "\t\t\t\tcreate_unit = {\n"
        f'\t\t\t\t\tdivision = "{_division()}"\n'
        "\t\t\t\t\towner = ROOT\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _run(tmp_path, content, deleted=frozenset({"Militia"})) == []
