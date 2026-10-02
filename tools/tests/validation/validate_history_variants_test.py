"""Tests for the equipment-variant module check in validate_history.

`create_equipment_variant` bypasses the engine's module tech checks, so a design
using a module no granted technology enables ships with a module the country
cannot otherwise build. The check unions the techs of every DLC branch (both
DLCs are active in normal play) and reports each variant/module pair once.
"""

import validate_history as V


def _write_country(tmp_path, body, name="TST - Test.txt"):
    path = tmp_path / "history" / "countries" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return str(path)


def _variant(name, modules, indent="\t"):
    body = "".join(f"{indent}\t\t{slot} = {module}\n" for slot, module in modules)
    return (
        f"{indent}create_equipment_variant = {{\n"
        f'{indent}\tname = "{name}"\n'
        f"{indent}\ttype = frigate_hull_2\n"
        f"{indent}\tmodules = {{\n"
        f"{body}"
        f"{indent}\t}}\n"
        f"{indent}}}\n"
    )


def test_find_dlc_if_blocks_tags_positive_has_dlc_guard():
    content = 'if = {\n\tlimit = { has_dlc = "By Blood Alone" }\n\tfoo = yes\n}\n'
    blocks = V._find_dlc_if_blocks(content)
    assert len(blocks) == 1
    start, end, dlc = blocks[0]
    assert dlc == "By Blood Alone"
    assert content[start:end].startswith("if = {")


def test_find_dlc_if_blocks_skips_negated_non_dlc_and_limitless_blocks():
    content = (
        "if = {\n"
        '\tlimit = { NOT = { has_dlc = "No Step Back" } }\n'
        "\tfoo = yes\n"
        "}\n"
        "if = {\n"
        "\tlimit = { has_country_flag = some_flag }\n"
        "\tfoo = yes\n"
        "}\n"
        "if = {\n"
        "\tfoo = yes\n"
        "}\n"
    )
    assert V._find_dlc_if_blocks(content) == []


def test_parse_variants_text_collects_modules_and_skips_empty_slots():
    content = _variant(
        "Naresuan Class",
        [
            ("fixed_ship_battery_slot", "ship_light_medium_battery_2"),
            ("fixed_ship_anti_air_slot", "empty"),
        ],
        indent="",
    )
    assert V._parse_variants_text(content) == [
        ("Naresuan Class", {"ship_light_medium_battery_2"}, frozenset())
    ]


def test_parse_variants_text_marks_unnamed_variant_and_dlc_gating():
    content = (
        "if = {\n"
        '\tlimit = { has_dlc = "By Blood Alone" }\n'
        "\tcreate_equipment_variant = {\n"
        "\t\ttype = frigate_hull_2\n"
        "\t\tmodules = {\n"
        "\t\t\tengine_slot = engine_2\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    variants = V._parse_variants_text(content)
    assert variants == [("?", {"engine_2"}, frozenset({"By Blood Alone"}))]


def test_parse_variants_text_handles_variant_without_a_modules_block():
    content = (
        "create_equipment_variant = {\n"
        '\tname = "Stock Frigate"\n'
        "\ttype = frigate_hull_2\n"
        "}\n"
    )
    assert V._parse_variants_text(content) == [("Stock Frigate", set(), frozenset())]


def test_parse_equipment_variants_missing_file_returns_empty(tmp_path):
    assert V.parse_equipment_variants(str(tmp_path / "gone.txt"), str(tmp_path)) == []


def test_parse_equipment_variants_reads_file(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write_country(
        tmp_path,
        "# a commented design must not count\n"
        + _variant("Type 32", [("engine_slot", "engine_2")], indent=""),
    )
    assert V.parse_equipment_variants(path, str(tmp_path)) == [
        ("Type 32", {"engine_2"}, frozenset())
    ]


def test_module_without_enabling_tech_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write_country(
        tmp_path, _variant("Type 32", [("engine_slot", "engine_2")], indent="")
    )
    assert V.validate_country_equipment((path, {}, str(tmp_path))) == []


def test_module_without_granted_tech_is_flagged(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write_country(
        tmp_path,
        "set_technology = {\n\tbasic_engines = 1\n}\n"
        + _variant("Type 32", [("engine_slot", "engine_4")], indent=""),
    )
    errors = V.validate_country_equipment(
        (path, {"engine_4": {"advanced_engines"}}, str(tmp_path))
    )
    assert errors == [
        'TST - Test.txt: variant "Type 32" uses engine_4 without enabling tech '
        "advanced_engines"
    ]


def test_alternative_enabling_techs_are_listed(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write_country(
        tmp_path, _variant("Type 32", [("engine_slot", "engine_4")], indent="")
    )
    errors = V.validate_country_equipment(
        (path, {"engine_4": {"engines_b", "engines_a"}}, str(tmp_path))
    )
    assert errors == [
        'TST - Test.txt: variant "Type 32" uses engine_4 without enabling tech '
        "one of: engines_a, engines_b"
    ]


def test_tech_granted_in_another_dlc_branch_still_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write_country(
        tmp_path,
        "if = {\n"
        '\tlimit = { has_dlc = "By Blood Alone" }\n'
        "\tset_technology = { advanced_engines = 1 }\n"
        "}\n" + _variant("Type 32", [("engine_slot", "engine_4")], indent=""),
    )
    assert (
        V.validate_country_equipment(
            (path, {"engine_4": {"advanced_engines"}}, str(tmp_path))
        )
        == []
    )


def test_same_variant_and_module_is_reported_once(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write_country(
        tmp_path,
        _variant("Type 32", [("engine_slot", "engine_4")], indent="")
        + _variant("Type 32", [("engine_slot", "engine_4")], indent=""),
    )
    errors = V.validate_country_equipment(
        (path, {"engine_4": {"advanced_engines"}}, str(tmp_path))
    )
    assert len(errors) == 1
