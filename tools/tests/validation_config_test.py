import json

import pytest
import shared_utils as U


def test_every_list_maps_entries_to_reasons():
    config = U._load_validation_config()
    for validator, lists in config.items():
        if validator == "version":
            continue
        for key, entries in lists.items():
            assert isinstance(entries, dict), f"{validator}.{key}"
            assert all(
                isinstance(r, str) for r in entries.values()
            ), f"{validator}.{key}"


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
