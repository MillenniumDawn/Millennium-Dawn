"""Shared test setup for linting unit tests."""

import sys
from pathlib import Path

# `tools/linting/` is on sys.path so `from check_common_mistakes import ...` resolves.
_LINTING_DIR = Path(__file__).resolve().parents[1]
if str(_LINTING_DIR) not in sys.path:
    sys.path.insert(0, str(_LINTING_DIR))

# `tools/` is also on sys.path so linting scripts can `from cleanup_or import ...`.
_TOOLS_DIR = _LINTING_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
