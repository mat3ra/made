from collections import Counter
from functools import cached_property
from typing import Dict, List, Tuple

import numpy as np
from pydantic import BaseModel
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from . import BaseMaterialAnalyzer

HEXAGON_SIZE = 6
# a dislocation core pairs an n-membered ring with a (12 - n)-membered one: 5|7, 4|8
CORE_RING_SIZES_SUM = 12
IMAGE_SHIFTS = np.array([[i, j] for i in (-1, 0, 1) for j in (-1, 0, 1)])
CENTRAL_IMAGE_INDEX = 4
Bonds = Tuple[np.ndarray, np.ndarray, np.ndarray]


def get_periodic_images(positions: np.ndarray, lattice_vectors: np.ndarray) -> np.ndarray:
    """Positions repeated over the 3 x 3 cells around the central one, central copy at CENTRAL_IMAGE_INDEX."""
    return (positions[None] + (IMAGE_SHIFTS @ lattice_vectors)[:, None]).reshape(-1, 2)


def sort_bonds(first: np.ndarray, second: np.ndarray, vectors: np.ndarray) -> Bonds:
    order = np.lexsort((np.arctan2(vectors[:, 1], vectors[:, 0]), first))
    return first[order], second[order], vectors[order]


def get_canonical_sequence(ring_sizes: List[int], is_closed: bool) -> str:
    """Smallest of the rotations (of a chain) and reversals, so the same arrangement reads the same at both lines."""
    rotations = [ring_sizes[index:] + ring_sizes[:index] for index in range(len(ring_sizes) if is_closed else 1)]
    text = "-".join(str(size) for size in min(rotations + [sequence[::-1] for sequence in rotations]))
    return f"({text})" if is_closed else f"[{text}]"


class RingsArrangement(BaseModel):
    """
    Rings other than hexagons nearest one line, and the bonds between sites of one species there. `sequence` holds
    each cluster of edge-sharing rings: "[5-7]" for a cluster, "(5-7-5-7)" for a chain closing through the cell.
    """

    ring_sizes: Dict[int, int]
    sequence: List[str]
    homo_bonds: Dict[str, int]
    rings_without_core_partner: int


class RingsMaterialAnalyzer(BaseMaterialAnalyzer):
    """
    Rings of the top-view bond network of a 2D material: the faces of that periodic planar network, their sizes, and
    how the rings other than hexagons are arranged along lines of the cell (grain boundaries). A site is the set of
    atoms sharing one top-view position (MoS2: Mo, and the two S above each other); sites closer than
    `bond_cutoff_factor` times the median nearest-site distance are bonded.
    """

    site_tolerance: float = 0.05
    bond_cutoff_factor: float = 1.3

    @cached_property
    def lattice_vectors(self) -> np.ndarray:
        return np.array(self.material.lattice.vector_arrays)[:2, :2]

    @cached_property
    def atom_positions(self) -> np.ndarray:
        material = self.material.clone()
        material.to_crystal()
        return (np.array(material.basis.coordinates.values)[:, :2]) @ self.lattice_vectors

    def get_pairs(self, positions: np.ndarray, cutoff: float) -> Bonds:
        """Pairs (i, j, vector from i to an image of j) closer than the cutoff, periodic in the plane of the cell."""
        images = get_periodic_images(positions, self.lattice_vectors)
        neighbors = cKDTree(images).query_ball_point(positions, cutoff)
        first = np.repeat(np.arange(len(positions)), [len(indices) for indices in neighbors])
        image_indices = np.concatenate(neighbors).astype(int)
        keep = image_indices != CENTRAL_IMAGE_INDEX * len(positions) + first
        first, image_indices = first[keep], image_indices[keep]
        return first, image_indices % len(positions), images[image_indices] - positions[first]

    @cached_property
    def atom_site_indices(self) -> np.ndarray:
        first, second, _ = self.get_pairs(self.atom_positions, self.site_tolerance)
        number_of_atoms = len(self.atom_positions)
        graph = coo_matrix((np.ones(len(first)), (first, second)), shape=(number_of_atoms, number_of_atoms))
        return connected_components(graph, directed=False)[1]

    @cached_property
    def site_first_atoms(self) -> np.ndarray:
        return np.unique(self.atom_site_indices, return_index=True)[1]

    @cached_property
    def site_positions(self) -> np.ndarray:
        return self.atom_positions[self.site_first_atoms]

    @cached_property
    def site_species(self) -> np.ndarray:
        return np.array(self.material.basis.elements.values)[self.site_first_atoms]

    @cached_property
    def bonds(self) -> Bonds:
        """Directed bonds (site, neighbor site, vector), grouped by site in counterclockwise order."""
        images = get_periodic_images(self.site_positions, self.lattice_vectors)
        nearest_distances = cKDTree(images).query(self.site_positions, k=2)[0][:, 1]
        return sort_bonds(*self.get_pairs(self.site_positions, self.bond_cutoff_factor * np.median(nearest_distances)))

    @cached_property
    def reverse_bonds(self) -> np.ndarray:
        first, second, vectors = self.bonds
        image_vectors = vectors - self.site_positions[second] + self.site_positions[first]
        images = np.round(image_vectors @ np.linalg.inv(self.lattice_vectors)).astype(int).tolist()
        keys = [(i, j, *image) for i, j, image in zip(first.tolist(), second.tolist(), images)]
        index = {key: bond for bond, key in enumerate(keys)}
        return np.array([index[(j, i, -image_x, -image_y)] for i, j, image_x, image_y in keys])

    @cached_property
    def next_bonds(self) -> np.ndarray:
        """The bond following each bond around its ring: the clockwise neighbor of its reverse."""
        first = self.bonds[0]
        degrees = np.bincount(first)
        starts = np.cumsum(degrees) - degrees
        positions_at_site = np.arange(len(first)) - starts[first]
        heads = first[self.reverse_bonds]
        return starts[heads] + (positions_at_site[self.reverse_bonds] - 1) % degrees[heads]

    @cached_property
    def rings(self) -> List[np.ndarray]:
        """Bonds around each ring."""
        visited = np.zeros(len(self.next_bonds), bool)
        rings = []
        for start in range(len(self.next_bonds)):
            bond, ring = start, []
            while not visited[bond]:
                visited[bond] = True
                ring.append(bond)
                bond = self.next_bonds[bond]
            rings += [np.array(ring)] if ring else []
        return rings

    @cached_property
    def ring_sizes(self) -> np.ndarray:
        return np.array([len(ring) for ring in self.rings])

    @cached_property
    def ring_of_bond(self) -> np.ndarray:
        ring_of_bond = np.empty(len(self.next_bonds), int)
        ring_of_bond[np.concatenate(self.rings)] = np.repeat(np.arange(len(self.rings)), self.ring_sizes)
        return ring_of_bond

    @cached_property
    def ring_centers(self) -> np.ndarray:
        """Mean of each ring's corners, followed around the ring from its first site (unwrapped across the cell)."""
        first, _, vectors = self.bonds
        starts = self.site_positions[[first[ring[0]] for ring in self.rings]]
        return starts + np.array(
            [np.mean(np.cumsum(vectors[ring], axis=0) - vectors[ring], axis=0) for ring in self.rings]
        )

    def get_nearest_lines(self, x_values: np.ndarray, line_positions: List[float]) -> np.ndarray:
        """Index of the nearest line x = const to each x, periodic in the cell width."""
        width = self.lattice_vectors[0, 0]
        return np.argmin(np.abs((np.subtract.outer(x_values, line_positions) + width / 2) % width - width / 2), axis=1)

    def get_line_arrangements(self, line_positions: List[float]) -> List[RingsArrangement]:
        """Arrangement nearest each line x = const of a cell whose first lattice vector lies along x."""
        ring_lines = self.get_nearest_lines(self.ring_centers[:, 0], line_positions)
        first, _, vectors = self.bonds
        bond_lines = self.get_nearest_lines(self.site_positions[first, 0] + vectors[:, 0] / 2, line_positions)
        defect_rings = self.ring_sizes != HEXAGON_SIZE
        return [
            self.get_arrangement(np.where(defect_rings & (ring_lines == line))[0], bond_lines == line)
            for line in range(len(line_positions))
        ]

    def get_arrangement(self, rings: np.ndarray, line_bonds: np.ndarray) -> RingsArrangement:
        """Arrangement of the given rings, each with its neighbors among them (one entry per shared edge)."""
        neighbors: Dict[int, List[int]] = {ring: [] for ring in rings}
        rings_without_core_partner = 0
        for ring in rings:
            adjacent = self.ring_of_bond[self.reverse_bonds[self.rings[ring]]]
            neighbors[ring] = [neighbor for neighbor in adjacent if neighbor in neighbors]
            partner_size = CORE_RING_SIZES_SUM - self.ring_sizes[ring]
            rings_without_core_partner += not np.any(self.ring_sizes[adjacent] == partner_size)
        return RingsArrangement(
            ring_sizes=dict(Counter(self.ring_sizes[rings].tolist())),
            sequence=sorted(self.get_cluster_sequence(cluster, neighbors) for cluster in self.get_clusters(neighbors)),
            homo_bonds=self.get_homo_bonds(line_bonds),
            rings_without_core_partner=rings_without_core_partner,
        )

    def get_clusters(self, neighbors: Dict[int, List[int]]) -> List[List[int]]:
        rings = list(neighbors)
        index = {ring: position for position, ring in enumerate(rings)}
        pairs = [(index[ring], index[neighbor]) for ring in rings for neighbor in neighbors[ring]]
        rows, columns = np.array(pairs, int).reshape(-1, 2).T
        graph = coo_matrix((np.ones(len(rows)), (rows, columns)), shape=(len(rings), len(rings)))
        labels = connected_components(graph, directed=False)[1]
        return [[ring for ring, label in zip(rings, labels) if label == cluster] for cluster in np.unique(labels)]

    def get_cluster_sequence(self, cluster: List[int], neighbors: Dict[int, List[int]]) -> str:
        """Ring sizes walked from an end of the cluster; a chain shares as many edges as it has rings."""
        distinct_neighbors = [len(set(neighbors[ring])) for ring in cluster]
        path = [cluster[int(np.argmin(distinct_neighbors))]]
        while following := [ring for ring in neighbors[path[-1]] if ring not in path]:
            path.append(following[0])
        shared_edges = sum(len(neighbors[ring]) for ring in cluster) // 2
        return get_canonical_sequence([int(self.ring_sizes[ring]) for ring in path], shared_edges >= len(cluster))

    def get_homo_bonds(self, line_bonds: np.ndarray) -> Dict[str, int]:
        first, second, _ = self.bonds
        species = self.site_species
        homo = line_bonds & (species[first] == species[second]) & (len(set(species)) > 1)
        return {f"{element}-{element}": count // 2 for element, count in Counter(species[first[homo]]).items()}


class RingsNetworkAnalyzer(RingsMaterialAnalyzer):
    """
    The same analysis for a given network of sites in the cell of the material: positions, species, bonds.
    """

    model_config = {"arbitrary_types_allowed": True}

    network_positions: np.ndarray
    network_species: np.ndarray
    network_bonds: Bonds

    @cached_property
    def site_positions(self) -> np.ndarray:
        return self.network_positions

    @cached_property
    def site_species(self) -> np.ndarray:
        return self.network_species

    @cached_property
    def bonds(self) -> Bonds:
        return sort_bonds(*self.network_bonds)
