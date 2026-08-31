"""Behavior tests for the dynamic-token log sync CLI."""

import os
import sys

import pytest
import sync_dynamic_tokens as sync


def write(path, text):
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def run(monkeypatch, log, output=None):
    argv = ["sync_dynamic_tokens.py", str(log)]
    if output is not None:
        argv += ["-o", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    sync.main()


def test_missing_log_is_an_argparse_error(monkeypatch, tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        run(monkeypatch, tmp_path / "absent.log", tmp_path / "tokens.txt")

    assert exc.value.code == 2
    assert "Log file not found" in capsys.readouterr().err


def test_quiet_log_reports_no_warnings(monkeypatch, tmp_path, capsys):
    log = tmp_path / "error.log"
    write(log, "[game.cpp:1]: something unrelated\n")
    output = tmp_path / "tokens.txt"

    run(monkeypatch, log, output)

    assert "No dynamic-token warnings found" in capsys.readouterr().out
    assert not output.exists()


def test_unparsed_phrase_reports_wording_drift(monkeypatch, tmp_path, capsys):
    log = tmp_path / "error.log"
    write(log, "complained about a dynamic token somewhere\n")

    run(monkeypatch, log, tmp_path / "tokens.txt")

    assert "the log wording may have changed" in capsys.readouterr().out


def test_creates_the_output_file_when_absent(monkeypatch, tmp_path, capsys):
    log = tmp_path / "error.log"
    write(log, "Token MD_alpha is a dynamic token\n")
    output = tmp_path / "nested" / "tokens.txt"
    output.parent.mkdir()

    run(monkeypatch, log, output)

    assert read(output) == "MD_alpha\n"
    assert "Added 1 new token(s)" in capsys.readouterr().out


def test_appends_only_tokens_absent_from_the_file(monkeypatch, tmp_path, capsys):
    log = tmp_path / "error.log"
    write(
        log,
        "Token MD_alpha is a dynamic token\n"
        "unrelated line\n"
        "Token MD_beta is a dynamic token\n"
        "Token MD_alpha is a dynamic token again\n",
    )
    output = tmp_path / "tokens.txt"
    write(output, "MD_alpha\n")

    run(monkeypatch, log, output)

    assert read(output) == "MD_alpha\nMD_beta\n"
    out = capsys.readouterr().out
    assert "Added 1 new token(s)" in out
    assert "MD_beta" in out


def test_separates_appended_tokens_from_an_unterminated_last_line(
    monkeypatch, tmp_path
):
    log = tmp_path / "error.log"
    write(log, "Token MD_beta is a dynamic token\n")
    output = tmp_path / "tokens.txt"
    write(output, "MD_alpha")

    run(monkeypatch, log, output)

    assert read(output) == "MD_alpha\nMD_beta\n"


def test_nothing_to_add_when_every_token_is_present(monkeypatch, tmp_path, capsys):
    log = tmp_path / "error.log"
    write(log, "Token MD_alpha is a dynamic token\n")
    output = tmp_path / "tokens.txt"
    write(output, "  MD_alpha  \n\n")

    run(monkeypatch, log, output)

    assert read(output) == "  MD_alpha  \n\n"
    assert "All 1 tokens already present" in capsys.readouterr().out


def test_default_output_is_the_synchronised_tokens_file():
    expected = os.path.join("common", "synchronized_dynamic_tokens", "MD_tokens.txt")
    assert sync.DEFAULT_OUTPUT.endswith(expected)
