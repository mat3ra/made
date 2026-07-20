"""Tests that shared data files in data/ are accessible after package installation.

These tests verify that the JSON files can be found and loaded via the
path resolution logic used in production code. If they fail, the data
files are likely missing from the installed package distribution.
"""

import json
from pathlib import Path


def _get_data_dir():
    """Resolve data/ directory the same way production code does.

    Production code uses Path(__file__).parents[N] to reach the repo root.
    This test uses the same approach from its own location to verify the
    path resolution works in the installed environment.
    """
    # tests/py/unit/test_data_files.py -> parents[3] -> repo root
    return Path(__file__).parents[3] / "data"


def test_data_dir_exists():
    data_dir = _get_data_dir()
    assert data_dir.exists(), f"data/ directory not found at {data_dir}"
    assert data_dir.is_dir(), f"{data_dir} is not a directory"


def test_data_constants_json_loadable():
    path = _get_data_dir() / "constants.json"
    assert path.exists(), f"constants.json not found at {path}"
    with open(path) as f:
        data = json.load(f)
    assert "molecule" in data, "constants.json missing 'molecule' key"
    assert "precision" in data, "constants.json missing 'precision' key"
    assert data["molecule"]["nonPeriodicMinimumLatticeSize"] == 3.0


def test_data_reciprocal_paths_json_loadable():
    path = _get_data_dir() / "reciprocal_paths.json"
    assert path.exists(), f"reciprocal_paths.json not found at {path}"
    with open(path) as f:
        data = json.load(f)
    assert len(data) == 22, f"Expected 22 path keys, got {len(data)}"
    assert "CUB" in data
    assert "FCC" in data
    assert "TRI" in data


def test_data_constants_importable_from_production_code():
    """Verify the actual production import path works."""
    from mat3ra.made.tools.convert.utils import (
        DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE,
        DIATOMIC_LATTICE_PADDING_FACTOR,
        MOLECULAR_LATTICE_PADDING_FACTOR,
    )

    assert DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE == 3.0
    assert DIATOMIC_LATTICE_PADDING_FACTOR == 3.0
    assert MOLECULAR_LATTICE_PADDING_FACTOR == 2.0


def test_data_reciprocal_paths_importable_from_production_code():
    """Verify the actual production import path works."""
    from mat3ra.made.reciprocal import RECIPROCAL_PATHS

    assert len(RECIPROCAL_PATHS) == 22
    assert "CUB" in RECIPROCAL_PATHS
