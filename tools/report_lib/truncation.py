"""Keep the rendered comment body under GitHub's 65 536-byte issue comment cap.

If the full body would exceed the cap we strip the two heavy sections — the
issues-by-file list and the raw-log collapsible — and replace them with a
stub pointing to the workflow artifact, keeping the summary table so the
reviewer still sees counts. The artifact download has the full data.
"""

from typing import Tuple

MAX_COMMENT_BYTES = 60_000  # headroom under GitHub's 65 536 hard limit


def truncate_if_needed(
    body: str, artifact_url: str = "", workflow_run_url: str = ""
) -> Tuple[str, bool]:
    """Return (possibly_truncated_body, was_truncated).

    Truncation strategy: keep the marker, title, metadata, and summary table;
    replace everything after the summary table with a short pointer to the
    workflow artifact or run.
    """
    if len(body.encode("utf-8")) <= MAX_COMMENT_BYTES:
        return body, False

    keep_up_to = _find_summary_table_end(body)
    if keep_up_to == -1:
        # Couldn't find the summary table — fall back to a hard byte slice
        # but still leave a visible note at the bottom.
        truncated = body.encode("utf-8")[: MAX_COMMENT_BYTES - 500].decode(
            "utf-8", errors="ignore"
        )
        return truncated + _tail_notice(artifact_url, workflow_run_url), True

    head = body[:keep_up_to]
    return head.rstrip() + "\n\n" + _tail_notice(artifact_url, workflow_run_url), True


def _find_summary_table_end(body: str) -> int:
    """Return the byte offset just after the summary table ends, or -1."""
    lines = body.splitlines(keepends=True)
    in_table = False
    offset = 0
    end_offset = -1
    for line in lines:
        if line.startswith("## Summary"):
            in_table = True
        elif in_table and line.startswith("## "):
            # Next H2 header — summary section ended at the previous line
            break
        elif in_table and line.strip().startswith("| **Total**"):
            # Found the totals row; end after this line and any trailing blank
            end_offset = offset + len(line)
        offset += len(line)

    if end_offset == -1 and in_table:
        # Summary header found but no totals row — keep everything we've seen
        end_offset = offset
    return end_offset


def _tail_notice(artifact_url: str, workflow_run_url: str) -> str:
    link = ""
    if artifact_url:
        link = f"[workflow artifact]({artifact_url})"
    elif workflow_run_url:
        link = f"the [step summary]({workflow_run_url})"
    else:
        link = "the step summary"
    return (
        "> ⚠ This report was too large for a single PR comment. "
        f"The full issue list is available in {link}.\n"
    )
