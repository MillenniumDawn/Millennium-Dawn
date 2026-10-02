"""Tests for the full-mode dry-run entry point."""

import sys

import fix_styling


def test_all_dry_run_uses_the_real_file_collection(tmp_path, monkeypatch, capsys):
    path = tmp_path / "common" / "fixture.txt"
    path.parent.mkdir()
    path.write_text("focus = {\n\tcost = 1\n}\n", encoding="utf-8", newline="")
    monkeypatch.setattr(fix_styling, "get_root_dir", lambda: str(tmp_path))
    monkeypatch.setattr(
        sys, "argv", [fix_styling.__file__, "--mode", "all", "--dry-run"]
    )

    assert fix_styling.main() == 0
    output = capsys.readouterr().out
    assert "Would fix 0 issues in 0 files" in output
    assert path.read_bytes() == b"focus = {\n\tcost = 1\n}\n"
