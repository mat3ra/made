"""
Matching two grains of a honeycomb monolayer along a boundary line, and the core and homo bonds of their ring network
at each candidate slide of the second grain along it.
"""
from functools import cached_property
from math import ceil, gcd
from typing import List, Optional, Tuple

import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)
from pydantic import model_validator

from ...build.defective_structures.one_dimensional.grain_boundary_linear.build_parameters import (
    GrainBoundaryLinearBuilderParameters,
)
from ...build.defective_structures.one_dimensional.grain_boundary_linear.builder import GrainBoundaryLinearBuilder
from ...build.defective_structures.one_dimensional.grain_boundary_linear.configuration import (
    GrainBoundaryLinearConfiguration,
)
from ...build.defective_structures.one_dimensional.grain_boundary_linear.enums import HomoBondsEnum
from ...utils import unwrap
from ..ring_network import RingNetworkAnalyzer
from ..rings import HEXAGON_SIZE, RingsArrangement, RingsMaterialAnalyzer
from ..utils import wrap_to_cell
from .simple import InterfaceAnalyzer

# a grain keeps one row of hexagons, one lattice constant wide, between the rebuilt bands at its two lines
KEPT_RING_ROW_WIDTH = 1.0  # lattice constants
# the turn mapping a honeycomb's lattice onto itself; a binary's elements map onto themselves every second one
LATTICE_SYMMETRY_ANGLE = 60.0  # degrees


class GrainBoundaryLinearMatchHolder(InMemoryEntityPydantic):
    boundary_vectors: List[List[int]]
    actual_angle: float
    period: float


def get_line_core(arrangements: List[RingsArrangement]) -> Optional[List[int]]:
    """
    Ring sizes of the one core that every cluster of defect rings at both lines repeats, [6] for hexagons only, if both
    lines hold the same clusters (the core then keeps a line flat, the sum of n - 6 over the cell being 0); None if not.
    """
    first, second = [arrangement.cores for arrangement in arrangements]
    cores = set()
    for cluster in first:
        sizes, counts = np.unique(cluster, return_counts=True)
        cores.add(tuple(np.repeat(sizes, counts // gcd(*counts)).tolist()))
    if first != second or len(cores) > 1:
        return None
    return list(cores.pop()) if cores else [HEXAGON_SIZE]


def get_arrangement_counts(arrangements: List[RingsArrangement]) -> Tuple[int, int, int]:
    """Defect rings, homo bonds and pairs of defect rings of one size sharing an edge, over the lines."""
    return (
        sum(len(core) for line in arrangements for core in line.cores),
        sum(sum(line.homo_bonds.values()) for line in arrangements),
        sum(line.same_size_pairs for line in arrangements),
    )


def get_across_vector(vector: np.ndarray) -> np.ndarray:
    """The shortest lattice vector perpendicular to (n, m), a quarter turn clockwise from it, in the 60 degree basis."""
    across = np.array([vector[0] + 2 * vector[1], -2 * vector[0] - vector[1]])
    return across // gcd(*across.tolist())


class GrainBoundaryLinearAnalyzer(InterfaceAnalyzer):
    """
    Matches two grains of a honeycomb monolayer along a boundary line and lists the cores and homo bonds of their ring
    network (RingNetworkAnalyzer) at both lines, the second grain as given and rotated by 180 degrees. The matching
    vectors are in the literature's 60 degree basis, (3, 1)|(1, 3) at 32.2 degrees: given, or the shortest pair of
    equal length rotated by `target_angle`. Each grain is the rectangular supercell [across, matching vector], repeated
    `number_of_periods_across` times across, by default the fewest that hold both rebuilt bands.
    """

    boundary_vectors: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    target_angle: float = 0.0
    angle_tolerance: float = 0.1
    number_of_periods_across: Optional[int] = None
    build_parameters: GrainBoundaryLinearBuilderParameters = GrainBoundaryLinearBuilderParameters()
    # search bound for a target angle (the 4.4 degree stress case needs (8, 7))
    maximum_vector_component: int = 30

    @model_validator(mode="after")
    def _validate_honeycomb(self):
        first, second = self.sites.lattice_vectors
        is_hexagonal = np.isclose(first @ first, second @ second) and np.isclose(abs(first @ second), first @ first / 2)
        if not is_hexagonal or len(self.sites.site_positions) != 2:
            raise ValueError("A grain boundary core needs a honeycomb: |a| = |b|, gamma 60 or 120 degrees, two sites")
        return self

    @cached_property
    def sites(self) -> RingsMaterialAnalyzer:
        return RingsMaterialAnalyzer(material=self.substrate_material)

    @cached_property
    def chiral_basis(self) -> np.ndarray:
        """The 60 degree basis in the lattice vectors: a, and b or a + b, whichever is 60 degrees from a."""
        first, second = self.sites.lattice_vectors
        return np.array([[1, 0], [0, 1] if first @ second > 0 else [1, 1]])

    def get_angles(self, vector: np.ndarray, others: np.ndarray) -> np.ndarray:
        """Counterclockwise angle in degrees, in [0, 360), from a vector to each of the others (60 degree basis)."""
        basis = self.chiral_basis @ self.sites.lattice_vectors
        start, ends = vector @ basis, others @ basis
        return np.degrees(np.arctan2(start[0] * ends[:, 1] - start[1] * ends[:, 0], ends @ start)) % 360

    @cached_property
    def matching_vectors(self) -> np.ndarray:
        """The given vectors, or the shortest pair of equal length rotated by the target angle (first by direction)."""
        if self.boundary_vectors is not None:
            return np.array(self.boundary_vectors)
        values = np.arange(-self.maximum_vector_component, self.maximum_vector_component + 1)
        vectors = np.stack(np.meshgrid(values, values, indexing="ij"), axis=-1).reshape(-1, 2)
        vectors = vectors[np.any(vectors != 0, axis=1)]
        lengths = vectors[:, 0] ** 2 + vectors[:, 0] * vectors[:, 1] + vectors[:, 1] ** 2
        order = np.lexsort((self.get_angles(np.array([1, 0]), vectors), lengths))
        for vector, length in zip(vectors[order], lengths[order]):
            candidates = vectors[(lengths == length) & np.any(vectors != vector, axis=1)]
            deviations = np.abs((self.get_angles(vector, candidates) - self.target_angle + 180) % 360 - 180)
            if deviations.min() < self.angle_tolerance:
                return np.array([vector, candidates[np.argmin(deviations)]])
        raise ValueError(f"No two different lattice vectors of equal length are rotated by {self.target_angle} degrees")

    @cached_property
    def match_holder(self) -> GrainBoundaryLinearMatchHolder:
        (first_n, first_m), (second_n, second_m) = self.matching_vectors
        if first_n**2 + first_n * first_m + first_m**2 != second_n**2 + second_n * second_m + second_m**2:
            raise ValueError(f"The matching vectors {self.matching_vectors.tolist()} differ in length")
        vectors = self.matching_vectors @ self.chiral_basis
        return GrainBoundaryLinearMatchHolder(
            boundary_vectors=vectors.tolist(),
            actual_angle=float(self.get_angles(self.matching_vectors[0], self.matching_vectors[1:])[0]),
            period=float(np.linalg.norm(vectors[0] @ self.sites.lattice_vectors)),
        )

    @cached_property
    def periods_across(self) -> int:
        """`number_of_periods_across`; by default the fewest for the narrower grain to hold both bands and a row."""
        lattice_constant = np.linalg.norm(self.sites.lattice_vectors[0])
        width = (2 * self.build_parameters.band_width + KEPT_RING_ROW_WIDTH) * lattice_constant
        across = np.array([get_across_vector(vector) for vector in self.matching_vectors]) @ self.chiral_basis
        minimum = ceil(width / np.linalg.norm(across @ self.sites.lattice_vectors, axis=1).min())
        if self.number_of_periods_across is not None and self.number_of_periods_across < minimum:
            raise ValueError(f"number_of_periods_across must be at least {minimum}")
        return self.number_of_periods_across or minimum

    @cached_property
    def symmetry_angle(self) -> float:
        """The smallest turn mapping the monolayer onto itself: 60 degrees if both sites hold one species, else 120."""
        elements = np.array(self.substrate_material.basis.elements.values)
        site_atoms = [sorted(elements[self.sites.atom_site_indices == site]) for site in (0, 1)]
        return LATTICE_SYMMETRY_ANGLE * (1 if site_atoms[0] == site_atoms[1] else 2)

    def get_stack_configuration(self, rotated: bool) -> Optional[GrainBoundaryLinearConfiguration]:
        """
        The grains stacked, the second as given or rotated by 180 degrees (a binary's elements swapped), with the
        misorientation of their lattices in [0, 60) degrees (the elements' relation is in homo_bonds); None if a turn
        of the monolayer onto itself maps one grain onto the other.
        """
        first, second = self.matching_vectors
        second = -second if rotated else second
        angle = self.match_holder.actual_angle + 180 * rotated
        if np.isclose(wrap_to_cell(angle, self.symmetry_angle), 0.0):
            return None
        actual_angle = float(wrap_to_cell(angle, LATTICE_SYMMETRY_ANGLE))
        components = []
        for vector in (first, second):
            matrix = (np.array([self.periods_across * get_across_vector(vector), vector]) @ self.chiral_basis).tolist()
            components.append(
                self.get_component_strained_configuration(
                    configuration=self.substrate_slab_configuration,
                    strain_matrix=self._no_strain_matrix,
                    xy_supercell_matrix=SupercellMatrix2DSchema(root=matrix),
                )
            )
        return GrainBoundaryLinearConfiguration(
            stack_components=components, gaps=ArrayWithIds.from_values([]), actual_angle=actual_angle
        )

    def get_network_analyzer(self, configuration: GrainBoundaryLinearConfiguration) -> RingNetworkAnalyzer:
        return RingNetworkAnalyzer(
            material=GrainBoundaryLinearBuilder(build_parameters=self.build_parameters).get_material(configuration),
            supercell_matrices=[unwrap(component.xy_supercell_matrix) for component in configuration.stack_components],
            band_width=self.build_parameters.band_width,
        )

    def get_candidate_slides(self, network_analyzer: RingNetworkAnalyzer) -> np.ndarray:
        """
        Slides at which a hexagon centre of the second grain lies level with one of the first (four centres can then lie
        on one circle), and the midpoints between them: such offsets repeat every a^2 / (2 P), lattice dot products
        being multiples of a^2 / 2. The network can change only where centres are level, so one slide per interval
        between them stands for it.
        """
        centers, grains = network_analyzer.hexagon_centers
        period = self.match_holder.period
        step = np.linalg.norm(self.sites.lattice_vectors[0]) ** 2 / (4 * period)
        offset = (centers[grains == 0][0, 1] - centers[grains == 1][0, 1]) % (2 * step)
        return wrap_to_cell(offset + step * np.arange(round(period / step)), period)

    def get_registry(self, network_analyzer: RingNetworkAnalyzer, slide: float) -> float:
        """
        The slide in terms of the two grains alone: how far the second grain's row of hexagon centres nearest its line
        lies along the line from the first grain's, modulo the period over which both rows repeat.
        """
        centers, grains = network_analyzer.hexagon_centers
        first_row_centers = [centers[grains == grain][np.argmin(centers[grains == grain, 0])] for grain in (0, 1)]
        repeats = np.lcm.reduce([gcd(*vector) for vector in self.matching_vectors.tolist()])
        offset = slide + first_row_centers[1][1] - first_row_centers[0][1]
        return float(wrap_to_cell(offset, self.match_holder.period / repeats))

    def get_homo_bonds(self, arrangements: List[RingsArrangement]) -> Optional[str]:
        """
        The homo bonds of a network: "none" without any, "alternating" with as many of every element at both lines, or
        the element whose homo bonds alone are at the first line and none at the second; None otherwise.
        """
        elements = sorted(set(self.sites.site_species))
        counts = np.array(
            [[line.homo_bonds.get(f"{element}-{element}", 0) for element in elements] for line in arrangements]
        )
        if not counts.any():
            return HomoBondsEnum.none.value
        if np.all(counts == counts[0, 0]):
            return HomoBondsEnum.alternating.value
        first_line_elements = np.flatnonzero(counts[0])
        is_rich = len(first_line_elements) == 1 and counts[1, first_line_elements[0]] == 0
        return elements[first_line_elements[0]] if is_rich else None

    def get_ranked_configurations(self, rotated: bool) -> List[Tuple[tuple, GrainBoundaryLinearConfiguration]]:
        """
        A configuration per candidate slide with one core at both lines and a homo-bond label, the second grain as given
        or rotated, with its rank: a unique network first, then the fewest defect rings, homo bonds and pairs of defect
        rings of one size sharing an edge (a core whose ring sizes alternate was the lower in energy in every MACE
        comparison with its paired form), then the registry.
        """
        configuration = self.get_stack_configuration(rotated)
        if configuration is None:
            return []
        network_analyzer = self.get_network_analyzer(configuration)
        ranked: List[Tuple[tuple, GrainBoundaryLinearConfiguration]] = []
        for slide in self.get_candidate_slides(network_analyzer):
            network = network_analyzer.get_network(slide)
            arrangements = network_analyzer.get_line_arrangements(network, slide)
            core_ring_sizes, homo_bonds = get_line_core(arrangements), self.get_homo_bonds(arrangements)
            if core_ring_sizes is None or homo_bonds is None:
                continue
            counts = get_arrangement_counts(arrangements)
            registry = self.get_registry(network_analyzer, slide)
            rank = (network.number_of_ties > 0, *counts, registry)
            update = {"xy_shift": [float(slide), 0.0], "core_ring_sizes": core_ring_sizes, "homo_bonds": homo_bonds}
            ranked.append((rank, configuration.model_copy(update=update)))
        return ranked

    @cached_property
    def configurations(self) -> List[GrainBoundaryLinearConfiguration]:
        """The configurations of both images of the second grain, best ranked first."""
        if self.get_stack_configuration(False) is None and self.get_stack_configuration(True) is None:
            raise ValueError(f"The matching vectors {self.matching_vectors.tolist()} are equivalent to no rotation")
        ranked = self.get_ranked_configurations(False) + self.get_ranked_configurations(True)
        return [configuration for _, configuration in sorted(ranked, key=lambda item: item[0])]
