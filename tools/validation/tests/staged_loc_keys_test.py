"""Regression tests for staged-mode lookup scans.

Bug family: lookup passes (loc keys, event references) used to restrict
their scan to staged files in --staged mode. A staged .txt whose loc or
references live in unchanged files then flooded with false positives
(5,644 of 6,007 warnings in one recorded validate_events --staged run).
Lookup scans must always cover the full repo; only the reporting scope
is staged-limited.
"""

from validator_common import BaseValidator


class _DummyValidator(BaseValidator):
    TITLE = "DUMMY"

    def run_validations(self):
        pass


def _make_loc_tree(tmp_path):
    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    (loc_dir / "test_l_english.yml").write_text(
        'l_english:\n TEST_key_one:0 "One"\n TEST_key_two:0 "Two"\n',
        encoding="utf-8-sig",
    )


def test_loc_keys_loaded_full_repo_in_staged_mode(tmp_path):
    _make_loc_tree(tmp_path)
    v = _DummyValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    # Simulate staged mode with only a .txt staged (the loc .yml is unchanged)
    v.staged_only = True
    v.staged_files = ["events/some_event.txt"]

    keys = v._load_localisation_keys()
    assert "TEST_key_one" in keys, (
        "Staged mode must still load loc keys from unstaged .yml files"
    )
    assert "TEST_key_two" in keys


def test_loc_keys_memoized(tmp_path):
    _make_loc_tree(tmp_path)
    v = _DummyValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    first = v._load_localisation_keys()
    second = v._load_localisation_keys()
    assert first is second, "Repeat calls must return the memoized frozenset"


def test_triggered_only_reference_scan_full_repo_in_staged_mode(tmp_path):
    from validate_events import Validator as EventsValidator

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "staged.txt").write_text(
        "add_namespace = stg\n"
        "country_event = {\n"
        "\tid = stg.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = stg.1.a }\n"
        "}\n",
        encoding="utf-8",
    )
    # The only reference lives in an UNSTAGED focus file
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True)
    (nf_dir / "unstaged.txt").write_text(
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tid = TAG_a\n"
        "\t\tcompletion_reward = { country_event = stg.1 }\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )

    v = EventsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.staged_only = True
    v.staged_files = ["events/staged.txt"]
    v.validate_triggered_only_unreferenced()
    assert v.warnings_found == 0, (
        "Reference in an unstaged file must count — staged mode used to "
        "scan only staged files and report the event as unreferenced"
    )
