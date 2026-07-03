from typing import List, Optional, Union

from mat3ra.esse.models.materials_category.defective_structures.three_dimensional.solid_solution.configuration import (
    SolidSolutionConfigurationSchema,
)
from mat3ra.esse.models.materials_category_components.entities.core.zero_dimensional.atom import AtomSchema
from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum
from mat3ra.made.material import Material

from .....build_components import MaterialWithBuildMetadata
from .....build_components.entities.auxiliary.zero_dimensional.point_defect_site.configuration import (
    PointDefectSiteConfiguration,
)
from .....build_components.operations.core.combinations.merge.configuration import MergeConfiguration


class SolidSolutionConfiguration(MergeConfiguration, SolidSolutionConfigurationSchema):
    """Configuration for building a solid solution by merging substitution sites.

    Physical specification: crystal, source_element, target_element, concentration.
    The merge_components hold the resolved substitution sites.
    """

    type: str = "SolidSolutionConfiguration"
    crystal: Union[Material, MaterialWithBuildMetadata]
    source_element: str
    target_element: str
    concentration: float
    merge_components: List[Union[Material, MaterialWithBuildMetadata, PointDefectSiteConfiguration]]
    merge_method: MergeMethodsEnum = MergeMethodsEnum.REPLACE

    @classmethod
    def from_parameters(
        cls,
        crystal: Union[Material, MaterialWithBuildMetadata],
        supercell_material: Union[Material, MaterialWithBuildMetadata],
        source_element: str,
        target_element: str,
        concentration: float,
        selected_site_indices: List[int],
        **kwargs,
    ):
        coords = supercell_material.basis.coordinates.values
        site_configs = [
            PointDefectSiteConfiguration(
                crystal=supercell_material,
                coordinate=coords[idx],
                element=AtomSchema(chemical_element=target_element),
            )
            for idx in selected_site_indices
        ]
        return cls(
            crystal=crystal,
            source_element=source_element,
            target_element=target_element,
            concentration=concentration,
            merge_components=[supercell_material] + site_configs,
            merge_method=MergeMethodsEnum.REPLACE,
            **kwargs,
        )
