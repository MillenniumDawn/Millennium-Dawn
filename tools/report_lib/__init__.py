"""Millennium Dawn PR validation report library.

Loads per-validator JSON sidecars produced by the validation suite, dedupes
issues across validators, and renders a single Markdown report plus optional
GitHub Checks API annotations.

Public entry points:
  - load_all(results_dir)  -> list[Issue]
  - dedupe(issues)         -> list[Issue]
  - render(state, ctx)     -> str  (Markdown body)
  - post_comment(...)      -> None
  - post_checks(...)       -> None

The CLI is `tools/generate_validation_report.py`.
"""

from .checks_api import post_checks
from .comment import REPORT_MARKER, find_existing_comment, post_comment
from .dedupe import dedupe
from .loader import discover_validator_runs, load_all
from .markdown import MAX_ISSUES_STEP_SUMMARY, render
from .models import Issue, ReportContext, Severity, ValidatorRun
from .truncation import MAX_COMMENT_BYTES, truncate_if_needed

__all__ = [
    "MAX_ISSUES_STEP_SUMMARY",
    "Issue",
    "Severity",
    "ValidatorRun",
    "ReportContext",
    "load_all",
    "discover_validator_runs",
    "dedupe",
    "render",
    "truncate_if_needed",
    "MAX_COMMENT_BYTES",
    "REPORT_MARKER",
    "find_existing_comment",
    "post_comment",
    "post_checks",
]
