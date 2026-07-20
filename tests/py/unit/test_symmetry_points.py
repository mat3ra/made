"""Tests for Brillouin zone symmetry points."""

import pytest
from mat3ra.made.lattice import Lattice
from mat3ra.made.reciprocal.symmetry_points import get_symmetry_points
from mat3ra.utils import assertion as assertion_utils


def test_symmetry_points_gamma_always_first():
    """Gamma point should always be the first symmetry point."""
    lattice = Lattice(a=1.0, b=1.0, c=1.0, type="CUB")
    points = get_symmetry_points(lattice)
    assert points[0]["point"] == "Г"
    assert points[0]["coordinates"] == [0.0, 0.0, 0.0]


def test_symmetry_points_cub():
    lattice = Lattice(a=5.64, b=5.64, c=5.64, type="CUB")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert labels == ["Г", "R", "X", "M"]
    # Verify specific coordinates
    r_point = next(p for p in points if p["point"] == "R")
    assertion_utils.assert_deep_almost_equal(r_point["coordinates"], [0.5, 0.5, 0.5])
    x_point = next(p for p in points if p["point"] == "X")
    assertion_utils.assert_deep_almost_equal(x_point["coordinates"], [0.0, 0.5, 0.0])
    m_point = next(p for p in points if p["point"] == "M")
    assertion_utils.assert_deep_almost_equal(m_point["coordinates"], [0.5, 0.5, 0.0])


def test_symmetry_points_fcc():
    lattice = Lattice(a=5.43, b=5.43, c=5.43, type="FCC")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert "K" in labels
    assert "L" in labels
    assert "U" in labels
    assert "W" in labels
    assert "X" in labels
    k_point = next(p for p in points if p["point"] == "K")
    assertion_utils.assert_deep_almost_equal(k_point["coordinates"], [3 / 8, 3 / 8, 3 / 4])


def test_symmetry_points_bcc():
    lattice = Lattice(a=3.0, b=3.0, c=3.0, type="BCC")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert labels == ["Г", "H", "P", "N"]
    h_point = next(p for p in points if p["point"] == "H")
    assertion_utils.assert_deep_almost_equal(h_point["coordinates"], [0.5, -0.5, 0.5])


def test_symmetry_points_hex():
    lattice = Lattice(a=2.46, b=2.46, c=6.71, type="HEX")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert set(labels) == {"Г", "A", "H", "K", "L", "M"}
    k_point = next(p for p in points if p["point"] == "K")
    assertion_utils.assert_deep_almost_equal(k_point["coordinates"], [1 / 3, 1 / 3, 0.0])


def test_symmetry_points_bct1():
    """BCT with c < a should give BCT-1 points."""
    lattice = Lattice(a=4.0, b=4.0, c=2.0, type="BCT")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert "Z" in labels
    assert "Z1" in labels
    # BCT-1: n = (1 + c²/a²) / 4 = (1 + 4/16) / 4 = 1.25/4 = 0.3125
    z_point = next(p for p in points if p["point"] == "Z")
    n = (1 + 4.0 / 16.0) / 4
    assertion_utils.assert_deep_almost_equal(z_point["coordinates"], [n, n, -n])


def test_symmetry_points_bct2():
    """BCT with c >= a should give BCT-2 points."""
    lattice = Lattice(a=2.0, b=2.0, c=4.0, type="BCT")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert "∑" in labels
    assert "Y" in labels
    assert "Z" not in [p["point"] for p in points if p["point"] == "Z1"]


def test_symmetry_points_tet():
    lattice = Lattice(a=3.0, b=3.0, c=5.0, type="TET")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert set(labels) == {"Г", "A", "M", "R", "X", "Z"}


def test_symmetry_points_orc():
    lattice = Lattice(a=2.0, b=3.0, c=4.0, type="ORC")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert set(labels) == {"Г", "R", "S", "T", "U", "X", "Y", "Z"}


def test_symmetry_points_rhl1():
    """RHL with cos(alpha) > 0 should give RHL-1 points."""
    lattice = Lattice(a=3.0, b=3.0, c=3.0, alpha=60.0, beta=60.0, gamma=60.0, type="RHL")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert "B" in labels
    assert "B1" in labels
    assert "F" in labels


def test_symmetry_points_rhl2():
    """RHL with cos(alpha) < 0 should give RHL-2 points."""
    lattice = Lattice(a=3.0, b=3.0, c=3.0, alpha=120.0, beta=120.0, gamma=120.0, type="RHL")
    points = get_symmetry_points(lattice)
    labels = [p["point"] for p in points]
    assert "Q" in labels
    assert "Q1" in labels
    # RHL-2 should NOT have B, B1 points
    assert "B" not in labels


def test_symmetry_points_tri_1a():
    """TRI with alpha, beta > 90 and gamma >= 90."""
    lattice = Lattice(a=1.0, b=2.0, c=3.0, alpha=95.0, beta=100.0, gamma=110.0, type="TRI")
    points = get_symmetry_points(lattice)
    # TRI-1a,2a: L at [1/2, 1/2, 0]
    l_point = next(p for p in points if p["point"] == "L")
    assertion_utils.assert_deep_almost_equal(l_point["coordinates"], [0.5, 0.5, 0.0])


def test_symmetry_points_tri_1b():
    """TRI without all angles > 90."""
    lattice = Lattice(a=1.0, b=2.0, c=3.0, alpha=80.0, beta=85.0, gamma=75.0, type="TRI")
    points = get_symmetry_points(lattice)
    # TRI-1b,2b: L at [1/2, -1/2, 0]
    l_point = next(p for p in points if p["point"] == "L")
    assertion_utils.assert_deep_almost_equal(l_point["coordinates"], [0.5, -0.5, 0.0])


@pytest.mark.parametrize(
    "lattice_type",
    ["CUB", "FCC", "BCC", "TET", "BCT", "ORC", "ORCF", "ORCI", "ORCC", "HEX", "RHL", "MCL", "MCLC", "TRI"],
)
def test_symmetry_points_all_lattice_types(lattice_type):
    """Every supported lattice type should return at least the Gamma point."""
    lattice = Lattice(a=3.0, b=4.0, c=5.0, alpha=80.0, beta=85.0, gamma=75.0, type=lattice_type)
    points = get_symmetry_points(lattice)
    assert len(points) >= 1
    assert points[0]["point"] == "Г"
    # All coordinates should be lists of 3 floats
    for p in points:
        assert len(p["coordinates"]) == 3
        assert all(isinstance(c, (int, float)) for c in p["coordinates"])
