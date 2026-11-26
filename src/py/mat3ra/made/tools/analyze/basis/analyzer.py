from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum
from mat3ra.made.utils import AXIS_TO_INDEX_MAP

from .. import BaseMaterialAnalyzer
from ..fingerprint import LayeredFingerprintAlongAxis, UniqueElementStringsPerLayer


class BasisMaterialAnalyzer(BaseMaterialAnalyzer):
    def get_layer_fingerprint(
        self, layer_thickness: float = 1.0, axis: AxisEnum = AxisEnum.z
    ) -> LayeredFingerprintAlongAxis:
        """
        Create a fingerprint of the material by analyzing layers along the specified axis.

        Args:
            layer_thickness: Thickness of each layer in Angstroms
            axis: Axis along which to compute the fingerprint

        Returns:
            LayeredFingerprintAlongAxis: Structured fingerprint with layer information
        """
        material_cartesian = self.material.clone()
        material_cartesian.to_cartesian()

        coordinates = material_cartesian.basis.coordinates.values
        elements = material_cartesian.basis.elements.values

        axis_index = AXIS_TO_INDEX_MAP[axis.value]
        axis_coords = [coord[axis_index] for coord in coordinates]
        min_coord, max_coord = min(axis_coords), max(axis_coords)

        fingerprint = LayeredFingerprintAlongAxis(axis=axis, layer_thickness=layer_thickness)

        current_coord = min_coord
        while current_coord < max_coord:
            layer_min = current_coord
            layer_max = current_coord + layer_thickness

            layer_elements = []
            for i, coord_val in enumerate(axis_coords):
                if layer_min <= coord_val < layer_max:
                    layer_elements.append(elements[i])

            unique_elements = sorted(list(set(layer_elements))) if layer_elements else []
            layer = UniqueElementStringsPerLayer(min_coord=layer_min, max_coord=layer_max, elements=unique_elements)
            fingerprint.layers.append(layer)

            current_coord += layer_thickness

        return fingerprint
