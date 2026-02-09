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
TOTAL_VALIDATORS=7

# 1. Run variable validation
echo -e "${CYAN}[1/$TOTAL_VALIDATORS] Running variable and event target validation...${NC}"
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
echo -e "${CYAN}[2/$TOTAL_VALIDATORS] Running scripted localisation validation...${NC}"
python3 tools/validation/validate_scripted_localisation.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/scripted-loc-validation.txt
SLOC_EXIT=$?
if [ $SLOC_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Scripted localisation validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Scripted localisation validation passed${NC}"
fi
echo ""

# 3. Run set variables validation
echo -e "${CYAN}[3/$TOTAL_VALIDATORS] Running set variables validation...${NC}"
python3 tools/validation/validate_set_variables.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/set-variables-validation.txt
SETVAR_EXIT=$?
if [ $SETVAR_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Set variables validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Set variables validation passed${NC}"
fi
echo ""

# 4. Run cosmetic tag validation
echo -e "${CYAN}[4/$TOTAL_VALIDATORS] Running cosmetic tag validation...${NC}"
python3 tools/validation/validate_cosmetic_tags.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/cosmetic-tags-validation.txt
CTAG_EXIT=$?
if [ $CTAG_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Cosmetic tag validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Cosmetic tag validation passed${NC}"
fi
echo ""

# 5. Run decision validation
echo -e "${CYAN}[5/$TOTAL_VALIDATORS] Running decision validation...${NC}"
python3 tools/validation/validate_decisions.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/decisions-validation.txt
DEC_EXIT=$?
if [ $DEC_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Decision validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Decision validation passed${NC}"
fi
echo ""

# 6. Run localisation validation
echo -e "${CYAN}[6/$TOTAL_VALIDATORS] Running localisation validation...${NC}"
python3 tools/validation/validate_localisation.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/localisation-validation.txt
LOC_EXIT=$?
if [ $LOC_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Localisation validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Localisation validation passed${NC}"
fi
echo ""

# 7. Run event validation
echo -e "${CYAN}[7/$TOTAL_VALIDATORS] Running event validation...${NC}"
python3 tools/validation/validate_events.py $STAGED_FLAG $STRICT_FLAG $COLOR_FLAG --output /tmp/events-validation.txt
EVT_EXIT=$?
if [ $EVT_EXIT -ne 0 ]; then
    echo -e "${RED}✗ Event validation found issues${NC}"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "${GREEN}✓ Event validation passed${NC}"
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
    [ $VAR_EXIT -ne 0 ] && echo "  - /tmp/variable-validation.txt"
    [ $SLOC_EXIT -ne 0 ] && echo "  - /tmp/scripted-loc-validation.txt"
    [ $SETVAR_EXIT -ne 0 ] && echo "  - /tmp/set-variables-validation.txt"
    [ $CTAG_EXIT -ne 0 ] && echo "  - /tmp/cosmetic-tags-validation.txt"
    [ $DEC_EXIT -ne 0 ] && echo "  - /tmp/decisions-validation.txt"
    [ $LOC_EXIT -ne 0 ] && echo "  - /tmp/localisation-validation.txt"
    [ $EVT_EXIT -ne 0 ] && echo "  - /tmp/events-validation.txt"
    echo ""

    if [ -n "$STRICT_FLAG" ]; then
        exit 1
    else
        exit 0
    fi
fi
