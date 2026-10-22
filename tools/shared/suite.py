"""Helpers shared by tools/tests. Not imported by production scripts."""

import importlib.util
import io
import json
import operator
import os
import re
import struct
import subprocess
import sys
import urllib.error
from http.client import HTTPMessage
from pathlib import Path
from types import ModuleType

import yaml
from report_lib.models import Issue, Severity
from shared_utils import iter_statement_ops, strip_comments

from shared.paths import REPO_ROOT

_SCRIPT_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[{}]|[<>!=]=?|[^\s{}<>=!]+')


def _economic_statements(source):
    source = strip_comments(source)
    entries = list(iter_statement_ops(source))
    rebuilt = " ".join(
        (
            f"{key} {comparison} {{ {body} }}"
            if body is not None
            else f'{key} {comparison} "{scalar}"'
        )
        for key, comparison, scalar, body in entries
    )

    def tokens(text):
        return [token.strip('"') for token in _SCRIPT_TOKEN.findall(text)]

    assert tokens(source) == tokens(rebuilt), "Malformed or unconsumed script"
    return entries


def script_block(source, name):
    """Extract exactly one direct child block from a script fixture or live source."""
    blocks = [
        body
        for key, comparison, _, body in iter_statement_ops(strip_comments(source))
        if key == name and comparison == "=" and body is not None
    ]
    assert len(blocks) == 1, (name, len(blocks))
    _economic_statements(blocks[0])
    return blocks[0]


class EconomicScriptFixture:
    """Bounded arithmetic/branch execution, with native effects recorded explicitly.

    This is not an engine simulator. Scopes, scheduling and timed-idea behavior are
    unsupported; round_variable accepts only integral fixtures to avoid claiming
    native rounding semantics. Unknown statements and missing inputs fail closed.
    """

    comparisons = {
        "=": operator.eq,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
    }

    def __init__(self, values, *, predicates=None, triggers=None, native_effects=()):
        self.values = dict(values)
        self.predicates = predicates or {}
        self.triggers = triggers or {}
        self.native_effects = set(native_effects)
        self.calls = []

    def number(self, scalar):
        try:
            return float(scalar)
        except ValueError:
            assert scalar in self.values, f"Missing numeric input: {scalar}"
            return self.values[scalar]

    def expression(self, entries):
        result = None
        for key, comparison, scalar, body in entries:
            assert comparison == "=", "Unsupported arithmetic operator"
            if key == "clamp":
                assert result is not None and body is not None
                limits = list(_economic_statements(body))
                assert [(item[0], item[1]) for item in limits] == [
                    ("min", "="),
                    ("max", "="),
                ]
                low, high = (self.number(item[2]) for item in limits)
                result = min(max(result, low), high)
                continue
            value = (
                self.expression(_economic_statements(body))
                if body
                else self.number(scalar)
            )
            if key == "value":
                assert result is None
                result = value
            else:
                assert result is not None
                operations = {"add": operator.add, "multiply": operator.mul}
                assert key in operations, f"Unsupported arithmetic: {key}"
                result = operations[key](result, value)
        assert result is not None
        return result

    def active(self, source, *, branch=False):
        taken = None
        for key, comparison, scalar, body in _economic_statements(source):
            if branch and key == "limit":
                continue
            if key in {"if", "else_if", "else"}:
                assert comparison == "=", "Unsupported branch operator"
                assert body is not None
                if key == "if":
                    taken = False
                else:
                    assert taken is not None, f"Unpaired {key}"
                matches = not taken and (
                    key == "else" or self.condition(script_block(body, "limit"))
                )
                if matches:
                    taken = True
                    yield from self.active(body, branch=True)
            else:
                taken = None
                yield key, comparison, scalar, body

    def condition(self, source):
        results = []
        for key, comparison, scalar, body in self.active(source):
            assert comparison == "=", "Unsupported predicate operator"
            if key == "tooltip":
                continue
            if key in {"AND", "OR", "NOT"}:
                children = list(_economic_statements(body))
                checks = [self.condition_entry(entry) for entry in children]
                result = any(checks) if key == "OR" else all(checks)
                results.append(not result if key == "NOT" else result)
            elif key == "custom_trigger_tooltip":
                results.append(self.condition(body))
            elif key == "check_variable":
                entries = list(_economic_statements(body))
                assert len(entries) == 1
                name, operation, threshold, nested = entries[0]
                assert nested is None and operation in self.comparisons
                results.append(
                    self.comparisons[operation](
                        self.number(name), self.number(threshold)
                    )
                )
            elif key == "check_expr":
                entries = list(_economic_statements(body))
                relations = [item for item in entries if item[0] == "greater_than"]
                assert len(relations) == 1
                assert relations[0][1] == "=" and relations[0][3] is not None
                actual = self.expression(
                    item for item in entries if item not in relations
                )
                expected = self.expression(_economic_statements(relations[0][3]))
                results.append(actual > expected)
            elif key in self.triggers:
                assert scalar in {"yes", "no"}
                results.append(self.condition(self.triggers[key]) == (scalar == "yes"))
            else:
                assert key in self.predicates, f"Unsupported predicate: {key}"
                predicate = self.predicates[key]
                if callable(predicate):
                    results.append(predicate(scalar, body))
                else:
                    assert scalar in {"yes", "no"}
                    results.append(predicate == (scalar == "yes"))
        return all(results)

    def condition_entry(self, entry):
        key, comparison, scalar, body = entry
        operand = f"{{ {body} }}" if body is not None else scalar
        return self.condition(f"{key} {comparison} {operand}")

    def execute(self, source):
        for key, comparison, scalar, body in self.active(source):
            assert comparison == "=", "Unsupported effect operator"
            if key in {"log", "custom_effect_tooltip"}:
                continue
            if key in {"set_variable", "multiply_variable"}:
                entries = list(_economic_statements(body))
                assert len(entries) == 1
                name, comparison, operand, expression = entries[0]
                assert comparison == "="
                value = (
                    self.expression(_economic_statements(expression))
                    if expression is not None
                    else self.number(operand)
                )
                if key == "multiply_variable":
                    value *= self.number(name)
                self.values[name] = value
            elif key == "round_variable":
                value = self.number(scalar)
                assert value == int(value), "Native fractional rounding is unsupported"
            else:
                assert key in self.native_effects, f"Unsupported effect: {key}"
                self.calls.append((key, scalar, body))

    def weight(self, source):
        weight = None
        for key, comparison, scalar, body in _economic_statements(source):
            assert comparison == "=", "Unsupported weight operator"
            if key == "base":
                weight = self.number(scalar)
                continue
            assert key == "modifier" and weight is not None
            entries = list(_economic_statements(body))
            condition = [
                entry for entry in entries if entry[0] not in {"factor", "add"}
            ]
            if all(self.condition_entry(entry) for entry in condition):
                for operation, comparison, amount, nested in entries:
                    if operation in {"factor", "add"}:
                        assert comparison == "=" and nested is None
                        value = self.number(amount)
                        weight = (
                            weight * value if operation == "factor" else weight + value
                        )
        assert weight is not None
        return weight


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


def run_tool_script(script, *args, timeout=60) -> subprocess.CompletedProcess:
    """Run tools/<script> as its own process, the way run.py and the hooks do."""
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / script), *map(str, args)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def build_validator(validator_cls, root, **kwargs):
    return validator_cls(
        mod_path=str(root), use_colors=False, workers=1, no_cache=True, **kwargs
    )


def run_validator(validator_cls, tmp_path, **kwargs):
    validator = build_validator(validator_cls, tmp_path, **kwargs)
    validator.run_validations()
    return validator


def checks_called_by_run(validator, monkeypatch):
    """Stub every `validate_*` method and run the validator.

    Returns (checks the run called, checks the class defines), both sorted.
    """
    checks = sorted(name for name in dir(validator) if name.startswith("validate_"))
    called = []
    for name in checks:
        monkeypatch.setattr(
            validator, name, lambda *_args, name=name: called.append(name)
        )
    validator.run_validations()
    return sorted(called), checks


def _finding_matches(row, entry):
    if isinstance(entry, str):
        return row == entry
    return all(part in row for part in entry)


def assert_findings(results, expected):
    """One result per expected entry: a string matches a whole result, a tuple
    matches a result holding every fragment in it. A result matches once."""
    unmatched = list(results)
    for entry in expected:
        match = next((row for row in unmatched if _finding_matches(row, entry)), None)
        assert match is not None, (entry, results)
        unmatched.remove(match)
    assert not unmatched, unmatched


def issue_categories(validator):
    return sorted(issue.category for issue in validator._issues)


def issue_rows(validator):
    return sorted(
        (issue.category, issue.message, issue.file, issue.line)
        for issue in validator._issues
    )


_YML_SECTIONS = (
    "brackets",
    "syntax",
    "mandatory",
    "typos",
    "prose",
    "var_refs",
    "subst",
    "yaml",
)


def yml_scan(path, section: str, valid_colors=()):
    """One section of the localisation validator's shared scan of a single file."""
    import validate_localisation

    results = validate_localisation._scan_shared_yml_file(
        (str(path), list(valid_colors), False, str(path))
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
    "treasury": ("_F_TREASURY", 1),
    "clamp_checks": ("_F_CLAMP", 5),
    "available": ("_F_AVAILABLE", 6),
    "available_flags": ("_F_AVAILABLE", 7),
    "scripted": ("_F_SCRIPTED", 8),
    "var_tooltips": ("_F_VAR_TOOLTIP", 9),
    "missing": ("_F_MISSING", 10),
    "flag_syntax": ("_F_FLAG_SYNTAX", 11),
}


def variable_scan(
    path,
    section: str,
    mod_path,
    *,
    ai_categories=frozenset(),
    flagged_names=frozenset(),
    backing=None,
):
    """One section of the variables validator's shared scan of a single file."""
    import validate_variables

    flag, index = _VARIABLE_SECTIONS[section]
    args: tuple = (
        str(path),
        str(mod_path),
        getattr(validate_variables, flag),
        ai_categories,
        flagged_names,
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


def decision_factory(body, basename="X.txt"):
    import validate_decisions as V

    return V.DecisionFactory(body, source_path=basename)


def event_block(event_id, *fields, kind="country_event"):
    """One event definition: the id on line 2, then one line per field.

    `event_id=None` leaves the id out. A multi-line field carries its own tabs
    after the first line.
    """
    lines = (f"id = {event_id}",) * (event_id is not None) + fields
    return f"{kind} = {{\n" + "".join(f"\t{line}\n" for line in lines) + "}\n"


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


def dds_stub(width: int, height: int) -> bytes:
    """A DDS header that carries a size and nothing else."""
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<II", header, 12, height, width)
    return bytes(header)


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


def write_tree(root: Path, files: dict) -> Path:
    """Write `{relative path: content}` under root."""
    for relative_path, content in files.items():
        write_under(root, relative_path, content)
    return root


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
