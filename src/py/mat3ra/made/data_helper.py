"""Resolve the shared data/ directory at the repository root."""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
