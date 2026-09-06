"""The redundant focus-set country flag check in validate_variables.

A country flag written by exactly one focus completion_reward and read back only
through has_country_flag duplicates state the engine already tracks, so
has_completed_focus replaces it. Each negative case below pins one of the five
disqualifiers that make the two constructs stop being equivalent.
"""

import pytest
import validate_variables as V


def _validator(tmp_path, **kwargs):
    return V.Validator(str(tmp_path), use_colors=False, workers=1, **kwargs)


def _run(tmp_path, **kwargs):
    validator = _validator(tmp_path, redundant_focus_flags=True, **kwargs)
    files = [str(p) for p in tmp_path.rglob("*.txt") if p.is_file()]
    validator.validate_redundant_focus_flags(files)
    return [
        (issue.message, issue.file, issue.line)
        for issue in validator._issues
        if issue.category == "redundant-focus-flag"
    ]


def _focus(reward_body, focus_id="TAG_focus", extra=""):
    return (
        "focus_tree = {\n"
        "\tid = tag_focus\n"
        "\tfocus = {\n"
        f"\t\tid = {focus_id}\n"
        f"{extra}"
        "\t\tcompletion_reward = {\n"
        f"{reward_body}"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def _tree(write_path, tmp_path, body, name="05_tag.txt"):
    return write_path(tmp_path, f"common/national_focus/{name}", body)


def _reader(write_path, tmp_path, body, name="tag.txt"):
    return write_path(tmp_path, f"common/decisions/{name}", body)


# --- positives -------------------------------------------------------------


def test_flag_set_once_in_completion_reward_is_reported(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done\n"))
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    found = _run(tmp_path)

    assert len(found) == 1
    message, file, _ = found[0]
    assert "tag_done" in message
    assert "has_completed_focus = TAG_focus" in message
    assert file.replace("\\", "/").endswith("common/national_focus/05_tag.txt")


def test_set_nested_in_hidden_effect_is_reported(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        _focus(
            "\t\t\thidden_effect = {\n"
            "\t\t\t\tset_country_flag = tag_done\n"
            "\t\t\t}\n"
        ),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert len(_run(tmp_path)) == 1


def test_reader_in_a_tag_scope_keeps_its_wrapper(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done\n"))
    _reader(
        write_path,
        tmp_path,
        "d = { available = { SAZ = { has_country_flag = tag_done } } }",
    )

    message, _, _ = _run(tmp_path)[0]
    assert "in SAZ scope - keep the wrapper" in message


def test_finding_is_located_at_the_set_site(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done\n"))
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    _, _, line = _run(tmp_path)[0]
    assert line == 6


# --- disqualifier 1: not set exactly once, in a focus reward ---------------


def test_two_setters_are_not_reported(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        _focus("\t\t\tset_country_flag = tag_done\n")
        + _focus("\t\t\tset_country_flag = tag_done\n", focus_id="TAG_other"),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


def test_setter_outside_any_focus_is_not_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/tag.txt",
        "tag_effect = { set_country_flag = tag_done }",
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


def test_timed_set_is_not_reported(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        _focus("\t\t\tset_country_flag = { flag = tag_done days = 30 value = 1 }\n"),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


# --- disqualifier 2: conditional or foreign-scope set ----------------------


@pytest.mark.parametrize("block", ["if", "else_if", "else", "random", "random_list"])
def test_conditional_set_is_not_reported(tmp_path, write_path, block):
    _tree(
        write_path,
        tmp_path,
        _focus(
            f"\t\t\t{block} = {{\n"
            "\t\t\t\tlimit = { has_war = yes }\n"
            "\t\t\t\tset_country_flag = tag_done\n"
            "\t\t\t}\n"
        ),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


def test_set_in_another_country_scope_is_not_reported(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        _focus("\t\t\tSAZ = {\n\t\t\t\tset_country_flag = tag_done\n\t\t\t}\n"),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


def test_set_in_select_effect_is_not_reported(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        "focus_tree = {\n"
        "\tid = tag_focus\n"
        "\tfocus = {\n"
        "\t\tid = TAG_focus\n"
        "\t\tselect_effect = {\n"
        "\t\t\tset_country_flag = tag_done\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


# --- disqualifier 3: the flag is cleared or modified -----------------------


def test_cleared_flag_is_not_reported(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done\n"))
    _reader(
        write_path,
        tmp_path,
        "d = { available = { has_country_flag = tag_done } "
        "complete_effect = { clr_country_flag = tag_done } }",
    )

    assert _run(tmp_path) == []


def test_modified_flag_is_not_reported(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done\n"))
    _reader(
        write_path,
        tmp_path,
        "d = { available = { has_country_flag = tag_done } "
        "complete_effect = { modify_country_flag = { flag = tag_done value = 1 } } }",
    )

    assert _run(tmp_path) == []


# --- disqualifier 4: readers ----------------------------------------------


def test_flag_with_no_readers_is_left_to_the_unused_flag_check(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done\n"))

    assert _run(tmp_path) == []


def test_long_form_read_is_not_reported(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done\n"))
    _reader(
        write_path,
        tmp_path,
        "d = { available = { has_country_flag = { flag = tag_done value > 0 } } }",
    )

    assert _run(tmp_path) == []


def test_dynamic_scope_flag_is_not_reported(tmp_path, write_path):
    _tree(write_path, tmp_path, _focus("\t\t\tset_country_flag = tag_done_@ROOT\n"))
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


# --- disqualifier 5: bypass and joint focuses ------------------------------


def test_bypassable_focus_is_not_reported(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        _focus(
            "\t\t\tset_country_flag = tag_done\n",
            extra="\t\tbypass = { has_war = yes }\n",
        ),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


def test_joint_reward_is_not_reported(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        "joint_focus = {\n"
        "\tid = TAG_focus\n"
        "\tcompletion_reward_joint_originator = {\n"
        "\t\tset_country_flag = tag_done\n"
        "\t}\n"
        "}\n",
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    assert _run(tmp_path) == []


# --- message annotations ---------------------------------------------------


def test_tree_reload_without_keep_completed_adds_a_caution(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        _focus("\t\t\tset_country_flag = tag_done\n")
        + _focus(
            "\t\t\tload_focus_tree = generic_focus\n",
            focus_id="TAG_swap",
        ),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    message, _, _ = _run(tmp_path)[0]
    assert "keep_completed = yes" in message


def test_keep_completed_reload_adds_no_caution(tmp_path, write_path):
    _tree(
        write_path,
        tmp_path,
        _focus("\t\t\tset_country_flag = tag_done\n")
        + _focus(
            "\t\t\tload_focus_tree = { tree = generic_focus keep_completed = yes }\n",
            focus_id="TAG_swap",
        ),
    )
    _reader(write_path, tmp_path, "d = { available = { has_country_flag = tag_done } }")

    message, _, _ = _run(tmp_path)[0]
    assert "keep_completed = yes" not in message


# --- wiring ----------------------------------------------------------------


def test_check_is_opt_in(tmp_path, monkeypatch):
    validator = _validator(tmp_path)
    called = []
    monkeypatch.setattr(
        validator, "validate_redundant_focus_flags", lambda *a: called.append(a)
    )
    validator.run_validations()

    assert called == []


def test_staged_mode_never_runs_the_check(tmp_path, monkeypatch):
    validator = _validator(tmp_path, redundant_focus_flags=True, staged_only=True)
    called = []
    monkeypatch.setattr(
        validator, "validate_redundant_focus_flags", lambda *a: called.append(a)
    )
    validator.run_validations()

    assert called == []


def test_cli_exposes_the_flag():
    import argparse

    parser = argparse.ArgumentParser()
    V._add_extra_args(parser)

    assert parser.parse_args(["--redundant-focus-flags"]).redundant_focus_flags
    assert not parser.parse_args([]).redundant_focus_flags
