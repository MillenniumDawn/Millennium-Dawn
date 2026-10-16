import argparse
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import shared_utils as U


def _write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def test_cpu_budget_override_ci_and_split(monkeypatch):
    monkeypatch.setenv("MD_MAX_WORKERS", "4")
    assert U.cpu_budget() == 4

    monkeypatch.setenv("MD_MAX_WORKERS", "0")
    monkeypatch.setattr(U.os, "cpu_count", lambda: 8)
    monkeypatch.delenv("CI", raising=False)
    assert U.cpu_budget() == 6
    assert U.split_cpu_budget(3) == (3, 2)
    assert U.split_cpu_budget(0) == (1, 6)

    monkeypatch.setenv("CI", "true")
    assert U.cpu_budget() == 8
    monkeypatch.setenv("MD_MAX_WORKERS", "not-a-number")
    assert U.cpu_budget() == 8


def test_logging_honors_debug_and_no_color(monkeypatch, capsys):
    U.log_message("DEBUG", "hidden")
    assert capsys.readouterr().err == ""

    monkeypatch.setenv("NO_COLOR", "1")
    U.log_message("INFO", "visible")
    U.log_message("NOTICE", "unknown", use_colors=False)
    captured = capsys.readouterr().err
    assert "INFO: visible" in captured
    assert "NOTICE: unknown" in captured
    assert "\033[" not in captured


def test_parser_factories_and_linting_extensions():
    file_parser = argparse.ArgumentParser()
    U.add_standard_file_arguments(file_parser, input_help="Custom input")
    assert "Custom input" in file_parser.format_help()
    parsed = file_parser.parse_args(["source.txt", "-o", "dest.txt", "-b", "-v"])
    assert parsed.input_file == "source.txt"
    assert parsed.output == "dest.txt"
    assert parsed.backup and parsed.verbose
    with pytest.raises(SystemExit):
        file_parser.parse_args(["source.txt", "--no-color"])

    validation = U.create_validation_parser("validation")
    parsed = validation.parse_args(
        ["--path", "/mod", "--strict", "--staged", "--no-cache", "--workers", "2"]
    )
    assert parsed.path == "/mod"
    assert parsed.strict and parsed.staged and parsed.no_cache
    assert parsed.workers == 2

    def add_extra(parser):
        parser.add_argument("--extra", action="store_true")

    lint = U.create_linting_parser("lint", include_diff=False, extra_args_fn=add_extra)
    parsed = lint.parse_args(["--mode", "staged", "--files", "x.txt", "--extra"])
    assert parsed.mode == "staged"
    assert parsed.files == ["x.txt"]
    assert parsed.extra
    with pytest.raises(SystemExit):
        lint.parse_args(["--mode", "diff"])


def test_parser_file_collection_modes_and_missing_warning(
    tmp_path, monkeypatch, capsys
):
    existing = tmp_path / "one.txt"
    _write(existing, "x")
    args = SimpleNamespace(
        filenames=[str(existing), str(tmp_path / "gone.txt")], files=None
    )
    args.mode = "all"
    assert U.collect_files_by_mode(args, str(tmp_path)) == [str(existing)]
    assert "not found" in capsys.readouterr().out

    calls = []
    monkeypatch.setattr(
        U,
        "get_git_diff_files",
        lambda **kwargs: calls.append(kwargs) or [str(existing)],
    )
    args = SimpleNamespace(filenames=[], files=[str(existing)], mode="all")
    assert U.collect_files_by_mode(args, str(tmp_path)) == [str(existing)]
    assert calls == []

    args.files = None
    args.mode = "diff"
    args.base_branch = "release"
    assert U.collect_files_by_mode(args, str(tmp_path)) == [str(existing)]
    assert calls[-1] == {"base_branch": "release", "include_interface": False}

    args.mode = "staged"
    assert U.collect_files_by_mode(args, str(tmp_path), include_interface=True)
    assert calls[-1] == {"staged_only": True, "include_interface": True}

    args.mode = "all"
    monkeypatch.setattr(U, "get_all_txt_files", lambda root, **kwargs: [str(existing)])
    assert U.collect_files_by_mode(args, str(tmp_path)) == [str(existing)]


def test_path_helpers_and_txt_targets(tmp_path):
    content = tmp_path / "common" / "nested"
    excluded = content / "tools"
    excluded.mkdir(parents=True)
    _write(content / "a.TXT", "a")
    _write(content / "b.yml", "b")
    _write(excluded / "ignored.txt", "ignored")
    assert U.is_excluded_path(str(excluded / "ignored.txt"), {"tools"}, str(tmp_path))
    assert not U.is_excluded_path(str(content / "a.TXT"), {"tools"}, str(tmp_path))

    found = list(U.iter_txt_targets(str(content), {"tools"}))
    assert found == [("a.TXT", str(content / "a.TXT"))]
    assert list(U.iter_txt_targets(str(content / "a.TXT"), set())) == [
        (str(content / "a.TXT"), str(content / "a.TXT"))
    ]
    assert list(U.iter_txt_targets(str(content / "missing.txt"), set())) == []


def test_text_blocks_and_spacing_edge_cases():
    assert U.strip_inline_comment("foo # comment") == "foo "
    assert (
        U.strip_inline_comment('foo = "# not a comment"') == 'foo = "# not a comment"'
    )
    assert U.find_matching_brace('x = { log = "}" value = { yes } }', 4) == 32
    assert U.find_matching_brace("x = {", 4) == -1
    assert U.extract_block_from_text("name = { value = 1 } tail", 0) == (
        " value = 1 ",
        20,
    )
    assert U.extract_block_from_text("name = no block", 0) == ("", -1)
    assert U.find_unquoted_block_end("inner } tail", 0) == (7, True)
    assert U.find_unquoted_block_end("inner", 0) == (5, False)
    assert U.compact_block(["a\n", "\n", " b  \n"]) == ["a", " b"]
    assert U.collapse_ws_outside_quotes('  a   "b  c"  d  ') == 'a "b  c" d'
    assert U.normalize_spacing("\t# unchanged = {x}") == "\t# unchanged = {x}"
    assert U.collapse_or_compact(["a = {\n", " b = 1\n", "}\n"]) == ["a = { b = 1 }"]
    commented = ["a = { # keep\n", " b = 1\n", "}\n"]
    assert U.collapse_or_compact(commented) == ["a = { # keep", "\tb = 1", "}"]
    assert (
        U.convert_root_factor_to_base(["ai_will_do = {\n", " factor = 2\n", "}\n"])[1]
        == " base = 2\n"
    )
    assert (
        U.convert_root_factor_to_base(["ai_will_do = {\n", " base = 2\n", "}\n"])[1]
        == " base = 2\n"
    )


def test_collapse_or_compact_reindents_a_multi_line_block():
    # Issue #4650: nested lines written at the wrong depth kept their tabs.
    block = [
        "\t\t34 = {\n",
        "\t\t\tadd_building_construction = {\n",
        "\t\t\ttype = infrastructure\n",
        "\t\t\tlevel = 1\n",
        "\t\t\t}\n",
        "\t\t}\n",
    ]
    expected = [
        "\t\t34 = {",
        "\t\t\tadd_building_construction = {",
        "\t\t\t\ttype = infrastructure",
        "\t\t\t\tlevel = 1",
        "\t\t\t}",
        "\t\t}",
    ]
    assert U.collapse_or_compact(block) == expected
    assert U.collapse_or_compact([line.lstrip() for line in block], "\t\t") == expected


def test_collapse_nested_blocks():
    reward = [
        "\t\tcompletion_reward = {",
        '\t\t\tlog = "x"',
        "\t\t\tset_temp_variable = {",
        "\t\t\t\tparty_popularity_increase = 0.1",
        "\t\t\t}",
        "\t\t\thas_country_leader = {",
        '\t\t\t\tname = "Serzh Sargsyan"',
        "\t\t\t\truling_only = yes",
        "\t\t\t}",
        "\t\t}",
    ]
    collapsed = U.collapse_nested_blocks(reward)
    assert collapsed == [
        "\t\tcompletion_reward = {",
        '\t\t\tlog = "x"',
        "\t\t\tset_temp_variable = { party_popularity_increase = 0.1 }",
        "\t\t\thas_country_leader = {",
        '\t\t\t\tname = "Serzh Sargsyan"',
        "\t\t\t\truling_only = yes",
        "\t\t\t}",
        "\t\t}",
    ]
    assert U.collapse_nested_blocks(collapsed) == collapsed
    assert U.collapse_or_compact(reward) == collapsed

    # Innermost first, at any depth; a child with a comment stays multi-line.
    assert U.collapse_nested_blocks(
        [
            "a = {",
            "\tb = {",
            "\t\tc = {",
            "\t\t\tx = 1",
            "\t\t}",
            "\t\ty = 2",
            "\t}",
            "}",
        ]
    ) == ["a = {", "\tb = {", "\t\tc = { x = 1 }", "\t\ty = 2", "\t}", "}"]
    commented = ["a = {", "\tb = {", "\t\tx = 1 # note", "\t}", "\tc = 3", "}"]
    assert U.collapse_nested_blocks(commented) == commented

    # Unbalanced input is handed back untouched rather than reshaped.
    unbalanced = ["a = {", "\tb = {", "\t\tx = 1", "}"]
    assert U.collapse_nested_blocks(unbalanced) == unbalanced
    assert U.collapse_nested_blocks(["a = { b = 1 }"]) == ["a = { b = 1 }"]

    # A multi-token list is not a single leaf; a one-token list still collapses.
    listed = [
        "\t\t\treduce_focus_completion_cost = {",
        "\t\t\t\tcost = 20",
        "\t\t\t\tfocus = {",
        "\t\t\t\t\tCHI_project_921",
        "\t\t\t\t\tCHI_shenzhou_program",
        "\t\t\t\t}",
        "\t\t\t}",
    ]
    assert U.collapse_or_compact(listed) == listed
    assert U.collapse_or_compact(
        [
            "\tx = {",
            "\t\tfocus = {",
            "\t\t\tJAP_blue_water_navy",
            "\t\t}",
            "\t\tcost = 35",
            "\t}",
        ]
    ) == ["\tx = { focus = { JAP_blue_water_navy } cost = 35 }"]


def test_atomic_encoding_backup_and_safe_reads(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "file.txt"
    U.atomic_write_text(str(target), "café\n", encoding="utf-8-sig", bom=True)
    binary = tmp_path / "nested" / "binary.dat"
    U.atomic_write_bytes(str(binary), b"\x00\xff")
    assert binary.read_bytes() == b"\x00\xff"
    assert target.read_bytes() == b"\xef\xbb\xbfcaf\xc3\xa9\n"
    assert U.read_text_strict(str(target)) == "café\n"
    assert U.read_text_strict(str(target), reject_symlink=False).startswith("café")

    inside = tmp_path / "inside.txt"
    assert U.write_text_under(str(inside), str(tmp_path), "inside") is None
    assert U.read_text_under(str(inside), str(tmp_path)) == "inside"
    with pytest.raises(ValueError):
        U.write_text_under(str(tmp_path.parent / "escape.txt"), str(tmp_path), "no")

    backup = U.create_backup(str(target))
    assert Path(backup).read_bytes() == target.read_bytes()
    assert U.clean_filepath("prefix/common/file.txt") == "common/file.txt"
    assert U.clean_filepath("unrelated.txt") == "unrelated.txt"

    assert U.create_backup(str(tmp_path / "missing")) == ""


def test_find_install_and_idea_categories(tmp_path, monkeypatch):
    install = tmp_path / "hoi4"
    install.mkdir()
    monkeypatch.setenv("HOI4_PATH", str(install))
    assert U.find_hoi4_install() == str(install)
    assert U.find_hoi4_install(str(install)) == str(install)
    monkeypatch.delenv("HOI4_PATH")
    monkeypatch.setattr(U, "HOI4_INSTALL_PATHS", [str(tmp_path / "missing-install")])
    monkeypatch.setattr(U, "HOI4_DISCOVERY_SOURCES", [])
    assert U.find_hoi4_install() is None

    monkeypatch.setattr(U, "HOI4_DISCOVERY_SOURCES", [lambda: [str(install)]])
    assert U.find_hoi4_install() == str(install)

    tags = tmp_path / "common" / "idea_tags"
    _write(
        tags / "00_tags.txt",
        "idea_categories = {\n"
        " selectable = { slot = national_spirit type = national_spirit }\n"
        " hidden = { hidden = yes slot = dynamic_modifier_slots }\n"
        " plain = { type = army_spirit }\n"
        "}\n",
    )
    _write(tags / "not_tags.txt", "not categories = { x = { yes = no } }\n")
    _write(tags / "broken.txt", "idea_categories = { broken = { slot = x\n")
    categories = U.get_all_idea_categories(str(tmp_path))
    assert [category["name"] for category in categories] == [
        "selectable",
        "hidden",
        "plain",
        "broken",
    ]
    assert categories[0]["has_slot"] and categories[0]["type"] == "national_spirit"
    assert categories[1]["hidden"] and categories[1]["has_char_slot"] is False
    assert U.get_non_selectable_idea_categories(str(tmp_path)) == frozenset(
        {"plain", "hidden"}
    )
    assert U.get_slotless_idea_categories(str(tmp_path)) == frozenset({"plain"})

    empty = tmp_path / "empty"
    assert U.get_all_idea_categories(str(empty)) == []
    assert U.get_non_selectable_idea_categories(str(empty)) == frozenset(
        {"country", "hidden_ideas"}
    )
    assert U.get_slotless_idea_categories(str(empty)) == frozenset()


def test_steam_library_installs_reads_every_library_folder(tmp_path, monkeypatch):
    steam = tmp_path / "Steam"
    other = tmp_path / "Games"
    game = other / "steamapps" / "common" / "Hearts of Iron IV"
    game.mkdir(parents=True)
    escaped_steam = str(steam).replace("\\", "\\\\")
    escaped_other = str(other).replace("\\", "\\\\")
    _write(
        steam / "steamapps" / "libraryfolders.vdf",
        '"libraryfolders"\n{\n'
        f'\t"0"\n\t{{\n\t\t"path"\t\t"{escaped_steam}"\n\t}}\n'
        f'\t"1"\n\t{{\n\t\t"path"\t\t"{escaped_other}"\n\t}}\n}}\n',
    )
    monkeypatch.setattr(U, "_steam_roots", lambda: [str(steam)])
    installs = U._steam_library_installs()
    assert installs == [
        os.path.join(str(steam), U._HOI4_GAME_SUBDIR),
        os.path.join(str(other), U._HOI4_GAME_SUBDIR),
    ]
    monkeypatch.setattr(U, "HOI4_INSTALL_PATHS", [])
    monkeypatch.delenv("HOI4_PATH", raising=False)
    assert U.find_hoi4_install() == str(game)

    monkeypatch.setattr(U, "_steam_roots", lambda: [str(tmp_path / "nowhere")])
    assert U._steam_library_installs() == []


def test_editor_settings_installs_parses_jsonc(tmp_path, monkeypatch):
    settings = tmp_path / "settings.json"
    _write(
        settings,
        "{\n"
        "    // user settings\n"
        '    "cwtools.cache.hoi4": "H:\\\\Games\\\\Hearts of Iron IV",\n'
        '    "mdHoi4Utilities.installPath": "h:\\\\Games\\\\Hearts of Iron IV\\\\",\n'
        '    "mdHoi4Utilities.modFile": "D:\\\\mod\\\\descriptor.mod",\n'
        "}\n",
    )
    monkeypatch.setattr(U, "_editor_settings_files", lambda: [str(settings)])
    assert U._editor_settings_installs() == [
        "H:\\Games\\Hearts of Iron IV",
        "h:\\Games\\Hearts of Iron IV",
    ]

    _write(settings, '{ "editor.tabSize": 4 }\n')
    assert U._editor_settings_installs() == []
    monkeypatch.setattr(U, "_editor_settings_files", lambda: [str(tmp_path / "gone")])
    assert U._editor_settings_installs() == []


def test_file_opener_cleaners_and_line_helpers(tmp_path, monkeypatch, capsys):
    path = tmp_path / "data.txt"
    _write(path, 'KEY = "Value # kept" # remove\n')
    U.FileOpener.clear_cache()
    raw = U.FileOpener.open_text_file(
        str(path), lowercase=True, strip_comments_flag=True
    )
    assert raw == 'key = "value # kept" \n'
    assert (
        U.FileOpener.open_text_file(str(path), lowercase=True, strip_comments_flag=True)
        == raw
    )
    U.FileOpener.invalidate(str(path))
    assert U.find_line_number(str(path), "KEY") == 1
    assert U.find_line_number(str(path), "missing") == 0
    assert U.strip_comments('a # x\n# whole\nlog = "# keep"') == 'a \n\nlog = "# keep"'
    assert U.strip_comments('log = "a \\" # keep" # x') == 'log = "a \\" # keep" '
    assert U.blank_quoted_strings('x = "a { b }"\nyes', {4}) == 'x = "a { b }"\nyes'

    assert U.drop_partial_matches({"abc": 1, "x": 2}, ("b",)) == ["x"]
    assert U.drop_partial_matches(["abc", "x"], ()) == ["abc", "x"]

    assert U.compute_line_offsets("a\nb\n") == [1, 3]
    assert U.line_for_offset([1, 3], 1) == 1
    monkeypatch.setenv("MD_TIMING", "0")
    assert not U.timing_enabled()
    U.print_timing_summary([])
    U.print_timing_summary([("step", 1.0)])
    assert capsys.readouterr().err == ""


def test_timer_and_timing_summary(monkeypatch, capsys):
    timer = U.Timer("manual", enabled=False)
    assert timer.stop() == 0.0
    with U.Timer("context", enabled=True):
        pass
    U.print_timing_summary([("first", 0.0), ("second", 1.0)])
    assert "Timing summary" in capsys.readouterr().err
    monkeypatch.setenv("MD_TIMING", "0")
    assert U.Timer("disabled").enabled is False


def test_git_file_discovery_and_pool_seams(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "common" / "a.txt", "a")
    _write(tmp_path / "interface" / "b.txt", "b")
    U._staged_files_cache = None
    monkeypatch.setenv("MD_STAGED_FILES", "common/a.txt\ninterface/b.txt\nmissing.txt")
    assert U.get_git_diff_files(staged_only=True) == ["common/a.txt"]
    U._staged_files_cache = None
    assert U.get_git_diff_files(staged_only=True, include_interface=True) == [
        "common/a.txt",
        "interface/b.txt",
    ]
    monkeypatch.delenv("MD_STAGED_FILES")
    result = SimpleNamespace(stdout="common/a.txt\ninterface/b.txt\n", returncode=0)
    calls = []
    monkeypatch.setattr(
        U.subprocess, "run", lambda command, **kwargs: calls.append(command) or result
    )
    assert U.get_git_diff_files(base_branch="release") == ["common/a.txt"]
    assert calls[0][-1] == "release...HEAD"
    monkeypatch.setattr(
        U.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(OSError())
    )
    assert U.get_git_diff_files() == []

    monkeypatch.setattr(
        U.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="")
    )
    assert U.get_staged_files(str(tmp_path)) is None
    assert U.get_all_txt_files(str(tmp_path)) == [str(tmp_path / "common" / "a.txt")]
    assert U.get_all_txt_files(str(tmp_path), include_interface=True) == [
        str(tmp_path / "common" / "a.txt"),
        str(tmp_path / "interface" / "b.txt"),
    ]

    assert U.run_with_pool(str.upper, ["a", "b"], workers=1) == ["A", "B"]
    assert U.run_with_pool(str.upper, [], workers=4) == []

    class FakePool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def map(self, func, items, **kwargs):
            self.map_kwargs = kwargs
            return [func(item) for item in items]

    import multiprocessing

    monkeypatch.setattr(multiprocessing, "Pool", FakePool)
    assert U.run_with_pool(
        str.upper, list("abcdefghij"), workers=2, chunksize=3
    ) == list("ABCDEFGHIJ")
    assert U.run_with_pool(str.upper, list("abcdefghij"), workers=2) == list(
        "ABCDEFGHIJ"
    )


def test_staged_file_parsing_subprocess_and_rename(tmp_path, monkeypatch):
    _write(tmp_path / "common" / "a.txt", "a")
    monkeypatch.setenv("MD_STAGED_FILES", "common/a.txt\ncommon/deleted.txt")
    assert U.get_staged_files(str(tmp_path), extensions=[".txt"]) == [
        str(tmp_path / "common" / "a.txt")
    ]
    assert U.get_staged_files(str(tmp_path), extensions=[".yml"]) is None
    assert U.get_staged_files(str(tmp_path), include_missing=True) == [
        str(tmp_path / "common" / "a.txt"),
        str(tmp_path / "common" / "deleted.txt"),
    ]

    monkeypatch.delenv("MD_STAGED_FILES")
    outputs = iter(
        [SimpleNamespace(stdout="R100\tcommon/old.txt\tcommon/new.txt\n", returncode=0)]
    )
    monkeypatch.setattr(U.subprocess, "run", lambda *args, **kwargs: next(outputs))
    assert U.get_staged_files(str(tmp_path), include_missing=True) == [
        str(tmp_path / "common" / "old.txt"),
        str(tmp_path / "common" / "new.txt"),
    ]

    monkeypatch.setattr(
        U.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("git", 1)
        ),
    )
    assert U.get_staged_files(str(tmp_path)) is None


def test_run_validator_main_cli_paths_and_strict(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    captured = {}

    class Validator:
        def __init__(self, mod_path, **kwargs):
            captured["path"] = mod_path
            captured["kwargs"] = kwargs

        def run_all_validations(self):
            return 1

    def extra(parser):
        parser.add_argument("--flavor", default="plain")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validator",
            "--path",
            str(tmp_path),
            "--strict",
            "--no-cache",
            "--flavor",
            "fast",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(Validator, extra_args_fn=extra)
    assert exc.value.code == 1
    assert captured["path"] == str(tmp_path.resolve())
    assert captured["kwargs"]["flavor"] == "fast"
    assert captured["kwargs"]["no_cache"] is True
    assert os.environ["MD_NO_CACHE"] == "1"

    file_path = tmp_path / "not-a-dir"
    _write(file_path, "x")
    monkeypatch.setattr(sys, "argv", ["validator", "--path", str(file_path)])
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(Validator)
    assert exc.value.code == 1

    monkeypatch.setattr(sys, "argv", ["validator", "--path", str(tmp_path / "gone")])
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(Validator)
    assert exc.value.code == 1

    class CleanValidator:
        def __init__(self, *_args, **_kwargs):
            pass

        def run_all_validations(self):
            return 0

    monkeypatch.setattr(sys, "argv", ["validator", "--path", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(CleanValidator)
    assert exc.value.code == 0
