import codecs
import runpy
import sys

import pytest
import validate_localization_encoding as loc_encoding
import validate_mod_encoding as mod_encoding
from validate_localization_encoding import (
    LocalizationValidator,
    find_english_localization_files,
)
from validate_mod_encoding import validate_mod_file


def _run_main(module, monkeypatch, *argv):
    monkeypatch.setattr(module.sys, "argv", [module.__name__, *argv])
    return module.main()


def _run_as_script(module, monkeypatch, *argv):
    """Execute the module the way the pre-commit hook does, under __main__."""
    monkeypatch.setattr(sys, "argv", [module.__file__, *argv])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(module.__file__, run_name="__main__")
    return excinfo.value.code


def test_localisation_encoding_accepts_one_bom(tmp_path):
    path = tmp_path / "ok.yml"
    path.write_bytes(codecs.BOM_UTF8 + 'l_english:\n café: "ok"\n'.encode())
    assert LocalizationValidator().validate_file(path)


def test_localisation_encoding_repairs_missing_bom_idempotently(tmp_path):
    path = tmp_path / "missing.yml"
    path.write_bytes(b"l_english:\n")
    validator = LocalizationValidator(fix_mode=True)
    assert validator.validate_file(path)
    first = path.read_bytes()
    assert first.startswith(codecs.BOM_UTF8)
    assert LocalizationValidator(fix_mode=True).validate_file(path)
    assert path.read_bytes() == first


def test_localisation_encoding_repairs_duplicate_bom(tmp_path):
    path = tmp_path / "duplicate.yml"
    path.write_bytes(codecs.BOM_UTF8 * 2 + b"l_english:\n")
    assert not LocalizationValidator().validate_file(path)
    assert LocalizationValidator(fix_mode=True).validate_file(path)
    assert path.read_bytes().count(codecs.BOM_UTF8) == 1


def test_localisation_encoding_does_not_rewrite_malformed_utf8(tmp_path):
    path = tmp_path / "bad.yml"
    original = b"l_english:\n bad: \xff\n"
    path.write_bytes(original)
    assert not LocalizationValidator(fix_mode=True).validate_file(path)
    assert path.read_bytes() == original


def test_mod_encoding_accepts_non_ascii_utf8_and_rejects_malformed(tmp_path):
    valid = tmp_path / "valid.mod"
    invalid = tmp_path / "invalid.mod"
    valid.write_bytes('name="Café"\n'.encode())
    invalid.write_bytes(b'name="\xff"\n')
    assert validate_mod_file(valid)
    assert not validate_mod_file(invalid)


def test_localisation_encoding_reports_missing_bom_without_fix_mode(tmp_path):
    path = tmp_path / "missing.yml"
    path.write_bytes(b"l_english:\n")
    validator = LocalizationValidator()

    assert not validator.validate_file(path)

    assert any("Missing UTF-8 BOM" in msg for msg in validator.errors)
    assert path.read_bytes() == b"l_english:\n"


def test_localisation_encoding_reports_duplicate_bom_distinctly(tmp_path):
    path = tmp_path / "duplicate.yml"
    path.write_bytes(codecs.BOM_UTF8 * 2 + b"l_english:\n")
    validator = LocalizationValidator()

    validator.validate_file(path)

    assert any("Duplicate UTF-8 BOM" in msg for msg in validator.errors)


def test_localisation_encoding_flags_bad_bytes_behind_a_valid_bom(tmp_path):
    path = tmp_path / "bommed_but_broken.yml"
    path.write_bytes(codecs.BOM_UTF8 + b'l_english:\n KEY: "\xff"\n')
    validator = LocalizationValidator()

    assert not validator.validate_file(path)

    assert any("Invalid UTF-8 encoding" in msg for msg in validator.errors)
    assert not validator.valid


def test_localisation_encoding_reports_unreadable_path_as_error(tmp_path):
    directory = tmp_path / "not_a_file.yml"
    directory.mkdir()
    validator = LocalizationValidator()

    assert not validator.validate_file(directory)

    assert any("Unexpected error" in msg for msg in validator.errors)


def test_localisation_encoding_reports_a_failed_write(tmp_path, monkeypatch):
    path = tmp_path / "missing.yml"
    path.write_bytes(b"l_english:\n")

    def _boom(_filename, _data):
        raise OSError("disk full")

    monkeypatch.setattr(loc_encoding, "atomic_write_bytes", _boom)
    validator = LocalizationValidator(fix_mode=True)

    assert not validator.validate_file(path)

    assert any("Error while fixing" in msg for msg in validator.errors)
    assert path.read_bytes() == b"l_english:\n"


def test_localisation_encoding_validate_files_reports_absent_paths(tmp_path):
    good = tmp_path / "good.yml"
    good.write_bytes(codecs.BOM_UTF8 + b"l_english:\n")
    validator = LocalizationValidator()

    assert not validator.validate_files([good, tmp_path / "gone.yml"])

    assert validator.valid
    assert any("File not found" in msg for msg in validator.errors)


def test_localisation_encoding_summary_only_when_several_results(tmp_path, capsys):
    single = LocalizationValidator()
    single.valid.append("one.yml: ok")
    single.print_summary()
    assert "Summary:" not in capsys.readouterr().out

    several = LocalizationValidator()
    several.valid.append("one.yml: ok")
    several.fixed.append("two.yml: fixed")
    several.errors.append("three.yml: broken")
    several.print_summary()

    captured = capsys.readouterr()
    assert "Summary: 1 valid, 1 fixed, 1 errors" in captured.out
    assert "three.yml: broken" in captured.err


def test_find_english_localization_files_covers_every_pattern(tmp_path, monkeypatch):
    nested = tmp_path / "localisation" / "english" / "sub"
    nested.mkdir(parents=True)
    (tmp_path / "localisation" / "english" / "a.yml").write_bytes(b"")
    (nested / "b.yml").write_bytes(b"")
    (tmp_path / "localisation" / "c_l_english.yml").write_bytes(b"")
    (tmp_path / "localisation" / "english" / "skipped.txt").write_bytes(b"")
    monkeypatch.chdir(tmp_path)

    found = [
        p.relative_to(tmp_path).as_posix() for p in find_english_localization_files()
    ]

    assert found == [
        "localisation/c_l_english.yml",
        "localisation/english/a.yml",
        "localisation/english/sub/b.yml",
    ]


def test_localisation_encoding_main_fixes_the_files_it_is_given(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "missing.yml"
    path.write_bytes(b"l_english:\n")

    assert _run_main(loc_encoding, monkeypatch, "--fix", str(path)) == 0

    assert path.read_bytes() == codecs.BOM_UTF8 + b"l_english:\n"
    assert "Normalized UTF-8 BOM" in capsys.readouterr().out


def test_localisation_encoding_main_exits_nonzero_on_an_error(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "missing.yml"
    path.write_bytes(b"l_english:\n")

    assert _run_main(loc_encoding, monkeypatch, str(path)) == 1

    assert "Missing UTF-8 BOM" in capsys.readouterr().err


def test_localisation_encoding_main_defaults_to_the_project_files(
    tmp_path, monkeypatch, capsys
):
    english = tmp_path / "localisation" / "english"
    english.mkdir(parents=True)
    (english / "a.yml").write_bytes(codecs.BOM_UTF8 + b"l_english:\n")
    monkeypatch.chdir(tmp_path)

    assert _run_main(loc_encoding, monkeypatch) == 0

    assert "Correct UTF-8 with BOM encoding" in capsys.readouterr().out


def test_localisation_encoding_main_reports_an_empty_project(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)

    assert _run_main(loc_encoding, monkeypatch) == 1

    assert "No English localization files found" in capsys.readouterr().err


def test_mod_encoding_announces_a_valid_file(tmp_path, capsys):
    path = tmp_path / "descriptor.mod"
    path.write_bytes(b'name="Millennium Dawn"\n')

    assert validate_mod_file(path)

    assert "Valid UTF-8 encoding" in capsys.readouterr().out


def test_mod_encoding_reports_a_missing_file(tmp_path, capsys):
    assert not validate_mod_file(tmp_path / "gone.mod")

    assert "File not found" in capsys.readouterr().err


def test_mod_encoding_reports_an_unreadable_path(tmp_path, capsys):
    directory = tmp_path / "descriptor.mod"
    directory.mkdir()

    assert not validate_mod_file(directory)

    assert "Unexpected error" in capsys.readouterr().err


def test_mod_encoding_main_requires_a_file(monkeypatch, capsys):
    assert _run_main(mod_encoding, monkeypatch) == 1

    assert "No files provided" in capsys.readouterr().err


def test_mod_encoding_main_stays_quiet_about_a_single_file(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "descriptor.mod"
    path.write_bytes(b'name="Millennium Dawn"\n')

    assert _run_main(mod_encoding, monkeypatch, str(path)) == 0

    assert "Summary:" not in capsys.readouterr().out


def test_mod_encoding_main_summarises_a_mixed_batch(tmp_path, monkeypatch, capsys):
    good = tmp_path / "good.mod"
    bad = tmp_path / "bad.mod"
    good.write_bytes(b'name="ok"\n')
    bad.write_bytes(b'name="\xff"\n')

    assert _run_main(mod_encoding, monkeypatch, str(good), str(bad)) == 1

    assert "Summary: 1 valid, 1 errors" in capsys.readouterr().out


def test_mod_encoding_script_exit_code_follows_the_findings(tmp_path, monkeypatch):
    bad = tmp_path / "bad.mod"
    bad.write_bytes(b'name="\xff"\n')
    good = tmp_path / "good.mod"
    good.write_bytes(b'name="ok"\n')

    assert _run_as_script(mod_encoding, monkeypatch, str(bad)) == 1
    assert _run_as_script(mod_encoding, monkeypatch, str(good)) == 0


def test_localisation_encoding_script_exit_code_follows_the_findings(
    tmp_path, monkeypatch
):
    bad = tmp_path / "missing.yml"
    bad.write_bytes(b"l_english:\n")

    assert _run_as_script(loc_encoding, monkeypatch, str(bad)) == 1
    assert _run_as_script(loc_encoding, monkeypatch, "--fix", str(bad)) == 0


@pytest.mark.parametrize("argv", [["--fix"], []])
def test_localisation_encoding_main_leaves_valid_files_alone(
    tmp_path, monkeypatch, argv
):
    path = tmp_path / "ok.yml"
    original = codecs.BOM_UTF8 + b'l_english:\n KEY: "value"\n'
    path.write_bytes(original)

    assert _run_main(loc_encoding, monkeypatch, *argv, str(path)) == 0

    assert path.read_bytes() == original
