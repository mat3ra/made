from typing import Optional, Tuple, Union

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.esse.models.materials_category.defective_structures.one_dimensional.grain_boundary_linear.configuration import (  # noqa: E501
    GrainBoundaryCoreEnum,
)

from mat3ra.made.material import Material
from .builder import GrainBoundaryLinearBuilder
from .configuration import GrainBoundaryLinearConfiguration
from ....compound_pristine_structures.two_dimensional.interface import get_commensurate_strained_configurations
from ....pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from .....analyze.interface.grain_boundary import GrainBoundaryLinearAnalyzer
from .....build_components import MaterialWithBuildMetadata


def create_grain_boundary_linear(
    material: Union[Material, MaterialWithBuildMetadata],
    target_angle: float = 0.0,
    angle_tolerance: float = 0.1,
    max_repetition_int: Optional[int] = None,
    limit_max_int: int = 20,
    return_first_match: bool = True,
    direction: AxisEnum = AxisEnum.x,
    gap: Optional[float] = 3.0,
    miller_indices: Tuple[int, int, int] = (0, 0, 1),
    number_of_layers: int = 1,
    vacuum: float = 0.0,
    use_conventional_cell: bool = True,
    boundary_vectors: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
    core: Optional[GrainBoundaryCoreEnum] = None,
    number_of_periods_across: int = 1,
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
        gap (Optional[float]): The gap between the two phases in Angstroms; None stacks them at their natural spacing.
        miller_indices (Tuple[int, int, int]): Miller indices for the slab surface.
        number_of_layers (int): Number of atomic layers in the slab.
        vacuum (float): Size of the vacuum layer in Angstroms.
        boundary_vectors (Optional[Tuple[Tuple[int, int], Tuple[int, int]]]): Lattice vectors of the two grains along
            the boundary, equal in length, in units of the lattice vectors; each grain is then the rectangular
            supercell [shortest perpendicular vector, boundary vector] (GrainBoundaryLinearAnalyzer).
        core (Optional[GrainBoundaryCoreEnum]): Ring pair ("5|7", "4|8") rebuilt along both lines of a honeycomb
            lattice; needs gap=None. Without boundary vectors, they are found from the target angle.
        number_of_periods_across (int): Repetitions of the perpendicular vector in each grain.

    Returns:
        Material: The grain boundary material.

    Raises:
        ValueError: If no commensurate lattice matches are found.
    """
    if boundary_vectors is not None or core is not None:
        slab_configuration = SlabConfiguration.from_parameters(
            material, miller_indices, number_of_layers, vacuum=vacuum, use_conventional_cell=use_conventional_cell
        )
        return create_grain_boundary_linear_on_line(
            slab_configuration, boundary_vectors, target_angle, angle_tolerance, number_of_periods_across, core, gap
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


def create_grain_boundary_linear_on_line(
    slab_configuration: SlabConfiguration,
    boundary_vectors: Optional[Tuple[Tuple[int, int], Tuple[int, int]]],
    target_angle: float,
    angle_tolerance: float,
    number_of_periods_across: int,
    core: Optional[GrainBoundaryCoreEnum],
    gap: Optional[float],
) -> MaterialWithBuildMetadata:
    """
    The grain boundary of two rectangular grains along x (GrainBoundaryLinearAnalyzer); with a core, grain 2 slid along
    the line as the analyzer chooses and the sites near both lines rebuilt.
    """
    analyzer = GrainBoundaryLinearAnalyzer(
        substrate_slab_configuration=slab_configuration,
        film_slab_configuration=slab_configuration,
        boundary_vectors=boundary_vectors,
        target_angle=target_angle,
        angle_tolerance=angle_tolerance,
        number_of_periods_across=number_of_periods_across,
        core=core,
    )
    configuration = GrainBoundaryLinearConfiguration(
        stack_components=analyzer.grain_configurations,
        gaps=ArrayWithIds.from_values([] if gap is None else [gap, gap]),
        actual_angle=analyzer.actual_angle,
    )
    builder = GrainBoundaryLinearBuilder()
    if analyzer.core is not None:
        slide = analyzer.get_slide(builder.get_material(configuration))
        configuration = configuration.model_copy(update={"xy_shift": [slide, 0.0], "core": analyzer.core})
    return builder.get_material(configuration)
