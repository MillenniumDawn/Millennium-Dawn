"""Unit tests for merge_gfx_entries de-duplication in gfx_entry_generator."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from gfx_entry_generator import (
    _build_scripted_gui_text,
    _extract_manual_body,
    generate_decisions,
    generate_decisions_desc,
    generate_modifier_icons,
    generate_scripted_gui,
    merge_gfx_entries,
)


def _render(name, tex):
    return f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{tex}"\n\t}}\n'


def _file(tmp_path, *blocks):
    p = tmp_path / "t.gfx"
    p.write_text("spriteTypes = {\n" + "".join(blocks) + "}\n", encoding="utf-8")
    return p


def test_dedup_same_texture(tmp_path):
    p = _file(
        tmp_path,
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_b", "gfx/b.dds"),
    )
    new, changed, orphaned, deduped, written, conflicts = merge_gfx_entries(
        p, {"GFX_a": "gfx/a.dds", "GFX_b": "gfx/b.dds"}, _render
    )
    out = p.read_text(encoding="utf-8")
    assert deduped == ["GFX_a"]
    assert conflicts == []
    assert out.count('name = "GFX_a"') == 1
    assert out.count('name = "GFX_b"') == 1
    assert written is True


def test_dedup_is_idempotent(tmp_path):
    p = _file(
        tmp_path,
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_b", "gfx/b.dds"),
    )
    entries = {"GFX_a": "gfx/a.dds", "GFX_b": "gfx/b.dds"}
    merge_gfx_entries(p, entries, _render)
    second = merge_gfx_entries(p, entries, _render)
    assert second[3] == []  # nothing left to de-duplicate
    assert second[4] is False  # no write on the second pass


def test_dedup_divergent_texture_is_reported(tmp_path):
    p = _file(
        tmp_path,
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_a", "gfx/a2.dds"),
    )
    _, _, _, deduped, _, conflicts = merge_gfx_entries(
        p, {"GFX_a": "gfx/a.dds"}, _render
    )
    out = p.read_text(encoding="utf-8")
    assert deduped == ["GFX_a"]
    assert conflicts == [("GFX_a", "gfx/a.dds", "gfx/a2.dds")]
    assert out.count('name = "GFX_a"') == 1
    assert "gfx/a.dds" in out and "gfx/a2.dds" not in out


def test_dedup_removes_trailing_inline_comment(tmp_path):
    dup_with_comment = (
        "\tspriteType = {\n"
        '\t\tname = "GFX_a"\n'
        '\t\ttexturefile = "gfx/a.dds"\n'
        "\t} # duplicate, remove me\n"
    )
    p = _file(
        tmp_path,
        _render("GFX_a", "gfx/a.dds"),
        dup_with_comment,
        _render("GFX_b", "gfx/b.dds"),
    )
    merge_gfx_entries(p, {"GFX_a": "gfx/a.dds", "GFX_b": "gfx/b.dds"}, _render)
    out = p.read_text(encoding="utf-8")
    assert "remove me" not in out
    assert out.count('name = "GFX_a"') == 1


def test_dedup_of_last_block_keeps_closing_brace(tmp_path):
    p = _file(
        tmp_path,
        _render("GFX_b", "gfx/b.dds"),
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_a", "gfx/a.dds"),
    )
    merge_gfx_entries(p, {"GFX_a": "gfx/a.dds", "GFX_b": "gfx/b.dds"}, _render)
    out = p.read_text(encoding="utf-8")
    assert out.count('name = "GFX_a"') == 1
    assert out.rstrip().endswith("}")


# --- generate_scripted_gui ---------------------------------------------------


def test_scripted_gui_text_groups_by_tag():
    per_tag = {
        "PER": [("GFX_ahmadinejad_portrait", "gfx/x/PER/ahmadinejad_portrait.dds")],
        "ALG": [("GFX_algiers_green", "gfx/x/ALG/algiers_green.dds")],
    }
    text = _build_scripted_gui_text(per_tag, "")
    assert text.startswith("spriteTypes = {")
    assert text.rstrip().endswith("}")
    # sorted tags: ALG before PER
    assert text.index("# ALG") < text.index("# PER")
    assert 'name = "GFX_ahmadinejad_portrait"' in text
    assert "BEGIN GENERATED" in text and "END GENERATED" in text


def test_scripted_gui_manual_region_round_trips():
    manual = '\tprogressbartype = {\n\t\tname = "GFX_bar"\n\t}'
    text = _build_scripted_gui_text({"PER": [("GFX_a", "p/a.dds")]}, manual)
    assert 'name = "GFX_bar"' in text
    assert _extract_manual_body(text).strip() == manual.strip()


def test_generate_scripted_gui_scans_and_preserves_manual(tmp_path):
    root = tmp_path
    per = root / "gfx" / "interface" / "scripted_gui" / "countries" / "PER"
    per.mkdir(parents=True)
    (per / "ahmadinejad_portrait.dds").write_bytes(b"x")
    (root / "interface").mkdir()
    generate_scripted_gui(root)
    out = (root / "interface" / "MD_scripted_gui.gfx").read_text(encoding="utf-8")
    assert 'name = "GFX_ahmadinejad_portrait"' in out
    assert "# PER" in out

    # inject a manual special, regenerate, confirm it survives
    injected = out.replace(
        "\t# === END MANUAL ===",
        '\tprogressbartype = {\n\t\tname = "GFX_keepme"\n\t}\n\t# === END MANUAL ===',
    )
    (root / "interface" / "MD_scripted_gui.gfx").write_text(injected, encoding="utf-8")
    generate_scripted_gui(root)
    out2 = (root / "interface" / "MD_scripted_gui.gfx").read_text(encoding="utf-8")
    assert 'name = "GFX_keepme"' in out2
    assert 'name = "GFX_ahmadinejad_portrait"' in out2


# --- decisions vs decisions_desc split -------------------------------------


def _decisions_tree(root):
    dec = root / "gfx" / "interface" / "decisions"
    (dec / "russia" / "decision_text").mkdir(parents=True)
    (dec / "netherlands" / "decision_text").mkdir(parents=True)
    (dec / "politics").mkdir(parents=True)
    (root / "interface").mkdir()
    # text icons under decision_text/
    (dec / "russia" / "decision_text" / "SOV_desctext_wagner.dds").write_bytes(b"x")
    (
        dec / "netherlands" / "decision_text" / "hol_voc_category_picture.dds"
    ).write_bytes(b"x")
    # a regular decision picture NOT under decision_text/
    (dec / "politics" / "propaganda.dds").write_bytes(b"x")
    return dec


def test_decisions_desc_uses_bare_gfx_and_only_scans_decision_text(tmp_path):
    _decisions_tree(tmp_path)
    generate_decisions_desc(tmp_path)
    out = (tmp_path / "interface" / "MD_decisions_desc.gfx").read_text(encoding="utf-8")
    # bare GFX_<stem>, never a decision_ prefix (£<stem> loc convention)
    assert 'name = "GFX_SOV_desctext_wagner"' in out
    assert 'name = "GFX_hol_voc_category_picture"' in out
    assert "GFX_decision_hol_voc_category_picture" not in out
    # non-decision_text art is not pulled into the desc file
    assert "propaganda" not in out


def test_decisions_skips_decision_text(tmp_path):
    _decisions_tree(tmp_path)
    generate_decisions(tmp_path)
    out = (tmp_path / "interface" / "MD_decisions.gfx").read_text(encoding="utf-8")
    # the regular picture is emitted with the decision_ prefix
    assert 'name = "GFX_decision_propaganda"' in out
    # decision_text/ art is excluded from MD_decisions.gfx entirely
    assert "desctext_wagner" not in out
    assert "hol_voc_category_picture" not in out


def test_generate_scripted_gui_skips_underscore_dirs(tmp_path):
    root = tmp_path
    per = root / "gfx" / "interface" / "scripted_gui" / "countries" / "PER"
    (per / "_manual").mkdir(parents=True)
    (per / "bushehr_red.dds").write_bytes(b"x")
    (per / "_manual" / "propaganda_green.dds").write_bytes(b"x")
    (root / "interface").mkdir()
    generate_scripted_gui(root)
    out = (root / "interface" / "MD_scripted_gui.gfx").read_text(encoding="utf-8")
    assert 'name = "GFX_bushehr_red"' in out
    assert "propaganda_green" not in out  # _manual/ skipped


# --- generate_modifier_icons -----------------------------------------------


def _modifier_icons_tree(root):
    (root / "gfx" / "texticons" / "modifier_icons").mkdir(parents=True)
    (root / "interface").mkdir()
    (
        root / "gfx" / "texticons" / "modifier_icons" / "air_spirit_texticon.dds"
    ).write_bytes(b"x")
    (
        root
        / "gfx"
        / "texticons"
        / "modifier_icons"
        / "Aircraft_Company_cost_factor.dds"
    ).write_bytes(b"x")
    return root


def test_modifier_icons_emits_gfx_full_stem(tmp_path):
    _modifier_icons_tree(tmp_path)
    generate_modifier_icons(tmp_path)
    out = (tmp_path / "interface" / "modifiericons_texticons.gfx").read_text(
        encoding="utf-8"
    )
    # Files whose stem already ends in _texticon: GFX_<full_stem>
    assert 'name = "GFX_air_spirit_texticon"' in out
    assert 'texturefile = "gfx/texticons/modifier_icons/air_spirit_texticon.dds"' in out
    # Files without _texticon suffix: GFX_<stem> (workshop convention)
    assert 'name = "GFX_Aircraft_Company_cost_factor"' in out
    assert (
        'texturefile = "gfx/texticons/modifier_icons/Aircraft_Company_cost_factor.dds"'
        in out
    )
    # Every block has legacy_lazy_load = no
    assert "legacy_lazy_load = no" in out


def test_modifier_icons_preserves_existing_gfx_name(tmp_path):
    """A GFX block already wired in the .gfx keeps its existing name even if the
    stem-derived default would differ (e.g. hand-rolled MD cost-factor entries
    with a `_texticon` suffix). This avoids orphaning and breaking .gui refs."""
    _modifier_icons_tree(tmp_path)
    out_path = tmp_path / "interface" / "modifiericons_texticons.gfx"
    out_path.write_text(
        "spriteTypes = {\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_Aircraft_Company_cost_factor_texticon"\n'
        '\t\ttexturefile = "gfx/texticons/modifier_icons/Aircraft_Company_cost_factor.dds"\n'
        "\t\tlegacy_lazy_load = no\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    generate_modifier_icons(tmp_path)
    out = out_path.read_text(encoding="utf-8")
    # The existing GFX_Aircraft_Company_cost_factor_texticon block is preserved verbatim
    assert 'name = "GFX_Aircraft_Company_cost_factor_texticon"' in out
    # No duplicate GFX_Aircraft_Company_cost_factor block was added
    assert 'name = "GFX_Aircraft_Company_cost_factor"' not in out


def test_modifier_icons_protected_set_keeps_role_icon_texturefile(tmp_path):
    """A protected GFX name (e.g. GFX_anti_air_texticon role icon) keeps its
    existing non-modifier_icons texturefile. The local .dds with the same stem
    is left unreferenced rather than added under a duplicate GFX name; the
    role icon block survives intact so vanilla references keep resolving."""
    (tmp_path / "gfx" / "texticons" / "modifier_icons").mkdir(parents=True)
    (tmp_path / "interface").mkdir()
    (
        tmp_path / "gfx" / "texticons" / "modifier_icons" / "anti_air_texticon.dds"
    ).write_bytes(b"x")
    out_path = tmp_path / "interface" / "modifiericons_texticons.gfx"
    out_path.write_text(
        "spriteTypes = {\n"
        "\tSpriteType = {\n"
        '\t\tname = "GFX_anti_air_texticon"\n'
        '\t\ttexturefile = "gfx/interface/equipmentdesigner/tanks/role_icons/role_icon_3.dds"\n'
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    generate_modifier_icons(tmp_path)
    out = out_path.read_text(encoding="utf-8")
    # The role-icon texturefile survives untouched
    assert (
        'texturefile = "gfx/interface/equipmentdesigner/tanks/role_icons/role_icon_3.dds"'
        in out
    )
    # Only the role-icon block exists (no duplicate local entry was added)
    assert out.count('name = "GFX_anti_air_texticon"') == 1


def test_modifier_icons_idempotent(tmp_path):
    _modifier_icons_tree(tmp_path)
    generate_modifier_icons(tmp_path)
    first = (tmp_path / "interface" / "modifiericons_texticons.gfx").read_text(
        encoding="utf-8"
    )
    generate_modifier_icons(tmp_path)
    second = (tmp_path / "interface" / "modifiericons_texticons.gfx").read_text(
        encoding="utf-8"
    )
    assert first == second
