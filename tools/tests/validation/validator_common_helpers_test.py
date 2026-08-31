"""Tests for the shared helpers and BaseValidator plumbing in validator_common."""

import importlib.util
import logging

import pytest
import validator_common as VC


class _Dummy(VC.BaseValidator):
    TITLE = "DUMMY"

    def run_validations(self):
        pass


@pytest.fixture
def dummy(tmp_path):
    return _Dummy(mod_path=str(tmp_path), use_colors=False, workers=1)


def test_mod_path_already_terminated_is_left_alone(tmp_path):
    v = _Dummy(mod_path=str(tmp_path) + "/", use_colors=False, workers=1)
    assert v.mod_path == str(tmp_path) + "/"


def test_report_tuple_with_unparsable_line_falls_back_to_zero(dummy):
    dummy._report([("finding", "a.txt", "not-a-number")], "OK", "Findings:")
    assert dummy._issues[0].line == 0


# ---- brace walking --------------------------------------------------------


def test_child_blocks_finds_direct_children():
    text = "root = {\n\tone = { a = 1 }\n\ttwo = { b = 2 }\n}\n"
    body_start = text.index("{") + 1
    names = [n for n, _s, _b, _e in VC._child_blocks(text, body_start, len(text))]
    assert names == ["one", "two"]


def test_child_blocks_stops_on_unbalanced_block():
    text = "root = { child = { a = 1 "
    assert VC._child_blocks(text, 0, len(text)) == []


def test_child_blocks_ignores_a_block_running_past_the_end():
    text = "one = { a = 1 } two = { b = 2 }"
    end = text.index("two")
    names = [n for n, _s, _b, _e in VC._child_blocks(text, 0, end)]
    assert names == ["one"]


def test_child_blocks_on_empty_span():
    assert VC._child_blocks("a = { }", 3, 3) == []


def test_match_brace_returns_minus_one_when_unclosed():
    assert VC._match_brace("{ a = 1", 0) == -1


# ---- leader trait parsing -------------------------------------------------


def test_parse_leader_trait_names_reads_only_txt_files(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/country_leader/traits.txt",
        "leader_traits = {\n\temerging_Communist-State = {\n\t}\n}\n",
    )
    write_path(
        tmp_path,
        "common/country_leader/notes.md",
        "leader_traits = {\n\tnot_a_trait = {\n\t}\n}\n",
    )

    names = VC.parse_leader_trait_names(str(tmp_path), "country_leader")

    assert names == {"emerging_Communist-State"}


def test_parse_leader_trait_names_survives_an_unreadable_dir(tmp_path, monkeypatch):
    (tmp_path / "common" / "unit_leader").mkdir(parents=True)
    monkeypatch.setattr(
        VC.os, "listdir", lambda path: (_ for _ in ()).throw(OSError("denied"))
    )

    assert VC.parse_leader_trait_names(str(tmp_path), "unit_leader") == set()


def test_parse_leader_trait_names_missing_dir(tmp_path):
    assert VC.parse_leader_trait_names(str(tmp_path), "country_leader") == set()


# ---- meta template scanning -----------------------------------------------


def test_scan_meta_constructed_names_skips_unreadable_files(tmp_path, write_path):
    live = write_path(
        tmp_path, "meta.txt", "meta_effect = {\n\tset_leader_[IDEOLOGY] = yes\n}\n"
    )
    files = [str(tmp_path / "gone.txt"), str(live)]

    assert VC.scan_meta_constructed_names(files, {"set_leader_democratic"}) == {
        "set_leader_democratic"
    }


def test_scan_meta_constructed_names_ignores_anchorless_templates(tmp_path, write_path):
    path = write_path(
        tmp_path,
        "meta.txt",
        'meta_effect = {\n\ttext = "[ANY]"\n}\n',
    )

    assert (
        VC.scan_meta_constructed_names([str(path)], {"set_leader_democratic"}) == set()
    )


def test_scan_meta_constructed_names_reports_each_name_once(tmp_path, write_path):
    path = write_path(
        tmp_path,
        "meta.txt",
        "meta_effect = {\n"
        "\tset_leader_[IDEOLOGY] = yes\n"
        "\tset_leader_[PARTY] = yes\n"
        "}\n",
    )

    names = {"set_leader_democratic", "set_leader_communist"}
    assert VC.scan_meta_constructed_names([str(path)], names) == names


def test_scan_meta_constructed_names_needs_a_substituted_segment(tmp_path, write_path):
    """`set_leader_[X]` must not claim the bare name `set_leader_` itself — the
    placeholder always expands to at least one character."""
    path = write_path(
        tmp_path,
        "meta.txt",
        "meta_effect = {\n\tset_leader_[IDEOLOGY] = yes\n}\n",
    )

    assert VC.scan_meta_constructed_names([str(path)], {"set_leader_"}) == set()


# ---- logging --------------------------------------------------------------


@pytest.mark.parametrize("level", ["ERROR", "INFO", "WARNING"])
def test_md_log_level_env_var_sets_the_module_threshold(monkeypatch, level):
    """The threshold is read at import, so it is env-driven, not settable later."""
    monkeypatch.setenv("MD_LOG_LEVEL", level.lower())
    spec = importlib.util.spec_from_file_location("validator_common_probe", VC.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._LOG_LEVEL == level


def test_warning_is_suppressed_at_error_log_level(dummy, monkeypatch, caplog):
    monkeypatch.setattr(VC, "_LOG_LEVEL", "ERROR")
    with caplog.at_level(logging.WARNING):
        dummy.log("a warning", "warning")
    assert caplog.text == ""
    assert dummy.output_lines == []


def test_info_reaches_the_log_at_info_level(dummy, monkeypatch, caplog):
    monkeypatch.setattr(VC, "_LOG_LEVEL", "INFO")
    with caplog.at_level(logging.INFO):
        dummy.log("progress", "info")
    assert "progress" in caplog.text
    assert dummy.output_lines == ["progress"]


def test_error_level_is_logged_and_recorded(dummy, caplog):
    with caplog.at_level(logging.ERROR):
        dummy.log("\033[91mboom\033[0m", "error")
    assert "boom" in caplog.text
    assert dummy.output_lines == ["boom"]


def test_log_section_without_timing_prints_nothing(dummy, capsys):
    dummy._show_timing = False
    dummy._log_section("first")
    dummy._log_section("second")
    dummy._finish_sections()
    assert capsys.readouterr().err == ""
    assert [title for title, _elapsed in dummy._section_timings] == ["first", "second"]


# ---- issue bookkeeping ----------------------------------------------------


def test_unknown_severity_counts_as_neither_error_nor_warning(dummy):
    dummy.add_issue("notice", "cat", "just so you know", "a.txt", 2)
    assert dummy.errors_found == 0
    assert dummy.warnings_found == 0
    assert dummy._issues[0].severity == "notice"


# ---- file indexes ---------------------------------------------------------


def test_basename_index_is_memoized(dummy, write_path, tmp_path):
    write_path(tmp_path, "common/a.txt", "x")
    first = dummy._basename_index(("**/*.txt",))
    write_path(tmp_path, "common/b.txt", "y")
    assert dummy._basename_index(("**/*.txt",)) is first


def test_basename_index_dedupes_overlapping_patterns(dummy, write_path, tmp_path):
    write_path(tmp_path, "common/a.txt", "x")
    index = dummy._basename_index(("**/*.txt", "common/*.txt"))
    assert len(index["a.txt"]) == 1


def test_basename_index_skips_ignored_paths(dummy, write_path, tmp_path):
    write_path(tmp_path, "docs/skipped.txt", "x")
    write_path(tmp_path, "common/kept.txt", "y")
    assert sorted(dummy._basename_index(("**/*.txt",))) == ["kept.txt"]


def test_get_full_path_finds_the_file_holding_the_item(dummy, write_path, tmp_path):
    write_path(tmp_path, "common/one/shared.txt", "wanted_item = yes\n")

    hit = dummy.get_full_path("shared.txt", "wanted_item")

    assert hit is not None
    assert hit.endswith("one/shared.txt")


def test_get_full_path_returns_none_when_no_candidate_has_the_item(
    dummy, write_path, tmp_path
):
    write_path(tmp_path, "common/one/shared.txt", "nothing here\n")
    write_path(tmp_path, "common/two/shared.txt", "nothing here either\n")

    assert dummy.get_full_path("shared.txt", "wanted_item") is None


def test_get_full_path_returns_none_when_unreadable(dummy, tmp_path):
    (tmp_path / "common" / "trap.txt").mkdir(parents=True)
    assert dummy.get_full_path("trap.txt", "anything") is None


# ---- file collection ------------------------------------------------------


def test_collect_files_staged_with_nothing_staged(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_STAGED_FILES", "")
    v = _Dummy(mod_path=str(tmp_path), use_colors=False, staged_only=True, workers=1)
    assert v._collect_files(["common/**/*.txt"]) == []


def test_collect_files_dedupes_overlapping_patterns(dummy, write_path, tmp_path):
    write_path(tmp_path, "common/a.txt", "x")
    files = dummy._collect_files(["common/*.txt", "**/*.txt"])
    assert len(files) == 1


def test_pool_map_falls_back_to_sequential_without_a_pool(tmp_path, monkeypatch):
    v = _Dummy(mod_path=str(tmp_path), use_colors=False, workers=2)
    monkeypatch.setattr(v, "_get_pool", lambda: None)
    assert v._pool_map(str, list(range(12))) == [str(i) for i in range(12)]


# ---- localisation keys ----------------------------------------------------


def test_localisation_loader_skips_unreadable_yml(dummy, write_path, tmp_path):
    write_path(
        tmp_path, "localisation/english/good_l_english.yml", 'l_english:\n k: "v"\n'
    )
    (tmp_path / "localisation" / "english" / "broken_l_english.yml").mkdir()

    keys = dummy._load_localisation_keys()

    assert "k" in keys
    assert "recruit_in_europe" in keys


# ---- run wiring -----------------------------------------------------------


def test_base_run_validations_is_abstract(tmp_path):
    with pytest.raises(NotImplementedError):
        VC.BaseValidator(str(tmp_path)).run_validations()


def test_run_all_validations_writes_the_output_file_and_sidecar(tmp_path):
    class _Failing(VC.BaseValidator):
        TITLE = "FAILING"

        def run_validations(self):
            self.add_error("cat", "broken", "a.txt", 7)

    out = tmp_path / "out.log"
    v = _Failing(mod_path=str(tmp_path), output_file=str(out), use_colors=False)
    assert v.run_all_validations() == 1

    log_text = out.read_text(encoding="utf-8")
    assert f"Output file: {out}" in log_text
    assert "a.txt:7 - broken" in log_text
    assert "1 ERROR(S) in 1 file" in log_text
    assert '"category": "cat"' in (tmp_path / "out.json").read_text(encoding="utf-8")
