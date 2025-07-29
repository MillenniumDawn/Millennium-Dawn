#!/bin/bash

# Script to find unreferenced scripted localisation names from a given scripted localisation file
# Usage: ./find_scripted_loc_references.sh <path_to_scripted_loc_file> [--show-all]

start_time=$(date +%s)

show_all=false
no_report=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --show-all)
            show_all=true
            shift
            ;;
        --no-report)
            no_report=true
            shift
            ;;
        *)
            SCRIPTED_LOC_FILE="$1"
            shift
            ;;
    esac
done

if [ -z "$SCRIPTED_LOC_FILE" ]; then
    echo "Usage: $0 <path_to_scripted_loc_file> [--show-all] [--no-report]"
    echo "Example: $0 common/scripted_localisation/LBA_scripted_localisation.txt"
    echo "         $0 common/scripted_localisation/ENG_scripted_localisation.txt --show-all"
    echo "         $0 common/scripted_localisation/BRM_scripted_localisation.txt --no-report"
    echo ""
    echo "This script searches for:"
    echo "  - Direct name references in interface, events, decisions, etc."
    echo "  - Bracketed references [name] in localisation files (.yml)"
    echo ""
    echo "Options:"
    echo "  --show-all    Show all scripted localisation names (including referenced ones)"
    echo "  --no-report   Skip the prompt to generate a detailed report file"
    echo "  Default:      Show only unreferenced scripted localisation names"
    exit 1
fi

if [ ! -f "$SCRIPTED_LOC_FILE" ]; then
    echo "Error: File '$SCRIPTED_LOC_FILE' not found!"
    exit 1
fi

echo "==========================================="
echo "SCRIPTED LOCALISATION REFERENCE ANALYZER"
echo "==========================================="
echo "Analyzing file: $SCRIPTED_LOC_FILE"
echo "File size: $(wc -l < "$SCRIPTED_LOC_FILE") lines"
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
if [ "$show_all" = true ]; then
    echo "Mode: Finding ALL references for scripted localisation names"
else
    echo "Mode: Finding UNREFERENCED scripted localisation names only"
fi
echo "==========================================="

echo "Extracting scripted localisation names from $SCRIPTED_LOC_FILE..."

# Find all "name = <value>" lines in defined_text blocks
scripted_loc_names=$(grep -E "^[[:space:]]*name = [A-Za-z][A-Za-z0-9_]*[[:space:]]*$" "$SCRIPTED_LOC_FILE" | \
                     sed -E 's/^[[:space:]]*name = ([A-Za-z][A-Za-z0-9_]*)[[:space:]]*$/\1/' | \
                     sort | uniq)

if [ -z "$scripted_loc_names" ]; then
    echo "No scripted localisation names found in $SCRIPTED_LOC_FILE"
    exit 1
fi

echo "Analyzing $(echo "$scripted_loc_names" | wc -l) scripted localisation names..."
echo ""

# Directories to search for references
search_dirs=("interface" "localisation" "events" "common/decisions" "common/national_focus" "common/scripted_effects" "common/on_actions" "common/focuses" "common/scripted_guis" "gfx/interface")

# Patterns to search for scripted localisation references
patterns=(
    "GetScriptedLocalisation"
    "\\[.*\\]"
    "= .*"
    "text.*="
    "localisation.*="
    '".*"'
    "'.*'"
)

total_references=0
unreferenced_names=()
referenced_names=()

for name in $scripted_loc_names; do
    found_any=false
    name_references=0

        for dir in "${search_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo -ne "\rSearching $name in $dir...                    "

            # Search for different patterns depending on directory
            if [[ "$dir" == "localisation"* ]]; then
                # In localisation files, search for [name] pattern
                results=$(grep -r -n "\\[$name\\]" "$dir" --include="*.yml" 2>/dev/null)
            else
                # In other files, search for the exact name in various contexts
                results=$(grep -r -n "$name" "$dir" --include="*.txt" --include="*.gui" --include="*.gfx" --include="*.yml" 2>/dev/null | \
                         grep -v "name = $name" | \
                         grep -E "$name")
            fi

            if [ ! -z "$results" ]; then
                found_any=true
                count=$(echo "$results" | wc -l)
                name_references=$((name_references + count))

                if [ "$show_all" = true ]; then
                    if [ "$name_references" -eq "$count" ]; then
                        echo -e "\nReferenced scripted localisation: $name"
                        echo "----------------------------------------"
                    fi
                    if [[ "$dir" == "localisation"* ]]; then
                        echo "  In $dir (bracketed pattern):"
                    else
                        echo "  In $dir:"
                    fi
                    echo "$results" | while IFS= read -r line; do
                        file=$(echo "$line" | cut -d: -f1)
                        line_num=$(echo "$line" | cut -d: -f2)
                        content=$(echo "$line" | cut -d: -f3-)
                        echo "    $file:$line_num -> $(echo "$content" | xargs)"
                    done
                fi
            fi
        fi
    done

    if [ "$found_any" = false ]; then
        unreferenced_names+=("$name")
        echo -e "\rUNREFERENCED: $name                              "
    else
        referenced_names+=("$name")
        total_references=$((total_references + name_references))
        if [ "$show_all" = true ]; then
            echo "  Total references for $name: $name_references"
            echo ""
        else
            echo -e "\rReferenced: $name ($name_references refs)                    "
        fi
    fi
done

echo -e "\r                                                      "

echo ""
echo "==========================================="
echo "Summary:"
echo "  Total scripted localisation names analyzed: $(echo "$scripted_loc_names" | wc -l)"
echo "  Referenced names: ${#referenced_names[@]}"
echo "  UNREFERENCED names: ${#unreferenced_names[@]}"
echo "  Total references found: $total_references"

end_time=$(date +%s)
execution_time=$((end_time - start_time))
minutes=$((execution_time / 60))
seconds=$((execution_time % 60))

echo ""
echo "Execution completed at: $(date '+%Y-%m-%d %H:%M:%S')"
if [ $minutes -gt 0 ]; then
    echo "Total execution time: ${minutes}m ${seconds}s"
else
    echo "Total execution time: ${seconds}s"
fi
echo "==========================================="

if [ ${#unreferenced_names[@]} -gt 0 ]; then
    echo ""
    echo "UNREFERENCED SCRIPTED LOCALISATION NAMES (consider removing):"
    for name in "${unreferenced_names[@]}"; do
        echo "  - $name"
    done
else
    echo ""
    echo "All scripted localisation names are referenced somewhere in the codebase!"
fi

if [ "$no_report" = false ]; then
    echo ""
    read -p "Generate detailed report file? (y/n): " -n 1 -r
    echo
fi

if [[ "$no_report" = false && $REPLY =~ ^[Yy]$ ]]; then
    if [ "$show_all" = true ]; then
        report_file="all_scripted_loc_references_$(basename "$SCRIPTED_LOC_FILE" .txt)_$(date +%Y%m%d_%H%M%S).txt"
    else
        report_file="unreferenced_scripted_loc_$(basename "$SCRIPTED_LOC_FILE" .txt)_$(date +%Y%m%d_%H%M%S).txt"
    fi

    echo "Generating detailed report: $report_file"

    {
        if [ "$show_all" = true ]; then
            echo "All Scripted Localisation References Report"
        else
            echo "Unreferenced Scripted Localisation Names Report"
        fi
        echo "============================================="
        echo "Source file: $SCRIPTED_LOC_FILE"
        echo "File size: $(wc -l < "$SCRIPTED_LOC_FILE") lines"
        echo "Analysis started: $(date -d @$start_time '+%Y-%m-%d %H:%M:%S')"
        echo "Analysis completed: $(date '+%Y-%m-%d %H:%M:%S')"
        if [ $minutes -gt 0 ]; then
            echo "Execution time: ${minutes}m ${seconds}s"
        else
            echo "Execution time: ${seconds}s"
        fi
        echo ""
        echo "Summary:"
        echo "  Total scripted localisation names analyzed: $(echo "$scripted_loc_names" | wc -l)"
        echo "  Referenced names: ${#referenced_names[@]}"
        echo "  Unreferenced names: ${#unreferenced_names[@]}"
        echo "  Total references found: $total_references"
        echo ""

        if [ ${#unreferenced_names[@]} -gt 0 ]; then
            echo "UNREFERENCED SCRIPTED LOCALISATION NAMES:"
            echo "========================================="
            for name in "${unreferenced_names[@]}"; do
                echo "- $name"
            done
            echo ""
        fi

        if [ "$show_all" = true ] && [ ${#referenced_names[@]} -gt 0 ]; then
            echo "REFERENCED SCRIPTED LOCALISATION NAMES:"
            echo "======================================="

            for name in "${referenced_names[@]}"; do
                echo ""
                echo "References for: $name"
                echo "$(printf '=%.0s' {1..40})"

                found_any=false
                for dir in "${search_dirs[@]}"; do
                    if [ -d "$dir" ]; then
                        # Search for different patterns depending on directory
                        if [[ "$dir" == "localisation"* ]]; then
                            # In localisation files, search for [name] pattern
                            results=$(grep -r -n "\\[$name\\]" "$dir" --include="*.yml" 2>/dev/null)
                        else
                            # In other files, search for the exact name in various contexts
                            results=$(grep -r -n "$name" "$dir" --include="*.txt" --include="*.gui" --include="*.gfx" --include="*.yml" 2>/dev/null | \
                                     grep -v "name = $name" | \
                                     grep -E "$name")
                        fi
                        if [ ! -z "$results" ]; then
                            found_any=true
                            if [[ "$dir" == "localisation"* ]]; then
                                echo "In $dir (bracketed pattern):"
                            else
                                echo "In $dir:"
                            fi
                            echo "$results" | while IFS= read -r line; do
                                file=$(echo "$line" | cut -d: -f1)
                                line_num=$(echo "$line" | cut -d: -f2)
                                content=$(echo "$line" | cut -d: -f3-)
                                echo "  $file:$line_num -> $(echo "$content" | xargs)"
                            done
                            echo ""
                        fi
                    fi
                done
            done
        fi
    } > "$report_file"

    echo "Report saved to: $report_file"
fi