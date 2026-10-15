"""
Ring network of a honeycomb grain boundary (graphene, h-BN, MoS2): grains labelled 0 and 1 stacked along x without a
gap, the boundary lines at x = 0 and x = the width of grain 0. The hexagon centres of both grains are the ring centres;
the sites are the vertices of their periodic Voronoi network, for any slide of grain 1 along the lines.
"""

from functools import cached_property
from typing import List, Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from scipy.spatial import Delaunay, cKDTree

from .rings import IMAGE_SHIFTS, Bonds, RingsMaterialAnalyzer, RingsNetworkAnalyzer, get_periodic_images

# a Voronoi vertex is the circumcentre of one Delaunay triangle, so every site of the network has three bonds
BONDS_PER_SITE = 3


def wrap_to_cell(points: np.ndarray, cell: np.ndarray) -> np.ndarray:
    """Points modulo a rectangular cell, values within rounding of the cell edge mapped to 0 (one owner per edge)."""
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
    For triangles of points tiled 3 x 3 (point index = tile * number_of_points + point): one integer key per periodic
    triangle, the same for all its copies, and whether a triangle is the copy whose lowest point lies in the central
    tile. The key encodes the three points as tile index relative to that lowest point times number_of_points plus
    point, sorted, in base 9 * number_of_points.
    """
    points, tiles = simplices % number_of_points, simplices // number_of_points
    anchors = IMAGE_SHIFTS[tiles[np.arange(len(tiles)), np.argmin(points, axis=1)]]
    relative = IMAGE_SHIFTS[tiles] - anchors[:, None]
    corners = np.sort(((relative[..., 0] + 1) * 3 + relative[..., 1] + 1) * number_of_points + points, axis=1)
    base = 9 * number_of_points
    return (corners[:, 0] * base + corners[:, 1]) * base + corners[:, 2], np.all(anchors == 0, axis=1)


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
        """Sublattice (0 or 1) whose nearest lattice point is closest to each point."""
        distances = []
        for offset in (0.0, self.sublattice_offset):
            fractional = (points - self.origin - offset) @ np.linalg.inv(self.vectors)
            distances.append(np.linalg.norm((fractional - np.round(fractional)) @ self.vectors, axis=1))
        return np.argmin(distances, axis=0)


class GrainBoundaryRingNetworkAnalyzer(RingsMaterialAnalyzer):
    """
    The sites within `band_width` lattice constants of either line are the ones the network rebuilds; every other
    site keeps its stacked position, as a vertex of ring centres that are all bulk.
    """

    supercell_matrices: List[List[List[int]]]
    band_width: float = 2.0

    @cached_property
    def cell(self) -> np.ndarray:
        return np.diag(self.lattice_vectors).copy()

    @cached_property
    def grain_widths(self) -> np.ndarray:
        areas = np.abs([np.linalg.det(matrix) for matrix in self.supercell_matrices])
        return self.cell[0] * areas / areas.sum()

    @cached_property
    def line_positions(self) -> List[float]:
        return [0.0, float(self.grain_widths[0])]

    @cached_property
    def site_grains(self) -> np.ndarray:
        return np.array(self.material.basis.labels.values)[self.site_first_atoms]

    @cached_property
    def grain_lattices(self) -> List[HoneycombGrainLattice]:
        return [self.get_grain_lattice(grain) for grain in (0, 1)]

    def get_grain_lattice(self, grain: int) -> HoneycombGrainLattice:
        """Vectors from the grain's supercell matrix; sublattice 1 is the nearest other site of the same grain."""
        sites = np.where(self.site_grains == grain)[0]
        offsets = self.site_positions[sites] - self.site_positions[sites[0]]
        offsets -= np.round(offsets / self.cell) * self.cell
        nearest = 1 + np.argmin(np.linalg.norm(offsets[1:], axis=1))
        return HoneycombGrainLattice(
            vectors=np.linalg.inv(self.supercell_matrices[grain]) @ np.diag([self.grain_widths[grain], self.cell[1]]),
            origin=self.site_positions[sites[0]],
            sublattice_offset=offsets[nearest],
            sublattice_sites=(sites[0], sites[nearest]),
        )

    @cached_property
    def site_distance(self) -> float:
        return float(np.linalg.norm(self.grain_lattices[0].sublattice_offset))

    @cached_property
    def kept_sites(self) -> np.ndarray:
        """Sites at `band_width` lattice constants or more from both lines."""
        x_values = self.site_positions[:, 0]
        distances = np.min([np.abs(x_values - line) for line in self.line_positions + [self.cell[0]]], axis=0)
        return np.where(distances >= self.band_width * np.sqrt(3) * self.site_distance)[0]

    @cached_property
    def ring_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        """Hexagon centres of each grain inside its own supercell, one per site of sublattice 0, and their grains."""
        centers = []
        for grain, lattice in enumerate(self.grain_lattices):
            sites = self.site_positions[self.site_grains == grain]
            points = sites[lattice.get_sublattices(sites) == 0] - lattice.sublattice_offset
            start = self.line_positions[grain]
            points[:, 0] = start + wrap_to_cell(points[:, 0] - start, self.grain_widths[grain])
            centers.append(wrap_to_cell(points, self.cell))
        return np.vstack(centers), np.repeat([0, 1], [len(points) for points in centers])

    def get_network(self, slide: float) -> Tuple[np.ndarray, Bonds, np.ndarray, np.ndarray]:
        """
        Voronoi network of the ring centres with the second grain (label 1) slid by `slide` along y: vertex positions,
        bonds grouped by vertex (BONDS_PER_SITE each), the grain holding most of each vertex's ring centres and its
        sublattice there.
        """
        centers, grains = self.ring_centers
        centers = wrap_to_cell(centers + np.outer(grains, [0.0, slide]), self.cell)
        images = get_periodic_images(centers, self.lattice_vectors)
        triangulation = Delaunay(images)
        keys, central = get_triangle_keys(triangulation.simplices, len(centers))
        vertices = np.where(central)[0][np.argsort(keys[central])]
        neighbors = triangulation.neighbors[vertices].ravel()
        circumcenters = get_circumcenters(images[triangulation.simplices[np.concatenate([vertices, neighbors])]])
        positions = circumcenters[: len(vertices)]
        first = np.repeat(np.arange(len(vertices)), BONDS_PER_SITE)
        second = np.searchsorted(keys[vertices], keys[neighbors])
        edge_vectors = circumcenters[len(vertices) :] - positions[first]
        vertex_grains = (grains[triangulation.simplices[vertices] % len(centers)].sum(axis=1) >= 2).astype(int)
        return (
            positions,
            (first, second, edge_vectors),
            vertex_grains,
            self.get_sublattices(positions, vertex_grains, slide),
        )

    def get_sublattices(self, positions: np.ndarray, grains: np.ndarray, slide: float) -> np.ndarray:
        """Sublattice of each vertex in the lattice of its grain, the second grain slid by `slide`."""
        unslid_positions = positions - np.outer(grains, [0.0, slide])
        return np.choose(grains, [lattice.get_sublattices(unslid_positions) for lattice in self.grain_lattices])

    def get_kept_vertices(self, positions: np.ndarray) -> np.ndarray:
        """The network vertex at each kept site."""
        kept_positions = wrap_to_cell(self.site_positions[self.kept_sites], self.cell)
        return cKDTree(wrap_to_cell(positions, self.cell), boxsize=self.cell).query(kept_positions)[1]

    def get_column_sites(self, grains: np.ndarray, sublattices: np.ndarray) -> np.ndarray:
        """The stacked site whose atoms each vertex takes: that of its grain and sublattice."""
        return np.array([lattice.sublattice_sites for lattice in self.grain_lattices])[grains, sublattices]

    def get_rings_analyzer(self, slide: float) -> RingsNetworkAnalyzer:
        positions, bonds, grains, sublattices = self.get_network(slide)
        species = self.site_species[self.get_column_sites(grains, sublattices)]
        return RingsNetworkAnalyzer(
            material=self.material, network_positions=positions, network_species=species, network_bonds=bonds
        )
