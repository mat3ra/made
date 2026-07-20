"""Tests for reciprocal paths data."""

from mat3ra.made.reciprocal import RECIPROCAL_PATHS

EXPECTED_KEYS = [
    "CUB",
    "BCC",
    "FCC",
    "TET",
    "BCT-1",
    "BCT-2",
    "ORC",
    "ORCF-1",
    "ORCF-2",
    "ORCF-3",
    "ORCI",
    "ORCC",
    "HEX",
    "RHL-1",
    "RHL-2",
    "MCL",
    "MCLC-1",
    "MCLC-2",
    "MCLC-3",
    "MCLC-4",
    "MCLC-5",
    "TRI",
]


def test_reciprocal_paths_all_keys_present():
    for key in EXPECTED_KEYS:
        assert key in RECIPROCAL_PATHS, f"Missing path key: {key}"


def test_reciprocal_paths_count():
    assert len(RECIPROCAL_PATHS) == len(EXPECTED_KEYS)


def test_reciprocal_paths_entry_structure():
    for key, path in RECIPROCAL_PATHS.items():
        assert isinstance(path, list), f"Path {key} should be a list"
        for entry in path:
            assert "point" in entry, f"Entry in {key} missing 'point'"
            assert "steps" in entry, f"Entry in {key} missing 'steps'"
            assert entry["steps"] == 10, f"Entry in {key} should have steps=10"


def test_reciprocal_paths_cub():
    path = RECIPROCAL_PATHS["CUB"]
    labels = [p["point"] for p in path]
    assert labels == ["Г", "X", "M", "Г", "R", "X", "M", "R"]


def test_reciprocal_paths_fcc():
    path = RECIPROCAL_PATHS["FCC"]
    labels = [p["point"] for p in path]
    assert labels == ["Г", "X", "W", "K", "Г", "L", "U", "W", "L", "U", "X"]


def test_reciprocal_paths_hex():
    path = RECIPROCAL_PATHS["HEX"]
    labels = [p["point"] for p in path]
    assert labels == ["Г", "M", "K", "Г", "A", "L", "H", "A", "L", "M", "K", "H"]
