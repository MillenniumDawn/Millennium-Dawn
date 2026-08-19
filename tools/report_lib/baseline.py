"""Validation baseline: store main-side findings, classify PR findings.

The nightly `check-baseline` job in validator-cache.yml persists the
per-validator JSON sidecars of a full main run as the shared baseline. PR
report jobs restore that entry (keyed on the validator source hash) and use
the key set here to tag every finding NEW (not on the latest main run) or
EXISTING (also present there).

Fingerprint: (severity, category, file, line, message) — the report_lib
dedupe key plus severity, computed after the same cross-validator dedupe
runs on both sides. Severity is part of the key so an existing warning that
escalates to an error reads as a new error (the alarm direction). Known
limitations:
  - an unrelated edit that shifts lines makes existing findings look NEW;
  - a PR that runs only a subset of validators can tag an existing finding
    NEW when main's cross-validator dedupe escalated its severity but the
    PR's subset didn't (see classify).
"""

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .dedupe import dedupe
from .models import Issue, Severity

META_FILENAME = "baseline-meta.json"

# (severity, category, file, line, message)
BaselineKey = Tuple[str, str, str, int, str]


@dataclass
class Baseline:
    """A loaded baseline: its meta plus the deduped key set."""

    meta: Dict[str, str]
    keys: Set[BaselineKey]


@dataclass
class BaselineStats:
    """NEW/EXISTING breakdown of one run against a baseline."""

    new_errors: int = 0
    new_warnings: int = 0
    existing_errors: int = 0
    existing_warnings: int = 0
    unclassified: int = 0
    new_issues: List[Issue] = field(default_factory=list)


def issue_key(issue: Issue) -> Optional[BaselineKey]:
    """The comparison key for one issue.

    None when the issue cannot be keyed: text-fallback issues carry no
    file/line, so they can never be proven to match a baseline entry. Line
    must be positive to agree with Issue.has_location.
    """
    if not issue.category or not issue.file or issue.line <= 0 or not issue.message:
        return None
    return (issue.severity, issue.category, issue.file, issue.line, issue.message)


def load_issues(sidecar_dir: str) -> List[Issue]:
    """Load and cross-validator dedupe every `<slug>.json` sidecar in a dir.

    The dir layout is the one `run_all_validators.py --persist-results`
    produces: one flat JSON list of issue dicts per validator. A validator
    that passed clean writes no sidecar at all, which is exactly the empty
    findings set the baseline wants.
    """
    issues: List[Issue] = []
    base = Path(sidecar_dir)
    for path in sorted(base.glob("*.json")):
        if path.name == META_FILENAME:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, list):
            continue
        issues.extend(
            Issue.from_dict(d, validator=path.stem) for d in data if isinstance(d, dict)
        )
    return dedupe(issues)


def load_baseline(
    baseline_dir: str, expected_toolshash: Optional[str] = None
) -> Optional[Baseline]:
    """Load the stored baseline, or None when missing or stale.

    A toolshash mismatch means the baseline was produced by a different
    validator generation; comparing against it would report every finding
    whose output shape moved as NEW, so the caller falls back to rendering
    without baseline annotation (or, nightly-side, establishing a fresh one).
    """
    base = Path(baseline_dir)
    meta_path = base / META_FILENAME
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(meta, dict):
        return None
    if expected_toolshash and meta.get("toolshash") != expected_toolshash:
        return None

    deduped = load_issues(baseline_dir)
    keys: Set[BaselineKey] = set()
    for issue in deduped:
        key = issue_key(issue)
        if key is not None:
            keys.add(key)
    return Baseline(meta=meta, keys=keys)


def classify(issues: List[Issue], baseline: Baseline) -> BaselineStats:
    """Tag each issue's `baseline_status` ("new"/"existing") in place.

    Unkeyable issues (no file/line) are left untagged and counted as
    unclassified. Rendering only adds a NEW tag when the field is set, so a
    missing baseline needs no special case at render time.

    Severity is part of the key on purpose: an existing warning escalated to
    an error must read as a new error (the alarm direction). The accepted
    asymmetry is de-escalation — a PR that runs only the validator reporting
    a warning while main's cross-validator dedupe recorded the same finding
    as an error tags it NEW even though it exists on main.
    """
    stats = BaselineStats()
    for issue in issues:
        key = issue_key(issue)
        if key is None:
            stats.unclassified += 1
            continue
        if key in baseline.keys:
            issue.baseline_status = "existing"
            if issue.severity == Severity.ERROR:
                stats.existing_errors += 1
            else:
                stats.existing_warnings += 1
        else:
            issue.baseline_status = "new"
            stats.new_issues.append(issue)
            if issue.severity == Severity.ERROR:
                stats.new_errors += 1
            else:
                stats.new_warnings += 1
    return stats


def write_baseline(sidecar_dir: str, baseline_dir: str, meta: Dict[str, str]) -> None:
    """Persist a baseline: one JSON per validator sidecar plus a meta file.

    Stale validator files (removed from the suite since the previous save)
    are dropped so the baseline can never keep reporting issues for a
    validator that no longer runs. All-json deletion is bounded to
    `baseline_dir` and skips the meta file.
    """
    source = Path(sidecar_dir)
    target = Path(baseline_dir)
    target.mkdir(parents=True, exist_ok=True)

    sidecars = sorted(p for p in source.glob("*.json") if p.is_file())
    keep = {p.name for p in sidecars} | {META_FILENAME}
    for stale in sorted(p for p in target.glob("*.json") if p.name not in keep):
        stale.unlink()
    for path in sidecars:
        shutil.copyfile(path, target / path.name)
    (target / META_FILENAME).write_text(
        json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8"
    )
