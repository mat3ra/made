from typing import Optional, Union

from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum
from mat3ra.esse.models.materials_category_components.entities.core.two_dimensional.vacuum import (
    VacuumConfigurationSchema,
)
from mat3ra.made.material import Material
from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseConfigurationPydantic

from ..... import MaterialWithBuildMetadata


class VacuumConfiguration(VacuumConfigurationSchema, BaseConfigurationPydantic):
    type: str = "VacuumConfiguration"
    size: float = VacuumConfigurationSchema.model_fields["size"].default
    crystal: Union[Material, MaterialWithBuildMetadata, None] = None
    direction: Optional[AxisEnum] = AxisEnum.z
