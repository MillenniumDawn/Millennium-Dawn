"""Drift guard between the two places the validator set is declared.

Every validator in `tools/validation/validate_*.py` is wired independently into
`.pre-commit-config.yaml` (the `md-validate-*` hooks) and into
`.github/workflows/coding-pipeline.yml` (the `validate-core` /
`validate-targeted` matrices). Those two lists are hand-maintained and drift: a
validator gets added to one and forgotten in the other, or `--strict` is set on
one side only. These tests fail when that happens, so the gap surfaces at PR
time instead of as a "passed locally, failed CI" surprise.

The workflow checks below also verify that matrix entries are reachable through
their parent job condition and that tool-test configuration files trigger the
workflow that reads them.

Scope is `tools/validation/validate_*.py` only. The linting scripts in
`tools/linting/` (check_common_mistakes, fix_styling) are few, stable, and not
matrix-driven, so they are out of scope here.

Intentional exceptions live in the EXEMPT / ALLOWED sets below, each with a
reason. The guard also checks those sets stay current: an exemption that no
longer applies (the validator got wired, or deleted) fails the test so the
stale entry gets removed.
"""

import re
from pathlib import Path

import pytest
import yaml
from precommit_validate import _REGISTRY
from validate_decisions import _DECISION_REFERENCE_SOURCE_PATTERNS
from validate_oob_units import _CREATE_UNIT_SOURCE_PATTERNS

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_DIR = Path(__file__).resolve().parents[1]
PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "coding-pipeline.yml"
TOOLS_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "tools-validation.yml"
VALIDATOR_CACHE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "validator-cache.yml"
NIGHTLY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "nightly-pr-validation.yml"

# Validators intentionally absent from the CI matrices. Each needs a reason.
CI_EXEMPT = {
    # Runs in the standalone styling-check job, diff-scoped to the changed
    # .txt files (MD_STAGED_FILES from detect-changes' style_files output) so a
    # PR is gated on the style it introduced, not the repo-wide backlog. Can't
    # join the validate-core/validate-targeted matrices: those run full-repo
    # with no diff-list injection, which would resurface the whole backlog.
    "validate_style.py",
    # ~22k pre-existing unreferenced textures plus a slow full-repo scan make
    # this a periodic mod-size audit, not a per-PR gate. Manual hook only.
    "validate_unused_textures.py",
    # Runs in the standalone validate-paths job. It reads path names from the
    # git index, which the matrix jobs don't have: they restore a content
    # bundle that carries no .git and omits map/.
    "validate_file_paths.py",
    # Runs in structural-lint because descriptors are root files in the
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
    import sys

    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from precommit_validate import _REGISTRY

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
    """Map validate_*.py -> {'strict': bool} from the two validator matrices."""
    wf = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    result = {}
    for job in ("validate-core", "validate-targeted"):
        matrix = wf["jobs"][job]["strategy"]["matrix"]["validator"]
        for entry in matrix:
            # CI Run step passes --strict unless `strict: false` is set.
            result[entry["script"]] = {"strict": bool(entry.get("strict", True))}
    return result


def _parse_ci_standalone():
    """Map validate_*.py -> {'strict': bool} for jobs that invoke one directly.

    The matrices name their script through `${{ matrix.validator.script }}`, so
    only the standalone jobs (styling-check, validate-paths) match here."""
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
    trigger = _workflow_trigger(workflow)
    return set(trigger.get("pull_request", {}).get("paths", []))


def _filter_definitions():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    detect = workflow["jobs"]["detect-changes"]
    step = next(step for step in detect["steps"] if step.get("id") == "filter")
    return detect, yaml.safe_load(step["with"]["filters"])


def test_should_run_expressions_render_strings():
    """A matrix `should_run` that does boolean logic must coerce to a string.

    The step guard is `if: matrix.validator.should_run == 'true'`. A bare
    boolean expression (`${{ A == 'true' || B == 'true' }}`) yields boolean
    true; GitHub coerces `true == 'true'` to `1 == NaN` = false, so every step
    silently skips and the validator never runs or reports. Any expression
    using `||`/`==` must end with `&& 'true' || 'false'` to stay a string.
    """
    wf = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    offenders = []
    for job in ("validate-core", "validate-targeted"):
        for entry in wf["jobs"][job]["strategy"]["matrix"]["validator"]:
            expr = entry.get("should_run")
            if not isinstance(expr, str):
                continue
            does_logic = "||" in expr or "==" in expr
            coerces_to_string = "'true'" in expr and "'false'" in expr
            if does_logic and not coerces_to_string:
                offenders.append(f"{entry.get('script')}: {expr}")
    assert not offenders, (
        "These should_run expressions evaluate to a boolean and fail the "
        "`== 'true'` step guard (validator silently skips). Wrap as "
        "`(<expr>) && 'true' || 'false'`:\n" + "\n".join(offenders)
    )


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
        "Validators exist on disk but are not in the CI matrices "
        f"(coding-pipeline.yml): {missing}. Add each to validate-core or "
        "validate-targeted, or add it to CI_EXEMPT with a reason."
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
        "into .pre-commit-config.yaml or the CI matrix, or add to "
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


def test_targeted_parent_reaches_every_matrix_entry():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["validate-targeted"]
    parent = job["if"]
    matrix = job["strategy"]["matrix"]["validator"]
    parent_true_outputs = set(
        re.findall(r"needs\.detect-changes\.outputs\.([\w-]+)\s*==\s*'true'", parent)
    )
    missing = {}
    for entry in matrix:
        expression = entry.get("should_run", "")
        outputs = set(
            re.findall(r"needs\.detect-changes\.outputs\.([\w-]+)", expression)
        )
        unreachable = outputs - parent_true_outputs
        if unreachable:
            missing[entry["script"]] = sorted(unreachable)
    assert not missing, (
        "validate-targeted parent condition cannot reach matrix entries for "
        f"these detect-changes outputs: {missing}"
    )


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


def test_nightly_keys_the_bundle_on_the_live_base_tip():
    # WORKSPACE_KEY's base component is the only thing that invalidates the
    # bundle when main advances under a PR that got no pushes. Cache keys are
    # immutable, so a base that doesn't move makes cache/save a no-op and every
    # validator restores the previous run's tree while the run reports green.
    config = yaml.safe_load(NIGHTLY_WORKFLOW.read_text(encoding="utf-8"))
    step = next(
        step
        for step in config["jobs"]["revalidate-open-prs"]["steps"]
        if "gh workflow run" in step.get("run", "")
    )
    script = "\n".join(
        line for line in step["run"].splitlines() if not line.lstrip().startswith("#")
    )
    assert (
        "commits/main" in script
    ), "the nightly must resolve main's live head for base_sha"
    assert (
        ".base.sha" not in script
    ), "the PR list's .base.sha does not track main, so it cannot key the bundle"


def test_mio_validator_runs_for_localisation_changes():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    entry = next(
        entry
        for entry in workflow["jobs"]["validate-targeted"]["strategy"]["matrix"][
            "validator"
        ]
        if entry["script"] == "validate_mios.py"
    )
    expression = entry["should_run"]
    for output in ("mios", "localisation"):
        assert f"needs.detect-changes.outputs.{output} == 'true'" in expression


def test_check_baseline_saves_only_on_clean_diff():
    # The save gating is the whole nightly alarm: baseline_check exits 1 on
    # new errors, and only `steps.diff.outcome == 'success'` reaches the
    # save step. If that `if` is dropped, a red night saves tonight's
    # regressed results as the new baseline and the alarm self-heals
    # silently.
    config = yaml.safe_load(VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8"))
    job = config["jobs"]["check-baseline"]
    assert job["needs"] == ["build-cache"]

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
    assert {
        ".claude/docs/typo-watchlist.md",
        "resources/documentation/modifiers_documentation.md",
        ".pre-commit-config.yaml",
        "pyproject.toml",
        ".github/workflows/coding-pipeline.yml",
        ".github/workflows/nightly-pr-validation.yml",
        ".github/workflows/validator-cache.yml",
    } <= paths


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

    workflow = yaml.safe_load(TOOLS_WORKFLOW.read_text(encoding="utf-8"))
    quality_steps = workflow["jobs"]["ruff-lint"]["steps"]
    commands = "\n".join(step.get("run", "") for step in quality_steps)
    assert "ruff check tools" in commands
    assert "black --check tools" in commands
    assert "pylint tools" in commands
    assert "mypy" in commands
    test_commands = "\n".join(
        step.get("run", "") for step in workflow["jobs"]["report-lib-tests"]["steps"]
    )
    assert "coverage run" in test_commands
    assert "coverage report" in test_commands

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for package in ("black==", "coverage==", "mypy==", "pylint==", "ruff=="):
        assert package in pyproject


def test_staged_validator_integration_runs_in_isolated_worktree():
    workflow = yaml.safe_load(TOOLS_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["staged-validator-integration"]["steps"]
    worktree_step = next(
        step for step in steps if step.get("name") == "Create isolated test worktree"
    )
    assert "git worktree add --detach" in worktree_step["run"]

    run_step = next(
        step for step in steps if step.get("name") == "Run staged-validator integration"
    )
    assert run_step["env"]["MD_RUN_STAGED_INTEGRATION"] == "1"
    assert "staged_validators_test.py" in run_step["run"]
    assert "staged_validators_real_test.py" in run_step["run"]


def test_tools_tests_checkout_consumed_configuration():
    workflow = yaml.safe_load(TOOLS_WORKFLOW.read_text(encoding="utf-8"))
    checkout = next(
        step
        for step in workflow["jobs"]["report-lib-tests"]["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    sparse_paths = set(checkout["with"]["sparse-checkout"].splitlines())
    assert {
        ".claude/docs/typo-watchlist.md",
        # validate_modifiers_test parses the shipped doc to catch a Paradox
        # format change; without it here the test reads an absent file.
        "resources/documentation/modifiers_documentation.md",
        ".github/workflows/validator-cache.yml",
        ".github/workflows/nightly-pr-validation.yml",
        "pyproject.toml",
    } <= sparse_paths


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


def test_ci_run_steps_default_to_strict():
    # _parse_ci models an omitted `strict:` as --strict. Both Run steps must
    # agree: keying off `= "true"` instead would silently drop the gate for any
    # entry added without the field, and this guard could not see it.
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    for job in ("validate-core", "validate-targeted"):
        run = next(
            step["run"]
            for step in workflow["jobs"][job]["steps"]
            if step.get("name") == "Run validation"
        )
        assert (
            'matrix.validator.strict }}" != "false"' in run
        ), f"{job}'s Run step must default to --strict when `strict:` is absent."


def test_oob_routes_cover_every_create_unit_source():
    # Derived from the validator's own glob list, not a copy of it: a directory
    # added there must reach both routes or a PR touching only it never runs.
    dirs = {p.rsplit("/", 1)[0] + "/" for p in _CREATE_UNIT_SOURCE_PATTERNS}
    _, filters = _filter_definitions()
    assert {d + "**" for d in dirs} <= set(filters["oob"])
    spec = next(s for s in _REGISTRY if s.script == "validate_oob_units")
    assert dirs <= {prefix for prefix, _ in spec.rules}


def test_decision_filter_covers_every_reference_source():
    _, filters = _filter_definitions()
    assert set(_DECISION_REFERENCE_SOURCE_PATTERNS) <= set(filters["decisions"])


def test_gfx_reference_validator_runs_for_all_reference_sources():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    entry = next(
        entry
        for entry in workflow["jobs"]["validate-targeted"]["strategy"]["matrix"][
            "validator"
        ]
        if entry["script"] == "validate_gfx_references.py"
    )
    expression = entry["should_run"]
    for output in ("interface", "common", "events", "history", "localisation"):
        assert f"needs.detect-changes.outputs.{output} == 'true'" in expression


def test_scripted_localisation_core_runs_for_interface_changes():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    core = workflow["jobs"]["validate-core"]
    assert "needs.detect-changes.outputs.interface == 'true'" in core["if"]
    scripts = {entry["script"] for entry in core["strategy"]["matrix"]["validator"]}
    assert "validate_scripted_localisation.py" in scripts


def test_mod_changes_reach_structural_lint():
    detect, filters = _filter_definitions()
    workflow_paths = _pull_request_paths(CI_WORKFLOW)
    assert "*.mod" in workflow_paths
    assert "mod" in detect["outputs"]
    assert filters["mod"] == ["*.mod"]
    assert "*.mod" in filters["content"]

    structural = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))["jobs"][
        "structural-lint"
    ]
    assert "needs.detect-changes.outputs.mod == 'true'" in structural["if"]
