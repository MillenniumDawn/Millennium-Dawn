"""Keep the rendered comment body under GitHub's 65 536-byte issue comment cap.

The findings lists lead the report and are the only unbounded part of it, so
truncation trims them from the bottom up and keeps the tail — the per-category,
Mod tests and Tools tests tables, all bounded — intact, with a stub pointing at
the workflow artifact in between. The reviewer keeps the branch's first findings
and every count; the artifact download has the full data.
"""

from typing import List, Tuple

MAX_COMMENT_BYTES = 60_000  # headroom under GitHub's 65 536 hard limit

# Everything from the first of these to the end of the body is kept whole.
_TAIL_HEADINGS = ("## Findings by category", "## Mod tests", "## Tools tests")
# Headroom for the <details> tags a mid-block cut leaves to be closed.
_CLOSE_RESERVE = 200


def truncate_if_needed(
    body: str, artifact_url: str = "", workflow_run_url: str = ""
) -> Tuple[str, bool]:
    """Return (possibly_truncated_body, was_truncated).

    Truncation strategy: keep the marker, title, verdict and metadata, as much
    of the findings lists as fits, and the whole table tail; replace what was
    dropped with a short pointer to the workflow artifact or run.
    """
    if _size(body) <= MAX_COMMENT_BYTES:
        return body, False

    notice = _tail_notice(artifact_url, workflow_run_url)
    split = _find_tail_start(body)
    if split == -1:
        return _hard_slice(body, notice), True

    head, tail = body[:split], body[split:]
    budget = MAX_COMMENT_BYTES - _size(tail) - _size(notice) - _CLOSE_RESERVE
    if budget <= 0:
        # Tables alone blow the cap (a pathological report) — fall back to a
        # blind slice so something still posts.
        return _hard_slice(body, notice), True

    return _trim_findings(head, budget) + "\n" + notice + "\n" + tail, True


def _size(text: str) -> int:
    return len(text.encode("utf-8"))


def _find_tail_start(body: str) -> int:
    """Offset of the first table section heading, or -1 when there is none."""
    offset = 0
    for line in body.splitlines(keepends=True):
        if line.startswith(_TAIL_HEADINGS):
            return offset
        offset += len(line)
    return -1


def _trim_findings(head: str, budget: int) -> str:
    """Drop trailing lines until `head` fits, then close any orphaned block."""
    lines: List[str] = head.splitlines(keepends=True)
    size = _size(head)
    while lines and size > budget:
        size -= _size(lines[-1])
        lines.pop()
    text = "".join(lines).rstrip() + "\n"
    unclosed = text.count("<details") - text.count("</details>")
    if unclosed > 0:
        text += "\n" + "</details>\n" * unclosed
    return text


def _hard_slice(body: str, notice: str) -> str:
    truncated = body.encode("utf-8")[: MAX_COMMENT_BYTES - 500].decode(
        "utf-8", errors="ignore"
    )
    return truncated + notice


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
