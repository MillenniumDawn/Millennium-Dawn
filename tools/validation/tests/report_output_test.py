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
