from types import SimpleNamespace

import numpy as np
import pytest
from mat3ra.made.cell.primitive_cell import PRIMITIVE_CELLS
from mat3ra.made.cell.standard_orientation import get_vectors_in_standard_orientation
from mat3ra.made.lattice import Lattice

# Conventional parameters per type, generic enough to have no accidental extra symmetry.
CONVENTIONAL_PARAMETERS = {
    "CUB": dict(a=3.0),
    "FCC": dict(a=4.0),
    "BCC": dict(a=3.2),
    "TET": dict(a=3.0, c=4.1),
    "BCT": dict(a=3.0, c=4.1),
    "ORC": dict(a=3.0, b=3.6, c=4.3),
    "ORCF": dict(a=3.0, b=3.6, c=4.3),
    "ORCI": dict(a=3.0, b=3.6, c=4.3),
    "ORCC": dict(a=3.0, b=3.6, c=4.3),
    "HEX": dict(a=3.0, c=4.8),
    "RHL": dict(a=3.5, alpha=70.0),
    "MCL": dict(a=3.0, b=3.6, c=4.3, alpha=75.0),
    "MCLC": dict(a=3.0, b=3.6, c=4.3, alpha=75.0),
    "TRI": dict(a=3.0, b=3.6, c=4.3, alpha=75.0, beta=80.0, gamma=85.0),
}


def standard_cell(lattice_type):
    values = {"alpha": 90.0, "beta": 90.0, "gamma": 90.0, **CONVENTIONAL_PARAMETERS[lattice_type]}
    values.setdefault("b", values["a"])
    values.setdefault("c", values["a"])
    if lattice_type == "RHL":
        values["beta"] = values["gamma"] = values["alpha"]
    return np.array(PRIMITIVE_CELLS[lattice_type](SimpleNamespace(**values)))


def lattice_from_parameters(lattice_type):
    """
    A lattice as a stored material holds it: parameters and type, no vectors.
    """
    shape = Lattice.from_vectors_array(standard_cell(lattice_type).tolist(), type=lattice_type)
    return Lattice(
        **{name: getattr(shape, name) for name in ("a", "b", "c", "alpha", "beta", "gamma")}, type=lattice_type
    )


@pytest.mark.parametrize("lattice_type", list(CONVENTIONAL_PARAMETERS))
def test_vectors_are_the_standard_primitive_cell_of_the_type(lattice_type):
    lattice = lattice_from_parameters(lattice_type)
    assert np.allclose(lattice.vector_arrays_in_standard_orientation, standard_cell(lattice_type), atol=1e-6)


@pytest.mark.parametrize("lattice_type", list(CONVENTIONAL_PARAMETERS))
def test_the_orientation_is_a_rotation_of_the_generic_vectors(lattice_type):
    lattice = lattice_from_parameters(lattice_type)
    generic = np.array(lattice.vector_arrays)
    standard = np.array(lattice.vector_arrays_in_standard_orientation)
    assert np.allclose(standard @ standard.T, generic @ generic.T, atol=1e-9)
    assert np.linalg.det(standard) == pytest.approx(np.linalg.det(generic), rel=1e-9)


def test_a_lattice_not_shaped_like_its_type_keeps_its_vectors():
    lattice = Lattice(a=2.6, b=2.6, c=2.6, alpha=70.0, beta=70.0, gamma=70.0, type="FCC")
    assert np.allclose(lattice.vector_arrays_in_standard_orientation, lattice.vector_arrays, atol=1e-12)


def test_the_generic_vectors_are_unchanged():
    lattice = lattice_from_parameters("FCC")
    vector_a, _, vector_c = lattice.vector_arrays
    assert vector_a[1] == 0.0
    assert vector_c[:2] == [0.0, 0.0]


def test_an_unknown_type_keeps_the_vectors():
    vectors = [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]]
    assert get_vectors_in_standard_orientation(vectors, "UNKNOWN") == vectors
