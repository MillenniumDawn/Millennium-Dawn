"""Tests for `disk_cache.per_file_cached`, `aggregate_cached`, and the
`MD_NO_CACHE` bypass."""

import os

import disk_cache
import pytest


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Each test starts with MD_NO_CACHE unset so tests can opt in explicitly."""
    monkeypatch.delenv("MD_NO_CACHE", raising=False)


def test_per_file_cached_hits_on_unchanged_file(tmp_path):
    src = tmp_path / "data.txt"
    src.write_text("hello")
    calls = []

    def compute():
        calls.append(1)
        return src.read_text().upper()

    first = disk_cache.per_file_cached(str(tmp_path), "ns", str(src), compute)
    second = disk_cache.per_file_cached(str(tmp_path), "ns", str(src), compute)

    assert first == "HELLO" == second
    assert len(calls) == 1, "Second call must hit the cache"


def test_per_file_cached_recomputes_when_file_changes(tmp_path):
    src = tmp_path / "data.txt"
    src.write_text("hello")
    calls = []

    def compute():
        calls.append(1)
        return src.read_text().upper()

    disk_cache.per_file_cached(str(tmp_path), "ns", str(src), compute)
    # Mutate the file — write_text refreshes mtime.
    src.write_text("world!")
    # Ensure mtime actually moves on filesystems with coarse resolution.
    os.utime(str(src), (os.stat(str(src)).st_atime + 1, os.stat(str(src)).st_mtime + 1))
    result = disk_cache.per_file_cached(str(tmp_path), "ns", str(src), compute)

    assert result == "WORLD!"
    assert len(calls) == 2, "Cache must invalidate after file change"


def test_no_cache_env_bypasses_per_file(tmp_path, monkeypatch):
    src = tmp_path / "data.txt"
    src.write_text("hello")
    calls = []

    def compute():
        calls.append(1)
        return "ok"

    monkeypatch.setenv("MD_NO_CACHE", "1")
    disk_cache.per_file_cached(str(tmp_path), "ns", str(src), compute)
    disk_cache.per_file_cached(str(tmp_path), "ns", str(src), compute)

    assert len(calls) == 2, "MD_NO_CACHE=1 must skip cache reads"
    # No cache file should have been written either.
    cache_dir = disk_cache.cache_root(str(tmp_path)) / "per_file"
    assert not cache_dir.exists() or not any(cache_dir.rglob("*.pickle"))


def test_no_cache_env_bypasses_aggregate(tmp_path, monkeypatch):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("a")
    b.write_text("b")
    calls = []

    def factory():
        calls.append(1)
        return "merged"

    monkeypatch.setenv("MD_NO_CACHE", "1")
    disk_cache.aggregate_cached(str(tmp_path), "key", [str(a), str(b)], factory)
    disk_cache.aggregate_cached(str(tmp_path), "key", [str(a), str(b)], factory)

    assert len(calls) == 2, "MD_NO_CACHE=1 must skip aggregate cache too"


def test_aggregate_cached_invalidates_when_file_added(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("a")
    calls = []

    def factory():
        calls.append(1)
        return "ok"

    disk_cache.aggregate_cached(str(tmp_path), "key", [str(a)], factory)
    b = tmp_path / "b.txt"
    b.write_text("b")
    disk_cache.aggregate_cached(str(tmp_path), "key", [str(a), str(b)], factory)

    assert len(calls) == 2, "Adding a tracked file must invalidate the aggregate"
