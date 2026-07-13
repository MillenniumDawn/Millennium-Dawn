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
    try:
        stat = os.stat(src)
        os.utime(src, (stat.st_atime + 1, stat.st_mtime + 1))
    except OSError as exc:
        pytest.fail(f"Could not update test file timestamp: {exc}")
    result = disk_cache.per_file_cached(str(tmp_path), "ns", str(src), compute)

    assert result == "WORLD!"
    assert len(calls) == 2, "Cache must invalidate after file change"


def test_per_file_content_cache_recomputes_after_code_change(tmp_path, monkeypatch):
    src = tmp_path / "data.txt"
    src.write_text("hello")
    calls = []

    def compute():
        calls.append(1)
        return len(calls)

    disk_cache.per_file_cached_by_content(
        str(tmp_path), "parse", str(src), "hello", compute
    )
    monkeypatch.setattr(disk_cache, "_CODE_FINGERPRINT", "changed-validator-source")
    result = disk_cache.per_file_cached_by_content(
        str(tmp_path), "parse", str(src), "hello", compute
    )

    assert result == 2
    assert len(calls) == 2, "Parser results must not survive validator source changes"


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


def test_validator_no_cache_flag_reaches_pool_workers(tmp_path, monkeypatch):
    # --no-cache was a silent no-op: BaseValidator stored self.no_cache, but the
    # per-file caches run in Pool workers that never see `self`. MD_NO_CACHE is the
    # only channel that reaches them, so the constructor has to set it.
    from validator_common import BaseValidator

    class _V(BaseValidator):
        TITLE = "T"

        def run_validations(self):
            pass

    _V(mod_path=str(tmp_path), use_colors=False, workers=1, no_cache=True)
    assert os.environ.get("MD_NO_CACHE") == "1"
    assert disk_cache._cache_disabled() is True

    calls = []

    def compute():
        calls.append(1)
        return "ok"

    disk_cache.per_file_cached_by_content(str(tmp_path), "ns", "f.txt", "body", compute)
    disk_cache.per_file_cached_by_content(str(tmp_path), "ns", "f.txt", "body", compute)
    assert len(calls) == 2, "--no-cache must bypass the cache the workers actually use"


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
