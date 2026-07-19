"""cleanup_or.py must never rewrite files under resources/.

resources/ is reference-only (AGENTS.md). The mid-walk os.walk pruning only
stops descent into a nested resources/ subdir; it never guards the walk root or
a directly-passed file. These regressions cover both entry points: a resources/
file path and the resources/ directory itself must be left untouched.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import cleanup_or  # noqa: E402

# A collapsible OR block cleanup_or would otherwise rewrite to a bare condition.
_REWRITABLE = "foo = {\n\tavailable = {\n\t\tOR = {\n\t\t\thas_country_flag = bar\n\t\t}\n\t}\n}\n"
_SIMPLIFIED = "foo = {\n\tavailable = {\n\t\thas_country_flag = bar\n\t}\n}\n"


def test_control_non_resources_file_is_rewritten(tmp_path):
    # sanity: the sample really is rewritable outside resources/, so the
    # exclusion tests below prove the guard and not an inert input
    f = tmp_path / "ctrl.txt"
    f.write_text(_REWRITABLE, encoding="utf-8")
    cleanup_or.main([str(f)])
    assert f.read_text(encoding="utf-8") == _SIMPLIFIED


def test_resources_file_path_not_modified(tmp_path):
    res = tmp_path / "resources"
    res.mkdir()
    f = res / "keep.txt"
    f.write_text(_REWRITABLE, encoding="utf-8")
    cleanup_or.main([str(f)])
    assert f.read_text(encoding="utf-8") == _REWRITABLE


def test_resources_directory_not_walked(tmp_path):
    res = tmp_path / "resources"
    res.mkdir()
    f = res / "keep.txt"
    f.write_text(_REWRITABLE, encoding="utf-8")
    cleanup_or.main([str(res)])
    assert f.read_text(encoding="utf-8") == _REWRITABLE
