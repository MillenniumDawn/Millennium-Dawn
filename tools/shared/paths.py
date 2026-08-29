"""Repo-anchored directories, derived from this file's location."""

from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOLS_DIR.parent
VALIDATION_DIR = TOOLS_DIR / "validation"
STANDARDIZATION_DIR = TOOLS_DIR / "standardization"
ASSETS_DIR = TOOLS_DIR / "assets"
GENERATORS_DIR = TOOLS_DIR / "generators"
