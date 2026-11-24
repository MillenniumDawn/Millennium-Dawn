#!/usr/bin/env python3
"""Report how much of one country's scripted content fired in a headless run.

MD content logs every focus, decision and event option into game.log. This reads
the mod files for what a tag owns, reads the log for what fired, and prints the
difference per kind (focuses, decisions, events): fired over defined, the fired
list by first date, the never-fired list, and ids that fired but were not found
in the mod scan (a gap in this scan, not necessarily in the mod).

    python tools/analysis/content_coverage.py --tag BRA --log game.log
    python tools/analysis/content_coverage.py --tag BRA --log game.log --json
    python tools/analysis/content_coverage.py --tag BRA --log game.log \\
        --namespace brazil --namespace brazil_news

What a tag owns:

    focuses    `id = TAG_...` of every focus, shared_focus and joint_focus block in
               common/national_focus/*.txt (top level or inside a focus_tree).
    decisions  every decision named `TAG_...` inside a category block of
               common/decisions/*.txt (categories/ is not read).
    events     every top-level `*_event` block of events/*.txt whose namespace
               (the id before the first dot) is claimed. A namespace is claimed when
               TAG is the tag named most often (strictly) by `original_tag = X`
               directly in the top-level `trigger` of its events. A country's own
               namespace also holds events it sends abroad, so a few other tags are
               expected. `--namespace` (repeatable) replaces that rule.

The log names countries by display name, not tag, so log lines are matched by id
and not by who fired them. Counts are log lines, not completions: an effect that
logs twice counts twice, and every country that receives a claimed event counts.

What this misses:

    - Focuses and decisions without a `TAG_` prefix, such as shared generic ones.
    - A namespace whose events never test `original_tag = TAG` at the top level of
      `trigger` (an OR, a news event with no tag trigger), and a namespace where
      another tag leads or ties, whose TAG events are skipped. Name the namespaces
      with `--namespace`; the report prints the ones it used.
    - Events of a claimed namespace that belong to someone else: they count.
    - Events with no option, and options with no `log` line: they never reach the
      log, so they read as never fired.
    - A joint focus logged under its owner's prefix counts for the owner whoever
      completed it.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Copied from summarize_game_log.py: the MCP server loads tools files standalone,
# so this script cannot import it.
DATE_RE = re.compile(r"\[(\d{4})\.(\d{1,2})\.(\d{1,2})\.\d{1,2}\]")
PAYLOAD_RE = re.compile(r"\d{1,2}:\d{2}, \d{1,2} [A-Za-z]+, \d{4}: (.+?)\s*$")

CONTENT_DIRS = ("common/national_focus", "common/decisions", "events")
FOCUS_BLOCKS = {"focus", "shared_focus", "joint_focus"}
KINDS = ("focuses", "decisions", "events")
KIND_OF = {"Focus": "focuses", "Decision": "decisions"}

_NOISE_RE = re.compile(r'"[^"\n]*"|#[^\n]*')
_BRACE_RE = re.compile(r"[{}]")
_NAME_RE = re.compile(r"([\w.:@-]+)\s*=\s*$")
_ID_RE = re.compile(r"\bid\s*=\s*([\w.]+)")
_ORIGINAL_TAG_RE = re.compile(r"\boriginal_tag\s*=\s*(\w+)")


@dataclass
class Hit:
    first: str
    count: int = 0
    options: Counter[str] = field(default_factory=Counter)


def split_block(text: str) -> tuple[str, list[tuple[str, str]]]:
    """The text outside nested braces, and each nested block as (name, body)."""
    outer: list[str] = []
    blocks: list[tuple[str, str]] = []
    depth = last = start = 0
    name = ""
    for brace in _BRACE_RE.finditer(text):
        if brace.group() == "{":
            if depth == 0:
                outer.append(text[last : brace.start()])
                head = _NAME_RE.search(outer[-1])
                name = head.group(1) if head else ""
                start = brace.end()
            depth += 1
        elif depth:
            depth -= 1
            if depth == 0:
                blocks.append((name, text[start : brace.start()]))
                last = brace.end()
    outer.append(text[last:])
    return "".join(outer), blocks


def block_id(body: str) -> str | None:
    match = _ID_RE.search(split_block(body)[0])
    return match.group(1) if match else None


def texts_mentioning(directory: Path, needle: str) -> list[str]:
    """Text of each `*.txt` in directory that contains needle, minus strings and comments.

    Braces inside a string or comment would unbalance the block scan.
    """
    raw = (
        path.read_text(encoding="utf-8-sig") for path in sorted(directory.glob("*.txt"))
    )
    return [_NOISE_RE.sub("", text) for text in raw if needle in text]


def scan_focuses(root: Path, tag: str) -> list[str]:
    ids = []
    for text in texts_mentioning(root / "common" / "national_focus", f"{tag}_"):
        for name, body in split_block(text)[1]:
            blocks = split_block(body)[1] if name == "focus_tree" else [(name, body)]
            ids += [
                focus_id
                for kind, block in blocks
                if kind in FOCUS_BLOCKS
                and (focus_id := block_id(block))
                and focus_id.startswith(f"{tag}_")
            ]
    return ids


def scan_decisions(root: Path, tag: str) -> list[str]:
    ids = []
    for text in texts_mentioning(root / "common" / "decisions", f"{tag}_"):
        for _, category in split_block(text)[1]:
            ids += [
                name
                for name, _ in split_block(category)[1]
                if name.startswith(f"{tag}_")
            ]
    return ids


def namespace_of(event_id: str) -> str:
    return event_id.split(".", 1)[0]


def scan_events(root: Path) -> tuple[list[str], dict[str, Counter[str]]]:
    """Every event id, and how often each tag is an `original_tag` trigger per namespace."""
    ids = []
    tag_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for text in texts_mentioning(root / "events", ""):
        for name, body in split_block(text)[1]:
            if not name.endswith("_event"):
                continue
            outer, children = split_block(body)
            match = _ID_RE.search(outer)
            if not match:
                continue
            ids.append(match.group(1))
            for kind, block in children:
                if kind == "trigger":
                    tags = _ORIGINAL_TAG_RE.findall(split_block(block)[0])
                    tag_counts[namespace_of(match.group(1))].update(tags)
    return ids, tag_counts


def leads(counts: Counter[str], tag: str) -> bool:
    """Whether tag is named more often than any other tag."""
    return counts[tag] > max((n for t, n in counts.items() if t != tag), default=0)


def scan_static(
    root: Path, tag: str, namespaces: list[str]
) -> tuple[dict[str, list[str]], list[str]]:
    """Defined ids per kind, and the event namespaces they were taken from."""
    event_ids, tag_counts = scan_events(root)
    claimed = sorted(
        set(namespaces)
        or {ns for ns, counts in tag_counts.items() if leads(counts, tag)}
    )
    defined = {
        "focuses": scan_focuses(root, tag),
        "decisions": scan_decisions(root, tag),
        "events": [i for i in event_ids if namespace_of(i) in claimed],
    }
    return {kind: list(dict.fromkeys(ids)) for kind, ids in defined.items()}, claimed


def message_pattern(tag: str, namespaces: list[str]) -> re.Pattern[str]:
    """Matches a focus, decision or event-option message of the tag's content.

    Also used as a cheap `search` prefilter: the log is far larger than the
    handful of lines that matter.
    """
    names = "|".join(map(re.escape, namespaces)) or "(?!)"
    return re.compile(
        rf"(?P<kind>Focus|Decision) (?P<id>{re.escape(tag)}_\w+)"
        rf"|(?P<event>(?:{names})\.\d+)(?:\.(?P<option>\w+))?(?=\s|$)"
    )


def scan_log(path: Path, tag: str, namespaces: list[str]) -> dict[str, dict[str, Hit]]:
    """First date, count and options per fired id, for each kind."""
    pattern = message_pattern(tag, namespaces)
    hits: dict[str, dict[str, Hit]] = {kind: {} for kind in KINDS}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not pattern.search(line):
                continue
            payload = PAYLOAD_RE.search(line)
            dates = DATE_RE.findall(line)
            if not payload or not dates:
                continue
            match = pattern.match(payload.group(1).partition(": ")[2])
            if not match:
                continue
            kind = "events" if match["event"] else KIND_OF[match["kind"]]
            year, month, day = dates[-1]
            date = f"{year}-{int(month):02d}-{int(day):02d}"
            hit = hits[kind].setdefault(match["event"] or match["id"], Hit(first=date))
            hit.first = min(hit.first, date)
            hit.count += 1
            if match["option"]:
                hit.options[match["option"]] += 1
    return hits


def fired_row(entry_id: str, hit: Hit) -> dict:
    row = {"id": entry_id, "first": hit.first, "count": hit.count}
    if hit.options:
        row["options"] = dict(sorted(hit.options.items()))
    return row


def kind_report(defined: list[str], hits: dict[str, Hit]) -> dict:
    known = set(defined)
    by_date = sorted(hits.items(), key=lambda item: (item[1].first, item[0]))
    fired = [fired_row(i, h) for i, h in by_date if i in known]
    return {
        "defined": len(defined),
        "fired": len(fired),
        "percent": round(100 * len(fired) / len(defined), 1) if defined else None,
        "fired_list": fired,
        "never_fired": [i for i in defined if i not in hits],
        "fired_not_found": [fired_row(i, h) for i, h in by_date if i not in known],
    }


def build_report(
    tag: str,
    log: Path,
    defined: dict[str, list[str]],
    namespaces: list[str],
    hits: dict[str, dict[str, Hit]],
) -> dict:
    report = {"tag": tag, "log": str(log), "namespaces": namespaces}
    for kind in KINDS:
        report[kind] = kind_report(defined[kind], hits[kind])
    return report


def fired_line(row: dict) -> str:
    options = ", ".join(
        f"{option} x{count}" if count > 1 else option
        for option, count in row.get("options", {}).items()
    )
    suffix = f"  [{options}]" if options else ""
    return f"  {row['first']}  {row['count']:>5}x  {row['id']}{suffix}"


def format_text(report: dict) -> str:
    lines = [f"{report['tag']} content coverage ({report['log']})"]
    for kind in KINDS:
        data = report[kind]
        percent = "n/a" if data["percent"] is None else f"{data['percent']:.1f}%"
        lines.append(f"  {kind:<10} {data['fired']}/{data['defined']}  {percent}")
    lines.append(f"  event namespaces: {', '.join(report['namespaces']) or '(none)'}")
    for kind in KINDS:
        data = report[kind]
        sections = (
            ("fired, by first date", [fired_line(r) for r in data["fired_list"]]),
            ("never fired", [f"  {i}" for i in data["never_fired"]]),
            (
                "fired but not found in the scan",
                [fired_line(r) for r in data["fired_not_found"]],
            ),
        )
        for title, rows in sections:
            lines += ["", f"== {kind}: {title} ({len(rows)}) ==", *rows]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Report which of a tag's focuses, decisions and events fired in a game.log"
    )
    parser.add_argument("--tag", required=True, help="country tag, such as BRA")
    parser.add_argument("--log", required=True, type=Path, help="path to game.log")
    parser.add_argument(
        "--root", type=Path, default=REPO_ROOT, help="mod root (default: repo root)"
    )
    parser.add_argument(
        "--namespace",
        action="append",
        default=[],
        metavar="NS",
        help="event namespace to count; repeatable, replaces the original_tag rule",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON, not text")
    args = parser.parse_args(argv)
    tag = args.tag.upper()

    if not any((args.root / name).is_dir() for name in CONTENT_DIRS):
        sys.exit(f"error: no {', '.join(CONTENT_DIRS)} under {args.root}")
    try:
        defined, namespaces = scan_static(args.root, tag, args.namespace)
        hits = scan_log(args.log, tag, namespaces)
    except FileNotFoundError:
        sys.exit(f"error: file not found: {args.log}")
    except UnicodeDecodeError as error:
        sys.exit(f"error: input is not valid UTF-8: {error}")

    report = build_report(tag, args.log, defined, namespaces, hits)
    print(json.dumps(report, indent=2) if args.json else format_text(report))


if __name__ == "__main__":
    main()
