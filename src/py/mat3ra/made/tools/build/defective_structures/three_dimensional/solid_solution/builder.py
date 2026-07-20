from typing import Dict, Type, Union

from mat3ra.made.material import Material

from .....analyze.other import get_chemical_formula_empirical
from .....build_components import MaterialWithBuildMetadata, TypeConfiguration
from .....build_components.entities.auxiliary.zero_dimensional.point_defect_site.builder import PointDefectSiteBuilder
from .....build_components.entities.auxiliary.zero_dimensional.point_defect_site.configuration import (
    PointDefectSiteConfiguration,
)
from .....build_components.operations.core.combinations.merge.builder import MergeBuilder
from .configuration import SolidSolutionConfiguration


class SolidSolutionBuilder(MergeBuilder):
    """Builds a solid solution by merging substitution sites into a supercell."""

    _ConfigurationType: Type[SolidSolutionConfiguration] = SolidSolutionConfiguration

    @property
    def merge_component_types_conversion_map(self) -> Dict[Type, Type]:
        return {
            PointDefectSiteConfiguration: PointDefectSiteBuilder,
        }

    def _update_material_name(
        self, material: Union[Material, MaterialWithBuildMetadata], configuration: TypeConfiguration
    ) -> MaterialWithBuildMetadata:
        formula = get_chemical_formula_empirical(material)
        concentration_percentage = configuration.actual_concentration * 100
        source_element = configuration.source_element
        target_element = configuration.target_element
        material.name = (
            f"{formula} - Solid Solution ({source_element}\u2192{target_element} "
            f"{concentration_percentage:.4g}%)"
        )
        return material
