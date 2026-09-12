"""Tests for the undefined unlock-tooltip target check (#3961).

`unlock_decision_tooltip` and `unlock_decision_category_tooltip` name the
decision or category something has just unlocked. A typo or a rename leaves the
tooltip naming nothing while the unlock itself still happens. #3957 was the
motivating case: a stale category name produced `Invalid Decision Category` in
error.log. Validation catches the stale reference during CI.
"""

import os

import validate_decisions as V
from shared.suite import write_text

_FOCUS_PATH = os.path.join("common", "national_focus", "test.txt")


def _focus_file(effects):
    return (
        "focus = {\n"
        "\tid = md_test_focus\n"
        "\tcompletion_reward = {\n"
        f"{effects}"
        "\t}\n"
        "}\n"
    )


def _write_mod(tmp_path, effects, *, no_cache=False):
    write_text(
        tmp_path / "common" / "decisions" / "categories" / "cat.txt",
        "md_category = {\n\ticon = GFX_decision_generic\n}\n"
        "md_hyphen-category = {\n\ticon = GFX_decision_generic\n}\n",
    )
    write_text(
        tmp_path / "common" / "decisions" / "dec.txt",
        "md_category = {\n"
        "\tmd_real_decision = {\n"
        "\t\ticon = GFX_decision_generic\n"
        "\t}\n"
        "\tmd_hyphen-decision = {\n"
        "\t\ticon = GFX_decision_generic\n"
        "\t}\n"
        "}\n",
    )
    write_text(
        tmp_path / "common" / "national_focus" / "test.txt",
        _focus_file(effects),
    )
    return V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=no_cache)


def _findings(validator):
    return validator._undefined_unlock_targets()


def test_defined_decision_reference_is_clean(tmp_path):
    validator = _write_mod(tmp_path, "\t\tunlock_decision_tooltip = md_real_decision\n")
    assert _findings(validator) == []


def test_defined_category_reference_is_clean(tmp_path):
    validator = _write_mod(
        tmp_path, "\t\tunlock_decision_category_tooltip = md_category\n"
    )
    assert _findings(validator) == []


def test_undefined_decision_reference_is_flagged(tmp_path):
    validator = _write_mod(tmp_path, "\t\tunlock_decision_tooltip = md_typo\n")

    assert _findings(validator) == [
        (
            "unlock_decision_tooltip = md_typo -> no decision named md_typo is "
            "defined in common/decisions (fix the typo or define it)",
            _FOCUS_PATH,
            4,
        )
    ]


def test_undefined_category_reference_is_flagged(tmp_path):
    # #3957: a decision used where the tooltip needs its category.
    validator = _write_mod(
        tmp_path, "\t\tunlock_decision_category_tooltip = md_real_decision\n"
    )

    message, path, line = _findings(validator)[0]
    assert "unlock_decision_category_tooltip = md_real_decision" in message
    assert "no category named md_real_decision" in message
    assert (path, line) == (_FOCUS_PATH, 4)


def test_decision_reference_naming_a_category_is_flagged(tmp_path):
    validator = _write_mod(tmp_path, "\t\tunlock_decision_tooltip = md_category\n")

    message, _, _ = _findings(validator)[0]
    assert "no decision named md_category" in message


def test_block_form_reference_is_clean(tmp_path):
    validator = _write_mod(
        tmp_path,
        "\t\tunlock_decision_tooltip = {\n"
        "\t\t\tdecision = md_real_decision\n"
        "\t\t\tshow_effect_tooltip = yes\n"
        "\t\t}\n",
    )
    assert _findings(validator) == []


def test_block_form_reference_to_an_undefined_decision_is_flagged(tmp_path):
    validator = _write_mod(
        tmp_path,
        "\t\tunlock_decision_tooltip = {\n"
        "\t\t\tdecision = md_typo\n"
        "\t\t\tshow_effect_tooltip = yes\n"
        "\t\t}\n",
    )
    message, path, line = _findings(validator)[0]
    assert "unlock_decision_tooltip = md_typo" in message
    assert "no decision named md_typo" in message
    assert (path, line) == (_FOCUS_PATH, 4)


def test_hyphenated_decision_reference_is_clean(tmp_path):
    validator = _write_mod(
        tmp_path, "\t\tunlock_decision_tooltip = md_hyphen-decision\n"
    )
    assert _findings(validator) == []


def test_hyphenated_decision_block_form_reference_is_clean(tmp_path):
    validator = _write_mod(
        tmp_path,
        "\t\tunlock_decision_tooltip = {\n"
        "\t\t\tdecision = md_hyphen-decision\n"
        "\t\t\tshow_effect_tooltip = yes\n"
        "\t\t}\n",
    )
    assert _findings(validator) == []


def test_hyphenated_category_reference_is_clean(tmp_path):
    validator = _write_mod(
        tmp_path, "\t\tunlock_decision_category_tooltip = md_hyphen-category\n"
    )
    assert _findings(validator) == []


def test_undefined_hyphenated_decision_reference_is_flagged(tmp_path):
    validator = _write_mod(tmp_path, "\t\tunlock_decision_tooltip = md_hyphen-typo\n")

    assert _findings(validator) == [
        (
            "unlock_decision_tooltip = md_hyphen-typo -> no decision named "
            "md_hyphen-typo is defined in common/decisions (fix the typo or "
            "define it)",
            _FOCUS_PATH,
            4,
        )
    ]


def test_undefined_hyphenated_block_form_reference_is_flagged(tmp_path):
    validator = _write_mod(
        tmp_path,
        "\t\tunlock_decision_tooltip = {\n"
        "\t\t\tdecision = md_hyphen-typo\n"
        "\t\t\tshow_effect_tooltip = yes\n"
        "\t\t}\n",
    )

    message, path, line = _findings(validator)[0]
    assert "no decision named md_hyphen-typo" in message
    assert (path, line) == (_FOCUS_PATH, 4)


def test_undefined_hyphenated_category_reference_is_flagged(tmp_path):
    validator = _write_mod(
        tmp_path, "\t\tunlock_decision_category_tooltip = md_hyphen-catagory\n"
    )

    message, path, line = _findings(validator)[0]
    assert "no category named md_hyphen-catagory" in message
    assert (path, line) == (_FOCUS_PATH, 4)


def test_commented_out_reference_is_ignored(tmp_path):
    validator = _write_mod(
        tmp_path,
        "\t\t# unlock_decision_tooltip = md_typo\n"
        "\t\tunlock_decision_tooltip = md_real_decision  # keep this one\n",
    )
    assert _findings(validator) == []


def test_quoted_string_naming_the_keyword_is_not_a_reference(tmp_path):
    # A quoted log string is text: blank_quoted_strings clears it before the
    # token scan, so a string quoting the effect names no target.
    validator = _write_mod(
        tmp_path,
        '\t\tlog = "[GetDateText]: unlock_decision_tooltip = md_typo"\n',
    )
    assert _findings(validator) == []


def test_quoted_string_naming_the_category_keyword_is_not_a_reference(tmp_path):
    validator = _write_mod(
        tmp_path,
        '\t\tlog = "[GetDateText]: unlock_decision_category_tooltip = md_typo"\n',
    )
    assert _findings(validator) == []


def test_quoted_string_does_not_shift_a_real_reference_line(tmp_path):
    # Blanking must keep offsets, so the line of the reference after it is right.
    validator = _write_mod(
        tmp_path,
        '\t\tlog = "[GetDateText]: unlock_decision_tooltip = md_typo"\n'
        "\t\tunlock_decision_tooltip = md_typo\n",
    )

    assert len(_findings(validator)) == 1
    assert _findings(validator)[0][1:] == (_FOCUS_PATH, 5)


def test_longer_key_around_the_keyword_is_not_a_reference(tmp_path):
    # The `\b` boundary rejects a key with the keyword as its tail, and `\s*= `
    # rejects one with the keyword as its head.
    validator = _write_mod(
        tmp_path,
        "\t\tmd_unlock_decision_tooltip = md_typo\n"
        "\t\tmd_unlock_decision_category_tooltip = md_typo\n"
        "\t\tunlock_decision_tooltip_days = md_typo\n"
        "\t\tunlock_decision_category_tooltip_of = md_typo\n",
    )
    assert _findings(validator) == []


def test_each_reference_site_is_reported(tmp_path):
    validator = _write_mod(tmp_path, "\t\tunlock_decision_tooltip = md_typo\n")
    write_text(
        tmp_path / "events" / "test.txt",
        "country_event = {\n"
        "\timmediate = {\n"
        "\t\tunlock_decision_tooltip = md_typo\n"
        "\t}\n"
        "}\n",
    )

    results = _findings(validator)

    assert {(path, line) for _, path, line in results} == {
        (_FOCUS_PATH, 4),
        (os.path.join("events", "test.txt"), 3),
    }


def test_finding_is_an_error_with_category_and_location(tmp_path):
    validator = _write_mod(tmp_path, "\t\tunlock_decision_tooltip = md_typo\n")

    validator.validate_undefined_unlock_tooltips()

    assert [(i.severity, i.category) for i in validator._issues] == [
        (V.Severity.ERROR, "undefined-unlock-tooltip-target")
    ]
    assert validator._issues[0].file == "common/national_focus/test.txt"
    assert validator._issues[0].line == 4


def test_run_validations_reports_undefined_targets_from_every_source_root(
    tmp_path,
):
    validator = _write_mod(
        tmp_path, "\t\tunlock_decision_tooltip = md_typo\n", no_cache=True
    )
    write_text(
        tmp_path / "events" / "md_test_events.txt",
        "country_event = {\n"
        "\timmediate = {\n"
        "\t\tunlock_decision_tooltip = md_typo\n"
        "\t}\n"
        "}\n",
    )
    write_text(
        tmp_path / "history" / "countries" / "md_test.txt",
        "unlock_decision_category_tooltip = md_typo\n",
    )

    validator.run_validations()

    reported = {
        (issue.file, issue.line, issue.severity)
        for issue in validator._issues
        if issue.category == "undefined-unlock-tooltip-target"
    }
    assert reported == {
        ("common/national_focus/test.txt", 4, V.Severity.ERROR),
        ("events/md_test_events.txt", 3, V.Severity.ERROR),
        ("history/countries/md_test.txt", 1, V.Severity.ERROR),
    }
