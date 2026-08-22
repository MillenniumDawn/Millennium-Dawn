import importlib.util
from pathlib import Path

import pytest


def _module():
    path = Path(__file__).resolve().parents[1] / "assets" / "state_gfx.py"
    spec = importlib.util.spec_from_file_location("state_gfx", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unknown_state_fails_before_bitmap_processing(tmp_path, monkeypatch):
    module = _module()
    states = tmp_path / "states"
    states.mkdir()
    definition = tmp_path / "definition.csv"
    bitmap = tmp_path / "provinces.bmp"
    definition.write_text("header\n", encoding="utf-8")
    bitmap.write_bytes(b"not-read")
    monkeypatch.setattr(module, "states_dir", str(states))
    monkeypatch.setattr(module, "definition_file", str(definition))
    monkeypatch.setattr(module, "provinces_bmp", str(bitmap))
    answers = iter(["999", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(
        module,
        "merge_provinces",
        lambda *_args: (_ for _ in ()).throw(AssertionError("bitmap processed")),
    )

    with pytest.raises(SystemExit, match="state ID 999"):
        module.main()
