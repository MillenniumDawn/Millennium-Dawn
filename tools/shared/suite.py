"""Helpers shared by tools/tests. Not imported by production scripts."""

import importlib.util
import io
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.error
from http.client import HTTPMessage
from pathlib import Path
from types import ModuleType


def symlinks_available() -> bool:
    """Whether this process may create a symlink.

    Windows refuses without Developer Mode or admin rights (WinError 1314), so
    symlink-rejection tests skip there instead of failing the whole suite.
    """
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "target"
        target.mkdir()
        try:
            (Path(folder) / "link").symlink_to(target)
        except (OSError, NotImplementedError):
            return False
    return True


def imagemagick_available() -> bool:
    """Whether a real ImageMagick binary is on PATH.

    Windows ships its own `convert.exe` (the FAT-to-NTFS converter), so the
    name alone proves nothing — ask the binary what it is.
    """
    return bool(md_art_convert_binary())


def md_art_convert_binary() -> str | None:
    for exe in ("magick", "convert", "identify"):
        found = shutil.which(exe)
        if found and _is_imagemagick(found):
            return found
    return None


def _is_imagemagick(path: str) -> bool:
    try:
        result = subprocess.run(
            [path, "-version"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return "imagemagick" in (result.stdout + result.stderr).lower()


def run_git(repository, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def initialize_git_repository(repository, *paths):
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "test@example.com")
    run_git(repository, "config", "user.name", "Test User")
    run_git(repository, "config", "diff.renames", "true")
    run_git(repository, "add", *paths)
    run_git(repository, "commit", "-m", "initial")


def collecting_validator(cls):
    """Wrap a Validator so `_report` appends to `.collected` instead of printing."""

    class _Collecting(cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.collected = []
            self.last_severity = None

        def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
            self.collected.extend(results)
            self.last_severity = severity

    return _Collecting


def fake_decisions_validator(*args, **kwargs):
    import validate_decisions as V

    return collecting_validator(V.Validator)(*args, **kwargs)


def decision_factory(body):
    import validate_decisions as V

    return V.DecisionFactory(body, source_basename="X.txt")


def decisions_results_for(factories, monkeypatch, check="validate_missing_log"):
    """Run a `validate_decisions.Validator` check on `factories`; return its results.

    Bound to validate_decisions only — use `collecting_validator` for other validators.
    """
    import validate_decisions as V

    validator = fake_decisions_validator("/tmp")
    # Some checks pass `lowercase=` explicitly, so the stub must accept it.
    monkeypatch.setattr(
        V, "parse_all_decision_factories", lambda mod_path, lowercase=False: factories
    )
    getattr(validator, check)()
    return validator.collected


def issue_dict(severity, file="a.txt", line=1, message="m", category="c"):
    return {
        "severity": severity,
        "category": category,
        "message": message,
        "file": file,
        "line": line,
    }


class _UnreadableHTTPError(urllib.error.HTTPError):
    def read(self, *_args, **_kwargs):
        raise OSError("response stream already consumed")


def http_error(code: int, body: bytes | None = b"denied"):
    error_type = _UnreadableHTTPError if body is None else urllib.error.HTTPError
    return error_type(
        "https://api.github.invalid",
        code,
        "err",
        HTTPMessage(),
        io.BytesIO(body or b""),
    )


def dds_header(
    magic: int,
    flags: int,
    height: int,
    width: int,
    linear_size: int,
    pixel_format: bytes,
    caps: int,
    mip_count: int = 0,
) -> bytes:
    return (
        struct.pack("<8I", magic, 124, flags, height, width, linear_size, 0, mip_count)
        + bytes(44)
        + pixel_format
        + struct.pack("<I", caps)
        + bytes(16)
    )


def load_tool_module(
    relative_path: str, *, module_name: str | None = None, register: bool = False
) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / relative_path
    name = module_name or f"_tool_test_{path.stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    if register:
        sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, content: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return path


def write_under(root: Path, relative_path: str, content: str) -> Path:
    return write_text(root / relative_path, content)


def write_under_str(root: Path, relative_path: str, content: str) -> str:
    return str(write_under(root, relative_path, content))


def read_text(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def write_slug_json(base: Path, slug: str, issues: list) -> None:
    write_text(Path(base) / f"{slug}.json", json.dumps(issues))


def write_log(artifact_dir: Path, slug: str, content: str) -> None:
    write_text(Path(artifact_dir) / f"validation-{slug}.log", content)


def write_sidecar(artifact_dir: Path, slug: str, issues: list) -> None:
    write_text(Path(artifact_dir) / f"validation-{slug}.json", json.dumps(issues))


def make_results_tree(tmp_path: Path, specs: dict) -> Path:
    """Create a validation-results tree matching `specs`.

    `specs` is a dict like:
      {
          "events": {
              "log": "...",
              "issues": [{"severity": "error", ...}],
          },
      }
    """
    root = Path(tmp_path) / "validation-results"
    root.mkdir(parents=True, exist_ok=True)
    for slug, data in specs.items():
        sub = root / f"validation-{slug}-results"
        sub.mkdir(parents=True, exist_ok=True)
        if "log" in data:
            write_log(sub, slug, data["log"])
        if "issues" in data:
            write_sidecar(sub, slug, data["issues"])
    return root
