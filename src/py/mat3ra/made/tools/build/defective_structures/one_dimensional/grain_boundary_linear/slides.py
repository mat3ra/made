"""The slide of the second grain along the line at which both boundary lines have the requested core and homo bonds."""
from collections import Counter
from typing import List, Optional, Tuple

import numpy as np

from .....analyze.rings import HEXAGON_SIZE, LineCounts, get_line_counts
from .network import Monolayer, get_cell_size, get_grains, get_hexagon_centers, get_network


def get_candidate_slides(monolayer: Monolayer, supercell_matrices: list) -> List[float]:
    """Slides midway between those at which hexagon centres of the two grains lie level (four may share a circle)."""
    grains = get_grains(monolayer, supercell_matrices, 0.0)
    centers, center_grains = get_hexagon_centers(monolayer, grains)
    period = grains[0].size[1]
    # centres lie along the line at multiples of a^2 / (2 P): dot products of lattice vectors are multiples of a^2 / 2
    spacing = np.linalg.norm(monolayer.lattice_vectors[0]) ** 2 / (2 * period)
    level = (centers[center_grains.index(0)][1] - centers[center_grains.index(1)][1]) % spacing
    return [level + spacing / 2 + step * spacing for step in range(round(period / spacing))]


def get_slide_line_counts(
    monolayer: Monolayer, supercell_matrices: list, slide: float, core_ring_sizes: List[int]
) -> Optional[List[LineCounts]]:
    """Defect rings and homo bonds at the line x = 0 and between the grains; None if the network is not unique."""
    grains = get_grains(monolayer, supercell_matrices, slide)
    network = get_network(monolayer, grains, core_ring_sizes)
    if network is None:
        return None
    elements = [monolayer.columns[site][0][0] for site in network.sites]
    return get_line_counts(network.positions, elements, network.bonds, get_cell_size(grains), [0.0, grains[0].size[0]])


def matches_core(rings: Counter, core_ring_sizes: List[int]) -> bool:
    """Whether a line's defect rings are the core's, once or repeated along it; none for hexagons only ([6])."""
    defect_sizes = [size for size in core_ring_sizes if size != HEXAGON_SIZE]
    repeats = sum(rings.values()) // max(len(defect_sizes), 1)
    return sorted(rings.elements()) == sorted(defect_sizes * repeats) and (repeats > 0 or not defect_sizes)


def matches_homo_bonds(line_counts: List[LineCounts], homo_bonds: Optional[str], elements: List[str]) -> bool:
    """Whether the lines have the homo bonds asked: any, none, as many of each element's, or one's at the first."""
    first, second = (bonds for _, bonds, _ in line_counts)
    if homo_bonds is None:
        return True
    if homo_bonds == "none":
        return not first and not second
    if homo_bonds == "alternating":
        counts_by_line = [{bonds[element] for element in elements} for bonds in (first, second)]
        return all(len(counts) == 1 and min(counts) > 0 for counts in counts_by_line)
    return set(first) == {homo_bonds} and homo_bonds not in second


def forms_chains(line_counts: List[LineCounts]) -> bool:
    """Whether defect rings share edges at both lines, never two of one size: the 5-7-5-7 chains of Li 2015 Fig. 3f."""
    return all(pairs and all(first != second for first, second in pairs) for _, _, pairs in line_counts)


def get_description(line_counts: List[LineCounts]) -> str:
    """The defect rings and homo bonds of both lines, as "5|5|7|7 {'B': 1, 'N': 1}; ..."."""
    rings_by_line = ["|".join(map(str, sorted(rings.elements()))) or "6" for rings, _, _ in line_counts]
    return "; ".join(f"{rings} {dict(bonds)}" for rings, (_, bonds, _) in zip(rings_by_line, line_counts))


def get_slide(
    monolayer: Monolayer, grain_pairs: List[list], core_ring_sizes: List[int], homo_bonds: Optional[str]
) -> Tuple[list, float]:
    """The grains and slide giving the core and homo bonds asked at both lines, the first forming chains if any does."""
    elements = sorted({column[0][0] for column in monolayer.columns})
    found = []
    for supercell_matrices in grain_pairs:
        for slide in get_candidate_slides(monolayer, supercell_matrices):
            line_counts = get_slide_line_counts(monolayer, supercell_matrices, slide, core_ring_sizes)
            found += [(line_counts, supercell_matrices, slide)] if line_counts is not None else []
    matching = [item for item in found if all(matches_core(rings, core_ring_sizes) for rings, _, _ in item[0])]
    matching = [item for item in matching if matches_homo_bonds(item[0], homo_bonds, elements)]
    if not matching:
        achieved = sorted({get_description(line_counts) for line_counts, _, _ in found})
        raise ValueError(f"No slide gives core {core_ring_sizes} with homo bonds {homo_bonds}; slides give: {achieved}")
    # Li 2015 Fig. 3f: the 5|7 boundaries are continuous 5-7-5-7 chains
    chains = [item for item in matching if forms_chains(item[0])]
    return (chains or matching)[0][1:]
