"""Reporting tests for validate_focus_tree's structural checks.

Covers duplicate IDs, orphan focuses, missing prerequisite targets, missing
localisation, focus icons, the cross-country aggregate, and the staged-mode
reporting scope (findings in unstaged files must stay out of a commit run).
"""

import argparse
import os

import validate_focus_tree as V
from shared.suite import write_under_str as _write


def _focus_file(tmp_path, body, name="test.txt"):
    return _write(tmp_path, f"common/national_focus/{name}", body)


def _validator(tmp_path, **kwargs):
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)


def _messages(validator):
    return [i.message for i in validator._issues]


def _sprite_index(*names):
    return frozenset({f"GFX_filler_{i}" for i in range(1000)} | set(names))


# ---------------------------------------------------------------------------
# Duplicate focus IDs
# ---------------------------------------------------------------------------


DUPLICATE_TREES = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
\tfocus = { id = TAG_focus_unique x = 2 y = 0 cost = 1 }
}
focus_tree = {
\tid = tree_b
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
}
"""


def test_duplicate_focus_id_lists_every_definition(tmp_path):
    _focus_file(tmp_path, DUPLICATE_TREES)
    v = _validator(tmp_path)
    v.validate_duplicate_focus_ids()

    focus_path = os.path.join("common", "national_focus", "test.txt")
    assert _messages(v) == [
        f"Duplicate focus ID 'TAG_focus_a' defined 2 times:"
        f" {focus_path}:3, {focus_path}:8"
    ]
    assert v._issues[0].line == 3
    assert v._issues[0].category == "duplicate-focus-id"


def test_registry_keeps_the_first_definition_of_a_shared_focus(tmp_path):
    """A shared focus redefined in another file is listed twice for the
    duplicate check but resolves to its first definition everywhere else."""
    parsed = [
        {
            "filepath": "a.txt",
            "shared_defs": {"TAG_shared_s": {"line": 1, "prereq_groups": [["P"]]}},
            "trees": [],
        },
        {
            "filepath": "b.txt",
            "shared_defs": {"TAG_shared_s": {"line": 9, "prereq_groups": []}},
            "trees": [],
        },
    ]
    all_focuses, focus_info = _validator(tmp_path)._build_focus_registry(parsed)

    assert all_focuses["TAG_shared_s"] == [("a.txt", 1), ("b.txt", 9)]
    assert focus_info["TAG_shared_s"] == ("a.txt", 1, [["P"]])


def test_duplicate_focus_id_collapses_to_one_graph_node(tmp_path):
    """The cycle graph registers each ID once; a redefinition must not reset
    the node it already recorded."""
    _focus_file(tmp_path, DUPLICATE_TREES)
    v = _validator(tmp_path)
    v.validate_dependency_cycles()
    assert v._issues == []


# ---------------------------------------------------------------------------
# Orphan focuses
# ---------------------------------------------------------------------------


ORPHAN_TREES = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
\tfocus = {
\t\tid = TAG_focus_orphan
\t\tx = 2
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_elsewhere }
\t}
\tfocus = {
\t\tid = TAG_focus_ghost
\t\tx = 4
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_nowhere }
\t}
\tfocus = {
\t\tid = TAG_focus_ok
\t\tx = 6
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_a }
\t}
}
focus_tree = {
\tid = tree_b
\tfocus = { id = TAG_focus_elsewhere x = 0 y = 0 cost = 1 }
}
"""


def test_orphan_focus_reported_only_when_the_target_exists_elsewhere(tmp_path):
    """A prerequisite defined in another tree is an orphan; one defined nowhere
    belongs to the missing-prerequisite check instead."""
    _focus_file(tmp_path, ORPHAN_TREES)
    v = _validator(tmp_path)
    v.validate_orphan_focuses()

    assert _messages(v) == [
        "Orphan focus 'TAG_focus_orphan': prerequisite group"
        " ['TAG_focus_elsewhere'] not present in tree"
    ]
    assert v._issues[0].line == 4
    assert v._issues[0].category == "orphan-focus"


def test_prerequisite_to_an_undefined_focus_adds_no_graph_edge(tmp_path):
    _focus_file(tmp_path, ORPHAN_TREES)
    v = _validator(tmp_path)
    v.validate_dependency_cycles()
    assert v._issues == []


# ---------------------------------------------------------------------------
# Missing prerequisite targets
# ---------------------------------------------------------------------------


MISSING_PREREQ_TREES = """shared_focus = {
\tid = TAG_shared_s
\tx = 0
\ty = 0
\tcost = 1
\tprerequisite = { focus = TAG_focus_MISSPELLED }
}
shared_focus = {
\tid = TAG_shared_t
\tx = 0
\ty = 2
\tcost = 1
\tprerequisite = { focus = TAG_focus_misspelled focus = TAG_shared_absent }
}
focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_misspelled x = 0 y = 0 cost = 1 }
\tfocus = {
\t\tid = TAG_focus_b
\t\tx = 2
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_SHARED_S }
\t}
\tfocus = {
\t\tid = TAG_focus_c
\t\tx = 4
\t\ty = 0
\t\tcost = 1
\t\tprerequisite = { focus = TAG_focus_absent }
\t\tprerequisite = { focus = TAG_shared_absent }
\t}
}
"""


def test_missing_prerequisites_report_case_mismatches_and_dedupe(tmp_path):
    _focus_file(tmp_path, MISSING_PREREQ_TREES)
    v = _validator(tmp_path)
    v.validate_missing_prerequisite_targets()

    assert _messages(v) == [
        "Missing prerequisite target 'TAG_focus_MISSPELLED' (referenced by"
        " 'TAG_shared_s'): case-mismatch reference 'TAG_focus_MISSPELLED' —"
        " defined as 'TAG_focus_misspelled' (works on Windows, fails on Linux)",
        "Missing prerequisite target 'TAG_shared_absent' (referenced by"
        " 'TAG_shared_t')",
        "Missing prerequisite target 'TAG_SHARED_S' (referenced by"
        " 'TAG_focus_b'): case-mismatch reference 'TAG_SHARED_S' — defined as"
        " 'TAG_shared_s' (works on Windows, fails on Linux)",
        "Missing prerequisite target 'TAG_focus_absent' (referenced by 'TAG_focus_c')",
    ]
    assert {i.category for i in v._issues} == {"missing-prerequisite"}


# ---------------------------------------------------------------------------
# Missing localisation
# ---------------------------------------------------------------------------


LOC_TREE = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
\tfocus = { id = TAG_focus_b x = 2 y = 0 cost = 1 }
}
"""


def test_missing_focus_loc_keys_reported_per_key(tmp_path):
    _focus_file(tmp_path, LOC_TREE)
    _write(
        tmp_path,
        "localisation/english/md_l_english.yml",
        "l_english:\n"
        ' TAG_focus_a:0 "A"\n'
        ' TAG_focus_a_desc:0 "A desc"\n'
        ' TAG_focus_b:0 "B"\n',
    )
    v = _validator(tmp_path)
    v.validate_missing_loc_keys()

    assert _messages(v) == [
        "Missing loc key 'TAG_focus_b_desc' for focus 'TAG_focus_b'"
    ]
    assert v._issues[0].category == "missing-loc-key"


# ---------------------------------------------------------------------------
# Focus icons
# ---------------------------------------------------------------------------


ICON_TREE = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 icon = GFX_known }
\tfocus = { id = TAG_focus_b x = 2 y = 0 cost = 1 icon = GFX_ghost }
\tfocus = { id = TAG_focus_c x = 4 y = 0 cost = 1 icon = "GFX_[?var]" }
}
"""


def test_missing_focus_icon_reported(tmp_path, monkeypatch):
    _focus_file(tmp_path, ICON_TREE)
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_known")
    )
    v = _validator(tmp_path, missing_icons=True)
    v.validate_focus_icons()

    assert _messages(v) == ["Missing icon sprite 'GFX_ghost' for focus 'TAG_focus_b'"]
    assert v._issues[0].category == "missing-focus-icon"


def test_icon_check_skips_when_the_sprite_index_failed_to_load(tmp_path, monkeypatch):
    _focus_file(tmp_path, ICON_TREE)
    monkeypatch.setattr(V, "build_sprite_index", lambda *a, **kw: frozenset({"GFX_a"}))
    v = _validator(tmp_path, missing_icons=True)
    v.validate_focus_icons()
    assert v._issues == []


def test_icon_check_runs_only_with_the_flag(tmp_path, monkeypatch):
    _focus_file(tmp_path, ICON_TREE)
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_known")
    )

    off = _validator(tmp_path)
    off.run_validations()
    assert not [i for i in off._issues if i.category == "missing-focus-icon"]

    on = _validator(tmp_path, missing_icons=True)
    on.run_validations()
    assert [i.category for i in on._issues if i.category == "missing-focus-icon"] == [
        "missing-focus-icon"
    ]


def test_missing_icons_flag_is_registered():
    parser = argparse.ArgumentParser()
    V._add_extra_args(parser)
    assert parser.parse_args([]).missing_icons is False
    assert parser.parse_args(["--missing-icons"]).missing_icons is True


# ---------------------------------------------------------------------------
# Cross-country tooltip aggregate
# ---------------------------------------------------------------------------


def _cross_country_tree(count):
    lines = ["focus_tree = {", "\tid = tree_a", "\tcountry = { tag = SWE }"]
    for i in range(count):
        lines += [
            "\tfocus = {",
            f"\t\tid = TAG_focus_{i}",
            f"\t\tx = {i * 2}",
            "\t\ty = 0",
            "\t\tcost = 1",
            "\t\tcompletion_reward = {",
            f"\t\t\tGER = {{ country_event = offer.{i} }}",
            "\t\t}",
            "\t}",
        ]
    lines.append("}")
    return "\n".join(lines) + "\n"


def test_cross_country_findings_aggregate_per_file(tmp_path):
    _focus_file(tmp_path, _cross_country_tree(4))
    v = _validator(tmp_path)
    v.validate_cross_country_event_tooltips()

    assert _messages(v) == [
        "4 focus(es) fire an event to another nation without a"
        " TT_IF_THEY_ACCEPT tooltip: TAG_focus_0 (line 4), TAG_focus_1"
        " (line 13), TAG_focus_2 (line 22) and 1 more"
    ]
    assert v._issues[0].line == 4
    assert v._issues[0].category == "missing-cross-country-tooltip"


# ---------------------------------------------------------------------------
# Staged-mode reporting scope
# ---------------------------------------------------------------------------


PROBLEM_TREE = """focus_tree = {
\tid = tree_a
\tcountry = { tag = SWE }
\tfocus = {
\t\tid = TAG_focus_a
\t\tx = 0
\t\ty = 0
\t\tcost = 1
\t\ticon = GFX_ghost
\t\tprerequisite = { focus = TAG_focus_b }
\t\tcompletion_reward = {
\t\t\tGER = { country_event = offer.1 }
\t\t\tadd_political_power = -50
\t\t\tadd_tech_bonus = { bonus = 0.5 uses = 1 category = infantry_tech }
\t\t}
\t}
\tfocus = {
\t\tid = TAG_focus_b
\t\tx = 2
\t\ty = 0
\t\tcost = 1
\t\ticon = GFX_ghost
\t\tprerequisite = { focus = TAG_focus_a }
\t}
}
focus_tree = {
\tid = tree_duplicate
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
}
"""

CLEAN_TREE = """focus_tree = {
\tid = tree_clean
\tfocus = {
\t\tid = TAG_focus_clean
\t\tx = 0
\t\ty = 0
\t\tcost = 1
\t\ticon = GFX_known
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t}
}
"""


def _staged_mod(tmp_path):
    _focus_file(tmp_path, PROBLEM_TREE, name="unstaged.txt")
    staged = _focus_file(tmp_path, CLEAN_TREE, name="staged.txt")
    _write(
        tmp_path,
        "localisation/english/md_l_english.yml",
        'l_english:\n TAG_focus_clean:0 "C"\n TAG_focus_clean_desc:0 "C desc"\n',
    )
    return staged


def test_findings_in_unstaged_files_are_not_reported(tmp_path, monkeypatch):
    staged = _staged_mod(tmp_path)
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_known")
    )
    v = _validator(tmp_path, missing_icons=True)
    v.staged_only = True
    v.staged_files = [staged]

    v.run_validations()

    assert v._issues == []
    assert v._get_staged_paths() == {
        os.path.join("common", "national_focus", "staged.txt")
    }


def test_no_staged_focus_files_reports_nothing(tmp_path, monkeypatch):
    _staged_mod(tmp_path)
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_known")
    )
    v = _validator(tmp_path, missing_icons=True)
    v.staged_only = True
    v.staged_files = []

    v.run_validations()

    assert v._issues == []
    assert v._get_staged_paths() == set()


def test_the_same_findings_are_reported_in_a_full_run(tmp_path, monkeypatch):
    """The staged runs above must be silent because of scope, not because the
    fixture is clean."""
    _staged_mod(tmp_path)
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_known")
    )
    v = _validator(tmp_path, missing_icons=True)

    v.run_validations()

    assert {i.category for i in v._issues} >= {
        "duplicate-focus-id",
        "dependency-cycle",
        "missing-focus-icon",
        "missing-loc-key",
        "missing-cross-country-tooltip",
        "pp-malus-completion-reward",
        "tech-bonus-name",
        "missing-search-filters",
    }
