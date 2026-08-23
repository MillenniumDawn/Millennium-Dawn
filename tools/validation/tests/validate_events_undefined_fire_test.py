"""Tests for validate_events.py: fires at an event ID no event file defines.

MD sets `replace_path = "events"`, so vanilla events never load and every fired
ID has to resolve inside the mod. A fire at an undefined ID compiles fine and
silently does nothing.

The definition scan brace-matches event blocks rather than keying off
indentation, because several event files indent their definitions one tab
deeper than the norm.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validate_events import (
    Validator,
    scan_event_definition_types,
    scan_event_definitions,
    scan_event_fires,
    scan_invalid_event_calls,
    scan_typed_event_fires,
)


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return str(p)


DEFINITION = """country_event = {
\tid = foo.1
\tis_triggered_only = yes
\toption = { name = foo.1.a }
}
"""

# Same event, but the whole block sits one tab deeper.
INDENTED_DEFINITION = """\tcountry_event = {
\t\tid = deep.1
\t\tis_triggered_only = yes
\t\toption = { name = deep.1.a }
\t}
"""


def test_definition_found(tmp_path):
    p = _write(tmp_path, "events/Ev.txt", DEFINITION)
    assert scan_event_definitions((p, frozenset())) == {"foo.1"}


def test_indented_definition_found(tmp_path):
    p = _write(tmp_path, "events/Ev.txt", INDENTED_DEFINITION)
    assert scan_event_definitions((p, frozenset())) == {"deep.1"}


def test_fire_block_is_not_a_definition(tmp_path):
    p = _write(
        tmp_path,
        "common/f.txt",
        "x = {\n\tcountry_event = { id = foo.1 days = 3 }\n}\n",
    )
    assert scan_event_definitions((p, frozenset())) == set()


def test_fires_short_and_block_form(tmp_path):
    p = _write(
        tmp_path,
        "common/f.txt",
        "x = {\n"
        "\tcountry_event = short.1\n"
        "\tcountry_event = { id = block.1 days = 3 }\n"
        "\tnews_event = { days = 2 id = reordered.1 }\n"
        "}\n",
    )
    assert {f[0] for f in scan_event_fires((p, frozenset()))} == {
        "short.1",
        "block.1",
        "reordered.1",
    }


def test_definition_and_fire_types_are_retained(tmp_path):
    definition = _write(
        tmp_path,
        "events/Ev.txt",
        DEFINITION.replace("country_event", "news_event"),
    )
    caller = _write(tmp_path, "common/f.txt", "country_event = foo.1\n")

    assert scan_event_definition_types((definition, frozenset())) == [
        ("foo.1", "news_event")
    ]
    assert scan_typed_event_fires((caller, frozenset())) == [
        ("foo.1", "country_event", caller, 1)
    ]


def test_type_mismatch_report_keeps_file_and_line(tmp_path):
    caller = _write(tmp_path, "common/f.txt", "country_event = foo.1\n")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator._definition_types_cache = {"foo.1": "news_event"}
    validator._typed_fires_cache = [("foo.1", "country_event", caller, 1)]

    validator.validate_event_fire_types()

    assert len(validator._issues) == 1
    assert validator._issues[0].file == "common/f.txt"
    assert validator._issues[0].line == 1


def test_malformed_call_scan_uses_staged_scope(tmp_path):
    staged = _write(tmp_path, "common/staged.txt", "country_event = foo.1\n")
    _write(tmp_path, "common/unstaged.txt", "event_country = foo.2\n")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = [staged]

    assert validator._get_scoped_fire_scan_args() == [(staged, frozenset())]


def test_reversed_and_missing_equals_calls_detected(tmp_path):
    caller = _write(
        tmp_path,
        "common/f.txt",
        "event_country = foo.1\ncountry_event { id = foo.2 days = 3 }\n",
    )

    assert scan_invalid_event_calls((caller, frozenset())) == [
        ("reversed", "event_country", "foo.1", caller, 1),
        ("missing-equals", "country_event", "foo.2", caller, 2),
    ]


def test_interpolated_id_skipped(tmp_path):
    """`UN.[ID]` has no literal form to resolve, so it must not be reported."""
    p = _write(tmp_path, "common/f.txt", "x = {\n\tcountry_event = UN.[ID]\n}\n")
    assert scan_event_fires((p, frozenset())) == []


def test_commented_fire_ignored(tmp_path):
    p = _write(tmp_path, "common/f.txt", "x = {\n\t#country_event = dead.1\n}\n")
    assert scan_event_fires((p, frozenset())) == []


def test_metadata_retains_event_without_id():
    from validate_events import _parse_event_metadata

    metadata, namespaces = _parse_event_metadata(
        "country_event = {\n\tis_triggered_only = yes\n\toption = { name = missing.id.a }\n}\n",
        "broken.txt",
    )

    assert namespaces == set()
    assert len(metadata) == 1
    assert metadata[0]["id"] is None
    assert metadata[0]["file"] == "broken.txt"
