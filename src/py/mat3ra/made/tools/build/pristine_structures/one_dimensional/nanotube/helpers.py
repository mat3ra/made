from typing import Optional, Tuple, Union

from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum

from mat3ra.made.material import Material
from ...two_dimensional.nanotape import NanoTapeConfiguration
from ...two_dimensional.nanoribbon.configuration import NanoribbonConfiguration
from .....build_components import MaterialWithBuildMetadata
from .....build_components.entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from .....build_components.entities.reusable.one_dimensional.crystal_lattice_lines.edge_types import EdgeTypesEnum
from .....build_components.entities.reusable.one_dimensional.crystal_lattice_lines.helpers import (
    create_lattice_lines_config_and_material,
)
from .builders import NanotubeBuilder
from .build_parameters import NanotubeBuilderParameters
from .configuration import NanotubeConfiguration


def create_nanotube(
    material: Union[Material, MaterialWithBuildMetadata],
    miller_indices_2d: Optional[Tuple[int, int]] = None,
    edge_type: EdgeTypesEnum = EdgeTypesEnum.zigzag,
    width: int = 2,
    length: int = 4,
    vacuum_width: float = 0.0,
    vacuum_length: float = 0.0,
    vacuum_around_tube: float = 10.0,
    termination_formula: Optional[str] = None,
) -> Material:
    """
    Creates a single-walled nanotube from a monolayer material.

    The nanotube is built by first creating a nanoribbon and then folding it into a cylinder:
    the width direction (y) of the nanoribbon becomes the circumference of the tube, and
    the length direction (x) becomes the periodic tube axis.

    Args:
        material: The monolayer material to create the nanotube from (assumes vacuum is present).
        miller_indices_2d: The (u,v) Miller indices for the nanotube chiral direction.
        edge_type: Edge type ("zigzag"/"armchair"). Used if miller_indices_2d is not provided.
        width: The width of the nanoribbon in unit cells (determines the tube circumference).
        length: The length of the nanoribbon in unit cells (determines the tube period).
        vacuum_width: Additional vacuum along the nanoribbon width before rolling (Angstroms).
            Defaults to 0 since the rolling step handles the radial vacuum.
        vacuum_length: Vacuum along the nanoribbon length / tube axis (Angstroms).
            Defaults to 0 for a fully periodic tube.
        vacuum_around_tube: Vacuum around the tube cross-section in the new cell (Angstroms).
        termination_formula: Termination formula for edge atoms (e.g., "H").

    Returns:
        Material: The generated single-walled nanotube material.
    """
    lattice_lines_config = create_lattice_lines_config_and_material(
        material=material,
        miller_indices_2d=miller_indices_2d,
        edge_type=edge_type,
        width=width,
        length=length,
        termination_formula=termination_formula,
    )
    nanotape_vacuum_config = VacuumConfiguration(
        size=vacuum_width,
        direction=AxisEnum.y,
    )
    nanotape_config = NanoTapeConfiguration(
        stack_components=[lattice_lines_config, nanotape_vacuum_config],
        direction=AxisEnum.y,
    )
    nanoribbon_vacuum_config = VacuumConfiguration(
        size=vacuum_length,
        direction=AxisEnum.x,
    )
    nanoribbon_config = NanoribbonConfiguration(
        stack_components=[nanotape_config, nanoribbon_vacuum_config],
        direction=AxisEnum.x,
    )
    config = NanotubeConfiguration(
        nanoribbon=nanoribbon_config,
        vacuum_around_tube=vacuum_around_tube,
    )
    builder = NanotubeBuilder(build_parameters=NanotubeBuilderParameters())
    return builder.get_material(config)
