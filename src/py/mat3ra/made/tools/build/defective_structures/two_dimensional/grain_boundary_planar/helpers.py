from typing import Optional, List, Tuple, Union

from mat3ra.made.material import Material
from .builder import GrainBoundaryPlanarBuilder
from .configuration import GrainBoundaryPlanarConfiguration
from .....analyze.interface import GrainBoundaryPlanarAnalyzer
from .....build_components import MaterialWithBuildMetadata


def create_grain_boundary_planar(
    phase_1_material: Union[Material, MaterialWithBuildMetadata],
    phase_2_material: Optional[Material] = None,
    phase_1_miller_indices: Tuple[int, int, int] = (0, 0, 1),
    phase_2_miller_indices: Tuple[int, int, int] = (0, 0, 1),
    phase_1_thickness: int = 1,
    phase_2_thickness: int = 1,
    translation_vector: List[float] = [0.0, 0.0],
    gap: float = 3.0,
    max_area: float = 50.0,
    match_id: int = 0,
    max_area_ratio_tol: float = 0.09,
    max_length_tol: float = 0.03,
    max_angle_tol: float = 0.01,
    use_conventional_cell: bool = True,
) -> Material:
    """
    Create a planar grain boundary between two materials with different orientations.

    Args:
        phase_1_material: The material to use for each phase of the grain boundary
        phase_1_miller_indices: Miller indices for phase 1
        phase_2_miller_indices: Miller indices for phase 2
        phase_1_thickness: Number of layers for phase 1
        phase_2_thickness: Number of layers for phase 2
        translation_vector: Relative shift between phases [x, y, z]
        gap: Gap between phases in Angstroms
        match_id: ZSL match ID to use (0 for first match)
        max_area: Maximum area for ZSL matching
        max_area_ratio_tol: Area ratio tolerance for ZSL matching
        max_length_tol: Length tolerance for ZSL matching
        max_angle_tol: Angle tolerance for ZSL matching

    Returns:
        Material: The grain boundary material
    """
    phase_2_material = phase_2_material or phase_1_material
    analyzer = GrainBoundaryPlanarAnalyzer(
        phase_1_material=phase_1_material,
        phase_2_material=phase_2_material,
        phase_1_miller_indices=phase_1_miller_indices,
        phase_2_miller_indices=phase_2_miller_indices,
        phase_1_thickness=phase_1_thickness,
        phase_2_thickness=phase_2_thickness,
        max_area=max_area,
        max_area_ratio_tol=max_area_ratio_tol,
        max_length_tol=max_length_tol,
        max_angle_tol=max_angle_tol,
    )

    strained_config = analyzer.get_grain_boundary_configuration_by_match_id(match_id)

    gb_config = GrainBoundaryPlanarConfiguration.from_parameters(
        phase_1_configuration=strained_config.substrate_configuration,
        phase_2_configuration=strained_config.film_configuration,
        xy_shift=translation_vector,
        gaps=[gap, gap],
    )

    builder = GrainBoundaryPlanarBuilder()
    return builder.get_material(gb_config)
