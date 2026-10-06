import importlib.util
import json
import re
import sys

import pytest
from shared.suite import write_text as _write


def _module():
    from shared.paths import GENERATORS_DIR

    path = GENERATORS_DIR / "add_international_system.py"
    spec = importlib.util.spec_from_file_location("add_international_system", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VARS = {"space": "var_open_MD_space_gui", "un": "var_open_MD_UN_gui"}


def _repo(tmp_path, keys=("space", "un")):
    """Build a minimal International Systems screen with the given tabs."""
    repo = tmp_path / "repo"
    tabs = ""
    for index, key in enumerate(keys):
        tabs += (
            "\t\t\tbuttonType = {\n"
            f'\t\t\t\tname = "{key}_gui_ledger_button"\n'
            f"\t\t\t\tposition = {{ x = {index * 84} y = 0 }}\n"
            '\t\t\t\tquadTextureSprite ="GFX_missiles_gui_ledger_btn"\n'
            "\t\t\t}\n\n"
            "\t\t\ticonType = {\n"
            f'\t\t\t\tname ="icon_{key}"\n'
            f'\t\t\t\tspriteType = "GFX_ledger_icon_small_{key}"\n'
            f"\t\t\t\tposition = {{ x = {index * 84 + 31} y = 12 }}\n"
            "\t\t\t}\n\n"
        )
    _write(
        repo / "interface/MD_countrymissilesview.gui",
        'guiTypes = {\n\tcontainerWindowType = {\n\t\tname = "MD_countrymissilesview"\n\n'
        '\t\tcontainerWindowType = {\n\t\t\tname = "missiles_gui_ledger_menu"\n\n'
        '\t\t\ticonType = {\n\t\t\t\tname ="trade_divider"\n\t\t\t}\n\n'
        f"{tabs.rstrip()}\n\t\t}}\n\t}}\n}}\n",
    )
    sprites = "".join(
        f'\tspriteType = {{\n\t\tname = "GFX_ledger_icon_small_{key}"\n\t}}\n'
        for key in keys
    )
    _write(
        repo / "interface/MD_countrymissilesview.gfx",
        'spriteTypes = {\n\tspriteType = {\n\t\tname = "GFX_missiles_gui_ledger_btn"\n'
        f"\t}}\n{sprites}}}\n",
    )
    variables = {key: VARS.get(key, f"var_open_MD_{key}_gui") for key in keys}
    handlers = ""
    for key in keys:
        clears = "".join(
            f"\t\t\t\tclear_variable = {var}\n"
            for other, var in variables.items()
            if other != key
        )
        handlers += (
            f"\t\t\t{key}_gui_ledger_button_click = {{\n"
            f"\t\t\t\tset_variable = {{ {variables[key]} = 2 }}\n"
            f"{clears}\t\t\t\tinternational_systems_update = yes\n\t\t\t}}\n"
        )
    frames = "".join(
        f"\t\t\t{key}_gui_ledger_button = {{\n\t\t\t\tframe = {var}\n\t\t\t}}\n"
        for key, var in variables.items()
    )
    _write(
        repo / "common/scripted_guis/00_missiles_scripted_guis.txt",
        "scripted_gui = {\n\tMD_missiles_gui = {\n\t\teffects = {\n"
        f"{handlers}\t\t}}\n\n\t\tproperties = {{\n{frames}\t\t}}\n\t}}\n}}\n",
    )
    _write(
        repo
        / "common/scripted_localisation/01_international_scripted_localisation.txt",
        "defined_text = {\n\tname = name_of_menu\n\ttext = {\n\t\ttrigger = {\n"
        "\t\t\tcheck_variable = { var_open_MD_UN_gui = 2 }\n\t\t}\n"
        "\t\tlocalization_key = IS_title_un\n\t}\n"
        "\ttext = {\n\t\tlocalization_key = IS_title_int_sys\n\t}\n}\n",
    )
    _write(
        repo / "common/scripted_effects/opener.txt",
        "open_un = {\n\tset_variable = { var_open_MD_UN_gui = 2 }\n}\n",
    )
    icon = repo / "gfx/interface/scripted_gui/missiles/ledger_icon_small_forums.dds"
    icon.parent.mkdir(parents=True)
    icon.write_bytes(b"dds")
    return repo


def _full_strip(tmp_path):
    """A six-tab strip with the wide tab sprite on disk, so a seventh tab goes narrow."""
    image = pytest.importorskip("PIL.Image")
    repo = _repo(tmp_path, ("a", "b", "c", "d", "e", "f"))
    art = repo / "gfx/interface/scripted_gui/missiles"
    image.new("RGBA", (180, 53), (1, 2, 3, 255)).save(
        art / "missiles_gui_ledger_btn.dds"
    )
    return image, _module(), repo, art


def _read(repo, path):
    with open(repo / path, encoding="utf-8", newline="") as handle:
        return handle.read()


def test_adds_a_wired_tab_after_the_anchor(tmp_path):
    module = _module()
    repo = _repo(tmp_path)

    written, order, openers = module.add_system(
        str(repo), "forums", "Economic Forums", "Track the forums.", after="space"
    )

    assert order == ["space", "forums", "un"]
    gui = _read(repo, "interface/MD_countrymissilesview.gui")
    assert re.findall(r'name = "(\w+)_gui_ledger_button"', gui) == order
    assert re.findall(r"position = \{ x = (\d+) y = 0 \}", gui) == ["0", "84", "168"]
    assert re.findall(r"position = \{ x = (\d+) y = 12 \}", gui) == ["31", "115", "199"]
    assert "btn_narrow" not in gui
    assert 'spriteType = "GFX_ledger_icon_small_forums"' in gui

    script = _read(repo, "common/scripted_guis/00_missiles_scripted_guis.txt")
    for key in ("space", "un"):
        handler = re.search(
            rf"{key}_gui_ledger_button_click = \{{.*?\n\t\t\t\}}", script, re.S
        )
        assert "clear_variable = var_open_MD_forums_gui" in handler.group(0)
    new_handler = re.search(
        r"forums_gui_ledger_button_click = \{.*?\n\t\t\t\}", script, re.S
    )
    assert "set_variable = { var_open_MD_forums_gui = 2 }" in new_handler.group(0)
    assert "clear_variable = var_open_MD_space_gui" in new_handler.group(0)
    assert "clear_variable = var_open_MD_UN_gui" in new_handler.group(0)
    assert (
        script.index("space_gui_ledger_button_click")
        < script.index("forums_gui_ledger_button_click")
        < script.index("un_gui_ledger_button_click")
    )
    assert (
        "forums_gui_ledger_button = {\n\t\t\t\tframe = var_open_MD_forums_gui" in script
    )

    titles = _read(
        repo, "common/scripted_localisation/01_international_scripted_localisation.txt"
    )
    assert titles.index("IS_title_forums") < titles.index("IS_title_int_sys")
    gfx = _read(repo, "interface/MD_countrymissilesview.gfx")
    assert 'name = "GFX_ledger_icon_small_forums"' in gfx
    assert "btn_narrow" not in gfx

    loc = (
        repo / "localisation/english/MD_international_forums_l_english.yml"
    ).read_bytes()
    assert loc.startswith(b"\xef\xbb\xbfl_english:\n")
    assert b'IS_title_forums: "ECONOMIC FORUMS"' in loc
    assert "interface/MD_international_forums.gui" in written
    assert "check_variable = { var_open_MD_forums_gui = 2 }" in _read(
        repo, "common/scripted_guis/01_international_forums_gui.txt"
    )
    assert openers == [("common/scripted_effects/opener.txt", 2)]


def test_switches_to_the_narrow_sprite_when_the_strip_overflows(tmp_path):
    image, module, repo, art = _full_strip(tmp_path)

    written, order, _ = module.add_system(str(repo), "forums", "Forums", "Forums.")

    assert order[-1] == "forums"
    assert (
        "gfx/interface/scripted_gui/missiles/missiles_gui_ledger_btn_narrow.dds"
        in written
    )
    gui = _read(repo, "interface/MD_countrymissilesview.gui")
    assert gui.count('quadTextureSprite ="GFX_missiles_gui_ledger_btn_narrow"') == 7
    assert re.findall(r"position = \{ x = (\d+) y = 0 \}", gui)[-1] == "372"
    assert '"GFX_missiles_gui_ledger_btn_narrow"' in _read(
        repo, "interface/MD_countrymissilesview.gfx"
    )
    with image.open(art / "missiles_gui_ledger_btn_narrow.dds") as narrow:
        assert narrow.size == (136, 53)


@pytest.mark.parametrize(
    ("key", "after", "keys", "message"),
    [
        ("forums", None, ("space", "forums"), "already exists"),
        ("forums", "moon", ("space", "un"), "is not a tab"),
        ("Forums", None, ("space", "un"), "lower_snake_case"),
        ("forums", None, tuple("abcdefgh"), "do not fit"),
    ],
)
def test_rejects_bad_requests_without_writing(tmp_path, key, after, keys, message):
    module = _module()
    repo = _repo(tmp_path, keys)
    before = _read(repo, "interface/MD_countrymissilesview.gui")

    with pytest.raises(module.ToolError, match=message):
        module.add_system(str(repo), key, "Forums", "Forums.", after=after)

    assert _read(repo, "interface/MD_countrymissilesview.gui") == before
    assert not (repo / "localisation").exists()


def test_escapes_quotes_in_localisation(tmp_path):
    module = _module()
    repo = _repo(tmp_path)

    module.add_system(str(repo), "forums", 'The "G7" Forum', 'Track the "G7" forum.')

    loc = _read(repo, "localisation/english/MD_international_forums_l_english.yml")
    assert 'FORUMS_GUI_LEDGER_TT_DELAYED: "Track the \\"G7\\" forum."' in loc
    assert 'IS_title_forums: "THE \\"G7\\" FORUM"' in loc


def test_rejects_multiline_text_without_writing(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    before = _read(repo, "interface/MD_countrymissilesview.gui")

    with pytest.raises(module.ToolError, match="single line"):
        module.add_system(str(repo), "forums", "Forums", "Two\nlines.")

    assert _read(repo, "interface/MD_countrymissilesview.gui") == before


def test_unreadable_script_stops_before_writing(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    (repo / "common/scripted_effects/broken.txt").write_bytes(b"\xff\xfe bad")
    before = _read(repo, "interface/MD_countrymissilesview.gui")

    with pytest.raises(UnicodeDecodeError):
        module.add_system(str(repo), "forums", "Forums", "Forums.")

    assert _read(repo, "interface/MD_countrymissilesview.gui") == before
    assert not (repo / "localisation").exists()


def test_requires_the_icon_first(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    (repo / "gfx/interface/scripted_gui/missiles/ledger_icon_small_forums.dds").unlink()

    with pytest.raises(module.ToolError, match="add the tab icon first"):
        module.add_system(str(repo), "forums", "Forums", "Forums.")


def test_rejects_keys_whose_loc_ids_already_exist(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    _write(
        repo / "localisation/english/MD_international_l_english.yml",
        '\ufeffl_english:\n IS_title_forums: "FORUMS"\n',
    )
    before = _read(repo, "interface/MD_countrymissilesview.gui")

    with pytest.raises(module.ToolError, match="IS_title_forums"):
        module.add_system(str(repo), "forums", "Forums", "Forums.")

    assert _read(repo, "interface/MD_countrymissilesview.gui") == before


def test_default_title_keeps_loc_tokens_as_written(tmp_path):
    module = _module()
    repo = _repo(tmp_path)

    module.add_system(str(repo), "forums", "[ROOT.GetAdjective] Forum", "Forums.")

    loc = _read(repo, "localisation/english/MD_international_forums_l_english.yml")
    assert 'IS_title_forums: "[ROOT.GetAdjective] FORUM"' in loc
    assert (
        module.default_title("$Some_Key$ £my_icon §Yhot§!")
        == "$Some_Key$ £my_icon §YHOT§!"
    )
    assert module.default_title("Economic\\nForums") == "ECONOMIC\\nFORUMS"


def test_rejects_keys_whose_sprite_already_exists(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    gfx = _read(repo, "interface/MD_countrymissilesview.gfx")
    sprite = '\tspriteType = {\n\t\tname = "GFX_ledger_icon_small_forums"\n\t}\n'
    _write(
        repo / "interface/MD_countrymissilesview.gfx",
        gfx[: gfx.rindex("}")] + sprite + "}\n",
    )
    before = _read(repo, "interface/MD_countrymissilesview.gui")

    with pytest.raises(module.ToolError, match="GFX_ledger_icon_small_forums"):
        module.add_system(str(repo), "forums", "Forums", "Forums.")

    assert _read(repo, "interface/MD_countrymissilesview.gui") == before


def test_tab_name_uses_the_key_term_colour(tmp_path):
    module = _module()
    repo = _repo(tmp_path)

    module.add_system(str(repo), "forums", "Economic Forums", "Forums.")

    loc = _read(repo, "localisation/english/MD_international_forums_l_english.yml")
    assert 'FORUMS_GUI_LEDGER_TT: "§YEconomic Forums§!"' in loc


def test_rejects_keys_that_alias_existing_tab_state(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    script = repo / "common/scripted_guis/00_missiles_scripted_guis.txt"
    _write(
        script,
        _read(repo, "common/scripted_guis/00_missiles_scripted_guis.txt").replace(
            "set_variable = { var_open_MD_space_gui = 2 }",
            "set_variable = { var_open_MD_space_gui = 2 }\n"
            "\t\t\t\tset_variable = { var_open_MD_orbit_gui = 2 }",
        ),
    )
    icon = repo / "gfx/interface/scripted_gui/missiles/ledger_icon_small_orbit.dds"
    icon.write_bytes(b"dds")
    before = _read(repo, "common/scripted_guis/00_missiles_scripted_guis.txt")

    with pytest.raises(module.ToolError, match="already used"):
        module.add_system(str(repo), "orbit", "Forums", "Forums.")

    assert _read(repo, "common/scripted_guis/00_missiles_scripted_guis.txt") == before


@pytest.mark.parametrize("description", ["Use C:\\Temp.", "Tab\\tstop."])
def test_rejects_unsupported_backslash_escapes(tmp_path, description):
    module = _module()
    repo = _repo(tmp_path)

    with pytest.raises(module.ToolError, match="backslash"):
        module.add_system(str(repo), "forums", "Forums", description)

    assert not (repo / "localisation").exists()


def test_keeps_the_newline_escape(tmp_path):
    module = _module()
    repo = _repo(tmp_path)

    module.add_system(str(repo), "forums", "Forums", "One.\\nTwo.")

    loc = _read(repo, "localisation/english/MD_international_forums_l_english.yml")
    assert 'FORUMS_GUI_LEDGER_TT_DELAYED: "One.\\nTwo."' in loc


def test_rejects_keys_whose_window_already_exists(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    _write(
        repo / "interface/other.gui",
        'guiTypes = {\n\tcontainerWindowType = {\n\t\tname = "MD_forums_system_window"\n\t}\n}\n',
    )
    before = _read(repo, "interface/MD_countrymissilesview.gui")

    with pytest.raises(module.ToolError, match="MD_forums_system_window"):
        module.add_system(str(repo), "forums", "Forums", "Forums.")

    assert _read(repo, "interface/MD_countrymissilesview.gui") == before


def test_adding_an_eighth_tab_reuses_the_narrow_sprite(tmp_path):
    image, module, repo, art = _full_strip(tmp_path)
    (art / "ledger_icon_small_race.dds").write_bytes(b"dds")
    module.add_system(str(repo), "forums", "Forums", "Forums.")

    written, order, _ = module.add_system(str(repo), "race", "Race", "Race.")

    assert order[-2:] == ["forums", "race"]
    assert not any(path.endswith("btn_narrow.dds") for path in written)
    gfx = _read(repo, "interface/MD_countrymissilesview.gfx")
    assert gfx.count('"GFX_missiles_gui_ledger_btn_narrow"') == 1


def test_wires_a_handler_that_clears_nothing_yet(tmp_path):
    module = _module()
    repo = _repo(tmp_path, ("space",))

    module.add_system(str(repo), "forums", "Forums", "Forums.")

    script = _read(repo, "common/scripted_guis/00_missiles_scripted_guis.txt")
    handler = re.search(
        r"space_gui_ledger_button_click = \{.*?\n\t\t\t\}", script, re.S
    )
    assert "clear_variable = var_open_MD_forums_gui" in handler.group(0)


def _break(path, old, new=""):
    def mutate(repo):
        text = _read(repo, path)
        assert old in text
        _write(repo / path, text.replace(old, new, 1))

    return mutate


GUI = "interface/MD_countrymissilesview.gui"
SCRIPT = "common/scripted_guis/00_missiles_scripted_guis.txt"
TITLES = "common/scripted_localisation/01_international_scripted_localisation.txt"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (_break(GUI, '"missiles_gui_ledger_menu"', '"other_menu"'), "could not find"),
        (
            _break(GUI, 'name = "un_gui_ledger_button"', 'label = "un"'),
            "unnamed tab button",
        ),
        (
            _break(
                SCRIPT,
                "un_gui_ledger_button = {\n\t\t\t\tframe = var_open_MD_UN_gui\n\t\t\t}\n",
            ),
            "no frame",
        ),
        (_break(TITLES, "name = name_of_menu", "name = other_menu"), "name_of_menu"),
        (_break(SCRIPT, "\t}\n}\n"), "unbalanced"),
    ],
)
def test_malformed_screen_files_stop_without_writing(tmp_path, mutate, message):
    module = _module()
    repo = _repo(tmp_path)
    mutate(repo)
    before = {path: _read(repo, path) for path in (GUI, SCRIPT, TITLES)}

    with pytest.raises(module.ToolError, match=message):
        module.add_system(str(repo), "forums", "Forums", "Forums.")

    assert {path: _read(repo, path) for path in before} == before
    assert not (repo / "localisation").exists()


def test_strip_with_a_missing_icon_stops(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    gui = _read(repo, GUI)
    start = gui.index('\t\t\ticonType = {\n\t\t\t\tname ="icon_un"')
    end = gui.index("}", start) + 1
    _write(repo / GUI, gui[:start] + gui[end:])

    with pytest.raises(module.ToolError, match="without an icon"):
        module.add_system(str(repo), "forums", "Forums", "Forums.")


def test_refuses_an_existing_stub_file(tmp_path):
    module = _module()
    repo = _repo(tmp_path)
    _write(repo / "interface/MD_international_forums.gui", "guiTypes = {\n}\n")

    with pytest.raises(
        module.ToolError, match="MD_international_forums.gui already exists"
    ):
        module.add_system(str(repo), "forums", "Forums", "Forums.")


def test_main_reports_the_result(tmp_path, monkeypatch, capsys):
    module = _module()
    repo = _repo(tmp_path)
    monkeypatch.setattr(module, "REPO_ROOT", repo)

    assert (
        module.main(
            [
                "forums",
                "Economic Forums",
                "--description",
                "Forums.",
                "--after",
                "space",
            ]
        )
        == 0
    )

    out = capsys.readouterr().out
    assert "Tabs: space, forums, un" in out
    assert "  wrote interface/MD_international_forums.gui" in out
    assert "  common/scripted_effects/opener.txt:2" in out


def test_main_exits_with_the_error(tmp_path, monkeypatch):
    module = _module()
    repo = _repo(tmp_path)
    monkeypatch.setattr(module, "REPO_ROOT", repo)

    with pytest.raises(SystemExit, match="ERROR: key 'Bad' must be lower_snake_case"):
        module.main(["Bad", "Forums", "--description", "Forums."])


def _art(tmp_path, keys=("space", "un")):
    """A strip with real images: the wide sprite, one styled premade and one category icon."""
    image = pytest.importorskip("PIL.Image")
    module = _module()
    repo = _repo(tmp_path, keys)
    art = repo / "gfx/interface/scripted_gui/missiles"
    (art / "ledger_icon_small_forums.dds").unlink()
    image.new("RGBA", (180, 53), (40, 40, 40, 255)).save(
        art / "missiles_gui_ledger_btn.dds"
    )
    image.new("RGBA", (28, 27), (200, 150, 90, 255)).save(
        art / "ledger_icon_small_missile.dds"
    )
    category = repo / "gfx/interface/decisions/decision_categories"
    category.mkdir(parents=True)
    emblem = image.new("RGBA", (64, 64))
    emblem.paste((250, 250, 250, 255), (16, 16, 48, 48))
    emblem.save(category / "decision_category_generic_industry.dds")
    return image, module, repo, art


def test_a_premade_icon_is_written_as_the_tab_icon(tmp_path):
    image, module, repo, art = _art(tmp_path)

    written, _, _ = module.add_system(
        str(repo), "forums", "Forums", "Forums.", icon="missile"
    )

    assert "gfx/interface/scripted_gui/missiles/ledger_icon_small_forums.dds" in written
    with image.open(art / "ledger_icon_small_forums.dds") as icon:
        assert icon.size == (28, 27)
        assert icon.convert("RGBA").getpixel((5, 5)) == (200, 150, 90, 255)


def test_other_images_are_fitted_and_recoloured(tmp_path):
    image, module, repo, art = _art(tmp_path)
    logo = tmp_path / "logo.png"
    emblem = image.new("RGBA", (120, 70))
    emblem.paste((255, 255, 255, 255), (10, 10, 110, 60))
    emblem.save(logo)

    module.add_system(str(repo), "forums", "Forums", "Forums.", icon=str(logo))

    with image.open(art / "ledger_icon_small_forums.dds") as icon:
        icon = icon.convert("RGBA")
        assert icon.size == (28, 27)
        red, green, blue, alpha = icon.getpixel((14, 13))
        assert alpha == 255 and red > green > blue
        assert icon.getpixel((14, 1))[3] == 0


@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize(
    ("filename", "mode", "message"),
    [
        ("logo.jpg", "RGB", "no transparency"),
        ("logo.png", "RGB", "no transparency"),
        ("opaque.png", "RGBA", "no transparency"),
        ("README.md", None, "cannot identify image"),
        ("broken.png", None, "cannot identify image"),
    ],
)
def test_invalid_custom_icons_report_cli_errors_without_writing(
    tmp_path, monkeypatch, filename, mode, message, preview
):
    image, module, repo, _ = _art(tmp_path)
    logo = repo / filename
    if mode:
        image.new(mode, (200, 100), "white").save(logo)
    else:
        _write(logo, "This is not an image.\n")
    before = {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    args = ["forums", "Forums", "--description", "Forums.", "--icon", filename]
    output = tmp_path / "strip.png"
    if preview:
        args.extend(["--preview", str(output)])

    with pytest.raises(SystemExit, match=f"ERROR: .*{message}"):
        module.main(args)

    assert {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()} == before
    assert not output.exists()


def test_the_catalog_lists_only_premade_icons_this_repo_has(tmp_path):
    _, module, repo, _ = _art(tmp_path)
    art_module = sys.modules["international_system_art"]

    catalog = art_module.icon_catalog(str(repo))

    assert [entry["name"] for entry in catalog] == ["missile", "industry"]
    assert all(entry["png"] for entry in catalog)


@pytest.mark.parametrize(
    ("setup", "icon", "message"),
    [
        (lambda art: None, "no_such_icon", "unknown icon"),
        (
            lambda art: (art / "ledger_icon_small_forums.dds").write_bytes(b"x"),
            "missile",
            "drop --icon",
        ),
    ],
)
def test_bad_icon_requests_stop_without_writing(tmp_path, setup, icon, message):
    _, module, repo, art = _art(tmp_path)
    setup(art)

    with pytest.raises(module.ToolError, match=message):
        module.add_system(str(repo), "forums", "Forums", "Forums.", icon=icon)

    assert not (repo / "localisation").exists()


@pytest.mark.parametrize(
    ("keys", "icon_x"), [(("space", "un"), 31), (tuple("abcdef"), 20)]
)
def test_preview_draws_the_strip_and_writes_nothing_else(tmp_path, keys, icon_x):
    image, module, repo, art = _art(tmp_path, keys)
    gfx = _read(repo, "interface/MD_countrymissilesview.gfx")
    _write(
        repo / "interface/MD_countrymissilesview.gfx",
        gfx.replace(
            f'name = "GFX_ledger_icon_small_{keys[0]}"',
            f'name = "GFX_ledger_icon_small_{keys[0]}"\n\t\ttexturefile = '
            '"gfx/interface/scripted_gui/missiles/ledger_icon_small_missile.dds"',
        ),
    )
    before = {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    preview = tmp_path / "strip.png"

    written, order, _ = module.add_system(
        str(repo), "forums", "Forums", "Forums.", icon="missile", preview=str(preview)
    )

    assert written == [str(preview)] and order[-1] == "forums"
    assert {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()} == before
    with image.open(preview) as strip:
        assert strip.size[0] == 550
        assert strip.convert("RGBA").getpixel((10 + icon_x + 5, 4 + 12 + 5)) == (
            200,
            150,
            90,
            255,
        )


def test_preview_reuses_an_existing_narrow_sprite_and_the_icon_on_disk(tmp_path):
    image, module, repo, art = _full_strip(tmp_path)
    image.new("RGBA", (136, 53), (9, 9, 9, 255)).save(
        art / "missiles_gui_ledger_btn_narrow.dds"
    )
    image.new("RGBA", (28, 27), (1, 200, 1, 255)).save(
        art / "ledger_icon_small_forums.dds"
    )
    preview = tmp_path / "strip.png"

    module.add_system(str(repo), "forums", "Forums", "Forums.", preview=str(preview))

    with image.open(preview) as strip:
        strip = strip.convert("RGBA")
        assert strip.getpixel((10 + 6 * 62 + 20 + 5, 4 + 12 + 5)) == (1, 200, 1, 255)


def test_main_lists_the_premade_icons_as_json(tmp_path, monkeypatch, capsys):
    _, module, repo, _ = _art(tmp_path)
    monkeypatch.setattr(module, "REPO_ROOT", repo)

    assert module.main(["--list-icons"]) == 0

    names = [entry["name"] for entry in json.loads(capsys.readouterr().out)]
    assert names == ["missile", "industry"]


def test_main_requires_the_tab_details(tmp_path, monkeypatch):
    module = _module()
    monkeypatch.setattr(module, "REPO_ROOT", _repo(tmp_path))

    with pytest.raises(SystemExit):
        module.main(["forums"])


def test_styled_premades_keep_their_art_at_other_sizes(tmp_path):
    image, module, repo, art = _art(tmp_path)
    image.new("RGBA", (26, 27), (200, 150, 90, 255)).save(
        art / "ledger_icon_small_missile.dds"
    )

    module.add_system(str(repo), "forums", "Forums", "Forums.", icon="missile")

    with image.open(art / "ledger_icon_small_forums.dds") as icon:
        icon = icon.convert("RGBA")
        assert icon.size == (28, 27)
        assert icon.getpixel((14, 13)) == (200, 150, 90, 255)
        assert icon.getpixel((0, 13))[3] == 0


def test_a_fully_transparent_icon_is_refused_before_writing(tmp_path):
    image, module, repo, _ = _art(tmp_path)
    blank = tmp_path / "blank.png"
    image.new("RGBA", (40, 40), (0, 0, 0, 0)).save(blank)

    with pytest.raises(module.ToolError, match="no visible pixels"):
        module.add_system(str(repo), "forums", "Forums", "Forums.", icon=str(blank))

    assert not (repo / "localisation").exists()


def test_the_art_helper_is_hidden_from_the_tool_launcher():
    from shared.paths import TOOLS_DIR

    spec = importlib.util.spec_from_file_location("run_launcher", TOOLS_DIR / "run.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)

    assert "international_system_art" not in launcher.find_all_tools()
