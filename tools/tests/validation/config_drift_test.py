"""Drift guard between the two places the validator set is declared.

Every validator in `tools/validation/validate_*.py` is wired independently into
`.pre-commit-config.yaml` (the `md-validate-*` hooks) and into
`tools/validation/validator_batches.py` (the coding pipeline's batch jobs and
the PR-code impact scan). Those two lists are hand-maintained and drift: a
validator gets added to one and forgotten in the other, or `--strict` is set on
one side only. These tests fail when that happens, so the gap surfaces at PR
time instead of as a "passed locally, failed CI" surprise.

The workflow checks below also verify that every change group a batch validator
selects on is reachable through the validate-batch job condition and that
tool-test configuration files trigger the workflow that reads them.

Scope is `tools/validation/validate_*.py` only. The linting scripts in
`tools/linting/` (check_common_mistakes, fix_styling) are few, stable, and not
batch-driven, so they are out of scope here.

Intentional exceptions live in the EXEMPT / ALLOWED sets below, each with a
reason. The guard also checks those sets stay current: an exemption that no
longer applies (the validator got wired, or deleted) fails the test so the
stale entry gets removed.
"""

import os
import re
import subprocess
from fnmatch import fnmatch

import pytest
import yaml
from coverage import Coverage
from precommit_validate import _REGISTRY
from shared.paths import REPO_ROOT, VALIDATION_DIR
from validate_decisions import _DECISION_REFERENCE_SOURCE_PATTERNS
from validate_ideas import Validator as IdeaValidator
from validate_oob_units import (
    _CREATE_UNIT_SOURCE_PATTERNS,
    _DELETE_TEMPLATE_SOURCE_PATTERNS,
    _VARIANT_SOURCE_PATTERNS,
)
from validate_scripted_params import _CALLER_PATTERNS
from validate_staged import VALIDATORS as STAGED_VALIDATORS
from validator_batches import ALL_SPECS, BATCHES, ValidatorSpec

PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "coding-pipeline.yml"
TOOLS_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "tools-validation.yml"
IMPACT_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "validator-impact.yml"
IMPACT_REPORT_WORKFLOW = (
    REPO_ROOT / ".github" / "workflows" / "validator-impact-report.yml"
)
VALIDATOR_CACHE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "validator-cache.yml"
NIGHTLY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "nightly-pr-validation.yml"
PR_CACHE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-cache-cleanup.yml"

# Every tree the engine runs script from. Deliberately not derived from a
# validator's own pattern list: it is the independent expectation the caller
# patterns are checked against.
SCRIPT_ROOTS = ("common", "events", "history")


def _checks_matrix_steps(check_id: str) -> list:
    """Return the `checks` job steps that actually run for one matrix entry.

    Every lint/test step in that job is gated on `matrix.check.id`, so scanning
    the job's steps unconditionally would pass even after the entry that runs
    them was deleted from the matrix.
    """
    job = yaml.safe_load(TOOLS_WORKFLOW.read_text(encoding="utf-8"))["jobs"]["checks"]
    ids = {entry["id"] for entry in job["strategy"]["matrix"]["check"]}
    assert check_id in ids, (
        f"tools-validation has no `{check_id}` entry in the checks matrix — "
        "its steps are present but never run"
    )
    guard = f"matrix.check.id == '{check_id}'"
    family_guard = f"startsWith(matrix.check.id, '{check_id}')"
    return [
        step
        for step in job["steps"]
        if "if" not in step or guard in step["if"] or family_guard in step["if"]
    ]


def _sole_checkout(steps: list) -> dict:
    checkouts = [s for s in steps if s.get("uses", "").startswith("actions/checkout@")]
    assert (
        len(checkouts) == 1
    ), f"expected exactly one checkout for this matrix entry, got {len(checkouts)}"
    return checkouts[0]


def _tools_scope_script() -> str:
    workflow = yaml.safe_load(IMPACT_WORKFLOW.read_text(encoding="utf-8"))
    return next(
        step["run"]
        for step in workflow["jobs"]["impact"]["steps"]
        if step.get("name") == "Compute tools validation scope"
    )


def _run_tools_scope(tmp_path, changed_files: list[str]) -> str:
    changed = tmp_path / ".changed-files.txt"
    output = tmp_path / "github-output"
    with changed.open("w", encoding="utf-8", newline="") as handle:
        handle.write("".join(f"{path}\n" for path in changed_files))
    subprocess.run(
        ["bash", "-euo", "pipefail", "-c", _tools_scope_script()],
        cwd=tmp_path,
        env={**os.environ, "GITHUB_OUTPUT": str(output)},
        check=True,
        capture_output=True,
        text=True,
    )
    values = dict(
        line.split("=", 1)
        for line in output.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )
    return values["run"]


@pytest.mark.parametrize(
    ("changed_file", "expected"),
    [
        ("docs/README.md", "false"),
        ("common/national_focus/example.txt", "false"),
        ("events/example.txt", "false"),
        ("history/example.txt", "false"),
        ("localisation/english/example.yml", "false"),
        ("interface/example.gui", "false"),
        ("example.mod", "false"),
        ("tools/validation/validate_tools.py", "true"),
        ("common/on_actions/example.txt", "true"),
        ("common/scripted_effects/example.txt", "true"),
        (".claude/docs/typo-watchlist.md", "true"),
        ("resources/documentation/modifiers_documentation.md", "true"),
        (".pre-commit-config.yaml", "true"),
        ("pyproject.toml", "true"),
        ("package.json", "true"),
        ("bun.lock", "true"),
        (".jscpd.json", "true"),
        (".github/workflows/coding-pipeline.yml", "true"),
        (".github/workflows/nightly-pr-validation.yml", "true"),
        (".github/workflows/pr-cache-cleanup.yml", "true"),
        (".github/workflows/tools-validation.yml", "true"),
        (".github/workflows/validator-cache.yml", "true"),
        (".github/workflows/validator-impact.yml", "true"),
        (".github/workflows/validator-impact-report.yml", "true"),
    ],
)
def test_tools_scope_matches_former_tools_validation_paths(
    tmp_path, changed_file, expected
):
    assert _run_tools_scope(tmp_path, [changed_file]) == expected


# Validators intentionally absent from the CI batches. Each needs a reason.
CI_EXEMPT = {
    # Runs in the content-checks job, diff-scoped to the changed
    # .txt files (MD_STAGED_FILES from detect-changes' style_files output) so a
    # PR is gated on the style it introduced, not the repo-wide backlog. Can't
    # join the validate-batch jobs: those run full-repo with no diff-list
    # injection, which would resurface the whole backlog.
    "validate_style.py",
    # ~22k pre-existing unreferenced textures plus a slow full-repo scan make
    # this a periodic mod-size audit, not a per-PR gate. Manual hook only.
    "validate_unused_textures.py",
    # Runs in the standalone validate-paths job. It reads path names from the
    # git index, which the batch jobs don't have: they restore a content
    # bundle that carries no .git and omits map/.
    "validate_file_paths.py",
    # Runs in content-checks because descriptors are root files in the
    # prepared workspace and only need checking when a .mod file changes.
    "validate_mod_descriptors.py",
}

# Validators intentionally without a pre-commit hook. Each needs a reason.
PRECOMMIT_EXEMPT: set[str] = set()

# Validators whose --strict setting intentionally differs between pre-commit and
# CI, because of a pre-existing backlog. Clear the backlog, then remove the
# entry so both sides gate identically.
STRICT_MISMATCH_ALLOWED = {
    # CI runs --strict; pre-commit runs without it because pre-existing
    # equipment-coverage gaps would otherwise block every commit.
    "validate_ai_equipment.py",
}


def _discover_disk_validators():
    return {p.name for p in VALIDATION_DIR.glob("validate_*.py")}


def _dispatcher_routed():
    """validate_*.py folded into the parallel commit-stage dispatcher
    (tools/precommit_validate.py) instead of a standalone md-validate-* hook.

    The dispatcher runs them on commit, so they count as default-stage hooks
    with the --strict flag recorded in its registry."""
    return {
        f"{spec.script}.py": {"strict": spec.strict, "stage": "default"}
        for spec in _REGISTRY
    }


def _parse_precommit():
    """Map validate_*.py -> {'strict': bool, 'stage': 'default'|'manual'}.

    Includes both standalone `md-validate-*` hooks and the validators folded
    into the parallel commit-stage dispatcher."""
    cfg = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    result = {}
    for repo in cfg.get("repos", []):
        for hook in repo.get("hooks", []):
            entry = hook.get("entry", "")
            m = re.search(r"tools/validation/(validate_\w+\.py)", entry)
            if not m:
                continue
            stages = hook.get("stages") or []
            result[m.group(1)] = {
                "strict": "--strict" in entry,
                "stage": "manual" if "manual" in stages else "default",
            }
    # A standalone hook (e.g. the manual full-run) wins over the dispatcher entry.
    for script, meta in _dispatcher_routed().items():
        result.setdefault(script, meta)
    return result


def _parse_ci():
    """Map validate_*.py -> {'strict': bool} from the CI batch list."""
    return {spec.script: {"strict": spec.strict} for spec in ALL_SPECS}


def _spec_for(script: str):
    return next(spec for spec in ALL_SPECS if spec.script == script)


def _parse_ci_standalone():
    """Map validate_*.py -> {'strict': bool} for jobs that invoke one directly.

    The matrices name their script through `${{ matrix.validator.script }}`, so
    only the standalone jobs (content-checks, validate-paths) match here."""
    wf = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    result = {}
    for job in wf["jobs"].values():
        for step in job.get("steps", []):
            command = step.get("run") or ""
            for m in re.finditer(r"tools/validation/(validate_\w+\.py)", command):
                result[m.group(1)] = {"strict": "--strict" in command}
    return result


def _workflow_trigger(workflow):
    config = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    # PyYAML 1.1 parses the YAML 1.2 `on` key as boolean True.
    return config.get("on", config.get(True, {}))


def _pull_request_paths(workflow):
    # coding-pipeline runs on pull_request_target so fork PRs get a writable
    # token for the report comment; tools-validation stays on pull_request.
    trigger = _workflow_trigger(workflow)
    on_pr = trigger.get("pull_request") or trigger.get("pull_request_target") or {}
    return set(on_pr.get("paths", []))


def _filter_definitions():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    detect = workflow["jobs"]["detect-changes"]
    step = next(step for step in detect["steps"] if step.get("id") == "filter")
    return detect, yaml.safe_load(step["with"]["filters"])


def _dispatch_groups():
    """The group names the dispatch step forces to 'true'."""
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    detect = workflow["jobs"]["detect-changes"]
    step = next(step for step in detect["steps"] if step.get("id") == "dispatch")
    match = re.search(r"for out in (.*?);", step["run"], re.DOTALL)
    assert match, "dispatch step no longer loops over group names"
    return set(match.group(1).split())


def _reachable_group_outputs():
    """Every detect-changes output a batch validator may select on.

    Union of the paths-filter keys and the dispatch step's forced list; a
    group outside it can never be 'true' and the validator would never run."""
    _, filters = _filter_definitions()
    return set(filters) | _dispatch_groups()


def test_batch_groups_are_reachable_detect_changes_outputs():
    known = _reachable_group_outputs()
    offenders = sorted(
        {group for spec in ALL_SPECS for group in spec.groups if group not in known}
    )
    assert not offenders, (
        "Batch validators select on detect-changes outputs that no filter or "
        f"dispatch entry can set, so they would never run: {offenders}. Add a "
        "paths-filter entry or a dispatch group, or fix the spec's groups."
    )


def test_validate_batch_job_reaches_every_group_its_validators_use():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["validate-batch"]
    job_true_outputs = set(
        re.findall(r"needs\.detect-changes\.outputs\.([\w-]+)\s*==\s*'true'", job["if"])
    )
    needed = {group for spec in ALL_SPECS for group in spec.groups}
    unreachable = sorted(needed - job_true_outputs)
    assert not unreachable, (
        "validate-batch's job condition does not reference every changed "
        f"group its validators select on: {unreachable}. A PR touching only "
        "those files would skip the batch entirely."
    )


def test_validate_batch_matrix_lists_every_batch():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["validate-batch"]["strategy"]["matrix"]["batch"]
    assert sorted(matrix) == sorted(BATCHES)


@pytest.fixture(scope="module")
def disk():
    return _discover_disk_validators()


@pytest.fixture(scope="module")
def precommit():
    return _parse_precommit()


@pytest.fixture(scope="module")
def ci():
    return _parse_ci()


@pytest.fixture(scope="module")
def ci_standalone():
    return _parse_ci_standalone()


def test_every_disk_validator_runs_on_ci(disk, ci):
    missing = sorted(disk - set(ci) - CI_EXEMPT)
    assert not missing, (
        "Validators exist on disk but are not in the CI batch list "
        f"(validator_batches.py): {missing}. Add each to a batch in "
        "validator_batches.BATCHES, or add it to CI_EXEMPT with a reason."
    )


def test_every_disk_validator_runs_somewhere(disk, precommit, ci, ci_standalone):
    # A validator must run on pre-commit OR in CI, or it is dead code. The
    # expensive cross-reference validators run CI-only (their unused manual
    # pre-commit hooks were removed); unused_textures runs pre-commit-only.
    # Neither side is required alone, but a validator in NEITHER place runs
    # nowhere.
    orphaned = sorted(
        disk - set(precommit) - set(ci) - set(ci_standalone) - PRECOMMIT_EXEMPT
    )
    assert not orphaned, (
        f"Validators run neither on pre-commit nor in CI: {orphaned}. Wire each "
        "into .pre-commit-config.yaml or the CI batch list, or add to "
        "PRECOMMIT_EXEMPT with a reason."
    )


def test_ci_exempt_validators_run_on_precommit(disk, precommit, ci, ci_standalone):
    # CI_EXEMPT only means "not in a matrix". A validator that is also absent
    # from the standalone CI jobs has pre-commit as its only home, so it must be
    # wired there or it runs nowhere.
    homeless = sorted(
        (CI_EXEMPT & disk) - set(precommit) - set(ci) - set(ci_standalone)
    )
    assert not homeless, (
        f"CI-exempt validators with no pre-commit hook: {homeless}. They run "
        "nowhere — add a hook in .pre-commit-config.yaml."
    )


def test_strict_flags_match_between_precommit_and_ci(disk, precommit, ci):
    mismatches = [
        f"{s}: pre-commit strict={precommit[s]['strict']}, CI strict={ci[s]['strict']}"
        for s in sorted(set(precommit) & set(ci))
        if s not in STRICT_MISMATCH_ALLOWED
        and precommit[s]["strict"] != ci[s]["strict"]
    ]
    assert not mismatches, (
        "Validators run with different --strict settings on pre-commit vs CI:\n"
        + "\n".join(mismatches)
        + "\nReconcile them, or add to STRICT_MISMATCH_ALLOWED with a reason."
    )


def test_ci_exempt_entries_are_current(disk, ci):
    gone = sorted(CI_EXEMPT - disk)
    assert not gone, f"CI_EXEMPT names validators that no longer exist: {gone}."
    wired = sorted(CI_EXEMPT & set(ci))
    assert not wired, (
        f"CI_EXEMPT names validators that ARE now in the CI matrices: {wired}. "
        "Remove them from CI_EXEMPT."
    )


def test_precommit_exempt_entries_are_current(disk, precommit):
    gone = sorted(PRECOMMIT_EXEMPT - disk)
    assert not gone, f"PRECOMMIT_EXEMPT names validators that no longer exist: {gone}."
    wired = sorted(PRECOMMIT_EXEMPT & set(precommit))
    assert not wired, (
        f"PRECOMMIT_EXEMPT names validators that ARE now pre-commit hooks: {wired}. "
        "Remove them from PRECOMMIT_EXEMPT."
    )


def test_strict_mismatch_allowlist_is_current(disk, precommit, ci):
    gone = sorted(STRICT_MISMATCH_ALLOWED - disk)
    assert (
        not gone
    ), f"STRICT_MISMATCH_ALLOWED names validators that no longer exist: {gone}."
    resolved = sorted(
        s
        for s in STRICT_MISMATCH_ALLOWED
        if s in precommit and s in ci and precommit[s]["strict"] == ci[s]["strict"]
    )
    assert not resolved, (
        "STRICT_MISMATCH_ALLOWED names validators whose strict settings now "
        f"match — the mismatch is resolved: {resolved}. Remove them."
    )


def test_dispatch_forces_every_batch_group():
    # Dispatch runs have no diff; detect-changes must force every group a
    # batch validator selects on to 'true' so a dispatch scans everything.
    forced = _dispatch_groups()
    missing = sorted({group for spec in ALL_SPECS for group in spec.groups} - forced)
    assert not missing, (
        f"The dispatch step does not force {missing}, so dispatched runs "
        "silently skip those validators."
    )


def test_validator_cache_build_and_baseline_share_one_job():
    workflow = VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count("python3 tools/validation/run_all_validators.py") == 1
    assert "--persist-results .validation_baseline_candidate" in workflow
    assert "actions/upload-artifact" not in workflow
    assert "actions/download-artifact" not in workflow
    config = yaml.safe_load(workflow)
    assert set(config["jobs"]) == {"build-cache"}
    steps = config["jobs"]["build-cache"]["steps"]
    checkouts = [
        step for step in steps if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert len(checkouts) == 1
    assert checkouts[0]["with"]["persist-credentials"] is False
    verify = next(
        step
        for step in steps
        if step.get("name") == "Verify validation result candidate completion"
    )
    assert verify["run"] == "test -f .validation_baseline_candidate/.persist-complete"
    assert "--current .validation_baseline_candidate" in workflow
    baseline_diff = next(
        step for step in steps if step.get("name") == "Diff against previous baseline"
    )
    assert baseline_diff["env"]["TOOLSHASH"] == "${{ steps.toolshash.outputs.hash }}"
    assert '--toolshash "$TOOLSHASH"' in baseline_diff["run"]


def test_validator_cache_restore_is_source_hash_scoped():
    # Both shared cache entries (the disk cache and the validation baseline)
    # are keyed on the validator source hash: a validator change must
    # invalidate every restore, never hand a PR cache or baseline output from
    # a different validator generation. Scoped by restore path so a swapped
    # prefix can't hide behind the other entry's.
    expected_prefix = {
        ".validation_cache": (
            "md-valcache-v1-${{ runner.os }}-${{ steps.toolshash.outputs.hash }}-"
        ),
        ".validation_baseline": (
            "md-baseline-v1-${{ runner.os }}-${{ steps.toolshash.outputs.hash }}-"
        ),
    }
    restores = {path: [] for path in expected_prefix}
    for workflow in (CI_WORKFLOW, VALIDATOR_CACHE_WORKFLOW):
        config = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        for job in config["jobs"].values():
            for step in job.get("steps", []):
                if "actions/cache/restore@" not in step.get("uses", ""):
                    continue
                path = step.get("with", {}).get("path", "")
                if path not in restores:
                    # Workspace-bundle restores key on the merge tree, not the
                    # validator source hash — out of scope for this guard.
                    continue
                restores[path].extend(
                    step.get("with", {}).get("restore-keys", "").splitlines()
                )
    for path, expected in expected_prefix.items():
        assert restores[path], f"No {path} restores found across the two workflows"
        assert all(key.startswith(expected) for key in restores[path]), (
            f"{path} is restored with a key outside the current validator "
            "source-hash generation"
        )


def test_mio_validator_runs_for_localisation_changes():
    for output in ("mios", "localisation"):
        assert output in _spec_for("validate_mios.py").groups


def test_check_baseline_saves_only_on_clean_diff():
    # The save gating is the whole nightly alarm: baseline_check exits 1 on
    # new errors, and only `steps.diff.outcome == 'success'` reaches the
    # save step. If that `if` is dropped, a red night saves tonight's
    # regressed results as the new baseline and the alarm self-heals
    # silently.
    config = yaml.safe_load(VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8"))
    job = config["jobs"]["build-cache"]

    diff = next(step for step in job["steps"] if step.get("id") == "diff")
    assert "tools/baseline_check.py" in diff["run"]

    save = next(
        step for step in job["steps"] if step.get("name") == "Save validation baseline"
    )
    assert save["if"] == "steps.diff.outcome == 'success'"


def test_report_job_wires_baseline_flags():
    # The PR report only annotates when the workflow passes the restored
    # baseline and the matching toolshash; a drifted flag or path silently
    # drops the NEW/EXISTING annotation for every PR.
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["validation-report"]

    restore = next(
        step
        for step in job["steps"]
        if step.get("name") == "Restore validation baseline"
    )
    baseline_prefix = (
        "md-baseline-v1-${{ runner.os }}-${{ steps.toolshash.outputs.hash }}-"
    )
    assert baseline_prefix in restore["with"]["restore-keys"]

    run = next(
        step["run"]
        for step in job["steps"]
        if step.get("name") == "Generate and post validation report"
    )
    assert "--baseline-dir .validation_baseline" in run
    assert "--baseline-toolshash" in run


def test_tools_validation_triggers_for_consumed_configuration():
    paths = _pull_request_paths(TOOLS_WORKFLOW)
    assert paths == {
        "tools/**",
        "common/on_actions/**",
        "common/scripted_effects/**",
        ".claude/docs/typo-watchlist.md",
        "resources/documentation/modifiers_documentation.md",
        ".pre-commit-config.yaml",
        "pyproject.toml",
        "package.json",
        "bun.lock",
        ".jscpd.json",
        ".github/workflows/coding-pipeline.yml",
        ".github/workflows/nightly-pr-validation.yml",
        ".github/workflows/pr-cache-cleanup.yml",
        ".github/workflows/tools-validation.yml",
        ".github/workflows/validator-cache.yml",
        ".github/workflows/validator-impact.yml",
        ".github/workflows/validator-impact-report.yml",
    }


def test_python_quality_checks_are_wired_in_precommit_and_ci():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = {
        hook["id"]: hook for repo in config["repos"] for hook in repo.get("hooks", [])
    }
    assert {"black-tools", "pylint-tools", "mypy-tools"} <= hooks.keys()
    assert hooks["black-tools"]["entry"] == "black"
    assert hooks["black-tools"]["language"] == "python"
    assert "black==26.5.1" in hooks["black-tools"]["additional_dependencies"]
    assert "pylint tools" in hooks["pylint-tools"]["entry"]
    assert hooks["pylint-tools"]["language"] == "python"
    assert "pylint==4.0.6" in hooks["pylint-tools"]["additional_dependencies"]
    assert hooks["mypy-tools"]["entry"] == "mypy"
    assert hooks["mypy-tools"]["language"] == "python"
    assert "mypy==2.3.0" in hooks["mypy-tools"]["additional_dependencies"]

    steps = _checks_matrix_steps("quality")
    commands = "\n".join(s.get("run", "") for s in steps)
    assert "ruff check tools" in commands
    assert "black --check tools" in commands
    assert "pylint tools" in commands
    # mypy runs bare; its target list comes from [tool.mypy] files in pyproject.
    assert any(s.get("run", "").strip() == "mypy" for s in steps)

    unit = "\n".join(s.get("run", "") for s in _checks_matrix_steps("unit"))
    assert "coverage run" in unit
    assert "coverage report" in unit

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for package in ("black==", "coverage==", "mypy==", "pylint==", "ruff=="):
        assert package in pyproject
    assert Coverage().config.include_namespace_packages is True


def test_pytest_collection_gate_cannot_self_exclude():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = {
        hook["id"]: hook for repo in config["repos"] for hook in repo.get("hooks", [])
    }
    prepush_guard = hooks["tools-pytest-config"]["entry"]
    prepush_suite = hooks["tools-pytest"]["entry"]
    assert "tools/tests/collection_layout_test.py" in prepush_guard
    assert "-o addopts=" in prepush_guard
    assert "pytest tools/tests" in prepush_suite
    assert "-o addopts=" in prepush_suite
    assert "python_files=*_test.py" in prepush_suite

    steps = _checks_matrix_steps("unit")
    ci_guard = next(
        step
        for step in steps
        if step.get("name") == "Verify pytest collection configuration"
    )["run"]
    ci_suite = next(step for step in steps if step.get("name") == "Run unit tests")[
        "run"
    ]
    assert "tools/tests/collection_layout_test.py" in ci_guard
    assert "-o addopts=" in ci_guard
    assert "pytest tools/tests" in ci_suite
    assert "-o addopts=" in ci_suite
    assert "python_files=*_test.py" in ci_suite


def test_tools_checks_share_one_matrix():
    jobs = yaml.safe_load(TOOLS_WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    assert set(jobs) == {"checks"}
    entries = jobs["checks"]["strategy"]["matrix"]["check"]
    by_id = {entry["id"]: entry for entry in entries}
    assert set(by_id) == {"unit", "unit-macos", "unit-windows", "quality"}
    assert by_id["unit"]["runner"] == "ubuntu-latest"
    assert by_id["unit-macos"]["runner"] == "macos-latest"
    assert by_id["unit-windows"]["runner"] == "windows-latest"
    assert by_id["quality"]["runner"] == "ubuntu-latest"


def test_unit_tests_run_on_all_supported_platforms():
    job = yaml.safe_load(TOOLS_WORKFLOW.read_text(encoding="utf-8"))["jobs"]["checks"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    for name in (
        "Checkout (unit tests)",
        "Install dependencies (unit tests)",
        "Verify pytest collection configuration",
    ):
        assert "startsWith(matrix.check.id, 'unit')" in steps[name]["if"]

    assert (
        "--group dev --group runtime"
        in steps["Install dependencies (unit tests)"]["run"]
    )

    cross_platform = steps["Run cross-platform unit tests"]
    assert "unit-macos" in cross_platform["if"]
    assert "unit-windows" in cross_platform["if"]
    assert "pytest tools/tests" in cross_platform["run"]
    assert "-o addopts=" in cross_platform["run"]
    assert "python_files=*_test.py" in cross_platform["run"]


def test_impact_job_shares_staged_setup_and_runs_branch_scan_once():
    workflow = yaml.safe_load(IMPACT_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["impact"]
    steps = job["steps"]

    worktree_step = next(
        s for s in steps if s.get("name") == "Create isolated test worktree"
    )
    assert "git worktree add --detach" in worktree_step["run"]
    assert '"${{ github.sha }}"' in worktree_step["run"]
    assert "steps.tools-scope.outputs.run == 'true'" in worktree_step["if"]

    run_step = next(
        s for s in steps if s.get("name") == "Run staged-validator integration"
    )
    assert run_step["env"]["MD_RUN_STAGED_INTEGRATION"] == "1"
    assert "staged_validators_test.py" in run_step["run"]
    assert "staged_validators_real_test.py" in run_step["run"]
    assert "steps.dependencies.outcome == 'success'" in run_step["if"]
    assert "steps.tools-scope.outputs.run == 'true'" in run_step["if"]

    tools_step = next(s for s in steps if s.get("name") == "Run tools validation")
    assert "always()" in tools_step["if"]
    assert "steps.dependencies.outcome == 'success'" in tools_step["if"]
    assert "steps.tools-scope.outputs.run == 'true'" in tools_step["if"]
    assert "tools/validate_tools.py --strict" in tools_step["run"]
    upload = next(s for s in steps if s.get("name") == "Upload tools validation report")
    assert upload["with"]["if-no-files-found"] == "error"
    assert "steps.tools-scope.outputs.run == 'true'" in upload["if"]

    branch_step = next(
        s for s in steps if s.get("name") == "Run branch common-mistakes validation"
    )
    assert "always()" in branch_step["if"]
    assert "steps.dependencies.outcome == 'success'" in branch_step["if"]
    assert "steps.tools-scope.outputs.run == 'true'" in branch_step["if"]
    assert "batch-manifest.json" in branch_step["run"]
    assert branch_step["env"]["MD_NO_CACHE"] == "1"
    assert "validate_common_mistakes.py" in branch_step["run"]
    assert "--strict" in branch_step["run"]
    scope = next(s for s in steps if s.get("name") == "Compute tools validation scope")
    assert scope["id"] == "tools-scope"
    for path in (
        "tools/**",
        "common/on_actions/**",
        "common/scripted_effects/**",
        ".claude/docs/typo-watchlist.md",
        "resources/documentation/modifiers_documentation.md",
        ".pre-commit-config.yaml",
        "pyproject.toml",
        "package.json",
        "bun.lock",
        ".jscpd.json",
        ".github/workflows/coding-pipeline.yml",
        ".github/workflows/nightly-pr-validation.yml",
        ".github/workflows/pr-cache-cleanup.yml",
        ".github/workflows/tools-validation.yml",
        ".github/workflows/validator-cache.yml",
        ".github/workflows/validator-impact.yml",
        ".github/workflows/validator-impact-report.yml",
    ):
        assert path in scope["run"]
    assert "--staged" not in branch_step["run"]
    assert steps.index(branch_step) > steps.index(run_step)

    dependencies = next(s for s in steps if s.get("name") == "Install dependencies")
    assert dependencies["id"] == "dependencies"
    assert len([s for s in steps if "actions/checkout@" in s.get("uses", "")]) == 1

    # This job is the only home for staged integration after it moved from the
    # path-filtered tools matrix.
    tools_workflow = yaml.safe_load(TOOLS_WORKFLOW.read_text(encoding="utf-8"))
    ids = {
        entry["id"]
        for entry in tools_workflow["jobs"]["checks"]["strategy"]["matrix"]["check"]
    }
    assert "staged" not in ids


def test_quality_job_combines_lint_and_duplication_checks():
    steps = _checks_matrix_steps("quality")
    checkout = _sole_checkout(steps)
    assert {
        "tools",
        "pyproject.toml",
        "package.json",
        "bun.lock",
        ".jscpd.json",
    } <= set(checkout["with"]["sparse-checkout"].split())
    commands = "\n".join(step.get("run", "") for step in steps)
    assert "ruff check tools" in commands
    assert "black --check tools" in commands
    assert "pylint tools" in commands
    assert "mypy" in commands
    assert "bun install --frozen-lockfile" in commands
    assert "bun run jscpd" in commands
    for name in (
        "Run ruff",
        "Check formatting (black)",
        "Run pylint",
        "Run mypy",
    ):
        condition = next(step for step in steps if step.get("name") == name)["if"]
        assert "always()" in condition
        assert "!cancelled()" in condition
        assert "steps.quality-deps.outcome == 'success'" in condition

    bun = next(step for step in steps if step.get("name") == "Setup Bun")
    assert "always()" in bun["if"]
    assert "!cancelled()" in bun["if"]
    assert "steps.quality-checkout.outcome == 'success'" in bun["if"]
    assert "steps.quality-deps.outcome" not in bun["if"]
    bun_deps = next(
        step for step in steps if step.get("name") == "Install duplication dependencies"
    )
    assert "steps.bun.outcome == 'success'" in bun_deps["if"]
    jscpd = next(step for step in steps if step.get("name") == "Run jscpd")
    assert "steps.bun-deps.outcome == 'success'" in jscpd["if"]


def test_tools_tests_checkout_consumed_configuration():
    # These paths must be present in the entry that actually runs pytest, not
    # merely somewhere in the workflow.
    checkout = _sole_checkout(_checks_matrix_steps("unit"))
    sparse = checkout.get("with", {}).get("sparse-checkout")
    if sparse is None:
        return  # full checkout exposes everything
    required = {
        ".pre-commit-config.yaml",
        ".claude/docs/typo-watchlist.md",
        "common",
        "resources",
        ".github/workflows/coding-pipeline.yml",
        ".github/workflows/validator-cache.yml",
        ".github/workflows/nightly-pr-validation.yml",
        ".github/workflows/pr-cache-cleanup.yml",
        ".github/workflows/tools-validation.yml",
        ".github/workflows/validator-impact.yml",
        ".github/workflows/validator-impact-report.yml",
        "pyproject.toml",
    }
    missing = sorted(required - set(sparse.split()))
    assert not missing, (
        "the tools-validation unit-test checkout does not expose "
        f"{missing} — the tests that read them silently pass on absent files"
    )


def test_manual_texture_audit_always_runs():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hook = next(
        hook
        for repo in config["repos"]
        for hook in repo.get("hooks", [])
        if hook.get("id") == "md-validate-unused-textures"
    )
    assert hook.get("always_run") is True
    assert hook.get("pass_filenames") is False


def test_ci_strict_gate_lives_in_the_batch_specs():
    # The batch runner passes --strict per spec. ValidatorSpec defaults to
    # strict=True, so a spec added without the field gates — never fail open
    # by default. The two WARNING-only informational validators are the only
    # deliberate opt-outs.
    assert ValidatorSpec("x", "validate_x.py", ("common",)).strict is True
    informational = sorted(spec.name for spec in ALL_SPECS if not spec.strict)
    assert informational == ["building-guards", "simplifications"]


def test_ci_redundant_modifier_gate_is_strict():
    assert _spec_for("validate_modifiers.py").strict is True


def test_ci_idea_icon_check_is_enabled():
    # The CI run passes no opt-in flag, so the check has to be default-on in
    # the validator itself — asserting the absent flag proves nothing alone.
    assert _spec_for("validate_ideas.py").args in ((), None)

    validator = IdeaValidator("/nonexistent", use_colors=False, workers=1)
    called = []
    validator._parse_all_ideas = lambda: ({}, {}, {})
    validator.validate_missing_icons = lambda defined_ideas: called.append(
        defined_ideas
    )
    for name in (
        "validate_undefined_idea_refs",
        "validate_idea_quality",
        "validate_category_icon_frames",
        "validate_unused_ideas",
    ):
        setattr(validator, name, lambda *a, **k: None)
    validator.run_validations()
    assert called, "validate_ideas.run_validations no longer runs the icon check"

    # CI has no HOI4 install, so the check resolves mod sprites from the
    # restored interface/ and vanilla names from the committed manifest.
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    paths = set(workflow["env"]["WORKSPACE_PATHS"].split())
    assert {"interface", "tools"} <= paths
    assert (VALIDATION_DIR / "vanilla_sprites.txt").is_file()


def test_scripted_param_patterns_scan_every_script_root():
    """Each script tree must be scanned whole, not by named subdirectories.

    The hand-maintained caller list this replaced missed six live directories.
    Any narrowing back to `common/<dir>/**` reintroduces that blind spot, so
    assert the patterns still cover each root wholesale.
    """
    whole_tree = {
        pattern.split("/", 1)[0]
        for pattern in _CALLER_PATTERNS
        if pattern.split("/", 1)[1:] == ["**/*.txt"]
    }
    missed = sorted(root for root in SCRIPT_ROOTS if root not in whole_tree)
    assert not missed, (
        f"_CALLER_PATTERNS no longer scans {missed} whole, so callers in any "
        f"directory it does not name are never validated: {_CALLER_PATTERNS}"
    )


def test_scripted_param_routes_cover_every_caller_source():
    caller_dirs = {pattern.split("*", 1)[0] for pattern in _CALLER_PATTERNS}
    staged = next(
        spec for spec in STAGED_VALIDATORS if spec["name"] == "scripted params"
    )
    assert caller_dirs <= set(staged["prefixes"])

    _, filters = _filter_definitions()
    spec = _spec_for("validate_scripted_params.py")
    for directory in caller_dirs:
        output = directory.rstrip("/").rsplit("/", 1)[-1].replace("_", "-")
        sample = directory + "_scripted_param_probe.txt"
        assert any(fnmatch(sample, pattern) for pattern in filters[output])
        assert output in spec.groups


def test_oob_routes_cover_every_create_unit_and_variant_source():
    # Derived from the validator's own glob lists, not a copy of them: a
    # directory added there must reach every route or a PR touching only it
    # never runs. The three lists nest today (variant < create_unit < delete),
    # so the union is only insurance against them being decoupled later.
    dirs = {
        p.rsplit("/", 1)[0] + "/"
        for p in (
            _CREATE_UNIT_SOURCE_PATTERNS
            + _DELETE_TEMPLATE_SOURCE_PATTERNS
            + _VARIANT_SOURCE_PATTERNS
        )
    }
    _, filters = _filter_definitions()
    assert {d + "**" for d in dirs} <= set(filters["oob"])
    spec = next(s for s in _REGISTRY if s.script == "validate_oob_units")
    assert dirs <= {prefix for prefix, _ in spec.rules}


def test_decision_filter_covers_every_reference_source():
    _, filters = _filter_definitions()
    assert set(_DECISION_REFERENCE_SOURCE_PATTERNS) <= set(filters["decisions"])


def test_gfx_reference_validator_runs_for_all_reference_sources():
    assert {"interface", "common", "events", "history", "localisation"} <= set(
        _spec_for("validate_gfx_references.py").groups
    )


def test_scripted_localisation_core_runs_for_interface_changes():
    # The scripted-localisation validator selects on the core group union,
    # which is where interface changes reach it.
    assert "interface" in _spec_for("validate_scripted_localisation.py").groups


def test_pr_target_pipeline_runs_for_conflicted_and_clean_prs():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    trigger = _workflow_trigger(CI_WORKFLOW)
    assert "pull_request" not in trigger
    assert set(trigger["pull_request_target"]["types"]) == {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    }
    assert "paths" not in trigger["pull_request_target"]
    report = workflow["jobs"]["validation-report"]
    assert report["if"] == "${{ always() && !cancelled() }}"
    assert report["permissions"]["pull-requests"] == "write"
    report_checkout = next(
        step
        for step in report["steps"]
        if step.get("name") == "Checkout report tooling"
    )
    assert report_checkout["with"]["repository"] == "${{ github.repository }}"
    report_ref = report_checkout["with"]["ref"]
    assert "needs.detect-changes.outputs.base-sha" in report_ref
    assert "github.event.pull_request.base.sha" in report_ref
    assert "github.event.pull_request.head.sha" not in report_ref


def test_validation_checkout_uses_the_live_pr_head():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    detect = workflow["jobs"]["detect-changes"]
    resolver = next(step for step in detect["steps"] if step.get("id") == "resolve-ref")
    script = resolver["run"]
    assert ".merge_commit_sha" not in script
    assert "git/ref/pull/" not in script
    assert 'head_repository="${EVENT_HEAD_REPOSITORY:-$GITHUB_REPOSITORY}"' in script
    assert 'head_sha="${EVENT_HEAD_SHA:-$GITHUB_SHA}"' in script
    assert 'base_sha="${INPUT_BASE_SHA:-$EVENT_BASE_SHA}"' in script
    assert 'requested_head_sha="$INPUT_HEAD_SHA"' in script
    assert "The PR head changed before validation was dispatched" in script
    assert 'echo "repository=$head_repository"' in script
    assert 'echo "ref=$head_sha"' in script
    assert 'echo "head-sha=$head_sha"' in script
    assert 'echo "base-sha=$base_sha"' in script
    assert detect["outputs"]["head-sha"] == "${{ steps.resolve-ref.outputs.head-sha }}"
    assert detect["outputs"]["base-sha"] == "${{ steps.resolve-ref.outputs.base-sha }}"
    assert detect["outputs"]["checkout-ref"] == "${{ steps.resolve-ref.outputs.ref }}"
    trigger = _workflow_trigger(CI_WORKFLOW)
    inputs = trigger["workflow_dispatch"]["inputs"]
    assert inputs["pr_number"]["required"] is False
    assert inputs["head_sha"]["type"] == "string"
    assert "inputs.head_sha" in workflow["run-name"]
    assert "inputs.base_sha" in workflow["run-name"]

    for job_name in ("prepare-workspace", "validate-paths"):
        job = workflow["jobs"][job_name]
        checkout = next(
            step
            for step in job["steps"]
            if step.get("uses", "").startswith("actions/checkout@")
        )
        assert (
            checkout["with"]["ref"]
            == "${{ needs.detect-changes.outputs.checkout-ref }}"
        )
        assert checkout["with"]["repository"] == (
            "${{ needs.detect-changes.outputs.checkout-repository }}"
        )
        assert checkout["with"]["persist-credentials"] is False


def test_prepare_workspace_uses_trusted_tools_and_run_artifact():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    prepare = workflow["jobs"]["prepare-workspace"]
    checkouts = [
        step
        for step in prepare["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert len(checkouts) == 2
    pr_checkout, trusted_checkout = checkouts
    assert "tools" not in pr_checkout["with"]["sparse-checkout"]
    assert "*.mod" in pr_checkout["with"]["sparse-checkout"]
    assert pr_checkout["with"]["sparse-checkout-cone-mode"] is False
    link_guard = next(
        step
        for step in prepare["steps"]
        if step.get("name") == "Reject links in PR content"
    )
    assert "120000|160000" in link_guard["run"]
    assert trusted_checkout["with"]["path"] == "trusted"
    assert trusted_checkout["with"]["repository"] == "${{ github.repository }}"
    assert (
        trusted_checkout["with"]["ref"]
        == "${{ needs.detect-changes.outputs.base-sha }}"
    )
    assert set(trusted_checkout["with"]["sparse-checkout"].split()) >= {
        "tools",
        "resources/documentation",
        ".claude",
        "CLAUDE.md",
    }
    install = next(
        step
        for step in prepare["steps"]
        if step.get("name") == "Install trusted tooling"
    )
    assert "cp -a trusted/tools ." in install["run"]
    upload = next(
        step
        for step in prepare["steps"]
        if step.get("name") == "Upload prepared workspace"
    )
    assert upload["with"]["name"] == "prepared-workspace"
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "actions/cache/save@" not in workflow_text
    assert "actions/cache@" not in workflow_text

    report = workflow["jobs"]["validation-report"]
    assert "prepare-workspace" in report["needs"]
    assert prepare["env"]["HEAD_SHA"] == "${{ needs.detect-changes.outputs.head-sha }}"
    manifest = next(
        step["run"]
        for step in prepare["steps"]
        if step.get("name") == "Write workspace manifest"
    )
    assert "head_sha=$HEAD_SHA" in manifest
    assert "needs.detect-changes.outputs.head-sha" in report["env"]["HEAD_SHA"]
    download = next(
        step
        for step in report["steps"]
        if step.get("name") == "Download all validation results"
    )
    assert download["id"] == "download-results"
    assert download["continue-on-error"] is True
    failure_step = next(
        step
        for step in report["steps"]
        if step.get("name") == "Record failed validation jobs"
    )
    assert "steps.download-results.outcome == 'failure'" in failure_step["if"]
    assert "needs.prepare-workspace.result == 'failure'" in failure_step["if"]
    assert "pipeline-job-failed" in failure_step["run"]
    command = next(
        step["run"]
        for step in report["steps"]
        if step.get("name") == "Generate and post validation report"
    )
    assert '--commit-sha "$HEAD_SHA"' in command
    assert "--checks-api" in command

    paths = workflow["jobs"]["validate-paths"]
    path_checkouts = [
        step
        for step in paths["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert path_checkouts[0]["with"]["path"] == "pr-tree"
    assert path_checkouts[1]["with"]["path"] == "trusted"
    assert path_checkouts[1]["with"]["repository"] == "${{ github.repository }}"
    assert (
        path_checkouts[1]["with"]["ref"]
        == "${{ needs.detect-changes.outputs.base-sha }}"
    )
    link_guard = next(
        step for step in paths["steps"] if step.get("name") == "Reject links in PR tree"
    )
    assert link_guard["working-directory"] == "pr-tree"
    assert "120000|160000" in link_guard["run"]
    upload = next(
        step for step in paths["steps"] if step.get("name") == "Upload results"
    )
    assert "pr-tree/validation-file-paths.log" in upload["with"]["path"]
    run = next(step for step in paths["steps"] if step.get("name") == "Run validation")
    assert run["working-directory"] == "pr-tree"
    assert "../trusted/tools/validation/validate_file_paths.py" in run["run"]


def test_nightly_skips_only_exact_successful_head_base_pairs():
    config = yaml.safe_load(NIGHTLY_WORKFLOW.read_text(encoding="utf-8"))
    job = config["jobs"]["revalidate-open-prs"]
    assert config["permissions"]["pull-requests"] == "read"
    assert job["env"]["GH_REPO"] == "${{ github.repository }}"
    force = _workflow_trigger(NIGHTLY_WORKFLOW)["workflow_dispatch"]["inputs"]["force"]
    assert force["type"] == "boolean"
    assert force["default"] is True
    step = next(
        step for step in job["steps"] if "gh workflow run" in step.get("run", "")
    )
    script = "\n".join(
        line for line in step["run"].splitlines() if not line.lstrip().startswith("#")
    )
    assert "--repo" not in script
    assert "commits/main" in script
    assert "--paginate" in script
    assert "state=open&base=main" in script
    assert "display_title" in script
    assert 'status == "completed"' in script
    assert 'conclusion == "success"' in script
    assert "head=$head_sha" in script
    assert "base=$base_sha" in script
    assert "grep -Fqx" in script
    assert "--ref main" in script
    assert '-f pr_number="$num"' in script
    assert '-f head_sha="$head_sha"' in script
    assert '-f base_sha="$base_sha"' in script
    assert "refs/pull/" not in script
    assert "merge ref" not in script
    assert ".head.repo.full_name" not in script
    assert 'if [ "$failed" -gt 0 ]; then' in script
    assert "failed=$((failed + 1))" in script
    assert "exit 1" in script


def test_pr_cache_cleanup_lists_before_deleting():
    workflow = PR_CACHE_WORKFLOW.read_text(encoding="utf-8")
    assert '"${cache_url}?ref=${ref}&per_page=100"' in workflow
    assert workflow.count("cache_ids=$(gh api --paginate") == 2
    assert workflow.count('done <<< "$cache_ids"') == 2
    assert workflow.count('gh api -X DELETE "${cache_url}/${id}"') == 2
    assert "| while read -r id" not in workflow
    assert '"actions/caches/"\\\n' not in workflow


def test_validation_jobs_require_complete_report_files():
    jobs = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    expected = {
        "content-checks": {
            "validation-style-check.log",
            "validation-style-check.json",
            "validation-common-mistakes.log",
            "validation-common-mistakes.json",
        },
        "validate-paths": {
            "pr-tree/validation-file-paths.log",
            "pr-tree/validation-file-paths.json",
        },
    }
    for job_name, paths in expected.items():
        steps = jobs[job_name]["steps"]
        commands = "\n".join(
            step.get("run", "") for step in steps if step["name"].startswith("Verify")
        )
        assert {f"test -f {path}" for path in paths} <= set(commands.splitlines())
        uploads = [
            step
            for step in steps
            if step.get("uses", "").startswith("actions/upload-artifact@")
        ]
        assert uploads
        assert all(
            upload["with"].get("if-no-files-found") == "error" for upload in uploads
        )


def test_batch_jobs_upload_complete_result_sets():
    # Per-validator log + sidecar verification moved inside
    # run_validator_batch.py (a crash or missing file fails the batch), so
    # the workflow side only has to ship what the runner produced and never
    # mask an empty batch with a successful upload.
    jobs = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    job = jobs["validate-batch"]
    uploads = [
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    assert len(uploads) == 1
    upload = uploads[0]
    assert upload["with"]["name"] == "validation-batch-${{ matrix.batch }}-results"
    assert upload["with"]["path"] == "batch-results"
    assert upload["with"]["if-no-files-found"] == "error"
    assert "hashFiles('batch-results/**') != ''" in upload["if"]
    run = next(
        step["run"]
        for step in job["steps"]
        if step.get("name") == "Run validator batch"
    )
    assert "run_validator_batch.py" in run
    assert "--changed-groups" in run


def test_pr_code_impact_scan_wiring():
    # The impact scan runs PR-owned validator code unprivileged: no cache
    # restore or save (a cache written under PR execution would poison the
    # shared cache), no PR comment or Checks API access, and results shipped
    # as data-only artifacts. Changed files come from the pinned base/head
    # git diff, not the 3000-file PR files API.
    workflow = yaml.safe_load(IMPACT_WORKFLOW.read_text(encoding="utf-8"))
    trigger = _workflow_trigger(IMPACT_WORKFLOW)
    assert set(trigger["pull_request"]["types"]) == {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    }
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] is True
    assert "pull_request.number" in workflow["concurrency"]["group"]
    job = workflow["jobs"]["impact"]

    checkout = next(
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["persist-credentials"] is False

    fetch = next(
        step["run"]
        for step in job["steps"]
        if step.get("name") == "Fetch PR base revision"
    )
    assert '"${{ github.sha }}"' in fetch

    verify = next(
        step["run"]
        for step in job["steps"]
        if step.get("name") == "Verify pinned revisions"
    )
    assert "base.sha" in verify
    assert "head.sha" in verify
    assert '"${{ github.sha }}^1"' in verify
    assert '"${{ github.sha }}^2"' in verify

    diff = next(
        step["run"]
        for step in job["steps"]
        if step.get("name") == "Derive changed files from the pinned diff"
    )
    assert "--name-status" in diff
    assert "merge-base" in diff
    assert "collect_changed_files.py" in diff
    assert "pulls/" not in diff and "api" not in diff
    assert "Checkout PR head revision" in IMPACT_WORKFLOW.read_text(encoding="utf-8")
    assert "continue-on-error" not in IMPACT_WORKFLOW.read_text(encoding="utf-8")
    assert "conflicted PR" not in IMPACT_WORKFLOW.read_text(encoding="utf-8")

    run = next(
        step["run"]
        for step in job["steps"]
        if "run_validator_batch.py" in (step.get("run") or "")
    )
    assert "--impact" in run
    assert "--changed-files-file" in run
    scan_step = next(
        step
        for step in job["steps"]
        if "run_validator_batch.py" in (step.get("run") or "")
    )
    assert "steps.tools-scope" not in scan_step["if"]

    cache_steps = [
        step for step in job["steps"] if "actions/cache" in step.get("uses", "")
    ]
    assert cache_steps == []

    dependencies = next(
        step for step in job["steps"] if step.get("name") == "Install dependencies"
    )
    assert dependencies["id"] == "dependencies"
    staged = next(
        step
        for step in job["steps"]
        if step.get("name") == "Run staged-validator integration"
    )
    assert "staged_validators_test.py" in staged["run"]
    assert "staged_validators_real_test.py" in staged["run"]

    scan = next(
        step
        for step in job["steps"]
        if (step.get("name") or "").startswith("Run changed validators")
    )
    assert scan["env"]["MD_NO_CACHE"] == "1"

    uploads = [
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    assert len(uploads) == 2
    tools_upload = next(
        step for step in uploads if step["with"]["path"] == "tools_validation.log"
    )
    assert tools_upload["with"]["if-no-files-found"] == "error"
    impact_upload = next(
        step for step in uploads if step["with"]["path"] == "validator-impact"
    )
    assert impact_upload["with"]["if-no-files-found"] == "error"
    assert "hashFiles('validator-impact/**') != ''" in impact_upload["if"]


def test_impact_base_fetch_has_full_history(tmp_path):
    workflow = yaml.safe_load(IMPACT_WORKFLOW.read_text(encoding="utf-8"))
    run = next(
        step["run"]
        for step in workflow["jobs"]["impact"]["steps"]
        if step.get("name") == "Fetch PR base revision"
    )
    fetch_line = next(
        line.strip()
        for line in run.splitlines()
        if line.strip().startswith("git fetch")
    )
    assert "--depth" not in fetch_line

    def git(repo, *args):
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()

    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.name", "Test")
    git(source, "config", "user.email", "test@example.com")
    (source / "state").write_text("root\n", encoding="utf-8")
    git(source, "add", "state")
    git(source, "commit", "-m", "root")
    (source / "state").write_text("old base\n", encoding="utf-8")
    git(source, "commit", "-am", "old base")
    old_base = git(source, "rev-parse", "HEAD")

    upstream = tmp_path / "upstream.git"
    git(tmp_path, "clone", "--bare", str(source), str(upstream))
    git(source, "checkout", "-b", "feature")
    (source / "state").write_text("feature\n", encoding="utf-8")
    git(source, "commit", "-am", "feature")
    head = git(source, "rev-parse", "HEAD")
    fork = tmp_path / "fork.git"
    git(tmp_path, "clone", "--bare", str(source), str(fork))
    git(source, "checkout", "main")
    (source / "state").write_text("new base\n", encoding="utf-8")
    git(source, "commit", "-am", "new base")
    base = git(source, "rev-parse", "HEAD")
    git(source, "push", str(upstream), "main")

    checkout = tmp_path / "checkout"
    git(tmp_path, "clone", str(fork), str(checkout))
    git(checkout, "checkout", "feature")
    options = [option for option in fetch_line.split()[2:] if option != "\\"]
    git(checkout, "fetch", *options, str(upstream), base)
    assert git(checkout, "merge-base", base, head) == old_base

    shallow = tmp_path / "shallow"
    git(tmp_path, "clone", str(fork), str(shallow))
    git(shallow, "checkout", "feature")
    git(shallow, "fetch", "--no-tags", "--depth=1", str(upstream), base)
    merge_base = subprocess.run(
        ["git", "merge-base", base, head],
        cwd=shallow,
        capture_output=True,
        text=True,
    )
    assert merge_base.returncode != 0


def test_impact_report_bridge_wiring():
    # The reporter is the privileged half: workflow_run from the default
    # branch, base-owned tooling, read-only on PR content.
    workflow = yaml.safe_load(IMPACT_REPORT_WORKFLOW.read_text(encoding="utf-8"))
    trigger = _workflow_trigger(IMPACT_REPORT_WORKFLOW)
    assert trigger["workflow_run"]["workflows"] == ["Validator impact"]
    assert trigger["workflow_run"]["types"] == ["completed"]
    assert workflow["permissions"]["pull-requests"] == "write"
    assert workflow["permissions"]["checks"] == "write"
    assert workflow["permissions"]["actions"] == "read"

    job = workflow["jobs"]["report"]
    assert job["if"] == "github.event.workflow_run.event == 'pull_request'"

    report = next(
        step["run"]
        for step in job["steps"]
        if "impact_report.py" in (step.get("run") or "")
    )
    assert '--workflow-run-json "$GITHUB_EVENT_PATH"' in report
    assert "GITHUB_EVENT_PATH" in report
    assert "toJSON" not in report
    assert "github.event.workflow_run" not in report

    checkouts = [
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert len(checkouts) == 1
    assert checkouts[0]["with"]["persist-credentials"] is False
    # The reporting checkout is the default branch; no PR ref is fetched.
    assert "ref" not in checkouts[0]["with"]


def test_impact_workflows_document_the_bootstrap_caveat():
    # workflow_run only fires once the report workflow reaches the default
    # branch, so the pair must not claim live coverage before that.
    assert "Bootstrap caveat" in IMPACT_WORKFLOW.read_text(encoding="utf-8")
    assert "Bootstrap caveat" in IMPACT_REPORT_WORKFLOW.read_text(encoding="utf-8")


def test_mod_changes_reach_content_checks():
    detect, filters = _filter_definitions()
    assert "mod" in detect["outputs"]
    assert filters["mod"] == ["*.mod"]
    assert "*.mod" in filters["content"]

    content_checks = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))["jobs"][
        "content-checks"
    ]
    assert "needs.detect-changes.outputs.mod == 'true'" in content_checks["if"]


def test_music_style_changes_reach_content_checks():
    _, filters = _filter_definitions()
    assert {
        "common/**/*.txt",
        "events/**/*.txt",
        "history/**/*.txt",
        "music/**/*.txt",
    } <= set(filters["style"])
    assert "music/**" in filters["content"]

    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    assert "music" in set(workflow["env"]["WORKSPACE_PATHS"].split())
    pr_checkout = next(
        step
        for step in workflow["jobs"]["prepare-workspace"]["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert "music" in set(pr_checkout["with"]["sparse-checkout"].split())
    assert (
        "needs.detect-changes.outputs.style == 'true'"
        in workflow["jobs"]["content-checks"]["if"]
    )
