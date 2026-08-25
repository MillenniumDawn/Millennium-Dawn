"""Shared test setup for tools/ root-script unit tests."""

import sys
from pathlib import Path

# `tools/` is on sys.path so tests can import root-level scripts directly
# (e.g. `import dev_setup`, `from cleanup_effect_tooltip import ...`).
_TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
