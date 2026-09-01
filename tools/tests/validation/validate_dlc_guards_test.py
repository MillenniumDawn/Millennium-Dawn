"""Tests for validate_dlc_guards.

A DLC-gated technology named by an `add_tech_bonus`, or a DLC-gated special
project referenced with `sp:`, must sit behind a `has_dlc` guard: without the
DLC the tooltip resolves into a disabled technology folder and the game crashes
to desktop. Regression for the China `CHI_project_jxx` CTD (issue #2790).
"""

import validate_dlc_guards as V

BBA = "By Blood Alone"
NSB = "No Step Back"

TECH_GATES = {
    "gen_5_light": frozenset({("require", BBA)}),
    "gen_5_medium": frozenset({("require", BBA)}),
    "gen_5_large": frozenset({("require", BBA)}),
    "Strike_fighter5": frozenset({("forbid", BBA)}),
    "nsb_artillery_0": frozenset({("require", NSB)}),
    "SP_arty_0": frozenset({("forbid", NSB)}),
    "ungated_tech": frozenset(),
}
CATEGORY_GATES = {"CAT_air_engine": frozenset({("require", BBA)})}
PROJECT_GATES = {"sp_stealth_technology": frozenset({("require", BBA)})}


def _scan(script):
    scanner = V.Scanner(V._sanitize(script), TECH_GATES, CATEGORY_GATES, PROJECT_GATES)
    scanner.walk(0, len(scanner.text), V.Context())
    return scanner.findings


def _messages(script):
    return [message for _, _, message in _scan(script)]


def _bonus(tech, indent="\t"):
    return (
        f"{indent}add_tech_bonus = {{\n"
        f"{indent}\tname = TST_focus\n"
        f"{indent}\tuses = 1\n"
        f"{indent}\ttechnology = {tech}\n"
        f"{indent}}}\n"
    )


# --- gate parsing -----------------------------------------------------------


def _write(tmp_path, relative, body):
    path = tmp_path.joinpath(*relative.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_parse_folder_gates_require_forbid_and_non_dlc(tmp_path):
    _write(
        tmp_path,
        "common/technology_tags/00_technology.txt",
        "technology_folders = {\n"
        "\tbba_aircraft_folder = {\n"
        "\t\tledger = air\n"
        f'\t\tavailable = {{ has_dlc = "{BBA}" }}\n'
        "\t}\n"
        "\tfixed_wing_folder = {\n"
        f'\t\tavailable = {{ NOT = {{ has_dlc = "{BBA}" }} }}\n'
        "\t}\n"
        "\tspecial_forces_doctrine_folder = {\n"
        "\t\tavailable = { always = no }\n"
        "\t}\n"
        "\tplain_folder = {\n"
        "\t\tledger = army\n"
        "\t}\n"
        "}\n",
    )
    gates = V.parse_folder_gates(str(tmp_path) + "/")
    assert gates["bba_aircraft_folder"] == frozenset({("require", BBA)})
    assert gates["fixed_wing_folder"] == frozenset({("forbid", BBA)})
    assert "special_forces_doctrine_folder" not in gates
    assert "plain_folder" not in gates


def test_parse_folder_gates_ignores_other_blocks_and_unreadable_files(tmp_path):
    _write(
        tmp_path,
        "common/technology_tags/00_technology.txt",
        "technology_Categories = {\n\tCAT_air_engine\n}\n"
        "technology_folders = {\n"
        "\tbba_aircraft_folder = {\n"
        "\t\tledger = air\n"
        "\t\tdoctrine = { }\n"
        f'\t\tavailable = {{ has_dlc = "{BBA}" }}\n'
        "\t}\n"
        "}\n",
    )
    (tmp_path / "common" / "technology_tags" / "broken.txt").mkdir()

    gates = V.parse_folder_gates(str(tmp_path) + "/")

    assert gates == {"bba_aircraft_folder": frozenset({("require", BBA)})}


def test_parse_tech_gates_ignores_other_blocks_and_unreadable_files(tmp_path):
    _write(
        tmp_path,
        "common/technologies/test.txt",
        "technology_sharing_group = {\n\tid = shared\n}\n"
        "technologies = {\n"
        "\tgen_5_light = {\n"
        "\t\tfolder = { name = bba_aircraft_folder }\n"
        "\t\tfolder = { position = { x = 1 y = 1 } }\n"
        "\t\tpath = { leads_to_tech = gen_5_medium }\n"
        "\t}\n"
        "}\n",
    )
    (tmp_path / "common" / "technologies" / "broken.txt").mkdir()

    tech_gates, _categories = V.parse_tech_gates(
        str(tmp_path) + "/", {"bba_aircraft_folder": frozenset({("require", BBA)})}
    )

    assert tech_gates == {"gen_5_light": frozenset({("require", BBA)})}


def test_category_shared_by_ungated_techs_only_is_not_gated(tmp_path):
    _, category_gates = _tech_gates(
        tmp_path,
        "\tplain_one = {\n\t\tcategories = { CAT_open }\n\t}\n"
        "\tplain_two = {\n\t\tcategories = { CAT_open }\n\t}\n",
        {},
    )

    assert category_gates == {}


def _tech_gates(tmp_path, body, folder_gates):
    _write(
        tmp_path, "common/technologies/test.txt", "technologies = {\n" + body + "}\n"
    )
    return V.parse_tech_gates(str(tmp_path) + "/", folder_gates)


def test_tech_inherits_gate_from_its_folder(tmp_path):
    tech_gates, _ = _tech_gates(
        tmp_path,
        "\tgen_5_light = {\n\t\tfolder = { name = bba_aircraft_folder }\n\t}\n",
        {"bba_aircraft_folder": frozenset({("require", BBA)})},
    )
    assert tech_gates["gen_5_light"] == frozenset({("require", BBA)})


def test_tech_in_gated_and_ungated_folder_is_not_gated(tmp_path):
    tech_gates, _ = _tech_gates(
        tmp_path,
        "\tshared_tech = {\n"
        "\t\tfolder = { name = bba_aircraft_folder }\n"
        "\t\tfolder = { name = plain_folder }\n"
        "\t}\n",
        {"bba_aircraft_folder": frozenset({("require", BBA)})},
    )
    assert tech_gates["shared_tech"] == frozenset()


def test_allow_branch_gate_without_folder(tmp_path):
    tech_gates, _ = _tech_gates(
        tmp_path,
        '\tencryption1 = {\n\t\tallow_branch = { NOT = { has_dlc = "La Resistance" } }\n\t}\n',
        {},
    )
    assert tech_gates["encryption1"] == frozenset({("forbid", "La Resistance")})


def test_category_gated_only_when_every_member_shares_the_gate(tmp_path):
    _, category_gates = _tech_gates(
        tmp_path,
        "\tgen_5_light = {\n"
        "\t\tfolder = { name = bba_aircraft_folder }\n"
        "\t\tcategories = { CAT_air_engine CAT_air_eqp }\n"
        "\t}\n"
        "\tgen_5_medium = {\n"
        "\t\tfolder = { name = bba_aircraft_folder }\n"
        "\t\tcategories = { CAT_air_engine }\n"
        "\t}\n"
        "\tpiston_engine = {\n"
        "\t\tcategories = { CAT_air_eqp }\n"
        "\t}\n",
        {"bba_aircraft_folder": frozenset({("require", BBA)})},
    )
    assert category_gates["CAT_air_engine"] == frozenset({("require", BBA)})
    assert "CAT_air_eqp" not in category_gates


def test_parse_project_gates(tmp_path):
    _write(
        tmp_path,
        "common/special_projects/projects/air_projects.txt",
        "sp_stealth_technology = {\n"
        f'\tallowed = {{ has_dlc = "{BBA}" }}\n'
        "\tspecialization = specialization_air\n"
        "}\n"
        "sp_open_project = {\n"
        "\tspecialization = specialization_air\n"
        "}\n",
    )
    gates = V.parse_project_gates(str(tmp_path) + "/")
    assert gates == {"sp_stealth_technology": frozenset({("require", BBA)})}


def test_parse_project_gates_skips_unreadable_files(tmp_path):
    _write(
        tmp_path,
        "common/special_projects/projects/air_projects.txt",
        "sp_stealth_technology = {\n"
        f'\tallowed = {{ has_dlc = "{BBA}" }}\n'
        "\tnth_completion_reward = { add_tech_bonus = { uses = 1 } }\n"
        "}\n",
    )
    (tmp_path / "common" / "special_projects" / "projects" / "broken.txt").mkdir()

    assert V.parse_project_gates(str(tmp_path) + "/") == {
        "sp_stealth_technology": frozenset({("require", BBA)})
    }


# --- guard walker -----------------------------------------------------------


def test_unguarded_tech_bonus_is_flagged():
    messages = _messages("completion_reward = {\n" + _bonus("gen_5_light") + "}\n")
    assert len(messages) == 1
    assert "gen_5_light" in messages[0]
    assert BBA in messages[0]


def test_ungated_tech_is_clean():
    assert _scan("completion_reward = {\n" + _bonus("ungated_tech") + "}\n") == []


def test_guarded_tech_bonus_is_clean():
    script = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("gen_5_light", "\t\t")
        + "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_sibling_else_of_a_dlc_if_flags_a_require_tech():
    script = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("gen_5_light", "\t\t")
        + "\t}\n"
        "\telse = {\n" + _bonus("gen_5_medium", "\t\t") + "\t}\n"
        "}\n"
    )
    messages = _messages(script)
    assert len(messages) == 1
    assert "gen_5_medium" in messages[0]


def test_sibling_else_of_a_dlc_if_accepts_the_legacy_tech():
    script = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("gen_5_light", "\t\t")
        + "\t}\n"
        "\telse = {\n" + _bonus("Strike_fighter5", "\t\t") + "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_nested_else_inverts_its_enclosing_if():
    """HOI4 also accepts `else` inside the `if` body, not only as a sibling."""
    script = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ NOT = {{ has_dlc = "{NSB}" }} }}\n'
        + _bonus("SP_arty_0", "\t\t")
        + "\t\telse = {\n"
        + _bonus("nsb_artillery_0", "\t\t\t")
        + "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_else_if_chain_is_clean():
    script = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" has_tech = gen_5_medium }}\n'
        + _bonus("gen_5_light", "\t\t")
        + "\t}\n"
        "\telse_if = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("gen_5_medium", "\t\t")
        + "\t}\n"
        "\telse = {\n" + _bonus("Strike_fighter5", "\t\t") + "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_forbid_tech_inside_a_dlc_branch_is_flagged():
    script = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("Strike_fighter5", "\t\t")
        + "\t}\n"
        "}\n"
    )
    messages = _messages(script)
    assert len(messages) == 1
    assert "unavailable" in messages[0]


def test_object_level_gate_covers_sibling_effects():
    script = (
        "decision = {\n"
        f'\tavailable = {{ has_dlc = "{BBA}" }}\n'
        "\tcomplete_effect = {\n" + _bonus("gen_5_light", "\t\t") + "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_brace_inside_a_quoted_string_does_not_desync_the_walker():
    script = (
        "completion_reward = {\n"
        '\tlog = "[GetDateText]: unbalanced { brace"\n'
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("gen_5_light", "\t\t")
        + "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_gated_category_is_flagged_and_guarded_category_is_clean():
    unguarded = (
        "completion_reward = {\n"
        "\tadd_tech_bonus = { name = TST_focus category = CAT_air_engine uses = 1 }\n"
        "}\n"
    )
    findings = _scan(unguarded)
    assert len(findings) == 1
    assert findings[0][0] == "dlc_tech_bonus_category"

    guarded = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        "\t\tadd_tech_bonus = { name = TST_focus category = CAT_air_engine uses = 1 }\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(guarded) == []


def test_special_project_reference_needs_the_same_guard():
    unguarded = (
        "completion_reward = {\n"
        "\tsp:sp_stealth_technology = { add_project_progress_ratio = 0.35 }\n"
        "}\n"
    )
    findings = _scan(unguarded)
    assert len(findings) == 1
    assert findings[0][0] == "dlc_special_project"

    guarded = (
        "completion_reward = {\n"
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        "\t\tsp:sp_stealth_technology = { add_project_progress_ratio = 0.35 }\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(guarded) == []


def test_project_jxx_regression():
    """The exact pre-fix CHI_project_jxx reward: three techs plus the project."""
    script = (
        "focus = {\n"
        "\tid = CHI_project_jxx\n"
        "\tcompletion_reward = {\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Focus CHI_project_jxx"\n'
        "\t\tadd_tech_bonus = {\n"
        "\t\t\tname = CHI_project_jxx\n"
        "\t\t\tahead_reduction = 5\n"
        "\t\t\tuses = 1\n"
        "\t\t\ttechnology = gen_5_light\n"
        "\t\t\ttechnology = gen_5_medium\n"
        "\t\t\ttechnology = gen_5_large\n"
        "\t\t}\n"
        "\t\tsp:sp_stealth_technology = { add_project_progress_ratio = 0.35 }\n"
        "\t}\n"
        "\tai_will_do = { base = 1 }\n"
        "}\n"
    )
    categories = [category for category, _, _ in _scan(script)]
    assert categories.count("dlc_tech_bonus") == 3
    assert categories.count("dlc_special_project") == 1


# --- sanitize -----------------------------------------------------------


def test_sanitize_handles_escaped_quote_ahead_of_braces():
    """A single escaped quote inside a string used to leave the old
    quote-blanker's regex one `"` short, so it never found a closing quote for
    the rest of the string and left everything after it — including a
    `key = {` -shaped fragment — as raw, unblanked text that `_child_blocks`
    would misread as a real block, desyncing the brace-depth walk."""
    script = (
        "completion_reward = {\n"
        '\tlog = "note \\"quoted bit: fake = { should_be_invisible = yes }"\n'
        "\tif = {\n"
        f'\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("gen_5_light", "\t\t")
        + "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


# --- scan_file cache ------------------------------------------------------


def test_scan_file_cache_invalidates_when_gate_maps_change(tmp_path, monkeypatch):
    """`scan_file`'s disk cache used to key only on the scanned file's own
    content. A `has_dlc` gate added to `common/technologies/` (etc.) without
    touching the referencing file would then return a stale "clean" result
    forever, defeating the validator (see the module docstring's CTD)."""
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    filepath = _write(
        tmp_path,
        "events/test_events.txt",
        "completion_reward = {\n" + _bonus("gen_5_light") + "}\n",
    )
    mod_path = str(tmp_path) + "/"

    ungated = {"gen_5_light": frozenset()}
    V._init_worker(ungated, {}, {}, V._fingerprint_gates(ungated, {}, {}), mod_path)
    assert V.scan_file(str(filepath)) == []

    gated = {"gen_5_light": frozenset({("require", BBA)})}
    V._init_worker(gated, {}, {}, V._fingerprint_gates(gated, {}, {}), mod_path)
    findings = V.scan_file(str(filepath))
    assert len(findings) == 1
    assert "gen_5_light" in findings[0][3]


def test_ungated_category_and_project_references_are_clean():
    script = (
        "completion_reward = {\n"
        "\tadd_tech_bonus = { name = TST_focus category = CAT_open uses = 1 }\n"
        "\tsp:sp_open_project = { add_project_progress_ratio = 0.2 }\n"
        "}\n"
    )
    assert _scan(script) == []


def test_scan_file_skips_unreadable_and_irrelevant_files(tmp_path):
    V._init_worker({}, {}, {}, "", str(tmp_path) + "/")
    (tmp_path / "broken.txt").mkdir()
    plain = _write(tmp_path, "events/plain.txt", "country_event = { id = test.1 }\n")

    assert V.scan_file(str(tmp_path / "broken.txt")) == []
    assert V.scan_file(str(plain)) == []


# --- validator wiring -------------------------------------------------------


def _dlc_repo(tmp_path):
    _write(
        tmp_path,
        "common/technology_tags/00_technology.txt",
        "technology_folders = {\n"
        "\tbba_aircraft_folder = {\n"
        f'\t\tavailable = {{ has_dlc = "{BBA}" }}\n'
        "\t}\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/technologies/air.txt",
        "technologies = {\n"
        "\tgen_5_light = {\n"
        "\t\tfolder = { name = bba_aircraft_folder }\n"
        "\t\tcategories = { CAT_air_engine }\n"
        "\t}\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/special_projects/projects/air.txt",
        "sp_stealth_technology = {\n" f'\tallowed = {{ has_dlc = "{BBA}" }}\n' "}\n",
    )


def test_validator_reports_crashing_errors_and_category_warnings(tmp_path, monkeypatch):
    import validator_common

    monkeypatch.setattr(validator_common, "_LOG_LEVEL", "INFO")
    _dlc_repo(tmp_path)
    _write(
        tmp_path,
        "common/national_focus/05_test.txt",
        "focus = {\n"
        "\tid = TST_jet\n"
        "\tcompletion_reward = {\n"
        + _bonus("gen_5_light", "\t\t")
        + "\t\tadd_tech_bonus = { name = TST_jet category = CAT_air_engine uses = 1 }\n"
        "\t\tsp:sp_stealth_technology = { add_project_progress_ratio = 0.35 }\n"
        "\t}\n"
        "}\n",
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)

    validator.run_validations()
    by_category = {i.category: i.severity for i in validator._issues}

    assert by_category == {
        "dlc_tech_bonus": "error",
        "dlc_tech_bonus_category": "warning",
        "dlc_special_project": "error",
    }
    assert any(
        "3 unguarded DLC-gated reference(s)" in line for line in validator.output_lines
    )
    assert any(
        line.startswith("  common/national_focus/05_test.txt:")
        for line in validator.output_lines
    )


def test_validator_stays_quiet_when_every_reference_is_guarded(tmp_path, monkeypatch):
    import validator_common

    monkeypatch.setattr(validator_common, "_LOG_LEVEL", "INFO")
    _dlc_repo(tmp_path)
    _write(
        tmp_path,
        "common/national_focus/05_test.txt",
        "focus = {\n"
        "\tid = TST_jet\n"
        "\tcompletion_reward = {\n"
        "\t\tif = {\n"
        f'\t\t\tlimit = {{ has_dlc = "{BBA}" }}\n'
        + _bonus("gen_5_light", "\t\t\t")
        + "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)

    validator.run_validations()

    assert validator._issues == []
    assert any("sit behind a has_dlc guard" in line for line in validator.output_lines)
