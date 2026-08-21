"""Failure handling tests for the localization helper."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import loc  # noqa: E402


def test_main_fails_when_localisation_output_cannot_be_written(tmp_path, monkeypatch):
    source = tmp_path / "focus.txt"
    source.write_text(
        "focus_tree = {\n\tfocus = {\n\t\tid = test_focus\n\t}\n}\n",
        encoding="utf-8",
    )
    output = tmp_path / "output.yml"

    def fail_write(*_args, **_kwargs):
        raise OSError("read-only")

    monkeypatch.setattr(loc, "atomic_write_text", fail_write)
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(output)])

    try:
        loc.main()
    except SystemExit as error:
        assert "Could not write file" in str(error)
    else:
        assert False, "loc.main should fail when the output cannot be written"


def test_main_creates_single_bom_localisation_file(tmp_path, monkeypatch):
    source = tmp_path / "focus.txt"
    source.write_text(
        "focus_tree = {\n\tfocus = {\n\t\tid = test_focus\n\t}\n}\n",
        encoding="utf-8",
    )
    output = tmp_path / "output.yml"
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(output)])

    loc.main()
    first = output.read_bytes()
    loc.main()

    assert first.startswith(b"\xef\xbb\xbf")
    assert first.count(b"\xef\xbb\xbf") == 1
    assert output.read_bytes() == first
