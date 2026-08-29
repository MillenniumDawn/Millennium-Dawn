"""Helpers shared by tools/tests. Not imported by production scripts."""

import json
import subprocess
from pathlib import Path

import validate_decisions as V


def run_git(repository, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def initialize_git_repository(repository, *paths):
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "test@example.com")
    run_git(repository, "config", "user.name", "Test User")
    run_git(repository, "config", "diff.renames", "true")
    run_git(repository, "add", *paths)
    run_git(repository, "commit", "-m", "initial")


def collecting_validator(cls):
    """Wrap a Validator so `_report` appends to `.collected` instead of printing."""

    class _Collecting(cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.collected = []
            self.last_severity = None

        def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
            self.collected.extend(results)
            self.last_severity = severity

    return _Collecting


_FakeValidator = collecting_validator(V.Validator)


def _factory(body):
    return V.DecisionFactory(body, source_basename="X.txt")


def results_for(factories, monkeypatch, check="validate_missing_log"):
    """Run `check` on a `_FakeValidator` fed `factories`; return its collected results."""
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(V, "parse_all_decision_factories", lambda mod_path: factories)
    getattr(validator, check)()
    return validator.collected


def issue_dict(severity, file="a.txt", line=1, message="m", category="c"):
    return {
        "severity": severity,
        "category": category,
        "message": message,
        "file": file,
        "line": line,
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def write_slug_json(base: Path, slug: str, issues: list) -> None:
    base.mkdir(parents=True, exist_ok=True)
    _write_text(base / f"{slug}.json", json.dumps(issues))


def write_log(artifact_dir: Path, slug: str, content: str) -> None:
    _write_text(artifact_dir / f"validation-{slug}.log", content)


def write_sidecar(artifact_dir: Path, slug: str, issues: list) -> None:
    _write_text(artifact_dir / f"validation-{slug}.json", json.dumps(issues))


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
