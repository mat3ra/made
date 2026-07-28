from typing import List

import numpy as np
from mat3ra.code.vector import Vector3D
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.made.material import Material

from ...build_components.metadata import MaterialWithBuildMetadata
from ...build_components.operations.core.modifications.perturb import FunctionHolder
from ...convert import from_ase, to_ase
from ...modify import translate_by_vector, wrap_to_unit_cell
from ...third_party import ase_make_supercell
from ...utils import decorator_convert_supercell_matrix_2x2_to_3x3


def translate(material: Material, vector: Vector3D) -> Material:
    return translate_by_vector(material, vector, use_cartesian_coordinates=True)


@decorator_convert_supercell_matrix_2x2_to_3x3
def supercell(material: MaterialWithBuildMetadata, supercell_matrix) -> MaterialWithBuildMetadata:
    atoms = to_ase(material)

    supercell_atoms = ase_make_supercell(atoms, supercell_matrix)
    material_config = from_ase(supercell_atoms)
    # ASE make_supercell drops atoms.info; merge prior build/boundaryConditions when present.
    source_metadata = material.to_dict().get("metadata") or {}
    if source_metadata:
        material_config["metadata"] = {**material_config.get("metadata", {}), **source_metadata}
    new_material = MaterialWithBuildMetadata.create(material_config)
    new_material.name = material.name
    return new_material


def edit_cell(material: Material, lattice_vectors=None) -> MaterialWithBuildMetadata:
    if lattice_vectors is not None:
        material.set_lattice_vectors(
            lattice_vector1=lattice_vectors[0], lattice_vector2=lattice_vectors[1], lattice_vector3=lattice_vectors[2]
        )
    wrapped_material = wrap_to_unit_cell(material)
    return wrapped_material


def strain(material: Material, strain_matrix: Matrix3x3Schema) -> Material:
    """
    Applies a strain to the material by modifying its lattice vectors while keeping the basis in crystal coordinates.
    """
    if not isinstance(strain_matrix, Matrix3x3Schema):
        raise ValueError("strain_matrix must be an instance of Matrix3x3Schema")

    strain_matrix_np = np.array([row.root for row in strain_matrix.root])
    lattice_vectors_np = np.array(material.lattice.vector_arrays)
    new_lattice_vectors_np = lattice_vectors_np @ strain_matrix_np
    new_lattice_vectors = new_lattice_vectors_np.tolist()

    new_material = material.clone()

    original_crystal_coords = new_material.basis.coordinates.values

    new_material.set_lattice_vectors_from_array(new_lattice_vectors)
    new_material.basis.coordinates.values = original_crystal_coords

    return new_material


def perturb(
    material: Material, perturbation_function: FunctionHolder, use_cartesian_coordinates: bool = False
) -> Material:
    """
    Applies a small delta perturbation to a each atom in the material. Lattice vectors are not modified.

    Args:
        material: The input Material instance containing coordinates.
        perturbation_function: A PerturbationFunctionHolder that defines
                     a function f(x,y,z) -> float (or vector) and
                     optional transform_coordinates behavior.
        use_cartesian_coordinates: If True, the perturbation is applied in Cartesian coordinates.
                                   If False, the perturbation is applied in crystal coordinates.

    Returns:
        A new Material with perturbed coordinates.
    """
    new_material = material.clone()
    if use_cartesian_coordinates:
        new_material.to_cartesian()
    original_coordinates = new_material.basis.coordinates.values
    perturbed_coordinates: List[List[float]] = []

    for coordinate in original_coordinates:
        displacement = perturbation_function.apply_function(coordinate, material=new_material)

        if isinstance(displacement, (list, tuple, np.ndarray)):
            delta = np.array(displacement)
        else:
            delta = np.array([0.0, 0.0, displacement])

        new_coordinate = np.array(coordinate) + delta
        perturbed_coordinates.append(new_coordinate.tolist())

    new_material.set_coordinates(perturbed_coordinates)
    if use_cartesian_coordinates:
        new_material.to_crystal()
    return new_material


def rotate(material: Material, axis: List[int], angle: float, wrap: bool = True) -> Material:
    """
    Rotate the basis of the material relative to the lattice.
    This operation breaks symmetry and does not modify lattice vectors.

    Args:
        material (Material): The material to rotate.
        axis (List[int]): The axis to rotate around, expressed as [x, y, z].
        angle (float): The angle of rotation in degrees.
        wrap (bool): Whether to wrap the material to the unit cell.
    Returns:
        Atoms: The rotated material.
    """
    new_material = material.clone()
    original_is_in_cartesian_units = new_material.basis.is_in_cartesian_units
    new_material.to_crystal()
    atoms = to_ase(new_material)
    atoms.rotate(v=axis, a=angle, center="COU", rotate_cell=False)
    if wrap:
        atoms.wrap()
    new_material = MaterialWithBuildMetadata.create(from_ase(atoms))
    if original_is_in_cartesian_units:
        new_material.to_cartesian()
    return new_material
