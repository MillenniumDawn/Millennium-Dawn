"""MIO trait icon assignment: modifier and icon selection, and the CLI."""

import sys

import assign_mio_icons
import pytest
from assign_mio_icons import PRE, choose_icon, inner_block, winning_modifier
from shared.suite import write_text


def test_winning_modifier_uses_absolute_value():
    block = """
    equipment_bonus = {
        soft_attack = -0.4
        hard_attack = 0.6
    }
    production_bonus = {
        production_speed = 0.5
    }
    """

    assert winning_modifier(block) == "hard_attack"


def test_winning_modifier_returns_none_without_supported_modifiers():
    assert winning_modifier("limit_to_equipment_type = tank") is None


def test_inner_block_returns_empty_when_the_brace_never_closes():
    assert inner_block("equipment_bonus = { soft_attack = 0.5", "equipment_bonus") == ""


# The first candidate that exists as a sprite wins.
# case: (family prefix, modifier, sprites defined, icon chosen)
_ICON_CASES = {
    "family alias": ("apc", "armor_value", ["apc_armor", "armor_value"], "apc_armor"),
    "standard suffix": ("smallarms", "soft_attack", ["soft_attack"], "soft_attack"),
    "family prefix": ("smallarms", "max_organisation", ["smallarms"], "smallarms"),
    "nothing matches": ("apc", "armor_value", [], "unique"),
}


@pytest.mark.parametrize(
    ("prefix", "modifier", "sprites", "icon"), _ICON_CASES.values(), ids=_ICON_CASES
)
def test_choose_icon_walks_the_candidate_chain(prefix, modifier, sprites, icon):
    defined = {PRE + sprite for sprite in sprites}

    assert choose_icon(prefix, modifier, defined) == PRE + icon


_TRAIT = (
    "token = TEST_MIO_TEST\n\n"
    "trait = {\n"
    "    token = test_trait\n"
    "    icon = x\n"
    "    limit_to_equipment_type = { infantry_weapons_type }\n"
    "    organization_modifier = { infantry_weapons_type = 1.0 }\n"
    "}\n"
)
_SMALLARMS = PRE + "smallarms"
_DEFAULT_FILE = (
    "common/military_industrial_organization/organizations/MD_HOL_organizations.txt"
)


def _run(monkeypatch, tmp_path, *argv, sprite=_SMALLARMS):
    """Run the CLI on a temp tree: the tools test checkout has no interface/.

    `sprite=None` leaves the sprite file out.
    """
    gfx = tmp_path / "traits.gfx"
    if sprite:
        write_text(gfx, f'\tspriteType = {{ name = "{sprite}" }}\n')
    monkeypatch.setattr(assign_mio_icons, "ROOT", tmp_path)
    monkeypatch.setattr(assign_mio_icons, "GFX", gfx)
    monkeypatch.setattr(sys, "argv", ["assign_mio_icons.py", *argv])
    assign_mio_icons.main()


def _with_icon(icon):
    return _TRAIT.replace("icon = x", f"icon = {icon}")


_NO_TOKEN = _TRAIT.replace("    token = test_trait\n", "")

# case: (file, sprite defined, file after --write, line in the report)
_WRITE_CASES = {
    "family sprite": (
        _TRAIT,
        _SMALLARMS,
        _with_icon(_SMALLARMS),
        "Total placeholders resolved: 1",
    ),
    "no matching sprite": (
        _TRAIT,
        PRE + "unrelated",
        _with_icon(PRE + "unique"),
        "unique fallbacks: 1 -> test_trait",
    ),
    "icon already set": (
        _with_icon("GFX_already_set"),
        _SMALLARMS,
        _with_icon("GFX_already_set"),
        "Total placeholders resolved: 0",
    ),
    "trait without a token": (
        _NO_TOKEN,
        _SMALLARMS,
        _NO_TOKEN.replace("icon = x", f"icon = {_SMALLARMS}"),
        "[smallarms]  ?",
    ),
}


@pytest.mark.parametrize(
    ("text", "sprite", "written", "report"), _WRITE_CASES.values(), ids=_WRITE_CASES
)
def test_write_resolves_each_placeholder_icon(
    tmp_path, monkeypatch, capsys, text, sprite, written, report
):
    # The relative path is resolved against the repository root.
    organization = write_text(tmp_path / "org.txt", text)

    _run(monkeypatch, tmp_path, "org.txt", "--write", sprite=sprite)

    assert organization.read_text() == written
    assert report in capsys.readouterr().out


def test_no_argument_reads_the_default_file_and_writes_nothing(
    tmp_path, monkeypatch, capsys
):
    default = write_text(tmp_path / _DEFAULT_FILE, _TRAIT)

    _run(monkeypatch, tmp_path)

    assert "Total placeholders resolved: 1" in capsys.readouterr().out
    assert default.read_text() == _TRAIT


def _disk_full(*_args):
    raise OSError("disk full")


# case: (sprite file exists, arguments, the replace fails, error message)
_ERROR_CASES = {
    "sprite file missing": (False, ["org.txt"], False, "cannot read sprite file"),
    "input file missing": (True, ["absent.txt"], False, "absent.txt: "),
    "write fails": (True, ["org.txt", "--write"], True, "cannot write"),
}


@pytest.mark.parametrize(
    ("has_sprites", "argv", "replace_fails", "message"),
    _ERROR_CASES.values(),
    ids=_ERROR_CASES,
)
def test_cli_exits_with_the_reason(
    tmp_path, monkeypatch, has_sprites, argv, replace_fails, message
):
    write_text(tmp_path / "org.txt", _TRAIT)
    if replace_fails:
        monkeypatch.setattr(assign_mio_icons.os, "replace", _disk_full)
    sprite = _SMALLARMS if has_sprites else None

    with pytest.raises(SystemExit, match=message):
        _run(monkeypatch, tmp_path, *argv, sprite=sprite)
