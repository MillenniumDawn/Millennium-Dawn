"""Regressions for the modify_treasury_effect state-scope check.

modify_treasury_effect writes the country-scope `treasury` variable, so calling
it inside a state block silently no-ops. The scope tracker only flags when the
nearest enclosing scope switch is a state, so random_list weights and intervening
owner/tag/ROOT openers must not produce false positives.
"""

import validate_variables as V


def _hits(tmp_path, body):
    path = tmp_path / "focus.txt"
    path.write_text(body)
    return V.process_file_for_treasury_scope((str(path), str(tmp_path)))


def test_state_id_block_is_flagged(tmp_path):
    body = (
        "completion_reward = {\n"
        "\t592 = {\n"
        "\t\tadd_building_construction = { type = infrastructure level = 1 }\n"
        "\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t\tmodify_treasury_effect = yes\n"
        "\t}\n"
        "}\n"
    )
    hits = _hits(tmp_path, body)
    assert len(hits) == 1
    assert "state scope" in hits[0][0]
    assert "592" in hits[0][0]


def test_random_state_iterator_is_flagged(tmp_path):
    body = (
        "remove_effect = {\n"
        "\trandom_owned_state = {\n"
        "\t\tset_temp_variable = { treasury_change = -3 }\n"
        "\t\tmodify_treasury_effect = yes\n"
        "\t}\n"
        "}\n"
    )
    assert len(_hits(tmp_path, body)) == 1


def test_random_list_weight_is_not_a_state(tmp_path):
    body = (
        "complete_effect = {\n"
        "\trandom_list = {\n"
        "\t\t20 = {\n"
        "\t\t\tset_temp_variable = { treasury_change = 25 }\n"
        "\t\t\tmodify_treasury_effect = yes\n"
        "\t\t}\n"
        "\t\t20 = {\n"
        "\t\t\tset_temp_variable = { treasury_change = 15 }\n"
        "\t\t\tmodify_treasury_effect = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _hits(tmp_path, body) == []


def test_owner_opener_masks_state_scope(tmp_path):
    body = (
        "completion_reward = {\n"
        "\trandom_owned_state = {\n"
        "\t\towner = {\n"
        "\t\t\tset_temp_variable = { treasury_change = -3 }\n"
        "\t\t\tmodify_treasury_effect = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _hits(tmp_path, body) == []


def test_country_tag_opener_masks_state_scope(tmp_path):
    body = (
        "immediate = {\n"
        "\t217 = {\n"
        "\t\tISR = {\n"
        "\t\t\tset_temp_variable = { treasury_change = 6 }\n"
        "\t\t\tmodify_treasury_effect = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _hits(tmp_path, body) == []


def test_top_level_country_scope_is_not_flagged(tmp_path):
    body = (
        "completion_reward = {\n"
        "\tset_temp_variable = { treasury_change = -10 }\n"
        "\tmodify_treasury_effect = yes\n"
        "}\n"
    )
    assert _hits(tmp_path, body) == []


def test_literal_brace_in_quoted_log_does_not_desync(tmp_path):
    # A `}` inside a quoted log string must not be counted as a real close brace:
    # without quote-aware blanking the stray brace popped the state frame early
    # and the modify_treasury_effect call in state scope was silently missed.
    body = (
        "completion_reward = {\n"
        "\t592 = {\n"
        '\t\tlog = "spurious brace } in a string"\n'
        "\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t\tmodify_treasury_effect = yes\n"
        "\t}\n"
        "}\n"
    )
    hits = _hits(tmp_path, body)
    assert len(hits) == 1
    assert "592" in hits[0][0]


def test_root_opener_is_conservative_not_flagged(tmp_path):
    body = (
        "completion_reward = {\n"
        "\trandom_owned_state = {\n"
        "\t\tROOT = {\n"
        "\t\t\tset_temp_variable = { treasury_change = -3 }\n"
        "\t\t\tmodify_treasury_effect = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _hits(tmp_path, body) == []
