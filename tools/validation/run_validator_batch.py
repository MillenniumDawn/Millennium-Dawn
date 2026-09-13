"""Run a selected set of validators with bounded parallelism.

Two consumers share this runner: the coding pipeline's batch jobs select by
detect-changes output groups (--batch with --changed-groups), and the PR
impact scan selects by changed files (--impact). A batch-manifest.json beside
the per-validators' log/sidecar pairs records the selection and execution
outcome for the trusted reporter.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Set, TextIO, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import run_all_validators
from shared_utils import Colors, split_cpu_budget
from validator_batches import BATCHES, ValidatorSpec, select_for_changed_files

RESULT_PREFIX = "validation-"
MANIFEST_NAME = "batch-manifest.json"


def parse_changed_groups(raw: str) -> Optional[Set[str]]:
    groups = {chunk for chunk in raw.replace(",", " ").split() if chunk}
    return groups or None


def selected_specs(batch: str, groups: Optional[Set[str]]) -> List[ValidatorSpec]:
    if batch not in BATCHES:
        raise SystemExit(
            f"Unknown batch '{batch}'. Known batches: {', '.join(sorted(BATCHES))}"
        )
    if groups is None:
        return list(BATCHES[batch])
    return [spec for spec in BATCHES[batch] if set(spec.groups) & groups]


def _output_paths(output_dir: str, name: str) -> Tuple[str, str]:
    stem = os.path.join(output_dir, f"{RESULT_PREFIX}{name}")
    return stem + ".log", stem + ".json"


def _count_severity(json_path: str, severity: str) -> int:
    try:
        with open(json_path, "r", encoding="utf-8") as handle:
            issues = json.load(handle)
        return sum(
            1
            for issue in issues
            if isinstance(issue, dict) and issue.get("severity") == severity
        )
    except (OSError, json.JSONDecodeError):
        return 0


def classify_result(spec, returncode: int, output_dir: str) -> Tuple[str, str]:
    """Classify a completed validator: ok / findings / crash / missing."""
    log_path, json_path = _output_paths(output_dir, spec.name)
    has_log = os.path.isfile(log_path)
    has_json = os.path.isfile(json_path)
    if returncode != 0 and not has_json:
        return "crash", f"exit code {returncode}"
    if returncode != 0:
        errors = _count_severity(json_path, "error")
        warnings = _count_severity(json_path, "warning")
        return "findings", f"{errors} error(s), {warnings} warning(s)"
    if not has_log or not has_json:
        missing = []
        if not has_log:
            missing.append(os.path.basename(log_path))
        if not has_json:
            missing.append(os.path.basename(json_path))
        return "missing", f"did not write {', '.join(missing)}"
    return "ok", ""


def _write_manifest(
    mode: str,
    batch: Optional[str],
    specs: List[ValidatorSpec],
    outcomes: Dict[str, Tuple[int, str]],
    output_dir: str,
) -> None:
    manifest = {
        "mode": mode,
        "batch": batch,
        "selected": [spec.name for spec in specs],
        "results": [
            {
                "name": spec.name,
                "script": spec.script,
                "strict": spec.strict,
                "returncode": outcomes[spec.name][0],
                "status": outcomes[spec.name][1],
            }
            for spec in specs
        ],
    }
    path = os.path.join(output_dir, MANIFEST_NAME)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def run_batch(specs: List[ValidatorSpec], args) -> int:
    mod_path = os.path.abspath(args.path)
    os.makedirs(args.output_dir, exist_ok=True)
    max_parallel, inner_workers = split_cpu_budget(len(specs))
    child_flags = ["--no-color", "--workers", str(inner_workers)]

    print(
        f"Running {len(specs)} validator(s), up to {max_parallel} at a time "
        f"({inner_workers} worker(s) each)",
        flush=True,
    )

    processes: Dict[str, Tuple[subprocess.Popen, TextIO]] = {}
    pending = list(specs)
    failures: List[str] = []
    outcomes: Dict[str, Tuple[int, str]] = {}

    def launch_next() -> None:
        if pending:
            spec = pending.pop(0)
            gate = ["--strict"] if spec.strict else []
            script = spec.script
            spec_flags = list(spec.args)
            if spec.runner == "standalone":
                script = "run_impact_standalone.py"
                spec_flags = ["--validator", spec.name] + spec_flags
            processes[spec.name] = run_all_validators.launch_validator(
                script,
                gate + child_flags + spec_flags,
                args.output_dir,
                f"{RESULT_PREFIX}{spec.name}",
                mod_path,
                output_filename=f"{RESULT_PREFIX}{spec.name}.log",
                apply_extra_flags=False,
            )

    for _ in range(max_parallel):
        launch_next()

    for spec in specs:
        proc, stderr_fh = processes[spec.name]
        returncode = proc.wait()
        stderr_fh.close()
        launch_next()

        status, detail = classify_result(spec, returncode, args.output_dir)
        outcomes[spec.name] = (returncode, status)
        if status == "ok":
            print(f"OK {spec.name} ({spec.script})", flush=True)
            continue
        failures.append(spec.name)
        print(
            f"FAILED {spec.name} ({spec.script}): {status} — {detail}",
            flush=True,
        )
        if status == "crash":
            run_all_validators._print_stderr_tail(
                args.output_dir, f"{RESULT_PREFIX}{spec.name}", stream=sys.stderr
            )

    _write_manifest(
        "impact" if getattr(args, "impact", False) else "batch",
        getattr(args, "batch", None),
        specs,
        outcomes,
        args.output_dir,
    )

    if failures:
        print(
            f"{len(failures)} of {len(specs)} validator(s) failed: "
            + ", ".join(sorted(failures)),
            flush=True,
        )
        return 1
    print(f"All {len(specs)} validator(s) passed.", flush=True)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a batch of MD validators")
    parser.add_argument("--batch", help="Batch name from validator_batches.BATCHES")
    parser.add_argument(
        "--changed-groups",
        default="",
        help="detect-changes outputs that are 'true' (default: all)",
    )
    parser.add_argument(
        "--impact",
        action="store_true",
        help="Select validators from the changed-file list instead of a batch",
    )
    parser.add_argument(
        "--changed-files-file",
        help="Newline-delimited changed paths for --impact selection",
    )
    parser.add_argument("--output-dir", default="validation-out")
    parser.add_argument("--path", default=".", help="Mod folder to validate")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)

    if args.no_color:
        for color in ("RED", "GREEN", "YELLOW", "CYAN", "ENDC"):
            setattr(Colors, color, "")

    if args.impact:
        # Impact scans bypass shared validator caches.
        os.environ["MD_NO_CACHE"] = "1"
        if not args.changed_files_file:
            parser.error("--impact requires --changed-files-file")
        with open(args.changed_files_file, "r", encoding="utf-8") as handle:
            changed = [line.strip() for line in handle if line.strip()]
        batch_specs, adhoc_specs = select_for_changed_files(changed)
        specs = batch_specs + adhoc_specs
        print(f"Changed files select {len(specs)} validator(s):")
        for spec in specs:
            print(f"  - {spec.name} ({spec.script})")
    else:
        if not args.batch:
            parser.error("either --batch or --impact is required")
        specs = selected_specs(args.batch, parse_changed_groups(args.changed_groups))
        print(f"Batch '{args.batch}' selects {len(specs)} validator(s):")
        for spec in specs:
            print(f"  - {spec.name} ({spec.script})")

    if not specs:
        os.makedirs(args.output_dir, exist_ok=True)
        _write_manifest(
            "impact" if args.impact else "batch",
            args.batch if not args.impact else None,
            [],
            {},
            args.output_dir,
        )
        print("Nothing to run; wrote an empty manifest.")
        return 0

    return run_batch(specs, args)


if __name__ == "__main__":
    sys.exit(main())
