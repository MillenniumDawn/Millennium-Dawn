"""State selection image tool: province recoloring and the interactive run."""

import importlib

import pytest
import state_gfx
from shared.suite import write_text

Image = importlib.import_module("PIL.Image")


def _bitmap(path, size, pixels):
    image = Image.new("RGB", size)
    for position, color in pixels.items():
        image.putpixel(position, color)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _mod(root, monkeypatch, state_file="12-State.txt", answers=("12", "1")):
    """A one-province mod tree with the module pointed at it and the prompts
    answered. Returns the definition file and the output folder."""
    states = root / "history" / "states"
    definition = write_text(root / "map" / "definition.csv", "id;r;g;b\n1;1;2;3\n")
    bitmap = root / "map" / "provinces.bmp"
    _bitmap(bitmap, (1, 1), {(0, 0): (99, 99, 99)})
    write_text(states / state_file, "provinces = { 1 }\n")
    desktop = root / "Desktop"
    for name, value in {
        "REPO_ROOT": root,
        "states_dir": states,
        "definition_file": definition,
        "provinces_bmp": bitmap,
        "desktop_path": desktop,
    }.items():
        monkeypatch.setattr(state_gfx, name, str(value))
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(replies))
    return definition, desktop


def test_merge_provinces_recolors_only_the_target_colors(tmp_path):
    source = tmp_path / "provinces.bmp"
    _bitmap(source, (3, 2), {(0, 0): (10, 20, 30), (2, 1): (40, 50, 60)})

    merged = state_gfx.merge_provinces(source, {"#0a141e", "#28323c"}, "#ffffff")

    assert merged.mode == "RGB"
    assert merged.getpixel((0, 0)) == (255, 255, 255)
    assert merged.getpixel((2, 1)) == (255, 255, 255)
    assert merged.getpixel((1, 0)) == (0, 0, 0)
    assert state_gfx.rgb_to_hex((1, 2, 255)) == "#0102ff"


def test_main_writes_the_scaled_selection(tmp_path, monkeypatch):
    definition, desktop = _mod(
        tmp_path, monkeypatch, "12-Test State.txt", answers=("12", "2")
    )
    write_text(
        tmp_path / "history/states/12-Test State.txt",
        "state = {\n\tprovinces = { 1 2 }\n}\n",
    )
    # A short row and a row with no numeric id are skipped.
    write_text(
        definition,
        "id;r;g;b;name\n1;10;20;30;One\n2;40;50;60;Two\nbad\n"
        "not-an-id;1;2;3;Bad\n3;70;80;90;Other\n",
    )
    _bitmap(
        tmp_path / "map/provinces.bmp",
        (4, 4),
        {(1, 1): (10, 20, 30), (2, 2): (40, 50, 60)},
    )
    desktop.mkdir()

    state_gfx.main()

    # The two provinces span 2x2 pixels, doubled by the scale.
    with Image.open(desktop / "test_state.png") as image:
        assert image.size == (4, 4)
        assert image.mode == "RGBA"
        assert image.getpixel((0, 0))[3] == 255
        assert image.getpixel((3, 3))[3] == 255


# case: (state file name, message printed)
_NO_OUTPUT_CASES = {
    "file name without a state name": ("12.txt", "Could not extract state name"),
    "no pixel has the province color": ("12-State.txt", "HEX Codes: ['#010203']"),
}


@pytest.mark.parametrize(
    ("state_file", "message"), _NO_OUTPUT_CASES.values(), ids=_NO_OUTPUT_CASES
)
def test_main_writes_nothing_without_a_selection(
    tmp_path, monkeypatch, capsys, state_file, message
):
    _definition, desktop = _mod(tmp_path, monkeypatch, state_file)

    state_gfx.main()

    assert message in capsys.readouterr().out
    assert not desktop.exists()


def test_main_exits_when_run_outside_the_repository(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    for name in ("states_dir", "definition_file", "provinces_bmp"):
        monkeypatch.setattr(state_gfx, name, str(missing / name))

    with pytest.raises(SystemExit, match="required path not found"):
        state_gfx.main()


# case: (state id typed, scale typed, read that fails, error)
_EXIT_CASES = {
    "scale is not a number": ("12", "bad", None, "Scale must be an integer"),
    "states cannot be listed": ("12", "1", "listdir", "cannot list states"),
    "state file cannot be read": ("12", "1", "state", "cannot read state file"),
    "definition cannot be read": (
        "12",
        "1",
        "definition",
        "cannot read definition file",
    ),
    "no file for the state": ("999", "1", None, "state file for state ID 999"),
}


@pytest.mark.parametrize(
    ("state_id", "scale", "broken", "error"), _EXIT_CASES.values(), ids=_EXIT_CASES
)
def test_main_exits_before_it_touches_the_bitmap(
    tmp_path, monkeypatch, state_id, scale, broken, error
):
    definition, _desktop = _mod(tmp_path, monkeypatch, answers=(state_id, scale))
    real_read = state_gfx.read_text_under

    def unreadable(*_args, **_kwargs):
        raise OSError("no access")

    def read(path, *args, **kwargs):
        if broken == "state" or (broken == "definition" and path == str(definition)):
            unreadable()
        return real_read(path, *args, **kwargs)

    if broken == "listdir":
        monkeypatch.setattr(state_gfx.os, "listdir", unreadable)
    monkeypatch.setattr(state_gfx, "read_text_under", read)
    monkeypatch.setattr(
        state_gfx, "merge_provinces", lambda *_: pytest.fail("bitmap processed")
    )

    with pytest.raises(SystemExit, match=error):
        state_gfx.main()
