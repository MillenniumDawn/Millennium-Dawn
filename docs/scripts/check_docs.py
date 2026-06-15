#!/usr/bin/env python3
"""Unified docs-site check runner.

Runs all docs-site checks in parallel and produces a single combined report.
Exit code is non-zero if any check fails.

Usage:
    python3 scripts/check_docs.py              # run all checks (build first)
    python3 scripts/check_docs.py --no-build   # skip the build step
    python3 scripts/check_docs.py --only content-html,flags  # run specific checks
    python3 scripts/check_docs.py --list       # list available checks
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

DOCS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DOCS_ROOT.parent
DIST_DIR = DOCS_ROOT / "dist"


# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    passed: bool
    output: str
    duration: float


@dataclass
class Check:
    name: str
    phase: str  # "sources", "build", "dist"
    fn: Callable[[], CheckResult]


def _run(name: str, cmd: list[str], cwd: Path = DOCS_ROOT) -> CheckResult:
    start = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    duration = time.monotonic() - start
    output = (proc.stdout + proc.stderr).strip()
    return CheckResult(name=name, passed=proc.returncode == 0, output=output, duration=duration)


def check_content_html() -> CheckResult:
    return _run("content-html", [sys.executable, "scripts/check_content_html.py"])


def check_flags() -> CheckResult:
    return _run("flags", [sys.executable, "scripts/check_flag_images.py"])


def check_hygiene() -> CheckResult:
    return _run("hygiene", [sys.executable, "scripts/check_docs_hygiene.py", "--repo-root", str(REPO_ROOT)])


def check_lint_md() -> CheckResult:
    return _run("lint:md", ["bun", "run", "lint:md"])


def check_astro() -> CheckResult:
    return _run("astro check", ["bun", "run", "check"])


def check_build() -> CheckResult:
    return _run("build", ["bun", "run", "build"])


def check_links() -> CheckResult:
    if not DIST_DIR.exists():
        return CheckResult(name="links", passed=False, output="dist/ not found. Run build first.", duration=0)
    return _run("links", [sys.executable, "scripts/check_site_links.py", "--site-dir", str(DIST_DIR)])


def check_og() -> CheckResult:
    if not DIST_DIR.exists():
        return CheckResult(name="og", passed=False, output="dist/ not found. Run build first.", duration=0)
    return _run("og", [sys.executable, "scripts/check_og_images.py", "--site-dir", str(DIST_DIR)])


def check_a11y() -> CheckResult:
    if not DIST_DIR.exists():
        return CheckResult(name="a11y", passed=False, output="dist/ not found. Run build first.", duration=0)
    return _run("a11y", [sys.executable, "scripts/check_accessibility_basics.py", "--site-dir", str(DIST_DIR)])


def check_perf() -> CheckResult:
    if not DIST_DIR.exists():
        return CheckResult(name="perf", passed=False, output="dist/ not found. Run build first.", duration=0)
    return _run("perf", [sys.executable, "scripts/check_perf_budgets.py", "--site-dir", str(DIST_DIR)])


# The canonical order: sources (parallel), build (sequential), dist (parallel)
ALL_CHECKS: list[Check] = [
    Check(name="content-html", phase="sources", fn=check_content_html),
    Check(name="flags",       phase="sources", fn=check_flags),
    Check(name="hygiene",     phase="sources", fn=check_hygiene),
    Check(name="lint:md",     phase="sources", fn=check_lint_md),
    Check(name="astro check", phase="build",   fn=check_astro),
    Check(name="build",       phase="build",   fn=check_build),
    Check(name="links",       phase="dist",    fn=check_links),
    Check(name="og",          phase="dist",    fn=check_og),
    Check(name="a11y",        phase="dist",    fn=check_a11y),
    Check(name="perf",        phase="dist",    fn=check_perf),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_checks(
    checks: list[Check],
    skip_build: bool = False,
    max_workers: int = 4,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    phases = ["sources", "build", "dist"] if not skip_build else ["sources", "dist"]

    for phase in phases:
        phase_checks = [c for c in checks if c.phase == phase]
        if not phase_checks:
            continue

        if phase == "build" and len(phase_checks) == 1:
            # Build steps run sequentially
            for check in phase_checks:
                print(f"  Running {check.name}...")
                result = check.fn()
                results.append(result)
        else:
            # Run in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(c.fn): c for c in phase_checks}
                for future in as_completed(futures):
                    check = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = CheckResult(
                            name=check.name, passed=False,
                            output=f"Exception: {exc}", duration=0
                        )
                    results.append(result)

    return results


def print_report(results: list[CheckResult]) -> None:
    print("\n" + "=" * 60)
    print("Docs Site Check Report")
    print("=" * 60 + "\n")

    failed = []
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        icon = "  " if r.passed else "  "
        print(f"{icon} {r.name:20s} {status}  ({r.duration:.1f}s)")
        if not r.passed:
            failed.append(r)

    print()

    if failed:
        print(f"FAILED ({len(failed)} of {len(results)} checks):\n")
        for r in failed:
            print(f"--- {r.name} ---")
            # Show last 30 lines of output
            lines = r.output.splitlines()
            for line in lines[-30:]:
                print(f"  {line}")
            print()
    else:
        print(f"ALL PASSED ({len(results)} checks).\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-build", action="store_true", help="Skip the build step.")
    parser.add_argument("--only", type=str, default=None,
                        help="Comma-separated list of check names to run.")
    parser.add_argument("--list", action="store_true", help="List available checks and exit.")
    parser.add_argument("--max-workers", type=int, default=4, help="Max parallel workers.")
    args = parser.parse_args()

    if args.list:
        for c in ALL_CHECKS:
            print(f"  {c.name:20s}  (phase: {c.phase})")
        return 0

    checks = ALL_CHECKS
    if args.only:
        names = {n.strip() for n in args.only.split(",")}
        checks = [c for c in ALL_CHECKS if c.name in names]
        unknown = names - {c.name for c in ALL_CHECKS}
        if unknown:
            print(f"Unknown checks: {', '.join(sorted(unknown))}")
            print(f"Available: {', '.join(c.name for c in ALL_CHECKS)}")
            return 1

    results = run_checks(checks, skip_build=args.no_build, max_workers=args.max_workers)
    print_report(results)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
