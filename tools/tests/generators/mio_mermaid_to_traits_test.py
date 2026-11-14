from pathlib import Path

from shared.suite import load_tool_module


def _module():
    return load_tool_module("generators/mio_mermaid_to_traits.py")


def _write(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as handle:
        handle.write(text)


def test_generates_traits_and_localisation_from_mermaid(tmp_path, monkeypatch):
    module = _module()
    repo = tmp_path / "repo"
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(
        module,
        "known_equipment_tokens",
        lambda: {"light_aircraft", "corvette", "stealth_corvette"},
    )

    source = repo / "docs/countries/testland/mio.md"
    _write(
        source,
        (
            "# Test MIO\n\n"
            "```mermaid\n"
            "flowchart TD\n"
            '    H1["Airframe Branch"]\n'
            '    T0["Root Trait<br/>light_aircraft: reliability +3%; mio_research +4%"]\n'
            '    T1["Child Trait<br/>build_cost -2%; production_efficiency_cap +10%"]\n'
            '    T2["Alt Parent<br/>soft_attack +5%"]\n'
            '    T3["Join Node<br/>hard_attack +6%"]\n'
            "    T0 --> T1\n"
            "    T0 --> T3\n"
            "    T2 --> T3\n"
            "    T0 -.-|mutually exclusive| T2\n"
            "```\n"
        ),
    )

    destination = (
        repo
        / "common/military_industrial_organization/organizations/MD_TST_organizations.txt"
    )
    _write(
        destination,
        (
            "TST_demo_mio = {\n"
            "\tallowed = { original_tag = TST }\n"
            "}\n"
        ),
    )
    loc = repo / "localisation/english/MD_focus_TST_l_english.yml"
    _write(loc, "\ufeffl_english:\n", encoding="utf-8-sig")

    module.run(
        "docs/countries/testland/mio.md",
        1,
        "common/military_industrial_organization/organizations/MD_TST_organizations.txt",
        2,
    )

    generated = destination.read_text(encoding="utf-8")
    assert "tree_header_text = {\n\ttext = TST_demo_mio_header_airframe_branch\n\tx = 2\n}" in generated
    assert "\ttoken = TST_demo_mio_root_trait" in generated
    assert "\tposition = { x = 2 y = 0 }" in generated
    assert "\tlimit_to_equipment_type = {\n\t\tlight_aircraft\n\t}" in generated
    assert (
        "\torganization_modifier = {\n\t\tmilitary_industrial_organization_research_bonus = 0.04\n\t}"
        in generated
    )
    assert (
        "\tproduction_bonus = {\n\t\tproduction_efficiency_cap_factor = 0.1\n\t}"
        in generated
    )
    assert "\tall_parents = {\n\t\tTST_demo_mio_root_trait\n\t}" in generated
    assert (
        "\tany_parent = {\n\t\tTST_demo_mio_root_trait\n\t\tTST_demo_mio_alt_parent\n\t}"
        in generated
    )
    assert "\trelative_position_id = TST_demo_mio_root_trait" in generated
    assert "\ttoken = TST_demo_mio_alt_parent" in generated
    assert "\tposition = { x = 5 y = 0 }" in generated

    loc_text = loc.read_text(encoding="utf-8-sig")
    assert ' TST_demo_mio_header_airframe_branch: "Airframe Branch"' in loc_text
    assert ' TST_demo_mio_root_trait: "Root Trait"' in loc_text
    assert ' TST_demo_mio_join_node: "Join Node"' in loc_text
