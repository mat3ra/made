from typing import Union

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum

from mat3ra.made.material import Material
from .. import InterfaceBuilder, InterfaceConfiguration
from ......analyze.interface import TwistedNanoribbonsInterfaceAnalyzer
from ......analyze.lattice import get_material_with_conventional_lattice
from ......build_components import MaterialWithBuildMetadata
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration


def create_interface_twisted(
    material1: Union[Material, MaterialWithBuildMetadata],
    material2: Union[Material, MaterialWithBuildMetadata],
    angle: float = 0.0,
    vacuum_x: float = 5.0,
    vacuum_y: float = 5.0,
    gap: float = 3.0,
    use_conventional_cell: bool = False,
) -> MaterialWithBuildMetadata:
    """
    Create a twisted interface between two nanoribbons.

    Args:
        material1 (Material): First nanoribbon material.
        material2 (Material): Second nanoribbon material.
        angle (float): Twist angle in degrees.
        vacuum_x (float): Vacuum along x on both sides, in Angstroms.
        vacuum_y (float): Vacuum along y on both sides, in Angstroms.
        gap (float): Gap between the nanoribbons in Angstroms.

    Returns:
        Material: The twisted interface material.
    """
    if use_conventional_cell:
        material1 = get_material_with_conventional_lattice(material1)
        material2 = get_material_with_conventional_lattice(material2)
    slab1 = SlabConfiguration.from_parameters(
        material_or_dict=material1,
        miller_indices=(0, 0, 1),
        number_of_layers=1,
        vacuum=0.0,
        use_conventional_cell=use_conventional_cell,
    )
    slab2 = SlabConfiguration.from_parameters(
        material_or_dict=material2,
        miller_indices=(0, 0, 1),
        number_of_layers=1,
        vacuum=0.0,
        use_conventional_cell=use_conventional_cell,
    )
    analyzer = TwistedNanoribbonsInterfaceAnalyzer(
        substrate_slab_configuration=slab1,
        film_slab_configuration=slab2,
        angle=angle,
        vacuum_x=vacuum_x,
        vacuum_y=vacuum_y,
    )
    processed_slab1 = analyzer.substrate_nanoribbon_configuration
    processed_slab2 = analyzer.film_nanoribbon_configuration

    configuration = InterfaceConfiguration(
        stack_components=[processed_slab1, processed_slab2],
        gaps=ArrayWithIds.from_values([gap, gap]),
        direction=AxisEnum.z,
    )
    builder = InterfaceBuilder()
    return builder.get_material(configuration)
