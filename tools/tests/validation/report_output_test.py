import json

import pytest
import validator_common as V


def test_save_output_writes_empty_sidecar_on_clean_run(tmp_path):
    validator = V.BaseValidator(str(tmp_path), output_file=str(tmp_path / "out.log"))
    validator.output_lines.append("result")
    validator.save_output()
    assert json.loads((tmp_path / "out.json").read_text(encoding="utf-8")) == []


def test_save_output_writes_issues_to_sidecar(tmp_path):
    validator = V.BaseValidator(str(tmp_path), output_file=str(tmp_path / "out.log"))
    validator.add_issue("error", "cat", "msg", file="a.txt", line=3)
    validator.save_output()
    issues = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert [i["message"] for i in issues] == ["msg"]


def test_base_validator_output_failure_propagates(tmp_path, monkeypatch):
    validator = V.BaseValidator(str(tmp_path), output_file=str(tmp_path / "out.log"))
    validator.output_lines.append("result")

    def fail_write(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(V, "atomic_write_text", fail_write)
    with pytest.raises(OSError, match="disk full"):
        validator.save_output()


def test_worker_count_is_clamped_to_the_cpu_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "cpu_budget", lambda: 3)
    assert V.BaseValidator(str(tmp_path), workers=32).workers == 3
    assert V.BaseValidator(str(tmp_path), workers=2).workers == 2
    assert V.BaseValidator(str(tmp_path)).workers <= 3
