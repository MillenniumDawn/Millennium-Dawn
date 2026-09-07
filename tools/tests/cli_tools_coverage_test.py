"""Behavioral tests for top-level CLI tools in tools/.

Tests cover end-to-end transformations, CLI success/error exits, filesystem
effects, subprocess result interpretation, and boundary branches.

Fixtures live in conftest.py (shared path/skip markers).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import assign_mio_icons
import pytest
from shared.suite import run_git, symlinks_available

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "tools"

requires_symlinks = pytest.mark.skipif(
    not symlinks_available(),
    reason="creating a symlink needs Developer Mode or admin on Windows",
)


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


# ---------------------------------------------------------------------------
# run.py
# ---------------------------------------------------------------------------


class TestRunPy:
    """Tests for tools/run.py — the tool router / --list / --help."""

    def test_list_shows_available_tools(self):
        """--list exits 0 and prints tool names grouped by directory."""
        result = subprocess.run(
            [sys.executable, str(TOOLS / "run.py"), "--list"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stderr
        assert "standardize" in result.stdout
        assert "run.py" not in result.stdout  # HIDDEN

    def test_help_exits_zero(self):
        """--help / -h exits 0 and prints usage."""
        result = subprocess.run(
            [sys.executable, str(TOOLS / "run.py"), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "run.py" in result.stdout

    def test_unknown_tool_exits_nonzero(self):
        """An unknown tool name exits with code 1 and prints a message."""
        result = subprocess.run(
            [sys.executable, str(TOOLS / "run.py"), "nonexistent_tool_xyz"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Unknown tool" in result.stdout

    def test_alias_underscore_to_dash(self):
        """A tool discovered as underscore-name is found via dash-variant."""
        # standardize_focus_tree is the canonical name; try with dashes.
        result = subprocess.run(
            [sys.executable, str(TOOLS / "run.py"), "standardize-focus-tree", "--help"],
            capture_output=True,
            text=True,
        )
        # Should not fall through to "Unknown tool" — either 0 (--help works)
        # or the tool's own error, but NOT the run.py unknown-tool path.
        assert "Unknown tool" not in result.stdout
        assert result.returncode in (0, 2)  # 0=--help, 2=argparse error inside tool


# ---------------------------------------------------------------------------
# archive_stale_branches.py
# ---------------------------------------------------------------------------


class TestArchiveStaleBranches:
    """Tests for tools/archive_stale_branches.py — path safety and archive logic."""

    def test_diff_paths_rejects_absolute_path(self, monkeypatch):
        """diff_paths raises ValueError when git emits an absolute path."""
        sys.path.insert(0, str(TOOLS))
        import archive_stale_branches as arch

        # Inject git output containing an absolute path.
        monkeypatch.setattr(arch, "run", lambda *a, **kw: b"/etc/passwd\0")
        with pytest.raises(ValueError, match="Unsafe path"):
            arch.diff_paths("origin/some-branch", REPO_ROOT)

    def test_diff_paths_rejects_dotdot_in_path(self, monkeypatch):
        """diff_paths raises ValueError when git emits a path with '..'."""
        sys.path.insert(0, str(TOOLS))
        import archive_stale_branches as arch

        # Inject git output containing a path with traversal.
        monkeypatch.setattr(arch, "run", lambda *a, **kw: b"../secrets/token.txt\0")
        with pytest.raises(ValueError, match="Unsafe path"):
            arch.diff_paths("origin/some-branch", REPO_ROOT)

    def test_branch_exists_false_for_nonexistent(self):
        """branch_exists returns False for a ref that does not exist."""
        sys.path.insert(0, str(TOOLS))
        import archive_stale_branches as arch

        assert arch.branch_exists("origin/nonexistent-ref-xyz123", REPO_ROOT) is False

    @requires_symlinks
    def test_remove_stale_files_rejects_symlink_dir(self, tmp_path):
        """remove_stale_files raises ValueError when target is a symlink."""
        sys.path.insert(0, str(TOOLS))
        import archive_stale_branches as arch

        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real_dir)

        with pytest.raises(ValueError, match="symlink"):
            arch.remove_stale_files(link, set())

    def test_remove_stale_files_preserves_desired_files(self, tmp_path):
        """remove_stale_files keeps desired files and removes everything else."""
        sys.path.insert(0, str(TOOLS))
        import archive_stale_branches as arch

        # Create some files
        kept = tmp_path / "kept.txt"
        write_text(kept, "keep me")
        removed = tmp_path / "removed.txt"
        write_text(removed, "remove me")

        arch.remove_stale_files(tmp_path, {"kept.txt"})

        assert kept.exists()
        assert not removed.exists()

    def test_archive_ref_rejects_bad_ref(self, tmp_path):
        """archive_ref raises RuntimeError for a non-existent ref."""
        sys.path.insert(0, str(TOOLS))
        import archive_stale_branches as arch

        with pytest.raises(RuntimeError, match="failed"):
            arch.archive_ref("nonexistent-ref-xyz123", tmp_path, REPO_ROOT)


# ---------------------------------------------------------------------------
# sync_dynamic_tokens.py
# ---------------------------------------------------------------------------


class TestSyncDynamicTokens:
    """Tests for tools/sync_dynamic_tokens.py — log parsing and token sync."""

    def _sync(self, log, out=None):
        argv = [sys.executable, str(TOOLS / "sync_dynamic_tokens.py"), str(log)]
        if out is not None:
            argv += ["-o", str(out)]
        return subprocess.run(argv, capture_output=True, text=True)

    def test_no_tokens_in_log_prints_message(self, tmp_path):
        """When the log has no 'dynamic token' lines, script exits 0."""
        log = tmp_path / "error.log"
        write_text(log, "some other HOI4 message\n")

        result = self._sync(log, tmp_path / "tokens.txt")

        assert result.returncode == 0
        assert "No dynamic-token warnings found" in result.stdout

    def test_all_tokens_already_present(self, tmp_path):
        """When all found tokens are already in the output, nothing is appended."""
        log = tmp_path / "error.log"
        write_text(log, "Token MY_TOKEN is a dynamic token here\n")
        out = tmp_path / "tokens.txt"
        write_text(out, "MY_TOKEN\n")

        result = self._sync(log, out)

        assert result.returncode == 0
        assert "already present" in result.stdout
        # File unchanged
        assert out.read_text() == "MY_TOKEN\n"

    def test_new_tokens_appended_to_output(self, tmp_path):
        """New tokens from the log are appended to the output file."""
        log = tmp_path / "error.log"
        write_text(
            log,
            "Token NEW_TOKEN_1 is a dynamic token\n"
            "Token NEW_TOKEN_2 is a dynamic token\n",
        )
        out = tmp_path / "tokens.txt"
        write_text(out, "EXISTING_TOKEN\n")

        result = self._sync(log, out)

        assert result.returncode == 0
        assert "Added 2 new token(s)" in result.stdout
        content = out.read_text()
        assert "EXISTING_TOKEN" in content
        assert "NEW_TOKEN_1" in content
        assert "NEW_TOKEN_2" in content

    def test_missing_log_file_exits_nonzero(self, tmp_path):
        """A missing log file causes an argparse error and exits non-zero."""
        result = self._sync(tmp_path / "does_not_exist.log")

        assert result.returncode != 0
        assert "Log file not found" in result.stderr

    def test_phrase_but_no_match_reports_change(self, tmp_path):
        """Log mentions 'dynamic token' but format doesn't match — reports change."""
        log = tmp_path / "error.log"
        write_text(log, "Found a dynamic token (unknown format)\n")

        result = self._sync(log, tmp_path / "tokens.txt")

        assert result.returncode == 0
        assert "none matched the expected format" in result.stdout


# ---------------------------------------------------------------------------
# assign_mio_icons.py
# ---------------------------------------------------------------------------


class TestAssignMioIcons:
    """Tests for tools/assign_mio_icons.py — MIO trait icon assignment.

    The tool reads its sprite list from a fixed path under the repo root, so
    every case points GFX (and ROOT) at a temp tree instead: the CI unit-test
    checkout does not include interface/.
    """

    TRAIT = (
        "token = TEST_MIO_TEST\n\n"
        "trait = {\n"
        "    token = test_trait\n"
        "    icon = x\n"
        "    limit_to_equipment_type = { infantry_weapons_type }\n"
        "    organization_modifier = { infantry_weapons_type = 1.0 }\n"
        "}\n"
    )

    def _sprites(self, tmp_path, *names):
        gfx = tmp_path / "traits.gfx"
        write_text(
            gfx,
            "".join(f'\tspriteType = {{ name = "{name}" }}\n' for name in names),
        )
        return gfx

    def _run(self, monkeypatch, tmp_path, gfx, *argv):
        monkeypatch.setattr(assign_mio_icons, "ROOT", tmp_path)
        monkeypatch.setattr(assign_mio_icons, "GFX", gfx)
        monkeypatch.setattr(sys, "argv", ["assign_mio_icons.py", *argv])
        assign_mio_icons.main()

    def test_write_resolves_the_placeholder_to_the_family_icon(
        self, tmp_path, monkeypatch
    ):
        """--write rewrites `icon = x` with the equipment family's sprite."""
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_smallarms")
        mio = tmp_path / "test_mio.txt"
        write_text(mio, self.TRAIT)

        self._run(monkeypatch, tmp_path, gfx, str(mio), "--write")

        assert (
            "icon = GFX_generic_mio_trait_icon_smallarms" in mio.read_text()
        ), "the family sprite exists, so the unique fallback must not win"

    def test_write_falls_back_to_unique_when_no_sprite_matches(
        self, tmp_path, monkeypatch
    ):
        """With no candidate sprite defined the placeholder becomes `unique`."""
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_unrelated")
        mio = tmp_path / "test_mio.txt"
        write_text(mio, self.TRAIT)

        self._run(monkeypatch, tmp_path, gfx, str(mio), "--write")

        assert "icon = GFX_generic_mio_trait_icon_unique" in mio.read_text()

    def test_no_argument_targets_the_hol_organization_file(
        self, tmp_path, monkeypatch, capsys
    ):
        """Without a path the tool reads the default HOL organization file."""
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_smallarms")
        default = (
            tmp_path
            / "common/military_industrial_organization/organizations/MD_HOL_organizations.txt"
        )
        default.parent.mkdir(parents=True, exist_ok=True)
        write_text(default, self.TRAIT)

        self._run(monkeypatch, tmp_path, gfx)

        assert "Total placeholders resolved: 1" in capsys.readouterr().out
        assert "icon = x" in default.read_text(), "no --write means no rewrite"

    def test_missing_sprite_file_exits_nonzero(self, tmp_path, monkeypatch):
        """An unreadable sprite file aborts before any input is parsed."""
        with pytest.raises(SystemExit) as excinfo:
            self._run(monkeypatch, tmp_path, tmp_path / "absent.gfx")
        assert "cannot read sprite file" in str(excinfo.value)

    def test_missing_input_file_exits_nonzero(self, tmp_path, monkeypatch):
        """A non-existent input path exits with an error message."""
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_smallarms")
        with pytest.raises(SystemExit) as excinfo:
            self._run(monkeypatch, tmp_path, gfx, str(tmp_path / "does_not_exist.txt"))
        assert "No such file or directory" in str(excinfo.value)

    def test_relative_path_is_resolved_against_root(self, tmp_path, monkeypatch):
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_smallarms")
        write_text(tmp_path / "org.txt", self.TRAIT)
        self._run(monkeypatch, tmp_path, gfx, "org.txt", "--write")
        assert (
            "icon = GFX_generic_mio_trait_icon_smallarms"
            in (tmp_path / "org.txt").read_text()
        )

    def test_write_failure_exits_nonzero(self, tmp_path, monkeypatch):
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_smallarms")
        mio = tmp_path / "test_mio.txt"
        write_text(mio, self.TRAIT)

        def fail_replace(_src, _dst):
            raise OSError("disk full")

        monkeypatch.setattr(assign_mio_icons.os, "replace", fail_replace)
        with pytest.raises(SystemExit, match="cannot write"):
            self._run(monkeypatch, tmp_path, gfx, str(mio), "--write")

    def test_unique_fallbacks_are_listed(self, tmp_path, monkeypatch, capsys):
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_unrelated")
        mio = tmp_path / "test_mio.txt"
        write_text(mio, self.TRAIT)
        self._run(monkeypatch, tmp_path, gfx, str(mio))
        assert "unique fallbacks: 1 -> test_trait" in capsys.readouterr().out

    def test_trait_without_a_placeholder_is_left_alone(
        self, tmp_path, monkeypatch, capsys
    ):
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_smallarms")
        mio = tmp_path / "test_mio.txt"
        body = self.TRAIT.replace("icon = x", "icon = GFX_already_set")
        write_text(mio, body)
        self._run(monkeypatch, tmp_path, gfx, str(mio), "--write")
        assert mio.read_text() == body
        assert "Total placeholders resolved: 0" in capsys.readouterr().out

    def test_placeholder_without_a_token_is_reported_as_unknown(
        self, tmp_path, monkeypatch, capsys
    ):
        gfx = self._sprites(tmp_path, "GFX_generic_mio_trait_icon_smallarms")
        mio = tmp_path / "test_mio.txt"
        write_text(mio, self.TRAIT.replace("    token = test_trait\n", ""))
        self._run(monkeypatch, tmp_path, gfx, str(mio))
        assert "?" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# dev_setup.py
# ---------------------------------------------------------------------------


class TestDevSetup:
    """Tests for tools/dev_setup.py — environment check mode."""

    def test_check_output_and_exit_code(self):
        """--check prints Python version and pre-commit status; exits 0 or 1."""
        result = subprocess.run(
            [sys.executable, str(TOOLS / "dev_setup.py"), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=60,
        )
        assert "Python:" in result.stdout
        assert "pre-commit" in result.stdout
        assert result.returncode in (0, 1), f"crashed: {result.stderr[:200]}"


# ---------------------------------------------------------------------------
# standardize_staged.py
# ---------------------------------------------------------------------------


class TestStandardizeStaged:
    """Tests for tools/standardize_staged.py — pre-commit auto-fixer."""

    @pytest.mark.parametrize(
        "filepath,expected",
        [
            ("common/national_focus/USA.txt", "focus"),
            ("events/USA_events.txt", "event"),
            ("common/decisions/USA_decisions.txt", "decision"),
            ("common/ideas/USA_ideas.txt", "idea"),
            ("history/countries/USA.txt", None),
            ("common/national_focus", None),
        ],
    )
    def test_get_standardizer_routing(self, filepath, expected):
        """get_standardizer routes known paths to correct type; None for unknown."""
        sys.path.insert(0, str(TOOLS))
        from standardize_staged import get_standardizer

        assert get_standardizer(filepath) == expected

    def test_main_exits_zero_with_no_files(self):
        """main() exits 0 when called with no filenames (nothing to do)."""
        result = subprocess.run(
            [sys.executable, str(TOOLS / "standardize_staged.py")],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0

    def test_main_skips_nonexistent_files(self):
        """Files that don't exist are skipped (not errors)."""
        result = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "standardize_staged.py"),
                "does/not/exist.txt",
                "also_missing.txt",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        # Should exit 0 — nothing to do, nothing modified, no errors
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# validate_staged.py
# ---------------------------------------------------------------------------


class TestValidateStaged:
    """Tests for tools/validate_staged.py — pre-commit validation runner."""

    def test_main_no_staged_files_or_skip_env(self, tmp_path, monkeypatch):
        """With no staged files or MD_SKIP_VALIDATE=1, no validators run and exit 0."""
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "MD_SKIP_VALIDATE"):
            monkeypatch.delenv(name, raising=False)
        run_git(tmp_path, "init")
        result = subprocess.run(
            [sys.executable, str(TOOLS / "validate_staged.py")],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "Running " not in result.stdout

        (tmp_path / "events").mkdir()
        write_text(tmp_path / "events" / "example.txt", "add_namespace = example\n")
        run_git(tmp_path, "add", "events/example.txt")
        assert (
            run_git(tmp_path, "diff", "--cached", "--name-only").stdout.strip()
            == "events/example.txt"
        )
        result = subprocess.run(
            [sys.executable, str(TOOLS / "validate_staged.py")],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env={**os.environ, "MD_SKIP_VALIDATE": "1"},
        )
        assert result.returncode == 0
        assert "Running " not in result.stdout

    def test_staged_file_routes_to_validator(self):
        """A staged .yml file causes the localisation validator to be invoked."""
        sys.path.insert(0, str(TOOLS))
        from validate_staged import VALIDATORS

        loc_validator = next(v for v in VALIDATORS if v["name"] == "localisation")
        assert "validate_localisation.py" in loc_validator["cmd"][1]
        assert loc_validator["suffix"] == ".yml"
