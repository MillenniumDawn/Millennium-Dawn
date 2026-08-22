import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads(
    (ROOT / "tools/corporate_history_contract.json").read_text(encoding="utf-8")
)
LIFECYCLE_SYSTEMS = MANIFEST["reusable_decision_lifecycles"]


def _block_at(text: str, opening_brace: int) -> str:
    depth = 0
    for index in range(opening_brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1 : index]
    raise AssertionError("Unbalanced scripted block")


def _blocks_at_indent(text: str, tabs: int) -> dict[str, str]:
    blocks = {}
    prefix = "\t" * tabs
    child_prefix = "\t" * (tabs + 1)
    offset = 0
    for line in text.splitlines(keepends=True):
        match = re.match(
            rf"^{re.escape(prefix)}([^\t#][A-Za-z0-9_.:-]*)\s*=\s*\{{",
            line,
        )
        if match is not None and not line.startswith(child_prefix):
            opening_brace = offset + line.index("{")
            blocks[match.group(1)] = _block_at(text, opening_brace)
        offset += len(line)
    return blocks


def _localisation_values(relative_path: str) -> dict[str, str]:
    text = (ROOT / relative_path).read_text(encoding="utf-8-sig")
    values = {}
    for line in text.splitlines():
        match = re.match(r'^\s*([^\s:#]+):\d*\s+"(.*)"\s*$', line)
        if match is not None:
            values[match.group(1)] = match.group(2)
    return values


@pytest.mark.parametrize(
    "system",
    LIFECYCLE_SYSTEMS,
    ids=[system["name"] for system in LIFECYCLE_SYSTEMS],
)
def test_reusable_decision_lifecycles_match_the_manifest(system):
    decision_text = (ROOT / system["decision_file"]).read_text(encoding="utf-8")
    decisions = _blocks_at_indent(decision_text, 1)
    declared = {program["decision"] for program in system["programs"]}
    actionable = {
        decision
        for decision, body in decisions.items()
        if "complete_effect = {" in body
    }
    assert actionable == declared

    effects = {}
    if effect_file := system.get("effect_file"):
        effect_text = (ROOT / effect_file).read_text(encoding="utf-8")
        effects = _blocks_at_indent(effect_text, 0)
    localisation = _localisation_values(system["localisation_file"])

    for program in system["programs"]:
        decision = program["decision"]
        body = decisions[decision]
        kind = program["kind"]
        active_days = program["active_days"]
        cooldown_days = program["cooldown_days"]

        assert "fire_only_once = no" in body
        assert cooldown_days <= 365

        if program["cooldown_mode"] == "days_re_enable":
            assert f"days_re_enable = {cooldown_days}" in body
        else:
            assert program["cooldown_mode"] == "active_duration"
            assert cooldown_days == 0
            assert f"days_remove = {active_days}" in body
            for marker in system.get("forbidden_cooldown_markers", []):
                assert marker not in body

        if kind == "timed_idea":
            assert 1 <= active_days <= 365
            source = program["duration_source"]
            source_body = body if source == "decision" else effects[source]
            expected_idea = (
                f"add_timed_idea = {{ idea = {program['idea']} "
                f"days = {active_days} }}"
            )
            assert source_body.count(expected_idea) == 1
            assert not re.search(
                r"\badd_timed_idea\s*=\s*\{[^{}]*\bdays\s*=\s*730\b",
                source_body,
            )
            if program["cooldown_mode"] == "days_re_enable":
                assert cooldown_days == active_days

            cleanup = effects[program["cleanup_effect"]]
            assert program["idea"] in cleanup
            if program.get("cleanup_decision"):
                assert f"remove_decision = {decision}" in cleanup
        else:
            assert active_days == 0
            assert "add_timed_idea" not in body

        if kind == "construction_project":
            mission = decisions[program["mission"]]
            assert f"days_mission_timeout = {program['project_days']}" in mission
            if program["project_days"] > 365:
                assert program["long_duration_reason"]

        expected_loc_days = active_days if kind == "timed_idea" else cooldown_days
        for key in program.get("localisation_keys", []):
            assert str(expected_loc_days) in localisation[key]
            assert "730" not in localisation[key]


def test_covered_temporary_programs_never_restore_a_730_day_active_effect():
    timed_programs = [
        (system, program)
        for system in LIFECYCLE_SYSTEMS
        for program in system["programs"]
        if program["kind"] == "timed_idea"
    ]
    assert timed_programs
    assert all(program["active_days"] <= 365 for _, program in timed_programs)
