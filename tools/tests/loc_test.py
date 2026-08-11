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
    real_open = open

    def fail_append(path, mode="r", *args, **kwargs):
        if "a" in mode:
            raise OSError("read-only")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(loc, "open", fail_append, raising=False)
    monkeypatch.setattr(sys, "argv", ["loc.py", str(source), str(output)])

    try:
        loc.main()
    except SystemExit as error:
        assert "Could not write file" in str(error)
    else:
        assert False, "loc.main should fail when the output cannot be written"
