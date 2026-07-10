import random
from typing import List, Optional, Union

import numpy as np
from mat3ra.made.material import Material

from mat3ra.made.tools.analyze import BaseMaterialAnalyzer
from mat3ra.made.tools.analyze.utils import minimum_image_distances
from mat3ra.made.tools.build.defective_structures.three_dimensional.solid_solution.enums import SiteSelectionMethodEnum
from mat3ra.made.tools.build_components import MaterialWithBuildMetadata
from mat3ra.made.tools.build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell


def _most_isotropic_dimensions(total_cells: int) -> List[int]:
    """Return the [a, b, c] repeat factors with minimum aspect ratio for total_cells."""
    best_dimensions = [1, 1, total_cells]
    best_spread = total_cells - 1
    for factor_a in range(1, total_cells + 1):
        if total_cells % factor_a != 0:
            continue
        remaining = total_cells // factor_a
        for factor_b in range(factor_a, remaining + 1):
            if remaining % factor_b != 0:
                continue
            factor_c = remaining // factor_b
            if factor_c < factor_b:
                continue
            spread = factor_c - factor_a
            if spread < best_spread:
                best_dimensions = [factor_a, factor_b, factor_c]
                best_spread = spread
    return best_dimensions


def _select_sites_uniform(
    material: Union[Material, MaterialWithBuildMetadata],
    source_indices: List[int],
    number_to_select: int,
    seed: int = None,
) -> List[int]:
    """
    Select number_to_select sites from source_indices using Farthest Point Sampling.

    Iteratively picks the site whose minimum distance to all already-selected
    sites is largest, producing a maximally dispersed subset under PBC.

    Args:
        material: Material with lattice and coordinates.
        source_indices: Indices of candidate sites in the material basis.
        number_to_select: Number of sites to select.
        seed: Random seed for the initial site choice.

    Returns:
        Sorted list of selected site indices.
    """
    if number_to_select <= 0:
        return []
    if number_to_select >= len(source_indices):
        return sorted(source_indices)

    material.to_crystal()
    fractional_coordinates = np.array(material.basis.coordinates.values)
    lattice_vectors = np.array(material.lattice.vector_arrays)
    distance_matrix = minimum_image_distances(
        fractional_coordinates[source_indices], lattice_vectors
    )

    random_generator = random.Random(seed)
    initial_index = random_generator.randrange(len(source_indices))
    selected_local_indices = [initial_index]
    minimum_distances = distance_matrix[initial_index].copy()
    # Sentinel excludes the seed site from subsequent farthest-point picks.
    minimum_distances[initial_index] = -1.0

    for _ in range(number_to_select - 1):
        maximum_distance = np.max(minimum_distances)
        candidate_local_indices = np.where(np.isclose(minimum_distances, maximum_distance))[0]
        next_local_index = int(random_generator.choice(candidate_local_indices))
        selected_local_indices.append(next_local_index)
        np.minimum(minimum_distances, distance_matrix[next_local_index], out=minimum_distances)
        minimum_distances[next_local_index] = -1.0

    return sorted([source_indices[local_index] for local_index in selected_local_indices])


class SolidSolutionAnalyzer(BaseMaterialAnalyzer):
    """
    Analyzes a unit cell to plan supercell dimensions and select substitution sites.

    Given a unit cell material and a desired substitution ratio, finds the
    most isotropic supercell matching the target concentration within tolerance,
    then selects specific sites for substitution.
    """

    source_element: str
    target_element: str
    target_concentration: float
    tolerance: float = 0.01
    max_supercell_cells: int = 128
    seed: Optional[int] = None
    site_selection_method: SiteSelectionMethodEnum = SiteSelectionMethodEnum.RANDOM

    @property
    def source_element_count_per_cell(self) -> int:
        return sum(1 for element in self.material.basis.elements.values if element == self.source_element)

    @property
    def optimal_supercell_dimensions(self) -> List[int]:
        source_count_per_cell = self.source_element_count_per_cell
        if source_count_per_cell == 0:
            raise ValueError(f"No {self.source_element} atoms found in the unit cell.")

        best_dimensions = None
        best_spread = self.max_supercell_cells
        for total_cells in range(1, self.max_supercell_cells + 1):
            source_count = source_count_per_cell * total_cells
            replacement_count = max(
                0, min(round(self.target_concentration * source_count), source_count)
            )
            if abs(replacement_count / source_count - self.target_concentration) > self.tolerance:
                continue
            dimensions = _most_isotropic_dimensions(total_cells)
            spread = dimensions[2] - dimensions[0]
            if spread < best_spread:
                best_dimensions = dimensions
                best_spread = spread
            if spread == 0:
                break

        if best_dimensions is None:
            raise ValueError(
                f"Cannot achieve concentration {self.target_concentration} "
                f"within tolerance {self.tolerance} for up to {self.max_supercell_cells} cells."
            )
        return best_dimensions

    @property
    def actual_concentration(self) -> float:
        dimensions = self.optimal_supercell_dimensions
        source_count = self.source_element_count_per_cell * dimensions[0] * dimensions[1] * dimensions[2]
        replacement_count = max(0, min(round(self.target_concentration * source_count), source_count))
        return replacement_count / source_count

    @property
    def selected_site_indices(self) -> List[int]:
        supercell = create_supercell(material=self.material, scaling_factor=self.optimal_supercell_dimensions)
        supercell_material = MaterialWithBuildMetadata.create(supercell.to_dict())
        elements = supercell_material.basis.elements.values
        source_indices = [index for index, element in enumerate(elements) if element == self.source_element]
        replacement_count = max(
            0, min(round(self.actual_concentration * len(source_indices)), len(source_indices))
        )

        if self.site_selection_method == SiteSelectionMethodEnum.UNIFORM:
            keep_count = len(source_indices) - replacement_count
            if keep_count < replacement_count:
                kept_indices = _select_sites_uniform(
                    supercell_material, source_indices, keep_count, self.seed
                )
                return sorted(set(source_indices) - set(kept_indices))
            return _select_sites_uniform(
                supercell_material, source_indices, replacement_count, self.seed
            )

        random_generator = random.Random(self.seed)
        return sorted(random_generator.sample(source_indices, replacement_count))
