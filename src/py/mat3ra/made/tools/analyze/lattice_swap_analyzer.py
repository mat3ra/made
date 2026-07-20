from typing import Union

import numpy as np
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.made.material import Material
from pydantic import BaseModel, Field

from ..build_components.metadata.material_with_build_metadata import MaterialWithBuildMetadata
from ..operations.reusable.unary import transform_material_by_matrix
from .basis import BasisMaterialAnalyzer
from .enums import POSSIBLE_TRANSFORMATION_MATRICES


class LatticeSwapDetectionResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    is_swapped: bool = Field(..., description="Whether a lattice swap was detected")
    permutation: Matrix3x3Schema = Field(..., description="Transformation matrix representing the swap")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")


class MaterialLatticeSwapAnalyzer(BaseModel):
    """
    Analyzer to detect lattice vector swaps/permutations between materials.

    This detects when lattice vectors have been reoriented (e.g., a->a, b->c, c->-b)
    rather than the basis being rotated within the lattice.
    """

    material: Union[Material, MaterialWithBuildMetadata]
    tolerance: float = 0.01

    def _compute_transformation_score(self, matrix: np.ndarray, target_fingerprint) -> float:
        transformed_material = transform_material_by_matrix(self.material, matrix)
        new_analyzer = BasisMaterialAnalyzer(material=transformed_material)
        new_fingerprint = new_analyzer.get_layer_fingerprint(target_fingerprint.layer_thickness)
        return target_fingerprint.get_similarity_score(new_fingerprint)

    def _create_detection_result(self, matrix: np.ndarray, score: float) -> LatticeSwapDetectionResult:
        is_identity = np.allclose(matrix, np.eye(3), atol=self.tolerance)
        return LatticeSwapDetectionResult(
            is_swapped=not is_identity,
            permutation=Matrix3x3Schema(root=matrix.tolist()),
            confidence=score,
        )

    def detect_swap_from_original(
        self, original_material: MaterialWithBuildMetadata, layer_thickness: float = 1.0, threshold: float = 0.1
    ) -> LatticeSwapDetectionResult:
        """
        Detect lattice swap from the original material.

        We apply every transformation matrix to lattice and basis, compute the fingerprint along z, then compare
        to the original material's fingerprint. The best matching transformation (if above threshold) is considered
        a detected swap.


        Args:
            original_material: The original material before transformation
            layer_thickness: Thickness of layers for fingerprint comparison
            threshold: Minimum improvement threshold to consider a swap detected

        Returns:
            LatticeSwapDetectionResult: Swap detection results with permutation and new lattice
        """
        target_analyzer = BasisMaterialAnalyzer(material=original_material)
        target_fingerprint = target_analyzer.get_layer_fingerprint(layer_thickness)
        possible_matrices = list(map(np.array, POSSIBLE_TRANSFORMATION_MATRICES))

        best_match = None
        max_score = 0

        for matrix in possible_matrices:
            score = self._compute_transformation_score(matrix, target_fingerprint)
            if score > max_score:
                best_match = self._create_detection_result(matrix, score)
                max_score = score

        if best_match and best_match.is_swapped and best_match.confidence >= threshold:
            return best_match
        # If no swap detected, return identity result
        return self._create_detection_result(np.eye(3), 1.0)

    def get_corrected_material(
        self,
        target: MaterialWithBuildMetadata,
        layer_thickness: float = 1.0,
        threshold: float = 0.1,
    ) -> MaterialWithBuildMetadata:
        """
        Correct the material's lattice to match the target material's orientation if a swap is detected.

        Args:
            target: The target material to match
            layer_thickness: Thickness of layers for fingerprint comparison
            threshold: Minimum improvement threshold to consider a swap detected

        Returns:
            MaterialWithBuildMetadata: Corrected material with lattice matching the target orientation
        """
        swap_info = self.detect_swap_from_original(target, layer_thickness, threshold)
        if swap_info.is_swapped:
            matrix_list = [list(row.root) if hasattr(row, "root") else row for row in swap_info.permutation.root]
            matrix_array = np.array(matrix_list)
            return transform_material_by_matrix(self.material, matrix_array)
        return self.material
