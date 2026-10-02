"""Behavior tests for the set_variable usage validator.

Pass 1 collects every variable-writing effect's target; pass 2 counts reads
across .txt, English .yml and .gui and reports the targets nothing reads.
"""

import argparse
import runpy
import sys

import pytest
import validate_set_variables
from shared.suite import write_under as _write
from validate_set_variables import (
    _DYNAMIC_REF_RE,
    SetVariables,
    Validator,
    _count_refs_in_text,
    _dynamic_ref_pattern,
    _dynamic_refs,
    _pass2_init,
    _resolve_mod_root,
    _scan_set_variables,
    _strip_scope_prefix,
    add_extra_args,
    count_all_variables_in_file,
    process_file_for_set_variables,
)

SETTERS = """setup_effect = {
\tset_variable = { TAG_used_var = 1 }
\tset_variable = { TAG_dead_var = 2 }
\tset_variable = { TAG_dyn_0_var = 3 }
\tset_variable = { global.TAG_global_var = 4 }
\tadd_to_variable = { TAG_gui_var = 1 }
\tadd_to_variable = { TAG_loc_var = 1 }
}
"""

READERS = """read_effect = {
\tcheck_variable = { TAG_used_var > 0 }
\tcheck_variable = { TAG_global_var > 0 }
\tcheck_variable = { var = TAG_dyn_[index]_var value = 1 }
}
"""

LOCALISATION = ' l_english:\n TEST_key:0 "Fuel: [?TAG_loc_var|0]"\n'

GUI = 'containerWindowType = {\n\ttextType = { text = "[?THIS.TAG_gui_var|0]" }\n}\n'


def _findings(validator):
    return [(issue.message, issue.file, issue.line) for issue in validator._issues]


def test_mod_root_is_found_from_a_subdirectory(tmp_path):
    _write(tmp_path, "descriptor.mod", 'name = "test"\n')
    nested = tmp_path / "common" / "scripted_effects"
    nested.mkdir(parents=True)

    assert _resolve_mod_root(str(nested)) == str(tmp_path)


def test_mod_root_falls_back_to_the_given_path(tmp_path):
    lonely = tmp_path / "no_mod_here"
    lonely.mkdir()

    assert _resolve_mod_root(str(lonely)) == str(lonely)


def test_scope_prefixes_are_stripped_except_global():
    assert _strip_scope_prefix("PREV.foo") == "foo"
    assert _strip_scope_prefix("global.foo") == "global.foo"
    assert _strip_scope_prefix("foo") == "foo"


def test_scan_skips_text_with_no_write_effect():
    assert _scan_set_variables("check_variable = { foo > 0 }\n") == []


def test_scan_keeps_targets_and_drops_reserved_words():
    text = (
        "e = {\n\tset_variable = { foo = 1 }\n\tadd_to_variable = { bar = days }\n}\n"
    )

    assert set(_scan_set_variables(text)) >= {"foo", "bar"}
    assert "days" not in _scan_set_variables(text)


def test_pass_one_skips_ignored_paths(tmp_path):
    ignored = _write(tmp_path, "gfx/notes.txt", SETTERS)

    assert process_file_for_set_variables(str(ignored), False, str(tmp_path)) == (
        [],
        {},
    )


def test_pass_one_maps_each_target_to_its_file(tmp_path):
    path = _write(tmp_path, "common/scripted_effects/vars.txt", SETTERS)

    variables, paths = process_file_for_set_variables(str(path), False, str(tmp_path))

    assert "TAG_dead_var" in variables
    assert paths["TAG_dead_var"] == "vars.txt"


def _counts(text, bare=None, dotted=None):
    _pass2_init("", bare or {}, dotted or {}, "counts.test")
    return _count_refs_in_text(text)


def test_bare_read_satisfies_a_global_namespaced_target():
    counts, patterns = _counts(
        "check_variable = { tag_global_var > 0 }",
        dotted={"global.tag_global_var": "global.TAG_global_var"},
    )

    assert counts == {"global.TAG_global_var": 1}
    assert patterns == set()


def test_namespaced_read_is_consumed_as_one_unit():
    counts, _ = _counts(
        "check_variable = { global.tag_global_var > 0 }",
        bare={"tag_global_var": "TAG_global_var"},
        dotted={"global.tag_global_var": "global.TAG_global_var"},
    )

    assert counts == {"global.TAG_global_var": 1}


def test_unknown_global_chain_still_counts_its_tail_segment():
    counts, _ = _counts(
        "log = global.tag_other_var", bare={"tag_other_var": "TAG_other_var"}
    )

    assert counts == {"TAG_other_var": 1}


def test_scoped_read_counts_against_the_bare_target():
    counts, _ = _counts("this.tag_gui_var", bare={"tag_gui_var": "TAG_gui_var"})

    assert counts == {"TAG_gui_var": 1}


def test_write_target_is_not_counted_as_a_read():
    counts, _ = _counts("set_variable = { tag_x = 1 }", bare={"tag_x": "TAG_x"})

    assert counts == {}


def test_dynamic_reference_patterns_need_a_literal_anchor():
    _, patterns = _counts("tag_dyn_[index]_var and [getname]")

    assert patterns == {r"^tag_dyn_\w+_var$"}


@pytest.mark.parametrize(
    ("text", "refs"),
    [
        ("a[x]b:c[y]", ["a[x]b", ":c[y]"]),
        ("ab[ cd[x]", ["cd[x]"]),
        ("[[x]]", ["[[x]"]),
        ("x..y[z].w", ["x..y[z].w"]),
        ("ökosteuer_[i]_var", ["ökosteuer_[i]_var"]),
        ("a_[x]_b_[y]_c", ["a_[x]_b_", "[y]_c"]),
        ("tail [open", []),
        ("[]", []),
        ("set = { foo_[i] }\r\nbar.[j]", ["foo_[i]", "bar.[j]"]),
    ],
)
def test_dynamic_refs_match_a_full_regex_scan(text, refs):
    assert list(_dynamic_refs(text)) == refs
    assert refs == [m.group() for m in _DYNAMIC_REF_RE.finditer(text)]


def test_dynamic_pattern_strips_a_scope_prefix_but_keeps_the_global_namespace():
    assert _dynamic_ref_pattern("this.foo_[i]") == r"^foo_\w+$"
    assert _dynamic_ref_pattern("global.foo_[i]") == r"^global\.foo_\w+$"
    assert _dynamic_ref_pattern("[getname]") is None


def test_reference_counting_skips_ignored_and_empty_files(tmp_path):
    _pass2_init(str(tmp_path), {"tag_x": "TAG_x"}, {}, "counts.file.test")
    ignored = _write(tmp_path, "gfx/notes.txt", "check_variable = { TAG_x > 0 }\n")
    empty = _write(tmp_path, "common/empty.txt", "")
    live = _write(tmp_path, "common/live.txt", "check_variable = { TAG_x > 0 }\n")

    assert count_all_variables_in_file(str(ignored)) == ({}, set())
    assert count_all_variables_in_file(str(empty)) == ({}, set())
    assert count_all_variables_in_file(str(live)) == ({"TAG_x": 1}, set())


class _RecordingPool:
    """Stand-in for a caller-owned pool; records that it was reused."""

    def __init__(self):
        self.calls = 0

    def map(self, func, items, chunksize=None):
        self.calls += 1
        return [func(item) for item in items]


def test_caller_supplied_pool_is_reused_for_pass_one(tmp_path):
    _write(tmp_path, "common/scripted_effects/vars.txt", SETTERS)
    pool = _RecordingPool()

    variables = SetVariables.get_all_set_variables(str(tmp_path), pool=pool)

    assert pool.calls == 1
    assert "tag_dead_var" in variables


def test_pass_one_runs_across_worker_processes(tmp_path):
    _write(tmp_path, "common/scripted_effects/vars.txt", SETTERS)

    variables = SetVariables.get_all_set_variables(
        str(tmp_path), lowercase=False, workers=2
    )

    assert "TAG_dead_var" in variables


def _mod_with_variables(tmp_path):
    _write(tmp_path, "common/scripted_effects/vars.txt", SETTERS)
    _write(tmp_path, "common/scripted_effects/reads.txt", READERS)
    _write(tmp_path, "localisation/english/MD_test_l_english.yml", LOCALISATION)
    _write(tmp_path, "interface/test.gui", GUI)
    return Validator(str(tmp_path), use_colors=False, workers=1)


def test_only_the_unread_variable_is_reported(tmp_path):
    validator = _mod_with_variables(tmp_path)

    validator.run_validations()

    # TAG_dyn_0_var has no literal read either, but a `TAG_dyn_[index]_var`
    # reference builds its name at runtime, so it is not dead.
    assert _findings(validator) == [
        ("TAG_dead_var (refs: 0)", "common/scripted_effects/vars.txt", 3)
    ]
    assert validator.errors_found == 1


def test_one_worker_run_collects_targets_in_process(tmp_path, monkeypatch):
    def no_pool(*_args, **_kwargs):
        raise AssertionError("one worker must not start a pool")

    monkeypatch.setattr(validate_set_variables, "Pool", no_pool)
    validator = _mod_with_variables(tmp_path)

    validator.run_validations()

    assert _findings(validator) == [
        ("TAG_dead_var (refs: 0)", "common/scripted_effects/vars.txt", 3)
    ]


EDGE_SETTERS = """setup_effect = {
\tset_variable = { TAG_first_var = 1 }
\tset_variable = { TAG_slot_3_var = 1 }
\tset_variable = { TAG_commented_var = 1 }
\tset_variable = { TAG_quoted_var = 1 }
\tset_variable = { TAG_dotted_var = 1 }
\tset_variable = { TAG_longer_var = 1 }
}
"""

EDGE_READERS = (
    "check_variable = { TAG_first_var > 0 }\r\n"
    "# check_variable = { TAG_commented_var > 0 }\r\n"
    'log = "[THIS.TAG_dotted_var]"\r\n'
    "check_variable = { TAG_longer_var_2 > 0 }\r\n"
    "check_variable = { var = TAG_slot_[index]_var value = 1 }"
)


def test_reads_on_edge_lines_and_in_quotes_count_but_comments_do_not(tmp_path):
    _write(tmp_path, "common/scripted_effects/vars.txt", EDGE_SETTERS)
    _write(tmp_path, "common/scripted_effects/reads.txt", EDGE_READERS)
    _write(
        tmp_path,
        "localisation/english/MD_test_l_english.yml",
        ' l_english:\n TEST_key:0 "50# {[?TAG_quoted_var|0]"\n',
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert _findings(validator) == [
        ("TAG_commented_var (refs: 0)", "common/scripted_effects/vars.txt", 4),
        ("TAG_longer_var (refs: 0)", "common/scripted_effects/vars.txt", 7),
    ]


def test_pooled_reference_scan_matches_the_in_process_scan(
    tmp_path, monkeypatch, pool_sizes
):
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    setters = "".join(
        f"\tset_variable = {{ TAG_v{index:02}_var = 1 }}\n" for index in range(12)
    )
    _write(tmp_path, "common/scripted_effects/vars.txt", f"e = {{\n{setters}}}\n")
    for index in range(0, 12, 2):
        _write(
            tmp_path,
            f"common/scripted_effects/read{index:02}.txt",
            f"check_variable = {{ TAG_v{index:02}_var > 0 }}\n",
        )
    for index in range(6):
        _write(tmp_path, f"events/filler{index}.txt", "e = { log = filler }\n")

    def run(workers):
        validator = Validator(str(tmp_path), use_colors=False, workers=workers)
        validator.run_all_validations()
        return _findings(validator)

    pooled = run(2)
    assert pool_sizes == [2, 2]
    assert (
        pooled
        == run(1)
        == [
            (
                f"TAG_v{index:02}_var (refs: 0)",
                "common/scripted_effects/vars.txt",
                index + 2,
            )
            for index in range(1, 12, 2)
        ]
    )


def test_min_refs_widens_the_report_to_thinly_used_variables(tmp_path):
    _write(tmp_path, "common/scripted_effects/vars.txt", SETTERS)
    _write(tmp_path, "common/scripted_effects/reads.txt", READERS)
    _write(tmp_path, "localisation/english/MD_test_l_english.yml", LOCALISATION)
    _write(tmp_path, "interface/test.gui", GUI)
    validator = Validator(str(tmp_path), min_refs=1, use_colors=False, workers=1)

    validator.run_validations()

    # Localisation and scripted-GUI reads are the only references to
    # TAG_loc_var and TAG_gui_var, so both scans have to count.
    assert [issue.message for issue in validator._issues] == [
        "TAG_dead_var (refs: 0)",
        "TAG_gui_var (refs: 1)",
        "TAG_loc_var (refs: 1)",
        "TAG_used_var (refs: 1)",
        "global.TAG_global_var (refs: 1)",
    ]


def test_variable_set_outside_the_mod_root_is_keyed_by_basename(tmp_path):
    outside = _write(
        tmp_path / "outside",
        "x.txt",
        "e = {\n\tset_variable = { TAG_orphan_var = 1 }\n}\n",
    )
    mod = tmp_path / "mod"
    (mod / "common").mkdir(parents=True)
    (mod / "localisation").mkdir()
    validator = Validator(str(mod), use_colors=False, workers=1)
    validator.staged_files = [str(outside)]

    validator.run_validations()

    assert _findings(validator) == [("TAG_orphan_var (refs: 0)", "x.txt", 0)]


def test_min_refs_argument_is_exposed_on_the_cli():
    parser = argparse.ArgumentParser()
    add_extra_args(parser)

    assert parser.parse_args([]).min_refs == 0
    assert parser.parse_args(["--min-refs", "2"]).min_refs == 2


def test_script_entry_point_exits_nonzero_under_strict(tmp_path, monkeypatch):
    _mod_with_variables(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            validate_set_variables.__file__,
            "--path",
            str(tmp_path),
            "--strict",
            "--workers",
            "1",
            "--no-color",
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(validate_set_variables.__file__, run_name="__main__")

    assert exit_info.value.code == 1
