"""Behavioral tests for tools/analysis/inspect_save.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.analysis import inspect_save  # noqa: E402

MOD_FILES = {
    "common/units/equipment/test.txt": """equipments = {
\tinfantry_weapons_type = {
\t\tis_archetype = yes
\t}
\tinfantry_weapons_1 = {
\t\tarchetype = infantry_weapons_type
\t}
\theavy_tank_chassis = {
\t\tis_archetype = yes
\t}
\theavy_tank_amphibious_chassis = {
\t\tarchetype = heavy_tank_chassis
\t}
}
""",
    "common/buildings/test.txt": """buildings = {
\tarms_factory = {
\t\tlevel_cap = {
\t\t\tshares_slots = yes
\t\t}
\t}
\tair_base = {
\t\tprovincial = yes
\t}
}
""",
    "common/state_category/test.txt": """state_categories = {
\tcity = {
\t\tlocal_building_slots = 4
\t}
}
""",
    "history/states/1-One.txt": "state = {\n\tid = 1\n\tprovinces = { 100 101 }\n}\n",
    "history/states/2-Two.txt": "state = {\n\tid = 2\n\tprovinces = { 200 }\n}\n",
}

# BBB comes first so a whole-save regex would read its stability. AAA's leader block
# opens with a column-0 brace, as the game writes it.
SAVE = """HOI4txt
player="AAA"
date="2002.1.1.12"
equipments={
\tinfantry_weapons_1={
\t\tid={ id=1 type=70 }
\t}
\theavy_tank_amphibious_chassis_0={
\t\tid={ id=2 type=70 }
\t}
}
states={
\t1={
\t\tbuildings={
\t\t\tarms_factory={
\t\t\t\tlevel=2
\t\t\t}
\t\t}
\t\towner="AAA"
\t\tstate_category=city
\t}
\t2={
\t\towner="BBB"
\t\tcontroller="AAA"
\t\tstate_category=city
\t}
\t3={
\t\towner="AAA"
\t\tcontroller="BBB"
\t\tstate_category=city
\t\textra_shared_slots=1
\t}
}
countries={
\tBBB={
\t\tstability=0.11
\t}
\tAAA={
\t\tstability=0.5
\t\tpolitics={
\t\t\tparties={
\t\t\t\tdemocratic={
\t\t\t\t\tcountry_leader={
{
\t\t\t\t\t\t\tideology="liberalism"
\t\t\t\t\t\t}
 \t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\tideas={
\t\t\t\tidea_a idea_b
\t\t\t}
\t\t\truling_party=democratic
\t\t\tpolitical_power=12.5
\t\t}
\t\tproduction={
\t\t\tequipments={
\t\t\t\tequipment={
\t\t\t\t\tid={ id=1 type=70 }
\t\t\t\t\tamount=500
\t\t\t\t}
\t\t\t}
\t\t\tgeneral_lines={
\t\t\t\tbuilding={
\t\t\t\t\tid={ id=5 type=59 }
\t\t\t\t\tproduced=1000
\t\t\t\t\tactive_factories=3
\t\t\t\t\tpriority=0
\t\t\t\t\tamount=2
\t\t\t\t\tspeed=1
\t\t\t\t\tcost=1000
\t\t\t\t\tcreated_date="2000.1.1.13"
\t\t\t\t\tbuilding={
\t\t\t\t\t\ttemplate=arms_factory
\t\t\t\t\t\tlocation=1
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tbuilding={
\t\t\t\t\tid={ id=6 type=59 }
\t\t\t\t\tpriority=1
\t\t\t\t\tamount=1
\t\t\t\t\tcost=500
\t\t\t\t\tcreated_date="2000.2.1.1"
\t\t\t\t\tbuilding={
\t\t\t\t\t\ttemplate=air_base
\t\t\t\t\t\tlocation=200
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tbuilding={
\t\t\t\t\tid={ id=7 type=59 }
\t\t\t\t\tpriority=2
\t\t\t\t\tamount=1
\t\t\t\t\tcost=500
\t\t\t\t\tcreated_date="2000.3.1.1"
\t\t\t\t\tbuilding={
\t\t\t\t\t\ttemplate=naval_base
\t\t\t\t\t\tlocation=101
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\tmilitary_lines={
\t\t\t\tid={ id=8 type=56 }
\t\t\t\tactive_factories=4
\t\t\t\tpriority=0
\t\t\t\trequested_factories=6
\t\t\t\tequipment_variant_index={ id=1 type=70 }
\t\t\t}
\t\t\tmilitary_lines={
\t\t\t\tid={ id=9 type=56 }
\t\t\t\tpriority=1
\t\t\t\trequested_factories=1
\t\t\t\tequipment_variant_index={ id=2 type=70 }
\t\t\t}
\t\t}
\t\tvariables={
\t\t\ttreasury=10
\t\t}
\t}
}
equipment_market={
\tcontracts={
\t\tpurchase_contract={
\t\t\tid={ id=1 type=81 }
\t\t\tcontract_definition={
\t\t\t\tcontract_draft={
\t\t\t\t\tseller="BBB"
\t\t\t\t\tbuyer="AAA"
\t\t\t\t\tequipments={
\t\t\t\t\t\tequipment={
\t\t\t\t\t\t\tid={ id=1 type=70 }
\t\t\t\t\t\t\tamount=300
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tprice_levels={
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}
"""


def _write(path: Path, text: str, eol: str = "\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", eol))


def _run(
    tmp_path: Path, monkeypatch, capsys, save_text: str, *args: str
) -> tuple[int, str]:
    for name, text in MOD_FILES.items():
        _write(tmp_path / "mod" / name, text)
    save = tmp_path / "test.hoi4"
    _write(save, save_text, eol="\r\n")
    argv = ["inspect_save.py", str(save), *args, "--path", str(tmp_path / "mod")]
    monkeypatch.setattr(sys, "argv", argv)
    code = inspect_save.main()
    captured = capsys.readouterr()
    return code, captured.out + captured.err


# case: (arguments after the save, fragment the report must contain)
_REPORT_CASES = {
    "stability from the country's own block": (["AAA"], "stability 0.5,"),
    "column-0 brace keeps the block": (["AAA"], "ruling party democratic"),
    "political power from politics": (["AAA"], "political power 12.5"),
    "named variable": (["AAA"], "treasury 10"),
    "ideas": (["AAA"], "ideas: idea_a idea_b"),
    "type grouped by archetype": (
        ["AAA"],
        "infantry_weapons_type                         4 requested    6",
    ),
    "sub-archetype kept apart": (
        ["AAA"],
        "heavy_tank_amphibious_chassis                 0 requested    1",
    ),
    "years left": (
        ["AAA"],
        "factories  3 since 2000.1.1.13, 2.7 years left, owned state 1",
    ),
    "provincial building by province": (
        ["AAA"],
        "air_base                 levels   1 factories  0 since 2000.2.1.1, no progress, not owned (BBB) state 2",
    ),
    "unknown provincial building by province": (
        ["AAA"],
        "naval_base               levels   1 factories  0 since 2000.3.1.1, no progress, owned state 1",
    ),
    "stockpile by archetype": (["AAA"], "stockpile: infantry_weapons_type 500"),
    "market contract": (["AAA"], "BBB -> AAA: infantry_weapons_type 300"),
    "owned states and shared slots": (
        ["AAA"],
        "2 owned (1 occupied by others), shared slots used 2 of 9, 2 states with 7 free",
    ),
    "missing tag": (["CCC"], "## CCC: not in this save"),
    "world production": (["--world"], "4 (100.0%)"),
    "world market": (["--world"], "market: 1 contract lines, 1 buyers"),
}


@pytest.mark.parametrize("args, fragment", _REPORT_CASES.values(), ids=_REPORT_CASES)
def test_report(tmp_path, monkeypatch, capsys, args, fragment):
    code, out = _run(tmp_path, monkeypatch, capsys, SAVE, *args)
    assert code == 0
    assert fragment in out


def test_binary_save_is_rejected(tmp_path, monkeypatch, capsys):
    code, out = _run(tmp_path, monkeypatch, capsys, "HOI4bin\n", "AAA")
    assert code == 1
    assert "not a text save" in out
