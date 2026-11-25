from typing import Union, TypeVar

from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum

from .builder import IslandDefectBuilder
from .configuration import IslandDefectConfiguration
from .....analyze.slab import SlabMaterialAnalyzer
from .....build_components import MaterialWithBuildMetadata
from .....build_components.entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.builder import SlabBuilder
from .....build_components.entities.reusable.two_dimensional.slab_stack.helpers import (
    recreate_slab_with_fractional_layers,
)
from .....build_components.entities.reusable.zero_dimensional.coordinates_shape_enum import CoordinatesShapeEnum
from .....entities.coordinate import (
    CoordinateCondition,
    CylinderCoordinateCondition,
    SphereCoordinateCondition,
    BoxCoordinateCondition,
    TriangularPrismCoordinateCondition,
    PlaneCoordinateCondition,
)
from .....modify import filter_by_condition_on_coordinates

CoordinateConditionType = TypeVar("CoordinateConditionType", bound=CoordinateCondition)


def create_defect_island(
    slab: MaterialWithBuildMetadata,
    condition: Union[
        CylinderCoordinateCondition,
        SphereCoordinateCondition,
        BoxCoordinateCondition,
        TriangularPrismCoordinateCondition,
        PlaneCoordinateCondition,
        CoordinateConditionType,
    ] = CylinderCoordinateCondition(),
    use_cartesian_coordinates: bool = True,
    number_of_added_layers: Union[int, float] = 1,
) -> MaterialWithBuildMetadata:
    """
    Create an island defect using the new IslandDefectConfiguration and IslandDefectBuilder.

    Args:
        slab: The slab material.
        condition: The coordinate condition that defines the island shape.
        number_of_added_layers: Number of additional layers to add to the slab, from which the island will be created.

    Returns:
        Material: The slab with island defect.
    """

    material_with_additional_layers = recreate_slab_with_fractional_layers(slab, number_of_added_layers)

    isolated_island = filter_by_condition_on_coordinates(
        material=material_with_additional_layers,
        condition=condition.condition,
        use_cartesian_coordinates=use_cartesian_coordinates,
    )

    # Create the island defect using IslandDefectBuilder
    analyzer = SlabMaterialAnalyzer(material=slab)
    slab_without_vacuum_configuration = analyzer.slab_configuration_with_no_vacuum
    slab_build_parameters = analyzer.build_parameters

    new_slab = SlabBuilder(build_parameters=slab_build_parameters).get_material(slab_without_vacuum_configuration)

    original_vacuum_config = analyzer.get_slab_vacuum_configuration()
    vacuum_config = VacuumConfiguration(
        size=original_vacuum_config.size, crystal=new_slab, direction=original_vacuum_config.direction
    )

    island_config = IslandDefectConfiguration(
        stack_components=[new_slab, isolated_island, vacuum_config], direction=AxisEnum.z
    )

    island_builder = IslandDefectBuilder()
    return island_builder.get_material(island_config)


def get_coordinate_condition(shape: CoordinatesShapeEnum, dict_params: dict):
    """
    Returns the appropriate coordinate condition based on the shape provided.

    Args:
        shape (CoordinatesShapeEnum): Shape of the island (e.g., cylinder, box, etc.).
        dict_params (dict): Parameters for the shape condition.

    Returns:
        CoordinateCondition: The appropriate condition object.
    """
    if shape == "cylinder":
        return CylinderCoordinateCondition(
            center_position=dict_params.get("center_position", [0.5, 0.5]),
            radius=dict_params["radius"],
            min_z=dict_params["min_z"],
            max_z=dict_params["max_z"],
        )
    elif shape == "sphere":
        return SphereCoordinateCondition(
            center_coordinate=dict_params.get("center_coordinate", [0.5, 0.5, 0.5]), radius=dict_params["radius"]
        )
    elif shape == "box":
        return BoxCoordinateCondition(
            min_coordinate=dict_params["min_coordinate"], max_coordinate=dict_params["max_coordinate"]
        )
    elif shape == "triangular_prism":
        return TriangularPrismCoordinateCondition(
            position_on_surface_1=dict_params["position_on_surface_1"],
            position_on_surface_2=dict_params["position_on_surface_2"],
            position_on_surface_3=dict_params["position_on_surface_3"],
            min_z=dict_params["min_z"],
            max_z=dict_params["max_z"],
        )
    else:
        raise ValueError(f"Unsupported island shape: {shape}")
