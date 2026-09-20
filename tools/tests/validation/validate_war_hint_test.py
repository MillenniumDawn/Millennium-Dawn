"""Tests for the decision war-hint check in validate_decisions.py.

A decision whose effect declares war (create_wargoal / declare_war) must carry
a war_with_on_* (fixed target) or war_with_target_on_* (FROM target) hint so the
AI prepares for the war.
"""

import validate_decisions as vd
from validate_decisions import Validator


def _write_decisions(tmp_path, body: str) -> str:
    dec_dir = tmp_path / "common" / "decisions"
    dec_dir.mkdir(parents=True)
    (dec_dir / "test.txt").write_text(body, encoding="utf-8")
    return str(tmp_path)


def _run(tmp_path, body: str):
    """Run validate_missing_war_hint over a single decisions file, return issues."""
    mod_path = _write_decisions(tmp_path, body)
    vd._set_cache_enabled(False)
    try:
        validator = Validator(mod_path=mod_path, use_colors=False)
        validator.validate_missing_war_hint()
        return list(validator._issues)
    finally:
        vd._set_cache_enabled(True)


def test_declares_war_without_hint_flagged(tmp_path):
    body = (
        "category = {\n"
        "\tno_hint_decision = {\n"
        "\t\tcomplete_effect = {\n"
        "\t\t\tcreate_wargoal = { type = annex_everything target = MOR }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    issues = _run(tmp_path, body)
    assert len(issues) == 1
    assert "no_hint_decision" in issues[0].message


def test_war_with_on_complete_clears(tmp_path):
    body = (
        "category = {\n"
        "\tfixed_target_decision = {\n"
        "\t\twar_with_on_complete = MOR\n"
        "\t\tcomplete_effect = {\n"
        "\t\t\tcreate_wargoal = { type = annex_everything target = MOR }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _run(tmp_path, body) == []


def test_war_with_target_on_complete_clears(tmp_path):
    body = (
        "category = {\n"
        "\ttargeted_decision = {\n"
        "\t\twar_with_target_on_complete = yes\n"
        "\t\tcomplete_effect = {\n"
        "\t\t\tcreate_wargoal = { type = annex_everything target = FROM }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _run(tmp_path, body) == []


def test_no_war_no_flag(tmp_path):
    body = (
        "category = {\n"
        "\tpeaceful_decision = {\n"
        "\t\tcomplete_effect = {\n"
        "\t\t\tadd_political_power = 50\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _run(tmp_path, body) == []


def test_ai_strategy_declare_war_value_not_flagged(tmp_path):
    """add_ai_strategy type = declare_war is an AI strategy value, not a war
    declaration effect — it must not trigger the missing-hint warning."""
    body = (
        "category = {\n"
        "\tai_strategy_decision = {\n"
        "\t\tcomplete_effect = {\n"
        "\t\t\tadd_ai_strategy = { type = declare_war id = MOR value = 200 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _run(tmp_path, body) == []
