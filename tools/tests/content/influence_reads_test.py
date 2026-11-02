"""Influence-reader contracts and the two already-fixed scope regressions."""

import pytest
import validate_influence_reads as V
from shared.paths import REPO_ROOT

_SOURCES = (
    "common/scripted_triggers/00_influence_scripted_triggers.txt",
    "common/scripted_triggers/99_EU_scripted_triggers.txt",
    "common/scripted_triggers/99_HOL_scripted_triggers.txt",
)


def _contracts(definition):
    found = set()
    for node in V._nodes(definition.children):
        if node.key == "check_variable":
            for child in node.children:
                if child.key.startswith("influence_array^"):
                    found.add((child.value.removesuffix(".id"), "THIS"))
        elif node.key == "is_in_array":
            array = V.value(node, "array")
            if array == "ROOT.influence_array":
                found.add((V.value(node, "value"), "ROOT"))
            elif V.value(node, "influence_array"):
                found.add((V.value(node, "influence_array"), "THIS"))
        elif node.key == "any_of" and V.value(node, "array") == "influence_array":
            sources = [
                child.value
                for scope in node.children
                if scope.key.startswith("var:")
                for child in scope.children
                if child.key == "tag"
            ]
            found.update((source, "THIS") for source in sources)
    return found


def test_registered_read_contracts_match_live_definitions():
    definitions = {
        node.key: node
        for path in _SOURCES
        for node in V.script_nodes((REPO_ROOT / path).read_text(encoding="utf-8"))
    }
    assert V.CONTRACTS.keys() <= definitions.keys()
    assert {name: _contracts(definitions[name]) for name in V.CONTRACTS} == {
        name: {contract} for name, contract in V.CONTRACTS.items()
    }
    core = V.script_nodes((REPO_ROOT / _SOURCES[0]).read_text(encoding="utf-8"))
    assert {node.key for node in core if _contracts(node)} <= V.CONTRACTS.keys()


# file, entry id, expected target arrays and source bindings
_REGRESSIONS = {
    "6198 Pivot Reversed": (
        "common/national_focus/03_china_north_korea_joint.txt",
        "CHI_The_Pivot_Reversed",
        {
            (
                "is_top3_influencer",
                "ROOT[CHI_The_Pivot_Reversed; original_tag=CHI]",
                "KOR",
            ),
            ("prev_is_top3_influencer", "USA", "KOR"),
        },
    ),
    "6197 achievement ROOT rather than sender": (
        "common/achievements/MD_achievements.txt",
        "achievement_legacy_of_michiel_de_ruyter",
        {
            (
                "is_top3_influencer",
                "ROOT[achievement_legacy_of_michiel_de_ruyter; original_tag=HOL]",
                target,
            )
            for target in ("USA", "ENG", "SOV", "CHI", "FRA")
        },
    ),
}


@pytest.mark.parametrize("path,entry,expected", _REGRESSIONS.values(), ids=_REGRESSIONS)
def test_reviewed_live_scope_baseline(path, entry, expected):
    nodes = V.script_nodes((REPO_ROOT / path).read_text(encoding="utf-8"))
    node = next(
        node
        for node in V._nodes(nodes)
        if node.key == entry or V.value(node, "id") == entry
    )
    rows = V.Reader({path: [node]}).scan()
    actual = {
        (row.trigger, row.influencer.split("@", 1)[0], row.target) for row in rows
    }
    assert actual == expected
    assert {row.status for row in rows} == {"resolved"}
    assert all(row.line > node.line for row in rows)
