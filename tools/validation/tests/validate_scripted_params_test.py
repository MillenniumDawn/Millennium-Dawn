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

import pytest
import validate_scripted_params as vsp
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


def _issues(caller_body, contracts, mod_path, valid_tags=_TEST_VALID_TAGS):
    """Run the per-file validator against a one-shot focus file."""
    focus_dir = mod_path / "common" / "national_focus"
    focus_dir.mkdir(parents=True, exist_ok=True)
    fpath = focus_dir / "test_focus.txt"
    fpath.write_text(caller_body, encoding="utf-8-sig")
    results = _validate_call_sites_in_file(
        (str(fpath), contracts, str(mod_path), frozenset(valid_tags))
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

    The validator's frame-based scope tracking keeps a temp var from a
    previous focus's completion_reward visible to the current call, even
    though it wouldn't be in scope at runtime.  Tagging a stale
    `tag_index` from 25+ lines back as identical to the current
    `influence_target` would create noise; the proximity window prevents
    that.
    """
    body = (
        "shared_focus = {\n"
        "    completion_reward = {\n"
        # Stale tag_index, 25+ lines back from the call.  At runtime this
        # would NOT be in scope (different focus's completion_reward),
        # but the validator's scope tracking is too coarse to know that.
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
