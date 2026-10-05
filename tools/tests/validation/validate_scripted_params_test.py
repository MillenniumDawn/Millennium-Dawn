"""Unit tests for validate_scripted_params.

Pins these behaviors for change_influence_percentage:
  1. tag_index and influence_target stay OPTIONAL (the effect's own
     fallbacks to ROOT / THIS are reliable defaults and are used by the
     majority of call sites — the `for_each_scope_loop` pattern depends
     on influence_target defaulting to THIS).
  2. When a call site does set BOTH params explicitly, the validator
     catches the self-influence (Code 5001) bug where they are set to
     the same value. Setting only one is fine; defaults are reliable.
  3. An explicit tag_index / influence_target that is not a real country
     tag or tag alias is flagged as an ERROR (a typo such as GBR for ENG
     or the mis-cased CHl for CHI). Scope keywords, var: / event_target:
     refs, array subscripts, numerics, and aliases are accepted.
"""

import json
import runpy
import sys

import pytest
import validate_scripted_params as vsp
from shared.suite import initialize_git_repository, run_git
from shared_utils import collapse_or_compact
from validate_scripted_params import _validate_call_sites_in_file


@pytest.fixture
def cip_contract():
    """The change_influence_percentage contract as the validator builds it.

    Pinning it here means a future refactor of the hardcoded block that
    promotes tag_index/influence_target to required (or removes them)
    will fail this test instead of silently regressing.
    """
    return {
        "change_influence_percentage": {
            "required": ["percent_change"],
            "optional": ["tag_index", "influence_target"],
        },
    }


# Tags + aliases the test bodies reference. STC / NTR stand in for real tag
# aliases; the rest are real country tags used across the fixtures.
_TEST_VALID_TAGS = frozenset(
    {
        "USA",
        "KOR",
        "CHI",
        "ENG",
        "ICE",
        "SOV",
        "GER",
        "FRA",
        "TAI",
        "ISR",
        "STC",  # alias
        "NTR",  # alias
    }
)


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(content)


def _issues(caller_body, contracts, mod_path, valid_tags=_TEST_VALID_TAGS):
    """Run the per-file validator against a one-shot focus file."""
    focus_dir = mod_path / "common" / "national_focus"
    fpath = focus_dir / "test_focus.txt"
    _write(fpath, caller_body)
    results = _validate_call_sites_in_file(
        (str(fpath), contracts, str(mod_path), frozenset(valid_tags), frozenset())
    )
    out = []
    for cat, msg, _line in results:
        if (
            cat in ("missing-required-param", "identical-influence-params")
            and "change_influence_percentage" in msg
        ):
            out.append((cat, msg))
        elif cat == "invalid-influence-tag":
            out.append((cat, msg))
    return out


def _missing_required_param_issues(tmp_path):
    validator = vsp.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return [
        issue
        for issue in validator._issues
        if issue.category == "missing-required-param"
    ]


def test_contract_parser_reads_parameter_after_header(tmp_path):
    effect_path = tmp_path / "common" / "scripted_effects" / "test_effect.txt"
    _write(
        effect_path,
        "# Parameter:\n# - required_param: country id\ntest_contracted_effect = {\n}\n",
    )

    assert vsp._parse_effect_contracts_from_file(str(effect_path)) == {
        "test_contracted_effect": {
            "required": ["required_param"],
            "optional": [],
        }
    }


def test_validator_enforces_uppercase_effect_and_parameter_names(tmp_path):
    effect_path = tmp_path / "common" / "scripted_effects" / "test_effect.txt"
    caller_path = tmp_path / "events" / "test_event.txt"
    _write(
        effect_path,
        "# Parameters:\n"
        "# - ENG_agitation_change: signed amount\n"
        "ENG_change_scottish_agitation = {\n}\n",
    )
    _write(caller_path, "ENG_change_scottish_agitation = yes\n")

    issues = _missing_required_param_issues(tmp_path)
    assert len(issues) == 1
    assert "ENG_agitation_change" in issues[0].message


@pytest.mark.parametrize(
    "caller_dir",
    [
        "common/on_actions",
        "common/scripted_guis",
        "common/operations",
        "common/scripted_diplomatic_actions",
        "common/ideas",
        "common/military_industrial_organization/organizations",
        "common/factions/goals",
        "common/bop",
        "events",
        "history/countries",
    ],
)
def test_validator_scans_all_scripted_effect_caller_directories(tmp_path, caller_dir):
    effect_path = tmp_path / "common" / "scripted_effects" / "test_effect.txt"
    caller_path = tmp_path / caller_dir / "test_caller.txt"
    _write(
        effect_path,
        "# Parameter:\n# - required_param: country id\ntest_contracted_effect = {\n}\n",
    )
    _write(caller_path, "test_contracted_effect = yes\n")

    issues = _missing_required_param_issues(tmp_path)
    assert len(issues) == 1
    assert issues[0].file == f"{caller_dir}/test_caller.txt"


def test_change_influence_percentage_with_only_percent_change_passes(
    tmp_path, cip_contract
):
    """Defaults are reliable: a call with only percent_change must not be flagged.

    This is the most common call-site pattern in the corpus — the effect
    defaults tag_index to ROOT and influence_target to THIS, which is
    correct when the call runs in the focus owner's scope.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert issues == []


def test_change_influence_percentage_with_only_tag_index_passes(tmp_path, cip_contract):
    """Setting only tag_index is fine: influence_target defaults to THIS."""
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = USA.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert issues == []


def test_change_influence_percentage_with_only_influence_target_passes(
    tmp_path, cip_contract
):
    """Setting only influence_target is fine: tag_index defaults to ROOT."""
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { influence_target = KOR.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert issues == []


def test_change_influence_percentage_dot_id_syntax_variants_are_flagged(
    tmp_path, cip_contract
):
    """Syntactic variants of the same country (USA vs USA.id) must flag.

    The corpus mixes both forms; at runtime they resolve to the same
    country ID.  Without normalization, a pair like
        set_temp_variable = { tag_index = USA }
        set_temp_variable = { influence_target = USA.id }
    would slip through the literal-string check even though it produces
    a self-influence at runtime.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = USA }\n"
        "        set_temp_variable = { influence_target = USA.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any("identical-influence-params" in c for c, _ in issues)
    flagged = next(m for c, m in issues if c == "identical-influence-params")
    # Both original values should appear in the message so a reader can
    # see the syntactic variant, not just the normalized form.
    assert "'USA'" in flagged
    assert "'USA.id'" in flagged


def test_change_influence_percentage_var_id_syntax_variants_are_flagged(
    tmp_path, cip_contract
):
    """var:foo vs var:foo.id (same variable, different syntax) must flag.

    Variable references in HOI4 can be written as `var:foo` (a scope)
    or `var:foo.id` (the scope's ID).  At runtime both pass the same
    numeric value to the effect; the check needs to treat them as equal.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = var:foo }\n"
        "        set_temp_variable = { influence_target = var:foo.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any("identical-influence-params" in c for c, _ in issues)


def test_change_influence_percentage_scope_keyword_id_variants_are_flagged(
    tmp_path, cip_contract
):
    """THIS vs THIS.id (same scope keyword, different syntax) must flag.

    The same applies to ROOT/PREV/FROM.  All five scope keywords are
    commonly written with or without the trailing .id; both forms
    resolve to the same country ID.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = THIS }\n"
        "        set_temp_variable = { influence_target = THIS.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any("identical-influence-params" in c for c, _ in issues)


def test_change_influence_percentage_event_target_id_variants_are_flagged(
    tmp_path, cip_contract
):
    """event_target:foo vs event_target:foo.id (same event target) must flag.

    Events commonly pass country references via event_target; the
    syntactic variant .id vs no .id is the same pattern as country tags.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = event_target:foo }\n"
        "        set_temp_variable = { influence_target = event_target:foo.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any("identical-influence-params" in c for c, _ in issues)


def test_change_influence_percentage_dot_id_normalization_keeps_distinct_values(
    tmp_path, cip_contract
):
    """USA and GER (different countries) must NOT flag even with .id variants.

    Regression guard for the normalization: stripping .id should not
    collapse genuinely different countries.  USA / GER.id and
    USA.id / GER should both stay unflagged.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = USA }\n"
        "        set_temp_variable = { influence_target = GER.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert not any(c == "identical-influence-params" for c, _ in issues)


def test_change_influence_percentage_identical_country_tag_is_flagged(
    tmp_path, cip_contract
):
    """Both set to the same country tag is a guaranteed self-influence (Code 5001)."""
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = USA.id }\n"
        "        set_temp_variable = { influence_target = USA.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any("identical-influence-params" in c for c, _ in issues)
    flagged = next(m for c, m in issues if c == "identical-influence-params")
    assert "'USA.id'" in flagged


def test_change_influence_percentage_identical_scope_is_flagged(tmp_path, cip_contract):
    """Both set to the same scope keyword (e.g. ROOT) is the canonical self-influence.

    This is the most common runtime Code 5001 trigger the corpus sees:
    a focus or event sets tag_index = ROOT and influence_target = ROOT
    (or omits one and lets the effect default it to ROOT/THIS), and the
    influence tries to push influence_target onto ROOT itself.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = ROOT.id }\n"
        "        set_temp_variable = { influence_target = ROOT.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any("identical-influence-params" in c for c, _ in issues)


def test_change_influence_percentage_this_in_outer_and_inner_scopes_passes(
    tmp_path, cip_contract
):
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = THIS.id }\n"
        "        every_neighbor_country = {\n"
        "            set_temp_variable = { influence_target = THIS }\n"
        "            change_influence_percentage = yes\n"
        "        }\n"
        "    }\n"
        "}\n"
    )
    assert _issues(body, cip_contract, tmp_path) == []


def test_change_influence_percentage_distinct_values_passes(tmp_path, cip_contract):
    """Both set but to different values is the correct call site — no flag."""
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = USA.id }\n"
        "        set_temp_variable = { influence_target = KOR.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert issues == []


def test_change_influence_percentage_with_zero_value_treated_as_unset(
    tmp_path, cip_contract
):
    """Explicitly setting tag_index = 0 must not flag against influence_target = USA.id.

    0 is the effect's sentinel for "use the default"; treating 0 as a
    real value would generate a flood of false positives on call sites
    that pre-initialise one of the two to 0 to make it explicit.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = 0 }\n"
        "        set_temp_variable = { influence_target = USA.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert issues == []


def test_change_influence_percentage_still_requires_percent_change(
    tmp_path, cip_contract
):
    """percent_change remains required; the identity check did not displace it."""
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { tag_index = USA.id }\n"
        "        set_temp_variable = { influence_target = KOR.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any(
        "missing-required-param" in c and "percent_change" in m for c, m in issues
    )


def test_change_influence_percentage_identical_across_adjacent_calls_is_flagged(
    tmp_path, cip_contract
):
    """The leak-between-calls bug pattern: tag_index from one call is reused by the next.

    Pattern in the corpus (e.g. 05_russia.txt:21561):
        set_temp_variable = { percent_change = 2 }
        set_temp_variable = { tag_index = TAI }
        set_temp_variable = { influence_target = SOV }
        change_influence_percentage = yes
        set_temp_variable = { percent_change = 2 }
        set_temp_variable = { influence_target = TAI }
        change_influence_percentage = yes    # tag_index = TAI still in scope

    The second call has influence_target = TAI explicitly and tag_index
    still resolving to TAI from the first call (no scope change between
    them).  At runtime, both resolve to TAI → Code 5001.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 2 }\n"
        "        set_temp_variable = { tag_index = TAI }\n"
        "        set_temp_variable = { influence_target = SOV }\n"
        "        change_influence_percentage = yes\n"
        "        set_temp_variable = { percent_change = 2 }\n"
        "        set_temp_variable = { influence_target = TAI }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    identical = [m for c, m in issues if c == "identical-influence-params"]
    assert len(identical) == 1
    assert "'TAI'" in identical[0]


def test_change_influence_percentage_identical_with_distant_set_is_filtered(
    tmp_path, cip_contract
):
    """The 20-line proximity window filters out scope-tracking false positives.

    The validator's frame-based scope tracking keeps a temp var from an
    earlier block it does not reset (a previous scripted effect) visible to
    the current call, even though it wouldn't be in scope at runtime.
    Tagging a stale `tag_index` from 25+ lines back as identical to the
    current `influence_target` would create noise; the proximity window
    prevents that.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        # Stale tag_index, 25+ lines back from the call.
        "        set_temp_variable = { tag_index = TAI }\n"
        + ("        add_political_power = 0.01\n" * 25)
        + "        set_temp_variable = { percent_change = 2 }\n"
        "        set_temp_variable = { influence_target = TAI }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert not any(c == "identical-influence-params" for c, _ in issues)


def test_compact_plain_scope_keeps_set_before_call_visible(tmp_path, cip_contract):
    body = (
        "shared_focus = { completion_reward = { "
        "set_temp_variable = { percent_change = 5 } "
        "change_influence_percentage = yes } }\n"
    )
    assert _issues(body, cip_contract, tmp_path) == []


def test_compact_scope_boundary_hides_set_after_close(tmp_path, cip_contract):
    body = (
        "shared_focus = { completion_reward = { "
        "ROOT = { set_temp_variable = { percent_change = 5 } } "
        "change_influence_percentage = yes } }\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any(
        category == "missing-required-param" and "percent_change" in message
        for category, message in issues
    )


def test_uppercase_controller_scope_hides_temp_after_close(tmp_path, cip_contract):
    body = (
        "shared_focus = { completion_reward = { "
        "CONTROLLER = { set_temp_variable = { percent_change = 5 } } "
        "change_influence_percentage = yes } }\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any(
        category == "missing-required-param" and "percent_change" in message
        for category, message in issues
    )


def test_multiline_temp_and_controller_target_pass(tmp_path, cip_contract):
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        CONTROLLER = { set_temp_variable = { influence_target = THIS } }\n"
        "        ROOT = {\n"
        "            set_temp_variable = {\n"
        "                percent_change = {\n"
        "                    value = 5\n"
        "                    multiply = -1\n"
        "                }\n"
        "            }\n"
        "            set_temp_variable = { tag_index = THIS.id }\n"
        "            change_influence_percentage = yes\n"
        "        }\n"
        "    }\n"
        "}\n"
    )
    assert _issues(body, cip_contract, tmp_path) == []


def test_hardcoded_cip_contract_keeps_optional_secondary_params():
    """Guard rail: HARDCODED_CONTRACTS must keep tag_index/influence_target optional.

    The original "promote to required" interpretation was rejected
    because it would flag ~870 call sites that rely on the ROOT/THIS
    defaults (e.g. every `for_each_scope_loop` over an array of
    influence targets). The identity check is the right way to catch
    the real bug class.
    """
    contract = vsp.HARDCODED_CONTRACTS.get("change_influence_percentage")
    assert contract is not None
    assert contract["required"] == ["percent_change"]
    assert set(contract["optional"]) == {"tag_index", "influence_target"}


# --- tag-validity check ---------------------------------------------------


def _tag_body(param, value):
    return (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        f"        set_temp_variable = {{ {param} = {value} }}\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )


def _invalid_tags(issues):
    return [m for c, m in issues if c == "invalid-influence-tag"]


@pytest.mark.parametrize("value", ["CHI", "CHI.id", "USA", "USA.ID"])
def test_valid_country_tag_passes(tmp_path, cip_contract, value):
    """A real tag, with or without .id (any case), is never flagged."""
    issues = _issues(_tag_body("tag_index", value), cip_contract, tmp_path)
    assert _invalid_tags(issues) == []


@pytest.mark.parametrize("value", ["STC", "NTR"])
def test_valid_tag_alias_passes(tmp_path, cip_contract, value):
    """Tag aliases (e.g. STC / NTR) are valid references, not typos."""
    issues = _issues(_tag_body("influence_target", value), cip_contract, tmp_path)
    assert _invalid_tags(issues) == []


@pytest.mark.parametrize("value", ["ROOT", "THIS", "FROM", "PREV", "Root", "FROM.ID"])
def test_scope_keyword_passes(tmp_path, cip_contract, value):
    """Scope keywords (case-insensitive, with or without .id) are not tags."""
    issues = _issues(_tag_body("influence_target", value), cip_contract, tmp_path)
    assert _invalid_tags(issues) == []


@pytest.mark.parametrize(
    "value",
    [
        "var:foo",
        "var:foo.id",
        "event_target:bar",
        "event_target:bar.id",
        "global.some_tag",
        "influence_array^0",
        "0",
        "some_lowercase_var",
        "v",
    ],
)
def test_non_tag_forms_pass(tmp_path, cip_contract, value):
    """var: / event_target: / global. refs, array subscripts, numerics, and
    bare temp-variable names are all accepted."""
    issues = _issues(_tag_body("tag_index", value), cip_contract, tmp_path)
    assert _invalid_tags(issues) == []


@pytest.mark.parametrize("value", ["GBR", "GBR.id", "SHI.id", "ISL"])
def test_invalid_uppercase_tag_is_flagged(tmp_path, cip_contract, value):
    """An uppercase literal that is neither a tag nor an alias is a typo."""
    issues = _issues(_tag_body("influence_target", value), cip_contract, tmp_path)
    flagged = _invalid_tags(issues)
    assert len(flagged) == 1
    assert "influence_target" in flagged[0]


def test_miscased_tag_is_flagged(tmp_path, cip_contract):
    """CHl (lowercase l) is a typo for CHI; tags are case-sensitive at runtime."""
    issues = _issues(_tag_body("influence_target", "CHl"), cip_contract, tmp_path)
    flagged = _invalid_tags(issues)
    assert len(flagged) == 1
    assert "CHl" in flagged[0]


def test_invalid_tag_placeholder_TAG_is_flagged(tmp_path, cip_contract):
    """The literal `TAG` placeholder is not a real tag."""
    issues = _issues(_tag_body("influence_target", "TAG"), cip_contract, tmp_path)
    assert len(_invalid_tags(issues)) == 1


# --- contract auto-discovery ----------------------------------------------


def test_contract_parser_raises_for_an_unreadable_file(tmp_path):
    with pytest.raises(OSError):
        vsp._parse_effect_contracts_from_file(str(tmp_path / "gone.txt"))


def test_contract_parser_skips_blank_and_separator_comment_lines(tmp_path):
    path = tmp_path / "common" / "scripted_effects" / "spaced.txt"
    _write(
        path,
        "# Parameters:\n"
        "#\n"
        "# -----\n"
        "# - first_param: the required one\n"
        "# - second_param: optional, defaults to 0\n"
        "spaced_effect = {\n}\n",
    )

    assert vsp._parse_effect_contracts_from_file(str(path)) == {
        "spaced_effect": {"required": ["first_param"], "optional": ["second_param"]}
    }


def test_contract_parser_reads_set_temp_variable_examples(tmp_path):
    """The corpus documents params as call examples as well as `- name:` bullets."""
    path = tmp_path / "common" / "scripted_effects" / "documented.txt"
    _write(
        path,
        "# Parameters:\n"
        "#   set_temp_variable = { required_one = 5 }\n"
        "#   set_temp_variable = { optional_one = 5 } (optional)\n"
        "\n"
        "documented_effect = {\n}\n",
    )

    assert vsp._parse_effect_contracts_from_file(str(path)) == {
        "documented_effect": {
            "required": ["required_one"],
            "optional": ["optional_one"],
        }
    }


def test_contract_parser_ignores_prose_and_skip_words(tmp_path):
    """`# - note: ...` and free prose are documentation, not parameters."""
    path = tmp_path / "common" / "scripted_effects" / "prose.txt"
    _write(
        path,
        "# Parameters:\n"
        "# See the block above\n"
        "# - note: nothing to pass\n"
        "prose_effect = {\n}\n",
    )

    assert vsp._parse_effect_contracts_from_file(str(path)) == {}


def test_contract_parser_never_shadows_a_hardcoded_contract(tmp_path):
    """A doc block on a hardcoded effect must not replace the curated contract."""
    path = tmp_path / "common" / "scripted_effects" / "influence.txt"
    _write(
        path,
        "# Parameters:\n"
        "# - percent_change: how much\n"
        "# - tag_index: the influencer\n"
        "change_influence_percentage = {\n}\n",
    )

    assert vsp._parse_effect_contracts_from_file(str(path)) == {}


def test_contract_parser_tolerates_a_parameter_block_at_end_of_file(tmp_path):
    path = tmp_path / "common" / "scripted_effects" / "dangling.txt"
    _write(path, "# Parameters:\n# - dangling_param: no definition follows\n")

    assert vsp._parse_effect_contracts_from_file(str(path)) == {}


def test_discovered_contract_with_only_optional_params_is_not_registered(tmp_path):
    """A contract with no required param has nothing to enforce at call sites."""
    _write(
        tmp_path / "common" / "scripted_effects" / "optional_only.txt",
        "# Parameters:\n"
        "# - maybe_param: optional switch\n"
        "optional_only_effect = {\n}\n",
    )

    validator = vsp.Validator(str(tmp_path), use_colors=False, workers=1)
    validator._build_contracts()

    assert "optional_only_effect" not in validator._contracts


# --- country tag / alias loading ------------------------------------------


def test_tag_set_accepts_both_country_tags_and_aliases(tmp_path):
    _write(
        tmp_path / "common" / "country_tags" / "00_countries.txt",
        "# Country tags\n"
        '\nUSA = "countries/USA.txt"\nGER = "countries/Germany.txt"\n',
    )
    _write(
        tmp_path / "common" / "country_tag_aliases" / "00_aliases.txt",
        "STC = {\n\toriginal_tag = YEM\n}\n",
    )

    assert vsp._load_valid_country_tags(str(tmp_path)) == (
        frozenset({"USA", "GER", "STC"}),
        [],
    )


def test_tag_set_reports_unreadable_entries(tmp_path):
    """A directory sitting where a .txt is expected must not abort the scan."""
    _write(
        tmp_path / "common" / "country_tags" / "00_countries.txt",
        'USA = "countries/USA.txt"\n',
    )
    (tmp_path / "common" / "country_tags" / "broken.txt").mkdir()
    (tmp_path / "common" / "country_tag_aliases").mkdir(parents=True)
    (tmp_path / "common" / "country_tag_aliases" / "broken.txt").mkdir()

    valid, unreadable = vsp._load_valid_country_tags(str(tmp_path))

    assert valid == frozenset({"USA"})
    assert len(unreadable) == 2
    assert all("cannot read file" in message for message in unreadable)


# --- call-site scanning edge cases ----------------------------------------


def test_hash_inside_a_quoted_log_does_not_swallow_the_call(tmp_path, cip_contract):
    """A `#` inside quotes is not a comment."""
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        '        log = "influence # 1"\n'
        "        set_temp_variable = { percent_change = 5 }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    assert _issues(body, cip_contract, tmp_path) == []


def test_empty_set_temp_variable_block_sets_no_parameter(tmp_path, cip_contract):
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = {\n"
        "        }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any(
        category == "missing-required-param" and "percent_change" in message
        for category, message in issues
    )


def test_call_to_an_uncontracted_effect_is_ignored(tmp_path, cip_contract):
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        some_other_effect = yes\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    assert _issues(body, cip_contract, tmp_path) == []


def test_file_naming_no_contracted_effect_is_skipped(tmp_path, cip_contract):
    body = "shared_focus = {\n    completion_reward = { add_stability = 0.05 }\n}\n"
    assert _issues(body, cip_contract, tmp_path) == []


def test_unreadable_caller_file_is_reported(tmp_path, cip_contract):
    path = tmp_path / "common" / "national_focus" / "test_focus.txt"
    path.mkdir(parents=True)

    results = _validate_call_sites_in_file(
        (str(path), cip_contract, str(tmp_path), frozenset(), frozenset())
    )

    assert [category for category, _message, _line in results] == ["unreadable-input"]


def test_stray_close_brace_does_not_desync_scope_tracking(tmp_path, cip_contract):
    """An extra `}` at root must not pop the root frame and lose every temp var."""
    body = (
        "}\n"
        "shared_focus = {\n"
        "    completion_reward = {\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n"
    )
    assert _issues(body, cip_contract, tmp_path) == []


@pytest.mark.parametrize("block", sorted(vsp.EFFECT_BLOCK_KEYWORDS))
def test_temp_variable_does_not_leak_into_the_next_effect_block(
    tmp_path, cip_contract, block
):
    body = (
        "container = {\n"
        f"    {block} = {{ set_temp_variable = {{ percent_change = 5 }} }}\n"
        f"    {block} = {{ change_influence_percentage = yes }}\n"
        "}\n"
    )
    issues = _issues(body, cip_contract, tmp_path)
    assert any(
        category == "missing-required-param" and "percent_change" in message
        for category, message in issues
    )


def test_numeric_scope_close_does_not_end_the_effect_block(tmp_path, cip_contract):
    body = (
        "shared_focus = { completion_reward = { "
        "set_temp_variable = { percent_change = 5 } "
        "741 = { add_extra_state_shared_building_slots = 1 } "
        "change_influence_percentage = yes } }\n"
    )
    assert _issues(body, cip_contract, tmp_path) == []


def test_temp_opinion_set_by_an_earlier_focus_does_not_hide_temp_change(tmp_path):
    """Regression for #5122: five GENERIC_ agriculture rewards set temp_change."""
    _write(
        tmp_path / "common" / "scripted_effects" / "test_effect.txt",
        "# Parameters:\n"
        "# - temp_opinion: signed opinion change\n"
        "change_farmers_opinion = {\n}\n",
    )
    agriculture_focus = (
        "\tfocus = {\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tset_temp_variable = { temp_change = 3 }\n"
        "\t\t\tchange_farmers_opinion = yes\n"
        "\t\t}\n"
        "\t}\n"
    )
    _write(
        tmp_path / "common" / "national_focus" / "00_generic.txt",
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tset_temp_variable = { temp_opinion = 10 }\n"
        "\t\t\tchange_farmers_opinion = yes\n"
        "\t\t}\n"
        "\t}\n" + agriculture_focus * 5 + "}\n",
    )

    issues = _missing_required_param_issues(tmp_path)
    assert [issue.line for issue in issues] == [11, 17, 23, 29, 35]
    assert all("'temp_opinion'" in issue.message for issue in issues)


# --- quote, comment and unreadable-input handling (#5184) ------------------

_AMOUNT_CONTRACT = {"test_effect": {"required": ["amount"], "optional": []}}

_MISSING = "missing-required-param"
_SHARED = "call-shares-line"

# name -> (script, expected (category, line) findings in order)
_SEMANTIC_FIXTURES = {
    "quoted_call": ('option = {\n\tlog = "test_effect = yes"\n}\n', []),
    "quoted_set_temp": (
        'option = {\n\tlog = "set_temp_variable = { amount = 1 }"\n'
        "\ttest_effect = yes\n}\n",
        [(_MISSING, 3)],
    ),
    "quoted_hash_same_line": (
        'option = {\n\tlog = "# text" test_effect = yes\n}\n',
        [(_SHARED, 2), (_MISSING, 2)],
    ),
    "escaped_quote_before_hash": (
        'option = {\n\tlog = "a \\" # b" test_effect = yes\n}\n',
        [(_SHARED, 2), (_MISSING, 2)],
    ),
    "escaped_quote_then_comment": (
        'option = {\n\tlog = "a \\" b" # test_effect = yes\n\ttest_effect = yes\n}\n',
        [(_MISSING, 3)],
    ),
    "quoted_braces": (
        "option = {\n\tset_temp_variable = { amount = 1 }\n"
        '\tlog = "} } {"\n\ttest_effect = yes\n}\n',
        [],
    ),
    "commented_set_temp": (
        "option = {\n\t# set_temp_variable = { amount = 1 }\n\ttest_effect = yes\n}\n",
        [(_MISSING, 3)],
    ),
    "trailing_comment_call": (
        "option = {\n\tadd_stability = 0.05 # test_effect = yes\n}\n",
        [],
    ),
    "trailing_comment_after_call": (
        "option = {\n\ttest_effect = yes # needs amount\n}\n",
        [(_MISSING, 2)],
    ),
    "multiline_set_temp": (
        "option = {\n\tset_temp_variable = {\n\t\tamount = 1\n\t}\n"
        "\ttest_effect = yes\n}\n",
        [],
    ),
    "multiline_other_set_temp": (
        "option = {\n\tset_temp_variable = {\n\t\tother = 1\n\t}\n"
        "\ttest_effect = yes\n}\n",
        [(_MISSING, 5)],
    ),
    "multiline_string": (
        'option = {\n\tlog = "first\n\ttest_effect = yes"\n\ttest_effect = yes\n}\n',
        [(_MISSING, 4)],
    ),
    "bom_crlf": (
        '\N{ZERO WIDTH NO-BREAK SPACE}option = {\r\n\tlog = "# x"\r\n'
        "\ttest_effect = yes\r\n}\r\n",
        [(_MISSING, 3)],
    ),
    "truncated_block": ("option = {\n\ttest_effect = yes", [(_MISSING, 2)]),
    "truncated_string": (
        'option = {\n\ttest_effect = yes\n\tlog = "test_effect = yes',
        [(_MISSING, 2)],
    ),
    "packed_block": (
        "option = { set_temp_variable = { amount = 1 } test_effect = yes }\n",
        [(_SHARED, 1)],
    ),
    "two_calls_one_line": (
        "option = {\n\tset_temp_variable = { amount = 1 }\n"
        "\ttest_effect = yes test_effect = yes\n}\n",
        [(_SHARED, 3)],
    ),
    "weighted_wrapper": ("25 = { test_effect = yes }\n", [(_MISSING, 1)]),
    "wrapper_with_comment": (
        'hidden_effect = { test_effect = yes } # " } test_effect = yes\n',
        [(_MISSING, 1)],
    ),
    "nested_wrapper": (
        "hidden_effect = { ROOT = { test_effect = yes } }\n",
        [(_MISSING, 1)],
    ),
    "closing_brace": ("option = {\ntest_effect = yes }\n", [(_MISSING, 2)]),
    "call_before_setter": (
        "option = { test_effect = yes set_temp_variable = { amount = 1 } }\n",
        [(_SHARED, 1), (_MISSING, 1)],
    ),
    "inline_limit": (
        "if = { limit = { always = yes } test_effect = yes }\n",
        [(_SHARED, 1), (_MISSING, 1)],
    ),
    "empty_sibling": (
        "test_effect = yes hidden_effect = { }\n",
        [(_SHARED, 1), (_MISSING, 1)],
    ),
}


@pytest.mark.parametrize("fixture", sorted(_SEMANTIC_FIXTURES))
def test_semantic_fixture_agrees_uncached_cold_and_warm(tmp_path, monkeypatch, fixture):
    script, expected = _SEMANTIC_FIXTURES[fixture]
    path = tmp_path / "events" / "fixture.txt"
    _write(path, script)
    args = (str(path), _AMOUNT_CONTRACT, str(tmp_path), frozenset(), frozenset())

    monkeypatch.setenv("MD_NO_CACHE", "1")
    uncached = _validate_call_sites_in_file(args)
    monkeypatch.delenv("MD_NO_CACHE")
    cold = _validate_call_sites_in_file(args)
    # A warm run must reuse the cached tokens.
    monkeypatch.delattr(vsp, "_tokenize")
    warm = _validate_call_sites_in_file(args)

    assert uncached == cold == warm
    assert [(category, line) for category, _message, line in uncached] == expected


@pytest.mark.parametrize("audit", [False, True])
def test_shared_line_calls_gate_and_audit_additions_only_warn(tmp_path, audit):
    _write(
        tmp_path / "common" / "scripted_effects" / "effects.txt",
        "# Parameters:\n# - amount: how much\ntest_effect = {\n}\nplain_effect = {\n}\n",
    )
    _write(
        tmp_path / "events" / "caller.txt",
        "option = {\n"
        "\tset_temp_variable = { amount = 1 } test_effect = yes\n"
        "\tif = { limit = { always = yes } plain_effect = yes }\n"
        "\tplain_effect = yes\n"
        "}\n",
    )

    validator = vsp.Validator(
        str(tmp_path), use_colors=False, workers=1, audit_shared_lines=audit
    )
    validator.run_validations()

    expected = [(_SHARED, vsp.Severity.ERROR, 2)]
    if audit:
        expected.append(("audit-call-shares-line", vsp.Severity.WARNING, 3))
    assert [
        (issue.category, issue.severity, issue.line) for issue in validator._issues
    ] == expected
    assert validator.errors_found == 1
    assert validator.warnings_found == int(audit)


@pytest.mark.parametrize(
    "calls",
    [
        "plain_effect = yes test_effect = yes",
        "test_effect = yes plain_effect = yes",
        "test_effect = yes test_effect = yes",
    ],
)
def test_contracted_call_owns_a_mixed_audit_line(tmp_path, calls):
    path = tmp_path / "mixed.txt"
    _write(path, "set_temp_variable = { amount = 1 }\n" + calls + "\n")
    findings = _validate_call_sites_in_file(
        (str(path), _AMOUNT_CONTRACT, str(tmp_path), frozenset(), {"plain_effect"})
    )
    assert [(category, line) for category, _message, line in findings] == [(_SHARED, 2)]
    assert "'test_effect'" in findings[0][1]


@pytest.mark.parametrize("wrapper", ["25", "hidden_effect", "ROOT", "var:target"])
def test_single_leaf_formatter_output_passes_the_call_rule(tmp_path, wrapper):
    block = [f"{wrapper} = {{", "\ttest_effect = yes", "}"]
    rendered = collapse_or_compact(block)
    assert rendered == [f"{wrapper} = {{ test_effect = yes }}"]
    assert collapse_or_compact(rendered) == rendered
    path = tmp_path / "formatted.txt"
    _write(path, "set_temp_variable = { amount = 1 }\n" + rendered[0] + "\n")
    assert (
        _validate_call_sites_in_file(
            (str(path), _AMOUNT_CONTRACT, str(tmp_path), frozenset(), frozenset())
        )
        == []
    )


def test_splitting_statements_preserves_influence_values_and_errors(
    tmp_path, cip_contract
):
    statements = [
        "option = {",
        "set_temp_variable = { percent_change = 2.00 }",
        "set_temp_variable = { tag_index = USA }",
        "set_temp_variable = { influence_target = USA }",
        "change_influence_percentage = yes",
        "set_temp_variable = { tag_index = ZZZ }",
        "change_influence_percentage = yes",
        "}",
    ]
    token_sequences = []
    for separator in (" ", "\n"):
        script = separator.join(statements)
        path = tmp_path / "influence.txt"
        _write(path, script)
        token_sequences.append(
            [(kind, name, rhs) for kind, _line, name, rhs in vsp._tokenize(script)]
        )
        findings = _validate_call_sites_in_file(
            (str(path), cip_contract, str(tmp_path), _TEST_VALID_TAGS, frozenset())
        )
        assert [
            category for category, _message, _line in findings if category != _SHARED
        ] == [
            "identical-influence-params",
            "invalid-influence-tag",
        ]
    assert token_sequences[0] == token_sequences[1]


@pytest.mark.parametrize("audit", [False, True])
@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize(
    "script, fails",
    [
        ("hidden_effect = { plain_effect = yes }", False),
        ("plain_effect = yes add_stability = 0.1", False),
        (
            "set_temp_variable = { amount = 1 }\n"
            "test_effect = yes add_stability = 0.1",
            True,
        ),
        (
            "set_temp_variable = { amount = 1 }\n"
            "hidden_effect = { test_effect = yes }",
            False,
        ),
        ("test_effect = yes", True),
    ],
)
def test_cli_keeps_audit_advisory_without_weakening_errors(
    tmp_path, monkeypatch, audit, strict, script, fails
):
    _write(
        tmp_path / "common" / "scripted_effects" / "contracts.txt",
        "# Parameters:\n# - amount: required\ntest_effect = { }\nplain_effect = { }\n",
    )
    _write(tmp_path / "events" / "calls.txt", script + "\n")
    argv = [vsp.__file__, "--path", str(tmp_path), "--workers", "1", "--no-color"]
    if audit:
        argv.append("--audit-shared-lines")
    if strict:
        argv.append("--strict")
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(vsp.__file__, run_name="__main__")
    assert exit_info.value.code == int(strict and fails)


def test_validator_reports_every_unreadable_input_as_an_error(tmp_path):
    """Invalid UTF-8 after a real call used to return no findings."""
    for relative in (
        "common/scripted_effects/broken.txt",
        "common/country_tags/broken.txt",
        "events/broken.txt",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(b"option = {\n\tchange_influence_percentage = yes\n}\n\xff\n")

    validator = vsp.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    assert [(issue.category, issue.file) for issue in validator._issues] == [
        ("unreadable-input", "common/country_tags/broken.txt"),
        ("unreadable-input", "common/scripted_effects/broken.txt"),
        ("unreadable-input", "events/broken.txt"),
    ]
    assert validator.errors_found == 3


# --- validator wiring ------------------------------------------------------


def test_validate_callers_without_contracts_scans_nothing(tmp_path, monkeypatch):
    """An empty registry short-circuits before the file scan."""
    _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "shared_focus = { completion_reward = { change_influence_percentage = yes } }\n",
    )
    validator = vsp.Validator(str(tmp_path), use_colors=False, workers=1)
    logged = []
    monkeypatch.setattr(validator, "log", lambda msg, *a, **k: logged.append(msg))

    validator._validate_callers()

    assert validator._issues == []
    assert any("No contracts found" in line for line in logged)


def test_validator_routes_identical_and_invalid_tag_findings(tmp_path):
    """Both influence-specific categories reach the report, not just the param one."""
    _write(
        tmp_path / "common" / "country_tags" / "00_countries.txt",
        'USA = "countries/USA.txt"\n',
    )
    _write(
        tmp_path / "events" / "test_events.txt",
        "country_event = {\n"
        "    id = test.1\n"
        "    option = {\n"
        "        name = test.1.a\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { tag_index = USA }\n"
        "        set_temp_variable = { influence_target = USA.id }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "    option = {\n"
        "        name = test.1.b\n"
        "        set_temp_variable = { percent_change = 5 }\n"
        "        set_temp_variable = { influence_target = ZZZ }\n"
        "        change_influence_percentage = yes\n"
        "    }\n"
        "}\n",
    )

    validator = vsp.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    assert sorted({issue.category for issue in validator._issues}) == [
        "identical-influence-params",
        "invalid-influence-tag",
    ]


def test_cli_entry_point_exits_zero_on_a_clean_tree(tmp_path, monkeypatch):
    _write(
        tmp_path / "common" / "country_tags" / "00_countries.txt",
        'USA = "countries/USA.txt"\n',
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [vsp.__file__, "--path", str(tmp_path), "--workers", "1", "--no-color"],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(vsp.__file__, run_name="__main__")

    assert exit_info.value.code == 0


# --- staged dependency rescans (#5185) -------------------------------------

_EFFECT_FILE = "common/scripted_effects/e.txt"
_TAG_FILE = "common/country_tags/00_countries.txt"
_ALIAS_FILE = "common/country_tag_aliases/aliases.txt"
_REQUIRES_AMOUNT = "# Parameters:\n# - amount: how much\ntest_effect = {\n}\n"
_BARE_CALL = "option = {\n\ttest_effect = yes\n}\n"
_INFLUENCE_CALL = (
    "option = {\n"
    "\tset_temp_variable = { percent_change = 5 }\n"
    "\tset_temp_variable = { influence_target = ZZZ }\n"
    "\tchange_influence_percentage = yes\n"
    "}\n"
)


def _committed_tree(tmp_path, monkeypatch, files):
    """Commit `files` as the base of a git repository at tmp_path."""
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "MD_STAGED_FILES"):
        monkeypatch.delenv(name, raising=False)
    for relative, content in files.items():
        _write(tmp_path / relative, content)
    initialize_git_repository(tmp_path, *files)


def _stage(tmp_path, relative, content):
    """Stage new content for a file, or its deletion when content is None."""
    if content is None:
        run_git(tmp_path, "rm", relative)
        return
    _write(tmp_path / relative, content)
    run_git(tmp_path, "add", relative)


def _cli_findings(tmp_path, monkeypatch, *flags):
    """Run the CLI on tmp_path and return each finding as (category, file, line)."""
    output = tmp_path / "result.log"
    argv = [vsp.__file__, "--path", str(tmp_path), "--workers", "1", "--no-color"]
    monkeypatch.setattr(sys, "argv", [*argv, "--output", str(output), *flags])
    with pytest.raises(SystemExit):
        runpy.run_path(vsp.__file__, run_name="__main__")
    with open(output.with_suffix(".json"), encoding="utf-8") as sidecar:
        return sorted(
            (issue["category"], issue["file"], issue["line"])
            for issue in json.load(sidecar)
        )


def test_staged_contract_change_rechecks_unchanged_callers(tmp_path, monkeypatch):
    """Staging only the contract used to report nothing for its callers."""
    _committed_tree(
        tmp_path,
        monkeypatch,
        {_EFFECT_FILE: "test_effect = {\n}\n", "events/e.txt": _BARE_CALL},
    )
    _stage(tmp_path, _EFFECT_FILE, _REQUIRES_AMOUNT)
    cache = tmp_path / ".validation_cache"

    full = _cli_findings(tmp_path, monkeypatch, "--no-cache")
    uncached = _cli_findings(tmp_path, monkeypatch, "--staged", "--no-cache")
    assert not cache.exists()
    monkeypatch.delenv("MD_NO_CACHE")
    cold = _cli_findings(tmp_path, monkeypatch, "--staged")
    assert cache.exists()
    warm = _cli_findings(tmp_path, monkeypatch, "--staged")

    assert full == uncached == cold == warm == [(_MISSING, "events/e.txt", 2)]


def test_staged_contract_removal_leaves_no_stale_warm_findings(tmp_path, monkeypatch):
    """The rescan still runs, so findings from other contracts stay."""
    _committed_tree(
        tmp_path,
        monkeypatch,
        {
            _EFFECT_FILE: _REQUIRES_AMOUNT,
            "events/e.txt": _BARE_CALL,
            "events/kept.txt": "option = {\n\tchange_influence_percentage = yes\n}\n",
        },
    )
    kept = (_MISSING, "events/kept.txt", 2)
    assert _cli_findings(tmp_path, monkeypatch) == [(_MISSING, "events/e.txt", 2), kept]

    _stage(tmp_path, _EFFECT_FILE, None)

    assert _cli_findings(tmp_path, monkeypatch, "--staged") == [kept]


@pytest.mark.parametrize(
    "dependency, base, staged",
    [
        (_TAG_FILE, 'ZZZ = "countries/ZZZ.txt"\n', 'ZZY = "countries/ZZZ.txt"\n'),
        (_TAG_FILE, 'ZZZ = "countries/ZZZ.txt"\n', None),
        (_ALIAS_FILE, "ZZZ = {\n}\n", "ZZY = {\n}\n"),
        (_ALIAS_FILE, "ZZZ = {\n}\n", None),
    ],
    ids=["tag-renamed", "tag-file-deleted", "alias-renamed", "alias-file-deleted"],
)
def test_staged_tag_or_alias_change_rechecks_unchanged_callers(
    tmp_path, monkeypatch, dependency, base, staged
):
    _committed_tree(
        tmp_path, monkeypatch, {dependency: base, "events/e.txt": _INFLUENCE_CALL}
    )
    assert _cli_findings(tmp_path, monkeypatch) == []

    _stage(tmp_path, dependency, staged)

    assert _cli_findings(tmp_path, monkeypatch, "--staged") == [
        ("invalid-influence-tag", "events/e.txt", 3)
    ]


def test_staged_caller_edit_scans_only_that_caller(tmp_path, monkeypatch):
    """No dependency changed, so unchanged and deleted callers are left alone."""
    _committed_tree(
        tmp_path,
        monkeypatch,
        {
            _EFFECT_FILE: _REQUIRES_AMOUNT,
            "events/changed.txt": _BARE_CALL,
            "events/unchanged.txt": _BARE_CALL,
            "events/removed.txt": _BARE_CALL,
        },
    )
    _stage(tmp_path, "events/changed.txt", "\n" + _BARE_CALL)
    _stage(tmp_path, "events/removed.txt", None)

    assert _cli_findings(tmp_path, monkeypatch, "--staged") == [
        (_MISSING, "events/changed.txt", 3)
    ]
