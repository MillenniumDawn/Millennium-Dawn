"""Keep the rendered comment body under GitHub's 65 536-byte issue comment cap.

If the full body would exceed the cap we strip the new-findings list and
anything after the summary tables, and replace them with a stub pointing
to the workflow artifact. The verdict and tables stay so the reviewer
still sees counts. The artifact download has the full data.
"""

from typing import Tuple

MAX_COMMENT_BYTES = 60_000  # headroom under GitHub's 65 536 hard limit

_TABLE_HEADINGS = ("## Tools tests", "## Mod tests", "## Findings by category")


def truncate_if_needed(
    body: str, artifact_url: str = "", workflow_run_url: str = ""
) -> Tuple[str, bool]:
    """Return (possibly_truncated_body, was_truncated).

    Truncation strategy: keep the marker, title, metadata, and summary tables;
    replace everything after the tables with a short pointer to the
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


def _is_table_section_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("|"):
        return True
    if stripped.startswith("✅"):
        return True
    # Italic one-line notes the tables carry ("_No validator results found._",
    # "_…and N more categories._").
    if stripped.startswith("_") and stripped.endswith("_"):
        return True
    return False


def _find_summary_table_end(body: str) -> int:
    """Return the offset just after the last summary table section, or -1."""
    lines = body.splitlines(keepends=True)
    in_section = False
    offset = 0
    end_offset = -1
    for line in lines:
        if line.startswith(_TABLE_HEADINGS):
            in_section = True
            end_offset = offset + len(line)
        elif in_section and line.startswith("## "):
            break
        elif in_section and _is_table_section_line(line):
            end_offset = offset + len(line)
        elif in_section:
            break
        offset += len(line)
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
