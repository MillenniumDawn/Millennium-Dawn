"""Event picture checks: art authored for the wrong window, and hidden events."""

import pytest
import validate_events as V
from shared.suite import write_under_str as _write

COUNTRY_ART = (217, 163)
NEWS_ART = (397, 153)

# A nested character portrait sits below the event's own depth and is not its
# picture; the conditional form contributes its inner reference instead.
PORTRAIT_FIELD = (
    "immediate = {\n\t\tcreate_country_leader = {\n\t\t\tpicture = GFX_wide\n\t\t}\n\t}"
)
CONDITIONAL_FIELD = (
    "picture = {\n\t\ttrigger = { has_country_flag = show_picture }"
    "\n\t\tpicture = GFX_wide\n\t}"
)


def _validator(tmp_path):
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def _event(event_type, event_id, *fields):
    """One event definition; `is_triggered_only` first so field lines are stable."""
    lines = "".join(f"\t{field}\n" for field in ("is_triggered_only = yes",) + fields)
    return f"{event_type} = {{\n\tid = {event_id}\n{lines}}}\n"


def _run(tmp_path, monkeypatch, sizes, *events):
    """Write the events, install a texture index, run the format check."""
    _write(tmp_path, "events/Ev.txt", "".join(events))
    if sizes is not None:
        index = {f"GFX_filler_{i}": f"filler_{i}.dds" for i in range(1000)}
        index.update({name: f"{name}.dds" for name in sizes})
        by_path = {f"{name}.dds": size for name, size in sizes.items()}
        monkeypatch.setattr(V, "build_sprite_texture_index", lambda *a, **kw: index)
        monkeypatch.setattr(V, "read_image_size", by_path.get)
    validator = _validator(tmp_path)
    validator.validate_event_picture_formats()
    return validator


@pytest.mark.parametrize(
    "size,expected",
    [
        ((217, 163), "country_event"),
        ((210, 176), "country_event"),
        ((1024, 768), "country_event"),
        ((397, 153), "news_event"),
        ((400, 150), "news_event"),
        ((500, 250), "news_event"),
    ],
)
def test_the_two_art_families_are_identified(size, expected):
    assert V._picture_format_for_size(*size) == expected


@pytest.mark.parametrize("size", [(300, 170), (33, 32), (60, 68), (120, 0)])
def test_sizes_outside_both_families_identify_no_window(size):
    assert V._picture_format_for_size(*size) is None


def test_news_art_on_a_country_event_is_reported(tmp_path, monkeypatch):
    v = _run(
        tmp_path,
        monkeypatch,
        {"GFX_wide": NEWS_ART},
        _event("country_event", "foo.1", "picture = GFX_wide"),
    )

    assert [(i.message, i.file, i.line, i.category) for i in v._issues] == [
        (
            "foo.1: picture = GFX_wide is 397x153, which is news event art; "
            "a country event picture is 217x163",
            "Ev.txt",
            4,
            "event-picture-format-mismatch",
        ),
    ]
    assert v.warnings_found == 1
    assert v.errors_found == 0


def test_country_art_on_a_news_event_is_reported(tmp_path, monkeypatch):
    v = _run(
        tmp_path,
        monkeypatch,
        {"GFX_narrow": COUNTRY_ART},
        _event("news_event", "foo.2", "major = yes", "picture = GFX_narrow"),
    )

    assert v.warnings_found == 1
    assert "country event art" in v._issues[0].message
    assert v._issues[0].line == 5


def test_matching_art_is_clean(tmp_path, monkeypatch):
    v = _run(
        tmp_path,
        monkeypatch,
        {"GFX_narrow": COUNTRY_ART, "GFX_wide": NEWS_ART},
        _event("country_event", "foo.1", "picture = GFX_narrow"),
        _event("news_event", "foo.2", "picture = GFX_wide"),
    )

    assert v._issues == []


def test_quoted_and_conditional_picture_values_are_checked(tmp_path, monkeypatch):
    v = _run(
        tmp_path,
        monkeypatch,
        {"GFX_wide": NEWS_ART},
        _event("country_event", "quoted.1", 'picture = "GFX_wide"'),
        _event("country_event", "block.1", CONDITIONAL_FIELD),
    )

    assert [(i.line, i.message.split(":")[0]) for i in v._issues] == [
        (4, "quoted.1"),
        (11, "block.1"),
    ]


def test_a_nested_character_portrait_is_not_the_events_picture(tmp_path, monkeypatch):
    v = _run(
        tmp_path,
        monkeypatch,
        {"GFX_narrow": COUNTRY_ART, "GFX_wide": NEWS_ART},
        _event("country_event", "foo.1", "picture = GFX_narrow", PORTRAIT_FIELD),
    )

    assert v._issues == []


def test_hidden_events_are_skipped_by_the_format_check(tmp_path, monkeypatch):
    v = _run(
        tmp_path,
        monkeypatch,
        {"GFX_wide": NEWS_ART},
        _event("country_event", "hid.1", "hidden = yes", "picture = GFX_wide"),
    )

    assert v._issues == []


def test_unresolved_and_unreadable_textures_are_left_alone(tmp_path, monkeypatch):
    v = _run(
        tmp_path,
        monkeypatch,
        {"GFX_unreadable": None},
        _event(
            "news_event",
            "foo.1",
            "picture = GFX_ghost",
            "picture = GFX_unreadable",
        ),
    )

    assert v._issues == []


def test_format_check_skips_when_no_event_pictures_are_in_scope(tmp_path, monkeypatch):
    def _explode(*_args, **_kwargs):
        raise AssertionError("texture index must not be built with nothing to check")

    monkeypatch.setattr(V, "build_sprite_texture_index", _explode)
    v = _run(tmp_path, monkeypatch, None, _event("country_event", "foo.1"))

    assert v._issues == []


def test_format_check_skips_when_the_texture_index_failed_to_load(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(V, "build_sprite_texture_index", lambda *a, **kw: {})
    v = _run(
        tmp_path,
        monkeypatch,
        None,
        _event("country_event", "foo.1", "picture = GFX_wide"),
    )

    assert v._issues == []
    assert any("skipping the picture format check" in line for line in v.output_lines)


def test_hidden_event_picture_is_reported(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        _event("country_event", "hid.1", "hidden = yes", "picture = GFX_narrow")
        + _event("country_event", "vis.1", "picture = GFX_narrow"),
    )
    v = _validator(tmp_path)
    v.validate_hidden_event_pictures()

    assert [i.message for i in v._issues] == ["hid.1 - Ev.txt"]
    assert v.warnings_found == 1
    assert v.errors_found == 0
    assert v._issues[0].category == "hidden-event-picture"


def test_hidden_event_with_only_a_nested_portrait_is_clean(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        _event("country_event", "hid.1", "hidden = yes", PORTRAIT_FIELD),
    )
    v = _validator(tmp_path)
    v.validate_hidden_event_pictures()

    assert v._issues == []
