from typing import Any, Dict, List, Optional, Type

from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum
from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseSingleBuilder, TypeConfiguration

from ......operations.core.binary import merge
from ..... import MaterialWithBuildMetadata
from .....entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from .build_parameters import MergeBuilderParameters
from .configuration import MergeConfiguration


class MergeBuilder(BaseSingleBuilder):
    """
    Builder class for merging materials based on parameters.
    """

    _ConfigurationType: Type[MergeConfiguration] = MergeConfiguration
    _BuildParametersType: Type[MergeBuilderParameters] = MergeBuilderParameters
    _DefaultBuildParameters: MergeBuilderParameters = MergeBuilderParameters()

    @property
    def merge_component_types_conversion_map(self) -> Dict[Type, Type]:
        return {}

    @property
    def merge_component_types_conversion_pre_process_map(self) -> Dict[Type, Any]:
        return {}

    def _merge_component_to_material(
        self,
        merge_component_configuration_or_material: Any,
        configuration: MergeConfiguration,
        merge_component_build_parameters: Any = None,
    ) -> Optional[MaterialWithBuildMetadata]:
        builder = self.merge_component_types_conversion_map.get(type(merge_component_configuration_or_material))
        pre_process_function = self.merge_component_types_conversion_pre_process_map.get(
            type(merge_component_configuration_or_material), lambda x, y: x
        )

        if builder:
            merge_component_configuration_or_material = pre_process_function(
                merge_component_configuration_or_material, configuration
            )
            return builder(build_parameters=merge_component_build_parameters).get_material(
                merge_component_configuration_or_material
            )
        elif isinstance(merge_component_configuration_or_material, VacuumConfiguration):
            raise ValueError("Merge with VacuumConfiguration is not supported by design.")
        else:
            return merge_component_configuration_or_material

    def _merge_by_method(
        self,
        materials: List[MaterialWithBuildMetadata],
        parameters: MergeBuilderParameters,
        method: MergeMethodsEnum = MergeMethodsEnum.ADD,
    ) -> MaterialWithBuildMetadata:
        if method not in MergeMethodsEnum:
            raise ValueError(f"Unknown merge method: {method}")
        return merge(
            materials=materials,
            merge_method=method,
            material_name=parameters.material_name or materials[0].name,
            distance_tolerance=parameters.distance_tolerance,
            merge_dangerously=parameters.merge_dangerously,
        )

    def _generate(self, configuration: TypeConfiguration) -> MaterialWithBuildMetadata:
        materials = []
        for component in configuration.merge_components:
            material = self._merge_component_to_material(component, configuration)
            if material is not None:
                materials.append(material)

        if len(materials) == 0:
            raise ValueError("No valid materials found after processing merge components")

        if len(materials) == 1:
            return materials[0]

        # Optimization: when there are many materials to merge, combine all non-first
        # materials into one before merging with the base to avoid N sequential merges.
        if len(materials) > 2:
            base = materials[0]
            combined = materials[1]
            for m in materials[2:]:
                combined.basis.add_atoms_from_another_basis(m.basis)
            materials = [base, combined]

        parameters = self.build_parameters or self._DefaultBuildParameters
        merge_method = getattr(configuration, "merge_method", None)
        return self._merge_by_method(materials, parameters, merge_method)
