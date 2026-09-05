"""Tests for the unknown-modifier-name check in validate_modifiers.py.

Invalid modifier names compile silently and do nothing in-game, so this check
is the only guard against typo'd modifiers in ideas/focuses/decisions.
"""

from shared.paths import REPO_ROOT
from validate_modifiers import (
    _DOC_REL_PATH,
    Validator,
    _check_file_for_unknown_modifiers,
    _extract_top_level_definition_blocks,
    _harvest_doctrine_folder_cost_factors,
    _is_parametric_modifier,
    _load_documented_modifiers,
)

NEWLINE = chr(10)


def _write_idea_file(tmp_path, modifier_body):
    ideas_dir = tmp_path / "common" / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    path = ideas_dir / "test_ideas.txt"
    path.write_text(
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\ttest_idea = {\n"
        "\t\t\tpicture = generic_foreign_capital\n"
        "\t\t\tmodifier = {\n"
        f"{modifier_body}"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    return path


def test_unknown_modifier_in_idea_flagged(tmp_path):
    path = _write_idea_file(
        tmp_path,
        "\t\t\t\tstability_factor = 0.05\n"
        "\t\t\t\tcompletely_fake_modifier_field = 0.1\n",
    )
    results = _check_file_for_unknown_modifiers(
        (str(path), frozenset({"stability_factor"}), str(tmp_path))
    )
    assert len(results) == 1
    name, rel, lineno = results[0]
    assert name == "completely_fake_modifier_field"
    assert rel.endswith("test_ideas.txt")
    assert lineno > 0


def test_known_modifier_not_flagged(tmp_path):
    path = _write_idea_file(tmp_path, "\t\t\t\tstability_factor = 0.05\n")
    results = _check_file_for_unknown_modifiers(
        (str(path), frozenset({"stability_factor"}), str(tmp_path))
    )
    assert results == []


def test_ai_weight_modifier_block_skipped(tmp_path):
    """A modifier = {} carrying factor/base/add is an AI weight block, not a
    game modifier block — its trigger keys must not be checked as modifiers."""
    ideas_dir = tmp_path / "common" / "ideas"
    ideas_dir.mkdir(parents=True)
    path = ideas_dir / "weights.txt"
    path.write_text(
        "random_list = {\n"
        "\t50 = {\n"
        "\t\tmodifier = {\n"
        "\t\t\tfactor = 2\n"
        "\t\t\tis_major = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    results = _check_file_for_unknown_modifiers((str(path), frozenset(), str(tmp_path)))
    assert results == []


def test_parametric_modifier_families_exempt():
    assert _is_parametric_modifier("production_speed_arms_factory_factor")
    assert _is_parametric_modifier("democratic_drift")
    assert not _is_parametric_modifier("completely_fake_modifier_field")


def test_doctrine_cost_factor_is_not_a_parametric_family():
    """Doctrine cost factors are harvested per folder, not matched by shape.

    A `<word>_doctrine_cost_factor` regex used to exempt the whole shape, which
    would have whitelisted a misspelled folder name. The real set is finite and
    declared, so it is harvested from common/doctrines/folders/ instead.
    """
    for name in (
        "air_doctrine_cost_factor",
        "land_doctrine_cost_factor",
        "naval_doctrine_cost_factor",
        "special_forces_doctrine_cost_factor",
        "equipment_doctrine_cost_factor",
        "equipmnt_doctrine_cost_factor",
    ):
        assert not _is_parametric_modifier(name), name


def test_doctrine_folder_cost_factors_are_harvested(tmp_path):
    """Every declared folder generates one, including mod-defined folders.

    MD declares its own `equipment` folder beside vanilla's four, so the shipped
    vanilla documentation cannot cover the set: harvesting is what keeps
    equipment_doctrine_cost_factor valid while a typo stays reportable.
    """
    folders = tmp_path / "common" / "doctrines" / "folders"
    folders.mkdir(parents=True)
    path = folders / "doctrine_folders.txt"
    path.write_text(
        "land = {"
        + NEWLINE
        + '	name = "land_doctrine_folder"'
        + NEWLINE
        + "}"
        + NEWLINE
        + "equipment = {"
        + NEWLINE
        + '	name = "equipment_doctrine_folder"'
        + NEWLINE
        + "}"
        + NEWLINE,
        encoding="utf-8",
    )
    harvested = _harvest_doctrine_folder_cost_factors([str(path)])
    assert harvested == {
        "land_doctrine_cost_factor",
        "equipment_doctrine_cost_factor",
    }


def test_shipped_doctrine_folders_cover_the_netherlands_ideas():
    """The five folders MD ships are exactly the five modifiers in use."""
    shipped = REPO_ROOT / "common" / "doctrines" / "folders" / "doctrine_folders.txt"
    if not shipped.exists():
        return
    harvested = _harvest_doctrine_folder_cost_factors([str(shipped)])
    assert "equipment_doctrine_cost_factor" in harvested
    for vanilla in ("air", "land", "naval", "special_forces"):
        assert f"{vanilla}_doctrine_cost_factor" in harvested


def test_shipped_doc_yields_concrete_names_and_families():
    """Guard the doc parse against a format change in the next refresh.

    1.19 dropped the placeholder from the `<span>` anchor id, which silently
    left every parametric family unexpanded. The loss only surfaced as
    unknown-modifier warnings on names the doc does document.
    """
    names, templates_by_word = _load_documented_modifiers(
        str(REPO_ROOT / _DOC_REL_PATH)
    )
    assert len(names) > 4000
    assert templates_by_word["unit"]
    assert templates_by_word["operation"]
    # Expanded from <Operation>_risk's Modified types, not a `## name` header.
    assert "operation_risk" in names
    # Documented concrete modifiers the pre-1.19 doc dump predated.
    assert {"casualty_trickleback", "org_damage_multiplier"} <= names


def test_repeated_unknown_modifier_is_not_known_or_reported_repeatedly(tmp_path):
    for index in range(3):
        path = _write_idea_file(
            tmp_path,
            "\t\t\t\trepeated_fake_modifier = 0.1\n",
        )
        path.rename(path.with_name(f"test_ideas_{index}.txt"))

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    assert "repeated_fake_modifier" not in known_good

    validator.validate_modifier_names(known_good)
    assert validator.warnings_found == 1
    assert len(validator._issues) == 1
    assert "repeated_fake_modifier" in validator._issues[0].message


def test_dynamic_modifier_nested_typo_is_not_self_whitelisted(tmp_path):
    definition_dir = tmp_path / "common" / "modifier_definitions"
    definition_dir.mkdir(parents=True)
    (definition_dir / "test.txt").write_text(
        "known_dynamic_modifier_key = { value_type = number }\n",
        encoding="utf-8",
    )
    dynamic_dir = tmp_path / "common" / "dynamic_modifiers"
    dynamic_dir.mkdir(parents=True)
    (dynamic_dir / "test.txt").write_text(
        "test_dynamic_modifier = {\n"
        "\tenable = { always = yes }\n"
        "\tknown_dynamic_modifier_key = 0.1\n"
        "\tnested_dynamic_modifier_typo = 0.2\n"
        "}\n",
        encoding="utf-8",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    assert "known_dynamic_modifier_key" in known_good
    assert "nested_dynamic_modifier_typo" not in known_good

    validator.validate_modifier_names(known_good)
    assert validator.warnings_found == 1
    assert len(validator._issues) == 1
    assert "nested_dynamic_modifier_typo" in validator._issues[0].message
    # The typo is on line 4 of the file — must not be misreported as the
    # enclosing block's header line (line 1).
    assert validator._issues[0].line == 4


def test_full_run_flags_only_undefined_modifier(tmp_path):
    """A name defined in common/modifier_definitions/ enters the known-good
    set regardless of usage frequency; a made-up name in the same block warns."""
    def_dir = tmp_path / "common" / "modifier_definitions"
    def_dir.mkdir(parents=True)
    (def_dir / "00_test_modifiers.txt").write_text(
        "my_custom_defined_modifier = {\n"
        "\tcolor_type = good\n"
        "\tvalue_type = number\n"
        "}\n",
        encoding="utf-8",
    )
    _write_idea_file(
        tmp_path,
        "\t\t\t\tmy_custom_defined_modifier = 0.05\n"
        "\t\t\t\tcompletely_fake_modifier_field = 0.1\n",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    validator.validate_modifier_names(known_good)

    assert validator.warnings_found == 1
    issue = validator._issues[0]
    assert issue.category == "unknown-modifier"
    assert "completely_fake_modifier_field" in issue.message
    assert "my_custom_defined_modifier" not in issue.message


def test_md_sub_unit_generates_army_sub_unit_modifiers(tmp_path):
    """MD's own sub_units entries aren't in the vanilla doc, so the engine-
    generated modifier_army_sub_unit_<Unit>_attack/defence_factor pair must be
    synthesized from the harvested sub-unit name, not looked up in the doc."""
    units_dir = tmp_path / "common" / "units"
    units_dir.mkdir(parents=True)
    (units_dir / "test.txt").write_text(
        "sub_units = {\n\ttest_unit_bat = {\n\t\tbuy_cost_ic = 1\n\t}\n}\n",
        encoding="utf-8",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    assert "modifier_army_sub_unit_test_unit_bat_attack_factor" in known_good
    assert "modifier_army_sub_unit_test_unit_bat_defence_factor" in known_good


def test_md_operation_generates_cost_outcome_risk_modifiers(tmp_path):
    """MD's own operations aren't in the vanilla doc's Modified types, so the
    <Operation>_cost/_outcome/_risk family must be expanded against harvested
    common/operations names using the doc's span templates."""
    doc_dir = tmp_path / "resources" / "documentation"
    doc_dir.mkdir(parents=True)
    (doc_dir / "modifiers_documentation.md").write_text(
        '##  <span id="_cost"></span><Operation>_cost\n\n'
        '##  <span id="_outcome"></span><Operation>_outcome\n\n'
        '##  <span id="_risk"></span><Operation>_risk\n',
        encoding="utf-8",
    )
    ops_dir = tmp_path / "common" / "operations"
    ops_dir.mkdir(parents=True)
    (ops_dir / "test.txt").write_text(
        "increase_graft = {\n\ticon = GFX_operation_unknown\n}\n",
        encoding="utf-8",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()
    assert "increase_graft_cost" in known_good
    assert "increase_graft_outcome" in known_good
    assert "increase_graft_risk" in known_good


def test_dynamic_modifier_attacker_flag_is_structural(tmp_path):
    """`attacker_modifier = yes` is a documented vanilla dynamic-modifier
    field (combat read flag), not a modifier key — it must not warn."""
    dynamic_dir = tmp_path / "common" / "dynamic_modifiers"
    dynamic_dir.mkdir(parents=True)
    (dynamic_dir / "test.txt").write_text(
        "test_dynamic_modifier = {\n"
        "\tenable = { always = yes }\n"
        "\tattacker_modifier = yes\n"
        "}\n",
        encoding="utf-8",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_modifier_names(validator._build_known_good_set())
    assert validator.warnings_found == 0
    assert validator._issues == []


def test_md_prefixed_modifiers_always_valid(tmp_path):
    path = _write_idea_file(tmp_path, "\t\t\t\tMD_custom_thing = 0.1\n")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_modifier_names(frozenset())
    assert validator.warnings_found == 0
    assert path.exists()


def test_body_line_tracks_the_opening_brace():
    """A brace on its own line must not shift findings inside the block."""
    text = "FOO_modifier =\n{\n\tenable = {\n\t\toriginal_tag = FRA\n\t}\n}\n"
    name, name_line, body_line, _body = _extract_top_level_definition_blocks(text)[0]
    assert name == "FOO_modifier"
    assert name_line == 1
    assert body_line == 2


def test_body_line_matches_name_line_on_the_usual_shape():
    """The common `FOO = {` form keeps both lines identical."""
    text = "FOO_modifier = {\n\tenable = { always = yes }\n}\n"
    _name, name_line, body_line, _body = _extract_top_level_definition_blocks(text)[0]
    assert name_line == body_line == 1


def test_lowercase_md_prefix_is_valid(tmp_path):
    """`md_` is the same custom-modifier prefix as `MD_`, minus the tag shape
    that makes `MD_x` read as a targeted modifier."""
    _write_idea_file(tmp_path, "\t\t\t\tmd_custom_thing = 0.1\n")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_modifier_names(frozenset())
    assert validator.warnings_found == 0


def test_parametric_family_member_is_not_reported(tmp_path):
    _write_idea_file(
        tmp_path,
        "\t\t\t\tproduction_speed_arms_factory_factor = 0.1\n"
        "\t\t\t\tproduction_speed_arms_factry_factor2 = 0.1\n",
    )
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_modifier_names(frozenset())

    assert validator.warnings_found == 1
    assert "production_speed_arms_factry_factor2" in validator._issues[0].message


def test_files_without_a_modifier_block_are_not_parsed(tmp_path):
    ideas_dir = tmp_path / "common" / "ideas"
    ideas_dir.mkdir(parents=True)
    path = ideas_dir / "plain.txt"
    path.write_text("ideas = {\n\tcountry = {\n\t}\n}\n", encoding="utf-8")
    assert _check_file_for_unknown_modifiers(
        (str(path), frozenset(), str(tmp_path))
    ) == ([])


def test_ignored_directories_are_not_parsed(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    path = docs / "sample.txt"
    path.write_text(
        "modifier = {\n\tcompletely_fake_modifier_field = 0.1\n}\n", encoding="utf-8"
    )
    assert _check_file_for_unknown_modifiers(
        (str(path), frozenset(), str(tmp_path))
    ) == ([])


def test_empty_definition_file_contributes_nothing(tmp_path):
    def_dir = tmp_path / "common" / "modifier_definitions"
    def_dir.mkdir(parents=True)
    (def_dir / "empty.txt").write_text("", encoding="utf-8")
    (def_dir / "real.txt").write_text(
        "my_custom_defined_modifier = { value_type = number }\n", encoding="utf-8"
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    assert "my_custom_defined_modifier" in validator._build_known_good_set()


def test_documented_concrete_modifier_enters_the_known_good_set(tmp_path):
    doc_dir = tmp_path / "resources" / "documentation"
    doc_dir.mkdir(parents=True)
    (doc_dir / "modifiers_documentation.md").write_text(
        "## casualty_trickleback\n\nSome prose.\n", encoding="utf-8"
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    known_good = validator._build_known_good_set()

    assert "casualty_trickleback" in known_good
    assert not any("known-good set is" in line for line in validator.output_lines)


def test_empty_dynamic_modifier_file_is_skipped(tmp_path):
    dynamic_dir = tmp_path / "common" / "dynamic_modifiers"
    dynamic_dir.mkdir(parents=True)
    (dynamic_dir / "empty.txt").write_text("", encoding="utf-8")
    (dynamic_dir / "real.txt").write_text(
        "FOO_modifier = {\n\tenable = { always = yes }\n}\n", encoding="utf-8"
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_redundant_enable_gates()

    assert validator.errors_found == 1
    assert validator._issues[0].file.endswith("real.txt")


def test_full_run_covers_all_three_checks(tmp_path):
    _write_idea_file(tmp_path, "\t\t\t\tcompletely_fake_modifier_field = 0.1\n")
    dynamic_dir = tmp_path / "common" / "dynamic_modifiers"
    dynamic_dir.mkdir(parents=True)
    (dynamic_dir / "test.txt").write_text(
        "FOO_modifier = {\n\tenable = { always = yes }\n}\n", encoding="utf-8"
    )
    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    (loc_dir / "test_l_english.yml").write_text(
        'l_english:\n FOO_modifier_TT:0 "tooltip"\n', encoding="utf-8-sig"
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    categories = {issue.category for issue in validator._issues}
    assert categories == {
        "unknown-modifier",
        "dynamic-modifier-name-loc",
        "redundant-enable-gate",
    }
