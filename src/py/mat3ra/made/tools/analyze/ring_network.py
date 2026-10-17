"""
The ring network of two grains stacked along x: the dual of their hexagon centres near the two lines (Ophus et al.,
PRB 92, 205402 (2015)), co-circular ties split by one rule, read as rings and homo bonds per line.
"""
from functools import cached_property
from typing import List, Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from scipy.spatial import Delaunay

from . import BaseMaterialAnalyzer
from .rings import HEXAGON_SIZE, RingsAndBonds, RingsArrangement, RingsMaterialAnalyzer, get_line_offsets
from .utils import IN_PLANE_IMAGE_SHIFTS, get_in_plane_periodic_images, wrap_to_cell

# positions this close are one, measured over every candidate slide of the 313 sweep cases. Four centres meant to share
# a circle miss it by the error of the stacked positions (stored to 1e-9 of the cell vectors; removing it takes the
# largest miss from 1.9e-6 to 3.3e-7), grown with the circle: up to 1.9e-6 on circles under 10 angstrom and 7.6e-6 on
# the flat triangles along the outer images, 1.3x below 1e-5. A fourth centre off the circle lies 1.6e-4 or more from
# it, 1.5e-5 on those flat triangles, 1.5x above. A tie's right-most corners coincide or lie 0.16 apart; stacked sites
# lie within 3e-8 of a band edge or 2.3e-3 and more from it.
POSITION_TOLERANCE = 1e-5  # angstrom
# a site of a ring network is a triangle of ring centres, bonded across its three edges
BONDS_PER_SITE = 3
IMAGE_SHIFTS = np.array(IN_PLANE_IMAGE_SHIFTS)


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
    two at one x the upper, is r-s instead. For a 4|8 core this gives the octagon at x = 0 to the second grain.
    """
    x, y = quadrilaterals[..., 0], quadrilaterals[..., 1]
    is_right = x > x.max(axis=1, keepdims=True) - POSITION_TOLERANCE
    return np.argmax(np.where(is_right, y, -np.inf), axis=1) >= 2


def get_padded_images(positions: np.ndarray, cell: np.ndarray, margins: np.ndarray) -> Tuple[np.ndarray, ...]:
    """Positions in a rectangular cell and their images within `margins` (x, y) of it; each one's point and shift."""
    images = get_in_plane_periodic_images(positions, np.diag(cell))
    points = np.tile(np.arange(len(positions)), len(IMAGE_SHIFTS))
    tiles = np.repeat(np.arange(len(IMAGE_SHIFTS)), len(positions))
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


def get_site_neighbors(keys: np.ndarray, sites: np.ndarray, neighbors: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    For the triangles beside each site (sites sorted by key): the site with the same key, and whether there is one (a
    triangle past the centres taken has no copy among the sites).
    """
    # the place of each key among the sites' sorted keys, that site's if the key is there (modulo: a key past the last)
    indices = np.searchsorted(keys[sites], keys[neighbors]) % len(sites)
    return indices, keys[sites][indices] == keys[neighbors]


class GrainLattice(InMemoryEntityPydantic):
    """A grain's lattice vectors (rows), a site of each of its two sublattices, and the stacked sites they are."""

    model_config = {"arbitrary_types_allowed": True}

    vectors: np.ndarray
    sublattice_origins: np.ndarray
    column_sites: np.ndarray

    def get_sublattices(self, points: np.ndarray) -> np.ndarray:
        """Sublattice of each point: the one whose nearest lattice point is nearer."""
        fractional = (points[:, None] - self.sublattice_origins) @ np.linalg.inv(self.vectors)
        return np.argmin(np.linalg.norm((fractional - np.round(fractional)) @ self.vectors, axis=2), axis=1)


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


class RingNetworkAnalyzer(BaseMaterialAnalyzer):
    """
    Reads two honeycomb grains stacked along x without a gap (the first at x = 0, the second from x = its width), with
    the supercell matrix of each, as the ring network of their hexagon centres: a site per Delaunay triangle, bonded
    across its edges, rebuilt within `band_width` lattice constants of either line; the second grain's centres can be
    slid along y.
    """

    model_config = {"arbitrary_types_allowed": True}

    supercell_matrices: List[List[List[int]]]
    band_width: float

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
    def site_grains(self) -> np.ndarray:
        return np.array(self.material.basis.labels.values)[self.sites.site_first_atoms]

    def get_grain_lattice(self, grain: int) -> GrainLattice:
        """The grain's vectors (from its supercell matrix), its first site and that site's nearest neighbor."""
        sites = np.flatnonzero(self.site_grains == grain)
        offsets = self.sites.site_positions[sites] - self.sites.site_positions[sites[0]]
        offsets -= np.round(offsets / self.cell) * self.cell
        nearest = 1 + np.argmin(np.linalg.norm(offsets[1:], axis=1))
        return GrainLattice(
            vectors=np.linalg.inv(self.supercell_matrices[grain]) @ np.diag([self.grain_widths[grain], self.cell[1]]),
            sublattice_origins=self.sites.site_positions[sites[0]] + np.array([[0.0, 0.0], offsets[nearest]]),
            column_sites=sites[[0, nearest]],
        )

    @cached_property
    def grain_lattices(self) -> List[GrainLattice]:
        return [self.get_grain_lattice(grain) for grain in range(len(self.supercell_matrices))]

    @cached_property
    def bond_length(self) -> float:
        return float(np.linalg.norm(np.diff(self.grain_lattices[0].sublattice_origins, axis=0)))

    @cached_property
    def hexagon_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Hexagon centres of each grain inside its own supercell, and their grains. A hexagon centre is a site of the
        first sublattice minus its bond to the second. Ordered by grain and by position in the grain's lattice in whole
        thirds of its vectors, so that no rounding digit decides.
        """
        centers = []
        for grain, lattice in enumerate(self.grain_lattices):
            positions = self.sites.site_positions[self.site_grains == grain]
            bond = lattice.sublattice_origins[1] - lattice.sublattice_origins[0]
            points = positions[lattice.get_sublattices(positions) == 0] - bond
            start = self.line_positions[grain]
            points[:, 0] = start + wrap_to_cell(points[:, 0] - start, self.grain_widths[grain])
            points = wrap_to_cell(points, self.cell)
            thirds = np.round(3 * (points - lattice.sublattice_origins[0]) @ np.linalg.inv(lattice.vectors)).astype(int)
            centers.append(points[np.lexsort(thirds.T[::-1])])
        return np.vstack(centers), np.repeat([0, 1], [len(points) for points in centers])

    @cached_property
    def band_edge(self) -> float:
        """Distance from a line within which sites are rebuilt, short of the band width by the position tolerance."""
        return self.band_width * np.sqrt(3) * self.bond_length - POSITION_TOLERANCE

    @cached_property
    def reach(self) -> float:
        """
        How far beyond the band the centres are taken, so that a kept site bonded to a rebuilt one has its own three
        neighbors: three lattice constants, measured (two leave h-BN (0, 7)|(5, 3) too short along the boundary).
        """
        return 3 * np.sqrt(3) * self.bond_length

    def get_line_distances(self, x_values: np.ndarray) -> np.ndarray:
        """Distance from each x to the nearer line, periodic in the cell width."""
        return np.abs(get_line_offsets(x_values, self.line_positions, self.cell[0])).min(axis=1)

    def get_tied_pairs(self, delaunay: Delaunay, points: np.ndarray) -> Tuple[np.ndarray, ...]:
        """
        Neighboring triangles with their four corners on one circle centred in a band, each pair once: the triangle,
        the neighbor, and their quadrilateral (p, q, r, s) with p-q the shared edge, r and s the corners off it.
        """
        simplices = delaunay.simplices
        centers, radii = get_circumcircles(points[simplices])
        triangles, corners = np.nonzero(delaunay.neighbors > np.arange(len(simplices))[:, None])
        others = delaunay.neighbors[triangles, corners]
        # the neighbor's corner off the shared edge: its corners' sum less the two corners the triangle shares with it
        fourth = simplices[others].sum(axis=1) - (simplices[triangles].sum(axis=1) - simplices[triangles, corners])
        distances = np.abs(np.linalg.norm(points[fourth] - centers[triangles], axis=1) - radii[triangles])
        is_pair = (distances < POSITION_TOLERANCE) & (self.get_line_distances(centers[triangles, 0]) < self.band_edge)
        triangles, corners, others, fourth = triangles[is_pair], corners[is_pair], others[is_pair], fourth[is_pair]
        shared = simplices[triangles][np.arange(3) != corners[:, None]].reshape(-1, 2)
        return triangles, others, np.column_stack([shared, simplices[triangles, corners], fourth])

    def get_resolved_simplices(self, points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Delaunay triangles of the points with each co-circular pair centred in a band (the centres of the two grains
        meet only at a line) split along the diagonal get_diagonal_flips chooses; and whether each came from a pair.
        """
        delaunay = Delaunay(points)
        simplices = delaunay.simplices.copy()
        triangles, others, quadrilaterals = self.get_tied_pairs(delaunay, points)
        flips = get_diagonal_flips(points[quadrilaterals])
        # a flip turns triangles p-q-r and p-q-s into r-s-p and r-s-q
        simplices[triangles[flips]] = quadrilaterals[flips][:, [2, 3, 0]]
        simplices[others[flips]] = quadrilaterals[flips][:, [2, 3, 1]]
        is_tied = np.zeros(len(simplices), bool)
        is_tied[np.concatenate([triangles, others])] = True
        return simplices, is_tied

    def get_nearby_centers(self, slide: float) -> Tuple[np.ndarray, np.ndarray]:
        """Hexagon centres within the band and `reach` of a line, the second grain's slid by `slide`; their grains."""
        centers, grains = self.hexagon_centers
        centers = wrap_to_cell(centers + np.outer(grains, [0.0, slide]), self.cell)
        nearby = self.get_line_distances(centers[:, 0]) < self.band_edge + self.reach
        return centers[nearby], grains[nearby]

    def get_network(self, slide: float) -> RingNetwork:
        """
        The ring network of the centres near the lines, triangulated with their images as near the cell across the
        lines and within `reach` along them; its sites are the triangles of the central copies, by periodic key.
        """
        centers, grains = self.get_nearby_centers(slide)
        images, points, tiles = get_padded_images(centers, self.cell, np.array([self.band_edge, 0.0]) + self.reach)
        simplices, is_tied = self.get_resolved_simplices(images)
        keys, is_central = get_periodic_keys(points[simplices], tiles[simplices])
        sites = np.flatnonzero(is_central)[np.argsort(keys[is_central])]
        triangles_beside = get_triangle_neighbors(simplices)[sites]
        neighbor_sites, is_linked = get_site_neighbors(keys, sites, triangles_beside)
        positions = images[simplices].mean(axis=1)
        is_rebuilt = self.get_line_distances(positions[sites, 0]) < self.band_edge
        if not np.all(is_linked[is_rebuilt]):
            raise ValueError(f"The cell is too short along the boundary ({self.cell[1]:.3f} angstrom) for its network")
        # a site without a neighbor across an edge is bonded to itself by a zero vector: no rebuilt site has one
        # (checked above), nor a kept site bonded to one (`reach`), and settling drops terms between kept sites
        return RingNetwork(
            centers=centers,
            center_grains=grains,
            positions=positions[sites],
            corners=points[simplices[sites]],
            neighbors=np.where(is_linked, neighbor_sites, np.arange(len(sites))[:, None]),
            vectors=np.where(is_linked[..., None], positions[triangles_beside] - positions[sites][:, None], 0.0),
            is_rebuilt=is_rebuilt,
            number_of_ties=int(is_tied[sites][is_rebuilt].sum()) // 2,
        )

    def get_site_grains(self, network: RingNetwork) -> np.ndarray:
        """Grain of each site: that of at least two of its three centres."""
        return (network.center_grains[network.corners].sum(axis=1) >= 2).astype(int)

    def get_site_columns(self, network: RingNetwork, slide: float) -> np.ndarray:
        """
        The stacked site whose atoms each network site takes: that of its sublattice in its grain, read at the site's
        image inside the grain (the stacked width is a lattice vector of neither grain), the second grain's slide
        undone.
        """
        grains = self.get_site_grains(network)
        middles = np.array(self.line_positions) + self.grain_widths / 2
        images_across = np.round((network.positions[:, 0] - middles[grains]) / self.cell[0])
        points = network.positions - np.outer(images_across, [self.cell[0], 0.0]) - np.outer(grains, [0.0, slide])
        sublattices = np.choose(grains, [lattice.get_sublattices(points) for lattice in self.grain_lattices])
        return np.array([lattice.column_sites for lattice in self.grain_lattices])[grains, sublattices]

    def get_line_arrangements(self, network: RingNetwork, slide: float) -> List[RingsArrangement]:
        """Rings (a centre's ring size is its number of triangles) and homo bonds of the rebuilt bands, by line."""
        species = self.sites.site_species[self.get_site_columns(network, slide)]
        sizes = np.bincount(network.corners.ravel(), minlength=len(network.centers))
        sizes[self.get_line_distances(network.centers[:, 0]) >= self.band_edge] = HEXAGON_SIZE
        first = np.repeat(np.arange(len(network.positions)), BONDS_PER_SITE)
        second = network.neighbors.ravel()
        in_band = network.is_rebuilt[first] & network.is_rebuilt[second]
        bond_middle_x = network.positions[first, 0] + network.vectors[..., 0].ravel() / 2
        return RingsAndBonds(
            ring_centers=network.centers,
            ring_sizes=sizes,
            ring_pairs=np.column_stack([network.corners.ravel(), np.roll(network.corners, 1, axis=1).ravel()]),
            bond_middle_x=bond_middle_x[in_band],
            bond_species=species[np.column_stack([first, second])][in_band],
            cell=self.cell,
        ).get_line_arrangements(self.line_positions)
