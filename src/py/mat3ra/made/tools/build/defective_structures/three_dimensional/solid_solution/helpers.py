from typing import Optional, Union

from mat3ra.esse.models.materials_category_components.entities.core.zero_dimensional.atom import AtomSchema
from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum
from mat3ra.made.material import Material

from .....analyze.solid_solution_analyzer import SolidSolutionAnalyzer
from .....build_components import MaterialWithBuildMetadata
from .....build_components.entities.auxiliary.zero_dimensional.point_defect_site.configuration import (
    PointDefectSiteConfiguration,
)
from .....build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell
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
    max_supercell_cells: int = 128,
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
        max_supercell_cells (int): Maximum supercell size to search.
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
        max_supercell_cells=max_supercell_cells,
        seed=seed,
        site_selection_method=site_selection_method,
    )
    supercell = create_supercell(material, scaling_factor=analyzer.optimal_supercell_dimensions)
    coordinates = supercell.basis.coordinates.values
    site_configurations = [
        PointDefectSiteConfiguration(
            crystal=supercell,
            coordinate=coordinates[site_index],
            element=AtomSchema(chemical_element=target_element),
        )
        for site_index in analyzer.selected_site_indices
    ]
    configuration = SolidSolutionConfiguration(
        crystal=material,
        source_element=source_element,
        target_element=target_element,
        target_concentration=concentration,
        actual_concentration=analyzer.actual_concentration,
        merge_components=[supercell] + site_configurations,
        merge_method=MergeMethodsEnum.REPLACE,
    )
    return SolidSolutionBuilder().get_material(configuration)
