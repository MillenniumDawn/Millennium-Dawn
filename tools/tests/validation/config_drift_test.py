"""Drift guards for validator declarations and the validation workflows."""

import re
import sys

import dev_setup
import pytest
import yaml
from change_groups import GROUP_PATTERNS, classify
from coverage import Coverage
from precommit_validate import _REGISTRY
from shared.paths import REPO_ROOT, VALIDATION_DIR
from shared.suite import run_bash_step, workflow_step, write_under_str
from validate_decisions import _DECISION_REFERENCE_SOURCE_PATTERNS
from validate_ideas import Validator as IdeaValidator
from validate_oob_units import (
    _CREATE_UNIT_SOURCE_PATTERNS,
    _DELETE_TEMPLATE_SOURCE_PATTERNS,
    _TEMPLATE_LIMIT_SOURCE_PATTERNS,
    _TEMPLATE_SOURCE_PATTERNS,
    _VARIANT_SOURCE_PATTERNS,
)
from validate_scripted_params import _CALLER_PATTERNS
from validator_batches import ALL_SPECS, BATCHES, ValidatorSpec

PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "test-suite.yml"
VALIDATOR_CACHE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "validator-cache.yml"
DOCS_QUALITY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "docs-quality.yml"
SETUP_MD_PYTHON = REPO_ROOT / ".github" / "actions" / "setup-md-python" / "action.yml"
DEVELOPER_SETUP = (
    REPO_ROOT / "docs" / "src" / "content" / "resources" / "developer-setup.md"
)
TOOLS_README = REPO_ROOT / "tools" / "README.md"
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


def _setup_python_version(steps):
    for step in steps:
        uses = str(step.get("uses", ""))
        if "actions/setup-python@" in uses:
            return step["with"]["python-version"]
    raise AssertionError("no actions/setup-python step")


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
    "validate_standardization.py",
    "validate_unused_textures.py",
    # The CI workspace ships no gfx/models or gfx/entities.
    "validate_mesh_textures.py",
    "validate_file_paths.py",
    "validate_mod_descriptors.py",
}
# Manual-only: the standardization report is deliberately unwired from
# pre-commit and CI; standardizers run by hand instead (see
# tools/standardization/README.md).
PRECOMMIT_EXEMPT: set[str] = {"validate_standardization.py"}
STRICT_MISMATCH_ALLOWED = {"validate_ai_equipment.py"}


def test_test_suite_replaces_old_workflows():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    assert workflow["name"] == "Test Suite"
    assert set(workflow["jobs"]) == {
        "detect-changes",
        "validate-paths",
        "prepare-workspace",
        "tools-tests",
        "content-tests",
        "tools-quality",
        "mod-tests",
        "docs-quality",
        "report",
        "gate",
    }
    assert "pull_request" in _workflow_trigger(CI_WORKFLOW)
    assert "pull_request_target" not in _workflow_trigger(CI_WORKFLOW)
    leftovers = [CI_WORKFLOW.parent / name for name in OLD_WORKFLOWS]
    assert not [path for path in leftovers if path.exists()]


def test_docs_quality_runs_in_suite_and_feeds_the_report():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["docs-quality"]
    assert job["uses"] == "./.github/workflows/docs-quality.yml"
    assert "needs.detect-changes.outputs.docs" in job["if"]
    assert "full_suite" in job["if"]
    assert "docs-quality" in workflow["jobs"]["report"]["needs"]
    detect = workflow["jobs"]["detect-changes"]
    assert detect["outputs"]["docs"] == "${{ steps.groups.outputs.docs }}"
    assert "workflow_call" in _workflow_trigger(DOCS_QUALITY_WORKFLOW)
    text = DOCS_QUALITY_WORKFLOW.read_text(encoding="utf-8")
    assert "suite-run.json" in text
    assert "docs-quality-results" in text


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


def _job_commands(workflow, job):
    return "\n".join(step.get("run", "") for step in workflow["jobs"][job]["steps"])


def test_tools_linux_collects_coverage():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["tools-tests"]["strategy"]["matrix"]["include"]
    assert {entry["os"]: entry["coverage"] for entry in matrix} == {
        "Linux": True,
        "macOS": False,
        "Windows": False,
    }
    commands = _job_commands(workflow, "tools-tests")
    assert "-n auto --cov --cov-branch" in commands
    assert "coverage report" in commands


def test_tools_quality_runs_beside_the_test_matrix():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    quality = workflow["jobs"]["tools-quality"]
    assert quality["needs"] == ["detect-changes"]
    assert quality["if"] == workflow["jobs"]["tools-tests"]["if"]
    commands = _job_commands(workflow, "tools-quality")
    for command in ("ruff check tools", "black --check tools", "pylint tools", "mypy"):
        assert command in commands
    assert "bun run jscpd" in commands
    assert "staged_validators_test.py" in commands
    assert "staged_validators_real_test.py" in commands
    assert "tools/validate_tools.py --strict" in commands
    test_commands = _job_commands(workflow, "tools-tests")
    for command in ("ruff check", "black --check", "pylint", "bun run jscpd"):
        assert command not in test_commands


def test_tools_tests_install_only_the_test_group():
    setup = "Set up Python and dependencies"
    assert workflow_step("tools-tests", setup)["with"]["group"] == "test"
    assert "group" not in workflow_step("tools-quality", setup)["with"]
    action = yaml.safe_load(SETUP_MD_PYTHON.read_text(encoding="utf-8"))
    assert action["inputs"]["group"]["default"] == "dev"
    lint = set(dev_setup._group_packages("dev")) - set(
        dev_setup._group_packages("test")
    )
    assert {spec.split("==")[0] for spec in lint} == {"ruff", "black", "mypy", "pylint"}


def test_python_version_declarations_agree():
    major, minor = dev_setup.MIN_PYTHON
    assert (major, minor) == (3, 12)
    assert not hasattr(dev_setup, "REC_PYTHON")
    version = f"{major}.{minor}"
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(rf'^target-version\s*=\s*"py{major}{minor}"\s*$', pyproject, re.M)
    assert re.search(rf'^py-version\s*=\s*"{re.escape(version)}"\s*$', pyproject, re.M)
    assert re.search(
        rf'^python_version\s*=\s*"{re.escape(version)}"\s*$', pyproject, re.M
    )
    assert re.search(
        rf'^pythonVersion\s*=\s*"{re.escape(version)}"\s*$', pyproject, re.M
    )

    for path in (
        SETUP_MD_PYTHON,
        VALIDATOR_CACHE_WORKFLOW,
        DOCS_QUALITY_WORKFLOW,
        DEVELOPER_SETUP,
        TOOLS_README,
    ):
        assert path.is_file(), path

    action = yaml.safe_load(SETUP_MD_PYTHON.read_text(encoding="utf-8"))
    cache = yaml.safe_load(VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8"))
    docs = yaml.safe_load(DOCS_QUALITY_WORKFLOW.read_text(encoding="utf-8"))
    assert _setup_python_version(action["runs"]["steps"]) == version
    assert _setup_python_version(cache["jobs"]["build-cache"]["steps"]) == version
    assert _setup_python_version(docs["jobs"]["docs-quality"]["steps"]) == version
    assert "3.x" not in SETUP_MD_PYTHON.read_text(encoding="utf-8")
    assert "3.x" not in VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8")

    setup_doc = DEVELOPER_SETUP.read_text(encoding="utf-8")
    assert f"{version}+" in setup_doc
    assert "3.10+" not in setup_doc
    assert f"Python {version}" in TOOLS_README.read_text(encoding="utf-8")


def test_tools_checkout_exposes_consumed_configuration():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    checkout = workflow["jobs"]["tools-tests"]["steps"][0]
    sparse = set(checkout["with"]["sparse-checkout"].split())
    required = {
        "tools",
        "pyproject.toml",
        "validation_config.json",
        ".pre-commit-config.yaml",
        ".claude/docs/typo-watchlist.md",
        ".github/actions/setup-md-python/action.yml",
        ".github/workflows/test-suite.yml",
        ".github/workflows/validator-cache.yml",
        ".github/workflows/docs-quality.yml",
        ".github/workflows/nightly-pr-validation.yml",
        ".github/workflows/pr-cache-cleanup.yml",
        "docs/src/content/resources/developer-setup.md",
    }
    assert required <= sparse
    # Whole trees would add ~590 MB of translations and art no test reads.
    assert not {"localisation", "resources"} & sparse
    assert checkout["with"]["fetch-depth"] == 1
    assert checkout["with"]["filter"] == "blob:none"


def test_content_tests_run_once_with_the_game_tree():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    game_trees = {"common", "events", "history", "localisation/english"}
    tools = workflow["jobs"]["tools-tests"]
    assert not game_trees & set(tools["steps"][0]["with"]["sparse-checkout"].split())
    suite_runs = [
        step["run"]
        for step in tools["steps"]
        if "pytest tools/tests " in step.get("run", "")
    ]
    assert len(suite_runs) == 2
    assert all("--ignore=tools/tests/content" in run for run in suite_runs)

    content = workflow["jobs"]["content-tests"]
    for group in ("full_suite", "content", "tools"):
        assert f"outputs.{group} == 'true'" in content["if"]
    assert game_trees <= set(content["steps"][0]["with"]["sparse-checkout"].split())
    assert any(
        "pytest tools/tests/content" in step.get("run", "") for step in content["steps"]
    )


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
    detect_script = next(
        step["run"]
        for step in detect["steps"]
        if step.get("name") == "Derive changed files"
    )
    assert re.search(
        r'git diff --unified=0 "\$merge_base" "\$HEAD_SHA" -- \\\n'
        r"\s+localisation/english/MD_politics_view_parties_l_english\.yml \\\n"
        r'\s+"\$hook_path" > party-loc-scope\.diff',
        detect_script,
    )
    assert "party-loc-scope.diff" in text
    assert "collect_changed_files.py" in text
    assert "change_groups.py" in text
    assert "full_suite" in detect["outputs"]
    assert "tools" in detect["outputs"]
    upload = next(
        step for step in detect["steps"] if step.get("name") == "Upload changed files"
    )
    assert "changed-files.txt" in upload["with"]["path"]
    assert "party-loc-scope.diff" in upload["with"]["path"]
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


def test_prepare_workspace_materializes_pr_code_on_every_run():
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
    # An exact-head workspace cache never hit: each head has a new key.
    assert "md-sparse" not in CI_WORKFLOW.read_text(encoding="utf-8")
    assert not any(
        "actions/cache/save@" in step.get("uses", "") for step in prepare["steps"]
    )
    assert checkout["with"]["fetch-depth"] == 1
    assert checkout["with"]["sparse-checkout"] == (
        "/tools/validation/ci_workspace_profile.txt"
    )
    materialize = next(
        step
        for step in prepare["steps"]
        if step.get("name", "").startswith("Materialize")
    )
    assert "if" not in materialize
    assert "git sparse-checkout set --no-cone --stdin" in materialize["run"]
    assert "ci_workspace_profile.txt" in materialize["run"]
    valcache = next(
        step
        for step in prepare["steps"]
        if "actions/cache/restore@" in step.get("uses", "")
        and "validation_cache" in step.get("with", {}).get("path", "")
    )
    assert "if" not in valcache
    assert "MD_NO_CACHE" not in prepare["env"]
    assert "steps.toolshash.outputs.hash" in valcache["with"]["key"]
    assert "base-sha" not in valcache["with"]["key"]


def test_targeted_b_downloads_and_hands_off_party_loc_scope():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["mod-tests"]["steps"]
    download = next(
        step
        for step in steps
        if step.get("name") == "Download party localisation scope"
    )
    assert download["if"] == "matrix.batch == 'targeted-b'"
    assert download["with"] == {
        "name": "changed-files",
        "path": "validation-scope",
    }
    batch = next(step for step in steps if step.get("name") == "Run validator batch")
    assert "MD_PARTY_LOC_DIFF" in batch["env"]
    assert "validation-scope/party-loc-scope.diff" in batch["env"]["MD_PARTY_LOC_DIFF"]
    assert "targeted-b" in batch["env"]["MD_PARTY_LOC_DIFF"]


def test_mod_core_runs_extra_checks_after_batch():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["mod-tests"]["steps"]
    names = [step.get("name") for step in steps]
    batch_index = names.index("Run validator batch")
    for name in (
        "Run style check",
        "Check localisation UTF-8 BOM",
        "Check localisation YAML syntax",
        "Check .mod file encoding",
        "Check mod descriptor replace_path sync",
    ):
        step = steps[names.index(name)]
        assert "matrix.batch == 'core'" in step["if"]
        assert names.index(name) > batch_index
    style = next(step for step in steps if step.get("name") == "Run style check")
    assert "MD_STAGED_FILES" in style["run"]
    loc_yaml = steps[names.index("Check localisation YAML syntax")]
    assert loc_yaml["run"] == "python3 tools/linting/fix_loc_yaml.py"


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


def test_suite_gate_requires_every_validation_job():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    gate = workflow["jobs"]["gate"]
    assert gate["name"] == "Test suite gate"
    assert gate["if"] == "${{ always() }}"
    assert set(gate["needs"]) == set(workflow["jobs"]) - {"gate"}
    failure_step = gate["steps"][0]
    for job in gate["needs"]:
        assert f"needs.{job}.result" in failure_step["if"]
    assert failure_step["run"] == "exit 1"


def test_gate_steps_cannot_be_switched_off():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    # The report job's downloads tolerate missing artifacts on purpose.
    gated = set(workflow["jobs"]["gate"]["needs"]) - {"report"} | {"gate"}
    for name in sorted(gated):
        job = workflow["jobs"][name]
        assert "continue-on-error" not in job, name
        for step in job.get("steps", []):
            label = f"{name}: {step.get('name') or step.get('id')}"
            assert "continue-on-error" not in step, label
            condition = str(step.get("if", "")).replace("${{", "").replace("}}", "")
            assert condition.strip().lower() != "false", label


CONTRACT_FILES = (
    "tools/validation/ci_workspace_profile.txt",
    "tools/validation/staged_sparse_profile.txt",
    "tools/tests/content/tool_data_drift_test.py",
    "validation_config.json",
    "pyproject.toml",
)


def _contract_guard():
    return workflow_step("detect-changes", "Check CI tooling contract")["run"]


@pytest.mark.skipif(sys.platform == "win32", reason="the step runs in bash on Linux")
@pytest.mark.parametrize(
    "dropped",
    [None, *CONTRACT_FILES[:4], "pytest-xdist", "pytest-cov"],
)
def test_detect_changes_stops_a_head_without_the_ci_contract(tmp_path, dropped):
    for relative in CONTRACT_FILES:
        if relative != dropped:
            body = (REPO_ROOT / relative).read_text(encoding="utf-8")
            if relative == "pyproject.toml" and dropped:
                body = "".join(
                    line
                    for line in body.splitlines(keepends=True)
                    if f'"{dropped}' not in line
                )
            write_under_str(tmp_path, relative, body)

    result = run_bash_step(_contract_guard(), tmp_path)

    if dropped is None:
        assert result.returncode == 0, result.stdout
    else:
        assert result.returncode == 1
        assert "predates the CI tooling contract" in result.stdout
        assert dropped in result.stdout


def test_contract_guard_covers_what_the_workflow_reads_from_the_head():
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    guard = _contract_guard()
    checkout = workflow_step("detect-changes", "Checkout PR head")
    sparse = {path.lstrip("/") for path in checkout["with"]["sparse-checkout"].split()}
    profiles = set(re.findall(r"tools/validation/\w+_profile\.txt", text))
    assert profiles
    assert set(profiles) < set(CONTRACT_FILES)
    for path in CONTRACT_FILES:
        assert path in sparse, path
        assert path in guard, path
    assert "-n auto" in text and "pytest-xdist" in guard
    assert "--cov" in text and "pytest-cov" in guard


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


@pytest.mark.parametrize(
    ("job", "artifact"),
    [
        ("tools-tests", "tools-tests-${{ matrix.os }}-results"),
        ("tools-quality", "tools-quality-results"),
    ],
)
def test_tools_sidecars_have_stable_schema(job, artifact):
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"][job]["steps"]
    sidecar = next(step for step in steps if step.get("id") == "suite-sidecar")
    assert "suite-run.json" in sidecar["run"]
    for field in ('"suite":"tools"', '"status"', '"errors"', '"warnings"', '"issues"'):
        assert field in sidecar["run"]
    # A step the sidecar does not count can fail without failing the report.
    for step in steps:
        if "id" in step and step is not sidecar:
            assert f"steps.{step['id']}.outcome" in sidecar["run"], step["id"]
    upload = next(step for step in steps if "upload-artifact@" in step.get("uses", ""))
    assert upload["with"]["name"] == artifact


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


def test_validation_config_reaches_every_validator_run():
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    assert "validation_config.json" in workflow["env"]["WORKSPACE_PATHS"].split()
    profile = (VALIDATION_DIR / "ci_workspace_profile.txt").read_text(encoding="utf-8")
    assert "/validation_config.json" in profile.split()
    checkout = next(
        step
        for step in workflow["jobs"]["report"]["steps"]
        if step.get("name") == "Checkout report tooling"
    )
    assert "validation_config.json" in checkout["with"]["sparse-checkout"].split()
    for source in (text, VALIDATOR_CACHE_WORKFLOW.read_text(encoding="utf-8")):
        hashes = re.findall(
            r"hashFiles\('tools/validation/\*\*/\*\.py',[^)]*\)", source
        )
        assert hashes
        assert all(
            "'validation_config.json'" in h and "'tools/validation/**/*.txt'" in h
            for h in hashes
        )
        assert "'tools/validation/**'" not in source
    profile = (VALIDATION_DIR / "staged_sparse_profile.txt").read_text(encoding="utf-8")
    assert "/validation_config.json" in profile.split()
    assert classify(["validation_config.json"])["full_suite"] is True
    assert workflow["jobs"]["detect-changes"]["outputs"]["style_config"] == (
        "${{ steps.groups.outputs.style_config }}"
    )
    steps = workflow["jobs"]["mod-tests"]["steps"]
    collect = next(s for s in steps if s.get("name") == "Collect style-relevant files")
    assert "needs.detect-changes.outputs.style_config" in collect["env"]["STYLE_CONFIG"]
    assert "find common/national_focus -type f -name '*.txt'" in collect["run"]
    style = next(s for s in steps if s.get("name") == "Run style check")
    assert "has-files" in style["if"]


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
    for package in (
        "black==",
        "coverage==",
        "mypy==",
        "pylint==",
        "pytest-cov==",
        "pytest-xdist==",
        "ruff==",
    ):
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
    assert "--cov --cov-branch" in text
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
    assert [spec.name for spec in ALL_SPECS if not spec.strict] == ["simplifications"]


def test_ci_oob_units_does_not_enable_missing_equipment_factor():
    spec = _spec_for("validate_oob_units.py")
    assert spec.name == "oob-units"
    assert "--missing-equipment-factor" not in spec.args


def test_ci_party_loc_gate_is_registered_and_strict():
    spec = _spec_for("validate_party_loc.py")
    assert spec.name == "party-loc"
    assert spec.groups == ("localisation", "common")
    assert spec.strict is True


def test_ci_redundant_modifier_gate_is_strict():
    assert _spec_for("validate_modifiers.py").strict is True


def test_ci_idea_icon_check_is_enabled():
    assert _spec_for("validate_ideas.py").args == ("--missing-name-loc",)
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
    assert {
        "interface",
        "common",
        "events",
        "history",
        "localisation",
        "graphic-db",
    } <= set(_spec_for("validate_gfx_references.py").groups)
    assert "interface" in _spec_for("validate_scripted_localisation.py").groups


_BATCH_GROUPS = sorted({group for spec in ALL_SPECS for group in spec.groups})


def test_every_batch_group_change_starts_the_mod_tests_job():
    # prepare-workspace and mod-tests only run on `content`.
    outside = [
        pattern
        for group in _BATCH_GROUPS
        for pattern in GROUP_PATTERNS[group]
        if not classify([pattern.replace("**", "probe").replace("*", "probe")])[
            "content"
        ]
    ]
    assert not outside


@pytest.mark.skipif(
    sys.platform != "linux", reason="the step needs bash 4, which only Linux ships"
)
@pytest.mark.parametrize("full_suite", ("true", "false"))
def test_every_batch_group_reaches_the_validator_batch(tmp_path, full_suite):
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    outputs = workflow["jobs"]["detect-changes"]["outputs"]
    step = workflow_step("mod-tests", "Compute changed validator groups")
    env = {"GITHUB_OUTPUT": str(tmp_path / "output"), "G_FULL_SUITE": full_suite}
    for group in _BATCH_GROUPS:
        variable = "G_" + group.upper().replace("-", "_")
        assert outputs[group] == f"${{{{ steps.groups.outputs.{group} }}}}"
        assert f"outputs.{group} }}}}" in step["env"][variable]
        env[variable] = "true"

    result = run_bash_step(step["run"], tmp_path, env)

    assert result.returncode == 0, result.stderr
    emitted = (tmp_path / "output").read_text(encoding="utf-8")
    assert set(_BATCH_GROUPS) <= set(emitted.removeprefix("groups=").split())


def test_group_patterns_preserve_cross_reference_routes():
    assert "interface/**" in GROUP_PATTERNS["scientist-traits"]
    assert "interface/**" in GROUP_PATTERNS["mios"]
    assert "common/**/*.txt" in GROUP_PATTERNS["decisions"]
    assert "map/adjacency_rules.txt" in GROUP_PATTERNS["map-adjacency"]
    dirs = set()
    for pattern in (
        _CREATE_UNIT_SOURCE_PATTERNS
        + _DELETE_TEMPLATE_SOURCE_PATTERNS
        + _TEMPLATE_LIMIT_SOURCE_PATTERNS
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
