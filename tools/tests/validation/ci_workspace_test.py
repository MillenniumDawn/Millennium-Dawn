"""The CI sparse workspace includes validator inputs, not unrelated art or audio."""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import PurePosixPath

import pytest
import yaml
from shared.paths import REPO_ROOT
from shared.suite import (
    initialize_git_repository,
    run_bash_step,
    run_git,
    substitute_expressions,
    workflow_step,
    write_under_str,
)

PROFILE = "tools/validation/ci_workspace_profile.txt"


def test_workspace_profile_materializes_only_validator_inputs(tmp_path):
    included = [
        "common/probe.txt",
        "events/probe.txt",
        "history/probe.txt",
        "localisation/english/probe.yml",
        "interface/core.gfx",
        "gfx/flags/probe.tga",
        "gfx/interface/decisions/probe.dds",
        "map/adjacency_rules.txt",
        "music/playlists/probe.txt",
        "resources/documentation/probe.md",
        ".claude/docs/typo-watchlist.md",
        ".github/actions/setup-md-python/action.yml",
        "CLAUDE.md",
        "pyproject.toml",
        "validation_config.json",
        "descriptor.mod",
    ]
    excluded = [
        "gfx/interface/portraits/probe.dds",
        "resources/vanilla/interface/probe.gfx",
        "map/provinces.bmp",
        "music/probe.ogg",
        "music/albums/probe.mp3",
        "music/probe.wav",
    ]
    for relative in included + excluded:
        write_under_str(tmp_path, relative, "probe\n")
    profile = (REPO_ROOT / PROFILE).read_text(encoding="utf-8")
    write_under_str(tmp_path, PROFILE, profile)
    initialize_git_repository(tmp_path, ".")
    result = subprocess.run(
        ["git", "sparse-checkout", "set", "--no-cone", "--stdin"],
        cwd=tmp_path,
        input=profile,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stderr == ""
    assert all((tmp_path / relative).is_file() for relative in included + [PROFILE])
    assert not any((tmp_path / relative).exists() for relative in excluded)


ART = "gfx/interface/portraits/probe.dds"
# Shipped by the CI workspace profile but not the staged one.
OUTSIDE_STAGED = ("gfx/interface/decisions/probe.dds", "localisation/french/p.yml")


def _staged_fetch(tmp_path):
    """Run the workflow's staged fetch into a blobless clone of an older base.

    Returns (checkout, target sha, oid of unrelated art the target changed)."""
    source = tmp_path / "source"
    for relative in ("common/probe.txt", "gfx/flags/probe.tga", ART, *OUTSIDE_STAGED):
        write_under_str(source, relative, f"initial {relative}\n")
    initialize_git_repository(source, ".")
    run_git(source, "branch", "base")
    run_git(source, "config", "uploadpack.allowFilter", "true")
    write_under_str(source, "common/probe.txt", "updated content\n")
    write_under_str(source, ART, "updated unused art\n")
    run_git(source, "commit", "-am", "target revision")
    target = run_git(source, "rev-parse", "HEAD").stdout.strip()
    checkout = tmp_path / "checkout"
    run_git(
        tmp_path,
        "clone",
        "--filter=blob:none",
        "--depth=1",
        "--no-checkout",
        "--branch",
        "base",
        source.as_uri(),
        str(checkout),
    )
    fetch = workflow_step("tools-quality", "Fetch PR head for staged integration")
    command = shlex.split(
        substitute_expressions(
            fetch["run"],
            {
                "needs.detect-changes.outputs.checkout-repository": "owner/repo",
                "needs.detect-changes.outputs.head-sha": target,
            },
        ).replace("https://github.com/owner/repo.git", source.as_uri())
    )
    assert command[:2] == ["git", "fetch"]
    assert "--depth=1" in command
    run_git(checkout, *command[1:])
    art_oid = run_git(source, "rev-parse", f"{target}:{ART}").stdout.strip()
    return checkout, target, art_oid


def _art_blob_missing(checkout, target, art_oid):
    missing = run_git(
        checkout, "rev-list", "--objects", target, "--missing=print"
    ).stdout.splitlines()
    return f"?{art_oid}" in missing


def test_staged_fetch_keeps_unrelated_blobs_missing(tmp_path):
    checkout, target, art_oid = _staged_fetch(tmp_path)
    assert _art_blob_missing(checkout, target, art_oid)


@pytest.mark.skipif(sys.platform == "win32", reason="the step runs in bash on Linux")
def test_staged_worktree_step_checks_out_only_the_staged_profile(tmp_path):
    checkout, target, art_oid = _staged_fetch(tmp_path)
    for profile in ("staged_sparse_profile.txt", "ci_workspace_profile.txt"):
        body = (REPO_ROOT / "tools/validation" / profile).read_text(encoding="utf-8")
        write_under_str(checkout, f"tools/validation/{profile}", body)
    step = workflow_step("tools-quality", "Create staged integration worktree")
    script = substitute_expressions(
        step["run"],
        {
            "runner.temp": str(tmp_path / "runner"),
            "needs.detect-changes.outputs.head-sha": target,
        },
    )

    result = run_bash_step(script, checkout)

    assert result.returncode == 0, result.stdout + result.stderr
    worktree = tmp_path / "runner" / "md-staged-validator-test"
    assert (worktree / "common/probe.txt").read_text(
        encoding="utf-8"
    ) == "updated content\n"
    assert (worktree / "gfx/flags/probe.tga").is_file()
    assert not any((worktree / path).exists() for path in (ART, *OUTSIDE_STAGED))
    assert _art_blob_missing(checkout, target, art_oid)


def _gnu_tar_with_zstd():
    if sys.platform == "win32" or shutil.which("zstd") is None:
        return False
    version = subprocess.run(["tar", "--version"], capture_output=True, text=True)
    return "GNU tar" in version.stdout


requires_gnu_tar = pytest.mark.skipif(
    not _gnu_tar_with_zstd(), reason="the workspace archive uses GNU tar and zstd"
)


def _extract_workspace(archive_dir, destination):
    step = workflow_step("mod-tests", "Extract prepared workspace")
    destination.mkdir()
    return run_bash_step(step["run"], destination, {"RUNNER_TEMP": str(archive_dir)})


@requires_gnu_tar
def test_workspace_archive_ships_the_declared_paths_without_git(tmp_path):
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/test-suite.yml").read_text(encoding="utf-8")
    )
    workspace_paths = workflow["env"]["WORKSPACE_PATHS"]
    shipped = [".workspace-manifest", ".validation_cache/v9/cache.db"]
    for entry in workspace_paths.split():
        entry = entry.replace("*", "descriptor")
        shipped.append(entry if PurePosixPath(entry).suffix else f"{entry}/probe")
    left_out = [".git/HEAD", "gfx/interface/portraits/probe.dds"]
    workspace = tmp_path / "workspace"
    for relative in shipped + left_out:
        write_under_str(workspace, relative, relative)
    runner = tmp_path / "runner"
    runner.mkdir()
    pack = workflow_step("prepare-workspace", "Pack prepared workspace")
    env = {"RUNNER_TEMP": str(runner), "WORKSPACE_PATHS": workspace_paths}

    packed = run_bash_step(pack["run"], workspace, env)
    extracted = _extract_workspace(runner, tmp_path / "mod")

    assert packed.returncode == 0, packed.stderr
    assert extracted.returncode == 0, extracted.stdout + extracted.stderr
    mod = tmp_path / "mod"
    assert all((mod / relative).is_file() for relative in shipped)
    assert not any((mod / relative).exists() for relative in left_out)


@requires_gnu_tar
@pytest.mark.parametrize("link", ["symlink", "hardlink"])
def test_workspace_extraction_rejects_links(tmp_path, link):
    staged = tmp_path / "staged"
    write_under_str(staged, "common/real.txt", "real\n")
    if link == "symlink":
        (staged / "common/link").symlink_to("/etc")
    else:
        os.link(staged / "common/real.txt", staged / "common/link")
    runner = tmp_path / "runner"
    runner.mkdir()
    archive = runner / "prepared-workspace.tar.zst"
    subprocess.run(
        ["tar", "--zstd", "-cf", str(archive), "common"], cwd=staged, check=True
    )

    result = _extract_workspace(runner, tmp_path / "mod")

    assert result.returncode == 1
    assert "link or special file" in result.stdout
    assert not any((tmp_path / "mod").iterdir())


def test_every_workspace_consumer_extracts_the_single_file_archive():
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/test-suite.yml").read_text(encoding="utf-8")
    )
    upload = workflow_step("prepare-workspace", "Upload prepared workspace")
    assert upload["with"]["path"] == "${{ runner.temp }}/prepared-workspace.tar.zst"
    assert upload["with"]["compression-level"] == 0
    consumers = []
    for name, job in workflow["jobs"].items():
        steps = job.get("steps", [])
        for index, step in enumerate(steps):
            if step.get("with", {}).get("name") == "prepared-workspace":
                consumers.append(name)
                if "download-artifact" in step.get("uses", ""):
                    assert step["with"]["path"] == "${{ runner.temp }}"
                    assert steps[index + 1]["name"] == "Extract prepared workspace"
    assert consumers == ["prepare-workspace", "mod-tests"]


def test_cache_builder_and_pr_workspace_use_the_same_profile():
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/validator-cache.yml").read_text(
            encoding="utf-8"
        )
    )
    steps = workflow["jobs"]["build-cache"]["steps"]
    checkout = next(step for step in steps if step.get("name") == "Checkout code")
    assert checkout["with"]["sparse-checkout"] == "/" + PROFILE
    assert checkout["with"]["sparse-checkout-cone-mode"] is False
    materialize = next(
        step for step in steps if step.get("name") == "Materialize validator workspace"
    )
    assert "git sparse-checkout set --no-cone --stdin" in materialize["run"]
    assert PROFILE in materialize["run"]


def test_pip_cache_tracks_the_dependency_groups_manifest():
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/actions/setup-md-python/action.yml").read_text(
            encoding="utf-8"
        )
    )
    setup = workflow["runs"]["steps"][0]
    assert setup["with"]["cache-dependency-path"] == "pyproject.toml"
    assert "inputs.install == 'true'" in setup["with"]["cache"]


def test_merge_driver_checkout_includes_its_ordering_dependency():
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/changelog-conflict-fixer.yml").read_text(
            encoding="utf-8"
        )
    )
    checkout = workflow["jobs"]["fix-changelog-conflicts"]["steps"][0]
    assert {
        "/tools/merge_changelog.py",
        "/tools/linting/check_changelog.py",
    } <= set(checkout["with"]["sparse-checkout"].split())
