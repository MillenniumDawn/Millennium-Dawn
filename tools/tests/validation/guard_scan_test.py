"""Tests for guard_scan module, specifically sanitize and Context."""

import guard_scan


def test_sanitize_empty_string():
    assert guard_scan.sanitize("") == ""


def test_sanitize_plain_script():
    script = (
        "if = {\n"
        "\tlimit = { fuel_silo > 0 }\n"
        "\tdamage_building = { type = fuel_silo damage = 1 }\n"
        "}\n"
    )
    assert guard_scan.sanitize(script) == script


def test_sanitize_full_line_comment_preserves_line_count():
    script = "# This is a comment line\n652 = {\n\tfuel_silo > 0\n}\n"
    sanitized = guard_scan.sanitize(script)
    lines = sanitized.split("\n")
    assert lines[0] == ""
    assert lines[1] == "652 = {"
    assert len(lines) == len(script.split("\n"))


def test_sanitize_inline_comment_stripped():
    script = "fuel_silo > 0 # check if silo present\n"
    sanitized = guard_scan.sanitize(script)
    assert sanitized == "fuel_silo > 0 \n"


def test_sanitize_comment_containing_braces_neutralized():
    script = "# if = { limit = { fuel_silo > 0 } }\n652 = { type = fuel_silo }\n"
    sanitized = guard_scan.sanitize(script)
    assert "if =" not in sanitized
    assert "{" not in sanitized.split("\n")[0]
    assert "652 = { type = fuel_silo }" in sanitized


def test_sanitize_blank_quoted_strings():
    inner = "building_damage = { type = fuel_silo }"
    script = f'log = "{inner}"\n'
    sanitized = guard_scan.sanitize(script)
    expected = f'log = "{" " * len(inner)}"\n'
    assert sanitized == expected
    assert len(sanitized) == len(script)


def test_sanitize_meta_effect_macro_template():
    inner = "[?building_damage_by_missile]"
    script = f'DAM = "{inner}"\n'
    sanitized = guard_scan.sanitize(script)
    expected = f'DAM = "{" " * len(inner)}"\n'
    assert sanitized == expected
    assert len(sanitized) == len(script)


def test_sanitize_quoted_string_with_comment_char():
    inner = "building #1 damage"
    script = f'log = "{inner}"\n'
    sanitized = guard_scan.sanitize(script)
    expected = f'log = "{" " * len(inner)}"\n'
    assert sanitized == expected


def test_sanitize_comment_with_quoted_string():
    script = '# log = "test string"\n652 = { fuel_silo > 0 }\n'
    sanitized = guard_scan.sanitize(script)
    assert sanitized == "\n652 = { fuel_silo > 0 }\n"


def test_sanitize_multiline_quoted_string():
    script = 'text = "line one\nline two"\n'
    sanitized = guard_scan.sanitize(script)
    assert sanitized == 'text = "        \n        "\n'
    assert len(sanitized.split("\n")) == 3


def test_sanitize_escaped_quote_in_string():
    script = 'log = "escaped \\"quote\\" inside"\n'
    sanitized = guard_scan.sanitize(script)
    expected = 'log = "                        "\n'
    assert sanitized == expected
    assert len(sanitized) == len(script)


def test_context_apply():
    ctx0 = guard_scan.Context()
    assert ctx0.present == frozenset()

    # Empty proven set returns same context instance
    ctx1 = ctx0.apply(set())
    assert ctx1 is ctx0

    # Non-empty set returns new Context with union
    ctx2 = ctx0.apply({"fuel_silo"})
    assert ctx2.present == frozenset({"fuel_silo"})

    ctx3 = ctx2.apply({"arms_factory"})
    assert ctx3.present == frozenset({"fuel_silo", "arms_factory"})
