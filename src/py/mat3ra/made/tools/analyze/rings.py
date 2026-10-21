"""Rings and homo bonds of the top-view bond network of a 2D material in a rectangular cell, read per boundary line."""

from collections import Counter
from typing import Dict, List, Tuple

import numpy as np
from scipy.spatial import cKDTree

from . import BaseMaterialAnalyzer

# the ring of a perfect honeycomb; a ring of any other size is a defect ring
HEXAGON_SIZE = 6
# every site of a honeycomb network, perfect or rebuilt, has three bonds
BONDS_PER_SITE = 3
# points closer than this are one: atoms of a top-view site (MoS2's sulfur pair) share x, y; sites are over 1 A apart
SAME_SITE_DISTANCE = 0.01  # angstrom
# the cell and its eight neighbours, the cell itself first
IMAGE_SHIFTS = [(0, 0)] + [(first, second) for first in (-1, 0, 1) for second in (-1, 0, 1) if first or second]

# a bond: the site, the bonded site, and the cell shift of the bonded site's copy it reaches
Bond = Tuple[int, int, Tuple[int, int]]
# a ring: its size and centre
Ring = Tuple[int, np.ndarray]
# per line, with their counts: defect ring sizes, homo bonds by element, edges shared by two defect rings by their sizes
LineCounts = Tuple[Counter, Counter, Counter]


def get_periodic_images(positions: np.ndarray, cell_size: np.ndarray) -> np.ndarray:
    """Positions in the rectangular cell and in its eight neighbours, the cell's own first."""
    return np.concatenate([positions + np.multiply(shift, cell_size) for shift in IMAGE_SHIFTS])


def get_nearest_bonds(positions: np.ndarray, cell_size: np.ndarray) -> List[Bond]:
    """Bonds of each site to its three nearest sites, listed once in each direction."""
    count = len(positions)
    _, nearest = cKDTree(get_periodic_images(positions, cell_size)).query(positions, k=BONDS_PER_SITE + 1)
    bonds = {
        (site, int(image) % count, IMAGE_SHIFTS[int(image) // count])
        for site, row in enumerate(nearest)
        for image in row[1:]
    }
    return sorted(bonds | {(second, first, (-shift[0], -shift[1])) for first, second, shift in bonds})


def get_bond_vector(positions: np.ndarray, cell_size: np.ndarray, bond: Bond) -> np.ndarray:
    """Vector from a bond's site to the copy of the bonded site it reaches."""
    first, second, shift = bond
    return positions[second] + np.multiply(shift, cell_size) - positions[first]


def get_next_bonds(positions: np.ndarray, cell_size: np.ndarray, bonds: List[Bond]) -> dict:
    """The bond after each one around its ring: at the bonded site, the next clockwise from the way back."""
    around: Dict[int, List[Bond]] = {bond[0]: [] for bond in bonds}
    for bond in sorted(bonds, key=lambda bond: np.arctan2(*get_bond_vector(positions, cell_size, bond)[::-1])):
        around[bond[0]].append(bond)
    next_bonds = {}
    for first, second, shift in bonds:
        back = around[second].index((second, first, (-shift[0], -shift[1])))
        next_bonds[(first, second, shift)] = around[second][back - 1]
    return next_bonds


def get_rings(positions: np.ndarray, cell_size: np.ndarray, bonds: List[Bond]) -> Tuple[List[Ring], Dict[Bond, int]]:
    """Size and centre of each ring of the periodic planar network, walked with it on the left, and each bond's ring."""
    next_bonds = get_next_bonds(positions, cell_size, bonds)
    ring_of_bond: Dict[Bond, int] = {}
    rings: List[Ring] = []
    for start in bonds:
        corners, bond = [positions[start[0]]], start
        while bond not in ring_of_bond:
            ring_of_bond[bond] = len(rings)
            corners.append(corners[-1] + get_bond_vector(positions, cell_size, bond))
            bond = next_bonds[bond]
        rings += [(len(corners) - 1, np.mean(corners[1:], axis=0))] if len(corners) > 1 else []
    return rings, ring_of_bond


def get_nearest_line(x: float, line_positions: List[float], width: float) -> int:
    """The line x = const nearest to x in a cell periodic over the width."""
    return int(np.argmin([abs((x - line + width / 2) % width - width / 2) for line in line_positions]))


def get_defect_rings_by_line(rings: List[Ring], cell_size: np.ndarray, line_positions: List[float]) -> List[Counter]:
    """Sizes of the defect rings nearest each line x = const, with their counts."""
    defect_rings: List[Counter] = [Counter() for _ in line_positions]
    for size, center in rings:
        if size != HEXAGON_SIZE:
            defect_rings[get_nearest_line(center[0], line_positions, cell_size[0])][size] += 1
    return defect_rings


def get_defect_pairs_by_line(
    rings: List[Ring], ring_of_bond: Dict[Bond, int], cell_size: np.ndarray, line_positions: List[float]
) -> List[Counter]:
    """Edges shared by two defect rings nearest each line x = const, counted by the two rings' sizes."""
    pairs: List[Counter] = [Counter() for _ in line_positions]
    for (first, second, shift), ring in ring_of_bond.items():
        other_ring = ring_of_bond[(second, first, (-shift[0], -shift[1]))]
        sizes = tuple(sorted((rings[ring][0], rings[other_ring][0])))
        if ring < other_ring and HEXAGON_SIZE not in sizes:
            pairs[get_nearest_line(rings[ring][1][0], line_positions, cell_size[0])][sizes] += 1
    return pairs


def get_homo_bonds_by_line(
    positions: np.ndarray, elements: List[str], bonds: List[Bond], cell_size: np.ndarray, line_positions: List[float]
) -> List[Counter]:
    """Bonds between sites of one element nearest each line x = const, counted by element; none if one element."""
    homo_bonds: List[Counter] = [Counter() for _ in line_positions]
    for first, second, shift in bonds:
        # each bond is listed in both directions: counted once, from the listing that sorts first
        is_counted = (first, second, shift) < (second, first, (-shift[0], -shift[1])) and len(set(elements)) > 1
        if is_counted and elements[first] == elements[second]:
            middle = positions[first][0] + get_bond_vector(positions, cell_size, (first, second, shift))[0] / 2
            homo_bonds[get_nearest_line(middle, line_positions, cell_size[0])][elements[first]] += 1
    return homo_bonds


def get_line_counts(
    positions: np.ndarray, elements: List[str], bonds: List[Bond], cell_size: np.ndarray, line_positions: List[float]
) -> List[LineCounts]:
    """Defect ring sizes, homo bonds by element, and edges shared by defect rings, nearest each line x = const."""
    rings, ring_of_bond = get_rings(positions, cell_size, bonds)
    defect_rings = get_defect_rings_by_line(rings, cell_size, line_positions)
    homo_bonds = get_homo_bonds_by_line(positions, elements, bonds, cell_size, line_positions)
    defect_pairs = get_defect_pairs_by_line(rings, ring_of_bond, cell_size, line_positions)
    return list(zip(defect_rings, homo_bonds, defect_pairs))


class RingsMaterialAnalyzer(BaseMaterialAnalyzer):
    """Rings and homo bonds of a 2D material whose cell is rectangular, with its first lattice vector along x."""

    def get_sites(self) -> Tuple[np.ndarray, List[str]]:
        """Top-view position and element of each site: atoms sharing x, y are one site, of the first one's element."""
        material = self.material.clone()
        material.to_cartesian()
        positions = np.array(material.basis.coordinates.values)[:, :2]
        repeated = {second for _, second in cKDTree(positions).query_pairs(SAME_SITE_DISTANCE)}
        sites = [index for index in range(len(positions)) if index not in repeated]
        return positions[sites], [material.basis.elements.values[index] for index in sites]

    def get_line_counts(self, line_positions: List[float]) -> List[LineCounts]:
        """Defect ring sizes, homo bonds by element, and edges shared by defect rings, nearest each line x = const."""
        positions, elements = self.get_sites()
        cell_size = np.diag(np.array(self.material.lattice.vector_arrays))[:2]
        return get_line_counts(positions, elements, get_nearest_bonds(positions, cell_size), cell_size, line_positions)
