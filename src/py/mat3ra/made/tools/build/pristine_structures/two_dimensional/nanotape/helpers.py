from typing import Optional, Tuple, Union

from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum

from mat3ra.made.material import Material
from . import NanoTapeConfiguration
from .builders import NanoTapeBuilder, NanoTapeBuilderParameters
from .....build_components import MaterialWithBuildMetadata
from .....build_components.entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from .....build_components.entities.reusable.one_dimensional.crystal_lattice_lines.edge_types import EdgeTypesEnum
from .....build_components.entities.reusable.one_dimensional.crystal_lattice_lines.helpers import (
    create_lattice_lines_config_and_material,
)


def create_nanotape(
    material: Union[Material, MaterialWithBuildMetadata],
    miller_indices_2d: Optional[Tuple[int, int]] = None,
    edge_type: EdgeTypesEnum = EdgeTypesEnum.zigzag,
    width: int = 2,
    length: int = 2,
    vacuum_width: float = 10.0,
    use_rectangular_lattice: bool = True,
    termination_formula: Optional[str] = None,
) -> Material:
    """
    Creates a nanotape material from a monolayer material.

    Args:
        material: The monolayer material to create the nanotape from (assumes vacuum is present).
        miller_indices_2d: The (u,v) Miller indices for the nanotape direction.
        edge_type: Edge type string ("zigzag"/"armchair"). Optional if miller_indices_2d is provided.
        width: The width of the nanotape in number of unit cells.
        length: The length of the nanotape in number of unit cells.
        vacuum_width: The width of the vacuum region in Angstroms (cartesian).
        use_rectangular_lattice: Whether the nanotape is rectangular.
        termination_formula: The termination formula to use for the nanotape (e.g., "Si").

    Returns:
        Material: The generated nanotape material.
    """
    lattice_lines_config = create_lattice_lines_config_and_material(
        material=material,
        miller_indices_2d=miller_indices_2d,
        edge_type=edge_type,
        width=width,
        length=length,
        termination_formula=termination_formula,
    )
    vacuum_config = VacuumConfiguration(
        size=vacuum_width,
        crystal=material,
        direction=AxisEnum.y,
    )
    config = NanoTapeConfiguration(
        stack_components=[lattice_lines_config, vacuum_config],
        direction=AxisEnum.y,
    )
    builder = NanoTapeBuilder(
        build_parameters=NanoTapeBuilderParameters(use_rectangular_lattice=use_rectangular_lattice)
    )
    return builder.get_material(config)
