from typing import Optional, Union

from mat3ra.esse.models.materials_category.defective_structures.two_dimensional.adatom.configuration import (
    PointDefectSiteSchema,
)
from mat3ra.esse.models.materials_category_components.entities.core.zero_dimensional.atom import AtomSchema
from mat3ra.esse.models.materials_category_components.entities.core.zero_dimensional.vacancy import VacancySchema

from ..crystal_site import CrystalSite


class PointDefectSiteConfiguration(CrystalSite, PointDefectSiteSchema):
    element: Union[VacancySchema, AtomSchema]
    host_atom_label: Optional[int] = None
