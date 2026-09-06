"""Run-loop tests for run_validator_batch without content scans."""

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import run_validator_batch as rvb
from impact_report import safe_extract
from report_lib import load_all
from validator_batches import ValidatorSpec


class _Process:
    def __init__(self, returncode=0):
        self.returncode = returncode

    def wait(self):
        return self.returncode


def _spec(name, script="validate_stub.py", strict=True):
    return ValidatorSpec(name=name, script=script, groups=("common",), strict=strict)


class _Args:
    def __init__(self, output_dir):
        self.output_dir = str(output_dir)
        self.path = "."
        self.batch = "core"


def _launcher(tmp_path, behaviors):
    """Build a launch_validator stub from {name: (returncode, log, json)}."""

    def launch(script, flags, output_dir, name, mod_path, **_kwargs):
        returncode, log, issues = behaviors[name]
        if log is not None:
            (tmp_path / f"{name}.log").write_text(log, encoding="utf-8")
        if issues is not None:
            (tmp_path / f"{name}.json").write_text(json.dumps(issues), encoding="utf-8")
        assert "--workers" in flags
        return _Process(returncode), _FakeStream()

    return launch


def _patch_runner(tmp_path, monkeypatch, behaviors, parallel):
    monkeypatch.setattr(
        rvb.run_all_validators, "launch_validator", _launcher(tmp_path, behaviors)
    )
    monkeypatch.setattr(rvb, "split_cpu_budget", lambda tasks: (parallel, 1))


class _FakeStream:
    def close(self):
        pass


_current_specs = []


def test_parse_changed_groups_empty_means_all():
    assert rvb.parse_changed_groups("") is None
    assert rvb.parse_changed_groups("  ") is None


def test_parse_changed_groups_splits_spaces_and_commas():
    assert rvb.parse_changed_groups("common, events  history") == {
        "common",
        "events",
        "history",
    }


def test_clean_batch_passes(tmp_path, monkeypatch):
    behaviors = {"validation-events": (0, "log", [])}
    _current_specs[:] = [_spec("events")]
    _patch_runner(tmp_path, monkeypatch, behaviors, 1)

    assert rvb.run_batch([_spec("events")], _Args(tmp_path)) == 0


def test_crash_fails_but_remaining_validators_still_run(tmp_path, monkeypatch, capsys):
    behaviors = {
        "validation-events": (2, None, None),
        "validation-variables": (0, "log", []),
    }
    _current_specs[:] = [_spec("events"), _spec("variables")]
    _patch_runner(tmp_path, monkeypatch, behaviors, 2)

    code = rvb.run_batch([_spec("events"), _spec("variables")], _Args(tmp_path))

    assert code == 1
    out = capsys.readouterr().out
    assert "FAILED events" in out
    assert "OK variables" in out
    assert "1 of 2 validator(s) failed: events" in out


def test_strict_findings_fail_and_non_strict_findings_pass(tmp_path, monkeypatch):
    finding = [{"severity": "error", "category": "c", "message": "m"}]
    behaviors = {
        "validation-gated": (1, "log", finding),
        "validation-advisory": (0, "log", finding),
    }
    _current_specs[:] = [_spec("gated"), _spec("advisory", strict=False)]
    _patch_runner(tmp_path, monkeypatch, behaviors, 2)

    code = rvb.run_batch(
        [_spec("gated"), _spec("advisory", strict=False)], _Args(tmp_path)
    )

    assert code == 1
    assert (tmp_path / "validation-advisory.json").is_file()


def test_missing_result_files_fail_the_run(tmp_path, monkeypatch, capsys):
    # A validator that exits 0 without writing its log and sidecar produced
    # no verdict — the workflow's old `test -f` step, now enforced here.
    behaviors = {"validation-events": (0, None, None)}
    _current_specs[:] = [_spec("events")]
    _patch_runner(tmp_path, monkeypatch, behaviors, 1)

    code = rvb.run_batch([_spec("events")], _Args(tmp_path))

    assert code == 1
    assert "missing" in capsys.readouterr().out


def test_concurrency_stays_bounded(tmp_path, monkeypatch):
    live = []
    peak = []

    def launch(_script, flags, _output_dir, name, _mod_path, **_kwargs):
        live.append(name)
        peak.append(len(live))
        (tmp_path / f"{name}.log").write_text("log", encoding="utf-8")
        (tmp_path / f"{name}.json").write_text("[]", encoding="utf-8")

        class _Tracked(_Process):
            def wait(self):
                live.remove(name)
                return 0

        return _Tracked(), _FakeStream()

    specs = [_spec(f"v{i}") for i in range(6)]
    _current_specs[:] = specs
    monkeypatch.setattr(rvb.run_all_validators, "launch_validator", launch)
    monkeypatch.setattr(rvb, "split_cpu_budget", lambda tasks: (2, 3))

    assert rvb.run_batch(specs, _Args(tmp_path)) == 0
    assert max(peak) == 2


STUB_VALIDATOR = """
import json
import os
import sys

args = sys.argv[1:]
out = args[args.index('--output') + 1]
issues = json.loads(os.environ.get('STUB_ISSUES', '[]'))
with open(out, 'w', encoding='utf-8') as handle:
    handle.write('stub log\\n')
with open(os.path.splitext(out)[0] + '.json', 'w', encoding='utf-8') as handle:
    json.dump(issues, handle)
sys.stderr.write(os.environ.get('STUB_STDERR', ''))
sys.exit(int(os.environ.get('STUB_EXIT', '0')))
"""


def _install_stub_runner(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "validate_stub.py").write_text(STUB_VALIDATOR, encoding="utf-8")
    monkeypatch.setattr(rvb.run_all_validators, "SCRIPTS_DIR", str(scripts))
    monkeypatch.setattr(rvb, "split_cpu_budget", lambda tasks: (2, 1))


def test_real_subprocess_launch_honors_output_names_and_exit_codes(
    tmp_path, monkeypatch
):
    """Integration: launch_validator uses batch output naming."""
    _install_stub_runner(tmp_path, monkeypatch)

    out_dir = tmp_path / "results"
    args = _Args(out_dir)
    args.path = str(tmp_path)

    # Clean run: rc 0, both files written.
    assert rvb.run_batch([_spec("stub")], args) == 0
    assert (out_dir / "validation-stub.log").is_file()
    assert (out_dir / "validation-stub.json").is_file()

    # Strict findings: sidecar reports an error, validator exits 1.
    monkeypatch.setenv("STUB_ISSUES", '[{"severity": "error"}]')
    monkeypatch.setenv("STUB_EXIT", "1")
    (out_dir / "validation-stub.log").unlink()
    (out_dir / "validation-stub.json").unlink()
    assert rvb.run_batch([_spec("stub")], args) == 1

    # Crash: non-zero exit with no sidecar at all.
    monkeypatch.setenv("STUB_ISSUES", "[]")
    monkeypatch.setenv("STUB_EXIT", "3")
    (out_dir / "validation-stub.log").unlink()
    (out_dir / "validation-stub.json").unlink()
    assert rvb.run_batch([_spec("stub")], args) == 1


def test_batch_selection_passes_strict_only_for_gated_specs(tmp_path, monkeypatch):
    strict_flags = []

    def launch(_script, flags, _output_dir, name, _mod_path, **_kwargs):
        strict_flags.append((name, "--strict" in flags))
        (tmp_path / f"{name}.log").write_text("log", encoding="utf-8")
        (tmp_path / f"{name}.json").write_text("[]", encoding="utf-8")
        return _Process(0), _FakeStream()

    specs = [_spec("gated"), _spec("advisory", strict=False)]
    _current_specs[:] = specs
    monkeypatch.setattr(rvb.run_all_validators, "launch_validator", launch)
    monkeypatch.setattr(rvb, "split_cpu_budget", lambda tasks: (2, 1))

    assert rvb.run_batch(specs, _Args(tmp_path)) == 0
    assert dict(strict_flags) == {
        "validation-gated": True,
        "validation-advisory": False,
    }


def test_main_impact_selects_by_changed_files(tmp_path, monkeypatch, capsys):
    list_file = tmp_path / "changed.txt"
    list_file.write_text(
        "tools/validation/validate_events.py\ntools/tests/whatever_test.py\n",
        encoding="utf-8",
    )
    ran = []

    def run_batch(specs, _args):
        ran.append([spec.name for spec in specs])
        return 0

    monkeypatch.setattr(rvb, "run_batch", run_batch)
    out_dir = tmp_path / "out"

    code = rvb.main(
        [
            "--impact",
            "--changed-files-file",
            str(list_file),
            "--output-dir",
            str(out_dir),
        ]
    )

    assert code == 0
    assert ran == [["events"]]


def test_main_impact_forces_the_disk_cache_off(tmp_path, monkeypatch):
    list_file = tmp_path / "changed.txt"
    list_file.write_text("tools/tests/whatever_test.py\n", encoding="utf-8")
    monkeypatch.setattr(rvb, "run_batch", lambda specs, _args: 0)
    monkeypatch.delenv("MD_NO_CACHE", raising=False)

    rvb.main(
        [
            "--impact",
            "--changed-files-file",
            str(list_file),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert rvb.os.environ.get("MD_NO_CACHE") == "1"


def test_main_impact_without_a_file_list_is_an_error(tmp_path, capsys):
    with pytest.raises(SystemExit):
        rvb.main(["--impact", "--output-dir", str(tmp_path / "out")])


def test_main_batch_with_no_selection_does_nothing(tmp_path, monkeypatch):
    ran = []
    monkeypatch.setattr(rvb, "run_batch", lambda specs, _args: ran.append(specs))

    code = rvb.main(
        [
            "--batch",
            "core",
            "--changed-groups",
            "factions",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert code == 0
    assert ran == []


def test_manifest_records_selection_and_execution_outcomes(
    tmp_path, monkeypatch, capsys
):
    behaviors = {
        "validation-events": (0, "log", []),
        "validation-variables": (2, None, None),
    }
    _current_specs[:] = [_spec("events"), _spec("variables")]
    _patch_runner(tmp_path, monkeypatch, behaviors, 2)

    assert rvb.run_batch([_spec("events"), _spec("variables")], _Args(tmp_path)) == 1

    with open(tmp_path / rvb.MANIFEST_NAME, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert manifest["mode"] == "batch"
    assert manifest["selected"] == ["events", "variables"]
    results = {entry["name"]: entry for entry in manifest["results"]}
    assert results["events"]["status"] == "ok"
    assert results["events"]["returncode"] == 0
    assert results["events"]["strict"] is True
    assert results["variables"]["status"] == "crash"
    assert results["variables"]["returncode"] == 2


def test_stub_batch_artifact_loads_end_to_end(tmp_path, monkeypatch):
    """The full stub run produces an artifact tree the loader consumes."""
    _install_stub_runner(tmp_path, monkeypatch)

    out_dir = tmp_path / "results"
    args = _Args(out_dir)
    args.path = str(tmp_path)

    monkeypatch.setenv("STUB_ISSUES", '[{"severity": "error"}]')
    monkeypatch.setenv("STUB_EXIT", "1")
    assert rvb.run_batch([_spec("stub")], args) == 1

    # Crash: non-zero exit with no sidecar at all.
    monkeypatch.delenv("STUB_ISSUES")
    monkeypatch.setenv("STUB_EXIT", "3")
    (out_dir / "validation-stub.log").unlink()
    (out_dir / "validation-stub.json").unlink()
    assert rvb.run_batch([_spec("stub")], args) == 1

    runs = {run.name: run for run in load_all(str(out_dir))}

    # One run per validator: the .stderr.log crash capture and the manifest
    # never surface as bogus validators.
    assert set(runs) == {"stub"}
    # Manifest execution metadata is applied by the ordinary report loader,
    # so an empty sidecar after a crash is failed per validator.
    assert runs["stub"].status == "failed"
    with open(out_dir / rvb.MANIFEST_NAME, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    # rc 3 with an empty sidecar classifies as an empty "findings" run; the
    # non-zero returncode is the load-bearing execution metadata.
    assert manifest["results"][0]["returncode"] == 3
    assert manifest["results"][0]["status"] in {"crash", "findings"}


@pytest.mark.parametrize(
    ("exit_code", "stderr", "expected_status"),
    [(0, "", "passed"), (1, "validator failed\n", "failed")],
)
def test_batch_archive_round_trip_includes_stderr(
    tmp_path, monkeypatch, exit_code, stderr, expected_status
):
    _install_stub_runner(tmp_path, monkeypatch)
    monkeypatch.setenv("STUB_ISSUES", "[]")
    monkeypatch.setenv("STUB_EXIT", str(exit_code))
    monkeypatch.setenv("STUB_STDERR", stderr)

    out_dir = tmp_path / "results"
    args = _Args(out_dir)
    args.path = str(tmp_path)
    assert rvb.run_batch([_spec("stub")], args) == (1 if exit_code else 0)

    archive_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path in sorted(out_dir.iterdir()):
            archive.write(path, path.name)
    extracted = tmp_path / "extracted"
    members = safe_extract(archive_path, extracted)

    assert "validation-stub.stderr.log" in members
    assert (extracted / "validation-stub.stderr.log").read_text(
        encoding="utf-8"
    ) == stderr
    runs = load_all(str(extracted))
    assert [run.name for run in runs] == ["stub"]
    assert runs[0].status == expected_status


def test_empty_impact_selection_writes_valid_manifest(tmp_path, monkeypatch):
    changed = tmp_path / "changed.txt"
    changed.write_text("common/notes.txt\n", encoding="utf-8")
    monkeypatch.setattr(rvb, "run_batch", lambda *_args: pytest.fail("must not run"))

    assert (
        rvb.main(
            [
                "--impact",
                "--changed-files-file",
                str(changed),
                "--output-dir",
                str(tmp_path / "results"),
            ]
        )
        == 0
    )

    with open(tmp_path / "results" / rvb.MANIFEST_NAME, encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert manifest == {
        "mode": "impact",
        "batch": None,
        "selected": [],
        "results": [],
    }


@pytest.mark.parametrize(
    ("validator", "relative_path", "content", "message"),
    [
        (
            "localization-encoding",
            "localisation/english/good.yml",
            b"\xef\xbb\xbfl_english:\n",
            "Correct UTF-8 with BOM encoding",
        ),
        (
            "mod-encoding",
            "descriptor.mod",
            b'name="Test"\n',
            "Valid UTF-8 encoding",
        ),
    ],
)
def test_standalone_adapter_clean_encoding_has_no_issues(
    tmp_path, validator, relative_path, content, message
):
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    output = tmp_path / "out" / f"validation-{validator}.log"

    result = subprocess.run(
        [
            sys.executable,
            str(
                Path(__file__).parents[3] / "tools/validation/run_impact_standalone.py"
            ),
            "--validator",
            validator,
            "--path",
            str(tmp_path),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert message in output.read_text(encoding="utf-8")
    with open(output.with_suffix(".json"), encoding="utf-8") as handle:
        assert json.load(handle) == []


def test_standalone_adapter_writes_report_sidecar(tmp_path):
    english = tmp_path / "localisation" / "english"
    english.mkdir(parents=True)
    (english / "bad.yml").write_bytes(b"l_english:\n")
    output = tmp_path / "out" / "validation-localization-encoding.log"

    result = subprocess.run(
        [
            sys.executable,
            str(
                Path(__file__).parents[3] / "tools/validation/run_impact_standalone.py"
            ),
            "--validator",
            "localization-encoding",
            "--path",
            str(tmp_path),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert output.is_file()
    with open(output.with_suffix(".json"), encoding="utf-8") as handle:
        issues = json.load(handle)
    assert issues[0]["category"] == "localization-encoding"
    assert issues[0]["file"] == "localisation/english/bad.yml"
