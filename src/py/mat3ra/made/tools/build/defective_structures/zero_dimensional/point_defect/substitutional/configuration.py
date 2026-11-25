from typing import Union, List

from mat3ra.esse.models.materials_category.defective_structures.zero_dimensional.point_defect.substitutional import (
    SubstitutionalPointDefectSchema,
)
from mat3ra.esse.models.materials_category_components.entities.core.zero_dimensional.atom import AtomSchema
from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum

from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.other import get_closest_site_id_from_coordinate
from ..base.configuration import PointDefectConfiguration
from ......build_components import MaterialWithBuildMetadata
from ......build_components.entities.auxiliary.zero_dimensional.point_defect_site.configuration import (
    PointDefectSiteConfiguration,
)


def _host_atom_label_at_coordinate(
    crystal: Union[Material, MaterialWithBuildMetadata], coordinate: List[float]
) -> Union[int, str, None]:
    site_index = get_closest_site_id_from_coordinate(crystal, coordinate)
    return crystal.basis.labels.to_padded_array_of_values(crystal.basis.elements.ids, None)[site_index]


class SubstitutionalDefectConfiguration(PointDefectConfiguration, SubstitutionalPointDefectSchema):
    type: str = "SubstitutionalDefectConfiguration"

    @classmethod
    def from_parameters(
        cls, crystal: Union[Material, MaterialWithBuildMetadata], coordinate: List[float], element: str, **kwargs
    ):
        substitution_site = PointDefectSiteConfiguration(
            crystal=crystal,
            element=AtomSchema(chemical_element=element),
            coordinate=coordinate,
            host_atom_label=_host_atom_label_at_coordinate(crystal, coordinate),
        )
        return cls(merge_components=[crystal, substitution_site], merge_method=MergeMethodsEnum.REPLACE, **kwargs)
