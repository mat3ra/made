from functools import reduce
from typing import List

import numpy as np
from mat3ra.esse.models.core.abstract.vector_2d import Vector2dSchema
from mat3ra.esse.models.materials_category_components.entities.auxiliary.two_dimensional.supercell_matrix_2d import (
    SupercellMatrix2DSchema,
)


def are_vectors_colinear(v1: Vector2dSchema, v2: Vector2dSchema, tol=1e-3):
    v1 = np.array(v1)
    v2 = np.array(v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < tol or norm2 < tol:
        return False
    cos_angle = np.dot(v1, v2) / (norm1 * norm2)
    # Colinear if |cos_angle| close to 1
    return np.abs(np.abs(cos_angle) - 1) < tol


def align_first_vector_to_x_2d_right_handed(vectors: List[Vector2dSchema]):
    """
    Rotates a set of 2D lattice vectors so that the first vector is aligned with the x-axis,
    and makes the cell right-handed.
    vectors: (2, 2) array
    Returns: rotated (2, 2) array
    """
    vectors_np = np.array(vectors)
    if vectors_np.shape != (2, 2):
        raise ValueError("Input must be two 2D vectors (shape (2, 2)).")
    v = vectors_np[0]
    a = np.linalg.norm(v)
    if a == 0:
        raise ValueError("First lattice vector has zero length.")
    # Angle to x-axis
    angle = np.arctan2(v[1], v[0])
    # 2D rotation matrix to align v with x-axis
    R = np.array([[np.cos(-angle), -np.sin(-angle)], [np.sin(-angle), np.cos(-angle)]])
    rotated_vectors = vectors_np @ R.T
    # Set first vector to [a, 0]
    rotated_vectors[0] = np.array([a, 0])

    # Check handedness: z-component of cross product should be positive
    cross_z = np.cross(rotated_vectors[0], rotated_vectors[1])
    if cross_z < 0:
        rotated_vectors[1] = -rotated_vectors[1]

    return rotated_vectors


def get_global_gcd(A: SupercellMatrix2DSchema, B: SupercellMatrix2DSchema) -> int:
    # flatten all entries, compute gcd over them
    vals = np.hstack((A.ravel(), B.ravel())).astype(int)
    return reduce(np.gcd, vals.tolist())
