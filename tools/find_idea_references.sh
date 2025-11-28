#!/bin/bash

# Script to find unreferenced ideas from a given ideas file
# Usage: ./find_idea_references.sh <path_to_ideas_file> [--show-all]

start_time=$(date +%s)

show_all=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --show-all)
            show_all=true
            shift
            ;;
        *)
            IDEAS_FILE="$1"
            shift
            ;;
    esac
done

if [ -z "$IDEAS_FILE" ]; then
    echo "Usage: $0 <path_to_ideas_file> [--show-all]"
    echo "Example: $0 common/ideas/Greek.txt"
    echo "         $0 common/ideas/American.txt --show-all"
    echo "         $0 common/ideas/generic.txt"
    echo ""
    echo "Options:"
    echo "  --show-all    Show all ideas (including referenced ones)"
    echo "  Default:      Show only unreferenced ideas"
    exit 1
fi

if [ ! -f "$IDEAS_FILE" ]; then
    echo "Error: File '$IDEAS_FILE' not found!"
    exit 1
fi

echo "==========================================="
echo "IDEA REFERENCE ANALYZER"
echo "==========================================="
echo "Analyzing file: $IDEAS_FILE"
echo "File size: $(wc -l < "$IDEAS_FILE") lines"
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
if [ "$show_all" = true ]; then
    echo "Mode: Finding ALL references for ideas"
else
    echo "Mode: Finding UNREFERENCED ideas only"
fi
echo "==========================================="

echo "Extracting idea names from $IDEAS_FILE..."

# Find all idea names, excluding common HOI4 keywords
# Ideas are typically at 2+ tab indentation and not common keywords or country tags
idea_names=$(grep -E "^[[:space:]]{2,}[A-Za-z][A-Za-z0-9_]+ = \{" "$IDEAS_FILE" | \
             grep -v -E "(ideas|country|hidden_ideas|modifier|allowed|allowed_civil_war|cancel|on_add|on_remove|equipment_bonus|if|limit|OR|AND|NOT|picture|name|corvette|frigate|stealth_corvette|destroyer|battleship|carrier|submarine|light_tank|medium_tank|heavy_tank|modern_tank|chassis|airframe|engine|armor|gun|has_resources_rights|_chassis|_airframe) = \{" | \
             sed -E 's/^[[:space:]]+([A-Za-z][A-Za-z0-9_]+) = \{.*/\1/' | \
             grep -v -E "^[A-Z]{2,4}$" | \
             sort | uniq)

if [ -z "$idea_names" ]; then
    echo "No idea names found in $IDEAS_FILE"
    exit 1
fi

echo "Analyzing $(echo "$idea_names" | wc -l) ideas..."
echo ""

search_dirs=("common/events" "common/decisions" "common/national_focus" "history/countries" "common/scripted_effects" "events" "common/on_actions" "common/focuses" "common/country_leader" "common/ideas")

patterns=(
    "add_ideas"
    "remove_ideas"
    "has_idea"
    "swap_ideas"
    "modify_ideas"
    "add_timed_idea"
    "remove_timed_idea"
    "idea.*="
    "= idea"
)

total_references=0
unreferenced_ideas=()
referenced_ideas=()

for idea in $idea_names; do
    found_any=false
    idea_references=0

    for dir in "${search_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo -ne "\rSearching $idea in $dir...                    "
            for pattern in "${patterns[@]}"; do
                results=$(grep -r -n -i "$idea" "$dir" --include="*.txt" 2>/dev/null | grep -E "$pattern")

                if [ ! -z "$results" ]; then
                    found_any=true
                    count=$(echo "$results" | wc -l)
                    idea_references=$((idea_references + count))

                    if [ "$show_all" = true ]; then
                        if [ "$idea_references" -eq "$count" ]; then
                            echo -e "\nReferenced idea: $idea"
                            echo "----------------------------------------"
                        fi
                        echo "  In $dir (pattern: $pattern):"
                        echo "$results" | while IFS= read -r line; do
                            file=$(echo "$line" | cut -d: -f1)
                            line_num=$(echo "$line" | cut -d: -f2)
                            content=$(echo "$line" | cut -d: -f3-)
                            echo "    $file:$line_num -> $(echo "$content" | xargs)"
                        done
                    fi
                fi
            done
        fi
    done

    if [ "$found_any" = false ]; then
        unreferenced_ideas+=("$idea")
        echo -e "\rUNREFERENCED: $idea                              "
    else
        referenced_ideas+=("$idea")
        total_references=$((total_references + idea_references))
        if [ "$show_all" = true ]; then
            echo "  Total references for $idea: $idea_references"
            echo ""
        else
            echo -e "\rReferenced: $idea ($idea_references refs)                    "
        fi
    fi
done

echo -e "\r                                                      "

echo ""
echo "==========================================="
echo "Summary:"
echo "  Total ideas analyzed: $(echo "$idea_names" | wc -l)"
echo "  Referenced ideas: ${#referenced_ideas[@]}"
echo "  UNREFERENCED ideas: ${#unreferenced_ideas[@]}"
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

if [ ${#unreferenced_ideas[@]} -gt 0 ]; then
    echo ""
    echo "UNREFERENCED IDEAS (consider removing):"
    for idea in "${unreferenced_ideas[@]}"; do
        echo "  - $idea"
    done
else
    echo ""
    echo "All ideas are referenced somewhere in the codebase!"
fi

echo ""
read -p "Generate detailed report file? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$show_all" = true ]; then
        report_file="all_idea_references_$(basename "$IDEAS_FILE" .txt)_$(date +%Y%m%d_%H%M%S).txt"
    else
        report_file="unreferenced_ideas_$(basename "$IDEAS_FILE" .txt)_$(date +%Y%m%d_%H%M%S).txt"
    fi

    echo "Generating detailed report: $report_file"

    {
        if [ "$show_all" = true ]; then
            echo "All Idea References Report"
        else
            echo "Unreferenced Ideas Report"
        fi
        echo "=========================="
        echo "Source file: $IDEAS_FILE"
        echo "File size: $(wc -l < "$IDEAS_FILE") lines"
        echo "Analysis started: $(date -d @$start_time '+%Y-%m-%d %H:%M:%S')"
        echo "Analysis completed: $(date '+%Y-%m-%d %H:%M:%S')"
        if [ $minutes -gt 0 ]; then
            echo "Execution time: ${minutes}m ${seconds}s"
        else
            echo "Execution time: ${seconds}s"
        fi
        echo ""
        echo "Summary:"
        echo "  Total ideas analyzed: $(echo "$idea_names" | wc -l)"
        echo "  Referenced ideas: ${#referenced_ideas[@]}"
        echo "  Unreferenced ideas: ${#unreferenced_ideas[@]}"
        echo "  Total references found: $total_references"
        echo ""

        if [ ${#unreferenced_ideas[@]} -gt 0 ]; then
            echo "UNREFERENCED IDEAS:"
            echo "==================="
            for idea in "${unreferenced_ideas[@]}"; do
                echo "- $idea"
            done
            echo ""
        fi

        if [ "$show_all" = true ] && [ ${#referenced_ideas[@]} -gt 0 ]; then
            echo "REFERENCED IDEAS:"
            echo "================="

            for idea in "${referenced_ideas[@]}"; do
                echo ""
                echo "References for: $idea"
                echo "$(printf '=%.0s' {1..40})"

                found_any=false
                for dir in "${search_dirs[@]}"; do
                    if [ -d "$dir" ]; then
                        for pattern in "${patterns[@]}"; do
                            results=$(grep -r -n -i "$idea" "$dir" --include="*.txt" 2>/dev/null | grep -E "$pattern")
                            if [ ! -z "$results" ]; then
                                found_any=true
                                echo "In $dir (pattern: $pattern):"
                                echo "$results" | while IFS= read -r line; do
                                    file=$(echo "$line" | cut -d: -f1)
                                    line_num=$(echo "$line" | cut -d: -f2)
                                    content=$(echo "$line" | cut -d: -f3-)
                                    echo "  $file:$line_num -> $(echo "$content" | xargs)"
                                done
                                echo ""
                            fi
                        done
                    fi
                done
            done
        fi
    } > "$report_file"

    echo "Report saved to: $report_file"
fi