"""Check that entity clone parents and attachment targets are declared."""

from functools import partial
from pathlib import Path

import disk_cache
from equipment_variant_context import script_nodes, value
from validator_common import BaseValidator, FileOpener, list_files, run_validator_main

ENTITY_DIRS = ("gfx/entities", "gfx/models")
VANILLA_ENTITIES = Path(__file__).with_name("vanilla_entities.txt")


def _parse_entities(text: str) -> tuple[set[str], list[tuple[str, str, str, int]]]:
    names = set()
    references = []
    for entity in script_nodes(text):
        if entity.key != "entity" or entity.op != "=":
            continue
        name = value(entity, "name")
        if not name:
            continue
        names.add(name.casefold())
        for field in entity.children:
            if field.op != "=":
                continue
            if field.key == "clone" and field.value:
                references.append((name, "clone", field.value.strip('"'), field.line))
            if field.key == "attach" and field.value is None:
                for target in field.children:
                    if target.key != "name" and target.op == "=" and target.value:
                        references.append(
                            (name, "attach", target.value.strip('"'), target.line)
                        )
    return names, references


class Validator(BaseValidator):
    TITLE = "ENTITY REFERENCE VALIDATION"
    STAGED_EXTENSIONS = [".asset", ".gfx"]
    STAGED_INCLUDE_MISSING = True

    def validate_entity_references(self):
        if self.staged_only and not self.staged_touches(ENTITY_DIRS):
            return
        root = Path(self.mod_path)
        entities = {}
        for directory in ENTITY_DIRS:
            for path in list_files(root / directory, ("*.asset", "*.gfx")):
                text = FileOpener.open_text_file(path)
                entities[path] = disk_cache.per_file_cached_by_content(
                    self.mod_path,
                    "entity_references",
                    path,
                    text,
                    partial(_parse_entities, text),
                )
        if not any(references for _, references in entities.values()):
            return
        defined = set()
        for line in VANILLA_ENTITIES.read_text(encoding="utf-8").splitlines():
            entry = line.strip()
            if entry and not entry.startswith("#"):
                defined.add(entry.casefold())
        for names, _ in entities.values():
            defined.update(names)
        for path, (_, references) in entities.items():
            relative = Path(path).relative_to(root).as_posix()
            for name, kind, target, line in references:
                if target.casefold() not in defined:
                    self.add_warning(
                        f"entity-missing-{kind}",
                        f"Entity '{name}' references undefined {kind} target '{target}'",
                        relative,
                        line,
                    )

    def run_validations(self):
        self.validate_entity_references()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate entity clone and attachment references")
