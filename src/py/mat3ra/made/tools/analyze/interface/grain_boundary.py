from typing import List, Tuple

from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)
from mat3ra.made.material import Material
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from pydantic import model_validator

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
