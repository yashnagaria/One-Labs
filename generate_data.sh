#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Test Data Generator"
echo "======================"
echo ""

echo -e "${YELLOW}Generating test data...${NC}"
python3 generate_test_data.py

echo ""
echo -e "${GREEN}✓ Done!${NC}"
echo ""
echo "Output files:"
echo "  - test_data_generator/output/platform_transactions.csv"
echo "  - test_data_generator/output/bank_statement.csv"
echo "  - test_data_generator/output/gap_manifest.json"
