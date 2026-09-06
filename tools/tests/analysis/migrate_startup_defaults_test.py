from pathlib import Path

import pytest
from migrate_startup_defaults import (
    CONTINENT_DEFAULTS,
    MigrationError,
    main,
    plan_migration,
)
from shared.suite import write_text

CONTINENTS = "continents = {\n\teurope\n\tafrica\n\tasia\n}\n"
DEFINITION = (
    "10;1;1;1;land;false;plains;1\n"
    "20;2;2;2;land;false;plains;2\n"
    "30;3;3;3;land;false;plains;3\n"
    "40;4;4;4;land;false;plains;2\n"
    "50;5;5;5;land;false;plains;3\n"
)


def _state(state_id, owner, province, productivity, controller=""):
    return (
        "state = {\n"
        f"\tid = {state_id}\n"
        "\thistory = {\n"
        f"\t\towner = {owner}\n"
        f"{controller}"
        f"\t\tset_variable = {{ productivity_state_var = {productivity} }}\n"
        "\t}\n"
        "\tprovinces = {\n"
        f"\t\t{province}\n"
        "\t}\n"
        "}\n"
    )


def _country(capital, body, dated="", ideas="\t\tstable_growth\n"):
    return (
        f"capital = {capital}\n"
        "2000.1.1 = {\n"
        f"{body}"
        "\tadd_ideas = {\n"
        f"{ideas}"
        "\t}\n"
        "}\n"
        f"{dated}"
    )


def _repo(mini_repo: Path):
    write_text(mini_repo / "map" / "continent.txt", CONTINENTS)
    write_text(mini_repo / "map" / "definition.csv", DEFINITION)
    write_text(
        mini_repo / "history" / "states" / "1-Test.txt",
        _state(1, "AAA", 10, 444),
    )
    write_text(
        mini_repo / "history" / "states" / "2-Test.txt",
        _state(2, "BBB", 20, 222),
    )
    write_text(
        mini_repo / "history" / "states" / "3-Test.txt",
        _state(3, "CCC", 30, 333),
    )
    write_text(
        mini_repo / "history" / "states" / "4-Test.txt",
        _state(4, "AAA", 40, 222),
    )
    write_text(
        mini_repo / "history" / "countries" / "AAA - Test.txt",
        _country(
            1,
            "\tset_variable = { currency_strength = 1.0 }\n",
            "2001.1.1 = { set_variable = { overall_productivity = 777 } }\n",
        ),
    )
    write_text(
        mini_repo / "history" / "countries" / "BBB - Test.txt",
        _country(
            2,
            "\tset_variable = { var = overall_productivity value = 333 }\n"
            "\tset_variable = { cb_policy_rate = 9 }\n"
            "\tadd_ideas = {\n\t\tgold_standard_back\n\t}\n",
        ),
    )
    write_text(
        mini_repo / "history" / "countries" / "CCC - Test.txt",
        _country(3, ""),
    )
    return mini_repo


def test_plan_preserves_explicit_values_and_maps_capital_region(mini_repo):
    root = _repo(mini_repo)
    changes = plan_migration(root)
    aaa = changes[str(root / "history" / "countries" / "AAA - Test.txt")]
    state = changes[str(root / "history" / "states" / "1-Test.txt")]
    overseas_state = changes[str(root / "history" / "states" / "4-Test.txt")]
    bbb = changes.get(str(root / "history" / "countries" / "BBB - Test.txt"), "")
    explicit_state = changes.get(str(root / "history" / "states" / "2-Test.txt"), "")

    assert "overall_productivity = 1000" in aaa
    assert "cb_policy_rate = 3" in aaa
    assert "no_currency_backing" in aaa
    assert "overall_productivity = 777" in aaa
    assert "productivity_state_var = 1000" in state
    assert "productivity_state_var = 222" not in state
    assert "productivity_state_var = 1000" in overseas_state
    assert bbb == ""
    assert explicit_state == ""


def test_country_history_controller_is_included(mini_repo):
    root = _repo(mini_repo)
    write_text(
        root / "history" / "countries" / "AAA - Test.txt",
        _country(1, "\tset_province_controller = 20\n"),
    )
    changes = plan_migration(root)
    controlled_state = changes[str(root / "history" / "states" / "2-Test.txt")]
    assert "productivity_state_var = 1000" in controlled_state


def test_partial_controller_with_different_defaults_is_rejected(mini_repo):
    root = _repo(mini_repo)
    write_text(
        root / "history" / "states" / "3-Test.txt",
        _state(3, "CCC", "30 50", 333, "\t\tAAA = { set_province_controller = 30 }\n"),
    )
    with pytest.raises(MigrationError, match="different startup defaults"):
        plan_migration(root)


def test_existing_values_support_reversed_fields_comments_and_nested_false_matches(
    mini_repo,
):
    root = _repo(mini_repo)
    write_text(
        root / "history" / "countries" / "AAA - Test.txt",
        _country(
            1,
            "\t# set_variable = { overall_productivity = 11 }\n"
            "\tforeign = { set_variable = { value = 12 var = overall_productivity } }\n"
            "\tset_variable = { value = 777 # keep this exact long form\n"
            "\t\tvar = overall_productivity }\n"
            "\tset_variable = { value = 8 var = cb_policy_rate }\n",
        ),
    )
    changes = plan_migration(root)
    country = changes[str(root / "history" / "countries" / "AAA - Test.txt")]
    assert "overall_productivity = 1000" not in country
    assert "cb_policy_rate = 3" not in country
    assert "value = 777 # keep this exact long form" in country
    assert (
        "foreign = { set_variable = { value = 12 var = overall_productivity } }"
        in country
    )


def test_future_assignments_and_multiple_ideas_are_not_startup_values(mini_repo):
    root = _repo(mini_repo)
    future = "2001.1.1 = { set_variable = { overall_productivity = 777 } }\n"
    country = _country(
        1,
        "\tadd_ideas = {\n\t\tstable_growth # not currency backing\n\t}\n",
        future,
        "\t\tgold_standard_back # alternative backing\n",
    )
    path = root / "history" / "countries" / "AAA - Test.txt"
    write_text(path, country)
    changes = plan_migration(root)
    updated = changes[str(path)]
    assert "overall_productivity = 1000" in updated
    assert "no_currency_backing" not in updated
    assert future in updated
    assert "gold_standard_back # alternative backing" in updated


def test_direct_controller_uses_controller_capital_region_not_state_region(mini_repo):
    root = _repo(mini_repo)
    write_text(root / "history" / "countries" / "AAA - Test.txt", _country(1, ""))
    write_text(root / "history" / "countries" / "BBB - Test.txt", _country(2, ""))
    write_text(
        root / "history" / "states" / "1-Test.txt",
        _state(1, "AAA", 10, 444, "\t\tcontroller = BBB\n"),
    )
    changes = plan_migration(root)
    assert (
        "productivity_state_var = 550"
        in changes[str(root / "history" / "states" / "1-Test.txt")]
    )


def test_comments_in_map_and_province_lists_are_ignored(mini_repo):
    root = _repo(mini_repo)
    write_text(
        root / "map" / "continent.txt",
        "continents = {\n\t# fake_continent\n\teurope # real\n\tafrica\n\tasia\n}\n",
    )
    write_text(
        root / "history" / "states" / "1-Test.txt",
        _state(1, "AAA", 10, 444).replace("\n\t\t10\n", "\n\t\t10 # province 999\n"),
    )
    changes = plan_migration(root)
    assert (
        "overall_productivity = 1000"
        in changes[str(root / "history" / "countries" / "AAA - Test.txt")]
    )


def test_undated_zombies_history_is_supported_and_preserved(mini_repo):
    root = _repo(mini_repo)
    path = root / "history" / "countries" / "ZOM - Zombies.txt"
    original = 'capital = 1\noob = "ZOM_2000"\nadd_ideas = {\n\tZombie\n}\n'
    write_text(path, original)
    changes = plan_migration(root)
    updated = changes[str(path)]
    assert 'capital = 1\noob = "ZOM_2000"\n' in updated
    assert "\tZombie\n" in updated
    assert "overall_productivity = 1000" in updated
    assert "cb_policy_rate = 3" in updated
    assert "no_currency_backing" in updated


def test_missing_add_ideas_for_c01_and_euu_is_created(mini_repo):
    root = _repo(mini_repo)
    c01 = root / "history" / "countries" / "C01 - Custom.txt"
    euu = root / "history" / "countries" / "EUU - EU.txt"
    write_text(c01, "capital = 1\n2000.1.1 = {\n}\n")
    write_text(euu, "capital = 1\n2000.1.1 = {\n}\n")
    changes = plan_migration(root)
    assert "add_ideas = {" in changes[str(c01)]
    assert "add_ideas = {" in changes[str(euu)]


def test_plan_is_idempotent_after_applying_changes(mini_repo):
    root = _repo(mini_repo)
    changes = plan_migration(root)
    for filename, content in changes.items():
        write_text(Path(filename), content)
    assert plan_migration(root) == {}


def test_undated_country_is_valid_and_missing_input_stays_unchanged(mini_repo):
    root = _repo(mini_repo)
    country = root / "history" / "countries" / "AAA - Test.txt"
    write_text(country, "capital = 1\n")
    before = country.read_text(encoding="utf-8")
    changes = plan_migration(root)
    assert country.read_text(encoding="utf-8") == before
    assert "overall_productivity = 1000" in changes[str(country)]
    assert CONTINENT_DEFAULTS["europe"] == 1000


def test_cli_dry_run_reports_changes_without_writing(mini_repo, capsys):
    root = _repo(mini_repo)
    paths = sorted((root / "history").rglob("*.txt"))
    before = {path: path.read_text(encoding="utf-8") for path in paths}
    assert main(("--root", str(root), "--dry-run")) == 0
    assert "would change" in capsys.readouterr().out
    assert before == {path: path.read_text(encoding="utf-8") for path in paths}


def test_inline_lists_and_complete_province_control(mini_repo):
    root = _repo(mini_repo)
    write_text(root / "map" / "continent.txt", "continents = { europe africa asia }")
    state_path = root / "history" / "states" / "3-Test.txt"
    write_text(
        state_path,
        _state(
            3,
            "CCC",
            "30 50",
            333,
            "\t\tAAA = { set_province_controller = 30 set_province_controller = 50 }\n",
        ),
    )
    country_path = root / "history" / "countries" / "AAA - Test.txt"
    write_text(
        country_path, _country(1, "", ideas="\t\tstable_growth gold_standard_back\n")
    )
    changes = plan_migration(root)
    assert "productivity_state_var = 1000" in changes[str(state_path)]
    assert "no_currency_backing" not in changes[str(country_path)]


def test_future_capital_and_controllers_are_ignored(mini_repo):
    root = _repo(mini_repo)
    country_path = root / "history" / "countries" / "AAA - Test.txt"
    write_text(
        country_path,
        _country(1, "", "2001.1.1 = { capital = 2 set_province_controller = 30 }\n"),
    )
    state_path = root / "history" / "states" / "1-Test.txt"
    write_text(
        state_path, _state(1, "AAA", 10, 444, "\t\t2001.1.1 = { controller = BBB }\n")
    )
    changes = plan_migration(root)
    assert "overall_productivity = 1000" in changes[str(country_path)]
    assert "productivity_state_var = 1000" in changes[str(state_path)]
    assert (
        "productivity_state_var = 650"
        in changes[str(root / "history" / "states" / "3-Test.txt")]
    )


def test_initial_dated_capital_and_state_productivity_override_root(mini_repo):
    root = _repo(mini_repo)
    country_path = root / "history" / "countries" / "AAA - Test.txt"
    write_text(country_path, _country(1, "\tcapital = 2\n"))
    state_path = root / "history" / "states" / "1-Test.txt"
    write_text(
        state_path,
        _state(
            1,
            "AAA",
            10,
            444,
            "\t\t2000.1.1 = { set_variable = { value = 777 var = productivity_state_var } }\n"
            "\t\t2001.1.1 = { set_variable = { productivity_state_var = 888 } }\n",
        ),
    )
    changes = plan_migration(root)
    assert "overall_productivity = 550" in changes[str(country_path)]
    assert "value = 550 var = productivity_state_var" in changes[str(state_path)]
    assert "productivity_state_var = 444" in changes[str(state_path)]
    assert "productivity_state_var = 888" in changes[str(state_path)]


def test_invalid_capital_fails_before_writing(mini_repo, capsys):
    root = _repo(mini_repo)
    country_path = root / "history" / "countries" / "CCC - Test.txt"
    write_text(country_path, _country(9999, ""))
    paths = sorted((root / "history").rglob("*.txt"))
    before = {path: path.read_bytes() for path in paths}
    assert main(("--root", str(root), "--write")) == 1
    assert "capital state 9999 not found" in capsys.readouterr().err
    assert before == {path: path.read_bytes() for path in paths}


def test_cli_write_is_idempotent(mini_repo):
    root = _repo(mini_repo)
    assert main(("--root", str(root), "--write")) == 0
    assert main(("--root", str(root), "--dry-run")) == 0
    assert plan_migration(root) == {}
