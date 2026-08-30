"""Unit tests for the shared AI-only detection helpers in shared_utils.

An unconditional `is_ai = yes` in `visible`/`available`/`allowed` hides a
decision or a whole decision category from every human player, which is what
lets the validators drop the localisation and tooltip requirements on it.
Nested inside OR/AND/if/limit or a scoped `TAG = { }` the token is conditional
and must not exempt anything.
"""

from shared_utils import (
    ai_only_decision_categories,
    direct_child_block,
    has_flat_is_ai,
    is_ai_only_block,
)


def test_flat_is_ai_detected():
    assert has_flat_is_ai("{\n\t\t\tis_ai = yes\n\t\t}")


def test_is_ai_nested_in_or_not_detected():
    assert not has_flat_is_ai("{\n\t\t\tOR = {\n\t\t\t\tis_ai = yes\n\t\t\t}\n\t\t}")


def test_direct_child_block_returns_block_with_braces():
    body = "\tcost = 25\n\tvisible = {\n\t\tis_ai = yes\n\t}\n"
    assert direct_child_block(body, "visible") == "{\n\t\tis_ai = yes\n\t}"


def test_direct_child_block_ignores_nested_same_name():
    # A `visible` inside an effect's `limit` is not the object's own gate.
    body = "\tcomplete_effect = {\n\t\tif = { limit = { visible = { is_ai = yes } } }\n\t}\n"
    assert direct_child_block(body, "visible") == ""


def test_direct_child_block_missing_returns_empty():
    assert direct_child_block("\tcost = 25\n", "visible") == ""


def test_is_ai_only_block_accepts_braced_body():
    assert is_ai_only_block("{\n\tvisible = { is_ai = yes }\n}")


def test_is_ai_only_block_accepts_bare_body():
    assert is_ai_only_block("\tallowed = { is_ai = yes }\n")


def test_is_ai_only_block_available_gate():
    assert is_ai_only_block("\tavailable = {\n\t\tis_ai = yes\n\t}\n")


def test_is_ai_only_block_ignores_nested_gate():
    assert not is_ai_only_block(
        "\tvisible = {\n\t\tOR = { is_ai = yes is_debug = yes }\n\t}\n"
    )


def test_is_ai_only_block_plain_decision():
    assert not is_ai_only_block("\tvisible = { has_country_flag = my_flag }\n")


def _write_categories(tmp_path, text):
    path = tmp_path / "common" / "decisions" / "categories" / "cat.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(tmp_path)


def test_ai_only_category_detected(tmp_path):
    mod = _write_categories(
        tmp_path,
        "md_ai_category = {\n"
        "\tallowed = { original_tag = JAP }\n"
        "\tvisible = {\n"
        "\t\tis_ai = yes\n"
        "\t\thas_global_flag = MD_some_flag\n"
        "\t}\n"
        "}\n"
        "md_human_category = {\n"
        "\tallowed = { original_tag = JAP }\n"
        "}\n",
    )
    assert ai_only_decision_categories(mod) == {"md_ai_category"}


def test_debug_gated_category_not_ai_only(tmp_path):
    mod = _write_categories(
        tmp_path,
        "md_templates_category = {\n"
        "\tallowed = {\n"
        "\t\tOR = {\n"
        "\t\t\tis_ai = yes\n"
        "\t\t\tis_debug = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert ai_only_decision_categories(mod) == set()


def test_commented_is_ai_not_ai_only(tmp_path):
    mod = _write_categories(
        tmp_path,
        "md_ai_category = {\n\tvisible = {\n\t\t# is_ai = yes\n\t}\n}\n",
    )
    assert ai_only_decision_categories(mod) == set()


def test_missing_categories_directory_is_empty(tmp_path):
    assert ai_only_decision_categories(str(tmp_path)) == set()
