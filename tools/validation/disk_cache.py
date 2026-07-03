#!/usr/bin/env python3
"""Disk-backed cache for expensive validator computations.

`per_file_cached` keys each entry on `(filename, mtime_ns, size)` so a re-run
only re-scans files that changed. `per_file_cached_by_content` keys on a content
hash instead (survives git checkouts that reset mtimes). `aggregate_cached`
invalidates a single merged result when any contributing file's stat changes.

Storage is a single SQLite database at `.validation_cache/v<N>/cache.db`
(gitignored). One row per `(namespace, key)`; re-writing an entry overwrites the
prior row in place, so the on-disk file count stays at one regardless of how many
entries exist (the old layout wrote one pickle per entry — 100k+ files). WAL mode
lets the many pool workers, spread across many validator processes, read
concurrently and write under a short serialized lock.

Bypass: set ``MD_NO_CACHE=1`` in the environment or pass ``--no-cache`` to any
validator (which sets the env var automatically). Both skip every lookup and
every write.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import shutil
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# Bump to invalidate every entry after a schema change. v5 replaced the
# one-pickle-per-entry layout with a single SQLite db; prune_old_versions drops
# the orphaned v4 tree (100k+ files) on the next suite run. v6 invalidated the
# scripted_params token cache after the 3-tuple → 4-tuple token format change
# (the cache keys on file content, not validator source, so a format change in
# the token shape requires a version bump to avoid stale 3-tuple entries).
CACHE_VERSION = 6

_CACHE_DIR_NAME = ".validation_cache"
# Records when the cache was created / last cleared (one unix timestamp), so the
# suite can auto-reset a cache that has been accumulating orphaned rows for a
# while. Lives at the cache root (version-independent), not inside a v<N> dir.
_CREATED_MARKER = "created"

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS entries ("
    " namespace TEXT NOT NULL,"
    " key TEXT NOT NULL,"
    " tag TEXT NOT NULL,"
    " value BLOB NOT NULL,"
    " PRIMARY KEY (namespace, key)"
    ") WITHOUT ROWID"
)

# A SQLite connection cannot be shared across a fork, so each process (the main
# validator and every pool worker) opens its own on first use, keyed by pid. The
# lock guards the rare threaded caller — pool workers are separate processes.
_conns: Dict[Tuple[int, str], sqlite3.Connection] = {}
_conns_lock = threading.Lock()

_DB_ERRORS = (sqlite3.Error, pickle.UnpicklingError, pickle.PicklingError, OSError)


# Setting MD_NO_CACHE=1 in the environment bypasses every cache lookup and
# every cache write — useful when iterating on a validator's internal logic
# (the cache keys on file stat/content, not on validator source, so behavior
# changes to the validator itself are otherwise invisible until CACHE_VERSION
# bumps). Inherited automatically by subprocesses launched from run_all.
def _cache_disabled() -> bool:
    return os.environ.get("MD_NO_CACHE") == "1"


def cache_root(mod_path: str) -> Path:
    return Path(mod_path) / _CACHE_DIR_NAME / f"v{CACHE_VERSION}"


def _db_path(mod_path: str) -> Path:
    return cache_root(mod_path) / "cache.db"


def _connect(mod_path: str) -> Optional[sqlite3.Connection]:
    key = (os.getpid(), str(_db_path(mod_path)))
    conn = _conns.get(key)
    if conn is not None:
        return conn
    with _conns_lock:
        conn = _conns.get(key)
        if conn is not None:
            return conn
        try:
            db = _db_path(mod_path)
            db.parent.mkdir(parents=True, exist_ok=True)
            # isolation_level=None -> autocommit; busy_timeout makes concurrent
            # writers wait for the WAL write lock rather than erroring out.
            conn = sqlite3.connect(
                str(db), timeout=30.0, isolation_level=None, check_same_thread=False
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute(_SCHEMA)
        except sqlite3.Error:
            return None
        _conns[key] = conn
        return conn


def _get(mod_path: str, namespace: str, key: str, tag: str) -> Tuple[bool, Any]:
    """Return (hit, result). hit is False on miss, stale tag, or any error."""
    conn = _connect(mod_path)
    if conn is None:
        return (False, None)
    try:
        with _conns_lock:
            row = conn.execute(
                "SELECT tag, value FROM entries WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        if row is not None and row[0] == tag:
            return (True, pickle.loads(row[1]))
    except _DB_ERRORS:
        return (False, None)
    return (False, None)


def _put(mod_path: str, namespace: str, key: str, tag: str, result: Any) -> None:
    # Caching is opportunistic — never fail the validator over a cache write.
    conn = _connect(mod_path)
    if conn is None:
        return
    try:
        blob = pickle.dumps(result, protocol=pickle.HIGHEST_PROTOCOL)
        with _conns_lock:
            conn.execute(
                "INSERT OR REPLACE INTO entries (namespace, key, tag, value)"
                " VALUES (?, ?, ?, ?)",
                (namespace, key, tag, blob),
            )
    except _DB_ERRORS:
        pass


def _file_stat(path: str) -> Optional[Tuple[int, int]]:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


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
    tag = f"s:{current_stat[0]}:{current_stat[1]}"
    hit, result = _get(mod_path, namespace, source_path, tag)
    if hit:
        return result
    result = compute_fn()
    _put(mod_path, namespace, source_path, tag, result)
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
    mtimes and make the stat-based key in ``per_file_cached`` miss on every entry
    on CI. The tag is prefixed ``c:`` (vs ``s:`` for stat keys), so a stale
    stat-keyed row under the same namespace simply fails the tag check and gets
    recomputed rather than being misread.
    """
    if _cache_disabled():
        return compute_fn()
    tag = f"c:{len(content)}:{hashlib.sha1(content.encode('utf-8')).hexdigest()}"
    hit, result = _get(mod_path, namespace, source_path, tag)
    if hit:
        return result
    result = compute_fn()
    _put(mod_path, namespace, source_path, tag, result)
    return result


def _stats_tag(stats: Dict[str, Optional[Tuple[int, int]]]) -> str:
    parts = []
    for p in sorted(stats):
        v = stats[p]
        parts.append(f"{p}={v[0]}:{v[1]}" if v else f"{p}=x")
    return "a:" + hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()


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
    tag = _stats_tag(current_stats)
    hit, result = _get(mod_path, "__aggregate__", key, tag)
    if hit:
        return result
    result = factory_fn()
    _put(mod_path, "__aggregate__", key, tag, result)
    return result


def _is_version_dir(name: str) -> bool:
    return len(name) > 1 and name[0] == "v" and name[1:].isdigit()


def prune_old_versions(mod_path: str) -> List[str]:
    """Delete cache dirs left behind by older CACHE_VERSIONs.

    ``cache_root`` only ever writes to ``v{CACHE_VERSION}``; bumping the version
    orphans the previous version's tree (the v4 pickle layout was 100k+ files)
    on disk forever. Removing them keeps the cache from growing without bound
    across schema bumps. Only non-current version dirs are touched, so a run
    still using the current version is unaffected. Returns the names removed
    (e.g. ``["v4"]``).
    """
    root = Path(mod_path) / _CACHE_DIR_NAME
    if not root.exists():
        return []
    current = f"v{CACHE_VERSION}"
    removed: List[str] = []
    try:
        children = list(root.iterdir())
    except OSError:
        return []
    for child in children:
        if child.name == current or not _is_version_dir(child.name):
            continue
        try:
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
                removed.append(child.name)
        except OSError:
            pass
    return removed


def clear(mod_path: str) -> None:
    # Drop any open connection to the db we're about to delete so a later call
    # in this process reopens against the fresh file.
    db = str(_db_path(mod_path))
    with _conns_lock:
        for k in [k for k in _conns if k[1] == db]:
            try:
                _conns.pop(k).close()
            except sqlite3.Error:
                pass
    root = Path(mod_path) / _CACHE_DIR_NAME
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)


def _marker_path(mod_path: str) -> Path:
    return Path(mod_path) / _CACHE_DIR_NAME / _CREATED_MARKER


def stamp_created(mod_path: str) -> None:
    """Record 'now' as the cache creation time, but only if unset.

    Idempotent so the marker tracks creation/last-clear, not last use. Called
    after a clear (the marker was just removed with the tree) and on the first
    run that sees a cache with no marker yet.
    """
    marker = _marker_path(mod_path)
    if marker.exists():
        return
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass


def cache_age_days(mod_path: str) -> Optional[float]:
    """Days since the cache was created/last cleared, or None if not stamped."""
    try:
        created = float(_marker_path(mod_path).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    return max(0.0, (time.time() - created) / 86400.0)


def clear_if_stale(mod_path: str, max_age_days: float) -> bool:
    """Clear the whole cache when it is older than ``max_age_days``.

    Returns True if it cleared. A non-positive ``max_age_days`` disables the
    check. When there is no marker yet (fresh cache or pre-existing one from
    before this feature) the creation time is stamped now, so the age clock
    starts from this run rather than triggering an immediate clear.
    """
    if max_age_days <= 0:
        return False
    age = cache_age_days(mod_path)
    if age is None:
        stamp_created(mod_path)
        return False
    if age > max_age_days:
        clear(mod_path)
        stamp_created(mod_path)
        return True
    return False
