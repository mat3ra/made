from typing import List, Optional, Tuple, Union

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum

from mat3ra.made.material import Material
from .builder import GrainBoundaryLinearBuilder
from .configuration import GrainBoundaryLinearConfiguration
from .matching import LATTICE_SYMMETRY_ANGLE, get_grain_supercell_matrices, get_rotation
from .network import get_monolayer
from .slides import get_slide
from ....compound_pristine_structures.two_dimensional.interface import get_commensurate_strained_configurations
from ....pristine_structures.two_dimensional.slab.builder import SlabBuilder
from ....pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from ....pristine_structures.two_dimensional.slab_strained_supercell.configuration import (
    SlabStrainedSupercellConfiguration,
)
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

    Returns:
        Material: The grain boundary material.

    Raises:
        ValueError: If no commensurate lattice matches are found.
    """
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

    builder = GrainBoundaryLinearBuilder()
    grain_boundary = builder.get_material(grain_boundary_config)

    return grain_boundary


def get_core_ring_sizes(core: str) -> List[int]:
    """Ring sizes of a core, "5|7" -> [5, 7]; sizes whose sum of n - 6 is not 0 make a disclination, refused."""
    ring_sizes = sorted(int(size) for size in core.split("|"))
    if sum(size - HEXAGON_SIZE for size in ring_sizes):
        raise ValueError(f"Core {core} is a disclination, which bends the sheet: the sum of n - 6 must be 0")
    return ring_sizes


def create_grain_boundary_linear_with_core(
    material: Union[Material, MaterialWithBuildMetadata],
    boundary_vectors: Tuple[Tuple[int, int], Tuple[int, int]],
    core: str = "5|7",
    homo_bonds: Optional[str] = None,
    number_of_periods_across: int = 1,
    vacuum: float = 0.0,
) -> MaterialWithBuildMetadata:
    """
    Two grains of a honeycomb monolayer (graphene, h-BN, MoS2) meeting at two lines with the given core.

    Each grain is the rectangular cell along its boundary vector, (n, m) = n a + m b with b 60 degrees from a; the two
    vectors are of equal length, their angle is the tilt; the second grain is tried as given and turned by 180 degrees:

        (2, 1)|(1, 2)  21.8 degrees        (4, 1)|(1, 4)  38.2
        (3, 1)|(1, 3)  32.2                (4, 3)|(3, 4)   9.4
        (3, 2)|(2, 3)  13.2                (5, 4)|(4, 5)   7.3
        (1, 1)|(1, 1)   0, the second grain turned: a binary's inversion line (4|8 or 6)

    Args:
        material: The monolayer.
        boundary_vectors: The vectors of the two grains along the line.
        core: Ring sizes along both lines, "5|7", "4|8", "6" for hexagons only; their sum of n - 6 must be 0.
        homo_bonds: Bonds between atoms of one element at the lines: "none", "alternating" (as many of each element's
            at both), an element (only its at the line x = 0, none at the other); by default any.
        number_of_periods_across: Repetitions of each grain's cell across the line.
        vacuum: Vacuum of the monolayer, in angstroms.
    """
    core_ring_sizes = get_core_ring_sizes(core)
    elements = sorted(set(material.basis.elements.values))
    if homo_bonds not in (None, "none", "alternating", *elements):
        raise ValueError(f"homo_bonds is none, alternating or an element of the material: {', '.join(elements)}")
    slab = SlabConfiguration.from_parameters(material, (0, 0, 1), 1, vacuum=vacuum)
    monolayer = get_monolayer(SlabBuilder().get_material(slab))
    grain_pairs = get_grain_supercell_matrices(monolayer, boundary_vectors, number_of_periods_across)
    supercell_matrices, slide = get_slide(monolayer, grain_pairs, core_ring_sizes, homo_bonds)
    configuration = GrainBoundaryLinearConfiguration(
        stack_components=[
            SlabStrainedSupercellConfiguration(
                stack_components=slab.stack_components, direction=slab.direction, xy_supercell_matrix=matrix
            )
            for matrix in supercell_matrices
        ],
        xy_shift=[slide, 0.0],
        actual_angle=get_rotation(monolayer, *boundary_vectors) % LATTICE_SYMMETRY_ANGLE,
        core_ring_sizes=core_ring_sizes,
        homo_bonds=homo_bonds,
    )
    return GrainBoundaryLinearBuilder().get_material(configuration)
