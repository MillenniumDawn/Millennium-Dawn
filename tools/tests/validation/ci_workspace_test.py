"""The CI sparse workspace includes validator inputs, not unrelated art or audio."""

import shlex
import subprocess

import yaml
from shared.paths import REPO_ROOT
from shared.suite import initialize_git_repository, run_git, write_under_str

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


def test_staged_fetch_keeps_unrelated_blobs_missing(tmp_path):
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/test-suite.yml").read_text(encoding="utf-8")
    )
    fetch = next(
        step["run"]
        for step in workflow["jobs"]["tools-tests"]["steps"]
        if step.get("id") == "staged-fetch"
    )
    source = tmp_path / "source"
    art = "gfx/interface/portraits/probe.dds"
    write_under_str(source, "common/probe.txt", "initial content\n")
    write_under_str(source, "gfx/flags/probe.tga", "flag content\n")
    write_under_str(source, art, "initial unused art\n")
    initialize_git_repository(source, ".")
    run_git(source, "branch", "base")
    run_git(source, "config", "uploadpack.allowFilter", "true")
    write_under_str(source, "common/probe.txt", "updated content\n")
    write_under_str(source, art, "updated unused art\n")
    run_git(source, "commit", "-am", "target revision")
    target = run_git(source, "rev-parse", "HEAD").stdout.strip()
    art_oid = run_git(source, "rev-parse", f"{target}:{art}").stdout.strip()
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
    command = shlex.split(
        fetch.replace(
            "https://github.com/${{ github.repository }}.git", source.as_uri()
        ).replace("${{ github.sha }}", target)
    )
    assert command[:2] == ["git", "fetch"]
    assert "--depth=1" in command
    run_git(checkout, *command[1:])
    missing = run_git(
        checkout, "rev-list", "--objects", target, "--missing=print"
    ).stdout.splitlines()
    assert f"?{art_oid}" in missing

    worktree = tmp_path / "staged"
    run_git(
        checkout, "worktree", "add", "--detach", "--no-checkout", str(worktree), target
    )
    profile = (REPO_ROOT / "tools/validation/staged_sparse_profile.txt").read_text(
        encoding="utf-8"
    )
    run_git(worktree, "sparse-checkout", "set", "--no-cone", *profile.splitlines())
    run_git(worktree, "checkout", target)
    assert (worktree / "common/probe.txt").read_text(
        encoding="utf-8"
    ) == "updated content\n"
    assert (worktree / "gfx/flags/probe.tga").is_file()
    assert not (worktree / art).exists()
    missing = run_git(
        checkout, "rev-list", "--objects", target, "--missing=print"
    ).stdout.splitlines()
    assert f"?{art_oid}" in missing


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
