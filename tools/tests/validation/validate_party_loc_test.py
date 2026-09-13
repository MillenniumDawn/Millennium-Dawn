"""Tests for validate_party_loc.py.

The validator audits the party loc keys that exist against the standard in
.claude/docs/party-loc-reference.md. It never reports a missing nation, a
missing slot or a missing key -- an unfilled slot is meant to fall through to
the generic label.
"""

import validate_party_loc as V
from shared.suite import issue_categories as _categories
from shared.suite import run_validator

LOC = V.LOC_PATH
HOOK = V.HOOK_PATH

_GRE_NAME = ' GRE.conservatism:0 "£GRE_conservative (ND) - New Democracy"\n'
_GRE_DESC = (
    ' GRE.conservatism_desc:0 "(Liberal Conservatism) - New Democracy'
    ' (Greek: Nea Dimokratia, ND)\\n\\nFounded in October 1974."\n'
)
_GRE_HOOKS = (
    "defined_text = {\n"
    "\tname = conservatism_L\n"
    "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism }\n"
    "\ttext = { localization_key = generic.conservatism }\n"
    "}\n"
    "defined_text = {\n"
    "\tname = conservatism_L_desc\n"
    "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism_desc }\n"
    "\ttext = { localization_key = generic.conservatism_desc }\n"
    "}\n"
)


def _run(tmp_path, write_path, loc_body, hook_body, **kwargs):
    write_path(tmp_path, LOC, "l_english:\n" + loc_body)
    write_path(tmp_path, HOOK, hook_body)
    kwargs.setdefault("scan_all", True)
    return run_validator(V.Validator, tmp_path, **kwargs)


def test_a_standard_block_is_clean(tmp_path, write_path):
    validator = _run(tmp_path, write_path, _GRE_NAME + _GRE_DESC, _GRE_HOOKS)
    assert validator._issues == []


def test_missing_files_are_not_an_error(tmp_path, write_path):
    validator = run_validator(V.Validator, tmp_path, scan_all=True)
    assert validator._issues == []


def test_name_without_abbreviation_is_flagged(tmp_path, write_path):
    loc = ' GRE.conservatism:0 "£GRE_conservative New Democracy"\n'
    validator = _run(tmp_path, write_path, loc, _GRE_HOOKS)
    assert "party-loc-name-format" in _categories(validator)


def test_monarchist_needs_no_abbreviation(tmp_path, write_path):
    loc = ' GRE.Monarchist:0 "£GRE_monarchist House of Glücksburg"\n'
    hooks = (
        "defined_text = {\n"
        "\tname = Monarchist_L\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.Monarchist }\n"
        "}\n"
    )
    validator = _run(tmp_path, write_path, loc, hooks)
    assert validator._issues == []


def test_empty_description_is_flagged(tmp_path, write_path):
    loc = _GRE_NAME + ' GRE.conservatism_desc:0 ""\n'
    validator = _run(tmp_path, write_path, loc, _GRE_HOOKS)
    assert _categories(validator) == ["party-loc-empty-desc"]


def test_description_header_and_body_are_flagged(tmp_path, write_path):
    loc = _GRE_NAME + ' GRE.conservatism_desc:0 "New Democracy is a Greek party."\n'
    validator = _run(tmp_path, write_path, loc, _GRE_HOOKS)
    assert _categories(validator) == ["party-loc-desc-body", "party-loc-desc-header"]


def test_key_with_no_hook_is_flagged(tmp_path, write_path):
    validator = _run(tmp_path, write_path, _GRE_NAME + _GRE_DESC, "")
    assert _categories(validator) == ["party-loc-missing-hook"] * 2


def test_hook_pointing_at_a_missing_key_is_flagged(tmp_path, write_path):
    hooks = _GRE_HOOKS + (
        "defined_text = {\n"
        "\tname = Nat_Fascism_L\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.Nat_Fascism }\n"
        "}\n"
    )
    validator = _run(tmp_path, write_path, _GRE_NAME + _GRE_DESC, hooks)
    assert _categories(validator) == ["party-loc-orphan-hook"]


def test_bespoke_key_is_not_flagged(tmp_path, write_path):
    loc = _GRE_NAME + _GRE_DESC + ' ITA.forza_nuova_loc_key:0 "£generic Forza"\n'
    validator = _run(tmp_path, write_path, loc, _GRE_HOOKS)
    assert validator._issues == []


def test_miscased_subideology_is_flagged(tmp_path, write_path):
    loc = _GRE_NAME + _GRE_DESC + ' POL.Neutral_Green:0 "£generic Greens"\n'
    validator = _run(tmp_path, write_path, loc, _GRE_HOOKS)
    assert _categories(validator) == ["party-loc-slot-case"]


def test_generic_block_is_never_flagged(tmp_path, write_path):
    loc = _GRE_NAME + _GRE_DESC + ' generic.conservatism:0 "£g Conservatives"\n'
    validator = _run(tmp_path, write_path, loc, _GRE_HOOKS)
    assert validator._issues == []


def test_icon_disagreeing_with_the_name_sprite_is_flagged(tmp_path, write_path):
    loc = _GRE_NAME + ' GRE.conservatism_icon:0 "£GRE_other"\n'
    hooks = (
        "defined_text = {\n"
        "\tname = conservatism_L\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism }\n"
        "}\n"
        "defined_text = {\n"
        "\tname = conservatism_L_icon\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism_icon }\n"
        "}\n"
    )
    validator = _run(tmp_path, write_path, loc, hooks)
    assert _categories(validator) == ["party-loc-icon-sprite-mismatch"]


def test_desc_without_a_name_key_is_flagged(tmp_path, write_path):
    hooks = (
        "defined_text = {\n"
        "\tname = conservatism_L_desc\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism_desc }\n"
        "}\n"
    )
    validator = _run(tmp_path, write_path, _GRE_DESC, hooks)
    assert _categories(validator) == ["party-loc-key-without-name"]


def test_duplicate_unconditional_gate_is_flagged(tmp_path, write_path):
    hooks = (
        "defined_text = {\n"
        "\tname = conservatism_L\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism }\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism }\n"
        "}\n"
        "defined_text = {\n"
        "\tname = conservatism_L_desc\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism_desc }\n"
        "}\n"
    )
    validator = _run(tmp_path, write_path, _GRE_NAME + _GRE_DESC, hooks)
    assert _categories(validator) == ["party-loc-duplicate-hook"]


def test_a_gated_pair_is_not_a_duplicate(tmp_path, write_path):
    """Date-split entries repeat the tag but each carries its own condition."""
    loc = (
        _GRE_NAME
        + _GRE_DESC
        + ' GRE.conservatism_alt:0 "£GRE_conservative (ND2) - New Democracy"\n'
    )
    hooks = (
        "defined_text = {\n"
        "\tname = conservatism_L\n"
        "\ttext = { trigger = { original_tag = GRE date < 2023.1.1 } localization_key = GRE.conservatism }\n"
        "\ttext = { trigger = { original_tag = GRE date > 2023.1.1 } localization_key = GRE.conservatism_alt }\n"
        "}\n"
        "defined_text = {\n"
        "\tname = conservatism_L_desc\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism_desc }\n"
        "}\n"
    )
    validator = _run(tmp_path, write_path, loc, hooks)
    assert validator._issues == []


def test_defined_text_opener_does_not_swallow_the_block(tmp_path, write_path):
    """`defined_text = {` must not be read as a `text = {` entry."""
    hooks = (
        "defined_text = {\n"
        "\tname = conservatism_L\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism }\n"
        "}\n"
        "defined_text = {\n"
        "\tname = conservatism_L_desc\n"
        "\ttext = { trigger = { original_tag = GRE } localization_key = GRE.conservatism_desc }\n"
        "}\n"
    )
    assert V.find_duplicate_hooks(hooks) == []


def test_nothing_changed_reports_nothing(tmp_path, write_path):
    """Without --all or --tag the scope comes from git, which sees no repo here."""
    loc = ' CAN.conservatism:0 "£generic Liberals"\n'
    validator = _run(tmp_path, write_path, loc, "", scan_all=False)
    assert validator._issues == []


def test_tag_filter_limits_the_audit(tmp_path, write_path):
    loc = _GRE_NAME + _GRE_DESC + ' CAN.conservatism:0 "£generic Liberals"\n'
    validator = _run(tmp_path, write_path, loc, _GRE_HOOKS, scan_all=False, tag=["GRE"])
    assert validator._issues == []


def test_only_the_staged_tag_is_audited(tmp_path, write_path):
    """The default scope is the tags the diff touches, not the whole file."""
    from shared.suite import initialize_git_repository, run_git

    broken = ' CAN.conservatism:0 "£generic Liberals"\n'
    write_path(tmp_path, LOC, "l_english:\n" + _GRE_NAME + _GRE_DESC + broken)
    write_path(tmp_path, HOOK, _GRE_HOOKS)
    initialize_git_repository(tmp_path, LOC, HOOK)

    write_path(
        tmp_path,
        LOC,
        "l_english:\n"
        + _GRE_NAME
        + _GRE_DESC
        + ' CAN.conservatism:0 "£generic Grits"\n',
    )
    run_git(tmp_path, "add", LOC)

    validator = run_validator(V.Validator, tmp_path)
    assert {issue.line for issue in validator._issues} == {4}
    assert _categories(validator) == [
        "party-loc-missing-hook",
        "party-loc-name-format",
    ]
