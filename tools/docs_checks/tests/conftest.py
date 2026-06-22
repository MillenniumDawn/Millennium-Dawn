"""Shared test setup for docs-site check unit tests."""

import sys
from pathlib import Path

# `tools/docs_checks/` is on sys.path so the checks resolve their sibling
# `from common import ...` when pytest is invoked from the repo root.
_DOCS_CHECKS_DIR = Path(__file__).resolve().parents[1]
if str(_DOCS_CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(_DOCS_CHECKS_DIR))
