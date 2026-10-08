"""Tests for missing search_filters reporting in validate_focus_tree."""

from shared.suite import write_focus_file as _write_focus_file
from validate_focus_tree import Validator, _FocusFile


def _run_validator(tmp_path, content):
    _write_focus_file(tmp_path, content)
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_missing_search_filters()
    return v


def _focus(search_filters=""):
    return f"""focus_tree = {{
\tid = test_tree
\tfocus = {{
\t\tid = TAG_focus_a
\t\tx = 1
\t\ty = 1
\t\tcost = 1
\t\t{search_filters}
\t}}
}}
"""


def test_validator_flags_focus_without_search_filters(tmp_path):
    content = _focus()
    v = _run_validator(tmp_path, content)

    issues = [i.message for i in v._issues if i.category == "missing-search-filters"]
    assert len(issues) == 1
    assert issues[0] == "Focus 'TAG_focus_a' missing search_filters"
    assert v.warnings_found == 1


def test_validator_allows_focus_with_search_filters(tmp_path):
    content = _focus("search_filters = { FOCUS_FILTER_POLITICAL }")
    v = _run_validator(tmp_path, content)

    assert [
        i.message for i in v._issues if i.category == "missing-search-filters"
    ] == []
    assert v.warnings_found == 0


def test_nested_search_filters_do_not_replace_top_level_requirements(tmp_path):
    content = """focus_tree = {
\tid = test_tree
\tfocus = {
\t\tid = TAG_focus_a
\t\tx = 1
\t\ty = 1
\t\tcost = 1
\t\tcompletion_reward = {
\t\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t\t}
\t}
}
"""
    v = _run_validator(tmp_path, content)

    issues = [i.message for i in v._issues if i.category == "missing-search-filters"]
    assert len(issues) == 1
    assert issues[0] == "Focus 'TAG_focus_a' missing search_filters"


def test_worker_checks_shared_and_joint_focus_blocks(tmp_path):
    content = """shared_focus = {
\tid = TAG_shared_a
\tx = 1
\ty = 1
\tcost = 1
\tsearch_filters = { FOCUS_FILTER_POLITICAL }
}

joint_focus = {
\tid = TAG_joint_a
\tx = 3
\ty = 3
\tcost = 1
}

focus_tree = {
\tid = test_tree
\tfocus = {
\t\tid = TAG_focus_a
\t\tcost = 1
\t\tx = 5
\t\ty = 5
\t}
}
"""
    fpath = _write_focus_file(tmp_path, content)

    missing = _FocusFile(str(fpath), str(tmp_path)).missing_search_filters()
    assert {item[0] for item in missing} == {"TAG_joint_a", "TAG_focus_a"}
