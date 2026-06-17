#!/usr/bin/env python
# Run all validation scripts in parallel (cross-platform).
# Usage: python run_all_validators.py [--staged] [--strict] [--no-color] [--format json]
import argparse
import glob
import json
import os
import re
import sys
import tempfile
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import Colors

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPTS_DIR)


_NON_VALIDATOR_SCRIPTS = frozenset(
    ("validate_tools.py", "validate_staged.py", "run_all_validators.py")
)

# Opt-in flags that only one validator understands, applied by its discovered
# `name` (validate_ideas.py -> "ideas"). The suite is non-strict by default, so
# these surface as warnings without gating. --missing-loc is intentionally left
# off — its ~7.8k backlog would drown the report; run it on demand instead.
_VALIDATOR_EXTRA_FLAGS: Dict[str, List[str]] = {
    "ideas": ["--missing-icons"],
    "focus-tree": ["--missing-icons"],
}


def discover_validators() -> List[Tuple[str, str, str]]:
    """Return (name, script_name, label) for every validate_*.py in this dir."""
    validators = []
    for script_path in glob.glob(os.path.join(SCRIPTS_DIR, "validate_*.py")):
        script_name = os.path.basename(script_path)
        if script_name in _NON_VALIDATOR_SCRIPTS:
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
):
    """Launch a single validator as a background subprocess (non-blocking)."""
    import subprocess

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
    stderr_fh = open(stderr_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=stderr_fh,
    )
    proc._md_stderr_fh = stderr_fh
    return proc


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


def _print_stderr_tail(output_dir: str, name: str, max_lines: int = 15) -> None:
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
        print(f"    {line}")


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
    """Collect all issues from validator output files."""
    all_issues = []
    seen_keys = set()

    for name, _, _ in validators:
        json_path = os.path.join(output_dir, f"{name}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    issues = json.load(f)
                    # Sort before the first-seen dedup: some validators emit
                    # same-key (file/line/severity/category) issues in
                    # nondeterministic order, which would otherwise make the
                    # surviving representative vary between runs.
                    issues.sort(key=_issue_sort_key)
                    for issue in issues:
                        # Message is part of the key — distinct findings on the
                        # same line (e.g. two missing loc keys) must both survive.
                        # Matches report_lib's dedupe key.
                        key = (
                            issue.get("file", ""),
                            issue.get("line", 0),
                            issue.get("severity", ""),
                            issue.get("category", ""),
                            issue.get("message", ""),
                        )
                        if key not in seen_keys:
                            seen_keys.add(key)
                            issue["validator"] = name
                            all_issues.append(issue)
            except Exception:
                pass

    return all_issues


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
    crashed: List[str] = None,
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
    args = parser.parse_args()

    if args.no_color:
        Colors.RED = ""
        Colors.GREEN = ""
        Colors.YELLOW = ""
        Colors.CYAN = ""
        Colors.ENDC = ""

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

    # TemporaryDirectory guarantees cleanup even on crashes — the previous
    # mkdtemp + per-file os.remove pattern leaked the dir on every non-clean
    # run (strict failures, partial crashes, KeyboardInterrupt).
    with tempfile.TemporaryDirectory(prefix="md_validators_") as output_dir:
        exit_code = _run_suite(args, extra_flags, output_dir, VALIDATORS, mod_path)

    sys.exit(exit_code)


def _run_suite(args, extra_flags, output_dir, VALIDATORS, mod_path) -> int:
    print(
        f"{Colors.CYAN}{'=' * 80}{Colors.ENDC}\n"
        f"{Colors.CYAN}Running Millennium Dawn Validation Suite{Colors.ENDC}\n"
        f"{Colors.CYAN}{'=' * 80}{Colors.ENDC}\n"
    )

    print(f"Discovered {len(VALIDATORS)} validators")
    for name, script, label in VALIDATORS:
        print(f"  - {name}: {label}")

    print()

    # Unbounded subprocess fan-out is intentional: capping concurrency or
    # forcing per-child --workers starves the regex-heavy slow validators
    # (verified slower in practice; the suite is I/O-bound, not CPU-bound).
    processes = {}
    for name, script, _label in VALIDATORS:
        processes[name] = launch_validator(
            script, extra_flags, output_dir, name, mod_path
        )

    total_errors = 0
    total_warnings = 0
    crashed_validators = []

    for name, _script, label in VALIDATORS:
        proc = processes[name]
        returncode = proc.wait()
        fh = getattr(proc, "_md_stderr_fh", None)
        if fh is not None:
            fh.close()
        error_count, warning_count = read_validator_counts(output_dir, name)

        if error_count > 0 or warning_count > 0:
            print(
                f"{Colors.RED}✗ {label}{Colors.ENDC} ({error_count} errors, {warning_count} warnings)"
            )
            total_errors += error_count
            total_warnings += warning_count
        elif returncode != 0:
            # Non-zero exit with no JSON output means the validator itself crashed
            print(
                f"{Colors.RED}✗ {label}{Colors.ENDC} (crashed, exit code {returncode})"
            )
            _print_stderr_tail(output_dir, name)
            crashed_validators.append(label)
            total_errors += 1
        else:
            print(f"{Colors.GREEN}✓ {label}{Colors.ENDC}")

    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.ENDC}")

    if total_errors == 0 and total_warnings == 0:
        print(f"{Colors.GREEN}✓ ALL VALIDATIONS PASSED{Colors.ENDC}")
        return 0

    report = generate_combined_report(
        output_dir, VALIDATORS, crashed_validators, not args.no_color
    )

    if args.format in ("json", "both"):
        combined_json = {
            "validators": len(VALIDATORS),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "issues": collect_all_issues(output_dir, VALIDATORS),
        }
        json_output = json.dumps(combined_json, indent=2)
        if args.output:
            with open(args.output.replace(".txt", ".json"), "w") as f:
                f.write(json_output)

    if args.format in ("text", "both"):
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(
                f"\n{Colors.YELLOW}Detailed report saved to: {args.output}{Colors.ENDC}"
            )
        else:
            print(f"\n{report}")

    if total_errors > 0:
        print(
            f"{Colors.RED}✗ VALIDATION FAILED \u2014 {total_errors} error(s), "
            f"{total_warnings} warning(s){Colors.ENDC}"
        )
    else:
        print(
            f"{Colors.YELLOW}⚠ VALIDATION COMPLETED WITH WARNINGS \u2014 "
            f"{total_warnings} warning(s){Colors.ENDC}"
        )

    # Warnings are advisory everywhere else (per-validator --strict gates on
    # errors only; the CI legend says warnings never block) — match that here.
    return 1 if (args.strict and total_errors > 0) else 0


if __name__ == "__main__":
    main()
