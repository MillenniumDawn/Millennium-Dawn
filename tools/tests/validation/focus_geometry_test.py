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
        "branch_terms": [],
        "offset": False,
        "prerequisites": [],
        "mutually_exclusive": [],
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


GATE_TERMS = ["has_completed_focus=rival", "option=HIDE"]


def leak_ids(nodes):
    result = analyze_layout([source(nodes)])
    assert result["counts"]["branch_leaks"] == len(result["branch_leaks"])
    return [message.split("'")[3] for message, _, _ in result["branch_leaks"]]


@pytest.mark.parametrize(
    "terms,expected",
    [(["option=no"], ["leak"]), (GATE_TERMS + ["option=no"], [])],
)
def test_child_allow_branch_must_repeat_hidden_ancestor_terms(terms, expected):
    nodes = [
        focus("gate", allow_branch=True, branch_terms=GATE_TERMS),
        focus("middle", prerequisites=[["gate"]]),
        focus("other", prerequisites=[["gate"]]),
        focus(
            "leak",
            allow_branch=True,
            branch_terms=terms,
            prerequisites=[["middle", "other"]],
        ),
    ]
    assert leak_ids(nodes) == expected


@pytest.mark.parametrize(
    "groups,expected",
    [([["middle", "visible"]], []), ([["middle"], ["visible"]], ["leak"])],
)
def test_branch_leak_needs_a_fully_hidden_prerequisite_group(groups, expected):
    nodes = [
        focus("gate", allow_branch=True, branch_terms=GATE_TERMS),
        focus("middle", prerequisites=[["gate"]]),
        focus("visible"),
        focus("leak", allow_branch=True, prerequisites=groups),
    ]
    assert leak_ids(nodes) == expected


RIVAL = "has_completed_focus=rival"
HIDDEN_RIVAL = "hide_rule:" + RIVAL


@pytest.mark.parametrize(
    "gate_terms,child_terms,expected",
    [
        ([HIDDEN_RIVAL], [HIDDEN_RIVAL], []),
        ([HIDDEN_RIVAL], [RIVAL], []),
        ([HIDDEN_RIVAL], ["hide_rule:has_completed_focus=other"], ["leak"]),
        ([RIVAL], [HIDDEN_RIVAL], ["leak"]),
        ([RIVAL], [RIVAL, "hide_rule:has_completed_focus=other"], []),
    ],
)
def test_terms_outside_the_hide_rule_satisfy_terms_inside_it(
    gate_terms, child_terms, expected
):
    nodes = [
        focus("gate", allow_branch=True, branch_terms=gate_terms),
        focus(
            "leak",
            allow_branch=True,
            branch_terms=child_terms,
            prerequisites=[["gate"]],
        ),
    ]
    assert leak_ids(nodes) == expected


def test_branch_leak_stops_at_the_first_gated_descendant():
    nodes = [
        focus("gate", allow_branch=True, branch_terms=GATE_TERMS),
        focus(
            "pair", allow_branch=True, branch_terms=GATE_TERMS, prerequisites=[["gate"]]
        ),
        focus("leak", allow_branch=True, prerequisites=[["pair"]]),
    ]
    assert leak_ids(nodes) == ["leak"]


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


def test_prerequisite_or_members_and_relative_shared_positions():
    host = source(
        [
            focus(
                "child",
                0,
                1,
                relative="SH_root",
                prerequisites=[["SH_root", "SH_child"]],
            )
        ],
        refs=["SH_root"],
    )
    shared = source(
        shared=[
            focus("SH_root", 0, 0, file="shared.txt"),
            focus(
                "SH_child",
                0,
                2,
                file="shared.txt",
                relative="SH_root",
                prerequisites=[["SH_root"]],
            ),
        ],
        name="shared.txt",
    )
    shared["trees"] = []
    result = analyze_layout([host, shared])
    assert result["counts"]["prerequisite_order_pairs"] == 1
    assert len(result["prerequisite_order"]) == 1
    warning = result["prerequisite_order"][0][0]
    assert "'SH_child' at (0, 2)" in warning
    assert "'child' at (0, 1)" in warning
    assert "'SH_root'" not in warning  # the other OR member is above the child


def test_prerequisite_rows_include_equal_and_every_bad_or_member_once():
    parents = [focus(f"P{i}", i * 3, 1) for i in range(4)]
    parents.append(focus("above", 20, 0))
    child = focus(
        "child",
        30,
        1,
        prerequisites=[["P0", "P1", "above"], ["P0", "P2", "P3"]],
    )
    result = analyze_layout([source(parents + [child])])
    assert result["counts"]["prerequisite_order_pairs"] == 4
    warnings = [message for message, _, _ in result["prerequisite_order"]]
    assert sum("prerequisite 'P0'" in message for message in warnings) == 1
    assert {f"P{i}" for i in range(4)} <= {
        message.split(" prerequisite '")[1].split("'")[0] for message in warnings
    }


def test_prerequisite_order_deduplicates_repeated_edge_but_keeps_reverse_edge():
    result = analyze_layout(
        [
            source(
                [
                    focus("A", prerequisites=[["B"], ["B"]]),
                    focus("B", prerequisites=[["A"]]),
                ]
            )
        ]
    )
    assert result["counts"]["prerequisite_order_pairs"] == 2
    assert len(result["prerequisite_order"]) == 2
    assert {
        message.split("prerequisite '")[1].split("'")[0]
        for message, _, _ in result["prerequisite_order"]
    } == {
        "A",
        "B",
    }


def test_prerequisite_row_warnings_skip_unresolved_and_cyclic_positions():
    result = analyze_layout(
        [
            source(
                [
                    focus("broken", relative="missing", prerequisites=[["child"]]),
                    focus("cycle_a", relative="cycle_b", prerequisites=[["cycle_b"]]),
                    focus("cycle_b", relative="cycle_a", prerequisites=[["cycle_a"]]),
                    focus("child", prerequisites=[["broken", "cycle_a"]]),
                ]
            )
        ]
    )
    assert result["counts"]["unresolved"] == 3
    assert result["counts"]["prerequisite_order_pairs"] == 0
    assert not result["prerequisite_order"]


def test_mutex_pairs_are_unordered_and_reciprocal_declarations_deduplicate():
    result = analyze_layout(
        [
            source(
                [
                    focus("A", 0, 0, mutually_exclusive=["B", "C"]),
                    focus("B", 3, 1, mutually_exclusive=["A"]),
                    focus("C", 6, 2, mutually_exclusive=["A"]),
                ]
            )
        ]
    )
    assert result["counts"]["mutually_exclusive_row_pairs"] == 2
    assert len(result["mutually_exclusive_rows"]) == 2
    assert all(
        "different rows" in message
        for message, _, _ in result["mutually_exclusive_rows"]
    )


def test_same_row_mutex_pair_is_not_reported():
    result = analyze_layout(
        [source([focus("A", 0, 0, mutually_exclusive=["B"]), focus("B", 3, 0)])]
    )
    assert result["counts"]["mutually_exclusive_row_pairs"] == 0
    assert not result["mutually_exclusive_rows"]


def test_gated_mutex_pair_is_skipped_even_when_rows_differ():
    result = analyze_layout(
        [
            source(
                [
                    focus(
                        "gated",
                        0,
                        0,
                        allow_branch=True,
                        mutually_exclusive=["candidate"],
                    ),
                    focus("candidate", 3, 2, mutually_exclusive=["gated"]),
                ]
            )
        ]
    )
    assert result["counts"]["gated"] == 1
    assert result["counts"]["mutually_exclusive_row_pairs"] == 0
    assert not result["mutually_exclusive_rows"]


def test_mutex_pair_from_imported_shared_relative_chain_is_reported():
    host = source(refs=["SH_root"])
    shared = source(
        shared=[
            focus("SH_root", 0, 0, file="shared.txt"),
            focus(
                "SH_middle",
                1,
                1,
                file="shared.txt",
                relative="SH_root",
                prerequisites=[["SH_root"]],
            ),
            focus(
                "SH_leaf",
                1,
                1,
                file="shared.txt",
                relative="SH_middle",
                prerequisites=[["SH_middle"]],
                mutually_exclusive=["SH_root"],
            ),
        ],
        name="shared.txt",
    )
    shared["trees"] = []
    shared["shared"][0]["mutually_exclusive"] = ["SH_leaf"]
    result = analyze_layout([host, shared])
    assert result["counts"]["instances"] == 3
    assert result["counts"]["mutually_exclusive_row_pairs"] == 1
    warning = result["mutually_exclusive_rows"][0][0]
    assert "'SH_root' at (0, 0)" in warning
    assert "'SH_leaf' at (2, 2)" in warning


def test_mutex_checks_skip_unresolved_and_absent_or_unimported_targets():
    file = source(
        [
            focus("missing_anchor", relative="absent", mutually_exclusive=["peer"]),
            focus("cycle_a", relative="cycle_b", mutually_exclusive=["cycle_b"]),
            focus("cycle_b", relative="cycle_a", mutually_exclusive=["cycle_a"]),
            focus(
                "peer",
                3,
                2,
                mutually_exclusive=[
                    "missing_anchor",
                    "absent_mutex",
                    "unimported_shared",
                ],
            ),
            focus(
                "child",
                6,
                2,
                prerequisites=[["unimported_shared"]],
                mutually_exclusive=["absent_mutex", "unimported_shared"],
            ),
        ],
        shared=[focus("unimported_shared", 0, 8)],
    )
    result = analyze_layout([file])
    assert result["counts"]["unresolved"] == 3
    assert result["counts"]["mutually_exclusive_row_pairs"] == 0
    assert not result["mutually_exclusive_rows"]


def test_large_prerequisite_and_mutex_groups_are_complete_and_deduplicated():
    members = [focus(f"P{i:03}", i * 3, 2) for i in range(64)]
    child = focus(
        "child",
        0,
        1,
        prerequisites=[[item["id"] for item in members]],
        mutually_exclusive=[item["id"] for item in members],
    )
    for member in members:
        member["mutually_exclusive"] = ["child"]
    result = analyze_layout([source(members + [child])])
    assert result["counts"]["prerequisite_order_pairs"] == 64
    assert result["counts"]["mutually_exclusive_row_pairs"] == 64
    assert len(result["prerequisite_order"]) == 64
    assert len(result["mutually_exclusive_rows"]) == 64


def test_prerequisite_and_mutex_warnings_skip_gated_or_offset_focus_pairs():
    result = analyze_layout(
        [
            source(
                [
                    focus("gate", 0, 2, allow_branch=True),
                    focus("gated_child", 0, 0, prerequisites=[["gate"]]),
                    focus("offset", 3, 2, offset=True),
                    focus(
                        "offset_child",
                        0,
                        -2,
                        relative="offset",
                        prerequisites=[["offset"]],
                        mutually_exclusive=["peer"],
                    ),
                    focus("peer", 6, 1, mutually_exclusive=["offset_child"]),
                ]
            )
        ]
    )
    assert result["counts"]["prerequisite_order_pairs"] == 0
    assert result["counts"]["mutually_exclusive_row_pairs"] == 0


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
