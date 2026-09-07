"""Focused regressions for scripted-localisation invocation scanning."""

import validate_scripted_localisation as V


def test_scripted_loc_keeps_and_reports_undefined_bracketed_invocation(tmp_path):
    loc_dir = tmp_path / "common" / "scripted_localisation"
    loc_dir.mkdir(parents=True)
    path = loc_dir / "test.txt"
    path.write_text(
        "defined_text = { name = Wrapper text = { localization_key = [MissingNestedLoc] } }\n"
    )

    used, paths = V.process_file_for_used_localisations(
        (str(path), {"Wrapper"}, False, str(tmp_path))
    )
    assert used == ["MissingNestedLoc"]

    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_missing_scripted_localisations([], ["Wrapper"], used, paths)
    assert len(validator._issues) == 1
    assert validator._issues[0].category == "missing-scripted-loc"
    assert "missingnestedloc" in validator._issues[0].message.lower()


def test_gfx_icon_check_accepts_bare_sprite_names(tmp_path):
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "icons.gfx").write_text(
        "spriteTypes = {\n\tspriteType = { name = GFX_bare_icon }\n}\n"
    )
    loc_dir = tmp_path / "common" / "scripted_localisation"
    loc_dir.mkdir(parents=True)
    (loc_dir / "icons.txt").write_text("localization_key = GFX_bare_icon\n")

    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_gfx_icons()

    assert validator._issues == []


def test_digit_prefixed_defined_loc_is_tracked_via_gui(tmp_path):
    gui_dir = tmp_path / "interface"
    gui_dir.mkdir()
    gui = gui_dir / "consumer.gui"
    gui.write_text('image = "[991_maoist_influence]"\n')

    used, paths = V.process_file_for_used_localisations(
        (str(gui), {"991_maoist_influence"}, False, str(tmp_path))
    )
    assert used == ["991_maoist_influence"]
    assert paths == {"991_maoist_influence": "consumer.gui"}
    assert V._scan_loc_tokens("[991_maoist_influence]", False) == {
        "991_maoist_influence"
    }


def test_defined_bracketed_invocation_is_tracked(tmp_path):
    path = tmp_path / "consumer.txt"
    path.write_text("custom_effect_tooltip = [DefinedNestedLoc]\n")

    used, paths = V.process_file_for_used_localisations(
        (str(path), {"DefinedNestedLoc"}, False, str(tmp_path))
    )
    assert used == ["DefinedNestedLoc"]
    assert paths == {"DefinedNestedLoc": "consumer.txt"}


def test_english_yml_keeps_undefined_bracketed_invocation(tmp_path):
    path = tmp_path / "localisation" / "english" / "consumer_l_english.yml"
    path.parent.mkdir(parents=True)
    path.write_text('l_english:\n  text: "[MissingYmlLoc] [GetYear]"\n')
    translated = tmp_path / "localisation" / "braz_por" / path.name
    translated.parent.mkdir(parents=True)
    translated.write_text('l_braz_por:\n  text: "[MissingYmlLoc]"\n')

    used, paths = V.process_file_for_used_localisations(
        (str(path), set(), False, str(tmp_path))
    )
    assert used == ["MissingYmlLoc"]
    assert paths == {"MissingYmlLoc": "consumer_l_english.yml"}

    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_missing_scripted_localisations([], [], used, paths)
    assert validator._issues[0].file == "localisation/english/consumer_l_english.yml"


def test_gui_keeps_undefined_bracketed_invocation(tmp_path):
    path = tmp_path / "consumer.gui"
    path.write_text('text = "[MissingGuiLoc]"\n')

    used, paths = V.process_file_for_used_localisations(
        (str(path), set(), False, str(tmp_path))
    )
    assert used == ["MissingGuiLoc"]
    assert paths == {"MissingGuiLoc": "consumer.gui"}


def test_scoped_bracketed_invocation_tracks_member_name():
    assert V._scan_loc_tokens("[THIS.MD_auto_agency_status]", False) == {
        "MD_auto_agency_status"
    }


def test_unknown_lowercase_and_uppercase_bracket_calls_are_retained():
    assert V._scan_loc_tokens("[status] [USA_STATUS]", False) == {
        "status",
        "USA_STATUS",
    }


def test_engine_getters_are_not_scripted_loc_candidates(tmp_path):
    getters = " ".join(
        f"[{value}] [ROOT.{value}]"
        for value in (
            "GetFullName",
            "GetRank",
            "GetRulingParty",
            "GetCountryContinent",
        )
    )
    gui = tmp_path / "consumer.gui"
    gui.write_text(f'text = "{getters} [MissingGuiLoc]"\n')
    yml = tmp_path / "localisation" / "english" / "consumer_l_english.yml"
    yml.parent.mkdir(parents=True)
    yml.write_text(f'l_english:\n  text: "{getters} [MissingYmlLoc]"\n')

    gui_used, _ = V.process_file_for_used_localisations(
        (str(gui), set(), False, str(tmp_path))
    )
    yml_used, _ = V.process_file_for_used_localisations(
        (str(yml), set(), False, str(tmp_path))
    )

    assert gui_used == ["MissingGuiLoc"]
    assert yml_used == ["MissingYmlLoc"]


def test_defined_get_prefixed_scripted_loc_is_retained():
    assert V._scan_loc_tokens("[GetProjectStatus]", False, {"GetProjectStatus"}) == {
        "GetProjectStatus"
    }


def test_staged_gui_uses_full_definition_set(tmp_path):
    loc_dir = tmp_path / "common" / "scripted_localisation"
    loc_dir.mkdir(parents=True)
    (loc_dir / "definitions.txt").write_text(
        "defined_text = { name = ExistingGuiLoc text = { localization_key = KEY } }\n"
    )
    gui_dir = tmp_path / "interface"
    gui_dir.mkdir()
    gui = gui_dir / "consumer.gui"
    gui.write_text('text = "[ExistingGuiLoc] [MissingGuiLoc]"\n')

    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = [str(gui)]
    validator.run_validations()

    missing = [
        issue.message
        for issue in validator._issues
        if issue.category == "missing-scripted-loc"
    ]
    assert len(missing) == 1
    assert "missingguiloc" in missing[0].lower()


def test_builtin_and_ordinary_syntax_do_not_create_candidates():
    text = (
        "localization_key = ORDINARY_LOC_KEY\n"
        "text = [GetDateText]\n"
        "text = [ROOT.GetName]\n"
        "text = [?country_var]\n"
        "text = $ORDINARY_LOC_KEY$\n"
    )
    assert V._scan_loc_tokens(text, is_scripted_loc_file=True) == set()


def test_hyphenated_scripted_loc_is_defined_and_used():
    # MD sub-ideology names carry hyphens (Communist-State_valid); a name class without
    # `-` truncates them to `Communist` on both sides and invents unused findings.
    defined, _ = V._scan_defined_locs(
        "defined_text = { name = Communist-State_valid }", "ideologies.txt"
    )
    assert defined == ["Communist-State_valid"]
    assert V._scan_loc_tokens("[Communist-State_valid]", False) == {
        "Communist-State_valid"
    }


def test_reference_line_skips_substring_match(tmp_path):
    path = tmp_path / "loc_l_english.yml"
    path.write_text(
        'l_english:\n a: "[SAF.GetAdjective]"\n b: "filler"\n c: "[SAF.Adjective]"\n'
    )
    assert V._find_reference_line(str(path), "adjective") == 4


def test_definition_line_skips_longer_name_prefix(tmp_path):
    path = tmp_path / "defs.txt"
    path.write_text(
        "defined_text = {\n\tname = Communist-State_valid\n}\n"
        "defined_text = {\n\tname = communist\n}\n"
    )
    assert V._find_definition_line(str(path), "communist") == 5


def _write_sloc(tmp_path, name, body):
    loc_dir = tmp_path / "common" / "scripted_localisation"
    loc_dir.mkdir(parents=True, exist_ok=True)
    path = loc_dir / name
    path.write_text(body, encoding="utf-8")
    return str(path)


def test_defined_scan_reports_names_and_their_file(tmp_path):
    path = _write_sloc(
        tmp_path,
        "defs.txt",
        "defined_text = {\n\tname = FirstLoc\n}\n"
        "defined_text = {\n\tname = SecondLoc\n}\n",
    )
    names, paths = V.process_file_for_defined_localisations(
        (path, False, str(tmp_path))
    )
    assert names == ["FirstLoc", "SecondLoc"]
    assert paths == {"FirstLoc": "defs.txt", "SecondLoc": "defs.txt"}


def test_defined_scan_ignores_a_file_without_defined_text(tmp_path):
    path = _write_sloc(tmp_path, "notes.txt", "name = NotADefinedText\n")
    assert V.process_file_for_defined_localisations((path, False, str(tmp_path))) == (
        [],
        {},
    )


def test_defined_scan_skips_the_french_loc_dump(tmp_path):
    # 00_scripted_localisation_FR_loc.txt is a translation dump, not definitions
    # (AGENTS.md keeps non-English loc out of scope).
    path = _write_sloc(
        tmp_path,
        "00_scripted_localisation_FR_loc.txt",
        "defined_text = {\n\tname = FrenchOnly\n}\n",
    )
    assert V.process_file_for_defined_localisations((path, False, str(tmp_path))) == (
        [],
        {},
    )


def test_scans_skip_ignored_directories(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    path = docs / "sample.txt"
    path.write_text("defined_text = {\n\tname = DocsOnly\n}\n", encoding="utf-8")

    assert (
        V.process_file_for_defined_localisations((str(path), False, str(tmp_path)))[0]
        == []
    )
    assert V.process_file_for_used_localisations(
        (str(path), {"DocsOnly"}, False, str(tmp_path))
    ) == ([], {})


def test_usage_scan_returns_nothing_when_no_name_matches(tmp_path):
    path = tmp_path / "consumer.txt"
    path.write_text("custom_effect_tooltip = SomeOtherKey\n")
    assert V.process_file_for_used_localisations(
        (str(path), {"DefinedLoc"}, False, str(tmp_path))
    ) == ([], {})


def test_reference_line_falls_back_through_the_tooltip_syntax(tmp_path):
    path = tmp_path / "consumer.txt"
    path.write_text(
        "filler = yes\ncustom_effect_tooltip = MyScriptedLoc\n",
    )
    assert V._find_reference_line(str(path), "myscriptedloc") == 2


def test_reference_line_skips_an_earlier_tooltip_for_another_key(tmp_path):
    path = tmp_path / "consumer.txt"
    path.write_text(
        "custom_effect_tooltip = OtherLoc\ncustom_trigger_tooltip = MyScriptedLoc\n",
    )
    assert V._find_reference_line(str(path), "myscriptedloc") == 2


def test_reference_line_falls_back_to_a_plain_search(tmp_path):
    path = tmp_path / "consumer.txt"
    path.write_text("filler = yes\nsomething = MyScriptedLoc\n")
    assert V._find_reference_line(str(path), "myscriptedloc") == 2


def test_reference_line_of_an_unreadable_file_is_zero(tmp_path):
    assert V._find_reference_line(str(tmp_path / "absent.txt"), "anything") == 0


def test_definition_line_falls_back_to_a_plain_search(tmp_path):
    # The anchored pattern refuses `name = communist_party` for `communist`;
    # the substring fallback still points at the only plausible line.
    path = tmp_path / "defs.txt"
    path.write_text("filler = yes\nname = communist_party\n")
    assert V._find_definition_line(str(path), "communist") == 2


def test_definition_line_of_an_unreadable_file_is_zero(tmp_path):
    assert V._find_definition_line(str(tmp_path / "absent.txt"), "anything") == 0


def test_meta_effect_template_counts_as_a_use(tmp_path):
    _write_sloc(
        tmp_path,
        "defs.txt",
        "defined_text = {\n\tname = tooltip_EU_FRA_approve\n}\n",
    )
    consumer = tmp_path / "common" / "scripted_effects" / "meta.txt"
    consumer.parent.mkdir(parents=True)
    consumer.write_text(
        "meta_effect = {\n"
        "\ttext = { custom_effect_tooltip = tooltip_EU_[TAG]_approve }\n"
        "}\n",
        encoding="utf-8",
    )

    used, paths = V.ScriptedLocalisation.get_all_used_localisations(
        str(tmp_path),
        {"tooltip_EU_FRA_approve"},
        lowercase=False,
        return_paths=True,
        workers=1,
    )

    assert "tooltip_EU_FRA_approve" in used
    assert paths["tooltip_EU_FRA_approve"] == "<meta_effect>"


def test_unused_definition_is_reported_with_its_line(tmp_path):
    _write_sloc(
        tmp_path,
        "defs.txt",
        "defined_text = {\n\tname = UsedLoc\n}\n"
        "defined_text = {\n\tname = OrphanLoc\n}\n",
    )
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_scripted_localisations(
        [],
        ["UsedLoc", "OrphanLoc"],
        {"UsedLoc": "defs.txt", "OrphanLoc": "defs.txt"},
        ["UsedLoc"],
    )

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "unused-scripted-loc"
    assert "orphanloc" in issue.message.lower()
    assert issue.file == "common/scripted_localisation/defs.txt"
    assert issue.line == 5


def test_unused_definition_whose_file_is_gone_is_not_reported(tmp_path):
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_scripted_localisations(
        [], ["OrphanLoc"], {"OrphanLoc": "deleted.txt"}, []
    )
    assert validator._issues == []


def test_unused_check_skips_the_preemptive_party_slot_library(tmp_path):
    _write_sloc(
        tmp_path,
        "defs.txt",
        "defined_text = {\n\tname = eu_parl_pg_party_7\n}\n",
    )
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_scripted_localisations(
        [], ["eu_parl_pg_party_7"], {"eu_parl_pg_party_7": "defs.txt"}, []
    )
    assert validator._issues == []


def test_missing_check_ignores_a_reference_it_cannot_locate(tmp_path):
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_missing_scripted_localisations(
        [], [], ["GhostLoc"], {"GhostLoc": "no_such_file.txt"}
    )
    assert validator._issues == []


def test_gfx_icon_check_flags_an_undefined_sprite(tmp_path):
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "icons.gfx").write_text(
        "spriteTypes = {\n\tspriteType = { name = GFX_real_icon }\n}\n"
    )
    _write_sloc(
        tmp_path,
        "icons.txt",
        "defined_text = {\n"
        "\tname = Icon\n"
        "\ttext = { localization_key = GFX_real_icon }\n"
        "\ttext = { localization_key = GFX_absent_icon }\n"
        "}\n",
    )

    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_gfx_icons()

    assert len(validator._issues) == 1
    assert validator._issues[0].category == "gfx-icon"
    assert "GFX_absent_icon" in validator._issues[0].message
    assert validator._issues[0].line == 4


def test_gfx_icon_check_in_staged_mode_reads_only_staged_files(tmp_path):
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "icons.gfx").write_text("spriteTypes = {\n}\n")
    staged = _write_sloc(
        tmp_path, "staged.txt", "localization_key = GFX_staged_missing\n"
    )
    _write_sloc(tmp_path, "other.txt", "localization_key = GFX_other_missing\n")

    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.staged_files = [staged]
    validator.validate_gfx_icons()

    messages = [issue.message for issue in validator._issues]
    assert any("GFX_staged_missing" in m for m in messages)
    assert not any("GFX_other_missing" in m for m in messages)


class _InlinePool:
    """Stand-in for the validator's shared worker pool: maps in-process."""

    def __init__(self):
        self.closed = False

    def map(self, fn, items, chunksize=None):
        return [fn(item) for item in items]

    def close(self):
        self.closed = True

    def join(self):
        pass


def test_supplied_pool_is_reused_and_left_open(tmp_path):
    _write_sloc(tmp_path, "defs.txt", "defined_text = {\n\tname = SharedLoc\n}\n")
    for name in ("a.txt", "b.txt"):
        consumer = tmp_path / name
        consumer.write_text("custom_effect_tooltip = SharedLoc\n", encoding="utf-8")

    pool = _InlinePool()
    defined = V.ScriptedLocalisation.get_all_defined_localisations(
        str(tmp_path), lowercase=False, pool=pool
    )
    used, paths = V.ScriptedLocalisation.get_all_used_localisations(
        str(tmp_path),
        set(defined),
        lowercase=False,
        return_paths=True,
        pool=pool,
    )

    assert defined == ["SharedLoc"]
    # Recorded once, from whichever consumer was scanned first.
    assert used == ["SharedLoc"]
    assert paths["SharedLoc"] in {"a.txt", "b.txt"}
    assert pool.closed is False


def test_full_run_reports_unused_definitions_and_undefined_icons(tmp_path):
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "icons.gfx").write_text("spriteTypes = {\n}\n")
    _write_sloc(
        tmp_path,
        "defs.txt",
        "defined_text = {\n"
        "\tname = OrphanLoc\n"
        "\ttext = { localization_key = GFX_absent_icon }\n"
        "}\n",
    )

    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    categories = {issue.category for issue in validator._issues}
    assert "unused-scripted-loc" in categories
    assert "gfx-icon" in categories


def test_staged_run_without_staged_files_does_nothing(tmp_path):
    _write_sloc(tmp_path, "defs.txt", "defined_text = {\n\tname = OrphanLoc\n}\n")
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = []
    validator.run_validations()
    assert validator._issues == []


def test_usage_scan_ignores_non_english_localisation(tmp_path):
    english = tmp_path / "localisation" / "english"
    french = tmp_path / "localisation" / "french"
    english.mkdir(parents=True)
    french.mkdir(parents=True)
    (english / "consumer_l_english.yml").write_text(
        'l_english:\n key: "[EnglishOnly]"\n', encoding="utf-8-sig"
    )
    (french / "consumer_l_french.yml").write_text(
        'l_french:\n key: "[FrenchOnly]"\n', encoding="utf-8-sig"
    )

    used = V.ScriptedLocalisation.get_all_used_localisations(
        str(tmp_path), {"EnglishOnly", "FrenchOnly"}, workers=1
    )

    assert "englishonly" in used
    assert "frenchonly" not in used
