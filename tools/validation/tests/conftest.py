"""Shared test setup and helpers for validator unit tests."""

import sys
from pathlib import Path

import pytest

# `tools/validation/` is on sys.path so `from validator_common import ...`
# resolves when pytest is invoked from the repo root.
_VALIDATION_DIR = Path(__file__).resolve().parents[1]
if str(_VALIDATION_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATION_DIR))

# `tools/` is also on sys.path so validators can `from shared_utils import ...`.
_TOOLS_DIR = _VALIDATION_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import validate_decisions as V


class _FakeValidator(V.Validator):
    """Validator whose _report collects results instead of rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collected = []

    def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
        self.collected.extend(results)


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


def _factory(body):
    return V.DecisionFactory(body, source_basename="X.txt")


def results_for(factories, monkeypatch, check="validate_missing_log"):
    """Run `check` on a `_FakeValidator` fed `factories`; return its collected results."""
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(V, "parse_all_decision_factories", lambda mod_path: factories)
    getattr(validator, check)()
    return validator.collected
