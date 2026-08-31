"""Behavioral tests for tools/validation/refresh_vanilla_data.py."""

import importlib

import pytest


@pytest.fixture
def rvd(monkeypatch):
    monkeypatch.setattr("shared_utils.find_hoi4_install", lambda explicit_path=None: "/fake/install")
    import validation.refresh_vanilla_data as module

    importlib.reload(module)
    return module


@pytest.fixture
def tmp_manifests(monkeypatch, tmp_path):
    """Redirect _HERE / _DOC_DIR into a tmp directory for this test."""
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_HERE", str(tmp_path))
    monkeypatch.setattr(
        rvd_mod, "_DOC_DIR", str(tmp_path / "resources/documentation")
    )
    return tmp_path


def test_install_helper_raises_when_no_game(monkeypatch):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "find_hoi4_install", lambda: None)
    with pytest.raises(rvd_mod.RefreshError, match="no HOI4 install"):
        rvd_mod._install()


def test_main_exits_one_when_no_install(monkeypatch):
    import validation.refresh_vanilla_data as rvd_mod

    importlib.reload(rvd_mod)
    monkeypatch.setattr(rvd_mod, "find_hoi4_install", lambda: None)
    monkeypatch.setattr("shared_utils.find_hoi4_install", lambda explicit_path=None: None)

    import sys as _sys

    _sys.argv = ["refresh_vanilla_data.py"]
    try:
        rc = rvd_mod.main()
    finally:
        _sys.argv = []

    assert rc == 1


def test_main_dispatches_each_target(monkeypatch, tmp_path, capsys):
    import validation.refresh_vanilla_data as rvd_mod

    importlib.reload(rvd_mod)
    monkeypatch.setattr(rvd_mod, "find_hoi4_install", lambda: str(tmp_path))
    for name in ("defines", "docs", "fonts", "gui", "paths", "sprites"):
        monkeypatch.setitem(rvd_mod._TARGETS, name, lambda n=name: f"{n}: ok")

    import sys as _sys

    _sys.argv = ["refresh_vanilla_data.py"]
    try:
        rc = rvd_mod.main()
    finally:
        _sys.argv = []

    captured = capsys.readouterr()
    assert rc == 0
    for name in ("defines", "docs", "fonts", "gui", "paths", "sprites"):
        assert f"{name}: ok" in captured.out


def test_main_only_runs_requested_targets(monkeypatch, tmp_path):
    import validation.refresh_vanilla_data as rvd_mod

    importlib.reload(rvd_mod)
    monkeypatch.setattr(rvd_mod, "find_hoi4_install", lambda: str(tmp_path))

    called = []

    def only_sprites():
        called.append("sprites")
        return "vanilla_sprites.txt: 1 entries"

    def exploded():
        called.append("defines")
        raise rvd_mod.RefreshError("should not be called")

    monkeypatch.setitem(rvd_mod._TARGETS, "sprites", only_sprites)
    monkeypatch.setitem(rvd_mod._TARGETS, "defines", exploded)

    import sys as _sys

    _sys.argv = ["refresh_vanilla_data.py", "--only", "sprites"]
    try:
        rc = rvd_mod.main()
    finally:
        _sys.argv = []

    assert rc == 0
    assert called == ["sprites"]


def test_main_returns_one_when_target_fails(monkeypatch, tmp_path, capsys):
    import validation.refresh_vanilla_data as rvd_mod

    importlib.reload(rvd_mod)
    monkeypatch.setattr(rvd_mod, "find_hoi4_install", lambda: str(tmp_path))

    def broken():
        raise rvd_mod.RefreshError("synthetic failure")

    monkeypatch.setitem(rvd_mod._TARGETS, "defines", broken)

    import sys as _sys

    _sys.argv = ["refresh_vanilla_data.py", "--only", "defines"]
    try:
        rc = rvd_mod.main()
    finally:
        _sys.argv = []

    captured = capsys.readouterr()
    assert rc == 1
    assert "synthetic failure" in captured.err


def test_refresh_defines_writes_manifest(monkeypatch, tmp_manifests):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(
        rvd_mod, "find_vanilla_defines", lambda: str(tmp_manifests / "defs.lua")
    )
    monkeypatch.setattr(
        rvd_mod,
        "parse_vanilla_defines",
        lambda p: {"NGame": {"END_DATE"}, "NEconomy": {"GDP_DEFICIT_FACTOR"}},
    )

    summary = rvd_mod._refresh_defines()
    assert summary.startswith("vanilla_defines.txt:")

    body = (tmp_manifests / "vanilla_defines.txt").read_text(encoding="utf-8")
    assert "NEconomy.GDP_DEFICIT_FACTOR" in body
    assert "NGame.END_DATE" in body


def test_refresh_defines_raises_when_missing(monkeypatch):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "find_vanilla_defines", lambda: None)
    with pytest.raises(rvd_mod.RefreshError, match="defines"):
        rvd_mod._refresh_defines()


def test_refresh_gui_writes_basename_manifest(monkeypatch, tmp_manifests):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_vanilla_gui_files", lambda: ["/x/main.gui", "/y/sub.gui"])
    summary = rvd_mod._refresh_gui()
    assert summary.startswith("vanilla_gui_files.txt:")

    body = (tmp_manifests / "vanilla_gui_files.txt").read_text(encoding="utf-8")
    assert "main.gui" in body
    assert "sub.gui" in body


def test_refresh_gui_raises_when_no_files(monkeypatch):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_vanilla_gui_files", lambda: [])
    with pytest.raises(rvd_mod.RefreshError):
        rvd_mod._refresh_gui()


def test_refresh_sprites_writes_manifest(monkeypatch, tmp_manifests):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_vanilla_gfx_files", lambda: ["/x/events.gfx"])
    monkeypatch.setattr(rvd_mod, "_read_raw", lambda p: "raw content" if "events" in p else None)
    monkeypatch.setattr(
        rvd_mod,
        "sprite_names_from_gfx_text",
        lambda raw: {"GFX_event_test_sprite"},
    )

    summary = rvd_mod._refresh_sprites()
    assert summary.startswith("vanilla_sprites.txt:")

    body = (tmp_manifests / "vanilla_sprites.txt").read_text(encoding="utf-8")
    assert "GFX_event_test_sprite" in body


def test_refresh_sprites_skips_unreadable_gfx(monkeypatch, tmp_manifests):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_vanilla_gfx_files", lambda: ["/x/events.gfx", "/y/bad.gfx"])
    monkeypatch.setattr(rvd_mod, "_read_raw", lambda p: "raw content" if "events" in p else None)
    monkeypatch.setattr(
        rvd_mod,
        "sprite_names_from_gfx_text",
        lambda raw: {"GFX_event_test_sprite"},
    )

    rvd_mod._refresh_sprites()
    body = (tmp_manifests / "vanilla_sprites.txt").read_text(encoding="utf-8")
    assert "GFX_event_test_sprite" in body


def test_refresh_fonts_writes_manifest(monkeypatch, tmp_manifests):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_vanilla_gfx_files", lambda: ["/x/fonts.gfx"])
    monkeypatch.setattr(rvd_mod, "_read_raw", lambda p: "raw content")
    monkeypatch.setattr(
        rvd_mod, "font_names_from_gfx_text", lambda raw: {"TestFont"}
    )

    summary = rvd_mod._refresh_fonts()
    assert summary.startswith("vanilla_fonts.txt:")

    body = (tmp_manifests / "vanilla_fonts.txt").read_text(encoding="utf-8")
    assert "TestFont" in body


def test_refresh_fonts_raises_when_no_gfx_files(monkeypatch):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_vanilla_gfx_files", lambda: [])
    with pytest.raises(rvd_mod.RefreshError):
        rvd_mod._refresh_fonts()


def test_refresh_paths_writes_manifest(monkeypatch, tmp_manifests):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_install", lambda: "/fake/install")
    monkeypatch.setattr(
        "validation.refresh_vanilla_data.collect_vanilla_paths",
        lambda p: {"common/defines", "interface"},
    )

    summary = rvd_mod._refresh_paths()
    assert summary.startswith("vanilla_paths.txt:")

    body = (tmp_manifests / "vanilla_paths.txt").read_text(encoding="utf-8")
    assert "common/defines" in body
    assert "interface" in body


def test_refresh_paths_raises_when_no_paths(monkeypatch):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_install", lambda: "/nope")
    monkeypatch.setattr(
        "validation.refresh_vanilla_data.collect_vanilla_paths", lambda p: set()
    )
    with pytest.raises(rvd_mod.RefreshError):
        rvd_mod._refresh_paths()


def test_refresh_docs_copies_files(monkeypatch, tmp_manifests, tmp_path):
    import validation.refresh_vanilla_data as rvd_mod

    install = tmp_path / "install"
    install.mkdir()
    (install / "new_doc.md").write_text("# New doc\nbody\n", encoding="utf-8")
    monkeypatch.setattr(rvd_mod, "_install", lambda: str(install))
    monkeypatch.setattr(
        "validation.refresh_vanilla_data.glob.glob",
        lambda *a, **k: [str(install / "new_doc.md")],
    )

    preexisting = tmp_manifests / "resources/documentation/new_doc.md"
    preexisting.parent.mkdir(parents=True, exist_ok=True)
    preexisting.write_text("OLD CONTENT\n", encoding="utf-8")

    summary = rvd_mod._refresh_docs()
    assert "files" in summary
    assert "New doc" in preexisting.read_text(encoding="utf-8")


def test_refresh_docs_counts_new(monkeypatch, tmp_manifests, tmp_path):
    import validation.refresh_vanilla_data as rvd_mod

    install = tmp_path / "install"
    install.mkdir()
    (install / "doc1.md").write_text("# Doc1\n", encoding="utf-8")
    monkeypatch.setattr(rvd_mod, "_install", lambda: str(install))
    monkeypatch.setattr(
        "validation.refresh_vanilla_data.glob.glob",
        lambda *a, **k: [str(install / "doc1.md")],
    )

    preexisting = tmp_manifests / "resources/documentation/doc1.md"
    preexisting.parent.mkdir(parents=True, exist_ok=True)
    if preexisting.exists():
        preexisting.unlink()

    summary = rvd_mod._refresh_docs()
    assert "(1 new)" in summary


def test_refresh_docs_raises_when_no_docs(monkeypatch):
    import validation.refresh_vanilla_data as rvd_mod

    monkeypatch.setattr(rvd_mod, "_install", lambda: "/nope")
    monkeypatch.setattr("validation.refresh_vanilla_data.glob.glob", lambda *a, **k: [])
    with pytest.raises(rvd_mod.RefreshError):
        rvd_mod._refresh_docs()


def test_targets_dict_has_expected_keys():
    import validation.refresh_vanilla_data as rvd_mod

    assert set(rvd_mod._TARGETS) == {
        "defines",
        "docs",
        "fonts",
        "gui",
        "paths",
        "sprites",
    }
