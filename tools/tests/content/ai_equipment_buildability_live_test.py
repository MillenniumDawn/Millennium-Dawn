"""Exercise the advisory check on the Greek and Turkish regression sources."""

from ai_equipment_buildability import parse_designs
from shared.paths import REPO_ROOT
from shared.suite import build_validator, write_tree
from validate_ai_equipment import Validator
from validator_common import Severity


def test_naval_regression_sources(tmp_path):
    paths = [
        REPO_ROOT / "common/ai_equipment/GRE_naval.txt",
        REPO_ROOT / "common/ai_equipment/TUR_naval.txt",
        REPO_ROOT / "history/countries/GRE - Greece.txt",
        REPO_ROOT / "history/countries/TUR - Turkey.txt",
    ]
    for directory in (
        "common/bookmarks",
        "common/technologies",
        "common/technology_tags",
        "common/scripted_effects",
        "common/units/equipment",
    ):
        paths.extend((REPO_ROOT / directory).rglob("*.txt"))
    sources = {
        path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8-sig")
        for path in paths
    }
    write_tree(tmp_path, sources)
    for country in ("GRE", "TUR"):
        path = f"common/ai_equipment/{country}_naval.txt"
        designs = parse_designs(sources[path], path)
        assert designs and all(design.users == {country} for design in designs)
        assert any(design.hull == "frigate_hull_2" for design in designs)
    validator = build_validator(Validator, tmp_path, check_buildability=True)
    validator._validate_buildability()
    assert validator.errors_found == 0
    assert not any(
        "DLC configuration limit" in issue.message for issue in validator._issues
    )
    assert all(issue.severity == Severity.WARNING for issue in validator._issues)
    assert all(
        issue.file.startswith("common/ai_equipment/")
        and issue.message.startswith(("GRE:", "TUR:"))
        for issue in validator._issues
    )
