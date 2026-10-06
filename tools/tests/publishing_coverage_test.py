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
import os
import signal
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath

import pytest
from shared.suite import write_text

from tools.publishing import publish_workshop as pw

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
# Frontend version banner patching
# ---------------------------------------------------------------------------


EXPECTED_FRONTEND_PATHS = {
    "localisation/braz_por/MD_frontend_l_braz_por.yml",
    "localisation/english/MD_frontend_l_english.yml",
    "localisation/french/MD_frontend_l_french.yml",
    "localisation/german/MD_frontend_l_german.yml",
    "localisation/japanese/MD_frontend_l_japanese.yml",
    "localisation/korean/MD_frontend_l_korean.yml",
    "localisation/polish/MD_frontend_l_polish.yml",
    "localisation/russian/MD_frontend_l_russian.yml",
    "localisation/simp_chinese/MD_frontend_l_simp_chinese.yml",
    "localisation/spanish/MD_frontend_l_spanish.yml",
}


EXPECTED_VERSION_LOC_KEYS = ("VERSION_MD_LOADING", "VERSION_MD")


def _frontend_loc(mod_dir, lang, body):
    path = mod_dir / "localisation" / lang / f"MD_frontend_l_{lang}.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
    return path


def test_frontend_loc_files_returns_the_fixed_locale_set(tmp_path):
    assert {
        path.relative_to(tmp_path).as_posix()
        for path in pw.frontend_loc_files(tmp_path)
    } == EXPECTED_FRONTEND_PATHS


def _frontend_body(lang, version="2.0.0"):
    loading = "Version: v{version} DEV"
    main = "Millennium Dawn: A Modern Day v{version} DEV"
    if lang == "korean":
        loading = "버전: v{version} DEV"
    elif lang == "simp_chinese":
        loading = "版本：v{version} 开发版"
        main = "千禧黎明：现代之日 v{version} 开发版"
    return (
        f"l_{lang}:\n"
        f' VERSION_MD_LOADING: "{loading.format(version=version)}"\n'
        f' VERSION_MD: "{main.format(version=version)}"\n'
        ' VERSION_MD_DATE: "Release Date: 11th September 2026"\n'
    )


def _write_frontend_tree(mod_dir, version="2.0.0", bodies=None):
    bodies = bodies or {}
    paths = []
    for rel in sorted(EXPECTED_FRONTEND_PATHS):
        path = mod_dir / rel
        lang = path.parent.name
        paths.append(
            _frontend_loc(
                mod_dir, lang, bodies.get(lang, _frontend_body(lang, version))
            )
        )
    return paths


def test_patch_frontend_version_rewrites_every_locale(tmp_path, capsys):
    paths = _write_frontend_tree(tmp_path)

    pw.patch_frontend_version(tmp_path, "1.2.3")

    for path in paths:
        raw = path.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf"), "BOM must survive"
        text = raw.decode("utf-8")
        for key in EXPECTED_VERSION_LOC_KEYS:
            matches = [
                line
                for line in text.splitlines()
                if line.split(":", 1)[0].strip() == key
            ]
            assert len(matches) == 1
            assert matches[0].count("v1.2.3") == 1
            assert "v2.0.0" not in matches[0]
        assert 'VERSION_MD_DATE: "Release Date: 11th September 2026"' in text
    assert "10/10 frontend files rewritten" in capsys.readouterr().out


def test_patch_frontend_version_keeps_translated_text(tmp_path):
    _write_frontend_tree(tmp_path)

    pw.patch_frontend_version(tmp_path, "2.1.0")

    korean = (tmp_path / "localisation/korean/MD_frontend_l_korean.yml").read_text(
        encoding="utf-8"
    )
    chinese = (
        tmp_path / "localisation/simp_chinese/MD_frontend_l_simp_chinese.yml"
    ).read_text(encoding="utf-8")
    assert 'VERSION_MD_LOADING: "버전: v2.1.0 DEV"' in korean
    assert 'VERSION_MD: "Millennium Dawn: A Modern Day v2.1.0 DEV"' in korean
    assert 'VERSION_MD_LOADING: "版本：v2.1.0 开发版"' in chinese
    assert 'VERSION_MD: "千禧黎明：现代之日 v2.1.0 开发版"' in chinese


def test_patch_frontend_version_replaces_a_complete_prerelease_token(tmp_path):
    _write_frontend_tree(tmp_path, version="2.0.0-beta.1")

    pw.patch_frontend_version(tmp_path, "2.0.0-beta.5")

    for rel in EXPECTED_FRONTEND_PATHS:
        text = (tmp_path / rel).read_text(encoding="utf-8")
        assert text.count("v2.0.0-beta.5") == 2
        assert "v2.0.0-beta.1" not in text


@pytest.mark.parametrize(
    "marker", [" BETA", " TEST", ""], ids=["beta", "test", "release"]
)
def test_patch_frontend_version_replaces_the_dev_marker_in_every_locale(
    tmp_path, marker
):
    paths = _write_frontend_tree(tmp_path)

    pw.patch_frontend_version(tmp_path, "2.1.0", marker)

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.count(f'v2.1.0{marker}"') == 2
        assert "DEV" not in text
        assert "开发版" not in text


def test_patch_frontend_version_relabels_without_a_version(tmp_path, capsys):
    paths = _write_frontend_tree(tmp_path)

    pw.patch_frontend_version(tmp_path, None, " BETA")

    for path in paths:
        assert path.read_text(encoding="utf-8").count('v2.0.0 BETA"') == 2
    assert "repo version BETA (10/10 frontend files rewritten)" in (
        capsys.readouterr().out
    )


@pytest.mark.parametrize(
    "source,expected",
    [
        ("v2.0.1 DEV", ["v2.0.1"]),
        ("v1.12.3b", ["v1.12.3b"]),
        ("v2.0.1-beta.1", ["v2.0.1-beta.1"]),
    ],
)
def test_version_token_matches_complete_supported_formats(source, expected):
    assert pw.VERSION_TOKEN.findall(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "xv2.0.1 DEV",
        "_v2.0.1 DEV",
        "v2.0.1+build.1",
        "v2.0.1_beta",
    ],
)
def test_version_token_rejects_partial_matches(source):
    assert pw.VERSION_TOKEN.findall(source) == []


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("0.0.0", "0.0.0"),
        ("1.2.3", "1.2.3"),
        ("1.2.3rc1", "1.2.3rc1"),
        (
            "123456789012345678901234567890.987654321098765432109876543210.111111111111111111111111111111",
            "123456789012345678901234567890.987654321098765432109876543210.111111111111111111111111111111",
        ),
        ("v1.12.3b", "1.12.3b"),
        ("v2.0.1-beta.5", "2.0.1-beta.5"),
    ],
)
def test_normalize_version_accepts_supported_formats(value, expected):
    assert pw.normalize_version(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "v",
        " 1.2.3",
        "1.2.3 ",
        '"1.2.3"',
        "1.2.3\\1",
        "1.2",
        "1.2.3-",
        "1.2.3-beta..1",
        "-1.2.3",
        "01.2.3",
        "1.2.3\n",
        "1.2.3\x00",
    ],
)
def test_normalize_version_rejects_malformed_values(value):
    with pytest.raises(SystemExit, match=r"^ERROR: Invalid version") as exc_info:
        pw.normalize_version(value)
    assert "One optional leading v or V is accepted" in str(exc_info.value)


def test_patch_frontend_version_rejects_a_missing_file_without_partial_writes(tmp_path):
    paths = _write_frontend_tree(tmp_path)
    before = {path: path.read_bytes() for path in paths}
    missing = tmp_path / "localisation/english/MD_frontend_l_english.yml"
    missing.unlink()

    with pytest.raises(SystemExit, match="Missing expected frontend localisation file"):
        pw.patch_frontend_version(tmp_path, "1.2.3")

    assert all(
        path.read_bytes() == data for path, data in before.items() if path != missing
    )


@pytest.mark.parametrize(
    "malformation, expected_error",
    [
        (
            (b" VERSION_MD: ", b" VERSION_REMOVED: "),
            "VERSION_MD must appear exactly once",
        ),
        (
            (
                b' VERSION_MD: "Millennium Dawn: A Modern Day v2.0.0 DEV"\n',
                b' VERSION_MD: "Millennium Dawn: A Modern Day v2.0.0 DEV"\n'
                b' VERSION_MD: "Duplicate v2.0.0 DEV"\n',
            ),
            "VERSION_MD must appear exactly once",
        ),
        (
            (
                b' VERSION_MD_LOADING: "Version: v2.0.0 DEV"',
                b' VERSION_MD_LOADING: "Version: missing DEV"',
            ),
            "VERSION_MD_LOADING must contain exactly one",
        ),
        (
            (
                b' VERSION_MD_LOADING: "Version: v2.0.0 DEV"',
                b' VERSION_MD_LOADING: "Version: v2.0.0 and v2.0.0 DEV"',
            ),
            "VERSION_MD_LOADING must contain exactly one",
        ),
    ],
    ids=[
        "missing_key",
        "duplicate_key",
        "zero_replaceable_tokens",
        "multiple_replaceable_tokens",
    ],
)
def test_patch_frontend_version_rejects_malformed_frontend_banners(
    tmp_path, malformation, expected_error
):
    paths = _write_frontend_tree(tmp_path)
    english = tmp_path / "localisation/english/MD_frontend_l_english.yml"
    old, new = malformation
    assert old in english.read_bytes()
    english.write_bytes(english.read_bytes().replace(old, new))
    before = {path: path.read_bytes() for path in paths}

    with pytest.raises(SystemExit, match=expected_error):
        pw.patch_frontend_version(tmp_path, "1.2.3")

    assert all(path.read_bytes() == data for path, data in before.items())


def test_patch_frontend_version_is_a_byte_for_byte_noop_for_same_version(tmp_path):
    paths = _write_frontend_tree(tmp_path, version="1.2.3")
    before = {path: path.read_bytes() for path in paths}

    pw.patch_frontend_version(tmp_path, "1.2.3")

    assert all(path.read_bytes() == data for path, data in before.items())


def test_real_frontend_files_match_the_fixed_production_locale_contract():
    localisation = pw.REPO_ROOT / "localisation"
    actual = {
        path.relative_to(pw.REPO_ROOT).as_posix()
        for path in localisation.glob("*/MD_frontend_l_*.yml")
    }
    assert actual == EXPECTED_FRONTEND_PATHS
    assert tuple(pw.VERSION_LOC_KEYS) == EXPECTED_VERSION_LOC_KEYS

    for rel in sorted(EXPECTED_FRONTEND_PATHS):
        path = pw.REPO_ROOT / rel
        lines = path.read_text(encoding="utf-8").splitlines()
        for key in EXPECTED_VERSION_LOC_KEYS:
            matches = [line for line in lines if line.split(":", 1)[0].strip() == key]
            assert len(matches) == 1, f"{rel}: expected exactly one {key}"
            assert (
                len(pw.VERSION_TOKEN.findall(matches[0])) == 1
            ), f"{rel}: {key} must have exactly one complete version token"
            banner = pw.BANNER_VERSION.search(matches[0])
            assert (
                banner and banner["marker"]
            ), f"{rel}: {key} must follow its version with a dev marker"


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
        # A directory, traversal, or a non-canonical spelling is never a match.
        (
            {"events/existing.txt", "descriptor.mod"},
            {"events", "../outside.txt", "events/../descriptor.mod", ""},
            set(),
        ),
    ],
    ids=["changed_tracked", "changed_not_on_disk", "changed_unsafe"],
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


def test_get_publishable_changed_files_rejects_paths_outside_staging(tmp_path):
    mod_dir = tmp_path / "mod"
    mod_dir.mkdir()
    outside = tmp_path / "outside.txt"
    write_text(outside, "secret")

    changed = {"../outside.txt", str(outside), outside.as_posix()}

    assert pw.get_publishable_changed_files(mod_dir, changed) == set()


def test_get_publishable_changed_files_rejects_symlinks(tmp_path):
    mod_dir = tmp_path / "mod"
    (mod_dir / "events").mkdir(parents=True)
    write_text(mod_dir / "events" / "real.txt", "content")
    outside = tmp_path / "outside"
    outside.mkdir()
    write_text(outside / "secret.txt", "secret")
    try:
        os.symlink(mod_dir / "events" / "real.txt", mod_dir / "events" / "link.txt")
        os.symlink(outside, mod_dir / "escape", target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")

    changed = {"events/real.txt", "events/link.txt", "escape/secret.txt"}

    assert pw.get_publishable_changed_files(mod_dir, changed) == {"events/real.txt"}


def test_get_publishable_changed_files_does_not_scan_the_tree(tmp_path, monkeypatch):
    mod_dir = tmp_path / "mod"
    (mod_dir / "events").mkdir(parents=True)
    write_text(mod_dir / "events" / "a.txt", "content")
    write_text(mod_dir / "events" / "unchanged.txt", "content")

    with monkeypatch.context() as scoped:
        for name in ("scandir", "listdir", "walk"):
            scoped.setattr(
                os, name, lambda *_a, **_k: pytest.fail("staged tree was scanned")
            )
        result = pw.get_publishable_changed_files(mod_dir, {"events/a.txt"})

    assert result == {"events/a.txt"}


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
        self.exited = False

    def poll(self):
        return self.returncode if self.exited else None

    def terminate(self):
        self.terminated = True
        self.exited = True

    def wait(self, timeout=None):
        self.exited = True
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


def test_copy_repo_reports_an_unreadable_tracked_file(tmp_path, monkeypatch):
    class _UnreadableMember:
        name = "events/a.txt"

        def issym(self):
            return False

        def islnk(self):
            return False

        def isdir(self):
            return False

        def isfile(self):
            return True

    class _UnreadableArchive:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def __iter__(self):
            return iter([_UnreadableMember()])

        def extractfile(self, _member):
            return None

    proc = _FakeArchiveProc(_tar_bytes([]))
    _archive_proc(monkeypatch, proc)
    monkeypatch.setattr(
        pw.tarfile, "open", lambda *args, **kwargs: _UnreadableArchive()
    )

    with pytest.raises(RuntimeError, match="Could not read tracked file"):
        pw.copy_repo(tmp_path / "publish", set())

    assert proc.terminated, "the git archive child must be torn down on failure"


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
        self.stderr = None
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
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
    # Scripted children have no real process group to signal.
    monkeypatch.setattr(pw, "OWN_GROUP", False)


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
    monkeypatch.setattr(
        sys, "argv", ["publish_workshop.py", "test", "--full", "--version", "1.2.3"]
    )

    with pytest.raises(SystemExit, match="No username"):
        pw.main()


def test_main_refuses_a_diff_that_deletes_files(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_workshop.py",
            "test",
            "--base-ref",
            "v1",
            "--username",
            "u",
            "--version",
            "1.2.3",
        ],
    )
    monkeypatch.setattr(pw, "get_deleted_files", lambda _ref: {"events/old.txt"})

    with pytest.raises(SystemExit, match="cannot safely express deleted files"):
        pw.main()


def test_main_refuses_a_diff_with_no_publishable_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_workshop.py",
            "test",
            "--base-ref",
            "v1",
            "--username",
            "u",
            "--version",
            "1.2.3",
        ],
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
        _write_frontend_tree(mod_dir)
        (mod_dir / "thumbnail.png").write_bytes(b"\x89PNG")
        return mod_dir

    def fake_publish(
        mod_dir, username, mod_id, changenote, verbose=False, description=None
    ):
        seen["descriptor"] = (mod_dir / "descriptor.mod").read_text(encoding="utf-8")
        seen["frontend_paths"] = {
            path.relative_to(mod_dir).as_posix()
            for path in mod_dir.glob("localisation/*/MD_frontend_l_*.yml")
        }
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
    assert seen["frontend_paths"] == EXPECTED_FRONTEND_PATHS
    assert seen["username"] == "uploader"
    assert seen["mod_id"] == "2777133449"
    assert seen["changenote"] == "notes"
    assert seen["verbose"] is False


def _staged_mod(dest_parent, description_body):
    mod_dir = dest_parent / "mod"
    mod_dir.mkdir()
    _write_frontend_tree(mod_dir)
    if description_body is not None:
        _write_description(mod_dir, description_body)
    write_text(mod_dir / "descriptor.mod", 'name="Old"\nversion="0.1"\n')
    (mod_dir / "thumbnail.png").write_bytes(b"\x89PNG")
    return mod_dir


def _main_staged(tmp_path, monkeypatch, *args, description_body=None):
    _prepare_full_main(tmp_path, monkeypatch, *args)
    seen = {}

    def fake_copy(dest_parent, excludes):
        mod_dir = _staged_mod(dest_parent, description_body)
        if "english" in excludes:
            (mod_dir / "localisation/english/MD_frontend_l_english.yml").unlink()
        return mod_dir

    def fake_publish(mod_dir, *_args, **_kwargs):
        seen["description"] = _kwargs.get("description")
        seen["description_file"] = (
            mod_dir / "descriptions/descriptions_EN.txt"
        ).exists()
        seen["frontend"] = (
            mod_dir / "localisation" / "english" / "MD_frontend_l_english.yml"
        ).read_text(encoding="utf-8")
        seen["frontend_paths"] = {
            path.relative_to(mod_dir).as_posix()
            for path in mod_dir.glob("localisation/*/MD_frontend_l_*.yml")
        }
        seen["frontends"] = {
            rel: (mod_dir / rel).read_text(encoding="utf-8")
            for rel in EXPECTED_FRONTEND_PATHS
        }
        seen["descriptor"] = (mod_dir / "descriptor.mod").read_text(encoding="utf-8")

    monkeypatch.setattr(pw, "copy_repo", fake_copy)
    monkeypatch.setattr(pw, "publish", fake_publish)
    pw.main()
    return seen


def _main_diff_staged(tmp_path, monkeypatch, changed, *args, description_body=None):
    monkeypatch.setattr(sys, "argv", ["publish_workshop.py", *args])
    monkeypatch.setattr(pw, "get_deleted_files", lambda _ref: set())
    monkeypatch.setattr(pw, "get_changed_files", lambda _ref: set(changed))
    monkeypatch.setattr(pw.tempfile, "mkdtemp", lambda prefix="": str(tmp_path / "pub"))
    (tmp_path / "pub").mkdir()
    seen = {}

    def fake_copy(dest_parent, _excludes):
        mod_dir = _staged_mod(dest_parent, description_body)
        (mod_dir / "events").mkdir()
        write_text(mod_dir / "events" / "foo.txt", "changed\n")
        return mod_dir

    def fake_publish(mod_dir, *_args, **_kwargs):
        seen["description"] = _kwargs.get("description")
        seen["description_file"] = (
            mod_dir / "descriptions/descriptions_EN.txt"
        ).exists()
        loc = mod_dir / "localisation" / "english" / "MD_frontend_l_english.yml"
        seen["banner"] = loc.read_text(encoding="utf-8") if loc.exists() else ""
        seen["frontend_paths"] = {
            path.relative_to(mod_dir).as_posix()
            for path in mod_dir.glob("localisation/*/MD_frontend_l_*.yml")
        }
        seen["kept_event"] = (mod_dir / "events" / "foo.txt").exists()

    monkeypatch.setattr(pw, "copy_repo", fake_copy)
    monkeypatch.setattr(pw, "publish", fake_publish)
    pw.main()
    return seen


def test_main_patches_the_version_banner_when_version_given(tmp_path, monkeypatch):
    staged = _main_staged(
        tmp_path,
        monkeypatch,
        "test",
        "--full",
        "--username",
        "u",
        "--version",
        "1.2.3",
    )

    assert 'VERSION_MD_LOADING: "Version: v1.2.3 TEST"' in staged["frontend"]
    assert staged["frontend_paths"] == EXPECTED_FRONTEND_PATHS


@pytest.mark.parametrize("target", ["release", "beta", "test"])
@pytest.mark.parametrize("mode", [(), ("--full",), ("--base-ref", "v1")])
def test_main_requires_version_before_staging(monkeypatch, capsys, target, mode):
    monkeypatch.setattr(
        sys, "argv", ["publish_workshop.py", target, *mode, "--username", "u"]
    )
    monkeypatch.setattr(
        pw.tempfile, "mkdtemp", lambda **_kwargs: pytest.fail("staging started")
    )
    with pytest.raises(SystemExit) as exc:
        pw.main()
    assert exc.value.code == 2
    assert "--version" in capsys.readouterr().err


def test_main_defaults_to_full_upload(tmp_path, monkeypatch):
    monkeypatch.setattr(
        pw, "get_deleted_files", lambda *_args: pytest.fail("diff called")
    )
    staged = _main_staged(
        tmp_path, monkeypatch, "release", "--username", "u", "--version", "1.2.3"
    )
    assert 'version="1.2.3"' in staged["descriptor"]
    assert 'VERSION_MD_LOADING: "Version: v1.2.3"' in staged["frontend"]
    assert staged["frontend_paths"] == EXPECTED_FRONTEND_PATHS


@pytest.mark.parametrize(
    "target,args,expected",
    [
        ("beta", ("--version", "2.0.0"), "Version: v2.0.0 BETA"),
        ("beta", ("--version", "1.2.3"), "Version: v1.2.3 BETA"),
        ("release", ("--version", "2.0.0"), "Version: v2.0.0"),
        ("release", ("--version", "1.2.3"), "Version: v1.2.3"),
    ],
)
def test_main_labels_the_version_banner_for_the_target(
    tmp_path, monkeypatch, target, args, expected
):
    staged = _main_staged(
        tmp_path, monkeypatch, target, "--full", "--username", "u", *args
    )

    assert f'VERSION_MD_LOADING: "{expected}"\n' in staged["frontend"]
    assert staged["frontend_paths"] == EXPECTED_FRONTEND_PATHS


@pytest.mark.parametrize(
    "target,marker", [("release", ""), ("beta", " BETA"), ("test", " TEST")]
)
@pytest.mark.parametrize(
    "supplied,normalized",
    [("v1.2.3", "1.2.3"), ("V2.0.1-beta.5", "2.0.1-beta.5"), ("v1.12.3b", "1.12.3b")],
)
def test_main_normalizes_descriptor_and_all_banners(
    tmp_path, monkeypatch, target, marker, supplied, normalized
):
    staged = _main_staged(
        tmp_path, monkeypatch, target, "--username", "u", "--version", supplied
    )
    assert f'version="{normalized}"' in staged["descriptor"]
    assert f'name="{pw.MOD_NAMES[target]}"' in staged["descriptor"]
    assert f'remote_file_id="{pw.MOD_IDS[target]}"' in staged["descriptor"]
    assert set(staged["frontends"]) == EXPECTED_FRONTEND_PATHS
    for body in staged["frontends"].values():
        assert body.count(f'v{normalized}{marker}"') == 2


def test_main_version_validation_happens_before_copy(tmp_path, monkeypatch):
    _prepare_full_main(
        tmp_path,
        monkeypatch,
        "test",
        "--full",
        "--username",
        "u",
        "--version",
        r"1.2.3\\1",
    )
    monkeypatch.setattr(pw, "copy_repo", lambda *_args: pytest.fail("copy_repo called"))

    with pytest.raises(SystemExit, match=r"^ERROR: Invalid version"):
        pw.main()


def test_main_excludes_a_required_locale_instead_of_uploading_a_mismatch(
    tmp_path, monkeypatch
):
    with pytest.raises(SystemExit, match="Missing expected frontend localisation file"):
        _main_staged(
            tmp_path,
            monkeypatch,
            "test",
            "--full",
            "--username",
            "u",
            "--version",
            "1.2.3",
            "--exclude",
            "english",
        )


def test_main_diff_publish_with_version_ships_the_patched_banner(
    tmp_path, monkeypatch, capsys
):
    staged = _main_diff_staged(
        tmp_path,
        monkeypatch,
        {"events/foo.txt"},
        "beta",
        "--base-ref",
        "v1",
        "--username",
        "u",
        "--version",
        "1.2.3",
    )

    assert 'VERSION_MD_LOADING: "Version: v1.2.3 BETA"' in staged["banner"]
    assert staged["frontend_paths"] == EXPECTED_FRONTEND_PATHS
    assert staged["kept_event"] is True
    assert "10/10 frontend files rewritten" in capsys.readouterr().out


def test_main_beta_diff_publish_ships_the_relabeled_banner(tmp_path, monkeypatch):
    staged = _main_diff_staged(
        tmp_path,
        monkeypatch,
        {"events/foo.txt"},
        "beta",
        "--base-ref",
        "v1",
        "--username",
        "u",
        "--version",
        "2.0.0",
    )

    assert 'VERSION_MD_LOADING: "Version: v2.0.0 BETA"' in staged["banner"]
    assert staged["frontend_paths"] == EXPECTED_FRONTEND_PATHS
    assert staged["kept_event"] is True


def test_main_test_diff_publish_ships_the_test_banner(tmp_path, monkeypatch):
    staged = _main_diff_staged(
        tmp_path,
        monkeypatch,
        {"events/foo.txt"},
        "test",
        "--base-ref",
        "v1",
        "--username",
        "u",
        "--version",
        "2.0.0",
    )

    assert 'VERSION_MD_LOADING: "Version: v2.0.0 TEST"' in staged["banner"]
    assert staged["frontend_paths"] == EXPECTED_FRONTEND_PATHS
    assert staged["kept_event"] is True


def test_main_diff_publish_with_version_still_refuses_an_empty_diff(
    tmp_path, monkeypatch
):
    with pytest.raises(SystemExit, match="No publishable mod files changed"):
        _main_diff_staged(
            tmp_path,
            monkeypatch,
            {"tools/secret.py"},
            "beta",
            "--base-ref",
            "v1",
            "--username",
            "u",
            "--version",
            "1.2.3",
        )


def test_main_no_default_excludes_is_honoured(tmp_path, monkeypatch):
    _prepare_full_main(
        tmp_path,
        monkeypatch,
        "beta",
        "--full",
        "--username",
        "u",
        "--version",
        "1.2.3",
        "--no-default-excludes",
        "--verbose",
    )
    seen = {}

    def fake_copy(dest_parent, excludes):
        seen["excludes"] = set(excludes)
        mod_dir = dest_parent / "mod"
        mod_dir.mkdir()
        _write_frontend_tree(mod_dir)
        write_text(mod_dir / "descriptor.mod", "name=x\n")
        (mod_dir / "thumbnail.png").write_bytes(b"\x89PNG")
        return mod_dir

    def fake_publish(
        mod_dir, username, mod_id, changenote, verbose=False, description=None
    ):
        seen["mod_id"] = mod_id
        seen["verbose"] = verbose

    monkeypatch.setattr(pw, "copy_repo", fake_copy)
    monkeypatch.setattr(pw, "publish", fake_publish)

    pw.main()

    assert seen["excludes"] == set()
    assert seen["mod_id"] == pw.MOD_IDS["beta"]
    assert seen["verbose"] is True


@pytest.mark.parametrize("source_marker", [" DEV", " BETA", " TEST", " 开发版", ""])
@pytest.mark.parametrize("target_marker", [" BETA", " TEST", ""])
def test_banner_target_rewrite_is_repeatable(tmp_path, source_marker, target_marker):
    bodies = {
        lang: _frontend_body(lang)
        .replace(" DEV", source_marker)
        .replace(" 开发版", source_marker)
        for lang in pw.FRONTEND_LOCALES
    }
    paths = _write_frontend_tree(tmp_path, bodies=bodies)
    pw.patch_frontend_version(tmp_path, "3.4.5-beta.2", target_marker)
    first = {path: path.read_bytes() for path in paths}
    pw.patch_frontend_version(tmp_path, "3.4.5-beta.2", target_marker)
    for path in paths:
        assert path.read_bytes() == first[path]
        assert (
            path.read_text(encoding="utf-8").count(f'v3.4.5-beta.2{target_marker}"')
            == 2
        )
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize("verbose", [False, True])
def test_publish_keeps_diagnostics_in_log_and_quiets_default_output(
    tmp_path, monkeypatch, capsys, verbose
):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(
        pw.subprocess,
        "Popen",
        lambda *_args, **_kwargs: _SteamProc(
            ["Preparing workshop item", "Warning: example diagnostic"]
        ),
    )
    pw.publish(_publish_mod(tmp_path), "user", "1", "note", verbose=verbose)
    out = capsys.readouterr().out
    assert "Warning: example diagnostic" in out
    assert "Upload completed" in out
    assert ("Phase timings" in out) is verbose
    assert ("Preparing workshop item" in out) is verbose
    log = next(tmp_path.glob("md_publish_*.log")).read_text(encoding="utf-8")
    assert "Preparing workshop item" in log
    assert "Warning: example diagnostic" in log
    assert "Phase timings" in log
    assert "--- workshop_upload.vdf ---" in log


def test_publish_ignores_blank_steamcmd_lines(tmp_path, monkeypatch, capsys):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(
        pw.subprocess,
        "Popen",
        lambda *_args, **_kwargs: _SteamProc(
            ["", "Uploading content", "", "Committing update", ""],
            returncode=0,
        ),
    )

    pw.publish(_publish_mod(tmp_path), "user", "1", "note")

    assert "Upload completed" in capsys.readouterr().out
    log = next(tmp_path.glob("md_publish_*.log")).read_text(encoding="utf-8")
    streamed = log.split("=== Attempt 1/3 ===\n", 1)[1].split(
        "\n  --- Phase timings", 1
    )[0]
    assert streamed.splitlines() == ["Uploading content", "Committing update"]


def test_spinner_does_not_start_animation_for_redirected_output(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(
        pw.threading.Thread, "start", lambda _self: pytest.fail("animation started")
    )
    with pw.Spinner("Copying"):
        pass
    assert "+ Copying" in capsys.readouterr().out


def test_main_rejects_conflicting_modes_before_staging(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_workshop.py",
            "release",
            "--version",
            "1.2.3",
            "--full",
            "--base-ref",
            "v1",
        ],
    )
    monkeypatch.setattr(
        pw.tempfile, "mkdtemp", lambda **_kwargs: pytest.fail("staging started")
    )
    with pytest.raises(SystemExit) as exc:
        pw.main()
    assert exc.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err


_DESCRIPTION = (
    "[b]Current Version:[/b] 2.0.0\n"
    "[b]Current HOI4 Version:[/b] 1.19.*\n"
    "[b]Expected Checksum:[/b] ccc6\n"
    "[url=https://example.invalid/v1.12.2]Tutorials for v1.12.*[/url]\n"
    '[b]Café "quoted" \\ text[/b]\n'
)


def _write_description(root, body):
    path = root / "descriptions/descriptions_EN.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    return path


@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_description_changes_only_current_version(tmp_path, ending):
    body = _DESCRIPTION.replace("\n", ending)
    path = _write_description(tmp_path, "\ufeff" + body)
    before = path.read_bytes()
    result = pw.read_description(tmp_path, "2.1.0-beta.5")
    assert result == body.replace(
        "[b]Current Version:[/b] 2.0.0", "[b]Current Version:[/b] 2.1.0-beta.5"
    )
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "body,error",
    [
        (None, "Cannot read English description"),
        (b"\xff", "Cannot read English description"),
        (" \n\t", "empty or contains a NUL"),
        (_DESCRIPTION + "\0", "empty or contains a NUL"),
        ("No version field", "exactly one Current Version"),
        (
            _DESCRIPTION + "[b]Current Version:[/b] 2.1.0\n",
            "exactly one Current Version",
        ),
        (_DESCRIPTION.replace("2.0.0", "not a version"), "invalid Current Version"),
        (_DESCRIPTION + "界" * 3000, "8000-byte limit"),
    ],
)
def test_invalid_description_stops_before_upload(tmp_path, monkeypatch, body, error):
    with pytest.raises(SystemExit, match=error):
        _main_staged(
            tmp_path,
            monkeypatch,
            "release",
            "--username",
            "u",
            "--version",
            "1.2.3",
            "--sync-description",
            description_body=body,
        )


@pytest.mark.parametrize("sync", [False, True])
@pytest.mark.parametrize("mode", ["full", "diff"])
def test_main_description_sync_is_opt_in_and_survives_diff_pruning(
    tmp_path, monkeypatch, sync, mode
):
    args = ["test", "--username", "u", "--version", "V2.1.0-beta.5"]
    if sync:
        args.append("--sync-description")
    if mode == "diff":
        staged = _main_diff_staged(
            tmp_path,
            monkeypatch,
            {"events/foo.txt"},
            *args,
            "--base-ref",
            "v1",
            description_body=_DESCRIPTION,
        )
        assert staged["description_file"] is False
    else:
        staged = _main_staged(
            tmp_path, monkeypatch, *args, description_body=_DESCRIPTION
        )
    assert staged["description"] == (
        _DESCRIPTION.replace("2.0.0", "2.1.0-beta.5") if sync else None
    )


@pytest.mark.parametrize("description", [None, _DESCRIPTION])
def test_publish_vdf_description_preserves_unicode_and_escapes_text(
    tmp_path, monkeypatch, description
):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(
        pw.subprocess, "Popen", lambda *_args, **_kwargs: _SteamProc(["Success"])
    )
    pw.publish(
        _publish_mod(tmp_path), "user", "2777133449", "notes", description=description
    )
    vdf = (tmp_path / "workshop_upload.vdf").read_text(encoding="utf-8")
    if description is None:
        assert '"description"' not in vdf
    else:
        assert '"description"     "' + pw.escape_vdf(description) + '"' in vdf
        assert 'Café \\"quoted\\" \\\\ text' in vdf
        assert "[b]Current Version:[/b] 2.0.0\\n" in vdf
    assert '"title"' not in vdf
    assert '"visibility"' not in vdf
    assert '"publishedfileid" "2777133449"' in vdf


# ---------------------------------------------------------------------------
# Child process finalizers — harmless Python children, never SteamCMD
# ---------------------------------------------------------------------------

posix_only = pytest.mark.skipif(
    os.name != "posix", reason="process groups are POSIX-only"
)

_CHILD = (
    "import signal, sys, time\n"
    "if sys.argv[1] == 'ignore':\n"
    "    signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
    "print('ready', flush=True)\n"
    "time.sleep(60)\n"
)

_WRAPPER = (
    "import subprocess, sys\n"
    "child = subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]])\n"
    "print(child.pid, flush=True)\n"
    "if sys.argv[3] == 'wait':\n"
    "    child.wait()\n"
)


def _spawn(*args, **kwargs):
    return subprocess.Popen(
        [sys.executable, "-c", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )


def _pid_gone(pid):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def test_stop_process_terminates_a_running_child():
    proc = _spawn(_CHILD, "obey")
    assert proc.stdout.readline().strip() == b"ready"

    pw.stop_process(proc)

    assert proc.returncode not in (None, 0)
    assert proc.stdout.closed and proc.stderr.closed


def test_stop_process_leaves_a_finished_child_alone():
    proc = _spawn("print('done')")
    proc.wait()

    pw.stop_process(proc)

    assert proc.returncode == 0
    assert proc.stdout.closed and proc.stderr.closed


@posix_only
def test_stop_process_kills_a_child_that_ignores_termination(monkeypatch):
    monkeypatch.setattr(pw, "STOP_TIMEOUT_SECS", 0.5)
    proc = _spawn(_CHILD, "ignore")
    assert proc.stdout.readline().strip() == b"ready"
    started = time.monotonic()

    pw.stop_process(proc)

    assert proc.returncode == -signal.SIGKILL
    assert time.monotonic() - started < 10


@posix_only
@pytest.mark.parametrize(
    "child_mode,wrapper_mode",
    [("obey", "exit"), ("ignore", "wait"), ("ignore", "exit")],
    ids=["wrapper_exits_first", "child_ignores_term", "both"],
)
def test_stop_process_stops_the_whole_group(
    monkeypatch, capsys, child_mode, wrapper_mode
):
    monkeypatch.setattr(pw, "STOP_TIMEOUT_SECS", 0.5)
    proc = _spawn(_WRAPPER, _CHILD, child_mode, wrapper_mode, start_new_session=True)
    lines = {proc.stdout.readline().strip() for _ in range(2)}
    assert b"ready" in lines
    child_pid = int((lines - {b"ready"}).pop())
    if wrapper_mode == "exit":
        proc.wait()
    started = time.monotonic()

    pw.stop_process(proc, own_group=True)

    assert time.monotonic() - started < 10
    assert _pid_gone(child_pid), "the descendant outlived its wrapper"
    assert proc.returncode is not None
    assert proc.stdout.closed and proc.stderr.closed
    assert "WARNING" not in capsys.readouterr().out


@posix_only
@pytest.mark.parametrize("error", [ProcessLookupError, PermissionError])
def test_signal_group_reports_an_empty_group(monkeypatch, error):
    def gone(_pgid, _sig):
        raise error

    monkeypatch.setattr(pw.os, "killpg", gone)

    assert pw._signal_group(4242, 0) is False


@posix_only
def test_stop_process_warns_when_the_group_survives_escalation(monkeypatch, capsys):
    signals = []
    monkeypatch.setattr(pw, "STOP_TIMEOUT_SECS", 0)
    monkeypatch.setattr(
        pw, "_signal_group", lambda _pgid, sig: signals.append(sig) or True
    )
    proc = _SteamProc([])
    proc.pid = 4242

    pw.stop_process(proc, own_group=True)

    assert [sig for sig in signals if sig] == [signal.SIGTERM, signal.SIGKILL]
    assert "WARNING: Child process 4242 is still running." in capsys.readouterr().out


def test_stop_process_warns_when_a_child_cannot_be_reaped(capsys):
    class _StuckProc:
        pid = 4242
        stdout = stderr = None
        killed = False

        def poll(self):
            return None

        def terminate(self):
            pass

        def kill(self):
            self.killed = True

        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired("stuck", timeout)

    proc = _StuckProc()

    pw.stop_process(proc)

    assert proc.killed
    assert "WARNING: Child process 4242 is still running." in capsys.readouterr().out


def test_copy_repo_closes_the_archive_pipes_without_terminating(tmp_path, monkeypatch):
    proc = _archive_proc(
        monkeypatch, _FakeArchiveProc(_tar_bytes([_file_member("a.txt", b"x\n")]))
    )

    pw.copy_repo(tmp_path / "publish", set())

    assert not proc.terminated
    assert proc.stdout.closed and proc.stderr.closed


@pytest.mark.parametrize("failure", [KeyboardInterrupt, SystemExit])
def test_copy_repo_stops_git_archive_when_interrupted(tmp_path, monkeypatch, failure):
    proc = _archive_proc(monkeypatch, _FakeArchiveProc(_tar_bytes([])))

    def interrupted(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(pw.tarfile, "open", interrupted)

    with pytest.raises(failure):
        pw.copy_repo(tmp_path / "publish", set())

    assert proc.terminated
    assert proc.stdout.closed and proc.stderr.closed


@pytest.mark.parametrize("failure", [KeyboardInterrupt, SystemExit, OSError])
def test_publish_stops_the_upload_group_and_keeps_the_log(
    tmp_path, monkeypatch, failure
):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(pw, "OWN_GROUP", True)
    stopped = []
    monkeypatch.setattr(
        pw,
        "stop_process",
        lambda proc, own_group=False: stopped.append((proc, own_group)),
    )

    class _FailingOutput:
        def __iter__(self):
            return self

        def __next__(self):
            raise failure

    proc = _SteamProc([])
    proc.stdout = _FailingOutput()
    popen_kwargs = {}

    def fake_popen(_cmd, **kwargs):
        popen_kwargs.update(kwargs)
        return proc

    monkeypatch.setattr(pw.subprocess, "Popen", fake_popen)

    with pytest.raises(failure):
        pw.publish(_publish_mod(tmp_path), "user", "1", "note")

    assert stopped == [(proc, True)]
    assert popen_kwargs["start_new_session"] is True
    log = next(tmp_path.glob("md_publish_*.log")).read_text(encoding="utf-8")
    assert "--- workshop_upload.vdf ---" in log
    assert "=== Attempt 1/3 ===" in log


def test_publish_stops_every_retry_attempt(tmp_path, monkeypatch):
    _stub_publish_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(pw.time, "sleep", lambda _seconds: None)
    procs = [
        _SteamProc(["Uploading content failed"], returncode=1),
        _SteamProc(["Committing update"]),
    ]
    remaining = iter(procs)
    stopped = []
    monkeypatch.setattr(
        pw, "stop_process", lambda proc, own_group=False: stopped.append(proc)
    )
    monkeypatch.setattr(pw.subprocess, "Popen", lambda *_a, **_k: next(remaining))

    pw.publish(_publish_mod(tmp_path), "user", "1", "note")

    assert stopped == procs
    log = next(tmp_path.glob("md_publish_*.log")).read_text(encoding="utf-8")
    assert "=== Attempt 1/3 ===" in log
    assert "=== Attempt 2/3 ===" in log


def test_termination_signals_become_system_exit(monkeypatch):
    installed = {}
    monkeypatch.setattr(
        pw.signal, "signal", lambda sig, handler: installed.update({sig: handler})
    )

    pw.exit_on_termination_signals()

    assert signal.SIGTERM in installed
    for sig, handler in installed.items():
        with pytest.raises(SystemExit, match="Interrupted by signal"):
            handler(sig, None)


# ---------------------------------------------------------------------------
# Staging cleanup
# ---------------------------------------------------------------------------

_FULL_ARGS = ("test", "--username", "u", "--version", "1.2.3")


def test_remove_staging_ignores_a_missing_path(tmp_path, capsys):
    pw.remove_staging(tmp_path / "gone")

    assert capsys.readouterr().out == ""


def test_remove_staging_clears_read_only_entries(tmp_path, capsys):
    staging = tmp_path / "pub"
    locked_dir = staging / "mod" / "events"
    locked_dir.mkdir(parents=True)
    write_text(locked_dir / "a.txt", "content")
    os.chmod(locked_dir / "a.txt", stat.S_IREAD)
    os.chmod(locked_dir, stat.S_IREAD | stat.S_IEXEC)

    pw.remove_staging(staging)

    assert not staging.exists()
    assert capsys.readouterr().out == ""


def test_remove_staging_leaves_symlink_targets_untouched(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    write_text(secret, "keep")
    os.chmod(secret, stat.S_IREAD)
    mode_before = secret.stat().st_mode
    staging = tmp_path / "pub"
    locked_dir = staging / "mod"
    locked_dir.mkdir(parents=True)
    try:
        os.symlink(outside, locked_dir / "escape", target_is_directory=True)
        os.symlink(secret, locked_dir / "secret-link")
    except OSError:
        pytest.skip("symlinks unavailable")
    os.chmod(locked_dir, stat.S_IREAD | stat.S_IEXEC)

    pw.remove_staging(staging)

    assert not staging.exists()
    assert secret.read_text(encoding="utf-8") == "keep"
    assert secret.stat().st_mode == mode_before


def test_remove_staging_refuses_a_symlinked_staging_path(tmp_path, capsys):
    outside = tmp_path / "outside"
    outside.mkdir()
    write_text(outside / "keep.txt", "keep")
    staging = tmp_path / "pub"
    try:
        os.symlink(outside, staging, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")

    pw.remove_staging(staging)

    assert (outside / "keep.txt").read_text(encoding="utf-8") == "keep"
    out = capsys.readouterr().out
    assert f"WARNING: Could not remove staging directory {staging}" in out


def test_remove_staging_warns_with_the_leftover_path(tmp_path, monkeypatch, capsys):
    staging = tmp_path / "pub"
    (staging / "mod").mkdir(parents=True)

    def locked(_path, ignore_errors=False):
        if not ignore_errors:
            raise PermissionError("file in use")

    monkeypatch.setattr(pw.shutil, "rmtree", locked)

    pw.remove_staging(staging)

    out = capsys.readouterr().out
    assert f"WARNING: Could not remove staging directory {staging}: file in use" in out
    assert staging.is_dir()


def test_main_removes_staging_after_a_successful_run(tmp_path, monkeypatch):
    _main_staged(tmp_path, monkeypatch, *_FULL_ARGS)

    assert not (tmp_path / "pub").exists()


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_main_removes_staging_when_the_upload_fails(tmp_path, monkeypatch, failure):
    _prepare_full_main(tmp_path, monkeypatch, *_FULL_ARGS)
    monkeypatch.setattr(pw, "copy_repo", lambda dest, _ex: _staged_mod(dest, None))

    def failing_publish(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(pw, "publish", failing_publish)

    with pytest.raises(failure):
        pw.main()

    assert not (tmp_path / "pub").exists()


def test_main_removes_partial_staging_when_the_copy_fails(tmp_path, monkeypatch):
    _prepare_full_main(tmp_path, monkeypatch, *_FULL_ARGS)

    def partial_copy(dest_parent, _excludes):
        (dest_parent / "mod" / "events").mkdir(parents=True)
        write_text(dest_parent / "mod" / "events" / "half.txt", "partial")
        raise RuntimeError("git archive HEAD failed")

    monkeypatch.setattr(pw, "copy_repo", partial_copy)

    with pytest.raises(RuntimeError, match="git archive HEAD failed"):
        pw.main()

    assert not (tmp_path / "pub").exists()


def test_main_keeps_the_original_error_when_cleanup_fails(
    tmp_path, monkeypatch, capsys
):
    _prepare_full_main(tmp_path, monkeypatch, *_FULL_ARGS)

    def broken_copy(_dest_parent, _excludes):
        raise RuntimeError("copy broke")

    def locked(_path, ignore_errors=False):
        if not ignore_errors:
            raise PermissionError("file in use")

    monkeypatch.setattr(pw, "copy_repo", broken_copy)
    monkeypatch.setattr(pw.shutil, "rmtree", locked)

    with pytest.raises(RuntimeError, match="copy broke"):
        pw.main()

    out = capsys.readouterr().out
    assert f"WARNING: Could not remove staging directory {tmp_path / 'pub'}" in out


def test_repeated_and_overlapping_runs_keep_separate_staging(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["publish_workshop.py", *_FULL_ARGS])
    monkeypatch.setattr(pw.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(pw, "copy_repo", lambda dest, _ex: _staged_mod(dest, None))
    saved_log = tmp_path / "md_publish_earlier.log"
    write_text(saved_log, "earlier run\n")
    staged = []

    def fake_publish(mod_dir, *_args, **_kwargs):
        staged.append(mod_dir)
        if len(staged) == 1:
            # A second run starts and finishes while the first is still live.
            pw.main()
            assert mod_dir.is_dir(), "the inner run removed the outer staging"

    monkeypatch.setattr(pw, "publish", fake_publish)

    pw.main()
    pw.main()

    assert len({mod_dir.parent for mod_dir in staged}) == 3
    assert list(tmp_path.glob("md_publish_*")) == [saved_log]
