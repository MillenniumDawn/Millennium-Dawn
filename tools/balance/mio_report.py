from dataclasses import dataclass, field, fields
from pathlib import Path
import sys
import os

_UTILS_DIR = os.path.join(os.path.dirname(__file__), "..", "utils")
_UTILS_DIR = os.path.abspath(_UTILS_DIR)
if _UTILS_DIR not in sys.path:
    sys.path.insert(0, _UTILS_DIR)

_TYPES_DIR = os.path.join(os.path.dirname(__file__), "..", "types")
_TYPES_DIR = os.path.abspath(_TYPES_DIR)
if _TYPES_DIR not in sys.path:
    sys.path.insert(0, _TYPES_DIR)

from equipment import Equipment
from mio import EquipmentGroup, MIO, BonusReport

if __name__ == "__main__":
    REPORT_ALL = "REPORT_ALL"
    def print_usage():
        print("""
Tool for analyzing MIO balance.
Usage:
python mio.py <target_equipment_type>
    Outputs a report to the console describing a ranking of MIOs affecting the target equipment type.
python mio.py {REPORT_ALL} [output_file]
    Generates an ODS report for all MIOs, optionally specifying the output file.
Available equipment types:""".format(REPORT_ALL=REPORT_ALL))
        tags = list()
        for equipment in Equipment.get_equipment_index().values():
            if equipment.is_archetype:
                tags.append(equipment.tag)
        tags = sorted(tags)
        for tag in tags:
            print(f"     {tag}")
    
    def report_specific_equipment_type(equ_type: Equipment, mios: dict[str, MIO]):
        applies_to = dict[MIO, BonusReport]()
        for org_id, mio in mios.items():
            if equ_type.tag in mio.equipment_types:
                boost = mio.sum_bonuses_for(equ_type)
                if not boost.is_empty():
                    applies_to[mio] = boost
        applies_to = dict(sorted(applies_to.items(), key=lambda item: item[1].score, reverse=True))
        for mio, boost in applies_to.items():
            print(boost.to_pretty_display())
    
    def spreadsheet_report(mios: dict[str, MIO], output_file: str):
        """Generate an ODS (Open Document SpreadSheet) report for all MIOs."""
        pass
    
    ############################
    ### Main execution block ###
    ############################
    
    if len(sys.argv) == 1:
        print_usage()
        sys.exit(1)
    
    equipment_groups = EquipmentGroup.from_file()
    mios = MIO.from_directory(
        "common/military_industrial_organization/organizations",
        equipment_groups,
    )
    print(f"Parsed {len(mios)} MIO organizations")
    
    if sys.argv[1] == REPORT_ALL:
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        else:
            output_file = "mio_report.ods"
        spreadsheet_report(mios, output_file)
    else:
        equipment = None
        try:
            equipment = Equipment.get_equipment_index()[sys.argv[1]]
        except KeyError:
            print(f"Error: Equipment type '{sys.argv[1]}' not found.")
            sys.exit(1)
        report_specific_equipment_type(equipment, mios)
