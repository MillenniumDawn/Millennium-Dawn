"""Behavioral tests for tools/publishing/publish_workshop.py.

Covers manifest/config constants, exclude logic, VDF escaping, size/time
formatting, descriptor patching, VDF generation, mod-file validation,
publishable-file filtering, dir/prune utilities, and the steamcmd upload and
CLI flows.

No mocks for filesystem behavior — temp dirs exercise the actual code paths.
The steamcmd child process, the `git archive` stream, and `git diff` are
scripted so nothing is ever uploaded or shelled out for real.
"""

from __future__ import annotations

import io
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

import pytest

from tools.publishing import publish_workshop as pw


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


# ---------------------------------------------------------------------------
# Config / manifest constants
# ---------------------------------------------------------------------------


def test_config_targets_consistent():
    assert (
        set(pw.MOD_IDS.keys())
        == set(pw.MOD_NAMES.keys())
        == {
            "release",
            "beta",
            "test",
        }
    )


def test_config_values_valid():
    for key in pw.MOD_IDS:
        assert pw.MOD_IDS[key].isdigit(), f"{key} mod ID not numeric"
    for key in pw.MOD_NAMES:
        assert len(pw.MOD_NAMES[key]) > 0, f"{key} name empty"
    assert "descriptor.mod" in pw.ALWAYS_KEEP
    assert "thumbnail.png" in pw.ALWAYS_KEEP
    assert pw.DEFAULT_EXCLUDES == pw.ROOT_ONLY_EXCLUDES | pw.ANYWHERE_EXCLUDES


# ---------------------------------------------------------------------------
# Pure helpers — each parametrize covers N input/output cases in 1 test
# ---------------------------------------------------------------------------

_EXCLUDES = pw.DEFAULT_EXCLUDES


@pytest.mark.parametrize(
    "path_str,expected",
    [
        # Root-only pattern: applies only at depth 1 (the repo root).
        (".gitignore", True),
        ("docs/.gitignore", True),
        # Anywhere patterns.
        ("common/.git", True),
        (".github/workflows/ci.yml", True),
        ("docs/a.txt", True),
        ("docs/sub/b.txt", True),
        ("tools/validate.py", True),
        ("resources/image.png", True),
        ("__pycache__/foo.pyo", True),
        ("common/foo.pyo", True),
        # Allowed files.
        ("common/national_focus/germany.txt", False),
        ("events/00_events.txt", False),
        ("localisation/english/md_l_english.yml", False),
        # Root-only with custom excludes: only root-level matches.
        ("README.md", True),
        ("subdir/README.md", False),
    ],
)
def test_archive_path_excluded(path_str, expected):
    assert pw._archive_path_excluded(PurePosixPath(path_str), _EXCLUDES) is expected


@pytest.mark.parametrize(
    "n,expected",
    [
        (500, "500.0 B"),
        (2048, "2.0 KB"),
        (2 * 1024 * 1024, "2.0 MB"),
        (int(1.5 * 1024**3), "1.5 GB"),
        (0, "0.0 B"),
    ],
)
def test_format_size(n, expected):
    assert pw.format_size(n) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("hello world", "hello world"),
        ("path\\to\\file", "path\\\\to\\\\file"),
        ('say "hello"', 'say \\"hello\\"'),
        ("line1\rline2", "line1\\rline2"),
        ("line1\nline2", "line1\\nline2"),
        (PurePosixPath("/tmp/mod"), "/tmp/mod"),
        ('"quoted"\\npath', '\\"quoted\\"\\\\npath'),
    ],
)
def test_escape_vdf(value, expected):
    assert pw.escape_vdf(value) == expected


@pytest.mark.parametrize(
    "elapsed,expected",
    [
        (0, "0s"),
        (90, "1m 30s"),
        (120, "2m 00s"),
    ],
)
def test_elapsed_str(monkeypatch, elapsed, expected):
    monkeypatch.setattr(pw.time, "time", lambda: 1_000)
    assert pw.elapsed_str(1_000 - elapsed) == expected


# ---------------------------------------------------------------------------
# Descriptor patching
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "original,target_name,mod_id,version,expect_lines",
    [
        # All three fields present and updated.
        (
            'name="Old"\nversion="0.0.1"\nremote_file_id="000"\n',
            "New",
            "1234567890",
            "1.2.3",
            ['name="New"', 'remote_file_id="1234567890"', 'version="1.2.3"'],
        ),
        # version=None → version line left untouched.
        (
            'name="My Mod"\nversion="5.0.0"\nremote_file_id="999"\n',
            "My Mod",
            "123",
            None,
            ['name="My Mod"', 'remote_file_id="123"', 'version="5.0.0"'],
        ),
        # remote_file_id absent → appended.
        (
            'name="Partial"\n',
            "Full Name",
            "555",
            None,
            ['name="Full Name"', 'remote_file_id="555"'],
        ),
    ],
)
def test_patch_descriptor(
    tmp_path, original, target_name, mod_id, version, expect_lines
):
    descriptor = tmp_path / "descriptor.mod"
    write_text(descriptor, original)
    pw.patch_descriptor(tmp_path, target_name, mod_id, version)
    lines = descriptor.read_text(encoding="utf-8").splitlines()
    for line in expect_lines:
        assert line in lines, f"Expected {line!r} in patched descriptor"


def test_patch_descriptor_missing_file_warns(tmp_path, capsys):
    pw.patch_descriptor(tmp_path, "Name", "123", None)
    out = capsys.readouterr().out
    assert "WARNING" in out or "warning" in out.lower()


# ---------------------------------------------------------------------------
# VDF generation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "changenote,assertions",
    [
        # Valid structure: appid, mod_id, and changenote all present.
        (
            "Bugfix release",
            {
                '"394360"',
                '"2777392649"',
                "Bugfix release",
            },
        ),
        # Raw newlines in changenote must be escaped.
        (
            "Line1\nLine2",
            {"\\n"},
        ),
    ],
    ids=["valid_structure", "newline_escaped"],
)
def test_write_vdf(tmp_path, changenote, assertions):
    mod_dir = tmp_path / "content"
    mod_dir.mkdir()
    mod_dir.joinpath("thumbnail.png").write_bytes(b"\x89PNG")
    vdf_path = pw.write_vdf(mod_dir, "2777392649", changenote)
    content = vdf_path.read_text(encoding="utf-8")
    for needle in assertions:
        assert needle in content


def test_write_vdf_newline_translation(tmp_path):
    mod_dir = tmp_path / "content"
    mod_dir.mkdir()
    mod_dir.joinpath("thumbnail.png").write_bytes(b"\x89PNG")
    vdf_path = pw.write_vdf(mod_dir, "123", "Note")
    assert b"\r\n" not in vdf_path.read_bytes()


# ---------------------------------------------------------------------------
# Mod-file validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "present,missing",
    [
        ({"descriptor.mod", "thumbnail.png"}, None),
        ({"thumbnail.png"}, "descriptor.mod"),
        ({"descriptor.mod"}, "thumbnail.png"),
    ],
    ids=["all_present", "descriptor_missing", "thumbnail_missing"],
)
def test_validate_mod_files(tmp_path, present, missing):
    if "descriptor.mod" in present:
        write_text(tmp_path / "descriptor.mod", "name=x\n")
    if "thumbnail.png" in present:
        (tmp_path / "thumbnail.png").write_bytes(b"\x89PNG")

    if missing is None:
        pw.validate_mod_files(tmp_path)
    else:
        with pytest.raises(SystemExit, match=missing):
            pw.validate_mod_files(tmp_path)


# ---------------------------------------------------------------------------
# Publishable-file filtering
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "files_in_mod,changed,expected",
    [
        # Files present and in changed set → returned.
        (
            {"events/new_event.txt", "descriptor.mod"},
            {"events/new_event.txt", "descriptor.mod"},
            {"events/new_event.txt", "descriptor.mod"},
        ),
        # Changed file not present on disk → excluded.
        (
            {"events/existing.txt"},
            {"events/new_file.txt"},
            set(),
        ),
    ],
    ids=["changed_tracked", "changed_not_on_disk"],
)
def test_get_publishable_changed_files(tmp_path, files_in_mod, changed, expected):
    mod_dir = tmp_path / "mod"
    mod_dir.mkdir()
    for rel in files_in_mod:
        p = mod_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        write_text(p, "content")
    result = pw.get_publishable_changed_files(mod_dir, changed)
    assert result == expected


# ---------------------------------------------------------------------------
# dir_stats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "setup,expected_count,expected_total",
    [
        ({"a.txt": 100, "b.txt": 50, "sub/c.txt": 25}, 3, 175),
        ({}, 0, 0),
    ],
    ids=["three_files", "empty_dir"],
)
def test_dir_stats(tmp_path, setup, expected_count, expected_total):
    for rel, size in setup.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)
    count, total = pw.dir_stats(tmp_path)
    assert count == expected_count
    assert total == expected_total


# ---------------------------------------------------------------------------
# prune_unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "initial_files,changed,expect_present,expect_absent",
    [
        # keep.txt and descriptor.mod kept; prune.txt removed.
        (
            {"keep.txt", "prune.txt", "descriptor.mod"},
            {"keep.txt"},
            {"keep.txt", "descriptor.mod"},
            {"prune.txt"},
        ),
        # ALWAYS_KEEP files survive even when changed set is empty.
        (
            {"descriptor.mod", "thumbnail.png", "delete_me.txt"},
            set(),
            {"descriptor.mod", "thumbnail.png"},
            {"delete_me.txt"},
        ),
    ],
    ids=["removes_untracked", "keeps_always_keep"],
)
def test_prune_unchanged(
    tmp_path, initial_files, changed, expect_present, expect_absent
):
    mod_dir = tmp_path / "mod"
    mod_dir.mkdir()
    for rel in initial_files:
        p = mod_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".png"):
            p.write_bytes(b"\x89PNG")
        else:
            write_text(p, "content")
    pw.prune_unchanged(mod_dir, changed)
    for rel in expect_present:
        assert (mod_dir / rel).exists(), f"{rel} should exist"
    for rel in expect_absent:
        assert not (mod_dir / rel).exists(), f"{rel} should not exist"


# ---------------------------------------------------------------------------
# steamcmd discovery
# ---------------------------------------------------------------------------


def test_find_steamcmd_prefers_the_one_on_path(monkeypatch):
    monkeypatch.setattr(pw.shutil, "which", lambda _name: "/opt/bin/steamcmd")
    assert pw.find_steamcmd() == Path("/opt/bin/steamcmd")


def test_find_steamcmd_falls_back_to_the_home_install(monkeypatch, tmp_path):
    monkeypatch.setattr(pw.shutil, "which", lambda _name: None)
    fallback = tmp_path / "steamcmd" / "steamcmd.sh"
    fallback.parent.mkdir()
    write_text(fallback, "#!/bin/sh\n")
    monkeypatch.setattr(pw.Path, "home", classmethod(lambda _cls: tmp_path))

    assert pw.find_steamcmd() == fallback


def test_find_steamcmd_exits_when_nothing_is_installed(monkeypatch):
    monkeypatch.setattr(pw.shutil, "which", lambda _name: None)
    monkeypatch.setattr(pw.Path, "exists", lambda _self: False)

    with pytest.raises(SystemExit, match="steamcmd not found"):
        pw.find_steamcmd()


# ---------------------------------------------------------------------------
# git diff plumbing
# ---------------------------------------------------------------------------


class _Completed:
    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr


def _record_git(monkeypatch, result):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    return calls


def test_changed_files_ask_git_for_renames(monkeypatch):
    calls = _record_git(monkeypatch, _Completed("events/a.txt\n\nevents/b.txt\n"))

    assert pw.get_changed_files("v1.12.3") == {"events/a.txt", "events/b.txt"}
    cmd, kwargs = calls[0]
    assert "--find-renames" in cmd
    assert "--diff-filter=ACMR" in cmd
    assert cmd[-1] == "v1.12.3...HEAD"
    assert kwargs["cwd"] == pw.REPO_ROOT
    assert kwargs["check"] is True


def test_deleted_files_disable_rename_detection(monkeypatch):
    calls = _record_git(monkeypatch, _Completed("events/gone.txt\n"))

    assert pw.get_deleted_files("v1.12.3") == {"events/gone.txt"}
    cmd = calls[0][0]
    assert "--no-renames" in cmd
    assert "--diff-filter=D" in cmd


def test_changed_files_exit_when_the_range_is_empty(monkeypatch):
    _record_git(monkeypatch, _Completed("\n"))

    with pytest.raises(SystemExit, match="Nothing to publish"):
        pw.get_changed_files("v1.12.3")


@pytest.mark.parametrize(
    "stdout,stderr,expected",
    [
        ("", "fatal: bad revision\n", "fatal: bad revision"),
        ("some stdout\n", "", "some stdout"),
        ("", "", "Command 'git diff' returned non-zero exit status 128."),
    ],
    ids=["stderr", "stdout_fallback", "exception_fallback"],
)
def test_diff_failure_reports_the_git_detail(monkeypatch, stdout, stderr, expected):
    failure = subprocess.CalledProcessError(128, "git diff", stdout, stderr)
    _record_git(monkeypatch, failure)

    with pytest.raises(
        SystemExit, match="Failed to diff against 'v1.12.3'"
    ) as exit_info:
        pw.git_diff_name_only("v1.12.3", "ACMR")

    assert expected in str(exit_info.value)


# ---------------------------------------------------------------------------
# copy_repo — driven by a synthetic `git archive` stream
# ---------------------------------------------------------------------------


class _FakeArchiveProc:
    def __init__(self, payload, stderr=b"", returncode=0):
        self.stdout = io.BytesIO(payload)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.terminated = False

    def terminate(self):
        self.terminated = True

    def wait(self):
        return self.returncode


def _tar_bytes(members):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for info, payload in members:
            archive.addfile(info, io.BytesIO(payload) if payload is not None else None)
    return buffer.getvalue()


def _file_member(name, payload):
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mode = 0o644
    return info, payload


def _dir_member(name):
    info = tarfile.TarInfo(name)
    info.type = tarfile.DIRTYPE
    info.mode = 0o755
    return info, None


def _fifo_member(name):
    info = tarfile.TarInfo(name)
    info.type = tarfile.FIFOTYPE
    return info, None


def _symlink_member(name, target):
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    return info, None


def _archive_proc(monkeypatch, proc):
    monkeypatch.setattr(pw.subprocess, "Popen", lambda *_args, **_kwargs: proc)
    return proc


def test_copy_repo_extracts_dirs_and_skips_excluded_and_special_members(
    tmp_path, monkeypatch
):
    payload = _tar_bytes(
        [
            _dir_member("events/"),
            _file_member("events/a.txt", b"content\n"),
            _file_member("tools/secret.py", b"dev only\n"),
            _fifo_member("weird.pipe"),
        ]
    )
    _archive_proc(monkeypatch, _FakeArchiveProc(payload))

    dest = pw.copy_repo(tmp_path / "publish", {"tools"})

    assert (dest / "events").is_dir()
    assert (dest / "events" / "a.txt").read_text(encoding="utf-8") == "content\n"
    assert not (dest / "tools").exists()
    assert not (dest / "weird.pipe").exists()


def test_copy_repo_rejects_a_path_escaping_the_tree(tmp_path, monkeypatch):
    proc = _archive_proc(
        monkeypatch,
        _FakeArchiveProc(_tar_bytes([_file_member("../escape.txt", b"nope\n")])),
    )

    with pytest.raises(RuntimeError, match="Unsafe path in tracked HEAD"):
        pw.copy_repo(tmp_path / "publish", set())

    assert proc.terminated, "the git archive child must be torn down on failure"


def test_copy_repo_reports_a_failed_git_archive(tmp_path, monkeypatch):
    _archive_proc(
        monkeypatch,
        _FakeArchiveProc(
            _tar_bytes([]), stderr=b"fatal: not a repository\n", returncode=128
        ),
    )

    with pytest.raises(RuntimeError, match="fatal: not a repository"):
        pw.copy_repo(tmp_path / "publish", set())


def test_format_size_reaches_terabytes():
    assert pw.format_size(2 * 1024**4) == "2.0 TB"


# ---------------------------------------------------------------------------
# prune_unchanged — directories, verbose listing, unlink failures
# ---------------------------------------------------------------------------


def test_prune_removes_emptied_directories_and_lists_kept_files(tmp_path, capsys):
    mod_dir = tmp_path / "mod"
    (mod_dir / "keep").mkdir(parents=True)
    (mod_dir / "drop").mkdir()
    write_text(mod_dir / "keep" / "a.txt", "kept")
    write_text(mod_dir / "drop" / "b.txt", "dropped")

    pw.prune_unchanged(mod_dir, {"keep/a.txt"}, verbose=True)

    assert (mod_dir / "keep" / "a.txt").exists()
    assert not (mod_dir / "drop").exists()
    out = capsys.readouterr().out
    assert "keep/a.txt" in out
    assert "TOTAL" in out
    assert "Removed 1, kept 1 files." in out


def test_prune_warns_when_a_file_cannot_be_removed(tmp_path, monkeypatch, capsys):
    mod_dir = tmp_path / "mod"
    mod_dir.mkdir()
    write_text(mod_dir / "locked.txt", "stuck")
    real_unlink = pw.Path.unlink

    def flaky_unlink(self, *args, **kwargs):
        if self.name == "locked.txt":
            raise PermissionError("file in use")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(pw.Path, "unlink", flaky_unlink)

    pw.prune_unchanged(mod_dir, set())

    assert (mod_dir / "locked.txt").exists()
    out = capsys.readouterr().out
    assert "WARNING: Failed to remove locked.txt: file in use" in out
    assert "Removed 0, kept 0 files" in out


class _SteamProc:
    def __init__(self, lines, returncode=0):
        self.stdout = io.StringIO("".join(line + "\n" for line in lines))
        self.returncode = returncode

    def wait(self):
        return self.returncode


def _publish_mod(tmp_path):
    mod_dir = tmp_path / "mod"
    mod_dir.mkdir()
    write_text(mod_dir / "descriptor.mod", 'name="Old"\nversion="0.1"\n')
    (mod_dir / "thumbnail.png").write_bytes(b"\x89PNG")
    return mod_dir


def _stub_publish_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(pw, "find_steamcmd", lambda: Path("/bin/steamcmd"))
    monkeypatch.setattr(pw, "steam_login", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pw.tempfile, "gettempdir", lambda: str(tmp_path))


def _prepare_full_main(tmp_path, monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["publish_workshop.py", *args])
    monkeypatch.setattr(pw.tempfile, "mkdtemp", lambda prefix="": str(tmp_path / "pub"))
    (tmp_path / "pub").mkdir()


def test_copy_repo_refuses_a_tracked_symlink(tmp_path, monkeypatch):
    proc = _archive_proc(
        monkeypatch,
        _FakeArchiveProc(_tar_bytes([_symlink_member("gfx/icon.dds", "other.dds")])),
    )

    with pytest.raises(RuntimeError, match="Refusing to publish tracked symlink"):
        pw.copy_repo(tmp_path / "publish", set())

    assert proc.terminated


def test_steam_login_exits_when_steamcmd_fails(monkeypatch):
    monkeypatch.setattr(pw.subprocess, "call", lambda _cmd: 7)

    with pytest.raises(SystemExit, match=r"Steam login failed \(exit code 7\)"):
        pw.steam_login(Path("/bin/steamcmd"), "user")


def test_steam_login_invokes_steamcmd_login(monkeypatch):
    calls = []
    steamcmd = Path("/bin/steamcmd")
    monkeypatch.setattr(pw.subprocess, "call", lambda cmd: calls.append(cmd) or 0)

    pw.steam_login(steamcmd, "user")

    assert calls == [[str(steamcmd), "+login", "user", "+quit"]]


def test_publish_succeeds_and_retries_a_transient_failure(
    tmp_path, monkeypatch, capsys
):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(pw.time, "sleep", lambda _seconds: None)
    procs = iter(
        [
            _SteamProc(["Uploading content failed"], returncode=1),
            _SteamProc(
                [
                    "Logging in",
                    "Uploading content",
                    "Uploading preview",
                    "Committing update",
                ],
                returncode=0,
            ),
        ]
    )
    popen_cmds = []

    def fake_popen(cmd, **_kwargs):
        popen_cmds.append(cmd)
        return next(procs)

    monkeypatch.setattr(pw.subprocess, "Popen", fake_popen)

    pw.publish(_publish_mod(tmp_path), "user", "2777133449", "note")

    assert len(popen_cmds) == 2
    assert "+workshop_build_item" in popen_cmds[0]
    out = capsys.readouterr().out
    assert "Retrying" in out
    assert "Upload completed" in out
    assert list(tmp_path.glob("md_publish_*.log"))


def test_publish_does_not_overwrite_predictable_log_path(tmp_path, monkeypatch):
    _stub_publish_runtime(tmp_path, monkeypatch)
    predictable_log = tmp_path / "md_publish_1700000000.log"
    write_text(predictable_log, "attacker-owned\n")
    monkeypatch.setattr(pw.time, "time", lambda: 1_700_000_000)
    monkeypatch.setattr(
        pw.subprocess,
        "Popen",
        lambda *_args, **_kwargs: _SteamProc(["Uploading content"], returncode=0),
    )

    pw.publish(_publish_mod(tmp_path), "user", "2777133449", "note")

    assert predictable_log.read_text(encoding="utf-8") == "attacker-owned\n"
    logs = list(tmp_path.glob("md_publish_*.log"))
    assert len(logs) == 2
    assert any(path != predictable_log for path in logs)


def test_publish_does_not_retry_an_auth_failure(tmp_path, monkeypatch):
    _stub_publish_runtime(tmp_path, monkeypatch)
    slept = []
    monkeypatch.setattr(pw.time, "sleep", slept.append)
    monkeypatch.setattr(
        pw.subprocess,
        "Popen",
        lambda *_args, **_kwargs: _SteamProc(
            ["Failed login: invalid password"], returncode=1
        ),
    )

    with pytest.raises(SystemExit, match="auth failure"):
        pw.publish(_publish_mod(tmp_path), "user", "1", "note")

    assert slept == []


def test_publish_exits_after_exhausted_retries(tmp_path, monkeypatch):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(pw.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        pw.subprocess,
        "Popen",
        lambda *_args, **_kwargs: _SteamProc(["timeout talking to CM"], returncode=2),
    )

    with pytest.raises(SystemExit, match="after 3 attempts"):
        pw.publish(_publish_mod(tmp_path), "user", "1", "note")


def test_publish_verbose_echoes_the_vdf_and_steamcmd_stream(
    tmp_path, monkeypatch, capsys
):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(
        pw.subprocess,
        "Popen",
        lambda *_args, **_kwargs: _SteamProc(["Preparing workshop item"], returncode=0),
    )

    pw.publish(_publish_mod(tmp_path), "user", "1", "Line1\nLine2", verbose=True)

    out = capsys.readouterr().out
    assert "--- workshop_upload.vdf ---" in out
    assert "Preparing workshop item" in out
    vdf = (tmp_path / "workshop_upload.vdf").read_text(encoding="utf-8")
    assert r"Line1\nLine2" in vdf


def test_main_exits_without_a_username(monkeypatch):
    monkeypatch.delenv("STEAM_USERNAME", raising=False)
    monkeypatch.setattr(sys, "argv", ["publish_workshop.py", "test", "--full"])

    with pytest.raises(SystemExit, match="No username"):
        pw.main()


def test_main_refuses_a_diff_that_deletes_files(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["publish_workshop.py", "test", "--base-ref", "v1", "--username", "u"],
    )
    monkeypatch.setattr(pw, "get_deleted_files", lambda _ref: {"events/old.txt"})

    with pytest.raises(SystemExit, match="cannot safely express deleted files"):
        pw.main()


def test_main_refuses_a_diff_with_no_publishable_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["publish_workshop.py", "test", "--base-ref", "v1", "--username", "u"],
    )
    monkeypatch.setattr(pw, "get_deleted_files", lambda _ref: set())
    monkeypatch.setattr(pw, "get_changed_files", lambda _ref: {"tools/secret.py"})
    monkeypatch.setattr(pw.tempfile, "mkdtemp", lambda prefix="": str(tmp_path / "pub"))
    (tmp_path / "pub").mkdir()

    def fake_copy(dest_parent, _excludes):
        mod_dir = dest_parent / "mod"
        mod_dir.mkdir()
        write_text(mod_dir / "descriptor.mod", "name=x\n")
        (mod_dir / "thumbnail.png").write_bytes(b"\x89PNG")
        return mod_dir

    monkeypatch.setattr(pw, "copy_repo", fake_copy)

    with pytest.raises(SystemExit, match="No publishable mod files changed"):
        pw.main()


def test_main_full_publish_patches_the_descriptor_then_uploads(tmp_path, monkeypatch):
    _prepare_full_main(
        tmp_path,
        monkeypatch,
        "test",
        "--full",
        "--username",
        "uploader",
        "--version",
        "1.2.3",
        "--changenote",
        "notes",
        "--exclude",
        "scratch",
    )
    seen = {}

    def fake_copy(dest_parent, excludes):
        seen["excludes"] = set(excludes)
        mod_dir = dest_parent / "mod"
        mod_dir.mkdir()
        write_text(
            mod_dir / "descriptor.mod",
            'name="Old"\nversion="0.1"\nremote_file_id="0"\n',
        )
        (mod_dir / "thumbnail.png").write_bytes(b"\x89PNG")
        return mod_dir

    def fake_publish(mod_dir, username, mod_id, changenote, verbose=False):
        seen["descriptor"] = (mod_dir / "descriptor.mod").read_text(encoding="utf-8")
        seen["username"] = username
        seen["mod_id"] = mod_id
        seen["changenote"] = changenote
        seen["verbose"] = verbose

    monkeypatch.setattr(pw, "copy_repo", fake_copy)
    monkeypatch.setattr(pw, "publish", fake_publish)

    pw.main()

    assert "scratch" in seen["excludes"]
    assert "tools" in seen["excludes"]
    assert 'name="MD Test"' in seen["descriptor"]
    assert 'remote_file_id="2777133449"' in seen["descriptor"]
    assert 'version="1.2.3"' in seen["descriptor"]
    assert seen["username"] == "uploader"
    assert seen["mod_id"] == "2777133449"
    assert seen["changenote"] == "notes"
    assert seen["verbose"] is False


def test_main_no_default_excludes_is_honoured(tmp_path, monkeypatch):
    _prepare_full_main(
        tmp_path,
        monkeypatch,
        "beta",
        "--full",
        "--username",
        "u",
        "--no-default-excludes",
        "--verbose",
    )
    seen = {}

    def fake_copy(dest_parent, excludes):
        seen["excludes"] = set(excludes)
        mod_dir = dest_parent / "mod"
        mod_dir.mkdir()
        write_text(mod_dir / "descriptor.mod", "name=x\n")
        (mod_dir / "thumbnail.png").write_bytes(b"\x89PNG")
        return mod_dir

    def fake_publish(mod_dir, username, mod_id, changenote, verbose=False):
        seen["mod_id"] = mod_id
        seen["verbose"] = verbose

    monkeypatch.setattr(pw, "copy_repo", fake_copy)
    monkeypatch.setattr(pw, "publish", fake_publish)

    pw.main()

    assert seen["excludes"] == set()
    assert seen["mod_id"] == pw.MOD_IDS["beta"]
    assert seen["verbose"] is True
