"""Unit tests for the idea icon / category-frame checks in validate_ideas.py.

Covers the picture-capturing parser, the GFX_idea_categories frame-count
reader, and the idea_categories.txt classification helpers in shared_utils.
"""

from shared_utils import get_all_idea_categories, get_non_selectable_idea_categories
from validate_ideas import (
    _IDEA_REF_BLOCK,
    _IDEA_REF_GENEROUS,
    _WORD_TOKEN,
    _idea_categories_frame_count,
    _missing_icon_message,
    _parse_ideas_from_text,
)


def _refs(text):
    out = set(_IDEA_REF_GENEROUS.findall(text))
    for m in _IDEA_REF_BLOCK.finditer(text):
        out.update(_WORD_TOKEN.findall(m.group(1)))
    return out


def test_unused_ref_scan_single_block_timed_swap():
    text = """
    completion_reward = { add_ideas = SPIRIT_one }
    add_ideas = { SPIRIT_two SPIRIT_three }
    add_timed_idea = { idea = SPIRIT_four days = 30 }
    swap_ideas = { remove_idea = SPIRIT_five add_idea = SPIRIT_six }
    has_idea = SPIRIT_seven
    """
    refs = _refs(text)
    assert {
        "SPIRIT_one",
        "SPIRIT_two",
        "SPIRIT_three",
        "SPIRIT_four",
        "SPIRIT_five",
        "SPIRIT_six",
        "SPIRIT_seven",
    } <= refs


def test_unused_ref_scan_ignores_unrelated_keys():
    # A name that only appears as an idea *definition* (not a reference keyword)
    # must not count as referenced.
    refs = _refs(
        "DEAD_idea = {\n picture = x\n modifier = { stability_factor = 0.1 }\n}"
    )
    assert "DEAD_idea" not in refs


SPRITES = frozenset({"GFX_idea_known_pic", "GFX_idea_AUTO", "GFX_idea_shared_key"})
HIDDEN = frozenset({"hidden_ideas"})


def test_icon_explicit_picture_defined():
    assert (
        _missing_icon_message("AUTO", "country", None, "known_pic", SPRITES, HIDDEN)
        is None
    )


def test_icon_explicit_picture_missing():
    msg = _missing_icon_message("X", "country", None, "nope", SPRITES, HIDDEN)
    assert msg == "X: picture = nope -> GFX_idea_nope (undefined)"


def test_icon_no_picture_auto_registered():
    # GFX_idea_AUTO exists -> no finding.
    assert _missing_icon_message("AUTO", "country", None, None, SPRITES, HIDDEN) is None


def test_icon_no_picture_missing_auto():
    msg = _missing_icon_message("LONELY", "country", None, None, SPRITES, HIDDEN)
    assert msg == "LONELY: no picture and no auto-icon GFX_idea_LONELY"


def test_icon_no_picture_name_override_sprite():
    # Auto-icon by idea id is missing, but the name-override sprite exists.
    assert (
        _missing_icon_message("X", "country", "shared_key", None, SPRITES, HIDDEN)
        is None
    )


def test_icon_hidden_category_skipped():
    assert (
        _missing_icon_message("X", "hidden_ideas", None, "nope", SPRITES, HIDDEN)
        is None
    )


def test_icon_character_token_skipped():
    assert _missing_icon_message("X", "character", None, None, SPRITES, HIDDEN) is None


def test_icon_dynamic_picture_skipped():
    assert (
        _missing_icon_message("X", "country", None, "[GetIcon]", SPRITES, HIDDEN)
        is None
    )


def test_parser_captures_picture():
    text = """ideas = {
 country = {
  WITH_pic = {
   picture = some_pic
   modifier = { stability_factor = 0.05 }
  }
  NO_pic = {
   modifier = { stability_factor = 0.05 }
  }
  RENAMED = {
   name = SHARED_key
   picture = pic_two
  }
 }
}"""
    defined, _ = _parse_ideas_from_text(text)
    assert defined["WITH_pic"] == ("country", None, "some_pic")
    assert defined["NO_pic"] == ("country", None, None)
    assert defined["RENAMED"] == ("country", "SHARED_key", "pic_two")


def test_picture_with_hyphen():
    text = """ideas = {
 materiel_manufacturer = {
  CO = {
   picture = Colt-Defense
   modifier = { stability_factor = 0.01 }
  }
 }
}"""
    defined, _ = _parse_ideas_from_text(text)
    assert defined["CO"][2] == "Colt-Defense"


def test_frame_count_reads_no_of_frames(tmp_path):
    gfx = tmp_path / "x.gfx"
    gfx.write_text(
        'spriteType = {\n name = "GFX_idea_categories"\n'
        ' texturefile = "gfx/interface/idea_categories.dds"\n noOfFrames = 6\n}\n',
        encoding="utf-8",
    )
    assert _idea_categories_frame_count([str(tmp_path)]) == 6


def test_frame_count_defaults_to_one_without_frames(tmp_path):
    gfx = tmp_path / "x.gfx"
    gfx.write_text(
        'spriteType = {\n name = "GFX_idea_categories"\n'
        ' texturefile = "gfx/interface/idea_categories.dds"\n}\n',
        encoding="utf-8",
    )
    assert _idea_categories_frame_count([str(tmp_path)]) == 1


def test_frame_count_first_dir_wins(tmp_path):
    mod = tmp_path / "mod"
    van = tmp_path / "van"
    mod.mkdir()
    van.mkdir()
    (mod / "a.gfx").write_text(
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 9 }', encoding="utf-8"
    )
    (van / "b.gfx").write_text(
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 6 }', encoding="utf-8"
    )
    assert _idea_categories_frame_count([str(mod), str(van)]) == 9


def test_frame_count_absent_returns_none(tmp_path):
    (tmp_path / "x.gfx").write_text(
        'spriteType = { name = "GFX_something_else" }', encoding="utf-8"
    )
    assert _idea_categories_frame_count([str(tmp_path)]) is None
    assert _idea_categories_frame_count(["/no/such/dir"]) is None


def _write_idea_tags(tmp_path):
    d = tmp_path / "common" / "idea_tags"
    d.mkdir(parents=True)
    (d / "00_idea.txt").write_text(
        """idea_categories = {
 hidden_ideas = { hidden = yes }
 country = { type = national_spirit }
 national_status = { slot = religion slot = corruption }
 military_staff = { character_slot = chief_of_staff }
 army_spirit = { type = army_spirit slot = army_chief }
}""",
        encoding="utf-8",
    )
    return str(tmp_path)


def test_get_all_idea_categories_classifies(tmp_path):
    root = _write_idea_tags(tmp_path)
    cats = {c["name"]: c for c in get_all_idea_categories(root)}
    assert cats["hidden_ideas"]["hidden"] is True
    assert cats["country"]["type"] == "national_spirit"
    assert cats["national_status"]["has_slot"] is True
    assert cats["national_status"]["type"] is None
    assert cats["military_staff"]["has_char_slot"] is True
    assert cats["army_spirit"]["type"] == "army_spirit"

    # Order preserved — frame assignment depends on it.
    names = [c["name"] for c in get_all_idea_categories(root)]
    assert names == [
        "hidden_ideas",
        "country",
        "national_status",
        "military_staff",
        "army_spirit",
    ]

    # Only national_status is a plain politics-view row category here.
    rows = [
        c["name"]
        for c in get_all_idea_categories(root)
        if not c["hidden"] and not c["has_char_slot"] and c["type"] is None
    ]
    assert rows == ["national_status"]


def test_non_selectable_refactor_preserved(tmp_path):
    root = _write_idea_tags(tmp_path)
    # hidden_ideas (hidden) + country (no slot/char_slot) are non-selectable.
    assert get_non_selectable_idea_categories(root) == frozenset(
        {"hidden_ideas", "country"}
    )
