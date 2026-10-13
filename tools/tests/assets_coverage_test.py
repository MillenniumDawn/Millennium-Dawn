from pathlib import Path

import gfx_entry_generator as generator
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _write_text(path, text, newline=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline=newline) as stream:
        stream.write(text)


def _read_text(path):
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _render(name, texture):
    return (
        f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{texture}"\n\t}}\n'
    )


def test_gfx_paths_scanning_and_block_parser_cover_recursive_inputs(tmp_path):
    scan = tmp_path / "scan"
    nested = scan / "nested"
    nested.mkdir(parents=True)
    for name in ("B.DDS", "a.png", "c.TgA", "ignored.jpg"):
        (nested / name).write_bytes(b"fixture")
    (scan / "not-an-image.txt").write_bytes(b"fixture")
    files = generator.scan_images(scan)
    assert [path.name for path in files] == ["a.png", "B.DDS", "c.TgA"]
    assert generator.rel_texture_path(files[0], tmp_path) == "scan/nested/a.png"
    assert generator.interface_path(tmp_path, "icons.gfx") == (
        tmp_path / "interface" / "icons.gfx"
    )

    seen = set()
    assert not generator.check_duplicate("GFX_a", seen, "a.png")
    assert generator.check_duplicate("GFX_a", seen, "other.png")

    parsed = list(
        generator._parse_named_blocks(
            _render("GFX_good", "gfx/good.dds")
            + '\tspriteType = {\n\t\tname = "GFX_no_texture"\n\t}\n'
            + '\tspriteType = {\n\t\ttexturefile = "gfx/no_name.dds"\n\t}\n'
            + "\tspriteType = {\n"
        )
    )
    assert [(name, texture) for name, texture, _start, _end in parsed] == [
        ("GFX_good", "gfx/good.dds"),
        ("GFX_no_texture", None),
        (None, "gfx/no_name.dds"),
    ]
    assert generator._match_brace("{ nested { value } }", 0) == 19
    with pytest.raises(ValueError, match="Unmatched"):
        generator._match_brace("{", 0)

    assert generator._format_names(["b", "a"], cap=3) == "a, b"
    assert generator._format_names([str(i) for i in range(4)], cap=2).endswith(
        "+2 more"
    )


def test_gfx_merge_reports_changes_orphans_protection_and_newlines(tmp_path, capsys):
    path = tmp_path / "entries.gfx"
    _write_text(
        path,
        (
            "spriteTypes = {\r\n"
            + _render("GFX_change", "old.dds").replace("\n", "\r\n")
            + _render("GFX_orphan", "orphan.dds").replace("\n", "\r\n")
            + _render("GFX_protected", "external.dds").replace("\n", "\r\n")
            + "}\r\n"
        ),
    )
    entries = {
        "GFX_change": "new.dds",
        "GFX_new": "new-entry.dds",
        "GFX_protected": "local.dds",
    }
    result = generator.merge_gfx_entries(
        path, entries, _render, protected=frozenset({"GFX_protected"})
    )
    assert result[:4] == (["GFX_new"], ["GFX_change"], ["GFX_orphan"], [])
    assert result[4] is True
    text = _read_text(path)
    assert "new.dds" in text and "old.dds" not in text
    assert "external.dds" in text and "local.dds" not in text
    assert "GFX_orphan" in text
    raw = path.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")

    second = generator.merge_gfx_entries(
        path, entries, _render, protected=frozenset({"GFX_protected"})
    )
    assert second[4] is False

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


def test_gfx_low_level_error_and_region_helpers(tmp_path, capsys):
    assert generator._read_lf(tmp_path / "missing.gfx") == ""
    assert generator._newline_of("line\r\n") == "\r\n"
    assert generator._newline_of("line\n") == "\n"
    assert generator._remove_block_by_name('name = "GFX_a"', "GFX_a")[1] is False
    assert (
        generator._remove_block_by_name('spriteType = { name = "GFX_a"', "GFX_a")[1]
        is False
    )
    assert generator._strip_region("before\nafter", "BEGIN", "END") == "before\nafter"
    assert generator._strip_region("before\nBEGIN\nbody", "BEGIN", "END") == "before\n"
    assert generator._extract_manual_body("no markers") == ""
    assert generator._extract_manual_body(f"{generator.SG_MANUAL_BEGIN}\nbody") == ""
    assert (
        generator._remove_tag_headers("### keep ###\n### remove ###", ["remove"])
        == "### keep ###"
    )
    assert generator._collapse_blanks("a\n\n\n\nb") == "a\n\nb"

    bad_target = tmp_path / "directory"
    bad_target.mkdir()
    generator._write_with_newline(bad_target, "text", "\n")
    assert "Failed to write" in capsys.readouterr().out


def test_gfx_goals_scans_recursively_and_deduplicates(tmp_path):
    (tmp_path / "interface").mkdir()
    goals = tmp_path / "gfx" / "interface" / "goals"
    (goals / "nested").mkdir(parents=True)
    (goals / "alpha.dds").write_bytes(b"fixture")
    (goals / "nested" / "alpha.png").write_bytes(b"fixture")
    (goals / "nested" / "gamma.png").write_bytes(b"fixture")
    (goals / "beta.tga").write_bytes(b"fixture")

    generator.generate_goals(tmp_path, gfxbool=1)

    output = _read_text(tmp_path / "interface" / "goals.gfx")
    shine = _read_text(tmp_path / "interface" / "goals_shine.gfx")
    assert 'name = "GFX_alpha"' in output
    assert output.count('name = "GFX_alpha"') == 1
    assert "gfx/interface/goals/nested/gamma.png" in output
    assert 'name = "GFX_gamma_shine"' in shine
    assert 'name = "GFX_beta_shine"' in shine
    assert 'effectfile = "gfx/FX/buttonstate.lua"' in shine


def test_gfx_goals_interactive_validation_and_event_names(
    tmp_path, monkeypatch, capsys
):
    (tmp_path / "interface").mkdir()
    goals = tmp_path / "gfx" / "interface" / "goals"
    goals.mkdir(parents=True)
    (goals / "goal.dds").write_bytes(b"fixture")
    answers = iter(["", "not a number", "4", "0"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    generator.generate_goals(tmp_path)
    assert 'name = "goal"' in _read_text(tmp_path / "interface" / "goals.gfx")
    assert "Input cannot be empty" in capsys.readouterr().out

    event = tmp_path / "gfx" / "event_pictures"
    (event / "nested").mkdir(parents=True)
    (event / "plain.dds").write_bytes(b"fixture")
    (event / "nested" / "GFX_existing.png").write_bytes(b"fixture")
    (event / "nested" / "GFX_existing.tga").write_bytes(b"fixture")
    generator.generate_event_pictures(tmp_path)
    output = _read_text(tmp_path / "interface" / "MD_eventpictures.gfx")
    assert 'name = "GFX_plain"' in output
    assert output.count('name = "GFX_existing"') == 1


def test_gfx_ideas_parties_intelligence_and_decisions_naming(tmp_path):
    (tmp_path / "interface").mkdir()
    ideas = tmp_path / "gfx" / "interface" / "ideas"
    ideas.mkdir(parents=True)
    for name in ("idea_reform.dds", "reform.png", "traits_strip.dds"):
        (ideas / name).write_bytes(b"fixture")
    generator.generate_ideas(tmp_path)
    ideas_text = _read_text(tmp_path / "interface" / "MD_ideas.gfx")
    assert 'name = "GFX_idea_reform"' in ideas_text
    assert ideas_text.count('name = "GFX_idea_traits_strip"') == 1

    parties = tmp_path / "gfx" / "texticons" / "parties_icons"
    parties.mkdir(parents=True)
    (parties / "social_democrat.dds").write_bytes(b"fixture")
    generator.generate_party_icons(tmp_path)
    assert 'name = "GFX_social_democrat"' in _read_text(
        tmp_path / "interface" / "MD_parties_icons.gfx"
    )

    agencies = tmp_path / "gfx" / "interface" / "operatives" / "agencies"
    agencies.mkdir(parents=True)
    (agencies / "agency_logo_PER.dds").write_bytes(b"fixture")
    (agencies / "GER.png").write_bytes(b"fixture")
    generator.generate_intelligence_icons(tmp_path)
    agency_text = _read_text(tmp_path / "interface" / "MD_intelligence_icons.gfx")
    assert 'name = "GFX_intelligence_agency_logo_PER"' in agency_text
    assert 'name = "GFX_intelligence_agency_logo_GER"' in agency_text

    decisions = tmp_path / "gfx" / "interface" / "decisions"
    (decisions / "country" / "decision_text").mkdir(parents=True)
    (decisions / "regular").mkdir(parents=True)
    (decisions / "country" / "decision_text" / "war.dds").write_bytes(b"fixture")
    (decisions / "regular" / "decision_category_reform.png").write_bytes(b"fixture")
    (decisions / "regular" / "trade.tga").write_bytes(b"fixture")
    generator.generate_decisions(tmp_path)
    decisions_text = _read_text(tmp_path / "interface" / "MD_decisions.gfx")
    assert 'name = "GFX_decision_trade"' in decisions_text
    assert 'name = "GFX_decision_category_reform"' in decisions_text
    assert "GFX_decision_war" not in decisions_text

    generator.generate_decisions_desc(tmp_path)
    desc_text = _read_text(tmp_path / "interface" / "MD_decisions_desc.gfx")
    assert 'name = "GFX_war"' in desc_text
    assert "legacy_lazy_load = no" in desc_text


def test_gfx_modifier_icons_preserve_external_and_existing_names(tmp_path):
    icons = tmp_path / "gfx" / "texticons" / "modifier_icons"
    icons.mkdir(parents=True)
    (icons / "air_cost.dds").write_bytes(b"fixture")
    (icons / "anti_air_texticon.png").write_bytes(b"fixture")
    out = tmp_path / "interface" / "modifiericons_texticons.gfx"
    _write_text(
        out,
        "spriteTypes = {\n"
        + _render("GFX_AirCost_texticon", "gfx/texticons/modifier_icons/air_cost.dds")
        + _render("GFX_anti_air_texticon", "gfx/vanilla/role.dds")
        + "}\n",
    )

    generator.generate_modifier_icons(tmp_path)

    text = _read_text(out)
    assert 'name = "GFX_AirCost_texticon"' in text
    assert 'name = "GFX_air_cost"' not in text
    assert 'texturefile = "gfx/vanilla/role.dds"' in text
    assert text.count('name = "GFX_anti_air_texticon"') == 1


def test_gfx_scripted_gui_preserves_manual_region_and_crlf(tmp_path, capsys):
    (tmp_path / "interface").mkdir()
    countries = tmp_path / "gfx" / "interface" / "scripted_gui" / "countries"
    (countries / "PER" / "_manual").mkdir(parents=True)
    (countries / "ALG").mkdir(parents=True)
    (countries / "EMPTY").mkdir(parents=True)
    (countries / "PER" / "z.dds").write_bytes(b"fixture")
    (countries / "PER" / "_manual" / "skip.png").write_bytes(b"fixture")
    (countries / "ALG" / "z.png").write_bytes(b"fixture")
    (countries / "ALG" / "a.tga").write_bytes(b"fixture")

    generator.generate_scripted_gui(tmp_path)
    out = tmp_path / "interface" / "MD_scripted_gui.gfx"
    initial = _read_text(out)
    assert 'name = "GFX_z"' in initial
    assert initial.count('name = "GFX_z"') == 1
    assert 'name = "GFX_a"' in initial
    assert "skip" not in initial

    manual = initial.replace(
        "\t# === END MANUAL ===",
        '\tprogressbartype = {\n\t\tname = "GFX_manual"\n\t}\n\t# === END MANUAL ===',
    )
    _write_text(out, manual.replace("\n", "\r\n"))
    generator.generate_scripted_gui(tmp_path)
    assert "GFX_manual" in _read_text(out)
    raw = out.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")
    assert "already up to date" in capsys.readouterr().out


def _focus_fixture(root):
    titlebar = root / "gfx" / "interface" / "focusview" / "titlebar"
    titlebar.mkdir(parents=True)
    for state, suffix in (
        ("unavailable", "alpha"),
        ("can_start", "alpha"),
        ("completed", "alpha"),
        ("can_start", "beta"),
        ("unavailable", "gamma"),
    ):
        (titlebar / f"focus_{state}_joint_{suffix}_bg.dds").write_bytes(b"fixture")
    (root / "interface").mkdir(parents=True)
    (root / "common" / "national_focus").mkdir(parents=True)
    gfx = (
        "spriteTypes = {\n"
        "\t# comment before generated content\n"
        + _render(
            "GFX_focus_unavailable_joint_alpha",
            "gfx/interface/focusview/titlebar/focus_unavailable_joint_alpha_bg.dds",
        )
        + _render(
            "GFX_focus_can_start_joint_epsilon",
            "gfx/interface/focusview/titlebar/focus_can_start_joint_epsilon_bg.dds",
        )
        + _render(
            "GFX_focus_current_joint_epsilon",
            "gfx/interface/focusview/titlebar/focus_can_start_joint_epsilon_bg.dds",
        )
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
    _write_text(root / "interface" / "nationalfocusview.gfx", gfx.replace("\n", "\r\n"))
    _write_text(
        root / "common" / "national_focus" / "00_titlebar_styles.txt",
        styles.replace("\n", "\r\n"),
    )


def test_gfx_focus_titlebars_generate_incomplete_sets_and_styles(tmp_path, capsys):
    _focus_fixture(tmp_path)
    generator.generate_focus_titlebars(tmp_path)

    gfx = tmp_path / "interface" / "nationalfocusview.gfx"
    styles = tmp_path / "common" / "national_focus" / "00_titlebar_styles.txt"
    output = _read_text(gfx)
    style_output = _read_text(styles)
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

    for path in (gfx, styles):
        raw = path.read_bytes()
        assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")


def test_gfx_generators_report_missing_source_directories(tmp_path, capsys):
    checks = (
        (generator.generate_goals, "Directory does not exist"),
        (generator.generate_event_pictures, "Directory does not exist"),
        (generator.generate_ideas, "Directory does not exist"),
        (generator.generate_party_icons, "Directory does not exist"),
        (generator.generate_intelligence_icons, "Directory does not exist"),
        (generator.generate_decisions, "Directory does not exist"),
        (generator.generate_decisions_desc, "Directory does not exist"),
        (generator.generate_modifier_icons, "Directory does not exist"),
        (generator.generate_scripted_gui, "Directory does not exist"),
        (generator.generate_focus_titlebars, "Titlebar directory not found"),
    )
    for function, message in checks:
        function(tmp_path)
        assert message in capsys.readouterr().out

    titlebar = tmp_path / "gfx" / "interface" / "focusview" / "titlebar"
    titlebar.mkdir(parents=True)
    generator.generate_focus_titlebars(tmp_path)
    assert "Missing file" in capsys.readouterr().out

    (tmp_path / "interface").mkdir(parents=True)
    (tmp_path / "interface" / "nationalfocusview.gfx").write_bytes(b"{}")
    generator.generate_focus_titlebars(tmp_path)
    assert "Missing file" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("selection", "function_name"),
    [
        (str(number), name)
        for number, name in enumerate(
            (
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
            ),
            start=1,
        )
    ],
)
def test_gfx_main_dispatches_each_command(selection, function_name, monkeypatch):
    calls = []
    monkeypatch.setattr(generator, function_name, lambda root: calls.append(root))
    monkeypatch.setattr("builtins.input", lambda _prompt: selection)
    generator.main()
    assert calls == [ROOT]


def test_gfx_main_rejects_invalid_input_before_dispatch(monkeypatch, capsys):
    answers = iter(["", "not numeric", "0", "11", "2"])
    calls = []
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(
        generator, "generate_event_pictures", lambda root: calls.append(root)
    )

    generator.main()

    output = capsys.readouterr().out
    assert "Input cannot be empty" in output
    assert "Invalid input" in output
    assert "Invalid selection" in output
    assert calls == [ROOT]
