"""Tests for validate_tech_categories."""

from validate_tech_categories import Validator, _references

_TAGS = """technology_Categories = {
\tCAT_Military
\tCAT_missile
\tCAT_encryption_tech
\tCAT_computing_tech \t#general computing
\tCAT_computer_systems \t#armour computer systems
}
"""


def _run(tmp_path, rel_path, content, tags=_TAGS):
    tags_path = tmp_path / "common" / "technology_tags" / "00_technology.txt"
    tags_path.parent.mkdir(parents=True, exist_ok=True)
    tags_path.write_text(tags, encoding="utf-8")

    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.run_validations()
    return v


def _messages(v):
    return [i.message for i in v._issues if i.category == "unknown-tech-category"]


def test_known_category_in_add_tech_bonus_is_accepted(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = CAT_computing_tech }\n}\n",
    )
    assert _messages(v) == []
    assert v.errors_found == 0


def test_unknown_category_in_add_tech_bonus_is_reported(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = CAT_computing }\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert "CAT_computing" in messages[0]
    assert v.errors_found == 1


def test_unknown_category_suggests_the_closest_real_name(tmp_path):
    v = _run(
        tmp_path,
        "common/ideas/Test.txt",
        "ideas = {\n\tcountry = {\n\t\tx = {\n"
        "\t\t\tresearch_bonus = { CAT_encryption = 0.02 }\n\t\t}\n\t}\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert "CAT_encryption_tech" in messages[0], messages[0]


def test_research_bonus_keys_are_checked(tmp_path):
    v = _run(
        tmp_path,
        "common/ideas/Test.txt",
        "ideas = {\n\tcountry = {\n\t\tx = {\n"
        "\t\t\tresearch_bonus = { CAT_missiles = 0.12 }\n\t\t}\n\t}\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert "CAT_missiles" in messages[0]


def test_country_flag_named_like_a_category_is_not_a_reference(tmp_path):
    # CAT_ is also the Catalonia tag prefix; a flag is not a category reference.
    v = _run(
        tmp_path,
        "events/Spain.txt",
        "country_event = {\n\ttrigger = {\n"
        "\t\tNOT = { has_country_flag = CAT_revolted_against_spain }\n\t}\n}\n",
    )
    assert _messages(v) == []


def test_tech_bonus_name_is_not_a_category_reference(tmp_path):
    # `name =` inside add_tech_bonus labels the bonus; only `category =` is one.
    v = _run(
        tmp_path,
        "common/ideas/tribute.txt",
        "ideas = {\n\tcountry = {\n\t\tx = {\n"
        "\t\t\tadd_tech_bonus = { name = CAT_tribute category = CAT_missile }\n"
        "\t\t}\n\t}\n}\n",
    )
    assert _messages(v) == []


def test_each_unknown_name_is_reported_once(tmp_path):
    body = "\n".join("\tadd_tech_bonus = { category = CAT_nope }" for _ in range(4))
    v = _run(tmp_path, "events/Test.txt", "country_event = {\n" + body + "\n}\n")
    assert len(_messages(v)) == 1


def test_commented_out_reference_is_ignored(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\t#add_tech_bonus = { category = CAT_nope }\n}\n",
    )
    assert _messages(v) == []


def test_mixed_case_category_is_recognised(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = CAT_Military }\n}\n",
    )
    assert _messages(v) == []


def test_references_reads_only_category_assignments_and_research_bonus_keys():
    text = (
        "name = CAT_tribute\n"
        "has_country_flag = CAT_revolted_against_spain\n"
        "category = CAT_one\n"
        "research_bonus = { CAT_two = 0.1 CAT_three = 0.2 }\n"
    )
    assert [n for n, _ in _references(text)] == ["CAT_one", "CAT_two", "CAT_three"]


def test_research_bonus_stops_at_its_closing_brace():
    text = (
        "research_bonus = { CAT_one = 0.1 }\n"
        "equipment_bonus = { CAT_two = 0.2 }\n"
    )
    assert [n for n, _ in _references(text)] == ["CAT_one"]
