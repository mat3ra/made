import math
from typing import List, Optional

import numpy as np
from mat3ra.code.constants import HASH_TOLERANCE
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.properties_directory.structural.lattice import (
    LatticeSchema,
    LatticeTypeEnum,
    LatticeUnitsSchema,
)
from mat3ra.utils.mixins import RoundNumericValuesMixin
from pydantic import BaseModel

from .cell import Cell

COORDINATE_TOLERANCE = 6


class LatticeVectors(Cell):
    pass


class LatticeSchemaVectorless(BaseModel):
    """LatticeSchema without the vectors field to avoid conflicts."""

    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float
    units: LatticeUnitsSchema = LatticeSchema.model_fields["units"].default_factory()
    type: LatticeTypeEnum = LatticeSchema.model_fields["type"].default


class Lattice(RoundNumericValuesMixin, LatticeSchemaVectorless, InMemoryEntityPydantic):
    __types__ = LatticeTypeEnum
    __type_default__ = LatticeSchema.model_fields["type"].default
    __units_default__ = LatticeSchema.model_fields["units"].default_factory()

    a: float = 1.0
    b: float = a
    c: float = a
    alpha: float = 90.0
    beta: float = alpha
    gamma: float = alpha

    @property
    def vectors(self) -> LatticeVectors:
        vectors = self.calculate_vectors()
        return LatticeVectors.from_vectors_array(vectors)

    def calculate_vectors(self):
        a = self.a
        b = self.b
        c = self.c
        # Convert degrees to radians for trigonometric functions
        alpha_rad = math.radians(self.alpha)
        beta_rad = math.radians(self.beta)
        gamma_rad = math.radians(self.gamma)

        # Calculate cosines and sines of the angles
        cos_alpha = math.cos(alpha_rad)
        cos_beta = math.cos(beta_rad)
        cos_gamma = math.cos(gamma_rad)
        sin_alpha = math.sin(alpha_rad)
        sin_beta = math.sin(beta_rad)

        # Compute gamma star (used in matrix calculation)
        gamma_star = math.acos((cos_alpha * cos_beta - cos_gamma) / (sin_alpha * sin_beta))
        cos_gamma_star = math.cos(gamma_star)
        sin_gamma_star = math.sin(gamma_star)

        # Calculate the vectors
        vector_a = [a * sin_beta, 0.0, a * cos_beta]
        vector_b = [-b * sin_alpha * cos_gamma_star, b * sin_alpha * sin_gamma_star, b * cos_alpha]
        vector_c = [0.0, 0.0, c]

        return [vector_a, vector_b, vector_c]

    @classmethod
    def from_vectors_array(
        cls,
        vectors: List[List[float]],
        units: Optional[LatticeUnitsSchema] = __units_default__,
        type: Optional[LatticeTypeEnum] = __type_default__,
    ) -> "Lattice":
        a = np.linalg.norm(vectors[0])
        b = np.linalg.norm(vectors[1])
        c = np.linalg.norm(vectors[2])
        bc = b * c
        ac = a * c
        ab = a * b

        if bc == 0 or ac == 0 or ab == 0:
            print("Vectors:", vectors)
            raise ValueError("Vectors must not be zero vectors.")

        alpha = np.degrees(np.arccos(np.dot(vectors[1], vectors[2]) / bc))
        beta = np.degrees(np.arccos(np.dot(vectors[0], vectors[2]) / ac))
        gamma = np.degrees(np.arccos(np.dot(vectors[0], vectors[1]) / ab))

        return cls(
            a=float(a),
            b=float(b),
            c=float(c),
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            units=units,
            type=type,
        )

    @property
    def vector_arrays(self) -> List[List[float]]:
        return self.vectors.vector_arrays

    @property
    def vector_arrays_rounded(self) -> List[List[float]]:
        return self.vectors.vector_arrays_rounded

    @property
    def cell_volume(self) -> float:
        return self.vectors.volume

    @property
    def cell_volume_rounded(self) -> float:
        return self.vectors.volume_rounded

    @property
    def reciprocal_vectors(self):
        return np.linalg.inv(np.array(self.vector_arrays, dtype=float)).T.tolist()

    @property
    def reciprocal_vector_norms(self) -> List[float]:
        return [float(np.linalg.norm(vector)) for vector in self.reciprocal_vectors]

    @property
    def reciprocal_vector_ratios(self) -> List[float]:
        norms = self.reciprocal_vector_norms
        max_norm = max(norms)
        return [round(float(value / max_norm), 3) for value in norms]

    @property
    def type_extended(self) -> str:
        """Get the extended lattice type classification.

        For lattice types with subtypes (BCT, ORCF, RHL, MCLC, TRI),
        returns the specific subtype based on lattice parameters.
        For other types, returns the base type string.
        """
        a, b, c = self.a, self.b, self.c
        alpha, beta, gamma = self.alpha, self.beta, self.gamma
        cos_alpha = math.cos(math.radians(alpha))
        lattice_type = self.type.value if hasattr(self.type, "value") else str(self.type)

        if lattice_type == "BCT":
            return "BCT-1" if c < a else "BCT-2"
        elif lattice_type == "ORCF":
            if 1 / (a * a) >= 1 / (b * b) + 1 / (c * c):
                return "ORCF-1"
            return "ORCF-2"
        elif lattice_type == "RHL":
            return "RHL-1" if cos_alpha > 0 else "RHL-2"
        elif lattice_type == "MCLC":
            if gamma >= 90:
                return "MCLC-1"
            if (b / c) * cos_alpha + (b * b / (a * a)) * (1 - cos_alpha * cos_alpha) <= 1:
                return "MCLC-3"
            return "MCLC-5"
        elif lattice_type == "TRI":
            if alpha > 90 and beta > 90 and gamma >= 90:
                return "TRI_1a"
            return "TRI_1b"
        else:
            return lattice_type

    def get_hash_string(self, is_scaled: bool = False) -> str:
        """Mirrors JS Lattice.getHashString(isScaled). Rounds to HASH_TOLERANCE decimal places."""
        scale = self.a if is_scaled else 1
        values = [self.a / scale, self.b / scale, self.c / scale, self.alpha, self.beta, self.gamma]
        return ";".join(f"{round(v, HASH_TOLERANCE):g}" for v in values) + ";"

    def get_scaled_by_matrix(self, matrix: List[List[float]]):
        """
        Scale the lattice by a matrix.
        Args:
            matrix (List[List[float]]): A 3x3 matrix.
        """
        np_vectors = np.array(self.vector_arrays)
        np_matrix = np.array(matrix)
        scaled_vectors = np.dot(np_matrix, np_vectors).tolist()
        new_lattice = self.from_vectors_array(vectors=scaled_vectors, units=self.units, type=self.type)
        return new_lattice
