#!/bin/bash
###############################################################################
# Run all validation scripts in parallel
# Usage:
#   ./run_all_validators.sh [--staged] [--strict] [--no-color]
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

STAGED_FLAG=""
STRICT_FLAG=""
COLOR_FLAG=""

for arg in "$@"; do
    case $arg in
        --staged)   STAGED_FLAG="--staged"  ;;
        --strict)   STRICT_FLAG="--strict"  ;;
        --no-color)
            COLOR_FLAG="--no-color"
            RED=''; GREEN=''; YELLOW=''; CYAN=''; NC=''
            ;;
    esac
done

OUTPUT_DIR=$(mktemp -d)
trap 'rm -rf "$OUTPUT_DIR"' EXIT

echo -e "${CYAN}================================================================================${NC}"
echo -e "${CYAN}Running Millennium Dawn Validation Suite (parallel)${NC}"
echo -e "${CYAN}================================================================================${NC}"
echo ""

# name -> script filename
declare -A SCRIPTS=(
    [variables]="validate_variables.py"
    [scripted-localisation]="validate_scripted_localisation.py"
    [cosmetic-tags]="validate_cosmetic_tags.py"
    [decisions]="validate_decisions.py"
    [localisation]="validate_localisation.py"
    [events]="validate_events.py"
    [history-techs]="validate_history_techs.py"
    [unused-scripted]="validate_unused_scripted.py"
    [oob-units]="validate_oob_units.py"
    [defines]="validate_defines.py"
    [ai-navy]="validate_ai_navy.py"
    [ai-equipment]="validate_ai_equipment.py"
    [ai-roles]="validate_ai_roles.py"
    [factions]="validate_factions.py"
)

# name -> human-readable label
declare -A LABELS=(
    [variables]="Variable and event target validation"
    [scripted-localisation]="Scripted localisation validation"
    [cosmetic-tags]="Cosmetic tag validation"
    [decisions]="Decision validation"
    [localisation]="Localisation validation"
    [events]="Event validation"
    [history-techs]="History technology dependency validation"
    [unused-scripted]="Unused scripted effects/triggers validation"
    [oob-units]="OOB unit name validation"
    [defines]="Defines validation (dead/namespace/duplicate)"
    [ai-navy]="AI navy validation (ship types, missions, fleet refs)"
    [ai-equipment]="AI equipment coverage validation (naval/land/air)"
    [ai-roles]="AI role reference validation"
    [factions]="Faction system validation"
)

# Ordered for consistent output
ORDERED=(variables scripted-localisation cosmetic-tags decisions localisation events history-techs unused-scripted oob-units defines ai-navy ai-equipment ai-roles factions)

declare -A PIDS=()

# Launch all validators in parallel
for name in "${ORDERED[@]}"; do
    python3 tools/validation/"${SCRIPTS[$name]}" $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG \
        --output "$OUTPUT_DIR/$name.txt" > /dev/null 2>&1 &
    PIDS[$name]=$!
done

# Collect results in order
TOTAL_ERRORS=0
for name in "${ORDERED[@]}"; do
    wait "${PIDS[$name]}"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ ${LABELS[$name]}${NC}"
        TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
    else
        echo -e "${GREEN}✓ ${LABELS[$name]}${NC}"
    fi
done

echo ""
echo -e "${CYAN}================================================================================${NC}"
if [ $TOTAL_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL VALIDATIONS PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ VALIDATION FAILED — ${TOTAL_ERRORS} script(s) reported issues${NC}"
    echo ""
    echo -e "${YELLOW}Detailed reports saved to: $OUTPUT_DIR${NC}"
    trap - EXIT  # keep temp dir so the user can read reports
    [ -n "$STRICT_FLAG" ] && exit 1 || exit 0
fi
