#!/bin/bash
###############################################################################
# Example pre-commit hook for variable validation
# To use this hook:
# 1. Copy this file to .git/hooks/pre-commit
# 2. Make it executable: chmod +x .git/hooks/pre-commit
# 3. The hook will run automatically before each commit
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Running variable validation on staged files..."

# Run the validator on staged files only
python3 tools/validation/validate_variables.py --staged --strict --no-color --output /tmp/validation-report.txt

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}✗ Validation failed!${NC}"
    echo "The following issues were found in your staged files:"
    echo ""
    cat /tmp/validation-report.txt | grep -A 999 "issues found" || cat /tmp/validation-report.txt
    echo ""
    echo "Please fix these issues before committing."
    echo "Full report saved to: /tmp/validation-report.txt"
    exit 1
else
    echo -e "${GREEN}✓ Validation passed!${NC}"
    exit 0
fi
