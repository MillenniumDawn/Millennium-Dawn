"""Geometry uses the validator's parsed files, cache and staged selection."""

import os

import pytest
import validate_focus_tree as V
from shared.suite import write_under_str

FOCUS_DIR = "common/national_focus"


def write_focus(root, text, name="tree.txt"):
    return write_under_str(root, f"{FOCUS_DIR}/{name}", text)


def validator(root, staged=None):
    value = V.Validator(str(root), workers=1, use_colors=False)
    if staged is not None:
        value.staged_only = True
        value.staged_files = staged
    value.validate_focus_overlap()
    return value


@pytest.mark.parametrize("x, count", [(-1, 1), (-2, 0)])
def test_brazil_before_and_after_5122(tmp_path, x, count):
    write_focus(
        tmp_path,
        "focus_tree = { id = brazil_focus\n"
        "focus = { id = BRA_nossa_economia x = -12 y = 0 }\n"
        "focus = { id = BRA_internationalize_the_real x = 0 y = 1 "
        "relative_position_id = BRA_nossa_economia }\n"
        f"focus = {{ id = BRA_growth_through_freedom x = {x} y = 1 "
        "relative_position_id = BRA_nossa_economia }\n}",
    )
    value = validator(tmp_path)
    assert value.errors_found == 0
    assert len(value._issues) == count
    assert value.layout_counts["overlap_pairs"] == count
    if count:
        issue = value._issues[0]
        assert issue.category == "focus-coordinate-overlap"
        assert issue.severity == V.Severity.WARNING
        assert "(-13, 1)" in issue.message and "(-12, 1)" in issue.message
        assert issue.file == f"{FOCUS_DIR}/tree.txt"


def test_direct_fields_and_line_numbers_ignore_effects_strings_and_comments(tmp_path):
    path = write_focus(
        tmp_path,
        "# focus_tree = { id = ghost }\n"
        'log = "focus_tree = { id = fake focus = { id = bad } }"\n'
        'focus_tree = {\n id = "real"\n'
        " shared_focus = { SH_a SH_b }\n"
        ' focus = { id = "a" x = -2 y = +1\n'
        " completion_reward = { x = 999 y = 99 offset = {} allow_branch = {} }\n"
        " }\n focus = { x = 2 y = 1 completion_reward = { id = nested } }\n"
        "}\nshared_focus = { id = SH_a x = 0 y = 0 }\n"
        "joint_focus = { id = SH_b x = 2 y = 0 }\n",
    )
    data = V._FocusFile(path, str(tmp_path)).layout()
    assert len(data["trees"]) == 1
    tree = data["trees"][0]
    assert (tree["id"], tree["line"], tree["shared_refs"]) == (
        "real",
        3,
        ["SH_a", "SH_b"],
    )
    assert len(tree["focuses"]) == 1
    focus = tree["focuses"][0]
    assert (focus["id"], focus["line"], focus["x"], focus["y"]) == ("a", 6, -2, 1)
    assert not focus["offset"] and not focus["allow_branch"]
    assert [item["id"] for item in data["shared"]] == ["SH_a", "SH_b"]


def test_escaped_quotes_cannot_supply_coordinates(tmp_path):
    path = write_focus(
        tmp_path,
        "focus_tree = { focus = { id = a x = 0 y = 0 "
        'desc = "text \\" x = 99 y = 99" } }',
    )
    focus = V._FocusFile(path, str(tmp_path)).layout()["trees"][0]["focuses"][0]
    assert (focus["x"], focus["y"]) == (0, 0)


def test_dynamic_markers_and_prerequisites_survive_cached_scan(tmp_path):
    path = write_focus(
        tmp_path,
        "focus_tree = { id = dynamic "
        "focus = { id = gate x = 0 y = 0 allow_branch = { always = yes } } "
        "focus = { id = moved x = 0 y = 0 offset = { x = 3 y = 0 } "
        "prerequisite = { focus = gate ignored = other focus = {} } } }",
    )
    focuses = V._FocusFile(path, str(tmp_path)).layout()["trees"][0]["focuses"]
    assert focuses[0]["allow_branch"] is True
    assert focuses[1]["offset"] is True
    assert focuses[1]["prerequisites"] == [["gate"]]
    value = validator(tmp_path)
    assert value.layout_counts["dynamic_skipped"] == 2
    assert value.layout_counts["overlap_pairs"] == 0


@pytest.mark.parametrize(
    "coordinates", ["y = 0", "x = invalid y = 0", "x = @column y = 0", "x = {} y = 0"]
)
def test_missing_or_nonnumeric_coordinates_are_unknown(tmp_path, coordinates):
    write_focus(tmp_path, f"focus_tree = {{ focus = {{ id = a {coordinates} }} }}")
    value = validator(tmp_path)
    assert value.layout_counts["unresolved"] == 1
    assert value._issues[0].category == "focus-coordinate-unresolved"


def shared_tree(root):
    host = write_focus(
        root,
        "focus_tree = { id = tree shared_focus = SH_root\n"
        "focus = { id = anchor x = 4 y = 0 }\n"
        "focus = { id = local x = 4 y = 1 } }",
    )
    shared = write_focus(
        root,
        "shared_focus = { id = SH_root x = 0 y = 1 relative_position_id = anchor }\n"
        "shared_focus = { id = SH_child x = 2 y = 1 relative_position_id = SH_root "
        "prerequisite = { focus = SH_root } }",
        "shared.txt",
    )
    return host, shared


def test_shared_staged_change_checks_unstaged_importer(tmp_path):
    host, shared = shared_tree(tmp_path)
    value = validator(tmp_path, [shared])
    assert value.layout_counts["selected_trees"] == 1
    assert value.layout_counts["instances"] == 4
    assert value.layout_counts["overlap_pairs"] == 1
    assert host not in value.staged_files
    assert "SH_root" in value._issues[0].message


@pytest.mark.parametrize("delete_file", [False, True])
def test_removed_shared_definition_rechecks_consumer(tmp_path, delete_file):
    _, shared = shared_tree(tmp_path)
    if delete_file:
        os.unlink(shared)
    else:
        write_focus(tmp_path, "# shared definition removed\n", "shared.txt")
    value = validator(tmp_path, [shared])
    assert value.layout_counts["selected_trees"] == 1
    assert any(
        "imported shared focus 'SH_root'" in issue.message for issue in value._issues
    )


def test_deleted_paths_preserved_from_shared_staged_selection(tmp_path, monkeypatch):
    _, shared = shared_tree(tmp_path)
    os.unlink(shared)
    monkeypatch.setenv("MD_STAGED_FILES", f"{FOCUS_DIR}/shared.txt")
    value = V.Validator(str(tmp_path), staged_only=True, workers=1, use_colors=False)
    value.validate_focus_overlap()
    assert shared in value.staged_files
    assert value.layout_counts["selected_trees"] == 1


def test_staged_without_focus_changes_does_not_read_files(tmp_path, monkeypatch):
    shared_tree(tmp_path)

    def unexpected(*_args):
        raise AssertionError("unexpected file read")

    monkeypatch.setattr(V, "_read_mod_text", unexpected)
    value = validator(tmp_path, [])
    assert value.layout_counts["selected_trees"] == 0
    assert value._issues == []


def test_layout_cache_reuses_parse_then_invalidates_shared_coordinates(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _, shared = shared_tree(tmp_path)
    assert validator(tmp_path).layout_counts["overlap_pairs"] == 1
    original = V._scan_focus_layout
    scanned = []

    def counted(source):
        scanned.append(source.filepath)
        return original(source)

    monkeypatch.setattr(V, "_scan_focus_layout", counted)
    assert validator(tmp_path).layout_counts["overlap_pairs"] == 1
    assert scanned == []
    write_focus(tmp_path, "shared_focus = { id = SH_root x = 7 y = 1 }", "shared.txt")
    assert validator(tmp_path, [shared]).layout_counts["overlap_pairs"] == 0
    assert scanned == [shared]


def test_parser_keeps_trees_separate_and_skips_unclosed_tree(tmp_path):
    path = write_focus(
        tmp_path,
        "focus_tree = { id = a focus = { id = same x = 0 y = 0 } }\n"
        "focus_tree = { id = b focus = { id = same x = 0 y = 0 } }\n"
        "focus_tree = {",
    )
    source = V._FocusFile(path, str(tmp_path))
    assert [tree["id"] for tree in source.layout()["trees"]] == ["a", "b"]
    assert validator(tmp_path).layout_counts["overlap_pairs"] == 0
