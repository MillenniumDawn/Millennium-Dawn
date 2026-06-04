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

Pool workers can call all three directly — they're process-safe via `os.replace`.
Errors loading a stale or corrupt cache fall back to recomputing.

## Layout

```
.validation_cache/
  v1/
    per_file/<namespace>/<sha1(path)>.pickle
    aggregate/<sha1(key)>.pickle
```

Bumping `disk_cache.CACHE_VERSION` invalidates every entry — use that when
changing the on-disk schema.

## CI integration

`.github/workflows/coding-pipeline.yml` restores the cache via
`actions/cache` keyed on `<runner>-<validator>-<base SHA>-<hash of
tools/validation>`. PRs that don't touch validator code restore the main
branch's cache and re-scan only the changed mod files.

## Clearing locally

```bash
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
