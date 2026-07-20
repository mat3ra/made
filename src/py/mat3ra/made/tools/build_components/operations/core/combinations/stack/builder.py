from typing import Any, Optional, Type

from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.made.material import Material
from mat3ra.made.utils import adjust_material_cell_to_set_gap_along_direction

from ......build_components import MaterialWithBuildMetadata
from ......operations.core.binary import stack
from .....entities.core.two_dimensional.vacuum.builder import VacuumBuilder
from .....entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from .....entities.reusable.base_builder import BaseSingleBuilder, TypeConfiguration
from .configuration import StackConfiguration


class StackNComponentsBuilder(BaseSingleBuilder):
    _ConfigurationType: Type[StackConfiguration] = StackConfiguration
    _StackComponentTypes = [MaterialWithBuildMetadata, VacuumConfiguration]

    @property
    def stack_component_types_conversion_map(self):
        return {
            VacuumConfiguration: VacuumBuilder,
        }

    @property
    def stack_component_types_conversion_pre_process_map(self):
        return {
            VacuumConfiguration: self.vacuum_configuration_set_crystal,
        }

    def vacuum_configuration_set_crystal(
        self, vacuum_configuration: VacuumConfiguration, stack_configuration: StackConfiguration
    ) -> VacuumConfiguration:
        # NOTE: we assume that the first component in the stack is used to define the vacuum crystal
        vacuum_prototype_crystal = stack_configuration.stack_components[0]
        vacuum_configuration.crystal = self._stack_component_to_material(vacuum_prototype_crystal, stack_configuration)
        return vacuum_configuration

    def _stack_component_to_material(
        self,
        stack_component_configuration_or_material: Any,
        configuration: StackConfiguration,
        stack_component_build_parameters: Any = None,
    ) -> Optional[MaterialWithBuildMetadata]:
        cache = getattr(self, "_stack_component_cache", None)
        cache_key = id(stack_component_configuration_or_material)
        if cache is not None and cache_key in cache:
            return cache[cache_key]

        builder = self.stack_component_types_conversion_map.get(type(stack_component_configuration_or_material))
        pre_process_function = self.stack_component_types_conversion_pre_process_map.get(
            type(stack_component_configuration_or_material), lambda x, y: x
        )
        if builder:
            stack_component_configuration_or_material = pre_process_function(
                stack_component_configuration_or_material, configuration
            )
            result = builder(build_parameters=stack_component_build_parameters).get_material(
                stack_component_configuration_or_material
            )
        else:
            result = stack_component_configuration_or_material

        if cache is not None:
            cache[cache_key] = result
        return result

    def _generate(self, configuration: TypeConfiguration) -> Material:
        self._stack_component_cache: Optional[dict] = {}
        try:
            materials = []
            for index, stack_component_config in enumerate(configuration.stack_components):
                material = self._stack_component_to_material(stack_component_config, configuration)
                gap = configuration.get_gap_by_id(index)
                if gap is not None:
                    material = adjust_material_cell_to_set_gap_along_direction(material, gap, configuration.direction)
                materials.append(material)
            # Filter out None values in case some stack components are V
            materials = [m for m in materials if m is not None]
            stacked_material = stack(materials, configuration.direction or AxisEnum.z)
            return stacked_material
        finally:
            self._stack_component_cache = None
