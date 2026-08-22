"""Unit tests for the decision icon/picture sprite check in validate_decisions.py.

Covers sprite-name resolution per reference kind, the reference extractor
(including the dynamic `icon = { key = ... }` form and depth-aware owner
attribution), and that build_sprite_index does not consult the vanilla manifest.
"""

from sprite_index import build_sprite_index
from validate_decisions import (
    _extract_decision_icons,
    _is_category_file,
    _missing_sprite_message,
    _owner_spans,
    _sprite_candidates,
)
from validate_gfx_references import _load_vanilla_sprite_manifest

SPRITES = frozenset(
    {
        "tungsten",
        "GFX_decision_generic_intelligence_operation",
        "GFX_decision_category_generic_economy",
        "GFX_zsr_parlament",
        "GFX_decision_oil",
    }
)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


# --- resolution -----------------------------------------------------------


def test_bare_decision_icon_resolves_verbatim():
    # `icon = tungsten` where a sprite literally named tungsten exists.
    assert _missing_sprite_message("decision", "d", "tungsten", SPRITES) is None


def test_bare_decision_icon_resolves_via_decision_prefix():
    # The engine auto-prepends GFX_decision_ to a bare name — not a bug.
    assert _missing_sprite_message("decision", "d", "oil", SPRITES) is None


def test_qualified_decision_icon_resolves_verbatim():
    msg = _missing_sprite_message(
        "decision", "d", "GFX_decision_generic_intelligence_operation", SPRITES
    )
    assert msg is None


def test_qualified_icon_does_not_get_double_prefixed():
    # A GFX_-prefixed value is only ever tried verbatim; suggesting
    # GFX_decision_GFX_decision_x in the message would be nonsense.
    assert _sprite_candidates("decision", "GFX_decision_missing") == [
        "GFX_decision_missing"
    ]


def test_missing_decision_icon_reports_candidates_and_remedy():
    msg = _missing_sprite_message("decision", "SOME_decision", "nope", SPRITES)
    assert msg == (
        "SOME_decision: icon = nope -> no sprite nope / GFX_decision_nope / "
        "GFX_nope defined in interface/*.gfx (create the sprite or pick an "
        "existing icon)"
    )


def test_category_icon_uses_category_prefix():
    assert (
        _missing_sprite_message("category_icon", "c", "generic_economy", SPRITES)
        is None
    )


def test_category_icon_not_satisfied_by_decision_sprite():
    # GFX_decision_oil exists but a category needs GFX_decision_category_oil.
    msg = _missing_sprite_message("category_icon", "c", "oil", SPRITES)
    assert msg is not None
    assert "GFX_decision_category_oil" in msg


def test_category_picture_requires_verbatim_name():
    assert (
        _missing_sprite_message("category_picture", "c", "GFX_zsr_parlament", SPRITES)
        is None
    )
    msg = _missing_sprite_message("category_picture", "c", "zsr_parlament", SPRITES)
    assert msg is not None
    assert msg.count("->") == 1
    assert "picture = zsr_parlament" in msg


def test_dynamic_value_skipped():
    assert _missing_sprite_message("decision", "d", "[GetIcon]", SPRITES) is None


# --- extraction -----------------------------------------------------------


def test_is_category_file_handles_windows_separators():
    assert _is_category_file(r"mod\common\decisions\categories\99_x.txt")
    assert not _is_category_file("mod/common/decisions/99_x.txt")


def test_extract_decision_icon_bare_and_quoted(tmp_path):
    f = _write(
        tmp_path,
        "d.txt",
        'cat = {\n\tfirst = {\n\t\ticon = money\n\t}\n\tsecond = {\n\t\ticon = "GFX_a b"\n\t}\n}\n',
    )
    refs = _extract_decision_icons((f, str(tmp_path)))
    # The quoted name carries a space, which the sprite-value pattern stops at;
    # only the bare reference is captured.
    assert ("first", "decision", "money", 3) in refs


def test_extract_ignores_commented_icon(tmp_path):
    f = _write(
        tmp_path,
        "d.txt",
        "cat = {\n\tfirst = {\n\t\t# icon = ghost\n\t\ticon = money\n\t}\n}\n",
    )
    values = [r[2] for r in _extract_decision_icons((f, str(tmp_path)))]
    assert values == ["money"]


def test_extract_keeps_dot_and_hyphen_in_name(tmp_path):
    # Regression guard shared with sprite_reference_test.py: `.` and `-` are
    # part of a sprite name, not a delimiter.
    f = _write(
        tmp_path,
        "d.txt",
        "cat = {\n\ta = {\n\t\ticon = GFX_CTC.5\n\t}\n\tb = {\n\t\ticon = GFX_MIG-29-GER\n\t}\n}\n",
    )
    values = [r[2] for r in _extract_decision_icons((f, str(tmp_path)))]
    assert values == ["GFX_CTC.5", "GFX_MIG-29-GER"]


def test_extract_dynamic_icon_block_yields_every_key(tmp_path):
    f = _write(
        tmp_path,
        "d.txt",
        "cat = {\n\tdyn = {\n\t\ticon = {\n"
        "\t\t\tkey = GFX_decision_high\n\t\t\ttrigger = { has_war = yes }\n"
        "\t\t}\n\t\ticon = {\n\t\t\tkey = GFX_decision_low\n\t\t}\n\t}\n}\n",
    )
    refs = _extract_decision_icons((f, str(tmp_path)))
    assert [r[2] for r in refs] == ["GFX_decision_high", "GFX_decision_low"]
    assert all(r[0] == "dyn" for r in refs)


def test_owner_is_decision_id_not_nested_block(tmp_path):
    # A one-line `visible = { ... }` between the id and its icon must not be
    # reported as the owner.
    f = _write(
        tmp_path,
        "d.txt",
        "cat = {\n\tJAP_bibi = {\n\t\tvisible = { has_completed_focus = X }\n"
        "\t\ticon = microchip\n\t}\n}\n",
    )
    refs = _extract_decision_icons((f, str(tmp_path)))
    assert refs == [("JAP_bibi", "decision", "microchip", 4)]


def test_category_file_yields_icon_and_picture(tmp_path):
    catdir = tmp_path / "common" / "decisions" / "categories"
    catdir.mkdir(parents=True)
    f = catdir / "c.txt"
    f.write_text(
        "ABK_politics = {\n\ticon = generic_economy\n\tpicture = GFX_decision_abkhaz\n}\n",
        encoding="utf-8",
    )
    refs = _extract_decision_icons((str(f), str(tmp_path)))
    assert refs == [
        ("ABK_politics", "category_icon", "generic_economy", 2),
        ("ABK_politics", "category_picture", "GFX_decision_abkhaz", 3),
    ]


def test_owner_spans_selects_requested_depth():
    text = "cat = {\n\tdec = {\n\t\tvisible = { a = yes }\n\t}\n}\n"
    assert [t for _, _, t in _owner_spans(text, 0)] == ["cat"]
    assert [t for _, _, t in _owner_spans(text, 1)] == ["dec"]


def test_unreadable_file_returns_no_refs(tmp_path):
    assert _extract_decision_icons((str(tmp_path / "missing.txt"), str(tmp_path))) == []


# --- sprite index ---------------------------------------------------------


def test_sprite_index_does_not_fold_in_vanilla_manifest(tmp_path):
    # The manifest is deliberately not consulted: the icon checks it fed are
    # opt-in and kept out of CI, so the index stays mod- plus live-install-only.
    manifest = _load_vanilla_sprite_manifest()
    if not manifest:
        return
    assert not (manifest <= build_sprite_index(str(tmp_path), include_vanilla=True))
    assert not build_sprite_index(str(tmp_path), include_vanilla=False)
