"""Event checks that walk the parsed metadata: one fixture per check, holding
the events it flags beside the ones it must leave alone."""

import pytest
import validate_events as V
from shared.suite import build_validator, event_block, write_tree

_PICTURE_FIX = "event has no picture, add `picture = GFX_<sprite>` below `desc =`"
_TRIGGERED = "is_triggered_only = yes"
_HIDDEN = "hidden = yes"
_MAJOR = "major = yes"
_MTTH = "mean_time_to_happen = { days = 30 }"
_PORTRAIT = (
    "immediate = {\n\t\tcreate_country_leader = {\n"
    '\t\t\tpicture = "gfx/leaders/x.dds"\n\t\t}\n\t}'
)
_CONDITIONAL_PICTURE = (
    "picture = {\n\t\ttrigger = { has_country_flag = show }\n"
    "\t\tpicture = GFX_conditional\n\t}"
)


def _option(event_id, letter="a"):
    return f"option = {{ name = {event_id}.{letter} }}"


def _plain(event_id, *fields):
    """A triggered-only country event with one option."""
    return event_block(event_id, _TRIGGERED, *fields, _option(event_id))


def _validator(tmp_path, *events, files=None):
    write_tree(tmp_path, {"events/Ev.txt": "".join(events), **(files or {})})
    return build_validator(V.Validator, tmp_path)


def _messages(validator):
    return [issue.message for issue in validator._issues]


def test_missing_triggered_only_reads_the_flag_and_ignores_a_commented_one(tmp_path):
    v = _validator(
        tmp_path,
        event_block("foo.1", _option("foo.1")),
        _plain("foo.2"),
        event_block("foo.3", "#" + _TRIGGERED, _option("foo.3")),
    )

    v.validate_missing_triggered_only()

    joined = " ".join(_messages(v))
    assert "foo.1" in joined and "foo.3" in joined
    assert "foo.2" not in joined


def test_identical_event_bodies_are_not_collapsed(tmp_path):
    body = event_block(None, "option = { name = dup.a }")
    v = _validator(tmp_path, files={"events/A.txt": body, "events/B.txt": body})

    v.validate_missing_triggered_only()

    joined = " ".join(_messages(v))
    assert "A.txt" in joined and "B.txt" in joined


def test_picture_omission_reports_visible_news_events_only(tmp_path):
    v = _validator(
        tmp_path,
        event_block("foo.1", _TRIGGERED),
        event_block("foo.2", _MAJOR, _TRIGGERED, kind="news_event"),
        event_block("hidden.1", _HIDDEN, _MAJOR, _TRIGGERED, kind="news_event"),
        "country_event = visible.1\nnews_event = { id = visible.2 days = 1 }\n",
        event_block(
            "own.1", _MAJOR, _TRIGGERED, "picture = GFX_own", kind="news_event"
        ),
        event_block(
            "block.1", _MAJOR, _TRIGGERED, _CONDITIONAL_PICTURE, kind="news_event"
        ),
        # A nested character portrait is not the event's own picture.
        event_block("nested.1", _MAJOR, _TRIGGERED, _PORTRAIT, kind="news_event"),
    )

    v.validate_event_picture_omissions()

    assert [(i.message, i.category, i.severity, i.file, i.line) for i in v._issues] == [
        (
            f"{event}: {_PICTURE_FIX}",
            "news-event-picture-omitted",
            "error",
            "Ev.txt",
            line,
        )
        for event, line in (("foo.2", 5), ("nested.1", 33))
    ]


def test_placeholder_event_pictures_are_errors(tmp_path):
    v = _validator(
        tmp_path,
        event_block("ph.1", _TRIGGERED, "picture = GFX_placeholder_news"),
        event_block("ph.2", _HIDDEN, _TRIGGERED, "picture = GFX_news_md4"),
        event_block("real.1", _TRIGGERED, "picture = GFX_real"),
    )

    v.validate_placeholder_event_pictures()

    assert [(i.message, i.line, i.category) for i in v._issues] == [
        ("ph.1 - GFX_placeholder_news", 4, "placeholder-event-picture"),
        ("ph.2 - GFX_news_md4", 10, "placeholder-event-picture"),
    ]
    assert v.errors_found == 2


def test_missing_loc_skips_hidden_events_and_dotless_keys(tmp_path):
    # `title = FOO_TITLE` carries no namespace dot, so it is not an event key.
    v = _validator(
        tmp_path,
        _plain("vis.1", "title = FOO_TITLE", "desc = vis.1.d"),
        _plain("vis.2", "title = vis.2.t"),
        _plain("hid.1", _HIDDEN, "title = hid.1.t"),
        files={
            "localisation/english/md_l_english.yml": 'l_english:\n vis.1.d:0 "Body"\n'
        },
    )

    v.validate_missing_localisation()

    assert sorted(_messages(v)) == [
        "vis.1 - Ev.txt: missing loc key 'vis.1.a'",
        "vis.2 - Ev.txt: missing loc key 'vis.2.a'",
        "vis.2 - Ev.txt: missing loc key 'vis.2.t'",
    ]


def test_title_given_as_both_a_key_and_a_block_is_reported(tmp_path):
    v = _validator(
        tmp_path,
        _plain("foo.1", "title = foo.1.t", "title = {\n\t\ttext = foo.1.t\n\t}"),
    )

    v.validate_unsupported_title_desc()

    assert [i.category for i in v._issues] == ["invalid-title-desc"]
    assert "foo.1" in v._issues[0].message


def test_mtth_on_triggered_only_flagged_unless_in_a_random_events_pool(tmp_path):
    v = _validator(
        tmp_path,
        _plain("foo.1", _MTTH),
        _plain("pool.1", _MTTH),
        event_block("auto.1", _MTTH, _option("auto.1")),
        files={
            "common/on_actions/00_on_actions.txt": "on_actions = {\n\ton_startup = {\n"
            "\t\trandom_events = {\n\t\t\t100 = pool.1\n\t\t}\n\t}\n}\n"
        },
    )

    v.validate_mtth_triggered_only()

    assert [(i.message, i.category) for i in v._issues] == [
        ("foo.1 - Ev.txt", "mtth-triggered-only")
    ]


def test_hidden_events_with_options_flagged_and_counted(tmp_path):
    v = _validator(
        tmp_path,
        _plain("hid.1", _HIDDEN),
        _plain("hid.2", _HIDDEN, _option("hid.2", "b")),
        event_block("hid.3", _HIDDEN, _TRIGGERED, "immediate = { add_stability = 1 }"),
    )

    v.validate_hidden_event_options()

    assert _messages(v) == [
        "hid.1 - Ev.txt: 1 option block",
        "hid.2 - Ev.txt: 2 option blocks"
        " (only the first auto-fires — the rest are dead code)",
    ]


def test_hidden_event_loc_flagged_only_when_the_key_resolves(tmp_path):
    v = _validator(
        tmp_path,
        event_block("hid.1", _HIDDEN, _TRIGGERED, "title = hid.1.t"),
        event_block("hid.2", _HIDDEN, _TRIGGERED, "title = hid.2.t"),
        files={
            "localisation/english/md_l_english.yml": 'l_english:\n hid.1.t:0 "Title"\n'
        },
    )

    v.validate_hidden_event_localisation()

    assert [(i.message, i.category) for i in v._issues] == [
        ("hid.1 - Ev.txt: hid.1.t", "hidden-event-localisation")
    ]


def test_duplicate_event_id_reports_the_overwriting_definition(tmp_path):
    v = _validator(tmp_path, _plain("dup.1"), _plain("uniq.1"), _plain("dup.1"))

    v.validate_duplicate_event_ids()

    assert [(i.message, i.category) for i in v._issues] == [
        ("dup.1 - defined in Ev.txt and Ev.txt", "duplicate-event-id")
    ]


def test_undeclared_namespace_flagged(tmp_path):
    v = _validator(
        tmp_path,
        "add_namespace = foo\n",
        _plain("foo.1"),
        _plain("bar.1"),
        _plain("nodot"),
    )

    v.validate_namespace_mismatch()

    assert _messages(v) == ["bar.1 - Ev.txt (namespace 'bar' not declared)"]


def test_unreferenced_triggered_only_flagged_unless_fired_dynamic_or_exempt(tmp_path):
    v = _validator(
        tmp_path,
        "add_namespace = foo\nadd_namespace = dyn\nadd_namespace = lar_collab_gov\n",
        _plain("foo.9"),
        _plain("dyn.1"),
        _plain("foo.8"),
        # Engine-dispatched events on the exempt list are never reported.
        _plain("lar_collab_gov.1"),
        files={
            "common/scripted_effects/00_fx.txt": "dispatch_effect = {\n"
            "\tcountry_event = dyn.[EVENT_ID]\n\tcountry_event = foo.8\n}\n"
        },
    )

    v.validate_triggered_only_unreferenced()

    assert [(i.message, i.category) for i in v._issues] == [
        ("foo.9 - Ev.txt", "unreferenced-triggered-only")
    ]


def test_unreferenced_skips_the_full_tree_scan_in_staged_mode(tmp_path, monkeypatch):
    v = _validator(tmp_path, _plain("foo.9"))
    v.staged_only = True
    v.staged_files = [str(tmp_path / "events" / "Ev.txt")]
    monkeypatch.setattr(v, "_pool_map", lambda *a, **k: pytest.fail("scanned the tree"))

    v.validate_triggered_only_unreferenced()

    assert v._issues == []


def test_a_block_with_no_id_is_skipped_or_reported_as_unknown(tmp_path):
    # A check that keys on the id skips the block. The others name it "unknown".
    v = _validator(
        tmp_path,
        "add_namespace = foo\n",
        event_block(
            None, _TRIGGERED, _HIDDEN, _MTTH, "title = foo.1.t", _option("foo.1")
        ),
        # A second block with no id would read as a duplicate of the first.
        event_block(None, _TRIGGERED, _option("foo.1")),
        _plain("foo.1"),
        files={
            "localisation/english/md_l_english.yml": 'l_english:\n foo.1.t:0 "Title"\n'
        },
    )

    v.validate_mtth_triggered_only()
    v.validate_duplicate_event_ids()
    v.validate_namespace_mismatch()
    assert v._issues == []

    v.validate_hidden_event_options()
    v.validate_hidden_event_localisation()
    assert _messages(v) == [
        "unknown - Ev.txt: 1 option block",
        "unknown - Ev.txt: foo.1.t",
    ]


def test_event_metadata_is_parsed_once_per_run(tmp_path):
    v = _validator(tmp_path, _plain("foo.1"))

    assert v._get_event_metadata() is v._get_event_metadata()


def test_empty_event_file_is_skipped(tmp_path):
    v = _validator(
        tmp_path,
        _plain("foo.1", "fire_only_once = yes"),
        files={"events/Empty.txt": ""},
    )

    meta, _ = v._get_event_metadata()

    assert [event["id"] for event in meta] == ["foo.1"]
    assert v._get_fire_only_once_ids() == {"foo.1"}
    assert v._get_fire_only_once_ids() is v._fire_only_once_ids_cache


def _indented(text):
    return "".join("\t" + line for line in text.splitlines(keepends=True))


def test_indented_definitions_reach_the_metadata_checks(tmp_path):
    # Definitions are found by brace matching, not by column: 64 definitions in
    # the mod are indented.
    v = _validator(
        tmp_path,
        "add_namespace = foo\n",
        _indented(_plain("foo.1")),
        _plain("foo.1"),
        _indented(_plain("undeclared.1")),
    )

    meta, namespaces = v._get_event_metadata()
    v.validate_duplicate_event_ids()
    v.validate_namespace_mismatch()

    assert namespaces == {"foo"}
    assert [event["id"] for event in meta] == ["foo.1", "foo.1", "undeclared.1"]
    assert _messages(v) == [
        "foo.1 - defined in Ev.txt and Ev.txt",
        "undeclared.1 - Ev.txt (namespace 'undeclared' not declared)",
    ]


def test_nested_fire_id_is_not_adopted_by_a_malformed_parent(tmp_path):
    # The malformed block has no id of its own but fires foo.1 from an option.
    # Taking that id would invent a duplicate of the real foo.1.
    fire = "option = {\n\t\tname = broken.a\n\t\tcountry_event = { id = foo.1 days = 1 }\n\t}"
    v = _validator(
        tmp_path,
        "add_namespace = foo\n",
        event_block(None, _TRIGGERED, fire),
        _plain("foo.1"),
    )

    meta, _ = v._get_event_metadata()
    v.validate_duplicate_event_ids()

    assert [event["id"] for event in meta] == [None, "foo.1"]
    assert v._issues == []


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_two_namespaces_and_exact_lines_survive_crlf(tmp_path, newline):
    # Event files are read without newline translation, so CRLF reaches the
    # parser. The last line has no trailing newline.
    text = (
        "add_namespace = alpha\nadd_namespace = beta\n"
        + event_block("alpha.1", _TRIGGERED, "picture = GFX_alpha")
        + event_block("beta.1", _TRIGGERED, "picture = GFX_beta", kind="news_event")
    ).rstrip("\n")

    meta, namespaces = _validator(
        tmp_path, text.replace("\n", newline)
    )._get_event_metadata()

    assert namespaces == {"alpha", "beta"}
    assert [(m["id"], m["type"], m["line"], m["picture_refs"]) for m in meta] == [
        ("alpha.1", "country_event", 3, [("GFX_alpha", 6)]),
        ("beta.1", "news_event", 8, [("GFX_beta", 11)]),
    ]


@pytest.mark.parametrize("staged", [False, True])
def test_lookup_id_sets_come_from_the_single_metadata_parse(
    tmp_path, monkeypatch, staged
):
    # The scoped checks and the full-repo fire_only_once and major lookups share
    # one parse per event file, in staged mode too.
    parsed = []
    original = V._parse_event_metadata
    monkeypatch.setattr(
        V,
        "_parse_event_metadata",
        lambda text, basename: parsed.append(basename) or original(text, basename),
    )
    write_tree(
        tmp_path,
        {
            "events/A.txt": event_block("once.1", _TRIGGERED, "fire_only_once = yes")
            + event_block("big.1", _TRIGGERED, _MAJOR),
            "events/B.txt": event_block("other.1", _TRIGGERED, "fire_only_once = yes"),
        },
    )
    v = build_validator(V.Validator, tmp_path)
    if staged:
        v.staged_only = True
        v.staged_files = [str(tmp_path / "events" / "A.txt")]

    meta, _ = v._get_event_metadata()

    scoped = [("once.1", "A.txt", 1), ("big.1", "A.txt", 6)]
    if not staged:
        scoped.append(("other.1", "B.txt", 1))
    assert sorted((m["id"], m["file"], m["line"]) for m in meta) == sorted(scoped)
    assert v._get_fire_only_once_ids() == {"once.1", "other.1"}
    assert v._get_major_event_ids() == {"big.1"}
    assert sorted(parsed) == ["A.txt", "B.txt"]


def test_conditional_picture_scope_ends_with_its_block(tmp_path):
    v = _validator(
        tmp_path,
        event_block(
            "cond.1",
            _TRIGGERED,
            _CONDITIONAL_PICTURE,
            "option = {\n\t\tname = cond.1.a\n\t\tpicture = GFX_option_scope\n\t}",
            "picture = GFX_own",
            kind="news_event",
        ),
    )

    meta, _ = v._get_event_metadata()

    assert meta[0]["picture_refs"] == [("GFX_conditional", 6), ("GFX_own", 12)]
