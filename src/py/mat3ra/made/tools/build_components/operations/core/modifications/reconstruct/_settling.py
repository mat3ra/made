"""Settling, the last step of the reconstruction: the rebuilt sites pulled to one bond length, the rest fixed."""
from functools import cached_property
from typing import Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from scipy.optimize import least_squares
from scipy.sparse import coo_matrix

from ......analyze.ring_network import BONDS_PER_SITE
from ......analyze.rings import Bonds

# second-neighbor distances (the angles) weigh a quarter of a bond, so bonds keep their length first; a bond enters
# twice (once per direction), hence sqrt(2 * 0.25) on the residual
SECOND_NEIGHBOR_WEIGHT = np.sqrt(0.5)


class NetworkSettling(InMemoryEntityPydantic):
    """
    Settles the movable sites of a planar network of three bonds per site by least squares, every other site fixed:
    each bond toward `bond_length`, and the ends of each two bonds of a site toward sqrt(3) times it (equal angles).
    Bonds are sorted by site; `tolerance` is that of least_squares on the coordinates, in angstrom.
    """

    model_config = {"arbitrary_types_allowed": True}

    positions: np.ndarray
    bonds: Bonds
    movable: np.ndarray
    bond_length: float
    tolerance: float

    @cached_property
    def variables(self) -> np.ndarray:
        """The movable sites, whose positions are the variables of the fit."""
        return np.where(self.movable)[0]

    @cached_property
    def distance_terms(self) -> Tuple[np.ndarray, ...]:
        """(start, end, offset to the image of end, target, weight) of each term touching a movable site."""
        first, second, edge_vectors = self.bonds
        offsets = edge_vectors - (self.positions[second] - self.positions[first])
        bond_indices = np.arange(len(first))
        following = bond_indices - bond_indices % BONDS_PER_SITE + (bond_indices + 1) % BONDS_PER_SITE
        pairs = np.unique(np.sort(np.column_stack([bond_indices, following]), axis=1), axis=0)
        bond_starts = np.concatenate([first, second[pairs[:, 0]]])
        bond_ends = np.concatenate([second, second[pairs[:, 1]]])
        offsets = np.concatenate([offsets, offsets[pairs[:, 1]] - offsets[pairs[:, 0]]])
        targets = np.repeat([self.bond_length, np.sqrt(3) * self.bond_length], [len(first), len(pairs)])
        weights = np.repeat([1.0, SECOND_NEIGHBOR_WEIGHT], [len(first), len(pairs)])
        terms = self.movable[bond_starts] | self.movable[bond_ends]
        return bond_starts[terms], bond_ends[terms], offsets[terms], targets[terms], weights[terms]

    def get_distance_residuals(self, coordinates: np.ndarray) -> np.ndarray:
        """Weighted deviation of each distance term from its target, the movable sites at the given coordinates."""
        bond_starts, bond_ends, offsets, targets, weights = self.distance_terms
        positions = self.positions.copy()
        positions[self.variables] = coordinates.reshape(-1, 2)
        return weights * (np.linalg.norm(positions[bond_ends] - positions[bond_starts] + offsets, axis=1) - targets)

    @cached_property
    def jacobian_sparsity(self) -> coo_matrix:
        """Residual i depends on the two coordinates of each movable end of distance term i."""
        columns = np.cumsum(self.movable) - 1
        rows, variable_columns = [], []
        for points in self.distance_terms[:2]:
            for axis in (0, 1):
                rows.append(np.where(self.movable[points])[0])
                variable_columns.append(2 * columns[points[self.movable[points]]] + axis)
        rows, variable_columns = np.concatenate(rows), np.concatenate(variable_columns)
        shape = (len(self.distance_terms[0]), 2 * len(self.variables))
        return coo_matrix((np.ones(len(rows)), (rows, variable_columns)), shape=shape)

    @cached_property
    def settled_positions(self) -> np.ndarray:
        """All positions, the movable ones at the least-squares minimum of the distance residuals."""
        result = least_squares(
            self.get_distance_residuals,
            self.positions[self.variables].ravel(),
            jac_sparsity=self.jacobian_sparsity,
            ftol=self.tolerance,
            xtol=self.tolerance,
            gtol=self.tolerance,
        )
        settled = self.positions.copy()
        settled[self.variables] = result.x.reshape(-1, 2)
        return settled
