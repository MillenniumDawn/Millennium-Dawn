"""Equipment-stat validation against the shipped aircraft and modules."""

from equipment_stats import build_equipment_stat_index
from shared.paths import REPO_ROOT
from validate_mios import Validator


def test_tekever_uav_detection_bonuses_reach_mission_stats(tmp_path):
    equipment = build_equipment_stat_index(str(REPO_ROOT))
    body = """
    equipment_type = { small_plane_suicide_airframe cv_small_plane_suicide_airframe }
    trait = {
        token = POR_tekever_eoir_gimbal_systems
        limit_to_equipment_type = { small_plane_suicide_airframe cv_small_plane_suicide_airframe }
        equipment_bonus = { surface_detection = 0.08 }
    }
    trait = {
        token = POR_tekever_unmanned_sigint
        limit_to_equipment_type = { small_plane_suicide_airframe cv_small_plane_suicide_airframe }
        equipment_bonus = { surface_detection = 0.12 }
    }
    """
    validator = Validator(str(tmp_path), workers=1)
    validator._check_org_trait_bonuses(
        "POR_tekever_aircraft_manufacturer", body, "f.txt", 0, equipment
    )
    assert not validator._issues
