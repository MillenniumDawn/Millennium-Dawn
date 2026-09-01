"""Deterministic test for tools/assets/duplicate_icon.py.

The script hardcodes the focus tree input path as `../common/national_focus/<arg>`.
These tests monkeypatch `open()` to feed fake focus files so we can exercise
both the duplicate-icon counter and the no-duplicate path without touching
the real `common/national_focus/` content.
"""

import io
import sys

import pytest
from shared.suite import load_tool_module, write_text

di = load_tool_module("assets/duplicate_icon.py")


class _FakeFile(io.StringIO):
    pass


def test_main_counts_and_prints_only_duplicate_icon_lines(
    tmp_path, monkeypatch, capsys
):
    fake_path = tmp_path / "turkey.txt"
    content = (
        "focus = {\n"
        "    id = TUR_historical\n"
        "    icon = GFX_TUR_historical\n"
        "    icon = GFX_TUR_historical\n"  # duplicate icon
        "    icon = GFX_TUR_other\n"
        "    icon = GFX_TUR_other\n"  # duplicate icon
        "}\n"
    )
    write_text(fake_path, content)

    opened = []

    def fake_open(file, *args, **kwargs):
        opened.append(str(file))
        return io.StringIO(content)

    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr(sys, "argv", ["duplicate_icon.py", "turkey.txt"])
    di.main()
    out = capsys.readouterr().out

    # Both duplicates counted AND printed.
    assert "2 duplicate icons" in out
    assert out.count("icon = GFX_TUR_historical") == 1
    assert out.count("icon = GFX_TUR_other") == 1


def test_main_returns_zero_when_no_duplicates(tmp_path, monkeypatch, capsys):
    content = (
        "focus = {\n"
        "    icon = GFX_alpha\n"
        "    icon = GFX_beta\n"
        "    icon = GFX_gamma\n"
        "}\n"
    )

    monkeypatch.setattr("builtins.open", lambda *a, **kw: io.StringIO(content))
    monkeypatch.setattr(sys, "argv", ["duplicate_icon.py", "any.txt"])
    di.main()
    assert "0 duplicate icons" in capsys.readouterr().out


def test_main_is_case_insensitive_across_repeated_lines(tmp_path, monkeypatch, capsys):
    content = "focus = {\n    icon = GFX_alpha\n    ICON = gfx_alpha\n}\n"
    monkeypatch.setattr("builtins.open", lambda *a, **kw: io.StringIO(content))
    monkeypatch.setattr(sys, "argv", ["duplicate_icon.py", "x.txt"])
    di.main()
    out = capsys.readouterr().out
    assert "1 duplicate icons" in out


def test_main_ignores_non_icon_duplicates(tmp_path, monkeypatch, capsys):
    content = (
        "focus = {\n"
        "    id = SAME_id\n"
        "    id = SAME_id\n"  # duplicate but not an icon line
        "    icon = GFX_one\n"
        "}\n"
    )
    monkeypatch.setattr("builtins.open", lambda *a, **kw: io.StringIO(content))
    monkeypatch.setattr(sys, "argv", ["duplicate_icon.py", "x.txt"])
    di.main()
    assert "0 duplicate icons" in capsys.readouterr().out


def test_main_propagates_io_error(monkeypatch):
    def boom(*_args, **_kwargs):
        raise OSError("cannot read")

    monkeypatch.setattr("builtins.open", boom)
    monkeypatch.setattr(sys, "argv", ["duplicate_icon.py", "missing.txt"])
    with pytest.raises(OSError, match="cannot read"):
        di.main()
