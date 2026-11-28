from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum
from sympy import ceiling

from ......analyze.slab import SlabMaterialAnalyzer
from ......build.pristine_structures.two_dimensional.slab.builder import SlabBuilder
from ......build.pristine_structures.two_dimensional.slab.helpers import create_slab
from ......modify import filter_by_box
from ..... import MaterialWithBuildMetadata
from ....core.two_dimensional.vacuum.configuration import VacuumConfiguration
from .builder import SlabStackBuilder
from .configuration import SlabStackConfiguration


def create_slab_stack(
    slab: MaterialWithBuildMetadata, added_component: MaterialWithBuildMetadata
) -> MaterialWithBuildMetadata:
    """
    Create a slab stack by stacking a slab, a slab component, and a vacuum layer.

    Args:
        slab: The original slab material.
        added_component: The material to be stacked on top of the slab.
    Returns:
        Material: The new slab stack material.
    """
    analyzer = SlabMaterialAnalyzer(material=slab)

    slab_without_vacuum_configuration = analyzer.slab_configuration_with_no_vacuum
    slab_build_parameters = analyzer.build_parameters

    new_slab = SlabBuilder(build_parameters=slab_build_parameters).get_material(slab_without_vacuum_configuration)

    original_vacuum_config = analyzer.get_slab_vacuum_configuration()
    vacuum_config = VacuumConfiguration(
        size=original_vacuum_config.size, crystal=new_slab, direction=original_vacuum_config.direction
    )

    slab_stack_config = SlabStackConfiguration(
        stack_components=[new_slab, added_component, vacuum_config], direction=AxisEnum.z
    )

    slab_stack_builder = SlabStackBuilder()
    return slab_stack_builder.get_material(slab_stack_config)


def recreate_slab_with_fractional_layers(
    slab: MaterialWithBuildMetadata, number_of_layers: float
) -> MaterialWithBuildMetadata:
    """
    Create a slab with a specified number of fractional layers.

    Args:
        slab: The original slab material.
        number_of_layers: The total number of layers in the new slab.
    Returns:
        Material: The new slab material with the specified number of layers and vacuum if needed.
    """
    analyzer = SlabMaterialAnalyzer(material=slab)
    slab_without_vacuum = analyzer.slab_configuration_with_no_vacuum
    build_parameters = analyzer.build_parameters

    ceiling_number_of_layers = int(ceiling(number_of_layers))
    slab_with_int_layers_without_vacuum = create_slab(
        crystal=slab_without_vacuum.atomic_layers.crystal,
        miller_indices=slab_without_vacuum.atomic_layers.miller_indices,
        termination_top_formula=slab_without_vacuum.atomic_layers.termination_top.formula
        if slab_without_vacuum.atomic_layers.termination_top
        else None,
        termination_bottom_formula=None,
        number_of_layers=ceiling_number_of_layers,
        vacuum=0,
        xy_supercell_matrix=build_parameters.xy_supercell_matrix,
    )

    max_z_crystal_coordinate = number_of_layers / ceiling_number_of_layers
    return filter_by_box(
        slab_with_int_layers_without_vacuum,
        max_coordinate=[1, 1, max_z_crystal_coordinate],
        reset_ids=True,
    )
