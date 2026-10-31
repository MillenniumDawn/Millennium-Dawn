"""Integration coverage for each named equipment variant consumer shape."""

import pytest
from shared.suite import write_tree
from validate_oob_units import Validator

_CONSUMERS = {
    "air wing": (
        "air_wings = { 696 = { REQUEST_TYPE = { owner = UKR creator = SOV "
        'amount = 1 version_name = "MiG-X" } } }'
    ),
    "forced equipment": (
        "units = { division = { force_equipment_variants = { REQUEST_TYPE = { "
        'owner = UKR creator = SOV version_name = "MiG-X" } } } }'
    ),
    "serialized forced equipment": (
        'create_unit = { division = "division_template = \\"Air\\" '
        "force_equipment_variants = { REQUEST_TYPE = { creator = SOV "
        'version_name = \\"MiG-X\\" } }" owner = UKR }'
    ),
    "stockpile": (
        "instant_effect = { add_equipment_to_stockpile = { type = REQUEST_TYPE "
        'producer = SOV variant_name = "MiG-X" amount = 1 } }'
    ),
    "production equipment": (
        "instant_effect = { add_equipment_production = { equipment = { "
        'type = REQUEST_TYPE creator = SOV version_name = "MiG-X" } amount = 1 } }'
    ),
    "production outer producer": (
        "instant_effect = { add_equipment_production = { producer = SOV "
        'equipment = { type = REQUEST_TYPE variant_name = "MiG-X" } amount = 1 } }'
    ),
}


@pytest.mark.parametrize("consumer", _CONSUMERS.values(), ids=_CONSUMERS)
@pytest.mark.parametrize(
    "equipment,errors",
    [
        ("medium_plane_airframe_1", 0),
        ("medium_plane_fighter_airframe_1", 1),
        ("small_plane_airframe_1", 1),
    ],
    ids=["matching type", "wrong subtype", "wrong size"],
)
def test_named_consumer_identity(tmp_path, consumer, equipment, errors):
    consumer_path = "history/units/UKR_2000_bba.txt"
    write_tree(
        tmp_path,
        {
            "history/countries/SOV - Russia.txt": (
                '2000.1.1 = { if = { limit = { has_dlc = "By Blood Alone" } '
                'create_equipment_variant = { name = "MiG-X" '
                "type = medium_plane_airframe_1 } } }"
            ),
            consumer_path: consumer.replace("REQUEST_TYPE", equipment),
        },
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.validate_oob_variant_references()

    assert validator.errors_found == errors
    assert len(validator._issues) == errors
    if errors:
        assert validator._issues[0].file == consumer_path
        assert validator._issues[0].category == (
            "NAMED VARIANT: name exists for a different equipment type"
        )
