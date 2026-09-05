"""Edge-case behaviour of the decision checks: skip paths, secondary blocks,
and the repo-scanning helpers."""

import validate_decisions as V
from shared.suite import decisions_results_for


def _block(name, content):
    body = "".join(f"\t\t\t{line}\n" for line in content.strip("\n").split("\n"))
    return f"\t\t{name} = {{\n{body}\t\t}}\n"


def _factory(token, body="", basename="test.txt"):
    return V.DecisionFactory(
        dec=f"\t{token} = {{\n{body}\t}}\n", source_basename=basename
    )


def _tokens(rows):
    return sorted(row.split()[0] for row in rows)


# ---- targeted / FROM performance checks ------------------------------------


def test_targeted_without_targets_skips_disabled_and_map_decisions(monkeypatch):
    factories = [
        _factory(
            "disabled",
            _block("target_root_trigger", "always = yes")
            + _block("allowed", "always = no"),
        ),
        _factory(
            "map_click",
            _block("target_trigger", "always = yes") + "\t\tstate_target = yes\n",
        ),
        _factory("daily_scan", _block("target_root_trigger", "always = yes")),
    ]

    rows = decisions_results_for(
        factories, monkeypatch, "validate_targeted_without_target"
    )

    assert _tokens(rows) == ["daily_scan"]


def test_from_filter_in_available_alone_needs_a_target_trigger(monkeypatch):
    factories = [
        _factory(
            "avail_from",
            "\t\ttargets = { GER }\n" + _block("available", "FROM = { has_war = yes }"),
        ),
        _factory("no_from", "\t\ttargets = { GER }\n"),
    ]

    rows = decisions_results_for(factories, monkeypatch, "validate_targets_no_trigger")

    assert _tokens(rows) == ["avail_from"]


def test_from_without_targets_covers_every_block_and_skips_disabled(monkeypatch):
    factories = [
        _factory(
            "disabled",
            _block("allowed", "always = no")
            + _block("visible", "FROM = { has_war = yes }"),
        ),
        _factory(
            "map_click",
            "\t\tstate_target = yes\n" + _block("visible", "FROM = { has_war = yes }"),
        ),
        _factory("avail_from", _block("available", "FROM = { has_war = yes }")),
        _factory(
            "effect_from", _block("complete_effect", "FROM = { add_stability = 0.1 }")
        ),
    ]

    rows = decisions_results_for(
        factories, monkeypatch, "validate_from_without_targets"
    )

    assert _tokens(rows) == ["avail_from", "effect_from"]
    assert any("FROM used in available" in row for row in rows)
    assert any("FROM used in complete_effect" in row for row in rows)


# ---- tag pin redundancy ----------------------------------------------------


def test_redundant_tag_checks_cover_the_available_block_and_both_pin_forms(
    monkeypatch,
):
    factories = [
        _factory(
            "multi_pin", _block("allowed", "original_tag = GER\noriginal_tag = FRA")
        ),
        _factory("both_pins", _block("allowed", "tag = GER\noriginal_tag = GER")),
        _factory("runtime_pin", _block("allowed", "tag = GER")),
        _factory(
            "avail_recheck",
            _block("allowed", "original_tag = GER") + _block("available", "tag = GER"),
        ),
        _factory(
            "avail_scope",
            _block("allowed", "original_tag = GER")
            + _block("available", "GER = { has_war = no }"),
        ),
    ]

    rows = decisions_results_for(
        factories, monkeypatch, "validate_redundant_tag_checks"
    )

    assert _tokens(rows) == ["avail_recheck", "avail_scope", "both_pins", "runtime_pin"]
    assert any("allowed has both 'tag' and 'original_tag'" in row for row in rows)
    assert any("allowed uses 'tag'" in row for row in rows)
    assert any("available re-checks tag" in row for row in rows)
    assert any("available self-scopes" in row for row in rows)


# ---- cost and localisation -------------------------------------------------


def test_non_numeric_cost_is_treated_as_zero(monkeypatch):
    factories = [
        _factory(
            "scripted_cost",
            "\t\tcost = var:GER_reform_cost\n"
            + _block("complete_effect", "add_political_power = -50"),
        )
    ]

    rows = decisions_results_for(factories, monkeypatch, "validate_pp_charge_in_effect")

    assert _tokens(rows) == ["scripted_cost"]


# ---- state_target ----------------------------------------------------------


def test_state_target_yes_with_targets_is_accepted(monkeypatch):
    factories = [
        _factory("ok", "\t\tstate_target = yes\n\t\ttargets = { GER }\n"),
        _factory("broken", "\t\tstate_target = current_state\n\t\ttargets = { GER }\n"),
    ]

    rows = decisions_results_for(
        factories, monkeypatch, "validate_state_target_with_targets"
    )

    assert _tokens(rows) == ["broken"]


# ---- pure helpers ----------------------------------------------------------


def test_empty_blocks_resolve_to_empty_results(tmp_path):
    assert V._extract_from_blocks("") == []
    assert V._flat_tag_pins("") == set()
    assert V._is_sole_flat_pin("", "GER") is False
    assert V.Validator(str(tmp_path))._normalize_block("") == ""


def test_extract_from_blocks_spans_nested_braces():
    block = "FROM = { OR = { has_war = yes } tag = GER }"

    assert V._extract_from_blocks(block) == [" OR = { has_war = yes } tag = GER "]


def test_flat_tag_pins_reads_a_nested_category_allowed_block():
    categories = {
        "cat": '\tallowed = {\n\t\tNOT = { has_dlc = "x" }\n\t\toriginal_tag = GER\n\t}\n'
    }

    assert V._category_allowed_pins(categories) == {"cat": {("original_tag", "GER")}}


def test_remove_available_block_reports_what_it_cannot_find():
    content = "\tdec = {\n\t\tcost = 10\n\t}\n"

    assert V._remove_available_block_for_token(content, "missing_token") is None
    assert V._remove_available_block_for_token(content, "dec") is None


def test_remove_available_block_handles_nested_braces():
    content = (
        "\tdec = {\n"
        "\t\tavailable = {\n"
        "\t\t\tNOT = { has_war = yes }\n"
        "\t\t}\n"
        "\t\tcost = 10\n"
        "\t}\n"
    )

    patched = V._remove_available_block_for_token(content, "dec")

    assert patched is not None
    assert "available" not in patched
    assert "cost = 10" in patched


def test_unbalanced_decision_block_is_not_patched():
    assert (
        V._remove_available_block_for_token("\tdec = {\n\t\tavailable = {\n", "dec")
        is None
    )


def test_decision_file_fixes_report_what_they_cannot_apply(tmp_path, write_path):
    write_path(tmp_path, "common/decisions/present.txt", "cat = {\n\tdec = { }\n}\n")
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)

    fixed = validator._apply_decision_file_fixes(
        [("absent_token", "absent.txt"), ("dec", "present.txt")],
        lambda content, token: None,
    )

    assert fixed == 0
    assert any("Could not locate file: absent.txt" in m for m in validator.output_lines)
    assert any(
        "Could not patch dec in present.txt" in m for m in validator.output_lines
    )


def test_skipped_files_contribute_no_activations_or_removals(tmp_path, write_path):
    skipped = write_path(
        tmp_path,
        "events/FR_loc_events.txt",
        "remove_decision = some_decision\n",
    )

    assert V._scan_activations_and_removals(str(skipped)) == (
        set(),
        set(),
        set(),
        set(),
    )


def test_unbalanced_dynamic_icon_block_is_skipped(tmp_path, write_path):
    path = write_path(
        tmp_path,
        "common/decisions/broken.txt",
        "cat = {\n\tdec = {\n\t\ticon = {\n\t\t\tkey = GFX_decision_x\n",
    )

    assert V._extract_decision_icons((str(path), str(tmp_path))) == []


def test_scripted_localisation_keys_skip_ignored_files(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_localisation/00_keys.txt",
        "defined_text = {\n\tname = GetDecisionCost\n\ttext = { trigger = { } }\n}\n",
    )
    write_path(
        tmp_path,
        "common/scripted_localisation/FR_loc_keys.txt",
        "defined_text = {\n\tname = GetFrenchCost\n}\n",
    )
    write_path(tmp_path, "common/scripted_localisation/no_defs.txt", "# nothing here\n")

    assert V._load_scripted_localisation_keys(str(tmp_path)) == {"GetDecisionCost"}


def test_formable_without_a_commit_write_is_reported():
    update_flag = _factory(
        "GER_update_flag",
        _block("available", "1 = { }\n2 = { }"),
        basename=V._FORMABLE_DECISIONS_BASENAME,
    )

    rows = V._find_formable_commitment_rows([update_flag], {})

    assert any("GER: no commit write" in row for row in rows)
    assert any("missing commitment gate" in row for row in rows)


def test_icon_checks_skip_themselves_without_a_sprite_index(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "build_sprite_index", lambda *a, **k: {"GFX_one": "x"})
    monkeypatch.setattr(V, "build_sprite_texture_index", lambda *a, **k: {})
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)

    validator.validate_missing_icons()
    validator.validate_icon_types()

    assert validator._issues == []
    assert sum("did not load" in line for line in validator.output_lines) == 2


def test_icon_type_message_accepts_art_sized_for_its_slot(tmp_path):
    from PIL import Image

    texture = tmp_path / "icon.dds"
    Image.new("RGB", (32, 31)).save(str(texture), format="DDS")
    textures = {"GFX_decision_x": str(texture)}

    assert V._icon_type_message("decision", "dec", "GFX_decision_x", textures) is None
    assert "category icon" in V._icon_type_message(
        "category_icon", "cat", "GFX_decision_x", textures
    )


def test_icon_type_message_skips_a_texture_it_cannot_measure(tmp_path):
    textures = {"GFX_decision_x": str(tmp_path / "gone.dds")}

    assert V._icon_type_message("decision", "dec", "GFX_decision_x", textures) is None


# ---- full-repo run ---------------------------------------------------------

_MISSION_ONLY = (
    "\tmission_remove = {\n"
    "\t\tdays_mission_timeout = 30\n"
    "\t\tremove_effect = { add_stability = 0.1 }\n"
    "\t}\n"
)

_DECISIONS = (
    "cat_bop_only = {\n"
    "\tbop_decision = {\n"
    "\t\ticon = good\n"
    '\t\tcustom_cost_text = "[GetUnknownCost]"\n'
    "\t\tcomplete_effect = {\n"
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision bop_decision"\n'
    "\t\t}\n"
    "\t}\n"
    "}\n"
    "cat_main = {\n"
    "\twrong_icon = {\n"
    "\t\ticon = wrong\n"
    "\t\tcomplete_effect = {\n"
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision wrong_icon"\n'
    "\t\t}\n"
    "\t}\n"
    "\tpartial_allowed = {\n"
    "\t\tallowed = {\n"
    "\t\t\toriginal_tag = GER\n"
    "\t\t\thas_war = no\n"
    "\t\t}\n"
    "\t\tcomplete_effect = {\n"
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision partial_allowed"\n'
    "\t\t}\n"
    "\t}\n"
    "\tdisabled_remove = {\n"
    "\t\tallowed = { always = no }\n"
    "\t\tremove_effect = { add_stability = 0.1 }\n"
    "\t}\n"
    "\tremoved_elsewhere = {\n"
    "\t\tremove_effect = { add_stability = 0.1 }\n"
    "\t}\n" + _MISSION_ONLY + "}\n"
)

_CATEGORIES = (
    "cat_empty = {\n\ticon = GFX_decision_category_generic_operation\n}\n"
    "cat_bop_only = {\n\ticon = GFX_decision_category_generic_operation\n}\n"
    "cat_main = {\n"
    "\ticon = GFX_decision_category_generic_operation\n"
    "\tvisible = { has_country_flag = midgame_flag }\n"
    "}\n"
)


def _filler_gfx(count):
    entries = "".join(
        f'\tspriteType = {{\n\t\tname = "GFX_filler_{i}"\n'
        f'\t\ttexturefile = "gfx/interface/filler.dds"\n\t}}\n'
        for i in range(count)
    )
    return (
        "spriteTypes = {\n"
        + entries
        + '\tspriteType = {\n\t\tname = "GFX_decision_good"\n'
        '\t\ttexturefile = "gfx/interface/filler.dds"\n\t}\n'
        '\tspriteType = {\n\t\tname = "GFX_decision_wrong"\n'
        '\t\ttexturefile = "gfx/interface/banner.dds"\n\t}\n'
        "}\n"
    )


def _decision_repo(tmp_path, write_path, *, with_bop=True):
    from PIL import Image

    write_path(tmp_path, "common/decisions/decisions.txt", _DECISIONS)
    write_path(tmp_path, "common/decisions/FR_loc_decisions.txt", "cat_fr = { }\n")
    write_path(tmp_path, "common/decisions/categories/categories.txt", _CATEGORIES)
    write_path(tmp_path, "interface/filler.gfx", _filler_gfx(1000))
    banner = tmp_path / "gfx" / "interface" / "banner.dds"
    banner.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (114, 101)).save(str(banner), format="DDS")
    if with_bop:
        write_path(tmp_path, "common/bop/bop.txt", "decision_category = cat_empty\n")
    write_path(
        tmp_path,
        "common/national_focus/germany.txt",
        "GER_unify = {\n\tcompletion_reward = {\n"
        "\t\tset_variable = { formable_committed_id = 1 }\n\t}\n}\n",
    )
    write_path(
        tmp_path,
        "events/removals.txt",
        "remove_decision = removed_elsewhere\n",
    )
    write_path(
        tmp_path,
        "localisation/english/decisions_l_english.yml",
        'l_english:\n bop_decision:0 "BOP"\n wrong_icon:0 "Wrong"\n'
        ' disabled_remove:0 "Disabled"\n removed_elsewhere:0 "Removed"\n'
        ' mission_remove:0 "Mission"\n cat_bop_only:0 "BOP category"\n'
        ' cat_main:0 "Main"\n cat_empty:0 "Empty"\n',
    )


def _run(tmp_path, **kwargs):
    validator = V.Validator(
        str(tmp_path), use_colors=False, workers=1, no_cache=True, **kwargs
    )
    validator.run_validations()
    return validator


def test_full_run_with_both_opt_in_checks(tmp_path, write_path):
    _decision_repo(tmp_path, write_path)

    validator = _run(tmp_path, missing_icons=True, unannounced_categories=True)
    categories = {issue.category for issue in validator._issues}

    assert "decision-icon-slot-mismatch" in categories
    assert "unannounced-decision-category" in categories
    assert any("cat_main" in i.message for i in validator._issues)
    assert any(
        "GetUnknownCost" in i.message
        for i in validator._issues
        if i.category == "missing-decision-localisation"
    )
    # `icon = good` and `icon = wrong` both resolve, so neither is missing.
    assert not any(
        "wrong_icon" in i.message or "bop_decision" in i.message
        for i in validator._issues
        if i.category == "missing-decision-icon"
    )


def test_orphaned_remove_effect_skips_every_exempt_shape(tmp_path, write_path):
    _decision_repo(tmp_path, write_path)
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)

    validator.validate_orphaned_remove_effect()

    assert validator._issues == []


def test_missing_bop_directory_is_reported(tmp_path, write_path):
    _decision_repo(tmp_path, write_path, with_bop=False)
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)

    validator.validate_unused_categories()

    assert any("No BOP files found" in line for line in validator.output_lines)
