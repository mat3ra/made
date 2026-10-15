from collections import Counter
from functools import cached_property
from typing import List, Optional, Tuple

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.esse.models.materials_category.defective_structures.one_dimensional.grain_boundary_linear.configuration import (  # noqa: E501
    GrainBoundaryCoreEnum,
)
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)
from mat3ra.made.material import Material
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from pydantic import model_validator

from ...build.defective_structures.one_dimensional.grain_boundary_linear.reconstruction import (
    GrainBoundaryCoreReconstruction,
)
from ...build.pristine_structures.two_dimensional.slab_strained_supercell.configuration import (
    SlabStrainedSupercellConfiguration,
)
from ..rings import RingsArrangement, RingsMaterialAnalyzer
from .simple import InterfaceAnalyzer
from .utils.holders import MatchedSubstrateFilmConfigurationHolder
from .zsl import ZSLInterfaceAnalyzer


class GrainBoundaryPlanarMatchHolder(InMemoryEntityPydantic):
    match_id: int
    substrate_transformation_matrix: SupercellMatrix2DSchema
    film_transformation_matrix: SupercellMatrix2DSchema
    match_area: float
    strain_transformation_matrix: Matrix3x3Schema
    total_strain_percentage: float


class GrainBoundaryPlanarAnalyzer(ZSLInterfaceAnalyzer):
    """
    Analyzer for creating grain boundaries between two orientations of the same material.

    Uses ZSL to find matching supercells between two phases with different
    orientations, then stacks them in x/y direction to create a grain boundary configuration.
    """

    phase_1_material: Material
    phase_2_material: Material
    phase_1_miller_indices: Tuple[int, int, int]
    phase_2_miller_indices: Tuple[int, int, int]
    phase_1_thickness: int = 1
    phase_2_thickness: int = 1

    @model_validator(mode="before")
    @classmethod
    def _setup_slab_configurations(cls, values):
        # we need to create slab configurations for both phases for InterfaceAnalyzer to use
        values["substrate_slab_configuration"] = SlabConfiguration.from_parameters(
            material_or_dict=values["phase_1_material"],
            miller_indices=values["phase_1_miller_indices"],
            number_of_layers=values.get("phase_1_thickness", 1),
            vacuum=0.0,
        )
        values["film_slab_configuration"] = SlabConfiguration.from_parameters(
            material_or_dict=values["phase_2_material"],
            miller_indices=values["phase_2_miller_indices"],
            number_of_layers=values.get("phase_2_thickness", 1),
            vacuum=0.0,
        )
        return values

    @property
    def grain_boundary_match_holders(self) -> List[GrainBoundaryPlanarMatchHolder]:
        zsl_matches = self.zsl_match_holders
        match_holders = []

        for idx, zsl_match in enumerate(zsl_matches):
            match_holder = GrainBoundaryPlanarMatchHolder(
                match_id=idx,
                substrate_transformation_matrix=zsl_match.substrate_supercell_matrix,
                film_transformation_matrix=zsl_match.film_supercell_matrix,
                match_area=zsl_match.match_area,
                strain_transformation_matrix=zsl_match.strain_transformation_matrix,
                total_strain_percentage=zsl_match.total_strain_percentage,
            )
            match_holders.append(match_holder)

        return match_holders

    def get_grain_boundary_configuration_by_match_id(self, match_id: int) -> MatchedSubstrateFilmConfigurationHolder:
        return self.get_strained_configuration_by_match_id(match_id)

    def get_grain_boundary_configurations(self) -> List[MatchedSubstrateFilmConfigurationHolder]:
        return self.get_strained_configurations()


class GrainBoundaryLinearAnalyzer(InterfaceAnalyzer):
    """
    Matches two grains of one 2D material along a boundary line. Each grain is the rectangular supercell
    [across, boundary vector], across being the shortest lattice vector perpendicular to the boundary vector, repeated
    `number_of_periods_across` times. The boundary vectors, in the lattice vectors of the slab, are given or found as
    the shortest pair of equal length rotated by `target_angle` from the first to the second.

    With a `core` (honeycomb lattices only), `get_slide` chooses the slide of grain 2 along the line.
    """

    boundary_vectors: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    target_angle: float = 0.0
    angle_tolerance: float = 0.1
    number_of_periods_across: int = 1
    core: Optional[GrainBoundaryCoreEnum] = None
    number_of_slides: int = 24
    maximum_vector_component: int = 30

    @model_validator(mode="after")
    def _validate_core_lattice(self):
        if self.core is not None and not self.honeycomb:
            raise ValueError(
                f"Core {self.core.value} needs a honeycomb lattice: |a| = |b|, gamma 60 or 120 degrees, "
                "two sites in top view"
            )
        return self

    @cached_property
    def honeycomb(self) -> bool:
        lattice = self.substrate_material.lattice
        sites = RingsMaterialAnalyzer(material=self.substrate_material)
        return bool(
            np.isclose(lattice.a, lattice.b, rtol=1e-3)
            and min(abs(lattice.gamma - 60), abs(lattice.gamma - 120)) < 0.5
            and len(sites.site_positions) == 2
        )

    @cached_property
    def lattice_vectors(self) -> np.ndarray:
        return np.array(self.substrate_material.lattice.vector_arrays)[:2, :2]

    @cached_property
    def integer_vectors(self) -> np.ndarray:
        values = np.arange(-self.maximum_vector_component, self.maximum_vector_component + 1)
        vectors = np.stack(np.meshgrid(values, values, indexing="ij"), axis=-1).reshape(-1, 2)
        cartesian = vectors @ self.lattice_vectors
        directions = np.arctan2(cartesian[:, 1], cartesian[:, 0]) % (2 * np.pi)
        vectors = vectors[np.lexsort((directions, np.round(np.linalg.norm(cartesian, axis=1), 6)))]
        return vectors[np.any(vectors != 0, axis=1)]

    def get_rotation_angles(self, vector: np.ndarray, others: np.ndarray) -> np.ndarray:
        start, ends = vector @ self.lattice_vectors, others @ self.lattice_vectors
        return np.degrees(np.arctan2(start[0] * ends[:, 1] - start[1] * ends[:, 0], ends @ start))

    @cached_property
    def matched_boundary_vectors(self) -> np.ndarray:
        if self.boundary_vectors is not None:
            return np.array(self.boundary_vectors)
        lengths = np.linalg.norm(self.integer_vectors @ self.lattice_vectors, axis=1)
        for vector, length in zip(self.integer_vectors, lengths):
            candidates = self.integer_vectors[np.isclose(lengths, length, rtol=1e-3)]
            deviations = np.abs((self.get_rotation_angles(vector, candidates) - self.target_angle + 180) % 360 - 180)
            if deviations.min() < self.angle_tolerance:
                return np.array([vector, candidates[np.argmin(deviations)]])
        raise ValueError(f"No boundary vectors of equal length rotated by {self.target_angle} degrees")

    @cached_property
    def actual_angle(self) -> float:
        first, second = self.matched_boundary_vectors
        return float(self.get_rotation_angles(first, second[None])[0] % 360)

    def get_across_vector(self, boundary_vector: np.ndarray) -> np.ndarray:
        """Shortest lattice vector perpendicular to the boundary vector, the pair right-handed."""
        cartesian = self.integer_vectors @ self.lattice_vectors
        boundary = boundary_vector @ self.lattice_vectors
        cosines = cartesian @ boundary / np.linalg.norm(cartesian, axis=1) / np.linalg.norm(boundary)
        determinants = self.integer_vectors[:, 0] * boundary_vector[1] - self.integer_vectors[:, 1] * boundary_vector[0]
        return self.integer_vectors[(np.abs(cosines) < 1e-5) & (determinants > 0)][0]

    @cached_property
    def supercell_matrices(self) -> List[List[List[int]]]:
        return [
            [(self.number_of_periods_across * self.get_across_vector(vector)).tolist(), vector.tolist()]
            for vector in self.matched_boundary_vectors
        ]

    @cached_property
    def grain_configurations(self) -> List[SlabStrainedSupercellConfiguration]:
        return [
            self.get_component_strained_configuration(
                self.substrate_slab_configuration, self._no_strain_matrix, SupercellMatrix2DSchema(root=matrix)
            )
            for matrix in self.supercell_matrices
        ]

    def get_slide(self, material: Material) -> float:
        """
        Slide of grain 2 along the line, for the two grains stacked without a gap or slide: of `number_of_slides`
        slides across the period, the one whose unrelaxed ring network has `core` at both lines and as many sites of
        each species, with the fewest rings other than hexagons, then the fewest homo bonds.
        """
        reconstruction = GrainBoundaryCoreReconstruction(material=material, supercell_matrices=self.supercell_matrices)
        slides = (np.arange(self.number_of_slides) + 0.5) * reconstruction.cell[1] / self.number_of_slides
        analyzers = [reconstruction.get_rings_analyzer(slide) for slide in slides]
        arrangements = [analyzer.get_line_arrangements(reconstruction.line_positions) for analyzer in analyzers]
        balanced_slides = [len(set(Counter(analyzer.site_species.tolist()).values())) == 1 for analyzer in analyzers]
        ranked_slides = [(self.get_rank(pair, self.core), slide) for pair, slide in zip(arrangements, slides)]
        valid_slides = [
            (rank, slide) for (rank, slide), balanced in zip(ranked_slides, balanced_slides) if rank and balanced
        ]
        if not valid_slides:
            achievable = [
                core.value for core in GrainBoundaryCoreEnum if any(self.get_rank(pair, core) for pair in arrangements)
            ]
            raise ValueError(f"No slide gives the requested core at both boundaries; achievable: {achievable}")
        return float(min(valid_slides)[1])

    @staticmethod
    def get_rank(arrangements: List[RingsArrangement], core: GrainBoundaryCoreEnum) -> Optional[Tuple[int, int]]:
        """
        (rings other than hexagons, homo bonds) if both lines hold only the rings of `core`, each beside its partner,
        in one arrangement; None otherwise.
        """
        core_ring_sizes = [int(size) for size in core.value.split("|")]
        first, second = arrangements
        if first.sequence != second.sequence or any(
            sorted(arrangement.ring_sizes) != core_ring_sizes or arrangement.rings_without_core_partner
            for arrangement in arrangements
        ):
            return None
        return (
            sum(sum(arrangement.ring_sizes.values()) for arrangement in arrangements),
            sum(sum(arrangement.homo_bonds.values()) for arrangement in arrangements),
        )
