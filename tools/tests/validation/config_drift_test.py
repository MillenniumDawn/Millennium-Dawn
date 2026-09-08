"""Drift guards for validator declarations and the validation workflows."""

import re

import pytest
import yaml
from change_groups import GROUP_PATTERNS, classify
from coverage import Coverage
from precommit_validate import _REGISTRY
from shared.paths import REPO_ROOT, VALIDATION_DIR
from validate_decisions import _DECISION_REFERENCE_SOURCE_PATTERNS
from validate_ideas import Validator as IdeaValidator
from validate_oob_units import (
    _CREATE_UNIT_SOURCE_PATTERNS,
    _DELETE_TEMPLATE_SOURCE_PATTERNS,
    _TEMPLATE_SOURCE_PATTERNS,
    _VARIANT_SOURCE_PATTERNS,
)
from validate_scripted_params import _CALLER_PATTERNS
from validate_staged import VALIDATORS as STAGED_VALIDATORS
from validator_batches import ALL_SPECS, BATCHES, ValidatorSpec

PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "test-suite.yml"
VALIDATOR_CACHE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "validator-cache.yml"
NIGHTLY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "nightly-pr-validation.yml"
PR_CACHE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-cache-cleanup.yml"

SCRIPT_ROOTS = ("common", "events", "history")
OLD_WORKFLOWS = (
    "coding-pipeline.yml",
    "tools-validation.yml",
    "validator-impact.yml",
    "validator-impact-report.yml",
)


def _workflow_trigger(workflow):
    config = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    return config.get("on", config.get(True, {}))


def _parse_precommit():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    result = {}
    for repo in config.get("repos", []):
        for hook in repo.get("hooks", []):
            match = re.search(
                r"tools/validation/(validate_\w+\.py)", hook.get("entry", "")
            )
            if match:
                result[match.group(1)] = {
                    "strict": "--strict" in hook.get("entry", ""),
                    "stage": (
                        "manual"
                        if "manual" in (hook.get("stages") or [])
                        else "default"
                    ),
                }
    for spec in _REGISTRY:
        result.setdefault(
            f"{spec.script}.py", {"strict": spec.strict, "stage": "default"}
        )
    return result


def _parse_ci():
    return {spec.script: {"strict": spec.strict} for spec in ALL_SPECS}


def _parse_ci_standalone():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    result = {}
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            command = step.get("run") or ""
            for match in re.finditer(
                r"tools/(?:validation|linting)/(validate_\w+\.py)", command
            ):
                result[match.group(1)] = {"strict": "--strict" in command}
    return result


def _spec_for(script):
    return next(spec for spec in ALL_SPECS if spec.script == script)


@pytest.fixture(scope="module")
def disk():
    return {path.name for path in VALIDATION_DIR.glob("validate_*.py")}


@pytest.fixture(scope="module")
def precommit():
    return _parse_precommit()


@pytest.fixture(scope="module")
def ci():
    return _parse_ci()


@pytest.fixture(scope="module")
def ci_standalone():
    return _parse_ci_standalone()


CI_EXEMPT = {
    "validate_style.py",
    "validate_unused_textures.py",
    "validate_file_paths.py",
    "validate_mod_descriptors.py",
}
PRECOMMIT_EXEMPT: set[str] = set()
STRICT_MISMATCH_ALLOWED = {"validate_ai_equipment.py"}


def test_test_suite_replaces_old_workflows():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    assert workflow["name"] == "Test Suite"
    assert set(workflow["jobs"]) == {
        "detect-changes",
        "validate-paths",
        "prepare-workspace",
        "tools-tests",
        "mod-tests",
        "report",
    }
    assert "pull_request" in _workflow_trigger(CI_WORKFLOW)
    assert "pull_request_target" not in _workflow_trigger(CI_WORKFLOW)
    leftovers = [CI_WORKFLOW.parent / name for name in OLD_WORKFLOWS]
    if any(path.exists() for path in leftovers):
        pytest.skip("old workflow deletion is pending parent cleanup")
    assert not [path for path in leftovers if path.exists()]


def test_change_groups_cover_every_batch_group():
    missing = sorted(
        {
            group
            for spec in ALL_SPECS
            for group in spec.groups
            if group not in GROUP_PATTERNS
        }
    )
    assert not missing


def test_mod_tests_matrix_lists_every_batch():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["mod-tests"]["strategy"]["matrix"]["batch"]
    assert sorted(matrix) == sorted(BATCHES)


def test_tools_linux_runs_quality_suite():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["tools-tests"]["strategy"]["matrix"]["include"]
    linux = next(entry for entry in matrix if entry["os"] == "Linux")
    assert linux["quality"] is True
    assert {entry["os"] for entry in matrix} == {"Linux", "macOS", "Windows"}
    steps = workflow["jobs"]["tools-tests"]["steps"]
    commands = "\n".join(step.get("run", "") for step in steps)
    assert "coverage run" in commands
    assert "coverage report" in commands
    for command in ("ruff check tools", "black --check tools", "pylint tools", "mypy"):
        assert command in commands
    assert "bun run jscpd" in commands
    assert "staged_validators_test.py" in commands
    assert "staged_validators_real_test.py" in commands


def test_tools_checkout_exposes_consumed_configuration():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    checkout = workflow["jobs"]["tools-tests"]["steps"][0]
    sparse = set(checkout["with"]["sparse-checkout"].split())
    required = {
        "tools",
        "pyproject.toml",
        ".pre-commit-config.yaml",
        ".claude/docs/typo-watchlist.md",
        ".github/actions/setup-md-python/action.yml",
        ".github/workflows/test-suite.yml",
        ".github/workflows/validator-cache.yml",
        ".github/workflows/nightly-pr-validation.yml",
        ".github/workflows/pr-cache-cleanup.yml",
    }
    assert required <= sparse


def test_file_paths_run_in_a_lightweight_index_job():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    detect = workflow["jobs"]["detect-changes"]
    path_job = workflow["jobs"]["validate-paths"]
    assert detect["outputs"]["file-paths"] == "${{ steps.groups.outputs.file-paths }}"
    assert path_job["needs"] == ["detect-changes"]
    assert path_job["if"].strip() == "needs.detect-changes.outputs.file-paths == 'true'"
    checkout = path_job["steps"][0]
    assert checkout["uses"].startswith("actions/checkout@")
    assert checkout["with"]["repository"] == (
        "${{ needs.detect-changes.outputs.checkout-repository }}"
    )
    assert checkout["with"]["ref"] == "${{ needs.detect-changes.outputs.checkout-ref }}"
    assert checkout["with"]["filter"] == "blob:none"
    sparse = set(checkout["with"]["sparse-checkout"].split())
    assert "descriptor.mod" in sparse
    assert "tools" in sparse
    assert "gfx" not in sparse
    assert "map" not in sparse
    run_step = next(
        step
        for step in path_job["steps"]
        if "validate_file_paths.py" in (step.get("run") or "")
    )
    run = run_step["run"]
    assert "working-directory" not in run_step
    assert "python3 tools/validation/validate_file_paths.py --path ." in run
    assert "--strict" in run
    assert "--output validation-file-paths.log" in run
    assert any(
        step.get("with", {}).get("name") == "validation-file-paths-results"
        for step in path_job["steps"]
    )
    report = workflow["jobs"]["report"]
    assert "validate-paths" in report["needs"]
    assert all(
        step.get("name") != "Record failed validation jobs" for step in report["steps"]
    )


def test_detect_changes_uses_python_grouping():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    detect = workflow["jobs"]["detect-changes"]
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "dorny/paths-filter" not in text
    assert "filter: blob:none" in text
    assert "git diff --name-status -z" in text
    assert "collect_changed_files.py" in text
    assert "change_groups.py" in text
    assert "full_suite" in detect["outputs"]
    assert "tools" in detect["outputs"]
    assert any(step.get("name") == "Upload changed files" for step in detect["steps"])
    for path in ("resources/documentation/modifiers_documentation.md",):
        assert classify([path])["full_suite"] is True


def test_dispatch_forces_all_content_groups():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    script = next(
        step["run"]
        for step in workflow["jobs"]["detect-changes"]["steps"]
        if step.get("name") == "Compute changed groups"
    )
    assert "--dispatch" in script
    assert "< changed-files.txt" in script


def test_prepare_workspace_is_pr_code_and_cache_scoped_to_head():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    prepare = workflow["jobs"]["prepare-workspace"]
    checkout = next(
        step for step in prepare["steps"] if step.get("name") == "Checkout PR workspace"
    )
    assert checkout["with"]["repository"] == (
        "${{ needs.detect-changes.outputs.checkout-repository }}"
    )
    assert checkout["with"]["ref"] == "${{ needs.detect-changes.outputs.checkout-ref }}"
    assert checkout["with"]["filter"] == "blob:none"
    checkouts = [
        step for step in prepare["steps"] if "actions/checkout@" in step.get("uses", "")
    ]
    assert len(checkouts) == 1
    assert not any(
        "validate_file_paths.py" in (step.get("run") or "") for step in prepare["steps"]
    )
    cache = next(
        step
        for step in prepare["steps"]
        if "actions/cache/restore@" in step.get("uses", "")
        and step.get("with", {}).get("path")
        and "sparse" in step.get("id", "")
    )
    assert "md-sparse-v1-${{ runner.os }}" in cache["with"]["key"]
    assert "needs.detect-changes.outputs.head-sha" in cache["with"]["key"]
    valcache = next(
        step
        for step in prepare["steps"]
        if "actions/cache/restore@" in step.get("uses", "")
        and "validation_cache" in step.get("with", {}).get("path", "")
    )
    assert "full_suite != 'true'" in valcache["if"]
    assert "steps.toolshash.outputs.hash" in valcache["with"]["key"]
    assert "base-sha" not in valcache["with"]["key"]


def test_mod_core_runs_extra_checks_after_batch():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["mod-tests"]["steps"]
    names = [step.get("name") for step in steps]
    batch_index = names.index("Run validator batch")
    for name in (
        "Run style check",
        "Run common-mistakes check",
        "Check localisation UTF-8 BOM",
        "Check .mod file encoding",
        "Check mod descriptor replace_path sync",
    ):
        step = steps[names.index(name)]
        assert "matrix.batch == 'core'" in step["if"]
        assert names.index(name) > batch_index
    style = next(step for step in steps if step.get("name") == "Run style check")
    assert "MD_STAGED_FILES" in style["run"]


def test_report_job_posts_comment_and_checks():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    report = workflow["jobs"]["report"]
    assert report["if"] == "${{ always() && !cancelled() }}"
    assert report["permissions"]["pull-requests"] == "write"
    assert report["permissions"]["checks"] == "write"
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "--post-comment" in text
    assert "--checks-api" in text
    assert 'pattern: "*results"' in text
    assert any(step.get("name") == "Download changed files" for step in report["steps"])
    assert "full_suite == 'true'" in text
    checkout = next(
        step for step in report["steps"] if "actions/checkout@" in step.get("uses", "")
    )
    assert "checkout-repository" in checkout["with"]["repository"]
    assert "checkout-ref" in checkout["with"]["ref"]


def test_report_restores_baseline_for_full_and_dispatch_runs():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    report = workflow["jobs"]["report"]
    restore = next(
        step
        for step in report["steps"]
        if step.get("name") == "Restore validation baseline"
    )
    assert "if" not in restore
    script = next(
        step["run"]
        for step in report["steps"]
        if step.get("name") == "Generate and post validation report"
    )
    assert "--baseline-dir .validation_baseline" in script
    assert '--baseline-toolshash "$TOOLSHASH"' in script
    assert "--changed-files changed-files/changed-files.txt" in script
    assert "if [ -f .validation_baseline/baseline-meta.json ]" not in script
    assert (
        "github.event_name == 'workflow_dispatch'" in report["env"]["VALIDATION_SCOPE"]
    )


def test_tools_sidecars_have_stable_schema():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["tools-tests"]["steps"]
    sidecar = next(step for step in steps if step.get("id") == "suite-sidecar")
    assert "suite-run.json" in sidecar["run"]
    for field in ('"suite":"tools"', '"status"', '"errors"', '"warnings"', '"issues"'):
        assert field in sidecar["run"]
    upload = next(
        step for step in steps if step.get("name") == "Upload tools test results"
    )
    assert upload["with"]["name"] == "tools-tests-${{ matrix.os }}-results"


def test_nightly_dispatches_test_suite_and_matches_its_runs():
    config = yaml.safe_load(NIGHTLY_WORKFLOW.read_text(encoding="utf-8"))
    job = config["jobs"]["revalidate-open-prs"]
    script = next(
        step["run"] for step in job["steps"] if "gh workflow run" in step.get("run", "")
    )
    assert "test-suite.yml" in script
    assert "actions/workflows/test-suite.yml/runs" in script
    assert "display_title" in script
    assert "head=$head_sha" in script
    assert "base=$base_sha" in script
    assert "grep -Fqx" in script


def test_housekeeping_has_one_job_and_three_actions():
    path = REPO_ROOT / ".github" / "workflows" / "pr-housekeeping.yml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(config["jobs"]) == {"housekeeping"}
    text = path.read_text(encoding="utf-8")
    assert "actions/labeler@" in text
    assert "Assign PR to author" in text
    assert "assign-milestone" in text


def test_issue_triage_has_one_job_and_three_steps():
    path = REPO_ROOT / ".github" / "workflows" / "issue-triage.yml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(config["jobs"]) == {"triage"}
    steps = config["jobs"]["triage"]["steps"]
    names = {step.get("name") for step in steps}
    assert {
        "Add issue to project",
        "Default issue type to Task",
        "Assign milestone",
    } <= names


def test_batch_validator_coverage_and_strict_flags(disk, precommit, ci, ci_standalone):
    missing = sorted(disk - set(ci) - CI_EXEMPT)
    assert not missing
    orphaned = sorted(
        disk - set(precommit) - set(ci) - set(ci_standalone) - PRECOMMIT_EXEMPT
    )
    assert not orphaned
    mismatches = [
        script
        for script in sorted(set(precommit) & set(ci))
        if script not in STRICT_MISMATCH_ALLOWED
        and precommit[script]["strict"] != ci[script]["strict"]
    ]
    assert not mismatches


def test_ci_exempt_entries_are_current(disk, ci):
    assert not CI_EXEMPT - disk
    assert not CI_EXEMPT & set(ci)


def test_precommit_exempt_entries_are_current(disk, precommit):
    assert not PRECOMMIT_EXEMPT - disk
    assert not PRECOMMIT_EXEMPT & set(precommit)


def test_strict_mismatch_allowlist_is_current(disk, precommit, ci):
    assert not STRICT_MISMATCH_ALLOWED - disk
    resolved = [
        script
        for script in STRICT_MISMATCH_ALLOWED
        if script in precommit
        and script in ci
        and precommit[script]["strict"] == ci[script]["strict"]
    ]
    assert not resolved


def test_validator_cache_wiring_stays_single_job():
    workflow = VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count("python3 tools/validation/run_all_validators.py") == 1
    assert "--persist-results .validation_baseline_candidate" in workflow
    config = yaml.safe_load(workflow)
    assert set(config["jobs"]) == {"build-cache"}
    steps = config["jobs"]["build-cache"]["steps"]
    assert (
        len([step for step in steps if "actions/checkout@" in step.get("uses", "")])
        == 1
    )
    verify = next(
        step
        for step in steps
        if step.get("name") == "Verify validation result candidate completion"
    )
    assert verify["run"] == "test -f .validation_baseline_candidate/.persist-complete"


def test_validator_cache_restores_are_source_hash_scoped():
    expected = "md-valcache-v1-${{ runner.os }}-${{ steps.toolshash.outputs.hash }}-"
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert expected in workflow
    assert expected in VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8")
    baseline = "md-baseline-v1-${{ runner.os }}-${{ steps.toolshash.outputs.hash }}-"
    assert baseline in CI_WORKFLOW.read_text(encoding="utf-8")


def test_baseline_saves_only_after_clean_diff():
    config = yaml.safe_load(VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8"))
    job = config["jobs"]["build-cache"]
    diff = next(step for step in job["steps"] if step.get("id") == "diff")
    assert "tools/baseline_check.py" in diff["run"]
    save = next(
        step for step in job["steps"] if step.get("name") == "Save validation baseline"
    )
    assert save["if"] == "steps.diff.outcome == 'success'"


def test_tools_quality_checks_are_wired_in_precommit_and_ci():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = {
        hook["id"]: hook for repo in config["repos"] for hook in repo.get("hooks", [])
    }
    assert {"black-tools", "pylint-tools", "mypy-tools"} <= hooks.keys()
    assert hooks["black-tools"]["entry"] == "black"
    assert "pylint tools" in hooks["pylint-tools"]["entry"]
    assert hooks["mypy-tools"]["entry"] == "mypy"
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "ruff check tools" in text
    assert "black --check tools" in text
    assert "pylint tools" in text
    assert "mypy" in text
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
    assert "python_files=*_test.py" in prepush_suite
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "tools/tests/collection_layout_test.py" in text
    assert "coverage run" in text
    assert "python_files=*_test.py" in text


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


def test_ci_strict_gate_lives_in_batch_specs():
    assert ValidatorSpec("x", "validate_x.py", ("common",)).strict is True
    assert sorted(spec.name for spec in ALL_SPECS if not spec.strict) == [
        "building-guards",
        "simplifications",
    ]


def test_ci_redundant_modifier_gate_is_strict():
    assert _spec_for("validate_modifiers.py").strict is True


def test_ci_idea_icon_check_is_enabled():
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
        setattr(validator, name, lambda *args, **kwargs: None)
    validator.run_validations()
    assert called
    assert (VALIDATION_DIR / "vanilla_sprites.txt").is_file()


def test_mio_validator_runs_for_localisation_changes():
    assert "localisation" in _spec_for("validate_mios.py").groups


def test_gfx_and_scripted_localisation_routes_are_preserved():
    assert {"interface", "common", "events", "history", "localisation"} <= set(
        _spec_for("validate_gfx_references.py").groups
    )
    assert "interface" in _spec_for("validate_scripted_localisation.py").groups


def test_group_patterns_preserve_cross_reference_routes():
    assert "interface/**" in GROUP_PATTERNS["scientist-traits"]
    assert "interface/**" in GROUP_PATTERNS["mios"]
    assert "common/**/*.txt" in GROUP_PATTERNS["decisions"]
    assert "map/adjacency_rules.txt" in GROUP_PATTERNS["map-adjacency"]
    dirs = set()
    for pattern in (
        _CREATE_UNIT_SOURCE_PATTERNS
        + _DELETE_TEMPLATE_SOURCE_PATTERNS
        + _TEMPLATE_SOURCE_PATTERNS
        + _VARIANT_SOURCE_PATTERNS
    ):
        directory = pattern.rsplit("/", 1)[0]
        if directory.endswith("/**"):
            directory = directory[:-3]
        dirs.add(directory + "/")
    assert {directory + "**" for directory in dirs} <= set(GROUP_PATTERNS["oob"])
    assert set(_DECISION_REFERENCE_SOURCE_PATTERNS) <= set(GROUP_PATTERNS["decisions"])


def test_scripted_param_patterns_scan_every_script_root():
    whole_tree = {
        pattern.split("/", 1)[0]
        for pattern in _CALLER_PATTERNS
        if pattern.split("/", 1)[1:] == ["**/*.txt"]
    }
    assert not sorted(set(SCRIPT_ROOTS) - whole_tree)
    caller_dirs = {pattern.split("*", 1)[0] for pattern in _CALLER_PATTERNS}
    staged = next(
        spec for spec in STAGED_VALIDATORS if spec["name"] == "scripted params"
    )
    assert caller_dirs <= set(staged["prefixes"])
    for directory in caller_dirs:
        sample = directory + "_scripted_param_probe.txt"
        assert classify([sample])["style"] is True


def test_mod_and_music_groups_are_reachable():
    assert "*.mod" in GROUP_PATTERNS["mod"]
    assert "music/**/*.txt" in GROUP_PATTERNS["style"]
    assert "music/**" in GROUP_PATTERNS["content"]
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    assert "music" in workflow["env"]["WORKSPACE_PATHS"]


def test_nightly_and_cache_workflows_keep_expected_permissions():
    nightly = yaml.safe_load(NIGHTLY_WORKFLOW.read_text(encoding="utf-8"))
    assert nightly["permissions"]["pull-requests"] == "read"
    cache = yaml.safe_load(PR_CACHE_WORKFLOW.read_text(encoding="utf-8"))
    assert cache["permissions"]["actions"] == "write"
    text = PR_CACHE_WORKFLOW.read_text(encoding="utf-8")
    assert '"${cache_url}?ref=${ref}&per_page=100"' in text
    assert text.count("cache_ids=$(gh api --paginate") == 2
