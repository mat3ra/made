from typing import Optional, Union

from mat3ra.made.material import Material

from .....analyze.solid_solution_analyzer import SolidSolutionAnalyzer
from .....build_components import MaterialWithBuildMetadata
from .builder import SolidSolutionBuilder
from .configuration import SolidSolutionConfiguration
from .enums import SiteSelectionMethodEnum


def create_solid_solution(
    material: Union[Material, MaterialWithBuildMetadata],
    source_element: str,
    target_element: str,
    concentration: float,
    seed: Optional[int] = None,
    tolerance: float = 0.01,
    site_selection_method: SiteSelectionMethodEnum = SiteSelectionMethodEnum.UNIFORM,
) -> MaterialWithBuildMetadata:
    """
    Create a solid solution by partially substituting one element for another.

    Automatically determines the optimal supercell size to achieve the target
    concentration, builds the supercell, and performs substitution.

    Args:
        material (Union[Material, MaterialWithBuildMetadata]): Unit cell crystal.
        source_element (str): Element to partially replace (e.g. "Hf").
        target_element (str): Replacement element (e.g. "Zr").
        concentration (float): Fraction of source_element to replace (0.0-1.0).
        seed (Optional[int]): Random seed for reproducible site selection.
        tolerance (float): Acceptable deviation from target concentration.
        site_selection_method (SiteSelectionMethodEnum): RANDOM or UNIFORM (Farthest Point Sampling).

    Returns:
        MaterialWithBuildMetadata: Solid solution with full build metadata.
    """
    analyzer = SolidSolutionAnalyzer(
        material=material,
        source_element=source_element,
        target_element=target_element,
        target_concentration=concentration,
        tolerance=tolerance,
        seed=seed,
        site_selection_method=site_selection_method,
    )
    config = SolidSolutionConfiguration.from_parameters(
        crystal=material,
        supercell_material=analyzer.supercell_material,
        source_element=source_element,
        target_element=target_element,
        concentration=analyzer.achievable_concentration,
        selected_site_indices=analyzer.selected_site_indices,
    )
    builder = SolidSolutionBuilder()
    return builder.get_material(config)
