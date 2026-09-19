import pytest
from equipment_variant_context import VariantContext, script_nodes
from shared_utils import FileOpener
from validate_equipment_variants import (
    Validator,
    check_variant_availability,
    equipment_unlocks,
)
from validator_batches import ALL_SPECS

UNLOCKS = {"hull": {"naval_tech"}, "tank": {"armor_tech"}, "plane": {"air_tech"}}


def write_technology(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/technologies/test.txt",
        "technologies = { naval_tech = { enable_equipments = { hull } } }",
    )


def reward(equipment="hull", extra="", consumer="add_equipment_production", creator=""):
    creation = f'create_equipment_variant = {{ name = "Test Design" type = {equipment} {extra} }}'
    if consumer == "add_equipment_production":
        use = f'equipment = {{ type = {equipment} version_name = "Test Design" {creator} }}'
    else:
        field = "equipment_variant" if consumer == "create_ship" else "variant_name"
        use = f'type = {equipment} {field} = "Test Design" {creator}'
    return f"{creation}\n{consumer} = {{ {use} }}"


@pytest.mark.parametrize("equipment", UNLOCKS)
@pytest.mark.parametrize(
    "consumer",
    ["add_equipment_production", "create_ship", "add_equipment_to_stockpile"],
)
def test_every_equipment_and_consumer(equipment, consumer):
    findings = check_variant_availability(reward(equipment, consumer=consumer), UNLOCKS)
    assert len(findings) == 1
    assert findings[0][1] == 2
    assert equipment in findings[0][0]
    assert consumer in findings[0][0]


@pytest.mark.parametrize(
    "prefix",
    [
        "set_technology = { naval_tech = 1 }",
        "if = { limit = { NOT = { has_tech = naval_tech } } set_technology = { naval_tech = 1 } }",
        "if = { limit = { has_war = yes } set_technology = { naval_tech = 1 } } else = { set_technology = { naval_tech = 1 } }",
    ],
)
def test_prior_guaranteed_grants(prefix):
    assert not check_variant_availability(prefix + reward(), UNLOCKS)


@pytest.mark.parametrize(
    "body",
    [
        reward(extra="allow_without_tech = yes"),
        "if = { limit = { has_tech = naval_tech } " + reward() + " }",
        "focus = { available = { has_tech = naval_tech } completion_reward = { "
        + reward()
        + " } }",
        "country_event = { trigger = { has_tech = naval_tech } option = { "
        + reward()
        + " } }",
        "if = { limit = { OR = { has_tech = naval_tech AND = { has_tech = naval_tech has_war = no } } } "
        + reward()
        + " }",
    ],
)
def test_explicit_permission_and_guards(body):
    assert not check_variant_availability(body, UNLOCKS)


@pytest.mark.parametrize(
    "wrapper", ["custom_trigger_tooltip", "custom_override_tooltip"]
)
@pytest.mark.parametrize(
    "container",
    [
        "if = { limit = { GUARD } BODY }",
        "focus = { available = { GUARD } completion_reward = { BODY } }",
        "country_event = { trigger = { GUARD } option = { BODY } }",
    ],
)
@pytest.mark.parametrize(
    "condition,expected_warnings",
    [
        ("has_tech = naval_tech", 0),
        ("NOT = { has_tech = naval_tech }", 1),
        ("OR = { has_tech = naval_tech has_war = yes }", 1),
        ("GER = { has_tech = naval_tech }", 1),
    ],
)
def test_tooltip_wrapped_technology_guards(
    wrapper, container, condition, expected_warnings
):
    guard = f"{wrapper} = {{ tooltip = TECH_REQUIRED {condition} }}"
    body = container.replace("GUARD", guard).replace("BODY", reward())
    assert len(check_variant_availability(body, UNLOCKS)) == expected_warnings


@pytest.mark.parametrize(
    "prefix",
    [
        "if = { limit = { has_war = yes } set_technology = { naval_tech = 1 } }",
        "GER = { set_technology = { naval_tech = 1 } }",
        "effect_tooltip = { set_technology = { naval_tech = 1 } }",
        "set_technology = { armor_tech = 1 }",
        "set_technology = { naval_tech = 0 }",
    ],
)
def test_unrelated_or_conditional_grant_does_not_prove_unlock(prefix):
    assert len(check_variant_availability(prefix + reward(), UNLOCKS)) == 1


@pytest.mark.parametrize(
    "condition",
    [
        "NOT = { has_tech = naval_tech }",
        "OR = { has_tech = naval_tech has_war = yes }",
        "GER = { has_tech = naval_tech }",
    ],
)
def test_weak_or_foreign_guards(condition):
    assert check_variant_availability(
        f"if = {{ limit = {{ {condition} }} {reward()} }}", UNLOCKS
    )


def test_order_and_hidden_effects():
    creation, use = reward().splitlines()
    grant = "hidden_effect = { set_technology = { naval_tech = 1 } }"
    assert not check_variant_availability(creation + grant + use, UNLOCKS)
    assert check_variant_availability(creation + use + grant, UNLOCKS)
    assert check_variant_availability(
        "hidden_effect = { " + creation + " }" + use, UNLOCKS
    )


def test_separate_scopes_and_rewards_do_not_share_variants():
    creation, use = reward().splitlines()
    for text in [
        creation + "GER = { " + use + " }",
        "option = { " + creation + " } option = { " + use + " }",
        "focus = { completion_reward = { "
        + creation
        + " } } focus = { completion_reward = { "
        + use
        + " } }",
    ]:
        assert not check_variant_availability(text, UNLOCKS)
    assert check_variant_availability(
        "GER = { " + reward(creator="creator = GER") + " }", UNLOCKS
    )
    assert not check_variant_availability(reward(creator="creator = GER"), UNLOCKS)


def test_matching_variant_identity():
    text = reward()
    assert not check_variant_availability(
        text.replace('version_name = "Test Design"', 'version_name = "Other"'), UNLOCKS
    )
    assert not check_variant_availability(
        text.replace("equipment = { type = hull", "equipment = { type = tank"), UNLOCKS
    )
    assert not check_variant_availability(reward("unknown"), UNLOCKS)
    assert not check_variant_availability(
        text.replace("Test Design", "[dynamic_name]"), UNLOCKS
    )
    assert not check_variant_availability(
        reward(consumer="add_equipment_to_stockpile", creator="producer = GER"), UNLOCKS
    )


def test_comments_strings_and_line_numbers():
    assert not check_variant_availability(
        "# " + reward().replace("\n", "\n# "), UNLOCKS
    )
    text = '# heading\nlog = "create_equipment_variant = { name = fake }"\n' + reward()
    assert check_variant_availability(text, UNLOCKS)[0][1] == 4


def test_conditional_creation_remains_pending_after_branch():
    creation, use = reward().splitlines()
    assert check_variant_availability(
        "if = { limit = { has_war = yes } " + creation + " }" + use, UNLOCKS
    )
    assert not check_variant_availability(
        "if = { limit = { has_tech = naval_tech } " + creation + " }" + use, UNLOCKS
    )


def test_equipment_unlock_mapping():
    assert equipment_unlocks("""
    technologies = {
        naval_tech = { enable_equipments = { hull } }
        alternate = { enable_equipments = { hull tank } }
        unrelated = { enable_equipment_modules = { plane } }
    }
    """) == {"hull": {"naval_tech", "alternate"}, "tank": {"alternate"}}


@pytest.mark.parametrize(
    "path",
    [
        "common/national_focus/test.txt",
        "common/decisions/test.txt",
        "common/scripted_effects/test.txt",
        "common/on_actions/test.txt",
        "common/special_projects/test.txt",
        "common/scripted_guis/test.txt",
        "events/test.txt",
        "history/countries/test.txt",
    ],
)
def test_validator_scans_all_effect_sources(tmp_path, write_path, path):
    write_technology(tmp_path, write_path)
    write_path(tmp_path, path, reward())
    validator = Validator(mod_path=str(tmp_path), workers=1, use_colors=False)
    validator.run_validations()
    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "equipment-variant-unavailable"
    assert issue.severity == "warning"
    assert issue.file.replace("\\", "/") == path


def test_ci_registration_is_warning_only():
    spec = next(spec for spec in ALL_SPECS if spec.name == "equipment-variants")
    assert not spec.strict
    assert set(spec.groups) == {"common", "events", "history"}


@pytest.mark.parametrize("staged", ["events/first.txt", "common/technologies/test.txt"])
def test_staged_sources_and_technology_changes(tmp_path, write_path, staged):
    write_technology(tmp_path, write_path)
    for name in ("first", "second"):
        write_path(tmp_path, f"events/{name}.txt", reward())
    validator = Validator(
        mod_path=str(tmp_path), staged_only=True, workers=1, use_colors=False
    )
    validator.staged_files = [str(tmp_path / staged)]
    validator.run_validations()
    assert len(validator._issues) == 2


@pytest.mark.parametrize(
    "wrapper",
    [
        "random = { chance = 50 BODY }",
        "while = { limit = { has_war = yes } BODY }",
        "random_list = { 50 = { BODY } 50 = { add_stability = 0.1 } }",
        "if = { limit = { has_war = yes } add_stability = 0.1 } else_if = { limit = { has_stability > 0.5 } BODY }",
    ],
)
def test_optional_grants_do_not_unlock_later_consumers(wrapper):
    prefix = wrapper.replace("BODY", "set_technology = { naval_tech = 1 }")
    assert check_variant_availability(prefix + reward(), UNLOCKS)


@pytest.mark.parametrize(
    "consumer,field",
    [
        ("add_equipment_production", "creator"),
        ("create_ship", "creator"),
        ("add_equipment_to_stockpile", "producer"),
    ],
)
def test_root_producer_is_local(consumer, field):
    body = reward(consumer=consumer, creator=f"{field} = ROOT")
    assert check_variant_availability("completion_reward = { " + body + " }", UNLOCKS)


@pytest.mark.parametrize("scope", ["ROOT", "THIS"])
def test_same_scope_preserves_technology_and_pending_variants(scope):
    creation, use = reward().splitlines()
    grant = "set_technology = { naval_tech = 1 }"
    assert not check_variant_availability(
        grant + f"{scope} = {{ {reward()} }}", UNLOCKS
    )
    assert not check_variant_availability(
        f"{scope} = {{ {grant} }}" + reward(), UNLOCKS
    )
    assert check_variant_availability(creation + f"{scope} = {{ {use} }}", UNLOCKS)
    assert check_variant_availability(f"{scope} = {{ {creation} }}" + use, UNLOCKS)


@pytest.mark.parametrize(
    "scope", ["random_other_country", "every_country", "FROM", "event_target:recipient"]
)
def test_foreign_selector_does_not_inherit_literal_country(scope):
    foreign = reward(creator="creator = GER")
    assert not check_variant_availability(
        f"GER = {{ {scope} = {{ {foreign} }} }}", UNLOCKS
    )
    local = reward(creator="creator = THIS")
    assert check_variant_availability(f"GER = {{ {scope} = {{ {local} }} }}", UNLOCKS)
    assert not check_variant_availability(
        f"{scope} = {{ {reward(creator='creator = ROOT')} }}", UNLOCKS
    )


def test_same_literal_scope_preserves_state():
    assert not check_variant_availability(
        "GER = { set_technology = { naval_tech = 1 } GER = { " + reward() + " } }",
        UNLOCKS,
    )


@pytest.mark.parametrize("event_type", ["country_event", "news_event"])
def test_event_immediate_seeds_each_option_independently(event_type):
    creation, use = reward().splitlines()
    grant = "set_technology = { naval_tech = 1 }"
    assert not check_variant_availability(
        f"{event_type} = {{ option = {{ {reward()} }} immediate = {{ {grant} }} }}",
        UNLOCKS,
    )
    text = (
        f"{event_type} = {{ immediate = {{ {creation} }} "
        f"option = {{ {grant} {use} }} option = {{ {use} }} }}"
    )
    assert len(check_variant_availability(text, UNLOCKS)) == 1
    assert check_variant_availability(
        f"{event_type} = {{ immediate = {{ {grant} }} }} "
        f"{event_type} = {{ option = {{ {reward()} }} }}",
        UNLOCKS,
    )


@pytest.mark.parametrize(
    "outcomes",
    [
        "1 = { GRANT } 1 = { GRANT }",
        "1 = { GRANT } 0 = { add_stability = 0.1 }",
        "1 = { GRANT } variable_weight = { GRANT }",
        "log = yes seed = some_seed 1 = { GRANT }",
    ],
)
def test_random_list_guaranteed_selection(outcomes):
    body = outcomes.replace("GRANT", "set_technology = { naval_tech = 1 }")
    assert not check_variant_availability(
        "random_list = { " + body + " }" + reward(), UNLOCKS
    )


@pytest.mark.parametrize(
    "outcomes",
    [
        "0 = { GRANT }",
        "variable_weight = { GRANT }",
        "1 = { trigger = { has_war = yes } GRANT }",
        "1 = { modifier = { factor = 0 has_war = yes } GRANT }",
        "1 = { GRANT } 1 = { }",
        "1 = { GRANT } 0 = { modifier = { add = 1 has_war = yes } add_stability = 0.1 }",
    ],
)
def test_random_list_optional_selection_or_grant(outcomes):
    body = outcomes.replace("GRANT", "set_technology = { naval_tech = 1 }")
    assert check_variant_availability(
        "random_list = { " + body + " }" + reward(), UNLOCKS
    )


def context_for(documents):
    documents = {
        "common/bookmarks/start.txt": "bookmarks = { bookmark = { date = 2000.1.1.12 } }",
        "common/technology_tags/folders.txt": 'technology_folders = { designer = { available = { has_dlc = "Designer" } } }',
        "common/technologies/test.txt": "technologies = { naval_tech = { folder = { name = designer } enable_equipments = { hull } } }",
        **documents,
    }
    context = VariantContext(
        documents={path: script_nodes(text) for path, text in documents.items()}
    )
    context.index()
    return context


def event_body(body, event="test.1", trigger="", triggered=True):
    mode = "is_triggered_only = yes" if triggered else ""
    return f"country_event = {{ id = {event} {mode} trigger = {{ {trigger} }} option = {{ {body} }} }}"


def country_focus(body, tag="GER"):
    return f"focus_tree = {{ country = {{ factor = 0 modifier = {{ add = 10 tag = {tag} }} }} focus = {{ completion_reward = {{ {body} }} }} }}"


@pytest.mark.parametrize(
    "gate", ["tag = GER", "original_tag = GER", "OR = { tag = GER tag = BEL }"]
)
def test_starting_history_for_event_recipients(gate):
    context = context_for(
        {
            f"history/countries/{tag} - Test.txt": '2000.1.1 = { if = { limit = { has_dlc = "Designer" } set_technology = { naval_tech = 1 } } }'
            for tag in ("GER", "BEL")
        }
    )
    assert not check_variant_availability(
        event_body(reward(), trigger=gate), UNLOCKS, context
    )


@pytest.mark.parametrize(
    "history,expected",
    [
        ("set_technology = { naval_tech = 1 }", 0),
        ("1999.12.31 = { set_technology = { naval_tech = 1 } }", 0),
        ("2000.1.1 = { set_technology = { naval_tech = 1 } }", 0),
        ("2001.1.1 = { set_technology = { naval_tech = 1 } }", 1),
        ("if = { limit = { has_war = yes } set_technology = { naval_tech = 1 } }", 1),
        ("set_technology = { naval_tech = 1 } set_technology = { naval_tech = 0 }", 1),
        (
            'if = { limit = { NOT = { has_dlc = "Designer" } } set_technology = { naval_tech = 1 } }',
            1,
        ),
        (
            'if = { limit = { has_dlc = "Other" } set_technology = { naval_tech = 1 } }',
            1,
        ),
        (
            'if = { limit = { has_dlc = "Other" } } else_if = { limit = { has_dlc = "Designer" } set_technology = { naval_tech = 1 } }',
            1,
        ),
        (
            'if = { limit = { NOT = { has_dlc = "Designer" } } } else = { set_technology = { naval_tech = 1 } }',
            0,
        ),
    ],
)
def test_history_only_guaranteed_starting_grants(history, expected):
    context = context_for({"history/countries/GER - Test.txt": history})
    assert (
        len(
            check_variant_availability(
                event_body(reward(), trigger="tag = GER"), UNLOCKS, context
            )
        )
        == expected
    )


@pytest.mark.parametrize(
    "gate",
    ["NOT = { tag = GER }", "OR = { tag = GER has_war = yes }", "BEL = { tag = GER }"],
)
def test_weak_country_guards_do_not_borrow_history(gate):
    context = context_for(
        {"history/countries/GER - Test.txt": "set_technology = { naval_tech = 1 }"}
    )
    assert check_variant_availability(
        event_body(reward(), trigger=gate), UNLOCKS, context
    )


def test_mixed_recipients_keep_missing_partner_warning():
    context = context_for(
        {"history/countries/GER - Test.txt": "set_technology = { naval_tech = 1 }"}
    )
    body = event_body(reward(), trigger="OR = { tag = GER tag = POL }")
    assert len(check_variant_availability(body, UNLOCKS, context)) == 1


@pytest.mark.parametrize(
    "guard,expected",
    [
        (
            'if = { limit = { has_dlc = "Designer" } has_tech = naval_tech } else = { has_tech = armor_tech }',
            0,
        ),
        (
            'if = { limit = { NOT = { has_dlc = "Designer" } } has_tech = naval_tech }',
            1,
        ),
        ("if = { limit = { has_war = yes } has_tech = naval_tech }", 1),
        (
            'if = { limit = { has_dlc = "Designer" } OR = { has_tech = naval_tech has_war = yes } }',
            1,
        ),
        (
            'if = { limit = { has_dlc = "Designer" } GER = { has_tech = naval_tech } }',
            1,
        ),
    ],
)
def test_conditional_focus_requirements(guard, expected):
    body = (
        f"focus = {{ available = {{ {guard} }} completion_reward = {{ {reward()} }} }}"
    )
    assert len(check_variant_availability(body, UNLOCKS, context_for({}))) == expected


def test_category_ownership_applies_to_decision_rewards():
    context = context_for(
        {
            "common/decisions/categories/test.txt": "military = { allowed = { original_tag = GER } }",
            "history/countries/GER - Test.txt": "set_technology = { naval_tech = 1 }",
        }
    )
    body = "military = { build_ship = { remove_effect = { " + reward() + " } } }"
    assert not check_variant_availability(body, UNLOCKS, context)
    assert check_variant_availability(
        body.replace("military =", "unknown =", 1), UNLOCKS, context
    )


def test_event_call_chain_infers_all_partner_countries():
    body = event_body(reward(), event="test.3")
    docs = {
        "common/national_focus/test.txt": country_focus(
            "BEL = { country_event = test.1 } HOL = { country_event = { id = test.1 days = 1 } }"
        ),
        "events/test.txt": event_body("country_event = test.2")
        + event_body("country_event = test.3", event="test.2")
        + body,
        **{
            f"history/countries/{tag} - Test.txt": "set_technology = { naval_tech = 1 }"
            for tag in ("BEL", "HOL")
        },
    }
    context = context_for(docs)
    assert context.event_countries["test.3"] == {"BEL", "HOL"}
    assert not check_variant_availability(body, UNLOCKS, context)
    del docs["history/countries/HOL - Test.txt"]
    assert check_variant_availability(body, UNLOCKS, context_for(docs))


@pytest.mark.parametrize("scope", ["GER", "ROOT", "THIS"])
def test_same_country_event_scope_keeps_direct_grant(scope):
    body = event_body(
        "set_technology = { naval_tech = 1 } "
        + f"{scope} = {{ {reward(creator='creator = ROOT')} }}"
    )
    context = context_for(
        {
            "events/test.txt": body,
            "common/national_focus/test.txt": country_focus("country_event = test.1"),
        }
    )
    assert context.event_countries["test.1"] == {"GER"}
    assert not check_variant_availability(body, UNLOCKS, context)
    assert check_variant_availability(
        body.replace("set_technology = { naval_tech = 1 }", ""), UNLOCKS, context
    )


@pytest.mark.parametrize(
    "extra",
    [
        "common/scripted_effects/unknown.txt",
        "common/on_actions/unknown.txt",
    ],
)
def test_unknown_callers_prevent_single_country_assumption(extra):
    body = event_body(reward())
    docs = {
        "events/test.txt": body,
        "common/national_focus/test.txt": country_focus("country_event = test.1"),
        "history/countries/GER - Test.txt": "set_technology = { naval_tech = 1 }",
        extra: "some_effect = { country_event = test.1 }",
    }
    context = context_for(docs)
    assert None in context.event_countries["test.1"]
    assert check_variant_availability(body, UNLOCKS, context)


def test_random_event_pool_is_an_unknown_caller():
    context = context_for(
        {
            "events/test.txt": event_body(reward()),
            "common/national_focus/test.txt": country_focus("country_event = test.1"),
            "common/on_actions/test.txt": "on_actions = { on_daily = { random_events = { 1 = test.1 } } }",
        }
    )
    assert context.event_countries["test.1"] == {"GER", None}


def test_recursive_event_chain_without_entry_is_unknown():
    context = context_for(
        {
            "events/test.txt": event_body("country_event = test.2")
            + event_body("country_event = test.1", event="test.2")
        }
    )
    assert context.event_countries == {"test.1": {None}, "test.2": {None}}


def test_foreign_scope_and_technology_revocation_do_not_borrow_unlock():
    context = context_for(
        {"history/countries/GER - Test.txt": "set_technology = { naval_tech = 1 }"}
    )
    for body in (
        "BEL = { " + reward() + " }",
        "set_technology = { naval_tech = 0 }" + reward(),
    ):
        assert check_variant_availability(
            event_body(body, trigger="tag = GER"), UNLOCKS, context
        )


def test_history_file_does_not_borrow_its_later_grant():
    body = "2000.1.1 = { " + reward() + " set_technology = { naval_tech = 1 } }"
    context = context_for({"history/countries/GER - Test.txt": body})
    assert check_variant_availability(body, UNLOCKS, context, history_country="GER")


def test_context_is_loaded_for_staged_consumers_and_rescanned_for_history(
    tmp_path, write_path
):
    body = event_body(reward(), trigger="tag = GER")
    docs = {
        "events/test.txt": body,
        "history/countries/GER - Test.txt": "2000.1.1 = { set_technology = { naval_tech = 1 } }",
    }
    write_technology(tmp_path, write_path)
    write_path(
        tmp_path,
        "common/bookmarks/start.txt",
        "bookmarks = { bookmark = { date = 2000.1.1 } }",
    )
    for path, text in docs.items():
        write_path(tmp_path, path, text)
    validator = Validator(
        mod_path=str(tmp_path), staged_only=True, workers=1, use_colors=False
    )
    validator.staged_files = [str(tmp_path / "events/test.txt")]
    validator.run_validations()
    assert not validator._issues
    write_path(
        tmp_path,
        "history/countries/GER - Test.txt",
        "set_technology = { armor_tech = 1 }",
    )
    FileOpener.clear_cache()
    validator.staged_files = [str(tmp_path / "history/countries/GER - Test.txt")]
    validator.run_validations()
    assert len(validator._issues) == 1


def test_alternative_unlock_does_not_assume_one_designers_dlc():
    context = context_for(
        {
            "history/countries/GER - Test.txt": 'if = { limit = { has_dlc = "Designer" } set_technology = { naval_tech = 1 } }'
        }
    )
    assert check_variant_availability(
        event_body(reward(), trigger="tag = GER"),
        {"hull": {"naval_tech", "other_tech"}},
        context,
    )


def test_history_dates_apply_chronologically_after_undated_defaults():
    context = context_for(
        {
            "history/countries/GER - Test.txt": "2000.1.1 = { set_technology = { naval_tech = 0 } } 1999.1.1 = { set_technology = { naval_tech = 1 } } set_technology = { naval_tech = 1 }"
        }
    )
    assert check_variant_availability(
        event_body(reward(), trigger="tag = GER"), UNLOCKS, context
    )


def test_random_list_event_calls_keep_country_identity():
    context = context_for(
        {
            "events/test.txt": event_body(reward()),
            "common/national_focus/test.txt": country_focus(
                "random_list = { 10 = { country_event = test.1 } }"
            ),
        }
    )
    assert context.event_countries["test.1"] == {"GER"}
