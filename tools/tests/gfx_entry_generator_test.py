"""GFX entry generator: image scanning, the merge into an existing .gfx file,
each generator's naming rule, the focus titlebar and scripted GUI files, and
the menu."""

import gfx_entry_generator as generator
import pytest
from shared.paths import REPO_ROOT
from shared.suite import read_text, write_text


def _render(name, texture):
    return (
        f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{texture}"\n\t}}\n'
    )


def _gfx_file(tmp_path, *blocks):
    return write_text(tmp_path / "t.gfx", "spriteTypes = {\n" + "".join(blocks) + "}\n")


def _images(root, directory, *names):
    """Touch image files under `directory`, and make the interface folder."""
    for name in names:
        path = root / directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
    (root / "interface").mkdir(exist_ok=True)


def _crlf_only(path):
    raw = path.read_bytes()
    return 0 < raw.count(b"\r\n") == raw.count(b"\n") == raw.count(b"\r")


# ---- scanning and parsing ----------------------------------------------------


def test_scan_images_finds_image_files_recursively_in_name_order(tmp_path):
    _images(tmp_path, "scan/nested", "B.DDS", "a.png", "c.TgA", "ignored.jpg")
    write_text(tmp_path / "scan" / "not-an-image.txt", "fixture")

    files = generator.scan_images(tmp_path / "scan")

    assert [path.name for path in files] == ["a.png", "B.DDS", "c.TgA"]
    assert generator.rel_texture_path(files[0], tmp_path) == "scan/nested/a.png"


def test_check_duplicate_reports_the_second_use_of_a_name():
    seen = set()

    assert not generator.check_duplicate("GFX_a", seen, "a.png")
    assert generator.check_duplicate("GFX_a", seen, "other.png")


def test_named_blocks_are_parsed_with_whatever_fields_they_have():
    parsed = generator._parse_named_blocks(
        _render("GFX_good", "gfx/good.dds")
        + '\tspriteType = {\n\t\tname = "GFX_no_texture"\n\t}\n'
        + '\tspriteType = {\n\t\ttexturefile = "gfx/no_name.dds"\n\t}\n'
        # An unclosed block ends the parse.
        + "\tspriteType = {\n"
    )

    assert [(name, texture) for name, texture, _start, _end in parsed] == [
        ("GFX_good", "gfx/good.dds"),
        ("GFX_no_texture", None),
        (None, "gfx/no_name.dds"),
    ]
    assert generator._match_brace("{ nested { value } }", 0) == 19
    with pytest.raises(ValueError, match="Unmatched"):
        generator._match_brace("{", 0)


def test_text_helpers_leave_text_alone_without_a_complete_block_or_marker():
    begin = generator.SG_MANUAL_BEGIN

    assert generator._remove_block_by_name('name = "GFX_a"', "GFX_a")[1] is False
    assert (
        generator._remove_block_by_name('spriteType = { name = "GFX_a"', "GFX_a")[1]
        is False
    )
    assert generator._strip_region("before\nafter", "BEGIN", "END") == "before\nafter"
    assert generator._strip_region("before\nBEGIN\nbody", "BEGIN", "END") == "before\n"
    assert generator._extract_manual_body("no markers") == ""
    assert generator._extract_manual_body(f"{begin}\nbody") == ""
    assert (
        generator._remove_tag_headers("### keep ###\n### remove ###", ["remove"])
        == "### keep ###"
    )
    assert generator._collapse_blanks("a\n\n\n\nb") == "a\n\nb"


def test_missing_file_reads_as_empty_and_a_failed_write_is_reported(tmp_path, capsys):
    assert generator._read_lf(tmp_path / "missing.gfx") == ""

    generator._write_with_newline(tmp_path, "text", "\n")

    assert "Failed to write" in capsys.readouterr().out


def test_long_name_lists_are_capped():
    assert generator._format_names(["b", "a"], cap=3) == "a, b"
    assert generator._format_names(["0", "1", "2", "3"], cap=2).endswith("+2 more")


# ---- merging into an existing .gfx file --------------------------------------


def test_merge_adds_changes_and_keeps_orphans_protected_names_and_crlf(tmp_path):
    protected = frozenset({"GFX_protected"})
    path = write_text(
        tmp_path / "entries.gfx",
        (
            "spriteTypes = {\n"
            + _render("GFX_change", "old.dds")
            + _render("GFX_orphan", "orphan.dds")
            + _render("GFX_protected", "external.dds")
            + "}\n"
        ).replace("\n", "\r\n"),
    )
    entries = {
        "GFX_change": "new.dds",
        "GFX_new": "new-entry.dds",
        "GFX_protected": "local.dds",
    }

    result = generator.merge_gfx_entries(path, entries, _render, protected=protected)

    assert result[:5] == (["GFX_new"], ["GFX_change"], ["GFX_orphan"], [], True)
    text = read_text(path)
    assert "new.dds" in text and "old.dds" not in text
    # A protected name keeps the texture it already points at.
    assert "external.dds" in text and "local.dds" not in text
    assert "GFX_orphan" in text
    assert _crlf_only(path)
    # Nothing is written when the file is already up to date.
    assert (
        generator.merge_gfx_entries(path, entries, _render, protected=protected)[4]
        is False
    )


def test_merge_report_names_a_texture_mismatch_or_says_up_to_date(capsys):
    generator._print_merge_report(
        "entries.gfx",
        ["new"],
        ["changed"],
        ["orphan"],
        ["duplicate"],
        True,
        [("duplicate", "kept", "dropped")],
    )
    report = capsys.readouterr().out
    assert "TEXTURE MISMATCH" in report and "already up to date" not in report

    generator._print_merge_report("entries.gfx", [], [], [], [], False)
    assert "already up to date" in capsys.readouterr().out


def test_dedup_same_texture(tmp_path):
    path = _gfx_file(
        tmp_path,
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_b", "gfx/b.dds"),
    )
    entries = {"GFX_a": "gfx/a.dds", "GFX_b": "gfx/b.dds"}

    _new, _changed, _orphaned, deduped, written, conflicts = (
        generator.merge_gfx_entries(path, entries, _render)
    )

    out = read_text(path)
    assert deduped == ["GFX_a"]
    assert conflicts == []
    assert out.count('name = "GFX_a"') == 1
    assert out.count('name = "GFX_b"') == 1
    assert written is True
    # The second pass finds nothing to remove and writes nothing.
    assert generator.merge_gfx_entries(path, entries, _render)[3:5] == ([], False)


def test_dedup_divergent_texture_is_reported(tmp_path):
    path = _gfx_file(
        tmp_path, _render("GFX_a", "gfx/a.dds"), _render("GFX_a", "gfx/a2.dds")
    )

    _, _, _, deduped, _, conflicts = generator.merge_gfx_entries(
        path, {"GFX_a": "gfx/a.dds"}, _render
    )

    out = read_text(path)
    assert deduped == ["GFX_a"]
    assert conflicts == [("GFX_a", "gfx/a.dds", "gfx/a2.dds")]
    assert out.count('name = "GFX_a"') == 1
    assert "gfx/a.dds" in out and "gfx/a2.dds" not in out


def test_dedup_removes_trailing_inline_comment(tmp_path):
    duplicate = _render("GFX_a", "gfx/a.dds").replace(
        "\t}\n", "\t} # duplicate, remove me\n"
    )
    path = _gfx_file(
        tmp_path,
        _render("GFX_a", "gfx/a.dds"),
        duplicate,
        _render("GFX_b", "gfx/b.dds"),
    )

    generator.merge_gfx_entries(
        path, {"GFX_a": "gfx/a.dds", "GFX_b": "gfx/b.dds"}, _render
    )

    out = read_text(path)
    assert "remove me" not in out
    assert out.count('name = "GFX_a"') == 1


def test_dedup_of_last_block_keeps_closing_brace(tmp_path):
    path = _gfx_file(
        tmp_path,
        _render("GFX_b", "gfx/b.dds"),
        _render("GFX_a", "gfx/a.dds"),
        _render("GFX_a", "gfx/a.dds"),
    )

    generator.merge_gfx_entries(
        path, {"GFX_a": "gfx/a.dds", "GFX_b": "gfx/b.dds"}, _render
    )

    out = read_text(path)
    assert out.count('name = "GFX_a"') == 1
    assert out.rstrip().endswith("}")


# ---- naming rule of each generator -------------------------------------------

# A prefix the file name already carries is not added twice, and two files
# that map to one name give one entry.
# case: (generator, image folder, output file, {image file: sprite name})
_NAMING_CASES = {
    "event pictures": (
        "generate_event_pictures",
        "gfx/event_pictures",
        "MD_eventpictures.gfx",
        {
            "plain.dds": "GFX_plain",
            "nested/GFX_existing.png": "GFX_existing",
            "nested/GFX_existing.tga": "GFX_existing",
        },
    ),
    "ideas": (
        "generate_ideas",
        "gfx/interface/ideas",
        "MD_ideas.gfx",
        {
            "idea_reform.dds": "GFX_idea_reform",
            "reform.png": "GFX_idea_reform",
            "traits_strip.dds": "GFX_idea_traits_strip",
        },
    ),
    "party icons": (
        "generate_party_icons",
        "gfx/texticons/parties_icons",
        "MD_parties_icons.gfx",
        {"social_democrat.dds": "GFX_social_democrat"},
    ),
    "intelligence agencies": (
        "generate_intelligence_icons",
        "gfx/interface/operatives/agencies",
        "MD_intelligence_icons.gfx",
        {
            "agency_logo_PER.dds": "GFX_intelligence_agency_logo_PER",
            "GER.png": "GFX_intelligence_agency_logo_GER",
        },
    ),
    "decisions": (
        "generate_decisions",
        "gfx/interface/decisions",
        "MD_decisions.gfx",
        {
            "regular/trade.tga": "GFX_decision_trade",
            "regular/decision_category_reform.png": "GFX_decision_category_reform",
        },
    ),
}


@pytest.mark.parametrize(
    ("function", "folder", "output", "names"),
    _NAMING_CASES.values(),
    ids=_NAMING_CASES,
)
def test_generator_names_each_sprite_once(tmp_path, function, folder, output, names):
    _images(tmp_path, folder, *names)

    getattr(generator, function)(tmp_path)

    text = read_text(tmp_path / "interface" / output)
    for name in set(names.values()):
        assert text.count(f'name = "{name}"') == 1


def _decisions_tree(root):
    _images(
        root,
        "gfx/interface/decisions",
        # Text icons sit under decision_text/. The last one does not.
        "russia/decision_text/SOV_desctext_wagner.dds",
        "netherlands/decision_text/hol_voc_category_picture.dds",
        "politics/propaganda.dds",
    )


def test_decisions_desc_uses_bare_gfx_and_only_scans_decision_text(tmp_path):
    _decisions_tree(tmp_path)

    generator.generate_decisions_desc(tmp_path)

    out = read_text(tmp_path / "interface" / "MD_decisions_desc.gfx")
    # Bare GFX_<stem>, never a decision_ prefix: the loc key is £<stem>.
    assert 'name = "GFX_SOV_desctext_wagner"' in out
    assert 'name = "GFX_hol_voc_category_picture"' in out
    assert "GFX_decision_hol_voc_category_picture" not in out
    assert "propaganda" not in out
    assert "legacy_lazy_load = no" in out


def test_decisions_skips_decision_text(tmp_path):
    _decisions_tree(tmp_path)

    generator.generate_decisions(tmp_path)

    out = read_text(tmp_path / "interface" / "MD_decisions.gfx")
    assert 'name = "GFX_decision_propaganda"' in out
    assert "desctext_wagner" not in out
    assert "hol_voc_category_picture" not in out


# ---- goals -------------------------------------------------------------------


def test_goals_scan_recursively_and_write_one_shine_per_name(tmp_path):
    _images(
        tmp_path,
        "gfx/interface/goals",
        "alpha.dds",
        "nested/alpha.png",
        "nested/gamma.png",
        "beta.tga",
    )

    generator.generate_goals(tmp_path, gfxbool=1)

    output = read_text(tmp_path / "interface" / "goals.gfx")
    shine = read_text(tmp_path / "interface" / "goals_shine.gfx")
    assert output.count('name = "GFX_alpha"') == 1
    assert "gfx/interface/goals/nested/gamma.png" in output
    assert 'name = "GFX_gamma_shine"' in shine
    assert 'name = "GFX_beta_shine"' in shine
    assert 'effectfile = "gfx/FX/buttonstate.lua"' in shine
    assert "spriteType = { \n" not in shine


def test_goals_prompt_repeats_until_the_prefix_choice_is_valid(
    tmp_path, monkeypatch, capsys
):
    _images(tmp_path, "gfx/interface/goals", "goal.dds")
    answers = iter(["", "not a number", "4", "0"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    generator.generate_goals(tmp_path)

    # The answer 0 means no GFX_ prefix.
    assert 'name = "goal"' in read_text(tmp_path / "interface" / "goals.gfx")
    assert "Input cannot be empty" in capsys.readouterr().out


# ---- modifier icons ----------------------------------------------------------

_MODIFIER_ICONS = "gfx/texticons/modifier_icons"
_MODIFIER_GFX = "interface/modifiericons_texticons.gfx"


def _modifier_icons_tree(root):
    _images(
        root,
        _MODIFIER_ICONS,
        "air_spirit_texticon.dds",
        "Aircraft_Company_cost_factor.dds",
    )


def test_modifier_icons_emits_gfx_full_stem(tmp_path):
    _modifier_icons_tree(tmp_path)

    generator.generate_modifier_icons(tmp_path)

    out = read_text(tmp_path / _MODIFIER_GFX)
    assert 'name = "GFX_air_spirit_texticon"' in out
    assert f'texturefile = "{_MODIFIER_ICONS}/air_spirit_texticon.dds"' in out
    assert 'name = "GFX_Aircraft_Company_cost_factor"' in out
    assert f'texturefile = "{_MODIFIER_ICONS}/Aircraft_Company_cost_factor.dds"' in out
    assert "legacy_lazy_load = no" in out
    # A second run changes nothing.
    generator.generate_modifier_icons(tmp_path)
    assert read_text(tmp_path / _MODIFIER_GFX) == out


def test_modifier_icons_preserves_existing_gfx_name(tmp_path):
    # A block already in the file keeps its name even when the name the stem
    # would give differs. Renaming it would orphan the .gui references.
    _modifier_icons_tree(tmp_path)
    write_text(
        tmp_path / _MODIFIER_GFX,
        "spriteTypes = {\n"
        + _render(
            "GFX_Aircraft_Company_cost_factor_texticon",
            f"{_MODIFIER_ICONS}/Aircraft_Company_cost_factor.dds",
        )
        + "}\n",
    )

    generator.generate_modifier_icons(tmp_path)

    out = read_text(tmp_path / _MODIFIER_GFX)
    assert 'name = "GFX_Aircraft_Company_cost_factor_texticon"' in out
    assert 'name = "GFX_Aircraft_Company_cost_factor"' not in out


def test_modifier_icons_protected_set_keeps_role_icon_texturefile(tmp_path):
    # GFX_anti_air_texticon is a vanilla role icon. It keeps its texture, and
    # the local file with the same stem is not added under the same name.
    role_icon = "gfx/interface/equipmentdesigner/tanks/role_icons/role_icon_3.dds"
    _images(tmp_path, _MODIFIER_ICONS, "anti_air_texticon.dds")
    write_text(
        tmp_path / _MODIFIER_GFX,
        "spriteTypes = {\n\tSpriteType = {\n"
        '\t\tname = "GFX_anti_air_texticon"\n'
        f'\t\ttexturefile = "{role_icon}"\n\t}}\n}}\n',
    )

    generator.generate_modifier_icons(tmp_path)

    out = read_text(tmp_path / _MODIFIER_GFX)
    assert f'texturefile = "{role_icon}"' in out
    assert out.count('name = "GFX_anti_air_texticon"') == 1


# ---- scripted GUI ------------------------------------------------------------


def test_scripted_gui_text_groups_by_tag():
    per_tag = {
        "PER": [("GFX_ahmadinejad_portrait", "gfx/x/PER/ahmadinejad_portrait.dds")],
        "ALG": [("GFX_algiers_green", "gfx/x/ALG/algiers_green.dds")],
    }

    text = generator._build_scripted_gui_text(per_tag, "")

    assert text.startswith("spriteTypes = {")
    assert text.rstrip().endswith("}")
    assert text.index("# ALG") < text.index("# PER")
    assert 'name = "GFX_ahmadinejad_portrait"' in text
    assert "BEGIN GENERATED" in text and "END GENERATED" in text


def test_scripted_gui_manual_region_round_trips():
    manual = '\tprogressbartype = {\n\t\tname = "GFX_bar"\n\t}'

    text = generator._build_scripted_gui_text({"PER": [("GFX_a", "p/a.dds")]}, manual)

    assert 'name = "GFX_bar"' in text
    assert generator._extract_manual_body(text).strip() == manual.strip()


def test_scripted_gui_scan_keeps_the_manual_region_and_crlf(tmp_path, capsys):
    countries = "gfx/interface/scripted_gui/countries"
    # PER and ALG both have a `z`. A folder starting with `_` is not scanned.
    _images(
        tmp_path,
        countries,
        "PER/z.dds",
        "PER/_manual/skip.png",
        "ALG/z.png",
        "ALG/a.tga",
    )
    (tmp_path / countries / "EMPTY").mkdir()
    out = tmp_path / "interface" / "MD_scripted_gui.gfx"

    generator.generate_scripted_gui(tmp_path)

    initial = read_text(out)
    assert initial.count('name = "GFX_z"') == 1
    assert 'name = "GFX_a"' in initial
    assert "# ALG" in initial
    assert "skip" not in initial

    manual = initial.replace(
        "\t# === END MANUAL ===",
        '\tprogressbartype = {\n\t\tname = "GFX_manual"\n\t}\n\t# === END MANUAL ===',
    )
    write_text(out, manual.replace("\n", "\r\n"))
    generator.generate_scripted_gui(tmp_path)

    assert "already up to date" in capsys.readouterr().out

    _images(tmp_path, countries, "ALG/b.png")
    generator.generate_scripted_gui(tmp_path)

    rewritten = read_text(out)
    assert "GFX_manual" in rewritten and 'name = "GFX_b"' in rewritten
    assert _crlf_only(out)


# ---- focus titlebars ---------------------------------------------------------

_TITLEBARS = "gfx/interface/focusview/titlebar"


def _titlebar(state, suffix):
    return f"focus_{state}_joint_{suffix}_bg.dds"


def _focus_fixture(root):
    """Titlebar art for a full set (alpha) and two partial ones, and CRLF files
    that already hold hand-made entries and an old generated region."""
    _images(
        root,
        _TITLEBARS,
        _titlebar("unavailable", "alpha"),
        _titlebar("can_start", "alpha"),
        _titlebar("completed", "alpha"),
        _titlebar("can_start", "beta"),
        _titlebar("unavailable", "gamma"),
    )
    epsilon = f"{_TITLEBARS}/{_titlebar('can_start', 'epsilon')}"
    gfx = (
        "spriteTypes = {\n"
        "\t# comment before generated content\n"
        + _render(
            "GFX_focus_unavailable_joint_alpha",
            f"{_TITLEBARS}/{_titlebar('unavailable', 'alpha')}",
        )
        + _render("GFX_focus_can_start_joint_epsilon", epsilon)
        + _render("GFX_focus_current_joint_epsilon", epsilon)
        + _render("GFX_focus_can_start_joint_delta", "gfx/hand/custom.dds")
        + "\t### alpha ###\n"
        + f"{generator.GFX_BEGIN}\nold generated\n{generator.GFX_END}\n"
        + "}\n"
    )
    styles = (
        "style = {\n"
        "\tname = JOINT_alpha_focus_style\n"
        "\tavailable = GFX_focus_can_start_joint_alpha\n"
        "}\n"
        f"{generator.STYLE_BEGIN}\nold styles\n{generator.STYLE_END}\n"
    )
    gfx_path = write_text(
        root / "interface" / "nationalfocusview.gfx", gfx.replace("\n", "\r\n")
    )
    styles_path = write_text(
        root / "common" / "national_focus" / "00_titlebar_styles.txt",
        styles.replace("\n", "\r\n"),
    )
    return gfx_path, styles_path


def test_focus_titlebars_fill_in_partial_sets_and_add_their_styles(tmp_path, capsys):
    gfx, styles = _focus_fixture(tmp_path)

    generator.generate_focus_titlebars(tmp_path)

    output = read_text(gfx)
    style_output = read_text(styles)
    assert 'name = "GFX_focus_unavailable_joint_alpha"' in output
    assert 'name = "GFX_focus_current_joint_alpha"' in output
    assert "GFX_focus_unavailable_joint_beta" not in output
    assert 'name = "GFX_focus_current_joint_beta"' in output
    assert "GFX_focus_can_start_joint_delta" in output
    assert "GFX_focus_unavailable_joint_gamma" not in output
    assert "JOINT_beta_focus_style" in style_output
    assert "JOINT_epsilon_focus_style" in style_output
    assert output.count(generator.GFX_BEGIN) == 1
    assert "Incomplete sets" in capsys.readouterr().out

    generator.generate_focus_titlebars(tmp_path)

    assert "0 new style(s) added" in capsys.readouterr().out
    assert _crlf_only(gfx) and _crlf_only(styles)


def test_focus_titlebars_need_both_of_their_files(tmp_path, capsys):
    (tmp_path / _TITLEBARS).mkdir(parents=True)

    generator.generate_focus_titlebars(tmp_path)
    assert "Missing file" in capsys.readouterr().out

    # The .gfx file alone is not enough: the styles file is missing too.
    write_text(tmp_path / "interface" / "nationalfocusview.gfx", "{}")
    generator.generate_focus_titlebars(tmp_path)
    assert "Missing file" in capsys.readouterr().out


# ---- the menu ----------------------------------------------------------------

# The menu number of each generator, in order.
_MENU = (
    "generate_goals",
    "generate_event_pictures",
    "generate_ideas",
    "generate_party_icons",
    "generate_intelligence_icons",
    "generate_decisions",
    "generate_focus_titlebars",
    "generate_scripted_gui",
    "generate_decisions_desc",
    "generate_modifier_icons",
)


_MISSING_FOLDER = dict.fromkeys(_MENU, "Directory does not exist") | {
    "generate_focus_titlebars": "Titlebar directory not found"
}


@pytest.mark.parametrize(("function", "message"), _MISSING_FOLDER.items())
def test_generator_reports_a_missing_source_folder(tmp_path, capsys, function, message):
    getattr(generator, function)(tmp_path)

    assert message in capsys.readouterr().out


@pytest.mark.parametrize(
    ("selection", "function"), [(str(n), f) for n, f in enumerate(_MENU, start=1)]
)
def test_main_dispatches_each_menu_number(selection, function, monkeypatch):
    calls = []
    monkeypatch.setattr(generator, function, calls.append)
    monkeypatch.setattr("builtins.input", lambda _prompt: selection)

    generator.main()

    assert calls == [REPO_ROOT]


def test_main_rejects_invalid_input_before_dispatch(monkeypatch, capsys):
    answers = iter(["", "not numeric", "0", "11", "2"])
    calls = []
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(generator, "generate_event_pictures", calls.append)

    generator.main()

    output = capsys.readouterr().out
    assert "Input cannot be empty" in output
    assert "Invalid input" in output
    assert "Invalid selection" in output
    assert calls == [REPO_ROOT]
