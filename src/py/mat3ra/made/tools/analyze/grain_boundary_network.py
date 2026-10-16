from functools import cached_property
from typing import Dict, List, Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.materials_category.defective_structures.one_dimensional.grain_boundary_linear.configuration import (  # noqa: E501
    GrainBoundaryCoreEnum,
)
from scipy.spatial import Delaunay, cKDTree

from .rings import HEXAGON_SIZE, IMAGE_SHIFTS, Bonds, RingsMaterialAnalyzer, RingsNetworkAnalyzer, get_periodic_images

# a Voronoi vertex is the circumcentre of one Delaunay triangle, so every site of the network has three bonds
BONDS_PER_SITE = 3
# a displacement that is a fixed periodic function of position, far above the platform noise of the coordinates, so
# the triangulation, and the co-circular groups found in it, are the same on every platform and for any atom order
TIE_BREAKING_DISPLACEMENT = 1e-5  # angstrom
TIE_BREAKING_WAVES = np.array([[3, 5], [7, 2]])
COCIRCULAR_TOLERANCE = 1e-3  # angstrom
# sites on the edge of the rebuilt band (lattice sites can sit exactly there) stay, whatever the rounding
BAND_EDGE_TOLERANCE = 1e-3  # angstrom
REBUILT_BAND_WIDTH = 2.0  # lattice constants
CORE_RING_SIZES: Dict[GrainBoundaryCoreEnum, List[int]] = {
    GrainBoundaryCoreEnum.field_5_7: [5, 7],
    GrainBoundaryCoreEnum.field_4_8: [4, 8],
    GrainBoundaryCoreEnum.field_6: [],
}


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


def get_triangle_neighbors(simplices: np.ndarray) -> np.ndarray:
    """Neighbor of each triangle across the edge opposite each of its corners, -1 at the outer border."""
    edges = np.stack([simplices[:, [1, 2]], simplices[:, [2, 0]], simplices[:, [0, 1]]], axis=1).reshape(-1, 2)
    keys = np.sort(edges, axis=1) @ np.array([simplices.max() + 1, 1])
    order = np.argsort(keys, kind="stable")
    shared = np.flatnonzero(keys[order][1:] == keys[order][:-1])
    neighbors = -np.ones(len(keys), int)
    neighbors[order[shared]], neighbors[order[shared + 1]] = order[shared + 1] // 3, order[shared] // 3
    return neighbors.reshape(-1, 3)


def get_triangulations(first: int, last: int) -> List[List[Tuple[int, int, int]]]:
    """Every triangulation of the convex polygon with corners first..last, in order around it."""
    if last - first < 2:
        return [[]]
    return [
        left + right + [(first, middle, last)]
        for middle in range(first + 1, last)
        for left in get_triangulations(first, middle)
        for right in get_triangulations(middle, last)
    ]


class CocircularGroups(InMemoryEntityPydantic):
    """
    Delaunay triangles of ring centres tiled 3 x 3. Where four or more centres lie on one empty circle the
    triangulation is not unique: each such group is triangulated so that its centres get rings of the allowed sizes,
    one group after another along the lines, every copy of a group in another cell alike; among equally good
    triangulations the Delaunay one stays.
    """

    model_config = {"arbitrary_types_allowed": True}

    images: np.ndarray
    simplices: np.ndarray
    cell: np.ndarray
    allowed_ring_sizes: List[int]

    @cached_property
    def number_of_centers(self) -> int:
        return len(self.images) // len(IMAGE_SHIFTS)

    @cached_property
    def tree(self) -> cKDTree:
        return cKDTree(self.images)

    @cached_property
    def circles(self) -> Tuple[np.ndarray, np.ndarray]:
        centers = get_circumcenters(self.images[self.simplices])
        return centers, np.linalg.norm(self.images[self.simplices[:, 0]] - centers, axis=1)

    @cached_property
    def candidates(self) -> np.ndarray:
        """
        Triangles whose empty circumcircle holds four or more centres; circles wider than half the cell (slivers at
        the border of the tiling) are left out, so a group never holds two copies of one centre.
        """
        centers, radii = self.circles
        outer = self.tree.query_ball_point(centers, radii + COCIRCULAR_TOLERANCE, return_length=True)
        inner = self.tree.query_ball_point(centers, radii - COCIRCULAR_TOLERANCE, return_length=True)
        return np.flatnonzero((outer - inner > 3) & (radii < self.cell.min() / 2))

    def get_circle_points(self, simplex: int) -> Tuple[int, ...]:
        """Centres on the circumcircle of a triangle, ordered around it."""
        center, radius = self.circles[0][simplex], self.circles[1][simplex]
        points = np.array(self.tree.query_ball_point(center, radius + COCIRCULAR_TOLERANCE))
        points = points[np.linalg.norm(self.images[points] - center, axis=1) > radius - COCIRCULAR_TOLERANCE]
        return tuple(points[np.argsort(np.arctan2(*(self.images[points] - center).T[::-1]))])

    @cached_property
    def groups(self) -> Dict[Tuple[int, ...], Tuple[np.ndarray, List[int]]]:
        """
        Centres of each group, ordered around the circle, with the centre of the circle and the Delaunay triangles of
        the group; only groups whose Delaunay triangles fill the polygon (none shared with an overlapping group).
        """
        groups: Dict[Tuple[int, ...], Tuple[np.ndarray, List[int]]] = {}
        for simplex in self.candidates:
            groups.setdefault(self.get_circle_points(simplex), (self.circles[0][simplex], []))[1].append(simplex)
        return {points: group for points, group in groups.items() if len(group[1]) == len(points) - 2}

    @cached_property
    def in_group(self) -> np.ndarray:
        in_group = np.zeros(len(self.simplices), bool)
        in_group[[simplex for _, members in self.groups.values() for simplex in members]] = True
        return in_group

    @cached_property
    def group_points(self) -> List[np.ndarray]:
        return [np.array(points) for points in self.groups]

    @cached_property
    def group_classes(self) -> List[int]:
        """For each group, the first group that is a copy of it, by the position of its circle in the cell."""
        wrapped = wrap_to_cell(np.array([center for center, _ in self.groups.values()]).reshape(-1, 2), self.cell)
        copies = cKDTree(wrapped, boxsize=self.cell).query_ball_point(wrapped, COCIRCULAR_TOLERANCE)
        return [min(found) for found in copies]

    @cached_property
    def options(self) -> Dict[int, List[List[Tuple[int, int, int]]]]:
        return {group: get_triangulations(0, len(self.group_points[group]) - 1) for group in set(self.group_classes)}

    def get_ring_sizes(self, group: int, option: int) -> np.ndarray:
        """Triangles at each ring centre (its ring size) that one triangulation of a group contributes."""
        corners = self.group_points[group][np.array(self.options[group][option])] % self.number_of_centers
        return np.bincount(corners.ravel(), minlength=self.number_of_centers)

    def get_delaunay_option(self, group: int) -> int:
        position = {point: index for index, point in enumerate(self.group_points[group])}
        members = self.simplices[list(self.groups.values())[group][1]]
        triangles = {tuple(sorted(position[point] for point in simplex)) for simplex in members}
        options = [{tuple(sorted(triangle)) for triangle in option} for option in self.options[group]]
        return options.index(triangles)

    def get_choices(self, group_order_keys: List[Tuple[int, float]]) -> Dict[int, int]:
        """Option of each group class: the fewest centres with rings outside the allowed sizes, given the others."""
        _, central = get_triangle_keys(self.simplices, self.number_of_centers)
        outside = self.simplices[central & ~self.in_group] % self.number_of_centers
        choices = {group: self.get_delaunay_option(group) for group in self.options}
        ring_sizes = np.bincount(outside.ravel(), minlength=self.number_of_centers)
        ring_sizes += sum(self.get_ring_sizes(group, option) for group, option in choices.items())
        for group in sorted(self.options, key=group_order_keys.__getitem__):
            ring_sizes -= self.get_ring_sizes(group, choices[group])
            centers = self.group_points[group] % self.number_of_centers
            scores = []
            for option in range(len(self.options[group])):
                sizes = (ring_sizes + self.get_ring_sizes(group, option))[centers]
                scores.append(((~np.isin(sizes, self.allowed_ring_sizes)).sum(), option != choices[group], option))
            choices[group] = min(scores)[2]
            ring_sizes += self.get_ring_sizes(group, choices[group])
        return choices

    def get_resolved_simplices(self, group_order_keys: List[Tuple[int, float]]) -> Tuple[np.ndarray, np.ndarray]:
        """Triangles counterclockwise, the groups triangulated as chosen; and which triangles came from a group."""
        choices = self.get_choices(group_order_keys)
        added = [
            points[np.array(self.options[group][choices[group]])]
            for points, group in zip(self.group_points, self.group_classes)
        ]
        simplices = np.vstack([self.simplices[~self.in_group], *added])
        corners = self.images[simplices]
        clockwise = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]) < 0
        simplices[clockwise] = simplices[clockwise][:, [0, 2, 1]]
        return simplices, np.arange(len(simplices)) >= (~self.in_group).sum()


class RingNetwork(InMemoryEntityPydantic):
    """
    Sites (Voronoi vertices): positions, bonds grouped by site (BONDS_PER_SITE each) with the ring on the left of each
    bond, the grain holding most of each site's ring centres and its sublattice there; and the ring centres.
    """

    model_config = {"arbitrary_types_allowed": True}

    positions: np.ndarray
    bonds: Bonds
    bond_rings: np.ndarray
    grains: np.ndarray
    sublattices: np.ndarray
    ring_centers: np.ndarray


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
    Ring network of a honeycomb grain boundary (graphene, h-BN, MoS2): grains labelled 0 and 1 stacked along x without
    a gap, the lines at x = 0 and x = the width of grain 0. The hexagon centres of both grains are the ring centres and
    the sites are the vertices of their periodic Voronoi network, for any slide of the second grain along the lines.
    Sites within `band_width` lattice constants of either line are rebuilt; every other site keeps its stacked position.
    """

    supercell_matrices: List[List[List[int]]]
    band_width: float = REBUILT_BAND_WIDTH

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
        return np.where(distances >= self.band_width * np.sqrt(3) * self.site_distance - BAND_EDGE_TOLERANCE)[0]

    @cached_property
    def grain_hexagon_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        """Hexagon centres of each grain inside its own supercell, one per site of sublattice 0, and their grains."""
        centers = []
        for grain, lattice in enumerate(self.grain_lattices):
            sites = self.site_positions[self.site_grains == grain]
            points = sites[lattice.get_sublattices(sites) == 0] - lattice.sublattice_offset
            start = self.line_positions[grain]
            points[:, 0] = start + wrap_to_cell(points[:, 0] - start, self.grain_widths[grain])
            centers.append(wrap_to_cell(points, self.cell))
        return np.vstack(centers), np.repeat([0, 1], [len(points) for points in centers])

    def get_ring_centers(self, slide: float) -> np.ndarray:
        """Hexagon centres with the second grain slid by `slide` along y, moved by the tie-breaking displacement."""
        centers, grains = self.grain_hexagon_centers
        centers = wrap_to_cell(centers + np.outer(grains, [0.0, slide]), self.cell)
        return centers + TIE_BREAKING_DISPLACEMENT * np.sin(2 * np.pi * (centers / self.cell) @ TIE_BREAKING_WAVES.T)

    def get_triangulation(self, centers: np.ndarray, core: GrainBoundaryCoreEnum) -> Tuple[np.ndarray, ...]:
        """Tiled ring centres and their triangles, co-circular groups triangulated for the rings of `core`."""
        images = get_periodic_images(centers, self.lattice_vectors)
        groups = CocircularGroups(
            images=images,
            simplices=Delaunay(images).simplices,
            cell=self.cell,
            allowed_ring_sizes=[HEXAGON_SIZE] + CORE_RING_SIZES[core],
        )
        wrapped = wrap_to_cell(np.array([center for center, _ in groups.groups.values()]).reshape(-1, 2), self.cell)
        lines = self.get_nearest_lines(wrapped[:, 0], self.line_positions)
        return (images, *groups.get_resolved_simplices(list(zip(lines.tolist(), wrapped[:, 1].tolist()))))

    def get_network(self, slide: float, core: GrainBoundaryCoreEnum) -> RingNetwork:
        """Voronoi network of the ring centres, the second grain slid by `slide` along y, for the rings of `core`."""
        centers = self.get_ring_centers(slide)
        images, simplices, from_group = self.get_triangulation(centers, core)
        keys, central = get_triangle_keys(simplices, len(centers))
        vertices = np.where(central)[0][np.argsort(keys[central])]
        neighbors = get_triangle_neighbors(simplices)[vertices].ravel()
        # the triangles of a group share one circumcentre; their centroids keep the sites apart
        anchors = np.where(from_group[:, None], images[simplices].mean(axis=1), get_circumcenters(images[simplices]))
        first = np.repeat(np.arange(len(vertices)), BONDS_PER_SITE)
        second = np.searchsorted(keys[vertices], keys[neighbors])
        if not np.array_equal(keys[vertices][second % len(vertices)], keys[neighbors]):
            raise ValueError(
                f"The cell is too short along the boundary ({self.cell[1]:.3f} angstrom) for its periodic ring "
                "network; use a multiple of the boundary vectors"
            )
        grains = (self.grain_hexagon_centers[1][simplices[vertices] % len(centers)].sum(axis=1) >= 2).astype(int)
        return RingNetwork(
            positions=anchors[vertices],
            bonds=(first, second, anchors[neighbors] - anchors[vertices][first]),
            bond_rings=simplices[vertices][:, [2, 0, 1]].ravel() % len(centers),
            grains=grains,
            sublattices=self.get_sublattices(anchors[vertices], grains, slide),
            ring_centers=centers,
        )

    def get_sublattices(self, positions: np.ndarray, grains: np.ndarray, slide: float) -> np.ndarray:
        """Sublattice of each site in the lattice of its grain, the second grain slid by `slide`."""
        unslid_positions = positions - np.outer(grains, [0.0, slide])
        return np.choose(grains, [lattice.get_sublattices(unslid_positions) for lattice in self.grain_lattices])

    def get_kept_vertices(self, positions: np.ndarray) -> np.ndarray:
        kept_positions = wrap_to_cell(self.site_positions[self.kept_sites], self.cell)
        return cKDTree(wrap_to_cell(positions, self.cell), boxsize=self.cell).query(kept_positions)[1]

    def get_column_sites(self, grains: np.ndarray, sublattices: np.ndarray) -> np.ndarray:
        """The stacked site whose atoms each vertex takes: that of its grain and sublattice."""
        return np.array([lattice.sublattice_sites for lattice in self.grain_lattices])[grains, sublattices]

    def get_rings_analyzer(self, slide: float, core: GrainBoundaryCoreEnum) -> RingsNetworkAnalyzer:
        network = self.get_network(slide, core)
        return RingsNetworkAnalyzer(
            material=self.material,
            network_positions=network.positions,
            network_species=self.site_species[self.get_column_sites(network.grains, network.sublattices)],
            network_bonds=network.bonds,
            network_bond_rings=network.bond_rings,
            network_ring_centers=network.ring_centers,
        )
