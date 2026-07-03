import random
from typing import List, Optional, Union

import numpy as np
from mat3ra.made.material import Material

from mat3ra.made.tools.analyze import BaseMaterialAnalyzer
from mat3ra.made.tools.build.defective_structures.three_dimensional.solid_solution.enums import SiteSelectionMethodEnum
from mat3ra.made.tools.build_components import MaterialWithBuildMetadata
from mat3ra.made.tools.build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell

MAX_SUPERCELL_CELLS = 128


def _most_isotropic_dimensions(total_cells: int) -> List[int]:
    best = [1, 1, total_cells]
    best_spread = total_cells - 1
    for a in range(1, total_cells + 1):
        if total_cells % a != 0:
            continue
        remaining = total_cells // a
        for b in range(a, remaining + 1):
            if remaining % b != 0:
                continue
            c = remaining // b
            if c < b:
                continue
            spread = c - a
            if spread < best_spread:
                best = [a, b, c]
                best_spread = spread
    return best


def _minimum_image_distances(frac_coords: np.ndarray, lattice_vectors: np.ndarray) -> np.ndarray:
    n = len(frac_coords)
    distances = np.zeros((n, n))
    for i in range(n):
        delta = frac_coords[i] - frac_coords[i + 1 :]
        delta -= np.round(delta)
        dists = np.linalg.norm(delta @ lattice_vectors, axis=1)
        distances[i, i + 1 :] = dists
        distances[i + 1 :, i] = dists
    return distances


def _select_sites_uniform(
    material: Union[Material, MaterialWithBuildMetadata],
    source_indices: List[int],
    n_select: int,
    seed: int = None,
) -> List[int]:
    """
    Select n_select sites from source_indices using Farthest Point Sampling.

    Iteratively picks the site whose minimum distance to all already-selected
    sites is largest, producing a maximally dispersed subset under PBC.

    Args:
        material: Material with lattice and coordinates.
        source_indices: Indices of candidate sites in the material basis.
        n_select: Number of sites to select.
        seed: Random seed for the initial site choice.

    Returns:
        Sorted list of selected site indices.
    """
    if n_select <= 0:
        return []
    if n_select >= len(source_indices):
        return sorted(source_indices)

    material.to_crystal()
    frac_coords = np.array(material.basis.coordinates.values)
    lattice_vectors = np.array(material.lattice.vector_arrays)
    dist_matrix = _minimum_image_distances(frac_coords[source_indices], lattice_vectors)

    rng = random.Random(seed)
    start = rng.randrange(len(source_indices))
    selected = [start]
    min_dist = dist_matrix[start].copy()
    min_dist[start] = -1.0

    for _ in range(n_select - 1):
        max_val = np.max(min_dist)
        candidates = np.where(np.isclose(min_dist, max_val))[0]
        next_idx = int(rng.choice(candidates))
        selected.append(next_idx)
        np.minimum(min_dist, dist_matrix[next_idx], out=min_dist)
        min_dist[next_idx] = -1.0

    return sorted([source_indices[i] for i in selected])


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
    seed: Optional[int] = None
    site_selection_method: SiteSelectionMethodEnum = SiteSelectionMethodEnum.RANDOM

    @property
    def source_element_count_per_cell(self) -> int:
        return sum(1 for el in self.material.basis.elements.values if el == self.source_element)

    @property
    def optimal_supercell_dimensions(self) -> List[int]:
        n_per_cell = self.source_element_count_per_cell
        if n_per_cell == 0:
            raise ValueError(f"No {self.source_element} atoms found in the unit cell.")

        best_dims, best_spread = None, MAX_SUPERCELL_CELLS
        for total_cells in range(1, MAX_SUPERCELL_CELLS + 1):
            n_source = n_per_cell * total_cells
            n_replace = max(0, min(round(self.target_concentration * n_source), n_source))
            if abs(n_replace / n_source - self.target_concentration) > self.tolerance:
                continue
            dims = _most_isotropic_dimensions(total_cells)
            spread = dims[2] - dims[0]
            if spread < best_spread:
                best_dims, best_spread = dims, spread
            if spread == 0:
                break

        if best_dims is None:
            raise ValueError(
                f"Cannot achieve concentration {self.target_concentration} "
                f"within tolerance {self.tolerance} for up to {MAX_SUPERCELL_CELLS} cells."
            )
        return best_dims

    @property
    def achievable_concentration(self) -> float:
        dims = self.optimal_supercell_dimensions
        n_source = self.source_element_count_per_cell * dims[0] * dims[1] * dims[2]
        return max(0, min(round(self.target_concentration * n_source), n_source)) / n_source

    @property
    def supercell_material(self) -> MaterialWithBuildMetadata:
        supercell = create_supercell(material=self.material, scaling_factor=self.optimal_supercell_dimensions)
        return MaterialWithBuildMetadata.create(supercell.to_dict())

    @property
    def selected_site_indices(self) -> List[int]:
        supercell = self.supercell_material
        elements = supercell.basis.elements.values
        source_indices = [i for i, el in enumerate(elements) if el == self.source_element]
        concentration = self.achievable_concentration
        n_replace = max(0, min(round(concentration * len(source_indices)), len(source_indices)))

        if self.site_selection_method == SiteSelectionMethodEnum.UNIFORM:
            n_keep = len(source_indices) - n_replace
            if n_keep < n_replace:
                kept = _select_sites_uniform(supercell, source_indices, n_keep, self.seed)
                return sorted(set(source_indices) - set(kept))
            else:
                return _select_sites_uniform(supercell, source_indices, n_replace, self.seed)
        else:
            rng = random.Random(self.seed)
            return sorted(rng.sample(source_indices, n_replace))
