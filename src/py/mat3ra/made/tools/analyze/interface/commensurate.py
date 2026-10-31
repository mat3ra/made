from functools import cached_property
from typing import Any, Dict, List, Optional

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

# Lengths, angles and steps are compared to 3 decimals, as material hashes are; near-hexagonal cells such as
# Standata h-BN (b = a + 1e-6) then still group as hexagonal.
COINCIDENCE_DECIMALS = HASH_TOLERANCE


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
    1. List the supercell vectors i·a + j·b, i steps along a and j along b, with |i| and |j| up to the size limit.
    2. Every two supercell vectors of equal length give a candidate twist angle; keep those within angle_tolerance.
    3. For a candidate twist, keep the supercell vectors whose twisted copy is also a lattice vector (shared by both).
    4. The two shortest shared vectors form the smallest common supercell; it is accepted only if
       get_angle_from_rotation_matrix_2d confirms the twist.
    5. Both layers are built as these supercells. They have equal lengths and angle, and the lattice is rebuilt with
       a along x, so the film's atoms come out rotated by the twist.

    Attributes:
        target_angle (float): The target twist angle, in degrees.
        angle_tolerance (float): Tolerance for matching angles, in degrees.
        max_supercell_matrix_int (Optional[int]): Size limit, if given: the largest |i| and |j| of the supercell
            vectors i·a + j·b searched.
        limit_max_int (int): Size limit if max_supercell_matrix_int is None: the largest |i| and |j| of the
            supercell vectors i·a + j·b searched.
        return_first_match (bool): If True, keeps only the smallest supercell.

    This class generates strained configurations for both substrate and film based on the commensurate matches found.
    """

    target_angle: float = 0.0
    angle_tolerance: float = 0.1
    max_supercell_matrix_int: Optional[int] = None
    limit_max_int: int = 82  # the Twister table's smallest angle (0.82°, enums.py) needs |i| and |j| up to 81
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
    def supercell_vector_steps(self) -> np.ndarray:
        """
        Each candidate supercell vector as (i, j): i steps along a plus j steps along b, up to the size limit.
        """
        size_limit = self.max_supercell_matrix_int or self.limit_max_int
        steps = range(-size_limit, size_limit + 1)
        # This order (i outer, both from -size_limit) decides which of several equally short vectors comes first.
        return np.array([(i, j) for i in steps for j in steps if (i, j) != (0, 0)])

    @cached_property
    def supercell_vectors(self) -> np.ndarray:
        """
        Each candidate supercell vector i·a + j·b in Cartesian coordinates, in Angstroms.
        """
        return self.supercell_vector_steps @ self.lattice_vectors_2d

    @cached_property
    def supercell_vector_lengths_squared(self) -> np.ndarray:
        """
        The squared length of each supercell vector in units of |a|², rounded so that equal lengths compare equal.
        """
        a_length_squared = self.lattice_vectors_2d[0] @ self.lattice_vectors_2d[0]
        return np.round((self.supercell_vectors**2).sum(axis=1) / a_length_squared, COINCIDENCE_DECIMALS)

    def _get_directions_by_length(self) -> List[np.ndarray]:
        """
        The direction of each supercell vector (its polar angle, in degrees), one array per vector length.
        """
        directions = np.degrees(np.arctan2(self.supercell_vectors[:, 1], self.supercell_vectors[:, 0]))
        lengths = self.supercell_vector_lengths_squared
        return [directions[lengths == length] for length in np.unique(lengths)]

    def _get_candidate_twist_angles(self) -> np.ndarray:
        """
        The twist angles between supercell vectors of equal length (0 for each vector with itself), within tolerance.
        """
        # Every difference between two directions of one length, in both orders.
        differences = [
            np.subtract.outer(directions, directions).ravel() for directions in self._get_directions_by_length()
        ]
        angles = np.concatenate(differences)
        angles = angles[np.abs(angles - self.target_angle) < self.angle_tolerance]
        # One unrounded angle per rounded value: a rounded angle would miss shared vectors in large supercells.
        _, first_of_each_angle = np.unique(np.round(angles, COINCIDENCE_DECIMALS), return_index=True)
        return angles[first_of_each_angle]

    def _get_twist_for_steps(self, angle: float) -> np.ndarray:
        """
        The twist by angle as a matrix acting on (i, j) steps written as rows.
        """
        cosine, sine = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        rotation = np.array([[cosine, sine], [-sine, cosine]])
        return self.lattice_vectors_2d @ rotation @ np.linalg.inv(self.lattice_vectors_2d)

    def _get_shared_mask(self, twist: np.ndarray) -> np.ndarray:
        """
        Whether each supercell vector's twisted copy is also a lattice vector (whole steps), that is, shared by both.
        """
        twisted_steps = self.supercell_vector_steps @ twist
        return np.all(np.abs(twisted_steps - np.round(twisted_steps)) < 10**-COINCIDENCE_DECIMALS, axis=1)

    def _get_two_shortest_shared_vectors(self, is_shared: np.ndarray) -> Optional[np.ndarray]:
        """
        The steps of the shortest shared vector and of the shortest shared one with the same handedness as (a, b).
        """
        steps, lengths = self.supercell_vector_steps[is_shared], self.supercell_vector_lengths_squared[is_shared]
        first = np.argmin(lengths)
        # A positive cross product of the (i, j) means the same handedness as (a, b).
        same_handedness = steps[first, 0] * steps[:, 1] - steps[first, 1] * steps[:, 0] > 0
        if not same_handedness.any():
            return None
        second = np.flatnonzero(same_handedness)[np.argmin(lengths[same_handedness])]
        return steps[[first, second]]

    def _get_smallest_shared_supercell(self, angle: float) -> Optional[Dict[str, Any]]:
        """
        The smallest supercell shared by both layers at this twist, as match fields, if the rotation check confirms it.
        """
        twist = self._get_twist_for_steps(angle)
        substrate_matrix = self._get_two_shortest_shared_vectors(self._get_shared_mask(twist))
        if substrate_matrix is None:
            return None
        film_matrix = np.round(substrate_matrix @ twist).astype(int)
        lattice_vectors_2d = self.lattice_vectors_2d
        # The rotation taking the film cell onto the substrate cell, (film_matrix · L)⁻¹ (substrate_matrix · L), written
        # as main writes it: np.linalg.solve gives the same matrix but can flip the sign of a ±180° result.
        rotation = (
            np.linalg.inv(lattice_vectors_2d) @ (np.linalg.inv(film_matrix) @ substrate_matrix) @ lattice_vectors_2d
        )
        twist_angle = get_angle_from_rotation_matrix_2d(rotation)
        if twist_angle is None:
            return None
        return dict(
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
        supercells = []
        for angle in self._get_candidate_twist_angles():
            supercell = self._get_smallest_shared_supercell(angle)
            if supercell is not None:
                supercells.append(supercell)
        supercells.sort(key=lambda supercell: round(np.linalg.det(supercell["xy_supercell_matrix_substrate"])))
        holders = [
            CommensurateLatticeMatchHolder(match_id=index, **supercell) for index, supercell in enumerate(supercells)
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
