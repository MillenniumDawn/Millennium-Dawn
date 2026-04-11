#!/usr/bin/env python
###############################################################################
# Run all validation scripts in parallel (cross-platform)
# Usage:
#   python run_all_validators.py [--staged] [--strict] [--no-color] [--format json]
###############################################################################
import argparse
import glob
import json
import os
import re
import sys
import tempfile
from typing import Dict, List, Tuple

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPTS_DIR)


def discover_validators(include_slow: bool = False) -> List[Tuple[str, str, str]]:
    """Auto-discover validators from the validation directory.

    Args:
        include_slow: If True, include slow validators (set-variables, unused-scripted, etc.)
    """
    validators = []

    # Validators that are slow and should be opt-in
    SLOW_VALIDATORS = {
        "set-variables",
        "unused-scripted",
        "unused-textures",
        "variables",
    }

    for script_path in glob.glob(os.path.join(SCRIPTS_DIR, "validate_*.py")):
        script_name = os.path.basename(script_path)

        if script_name in (
            "validate_tools.py",
            "validate_staged.py",
            "run_all_validators.py",
        ):
            continue

        name = script_name.replace("validate_", "").replace(".py", "").replace("_", "-")

        if not include_slow and name in SLOW_VALIDATORS:
            continue

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

    cmd = [
        sys.executable,
        script_path,
        "--path",
        mod_path,
        "--output",
        output_path,
    ] + extra_flags

    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


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
                    for issue in issues:
                        key = (
                            issue.get("file", ""),
                            issue.get("line", 0),
                            issue.get("severity", ""),
                            issue.get("category", ""),
                        )
                        if key not in seen_keys:
                            seen_keys.add(key)
                            issue["validator"] = name
                            all_issues.append(issue)
            except Exception:
                pass

    return all_issues


def generate_combined_report(
    output_dir: str, validators: List[Tuple[str, str, str]], use_colors: bool = True
) -> str:
    """Generate a combined deduplicated report from all validators."""
    all_issues = collect_all_issues(output_dir, validators)

    errors = [i for i in all_issues if i.get("severity") == "error"]
    warnings = [i for i in all_issues if i.get("severity") == "warning"]

    lines = []
    lines.append("=" * 80)
    lines.append("COMBINED VALIDATION REPORT")
    lines.append("=" * 80)
    lines.append(f"Total validators run: {len(validators)}")
    lines.append("")

    if not errors and not warnings:
        lines.append("✓ ALL VALIDATIONS PASSED")
    else:
        if errors:
            lines.append(f"✗ {len(errors)} ERROR(S)")
            lines.append("")

            by_file: Dict[str, List[Dict]] = {}
            for e in errors:
                f = e.get("file", "unknown")
                if f not in by_file:
                    by_file[f] = []
                by_file[f].append(e)

            for file_path, issues in sorted(by_file.items()):
                lines.append(f"  {file_path} ({len(issues)} issue(s))")
                for issue in issues:
                    lines.append(
                        f"    - [{issue.get('category', 'unknown')}] {issue.get('message', '')}"
                    )
                lines.append("")

        if warnings:
            lines.append(f"⚠ {len(warnings)} WARNING(S)")
            lines.append("")

            by_file: Dict[str, List[Dict]] = {}
            for w in warnings:
                f = w.get("file", "unknown")
                if f not in by_file:
                    by_file[f] = []
                by_file[f].append(w)

            for file_path, issues in sorted(by_file.items()):
                lines.append(f"  {file_path} ({len(issues)} issue(s))")
                for issue in issues:
                    lines.append(
                        f"    - [{issue.get('category', 'unknown')}] {issue.get('message', '')}"
                    )
                lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"


def main():
    parser = argparse.ArgumentParser(description="Run all MD validators in parallel")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-color", action="store_true")
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
        "--include-slow",
        action="store_true",
        help="Include slow validators (set-variables, unused-scripted, variables, unused-textures)",
    )
    args = parser.parse_args()

    if args.no_color:
        Colors.RED = ""
        Colors.GREEN = ""
        Colors.YELLOW = ""
        Colors.CYAN = ""
        Colors.NC = ""

    extra_flags = []
    if args.staged:
        extra_flags.append("--staged")
    if args.strict:
        extra_flags.append("--strict")
    if args.no_color:
        extra_flags.append("--no-color")

    output_dir = tempfile.mkdtemp()
    VALIDATORS = discover_validators(include_slow=args.include_slow)
    mod_path = os.path.abspath(args.path)

    print(
        f"{Colors.CYAN}{'=' * 80}{Colors.NC}\n"
        f"{Colors.CYAN}Running Millennium Dawn Validation Suite{Colors.NC}\n"
        f"{Colors.CYAN}{'=' * 80}{Colors.NC}\n"
    )

    print(f"Discovered {len(VALIDATORS)} validators")
    for name, script, label in VALIDATORS:
        print(f"  - {name}: {label}")

    if not args.include_slow:
        print(
            "\n  (Use --include-slow to also run: set-variables, unused-scripted, variables, unused-textures)"
        )
    print()

    # Launch all validators in parallel
    processes = {}
    for name, script, _label in VALIDATORS:
        processes[name] = launch_validator(
            script, extra_flags, output_dir, name, mod_path
        )

    # Collect results in order
    total_errors = 0
    total_warnings = 0

    for name, _script, label in VALIDATORS:
        returncode = processes[name].wait()
        error_count, warning_count = read_validator_counts(output_dir, name)

        if error_count > 0 or warning_count > 0:
            print(
                f"{Colors.RED}✗ {label}{Colors.NC} ({error_count} errors, {warning_count} warnings)"
            )
            total_errors += error_count
            total_warnings += warning_count
        elif returncode != 0:
            print(f"{Colors.RED}✗ {label}{Colors.NC} (exit code {returncode})")
            total_errors += 1
        else:
            print(f"{Colors.GREEN}✓ {label}{Colors.NC}")

    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.NC}")

    if total_errors == 0 and total_warnings == 0:
        print(f"{Colors.GREEN}✓ ALL VALIDATIONS PASSED{Colors.NC}")

        for name, _, _ in VALIDATORS:
            txt_path = os.path.join(output_dir, f"{name}.txt")
            json_path = os.path.join(output_dir, f"{name}.json")
            for path in [txt_path, json_path]:
                if os.path.exists(path):
                    os.remove(path)
        try:
            os.rmdir(output_dir)
        except:
            pass

        sys.exit(0)
    else:
        report = generate_combined_report(output_dir, VALIDATORS, not args.no_color)

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
                    f"\n{Colors.YELLOW}Detailed report saved to: {args.output}{Colors.NC}"
                )
            else:
                print()
                print(report)

        exit_code = 1 if args.strict else 0
        if total_errors > 0:
            print(
                f"{Colors.RED}✗ VALIDATION FAILED \u2014 {total_errors} error(s), "
                f"{total_warnings} warning(s){Colors.NC}"
            )
        else:
            print(
                f"{Colors.YELLOW}⚠ VALIDATION COMPLETED WITH WARNINGS \u2014 "
                f"{total_warnings} warning(s){Colors.NC}"
            )

        sys.exit(exit_code)


if __name__ == "__main__":
    main()
