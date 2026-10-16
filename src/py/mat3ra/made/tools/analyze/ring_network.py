from functools import cached_property, partial
from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from scipy.spatial import Delaunay, cKDTree

from ...utils import get_tolerant_ranks
from .rings import IMAGE_SHIFTS, RingNetwork, get_periodic_images

# a Voronoi vertex is the circumcentre of one Delaunay triangle, so every site of the network has three bonds
BONDS_PER_SITE = 3
# positions this close are one: above the tie-breaking displacement (1e-5) and the rounding of stored coordinates; the
# measured margins (spectrum rows) are 1.5e-3 from a co-circular circle to the nearest other centre and 3.9e-3 from the
# rebuilt band's edge to the nearest site off it
POSITION_TOLERANCE = 1e-3  # angstrom
# positions closer than this are equal when two triangulations of a group are equally good: above the ~1e-7 angstrom
# by which centres from coordinates stored to 9 decimals differ, below the tie-breaking displacement (1e-5), which it
# must not merge
TIE_KEY_TOLERANCE = 1e-6  # angstrom


def wrap_to_cell(values: np.ndarray, periods) -> np.ndarray:
    """Values modulo their periods, values within rounding of a period mapped to 0 (one owner per cell edge)."""
    wrapped = values % periods
    return np.where(np.isclose(wrapped, periods), 0.0, wrapped)


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


class CocircularGroup(InMemoryEntityPydantic):
    """Centres on one empty circle, in order around it, and the Delaunay triangles between them."""

    model_config = {"arbitrary_types_allowed": True}

    points: np.ndarray
    members: List[int]


class CocircularTriangulation(InMemoryEntityPydantic):
    """
    Delaunay triangles of ring centres tiled 3 x 3. Where four or more centres lie on one empty circle the
    triangulation is not unique: each such group is triangulated so that its centres get rings of the allowed sizes,
    one group after another by the position of its circle (y, then x), given the groups before it; among equally good
    triangulations the one whose diagonals' centres come first by (y, x) in the cell, so that the choice depends on
    positions only. The copy of a group whose lowest centre lies in the central cell is resolved; its copies follow it.
    """

    model_config = {"arbitrary_types_allowed": True}

    centers: np.ndarray
    lattice_vectors: np.ndarray
    allowed_ring_sizes: List[int]
    small_cell_message: str = "The cell is too small for its periodic ring network; use a larger supercell"

    @cached_property
    def images(self) -> np.ndarray:
        return get_periodic_images(self.centers, self.lattice_vectors)

    @cached_property
    def simplices(self) -> np.ndarray:
        return Delaunay(self.images).simplices

    @cached_property
    def circles(self) -> Tuple[np.ndarray, np.ndarray]:
        """Centre and radius of the circumcircle of each triangle."""
        centers = get_circumcenters(self.images[self.simplices])
        return centers, np.linalg.norm(self.images[self.simplices[:, 0]] - centers, axis=1)

    @cached_property
    def groups(self) -> List[CocircularGroup]:
        """
        Centres on the empty circumcircle of a triangle, four or more, narrower than half the shorter cell vector (wider
        ones are slivers at the border of the tiling), whose Delaunay triangles fill their polygon.
        """
        centers, radii = self.circles
        tree = cKDTree(self.images)
        outer = tree.query_ball_point(centers, radii + POSITION_TOLERANCE, return_length=True)
        inner = tree.query_ball_point(centers, radii - POSITION_TOLERANCE, return_length=True)
        shortest_cell_vector = np.linalg.norm(self.lattice_vectors, axis=1).min()
        groups: Dict[Tuple[int, ...], List[int]] = {}
        for simplex in np.flatnonzero((outer - inner > 3) & (radii < shortest_cell_vector / 2)):
            points = np.array(tree.query_ball_point(centers[simplex], radii[simplex] + POSITION_TOLERANCE))
            offsets = self.images[points] - centers[simplex]
            on_circle = np.linalg.norm(offsets, axis=1) > radii[simplex] - POSITION_TOLERANCE
            order = np.argsort(np.arctan2(*offsets[on_circle].T[::-1]))
            groups.setdefault(tuple(points[on_circle][order]), []).append(simplex)
        return [
            CocircularGroup(points=np.array(points), members=members)
            for points, members in groups.items()
            if len(members) == len(points) - 2
        ]

    @cached_property
    def representatives(self) -> Dict[int, int]:
        """
        Each group that has a copy whose lowest centre lies in the central cell, matched by its corners relative to that
        centre, with that copy. A group with no such copy (a sliver at the border of the tiling) is not in it.
        """
        periodic_corners = [get_periodic_corners(group.points[None], len(self.centers)) for group in self.groups]
        keys = [tuple(corners[0]) for corners, _ in periodic_corners]
        central = {keys[group]: group for group, (_, is_central) in enumerate(periodic_corners) if is_central[0]}
        return {group: central[key] for group, key in enumerate(keys) if key in central}

    @cached_property
    def triangulations(self) -> Dict[int, List[List[Tuple[int, int, int]]]]:
        """Every triangulation of each resolved group."""
        resolved = set(self.representatives.values())
        return {group: get_triangulations(0, len(self.groups[group].points) - 1) for group in resolved}

    @cached_property
    def is_group_triangle(self) -> np.ndarray:
        """Triangles of the groups that have a resolved copy; those of a sliver group stay as Delaunay made them."""
        is_group_triangle = np.zeros(len(self.simplices), bool)
        is_group_triangle[[simplex for group in self.representatives for simplex in self.groups[group].members]] = True
        return is_group_triangle

    def get_ring_sizes(self, group: int, triangulation: int) -> np.ndarray:
        """Triangles at each ring centre (its ring size) that one triangulation of a group contributes."""
        triangles = self.groups[group].points[np.array(self.triangulations[group][triangulation])]
        return np.bincount((triangles % len(self.centers)).ravel(), minlength=len(self.centers))

    def get_diagonal_key(self, group: int, triangulation: int) -> List[List[Tuple[int, ...]]]:
        """The diagonals of one triangulation of a group, each as its two centres' ranks by (y, x) in the cell."""
        points = self.groups[group].points
        positions = wrap_to_cell(self.images[points] @ np.linalg.inv(self.lattice_vectors), 1.0) @ self.lattice_vectors
        corners = np.column_stack([get_tolerant_ranks(positions[:, axis], TIE_KEY_TOLERANCE) for axis in (1, 0)])
        triangles = self.triangulations[group][triangulation]
        edges = {tuple(sorted(edge)) for triangle in triangles for edge in combinations(triangle, 2)}
        diagonals = [(first, second) for first, second in edges if second - first not in (1, len(points) - 1)]
        return sorted(sorted([tuple(corners[first]), tuple(corners[second])]) for first, second in diagonals)

    @cached_property
    def group_order(self) -> List[int]:
        """Resolved groups by the position of their circle in the cell, y then x."""
        groups = list(self.triangulations)
        centers = self.circles[0][[self.groups[group].members[0] for group in groups]].reshape(-1, 2)
        centers = wrap_to_cell(centers @ np.linalg.inv(self.lattice_vectors), 1.0) @ self.lattice_vectors
        return [groups[index] for index in np.lexsort((centers[:, 0], centers[:, 1]))]

    @cached_property
    def choices(self) -> Dict[int, int]:
        """
        Triangulation of each resolved group, in group_order: the fewest centres with rings outside the allowed sizes,
        given the other groups (those after it as first chosen), then the smallest diagonal key.
        """
        central = get_periodic_corners(self.simplices, len(self.centers))[1]
        ungrouped_corners = self.simplices[central & ~self.is_group_triangle] % len(self.centers)
        choices = {
            group: min(range(len(triangulations)), key=partial(self.get_diagonal_key, group))
            for group, triangulations in self.triangulations.items()
        }
        ring_sizes = np.bincount(ungrouped_corners.ravel(), minlength=len(self.centers))
        ring_sizes += sum(self.get_ring_sizes(group, triangulation) for group, triangulation in choices.items())
        for group in self.group_order:
            ring_sizes -= self.get_ring_sizes(group, choices[group])
            centers = self.groups[group].points % len(self.centers)
            scores = []
            for triangulation in range(len(self.triangulations[group])):
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
            self.groups[group].points[np.array(self.triangulations[representative][self.choices[representative]])]
            for group, representative in self.representatives.items()
        ]
        simplices = np.vstack([self.simplices[~self.is_group_triangle], *added])
        corners = self.images[simplices]
        clockwise = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]) < 0
        simplices[clockwise] = simplices[clockwise][:, [0, 2, 1]]
        return simplices, np.arange(len(simplices)) >= (~self.is_group_triangle).sum()

    @cached_property
    def network(self) -> RingNetwork:
        """
        One site per triangle, at its circumcentre (its centroid if it came from a co-circular group, whose triangles
        share one circumcentre), bonded to the sites of the three triangles beside it. Raises `small_cell_message` when
        a triangle's neighbor has no copy among the central triangles.
        """
        simplices, centroid_triangles = self.resolved_simplices
        corners, central = get_periodic_corners(simplices, len(self.centers))
        base = 9 * len(self.centers)
        keys = (corners[:, 0] * base + corners[:, 1]) * base + corners[:, 2]
        vertices = np.where(central)[0][np.argsort(keys[central])]
        neighbors = get_triangle_neighbors(simplices)[vertices].ravel()
        triangles = self.images[simplices]
        anchors = np.where(centroid_triangles[:, None], triangles.mean(axis=1), get_circumcenters(triangles))
        first = np.repeat(np.arange(len(vertices)), BONDS_PER_SITE)
        second = np.searchsorted(keys[vertices], keys[neighbors])
        if not np.array_equal(keys[vertices][second % len(vertices)], keys[neighbors]):
            raise ValueError(self.small_cell_message)
        return RingNetwork(
            positions=anchors[vertices],
            bonds=(first, second, anchors[neighbors] - anchors[vertices][first]),
            bond_rings=simplices[vertices][:, [2, 0, 1]].ravel() % len(self.centers),
            ring_centers=self.centers,
        )
