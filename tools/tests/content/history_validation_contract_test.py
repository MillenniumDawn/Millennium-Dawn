"""Reported Japan and Ukraine validation regressions against real history data."""

import pytest
from equipment_variant_context import VariantContext, script_nodes
from shared.paths import REPO_ROOT
from shared_utils import FileOpener
from validate_equipment_variants import check_variant_availability, equipment_unlocks
from validate_history import check_influence_order


def read(relative):
    return FileOpener.open_text_file(str(REPO_ROOT / relative))


@pytest.mark.parametrize("late_init", [False, True])
def test_japan_influence_setup(late_init):
    text = read("history/countries/JAP - Japan.txt")
    if late_init:
        text = text.replace("init_influence = yes", "", 1).replace(
            "sort_influence = yes", "init_influence = yes\nsort_influence = yes", 1
        )
    findings = check_influence_order(text, "JAP")
    assert bool(findings) == late_init
    if late_init:
        assert any("clears earlier" in message for message, _ in findings)


@pytest.mark.parametrize("remove_grant", [False, True])
def test_ukraine_starting_apc_stockpile(remove_grant):
    paths = [
        "history/countries/UKR - Ukraine.txt",
        "common/technologies/armor.txt",
        "common/technology_tags/00_technology.txt",
    ]
    documents = {path: read(path) for path in paths}
    for path in sorted((REPO_ROOT / "common/bookmarks").glob("*.txt")):
        documents[path.relative_to(REPO_ROOT).as_posix()] = read(
            path.relative_to(REPO_ROOT)
        )
    if remove_grant:
        documents[paths[0]] = documents[paths[0]].replace("APC_1 = 1", "APC_1 = 0")
    context = VariantContext(
        documents={path: script_nodes(text) for path, text in documents.items()}
    )
    context.index()
    # Original event sequence, before the later scripted-effect rework added a grant.
    source = """country_event = {
        id = regression.5773
        trigger = { original_tag = UKR }
        option = {
            create_equipment_variant = { name = "BTR-60D" type = APC_1 }
            add_equipment_to_stockpile = { type = APC_1 variant_name = "BTR-60D" amount = 100 producer = UKR }
        }
    }"""
    findings = check_variant_availability(
        source, equipment_unlocks(documents[paths[1]]), context
    )
    assert bool(findings) == remove_grant
