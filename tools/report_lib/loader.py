"""Load validator results from CI artifact directories."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import Issue, Severity, ValidatorRun

MANIFEST_NAME = "batch-manifest.json"
_VALID_MODES = {"batch", "impact"}
_VALID_STATUSES = {"ok", "findings", "crash", "missing"}
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SCRIPT_RE = re.compile(r"^validate_[a-z0-9_-]+\.py$")
_RESULT_RE = re.compile(
    r"^validation-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.(?P<kind>log|json)$"
)


def load_manifest(path: Path) -> Dict[str, Any]:
    """Read and validate a batch runner manifest."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"missing or unreadable {MANIFEST_NAME}") from exc
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: Any) -> None:
    """Raise ValueError when a batch manifest does not match its schema."""
    if not isinstance(manifest, dict):
        raise ValueError(f"{MANIFEST_NAME} is not an object")
    required = {"mode", "batch", "selected", "results"}
    if not required <= manifest.keys():
        raise ValueError(f"{MANIFEST_NAME} is missing required fields")
    mode = manifest["mode"]
    batch = manifest["batch"]
    if not isinstance(mode, str) or mode not in _VALID_MODES:
        raise ValueError(f"{MANIFEST_NAME} has an invalid mode")
    if mode == "impact" and batch is not None:
        raise ValueError(f"{MANIFEST_NAME} impact batch must be null")
    if mode == "batch" and (
        not isinstance(batch, str) or not _SLUG_RE.fullmatch(batch)
    ):
        raise ValueError(f"{MANIFEST_NAME} has an invalid batch")

    selected = manifest["selected"]
    if not isinstance(selected, list) or not all(
        isinstance(name, str) and _SLUG_RE.fullmatch(name) for name in selected
    ):
        raise ValueError(f"{MANIFEST_NAME} selected is not a valid slug list")
    if len(selected) != len(set(selected)):
        raise ValueError(f"{MANIFEST_NAME} selected contains duplicates")

    results = manifest["results"]
    if not isinstance(results, list) or not all(
        isinstance(entry, dict) for entry in results
    ):
        raise ValueError(f"{MANIFEST_NAME} results is not an object list")
    names = []
    for entry in results:
        fields = {"name", "script", "strict", "returncode", "status"}
        if not fields <= entry.keys():
            raise ValueError(f"{MANIFEST_NAME} result entry lacks required fields")
        name = entry["name"]
        script = entry["script"]
        if not isinstance(name, str) or not _SLUG_RE.fullmatch(name):
            raise ValueError(f"{MANIFEST_NAME} result has an invalid name")
        if not isinstance(script, str) or not _SCRIPT_RE.fullmatch(script):
            raise ValueError(f"{MANIFEST_NAME} result {name!r} has an invalid script")
        if type(entry["strict"]) is not bool:
            raise ValueError(f"{MANIFEST_NAME} result {name!r} has invalid strict")
        if type(entry["returncode"]) is not int:
            raise ValueError(f"{MANIFEST_NAME} result {name!r} has invalid returncode")
        status = entry["status"]
        if not isinstance(status, str) or status not in _VALID_STATUSES:
            raise ValueError(f"{MANIFEST_NAME} result {name!r} has invalid status")
        if (
            (status == "ok" and entry["returncode"] != 0)
            or (status in {"findings", "crash"} and entry["returncode"] == 0)
            or (status == "missing" and entry["returncode"] != 0)
        ):
            raise ValueError(f"{MANIFEST_NAME} result {name!r} has inconsistent status")
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError(f"{MANIFEST_NAME} results contains duplicates")
    if set(names) != set(selected):
        raise ValueError(f"{MANIFEST_NAME} selected/results do not match")


def artifact_members(results_dir: str) -> Dict[str, List[Tuple[str, Path]]]:
    """Return result files grouped by slug and file kind."""
    members: Dict[str, List[Tuple[str, Path]]] = {}
    base = Path(results_dir)
    if not base.is_dir():
        return members
    for path in sorted(base.rglob("validation-*")):
        if not path.is_file():
            continue
        match = _RESULT_RE.fullmatch(path.name)
        if match:
            members.setdefault(match.group("slug"), []).append(
                (match.group("kind"), path)
            )
    return members


def discover_validator_runs(results_dir: str) -> List[Tuple[str, Path]]:
    """Return [(validator_slug, artifact_dir), ...] sorted by slug."""
    base = Path(results_dir)
    if not base.is_dir():
        return []

    runs: Dict[str, Path] = {}
    run_dirs: Set[Path] = set()
    for path in sorted(base.rglob("validation-*")):
        if not path.is_file() or path.suffix not in {".json", ".log"}:
            continue
        if path.name.endswith(".stderr.log"):
            continue
        slug = path.stem.removeprefix("validation-")
        if not slug:
            continue
        runs.setdefault(slug, path.parent)
        run_dirs.add(path.parent)

    for sub in sorted(base.rglob("*")):
        if not sub.is_dir() or not sub.name.startswith("validation-"):
            continue
        if not sub.name.endswith("-results"):
            continue
        if (sub / MANIFEST_NAME).is_file():
            continue
        if any(sub == directory or sub in directory.parents for directory in run_dirs):
            continue
        slug = sub.name.removeprefix("validation-").removesuffix("-results")
        if slug:
            runs.setdefault(slug, sub)

    return sorted(runs.items())


def load_all(results_dir: str) -> List[ValidatorRun]:
    """Load validator results and apply any batch manifest metadata."""
    records = [
        (slug, artifact_dir, _load_one(slug, artifact_dir))
        for slug, artifact_dir in discover_validator_runs(results_dir)
    ]
    manifests = []
    base = Path(results_dir)
    if base.is_dir():
        for path in sorted(base.rglob(MANIFEST_NAME)):
            try:
                manifests.append((path.parent, load_manifest(path)))
            except ValueError as exc:
                related = [
                    run for _slug, directory, run in records if directory == path.parent
                ]
                if not related:
                    records.append(
                        (
                            f"manifest-{path.parent.name}",
                            path.parent,
                            _manifest_failure(f"Malformed {MANIFEST_NAME}: {exc}"),
                        )
                    )
                else:
                    for run in related:
                        _add_failure(run, "malformed-batch-manifest", str(exc))

    for directory, manifest in manifests:
        members = artifact_members(str(directory))
        by_name: Dict[str, ValidatorRun] = {
            slug: run
            for slug, run_directory, run in records
            if run_directory == directory
        }
        entries = {entry["name"]: entry for entry in manifest["results"]}
        for name in manifest["selected"]:
            existing_run = by_name.get(name)
            member_kinds = [kind for kind, _path in members.get(name, [])]
            if existing_run is None:
                current_run = _manifest_failure(
                    f"validator {name} did not produce result files", name=name
                )
                records.append((name, directory, current_run))
                by_name[name] = current_run
            else:
                current_run = existing_run
            if existing_run is not None and sorted(member_kinds) != ["json", "log"]:
                _add_failure(
                    current_run,
                    "missing-validator-result",
                    f"validator {name} must provide exactly one log and JSON sidecar",
                )
            current_run.strict = entries[name]["strict"]
            execution_failed = entries[name]["returncode"] != 0 or entries[name][
                "status"
            ] in {"crash", "missing"}
            if execution_failed:
                current_run.execution_complete = False
                if current_run.status != "failed":
                    _add_failure(
                        current_run,
                        "impact-run-incomplete",
                        f"validator exited {entries[name]['returncode']} "
                        f"({entries[name]['status']}); no trustworthy verdict",
                    )
        for name, run in by_name.items():
            if name not in entries:
                _add_failure(
                    run,
                    "unselected-validator-result",
                    f"result files for {name} were not selected by {MANIFEST_NAME}",
                )

    return [run for _slug, _directory, run in sorted(records, key=lambda item: item[0])]


def _manifest_failure(message: str, name: str = "impact-verification") -> ValidatorRun:
    return ValidatorRun(
        name=name,
        title=_slug_to_title(name),
        issues=[
            Issue(
                severity=Severity.ERROR,
                category="batch-manifest",
                message=message,
                validator="impact-verification",
            )
        ],
        status="failed",
        errors=1,
        execution_complete=False,
    )


def _add_failure(run: ValidatorRun, category: str, message: str) -> None:
    run.issues.append(
        Issue(
            severity=Severity.ERROR,
            category=category,
            message=message,
            validator=run.name,
        )
    )
    run.status = "failed"
    run.execution_complete = False
    run.errors += 1


def _load_one(slug: str, artifact_dir: Path) -> ValidatorRun:
    title = _slug_to_title(slug)
    log_text = _read_first(artifact_dir, slug)
    try:
        json_issues = _read_json_sidecar(artifact_dir, slug)
    except ValueError as exc:
        return ValidatorRun(
            name=slug,
            title=title,
            log_text=log_text,
            issues=[
                Issue(
                    severity=Severity.ERROR,
                    category="malformed-validator-sidecar",
                    message=str(exc),
                    validator=slug,
                )
            ],
            status="failed",
            errors=1,
            had_json=True,
            execution_complete=False,
        )

    run = ValidatorRun(name=slug, title=title, log_text=log_text)
    if json_issues is not None:
        run.had_json = True
        run.issues = [Issue.from_dict(d, validator=slug) for d in json_issues]
    else:
        run.had_json = False
        summary_errors, summary_warnings = _summary_counts(log_text or "")
        default_severity = (
            Severity.WARNING
            if summary_errors == 0 and summary_warnings > 0
            else Severity.ERROR
        )
        run.issues = _parse_issues_from_log(
            log_text or "", validator=slug, default_severity=default_severity
        )

    run.errors = sum(1 for i in run.issues if i.severity == Severity.ERROR)
    run.warnings = sum(1 for i in run.issues if i.severity == Severity.WARNING)
    if not run.had_json and log_text:
        s_err, s_warn = _summary_counts(log_text)
        if s_err + s_warn > 0:
            run.errors = s_err
            run.warnings = s_warn
    run.status = _determine_status(run, log_text)
    run.execution_complete = run.status not in {"unknown", "no_output"}
    return run


def _summary_counts(log_text: str) -> tuple:
    """Extract (errors, warnings) from a validator completion line."""
    legacy = re.search(r"✗ VALIDATION COMPLETE - (\d+) TOTAL ISSUES FOUND", log_text)
    if legacy:
        return int(legacy.group(1)), 0
    err_m = re.search(r"✗ VALIDATION COMPLETE[^\n]*?(\d+) ERROR\(S\)", log_text)
    warn_m = re.search(r"✗ VALIDATION COMPLETE[^\n]*?(\d+) WARNING\(S\)", log_text)
    errors = int(err_m.group(1)) if err_m else 0
    warnings = int(warn_m.group(1)) if warn_m else 0
    return errors, warnings


def _slug_to_title(slug: str) -> str:
    return slug.replace("-", " ").title()


def _read_first(artifact_dir: Path, slug: str) -> Optional[str]:
    """Read the validator log, never a neighbor's in a batch directory."""
    exact = sorted(artifact_dir.glob(f"validation-{slug}.log"))
    if not exact:
        if artifact_dir.name != f"validation-{slug}-results":
            return None
        exact = sorted(artifact_dir.glob("*.log"))
        if len(exact) != 1:
            return None
    try:
        return exact[0].read_text(encoding="utf-8")
    except Exception:
        return None


def _read_json_sidecar(artifact_dir: Path, slug: str) -> Optional[list]:
    """Return the validated JSON issue list, or None when absent."""
    candidates = list(artifact_dir.glob(f"validation-{slug}.json"))
    if not candidates and artifact_dir.name == f"validation-{slug}-results":
        legacy = sorted(artifact_dir.glob("*.json"))
        if len(legacy) == 1:
            candidates = legacy
    if not candidates:
        return None
    path = sorted(candidates)[0]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Malformed validator sidecar: {path.name}") from exc
    if not isinstance(data, list) or not all(_is_valid_issue(item) for item in data):
        raise ValueError(f"Malformed validator sidecar: {path.name}")
    return data


def _is_valid_issue(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    required = {"severity", "category", "message"}
    if not required <= item.keys():
        return False
    if not isinstance(item["severity"], str) or item["severity"] not in {
        Severity.ERROR,
        Severity.WARNING,
    }:
        return False
    for field in ("category", "message", "file", "validator"):
        if field in item and not isinstance(item[field], str):
            return False
    if "line" in item and (type(item["line"]) is not int or item["line"] < 0):
        return False
    if "detected_by" in item and not (
        isinstance(item["detected_by"], list)
        and all(isinstance(value, str) for value in item["detected_by"])
    ):
        return False
    return True


_LOG_ISSUE_RE = re.compile(
    r"""^\s{2,}(?P<path>[^\s:][^:]*?):(?P<line>\d+)\s*-\s*(?P<msg>.+?)\s*$""",
    re.MULTILINE,
)


def _parse_issues_from_log(
    log: str, validator: str, default_severity: str = Severity.ERROR
) -> List[Issue]:
    """Parse file and line issue entries from a validator log."""
    return [
        Issue(
            severity=default_severity,
            category=validator,
            message=match.group("msg"),
            file=match.group("path"),
            line=int(match.group("line")),
            validator=validator,
        )
        for match in _LOG_ISSUE_RE.finditer(log)
    ]


def _determine_status(run: ValidatorRun, log_text: Optional[str]) -> str:
    if log_text is None and not run.had_json:
        return "no_output"
    if run.had_json:
        if run.errors > 0:
            return "failed"
        if run.warnings > 0:
            return "warnings"
        return "passed"
    if log_text is None:
        return "no_output"
    if "✓ VALIDATION COMPLETE" in log_text and run.errors == 0 and run.warnings == 0:
        return "passed"
    if "✗ VALIDATION COMPLETE" in log_text or run.errors > 0 or run.warnings > 0:
        if run.errors == 0 and run.warnings > 0:
            return "warnings"
        if run.errors > 0:
            return "failed"
        return "failed"
    return "unknown"
