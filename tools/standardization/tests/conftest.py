"""Shared test setup for standardizer unit tests."""

import sys
from pathlib import Path

# `tools/standardization/` is on sys.path so `from standardize_focus_tree import ...`
# and `from common_utils import ...` resolve when pytest runs from the repo root.
_STD_DIR = Path(__file__).resolve().parents[1]
if str(_STD_DIR) not in sys.path:
    sys.path.insert(0, str(_STD_DIR))

# `tools/` is also on sys.path so standardizers can `from shared_utils import ...`.
_TOOLS_DIR = _STD_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
