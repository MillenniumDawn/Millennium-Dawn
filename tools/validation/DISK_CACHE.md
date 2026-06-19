# Validator disk cache

Heavy validators persist their per-file scan results under
`.validation_cache/` (gitignored). A re-run only re-scans files whose mtime
or size changed.

## How it works

`tools/validation/disk_cache.py` exposes two helpers:

```python
disk_cache.per_file_cached(mod_path, namespace, source_path, compute_fn)
disk_cache.per_file_cached_by_content(mod_path, namespace, source_path, content, compute_fn)
disk_cache.aggregate_cached(mod_path, key, tracked_files, factory_fn)
```

| Function                     | Key                                      | Use when                                               |
| ---------------------------- | ---------------------------------------- | ------------------------------------------------------ |
| `per_file_cached`            | `(filename, mtime_ns, size)` + namespace | One result per source file (mtime-based)               |
| `per_file_cached_by_content` | `(len, sha1(content))` + namespace       | One result per source file, keyed on content not mtime |
| `aggregate_cached`           | `(mtime_ns, size)` of every tracked file | Merged result that depends on the whole tree           |

`per_file_cached_by_content` is preferred on CI, where git checkouts reset mtimes and make the stat-based key miss every entry. Supply the already-read content string; no extra file read.

Most validators use `per_file_cached_by_content` indirectly via `BaseValidator.parse_files_cached()`, which handles file collection, comment stripping, and caching in one call. Direct `disk_cache.*` calls are mainly for aggregate scans or pool-worker paths that operate outside the standard parse loop.

Pool workers can call all three directly — they're process-safe via SQLite WAL
mode (concurrent readers, serialized writers with a 30s busy timeout). Errors
loading a stale or corrupt cache fall back to recomputing.

## Layout

```
.validation_cache/
  v5/
    cache.db        # single SQLite db: one row per (namespace, key)
    cache.db-wal
    cache.db-shm
```

Every entry is a row `(namespace, key, tag, value)` — `tag` is the stat/content
signature used to detect staleness, `value` is the pickled result. Re-writing an
entry does `INSERT OR REPLACE`, overwriting the row in place, so the file count
stays at one no matter how many entries accumulate. (The pre-v5 layout wrote one
pickle file per entry, which ballooned to 100k+ files.)

Bumping `disk_cache.CACHE_VERSION` invalidates every entry — use that when
changing the on-disk schema. The previous version's `v<N>/` tree is orphaned by
the bump; `run_all_validators.py` calls `disk_cache.prune_old_versions()` at
startup to delete any non-current `v<N>/` dir, so stale versions clean
themselves up on the next suite run.

## CI integration

`.github/workflows/coding-pipeline.yml` restores the cache via
`actions/cache` keyed on `<runner>-<validator>-<base SHA>-<hash of
tools/validation>`. PRs that don't touch validator code restore the main
branch's cache and re-scan only the changed mod files.

## Auto-reset when stale

`run_all_validators.py` records the cache's creation time in
`.validation_cache/created` and, on each run, clears the whole cache when it is
older than **7 days** (rebuilding from scratch that run). A single db file never
re-bloats the way the old layout did, but rows for deleted files and stale
namespace hashes still accumulate over time; the weekly reset bounds that. Tune
or disable it:

```bash
python3 tools/validation/run_all_validators.py --cache-max-age-days 14   # reset after two weeks
python3 tools/validation/run_all_validators.py --cache-max-age-days 0    # disable auto-reset
```

## Clearing locally

```bash
# Reset the cache and re-validate in one step:
python3 tools/validation/run_all_validators.py --clear-cache

# Or just delete it:
rm -rf .validation_cache/
# or, from a Python REPL:
python3 -c "import sys; sys.path.insert(0,'tools/validation'); import disk_cache; disk_cache.clear('.')"
```

## Bypassing for one run

When iterating on a validator's internal logic, the cache keys on file
stat (not validator source), so behavior changes are invisible until
`CACHE_VERSION` bumps. Use `--no-cache` to skip every read and write for a
single run without touching the on-disk cache:

```bash
python3 tools/validation/run_all_validators.py --no-cache
```

Equivalent for individual validators or other entry points:

```bash
MD_NO_CACHE=1 python3 tools/validation/validate_variables.py
```

`--no-cache` exports `MD_NO_CACHE=1` for the spawned subprocesses, so a
single flag covers the entire suite.
