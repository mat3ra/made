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
        limit_max_int (int): Largest integer coordinate of the lattice vectors searched for the coincidence lattice.
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

    @staticmethod
    def _get_lattice_vectors(matrix_ab: np.ndarray, max_int: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Lattice vectors with integer coordinates up to max_int: the coordinates, the Cartesian vectors and their
        squared lengths in units of |a|², rounded so that equal lengths compare equal.
        """
        steps = np.arange(-max_int, max_int + 1)
        integer_vectors = np.stack(np.meshgrid(steps, steps, indexing="ij"), axis=-1).reshape(-1, 2)
        integer_vectors = integer_vectors[np.any(integer_vectors != 0, axis=1)]
        vectors = integer_vectors @ matrix_ab
        squared_lengths = np.round((vectors**2).sum(axis=1) / (matrix_ab[0] @ matrix_ab[0]), HASH_TOLERANCE)
        return integer_vectors, vectors, squared_lengths

    def _get_candidate_angles(self, vectors: np.ndarray, squared_lengths: np.ndarray) -> np.ndarray:
        """
        Rotation angles between lattice vectors of equal length (a vector and itself give 0), within angle_tolerance
        of target_angle, once each.
        """
        order = np.argsort(squared_lengths, kind="stable")
        polar_angles = np.degrees(np.arctan2(vectors[order, 1], vectors[order, 0]))
        sorted_lengths = squared_lengths[order]
        differences = [np.zeros(1)]
        for shift in range(1, np.unique(squared_lengths, return_counts=True)[1].max()):
            same_length = sorted_lengths[shift:] == sorted_lengths[:-shift]
            difference = polar_angles[shift:][same_length] - polar_angles[:-shift][same_length]
            differences += [difference, -difference]
        angles = np.concatenate(differences)
        angles = angles[np.abs(angles - self.target_angle) < self.angle_tolerance]
        return angles[np.unique(np.round(angles, HASH_TOLERANCE), return_index=True)[1]]

    @staticmethod
    def _get_coincidence_cell(
        angle: float,
        matrix_ab: np.ndarray,
        integer_vectors: np.ndarray,
        vectors: np.ndarray,
        squared_lengths: np.ndarray,
    ) -> Optional[Tuple[float, np.ndarray, np.ndarray]]:
        """
        The two shortest right-handed vectors shared by the lattice and its copy rotated by angle (the substrate
        supercell rows) and their coordinates in the rotated copy (the film supercell rows), with the rotation angle;
        None if fewer than two, or if the pair is not a rotation by get_angle_from_rotation_matrix_2d.
        """
        cosine, sine = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        images = vectors @ np.array([[cosine, sine], [-sine, cosine]]) @ np.linalg.inv(matrix_ab)
        coincident = np.all(np.abs(images - np.round(images)) < 10**-HASH_TOLERANCE, axis=1)
        substrate, film = integer_vectors[coincident], np.round(images[coincident]).astype(int)
        lengths = squared_lengths[coincident]
        first = np.argmin(lengths)
        right_handed = substrate[first, 0] * substrate[:, 1] - substrate[first, 1] * substrate[:, 0] > 0
        if not right_handed.any():
            return None
        cell = [first, np.flatnonzero(right_handed)[np.argmin(lengths[right_handed])]]
        product = np.linalg.inv(matrix_ab) @ (np.linalg.inv(film[cell]) @ substrate[cell]) @ matrix_ab
        rotation_angle = get_angle_from_rotation_matrix_2d(product)
        return None if rotation_angle is None else (rotation_angle, substrate[cell], film[cell])

    @cached_property
    def commensurate_lattice_match_holders(self) -> List[CommensurateLatticeMatchHolder]:
        matrix_ab = np.array(self.material.lattice.vector_arrays)[:2, :2]
        integer_vectors, vectors, squared_lengths = self._get_lattice_vectors(matrix_ab, self.limit_max_int)
        matches = []
        for candidate_angle in self._get_candidate_angles(vectors, squared_lengths):
            cell = self._get_coincidence_cell(candidate_angle, matrix_ab, integer_vectors, vectors, squared_lengths)
            if cell is None:
                continue
            angle_difference = abs((cell[0] - self.target_angle + 180) % 360 - 180)
            if angle_difference < self.angle_tolerance:
                matches.append((round(abs(np.linalg.det(cell[1]))), angle_difference, cell))
        matches.sort(key=lambda match: match[:2])
        holders = [
            CommensurateLatticeMatchHolder(
                match_id=match_id,
                angle=angle,
                actual_angle=angle,
                xy_supercell_matrix_substrate=substrate.tolist(),
                xy_supercell_matrix_film=film.tolist(),
            )
            for match_id, (_, _, (angle, substrate, film)) in enumerate(matches)
        ]
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
