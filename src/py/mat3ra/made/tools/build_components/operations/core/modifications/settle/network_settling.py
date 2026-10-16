from functools import cached_property
from typing import Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from scipy.optimize import least_squares
from scipy.sparse import coo_matrix

from ......analyze.rings import Bonds

# weight of a second-neighbor distance against a bond, which enters once per direction
SECOND_NEIGHBOR_WEIGHT = np.sqrt(0.5)
SETTLING_TOLERANCE = 1e-10


class NetworkSettling(InMemoryEntityPydantic):
    """
    Settles the movable sites of a planar network of bonded sites by least squares, every other site fixed: each bond
    toward its length in `bond_lengths`, and the ends of each two bonds next to each other around a site toward their
    distance at equal angles around it (sqrt(3) times the bond length for three equal bonds). Bonds are grouped by
    site, in order around it.
    """

    model_config = {"arbitrary_types_allowed": True}

    positions: np.ndarray
    bonds: Bonds
    movable: np.ndarray
    bond_lengths: np.ndarray

    @cached_property
    def variables(self) -> np.ndarray:
        return np.where(self.movable)[0]

    @cached_property
    def neighbor_bond_pairs(self) -> np.ndarray:
        """Each two bonds next to each other around a site, once, the earlier bond first."""
        first = self.bonds[0]
        bonds_at_site, starts = np.bincount(first)[first], np.searchsorted(first, first)
        following = starts + (np.arange(len(first)) - starts + 1) % bonds_at_site
        return np.unique(np.sort(np.column_stack([np.arange(len(first)), following]), axis=1), axis=0)

    def get_second_neighbor_distances(self, pairs: np.ndarray) -> np.ndarray:
        """Distance between the ends of two bonds of their lengths, at 360 degrees over the bonds of their site."""
        lengths = self.bond_lengths[pairs]
        chords = 2 * np.sin(np.pi / np.bincount(self.bonds[0])[self.bonds[0][pairs[:, 0]]])
        return np.sqrt((lengths[:, 0] - lengths[:, 1]) ** 2 + (chords * np.sqrt(lengths[:, 0] * lengths[:, 1])) ** 2)

    @cached_property
    def distance_terms(self) -> Tuple[np.ndarray, ...]:
        """(start, end, offset to the image of end, target, weight) of each term touching a movable site."""
        first, second, edge_vectors = self.bonds
        offsets = edge_vectors - (self.positions[second] - self.positions[first])
        pairs = self.neighbor_bond_pairs
        bond_starts = np.concatenate([first, second[pairs[:, 0]]])
        bond_ends = np.concatenate([second, second[pairs[:, 1]]])
        offsets = np.concatenate([offsets, offsets[pairs[:, 1]] - offsets[pairs[:, 0]]])
        targets = np.concatenate([self.bond_lengths, self.get_second_neighbor_distances(pairs)])
        weights = np.repeat([1.0, SECOND_NEIGHBOR_WEIGHT], [len(first), len(pairs)])
        terms = self.movable[bond_starts] | self.movable[bond_ends]
        return bond_starts[terms], bond_ends[terms], offsets[terms], targets[terms], weights[terms]

    def get_distance_residuals(self, coordinates: np.ndarray) -> np.ndarray:
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
        result = least_squares(
            self.get_distance_residuals,
            self.positions[self.variables].ravel(),
            jac_sparsity=self.jacobian_sparsity,
            ftol=SETTLING_TOLERANCE,
            xtol=SETTLING_TOLERANCE,
            gtol=SETTLING_TOLERANCE,
        )
        settled = self.positions.copy()
        settled[self.variables] = result.x.reshape(-1, 2)
        return settled
