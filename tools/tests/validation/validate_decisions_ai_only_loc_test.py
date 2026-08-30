"""Tests for the AI-only decision localisation checks.

An AI-only decision is hidden from every human player, so it needs no
localisation and must not carry any. The check runs in both directions, and
covers AI-only decision categories as well as the decisions inside them.
"""

import validate_decisions as V
from shared.suite import decision_factory, fake_decisions_validator


def _results_for(
    factories,
    loc_keys,
    monkeypatch,
    ai_only_by_category=(),
    ai_only_categories=(),
    unlocked_categories=(),
):
    validator = fake_decisions_validator("/tmp")
    monkeypatch.setattr(
        V, "parse_all_decision_factories", lambda mod_path, lowercase=False: factories
    )
    monkeypatch.setattr(V, "_load_scripted_localisation_keys", lambda mod_path: set())
    monkeypatch.setattr(V, "_category_source_basenames", lambda mod_path, names: {})
    monkeypatch.setattr(
        validator, "_load_localisation_keys", lambda: set(loc_keys), raising=False
    )
    monkeypatch.setattr(
        validator,
        "_get_ai_only_by_category",
        lambda: set(ai_only_by_category),
        raising=False,
    )
    monkeypatch.setattr(
        validator,
        "_get_ai_only_categories",
        lambda: set(ai_only_categories),
        raising=False,
    )
    monkeypatch.setattr(
        validator,
        "_get_unlocked_categories",
        lambda: set(unlocked_categories),
        raising=False,
    )
    validator.validate_missing_localisation()
    return validator.collected


# --- _has_flat_is_ai ---------------------------------------------------------


def test_flat_is_ai_detected():
    assert V._has_flat_is_ai("{\n\t\t\tis_ai = yes\n\t\t}")


def test_single_line_is_ai_detected():
    assert V._has_flat_is_ai("{ is_ai = yes }")


def test_is_ai_nested_in_or_not_detected():
    assert not V._has_flat_is_ai("{\n\t\t\tOR = {\n\t\t\t\tis_ai = yes\n\t\t\t}\n\t\t}")


def test_is_ai_scoped_to_tag_not_detected():
    assert not V._has_flat_is_ai("{\n\t\t\tGRE = {\n\t\t\t\tis_ai = yes\n\t\t\t}\n\t\t}")


def test_is_ai_in_if_limit_not_detected():
    block = "{\n\t\t\tif = {\n\t\t\t\tlimit = { is_ai = yes }\n\t\t\t}\n\t\t}"
    assert not V._has_flat_is_ai(block)


def test_is_ai_no_not_detected():
    assert not V._has_flat_is_ai("{\n\t\t\tis_ai = no\n\t\t}")


def test_commented_is_ai_not_detected():
    assert not V._has_flat_is_ai("{\n\t\t\t# is_ai = yes\n\t\t}")


def test_is_ai_mid_token_not_detected():
    assert not V._has_flat_is_ai("{\n\t\t\tfoo_is_ai = yes\n\t\t}")


def test_empty_block_not_detected():
    assert not V._has_flat_is_ai("")


# --- DecisionFactory.ai_only -------------------------------------------------


def test_factory_ai_only_from_visible():
    factory = decision_factory(
        "dec_one = {\n\tvisible = {\n\t\tis_ai = yes\n\t}\n}"
    )
    assert factory.ai_only


def test_factory_not_ai_only_when_nested():
    factory = decision_factory(
        "dec_two = {\n\tvisible = {\n\t\tOR = {\n\t\t\tis_ai = yes\n"
        "\t\t\tis_debug = yes\n\t\t}\n\t}\n}"
    )
    assert not factory.ai_only


# --- validate_missing_localisation -------------------------------------------


def test_ai_only_decision_without_loc_not_flagged(monkeypatch):
    factory = decision_factory("dec_one = {\n\tvisible = {\n\t\tis_ai = yes\n\t}\n}")
    assert _results_for([factory], set(), monkeypatch) == []


def test_ai_only_decision_with_loc_flagged(monkeypatch):
    factory = decision_factory("dec_one = {\n\tvisible = {\n\t\tis_ai = yes\n\t}\n}")
    results = _results_for([factory], {"dec_one", "dec_one_desc"}, monkeypatch)
    assert len(results) == 2
    assert all("AI-only decision has localisation key" in r for r in results)
    assert any("'dec_one'" in r for r in results)
    assert any("'dec_one_desc'" in r for r in results)


def test_ai_only_by_category_exempt_from_missing(monkeypatch):
    factory = decision_factory("dec_one = {\n\tcost = 25\n}")
    results = _results_for(
        [factory], set(), monkeypatch, ai_only_by_category={"dec_one"}
    )
    assert results == []


def test_ai_only_by_category_with_loc_flagged(monkeypatch):
    factory = decision_factory("dec_one = {\n\tcost = 25\n}")
    results = _results_for(
        [factory], {"dec_one"}, monkeypatch, ai_only_by_category={"dec_one"}
    )
    assert len(results) == 1
    assert "AI-only decision has localisation key 'dec_one'" in results[0]


def test_ordinary_decision_missing_loc_still_flagged(monkeypatch):
    factory = decision_factory("dec_one = {\n\tcost = 25\n}")
    results = _results_for([factory], set(), monkeypatch)
    assert len(results) == 1
    assert "missing loc key 'dec_one'" in results[0]


def test_ordinary_decision_desc_not_required(monkeypatch):
    factory = decision_factory("dec_one = {\n\tcost = 25\n}")
    assert _results_for([factory], {"dec_one"}, monkeypatch) == []


# --- AI-only categories ------------------------------------------------------


def test_ai_only_category_without_loc_not_flagged(monkeypatch):
    results = _results_for(
        [], set(), monkeypatch, ai_only_categories={"md_test_category"}
    )
    assert results == []


def test_ai_only_category_with_loc_flagged(monkeypatch):
    results = _results_for(
        [],
        {"md_test_category", "md_test_category_desc"},
        monkeypatch,
        ai_only_categories={"md_test_category"},
    )
    assert len(results) == 2
    assert all("AI-only decision category has localisation key" in r for r in results)
    assert any("'md_test_category'" in r for r in results)
    assert any("'md_test_category_desc'" in r for r in results)


def test_unlocked_ai_only_category_not_flagged(monkeypatch):
    """`unlock_decision_category_tooltip` renders the name key to a player."""
    results = _results_for(
        [],
        {"md_test_category"},
        monkeypatch,
        ai_only_categories={"md_test_category"},
        unlocked_categories={"md_test_category"},
    )
    assert results == []


def test_ordinary_category_with_loc_not_flagged(monkeypatch):
    results = _results_for([], {"md_test_category"}, monkeypatch)
    assert results == []


# --- category resolution on a real mod tree ----------------------------------


def _write_mod(tmp_path, category_visible, category_loc=False, unlock_ref=False):
    categories = tmp_path / "common" / "decisions" / "categories"
    categories.mkdir(parents=True)
    with (categories / "cat.txt").open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "md_test_category = {\n"
            "\ticon = GFX_decision_generic\n"
            f"\tvisible = {{\n{category_visible}\n\t}}\n"
            "}\n"
        )
    decisions = tmp_path / "common" / "decisions"
    with (decisions / "dec.txt").open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "md_test_category = {\n"
            "\tmd_test_decision = {\n"
            "\t\ticon = GFX_decision_generic\n"
            "\t\tcost = 25\n"
            "\t}\n"
            "}\n"
        )
    if unlock_ref:
        focus = tmp_path / "common" / "national_focus"
        focus.mkdir(parents=True)
        with (focus / "test.txt").open("w", encoding="utf-8", newline="") as handle:
            handle.write(
                "focus = {\n"
                "\tid = md_test_focus\n"
                "\tcompletion_reward = {\n"
                "\t\tunlock_decision_category_tooltip = md_test_category\n"
                "\t}\n"
                "}\n"
            )
    loc = tmp_path / "localisation" / "english"
    loc.mkdir(parents=True)
    with (loc / "test_l_english.yml").open("w", encoding="utf-8", newline="") as handle:
        handle.write('l_english:\n md_test_decision: "Test"\n')
        if category_loc:
            handle.write(' md_test_category: "Test Category"\n')
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def test_decision_in_ai_only_category_is_ai_only(tmp_path):
    validator = _write_mod(tmp_path, "\t\tis_ai = yes")
    assert validator._get_ai_only_by_category() == {"md_test_decision"}


def test_decision_in_debug_gated_category_is_not_ai_only(tmp_path):
    validator = _write_mod(
        tmp_path, "\t\tOR = {\n\t\t\tis_ai = yes\n\t\t\tis_debug = yes\n\t\t}"
    )
    assert validator._get_ai_only_by_category() == set()


def test_ai_only_category_loc_reported_on_real_validator(tmp_path):
    validator = _write_mod(tmp_path, "\t\tis_ai = yes")
    validator.validate_missing_localisation()
    assert validator.warnings_found >= 1


def test_ai_only_category_names_resolved(tmp_path):
    validator = _write_mod(tmp_path, "\t\tis_ai = yes")
    assert validator._get_ai_only_categories() == {"md_test_category"}


def test_category_key_reported_with_source_file(tmp_path):
    validator = _write_mod(tmp_path, "\t\tis_ai = yes")
    assert validator._ai_only_category_loc({"md_test_category"}) == [
        "md_test_category - cat.txt: AI-only decision category has "
        "localisation key 'md_test_category'"
    ]


def test_category_key_exempt_when_unlocked_by_focus(tmp_path):
    validator = _write_mod(tmp_path, "\t\tis_ai = yes", unlock_ref=True)
    assert validator._ai_only_category_loc({"md_test_category"}) == []


def test_category_key_counted_end_to_end(tmp_path):
    """One warning for the decision's key, one for the category's."""
    validator = _write_mod(tmp_path, "\t\tis_ai = yes", category_loc=True)
    validator.validate_missing_localisation()
    assert validator.warnings_found == 2
