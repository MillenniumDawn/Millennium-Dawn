import os

import archive_stale_branches as A
import pytest


def test_diff_paths_accepts_nul_delimited_unicode(monkeypatch, tmp_path):
    monkeypatch.setattr(
        A,
        "run",
        lambda *_args, **_kwargs: "café.txt\0renamed file.txt\0".encode(),
    )
    assert A.diff_paths("branch", tmp_path) == ["café.txt", "renamed file.txt"]


def test_diff_paths_rejects_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr(A, "run", lambda *_args, **_kwargs: b"../escape.txt\0")
    with pytest.raises(ValueError, match="Unsafe path"):
        A.diff_paths("branch", tmp_path)


def test_remove_stale_files_keeps_only_current_divergences(tmp_path):
    target = tmp_path / "archive"
    (target / "nested").mkdir(parents=True)
    keep = target / "nested" / "keep.txt"
    stale = target / "stale.txt"
    keep.write_text("keep", encoding="utf-8")
    stale.write_text("stale", encoding="utf-8")

    removed = A.remove_stale_files(target, {"nested/keep.txt"})

    assert removed == 1
    assert keep.exists()
    assert not stale.exists()


def test_diff_paths_decodes_filesystem_bytes(monkeypatch, tmp_path):
    raw = os.fsencode("naïve.txt") + b"\0"
    monkeypatch.setattr(A, "run", lambda *_args, **_kwargs: raw)
    assert A.diff_paths("branch", tmp_path) == ["naïve.txt"]
