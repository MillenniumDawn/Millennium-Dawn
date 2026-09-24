"""Tests for the decision war-hint check in validate_decisions.py.

A decision whose effect declares war (create_wargoal / declare_war) must carry
a war_with_on_* (fixed target) or war_with_target_on_* (FROM target) hint so the
AI prepares for the war.
"""

import pytest
import validate_decisions as vd
from validate_decisions import Validator


def _write_decisions(tmp_path, body: str) -> str:
    dec_dir = tmp_path / "common" / "decisions"
    dec_dir.mkdir(parents=True, exist_ok=True)
    (dec_dir / "test.txt").write_text(body, encoding="utf-8")
    return str(tmp_path)


def _run(tmp_path, body: str, *, check="validate_missing_war_hint"):
    """Run one decision check over a single decisions file, return issues."""
    mod_path = _write_decisions(tmp_path, body)
    vd._invalidate_decision_cache()
    vd._set_cache_enabled(False)
    try:
        validator = Validator(mod_path=mod_path, use_colors=False)
        getattr(validator, check)()
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


def test_country_flag_in_decision_allowed_but_not_category(tmp_path):
    categories = tmp_path / "common" / "decisions" / "categories"
    categories.mkdir(parents=True)
    (categories / "test.txt").write_text(
        "category = {\n\tallowed = { has_country_flag = category_flag }\n}\n",
        encoding="utf-8",
    )
    body = (
        "category = {\n"
        "\tbad = {\n\t\tallowed = { NOT = { has_country_flag = gate } }\n\t}\n"
        "\tgood = {\n\t\tvisible = { has_country_flag = visible_flag }\n\t}\n"
        "}\n"
    )
    issues = _run(tmp_path, body, check="validate_allowed_country_flag")
    assert len(issues) == 1
    assert "bad" in issues[0].message
    assert issues[0].category == "unsupported-decision-allowed-flag"


@pytest.mark.parametrize(
    "effect,hint,expected",
    [
        ("remove", "", True),
        ("remove", "war_with_on_remove = IRQ", False),
        ("remove", "war_with_on_complete = IRQ", True),
        ("complete", "war_with_on_complete = IRQ", False),
        ("timeout", "war_with_on_timeout = IRQ", False),
    ],
)
def test_event_chain_war_hint_matches_effect_and_target(
    tmp_path, effect, hint, expected
):
    categories = tmp_path / "common" / "decisions" / "categories"
    categories.mkdir(parents=True)
    (categories / "test.txt").write_text(
        "war_on_terror = {\n\tallowed = { original_tag = USA }\n}\n",
        encoding="utf-8",
    )
    events = tmp_path / "events"
    events.mkdir()
    (events / "war.txt").write_text(
        "country_event = {\n\tid = war.1\n\toption = { country_event = war.2 }\n}\n"
        "country_event = {\n\tid = war.2\n\toption = { "
        "create_wargoal = { target = IRQ type = annex_everything } }\n}\n",
        encoding="utf-8",
    )
    body = (
        "war_on_terror = {\n"
        "\tusa_operation = {\n"
        f"\t\t{hint}\n"
        f"\t\t{effect}_effect = {{ USA = {{ country_event = war.1 }} }}\n"
        "\t}\n}\n"
    )
    issues = _run(tmp_path, body)
    assert bool(issues) is expected
    if expected:
        assert "war.1 -> war.2" in issues[0].message


@pytest.mark.parametrize("effect", ["complete", "remove", "timeout"])
def test_targeted_decision_war_hints(tmp_path, effect):
    body = (
        "category = {\n\ttargeted = {\n"
        "\t\ttargets = { IRQ }\n"
        f"\t\t{effect}_effect = {{ declare_war_on = {{ target = FROM }} }}\n"
        "\t}\n}\n"
    )
    assert len(_run(tmp_path, body)) == 1
    wrong_hint = f"war_with_on_{effect} = FROM"
    assert (
        len(
            _run(
                tmp_path, body.replace("\t\ttargets", f"\t\t{wrong_hint}\n\t\ttargets")
            )
        )
        == 1
    )
    hint = f"war_with_target_on_{effect} = yes"
    assert _run(tmp_path, body.replace("\t\ttargets", f"\t\t{hint}\n\t\ttargets")) == []


def test_quoted_war_effect_and_hint_do_not_count(tmp_path):
    body = (
        "category = {\n\tdecision = {\n"
        '\t\tcomplete_effect = { log = "create_wargoal = { target = IRQ }" }\n'
        "\t}\n}\n"
    )
    assert _run(tmp_path, body) == []
    body = (
        "category = {\n\tdecision = {\n"
        '\t\tlog = "war_with_on_complete = IRQ"\n'
        "\t\tcomplete_effect = { create_wargoal = { target = IRQ } }\n"
        "\t}\n}\n"
    )
    assert len(_run(tmp_path, body)) == 1


def test_war_in_foreign_event_scope_does_not_require_hint(tmp_path):
    events = tmp_path / "events"
    events.mkdir()
    (events / "war.txt").write_text(
        "country_event = {\n\tid = proxy.1\n"
        "\toption = { MOR = { declare_war_on = { target = IRQ } } }\n}\n",
        encoding="utf-8",
    )
    body = (
        "category = {\n\tdecision = {\n"
        "\t\tremove_effect = { country_event = proxy.1 }\n"
        "\t}\n}\n"
    )
    assert _run(tmp_path, body) == []
