"""Tests for the dynamic modifier `enable` stripper.

The gates it removes can never be false. The ones it must not touch go false
while the modifier is still attached, which is the only reason `enable` exists:
`05_internal_factions_modifiers.txt` has no `remove_dynamic_modifier` anywhere,
so its `has_idea` gates are all that neutralise a faction the country lost.
"""

from strip_dynmod_tag_gates import strip_enable_gates


def _strip(text):
    out, removed, trimmed = strip_enable_gates(text.split("\n"))
    return "\n".join(out), removed, trimmed


def test_removes_always_yes():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { always = yes }",
            "",
            "\tpolitical_power_factor = FOO_ppf",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (1, 0)
    assert "enable" not in out
    assert "political_power_factor = FOO_ppf" in out


def test_removes_one_line_tag_gate():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\ticon = GFX_idea_foo",
            "\tenable = { original_tag = FOO }",
            "",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (1, 0)
    assert "enable" not in out
    assert "icon = GFX_idea_foo" in out


def test_removes_multiline_tag_gate():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = {",
            "\t\toriginal_tag = FOO",
            "\t}",
            "",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (1, 0)
    assert "original_tag" not in out


def test_trims_tag_gate_but_keeps_sibling_trigger():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = {",
            "\t\toriginal_tag = FOO",
            "\t\tNOT = {",
            "\t\t\thas_country_flag = collapsed_nation",
            "\t\t}",
            "\t}",
            "",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (0, 1)
    assert "original_tag" not in out
    assert "has_country_flag = collapsed_nation" in out
    assert out.count("{") == out.count("}")


def test_keeps_has_idea_gate():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { has_idea = the_military }",
            "",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (0, 0)
    assert "has_idea = the_military" in out


def test_keeps_country_exists_gate():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { country_exists = ISR }",
            "",
            "\tlocal_building_slots = 2",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (0, 0)
    assert "country_exists = ISR" in out


def test_keeps_tag_inside_or_branch():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = {",
            "\t\tOR = {",
            "\t\t\toriginal_tag = SOV",
            "\t\t\toriginal_tag = TAJ",
            "\t\t}",
            "\t}",
            "",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (0, 0)
    assert "original_tag = SOV" in out
    assert "original_tag = TAJ" in out


def test_ignores_enable_that_is_not_a_direct_child():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tremove_trigger = {",
            "\t\tenable = { always = yes }",
            "\t}",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (0, 0)
    assert "enable = { always = yes }" in out


def test_ignores_commented_template_line():
    text = "\n".join(
        [
            "# FOO_modifier = {",
            "#\t\tenable = { always = yes } #optional",
            "# }",
            "BAR_modifier = {",
            "\tstability_factor = BAR_stab",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    assert (removed, trimmed) == (0, 0)
    assert "#\t\tenable = { always = yes } #optional" in out


def test_is_idempotent():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = {",
            "\t\toriginal_tag = FOO",
            "\t\tNOT = { has_country_flag = collapsed_nation }",
            "\t}",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    once, _, _ = _strip(text)
    twice, removed, trimmed = _strip(once)
    assert (removed, trimmed) == (0, 0)
    assert twice == once
