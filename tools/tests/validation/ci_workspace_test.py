"""The CI sparse workspace includes validator inputs, not unrelated art or audio."""

import subprocess

import yaml
from shared.paths import REPO_ROOT
from shared.suite import initialize_git_repository, write_under_str

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
