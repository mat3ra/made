from functools import wraps
from typing import TYPE_CHECKING, Union

import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds, RoundedArrayWithIds
from mat3ra.made.material import Material

if TYPE_CHECKING:
    from .material import MaterialWithCrystalSites


def decorator_handle_periodic_boundary_conditions(cutoff):
    """
    Decorator to handle periodic boundary conditions.

    Copies atoms near boundaries within the cutoff distance beyond the opposite side of the cell
    creating the effect of periodic boundary conditions for edge atoms.

    Results of the function are filtered to remove atoms or coordinates outside the original cell.

    Args:
        cutoff (float): The cutoff distance for a border slice in crystal coordinates.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(material, *args, **kwargs):
            augmented_material, last_id = augment_material_with_periodic_images(material, cutoff)

            result = func(augmented_material, *args, **kwargs)

            original_ids = material.basis.coordinates.ids
            if isinstance(result, (ArrayWithIds, RoundedArrayWithIds)):
                result.filter_by_ids(original_ids)
            if isinstance(result, list):
                if all(isinstance(x, int) for x in result):
                    result = [id for id in result if id <= last_id]
                elif all(isinstance(x, list) and len(x) == 3 for x in result):
                    result = [coord for coord in result if all(0 <= c < 1 for c in coord)]
            return result

        return wrapper

    return decorator


def augment_material_with_periodic_images(material: Union[Material, "MaterialWithCrystalSites"], cutoff: float = 0.25):
    """
    Augment the material's dataset by adding atoms from periodic images within a cutoff distance
    from the boundaries by copying them to the opposite side of the cell.

    Args:
        material (Material): The material to augment.
        cutoff (float): The cutoff value for filtering atoms near boundaries, in crystal coordinates.

    Returns:
        Tuple[Material, int]: The augmented material and the last id of the original material for filtering.
    """
    augmented_material = material.clone()

    last_id = material.basis.coordinates.ids[-1]
    original_basis_is_in_cartesian = material.basis.is_in_cartesian_units

    augmented_material.to_crystal()
    coordinates = np.array(augmented_material.basis.coordinates.values)
    elements = np.array(augmented_material.basis.elements.values)

    for axis in range(3):
        for direction in [-1, 1]:
            mask = (coordinates[:, axis] < cutoff) if direction == 1 else (coordinates[:, axis] > (1 - cutoff))
            filtered_coordinates = coordinates[mask]
            filtered_elements = elements[mask]
            translation_vector = np.zeros(3)
            translation_vector[axis] = direction
            translated_coordinates = filtered_coordinates + translation_vector
            for coord, elem in zip(translated_coordinates, filtered_elements):
                augmented_material.add_atom(elem, coord)

    if original_basis_is_in_cartesian:
        augmented_material.to_cartesian()

    return augmented_material, last_id


def decorator_perform_operation_in_cartesian_coordinates(func):
    """
    Decorator to perform operations in Cartesian coordinates.

    Converts the material to Cartesian coordinates before executing the function
    and converts it back to crystal coordinates after execution.

    Args:
        func (Callable): The function to decorate.

    Returns:
        Callable: The decorated function.
    """

    @wraps(func)
    def wrapper(material, *args, **kwargs):
        original_basis_is_in_cartesian = material.material.basis.is_in_cartesian_units
        if not original_basis_is_in_cartesian:
            material.material.to_cartesian()

        result = func(material, *args, **kwargs)

        if not original_basis_is_in_cartesian:
            material.material.to_crystal()

        return result

    return wrapper


def calculate_von_mises_strain(strain_matrix: np.ndarray) -> float:
    """
    Calculate von Mises strain (%) from a 2D strain transformation matrix (top-left 2x2 of 3x3).

    Args:
        strain_matrix (np.ndarray): A 2D numpy array representing the strain transformation matrix.
    Returns:
        float: The von Mises strain in percentage.
    """
    # allow passing a Python list
    strain_matrix_2x2 = np.array(strain_matrix, dtype=float)[:2, :2]
    E = 0.5 * (strain_matrix_2x2.T @ strain_matrix_2x2 - np.eye(2))

    exx = E[0, 0]
    eyy = E[1, 1]
    exy = 0.5 * (E[0, 1] + E[1, 0])

    e_von_mises = np.sqrt(exx**2 - exx * eyy + eyy**2 + 3 * exy**2)

    return abs(e_von_mises) * 100.0


def minimum_image_distances(frac_coords: np.ndarray, lattice_vectors: np.ndarray) -> np.ndarray:
    """
    Compute pairwise distances between fractional coordinates under periodic boundary conditions.

    Applies the minimum image convention: for each pair, the shortest distance
    across all periodic images is returned.

    Args:
        frac_coords (np.ndarray): Fractional coordinates, shape (N, 3).
        lattice_vectors (np.ndarray): Lattice vectors, shape (3, 3), rows are vectors.

    Returns:
        np.ndarray: Symmetric distance matrix, shape (N, N), in the same units as lattice_vectors.
    """
    n = len(frac_coords)
    distances = np.zeros((n, n))
    for i in range(n):
        delta = frac_coords[i] - frac_coords[i + 1 :]
        delta -= np.round(delta)
        dists = np.linalg.norm(delta @ lattice_vectors, axis=1)
        distances[i, i + 1 :] = dists
        distances[i + 1 :, i] = dists
    return distances
