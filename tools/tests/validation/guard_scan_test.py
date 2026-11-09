"""Shared file-input contracts for the guard validators."""

import disk_cache
import guard_scan
import pytest
import validate_ai_weight_order
import validate_building_guards
import validate_dynamic_modifier_guards
import validate_influence_calls

_CASES = [
    (
        validate_dynamic_modifier_guards,
        "remove_dynamic_modifier = { modifier = PER_pan_iranist_attack }",
        "remove_dynamic_modifier = { modifier = PER_pan_iranist_attack } is not "
        "guarded by a check that PER_pan_iranist_attack is applied",
        None,
    ),
    (
        validate_influence_calls,
        "every_country = { change_influence_percentage = yes }",
        "change_influence_percentage = yes runs inside every_country without a "
        "per-iteration influence_target; temp variables persist across "
        "iterations, so every pass after the first re-targets the first "
        "iterated country",
        None,
    ),
    (
        validate_ai_weight_order,
        "ai_chance = { modifier = { factor = 0 } modifier = { add = 5 } }",
        "ai_chance adds after a factor = 0 modifier, which brings the zeroed "
        "weight back; move the factor = 0 modifiers last",
        None,
    ),
    (
        validate_building_guards,
        "damage_building = { type = fuel_silo damage = 1 }",
        "damage_building = { type = fuel_silo ... } is not guarded by a check "
        "that fuel_silo exists",
        "unguarded-damage-building",
    ),
]


@pytest.fixture(params=_CASES, ids=[case[0].__name__ for case in _CASES])
def scanner_case(request):
    return request.param


def test_scan_file_reads_and_relativizes_path(tmp_path, monkeypatch, scanner_case):
    scanner, script, message, category = scanner_case
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    target = tmp_path / "events"
    target.mkdir()
    path = target / "Test.txt"
    path.write_text("wrapper = {\n\t" + script + "\n}\n", encoding="utf-8-sig")
    args = (str(path), str(tmp_path) + "/")
    expected = ("events/Test.txt", 2, message)
    if category:
        expected = (category, *expected)
    assert scanner.scan_file(args) == [expected]
    assert scanner.scan_file(args) == [expected]


def test_scan_file_skips_files_without_the_effect(tmp_path, monkeypatch, scanner_case):
    def scanned(*_args):
        raise AssertionError("a file without the effect reached the scan")

    monkeypatch.setattr(disk_cache, "per_file_cached_by_content", scanned)
    path = tmp_path / "quiet.txt"
    path.write_text("focus = { id = TST_focus }\n", encoding="utf-8")
    assert scanner_case[0].scan_file((str(path), str(tmp_path) + "/")) == []


@pytest.mark.parametrize("bad_input", ["missing", "directory", "invalid-utf8"])
def test_read_file_reports_unreadable_input(tmp_path, bad_input):
    path = tmp_path / "broken.txt"
    if bad_input == "directory":
        path.mkdir()
    elif bad_input == "invalid-utf8":
        path.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="Cannot scan"):
        guard_scan.read_file(str(path))


def test_scan_file_reports_unreadable_input(tmp_path, scanner_case):
    with pytest.raises(ValueError, match="Cannot scan"):
        scanner_case[0].scan_file((str(tmp_path / "missing.txt"), str(tmp_path)))
