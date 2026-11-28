from typing import Optional

import numpy as np
from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum
from mat3ra.made.basis import Basis
from mat3ra.made.material import Material

from ...build_components import MaterialWithBuildMetadata


def merge_two_bases(basis1: Basis, basis2: Basis, distance_tolerance: float) -> Basis:
    """
    Merges two Basis objects into a new Basis object, resolving overlapping coordinates.
    The function assumes that both Basis objects have the same lattice structure handled separately.

    Args:
        basis1 (Basis): The first Basis object to merge.
        basis2 (Basis): The second Basis object to merge.
        distance_tolerance (float): The tolerance for resolving overlapping coordinates.

    Returns:
        Basis: A new Basis object containing merged elements, coordinates, labels, and constraints.
    """
    basis1.to_crystal()
    basis2.to_crystal()

    new_basis = basis1.clone()
    new_basis.add_atoms_from_another_basis(basis2)
    new_basis.resolve_colliding_coordinates(tolerance=distance_tolerance)

    return new_basis


def merge_two_materials(
    material1: Material,
    material2: Material,
    merge_method: Optional[MergeMethodsEnum] = MergeMethodsEnum.ADD,
    material_name: Optional[str] = None,
    distance_tolerance: float = 0.1,
    merge_dangerously: bool = False,
) -> MaterialWithBuildMetadata:
    """
    Merge two materials using a specific merge method.

    Args:
        material1 (Material): The first material to merge.
        material2 (Material): The second material to merge.
        merge_method (MergeMethodsEnum): The merge method to use.
        material_name (Optional[str]): Name of the merged material.
        distance_tolerance (float): The tolerance for resolving overlapping coordinates.
        merge_dangerously (bool): If True, allows merging even if lattices are different.

    Returns:
        MaterialWithBuildMetadata: The merged material.
    """
    if not np.allclose(material1.lattice.vector_arrays, material2.lattice.vector_arrays) and not merge_dangerously:
        raise ValueError("Lattices of the two materials must be the same.")

    if merge_method == MergeMethodsEnum.ADD:
        merged_basis = merge_bases_add(material1.basis, material2.basis, distance_tolerance)
    elif merge_method == MergeMethodsEnum.REPLACE:
        merged_basis = merge_bases_replace(material1.basis, material2.basis, distance_tolerance)
    elif merge_method == MergeMethodsEnum.YIELD:
        merged_basis = merge_bases_yield(material1.basis, material2.basis, distance_tolerance)
    else:
        raise ValueError(f"Unknown merge method: {merge_method}")

    name = material_name or "Merged Material"
    new_material = MaterialWithBuildMetadata.create(
        {"name": name, "lattice": material1.lattice.to_dict(), "basis": merged_basis.to_dict()}
    )

    return new_material


def should_skip_stacking(
    material_1: Material,
    material_2: Material,
    lattice_vector_index: int,
) -> bool:
    """
    Determine if stacking should be skipped due to zero thickness in material_2.

    Also validates that materials are compatible for stacking.

    Args:
        material_1: First material to stack.
        material_2: Second material to stack.
        lattice_vector_index: Index of the lattice vector in the stacking direction.

    Returns:
        bool: True if stacking should be skipped (material_2 has zero thickness).

    Raises:
        ValueError: If in-plane lattice vectors are not the same.
    """
    material_1_lattice_vectors = material_1.lattice.vector_arrays
    material_2_lattice_vectors = material_2.lattice.vector_arrays

    is_zero_thickness = np.allclose(material_2_lattice_vectors[lattice_vector_index], [0, 0, 0])
    if is_zero_thickness:
        return True

    # Check that in-plane vectors are the same
    all_indices = [0, 1, 2]
    in_plane_indices = [i for i in all_indices if i != lattice_vector_index]

    material_1_in_plane_vectors = np.array(material_1_lattice_vectors)[in_plane_indices]
    material_2_in_plane_vectors = np.array(material_2_lattice_vectors)[in_plane_indices]

    if not np.allclose(material_1_in_plane_vectors, material_2_in_plane_vectors):
        difference = np.abs(material_1_in_plane_vectors - material_2_in_plane_vectors)
        raise ValueError(f"In-plane lattice vectors of the two materials must be the same for stacking.\n{difference}")

    return False


def merge_bases_add(basis1: Basis, basis2: Basis, distance_tolerance: float) -> Basis:
    return merge_two_bases(basis1, basis2, distance_tolerance)


def merge_bases_replace(basis1: Basis, basis2: Basis, distance_tolerance: float) -> Basis:
    base1 = basis1.clone()
    return merge_two_bases(base1, basis2, distance_tolerance)


def merge_bases_yield(basis1: Basis, basis2: Basis, distance_tolerance: float) -> Basis:
    base2 = basis2.clone()
    return merge_two_bases(base2, basis1, distance_tolerance)
