"""Helpers shared by tools/tests. Not imported by production scripts."""

import importlib.util
import io
import json
import os
import struct
import subprocess
import sys
import tempfile
import urllib.error
from http.client import HTTPMessage
from pathlib import Path
from types import ModuleType

import yaml
from report_lib.models import Issue, Severity

from shared.paths import REPO_ROOT


def symlinks_available() -> bool:
    """Whether this process may create a symlink.

    Windows refuses without Developer Mode or admin rights (WinError 1314), so
    symlink-rejection tests skip there instead of failing the whole suite.
    """
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "target"
        target.mkdir()
        try:
            (Path(folder) / "link").symlink_to(target)
        except (OSError, NotImplementedError):
            return False
    return True


def imagemagick_available() -> bool:
    """Whether a real ImageMagick binary is on PATH.

    Windows ships its own `convert.exe` (the FAT-to-NTFS converter), so the
    tool's own resolver decides — the name alone proves nothing.
    """
    converter = load_tool_module("assets/md_art_convert.py")
    return converter.find_imagemagick("magick", "convert", "identify") is not None


def prevent_commit_signing_during_tests(*args) -> tuple:
    """Prevents git commit signing during tests."""
    git_args = tuple(args)
    if "pytest" in sys.modules and "commit" in args:
        git_args += ("--no-gpg-sign",)
    return git_args


def run_git(repository, *args):
    git_args = prevent_commit_signing_during_tests(*args)
    return subprocess.run(
        ["git", *git_args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def initialize_git_repository(repository, *paths):
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "test@example.com")
    run_git(repository, "config", "user.name", "Test User")
    run_git(repository, "config", "diff.renames", "true")
    run_git(repository, "add", *paths)
    run_git(repository, "commit", "-m", "initial")


TEST_SUITE_WORKFLOW = REPO_ROOT / ".github/workflows/test-suite.yml"


def workflow_step(job: str, name: str) -> dict:
    """Return one named step of a test-suite.yml job."""
    workflow = yaml.safe_load(TEST_SUITE_WORKFLOW.read_text(encoding="utf-8"))
    return next(
        step for step in workflow["jobs"][job]["steps"] if step.get("name") == name
    )


def substitute_expressions(script: str, values: dict) -> str:
    """Replace each `${{ expr }}` with its value; every expression must be known."""
    for expression, value in values.items():
        script = script.replace("${{ " + expression + " }}", value)
    assert "${{" not in script, f"unsubstituted expression in: {script}"
    return script


def run_bash_step(script: str, cwd, env=None) -> subprocess.CompletedProcess:
    """Run a workflow `run:` script the way an ubuntu runner does: `bash -e`."""
    return subprocess.run(
        ["bash", "-e", "-c", script],
        cwd=cwd,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        timeout=60,
    )


def run_validator(validator_cls, tmp_path, **kwargs):
    validator = validator_cls(
        mod_path=str(tmp_path), use_colors=False, workers=1, no_cache=True, **kwargs
    )
    validator.run_validations()
    return validator


def issue_categories(validator):
    return sorted(issue.category for issue in validator._issues)


def issue_rows(validator):
    return sorted(
        (issue.category, issue.message, issue.file, issue.line)
        for issue in validator._issues
    )


_YML_SECTIONS = ("brackets", "syntax", "mandatory", "typos", "prose", "var_refs")


def yml_scan(path, section: str, valid_colors=()):
    """One section of the localisation validator's shared scan of a single file."""
    import validate_localisation

    results = validate_localisation._scan_shared_yml_file(
        (str(path), list(valid_colors))
    )
    return results[_YML_SECTIONS.index(section)]


def yml_syntax(path, valid_colors, subst_keys=frozenset()):
    """Syntax findings as the validator reports them: substitution keys exempt."""
    pairs = yml_scan(path, "syntax", valid_colors)
    return [finding for finding, key in pairs if key not in subst_keys]


_CALL_SITE_SECTIONS = (
    "longform",
    "invalid",
    "typed",
    "counts",
    "dynamic",
    "fof",
    "major",
)


def call_site_scan(path, section: str, mod_path, tracked=frozenset()):
    """One section of the event validator's shared call-site scan of a single file."""
    import validate_events

    index = _CALL_SITE_SECTIONS.index(section)
    args = (str(path), str(mod_path), 1 << index, tracked, tracked, tracked)
    return validate_events._scan_shared_call_site_file(args)[index]


# section: (mask flag, index in the shared result)
_VARIABLE_SECTIONS = {
    "math": ("_F_MATH", 0),
    "orphan": ("_F_ORPHAN", 1),
    "treasury": ("_F_TREASURY", 2),
    "clamp_checks": ("_F_CLAMP", 6),
    "available": ("_F_AVAILABLE", 7),
    "available_flags": ("_F_AVAILABLE", 8),
    "scripted": ("_F_SCRIPTED", 9),
    "var_tooltips": ("_F_VAR_TOOLTIP", 10),
    "missing": ("_F_MISSING", 11),
    "flag_syntax": ("_F_FLAG_SYNTAX", 12),
}


def variable_scan(
    path,
    section: str,
    mod_path,
    *,
    ai_categories=frozenset(),
    flagged_names=frozenset(),
    consumer_map=None,
    backing=None,
):
    """One section of the variables validator's shared scan of a single file."""
    import validate_variables

    flag, index = _VARIABLE_SECTIONS[section]
    args = (
        str(path),
        str(mod_path),
        getattr(validate_variables, flag),
        ai_categories,
        flagged_names,
        consumer_map or {},
        backing or {},
        {},
        frozenset(),
    )
    return validate_variables._scan_shared_file(args)[index]


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


def fake_decisions_validator(*args, **kwargs):
    import validate_decisions as V

    return collecting_validator(V.Validator)(*args, **kwargs)


def decision_factory(body):
    import validate_decisions as V

    return V.DecisionFactory(body, source_basename="X.txt")


def decisions_results_for(factories, monkeypatch, check="validate_missing_log"):
    """Run a `validate_decisions.Validator` check on `factories`; return its results.

    Bound to validate_decisions only — use `collecting_validator` for other validators.
    """
    import validate_decisions as V

    validator = fake_decisions_validator("/tmp")
    # Some checks pass `lowercase=` explicitly, so the stub must accept it.
    monkeypatch.setattr(
        V, "parse_all_decision_factories", lambda mod_path, lowercase=False: factories
    )
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


def make_issue(**overrides):
    fields = {
        "severity": Severity.ERROR,
        "category": "missing_key",
        "message": "key FOO not found",
        "file": "events/MD_x.txt",
        "line": 212,
        "validator": "events",
    }
    fields.update(overrides)
    return Issue(**fields)


class _UnreadableHTTPError(urllib.error.HTTPError):
    def read(self, *_args, **_kwargs):
        raise OSError("response stream already consumed")


def http_error(code: int, body: bytes | None = b"denied"):
    error_type = _UnreadableHTTPError if body is None else urllib.error.HTTPError
    return error_type(
        "https://api.github.invalid",
        code,
        "err",
        HTTPMessage(),
        io.BytesIO(body or b""),
    )


def dds_header(
    magic: int,
    flags: int,
    height: int,
    width: int,
    linear_size: int,
    pixel_format: bytes,
    caps: int,
    mip_count: int = 0,
) -> bytes:
    return (
        struct.pack("<8I", magic, 124, flags, height, width, linear_size, 0, mip_count)
        + bytes(44)
        + pixel_format
        + struct.pack("<I", caps)
        + bytes(16)
    )


def load_tool_module(
    relative_path: str, *, module_name: str | None = None, register: bool = False
) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / relative_path
    name = module_name or f"_tool_test_{path.stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    if register:
        sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, content: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return path


def write_under(root: Path, relative_path: str, content: str) -> Path:
    return write_text(root / relative_path, content)


def write_under_str(root: Path, relative_path: str, content: str) -> str:
    return str(write_under(root, relative_path, content))


def write_focus_file(root: Path, content: str) -> Path:
    return write_under(root, "common/national_focus/test.txt", content)


def write_yml(root: Path, name: str, value_line: str) -> str:
    """One English localisation entry in a file that starts with a BOM."""
    return write_under_str(root, name, f"﻿l_english:\n {value_line}\n")


def read_text(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def write_slug_json(base: Path, slug: str, issues: list) -> None:
    write_text(Path(base) / f"{slug}.json", json.dumps(issues))


def write_log(artifact_dir: Path, slug: str, content: str) -> None:
    write_text(Path(artifact_dir) / f"validation-{slug}.log", content)


def write_sidecar(artifact_dir: Path, slug: str, issues: list) -> None:
    write_text(Path(artifact_dir) / f"validation-{slug}.json", json.dumps(issues))


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
    root = Path(tmp_path) / "validation-results"
    root.mkdir(parents=True, exist_ok=True)
    for slug, data in specs.items():
        sub = root / f"validation-{slug}-results"
        sub.mkdir(parents=True, exist_ok=True)
        if "log" in data:
            write_log(sub, slug, data["log"])
        if "issues" in data:
            write_sidecar(sub, slug, data["issues"])
    return root
