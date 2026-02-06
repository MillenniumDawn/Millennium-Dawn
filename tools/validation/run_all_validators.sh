#!/bin/bash
###############################################################################
# Run all validation scripts
# This script runs all available validators and reports results
# Usage:
#   ./run_all_validators.sh [--staged] [--strict] [--no-color]
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
STAGED_FLAG=""
STRICT_FLAG=""
COLOR_FLAG=""

for arg in "$@"; do
    case $arg in
        --staged)
            STAGED_FLAG="--staged"
            shift
            ;;
        --strict)
            STRICT_FLAG="--strict"
            shift
            ;;
        --no-color)
            COLOR_FLAG="--no-color"
            RED=''
            GREEN=''
            YELLOW=''
            CYAN=''
            NC=''
            shift
            ;;
    esac
done

echo -e "${CYAN}================================================================================${NC}"
echo -e "${CYAN}Running Millennium Dawn Validation Suite${NC}"
echo -e "${CYAN}================================================================================${NC}"
echo ""

TOTAL_ERRORS=0

# 1. Run variable validation
echo -e "${CYAN}[1/2] Running variable and event target validation...${NC}"
python3 tools/validation/validate_variables.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/variable-validation.txt
VAR_EXIT=$?
if [ $VAR_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Variable validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Variable validation passed${NC}"
fi
echo ""

# 2. Run scripted localisation validation
echo -e "${CYAN}[2/2] Running scripted localisation validation...${NC}"
python3 tools/validation/validate_scripted_localisation.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/scripted-loc-validation.txt
LOC_EXIT=$?
if [ $LOC_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Scripted localisation validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Scripted localisation validation passed${NC}"
fi
echo ""

# Summary
echo -e "${CYAN}================================================================================${NC}"
if [ $TOTAL_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL VALIDATIONS PASSED${NC}"
    echo ""
    echo "No issues found!"
    exit 0
else
    echo -e "${RED}✗ VALIDATION FAILED${NC}"
    echo ""
    echo -e "${YELLOW}$TOTAL_ERRORS validation script(s) reported issues${NC}"
    echo ""
    echo "Detailed reports saved to:"
    if [ $VAR_EXIT -ne 0 ]; then
        echo "  - /tmp/variable-validation.txt"
    fi
    if [ $LOC_EXIT -ne 0 ]; then
        echo "  - /tmp/scripted-loc-validation.txt"
    fi
    echo ""

    if [ -n "$STRICT_FLAG" ]; then
        exit 1
    else
        exit 0
    fi
fi
