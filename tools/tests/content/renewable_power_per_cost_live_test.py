"""renewable_power_per_cost.py against the shipped industry.txt."""

import subprocess
import sys

import pytest
from shared.paths import REPO_ROOT

pytest.importorskip("numpy", reason="numpy is in the optional analysis group")
pytest.importorskip("matplotlib", reason="matplotlib is in the optional analysis group")
SCRIPT = REPO_ROOT / "tools" / "analysis" / "renewable_power_per_cost.py"


def test_cli_writes_png(tmp_path):
    out = tmp_path / "chart.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out)],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(REPO_ROOT),
    )
    assert out.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    for label in ("ren:", "nuc:", "fos:", "state"):
        assert label in result.stdout
