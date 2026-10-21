"""Two grains of a honeycomb monolayer matched along a boundary line by a lattice vector of each (60 degree basis)."""
from math import gcd
from typing import List, Tuple

import numpy as np

from .network import Monolayer

# a honeycomb lattice maps onto itself every 60 degrees; with two different sites (h-BN, MoS2) every 120
LATTICE_SYMMETRY_ANGLE = 60.0  # degrees


def get_chiral_basis(monolayer: Monolayer) -> np.ndarray:
    """The 60 degree basis in the lattice vectors: a and b, or a and a + b if a and b are 120 degrees apart."""
    first, second = monolayer.lattice_vectors
    return np.array([[1, 0], [0, 1]] if first @ second > 0 else [[1, 0], [1, 1]])


def get_across_vector(vector: Tuple[int, int]) -> np.ndarray:
    """The shortest lattice vector perpendicular to (n, m), a quarter turn clockwise from it (60 degree basis)."""
    across = np.array([vector[0] + 2 * vector[1], -2 * vector[0] - vector[1]])
    return across // gcd(*across.tolist())


def get_supercell_matrix(monolayer: Monolayer, vector: Tuple[int, int], number_of_periods_across: int) -> list:
    """The rectangular supercell of a grain, across and along the line, in the lattice vectors."""
    rows = np.array([number_of_periods_across * get_across_vector(vector), vector])
    return (rows @ get_chiral_basis(monolayer)).tolist()


def get_rotation(monolayer: Monolayer, first: Tuple[int, int], second: Tuple[int, int]) -> float:
    """Counterclockwise angle in degrees from the first vector to the second (60 degree basis)."""
    vectors = np.array([first, second]) @ get_chiral_basis(monolayer) @ monolayer.lattice_vectors
    (first_x, first_y), (second_x, second_y) = vectors
    return float(np.degrees(np.arctan2(second_y, second_x) - np.arctan2(first_y, first_x)))


def get_grain_supercell_matrices(
    monolayer: Monolayer, boundary_vectors: Tuple[Tuple[int, int], Tuple[int, int]], number_of_periods_across: int
) -> List[list]:
    """Supercell matrices of both grains, the second as given and turned by 180 degrees, where that is a rotation."""
    first, second = boundary_vectors
    if first[0] ** 2 + first[0] * first[1] + first[1] ** 2 != second[0] ** 2 + second[0] * second[1] + second[1] ** 2:
        raise ValueError(f"The boundary vectors {first} and {second} differ in length")
    symmetry_angle = LATTICE_SYMMETRY_ANGLE * (1 if len({column[0][0] for column in monolayer.columns}) == 1 else 2)
    pairs = []
    for turned in (second, (-second[0], -second[1])):
        rotation = get_rotation(monolayer, first, turned) % symmetry_angle
        if not (np.isclose(rotation, 0.0) or np.isclose(rotation, symmetry_angle)):
            vectors = (first, turned)
            pairs.append([get_supercell_matrix(monolayer, vector, number_of_periods_across) for vector in vectors])
    return pairs
