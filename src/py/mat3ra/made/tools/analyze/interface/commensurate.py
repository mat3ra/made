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
from .utils.vector import get_integer_vectors_in_box, get_shortest_right_handed_pair


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
    this analyzer finds commensurate supercells at a target twist angle: the coincidence cells whose twist is within
    angle_tolerance of target_angle, smallest cell first; lower max_supercell_matrix_int or angle_tolerance to bound
    the size.

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
    def matrix_ab(self) -> np.ndarray:
        """
        The in-plane lattice vectors a and b as rows, in Angstroms.
        """
        return np.array(self.material.lattice.vector_arrays)[:2, :2]

    @cached_property
    def integer_vectors(self) -> np.ndarray:
        """
        Integer coordinates of the supercell vectors searched, up to max_supercell_matrix_int, else limit_max_int.
        """
        return get_integer_vectors_in_box(self.max_supercell_matrix_int or self.limit_max_int)

    @cached_property
    def squared_lengths(self) -> np.ndarray:
        """
        Squared lengths of the supercell vectors in units of |a|², rounded so that equal lengths compare equal.
        """
        vectors = self.integer_vectors @ self.matrix_ab
        return np.round((vectors**2).sum(axis=1) / (self.matrix_ab[0] @ self.matrix_ab[0]), HASH_TOLERANCE)

    def _get_polar_angles_grouped_by_length(self) -> List[np.ndarray]:
        """
        Polar angles of the supercell vectors in degrees, one array per vector length.
        """
        vectors = self.integer_vectors @ self.matrix_ab
        polar_angles = np.degrees(np.arctan2(vectors[:, 1], vectors[:, 0]))
        return [polar_angles[self.squared_lengths == length] for length in np.unique(self.squared_lengths)]

    def _get_candidate_angles(self) -> np.ndarray:
        """
        Angles between supercell vectors of equal length (0 for each vector with itself), within angle_tolerance.
        """
        groups = self._get_polar_angles_grouped_by_length()
        angles = np.concatenate([np.subtract.outer(group, group).ravel() for group in groups])
        angles = angles[np.abs(angles - self.target_angle) < self.angle_tolerance]
        _, first_of_each_angle = np.unique(np.round(angles, HASH_TOLERANCE), return_index=True)
        return angles[first_of_each_angle]

    def _get_rotation_in_lattice_coordinates(self, angle: float) -> np.ndarray:
        """
        The rotation by angle, acting on row vectors of lattice coordinates.
        """
        cosine, sine = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        return self.matrix_ab @ np.array([[cosine, sine], [-sine, cosine]]) @ np.linalg.inv(self.matrix_ab)

    def _get_coincident_vectors(self, angle: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Supercell vectors whose rotated image is a lattice vector: the vectors, the images and their lengths.
        """
        images = self.integer_vectors @ self._get_rotation_in_lattice_coordinates(angle)
        shared = np.all(np.abs(images - np.round(images)) < 10**-HASH_TOLERANCE, axis=1)
        return self.integer_vectors[shared], np.round(images[shared]).astype(int), self.squared_lengths[shared]

    def _get_match(self, angle: float) -> Optional[CommensurateLatticeMatchHolder]:
        """
        The smallest coincidence cell of the rotation by angle, if get_angle_from_rotation_matrix_2d accepts it.
        """
        substrate_vectors, film_vectors, lengths = self._get_coincident_vectors(angle)
        pair = get_shortest_right_handed_pair(substrate_vectors, lengths)
        if pair is None:
            return None
        substrate, film = substrate_vectors[pair], film_vectors[pair]
        product = np.linalg.inv(self.matrix_ab) @ (np.linalg.inv(film) @ substrate) @ self.matrix_ab
        rotation_angle = get_angle_from_rotation_matrix_2d(product)
        if rotation_angle is None:
            return None
        return CommensurateLatticeMatchHolder(
            match_id=0,
            angle=rotation_angle,
            actual_angle=rotation_angle,
            xy_supercell_matrix_substrate=substrate.tolist(),
            xy_supercell_matrix_film=film.tolist(),
        )

    @cached_property
    def commensurate_lattice_match_holders(self) -> List[CommensurateLatticeMatchHolder]:
        """
        The coincidence cells within angle_tolerance of target_angle, smallest cell first.
        """
        holders = [holder for holder in map(self._get_match, self._get_candidate_angles()) if holder is not None]
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
