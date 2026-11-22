from typing import List, Optional

import numpy as np
from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum
from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum
from mat3ra.made.material import Material
from mat3ra.made.utils import AXIS_TO_INDEX_MAP

from ...build_components import MaterialWithBuildMetadata
from ...modify import translate_by_vector
from .utils import merge_two_materials, should_skip_stacking


def merge(
    materials: List[Material],
    merge_method: Optional[MergeMethodsEnum] = MergeMethodsEnum.ADD,
    material_name: Optional[str] = None,
    distance_tolerance: float = 0.1,
    merge_dangerously: bool = False,
) -> MaterialWithBuildMetadata:
    """
    Merge multiple materials using a specific merge method.

    Args:
        materials (List[Material]): List of materials to merge.
        merge_method (MergeMethodsEnum): The merge method to use.
        material_name (Optional[str]): Name of the merged material.
        distance_tolerance (float): The tolerance for resolving overlapping coordinates.
        merge_dangerously (bool): If True, allows merging even if lattices are different.

    Returns:
        MaterialWithBuildMetadata: The merged material.
    """
    merged_material = materials[0]
    for material in materials[1:]:
        merged_material = merge_two_materials(
            merged_material, material, merge_method, material_name, distance_tolerance, merge_dangerously
        )
    return merged_material


def stack(materials: List[Material], direction: AxisEnum) -> MaterialWithBuildMetadata:
    result = materials[0]
    for material in materials[1:]:
        result = stack_two_materials(material_1=result, material_2=material, direction=direction)
    return result


def stack_two_materials(
    material_1: Material,
    material_2: Material,
    direction: AxisEnum = AxisEnum.z,
) -> MaterialWithBuildMetadata:
    """
    Stack two materials along a specified direction by expanding lattices and merging.

    First attempts to stack materials as-is. If that fails due to lattice mismatch,
    adjusts the in-plane lattice vectors of material_2 to match material_1 and tries again.

    Args:
        material_1: First material to stack.
        material_2: Second material to stack.
        direction: Direction along which to stack (x, y, or z axis).

    Returns:
        MaterialWithBuildMetadata: Stacked material with combined lattice and atoms.
    """
    lattice_vector_index = AXIS_TO_INDEX_MAP[direction.value]

    try:
        if should_skip_stacking(material_1, material_2, lattice_vector_index):
            return material_1.clone()

        material_1_lattice_vectors = material_1.lattice.vector_arrays
        material_2_lattice_vectors = material_2.lattice.vector_arrays

        stacked_lattice_vectors_values = [vector.copy() for vector in material_1_lattice_vectors]
        stacked_lattice_vectors_values[lattice_vector_index] = (
            np.array(material_1_lattice_vectors[lattice_vector_index])
            + np.array(material_2_lattice_vectors[lattice_vector_index])
        ).tolist()

        material_1_final_lattice_config = material_1.clone()
        material_1_final_lattice_config.set_lattice_vectors_from_array(stacked_lattice_vectors_values)

        # Translate material2 so its atoms are positioned correctly relative to material1
        material_2_adjusted_c = material_2.clone()
        material_2_adjusted_c.set_lattice_vectors_from_array(stacked_lattice_vectors_values)
        # The translation amount is the original lattice vector of material1 in the stacking direction
        translation_vec = material_1_lattice_vectors[lattice_vector_index]
        material_2_translated = translate_by_vector(
            material_2_adjusted_c, translation_vec, use_cartesian_coordinates=True
        )

        stacked_material = merge_two_materials(
            material1=material_1_final_lattice_config,
            material2=material_2_translated,
            distance_tolerance=0,
            merge_dangerously=False,
            material_name=material_1.name,
        )
        return stacked_material
    except ValueError as e:
        raise ValueError(
            f"Failed to stack materials {material_1.name} and {material_2.name} due to lattice mismatch: {str(e)}"
        ) from e
