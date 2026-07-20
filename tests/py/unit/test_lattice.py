import pytest
from mat3ra.code.vector import RoundedVector3D
from mat3ra.made.lattice import Lattice
from mat3ra.utils import assertion as assertion_utils

DEFAULT_UNITS = Lattice.__units_default__
DEFAULT_TYPE = Lattice.__type_default__


def test_lattice_creation():
    lattice = Lattice(a=2.0, b=3.0, c=4.0)
    assert lattice.a == 2.0
    assert lattice.b == 3.0
    assert lattice.c == 4.0
    assert lattice.alpha == 90.0
    assert lattice.beta == 90.0
    assert lattice.gamma == 90.0
    assert lattice.units == DEFAULT_UNITS
    assert lattice.type == DEFAULT_TYPE


def test_lattice_get_vectors():
    lattice = Lattice(a=2.0, b=3.0, c=4.0)
    expected_vectors = [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]]
    assert expected_vectors == lattice.vector_arrays_rounded


def test_lattice_vectors_access():
    lattice = Lattice(a=2.0, b=3.0, c=4.0)

    # Test individual vector access
    assert isinstance(lattice.vectors.a, RoundedVector3D)
    assert isinstance(lattice.vectors.b, RoundedVector3D)
    assert isinstance(lattice.vectors.c, RoundedVector3D)

    # Test vector arrays access
    arrays = lattice.vector_arrays
    assert len(arrays) == 3
    assert arrays[0] == lattice.vectors.a
    assert arrays[1] == lattice.vectors.b
    assert arrays[2] == lattice.vectors.c

    # Test get value of vectors, without rounding
    assertion_utils.assert_deep_almost_equal(lattice.vectors.a.root, [2.0, 0.0, 0.0])


def test_lattice_from_vectors():
    lattice = Lattice.from_vectors_array(vectors=[[2.0, 0, 0], [0, 3.0, 0], [0, 0, 4.0]])
    assert lattice.a == 2.0
    assert lattice.b == 3.0
    assert lattice.c == 4.0
    assert lattice.alpha == 90.0
    assert lattice.beta == 90.0
    assert lattice.gamma == 90.0
    assert lattice.units == DEFAULT_UNITS
    assert lattice.type.value == DEFAULT_TYPE
    # Avoid floating point comparison issue
    assertion_utils.assert_deep_almost_equal(lattice.cell_volume, 24.0)
    assert lattice.cell_volume_rounded == 24.0
    assert lattice.vector_arrays_rounded == [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]]


def test_lattice_get_scaled_by_matrix():
    original_lattice = Lattice(a=2.0, b=3.0, c=4.0)
    matrix = [[1.5, 0, 0], [0, 1.5, 0], [0, 0, 0.5]]
    expected_vector_values = [[3.0, 0.0, 0.0], [0.0, 4.5, 0.0], [0.0, 0.0, 2.0]]
    lattice = original_lattice.get_scaled_by_matrix(matrix)
    assert lattice.a == 3.0
    assert lattice.b == 4.5
    assert lattice.c == 2.0
    assert lattice.alpha == pytest.approx(90.0)
    assert lattice.beta == pytest.approx(90.0)
    assert lattice.gamma == pytest.approx(90.0)
    assert lattice.units == DEFAULT_UNITS
    assert lattice.type.value == DEFAULT_TYPE
    assertion_utils.assert_deep_almost_equal(lattice.vector_arrays, expected_vector_values)


def test_reciprocal_vectors():
    lattice = Lattice(a=2.0, b=3.0, c=4.0)
    expected_vectors = [[0.5, 0.0, 0.0], [0.0, 1 / 3, 0.0], [0.0, 0.0, 0.25]]
    assertion_utils.assert_deep_almost_equal(lattice.reciprocal_vectors, expected_vectors)


def test_reciprocal_vector_norms():
    lattice = Lattice(a=2.0, b=3.0, c=4.0)
    expected_norms = [0.5, 1 / 3, 0.25]
    assertion_utils.assert_deep_almost_equal(lattice.reciprocal_vector_norms, expected_norms)


@pytest.mark.parametrize(
    "lattice, expected",
    [
        (Lattice(a=2.0, b=3.0, c=4.0), [1.0, 0.667, 0.5]),
        (Lattice(a=5.43, b=5.43, c=5.43), [1.0, 1.0, 1.0]),
    ],
)
def test_reciprocal_vector_ratios(lattice, expected):
    assert lattice.reciprocal_vector_ratios == expected


# to test: create, calculate_vectors, from_vectors, get_lattice_type, clone
# from_vectors, to_dict, cell, cell_volume, scale_by_matrix, update_from_lattice,
