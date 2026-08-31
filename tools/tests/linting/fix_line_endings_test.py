"""Behavioral tests for tools/linting/fix_line_endings.py."""

import importlib
import sys
from pathlib import Path

_FIX = importlib.import_module("fix_line_endings")
_CLI = Path(__file__).resolve().parents[2] / "linting" / "fix_line_endings.py"


def _run_cli(*args):
    import subprocess

    return subprocess.run(
        [sys.executable, str(_CLI), *args],
        capture_output=True,
        text=True,
    )


def test_returns_false_when_already_lf(tmp_path):
    f = tmp_path / "ok.txt"
    f.write_bytes(b"line one\nline two\n")

    assert _FIX.fix_line_endings(f) is False
    assert f.read_bytes() == b"line one\nline two\n"


def test_converts_crlf_to_lf(tmp_path):
    f = tmp_path / "mixed.txt"
    f.write_bytes(b"line one\r\nline two\r\nline three\r\n")

    assert _FIX.fix_line_endings(f) is True
    assert f.read_bytes() == b"line one\nline two\nline three\n"


def test_returns_false_for_missing_path(tmp_path, capsys):
    target = tmp_path / "does_not_exist.txt"

    assert _FIX.fix_line_endings(target) is False
    captured = capsys.readouterr()
    assert "Not a file" in captured.out


def test_returns_false_for_directory(tmp_path, capsys):
    assert _FIX.fix_line_endings(tmp_path) is False
    captured = capsys.readouterr()
    assert "Not a file" in captured.out


def test_handles_internal_cr_without_lf(tmp_path):
    f = tmp_path / "lone_cr.txt"
    f.write_bytes(b"alpha\rbeta\ngamma\n")

    # Lone CR (not CRLF) is left alone -- only the explicit `\r\n`
    # sequence is rewritten.
    assert _FIX.fix_line_endings(f) is False
    assert f.read_bytes() == b"alpha\rbeta\ngamma\n"


def test_handles_binary_blob_with_some_crlf(tmp_path):
    f = tmp_path / "binary.txt"
    f.write_bytes(b"\x00\x01\r\nbinary\r\ntrailing")

    assert _FIX.fix_line_endings(f) is True
    assert f.read_bytes() == b"\x00\x01\nbinary\ntrailing"


def test_returns_false_when_read_fails(tmp_path, monkeypatch):
    f = tmp_path / "broken.txt"
    f.write_bytes(b"hello\r\n")

    def boom(*args, **kwargs):
        raise OSError("synthetic read failure")

    monkeypatch.setattr("builtins.open", boom)
    assert _FIX.fix_line_endings(f) is False


def test_main_returns_one_with_no_args():
    monkey_argv = sys.argv[:]
    sys.argv = [str(_CLI)]
    try:
        rc = _FIX.main()
        assert rc == 1
    finally:
        sys.argv = monkey_argv


def test_main_returns_zero_when_all_clean(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"alpha\nbeta\n")
    b.write_bytes(b"gamma\n")

    monkey_argv = sys.argv[:]
    sys.argv = [str(_CLI), str(a), str(b)]
    try:
        rc = _FIX.main()
        assert rc == 0
    finally:
        sys.argv = monkey_argv


def test_main_returns_zero_when_files_fixed(tmp_path):
    a = tmp_path / "a.txt"
    a.write_bytes(b"alpha\r\nbeta\r\n")
    b = tmp_path / "b.txt"
    b.write_bytes(b"gamma\ndelta\n")

    monkey_argv = sys.argv[:]
    sys.argv = [str(_CLI), str(a), str(b)]
    try:
        rc = _FIX.main()
        assert rc == 0
    finally:
        sys.argv = monkey_argv

    assert a.read_bytes() == b"alpha\nbeta\n"
    # Summary path taken when len(files) > 1.
    assert b.read_bytes() == b"gamma\ndelta\n"


def test_main_returns_one_when_file_missing(tmp_path):
    missing = tmp_path / "missing.txt"

    monkey_argv = sys.argv[:]
    sys.argv = [str(_CLI), str(missing)]
    try:
        rc = _FIX.main()
        assert rc == 0  # Missing files are skipped, not counted as errors.
    finally:
        sys.argv = monkey_argv


def test_main_returns_one_when_fix_raises(tmp_path, monkeypatch):
    a = tmp_path / "a.txt"
    a.write_bytes(b"line\r\n")
    b = tmp_path / "b.txt"
    b.write_bytes(b"line\r\n")

    def boom(path):
        raise RuntimeError("synthetic failure inside fix")

    monkeypatch.setattr(_FIX, "fix_line_endings", boom)

    monkey_argv = sys.argv[:]
    sys.argv = [str(_CLI), str(a), str(b)]
    try:
        rc = _FIX.main()
        assert rc == 1
    finally:
        sys.argv = monkey_argv


def test_cli_invocation_runs(tmp_path):
    target = tmp_path / "cli.txt"
    target.write_bytes(b"a\r\nb\r\n")

    result = _run_cli(str(target))
    assert result.returncode == 0
    assert target.read_bytes() == b"a\nb\n"
    assert "Fixed mixed line endings" in result.stdout


def test_cli_invocation_already_lf(tmp_path):
    target = tmp_path / "cli_lf.txt"
    target.write_bytes(b"a\nb\n")

    result = _run_cli(str(target))
    assert result.returncode == 0
    assert "Already has Unix" in result.stdout


def test_cli_invocation_no_args(tmp_path):
    result = _run_cli()
    assert result.returncode == 1
    assert "No files provided" in result.stderr
