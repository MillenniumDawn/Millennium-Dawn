"""Tests for the unannounced decision category check.

A category gated on state that flips during play appears part-way through a
game. Unless something calls `unlock_decision_category_tooltip` (or
`unlock_decision_tooltip` on one of its decisions), a whole tab of decisions
shows up with no indication of where it came from.
"""

import validate_decisions as V


def _write_mod(tmp_path, category_visible, unlock=None):
    categories = tmp_path / "common" / "decisions" / "categories"
    categories.mkdir(parents=True)
    with (categories / "cat.txt").open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "md_test_category = {\n"
            "\ticon = GFX_decision_generic\n"
            f"{category_visible}"
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
    if unlock:
        focus = tmp_path / "common" / "national_focus"
        focus.mkdir(parents=True)
        with (focus / "test.txt").open("w", encoding="utf-8", newline="") as handle:
            handle.write(
                "focus = {\n"
                "\tid = md_test_focus\n"
                f"\tcompletion_reward = {{\n\t\t{unlock}\n\t}}\n"
                "}\n"
            )
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


_FLAG_GATE = "\tvisible = {\n\t\thas_country_flag = md_test_flag\n\t}\n"


def _findings(validator):
    return validator._unannounced_categories()


def test_check_is_opt_in(tmp_path):
    # 118 existing cases in the mod, so it must not gate ordinary work.
    validator = _write_mod(tmp_path, _FLAG_GATE)
    assert validator.unannounced_categories is False
    assert (
        V.Validator(
            mod_path=str(tmp_path),
            use_colors=False,
            workers=1,
            unannounced_categories=True,
        ).unannounced_categories
        is True
    )


def test_flag_gated_category_without_announcement_is_flagged(tmp_path):
    out = _findings(_write_mod(tmp_path, _FLAG_GATE))
    assert len(out) == 1
    assert "md_test_category" in out[0]
    assert "has_country_flag = md_test_flag" in out[0]


def test_category_announced_by_focus_is_not_flagged(tmp_path):
    validator = _write_mod(
        tmp_path,
        _FLAG_GATE,
        unlock="unlock_decision_category_tooltip = md_test_category",
    )
    assert _findings(validator) == []


def test_category_whose_decision_is_announced_is_not_flagged(tmp_path):
    validator = _write_mod(
        tmp_path, _FLAG_GATE, unlock="unlock_decision_tooltip = md_test_decision"
    )
    assert _findings(validator) == []


def test_category_with_no_visible_block_is_not_flagged(tmp_path):
    assert _findings(_write_mod(tmp_path, "")) == []


def test_tag_gated_category_is_not_flagged(tmp_path):
    # On from the first day for that country, so there is nothing to announce.
    gate = "\tvisible = {\n\t\toriginal_tag = JAP\n\t}\n"
    assert _findings(_write_mod(tmp_path, gate)) == []


def test_ai_only_category_is_not_flagged(tmp_path):
    gate = "\tvisible = {\n\t\tis_ai = yes\n\t\thas_country_flag = md_test_flag\n\t}\n"
    assert _findings(_write_mod(tmp_path, gate)) == []


def test_focus_gated_category_is_flagged(tmp_path):
    gate = "\tvisible = {\n\t\thas_completed_focus = md_other_focus\n\t}\n"
    out = _findings(_write_mod(tmp_path, gate))
    assert len(out) == 1
    assert "has_completed_focus = md_other_focus" in out[0]
