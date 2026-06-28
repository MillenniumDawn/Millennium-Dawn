#!/usr/bin/env python3
"""Parallel dispatcher for the run-on-commit Millennium Dawn validators.

The commit-stage `md-validate-*` hooks each ran as a separate process, one after
another, and each re-discovered the staged files with its own `git diff`. This
folds them into a single hook that runs them concurrently.

Measurement (the commit-stage set, branch changeset, this machine):

  * serial, one hook after another ... ~1.13s
  * this dispatcher, in parallel ..... ~0.38s

Folding them into ONE process instead was measured to be *slower*: a single
process can only run validators serially, the per-validator full-repo
cross-reference scan (not process startup) dominates, and pooling thousands of
file contents in one `FileOpener` cache adds memory pressure that slows the
CPU-bound parsing. So each validator keeps its own process; the win is running
them at the same time.

This dispatcher:

  * discovers the staged files once and shares them via `MD_STAGED_FILES`, so
    no validator shells out to git;
  * runs only the validators whose file rules match a staged path (mirroring
    each hook's `files:` regex);
  * runs them concurrently, splitting cores between the outer fan-out and each
    validator's own worker pool so the two layers don't oversubscribe.

Only the commit-stage validators live here. The expensive cross-reference
validators are deliberately `stages: [manual]` (CI-gated) and must stay out, or
they would run on every commit — running the full suite on commit was measured
at ~7s warm, a large regression. Validators keyed off non-`.txt`/`.yml` files
(`validate_scripted_gui`, `validate_scripted_localisation`, `validate_defines`,
`validate_gfx_references`) also stay as their own hooks.

Opt out with `MD_SKIP_VALIDATE=1 git commit ...`.
"""

import argparse
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

TXT = ".txt"
YML = ".yml"


class _Spec:
    """One validator: script to run, the staged-path rules that trigger it,
    whether it runs with --strict (a few hooks are warning-only), and an
    optional exclude regex mirroring the hook's `exclude:` so the run-gate
    matches the current config exactly."""

    __slots__ = ("script", "rules", "strict", "exclude")

    def __init__(self, script, rules, strict=True, exclude=None):
        self.script = script
        self.rules = rules
        self.strict = strict
        self.exclude = re.compile(exclude) if exclude else None

    def matches(self, rel_paths):
        for path in rel_paths:
            if self.exclude and self.exclude.search(path):
                continue
            if any(path.startswith(p) and path.endswith(e) for p, e in self.rules):
                return True
        return False


# Only the commit-stage validators belong here. The expensive cross-reference
# validators (cosmetic_tags, localisation, focus_tree, variables, decisions,
# modifiers, scripted_params, simplifications, ...) are deliberately
# `stages: [manual]` in .pre-commit-config.yaml — CI gates them, they do NOT run
# on commit. Folding them in here would drag them back onto every commit, so
# this registry mirrors exactly the run-on-commit `md-validate-*` hooks (their
# `files:` patterns and --strict flags). Keep in sync when hooks change; the
# golden test in tools/tests/precommit_validate_test.py guards against drift.
_REGISTRY = [
    _Spec(
        "validate_style",
        [("", TXT)],
        exclude=r"Changelog\.txt$|AUTHORS\.txt$|descriptions.*\.txt$",
    ),
    _Spec(
        "validate_oob_units",
        [
            ("history/units/", TXT),
            ("common/units/", TXT),
            ("common/ai_templates/", TXT),
            ("common/scripted_effects/", TXT),
        ],
    ),
    _Spec(
        "validate_ai_roles",
        [("common/ai_strategy/", TXT), ("common/ai_templates/", TXT)],
    ),
    _Spec("validate_ai_navy", [("common/ai_navy/", TXT), ("common/units/", TXT)]),
    _Spec("validate_ai_equipment", [("common/ai_equipment/", TXT)], strict=False),
    _Spec(
        "validate_agency_upgrades",
        [
            ("common/intelligence_agency_upgrades/", TXT),
            ("common/on_actions/MD_auto_agency_on_actions.txt", ""),
            ("common/scripted_guis/00_MD_auto_agency_scripted_gui.txt", ""),
            ("localisation/english/MD_auto_agency_l_english.yml", ""),
        ],
    ),
    _Spec(
        "validate_ideas",
        [
            ("common/ideas/", TXT),
            ("common/national_focus/", TXT),
            ("common/decisions/", TXT),
            ("events/", TXT),
            ("localisation/english/", YML),
        ],
    ),
    _Spec("validate_events", [("events/", TXT)]),
]


def _discover_staged(mod_path, argv_files):
    """Staged paths relative to *mod_path*. Prefer the filenames pre-commit
    already matched (argv); fall back to git for manual invocation."""
    if argv_files:
        out = []
        for f in argv_files:
            out.append(os.path.relpath(os.path.abspath(f), mod_path))
        return out
    from shared_utils import get_staged_files

    staged = get_staged_files(mod_path, extensions=[TXT, YML]) or []
    return [os.path.relpath(f, mod_path) for f in staged]


def _run(spec, mod_path, env, no_color, inner_workers):
    cmd = [
        sys.executable,
        os.path.join("tools", "validation", f"{spec.script}.py"),
        "--staged",
        "--workers",
        str(inner_workers),
    ]
    if spec.strict:
        cmd.append("--strict")
    if no_color:
        cmd.append("--no-color")
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=mod_path, env=env, capture_output=True, text=True)
    return (
        spec.script,
        proc.returncode,
        proc.stdout,
        proc.stderr,
        time.perf_counter() - start,
    )


def main():
    if os.environ.get("MD_SKIP_VALIDATE"):
        print("MD_SKIP_VALIDATE set — skipping content validation.")
        return 0

    parser = argparse.ArgumentParser(description="MD parallel content validation")
    parser.add_argument("--path", default=os.getcwd())
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("files", nargs="*", help="staged files (from pre-commit)")
    args = parser.parse_args()

    mod_path = os.path.abspath(args.path)
    rel_paths = [p.replace("\\", "/") for p in _discover_staged(mod_path, args.files)]
    rel_paths = [p for p in rel_paths if p.endswith((TXT, YML))]
    if not rel_paths:
        print("No staged .txt/.yml content files — nothing to validate.")
        return 0

    selected = [spec for spec in _REGISTRY if spec.matches(rel_paths)]
    if not selected:
        print("No content validators match the staged files.")
        return 0

    # Share the staged list so no validator shells out to git. Paths are
    # repo-relative, which is what get_staged_files expects from the env var.
    env = dict(os.environ)
    env["MD_STAGED_FILES"] = "\n".join(rel_paths)

    cores = max(1, cpu_count())
    max_parallel = min(len(selected), cores)
    # Split cores between the outer fan-out and each validator's own worker pool.
    # Floor of 2 so the heavy full-repo scanners (cosmetic_tags, focus_tree)
    # keep some internal parallelism even on low-core machines, where dividing
    # cores evenly would otherwise starve them back to single-threaded.
    inner_workers = max(2, cores // max_parallel)
    print(
        f"MD content validation: {len(rel_paths)} staged file(s), "
        f"{len(selected)} validator(s), up to {max_parallel} in parallel "
        f"({inner_workers} worker(s) each)\n"
    )

    results = []
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = [
            pool.submit(_run, spec, mod_path, env, args.no_color, inner_workers)
            for spec in selected
        ]
        for fut in futures:
            results.append(fut.result())

    results.sort(key=lambda r: r[0])
    failed = 0
    for script, code, out, err, _elapsed in results:
        if code != 0:
            failed += 1
            print(f"\n{'─' * 72}\n✗ {script}\n{'─' * 72}")
            if out.strip():
                print(out.rstrip())
            if err.strip():
                print(err.rstrip())

    print(f"\n{'=' * 72}\nMD content validation summary\n{'=' * 72}")
    for script, code, _out, _err, elapsed in results:
        flag = "FAIL" if code != 0 else "ok  "
        print(f"  [{flag}] {script:<34} {elapsed * 1000:6.0f}ms")
    print("=" * 72)

    if failed:
        print(f"\n✗ {failed} validator(s) failed — commit blocked.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
