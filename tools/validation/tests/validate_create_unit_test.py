"""Tests for the create_unit effect structural checks in validate_oob_units.py.

A create_unit only spawns units in a state scope, needs a single-line division
string naming a division_template, and must set owner. When it defines the
template itself, the template must come first.
"""

from validate_oob_units import _check_created_units

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


def _run(content, tmp_path, filename="test.txt"):
    target = tmp_path / "common" / "national_focus" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _check_created_units((str(target), filename, str(tmp_path)))


def _cats(issues):
    return [i.category for i in issues]


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
