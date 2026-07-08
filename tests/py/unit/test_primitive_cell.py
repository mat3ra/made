import math
import pytest

from mat3ra.made.cell.primitive_cell import get_primitive_lattice_vectors_from_config
from mat3ra.made.lattice import Lattice, LatticeTypeEnum
from tests.py.unit.utils import assert_two_entities_deep_almost_equal

EXPECTED_PRIMITIVE_CELL_NA4CL4 = [
    [5.691694, 0.0, 0.0],
    [0.0, 5.691694, 0.0],
    [0.0, 0.0, 5.691694],
]


def test_primitive_lattice_vectors_na4cl4():
    """
    Replicates the TypeScript test for Na4Cl4 (CUB cell).
    Translates from: tests/js/cell/primitive_cell.ts
    """
    lattice = Lattice(type=LatticeTypeEnum.CUB, a=5.691694)
    actual_primitive_cell = get_primitive_lattice_vectors_from_config(lattice)

    assert_two_entities_deep_almost_equal(EXPECTED_PRIMITIVE_CELL_NA4CL4, actual_primitive_cell)


@pytest.mark.parametrize(
    "l_type, kwargs, expected",
    [
        (LatticeTypeEnum.CUB, {"a": 2.0}, [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]),
        (LatticeTypeEnum.FCC, {"a": 2.0}, [[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]]),
        (LatticeTypeEnum.BCC, {"a": 2.0}, [[-1.0, 1.0, 1.0], [1.0, -1.0, 1.0], [1.0, 1.0, -1.0]]),
        (LatticeTypeEnum.TET, {"a": 2.0, "c": 3.0}, [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]]),
        (LatticeTypeEnum.BCT, {"a": 2.0, "c": 3.0}, [[-1.0, 1.0, 1.5], [1.0, -1.0, 1.5], [1.0, 1.0, -1.5]]),
        (LatticeTypeEnum.ORC, {"a": 2.0, "b": 3.0, "c": 4.0}, [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]]),
        (
            LatticeTypeEnum.ORCF,
            {"a": 2.0, "b": 3.0, "c": 4.0},
            [[0.0, 1.5, 2.0], [1.0, 0.0, 2.0], [1.0, 1.5, 0.0]],
        ),
        (
            LatticeTypeEnum.ORCI,
            {"a": 2.0, "b": 3.0, "c": 4.0},
            [[-1.0, 1.5, 2.0], [1.0, -1.5, 2.0], [1.0, 1.5, -2.0]],
        ),
        (
            LatticeTypeEnum.ORCC,
            {"a": 2.0, "b": 3.0, "c": 4.0},
            [[1.0, 1.5, 0.0], [-1.0, 1.5, 0.0], [0.0, 0.0, 4.0]],
        ),
        (
            LatticeTypeEnum.HEX,
            {"a": 2.0, "c": 3.0},
            [[1.0, -math.sqrt(3), 0.0], [1.0, math.sqrt(3), 0.0], [0.0, 0.0, 3.0]],
        ),
        (
            LatticeTypeEnum.RHL,
            {"a": 2.0, "alpha": 60.0},
            [[1.7320508, -1.0, 0.0], [1.7320508, 1.0, 0.0], [1.1547005, 0.0, 1.6329931]],
        ),
        (
            LatticeTypeEnum.MCL,
            {"a": 2.0, "b": 3.0, "c": 4.0, "alpha": 60.0},
            [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 2.0, 3.4641016]],
        ),
        (
            LatticeTypeEnum.MCLC,
            {"a": 2.0, "b": 3.0, "c": 4.0, "alpha": 60.0},
            [[1.0, 1.5, 0.0], [-1.0, 1.5, 0.0], [0.0, 2.0, 3.4641016]],
        ),
        (
            LatticeTypeEnum.TRI,
            {"a": 2.0, "b": 3.0, "c": 4.0, "alpha": 90.0, "beta": 90.0, "gamma": 90.0},
            [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]],
        ),
    ],
)
def test_primitive_lattice_generators(l_type, kwargs, expected):
    """Validates the math generators for all 14 Bravais lattice scenarios."""
    lattice = Lattice(type=l_type, **kwargs)
    result = get_primitive_lattice_vectors_from_config(lattice)
    assert_two_entities_deep_almost_equal(expected, result)


def test_fallback_to_tri_when_type_is_none():
    """Tests default fallback to 'TRI' when lattice_config.type is None."""
    # Use a simple dummy class to bypass Pydantic's strict validation
    # and simulate a malformed or incomplete Lattice config.
    class MockLattice:
        type = None
        a, b, c = 2.0, 2.0, 2.0
        alpha, beta, gamma = 90.0, 90.0, 90.0

    lattice = MockLattice()
    result = get_primitive_lattice_vectors_from_config(lattice)
    expected = [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]

    assert_two_entities_deep_almost_equal(expected, result)


def test_unsupported_lattice_type_raises_value_error():
    """Ensures a ValueError is raised for an unknown lattice type mapping."""
    # Using a MagicMock specifically here to force an invalid type value
    # since LatticeTypeEnum won't allow arbitrary strings
    class MockType:
        value = "INVALID_TYPE"

    class MockLattice:
        type = MockType()
        # Provide dummy parameters just in case
        a, b, c = 2.0, 2.0, 2.0
        alpha, beta, gamma = 90.0, 90.0, 90.0

    lattice = MockLattice()

    with pytest.raises(ValueError) as exc_info:
        get_primitive_lattice_vectors_from_config(lattice)

    assert "Unsupported lattice type 'INVALID_TYPE'" in str(exc_info.value)
