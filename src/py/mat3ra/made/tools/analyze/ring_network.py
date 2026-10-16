from functools import cached_property, partial
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from scipy.spatial import Delaunay, cKDTree

from .rings import HEXAGON_SIZE, IMAGE_SHIFTS, Bonds, RingsMaterialAnalyzer, RingsNetworkAnalyzer, get_periodic_images

# a Voronoi vertex is the circumcentre of one Delaunay triangle, so every site of the network has three bonds
BONDS_PER_SITE = 3
# centres this close to one circle lie on it: far above the tie-breaking displacement, far below the distance between
# distinct circles of a lattice
COCIRCULAR_TOLERANCE = 1e-3  # angstrom
# positions closer than this are equal when two triangulations of a group are equally good: above the ~1e-7 angstrom
# by which centres from coordinates stored to 9 decimals differ, below TIE_BREAKING_DISPLACEMENT, which it must not
# merge
TIE_KEY_TOLERANCE = 1e-6  # angstrom


def wrap_to_cell(values: np.ndarray, periods) -> np.ndarray:
    """Values modulo their periods, values within rounding of a period mapped to 0 (one owner per cell edge)."""
    wrapped = values % periods
    return np.where(np.isclose(wrapped, periods), 0.0, wrapped)


def wrap_to_lattice(points: np.ndarray, lattice_vectors: np.ndarray) -> np.ndarray:
    """Points moved into the cell of the lattice vectors (rows), points on an edge of it to the edge at the origin."""
    return wrap_to_cell(points @ np.linalg.inv(lattice_vectors), 1.0) @ lattice_vectors


def get_tolerant_ranks(values: np.ndarray, tolerance: float) -> np.ndarray:
    """Rank of each value, values within `tolerance` of their sorted neighbor sharing one rank."""
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), int)
    ranks[order] = np.cumsum(np.diff(values[order], prepend=values[order][0]) > tolerance)
    return ranks


def get_circumcenters(triangles: np.ndarray) -> np.ndarray:
    second, third = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    second_squared, third_squared = (second**2).sum(axis=1), (third**2).sum(axis=1)
    denominator = 2 * (second[:, 0] * third[:, 1] - second[:, 1] * third[:, 0])
    x = (third[:, 1] * second_squared - second[:, 1] * third_squared) / denominator
    y = (second[:, 0] * third_squared - third[:, 0] * second_squared) / denominator
    return triangles[:, 0] + np.stack([x, y], axis=1)


def get_periodic_corners(polygons: np.ndarray, number_of_points: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    For polygons (rows of point indices) of points tiled 3 x 3 (point index = tile * number_of_points + point): the
    corners of each, the same for all its copies, and whether a polygon is the copy whose lowest point lies in the
    central tile. A corner is its tile relative to that lowest point's times number_of_points plus its point, sorted.
    """
    points, tiles = polygons % number_of_points, polygons // number_of_points
    anchors = IMAGE_SHIFTS[tiles[np.arange(len(tiles)), np.argmin(points, axis=1)]]
    relative = IMAGE_SHIFTS[tiles] - anchors[:, None]
    corners = np.sort(((relative[..., 0] + 1) * 3 + relative[..., 1] + 1) * number_of_points + points, axis=1)
    return corners, np.all(anchors == 0, axis=1)


def get_triangle_keys(simplices: np.ndarray, number_of_points: int) -> Tuple[np.ndarray, np.ndarray]:
    """One integer key per periodic triangle, its corners in base 9 * number_of_points; and whether it is central."""
    corners, central = get_periodic_corners(simplices, number_of_points)
    base = 9 * number_of_points
    return (corners[:, 0] * base + corners[:, 1]) * base + corners[:, 2], central


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


class CocircularTriangulation(InMemoryEntityPydantic):
    """
    Delaunay triangles of ring centres tiled 3 x 3. Where four or more centres lie on one empty circle the
    triangulation is not unique: each such group is triangulated so that its centres get rings of the allowed sizes,
    one group after another by the position of its circle (y, then x), given the groups before it; among equally good
    triangulations the one whose diagonals' centres come first by (y, x) in the cell, so that the choice depends on
    positions only. The group whose lowest centre lies in the central cell is resolved; its copies follow it.
    """

    model_config = {"arbitrary_types_allowed": True}

    images: np.ndarray
    simplices: np.ndarray
    lattice_vectors: np.ndarray
    allowed_ring_sizes: List[int]

    @cached_property
    def number_of_centers(self) -> int:
        return len(self.images) // len(IMAGE_SHIFTS)

    @cached_property
    def tree(self) -> cKDTree:
        return cKDTree(self.images)

    @cached_property
    def circle_centers(self) -> np.ndarray:
        """Centre of the circumcircle of each triangle."""
        return get_circumcenters(self.images[self.simplices])

    @cached_property
    def circle_radii(self) -> np.ndarray:
        return np.linalg.norm(self.images[self.simplices[:, 0]] - self.circle_centers, axis=1)

    @cached_property
    def candidates(self) -> np.ndarray:
        """
        Triangles whose empty circumcircle holds four or more centres; circles wider than half the shorter cell vector
        (slivers at the border of the tiling) are left out, so a group never holds two copies of one centre.
        """
        centers, radii = self.circle_centers, self.circle_radii
        outer = self.tree.query_ball_point(centers, radii + COCIRCULAR_TOLERANCE, return_length=True)
        inner = self.tree.query_ball_point(centers, radii - COCIRCULAR_TOLERANCE, return_length=True)
        shortest_cell_vector = np.linalg.norm(self.lattice_vectors, axis=1).min()
        return np.flatnonzero((outer - inner > 3) & (radii < shortest_cell_vector / 2))

    def get_circle_points(self, simplex: int) -> Tuple[int, ...]:
        """Centres on the circumcircle of a triangle, ordered around it."""
        center, radius = self.circle_centers[simplex], self.circle_radii[simplex]
        points = np.array(self.tree.query_ball_point(center, radius + COCIRCULAR_TOLERANCE))
        points = points[np.linalg.norm(self.images[points] - center, axis=1) > radius - COCIRCULAR_TOLERANCE]
        return tuple(points[np.argsort(np.arctan2(*(self.images[points] - center).T[::-1]))])

    @cached_property
    def groups(self) -> Dict[Tuple[int, ...], List[int]]:
        """
        Centres of each group, ordered around the circle, with the Delaunay triangles of the group; only groups whose
        Delaunay triangles fill the polygon (none shared with an overlapping group).
        """
        groups: Dict[Tuple[int, ...], List[int]] = {}
        for simplex in self.candidates:
            groups.setdefault(self.get_circle_points(simplex), []).append(simplex)
        return {points: members for points, members in groups.items() if len(members) == len(points) - 2}

    @cached_property
    def group_points(self) -> List[np.ndarray]:
        return [np.array(points) for points in self.groups]

    @cached_property
    def group_members(self) -> List[List[int]]:
        return list(self.groups.values())

    @cached_property
    def group_representatives(self) -> Dict[int, int]:
        """
        Each group that has a copy whose lowest centre lies in the central cell, matched by its corners relative to that
        centre, with that copy. A group with no such copy (a sliver at the border of the tiling) is not in it.
        """
        periodic_corners = [get_periodic_corners(points[None], self.number_of_centers) for points in self.group_points]
        keys = [tuple(corners[0]) for corners, _ in periodic_corners]
        representatives = {keys[group]: group for group, (_, central) in enumerate(periodic_corners) if central[0]}
        return {group: representatives[key] for group, key in enumerate(keys) if key in representatives}

    @cached_property
    def group_triangulations(self) -> Dict[int, List[List[Tuple[int, int, int]]]]:
        representatives = set(self.group_representatives.values())
        return {group: get_triangulations(0, len(self.group_points[group]) - 1) for group in representatives}

    @cached_property
    def is_group_triangle(self) -> np.ndarray:
        """Triangles of the groups that are resolved; those of a sliver group stay as Delaunay made them."""
        is_group_triangle = np.zeros(len(self.simplices), bool)
        is_group_triangle[
            [simplex for group in self.group_representatives for simplex in self.group_members[group]]
        ] = True
        return is_group_triangle

    def get_ring_sizes(self, group: int, triangulation: int) -> np.ndarray:
        """Triangles at each ring centre (its ring size) that one triangulation of a group contributes."""
        triangles = np.array(self.group_triangulations[group][triangulation])
        corners = self.group_points[group][triangles] % self.number_of_centers
        return np.bincount(corners.ravel(), minlength=self.number_of_centers)

    def get_diagonal_key(self, group: int, triangulation: int) -> List[List[Tuple[int, ...]]]:
        """The diagonals of one triangulation of a group, each as its two centres' ranks by (y, x) in the cell."""
        points = self.group_points[group]
        positions = wrap_to_lattice(self.images[points], self.lattice_vectors)
        corners = np.column_stack([get_tolerant_ranks(positions[:, axis], TIE_KEY_TOLERANCE) for axis in (1, 0)])
        triangles = self.group_triangulations[group][triangulation]
        edges = {tuple(sorted(edge)) for triangle in triangles for edge in combinations(triangle, 2)}
        diagonals = [(first, second) for first, second in edges if second - first not in (1, len(points) - 1)]
        return sorted(sorted([tuple(corners[first]), tuple(corners[second])]) for first, second in diagonals)

    def get_first_triangulation(self, group: int) -> int:
        """The triangulation of a group with the smallest diagonal key."""
        return min(range(len(self.group_triangulations[group])), key=partial(self.get_diagonal_key, group))

    @cached_property
    def group_order(self) -> List[int]:
        """Groups to resolve by the position of their circle in the cell, y then x."""
        groups = list(self.group_triangulations)
        first_members = [self.group_members[group][0] for group in groups]
        centers = wrap_to_lattice(self.circle_centers[first_members].reshape(-1, 2), self.lattice_vectors)
        return [groups[index] for index in np.lexsort((centers[:, 0], centers[:, 1]))]

    @cached_property
    def choices(self) -> Dict[int, int]:
        """
        Triangulation of each group: the fewest centres with rings outside the allowed sizes, given the others, then
        the smallest diagonal key.
        """
        _, central = get_triangle_keys(self.simplices, self.number_of_centers)
        ungrouped_corners = self.simplices[central & ~self.is_group_triangle] % self.number_of_centers
        choices = {group: self.get_first_triangulation(group) for group in self.group_triangulations}
        ring_sizes = np.bincount(ungrouped_corners.ravel(), minlength=self.number_of_centers)
        ring_sizes += sum(self.get_ring_sizes(group, triangulation) for group, triangulation in choices.items())
        for group in self.group_order:
            ring_sizes -= self.get_ring_sizes(group, choices[group])
            centers = self.group_points[group] % self.number_of_centers
            scores = []
            for triangulation in range(len(self.group_triangulations[group])):
                sizes = (ring_sizes + self.get_ring_sizes(group, triangulation))[centers]
                outside = (~np.isin(sizes, self.allowed_ring_sizes)).sum()
                scores.append((outside, self.get_diagonal_key(group, triangulation), triangulation))
            choices[group] = min(scores)[2]
            ring_sizes += self.get_ring_sizes(group, choices[group])
        return choices

    @cached_property
    def resolved_simplices(self) -> Tuple[np.ndarray, np.ndarray]:
        """Triangles counterclockwise, the groups triangulated as chosen; and which triangles came from a group."""
        added = [
            self.group_points[group][np.array(self.group_triangulations[representative][self.choices[representative]])]
            for group, representative in self.group_representatives.items()
        ]
        simplices = np.vstack([self.simplices[~self.is_group_triangle], *added])
        corners = self.images[simplices]
        clockwise = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]) < 0
        simplices[clockwise] = simplices[clockwise][:, [0, 2, 1]]
        return simplices, np.arange(len(simplices)) >= (~self.is_group_triangle).sum()


class RingNetwork(InMemoryEntityPydantic):
    """
    Sites (Voronoi vertices of the ring centres): positions, bonds grouped by site (BONDS_PER_SITE each, in order
    around it) with the ring on the left of each bond; and the ring centres.
    """

    model_config = {"arbitrary_types_allowed": True}

    positions: np.ndarray
    bonds: Bonds
    bond_rings: np.ndarray
    ring_centers: np.ndarray


class HoneycombLattice(InMemoryEntityPydantic):
    """
    A honeycomb lattice in the cell: vectors (rows), a site of sublattice 0, the offset to sublattice 1, and the two
    input sites whose atoms are the columns of the sublattices.
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


class RingNetworkAnalyzer(RingsMaterialAnalyzer):
    """
    Ring network of a honeycomb 2D material (graphene, h-BN, MoS2) built from ring centres in its cell: the centres are
    triangulated periodically (CocircularTriangulation), and each triangle becomes a site, at its circumcentre, bonded
    to the sites of the three triangles beside it. A site takes the atoms of the input site of its sublattice in
    `honeycomb_lattice`. The material's own ring centres give back its own sites.
    """

    @cached_property
    def honeycomb_lattice(self) -> HoneycombLattice:
        """Lattice of the first site: sublattice 1 at its first bond, vectors between the ends of its bonds."""
        first, second, vectors = self.bonds
        site_bonds = np.where(first == 0)[0]
        return HoneycombLattice(
            vectors=vectors[site_bonds[0]] - vectors[site_bonds[1:]],
            origin=self.site_positions[0],
            sublattice_offset=vectors[site_bonds[0]],
            sublattice_sites=(0, int(second[site_bonds[0]])),
        )

    def get_triangulation(
        self, centers: np.ndarray, ring_sizes: Sequence[int]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Tiled ring centres and their triangles, co-circular groups triangulated for hexagons and `ring_sizes`."""
        images = get_periodic_images(centers, self.lattice_vectors)
        triangulation = CocircularTriangulation(
            images=images,
            simplices=Delaunay(images).simplices,
            lattice_vectors=self.lattice_vectors,
            allowed_ring_sizes=[HEXAGON_SIZE, *ring_sizes],
        )
        return (images, *triangulation.resolved_simplices)

    def get_network(self, centers: np.ndarray, ring_sizes: Sequence[int]) -> RingNetwork:
        """Voronoi network of ring centres in the cell, co-circular centres given rings of hexagons and `ring_sizes`."""
        images, simplices, from_group = self.get_triangulation(centers, ring_sizes)
        keys, central = get_triangle_keys(simplices, len(centers))
        vertices = np.where(central)[0][np.argsort(keys[central])]
        neighbors = get_triangle_neighbors(simplices)[vertices].ravel()
        # the triangles of a group share one circumcentre; their centroids keep the sites apart
        anchors = np.where(from_group[:, None], images[simplices].mean(axis=1), get_circumcenters(images[simplices]))
        first = np.repeat(np.arange(len(vertices)), BONDS_PER_SITE)
        second = np.searchsorted(keys[vertices], keys[neighbors])
        if not np.array_equal(keys[vertices][second % len(vertices)], keys[neighbors]):
            raise self.get_small_cell_error()
        return RingNetwork(
            positions=anchors[vertices],
            bonds=(first, second, anchors[neighbors] - anchors[vertices][first]),
            bond_rings=simplices[vertices][:, [2, 0, 1]].ravel() % len(centers),
            ring_centers=centers,
        )

    def get_small_cell_error(self) -> ValueError:
        return ValueError("The cell is too small for its periodic ring network; use a larger supercell")

    def get_column_sites(self, network: RingNetwork) -> np.ndarray:
        """The input site whose atoms each site of the network takes: that of its sublattice."""
        sublattices = self.honeycomb_lattice.get_sublattices(network.positions)
        return np.array(self.honeycomb_lattice.sublattice_sites)[sublattices]

    def get_rings_analyzer(self, network: RingNetwork, column_sites: np.ndarray) -> RingsNetworkAnalyzer:
        """Rings of the network, each site of the species of its column."""
        return RingsNetworkAnalyzer(
            material=self.material,
            network_positions=network.positions,
            network_species=self.site_species[column_sites],
            network_bonds=network.bonds,
            network_bond_rings=network.bond_rings,
            network_ring_centers=network.ring_centers,
        )
