"""Regression coverage for conservative, tree-scoped focus geometry."""

import copy
from decimal import Decimal

import pytest
from focus_geometry import analyze_layout


def focus(name, x=0, y=0, **kwargs):
    return {
        "id": name,
        "file": "focus.txt",
        "line": 1,
        "x": x,
        "y": y,
        "relative": None,
        "allow_branch": False,
        "offset": False,
        "prerequisites": [],
        **kwargs,
    }


def source(focuses=(), shared=(), refs=(), name="focus.txt", tree_id="tree"):
    return {
        "filepath": name,
        "trees": [
            {
                "id": tree_id,
                "line": 1,
                "focuses": list(focuses),
                "shared_refs": list(refs),
            }
        ],
        "shared": list(shared),
    }


@pytest.mark.parametrize(
    "distance,expected", [(0, 1), (1, 1), (2, 0), (-1, 1), (-2, 0)]
)
def test_horizontal_spacing(distance, expected):
    result = analyze_layout([source([focus("A", -3), focus("B", -3 + distance)])])
    assert result["counts"]["overlap_pairs"] == expected
    assert len(result["findings"]) == expected
    assert result["counts"]["static_eligible"] == 2


def test_separate_rows_and_brazil_regression():
    before = source([focus("A", -13, 1), focus("B", -12, 1), focus("C", -12, 2)])
    assert analyze_layout([before])["counts"]["overlap_pairs"] == 1
    before["trees"][0]["focuses"][0]["x"] = -14
    assert not analyze_layout([before])["findings"]


def test_stacked_cells_emit_all_six_pairs_once():
    result = analyze_layout(
        [source([focus("A"), focus("B"), focus("C", 1), focus("D", 1)])]
    )
    assert result["counts"]["overlap_pairs"] == 6
    assert len(set(result["findings"])) == 6
    assert result["counts"]["trees_with_overlaps"] == 1
    assert "focus.txt:1" in result["findings"][0][0]


def test_shared_import_descendants_and_cross_file_anchor():
    definitions = [
        focus("root", 3, file="shared.txt"),
        focus("child", 1, file="shared.txt", relative="root", prerequisites=[["root"]]),
        focus("other", 4, file="shared.txt"),
    ]
    host = source([focus("local", 0, relative="child")], refs=["root"])
    shared = source(shared=definitions, name="shared.txt")
    shared["trees"] = []
    result = analyze_layout([host, shared])
    assert result["counts"]["instances"] == 3
    assert result["counts"]["overlap_pairs"] == 3
    assert not result["unresolved"]
    assert result == analyze_layout([shared, host])
    assert result == analyze_layout([host, shared], {"shared.txt"})
    assert result == analyze_layout([host, shared], {"unrelated.txt"})
    assert not analyze_layout([host, shared], set())["findings"]


def test_shared_requires_all_prerequisites_and_follows_reversed_order():
    shared = [
        focus("leaf", prerequisites=[["middle", "second"]]),
        focus("middle", prerequisites=[["root"]]),
        focus("root"),
        focus("second"),
    ]
    file = source(shared=shared, refs=["root"])
    assert analyze_layout([file])["counts"]["instances"] == 2
    file["trees"][0]["shared_refs"].append("second")
    assert analyze_layout([file])["counts"]["instances"] == 4


def test_trees_are_isolated_and_unimported_anchor_is_unresolved():
    first = source([focus("A", relative="shared")], shared=[focus("shared")])
    first["trees"].append(source([focus("A")], tree_id="other")["trees"][0])
    result = analyze_layout([first])
    assert result["counts"]["selected_trees"] == 2
    assert result["counts"]["unresolved"] == 1
    assert result["counts"]["resolved"] == 1
    assert not result["findings"]
    assert "absent from this tree" in result["unresolved"][0][0]


def test_dynamic_union_and_alternate_prerequisite_paths():
    nodes = [
        focus("gate", allow_branch=True, offset=True),
        focus("child", prerequisites=[["gate", "static"]]),
        focus("grandchild", prerequisites=[["child"]]),
        focus("relative", relative="gate"),
        focus("static", 5),
    ]
    result = analyze_layout([source(nodes)])
    assert result["counts"]["gated"] == 3
    assert result["counts"]["offset"] == 2
    assert result["counts"]["dynamic_skipped"] == 4
    assert result["counts"]["static_eligible"] == 1
    assert not result["findings"]


def test_prerequisite_cycle_terminates_and_available_does_not_hide():
    nodes = [
        focus("A", allow_branch=True, prerequisites=[["B"]]),
        focus("B", prerequisites=[["A"]]),
        focus("C", available=False, mutually_exclusive=["D"]),
        focus("D"),
    ]
    result = analyze_layout([source(nodes)])
    assert result["counts"]["gated"] == 2
    assert result["counts"]["overlap_pairs"] == 1


@pytest.mark.parametrize("coordinate", ["x", "y"])
def test_missing_coordinate_invalidates_descendants_once(coordinate):
    nodes = [focus("bad", **{coordinate: None}), focus("child", relative="bad")]
    result = analyze_layout([source(nodes)])
    assert result["counts"]["unresolved"] == 2
    assert len(result["unresolved"]) == 1
    assert "missing or nonnumeric" in result["unresolved"][0][0]


def test_broken_chains_and_duplicates_have_root_diagnostics():
    nodes = [
        focus("A", relative="B"),
        focus("B", relative="A"),
        focus("C", relative="B"),
        focus("D", relative="missing"),
        focus("E", relative="missing"),
        focus("F"),
        focus("F", line=2),
        focus("G", relative="F"),
    ]
    result = analyze_layout([source(nodes)])
    assert result["counts"]["unresolved"] == 8
    assert len(result["unresolved"]) == 3
    assert not result["findings"]
    assert any("cycle" in message for message, _, _ in result["unresolved"])
    assert any("ambiguous" in message for message, _, _ in result["unresolved"])


def test_long_relative_chain_is_iterative_and_does_not_mutate_inputs():
    nodes = [focus("N2499", 2)]
    nodes.extend(focus(f"N{i:04}", 2, relative=f"N{i+1:04}") for i in range(2499))
    file = source(list(reversed(nodes)))
    original = copy.deepcopy(file)
    result = analyze_layout([file])
    assert result["counts"]["resolved"] == 2500
    assert not result["findings"]
    assert not result["unresolved"]
    assert file == original
    assert result == analyze_layout([file])


def test_missing_shared_import_rescanned_and_cannot_import_descendants():
    file = source(
        shared=[focus("child", prerequisites=[["missing"]])], refs=["missing"]
    )
    result = analyze_layout([file], {"changed_shared.txt"})
    assert result["counts"]["selected_trees"] == 1
    assert result["counts"]["instances"] == 0
    assert len(result["unresolved"]) == 1
    assert "has no definition" in result["unresolved"][0][0]
    assert result["counts"]["missing_shared_refs"] == 1
    assert analyze_layout([file], set())["counts"]["selected_trees"] == 0


def test_empty_layout():
    result = analyze_layout([])
    assert not any(result["counts"].values())
    assert not result["findings"]
    assert not result["unresolved"]


def test_shared_dependency_queue_waits_for_later_import():
    definitions = [
        focus("A_leaf", prerequisites=[["root", "Z_middle"]]),
        focus("Z_middle", prerequisites=[["root"]]),
        focus("root"),
    ]
    result = analyze_layout([source(shared=definitions, refs=["root"])])
    assert result["counts"]["instances"] == 3
    assert result["counts"]["overlap_pairs"] == 3


def test_ambiguous_imported_shared_id_invalidates_local_anchor():
    file = source(
        [focus("local", relative="shared")],
        shared=[focus("shared"), focus("shared", line=2)],
        refs=["shared"],
    )
    result = analyze_layout([file])
    assert result["counts"]["unresolved"] == 3
    assert len(result["unresolved"]) == 1
    assert not result["findings"]
    file["shared"].reverse()
    assert result == analyze_layout([file])


def test_shared_descendant_ignores_local_prerequisites_but_requires_all_shared():
    definitions = [
        focus("root"),
        focus("other_root"),
        focus("child", prerequisites=[["root", "local"]]),
        focus("join", prerequisites=[["root", "other_root"], ["child", "local"]]),
    ]
    file = source([focus("local", 4)], shared=definitions, refs=["root"])
    assert analyze_layout([file])["counts"]["instances"] == 3
    file["trees"][0]["shared_refs"].append("other_root")
    assert analyze_layout([file])["counts"]["instances"] == 5


@pytest.mark.parametrize(
    "distance,expected",
    [("0.5", 1), ("1.99", 1), ("2.0", 0), ("2.01", 0), ("-1.5", 1), ("-2.0", 0)],
)
def test_fractional_spacing(distance, expected):
    file = source(
        [focus("A", Decimal("-1.2")), focus("B", Decimal("-1.2") + Decimal(distance))]
    )
    result = analyze_layout([file])
    assert result["counts"]["overlap_pairs"] == expected
    assert all("Decimal(" not in message for message, _, _ in result["findings"])


def test_fractional_relative_chain_has_exact_rows_and_coordinates():
    file = source(
        [
            focus("root", Decimal("0.1"), Decimal("0.1")),
            focus("child", Decimal("0.2"), Decimal("0.2"), relative="root"),
            focus("peer", Decimal("0.3"), Decimal("0.3")),
            focus("boundary", Decimal("2.3"), Decimal("0.3")),
        ]
    )
    result = analyze_layout([file])
    assert result["counts"]["overlap_pairs"] == 1
    assert "'child' at (0.3, 0.3)" in result["findings"][0][0]
    assert "'peer' at (0.3, 0.3)" in result["findings"][0][0]


def test_fractional_neighbor_buckets_include_all_stacked_products():
    nodes = [
        focus("A"),
        focus("B"),
        focus("C", Decimal("0.5")),
        focus("D", Decimal("0.5")),
        focus("E", Decimal("1.5")),
        focus("F", Decimal("3.5")),
    ]
    result = analyze_layout([source(nodes)])
    assert result["counts"]["overlap_pairs"] == 10
    assert len(set(result["findings"])) == 10
    assert not any("'F'" in message for message, _, _ in result["findings"])


@pytest.mark.parametrize("removed", [True, False])
def test_staged_removed_or_reparented_shared_descendant_rechecks_host(removed):
    host = source([focus("local", relative="child")], refs=["root"])
    root = source(shared=[focus("root", file="root.txt")], name="root.txt")
    changed = source(
        shared=[focus("child", file="changed.txt", prerequisites=[["root"]])],
        name="changed.txt",
    )
    root["trees"] = []
    changed["trees"] = []
    assert not analyze_layout([host, root, changed])["unresolved"]
    if removed:
        changed["shared"] = []
    else:
        changed["shared"][0]["prerequisites"] = [["different_root"]]
        root["shared"].append(focus("different_root", file="root.txt"))
    result = analyze_layout([host, root, changed], {"changed.txt"})
    assert result["counts"]["selected_trees"] == 1
    assert result["counts"]["unresolved"] == 1
    assert "relative anchor 'child' is absent" in result["unresolved"][0][0]
