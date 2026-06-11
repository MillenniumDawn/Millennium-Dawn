#!/usr/bin/env python3
"""Disk-backed cache for expensive validator computations.

`per_file_cached` keys each entry on `(filename, mtime_ns, size)` so a re-run
only re-scans files that changed. `aggregate_cached` invalidates a single
merged result when any contributing file's stat changes.

Cache lives under `.validation_cache/v<N>/` (gitignored). Pool workers call
these directly; atomic writes via `os.replace` keep concurrent writers safe.

Bypass: set ``MD_NO_CACHE=1`` in the environment or pass ``--no-cache`` to
any validator (which sets the env var automatically). Both skip every lookup
and every write.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import shutil
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Tuple

# Bump to invalidate every entry after a schema change.
CACHE_VERSION = 4

_CACHE_DIR_NAME = ".validation_cache"
_PICKLE_ERRORS = (FileNotFoundError, EOFError, pickle.UnpicklingError, OSError)


# Setting MD_NO_CACHE=1 in the environment bypasses every cache lookup and
# every cache write — useful when iterating on a validator's internal logic
# (the cache keys on file stat, not on validator source, so behavior changes
# to the validator itself are otherwise invisible until CACHE_VERSION bumps).
# Inherited automatically by subprocesses launched from run_all_validators.
def _cache_disabled() -> bool:
    return os.environ.get("MD_NO_CACHE") == "1"


def cache_root(mod_path: str) -> Path:
    return Path(mod_path) / _CACHE_DIR_NAME / f"v{CACHE_VERSION}"


def _hash_key(key: str) -> str:
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]


def _per_file_path(mod_path: str, namespace: str, source_path: str) -> Path:
    return (
        cache_root(mod_path)
        / "per_file"
        / namespace
        / f"{_hash_key(source_path)}.pickle"
    )


def _aggregate_path(mod_path: str, key: str) -> Path:
    return cache_root(mod_path) / "aggregate" / f"{_hash_key(key)}.pickle"


def _file_stat(path: str) -> Optional[Tuple[int, int]]:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def _atomic_write(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # Tmp suffix includes pid so two workers racing on the same source don't collide.
    tmp = target.with_suffix(target.suffix + f".{os.getpid()}.tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, target)
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass


def _load(cache_path: Path) -> Optional[dict]:
    try:
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    except _PICKLE_ERRORS:
        return None


def _store(cache_path: Path, entry: dict) -> None:
    # Caching is opportunistic — never fail the validator over a cache write.
    try:
        _atomic_write(cache_path, pickle.dumps(entry, protocol=pickle.HIGHEST_PROTOCOL))
    except (OSError, pickle.PicklingError):
        pass


def per_file_cached(
    mod_path: str,
    namespace: str,
    source_path: str,
    compute_fn: Callable[[], Any],
) -> Any:
    if _cache_disabled():
        return compute_fn()
    current_stat = _file_stat(source_path)
    if current_stat is None:
        return compute_fn()
    cache_path = _per_file_path(mod_path, namespace, source_path)
    entry = _load(cache_path)
    if entry is not None and entry.get("stat") == current_stat:
        return entry["result"]
    result = compute_fn()
    _store(cache_path, {"stat": current_stat, "result": result})
    return result


def per_file_cached_by_content(
    mod_path: str,
    namespace: str,
    source_path: str,
    content: str,
    compute_fn: Callable[[], Any],
) -> Any:
    """Like ``per_file_cached`` but keyed on a content hash instead of file stat.

    The caller supplies ``content`` it has already read, so this adds no extra
    file read. Keying on ``(len, sha1)`` survives git checkouts, which reset
    mtimes and make the stat-based key in ``per_file_cached`` miss on every
    entry on CI. Entries store a ``"content"`` field (vs ``per_file_cached``'s
    ``"stat"``), so a stale stat-keyed entry under the same namespace simply
    fails the check and gets recomputed rather than being misread.
    """
    if _cache_disabled():
        return compute_fn()
    content_key = (len(content), hashlib.sha1(content.encode("utf-8")).hexdigest())
    cache_path = _per_file_path(mod_path, namespace, source_path)
    entry = _load(cache_path)
    if entry is not None and entry.get("content") == content_key:
        return entry["result"]
    result = compute_fn()
    _store(cache_path, {"content": content_key, "result": result})
    return result


def aggregate_cached(
    mod_path: str,
    key: str,
    tracked_files: Iterable[str],
    factory_fn: Callable[[], Any],
) -> Any:
    if _cache_disabled():
        return factory_fn()
    tracked: List[str] = list(tracked_files)
    current_stats = {p: _file_stat(p) for p in tracked}
    cache_path = _aggregate_path(mod_path, key)
    entry = _load(cache_path)
    if entry is not None and entry.get("stats") == current_stats:
        return entry["result"]
    result = factory_fn()
    _store(cache_path, {"stats": current_stats, "result": result})
    return result


def clear(mod_path: str) -> None:
    root = Path(mod_path) / _CACHE_DIR_NAME
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
