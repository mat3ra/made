from collections import defaultdict
from functools import cached_property
from typing import ClassVar, List, Optional

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.builder import SlabBuilder
from mat3ra.utils.matrix import convert_2x2_to_3x3
from pymatgen.analysis.interfaces.coherent_interfaces import ZSLGenerator as PymatgenZSLGenerator

from ...build_components import MaterialWithBuildMetadata
from ..interface.simple import InterfaceAnalyzer
from ..interface.utils.holders import MatchedSubstrateFilmConfigurationHolder
from ..utils import calculate_von_mises_strain
from .utils.vector import align_first_vector_to_x_2d_right_handed, are_vectors_colinear, get_global_gcd


class ZSLMatchHolder(InMemoryEntityPydantic):
    match_id: int
    substrate_supercell_matrix: SupercellMatrix2DSchema
    film_supercell_matrix: SupercellMatrix2DSchema
    strain_transformation_matrix: Matrix3x3Schema
    substrate_sl_vector_arrays: np.ndarray = None
    film_sl_vector_arrays: np.ndarray = None
    film_vectors: np.ndarray = None
    substrate_vectors: np.ndarray = None
    match_area: float
    total_strain_percentage: float


class ZSLInterfaceAnalyzer(InterfaceAnalyzer):
    """Interface analyzer using Pymatgen's ZSL algorithm to find matching supercells."""

    max_area: float = 50.0
    max_area_ratio_tol: float = 0.09
    max_length_tol: float = 0.03
    max_angle_tol: float = 0.01
    reduce_result_cell: bool = True

    math_precision: ClassVar[float] = 1e-4

    @classmethod
    def calculate_total_strain_percentage(cls, strain_matrix: list) -> float:
        return calculate_von_mises_strain(np.array(strain_matrix))

    @cached_property
    def film_slab(self) -> MaterialWithBuildMetadata:
        return SlabBuilder().get_material(self.film_slab_configuration)

    @cached_property
    def substrate_slab(self) -> MaterialWithBuildMetadata:
        return SlabBuilder().get_material(self.substrate_slab_configuration)

    @cached_property
    def generated_matches(self):
        zsl_generator = PymatgenZSLGenerator(
            max_area=self.max_area,
            max_area_ratio_tol=self.max_area_ratio_tol,
            max_length_tol=self.max_length_tol,
            max_angle_tol=self.max_angle_tol,
        )

        film_vectors = self.film_slab.lattice.vector_arrays_rounded[0:2]
        substrate_vectors = self.substrate_slab.lattice.vector_arrays_rounded[0:2]

        zsl_matches_pymatgen = list(
            zsl_generator(
                film_vectors=film_vectors,
                substrate_vectors=substrate_vectors,
            )
        )
        return zsl_matches_pymatgen

    @cached_property
    def zsl_match_holders(self) -> List[ZSLMatchHolder]:
        match_holders = []
        for idx, match_pymatgen in enumerate(self.generated_matches):
            match_holder = self.convert_generated_match_to_match_holder(idx, match_pymatgen)
            if match_holder is None:
                continue
            match_holders.append(match_holder)

        match_holders = self.purge_equivalent_matches(match_holders)

        # sort matches by strain in ascending order, then for each equal strain by area in ascending order
        match_holders = self.sort_by_strain_then_area(match_holders)

        return match_holders

    def purge_equivalent_matches(self, match_holders: List[ZSLMatchHolder]) -> List[ZSLMatchHolder]:
        unique_matches = []
        seen_matches = set()

        for holder in match_holders:
            match_key = (
                round(holder.match_area / self.math_precision) * self.math_precision,
                round(holder.total_strain_percentage / self.math_precision) * self.math_precision,
            )

            if match_key not in seen_matches:
                seen_matches.add(match_key)
                unique_matches.append(holder)

        return unique_matches

    def convert_generated_match_to_match_holder(self, match_id: int, match_pymatgen) -> Optional[ZSLMatchHolder]:
        film_slab_vectors = np.array(self.film_slab.lattice.vector_arrays_rounded[0:2])[:, :2]
        substrate_slab_vectors = np.array(self.substrate_slab.lattice.vector_arrays_rounded[0:2])[:, :2]

        pymatgen_film_sl_vectors = match_pymatgen.film_sl_vectors[:, :2]
        pymatgen_substrate_sl_vectors = match_pymatgen.substrate_sl_vectors[:, :2]

        film_sl_vectors, substrate_sl_vectors = self._get_sl_vectors_for_supercell_calculation(
            pymatgen_film_sl_vectors, pymatgen_substrate_sl_vectors
        )
        if film_sl_vectors is None:
            return None

        film_supercell_matrix, substrate_supercell_matrix, area = self._calculate_and_reduce_supercell_matrices(
            film_slab_vectors,
            substrate_slab_vectors,
            film_sl_vectors,
            substrate_sl_vectors,
            match_pymatgen.match_area,
        )

        film_sl_supercell_vectors = film_supercell_matrix @ film_slab_vectors
        substrate_sl_supercell_vectors = substrate_supercell_matrix @ substrate_slab_vectors

        if (
            abs(np.linalg.det(film_sl_supercell_vectors)) < self.math_precision
            or abs(np.linalg.det(substrate_sl_supercell_vectors)) < self.math_precision
        ):
            return None

        real_strain_matrix, strain_percentage = self._calculate_strain(
            film_sl_supercell_vectors, substrate_sl_supercell_vectors
        )

        return ZSLMatchHolder(
            match_id=match_id,
            substrate_supercell_matrix=SupercellMatrix2DSchema(root=substrate_supercell_matrix.tolist()),
            film_supercell_matrix=SupercellMatrix2DSchema(root=film_supercell_matrix.tolist()),
            strain_transformation_matrix=Matrix3x3Schema(root=real_strain_matrix),
            match_area=area,
            total_strain_percentage=strain_percentage,
        )

    def _get_sl_vectors_for_supercell_calculation(self, pymatgen_film_sl_vectors, pymatgen_substrate_sl_vectors):
        """
        Determine which superlattice vectors to use for supercell matrix calculation.

        Calculating the supercell transformation matrix requires that corresponding
        superlattice vectors of film and substrate are colinear. Non-colinear vectors
        cannot be used to derive a valid integer transformation matrix from original to supercell.
        While diagonal matrices can be used, and can give smaller area match, so they should be preserved.
        """
        pymatgen_substrate_sl_vectors_aligned = align_first_vector_to_x_2d_right_handed(pymatgen_substrate_sl_vectors)
        pymatgen_film_sl_vectors_aligned = align_first_vector_to_x_2d_right_handed(pymatgen_film_sl_vectors)

        a_colinear = are_vectors_colinear(pymatgen_film_sl_vectors_aligned[0], pymatgen_substrate_sl_vectors_aligned[0])
        b_colinear = are_vectors_colinear(pymatgen_film_sl_vectors_aligned[1], pymatgen_substrate_sl_vectors_aligned[1])

        if not (a_colinear and b_colinear):
            return None, None

        is_film_diag = np.allclose(pymatgen_film_sl_vectors_aligned, np.diag(np.diag(pymatgen_film_sl_vectors_aligned)))
        is_substrate_diag = np.allclose(
            pymatgen_substrate_sl_vectors_aligned, np.diag(np.diag(pymatgen_substrate_sl_vectors_aligned))
        )

        if is_film_diag and is_substrate_diag:
            return pymatgen_film_sl_vectors, pymatgen_substrate_sl_vectors
        else:
            return pymatgen_film_sl_vectors_aligned, pymatgen_substrate_sl_vectors_aligned

    def _calculate_and_reduce_supercell_matrices(
        self, film_slab_vectors, substrate_slab_vectors, film_sl_vectors, substrate_sl_vectors, match_area
    ):
        film_supercell_matrix = np.rint(np.linalg.solve(film_slab_vectors, film_sl_vectors)).astype(int)
        substrate_supercell_matrix = np.rint(np.linalg.solve(substrate_slab_vectors, substrate_sl_vectors)).astype(int)

        area = match_area
        if self.reduce_result_cell:
            g = get_global_gcd(film_supercell_matrix, substrate_supercell_matrix)
            film_supercell_matrix = film_supercell_matrix // g
            substrate_supercell_matrix = substrate_supercell_matrix // g
            area = area / g**2

        return film_supercell_matrix, substrate_supercell_matrix, area

    def _calculate_strain(self, film_sl_supercell_vectors, substrate_sl_supercell_vectors):
        film_det = np.linalg.det(film_sl_supercell_vectors)
        substrate_det = np.linalg.det(substrate_sl_supercell_vectors)

        # Handle cases where lattices match but are oriented in opposite directions (e.g., 180° rotation).
        # This keeps the right-handed system for the strain calculation.
        # The strain calculation uses vector magnitudes, so we need consistent orientation to avoid artificial strain
        if (film_det > 0) != (substrate_det > 0):
            film_sl_supercell_vectors = film_sl_supercell_vectors.copy()
            film_sl_supercell_vectors[1] = -film_sl_supercell_vectors[1]

        real_strain_matrix = np.linalg.solve(film_sl_supercell_vectors, substrate_sl_supercell_vectors)
        real_strain_matrix = convert_2x2_to_3x3(real_strain_matrix.tolist())
        strain_percentage = self.calculate_total_strain_percentage(real_strain_matrix)
        return real_strain_matrix, strain_percentage

    def get_strained_configuration_by_match_id(self, match_id: int) -> MatchedSubstrateFilmConfigurationHolder:
        match_holders = self.zsl_match_holders
        if not match_holders:
            raise ValueError("No ZSL matches found. Please check the input configurations.")
        if match_id < 0 or match_id >= len(match_holders):
            raise ValueError(f"Match ID {match_id} out of range. Available IDs: 0-{len(match_holders)-1}")

        match_holder = match_holders[match_id]
        return self._create_strained_configs_from_match(match_holder)

    def _create_strained_configs_from_match(
        self, match_holder: ZSLMatchHolder
    ) -> MatchedSubstrateFilmConfigurationHolder:
        return super().create_matched_configuration_holder(
            substrate_slab_config=self.substrate_slab_configuration,
            film_slab_config=self.film_slab_configuration,
            match_id=match_holder.match_id,
            substrate_xy_supercell_matrix=match_holder.substrate_supercell_matrix,
            film_xy_supercell_matrix=match_holder.film_supercell_matrix,
            substrate_strain_matrix=self._no_strain_matrix,
            film_strain_matrix=match_holder.strain_transformation_matrix,
            total_strain_percentage=match_holder.total_strain_percentage,
        )

    def get_strained_configurations(
        self,
    ) -> List[MatchedSubstrateFilmConfigurationHolder]:
        strained_configs = []

        for match_holder in self.zsl_match_holders:
            config_holder = self._create_strained_configs_from_match(match_holder)
            strained_configs.append(config_holder)

        return strained_configs

    def sort_by_strain_then_area(self, match_holders: List[ZSLMatchHolder], strain_tol=1e-3):
        same_strain_groups = defaultdict(list)
        for m in match_holders:
            strain_key = round(m.total_strain_percentage / strain_tol) * strain_tol
            same_strain_groups[strain_key].append(m)

        result = []
        for strain_key in sorted(same_strain_groups.keys()):
            bucket = same_strain_groups[strain_key]
            bucket.sort(key=lambda m: m.match_area)
            result.extend(bucket)

        return result
