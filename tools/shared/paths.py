"""Repo-anchored directories and import-root lists.

`PYTEST_PYTHONPATH` is the single list pytest and pyright must share.
`PYLINT_PATHS` is the init-hook list (script dirs pylint imports by basename).
"""

from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOLS_DIR.parent
VALIDATION_DIR = TOOLS_DIR / "validation"
STANDARDIZATION_DIR = TOOLS_DIR / "standardization"
ASSETS_DIR = TOOLS_DIR / "assets"
GENERATORS_DIR = TOOLS_DIR / "generators"

PYTEST_PYTHONPATH = (
    ".",
    "tools",
    "tools/validation",
    "tools/linting",
    "tools/standardization",
    "tools/docs_checks",
    "tools/analysis",
    "tools/assets",
)

PYLINT_PATHS = (
    "tools",
    "tools/analysis",
    "tools/assets",
    "tools/balance",
    "tools/docs_checks",
    "tools/generators",
    "tools/linting",
    "tools/publishing",
    "tools/report_lib",
    "tools/standardization",
    "tools/validation",
)
