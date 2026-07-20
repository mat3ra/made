"""Tests for Lattice.type_extended property."""

import pytest
from mat3ra.made.lattice import Lattice


@pytest.mark.parametrize(
    "lattice_params, expected_type",
    [
        # Simple types return base type
        ({"a": 1.0, "b": 1.0, "c": 1.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "CUB"}, "CUB"),
        ({"a": 1.0, "b": 1.0, "c": 1.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "FCC"}, "FCC"),
        ({"a": 1.0, "b": 1.0, "c": 1.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "BCC"}, "BCC"),
        ({"a": 1.0, "b": 1.0, "c": 2.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "TET"}, "TET"),
        ({"a": 2.0, "b": 3.0, "c": 4.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "ORC"}, "ORC"),
        ({"a": 1.0, "b": 1.0, "c": 2.0, "alpha": 90, "beta": 90, "gamma": 120, "type": "HEX"}, "HEX"),
        # BCT subtypes
        ({"a": 2.0, "b": 2.0, "c": 1.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "BCT"}, "BCT-1"),  # c < a
        ({"a": 1.0, "b": 1.0, "c": 2.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "BCT"}, "BCT-2"),  # c >= a
        # ORCF subtypes
        (
            {"a": 3.0, "b": 4.0, "c": 5.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "ORCF"},
            "ORCF-1",
        ),  # 1/a^2 >= 1/b^2 + 1/c^2 for a=3,b=4,c=5: 1/9≈0.111 vs 1/16+1/25≈0.1025
        (
            {"a": 4.0, "b": 2.0, "c": 3.0, "alpha": 90, "beta": 90, "gamma": 90, "type": "ORCF"},
            "ORCF-2",
        ),  # 1/a^2 < 1/b^2 + 1/c^2: 1/16=0.0625 < 1/4+1/9=0.361
        # RHL subtypes
        ({"a": 1.0, "b": 1.0, "c": 1.0, "alpha": 60, "beta": 60, "gamma": 60, "type": "RHL"}, "RHL-1"),  # cos(60)>0
        (
            {"a": 1.0, "b": 1.0, "c": 1.0, "alpha": 120, "beta": 120, "gamma": 120, "type": "RHL"},
            "RHL-2",
        ),  # cos(120)<0
        # MCLC subtypes
        (
            {"a": 1.0, "b": 2.0, "c": 3.0, "alpha": 80, "beta": 90, "gamma": 95, "type": "MCLC"},
            "MCLC-1",
        ),  # gamma >= 90
        # TRI subtypes
        (
            {"a": 1.0, "b": 2.0, "c": 3.0, "alpha": 95, "beta": 100, "gamma": 110, "type": "TRI"},
            "TRI_1a",
        ),  # all > 90
        (
            {"a": 1.0, "b": 2.0, "c": 3.0, "alpha": 80, "beta": 85, "gamma": 75, "type": "TRI"},
            "TRI_1b",
        ),  # not all > 90
    ],
)
def test_type_extended(lattice_params, expected_type):
    lattice = Lattice(**lattice_params)
    assert lattice.type_extended == expected_type
