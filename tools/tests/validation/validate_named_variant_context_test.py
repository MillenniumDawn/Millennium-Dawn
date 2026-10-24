"""Review blockers: run from the checkout with ``pytest -c pyproject.toml PATH``."""

import pytest
import validate_oob_units as v


def definition(equipment):
    return f'create_equipment_variant = {{ name = "Review-X" type = {equipment} }}'


def stockpile(equipment):
    return (
        f"add_equipment_to_stockpile = {{ type = {equipment} "
        'producer = SOV variant_name = "Review-X" amount = 1 }'
    )


MEDIUM = "medium_plane_airframe_1"
SMALL = "small_plane_airframe_1"
WRONG = "wrong_variant_type"
UNKNOWN = "unknown_named_variant"
SOV = "history/countries/SOV - Russia.txt"
UKR = "history/countries/UKR - Ukraine.txt"
BBA = 'limit = { has_dlc = "By Blood Alone" }'

CASES = {
    "future-only definition cannot prove a startup type mismatch": (
        [(SOV, f"2017.1.1 = {{ {definition(MEDIUM)} }}")],
        UKR,
        f"2000.1.1 = {{ {stockpile(SMALL)} }}",
        [UNKNOWN],
    ),
    "future exact definition cannot hide a startup mismatch": (
        [
            (
                SOV,
                f"2000.1.1 = {{ {definition(MEDIUM)} }} "
                f"2017.1.1 = {{ {definition(SMALL)} }}",
            )
        ],
        UKR,
        f"2000.1.1 = {{ {stockpile(SMALL)} }}",
        [WRONG],
    ),
    "nested literal country overrides history filename": (
        [(SOV, f"2000.1.1 = {{ UKR = {{ {definition(MEDIUM)} }} }}")],
        UKR,
        stockpile(SMALL),
        [UNKNOWN],
    ),
    "explicit foreign event scope cannot satisfy another producer": (
        [
            (SOV, definition(MEDIUM)),
            (
                "events/Review.txt",
                f"country_event = {{ immediate = {{ UKR = {{ {definition(SMALL)} }} }} }}",
            ),
        ],
        UKR,
        stockpile(SMALL),
        [WRONG],
    ),
    "unscoped exact type cannot prove producer identity": (
        [
            (SOV, definition(MEDIUM)),
            ("events/Review.txt", definition(SMALL)),
        ],
        UKR,
        stockpile(SMALL),
        [UNKNOWN],
    ),
    "scripted dynamic type makes a static mismatch uncertain": (
        [
            (SOV, definition(MEDIUM)),
            (
                "common/scripted_effects/Review.txt",
                f"review_effect = {{ {definition('$TYPE$')} }}",
            ),
        ],
        UKR,
        stockpile(SMALL),
        [UNKNOWN],
    ),
    "compound DLC else does not imply missing DLC": (
        [
            (
                SOV,
                f'2000.1.1 = {{ if = {{ limit = {{ has_dlc = "By Blood Alone" '
                f"has_country_flag = special }} {definition(MEDIUM)} }} "
                f"else = {{ {definition(SMALL)} }} }}",
            )
        ],
        "history/units/UKR_2000_bba.txt",
        stockpile(SMALL),
        "unresolved with uncertain DLC",
    ),
    "NOT under OR is not an unconditional DLC gate": (
        [
            (
                SOV,
                f"2000.1.1 = {{ if = {{ limit = {{ OR = {{ NOT = {{ "
                f'has_dlc = "By Blood Alone" }} has_country_flag = special }} }} '
                f"{definition(SMALL)} }} }}",
            )
        ],
        "history/units/UKR_2000_bba.txt",
        stockpile(SMALL),
        "skip uncertain DLC match",
    ),
    "else_if cannot satisfy a consumer in the prior true branch": (
        [
            (
                SOV,
                f'2000.1.1 = {{ if = {{ limit = {{ has_dlc = "No Step Back" }} '
                f"{definition(MEDIUM)} }} else_if = {{ {BBA} {definition(SMALL)} }} }}",
            )
        ],
        "history/units/UKR_2000_nsb.txt",
        stockpile(SMALL),
        [WRONG],
    ),
    "same-line references retain their own DLC offsets": (
        [
            (
                SOV,
                f"2000.1.1 = {{ if = {{ {BBA} {definition(MEDIUM)} }} "
                f"else = {{ {definition(SMALL)} }} }}",
            )
        ],
        "history/units/UKR_2000.txt",
        f"if = {{ {BBA} {stockpile(SMALL)} }} else = {{ {stockpile(MEDIUM)} }}",
        [WRONG, WRONG],
    ),
    "literal legacy air wing is also a consumer": (
        [(SOV, definition("AS_Fighter2"))],
        "history/units/UKR_2000_nonbba.txt",
        "air_wings = { 696 = { AS_Fighter1 = { owner = UKR creator = SOV "
        'version_name = "Review-X" amount = 1 } } }',
        [WRONG],
    ),
}


@pytest.mark.parametrize(
    "raw_sources,path,consumer,expected", CASES.values(), ids=CASES
)
def test_context_review_blockers(raw_sources, path, consumer, expected):
    sources = [(rel, v.created_variant_spans(text)) for rel, text in raw_sources]
    by_tag, wildcard = v.build_variant_name_index(sources)
    index = v.build_variant_dlc_index(sources)
    if expected in (
        "unresolved with uncertain DLC",
        "skip uncertain DLC match",
    ):
        candidates = [
            context
            for equipment, _, context, _ in index[0]["SOV"]
            if equipment == SMALL
        ]
        assert candidates
        assert all(context.get("By Blood Alone") is not False for context in candidates)
        assert all(context.get("__uncertain__") for context in candidates)
        expected = [UNKNOWN] if expected == "unresolved with uncertain DLC" else []
    found = v.check_named_variant_refs(
        consumer,
        by_tag,
        wildcard,
        source_path=path,
        variant_dlc_index=index,
    )
    assert [finding.kind for finding in found] == expected


@pytest.mark.parametrize(
    "scope",
    [
        "random_country = { limit = { tag = GER }",
        "event_target:buyer = {",
    ],
    ids=["country iterator", "dynamic country target"],
)
def test_dynamic_history_scope_does_not_inherit_filename_producer(scope):
    source = (
        "history/countries/SOV - Russia.txt",
        f"2000.1.1 = {{ {scope} {definition(MEDIUM)} }} }}",
    )
    sources = [(source[0], v.created_variant_spans(source[1]))]
    index = v.build_variant_dlc_index(sources)

    assert not index[0].get("SOV")
    assert len(index[1]) == 1
    equipment, name, context, _ = index[1][0]
    assert (equipment, name) == (MEDIUM, "Review-X")
    assert context.get(v._UNCERTAIN_PRODUCER_CONTEXT)

    found = v.check_named_variant_refs(
        stockpile(SMALL),
        *v.build_variant_name_index(sources),
        source_path="history/units/UKR_2000_bba.txt",
        variant_dlc_index=index,
    )
    assert [finding.kind for finding in found] == [UNKNOWN]


def test_dynamic_meta_effect_type_is_not_truncated_to_a_literal_prefix():
    sources = [
        (
            "history/countries/SOV - Russia.txt",
            v.created_variant_spans(f"2000.1.1 = {{ {definition(MEDIUM)} }}"),
        ),
        (
            "common/scripted_effects/Review.txt",
            v.created_variant_spans(
                "review_dynamic = { meta_effect = { text = { "
                f"{definition('small_plane_airframe_[LEVEL]')} "
                '} LEVEL = "[?selected_level]" } }'
            ),
        ),
    ]
    index = v.build_variant_dlc_index(sources)

    assert any(
        equipment is None and name == "Review-X" for equipment, name, _, _ in index[1]
    )
    found = v.check_named_variant_refs(
        stockpile(SMALL),
        *v.build_variant_name_index(sources),
        source_path="events/Review.txt",
        variant_dlc_index=index,
    )
    assert [finding.kind for finding in found] == [UNKNOWN]
