"""Tests for validate_dynamic_modifier_guards.

`remove_dynamic_modifier` against a scope that is not carrying the modifier
logs an error and does nothing (issue #3764). The guard must name the *same*
modifier as the removal: an `if`/`limit` gating on a flag or an idea reads like
a guard and proves nothing.
"""

import re

import validate_dynamic_modifier_guards as V

REMOVE = "remove_dynamic_modifier = {{ modifier = {name} }}"
GUARDED = (
    "if = {{ limit = {{ has_dynamic_modifier = {{ modifier = {name} }} }} "
    + REMOVE
    + " }}"
)


def _findings(script):
    return V.scan_text(script)


def _modifiers(script):
    """The modifier name each finding names, in report order."""
    return [
        re.search(r"modifier = (\w+) \}", message).group(1)
        for _, message in _findings(script)
    ]


# --- unguarded removals ---------------------------------------------------


def test_bare_removal_is_flagged():
    findings = _findings(REMOVE.format(name="ITA_mafia_modifier") + "\n")
    assert len(findings) == 1
    assert findings[0][0] == 1
    assert "ITA_mafia_modifier" in findings[0][1]


def test_removal_inside_a_state_scope_is_flagged():
    script = "1052 = { " + REMOVE.format(name="BOS_landmine_contamination") + " }\n"
    assert _modifiers(script) == ["BOS_landmine_contamination"]


def test_every_unguarded_sibling_is_reported_separately():
    script = (
        "hidden_effect = {\n"
        "\t935 = { " + REMOVE.format(name="pkk_static_modifier") + " }\n"
        "\t162 = { " + REMOVE.format(name="kurdish_resistance") + " }\n"
        "}\n"
    )
    assert _modifiers(script) == ["pkk_static_modifier", "kurdish_resistance"]


def test_effect_tooltip_preview_is_ignored():
    script = "effect_tooltip = { " + REMOVE.format(name="GRE_debt_modifier") + " }\n"
    assert _findings(script) == []


# --- accepted guard idioms -------------------------------------------------


def test_single_line_house_style_guard_is_clean():
    """common/scripted_effects/99_FRA_scripted_effects.txt's form."""
    assert _findings(GUARDED.format(name="FRA_ps_econ_policy") + "\n") == []


def test_multi_line_guard_is_clean():
    script = (
        "if = {\n"
        "\tlimit = { has_dynamic_modifier = { modifier = ALG_constitution_1996 } }\n"
        "\t" + REMOVE.format(name="ALG_constitution_1996") + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_cross_scope_guard_is_clean():
    """common/national_focus/05_egypt.txt: the limit re-enters state 215."""
    script = (
        "if = {\n"
        "\tlimit = { 215 = { has_dynamic_modifier = { modifier = EGY_slums_5_level } } }\n"
        "\t215 = { " + REMOVE.format(name="EGY_slums_5_level") + " }\n"
        "}\n"
    )
    assert _findings(script) == []


def test_guard_nested_in_an_or_is_clean():
    script = (
        "if = {\n"
        "\tlimit = {\n"
        "\t\tOR = {\n"
        "\t\t\thas_dynamic_modifier = { modifier = PER_kurd_separatism }\n"
        "\t\t\thas_country_flag = PER_purge_done\n"
        "\t\t}\n"
        "\t}\n"
        "\t" + REMOVE.format(name="PER_kurd_separatism") + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_scoped_presence_trigger_counts_as_a_guard():
    """common/decisions/Syria.txt passes `scope =` to has_dynamic_modifier."""
    script = (
        "if = {\n"
        "\tlimit = { has_dynamic_modifier = { modifier = kurdish_inclusiveness scope = SYR } }\n"
        "\t" + REMOVE.format(name="kurdish_inclusiveness") + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_guard_carries_into_nested_scopes():
    script = (
        "if = {\n"
        "\tlimit = { has_dynamic_modifier = { modifier = TUR_pkk_presence } }\n"
        "\thidden_effect = { 935 = { "
        + REMOVE.format(name="TUR_pkk_presence")
        + " } }\n"
        "}\n"
    )
    assert _findings(script) == []


# --- the guard must name the same modifier ---------------------------------


def test_limit_on_a_country_flag_still_flags():
    script = (
        "if = {\n"
        "\tlimit = { has_country_flag = CHI_hkg_integrated }\n"
        "\t" + REMOVE.format(name="CHI_HKG_sinicization_modifier") + "\n"
        "}\n"
    )
    assert _modifiers(script) == ["CHI_HKG_sinicization_modifier"]


def test_limit_naming_a_different_modifier_still_flags():
    script = (
        "if = {\n"
        "\tlimit = { has_dynamic_modifier = { modifier = ITA_party_propaganda_modifier } }\n"
        "\t" + REMOVE.format(name="ITA_party_popularity_drift_modifier") + "\n"
        "}\n"
    )
    assert _modifiers(script) == ["ITA_party_popularity_drift_modifier"]


def test_else_branch_does_not_inherit_the_guard():
    script = (
        "if = {\n"
        "\tlimit = { has_dynamic_modifier = { modifier = EGY_slums_5_level } }\n"
        "\t" + REMOVE.format(name="EGY_slums_5_level") + "\n"
        "}\n"
        "else = {\n"
        "\t" + REMOVE.format(name="EGY_slums_5_level") + "\n"
        "}\n"
    )
    assert _modifiers(script) == ["EGY_slums_5_level"]


def test_decision_available_is_not_a_guard():
    script = (
        "ARM_remove_fsb_borderguards = {\n"
        "\tavailable = { has_dynamic_modifier = { modifier = ARM_fsb_borderguards } }\n"
        "\tremove_effect = { " + REMOVE.format(name="ARM_fsb_borderguards") + " }\n"
        "}\n"
    )
    assert _modifiers(script) == ["ARM_fsb_borderguards"]


def test_event_trigger_is_not_a_guard():
    script = (
        "country_event = {\n"
        "\ttrigger = { has_dynamic_modifier = { modifier = ITA_mafia_modifier } }\n"
        "\toption = { " + REMOVE.format(name="ITA_mafia_modifier") + " }\n"
        "}\n"
    )
    assert _modifiers(script) == ["ITA_mafia_modifier"]


def test_removal_without_a_modifier_field_is_ignored():
    assert _findings("remove_dynamic_modifier = { }\n") == []


# --- scan_file --------------------------------------------------------------


def test_scan_file_relativizes_the_path_and_reports_the_line(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    target = tmp_path / "common" / "decisions"
    target.mkdir(parents=True)
    path = target / "Iran.txt"
    path.write_text(
        "PER_purge = {\n\tcomplete_effect = {\n\t\t"
        + REMOVE.format(name="PER_pan_iranist_attack")
        + "\n\t}\n}\n",
        encoding="utf-8",
    )
    findings = V.scan_file((str(path), str(tmp_path) + "/"))
    assert findings == [
        (
            "common/decisions/Iran.txt",
            3,
            "remove_dynamic_modifier = { modifier = PER_pan_iranist_attack } is not "
            "guarded by a check that PER_pan_iranist_attack is applied",
        )
    ]


def test_scan_file_skips_files_without_the_effect(tmp_path):
    path = tmp_path / "quiet.txt"
    path.write_text("add_dynamic_modifier = { modifier = X }\n", encoding="utf-8")
    assert V.scan_file((str(path), str(tmp_path) + "/")) == []


def test_scan_file_survives_an_unreadable_path(tmp_path):
    (tmp_path / "remove_dynamic_modifier.txt").mkdir()
    args = (str(tmp_path / "remove_dynamic_modifier.txt"), str(tmp_path))
    assert V.scan_file(args) == []


# --- validator wiring -------------------------------------------------------


def _validate(tmp_path, write_path, monkeypatch, script):
    import validator_common

    monkeypatch.setattr(validator_common, "_LOG_LEVEL", "INFO")
    write_path(tmp_path, "common/decisions/Italy.txt", script)
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)
    validator.run_validations()
    return validator


def test_run_raises_an_error_per_unguarded_removal(tmp_path, write_path, monkeypatch):
    validator = _validate(
        tmp_path,
        write_path,
        monkeypatch,
        REMOVE.format(name="ITA_mafia_modifier") + "\n",
    )

    assert [(issue.severity, issue.category) for issue in validator._issues] == [
        ("error", "unguarded-remove-dynamic-modifier")
    ]
    assert validator._issues[0].file == "common/decisions/Italy.txt"
    assert any(
        line.startswith("  common/decisions/Italy.txt:1 - ")
        for line in validator.output_lines
    )
    assert any(
        "1 unguarded dynamic modifier removal(s)" in line
        for line in validator.output_lines
    )


def test_run_stays_quiet_when_every_removal_is_guarded(
    tmp_path, write_path, monkeypatch
):
    validator = _validate(
        tmp_path,
        write_path,
        monkeypatch,
        GUARDED.format(name="ITA_mafia_modifier") + "\n",
    )

    assert validator._issues == []
    assert any("All remove_dynamic_modifier" in line for line in validator.output_lines)
