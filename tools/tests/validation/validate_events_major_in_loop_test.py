"""Tests for validate_events.py: major = yes events fired inside an
every_*/for_each_* iterator.

A major event already broadcasts to every country on each fire. Inside an
iterating scope that becomes one broadcast per iteration. Unlike
fire_only_once, a pinned ROOT/TAG scope does not exempt it: the same global
broadcast still repeats. Non-major news_event fires inside every_country are
the per-country notification pattern and are not flagged.
"""

from validate_events import (
    _parse_event_metadata,
    scan_major_event_in_loop,
)


def _major_block(eid, extra="major = yes\n"):
    return (
        f"news_event = {{\n"
        f"\tid = {eid}\n"
        f"\tis_triggered_only = yes\n"
        f"\t{extra}"
        f"\toption = {{ name = {eid}.a }}\n"
        f"}}\n"
    )


def _scan(tmp_path, body, ids=("foo.1",)):
    call = tmp_path / "common" / "f.txt"
    call.parent.mkdir(parents=True, exist_ok=True)
    call.write_text(body, encoding="utf-8")
    return scan_major_event_in_loop((str(call), frozenset(ids), str(tmp_path)))


def test_major_news_inside_every_country_flagged(tmp_path):
    res = _scan(
        tmp_path, "x = {\n\tevery_country = {\n\t\tnews_event = foo.1\n\t}\n}\n"
    )
    assert len(res) == 1
    assert "foo.1" in res[0]
    assert "major event" in res[0]


def test_major_country_event_inside_every_country_flagged(tmp_path):
    res = _scan(
        tmp_path, "x = {\n\tevery_country = {\n\t\tcountry_event = foo.1\n\t}\n}\n"
    )
    assert len(res) == 1


def test_non_major_news_inside_every_country_not_flagged(tmp_path):
    res = _scan(
        tmp_path,
        "x = {\n\tevery_country = {\n\t\tnews_event = foo.1\n\t}\n}\n",
        ids=(),
    )
    assert res == []


def test_every_other_country_flagged(tmp_path):
    res = _scan(
        tmp_path, "x = {\n\tevery_other_country = {\n\t\tnews_event = foo.1\n\t}\n}\n"
    )
    assert len(res) == 1


def test_every_state_flagged(tmp_path):
    res = _scan(tmp_path, "x = {\n\tevery_state = {\n\t\tnews_event = foo.1\n\t}\n}\n")
    assert len(res) == 1


def test_for_each_scope_loop_flagged(tmp_path):
    res = _scan(
        tmp_path,
        "x = {\n"
        "\tfor_each_scope_loop = {\n"
        "\t\tarray = global.bloc\n"
        "\t\tnews_event = { id = foo.1 days = 1 }\n"
        "\t}\n"
        "}\n",
    )
    assert len(res) == 1


def test_id_not_first_arg_still_extracted(tmp_path):
    res = _scan(
        tmp_path,
        "x = {\n"
        "\tevery_country = {\n"
        "\t\tnews_event = { hours = 2 id = foo.1 }\n"
        "\t}\n"
        "}\n",
    )
    assert len(res) == 1
    assert "foo.1" in res[0]


def test_random_country_single_pick_not_flagged(tmp_path):
    res = _scan(
        tmp_path, "x = {\n\trandom_country = {\n\t\tnews_event = foo.1\n\t}\n}\n"
    )
    assert res == []


def test_pinned_root_scope_still_flagged(tmp_path):
    res = _scan(
        tmp_path,
        "x = {\n"
        "\tevery_country = {\n"
        "\t\tROOT = {\n"
        "\t\t\tnews_event = foo.1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert len(res) == 1


def test_pinned_tag_scope_still_flagged(tmp_path):
    res = _scan(
        tmp_path,
        "x = {\n"
        "\tevery_country = {\n"
        "\t\tPHI = {\n"
        "\t\t\tnews_event = { id = foo.1 days = 1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert len(res) == 1


def test_literal_brace_in_quoted_log_does_not_desync(tmp_path):
    res = _scan(
        tmp_path,
        "x = {\n"
        "\tevery_country = {\n"
        '\t\tlog = "unbalanced brace } inside a string"\n'
        "\t\tnews_event = foo.1\n"
        "\t}\n"
        "}\n",
    )
    assert len(res) == 1


def test_worker_returns_empty_for_an_unreadable_file(tmp_path):
    args = (str(tmp_path / "common" / "gone.txt"), frozenset({"foo.1"}), str(tmp_path))
    assert scan_major_event_in_loop(args) == []


def test_worker_short_circuits_files_with_no_event_calls(tmp_path):
    call = tmp_path / "common" / "fx.txt"
    call.parent.mkdir(parents=True)
    call.write_text(
        "fx = {\n\tevery_country = { add_political_power = 5 }\n}\n",
        encoding="utf-8",
    )
    assert (
        scan_major_event_in_loop((str(call), frozenset({"foo.1"}), str(tmp_path))) == []
    )


def test_parse_metadata_major_yes():
    meta, _ = _parse_event_metadata(_major_block("foo.1"), "Ev.txt")
    assert meta[0]["is_major"] is True


def test_parse_metadata_strips_commented_major():
    meta, _ = _parse_event_metadata(
        _major_block("foo.1", extra="#major = yes\n"), "Ev.txt"
    )
    assert meta[0]["is_major"] is False


def test_parse_metadata_is_major_trigger_is_not_event_major():
    text = (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n"
        "\t\tname = foo.1.a\n"
        "\t\ttrigger = { is_major = yes }\n"
        "\t}\n"
        "}\n"
    )
    meta, _ = _parse_event_metadata(text, "Ev.txt")
    assert meta[0]["is_major"] is False


def test_major_lookup_full_repo_in_staged_mode(tmp_path):
    from validate_events import Validator as EventsValidator

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "def.txt").write_text(
        "add_namespace = foo\n" + _major_block("foo.1"),
        encoding="utf-8",
    )
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    caller = common_dir / "caller.txt"
    caller.write_text(
        "x = {\n\tevery_country = {\n\t\tnews_event = foo.1\n\t}\n}\n",
        encoding="utf-8",
    )

    v = EventsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.staged_only = True
    v.staged_files = [str(caller)]
    v.validate_major_event_in_loop()
    assert v.errors_found >= 1, (
        "major definition in an unstaged file must still be looked up — "
        "staged mode used to scan only staged event files and miss it, "
        "silently passing the in-loop broadcast bug at commit time"
    )


def test_major_check_short_circuits_without_declarations(tmp_path, monkeypatch):
    from validate_events import Validator as EventsValidator

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "Ev.txt").write_text(
        "add_namespace = foo\n" + _major_block("foo.1", extra=""),
        encoding="utf-8",
    )
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    (common_dir / "caller.txt").write_text(
        "x = {\n\tevery_country = {\n\t\tnews_event = foo.1\n\t}\n}\n",
        encoding="utf-8",
    )

    v = EventsValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v._get_major_event_ids()

    def _fail(*args, **kwargs):
        raise AssertionError("scanned for in-loop fires with no major events")

    monkeypatch.setattr(v, "_pool_map", _fail)
    v.validate_major_event_in_loop()
    assert v._issues == []
