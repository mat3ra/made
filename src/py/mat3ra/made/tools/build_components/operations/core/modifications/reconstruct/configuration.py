from typing import List, Union

from mat3ra.made.material import Material
from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseConfigurationPydantic

from ..... import MaterialWithBuildMetadata


class RingNetworkReconstructionConfiguration(BaseConfigurationPydantic):
    """
    Configuration for rebuilding the band along each line of two stacked grains as their ring network.

    Args:
        material (Material): Two honeycomb grains stacked along x without a gap, labelled 0 and 1.
        supercell_matrices (List[List[List[int]]]): Supercell matrix of each grain, rows the vector across the
            boundary and the vector along it.
    """

    type: str = "RingNetworkReconstructionConfiguration"
    material: Union[Material, MaterialWithBuildMetadata]
    supercell_matrices: List[List[List[int]]]
