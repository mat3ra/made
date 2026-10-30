from functools import cached_property
from typing import List, Optional, Tuple

import numpy as np
from mat3ra.code.constants import HASH_TOLERANCE
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)
from mat3ra.made.material import Material
from pydantic import model_validator

from ....utils import get_angle_from_rotation_matrix_2d
from .simple import InterfaceAnalyzer
from .utils.holders import MatchedSubstrateFilmConfigurationHolder
from .utils.vector import get_integer_coordinates_up_to, get_shortest_right_handed_pair


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
    this analyzer finds the supercells shared by both layers at a target twist angle, smallest first:
    1. List the supercell vectors i·a + j·b with |i| and |j| up to max_supercell_matrix_int (else limit_max_int).
    2. Every two supercell vectors of equal length give a candidate twist angle; keep those within angle_tolerance.
    3. For a candidate twist, keep the supercell vectors whose twisted copy is also a lattice vector (shared by both).
    4. The two shortest shared vectors form the smallest common supercell; it is accepted only if
       get_angle_from_rotation_matrix_2d confirms the twist.

    Attributes:
        target_angle (float): The target twist angle, in degrees.
        angle_tolerance (float): Tolerance for matching angles, in degrees.
        max_supercell_matrix_int (Optional[int]): Largest integer coordinate of the supercell vectors searched.
        limit_max_int (int): Largest integer coordinate of the supercell vectors searched, if max_supercell_matrix_int
            is None.
        return_first_match (bool): If True, returns only the first match found (to speed up the process).

    This class generates strained configurations for both substrate and film based on the commensurate matches found.
    """

    target_angle: float = 0.0
    angle_tolerance: float = 0.1
    max_supercell_matrix_int: Optional[int] = None
    limit_max_int: int = 82
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

    @cached_property
    def lattice_vectors_2d(self) -> np.ndarray:
        """
        The in-plane lattice vectors a and b as rows, in Angstroms.
        """
        return np.array(self.material.lattice.vector_arrays)[:2, :2]

    @cached_property
    def supercell_vector_coordinates(self) -> np.ndarray:
        """
        The (i, j) of each supercell vector i·a + j·b searched, up to max_supercell_matrix_int, else limit_max_int.
        """
        return get_integer_coordinates_up_to(self.max_supercell_matrix_int or self.limit_max_int)

    @cached_property
    def supercell_vector_lengths_squared(self) -> np.ndarray:
        """
        The squared length of each supercell vector in units of |a|², rounded so that equal lengths compare equal.
        """
        supercell_vectors = self.supercell_vector_coordinates @ self.lattice_vectors_2d
        a_length_squared = self.lattice_vectors_2d[0] @ self.lattice_vectors_2d[0]
        return np.round((supercell_vectors**2).sum(axis=1) / a_length_squared, HASH_TOLERANCE)

    def _get_directions_by_length(self) -> List[np.ndarray]:
        """
        The direction of each supercell vector (its polar angle, in degrees), one array per vector length.
        """
        supercell_vectors = self.supercell_vector_coordinates @ self.lattice_vectors_2d
        directions = np.degrees(np.arctan2(supercell_vectors[:, 1], supercell_vectors[:, 0]))
        lengths = self.supercell_vector_lengths_squared
        return [directions[lengths == length] for length in np.unique(lengths)]

    def _get_candidate_twist_angles(self) -> np.ndarray:
        """
        The twist angles between supercell vectors of equal length (0 for each vector with itself), within tolerance.
        """
        directions_by_length = self._get_directions_by_length()
        angles = np.concatenate(
            [np.subtract.outer(directions, directions).ravel() for directions in directions_by_length]
        )
        angles = angles[np.abs(angles - self.target_angle) < self.angle_tolerance]
        _, first_of_each_angle = np.unique(np.round(angles, HASH_TOLERANCE), return_index=True)
        return angles[first_of_each_angle]

    def _get_twist_in_lattice_coordinates(self, angle: float) -> np.ndarray:
        """
        The twist by angle as a matrix acting on (i, j) coordinates written as rows.
        """
        cosine, sine = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        rotation = np.array([[cosine, sine], [-sine, cosine]])
        return self.lattice_vectors_2d @ rotation @ np.linalg.inv(self.lattice_vectors_2d)

    def _get_shared_supercell_vectors(self, angle: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        The supercell vectors whose twisted copy is also a lattice vector: their (i, j), the copy's (i, j), lengths.
        """
        twisted_coordinates = self.supercell_vector_coordinates @ self._get_twist_in_lattice_coordinates(angle)
        is_shared = np.all(np.abs(twisted_coordinates - np.round(twisted_coordinates)) < 10**-HASH_TOLERANCE, axis=1)
        return (
            self.supercell_vector_coordinates[is_shared],
            np.round(twisted_coordinates[is_shared]).astype(int),
            self.supercell_vector_lengths_squared[is_shared],
        )

    def _get_smallest_shared_supercell(self, angle: float) -> Optional[CommensurateLatticeMatchHolder]:
        """
        The smallest supercell shared by both layers at this twist, if get_angle_from_rotation_matrix_2d confirms it.
        """
        substrate_coordinates, film_coordinates, lengths = self._get_shared_supercell_vectors(angle)
        pair = get_shortest_right_handed_pair(substrate_coordinates, lengths)
        if pair is None:
            return None
        substrate_matrix, film_matrix = substrate_coordinates[pair], film_coordinates[pair]
        lattice_vectors_2d = self.lattice_vectors_2d
        twist = np.linalg.inv(lattice_vectors_2d) @ (np.linalg.inv(film_matrix) @ substrate_matrix) @ lattice_vectors_2d
        twist_angle = get_angle_from_rotation_matrix_2d(twist)
        if twist_angle is None:
            return None
        return CommensurateLatticeMatchHolder(
            match_id=0,
            angle=twist_angle,
            actual_angle=twist_angle,
            xy_supercell_matrix_substrate=substrate_matrix.tolist(),
            xy_supercell_matrix_film=film_matrix.tolist(),
        )

    @cached_property
    def commensurate_lattice_match_holders(self) -> List[CommensurateLatticeMatchHolder]:
        """
        The supercells shared by both layers within angle_tolerance of target_angle, smallest first.
        """
        candidates = map(self._get_smallest_shared_supercell, self._get_candidate_twist_angles())
        holders = [holder for holder in candidates if holder is not None]
        holders.sort(key=lambda holder: round(np.linalg.det(holder.xy_supercell_matrix_substrate)))
        for match_id, holder in enumerate(holders):
            holder.match_id = match_id
        return holders[:1] if self.return_first_match else holders

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
