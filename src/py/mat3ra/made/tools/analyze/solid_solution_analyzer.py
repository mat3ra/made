import random
from typing import List, Optional, Union

import numpy as np
from mat3ra.made.material import Material

from ..analyze import BaseMaterialAnalyzer
from ..analyze.utils import minimum_image_distances
from ..build.defective_structures.three_dimensional.solid_solution.enums import SiteSelectionMethodEnum
from ..build_components import MaterialWithBuildMetadata
from ..build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell


def _most_isotropic_dimensions(total_cells: int) -> List[int]:
    """
    Find [a, b, c] repeat factors whose product equals total_cells with minimum aspect ratio.

    Enumerates factor triples with a <= b <= c and returns the triple with the
    smallest spread (c - a).

    Args:
        total_cells (int): Target number of unit cells in the supercell.

    Returns:
        List[int]: Repeat factors [a, b, c] along the three lattice directions.
    """
    best_dimensions = [1, 1, total_cells]
    best_spread = total_cells - 1
    for a in range(1, total_cells + 1):
        if total_cells % a:
            continue
        for b in range(a, total_cells // a + 1):
            if (total_cells // a) % b:
                continue
            c = total_cells // (a * b)
            if c < b:
                continue
            spread = c - a
            if spread < best_spread:
                best_dimensions = [a, b, c]
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
        material (Union[Material, MaterialWithBuildMetadata]): Material with lattice and coordinates.
        source_indices (List[int]): Indices of candidate sites in the material basis.
        number_to_select (int): Number of sites to select.
        seed (int, optional): Random seed for the initial site choice.

    Returns:
        List[int]: Sorted list of selected site indices.
    """
    if number_to_select <= 0:
        return []
    if number_to_select >= len(source_indices):
        return sorted(source_indices)

    material.to_crystal()
    fractional_coordinates = np.array(material.basis.coordinates.values)
    lattice_vectors = np.array(material.lattice.vector_arrays)
    pairwise_distances = minimum_image_distances(fractional_coordinates[source_indices], lattice_vectors)

    random_generator = random.Random(seed)
    first_pick = random_generator.randrange(len(source_indices))
    selected = [first_pick]
    distance_to_selected = pairwise_distances[first_pick].copy()
    is_candidate = np.ones(len(source_indices), dtype=bool)
    is_candidate[first_pick] = False

    for _ in range(number_to_select - 1):
        farthest_distance = np.max(distance_to_selected[is_candidate])
        tied_candidates = np.where(is_candidate & np.isclose(distance_to_selected, farthest_distance))[0]
        next_pick = int(random_generator.choice(tied_candidates))
        selected.append(next_pick)
        is_candidate[next_pick] = False
        np.minimum(distance_to_selected, pairwise_distances[next_pick], out=distance_to_selected)

    return sorted(source_indices[i] for i in selected)


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
    site_selection_method: SiteSelectionMethodEnum = SiteSelectionMethodEnum.UNIFORM

    @property
    def source_element_count_per_cell(self) -> int:
        return sum(1 for element in self.material.basis.elements.values if element == self.source_element)

    @property
    def optimal_supercell_dimensions(self) -> List[int]:
        source_count_per_cell = self.source_element_count_per_cell
        if source_count_per_cell == 0:
            raise ValueError(f"No {self.source_element} atoms found in the unit cell.")

        best_dimensions = None
        best_shape_spread = self.max_supercell_cells
        for cell_count in range(1, self.max_supercell_cells + 1):
            source_atoms = source_count_per_cell * cell_count
            replacement_atoms = min(max(round(self.target_concentration * source_atoms), 0), source_atoms)
            achieved_concentration = replacement_atoms / source_atoms
            if abs(achieved_concentration - self.target_concentration) > self.tolerance:
                continue

            dimensions = _most_isotropic_dimensions(cell_count)
            shape_spread = dimensions[2] - dimensions[0]
            if shape_spread < best_shape_spread:
                best_dimensions = dimensions
                best_shape_spread = shape_spread
            if shape_spread == 0:
                break

        if best_dimensions is None:
            raise ValueError(
                f"Cannot achieve concentration {self.target_concentration} "
                f"within tolerance {self.tolerance} for up to {self.max_supercell_cells} cells."
            )
        return best_dimensions

    @property
    def actual_concentration(self) -> float:
        a, b, c = self.optimal_supercell_dimensions
        source_atoms = self.source_element_count_per_cell * a * b * c
        replacement_atoms = min(max(round(self.target_concentration * source_atoms), 0), source_atoms)
        return replacement_atoms / source_atoms

    @property
    def selected_site_indices(self) -> List[int]:
        supercell = create_supercell(material=self.material, scaling_factor=self.optimal_supercell_dimensions)
        supercell_material = MaterialWithBuildMetadata.create(supercell.to_dict())
        elements = supercell_material.basis.elements.values
        source_indices = [index for index, element in enumerate(elements) if element == self.source_element]
        replacement_atoms = min(
            max(round(self.actual_concentration * len(source_indices)), 0),
            len(source_indices),
        )

        if self.site_selection_method == SiteSelectionMethodEnum.UNIFORM:
            keep_atoms = len(source_indices) - replacement_atoms
            if keep_atoms < replacement_atoms:
                kept_indices = _select_sites_uniform(supercell_material, source_indices, keep_atoms, self.seed)
                return sorted(set(source_indices) - set(kept_indices))
            return _select_sites_uniform(supercell_material, source_indices, replacement_atoms, self.seed)

        random_generator = random.Random(self.seed)
        return sorted(random_generator.sample(source_indices, replacement_atoms))
