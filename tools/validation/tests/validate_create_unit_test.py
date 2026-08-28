"""Tests for the create_unit effect structural checks in validate_oob_units.py.

A create_unit only spawns units in a state scope, needs a single-line division
string that parses as army data and names a division_template, and must set
owner. When it defines the template itself, the template must come first.
When the template it names is also removed by delete_unit_template_and_units
somewhere in the mod, the create_unit must create it earlier in the same effect
or sit behind a has_template guard — persistent.cpp reports a missing runtime
template as a malformed token. Templates nothing deletes are not required to
carry that ensure pattern.
"""

from textwrap import indent

from validate_oob_units import (
    Validator,
    _check_created_units,
    _deleted_template_names,
    _effect_template_closure,
    _parse_division_string,
)
from validator_common import Severity

# The engine stores inner quotes in the division string as backslash-escaped
# (\\\"...\\\"). Build them explicitly so no source-level unescaping bites.
_BS = chr(92)


def _esc_quote(value):
    """Wrap *value* in engine-escaped quotes (\\\"value\\\")."""
    return _BS + '"' + value + _BS + '"'


def _div_for(tname, unitname):
    """A division string referencing *tname* with the given unit *unitname*."""
    return (
        "name = " + _esc_quote(unitname) + " division_template = " + _esc_quote(tname)
    )


def _run(
    content, tmp_path, filename="test.txt", deleted_names=frozenset(), closure=None
):
    target = tmp_path / "common" / "national_focus" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _check_created_units(
        (str(target), filename, str(tmp_path), deleted_names, closure or {})
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


def test_guarded_correct_pattern_is_clean(tmp_path):
    assert _run(_GUARDED, tmp_path) == []


def test_template_defined_after_create_unit_is_flagged(tmp_path):
    content = _GUARDED.replace(
        """			hidden_effect = {
				if = {
					limit = { NOT = { has_template = "Territorial Defense Brigade" } }
					division_template = {
						name = "Territorial Defense Brigade"
						regiments = {
							L_Inf_Bat = { x = 0 y = 0 }
						}
					}
				}
				capital_scope = {""",
        """			hidden_effect = {
				capital_scope = {""",
    ).replace(
        """						owner = ROOT
					}
				}
			}
		}""",
        """						owner = ROOT
					}
				}
				division_template = {
					name = "Territorial Defense Brigade"
					regiments = {
						L_Inf_Bat = { x = 0 y = 0 }
					}
				}
			}
		}""",
    )
    cats = _cats(_run(content, tmp_path))
    assert "CREATE UNIT: template defined after create_unit" in cats


def test_missing_owner_and_out_of_scope_flagged(tmp_path):
    content = _GUARDED.replace(
        "				capital_scope = {\n					create_unit = {",
        "				create_unit = {",
    ).replace("						owner = ROOT\n", "")
    cats = _cats(_run(content, tmp_path))
    assert "CREATE UNIT: not in a state scope" in cats
    assert "CREATE UNIT: missing owner" in cats


def test_multiline_division_flagged(tmp_path):
    div = _div_for("Territorial Defense Brigade", "1st Territorial Defense Brigade")
    content = _GUARDED.replace(
        div, div.replace("division_template", "\n\t\t\t\t\t\tdivision_template", 1)
    )
    cats = _cats(_run(content, tmp_path))
    assert "CREATE UNIT: division string spans lines" in cats


# An `if = { limit = { has_template = X } } ... else = { division_template = X }`
# is mutually exclusive: the create_unit under the guard only runs when the
# template already exists, so the later definition is not an ordering bug.
def test_has_template_guard_else_pattern_is_clean(tmp_path):
    div = _div_for("Quds", "Quds")
    content = """focus_tree = {
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
""".replace("{DIV}", div)
    assert _run(content, tmp_path) == []


def test_unguarded_create_unit_without_template_is_flagged(tmp_path):
    div = _div_for("Tip-e Piade Nezam", "Niru")
    content = _focus_with_effect(
        _block("capital_scope", _create_unit(div, owner="PER"))
    )
    issues = _run(content, tmp_path, deleted_names=frozenset({"Tip-e Piade Nezam"}))
    assert (
        "CREATE UNIT: template not created or has_template-guarded in this effect"
        in _cats(issues)
    )
    assert all(i.severity == Severity.WARNING for i in issues)


def test_oob_template_without_delete_is_clean(tmp_path):
    div = _div_for("Tip-e Piade Nezam", "Niru")
    content = _focus_with_effect(
        _block("capital_scope", _create_unit(div, owner="PER"))
    )
    assert _run(content, tmp_path) == []


def test_owner_scoped_template_covers_state_spawn(tmp_path):
    div = _div_for("Tip-e Piade Nezam", "Niru")
    effect = "\n".join(
        (
            _block(
                "PER",
                _block(
                    "if",
                    "\n".join(
                        (
                            _block(
                                "limit",
                                _block("NOT", 'has_template = "Tip-e Piade Nezam"'),
                            ),
                            _division_template("Tip-e Piade Nezam"),
                        )
                    ),
                ),
            ),
            _block("406", _create_unit(div, owner="PER")),
        )
    )
    assert (
        _run(
            _focus_with_effect(effect),
            tmp_path,
            deleted_names=frozenset({"Tip-e Piade Nezam"}),
        )
        == []
    )


def test_foreign_template_does_not_satisfy_ensure(tmp_path):
    div = _div_for("Militia", "Militia")
    content = _focus_with_effect(
        "\n".join(
            (
                _block("FSA", _division_template("Militia")),
                _block("capital_scope", _create_unit(div)),
            )
        )
    )
    assert (
        "CREATE UNIT: template not created or has_template-guarded in this effect"
        in _cats(_run(content, tmp_path, deleted_names=frozenset({"Militia"})))
    )


# A template defined before the create_unit is fine even when a second,
# same-named definition appears later (e.g. one per scope). The earliest
# definition must be the one compared.
def test_earliest_template_definition_wins(tmp_path):
    div = _div_for("Territorial Defense Brigade", "1st Territorial Defense Brigade")
    content = """focus_tree = {
	focus = {
		id = TAG_focus
		x = 0
		y = 0
		cost = 5
		completion_reward = {
			hidden_effect = {
				division_template = {
					name = "Territorial Defense Brigade"
					regiments = { L_Inf_Bat = { x = 0 y = 0 } }
				}
				capital_scope = {
					create_unit = {
						division = "{DIV}"
						owner = ROOT
					}
				}
				division_template = {
					name = "Territorial Defense Brigade"
					regiments = { L_Inf_Bat = { x = 0 y = 1 } }
				}
			}
		}
		ai_will_do = { base = 1 }
	}
}
""".replace("{DIV}", div)
    assert _run(content, tmp_path) == []


# A decision's effect runs in `remove_effect`; a template defined in a separate
# decision must not be compared across the boundary.
def test_decision_remove_effect_boundary(tmp_path):
    div = _div_for("Expanded", "Expanded")
    content = """decisions = {
	category = {
		decision_a = {
			remove_effect = {
				94 = {
					create_unit = {
						division = "{DIV}"
						owner = SPR
					}
				}
			}
		}
		decision_b = {
			remove_effect = {
				SPR = {
					division_template = {
						name = "Expanded"
						regiments = { L_arm_Bat = { x = 0 y = 0 } }
					}
				}
			}
		}
	}
}
""".replace("{DIV}", div)
    issues = _run(content, tmp_path, filename="decisions.txt")
    assert all("template defined after" not in c for c in _cats(issues))


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


def test_deleted_template_names_reads_delete_blocks(tmp_path):
    target = tmp_path / "common" / "ideas" / "test.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        'on_remove = {\n\tdelete_unit_template_and_units = {\n\t\tdivision_template = "OMON"\n'
        "\t\tdisband = yes\n\t}\n}\n"
        '# delete_unit_template_and_units = { division_template = "Commented" }\n',
        encoding="utf-8",
    )
    assert _deleted_template_names(str(tmp_path), [str(target)]) == frozenset({"OMON"})


def test_ideas_deletion_drives_missing_template_ensure(tmp_path):
    div = _div_for("OMON", "OMON Chechnya")
    idea = tmp_path / "common" / "ideas" / "test.txt"
    idea.parent.mkdir(parents=True, exist_ok=True)
    idea.write_text(
        'on_remove = {\n\tdelete_unit_template_and_units = {\n\t\tdivision_template = "OMON"\n\t}\n}\n',
        encoding="utf-8",
    )
    focus = tmp_path / "common" / "national_focus" / "test.txt"
    focus.parent.mkdir(parents=True, exist_ok=True)
    focus.write_text(
        _focus_with_effect(_block("capital_scope", _create_unit(div))),
        encoding="utf-8",
    )

    validator = Validator(str(tmp_path), workers=1)
    validator.validate_created_units()

    assert [issue.category for issue in validator._issues] == [
        "CREATE UNIT: template not created or has_template-guarded in this effect"
    ]
    assert validator._issues[0].severity == Severity.WARNING


def test_effect_closure_follows_nested_calls(tmp_path):
    target = tmp_path / "common" / "scripted_effects" / "test.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        _block("TAG_ensure_militia", _division_template("Militia"))
        + "\n"
        + _block("TAG_setup", "\tTAG_ensure_militia = yes")
        + "\n",
        encoding="utf-8",
    )
    closure = _effect_template_closure(str(tmp_path), [str(target)])
    assert closure["TAG_ensure_militia"] == frozenset({"Militia"})
    assert closure["TAG_setup"] == frozenset({"Militia"})


def test_prior_ensure_effect_call_satisfies_the_guard(tmp_path):
    div = _div_for("Militia", "Militia")
    content = _focus_with_effect(
        "TAG_setup = yes\n" + _block("capital_scope", _create_unit(div))
    )
    closure = {"TAG_setup": frozenset({"Militia"})}
    assert _run(content, tmp_path, deleted_names=frozenset({"Militia"})) != []
    assert (
        _run(content, tmp_path, deleted_names=frozenset({"Militia"}), closure=closure)
        == []
    )


def test_ensure_effect_call_after_create_unit_does_not_count(tmp_path):
    div = _div_for("Militia", "Militia")
    content = _focus_with_effect(
        _block("capital_scope", _create_unit(div)) + "\nTAG_setup = yes"
    )
    closure = {"TAG_setup": frozenset({"Militia"})}
    cats = _cats(
        _run(content, tmp_path, deleted_names=frozenset({"Militia"}), closure=closure)
    )
    assert (
        "CREATE UNIT: template not created or has_template-guarded in this effect"
        in cats
    )


def test_force_equipment_variants_owner_is_not_the_block_owner(tmp_path):
    # The donor tag inside force_equipment_variants must not be mistaken for
    # the create_unit's own owner when resolving which country's template covers.
    div = (
        _div_for("Militia", "Militia")
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
    cats = _cats(_run(content, tmp_path, deleted_names=frozenset({"Militia"})))
    assert (
        "CREATE UNIT: template not created or has_template-guarded in this effect"
        in cats
    )


def test_foreign_template_does_not_mask_late_local_definition(tmp_path):
    div = _div_for("Militia", "Militia")
    content = _focus_with_effect(
        "\n".join(
            (
                _block("FSA", _division_template("Militia")),
                _block("capital_scope", _create_unit(div)),
                _division_template("Militia"),
            )
        )
    )
    assert "CREATE UNIT: template defined after create_unit" in _cats(
        _run(content, tmp_path)
    )


def test_foreign_has_template_guard_does_not_mask_late_local_definition(tmp_path):
    div = _div_for("Militia", "Militia")
    guarded_create = "\n".join(
        (
            _block("limit", _block("FSA", 'has_template = "Militia"')),
            _block("capital_scope", _create_unit(div)),
        )
    )
    content = _focus_with_effect(
        "\n".join((_block("if", guarded_create), _division_template("Militia")))
    )
    assert "CREATE UNIT: template defined after create_unit" in _cats(
        _run(content, tmp_path)
    )


def test_non_guaranteeing_has_template_guards_do_not_skip_ordering(tmp_path):
    div = _div_for("Militia", "Militia")
    for index, condition in enumerate(
        (
            'NOT = { has_template = "Militia" }',
            'OR = { has_template = "Militia" always = yes }',
        )
    ):
        guarded_create = "\n".join(
            (
                _block("limit", condition),
                _block("capital_scope", _create_unit(div)),
            )
        )
        content = _focus_with_effect(
            "\n".join((_block("if", guarded_create), _division_template("Militia")))
        )
        assert "CREATE UNIT: template defined after create_unit" in _cats(
            _run(content, tmp_path, filename=f"guard-{index}.txt")
        )


def test_country_iterator_template_does_not_mask_late_local_definition(tmp_path):
    div = _div_for("Militia", "Militia")
    content = _focus_with_effect(
        "\n".join(
            (
                _block("every_country", _division_template("Militia")),
                _block("capital_scope", _create_unit(div)),
                _division_template("Militia"),
            )
        )
    )
    assert "CREATE UNIT: template defined after create_unit" in _cats(
        _run(content, tmp_path)
    )


# A numeric state block leaves the country scope alone. State IDs 100-999 have
# the same shape as a country tag, so both widths must reach the same verdict.
def test_state_id_block_does_not_mask_late_local_definition(tmp_path):
    div = _div_for("Militia", "Militia")
    for state in ("129", "1054"):
        effect = _block(
            "RSK",
            "\n".join(
                (
                    _block(state, _create_unit(div, owner="RSK")),
                    _division_template("Militia"),
                )
            ),
        )
        assert "CREATE UNIT: template defined after create_unit" in _cats(
            _run(_focus_with_effect(effect), tmp_path, filename=f"state-{state}.txt")
        )


def test_other_event_option_does_not_mask_late_definition(tmp_path):
    div = _div_for("Militia", "Militia")
    content = """country_event = {
	id = test.1
	option = {
		division_template = {
			name = "Militia"
			regiments = { L_Inf_Bat = { x = 0 y = 0 } }
		}
	}
	option = {
		1 = {
			create_unit = {
				division = "{DIV}"
				owner = ROOT
			}
		}
		division_template = {
			name = "Militia"
			regiments = { L_Inf_Bat = { x = 0 y = 0 } }
		}
	}
}
""".replace("{DIV}", div)
    assert "CREATE UNIT: template defined after create_unit" in _cats(
        _run(content, tmp_path, filename="events.txt")
    )


def _kinds(issues):
    return [kind for kind, _ in issues]


def test_parse_division_string_wiki_examples_are_clean():
    issues, tname = _parse_division_string(
        'name = "Infantry Division" division_template = "Infantry Division" '
        "start_experience_factor = 0.5"
    )
    assert issues == []
    assert tname == "Infantry Division"

    issues, tname = _parse_division_string(
        'name = "Artie" division_template = "Artillery Division" '
        "start_manpower_factor = 0.3"
    )
    assert issues == []
    assert tname == "Artillery Division"

    issues, tname = _parse_division_string(
        'name = "Tank division" division_template = "Tank Division" '
        "start_manpower_factor = 1 force_equipment_variants = { "
        'medium_tank_chassis_2 = { owner = "USA" amount = 100 '
        'version_name = "M4 Sherman" }}'
    )
    assert issues == []
    assert tname == "Tank Division"


def test_parse_division_string_unquoted_owner_in_fev_is_clean():
    issues, tname = _parse_division_string(
        'name = "Al-Saiqa" division_template = "Al-Saiqa" '
        "start_experience_factor = 0.8 start_equipment_factor = 1.0 "
        "force_equipment_variants = { infantry_weapons_1 = { owner = SOV } "
        "cnc_equipment_1 = { owner = SOV } }"
    )
    assert issues == []
    assert tname == "Al-Saiqa"


def test_parse_division_string_rejects_german_danish_letters():
    issues, tname = _parse_division_string(
        'division_template = "militärdistriktet" start_experience_factor = 0.2 '
        "start_equipment_factor = 0.01"
    )
    assert "out-of-bounds-division" in _kinds(issues)
    assert any("out-of-bounds letter in: militärdistriktet" in msg for _, msg in issues)
    assert tname == "militärdistriktet"


def test_parse_division_string_allows_romance_accents():
    issues, tname = _parse_division_string(
        'name = "Québécois Infanterie" division_template = "Brigada de Liberación" '
        "start_experience_factor = 0.5"
    )
    assert issues == []
    assert tname == "Brigada de Liberación"


def test_parse_division_string_rejects_unknown_inner_key():
    issues, tname = _parse_division_string(
        'division_template = "Infantry Division" location = 6040'
    )
    assert "unknown-division-key" in _kinds(issues)
    assert tname == "Infantry Division"


def test_parse_division_string_rejects_unquoted_template():
    issues, tname = _parse_division_string(
        "division_template = Infantry start_experience_factor = 0.5"
    )
    assert "unquoted-value" in _kinds(issues)
    assert tname is None


def test_parse_division_string_rejects_missing_template():
    issues, tname = _parse_division_string('name = "Infantry Division"')
    assert "missing-template" in _kinds(issues)
    assert tname is None


def test_parse_division_string_rejects_non_numeric_factor():
    issues, _tname = _parse_division_string(
        'division_template = "Infantry Division" start_experience_factor = yes'
    )
    assert "malformed-division" in _kinds(issues)
    assert any("must be a number" in msg for _, msg in issues)


def test_parse_division_string_rejects_unknown_fev_key():
    issues, tname = _parse_division_string(
        'division_template = "Tank Division" force_equipment_variants = { '
        'medium_tank_chassis_2 = { owner = "USA" slot = 1 } }'
    )
    assert "unknown-division-key" in _kinds(issues)
    assert tname == "Tank Division"


def test_parse_division_string_rejects_unquoted_version_name():
    issues, _tname = _parse_division_string(
        'division_template = "Tank Division" force_equipment_variants = { '
        "medium_tank_chassis_2 = { owner = USA amount = 100 version_name = Sherman } }"
    )
    assert "unquoted-value" in _kinds(issues)


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
