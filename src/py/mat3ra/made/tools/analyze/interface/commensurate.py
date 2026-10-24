from functools import cached_property
from typing import List, NamedTuple, Optional

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


class CoincidenceCell(NamedTuple):
    angle: float
    substrate_matrix: np.ndarray
    film_matrix: np.ndarray


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
        return np.array(self.material.lattice.vector_arrays)[:2, :2]

    @cached_property
    def integer_vectors(self) -> np.ndarray:
        """
        Integer coordinates of the supercell vectors searched: up to max_supercell_matrix_int, else limit_max_int.
        """
        max_int = self.max_supercell_matrix_int or self.limit_max_int
        steps = np.arange(-max_int, max_int + 1)
        integer_vectors = np.stack(np.meshgrid(steps, steps, indexing="ij"), axis=-1).reshape(-1, 2)
        return integer_vectors[np.any(integer_vectors != 0, axis=1)]

    @cached_property
    def squared_lengths(self) -> np.ndarray:
        """
        Squared lengths of the supercell vectors in units of |a|², rounded so that equal lengths compare equal.
        """
        vectors = self.integer_vectors @ self.matrix_ab
        return np.round((vectors**2).sum(axis=1) / (self.matrix_ab[0] @ self.matrix_ab[0]), HASH_TOLERANCE)

    def _get_candidate_angles(self) -> np.ndarray:
        """
        Rotation angles between supercell vectors of equal length (a vector and itself give 0), within
        angle_tolerance of target_angle, once each.
        """
        order = np.argsort(self.squared_lengths, kind="stable")
        vectors = self.integer_vectors[order] @ self.matrix_ab
        polar_angles, sorted_lengths = np.degrees(np.arctan2(vectors[:, 1], vectors[:, 0])), self.squared_lengths[order]
        differences = [np.zeros(1)]
        for shift in range(1, np.unique(sorted_lengths, return_counts=True)[1].max()):
            same_length = sorted_lengths[shift:] == sorted_lengths[:-shift]
            differences.append(polar_angles[shift:][same_length] - polar_angles[:-shift][same_length])
        angles = np.concatenate(differences)
        angles = angles[np.abs(angles - self.target_angle) < self.angle_tolerance]
        return angles[np.unique(np.round(angles, HASH_TOLERANCE), return_index=True)[1]]

    def _get_coincidence_cell(self, angle: float) -> Optional[CoincidenceCell]:
        """
        The two shortest right-handed supercell vectors shared by the lattice and its copy rotated by angle, with their
        coordinates in the rotated copy; None if fewer than two, or if get_angle_from_rotation_matrix_2d rejects them.
        """
        cosine, sine = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        rotation = self.matrix_ab @ np.array([[cosine, sine], [-sine, cosine]]) @ np.linalg.inv(self.matrix_ab)
        images = self.integer_vectors @ rotation
        coincident = np.all(np.abs(images - np.round(images)) < 10**-HASH_TOLERANCE, axis=1)
        substrate, film = self.integer_vectors[coincident], np.round(images[coincident]).astype(int)
        lengths = self.squared_lengths[coincident]
        first = np.argmin(lengths)
        right_handed = substrate[first, 0] * substrate[:, 1] - substrate[first, 1] * substrate[:, 0] > 0
        if not right_handed.any():
            return None
        rows = [first, np.flatnonzero(right_handed)[np.argmin(lengths[right_handed])]]
        product = np.linalg.inv(self.matrix_ab) @ (np.linalg.inv(film[rows]) @ substrate[rows]) @ self.matrix_ab
        rotation_angle = get_angle_from_rotation_matrix_2d(product)
        return None if rotation_angle is None else CoincidenceCell(rotation_angle, substrate[rows], film[rows])

    @cached_property
    def commensurate_lattice_match_holders(self) -> List[CommensurateLatticeMatchHolder]:
        cells = [cell for cell in map(self._get_coincidence_cell, self._get_candidate_angles()) if cell is not None]
        cells.sort(key=lambda cell: round(abs(np.linalg.det(cell.substrate_matrix))))
        holders = [
            CommensurateLatticeMatchHolder(
                match_id=match_id,
                angle=cell.angle,
                actual_angle=cell.angle,
                xy_supercell_matrix_substrate=cell.substrate_matrix.tolist(),
                xy_supercell_matrix_film=cell.film_matrix.tolist(),
            )
            for match_id, cell in enumerate(cells)
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
