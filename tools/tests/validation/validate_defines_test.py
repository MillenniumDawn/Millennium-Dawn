"""Tests for validate_defines.py — MD_defines.lua vs vanilla 00_defines.lua.

The vanilla file is not in the repo and this validator is CI-exempt (the CI
runner has no HOI4 install), so these fixture-driven tests are its only
automated gate. Fixtures supply a tiny fake vanilla defines file via the
validator's ``vanilla_path`` injection point.
"""

from validate_defines import Validator, parse_md_defines, parse_vanilla_defines

_VANILLA = """NDefines = {
\tNCountry = {
\t\tSTARTING_COMMAND_POWER = 10,
\t\tMAX_COMMAND_POWER = 200, -- inline comment
\t},
\tNAI = {
\t\tDIVISION_DESIRED_WIDTH = 20,
\t},
}
"""


def _write_vanilla(tmp_path):
    path = tmp_path / "00_defines.lua"
    path.write_text(_VANILLA, encoding="utf-8")
    return str(path)


def _write_md_defines(tmp_path, body):
    defines_dir = tmp_path / "common" / "defines"
    defines_dir.mkdir(parents=True)
    (defines_dir / "MD_defines.lua").write_text(body, encoding="utf-8")


def _run(tmp_path, md_body):
    vanilla = _write_vanilla(tmp_path)
    _write_md_defines(tmp_path, md_body)
    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, vanilla_path=vanilla
    )
    validator.run_validations()
    return validator


def test_parse_vanilla_defines_extracts_namespaced_names(tmp_path):
    namespaces = parse_vanilla_defines(_write_vanilla(tmp_path))
    assert "STARTING_COMMAND_POWER" in namespaces["NCountry"]
    assert "MAX_COMMAND_POWER" in namespaces["NCountry"]
    assert "DIVISION_DESIRED_WIDTH" in namespaces["NAI"]
    assert "DIVISION_DESIRED_WIDTH" not in namespaces["NCountry"]


def test_parse_md_defines_skips_comments(tmp_path):
    _write_md_defines(
        tmp_path,
        "-- header comment\n"
        "NDefines.NCountry.STARTING_COMMAND_POWER = 25 -- trailing\n",
    )
    md_path = tmp_path / "common" / "defines" / "MD_defines.lua"
    results = parse_md_defines(str(md_path))
    assert len(results) == 1
    namespace, name, line_num, _full = results[0]
    assert (namespace, name, line_num) == ("NCountry", "STARTING_COMMAND_POWER", 2)


def test_clean_defines_pass(tmp_path):
    validator = _run(
        tmp_path,
        "NDefines.NCountry.STARTING_COMMAND_POWER = 25\n"
        "NDefines.NAI.DIVISION_DESIRED_WIDTH = 30\n",
    )
    assert validator.errors_found == 0
    assert validator._issues == []


def test_dead_define_flagged_with_suggestion(tmp_path):
    validator = _run(tmp_path, "NDefines.NCountry.MAX_COMAND_POWER = 500\n")
    assert validator.errors_found == 1
    message = validator._issues[0].message
    assert "MAX_COMAND_POWER does not exist in vanilla" in message
    assert "did you mean 'MAX_COMMAND_POWER'" in message


def test_wrong_namespace_flagged(tmp_path):
    validator = _run(tmp_path, "NDefines.NAI.STARTING_COMMAND_POWER = 5\n")
    assert validator.errors_found == 1
    message = validator._issues[0].message
    assert "wrong namespace" in message
    assert "NCountry" in message


def test_duplicate_define_flagged(tmp_path):
    validator = _run(
        tmp_path,
        "NDefines.NCountry.MAX_COMMAND_POWER = 300\n"
        "NDefines.NCountry.MAX_COMMAND_POWER = 400\n",
    )
    assert validator.errors_found == 1
    message = validator._issues[0].message
    assert "duplicate NCountry.MAX_COMMAND_POWER" in message
    assert "first defined at line 1" in message


def test_missing_md_defines_is_setup_error(tmp_path):
    vanilla = _write_vanilla(tmp_path)
    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, vanilla_path=vanilla
    )
    validator.run_validations()
    assert validator.errors_found == 1
    assert validator._issues[0].category == "defines-setup"


def test_manifest_fallback_when_no_install(tmp_path, monkeypatch):
    import validate_defines as vd

    manifest = tmp_path / "vanilla_defines.txt"
    manifest.write_text(
        "# header\nNCountry.STARTING_COMMAND_POWER\nNAI.DIVISION_DESIRED_WIDTH\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(vd, "_DEFINES_MANIFEST", str(manifest))
    monkeypatch.setattr(vd, "find_vanilla_defines", lambda: None)
    _write_md_defines(tmp_path, "NDefines.NAI.DIVISION_DESIRED_WIDTH = 25\n")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    assert validator.errors_found == 0


def test_manifest_fallback_flags_dead_define(tmp_path, monkeypatch):
    import validate_defines as vd

    manifest = tmp_path / "vanilla_defines.txt"
    manifest.write_text("NCountry.STARTING_COMMAND_POWER\n", encoding="utf-8")
    monkeypatch.setattr(vd, "_DEFINES_MANIFEST", str(manifest))
    monkeypatch.setattr(vd, "find_vanilla_defines", lambda: None)
    _write_md_defines(tmp_path, "NDefines.NCountry.NOT_A_REAL_DEFINE = 1\n")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    assert validator.errors_found == 1


def test_corrupt_manifest_reads_as_absent(tmp_path, monkeypatch):
    import validate_defines as vd

    manifest = tmp_path / "vanilla_defines.txt"
    manifest.write_bytes(b"\xff\xfe\x00 not utf-8 \x80")
    monkeypatch.setattr(vd, "_DEFINES_MANIFEST", str(manifest))
    assert vd.load_defines_manifest() == {}


def test_explicit_wrong_vanilla_path_is_setup_error(tmp_path):
    _write_md_defines(tmp_path, "NDefines.NCountry.STARTING_COMMAND_POWER = 5\n")
    validator = Validator(
        mod_path=str(tmp_path),
        use_colors=False,
        workers=1,
        vanilla_path=str(tmp_path / "does_not_exist.lua"),
    )
    validator.run_validations()
    assert validator.errors_found == 1
