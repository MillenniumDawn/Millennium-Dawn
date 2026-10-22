"""Tests for the create_unit checks in validate_oob_units.py.

A create_unit only spawns units in a state scope, needs a single-line division
string that parses as army data and names a division_template, and must set
owner. When it defines the template itself, the template must come first.
When the template it names is also removed by delete_unit_template_and_units
somewhere in the mod, the create_unit must create it earlier in the same effect
or sit behind a has_template guard: persistent.cpp reports a missing runtime
template as a malformed token.
"""

import argparse
from textwrap import indent

import pytest
import validate_oob_units as oob
from validate_oob_units import (
    Validator,
    _check_created_units,
    _parse_division_string,
    build_division_template_index,
    division_template_entries,
)
from validator_common import Severity

# The engine stores inner quotes in the division string as backslash-escaped
# (\\\"...\\\"). Build them explicitly so no source-level unescaping bites.
_BS = chr(92)
_LATE = "CREATE UNIT: template defined after create_unit"
_ENSURE = "CREATE UNIT: template not created or has_template-guarded in this effect"
_FOREIGN = "CREATE UNIT: foreign-only static template definition"
_NO_FACTOR = "CREATE UNIT: division string lacks start_equipment_factor"


def _esc_quote(value):
    """Wrap *value* in engine-escaped quotes (\\\"value\\\")."""
    return _BS + '"' + value + _BS + '"'


def _div_for(tname, unitname):
    """A division string referencing *tname* with the given unit *unitname*."""
    base = "name = " + _esc_quote(unitname)
    base += " division_template = " + _esc_quote(tname)
    return base + " start_equipment_factor = 1.0"


def _run(
    content,
    tmp_path,
    filename="test.txt",
    deleted_names=frozenset(),
    closure=None,
    template_owners=None,
    template_wildcard=frozenset(),
):
    target = tmp_path / "common" / "national_focus" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _check_created_units(
        (
            str(target),
            filename,
            str(tmp_path),
            deleted_names,
            closure or {},
            template_owners or {},
            template_wildcard,
        )
    )


def _cats(issues):
    return [i.category for i in issues]


def _block(name, content):
    return f"{name} = {{\n{indent(content, chr(9))}\n}}"


def _division_template(name):
    return _block(
        "division_template",
        f'\tname = "{name}"\n\tregiments = {{ L_Inf_Bat = {{ x = 0 y = 0 }} }}',
    )


def _create_unit(div, owner="ROOT"):
    return _block("create_unit", f'\tdivision = "{div}"\n\towner = {owner}')


def _focus_with_effect(effect):
    return (
        "focus_tree = {\n\tfocus = {\n\t\tid = TAG_focus\n\t\tx = 0\n\t\ty = 0\n"
        "\t\tcost = 5\n\t\tcompletion_reward = {\n\t\t\thidden_effect = {\n"
        f"{indent(effect, chr(9) * 4)}\n"
        "\t\t\t}\n\t\t}\n\t\tai_will_do = { base = 1 }\n\t}\n}\n"
    )


def _focus_with_template_owner(owner, template):
    return (
        "focus_tree = {\n"
        f"\tcountry = {{ modifier = {{ add = 20 original_tag = {owner} }} }}\n"
        f"{indent(template, chr(9))}\n"
        "}\n"
    )


def _template_index(*sources):
    return build_division_template_index(
        [division_template_entries(rel, raw) for rel, raw in sources]
    )


def _guarded_focus(div):
    return """focus_tree = {
	focus = {
		id = TAG_focus
		x = 0
		y = 0
		cost = 5
		completion_reward = {
			hidden_effect = {
				if = {
					limit = { NOT = { has_template = "Territorial Defense Brigade" } }
					division_template = {
						name = "Territorial Defense Brigade"
						regiments = {
							L_Inf_Bat = { x = 0 y = 0 }
						}
					}
				}
				capital_scope = {
					create_unit = {
						division = "{DIV}"
						owner = ROOT
					}
				}
			}
		}
		ai_will_do = { base = 1 }
	}
}
""".replace("{DIV}", div)


_GUARDED = _guarded_focus(
    _div_for("Territorial Defense Brigade", "1st Territorial Defense Brigade")
)
_MILITIA = _div_for("Militia", "Militia")


# ---- the create_unit block -------------------------------------------------


def test_missing_owner_and_out_of_scope_flagged(tmp_path):
    content = _GUARDED.replace(
        "\t\t\t\tcapital_scope = {\n\t\t\t\t\tcreate_unit = {",
        "\t\t\t\tcreate_unit = {",
    ).replace("\t\t\t\t\t\towner = ROOT\n", "")
    cats = _cats(_run(content, tmp_path))
    assert "CREATE UNIT: not in a state scope" in cats
    assert "CREATE UNIT: missing owner" in cats


def test_multiline_division_flagged(tmp_path):
    div = _div_for("Territorial Defense Brigade", "1st Territorial Defense Brigade")
    content = _GUARDED.replace(
        div, div.replace("division_template", "\n\t\t\t\t\t\tdivision_template", 1)
    )
    assert "CREATE UNIT: division string spans lines" in _cats(_run(content, tmp_path))


def test_unescaped_inner_quotes_break_the_division_string(tmp_path):
    div = 'name = "1st Operational Brigade division_template = Natsionalna'
    content = _focus_with_effect(_create_unit(div, owner="UKR"))
    issues = _run(content, tmp_path)
    assert "CREATE UNIT: division string does not parse" in _cats(issues)


def test_umlaut_create_unit_is_flagged(tmp_path):
    div = _div_for("militärdistriktet", "militärdistriktet")
    content = _guarded_focus(div).replace(
        "Territorial Defense Brigade", "militärdistriktet"
    )
    issues = _run(content, tmp_path)
    assert "CREATE UNIT: division string has German/Danish letters" in _cats(issues)
    assert any(
        "out-of-bounds letter in: militärdistriktet" in i.message for i in issues
    )
    assert all(
        i.severity == Severity.WARNING for i in issues if "German/Danish" in i.category
    )


def test_extra_create_unit_sources_are_checked(tmp_path):
    content = _GUARDED.replace("\t\t\t\t\t\towner = ROOT\n", "")
    sources = (
        "common/on_actions/test.txt",
        "common/operations/test.txt",
        "common/resistance_compliance_modifiers/test.txt",
        "common/scripted_guis/test.txt",
    )
    for source in sources:
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    validator = Validator(str(tmp_path), workers=1)
    validator.validate_created_units()

    assert validator.errors_found == len(sources)
    assert {issue.file for issue in validator._issues} == set(sources)
    assert all(issue.severity == Severity.ERROR for issue in validator._issues)


# ---- division string factors -----------------------------------------------

_ZERO = "CREATE UNIT: equipment/manpower factor is zero"
_BELOW = "CREATE UNIT: equipment/manpower factor below 0.01"


@pytest.mark.parametrize(
    ("factor", "category"),
    [
        ("start_equipment_factor = +0", _ZERO),
        ("start_equipment_factor = 1.0 start_manpower_factor = 0.", _ZERO),
        ("start_equipment_factor = 1.0 start_manpower_factor = .0", _ZERO),
        ("start_equipment_factor = 0.005", _BELOW),
        ("start_equipment_factor = -0.5", _BELOW),
        ("start_equipment_factor = 1.0 start_manpower_factor = -0.5", _BELOW),
        ("start_equipment_factor = 0.01", None),
    ],
)
def test_division_factor_floor(tmp_path, factor, category):
    issues = _run(_GUARDED.replace("start_equipment_factor = 1.0", factor), tmp_path)
    if category is None:
        assert issues == []
    else:
        assert [i.severity for i in issues if i.category == category] == [
            Severity.ERROR
        ]


def _missing_factor_validator(tmp_path, **kwargs):
    target = tmp_path / "common" / "national_focus" / "test.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        _GUARDED.replace(" start_equipment_factor = 1.0", ""), encoding="utf-8"
    )
    validator = Validator(str(tmp_path), workers=1, **kwargs)
    validator.validate_created_units()
    return validator


@pytest.mark.parametrize(
    ("kwargs", "reported"),
    [({}, False), ({"missing_equipment_factor": True}, True)],
    ids=["off by default", "flag on"],
)
def test_missing_equipment_factor(tmp_path, kwargs, reported):
    validator = _missing_factor_validator(tmp_path, **kwargs)
    assert validator.missing_equipment_factor is reported
    assert (_NO_FACTOR in _cats(validator._issues)) is reported


def test_missing_equipment_factor_flag_is_registered():
    parser = argparse.ArgumentParser()
    oob._add_extra_args(parser)
    assert parser.parse_args(["--missing-equipment-factor"]).missing_equipment_factor
    assert not parser.parse_args([]).missing_equipment_factor


# ---- division string parsing -----------------------------------------------


@pytest.mark.parametrize(
    ("text", "kinds", "tname"),
    [
        pytest.param(
            'name = "Infantry Division" division_template = "Infantry Division" '
            "start_experience_factor = 0.5",
            [],
            "Infantry Division",
            id="experience factor",
        ),
        pytest.param(
            'name = "Artie" division_template = "Artillery Division" '
            "start_manpower_factor = 0.3",
            [],
            "Artillery Division",
            id="manpower factor",
        ),
        pytest.param(
            'name = "Tank division" division_template = "Tank Division" '
            "start_manpower_factor = 1 force_equipment_variants = { "
            'medium_tank_chassis_2 = { owner = "USA" amount = 100 '
            'version_name = "M4 Sherman" }}',
            [],
            "Tank Division",
            id="force_equipment_variants",
        ),
        pytest.param(
            'division_template = "Infantry Division" start_experience_factor = yes',
            ["malformed-division"],
            "Infantry Division",
            id="non-numeric factor",
        ),
        pytest.param(
            'division_template = "Tank Division" force_equipment_variants = { '
            'medium_tank_chassis_2 = { owner = "USA" slot = 1 } }',
            ["unknown-division-key"],
            "Tank Division",
            id="unknown force_equipment_variants key",
        ),
        pytest.param(
            'division_template = "Tank Division" force_equipment_variants = { '
            "medium_tank_chassis_2 = { owner = USA amount = 100 version_name = Sherman } }",
            ["unquoted-value"],
            "Tank Division",
            id="unquoted version_name",
        ),
        pytest.param(
            "division_template = Infantry start_experience_factor = 0.5",
            ["unquoted-value", "missing-template"],
            None,
            id="unquoted template",
        ),
    ],
)
def test_parse_division_string(text, kinds, tname):
    issues, found = _parse_division_string(text)
    assert [kind for kind, _message in issues] == kinds
    assert found == tname
    if "malformed-division" in kinds:
        assert any("must be a number" in message for _kind, message in issues)


# ---- template ordering and the ensure pattern ------------------------------


@pytest.mark.parametrize(
    ("content", "deleted"),
    [
        pytest.param(
            """focus_tree = {
	focus = {
		id = TAG_focus
		x = 0
		y = 0
		cost = 5
		completion_reward = {
			hidden_effect = {
				if = {
					limit = { has_template = "Quds" }
					capital_scope = {
						create_unit = {
							division = "{DIV}"
							owner = ROOT
						}
					}
				}
				else = {
					division_template = {
						name = "Quds"
						regiments = {
							Special_Forces = { x = 0 y = 0 }
						}
					}
				}
			}
		}
		ai_will_do = { base = 1 }
	}
}
""".replace("{DIV}", _div_for("Quds", "Quds")),
            frozenset(),
            # The create_unit under the guard runs only once the template exists.
            id="has_template guard with the definition in else",
        ),
        pytest.param(
            _focus_with_effect(
                _block(
                    "capital_scope",
                    _create_unit(_div_for("Tip-e Piade Nezam", "Niru"), owner="PER"),
                )
            ),
            frozenset(),
            id="template nothing deletes",
        ),
        pytest.param(
            _focus_with_effect(
                "\n".join(
                    (
                        _block(
                            "PER",
                            _block(
                                "if",
                                "\n".join(
                                    (
                                        _block(
                                            "limit",
                                            _block(
                                                "NOT",
                                                'has_template = "Tip-e Piade Nezam"',
                                            ),
                                        ),
                                        _division_template("Tip-e Piade Nezam"),
                                    )
                                ),
                            ),
                        ),
                        _block(
                            "406",
                            _create_unit(
                                _div_for("Tip-e Piade Nezam", "Niru"), owner="PER"
                            ),
                        ),
                    )
                )
            ),
            frozenset({"Tip-e Piade Nezam"}),
            id="owner-scoped template covers a state spawn",
        ),
    ],
)
def test_create_unit_patterns_that_are_clean(tmp_path, content, deleted):
    assert _run(content, tmp_path, deleted_names=deleted) == []


@pytest.mark.parametrize(
    "effect",
    [
        pytest.param(
            "\n".join(
                (
                    _block(
                        "if",
                        "\n".join(
                            (
                                _block(
                                    "limit", _block("FSA", 'has_template = "Militia"')
                                ),
                                _block("capital_scope", _create_unit(_MILITIA)),
                            )
                        ),
                    ),
                    _division_template("Militia"),
                )
            ),
            id="foreign has_template guard",
        ),
        *(
            pytest.param(
                "\n".join(
                    (
                        _block(
                            "if",
                            "\n".join(
                                (
                                    _block("limit", condition),
                                    _block("capital_scope", _create_unit(_MILITIA)),
                                )
                            ),
                        ),
                        _division_template("Militia"),
                    )
                ),
                id=condition,
            )
            for condition in (
                'NOT = { has_template = "Militia" }',
                'OR = { has_template = "Militia" always = yes }',
            )
        ),
        pytest.param(
            "\n".join(
                (
                    _block("every_country", _division_template("Militia")),
                    _block("capital_scope", _create_unit(_MILITIA)),
                    _division_template("Militia"),
                )
            ),
            id="template defined in a country iterator first",
        ),
    ],
)
def test_late_local_definition_is_flagged(tmp_path, effect):
    assert _LATE in _cats(_run(_focus_with_effect(effect), tmp_path))


def test_prior_ensure_effect_call_satisfies_the_guard(tmp_path):
    content = _focus_with_effect(
        "TAG_setup = yes\n" + _block("capital_scope", _create_unit(_MILITIA))
    )
    closure = {"TAG_setup": frozenset({"Militia"})}
    deleted = frozenset({"Militia"})
    assert _run(content, tmp_path, deleted_names=deleted) != []
    assert _run(content, tmp_path, deleted_names=deleted, closure=closure) == []


def test_force_equipment_variants_owner_is_not_the_block_owner(tmp_path):
    # The donor tag inside force_equipment_variants must not be mistaken for
    # the create_unit's own owner when resolving which country's template covers.
    div = (
        _MILITIA
        + " force_equipment_variants = { infantry_weapons_1 = { owner = SOV } }"
    )
    content = _focus_with_effect(
        "\n".join(
            (
                _block("SOV", _division_template("Militia")),
                _block("capital_scope", _create_unit(div)),
            )
        )
    )
    assert _ENSURE in _cats(
        _run(content, tmp_path, deleted_names=frozenset({"Militia"}))
    )


# ---- static template owners ------------------------------------------------


def test_ukraine_spawn_warns_for_foreign_static_templates(tmp_path):
    div = (
        "name = "
        + _esc_quote("1st Operational Brigade of the National Guard of Ukraine")
        + " division_template = "
        + _esc_quote("Natsionalna Hvardiya")
        + " start_experience_factor = 0.1"
    )
    owners, wildcard = _template_index(
        *(
            (
                f"common/national_focus/{name}.txt",
                _focus_with_template_owner(
                    tag, _division_template("Natsionalna Hvardiya")
                ),
            )
            for name, tag in (
                ("Odessa", "OPR"),
                ("Malorossiya", "MLR"),
                ("05_south_ossetia", "SOO"),
            )
        )
    )
    issues = _run(
        _focus_with_effect(_create_unit(div, owner="UKR")),
        tmp_path,
        template_owners=owners,
        template_wildcard=wildcard,
    )
    assert "CREATE UNIT: division string does not parse" not in _cats(issues)
    foreign = [issue for issue in issues if issue.category == _FOREIGN]
    assert len(foreign) == 1
    assert "only static definitions found for MLR, OPR, SOO" in foreign[0].message
    assert "none found for UKR" in foreign[0].message


def _militia_index(owner):
    return _template_index(
        (
            "common/national_focus/Odessa.txt",
            _focus_with_template_owner(owner, _division_template("Militia")),
        )
    )


def test_unknown_definition_scope_is_wildcard(tmp_path):
    owners, wildcard = _template_index(
        (
            "common/scripted_effects/templates.txt",
            "event_target:recipient = { " + _division_template("Militia") + " }",
        )
    )
    issues = _run(
        _focus_with_effect(_create_unit(_MILITIA, owner="UKR")),
        tmp_path,
        template_owners=owners,
        template_wildcard=wildcard,
    )
    assert _FOREIGN not in _cats(issues)
    assert "Militia" in wildcard


def test_nested_literal_scope_overrides_focus_root(tmp_path):
    source = _focus_with_template_owner(
        "OPR", _block("UKR", _division_template("Militia"))
    )
    owners, wildcard = _template_index(("common/national_focus/shared.txt", source))
    assert owners == {"Militia": frozenset({"UKR"})}
    issues = _run(
        _focus_with_effect(_create_unit(_MILITIA, owner="UKR")),
        tmp_path,
        template_owners=owners,
        template_wildcard=wildcard,
    )
    assert _FOREIGN not in _cats(issues)


def test_dynamic_template_owner_is_skipped(tmp_path):
    owners, wildcard = _militia_index("OPR")
    issues = _run(
        _focus_with_effect(_create_unit(_MILITIA, owner="var:UKR")),
        tmp_path,
        template_owners=owners,
        template_wildcard=wildcard,
    )
    assert _FOREIGN not in _cats(issues)


def test_staged_definition_change_rescans_unstaged_callers(tmp_path, monkeypatch):
    definition = tmp_path / "common" / "national_focus" / "definition.txt"
    definition.parent.mkdir(parents=True, exist_ok=True)
    definition.write_text(
        _focus_with_template_owner("OPR", _division_template("Militia")),
        encoding="utf-8",
    )
    caller = tmp_path / "common" / "national_focus" / "caller.txt"
    caller.write_text(
        _focus_with_effect(_create_unit(_MILITIA, owner="UKR")), encoding="utf-8"
    )
    monkeypatch.setattr(
        oob, "get_staged_files", lambda *args, **kwargs: [str(definition)]
    )
    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, staged_only=True, workers=1
    )

    validator.validate_created_units()

    assert _FOREIGN in _cats(validator._issues)


def test_changed_lines_match_detects_a_staged_removal(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    commands = []
    returncodes = iter((1, 1))

    def _run_git(command, **_kwargs):
        commands.append(command)
        return oob.subprocess.CompletedProcess(command, next(returncodes))

    monkeypatch.setattr(oob.subprocess, "run", _run_git)
    path = str(tmp_path / "common" / "national_focus" / "definition.txt")

    assert oob._changed_lines_match(
        str(tmp_path), [path], oob._DIVISION_TEMPLATE_DEF_PATTERN
    )
    assert commands[1][2] == "--cached"
    assert any(arg.startswith("-Gdivision_template") for arg in commands[1])
