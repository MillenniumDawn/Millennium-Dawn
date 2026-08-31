import io
import json
import os
import pickle
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import disk_cache as cache
import precommit_validate as dispatcher
import pytest
import run_all_validators as suite
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
    standard = U.create_standard_parser("standard")
    parsed = standard.parse_args(
        ["input.txt", "--output", "out.txt", "--backup", "-v", "--no-color"]
    )
    assert parsed.input_file == "input.txt"
    assert parsed.output == "out.txt"
    assert parsed.backup and parsed.verbose and parsed.no_color

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
    assert U.collapse_or_compact(commented) == ["a = { # keep", " b = 1", "}"]
    assert (
        U.convert_root_factor_to_base(["ai_will_do = {\n", " factor = 2\n", "}\n"])[1]
        == " base = 2\n"
    )
    assert (
        U.convert_root_factor_to_base(["ai_will_do = {\n", " base = 2\n", "}\n"])[1]
        == " base = 2\n"
    )


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
    assert U.find_hoi4_install() is None

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
    assert U.blank_quoted_strings('x = "a { b }"\nyes', {4}) == 'x = "a { b }"\nyes'

    assert U.DataCleaner.clear_false_positives({"a": 1, "b": 2}, ("b", "gone")) == {
        "a": 1
    }
    assert U.DataCleaner.clear_false_positives(["a", "b"], ("b",)) == ["a"]
    assert U.DataCleaner.clear_false_positives(["a"], ()) == ["a"]
    assert U.DataCleaner.clear_false_positives("a", ()) is None
    assert U.DataCleaner.clear_false_positives_partial_match(
        {"abc": 1, "x": 2}, ("b",)
    ) == {"x": 2}
    assert U.DataCleaner.clear_false_positives_partial_match(["abc", "x"], ("b",)) == [
        "x"
    ]
    assert U.DataCleaner.clear_false_positives_partial_match("a", ()) is None

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


def test_run_tool_main_success_backup_and_failures(tmp_path, monkeypatch, capsys):
    source = tmp_path / "input.txt"
    destination = tmp_path / "output.txt"
    _write(source, "input")
    seen = {}

    class Tool:
        def __init__(self, verbose=False, use_colors=True):
            seen["ctor"] = (verbose, use_colors)

        def process_file(self, input_file, output_file):
            _write(output_file, Path(input_file).read_text(encoding="utf-8").upper())
            return True

    monkeypatch.setattr(
        U,
        "create_backup",
        lambda filename: seen.setdefault("backup", filename) or "backup",
    )
    U.run_tool_main(
        Tool,
        argv=[str(source), "-o", str(destination), "--backup", "-v", "--no-color"],
    )
    assert destination.read_text(encoding="utf-8") == "INPUT"
    assert seen["ctor"] == (True, False)
    assert seen["backup"] == str(source)
    assert "Processing completed" in capsys.readouterr().err

    class Broken:
        def process_file(self, *_args):
            return False

    with pytest.raises(SystemExit) as exc:
        U.run_tool_main(Broken, argv=[str(source)])
    assert exc.value.code == 1

    with pytest.raises(SystemExit) as exc:
        U.run_tool_main(Broken, argv=[str(tmp_path / "missing.txt")])
    assert exc.value.code == 1

    monkeypatch.setattr(U, "create_backup", lambda _filename: "")
    with pytest.raises(SystemExit) as exc:
        U.run_tool_main(Broken, argv=[str(source), "--backup"])
    assert exc.value.code == 1


def test_run_validator_main_cli_paths_and_strict(tmp_path, monkeypatch):
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


def test_dispatcher_spec_discovery_and_run_timeout(tmp_path, monkeypatch):
    spec = dispatcher._Spec("stub", [("events/", ".txt")], exclude=r"skip")
    assert spec.matches(["events/ok.txt"])
    assert not spec.matches(["events/skip.txt"])
    assert not spec.matches(["common/ok.yml"])

    monkeypatch.setattr(
        U,
        "get_staged_files",
        lambda mod_path, extensions, include_missing: [
            os.path.join(mod_path, "events", "staged.txt")
        ],
    )
    assert dispatcher._discover_staged(str(tmp_path), []) == ["events/staged.txt"]
    passed = str(tmp_path / "events" / "passed.txt")
    assert dispatcher._discover_staged(str(tmp_path), [passed]) == [
        "events/passed.txt",
        "events/staged.txt",
    ]

    monkeypatch.setattr(
        dispatcher.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("validator", 1, output=b"out", stderr=b"err")
        ),
    )
    result = dispatcher._run(spec, str(tmp_path), {"PATH": "x"}, True, 2)
    assert result[1] == 124
    assert result[2] == "out"
    assert "TIMED OUT" in result[3]
    assert result[4] >= 0

    monkeypatch.setattr(
        dispatcher.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("validator", 1)
        ),
    )
    result = dispatcher._run(spec, str(tmp_path), {}, False, 1)
    assert result[2] == ""
    assert "TIMED OUT" in result[3]


def test_dispatcher_main_skip_empty_nomatch_and_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MD_SKIP_VALIDATE", "1")
    monkeypatch.setattr(sys, "argv", ["precommit", "--path", str(tmp_path)])
    assert dispatcher.main() == 0
    assert "skipping" in capsys.readouterr().out
    monkeypatch.delenv("MD_SKIP_VALIDATE")

    monkeypatch.setattr(dispatcher, "_discover_staged", lambda *_args: [])
    assert dispatcher.main() == 0
    assert "nothing to validate" in capsys.readouterr().out

    monkeypatch.setattr(
        dispatcher, "_discover_staged", lambda *_args: ["Changelog.txt"]
    )
    assert dispatcher.main() == 0
    assert "match" in capsys.readouterr().out

    spec = dispatcher._Spec("stub", [("events/", ".txt")])
    monkeypatch.setattr(dispatcher, "_REGISTRY", [spec])
    monkeypatch.setattr(dispatcher, "_discover_staged", lambda *_args: ["events/x.txt"])
    monkeypatch.setattr(dispatcher, "split_cpu_budget", lambda tasks: (1, 2))
    monkeypatch.setattr(
        dispatcher, "_run", lambda *_args: ("stub", 1, "stdout", "stderr", 0.1)
    )
    assert dispatcher.main() == 1
    output = capsys.readouterr().out
    assert "stdout" in output and "stderr" in output and "commit blocked" in output


def test_cache_corruption_and_file_cache_lifecycle(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    source = tmp_path / "source.txt"
    _write(source, "one")
    calls = []

    def compute():
        calls.append(len(calls))
        return {"value": len(calls)}

    assert cache.per_file_cached(str(tmp_path), "test", str(source), compute) == {
        "value": 1
    }
    assert cache.per_file_cached(str(tmp_path), "test", str(source), compute) == {
        "value": 1
    }
    assert calls == [0]

    conn = cache._connect(str(tmp_path))
    assert conn is not None
    conn.execute(
        "UPDATE entries SET value = ? WHERE namespace = ? AND key = ?",
        (b"corrupt", "test", str(source)),
    )
    assert cache.per_file_cached(str(tmp_path), "test", str(source), compute) == {
        "value": 2
    }

    missing = tmp_path / "missing.txt"
    assert cache.per_file_cached(str(tmp_path), "missing", str(missing), compute) == {
        "value": 3
    }
    _write(source, "two")
    assert cache.per_file_cached_by_content(
        str(tmp_path), "content", str(source), "body", compute
    ) == {"value": 4}
    assert cache.per_file_cached_by_content(
        str(tmp_path), "content", str(source), "body", compute
    ) == {"value": 4}
    assert calls == [0, 1, 2, 3]

    assert cache._file_stat(str(missing)) is None
    assert cache._stats_tag({"missing": None, "source": (1, 2)}, "test").startswith(
        "a:"
    )
    monkeypatch.setenv("MD_NO_CACHE", "1")
    assert cache.per_file_cached_by_content(
        str(tmp_path), "disabled", "x", "body", compute
    ) == {"value": 5}
    monkeypatch.delenv("MD_NO_CACHE")


def test_cache_put_errors_aggregate_and_version_pruning(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)

    class Unpicklable:
        def __reduce__(self):
            raise pickle.PicklingError("no pickle")

    cache._put(str(tmp_path), "errors", "key", "tag", Unpicklable())
    assert cache._get(str(tmp_path), "errors", "key", "tag") == (False, None)
    assert cache._get(str(tmp_path), "errors", "key", "other") == (False, None)

    one = tmp_path / "one.txt"
    _write(one, "one")
    values = []
    assert (
        cache.aggregate_cached(
            str(tmp_path), "aggregate", [str(one)], lambda: values.append(1) or "result"
        )
        == "result"
    )
    assert (
        cache.aggregate_cached(
            str(tmp_path), "aggregate", [str(one)], lambda: values.append(1) or "new"
        )
        == "result"
    )
    _write(one, "changed")
    assert (
        cache.aggregate_cached(
            str(tmp_path),
            "aggregate",
            [str(one)],
            lambda: values.append(1) or "changed",
        )
        == "changed"
    )
    assert values == [1, 1]

    root = tmp_path / ".validation_cache"
    (root / "v1").mkdir(parents=True)
    (root / f"v{cache.CACHE_VERSION}").mkdir(exist_ok=True)
    (root / "not-a-version").mkdir()
    assert cache.prune_old_versions(str(tmp_path)) == ["v1"]
    assert not (root / "v1").exists()
    assert (root / f"v{cache.CACHE_VERSION}").exists()
    assert cache.prune_old_versions(str(tmp_path)) == []


def test_cache_marker_stale_clear_and_corrupt_marker(tmp_path):
    assert cache.cache_age_days(str(tmp_path)) is None
    assert not cache.clear_if_stale(str(tmp_path), 0)
    assert not cache.clear_if_stale(str(tmp_path), 1)
    marker = cache._marker_path(str(tmp_path))
    assert marker.exists()
    first = marker.read_text(encoding="utf-8")
    cache.stamp_created(str(tmp_path))
    assert marker.read_text(encoding="utf-8") == first
    age = cache.cache_age_days(str(tmp_path))
    assert age is not None
    assert age >= 0

    _write(tmp_path / ".validation_cache" / "v1" / "old", "old")
    _write(marker, "not-a-time")
    assert cache.cache_age_days(str(tmp_path)) is None
    assert not cache.clear_if_stale(str(tmp_path), 1)
    _write(marker, "0")
    assert cache.clear_if_stale(str(tmp_path), 1)
    assert marker.exists()
    age = cache.cache_age_days(str(tmp_path))
    assert age is not None
    assert age < 1

    cache.clear(str(tmp_path))
    assert not (tmp_path / ".validation_cache").exists()
    cache.clear(str(tmp_path))


def test_cache_connect_failure_is_opportunistic(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cache.sqlite3,
        "connect",
        lambda *args, **kwargs: (_ for _ in ()).throw(sqlite3_error()),
    )
    assert cache._connect(str(tmp_path)) is None
    assert cache._get(str(tmp_path), "ns", "key", "tag") == (False, None)


def sqlite3_error():
    return sqlite3.OperationalError("unavailable")


def test_validator_labels_discovery_and_launch(tmp_path, monkeypatch):
    title = tmp_path / "validate_title.py"
    class_script = tmp_path / "validate_class.py"
    fallback = tmp_path / "validate_fallback.py"
    _write(title, 'TITLE = "TITLE VALIDATION"\n')
    _write(class_script, "class ExampleValidator(Base):\n    pass\n")
    _write(fallback, "# no metadata\n")
    assert suite._extract_label_from_script(str(title), "title") == "TITLE"
    assert (
        suite._extract_label_from_script(str(class_script), "class-name") == "Example"
    )
    assert (
        suite._extract_label_from_script(str(fallback), "fallback-name")
        == "Fallback Name"
    )
    assert (
        suite._extract_label_from_script(str(tmp_path / "gone.py"), "gone-name")
        == "Gone Name"
    )

    monkeypatch.setattr(suite, "SCRIPTS_DIR", str(tmp_path))
    monkeypatch.setattr(
        suite.glob,
        "glob",
        lambda pattern: [
            str(title),
            str(class_script),
            str(fallback),
            str(tmp_path / "validate_tools.py"),
        ],
    )
    discovered = suite.discover_validators()
    assert [name for name, _script, _label in discovered] == [
        "class",
        "fallback",
        "title",
    ]

    output_dir = tmp_path / "out"
    output_dir.mkdir()
    captured = {}

    class Process:
        pass

    def popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return Process()

    monkeypatch.setattr(suite.subprocess, "Popen", popen)
    process, stderr = suite.launch_validator(
        "validate_title.py",
        ["--missing-icons", "--missing-icons"],
        str(output_dir),
        "focus-tree",
        str(tmp_path),
    )
    stderr.close()
    assert isinstance(process, Process)
    assert captured["command"].count("--missing-icons") == 1
    assert captured["kwargs"]["stderr"].closed


def test_validator_launch_failure_counts_and_stderr(tmp_path, monkeypatch, capsys):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    monkeypatch.setattr(
        suite.subprocess,
        "Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("cannot launch")),
    )
    with pytest.raises(OSError, match="cannot launch"):
        suite.launch_validator(
            "validate.py", [], str(output_dir), "broken", str(tmp_path)
        )

    _write(
        output_dir / "valid.json",
        json.dumps(
            [{"severity": "error"}, {"severity": "warning"}, {"severity": "info"}]
        ),
    )
    assert suite.read_validator_counts(str(output_dir), "valid") == (1, 1)
    _write(output_dir / "bad.json", "not json")
    assert suite.read_validator_counts(str(output_dir), "bad") == (0, 0)
    assert suite.read_validator_counts(str(output_dir), "missing") == (0, 0)

    _write(output_dir / "broken.stderr.log", "one\ntwo\nthree\n")
    suite._print_stderr_tail(str(output_dir), "broken", max_lines=2)
    assert "two" in capsys.readouterr().out
    suite._print_stderr_tail(str(output_dir), "missing")
    assert suite._issue_sort_key({"line": "bad", "file": "x"})[:2] == ("x", 0)


def test_reports_format_issues_and_persistence(tmp_path):
    issue = {
        "severity": "error",
        "category": "cat",
        "message": "bad",
        "file": "a.txt",
        "line": 2,
    }
    warning = {
        "severity": "warning",
        "category": "warn",
        "message": "care",
        "file": "b.txt",
        "line": 0,
    }
    _write(tmp_path / "one.json", json.dumps([issue, warning]))
    validators = [("one", "one.py", "One")]
    report = suite.generate_combined_report(
        str(tmp_path), validators, ["Crashed"], use_colors=False
    )
    assert "1 ERROR(S)" in report and "1 WARNING(S)" in report and "Crashed" in report
    lines = []
    suite._format_issues_by_file([issue, warning], lines)
    assert "a.txt:2" in "\n".join(lines)
    assert "ALL VALIDATIONS PASSED" in suite.generate_combined_report(
        str(tmp_path / "empty"), [], []
    )
    _write(tmp_path / "shape.json", json.dumps({"issue": issue}))
    with pytest.raises(ValueError, match="Malformed validator sidecar"):
        suite.collect_all_issues(str(tmp_path), [("shape", "shape.py", "Shape")])

    persist = tmp_path / "persist"
    persist.mkdir()
    _write(persist / "stale.json", "[]")
    _write(persist / suite.PERSISTENCE_MARKER, "old\n")
    suite._persist_sidecars(str(tmp_path), str(persist))
    assert json.loads((persist / "one.json").read_text(encoding="utf-8")) == [
        issue,
        warning,
    ]
    assert (persist / suite.PERSISTENCE_MARKER).read_text(
        encoding="utf-8"
    ) == "complete\n"


def test_suite_scheduling_reports_crash_and_main_cli(tmp_path, monkeypatch, capsys):
    validators = [("first", "first.py", "First"), ("second", "second.py", "Second")]
    monkeypatch.setattr(suite, "split_cpu_budget", lambda tasks: (1, 1))

    def launch(_script, _flags, output_dir, name, _mod_path):
        _write(Path(output_dir) / f"{name}.stderr.log", "traceback\nlast line\n")
        return SimpleNamespace(returncode=3, wait=lambda: 3), io.StringIO()

    monkeypatch.setattr(suite, "launch_validator", launch)
    args = SimpleNamespace(
        format="text", output=None, strict=False, no_color=True, persist_results=None
    )
    assert (
        suite._run_suite(args, [], str(tmp_path / "out"), validators, str(tmp_path))
        == 1
    )
    assert "crashed" in capsys.readouterr().out

    calls = []
    monkeypatch.setattr(suite, "discover_validators", lambda: validators)
    monkeypatch.setattr(
        suite.disk_cache, "clear", lambda path: calls.append(("clear", path))
    )
    monkeypatch.setattr(
        suite.disk_cache, "stamp_created", lambda path: calls.append(("stamp", path))
    )
    monkeypatch.setattr(
        suite.disk_cache,
        "clear_if_stale",
        lambda path, age: calls.append(("stale", age)) or False,
    )
    monkeypatch.setattr(suite.disk_cache, "prune_old_versions", lambda path: ["v1"])
    monkeypatch.setattr(
        suite, "_run_suite", lambda *args: calls.append(("run", args[1])) or 0
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner",
            "--path",
            str(tmp_path),
            "--clear-cache",
            "--no-cache",
            "--staged",
            "--strict",
            "--no-color",
            "--format",
            "json",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        suite.main()
    assert exc.value.code == 0
    assert ("clear", str(tmp_path)) in calls
    assert ("stamp", str(tmp_path)) in calls
    assert ("run", ["--staged", "--strict", "--no-color"]) in calls
    assert os.environ["MD_NO_CACHE"] == "1"

    monkeypatch.delenv("MD_NO_CACHE")
    calls.clear()
    monkeypatch.setattr(
        suite.disk_cache,
        "clear_if_stale",
        lambda path, age: calls.append(("stale", age)) or True,
    )
    monkeypatch.setattr(
        sys, "argv", ["runner", "--path", str(tmp_path), "--cache-max-age-days", "2"]
    )
    with pytest.raises(SystemExit) as exc:
        suite.main()
    assert exc.value.code == 0
    assert any(call[0] == "stale" for call in calls)
    assert "Pruned stale" in capsys.readouterr().out
