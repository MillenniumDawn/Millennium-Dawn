"""Regressions for the untooltipped-available-scripted-trigger check in
validate_variables.

A scripted trigger whose body is a stack of unwrapped has_global_flag checks
renders no tooltip of its own. Called bare (`<name> = yes`) inside a
player-facing `available` block with no wrapper, the player sees nothing at
all where a requirement line belongs - one hop further out than the
unlocalised-available-flag check, which at least sees the raw flag token
directly in `available`. Wrappers inside the definition already supply that
line, so those triggers are not indexed.

`visible` is deliberately not covered, for the same reason as the sibling
checks: a failing visible hides the object outright, so no tooltip renders
either way.
"""

import validate_variables as V

_FLAGGED = frozenset({"pak_raj_border_available"})


def _findings(tmp_path, text, flagged=_FLAGGED):
    f = tmp_path / "src.txt"
    f.write_text(text, encoding="utf-8")
    return V.process_file_for_untooltipped_available_scripted_trigger(
        (str(f), str(tmp_path), flagged)
    )


def test_bare_flagged_trigger_in_available_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tpak_raj_border_available = yes\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1
    assert "pak_raj_border_available" in out[0][0]
    assert "resolves to a scripted trigger" in out[0][0]
    assert out[0][2] == 3


def test_custom_trigger_tooltip_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_trigger_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\tpak_raj_border_available = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_hidden_trigger_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thidden_trigger = { pak_raj_border_available = yes }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_custom_override_tooltip_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_override_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\tpak_raj_border_available = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_visible_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tvisible = {\n"
        "\t\tpak_raj_border_available = yes\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_builtin_block_excluded_from_index(tmp_path):
    # A builtin block name sitting at depth 0 of a scripted_triggers file
    # (malformed script, or a block header collision) must never be indexed
    # as a scripted trigger - HOI4_BUILTIN_BLOCKS is the guard. Filtering
    # happens when the index is built, not in the pool worker, which trusts
    # whatever name set it is handed.
    trig_dir = tmp_path / "common" / "scripted_triggers"
    trig_dir.mkdir(parents=True)
    (trig_dir / "malformed.txt").write_text(
        "if = {\n\thas_global_flag = GLOBAL_x\n}\n",
        encoding="utf-8",
    )
    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    assert "if" not in v._collect_scripted_trigger_flag_names()


def test_unknown_token_not_flagged(tmp_path):
    # A bare call whose name never resolved to an indexed scripted trigger
    # (typo, or a trigger with no flag body) is out of scope.
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tsome_other_trigger = yes\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_no_flagged_names_short_circuits(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tpak_raj_border_available = yes\n"
        "\t}\n"
        "}\n",
        flagged=frozenset(),
    )
    assert out == []


def test_brace_in_log_string_does_not_desync(tmp_path):
    # An unblanked `}` inside a quoted string would pop the stack early and
    # hide the real finding below it.
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tcomplete_effect = {\n"
        '\t\tlog = "[GetDateText]: broken } brace"\n'
        "\t}\n"
        "\tavailable = {\n"
        "\t\tpak_raj_border_available = yes\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1


def test_commented_line_ignored(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\t# pak_raj_border_available = yes\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_index_builder_finds_flagged_trigger(tmp_path):
    trig_dir = tmp_path / "common" / "scripted_triggers"
    trig_dir.mkdir(parents=True)
    (trig_dir / "border_war.txt").write_text(
        "pak_raj_border_available = {\n"
        "\tNOT = { has_global_flag = GLOBAL_pak_raj_border_war_active }\n"
        "}\n"
        "pak_raj_border_pair_valid = {\n"
        "\tis_puppet = no\n"
        "}\n",
        encoding="utf-8",
    )
    dec_dir = tmp_path / "common" / "decisions"
    dec_dir.mkdir(parents=True)
    (dec_dir / "test.txt").write_text(
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tpak_raj_border_available = yes\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )

    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_untooltipped_available_scripted_trigger()

    assert len(v._issues) == 1
    issue = v._issues[0]
    assert "pak_raj_border_available" in issue.message
    assert issue.severity == V.Severity.WARNING
    assert issue.category == "untooltipped-available-scripted-trigger"


def _index_names(tmp_path, text):
    trig_dir = tmp_path / "common" / "scripted_triggers"
    trig_dir.mkdir(parents=True)
    (trig_dir / "t.txt").write_text(text, encoding="utf-8")
    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    return v._collect_scripted_trigger_flag_names()


def test_index_skips_custom_trigger_tooltip_in_body(tmp_path):
    names = _index_names(
        tmp_path,
        "can_do_african_union_focus = {\n"
        "\tcustom_trigger_tooltip = {\n"
        "\t\ttooltip = can_do_african_union_focus_tt\n"
        "\t\tcheck_variable = { global.african_union_western_outlook_share > 0.50 }\n"
        "\t}\n"
        "\tcustom_trigger_tooltip = {\n"
        "\t\ttooltip = african_union_available_mandate_tt\n"
        "\t\thas_global_flag = african_union_mandate_granted\n"
        "\t}\n"
        "}\n",
    )
    assert "can_do_african_union_focus" not in names


def test_index_skips_custom_override_tooltip_in_body(tmp_path):
    names = _index_names(
        tmp_path,
        "au_mandate_ready = {\n"
        "\tcustom_override_tooltip = {\n"
        "\t\ttooltip = african_union_available_mandate_tt\n"
        "\t\thas_global_flag = african_union_mandate_granted\n"
        "\t}\n"
        "}\n",
    )
    assert "au_mandate_ready" not in names


def test_index_skips_hidden_trigger_in_body(tmp_path):
    names = _index_names(
        tmp_path,
        "hidden_mandate = {\n"
        "\thidden_trigger = { has_global_flag = african_union_mandate_granted }\n"
        "}\n",
    )
    assert "hidden_mandate" not in names


def test_index_still_flags_mixed_wrapped_and_bare(tmp_path):
    names = _index_names(
        tmp_path,
        "mixed_trigger = {\n"
        "\tcustom_trigger_tooltip = {\n"
        "\t\ttooltip = wrapped_tt\n"
        "\t\thas_global_flag = WRAP_ok\n"
        "\t}\n"
        "\thas_global_flag = BARE_bad\n"
        "}\n",
    )
    assert "mixed_trigger" in names


def test_wrapped_body_bare_call_not_flagged(tmp_path):
    trig_dir = tmp_path / "common" / "scripted_triggers"
    trig_dir.mkdir(parents=True)
    (trig_dir / "au.txt").write_text(
        "can_do_african_union_focus = {\n"
        "\tcustom_trigger_tooltip = {\n"
        "\t\ttooltip = can_do_african_union_focus_tt\n"
        "\t\tcheck_variable = { global.african_union_western_outlook_share > 0.50 }\n"
        "\t}\n"
        "\tcustom_trigger_tooltip = {\n"
        "\t\ttooltip = african_union_available_mandate_tt\n"
        "\t\thas_global_flag = african_union_mandate_granted\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    focus_dir = tmp_path / "common" / "national_focus"
    focus_dir.mkdir(parents=True)
    (focus_dir / "au.txt").write_text(
        "shared_focus = {\n"
        "\tid = AFRICAN_UNION_shared_focus_create_investment_bank\n"
        "\tavailable = {\n"
        "\t\tcan_do_african_union_focus = yes\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )

    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_untooltipped_available_scripted_trigger()

    assert v._issues == []
