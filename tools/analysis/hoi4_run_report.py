#!/usr/bin/env python3
"""Classify a HOI4 run's error.log, after the game has actually exited.

The log is written progressively during load. Reading it while HOI4 is still
running gives a partial file that can look completely clean minutes before the
errors arrive, so `--wait` polls for the process to disappear rather than for
the file to stop changing. A settled mtime is not a finish signal.

Usage:
    python tools/analysis/hoi4_run_report.py --wait
    python tools/analysis/hoi4_run_report.py --baseline before.json
    python tools/analysis/hoi4_run_report.py --save-baseline before.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from typing import Dict, List, Optional, Tuple

DEFAULT_LOG = os.path.expanduser(
    r"~/Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log"
)

# [12:34:56][no_game_date][parser.cpp:1111]: Error: ...
_LINE_RE = re.compile(
    r"^\[(?P<clock>\d{2}:\d{2}:\d{2})\]"
    r"\[(?P<date>[^\]]*)\]"
    r"\[(?P<source>[a-z_]+\.cpp:\d+)\]:\s*(?P<body>.*)$"
)
_FILE_RE = re.compile(r"(?:in )?file: \"([^\"]+)\"|in ([\w/]+\.(?:txt|gui|gfx|yml))")
_NUM_RE = re.compile(r"\b\d+\b")

# Only drop a line that actually names a third-party mod. Matching on the audio
# subsystem alone would hide an audio error belonging to this mod and let a run
# carrying nothing else report zero.
_THIRD_PARTY = re.compile(r"ugc_\d+|mod/[\w.-]+\.mod|Invalid supported_version", re.I)

# Audio diagnostics with no third-party evidence. Counted and shown separately
# rather than dropped, because ownership cannot be established from the line.
_AUDIO = re.compile(
    r"pdx_audio|pdx_audiomusic|assetfactory_audio|44\.1kHz|already added", re.I
)


def hoi4_is_running() -> bool:
    """True while a hoi4 process is alive."""
    try:
        out = subprocess.run(
            ["tasklist"], capture_output=True, text=True, timeout=30
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return "hoi4" in out.lower()


def wait_for_exit(timeout: float, poll: float = 5.0) -> Tuple[bool, str]:
    """Block until HOI4 exits. Returns (exited, explanation)."""
    if not hoi4_is_running():
        return True, "HOI4 was not running; reading the log as-is"
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(poll)
        if not hoi4_is_running():
            # the final flush can trail process exit slightly
            time.sleep(2)
            return True, "HOI4 exited; log is complete"
    return False, f"HOI4 still running after {timeout:.0f}s - report is PARTIAL"


def _origin(body: str) -> Optional[str]:
    match = _FILE_RE.search(body)
    if not match:
        return None
    return (match.group(1) or match.group(2) or "").replace("\\", "/") or None


def _shape(body: str) -> str:
    """Collapse an error to its shape so repeats group together."""
    text = _FILE_RE.sub('file: "X"', body)
    return _NUM_RE.sub("N", text).strip()


def parse(path: str) -> Dict[str, object]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as handle:
            raw = handle.read()
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}")

    lines = raw.split("\n")
    mod: List[Tuple[str, str, str]] = []
    third_party = 0
    audio = 0
    runtime = 0
    clocks: List[str] = []

    for line in lines:
        if not line.strip():
            continue
        match = _LINE_RE.match(line)
        if not match:
            continue
        clocks.append(match.group("clock"))
        body = match.group("body")
        if _THIRD_PARTY.search(line):
            third_party += 1
            continue
        if _AUDIO.search(line):
            audio += 1
            continue
        if match.group("date") != "no_game_date":
            runtime += 1
        mod.append((match.group("source"), _origin(body) or "(no file)", _shape(body)))

    by_file = Counter(origin for _s, origin, _sh in mod)
    by_shape = Counter(f"{src} {shape}" for src, _o, shape in mod)

    return {
        "log": path,
        "total_lines": len([ln for ln in lines if ln.strip()]),
        "third_party": third_party,
        "audio": audio,
        "mod_errors": len(mod),
        "runtime_errors": runtime,
        "span": (clocks[0], clocks[-1]) if clocks else ("", ""),
        "by_file": dict(by_file.most_common()),
        "by_shape": dict(by_shape.most_common(25)),
    }


def render(report: Dict[str, object], baseline: Optional[Dict[str, object]]) -> str:
    out: List[str] = []
    span = report["span"]
    out.append(f"log      {report['log']}")
    out.append(f"span     {span[0]} -> {span[1]}")
    out.append(
        f"errors   {report['mod_errors']} from the mod"
        f"  ({report['runtime_errors']} after the game date started)"
    )
    out.append(f"ignored  {report['third_party']} third-party mod lines")
    out.append(f"audio    {report['audio']} audio diagnostics, ownership unclear")
    out.append("")

    by_file: Dict[str, int] = report["by_file"]  # type: ignore[assignment]
    if not by_file:
        if report.get("audio"):
            out.append(
                f"No mod errors, but {report['audio']} audio diagnostics were seen"
                " and could not be attributed."
            )
        else:
            out.append("No mod errors.")
    else:
        out.append("by file")
        for name, count in list(by_file.items())[:20]:
            out.append(f"  {count:6}  {name}")
        out.append("")
        out.append("by error shape")
        for shape, count in list(report["by_shape"].items())[:12]:  # type: ignore[union-attr]
            out.append(f"  {count:6}  {shape[:120]}")

    if baseline:
        out.append("")
        out.append("vs baseline")
        old: Dict[str, int] = baseline.get("by_file", {})  # type: ignore[assignment]
        names = sorted(set(by_file) | set(old))
        moved = False
        for name in names:
            delta = by_file.get(name, 0) - old.get(name, 0)
            if delta:
                moved = True
                out.append(f"  {delta:+6}  {name}")
        if not moved:
            out.append("  no change")
    return "\n".join(out)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default=DEFAULT_LOG)
    parser.add_argument(
        "--wait",
        action="store_true",
        help="block until HOI4 exits before reading (the log grows during load)",
    )
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--baseline", help="compare against a saved report")
    parser.add_argument(
        "--save-baseline", help="write this report for later comparison"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    partial = False
    if args.wait:
        exited, note = wait_for_exit(args.timeout)
        partial = not exited
        print(f"[{'ok' if exited else 'WARN'}] {note}", file=sys.stderr)
    elif hoi4_is_running():
        partial = True
        print(
            "[WARN] HOI4 is running; the log is still being written and this "
            "report may be incomplete. Use --wait.",
            file=sys.stderr,
        )

    report = parse(args.log)
    report["partial"] = partial

    baseline = None
    if args.baseline:
        with open(args.baseline, encoding="utf-8") as handle:
            baseline = json.load(handle)

    if args.save_baseline:
        with open(args.save_baseline, "w", encoding="utf-8", newline="") as handle:
            json.dump(report, handle, indent=2)

    print(json.dumps(report, indent=2) if args.json else render(report, baseline))
    if partial:
        return 2
    return 1 if report["mod_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
