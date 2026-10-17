"""The user call: a grain boundary from an angle or matching vectors, with a core and its homo bonds rebuilt."""
from typing import List, Optional, Tuple, Union

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum

from mat3ra.made.material import Material
from .builder import GrainBoundaryLinearBuilder
from .configuration import GrainBoundaryLinearConfiguration
from .enums import HomoBondsEnum
from ....compound_pristine_structures.two_dimensional.interface import get_commensurate_strained_configurations
from ....pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from .....analyze.interface.grain_boundary_linear import GrainBoundaryLinearAnalyzer
from .....analyze.rings import HEXAGON_SIZE
from .....build_components import MaterialWithBuildMetadata


def create_grain_boundary_linear(
    material: Union[Material, MaterialWithBuildMetadata],
    target_angle: float = 0.0,
    angle_tolerance: float = 0.1,
    max_repetition_int: Optional[int] = None,
    limit_max_int: int = 20,
    return_first_match: bool = True,
    direction: AxisEnum = AxisEnum.x,
    gap: float = 3.0,
    miller_indices: Tuple[int, int, int] = (0, 0, 1),
    number_of_layers: int = 1,
    vacuum: float = 0.0,
    use_conventional_cell: bool = True,
    boundary_vectors: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
    core: Optional[str] = None,
    homo_bonds: str = HomoBondsEnum.alternating.value,
    number_of_periods_across: Optional[int] = None,
) -> Material:
    """
    Create a linear grain boundary from a material with specified twist angle.

    This function creates a grain boundary by:
    1. Creating a slab configuration from the material
    2. Finding commensurate lattice matches at the target angle using CommensurateLatticeInterfaceAnalyzer
    3. Creating strained configurations with directional gaps for both phases
    4. Stacking them along the specified direction

    Args:
        material (Material): The material to create the grain boundary from.
        target_angle (float): The target twist angle in degrees.
        angle_tolerance (float): Tolerance for matching angles in degrees.
        max_repetition_int (Optional[int]): Maximum integer for supercell matrix elements.
        limit_max_int (int): Limit for maximum integer to search for supercell matrices.
        return_first_match (bool): Whether to return the first match or all matches.
        direction (AxisEnum): Direction along which to stack components (x or y).
        gap (float): The gap between the two phases in Angstroms.
        miller_indices (Tuple[int, int, int]): Miller indices for the slab surface.
        number_of_layers (int): Number of atomic layers in the slab.
        vacuum (float): Size of the vacuum layer in Angstroms.
        boundary_vectors (Optional[Tuple[Tuple[int, int], Tuple[int, int]]]): With a core, the matching vectors of the
            two grains in the 60 degree basis ((3, 1), (1, 3) is the 32.2 degree boundary); by default found from the
            target angle and tolerance.
        core (Optional[str]): Ring sizes of the core rebuilt along both boundaries of a honeycomb monolayer, "5|7",
            "4|8", "6" for hexagons only, or any sizes whose sum of n - 6 is 0; the arguments from max_repetition_int
            to number_of_layers and use_conventional_cell then do not apply.
        homo_bonds (str): With a core, "alternating" (the grains mirror images with the elements swapped), "none",
            or an element of the material (the first boundary rich in it, the second in the other).
        number_of_periods_across (Optional[int]): With a core, repetitions of each grain across the boundary; by
            default the fewest that hold both rebuilt bands.

    Returns:
        Material: The grain boundary material.

    Raises:
        ValueError: If no commensurate lattice matches are found; with a core, if it is not achievable (the message
            lists what is), or the material, vectors, homo bonds or periods do not allow one.
    """
    if core is not None:
        return create_grain_boundary_linear_with_core(
            material,
            boundary_vectors,
            target_angle,
            angle_tolerance,
            core,
            homo_bonds,
            number_of_periods_across,
            vacuum,
        )
    strained_configs, actual_angle = get_commensurate_strained_configurations(
        material=material,
        target_angle=target_angle,
        angle_tolerance=angle_tolerance,
        max_repetition_int=max_repetition_int,
        limit_max_int=limit_max_int,
        return_first_match=return_first_match,
        miller_indices=miller_indices,
        number_of_layers=number_of_layers,
        vacuum=vacuum,
        use_conventional_cell=use_conventional_cell,
    )

    grain_boundary_config = GrainBoundaryLinearConfiguration(
        stack_components=strained_configs,
        direction=direction,
        gaps=ArrayWithIds.from_values([gap, gap]),
        actual_angle=actual_angle,
    )
    return GrainBoundaryLinearBuilder().get_material(grain_boundary_config)


def get_core_ring_sizes(core: str) -> List[int]:
    """Ring sizes of a core label, "5|7" -> [5, 7]; sizes whose sum of n - 6 is not 0 are a disclination, refused."""
    sizes = sorted(int(size) for size in core.split("|"))
    if sum(size - HEXAGON_SIZE for size in sizes):
        raise ValueError(f"Core {core} is a disclination, which bends the sheet: the sum of n - 6 must be 0")
    return sizes


def create_grain_boundary_linear_with_core(
    material: Union[Material, MaterialWithBuildMetadata],
    boundary_vectors: Optional[Tuple[Tuple[int, int], Tuple[int, int]]],
    target_angle: float,
    angle_tolerance: float,
    core: str,
    homo_bonds: str,
    number_of_periods_across: Optional[int],
    vacuum: float,
) -> MaterialWithBuildMetadata:
    """
    The first ranked configuration of GrainBoundaryLinearAnalyzer with the requested core and homo bonds, the second
    grain rotated by 180 degrees for "alternating" and as given otherwise.
    """
    requested = (get_core_ring_sizes(core), homo_bonds)
    elements = sorted(set(material.basis.elements.values))
    if homo_bonds not in [*HomoBondsEnum, *elements]:
        raise ValueError(f"homo_bonds is alternating, none or an element of the material: {', '.join(elements)}")
    slab = SlabConfiguration.from_parameters(material, (0, 0, 1), 1, vacuum=vacuum)
    analyzer = GrainBoundaryLinearAnalyzer(
        substrate_slab_configuration=slab,
        film_slab_configuration=slab,
        boundary_vectors=boundary_vectors,
        target_angle=target_angle,
        angle_tolerance=angle_tolerance,
        number_of_periods_across=number_of_periods_across,
    )
    for configuration in analyzer.get_configurations(rotated=homo_bonds == HomoBondsEnum.alternating):
        if (configuration.core_ring_sizes, configuration.homo_bonds) == requested:
            return GrainBoundaryLinearBuilder(build_parameters=analyzer.build_parameters).get_material(configuration)
    achievable = {("|".join(map(str, item.core_ring_sizes)), item.homo_bonds) for item in analyzer.configurations}
    raise ValueError(
        f"No slide gives core {core} with homo bonds {homo_bonds} at both boundaries; achievable: {sorted(achievable)}"
    )
