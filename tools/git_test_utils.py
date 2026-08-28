"""Git fixture helpers."""

import subprocess


def run_git(repository, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def initialize_git_repository(repository, *paths):
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "test@example.com")
    run_git(repository, "config", "user.name", "Test User")
    run_git(repository, "config", "diff.renames", "true")
    run_git(repository, "add", *paths)
    run_git(repository, "commit", "-m", "initial")
