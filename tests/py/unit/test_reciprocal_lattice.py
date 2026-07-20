"""Tests for the ReciprocalLattice class."""

from mat3ra.made.reciprocal import ReciprocalLattice
from mat3ra.utils import assertion as assertion_utils


def test_reciprocal_lattice_symmetry_points_cub():
    """CUB lattice should have Г, R, X, M symmetry points."""
    lattice = ReciprocalLattice(a=5.64, b=5.64, c=5.64, type="CUB")
    points = lattice.symmetry_points
    labels = [p["point"] for p in points]
    assert labels == ["Г", "R", "X", "M"]


def test_reciprocal_lattice_default_kpoint_path_cub():
    lattice = ReciprocalLattice(a=5.64, b=5.64, c=5.64, type="CUB")
    path = lattice.default_kpoint_path
    labels = [p["point"] for p in path]
    assert labels == ["Г", "X", "M", "Г", "R", "X", "M", "R"]


def test_reciprocal_lattice_default_kpoint_path_bct():
    """BCT with c < a should use BCT-1 path."""
    lattice = ReciprocalLattice(a=4.0, b=4.0, c=2.0, type="BCT")
    path = lattice.default_kpoint_path
    labels = [p["point"] for p in path]
    assert "Z1" in labels  # BCT-1 specific


def test_reciprocal_lattice_extract_kpoint_path():
    lattice = ReciprocalLattice(a=5.64, b=5.64, c=5.64, type="CUB")
    data_points = [[0, 0, 0], [0.5, 0.5, 0.5]]
    result = lattice.extract_kpoint_path(data_points)
    assert len(result) == 2
    assert result[0]["point"] == "Г"
    assert result[0]["steps"] == 0
    assert result[1]["point"] == "R"
    assert result[1]["steps"] == 1


def test_reciprocal_lattice_extract_kpoint_path_empty():
    lattice = ReciprocalLattice(a=5.64, b=5.64, c=5.64, type="CUB")
    result = lattice.extract_kpoint_path([])
    assert result == []


def test_reciprocal_lattice_cartesian_coordinates():
    lattice = ReciprocalLattice(a=5.64, b=5.64, c=5.64, type="CUB")
    cart = lattice.cartesian_coordinates([0.5, 0.5, 0.5])
    assert len(cart) == 3
    assert all(isinstance(c, float) for c in cart)


def test_reciprocal_lattice_dimensions_from_points_count():
    """Test grid dimension calculation from total k-point count."""
    lattice = ReciprocalLattice(a=2.0, b=3.0, c=4.0, type="ORC")
    dims = lattice.get_dimensions_from_points_count(500)
    assert len(dims) == 3
    assert all(d >= 1 for d in dims)
    # Product should be close to 500
    product = dims[0] * dims[1] * dims[2]
    assert product >= 500  # Should be at least 500 due to ceiling


def test_reciprocal_lattice_dimensions_from_spacing():
    lattice = ReciprocalLattice(a=2.0, b=3.0, c=4.0, type="ORC")
    dims = lattice.get_dimensions_from_spacing(0.1)
    assert len(dims) == 3
    assert all(d >= 1 for d in dims)


def test_reciprocal_lattice_spacing_from_dimensions():
    lattice = ReciprocalLattice(a=2.0, b=3.0, c=4.0, type="ORC")
    dims = [10, 7, 5]
    spacing = lattice.get_spacing_from_dimensions(dims)
    assert isinstance(spacing, float)
    assert spacing > 0


def test_reciprocal_lattice_reciprocal_vectors_inherited():
    """ReciprocalLattice should inherit reciprocal_vectors from Lattice."""
    lattice = ReciprocalLattice(a=2.0, b=3.0, c=4.0, type="ORC")
    vecs = lattice.reciprocal_vectors
    assert len(vecs) == 3
    expected = [[0.5, 0.0, 0.0], [0.0, 1 / 3, 0.0], [0.0, 0.0, 0.25]]
    assertion_utils.assert_deep_almost_equal(vecs, expected)
