"""Shared fixtures for validator unit tests."""

import pytest


@pytest.fixture
def no_vanilla_gfx(monkeypatch):
    import validate_gfx_references as vg

    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_sprite_manifest", lambda: frozenset())
    monkeypatch.setattr(vg, "_vanilla_gui_ref_index", lambda: {})


@pytest.fixture
def write_path():
    def write(root, relative_path, content=""):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as file:
            file.write(content)
        return path

    return write


@pytest.fixture
def gfx_notices(monkeypatch):
    from validate_gfx_references import Validator

    def collect(tmp_path, check):
        logged = []
        validator = Validator(str(tmp_path), use_colors=False)
        monkeypatch.setattr(validator, "log", lambda msg, *a, **k: logged.append(msg))
        check(validator)
        return logged

    return collect
