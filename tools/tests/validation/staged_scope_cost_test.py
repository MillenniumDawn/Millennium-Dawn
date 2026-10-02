"""Staged runs build a repo-wide index only when a staged file reaches its check.

Each early exit is pinned twice: once with the expensive work made to raise,
proving a staged set that cannot use it never pays for it, and once with a
staged file that does need it, proving the check still fires with the same
file, line and message.
"""

import pytest
import validate_scripted_localisation as SL


def _staged(validator, *paths):
    validator.staged_only = True
    validator.staged_files = [str(path) for path in paths]
    return validator


def _rows(validator):
    return sorted(
        (issue.category, issue.message, issue.file, issue.line)
        for issue in validator._issues
    )


def _forbid(monkeypatch, target, *names):
    def boom(*_args, **_kwargs):
        raise AssertionError("staged run built an index it cannot use")

    for name in names:
        monkeypatch.setattr(target, name, boom)


@pytest.fixture(autouse=True)
def _no_shared_staged_list(monkeypatch):
    # The pre-commit dispatcher exports this; a test must not inherit it.
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)


# --- scripted localisation -------------------------------------------------

_SLOC_DEFS = (
    "defined_text = {\n\tname = UsedLoc\n}\n"
    "defined_text = {\n\tname = OrphanLoc\n}\n"
)


def test_scripted_loc_without_a_staged_definition_skips_the_usage_scan(
    tmp_path, write_path, monkeypatch
):
    write_path(tmp_path, "common/scripted_localisation/defs.txt", _SLOC_DEFS)
    yml = write_path(
        tmp_path,
        "localisation/english/use_l_english.yml",
        'l_english:\n key: "[UsedLoc] [GhostLoc]"\n',
    )
    usage_scan = SL.ScriptedLocalisation.get_all_used_localisations

    def staged_usage_only(*args, staged_files=None, **kwargs):
        if staged_files is None:
            raise AssertionError("repo-wide usage scan ran")
        return usage_scan(*args, staged_files=staged_files, **kwargs)

    monkeypatch.setattr(
        SL.ScriptedLocalisation, "get_all_used_localisations", staged_usage_only
    )
    validator = _staged(SL.Validator(str(tmp_path), use_colors=False, workers=4), yml)
    _forbid(monkeypatch, validator, "_get_pool")

    validator.run_validations()

    assert _rows(validator) == [
        (
            "missing-scripted-loc",
            "ghostloc",
            "localisation/english/use_l_english.yml",
            2,
        )
    ]


def test_staged_scripted_loc_definition_still_reads_unstaged_consumers(
    tmp_path, write_path
):
    defs = write_path(tmp_path, "common/scripted_localisation/defs.txt", _SLOC_DEFS)
    write_path(tmp_path, "interface/use.gui", 'text = "[UsedLoc]"\n')
    validator = _staged(SL.Validator(str(tmp_path), use_colors=False, workers=1), defs)

    validator.run_validations()

    assert _rows(validator) == [
        (
            "unused-scripted-loc",
            "orphanloc",
            "common/scripted_localisation/defs.txt",
            5,
        )
    ]
