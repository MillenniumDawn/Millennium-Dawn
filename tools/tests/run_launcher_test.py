import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import run as launcher


def stub_subprocess(monkeypatch, returncode=0):
    calls = []
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda command, cwd: (
            calls.append((command, cwd)) or SimpleNamespace(returncode=returncode)
        ),
    )
    return calls


def invoke(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["run.py", *argv])
    with pytest.raises(SystemExit) as exc:
        launcher.main()
    return exc.value.code


def build_tools_tree(tmp_path):
    """A miniature tools/ tree: one subdir, one root script, one shadowed name."""
    (tmp_path / "analysis").mkdir()
    for rel in (
        "analysis/estimate_gdp.py",
        "analysis/_helper.py",
        "analysis/shared.py",
        "shared.py",
        "root_only.py",
        "run.py",
        "shared_utils.py",
    ):
        (tmp_path / rel).touch()
    return tmp_path


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


def test_discovery_skips_private_hidden_and_absent_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "TOOLS_DIR", build_tools_tree(tmp_path))

    tools = launcher.find_all_tools()

    assert set(tools) == {"estimate_gdp", "shared", "root_only"}
    assert "_helper" not in tools
    assert "run" not in tools
    assert "shared_utils" not in tools


def test_a_subdirectory_script_shadows_the_root_script_of_the_same_name(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(launcher, "TOOLS_DIR", build_tools_tree(tmp_path))

    assert launcher.find_all_tools()["shared"].parent.name == "analysis"


def test_print_list_groups_tools_by_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(launcher, "TOOLS_DIR", build_tools_tree(tmp_path))

    launcher.print_list(launcher.find_all_tools())

    out = capsys.readouterr().out
    assert "  analysis/" in out
    assert "  root/" in out
    assert out.index("analysis/") < out.index("root/")
    assert "    estimate_gdp" in out
    assert "assets/" not in out


@pytest.mark.parametrize("argv", [(), ("--help",), ("-h",)])
def test_bare_invocation_prints_usage_and_exits_zero(argv, monkeypatch, capsys):
    assert invoke(monkeypatch, *argv) == 0
    assert "python3 tools/run.py <tool-name>" in capsys.readouterr().out


def test_list_flag_prints_the_catalogue(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(launcher, "TOOLS_DIR", build_tools_tree(tmp_path))

    assert invoke(monkeypatch, "--list") == 0
    assert "Available tools:" in capsys.readouterr().out


def test_exact_name_launches_the_script_and_propagates_its_exit_code(monkeypatch):
    script = Path("/tools/analysis/estimate_gdp.py")
    monkeypatch.setattr(launcher, "find_all_tools", lambda: {"estimate_gdp": script})
    calls = stub_subprocess(monkeypatch, returncode=3)

    assert invoke(monkeypatch, "estimate_gdp.py", "--all") == 3
    assert calls == [([sys.executable, str(script), "--all"], os.getcwd())]


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
    calls = stub_subprocess(monkeypatch)

    assert invoke(monkeypatch, requested, "--help") == 0
    assert calls[0][0][1:] == [str(script), "--help"]


def test_a_unique_substring_resolves_to_the_only_match(monkeypatch):
    script = Path("/tools/analysis/estimate_gdp.py")
    monkeypatch.setattr(
        launcher,
        "find_all_tools",
        lambda: {"estimate_gdp": script, "review_branch": Path("/tools/rb.py")},
    )
    calls = stub_subprocess(monkeypatch)

    assert invoke(monkeypatch, "gdp") == 0
    assert calls[0][0][1] == str(script)


def test_an_ambiguous_substring_lists_the_candidates_and_fails(monkeypatch, capsys):
    monkeypatch.setattr(
        launcher,
        "find_all_tools",
        lambda: {
            "validate_events": Path("/tools/e.py"),
            "validate_ideas": Path("/tools/i.py"),
        },
    )
    calls = stub_subprocess(monkeypatch)

    assert invoke(monkeypatch, "validate") == 1
    out = capsys.readouterr().out
    assert "Ambiguous tool name 'validate'" in out
    assert "  validate_events" in out
    assert "  validate_ideas" in out
    assert calls == []


def test_an_unknown_name_points_at_the_catalogue(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "find_all_tools", lambda: {"estimate_gdp": Path("x")})
    calls = stub_subprocess(monkeypatch)

    assert invoke(monkeypatch, "nonexistent_tool_xyz") == 1
    out = capsys.readouterr().out
    assert "Unknown tool: 'nonexistent_tool_xyz'" in out
    assert "--list" in out
    assert calls == []
