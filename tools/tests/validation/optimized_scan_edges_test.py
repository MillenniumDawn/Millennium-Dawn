"""Malformed inputs and empty-file paths of the shared validator scans."""

import check_common_mistakes as mistakes
import pytest
import validate_events as events
import validate_focus_tree as focus
import validate_localisation as loc
import validate_mios as mios
import validate_oob_units as oob
import validate_variables as variables
from shared.suite import yml_scan


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ""),
        ("ROOT.GetName", ""),
        ("FROM.CONTROLLER:some_value", "some_value"),
        ("123:some_value", "123:some_value"),
        ("FROM.123:some_value", "123:some_value"),
    ],
)
def test_localisation_variable_names_keep_scope_and_promote_rules(raw, expected):
    assert loc._loc_var_name(raw) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", set()),
        ("for_each_loop = { value = loop_value", set()),
        ("dynamic_lists = { entry = { value = list_value }", set()),
        (
            "dynamic_lists = { metadata = yes entry = { value = list_value } }",
            {"list_value"},
        ),
        ("set_variable = { var = some_value", {"some_value"}),
    ],
)
def test_localisation_variable_writes_keep_malformed_block_behavior(
    tmp_path, write_path, text, expected
):
    path = write_path(tmp_path, "common/scripted_effects/edge.txt", text)
    assert loc.process_txt_for_var_writes((str(path),)) == expected


@pytest.mark.parametrize(
    "text",
    [
        "has_variable = token:some_value",
        "has_variable = some_value@ROOT",
        "has_variable = ROOT",
        "check_variable = { some_value > 0",
        "check_variable = { var = token:some_value value > 0 }",
    ],
)
def test_localisation_script_reads_exclude_tokens_scopes_and_unclosed_blocks(text):
    assert loc._scan_script_var_reads_text(text, "edge.txt") == []


def test_trigger_tooltip_without_a_tooltip_key_is_empty():
    assert loc._trigger_tooltip_keys("custom_trigger_tooltip = { always = yes }") == []


def test_shared_localisation_worker_skips_both_unselected_scan_groups(tmp_path):
    assert loc._scan_shared_txt_file(
        (str(tmp_path / "missing.txt"), str(tmp_path), False, False)
    ) == ([], (set(), [], set()), set(), [], [])


def test_localisation_variable_reference_scan_keeps_exact_lines(tmp_path, write_path):
    path = write_path(
        tmp_path, "edge.yml", 'l_english:\n KEY:0 "[?some_value] [?ROOT.GetName]"\n'
    )
    assert yml_scan(path, "var_refs") == [("some_value", "edge.yml", 2)]


@pytest.mark.parametrize(
    "relative", ["tools/edge.txt", "events/missing.txt", "events/edge.txt"]
)
def test_shared_variable_worker_handles_skipped_missing_and_unselected_files(
    tmp_path, write_path, relative
):
    if "missing" not in relative:
        write_path(tmp_path, relative, "some_value = yes\n")
    args = (
        str(tmp_path / relative),
        str(tmp_path),
        0,
        frozenset(),
        frozenset(),
        {},
        {},
        frozenset(),
    )
    assert variables._scan_shared_file(args) == variables._EMPTY_SHARED_RESULT


def test_clamp_resolution_skips_duplicate_and_non_numeric_comparisons():
    checks = [
        ("some_value", "20", 1, 10),
        ("some_value", "20", 2, 10),
        ("some_value", "other_value", 3, 30),
    ]
    assert variables._resolve_clamp_checks(
        checks, "edge.txt", {"some_value": (0, 10)}
    ) == [
        "edge.txt:1 - some_value is clamped to 0..10 but compared against 20"
        " — the check can never change outcome"
    ]


@pytest.mark.parametrize("relative", ["tools/edge.txt", "events/missing.txt"])
def test_event_option_log_worker_handles_skipped_and_missing_files(tmp_path, relative):
    assert (
        events._extract_option_logs_without_effects(
            str(tmp_path / relative), mod_path=str(tmp_path)
        )
        == []
    )


def test_event_option_log_worker_reports_effect_free_options(tmp_path, write_path):
    path = write_path(
        tmp_path,
        "events/edge.txt",
        'country_event = { option = { name = tst.1.a log = "tst.1.a" } }',
    )
    assert events._extract_option_logs_without_effects(
        str(path), mod_path=str(tmp_path)
    ) == [("tst.1.a", str(path), 1)]


def test_shared_event_worker_handles_a_missing_file(tmp_path):
    args = (
        str(tmp_path / "events/missing.txt"),
        str(tmp_path),
        events._C_TYPED,
        {},
        frozenset(),
        frozenset(),
    )
    assert (
        events._scan_shared_call_site_file(args)
        == events._EMPTY_SHARED_CALL_SITE_RESULT
    )


def test_relative_position_scan_ignores_focus_blocks_without_an_id(
    tmp_path, write_path
):
    path = write_path(
        tmp_path, "common/national_focus/edge.txt", "focus = { cost = 1 }"
    )
    source = focus._FocusFile(str(path), str(tmp_path))
    assert focus._scan_relative_positions(source) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('inner = { owner = GER } owner = "TST"', "TST"),
        ('owner = "unterminated', None),
        ("owner = ", None),
        ("owner = { }", None),
        ('log = "escaped \\" brace { }" owner = TST', "TST"),
    ],
)
def test_oob_owner_value_respects_top_level_and_quoted_boundaries(text, expected):
    assert oob._top_level_value(text, 0, len(text), "owner") == expected


@pytest.mark.parametrize(
    "selector",
    [
        "",
        "country = { tag = TST } country = { tag = GER }",
        "country = { tag = ROOT }",
        "country = { tag = TST tag = GER }",
    ],
)
def test_oob_focus_owner_rejects_ambiguous_or_dynamic_selectors(selector):
    text = f"focus_tree = {{ {selector} focus = {{ id = TST_focus }} }}"
    nodes = oob._build_block_nodes(text)
    child = next(index for index, node in enumerate(nodes) if node["label"] == "focus")
    assert oob._focus_root_owner(nodes, text, child) is None


def test_mio_policy_scan_runs_icon_and_modifier_checks(tmp_path, write_path):
    write_path(
        tmp_path,
        f"{mios.POLICY_DIR}/edge.txt",
        "organization_modifier = { military_industrial_organization_research_bonus = invalid }\n"
        "icon = not_a_sprite\n",
    )
    validator = mios.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("mio-icon-not-gfx", f"{mios.POLICY_DIR}/edge.txt", 2)]


def test_mio_run_handles_files_removed_after_collection(tmp_path, monkeypatch):
    validator = mios.Validator(str(tmp_path), use_colors=False, workers=1)
    missing = str(tmp_path / "missing.txt")
    for method in ("_org_files", "_bonus_files", "_doctrine_files", "_reference_files"):
        monkeypatch.setattr(validator, method, lambda: [missing])
    monkeypatch.setattr(validator, "_org_universe", dict)
    validator.run_validations()
    assert validator._issues == []


def test_mio_tag_and_geometry_indexes_handle_missing_entries(tmp_path, monkeypatch):
    validator = mios.Validator(str(tmp_path), use_colors=False, workers=1)
    monkeypatch.setattr(validator, "_trait_index", dict)
    validator._check_trait_geometry(
        "TST_org", "trait = { }\ntrait = {\n token = missing\n}", "edge.txt", 0
    )
    assert validator._allowed_tags("trait = { }") == frozenset()
    monkeypatch.setattr(
        validator,
        "_collect_files",
        lambda *args, **kwargs: [str(tmp_path / "missing.txt")],
    )
    assert validator._scripted_trigger_tags() == {}
    assert validator._issues == []


def test_mio_geometry_reports_symmetric_mutex_pairs_once(tmp_path, monkeypatch):
    body = (
        "trait = {\n token = BBB\n position = { x = 0 y = 1 }\n"
        " mutually_exclusive = { AAA NO_POS }\n}\n"
        "trait = {\n token = AAA\n position = { x = 0 y = 2 }\n"
        " mutually_exclusive = { BBB }\n}\n"
        "trait = {\n token = NO_POS\n mutually_exclusive = { BBB }\n}\n"
        "trait = {\n token = CHILD\n position = { x = 0 y = 3 }\n"
        " parent = { AAA BBB }\n}\n"
    )
    index = mios._parse_org_traits(body)
    validator = mios.Validator(str(tmp_path), use_colors=False, workers=1)
    monkeypatch.setattr(validator, "_trait_index", lambda: index)
    validator._check_trait_geometry("TST_org", body, "edge.txt", 0)
    assert [
        (issue.category, issue.file, issue.line, issue.message)
        for issue in validator._issues
    ] == [
        (
            "trait-geometry-mutex-row",
            "edge.txt",
            1,
            "mutually exclusive traits `BBB` and `AAA` sit on different rows"
            " (1 vs 2); exclusive traits share a row",
        ),
        (
            "trait-geometry-mutex-parents",
            "edge.txt",
            15,
            "trait `CHILD` requires both `AAA` and `BBB`, but they are mutually"
            " exclusive — the trait is locked out; use any_parent",
        ),
    ]


def test_mio_scripted_trigger_index_ignores_blocks_without_tag_selectors(
    tmp_path, write_path
):
    write_path(
        tmp_path,
        f"{mios.SCRIPTED_TRIGGER_DIR}/edge.txt",
        "any_tag = {\n always = yes\n}\nTST_only = {\n original_tag = TST\n}\n",
    )
    validator = mios.Validator(str(tmp_path), use_colors=False, workers=1)
    tags = validator._scripted_trigger_tags()
    assert tags == {"TST_only": frozenset({"TST"})}
    assert validator._scripted_trigger_tags() is tags


def test_mio_nested_bonus_with_unknown_equipment_does_not_invent_dead_stats(tmp_path):
    validator = mios.Validator(str(tmp_path), use_colors=False, workers=1)
    equipment = mios.build_equipment_stat_index(str(tmp_path))
    validator._check_nested_equipment_bonus(
        "equipment_bonus = {\n no_equipment = {\n build_cost_ic = -0.1\n }\n}",
        "edge.txt",
        equipment,
    )
    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("mio-equipment-type-unknown", "edge.txt", 2)]


def test_event_index_skips_non_definitions_and_non_script_files(tmp_path, write_path):
    write_path(tmp_path, "events/ignored.md", "country_event = { id = ignored.1 }")
    path = write_path(
        tmp_path,
        "events/edge.txt",
        "country_event = { id = caller.1 }\n"
        "country_event = { id = tst.1 is_triggered_only = yes }\n"
        "country_event = { is_triggered_only = yes }\n",
    )
    assert mistakes._build_event_index(str(tmp_path)) == {"tst.1": str(path)}
    assert mistakes._build_event_index(None) == {}
    assert mistakes._build_event_index(str(tmp_path / "missing")) == {}


def test_event_block_lookup_keeps_missing_files_cached(tmp_path, monkeypatch):
    path = str(tmp_path / "missing.txt")
    monkeypatch.setattr(mistakes, "_EVENT_BLOCKS", {})
    index = {"tst.1": path}
    assert mistakes._get_event_block("tst.1", event_index=index) is None
    assert mistakes._EVENT_BLOCKS == {path: {}}
    assert mistakes._get_event_block("tst.1", event_index=index) is None


def test_event_index_lookup_handles_root_resolution_failure(monkeypatch):
    def no_root():
        raise OSError("no checkout")

    monkeypatch.setattr(mistakes, "get_root_dir", no_root)
    monkeypatch.setattr(mistakes, "_EVENT_INDEX_BUILT", False)
    monkeypatch.setattr(mistakes, "_EVENT_INDEX", {})
    assert mistakes._get_event_block("tst.1") is None
    assert mistakes._EVENT_INDEX_BUILT is True


def test_event_index_handles_a_definition_file_removed_after_collection(
    tmp_path, write_path, monkeypatch
):
    write_path(tmp_path, "events/edge.txt", "country_event = { id = tst.1 }")

    def unreadable(*args, **kwargs):
        raise OSError("removed file")

    monkeypatch.setattr(mistakes, "open", unreadable, raising=False)
    assert mistakes._build_event_index(str(tmp_path)) == {}


def test_oob_focus_owner_requires_a_focus_tree():
    text = "focus = { id = TST_focus }"
    nodes = oob._build_block_nodes(text)
    assert oob._focus_root_owner(nodes, text, 0) is None


@pytest.mark.parametrize(
    "worker", [loc.process_txt_for_targeted_vars, loc.process_txt_for_script_var_reads]
)
def test_localisation_reference_workers_handle_empty_text(tmp_path, write_path, worker):
    path = write_path(tmp_path, "common/empty.txt", "")
    assert worker((str(path),)) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [("no block", []), ("{ { content } }", []), ("{ { content", [""])],
)
def test_variable_block_path_handles_absent_bare_and_closed_scopes(text, expected):
    assert variables._block_path_at(text, 0, len(text)) == expected


def test_raid_localisation_handles_files_removed_after_collection(
    tmp_path, monkeypatch
):
    validator = loc.Validator(str(tmp_path), use_colors=False, workers=1)
    monkeypatch.setattr(
        validator,
        "_collect_files",
        lambda *args, **kwargs: [str(tmp_path / "missing.txt")],
    )
    validator.validate_raid_localisation({}, set())
    assert validator._issues == []


def test_shared_localisation_worker_skips_unselected_script_reads(tmp_path, write_path):
    path = write_path(tmp_path, "common/edge.txt", "some_value = yes\n")
    assert loc._scan_shared_txt_file((str(path), str(tmp_path), True, False)) == (
        [],
        (set(), [], set()),
        set(),
        [],
        [],
    )
