"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
