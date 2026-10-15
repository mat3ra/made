"""
Rebuilds the sites near both lines of a honeycomb grain boundary (graphene, h-BN, MoS2) into rings of a chosen core.

The hexagon centres of both stacked grains are the ring centres; the rebuilt sites are the vertices of their periodic
Voronoi network, each given the column of atoms of its sublattice and settled by least squares on the bond and
second-neighbor distances of the input lattice. Every site away from the lines stays the stacked one.
"""

from functools import cached_property
from typing import List, Tuple, Union

import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.material import BasisUnitsEnum
from mat3ra.made.basis import Basis
from mat3ra.made.basis.coordinates import Coordinates
from mat3ra.made.material import Material
from scipy.optimize import least_squares
from scipy.sparse import coo_matrix
from scipy.spatial import Delaunay, cKDTree

from .....analyze.rings import IMAGE_SHIFTS, Bonds, RingsMaterialAnalyzer, RingsNetworkAnalyzer
from .....build_components import MaterialWithBuildMetadata

# weight of the second-neighbor distance terms against a bond, which enters once per direction
SECOND_NEIGHBOR_WEIGHT = np.sqrt(0.5)
BOND_PAIRS_AT_SITE = [[0, 1], [0, 2], [1, 2]]


def wrap(points: np.ndarray, cell: np.ndarray) -> np.ndarray:
    wrapped = points % cell
    return np.where(np.isclose(wrapped, cell), 0.0, wrapped)


def get_circumcenters(triangles: np.ndarray) -> np.ndarray:
    second, third = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    second_squared, third_squared = (second**2).sum(axis=1), (third**2).sum(axis=1)
    denominator = 2 * (second[:, 0] * third[:, 1] - second[:, 1] * third[:, 0])
    x = (third[:, 1] * second_squared - second[:, 1] * third_squared) / denominator
    y = (second[:, 0] * third_squared - third[:, 0] * second_squared) / denominator
    return triangles[:, 0] + np.stack([x, y], axis=1)


def get_triangle_keys(simplices: np.ndarray, number_of_points: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Key of the periodic triangle behind each triangle of points tiled 3 x 3, and whether the triangle is the copy
    whose lowest-index point lies in the central tile.
    """
    points, tiles = simplices % number_of_points, simplices // number_of_points
    anchors = IMAGE_SHIFTS[tiles[np.arange(len(tiles)), np.argmin(points, axis=1)]]
    relative = IMAGE_SHIFTS[tiles] - anchors[:, None]
    corners = np.sort(((relative[..., 0] + 1) * 3 + relative[..., 1] + 1) * number_of_points + points, axis=1)
    base = 9 * number_of_points
    return (corners[:, 0] * base + corners[:, 1]) * base + corners[:, 2], np.all(anchors == 0, axis=1)


def get_distance_residuals(coordinates, positions, variables, starts, ends, offsets, targets, weights) -> np.ndarray:
    positions = positions.copy()
    positions[variables] = coordinates.reshape(-1, 2)
    return weights * (np.linalg.norm(positions[ends] - positions[starts] + offsets, axis=1) - targets)


def get_jacobian_sparsity(starts: np.ndarray, ends: np.ndarray, movable: np.ndarray) -> coo_matrix:
    columns = np.cumsum(movable) - 1
    rows, variable_columns = [], []
    for points in (starts, ends):
        for axis in (0, 1):
            rows.append(np.where(movable[points])[0])
            variable_columns.append(2 * columns[points[movable[points]]] + axis)
    rows, variable_columns = np.concatenate(rows), np.concatenate(variable_columns)
    return coo_matrix((np.ones(len(rows)), (rows, variable_columns)), shape=(len(starts), 2 * movable.sum()))


class HoneycombGrainLattice(InMemoryEntityPydantic):
    """
    Lattice of one grain in the stacked cell: vectors (rows), a site of sublattice 0, the offset to sublattice 1,
    and the two sites whose atoms are the columns of the sublattices.
    """

    model_config = {"arbitrary_types_allowed": True}

    vectors: np.ndarray
    origin: np.ndarray
    sublattice_offset: np.ndarray
    sublattice_sites: Tuple[int, int]

    def get_sublattices(self, points: np.ndarray) -> np.ndarray:
        distances = []
        for offset in (0.0, self.sublattice_offset):
            fractional = (points - self.origin - offset) @ np.linalg.inv(self.vectors)
            distances.append(np.linalg.norm((fractional - np.round(fractional)) @ self.vectors, axis=1))
        return np.argmin(distances, axis=0)


class GrainBoundaryCoreReconstruction(InMemoryEntityPydantic):
    """
    Grains labelled 0 and 1 stacked along x without a gap: the lines are at x = 0 and x = the width of grain 0, and the
    sites within `band_width` lattice constants of either line are rebuilt.
    """

    model_config = {"arbitrary_types_allowed": True}

    material: Union[Material, MaterialWithBuildMetadata]
    supercell_matrices: List[List[List[int]]]
    band_width: float = 2.0

    @cached_property
    def sites(self) -> RingsMaterialAnalyzer:
        return RingsMaterialAnalyzer(material=self.material)

    @cached_property
    def cell(self) -> np.ndarray:
        return np.diag(self.sites.lattice_vectors).copy()

    @cached_property
    def grain_widths(self) -> np.ndarray:
        areas = np.abs([np.linalg.det(matrix) for matrix in self.supercell_matrices])
        return self.cell[0] * areas / areas.sum()

    @cached_property
    def line_positions(self) -> List[float]:
        return [0.0, float(self.grain_widths[0])]

    @cached_property
    def site_grains(self) -> np.ndarray:
        return np.array(self.material.basis.labels.values)[self.sites.site_first_atoms]

    @cached_property
    def grain_lattices(self) -> List[HoneycombGrainLattice]:
        return [self.get_grain_lattice(grain) for grain in (0, 1)]

    def get_grain_lattice(self, grain: int) -> HoneycombGrainLattice:
        sites = np.where(self.site_grains == grain)[0]
        offsets = self.sites.site_positions[sites] - self.sites.site_positions[sites[0]]
        offsets -= np.round(offsets / self.cell) * self.cell
        nearest = 1 + np.argmin(np.linalg.norm(offsets[1:], axis=1))
        return HoneycombGrainLattice(
            vectors=np.linalg.inv(self.supercell_matrices[grain]) @ np.diag([self.grain_widths[grain], self.cell[1]]),
            origin=self.sites.site_positions[sites[0]],
            sublattice_offset=offsets[nearest],
            sublattice_sites=(sites[0], sites[nearest]),
        )

    @cached_property
    def site_distance(self) -> float:
        return float(np.linalg.norm(self.grain_lattices[0].sublattice_offset))

    @cached_property
    def kept_sites(self) -> np.ndarray:
        x_values = self.sites.site_positions[:, 0]
        distances = np.min([np.abs(x_values - line) for line in self.line_positions + [self.cell[0]]], axis=0)
        return np.where(distances >= self.band_width * np.sqrt(3) * self.site_distance)[0]

    @cached_property
    def ring_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Hexagon centres of each grain inside its own supercell, one per site of sublattice 0, and their grains.
        """
        centers = []
        for grain, lattice in enumerate(self.grain_lattices):
            sites = self.sites.site_positions[self.site_grains == grain]
            points = sites[lattice.get_sublattices(sites) == 0] - lattice.sublattice_offset
            start = self.line_positions[grain]
            points[:, 0] = start + wrap(points[:, 0] - start, self.grain_widths[grain])
            centers.append(wrap(points, self.cell))
        return np.vstack(centers), np.repeat([0, 1], [len(points) for points in centers])

    def get_network(self, slide: float) -> Tuple[np.ndarray, Bonds, np.ndarray, np.ndarray]:
        """
        Voronoi network of the ring centres with grain 1 slid by `slide` along y: vertex positions, bonds, and the
        grain and sublattice of each vertex.
        """
        centers, grains = self.ring_centers
        centers = wrap(centers + np.outer(grains, [0.0, slide]), self.cell)
        images = (centers[None] + (IMAGE_SHIFTS * self.cell)[:, None]).reshape(-1, 2)
        triangulation = Delaunay(images)
        keys, central = get_triangle_keys(triangulation.simplices, len(centers))
        vertices = np.where(central)[0][np.argsort(keys[central])]
        neighbors = triangulation.neighbors[vertices].ravel()
        circumcenters = get_circumcenters(images[triangulation.simplices[np.concatenate([vertices, neighbors])]])
        positions = circumcenters[: len(vertices)]
        bonds = (
            np.repeat(np.arange(len(vertices)), 3),
            np.searchsorted(keys[vertices], keys[neighbors]),
            circumcenters[len(vertices) :] - np.repeat(positions, 3, axis=0),
        )
        vertex_grains = (grains[triangulation.simplices[vertices] % len(centers)].sum(axis=1) >= 2).astype(int)
        unslid_positions = positions - np.outer(vertex_grains, [0.0, slide])
        sublattices = [lattice.get_sublattices(unslid_positions) for lattice in self.grain_lattices]
        return positions, bonds, vertex_grains, np.choose(vertex_grains, sublattices)

    def get_column_sites(self, grains: np.ndarray, sublattices: np.ndarray) -> np.ndarray:
        return np.array([lattice.sublattice_sites for lattice in self.grain_lattices])[grains, sublattices]

    def get_rings_analyzer(self, slide: float) -> RingsNetworkAnalyzer:
        positions, bonds, grains, sublattices = self.get_network(slide)
        species = self.sites.site_species[self.get_column_sites(grains, sublattices)]
        return RingsNetworkAnalyzer(
            material=self.material, network_positions=positions, network_species=species, network_bonds=bonds
        )

    def get_settled_positions(self, positions: np.ndarray, bonds: Bonds, movable: np.ndarray) -> np.ndarray:
        first, second, vectors = bonds
        offsets = vectors - (positions[second] - positions[first])
        pairs = np.arange(len(first)).reshape(-1, 3)[:, BOND_PAIRS_AT_SITE].reshape(-1, 2)
        starts = np.concatenate([first, second[pairs[:, 0]]])
        ends = np.concatenate([second, second[pairs[:, 1]]])
        offsets = np.concatenate([offsets, offsets[pairs[:, 1]] - offsets[pairs[:, 0]]])
        targets = self.site_distance * np.repeat([1.0, np.sqrt(3)], [len(first), len(pairs)])
        weights = np.repeat([1.0, SECOND_NEIGHBOR_WEIGHT], [len(first), len(pairs)])
        terms = movable[starts] | movable[ends]
        variables = np.where(movable)[0]
        result = least_squares(
            get_distance_residuals,
            positions[variables].ravel(),
            jac_sparsity=get_jacobian_sparsity(starts[terms], ends[terms], movable),
            args=(positions, variables, starts[terms], ends[terms], offsets[terms], targets[terms], weights[terms]),
            ftol=1e-10,
            xtol=1e-10,
            gtol=1e-10,
        )
        settled = positions.copy()
        settled[variables] = result.x.reshape(-1, 2)
        return settled

    def get_material(self) -> Union[Material, MaterialWithBuildMetadata]:
        positions, bonds, grains, sublattices = self.get_network(0.0)
        kept_positions = self.sites.site_positions[self.kept_sites]
        kept = cKDTree(wrap(positions, self.cell), boxsize=self.cell).query(wrap(kept_positions, self.cell))[1]
        movable = np.ones(len(positions), bool)
        movable[kept] = False
        settled = wrap(self.get_settled_positions(positions, bonds, movable), self.cell)
        column_sites = self.get_column_sites(grains[movable], sublattices[movable])
        return self.get_assembled_material(settled[movable], column_sites, grains[movable])

    def get_assembled_material(
        self, positions: np.ndarray, column_sites: np.ndarray, grains: np.ndarray
    ) -> Union[Material, MaterialWithBuildMetadata]:
        material = self.material.clone()
        material.to_cartesian()
        coordinates = np.array(material.basis.coordinates.values)
        elements, labels = np.array(material.basis.elements.values), np.array(material.basis.labels.values)
        kept_atoms = np.where(np.isin(self.sites.atom_site_indices, self.kept_sites))[0]
        columns = [np.where(self.sites.atom_site_indices == site)[0] for site in column_sites]
        column_atoms, repeats = np.concatenate(columns), [len(column) for column in columns]
        added_coordinates = np.column_stack([np.repeat(positions, repeats, axis=0), coordinates[column_atoms, 2]])
        material.basis = Basis(
            elements=ArrayWithIds.from_values(elements[np.concatenate([kept_atoms, column_atoms])].tolist()),
            coordinates=Coordinates.from_values(np.vstack([coordinates[kept_atoms], added_coordinates]).tolist()),
            units=BasisUnitsEnum.cartesian,
            cell=material.basis.cell,
            labels=ArrayWithIds.from_values(np.concatenate([labels[kept_atoms], np.repeat(grains, repeats)]).tolist()),
        )
        material.to_crystal()
        return material
