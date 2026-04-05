"""Pytest configuration and fixtures for clustering-service tests."""

import pytest
import sys
from pathlib import Path

# Add the app directory to the path so tests can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

