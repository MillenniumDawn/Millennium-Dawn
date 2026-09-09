"""Tests for three loc-integrity checks:

1. validate_localisation.process_yml_for_syntax — formatter-mangled loc lines
   (a Prettier/pre-commit --all-files run once split `KEY:0 "value"` across
   two lines and rewrote double quotes to single quotes).
2. validate_oob_units.Validator.validate_air_wing_names_template_loc —
   air_wing_names_template = KEY must resolve to a defined English loc key.
3. validate_modifiers.Validator.validate_dynamic_modifier_name_loc — a dynamic
   modifier with a _TT/_desc loc entry must also have the bare-name key (the
   in-game header renders it).
"""

from validate_localisation import Issue, process_yml_for_syntax
from validate_modifiers import Validator as ModifiersValidator
from validate_oob_units import Validator as OOBValidator


def _write_yml(tmp_path, name, value_line):
    p = tmp_path / name
    p.write_text(f"l_english:\n {value_line}\n", encoding="utf-8-sig")
    return str(p)


def _issues_only(results):
    return [r for r in results if isinstance(r, Issue)]


# ---------------------------------------------------------------------------
# 1. Formatter-mangled loc lines
# ---------------------------------------------------------------------------


def test_syntax_check_flags_key_with_no_value(tmp_path):
    path = _write_yml(tmp_path, "a_l_english.yml", "SOME_KEY:0")
    results = _issues_only(process_yml_for_syntax((path, ["Y", "R", "G"], frozenset())))
    assert len(results) == 1
    assert results[0].category == "mangled-loc-line"
    assert "no value" in results[0].message


def test_syntax_check_flags_single_quoted_value(tmp_path):
    path = _write_yml(tmp_path, "b_l_english.yml", "SOME_KEY:0 'Some Value'")
    results = _issues_only(process_yml_for_syntax((path, ["Y", "R", "G"], frozenset())))
    assert len(results) == 1
    assert results[0].category == "mangled-loc-line"
    assert "single quotes" in results[0].message


def test_syntax_check_clean_double_quoted_value(tmp_path):
    path = _write_yml(tmp_path, "c_l_english.yml", 'SOME_KEY:0 "Some Value"')
    results = _issues_only(process_yml_for_syntax((path, ["Y", "R", "G"], frozenset())))
    assert results == []


# ---------------------------------------------------------------------------
# 2. air_wing_names_template loc cross-check
# ---------------------------------------------------------------------------


def _write_air_wing_names(tmp_path, key):
    names_dir = tmp_path / "common" / "units" / "names"
    names_dir.mkdir(parents=True)
    (names_dir / "00_TST_names.txt").write_text(
        f"TST = {{\n\tair_wing_names_template = {key}\n}}\n", encoding="utf-8"
    )


def _write_loc_file(tmp_path, keys):
    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    body = "\n".join(f' {k}: "value"' for k in keys)
    (loc_dir / "test_l_english.yml").write_text(
        f"l_english:\n{body}\n", encoding="utf-8-sig"
    )


def test_air_wing_template_missing_loc_key_flagged(tmp_path):
    _write_air_wing_names(tmp_path, "AIR_WING_NAME_TST_FALLBACK")
    _write_loc_file(tmp_path, [])

    validator = OOBValidator(mod_path=str(tmp_path), use_colors=False)
    validator.validate_air_wing_names_template_loc()

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "air-wing-template-loc"
    assert "AIR_WING_NAME_TST_FALLBACK" in issue.message


def test_air_wing_template_defined_loc_key_clean(tmp_path):
    _write_air_wing_names(tmp_path, "AIR_WING_NAME_TST_FALLBACK")
    _write_loc_file(tmp_path, ["AIR_WING_NAME_TST_FALLBACK"])

    validator = OOBValidator(mod_path=str(tmp_path), use_colors=False)
    validator.validate_air_wing_names_template_loc()

    assert validator._issues == []


# ---------------------------------------------------------------------------
# 3. Dynamic modifier bare-name loc key
# ---------------------------------------------------------------------------


def _write_dynamic_modifier(tmp_path, body):
    dm_dir = tmp_path / "common" / "dynamic_modifiers"
    dm_dir.mkdir(parents=True)
    (dm_dir / "00_test_dynamic_modifiers.txt").write_text(body, encoding="utf-8")


def test_dynamic_modifier_missing_bare_key_flagged(tmp_path):
    _write_dynamic_modifier(
        tmp_path,
        "test_dynamic_modifier = {\n"
        "\tenable = { always = yes }\n"
        "\tstability_factor = 0.1\n"
        "}\n",
    )
    _write_loc_file(tmp_path, ["test_dynamic_modifier_TT"])

    validator = ModifiersValidator(mod_path=str(tmp_path), use_colors=False)
    validator.validate_dynamic_modifier_name_loc()

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "dynamic-modifier-name-loc"
    assert "test_dynamic_modifier" in issue.message


def test_dynamic_modifier_with_bare_key_clean(tmp_path):
    _write_dynamic_modifier(
        tmp_path,
        "test_dynamic_modifier = {\n"
        "\tenable = { always = yes }\n"
        "\tstability_factor = 0.1\n"
        "}\n",
    )
    _write_loc_file(tmp_path, ["test_dynamic_modifier", "test_dynamic_modifier_TT"])

    validator = ModifiersValidator(mod_path=str(tmp_path), use_colors=False)
    validator.validate_dynamic_modifier_name_loc()

    assert validator._issues == []
