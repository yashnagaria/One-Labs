#!/usr/bin/env python3
"""
Launcher script for test data generator.
Run this from the project root directory.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from test_data_generator.generate import main

if __name__ == "__main__":
    main()
