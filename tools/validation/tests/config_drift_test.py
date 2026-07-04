"""Drift guard between the two places the validator set is declared.

Every validator in `tools/validation/validate_*.py` is wired independently into
`.pre-commit-config.yaml` (the `md-validate-*` hooks) and into
`.github/workflows/coding-pipeline.yml` (the `validate-core` /
`validate-targeted` matrices). Those two lists are hand-maintained and drift: a
validator gets added to one and forgotten in the other, or `--strict` is set on
one side only. These tests fail when that happens, so the gap surfaces at PR
time instead of as a "passed locally, failed CI" surprise.

Scope is `tools/validation/validate_*.py` only. The linting scripts in
`tools/linting/` (coding_standards, check_basic_style*, check_common_mistakes)
are few, stable, and not matrix-driven, so they are out of scope here.

Intentional exceptions live in the EXEMPT / ALLOWED sets below, each with a
reason. The guard also checks those sets stay current: an exemption that no
longer applies (the validator got wired, or deleted) fails the test so the
stale entry gets removed.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_DIR = Path(__file__).resolve().parents[1]
PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "coding-pipeline.yml"

# Validators intentionally absent from the CI matrices. Each needs a reason.
CI_EXEMPT = {
    # Needs vanilla HOI4 00_defines.lua, which isn't checked into the repo, so
    # it can only run as a contributor's pre-commit hook.
    "validate_defines.py",
    # ~22k pre-existing unreferenced textures plus a slow full-repo scan make
    # this a periodic mod-size audit, not a per-PR gate. Manual hook only.
    "validate_unused_textures.py",
}

# Validators intentionally without a pre-commit hook. Each needs a reason.
PRECOMMIT_EXEMPT = set()

# Validators whose --strict setting intentionally differs between pre-commit and
# CI, because of a pre-existing backlog. Clear the backlog, then remove the
# entry so both sides gate identically.
STRICT_MISMATCH_ALLOWED = {
    # CI runs --strict; pre-commit runs without it because pre-existing
    # equipment-coverage gaps would otherwise block every commit.
    "validate_ai_equipment.py",
    # pre-commit runs --strict; CI runs informational (strict: false) because of
    # ~30 pre-existing undefined-idea references on main awaiting triage.
    "validate_ideas.py",
}


def _discover_disk_validators():
    return {p.name for p in VALIDATION_DIR.glob("validate_*.py")}


def _parse_precommit():
    """Map validate_*.py -> {'strict': bool, 'stage': 'default'|'manual'}."""
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
    return result


def _parse_ci():
    """Map validate_*.py -> {'strict': bool} from the two validator matrices."""
    wf = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    result = {}
    for job in ("validate-core", "validate-targeted"):
        matrix = wf["jobs"][job]["strategy"]["matrix"]["validator"]
        for entry in matrix:
            # CI Run step passes --strict unless `strict: false` is set.
            result[entry["script"]] = {"strict": entry.get("strict", True) is not False}
    return result


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


def test_every_disk_validator_runs_on_ci(disk, ci):
    missing = sorted(disk - set(ci) - CI_EXEMPT)
    assert not missing, (
        "Validators exist on disk but are not in the CI matrices "
        f"(coding-pipeline.yml): {missing}. Add each to validate-core or "
        "validate-targeted, or add it to CI_EXEMPT with a reason."
    )


def test_every_disk_validator_is_a_precommit_hook(disk, precommit):
    missing = sorted(disk - set(precommit) - PRECOMMIT_EXEMPT)
    assert not missing, (
        "Validators exist on disk but have no md-validate-* hook "
        f"(.pre-commit-config.yaml): {missing}. Add a hook, or add it to "
        "PRECOMMIT_EXEMPT with a reason."
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
