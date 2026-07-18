"""Unit tests for the shared sprite index and the event-picture / focus-icon
reference extractors.
"""

from sprite_index import _names_in_file
from validate_events import _EVENT_PICTURE_REF, _extract_event_pictures
from validate_focus_tree import _extract_focus_icons


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_names_in_file_block_scoped_and_comment_safe(tmp_path):
    # `//` and `#` are line comments; a sprite after a commented line must still
    # be collected (regression: a `//.*` DOTALL pattern ate the rest of the file).
    f = _write(
        tmp_path,
        "x.gfx",
        "spriteTypes = {\n"
        '  spriteType = { name = "GFX_one" texturefile = "a.dds" } // a comment\n'
        "  # another comment\n"
        '  spriteType = { name = "bare_two" texturefile = "b.dds" }\n'
        "}\n",
    )
    names = set(_names_in_file(f))
    assert names == {"GFX_one", "bare_two"}


def test_event_picture_regex_matches_quoted_and_unquoted():
    assert _EVENT_PICTURE_REF.search("picture = GFX_political_deal").group(1) == (
        "GFX_political_deal"
    )
    assert _EVENT_PICTURE_REF.search('picture = "GFX_handshake"').group(1) == (
        "GFX_handshake"
    )


def test_event_picture_regex_keeps_frame_and_hyphen():
    # Sprite names can carry a `.N` frame suffix or a hyphen; both are part of
    # the name, not a delimiter (regression: stopping at `.`/`-` flagged the
    # real sprite GFX_CTC.5 / GFX_Polizistin-Kiesewetter as undefined).
    assert _EVENT_PICTURE_REF.search("picture = GFX_CTC.5").group(1) == "GFX_CTC.5"
    assert (
        _EVENT_PICTURE_REF.search("picture = GFX_Polizistin-Kiesewetter").group(1)
        == "GFX_Polizistin-Kiesewetter"
    )


def test_extract_event_pictures(tmp_path):
    f = _write(
        tmp_path,
        "evt.txt",
        "country_event = {\n id = foo.1\n picture = GFX_report_event_x\n}\n"
        "# picture = GFX_commented_out\n"
        "country_event = {\n id = foo.2\n picture = GFX_another\n}\n",
    )
    refs = _extract_event_pictures(f)
    sprites = {r[0] for r in refs}
    assert sprites == {"GFX_report_event_x", "GFX_another"}
    # commented-out picture is ignored
    assert "GFX_commented_out" not in sprites
    # line numbers are populated
    assert all(r[2] > 0 for r in refs)


def test_extract_focus_icons_bare_and_gfx(tmp_path):
    f = _write(
        tmp_path,
        "tree.txt",
        "focus_tree = {\n"
        " id = test_tree\n"
        " focus = {\n  id = f_money\n  icon = money\n  x = 1\n  y = 1\n }\n"
        " focus = {\n  id = f_brics\n  icon = GFX_brics\n  x = 2\n  y = 1\n }\n"
        " focus = {\n  id = f_dynamic\n  icon = [GetIcon]\n  x = 3\n  y = 1\n }\n"
        " focus = {\n  id = f_noicon\n  x = 4\n  y = 1\n }\n"
        ' focus = {\n  id = f_spaced\n  icon = "Finnish Air_Force"\n  x = 5\n  y = 1\n }\n'
        "}\n",
    )
    by_id = {
        fid: icon for fid, icon, _fp, _line in _extract_focus_icons((f, str(tmp_path)))
    }
    assert by_id == {
        "f_money": "money",
        "f_brics": "GFX_brics",
        # a quoted value with a space is one verbatim sprite name, not two tokens
        "f_spaced": "Finnish Air_Force",
    }
    # dynamic [...] and no-icon focuses are skipped
    assert "f_dynamic" not in by_id
    assert "f_noicon" not in by_id


def test_extract_focus_icons_shared_focus(tmp_path):
    f = _write(
        tmp_path,
        "shared.txt",
        "shared_focus = {\n id = s_focus\n icon = welfare\n x = 1\n y = 1\n}\n",
    )
    icons = _extract_focus_icons((f, str(tmp_path)))
    assert icons and icons[0][0] == "s_focus" and icons[0][1] == "welfare"
