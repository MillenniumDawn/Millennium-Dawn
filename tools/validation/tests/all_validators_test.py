"""Suite-wide smoke tests over every validate_*.py.

Parametrized across all discovered validators so `pytest` exercises the whole
suite: each must expose a BaseValidator subclass with run_validations, and must
run cleanly over an empty mod tree (catches import errors, missing contracts,
and crashes on absent input — the cheapest broad safety net we have).
"""

import importlib
from pathlib import Path

import pytest
from validator_common import BaseValidator

VALIDATION_DIR = Path(__file__).resolve().parents[1]
VALIDATORS = sorted(p.stem for p in VALIDATION_DIR.glob("validate_*.py"))


def _validator_class(modname):
    mod = importlib.import_module(modname)
    classes = [
        v
        for v in vars(mod).values()
        if isinstance(v, type)
        and issubclass(v, BaseValidator)
        and v is not BaseValidator
    ]
    return mod, classes


def test_validators_discovered():
    # Guard against an empty glob (wrong cwd / renamed dir) silently passing
    # every parametrized test below.
    assert len(VALIDATORS) >= 20, f"only found {len(VALIDATORS)} validators"


@pytest.mark.parametrize("modname", VALIDATORS)
def test_validator_exposes_contract(modname):
    mod, classes = _validator_class(modname)
    assert classes, f"{modname} exposes no BaseValidator subclass"
    assert hasattr(
        classes[0], "run_validations"
    ), f"{modname}'s validator has no run_validations()"


@pytest.mark.parametrize("modname", VALIDATORS)
def test_validator_runs_on_empty_tree(tmp_path, modname):
    _mod, classes = _validator_class(modname)
    validator = classes[0](mod_path=str(tmp_path), use_colors=False)
    # Must not raise on an empty mod tree — validators have to tolerate missing
    # directories/files gracefully.
    validator.run_all_validations()
