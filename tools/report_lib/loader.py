"""Load validator results from CI artifact directories.

Primary path: read the `.json` sidecar that every validator emits. Fallback:
when a validator only produced a `.log` (e.g. crashed mid-run, or was an
older version that didn't emit JSON), parse the log text for issue lines and
summary counts. Fallback issues have no structured `file`/`line` and are
therefore not eligible for Checks API annotations, but they still count in
the summary table.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from .models import Issue, Severity, ValidatorRun


def discover_validator_runs(results_dir: str) -> List[Tuple[str, Path]]:
    """Return [(validator_slug, artifact_dir), ...] sorted by slug.

    Matches any subdirectory named `validation-<slug>-results`, which is the
    convention the workflow uses for uploaded artifacts.
    """
    base = Path(results_dir)
    if not base.is_dir():
        return []

    runs = []
    for sub in sorted(base.glob("validation-*-results")):
        if not sub.is_dir():
            continue
        slug = sub.name.removeprefix("validation-").removesuffix("-results")
        runs.append((slug, sub))
    return runs


def load_all(results_dir: str) -> List[ValidatorRun]:
    """Load one `ValidatorRun` per artifact directory under `results_dir`."""
    out: List[ValidatorRun] = []
    for slug, artifact_dir in discover_validator_runs(results_dir):
        run = _load_one(slug, artifact_dir)
        out.append(run)
    return out


def _load_one(slug: str, artifact_dir: Path) -> ValidatorRun:
    title = _slug_to_title(slug)
    log_text = _read_first(artifact_dir, "*.log")
    json_issues = _read_json_sidecar(artifact_dir, slug)

    run = ValidatorRun(name=slug, title=title, log_text=log_text)

    if json_issues is not None:
        run.had_json = True
        run.issues = [Issue.from_dict(d, validator=slug) for d in json_issues]
    else:
        # Text fallback — parse bullet lines from the log and infer
        # severity from the ✗ VALIDATION COMPLETE summary line when the
        # validator didn't emit a JSON sidecar.
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

    # When text-fallback gave us fewer (or more) issues than the summary
    # line reported, trust the summary counts for the totals row. The
    # parsed issues still drive the "Issues by file" section and Checks
    # API annotations (where available).
    if not run.had_json and log_text:
        s_err, s_warn = _summary_counts(log_text)
        if s_err + s_warn > 0:
            run.errors = s_err
            run.warnings = s_warn

    run.status = _determine_status(run, log_text)
    return run


def _summary_counts(log_text: str) -> tuple:
    """Extract (errors, warnings) from a validator's ``VALIDATION COMPLETE`` line."""
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


def _read_first(artifact_dir: Path, pattern: str) -> Optional[str]:
    for path in sorted(artifact_dir.glob(pattern)):
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return None
    return None


def _read_json_sidecar(artifact_dir: Path, slug: str) -> Optional[list]:
    """Return the parsed JSON list of issue dicts, or None if not present.

    Validators emit `<output_stem>.json` next to their `.log`. In CI the log
    path is `validation-<slug>.log` so the sidecar is `validation-<slug>.json`.
    We also search for any `*.json` in the artifact dir as a fallback.
    """
    candidates = list(artifact_dir.glob(f"validation-{slug}.json"))
    if not candidates:
        candidates = list(artifact_dir.glob("*.json"))
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            continue
    return None


_LOG_ISSUE_RE = re.compile(
    r"""^\s{2,}(?P<path>[^\s:][^:]*?):(?P<line>\d+)\s*-\s*(?P<msg>.+?)\s*$""",
    re.MULTILINE,
)


def _parse_issues_from_log(
    log: str, validator: str, default_severity: str = Severity.ERROR
) -> List[Issue]:
    """Best-effort parse of `file.txt:NNN - message` lines from a log body.

    BaseValidator's ``_report()`` prints each issue indented with two spaces.
    Text fallback can't tell errors from warnings per-line, so every parsed
    issue takes ``default_severity`` (caller infers this from the ``✗
    VALIDATION COMPLETE`` summary line). Some validators also print without
    a line number; those are skipped since they can't be converted to a
    structured Issue here.
    """
    issues: List[Issue] = []
    for m in _LOG_ISSUE_RE.finditer(log):
        issues.append(
            Issue(
                severity=default_severity,
                category=validator,
                message=m.group("msg"),
                file=m.group("path"),
                line=int(m.group("line")),
                validator=validator,
            )
        )
    return issues


def _determine_status(run: ValidatorRun, log_text: Optional[str]) -> str:
    if log_text is None:
        return "no_output"
    if "✓ VALIDATION COMPLETE" in log_text and run.errors == 0 and run.warnings == 0:
        return "passed"
    if "✗ VALIDATION COMPLETE" in log_text or run.errors > 0 or run.warnings > 0:
        if run.errors == 0 and run.warnings > 0:
            return "warnings"
        if run.errors > 0:
            return "failed"
        # Log has ✗ marker but we can't see issues — treat as failure
        return "failed"
    return "unknown"
