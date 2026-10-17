from typing import Any, Dict, List, Literal, Union

import numpy as np
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.made.material import Material

# TODO: move to mat3ra-code
AXIS_TO_INDEX_MAP = {"x": 0, "y": 1, "z": 2}


# TODO: use mat3ra-code
def map_array_to_array_with_id_value(array: List[Any], remove_none: bool = False) -> List[Any]:
    full_array = [{"id": i, "value": item} for i, item in enumerate(array)]
    if remove_none:
        return list(filter(lambda x: x["value"] is not None, full_array))
    return full_array


# TODO: use mat3ra-code
def map_array_with_id_value_to_array(array: List[Dict[str, Any]]) -> List[Any]:
    return [item["value"] for item in array]


def get_center_of_coordinates(coordinates: List[List[float]]) -> List[float]:
    """
    Calculate the center of the coordinates.

    Args:
        coordinates (List[List[float]]): The list of coordinates.

    Returns:
        List[float]: The center of the coordinates.
    """
    return np.mean(np.array(coordinates), axis=0).tolist()


def create_2d_supercell_matrices(max_search: int) -> List[np.ndarray]:
    """
    Create a list of 2D supercell matrices within a maximum search range.

    Filtering conditions:
    - Non-zero area constraint
    - Positive determinant (to exclude mirroring transformations)

    Args:
        max_search: The maximum search range.
    Returns:
        List[np.ndarray]: The list of supercell matrices.
    """
    matrices = []
    for s11 in range(-max_search, max_search + 1):
        for s12 in range(-max_search, max_search + 1):
            for s21 in range(-max_search, max_search + 1):
                for s22 in range(-max_search, max_search + 1):
                    matrix = np.array([[s11, s12], [s21, s22]])
                    determinant = np.linalg.det(matrix)
                    if determinant == 0 or determinant < 0:
                        continue
                    matrices.append(matrix)
    return matrices


def get_angle_from_rotation_matrix_2d(
    matrix: np.ndarray, zero_tolerance: float = 1e-6, round_digits: int = 3
) -> Union[float, None]:
    """
    Get the angle from a 2x2 rotation matrix in degrees if it's a pure rotation matrix.
    Args:
        matrix: The 2x2 rotation matrix.
        zero_tolerance: The zero tolerance for the determinant.
        round_digits: The number of digits to round the angle.

    Returns:
        Union[float, None]: The angle in degrees if it's a pure rotation matrix, otherwise None.
    """
    if matrix.shape != (2, 2):
        return None
    if np.abs(np.linalg.det(matrix) - 1) > zero_tolerance:
        return None
    if not np.all(np.abs(matrix) <= 1):
        return None
    # Check if it's in form of rotation matrix [cos(theta), -sin(theta); sin(theta), cos(theta)]
    if not np.allclose(matrix @ matrix.T, np.eye(2), atol=zero_tolerance):
        return None
    cos_theta = matrix[0, 0]
    sin_theta = matrix[1, 0]
    angle_rad = np.arctan2(sin_theta, cos_theta)
    angle_deg = np.round(np.degrees(angle_rad), round_digits)
    return angle_deg


def adjust_material_cell_to_set_gap_along_direction(
    material: Material, gap: float, direction: AxisEnum = AxisEnum.z
) -> Material:
    """
    Adjust the cell along the stacking direction to make the distance from the cell end to its closest atom
    to be equal to the gap, in Angstroms.
    """
    direction_str = direction.value
    axis_index = AXIS_TO_INDEX_MAP[direction_str]

    max_fractional = get_atomic_coordinates_extremum(material, "max", direction_str, False)
    current_vectors = material.lattice.vector_arrays
    current_vector = np.array(current_vectors[axis_index])
    current_length = np.linalg.norm(current_vector)

    # Add a small nudge when gap=0 to prevent atoms at fractional coordinate 1.0 from being wrapped
    nudge = 0.0001 if gap == 0 else 0
    new_length = (max_fractional * current_length) + gap + nudge

    new_vector = current_vector * (new_length / current_length)

    new_lattice_vectors = list(current_vectors)
    new_lattice_vectors[axis_index] = new_vector.tolist()

    new_material = material.clone()
    new_material.set_lattice_vectors_from_array(new_lattice_vectors)

    return new_material


def get_atomic_coordinates_extremum(
    material: Material,
    extremum: Literal["max", "min"] = "max",
    axis: Literal["x", "y", "z"] = "z",
    use_cartesian_coordinates: bool = False,
) -> float:
    """
    Return minimum or maximum of coordinates along the specified axis.

    Args:
        material (Material): Material object.
        extremum (str): "min" or "max".
        axis (str):  "x", "y", or "z".
        use_cartesian_coordinates (bool): Whether to use Cartesian coordinates.
    Returns:
        float: Minimum or maximum of coordinates along the specified axis.
    """
    new_material = material.clone()
    if use_cartesian_coordinates:
        new_material.to_cartesian()
    else:
        new_material.to_crystal()
    return new_material.basis.coordinates.get_extremum_value_along_axis(extremum, axis)
