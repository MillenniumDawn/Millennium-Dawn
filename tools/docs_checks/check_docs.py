#!/usr/bin/env python3
"""Unified docs-site check runner.

Runs every docs-site check and produces a single combined report. Checks run
in three phases: source checks (parallel), the build (sequential), then
dist checks against the built site (parallel). Exit code is non-zero if any
check fails.

Usage:
    python3 check_docs.py                     # run all checks (build first)
    python3 check_docs.py --no-build          # skip the build, reuse dist/
    python3 check_docs.py --only link-syntax,flags
    python3 check_docs.py --list              # list available checks
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from common import DIST_DIR, REPO_ROOT, SITE_BASEURL, CheckResult, run_cmd
except ImportError:  # when imported as a package module
    from .common import DIST_DIR, REPO_ROOT, SITE_BASEURL, CheckResult, run_cmd

HERE = Path(__file__).resolve().parent

# The individual checks are sibling modules. Each exposes `run(...) -> (bool, str)`
# so the runner can call them in-process (one orchestrator, no subprocess fan-out).
# The check list below is the single source of truth for what runs and when.
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import check_accessibility_basics as _a11y  # noqa: E402
import check_content_html as _content_html  # noqa: E402
import check_docs_hygiene as _hygiene  # noqa: E402
import check_flag_images as _flags  # noqa: E402
import check_link_syntax as _link_syntax  # noqa: E402
import check_og_images as _og  # noqa: E402
import check_perf_budgets as _perf  # noqa: E402
import check_site_links as _links  # noqa: E402

# Bun/Node checks stay as subprocesses: they drive external tools, not Python.
_BUN_CHECKS = {
    "lint:md": ["bun", "run", "lint:md"],
    "astro check": ["bun", "run", "check"],
    "build": ["bun", "run", "build"],
}


def _timed(name: str, fn: Callable[[], tuple[bool, str]]) -> CheckResult:
    """Run an in-process check function and capture it as a CheckResult."""
    start = time.monotonic()
    try:
        passed, output = fn()
    except Exception as exc:  # noqa: BLE001 - surface as a failed check
        passed, output = False, f"Exception: {exc}"
    return CheckResult(name, passed, output.strip(), time.monotonic() - start)


# ---------------------------------------------------------------------------
# Source checks (no build required)
# ---------------------------------------------------------------------------


def check_link_syntax() -> CheckResult:
    return _timed("link-syntax", _link_syntax.run)


def check_content_html() -> CheckResult:
    return _timed("content-html", _content_html.run)


def check_flags() -> CheckResult:
    return _timed("flags", _flags.run)


def check_hygiene() -> CheckResult:
    return _timed("hygiene", lambda: _hygiene.run(REPO_ROOT))


def check_lint_md() -> CheckResult:
    return run_cmd("lint:md", _BUN_CHECKS["lint:md"])


# ---------------------------------------------------------------------------
# Build checks (sequential)
# ---------------------------------------------------------------------------


def check_astro() -> CheckResult:
    return run_cmd("astro check", _BUN_CHECKS["astro check"])


def check_build() -> CheckResult:
    return run_cmd("build", _BUN_CHECKS["build"])


# ---------------------------------------------------------------------------
# Dist checks (require a built site)
# ---------------------------------------------------------------------------


def _dist_check(name: str, fn: Callable[[], tuple[bool, str]]) -> CheckResult:
    if not DIST_DIR.exists():
        return CheckResult(name, False, "dist/ not found. Run build first.", 0.0)
    return _timed(name, fn)


def check_links() -> CheckResult:
    return _dist_check("links", lambda: _links.run(DIST_DIR, SITE_BASEURL))


def check_og() -> CheckResult:
    return _dist_check("og", lambda: _og.run(DIST_DIR, SITE_BASEURL))


def check_a11y() -> CheckResult:
    return _dist_check("a11y", lambda: _a11y.run(DIST_DIR))


def check_perf() -> CheckResult:
    return _dist_check("perf", lambda: _perf.run(DIST_DIR))


@dataclass
class Check:
    name: str
    phase: str  # "sources", "build", "dist"
    fn: Callable[[], CheckResult]


ALL_CHECKS: list[Check] = [
    Check("link-syntax", "sources", check_link_syntax),
    Check("content-html", "sources", check_content_html),
    Check("flags", "sources", check_flags),
    Check("hygiene", "sources", check_hygiene),
    Check("lint:md", "sources", check_lint_md),
    Check("astro check", "build", check_astro),
    Check("build", "build", check_build),
    Check("links", "dist", check_links),
    Check("og", "dist", check_og),
    Check("a11y", "dist", check_a11y),
    Check("perf", "dist", check_perf),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _run_parallel(checks: list[Check], max_workers: int) -> list[CheckResult]:
    results: list[CheckResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(c.fn): c for c in checks}
        for future in as_completed(futures):
            check = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001 - surface as a failed check
                results.append(CheckResult(check.name, False, f"Exception: {exc}", 0.0))
    return results


def run_checks(
    checks: list[Check],
    skip_build: bool = False,
    max_workers: int = 4,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    phases = ["sources", "build", "dist"] if not skip_build else ["sources", "dist"]
    build_ran = any(c.phase == "build" for c in checks) and not skip_build
    build_ok = True

    for phase in phases:
        phase_checks = [c for c in checks if c.phase == phase]
        if not phase_checks:
            continue

        if phase == "build":
            # Always sequential: astro check, then the build. Both drive the same
            # Vite/Astro pipeline, and the dist phase depends on the build output.
            for check in phase_checks:
                print(f"  Running {check.name}...")
                result = check.fn()
                results.append(result)
                if not result.passed:
                    build_ok = False
        elif phase == "dist" and build_ran and not build_ok:
            # No point checking a site that failed to build.
            for check in phase_checks:
                results.append(
                    CheckResult(check.name, False, "skipped: build failed", 0.0)
                )
        else:
            results.extend(_run_parallel(phase_checks, max_workers))

    return results


def print_report(results: list[CheckResult]) -> None:
    print("\n" + "=" * 60)
    print("Docs Site Check Report")
    print("=" * 60 + "\n")

    failed = [r for r in results if not r.passed]
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  {r.name:20s} {status}  ({r.duration:.1f}s)")

    print()

    if failed:
        print(f"FAILED ({len(failed)} of {len(results)} checks):\n")
        for r in failed:
            print(f"--- {r.name} ---")
            for line in r.output.splitlines()[-30:]:
                print(f"  {line}")
            print()
    else:
        print(f"ALL PASSED ({len(results)} checks).\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--no-build", action="store_true", help="Skip the build step.")
    parser.add_argument(
        "--only", type=str, default=None, help="Comma-separated check names to run."
    )
    parser.add_argument(
        "--list", action="store_true", help="List available checks and exit."
    )
    parser.add_argument(
        "--max-workers", type=int, default=4, help="Max parallel workers."
    )
    args = parser.parse_args()

    if args.list:
        for c in ALL_CHECKS:
            print(f"  {c.name:20s}  (phase: {c.phase})")
        return 0

    checks = ALL_CHECKS
    if args.only:
        names = {n.strip() for n in args.only.split(",")}
        unknown = names - {c.name for c in ALL_CHECKS}
        if unknown:
            print(f"Unknown checks: {', '.join(sorted(unknown))}")
            print(f"Available: {', '.join(c.name for c in ALL_CHECKS)}")
            return 1
        checks = [c for c in ALL_CHECKS if c.name in names]

    results = run_checks(checks, skip_build=args.no_build, max_workers=args.max_workers)
    print_report(results)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
