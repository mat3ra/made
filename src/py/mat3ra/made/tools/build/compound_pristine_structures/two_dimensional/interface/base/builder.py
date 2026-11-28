from typing import Optional, Any, Type, Union, cast

import numpy as np

from mat3ra.made.material import Material
from mat3ra.made.utils import AXIS_TO_INDEX_MAP
from .build_parameters import InterfaceBuilderParameters
from .configuration import InterfaceConfiguration
from .....pristine_structures.two_dimensional.slab_strained_supercell.builder import SlabStrainedSupercellBuilder
from .....pristine_structures.two_dimensional.slab_strained_supercell.configuration import (
    SlabStrainedSupercellConfiguration,
)
from ......analyze import BaseMaterialAnalyzer
from ......analyze.lattice import get_material_with_primitive_lattice
from ......build_components import MaterialWithBuildMetadata
from ......build_components.operations.core.combinations.stack.builder import StackNComponentsBuilder
from ......build_components.operations.core.combinations.stack.configuration import StackConfiguration
from ......convert.interface_parts_enum import InterfacePartsEnum
from ......modify import translate_by_vector, translate_to_center, wrap_to_unit_cell
from ......operations.core.unary import supercell
from ......operations.core.utils import should_skip_stacking


class InterfaceBuilder(StackNComponentsBuilder):
    """
    Creates an interface by straining the film to match the substrate.
    """

    _ConfigurationType: Type[InterfaceConfiguration] = InterfaceConfiguration
    _BuildParametersType: Type[InterfaceBuilderParameters] = InterfaceBuilderParameters
    _DefaultBuildParameters: InterfaceBuilderParameters = InterfaceBuilderParameters()
    _GeneratedItemType: Type[Material] = Material

    @property
    def stack_component_types_conversion_map(self):
        return {
            **super().stack_component_types_conversion_map,
            SlabStrainedSupercellConfiguration: SlabStrainedSupercellBuilder,
        }

    def _generate(self, configuration: InterfaceConfiguration) -> MaterialWithBuildMetadata:
        film_material = self._stack_component_to_material(configuration.film_configuration, configuration)
        substrate_material = self._stack_component_to_material(configuration.substrate_configuration, configuration)

        if film_material:
            film_material.set_labels_from_value(InterfacePartsEnum.FILM.value)
        if substrate_material:
            substrate_material.set_labels_from_value(InterfacePartsEnum.SUBSTRATE.value)

        # Apply xy shift to the film material
        stacking_axis = AXIS_TO_INDEX_MAP[configuration.direction.value]
        other_axes = [i for i in range(3) if i != stacking_axis]
        translation_vector = [0.0, 0.0, 0.0]
        translation_vector[other_axes[0]] = configuration.xy_shift[0]
        translation_vector[other_axes[1]] = configuration.xy_shift[1]
        film_material = translate_by_vector(film_material, translation_vector, use_cartesian_coordinates=True)

        try:
            should_skip_stacking(substrate_material, film_material, stacking_axis)
        except ValueError:
            film_material = supercell(film_material, [[0, 1, 0], [1, 0, 0], [0, 0, 1]])
            print(
                "Switched in-plane lattice vectors of the film material to match substrate"
                + "Direct stacking was not possible."
            )
            should_skip_stacking(substrate_material, film_material, stacking_axis)

        stack_configuration = StackConfiguration(
            stack_components=[substrate_material, film_material, configuration.vacuum_configuration],
            gaps=configuration.gaps,
            direction=configuration.direction,
        )
        interface = super()._generate(stack_configuration)
        wrapped_interface = wrap_to_unit_cell(interface)
        return wrapped_interface

    def _post_process(
        self,
        material: MaterialWithBuildMetadata,
        post_process_parameters: Optional[Any],
        configuration: Optional[InterfaceConfiguration] = None,
    ) -> MaterialWithBuildMetadata:
        build_params = cast(InterfaceBuilderParameters, self.build_parameters)
        if build_params.make_primitive:
            primitive_material = get_material_with_primitive_lattice(
                material, return_original_if_not_reduced=True, keep_orientation=True
            )

            if primitive_material != material:
                if configuration is None:
                    raise ValueError(
                        "Configuration cannot be None when make_primitive is True and material is changed."
                    )
                primitive_material = self._preserve_interface_labels_after_primitive_conversion(
                    original_material=material,
                    primitive_material=primitive_material,
                    axis=configuration.direction.value,
                )

            material = primitive_material

        return super()._post_process(material, post_process_parameters=None, configuration=configuration)

    def get_base_name_from_configuration(self, first_configuration, second_configuration) -> str:
        first_component_formula = BaseMaterialAnalyzer(material=first_configuration.atomic_layers.crystal).formula
        second_component_formula = BaseMaterialAnalyzer(material=second_configuration.atomic_layers.crystal).formula
        first_component_miller = first_configuration.atomic_layers.miller_indices_as_string
        second_component_miller = second_configuration.atomic_layers.miller_indices_as_string
        return f"{first_component_formula}{first_component_miller}-{second_component_formula}{second_component_miller}"

    def get_name_suffix(self, configuration: InterfaceConfiguration) -> str:
        strain = configuration.von_mises_strain_percentage
        if strain == 0:
            return "Interface"
        return f"Interface, Strain {strain:.3f}pct"

    def _update_material_name(
        self, material: Union[Material, MaterialWithBuildMetadata], configuration: InterfaceConfiguration
    ) -> MaterialWithBuildMetadata:
        base_name = self.get_base_name_from_configuration(
            configuration.film_configuration, configuration.substrate_configuration
        )
        name_suffix = self.get_name_suffix(configuration) or self.name_suffix
        name = f"{base_name}, {name_suffix}"
        material.name = name
        return material

    def _preserve_interface_labels_after_primitive_conversion(
        self, original_material: MaterialWithBuildMetadata, primitive_material: MaterialWithBuildMetadata, axis: str
    ) -> MaterialWithBuildMetadata:
        if not original_material.basis.labels.values:
            return primitive_material

        labeled_primitive = primitive_material.clone()
        interface_gap_coordinate = self._find_interface_coordinate_level(original_material, axis)
        primitive_labels = self._assign_labels_by_coordinate_level(labeled_primitive, interface_gap_coordinate, axis)
        labeled_primitive.set_labels_from_list(primitive_labels)
        return labeled_primitive

    def _find_interface_coordinate_level(self, material: MaterialWithBuildMetadata, axis) -> float:
        normalized_material = translate_to_center(material, axes=[axis])
        normalized_material.to_cartesian()
        direction_coords = np.array(normalized_material.coordinates_array)[:, AXIS_TO_INDEX_MAP[axis]]
        labels = material.basis.atomic_labels_array

        substrate_gap_coordinate = direction_coords[np.array(labels) == int(InterfacePartsEnum.SUBSTRATE.value)]
        film_gap_coordinate = direction_coords[np.array(labels) == int(InterfacePartsEnum.FILM.value)]

        if len(substrate_gap_coordinate) == 0 or len(film_gap_coordinate) == 0:
            return (np.min(direction_coords) + np.max(direction_coords)) / 2

        max_substrate_gap_coordinate = np.max(substrate_gap_coordinate)
        min_film_gap_coordinate = np.min(film_gap_coordinate)
        return (max_substrate_gap_coordinate + min_film_gap_coordinate) / 2

    def _assign_labels_by_coordinate_level(
        self, material: MaterialWithBuildMetadata, interface_gap_coordinate: float, axis
    ) -> list:
        normalized_material = translate_to_center(material, axes=[axis])
        normalized_material.to_cartesian()
        direction_coords = np.array(normalized_material.coordinates_array)[:, AXIS_TO_INDEX_MAP[axis]]
        substrate_label = int(InterfacePartsEnum.SUBSTRATE.value)
        film_label = int(InterfacePartsEnum.FILM.value)
        return [substrate_label if z < interface_gap_coordinate else film_label for z in direction_coords]
