from typing import Optional

from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum
# fmt: off
from mat3ra.esse.models.materials_category.defective_structures.one_dimensional. \
    grain_boundary_linear.configuration import GrainBoundaryLinearConfigurationSchema

# fmt: on
from ....compound_pristine_structures.two_dimensional.interface import InterfaceConfiguration
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration


class GrainBoundaryLinearConfiguration(InterfaceConfiguration, GrainBoundaryLinearConfigurationSchema):
    """
    Configuration for creating a linear grain boundary.

    Args:
        stack_components (: of configuration objects for grain boundary components.
        direction (AxisEnum): Direction along which to stack components (x or y).
    """

    type: str = "GrainBoundaryLinearConfiguration"
    direction: AxisEnum = AxisEnum.x
    actual_angle: Optional[float] = None

    @property
    def phase_1_configuration(self) -> SlabConfiguration:
        return self.stack_components[0]

    @property
    def phase_2_configuration(self) -> SlabConfiguration:
        return self.stack_components[1]

    @property
    def substrate_configuration(self) -> SlabConfiguration:
        return self.phase_1_configuration

    @property
    def film_configuration(self) -> SlabConfiguration:
        return self.phase_2_configuration
