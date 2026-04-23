"""Shared test helpers for the report_lib suite."""

import json
import sys
from pathlib import Path

# Make `tools/` importable so `from report_lib import ...` works when pytest
# is invoked from the repo root.
_TOOLS_DIR = Path(__file__).resolve().parents[2]
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


def write_log(artifact_dir: Path, slug: str, content: str) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / f"validation-{slug}.log").write_text(content, encoding="utf-8")


def write_sidecar(artifact_dir: Path, slug: str, issues: list) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / f"validation-{slug}.json").write_text(
        json.dumps(issues), encoding="utf-8"
    )


def make_results_tree(tmp_path: Path, specs: dict) -> Path:
    """Create a validation-results tree matching `specs`.

    `specs` is a dict like:
      {
          "events": {
              "log": "...",
              "issues": [{"severity": "error", ...}],
          },
      }
    """
    root = tmp_path / "validation-results"
    root.mkdir(parents=True, exist_ok=True)
    for slug, data in specs.items():
        sub = root / f"validation-{slug}-results"
        sub.mkdir(parents=True, exist_ok=True)
        if "log" in data:
            write_log(sub, slug, data["log"])
        if "issues" in data:
            write_sidecar(sub, slug, data["issues"])
    return root
