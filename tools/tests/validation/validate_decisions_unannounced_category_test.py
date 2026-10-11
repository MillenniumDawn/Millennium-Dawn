"""Tests for the unannounced decision category check.

A category gated on state that flips during play appears part-way through a
game. Unless something calls `unlock_decision_category_tooltip` (or
`unlock_decision_tooltip` on one of its decisions), a whole tab of decisions
shows up with no indication of where it came from.
"""

import argparse

import pytest
import validate_decisions as V
from shared.suite import write_text

# Where an announcement can live: one file under each scanned root, with `%s`
# standing in for the effect.
_SOURCES = {
    "focus": (
        "common/national_focus/test.txt",
        "focus = {\n\tid = md_test_focus\n\tcompletion_reward = {\n\t\t%s\n\t}\n}\n",
    ),
    "event": (
        "events/test.txt",
        "country_event = {\n\tid = md_test.1\n\toption = {\n\t\t%s\n\t}\n}\n",
    ),
    "idea": (
        "common/ideas/test.txt",
        "ideas = {\n\tcountry = {\n\t\tmd_test_idea = {\n"
        "\t\t\ton_add = {\n\t\t\t\t%s\n\t\t\t}\n\t\t}\n\t}\n}\n",
    ),
    "decision": (
        "common/decisions/other.txt",
        "md_other_category = {\n\tmd_other_decision = {\n"
        "\t\tcomplete_effect = {\n\t\t\t%s\n\t\t}\n\t}\n}\n",
    ),
    "history": ("history/countries/md_test.txt", "%s\n"),
}


def _write_mod(
    tmp_path,
    category_visible,
    unlock=None,
    category="md_test_category",
    source="focus",
):
    categories = tmp_path / "common" / "decisions" / "categories"
    categories.mkdir(parents=True)
    with (categories / "cat.txt").open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            f"{category} = {{\n\ticon = GFX_decision_generic\n{category_visible}}}\n"
        )
    decisions = tmp_path / "common" / "decisions"
    with (decisions / "dec.txt").open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            f"{category} = {{\n"
            "\tmd_test_decision = {\n"
            "\t\ticon = GFX_decision_generic\n"
            "\t\tcost = 25\n"
            "\t}\n"
            "}\n"
        )
    if unlock:
        path, template = _SOURCES[source]
        write_text(tmp_path / path, template % unlock)
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


_FLAG_GATE = "\tvisible = {\n\t\thas_country_flag = md_test_flag\n\t}\n"


def _findings(validator):
    return validator._unannounced_categories()


def test_cli_exposes_the_flag():
    parser = argparse.ArgumentParser()
    V._add_extra_args(parser)

    assert parser.parse_args(["--unannounced-categories"]).unannounced_categories
    assert not parser.parse_args([]).unannounced_categories


def test_run_validations_skips_the_check_by_default(tmp_path, monkeypatch):
    validator = _write_mod(tmp_path, _FLAG_GATE)
    called = []
    monkeypatch.setattr(
        validator, "validate_unannounced_categories", lambda: called.append(True)
    )

    validator.run_validations()

    assert called == []
    assert validator.unannounced_categories is False


def test_run_validations_runs_the_check_when_enabled(tmp_path, monkeypatch):
    validator = _write_mod(tmp_path, _FLAG_GATE)
    validator.unannounced_categories = True
    called = []
    monkeypatch.setattr(
        validator, "validate_unannounced_categories", lambda: called.append(True)
    )

    validator.run_validations()

    assert called == [True]


def test_flag_gated_category_without_announcement_is_flagged(tmp_path):
    out = _findings(_write_mod(tmp_path, _FLAG_GATE))
    assert len(out) == 1
    assert "md_test_category" in out[0]
    assert "has_country_flag = md_test_flag" in out[0]


def test_category_announced_by_focus_is_not_flagged(tmp_path):
    validator = _write_mod(
        tmp_path,
        _FLAG_GATE,
        unlock="unlock_decision_category_tooltip = md_test_category",
    )
    assert _findings(validator) == []


def test_category_whose_decision_is_announced_is_not_flagged(tmp_path):
    validator = _write_mod(
        tmp_path, _FLAG_GATE, unlock="unlock_decision_tooltip = md_test_decision"
    )
    assert _findings(validator) == []


@pytest.mark.parametrize("source", _SOURCES)
@pytest.mark.parametrize(
    "unlock",
    (
        "unlock_decision_category_tooltip = md_test_category",
        "unlock_decision_tooltip = { decision = md_test_decision }",
    ),
)
def test_announcement_from_any_source_clears_the_finding(tmp_path, source, unlock):
    validator = _write_mod(tmp_path, _FLAG_GATE, unlock=unlock, source=source)
    assert _findings(validator) == []


@pytest.mark.parametrize("source", _SOURCES)
def test_source_without_the_call_is_still_flagged(tmp_path, source):
    validator = _write_mod(
        tmp_path, _FLAG_GATE, unlock="add_political_power = 10", source=source
    )
    assert len(_findings(validator)) == 1


@pytest.mark.parametrize(
    "not_an_announcement",
    (
        "# unlock_decision_category_tooltip = md_test_category",
        'log = "unlock_decision_category_tooltip = md_test_category"',
        "md_unlock_decision_category_tooltip = md_test_category",
        "unlock_decision_category_tooltip = md_other_category",
    ),
)
def test_lookalike_does_not_announce_the_category(tmp_path, not_an_announcement):
    validator = _write_mod(tmp_path, _FLAG_GATE, unlock=not_an_announcement)
    assert len(_findings(validator)) == 1


def test_finding_is_a_warning_with_the_category(tmp_path):
    validator = _write_mod(tmp_path, _FLAG_GATE)

    validator.validate_unannounced_categories()

    assert [(i.severity, i.category) for i in validator._issues] == [
        (V.Severity.WARNING, "unannounced-decision-category")
    ]


def test_category_with_no_visible_block_is_not_flagged(tmp_path):
    assert _findings(_write_mod(tmp_path, "")) == []


def test_tag_gated_category_is_not_flagged(tmp_path):
    # On from the first day for that country, so there is nothing to announce.
    gate = "\tvisible = {\n\t\toriginal_tag = JAP\n\t}\n"
    assert _findings(_write_mod(tmp_path, gate)) == []


def test_ai_only_category_is_not_flagged(tmp_path):
    gate = "\tvisible = {\n\t\tis_ai = yes\n\t\thas_country_flag = md_test_flag\n\t}\n"
    assert _findings(_write_mod(tmp_path, gate)) == []


@pytest.mark.parametrize("country", ("MDT - Test.txt", "OTH - Other.txt"))
@pytest.mark.parametrize(
    ("gate", "history"),
    (
        (_FLAG_GATE, "set_country_flag = md_test_flag"),
        (
            "\tvisible = {\n\t\thas_idea = md_test_idea\n\t}\n",
            "add_ideas = {\n\tmd_other_idea\n\tmd_test_idea\n}",
        ),
        (
            "\tvisible = {\n\t\thas_completed_focus = md_test_focus\n\t}\n",
            "complete_national_focus = md_test_focus",
        ),
        (_FLAG_GATE, 'log = "md_test_flag"'),
    ),
)
def test_history_gate_requires_explicit_exemption(tmp_path, country, gate, history):
    write_text(tmp_path / "history/countries" / country, history + "\n")
    assert len(_findings(_write_mod(tmp_path, gate))) == 1


@pytest.mark.parametrize(
    ("path", "history"),
    (
        ("history/countries/MDT - Test.txt", "# set_country_flag = md_test_flag"),
        ("history/states/1-Test.txt", "set_country_flag = md_test_flag"),
    ),
)
def test_gate_outside_country_history_effects_is_flagged(tmp_path, path, history):
    write_text(tmp_path / path, history + "\n")
    assert len(_findings(_write_mod(tmp_path, _FLAG_GATE))) == 1


def test_history_does_not_skip_the_first_gate(tmp_path):
    write_text(
        tmp_path / "history/countries/MDT - Test.txt", "set_country_flag = md_start\n"
    )
    gate = (
        "\tvisible = {\n\t\thas_country_flag = md_start\n"
        "\t\thas_country_flag = md_test_flag\n\t}\n"
    )
    out = _findings(_write_mod(tmp_path, gate))
    assert len(out) == 1
    assert "becomes visible on has_country_flag = md_start but" in out[0]


def test_config_exempt_category_is_not_flagged(tmp_path):
    # Uses a real config key so a broken load (values instead of ids) fails.
    assert V._UNANNOUNCED_CATEGORY_EXEMPT
    exempt = sorted(V._UNANNOUNCED_CATEGORY_EXEMPT)[0]
    assert _findings(_write_mod(tmp_path, _FLAG_GATE, category=exempt)) == []


def test_unannounced_category_exemptions_have_reasons():
    exemptions = V.validation_config(
        "validate_decisions", "unannounced_category_exempt"
    )
    assert all(reason.strip() for reason in exemptions.values())


@pytest.mark.parametrize(
    ("trigger", "reported"),
    (
        (
            "has_completed_focus = md_other_focus",
            "has_completed_focus = md_other_focus",
        ),
        ("has_global_flag = md_test_flag", "has_global_flag = md_test_flag"),
        ("has_idea = md_test_idea", "has_idea = md_test_idea"),
        ("check_variable = { md_test_var > 0 }", "check_variable"),
    ),
)
def test_other_midgame_gate_is_flagged(tmp_path, trigger, reported):
    gate = f"\tvisible = {{\n\t\t{trigger}\n\t}}\n"
    out = _findings(_write_mod(tmp_path, gate))
    assert len(out) == 1
    assert f"becomes visible on {reported} but" in out[0]
