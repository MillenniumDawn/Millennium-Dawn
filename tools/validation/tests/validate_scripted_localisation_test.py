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
