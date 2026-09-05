"""Tests for the dynamic modifier `enable` stripper.

The gates it removes can never be false. The ones it must not touch go false
while the modifier is still attached, which is the only reason `enable` exists:
`05_internal_factions_modifiers.txt` has no `remove_dynamic_modifier` anywhere,
so its `has_idea` gates are all that neutralise a faction the country lost.
"""

import sys

from strip_dynmod_tag_gates import main, process_file, strip_enable_gates


def _strip(text):
    out, removed, trimmed, _skipped = strip_enable_gates(text.split("\n"))
    return "\n".join(out), removed, trimmed


def _strip_full(text):
    out, removed, trimmed, skipped = strip_enable_gates(text.split("\n"))
    return "\n".join(out), removed, trimmed, skipped


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


def test_packed_body_keeps_a_nested_trigger_intact():
    # Splitting this on statements drops the nested block's braces; splicing
    # the gate out of the raw text copies them through.
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { original_tag = FOO OR = { has_idea = a has_idea = b } }",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed, skipped = _strip_full(text)
    assert (removed, trimmed, skipped) == (0, 1, 0)
    assert out.count("{") == out.count("}")
    assert "OR = { has_idea = a has_idea = b }" in out
    assert "original_tag" not in out


def test_trimmed_block_keeps_its_indentation():
    # The opener regex matches from column 0, so a `head` sliced at match.start()
    # is always empty and every trimmed block lands flush left.
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = {",
            "\t\toriginal_tag = FOO",
            "\t\thas_idea = the_military",
            "\t}",
            "}",
        ]
    )
    out, _removed, trimmed = _strip(text)
    assert trimmed == 1
    assert out.split("\n")[1] == "\tenable = {"


def test_gate_on_the_closing_line_is_stripped():
    # The validator counts a gate here, so the stripper has to reach it too or
    # it reports a finding no tool will fix.
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = {",
            "\t\thas_idea = the_military",
            "\t\talways = yes }",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed, skipped = _strip_full(text)
    assert (removed, trimmed, skipped) == (0, 1, 0)
    assert "always" not in out
    assert "has_idea = the_military" in out
    assert out.count("{") == out.count("}")


def test_removing_the_first_child_leaves_no_blank_under_the_opener():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { always = yes }",
            "",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, _trimmed = _strip(text)
    assert removed == 1
    assert out.split("\n") == [
        "FOO_modifier = {",
        "\tstability_factor = FOO_stab",
        "}",
    ]


def test_removing_the_last_child_leaves_no_blank_above_the_closer():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tstability_factor = FOO_stab",
            "",
            "\tenable = { always = yes }",
            "}",
        ]
    )
    out, removed, _trimmed = _strip(text)
    assert removed == 1
    assert out.split("\n") == [
        "FOO_modifier = {",
        "\tstability_factor = FOO_stab",
        "}",
    ]


def test_packed_body_keeps_a_trigger_whose_name_ends_in_tag():
    # `tag = ISR` is a substring of `has_cosmetic_tag = ISR`; without a word
    # boundary the splice eats a live trigger and leaves `has_cosmetic_`.
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { has_cosmetic_tag = ISR }",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed, skipped = _strip_full(text)
    assert (removed, trimmed, skipped) == (0, 0, 0)
    assert out == text


def test_tag_inside_a_packed_nested_branch_is_not_spliced():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { OR = { original_tag = SOV original_tag = TAJ } }",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed, skipped = _strip_full(text)
    assert (removed, trimmed, skipped) == (0, 0, 0)
    assert out == text


def test_closer_shared_with_the_modifier_own_brace_keeps_that_brace():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tstability_factor = FOO_stab",
            "\tenable = { original_tag = FOO } }",
            "BAR_modifier = {",
            "\tenable = { original_tag = BAR }",
            "\tstability_factor = BAR_stab",
            "}",
        ]
    )
    out, removed, trimmed = _strip(text)
    # The second block proves the definition stack did not drift a level
    # deeper when the shared closer was emitted.
    assert (removed, trimmed) == (2, 0)
    assert out.count("{") == out.count("}")
    assert "BAR_modifier" in out
    assert "original_tag" not in out


def test_gate_packed_onto_a_multiline_opener_is_stripped():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = { original_tag = FOO",
            "\t\thas_idea = the_military",
            "\t}",
            "\tstability_factor = FOO_stab",
            "}",
        ]
    )
    out, removed, trimmed, skipped = _strip_full(text)
    assert (removed, trimmed, skipped) == (0, 1, 0)
    assert "original_tag" not in out
    assert "has_idea = the_military" in out
    assert out.count("{") == out.count("}")


def test_unbalanced_block_is_left_alone():
    text = "\n".join(
        [
            "FOO_modifier = {",
            "\tenable = {",
            "\t\toriginal_tag = FOO",
        ]
    )
    out, removed, trimmed, skipped = _strip_full(text)
    assert (removed, trimmed, skipped) == (0, 0, 1)
    assert out == text


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


_MOD_SAMPLE = (
    "FOO_modifier = {\n\tenable = { always = yes }\n\tstability_factor = x\n}\n"
)


def _write_mod(path, text, newline=""):
    with open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def test_dry_run_reports_without_writing(tmp_path):
    mod_path = tmp_path / "dynmod.txt"
    _write_mod(mod_path, _MOD_SAMPLE)

    assert process_file(str(mod_path), dry_run=True, backup=False) == (1, 0, 0, False)
    assert mod_path.read_text(encoding="utf-8") == _MOD_SAMPLE


def test_crlf_survives_the_rewrite(tmp_path):
    mod_path = tmp_path / "dynmod.txt"
    _write_mod(mod_path, _MOD_SAMPLE.replace("\n", "\r\n"))

    process_file(str(mod_path), dry_run=False, backup=False)
    payload = mod_path.read_bytes()
    assert b"\r\n" in payload
    assert b"\n" not in payload.replace(b"\r\n", b"")
    assert b"enable" not in payload


def test_unreadable_file_is_reported_not_raised(tmp_path):
    assert process_file(str(tmp_path / "missing.txt"), False, False) == (0, 0, 0, True)


def test_main_exits_non_zero_on_an_unbalanced_block(tmp_path, monkeypatch):
    path = tmp_path / "test.txt"
    _write_mod(path, "FOO_modifier = {\n\tenable = {\n\t\toriginal_tag = FOO\n")
    monkeypatch.setattr(
        sys, "argv", ["strip_dynmod_tag_gates.py", "--root", str(tmp_path), str(path)]
    )

    assert main() == 1


def test_backup_is_written_beside_the_rewritten_file(tmp_path):
    mod_path = tmp_path / "dynmod.txt"
    _write_mod(mod_path, _MOD_SAMPLE)

    assert process_file(str(mod_path), dry_run=False, backup=True) == (1, 0, 0, False)
    assert "enable" not in mod_path.read_text(encoding="utf-8")
    assert list(tmp_path.glob("dynmod.txt.backup.*"))


def test_main_sweeps_the_dynamic_modifiers_directory_by_default(tmp_path, monkeypatch):
    mod_dir = tmp_path / "common" / "dynamic_modifiers"
    mod_dir.mkdir(parents=True)
    target = mod_dir / "modifiers.txt"
    _write_mod(target, _MOD_SAMPLE)
    monkeypatch.setattr(
        sys, "argv", ["strip_dynmod_tag_gates.py", "--root", str(tmp_path)]
    )

    assert main() == 0
    assert "enable" not in target.read_text(encoding="utf-8")


def test_main_errors_when_the_modifier_directory_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["strip_dynmod_tag_gates.py", "--root", str(tmp_path)]
    )
    assert main() == 1


def test_main_reports_a_file_it_cannot_read(tmp_path, monkeypatch):
    clean = tmp_path / "clean.txt"
    _write_mod(clean, "FOO_modifier = {\n\tstability_factor = x\n}\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "strip_dynmod_tag_gates.py",
            "--root",
            str(tmp_path),
            str(tmp_path / "missing.txt"),
            str(clean),
        ],
    )

    assert main() == 1
    assert clean.read_text(encoding="utf-8") == (
        "FOO_modifier = {\n\tstability_factor = x\n}\n"
    )
