"""
Primitive lattice vectors in the standard orientation of their lattice type.
Python equivalent of src/js/cell/standard_orientation.ts.

Lattice parameters (a, b, c, alpha, beta, gamma) fix the shape of a cell but not its
orientation. The generic construction places the third vector along z and the first in
the xz plane for every type, which leaves the symmetry axes of most centred lattices
tilted away from x, y and z. The standard primitive cells of Setyawan and Curtarolo
(doi:10.1016/j.commatsci.2010.05.010, `PRIMITIVE_CELLS`) have the conventional axes
along x, y and z. Programs that look for symmetry only about the Cartesian axes, such
as Quantum ESPRESSO's pw.x with explicit cell vectors, find the full point group only
there.

A rigid rotation changes no lengths or angles, so fractional coordinates stay valid.
"""

import math
from types import SimpleNamespace
from typing import List

import numpy as np

from .conventional_cell import PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS
from .primitive_cell import PRIMITIVE_CELLS

Matrix3x3 = List[List[float]]

TOLERANCE = 1e-6


def conventional_parameters(vectors: np.ndarray, lattice_type: str) -> SimpleNamespace:
    """
    The conventional cell parameters of primitive `vectors` of `lattice_type`.

    The conventional vectors are the type's multiplier times the primitive ones; alpha is
    the angle between the second and third, as the monoclinic standard cells use it.
    """
    conventional = np.array(PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS[lattice_type]) @ vectors
    lengths = np.linalg.norm(conventional, axis=1)
    cosines = [
        np.dot(conventional[1], conventional[2]) / (lengths[1] * lengths[2]),
        np.dot(conventional[0], conventional[2]) / (lengths[0] * lengths[2]),
        np.dot(conventional[0], conventional[1]) / (lengths[0] * lengths[1]),
    ]
    alpha, beta, gamma = (math.degrees(math.acos(max(-1.0, min(1.0, cosine)))) for cosine in cosines)
    return SimpleNamespace(a=lengths[0], b=lengths[1], c=lengths[2], alpha=alpha, beta=beta, gamma=gamma)


def get_vectors_in_standard_orientation(vectors: Matrix3x3, lattice_type: str) -> Matrix3x3:
    """
    `vectors` rotated rigidly onto the standard primitive cell of `lattice_type`.

    The rotation R solves vectors · R = standard. The standard cell is used only when R is
    a proper rotation, which holds when `vectors` are the type's primitive vectors in the
    standard choice and order; otherwise, for a lattice whose shape does not match its
    type, or that matches only by a reflection, `vectors` are returned unchanged.
    """
    if lattice_type not in PRIMITIVE_CELLS:
        return vectors
    vectors_array = np.array(vectors, dtype=float)
    parameters = conventional_parameters(vectors_array, lattice_type)
    standard = np.array(PRIMITIVE_CELLS[lattice_type](parameters), dtype=float)
    rotation = np.linalg.solve(vectors_array, standard)
    is_orthogonal = np.allclose(rotation.T @ rotation, np.eye(3), rtol=0, atol=TOLERANCE)
    if not is_orthogonal or np.linalg.det(rotation) <= 0:
        return vectors
    return standard.tolist()
