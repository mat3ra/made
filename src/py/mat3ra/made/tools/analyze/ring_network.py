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

# positions this close are one, measured over every candidate slide of 313 boundaries of graphene, h-BN and MoS2. Four
# centres meant to share a circle miss it by the error of the stacked positions (stored to 1e-9 of the cell vectors;
# removing it takes the largest miss from 1.9e-6 to 3.3e-7), grown with the circle: up to 1.9e-6 on circles under 10
# angstrom and 7.6e-6 on the flat triangles along the outer images, 1.3x below 1e-5. A fourth centre off the circle lies
# 1.6e-4 or more from it, 1.5e-5 on those flat triangles, 1.5x above. A tie's right-most corners coincide or lie 0.16
# apart; stacked sites lie within 3e-8 of a band edge or 2.3e-3 and more from it.
POSITION_TOLERANCE = 1e-5  # angstrom
# a site of a ring network is a triangle of ring centres, bonded across its three edges
BONDS_PER_SITE = 3
# a honeycomb's two sites and its hexagon centres lie on a lattice a third of the honeycomb's lattice vectors apart
POSITIONS_PER_LATTICE_VECTOR = 3
# how far beyond its band the centres are taken, so that a kept site bonded to a rebuilt one has its own three
# neighbors; measured: two lattice constants leave h-BN (0, 7)|(5, 3) too short along the boundary
REACH = 3.0  # lattice constants


def get_circumcircles(triangles: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Centre and radius of the circle through the corners of each triangle."""
    second, third = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    second_squared, third_squared = (second**2).sum(axis=1), (third**2).sum(axis=1)
    denominator = 2 * (second[:, 0] * third[:, 1] - second[:, 1] * third[:, 0])
    x = (third[:, 1] * second_squared - second[:, 1] * third_squared) / denominator
    y = (second[:, 0] * third_squared - third[:, 0] * second_squared) / denominator
    return triangles[:, 0] + np.stack([x, y], axis=1), np.hypot(x, y)


def get_diagonal_flips(edge_corners: np.ndarray, opposite_corners: np.ndarray) -> np.ndarray:
    """
    Whether each pair of triangles on four co-circular corners is split along its other diagonal, the one between the
    two corners off the shared edge: when that diagonal holds the right-most corner (of two at one x, the upper). For a
    4|8 core this gives the octagon at x = 0 to the second grain.
    """
    corners = np.concatenate([edge_corners, opposite_corners], axis=1)
    x, y = corners[..., 0], corners[..., 1]
    is_right = x > x.max(axis=1, keepdims=True) - POSITION_TOLERANCE
    return np.argmax(np.where(is_right, y, -np.inf), axis=1) >= edge_corners.shape[1]


def get_padded_images(
    positions: np.ndarray, cell: np.ndarray, padding: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Positions in a rectangular cell and their images within `padding` (x, y) of it: where, which one, which cell."""
    images = get_in_plane_periodic_images(positions, np.diag(cell))
    indices = np.tile(np.arange(len(positions)), len(IN_PLANE_IMAGE_SHIFTS))
    shifts = np.repeat(np.array(IN_PLANE_IMAGE_SHIFTS), len(positions), axis=0)
    is_near = np.all((images > -padding) & (images < cell + padding), axis=1)
    return images[is_near], indices[is_near], shifts[is_near]


def get_row_groups(rows: np.ndarray) -> np.ndarray:
    """A number for each row of an integer table: equal rows share it, ranked by value column by column."""
    order = np.lexsort(rows.T[::-1])
    is_new_value = np.any(rows[order][1:] != rows[order][:-1], axis=1)
    groups = np.empty(len(rows), int)
    groups[order] = np.concatenate([[0], np.cumsum(is_new_value)])
    return groups


def get_triangle_copies(corner_indices: np.ndarray, corner_shifts: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    For triangles given by the position and cell of each corner: an index that all periodic copies of a triangle share,
    and whether the triangle is the copy whose lowest-numbered position lies in the cell itself.
    """
    lowest = np.argmin(corner_indices, axis=1)
    lowest_shifts = corner_shifts[np.arange(len(corner_indices)), lowest]
    # each corner as (its cell relative to that of the lowest-numbered position, its position), the same in every copy
    corners = np.concatenate([corner_shifts - lowest_shifts[:, None], corner_indices[..., None]], axis=2)
    order = np.lexsort((corners[..., 2], corners[..., 1], corners[..., 0]), axis=-1)
    copies = np.take_along_axis(corners, order[..., None], axis=1).reshape(len(corners), -1)
    return get_row_groups(copies), np.all(lowest_shifts == 0, axis=1)


def get_triangle_neighbors(triangles: np.ndarray) -> np.ndarray:
    """The triangle across the edge opposite each corner of each triangle; -1 at the outer border."""
    corners_per_triangle = triangles.shape[1]
    edges = np.stack([triangles[:, [1, 2]], triangles[:, [2, 0]], triangles[:, [0, 1]]], axis=1)
    edge_indices = get_row_groups(np.sort(edges, axis=2).reshape(-1, 2))
    order = np.argsort(edge_indices, kind="stable")
    shared = np.flatnonzero(edge_indices[order][1:] == edge_indices[order][:-1])
    # the edges are listed triangle by triangle, so the edge numbered e belongs to triangle e // corners_per_triangle
    neighbors = -np.ones(len(edge_indices), int)
    neighbors[order[shared]] = order[shared + 1] // corners_per_triangle
    neighbors[order[shared + 1]] = order[shared] // corners_per_triangle
    return neighbors.reshape(-1, corners_per_triangle)


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
    The ring network of hexagon centres (and their grains) in a rectangular periodic cell: a site per Delaunay triangle
    of the centres and of their images within `padding` of the cell, bonded to the sites across its three edges; the
    sites within `band_edge` of a line are the rebuilt ones.
    """

    model_config = {"arbitrary_types_allowed": True}

    centers: np.ndarray
    center_grains: np.ndarray
    cell: np.ndarray
    line_positions: List[float]
    band_edge: float
    padding: np.ndarray

    def get_line_distances(self, x_values: np.ndarray) -> np.ndarray:
        """Distance from each x to the nearer line, periodic in the cell width."""
        return np.abs(get_line_offsets(x_values, self.line_positions, self.cell[0])).min(axis=1)

    @cached_property
    def padded_images(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """The centres and their images within `padding` of the cell: where, which centre, which cell."""
        return get_padded_images(self.centers, self.cell, self.padding)

    @cached_property
    def delaunay(self) -> Delaunay:
        """The Delaunay triangulation of the centres and their images."""
        return Delaunay(self.padded_images[0])

    @cached_property
    def tied_pairs(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Neighboring Delaunay triangles with their four corners on one circle centred in a band (the centres of the two
        grains meet only at a line), each pair once: the triangle, its neighbor, the shared edge, the corners off it.
        """
        simplices, neighbors, points = self.delaunay.simplices, self.delaunay.neighbors, self.padded_images[0]
        triangles, corners = np.nonzero(neighbors > np.arange(len(simplices))[:, None])
        others = neighbors[triangles, corners]
        # the neighbor's corner off the shared edge is the one across which it borders the triangle
        other_corners = np.argmax(neighbors[others] == triangles[:, None], axis=1)
        opposite = np.column_stack([simplices[triangles, corners], simplices[others, other_corners]])
        centers, radii = get_circumcircles(points[simplices[triangles]])
        distances = np.abs(np.linalg.norm(points[opposite[:, 1]] - centers, axis=1) - radii)
        is_pair = (distances < POSITION_TOLERANCE) & (self.get_line_distances(centers[:, 0]) < self.band_edge)
        edges = simplices[triangles][np.arange(simplices.shape[1]) != corners[:, None]].reshape(-1, 2)
        return triangles[is_pair], others[is_pair], edges[is_pair], opposite[is_pair]

    @cached_property
    def triangles(self) -> np.ndarray:
        """The Delaunay triangles, each tied pair split along the diagonal get_diagonal_flips chooses."""
        triangles = self.delaunay.simplices.copy()
        pairs, others, edges, opposite = self.tied_pairs
        flips = get_diagonal_flips(self.padded_images[0][edges], self.padded_images[0][opposite])
        triangles[pairs[flips]] = np.column_stack([opposite[flips], edges[flips, 0]])
        triangles[others[flips]] = np.column_stack([opposite[flips], edges[flips, 1]])
        return triangles

    @cached_property
    def triangle_copies(self) -> Tuple[np.ndarray, np.ndarray]:
        """Which periodic triangle each triangle is a copy of, and whether it is that triangle's copy in the cell."""
        _, indices, shifts = self.padded_images
        return get_triangle_copies(indices[self.triangles], shifts[self.triangles])

    @cached_property
    def sites(self) -> np.ndarray:
        """The triangles in the cell, one per site, in the order of their copies."""
        copies, is_in_cell = self.triangle_copies
        return np.flatnonzero(is_in_cell)[np.argsort(copies[is_in_cell])]

    @cached_property
    def triangle_positions(self) -> np.ndarray:
        """Where the site of each triangle, or an image of it, sits: at the triangle's centroid."""
        return self.padded_images[0][self.triangles].mean(axis=1)

    @cached_property
    def positions(self) -> np.ndarray:
        """Where each site sits."""
        return self.triangle_positions[self.sites]

    @cached_property
    def corners(self) -> np.ndarray:
        """The hexagon centres at the corners of each site's triangle."""
        return self.padded_images[1][self.triangles[self.sites]]

    @cached_property
    def is_rebuilt(self) -> np.ndarray:
        """Whether each site lies in the band along a line."""
        return self.get_line_distances(self.positions[:, 0]) < self.band_edge

    @cached_property
    def has_ties(self) -> bool:
        """Whether any rebuilt site comes from four centres on one circle."""
        pairs, others, _, _ = self.tied_pairs
        return bool(np.any(self.is_rebuilt[np.isin(self.sites, np.concatenate([pairs, others]))]))

    @cached_property
    def neighbor_triangles(self) -> np.ndarray:
        """The triangle across each edge of each site; -1 at the outer border of the centres taken."""
        return get_triangle_neighbors(self.triangles)[self.sites]

    @cached_property
    def triangle_sites(self) -> np.ndarray:
        """The site each triangle is a copy of; -1 if that triangle's copy in the cell is not among the sites."""
        copies, _ = self.triangle_copies
        sites_by_copy = np.full(copies.max() + 1, -1)
        sites_by_copy[copies[self.sites]] = np.arange(len(self.sites))
        return sites_by_copy[copies]

    @cached_property
    def is_linked(self) -> np.ndarray:
        """Whether each site has a site across each of its edges."""
        return (self.neighbor_triangles >= 0) & (self.triangle_sites[self.neighbor_triangles] >= 0)

    @cached_property
    def neighbors(self) -> np.ndarray:
        """
        The site across each edge of each site; the site itself where there is none. No rebuilt site has such a bond
        (RingNetworkAnalyzer.get_network checks), nor a kept site bonded to one (REACH), and settling drops it.
        """
        own = np.arange(len(self.sites))[:, None]
        return np.where(self.is_linked, self.triangle_sites[self.neighbor_triangles], own)

    @cached_property
    def vectors(self) -> np.ndarray:
        """The vector from each site to its neighbor across each edge; zero where it has none."""
        to_neighbors = self.triangle_positions[self.neighbor_triangles] - self.positions[:, None]
        return np.where(self.is_linked[..., None], to_neighbors, 0.0)


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
        """The lengths of the rectangular cell along x and y."""
        return np.diag(self.sites.lattice_vectors).copy()

    @cached_property
    def grain_widths(self) -> np.ndarray:
        """The width of each grain across the lines, in proportion to its supercell's area."""
        areas = np.abs([np.linalg.det(matrix) for matrix in self.supercell_matrices])
        return self.cell[0] * areas / areas.sum()

    @cached_property
    def line_positions(self) -> List[float]:
        """The x of the two lines: the start of each grain."""
        return [0.0, float(self.grain_widths[0])]

    def get_second_grain_turned(self, supercell_matrices: List[List[List[int]]]) -> "RingNetworkAnalyzer":
        """
        The same stack with the second grain turned by 180 degrees about its cell's centre, as stacking it with its
        supercell matrix negated gives (the given matrices).
        """
        material = self.material.clone()
        material.to_cartesian()
        coordinates = np.array(material.basis.coordinates.values)
        second = np.array(material.basis.labels.values) == 1
        coordinates[second, 0] = self.line_positions[1] + wrap_to_cell(
            self.cell[0] - coordinates[second, 0], self.grain_widths[1]
        )
        coordinates[second, 1] = wrap_to_cell(-coordinates[second, 1], self.cell[1])
        material.set_coordinates(coordinates.tolist())
        material.to_crystal()
        return RingNetworkAnalyzer(material=material, supercell_matrices=supercell_matrices, band_width=self.band_width)

    @cached_property
    def site_grains(self) -> np.ndarray:
        """The grain of each stacked site."""
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
        """The lattice of each grain."""
        return [self.get_grain_lattice(grain) for grain in range(len(self.supercell_matrices))]

    @cached_property
    def bond_length(self) -> float:
        """The bond length of the monolayer, from the first grain."""
        return float(np.linalg.norm(np.diff(self.grain_lattices[0].sublattice_origins, axis=0)))

    @cached_property
    def lattice_constant(self) -> float:
        """A honeycomb's lattice constant: its bond length times sqrt(3)."""
        return float(np.sqrt(3) * self.bond_length)

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
            fractional = (points - lattice.sublattice_origins[0]) @ np.linalg.inv(lattice.vectors)
            thirds = np.round(POSITIONS_PER_LATTICE_VECTOR * fractional).astype(int)
            centers.append(points[np.lexsort(thirds.T[::-1])])
        return np.vstack(centers), np.repeat([0, 1], [len(points) for points in centers])

    @cached_property
    def band_edge(self) -> float:
        """Distance from a line within which sites are rebuilt, short of the band width by the position tolerance."""
        return self.band_width * self.lattice_constant - POSITION_TOLERANCE

    @cached_property
    def padding(self) -> np.ndarray:
        """How far beyond the cell the centres' images are taken: across the lines past the band, along them."""
        return np.array([self.band_edge, 0.0]) + REACH * self.lattice_constant

    def get_line_distances(self, x_values: np.ndarray) -> np.ndarray:
        """Distance from each x to the nearer line, periodic in the cell width."""
        return np.abs(get_line_offsets(x_values, self.line_positions, self.cell[0])).min(axis=1)

    def get_nearby_centers(self, slide: float) -> Tuple[np.ndarray, np.ndarray]:
        """Hexagon centres within the band and REACH of a line, the second grain's slid by `slide`; their grains."""
        centers, grains = self.hexagon_centers
        centers = wrap_to_cell(centers + np.outer(grains, [0.0, slide]), self.cell)
        nearby = self.get_line_distances(centers[:, 0]) < self.padding[0]
        return centers[nearby], grains[nearby]

    def get_network(self, slide: float) -> RingNetwork:
        """The ring network of the hexagon centres near the lines, the second grain's slid along them by `slide`."""
        centers, grains = self.get_nearby_centers(slide)
        network = RingNetwork(
            centers=centers,
            center_grains=grains,
            cell=self.cell,
            line_positions=self.line_positions,
            band_edge=self.band_edge,
            padding=self.padding,
        )
        if not np.all(network.is_linked[network.is_rebuilt]):
            raise ValueError(f"The cell is too short along the boundary ({self.cell[1]:.3f} angstrom) for its network")
        return network

    def get_site_grains(self, network: RingNetwork) -> np.ndarray:
        """Grain of each site: that of most of its three corners."""
        return np.round(network.center_grains[network.corners].mean(axis=1)).astype(int)

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
