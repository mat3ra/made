"""Rings and homo bonds of a 2D material's top-view bond network, read per boundary line from its geometry."""
from collections import Counter, defaultdict
from functools import cached_property
from typing import Dict, List, Set, Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from pydantic import BaseModel
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from . import BaseMaterialAnalyzer
from .utils import IN_PLANE_IMAGE_SHIFTS, get_in_plane_periodic_images

# the ring of a perfect honeycomb; every other ring is a defect ring
HEXAGON_SIZE = 6
# the cell's own images sit in the middle of the in-plane images
CENTRAL_IMAGE_INDEX = len(IN_PLANE_IMAGE_SHIFTS) // 2
# bonds and pairs of rings sharing an edge are listed once in each direction
DIRECTIONS_PER_BOND = 2
Bonds = Tuple[np.ndarray, np.ndarray, np.ndarray]


def get_line_offsets(x_values: np.ndarray, line_positions: List[float], width: float) -> np.ndarray:
    """Signed distance from each line x = const to each x, periodic in the cell width."""
    return (np.subtract.outer(x_values, line_positions) + width / 2) % width - width / 2


def get_canonical_sequence(sizes: List[int]) -> List[int]:
    """The least reading of a cyclic sequence, over every start and both directions."""
    readings = [sizes[start:] + sizes[:start] for start in range(len(sizes))]
    return min(readings + [reading[::-1] for reading in readings])


def get_chain(start: int, neighbors: Dict[int, Set[int]]) -> List[int]:
    """The rings met walking from `start` along shared edges, each step away from the rings already walked."""
    chain = [start]
    following = list(neighbors[start])
    while following:
        chain.append(min(following))
        following = [ring for ring in neighbors[chain[-1]] if ring not in chain]
    return chain


class RingsArrangement(BaseModel):
    """
    Defect rings nearest one line: each cluster of them sharing edges as the ring sizes along the chain they form (its
    least reading, over the starts of a closed chain and both directions; the sorted sizes if a ring shares edges with
    three others), and the pairs of defect rings of one size sharing an edge; the bonds between sites of one species
    there, by species.
    """

    cores: List[List[int]]
    same_size_pairs: int
    homo_bonds: Dict[str, int]


class RingsAndBonds(InMemoryEntityPydantic):
    """
    The rings of a periodic top-view network in a rectangular cell (centres, sizes, the pairs sharing an edge) and its
    bonds (x of the middle, species at both ends), each pair and bond listed once in each direction.
    """

    model_config = {"arbitrary_types_allowed": True}

    ring_centers: np.ndarray
    ring_sizes: np.ndarray
    ring_pairs: np.ndarray
    bond_middle_x: np.ndarray
    bond_species: np.ndarray
    cell: np.ndarray

    def get_nearest_lines(self, x_values: np.ndarray, line_positions: List[float]) -> np.ndarray:
        """The line nearest each x."""
        return np.argmin(np.abs(get_line_offsets(x_values, line_positions, self.cell[0])), axis=1)

    @cached_property
    def defect_pairs(self) -> np.ndarray:
        """The pairs of defect rings sharing an edge."""
        is_defect = self.ring_sizes != HEXAGON_SIZE
        return self.ring_pairs[np.all(is_defect[self.ring_pairs], axis=1)]

    @cached_property
    def clusters(self) -> np.ndarray:
        """Cluster of each ring, defect rings sharing an edge being one."""
        graph = coo_matrix(
            (np.ones(len(self.defect_pairs)), tuple(self.defect_pairs.T)), shape=(len(self.ring_sizes),) * 2
        )
        return connected_components(graph)[1]

    @cached_property
    def defect_neighbors(self) -> Dict[int, Set[int]]:
        """The other defect rings each defect ring shares an edge with."""
        neighbors: Dict[int, Set[int]] = defaultdict(set)
        for first, second in self.defect_pairs.tolist():
            neighbors[first] |= {second} - {first}
        return neighbors

    def get_core(self, rings: np.ndarray) -> List[int]:
        """Sizes of a cluster's rings as RingsArrangement reads them: along their chain, or sorted if it branches."""
        members = set(rings.tolist())
        neighbors = {ring: self.defect_neighbors[ring] & members for ring in members}
        if any(len(others) > 2 for others in neighbors.values()):
            return sorted(self.ring_sizes[rings].tolist())
        ends = [ring for ring, others in neighbors.items() if len(others) < 2]
        sizes = self.ring_sizes[get_chain(min(ends or members), neighbors)].tolist()
        return min(sizes, sizes[::-1]) if ends else get_canonical_sequence(sizes)

    def get_homo_bonds(self, bonds: np.ndarray) -> Dict[str, int]:
        """Bonds between sites of one species among the given ones, by species; none in a material of one species."""
        species = self.bond_species[bonds]
        is_homo = (species[:, 0] == species[:, 1]) & (len(set(self.bond_species.ravel())) > 1)
        counts = Counter(species[is_homo, 0].tolist())
        return {f"{element}-{element}": count // DIRECTIONS_PER_BOND for element, count in counts.items()}

    def get_same_size_pairs(self, is_at_line: np.ndarray) -> int:
        """Pairs of defect rings of one size sharing an edge, among the rings at a line."""
        first, second = self.defect_pairs.T
        is_same_size = (self.ring_sizes[first] == self.ring_sizes[second]) & is_at_line[first]
        return int(np.sum(is_same_size)) // DIRECTIONS_PER_BOND

    def get_arrangement(self, is_ring_at_line: np.ndarray, is_bond_at_line: np.ndarray) -> RingsArrangement:
        """The defect-ring clusters, same-size ring pairs and homo bonds of the rings and bonds at one line."""
        rings = np.flatnonzero((self.ring_sizes != HEXAGON_SIZE) & is_ring_at_line)
        cores = [self.get_core(rings[self.clusters[rings] == cluster]) for cluster in np.unique(self.clusters[rings])]
        return RingsArrangement(
            cores=sorted(cores),
            same_size_pairs=self.get_same_size_pairs(is_ring_at_line),
            homo_bonds=self.get_homo_bonds(np.flatnonzero(is_bond_at_line)),
        )

    def get_line_arrangements(self, line_positions: List[float]) -> List[RingsArrangement]:
        """Arrangement nearest each line x = const."""
        ring_lines = self.get_nearest_lines(self.ring_centers[:, 0], line_positions)
        bond_lines = self.get_nearest_lines(self.bond_middle_x, line_positions)
        return [self.get_arrangement(ring_lines == line, bond_lines == line) for line in range(len(line_positions))]


class RingsMaterialAnalyzer(BaseMaterialAnalyzer):
    """
    Rings of the top-view bond network of a 2D material: the faces of that periodic planar network, their sizes, and
    the defect rings and homo bonds nearest given lines of the cell. A site is the set of atoms sharing one top-view
    position (MoS2: Mo, and the two S above each other).
    """

    # atoms of one site share x, y up to the rounding of stored coordinates; distinct sites are a bond (> 1 A) apart
    site_tolerance: float = 0.05
    # bonded sites are closer than this times the nearest-site distance: between first (1) and second (1.73) neighbors
    bond_cutoff_factor: float = 1.3

    @cached_property
    def lattice_vectors(self) -> np.ndarray:
        """The in-plane lattice vectors of the material (rows)."""
        return np.array(self.material.lattice.vector_arrays)[:2, :2]

    @cached_property
    def atom_positions(self) -> np.ndarray:
        """The in-plane position of each atom."""
        material = self.material.clone()
        material.to_crystal()
        return (np.array(material.basis.coordinates.values)[:, :2]) @ self.lattice_vectors

    def get_pairs(self, positions: np.ndarray, cutoff: float) -> Bonds:
        """Pairs (i, j, vector from i to an image of j) closer than the cutoff, periodic in the plane of the cell."""
        images = get_in_plane_periodic_images(positions, self.lattice_vectors)
        neighbors = cKDTree(images).query_ball_point(positions, cutoff)
        first = np.repeat(np.arange(len(positions)), [len(indices) for indices in neighbors])
        image_indices = np.concatenate(neighbors).astype(int)
        # the images come in blocks of len(positions), one per cell: the position's own copy is in the central block
        keep = image_indices != CENTRAL_IMAGE_INDEX * len(positions) + first
        first, image_indices = first[keep], image_indices[keep]
        return first, image_indices % len(positions), images[image_indices] - positions[first]

    @cached_property
    def atom_site_indices(self) -> np.ndarray:
        """The top-view site of each atom: atoms above one another share one."""
        first, second, _ = self.get_pairs(self.atom_positions, self.site_tolerance)
        graph = coo_matrix((np.ones(len(first)), (first, second)), shape=(len(self.atom_positions),) * 2)
        return connected_components(graph, directed=False)[1]

    @cached_property
    def site_first_atoms(self) -> np.ndarray:
        """The first atom of each site."""
        return np.unique(self.atom_site_indices, return_index=True)[1]

    @cached_property
    def site_positions(self) -> np.ndarray:
        """The in-plane position of each site."""
        return self.atom_positions[self.site_first_atoms]

    @cached_property
    def site_species(self) -> np.ndarray:
        """The species of each site: that of its first atom."""
        return np.array(self.material.basis.elements.values)[self.site_first_atoms]

    @cached_property
    def bonds(self) -> Bonds:
        """Directed bonds (site, neighbor site, vector), grouped by site in counterclockwise order."""
        images = get_in_plane_periodic_images(self.site_positions, self.lattice_vectors)
        cutoff = self.bond_cutoff_factor * np.median(cKDTree(images).query(self.site_positions, k=2)[0][:, 1])
        first, second, vectors = self.get_pairs(self.site_positions, cutoff)
        order = np.lexsort((np.arctan2(vectors[:, 1], vectors[:, 0]), first))
        return first[order], second[order], vectors[order]

    @cached_property
    def reverse_bonds(self) -> np.ndarray:
        """The same bond in the other direction: the one between the same sites whose periodic image is the opposite."""
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
        """The number of sites around each ring."""
        return np.array([len(ring) for ring in self.rings])

    @cached_property
    def ring_of_bond(self) -> np.ndarray:
        """The ring each directed bond belongs to, walking around that ring."""
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

    @cached_property
    def rings_and_bonds(self) -> RingsAndBonds:
        """The rings and bonds of the network, as RingsAndBonds reads them by line."""
        first, second, vectors = self.bonds
        return RingsAndBonds(
            ring_centers=self.ring_centers,
            ring_sizes=self.ring_sizes,
            ring_pairs=np.column_stack([self.ring_of_bond, self.ring_of_bond[self.reverse_bonds]]),
            bond_middle_x=self.site_positions[first, 0] + vectors[:, 0] / 2,
            bond_species=self.site_species[np.column_stack([first, second])],
            cell=np.diag(self.lattice_vectors),
        )

    def get_line_arrangements(self, line_positions: List[float]) -> List[RingsArrangement]:
        """Arrangement nearest each line x = const of a rectangular cell whose first lattice vector lies along x."""
        return self.rings_and_bonds.get_line_arrangements(line_positions)
