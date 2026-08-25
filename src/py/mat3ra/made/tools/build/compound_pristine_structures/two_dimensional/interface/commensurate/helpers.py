from typing import List, Optional, Tuple, Union

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum

from mat3ra.made.material import Material
from .. import InterfaceBuilder, InterfaceConfiguration
from ......build_components.entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from .....pristine_structures.two_dimensional.slab_strained_supercell.configuration import (
    SlabStrainedSupercellConfiguration,
)
from ......analyze.interface import CommensurateLatticeInterfaceAnalyzer
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from ......build_components.metadata import MaterialWithBuildMetadata


def get_commensurate_strained_configurations(
    material: Union[Material, MaterialWithBuildMetadata],
    target_angle: float,
    angle_tolerance: float,
    max_repetition_int: Optional[int],
    limit_max_int: int,
    return_first_match: bool,
    miller_indices: Tuple[int, int, int],
    number_of_layers: int,
    vacuum: float,
    match_id: int = 0,
    use_conventional_cell: bool = True,
) -> Tuple[List[SlabStrainedSupercellConfiguration], float]:
    """
    Get strained configurations for commensurate lattice matching.

    This function creates strained configurations for both substrate and film phases
    based on commensurate lattice matching at a specified twist angle.

    Args:
        material (Material): The material to create configurations from.
        target_angle (float): The target twist angle in degrees.
        angle_tolerance (float): Tolerance for matching angles in degrees.
        max_repetition_int (Optional[int]): Maximum integer for supercell matrix elements.
        limit_max_int (int): Limit for maximum integer to search for supercell matrices.
        return_first_match (bool): Whether to return the first match or all matches.
        miller_indices (Tuple[int, int, int]): Miller indices for the slab surface.
        number_of_layers (int): Number of atomic layers in the slab.
        vacuum (float): Size of the vacuum layer in Angstroms.
        match_id (int): ID of the match to use (0 for first match).
        use_conventional_cell (bool): Accepted for signature compatibility but not honored --
            the slab configuration takes the schema default and conventionalizes either way.

    Returns:
        Tuple[List[SlabStrainedSupercellConfiguration], float]:
            List of strained configurations [substrate, film] and the actual angle.

    Raises:
        ValueError: If no commensurate lattice matches are found.
    """
    slab_config = SlabConfiguration.from_parameters(
        material_or_dict=material,
        miller_indices=miller_indices,
        number_of_layers=number_of_layers,
        vacuum=vacuum,
    )

    analyzer = CommensurateLatticeInterfaceAnalyzer(
        substrate_slab_configuration=slab_config,
        target_angle=target_angle,
        angle_tolerance=angle_tolerance,
        max_supercell_matrix_int=max_repetition_int,
        limit_max_int=limit_max_int,
        return_first_match=return_first_match,
    )

    match_holders = analyzer.commensurate_lattice_match_holders
    if not match_holders:
        raise ValueError(f"No commensurate lattice matches found for angle {target_angle}°")

    selected_config = analyzer.get_strained_configuration_by_match_id(match_id)
    actual_angle = match_holders[match_id].actual_angle
    return [selected_config.substrate_configuration, selected_config.film_configuration], actual_angle


def create_interface_commensurate(
    material: Union[Material, MaterialWithBuildMetadata],
    target_angle: float = 0.0,
    angle_tolerance: float = 0.1,
    max_repetition_int: Optional[int] = None,
    limit_max_int: int = 20,
    return_first_match: bool = True,
    direction: AxisEnum = AxisEnum.z,
    gap: float = 3.0,
    miller_indices: Tuple[int, int, int] = (0, 0, 1),
    number_of_layers: int = 1,
    vacuum: float = 0.0,
    match_id: int = 0,
    use_conventional_cell: bool = True,
    remove_overlapping_atoms: bool = True,
    tolerance_for_overlap: float = 1.0,
) -> MaterialWithBuildMetadata:
    """
    Create a commensurate lattice interface (twisted interface) from a material with specified twist angle.

    This function creates a commensurate interface by:
    1. Creating a slab configuration from the material
    2. Finding commensurate lattice matches at the target angle using CommensurateLatticeInterfaceAnalyzer
    3. Creating strained configurations with directional gaps for both phases
    4. Stacking them along the specified direction

    Args:
        material (Material): The material to create the interface from.
        target_angle (float): The target twist angle in degrees.
        angle_tolerance (float): Tolerance for matching angles in degrees.
        max_repetition_int (Optional[int]): Maximum integer for supercell matrix elements.
        limit_max_int (int): Limit for maximum integer to search for supercell matrices.
        return_first_match (bool): Whether to return the first match or all matches.
        direction (AxisEnum): Direction along which to stack components (x, y, or z).
        gap (float): The gap between the two phases in Angstroms.
        miller_indices (Tuple[int, int, int]): Miller indices for the slab surface.
        number_of_layers (int): Number of atomic layers in the slab.
        vacuum (float): Size of the vacuum layer in Angstroms.
        match_id (int): ID of the match to use (0 for first match).
        use_conventional_cell (bool): Accepted for signature compatibility but not honored --
            the slab configuration below takes the schema default, which conventionalizes
            either way. Making it live changes built geometry; see SOF-8034.
        remove_overlapping_atoms (bool): Whether to resolve overlapping atoms in the interface after creation.
        tolerance_for_overlap (float): Tolerance for resolving overlapping atoms, in Angstroms.
    Returns:
        Material: The commensurate interface material.

    Raises:
        ValueError: If no commensurate lattice matches are found.
    """
    strained_configs, _ = get_commensurate_strained_configurations(
        material=material,
        target_angle=target_angle,
        angle_tolerance=angle_tolerance,
        max_repetition_int=max_repetition_int,
        limit_max_int=limit_max_int,
        return_first_match=return_first_match,
        miller_indices=miller_indices,
        number_of_layers=number_of_layers,
        vacuum=vacuum,
        match_id=match_id,
        use_conventional_cell=use_conventional_cell,
    )

    vacuum_config = VacuumConfiguration(size=vacuum, crystal=None, direction=direction)
    interface_config = InterfaceConfiguration(
        stack_components=strained_configs + [vacuum_config],
        gaps=ArrayWithIds.from_values([gap, gap]),
        direction=direction,
    )

    builder = InterfaceBuilder()
    interface = builder.get_material(interface_config)
    if remove_overlapping_atoms:
        interface.basis.resolve_colliding_coordinates(tolerance=tolerance_for_overlap)
    return interface
