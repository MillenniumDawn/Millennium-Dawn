"""Variant registry persistence, duplicate creation, and conservative rescan failures."""

import os
import subprocess

import pytest
import validate_oob_units as oob
from shared.suite import write_tree
from shared.suite import write_under as write

_SWE = "history/countries/SWE - Sweden.txt"
_SOV = "history/countries/SOV - Russia.txt"
_EVENT = "events/Purchase.txt"
_VARIANT = 'create_equipment_variant = { name = "Design" type = infantry_weapons_2 }\n'
_SCOPED = "SWE = {\n" + _VARIANT + "}\n"


def registry(files):
    return oob.build_variant_registry(
        (path, oob.created_variant_spans(text)) for path, text in files.items()
    )


# case: (source files, number of duplicate-creation warnings)
_DUPLICATE_CASES = {
    "unique creation": ({_SWE: _VARIANT}, 0),
    "same identity twice": ({_SWE: _VARIANT * 2}, 1),
    "one warning per repeated creation": ({_SWE: _VARIANT * 3}, 2),
    "different names": ({_SWE: _VARIANT + _VARIANT.replace("Design", "Other")}, 0),
    "different types": (
        {_SWE: _VARIANT + _VARIANT.replace("infantry_weapons_2", "infantry_weapons_3")},
        0,
    ),
    "different producers": ({_SWE: _VARIANT, _SOV: _VARIANT}, 0),
    "cross-file explicit producer": ({_SWE: _VARIANT, _EVENT: _SCOPED}, 1),
    "unknown producer is not a proven duplicate": ({_EVENT: _VARIANT * 2}, 0),
    "dynamic producer is not the history owner": (
        {_SWE: "random_country = {\n" + _VARIANT * 2 + "}\n"},
        0,
    ),
    "dynamic equipment type": (
        {_SWE: _VARIANT.replace("infantry_weapons_2", "$TYPE$") * 2},
        0,
    ),
    "dynamic name": ({_SWE: _VARIANT.replace("Design", "[?variant_name]") * 2}, 0),
    "case-sensitive names": (
        {_SWE: _VARIANT + _VARIANT.replace("Design", "design")},
        0,
    ),
    "parent version does not make a new name": (
        {_SWE: _VARIANT + _VARIANT.replace("type =", "parent_version = 1 type =")},
        1,
    ),
    "exclusive sibling DLC branches": (
        {
            _SWE: 'if = { limit = { has_dlc = "No Step Back" }\n'
            + _VARIANT
            + "}\nelse = {\n"
            + _VARIANT
            + "}\n"
        },
        0,
    ),
    "exclusive nested DLC branches": (
        {
            _SWE: 'if = { limit = { has_dlc = "No Step Back" }\n'
            + _VARIANT
            + "else = {\n"
            + _VARIANT
            + "}\n}\n"
        },
        0,
    ),
    "exclusive path DLC contexts": (
        {"events/Purchase_nsb.txt": _SCOPED, "events/Purchase_nonnsb.txt": _SCOPED},
        0,
    ),
    "overlapping DLC contexts": (
        {
            _SWE: 'if = { limit = { has_dlc = "No Step Back" }\n'
            + _VARIANT
            + '}\nif = { limit = { has_dlc = "By Blood Alone" }\n'
            + _VARIANT
            + "}\n"
        },
        1,
    ),
    "contradictory DLC gates": (
        {
            _SWE: 'if = { limit = { has_dlc = "No Step Back" }\nif = { limit = { NOT = { has_dlc = "No Step Back" } }\n'
            + _VARIANT * 2
            + "}\n}\n"
        },
        0,
    ),
    "exclusive unknown condition branches": (
        {
            _SWE: "if = { limit = { has_country_flag = test }\n"
            + _VARIANT
            + "}\nelse_if = { limit = { has_country_flag = other }\n"
            + _VARIANT
            + "}\nelse = {\n"
            + _VARIANT
            + "}\n"
        },
        0,
    ),
    "duplicate inside one conditional branch": (
        {_SWE: "if = { limit = { has_country_flag = test }\n" + _VARIANT * 2 + "}\n"},
        1,
    ),
    "independent conditional branches can overlap": (
        {
            _SWE: "if = { limit = { has_country_flag = test }\n"
            + _VARIANT
            + "}\nif = { limit = { has_country_flag = other }\n"
            + _VARIANT
            + "}\n"
        },
        1,
    ),
    "mutually exclusive event options": (
        {
            _EVENT: "country_event = {\noption = {\n"
            + _SCOPED
            + "}\noption = {\n"
            + _SCOPED
            + "}\n}\n"
        },
        0,
    ),
    "mutually exclusive random outcomes": (
        {
            _EVENT: "SWE = { random_list = {\n50 = {\n"
            + _VARIANT
            + "}\n50 = {\n"
            + _VARIANT
            + "}\n}\n}\n"
        },
        0,
    ),
    "tooltips do not create variants": (
        {
            _SWE: _VARIANT
            + "effect_tooltip = {\n"
            + _VARIANT
            + "}\ncustom_effect_tooltip = {\n"
            + _VARIANT
            + "}\n"
        },
        0,
    ),
    "different history dates can repeat a creation": (
        {_SWE: "2000.1.1 = {\n" + _VARIANT + "}\n2017.1.1 = {\n" + _VARIANT + "}\n"},
        1,
    ),
}


@pytest.mark.parametrize(
    "files, expected", _DUPLICATE_CASES.values(), ids=_DUPLICATE_CASES
)
def test_duplicate_variant_creations(files, expected):
    findings = oob.check_duplicate_variant_creations(registry(files))

    assert len(findings) == expected
    assert all(issue.severity == "warning" for issue in findings)
    assert all(issue.category == "duplicate-equipment-variant" for issue in findings)
    assert all("also defined at " in issue.message for issue in findings)


def test_duplicate_creation_reports_both_locations():
    findings = oob.check_duplicate_variant_creations(registry({_SWE: _VARIANT * 2}))

    assert [(issue.file, issue.line) for issue in findings] == [(_SWE, 2)]
    assert findings[0].message == (
        'SWE creates named variant "Design" for infantry_weapons_2 '
        "more than once in potentially overlapping contexts; "
        f"also defined at {_SWE}:1"
    )


@pytest.mark.parametrize("staged", [_EVENT, _SWE], ids=["earlier path", "later path"])
def test_staged_duplicate_creation_is_reported_on_the_staged_file(tmp_path, staged):
    write_tree(tmp_path, {_SWE: _VARIANT, _EVENT: _SCOPED})
    validator = oob.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = [str(tmp_path / staged)]

    validator.validate_duplicate_variant_creations()

    assert [(issue.file, issue.severity) for issue in validator._issues] == [
        (staged, "warning")
    ]
    assert validator.errors_found == 0
    assert validator.warnings_found == 1


def test_default_names_are_not_explicit_variant_creations(tmp_path):
    write_tree(
        tmp_path,
        {
            _SWE: _VARIANT,
            "common/units/equipment/test.txt": "equipments = { infantry_weapons_2 = {} infantry_weapons_3 = {} }",
            "localisation/english/equipment_l_english.yml": 'l_english:\n SWE_infantry_weapons_2: "Design"\n SWE_infantry_weapons_3: "Base model"\n',
        },
    )
    validator = oob.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.validate_duplicate_variant_creations()

    assert list(validator._get_variant_registry().by_identity) == [
        ("SWE", "infantry_weapons_2", "Design")
    ]
    assert validator._issues == []


def test_warm_variant_registry_reuses_persisted_parsing(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    write_tree(tmp_path, {_SWE: _VARIANT, _SOV: _VARIANT})
    cold = oob.Validator(str(tmp_path), workers=1)._get_variant_registry()

    def must_not_parse(*_args):
        raise AssertionError("unchanged variant sources should use the disk cache")

    monkeypatch.setattr(oob, "created_variant_spans", must_not_parse)
    monkeypatch.setattr(oob, "_parse_variant_definitions", must_not_parse)
    warm = oob.Validator(str(tmp_path), workers=1)._get_variant_registry()

    assert warm == cold
    assert set(warm.by_identity) == {
        ("SWE", "infantry_weapons_2", "Design"),
        ("SOV", "infantry_weapons_2", "Design"),
    }


# case: (replacement source tree, files that must be reparsed)
_CACHE_CHANGES = {
    "same-size edit with unchanged timestamps": (
        {_SWE: _VARIANT.replace("Design", "Rename"), _SOV: _VARIANT},
        [_SWE],
    ),
    "deleted source": ({_SOV: _VARIANT}, []),
    "renamed producer": (
        {"history/countries/CHI - China.txt": _VARIANT, _SOV: _VARIANT},
        ["history/countries/CHI - China.txt"],
    ),
    "added source": ({_SWE: _VARIANT, _SOV: _VARIANT, _EVENT: _SCOPED}, [_EVENT]),
    "changed surrounding DLC context": (
        {
            _SWE: 'if = { limit = { has_dlc = "No Step Back" }\n' + _VARIANT + "}\n",
            _SOV: _VARIANT,
        },
        [_SWE],
    ),
}


@pytest.mark.parametrize(
    "updated, reparsed", _CACHE_CHANGES.values(), ids=_CACHE_CHANGES
)
def test_variant_registry_cache_invalidates_current_sources(
    tmp_path, monkeypatch, updated, reparsed
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    original = {_SWE: _VARIANT, _SOV: _VARIANT}
    write_tree(tmp_path, original)
    oob.Validator(str(tmp_path), workers=1)._get_variant_registry()
    stat = (tmp_path / _SWE).stat()
    for path in original.keys() - updated.keys():
        (tmp_path / path).unlink()
    write_tree(tmp_path, updated)
    if _SWE in updated and len(updated[_SWE]) == len(_VARIANT):
        os.utime(tmp_path / _SWE, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    parsed = []
    parse = oob._parse_variant_definitions

    def record(path, variants):
        parsed.append(path)
        return parse(path, variants)

    monkeypatch.setattr(oob, "_parse_variant_definitions", record)
    current = oob.Validator(str(tmp_path), workers=1)._get_variant_registry()

    assert sorted(parsed) == sorted(reparsed)
    monkeypatch.setenv("MD_NO_CACHE", "1")
    assert current == registry(updated)


def test_no_cache_bypasses_persisted_variant_registry(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    write_tree(tmp_path, {_SWE: _VARIANT})
    cached = oob.Validator(str(tmp_path), workers=1)._get_variant_registry()
    parsed = []
    parse = oob._parse_variant_definitions

    def record(path, variants):
        parsed.append(path)
        return parse(path, variants)

    monkeypatch.setattr(oob, "_parse_variant_definitions", record)
    uncached = oob.Validator(
        str(tmp_path), workers=1, no_cache=True
    )._get_variant_registry()

    assert uncached == cached
    assert parsed == [_SWE]


# case: (selected sources, current contents, rescan consumers)
_NO_GIT_CASES = {
    "no selected sources": ([], _VARIANT, False),
    "variant source": ([_SWE], _VARIANT, True),
    "unrelated source": ([_SWE], "add_political_power = 1", False),
}


@pytest.mark.parametrize(
    "paths, content, expected", _NO_GIT_CASES.values(), ids=_NO_GIT_CASES
)
def test_variant_rescan_without_git_is_conservative(tmp_path, paths, content, expected):
    write(tmp_path, _SWE, content)
    assert (
        oob._variant_definitions_changed(
            str(tmp_path), [str(tmp_path / path) for path in paths]
        )
        is expected
    )


_GIT_FAILURES = {
    "unavailable git": OSError("git unavailable"),
    "failed diff": subprocess.CalledProcessError(128, ["git", "diff"]),
    "timed out diff": subprocess.TimeoutExpired(["git", "diff"], 15),
}


@pytest.mark.parametrize("failure", _GIT_FAILURES.values(), ids=_GIT_FAILURES)
def test_variant_rescan_widens_and_reports_git_failures(
    tmp_path, monkeypatch, capsys, failure
):
    (tmp_path / ".git").mkdir()

    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(oob.subprocess, "run", fail)

    assert oob._variant_definitions_changed(str(tmp_path), [str(tmp_path / _SWE)])
    assert (
        "Cannot compare variant definitions; rescanning consumers"
        in capsys.readouterr().err
    )
