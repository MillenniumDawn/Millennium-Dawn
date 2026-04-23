"""Shared test setup for validator unit tests."""

import sys
from pathlib import Path

# `tools/validation/` is on sys.path so `from validator_common import ...`
# resolves when pytest is invoked from the repo root.
_VALIDATION_DIR = Path(__file__).resolve().parents[1]
if str(_VALIDATION_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATION_DIR))

# `tools/` is also on sys.path so validators can `from shared_utils import ...`.
_TOOLS_DIR = _VALIDATION_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
