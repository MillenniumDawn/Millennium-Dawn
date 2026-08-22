#!/usr/bin/env python
# Run auto-runnable validation scripts in parallel (cross-platform).
# Usage: python run_all_validators.py [--staged] [--strict] [--no-color] [--format json]
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, TextIO, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import disk_cache
from report_lib.dedupe import dedupe
from report_lib.models import Issue
from shared_utils import Colors

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PERSISTENCE_MARKER = ".persist-complete"
TOOLS_DIR = os.path.dirname(SCRIPTS_DIR)


# The manual texture audit needs the full gfx tree, which cache warm-up omits.
_AUTO_RUN_EXCLUDED_SCRIPTS = frozenset(
    (
        "validate_tools.py",
        "validate_staged.py",
        "run_all_validators.py",
        "validate_unused_textures.py",
    )
)

# Opt-in flags that only one validator understands, applied by its discovered
# `name` (validate_ideas.py -> "ideas"). The suite is non-strict by default, so
# these surface as warnings without gating. --missing-loc is intentionally left
# off — its ~7.8k backlog would drown the report; run it on demand instead.
_VALIDATOR_EXTRA_FLAGS: Dict[str, List[str]] = {
    "focus-tree": ["--missing-icons"],
}


def discover_validators() -> List[Tuple[str, str, str]]:
    """Return (name, script_name, label) for each auto-runnable validator."""
    validators = []
    for script_path in glob.glob(os.path.join(SCRIPTS_DIR, "validate_*.py")):
        script_name = os.path.basename(script_path)
        if script_name in _AUTO_RUN_EXCLUDED_SCRIPTS:
            continue
        name = script_name.replace("validate_", "").replace(".py", "").replace("_", "-")
        label = _extract_label_from_script(script_path, name)
        validators.append((name, script_name, label))
    validators.sort(key=lambda x: x[0])
    return validators


def _extract_label_from_script(script_path: str, fallback_name: str) -> str:
    """Extract human-readable label from validator script."""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        title_match = re.search(r'TITLE\s*=\s*["\']([^"\']+)["\']', content)
        if title_match:
            return title_match.group(1).replace("VALIDATION", "").strip()

        class_match = re.search(r"class\s+(\w+Validator)\s*\(", content)
        if class_match:
            class_name = class_match.group(1)
            return class_name.replace("Validator", "").replace("_", " ").strip()
    except Exception:
        pass

    return fallback_name.replace("-", " ").title()


def launch_validator(
    script_name: str, extra_flags: List[str], output_dir: str, name: str, mod_path: str
) -> Tuple[subprocess.Popen, TextIO]:
    """Launch a single validator as a background subprocess (non-blocking)."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    output_path = os.path.join(output_dir, f"{name}.txt")

    combined_flags: List[str] = []
    for flag in extra_flags + _VALIDATOR_EXTRA_FLAGS.get(name, []):
        if flag not in combined_flags:
            combined_flags.append(flag)

    cmd = [
        sys.executable,
        script_path,
        "--path",
        mod_path,
        "--output",
        output_path,
    ] + combined_flags

    # Capture stderr per validator so a crash leaves a traceback to read;
    # previously DEVNULL made crashes undiagnosable from the suite output.
    stderr_path = os.path.join(output_dir, f"{name}.stderr.log")
    try:
        stderr_fh = open(stderr_path, "w", encoding="utf-8", newline="")
    except OSError:
        raise
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=stderr_fh,
        )
    except OSError:
        stderr_fh.close()
        raise
    return proc, stderr_fh


def read_validator_counts(output_dir: str, name: str) -> Tuple[int, int]:
    """Read error/warning counts from a completed validator's JSON output."""
    json_path = os.path.join(output_dir, f"{name}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                issues = json.load(f)
                error_count = sum(1 for i in issues if i.get("severity") == "error")
                warning_count = sum(1 for i in issues if i.get("severity") == "warning")
                return error_count, warning_count
        except Exception:
            pass
    return 0, 0


def _print_stderr_tail(
    output_dir: str, name: str, max_lines: int = 15, stream=None
) -> None:
    """Print the tail of a crashed validator's captured stderr (the traceback)."""
    stderr_path = os.path.join(output_dir, f"{name}.stderr.log")
    try:
        with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().strip().splitlines()
    except OSError:
        return
    if not lines:
        return
    for line in lines[-max_lines:]:
        print(f"    {line}", file=stream)


def _issue_sort_key(issue: Dict):
    line = issue.get("line", 0)
    if not isinstance(line, int):
        line = 0
    return (
        str(issue.get("file", "")),
        line,
        str(issue.get("severity", "")),
        str(issue.get("category", "")),
        str(issue.get("message", "")),
    )


def collect_all_issues(
    output_dir: str, validators: List[Tuple[str, str, str]]
) -> List[Dict]:
    """Collect and semantically deduplicate validator sidecar issues."""
    collected: List[Issue] = []
    for name, _, _ in validators:
        json_path = os.path.join(output_dir, f"{name}.json")
        if not os.path.exists(json_path):
            continue
        try:
            with open(json_path, "r", encoding="utf-8") as handle:
                raw_issues = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Malformed validator sidecar: {json_path}") from exc
        if not isinstance(raw_issues, list) or not all(
            isinstance(issue, dict) for issue in raw_issues
        ):
            raise ValueError(f"Malformed validator sidecar: {json_path}")
        raw_issues.sort(key=_issue_sort_key)
        collected.extend(Issue.from_dict(issue, validator=name) for issue in raw_issues)
    return [issue.to_dict() for issue in dedupe(collected)]


def _format_issues_by_file(issues: List[Dict], lines: List[str]) -> None:
    """Append issues grouped by file, sorted by line number, to lines list."""
    by_file: Dict[str, List[Dict]] = {}
    for issue in issues:
        f = issue.get("file", "unknown")
        if f not in by_file:
            by_file[f] = []
        by_file[f].append(issue)

    for file_path, file_issues in sorted(by_file.items()):
        file_issues.sort(key=lambda i: i.get("line", 0))
        lines.append(f"  {file_path} ({len(file_issues)} issue(s))")
        for issue in file_issues:
            line_ref = f":{issue['line']}" if issue.get("line") else ""
            lines.append(
                f"    - {file_path}{line_ref}: [{issue.get('category', 'unknown')}] {issue.get('message', '')}"
            )
        lines.append("")


def generate_combined_report(
    output_dir: str,
    validators: List[Tuple[str, str, str]],
    crashed: Optional[List[str]] = None,
    use_colors: bool = True,
) -> str:
    """Generate a combined deduplicated report from all validators."""
    all_issues = collect_all_issues(output_dir, validators)
    crashed = crashed or []

    errors = [i for i in all_issues if i.get("severity") == "error"]
    warnings = [i for i in all_issues if i.get("severity") == "warning"]

    lines = []
    lines.append("=" * 80)
    lines.append("COMBINED VALIDATION REPORT")
    lines.append("=" * 80)
    lines.append(f"Total validators run: {len(validators)}")
    lines.append("")

    if not errors and not warnings and not crashed:
        lines.append("✓ ALL VALIDATIONS PASSED")
    else:
        if errors:
            lines.append(f"✗ {len(errors)} ERROR(S)")
            lines.append("")
            _format_issues_by_file(errors, lines)

        if warnings:
            lines.append(f"⚠ {len(warnings)} WARNING(S)")
            lines.append("")
            _format_issues_by_file(warnings, lines)

        if crashed:
            lines.append(f"💥 {len(crashed)} VALIDATOR(S) CRASHED (no output produced)")
            lines.append("")
            for name in crashed:
                lines.append(f"  - {name}")
            lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def _persist_sidecars(output_dir: str, persist_dir: str) -> None:
    """Copy every validator's JSON sidecar into persist_dir.

    The suite runs inside a TemporaryDirectory that is deleted on exit; the
    copies are the only per-validator results that survive. A validator that
    passed clean writes no sidecar, which is exactly the empty findings set a
    baseline wants from it. Copy errors raise: a silent partial persist would
    save a truncated baseline under a valid-looking meta.
    """
    try:
        os.makedirs(persist_dir, exist_ok=True)
    except OSError:
        raise
    marker_path = os.path.join(persist_dir, PERSISTENCE_MARKER)
    try:
        os.unlink(marker_path)
    except FileNotFoundError:
        pass
    for stale_path in glob.glob(os.path.join(persist_dir, "*.json")):
        try:
            os.unlink(stale_path)
        except FileNotFoundError:
            pass
    copied = 0
    for json_path in glob.glob(os.path.join(output_dir, "*.json")):
        try:
            shutil.copyfile(
                json_path, os.path.join(persist_dir, os.path.basename(json_path))
            )
        except OSError:
            raise
        copied += 1
    try:
        with open(marker_path, "w", encoding="utf-8", newline="") as marker:
            marker.write("complete\n")
    except OSError:
        raise
    print(
        f"Persisted {copied} validator result sidecar(s) to {persist_dir}",
        file=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser(description="Run all MD validators in parallel")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help=(
            "Bypass the .validation_cache/ disk cache for this run. Use when "
            "iterating on validator logic — cache keys on file stat, not on "
            "validator source, so logic changes are otherwise invisible until "
            "CACHE_VERSION bumps. Sets MD_NO_CACHE=1 for child validators."
        ),
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help=(
            "Delete the entire .validation_cache/ before running, then rebuild "
            "it from scratch this run. Use to reset a stale or oversized cache."
        ),
    )
    parser.add_argument(
        "--cache-max-age-days",
        type=float,
        default=7.0,
        help=(
            "Auto-clear .validation_cache/ when it is older than this many days "
            "(since creation/last clear), then rebuild. 0 disables. Default: 7."
        ),
    )
    parser.add_argument("--format", choices=["text", "json", "both"], default="text")
    parser.add_argument(
        "--output", "-o", type=str, help="Output file for combined report"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the mod folder (default: current directory)",
    )
    parser.add_argument(
        "--persist-results",
        type=str,
        default=None,
        help=(
            "Copy each validator's JSON sidecar into this directory before "
            "the run's temporary output is deleted. Used by the nightly "
            "baseline job to keep the per-validator results after the suite "
            "completes."
        ),
    )
    args = parser.parse_args()

    if args.no_color:
        for color in ("RED", "GREEN", "YELLOW", "CYAN", "ENDC"):
            setattr(Colors, color, "")

    extra_flags = []
    if args.staged:
        extra_flags.append("--staged")
    if args.strict:
        extra_flags.append("--strict")
    if args.no_color:
        extra_flags.append("--no-color")

    if args.no_cache:
        # subprocess.Popen inherits the parent env by default, so setting
        # this once here propagates to every spawned validator.
        os.environ["MD_NO_CACHE"] = "1"

    VALIDATORS = discover_validators()
    mod_path = os.path.abspath(args.path)

    human_stream = sys.stderr if args.format == "json" and not args.output else None

    if args.clear_cache:
        disk_cache.clear(mod_path)
        disk_cache.stamp_created(mod_path)
        print(
            "Cleared .validation_cache/ (rebuilding from scratch this run).",
            file=human_stream,
        )
    else:
        # Auto-reset a cache that's been accumulating orphaned rows (deleted
        # files, stale namespace hashes) for longer than the age limit.
        if disk_cache.clear_if_stale(mod_path, args.cache_max_age_days):
            print(
                f"Cache older than {args.cache_max_age_days:g} day(s) — "
                "cleared and rebuilding from scratch.",
                file=human_stream,
            )
        # Old CACHE_VERSION dirs are orphaned on a version bump (often 100k+
        # files); drop them so the cache doesn't grow without bound.
        pruned = disk_cache.prune_old_versions(mod_path)
        if pruned:
            print(
                f"Pruned stale cache version(s): {', '.join(sorted(pruned))}",
                file=human_stream,
            )

    # TemporaryDirectory guarantees cleanup even on crashes — the previous
    # mkdtemp + per-file os.remove pattern leaked the dir on every non-clean
    # run (strict failures, partial crashes, KeyboardInterrupt).
    with tempfile.TemporaryDirectory(prefix="md_validators_") as output_dir:
        exit_code = _run_suite(args, extra_flags, output_dir, VALIDATORS, mod_path)

    sys.exit(exit_code)


def _run_suite(args, extra_flags, output_dir, VALIDATORS, mod_path) -> int:
    human_stream = sys.stderr if args.format == "json" and not args.output else None
    print(
        f"{Colors.CYAN}{'=' * 80}{Colors.ENDC}\n"
        f"{Colors.CYAN}Running Millennium Dawn Validation Suite{Colors.ENDC}\n"
        f"{Colors.CYAN}{'=' * 80}{Colors.ENDC}\n",
        file=human_stream,
    )

    print(f"Discovered {len(VALIDATORS)} validators", file=human_stream)
    for name, script, label in VALIDATORS:
        print(f"  - {name}: {label}", file=human_stream)

    print(file=human_stream)

    # Unbounded subprocess fan-out is intentional: capping concurrency or
    # forcing per-child --workers starves the regex-heavy slow validators
    # (verified slower in practice; the suite is I/O-bound, not CPU-bound).
    processes = {}
    for name, script, _label in VALIDATORS:
        processes[name] = launch_validator(
            script, extra_flags, output_dir, name, mod_path
        )

    crashed_validators = []

    for name, _script, label in VALIDATORS:
        proc, stderr_fh = processes[name]
        returncode = proc.wait()
        stderr_fh.close()
        error_count, warning_count = read_validator_counts(output_dir, name)

        if error_count > 0 or warning_count > 0:
            print(
                f"{Colors.RED}✗ {label}{Colors.ENDC} ({error_count} errors, {warning_count} warnings)",
                file=human_stream,
            )
        elif returncode != 0:
            # Non-zero exit with no JSON output means the validator itself crashed
            print(
                f"{Colors.RED}✗ {label}{Colors.ENDC} (crashed, exit code {returncode})",
                file=human_stream,
            )
            _print_stderr_tail(output_dir, name, stream=human_stream)
            crashed_validators.append(label)
        else:
            print(f"{Colors.GREEN}✓ {label}{Colors.ENDC}", file=human_stream)

    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.ENDC}", file=human_stream)

    report = generate_combined_report(
        output_dir, VALIDATORS, crashed_validators, not args.no_color
    )
    combined_issues = collect_all_issues(output_dir, VALIDATORS)
    total_errors = sum(
        1 for issue in combined_issues if issue.get("severity") == "error"
    ) + len(crashed_validators)
    total_warnings = sum(
        1 for issue in combined_issues if issue.get("severity") == "warning"
    )

    if args.format in ("json", "both"):
        combined_json = {
            "validators": len(VALIDATORS),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "issues": combined_issues,
        }
        json_output = json.dumps(combined_json, indent=2)
        if args.output:
            if args.format == "json":
                json_path = args.output
            else:
                root, extension = os.path.splitext(args.output)
                json_path = (
                    f"{root}.json"
                    if extension.lower() == ".txt"
                    else f"{args.output}.json"
                )
            try:
                with open(json_path, "w", encoding="utf-8", newline="") as f:
                    f.write(json_output)
            except OSError:
                raise
        else:
            print(json_output)

    if args.format in ("text", "both"):
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8", newline="") as f:
                    f.write(report)
            except OSError:
                raise
            print(
                f"\n{Colors.YELLOW}Detailed report saved to: {args.output}{Colors.ENDC}",
                file=human_stream,
            )
        else:
            print(f"\n{report}")

    # Persist before the TemporaryDirectory cleanup in main() reclaims the
    # sidecars. Runs even when validators crashed so a failing night still
    # leaves the partial results to inspect (the nightly baseline job gates
    # its diff on this step's exit code, so a partial persist never becomes
    # the baseline).
    persist_dir = getattr(args, "persist_results", None)
    if persist_dir:
        _persist_sidecars(output_dir, persist_dir)

    if total_errors == 0 and total_warnings == 0:
        print(f"{Colors.GREEN}✓ ALL VALIDATIONS PASSED{Colors.ENDC}", file=human_stream)
    elif total_errors > 0:
        print(
            f"{Colors.RED}✗ VALIDATION FAILED \u2014 {total_errors} error(s), "
            f"{total_warnings} warning(s){Colors.ENDC}",
            file=human_stream,
        )
    else:
        print(
            f"{Colors.YELLOW}⚠ VALIDATION COMPLETED WITH WARNINGS \u2014 "
            f"{total_warnings} warning(s){Colors.ENDC}",
            file=human_stream,
        )

    # A crashed validator is infrastructure failure, not findings: it produced
    # no verdict at all, so it must fail the run regardless of --strict.
    if crashed_validators:
        return 1

    # Warnings are advisory everywhere else (per-validator --strict gates on
    # errors only; the CI legend says warnings never block) — match that here.
    return 1 if (args.strict and total_errors > 0) else 0


if __name__ == "__main__":
    main()
