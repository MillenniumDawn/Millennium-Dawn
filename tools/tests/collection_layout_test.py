"""Guards the unified tools test layout and shared import-root config."""

import re
from pathlib import Path

from shared.paths import (
    PYLINT_PATHS,
    PYTEST_PYTHONPATH,
    REPO_ROOT,
    TOOLS_DIR,
    VALIDATION_DIR,
)


def _pyproject_text():
    return (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")


def _quoted_list(text, key):
    match = re.search(rf"{re.escape(key)}\s*=\s*\[(.*?)\]", text, re.S)
    assert match, f"pyproject.toml has no {key} list"
    return re.findall(r'"([^"]+)"', match.group(1))


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


def test_no_stray_test_modules_outside_tools_tests():
    allowed = (TOOLS_DIR / "tests").resolve()
    stray = sorted(
        p
        for p in TOOLS_DIR.rglob("*_test.py")
        if "__pycache__" not in p.parts and allowed not in p.resolve().parents
    )
    assert stray == [], f"move *_test.py under tools/tests/: {stray}"


def test_no_conventional_test_module_names():
    conventional = sorted(
        path for path in TOOLS_DIR.rglob("test_*.py") if "__pycache__" not in path.parts
    )
    assert conventional == [], (
        "rename conventional test_*.py modules to *_test.py: " f"{conventional}"
    )


def test_pytest_pythonpath_matches_shared_paths(pytestconfig):
    got = {Path(p).resolve() for p in pytestconfig.getini("pythonpath")}
    expected = {
        (REPO_ROOT / rel).resolve() if rel != "." else REPO_ROOT.resolve()
        for rel in PYTEST_PYTHONPATH
    }
    assert got == expected


def test_pyproject_pythonpath_list_matches_shared_paths():
    assert _quoted_list(_pyproject_text(), "pythonpath") == list(PYTEST_PYTHONPATH)


def test_pyright_extra_paths_match_pytest_pythonpath():
    text = _pyproject_text()
    start = text.index("[tool.pyright]")
    chunk = text[start:]
    next_section = re.search(r"\n\[tool\.", chunk[len("[tool.pyright]") :])
    if next_section:
        chunk = chunk[: len("[tool.pyright]") + next_section.start()]
    assert _quoted_list(chunk, "extraPaths") == list(PYTEST_PYTHONPATH)


def test_pylint_init_hook_matches_shared_paths():
    match = re.search(r"sys\.path\.extend\(\[(.*?)\]\)", _pyproject_text(), re.S)
    assert match, "pylint init-hook has no sys.path.extend list"
    listed = re.findall(r"'([^']+)'", match.group(1))
    assert listed == list(PYLINT_PATHS)


def test_validation_dir_is_the_production_package():
    assert VALIDATION_DIR.is_dir()
    assert (VALIDATION_DIR / "validator_common.py").is_file()
    assert (REPO_ROOT / "pyproject.toml").is_file()
