"""Validation baseline: store main-side findings, classify PR findings.

validator-cache.yml persists the per-validator JSON sidecars of a full run
of each main commit as that commit's baseline. PR report jobs restore the
entry for their base commit (keyed on the validator source hash and the
commit) and use the key counts here to tag every finding NEW (not on that
main commit) or EXISTING (also present there).

Every validator writes a sidecar, even when clean, so the meta lists the
sidecars a baseline holds. A missing, extra, or malformed sidecar makes the
whole baseline unavailable rather than quietly smaller.

Fingerprint: (severity, category, file, message) with line references in
the message (`file.txt:123`, `line 123`) masked, counted after the same
cross-validator dedupe runs on both sides. Leaving lines out keeps an
existing finding EXISTING when an unrelated edit shifts it; counting keeps a
real second instance NEW. Severity is part of the key so an existing warning
that escalates to an error reads as a new error (the alarm direction); a
warning still matches main's error for the same finding (see classify).
Known limitation: when one file has the same finding twice, fixing one and
adding another in that file reads as two EXISTING findings. A finding with no
file has the same limit across the repo.
"""

import json
import re
import shutil
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .dedupe import dedupe
from .models import Issue, Severity

META_FILENAME = "baseline-meta.json"

# (severity, category, file, message with line references masked)
BaselineKey = Tuple[str, str, str, str]

_LINE_REF = re.compile(r"(\.\w+:|\bline )\d+")


@dataclass
class Baseline:
    """A loaded baseline: its meta plus the deduped key counts."""

    meta: Dict[str, Any]
    keys: Counter[BaselineKey]


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
    """The comparison key for one issue, or None without a category or message.

    A finding with no file keys on its message, which names what it is about
    (decision and file, idea and sprite), so it is counted repo-wide.
    """
    if not issue.category or not issue.message:
        return None
    message = _LINE_REF.sub(r"\1#", issue.message)
    return (issue.severity, issue.category, issue.file, message)


def count_keys(issues: Iterable[Issue]) -> Counter[BaselineKey]:
    """How many keyable issues share each key; unkeyable issues are skipped."""
    return Counter(key for key in map(issue_key, issues) if key is not None)


def sidecar_names(sidecar_dir: str) -> List[str]:
    """File names of the validator sidecars in a dir, meta excluded."""
    return sorted(
        path.name
        for path in Path(sidecar_dir).glob("*.json")
        if path.name != META_FILENAME
    )


def load_issues(sidecar_dir: str) -> List[Issue]:
    """Load and cross-validator dedupe every `<slug>.json` sidecar in a dir.

    The dir layout is the one `run_all_validators.py --persist-results`
    produces: one flat JSON list of issue dicts per validator. Raises
    ValueError on a sidecar that is unreadable or not a list of dicts.
    """
    issues: List[Issue] = []
    for name in sidecar_names(sidecar_dir):
        path = Path(sidecar_dir) / name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Malformed validator sidecar: {path}") from exc
        if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
            raise ValueError(f"Malformed validator sidecar: {path}")
        issues.extend(Issue.from_dict(d, validator=path.stem) for d in data)
    return dedupe(issues)


def load_baseline(
    baseline_dir: str,
    expected_toolshash: Optional[str] = None,
    expected_commit: Optional[str] = None,
) -> Optional[Baseline]:
    """Load the stored baseline, or None when missing, stale, or incomplete.

    A toolshash mismatch means the baseline was produced by a different
    validator generation; comparing against it would report every finding
    whose output shape moved as NEW, so the caller falls back to rendering
    without baseline annotation (or, nightly-side, establishing a fresh one).
    A baseline of another main commit, or an incomplete one, does the same,
    since its differences would also read as NEW findings.
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
    if expected_commit and meta.get("commit_sha") != expected_commit:
        return None
    sidecars = meta.get("sidecars")
    if not sidecars or sidecars != sidecar_names(baseline_dir):
        return None
    try:
        issues = load_issues(baseline_dir)
    except ValueError:
        return None
    return Baseline(meta=meta, keys=count_keys(issues))


def load_renames(path: str) -> Dict[str, str]:
    """Old path -> new path, from a list of each old path followed by its new one."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return dict(zip(lines[::2], lines[1::2]))


def rename_keys(
    keys: Counter[BaselineKey], renames: Dict[str, str]
) -> Counter[BaselineKey]:
    """Move main's findings in each file the PR renamed to its new path.

    The file field and any mention of the old path in the message move. A
    basename-only file field stays, since it cannot say which file it was.
    """
    moved: Counter[BaselineKey] = Counter()
    for (severity, category, file, message), count in keys.items():
        for old, new in renames.items():
            message = message.replace(old, new)
        moved[(severity, category, renames.get(file, file), message)] += count
    return moved


def tool_effect(
    pr_tools: Counter[BaselineKey], main_tools: Counter[BaselineKey]
) -> Dict[str, Tuple[int, int]]:
    """Per category, the findings the PR's validators add to and drop from
    main's own scan of the same commit. A reworded finding counts as both."""
    effect: Dict[str, List[int]] = {}
    for side, diff in ((0, pr_tools - main_tools), (1, main_tools - pr_tools)):
        for (_severity, category, _file, _message), count in diff.items():
            effect.setdefault(category, [0, 0])[side] += count
    return {category: (added, dropped) for category, (added, dropped) in effect.items()}


def classify(issues: List[Issue], baseline: Baseline) -> BaselineStats:
    """Tag each issue's `baseline_status` ("new"/"existing") in place.

    Unkeyable issues (no category or message) are left untagged and counted
    as unclassified. Rendering only adds a NEW tag when the field is set, so a
    missing baseline needs no special case at render time.

    Each baseline entry matches one issue: with N on main, the first N
    issues sharing that key read EXISTING and any more read NEW.

    Severity is part of the key on purpose: an existing warning escalated to
    an error must read as a new error (the alarm direction). A warning that
    main recorded as an error reads EXISTING: main's cross-validator dedupe
    raises a finding that another validator reports as an error, and a PR
    running fewer validators sees only the warning. Exact matches are taken
    first, so such a warning only gets an error no exact match claimed.
    """
    stats = BaselineStats()
    unmatched = baseline.keys.copy()
    keys = [issue_key(issue) for issue in issues]
    exact: List[bool] = []
    for key in keys:
        if key is not None and unmatched[key] > 0:
            unmatched[key] -= 1
            exact.append(True)
        else:
            exact.append(False)
    for issue, key, matched in zip(issues, keys, exact):
        if key is None:
            stats.unclassified += 1
            continue
        if not matched and issue.severity == Severity.WARNING:
            raised = (Severity.ERROR, key[1], key[2], key[3])
            matched = unmatched[raised] > 0
            if matched:
                unmatched[raised] -= 1
        if matched:
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


def write_baseline(sidecar_dir: str, baseline_dir: str, meta: Dict[str, Any]) -> None:
    """Persist a baseline: one JSON per validator sidecar plus a meta file.

    Stale validator files (removed from the suite since the previous save)
    are dropped so the baseline can never keep reporting issues for a
    validator that no longer runs. All-json deletion is bounded to
    `baseline_dir` and skips the meta file. The meta records the sidecar
    names so load_baseline can tell a complete baseline from a partial one.
    """
    source = Path(sidecar_dir)
    target = Path(baseline_dir)
    target.mkdir(parents=True, exist_ok=True)

    sidecars = sidecar_names(sidecar_dir)
    keep = set(sidecars) | {META_FILENAME}
    for stale in sorted(p for p in target.glob("*.json") if p.name not in keep):
        stale.unlink()
    for name in sidecars:
        shutil.copyfile(source / name, target / name)
    with open(target / META_FILENAME, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps({**meta, "sidecars": sidecars}, indent=2, sort_keys=True))


def load_changed_files(path: str) -> Set[str]:
    """Load one repo-relative path per line, normalised to forward slashes."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return set()
    paths: Set[str] = set()
    for line in text.splitlines():
        stripped = line.strip().replace("\\", "/")
        if stripped:
            paths.add(stripped)
    return paths


def tag_changed_files(issues: List[Issue], changed_files: Set[str]) -> None:
    """Set ``Issue.in_diff`` when the finding's file is in the PR diff."""
    if not changed_files:
        return
    normalised = {p.replace("\\", "/") for p in changed_files}
    for issue in issues:
        file_path = (issue.file or "").replace("\\", "/")
        issue.in_diff = bool(file_path) and file_path in normalised
