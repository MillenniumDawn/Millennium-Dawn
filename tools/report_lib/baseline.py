"""Validation baseline: store main-side findings, classify PR findings.

validator-cache.yml persists the per-validator JSON sidecars of a full run
of each main commit as that commit's baseline. PR report jobs restore the
entry for their base commit (keyed on the validator source hash and the
commit) and tag every finding NEW (not on that main commit), EXISTING (also
there), RAISED (a warning there, an error now), or LOWERED (the reverse).

Every validator writes a sidecar, even when clean, so the meta lists the
sidecars a baseline holds. A missing, extra, or malformed sidecar makes the
whole baseline unavailable rather than quietly smaller.

Each main finding matches at most one PR finding with the same category,
file, and message, line references in the message (`file.txt:123`,
`line 123`) masked. With the PR's diff hunks, the match also needs the same
place: main's line shifted past the PR's edits, or the same changed hunk.
So fixing one copy of a finding and adding another elsewhere reads NEW, and
an unrelated edit above a finding keeps it EXISTING. Findings with no line
match by count. Main's findings come only from the validators the PR ran,
deduped the same way, so a severity difference is a real transition.
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
# (old start, old count, new start, new count) of one changed range
Hunk = Tuple[int, int, int, int]

_LINE_REF = re.compile(r"(\.\w+:|\bline )\d+")
_HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class Baseline:
    """A loaded baseline: its meta plus each validator's raw findings."""

    meta: Dict[str, Any]
    sidecars: Dict[str, List[Dict[str, Any]]]

    def issues(self, validators: Optional[Set[str]] = None) -> List[Issue]:
        """Main's deduped findings, from only `validators` when given."""
        return _dedupe_sidecars(self.sidecars, validators)


@dataclass
class BaselineStats:
    """NEW/EXISTING breakdown of one run against a baseline."""

    new_errors: int = 0
    new_warnings: int = 0
    existing_errors: int = 0
    existing_warnings: int = 0
    unclassified: int = 0
    new_issues: List[Issue] = field(default_factory=list)
    raised: List[Issue] = field(default_factory=list)
    lowered: List[Issue] = field(default_factory=list)


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


def _read_sidecars(sidecar_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """Validator name -> its issue dicts, for every `<slug>.json` in a dir.

    The dir layout is the one `run_all_validators.py --persist-results`
    produces: one flat JSON list of issue dicts per validator. Raises
    ValueError on a sidecar that is unreadable or not a list of dicts.
    """
    sidecars: Dict[str, List[Dict[str, Any]]] = {}
    for name in sidecar_names(sidecar_dir):
        path = Path(sidecar_dir) / name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Malformed validator sidecar: {path}") from exc
        if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
            raise ValueError(f"Malformed validator sidecar: {path}")
        sidecars[path.stem] = data
    return sidecars


def _dedupe_sidecars(
    sidecars: Dict[str, List[Dict[str, Any]]], validators: Optional[Set[str]] = None
) -> List[Issue]:
    return dedupe(
        [
            Issue.from_dict(d, validator=name)
            for name, data in sidecars.items()
            if validators is None or name in validators
            for d in data
        ]
    )


def load_issues(sidecar_dir: str) -> List[Issue]:
    """Load and cross-validator dedupe every sidecar in a dir."""
    return _dedupe_sidecars(_read_sidecars(sidecar_dir))


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
        sidecars = _read_sidecars(baseline_dir)
    except ValueError:
        return None
    return Baseline(meta=meta, sidecars=sidecars)


def load_renames(path: str) -> Dict[str, str]:
    """Old path -> new path, from a list of each old path followed by its new one."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return dict(zip(lines[::2], lines[1::2]))


def rename_issues(issues: List[Issue], renames: Dict[str, str]) -> None:
    """Move main's findings in each file the PR renamed to its new path.

    The file field and any mention of the old path in the message move. A
    basename-only file field stays, since it cannot say which file it was.
    """
    for issue in issues:
        for old, new in renames.items():
            issue.message = issue.message.replace(old, new)
        issue.file = renames.get(issue.file, issue.file)


def load_hunks(path: str) -> Dict[str, List[Hunk]]:
    """New path -> its changed ranges, from `git diff --unified=0` headers.

    The file holds only the `diff --git`, `+++`, and `@@` lines. An added line
    can also start with `+++`, so only the one before a file's first hunk
    names it. A deleted file (`+++ /dev/null`) has nothing to map to.
    """
    hunks: Dict[str, List[Hunk]] = {}
    current: Optional[List[Hunk]] = None
    in_hunks = False
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("diff --git "):
            current, in_hunks = None, False
        elif line.startswith("+++ b/") and not in_hunks:
            # git ends a path that has a space with a tab.
            current = hunks.setdefault(line[len("+++ b/") :].rstrip("\t"), [])
        elif match := _HUNK.match(line):
            in_hunks = True
            if current is not None:
                old_start, old_count, new_start, new_count = match.groups()
                current.append(
                    (
                        int(old_start),
                        int(old_count or 1),
                        int(new_start),
                        int(new_count or 1),
                    )
                )
    return hunks


def _position(
    issue: Issue, hunks: Dict[str, List[Hunk]], on_main: bool
) -> Optional[Tuple[str, int]]:
    """Where a finding sits in the PR's version of its file.

    ("hunk", i) on a line the PR changed, ("line", n) on an unchanged line,
    with main's lines shifted past the PR's edits. None without a file path
    and line; a basename cannot be placed.
    """
    if "/" not in issue.file or issue.line <= 0:
        return None
    shift = 0
    for index, (old_start, old_count, new_start, new_count) in enumerate(
        hunks.get(issue.file, ())
    ):
        start, count = (old_start, old_count) if on_main else (new_start, new_count)
        if count and start <= issue.line < start + count:
            return ("hunk", index)
        # A range with no lines sits after its start line.
        if issue.line < start or (not count and issue.line == start):
            break
        shift += new_count - old_count
    return ("line", issue.line + shift if on_main else issue.line)


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


def classify(
    issues: List[Issue],
    baseline_issues: List[Issue],
    hunks: Optional[Dict[str, List[Hunk]]] = None,
) -> BaselineStats:
    """Tag each issue's `baseline_status` in place against main's findings.

    Unkeyable issues (no category or message) are left untagged and counted
    as unclassified. Rendering only adds a NEW tag when the field is set, so a
    missing baseline needs no special case at render time.

    Each main finding matches one issue: with N on main, the first N issues
    sharing a match read EXISTING and any more read NEW. Without `hunks`
    nothing is placed and matches ignore lines. Same-severity matches are
    taken first; a match across severities is RAISED (warning to error) or
    LOWERED (error to warning).
    """

    def match_key(issue: Issue, on_main: bool):
        key = issue_key(issue)
        if key is None:
            return None
        place = _position(issue, hunks, on_main) if hunks is not None else None
        return (*key[1:], place)

    stats = BaselineStats()
    unmatched: Counter = Counter(
        (issue.severity, key)
        for issue in baseline_issues
        if (key := match_key(issue, True)) is not None
    )
    keys = [match_key(issue, False) for issue in issues]
    exact: List[bool] = []
    for issue, key in zip(issues, keys):
        hit = key is not None and unmatched[(issue.severity, key)] > 0
        if hit:
            unmatched[(issue.severity, key)] -= 1
        exact.append(hit)
    for issue, key, hit in zip(issues, keys, exact):
        if key is None:
            stats.unclassified += 1
            continue
        error = issue.severity == Severity.ERROR
        other = (Severity.WARNING if error else Severity.ERROR, key)
        if hit:
            issue.baseline_status = "existing"
            if error:
                stats.existing_errors += 1
            else:
                stats.existing_warnings += 1
        elif unmatched[other] > 0:
            unmatched[other] -= 1
            issue.baseline_status = "raised" if error else "lowered"
            (stats.raised if error else stats.lowered).append(issue)
        else:
            issue.baseline_status = "new"
            stats.new_issues.append(issue)
            if error:
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
