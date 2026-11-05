from typing import Literal

import numpy as np
from mat3ra.code.array_with_ids import RoundedArrayWithIds
from mat3ra.code.value_with_id import RoundedValueWithId
from mat3ra.code.vector import RoundedVector3D as RoundedPoint3D


class Coordinate(RoundedValueWithId):
    value: RoundedPoint3D

    def get_value_along_axis(self, axis: Literal["x", "y", "z"] = "z"):
        return self.value.root[{"x": 0, "y": 1, "z": 2}[axis]]


class Coordinates(RoundedArrayWithIds):
    @classmethod
    def to_standard_coordinate(cls, value):
        """
        Rounds to the coordinate precision, then wraps exactly into [0, 1): the wrapped value is rounded again, so
        the result is its own standard coordinate.
        """
        return cls.round_array_or_number(np.mod(cls.round_array_or_number(value), 1))

    def get_values_along_axis(
        self,
        axis: Literal["x", "y", "z"] = "z",
    ):
        values_along_axis = [Coordinate(value=coord).get_value_along_axis(axis) for coord in self.values]
        return values_along_axis

    def get_max_value_along_axis(
        self,
        axis: Literal["x", "y", "z"] = "z",
    ):
        return np.max(self.get_values_along_axis(axis))

    def get_min_value_along_axis(
        self,
        axis: Literal["x", "y", "z"] = "z",
    ):
        return np.min(self.get_values_along_axis(axis))

    def get_extremum_value_along_axis(
        self,
        extremum: Literal["max", "min"] = "max",
        axis: Literal["x", "y", "z"] = "z",
    ):
        if extremum == "max":
            return self.get_max_value_along_axis(axis)
        return self.get_min_value_along_axis(axis)
