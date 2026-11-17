import json

import pytest
import shared_utils as U


def test_every_list_maps_entries_to_reasons():
    config = U._load_validation_config()
    for validator, lists in config.items():
        if validator == "version":
            continue
        for key, entries in lists.items():
            if key == "modifier_caps":
                continue
            assert isinstance(entries, dict), f"{validator}.{key}"
            assert all(
                isinstance(r, str) for r in entries.values()
            ), f"{validator}.{key}"


def test_every_modifier_cap_row_is_complete():
    lists = U._load_validation_config()["validate_modifiers"]
    for row in lists["modifier_caps"]:
        assert row["match"] and all(isinstance(p, str) for p in row["match"]), row
        assert isinstance(row["reason"], str) and row["reason"], row
        if row.get("skip"):
            continue
        assert row["cap"] >= 0 and row["direction"] in ("bonus", "either"), row
        assert row.get("bonus_cap", 0) >= 0, row
        assert isinstance(row["category"], str), row
        if "exceptions" in row:
            assert row["exceptions"] in lists, row


def test_unknown_version_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "validation_config.json"
    path.write_text(json.dumps({"version": 2}), encoding="utf-8")
    monkeypatch.setattr(U, "VALIDATION_CONFIG_PATH", str(path))
    U._load_validation_config.cache_clear()
    try:
        with pytest.raises(ValueError, match="expected version 1"):
            U.validation_config("validate_ideas", "vanilla_idea_prefixes")
    finally:
        U._load_validation_config.cache_clear()
