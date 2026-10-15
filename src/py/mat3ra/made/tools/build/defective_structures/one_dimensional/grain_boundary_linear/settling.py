"""
Settles the rebuilt sites of a grain boundary network in the plane: least squares on the bond and second-neighbor
distances of the input honeycomb, every other site fixed.
"""

from functools import cached_property
from itertools import combinations
from typing import Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from scipy.optimize import least_squares
from scipy.sparse import coo_matrix

from .....analyze.grain_boundary_network import BONDS_PER_SITE
from .....analyze.rings import Bonds

# weight of a second-neighbor distance against a bond, which enters once per direction
SECOND_NEIGHBOR_WEIGHT = np.sqrt(0.5)
SECOND_NEIGHBOR_DISTANCE_FACTOR = np.sqrt(3)
SETTLING_TOLERANCE = 1e-10
BOND_PAIRS_AT_SITE = list(combinations(range(BONDS_PER_SITE), 2))


def get_distance_residuals(coordinates, positions, variables, bond_starts, bond_ends, offsets, targets, weights):
    positions = positions.copy()
    positions[variables] = coordinates.reshape(-1, 2)
    return weights * (np.linalg.norm(positions[bond_ends] - positions[bond_starts] + offsets, axis=1) - targets)


def get_jacobian_sparsity(bond_starts: np.ndarray, bond_ends: np.ndarray, movable: np.ndarray) -> coo_matrix:
    """Residual i depends on the two coordinates of each movable end of distance term i."""
    columns = np.cumsum(movable) - 1
    rows, variable_columns = [], []
    for points in (bond_starts, bond_ends):
        for axis in (0, 1):
            rows.append(np.where(movable[points])[0])
            variable_columns.append(2 * columns[points[movable[points]]] + axis)
    rows, variable_columns = np.concatenate(rows), np.concatenate(variable_columns)
    return coo_matrix((np.ones(len(rows)), (rows, variable_columns)), shape=(len(bond_starts), 2 * movable.sum()))


class NetworkSettling(InMemoryEntityPydantic):
    """
    Network positions, bonds grouped by site with BONDS_PER_SITE each, the movable sites and the bond length of the
    input lattice; second neighbors are the two ends of two bonds at one site, at sqrt(3) times the bond length.
    """

    model_config = {"arbitrary_types_allowed": True}

    positions: np.ndarray
    bonds: Bonds
    movable: np.ndarray
    site_distance: float

    @cached_property
    def distance_terms(self) -> Tuple[np.ndarray, ...]:
        """(start, end, offset to the image of end, target, weight) of each term touching a movable site."""
        first, second, edge_vectors = self.bonds
        offsets = edge_vectors - (self.positions[second] - self.positions[first])
        pairs = np.arange(len(first)).reshape(-1, BONDS_PER_SITE)[:, BOND_PAIRS_AT_SITE].reshape(-1, 2)
        bond_starts = np.concatenate([first, second[pairs[:, 0]]])
        bond_ends = np.concatenate([second, second[pairs[:, 1]]])
        offsets = np.concatenate([offsets, offsets[pairs[:, 1]] - offsets[pairs[:, 0]]])
        targets = self.site_distance * np.repeat([1.0, SECOND_NEIGHBOR_DISTANCE_FACTOR], [len(first), len(pairs)])
        weights = np.repeat([1.0, SECOND_NEIGHBOR_WEIGHT], [len(first), len(pairs)])
        terms = self.movable[bond_starts] | self.movable[bond_ends]
        return bond_starts[terms], bond_ends[terms], offsets[terms], targets[terms], weights[terms]

    @cached_property
    def settled_positions(self) -> np.ndarray:
        variables = np.where(self.movable)[0]
        bond_starts, bond_ends = self.distance_terms[:2]
        result = least_squares(
            get_distance_residuals,
            self.positions[variables].ravel(),
            jac_sparsity=get_jacobian_sparsity(bond_starts, bond_ends, self.movable),
            args=(self.positions, variables, *self.distance_terms),
            ftol=SETTLING_TOLERANCE,
            xtol=SETTLING_TOLERANCE,
            gtol=SETTLING_TOLERANCE,
        )
        settled = self.positions.copy()
        settled[variables] = result.x.reshape(-1, 2)
        return settled
