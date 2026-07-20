from typing import List, Union

from mat3ra.esse.models.materials_category.defective_structures.three_dimensional.solid_solution.configuration import (
    SolidSolutionConfigurationSchema,
)
from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum
from mat3ra.made.material import Material

from .....build_components import MaterialWithBuildMetadata
from .....build_components.entities.auxiliary.zero_dimensional.point_defect_site.configuration import (
    PointDefectSiteConfiguration,
)
from .....build_components.operations.core.combinations.merge.configuration import MergeConfiguration


class SolidSolutionConfiguration(MergeConfiguration, SolidSolutionConfigurationSchema):
    """Configuration for building a solid solution by merging substitution sites.

    Physical specification: crystal, source_element, target_element, concentrations.
    The merge_components hold the resolved substitution sites.
    """

    type: str = "SolidSolutionConfiguration"
    crystal: Union[Material, MaterialWithBuildMetadata]
    source_element: str
    target_element: str
    target_concentration: float
    actual_concentration: float
    merge_components: List[Union[Material, MaterialWithBuildMetadata, PointDefectSiteConfiguration]]
    merge_method: MergeMethodsEnum = MergeMethodsEnum.REPLACE
