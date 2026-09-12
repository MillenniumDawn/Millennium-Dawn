"""Tests for `disk_cache.per_file_cached`, `aggregate_cached`, and the
`MD_NO_CACHE` bypass."""

import os
import shutil

import disk_cache
import pytest
import sprite_index


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Each test starts with MD_NO_CACHE unset so tests can opt in explicitly."""
    monkeypatch.delenv("MD_NO_CACHE", raising=False)


def _counted_compute(calls, namespace):
    def run():
        calls[namespace] += 1
        return calls[namespace]

    return run


def _patch_helper_change(monkeypatch, namespace, helper_name):
    helper = next(
        path
        for path in disk_cache._fingerprint_paths(namespace)
        if path.name == helper_name
    )
    original_read_bytes = type(helper).read_bytes

    def changed_read_bytes(path):
        if path == helper:
            return original_read_bytes(path) + b"\\nhelper change"
        return original_read_bytes(path)

    monkeypatch.setattr(type(helper), "read_bytes", changed_read_bytes)


def _close_cache_connections():
    with disk_cache._conns_lock:
        for key in list(disk_cache._conns):
            conn = disk_cache._conns.pop(key)
            try:
                conn.close()
            except (OSError, disk_cache.sqlite3.Error):
                pass


def _copy_cache(src, dst):
    _close_cache_connections()
    shutil.copytree(src / disk_cache._CACHE_DIR_NAME, dst / disk_cache._CACHE_DIR_NAME)


def _two_identical_files(tmp_path, rel="common/x.txt", body="hello"):
    first = tmp_path / "a"
    second = tmp_path / "b"
    for root in (first, second):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return first, second


def _warm_content(root, content="hello", namespace="ns", rel="common/x.txt"):
    calls = []

    def compute():
        calls.append(1)
        return content

    disk_cache.per_file_cached_by_content(
        str(root), namespace, str(root / rel), content, compute
    )
    return calls, compute


def test_code_fingerprints_are_scoped_to_owner_and_shared_code():
    events = disk_cache._fingerprint_paths("events.metadata")
    focus = disk_cache._fingerprint_paths("focus_tree.parse")
    party_loc = disk_cache._fingerprint_paths("party_loc.registered_tags")
    sprites = disk_cache._fingerprint_paths("sprite_index.names")

    assert any(path.name == "validate_events.py" for path in events)
    assert any(path.name == "shared_utils.py" for path in events)
    assert any(path.name == "validator_common.py" for path in events)
    assert not any(path.name == "validate_focus_tree.py" for path in events)
    assert any(path.name == "validate_focus_tree.py" for path in focus)
    assert any(path.name == "validate_party_loc.py" for path in party_loc)
    assert any(path.name == "validate_gfx_references.py" for path in sprites)
    assert not any(path.name == "validate_focus_tree.py" for path in sprites)


def test_sprite_index_cached_and_uncached_results_match(tmp_path, monkeypatch):
    gfx = tmp_path / "sample.gfx"
    gfx.write_text('spriteType = { name = "GFX_sample" }', encoding="utf-8")

    cached = sprite_index._names_in_file(str(gfx), str(tmp_path))
    monkeypatch.setenv("MD_NO_CACHE", "1")
    uncached = sprite_index._names_in_file(str(gfx), str(tmp_path))

    assert cached == uncached == ["GFX_sample"]


def test_sprite_index_helper_change_invalidates_actual_cache(tmp_path, monkeypatch):
    gfx = tmp_path / "sample.gfx"
    gfx.write_text('spriteType = { name = "GFX_sample" }', encoding="utf-8")
    disk_cache._FINGERPRINT_CACHE.clear()
    sprite_index._names_in_file(str(gfx), str(tmp_path))

    original_parse = sprite_index._parse_names
    calls = []

    def counted_parse(raw):
        calls.append(raw)
        return original_parse(raw)

    _patch_helper_change(
        monkeypatch, "sprite_index.names", "validate_gfx_references.py"
    )
    monkeypatch.setattr(sprite_index, "_parse_names", counted_parse)
    disk_cache._FINGERPRINT_CACHE.clear()

    assert sprite_index._names_in_file(str(gfx), str(tmp_path)) == ["GFX_sample"]
    assert len(calls) == 1


def test_namespace_mapping_covers_all_real_cache_prefixes():
    expected = {
        "agency",
        "building_guards_scan_v3",
        "cosmetic",
        "decisions",
        "dlc_guards",
        "dynamic_modifier_guards_scan_v1",
        "events",
        "focus_tree",
        "gfx_ref",
        "history_techs",
        "ideas",
        "loc",
        "math_expr",
        "modifiers",
        "oob_units",
        "on_actions",
        "party_loc",
        "scripted_gui",
        "sgui",
        "scripted_params",
        "set_variables",
        "simplifications",
        "sprite_index",
        "style",
        "unused_scripted",
        "unused_textures",
        "variables",
    }
    assert expected <= set(disk_cache._VALIDATOR_NAMESPACES)


def test_fingerprints_are_memoized_until_source_changes(tmp_path, monkeypatch):
    source = tmp_path / "owner.py"
    source.write_text("one", encoding="utf-8")
    monkeypatch.setattr(disk_cache, "_fingerprint_paths", lambda _namespace: [source])
    disk_cache._FINGERPRINT_CACHE.clear()
    calls = []
    original = type(source).read_bytes
    monkeypatch.setattr(
        type(source),
        "read_bytes",
        lambda path: (calls.append(path), original(path))[1],
    )

    first = disk_cache._validator_code_fingerprint("memoized")
    second = disk_cache._validator_code_fingerprint("memoized")

    assert first == second
    assert len(calls) == 1

    # Different length, not just different bytes: Windows clock granularity can
    # leave two writes this close together sharing an mtime, and the memo keys
    # on (path, mtime_ns, size).
    source.write_text("two lines", encoding="utf-8")
    changed = disk_cache._validator_code_fingerprint("memoized")
    assert changed != first
    assert len(calls) == 2


def test_owner_source_change_invalidates_only_that_namespace(tmp_path, monkeypatch):
    owner = tmp_path / "owner.py"
    other_owner = tmp_path / "other_owner.py"
    owner.write_text("one", encoding="utf-8")
    other_owner.write_text("other", encoding="utf-8")
    monkeypatch.setattr(
        disk_cache,
        "_fingerprint_paths",
        lambda namespace: [owner] if namespace.startswith("owned") else [other_owner],
    )
    disk_cache._FINGERPRINT_CACHE.clear()
    calls = {"owned": 0, "other": 0}

    first_owned = disk_cache.per_file_cached_by_content(
        str(tmp_path),
        "owned.result",
        "source.txt",
        "body",
        _counted_compute(calls, "owned"),
    )
    first_other = disk_cache.per_file_cached_by_content(
        str(tmp_path),
        "other.result",
        "source.txt",
        "body",
        _counted_compute(calls, "other"),
    )
    owner.write_text("changed owner", encoding="utf-8")
    second_owned = disk_cache.per_file_cached_by_content(
        str(tmp_path),
        "owned.result",
        "source.txt",
        "body",
        _counted_compute(calls, "owned"),
    )
    second_other = disk_cache.per_file_cached_by_content(
        str(tmp_path),
        "other.result",
        "source.txt",
        "body",
        _counted_compute(calls, "other"),
    )

    assert (first_owned, second_owned) == (1, 2)
    assert (first_other, second_other) == (1, 1)
    assert calls == {"owned": 2, "other": 1}


def test_configured_helper_change_invalidates_affected_namespace_only(
    tmp_path, monkeypatch
):
    source = tmp_path / "data.txt"
    source.write_text("hello", encoding="utf-8")
    disk_cache._FINGERPRINT_CACHE.clear()
    calls = {"building": 0, "events": 0}

    def run_both():
        for namespace, key in (
            ("building_guards_scan_v3.result", "building"),
            ("events.result", "events"),
        ):
            disk_cache.per_file_cached_by_content(
                str(tmp_path),
                namespace,
                str(source),
                "body",
                _counted_compute(calls, key),
            )

    run_both()
    _patch_helper_change(monkeypatch, "building_guards_scan_v3.result", "guard_scan.py")
    disk_cache._FINGERPRINT_CACHE.clear()
    run_both()

    assert calls == {"building": 2, "events": 1}


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
    owner = tmp_path / "owner.py"
    src.write_text("hello")
    owner.write_text("one", encoding="utf-8")
    monkeypatch.setattr(disk_cache, "_fingerprint_paths", lambda _namespace: [owner])
    disk_cache._FINGERPRINT_CACHE.clear()
    calls = []

    def compute():
        calls.append(1)
        return len(calls)

    disk_cache.per_file_cached_by_content(
        str(tmp_path), "parse", str(src), "hello", compute
    )
    owner.write_text("two lines", encoding="utf-8")
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


def test_fingerprint_of_a_missing_source_is_stable(tmp_path, monkeypatch):
    """A validator source that is not on disk must not crash or churn the key."""
    monkeypatch.setattr(
        disk_cache, "_fingerprint_paths", lambda _namespace: [tmp_path / "gone.py"]
    )
    disk_cache._FINGERPRINT_CACHE.clear()

    first = disk_cache._validator_code_fingerprint("absent")
    disk_cache._FINGERPRINT_CACHE.clear()
    second = disk_cache._validator_code_fingerprint("absent")

    assert first == second


def test_results_are_still_computed_when_the_db_cannot_open(tmp_path, monkeypatch):
    monkeypatch.setattr(disk_cache, "_connect", lambda mod_path: None)
    calls = []

    def compute():
        calls.append(1)
        return "ok"

    first = disk_cache.per_file_cached_by_content(
        str(tmp_path), "ns", "f.txt", "body", compute
    )
    second = disk_cache.per_file_cached_by_content(
        str(tmp_path), "ns", "f.txt", "body", compute
    )

    assert (first, second) == ("ok", "ok")
    assert len(calls) == 2


def test_connect_reuses_a_connection_opened_while_waiting_for_the_lock(
    tmp_path, monkeypatch
):
    """The double-checked lock must not open a second connection to one db."""
    sentinel = object()
    conns = {}
    monkeypatch.setattr(disk_cache, "_conns", conns)
    key = (disk_cache.os.getpid(), str(disk_cache._db_path(str(tmp_path))))

    class _RacingLock:
        def __enter__(self):
            conns[key] = sentinel

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(disk_cache, "_conns_lock", _RacingLock())

    assert disk_cache._connect(str(tmp_path)) is sentinel


# ---- cache maintenance -----------------------------------------------------


def test_prune_old_versions_without_a_cache_dir(tmp_path):
    assert disk_cache.prune_old_versions(str(tmp_path)) == []


def test_prune_old_versions_when_the_cache_root_is_not_a_dir(tmp_path, write_path):
    write_path(tmp_path, disk_cache._CACHE_DIR_NAME, "not a directory")
    assert disk_cache.prune_old_versions(str(tmp_path)) == []


def test_prune_old_versions_removes_only_stale_version_dirs(tmp_path, write_path):
    root = tmp_path / disk_cache._CACHE_DIR_NAME
    (root / "v4" / "old").mkdir(parents=True)
    (root / f"v{disk_cache.CACHE_VERSION}").mkdir(parents=True)
    write_path(tmp_path, f"{disk_cache._CACHE_DIR_NAME}/notes.txt", "keep me")
    write_path(tmp_path, f"{disk_cache._CACHE_DIR_NAME}/v3", "a file, not a dir")

    removed = disk_cache.prune_old_versions(str(tmp_path))

    assert removed == ["v4"]
    assert not (root / "v4").exists()
    assert (root / "v3").is_file()
    assert (root / f"v{disk_cache.CACHE_VERSION}").is_dir()


def test_prune_old_versions_survives_a_failing_removal(tmp_path, monkeypatch):
    (tmp_path / disk_cache._CACHE_DIR_NAME / "v4").mkdir(parents=True)
    monkeypatch.setattr(
        disk_cache.shutil,
        "rmtree",
        lambda *a, **k: (_ for _ in ()).throw(OSError("busy")),
    )

    assert disk_cache.prune_old_versions(str(tmp_path)) == []


def test_clear_closes_open_connections_even_when_close_fails(tmp_path, monkeypatch):
    conns = {}
    monkeypatch.setattr(disk_cache, "_conns", conns)
    key = (disk_cache.os.getpid(), str(disk_cache._db_path(str(tmp_path))))

    class _Stubborn:
        def close(self):
            raise OSError("still in use")

    conns[key] = _Stubborn()
    (tmp_path / disk_cache._CACHE_DIR_NAME).mkdir()

    disk_cache.clear(str(tmp_path))

    assert conns == {}
    assert not (tmp_path / disk_cache._CACHE_DIR_NAME).exists()


def test_clear_survives_a_failing_tree_removal(tmp_path, monkeypatch):
    (tmp_path / disk_cache._CACHE_DIR_NAME).mkdir()
    monkeypatch.setattr(
        disk_cache.shutil,
        "rmtree",
        lambda *a, **k: (_ for _ in ()).throw(OSError("busy")),
    )

    disk_cache.clear(str(tmp_path))

    assert (tmp_path / disk_cache._CACHE_DIR_NAME).exists()


def test_stamp_created_survives_an_unwritable_cache_root(tmp_path, write_path):
    write_path(tmp_path, disk_cache._CACHE_DIR_NAME, "not a directory")

    disk_cache.stamp_created(str(tmp_path))

    assert disk_cache.cache_age_days(str(tmp_path)) is None


def test_clear_if_stale_keeps_a_fresh_cache(tmp_path):
    disk_cache.stamp_created(str(tmp_path))

    assert disk_cache.clear_if_stale(str(tmp_path), 7.0) is False
    assert disk_cache._marker_path(str(tmp_path)).exists()


def test_source_key_is_relative_under_the_checkout(tmp_path):
    source = tmp_path / "common" / "x.txt"
    source.parent.mkdir()
    source.write_text("hello", encoding="utf-8")

    assert disk_cache._source_key(str(tmp_path), str(source)) == "common/x.txt"
    assert disk_cache._source_key(str(tmp_path), "already/rel.txt") == (
        "already/rel.txt"
    )


def test_code_fingerprint_ignores_checkout_root(tmp_path, monkeypatch):
    first = tmp_path / "a" / "owner.py"
    second = tmp_path / "b" / "owner.py"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("same", encoding="utf-8")
    second.write_text("same", encoding="utf-8")
    disk_cache._FINGERPRINT_CACHE.clear()
    monkeypatch.setattr(disk_cache, "_fingerprint_paths", lambda _ns: [first])
    left = disk_cache._validator_code_fingerprint("ns")
    disk_cache._FINGERPRINT_CACHE.clear()
    monkeypatch.setattr(disk_cache, "_fingerprint_paths", lambda _ns: [second])
    right = disk_cache._validator_code_fingerprint("ns")

    assert left == right


def test_copied_content_cache_hits_at_a_different_root(tmp_path):
    first, second = _two_identical_files(tmp_path)
    calls, compute = _warm_content(first)
    _copy_cache(first, second)
    disk_cache.per_file_cached_by_content(
        str(second), "ns", str(second / "common" / "x.txt"), "hello", compute
    )

    assert calls == [1]
    conn = disk_cache._connect(str(first))
    assert conn is not None
    keys = [row[0] for row in conn.execute("SELECT key FROM entries")]
    assert keys == ["common/x.txt"]


def test_modified_content_at_the_new_root_misses(tmp_path):
    first, second = _two_identical_files(tmp_path)
    calls, compute = _warm_content(first)
    _copy_cache(first, second)
    disk_cache.per_file_cached_by_content(
        str(second), "ns", str(second / "common" / "x.txt"), "changed", compute
    )

    assert calls == [1, 1]


def test_helper_change_still_invalidates_after_a_copy(tmp_path, monkeypatch):
    first, second = _two_identical_files(tmp_path)
    calls = []

    def compute():
        calls.append(1)
        return "ok"

    disk_cache._FINGERPRINT_CACHE.clear()
    disk_cache.per_file_cached_by_content(
        str(first),
        "sprite_index.names",
        str(first / "common" / "x.txt"),
        "hello",
        compute,
    )
    _copy_cache(first, second)
    _patch_helper_change(
        monkeypatch, "sprite_index.names", "validate_gfx_references.py"
    )
    disk_cache._FINGERPRINT_CACHE.clear()
    disk_cache.per_file_cached_by_content(
        str(second),
        "sprite_index.names",
        str(second / "common" / "x.txt"),
        "hello",
        compute,
    )

    assert calls == [1, 1]


def test_deleted_tracked_file_invalidates_aggregate_after_a_copy(tmp_path):
    first, second = _two_identical_files(tmp_path)
    extra = first / "common" / "y.txt"
    extra.write_text("y", encoding="utf-8")
    (second / "common" / "y.txt").write_text("y", encoding="utf-8")
    calls = []

    def factory():
        calls.append(1)
        return "merged"

    tracked_first = [str(first / "common" / "x.txt"), str(extra)]
    disk_cache.aggregate_cached(str(first), "agg", tracked_first, factory)
    _copy_cache(first, second)
    (second / "common" / "y.txt").unlink()
    disk_cache.aggregate_cached(
        str(second), "agg", [str(second / "common" / "x.txt")], factory
    )

    assert calls == [1, 1]


def test_embedded_checkout_paths_rehome_on_restore(tmp_path):
    first, second = _two_identical_files(tmp_path)
    src_first = str(first / "common" / "x.txt")
    src_second = str(second / "common" / "x.txt")
    disk_cache.per_file_cached_by_content(
        str(first),
        "ns",
        src_first,
        "hello",
        lambda: {"file": src_first, "ok": True},
    )
    _copy_cache(first, second)
    result = disk_cache.per_file_cached_by_content(
        str(second),
        "ns",
        src_second,
        "hello",
        lambda: {"file": "miss", "ok": False},
    )

    assert result == {"file": src_second, "ok": True}


def test_sprite_textures_rehome_and_do_not_store_absolute_paths(tmp_path):
    first, second = _two_identical_files(tmp_path)
    gfx_body = (
        'spriteType = {\n\tname = "GFX_g"\n' '\ttexturefile = "gfx/art/g.dds"\n}\n'
    )
    for root in (first, second):
        gfx = root / "interface" / "g.gfx"
        gfx.parent.mkdir(parents=True)
        gfx.write_text(gfx_body, encoding="utf-8")
    index_first = sprite_index.build_sprite_texture_index(
        str(first), include_vanilla=False
    )
    conn = disk_cache._connect(str(first))
    assert conn is not None
    row = conn.execute(
        "SELECT value FROM entries WHERE namespace = ?",
        ("sprite_index.textures",),
    ).fetchone()
    stored = disk_cache._unpack(str(first), row[0])
    assert stored == [["GFX_g", "gfx/art/g.dds"]]
    assert str(first) not in str(stored)
    _copy_cache(first, second)
    index_second = sprite_index.build_sprite_texture_index(
        str(second), include_vanilla=False
    )

    assert index_first["GFX_g"] == os.path.join(str(first), "gfx", "art", "g.dds")
    assert index_second["GFX_g"] == os.path.join(str(second), "gfx", "art", "g.dds")
    assert str(first) not in index_second["GFX_g"]


def test_vanilla_install_paths_do_not_leak_across_installs(tmp_path, monkeypatch):
    first, second = _two_identical_files(tmp_path)
    for root in (first, second):
        (root / "interface").mkdir(parents=True, exist_ok=True)
        (root / "interface" / "mod.gfx").write_text(
            'spriteType = { name = "GFX_mod" texturefile = "gfx/mod.dds" }\n',
            encoding="utf-8",
        )
    van_first = tmp_path / "van_a" / "interface" / "v.gfx"
    van_second = tmp_path / "van_b" / "interface" / "v.gfx"
    van_first.parent.mkdir(parents=True)
    van_second.parent.mkdir(parents=True)
    gfx_text = 'spriteType = { name = "GFX_van" texturefile = "gfx/van.dds" }\n'
    van_first.write_text(gfx_text, encoding="utf-8")
    van_second.write_text(gfx_text, encoding="utf-8")
    monkeypatch.setattr(sprite_index, "_vanilla_gfx_files", lambda: [str(van_first)])
    index_first = sprite_index.build_sprite_texture_index(
        str(first), include_vanilla=True
    )
    _copy_cache(first, second)
    monkeypatch.setattr(sprite_index, "_vanilla_gfx_files", lambda: [str(van_second)])
    index_second = sprite_index.build_sprite_texture_index(
        str(second), include_vanilla=True
    )

    assert index_first["GFX_van"].endswith(os.path.join("gfx", "van.dds"))
    assert str(tmp_path / "van_a") in index_first["GFX_van"]
    assert index_second["GFX_van"].endswith(os.path.join("gfx", "van.dds"))
    assert str(tmp_path / "van_b") in index_second["GFX_van"]
    assert str(tmp_path / "van_a") not in index_second["GFX_van"]


def test_portable_key_and_rehome_edges(tmp_path):
    old = str(tmp_path / "old")
    new = str(tmp_path / "new")
    posix_new = os.path.normpath(new).replace("\\", "/")
    assert disk_cache._source_key(str(tmp_path), "") == ""
    assert disk_cache._source_key(str(tmp_path), str(tmp_path)) == "."
    outside = tmp_path.parent / "other.txt"
    assert disk_cache._source_key(str(tmp_path), str(outside)) == os.path.normpath(
        str(outside)
    ).replace("\\", "/")
    assert disk_cache._rehome_str(old, old, new) == posix_new
    assert disk_cache._rehome_mod_paths([old + "/a.txt"], old, new) == [
        os.path.join(new, "a.txt").replace("\\", "/")
    ]
    assert disk_cache._rehome_mod_paths((old + "/a.txt",), old, new) == (
        os.path.join(new, "a.txt").replace("\\", "/"),
    )
    assert disk_cache._rehome_mod_paths({old + "/a.txt"}, old, new) == {
        os.path.join(new, "a.txt").replace("\\", "/")
    }
    assert disk_cache._rehome_mod_paths(frozenset({old + "/a.txt"}), old, new) == (
        frozenset({os.path.join(new, "a.txt").replace("\\", "/")})
    )
    from collections import namedtuple

    rec = namedtuple("Rec", "path")
    moved = disk_cache._rehome_mod_paths(rec(old + "/a.txt"), old, new)
    assert moved.path == os.path.join(new, "a.txt").replace("\\", "/")
    loop: list = []
    loop.append(loop)
    disk_cache._rehome_mod_paths(loop, old, new)
    with pytest.raises(disk_cache.pickle.UnpicklingError):
        disk_cache._unpack(str(tmp_path), disk_cache.pickle.dumps(("nope",)))
