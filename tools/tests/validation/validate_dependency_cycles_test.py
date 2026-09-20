"""Tests for the dependency-cycle check in validate_focus_tree.

A prerequisite cycle must be reported once. The iterative DFS used to crash
with `ValueError: X is not in list` when a fan-in focus's DFS reached a node
left GRAY by an earlier cycle abort (cycle A->B->C->A plus D->C, E->C): the
GRAY branch indexed a node that was never on the second DFS's own path.
"""

from validate_focus_tree import Validator


def _write_focus_file(tmp_path, content):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(content, encoding="utf-8")
    return fpath


# A->B->C->A is the cycle; D->C and E->C fan in from outside it. Two fan-in
# roots make the pre-fix crash order-independent: whichever DFS reaches the
# cycle first aborts, and at least one fan-in root is still WHITE afterwards.
CYCLE_TREE = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_b }
	}
	focus = {
		id = TAG_focus_b
		x = 2
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_c }
	}
	focus = {
		id = TAG_focus_c
		x = 4
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_a }
	}
	focus = {
		id = TAG_focus_d
		x = 6
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_c }
	}
	focus = {
		id = TAG_focus_e
		x = 8
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_c }
	}
}
"""


def test_cycle_with_fanin_is_reported_without_raising(tmp_path):
    _write_focus_file(tmp_path, CYCLE_TREE)
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)

    v.validate_dependency_cycles()

    assert v.errors_found == 1
    cycle_issues = [i for i in v._issues if "Dependency cycle detected" in i.message]
    assert len(cycle_issues) == 1
    message = cycle_issues[0].message
    assert "TAG_focus_a" in message
    assert "TAG_focus_b" in message
    assert "TAG_focus_c" in message


def _cycle_issues(v):
    return [i for i in v._issues if "Dependency cycle detected" in i.message]


# A->B->A: the minimal prerequisite cycle.
TWO_NODE_CYCLE = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_b }
	}
	focus = {
		id = TAG_focus_b
		x = 2
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_a }
	}
}
"""


def test_two_node_cycle_is_reported(tmp_path):
    _write_focus_file(tmp_path, TWO_NODE_CYCLE)
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)

    v.validate_dependency_cycles()

    issues = _cycle_issues(v)
    assert len(issues) == 1
    assert "TAG_focus_a" in issues[0].message
    assert "TAG_focus_b" in issues[0].message


# The cycle routes through a shared_focus target: TAG_focus_a -> TAG_shared_s ->
# TAG_focus_a. The shared focus lives outside any focus_tree, so a per-tree graph
# drops both edges and reports nothing (the main false negative this pins).
SHARED_FOCUS_CYCLE = """shared_focus = {
	id = TAG_shared_s
	x = 0
	y = 0
	cost = 1
	prerequisite = { focus = TAG_focus_a }
}
focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 2
		cost = 1
		prerequisite = { focus = TAG_shared_s }
	}
}
"""


def test_cycle_through_shared_focus_is_reported(tmp_path):
    _write_focus_file(tmp_path, SHARED_FOCUS_CYCLE)
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)

    v.validate_dependency_cycles()

    issues = _cycle_issues(v)
    assert len(issues) == 1
    assert "TAG_shared_s" in issues[0].message
    assert "TAG_focus_a" in issues[0].message


# Diamond DAG: top depends on both A and B, both depend on root. No back-edge.
DIAMOND_DAG = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_root
		x = 4
		y = 0
		cost = 1
	}
	focus = {
		id = TAG_focus_a
		x = 2
		y = 2
		cost = 1
		prerequisite = { focus = TAG_focus_root }
	}
	focus = {
		id = TAG_focus_b
		x = 6
		y = 2
		cost = 1
		prerequisite = { focus = TAG_focus_root }
	}
	focus = {
		id = TAG_focus_top
		x = 4
		y = 4
		cost = 1
		prerequisite = { focus = TAG_focus_a }
		prerequisite = { focus = TAG_focus_b }
	}
}
"""


def test_diamond_dag_reports_no_cycle(tmp_path):
    _write_focus_file(tmp_path, DIAMOND_DAG)
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)

    v.validate_dependency_cycles()

    assert _cycle_issues(v) == []
    assert v.errors_found == 0


# Two cycles sharing node A: A<->B and A<->C. The pre-fix detector leaves A GRAY
# after aborting on the first, so the second (through the same node) is missed.
TWO_CYCLES_SHARED_NODE = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_b }
		prerequisite = { focus = TAG_focus_c }
	}
	focus = {
		id = TAG_focus_b
		x = 2
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_a }
	}
	focus = {
		id = TAG_focus_c
		x = 4
		y = 0
		cost = 1
		prerequisite = { focus = TAG_focus_a }
	}
}
"""


def test_two_independent_cycles_are_both_reported(tmp_path):
    _write_focus_file(tmp_path, TWO_CYCLES_SHARED_NODE)
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)

    v.validate_dependency_cycles()

    issues = _cycle_issues(v)
    assert len(issues) == 2
    messages = " ".join(i.message for i in issues)
    assert "TAG_focus_b" in messages
    assert "TAG_focus_c" in messages


def _linear_chain(n):
    lines = ["focus_tree = {", "\tid = test_tree"]
    for i in range(n):
        lines.append("\tfocus = {")
        lines.append(f"\t\tid = TAG_focus_{i}")
        lines.append(f"\t\tx = {i}")
        lines.append("\t\ty = 0")
        lines.append("\t\tcost = 1")
        if i > 0:
            lines.append(f"\t\tprerequisite = {{ focus = TAG_focus_{i - 1} }}")
        lines.append("\t}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def test_deep_linear_chain_does_not_recurse(tmp_path):
    _write_focus_file(tmp_path, _linear_chain(3000))
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)

    v.validate_dependency_cycles()

    assert _cycle_issues(v) == []
    assert v.errors_found == 0
