"""Tests for the category-lock tag/original_tag redundancy check (Check D).

_find_category_redundant_rows fills the gap between validate_redundant_tag_checks
(decision's own allowed pin vs its own visible/available) and
validate_allowed_redundant_with_category (sole-content allowed duplicating the
category pin): neither compares the *category*'s single-tag lock against a
decision's visible/available, or against a partial (multi-condition) allowed
block.
"""

from validate_decisions import DecisionFactory, _find_category_redundant_rows


def _make_factory(
    token, allowed=None, available=None, visible=None, basename="test.txt"
):
    """Build a DecisionFactory for a single decision block with the given
    (inner, brace-free) allowed/available/visible content."""
    lines = [f"\t{token} = {{"]
    for field, content in (
        ("allowed", allowed),
        ("available", available),
        ("visible", visible),
    ):
        if content is None:
            continue
        lines.append(f"\t\t{field} = {{")
        for line in content.strip("\n").split("\n"):
            lines.append(f"\t\t\t{line}")
        lines.append("\t\t}")
    lines.append("\t}")
    raw = "\n".join(lines) + "\n"
    return DecisionFactory(dec=raw, source_basename=basename)


CAT = "some_category"


def test_original_tag_lock_flags_original_tag_recheck():
    factories = [_make_factory("dec1", available="original_tag = GER")]
    cat_pins = {CAT: {("original_tag", "GER")}}
    cats_with_decs = {CAT: ["dec1"]}

    rows = _find_category_redundant_rows(factories, cat_pins, cats_with_decs)

    assert len(rows) == 1
    assert "dec1" in rows[0]
    assert "available" in rows[0]


def test_original_tag_lock_does_not_flag_tag_recheck():
    # original_tag lock admits civil-war split-offs; a runtime `tag` check is
    # a real restriction, not a redundant re-check.
    factories = [_make_factory("dec1", available="tag = GER")]
    cat_pins = {CAT: {("original_tag", "GER")}}
    cats_with_decs = {CAT: ["dec1"]}

    assert _find_category_redundant_rows(factories, cat_pins, cats_with_decs) == []


def test_tag_lock_flags_both_tag_and_original_tag_recheck():
    factories = [
        _make_factory("dec_tag_recheck", available="tag = GER"),
        _make_factory("dec_origtag_recheck", visible="original_tag = GER"),
    ]
    cat_pins = {CAT: {("tag", "GER")}}
    cats_with_decs = {CAT: ["dec_tag_recheck", "dec_origtag_recheck"]}

    rows = _find_category_redundant_rows(factories, cat_pins, cats_with_decs)

    assert len(rows) == 2
    joined = "\n".join(rows)
    assert "dec_tag_recheck" in joined
    assert "dec_origtag_recheck" in joined


def test_not_wrapped_recheck_skipped():
    factories = [_make_factory("dec1", available="NOT = {\n\toriginal_tag = GER\n}")]
    cat_pins = {CAT: {("original_tag", "GER")}}
    cats_with_decs = {CAT: ["dec1"]}

    assert _find_category_redundant_rows(factories, cat_pins, cats_with_decs) == []


def test_from_wrapped_recheck_skipped():
    factories = [_make_factory("dec1", available="FROM = {\n\toriginal_tag = GER\n}")]
    cat_pins = {CAT: {("original_tag", "GER")}}
    cats_with_decs = {CAT: ["dec1"]}

    assert _find_category_redundant_rows(factories, cat_pins, cats_with_decs) == []


def test_multi_tag_lock_skipped():
    # Category pins two different tag values at depth 0 - not a single-tag
    # lock, so a decision's own single-tag check is narrowing, not redundant.
    factories = [_make_factory("dec1", available="original_tag = GER")]
    cat_pins = {CAT: {("original_tag", "GER"), ("original_tag", "ITA")}}
    cats_with_decs = {CAT: ["dec1"]}

    assert _find_category_redundant_rows(factories, cat_pins, cats_with_decs) == []


def test_scripted_trigger_category_no_lock_skipped():
    # A scripted-trigger allowed (e.g. has_country_flag = x) has no flat tag
    # pin, so _category_allowed_pins maps it to an empty set - no lock.
    factories = [_make_factory("dec1", available="original_tag = GER")]
    cat_pins = {CAT: set()}
    cats_with_decs = {CAT: ["dec1"]}

    assert _find_category_redundant_rows(factories, cat_pins, cats_with_decs) == []


def test_sole_pin_allowed_skipped():
    # allowed's only content is the pin itself - already owned by
    # validate_allowed_redundant_with_category; must not be double-reported.
    factories = [_make_factory("dec1", allowed="original_tag = GER")]
    cat_pins = {CAT: {("original_tag", "GER")}}
    cats_with_decs = {CAT: ["dec1"]}

    assert _find_category_redundant_rows(factories, cat_pins, cats_with_decs) == []


def test_ger_territorial_defense_shape_flagged():
    # Mirrors common/decisions/Germany.txt:1956-1965: category
    # GER_V_fall_Decision is locked to `original_tag = GER`
    # (common/decisions/categories/99_GER_decision_categories.txt:96-100), and
    # GER_Territorial_Defense re-checks it in `available` with no `allowed`
    # at all, so the sole-pin-allowed exemption doesn't apply.
    factories = [
        _make_factory(
            "GER_Territorial_Defense",
            available="original_tag = GER",
            visible="has_country_flag = GER_V_fall",
        )
    ]
    cat_pins = {"GER_V_fall_Decision": {("original_tag", "GER")}}
    cats_with_decs = {"GER_V_fall_Decision": ["GER_Territorial_Defense"]}

    rows = _find_category_redundant_rows(factories, cat_pins, cats_with_decs)

    assert len(rows) == 1
    assert "GER_Territorial_Defense" in rows[0]
    assert "available" in rows[0]
