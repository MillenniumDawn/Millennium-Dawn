"""Tests for validate_events.py call scanning: long-form calls, malformed
calls, undefined/typed fires, event pictures, and the pool workers' behaviour
on files they cannot or must not read.

Every scanner here runs in a worker process in production, so an unreadable or
skipped file has to come back empty rather than raise — a raising worker takes
the whole pool down and the check silently reports nothing.
"""

import os

import pytest
import validate_events as V
from shared.suite import write_under_str as _write


def _validator(tmp_path):
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def _sprite_index(*names):
    """A sprite index above the validator's 1000-sprite sanity floor."""
    return frozenset({f"GFX_filler_{i}" for i in range(1000)} | set(names))


# ---------------------------------------------------------------------------
# Pool workers on unreadable / skipped files
# ---------------------------------------------------------------------------


_WORKERS = [
    (V.scan_event_definitions, set()),
    (V.scan_event_definition_types, []),
    (V.scan_event_fires, []),
    (V.scan_typed_event_fires, []),
    (V.scan_dynamic_event_namespaces, set()),
    (V.scan_date_gated_events, []),
    (V.scan_event_fire_graph, []),
    (V.scan_invalid_event_calls, []),
    (V.scan_probability_rolled_fires, set()),
    (V.count_event_ids_in_file, {}),
]

# scan_event_definitions / scan_event_definition_types read with skip=False:
# an event definition counts wherever it lives.
_SKIP_AWARE_WORKERS = [
    (worker, empty)
    for worker, empty in _WORKERS
    if worker not in (V.scan_event_definitions, V.scan_event_definition_types)
]


@pytest.mark.parametrize("worker, empty", _WORKERS)
def test_worker_returns_empty_for_an_unreadable_file(tmp_path, worker, empty):
    assert worker((str(tmp_path / "events" / "gone.txt"), frozenset())) == empty


@pytest.mark.parametrize("worker, empty", _SKIP_AWARE_WORKERS)
def test_worker_skips_non_content_directories(tmp_path, worker, empty):
    path = _write(tmp_path, "tools/helper.txt", "country_event = foo.1\n")
    assert worker((path, frozenset())) == empty


def test_picture_worker_skips_unreadable_and_ignored_files(tmp_path):
    assert V._extract_event_pictures(str(tmp_path / "events" / "gone.txt")) == []
    skipped = _write(tmp_path, "tools/helper.txt", "picture = GFX_x\n")
    assert V._extract_event_pictures(skipped) == []


def test_fire_only_once_worker_survives_an_unreadable_file(tmp_path):
    args = (str(tmp_path / "common" / "gone.txt"), frozenset({"foo.1"}), str(tmp_path))
    assert V.scan_fire_only_once_in_loop(args) == []


def test_fire_only_once_worker_short_circuits_files_with_no_event_calls(tmp_path):
    path = _write(
        tmp_path,
        "common/scripted_effects/00_fx.txt",
        "fx = {\n\tevery_country = { add_political_power = 5 }\n}\n",
    )
    assert (
        V.scan_fire_only_once_in_loop((path, frozenset({"foo.1"}), str(tmp_path))) == []
    )


def test_fire_only_once_worker_survives_a_stray_closing_brace(tmp_path):
    """An unbalanced `}` must not desync the scope stack for the rest of the
    file — every finding after it would otherwise be wrong."""
    path = _write(
        tmp_path,
        "common/scripted_effects/00_fx.txt",
        "}\nevery_country = {\n\tcountry_event = foo.1\n}\n",
    )
    findings = V.scan_fire_only_once_in_loop(
        (path, frozenset({"foo.1"}), str(tmp_path))
    )
    assert len(findings) == 1
    assert "fire_only_once event foo.1 fired inside" in findings[0]


# ---------------------------------------------------------------------------
# Definition / fire parsing edge cases
# ---------------------------------------------------------------------------


def test_unclosed_event_block_is_not_a_definition(tmp_path):
    path = _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n\tid = foo.1\n\ttitle = foo.1.t\n",
    )
    assert V.scan_event_definitions((path, frozenset())) == set()


def test_fire_block_without_an_id_is_ignored(tmp_path):
    path = _write(
        tmp_path,
        "common/f.txt",
        "x = {\n\tcountry_event = { days = 3 }\n\tcountry_event = { id = real.1 }\n}\n",
    )
    assert {f[0] for f in V.scan_event_fires((path, frozenset()))} == {"real.1"}


def test_option_trigger_is_not_the_events_own_gate(tmp_path):
    """Only a depth-0 `trigger = { }` gates the event itself."""
    path = _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n"
        "\t\tname = foo.1.a\n"
        "\t\ttrigger = { date > 2005.1.1 }\n"
        "\t}\n"
        "}\n",
    )
    assert V.scan_date_gated_events((path, frozenset())) == []


def test_self_firing_event_is_not_its_own_parent(tmp_path):
    path = _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = loop.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n"
        "\t\tname = loop.1.a\n"
        "\t\tcountry_event = { id = loop.1 days = 30 }\n"
        "\t\tcountry_event = next.1\n"
        "\t}\n"
        "}\n",
    )
    assert V.scan_event_fire_graph((path, frozenset())) == [("loop.1", "next.1")]


def test_scheduled_chain_walk_terminates_on_a_parent_cycle():
    parents = {"a.1": {"b.1"}, "b.1": {"a.1"}}
    assert V._is_scheduled_chain("a.1", set(), parents) is False
    assert V._is_scheduled_chain("a.1", {"b.1"}, parents) is True


# ---------------------------------------------------------------------------
# Long-form event calls
# ---------------------------------------------------------------------------


def test_long_form_id_only_call_flagged_once_per_site(tmp_path):
    path = _write(
        tmp_path,
        "common/national_focus/GER.txt",
        "reward = { country_event = { id = foo.1 } country_event = { id = foo.1 } }\n"
        "other = { news_event = { id = foo.2 } }\n"
        "kept = { country_event = { id = foo.3 days = 3 } }\n",
    )
    relative = os.path.join("common", "national_focus", "GER.txt")
    assert V.process_txt_for_long_form_events((path, str(tmp_path))) == [
        f"{relative}:1 - country_event = {{ id = foo.1 }}"
        " → use shorthand `country_event = foo.1`",
        f"{relative}:2 - news_event = {{ id = foo.2 }}"
        " → use shorthand `news_event = foo.2`",
    ]


def test_long_form_worker_skips_unreadable_and_ignored_files(tmp_path):
    skipped = _write(tmp_path, "tools/helper.txt", "country_event = { id = foo.1 }\n")
    assert V.process_txt_for_long_form_events((skipped, str(tmp_path))) == []
    missing = str(tmp_path / "common" / "gone.txt")
    assert V.process_txt_for_long_form_events((missing, str(tmp_path))) == []


def test_long_form_check_reports_through_the_validator(tmp_path):
    _write(
        tmp_path,
        "common/national_focus/GER.txt",
        "reward = { country_event = { id = foo.1 } }\n",
    )
    v = _validator(tmp_path)
    v.validate_event_call_long_form()
    assert len(v._issues) == 1
    assert v._issues[0].file == "common/national_focus/GER.txt"
    assert v._issues[0].line == 1


# ---------------------------------------------------------------------------
# Malformed calls, fire types and undefined fires
# ---------------------------------------------------------------------------


def test_malformed_calls_reported_with_their_shape(tmp_path):
    _write(
        tmp_path,
        "common/f.txt",
        "event_country = foo.1\ncountry_event { id = foo.2 days = 3 }\n",
    )
    v = _validator(tmp_path)
    v.validate_invalid_event_calls()
    assert [(i.message, i.line) for i in v._issues] == [
        ("event_country = foo.1 - use an event effect keyword", 1),
        ("country_event { id = foo.2 } - missing '='", 2),
    ]
    assert {i.category for i in v._issues} == {"malformed-event-fire"}


def test_matching_fire_type_is_not_flagged(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "news_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n",
    )
    _write(tmp_path, "common/f.txt", "x = { news_event = foo.1 }\n")
    v = _validator(tmp_path)
    v.validate_event_fire_types()
    assert v._issues == []
    assert v._get_event_definition_types() == {"foo.1": "news_event"}


def test_undefined_fire_reported_once_per_id(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = real.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = real.1.a }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/f.txt",
        "x = {\n"
        "\tcountry_event = real.1\n"
        "\tcountry_event = ghost.1\n"
        "\tcountry_event = ghost.1\n"
        "\tcountry_event = dyn.[EVENT_ID]\n"
        "\tcountry_event = dyn.4\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_undefined_event_fires()
    relative = os.path.join("common", "f.txt")
    assert [i.message for i in v._issues] == [
        f"ghost.1 - fired from {relative}:3, no event defines it"
    ]
    assert v._issues[0].category == "undefined-event-fire"


def test_event_fire_caches_are_reused(tmp_path):
    _write(tmp_path, "common/f.txt", "x = { country_event = foo.1 }\n")
    v = _validator(tmp_path)
    assert v._get_event_fires() is v._get_event_fires()
    assert v._get_typed_event_fires() is v._get_typed_event_fires()
    assert [f[0] for f in v._get_event_fires()] == ["foo.1"]
    assert v._rel_posix(str(tmp_path / "common" / "f.txt")) == "common/f.txt"


def test_empty_on_actions_file_contributes_no_random_event_ids(tmp_path):
    _write(tmp_path, "common/on_actions/00_empty.txt", "")
    v = _validator(tmp_path)
    assert v._get_random_event_ids() == set()


# ---------------------------------------------------------------------------
# Event pictures
# ---------------------------------------------------------------------------


EVENT_WITH_PICTURE = """country_event = {
\tid = foo.1
\tis_triggered_only = yes
\tpicture = GFX_SPRITE
\toption = { name = foo.1.a }
}
"""


def _event_with_picture(sprite):
    return EVENT_WITH_PICTURE.replace("GFX_SPRITE", sprite)


def test_missing_event_picture_is_an_error(tmp_path, monkeypatch):
    _write(tmp_path, "events/Ev.txt", _event_with_picture("GFX_ghost"))
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_real")
    )
    v = _validator(tmp_path)
    v.validate_event_pictures()
    assert [(i.message, i.file, i.line) for i in v._issues] == [
        ("GFX_ghost", "Ev.txt", 4)
    ]
    assert v.errors_found == 1
    assert v._issues[0].category == "missing-event-picture"


def test_defined_event_picture_is_clean(tmp_path, monkeypatch):
    _write(tmp_path, "events/Ev.txt", _event_with_picture("GFX_real"))
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_real")
    )
    v = _validator(tmp_path)
    v.validate_event_pictures()
    assert v._issues == []


def test_repeated_picture_reference_on_one_line_reported_once(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "events/Ev.txt",
        _event_with_picture("GFX_ghost picture = GFX_ghost"),
    )
    monkeypatch.setattr(
        V, "build_sprite_index", lambda *a, **kw: _sprite_index("GFX_real")
    )
    v = _validator(tmp_path)
    v.validate_event_pictures()
    assert len(v._issues) == 1


def test_picture_check_skips_when_no_event_files_are_in_scope(tmp_path, monkeypatch):
    """No events to check means the sprite index is never even built."""

    def _fail(*args, **kwargs):
        raise AssertionError("sprite index built with no event files in scope")

    _write(tmp_path, "common/f.txt", "x = { country_event = foo.1 }\n")
    monkeypatch.setattr(V, "build_sprite_index", _fail)
    v = _validator(tmp_path)
    v.validate_event_pictures()
    assert v._issues == []


def test_picture_check_skips_when_the_sprite_index_failed_to_load(
    tmp_path, monkeypatch
):
    """A near-empty index means the .gfx files did not load; flagging every
    picture would be thousands of false errors."""
    _write(tmp_path, "events/Ev.txt", _event_with_picture("GFX_ghost"))
    monkeypatch.setattr(V, "build_sprite_index", lambda *a, **kw: frozenset({"GFX_a"}))
    v = _validator(tmp_path)
    v.validate_event_pictures()
    assert v._issues == []
    assert any("skipping the picture check" in line for line in v.output_lines)


# ---------------------------------------------------------------------------
# fire_only_once short circuit and the full run
# ---------------------------------------------------------------------------


def test_fire_only_once_check_short_circuits_without_declarations(
    tmp_path, monkeypatch
):
    """With nothing declared fire_only_once there is nothing to scan for, so
    the repo-wide file walk must not run at all."""
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/scripted_effects/00_fx.txt",
        "fx = {\n\tevery_country = { country_event = foo.1 }\n}\n",
    )
    v = _validator(tmp_path)
    v._get_fire_only_once_ids()

    def _fail(*args, **kwargs):
        raise AssertionError("scanned for in-loop fires with no fire_only_once events")

    monkeypatch.setattr(v, "_pool_map", _fail)
    v.validate_fire_only_once_in_loop()
    assert v._issues == []


MOD_EVENTS = """add_namespace = foo

country_event = {
\tid = foo.1
\tis_triggered_only = yes
\tfire_only_once = yes
\ttitle = foo.1.t
\tdesc = foo.1.d
\toption = {
\t\tname = foo.1.a
\t}
}
"""


def test_run_validations_executes_every_check(tmp_path):
    _write(tmp_path, "events/Ev.txt", MOD_EVENTS)
    _write(
        tmp_path,
        "localisation/english/md_l_english.yml",
        'l_english:\n foo.1.t:0 "T"\n foo.1.d:0 "D"\n foo.1.a:0 "A"\n',
    )
    _write(
        tmp_path,
        "common/scripted_effects/00_fx.txt",
        "fx = {\n\tcountry_event = foo.1\n}\n",
    )
    v = _validator(tmp_path)
    v.run_validations()
    assert v._issues == []
    assert v.errors_found == 0
    assert v.warnings_found == 0
