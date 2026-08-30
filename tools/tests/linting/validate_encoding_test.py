import codecs

from validate_localization_encoding import LocalizationValidator
from validate_mod_encoding import validate_mod_file


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
