"""Tests for tools/validate_tools.py (ToolsValidator).

Runs against a synthetic tools/ tree under tmp_path — the validator derives
its scan root from mod_path, so no production files are touched.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from validate_tools import ToolsValidator  # noqa: E402

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
    tools_dir.mkdir(exist_ok=True)
    path = tools_dir / name
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


def test_style_warnings_for_bare_script(tmp_path):
    # No shebang, no main guard, not executable — warnings only, not errors.
    _write_script(tmp_path, "bare_script.py", "x = 1\n", mode=0o644)
    validator = _run(tmp_path)
    assert validator.errors_found == 0
    output = "\n".join(validator.output_lines)
    assert "missing python shebang" in output
    assert "not executable" in output
    assert "no main guard" in output


def test_library_modules_exempt_from_style_checks(tmp_path):
    _write_script(tmp_path, "shared_utils.py", "x = 1\n", mode=0o644)
    validator = _run(tmp_path)
    assert validator.errors_found == 0
    assert not any("Warning:" in line for line in validator.output_lines)


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
