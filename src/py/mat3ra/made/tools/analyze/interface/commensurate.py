from collections import defaultdict
from functools import cached_property
from typing import List, Optional

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)
from mat3ra.made.lattice import Lattice
from mat3ra.made.material import Material
from pydantic import model_validator

from ....utils import create_2d_supercell_matrices, get_angle_from_rotation_matrix_2d
from .enums import angle_to_supercell_matrix_values_for_hex
from .simple import InterfaceAnalyzer
from .utils.holders import MatchedSubstrateFilmConfigurationHolder


class CommensurateLatticeMatchHolder(InMemoryEntityPydantic):
    match_id: int
    angle: float
    actual_angle: float
    xy_supercell_matrix_film: List[List[int]]
    xy_supercell_matrix_substrate: List[List[int]]


class CommensurateLatticeInterfaceAnalyzer(InterfaceAnalyzer):
    """
    Interface analyzer using commensurate lattice matching for commensurate lattice interfaces.

    For commensurate lattice bilayer materials where film and substrate are the same material,
    this analyzer finds commensurate supercells at a target twist angle.

    Attributes:
        target_angle (float): The target twist angle, in degrees.
        angle_tolerance (float): Tolerance for matching angles, in degrees.
        max_supercell_matrix_int (Optional[int]): Maximum integer for supercell matrix elements.
        limit_max_int (int): Limit for maximum integer to search for supercell matrices.
        return_first_match (bool): If True, returns only the first match found (to speed up the process).

    This class generates strained configurations for both substrate and film based on the commensurate matches found.

    """

    target_angle: float = 0.0
    angle_tolerance: float = 0.1
    max_supercell_matrix_int: Optional[int] = None
    limit_max_int: int = 50
    return_first_match: bool = True

    @model_validator(mode="before")
    def _handle_missing_substrate_or_film(cls, values):
        substrate = values.get("substrate_slab_configuration")
        film = values.get("film_slab_configuration")
        if substrate and not film:
            values["film_slab_configuration"] = substrate
        elif film and not substrate:
            values["substrate_slab_configuration"] = film
        return values

    @property
    def material(self) -> Material:
        return self.substrate_material

    def _get_initial_guess_for_max_int(self, material: Material, target_angle: float) -> int:
        if material.lattice.type == Lattice.__types__.HEX:
            xy_supercell_matrix_for_closest_angle = min(
                angle_to_supercell_matrix_values_for_hex, key=lambda x: abs(x["angle"] - target_angle)
            )
            return max(abs(x) for row in xy_supercell_matrix_for_closest_angle["xy_supercell"] for x in row)
        return 1

    def _generate_commensurate_lattices(
        self,
        material: Material,
        target_angle: float,
        max_supercell_matrix_element_int: int,
    ) -> List[CommensurateLatticeMatchHolder]:
        a = material.lattice.vector_arrays[0][:2]
        b = material.lattice.vector_arrays[1][:2]

        matrices = create_2d_supercell_matrices(max_supercell_matrix_element_int)
        matrix_ab = np.array([a, b])
        matrix_ab_inverse = np.linalg.inv(matrix_ab)
        matrix_ab_in_units_of_a = matrix_ab / np.linalg.norm(a)
        matrices_by_metric = defaultdict(list)

        solutions: List[CommensurateLatticeMatchHolder] = []
        match_id = 0

        for matrix1 in matrices:
            supercell_vectors = matrix1 @ matrix_ab_in_units_of_a
            metric = tuple(np.round(supercell_vectors @ supercell_vectors.T, 6).flatten())
            matrices_by_metric[metric].append(matrix1)
            for matrix2 in matrices_by_metric[metric]:
                matrix2_inverse = np.linalg.inv(matrix2)
                intermediate_product = matrix2_inverse @ matrix1
                product = matrix_ab_inverse @ intermediate_product @ matrix_ab
                angle = get_angle_from_rotation_matrix_2d(product)

                if angle is not None and np.abs(angle - target_angle) < self.angle_tolerance:
                    solutions.append(
                        CommensurateLatticeMatchHolder(
                            match_id=match_id,
                            angle=angle,
                            actual_angle=angle,
                            xy_supercell_matrix_substrate=matrix1.tolist(),
                            xy_supercell_matrix_film=matrix2.tolist(),
                        )
                    )
                    match_id += 1

                    if self.return_first_match:
                        return solutions

        return solutions

    @cached_property
    def commensurate_lattice_match_holders(self) -> List[CommensurateLatticeMatchHolder]:
        max_int = self.max_supercell_matrix_int or self._get_initial_guess_for_max_int(self.material, self.target_angle)

        commensurate_lattice_matches: List[CommensurateLatticeMatchHolder] = []

        while not commensurate_lattice_matches and max_int < self.limit_max_int:
            commensurate_lattice_matches = self._generate_commensurate_lattices(
                self.material, self.target_angle, max_int
            )
            max_int += 1

        return commensurate_lattice_matches

    def get_strained_configuration_by_match_id(self, match_id: int) -> MatchedSubstrateFilmConfigurationHolder:
        match_holders = self.commensurate_lattice_match_holders
        if match_id < 0 or match_id >= len(match_holders):
            raise ValueError(f"Match ID {match_id} out of range. Available IDs: 0-{len(match_holders)-1}")

        match_holder = match_holders[match_id]
        return self._create_strained_configs_from_match(match_holder)

    def _create_strained_configs_from_match(
        self, match_holder: CommensurateLatticeMatchHolder
    ) -> MatchedSubstrateFilmConfigurationHolder:
        substrate_matrix_schema = SupercellMatrix2DSchema(root=match_holder.xy_supercell_matrix_substrate)
        film_matrix_schema = SupercellMatrix2DSchema(root=match_holder.xy_supercell_matrix_film)

        return self.create_matched_configuration_holder(
            self.substrate_slab_configuration,
            self.film_slab_configuration,
            match_id=match_holder.match_id,
            substrate_xy_supercell_matrix=substrate_matrix_schema,
            film_xy_supercell_matrix=film_matrix_schema,
        )

    def get_strained_configurations(self) -> List[MatchedSubstrateFilmConfigurationHolder]:
        strained_configs = []

        for match_holder in self.commensurate_lattice_match_holders:
            config_holder = self._create_strained_configs_from_match(match_holder)
            strained_configs.append(config_holder)

        return strained_configs
