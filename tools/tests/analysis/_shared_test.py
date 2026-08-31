"""Behavioral tests for tools/analysis/_shared.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
# Add the analysis package parent so `import tools.analysis._shared` resolves
# via the package (so coverage can track it) and the absolute path so the
# legacy `import _shared` import in _shared.py still finds `shared_utils`.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools" / "analysis"))

from tools.analysis import _shared  # noqa: E402


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Drop REPO_ROOT-bound helpers onto a sandboxed tree."""
    monkeypatch.setattr(_shared, "REPO_ROOT", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# configure_import_paths
# ---------------------------------------------------------------------------


class TestConfigureImportPaths:
    def test_inserts_tools_dir_when_absent(self, monkeypatch):
        # Reset sys.path to something the function will mutate.
        monkeypatch.setattr(sys, "path", ["/some/clean/path"])
        _shared.configure_import_paths()
        assert str(_shared.REPO_ROOT / "tools") in sys.path
        # Inserted at position 0 so sibling imports resolve before anything else.
        assert sys.path[0] == str(_shared.REPO_ROOT / "tools")

    def test_idempotent_when_already_present(self, monkeypatch):
        tools_dir = str(_shared.REPO_ROOT / "tools")
        monkeypatch.setattr(sys, "path", [tools_dir])
        _shared.configure_import_paths()
        # No duplicate insertion.
        assert sys.path.count(tools_dir) == 1


# ---------------------------------------------------------------------------
# read_text_lines
# ---------------------------------------------------------------------------


class TestReadTextLines:
    def test_returns_splitlines(self, workspace):
        target = workspace / "data.txt"
        target.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        assert _shared.read_text_lines(target) == ["alpha", "beta", "gamma"]

    def test_replaces_invalid_bytes(self, workspace):
        target = workspace / "broken.txt"
        target.write_bytes(b"good\n\xff\xfe\nbad\n")
        lines = _shared.read_text_lines(target)
        assert lines is not None
        assert lines[0] == "good"
        assert lines[2] == "bad"
        # Middle line: at least one replacement char is present.
        assert "\ufffd" in lines[1]

    def test_returns_none_on_missing_file(self, workspace):
        assert _shared.read_text_lines(workspace / "absent.txt") is None

    def test_returns_none_on_oserror(self, workspace, monkeypatch):
        # Force read_text to raise OSError, which is the contract branch.
        target = workspace / "data.txt"
        target.write_text("x\n", encoding="utf-8")

        def boom(*_args, **_kwargs):
            raise OSError("nope")

        monkeypatch.setattr(_shared.Path, "read_text", boom)
        assert _shared.read_text_lines(target) is None


# ---------------------------------------------------------------------------
# compile_token_regex
# ---------------------------------------------------------------------------


class TestCompileTokenRegex:
    def test_matches_whole_words_only(self):
        pattern = _shared.compile_token_regex(["alpha", "beta"])
        text = "alpha beta alphabet beta_test _alpha"
        assert sorted(pattern.findall(text)) == ["alpha", "beta"]

    def test_escapes_regex_metacharacters(self):
        pattern = _shared.compile_token_regex(["a.b", "x[y]"])
        assert pattern.search("see a.b here") is not None
        # Same characters inside another word should not match.
        assert pattern.search("a_b") is None
        # Bracket form is escaped, not a character class.
        assert pattern.search("x[y]") is not None
        assert pattern.search("xy") is None

    def test_returns_compiled_pattern(self):
        pattern = _shared.compile_token_regex(["foo"])
        assert isinstance(pattern, re.Pattern)
        assert pattern.search("foo") is not None


# ---------------------------------------------------------------------------
# iter_existing_dirs / iter_readable_files
# ---------------------------------------------------------------------------


class TestIterExistingDirs:
    def test_yields_only_existing_dirs(self, workspace):
        a = workspace / "a"
        b = workspace / "b"
        a.mkdir()
        # b intentionally not created.
        result = list(_shared.iter_existing_dirs([a, b, workspace / "missing"]))
        assert result == [a]

    def test_empty_input_yields_nothing(self):
        assert list(_shared.iter_existing_dirs([])) == []


class TestIterReadableFiles:
    def test_yields_matching_files_with_lines(self, workspace):
        search = workspace / "d"
        search.mkdir()
        (search / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
        (search / "skip.md").write_text("ignored\n", encoding="utf-8")
        (search / "b.txt").write_text("three\n", encoding="utf-8")

        results = list(_shared.iter_readable_files([search], ("*.txt",)))
        paths = sorted(p.name for p, _ in results)
        assert paths == ["a.txt", "b.txt"]
        for _, lines in results:
            assert isinstance(lines, list)

    def test_skips_nonexistent_search_dirs(self, workspace):
        missing = workspace / "absent"
        assert list(_shared.iter_readable_files([missing], ("*.txt",))) == []

    def test_handles_multiple_patterns(self, workspace):
        search = workspace / "d"
        search.mkdir()
        (search / "x.txt").write_text("a\n", encoding="utf-8")
        (search / "y.yml").write_text("b: 1\n", encoding="utf-8")
        results = list(
            _shared.iter_readable_files([search], ("*.txt", "*.yml"))
        )
        names = sorted(p.suffix for p, _ in results)
        assert names == [".txt", ".yml"]
