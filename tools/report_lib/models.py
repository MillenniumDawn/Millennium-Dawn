"""Lightweight data models for validation reporting.

Mirrors `tools/validation/validator_common.Issue` but with no multiprocessing
or filesystem dependencies so this module stays cheap to import in CI jobs
that only need to render reports.
"""

from dataclasses import dataclass, field
from typing import List, Optional


class Severity:
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    severity: str
    category: str
    message: str
    file: str = ""
    line: int = 0
    validator: str = ""
    detected_by: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict, validator: str = "") -> "Issue":
        return cls(
            severity=d.get("severity", Severity.ERROR),
            category=d.get("category", ""),
            message=d.get("message", ""),
            file=d.get("file", ""),
            line=int(d.get("line", 0) or 0),
            validator=d.get("validator", validator),
        )

    @property
    def dedup_key(self) -> tuple:
        return (self.category, self.file, self.line, self.message)

    @property
    def has_location(self) -> bool:
        return bool(self.file) and self.line > 0


@dataclass
class ValidatorRun:
    """One validator's result, loaded from its artifact directory."""

    name: str  # slug used in CI (e.g. "events", "oob-units")
    title: str  # pretty title for display
    log_text: Optional[str] = None  # raw log content (may be None if log missing)
    issues: List[Issue] = field(default_factory=list)
    status: str = "unknown"  # "passed" | "warnings" | "failed" | "no_output"
    errors: int = 0
    warnings: int = 0
    had_json: bool = False  # True when JSON sidecar was loaded; False = text fallback

    def status_symbol(self) -> str:
        return {
            "passed": "✓ Pass",
            "warnings": "⚠ Warn",
            "failed": "✗ Fail",
            "no_output": "⚠ No output",
            "unknown": "⚠ Unknown",
        }.get(self.status, "⚠ Unknown")


@dataclass
class ReportContext:
    """Metadata threaded through rendering (commit, PR number, links)."""

    pr_number: Optional[str] = None
    commit_sha: Optional[str] = None
    workflow_run_url: Optional[str] = None
    artifact_url: Optional[str] = None
    date_utc: Optional[str] = None
