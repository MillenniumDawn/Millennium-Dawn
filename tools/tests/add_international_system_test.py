import importlib.util
import re

import pytest


def _module():
    from shared.paths import GENERATORS_DIR

    path = GENERATORS_DIR / "add_international_system.py"
    spec = importlib.util.spec_from_file_location("add_international_system", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VARS = {"space": "var_open_MD_space_gui", "un": "var_open_MD_UN_gui"}


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


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
