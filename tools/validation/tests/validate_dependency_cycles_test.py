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
    cycle_issues = [
        i for i in v._issues if "Dependency cycle detected" in i.message
    ]
    assert len(cycle_issues) == 1
    message = cycle_issues[0].message
    assert "TAG_focus_a" in message
    assert "TAG_focus_b" in message
    assert "TAG_focus_c" in message
