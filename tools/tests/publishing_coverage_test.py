"""Behavioral tests for tools/publishing/publish_workshop.py.

Covers manifest/config constants, exclude logic, VDF escaping, size/time
formatting, descriptor patching, VDF generation, mod-file validation,
publishable-file filtering, and dir/prune utilities.

No mocks for filesystem behavior — temp dirs exercise the actual code paths.
"""

from __future__ import annotations

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
        (Path("/tmp/mod"), "/tmp/mod"),
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
