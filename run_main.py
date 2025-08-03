#!/usr/bin/env python3
"""
Launcher script for ECG Converter - Modular Version
Run this script from the root directory to start the application
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
from src.main import main

if __name__ == "__main__":
    print("Starting ECG Converter - Modular Version...")
    print("Loading modules from src/ directory...")
    main() 