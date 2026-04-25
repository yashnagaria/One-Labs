#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Reconciliation Streamlit App Launcher"
echo "========================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

if ! pip show streamlit &> /dev/null; then
    echo -e "${YELLOW}Installing Streamlit dependencies...${NC}"
    pip install -q streamlit pandas plotly
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

if [ "$1" == "--generate-data" ] || [ ! -f "test_data_generator/output/platform_transactions.csv" ]; then
    echo -e "${YELLOW}Generating test data...${NC}"
    PYTHONPATH="$SCRIPT_DIR" python3 test_data_generator/generate.py
    echo -e "${GREEN}✓ Test data generated${NC}"
fi

echo ""
echo "🌐 Starting Streamlit server..."
echo -e "${GREEN}App will be available at: http://localhost:8501${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run streamlit_app.py --server.port=8501
