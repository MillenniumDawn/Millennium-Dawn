"""Tests for validate_events.py call scanning: long-form calls, malformed
calls, undefined/typed fires, event pictures, and the pool workers' behaviour
on files they cannot or must not read.

Every scanner here runs in a worker process in production, so an unreadable or
skipped file has to come back empty rather than raise — a raising worker takes
the whole pool down and the check silently reports nothing.
"""

import os
from multiprocessing import get_context

import pytest
import validate_events as V
import validator_common
from shared.suite import call_site_scan
from shared.suite import write_under_str as _write


def _validator(tmp_path):
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def _sprite_index(*names):
    """A sprite index above the validator's 1000-sprite sanity floor."""
    return frozenset({f"GFX_filler_{i}" for i in range(1000)} | set(names))


# ---------------------------------------------------------------------------
# Pool workers on unreadable / skipped files
# ---------------------------------------------------------------------------


_WORKERS: list[tuple[object, object]] = [
    (V.scan_event_definition_types, []),
    (V.scan_date_gated_events, []),
    (V.scan_date_bounded_events, []),
    (V.scan_event_fire_graph, []),
    (V.scan_probability_rolled_fires, set()),
]

# scan_event_definition_types reads with skip=False: an event definition counts
# wherever it lives.
_SKIP_AWARE_WORKERS = [
    (worker, empty)
    for worker, empty in _WORKERS
    if worker is not V.scan_event_definition_types
]

_CALL_SITE_EMPTY = [
    ("longform", []),
    ("invalid", []),
    ("typed", []),
    ("counts", {}),
    ("dynamic", set()),
    ("fof", []),
    ("major", []),
]


@pytest.mark.parametrize("worker, empty", _WORKERS)
def test_worker_returns_empty_for_an_unreadable_file(tmp_path, worker, empty):
    assert worker((str(tmp_path / "events" / "gone.txt"), frozenset())) == empty


@pytest.mark.parametrize("worker, empty", _SKIP_AWARE_WORKERS)
def test_worker_skips_non_content_directories(tmp_path, worker, empty):
    event = (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\ttrigger = { date > 2005.1.1 }\n"
        "\timmediate = { random = { chance = 5 country_event = foo.2 } }\n"
        "}\n"
    )
    skipped = _write(tmp_path, "tools/helper.txt", event)
    assert worker((skipped, frozenset())) == empty
    read = _write(tmp_path, "events/helper.txt", event)
    assert worker((read, frozenset())) != empty


@pytest.mark.parametrize("section, empty", _CALL_SITE_EMPTY)
def test_call_site_scan_is_empty_for_unreadable_and_ignored_files(
    tmp_path, section, empty
):
    tracked = frozenset({"foo.1"})
    gone = tmp_path / "events" / "gone.txt"
    assert call_site_scan(gone, section, tmp_path, tracked) == empty
    calls = (
        "every_country = { country_event = { id = foo.1 } }\n"
        "country_event { id = foo.2 }\n"
        "country_event = dyn.[EVENT_ID]\n"
    )
    skipped = _write(tmp_path, "tools/helper.txt", calls)
    assert call_site_scan(skipped, section, tmp_path, tracked) == empty
    read = _write(tmp_path, "common/helper.txt", calls)
    assert call_site_scan(read, section, tmp_path, tracked) != empty


def test_picture_worker_skips_unreadable_and_ignored_files(tmp_path):
    assert V._extract_event_pictures(str(tmp_path / "events" / "gone.txt")) == []
    skipped = _write(tmp_path, "tools/helper.txt", "picture = GFX_x\n")
    assert V._extract_event_pictures(skipped) == []


def test_fire_only_once_worker_short_circuits_files_with_no_event_calls(tmp_path):
    path = _write(
        tmp_path,
        "common/scripted_effects/00_fx.txt",
        "fx = {\n\tevery_country = { add_political_power = 5 }\n}\n",
    )
    assert call_site_scan(path, "fof", tmp_path, frozenset({"foo.1"})) == []


def test_fire_only_once_worker_survives_a_stray_closing_brace(tmp_path):
    """An unbalanced `}` must not desync the scope stack for the rest of the
    file — every finding after it would otherwise be wrong."""
    path = _write(
        tmp_path,
        "common/scripted_effects/00_fx.txt",
        "}\nevery_country = {\n\tcountry_event = foo.1\n}\n",
    )
    findings = call_site_scan(path, "fof", tmp_path, frozenset({"foo.1"}))
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
    assert V.scan_event_definition_types((path, frozenset())) == []


def test_fire_block_without_an_id_is_ignored(tmp_path):
    path = _write(
        tmp_path,
        "common/f.txt",
        "x = {\n\tcountry_event = { days = 3 }\n\tcountry_event = { id = real.1 }\n}\n",
    )
    assert {f[0] for f in call_site_scan(path, "typed", tmp_path)} == {"real.1"}


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
    assert call_site_scan(path, "longform", tmp_path) == [
        f"{relative}:1 - country_event = {{ id = foo.1 }}"
        " → use shorthand `country_event = foo.1`",
        f"{relative}:2 - news_event = {{ id = foo.2 }}"
        " → use shorthand `news_event = foo.2`",
    ]


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


def _validator_for_staged_event_change(tmp_path, definition, caller):
    event = _write(tmp_path, "events/Ev.txt", definition)
    _write(tmp_path, "common/f.txt", caller)
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator.staged_files = [event]
    return validator


def test_staged_event_type_change_rescans_unchanged_callers(tmp_path):
    validator = _validator_for_staged_event_change(
        tmp_path,
        "news_event = { id = foo.1 is_triggered_only = yes }\n",
        "x = { country_event = foo.1 }\n",
    )

    validator.validate_event_fire_types()

    assert [issue.category for issue in validator._issues] == [
        "event-fire-type-mismatch"
    ]


def test_staged_event_definition_removal_rescans_unchanged_callers(tmp_path):
    validator = _validator_for_staged_event_change(
        tmp_path,
        "country_event = { id = real.1 is_triggered_only = yes }\n",
        "x = { country_event = removed.1 }\n",
    )

    validator.validate_undefined_event_fires()

    assert [issue.category for issue in validator._issues] == ["undefined-event-fire"]
    assert "removed.1" in validator._issues[0].message


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


def test_event_fire_views_share_typed_scan(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    _write(tmp_path, "common/f.txt", "x = { country_event = foo.1 }\n")
    calls = []
    original = V._scan_typed_fires_text

    def wrapped(cleaned, filename):
        calls.append(filename)
        return original(cleaned, filename)

    monkeypatch.setattr(V, "_scan_typed_fires_text", wrapped)
    v = _validator(tmp_path)
    fires = v._get_event_fires()
    typed_fires = v._get_shared_call_site_scan()["typed"]

    assert calls == [str(tmp_path / "common" / "f.txt")]
    assert fires is v._get_event_fires()
    assert fires == [(eid, filename, line) for eid, _, filename, line in typed_fires]
    assert [f[0] for f in fires] == ["foo.1"]
    assert v._rel_posix(str(tmp_path / "common" / "f.txt")) == "common/f.txt"


def test_event_fires_hit_disk_cache_across_instances(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    path = _write(
        tmp_path,
        "common/f.txt",
        "x = {\n\tcountry_event = foo.1\n\tnews_event = { id = foo.2 }\n}\n",
    )
    calls = []
    original = V._scan_typed_fires_text

    def wrapped(cleaned, filename):
        calls.append(filename)
        return original(cleaned, filename)

    monkeypatch.setattr(V, "_scan_typed_fires_text", wrapped)
    first = _validator(tmp_path)._get_event_fires()
    assert calls == [path], "the first instance must scan and write the cache"

    monkeypatch.setattr(
        V,
        "_scan_typed_fires_text",
        lambda *_a: pytest.fail("the second instance must read the cached fires"),
    )
    second = _validator(tmp_path)._get_event_fires()
    assert second == first == [("foo.1", path, 2), ("foo.2", path, 3)]


def test_event_definition_types_hit_disk_cache_across_instances(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write(
        tmp_path,
        "events/Ev.txt",
        "news_event = {\n\tid = foo.1\n\tis_triggered_only = yes\n}\n",
    )
    first = _validator(tmp_path)._get_event_definition_types()
    calls = []
    original = V.scan_event_definition_types

    def wrapped(args):
        calls.append(args[0])
        return original(args)

    monkeypatch.setattr(V, "scan_event_definition_types", wrapped)
    second = _validator(tmp_path)._get_event_definition_types()
    assert calls == []
    assert second == first


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
\tpicture = GFX_event
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


# ---------------------------------------------------------------------------
# Shared call-site scan: prepared texts, line numbers, file gates, scope
# ---------------------------------------------------------------------------

_KEYWORDS = (
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
)


def _write_tree(root, files):
    return {relative: _write(root, relative, text) for relative, text in files.items()}


def _shared_scan(root, staged=(), workers=1):
    v = V.Validator(mod_path=str(root), use_colors=False, workers=workers)
    if staged:
        v.staged_only = True
        v.staged_files = list(staged)
    return v._get_shared_call_site_scan()


def _longform(rel, line, keyword, eid):
    return (
        f"{rel}:{line} - {keyword} = {{ id = {eid} }}"
        f" → use shorthand `{keyword} = {eid}`"
    )


def _in_loop(rel, line, message, eid):
    return f"{rel}:{line} - {message.format(eid=eid)}"


CALL_EDGES = (
    "news_event = first.1\n"
    "country_event = second.1\n"
    'log = "country_event = { id = quoted.1 }"\n'
    "# country_event = commented.1\n"
    "country_event { id = noeq.1 }\n"
    "event_country = rev.1\n"
    "country_event = { id = long.1 }\n"
    "news_event = last.1"
)


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_call_sites_keep_exact_lines_across_quotes_comments_and_file_edges(
    tmp_path, newline
):
    """Fires and long-form calls read comment-stripped text, so a call in a
    quoted string still counts there; malformed calls read quote-blanked text,
    so it does not. The first line is a fire and the last has no newline."""
    path = _write(tmp_path, "common/f.txt", CALL_EDGES.replace("\n", newline))
    rel = os.path.join("common", "f.txt")
    shared = _shared_scan(tmp_path)
    assert shared["typed"] == [
        ("first.1", "news_event", path, 1),
        ("second.1", "country_event", path, 2),
        ("last.1", "news_event", path, 8),
        ("quoted.1", "country_event", path, 3),
        ("long.1", "country_event", path, 7),
    ]
    assert shared["longform"] == [
        _longform(rel, 3, "country_event", "quoted.1"),
        _longform(rel, 7, "country_event", "long.1"),
    ]
    assert shared["invalid"] == [
        ("missing-equals", "country_event", "noeq.1", path, 5),
        ("reversed", "event_country", "rev.1", path, 6),
    ]


@pytest.mark.parametrize("keyword", _KEYWORDS)
def test_every_event_keyword_reaches_each_call_site_scan(tmp_path, keyword):
    reversed_keyword = "event_" + keyword.removesuffix("_event")
    path = _write(
        tmp_path,
        "common/f.txt",
        f"{keyword} = short.1\n"
        f"{keyword} = {{ id = block.1 days = 1 }}\n"
        f"{keyword} = {{ id = long.1 }}\n"
        f"{keyword} {{ id = noeq.1 }}\n"
        f"{keyword} = dyn.[EVENT_ID]\n"
        f"{reversed_keyword} = rev.1\n",
    )
    shared = _shared_scan(tmp_path)
    assert shared["typed"] == [
        ("short.1", keyword, path, 1),
        ("block.1", keyword, path, 2),
        ("long.1", keyword, path, 3),
    ]
    assert shared["longform"] == [
        _longform(os.path.join("common", "f.txt"), 3, keyword, "long.1")
    ]
    assert shared["invalid"] == [
        ("missing-equals", keyword, "noeq.1", path, 4),
        ("reversed", reversed_keyword, "rev.1", path, 6),
    ]
    assert shared["dynamic"] == {"dyn"}


def test_reversed_call_in_a_file_without_event_keywords_is_still_scanned(tmp_path):
    path = _write(tmp_path, "common/f.txt", "x = {\n\tevent_news = { id = rev.2 }\n}\n")
    assert _shared_scan(tmp_path)["invalid"] == [
        ("reversed", "event_news", "rev.2", path, 2)
    ]


def test_keyword_used_as_a_call_target_is_not_a_second_fire(tmp_path):
    """The fire scan resumes after each match, so a keyword consumed as another
    call's target never starts a fire of its own."""
    _write(tmp_path, "common/f.txt", "country_event = news_event = foo.1\n")
    assert _shared_scan(tmp_path)["typed"] == []


STAGED_EVENTS = (
    "country_event = {\n"
    "\tid = st.1\n"
    "\tis_triggered_only = yes\n"
    "\tfire_only_once = yes\n"
    "\toption = {\n"
    "\t\tname = st.1.a\n"
    "\t\tevery_country = {\n"
    "\t\t\tcountry_event = st.1\n"
    "\t\t\tnews_event = { id = st.2 }\n"
    "\t\t}\n"
    "\t\tcountry_event { id = st.2 }\n"
    "\t}\n"
    "}\n"
    "news_event = {\n"
    "\tid = st.2\n"
    "\tis_triggered_only = yes\n"
    "\tmajor = yes\n"
    "}\n"
)

UNSTAGED_CALLER = (
    "fx = {\n"
    "\tcountry_event = { id = st.1 }\n"
    "\tnews_event { id = st.2 }\n"
    "\tevery_country = {\n"
    "\t\tcountry_event = st.1\n"
    "\t\tnews_event = st.2\n"
    "\t}\n"
    "}\n"
)


def test_staged_event_file_keeps_scoped_findings_to_staged_files(tmp_path):
    """A staged events/ file widens the fire scan to every caller, but the
    long-form, malformed and in-loop checks still report only staged files."""
    paths = _write_tree(
        tmp_path,
        {
            "events/Ev.txt": STAGED_EVENTS,
            "common/scripted_effects/caller.txt": UNSTAGED_CALLER,
        },
    )
    event, caller = paths["events/Ev.txt"], paths["common/scripted_effects/caller.txt"]
    ev_rel = os.path.join("events", "Ev.txt")
    caller_rel = os.path.join("common", "scripted_effects", "caller.txt")

    full = _shared_scan(tmp_path)
    assert [finding.split(" - ")[0] for finding in full["longform"]] == [
        f"{caller_rel}:2",
        f"{ev_rel}:9",
    ]
    assert [(f, line) for *_, f, line in full["invalid"]] == [(caller, 3), (event, 11)]
    assert [finding.split(" - ")[0] for finding in full["fof"] + full["major"]] == [
        f"{caller_rel}:5",
        f"{ev_rel}:8",
        f"{caller_rel}:6",
        f"{ev_rel}:9",
    ]

    staged = _shared_scan(tmp_path, staged=[event])
    assert staged["longform"] == [_longform(ev_rel, 9, "news_event", "st.2")]
    assert staged["invalid"] == [("missing-equals", "country_event", "st.2", event, 11)]
    assert staged["fof"] == [_in_loop(ev_rel, 8, V._FOF_IN_LOOP_MSG, "st.1")]
    assert staged["major"] == [_in_loop(ev_rel, 9, V._MAJOR_IN_LOOP_MSG, "st.2")]
    assert sorted(
        (eid, line) for eid, _keyword, f, line in staged["typed"] if f == caller
    ) == [("st.1", 2), ("st.1", 5), ("st.2", 6)]


MOD_PATH_EVENTS = (
    "country_event = {\n"
    "\tid = mp.1\n"
    "\tis_triggered_only = yes\n"
    "\tfire_only_once = yes\n"
    "\tpicture = GFX_missing\n"
    "\ttrigger = { date > 2001.1.1 }\n"
    "\timmediate = { country_event = mp.2 }\n"
    "\toption = {\n"
    "\t\tname = mp.1.a\n"
    '\t\tlog = "mp.1.a"\n'
    "\t}\n"
    "}\n"
) + "".join(
    f"country_event = {{\n\tid = mp.{n}\n\tis_triggered_only = yes\n"
    f"\ttrigger = {{ date > 200{n}.1.1 }}\n}}\n"
    for n in (2, 3, 4)
)


def test_a_mod_root_inside_an_ignored_directory_is_still_scanned(tmp_path, monkeypatch):
    """Every per-file worker checks skips relative to the mod root. Under a
    `tools/` parent, an absolute-path check would skip the whole mod."""
    root = tmp_path / "tools" / "mod"
    _write_tree(
        root,
        {
            "events/Ev.txt": MOD_PATH_EVENTS,
            V._YEARLY_EFFECTS_REL: (
                "MD_event_on_startup_events = {\n"
                "\tevery_country = {\n"
                "\t\tcountry_event = { id = mp.1 }\n"
                "\t}\n"
                "}\n"
            ),
            "common/on_actions/00_on_actions.txt": (
                "on_actions = {\n\ton_daily = {\n\t\trandom = {\n"
                "\t\t\tchance = 5\n\t\t\tcountry_event = mp.3\n\t\t}\n\t}\n}\n"
            ),
        },
    )
    monkeypatch.setattr(V, "build_sprite_index", lambda *a, **kw: _sprite_index())
    v = _validator(root)
    v.validate_event_pictures()
    v.validate_option_log_without_effect()
    v.validate_date_gated_scheduling()
    v.validate_scheduled_date_bounds()
    v.validate_event_call_long_form()
    v.validate_fire_only_once_in_loop()

    yearly = V._YEARLY_EFFECTS_REL
    assert [(i.category, i.file, i.line, i.message) for i in v._issues] == [
        ("missing-event-picture", "Ev.txt", 5, "GFX_missing"),
        ("event-option-log-without-effect", "Ev.txt", 10, "mp.1.a"),
        (
            "date-gated-not-scheduled",
            "",
            0,
            f"mp.4 - events/Ev.txt:23 has a date > guard but nothing schedules it"
            f" from {yearly} (fired from: nothing)",
        ),
        (
            "scheduled-event-date-bound",
            "",
            0,
            f"mp.1 - events/Ev.txt:1 is scheduled from {yearly}, so the date bound"
            " in its trigger is redundant (remove it; drop the trigger block if"
            " nothing else is left)",
        ),
        (
            "Long-form event calls with only id (use shorthand instead)",
            yearly,
            3,
            _longform(yearly, 3, "country_event", "mp.1").split(" - ", 1)[1],
        ),
        (
            "fire-only-once-in-loop",
            yearly,
            3,
            V._FOF_IN_LOOP_MSG.format(eid="mp.1"),
        ),
    ]


def _pooled_caller(number):
    return (
        f"fx_{number} = {{\n" + "\n" * number + "\tevery_country = {\n"
        "\t\tcountry_event = st.1\n"
        "\t\tnews_event = { id = st.2 }\n"
        "\t}\n"
        "\tcountry_event = { id = st.1 }\n"
        "}\n"
    )


def test_pooled_shared_scan_matches_the_in_process_scan(tmp_path, monkeypatch):
    """Enough files to cross the pool threshold: the workers must rebuild every
    finding, line included, from their arguments alone."""
    monkeypatch.setenv("MD_NO_CACHE", "1")
    files = {"events/Ev.txt": STAGED_EVENTS}
    files.update(
        {f"common/scripted_effects/{n:02}.txt": _pooled_caller(n) for n in range(12)}
    )
    _write_tree(tmp_path, files)
    spawn_pool = get_context("spawn").Pool
    pools = []

    def counting_pool(*args, **kwargs):
        pools.append(kwargs.get("processes", args[0] if args else None))
        return spawn_pool(*args, **kwargs)

    monkeypatch.setattr(validator_common, "Pool", counting_pool)

    def run(workers):
        v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=workers)
        result = {}
        monkeypatch.setattr(
            v, "run_validations", lambda: result.update(v._get_shared_call_site_scan())
        )
        v.run_all_validations()
        assert v._pool is None
        return result

    pooled = run(2)
    assert pools == [2], "the shared scan did not run in a worker pool"
    in_process = run(1)
    assert pools == [2]
    assert pooled == in_process
    assert (len(pooled["fof"]), len(pooled["major"]), len(pooled["longform"])) == (
        13,
        13,
        25,
    )
    rel = os.path.join("common", "scripted_effects", "11.txt")
    assert _in_loop(rel, 14, V._FOF_IN_LOOP_MSG, "st.1") in pooled["fof"]
    assert _in_loop(rel, 15, V._MAJOR_IN_LOOP_MSG, "st.2") in pooled["major"]
    assert _longform(rel, 17, "country_event", "st.1") in pooled["longform"]
