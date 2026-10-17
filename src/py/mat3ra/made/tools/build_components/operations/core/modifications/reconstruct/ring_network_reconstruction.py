"""
Steps 2 to 5 of the grain boundary construction: the band along each line rebuilt as the dual of both grains'
hexagon centres (Ophus et al., PRB 92, 205402 (2015)), ties split by one rule, each site taking the atoms of the basis
site it maps onto, then settled.
"""
from functools import cached_property
from typing import List, Tuple

import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.material import BasisUnitsEnum
from mat3ra.made.basis import Basis
from mat3ra.made.basis.coordinates import Coordinates
from mat3ra.made.material import Material
from scipy.spatial import Delaunay

from ......analyze.rings import (
    HEXAGON_SIZE,
    IMAGE_SHIFTS,
    RingsArrangement,
    RingsMaterialAnalyzer,
    get_line_arrangements,
    get_line_offsets,
)
from ..settle.network_settling import BONDS_PER_SITE, NetworkSettling

# positions this close are one: centres meant to share a circle lie within 7.6e-6 of it (rounded input coordinates), any
# other fourth centre 1.5e-5 or more from it; a tie's right-most corners coincide or lie 0.16 apart; stacked sites lie
# within 3e-8 of a band edge or 2.3e-3 and more from it (every candidate slide of the sweep)
POSITION_TOLERANCE = 1e-5  # angstrom
# a grain's lattice vectors (rows), a site of each sublattice, and the stacked sites whose atoms are their columns
GrainLattice = Tuple[np.ndarray, np.ndarray, np.ndarray]


def wrap_to_cell(values: np.ndarray, periods) -> np.ndarray:
    """Values modulo their periods, values within rounding of a period mapped to 0 (one owner per cell edge)."""
    wrapped = values % periods
    return np.where(np.isclose(wrapped, periods), 0.0, wrapped)


def get_circumcircles(triangles: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Centre and radius of the circle through the corners of each triangle."""
    second, third = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    second_squared, third_squared = (second**2).sum(axis=1), (third**2).sum(axis=1)
    denominator = 2 * (second[:, 0] * third[:, 1] - second[:, 1] * third[:, 0])
    x = (third[:, 1] * second_squared - second[:, 1] * third_squared) / denominator
    y = (second[:, 0] * third_squared - third[:, 0] * second_squared) / denominator
    return triangles[:, 0] + np.stack([x, y], axis=1), np.hypot(x, y)


def get_diagonal_flips(quadrilaterals: np.ndarray) -> np.ndarray:
    """
    For corners (p, q, r, s) of quadrilaterals split along p-q: whether the diagonal through the right-most corner, of
    two at one x the upper, is r-s instead.
    """
    x, y = quadrilaterals[..., 0], quadrilaterals[..., 1]
    is_right = x > x.max(axis=1, keepdims=True) - POSITION_TOLERANCE
    return np.argmax(np.where(is_right, y, -np.inf), axis=1) >= 2


def get_padded_images(positions: np.ndarray, cell: np.ndarray, margins: np.ndarray) -> Tuple[np.ndarray, ...]:
    """Positions in a rectangular cell and their images within `margins` (x, y) of it; each one's position and shift."""
    tiles = np.repeat(np.arange(len(IMAGE_SHIFTS)), len(positions))
    points = np.tile(np.arange(len(positions)), len(IMAGE_SHIFTS))
    images = positions[points] + IMAGE_SHIFTS[tiles] * cell
    is_near = np.all((images > -margins) & (images < cell + margins), axis=1)
    return images[is_near], points[is_near], tiles[is_near]


def get_periodic_keys(points: np.ndarray, tiles: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    For triangles of points (rows of point indices) in image shifts (rows of IMAGE_SHIFTS indices): an integer the same
    for all copies of a triangle (each point with its shift relative to the lowest point's), and whether the triangle
    is the copy whose lowest point is not shifted.
    """
    number_of_points = points.max() + 1
    anchors = IMAGE_SHIFTS[tiles[np.arange(len(tiles)), np.argmin(points, axis=1)]]
    # a shift relative to the lowest point's runs from -2 to 2 per axis: five values each, 25 per point
    relative = IMAGE_SHIFTS[tiles] - anchors[:, None] + 2
    corners = np.sort((relative[..., 0] * 5 + relative[..., 1]) * number_of_points + points, axis=1)
    base = 25 * number_of_points
    return (corners[:, 0] * base + corners[:, 1]) * base + corners[:, 2], np.all(anchors == 0, axis=1)


def get_triangle_neighbors(simplices: np.ndarray) -> np.ndarray:
    """Neighbor of each triangle across the edge opposite each of its corners, -1 at the outer border."""
    edges = np.stack([simplices[:, [1, 2]], simplices[:, [2, 0]], simplices[:, [0, 1]]], axis=1).reshape(-1, 2)
    keys = np.sort(edges, axis=1) @ np.array([simplices.max() + 1, 1])
    order = np.argsort(keys, kind="stable")
    shared = np.flatnonzero(keys[order][1:] == keys[order][:-1])
    neighbors = -np.ones(len(keys), int)
    neighbors[order[shared]], neighbors[order[shared + 1]] = order[shared + 1] // 3, order[shared] // 3
    return neighbors.reshape(-1, 3)


def get_sublattices(points: np.ndarray, lattice: GrainLattice) -> np.ndarray:
    """Sublattice of each point: the one whose nearest lattice point is nearer."""
    vectors, origins, _ = lattice
    fractional = (points[:, None] - origins) @ np.linalg.inv(vectors)
    return np.argmin(np.linalg.norm((fractional - np.round(fractional)) @ vectors, axis=2), axis=1)


class RingNetwork(InMemoryEntityPydantic):
    """
    The dual of ring centres (and their grains) in a cell: a site per triangle at its centroid, the centres at its
    corners, the neighbor site across each edge and the vector to it; the rebuilt sites and the co-circular pairs there.
    """

    model_config = {"arbitrary_types_allowed": True}

    centers: np.ndarray
    center_grains: np.ndarray
    positions: np.ndarray
    corners: np.ndarray
    neighbors: np.ndarray
    vectors: np.ndarray
    is_rebuilt: np.ndarray
    number_of_ties: int


class RingNetworkReconstruction(InMemoryEntityPydantic):
    """
    Rebuilds the bands within `band_width` lattice constants of both lines of two honeycomb grains stacked along x
    without a gap (labels 0 and 1, lines at x = 0 and x = the width of grain 0) as the dual of the grains' hexagon
    centres: a site per Delaunay triangle, bonded across its edges, with the atoms of the input basis site it maps onto
    in the grain of most of its centres; then settles them to the bond length, every stacked atom outside the bands
    kept. The hexagon centres of grain 1 are slid by `slide` along y.
    """

    model_config = {"arbitrary_types_allowed": True}

    material: Material
    supercell_matrices: List[List[List[int]]]
    slide: float = 0.0
    band_width: float
    settling_tolerance: float

    @cached_property
    def sites(self) -> RingsMaterialAnalyzer:
        """The top-view sites (atom columns) of the stacked grains."""
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
    def grain_lattices(self) -> List[GrainLattice]:
        """Each grain's vectors (from its supercell matrix), its first site and that site's nearest neighbor."""
        site_grains = np.array(self.material.basis.labels.values)[self.sites.site_first_atoms]
        lattices = []
        for grain, matrix in enumerate(self.supercell_matrices):
            sites = np.flatnonzero(site_grains == grain)
            offsets = self.sites.site_positions[sites] - self.sites.site_positions[sites[0]]
            offsets -= np.round(offsets / self.cell) * self.cell
            nearest = 1 + np.argmin(np.linalg.norm(offsets[1:], axis=1))
            vectors = np.linalg.inv(matrix) @ np.diag([self.grain_widths[grain], self.cell[1]])
            origins = self.sites.site_positions[sites[0]] + np.array([[0.0, 0.0], offsets[nearest]])
            lattices.append((vectors, origins, sites[[0, nearest]]))
        return lattices

    @cached_property
    def bond_length(self) -> float:
        return float(np.linalg.norm(np.diff(self.grain_lattices[0][1], axis=0)))

    @cached_property
    def hexagon_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Hexagon centres of each grain inside its own supercell, one per site of its first sublattice, and their grains,
        by grain and position in the grain's lattice in whole thirds of its vectors (so no rounding digit decides).
        """
        site_grains = np.array(self.material.basis.labels.values)[self.sites.site_first_atoms]
        centers = []
        for grain, lattice in enumerate(self.grain_lattices):
            vectors, origins, _ = lattice
            positions = self.sites.site_positions[site_grains == grain]
            points = positions[get_sublattices(positions, lattice) == 0] - np.diff(origins, axis=0)
            start = self.line_positions[grain]
            points[:, 0] = start + wrap_to_cell(points[:, 0] - start, self.grain_widths[grain])
            points = wrap_to_cell(points, self.cell)
            thirds = np.round(3 * (points - origins[0]) @ np.linalg.inv(vectors)).astype(int)
            centers.append(points[np.lexsort(thirds.T[::-1])])
        return np.vstack(centers), np.repeat([0, 1], [len(points) for points in centers])

    @cached_property
    def band_edge(self) -> float:
        """Distance from a line within which sites are rebuilt, short of the band width by the position tolerance."""
        return self.band_width * np.sqrt(3) * self.bond_length - POSITION_TOLERANCE

    @cached_property
    def reach(self) -> float:
        """
        How far beyond the band the centres are taken: three lattice constants, so that the triangles beside a fixed
        site bonded to a rebuilt one (settled through it) and their circumcircles lie among them.
        """
        return 3 * np.sqrt(3) * self.bond_length

    def get_line_distances(self, x_values: np.ndarray) -> np.ndarray:
        return np.abs(get_line_offsets(x_values, self.line_positions, self.cell[0])).min(axis=1)

    def get_resolved_simplices(self, points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Delaunay triangles of the points; two triangles with their four corners on one circle centred in a band (the
        centres of two grains meet only at a line) split along the diagonal get_diagonal_flips chooses; and whether each
        triangle came from such a pair.
        """
        delaunay = Delaunay(points)
        simplices = delaunay.simplices.copy()
        centers, radii = get_circumcircles(points[simplices])
        triangles, corners = np.nonzero(delaunay.neighbors > np.arange(len(simplices))[:, None])
        others = delaunay.neighbors[triangles, corners]
        fourth = simplices[others].sum(axis=1) - simplices[triangles].sum(axis=1) + simplices[triangles, corners]
        distances = np.abs(np.linalg.norm(points[fourth] - centers[triangles], axis=1) - radii[triangles])
        is_pair = (distances < POSITION_TOLERANCE) & (self.get_line_distances(centers[triangles, 0]) < self.band_edge)
        triangles, corners, others, fourth = triangles[is_pair], corners[is_pair], others[is_pair], fourth[is_pair]
        shared = simplices[triangles][np.arange(3) != corners[:, None]].reshape(-1, 2)
        quadrilaterals = np.column_stack([shared, simplices[triangles, corners], fourth])
        flips = get_diagonal_flips(points[quadrilaterals])
        simplices[triangles[flips]] = quadrilaterals[flips][:, [2, 3, 0]]
        simplices[others[flips]] = quadrilaterals[flips][:, [2, 3, 1]]
        is_tied = np.zeros(len(simplices), bool)
        is_tied[np.concatenate([triangles, others])] = True
        return simplices, is_tied

    def get_network(self, slide: float) -> RingNetwork:
        """
        The ring network of the hexagon centres within the band and `reach` of a line, and of their images as near the
        cell across the lines and within `reach` of it along them, grain 1's slid by `slide`; its sites by periodic key.
        A triangle beside a site that has no copy among the sites (past the centres taken) is no neighbor: the site's
        bond across that edge points to itself.
        """
        centers, grains = self.hexagon_centers
        centers = wrap_to_cell(centers + np.outer(grains, [0.0, slide]), self.cell)
        nearby = self.get_line_distances(centers[:, 0]) < self.band_edge + self.reach
        centers, grains = centers[nearby], grains[nearby]
        images, points, tiles = get_padded_images(centers, self.cell, np.array([self.band_edge, 0.0]) + self.reach)
        simplices, is_tied = self.get_resolved_simplices(images)
        keys, central = get_periodic_keys(points[simplices], tiles[simplices])
        sites = np.flatnonzero(central)[np.argsort(keys[central])]
        neighbors = get_triangle_neighbors(simplices)[sites]
        positions = images[simplices].mean(axis=1)
        neighbor_sites = np.searchsorted(keys[sites], keys[neighbors]) % len(sites)
        is_site = keys[sites][neighbor_sites] == keys[neighbors]
        is_rebuilt = self.get_line_distances(positions[sites, 0]) < self.band_edge
        if not np.all(is_site[is_rebuilt]):
            raise ValueError(
                f"The cell is too short along the boundary ({self.cell[1]:.3f} angstrom) for its periodic ring "
                "network; use a multiple of the boundary vectors"
            )
        return RingNetwork(
            centers=centers,
            center_grains=grains,
            positions=positions[sites],
            corners=points[simplices[sites]],
            neighbors=np.where(is_site, neighbor_sites, np.arange(len(sites))[:, None]),
            vectors=np.where(is_site[..., None], positions[neighbors] - positions[sites][:, None], 0.0),
            is_rebuilt=is_rebuilt,
            number_of_ties=int(is_tied[sites][is_rebuilt].sum()) // 2,
        )

    def get_site_grains(self, network: RingNetwork) -> np.ndarray:
        return (network.center_grains[network.corners].sum(axis=1) >= 2).astype(int)

    def get_site_columns(self, network: RingNetwork, slide: float) -> np.ndarray:
        """
        The stacked site whose atoms each network site takes: that of its sublattice in its grain, read at the site's
        image inside the grain (the stacked width is a lattice vector of neither grain), grain 1's slide undone.
        """
        grains = self.get_site_grains(network)
        middles = np.array(self.line_positions) + self.grain_widths / 2
        images_across = np.round((network.positions[:, 0] - middles[grains]) / self.cell[0])
        points = network.positions - np.outer(images_across, [self.cell[0], 0.0]) - np.outer(grains, [0.0, slide])
        sublattices = np.choose(grains, [get_sublattices(points, lattice) for lattice in self.grain_lattices])
        return np.array([lattice[2] for lattice in self.grain_lattices])[grains, sublattices]

    def get_line_arrangements(self, network: RingNetwork, slide: float) -> List[RingsArrangement]:
        """Rings (a centre's ring size is its number of triangles) and homo bonds of the rebuilt bands, by line."""
        species = self.sites.site_species[self.get_site_columns(network, slide)]
        sizes = np.bincount(network.corners.ravel(), minlength=len(network.centers))
        sizes[self.get_line_distances(network.centers[:, 0]) >= self.band_edge] = HEXAGON_SIZE
        first = np.repeat(np.arange(len(network.positions)), BONDS_PER_SITE)
        second = network.neighbors.ravel()
        in_band = network.is_rebuilt[first] & network.is_rebuilt[second]
        bond_x = network.positions[first, 0] + network.vectors[..., 0].ravel() / 2
        return get_line_arrangements(
            (network.centers[:, 0], sizes),
            (network.corners.ravel(), np.roll(network.corners, 1, axis=1).ravel()),
            (bond_x[in_band], species[np.column_stack([first, second])][in_band]),
            self.line_positions,
            self.cell[0],
        )

    @cached_property
    def reconstructed_material(self) -> Material:
        """The stacked grains with the band along each line rebuilt and settled."""
        network = self.get_network(self.slide)
        rebuilt = network.is_rebuilt
        first = np.repeat(np.arange(len(rebuilt)), BONDS_PER_SITE)
        settling = NetworkSettling(
            positions=network.positions,
            bonds=(first, network.neighbors.ravel(), network.vectors.reshape(-1, 2)),
            movable=rebuilt,
            bond_length=self.bond_length,
            tolerance=self.settling_tolerance,
        )
        kept_atoms = np.flatnonzero(self.get_line_distances(self.sites.atom_positions[:, 0]) >= self.band_edge)
        columns = self.get_site_columns(network, self.slide)[rebuilt]
        positions = wrap_to_cell(settling.settled_positions[rebuilt], self.cell)
        return self.get_assembled_material(kept_atoms, columns, positions, self.get_site_grains(network)[rebuilt])

    def get_assembled_material(
        self, kept_atoms: np.ndarray, columns: np.ndarray, positions: np.ndarray, grains: np.ndarray
    ) -> Material:
        """The kept stacked atoms, then the atoms of each rebuilt site's column at its position."""
        material = self.material.clone()
        material.to_cartesian()
        coordinates = np.array(material.basis.coordinates.values)
        column_atoms = [np.flatnonzero(self.sites.atom_site_indices == column) for column in columns]
        rebuilt_atoms = np.concatenate(column_atoms)
        sites = np.repeat(np.arange(len(columns)), [len(atoms) for atoms in column_atoms])
        atoms = np.concatenate([kept_atoms, rebuilt_atoms])
        rebuilt_coordinates = np.column_stack([positions[sites], coordinates[rebuilt_atoms, 2]])
        material.basis = Basis(
            elements=ArrayWithIds.from_values(np.array(material.basis.elements.values)[atoms].tolist()),
            coordinates=Coordinates.from_values(np.vstack([coordinates[kept_atoms], rebuilt_coordinates]).tolist()),
            units=BasisUnitsEnum.cartesian,
            cell=material.basis.cell,
            labels=ArrayWithIds.from_values(
                np.concatenate([np.array(material.basis.labels.values)[kept_atoms], grains[sites]]).tolist()
            ),
        )
        material.to_crystal()
        return material
