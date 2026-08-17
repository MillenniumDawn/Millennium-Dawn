"""Regressions for the two variable-tooltip checks in validate_variables.

`variable-tooltip-missing-loc` flags a `tooltip = KEY` inside a variable effect
whose key has no English loc entry. `dynamic-modifier-tooltip-missing` flags an
`add_to_variable` moving a dynamic modifier's backing variable with no tooltip
at all, but only inside the block kinds the engine renders to the player.
"""

import pytest
import validate_variables as V

DYN_MODS = """\
test_modifier = {
	icon = x
	political_power_factor = tag_pp_var
	stability_factor = tag_dual_var
	war_support_factor = tag_dual_var
	research_speed_factor = var:tag_scoped_var
	monthly_population = global.tag_global_var
	local_building_slots_factor = TAG.tag_array_var^0
	master_build_autonomy_factor = 0.05
	army_speed_factor = tag_unlocalised_var
	custom_modifier_tooltip = tag_custom_tt
	remove_trigger = {
		original_tag = TAG
	}
}
"""

# army_speed_factor_tt is deliberately absent — it drives the "add the key first"
# branch. tag_custom_tt is present to prove custom_modifier_tooltip is still not
# treated as a modifier key.
LOC = """\
l_english:
 political_power_factor_tt: "a"
 stability_factor_tt: "a"
 war_support_factor_tt: "a"
 research_speed_factor_tt: "a"
 monthly_population_tt: "a"
 local_building_slots_factor_tt: "a"
 tag_custom_tt: "a"
"""


def _mod(tmp_path, files, loc=LOC, dyn=DYN_MODS):
    """Build a minimal mod tree and return a Validator pointed at it."""
    dyn_dir = tmp_path / "common" / "dynamic_modifiers"
    dyn_dir.mkdir(parents=True)
    (dyn_dir / "00_test.txt").write_text(dyn, encoding="utf-8")

    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    (loc_dir / "test_l_english.yml").write_text(loc, encoding="utf-8")

    for rel, body in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    return V.Validator(str(tmp_path), use_colors=False, workers=1)


def _missing_tooltips(tmp_path, files, **kwargs):
    validator = _mod(tmp_path, files, **kwargs)
    validator.validate_missing_variable_tooltips()
    return validator._issues


def _bad_keys(tmp_path, files, **kwargs):
    validator = _mod(tmp_path, files, **kwargs)
    validator.validate_variable_tooltip_keys()
    return validator._issues


def _focus(body):
    return "focus = {\n\tid = TAG_test\n\tcompletion_reward = {\n%s\n\t}\n}\n" % body


# --- the dynamic modifier map -------------------------------------------------


def _map(tmp_path, dyn=DYN_MODS):
    return _mod(tmp_path, {}, dyn=dyn)._collect_dynamic_modifier_vars()


def test_map_normalises_every_value_form(tmp_path):
    got = _map(tmp_path)
    assert got["tag_pp_var"] == ("political_power_factor",)
    assert got["tag_scoped_var"] == ("research_speed_factor",)  # var:
    assert got["tag_global_var"] == ("monthly_population",)  # global.
    assert got["tag_array_var"] == ("local_building_slots_factor",)  # TAG.x^0


def test_map_excludes_non_variable_entries(tmp_path):
    got = _map(tmp_path)
    # Literal value, placeholder icon, custom tooltip key, and a remove_trigger
    # body key must never become backing variables.
    assert "0.05" not in got
    assert "x" not in got
    assert "tag_custom_tt" not in got
    assert "TAG" not in got
    assert "original_tag" not in got


def test_map_keeps_every_key_a_variable_backs(tmp_path):
    assert _map(tmp_path)["tag_dual_var"] == ("stability_factor", "war_support_factor")


# --- dynamic-modifier-tooltip-missing ----------------------------------------


def test_untooltipped_write_flagged(tmp_path):
    issues = _missing_tooltips(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { tag_pp_var = 0.05 }"
            )
        },
    )
    assert len(issues) == 1
    assert issues[0].category == "dynamic-modifier-tooltip-missing"
    assert "add tooltip = political_power_factor_tt" in issues[0].message


def test_tooltipped_write_clean(tmp_path):
    assert not _missing_tooltips(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { tag_pp_var = 0.05 tooltip = political_power_factor_tt }"
            )
        },
    )


def test_subtract_from_variable_flagged_and_named(tmp_path):
    issues = _missing_tooltips(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tsubtract_from_variable = { tag_pp_var = 0.05 }"
            )
        },
    )
    assert len(issues) == 1
    assert issues[0].message.startswith("subtract_from_variable = {")


def test_long_form_target_flagged(tmp_path):
    issues = _missing_tooltips(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { var = tag_pp_var value = 0.05 }"
            )
        },
    )
    assert len(issues) == 1


def test_variable_backing_two_modifiers_lists_both(tmp_path):
    issues = _missing_tooltips(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { tag_dual_var = 0.05 }"
            )
        },
    )
    assert (
        "add tooltip = stability_factor_tt or tooltip = war_support_factor_tt"
        in issues[0].message
    )


def test_missing_tt_key_asks_for_the_key_first(tmp_path):
    issues = _missing_tooltips(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { tag_unlocalised_var = 0.05 }"
            )
        },
    )
    assert "`army_speed_factor_tt` does not exist either" in issues[0].message


def test_non_backing_variable_ignored(tmp_path):
    assert not _missing_tooltips(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { TAG_some_counter = 1 }"
            )
        },
    )


# --- scoping to rendered effect blocks ---------------------------------------

_WRITE = "add_to_variable = { tag_pp_var = 0.05 }"


@pytest.mark.parametrize(
    "rel,body",
    [
        (
            "common/national_focus/t.txt",
            "focus = {\n\tcompletion_reward = {\n\t\t%s\n\t}\n}\n" % _WRITE,
        ),
        (
            "common/decisions/t.txt",
            "cat = {\n\td = {\n\t\tcomplete_effect = {\n\t\t\t%s\n\t\t}\n\t}\n}\n"
            % _WRITE,
        ),
        (
            "common/decisions/t.txt",
            "cat = {\n\td = {\n\t\ttimeout_effect = {\n\t\t\t%s\n\t\t}\n\t}\n}\n"
            % _WRITE,
        ),
        (
            "common/decisions/t.txt",
            "cat = {\n\td = {\n\t\tremove_effect = {\n\t\t\t%s\n\t\t}\n\t}\n}\n"
            % _WRITE,
        ),
        (
            "events/t.txt",
            "country_event = {\n\tid = t.1\n\toption = {\n\t\tname = t.1.a\n\t\t%s\n\t}\n}\n"
            % _WRITE,
        ),
        (
            "common/military_industrial_organization/organizations/t.txt",
            "org = {\n\ttrait = {\n\t\ttoken = a\n\t\ton_complete = {\n\t\t\t%s\n\t\t}\n\t}\n}\n"
            % _WRITE,
        ),
    ],
    ids=[
        "completion_reward",
        "complete_effect",
        "timeout_effect",
        "remove_effect",
        "option",
        "on_complete",
    ],
)
def test_every_rendered_block_kind_is_scanned(tmp_path, rel, body):
    assert len(_missing_tooltips(tmp_path, {rel: body})) == 1


def test_joint_focus_needs_no_special_case(tmp_path):
    body = (
        "joint_focus = {\n\tid = TAG_joint\n\tcompletion_reward = {\n\t\t%s\n\t}\n}\n"
        % _WRITE
    )
    assert len(_missing_tooltips(tmp_path, {"common/national_focus/t.txt": body})) == 1


def test_nested_inside_rendered_block_still_flagged(tmp_path):
    body = _focus(
        "\t\tif = {\n\t\t\tlimit = { has_war = no }\n\t\t\t%s\n\t\t}" % _WRITE
    )
    assert len(_missing_tooltips(tmp_path, {"common/national_focus/t.txt": body})) == 1


def test_top_level_write_not_flagged(tmp_path):
    # The history/ bootstrap shape: no enclosing effect block, no tooltip surface.
    assert not _missing_tooltips(
        tmp_path, {"common/national_focus/t.txt": "%s\n" % _WRITE}
    )


def test_cancel_effect_not_flagged(tmp_path):
    body = "cat = {\n\td = {\n\t\tcancel_effect = {\n\t\t\t%s\n\t\t}\n\t}\n}\n" % _WRITE
    assert not _missing_tooltips(tmp_path, {"common/decisions/t.txt": body})


def test_hidden_effect_beats_enclosing_rendered_block(tmp_path):
    body = _focus("\t\thidden_effect = {\n\t\t\t%s\n\t\t}" % _WRITE)
    assert not _missing_tooltips(tmp_path, {"common/national_focus/t.txt": body})


def test_temp_variable_writes_ignored(tmp_path):
    body = _focus(
        "\t\tset_temp_variable = { tag_pp_var = 0.05 }\n"
        "\t\tadd_to_temp_variable = { tag_pp_var = 0.05 }\n"
        "\t\tsubtract_from_temp_variable = { tag_pp_var = 0.05 }"
    )
    assert not _missing_tooltips(tmp_path, {"common/national_focus/t.txt": body})


def test_commented_write_ignored(tmp_path):
    assert not _missing_tooltips(
        tmp_path, {"common/national_focus/t.txt": _focus("\t\t# %s" % _WRITE)}
    )


def test_brace_in_log_string_does_not_desync_spans(tmp_path):
    # Regression: an unbalanced `{` inside a quoted log string used to eat the
    # completion_reward span, silently dropping every write below it.
    body = _focus('\t\tlog = "stray { brace"\n\t\t%s' % _WRITE)
    assert len(_missing_tooltips(tmp_path, {"common/national_focus/t.txt": body})) == 1


# --- variable-tooltip-missing-loc --------------------------------------------


def test_unlocalised_tooltip_key_flagged(tmp_path):
    issues = _bad_keys(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { tag_pp_var = 0.05 tooltip = no_such_key_tt }"
            )
        },
    )
    assert len(issues) == 1
    assert issues[0].category == "variable-tooltip-missing-loc"
    assert "tooltip = no_such_key_tt" in issues[0].message


def test_localised_tooltip_key_clean(tmp_path):
    assert not _bad_keys(
        tmp_path,
        {
            "common/national_focus/t.txt": _focus(
                "\t\tadd_to_variable = { tag_pp_var = 0.05 tooltip = political_power_factor_tt }"
            )
        },
    )


def test_bad_key_checked_on_every_variable_effect(tmp_path):
    body = _focus(
        "\t\tset_variable = { a = 1 tooltip = bad_one_tt }\n"
        "\t\tmultiply_variable = { b = 1 tooltip = bad_two_tt }\n"
        "\t\tclamp_variable = { var = c min = 0 max = 1 tooltip = bad_three_tt }"
    )
    assert len(_bad_keys(tmp_path, {"common/national_focus/t.txt": body})) == 3


def test_bad_key_in_hidden_effect_not_flagged(tmp_path):
    body = _focus(
        "\t\thidden_effect = {\n"
        "\t\t\tadd_to_variable = { tag_pp_var = 0.05 tooltip = no_such_key_tt }\n"
        "\t\t}"
    )
    assert not _bad_keys(tmp_path, {"common/national_focus/t.txt": body})


def test_bad_key_flagged_outside_rendered_blocks(tmp_path):
    # Unlike the missing-tooltip check, a broken key is broken wherever it sits.
    assert (
        len(
            _bad_keys(
                tmp_path,
                {
                    "common/scripted_effects/t.txt": "e = {\n\tadd_to_variable = { tag_pp_var = 1 tooltip = no_such_key_tt }\n}\n"
                },
            )
        )
        == 1
    )


def test_repeated_bad_key_reported_once_per_file(tmp_path):
    body = _focus(
        "\t\tadd_to_variable = { tag_pp_var = 0.05 tooltip = no_such_key_tt }\n"
        "\t\tadd_to_variable = { tag_dual_var = 0.05 tooltip = no_such_key_tt }"
    )
    assert len(_bad_keys(tmp_path, {"common/national_focus/t.txt": body})) == 1


def test_commented_tooltip_ignored(tmp_path):
    body = _focus(
        "\t\t# add_to_variable = { tag_pp_var = 0.05 tooltip = no_such_key_tt }"
    )
    assert not _bad_keys(tmp_path, {"common/national_focus/t.txt": body})
