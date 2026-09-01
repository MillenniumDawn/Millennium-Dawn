"""Behavior tests for the scientist trait medal-sprite check."""

import pytest
from validate_gfx_references import _load_vanilla_sprite_manifest
from validate_scientist_traits import Validator, parse_trait_icons
from validator_common import Severity

# `scientist_trait_fast_learner` is the shadowed case: vanilla declares its
# sprite only in interface/unitleaderwindow.gfx, the file MD replaces.
SHADOWED_TOKEN = "scientist_trait_fast_learner"

TRAITS = (
    "scientist_trait_ok = {\n"  # 1: implicit GFX_<token>, defined
    "\tmodifier = {\n"
    "\t\tscientist_xp_gain_factor = 0.1\n"
    "\t}\n"
    "}\n"
    "\n"
    "scientist_trait_custom = {\n"  # 7: explicit icon, defined
    "\ticon = GFX_custom_medal\n"
    "}\n"
    "\n"
    "scientist_trait_custom_broken = {\n"  # 11: explicit icon, undefined
    "\ticon = GFX_no_such_medal\n"
    "}\n"
    "\n"
    "scientist_trait_nothing = {\n"  # 15: implicit, undefined
    "}\n"
    "\n"
    f"{SHADOWED_TOKEN} = {{\n"  # 18: implicit, vanilla-only
    "}\n"
    "\n"
    "scientist_trait_stale = {\t#TODO: ICON\n"  # 21: marker, but defined
    "}\n"
    "\n"
    "scientist_trait_marked_missing = { #TODO: ICON\n"  # 24: marker, undefined
    "}\n"
)

GFX = (
    "spriteTypes = {\n"
    '\tspriteType = { name = "GFX_scientist_trait_ok" texturefile = "a.dds" }\n'
    '\tspriteType = { name = "GFX_custom_medal" texturefile = "b.dds" }\n'
    '\tspriteType = { name = "GFX_scientist_trait_stale" texturefile = "c.dds" }\n'
    "}\n"
)


def _write_fixture(tmp_path, traits: str = TRAITS, gfx: str = GFX):
    trait_dir = tmp_path / "common" / "scientist_traits"
    gfx_dir = tmp_path / "interface"
    trait_dir.mkdir(parents=True)
    gfx_dir.mkdir(parents=True)
    (trait_dir / "00_traits.txt").write_text(traits, encoding="utf-8")
    (gfx_dir / "test.gfx").write_text(gfx, encoding="utf-8")


@pytest.fixture(autouse=True)
def _no_index_floor(monkeypatch):
    # The real floor guards against an empty sprite index; a fixture .gfx holds a
    # handful of sprites, so every behavior test below would skip without this.
    monkeypatch.setattr("validate_scientist_traits._MIN_SPRITE_INDEX", 0)


def _issues(tmp_path):
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return {
        (issue.category, issue.line): issue for issue in validator._issues
    }, validator


def test_parse_trait_icons_resolves_explicit_and_implicit_names():
    content = (
        "scientist_trait_a = {\n"
        "\ticon = GFX_elsewhere\n"
        "}\n"
        "scientist_trait_b = {\n"
        '\ticon = "GFX_quoted"\n'
        "}\n"
        "scientist_trait_c = {\n"
        "}\n"
    )

    assert parse_trait_icons(content, content) == [
        ("scientist_trait_a", "GFX_elsewhere", 1, False),
        ("scientist_trait_b", "GFX_quoted", 4, False),
        ("scientist_trait_c", "GFX_scientist_trait_c", 7, False),
    ]


def test_parse_trait_icons_reads_the_todo_marker_from_the_raw_text():
    raw = "scientist_trait_a = {\t#TODO: ICON\n}\nscientist_trait_b = {\n}\n"
    stripped = "scientist_trait_a = {\t\n}\nscientist_trait_b = {\n}\n"

    assert [
        (token, marked) for token, _, _, marked in parse_trait_icons(stripped, raw)
    ] == [
        ("scientist_trait_a", True),
        ("scientist_trait_b", False),
    ]


def test_shadowed_token_is_still_in_the_vanilla_manifest():
    # Guards the fixture: if a HOI4 update drops this name from
    # vanilla_sprites.txt, the shadowed-case test below turns into a
    # missing-case test and the failure would be cryptic.
    assert f"GFX_{SHADOWED_TOKEN}" in _load_vanilla_sprite_manifest()


def test_defined_icons_produce_no_issue(tmp_path):
    _write_fixture(
        tmp_path,
        traits="scientist_trait_ok = {\n}\nscientist_trait_custom = {\n\ticon = GFX_custom_medal\n}\n",
    )

    _, validator = _issues(tmp_path)

    assert validator._issues == []


def test_undefined_icons_are_reported_with_their_line(tmp_path):
    _write_fixture(tmp_path)

    found, _ = _issues(tmp_path)

    missing = {
        line: issue.message
        for (category, line), issue in found.items()
        if category == "missing-scientist-trait-icon"
    }
    assert set(missing) == {11, 15, 24}
    assert "GFX_no_such_medal" in missing[11]
    assert "GFX_scientist_trait_nothing" in missing[15]


def test_vanilla_only_sprite_is_reported_as_shadowed_not_missing(tmp_path):
    _write_fixture(tmp_path)

    found, _ = _issues(tmp_path)

    assert ("shadowed-scientist-trait-icon", 18) in found
    assert ("missing-scientist-trait-icon", 18) not in found
    assert (
        "unitleaderwindow.gfx" in found[("shadowed-scientist-trait-icon", 18)].message
    )


def test_stale_todo_marker_is_reported_when_the_sprite_exists(tmp_path):
    _write_fixture(tmp_path)

    found, _ = _issues(tmp_path)

    assert ("stale-scientist-trait-icon-todo", 21) in found
    # A marker on a trait that really has no sprite is the backlog, not a stale
    # marker: it must be reported once, as missing.
    assert ("stale-scientist-trait-icon-todo", 24) not in found


def test_every_finding_is_warning_severity(tmp_path):
    _write_fixture(tmp_path)

    _, validator = _issues(tmp_path)

    assert validator._issues
    assert {issue.severity for issue in validator._issues} == {Severity.WARNING}


def test_check_is_skipped_when_the_sprite_index_is_suspiciously_small(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("validate_scientist_traits._MIN_SPRITE_INDEX", 1000)
    _write_fixture(tmp_path)

    _, validator = _issues(tmp_path)

    assert validator._issues == []
