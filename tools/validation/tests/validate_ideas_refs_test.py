"""Tests for undefined idea-reference consumer coverage."""

import pytest
from validate_ideas import Validator, _scan_idea_refs


def test_scan_idea_refs_supports_multiline_add_remove_blocks():
    text = """
    add_ideas = {
        first_block_idea
        second_block_idea
    }
    remove_ideas = { third_block_idea fourth_block_idea }
    """
    assert set(_scan_idea_refs(text)) >= {
        "first_block_idea",
        "second_block_idea",
        "third_block_idea",
        "fourth_block_idea",
    }


def test_scan_idea_refs_skips_top_level_assignments_and_comments():
    text = """
    add_ideas = {
        first_block_idea
        idea = yes
        if = {
            limit = { has_country_flag = enabled }
            add_ideas = nested_idea
        }
        # commented_out_idea
        second_block_idea
    }
    remove_ideas = {
        modifier = { factor = 2 }
        third_block_idea fourth_block_idea
    }
    """
    refs = set(_scan_idea_refs(text))

    assert refs >= {
        "first_block_idea",
        "second_block_idea",
        "third_block_idea",
        "fourth_block_idea",
        "nested_idea",
    }
    assert refs.isdisjoint(
        {
            "idea",
            "yes",
            "if",
            "limit",
            "enabled",
            "commented_out_idea",
            "modifier",
            "factor",
            "2",
        }
    )


@pytest.mark.parametrize(
    "consumer_path",
    [
        "history/countries/test.txt",
        "common/on_actions/test.txt",
        "common/scripted_triggers/test.txt",
    ],
)
def test_staged_idea_consumer_is_scanned(tmp_path, consumer_path):
    path = tmp_path / consumer_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("has_idea = undefined_test_idea\n", encoding="utf-8")

    validator = Validator(
        mod_path=str(tmp_path),
        use_colors=False,
        workers=1,
        unused_ideas=False,
    )
    validator.staged_only = True
    validator.staged_files = [str(path)]
    validator.validate_undefined_idea_refs({})

    assert validator.errors_found == 1
    assert len(validator._issues) == 1
    assert "undefined_test_idea" in validator._issues[0].message
