#!/usr/bin/env bash
#
# Run all test suites for avl2step
#

set -e  # Exit on first failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================"
echo "Running all avl2step test suites"
echo "========================================"
echo ""

# Find all TEST.py files
TEST_FILES=$(find "$SCRIPT_DIR" -type f -name "TEST.py" | sort)

if [ -z "$TEST_FILES" ]; then
    echo -e "${RED}No test files found!${NC}"
    exit 1
fi

# Run each test
for TEST_FILE in $TEST_FILES; do
    TEST_DIR=$(dirname "$TEST_FILE")
    TEST_NAME=$(basename "$TEST_DIR")
    
    echo -e "${YELLOW}Running: $TEST_NAME${NC}"
    echo "----------------------------------------"
    
    cd "$TEST_DIR"
    
    if python3 TEST.py; then
        echo -e "${GREEN}✓ PASSED: $TEST_NAME${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED: $TEST_NAME${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
done

# Print summary
echo "========================================"
echo "TEST SUMMARY"
echo "========================================"
echo -e "Total test suites: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    exit 1
else
    echo -e "Failed: $FAILED_TESTS"
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
