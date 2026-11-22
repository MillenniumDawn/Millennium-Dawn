import os
import re
import sys
from collections import OrderedDict
from dataclasses import fields
from pathlib import Path
from typing import Any

import xlsxwriter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "types"))

from equipment import AllEquipmentStats, Equipment
from mio import MIO, BonusReport, EquipmentGroup

REPORT_ALL = "REPORT_ALL"
WEIGHTS: AllEquipmentStats = AllEquipmentStats(
    reliability=2,
    soft_attack=1.5,
    hard_attack=1.5,
    ap_attack=1.2,
    breakthrough=1.3,
    defense=1.3,
    air_attack=1.5,
    max_strength=1.5,
    lg_armor_piercing=1.2,
    lg_attack=1.5,
    hg_armor_piercing=1.2,
    hg_attack=1.5,
    torpedo_attack=1.5,
    anti_air_attack=1.5,
    carrier_size=5,
    air_defence=1.5,
    air_range=3,
    air_agility=1.5,
    air_superiority=1.3,
)


def print_usage():
    """Print command-line usage and list valid archetype equipment tags.

    This helper is used when no arguments are provided, or when users need a
    reminder of the accepted execution modes.
    """
    print("""
Tool for analyzing MIO balance.
Usage:
python mio.py <target_equipment_type>
    Outputs a report to the console describing a ranking of MIOs affecting the target equipment type.
python mio.py {REPORT_ALL} [output_file]
    Generates an Excel report for all MIOs, optionally specifying the output file.
Available equipment types:""".format(REPORT_ALL=REPORT_ALL))
    tags = list()
    for equipment in Equipment.get_equipment_index().values():
        if equipment.is_archetype:
            tags.append(equipment.tag)
    tags = sorted(tags)
    for tag in tags:
        print(f"     {tag}")


def report_specific_equipment_type(
    equ_type: Equipment, mios: dict[str, MIO], WEIGHTS: AllEquipmentStats
):
    """Print ranked MIO bonus reports for one equipment archetype.

    Args:
        equ_type: The target archetype Equipment object to analyze.
        mios: Mapping of MIO id to parsed MIO object to evaluate.

    The output is sorted by descending score and includes only MIOs that both
    apply to the selected equipment and contribute at least one non-empty bonus.
    """
    applies_to = dict[MIO, BonusReport]()
    for org_id, mio in mios.items():
        if equ_type.tag in mio.equipment_types:
            boost = mio.sum_bonuses_for(equ_type, WEIGHTS)
            if not boost.is_empty():
                applies_to[mio] = boost
    applies_to = dict(
        sorted(applies_to.items(), key=lambda item: item[1].score, reverse=True)
    )
    for mio, boost in applies_to.items():
        print(boost.to_pretty_display())


def spreadsheet_report(
    mios: dict[str, MIO], WEIGHTS: AllEquipmentStats, output_file: str
):
    """Generate an XLSX report for all MIOs across all archetype equipment.

    Args:
        mios: Mapping of MIO id to parsed MIO object to include in the report.
        WEIGHTS: The weight vector to use when calculating MIO scores.
        output_file: Requested output path for the report. If the provided path
            does not end with ``.xlsx``, the extension is replaced automatically.

    Report layout:
        - ``Cover`` sheet with report summary and archetypes lacking any bonus.
        - One sheet per archetype that has at least one non-empty MIO bonus.
        - Per-equipment rows sorted by descending total score.
        - For each visible stat: total value column followed by ``_avg`` column.
        - Stat columns with no values across all rows are omitted.
    """
    equipment_index = Equipment.get_equipment_index()
    archetypes = sorted(
        (equipment for equipment in equipment_index.values() if equipment.is_archetype),
        key=lambda equipment: equipment.tag,
    )

    workbook = OrderedDict()
    uncovered_equipment: list[str] = []

    total_mio_rows = 0
    for equipment in archetypes:
        applicable_reports: list[BonusReport] = []
        for mio in mios.values():
            if equipment.tag not in mio.equipment_types:
                continue

            report = mio.sum_bonuses_for(equipment, WEIGHTS)
            if report.is_empty():
                continue
            applicable_reports.append(report)

        applicable_reports.sort(key=lambda report: report.score, reverse=True)
        if not applicable_reports:
            uncovered_equipment.append(equipment.tag)
            continue

        total_mio_rows += len(applicable_reports)
        stat_headers = [field.name for field in fields(equipment.stats)]
        visible_stat_headers = [
            stat_name
            for stat_name in stat_headers
            if any(
                report.boost.get_or_default(stat_name, None) is not None
                for report in applicable_reports
            )
        ]

        stat_columns: list[object] = []
        for stat_name in visible_stat_headers:
            stat_columns.append(stat_name)
            stat_columns.append(f"{stat_name}_avg")

        header: list[object] = [
            "MIO",
            "Countries",
            "Score",
            "Contributing Traits",
            *stat_columns,
        ]

        rows: list[list[object]] = [header]
        for report in applicable_reports:
            stat_values: list[object] = []
            for stat_name in visible_stat_headers:
                stat_values.append(report.boost.get_or_default(stat_name, ""))
                stat_values.append(report.averaged_boost.get_or_default(stat_name, ""))

            countries_cell = ", ".join(report.mio.countries)
            if report.mio.required_flags:
                countries_cell += f"[{', '.join(report.mio.required_flags)}]"
            rows.append(
                [
                    report.mio.token,
                    countries_cell,
                    report.score,
                    report.n_traits,
                    *stat_values,
                ]
            )

        workbook[equipment.tag] = rows

    cover_rows: list[list[object]] = [
        ["MIO Balance Report"],
        [""],
        ["Total archetypes", len(archetypes)],
        [
            "Archetypes with at least one MIO bonus",
            len(archetypes) - len(uncovered_equipment),
        ],
        ["Archetypes without any MIO bonus", len(uncovered_equipment)],
        ["Total MIO rows across all equipment sheets", total_mio_rows],
        [""],
        ["Archetypes without MIO coverage"],
        ["Equipment Tag"],
    ]

    if uncovered_equipment:
        for equipment_tag in uncovered_equipment:
            cover_rows.append([equipment_tag])
    else:
        cover_rows.append(["(none)"])

    output_path = Path(output_file)
    if output_path.suffix.lower() != ".xlsx":
        output_path = output_path.with_suffix(".xlsx")
    resolved_output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def sanitize_sheet_name(name: str) -> str:
        """Normalize a worksheet name to satisfy Excel naming constraints.

        Returns:
            A safe sheet name with invalid characters replaced, trimmed to
            Excel's 31-character limit, and never empty.
        """
        sanitized = re.sub(r"[\\[\]:*?/\\]", "_", name).strip("'")
        if not sanitized:
            sanitized = "Sheet"
        return sanitized[:31]

    used_sheet_names: set[str] = set()

    def unique_sheet_name(name: str) -> str:
        """Return a collision-free worksheet name.

        Returns:
            A unique worksheet name, adding numeric suffixes when needed.
        """
        base = sanitize_sheet_name(name)
        candidate = base
        index = 2
        while candidate in used_sheet_names:
            suffix = f"_{index}"
            candidate = f"{base[: 31 - len(suffix)]}{suffix}"
            index += 1
        used_sheet_names.add(candidate)
        return candidate

    def compute_column_widths(
        rows: list[list[object]], max_width: int = 40
    ) -> list[int]:
        """Compute display widths from cell content for one sheet.

        Args:
            rows: 2D table data to scan.
            max_width: Hard cap to avoid oversized columns.

        Returns:
            Per-column widths with a small readability padding.
        """
        if not rows:
            return []

        width_by_col = [0] * max(len(row) for row in rows)
        for row in rows:
            for col_index, value in enumerate(row):
                value_text = str(value)
                width_by_col[col_index] = max(width_by_col[col_index], len(value_text))

        return [min(max_width, width) for width in width_by_col]

    def write_sheet(
        sheet: Any,
        rows: list[list[object]],
        header_format: Any,
        integer_format: Any,
        float_format: Any,
        regular_format: Any,
        number_columns: set[int],
        integer_columns: set[int],
        freeze_header: bool,
        widths_override: dict[int, int] | None = None,
    ):
        """Write one worksheet with formatting, widths, and numeric handling.

        Args:
            sheet: xlsxwriter worksheet object to populate.
            rows: 2D table where row 0 is treated as header.
            header_format: Cell format used for the header row.
            integer_format: Number format for integer-only columns.
            float_format: Number format for floating-point columns.
            regular_format: Default format for non-numeric cells.
            number_columns: Column indexes to render as float numbers.
            integer_columns: Column indexes to render as integer numbers.
            freeze_header: If true, freeze the top row and enable autofilter.
            widths_override: Optional minimum widths by column index.
        """
        if not rows:
            return

        if freeze_header:
            sheet.freeze_panes(1, 0)
            sheet.autofilter(0, 0, len(rows) - 1, len(rows[0]) - 1)

        widths = compute_column_widths(rows)
        if widths_override:
            for col_index, width in widths_override.items():
                if col_index < len(widths):
                    widths[col_index] = max(widths[col_index], width)

        for col_index, width in enumerate(widths):
            sheet.set_column(col_index, col_index, width)

        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                if row_index == 0:
                    sheet.write(row_index, col_index, value, header_format)
                    continue

                if col_index in integer_columns and isinstance(value, int):
                    sheet.write_number(row_index, col_index, value, integer_format)
                    continue

                if col_index in number_columns and isinstance(value, (int, float)):
                    sheet.write_number(row_index, col_index, float(value), float_format)
                    continue

                sheet.write(row_index, col_index, value, regular_format)

    with xlsxwriter.Workbook(str(output_path)) as xlsx_workbook:
        header_format = xlsx_workbook.add_format(
            {
                "bold": True,
                "bg_color": "#DDEBF7",
                "border": 1,
                "text_wrap": True,
                "valign": "vcenter",
            }
        )
        regular_format = xlsx_workbook.add_format({"border": 1})
        integer_format = xlsx_workbook.add_format({"border": 1, "num_format": "0"})
        float_format = xlsx_workbook.add_format({"border": 1, "num_format": "0.00"})

        cover_sheet = xlsx_workbook.add_worksheet(unique_sheet_name("Cover"))
        write_sheet(
            cover_sheet,
            cover_rows,
            header_format=header_format,
            integer_format=integer_format,
            float_format=float_format,
            regular_format=regular_format,
            number_columns={1},
            integer_columns={1},
            freeze_header=False,
            widths_override={0: 46, 1: 20},
        )

        for sheet_name, sheet_rows in workbook.items():
            sheet = xlsx_workbook.add_worksheet(unique_sheet_name(sheet_name))

            header_row = sheet_rows[0]
            score_col = header_row.index("Score")
            trait_count_col = header_row.index("Contributing Traits")
            stat_cols = {
                idx
                for idx, name in enumerate(header_row)
                if isinstance(name, str)
                and name not in {"MIO", "Countries", "Contributing Traits"}
            }

            write_sheet(
                sheet,
                sheet_rows,
                header_format=header_format,
                integer_format=integer_format,
                float_format=float_format,
                regular_format=regular_format,
                number_columns={score_col, *stat_cols},
                integer_columns={trait_count_col},
                freeze_header=True,
                widths_override={0: 32},
            )

    print(
        f"Wrote Excel report to {resolved_output_path} ({len(workbook)} equipment sheets)"
    )


if __name__ == "__main__":

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
        True,
    )
    if sys.argv[1] == REPORT_ALL:
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        else:
            output_file = "mio_report.xlsx"
        spreadsheet_report(mios, WEIGHTS, output_file)
    else:
        equipment = None
        try:
            equipment = Equipment.get_equipment_index()[sys.argv[1]]
        except KeyError:
            print(f"Error: Equipment type '{sys.argv[1]}' not found.")
            sys.exit(1)
        report_specific_equipment_type(equipment, mios, WEIGHTS)
