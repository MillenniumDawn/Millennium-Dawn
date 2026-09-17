"""Tests for validate_tech_categories."""

from validate_tech_categories import (
    Validator,
    _brace_span,
    _doctrine_category_bodies,
    _references,
)

_TAG_NAMES = [
    "CAT_military",
    "CAT_missile",
    "CAT_encryption_tech",
    "CAT_computing_tech",
    "CAT_computer_systems",
]

_TAGS = """technology_Categories = {
\tCAT_military
\tCAT_missile
\tCAT_encryption_tech
\tCAT_computing_tech \t#general computing
\tCAT_computer_systems \t#armour computer systems
}
"""

# One tech per tag so every declared tag is used.
_TECHS = (
    "technologies = {\n"
    + "".join(
        f"\ttech_{i} = {{\n\t\tcategories = {{ {name} }}\n\t}}\n"
        for i, name in enumerate(_TAG_NAMES)
    )
    + "}\n"
)

_LOC = "l_english:\n" + "".join(
    f' {name}: "{name}"\n {name}_research: "${name}$ Research"\n' for name in _TAG_NAMES
)


def _write(tmp_path, rel_path, content):
    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _run(tmp_path, rel_path, content, tags=_TAGS, techs=_TECHS, loc=_LOC):
    _write(tmp_path, "common/technology_tags/00_technology.txt", tags)
    _write(tmp_path, "common/technologies/00_test.txt", techs)
    _write(tmp_path, "localisation/english/test_l_english.yml", loc)
    _write(tmp_path, rel_path, content)

    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.run_validations()
    return v


def _messages(v, category="unknown-tech-category"):
    return [i.message for i in v._issues if i.category == category]


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


def test_mixed_case_tag_is_a_format_error(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = CAT_Military }\n}\n",
        tags=_TAGS.replace("CAT_military", "CAT_Military"),
        techs=_TECHS.replace("CAT_military", "CAT_Military"),
        loc=_LOC.replace("CAT_military", "CAT_Military"),
    )
    assert _messages(v) == []
    assert _messages(v, "tech-category-name-format") == [
        "Technology category 'CAT_Military' is not CAT_lowercase"
    ]


def test_tech_file_categories_are_checked(tmp_path):
    v = _run(
        tmp_path,
        "common/technologies/01_armor.txt",
        "technologies = {\n\tengine_1 = {\n"
        "\t\tcategories = {\n\t\t\tCAT_missile\n\t\t\tCat_Armor_Engines\n\t\t}\n"
        "\t}\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert "Cat_Armor_Engines" in messages[0]


def test_mixed_case_category_assignment_is_reported(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = Cat_Armor_Engines }\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert "Cat_Armor_Engines" in messages[0]


def test_categories_block_outside_tech_files_is_not_a_reference(tmp_path):
    # Doctrines and sub-units carry categories blocks of their own.
    v = _run(
        tmp_path,
        "common/doctrines/tracks/land.txt",
        "track = {\n\tmastery = {\n\t\tcategories = { category_all_infantry }\n"
        "\t}\n}\n",
    )
    assert _messages(v) == []


def test_mio_research_categories_are_checked(tmp_path):
    v = _run(
        tmp_path,
        "common/military_industrial_organization/organizations/MD_X.txt",
        "X_manufacturer = {\n"
        "\tresearch_categories = {\n\t\tCAT_missile\n\t\tCAT_rockets\n\t}\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert "CAT_rockets" in messages[0]


def test_ai_focus_research_weights_are_checked(tmp_path):
    v = _run(
        tmp_path,
        "common/ai_focuses/MD_X.txt",
        "X_ai = {\n\tresearch = {\n\t\tdefensive = 5.0\n"
        "\t\tCAT_missile = 5.0\n\t\tCAT_sam = 5.0\n\t}\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert "CAT_sam" in messages[0]


def test_tag_without_loc_keys_is_reported(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n}\n",
        loc=_LOC.replace(' CAT_missile_research: "$CAT_missile$ Research"\n', ""),
    )
    assert _messages(v, "tech-category-unlocalised") == [
        "Technology category 'CAT_missile' has no English loc key CAT_missile_research"
    ]


def test_tag_no_tech_uses_is_reported(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n}\n",
        techs=_TECHS.replace("categories = { CAT_missile }", "categories = { }"),
    )
    assert _messages(v, "tech-category-unused") == [
        "Technology category 'CAT_missile' is not used by any technology or doctrine"
    ]


def test_doctrine_categories_are_checked(tmp_path):
    v = _run(
        tmp_path,
        "common/doctrines/grand_doctrines/land.txt",
        "combined_arms = {\n\tfolder = land\n\tcategories = {\n"
        "\t\tCAT_zzz_doctrine\n\t}\n}\n",
    )
    messages = _messages(v)
    assert len(messages) == 1
    assert messages[0].startswith("Unknown technology category 'CAT_zzz_doctrine'")


def test_doctrine_mastery_categories_are_not_references(tmp_path):
    v = _run(
        tmp_path,
        "common/doctrines/subdoctrines/land/x.txt",
        "sub = {\n\ttrack = t\n\tcategories = {\n\t\tCAT_missile\n\t}\n"
        "\tmastery = {\n\t\tcategories = { category_all_infantry }\n\t}\n}\n",
    )
    assert _messages(v) == []


def test_doctrine_carrier_satisfies_unused_check(tmp_path):
    v = _run(
        tmp_path,
        "common/doctrines/subdoctrines/land/x.txt",
        "sub = {\n\tcategories = {\n\t\tCAT_missile\n\t}\n}\n",
        techs=_TECHS.replace("categories = { CAT_missile }", "categories = { }"),
    )
    assert _messages(v, "tech-category-unused") == []


def test_doctrine_category_bodies_skips_nested_mastery_block():
    text = (
        "a = {\n\tcategories = { X }\n\tmastery = {\n\t\tcategories = { Y }\n\t}\n}\n"
    )
    bodies = list(_doctrine_category_bodies(text))
    assert len(bodies) == 1
    assert "X" in bodies[0][0]


def test_clean_fixture_has_no_definition_findings(tmp_path):
    v = _run(tmp_path, "events/Test.txt", "country_event = {\n}\n")
    assert [i.category for i in v._issues] == []


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
        "research_bonus = { CAT_one = 0.1 }\n" "equipment_bonus = { CAT_two = 0.2 }\n"
    )
    assert [n for n, _ in _references(text)] == ["CAT_one"]


def test_research_bonus_spans_a_nested_block():
    text = (
        "research_bonus = {\n"
        "\tif = { limit = { always = yes } }\n"
        "\tCAT_one = 0.1\n"
        "}\n"
        "research_bonus = { CAT_two = 0.2 }\n"
    )
    assert [n for n, _ in _references(text)] == ["CAT_one", "CAT_two"]


def test_brace_span_of_an_unclosed_block_runs_to_the_end():
    text = "research_bonus = { CAT_one = 0.1"
    assert _brace_span(text, text.index("{")) == len(text)


def test_unclosed_research_bonus_still_yields_its_keys():
    text = "research_bonus = { CAT_nope = 0.1\n"
    assert [n for n, _ in _references(text)] == ["CAT_nope"]


def test_unreadable_tag_file_is_skipped(tmp_path):
    (tmp_path / "common" / "technology_tags" / "broken.txt").mkdir(parents=True)
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = CAT_computing }\n}\n",
    )
    assert len(_messages(v)) == 1


def test_unreadable_scanned_file_is_skipped(tmp_path):
    (tmp_path / "events" / "broken.txt").mkdir(parents=True)
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = CAT_missile }\n}\n",
    )
    assert _messages(v) == []
    assert v.errors_found == 0


def test_missing_category_set_is_reported_once(tmp_path):
    v = _run(
        tmp_path,
        "events/Test.txt",
        "country_event = {\n\tadd_tech_bonus = { category = CAT_missile }\n}\n",
        tags="",
    )
    assert [i.category for i in v._issues] == ["tech-category-set-missing"]
