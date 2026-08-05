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

from validate_events import scan_event_definitions, scan_event_fires


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


def test_interpolated_id_skipped(tmp_path):
    """`UN.[ID]` has no literal form to resolve, so it must not be reported."""
    p = _write(tmp_path, "common/f.txt", "x = {\n\tcountry_event = UN.[ID]\n}\n")
    assert scan_event_fires((p, frozenset())) == []


def test_commented_fire_ignored(tmp_path):
    p = _write(tmp_path, "common/f.txt", "x = {\n\t#country_event = dead.1\n}\n")
    assert scan_event_fires((p, frozenset())) == []
