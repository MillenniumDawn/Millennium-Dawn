import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import run as launcher


def test_discovery_hides_tests_and_validation_libraries():
    tools = launcher.find_all_tools()

    assert not any(path.parent.name == "tests" for path in tools.values())
    assert (
        not {
            "check_common_mistakes",
            "disk_cache",
            "equipment_module_slots",
            "equipment_stats",
            "sprite_index",
        }
        & tools.keys()
    )
    assert "validate_common_mistakes" in tools


@pytest.mark.parametrize(
    ("requested", "discovered"),
    [
        ("batchdds-2", "batchdds-2"),
        ("flag_reference_checker", "flag-reference-checker"),
    ],
)
def test_launcher_resolves_hyphenated_aliases(requested, discovered, monkeypatch):
    script = Path(f"/tools/{discovered}.py")
    monkeypatch.setattr(launcher, "find_all_tools", lambda: {discovered: script})
    calls = []
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda command, cwd: (
            calls.append((command, cwd)) or SimpleNamespace(returncode=0)
        ),
    )
    monkeypatch.setattr(sys, "argv", ["run.py", requested, "--help"])
    with pytest.raises(SystemExit) as exc:
        launcher.main()
    assert exc.value.code == 0
    assert calls[0][0][1:] == [str(script), "--help"]
