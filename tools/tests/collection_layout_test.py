"""Guards the unified tools test layout.

A revived `tools/<domain>/tests/` directory is silently uncollected because
`testpaths` is only `tools/tests`. Fail here instead of in CI mystery.
"""

from pathlib import Path

from shared.paths import REPO_ROOT, TOOLS_DIR, VALIDATION_DIR


def test_testpaths_is_tools_tests(pytestconfig):
    assert pytestconfig.getini("testpaths") == ["tools/tests"]


def test_python_files_are_star_test_py(pytestconfig):
    assert pytestconfig.getini("python_files") == ["*_test.py"]


def test_no_nested_tests_dirs_outside_tools_tests():
    allowed = (TOOLS_DIR / "tests").resolve()
    stray = sorted(
        p
        for p in TOOLS_DIR.rglob("tests")
        if p.is_dir()
        and p.resolve() != allowed
        and "__pycache__" not in p.parts
        and allowed not in p.resolve().parents
    )
    assert stray == [], f"move nested tests under tools/tests/: {stray}"


def test_pythonpath_includes_tools_and_validation(pytestconfig):
    names = {Path(p).name for p in pytestconfig.getini("pythonpath")}
    assert "tools" in names
    assert "validation" in names


def test_validation_dir_is_the_production_package():
    assert VALIDATION_DIR.is_dir()
    assert (VALIDATION_DIR / "validator_common.py").is_file()
    assert (REPO_ROOT / "pyproject.toml").is_file()
