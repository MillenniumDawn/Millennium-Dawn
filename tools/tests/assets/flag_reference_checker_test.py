"""Deterministic tests for tools/assets/flag-reference-checker.py.

Covers the regex flag finder, the directory/file exclusion filter, the scan
pipeline (which counts token occurrences once per file across all detected
flags), and the CLI error paths.
"""

import importlib.util
import io
import sys
from pathlib import Path

import pytest


def _load_asset(name):
    path = Path(__file__).resolve().parents[2] / "assets" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_asset_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


frc = _load_asset("flag-reference-checker")


# --- find_flags -----------------------------------------------------------


def test_find_flags_collects_set_country_flag_and_bare_flag_forms():
    content = (
        "set_country_flag = ABC_one\n"
        "set_country_flag = abc_one\n"  # case-sensitive duplication in scan
        "flag = XYZ_one\n"
        "ignore = not_a_flag\n"
    )
    flags = frc.find_flags(content)
    assert "ABC_one" in flags
    assert "abc_one" in flags
    assert "XYZ_one" in flags
    assert "not_a_flag" not in flags


def test_find_flags_skips_bare_flag_form_without_set_country_flag():
    # Bare `flag = X` is treated as a flag only when set_country_flag appears
    # anywhere in the same content; otherwise it is just a regular assignment.
    content = "flag = ALPHA_only_bare\n"
    flags = frc.find_flags(content)
    assert "ALPHA_only_bare" not in flags


def test_find_flags_returns_set_of_unique_names():
    content = "set_country_flag = X\nset_country_flag = X\n"
    flags = frc.find_flags(content)
    assert flags == {"X"}


# --- should_skip ----------------------------------------------------------


def test_should_skip_rejects_dotfiles_and_yaml_files():
    assert frc.should_skip("/some/place", ".hidden") is True
    # yaml rule needs parent dir to match localisation/localization.
    assert frc.should_skip("/loc", "file.yml") is False
    assert frc.should_skip("/place/localisation", "file.yml") is True
    assert frc.should_skip("/place/gfx/sub", "file.txt") is True


def test_should_skip_directory_match_is_case_insensitive_for_gfx_localisation():
    # The implementation lower-cases path components, so gfx/localisation under
    # capitalised directory names still hit the skip branches.
    assert frc.should_skip("/place/GFX/whatever", "real.txt") is True
    assert frc.should_skip("/place/Localisation/whatever", "real.yml") is True


# --- scan_directory -------------------------------------------------------


def _write(root, name, content):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def test_scan_directory_counts_tokens_per_file_using_one_pass(tmp_path, capsys):
    _write(tmp_path, "events/01_a.txt", "set_country_flag = CHOSEN_ONE\n")
    _write(tmp_path, "events/01_b.txt", "set_country_flag = CHOSEN_ONE\n")
    _write(tmp_path, "events/01_c.txt", "set_country_flag = OTHER\n")

    all_flags, refs = frc.scan_directory(str(tmp_path))

    assert {"CHOSEN_ONE", "OTHER"} <= all_flags
    chosen = refs["CHOSEN_ONE"]
    assert sum(chosen.values()) == 2
    assert str(tmp_path / "events" / "01_a.txt") in chosen
    assert str(tmp_path / "events" / "01_b.txt") in chosen
    assert str(tmp_path / "events" / "01_c.txt") not in chosen

    out = capsys.readouterr().out
    assert "Reading files" in out
    assert "Analyzing flag references" in out


def test_scan_directory_skips_hidden_gfx_and_localisation_directories(tmp_path):
    _write(tmp_path, "events/public.txt", "set_country_flag = KEEP\n")
    _write(tmp_path, ".hidden/skipped.txt", "set_country_flag = DROP\n")
    _write(tmp_path, "gfx/skip.png", "// fake gfx content")
    _write(tmp_path, "localisation/skip.yml", "key: value\n")
    _write(tmp_path, "LOCALIZATION/skip.yml", "key: value\n")

    all_flags, refs = frc.scan_directory(str(tmp_path))

    assert "KEEP" in all_flags
    assert "DROP" not in all_flags
    referenced = {fp for fp in refs.get("KEEP", {})}
    assert any(fp.endswith("events/public.txt") for fp in referenced)
    assert not any(".hidden" in fp for fp in referenced)
    assert not any("localisation" in fp or "LOCALIZATION" in fp for fp in referenced)
    assert not any("/gfx/" in fp for fp in referenced)


def test_scan_directory_ignores_unreadable_files(tmp_path, monkeypatch):
    _write(tmp_path, "events/readable.txt", "set_country_flag = X\n")
    real_open = io.open

    def selective_open(path, *args, **kwargs):
        if "events/readable.txt" not in str(path):
            raise OSError("blocked")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", selective_open)
    all_flags, _refs = frc.scan_directory(str(tmp_path))
    assert "X" in all_flags


# --- CLI / main ----------------------------------------------------------


def test_main_requires_exactly_one_argument(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["flag-reference-checker.py"])
    with pytest.raises(SystemExit) as exit_info:
        frc.main()
    assert exit_info.value.code == 1
    assert "Usage" in capsys.readouterr().out


def test_main_rejects_non_directory_input(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["flag-reference-checker.py", "/no/such/dir/here"])
    with pytest.raises(SystemExit) as exit_info:
        frc.main()
    assert exit_info.value.code == 1
    assert "does not exist" in capsys.readouterr().out


def test_main_reports_unreferenced_flags_sorted_alpha(tmp_path, monkeypatch, capsys):
    _write(tmp_path, "events/files.txt", "set_country_flag = ALPHA\n")
    _write(tmp_path, "events/other.txt", "set_country_flag = ZULU\n")

    monkeypatch.setattr(sys, "argv", ["flag-reference-checker.py", str(tmp_path)])
    frc.main()
    out = capsys.readouterr().out
    assert "Found 2 unique flags" in out
    # The non-referenced flag (one file listing) must appear alphabetically.
    assert out.index("Flag: ALPHA") < out.index("Flag: ZULU")
    assert "Scan complete!" in out
