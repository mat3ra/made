"""The grains of a boundary as lattices in the stacked cell, and its bond network: as stacked, or rebuilt one atom per
triangle of both grains' hexagon centres (the dual-lattice construction of Ophus et al., PRB 92, 205402 (2015))."""
from collections import Counter
from typing import List, NamedTuple, Optional, Tuple

import numpy as np
from mat3ra.made.basis import Basis
from mat3ra.made.lattice import COORDINATE_TOLERANCE
from scipy.spatial import Delaunay

from .....analyze.rings import IMAGE_SHIFTS, Bond, get_nearest_bonds, get_periodic_images
from .....build_components import MaterialWithBuildMetadata
from .....modify import wrap_to_unit_cell

# lattice points on the edge of a grain's cell belong to it once: the window [-tolerance, 1 - tolerance) of cell
# fractions is wider than the rounding of stored crystal coordinates (6 decimals)
CELL_FRACTION_TOLERANCE = 1e-4

# a triangle's corners: (hexagon centre, cell shift of its copy)
Corners = List[Tuple[int, Tuple[int, int]]]


class Monolayer(NamedTuple):
    """A honeycomb monolayer: lattice vectors, its two top-view sites (x, y fractions), each site's (element, z)."""

    lattice_vectors: np.ndarray
    site_fractions: np.ndarray
    columns: List[List[Tuple[str, float]]]


class Grain(NamedTuple):
    """A grain in the stacked cell: its supercell matrix (across, along the line), cell size and cell corner."""

    supercell_matrix: np.ndarray
    size: np.ndarray
    origin: np.ndarray


class Network(NamedTuple):
    """Sites (positions, monolayer site of each), bonds, and the sites settling moves: those joining the grains."""

    positions: np.ndarray
    sites: List[int]
    bonds: List[Bond]
    moving: List[int]


def get_monolayer(slab: MaterialWithBuildMetadata) -> Monolayer:
    """The monolayer of a one-layer slab; atoms sharing x, y (MoS2's sulfur pair) are one top-view site."""
    slab = slab.clone()
    slab.to_crystal()
    columns: dict = {}
    for (x, y, z), element in zip(slab.basis.coordinates.values, slab.basis.elements.values):
        site = (round(x, COORDINATE_TOLERANCE), round(y, COORDINATE_TOLERANCE))
        columns.setdefault(site, []).append((element, z * slab.lattice.c))
    return Monolayer(np.array(slab.lattice.vector_arrays)[:2, :2], np.array(list(columns)), list(columns.values()))


def get_grains(monolayer: Monolayer, supercell_matrices: list, slide: float) -> List[Grain]:
    """Both grains as stacked: the first at the origin, the second after it along x and slid along y."""
    sizes = [np.linalg.norm(np.array(matrix) @ monolayer.lattice_vectors, axis=1) for matrix in supercell_matrices]
    origins = [np.zeros(2), np.array([sizes[0][0], slide])]
    return [Grain(np.array(matrix), size, origin) for matrix, size, origin in zip(supercell_matrices, sizes, origins)]


def get_cell_size(grains: List[Grain]) -> np.ndarray:
    """Width and period of the stacked cell."""
    return np.array([grains[0].size[0] + grains[1].size[0], grains[0].size[1]])


def get_grain_points(grain: Grain, fraction: np.ndarray) -> List[np.ndarray]:
    """The lattice translates of a point of the monolayer (x, y fractions) inside the grain's cell, as stacked."""
    corners = np.array([[0, 0], *grain.supercell_matrix, grain.supercell_matrix.sum(axis=0)])
    points = []
    for first in range(corners[:, 0].min() - 1, corners[:, 0].max() + 1):
        for second in range(corners[:, 1].min() - 1, corners[:, 1].max() + 1):
            cell_fraction = (fraction + [first, second]) @ np.linalg.inv(grain.supercell_matrix)
            if np.all((cell_fraction >= -CELL_FRACTION_TOLERANCE) & (cell_fraction < 1 - CELL_FRACTION_TOLERANCE)):
                points.append(grain.origin + cell_fraction * grain.size)
    return points


def get_nearest_site(monolayer: Monolayer, grain: Grain, position: np.ndarray) -> int:
    """The monolayer site whose lattice in the grain passes nearest the position."""
    primitive_vectors = np.linalg.inv(grain.supercell_matrix) @ np.diag(grain.size)
    fraction = (position - grain.origin) @ np.linalg.inv(primitive_vectors)
    distances = []
    for site_fraction in monolayer.site_fractions:
        offsets = fraction - site_fraction - np.round(fraction - site_fraction) - np.array(IMAGE_SHIFTS)
        distances.append(np.min(np.linalg.norm(offsets @ primitive_vectors, axis=1)))
    return int(np.argmin(distances))


def get_stacked_network(monolayer: Monolayer, grains: List[Grain]) -> Network:
    """The sites of both grains as stacked, each bonded to its three nearest; those bonded across a line move."""
    sites = [
        (point, site, index)
        for index, grain in enumerate(grains)
        for site, fraction in enumerate(monolayer.site_fractions)
        for point in get_grain_points(grain, fraction)
    ]
    positions = np.array([point for point, _, _ in sites])
    bonds = get_nearest_bonds(positions, get_cell_size(grains))
    moving = sorted({first for first, second, _ in bonds if sites[first][2] != sites[second][2]})
    return Network(positions, [site for _, site, _ in sites], bonds, moving)


def get_hexagon_centers(monolayer: Monolayer, grains: List[Grain]) -> Tuple[np.ndarray, List[int]]:
    """Hexagon centres of both grains, at the honeycomb's empty third site 2 B - A, and the grain of each."""
    first, second = monolayer.site_fractions
    centers = [get_grain_points(grain, 2 * second - first) for grain in grains]
    return np.concatenate(centers), [index for index, points in enumerate(centers) for _ in points]


def get_triangle_identity(corners: Corners) -> tuple:
    """A triangle's corners relative to its least corner: one value for all its periodic copies."""
    least_shift = min(corners)[1]
    return tuple(sorted((center, (shift[0] - least_shift[0], shift[1] - least_shift[1])) for center, shift in corners))


def get_triangle_center(triangulation: Delaunay, triangle: int) -> np.ndarray:
    """Circumcentre of a triangle of the triangulation."""
    corners = triangulation.points[triangulation.simplices[triangle]]
    edges = np.array([corners[1] - corners[0], corners[2] - corners[0]])
    return corners[0] + np.linalg.solve(2 * edges, [edges[0] @ edges[0], edges[1] @ edges[1]])


def get_triangle_bonds(
    triangulation: Delaunay, corners: List[Corners], triangles: List[int], positions: np.ndarray, cell_size: np.ndarray
) -> Optional[List[Bond]]:
    """Bonds between atoms of triangles sharing an edge; None if copies differ (four centres share a circle)."""
    atoms = {get_triangle_identity(corners[triangle]): atom for atom, triangle in enumerate(triangles)}
    bonds = []
    for atom, triangle in enumerate(triangles):
        for neighbor in triangulation.neighbors[triangle]:
            other = atoms.get(get_triangle_identity(corners[neighbor]))
            center = get_triangle_center(triangulation, neighbor)
            if other is None:
                return None
            shift_x, shift_y = np.round((center - positions[other]) / cell_size).astype(int).tolist()
            bonds.append((atom, other, (shift_x, shift_y)))
    return bonds


def get_rebuilt_network(monolayer: Monolayer, grains: List[Grain]) -> Optional[Network]:
    """
    One site per triangle of hexagon centres, at its circumcentre, of the site of the grain holding two or three of its
    corners; the sites of triangles spanning both grains move. None if four centres share a circle.
    """
    centers, center_grains = get_hexagon_centers(monolayer, grains)
    triangulation = Delaunay(get_periodic_images(centers, get_cell_size(grains)))
    count = len(centers)
    simplices = triangulation.simplices
    corners = [[(int(point) % count, IMAGE_SHIFTS[int(point) // count]) for point in simplex] for simplex in simplices]
    # each triangle once: the copy whose least corner lies in the cell itself
    triangles = [triangle for triangle, triangle_corners in enumerate(corners) if min(triangle_corners)[1] == (0, 0)]
    positions = np.array([get_triangle_center(triangulation, triangle) for triangle in triangles])
    bonds = get_triangle_bonds(triangulation, corners, triangles, positions, get_cell_size(grains))
    if bonds is None:
        return None
    grain_counts = [Counter(center_grains[center] for center, _ in corners[triangle]) for triangle in triangles]
    majority_grains = [grains[counts.most_common(1)[0][0]] for counts in grain_counts]
    sites = [get_nearest_site(monolayer, grain, position) for grain, position in zip(majority_grains, positions)]
    return Network(positions, sites, bonds, [atom for atom, counts in enumerate(grain_counts) if len(counts) > 1])


def get_network(monolayer: Monolayer, grains: List[Grain], core_ring_sizes: List[int]) -> Optional[Network]:
    """The boundary's network: rebuilt for odd rings (5|7); even cores (4|8, 6) form from the grains as stacked."""
    if any(size % 2 for size in core_ring_sizes):
        return get_rebuilt_network(monolayer, grains)
    return get_stacked_network(monolayer, grains)


def get_material_with_sites(
    material: MaterialWithBuildMetadata, monolayer: Monolayer, positions: np.ndarray, sites: List[int]
) -> MaterialWithBuildMetadata:
    """The material with its atoms replaced by each monolayer site's atoms at the given top-view positions."""
    atoms = [(element, [*xy, z]) for xy, site in zip(positions, sites) for element, z in monolayer.columns[site]]
    rebuilt = material.clone()
    rebuilt.basis = Basis.from_dict(
        elements=[{"id": index, "value": element} for index, (element, _) in enumerate(atoms)],
        coordinates=[{"id": index, "value": coordinate} for index, (_, coordinate) in enumerate(atoms)],
        units="cartesian",
        cell=rebuilt.lattice.vector_arrays,
        labels=[],
        constraints=[],
    )
    rebuilt.to_crystal()
    return wrap_to_unit_cell(rebuilt)
