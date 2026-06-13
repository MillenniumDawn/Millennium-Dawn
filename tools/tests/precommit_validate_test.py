"""Coverage tests for the parallel content-validation dispatcher.

The dispatcher (`tools/precommit_validate.py`) replaces ~20 individual
`md-validate-*` pre-commit hooks. The risk of that consolidation is *coverage*:
if a registry rule drifts from the validator's old `files:` regex, a validator
could silently stop running on some paths. These tests pin which validators a
given staged path selects, so an unintended coverage change fails CI.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from precommit_validate import _REGISTRY  # noqa: E402

_BY_SCRIPT = {spec.script: spec for spec in _REGISTRY}


def _selected(path):
    """Set of validator scripts the dispatcher runs for a single staged path."""
    return {spec.script for spec in _REGISTRY if spec.matches([path])}


# path -> the exact set of commit-stage validators the dispatcher selects.
# Only run-on-commit validators are folded in; the expensive cross-reference
# ones (cosmetic_tags, variables, focus_tree, decisions, modifiers,
# scripted_params, simplifications, localisation, factions, history_techs, ...)
# are stages:[manual] in the config and intentionally absent here.
_GOLDEN = {
    "common/national_focus/france.txt": {"validate_style", "validate_ideas"},
    "events/Syria.txt": {"validate_style", "validate_ideas", "validate_events"},
    "common/decisions/Sudan.txt": {"validate_style", "validate_ideas"},
    "common/scripted_effects/00_x.txt": {"validate_style", "validate_oob_units"},
    "common/units/MD_land_units.txt": {
        "validate_style",
        "validate_oob_units",
        "validate_ai_navy",
    },
    "common/ai_templates/x.txt": {
        "validate_style",
        "validate_oob_units",
        "validate_ai_roles",
    },
    "common/ai_strategy/CAN.txt": {"validate_style", "validate_ai_roles"},
    "common/ai_navy/x.txt": {"validate_style", "validate_ai_navy"},
    "common/ai_equipment/x.txt": {"validate_style", "validate_ai_equipment"},
    "common/intelligence_agency_upgrades/x.txt": {
        "validate_style",
        "validate_agency_upgrades",
    },
    "localisation/english/MD_focus_SER_l_english.yml": {"validate_ideas"},
    # factories/history are manual-only now, so only the catch-all style runs.
    "common/factions/x.txt": {"validate_style"},
    "history/countries/x.txt": {"validate_style"},
}


def test_golden_selection():
    for path, expected in _GOLDEN.items():
        assert _selected(path) == expected, path


def test_style_excludes_changelog_and_authors():
    # Old md-validate-style hook excluded these; the run-gate must match.
    assert "validate_style" not in _selected("Changelog.txt")
    assert "validate_style" not in _selected("AUTHORS.txt")
    assert "validate_style" not in _selected("common/units/descriptions_units.txt")


def test_style_runs_on_normal_txt():
    assert "validate_style" in _selected("common/national_focus/france.txt")


def test_agency_upgrades_exact_file_match():
    spec = _BY_SCRIPT["validate_agency_upgrades"]
    assert spec.matches(["common/on_actions/MD_auto_agency_on_actions.txt"])
    assert spec.matches(["common/intelligence_agency_upgrades/x.txt"])
    # An unrelated on_actions file must NOT trigger it.
    assert not spec.matches(["common/on_actions/00_on_actions.txt"])


def test_ai_equipment_is_warning_only():
    # Mirrors the hook: validate_ai_equipment runs without --strict.
    assert _BY_SCRIPT["validate_ai_equipment"].strict is False


def test_strict_validators_are_strict():
    for script in ("validate_events", "validate_ideas", "validate_oob_units"):
        assert _BY_SCRIPT[script].strict is True


def test_manual_validators_not_folded():
    # These are stages:[manual] in the config and must stay out of the
    # commit-stage dispatcher, or they would run on every commit.
    folded = set(_BY_SCRIPT)
    for script in (
        "validate_cosmetic_tags",
        "validate_localisation",
        "validate_focus_tree",
        "validate_variables",
        "validate_decisions",
        "validate_modifiers",
        "validate_scripted_params",
        "validate_simplifications",
    ):
        assert script not in folded


def test_no_match_outside_scope():
    # A .lua define, a gui file, a texture — none are owned by this dispatcher.
    assert _selected("common/defines/00_defines.lua") == set()
    assert _selected("interface/x.gui") == set()
    assert _selected("gfx/x.dds") == set()
