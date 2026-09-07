"""Tests for tools/validate_tools.py (ToolsValidator).

Runs against a synthetic tools/ tree under tmp_path — the validator derives
its scan root from mod_path, so no production files are touched.
"""

import os

import validate_tools as V
from validate_tools import ToolsValidator

_HEALTHY = (
    "#!/usr/bin/env python3\n"
    "def main():\n"
    '    print("ok")\n'
    "\n"
    'if __name__ == "__main__":\n'
    "    main()\n"
)

_BROKEN = (
    "#!/usr/bin/env python3\n"
    "def broken(:\n"
    "    pass\n"
    'if __name__ == "__main__":\n'
    "    pass\n"
)


def _write_script(tmp_path, name, content, mode=0o755):
    tools_dir = tmp_path / "tools"
    path = tools_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)
    return path


def _run(tmp_path):
    validator = ToolsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return validator


def test_healthy_script_passes(tmp_path):
    _write_script(tmp_path, "good_script.py", _HEALTHY)
    validator = _run(tmp_path)
    assert validator.errors_found == 0
    assert not any("Warning:" in line for line in validator.output_lines)


def test_syntax_error_flagged(tmp_path):
    _write_script(tmp_path, "broken_script.py", _BROKEN)
    validator = _run(tmp_path)
    assert validator.errors_found == 1
    assert "broken_script.py" in validator._issues[0].message


def test_index_mode_controls_executable_check(tmp_path, monkeypatch):
    executable = _write_script(tmp_path, "executable.py", _HEALTHY)
    regular = _write_script(tmp_path, "regular.py", _HEALTHY)

    def indexed_files(*args, **kwargs):
        return V.subprocess.CompletedProcess(
            args[0],
            0,
            "100755 hash 0\ttools/executable.py\n100644 hash 0\ttools/regular.py\n",
            "",
        )

    monkeypatch.setattr(V.subprocess, "run", indexed_files)
    validator = ToolsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    indexed = validator._indexed_executable_paths()

    assert indexed == {executable.resolve()}
    assert validator._is_executable(executable, indexed)
    assert not validator._is_executable(regular, indexed)


def test_style_warnings_for_bare_script(tmp_path):
    # No shebang, no main guard, not executable — warnings only, not errors.
    _write_script(tmp_path, "bare_script.py", "x = 1\n", mode=0o644)
    validator = _run(tmp_path)
    assert validator.errors_found == 0
    output = "\n".join(validator.output_lines)
    assert "missing python shebang" in output
    if os.name == "nt":
        assert "not executable" not in output
    else:
        assert "not executable" in output
    assert "no main guard" in output


def test_test_files_and_markers_exempt(tmp_path):
    for name in ("thing_test.py", "test_thing.py", "__init__.py", "conftest.py"):
        _write_script(tmp_path, name, "x = 1\n", mode=0o644)
    validator = _run(tmp_path)
    assert validator.errors_found == 0
    assert not any("Warning:" in line for line in validator.output_lines)


def test_files_under_tests_dir_exempt(tmp_path):
    _write_script(tmp_path, "tests/helper_bits.py", "x = 1\n", mode=0o644)
    validator = _run(tmp_path)
    assert not any("Warning:" in line for line in validator.output_lines)


def test_private_module_exempt(tmp_path):
    _write_script(tmp_path, "_internal.py", "x = 1\n", mode=0o644)
    validator = _run(tmp_path)
    assert not any("Warning:" in line for line in validator.output_lines)


def test_in_package_library_exempt(tmp_path):
    _write_script(tmp_path, "pkg/__init__.py", "", mode=0o644)
    _write_script(tmp_path, "pkg/helper.py", "x = 1\n", mode=0o644)
    validator = _run(tmp_path)
    assert not any("Warning:" in line for line in validator.output_lines)


def test_imported_standalone_library_exempt(tmp_path):
    _write_script(tmp_path, "shared_bits.py", "x = 1\n", mode=0o644)
    _write_script(
        tmp_path, "runner.py", "#!/usr/bin/env python3\nimport shared_bits\n" + _HEALTHY
    )
    validator = _run(tmp_path)
    assert validator.errors_found == 0
    assert not any("Warning:" in line for line in validator.output_lines)


def test_guarded_script_checked_even_when_imported(tmp_path):
    # A main guard means "runnable"; being imported by a test must not exempt it.
    guarded = (
        "#!/usr/bin/env python3\n"
        "def main():\n"
        '    print("ok")\n'
        "\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )
    _write_script(tmp_path, "dual_use.py", guarded, mode=0o644)
    _write_script(
        tmp_path, "runner.py", "#!/usr/bin/env python3\nimport dual_use\n" + _HEALTHY
    )
    validator = _run(tmp_path)
    output = "\n".join(validator.output_lines)
    if os.name == "nt":
        assert "not executable" not in output
    else:
        assert "not executable — dual_use.py" in output
    assert "no main guard or main() — dual_use.py" not in output
    assert "missing python shebang — dual_use.py" not in output


def test_old_directory_excluded(tmp_path):
    old_dir = tmp_path / "tools" / "old"
    old_dir.mkdir(parents=True)
    (old_dir / "legacy_broken.py").write_text(_BROKEN, encoding="utf-8")
    validator = _run(tmp_path)
    assert validator.errors_found == 0


def test_missing_runtime_dependency_reported(tmp_path):
    _write_script(tmp_path, "good_script.py", _HEALTHY)
    (tmp_path / "pyproject.toml").write_text(
        "[dependency-groups]\n"
        "runtime = [\n"
        '    "definitely_not_a_real_package_xyz>=1.0",\n'
        '    "pytest",\n'
        "]\n",
        encoding="utf-8",
    )
    validator = ToolsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    missing = validator._check_dependencies()
    assert missing == ["definitely_not_a_real_package_xyz"]


def test_no_pyproject_means_no_dependency_findings(tmp_path):
    _write_script(tmp_path, "good_script.py", _HEALTHY)
    validator = ToolsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    assert validator._check_dependencies() == []


def test_tools_scan_failure_is_warned(tmp_path, monkeypatch):
    validator = ToolsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)

    def boom(_self, _pattern):
        raise NotADirectoryError("not a directory")

    monkeypatch.setattr(V.Path, "rglob", boom)
    assert validator._find_scripts() == []
    assert "tools directory not found" in "\n".join(validator.output_lines)


def test_unreadable_script_is_reported(tmp_path):
    locked = tmp_path / "tools" / "locked.py"
    locked.parent.mkdir(parents=True, exist_ok=True)
    locked.mkdir()
    validator = _run(tmp_path)
    assert validator.errors_found == 1
    assert "locked.py" in validator._issues[0].message


def test_null_byte_in_source_is_a_parse_error(tmp_path):
    path = tmp_path / "tools" / "nulls.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"#!/usr/bin/env python3\nx = 1\x00\n")
    path.chmod(0o755)
    validator = _run(tmp_path)
    assert validator.errors_found == 1
    assert "nulls.py" in validator._issues[0].message


def test_relative_import_does_not_crash_import_collection(tmp_path):
    _write_script(
        tmp_path,
        "rel.py",
        "#!/usr/bin/env python3\nfrom . import helper\n" + _HEALTHY,
    )
    validator = _run(tmp_path)
    assert validator.errors_found == 0


def test_from_import_is_collected(tmp_path):
    _write_script(
        tmp_path,
        "fromimp.py",
        "#!/usr/bin/env python3\nfrom pathlib import Path\n" + _HEALTHY,
    )
    validator = _run(tmp_path)
    assert validator.errors_found == 0


def test_non_syntax_parse_error_is_reported(tmp_path, monkeypatch):
    _write_script(tmp_path, "ok.py", _HEALTHY)

    def boom(_src, filename=None):
        raise TypeError("bad ast")

    monkeypatch.setattr(V.ast, "parse", boom)
    validator = _run(tmp_path)
    assert validator.errors_found == 1
    assert "bad ast" in validator._issues[0].message


def test_unreadable_pyproject_is_reported(tmp_path):
    _write_script(tmp_path, "good_script.py", _HEALTHY)
    (tmp_path / "pyproject.toml").mkdir()
    validator = ToolsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    missing = validator._check_dependencies()
    assert missing and missing[0].startswith("Error reading pyproject.toml")


def test_pyproject_without_runtime_group_has_no_dependency_findings(tmp_path):
    _write_script(tmp_path, "good_script.py", _HEALTHY)
    (tmp_path / "pyproject.toml").write_text(
        '[dependency-groups]\ndev = ["pytest"]\n', encoding="utf-8"
    )
    validator = ToolsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    assert validator._check_dependencies() == []
