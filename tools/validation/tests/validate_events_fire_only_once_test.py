"""Tests for validate_events.py: fire_only_once events fired inside an
every_*/for_each_* iterator, and the comment-stripping fix in
_parse_event_metadata that stops commented-out `#fire_only_once = yes` from
being counted as an active directive.

A fire_only_once event inside an iterating scope only reaches the first
recipient (the one-shot flag is set on the first firing). The detector flags
the call site. `random_country` / `random_state` are single-pick and are not
iterators, so a call nested only in them is not flagged.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validate_events import _parse_event_metadata, scan_fire_only_once_in_loop


def _event_block(eid, body_extra="fire_only_once = yes\n"):
    return (
        f"country_event = {{\n"
        f"\tid = {eid}\n"
        f"\tis_triggered_only = yes\n"
        f"\t{body_extra}"
        f"\toption = {{ name = {eid}.a }}\n"
        f"}}\n"
    )


def test_fires_inside_every_country_flagged(tmp_path):
    ev = tmp_path / "events" / "Ev.txt"
    ev.parent.mkdir(parents=True)
    ev.write_text(_event_block("foo.1"), encoding="utf-8")
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n\tevery_country = {\n\t\tcountry_event = foo.1\n\t}\n}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1
    assert "foo.1" in res[0]
    assert "iterator" in res[0]


def test_fires_inside_for_each_scope_loop_flagged(tmp_path):
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tfor_each_scope_loop = {\n"
        "\t\tarray = global.bloc\n"
        "\t\tcountry_event = { id = foo.1 days = 1 }\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1
    assert "foo.1" in res[0]


def test_id_not_first_arg_still_extracted(tmp_path):
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tevery_country = {\n"
        "\t\tcountry_event = { days = 20 id = foo.1 }\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1
    assert "foo.1" in res[0]


def test_operative_leader_event_short_form_flagged(tmp_path):
    # Regression: the keyword set had `operative_event` (no such keyword) and no
    # word boundary before `_leader_event`, so operative_leader_event calls were
    # never scanned for the fire_only_once-in-loop bug.
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n\tevery_country = {\n\t\toperative_leader_event = foo.1\n\t}\n}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1
    assert "foo.1" in res[0]


def test_operative_leader_event_long_form_flagged(tmp_path):
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tevery_state = {\n"
        "\t\toperative_leader_event = { id = foo.1 days = 2 }\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1
    assert "foo.1" in res[0]


def test_literal_brace_in_quoted_log_does_not_desync(tmp_path):
    # A `}` inside a quoted log string must not pop the iterator frame: without
    # quote-aware blanking the stray brace closed the every_country scope early
    # and the following fire_only_once call was silently missed.
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tevery_country = {\n"
        '\t\tlog = "unbalanced brace } inside a string"\n'
        "\t\tcountry_event = foo.1\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1
    assert "foo.1" in res[0]


def test_random_country_single_pick_not_flagged(tmp_path):
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n\trandom_country = {\n\t\tcountry_event = foo.1\n\t}\n}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert res == []


def test_random_nested_in_every_country_flagged(tmp_path):
    # A random_country inside an every_country still iterates: only the first
    # iteration's random pick gets the fire_only_once event.
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tevery_country = {\n"
        "\t\trandom_country = {\n"
        "\t\t\tcountry_event = foo.1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1


def test_pinned_root_scope_in_every_country_not_flagged(tmp_path):
    # A scope switch to ROOT between the iterator and the call fires the same
    # recipient every iteration, so fire_only_once is a legitimate dedup idiom.
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tevery_country = {\n"
        "\t\tROOT = {\n"
        "\t\t\tcountry_event = foo.1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert res == []


def test_pinned_tag_scope_in_every_country_not_flagged(tmp_path):
    # A literal tag scope (SAU = { ... }) between the iterator and the call pins
    # the recipient the same way ROOT does.
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tevery_country = {\n"
        "\t\tSAU = {\n"
        "\t\t\tcountry_event = { id = foo.1 days = 2 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert res == []


def test_iterator_wrapping_pinned_scope_still_flagged(tmp_path):
    # A pinned scope OUTSIDE the loop does not shield: every_country still fires
    # to each iterated country, so only the first gets the fire_only_once event.
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n"
        "\tROOT = {\n"
        "\t\tevery_country = {\n"
        "\t\t\tcountry_event = foo.1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path)))
    assert len(res) == 1


def test_non_fire_only_once_event_not_flagged(tmp_path):
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "x = {\n\tevery_country = {\n\t\tcountry_event = foo.1\n\t}\n}\n",
        encoding="utf-8",
    )
    res = scan_fire_only_once_in_loop((str(call), frozenset(), str(tmp_path)))
    assert res == []


def test_fire_only_once_lookup_full_repo_in_staged_mode(tmp_path):
    # Regression: the in-loop check built its fire_only_once ID set from
    # _get_event_metadata(), a staged-limited scan. Under --staged a staged
    # caller firing an existing fire_only_once event from a loop went unflagged
    # when the `fire_only_once = yes` definition lived in an unstaged file.
    from validate_events import Validator as EventsValidator

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    # Definition lives in an UNSTAGED event file.
    (events_dir / "def.txt").write_text(
        "add_namespace = foo\n" + _event_block("foo.1"),
        encoding="utf-8",
    )
    # Staged caller fires it inside an every_country iterator.
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    caller = common_dir / "caller.txt"
    caller.write_text(
        "x = {\n\tevery_country = {\n\t\tcountry_event = foo.1\n\t}\n}\n",
        encoding="utf-8",
    )

    v = EventsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.staged_only = True
    v.staged_files = [str(caller)]
    v.validate_fire_only_once_in_loop()
    # WARNING-severity until the pre-existing backlog is cleared.
    assert v.warnings_found >= 1, (
        "fire_only_once definition in an unstaged file must still be looked "
        "up — staged mode used to scan only staged event files and miss it, "
        "silently passing the in-loop bug at commit time"
    )


def test_parse_metadata_strips_commented_fire_only_once(tmp_path):
    # A commented-out `#fire_only_once = yes` must NOT mark the event as
    # fire_only_once (regression: the unstripped `in body` check counted it).
    text = (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\t#fire_only_once = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
    )
    meta, _ = _parse_event_metadata(text, "Ev.txt")
    assert len(meta) == 1
    assert meta[0]["fire_only_once"] is False


def test_parse_metadata_keeps_active_fire_only_once(tmp_path):
    text = (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\tfire_only_once = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
    )
    meta, _ = _parse_event_metadata(text, "Ev.txt")
    assert meta[0]["fire_only_once"] is True


def test_parse_metadata_strips_commented_hidden_and_triggered_only():
    # The same comment-stripping fix covers hidden = yes and is_triggered_only.
    text = (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\t#is_triggered_only = yes\n"
        "\t#hidden = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
    )
    meta, _ = _parse_event_metadata(text, "Ev.txt")
    assert meta[0]["is_triggered_only"] is False
    assert meta[0]["is_hidden"] is False
