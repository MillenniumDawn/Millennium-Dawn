"""Tests for validate_agency_upgrades: the intelligence agency upgrade registry,
its loc and GFX, the scripted GUI prerequisites, the completion cache and the
can-select dispatch, and the script calls that name upgrades."""

import pytest
import validate_agency_upgrades as agency
from shared.suite import build_validator, issue_categories
from shared.suite import write_under as _write


def _validator(root, **kwargs):
    return build_validator(agency.Validator, root, **kwargs)


def _messages(validator):
    return [issue.message for issue in validator._issues]


# ---- helpers -----------------------------------------------------------------


def test_read_of_a_missing_file_is_empty(tmp_path):
    assert agency._read(tmp_path / "missing.txt") == ""


def test_line_of_counts_from_one():
    assert agency.line_of("a\nb\n", 2) == 2


@pytest.mark.parametrize(
    "token, expected",
    [
        ("MD_auto_agency_12_upgrade_x", "upgrade_x"),
        ("MD_auto_agency_12_upgrade_x_name", "upgrade_x"),
        ("literal", "literal"),
    ],
)
def test_short_token(token, expected):
    assert agency.Validator._short_token(token) == expected


def test_call_scan_reads_icons_and_upgrades_and_skips_comments():
    text = (
        "# create_intelligence_agency = { icon = GFX_ignored }\n"
        "create_intelligence_agency = {\n"
        "\ticon = GFX_real\n"
        "}\n"
        "create_intelligence_agency = { }\n"
        "upgrade_intelligence_agency = upgrade_real\n"
        "upgrade_intelligence_agency = upgrade_other\n"
    )
    assert agency._scan_agency_calls(agency.strip_comments(text), "events/x.txt") == (
        [("events/x.txt", 2, "GFX_real")],
        [("events/x.txt", 6, "upgrade_real"), ("events/x.txt", 7, "upgrade_other")],
    )


def test_call_worker_on_a_missing_file_finds_nothing(tmp_path):
    assert agency.process_file_for_agency_calls(
        (str(tmp_path / "missing.txt"), str(tmp_path))
    ) == ([], [])


# ---- full runs ---------------------------------------------------------------


def test_full_run_reports_every_integration_group(tmp_path):
    _write(
        tmp_path,
        "common/intelligence_agency_upgrades/upgrades.txt",
        "\tupgrade_good = {\n\t\tlevel = { }\n\t\tlevel = { }\n\t}\n"
        "\tupgrade_no_picture = {\n\t\tlevel = { }\n\t}\n",
    )
    _write(
        tmp_path,
        agency.ON_ACTIONS_FILE,
        "global.agency_upgrades^0 = token:MD_auto_agency_0_upgrade_good\n"
        "global.agency_names^0 = token:MD_auto_agency_0_wrong_name\n"
        "global.agency_gfx^0 = token:MD_auto_agency_0_wrong_gfx\n"
        "global.agency_max_upgrades^0 = 1\n"
        "global.agency_upgrades^1 = token:MD_auto_agency_1_upgrade_unknown\n"
        "global.agency_gfx^1 = token:MD_auto_agency_1_upgrade_unknown_gfx\n"
        "global.agency_names^2 = token:MD_auto_agency_2_upgrade_unknown_name\n"
        "resize_array = { array = global.agency_upgrades value = 0 size = 3 }\n",
    )
    _write(
        tmp_path,
        agency.LOC_FILE,
        'MD_auto_agency_0_upgrade_good: "Good"\n'
        'MD_auto_agency_0_upgrade_good_gfx: "GFX_other"\n',
    )
    _write(tmp_path, "interface/agency.gfx", 'spriteType = { name = "GFX_good" }\n')
    _write(
        tmp_path,
        agency.SCRIPTED_GUI_FILE,
        "scripted_gui = {\n\tcheck = {\n\t\thas_done_agency_upgrade = upgrade_unknown\n"
        "\t}\n}\n",
    )
    _write(
        tmp_path,
        "events/calls.txt",
        "create_intelligence_agency = { icon = GFX_missing }\n"
        "upgrade_intelligence_agency = upgrade_unknown\n",
    )

    validator = _validator(tmp_path)
    validator.run_all_validations()

    assert set(issue_categories(validator)) == {
        "agency-upgrades-registry",
        "agency-upgrades-max-levels",
        "agency-upgrades-loc-gfx",
        "agency-upgrades-array-size",
        "agency-upgrades-prereqs",
        "agency-upgrades-calls",
    }
    messages = " ".join(_messages(validator))
    assert "upgrade_no_picture" in messages
    assert "index ^1 missing" in messages


def _clean_tree(tmp_path):
    _write(
        tmp_path,
        "common/intelligence_agency_upgrades/upgrades.txt",
        "\tupgrade_good = {\n\t\tpicture = GFX_good\n\t\tlevel = { }\n\t}\n",
    )
    _write(
        tmp_path,
        agency.ON_ACTIONS_FILE,
        "global.agency_upgrades^0 = token:MD_auto_agency_0_upgrade_good\n"
        "global.agency_names^0 = token:MD_auto_agency_0_upgrade_good_name\n"
        "global.agency_gfx^0 = token:MD_auto_agency_0_upgrade_good_gfx\n"
        "resize_array = { array = global.agency_upgrades value = 0 size = 1 }\n",
    )
    _write(
        tmp_path,
        agency.LOC_FILE,
        'MD_auto_agency_0_upgrade_good: "Good"\n'
        'MD_auto_agency_0_upgrade_good_name: "Good name"\n'
        'MD_auto_agency_0_upgrade_good_gfx: "GFX_good"\n',
    )
    _write(tmp_path, "interface/agency.gfx", 'spriteType = { name = "GFX_good" }\n')
    _write(tmp_path, agency.SCRIPTED_GUI_FILE, "scripted_gui = { check = { } }\n")


@pytest.mark.parametrize("staged_only", [False, True], ids=["full", "staged"])
def test_a_fully_wired_upgrade_is_clean(tmp_path, monkeypatch, staged_only):
    _clean_tree(tmp_path)
    monkeypatch.setenv(
        "MD_STAGED_FILES", "common/intelligence_agency_upgrades/upgrades.txt"
    )
    validator = _validator(tmp_path, staged_only=staged_only)
    assert validator.run_all_validations() == 0
    assert validator._issues == []


def test_a_missing_scripted_gui_file_has_no_prerequisites(tmp_path):
    validator = _validator(tmp_path / "missing-gui")
    validator._validate_scripted_gui_prereqs()
    assert validator._issues == []


# ---- completion cache --------------------------------------------------------


def _completion_cache(tmp_path, triggers, effects):
    _write(
        tmp_path,
        agency.ON_ACTIONS_FILE,
        "global.agency_upgrades^0 = token:MD_auto_agency_0_upgrade_a\n"
        "global.agency_upgrades^1 = token:MD_auto_agency_1_upgrade_b\n",
    )
    _write(tmp_path, agency.SCRIPTED_TRIGGERS_FILE, triggers)
    _write(tmp_path, agency.SCRIPTED_EFFECTS_FILE, effects)
    validator = _validator(tmp_path)
    validator._collect_registry()
    validator._validate_completion_cache()
    return validator


def _slot_trigger(idx, read_idx=None, max_idx=None):
    read_idx = idx if read_idx is None else read_idx
    max_idx = idx if max_idx is None else max_idx
    return (
        f"MD_auto_agency_slot_available_{idx}_trigger = {{\n"
        f"\tNOT = {{\n"
        f"\t\tcheck_variable = {{\n"
        f"\t\t\tvar = agency_upgrades_completed_and_queued^{read_idx}\n"
        f"\t\t\tvalue = global.agency_max_upgrades^{max_idx}\n"
        f"\t\t\tcompare = greater_than_or_equals\n"
        f"\t\t}}\n"
        f"\t}}\n"
        f"}}\n"
    )


def _seed_branch(idx, upgrade):
    return (
        f"\tif = {{\n"
        f"\t\tlimit = {{ has_done_agency_upgrade = {upgrade} }}\n"
        f"\t\tset_variable = {{ agency_upgrades_completed_and_queued^{idx} = 1 }}\n"
        f"\t}}\n"
    )


def _seed_block(*branches):
    return "MD_auto_agency_seed_completed_cache = {\n" + "".join(branches) + "}\n"


def _can_upgrade_block(indices):
    branches = "".join(
        f"\t\tAND = {{\n"
        f"\t\t\tMD_auto_agency_slot_available_{i}_trigger = yes\n"
        f"\t\t\tMD_auto_agency_can_select_upgrade_{i}_trigger = yes\n"
        f"\t\t}}\n"
        for i in indices
    )
    return f"MD_auto_agency_can_upgrade = {{\n\tOR = {{\n{branches}\t}}\n}}\n"


def test_completion_cache_accepts_a_fully_wired_pair(tmp_path):
    validator = _completion_cache(
        tmp_path,
        _slot_trigger(0) + _slot_trigger(1) + _can_upgrade_block([0, 1]),
        _seed_block(_seed_branch(0, "upgrade_a"), _seed_branch(1, "upgrade_b")),
    )
    assert validator._issues == []


def test_completion_cache_flags_missing_and_mismatched_wiring(tmp_path):
    # Index 1 has no slot trigger, no can_upgrade branch and no seed branch;
    # index 0 reads the wrong array slot and seeds from the wrong upgrade.
    validator = _completion_cache(
        tmp_path,
        _slot_trigger(0, read_idx=1, max_idx=1) + _can_upgrade_block([0]),
        _seed_block(_seed_branch(0, "upgrade_b")),
    )
    messages = _messages(validator)
    assert set(issue_categories(validator)) == {"agency-upgrades-completion-cache"}
    for fragment in (
        "does not read agency_upgrades_completed_and_queued^0",
        "does not compare against global.agency_max_upgrades^0",
        "MD_auto_agency_slot_available_1_trigger definition",
        "MD_auto_agency_slot_available_1_trigger = yes branch",
        "MD_auto_agency_can_select_upgrade_1_trigger = yes branch",
        "seeds index ^0 from 'upgrade_b' but the registry has 'upgrade_a'",
    ):
        assert any(fragment in m for m in messages), fragment
    assert any("never seeds" in m and "^1" in m for m in messages)


def test_completion_cache_flags_orphans_and_a_missing_can_upgrade_block(tmp_path):
    validator = _completion_cache(
        tmp_path,
        _slot_trigger(0) + _slot_trigger(1) + _slot_trigger(9),
        _seed_block(
            _seed_branch(0, "upgrade_a"),
            _seed_branch(1, "upgrade_b"),
            _seed_branch(9, "upgrade_ghost"),
        ),
    )
    messages = _messages(validator)
    for fragment in (
        "MD_auto_agency_can_upgrade block not found",
        "MD_auto_agency_slot_available_9_trigger is defined but index ^9 is not registered",
        "seeds index ^9 but it is not registered",
    ):
        assert any(fragment in m for m in messages), fragment


def test_completion_cache_flags_a_missing_seed_block(tmp_path):
    validator = _completion_cache(
        tmp_path,
        _slot_trigger(0) + _slot_trigger(1) + _can_upgrade_block([0, 1]),
        "MD_auto_agency_other_effect = {\n}\n",
    )
    assert any(
        "MD_auto_agency_seed_completed_cache block not found" in m
        for m in _messages(validator)
    )


def test_completion_cache_without_script_files_reports_nothing(tmp_path):
    validator = _validator(tmp_path / "missing")
    validator._validate_completion_cache()
    assert validator._issues == []


# ---- can-select dispatch -----------------------------------------------------


def _can_select(tmp_path, triggers):
    _write(
        tmp_path,
        agency.ON_ACTIONS_FILE,
        "global.agency_upgrades^0 = token:MD_auto_agency_0_upgrade_a\n"
        "global.agency_upgrades^1 = token:MD_auto_agency_1_upgrade_b\n",
    )
    _write(tmp_path, agency.SCRIPTED_TRIGGERS_FILE, triggers)
    validator = _validator(tmp_path)
    validator._collect_registry()
    validator._validate_can_select_dispatch()
    return validator


def _can_select_trigger(idx):
    return f"MD_auto_agency_can_select_upgrade_{idx}_trigger = {{\n\talways = yes\n}}\n"


def _v_can_select_block(indices):
    branches = "".join(
        f"\t\tMD_auto_agency_can_select_upgrade_{i}_trigger = yes\n" for i in indices
    )
    return f"MD_auto_agency_v_can_select = {{\n\tOR = {{\n{branches}\t}}\n}}\n"


def test_can_select_accepts_a_fully_wired_pair(tmp_path):
    triggers = (
        _can_select_trigger(0) + _can_select_trigger(1) + _v_can_select_block([0, 1])
    )
    assert _can_select(tmp_path, triggers)._issues == []


def test_can_select_flags_missing_and_orphan_wiring(tmp_path):
    # Index 1 has no definition and no dispatch branch; 9 is defined and 7 is
    # dispatched, but neither is registered.
    triggers = (
        _can_select_trigger(0) + _can_select_trigger(9) + _v_can_select_block([0, 7])
    )
    validator = _can_select(tmp_path, triggers)
    messages = _messages(validator)
    assert set(issue_categories(validator)) == {"agency-upgrades-can-select"}
    assert len(messages) == 4
    for fragment in (
        "has no MD_auto_agency_can_select_upgrade_1_trigger definition",
        "has no MD_auto_agency_can_select_upgrade_1_trigger = yes branch",
        "MD_auto_agency_can_select_upgrade_9_trigger is defined but index ^9 is not registered",
        "dispatches index ^7 but it is not registered",
    ):
        assert any(fragment in m for m in messages), fragment


def test_can_select_reports_a_missing_dispatch_block_once(tmp_path):
    validator = _can_select(tmp_path, _can_select_trigger(0) + _can_select_trigger(1))
    messages = _messages(validator)
    assert len(messages) == 1
    assert "MD_auto_agency_v_can_select block not found" in messages[0]
