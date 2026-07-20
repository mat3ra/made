import numpy as np
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.made.material import Material

from ...modify import wrap_to_unit_cell
from ..core.unary import strain


def transform_material_by_matrix(material: Material, matrix: np.ndarray) -> Material:
    """
    Transforms a material by applying a transformation matrix to lattice vectors and coordinates.

    Args:
        material: The material to be transformed.
        matrix: The 3x3 transformation matrix as a numpy array.

    Returns:
        A new material instance with transformed lattice and coordinates, wrapped to unit cell.
    """
    current_lattice_vectors = np.array(material.lattice.vector_arrays)
    current_coordinates = material.basis.coordinates.values

    new_lattice_vectors = (matrix @ current_lattice_vectors.T).tolist()
    new_coordinates = (np.linalg.inv(matrix) @ np.array(current_coordinates).T).T.tolist()

    transformed_material = material.clone()
    transformed_material.set_lattice_vectors_from_array(new_lattice_vectors)
    transformed_material.basis.coordinates.values = new_coordinates
    return wrap_to_unit_cell(transformed_material)


def strain_to_match_lattice(material_to_strain: Material, target_material: Material) -> Material:
    """
    Strains a material to match the lattice of a target material.

    Args:
        material_to_strain: The material to be strained.
        target_material: The material with the target lattice.

    Returns:
        A new material instance with the strained lattice.
    """
    target_lattice_vectors = np.array(target_material.lattice.vector_arrays)
    source_lattice_vectors = np.array(material_to_strain.lattice.vector_arrays)

    # Prevent division by zero or singular matrix issues
    if np.linalg.det(source_lattice_vectors) == 0:
        raise ValueError("Lattice of material to strain is singular and cannot be inverted.")

    strain_matrix_np = np.linalg.inv(source_lattice_vectors) @ target_lattice_vectors
    strain_matrix = Matrix3x3Schema(root=strain_matrix_np.tolist())
    strained_material = strain(material_to_strain, strain_matrix)
    return strained_material
