"""Tests for entity clone and attachment references."""

import pytest
import validate_entity_references as V
from shared.suite import (
    build_validator,
    checks_called_by_run,
    run_validator,
    write_tree,
)

_ENTITY = "gfx/entities/child.asset"
_PARENT = "gfx/models/units/parent.gfx"

# case: (entity body, expected (category, target, line) findings)
_REFERENCES = {
    "missing clone": ('clone = "absent"', [("entity-missing-clone", "absent", 3)]),
    "missing attachment": (
        'attach = { name = "slot"\n hand = "absent" }',
        [("entity-missing-attach", "absent", 4)],
    ),
    "declared in another file": ('clone = "MOD_PARENT"', []),
    "vanilla attachment": ("attach = { name = slot hand = Vanilla_Parent }", []),
    "comment": ('# clone = "absent"', []),
    "quoted field": ('label = "clone = absent"', []),
    "nested field": ('state = { clone = "absent" }', []),
}


@pytest.mark.parametrize("body, expected", _REFERENCES.values(), ids=_REFERENCES)
def test_entity_references(tmp_path, monkeypatch, body, expected):
    manifest = tmp_path / "vanilla_entities.txt"
    write_tree(
        tmp_path,
        {
            manifest.name: "# manifest\nvanilla_parent\n",
            _PARENT: "entity = { name = mod_parent }\n",
            _ENTITY: f'entity = {{\n name = "child"\n {body}\n}}\n',
        },
    )
    monkeypatch.setattr(V, "VANILLA_ENTITIES", manifest)
    validator = run_validator(V.Validator, tmp_path)

    assert [(i.category, i.line) for i in validator._issues] == [
        (category, line) for category, _target, line in expected
    ]
    for issue, (_, target, _) in zip(validator._issues, expected, strict=True):
        assert issue.file == _ENTITY and issue.severity == "warning"
        assert f"target '{target}'" in issue.message


def test_staged_definition_removal_checks_unchanged_reference(tmp_path, monkeypatch):
    write_tree(tmp_path, {_ENTITY: "entity = { name = child clone = gone }\n"})
    monkeypatch.setenv("MD_STAGED_FILES", _PARENT)
    validator = run_validator(V.Validator, tmp_path, staged_only=True)

    assert [i.file for i in validator._issues] == [_ENTITY]


def test_run_validations_calls_every_check(tmp_path, monkeypatch):
    validator = build_validator(V.Validator, tmp_path)
    called, checks = checks_called_by_run(validator, monkeypatch)
    assert called == checks
