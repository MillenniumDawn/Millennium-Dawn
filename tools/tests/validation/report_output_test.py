import pytest
import validator_common as V


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
