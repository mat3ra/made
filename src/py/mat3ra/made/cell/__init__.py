from typing import List

import numpy as np
from mat3ra.code.vector import RoundedVector3D
from mat3ra.esse.models.properties_directory.structural.lattice import LatticeVectorsSchema as CellSchema
from mat3ra.utils.mixins import RoundNumericValuesMixin
from pydantic import Field

DEFAULT_CELL = np.eye(3).tolist()


class Cell(RoundNumericValuesMixin, CellSchema):
    __rounded_vector3d__ = RoundedVector3D
    __default_vectors__ = DEFAULT_CELL

    a: RoundedVector3D = Field(default_factory=lambda: Cell.__rounded_vector3d__(DEFAULT_CELL[0]))
    b: RoundedVector3D = Field(default_factory=lambda: Cell.__rounded_vector3d__(DEFAULT_CELL[1]))
    c: RoundedVector3D = Field(default_factory=lambda: Cell.__rounded_vector3d__(DEFAULT_CELL[2]))

    @classmethod
    def from_vectors_array(cls, vectors: List[List[float]] = DEFAULT_CELL) -> "Cell":
        return cls(
            a=RoundedVector3D(vectors[0]),
            b=RoundedVector3D(vectors[1]),
            c=RoundedVector3D(vectors[2]),
        )

    def get_vector_arrays(self, skip_rounding=False) -> List[List[float]]:
        if skip_rounding:
            return [self.a.value, self.b.value, self.c.value]
        return [self.a.value_rounded, self.b.value_rounded, self.c.value_rounded]

    @property
    def vector_arrays(self) -> List[List[float]]:
        return self.get_vector_arrays(skip_rounding=True)

    @property
    def vector_arrays_rounded(self) -> List[List[float]]:
        return self.get_vector_arrays(skip_rounding=False)

    def convert_point_to_cartesian(self, point: List[float]) -> List[float]:
        np_vector = np.array(self.vector_arrays)
        return np.dot(point, np_vector).tolist()

    def convert_point_to_crystal(self, point: List[float]) -> List[float]:
        np_vector = np.array(self.vector_arrays)
        return np.dot(point, np.linalg.inv(np_vector)).tolist()

    @property
    def volume(self) -> float:
        return np.linalg.det(np.array(self.vector_arrays))

    @property
    def volume_rounded(self) -> float:
        return self.round_array_or_number(self.volume)
