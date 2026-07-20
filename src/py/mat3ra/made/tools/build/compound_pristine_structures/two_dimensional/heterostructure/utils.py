from typing import List

import numpy as np
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)

from .types import StackComponentDict
from mat3ra.made.utils import adjust_material_cell_to_set_gap_along_direction
from ....pristine_structures.two_dimensional.slab.helpers import create_slab
from ....pristine_structures.two_dimensional.slab_strained_supercell.builder import SlabStrainedSupercellBuilder
from ....pristine_structures.two_dimensional.slab_strained_supercell.configuration import (
    SlabStrainedSupercellConfiguration,
)
from .....analyze.interface import InterfaceAnalyzer
from .....analyze.slab import SlabMaterialAnalyzer
from .....build_components import MaterialWithBuildMetadata
from .....operations.core.binary import stack


def validate_heterostructure_inputs(stack_component_dicts: List[StackComponentDict], gaps: List[float]) -> None:
    """Validate inputs for heterostructure creation."""
    if len(stack_component_dicts) < 2:
        raise ValueError("At least 2 stack components are required for a heterostructure")
    if len(gaps) != len(stack_component_dicts) - 1:
        raise ValueError("Number of gaps must be one less than number of stack components")


def create_initial_slabs(
    stack_component_dicts: List[StackComponentDict], vacuum: float, use_conventional_cell: bool
) -> List[MaterialWithBuildMetadata]:
    """Create initial slabs from stack components."""
    slabs = []
    for i, component in enumerate(stack_component_dicts):
        slab = create_slab(
            crystal=component.crystal,
            miller_indices=component.miller_indices,
            number_of_layers=component.thickness,
            vacuum=0.0 if i < len(stack_component_dicts) - 1 else vacuum,
            use_conventional_cell=use_conventional_cell,
            xy_supercell_matrix=component.xy_supercell_matrix or [[1, 0], [0, 1]],
        )
        slabs.append(slab)
    return slabs


def find_common_supercell_matrix(
    slabs: List[MaterialWithBuildMetadata], optimize_layer_supercells: bool
) -> SupercellMatrix2DSchema:
    """Find common supercell matrix for all materials."""
    reference_substrate = slabs[0]

    for i in range(1, len(slabs)):
        film_slab = slabs[i]

        substrate_analyzer = SlabMaterialAnalyzer(material=reference_substrate)
        film_analyzer = SlabMaterialAnalyzer(material=film_slab)

        analyzer = InterfaceAnalyzer(
            substrate_slab_configuration=substrate_analyzer.build_configuration,
            film_slab_configuration=film_analyzer.build_configuration,
            substrate_build_parameters=substrate_analyzer.build_parameters,
            film_build_parameters=film_analyzer.build_parameters,
            optimize_film_supercell=optimize_layer_supercells,
        )
        analyzer.__dict__["substrate_material"] = reference_substrate
        analyzer.__dict__["film_material"] = film_slab

        return analyzer.film_strained_configuration.xy_supercell_matrix


def create_strained_substrate(
    reference_substrate: MaterialWithBuildMetadata, common_supercell_matrix: SupercellMatrix2DSchema
) -> MaterialWithBuildMetadata:
    """Create strained substrate with common supercell."""
    substrate_analyzer = SlabMaterialAnalyzer(material=reference_substrate)

    substrate_config = SlabStrainedSupercellConfiguration(
        **substrate_analyzer.build_configuration.model_dump(),
        strain_matrix=Matrix3x3Schema(root=np.eye(3).tolist()),
        xy_supercell_matrix=common_supercell_matrix,
    )

    builder = SlabStrainedSupercellBuilder()
    return builder.get_material(substrate_config)


def create_strained_films(
    slabs: List[MaterialWithBuildMetadata],
    common_supercell_matrix: SupercellMatrix2DSchema,
    optimize_layer_supercells: bool,
) -> List[MaterialWithBuildMetadata]:
    """Create strained films with common supercell."""
    reference_substrate = slabs[0]
    strained_films = []
    builder = SlabStrainedSupercellBuilder()

    for i in range(1, len(slabs)):
        film_slab = slabs[i]

        substrate_analyzer = SlabMaterialAnalyzer(material=reference_substrate)
        film_analyzer = SlabMaterialAnalyzer(material=film_slab)

        analyzer = InterfaceAnalyzer(
            substrate_slab_configuration=substrate_analyzer.build_configuration,
            film_slab_configuration=film_analyzer.build_configuration,
            substrate_build_parameters=substrate_analyzer.build_parameters,
            film_build_parameters=film_analyzer.build_parameters,
            optimize_film_supercell=optimize_layer_supercells,
        )
        analyzer.__dict__["substrate_material"] = reference_substrate
        analyzer.__dict__["film_material"] = film_slab

        film_config = analyzer.film_strained_configuration
        film_config_dict = film_config.model_dump()
        film_config_dict["xy_supercell_matrix"] = common_supercell_matrix
        film_config_common = SlabStrainedSupercellConfiguration(**film_config_dict)

        strained_film = builder.get_material(film_config_common)
        strained_films.append(strained_film)

    return strained_films


def apply_gaps_and_stack(
    strained_slabs: List[MaterialWithBuildMetadata], gaps: List[float]
) -> MaterialWithBuildMetadata:
    """Apply gaps and stack materials."""
    stacked_materials = []
    for i, slab in enumerate(strained_slabs):
        if i < len(gaps):
            slab_with_gap = adjust_material_cell_to_set_gap_along_direction(slab, gaps[i], AxisEnum.z)
            stacked_materials.append(slab_with_gap)
        else:
            stacked_materials.append(slab)

    return stack(stacked_materials, AxisEnum.z)
